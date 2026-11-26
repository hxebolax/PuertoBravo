"""Integration checks for independently switchable local-game cheats.

These use the upstream app fixture under pytest. The frozen build also runs
them headlessly with --cheats-self-test, without touching player save slots.
"""
import copy
import math

import pygame

from juego import menus_juego
from juego.cheats import OPTIONS, menu_option
from juego.config import Config, POR_DEFECTO
from juego.entidades import Jugador, Objeto, Persona, Vehiculo
from juego.mochila import CATALOGO


def fresh(app):
    app.vuelo_en_pruebas = False
    app.teclas = set()
    app.cfg.v = copy.deepcopy(POR_DEFECTO)
    app.cfg["tutorial_visto"] = True
    app.empezar_partida(None)
    p = app.partida
    app.pila = [p]
    p.personas = []
    p.objetos = []
    p.vehiculos = []
    p.mision = p.trabajo = p.evento = None
    p.transicion = False
    p.j.dinero = 1000000
    p.cfg["ambulancias"] = False
    p.cfg["sucesos"] = False
    p.cfg["sin_policia"] = True
    p.cfg["impuestos_facturas"] = False
    return p


def enemy(p, tipo="enemigo", distance=1):
    q = Persona(tipo, p.j.x + distance, p.j.y)
    q.hostil = True
    p.personas.append(q)
    return q


def car(p):
    model = next(v for v in p.datos["vehiculos"] if not v.get("vuela") and not v.get("barco") and v.get("motor") != "motor_bici")
    v = Vehiculo(model, p.j.x, p.j.y)
    p.vehiculos.append(v)
    return v


def test_options_default_off_and_independent(app):
    p = fresh(app)
    assert all(p.cfg[row[0]] is False for row in OPTIONS)
    p.cfg["cheat_recoger"] = True
    assert all(p.cfg[row[0]] is False for row in OPTIONS if row[0] != "cheat_recoger")


def test_options_save_and_reload(app):
    from juego import rutas
    import os
    filename = os.path.join(rutas.DATA, "cheat_test_options.json")
    c = Config(filename)
    for row in OPTIONS:
        c[row[0]] = True
    c.guardar()
    again = Config(filename)
    assert all(again[row[0]] is True for row in OPTIONS)


def test_menu_exposes_all_toggles_and_help(app):
    fresh(app)
    menu_option(app).accion()
    m = app.pila[-1]
    for i, row in enumerate(OPTIONS):
        assert m.opciones[i].ayuda
        assert not app.cfg[row[0]]
        m.opciones[i].ajuste(1)
        assert app.cfg[row[0]]
        m.opciones[i].ajuste(-1)
        assert not app.cfg[row[0]]


def test_remote_briefcase_without_kill_and_no_double_reward(app):
    p = fresh(app)
    o = Objeto("dinero", "briefcase", p.j.x + 500, p.j.y + 500)
    o.valor = 600
    p.objetos.append(o)
    before = p.j.dinero
    p.cheat_collect()
    assert o in p.objetos
    p.cfg["cheat_recoger"] = True
    p.cheat_collect()
    assert o not in p.objetos and p.j.dinero == before + 600
    p.recoger(o)
    p.cheat_collect()
    assert p.j.dinero == before + 600 and p.j.stats["enemigos"] == 0


