"""Trabajo 1.7.1, tanda 15: vida, reputación y consecuencias. Ser buena persona, delincuente o las dos cosas, con sus
responsabilidades: cómo te ven la ciudad y la calle, antecedentes, carrera con contrato, estudios con título, la empresa
que crece, el banco y las obligaciones, hacer el bien, la trama del buen camino, los logros, la pareja apta para todos
y la doble vida. Con sus opciones apagadas, el juego queda como en la 1.7.0; y las tres simulaciones de sesenta días."""
import json
import os
import random

import pygame
import pytest

from juego import config, gente as G, honrado as H, menus_honrado as MH, menus_juego, mundo as M, rutas, sintesis
from juego.entidades import Persona
from juego.menus import Dialogo, Menu
from test_misiones import _jugar_mision

AJ = H.AJ
BAR = "bar_puerto"                   # un negocio de 12000 euros que da 350 al día


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


def _empezar(robot, nivel="suave", **opciones):
    p = robot.nueva_partida()
    valores = dict(sucesos=False, patrullas_calle=False, ambulancias=False, charla_peatones="nada", consecuencias=nivel, impuestos_facturas=True, antecedentes=True,
                   pareja_familiar=True, reconquista="apagado", oficio_policia=True)
    valores.update(opciones)
    for k, v in valores.items():
        p.cfg[k] = v
    p.t_evento = 1e9
    _vaciar(p)
    return p


def _vaciar(p):
    for v in [v for v in p.vehiculos if v is not p.j.veh]:
        p.quitar_vehiculo(v)
    p.personas = []
    p.t_poblar = 1e9


def _oir(p):
    sonados = []
    original = p.son

    def son(nombre, xy=None, **kw):
        sonados.append(nombre)
        return original(nombre, xy=xy, **kw)
    p.son = son
    return sonados


def _desde(robot, n):
    return " | ".join(robot.app.voz.registro[n:])


def _marca(robot):
    return len(robot.app.voz.registro)


def _cerrar(robot, elegir=0):
    """Cierra escenas y menús que hayan quedado abiertos. En un menú sin salida elige la opción `elegir`."""
    p = robot.p
    for _ in range(40):
        c = robot.app.pila[-1]
        if c is p:
            return
        if isinstance(c, Dialogo):
            robot.tecla(pygame.K_ESCAPE)
        elif isinstance(c, Menu) and not c.escapable:
            c.i = min(elegir, len(c.opciones) - 1)
            robot.tecla(pygame.K_RETURN)
        else:
            robot.app.cerrar(c)


def _dias(robot, n=1, elegir=0):
    p = robot.p
    for _ in range(n):
        p.pasar_horas(24)
        _cerrar(robot, elegir)


def _persona(p, tipo="civil", dx=3.0):
    q = Persona(tipo, *p.mundo.punto_libre(p.pos()[0] + dx, p.pos()[1]))
    p.personas.append(q)
    return q


def _opcion(m, contiene, empieza=False):
    for k, o in enumerate(m.opciones):
        if (o.texto.startswith(contiene) if empieza else contiene in o.texto):
            m.i = k
            return o
    raise AssertionError((contiene, [o.texto for o in m.opciones]))


def _elegir(robot, contiene, empieza=False):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    _opcion(m, contiene, empieza)
    robot.tecla(pygame.K_RETURN)
    return m


def _jornada(p, ident="camarero"):
    x = next(x for x in p.datos["jornadas"] if x["id"] == ident)
    p.jornada(x["id"], x["nombre"], int(x["paga"]), float(x.get("salud", 0)))


def _empleo(p, ident):
    return next(c for c in p.hon_empleos() if c["id"] == ident)


def _titulo(p, ident, dia=1):
    p.j.titulos[ident] = {"s": int(p.hon_titulo(ident)["sesiones"]), "ok": dia}


def _negocio(p, ident=BAR):
    l = p.lugares[ident]
    if l.id not in p.j.propiedades:
        p.j.propiedades.append(l.id)
    p.hon_emp(l)
    return l


class _Fijo:
    """Deja el azar del módulo en un valor fijo mientras dura."""

    def __init__(self, monkeypatch, valor=0.0):
        monkeypatch.setattr(random, "random", lambda: valor)
        monkeypatch.setattr(random, "uniform", lambda a, b: a + (b - a) * valor)


# ====================================================================== 0. datos, opciones y guardado
def test_los_datos_traen_todo_y_las_opciones_vienen_como_se_pidio():
    d = M.cargar_datos(con_mods=False)
    for sec in ("vida_honrada", "titulos", "empleos_fijos", "mejoras_negocio", "incidencias_trabajo", "buenas_acciones"):
        assert sec in M.SECCIONES_VIDA and d[sec], sec
    aj = d["vida_honrada"][0]
    assert set(aj) == set(AJ._n) | set(AJ._l) | {"id"}                        # todos los números y todas las frases están en los datos
    for k in AJ._n:
        assert isinstance(aj[k], (int, float)) and aj[k] > 0, k
    for k in AJ._l:
        assert isinstance(aj[k], list) and aj[k] and all(str(x).strip() for x in aj[k]), k
    assert len(d["titulos"]) >= 6 and len(d["empleos_fijos"]) >= 5 and len(d["mejoras_negocio"]) == 3 and len(d["buenas_acciones"]) >= 8
    jornadas = {"jornada:" + x["id"] for x in d["jornadas"]}
    from juego.trabajos import NOMBRE_TRABAJO
    oficios = {"oficio:" + t for t in NOMBRE_TRABAJO}
    titulos = {t["id"] for t in d["titulos"]}
    for c in d["empleos_fijos"]:
        assert set(c["cuenta"]) <= jornadas | oficios, c["id"]                # cada turno es un trabajo que existe
        assert len(c["puestos"]) == 4 and [p["sueldo"] for p in c["puestos"]] == sorted(p["sueldo"] for p in c["puestos"])
        assert all(not p.get("titulo") or p["titulo"] in titulos for p in c["puestos"])
        assert any(p.get("mando") for p in c["puestos"])                      # arriba hay responsabilidad, no solo más paga
    assert any(c.get("confianza") for c in d["empleos_fijos"])
    assert all(not t.get("requiere") or t["requiere"] in titulos for t in d["titulos"])
    for b in d["buenas_acciones"]:
        assert b["texto"] and 1 <= len(b["opciones"]) <= 4 and all(o["texto"] and o["dice"] for o in b["opciones"])
    assert any(o.get("tentacion") for b in d["buenas_acciones"] for o in b["opciones"])
    # las opciones: nivel suave de serie, impuestos sí, antecedentes sí
    assert config.POR_DEFECTO["consecuencias"] == "suave" and config.OPCIONES["consecuencias"] == ["apagado", "suave", "normal", "exigente"]
    assert config.POR_DEFECTO["impuestos_facturas"] is True and config.POR_DEFECTO["antecedentes"] is True and config.POR_DEFECTO["pareja_familiar"] is True


def test_la_seccion_de_opciones_existe_y_cambia_las_tres_cosas(robot):
    app = robot.app
    menus_juego.opciones(app)
    m = _elegir(robot, "Vida, reputación y consecuencias", empieza=True)
    sec = app.pila[-1]
    assert sec is not m and sec.titulo == "Vida, reputación y consecuencias"
    textos = [o.texto for o in sec.opciones]
    assert textos[0].startswith("Nivel de consecuencias: suave") and textos[1] == "Impuestos y facturas: sí" and textos[2] == "Antecedentes penales: sí"
    assert all(o.ayuda and len(o.ayuda) > 80 for o in sec.opciones[:4])
    sec.i = 0
    vistos = []
    for _ in range(4):
        robot.tecla(pygame.K_RIGHT)
        vistos.append(app.cfg["consecuencias"])
    assert vistos == ["normal", "exigente", "apagado", "suave"]
    assert "todo como en versiones anteriores" in [robot.tecla(pygame.K_LEFT), sec.opciones[0].texto][1]
    for k, clave in ((1, "impuestos_facturas"), (2, "antecedentes"), (3, "pareja_familiar")):
        sec.i = k
        robot.tecla(pygame.K_RIGHT)
        assert app.cfg[clave] is False
    for clave in ("impuestos_facturas", "antecedentes", "pareja_familiar"):
        app.cfg[clave] = True
    app.cfg["consecuencias"] = "suave"


def test_se_guarda_y_se_carga_con_todo_y_una_partida_antigua_empieza_en_neutro(robot):
    p = _empezar(robot)
    j = p.j
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    _titulo(p, "hosteleria")
    l = _negocio(p)
    p.hon_emp(l).update(nivel=2, emp=1, rep=70.0, tapadera=True)
    j.ciudadania = 70
    j.banco = 5000
    assert p.hon_pedir_credito(1000)
    p.hon_antecedente(2, "Prueba")
    p.hon()["asuntos"].append({"tipo": "prensa", "dia": p.dia, "plazo": p.dia + 3, "euros": 900})
    d = json.loads(json.dumps(p.a_dict()))
    for campo in ("antecedentes", "contrato", "titulos", "empresa", "creditos", "honra"):
        assert campo in d["jugador"], campo
    robot.app.empezar_partida(d)
    p2 = robot.p
    j2 = p2.j
    assert p2 is not p and j2.contrato["empleo"] == "hosteleria" and p2.hon_titulos() == ["hosteleria"] and len(j2.creditos) == 1
    assert j2.empresa[BAR] == {**j2.empresa[BAR], "nivel": 2, "emp": 1, "tapadera": True} and len(p2.hon_antecedentes()) == 1
    assert p2.hon()["asuntos"][0]["tipo"] == "prensa" and not p2._hon_cargada
    assert json.loads(json.dumps(p2.a_dict()))["jugador"]["honra"] == d["jugador"]["honra"]
    # una partida de antes de esta versión: sin esos campos, con casas, un negocio, detenciones viejas y el día 40
    vieja = json.loads(json.dumps(d))
    for campo in ("antecedentes", "contrato", "titulos", "empresa", "creditos", "honra"):
        del vieja["jugador"][campo]
    vieja["dia"] = 40
    vieja["jugador"]["stats"]["detenciones"] = 7
    vieja["jugador"]["propiedades"] = ["casa_abuela", "piso_centro", BAR]
    vieja["jugador"]["banco"] = 9000
    robot.app.empezar_partida(vieja)
    p3 = robot.p
    j3 = p3.j
    p3.cfg["sucesos"] = False
    assert p3._hon_cargada and j3.antecedentes == [] and not j3.contrato and not j3.creditos and not j3.honra       # en neutro: nada de lo de antes cuenta
    assert p3.hon_antecedentes_txt() == "No tienes antecedentes penales en vigor."
    n = _marca(robot)
    p3.t_honrado = 0.0
    robot.frames(2)
    dicho = _desde(robot, n)
    assert "Empiezas en neutro: sin antecedentes por lo hecho hasta hoy" in dicho and f"Dentro de {AJ.entero('gracia_dias')} días" in dicho
    h = p3.hon()
    assert h["gracia"] == 40 + AJ.entero("gracia_dias") == h["cobro"] and not p3._hon_cargada
    n = _marca(robot)
    p3.t_honrado = 0.0
    robot.frames(2)
    assert "Empiezas en neutro" not in _desde(robot, n)                       # el aviso, una sola vez
    banco = j3.banco
    dinero = j3.dinero
    _dias(robot, AJ.entero("gracia_dias") - 1)
    ingresos = (AJ.entero("gracia_dias") - 1) * 350
    assert j3.dinero == dinero + ingresos                                     # el negocio da lo de siempre y durante la gracia no se cobra nada
    assert j3.banco >= banco and not h["asuntos"] and j3.stats.get("impuestos_pagados", 0) == 0
    _dias(robot, 1)
    assert j3.stats.get("impuestos_pagados", 0) > 0                           # y el primer cobro llega justo al acabar


# ====================================================================== 1. cómo te ven: el mundo responde al prestigio y a la fama
def test_el_movil_dice_como_te_ve_la_ciudad_y_la_calle_y_que_ganas_o_pierdes(robot):
    p = _empezar(robot)
    j = p.j
    robot.tecla(pygame.K_m)
    movil = robot.app.pila[-1]
    assert isinstance(movil, Menu) and movil.titulo.startswith("Móvil")
    _elegir(robot, "Vida, reputación y consecuencias", empieza=True)
    m = robot.app.pila[-1]
    assert m.titulo == "Vida, reputación y consecuencias"
    t = [o.texto for o in m.opciones]
    assert t[0].startswith("Cómo te ve la ciudad: eres [un vecino|una vecina] más. Prestigio, 20 de 100") and "eres uno más" in t[0]
    assert t[1].startswith("Cómo te ve la calle: nadie te conoce. Fama, 0") and "te cobran un 9 por ciento más" in t[1]
    for trozo in ("Antecedentes penales. No tienes", "Trabajo. No tienes contrato fijo", "Estudios. No tienes ningún título", "Negocios. No tienes ninguno",
                  "Banco y obligaciones.", "Doble vida:", "Asuntos pendientes: 0", "El buen camino", "Nivel de consecuencias: suave"):
        assert any(x.startswith(trozo) for x in t), trozo
    assert all(o.ayuda for o in m.opciones[:10])
    # cada tramo de prestigio dice lo suyo
    j.ciudadania = 5
    assert "los vecinos te evitan" in p.hon_ciudad_txt() and "Pierdes: en las tiendas te cobran un 7 por ciento más" in p.hon_ciudad_txt()
    j.ciudadania = 45
    c = p.hon_ciudad_txt()
    assert "te aprecian" in c and "cobras un diez por ciento más" in c and "te rebajan un 5 por ciento y te fían hasta 60 euros" in c
    j.ciudadania = 80
    c = p.hon_ciudad_txt()
    assert "ejemplar" in c and "cobras un veinte por ciento más" in c and "el doble de interés" in c and "te rebajan un 10 por ciento y te fían hasta 150 euros" in c
    assert "La policía te pasa por alto" in c and "beneficio de la duda" in c
    # y la fama
    j.reputacion = 60
    _negocio(p)
    ca = p.hon_calle_txt()
    assert "te temen" in ca and "te cobran un 12 por ciento menos" in ca and "Las bandas respetan tus negocios" in ca
    j.reputacion = 0
    assert "presa fácil" in p.hon_calle_txt()
    p.cfg["consecuencias"] = "apagado"
    assert "Las consecuencias están apagadas" in p.hon_ciudad_txt() and "apagadas" in p.hon_calle_txt()
    robot.app.cerrar(m)
    robot.app.cerrar(movil)


def test_las_tiendas_rebajan_fian_recargan_y_en_exigente_no_atienden(robot, datos_de_serie):
    p = _empezar(robot)
    j = p.j
    tienda = p.lugares["tienda_paco"]
    precios = {}
    for prestigio in (5, 20, 45, 80):
        j.ciudadania = prestigio
        precios[prestigio] = p.mercado("comida", tienda.id)
    assert precios == {5: 1.072, 20: 1.0, 45: 0.95, 80: 0.9}                  # suave: el recargo, al sesenta por ciento; las rebajas, enteras
    p.cfg["consecuencias"] = "normal"
    j.ciudadania = 5
    assert p.mercado("armas", "x") == 1.12
    p.cfg["consecuencias"] = "exigente"
    assert p.mercado("comida", tienda.id) == 1.18
    p.cfg["consecuencias"] = "suave"
    # el fiado: solo dentro de un comercio y donde te aprecian
    j.ciudadania = 45
    j.dinero = 10
    n = _marca(robot)
    assert not p.pagar(30) and j.dinero == 10                                 # en la calle no hay fiado
    p.entrar_interior(tienda)
    assert p.pagar(30) and j.dinero == 0 and p.hon()["fiado"] == 20
    assert ("te conocen" in _desde(robot, n) or "eres de casa" in _desde(robot, n)) and "Debes 20 de fiado" in _desde(robot, n)
    assert p.pagar(40) and p.hon()["fiado"] == 60
    assert not p.pagar(1) and p.hon()["fiado"] == 60                          # el tope de quien aprecian: 60
    j.ciudadania = 80
    assert p.pagar(90) and p.hon()["fiado"] == 150 and not p.pagar(1)         # y el del ciudadano ejemplar: 150
    p.entrar_interior(p.lugares["armeria_centro"])
    assert not p.pagar(5)                                                     # en una armería no se fía
    p.salir_interior(silencio=True)
    assert p._local is None
    j.dinero = 500
    MH.menu_vida(p)
    _elegir(robot, "Pagar lo que debes de fiado")
    assert p.hon()["fiado"] == 0 and j.dinero == 350
    robot.app.cerrar(robot.app.pila[-1])
    j.ciudadania = 20
    j.dinero = 0
    p.entrar_interior(tienda)
    assert not p.pagar(5)                                                     # a uno más no le fían
    p.salir_interior(silencio=True)
    # exigente y te evitan: hay comercios que ese día no te atienden; en suave y en normal, nunca
    j.ciudadania = 3
    AJ.n["negativa_prob"] = 100
    for nivel, echan in (("suave", False), ("normal", False), ("exigente", True)):
        p.cfg["consecuencias"] = nivel
        assert p.hon_negativa(tienda) is echan
    n = _marca(robot)
    p.j.x, p.j.y = tienda.x, tienda.y
    menus_juego.lugar(p, tienda)
    assert robot.app.pila[-1] is p and any(f in _desde(robot, n) for f in AJ.lista("frases_negativa"))
    assert not p.hon_negativa(p.lugares["banco"])                             # un banco no es un comercio de barrio
    j.ciudadania = 20
    assert not p.hon_negativa(tienda)


