"""Issue 48: arrancar y apagar el motor con Mayúsculas E (o el menú de acciones del mando)."""
import pygame

from juego import mando


def _en_coche(robot, modelo="sedan"):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    j = p.j
    v = p.crear_vehiculo(modelo, j.x + 3, j.y, 0, None)
    v.cerrado = False
    p._subir(v, False, callar=True)
    robot.frames(2)
    return p, j, v


def test_apagado_no_anda_ni_gasta_ni_suena_y_luego_arranca(robot):
    p, j, v = _en_coche(robot)
    assert v.canal is not None and not v.motor_apagado
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    assert v.motor_apagado and v.canal is None and "Motor apagado" in robot.dicho()
    litros = p.litros(v)
    robot.frames(60, mantener=(pygame.K_UP,))
    assert abs(v.vel) < 0.01 and p.litros(v) == litros                 # ni anda ni gasta
    assert "El motor está apagado" in robot.dicho()
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    assert not v.motor_apagado and v.canal is not None and "Motor en marcha" in robot.dicho()
    robot.frames(30, mantener=(pygame.K_UP,))
    assert v.vel > 1


def test_no_se_apaga_en_marcha_ni_en_la_bici(robot):
    p, j, v = _en_coche(robot)
    v.vel = 10.0
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    assert not v.motor_apagado and "Para el vehículo antes" in robot.dicho()
    p.salir_vehiculo(forzado=True)
    b = p.crear_vehiculo("bici", j.x + 3, j.y, 0, None)
    b.cerrado = False
    p._subir(b, False, callar=True)
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    assert not getattr(b, "motor_apagado", False) and "No tiene motor" in robot.dicho()


def test_sin_combustible_no_arranca_y_al_subir_otra_vez_arranca_solo(robot):
    p, j, v = _en_coche(robot)
    p.cfg["combustible"] = True
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    v.litros = 0.0
    if p.gasta(v):
        robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
        assert v.motor_apagado and "no queda combustible" in robot.dicho()
    v.litros = 20.0
    p.salir_vehiculo(forzado=True)
    p._subir(v, False, callar=True)
    assert not v.motor_apagado and v.canal is not None


def test_muy_danado_puede_no_arrancar(robot, monkeypatch):
    p, j, v = _en_coche(robot)
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    v.salud = v.salud_max * 0.05
    monkeypatch.setattr("random.random", lambda: 0.0)
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    assert v.motor_apagado and "no arranca" in robot.dicho()
    monkeypatch.setattr("random.random", lambda: 0.99)
    robot.tecla(pygame.K_e, pygame.KMOD_SHIFT)
    assert not v.motor_apagado


def test_esta_en_el_mando_y_en_los_datos():
    assert "motor" in mando.ACCIONES
    assert any(t == pygame.K_e and m == pygame.KMOD_SHIFT and d == "coche" for _, t, m, d, *_ in mando.MENU_ACCIONES)
    import json
    import os
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(raiz, "data", "datos", "vida.json"), encoding="utf-8") as f:
        c = json.load(f)["vehiculos_propios"][0]
    assert {"motor_parado", "motor_danado_pct", "motor_fallo_pct"} <= set(c)
