"""Trabajo 1.7.1, tanda 14: lo que contaron los jugadores tras la 1.7.0 (tercera ronda).

A. Ningún vehículo propio se pierde al reintentar una misión. B. La O dice primero dónde está el objetivo. C. La O da
siempre dirección, el móvil guía al paso actual y hay una forma única de volver al objetivo. D. Los desvíos del GPS:
un solo destino, y al acabar el desvío se vuelve al anterior diciéndolo. E. Recuperar el destino cancelado.
F. Ayuda en las persecuciones. H. Dos retoques del actualizador.
"""
import copy
import math
import os

import pygame
import pytest

from juego import destinos as D, mando, menus_juego, mundo as M
from juego.entidades import Objeto, Persona
from juego.menus import Dialogo, Menu

S, C = pygame.KMOD_SHIFT, pygame.KMOD_CTRL


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


def _partida(robot, dinero=5000, **opciones):
    p = robot.nueva_partida()
    for k, v in dict(sucesos=False, patrullas_calle=False, ambulancias=False, charla_peatones="nada", **opciones).items():
        p.cfg[k] = v
    p.t_evento = 1e9
    p.j.dinero = dinero
    p.personas[:] = []
    for v in list(p.vehiculos):
        p.quitar_vehiculo(v)
    if "m01" not in p.completadas:
        p.completadas.append("m01")
    return p


def _coche(p, modelo="utilitario", subir=True, x=None, y=None, mio=False):
    px, py, d = p.mundo.plaza_en(*(p.pos() if x is None else (x, y)))
    v = p.crear_vehiculo(modelo, px, py, d, None)
    if subir:
        p._subir(v, False, callar=True)
    if mio:
        assert p.hacer_mio(v, callar=True)
    return v


def _elegir(robot, trozo):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), (m, robot.dicho()[-300:])
    m.refrescar(False)
    m.i = next(k for k, o in enumerate(m.opciones) if trozo in o.texto)
    robot.tecla(pygame.K_RETURN)


def _al_juego(robot):
    for _ in range(12):
        if robot.app.pila[-1] is robot.p:
            return
        robot.tecla(pygame.K_ESCAPE)
    assert robot.app.pila[-1] is robot.p


def _dialogos(robot):
    for _ in range(40):
        if not isinstance(robot.app.pila[-1], Dialogo):
            return
        robot.tecla(pygame.K_ESCAPE)


def _tecla(robot, k, mod=0):
    """Pulsa una tecla y devuelve lo que el juego ha dicho por ella."""
    n = len(robot.app.voz.registro)
    robot.tecla(k, mod)
    return " | ".join(robot.app.voz.registro[n:])


def _mision(robot, mid):
    p = robot.p
    m = next(x for x in p.datos["misiones"] if x["id"] == mid)
    p.iniciar_mision(m)
    _dialogos(robot)
    robot.frames(5)
    return p.mision


def _propia(robot, pasos, lugar="periodico", titulo="Prueba"):
    """Una misión hecha a medida, con los pasos que hagan falta."""
    p = robot.p
    p.iniciar_mision({"id": "prueba_foro3", "titulo": titulo, "lugar": lugar, "requiere": [], "repetible": True, "pasos": pasos, "recompensa": {"dinero": 10}})
    _dialogos(robot)
    robot.frames(5)
    return p.mision


def _reintentar(robot, como="Reintentar desde el principio", motivo="Te ha visto."):
    p = robot.p
    if p.mision:
        p.fallar_mision(motivo)
    assert "Misión fallida" in robot.app.pila[-1].titulo
    _elegir(robot, como)
    _dialogos(robot)
    robot.frames(5)
    assert robot.app.pila[-1] is p and p.mision is not None


def _inventario(p):
    """Todos los vehículos del jugador, estén donde estén: {"garajes": [...], "calle": [...], "lejos": [...]} por nombre."""
    return {"garajes": sorted(f.get("nombre") or f["modelo"] for g in p.j.garajes.values() for f in g),
            "calle": sorted(v.nombre for v in p.vehiculos if not v.muerto and (p.es_mio(v) or v is p.ultimo_veh or v is p.j.veh) and not v.tag),
            "lejos": sorted(f.get("nombre") or f["modelo"] for f in p.mis_lejos)}


def _radar_a(robot, cosa, filtro="todo"):
    """Deja el radar sobre esa cosa, como si se hubiera llegado a ella con Tabulador, y pulsa la B."""
    p = robot.p
    p.cfg["radar_filtro"] = filtro
    p.radar_lista = p._radar_construir()
    p.radar_idx = next(k for k, e in enumerate(p.radar_lista) if e[3] is cosa)
    return _tecla(robot, pygame.K_b)


def _total(p):
    i = _inventario(p)
    return len(i["garajes"]) + len(i["calle"]) + len(i["lejos"])


# ====================================================================== A. el vehículo al reintentar
def test_la_secuencia_del_aviso_al_garaje_por_el_movil_guardar_mision_fallar_y_reintentar(robot):
    """Tal como lo contó el jugador: manda el coche al garaje con el servicio del móvil, guarda, empieza la misión de
    seguir al prestamista, la falla de verdad, reintenta. El garaje tiene que seguir con el coche: una vez, y siempre."""
    p = _partida(robot)
    v = _coche(p)
    nombre = v.nombre
    robot.tecla(pygame.K_m)
    _elegir(robot, "Servicios")
    _elegir(robot, "Mandar tu vehículo")
    _elegir(robot, "Piso de la abuela")
    _al_juego(robot)
    assert p.j.veh is None and v not in p.vehiculos and _inventario(p) == {"garajes": [nombre], "calle": [], "lejos": []}
    assert menus_juego.escribir_ranura(p, "1")
    l = p.lugares["periodico"]
    p.teletransportar(l.x, l.y)
    robot.frames(3)
    if (p.mision_en_lugar("periodico") or {}).get("id") == "eo1":
        robot.tecla(pygame.K_RETURN)                             # en la puerta, Intro la empieza
    else:
        p.iniciar_mision(next(x for x in p.datos["misiones"] if x["id"] == "eo1"))
    _dialogos(robot)
    robot.frames(5)
    ms = p.mision
    assert ms and ms["def"]["id"] == "eo1" and ms["def"]["pasos"][ms["paso"]]["tipo"] == "seguir"
    # la falla de verdad: llega hasta él y se le pega
    o = ms["movil"]
    p.j.x, p.j.y = p.mundo.punto_libre(o["x"] + 20, o["y"])
    robot.frames(10)
    assert o["visto"]
    for _ in range(450):                                          # mientras espera quieto no mira: te ve cuando ya anda (1.7.6)
        p.j.x, p.j.y = o["x"] + 1.0, o["y"]
        robot.frames(1)
        if p.mision is None:
            break
    assert p.mision is None and "Misión fallida" in robot.app.pila[-1].titulo and "se ha dado cuenta" in robot.app.pila[-1].titulo
    for vez in range(3):
        _reintentar(robot)
        assert _inventario(p) == {"garajes": [nombre], "calle": [], "lejos": []}, vez
        assert math.hypot(p.j.x - l.x, p.j.y - l.y) < 12 and p.j.veh is None
        assert "Tus vehículos siguen donde estaban: 1 en tu garaje" in robot.dicho()
    # «Mis vehículos» lo cuenta igual que el garaje
    p.abandonar_mision()
    robot.tecla(pygame.K_m)
    m = robot.app.pila[-1]
    assert any("Mis vehículos: 0 en la calle y 1 en garajes" in o.texto for o in m.opciones)
    _al_juego(robot)
    # y al guardar y cargar después, sigue ahí
    assert menus_juego.escribir_ranura(p, "2")
    robot.app.empezar_partida(menus_juego.leer_ranura("2"))
    _dialogos(robot)
    assert _inventario(robot.p) == {"garajes": [nombre], "calle": [], "lejos": []}
    # y la partida guardada antes de la misión, también
    robot.app.empezar_partida(menus_juego.leer_ranura("1"))
    _dialogos(robot)
    assert _inventario(robot.p) == {"garajes": [nombre], "calle": [], "lejos": []}