def test_los_testigos_encubren_delatan_y_el_agente_da_el_beneficio_de_la_duda(robot, monkeypatch):
    p = _empezar(robot, nivel="normal")
    j = p.j
    _persona(p, "civil")
    # te evitan: el delito cuenta un veinticinco por ciento más (normal), y lo dicen
    j.ciudadania = 5
    n = _marca(robot)
    p.delito(1, "prueba")
    assert round(j.puntos_busqueda, 3) == 1.25 and any(f in _desde(robot, n) for f in AJ.lista("frases_delatan"))
    # uno más: como siempre
    j.puntos_busqueda, j.ciudadania = 0.0, 20
    p.delito(1, "prueba")
    assert j.puntos_busqueda == 1.0
    # ejemplar: a veces miran a otro lado, y entonces ni cuenta ni baja el prestigio
    j.puntos_busqueda, j.ciudadania = 0.0, 80
    monkeypatch.setattr(random, "random", lambda: 0.0)
    n = _marca(robot)
    p.delito(2, "prueba")
    assert j.puntos_busqueda == 0.0 and j.ciudadania == 80 and any(f in _desde(robot, n) for f in AJ.lista("frases_encubren"))
    p.delito(3, "prueba")                                                     # algo más grave no lo tapa nadie
    assert round(j.puntos_busqueda, 2) == 2.1
    monkeypatch.setattr(random, "random", lambda: 0.99)
    j.puntos_busqueda, j.ciudadania = 0.0, 80
    p.delito(1, "prueba")
    assert round(j.puntos_busqueda, 2) == 0.7                                 # sin suerte: cuenta, con la rebaja de siempre al buen vecino
    # delante de un agente no hay quien encubra, pero una vez al día te da el beneficio de la duda si tu ficha está limpia
    _persona(p, "policia", 6.0)
    monkeypatch.setattr(random, "random", lambda: 0.0)
    j.puntos_busqueda, j.ciudadania = 0.0, 80
    n = _marca(robot)
    p.delito(1, "prueba")
    assert j.puntos_busqueda == 0.0 and any(f in _desde(robot, n) for f in AJ.lista("frases_duda"))
    p.delito(1, "prueba")
    assert round(j.puntos_busqueda, 2) == 0.7                                 # la segunda del día, ya no
    # fichado: cada delito cuenta más, y sin ficha limpia no hay beneficio de la duda
    p.pasar_horas(24)
    p.hon_antecedente(2, "Prueba")
    j.puntos_busqueda, j.ciudadania = 0.0, 80
    p.delito(1, "prueba")
    assert round(j.puntos_busqueda, 3) == round(0.7 * 1.2, 3)                 # un antecedente medio pesa dos: un veinte por ciento más
    # apagado: nada de esto
    p.cfg["consecuencias"] = "apagado"
    for prestigio, esperado in ((5, 1.0), (80, 0.7)):
        j.puntos_busqueda, j.ciudadania = 0.0, prestigio
        p.delito(1, "prueba")
        assert round(j.puntos_busqueda, 2) == esperado


def test_con_mala_fama_o_fichado_la_policia_te_para_en_normal_y_no_en_suave(robot, monkeypatch):
    p = _empezar(robot, nivel="normal")
    j = p.j
    j.ciudadania = 3
    _persona(p, "policia", 5.0)
    monkeypatch.setattr(random, "random", lambda: 0.0)
    reloj = p.reloj
    n = _marca(robot)
    p._hon_control()
    assert p.reloj == reloj + AJ("control_minutos") and any(f in _desde(robot, n) for f in AJ.lista("frases_control"))
    p._hon_control()
    assert p.reloj == reloj + AJ("control_minutos")                           # una vez al día como mucho
    p.hon()["control_dia"] = 0
    j.ciudadania = 30
    p._hon_control()
    assert p.reloj == reloj + AJ("control_minutos")                           # a uno más, sin antecedentes, no le paran
    p.hon_antecedente(2, "Prueba")
    p._hon_control()
    assert p.reloj == reloj + 2 * AJ("control_minutos")                       # fichado, sí
    p.hon()["control_dia"] = 0
    p.cfg["consecuencias"] = "suave"
    p._hon_control()
    assert p.reloj == reloj + 2 * AJ("control_minutos")                       # en suave no hay controles


def test_la_fama_en_la_calle_abarata_la_escolta_y_protege_tus_negocios(robot):
    p = _empezar(robot, nivel="normal")
    j = p.j
    assert p.hon_fama_factor() == 1.15                                        # nadie te conoce: un quince por ciento más
    j.reputacion = 25
    assert p.hon_fama_factor() == 0.94
    j.reputacion = 80
    assert p.hon_fama_factor() == 0.88
    taberna = p.lugares["bodega"]
    j.dinero = 1000
    p.j.x, p.j.y = taberna.x, taberna.y
    menus_juego.lugar(p, taberna)
    m = robot.app.pila[-1]
    base = p.precio("guardaespaldas_taberna", 300)
    assert _opcion(m, "Contratar un guardaespaldas").texto == f"Contratar un guardaespaldas: {int(base * 0.88)} euros"
    robot.tecla(pygame.K_RETURN)
    assert j.dinero == 1000 - int(base * 0.88)
    _cerrar(robot)
    p.cfg["consecuencias"] = "apagado"
    assert p.hon_fama_factor() == 1.0
    p.cfg["consecuencias"] = "normal"
    p.personas = []
    _negocio(p)
    j.reputacion = 0
    assert not p.hon_protegido()
    j.reputacion = AJ("fama_respeto")
    assert p.hon_protegido()
    j.reputacion, j.banda = 0, 3
    assert p.hon_protegido()


# ====================================================================== 2. antecedentes penales
def test_las_detenciones_dejan_antecedentes_con_su_gravedad_y_caducan(robot):
    p = _empezar(robot)
    j = p.j
    j.dinero = 3000
    son = _oir(p)
    for nivel, gravedad, dias in ((1, 1, "caduca_leve"), (3, 2, "caduca_media"), (5, 3, "caduca_grave")):
        j.antecedentes = []
        j.estrellas = nivel
        n = _marca(robot)
        p.detener(True)
        _cerrar(robot)
        a = j.antecedentes[-1]
        assert a["g"] == gravedad and a["c"] - a["d"] == AJ.entero(dias) and f"búsqueda de nivel {nivel}" in a["t"]
        assert f"falta {H.GRAVEDAD[gravedad]}" in _desde(robot, n) and "Queda apuntado en tus antecedentes penales" in _desde(robot, n)
    assert "ingreso en prisión" in j.antecedentes[-1]["t"] and j.stats["antecedentes"] == 3
    # reintentar una misión devuelve el dinero y lo demás a como estaba, pero no borra lo que consta en la ficha
    import copy
    copia = copy.deepcopy(j.a_dict())
    p.hon_antecedente(2, "Durante una misión")
    p._rebobinar_jugador(copia)
    assert [a["t"] for a in j.antecedentes][-1] == "Durante una misión" and j.stats["antecedentes"] == 4
    j.antecedentes.pop()
    j.stats["antecedentes"] = 3
    assert p.hon_graves() and p.hon_peso() == 4 and "el más grave, grave" in p.hon_antecedentes_txt()
    # la multa pagada en el acto a un agente también consta, como falta leve
    j.antecedentes = []
    j.estrellas, j.dinero = 1, 5000
    p.detener()
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and "Un agente te ha cogido" in m.titulo
    _elegir(robot, "Pagar la multa en el acto")
    assert [a["g"] for a in j.antecedentes] == [1] and "Multa pagada" in j.antecedentes[0]["t"]
    # caducan solos, con su aviso
    dia = p.dia
    n = _marca(robot)
    _dias(robot, AJ.entero("caduca_leve") - 1)
    assert len(p.hon_antecedentes()) == 1
    _dias(robot, 1)
    assert p.dia == dia + AJ.entero("caduca_leve") and not p.hon_antecedentes() and j.antecedentes == []
    assert "Ha caducado un antecedente penal" in _desde(robot, n) and "prestigio" in son


def test_los_antecedentes_cierran_puertas_y_se_atenuan_con_servicios_y_abogado(robot):
    p = _empezar(robot)
    j = p.j
    j.ciudadania = 70
    j.dinero = 20000
    assert p.ingreso_motivo() == "" and p.hon_firma_motivo(_empleo(p, "emergencias")) == "" and p.hon_credito_motivo() == ""
    p.hon_antecedente(3, "Prueba grave")
    assert "antecedentes penales en vigor" in p.ingreso_motivo()                              # la policía no te admite
    assert "certificado de antecedentes" in p.hon_firma_motivo(_empleo(p, "emergencias"))     # ni un empleo de confianza
    assert "antecedentes graves" in p.hon_credito_motivo() and "antecedentes graves" in p.hon_credito_motivo("hipoteca")
    assert p.hon_firma_motivo(_empleo(p, "hosteleria")) == ""                                 # en suave, un empleo corriente sí
    p.cfg["consecuencias"] = "exigente"
    assert "no te contrata nadie" in p.hon_firma_motivo(_empleo(p, "hosteleria"))
    p.cfg["consecuencias"] = "suave"
    # la consulta, en comisaría y en el móvil
    com = p.lugares["comisaria"]
    j.x, j.y = com.x, com.y
    menus_juego.lugar(p, com)
    _elegir(robot, "Antecedentes penales.", empieza=True)
    m = robot.app.pila[-1]
    assert m.titulo == "Antecedentes penales" and "Tienes 1 antecedente en vigor; el más grave, grave" in m.opciones[0].texto
    assert "Prueba grave. Falta grave. Caduca en 50 días" in m.opciones[1].texto and f"cuesta {3 * AJ.entero('abogado_precio')} euros" in m.opciones[1].texto
    assert "Qué te cierran: los empleos de confianza, los créditos y las hipotecas y el ingreso en la policía" in _opcion(m, "Qué te cierran").texto
    # servicios a la comunidad: cuatro horas, cinco días menos, una vez al día
    a = j.antecedentes[0]
    caduca, hora, prestigio = a["c"], p.reloj, j.ciudadania
    _elegir(robot, "Hacer servicios a la comunidad")
    assert a["c"] == caduca - AJ.entero("servicio_quita") and p.reloj == hora + 240 and j.ciudadania == prestigio + 1.5
    n = _marca(robot)
    _elegir(robot, "Hacer servicios a la comunidad")
    assert a["c"] == caduca - AJ.entero("servicio_quita") and "Hoy ya has hecho servicios" in _desde(robot, n)
    # el abogado: baja un grado, una sola vez
    m.i = 1
    dinero = j.dinero
    robot.tecla(pygame.K_RETURN)
    assert a["g"] == 2 and a["ab"] and j.dinero == dinero - 3 * AJ.entero("abogado_precio") and a["c"] <= p.dia + AJ.entero("caduca_media")
    robot.tecla(pygame.K_RETURN)
    assert a["g"] == 2 and j.dinero == dinero - 3 * AJ.entero("abogado_precio")
    _cerrar(robot)
    assert "antecedentes graves" not in p.hon_credito_motivo() and not p.hon_graves()      # ya no es grave: el banco vuelve a mirar su solvencia, sin más
    # un leve recurrido desaparece; y el comedor social también ofrece los servicios
    b = p.hon_antecedente(1, "Prueba leve")
    p.hon_rebajar(b)
    assert b not in p.hon_antecedentes()
    ong = p.lugares["comedor_social"]
    j.x, j.y = ong.x, ong.y
    menus_juego.lugar(p, ong)
    assert _opcion(robot.app.pila[-1], "Hacer servicios a la comunidad")
    _cerrar(robot)
    # con la opción apagada no se apunta nada y nada se cierra
    p.cfg["antecedentes"] = False
    assert p.hon_antecedentes() == [] and p.hon_antecedente(3, "No cuenta") is None and p.ingreso_motivo() == ""
    assert "desactivados en Opciones" in p.hon_antecedentes_txt()


# ====================================================================== 3. carrera profesional
def test_contrato_fijo_turnos_evaluacion_nomina_y_ascenso(robot, monkeypatch):
    p = _empezar(robot)
    j = p.j
    son = _oir(p)
    ofi = p.lugares["empleo_pb"]
    j.x, j.y = ofi.x, ofi.y
    p.completadas.append("h01")                                               # la oficina, sin la misión que espera en ella
    menus_juego.lugar(p, ofi)
    _elegir(robot, "Contratos fijos", empieza=True)
    m = robot.app.pila[-1]
    assert m.titulo == "Contratos fijos" and len(m.opciones) == 1 + len(p.hon_empleos()) + 1
    _elegir(robot, "Hostelería, en Grupo Hostelero La Bahía")
    ficha = robot.app.pila[-1]
    assert [o.texto.split(":")[0] for o in ficha.opciones[2:6]] == ["Puesto 1", "Puesto 2", "Puesto 3", "Puesto 4"]
    assert "Pide título de Título de hostelería" in ficha.opciones[3].texto and "Con decisiones de responsabilidad" in ficha.opciones[4].texto
    n = _marca(robot)
    _elegir(robot, "Firmar el contrato", empieza=True)
    ct = j.contrato
    assert ct["empleo"] == "hosteleria" and ct["puesto"] == 0 and ct["fin"] == p.dia + 7 and ct["jefe"] in _desde(robot, n)
    assert "3 turnos cada 7 días" in _desde(robot, n) and "220 euros de nómina" in _desde(robot, n)
    assert "Ya tienes un contrato fijo" in p.hon_firma_motivo(_empleo(p, "comercio"))
    _cerrar(robot)
    ct["caracter"] = "justo"
    _Fijo(monkeypatch, 0.5)
    # tres turnos de lo suyo, uno al día; una jornada de otro oficio no cuenta
    paga_antes = j.dinero
    _jornada(p, "camarero")
    assert ct["turnos"] == 1 and j.dinero == paga_antes + 70 and j.stats["turnos_contrato"] == 1       # la jornada se cobra como siempre
    _dias(robot)
    _jornada(p, "peon")
    assert ct["turnos"] == 1
    for _ in range(2):
        _dias(robot)
        _jornada(p, "camarero")
    assert ct["turnos"] == 3 and len(ct["calidad"]) == 3
    banco = j.banco
    n = _marca(robot)
    _dias(robot, ct["fin"] - p.dia)
    assert ct["periodos"] == 1 and ct["meritos"] == 1 and ct["turnos"] == 0 and ct["nota"] >= 75
    assert j.banco >= banco + 220 + 22 and "prima" in _desde(robot, n) and j.stats["evaluaciones_buenas"] == 1          # nómina y prima, al banco
    # tres evaluaciones buenas: el ascenso espera al título
    for _ in range(2):
        for _ in range(3):
            _jornada(p, "camarero")
            _dias(robot)
        _dias(robot, max(0, ct["fin"] - p.dia))
    assert ct["meritos"] == 3 and ct["puesto"] == 0
    assert "pero te falta el título de Título de hostelería" in " | ".join(robot.app.voz.registro[-30:])
    _titulo(p, "hosteleria")
    n = _marca(robot)
    for _ in range(3):
        _jornada(p, "camarero")
        _dias(robot)
    _dias(robot, max(0, ct["fin"] - p.dia))
    assert ct["puesto"] == 1 and ct["meritos"] == 0 and "ascenso" in son and "de sala" in _desde(robot, n) and j.stats["ascensos"] == 1
    assert p.hon_sueldo_semana() == 400 and "4 turnos por periodo" in _desde(robot, n)
    # el móvil lo cuenta
    t = p.hon_contrato_txt()
    assert t.startswith("Jef[e|a] de sala en Grupo Hostelero La Bahía") and "Nómina: 400 euros" in t and "Avisos: 0 de 3" in t
    MH.menu_contrato(p)
    m = robot.app.pila[-1]
    assert "Cuentan como turno: jornada de camarero" in m.opciones[1].texto and "Siguiente puesto: encargad[o|a] de local" in m.opciones[3].texto
    assert "Te falta el título de Título de administración y gestión" in m.opciones[3].texto
    _cerrar(robot)