def test_briefcase_wins_before_timeout(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    o = Objeto("dinero", "briefcase", p.j.x + 60, p.j.y)
    o.valor = 300
    p.objetos.append(o)
    p.evento = {"tipo": "maletin", "objeto": o, "t": 0}
    before = p.j.dinero
    p.cheat_collect()
    p._eventos(0.05)
    assert p.evento is None and p.j.dinero == before + 300


def test_collect_in_vehicle_and_full_backpack(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    p.j.veh = car(p)
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": False} for _ in range(100)]
    o = Objeto("valor", "valuable", p.j.x + 100, p.j.y)
    o.item = ident
    o.robado = True
    p.objetos.append(o)
    p.cheat_collect()
    assert o not in p.objetos and len(p.j.mochila) == 101


def test_remote_mission_pickup_uses_normal_progress(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    o = Objeto("mision", "case", p.j.x + 100, p.j.y)
    p.objetos.append(o)
    p.mision = {"objeto": o, "recogido": False}
    p.cheat_collect()
    assert p.mision["recogido"] and p.mision["objeto"] is None


def test_collects_dropped_weapon_and_ammunition(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    ident = next(a["id"] for a in p.datos["armas"] if a["tipo"] == "fuego")
    for tipo, amount in (("arma", 10), ("municion", 20)):
        o = Objeto(tipo, tipo, p.j.x + 100, p.j.y)
        o.arma = ident
        o.valor = amount
        p.objetos.append(o)
        p.cheat_collect()
    ammo = p.j.armas[ident]
    assert ammo["cargador"] + ammo["reserva"] == 30


def test_mission_timed_container_is_collected_without_opening_wait(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    o = Objeto("mision", "safe", p.j.x + 100, p.j.y)
    p.objetos.append(o)
    p.mision = {"objeto": o, "recogido": False, "paso": 0,
                "def": {"pasos": [{"tipo": "recoger", "objeto": "safe", "tarda": 30}]}}
    p.cheat_collect()
    assert p.mision["recogido"] and not p.mision.get("abriendo")


def test_contact_spares_civilians_friends_and_sports(app):
    p = fresh(app)
    hostile = enemy(p)
    people = [enemy(p, t) for t in ("civil", "aliado", "perro")]
    sport = enemy(p)
    sport.deportivo = True
    dummy = enemy(p)
    dummy.inofensivo = True
    p.cheat_step()
    assert not hostile.muerto
    p.cfg["cheat_contacto"] = True
    p.cheat_step()
    assert hostile.muerto
    assert all(not q.muerto for q in people + [sport, dummy])


def test_contact_does_not_trigger_inside_vehicle(app):
    p = fresh(app)
    p.cfg["cheat_contacto"] = True
    p.j.veh = car(p)
    q = enemy(p)
    p.cheat_step()
    assert not q.muerto


def test_growth_changes_base_health_damage_and_skills(app):
    p = fresh(app)
    p.cfg["cheat_crecer"] = True
    before = p.j.salud_max
    q = enemy(p)
    p.danar_persona(q, 100)
    assert p.j.cheat_bajas == 1 and p.j.salud_max == before + 1
    assert p.nivel("resistencia") >= 1
    q2 = enemy(p)
    p.danar_persona(q2, 1)
    assert q2.salud == 47  # base hit 1 + earned damage 2


def test_growth_toggle_suspends_and_restores_without_stacking(app):
    p = fresh(app)
    p.j.cheat_bajas = 7
    p.cfg["cheat_crecer"] = True
    before = p.j.salud_max
    p.cheat_sync_growth()
    p.cheat_sync_growth()
    assert p.j.salud_max == before + 7
    p.cfg["cheat_crecer"] = False
    p.cheat_sync_growth()
    assert p.j.salud_max == before and p.cheat_growth() == 0
    p.cfg["cheat_crecer"] = True
    p.cheat_sync_growth()
    assert p.j.salud_max == before + 7 and p.j.cheat_bajas == 7


def test_growth_saved_and_restored(app):
    p = fresh(app)
    p.cfg["cheat_crecer"] = True
    p.j.cheat_bajas = 40
    p.cheat_sync_growth()
    d = copy.deepcopy(p.a_dict())
    app.empezar_partida(d)
    loaded = app.partida
    loaded.cheat_sync_growth()
    assert loaded.j.cheat_bajas == 40 and loaded.j.salud_max == p.j.salud_max
    loaded.cfg["cheat_crecer"] = False
    loaded.cheat_sync_growth()
    assert loaded.j.salud_max == p.j.salud_max - 40


def test_growth_eventually_produces_one_hit_kills(app):
    p = fresh(app)
    p.cfg["cheat_crecer"] = True
    p.j.cheat_bajas = 500
    q = enemy(p)
    q.salud = 1000
    p.danar_persona(q, 1)
    assert q.muerto


def test_training_targets_and_sports_do_not_award_growth(app):
    p = fresh(app)
    p.cfg["cheat_crecer"] = True
    for flag in ("inofensivo", "deportivo"):
        q = enemy(p)
        setattr(q, flag, True)
        p.danar_persona(q, 100)
    assert p.j.cheat_bajas == 0


def test_destroyed_vehicle_passenger_counts_for_growth(app):
    p = fresh(app)
    p.cfg["cheat_crecer"] = True
    v = car(p)
    q = Persona("enemigo", v.x + 100, v.y)
    v.pasajeros = [q]
    p.explotar(v)
    assert q.muerto and p.j.cheat_bajas == 1


def test_vehicle_repaired_on_entry_and_protected_until_exit(app):
    p = fresh(app)
    p.cfg["invulnerable"] = True
    v = car(p)
    v.salud = 1
    v.pinchada = v.revision_debida = True
    p._subir(v, False, callar=True)
    assert v.salud == v.salud_max and not v.pinchada and not v.revision_debida
    p.danar_vehiculo(v, 100000)
    p.pinchar(v)
    p.explotar(v)
    assert p.j.veh is v and not v.muerto and v.ardiendo < 0 and v.salud == v.salud_max and not v.pinchada
    p.salir_vehiculo(forzado=True)
    p.danar_vehiculo(v, 1)
    assert v.salud < v.salud_max


def test_other_vehicles_take_damage_normally(app):
    p = fresh(app)
    p.cfg["invulnerable"] = True
    p.j.veh = car(p)
    other = car(p)
    before = other.salud
    p.danar_vehiculo(other, 10)
    assert other.salud == before - 10


def test_arrest_retains_all_inventory_even_high_wanted(app):
    p = fresh(app)
    p.cfg["cheat_conservar"] = True
    p.cfg["sin_policia"] = False
    p.j.armas.update({a["id"]: {"cargador": 2, "reserva": 20} for a in p.datos["armas"]})
    p.j.arma = next(a["id"] for a in p.datos["armas"] if a["tipo"] == "fuego")
    p.j.blindaje = 99
    p.j.sustancias = {"alcohol": 3, "cannabis": 4}
    p.j.mochila = [{"id": next(iter(CATALOGO)), "robado": True}]
    before = copy.deepcopy({k: getattr(p.j, k) for k in ("armas", "arma", "blindaje", "objetos", "sustancias", "mochila")})
    p.j.estrellas = 5
    p.detener(sin_trato=True, rendicion=True)
    assert all(getattr(p.j, k) == v for k, v in before.items())
    assert p.j.stats["detenciones"] == 1 and p.j.antecedentes


def test_arrest_confiscates_with_toggle_off(app):
    p = fresh(app)
    ident = next(a["id"] for a in p.datos["armas"] if a["tipo"] == "fuego")
    p.j.armas[ident] = {"cargador": 2, "reserva": 20}
    p.j.arma = ident
    p.detener(sin_trato=True)
    assert ident not in p.j.armas


def test_skill_study_can_repeat_same_day(app):
    p = fresh(app)
    p.j.curso_dia = p.dia
    before = p.j.hab["resistencia"]
    p.curso("resistencia")
    assert p.j.hab["resistencia"] == before
    p.cfg["cheat_estudiar"] = True
    p.curso("resistencia")
    first = p.j.hab["resistencia"]
    p.curso("resistencia")
    assert first > before and p.j.hab["resistencia"] > first


def test_qualification_sessions_repeat_immediately(app):
    p = fresh(app)
    p.cfg["cheat_estudiar"] = p.cfg["cheat_admision"] = True
    t = {"id": "test", "nombre": "Test", "sesiones": 4, "horas": 1, "precio": 10, "prestigio": 100}
    for i in range(4):
        p.hon_estudiar(t)
    assert p.j.titulos["test"]["ok"] and p.j.titulos["test"]["s"] == 4
    p.hon_estudiar(t)
    assert p.j.titulos["test"]["s"] == 4


def test_academy_ignores_standing_but_preserves_prerequisites(app):
    p = fresh(app)
    p.j.ciudadania = 0
    p.j.estrellas = 5
    t = {"id": "test", "nombre": "Test", "prestigio": 100}
    assert p.hon_titulo_motivo(t)
    p.cfg["cheat_admision"] = True
    assert not p.hon_titulo_motivo(t)
    t["requiere"] = "basic"
    assert p.hon_titulo_motivo(t)


def test_academy_entry_bypasses_closed_and_banned(app):
    p = fresh(app)
    academy = next(l for l in p.lugares.values() if l.tipo == "academia")
    p.cfg["cheat_admision"] = True
    p.lugar_abierto = lambda l: False
    p.entrada_vetada = lambda l: True
    p.hon_negativa = lambda l: True
    menus_juego.lugar(p, academy)
    assert app.pila[-1] is not p


def test_u_teleports_to_q_target(app):
    p = fresh(app)
    p.cfg["cheat_teleport"] = True
    q = enemy(p, distance=30)
    p.fijar(callar=True)
    assert p.objetivo is q
    p.tecla(type("Event", (), {"key": pygame.K_u, "mod": 0})())
    assert q.dist(*p.pos()) < 10


def test_u_teleports_to_gps(app):
    p = fresh(app)
    p.cfg["cheat_teleport"] = True
    l = next(l for l in p.mundo.lugares.values() if math.hypot(l.x - p.j.x, l.y - p.j.y) > 30)
    p.fijar_gps(l.x, l.y, l.nombre, callar=True)
    p.cheat_travel()
    assert math.hypot(p.j.x - l.x, p.j.y - l.y) < 10


def test_u_without_cheat_keeps_walking(app):
    p = fresh(app)
    l = next(iter(p.mundo.lugares.values()))
    p.fijar_gps(l.x, l.y, l.nombre, callar=True)
    before = p.pos()
    p.tecla(type("Event", (), {"key": pygame.K_u, "mod": 0})())
    assert p.pos() == before and p.paseo_auto


def test_lethal_runover_of_enemy_and_police(app):
    p = fresh(app)
    p.cfg["cheat_atropellar"] = True
    for tipo in ("enemigo", "policia"):
        q = enemy(p, tipo)
        q.salud = 10000
        p.danar_persona(q, 24, atropello=True)
        assert q.muerto


def test_runover_off_keeps_normal_damage(app):
    p = fresh(app)
    q = enemy(p)
    p.danar_persona(q, 24, atropello=True)
    assert not q.muerto and q.salud == 26


def test_actual_vehicle_collision_defeats_enemies_and_spares_allies(app):
    p = fresh(app)
    p.cfg["cheat_atropellar"] = True
    p.cfg["invulnerable"] = True
    v = car(p)
    p.j.veh = v
    v.vel = 4
    q = enemy(p)
    q.salud = 10000
    ally = enemy(p, "aliado")
    p._choques_jugador(v)
    assert q.muerto and not ally.muerto and v.salud == v.salud_max


def test_player_no_damage_still_works(app):
    p = fresh(app)
    p.cfg["invulnerable"] = True
    p.danar_jugador(10000, None)
    assert p.j.salud == p.j.salud_max and not p.transicion


def test_expunge_is_voluntary_and_retains_lifetime_stats(app):
    p = fresh(app)
    p.j.antecedentes = [{"d": 1, "g": 3, "t": "test", "c": 100}]
    p.j.stats["detenciones"] = 10
    p.cheat_expunge()
    assert p.j.antecedentes
    p.cfg["cheat_borrar"] = True
    assert p.j.antecedentes  # enabling is not the action
    police = next(l for l in p.lugares.values() if l.tipo == "comisaria")
    menus_juego._comisaria(p, police)
    m = app.pila[-1]
    action = next(o for o in m.opciones if o.texto in ("Borrar antecedentes penales", "Expunge criminal record"))
    action.accion()
    assert not p.j.antecedentes and p.j.stats["detenciones"] == 10


def test_ngplus_keeps_growth_qualifications_and_business_upgrades(app):
    p = fresh(app)
    p.cfg["cheat_ngplus"] = p.cfg["cheat_crecer"] = True
    p.j.cheat_bajas = 23
    p.cheat_sync_growth()
    p.j.titulos = {"test": {"s": 4, "ok": 3}, "partial": {"s": 2, "ok": 0}}
    p.j.empresa = {"bar_puerto": {"nivel": 3, "emp": 2, "rep": 85, "precios": "altos", "visto": 99}}
    p.j.propiedades.append("bar_puerto")
    old = copy.deepcopy(p.a_dict())
    read = menus_juego.leer_ranura
    try:
        menus_juego.leer_ranura = lambda r, *args: copy.deepcopy(old)
        menus_juego.partida_mas(app)
        app.pila[-1].opciones[0].accion()
    finally:
        menus_juego.leer_ranura = read
    new = app.partida
    assert new.j.cheat_bajas == 23 and new.j.salud_max == p.j.salud_max
    assert new.j.titulos == p.j.titulos
    assert new.j.empresa["bar_puerto"]["nivel"] == 3
    assert new.j.empresa["bar_puerto"]["emp"] == 2 and new.j.empresa["bar_puerto"]["visto"] == new.dia


def test_all_cheats_disabled_in_online_session(app):
    p = fresh(app)
    for row in OPTIONS:
        p.cfg[row[0]] = True
    p.cfg["invulnerable"] = True
    p.en_servidor = True
    assert not any(p.cheat_on(row[0]) for row in OPTIONS)
    assert not p.cheat_on("invulnerable")


def test_old_character_save_gets_safe_defaults(app):
    old = Jugador().a_dict()
    old.pop("cheat_bajas")
    old.pop("cheat_salud_aplicada")
    j = Jugador()
    j.de_dict(old)
    assert j.cheat_bajas == 0 and j.cheat_salud_aplicada == 0


def sea(p):
    from juego.mundo import Mar
    p.mundo = Mar({"id": "test_sea", "nombre": "Test sea", "ancho": 800, "alto": 600,
                   "lugares": [], "islas": [{"x": 400, "y": 300, "r": 60}]})
    p.j.x, p.j.y = 200, 300
    return p.mundo


def test_water_route_goes_around_island(app):
    p = fresh(app)
    world = sea(p)
    from juego.cheat_vehicles import segment_distance, water_route
    route = water_route(world, (200, 300), (600, 300))
    assert len(route) > 1
    last = (200, 300)
    for point in route:
        assert segment_distance((400, 300), last, point) >= 63
        last = point
    assert route[-1] == (600, 300)


def test_water_autopilot_navigates_and_stops_without_grounding(app):
    p = fresh(app)
    sea(p)
    model = next(m for m in p.datos["vehiculos"] if m.get("barco"))
    v = Vehiculo(model, 200, 300)
    p.j.veh = v
    p.cfg["cheat_piloto_agua"] = p.cfg["piloto_gps"] = True
    p.gps = {"dest": (600, 300), "nombre": "Port", "radio": 6}
    for _ in range(2400):
        p.conducir(0.05)
        assert p.mundo.superficie(v.x, v.y) == "agua"
        if math.hypot(v.x - 600, v.y - 300) <= 6 and v.vel == 0:
            break
    assert math.hypot(v.x - 600, v.y - 300) <= 6 and v.vel == 0


def test_water_autopilot_is_independently_switchable_and_manual_override(app):
    p = fresh(app)
    sea(p)
    v = Vehiculo(next(m for m in p.datos["vehiculos"] if m.get("barco")), 200, 300)
    p.j.veh = v
    p.cfg["piloto_gps"] = True
    p.gps = {"dest": (300, 300), "nombre": "Port", "radio": 6}
    assert not p.cheat_drive(v, 0.05, set())
    p.cfg["cheat_piloto_agua"] = True
    assert not p.cheat_drive(v, 0.05, {pygame.K_LEFT})
    assert p.cheat_drive(v, 0.05, set())
    p.cfg["cheat_piloto_agua"] = False
    assert not p.cheat_drive(v, 0.05, set()) and v.vel == 0


def test_invulnerability_protects_water_vehicle(app):
    p = fresh(app)
    sea(p)
    v = Vehiculo(next(m for m in p.datos["vehiculos"] if m.get("barco")), 200, 300)
    p.cfg["invulnerable"] = True
    v.salud = 1
    p._subir(v, False, callar=True)
    p.danar_vehiculo(v, 100000)
    p.explotar(v)
    assert p.j.veh is v and v.salud == v.salud_max
    p.salir_vehiculo(forzado=True)
    p.danar_vehiculo(v, 10)
    assert v.salud < v.salud_max


def test_flying_car_uses_copied_model_and_restores_on_exit(app):
    p = fresh(app)
    p.cfg["cheat_volar"] = True
    v = car(p)
    original = v.modelo
    p._subir(v, False, callar=True)
    assert v.modelo.get("vuela") and not original.get("vuela") and v.modelo is not original
    p.salir_vehiculo(forzado=True)
    assert v.modelo is original and not v.modelo.get("vuela")


def test_flying_boat_uses_flight_controls_and_can_land_on_water(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    sea(p)
    p.cfg["cheat_volar"] = True
    v = Vehiculo(next(m for m in p.datos["vehiculos"] if m.get("barco")), 200, 300)
    p._subir(v, False, callar=True)
    v.fase, v.alt, v.vel = "vuelo", 30, 0
    assert p.vuelo_aterrizar(v) and v.fase == "aterrizando"
    assert v.modelo.get("vuela")


def test_disabling_flying_car_descends_and_restores_ground_model(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    p.cfg["cheat_volar"] = True
    v = car(p)
    original = v.modelo
    p._subir(v, False, callar=True)
    v.fase, v.alt = "vuelo", 40
    p.cfg["cheat_volar"] = False
    for _ in range(300):
        p.conducir(0.05)
        if v.modelo is original:
            break
    assert p.j.veh is v and v.modelo is original and v.alt == 0


def test_flying_car_takes_off_with_normal_aircraft_keys(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    p.cfg["cheat_volar"] = True
    v = car(p)
    p._subir(v, False, callar=True)
    app.teclas = {pygame.K_UP}
    for _ in range(400):
        p.conducir(0.05)
        if v.fase == "vuelo":
            break
    app.teclas = set()
    assert v.fase == "vuelo" and v.alt > 0


def test_air_gps_autopilot_takes_off_flies_and_lands(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    model = next(m for m in p.datos["vehiculos"] if m.get("vuela") and not __import__("juego.vuelo", fromlist=["aeronave"]).aeronave(m)["pista"])
    v = Vehiculo(model, p.j.x, p.j.y)
    p._subir(v, False, callar=True)
    goal = p.mundo.punto_libre(v.x + 100, v.y + 100)
    p.gps = {"dest": goal, "nombre": "Landing", "radio": 8}
    p.cfg["piloto_gps"] = p.cfg["cheat_piloto_aire"] = True
    airborne = False
    for _ in range(1600):
        p.conducir(0.05)
        airborne |= v.alt > 0
        if airborne and math.dist((v.x, v.y), goal) <= 8 and v.fase == "tierra":
            break
    assert airborne and math.dist((v.x, v.y), goal) <= 8
    assert p.j.veh is v and v.vel == 0 and v.fase == "tierra"


def test_invulnerability_protects_local_aircraft_crash_and_forced_landing(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    p.cfg["invulnerable"] = True
    v = Vehiculo(next(m for m in p.datos["vehiculos"] if m.get("vuela")), p.j.x, p.j.y)
    p._subir(v, False, callar=True)
    v.fase, v.alt, v.forzoso = "aterrizando", 0, True
    p._vuelo_toca_tierra(v)
    assert v.salud == v.salud_max
    p._vuelo_caida(v)
    assert v.salud == v.salud_max and p.j.salud == p.j.salud_max


def test_intercity_flight_autopilot_and_damage_protection(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    p.cfg["invulnerable"] = True
    v = Vehiculo(next(m for m in p.datos["vehiculos"] if m.get("vuela")), p.j.x, p.j.y)
    p._subir(v, False, callar=True)
    destination = next(d for d in p.vuelo_destinos(v) if d["mapa"].id != p.mundo.id)
    from juego.vuelo_pantalla import Crucero
    cruise = Crucero(p, v, destination)
    assert cruise.auto
    cruise._dano(99, "collision")
    assert v.salud == v.salud_max
    original = list(cruise.pos)
    for _ in range(10):
        cruise.actualizar(0.05)
    assert cruise.auto and cruise.pos != original and v.salud == v.salud_max
    cruise._forzoso()
    assert v.salud == v.salud_max and p.j.salud == p.j.salud_max


def test_empty_vehicle_pursues_and_rams_hostile_enemy(app):
    p = fresh(app)
    p.cfg["cheat_vehiculos_aliados"] = True
    v = car(p)
    v.ia = "aparcado"
    q = enemy(p, distance=20)
    for _ in range(600):
        p.actualizar_vehiculos(0.05)
        if q.muerto:
            break
    assert q.muerto and p.j.veh is None


def test_empty_vehicle_toggle_stops_it_and_spares_player_and_allies(app):
    p = fresh(app)
    p.cfg["cheat_vehiculos_aliados"] = True
    v = car(p)
    q = enemy(p, distance=40)
    friend = enemy(p, "aliado", distance=2)
    p.actualizar_vehiculos(0.05)
    assert getattr(v, "_cheat_autonomous", False)
    p.cfg["cheat_vehiculos_aliados"] = False
    pos = (v.x, v.y)
    p.actualizar_vehiculos(0.05)
    assert v.vel == 0 and (v.x, v.y) == pos and not q.muerto and not friend.muerto
    assert p.j.salud == p.j.salud_max


def test_empty_vehicle_does_not_recruit_occupied_or_mission_vehicle(app):
    p = fresh(app)
    p.cfg["cheat_vehiculos_aliados"] = True
    enemy(p)
    occupied, mission = car(p), car(p)
    occupied.ocupado = True
    mission.tag = "objetivo"
    assert not p.cheat_empty_vehicle(occupied, 0.05)
    assert not p.cheat_empty_vehicle(mission, 0.05)


def test_abandoned_police_vehicle_targets_enemies_and_restores_on_toggle_off(app):
    p = fresh(app)
    p.cfg["cheat_vehiculos_aliados"] = True
    v = car(p)
    v.ia, v.desplegado, v.hostil = "policia", True, True
    q = enemy(p, distance=50)
    assert p.cheat_empty_vehicle(v, 0.05) and not v.hostil
    p.cfg["cheat_vehiculos_aliados"] = False
    assert not p.cheat_empty_vehicle(v, 0.05)
    assert v.vel == 0 and v.hostil and not q.muerto


def test_airplane_autopilot_can_take_off_with_runway_model(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    from juego.vuelo import aeronave
    model = next(m for m in p.datos["vehiculos"] if m.get("vuela") and aeronave(m)["pista"])
    v = Vehiculo(model, p.j.x, p.j.y)
    p._subir(v, False, callar=True)
    p.gps = {"dest": p.mundo.punto_libre(v.x + 300, v.y + 100), "nombre": "Airport", "radio": 8}
    p.cfg["piloto_gps"] = p.cfg["cheat_piloto_aire"] = True
    for _ in range(1000):
        p.conducir(0.05)
        if v.fase == "vuelo":
            break
    assert v.fase == "vuelo" and v.alt > 0


def test_disabling_flight_over_sea_waits_for_land_for_a_car(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    sea(p)
    p.cfg["cheat_volar"] = True
    v = car(p)
    p._subir(v, False, callar=True)
    v.fase, v.alt = "vuelo", 40
    p.cfg["cheat_volar"] = False
    p.cheat_sync_flight()
    assert v.modelo.get("vuela") and v.fase == "vuelo" and v.alt == 40