def test_mandarlo_al_garaje_con_la_mision_ya_empezada_que_es_como_se_perdia_en_la_1_7_0(robot):
    """En la 1.7.0, el reintento devolvía los garajes a como estaban al aceptar la misión: el coche mandado al garaje
    después de aceptarla desaparecía de la calle y del garaje. Reproducido con el código de la 1.7.0; aquí no puede pasar."""
    p = _partida(robot)
    v = _coche(p)
    nombre = v.nombre
    _mision(robot, "eo1")
    robot.tecla(pygame.K_m)
    _elegir(robot, "Servicios")
    _elegir(robot, "Mandar tu vehículo")
    _elegir(robot, "Piso de la abuela")
    _al_juego(robot)
    assert _inventario(p) == {"garajes": [nombre], "calle": [], "lejos": []}
    for vez in range(3):
        _reintentar(robot)
        assert _inventario(p) == {"garajes": [nombre], "calle": [], "lejos": []}, vez
    p.abandonar_mision()
    assert menus_juego.escribir_ranura(p, "2")
    robot.app.empezar_partida(menus_juego.leer_ranura("2"))
    _dialogos(robot)
    assert _inventario(robot.p) == {"garajes": [nombre], "calle": [], "lejos": []}


def test_sacarlo_del_garaje_durante_la_mision_no_lo_duplica(robot):
    p = _partida(robot)
    v = _coche(p)
    nombre = v.nombre
    assert p.mandar_al_garaje(v, p.lugares["casa_abuela"])
    _mision(robot, "eo1")
    robot.tecla(pygame.K_m)
    _elegir(robot, "Servicios")
    _elegir(robot, "Que te traigan")
    robot.app.pila[-1].i = 0
    robot.tecla(pygame.K_RETURN)
    _al_juego(robot)
    robot.frames(10)
    assert _inventario(p) == {"garajes": [], "calle": [nombre], "lejos": []}
    for vez in range(3):
        _reintentar(robot)
        assert _inventario(p) == {"garajes": [], "calle": [nombre], "lejos": []}, vez


@pytest.mark.parametrize("mio", [True, False])
def test_el_vehiculo_en_el_que_ibas_viene_contigo_al_reintentar(robot, mio):
    """Ibas en tu coche (o en uno que acababas de coger): tras fallar lejos y reintentar, queda aparcado a tu lado."""
    p = _partida(robot)
    v = _coche(p, mio=mio)
    _mision(robot, "eo1")
    l = p.lugares["periodico"]
    lejos = p.lugares["banco"]
    for vez in range(3):
        p.salir_vehiculo(forzado=True) if p.j.veh else None
        p._subir(v, False, callar=True)
        v.x, v.y = p.mundo.plaza_en(lejos.x, lejos.y)[:2]         # conduces hasta el banco y allí fallas
        robot.frames(3)
        _reintentar(robot)
        assert v in p.vehiculos and not v.muerto and p.j.veh is None and p.es_mio(v) == mio, vez
        assert v.dist(l.x, l.y) < 60 and math.hypot(p.j.x - l.x, p.j.y - l.y) < 12, (vez, v.dist(l.x, l.y))
        assert "viene contigo: queda aparcado a tu lado" in robot.dicho() and p.tu_vehiculo(80) is v
        assert sum(1 for o in p.vehiculos if o.modelo is v.modelo and not o.muerto and o.ia is None) == 1
    assert _total(p) == 1


def test_el_vehiculo_propio_aparcado_lejos_se_queda_donde_estaba(robot):
    p = _partida(robot)
    l = p.lugares["banco"]
    v = _coche(p, x=l.x, y=l.y, mio=True)
    p.salir_vehiculo(forzado=True)
    otro = p.lugares["periodico"]
    p.teletransportar(otro.x, otro.y)
    donde = (v.x, v.y)
    assert v.dist(*p.pos()) > 120
    _mision(robot, "eo1")
    for vez in range(2):
        _reintentar(robot)
        assert v in p.vehiculos and (v.x, v.y) == donde and p.es_mio(v)
    assert _inventario(p) == {"garajes": [], "calle": [v.nombre], "lejos": []}


def test_una_mision_que_da_vehiculo_no_se_lleva_el_tuyo_al_reintentar(robot):
    p = _partida(robot)
    v = _coche(p, mio=True)
    ms = _propia(robot, [{"tipo": "robar", "lugar": "banco", "modelo": "sedan", "abierto": True, "texto": "Llévate el sedán."},
                         {"tipo": "entregar", "lugar": "museo", "texto": "Déjalo en el museo."}])
    banco = p.lugares["banco"]
    p.salir_vehiculo(forzado=True)
    p.teletransportar(banco.x, banco.y)
    robot.frames(10)
    vm = p.mision["veh"]
    assert vm is not None and vm.tag == "mision"
    p._subir(vm, False, callar=True)
    robot.frames(5)
    for vez in range(2):
        _reintentar(robot, motivo="El vehículo ha quedado destruido.")
        assert v in p.vehiculos and not v.muerto and p.es_mio(v), vez
        assert vm.muerto and vm not in p.vehiculos
    assert _inventario(p) == {"garajes": [], "calle": [v.nombre], "lejos": []}