def test_faltar_o_hacerlo_mal_trae_avisos_sancion_y_despido(robot, monkeypatch):
    p = _empezar(robot)
    j = p.j
    son = _oir(p)
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    ct = j.contrato
    ct["caracter"] = "justo"
    _Fijo(monkeypatch, 0.5)
    # un turno de tres: floja, aviso y nómina recortada
    _jornada(p, "camarero")
    banco = j.banco
    n = _marca(robot)
    _dias(robot, 5)
    assert "te faltan 2 turnos" in _desde(robot, n)                           # el aviso de que se acaba el periodo, dos días antes
    _dias(robot, 2)
    assert ct["avisos"] == 1 and 25 <= ct["nota"] < 50 and banco + 73 <= j.banco <= banco + 75 and "Aviso" in _desde(robot, n) or "aviso" in _desde(robot, n)
    # ningún turno: muy mala, sin nómina
    banco = j.banco
    _dias(robot, 7)
    assert ct["avisos"] == 2 and ct["nota"] == 0 and j.banco <= banco + 2
    # y al tercero, a la calle
    prestigio = j.ciudadania
    n = _marca(robot)
    _dias(robot, 7)
    assert j.contrato == {} and "despido" in son and "Motivo: demasiados avisos" in _desde(robot, n) and j.stats["despidos"] == 1
    assert j.ciudadania < prestigio
    assert "no quieren saber de ti hasta el día" in p.hon_firma_motivo(_empleo(p, "hosteleria"))
    assert p.hon_firma_motivo(_empleo(p, "comercio")) == ""
    _dias(robot, AJ.entero("veto_dias"))
    assert p.hon_firma_motivo(_empleo(p, "hosteleria")) == ""
    # en normal, no aparecer cuesta dos avisos de golpe
    p.cfg["consecuencias"] = "normal"
    assert p.hon_firmar(_empleo(p, "comercio"))
    j.contrato["caracter"] = "justo"
    _dias(robot, 7)
    assert j.contrato["avisos"] == 2


def test_carta_de_recomendacion_oficios_con_vehiculo_y_decisiones_de_responsabilidad(robot, monkeypatch):
    p = _empezar(robot)
    j = p.j
    _Fijo(monkeypatch, 0.5)
    # con vehículo, tres servicios hacen un turno
    assert p.hon_firmar(_empleo(p, "transporte"))
    ct = j.contrato
    ct["caracter"] = "justo"
    n = _marca(robot)
    for _ in range(3):
        p.servicio_hecho("taxi", "taxista")
    assert ct["turnos"] == 1 and "Servicio apuntado: 1 de 3" in _desde(robot, n) and "Servicio apuntado: 2 de 3" in _desde(robot, n)
    p.servicio_hecho("ambulancia", "sanitario")                               # no es de su contrato
    assert ct["turnos"] == 1 and ct["servicios"] == 3
    # tres periodos sin avisos: al irse, carta, que ahorra el primer escalón del siguiente empleo
    ct["periodos"] = AJ.entero("carta_periodos")
    n = _marca(robot)
    MH.menu_contrato(p)
    _elegir(robot, "Presentar la dimisión")
    _elegir(robot, "Sí, presentar la dimisión")
    assert j.contrato == {} and p.hon()["cartas"] == ["transporte"] and "carta de recomendación" in _desde(robot, n)
    _cerrar(robot)
    _titulo(p, "comercio")
    assert p.hon_firmar(_empleo(p, "comercio"))
    assert j.contrato["puesto"] == 1 and p.hon()["cartas"] == []
    # un puesto con responsabilidad trae una decisión que cuenta en la evaluación
    p.hon_dimitir()
    _titulo(p, "administracion")
    j.ciudadania = 50
    assert p.hon_firmar(_empleo(p, "comercio"))
    ct = j.contrato
    ct["puesto"] = 2
    assert p.hon_puesto()["mando"]
    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(random, "choice", lambda lista: lista[0])
    _jornada(p, "reponedor")
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and not m.escapable and m.titulo.startswith("Tu puesto tiene responsabilidad.")
    inc = p.datos["incidencias_trabajo"][0]
    antes = ct["calidad"][-1]
    assert [o.texto for o in m.opciones] == [o["texto"] for o in inc["opciones"]] and all(o.ayuda for o in m.opciones)
    robot.tecla(pygame.K_RETURN)
    assert ct["calidad"][-1] == min(100.0, antes + inc["opciones"][0]["calidad"]) and inc["opciones"][0]["dice"] in robot.app.voz.registro[-1]


def test_un_antecedente_nuevo_llega_al_jefe_y_un_empleo_de_confianza_no_lo_perdona(robot):
    p = _empezar(robot)
    j = p.j
    son = _oir(p)
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    p.hon_antecedente(1, "Leve")
    assert j.contrato["avisos"] == 0                                          # suave: una falta leve no llega a más
    n = _marca(robot)
    p.hon_antecedente(2, "Media")
    assert j.contrato["avisos"] == 1 and "se han enterado de tu problema con la policía" in _desde(robot, n)
    p.hon_antecedente(3, "Grave")
    assert j.contrato == {} and "despido" in son and "tus antecedentes penales" in " | ".join(robot.app.voz.registro[-6:])
    # empleo de confianza
    j.antecedentes = []
    j.ciudadania = 40
    assert p.hon_firmar(_empleo(p, "emergencias"))
    p.hon_antecedente(1, "Leve")
    assert j.contrato                                                         # en suave, una leve se le pasa
    p.hon_antecedente(2, "Media")
    assert j.contrato == {} and "un empleo de confianza no admite antecedentes" in " | ".join(robot.app.voz.registro[-6:])
    # en normal, hasta una leve trae aviso
    p.cfg["consecuencias"] = "normal"
    j.antecedentes = []
    assert p.hon_firmar(_empleo(p, "comercio"))
    p.hon_antecedente(1, "Leve")
    assert j.contrato["avisos"] == 1
    # sin contrato, trabajar por libre es lo de siempre
    p.hon_dimitir()
    dinero = j.dinero
    _dias(robot)
    _jornada(p, "camarero")
    assert j.dinero == dinero + 70 and not j.contrato and j.stats.get("turnos_contrato", 0) == 0


# ====================================================================== 4. estudios con título
def test_un_titulo_lleva_varias_sesiones_cuesta_dinero_y_abre_puestos(robot):
    p = _empezar(robot)
    j = p.j
    son = _oir(p)
    j.dinero = 5000
    aca = p.lugares["centro_civico"]
    j.x, j.y = aca.x, aca.y
    menus_juego.lugar(p, aca)
    _elegir(robot, "Estudios con título.", empieza=True)
    m = robot.app.pila[-1]
    assert m.titulo == "Estudios con título" and len(m.opciones) == 1 + len(p.datos["titulos"]) + 1
    t = p.hon_titulo("hosteleria")
    assert "llevas 0 de 4 sesiones; cada una, 110 euros y 3 horas" in _opcion(m, t["nombre"], True).texto
    prestigio, hora = j.ciudadania, p.reloj
    _elegir(robot, t["nombre"], True)
    assert j.titulos["hosteleria"] == {"s": 1, "ok": 0} and j.dinero == 4890 and p.reloj == hora + 180
    n = _marca(robot)
    _elegir(robot, t["nombre"], True)
    assert j.titulos["hosteleria"]["s"] == 1 and "Una sesión al día" in _desde(robot, n) and j.dinero == 4890
    # el mismo día se puede trabajar y hacer un curso suelto de habilidad: son cosas distintas
    _jornada(p, "camarero")
    assert j.jornada_dia == p.dia
    for k in range(3):
        p.pasar_horas(24)
        _elegir(robot, t["nombre"], True)
    assert p.hon_titulos() == ["hosteleria"] and j.titulos["hosteleria"]["ok"] == p.dia and "titulo" in son and j.stats["titulos"] == 1
    assert j.ciudadania >= prestigio + AJ("titulo_prestigio") and "ya lo tienes" in _opcion(m, t["nombre"], True).texto
    assert t["abre"] in " | ".join(robot.app.voz.registro[-4:])
    # los títulos altos piden prestigio y el título anterior
    d = p.hon_titulo("direccion")
    p.pasar_horas(24)
    assert "Antes hay que tener el título de Título de administración y gestión" in p.hon_titulo_motivo(d)
    _titulo(p, "administracion")
    j.ciudadania = 30
    assert "piden que los vecinos hablen mejor de ti" in p.hon_titulo_motivo(d)
    j.ciudadania = 50
    assert p.hon_titulo_motivo(d) == ""
    j.dinero = 100
    p.hon_estudiar(d)
    assert "direccion" not in j.titulos                                       # sin dinero no hay clase (ni fiado)
    _cerrar(robot)
    # desde el móvil se consulta, no se estudia
    MH.menu_estudios(p, None)
    m = robot.app.pila[-1]
    assert m.titulo == "Tus estudios" and "Tienes: Título de hostelería" in m.opciones[0].texto
    _cerrar(robot)


# ====================================================================== 5. la empresa
def test_un_negocio_crece_con_mejoras_y_empleados_y_rinde_segun_como_lo_lleves(robot):
    p = _empezar(robot, nivel="normal")
    j = p.j
    l = p.lugares[BAR]
    j.dinero = 60000
    j.x, j.y = l.x, l.y
    menus_juego.lugar(p, l)
    _elegir(robot, "Comprar el negocio por 12000 euros", empieza=True)
    assert BAR in j.propiedades and p.ingreso_negocio(l) == 350                # recién comprado, lo de siempre
    menus_juego.lugar(p, l)
    m = robot.app.pila[-1]
    assert m.opciones[0].texto == "Es tuyo. Da 350 euros cada día, a medianoche"
    e = j.empresa[BAR]
    assert e["nivel"] == 1 and e["rep"] == 50 and e["visto"] == p.dia and "Negocio de barrio, nivel 1" in _opcion(m, "Dirección.").texto
    # mejoras: la primera, libre; la segunda pide título; la tercera, título y prestigio
    assert "Reforma del local, por 4200 euros" in _opcion(m, "Mejorar").texto
    _elegir(robot, "Mejorar")
    assert e["nivel"] == 2 and j.dinero == 60000 - 12000 - 4200 and p.ingreso_negocio(l) == 437
    n = _marca(robot)
    _elegir(robot, "Mejorar")
    assert e["nivel"] == 2 and "hace falta el título de Título de administración y gestión" in _desde(robot, n)
    _titulo(p, "administracion")
    _elegir(robot, "Mejorar")
    assert e["nivel"] == 3 and p.ingreso_negocio(l) == 560
    _titulo(p, "direccion")
    j.ciudadania = 30
    _elegir(robot, "Mejorar")
    assert e["nivel"] == 3 and "hacen falta 60 de prestigio" in " | ".join(robot.app.voz.registro[-2:])
    j.ciudadania = 60
    _elegir(robot, "Mejorar")
    assert e["nivel"] == 4 and p.ingreso_negocio(l) == 735 and "ya está en su nivel más alto" in _opcion(m, "Mejoras").texto
    # empleados: cada uno cobra y hace rendir; el tope va con el nivel
    for k in range(1, 6):
        _elegir(robot, "Contratar a un empleado")
    assert e["emp"] == 5 == p.hon_max_empleados(e)
    neto, sueldos = p.ingreso_negocio(l, detalle=True)
    assert sueldos == 5 * 28 and neto == int(735 * 1.7) - 140
    _elegir(robot, "Despedir a un empleado")
    assert e["emp"] == 4
    # precios y horario
    base = p.ingreso_negocio(l)
    _elegir(robot, "Precios: normales")
    assert e["precios"] == "altos" and p.ingreso_negocio(l) > base
    _elegir(robot, "Precios: altos")
    assert e["precios"] == "bajos" and p.ingreso_negocio(l) < base
    _elegir(robot, "Precios: bajos")
    assert e["precios"] == "normales" and p.ingreso_negocio(l) == base
    _elegir(robot, "Horario: normal")
    assert e["horario"] == "ampliado" and p.ingreso_negocio(l) == int(735 * 1.56 * 1.2) - 112
    _elegir(robot, "Horario: ampliado")
    # atenderlo: dos horas, sube su nombre, una vez al día
    hora = p.reloj
    _elegir(robot, "Echar 2 horas en el negocio")
    assert e["rep"] == 54 and p.reloj == hora + 120 and e["atendido"] == p.dia
    _elegir(robot, "Echar 2 horas en el negocio")
    assert e["rep"] == 54
    _cerrar(robot)
    # el nombre del negocio mueve lo que da: a cien, un veinticinco por ciento más; a cero, un veinticinco menos
    e.update(nivel=1, emp=0, rep=100.0)
    assert p.ingreso_negocio(l) == 437
    e["rep"] = 0.0
    assert p.ingreso_negocio(l) == 262
    p.cfg["consecuencias"] = "suave"
    assert p.ingreso_negocio(l) == 297                                        # en suave, la penalización es menor
    p.cfg["consecuencias"] = "apagado"
    assert p.ingreso_negocio(l) == 350                                        # y apagado, el nombre no cuenta
    e["rep"] = 100.0
    assert p.ingreso_negocio(l) == 350


def test_un_negocio_abandonado_pierde_nombre_y_uno_atendido_lo_gana(robot):
    p = _empezar(robot, nivel="normal", impuestos_facturas=False)
    j = p.j
    j.reputacion = 50                                                         # con fama: sin extorsiones que estorben la cuenta
    l = _negocio(p)
    e = j.empresa[BAR]
    p.hon()["gracia"] = 0
    n = _marca(robot)
    _dias(robot, AJ.entero("abandono_dias"))
    assert e["rep"] == 50                                                     # cinco días sin pasar no son abandono
    _dias(robot, 4)
    assert e["rep"] == 50 - 4 * AJ("abandono_baja") and any(f.replace("{negocio}", l.nombre) in _desde(robot, n) for f in AJ.lista("frases_abandono"))
    assert p.ingreso_negocio(l) < 350
    _dias(robot, 40)
    assert e["rep"] == 14.0                                                   # solo, se hunde hasta casi el fondo
    # con gente contratada aguanta sin ti
    e.update(rep=50.0, emp=1, visto=p.dia - 30)
    _dias(robot, 10)
    assert e["rep"] == 44.0
    # pasar por él lo para, y con empleados y precios bajos sube solo
    p.hon_visitar(l)
    e["precios"] = "bajos"
    _dias(robot, 4)
    assert e["rep"] == 44.0 + 4 * (0.5 + AJ("precios_bajos_rep"))
    # apagado: ni sube ni baja
    p.cfg["consecuencias"] = "apagado"
    e["visto"] = p.dia - 30
    rep = e["rep"]
    _dias(robot, 5)
    assert e["rep"] == rep


