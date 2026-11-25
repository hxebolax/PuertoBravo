"""Issues #31 y #32: el piloto rápido usa todo lo que da el vehículo, mejoras incluidas, y la policía dice por qué te busca."""
import math

from juego import sistemas


def _al_volante(robot, modelo="deportivo"):
    p = robot.p
    j = p.j
    x, y, rumbo = p.mundo.plaza_aparcamiento(j.x, j.y) if hasattr(p.mundo, "plaza_aparcamiento") else (j.x, j.y, 0)
    v = p.crear_vehiculo(modelo, x, y, rumbo, None)
    p._subir(v, False, callar=True)
    return v


def _piloto(robot):
    p = robot.nueva_partida()
    p.cfg["conduccion"] = "asistida"
    p.cfg["piloto_gps"] = True
    p.cfg["sucesos"] = False
    v = _al_volante(robot)
    robot.frames(10)
    destino = max(p.mundo.lugares.values(), key=lambda l: math.hypot(l.x - v.x, l.y - v.y))
    p.gps_a_lugar(destino, callar=True)
    p._piloto_semaforo = lambda *a: None                            # sin semáforos ni curvas: solo cuenta la velocidad que busca
    p._piloto_curva = lambda *a: 999.0
    return p, v


def test_con_mucha_prisa_va_a_toda_velocidad_con_la_mejora_de_motor(robot):
    p, v = _piloto(robot)
    v.mejoras = {"motor": 3}
    tope = v.modelo["vel_max"] * sistemas.factor_velocidad(v) * (1 + 0.01 * p.nivel("conduccion"))
    assert tope > v.modelo["vel_max"] * 1.2
    for estilo in ("mucha_prisa", "temerario"):
        p.cfg["piloto_estilo"] = estilo
        v.vel = tope + 5.0
        p._pilotar(v, 1.0, 100.0)
        assert abs(v.vel - tope) < 0.01, estilo                      # el cien por cien de lo que da, no el 95 ni el de serie


def test_el_piloto_acelera_con_la_mejora_de_motor(robot):
    p, v = _piloto(robot)
    p.cfg["piloto_estilo"] = "temerario"
    ganado = {}
    for mejoras in ({}, {"motor": 3}):
        v.mejoras = mejoras
        v.vel = 0.0
        p._pilotar(v, 0.1, 100.0)
        ganado[bool(mejoras)] = v.vel
    assert abs(ganado[True] / ganado[False] - sistemas.factor_aceleracion(v)) < 0.01


def test_chocar_contra_un_coche_patrulla_se_dice(robot):
    p = robot.nueva_partida()
    p.delito(1, "chocar contra un coche patrulla", siempre=True)
    assert "chocar contra un coche patrulla" in robot.dicho()


def test_al_subir_la_busqueda_se_dice_por_que(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    p.poner_busqueda(1)
    robot.frames(3)
    assert p.j.estrellas == 1
    p.delito(6, "agresión a un agente", siempre=True)
    robot.frames(3)
    assert p.j.estrellas > 1
    dicho = robot.dicho()
    assert "Nivel de búsqueda" in dicho and "Delito: agresión a un agente" in dicho