def test_volver_al_punto_de_control_tampoco_pierde_ninguno(robot):
    p = _partida(robot)
    v = _coche(p, mio=True)
    g = _coche(p, "sedan", subir=False, x=p.j.x + 40, y=p.j.y, mio=True)
    assert p.mandar_al_garaje(g, p.lugares["casa_abuela"])
    _propia(robot, [{"tipo": "ir", "lugar": "banco", "texto": "Ve al banco."}, {"tipo": "ir", "lugar": "museo", "texto": "Ve al museo."}])
    banco = p.lugares["banco"]
    v.x, v.y = p.mundo.plaza_en(banco.x, banco.y)[:2]
    for _ in range(90):
        robot.frames(1)
        if p.mision["paso"] == 1:
            break
    assert p.mision["paso"] == 1 and p.mision.get("control")
    museo = p.lugares["museo"]
    v.x, v.y = p.mundo.plaza_en((banco.x + museo.x) / 2, (banco.y + museo.y) / 2)[:2]
    antes = _total(p)
    _reintentar(robot, "Reintentar desde el último punto de control", "Se ha acabado el tiempo.")
    assert p.mision["paso"] == 1 and _total(p) == antes == 2
    assert v in p.vehiculos and v.dist(*p.pos()) < 60 and len(p.j.garajes["casa_abuela"]) == 1


def test_reintentar_desde_otra_localidad_trae_tu_vehiculo_y_no_lo_duplica(robot):
    p = _partida(robot)
    v = _coche(p, mio=True)
    v.nombre = "Rayo"
    _propia(robot, [{"tipo": "ir", "lugar": "banco", "texto": "Ve al banco."}])
    origen = p.mundo.id
    otro = next(k for k, m in p.mapas.items() if k != origen and m.tipo != "mar")
    p.cambiar_mapa(otro, 200, 200)
    assert p.mundo.id == otro and p.j.veh is v and p.mision is not None
    _reintentar(robot)
    l = p.lugares["periodico"]
    assert p.mundo.id == origen and p.j.veh is None
    mios = p.mis_vivos()
    assert len(mios) == 1 and mios[0].nombre == "Rayo" and mios[0].dist(l.x, l.y) < 60 and not p.mis_lejos
    assert _total(p) == 1


def test_una_casa_comprada_durante_la_mision_no_se_queda_con_tus_vehiculos(robot):
    """La casa vuelve a no ser tuya y el dinero vuelve; lo que metiste en su garaje pasa a otro garaje o, si no hay
    sitio, a la calle a tu nombre. Nunca se queda en un garaje al que no puedes entrar."""
    p = _partida(robot, dinero=20000)
    a = _coche(p, mio=True)
    b = _coche(p, "sedan", subir=False, x=p.j.x + 30, y=p.j.y, mio=True)
    abuela = p.lugares["casa_abuela"]
    p.salir_vehiculo(forzado=True)
    assert p.mandar_al_garaje(a, abuela) and p.mandar_al_garaje(b, abuela) and p.garaje_con_sitio() is None
    _mision(robot, "eo1")
    piso = p.lugares["piso_centro"]
    p.j.propiedades.append(piso.id)                               # la compras durante la misión
    p.j.dinero -= 6000
    c = _coche(p, "todoterreno", subir=False, mio=True)
    assert p.mandar_al_garaje(c, piso, cobrar=False)
    assert _total(p) == 3
    _reintentar(robot)
    assert piso.id not in p.j.propiedades and p.j.dinero == 20000 - 200
    assert not p.j.garajes.get(piso.id) and len(p.j.garajes[abuela.id]) == 2
    assert _total(p) == 3 and len(p.mis_vivos()) + len(p.mis_lejos) == 1
    suelto = (p.mis_vivos() + p.mis_lejos)[0]
    assert (suelto.modelo["id"] if not isinstance(suelto, dict) else suelto["modelo"]) == "todoterreno"
    # y con sitio en otro garaje, va a ese garaje
    abuela_plazas = p.j.garajes[abuela.id]
    abuela_plazas.pop()
    p.j.propiedades.append(piso.id)
    p.j.garajes.setdefault(piso.id, []).append({"modelo": "sedan", "salud": 100, "nombre": "El de la casa nueva", "mejoras": {}})
    _reintentar(robot)
    assert piso.id not in p.j.propiedades and not p.j.garajes.get(piso.id)
    assert "El de la casa nueva" in [f["nombre"] for f in p.j.garajes[abuela.id]]


def test_un_barco_tuyo_no_se_pierde_ni_se_duplica_al_reintentar(robot):
    from juego import menus_lugares
    p = _partida(robot)
    emb = p.lugares["emb_puerto"]
    barco = {"modelo": "lancha", "nombre": "La Gaviota", "salud": 80, "en": emb.id}
    p.j.barcos.append(dict(barco))
    _propia(robot, [{"tipo": "ir", "lugar": "banco", "texto": "Ve al banco."}])
    b = p.j.barcos.pop(0)                                         # zarpas con él durante la misión
    menus_lugares._zarpar(p, emb, b["modelo"], b.get("salud"), b.get("nombre"), {"modelo": b["modelo"], "nombre": b.get("nombre")})
    robot.frames(5)
    assert p.mundo.tipo == "mar" and p.j.barco_actual and not p.j.barcos
    if p.mision is None:                                          # hay misiones que no dejan salir al mar: se monta el fallo a mano
        pytest.skip("la misión no sigue en el mar")
    _reintentar(robot)
    assert p.mundo.tipo != "mar" and p.j.barco_actual is None
    assert [(x["modelo"], x["nombre"]) for x in p.j.barcos] == [("lancha", "La Gaviota")]
    assert "queda amarrado" in robot.dicho()
    # y el que amarraste durante la misión no desaparece al rebobinar
    copia = copy.deepcopy(p.j.a_dict())
    copia["barcos"], copia["barco_actual"] = [], {"modelo": "lancha", "nombre": "La Gaviota"}
    p._rebobinar_jugador(copia)
    assert len(p.j.barcos) == 1 and p.j.barco_actual is None


def test_repetir_una_mision_desde_el_diario_usa_el_mismo_camino(robot):
    p = _partida(robot)
    v = _coche(p, mio=True)
    banco = p.lugares["banco"]
    v.x, v.y = p.mundo.plaza_en(banco.x, banco.y)[:2]
    robot.frames(2)
    l = p.lugares["periodico"]
    assert p.llevarte_a(l.mapa, l.x, l.y) is v
    assert p.j.veh is None and v.dist(l.x, l.y) < 60 and p.es_mio(v) and _total(p) == 1
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "juego", "menus_juego.py"), encoding="utf-8").read()
    assert "p.llevarte_a(l.mapa, l.x, l.y)" in src


# ====================================================================== B. la O en las persecuciones
PERSECUCION = [{"tipo": "perseguir", "lugar": "banco", "modelo": "sedan", "nombre": "el sedán del mensajero", "salud": 110,
                "texto": "Persigue el coche del mensajero y destrúyelo a golpes o a tiros. Pulsa Q para fijarlo: oirás dónde está."}]