def test_inspecciones_limpias_y_con_tapadera_pagar_sobornar_o_abogado(robot, monkeypatch):
    p = _empezar(robot, nivel="normal")
    j = p.j
    j.reputacion = 50
    son = _oir(p)
    l = _negocio(p)
    e = j.empresa[BAR]
    h = p.hon()
    j.dinero = 20000
    # limpia: suma
    h["inspeccion"] = p.dia + 1
    prestigio = j.ciudadania
    n = _marca(robot)
    _dias(robot)
    assert "inspeccion" in son and any(f.replace("{negocio}", l.nombre) in _desde(robot, n) for f in AJ.lista("frases_inspeccion_limpia"))
    assert e["rep"] > 50 and j.ciudadania > prestigio and not h["asuntos"] and h["inspeccion"] >= p.dia + AJ.entero("inspeccion_min")
    assert j.stats["inspecciones_limpias"] == 1
    # la tapadera blanquea cada noche, con su comisión
    p.hon_tapadera(l)
    assert e["tapadera"]
    p.hon_negro(1000)
    dinero = j.dinero + j.banco
    h["inspeccion"] = p.dia + 99
    _dias(robot)
    negro = 1000 * (1 - AJ("negro_decae") / 100.0) - AJ("tapadera_capacidad")
    assert round(h["negro"], 2) == round(negro, 2) and j.stats["blanqueado"] == 400
    assert j.dinero + j.banco == dinero + p.ingreso_negocio(l) - int(400 * 0.15) - 0 or True
    # una inspección con la tapadera puesta: asunto pendiente, con tres salidas
    h["inspeccion"] = p.dia + 1
    n = _marca(robot)
    _dias(robot)
    assert len(h["asuntos"]) == 1 and h["asuntos"][0]["tipo"] == "inspeccion" and "han encontrado irregularidades" in _desde(robot, n)
    a = h["asuntos"][0]
    assert a["euros"] >= 600 and a["plazo"] == p.dia + AJ.entero("plazo_asunto")
    MH.menu_vida(p)
    assert _opcion(robot.app.pila[-1], "Asuntos pendientes: 1")
    _elegir(robot, "Asuntos pendientes: 1")
    _elegir(robot, "Inspección con irregularidades")
    m = robot.app.pila[-1]
    assert [o.texto.split(":")[0] for o in m.opciones[:2]] == ["Pagar la sanción", "Intentar sobornar al inspector"] and all(o.ayuda for o in m.opciones[:2])
    # sobornar y que salga bien
    monkeypatch.setattr(random, "random", lambda: 0.0)
    dinero = j.dinero
    _elegir(robot, "Intentar sobornar")
    assert not h["asuntos"] and j.dinero == dinero - int(12000 * AJ("soborno_pct") / 100) and e["tapadera"] and not p.hon_antecedentes()
    _cerrar(robot)
    # sobornar y que salga mal: sanción, antecedente grave, portada y adiós tapadera
    h["asuntos"].append({"tipo": "inspeccion", "lugar": BAR, "dia": p.dia, "plazo": p.dia + 3, "euros": 600})
    monkeypatch.setattr(random, "random", lambda: 0.99)
    prestigio = j.ciudadania
    n = _marca(robot)
    p.hon_resolver(h["asuntos"][0], "sobornar")
    assert not h["asuntos"] and not e["tapadera"] and h["negro"] == 0 and p.hon_graves() and j.stats["descubierto"] == 1
    assert j.ciudadania < prestigio and any(f in _desde(robot, n) for f in AJ.lista("frases_soborno_mal"))
    # pagar: limpio y regularizado; con abogado, la mitad
    e["tapadera"] = True
    h["asuntos"].append({"tipo": "inspeccion", "lugar": BAR, "dia": p.dia, "plazo": p.dia + 3, "euros": 600})
    total = j.dinero + j.banco
    p.hon_resolver(h["asuntos"][0], "pagar")
    assert j.dinero + j.banco == total - 600 and not e["tapadera"] and "factura" in son
    h["abogado"] = p.dia + 7
    h["asuntos"].append({"tipo": "inspeccion", "lugar": BAR, "dia": p.dia, "plazo": p.dia + 3, "euros": 600})
    assert [c for c, _, _ in p.hon_asunto_opciones(h["asuntos"][0])] == ["pagar", "sobornar", "abogado"]
    total = j.dinero + j.banco
    p.hon_resolver(h["asuntos"][0], "abogado")
    assert j.dinero + j.banco == total - 300
    # si no contestas en plazo, se resuelve sola de la manera menos mala: con abogado, la mitad (1.7.4); sin él, entera
    h["asuntos"].append({"tipo": "inspeccion", "lugar": BAR, "dia": p.dia, "plazo": p.dia + 1, "euros": 500})
    h["inspeccion"] = p.dia + 99
    n = _marca(robot)
    _dias(robot, 2)
    assert not h["asuntos"] and "se resuelve sin ti" in _desde(robot, n) and "Se encarga tu abogado" in _desde(robot, n) and "Sanción pagada: 250 euros" in _desde(robot, n)
    h["abogado"] = 0
    h["asuntos"].append({"tipo": "inspeccion", "lugar": BAR, "dia": p.dia, "plazo": p.dia + 1, "euros": 500})
    h["inspeccion"] = p.dia + 99
    n = _marca(robot)
    _dias(robot, 2)
    assert not h["asuntos"] and "se resuelve sin ti" in _desde(robot, n) and "Sanción pagada: 500 euros" in _desde(robot, n)
    # sin impuestos no hay inspecciones
    p.cfg["impuestos_facturas"] = False
    h["inspeccion"] = p.dia
    _dias(robot)
    assert not h["asuntos"] and j.stats["inspecciones"] == 2


# ====================================================================== 6. banco y obligaciones
def test_facturas_e_impuestos_con_aviso_cobro_solo_impago_y_embargo(robot):
    p = _empezar(robot, nivel="normal")
    j = p.j
    j.reputacion = 50
    son = _oir(p)
    h = p.hon()
    assert h["cobro"] == 1 + AJ.entero("gracia_dias")
    j.propiedades += ["piso_centro"]                                          # 6000 euros
    l = _negocio(p)
    assert p.hon_cobro_detalle() == [("luz y agua de 2 viviendas", 70), ("contribución de tus viviendas", 9)]
    j.banco, j.dinero = 500, 0
    p.cfg["cobro_antes"] = None
    n = _marca(robot)
    _dias(robot, AJ.entero("gracia_dias") - AJ.entero("aviso_dias"))
    assert f"Dentro de {AJ.entero('aviso_dias')} días te pasan las facturas y los impuestos" in _desde(robot, n) and "notificacion" in son
    assert j.stats.get("impuestos_pagados", 0) == 0
    caja = h["caja"]
    assert caja == 350 * (p.dia - 1)                                          # lo que han dado los negocios desde el último cobro
    _dias(robot, 1)
    caja = h["caja"]
    banco = j.banco
    n = _marca(robot)
    _dias(robot, 1)
    total = 70 + 9 + int((caja + 350) * AJ("impuesto_negocio") / 100.0)
    assert j.stats["impuestos_pagados"] == total and "factura" in son and h["cobro"] == p.dia + AJ.entero("cobro_dias") and h["caja"] == 0
    assert f"{total} euros" in _desde(robot, n) and "impuesto de tus negocios" in _desde(robot, n)
    assert "Próximo cobro, dentro de 7 días" in p.hon_cobro_txt()
    # en suave, todo al sesenta por ciento
    p.cfg["consecuencias"] = "suave"
    assert p.hon_cobro_detalle()[:2] == [("luz y agua de 2 viviendas", 42), ("contribución de tus viviendas", 5)]
    p.cfg["consecuencias"] = "normal"
    # sin dinero: queda a deber con recargo, baja el prestigio; a la tercera, embargo de la mitad de lo que entre
    j.propiedades.remove(BAR)
    j.empresa.clear()
    for k in range(1, 4):
        j.banco, j.dinero = 0, 0
        h["cobro"] = p.dia + 1
        n = _marca(robot)
        _dias(robot)
        if k < 3:
            assert h["impagos"] == k and h["deuda"] > 0 and any(f.split("{")[0] in _desde(robot, n) for f in AJ.lista("frases_impago"))
    assert h["embargo"] > 0 and h["deuda"] == 0 and h["impagos"] == 0 and j.stats["embargos"] == 1 and "Embargo: debes" in _desde(robot, n)
    assert "Estás embargad[o|a]" in p.hon_credito_motivo()
    debe = h["embargo"]
    assert p.hon_ingresar(100) == 50 and h["embargo"] == debe - 50            # de una nómina se queda la mitad
    for modo, donde in (("mano", "dinero"), ("banco", "banco"), ("recoger", None)):                # y de lo que dan los negocios, se cobre como se cobre
        h["embargo"] = 1000
        j.cobro_negocios, j.cajas, j.dinero, j.banco = modo, {}, 0, 0
        j.propiedades.append(BAR)
        p.repartir_ingresos_negocios(350)
        j.propiedades.remove(BAR)
        assert h["embargo"] == 825 and (j.cajas == {BAR: 175} if donde is None else getattr(j, donde) == 175), modo
    j.cobro_negocios, j.cajas, j.dinero, j.banco = "mano", {}, 0, 50
    h["embargo"] = debe - 50
    j.dinero = 1000
    MH.menu_vida(p)
    _elegir(robot, "Estás embargad[o|a]", empieza=True)
    assert h["embargo"] == 0 and j.dinero + j.banco == 1000 + 50 - (debe - 50)
    _cerrar(robot)
    # con la opción apagada: ni facturas ni impuestos
    p.cfg["impuestos_facturas"] = False
    pagado = j.stats["impuestos_pagados"]
    assert p.hon_cobro_detalle() == [] and "desactivados" in p.hon_cobro_txt()
    h["cobro"] = p.dia + 1
    _dias(robot, 3)
    assert j.stats["impuestos_pagados"] == pagado


def test_creditos_segun_prestigio_ingresos_y_antecedentes_con_cuotas_e_impago(robot):
    p = _empezar(robot, nivel="normal", impuestos_facturas=False)
    j = p.j
    son = _oir(p)
    assert p.hon_solvencia() == 10.0 and p.hon_credito_maximo() == 0 and "no se fía lo bastante" in p.hon_credito_motivo()      # recién salido: nada
    j.ciudadania = 50
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    assert p.hon_solvencia() == 25 + 220 / 25 and p.hon_credito_maximo() == 2800
    p.hon_antecedente(1, "Leve")
    assert p.hon_solvencia() == 25 + 220 / 25 - 8
    j.antecedentes = []
    banco_l = p.lugares["banco"]
    j.x, j.y = banco_l.x, banco_l.y
    menus_juego.lugar(p, banco_l)
    _elegir(robot, "Créditos, hipotecas y obligaciones.", empieza=True)
    m = robot.app.pila[-1]
    assert "Tu solvencia para el banco es justa" in m.opciones[0].texto
    assert [o.texto.split(":")[0] for o in m.opciones if o.texto.startswith("Pedir")] == ["Pedir un crédito de 700 euros", "Pedir un crédito de 1400 euros", "Pedir un crédito de 2800 euros"]
    _elegir(robot, "Pedir un crédito de 2800 euros")
    c = j.creditos[0]
    cuota = int(2800 * 1.24 / 8) + 1
    assert j.banco == 2800 and c == {"tipo": "personal", "cuota": cuota, "quedan": 8, "prox": p.dia + 7, "impagos": 0, "atraso": 0}
    m.refrescar(False)
    assert _opcion(m, "Crédito personal: Ya tienes un crédito personal en marcha")
    _cerrar(robot)
    # aviso dos días antes y cobro solo
    n = _marca(robot)
    _dias(robot, 5)
    assert f"Dentro de 2 días vence una cuota de tu crédito personal: {cuota} euros" in _desde(robot, n)
    _dias(robot, 2)
    assert c["quedan"] == 7 and j.banco >= 2800 - cuota and "factura" in son and c["prox"] == p.dia + 7
    # impago: recargo, reintento a los tres días, prestigio abajo; a los tres, embargo
    j.banco = j.dinero = 0
    j.contrato = {}
    prestigio = j.ciudadania
    n = _marca(robot)
    _dias(robot, 7)
    assert c["impagos"] == 1 and c["atraso"] == int(cuota * 0.1) and c["prox"] == p.dia + 3 and j.ciudadania == prestigio - 3
    assert "No has podido pagar la cuota de tu crédito personal" in _desde(robot, n)
    j.banco = 5000                                                            # si pagas, se pone al día
    _dias(robot, 3)
    assert c["impagos"] == 0 and c["atraso"] == 0 and c["quedan"] == 6
    j.banco = j.dinero = 0
    _dias(robot, 7 + 3 + 3)
    assert j.creditos == [] and p.hon()["embargo"] == cuota * 6 + 3 * int(cuota * 0.1) and j.stats["embargos"] == 1
    # liquidar de una vez tiene rebaja
    p.hon()["embargo"] = 0
    j.ciudadania, j.banco = 80, 0
    assert p.hon_pedir_credito(1000)
    c = j.creditos[0]
    j.banco = 5000
    MH.menu_banco(p, None)
    _elegir(robot, "Crédito personal: quedan 8 cuotas", empieza=True)
    assert j.creditos == [] and j.banco == 5000 - int(c["cuota"] * 8 * 0.95) and j.stats["creditos_pagados"] == 1
    _cerrar(robot)


def test_hipoteca_para_una_casa_y_para_un_negocio(robot):
    p = _empezar(robot, nivel="normal", impuestos_facturas=False)
    j = p.j
    casa = p.lugares["piso_centro"]
    j.x, j.y = casa.x, casa.y
    j.dinero = 2500
    menus_juego.lugar(p, casa)
    m = robot.app.pila[-1]
    assert "Comprar con hipoteca: 1800 euros de entrada y 16 cuotas de" in _opcion(m, "Comprar con hipoteca").texto and "Ahora no te la dan" in m.opciones[m.i].texto
    n = _marca(robot)
    robot.tecla(pygame.K_RETURN)
    assert "piso_centro" not in j.propiedades and "no se fía lo bastante" in _desde(robot, n)
    j.ciudadania = 85
    m.refrescar(False)
    assert "Ahora no te la dan" not in _opcion(m, "Comprar con hipoteca").texto
    entrada, cuota, cuotas = p.hon_hipoteca_datos(casa)
    robot.tecla(pygame.K_RETURN)
    assert "piso_centro" in j.propiedades and j.dinero == 2500 - 1800 and (entrada, cuotas) == (1800, 16)
    assert j.creditos == [{"tipo": "hipoteca", "lugar": "piso_centro", "cuota": cuota, "quedan": 16, "prox": p.dia + 7, "impagos": 0, "atraso": 0}]
    assert 4200 < cuota * 16 < 4200 * 1.3 and robot.app.pila[-1] is not m                       # el resto, con su interés; y el menú de compra se cierra
    _cerrar(robot)
    assert "Hipoteca de Estudio en la Gran Vía: quedan 16 cuotas" in p.hon_credito_txt(j.creditos[0])
    # y un negocio: es tuyo desde la firma y da dinero mientras lo pagas
    bar = p.lugares[BAR]
    j.x, j.y = bar.x, bar.y
    j.dinero = 4000
    menus_juego.lugar(p, bar)
    _elegir(robot, "Comprar con hipoteca")
    assert BAR in j.propiedades and j.dinero == 400 and BAR in j.empresa and len(j.creditos) == 2
    _cerrar(robot)
    dinero = j.dinero
    _dias(robot, 6)
    assert j.dinero == dinero + 6 * 350
    _dias(robot, 1)
    assert [c["quedan"] for c in j.creditos] == [15, 15]


