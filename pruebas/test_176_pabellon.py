"""Los combates del gimnasio se pelean en el pabellón (data/datos/mapas/arena.json): sin tráfico, sin peatones y sin
policía, para que aporrear el golpe con el rival lejos no le dé al que pasa y venga la policía en mitad del combate. Se
entra al empezar y se vuelve a la puerta del gimnasio al terminar, de cualquier manera."""
import pygame

from juego.entidades import Persona


def _gimnasio(p):
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "gimnasio")
    p.teletransportar(l.x, l.y)
    return l


def _al_pabellon(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    l = _gimnasio(p)
    p.empezar_combate(l, p.combate_def("boxeo"))
    robot.frames(5)
    return p, l


def test_el_combate_se_pelea_en_el_pabellon_sin_nadie_mas(robot):
    p, l = _al_pabellon(robot)
    assert p.mundo.id == "arena" and "pabellón" in robot.dicho()
    rival = next(e for e in p.mision["enemigos"] if not e.muerto)
    assert rival in p.personas and rival.deportivo
    robot.frames(60)
    assert not [q for q in p.personas if q.tipo in ("civil", "policia")]       # ni peatones ni policía
    assert not [v for v in p.vehiculos if v is not p.j.veh]                     # ni tráfico
    # con el rival fuera del alcance de los puños, aporrear el golpe no se queda en una agresión
    x, y = p.pos()
    rival.x, rival.y = p.mundo.punto_libre(x + 25, y)
    for _ in range(10):
        p.j.t_ataque = 0
        p.atacar()
    assert p.j.puntos_busqueda == 0 and p.j.estrellas == 0


def test_al_ganar_vuelves_a_la_puerta_del_gimnasio(robot):
    p, l = _al_pabellon(robot)
    for _ in range(3):                                               # un asalto en el boxeo; hasta tres por si un mod pone más
        vivos = [e for e in (p.mision or {}).get("enemigos", []) if not e.muerto]
        if not vivos:
            break
        p.danar_persona(vivos[0], 5000)
        robot.frames(5)
    robot.saltar_dialogos()
    assert not p.mision and p.j.stats.get("boxeo") == 1
    assert p.mundo.id == l.mapa and abs(p.j.x - l.x) + abs(p.j.y - l.y) < 16


def test_al_dejarlo_o_caer_tambien_se_sale(robot):
    p, l = _al_pabellon(robot)
    p.abandonar_mision()
    assert p.mundo.id == l.mapa and abs(p.j.x - l.x) + abs(p.j.y - l.y) < 16
    # caer en el combate: al hospital de la localidad del gimnasio, no al de otra
    p.empezar_combate(l, p.combate_def("boxeo"))
    robot.frames(5)
    assert p.mundo.id == "arena"
    p.morir()
    assert p.mundo.id == l.mapa
    robot.saltar_dialogos()
    assert not p.mision


def test_la_partida_guardada_en_el_pabellon_te_deja_en_el_gimnasio(robot):
    p, l = _al_pabellon(robot)
    j = p.a_dict()["jugador"]
    assert j["mapa"] == l.mapa and abs(j["x"] - l.x) < 1 and abs(j["y"] - l.y) < 1


def test_el_pabellon_no_es_una_localidad(robot):
    p = robot.nueva_partida()
    assert p.mapas["arena"].tipo == "recinto"
    from juego import extras2
    viajero = next(x for x in extras2.LOGROS if x[0] == "viajero")
    p.j.barrios_vistos = [b["id"] for m in p.mapas.values() if m.id != "arena" for b in m.barrios]
    assert viajero[3](p)                                             # para visitarlo todo no hace falta pelear
    from juego.enlinea import mundo_servidor
    assert "arena" not in mundo_servidor()["mapas"]                  # ni el servidor lo conoce: la huella no cambia


def test_en_un_servidor_se_sigue_peleando_en_la_calle(robot):
    p = robot.nueva_partida()
    assert p.hay_arena()
    p.en_servidor = True
    assert not p.hay_arena()                                         # en línea el mundo es común: el combate, en la calle
    p.en_servidor = False


def test_una_pelea_ilegal_de_un_mod_sigue_en_la_calle(robot):
    p = robot.nueva_partida()
    l = _gimnasio(p)
    p.empezar_combate(l, {"id": "clandestina", "nombre": "Pelea clandestina", "rivales": ["el Sordo"], "deportivo": False})
    robot.frames(3)
    assert p.mundo.id == l.mapa                                      # con testigos: es delito, y se ve
    p.abandonar_mision()