def _persecucion(robot, limite=None, **opciones):
    p = _partida(robot, **opciones)
    banco = p.lugares["banco"]
    p.teletransportar(banco.x + 40, banco.y)
    _coche(p, "deportivo" if "deportivo" in p.modelos else "sedan")
    pasos = copy.deepcopy(PERSECUCION)
    if limite:
        pasos[0]["limite"] = limite
    ms = _propia(robot, pasos, lugar="banco", titulo="El mensajero")
    assert ms["veh_objetivo"] is not None
    return p, ms, ms["veh_objetivo"]


def test_la_o_en_una_persecucion_dice_primero_donde_esta_y_hacia_donde_va(robot):
    p, ms, vo = _persecucion(robot)
    robot.frames(60)
    assert abs(vo.vel) > 1
    p._o_ultima = None
    t = _tecla(robot, pygame.K_o)
    assert t.startswith(f"{vo.nombre}: a ") and " metros, " in t and ", por " in t and ", va hacia el " in t
    assert "Persigue el coche" not in t and "Misión" not in t                 # la explicación no estorba
    assert t.endswith("Pulsa O dos veces seguidas para oír la explicación de la misión.")
    # dos pulsaciones seguidas: la explicación entera, y también con la posición por delante
    t2 = _tecla(robot, pygame.K_o)
    assert t2.startswith(f"{vo.nombre}: a ") and "Misión El mensajero. Persigue el coche del mensajero" in t2
    # pasado un rato, otra vez la corta, y ya sin repetir cómo se oye la larga
    p._o_ultima = None
    t3 = _tecla(robot, pygame.K_o)
    assert t3.startswith(f"{vo.nombre}: a ") and "Misión" not in t3 and "dos veces" not in t3
    # dos pulsaciones separadas por más tiempo del que dicen los datos no cuentan como doble
    p._o_ultima = (p._o_ultima[0] - D.AJ("doble_o") - 0.5, p._o_ultima[1])
    assert "Misión" not in _tecla(robot, pygame.K_o)


def test_la_o_con_el_tiempo_corriendo_dice_lo_que_queda(robot):
    p, ms, vo = _persecucion(robot, limite=200, ayuda_persecucion=False)
    p._o_ultima = None
    t = _tecla(robot, pygame.K_o)
    assert t.startswith(f"{vo.nombre}: a ") and "Te quedan 19" in t and "Misión" not in t


def test_la_o_siguiendo_a_alguien_a_pie_y_con_un_destino_quieto(robot):
    p = _partida(robot)
    ms = _mision(robot, "eo1")
    # todavía no le has visto: dónde te espera, con metros y dirección
    t = p.objetivo_txt()
    banco = p.lugares["banco"]
    assert t.startswith(f"El prestamista te espera en: {banco.nombre}, ") and " metros, al " in t and "Misión La sombra del prestamista" in t
    o = ms["movil"]
    p.j.x, p.j.y = p.mundo.punto_libre(o["x"] + 20, o["y"])
    robot.frames(10)
    assert o["visto"]
    p._o_ultima = None
    t = _tecla(robot, pygame.K_o)
    assert t.startswith("El prestamista va a ") and " metros, al " in t and "Misión" not in t
    assert "va a" in p.objetivo_txt() and "Síguele por el sonido de sus pasos" in p.objetivo_txt()
    # un destino que no se mueve: todo de una vez, y la posición primero
    p.abandonar_mision()
    _propia(robot, [{"tipo": "ir", "lugar": "museo", "texto": "Lleva el cuadro al museo."}])
    museo = p.lugares["museo"]
    p._o_ultima = None
    t = _tecla(robot, pygame.K_o)
    assert t.startswith(f"Destino: {museo.nombre}, ") and " metros, al " in t and t.rstrip().endswith("Lleva el cuadro al museo.")


@pytest.mark.parametrize("tipo", ["xbox", "ps"])
def test_con_mando_el_objetivo_y_volver_a_el(robot, datos_de_serie, tipo):
    from test_171_mando import Md
    p, ms, vo = _persecucion(robot)
    md = Md(robot, tipo)
    p._o_ultima = None
    n = len(robot.app.voz.registro)
    md.combinar("y")                                             # al volante, el objetivo es la combinación con Y o Triángulo
    t = " | ".join(robot.app.voz.registro[n:])
    assert t.startswith(f"{vo.nombre}: a ") and "Misión" not in t
    assert "dos veces seguidas" in t and "Pulsa O" not in t       # con mando, la frase nombra el botón
    n = len(robot.app.voz.registro)
    md.combinar("y")
    assert "Misión El mensajero" in " | ".join(robot.app.voz.registro[n:])
    # el menú de acciones tiene las dos entradas nuevas, y funcionan
    p.cancelar_gps()
    p.mision["gps_callado"] = True
    md.combinar("rt")
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and m.titulo.startswith("Acciones")
    md.hasta("Volver al objetivo de la misión")
    md.pulsar("a")
    assert robot.app.pila[-1] is p and p.gps is not None and p.gps["sigue"] is vo and "Vuelves al objetivo" in robot.dicho()
    md.combinar("l3")                                            # quitar el GPS
    assert p.gps is None
    md.combinar("rt")
    md.hasta("Recuperar el último destino")
    md.pulsar("a")
    assert p.gps is not None and p.gps["sigue"] is vo


# ====================================================================== C. la misión del museo
def _casete(p, dx=18):
    x, y = p.pos()
    p.objetos[:] = [o for o in p.objetos if o.tipo != "casete"]
    ox, oy = p.mundo.punto_libre(x + dx, y)
    o = Objeto("casete", "Cinta de casete número 1", ox, oy, "loc_casete")
    o.tag = "prueba:1"
    p.objetos.append(o)
    return o