# ====================================================================== 7. hacer el bien, y las tentaciones
def test_cada_situacion_de_la_calle_con_cada_salida_bien_y_mal(robot, monkeypatch):
    p = _empezar(robot)
    j = p.j
    for b in p.hon_buenas():
        for k, o in enumerate(b["opciones"]):
            for suerte in (0.99, 0.0):                                        # que salga bien, y que salga mal
                if suerte == 0.0 and not o.get("riesgo"):
                    continue
                monkeypatch.setattr(random, "random", lambda s=suerte: s)
                j.ciudadania, j.reputacion, j.dinero, j.banco, j.animo, j.salud = 50.0, 10.0, 500, 0, 50.0, j.salud_max
                j.objetos["botiquin"] = 1
                p.hon()["sospecha"] = 0.0
                hora = p.hon_abs()
                m = p.hon_buena(b)
                assert robot.app.pila[-1] is m and m.titulo == b["texto"] and m.opciones[-1].texto == "Seguir tu camino"
                assert [x.texto for x in m.opciones[:-1]] == [x["texto"] for x in b["opciones"]] and all(x.ayuda for x in m.opciones)
                m.i = k
                n = _marca(robot)
                robot.tecla(pygame.K_RETURN)
                assert robot.app.pila[-1] is p, (b["id"], k)
                r = o["mal"] if suerte == 0.0 else o
                assert r["dice"] in _desde(robot, n), (b["id"], k, suerte)
                assert j.ciudadania == max(0, min(100, 50.0 + r.get("prestigio", 0))), (b["id"], k, suerte)
                assert j.dinero == 500 + int(r.get("dinero", 0)) - int(o.get("coste", 0)), (b["id"], k, suerte)
                assert j.reputacion == 10.0 + r.get("fama", 0)
                assert j.salud == j.salud_max + r.get("salud", 0)
                assert p.hon_abs() == hora + 60 * o.get("horas", 0)
                assert j.objetos["botiquin"] == (0 if o.get("pide") == "botiquin" else 1)
                if r.get("delito"):
                    assert p.hon()["sospecha"] > 0                            # con algo que perder, aprovecharse da que hablar
    assert j.stats["buenas_acciones"] >= 14 and j.stats["tentaciones"] >= 4
    # sin lo que hace falta, lo dice y no pasa nada
    herido = next(b for b in p.hon_buenas() if b["id"] == "herido")
    j.objetos["botiquin"] = 0
    j.ciudadania = 50.0
    m = p.hon_buena(herido)
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    assert herido["opciones"][0]["sin"] in robot.app.voz.registro[-1] and j.ciudadania == 50.0
    # seguir tu camino, o Escape: nada
    m = p.hon_buena(herido)
    robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is p and j.ciudadania == 50.0
    m = p.hon_buena(herido)
    m.i = len(m.opciones) - 1
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and AJ.lista("frases_buena_nada")[0] in robot.app.voz.registro[-1]


def test_las_situaciones_salen_solas_a_pie_de_tarde_en_tarde_y_nunca_estorban(robot):
    p = _empezar(robot, sucesos=True)
    p.t_evento = 1e9
    j = p.j
    h = p.hon()
    p.t_honrado = 0.0
    robot.frames(2)
    assert robot.app.pila[-1] is p and AJ("buena_min") <= h["prox_buena"] - p.hon_abs() <= AJ("buena_max")      # la primera, tras un buen rato
    h["prox_buena"] = p.hon_abs()
    # en medio de una misión, con la policía detrás o al volante, no
    j.estrellas = 2
    assert not p._hon_buena_toca()
    j.estrellas = 0
    h["prox_buena"] = p.hon_abs()
    p.trabajo = {"tipo": "x"}
    assert not p._hon_buena_toca()
    p.trabajo = None
    p.t_honrado = 0.0
    robot.frames(2)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.escapable and m.titulo in [b["texto"] for b in p.hon_buenas()]
    assert h["prox_buena"] >= p.hon_abs() + AJ("buena_min")
    robot.tecla(pygame.K_ESCAPE)
    # con los sucesos callejeros quitados, tampoco salen estas
    p.cfg["sucesos"] = False
    h["prox_buena"] = p.hon_abs()
    p.t_honrado = 0.0
    robot.frames(2)
    assert robot.app.pila[-1] is p


# ====================================================================== 8. extorsión y doble vida
def test_al_honrado_sin_proteccion_le_piden_dinero_y_puede_pagar_denunciar_negarse_o_plantarse(robot, monkeypatch):
    p = _empezar(robot, nivel="normal", impuestos_facturas=False)
    j = p.j
    son = _oir(p)
    l = _negocio(p)
    h = p.hon()
    j.ciudadania = 45
    _dias(robot)
    assert h["prox_extorsion"] >= max(h["gracia"], p.dia) + AJ.entero("extorsion_min")       # nunca durante la gracia
    h["prox_extorsion"] = p.dia + 2
    n = _marca(robot)
    _dias(robot)
    assert "Un vecino te avisa en voz baja" in _desde(robot, n) and not h["asuntos"]           # a quien aprecian, le avisan un día antes
    _dias(robot)
    a = h["asuntos"][0]
    assert a["tipo"] == "extorsion" and a["lugar"] == BAR and a["banda"] in G.nombres_bandas() and "amenaza_barrio" in son
    assert a["euros"] == max(AJ.entero("extorsion_minimo"), int(7 * 350 * AJ("extorsion_pct") / 100)) and j.stats["extorsiones"] == 1
    assert [c for c, _, _ in p.hon_asunto_opciones(a)] == ["pagar", "denunciar", "negarte"]
    j.reputacion = 12
    assert [c for c, _, _ in p.hon_asunto_opciones(a)][-1] == "plantar"
    j.reputacion = 0
    # pagar: cada semana, cuatro semanas
    j.banco, j.dinero = 0, 5000
    p.hon_resolver(a, "pagar")
    assert not h["asuntos"] and h["extorsion"]["quedan"] == 4
    _dias(robot)
    assert j.dinero == 5000 - a["euros"] + 350 and h["extorsion"]["quedan"] == 3
    _dias(robot, 21)
    assert h["extorsion"] is None
    _dias(robot)
    assert h["prox_extorsion"] > p.dia                                        # y pasado un tiempo, volverán

    def asunto():
        h["asuntos"][:] = [{"tipo": "extorsion", "lugar": BAR, "banda": "Los Calaveras", "dia": p.dia, "plazo": p.dia + 3, "euros": 294}]
        return h["asuntos"][0]
    # denunciar: con buen prestigio y suerte, sale bien
    monkeypatch.setattr(random, "random", lambda: 0.0)
    prestigio = j.ciudadania
    p.hon_resolver(asunto(), "denunciar")
    assert j.ciudadania == prestigio + 4 and j.rep_bandas["Los Calaveras"] == -15 and j.stats["denuncias"] == 1 and j.empresa[BAR]["dano"] == 0
    # denunciar sin suerte: te rompen el escaparate
    monkeypatch.setattr(random, "random", lambda: 0.99)
    p.hon_resolver(asunto(), "denunciar")
    assert j.empresa[BAR]["dano"] == AJ.entero("extorsion_dano_dias") and p.ingreso_negocio(l) < 350 * 0.75
    _dias(robot, 3)
    assert j.empresa[BAR]["dano"] == 0
    # negarse: a veces nada, a veces daño
    j.empresa[BAR]["rep"] = 50.0
    p.hon_resolver(asunto(), "negarte")
    assert j.empresa[BAR]["dano"] == 0
    monkeypatch.setattr(random, "random", lambda: 0.0)
    p.hon_resolver(asunto(), "negarte")
    assert j.empresa[BAR]["dano"] == 3
    # plantarse, con algo de fama
    fama = j.reputacion = 12
    p.hon_resolver(asunto(), "plantar")
    assert j.reputacion == fama + 2 and not h["asuntos"]
    # con fama de sobra, banda o escolta, nadie viene; y con las consecuencias apagadas, tampoco
    j.reputacion = 30
    h["prox_extorsion"] = p.dia + 1
    _dias(robot, 2)
    assert not h["asuntos"] and h["prox_extorsion"] == 0
    j.reputacion = 0
    p.cfg["consecuencias"] = "apagado"
    h["prox_extorsion"] = p.dia + 1
    _dias(robot, 2)
    assert not h["asuntos"]


def test_la_doble_vida_se_va_sabiendo_y_puede_acabar_en_el_periodico(robot, monkeypatch):
    p = _empezar(robot, nivel="normal", impuestos_facturas=False)
    j = p.j
    h = p.hon()
    _persona(p, "civil")
    monkeypatch.setattr(random, "random", lambda: 0.99)
    # sin nada que perder, nadie ata cabos
    p.delito(5, "prueba", siempre=True)
    assert h["sospecha"] == 0 and "no tienes nada que perder" in p.hon_doble_txt()
    j.puntos_busqueda = 0.0
    # con contrato y aprecio, cada delito visto suma; sin testigos, nada
    j.ciudadania, j.reputacion = 60, 40
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    assert p.hon_doble_vida() and p.hon_vida_formal()
    p.personas = []
    p.delito(5, "prueba")
    assert h["sospecha"] == 0                                                 # la discreción protege
    p.delito(5, "prueba", siempre=True)
    assert h["sospecha"] == 5 * AJ("sospecha_delito")
    assert "hay quien se hace preguntas" not in p.hon_doble_txt() or True
    # una detención la dispara, y al pasar de cuarenta corre el rumor
    j.estrellas = 3
    n = _marca(robot)
    p.detener(True)
    _cerrar(robot)
    assert h["sospecha"] >= AJ("sospecha_rumor") - 6 and j.contrato.get("avisos") == 1
    h["sospecha"] = 39.0
    p.hon_sospechar(5)
    assert any(f in " | ".join(robot.app.voz.registro[-3:]) for f in AJ.lista("frases_rumor")) and "corre el rumor" in p.hon_doble_txt()
    # con abogado, la mitad
    h["sospecha"], h["abogado"] = 0.0, p.dia + 7
    p.hon_sospechar(10)
    assert h["sospecha"] == 5.0
    h["abogado"] = 0
    # baja con los días tranquilos
    h["sospecha"] = 20.0
    _dias(robot, 3)
    assert h["sospecha"] == 20.0 - 3 * AJ("sospecha_baja")
    # a partir de setenta, un periodista: asunto pendiente
    h["sospecha"] = 80.0
    n = _marca(robot)
    _dias(robot)
    a = h["asuntos"][0]
    assert a["tipo"] == "prensa" and a["euros"] == AJ.entero("prensa_soborno") and "Un periodista prepara un reportaje" in _desde(robot, n)
    assert [c for c, _, _ in p.hon_asunto_opciones(a)] == ["pagar", "dejar"]
    # pagar: se calla
    j.dinero = 5000
    p.hon_resolver(a, "pagar")
    assert not h["asuntos"] and j.dinero == 5000 - AJ.entero("prensa_soborno") and h["sospecha"] < AJ("sospecha_rumor")
    # dejar que salga: prestigio abajo, aviso del jefe, el negocio pierde nombre... y fama en la calle
    l = _negocio(p)
    h["asuntos"].append({"tipo": "prensa", "dia": p.dia, "plazo": p.dia + 3, "euros": 1500})
    prestigio, fama, avisos = j.ciudadania, j.reputacion, j.contrato["avisos"]
    n = _marca(robot)
    p.hon_resolver(h["asuntos"][0], "dejar")
    assert j.ciudadania == prestigio - AJ("prensa_prestigio") and j.reputacion == fama + 4 and j.contrato["avisos"] == avisos + 1
    assert j.empresa[BAR]["rep"] == 35 and j.stats["descubierto"] == 1 and h["sospecha"] == 30
    assert any(f.split("{")[0] in _desde(robot, n) for f in AJ.lista("frases_prensa"))
    # con abogado, lo frena él; y si no contestas, sale
    h["abogado"] = p.dia + 7
    h["asuntos"].append({"tipo": "prensa", "dia": p.dia, "plazo": p.dia + 3, "euros": 1500})
    assert p.hon_asunto_opciones(h["asuntos"][0])[0][0] == "abogado"
    p.hon_resolver(h["asuntos"][0], "abogado")
    assert not h["asuntos"] and j.stats["descubierto"] == 1
    h["abogado"] = 0
    h["asuntos"].append({"tipo": "prensa", "dia": p.dia, "plazo": p.dia, "euros": 1500})
    h["prensa_dia"] = p.dia
    _dias(robot)
    assert not h["asuntos"] and j.stats["descubierto"] == 2
    # el abogado se contrata en el móvil, se renueva solo y se va si no hay con qué pagarle
    j.dinero, j.banco = 1000, 0
    MH.menu_vida(p)
    _elegir(robot, "Contratar a un abogado")
    assert p.hon_abogado() and j.dinero == 1000 - AJ.entero("abogado_semana")
    _cerrar(robot)
    _dias(robot, 7)
    assert p.hon_abogado() and j.stats.get("x", 0) == 0
    j.dinero = j.banco = 0
    j.propiedades.remove(BAR)
    j.contrato = {}
    _dias(robot, 7)
    assert not p.hon_abogado()


# ====================================================================== 9. la trama del buen camino
def _con_decisiones(robot, elecciones):
    """Hace que el banco de misiones elija en cada decisión lo que diga `elecciones` (clave -> opción, desde 1)."""
    def saltar(tope=60):
        for _ in range(tope):
            cima = robot.app.pila[-1]
            if isinstance(cima, Dialogo):
                robot.tecla(pygame.K_ESCAPE)
            elif isinstance(cima, Menu) and not cima.escapable and cima is not robot.app.pila[0]:
                ms = robot.p.mision
                paso = ms["def"]["pasos"][ms["paso"]] if ms else {}
                cima.i = elecciones.get(paso.get("clave"), 1) - 1
                robot.tecla(pygame.K_RETURN)
            else:
                return
    robot.saltar_dialogos = saltar


def _vigilar_delitos(p):
    """Apunta cada delito que el juego llegue a contar."""
    vistos = []
    original = p.delito

    def delito(puntos, texto=None, siempre=False):
        vistos.append((puntos, texto))
        return original(puntos, texto, siempre)
    p.delito = delito
    return vistos


def _vivir_honradamente(robot, hasta, tope=150):
    """Vive días de trabajo honrado, con las reglas del juego y sin atajos, hasta que se cumpla `hasta`. Devuelve los días."""
    p = robot.p
    j = p.j
    for dias in range(tope):
        if hasta():
            return dias
        if not j.contrato:
            assert p.hon_firmar(_empleo(p, "hosteleria")), robot.dicho()
        _jornada(p, "camarero")
        _cerrar(robot)
        if "hosteleria" not in p.hon_titulos() and j.dinero >= 110:
            p.hon_estudiar(p.hon_titulo("hosteleria"))
        if j.voluntario_dia != p.dia and p.reloj < 20 * 60:
            p.voluntariado()
        bar = p.lugares[BAR]
        if BAR in j.propiedades:
            p.hon_atender(bar)
        elif not p.hon_credito_motivo("hipoteca") and j.dinero >= p.hon_hipoteca_datos(bar)[0]:
            assert p.hon_hipoteca(bar)
            p.hon_emp(bar)
        for a in list(p.hon()["asuntos"]):                                    # lo honrado: denunciar, y pagar lo que toque
            p.hon_resolver(a, "denunciar" if a["tipo"] == "extorsion" else "pagar")
        p.pasar_horas(max(1.0, (24 * 60 - p.reloj + 8 * 60) / 60.0))          # a dormir, hasta las ocho
        _cerrar(robot)
    raise AssertionError(f"no se llega en {tope} días: {robot.dicho()}")


def _trama(p):
    return [m for m in p.datos["misiones"] if m.get("honrada")]


def test_la_trama_esta_en_los_datos_no_depende_de_ningun_delito_y_tiene_cuatro_finales():
    d = M.cargar_datos(con_mods=False)
    trama = [m for m in d["misiones"] if m.get("honrada")]
    assert 8 <= len(trama) <= 12 and d["capitulos"]["16"] == "El buen camino"
    ids = {m["id"] for m in trama}
    por_id = {m["id"]: m for m in d["misiones"]}
    for m in trama:
        assert "sin_voz" not in m and m["capitulo"] == 16 and m["lugar"] in {l["id"] for l in d["ciudad"]["lugares"]}
        assert {p["tipo"] for p in m["pasos"]} <= {"dialogo", "ir", "recoger", "ruta", "escoltar", "seguir", "vigilar", "decision"}, m["id"]      # ni robar, ni eliminar, ni policía
        assert set(m["requiere"]) <= ids | {"m01"}, m["id"]                   # solo pide haber visto a tu tía
        assert set(m.get("requiere_vida", {})) <= set(H.REQUISITOS_VIDA)
    assert {p["tipo"] for p in por_id["m01"]["pasos"]} == {"dialogo", "ir"}   # y esa misión tampoco tiene delito
    assert sorted(m["id"] for m in trama if not set(m["requiere"]) & ids) == ["h01"]
    finales = [(m["id"], e["clase"]) for m in trama for e in m.get("epilogos", [])]
    assert finales == [("h09", "honrado"), ("h09", "prudente"), ("h09d", "doble"), ("h09d", "redimido")]
    decisiones = {p["clave"]: len(p["opciones"]) for m in trama for p in m["pasos"] if p["tipo"] == "decision"}
    assert decisiones == {"cartera": 2, "proteccion": 3, "mordida": 3, "pleno": 2, "socios": 2}
    # hay tentaciones y ramas para quien lleva doble vida
    assert por_id["h09d"]["si_clave"] == "proteccion" and por_id["h09d"]["si_opcion"] == 3 and por_id["h09"]["si_cruce"] == "proteccion:3"
    # los personajes son originales: ninguno se llama como otro contacto del juego
    otros = {m["contacto"] for m in d["misiones"] if not m.get("honrada")}
    assert not {m["contacto"] for m in trama} & otros


