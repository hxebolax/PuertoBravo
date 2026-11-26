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
    p.cfg["cheat_mochila"] = True
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


def owned_ammo(p, kind, clip=0, reserve=0):
    a = next(a for a in p.datos["armas"] if a["tipo"] == kind)
    p.j.armas[a["id"]] = {"cargador": clip, "reserva": reserve}
    p.j.arma = a["id"]
    p.j.t_ataque = 0
    return a, p.j.armas[a["id"]]


def ammo_drop(p, ident, amount, kind="municion"):
    o = Objeto(kind, kind, p.j.x + 100, p.j.y)
    o.arma, o.valor = ident, amount
    p.objetos.append(o)
    return o


def test_new_ammo_and_backpack_options_registered_and_default_off(app):
    p = fresh(app)
    keys = {"cheat_municion", "cheat_explosivos", "cheat_mochila"}
    assert keys <= {row[0] for row in OPTIONS}
    for enabled in keys:
        assert all(p.cfg[key] is False for key in keys)
        p.cfg[enabled] = True
        assert all(p.cfg[key] is False for key in keys - {enabled})
        p.cfg[enabled] = False


def test_infinite_firearm_shoots_at_zero_without_creating_or_spending_ammo(app):
    p = fresh(app)
    p.cfg["cheat_municion"] = True
    a, m = owned_ammo(p, "fuego")
    sounds = []
    p.son = lambda name, *args, **kwargs: sounds.append(name)
    for clip, reserve in ((0, 0), (2, 3)):
        m.update(cargador=clip, reserva=reserve)
        before = copy.deepcopy(m)
        for _ in range(3):
            p.j.t_ataque = 0
            p.atacar()
            assert m == before and p.j.t_ataque == a["cadencia"]
    assert sounds.count(a["sonido"]) == 6 and "sin_balas" not in sounds


def test_infinite_firearm_empty_magazine_still_damages_target(app):
    from juego import combate
    p = fresh(app)
    p.cfg["cheat_municion"] = True
    a, m = owned_ammo(p, "fuego")
    q = enemy(p)
    q.salud = 10000
    p.objetivo = q
    before = q.salud
    random_roll = combate.random.random
    try:
        combate.random.random = lambda: 0.0
        p.atacar()
    finally:
        combate.random.random = random_roll
    assert q.salud < before and m == {"cargador": 0, "reserva": 0}


def test_infinite_builtin_throwables_and_rockets_launch_with_zero_ammo(app):
    p = fresh(app)
    p.cfg["cheat_explosivos"] = True
    explosives = [a for a in p.datos["armas"] if a["tipo"] == "explosivo"]
    assert explosives
    for a in explosives:
        p.j.arma = a["id"]
        for clip, reserve in ((0, 0), (1, 2)):
            m = p.j.armas[a["id"]] = {"cargador": clip, "reserva": reserve}
            before = copy.deepcopy(m)
            for _ in range(2):
                n = len(p.explosiones)
                p.j.t_ataque = 0
                p.atacar()
                assert len(p.explosiones) == n + 1
                assert p.explosiones[-1]["arma"] == a["id"] and m == before


def test_mod_explosive_infinity_uses_weapon_type(app):
    p = fresh(app)
    model = copy.deepcopy(next(a for a in p.datos["armas"] if a["tipo"] == "explosivo"))
    model.update(id="test_mod_throwable", nombre="Test mod throwable", cargador=2, balas=7)
    p.armas_d[model["id"]] = model
    p.orden_armas.append(model["id"])
    p.j.arma = model["id"]
    m = p.j.armas[model["id"]] = {"cargador": 0, "reserva": 0}
    p.cfg["cheat_municion"] = True
    assert not p.cheat_infinite_ammo()
    p.cfg["cheat_explosivos"] = True
    assert p.cheat_infinite_ammo() and p.cheat_ammo_capacity(model["id"]) == 9
    p.atacar()
    assert len(p.explosiones) == 1 and p.explosiones[0]["arma"] == model["id"]
    assert m == {"cargador": 0, "reserva": 0}


def test_ammo_toggles_are_independent_and_switching_off_restores_consumption(app):
    p = fresh(app)
    for kind, option, other in (("fuego", "cheat_municion", "cheat_explosivos"),
                                ("explosivo", "cheat_explosivos", "cheat_municion")):
        a, m = owned_ammo(p, kind, 1, 2)
        p.cfg[option], p.cfg[other] = False, True
        assert not p.cheat_infinite_ammo(a["id"])
        p.atacar()
        assert m["cargador"] + m["reserva"] == 2
        p.cfg[option] = True
        before = copy.deepcopy(m)
        p.j.t_ataque = 0
        p.atacar()
        assert m == before
        p.cfg[option] = False
        p.j.t_ataque = 0
        if kind == "fuego":
            p.recargar()
            p.j.t_ataque = 0
        p.atacar()
        assert m["cargador"] + m["reserva"] == 1