def test_la_mision_del_museo_con_un_desvio_a_una_cinta_de_casete(robot):
    """La secuencia del aviso: misión del cuadro, de camino se marca una cinta con el radar, se recoge y se vuelve."""
    p = _partida(robot)
    p.completadas += ["m02", "m03"]
    museo, deposito = p.lugares["museo"], p.lugares["deposito"]
    p.teletransportar(museo.x, museo.y)
    ms = _mision(robot, "n04")
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "sigilo" and p.gps["nombre"] == deposito.nombre
    # la O da siempre dirección, también la de los vigilantes, y dice el nombre de verdad del sitio
    t = _tecla(robot, pygame.K_o)
    assert t.startswith(f"Destino: {deposito.nombre}, ") and t.count(" metros, al ") == 2 and "el más cercano, a " in t
    # el desvío
    o = _casete(p)
    p.cfg["radar_filtro"] = "objetos"
    p.radar_lista = []
    assert "Cinta de casete" in _tecla(robot, pygame.K_TAB)
    t = _tecla(robot, pygame.K_b)
    assert f"Desvío a {o.nombre}. Al llegar, el GPS vuelve a {deposito.nombre}" in t
    assert p.gps["nombre"] == o.nombre and p.gps["anterior"]["nombre"] == deposito.nombre
    assert o.nombre in _tecla(robot, pygame.K_g)                 # la G dice adónde guía de verdad
    t = _tecla(robot, pygame.K_o)                                # y la O no lo esconde
    assert t.startswith(f"Destino: {deposito.nombre}, ") and f"El GPS está en un desvío a {o.nombre}: con Mayúsculas O vuelves al objetivo." in t
    # se recoge: el GPS vuelve solo a la misión, diciéndolo
    p.j.x, p.j.y = o.x, o.y
    robot.frames(5)
    if o in p.objetos:
        robot.tecla(pygame.K_RETURN)
    robot.frames(40)
    assert o not in p.objetos
    assert f"{o.nombre}: recogido. El GPS vuelve a {deposito.nombre}." in robot.dicho() or f"Has llegado a {o.nombre}. El GPS vuelve a {deposito.nombre}." in robot.dicho()
    assert p.gps["nombre"] == deposito.nombre and p.gps["auto"] and p.gps.get("anterior") is None
    t = _tecla(robot, pygame.K_o)
    assert t.startswith(f"Destino: {deposito.nombre}, ") and "desvío" not in t
    assert deposito.nombre in _tecla(robot, pygame.K_g)
    # el móvil: la misión en curso va la primera y guía al paso actual, no al museo
    p.gps_a_lugar(next(l for l in p.mundo.lugares.values() if l.tipo == "hospital"))      # con otro destino puesto
    robot.tecla(pygame.K_m)
    _elegir(robot, "Misiones disponibles")
    m = robot.app.pila[-1]
    assert m.opciones[0].texto.startswith(f"En curso: Lo que falta en el museo. Destino: {deposito.nombre}, ")
    assert sum(1 for x in m.opciones if "Lo que falta en el museo" in x.texto) == 1      # ya no sale además como disponible
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.gps["nombre"] == deposito.nombre and p.gps["auto"] and "Vuelves al objetivo" in robot.dicho()
    # el móvil tiene además la entrada directa, y la lista de la L empieza por el objetivo
    p.gps_a_lugar(museo)
    robot.tecla(pygame.K_m)
    _elegir(robot, "Volver al objetivo")
    assert robot.app.pila[-1] is p and p.gps["nombre"] == deposito.nombre
    p.gps_a_lugar(museo)
    robot.tecla(pygame.K_l)
    m = robot.app.pila[-1]
    assert m.opciones[0].texto.startswith(f"Objetivo de la misión. Destino: {deposito.nombre}, ")
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and p.gps["nombre"] == deposito.nombre
    # y el sitio está en la lista de lugares con ese mismo nombre
    robot.tecla(pygame.K_l)
    _elegir(robot, "Todos los lugares")
    assert any(x.texto.startswith(deposito.nombre) for x in robot.app.pila[-1].opciones)
    _al_juego(robot)
    # siguiente paso: llevar el cuadro al museo. La O y el GPS pasan a la vez al museo
    p.j.x, p.j.y = deposito.x, deposito.y
    ms["guardias"] = []
    robot.frames(10)
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "ir" and p.gps["nombre"] == museo.nombre
    assert _tecla(robot, pygame.K_o).startswith(f"Destino: {museo.nombre}, ")


def test_mayusculas_o_vuelve_al_objetivo_siempre_igual(robot):
    p = _partida(robot)
    ms = _propia(robot, [{"tipo": "ir", "lugar": "museo", "texto": "Ve al museo."}])
    museo = p.lugares["museo"]
    hospital = next(l for l in p.mundo.lugares.values() if l.tipo == "hospital")
    # 1: con un desvío puesto
    p.gps_a_lugar(hospital)
    assert p.gps["nombre"] == hospital.nombre and p.gps["anterior"]["nombre"] == museo.nombre
    t = _tecla(robot, pygame.K_o, S)
    assert t.startswith(f"Vuelves al objetivo. Destino: {museo.nombre}, ") and "Marcado en el GPS" in t
    assert p.gps["nombre"] == museo.nombre and p.gps["auto"] and p.gps.get("anterior") is None
    # 2: con el GPS quitado a mano
    _tecla(robot, pygame.K_g, S)
    assert p.gps is None and ms["gps_callado"]
    assert _tecla(robot, pygame.K_o, S).startswith("Vuelves al objetivo.") and p.gps["nombre"] == museo.nombre and not ms["gps_callado"]
    # 3: ya estaba marcado: lo dice igual
    assert _tecla(robot, pygame.K_o, S).startswith("Vuelves al objetivo.") and p.gps["nombre"] == museo.nombre
    # 4: cerca del objetivo, queda elegido en el radar, aunque el filtro no lo dejara ver
    p.teletransportar(museo.x + 30, museo.y)
    p.cfg["radar_filtro"] = "personas"
    t = _tecla(robot, pygame.K_o, S)
    assert "elegido en el radar" in t and p.radar_lista[p.radar_idx][3] is museo
    # 5: sin misión ni trabajo, lo dice
    p.abandonar_mision()
    assert "No tienes ninguna misión ni ningún trabajo en curso" in _tecla(robot, pygame.K_o, S)
    # y está en la ayuda de F1 y en el manual
    from juego import ayuda
    assert any(e == "Mayúsculas O" for e, _ in ayuda.TECLAS["general"]) and any(e == "Control G" for e, _ in ayuda.TECLAS["general"])
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manual = open(os.path.join(raiz, "data", "docs", "manual_es.html"), encoding="utf-8").read()
    teclas = open(os.path.join(raiz, "data", "docs", "teclas_es.html"), encoding="utf-8").read()
    for doc in (manual, teclas):
        assert "Mayúsculas O" in doc and "Control G" in doc


# ====================================================================== D. los desvíos
def _con_destino(robot, mision):
    """Una partida con un destino en marcha: el de una misión, o uno marcado por el jugador."""
    p = _partida(robot)
    museo = p.lugares["museo"]
    if mision:
        _propia(robot, [{"tipo": "ir", "lugar": "museo", "texto": "Ve al museo."}])
        assert p.gps["auto"]
    else:
        p.gps_a_lugar(museo)
    assert p.gps["nombre"] == museo.nombre
    return p, museo


def _coherente(robot, nombre):
    """Lo que dice la G es adonde guían la baliza y el piloto: todo sale del mismo destino."""
    p = robot.p
    assert p.gps is not None and p.gps["nombre"] == nombre
    assert nombre.split(",")[0] in _tecla(robot, pygame.K_g)
    if p.gps["ruta"]:
        assert math.hypot(p.gps["ruta"][-1][0] - p.gps["dest"][0], p.gps["ruta"][-1][1] - p.gps["dest"][1]) < 1