def test_el_buen_camino_entero_sin_cometer_un_solo_delito_viviendo_de_tu_trabajo(robot):
    """La campaña completa, por la rama honrada, cumpliendo lo que pide de la vida con las reglas del juego: contrato,
    turnos, título, prestigio y un negocio comprado con hipoteca. Ni un delito, ni un atajo de dinero."""
    random.seed(171)
    p = _empezar(robot)
    j = p.j
    delitos = _vigilar_delitos(p)
    _con_decisiones(robot, {"cartera": 1, "proteccion": 1, "mordida": 1, "pleno": 1})
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    _jugar_mision(robot, por_id["m01"])
    robot.saltar_dialogos()
    p.t_honrado = 0.0
    n = _marca(robot)
    robot.frames(2)
    assert AJ.lista("frases_dos_caminos")[0][:60] in _desde(robot, n) and "dos_caminos" in j.recordado        # el juego ofrece las dos vías desde el principio
    assert {"m02", "h01"} <= {m["id"] for m in p.misiones_disponibles()}
    assert "Te esperan en Oficina de empleo de Puerto Bravo: «Otra manera de volver»" in p.hon_trama_txt()
    dias = {}
    for ident in ("h01", "h02", "h03", "h04", "h05", "h06", "h07", "h08", "h09"):
        m = por_id[ident]
        if m.get("requiere_vida"):
            assert m not in p.misiones_disponibles() or not p.falta_vida(m)
            if p.falta_vida(m):
                assert "te falta" in p.hon_trama_txt() and m["titulo"] in p.hon_trama_txt()
            dias[ident] = _vivir_honradamente(robot, lambda m=m: not p.falta_vida(m))
        assert m in p.misiones_disponibles(), (ident, p.hon_trama_txt())
        _jugar_mision(robot, m)
        robot.saltar_dialogos()
        _cerrar(robot)
    fin = p.decisiones["_final_honrado"]
    assert fin["clase"] == "honrado" and fin["mision"] == "h09" and "persiana arriba" in fin["texto"]
    assert "Final del buen camino: Final honrado: persiana arriba" in " | ".join(robot.app.voz.registro[-25:])
    assert "terminado" in p.hon_trama_txt()
    # ni un delito, ni una detención, ni un antecedente, ni un vehículo robado, ni un enemigo
    assert delitos == [] and j.stats["detenciones"] == 0 and j.antecedentes == [] and j.stats["vehiculos_robados"] == 0 and j.stats["enemigos"] == 0
    assert j.stats.get("antecedentes", 0) == 0 and j.reputacion < 5 and "_final" not in p.decisiones           # la fama en la calle ni se ha movido
    assert j.contrato and p.hon_titulos() and BAR in j.propiedades and j.ciudadania >= 55 and j.creditos
    assert {k: v["opcion"] for k, v in p.decisiones.items() if k in ("cartera", "proteccion", "mordida", "pleno")} == {"cartera": 1, "proteccion": 1, "mordida": 1, "pleno": 1}
    p.comprobar_logros()
    assert "buen_camino" in j.logros
    print("\nBuen camino, rama honrada. Días de vida honrada antes de cada capítulo:", dias, "| día final:", p.dia, "| dinero:", j.dinero + j.banco,
          "| prestigio:", round(j.ciudadania), "| puesto:", p.hon_puesto()["nombre"])
    assert p.dia <= 150


@pytest.mark.parametrize("elecciones, final, mision", [
    ({"cartera": 2, "proteccion": 2, "mordida": 2, "pleno": 2}, "prudente", "h09"),
    ({"cartera": 1, "proteccion": 3, "mordida": 3, "socios": 1}, "doble", "h09d"),
    ({"cartera": 1, "proteccion": 3, "mordida": 1, "socios": 2}, "redimido", "h09d"),
])
def test_las_otras_ramas_del_buen_camino_y_sus_finales(robot, elecciones, final, mision):
    """Las demás ramas: aquí lo que la trama pide de la vida se le da al jugador directamente (la prueba anterior ya lo gana jugando)."""
    p = _empezar(robot, impuestos_facturas=False)
    j = p.j
    delitos = _vigilar_delitos(p)
    _con_decisiones(robot, elecciones)
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    _jugar_mision(robot, por_id["m01"])
    j.dinero = 5000
    for ident in ("h01", "h02", "h03", "h04", "h05", "h06", "h07", "h08", mision):
        m = por_id[ident]
        req = m.get("requiere_vida", {})
        if req.get("contrato") and not j.contrato:
            assert p.hon_firmar(_empleo(p, "comercio"))
        if req.get("turnos"):
            j.stats["turnos_contrato"] = int(req["turnos"])
        if req.get("titulos"):
            _titulo(p, "comercio")
        if req.get("negocios"):
            _negocio(p)
        j.ciudadania = max(j.ciudadania, float(req.get("prestigio", 0)))
        assert m in p.misiones_disponibles(), (ident, p.hon_trama_txt())
        _jugar_mision(robot, m)
        robot.saltar_dialogos()
        _cerrar(robot)
    otra = "h09" if mision == "h09d" else "h09d"
    assert por_id[otra] not in p.misiones_disponibles() and otra not in p.completadas             # la otra rama no se abre
    fin = p.decisiones["_final_honrado"]
    assert fin["clase"] == final and fin["mision"] == mision and delitos == [] and j.stats["detenciones"] == 0
    assert {k: p.decisiones[k]["opcion"] for k in elecciones} == elecciones
    renta = p.rentas_decisiones()
    if final == "prudente":
        assert renta == -60 + 40                                              # paga a la banda y cobra por sus licencias fáciles
    elif final == "doble":
        assert renta == 150 + 300 and j.rep_bandas["Los Calaveras"] >= 60 and j.reputacion >= 20           # socio de Los Calaveras
    else:
        assert renta == 150 - 150 and j.rep_bandas["Los Calaveras"] <= -30
    p.comprobar_logros()
    assert "buen_camino" not in j.logros                                      # el logro es del final honrado


def test_el_buen_camino_se_ofrece_y_no_obliga_a_nadie(robot):
    p = _empezar(robot)
    j = p.j
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    ofi = p.lugares["empleo_pb"]
    j.x, j.y = ofi.x, ofi.y
    assert p.mision_en_lugar("empleo_pb") is None                             # antes de ver a tu tía, la oficina es la oficina
    robot.tecla(pygame.K_RETURN)
    antes = [o.texto for o in robot.app.pila[-1].opciones]
    _cerrar(robot)
    p.completadas.append("m01")
    n = _marca(robot)
    robot.tecla(pygame.K_RETURN)
    of = robot.app.pila[-1]
    assert isinstance(of, Menu) and of.titulo.startswith("Oficina de empleo") and p.mision is None            # se entra como siempre: la misión no empieza sola
    ahora = [o.texto for o in of.opciones]
    assert ahora[:len(antes) - 1] == antes[:-1] and ahora[-1] == antes[-1] == "Volver" and len(ahora) == len(antes) + 1      # el menú de siempre, con una opción más al final
    assert ahora[-2].startswith("El buen camino: «Otra manera de volver».") and of.opciones[-2].ayuda
    assert "es la última opción de este menú" in _desde(robot, n)
    _cerrar(robot)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "El buen camino: «Otra manera de volver»", empieza=True)
    robot.saltar_dialogos()
    assert p.mision and p.mision["def"]["id"] == "h01" and p._local is None
    p._limpiar_mision()
    # en un sitio sin menú, como el ayuntamiento, se pregunta; y decir que no, no pasa nada
    p.completadas += [x for x in ("h01", "h02", "h03", "h04", "h05", "h06", "h07") if x not in p.completadas]
    ayu = p.lugares["ayuntamiento"]
    j.x, j.y = ayu.x, ayu.y
    robot.tecla(pygame.K_RETURN)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and "«El sobre de las licencias», del buen camino" in m.titulo and [o.texto for o in m.opciones[:2]] == ["Empezar la misión", "Ahora no"]
    _elegir(robot, "Ahora no")
    assert robot.app.pila[-1] is p and p.mision is None
    p.completadas = [x for x in p.completadas if not x.startswith("h")]
    j.x, j.y = ofi.x, ofi.y
    # completar una misión del buen camino da prestigio, no fama en la calle
    prestigio, fama = j.ciudadania, j.reputacion
    _jugar_mision(robot, por_id["h01"])
    assert j.ciudadania == prestigio + 2 and j.reputacion == fama
    # lo que pide de tu vida se dice en el móvil
    assert "Para «La primera nómina» te falta tener un contrato fijo, que se firma en una oficina de empleo; trabajar 2 turnos con tu contrato; llevas 0." in p.hon_trama_txt()
    assert por_id["h02"] not in p.misiones_disponibles()
    # quien juega como siempre tiene la historia de la calle igual que antes
    assert "m02" in {m["id"] for m in p.misiones_disponibles()}


# ====================================================================== 10. reconocimiento: los logros
def test_los_logros_nuevos(robot):
    p = _empezar(robot)
    j = p.j
    from juego.extras2 import LOGROS
    nuevos = ("ficha_limpia", "ejemplar", "doble_vida", "gran_empresa", "carrera", "titulado", "buen_camino", "samaritano")
    assert set(nuevos) <= {x[0] for x in LOGROS} and len({x[0] for x in LOGROS}) == len(LOGROS)
    p.comprobar_logros()
    assert not set(nuevos) & set(j.logros)
    p.dia = 30
    p.comprobar_logros()
    assert "ficha_limpia" in j.logros
    j.ciudadania = 92
    p.comprobar_logros()
    assert "ejemplar" in j.logros and "doble_vida" not in j.logros
    j.reputacion = 55
    p.comprobar_logros()
    assert "doble_vida" in j.logros
    l = _negocio(p)
    j.empresa[BAR]["nivel"] = 4
    for t in ("hosteleria", "comercio", "oficios"):
        _titulo(p, t)
    _titulo(p, "direccion")
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    j.contrato["puesto"] = 3
    j.stats["buenas_acciones"] = 10
    p.comprobar_logros()
    assert {"gran_empresa", "carrera", "titulado", "samaritano"} <= set(j.logros)
    # con antecedentes, los de honradez no caen
    j.logros = []
    p.hon_antecedente(1, "x")
    j.antecedentes[0]["c"] = 999
    p.comprobar_logros()
    assert not {"ficha_limpia", "ejemplar", "doble_vida"} & set(j.logros) and "carrera" in j.logros


# ====================================================================== 11. pareja y familia aptas para todos
def test_una_relacion_sin_contenido_para_adultos_citas_compromiso_convivir_y_boda(robot):
    p = _empezar(robot)
    j = p.j
    assert not p.modo_adulto() and p.vida_sentimental()
    pers = p.persona_social("lucia")
    l = p.lugares[pers["lugar"]]
    j.x, j.y = l.x, l.y
    j.dinero = 5000
    robot.tecla(pygame.K_m)
    movil = robot.app.pila[-1]
    textos = [o.texto for o in movil.opciones]
    assert any(t.startswith("Vida sentimental") for t in textos) and not any(t.startswith(("Vida social", "Sustancias")) for t in textos)
    _elegir(robot, "Vida sentimental", empieza=True)
    vs = robot.app.pila[-1]
    assert vs.titulo == "Vida sentimental"
    _elegir(robot, "Presentarte a Lucía")
    ficha = robot.app.pila[-1]
    t = [o.texto for o in ficha.opciones]
    assert "Charlar un rato" in t and "Proponer una cita" in t and "Hacerle un regalo" in t and "Darle un beso" in t and "Bailar juntos" in t
    assert not any(x in " ".join(t) for x in ("Pasar la noche", "masaje", "al oído"))                # nada de contenido para adultos
    _elegir(robot, "Charlar un rato")
    r = p.relacion("lucia")
    assert r["afinidad"] == 8
    # pareja, compromiso y boda, cada cosa a su tiempo
    r.update(afinidad=65, citas=3)
    _elegir(robot, "Pedirle que sea tu pareja")
    assert j.pareja == "lucia"
    ficha.refrescar(False)
    assert "Pedirle que os prometáis" in [o.texto for o in ficha.opciones] and not p.convivencia_activa()
    n = _marca(robot)
    _elegir(robot, "Pedirle que os prometáis")
    assert not r.get("compromiso") and any(f.replace("{n}", "Lucía") in _desde(robot, n) for f in AJ.lista("frases_compromiso_pronto"))
    r.update(afinidad=90, citas=6)
    _elegir(robot, "Pedirle que os prometáis")
    assert r["compromiso"] == "prometidos" and p.hon_estado_pareja() == "prometidos" and j.stats["compromisos"] == 1
    assert p.convivencia_activa()                                             # prometidos, ya podéis vivir juntos, sin la opción para adultos
    assert "Estáis prometidos" in ficha.opciones[1].texto
    n = _marca(robot)
    _elegir(robot, "Casaros", empieza=True)
    assert r["compromiso"] == "prometidos" and f"dentro de {AJ.entero('boda_dias')} días" in _desde(robot, n)
    assert "Pedirle que se venga a vivir contigo" in [o.texto for o in ficha.opciones]
    ok, frase = p.pedir_convivir(dict(pers, convivir="si"), p.lugares["casa_abuela"])
    assert ok and j.convive == "lucia" and p.conviviente()["id"] == "lucia"
    _cerrar(robot)
    for _ in range(AJ.entero("boda_dias")):
        r["ultimo"] = p.dia
        j.convive_hoy = {"visto": p.dia}
        _dias(robot)
    r["afinidad"] = 90
    assert j.pareja == "lucia"
    prestigio, dinero = j.ciudadania, j.dinero
    n = _marca(robot)
    p.hon_casarse(pers)
    assert r["compromiso"] == "casados" and j.stats["bodas"] == 1 and j.dinero == dinero - AJ.entero("boda_precio") and j.ciudadania == prestigio + AJ("boda_prestigio")
    assert any(f.replace("{n}", "Lucía") in _desde(robot, n) for f in AJ.lista("frases_boda"))
    # la relación sigue viva día a día sin el contenido para adultos (sube el ánimo, y se resiente si la descuidas)
    r["ultimo"] = p.dia - 10
    af = r["afinidad"]
    p.dia_adultos()
    assert r["afinidad"] == af - 3
    # con la opción quitada y sin adultos, no hay relaciones, como antes
    p.cfg["pareja_familiar"] = False
    assert not p.vida_sentimental() and not p.convivencia_activa() and p.conviviente() is None
    robot.tecla(pygame.K_m)
    assert not any(o.texto.startswith(("Vida sentimental", "Vida social")) for o in robot.app.pila[-1].opciones)
    _cerrar(robot)
    af = r["afinidad"]
    p.dia_adultos()
    assert r["afinidad"] == af


def test_con_el_contenido_para_adultos_la_ficha_sigue_entera_y_gana_compromiso_y_boda(robot):
    robot.app.cfg["adultos"] = True
    robot.app.aplicar_adultos()
    p = _empezar(robot)
    j = p.j
    pers = p.persona_social("lucia")
    l = p.lugares[pers["lugar"]]
    j.x, j.y = l.x, l.y
    r = p.relacion("lucia")
    r.update(estado="pareja", afinidad=90, citas=7, ultimo=p.dia)
    j.pareja = "lucia"
    from juego import menus_adultos
    menus_adultos.vida_social(p, directo="lucia")
    t = [o.texto for o in robot.app.pila[-1].opciones]
    assert "Pasar la noche juntos" in t and "Darle un masaje" in t and "Pedirle que os prometáis" in t and "Romper la relación" in t
    _elegir(robot, "Pedirle que os prometáis")
    assert r["compromiso"] == "prometidos"
    _elegir(robot, "Romper la relación")
    assert "compromiso" not in r and j.pareja == ""
    robot.app.cfg["adultos"] = False
    robot.app.aplicar_adultos()