def test_infinite_reload_explains_no_reload_and_keeps_real_counts(app):
    p = fresh(app)
    said = []
    p.decir = lambda message, *args, **kwargs: said.append(message)
    for kind, option in (("fuego", "cheat_municion"), ("explosivo", "cheat_explosivos")):
        a, m = owned_ammo(p, kind, 0, 2)
        p.cfg[option] = True
        p.recargar()
        assert m == {"cargador": 0, "reserva": 2} and p.j.t_ataque == 0
        assert said and ("recargar" in said[-1].lower() or "reload" in said[-1].lower())
        p.cfg[option] = False
        p.recargar()
        assert m["cargador"] > 0 and m["cargador"] + m["reserva"] == 2


def test_online_attacks_consume_ammo_and_restore_normal_pickup_and_bag_limits(app):
    p = fresh(app)
    for key in ("cheat_municion", "cheat_explosivos", "cheat_mochila"):
        p.cfg[key] = True
    normal_bag = p.moc_capacidad()
    p.en_servidor = True
    # Exercise normal combat without connecting to a network or spawning peers.
    p.sv_ruido = lambda *args: None
    p.sv_objetivos = lambda *args: []
    for kind in ("fuego", "explosivo"):
        a, m = owned_ammo(p, kind, 1, 1)
        assert not p.cheat_infinite_ammo() and p.cheat_ammo_room(a["id"]) is None
        p.atacar()
        assert m["cargador"] + m["reserva"] == 1
        amount = p.cheat_ammo_capacity(a["id"]) + 5
        assert p.sumar_municion(a["id"], amount) == amount
        m.update(cargador=0, reserva=0)
        n = len(p.explosiones)
        p.j.t_ataque = 0
        p.atacar()
        assert m == {"cargador": 0, "reserva": 0} and len(p.explosiones) == n
    p.cfg["cheat_mochila"] = False
    expected_bag = p.moc_capacidad()
    p.cfg["cheat_mochila"] = True
    assert p.moc_capacidad() == expected_bag <= normal_bag
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": False} for _ in range(expected_bag + 1)]
    before = copy.deepcopy(p.j.mochila)
    assert not p.moc_meter(ident, callar=True) and p.j.mochila == before


def test_ammo_cheats_never_grant_an_unowned_weapon(app):
    p = fresh(app)
    p.cfg["cheat_municion"] = p.cfg["cheat_explosivos"] = True
    before = copy.deepcopy(p.j.armas)
    for a in p.datos["armas"]:
        if a["tipo"] not in ("fuego", "explosivo"):
            continue
        p.j.arma, p.j.t_ataque = a["id"], 0
        assert not p.cheat_infinite_ammo() and p.cheat_ammo_room(a["id"]) is None
        assert p.sumar_municion(a["id"], 100) == 0
        p.atacar()
        assert p.j.armas == before and not p.explosiones


def test_ammo_pickup_capacity_uses_normal_reserve_and_expanded_magazine(app):
    p = fresh(app)
    for kind, option in (("fuego", "cheat_municion"), ("explosivo", "cheat_explosivos")):
        a, m = owned_ammo(p, kind)
        ident = a["id"]
        expected = int(a.get("cargador", 0)) + int(a.get("balas", 0))
        assert p.cheat_ammo_capacity(ident) == expected
        assert p.cheat_ammo_room(ident) is None
        p.cfg[option] = True
        assert p.cheat_ammo_room(ident) == expected
        m["ampliado"] = True
        expanded = p.capacidad(ident) + int(a.get("balas", 0))
        assert p.cheat_ammo_capacity(ident) == expanded
        if kind == "fuego":
            assert expanded > expected
        else:
            assert expanded == expected
        m.update(cargador=1, reserva=1)
        assert p.cheat_ammo_room(ident) == max(0, expanded - 2)


def test_real_ammo_additions_stop_at_ceiling_and_resume_uncapped_when_off(app):
    p = fresh(app)
    for kind, option in (("fuego", "cheat_municion"), ("explosivo", "cheat_explosivos")):
        a, m = owned_ammo(p, kind)
        ident = a["id"]
        p.cfg[option] = True
        cap = p.cheat_ammo_capacity(ident)
        m.update(cargador=1, reserva=max(0, cap - 3))
        before = copy.deepcopy(m)
        assert p.sumar_municion(ident, 100) == 2
        assert m["cargador"] == before["cargador"]
        assert m["cargador"] + m["reserva"] == cap
        assert p.cheat_ammo_room(ident) == 0
        at_cap = copy.deepcopy(m)
        assert p.sumar_municion(ident, 5) == 0 and m == at_cap
        p.cfg[option] = False
        assert p.cheat_ammo_room(ident) is None
        assert p.sumar_municion(ident, 5) == 5
        assert m["cargador"] + m["reserva"] == cap + 5


def test_enabling_infinity_preserves_preexisting_over_capacity_ammo(app):
    p = fresh(app)
    for kind, option in (("fuego", "cheat_municion"), ("explosivo", "cheat_explosivos")):
        a, m = owned_ammo(p, kind, 1, 1000)
        before = copy.deepcopy(m)
        p.cfg[option] = True
        assert p.cheat_ammo_room(a["id"]) == 0
        assert p.sumar_municion(a["id"], 50) == 0 and m == before
        o = ammo_drop(p, a["id"], 50)
        p.recoger(o)
        assert o.recogido and o not in p.objetos and m == before
        p.atacar()
        assert m == before
        p.cfg[option] = False
        assert m == before