@pytest.mark.parametrize("mision", [True, False])
def test_desvio_a_un_vehiculo_aparcado_se_acaba_al_subir(robot, mision):
    p, museo = _con_destino(robot, mision)
    x, y = p.pos()
    v = _coche(p, subir=False, x=x + 25, y=y)
    v.ia = "aparcado"
    t = _radar_a(robot, v, "vehiculos")
    assert "Desvío a" in t and f"Al subir a él, el GPS vuelve a {museo.nombre}" in t and "Mayúsculas G" in t
    _coherente(robot, p.gps["nombre"])
    assert p.gps["sigue"] is v and p.gps["anterior"]["nombre"] == museo.nombre
    # llegar a su lado no lo acaba (hay que forzarlo o abrirlo): sigue diciendo el vehículo
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 2, v.y + 2)
    robot.frames(40)
    assert p.gps["sigue"] is v
    # al subir, vuelve a lo de antes y lo dice; la G y la O dicen ya lo mismo
    p._subir(v, False, callar=True)
    robot.frames(40)
    assert f"Ya estás en {v.nombre}. El GPS vuelve a {museo.nombre}." in robot.dicho()
    _coherente(robot, museo.nombre)
    assert p.gps.get("anterior") is None and p.gps["sigue"] is None
    if mision:
        assert _tecla(robot, pygame.K_o).startswith(f"Destino: {museo.nombre}, ") and "desvío" not in robot.app.voz.registro[-1]


@pytest.mark.parametrize("mision", [True, False])
def test_desvio_a_un_objeto_a_una_persona_y_a_un_lugar(robot, mision):
    p, museo = _con_destino(robot, mision)
    # --- un objeto: se acaba al recogerlo
    o = _casete(p)
    assert f"Al llegar, el GPS vuelve a {museo.nombre}" in _radar_a(robot, o, "objetos")
    _coherente(robot, o.nombre)
    p.j.x, p.j.y = p.mundo.punto_libre(o.x + 4, o.y)             # a cuatro metros todavía no se ha llegado: sigue guiando hasta el objeto
    robot.frames(40)
    assert p.gps["nombre"] == o.nombre
    p.recoger(o)                                                 # se recoge (aquí, sin pasar por encima): el desvío se acaba
    robot.frames(40)
    assert f"{o.nombre}: recogido. El GPS vuelve a {museo.nombre}." in robot.dicho()
    _coherente(robot, museo.nombre)
    # --- una persona: se acaba al llegar a su lado
    x, y = p.pos()
    q = Persona("civil", *p.mundo.punto_libre(x + 20, y))
    q.nombre = "Un vecino"
    q.vel = 0.0
    p.personas.append(q)
    assert f"Al llegar a su lado, el GPS vuelve a {museo.nombre}" in _radar_a(robot, q, "personas")
    assert p.gps["sigue"] is q
    _coherente(robot, p.gps["nombre"])
    p.j.x, p.j.y = p.mundo.punto_libre(q.x + 1.5, q.y)
    robot.frames(40)
    assert f"Has llegado junto a {q.nombre}. El GPS vuelve a {museo.nombre}." in robot.dicho()
    _coherente(robot, museo.nombre)
    p.personas[:] = []
    # --- un lugar del radar: se acaba al llegar
    lugar = min((l for l in p.mundo.lugares.values() if l is not museo and 12 < math.hypot(l.x - p.j.x, l.y - p.j.y) < 110), key=lambda l: math.hypot(l.x - p.j.x, l.y - p.j.y))
    p.cfg["radar_filtro"] = "lugares"
    p.radar_lista = p._radar_construir()
    p.radar_idx = next(k for k, e in enumerate(p.radar_lista) if e[3] is lugar)
    assert f"Al llegar, el GPS vuelve a {museo.nombre}" in _tecla(robot, pygame.K_b)
    _coherente(robot, lugar.nombre)
    p.j.x, p.j.y = p.mundo.punto_libre(lugar.x, lugar.y)
    robot.frames(40)
    assert f"Has llegado a {lugar.nombre}. El GPS vuelve a {museo.nombre}." in robot.dicho()
    _coherente(robot, museo.nombre)
    # --- lo que se seguía desaparece: también se vuelve, y se dice
    v = _coche(p, subir=False, x=p.j.x + 30, y=p.j.y)
    _radar_a(robot, v, "vehiculos")
    assert p.gps["sigue"] is v
    p.quitar_vehiculo(v)
    robot.frames(40)
    assert f"{v.nombre} ya no está. El GPS vuelve a {museo.nombre}." in robot.dicho()
    _coherente(robot, museo.nombre)


def test_lo_que_marcas_tu_durante_una_mision_es_un_desvio_y_la_mision_espera_debajo(robot):
    p, museo = _con_destino(robot, True)
    hospital = next(l for l in p.mundo.lugares.values() if l.tipo == "hospital")
    n = len(robot.app.voz.registro)
    p.gps_a_lugar(hospital)                                      # desde la lista de lugares, el móvil o el mapa
    assert f"Desvío a {hospital.nombre}. Al llegar, el GPS vuelve a {museo.nombre}." in " | ".join(robot.app.voz.registro[n:])
    _coherente(robot, hospital.nombre)
    # otro sitio más: sustituye al desvío, y la misión sigue debajo
    banco = p.lugares["banco"]
    p.gps_a_lugar(banco)
    assert p.gps["nombre"] == banco.nombre and p.gps["anterior"]["nombre"] == museo.nombre and p.gps["anterior"].get("anterior") is None
    # la misión cambia de destino durante el desvío: cambia lo que espera debajo, y se dice
    ms = p.mision
    ms["def"]["pasos"].append({"tipo": "ir", "lugar": "periodico", "texto": "Ahora, al periódico."})
    p._paso_hecho()
    periodico = p.lugares["periodico"]
    assert p.gps["nombre"] == banco.nombre and p.gps["anterior"]["nombre"] == periodico.nombre
    assert f"Sigues en el desvío a {banco.nombre}. Cuando lo acabes, el GPS irá a {periodico.nombre}." in robot.dicho()
    p.j.x, p.j.y = p.mundo.punto_libre(banco.x, banco.y)
    robot.frames(40)
    assert f"Has llegado a {banco.nombre}. El GPS vuelve a {periodico.nombre}." in robot.dicho()
    _coherente(robot, periodico.nombre)
    # la misión se acaba durante un desvío: el desvío se queda, y debajo ya no hay nada
    p.gps_a_lugar(hospital)
    assert p.gps["anterior"]["nombre"] == periodico.nombre
    p.abandonar_mision()
    assert p.gps is not None and p.gps["nombre"] == hospital.nombre and p.gps.get("anterior") is None