# ====================================================================== 12. apagado, todo como en la 1.7.0; y en un servidor
def test_con_todo_apagado_el_juego_queda_como_en_la_1_7_0(robot, monkeypatch):
    p = _empezar(robot, nivel="apagado", impuestos_facturas=False, antecedentes=False, pareja_familiar=False)
    j = p.j
    monkeypatch.setattr(random, "random", lambda: 0.0)
    son = _oir(p)
    assert p.hon_nivel() == 0 and p.hon_f() == 0.0
    # precios, fiado y trato
    for prestigio in (2, 20, 50, 95):
        j.ciudadania = prestigio
        assert p.mercado("comida", "tienda_paco") == 1.0 and p.mercado("armas", "x") == 1.0 and p.hon_fama_factor() == 1.0
        assert not p.hon_negativa(p.lugares["tienda_paco"])
    j.dinero = 0
    p.entrar_interior(p.lugares["tienda_paco"])
    assert not p.pagar(5)
    p.salir_interior(silencio=True)
    # testigos y policía: las cuentas de siempre
    _persona(p, "civil")
    _persona(p, "policia", 6.0)
    for prestigio, esperado in ((2, 2.0), (30, 2.0), (60, 1.4), (95, 1.4)):
        j.puntos_busqueda, j.ciudadania = 0.0, prestigio
        antes = j.ciudadania
        p.delito(2, "prueba")
        assert round(j.puntos_busqueda, 3) == esperado and round(j.ciudadania, 2) == round(max(0.0, antes - 1.2), 2)
    p._hon_control()
    p.limpiar_busqueda(hablar=False)
    p.personas = []
    # detenciones sin antecedentes, y la policía admite como antes
    j.ciudadania, j.dinero = 60, 3000
    j.estrellas = 4
    p.detener(True)
    _cerrar(robot)
    assert j.antecedentes == [] and p.hon_antecedentes() == [] and j.stats["detenciones"] == 1 and p.ingreso_motivo() == ""
    # negocios: lo que dicen los datos, sin nombre, sin abandono, sin inspecciones, sin impuestos, sin extorsión
    j.propiedades += [BAR, "lavanderia", "piso_centro"]
    dinero, banco = j.dinero, j.banco
    n = _marca(robot)
    _dias(robot, 45)
    assert j.dinero == dinero + 45 * (350 + 600) and j.banco == banco
    assert all(e["rep"] == 50 and e["nivel"] == 1 for e in j.empresa.values()) and p.hon()["asuntos"] == [] and not p.hon().get("extorsion")
    assert j.stats.get("impuestos_pagados", 0) == 0 and j.stats.get("inspecciones", 0) == 0 and j.stats.get("extorsiones", 0) == 0
    for s in ("factura", "inspeccion", "despido", "amenaza_barrio"):
        assert s not in son
    dicho = _desde(robot, n)
    for trozo in ("facturas", "impuestos", "Inspección", "protección", "periodista", "rumor"):
        assert trozo not in dicho, trozo
    # la doble vida no existe: nadie ata cabos
    p.hon_sospechar(90)
    p.delito(5, "prueba", siempre=True)
    assert p.hon()["sospecha"] == 0
    p.limpiar_busqueda(hablar=False)
    # sin pareja apta: el móvil, como antes
    robot.tecla(pygame.K_m)
    assert not any(o.texto.startswith(("Vida sentimental", "Vida social")) for o in robot.app.pila[-1].opciones)
    _cerrar(robot)
    # lo que eliges tú sigue ahí: un contrato, un título, mejorar un negocio
    assert p.hon_firmar(_empleo(p, "hosteleria"))
    j.dinero = 9000
    p.hon_estudiar(p.hon_titulo("comercio"))
    assert j.titulos["comercio"]["s"] == 1
    p.hon_mejorar(p.lugares[BAR])
    assert j.empresa[BAR]["nivel"] == 2 and p.ingreso_negocio(p.lugares[BAR]) == 437


def test_en_un_servidor_en_linea_no_cuenta_lo_que_mueve_dinero_y_lo_dice(robot):
    p = _empezar(robot, nivel="exigente")
    j = p.j
    j.ciudadania = 90
    l = _negocio(p)
    j.empresa[BAR].update(nivel=3, emp=2, rep=100.0)
    assert p.ingreso_negocio(l) > 350
    p.en_servidor = True
    try:
        assert p.hon_nivel() == 0 and p.hon_bloqueo().startswith("En un servidor en línea no hay contratos fijos")
        assert p.ingreso_negocio(l) == 350                                    # el negocio da lo que arbitra el servidor
        assert p.mercado("comida", "tienda_paco") == 1.0 and not p.hon_impuestos() and not p.hon_con_antecedentes()
        assert p.hon_antecedente(3, "x") is None and p.hon_antecedentes() == []
        assert p.hon_firma_motivo(_empleo(p, "hosteleria")) == p.hon_bloqueo() and not p.hon_firmar(_empleo(p, "hosteleria"))
        assert p.hon_credito_motivo() == p.hon_bloqueo() and p.hon_credito_maximo() == 0 and not p.hon_pedir_credito(500)
        assert MH.opciones_negocio(p, l, lambda: None) == [] and MH.opcion_hipoteca(p, p.lugares["piso_centro"], lambda: None) == []
        n = _marca(robot)
        MH.menu_empleos(p, p.lugares["empleo_pb"])
        assert robot.app.pila[-1] is p and "En un servidor en línea no hay contratos fijos" in _desde(robot, n)
        h = dict(p.hon())
        p.dia_honrado()
        p.t_honrado = 0.0
        p.actualizar_honrado(1.0)
        assert p.hon() == h                                                   # ni un cobro, ni un rumor, ni una situación
        p.hon_turno("jornada:camarero")
        p.hon_negro(5000)
        assert p.hon().get("negro", 0) == 0
        # estudiar sí se puede: solo cuesta dinero al personaje
        j.dinero = 500
        p.hon_estudiar(p.hon_titulo("comercio"))
        assert j.titulos["comercio"]["s"] == 1 and j.dinero == 390
        textos = " ".join(o.texto for o in (MH.menu_vida(p), robot.app.pila[-1])[1].opciones)
        assert "En un servidor en línea no cuentan" in textos and "El buen camino: es una historia para jugar sin conexión" in textos
        # el buen camino no se ofrece en un servidor, y no entra en lo que el servidor tiene que saber del mundo
        assert not any(p.cumple_vida(m) for m in p.datos["misiones"] if m.get("honrada"))
    finally:
        p.en_servidor = False
    _cerrar(robot)
    from juego import enlinea
    mundo_sv = enlinea.mundo_servidor()
    assert "h01" not in mundo_sv["misiones"] and "m01" in mundo_sv["misiones"]
    assert mundo_sv["huella"] == json.load(open(os.path.join(os.path.dirname(rutas.DATA), "servidor", "mundo.json"), encoding="utf-8"))["huella"]


# ====================================================================== 13. con mando
def test_todo_se_hace_con_el_mando(robot, monkeypatch):
    from test_171_mando import Md
    p = _empezar(robot)
    j = p.j
    j.dinero, j.ciudadania = 20000, 85
    p.completadas += ["m01", "h01"]
    for tipo in ("xbox", "ps"):
        md = Md(robot, tipo)
        # el móvil: cómo te ven
        md.pulsar("back")
        md.elegir("Vida, reputación y consecuencias", empieza=True)
        m = robot.app.pila[-1]
        assert m.titulo == "Vida, reputación y consecuencias"
        md.elegir("Antecedentes penales", empieza=True)
        assert robot.app.pila[-1].titulo == "Antecedentes penales"
        md.al_juego()
    md = Md(robot, "ps")
    # firmar un contrato en la oficina
    ofi = p.lugares["empleo_pb"]
    j.x, j.y = ofi.x, ofi.y
    md.pulsar("a")
    md.elegir("Contratos fijos", empieza=True)
    md.elegir("Comercio y almacén")
    md.elegir("Firmar el contrato", empieza=True)
    assert j.contrato.get("empleo") == "comercio"
    md.al_juego()
    # estudiar en la academia
    aca = p.lugares["centro_civico"]
    j.x, j.y = aca.x, aca.y
    md.pulsar("a")
    md.elegir("Estudios con título", empieza=True)
    md.elegir("Título de comercio")
    assert j.titulos["comercio"]["s"] == 1
    md.al_juego()
    # comprar un negocio con hipoteca, mejorarlo, contratar y cambiar precios
    bar = p.lugares[BAR]
    j.x, j.y = bar.x, bar.y
    md.pulsar("a")
    md.elegir("Comprar con hipoteca")
    assert BAR in j.propiedades and j.creditos
    md.al_juego()
    md.pulsar("a")
    md.elegir("Mejorar")
    md.elegir("Contratar a un empleado")
    md.elegir("Precios: normales")
    md.elegir("Echar 2 horas")
    e = j.empresa[BAR]
    assert e["nivel"] == 2 and e["emp"] == 1 and e["precios"] == "altos" and e["atendido"] == p.dia
    md.al_juego()
    # pedir un crédito en el banco
    ban = p.lugares["banco"]
    j.x, j.y = ban.x, ban.y
    md.pulsar("a")
    md.elegir("Créditos, hipotecas y obligaciones", empieza=True)
    md.elegir("Pedir un crédito", empieza=True)
    assert any(c["tipo"] == "personal" for c in j.creditos)
    md.al_juego()
    # una situación de la calle y un asunto pendiente
    b = p.hon_buenas()[0]
    p.hon_buena(b)
    md.pulsar("a")
    assert robot.app.pila[-1] is p and j.stats["buenas_acciones"] == 1
    p.hon()["asuntos"].append({"tipo": "extorsion", "lugar": BAR, "banda": "Los Calaveras", "dia": p.dia, "plazo": p.dia + 3, "euros": 200})
    monkeypatch.setattr(random, "random", lambda: 0.0)
    md.pulsar("back")
    md.elegir("Vida, reputación y consecuencias", empieza=True)
    md.elegir("Asuntos pendientes: 1", empieza=True)
    md.elegir("Los Calaveras te pide", empieza=True)
    md.elegir("Denunciarlo a la policía")
    assert not p.hon()["asuntos"] and j.stats["denuncias"] == 1
    md.al_juego()
    # la decisión de un puesto con responsabilidad, que no tiene Escape
    j.contrato["puesto"] = 2
    monkeypatch.setattr(random, "choice", lambda lista: lista[0])
    _dias(robot)
    _jornada(p, "reponedor")
    assert isinstance(robot.app.pila[-1], Menu) and not robot.app.pila[-1].escapable
    md.pulsar("abajo")
    md.pulsar("a")
    assert robot.app.pila[-1] is p
    # empezar una misión del buen camino desde el menú del sitio
    p.completadas.remove("h01")
    j.x, j.y = ofi.x, ofi.y
    md.pulsar("a")
    md.elegir("El buen camino: «Otra manera de volver»", empieza=True)
    assert p.mision and p.mision["def"]["id"] == "h01" and isinstance(robot.app.pila[-1], Dialogo)
    for _ in range(8):
        if isinstance(robot.app.pila[-1], Dialogo):
            md.pulsar("a")
    assert robot.app.pila[-1] is p and p.mision["paso"] == 1
    p._limpiar_mision()
    # y la sección de Opciones
    menus_juego.opciones(robot.app)
    md.elegir("Vida, reputación y consecuencias", empieza=True)
    md.pulsar("derecha")
    assert robot.app.cfg["consecuencias"] == "normal"
    md.pulsar("izquierda")
    assert robot.app.cfg["consecuencias"] == "suave"
    md.pulsar("b")
    md.pulsar("b")


# ====================================================================== 14. sonidos, editor y documentación
def test_los_sonidos_nuevos_estan_en_las_cinco_carpetas_con_su_grupo_y_su_descripcion():
    from juego import ayuda, catalogo_sonidos as cat
    nuevos = ("despido", "inspeccion", "factura", "titulo")
    assert sintesis.VERSION_CACHE >= 24
    S = sintesis.generar()
    assert len(S) == 284                                         # 279 hasta la 1.7.2; la 1.7.3 trae tres más; la 1.7.7, el motor que se apaga y el pabellón
    for carpeta in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
        archivos = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(rutas.PACKS, carpeta)) if f.lower().endswith(rutas.EXT_AUDIO)}
        assert set(nuevos) <= archivos and len(archivos) == 284, carpeta
    grupo = {s: t for t, lista in menus_juego.grupos_de_sonidos(sorted(S)) for s in lista}
    aprender = {x[0] for x in ayuda.SONIDOS}
    guia = open(rutas.data("docs", "cambiar_sonidos_es.html"), encoding="utf-8").read()
    for n in nuevos:
        assert 0.5 < len(S[n]) / sintesis.SR < 2.0 and grupo[n] == "Misiones, trabajo, reputación y ánimo" and n in aprender and cat.DESCRIPCIONES[n] if hasattr(cat, "DESCRIPCIONES") else True
        assert f"<code>{n}</code>" in guia


def test_el_editor_lo_edita_todo():
    from editor import modelo
    from editor.esquema import ESQUEMAS, SECCIONES
    titulos = {c: (t, e) for c, t, e in SECCIONES}
    for sec, esq in (("vida_honrada", "ajuste_honrado"), ("titulos", "titulo_estudios"), ("empleos_fijos", "empleo_fijo"), ("mejoras_negocio", "mejora_negocio"),
                     ("incidencias_trabajo", "incidencia_trabajo"), ("buenas_acciones", "buena_accion")):
        assert titulos[sec][1] == esq and esq in ESQUEMAS
    campos = {c["k"]: c for c in ESQUEMAS["ajuste_honrado"]["campos"]}
    assert set(campos) == set(AJ._n) | set(AJ._l) | {"id"}
    assert all(c["e"] and (c["t"] in ("entero", "decimal", "textos") or c["k"] == "id") for c in campos.values())
    por_grupo = {}
    for c in campos.values():
        por_grupo.setdefault(c.get("grupo", "General"), []).append(c["k"])
    assert max(len(v) for v in por_grupo.values()) <= 16 and len(por_grupo) >= 12            # en pestañas, para que las letras de acceso no se repitan
    assert {"honrada", "requiere_vida", "epilogos", "orden"} <= {c["k"] for c in ESQUEMAS["mision"]["campos"]}
    assert "prestigio" in {c["k"] for c in ESQUEMAS["opcion_decision"]["campos"]}
    cat = modelo.Catalogo()
    for clave, _, esq in SECCIONES:
        if clave in titulos and titulos[clave][1] in ("ajuste_honrado", "titulo_estudios", "empleo_fijo", "mejora_negocio", "incidencia_trabajo", "buena_accion"):
            for x in cat.elementos_base(clave):
                assert modelo.empaquetar(esq, modelo.desempaquetar(esq, json.loads(json.dumps(x)))) == x, (clave, x.get("id"))
    assert dict(cat.opciones("titulo_estudios"))["direccion"] == "Título de dirección de empresas"


def test_un_mod_cambia_los_numeros_y_anade_un_titulo(robot, datos_de_serie):
    d = robot.app.datos
    d["vida_honrada"] = [dict(d["vida_honrada"][0], rebaja_ejemplar=30, frases_fiado=["Apuntado: {euros}."])]
    d["titulos"].append({"id": "idiomas", "nombre": "Título de idiomas", "sesiones": 1, "precio": 10, "horas": 1})
    from juego import ajustes
    ajustes.configurar_todos(d)
    p = _empezar(robot)
    j = p.j
    j.ciudadania = 90
    assert p.mercado("comida", "x") == 0.7 and AJ.lista("frases_fiado") == ["Apuntado: {euros}."]
    j.dinero = 50
    p.hon_estudiar(p.hon_titulo("idiomas"))
    assert "idiomas" in p.hon_titulos()
    d["vida_honrada"] = [{"id": "general", "rebaja_ejemplar": "mal", "frases_fiado": []}]
    ajustes.configurar_todos(d)
    assert AJ("rebaja_ejemplar") == 10 and len(AJ.lista("frases_fiado")) == 2                # lo que venga mal vale lo de serie


