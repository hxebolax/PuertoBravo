"""Lo del foro tras la 1.7.6: el botiquín con la salud al máximo, los productos de aseo, y volar alto (ni sucesos de la
calle, ni tiros a tierra desde 800 metros, ni la calle sonando como si estuvieras en ella)."""
import types

import pygame

from juego import vuelo


def test_con_la_salud_llena_no_se_gasta_el_botiquin(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    j = p.j
    j.objetos["botiquin"] = 2
    j.salud = j.salud_max - 0.4                                     # se dice «100»: no tiene sentido gastarlo
    p.usar_botiquin()
    assert j.objetos["botiquin"] == 2 and "guardas el botiquín" in robot.dicho()
    j.salud = j.salud_max - 30
    p.usar_botiquin()
    assert j.objetos["botiquin"] == 1


def test_el_desodorante_es_para_asearte():
    import inspect
    from juego import compra
    fuente = inspect.getsource(compra)
    assert 'tr("Para asearte") if _num(prod, "aseo") > 0' in fuente
    assert compra.comestible({"aseo": 25})                          # se usa desde lo que llevas, pero no se come


def test_volando_alto_no_salen_sucesos_ni_se_alcanza_a_tierra(robot, monkeypatch):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = True
    monkeypatch.setattr(type(p), "volando", lambda self, v=None: True)
    monkeypatch.setattr(type(p), "vuelo_real", lambda self: True)
    monkeypatch.setattr(type(p), "vuelo_alt", lambda self: 800.0)
    p.t_evento = 0.0
    antes = getattr(p, "evento", None)
    for _ in range(20):
        p.t_evento = 0.0
        p._eventos(0.5)
    assert getattr(p, "evento", None) is antes
    o = types.SimpleNamespace(dist=lambda x, y: 10.0)
    assert p.dist_tiro(o, 0, 0) > 799                               # el atracador de abajo está a 800 metros
    monkeypatch.setattr(type(p), "vuelo_alt", lambda self: 0.0)
    assert p.dist_tiro(o, 0, 0) == 10.0
    assert vuelo.AJ("alt_alta") == 150


def test_volando_la_calle_suena_de_lejos_y_las_senales_no(robot):
    mez = robot.app.mez
    p = robot.nueva_partida()
    x, y = p.pos()
    mez.situar_oyente(x, y, 0)
    calle = mez.sonar("ladrido", xy=(x + 5, y), ref=6, maxd=80, cat="efectos")
    senal = mez.sonar("baliza", xy=(x + 5, y), ref=6, maxd=80, cat="interfaz")
    if calle is None or senal is None:
        return
    viejo = mez.altura
    try:
        mez.altura = 0.0
        mez._calcular(calle)
        mez._calcular(senal)
        abajo = (calle.gl_obj + calle.gr_obj, senal.gl_obj + senal.gr_obj)
        mez.altura = 110.0
        mez._calcular(calle)
        mez._calcular(senal)
        arriba = (calle.gl_obj + calle.gr_obj, senal.gl_obj + senal.gr_obj)
    finally:
        mez.altura = viejo
    assert arriba[0] < abajo[0] * 0.2 and abs(arriba[1] - abajo[1]) < 1e-6