def test_cancelar_el_desvio_y_el_destino_y_recuperarlos(robot):
    p, museo = _con_destino(robot, False)
    hospital = next(l for l in p.mundo.lugares.values() if l.tipo == "hospital")
    p.fijar_gps(hospital.x, hospital.y, hospital.nombre, desvio=True)
    assert p.gps["anterior"]["nombre"] == museo.nombre
    # Mayúsculas G: primero el desvío...
    t = _tecla(robot, pygame.K_g, S)
    assert f"Dejas el desvío a {hospital.nombre}. El GPS vuelve a {museo.nombre}." in t and "Con Control G lo recuperas." in t
    _coherente(robot, museo.nombre)
    # ...Control G lo recupera, otra vez como desvío
    t = _tecla(robot, pygame.K_g, C)
    assert f"Recuperado: el GPS vuelve a guiarte a {hospital.nombre}. Al acabar, vuelve a {museo.nombre}." in t
    _coherente(robot, hospital.nombre)
    assert p.gps["anterior"]["nombre"] == museo.nombre
    # dos veces Mayúsculas G: fuera el desvío y fuera el destino
    _tecla(robot, pygame.K_g, S)
    t = _tecla(robot, pygame.K_g, S)
    assert t.startswith(f"GPS cancelado: ya no te guía a {museo.nombre}. Con Control G lo recuperas.") and p.gps is None
    # sin destino: Mayúsculas G lo dice y recuerda cómo recuperarlo; la G sola también lo recupera
    assert f"No hay ningún destino marcado. Con Control G recuperas el último que quitaste: {museo.nombre}." in _tecla(robot, pygame.K_g, S)
    t = _tecla(robot, pygame.K_g)
    assert f"Recuperado: el GPS vuelve a guiarte a {museo.nombre}." in t
    _coherente(robot, museo.nombre)
    # ya no queda nada que recuperar
    assert "No has quitado ningún destino que se pueda recuperar." in _tecla(robot, pygame.K_g, C)
    # un vehículo que seguías y ya no está no se puede recuperar, y se dice
    v = _coche(p, subir=False, x=p.j.x + 30, y=p.j.y)
    p.cancelar_gps()
    p.fijar_gps(v.x, v.y, v.nombre, sigue=v, cosa=v)
    _tecla(robot, pygame.K_g, S)
    p.quitar_vehiculo(v)
    assert "ya no está: no se puede recuperar ese destino" in _tecla(robot, pygame.K_g, C) and p.gps is None


def test_en_una_mision_cancelar_y_recuperar(robot):
    p, museo = _con_destino(robot, True)
    ms = p.mision
    t = _tecla(robot, pygame.K_g, S)
    assert "GPS cancelado" in t and "Con la G vuelves a marcar la misión." in t and p.gps is None and ms["gps_callado"]
    robot.frames(120)
    assert p.gps is None                                          # lo has quitado tú: no vuelve solo
    _tecla(robot, pygame.K_g, C)                                 # Control G vuelve al objetivo
    assert p.gps is not None and p.gps["nombre"] == museo.nombre and p.gps["auto"]
    _tecla(robot, pygame.K_g, S)
    _tecla(robot, pygame.K_g)                                    # y la G de siempre, también
    assert p.gps is not None and p.gps["nombre"] == museo.nombre


def test_mayusculas_l_al_vehiculo_es_un_desvio_y_se_acaba_al_subir(robot):
    p, museo = _con_destino(robot, True)
    v = _coche(p)
    p.salir_vehiculo(forzado=True)
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 60, v.y + 3)
    t = _tecla(robot, pygame.K_l, S)
    assert "Marcado en el GPS" in t and f"Al llegar, el GPS vuelve a {museo.nombre}" in t
    assert p.gps["nombre"] == v.nombre and p.gps["anterior"]["nombre"] == museo.nombre
    p.j.x, p.j.y = v.x, v.y + 12
    p._subir(v, False, callar=True)
    robot.frames(40)
    assert f"El GPS vuelve a {museo.nombre}." in robot.dicho() and p.gps["nombre"] == museo.nombre


# ====================================================================== F. persecuciones
def test_al_empezar_una_persecucion_se_explica_que_hace_falta_y_como_seguirle(robot):
    p, ms, vo = _persecucion(robot)
    d = robot.dicho()
    assert "Es una persecución en vehículo: a pie no le alcanzas, y con un vehículo lento, tampoco." in d
    assert "La O te dice dónde está y hacia dónde va" in d and "Llevas puesta la ayuda en las persecuciones" in d
    assert "Vas a pie" not in d
    # a pie, lo dice; y sin la ayuda, dice dónde está la opción
    p.abandonar_mision()
    p.salir_vehiculo(forzado=True)
    p.cfg["ayuda_persecucion"] = False
    _propia(robot, copy.deepcopy(PERSECUCION), lugar="banco")
    d = " | ".join(robot.app.voz.registro[-6:])
    assert "Vas a pie: sube cuanto antes a un vehículo rápido" in d and "en Opciones, Combate y dificultad, está la ayuda en las persecuciones" in d


def test_la_ayuda_en_las_persecuciones_viene_puesta_y_cambia_los_numeros(robot, datos_de_serie):
    from juego import config
    assert config.POR_DEFECTO["ayuda_persecucion"] is True if hasattr(config, "POR_DEFECTO") else robot.app.cfg["ayuda_persecucion"] is True
    p, ms, vo = _persecucion(robot, dificultad="normal")
    base = ms["vel_huida"]
    x, y = p.pos()
    casos = {True: ((200, 0.45), (80, 0.70), (40, 1.0)), False: ((200, 0.55), (120, 0.80), (80, 1.0))}
    for ayuda, lista in casos.items():
        p.cfg["ayuda_persecucion"] = ayuda
        for lejos, factor in lista:
            vo.x, vo.y = x + lejos, y
            ms["t_canta"] = 99
            p.actualizar_mision(0.03)
            assert vo.vel_obj == pytest.approx(base * factor), (ayuda, lejos)
    # los avisos: cada 7 segundos desde 25 metros con la ayuda; cada 12 desde 45 sin ella. Y dicen la calle y hacia dónde va
    for ayuda, cada, desde in ((True, 7, 25), (False, 12, 45)):
        p.cfg["ayuda_persecucion"] = ayuda
        vo.x, vo.y = x + desde + 5, y
        vo.vel = 8.0
        ms["t_canta"] = 0.0
        n = len(robot.app.voz.registro)
        p.actualizar_mision(0.03)
        dicho = " | ".join(robot.app.voz.registro[n:])
        assert f"{vo.nombre}: a {desde + 5} metros, " in dicho and ", por " in dicho and ", va hacia el " in dicho, (ayuda, dicho)
        assert ms["t_canta"] == pytest.approx(cada)
        vo.x = x + desde - 5
        ms["t_canta"] = 0.0
        n = len(robot.app.voz.registro)
        p.actualizar_mision(0.03)
        assert f"{vo.nombre}: a " not in " | ".join(robot.app.voz.registro[n:])
    # con la ayuda, cada giro se canta; sin ella, no
    for ayuda in (True, False):
        p.cfg["ayuda_persecucion"] = ayuda
        vo.x, vo.y, vo.vel = x + 60, y, 8.0
        vo.rumbo = 0.0
        ms["rumbo_obj"], ms["t_giro"], ms["t_canta"] = None, 0.0, 99
        p.actualizar_mision(0.03)
        vo.rumbo = 90.0
        n = len(robot.app.voz.registro)
        p.actualizar_mision(0.03)
        assert ("Gira hacia el este" in " | ".join(robot.app.voz.registro[n:])) == ayuda
    # los números salen de los datos: un mod los cambia
    datos = M.cargar_datos()
    datos["persecuciones"] = [{"id": "general", "ayuda_canta_cada": 4, "factor_lejos": 30}]
    from juego import ajustes
    ajustes.configurar_todos(datos)
    p.cfg["ayuda_persecucion"] = True
    assert p.pers("canta_cada") == 4
    p.cfg["ayuda_persecucion"] = False
    assert p.pers("canta_cada") == 12 and p.pers("factor_lejos") == 30