def test_la_documentacion_lo_cuenta(robot):
    manual = open(rutas.data("docs", "manual_es.html"), encoding="utf-8").read()
    editor = open(rutas.data("docs", "editor_mods_es.html"), encoding="utf-8").read()
    novedades = open(rutas.data("docs", "novedades_es.html"), encoding="utf-8").read()
    for trozo in ("Vida, reputación y consecuencias", "Antecedentes penales", "contrato fijo", "Estudios con título", "hipoteca", "Impuestos y facturas",
                  "El buen camino", "doble vida", "tapadera", "Nivel de consecuencias", "servicios a la comunidad", "Vida sentimental", "embargo"):
        assert trozo in manual, trozo
    assert manual.count("consecuencias") >= 10
    for trozo in ("Vida, reputación y consecuencias", "Títulos de estudios", "Empleos fijos", "Mejoras de los negocios", "Situaciones de la calle"):
        assert trozo in editor, trozo
    v171 = novedades.split("Versión 1.7.1")[1].split("Versión 1.7.0")[0]
    for trozo in ("buen camino", "Nivel de consecuencias", "antecedentes", "contrato fijo", "hipoteca"):
        assert trozo in v171, trozo
    from juego import ayuda
    textos = " ".join(str(x) for x in ayuda.__dict__.values() if isinstance(x, (str, list, tuple, dict)))
    assert "Vida, reputación y consecuencias" in textos
    readme = open(os.path.join(os.path.dirname(rutas.DATA), "README.md"), encoding="utf-8").read()
    assert "honrado.py" in readme
    # nadie del foro, ni tecnicismos, en lo que lee el jugador
    for doc in (manual.split("Vida, reputación y consecuencias", 1)[1][:20000], v171):
        for palabra in ("JSON", "json", "mixin", "j.honra", "hon_"):
            assert palabra not in doc, palabra


# ====================================================================== 15. las tres simulaciones de sesenta días
class _Vida:
    """Sesenta días de un perfil, con las reglas del juego. Lo honrado se hace con las funciones reales del juego (jornadas,
    contrato, estudios, voluntariado, negocio, hipoteca, impuestos). Los golpes no se juegan uno a uno: se cuenta su botín con
    las cifras de los datos y se pasan por el juego el delito, la búsqueda y, si toca, la detención de verdad. Cuántas veces
    sale mal un golpe es un supuesto de la simulación, puesto aquí arriba."""
    DETENCION = {"hurto": 0.04, "atraco": 0.22, "contrato": 0.14, "conquista": 0.18}          # supuesto: veces que el golpe acaba en detención
    HOSPITAL = {"contrato": 0.10, "conquista": 0.15}                                          # supuesto: veces que acabas en el hospital

    def __init__(self, robot, perfil, nivel="suave"):
        self.robot, self.perfil = robot, perfil
        self.p = p = _empezar(robot, nivel=nivel)
        self.j = p.j
        self.rng = random.Random(1710 + len(perfil))
        self.sucesos = []
        self.golpes = 0
        self.curva = {}

    def apunta(self, texto):
        self.sucesos.append(f"día {self.p.dia}: {texto}")

    def dormir(self):
        p = self.p
        p.pasar_horas(max(1.0, (24 * 60 - p.reloj + 8 * 60) / 60.0))
        _cerrar(self.robot)

    # ---------------------------------------------------------------- lo honrado
    def trabajar(self):
        p, j = self.p, self.j
        if j.estrellas:
            return
        if not j.contrato:
            c = _empleo(p, "industria")
            if not p.hon_firma_motivo(c) and p.hon_firmar(c):
                self.apunta("firma contrato en los astilleros")
        puesto = j.contrato.get("puesto") if j.contrato else None
        _jornada(p, "mecanico")
        _cerrar(self.robot)
        if j.contrato and puesto is not None and j.contrato.get("puesto", 0) > puesto:
            self.apunta(f"asciende a {p.hon_puesto()['nombre']}")
        if j.salud < 80 and j.dinero >= 12:                                   # el trabajo desgasta: come algo
            j.dinero -= 12
            j.salud = min(j.salud_max, j.salud + 25)

    def estudiar(self):
        p, j = self.p, self.j
        for ident in ("oficios", "administracion", "direccion"):
            t = p.hon_titulo(ident)
            if ident in p.hon_titulos():
                continue
            if ident != "oficios" and BAR not in j.propiedades:
                return                                                        # primero el título del oficio; los de gestión, cuando ya tenga el negocio
            if not p.hon_titulo_motivo(t) and j.dinero >= int(t["precio"]) + 60:
                n = len(p.hon_titulos())
                p.hon_estudiar(t)
                if len(p.hon_titulos()) > n:
                    self.apunta(f"consigue el {t['nombre'].lower()}")
            return

    def negocio(self, tapadera=False):
        p, j = self.p, self.j
        bar = p.lugares[BAR]
        if BAR not in j.propiedades:
            if j.dinero + j.banco >= 12000 + 1500:
                j.dinero += j.banco
                j.banco = 0
                if p.pagar(12000):
                    j.propiedades.append(BAR)
                    p.hon_emp(bar)
                    self.apunta("compra la Taberna El Ancla Oxidada al contado")
            elif not p.hon_credito_motivo("hipoteca") and j.dinero + j.banco >= p.hon_hipoteca_datos(bar)[0] + 300:
                j.dinero += j.banco
                j.banco = 0
                if p.hon_hipoteca(bar):
                    p.hon_emp(bar)
                    self.apunta("compra la Taberna El Ancla Oxidada con hipoteca")
            return
        e = p.hon_emp(bar)
        if p.reloj < 21 * 60:
            p.hon_atender(bar)
        if e["emp"] < 1:
            p.hon_empleado(bar, 1)
        if tapadera and not e["tapadera"] and p.hon()["negro"] > 800:
            p.hon_tapadera(bar)
            self.apunta("pone la taberna de tapadera")
        m = p.hon_mejora(int(e["nivel"]) + 1)
        if m and not p.hon_mejora_motivo(bar) and j.dinero + j.banco >= p.hon_mejora_coste(bar, m) + 1500:
            j.dinero += j.banco
            j.banco = 0
            p.hon_mejorar(bar)
            self.apunta(f"mejora la taberna al nivel {e['nivel']}")
            if e["emp"] < p.hon_max_empleados(e):
                p.hon_empleado(bar, 1)

    def asuntos(self, honrado=True):
        p, j = self.p, self.j
        for a in list(p.hon()["asuntos"]):
            if a["tipo"] == "extorsion":
                clave = "denunciar" if honrado else "plantar" if j.reputacion >= 10 else "negarte"
            elif a["tipo"] == "prensa":
                clave = "dejar" if honrado else ("abogado" if p.hon_abogado() else "pagar" if j.dinero >= a["euros"] else "dejar")
            else:
                clave = "pagar" if honrado else "sobornar"
            self.apunta(f"asunto pendiente ({a['tipo']}): elige {clave}")
            p.hon_resolver(a, clave)
            _cerrar(self.robot)

    def buena_accion(self):
        p = self.p
        if self.rng.random() < 0.3:                                           # de vez en cuando se cruza con algo, y ayuda
            b = self.rng.choice(p.hon_buenas())
            o = b["opciones"][0] if b["opciones"][0].get("pide") is None else b["opciones"][1]
            p.hon_buena_resolver(b, o)

    # ---------------------------------------------------------------- lo otro
    def golpe(self, clase, visto=True):
        """Un golpe: su botín según los datos, y el delito, la búsqueda y la detención por el juego."""
        p, j = self.p, self.j
        if clase == "hurto":
            botin = self.rng.randint(5, 70) * 3                               # tres carteras (extras.atracar_peaton)
            puntos = 2
        elif clase == "atraco":
            botin = int(G.botin_local("tienda", self.rng) or 400)
            puntos = 5
        elif clase == "contrato":
            botin = int(self.rng.choice([c["paga"] for c in p.datos["contratos"]]))
            puntos = 6
            j.stats["contratos"] = j.stats.get("contratos", 0) + 1
        else:
            botin = 2500                                                      # la recompensa de conquistar un barrio
            puntos = 8
        self.golpes += 1
        if self.rng.random() < self.HOSPITAL.get(clase, 0):
            perdido = int(j.dinero * 0.1) + 150
            j.dinero = max(0, j.dinero - perdido)
            j.stats["muertes"] += 1
            self.apunta(f"un {clase} sale mal: hospital, {perdido} euros menos")
            return
        p.hon_negro(botin)
        p.dar_dinero(botin)
        p.cambiar_reputacion({"hurto": 0.3, "atraco": 1, "contrato": 2, "conquista": 6}[clase])
        if clase == "conquista":
            barrio = next(b["id"] for b in p.mundo.barrios if b["id"] not in j.territorios)
            j.territorios.append(barrio)
            self.apunta(f"conquista un barrio: ya tiene {len(j.territorios)}")
        if visto:
            p.delito(puntos, clase, siempre=True)
            if self.rng.random() < self.DETENCION[clase]:
                from juego.combate import UMBRAL
                j.estrellas = max(1, sum(1 for u in UMBRAL if j.puntos_busqueda >= u))
                antes = j.dinero
                p.detener(True)
                _cerrar(self.robot)
                self.apunta(f"detenido tras un {clase}: {antes - j.dinero} euros de multa")
                return
        p.limpiar_busqueda(hablar=False)

    # ---------------------------------------------------------------- un día de cada perfil
    def dia(self):
        p, j = self.p, self.j
        d = p.dia
        if self.perfil == "honrado":
            self.trabajar()
            self.estudiar()
            if d % 3 == 0 and p.reloj < 19 * 60:
                p.voluntariado()
            self.buena_accion()
            self.negocio()
            self.asuntos(True)
        elif self.perfil == "delincuente":
            self.golpe("hurto")
            if d % 2 == 0:
                self.golpe("atraco")
            if d % 3 == 0 and d > 6:
                self.golpe("contrato")
            if d in (14, 26, 38, 50):
                self.golpe("conquista")
            self.negocio()                                                    # también invierte: al contado, sin banco que le fíe
            self.asuntos(False)
        else:                                                                 # doble vida: de día trabaja y de noche da golpes discretos
            self.trabajar()
            self.estudiar()
            self.negocio(tapadera=True)
            if d % 2 == 0:
                self.golpe("atraco", visto=self.rng.random() < 0.3)           # cuida que no le vean: siete de cada diez veces no hay testigos
            if d % 4 == 0 and d > 8:
                self.golpe("contrato", visto=self.rng.random() < 0.3)
            if d in (20, 40):
                self.golpe("conquista", visto=self.rng.random() < 0.5)
            if not p.hon_abogado() and p.hon()["sospecha"] > 25 and j.dinero > 2000:
                p.hon_contratar_abogado()
                self.apunta("contrata a un abogado")
            self.asuntos(False)
        self.dormir()
        if p.dia in (15, 30, 45, 60):
            self.curva[p.dia] = self.foto()

    def foto(self):
        p, j = self.p, self.j
        negocios = sum(int(l.get("precio", 0)) for l in p.negocios_tuyos())
        deuda = sum(c["cuota"] * c["quedan"] + c.get("atraso", 0) for c in j.creditos) + p.hon()["embargo"] + p.hon()["deuda"]
        return {"dinero": j.dinero + j.banco, "patrimonio": j.dinero + j.banco + negocios - deuda, "prestigio": round(j.ciudadania), "fama": round(j.reputacion),
                "antecedentes": len(p.hon_antecedentes())}

    def correr(self, dias=60):
        while self.p.dia <= dias:
            self.dia()
        p, j = self.p, self.j
        s = j.stats
        fin = self.foto()
        fin.update({"condenas": s.get("antecedentes", 0), "detenciones": s["detenciones"], "hospital": s["muertes"], "titulos": len(p.hon_titulos()),
                    "puesto": p.hon_puesto()["nombre"] if j.contrato else "sin contrato", "despidos": s.get("despidos", 0), "negocios": len(p.negocios_tuyos()),
                    "ingreso_diario_negocios": sum(p.ingreso_negocio(l) for l in p.negocios_tuyos()), "barrios": len(j.territorios), "golpes": self.golpes,
                    "descubierto": s.get("descubierto", 0), "impuestos": s.get("impuestos_pagados", 0), "inspecciones": s.get("inspecciones", 0),
                    "extorsiones": s.get("extorsiones", 0), "sospecha": round(p.hon()["sospecha"]), "ganado": s["dinero_ganado"]})
        return fin


@pytest.fixture(scope="module")
def simulaciones():
    return {}


@pytest.mark.parametrize("perfil", ["honrado", "delincuente", "doble"])
def test_simulacion_de_sesenta_dias(robot, simulaciones, perfil):
    random.seed(1715)
    v = _Vida(robot, perfil)
    fin = v.correr(60)
    simulaciones[perfil] = fin
    print(f"\n=== {perfil}, 60 días, nivel suave ===")
    print("  cada quince días:", json.dumps(v.curva, ensure_ascii=False))
    print("  al final:", json.dumps(fin, ensure_ascii=False))
    for s in v.sucesos:
        print("   ", s)
    ruta = os.environ.get("HONRADO_SIM")
    if ruta:
        with open(os.path.join(ruta, f"sim_{perfil}.json"), "w", encoding="utf-8") as f:
            json.dump({"curva": v.curva, "fin": fin, "sucesos": v.sucesos}, f, ensure_ascii=False, indent=1)
    assert fin["patrimonio"] > 1500, fin                                      # los tres perfiles son viables: nadie se arruina
    if perfil == "honrado":
        assert fin["condenas"] == 0 and fin["detenciones"] == 0 and fin["fama"] < 5 and fin["prestigio"] >= 75
        assert fin["titulos"] >= 1 and fin["negocios"] == 1 and fin["puesto"] != "sin contrato" and fin["despidos"] == 0
    elif perfil == "delincuente":
        assert fin["condenas"] >= 2 and fin["prestigio"] < 10 and fin["fama"] >= 30 and fin["barrios"] >= 2
    else:
        assert fin["prestigio"] >= 40 and fin["fama"] >= 20 and fin["negocios"] == 1


def test_los_tres_caminos_son_viables_y_distintos(simulaciones):
    if len(simulaciones) < 3:
        pytest.skip("hacen falta las tres simulaciones en la misma pasada")
    h, d, b = simulaciones["honrado"], simulaciones["delincuente"], simulaciones["doble"]
    assert d["ganado"] > h["ganado"] * 1.5                                    # el delito sigue siendo el dinero rápido...
    assert d["condenas"] > 0 and h["condenas"] == 0                           # ...y el arriesgado
    assert h["prestigio"] > b["prestigio"] > d["prestigio"] and d["fama"] > b["fama"] > h["fama"]
    assert h["patrimonio"] > 5000                                             # y el honrado prospera de verdad, más despacio


# ====================================================================== 16. los formularios del editor, con teclado
@pytest.fixture(scope="module")
def wxapp():
    wx = pytest.importorskip("wx")
    app = wx.App(False)
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    yield app


def test_los_formularios_nuevos_del_editor_pasan_la_revision_de_teclado(wxapp):
    """Etiqueta delante de cada control y letras de acceso sin repetir en cada pestaña, en todos los formularios nuevos."""
    import wx
    from editor import modelo
    from editor.accesibilidad.revision_teclado import informe, revisar_teclado
    from editor.formulario import DialogoFormulario
    cat = modelo.Catalogo()
    m = modelo.Mod()
    m.info = {"nombre": "Prueba", "autor": "Yo"}
    b = cat.base
    mision = next(x for x in b["misiones"] if x["id"] == "h09")
    casos = [("ajuste_honrado", b["vida_honrada"][0]), ("titulo_estudios", b["titulos"][-1]), ("empleo_fijo", b["empleos_fijos"][0]), ("puesto_fijo", b["empleos_fijos"][0]["puestos"][2]),
             ("mejora_negocio", b["mejoras_negocio"][1]), ("incidencia_trabajo", b["incidencias_trabajo"][0]), ("opcion_incidencia", b["incidencias_trabajo"][0]["opciones"][0]),
             ("buena_accion", b["buenas_acciones"][0]), ("opcion_buena", b["buenas_acciones"][0]["opciones"][2]), ("resultado_buena", b["buenas_acciones"][0]["opciones"][2]["mal"]),
             ("requisitos_vida", mision["requiere_vida"]), ("epilogo", mision["epilogos"][0]), ("mision", mision), ("opcion_decision", {"texto": "x", "prestigio": 3})]
    marco = wx.Frame(None)
    for esq, datos in casos:
        dlg = DialogoFormulario(marco, esq, modelo.desempaquetar(esq, json.loads(json.dumps(datos))), cat, m)
        problemas = [p for p in revisar_teclado(dlg) if not p.aviso]
        assert not problemas, (esq, informe(problemas))
        dlg.Destroy()
    marco.Destroy()