def test_full_ammo_pickups_are_consumed_once_without_overflow(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    for kind, option in (("fuego", "cheat_municion"), ("explosivo", "cheat_explosivos")):
        a, m = owned_ammo(p, kind)
        ident = a["id"]
        p.cfg[option] = True
        cap = p.cheat_ammo_capacity(ident)
        m.update(cargador=1, reserva=cap - 2)
        pickups = [ammo_drop(p, ident, 100), ammo_drop(p, ident, 100, "arma")]
        p.cheat_collect()
        assert m["cargador"] + m["reserva"] == cap
        assert all(o.recogido and o not in p.objetos for o in pickups)
        at_cap = copy.deepcopy(m)
        for o in pickups:
            p.recoger(o)
        p.cheat_collect()
        assert m == at_cap
        extra = ammo_drop(p, ident, 5)
        p.cheat_collect()
        assert extra.recogido and extra not in p.objetos and m == at_cap
        p.cfg[option] = False
        uncapped = ammo_drop(p, ident, 5)
        p.cheat_collect()
        assert uncapped.recogido and m["cargador"] + m["reserva"] == cap + 5


def test_new_weapon_pickups_acquire_only_real_capped_ammo(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    for kind, option in (("fuego", "cheat_municion"), ("explosivo", "cheat_explosivos")):
        a = next(a for a in p.datos["armas"] if a["tipo"] == kind)
        ident = a["id"]
        p.cfg[option] = True
        assert ident not in p.j.armas and not p.cheat_infinite_ammo(ident)
        o = ammo_drop(p, ident, 1000, "arma")
        p.cheat_collect()
        assert o.recogido and ident in p.j.armas and p.cheat_infinite_ammo(ident)
        m = p.j.armas[ident]
        assert m["cargador"] + m["reserva"] == p.cheat_ammo_capacity(ident)
        assert set(m) == {"cargador", "reserva"}


def test_ammo_only_drop_does_not_acquire_a_missing_weapon(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = p.cfg["cheat_municion"] = p.cfg["cheat_explosivos"] = True
    before = copy.deepcopy(p.j.armas)
    for kind in ("fuego", "explosivo"):
        ident = next(a["id"] for a in p.datos["armas"] if a["tipo"] == kind)
        o = ammo_drop(p, ident, 100)
        p.cheat_collect()
        assert o.recogido and o not in p.objetos and p.j.armas == before


def test_unlimited_backpack_grows_with_actual_items_and_integer_headroom(app):
    p = fresh(app)
    base = p.moc_capacidad()
    p.cfg["cheat_mochila"] = True
    ident = max(CATALOGO, key=lambda ident: CATALOGO[ident]["peso"])
    weight = CATALOGO[ident]["peso"]
    limit = base // weight + 6
    assert not p.j.mochila
    for n in range(limit):
        assert p.moc_meter(ident, robado=bool(n % 2), callar=True)
        capacity = p.moc_capacidad()
        assert type(capacity) is int and capacity >= p.moc_usado() + weight
        assert capacity <= max(base, p.moc_usado() + max(o["peso"] for o in CATALOGO.values()))
        assert len(p.j.mochila) == n + 1
        assert p.j.mochila[-1] == {"id": ident, "robado": bool(n % 2)}
    assert p.moc_usado() > base and all(set(o) == {"id", "robado"} for o in p.j.mochila)


def test_unlimited_backpack_off_retains_items_and_restores_admission_limits(app):
    p = fresh(app)
    base = p.moc_capacidad()
    ident = next(iter(CATALOGO))
    p.cfg["cheat_mochila"] = True
    while p.moc_usado() <= base:
        assert p.moc_meter(ident, robado=True, callar=True)
    before = copy.deepcopy(p.j.mochila)
    p.cfg["cheat_mochila"] = False
    assert p.moc_capacidad() == base and p.j.mochila == before
    assert not p.moc_meter(ident, callar=True) and p.j.mochila == before
    p.cfg["cheat_mochila"] = True
    assert p.moc_meter(ident, callar=True) and len(p.j.mochila) == len(before) + 1


def test_auto_collect_needs_separate_backpack_toggle_when_full(app):
    p = fresh(app)
    p.cfg["cheat_recoger"] = True
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": False} for _ in range(p.moc_capacidad() + 1)]
    o = Objeto("valor", "valuable", p.j.x + 100, p.j.y)
    o.item, o.robado = ident, True
    p.objetos.append(o)
    before = copy.deepcopy(p.j.mochila)
    for _ in range(3):
        p.cheat_collect()
    assert o in p.objetos and not getattr(o, "recogido", False) and p.j.mochila == before
    p.cfg["cheat_mochila"] = True
    p.cheat_collect()
    assert o.recogido and o not in p.objetos
    assert p.j.mochila == before + [{"id": ident, "robado": True}]
    p.cheat_collect()
    assert len(p.j.mochila) == len(before) + 1


def test_ammo_and_overfull_backpack_save_without_changing_item_schema(app):
    p = fresh(app)
    base = p.moc_capacidad()
    for key in ("cheat_municion", "cheat_explosivos", "cheat_mochila"):
        p.cfg[key] = True
    a, m = owned_ammo(p, "fuego", 0, 1000)
    m.update(ampliado=True, silenciador=True)
    owned_ammo(p, "explosivo", 0, 0)
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": bool(n % 2)} for n in range(base + 5)]
    arms, items = copy.deepcopy(p.j.armas), copy.deepcopy(p.j.mochila)
    app.empezar_partida(copy.deepcopy(p.a_dict()))
    loaded = app.partida
    assert loaded.j.armas == arms and loaded.j.mochila == items
    assert all(set(o) == {"id", "robado"} for o in loaded.j.mochila)
    assert loaded.cheat_ammo_room(a["id"]) == 0
    for key in ("cheat_municion", "cheat_explosivos", "cheat_mochila"):
        assert loaded.cfg[key] is True
        loaded.cfg[key] = False
    assert loaded.j.armas == arms and loaded.j.mochila == items
    assert loaded.moc_capacidad() == base


def test_new_game_plus_keeps_ammo_options_and_overfull_inventory(app):
    p = fresh(app)
    for key in ("cheat_ngplus", "cheat_municion", "cheat_explosivos", "cheat_mochila"):
        p.cfg[key] = True
    a, m = owned_ammo(p, "fuego", 0, 1000)
    m["ampliado"] = True
    owned_ammo(p, "explosivo", 0, 0)
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": True} for _ in range(100)]
    arms, items = copy.deepcopy(p.j.armas), copy.deepcopy(p.j.mochila)
    old = copy.deepcopy(p.a_dict())
    read = menus_juego.leer_ranura
    try:
        menus_juego.leer_ranura = lambda r, *args: copy.deepcopy(old)
        menus_juego.partida_mas(app)
        app.pila[-1].opciones[0].accion()
    finally:
        menus_juego.leer_ranura = read
    new = app.partida
    assert new.j.armas == arms and new.j.mochila == items
    assert all(new.cfg[key] is True for key in ("cheat_municion", "cheat_explosivos", "cheat_mochila"))
    assert new.cheat_ammo_room(a["id"]) == 0 and new.moc_libre() > 0


def test_duplicate_weapon_withdrawal_keeps_excess_ammo_in_home_storage(app):
    from juego.i18n import tr
    from juego.mochila import menu_armario
    p = fresh(app)
    a, m = owned_ammo(p, "fuego")
    ident = a["id"]
    p.cfg["cheat_municion"] = True
    cap = p.cheat_ammo_capacity(ident)
    m.update(cargador=1, reserva=cap - 3)
    home = next(l for l in p.lugares.values() if l.tipo == "casa")
    storage = p.almacen(home.id)["armas"]
    storage[ident] = {"cargador": 5, "reserva": 45, "ampliado": True}
    menu_armario(p, home)
    menu = app.pila[-1]

    def withdraw():
        label = tr('Sacar {nombre}').format(nombre=a["nombre"])
        next(o for o in menu.opciones if o.texto == label).accion()

    withdraw()
    assert m["cargador"] + m["reserva"] == cap
    assert storage[ident]["cargador"] + storage[ident]["reserva"] == 48
    assert storage[ident]["ampliado"] is True
    before = copy.deepcopy(storage[ident])
    withdraw()
    assert storage[ident] == before and m["cargador"] + m["reserva"] == cap
    p.cfg["cheat_municion"] = False
    withdraw()
    assert ident not in storage and m["cargador"] + m["reserva"] == cap + 48


def test_storage_withdraw_and_store_cycle_preserves_all_rounds_and_upgrades(app):
    from juego.i18n import tr
    from juego.mochila import menu_armario
    p = fresh(app)
    a, m = owned_ammo(p, "fuego")
    ident = a["id"]
    p.cfg["cheat_municion"] = True
    cap = p.cheat_ammo_capacity(ident)
    m.update(cargador=1, reserva=cap - 3, silenciador=True)
    home = next(l for l in p.lugares.values() if l.tipo == "casa")
    storage = p.almacen(home.id)["armas"]
    storage[ident] = {"cargador": 5, "reserva": 45, "ampliado": True}
    total = cap - 2 + 50
    menu_armario(p, home)
    menu = app.pila[-1]

    def action(template):
        label = tr(template).format(nombre=a["nombre"])
        next(o for o in menu.opciones if o.texto == label).accion()

    action('Sacar {nombre}')
    action('Guardar {nombre}')
    assert ident not in p.j.armas
    assert storage[ident]["cargador"] + storage[ident]["reserva"] == total
    assert storage[ident]["ampliado"] is True and storage[ident]["silenciador"] is True
    action('Sacar {nombre}')
    restored = p.j.armas[ident]
    assert ident not in storage and restored["cargador"] + restored["reserva"] == total
    assert restored["ampliado"] is True and restored["silenciador"] is True


def test_unlimited_inventory_merchandise_headroom_is_finite_and_over_one_hundred(app):
    p = fresh(app)
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": False} for _ in range(p.moc_capacidad() + 1)]
    p.j.sustancias = {"test_merchandise": 250}
    p.cfg["cheat_mochila"] = True
    before = copy.deepcopy(p.j.sustancias)
    room = p.hueco_mercancia(1000)
    assert type(room) is int and 1000 <= room < 10000
    assert p.j.sustancias == before
    p.j.sustancias["test_merchandise"] += 1000
    assert p.carga() == 1250 and p.hueco_mercancia(1) >= 1
    assert type(p.moc_capacidad()) is int and p.moc_capacidad() > p.moc_usado()
    before = copy.deepcopy(p.j.sustancias)
    p.cfg["cheat_mochila"] = False
    assert p.hueco_mercancia(1000) == 0 and p.j.sustancias == before
    p.cfg["cheat_mochila"] = True
    p.en_servidor = True
    assert p.hueco_mercancia(1000) == 0 and p.j.sustancias == before


def test_ammo_shop_caps_partial_purchase_and_does_not_charge_at_full_capacity(app):
    p = fresh(app)
    a, m = owned_ammo(p, "fuego")
    p.cfg["cheat_municion"] = True
    cap = p.cheat_ammo_capacity(a["id"])
    m.update(cargador=0, reserva=cap - 1)
    store = next(l for l in p.lugares.values() if l.tipo == "armeria")
    menus_juego._armeria(p, store)
    menu = app.pila[-1]

    def buy():
        next(o for o in menu.opciones if a["nombre"] in o.texto and o.texto.startswith(("Munici\u00f3n para ", "Ammunition for "))).accion()

    money = p.j.dinero
    buy()
    assert m["cargador"] + m["reserva"] == cap and p.j.dinero < money
    money, before = p.j.dinero, copy.deepcopy(m)
    buy()
    buy()
    assert p.j.dinero == money and m == before
    p.cfg["cheat_municion"] = False
    buy()
    assert p.j.dinero < money and m["cargador"] + m["reserva"] == cap + a["balas"]


def test_unlimited_inventory_withdraws_large_merchandise_batches_with_full_bag(app):
    from juego.i18n import tr
    from juego.mochila import menu_armario
    p = fresh(app)
    p.cfg["cheat_mochila"] = True
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": False} for _ in range(100)]
    p.j.sustancias = {"pastillas": 250}
    home = next(l for l in p.lugares.values() if l.tipo == "casa")
    storage = p.almacen(home.id)
    storage["sust"] = {"pastillas": 1000, "polvo": 25}
    menu_armario(p, home)
    menu = app.pila[-1]
    label = tr('Sacar mercanc\u00eda: hay {sum} unidades').format(sum=1025)
    next(o for o in menu.opciones if o.texto == label).accion()
    assert p.j.sustancias == {"pastillas": 1250, "polvo": 25}
    assert storage["sust"] == {} and len(p.j.mochila) == 100
    p.cfg["cheat_mochila"] = False
    storage["sust"] = {"pastillas": 10}
    menu.refrescar(False)
    label = tr('Sacar mercanc\u00eda: hay {sum} unidades').format(sum=10)
    next(o for o in menu.opciones if o.texto == label).accion()
    assert p.j.sustancias == {"pastillas": 1250, "polvo": 25}
    assert storage["sust"] == {"pastillas": 10}


def test_unlimited_inventory_supplier_purchase_above_normal_merchandise_cap(app):
    from juego import menus_adultos
    from juego.i18n import tr
    p = fresh(app)
    p.cfg["adultos"] = True
    app.aplicar_adultos()
    try:
        p.cfg["cheat_mochila"] = True
        ident = next(iter(CATALOGO))
        p.j.mochila = [{"id": ident, "robado": False} for _ in range(100)]
        substance = next(s for s in p.dato_adulto("sustancias") if not s.get("legal"))
        p.j.sustancias = {substance["id"]: 150}
        store = next(l for l in p.lugares.values() if l.tipo == "proveedor")
        menus_adultos.proveedor(p, store)
        next(o for o in app.pila[-1].opciones if o.texto.startswith(substance["nombre"] + ":")).accion()
        buy = next(o for o in app.pila[-1].opciones if o.texto == tr("Comprar 10"))
        money = p.j.dinero
        buy.accion()
        assert p.j.sustancias[substance["id"]] == 160 and p.j.dinero < money
        p.cfg["cheat_mochila"] = False
        money = p.j.dinero
        buy.accion()
        assert p.j.sustancias[substance["id"]] == 160 and p.j.dinero == money
    finally:
        p.cfg["adultos"] = False
        app.aplicar_adultos()


def test_unlimited_inventory_lab_production_above_normal_merchandise_cap(app):
    from juego import laboratorio
    from juego.i18n import tr
    from juego.menus import Menu, Opcion
    p = fresh(app)
    p.cfg["adultos"] = p.cfg["cheat_mochila"] = True
    p.cfg["minijuego_laboratorio"] = False
    home = next(l for l in p.lugares.values() if l.tipo == "casa")
    p.j.propiedades.append(home.id)
    p.j.laboratorios.append(home.id)
    p.j.material = 2
    p.j.sustancias = {"cristal": 150}
    ident = next(iter(CATALOGO))
    p.j.mochila = [{"id": ident, "robado": False} for _ in range(100)]
    p.delito = lambda *args, **kwargs: None
    laboratorio.opciones_casa(p, home, Menu, Opcion)[0].accion()
    substance = p.sustancia("cristal")
    label = tr('Fabricar {lower}').format(lower=substance["nombre"].lower())
    produce = next(o for o in app.pila[-1].opciones if o.texto == label)
    produce.accion()
    expected = int(round(4 + 12 * laboratorio.CALIDAD_SIN_MINIJUEGO))
    assert p.j.sustancias["cristal"] == 150 + expected and p.j.material == 1
    assert p.almacen(home.id)["sust"] == {}
    p.cfg["cheat_mochila"] = False
    produce.accion()
    assert p.j.sustancias["cristal"] == 150 + expected and p.j.material == 1
    p.cfg["cheat_mochila"] = True
    p.en_servidor = True
    produce.accion()
    assert p.j.sustancias["cristal"] == 150 + expected and p.j.material == 1



def test_all_business_upgrades_ignore_prestige_and_keep_cost(app):
    p = fresh(app)
    businesses = [l for l in p.lugares.values() if l.tipo == "negocio"]
    assert businesses
    p.j.ciudadania = 0
    p.j.titulos = {"direccion": {"s": 1, "ok": 1}}
    upgrade = p.hon_mejora(4)
    assert upgrade and upgrade.get("prestigio", 0) > 0
    for l in businesses:
        p.j.propiedades.append(l.id)
        e = p.hon_emp(l)
        e["nivel"] = 3
        p.cfg["cheat_negocios"] = False
        assert p.hon_mejora_motivo(l)
        p.cfg["cheat_negocios"] = True
        assert not p.hon_mejora_motivo(l)
        before = p.j.dinero
        p.hon_mejorar(l)
        assert e["nivel"] == 4
        assert p.j.dinero == before - p.hon_mejora_coste(l, upgrade)
        assert p.hon_mejora_motivo(l)  # Still respects the highest upgrade.


def test_business_upgrade_still_requires_qualification(app):
    p = fresh(app)
    l = next(l for l in p.lugares.values() if l.tipo == "negocio")
    p.j.propiedades.append(l.id)
    p.hon_emp(l)["nivel"] = 3
    p.j.ciudadania = 0
    p.j.titulos = {}
    p.cfg["cheat_negocios"] = True
    before = p.j.dinero
    assert p.hon_mejora_motivo(l)
    p.hon_mejorar(l)
    assert p.hon_emp(l)["nivel"] == 3 and p.j.dinero == before


def test_business_upgrade_prestige_cheat_disabled_online(app):
    p = fresh(app)
    l = next(l for l in p.lugares.values() if l.tipo == "negocio")
    p.hon_emp(l)["nivel"] = 3
    p.j.ciudadania = 0
    p.j.titulos = {"direccion": {"s": 1, "ok": 1}}
    p.cfg["cheat_negocios"] = True
    assert not p.hon_mejora_motivo(l)
    p.en_servidor = True
    assert p.hon_mejora_motivo(l)


def test_f_enters_q_police_helicopter_and_detaches_pursuit(app):
    p = fresh(app)
    app.vuelo_en_pruebas = True
    p.cfg["cheat_entrar"] = True
    p._heli_llega()
    v = p.heli["veh"]
    v.x, v.y = p.j.x + 100, p.j.y
    p.fijar(callar=True)
    assert p.objetivo is v
    assert v.volando and v.ocupado
    p.entrar_salir()
    assert p.j.veh is v and v in p.vehiculos
    assert p.heli is None and v.ia is None and v.tag is None
    assert not v.volando and not v.ocupado and not v.hostil
    assert v.fase == "vuelo" and v.alt > 0 and v.queroseno > 0
    assert p.objetivo is None
    xy = p.pos()
    p._helicoptero(0.05)
    p.actualizar_vehiculos(0.05)
    assert p.j.veh is v and v in p.vehiculos and p.pos() == xy
    p.cfg["cheat_entrar"] = False
    assert p.j.veh is v
    p.salir_vehiculo(forzado=True)
    assert p.j.veh is None and v in p.vehiculos and v.fase == "tierra"


def test_f_selected_vehicle_retains_stock_rules_off_and_online(app):
    p = fresh(app)
    p._heli_llega()
    v = p.heli["veh"]
    p.objetivo = v
    p.entrar_salir()
    assert p.j.veh is None and p.heli["veh"] is v
    p.cfg["cheat_entrar"] = True
    p.en_servidor = True
    assert p.cheat_enter_target() is False
    assert p.j.veh is None and p.heli["veh"] is v


def test_f_ignores_removed_destroyed_and_coordinate_only_targets(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = True
    v = car(p)
    v.x += 100
    p.objetivo = v
    v.muerto = True
    assert p.cheat_enter_target() is False
    v.muerto = False
    p.vehiculos.remove(v)
    assert p.cheat_enter_target() is False
    p.objetivo = None
    p.vehiculos.append(v)
    p.fijar_gps(v.x, v.y, v.nombre, callar=True)
    assert p.cheat_enter_target() is False
    assert p.j.veh is None


def test_f_q_target_takes_priority_over_gps_vehicle(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = True
    q = car(p)
    q.x += 60
    g = car(p)
    g.x += 40
    p.fijar_gps(g.x, g.y, g.nombre, sigue=g, cosa=g, callar=True)
    p.objetivo = q
    p.entrar_salir()
    assert p.j.veh is q and g in p.vehiculos

def test_f_enters_gps_u_vehicle_across_models_and_occupants(app):
    models = []
    p = fresh(app)
    for predicate in (lambda m: not m.get("vuela") and not m.get("barco"),
                      lambda m: m.get("barco"), lambda m: m.get("vuela")):
        models.append(next(m for m in p.datos["vehiculos"] if predicate(m)))
    for model in models:
        for ia in ("policia", "enemigos", "ambulancia", "trafico", "barco"):
            p = fresh(app)
            p.cfg["cheat_entrar"] = True
            p.cfg["invulnerable"] = True
            v = Vehiculo(model, p.j.x + 100, p.j.y + 70, ia=ia)
            v.cerrado = v.ocupado = v.hostil = True
            v.vel, v.ardiendo, v.salud = 35.0, 4.0, 1.0
            p.vehiculos.append(v)
            p.fijar_gps(v.x, v.y, v.nombre, sigue=v, cosa=v, callar=True)
            p.tecla_pie(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_u, mod=0), False)
            assert p.paseo_auto
            p.entrar_salir()
            assert p.j.veh is v and p.pos() == (v.x, v.y)
            assert not v.cerrado and not v.ocupado and not v.hostil
            assert not p.paseo_auto and v.vel == 0
            assert v.salud == v.salud_max and v.ardiendo < 0


def test_f_preserves_enemy_passengers_when_taking_their_vehicle(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = True
    v = car(p)
    v.x += 80
    v.ia, v.ocupado, v.hostil, v.tag = "enemigos", True, True, "enemigos"
    q = Persona("enemigo", v.x, v.y)
    q.hostil = True
    v.pasajeros = [q]
    p.objetivo = v
    p.entrar_salir()
    assert p.j.veh is v and q in p.personas and not q.muerto
    assert not v.pasajeros and v.tag is None
    assert p.j.stats["enemigos"] == 0

def test_f_enters_air_vehicle_after_u_teleport(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = p.cfg["cheat_teleport"] = True
    p._heli_llega()
    v = p.heli["veh"]
    p.fijar_gps(v.x, v.y, v.nombre, sigue=v, cosa=v, callar=True)
    p.tecla_pie(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_u, mod=0), False)
    assert p.j.veh is None and p.gps["cosa"] is v
    p.entrar_salir()
    assert p.j.veh is v and p.heli is None and v in p.vehiculos


def test_f_targeted_entry_stays_off_during_transition(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = True
    v = car(p)
    v.x += 60
    p.objetivo = v
    p.transicion = True
    assert p.cheat_enter_target() is False
    assert p.j.veh is None

def test_f_transfers_from_moving_and_airborne_vehicle(app):
    for flight in (False, True):
        p = fresh(app)
        p.cfg["cheat_entrar"] = p.cfg["invulnerable"] = True
        p.cfg["cheat_volar"] = flight
        app.vuelo_en_pruebas = flight
        old = car(p)
        original = old.modelo
        p._subir(old, False)
        old.vel = 25.0
        if flight:
            old.fase, old.alt = "vuelo", 80.0
            assert old.modelo.get("vuela")
        new = car(p)
        new.x += 100
        new.cerrado, new.ocupado = True, True
        p.objetivo = new
        p.entrar_salir()
        assert p.j.veh is new and p.pos() == (new.x, new.y)
        assert old in p.vehiculos and old.modelo is original and old.vel == 0
        assert not hasattr(old, "_cheat_ground_model")
        if flight:
            assert old.fase == "tierra" and old.alt == 0
        old.salud -= 10
        assert not p.cheat_repair(old)
        assert old.salud < old.salud_max
        assert p.cheat_repair(new)


def test_f_no_other_target_keeps_exit_and_landing_controls(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = True
    v = car(p)
    p._subir(v, False)
    v.vel = 20.0
    p.entrar_salir()
    assert p.j.veh is v
    v.vel = 0.0
    p.fijar_gps(v.x, v.y, v.nombre, sigue=v, cosa=v, callar=True)
    p.entrar_salir()
    assert p.j.veh is None
    p = fresh(app)
    app.vuelo_en_pruebas = True
    p.cfg["cheat_entrar"] = True
    model = next(m for m in p.datos["vehiculos"] if m.get("vuela"))
    v = Vehiculo(model, p.j.x, p.j.y)
    p.vehiculos.append(v)
    p._subir(v, False)
    v.fase, v.alt = "vuelo", 60.0
    p.objetivo = v
    p.entrar_salir()
    assert p.j.veh is v and v.fase == "aterrizando"


def test_f_transfers_from_friendly_passenger_seat(app):
    p = fresh(app)
    p.cfg["cheat_entrar"] = True
    p.pasajero = "friend"
    v = car(p)
    v.x += 70
    p.objetivo = v
    p.entrar_salir()
    assert p.pasajero is None and p.j.veh is v


# Append to test_cheats.py: uses its fresh/enemy helpers and imported entities.

def _reflection_shooter(p, weapon="pistola", tipo="enemigo", distance=10):
    q = enemy(p, tipo=tipo, distance=distance)
    q.arma = weapon
    q.estado = "quieto"
    q.t_disparo = 0
    q.punteria = 0
    q.salud = 100000
    return q


def test_reflected_firearm_hits_original_shooter_without_target_lock(app):
    p = fresh(app)
    p.cfg["cheat_reflejar"] = True
    q = _reflection_shooter(p)
    bystander = Persona("civil", p.j.x + 40, p.j.y)
    bystander.estado = "quieto"
    p.personas.append(bystander)
    p.objetivo = bystander
    health, other, shooter = p.j.salud, bystander.salud, q.salud
    p.actualizar_personas(0.01)
    assert p.j.salud == health and bystander.salud == other
    assert q.salud == shooter - p.armas_d[q.arma]["dano"] * 0.4
    assert q.t_disparo > 0


def test_reflection_protects_occupied_land_water_and_air_vehicles(app):
    for category in ("land", "water", "air"):
        for invulnerable in (False, True):
            p = fresh(app)
            p.cfg["cheat_reflejar"] = True
            p.cfg["invulnerable"] = invulnerable
            model = next(m for m in p.datos["vehiculos"] if
                         (bool(m.get("vuela")) if category == "air" else
                          bool(m.get("barco")) and not m.get("vuela") if category == "water" else
                          not m.get("vuela") and not m.get("barco")))
            v = Vehiculo(model, p.j.x, p.j.y)
            p.vehiculos.append(v)
            p.j.veh = v
            q = _reflection_shooter(p)
            health, vehicle, shooter = p.j.salud, v.salud, q.salud
            p.actualizar_personas(0.01)
            assert p.j.salud == health and v.salud == vehicle
            assert q.salud < shooter


def test_police_and_explosive_typed_shots_return_as_well(app):
    p = fresh(app)
    explosive_ids = [a["id"] for a in p.datos["armas"] if a["tipo"] == "explosivo"]
    for weapon in ["pistola"] + explosive_ids + ["reflection_mod_rocket"]:
        p = fresh(app)
        p.cfg["cheat_reflejar"] = True
        p.j.estrellas = 3
        if weapon == "reflection_mod_rocket":
            a = dict(next(a for a in p.datos["armas"] if a["tipo"] == "explosivo"))
            a["id"] = weapon
            p.armas_d[weapon] = a
        q = _reflection_shooter(p, weapon=weapon, tipo="policia")
        health, shooter = p.j.salud, q.salud
        p.actualizar_personas(0.01)
        assert p.j.salud == health
        assert q.salud == shooter - p.armas_d[weapon]["dano"] * 0.4
        assert not p.explosiones


def test_reflection_off_restores_incoming_shot_damage(app):
    from juego import combate
    p = fresh(app)
    q = _reflection_shooter(p)
    q.punteria = 1
    health, shooter = p.j.salud, q.salud
    saved = combate.random.random
    combate.random.random = lambda: 0
    try:
        p.actualizar_personas(0.01)
    finally:
        combate.random.random = saved
    assert p.j.salud < health and q.salud == shooter


def test_reflection_does_not_return_melee_or_player_explosions(app):
    from juego import combate
    p = fresh(app)
    p.cfg["cheat_reflejar"] = True
    q = _reflection_shooter(p, weapon="punos", distance=1)
    health, shooter = p.j.salud, q.salud
    saved = combate.random.random
    combate.random.random = lambda: 0
    try:
        p.actualizar_personas(0.01)
    finally:
        combate.random.random = saved
    assert p.j.salud < health and q.salud == shooter
    p.personas = []
    health = p.j.salud
    p._estallar({"x": p.j.x, "y": p.j.y, "radio": 8, "dano": 10, "arma": "granada"})
    assert p.j.salud < health


def test_reflection_never_targets_missing_dead_or_online_sources(app):
    p = fresh(app)
    p.cfg["cheat_reflejar"] = True
    q = _reflection_shooter(p)
    a = p.armas_d[q.arma]
    health = q.salud
    p.en_servidor = True
    assert not p.reflejar_disparo(q, a) and q.salud == health
    p.en_servidor = False
    p.personas.remove(q)
    assert not p.reflejar_disparo(q, a) and q.salud == health
    p.personas.append(q)
    q.muerto = True
    assert not p.reflejar_disparo(q, a) and q.salud == health
    assert not p.reflejar_disparo(None, a)


def test_reflected_kill_uses_normal_growth_once(app):
    p = fresh(app)
    p.cfg["cheat_reflejar"] = p.cfg["cheat_crecer"] = True
    q = _reflection_shooter(p)
    q.salud = 1
    p.actualizar_personas(0.01)
    assert q.muerto and p.j.cheat_bajas == 1
    p.actualizar_personas(0.01)
    assert p.j.cheat_bajas == 1


def test_reflection_is_disabled_for_actual_online_npc_shots(app):
    from juego import combate
    p = fresh(app)
    p.cfg["cheat_reflejar"] = True
    p.cfg["defensa_propia"] = False
    p.en_servidor = True
    q = _reflection_shooter(p)
    q.punteria = 1
    health, shooter = p.j.salud, q.salud
    saved = combate.random.random
    combate.random.random = lambda: 0
    try:
        p.actualizar_personas(0.01)
    finally:
        combate.random.random = saved
    assert p.j.salud < health and q.salud == shooter