def test_con_la_ayuda_hay_algo_mas_de_tiempo_y_a_pie_se_aguanta_mas(robot):
    p, ms, vo = _persecucion(robot, limite=200)
    assert ms["limite"] == pytest.approx(200 * 1.15, abs=1.0)
    p.abandonar_mision()
    p.salir_vehiculo(forzado=True)
    p.cfg["ayuda_persecucion"] = False
    ms = _propia(robot, copy.deepcopy(PERSECUCION[:1]) and [dict(PERSECUCION[0], limite=200)], lugar="banco")
    assert ms["limite"] == pytest.approx(200, abs=1.0)
    p.abandonar_mision()
    # seguir a pie
    for ayuda, aguante, tope, aviso in ((True, 14.0, 65, 3.5), (False, 9.0, 55, 5)):
        p.cfg["ayuda_persecucion"] = ayuda
        ms = _mision(robot, "eo1")
        o = ms["movil"]
        assert o["aguante"] == pytest.approx(aguante) and p.pers("seguir_lejos") == tope and p.pers("seguir_aviso") == aviso
        p.abandonar_mision()
    # con la ayuda, se dice cuando dobla una esquina
    p.cfg["ayuda_persecucion"] = True
    ms = _mision(robot, "eo1")
    o = ms["movil"]
    p.j.x, p.j.y = p.mundo.punto_libre(o["x"] + 20, o["y"])
    robot.frames(10)
    o["espera"] = 0.0
    assert len(o["ruta"]) >= 2
    giros = 0
    for _ in range(4000):
        p.j.x, p.j.y = p.mundo.punto_libre(o["x"] + 15, o["y"] + 15)      # siempre a una distancia cómoda
        robot.frames(1)
        if p.mision is None or p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] != "seguir":
            break
    assert "El prestamista tuerce hacia el " in " | ".join(robot.app.voz.registro)


def test_la_opcion_esta_en_opciones_y_los_datos_en_el_editor(robot, datos_de_serie):
    p = _partida(robot)
    robot.tecla(pygame.K_ESCAPE)
    _elegir(robot, "Opciones")
    _elegir(robot, "Combate y dificultad")
    m = robot.app.pila[-1]
    o = next(x for x in m.opciones if x.texto.startswith("Ayuda en las persecuciones"))
    assert o.texto == "Ayuda en las persecuciones: sí" and "suave" in o.ayuda
    m.i = m.opciones.index(o)
    robot.tecla(pygame.K_RIGHT)
    assert p.cfg["ayuda_persecucion"] is False and o.texto.endswith(": no")
    from editor import esquema
    campos = {c["k"] for c in esquema.ESQUEMAS["ajuste_persecuciones"]["campos"]}
    datos = M.cargar_datos()
    assert set(datos["persecuciones"][0]) <= campos and set(D.AJ._n) | set(D.AJ._l) <= campos
    assert {k: v for k, v in datos["persecuciones"][0].items() if k in D.AJ._n} == {k: v for k, v in D.AJ._n.items()}


def test_las_dieciseis_persecuciones_de_la_historia_arrancan_con_la_explicacion(robot):
    p = _partida(robot)
    n = 0
    for m in p.datos["misiones"]:
        pasos = [q for q in m["pasos"] if q["tipo"] == "perseguir"]
        if not pasos:
            continue
        l = p.lugares.get(pasos[0].get("lugar", ""))
        if l is None or l.mapa != p.mundo.id:
            continue
        p.iniciar_mision({"id": "pr_" + m["id"], "titulo": m["titulo"], "lugar": m["lugar"], "requiere": [], "repetible": True, "pasos": [dict(pasos[0])]})
        _dialogos(robot)
        robot.frames(3)
        ms = p.mision
        assert ms and ms.get("veh_objetivo") is not None, m["id"]
        assert "Es una persecución en vehículo" in " | ".join(robot.app.voz.registro[-8:]), m["id"]
        p._o_ultima = None
        assert _tecla(robot, pygame.K_o).startswith(f"{ms['veh_objetivo'].nombre}: a "), m["id"]
        p.abandonar_mision()
        n += 1
    assert n >= 3


# ====================================================================== H. el actualizador
def test_el_resumen_de_novedades_se_corta_en_un_punto_completo():
    from herramientas import publicar
    lineas = [f"Punto número {k}: " + "palabra " * 30 + "fin." for k in range(60)]
    t = publicar.recortar_novedades(lineas, 3000)
    partes = t.split("\n")
    assert len(t) <= 3000 and partes[-1].startswith("Hay más: la lista completa está en el menú principal del juego, en Acerca de")
    assert all(x in lineas for x in partes[:-1]) and partes[:-1] == lineas[:len(partes) - 1] and len(partes) > 5
    assert publicar.recortar_novedades(lineas[:3], 3000) == "\n".join(lineas[:3])          # si cabe entero, tal cual
    real = publicar.novedades()
    assert real and len(real) <= publicar.NOVEDADES_MAX and "<" not in real
    assert real.split("\n")[-1].endswith(".")


def test_tras_actualizar_se_dice_donde_estan_las_novedades(robot, monkeypatch):
    import sys
    from juego import actualizador as A, menus_actualizar
    monkeypatch.setattr(sys, "argv", sys.argv + [A.ARG_TRAS_ACTUALIZAR])
    monkeypatch.setattr(A, "limpiar", lambda *a, **k: None)
    monkeypatch.setattr(A, "limpiar_registro_instalador", lambda *a, **k: None)
    monkeypatch.setattr(A, "leer_registro_instalador", lambda *a, **k: {})
    monkeypatch.setattr(menus_actualizar.registro, "_sanear", lambda *a, **k: None)
    n = len(robot.app.voz.registro)
    menus_actualizar.al_arrancar(robot.app)
    dicho = " | ".join(robot.app.voz.registro[n:])
    assert "Las novedades están en el menú principal, en Acerca de, Novedades de esta versión." in dicho and "en el manual" not in dicho
    # y ese camino existe de verdad
    m = robot.app.pila[0]
    assert any(o.texto == "Acerca de" for o in m.opciones)
    _elegir(robot, "Acerca de")
    assert any(o.texto == "Novedades de esta versión" for o in robot.app.pila[-1].opciones)
