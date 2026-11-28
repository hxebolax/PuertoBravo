"""Trabajo 1.7.2: lo que llegó por GitHub y por el hilo del foro tras la 1.7.1.

A. Fallos de las issues: el GPS al recoger lo que buscabas, el hilo de voces sin pila, el vehículo traído del garaje en un
servidor y la F con varios vehículos pegados. B. Las bandas con la buena gente y la defensa propia. C. El piloto del GPS y
los semáforos. D. Escribir con tildes. E. El historial. F. Los títulos dicen dónde sirven. G. La policía en una
persecución. H. Alquilar casas. I. La pareja: elegir casa, mudarse y darle dinero. J. Tratar con tu gente.
"""
import math
import random

import pygame
import pytest

from juego import mundo as M
from juego.entidades import Objeto, Persona
from juego.menus import EntradaTexto, Menu


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


def _dicho(robot, n):
    return " | ".join(robot.app.voz.registro[n:])


# ============================================================================ A. las issues
def test_repetir_el_gps_tras_recoger_lo_que_buscabas_no_cierra_el_juego(robot):
    p = _partida(robot)
    x, y = p.pos()
    o = Objeto("dinero", "Dinero en el suelo", *p.mundo.punto_libre(x + 6, y))
    o.valor = 70
    p.objetos.append(o)
    p.cancelar_gps()
    p.fijar_gps(o.x, o.y, o.nombre, desvio=True, cosa=o)
    assert p.gps is not None
    p.objetos.remove(o)                                      # recogido
    o.recogido = True
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_g)                                  # antes: TypeError, 'NoneType' object is not subscriptable
    assert p.gps is None and "recogido" in _dicho(robot, n)


def test_repetir_el_gps_tras_subir_al_vehiculo_que_te_han_traido_no_cierra_el_juego(robot):
    """Issue 7: Mayúsculas L al último vehículo, pedir que te lo traigan, subir con la F y pulsar G."""
    p = _partida(robot)
    j = p.j
    x, y = p.pos()
    v = p.crear_vehiculo("utilitario", *p.mundo.punto_libre(x + 200, y), 0, "aparcado")
    p.hacer_mio(v, callar=True)
    p.ultimo_veh = v
    p.cancelar_gps()
    robot.tecla(pygame.K_l, pygame.KMOD_LSHIFT)                # el GPS al último vehículo
    assert p.gps is not None and (p.gps.get("cosa") is v or p.gps.get("sigue") is v)
    assert p.traer_mi_vehiculo(v) is v                        # «Pedir que te lo traigan», en Mis vehículos
    j.x, j.y = v.x, v.y
    robot.tecla(pygame.K_f)
    assert j.veh is v
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_g)                                  # en la 1.7.1: TypeError, 'NoneType' object is not subscriptable
    assert p.gps is None and "Ya estás en" in _dicho(robot, n)


def test_las_voces_se_generan_en_un_hilo_con_pila_holgada_y_se_guardan_a_trozos(tmp_path):
    import threading
    import numpy as np
    import soundfile as sf
    from juego import vozgen
    vista = {}

    def mirar():
        vista["pila"] = threading.stack_size()
    h = vozgen.hilo_con_pila(mirar, "prueba")
    h.join(5)
    assert threading.stack_size() == 0                       # se deja como estaba para los demás hilos
    pcm = (np.sin(np.linspace(0, 2000, 24000 * 3)) * 0.3).astype(np.float32)
    ruta = str(tmp_path / "frase.ogg")
    vozgen.escribir_ogg(ruta, pcm, 24000)
    leido, sr = sf.read(ruta)
    assert sr == 24000 and abs(len(leido) - len(pcm)) < 2000


def _coche(p, modelo="utilitario", x=None, y=None):
    px, py, d = p.mundo.plaza_en(*(p.pos() if x is None else (x, y)))
    return p.crear_vehiculo(modelo, px, py, d, None)


def test_el_vehiculo_traido_del_garaje_es_tuyo_y_la_f_lo_prefiere(robot):
    p = _partida(robot)
    j = p.j
    j.garajes["casa_abuela"] = [{"modelo": "todoterreno" if "todoterreno" in p.modelos else "utilitario", "salud": 100.0, "nombre": "Mi cuatro por cuatro", "mejoras": {}}]
    x, y, _ = p.plaza_cercana()
    estorbo = p.crear_vehiculo("camion" if "camion" in p.modelos else "utilitario", x, y, 0, "aparcado")
    v = p.traer_mi_vehiculo(j.garajes["casa_abuela"][0], "casa_abuela")
    assert v is not None and v.nombre == "Mi cuatro por cuatro"
    assert estorbo.muerto, "el que estorbaba en la plaza se quita"
    assert p.tu_vehiculo() is v and p.es_mio(v)
    # con otro vehículo pegado, la F elige el tuyo
    otro = p.crear_vehiculo("utilitario", v.x + 0.5, v.y, 0, "aparcado")
    otro.cerrado = True
    j.x, j.y = otro.x, otro.y
    robot.tecla(pygame.K_f)
    assert j.veh is v


class _Red:
    def __init__(self):
        self.enviado = []
        self.conectado = True

    def enviar(self, m):
        self.enviado.append(m)


def test_en_un_servidor_el_vehiculo_traido_queda_apuntado_como_tuyo(robot):
    p = _partida(robot)
    j = p.j
    j.garajes["casa_abuela"] = [{"modelo": "utilitario", "salud": 100.0, "nombre": "El de casa", "mejoras": {}}]
    p.en_servidor, red = True, _Red()
    for k, vacio in (("info", {}), ("vehs", {}), ("mios", set()), ("veh_pend", {}), ("trafico", {})):
        p.sv.setdefault(k, vacio)
    antes = p.red
    p.red = red
    try:
        v = p.traer_mi_vehiculo(j.garajes["casa_abuela"][0], "casa_abuela")
        assert v is not None and p.tu_vehiculo() is v and not j.garajes["casa_abuela"]
        alta = [m for m in red.enviado if m.get("t") == "veh_tomar"]
        assert alta and alta[-1]["ref"] == v.id
        p._svm_veh_tuyo({"id": 77, "ref": v.id})              # el servidor contesta: es tuyo, y como no vas dentro, aparcado
        assert v.id_red == 77 and v.red_dueno and 77 in p.sv["mios"]
        assert any(m.get("t") == "veh_dejar" and m.get("id") == 77 for m in red.enviado)
        for _ in range(3):
            p._poblar()
        assert v in p.vehiculos and not v.muerto             # no desaparece al alejarte
    finally:
        p.en_servidor = False
        p.red = antes


# ============================================================================ B. bandas y buena gente
def _pandillero(p, d=10):
    x, y = p.pos()
    e = Persona("banda", *p.mundo.punto_libre(x + d, y), nombre="Calavera")
    e.banda, e.hostil, e.activo, e.arma = "Los Calaveras", True, True, "navaja"
    p.personas.append(e)
    return e


def test_la_buena_gente_a_veces_pasa_y_defenderse_no_cuesta_con_la_banda(robot):
    from juego import honrado
    p = _partida(robot)
    j = p.j
    j.ciudadania = 60
    honrado.AJ.n["banda_deja_prob"] = 100
    try:
        e = _pandillero(p)
        robot.frames(3)
        assert getattr(e, "deja_pasar", False) and not e.hostil and robot.app.voz.registro[-1].startswith("Calavera")
    finally:
        honrado.AJ.n["banda_deja_prob"] = 65
    # uno que sí ataca: tumbarlo es defensa propia, y su banda no lo tiene en cuenta
    e2 = _pandillero(p, 3)
    e2.deja_pasar = False
    p.marcar_agresor(e2)
    rep = p.rep_banda("Los Calaveras")
    p.danar_persona(e2, 500)
    assert e2.muerto and p.rep_banda("Los Calaveras") == rep and j.puntos_busqueda == 0


def test_sin_prestigio_la_defensa_propia_resta_poco(robot):
    p = _partida(robot)
    p.j.ciudadania = 5
    e = _pandillero(p, 3)
    p.marcar_agresor(e)
    rep = p.rep_banda("Los Calaveras")
    p.danar_persona(e, 500)
    assert p.rep_banda("Los Calaveras") == rep - 1
    e2 = _pandillero(p, 3)                                   # el que no te ha hecho nada: los cuatro de siempre
    rep = p.rep_banda("Los Calaveras")
    p.danar_persona(e2, 500)
    assert p.rep_banda("Los Calaveras") == rep - 4


# ============================================================================ C. el piloto y los semáforos
def test_el_piloto_frena_a_tiempo_en_rojo_y_no_se_lo_salta_en_un_trabajo(robot):
    p = _partida(robot, conduccion="asistida", piloto_gps=True)
    m = p.mundo
    # un autobús a 24 metros de un cruce, a la velocidad del piloto: antes solo miraba el semáforo entre 17 y 7,5 metros,
    # y con lo que frena un autobús acababa dentro del cruce
    i, jj = 3, 5
    x = m.carril("V", i, 0)
    y = jj * M.B - 24
    v = p.crear_vehiculo("autobus", x, y, 0, None)
    p._subir(v, False, callar=True)
    v.vel = 14.0
    freno = v.modelo["freno"]
    while m.verde_vertical(m._idx(v.x, m.NX), jj, p.t):        # rojo para quien va por esta calle
        p.t += 1.0
    linea = p._piloto_semaforo(v, freno)
    assert linea is not None and linea > 14, linea
    # en un trabajo contra el reloj espera en rojo
    p.trabajo = {"limite": 100.0}
    p.sirena_propia = None
    p.fijar_gps(x, y + 400, "Parada", auto=True, callar=True)
    for _ in range(300):
        p._pilotar(v, 1 / 30, freno)
        v.y += v.vel / 30
        if v.vel <= 0.01:
            break
    assert v.vel <= 0.01 and jj * M.B - v.y > 7.5, (v.vel, jj * M.B - v.y)
    p.trabajo = {}


def test_al_subir_con_el_piloto_puesto_se_dice_por_que_no_conduce(robot):
    p = _partida(robot, conduccion="libre", piloto_gps=True)
    v = _coche(p)
    n = len(robot.app.voz.registro)
    p._subir(v, False)
    assert "conducción asistida" in _dicho(robot, n)


# ============================================================================ D. escribir con tildes
def test_el_cuadro_de_texto_recibe_lo_que_llega_como_texto(robot):
    app = robot.app
    hecho = []
    e = EntradaTexto(app, "Nombre", hecho.append)
    app.abrir(e)
    robot.tecla(pygame.K_a, 0, "a")
    app.evento_texto("a")                                    # el eco de la misma tecla: no se escribe dos veces
    app.evento_texto("é")                                    # una tilde con tecla muerta: solo llega como texto
    assert e.texto == "aé"
    robot.tecla(pygame.K_RETURN)
    assert hecho == ["aé"]


# ============================================================================ E. el historial
def test_control_re_pag_y_av_pag_y_la_opcion_de_seguir_al_final(robot):
    p = _partida(robot)
    voz = robot.app.voz
    for k in range(5):
        p.decir(f"mensaje {k}")
    robot.tecla(pygame.K_PAGEUP, pygame.KMOD_CTRL)
    assert voz.cursor == 0 and voz.registro[-1].startswith("Primero.")
    robot.tecla(pygame.K_PAGEDOWN, pygame.KMOD_CTRL)
    assert voz.cursor == len(voz.historial) - 1 and voz.registro[-1].startswith("Último.")
    p.cfg["historial_al_final"] = False
    robot.tecla(pygame.K_PAGEUP)
    robot.tecla(pygame.K_PAGEUP)
    donde = voz.cursor
    p.decir("otro mensaje")
    assert voz.cursor == donde                               # te quedas donde estabas
    p.cfg["historial_al_final"] = True
    voz.repaso_t = -1e9                                      # hace rato que no repasas
    p.decir("y otro")
    assert voz.cursor == len(voz.historial) - 1


# ============================================================================ F. títulos
def test_un_titulo_dice_en_que_contrato_sirve(robot):
    p = _partida(robot)
    t = next(x for x in p.datos["titulos"] if x["id"] == "hosteleria")
    texto = p.hon_titulo_donde(t)
    assert "Oficina de empleo" in texto and "Grupo Hostelero La Bahía" in texto
    assert "Abre el puesto" not in t["abre"]


# ============================================================================ G. la policía
def test_en_una_persecucion_la_fuerza_vale_mas_lejos(robot):
    from juego import agente
    p = _partida(robot)
    x, y = p.pos()
    v = p.crear_vehiculo("utilitario", x + 200, y, 0, "huida")
    p.trabajo = {"aviso": {"veh": v, "fase": "seguir", "tipo": "persecucion", "sospechosos": []}}
    try:
        assert p._sospechoso_cerca()
        p.trabajo["aviso"]["tipo"] = "temerario"                 # si todavía no ha huido, la distancia de siempre
        assert not p._sospechoso_cerca()
    finally:
        p.trabajo = {}
    assert agente.AJ("radio_fuerza_vehiculo") == 300


# ============================================================================ H. alquilar casas
def test_alquilar_una_casa_cobrar_y_recuperarla(robot):
    p = _partida(robot, dinero=100000)
    j = p.j
    casa = p.lug("piso_centro")
    j.propiedades.append(casa.id)
    assert "otra" not in p.alquiler_motivo(casa)
    j.garajes[casa.id] = [{"modelo": "utilitario", "salud": 100.0}]
    assert "garaje" in p.alquiler_motivo(casa)
    j.garajes[casa.id] = []
    texto = p.alquilar_casa(casa)
    assert p.alquilada(casa.id) and "euros" in texto
    assert "Ya está alquilada" in p.alquiler_motivo(casa)
    assert p.alquiler_motivo(p.lug("casa_abuela")).startswith("Es la única casa")
    antes = j.dinero
    random.seed(3)
    for _ in range(10):
        p.dia_alquiler()
    assert j.dinero > antes and j.alquiladas[casa.id]["cobrado"] > 0
    # alquilada: su garaje no se usa
    assert casa not in [l for l in (p.lug(i) for i in j.propiedades) if l is not None and not p.alquilada(l.id) and l.id == casa.id]
    antes = j.dinero
    t = p.recuperar_casa(casa)
    assert not p.alquilada(casa.id) and j.dinero == antes - j.alquiladas.get(casa.id, {"renta": 0})["renta"] * 0 - p.renta_de(casa) * 2 and "fianza" in t
    p.en_servidor = True
    try:
        assert "servidor" in p.alquiler_motivo(casa)
    finally:
        p.en_servidor = False


def test_el_menu_de_una_casa_alquilada(robot):
    from juego import menus_juego
    p = _partida(robot, dinero=100000)
    casa = p.lug("piso_centro")
    p.j.propiedades.append(casa.id)
    p.alquilar_casa(casa)
    menus_juego._casa(p, casa)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu)
    textos = " | ".join(o.texto for o in m.opciones)
    assert "Alquilada a" in textos and "Recuperar la casa" in textos and "Descansar" not in textos


# ============================================================================ I. la pareja
def _pareja(p):
    p.cfg["pareja_familiar"] = True
    pers = p.dato_adulto("personas")[0]
    j = p.j
    j.pareja = pers["id"]
    r = p.relacion(pers["id"])
    r["afinidad"], r["citas"], r["estado"] = 95, 10, "pareja"
    r["compromiso"] = "casados"
    return pers


def test_la_pareja_se_muda_a_otra_casa_y_le_das_dinero(robot):
    p = _partida(robot, dinero=5000)
    j = p.j
    pers = _pareja(p)
    j.propiedades.append("piso_centro")
    j.convive, j.convive_casa, j.convive_desde = pers["id"], "casa_abuela", p.dia
    texto = p.mudar_convivencia(p.lug("piso_centro"))
    assert j.convive_casa == "piso_centro" and "Estudio en la Gran Vía" in texto
    p.relacion(pers["id"])["afinidad"] = antes = 50
    t = p.dar_dinero_pareja(pers, 250)
    assert j.dinero == 4750 and p.relacion(pers["id"])["afinidad"] > antes and pers["nombre"] in t
    assert "Hoy ya" in p.dar_dinero_pareja(pers, 50)
    p.dia += 1
    assert pers["nombre"] in p.compra_de_pareja()
    # una casa alquilada no vale para vivir
    j.propiedades.append("piso_playa")
    j.alquiladas["piso_playa"] = {"renta": 50, "inquilino": "alguien", "desde": 1}
    assert all(c.id != "piso_playa" for c in p.casas_para_vivir())


def test_lo_que_se_compro_se_cuenta_al_dia_siguiente(robot):
    p = _partida(robot, dinero=5000)
    pers = _pareja(p)
    p.dar_dinero_pareja(pers, 100)
    assert p.compra_de_pareja() == ""                        # el mismo día, todavía no
    p.dia += 1
    t = p.compra_de_pareja()
    assert pers["nombre"] in t and p.compra_de_pareja() == ""


# ============================================================================ J. tu gente
def test_tratar_con_tu_gente_por_su_nombre(robot):
    from juego import golpes
    p = _partida(robot, dinero=5000)
    p.j.banda = 2
    f = p.banda_fichas()[0]
    f["lealtad"] = 50
    golpes.menu_miembro(p, f)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Darle una paga"))
    robot.tecla(pygame.K_RETURN)
    assert f["lealtad"] == 58 and p.j.dinero == 5000 - golpes.AJ.entero("paga_precio")
    robot.tecla(pygame.K_RETURN)                             # una vez al día
    assert f["lealtad"] == 58 and "Hoy ya" in robot.app.voz.registro[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Echar"))
    robot.tecla(pygame.K_RETURN)
    c = robot.app.pila[-1]
    c.i = 1
    robot.tecla(pygame.K_RETURN)
    assert p.j.banda == 1 and all(x["id"] != f["id"] for x in p.banda_fichas())


def test_los_datos_traen_lo_nuevo_y_el_editor_lo_cubre():
    from juego import alquiler, convivencia, golpes, honrado, agente
    d = M.cargar_datos(con_mods=False)
    for sec, aj in (("alquiler", alquiler.AJ), ("convivencia", convivencia.AJ), ("golpes", golpes.AJ), ("vida_honrada", honrado.AJ), ("policia_oficio", agente.AJ)):
        claves = set(d[sec][0])
        for k in list(aj._n) + list(aj._l):
            if k in ("vehiculos",):
                continue
            assert k in claves, (sec, k)


def test_el_aviso_de_negocio_abandonado_dice_que_con_alguien_contratado_aguanta(robot):
    """Hilo del foro: tener negocios en varias localidades. El aviso dice cómo evitar que se hunda; con gente, no se dice."""
    from test_171_honrado import BAR, _dias, _empezar, _marca, _desde, _negocio
    from juego import honrado as H
    p = _empezar(robot, nivel="normal", impuestos_facturas=False)
    p.j.reputacion = 50
    l = _negocio(p)
    e = p.j.empresa[BAR]
    p.hon()["gracia"] = 0
    n = _marca(robot)
    _dias(robot, H.AJ.entero("abandono_dias") + 1)
    assert "Con alguien contratado, aguantaría sin ti." in _desde(robot, n)
    e.update(rep=50.0, emp=1, visto=p.dia)
    n = _marca(robot)
    _dias(robot, H.AJ.entero("abandono_dias") + 1)
    assert l.nombre in _desde(robot, n) and "aguantaría sin ti" not in _desde(robot, n)
    assert e["rep"] >= 44.0


# ============================================================================ K. el seguro de tus vehículos
def _mi_coche(p, modelo="deportivo", dx=8.0):
    from juego import sistemas
    x, y = p.pos()
    v = p.crear_vehiculo(modelo, *p.mundo.punto_libre(x + dx, y), 0, "aparcado")
    p.hacer_mio(v, callar=True)
    sistemas.poner(v, {next(iter(sistemas.MEJORAS)): 2})
    return v


def test_sin_seguro_un_vehiculo_tuyo_que_explota_se_pierde_y_se_dice_que_hay_seguro(robot):
    p = _partida(robot)
    v = _mi_coche(p)
    n = len(robot.app.voz.registro)
    p.explotar(v)
    dicho = _dicho(robot, n)
    assert v.muerto and "se ha perdido con todas sus mejoras" in dicho and "Mis vehículos" in dicho
    assert not p.j.seguro_pend


def test_el_seguro_cubre_desde_manana_cobra_por_vehiculo_en_la_calle_y_devuelve_el_coche(robot):
    from juego import misvehiculos as MV
    p = _partida(robot, dinero=1000)
    j = p.j
    j.banco = 0
    v = _mi_coche(p)
    _mi_coche(p, "utilitario", dx=-8.0)
    mejoras = dict(v.mejoras)
    assert p.seguro_contratar(True) and j.seguro_desde == p.dia + 1
    assert not p.seguro_cubre()                                   # el mismo día no cubre: no vale contratarlo con el coche ardiendo
    p.dia += 1
    assert p.seguro_cubre()
    p.dia_seguro()
    assert j.dinero == 1000 - 2 * MV.AJUSTES["seguro_cuota"]      # dos vehículos en la calle
    # explota: la grúa se lo lleva y al día siguiente vuelve, reparado y con sus mejoras, al garaje
    for l in (p.lug(i) for i in j.propiedades):
        if l is not None:
            j.garajes[l.id] = []
    n = len(robot.app.voz.registro)
    p.explotar(v)
    assert "grúa de tu seguro" in _dicho(robot, n) and len(j.seguro_pend) == 1
    franquicia = p.seguro_franquicia("deportivo")
    assert franquicia == max(MV.AJUSTES["seguro_franquicia_min"], 24000 * MV.AJUSTES["seguro_franquicia_pct"] // 100)
    p.dia_seguro()
    assert len(j.seguro_pend) == 1                                # hoy todavía no
    p.dia += 1
    j.dinero = 5000
    p.dia_seguro()
    assert not j.seguro_pend
    ficha = next(f for g in j.garajes.values() for f in g)
    assert ficha["modelo"] == "deportivo" and ficha["mejoras"] == mejoras
    assert j.dinero == 5000 - MV.AJUSTES["seguro_cuota"] - franquicia      # ya solo queda uno en la calle
    assert j.stats["seguro_pagado"] == 4 * MV.AJUSTES["seguro_cuota"] + franquicia


def test_el_seguro_sin_garaje_lo_deja_en_un_taller_y_espera_la_franquicia(robot):
    p = _partida(robot, dinero=0)
    j = p.j
    j.banco = 0
    j.propiedades[:] = []
    v = _mi_coche(p, "utilitario")
    _mi_coche(p, "sedan", dx=-8.0)                                # otro en la calle: hay cuota que pagar
    j.seguro_desde = p.dia
    p.explotar(v)
    p.dia += 1
    n = len(robot.app.voz.registro)
    p.dia_seguro()                                                # sin dinero para la cuota: baja, pero lo reparado se guarda
    assert j.seguro_desde == 0 and "te dan de baja" in _dicho(robot, n)
    assert len(j.seguro_pend) == 1 and "franquicia" in _dicho(robot, n)
    j.dinero = 1000
    p.dia_seguro()
    assert not j.seguro_pend
    nuevo = [x for x in p.mis_vivos() if x.modelo["id"] == "utilitario"]
    assert len(nuevo) == 1 and nuevo[0].salud == nuevo[0].salud_max and j.dinero == 1000 - p.seguro_franquicia("utilitario")


def test_el_seguro_en_el_menu_en_los_datos_y_en_el_editor(robot):
    from juego import misvehiculos as MV
    from editor import esquema
    p = _partida(robot)
    _mi_coche(p)
    MV.menu_mis_vehiculos(p)
    m = robot.app.pila[-1]
    op = next(o for o in m.opciones if o.texto.startswith("Seguro de tus vehículos: sin contratar"))
    op.accion()
    assert p.j.seguro_desde == p.dia + 1 and any("cubre desde mañana" in o.texto for o in m.opciones)
    d = M.cargar_datos(con_mods=False)["vehiculos_propios"][0]
    campos = {c["k"] for c in esquema.ESQUEMAS["ajuste_vehiculos"]["campos"]}
    for k in ("seguro_cuota", "seguro_franquicia_pct", "seguro_franquicia_min"):
        assert k in d and k in campos and k in MV.AJUSTES
    MV.configurar({"vehiculos_propios": [{"id": "general", "seguro_cuota": 0}]})
    try:
        assert MV.AJUSTES["seguro_cuota"] == 0
    finally:
        MV.configurar(M.cargar_datos(con_mods=False))
    p.en_servidor = True
    try:
        assert not p.seguro_contratar(True) and not p.seguro_siniestro(_mi_coche(p))
    finally:
        p.en_servidor = False


# ============================================================================ L. los coches aparcados y el desguace
def test_cada_plaza_saca_cada_dia_otro_modelo_y_los_caros_salen_menos(robot):
    from juego import desguace as D
    p = _partida(robot)
    m = p.mundo
    ids = ["lujo", "deportivo", "todoterreno", "sedan", "limusina", "descapotable", "caravana"]
    ids = [i for i in ids if i in p.modelos]
    plazas = m.aparcados[:300]
    hoy = [D.modelo_de_plaza(p, pl, ids, m.id) for pl in plazas]
    assert hoy == [D.modelo_de_plaza(p, pl, ids, m.id) for pl in plazas]      # el mismo todo el día
    p.dia += 1
    manana = [D.modelo_de_plaza(p, pl, ids, m.id) for pl in plazas]
    assert sum(a != b for a, b in zip(hoy, manana)) > len(plazas) // 2         # al día siguiente, otra calle
    vacias = sum(1 for x in hoy if x is None)
    assert 0 < vacias < len(plazas) // 3
    caros = sum(1 for x in hoy if x and p.modelos[x]["valor"] >= D.AJ("caro_valor"))
    normales = sum(1 for x in hoy if x and p.modelos[x]["valor"] < D.AJ("caro_valor"))
    n_caros = sum(1 for i in ids if p.modelos[i]["valor"] >= D.AJ("caro_valor"))
    assert caros / n_caros < normales / (len(ids) - n_caros) / 2               # un caro sale bastante menos que uno normal


def test_el_desguace_paga_menos_por_lo_robado_se_satura_y_tiene_cupo(robot):
    from juego import desguace as D, menus_juego
    p = _partida(robot, dinero=0)
    j = p.j
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "desguace")
    ganado = []
    for k in range(D.AJ.entero("cupo_dia") + 1):
        v = p.crear_vehiculo("lujo", l.x + 4, l.y, 0, "aparcado")
        v.cerrado = False
        if k == 0:
            assert D.precio(p, v) == int(v.modelo["valor"] * D.AJ("robado_pct") / 100)      # robado y entero: el 60 por ciento
        j.veh = v
        j.x, j.y = v.x, v.y
        antes = j.dinero
        menus_juego._desguace(p, l)
        robot.app.pila[-1].opciones[0].accion()
        ganado.append(j.dinero - antes)
        while len(robot.app.pila) > 1:
            robot.app.cerrar(robot.app.pila[-1])
    assert ganado[0] > ganado[1] > ganado[2] > 0                                # cada Platino de la semana vale menos
    assert ganado[-1] == 0 and j.veh is not None                                # pasado el cupo, hoy no compra más
    assert sum(ganado) < 3 * 9000                                               # adiós a los 27000 euros al día
    p.dia += 1
    assert not D.cupo_lleno(p, l)
    # uno tuyo, con papeles, se paga entero
    v = j.veh
    v.propio = True
    j.desguace["ventas"] = []
    assert D.precio(p, v) == int(v.modelo["valor"] * (0.3 + 0.7 * v.salud / v.salud_max))


def test_los_datos_y_el_editor_cubren_el_desguace():
    from juego import desguace as D
    from editor import esquema
    d = M.cargar_datos(con_mods=False)["desguace"][0]
    campos = {c["k"] for c in esquema.ESQUEMAS["ajuste_desguace"]["campos"]}
    for k in list(D.AJ._n) + list(D.AJ._l):
        assert k in d and k in campos, k


# ============================================================================ M. la mochila y el armario de casa
def _cerrar_todo(robot):
    for _ in range(20):
        if len(robot.app.pila) <= 1:
            break
        robot.app.cerrar(robot.app.pila[-1])


def test_la_mochila_tiene_sitio_y_lo_que_no_cabe_se_queda_en_el_suelo(robot):
    from juego import mochila as MO
    p = _partida(robot)
    j = p.j
    assert p.moc_capacidad() == MO.AJ.entero("capacidad") and p.moc_usado() == 0
    x, y = p.pos()
    ob = p.moc_soltar(x + 1, y, "portatil", True)
    p.recoger(ob)
    assert j.mochila == [{"id": "portatil", "robado": True}] and p.moc_usado() == 4
    while p.moc_meter("herramientas", True, callar=True):
        pass
    assert p.moc_libre() < MO.CATALOGO["herramientas"]["peso"]
    ob = p.moc_soltar(x + 1, y, "herramientas", False)
    n = len(robot.app.voz.registro)
    p.recoger(ob)
    assert ob in p.objetos and "No te cabe" in _dicho(robot, n) or "llena" in _dicho(robot, n)
    j.mochila_grande = True
    assert p.moc_capacidad() == MO.AJ.entero("capacidad_grande")


def test_de_donde_salen_los_objetos_atraco_guantera_caidos_y_buceo(robot, monkeypatch):
    from juego import mochila as MO
    p = _partida(robot)
    j = p.j
    monkeypatch.setattr(MO.random, "random", lambda: 0.0)                     # siempre sale algo
    for origen in ("atraco", "guantera"):
        o = p.moc_botin(origen)
        assert o is not None and origen in o["donde"] and j.mochila[-1] == {"id": o["id"], "robado": True}
    x, y = p.pos()
    o = p.moc_botin("caido", x + 2, y)
    assert o is not None and any(ob.tipo == "valor" and ob.item == o["id"] for ob in p.objetos)
    o = p.moc_botin("buceo")
    assert o is not None and j.mochila[-1]["robado"] is False                 # lo del fondo del mar es encontrado


def test_la_casa_de_empenos_paga_menos_por_lo_robado(robot):
    from juego import menus_lugares, mochila as MO
    p = _partida(robot, dinero=0)
    j = p.j
    l = p.lug("empenos")
    j.mochila = [{"id": "reloj", "robado": True}, {"id": "reloj", "robado": False}]
    robado, limpio = (p.moc_precio(x, l) for x in j.mochila)
    assert robado < limpio
    assert abs(robado / (MO.CATALOGO["reloj"]["valor"] * p.mercado("empenos", l.id)) - MO.AJ("robado_pct") / 100) < 0.02
    menus_lugares.empenos(p, l)
    m = robot.app.pila[-1]
    op = next(o for o in m.opciones if o.texto.startswith("Vender todo lo de la mochila"))
    op.accion()
    assert j.mochila == [] and j.dinero == robado + limpio
    _cerrar_todo(robot)


def test_el_armario_de_casa_guarda_objetos_mercancia_y_armas(robot):
    from juego import mochila as MO
    p = _partida(robot)
    j = p.j
    casa = p.lug(j.propiedades[0])
    j.mochila = [{"id": "cadena", "robado": True}]
    j.sustancias = {"hierba": 15}
    j.armas["pistola"] = {"cargador": 12, "reserva": 30}
    MO.menu_armario(p, casa)
    m = robot.app.pila[-1]
    next(o for o in m.opciones if o.texto.startswith("Guardar toda la mercancía")).accion()
    next(o for o in m.opciones if o.texto.startswith("Guardar Pistola") or o.texto.startswith("Guardar pistola")).accion()
    MO.menu_mochila(p, casa)
    robot.app.pila[-1].opciones[1].accion()                                  # el primer objeto, al armario
    a = p.almacen(casa.id)
    assert a["objetos"] == [{"id": "cadena", "robado": True}] and a["sust"] == {"hierba": 15} and "pistola" in a["armas"]
    assert j.mochila == [] and p.carga() == 0 and "pistola" not in j.armas
    # en casa no te lo quita la policía
    p.detener(sin_trato=True)
    _cerrar_todo(robot)
    assert p.almacen(casa.id)["armas"]["pistola"]["reserva"] == 30
    # y se saca
    MO.menu_armario(p, casa)
    m = robot.app.pila[-1]
    next(o for o in m.opciones if o.texto.startswith("Sacar mercancía")).accion()
    assert j.sustancias.get("hierba") == 15
    _cerrar_todo(robot)
    # una casa que deja de ser tuya se lleva el armario
    j.propiedades.remove(casa.id)
    p.limpiar_almacenes()
    assert casa.id not in j.almacen


def test_la_mercancia_ocupa_sitio_y_al_detenerte_se_llevan_lo_robado_y_la_mercancia(robot):
    from juego import mochila as MO
    p = _partida(robot, dinero=1000)
    j = p.j
    j.sustancias = {"hierba": 25}
    assert p.moc_huecos_mercancia() == 3
    j.mochila = [{"id": "reloj", "robado": True}, {"id": "monedas", "robado": False}]
    assert p.hueco_mercancia() == min(100 - 25, p.moc_libre() * 10 + 5)
    n = len(robot.app.voz.registro)
    p.detener(sin_trato=True)
    texto = " ".join(t for d in robot.app.pila if hasattr(d, "lineas") for _, t in d.lineas) + _dicho(robot, n)
    _cerrar_todo(robot)
    assert p.carga() == 0 and j.mochila == [{"id": "monedas", "robado": False}]       # lo encontrado no te lo quitan
    assert "mercancía" in texto and "robado" in texto


def test_con_algo_comprometido_el_agente_te_cachea_y_no_hay_multa(robot):
    p = _partida(robot, dinero=5000)
    j = p.j
    p.cfg["multas"] = True
    j.estrellas = 1
    j.mochila = [{"id": "movil", "robado": True}]
    n = len(robot.app.voz.registro)
    p.detener()
    m = robot.app.pila[-1]
    assert not any(o.texto.startswith("Pagar la multa") for o in m.opciones)
    assert "cachea" in _dicho(robot, n) or "registran" in _dicho(robot, n)
    _cerrar_todo(robot)
    j.mochila = []
    j.estrellas = 1
    p.transicion = False
    p.detener()
    assert any(o.texto.startswith("Pagar la multa") for o in robot.app.pila[-1].opciones)
    _cerrar_todo(robot)


def test_los_datos_y_el_editor_cubren_la_mochila():
    from juego import mochila as MO
    from editor import esquema
    d = M.cargar_datos(con_mods=False)
    campos = {c["k"] for c in esquema.ESQUEMAS["ajuste_mochila"]["campos"]}
    for k in list(MO.AJ._n) + list(MO.AJ._l):
        assert k in d["mochila"][0] and k in campos, k
    assert {o["id"] for o in d["objetos_valor"]} == set(MO.CATALOGO)
    assert {c["k"] for c in esquema.ESQUEMAS["objeto_valor"]["campos"]} >= {"id", "nombre", "peso", "valor", "donde"}


# ============================================================================ N. la vida social en persona, quedar y horarios
def _social(robot, **kw):
    p = _partida(robot, dinero=5000, **kw)
    p.cfg["adultos"] = True
    pers = p.persona_social("lucia")
    l = p.lug(pers["lugar"])
    if l.mapa != p.mundo.id:
        p.cambiar_mapa(l.mapa, l.x, l.y)
    p.j.x, p.j.y = p.mundo.punto_libre(l.x + 30, l.y + 30)     # lejos de su sitio
    return p, pers, l


def _ficha(robot, p, pid):
    from juego import menus_adultos
    menus_adultos.vida_social(p, directo=pid)
    return robot.app.pila[-1]


def test_desde_lejos_se_llama_y_se_manda_el_regalo_pero_los_gestos_son_en_persona(robot):
    from juego import encuentros as EN
    p, pers, l = _social(robot)
    r = p.relacion("lucia")
    r["afinidad"] = 50
    assert not EN.cara_a_cara(p, pers)
    m = _ficha(robot, p, "lucia")
    textos = [o.texto for o in m.opciones]
    assert "Llamarle por teléfono" in textos and "Mandarle un regalo a domicilio" in textos and "Quedar en un sitio a una hora" in textos
    n = len(robot.app.voz.registro)
    next(o for o in m.opciones if "beso" in o.texto.lower()).accion()
    assert r["afinidad"] == 50 and "en persona" in _dicho(robot, n)
    next(o for o in m.opciones if o.texto == "Llamarle por teléfono").accion()
    assert r["afinidad"] == 50 + EN.AJ.entero("llamada_afinidad")
    _cerrar_todo(robot)
    p.j.x, p.j.y = l.x, l.y                                     # en persona: allí mismo
    assert EN.cara_a_cara(p, pers)
    m = _ficha(robot, p, "lucia")
    antes = r["afinidad"]
    next(o for o in m.opciones if "beso" in o.texto.lower()).accion()
    assert r["afinidad"] > antes
    _cerrar_todo(robot)


def test_quedar_avisa_y_si_llegas_el_plan_se_vive_alli(robot):
    from juego import encuentros as EN
    p, pers, l = _social(robot)
    r = p.relacion("lucia")
    r["afinidad"] = 30
    act = next(a for a in p.dato_adulto("actividades") if a["id"] == "cena")
    sitio = EN.sitio_para(p, act, l)
    assert sitio.tipo in EN.sitios_de(act) and sitio.id != l.id
    EN.quedar(p, "lucia", pers["nombre"], sitio, EN.ahora(p) + 120, "cena")
    p.reloj += 95
    n = len(robot.app.voz.registro)
    EN.actualizar(p, 2.0)
    assert "has quedado" in _dicho(robot, n) or "te espera" in _dicho(robot, n)
    p.reloj += 25
    p.j.x, p.j.y = sitio.x, sitio.y
    citas = r.get("citas", 0)
    EN.actualizar(p, 2.0)
    assert r.get("citas", 0) == citas + 1 and r["afinidad"] > 30 and not EN.quedadas(p)
    _cerrar_todo(robot)


@pytest.mark.parametrize("aceptar", [True, False])
def test_llamada_social_puede_devolverse_sin_repetirse(robot, aceptar):
    import json
    from juego import encuentros as EN, menus_juego
    p, pers, _ = _social(robot)
    p.cfg["adultos"] = False
    p.cfg["pareja_familiar"] = True
    p.cfg["horarios"] = "apagado"
    r = p.relacion(pers["id"])
    r.update(afinidad=40, ultimo=p.dia - 1)
    p.reloj = 8 * 60
    EN.invitacion_diaria(p)
    plan = r["invitacion"]
    p._tiempo(2)
    assert "suena_hasta" not in plan
    p.reloj = 10 * 60
    p.j.estrellas = 1
    p._tiempo(2)
    assert "suena_hasta" not in plan
    p.j.estrellas = 0
    p._tiempo(2)
    hasta = plan["suena_hasta"]
    p._tiempo(2)
    assert plan["suena_hasta"] == hasta and not EN.quedadas(p)
    menus_juego.movil(p)
    assert p.app.pila[-1].opciones[0].texto == "Contestar a " + pers["nombre"]
    robot.tecla(pygame.K_ESCAPE)
    p.reloj += 11
    p.cargar_dict(json.loads(json.dumps(p.a_dict())))
    menus_juego.movil(p)
    telefono = p.app.pila[-1]
    assert telefono.opciones[0].texto == "Devolver la llamada a " + pers["nombre"]
    robot.tecla(pygame.K_RETURN)
    assert p.lug(plan["lugar"]).nombre in p.app.pila[-1].titulo
    robot.tecla(pygame.K_ESCAPE)
    assert p.app.pila[-1] is telefono and not EN.quedadas(p)
    robot.tecla(pygame.K_RETURN)
    if not aceptar:
        robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_RETURN)
    assert p.app.pila[-1] is telefono and "llamada" not in telefono.opciones[0].texto
    assert "invitacion" not in p.relacion(pers["id"])
    assert len(EN.quedadas(p)) == int(aceptar)
    assert p.relacion(pers["id"])["afinidad"] == 40


def test_llamada_respeta_turno_privacidad_y_caducidad(robot, monkeypatch):
    from juego import encuentros as EN
    p, pers, _ = _social(robot)
    r = p.relacion(pers["id"])
    r.update(afinidad=40, ultimo=p.dia - 1)
    p.cfg["horarios"] = "gente"
    p.reloj = 10 * 60
    EN.invitacion_diaria(p)
    plan = r["invitacion"]
    plan["min"] = (p.dia + 1) * 1440 + 18 * 60
    monkeypatch.setattr(EN, "presente", lambda p, pers: True)
    EN.avisar_llamada(p)
    assert "suena_hasta" not in plan
    p.j.ocultos_social.append(pers["id"])
    assert EN.llamada_social(p) is None
    p.j.ocultos_social.remove(pers["id"])
    p.reloj = 20 * 60
    EN.avisar_llamada(p)
    assert not plan["llamar"] and not EN.llamada_social(p)
    assert EN.texto_invitacion(p, plan) and not EN.quedadas(p)
    plan.pop("llamar")  # las invitaciones de partidas anteriores se contestan por escrito
    assert not EN.llamada_social(p)
    plan.update(llamar=True, min=EN.ahora(p))
    assert not EN.llamada_social(p)


def test_el_planton_sienta_mal(robot):
    from juego import encuentros as EN
    p, pers, l = _social(robot)
    r = p.relacion("lucia")
    r["afinidad"] = 40
    EN.quedar(p, "lucia", pers["nombre"], l, EN.ahora(p) + 60, "paseo")
    p.reloj += 60 + EN.AJ.entero("espera_minutos") + 5
    EN.actualizar(p, 2.0)
    assert r["afinidad"] == 40 - EN.AJ.entero("planton_afinidad") and not EN.quedadas(p)


def test_la_cita_en_persona_se_viene_contigo_y_pasa_al_llegar_al_sitio(robot):
    from juego import encuentros as EN, sistemas
    p, pers, l = _social(robot)
    r = p.relacion("lucia")
    r["afinidad"] = 30
    p.j.x, p.j.y = l.x, l.y
    act = next(a for a in p.dato_adulto("actividades") if a["id"] == "cine")
    assert sistemas.empezar_paseo(p, pers, plan=act)
    assert p.acompanante["plan"] == "cine" and p.gps is not None
    cine = EN.sitio_para(p, act, l)
    citas = r.get("citas", 0)
    sistemas.visita_con_acompanante(p, cine)
    assert r["citas"] == citas + 1 and p.acompanante and p.acompanante["plan"] is None
    _cerrar_todo(robot)


def test_cita_interactiva_cancelar_reintentar_y_pagar_a_medias(robot):
    from juego import encuentros as EN, sistemas
    p, pers, base = _social(robot)
    p.cfg["citas_interactivas"] = True
    act = next(a for a in p.dato_adulto("actividades") if a["id"] == "cine")
    r = p.relacion(pers["id"])
    assert sistemas.empezar_paseo(p, pers, plan=act)
    cine = EN.sitio_para(p, act, base)
    a = p.acompanante
    hasta, hora, citas = a["hasta"], EN.ahora(p), r.get("citas", 0)
    for avanzar in (False, True):
        sistemas.visita_con_acompanante(p, cine)
        if avanzar:
            robot.tecla(pygame.K_RETURN)
        robot.tecla(pygame.K_ESCAPE)
        assert (a["plan"], a["hasta"], EN.ahora(p), r.get("citas", 0)) == ("cine", hasta, hora, citas)
        assert cine.id not in a["sitios"]
    sistemas.visita_con_acompanante(p, cine)
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_RETURN)
    cuenta = p.app.pila[-1]
    assert pers["nombre"] in cuenta.titulo
    mitad = (act["precio"] + 1) // 2
    p.j.dinero = mitad
    robot.tecla(pygame.K_RETURN)
    assert p.app.pila[-1] is cuenta and p.j.dinero == mitad and r.get("citas", 0) == citas
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_RETURN)
    assert p.j.dinero == 0 and r["citas"] == citas + 1 and a["plan"] is None
    assert a["sitios"].count(cine.id) == 1 and a["hasta"] == hasta + 60 * act["horas"]


def test_cita_interactiva_desde_el_movil_y_al_llegar_a_una_quedada(robot):
    from juego import encuentros as EN
    p, pers, base = _social(robot)
    p.cfg["citas_interactivas"] = True
    p.cfg["vida_en_persona"] = False
    p.cfg["adultos"] = False
    p.cfg["pareja_familiar"] = True
    r = p.relacion(pers["id"])
    r["afinidad"] = 30
    ficha = _ficha(robot, p, pers["id"])
    next(o for o in ficha.opciones if o.texto == "Proponer una cita").accion()
    planes = p.app.pila[-1]
    next(o for o in planes.opciones if "paseo" in o.texto.lower()).accion()
    robot.tecla(pygame.K_RETURN)
    assert p.app.pila[-1].opciones[0].texto == "Terminar la cita"
    robot.tecla(pygame.K_ESCAPE)
    assert p.app.pila[-1] is planes and not r.get("citas")
    _cerrar_todo(robot)
    act = next(a for a in p.dato_adulto("actividades") if a["id"] == "copas")
    sitio = EN.sitio_para(p, act, base)
    EN.quedar(p, pers["id"], pers["nombre"], sitio, EN.ahora(p) + 60, act["id"])
    p.reloj += 60
    p.j.x, p.j.y = sitio.x, sitio.y
    dinero = p.j.dinero
    EN.actualizar(p, 2.)
    assert sitio.nombre in p.app.pila[-1].titulo and not EN.quedadas(p)
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_RETURN)
    assert p.j.dinero == dinero - (act["precio"] + 1) // 2 and r["citas"] == 1


def test_horarios_de_la_gente_y_de_los_locales(robot):
    from juego import encuentros as EN
    p, pers, l = _social(robot)
    assert EN.presente(p, pers)                                   # apagado: como antes
    p.cfg["horarios"] = "gente"
    desde, hasta, libre = EN.horario_persona(p, pers)
    p.dia = next(d for d in range(1, 9) if EN.dia_semana(p, d) != libre)
    p.reloj = desde * 60 + 30
    assert EN.presente(p, pers) and "Ahora está allí" in EN.donde_txt(p, pers)
    p.reloj = 4 * 60
    assert not EN.presente(p, pers) and "no está allí" in EN.donde_txt(p, pers)
    p.dia = next(d for d in range(1, 9) if EN.dia_semana(p, d) == libre)
    p.reloj = desde * 60 + 30
    assert not EN.presente(p, pers)
    banco = next(x for x in p.lugares.values() if x.tipo == "banco")
    assert EN.local_abierto(p, banco)[0]                          # con «gente», los locales abren siempre
    p.cfg["horarios"] = "todo"
    p.dia = next(d for d in range(1, 9) if EN.dia_semana(p, d) == 6)      # domingo
    p.reloj = 11 * 60
    abierto, texto = EN.local_abierto(p, banco)
    assert not abierto and ("Abre mañana" in texto or "Abre el lunes" in texto)
    p.reloj = 22 * 60
    p.dia += 1
    assert not EN.local_abierto(p, banco)[0]
    abre = EN.horario_local(p, banco)[0]
    p.reloj = abre * 60 + 30
    assert EN.local_abierto(p, banco)[0]
    p.reloj = 22 * 60
    p.mision = {"def": {}}                                        # con una misión en curso, todo abierto
    try:
        assert EN.local_abierto(p, banco)[0]
    finally:
        p.mision = None


def test_la_infidelidad_deja_herida_y_a_la_segunda_se_acaba(robot, monkeypatch):
    from juego import adultos, encuentros as EN
    p, pers, l = _social(robot)
    j = p.j
    r = p.relacion("lucia")
    r.update(afinidad=90, estado="pareja")
    j.pareja = "lucia"
    monkeypatch.setattr(adultos.random, "random", lambda: 0.0)               # se entera siempre
    p.celos("andres")
    assert EN.desconfianza(p, "lucia") == EN.AJ.entero("desconfianza_dias") and j.pareja == "lucia"
    antes = r["afinidad"]
    p.sumar_afinidad("lucia", 10)
    assert r["afinidad"] == antes + 5                                        # mientras dura, acerca la mitad
    monkeypatch.setattr(EN.random, "random", lambda: 0.0)
    p.j.x, p.j.y = l.x, l.y
    assert EN.pedir_perdon(p, pers) and EN.desconfianza(p, "lucia") == EN.AJ.entero("desconfianza_dias") - EN.AJ.entero("perdon_dias")
    p.celos("andres")                                                        # otra vez, con la herida abierta
    assert j.pareja == "" and r["estado"] == "ex"


def test_quedar_con_un_conocido(robot):
    from juego import encuentros as EN
    p = _partida(robot, dinero=100)
    j = p.j
    j.conocidos.append({"nombre": "Ramiro", "genero": "h", "edad": 40, "oficio": "pescador", "caracter": "amable", "mapa": p.mundo.id, "dia": 1, "ultimo": 0})
    bar = next(x for x in p.mundo.lugares.values() if x.tipo in ("bar", "taberna", "comida", "pizzeria"))
    EN.quedar(p, "c:Ramiro", "Ramiro", bar, EN.ahora(p) + 60)
    p.reloj += 60
    p.j.x, p.j.y = bar.x, bar.y
    EN.actualizar(p, 2.0)
    assert j.conocidos[-1]["amistad"] == EN.AJ.entero("conocido_amistad") and j.dinero == 100 - EN.AJ.entero("conocido_precio")


def test_los_datos_y_el_editor_cubren_las_citas_y_los_horarios():
    from juego import encuentros as EN
    from editor import esquema
    d = M.cargar_datos(con_mods=False)
    campos = {c["k"] for c in esquema.ESQUEMAS["ajuste_encuentros"]["campos"]}
    for k in list(EN.AJ._n) + list(EN.AJ._l):
        assert k in d["encuentros"][0] and k in campos, k
    assert {h["tipo"] for h in d["horarios_locales"]} == set(EN.HORARIOS)
    assert all("lugares" in a for a in d["adultos"]["actividades"] if a["id"] != "paseo")
    assert "lugares" in {c["k"] for c in esquema.ESQUEMAS["actividad"]["campos"]}


# ============================================================================ O. el vestuario
def test_la_tienda_de_ropa_va_por_estilos_y_lo_comprado_se_queda(robot):
    from juego import menus_lugares, vestuario as VE
    p = _partida(robot, dinero=5000)
    j = p.j
    l = next(x for x in p.lugares.values() if x.tipo == "ropa")
    menus_lugares.ropa(p, l)
    m = robot.app.pila[-1]
    textos = [o.texto for o in m.opciones]
    assert any(t.startswith("Ropa elegante") for t in textos) and any(t.startswith("Calzado:") for t in textos)
    next(o for o in m.opciones if o.texto.startswith("Ropa elegante")).accion()
    sub = robot.app.pila[-1]
    traje = next(o for o in sub.opciones if o.texto.startswith("Traje elegante"))
    traje.accion()
    assert j.ropa == "traje elegante" and j.dinero == 5000 - 400 and VE.estilo(p) == "elegante"
    assert "Lo llevas puesto" in traje.texto
    _cerrar_todo(robot)
    # ponerse otra cosa y volver a lo que ya era tuyo, sin pagar
    VE.poner_prenda(p, VE.prenda(p, "Chándal"))
    antes = j.dinero
    VE.menu_vestirte(p)
    vm = robot.app.pila[-1]
    next(o for o in vm.opciones if o.texto.startswith("Ponerte traje elegante")).accion()
    assert j.ropa == "traje elegante" and j.dinero == antes
    _cerrar_todo(robot)


def test_el_calzado_a_juego_y_el_estilo_que_le_gusta_en_una_cita(robot):
    from juego import encuentros as EN, vestuario as VE
    p, pers, l = _social(robot)
    r = p.relacion("lucia")
    r["afinidad"] = 30
    e = VE.estilo_de(p, pers)
    assert e == "fiesta"                                           # lo dicen los datos
    pr = next(x for x in p.datos["prendas"] if x.get("estilo") == e)
    ca = next(x for x in p.datos["calzado"] if x.get("estilo") == e)
    VE.poner_prenda(p, pr)
    VE.poner_calzado(p, ca)
    assert VE.conjuntado(p) and VE.bono_cita(p, pers)[0] == VE.AJ.entero("cita_estilo_afinidad") + VE.AJ.entero("conjunto_afinidad")
    act = next(a for a in p.dato_adulto("actividades") if a["id"] == "copas")
    gusta = act["id"] in pers.get("gustos", [])
    EN.vivir_cita(p, pers, act)
    assert r["afinidad"] == 30 + (13 if gusta else 5) + VE.AJ.entero("cita_estilo_afinidad") + VE.AJ.entero("conjunto_afinidad")
    _cerrar_todo(robot)
    VE.poner_prenda(p, VE.prenda(p, "Mono de trabajo"))
    assert VE.bono_cita(p, pers)[0] == 0
    assert "calzado" in p.aspecto_txt() or ca["nombre"].lower() in p.aspecto_txt()


def test_una_partida_antigua_empieza_con_lo_que_llevaba_y_el_editor_lo_cubre(robot):
    from juego import vestuario as VE
    from editor import esquema
    p = _partida(robot)
    j = p.j
    j.vestuario = {}
    j.ropa = "cazadora de cuero"
    j.accesorios = {"gafas": "Gafas de sol"}
    v = VE.vestuario(p)
    assert "cazadora de cuero" in v["prendas"] and "Gafas de sol" in v["complementos"]
    d = M.cargar_datos(con_mods=False)
    assert len(d["prendas"]) >= 30 and len(d["calzado"]) >= 12 and len(d["complementos"]) >= 25
    assert all(x.get("estilo") in VE.ESTILOS for x in d["prendas"] + d["calzado"])
    campos = lambda t: {c["k"] for c in esquema.ESQUEMAS[t]["campos"]}
    assert {"estilo", "desc"} <= campos("prenda") and {"estilo", "animo", "desc"} <= campos("calzado")
    assert {"estilo", "desde", "hasta", "libre"} <= campos("persona")
    for k in list(VE.AJ._n) + list(VE.AJ._l):
        assert k in d["vestuario"][0] and k in campos("ajuste_vestuario"), k


# ============================================================================ P. la bolsa
def test_la_bolsa_avisa_cada_medianoche_reparte_dividendos_y_cuenta_lo_ganado(robot, monkeypatch):
    from juego import bolsa as B, menus_extra
    p = _partida(robot, dinero=100000)
    j = p.j
    j.banco = 0
    assert p.comprar_acciones("naviera", 600)
    coste = j.coste_acciones["naviera"]
    p.dia = B.AJ.entero("dividendo_dias") - 1
    n = len(robot.app.voz.registro)
    p.dia += 1
    p.mover_bolsa()
    dicho = _dicho(robot, n)
    assert "tus acciones valen" in dicho or "tu cartera vale" in dicho
    assert j.banco > 0 and "dividendos" in dicho.lower()                       # la naviera reparte
    menus_extra.bolsa(p)
    m = robot.app.pila[-1]
    assert m.opciones[0].texto.startswith("Tu cartera vale")
    assert any("desde ayer" in o.texto for o in m.opciones)
    k, ganado = p.vender_acciones("naviera", 300)
    assert k == 300 and abs(j.coste_acciones["naviera"] - coste / 2) < 1
    _cerrar_todo(robot)


def test_las_noticias_mueven_la_bolsa_y_se_cuentan(robot, monkeypatch):
    from juego import bolsa as B
    p = _partida(robot, dinero=100000)
    j = p.j
    p.comprar_acciones("conservas", 100)
    monkeypatch.setattr(B.random, "random", lambda: 0.0)                     # noticia segura, y de subida
    antes = p.precio_accion("conservas")
    n = len(robot.app.voz.registro)
    p.mover_bolsa()
    assert j.bolsa_noticias and j.bolsa_noticias[0]["id"] in B.EMPRESAS
    assert any(x["texto"] in _dicho(robot, n) for x in j.bolsa_noticias if x["id"] == "conservas")
    assert p.precio_accion("conservas") != antes


def test_los_datos_y_el_editor_cubren_la_bolsa():
    from juego import bolsa as B
    from editor import esquema
    d = M.cargar_datos(con_mods=False)
    assert {e["id"] for e in d["bolsa_empresas"]} == set(B.EMPRESAS)
    campos = lambda t: {c["k"] for c in esquema.ESQUEMAS[t]["campos"]}
    for k in list(B.AJ._n) + list(B.AJ._l):
        assert k in d["bolsa"][0] and k in campos("ajuste_bolsa"), k
    assert {"base", "volatilidad", "dividendo", "sube", "baja"} <= campos("empresa_bolsa")


# ============================================================================ Q. higiene, hambre y sed
def test_oliendo_mal_la_gente_lo_nota_y_el_portero_no_deja_pasar(robot):
    from juego import necesidades as NE
    p, pers, l = _social(robot)
    p.cfg["vida_realista"] = True
    j = p.j
    j.suciedad = 95
    assert p.apesta() and p.sucio()
    club = next((x for x in p.lugares.values() if x.tipo in NE.AJ.lista("locales_exigentes")), None)
    if club is not None:
        assert p.portero_no_deja(club)
    # la cita acerca la mitad, y nada de besos
    r = p.relacion("lucia")
    r["afinidad"] = 30
    act = next(a for a in p.dato_adulto("actividades") if a["id"] == "cine")
    from juego import encuentros as EN
    EN.vivir_cita(p, pers, act)
    _cerrar_todo(robot)
    gana = r["afinidad"] - 30
    j.suciedad = 0
    r["afinidad"] = 30
    r["hoy"] = {}
    EN.vivir_cita(p, pers, act)
    _cerrar_todo(robot)
    assert gana < r["afinidad"] - 30
    j.suciedad = 95
    assert not p.gesto("lucia", pers, "beso")
    # la charla: menos confianza
    f = {"confianza": 0}
    p._trato(f, 10)
    assert f["confianza"] == 5


def test_asearse_en_el_gimnasio_en_el_mar_y_con_lo_de_la_drogueria(robot):
    from juego import menus_lugares, necesidades as NE
    p = _partida(robot, dinero=100)
    p.cfg["vida_realista"] = True
    j = p.j
    j.suciedad = 95
    p.asearse(25)
    assert j.suciedad == 70
    p.asearse(100)
    assert j.suciedad == NE.AJ("aseo_minimo")                   # sin ducha, no del todo
    j.suciedad = 95
    p.bano_en_el_mar()
    assert j.suciedad == NE.AJ("mar_limpia")
    gym = next(x for x in p.lugares.values() if x.tipo == "gimnasio")
    menus_lugares.gimnasio(p, gym)
    next(o for o in robot.app.pila[-1].opciones if o.texto.startswith("Ducharte")).accion()
    assert j.suciedad == 0 and j.dinero == 100 - NE.AJ.entero("ducha_gimnasio_precio")
    _cerrar_todo(robot)
    # el desodorante, desde lo que llevas encima
    j.suciedad = 80
    j.encima = [{"id": "desodorante", "n": 1}]
    texto = p.comer_lote(j.encima, j.encima[0])
    assert texto and "Desodorante" in texto or "desodorante" in texto
    assert j.suciedad == 55


def test_con_hambre_sed_o_suciedad_el_animo_baja_y_se_bebe_en_las_fuentes(robot):
    from juego import necesidades as NE
    p = _partida(robot)
    p.cfg["vida_realista"] = True
    j = p.j
    j.hambre, j.sed, j.suciedad, j.animo = 90, 0, 0, 60.0
    p.pasar_necesidades(NE.AJ("animo_cada") + 1)
    assert j.animo < 60
    fuente = next((l for l in p.lugares.values() if l.get("fuente")), None)
    assert fuente is not None
    j.sed = 80
    p.beber_en_fuente()
    assert j.sed == 80 - NE.AJ("fuente_sed")


def test_los_datos_y_el_editor_cubren_la_higiene():
    from juego import necesidades as NE
    from editor import esquema
    d = M.cargar_datos(con_mods=False)
    campos = lambda t: {c["k"] for c in esquema.ESQUEMAS[t]["campos"]}
    for k in list(NE.AJ._n) + list(NE.AJ._l):
        assert k in d["necesidades"][0] and k in campos("ajuste_necesidades"), k
    assert "aseo" in campos("producto")
    assert any(x.get("aseo") for x in d["productos"]) and "drogueria" in {x["id"] for x in d["pasillos"]}
    assert "drogueria" in next(t for t in d["tipos_tienda"] if t["id"] == "supermercado")["pasillos"]
    assert "fuente" in campos("lugar")                                        # las fuentes, en los datos de cada lugar
    assert any(l.get("fuente") for l in d["lugares"]) if isinstance(d.get("lugares"), list) else True


# ============================================================================ R. la vida del capo
def _con_banda(robot, n=2, **kw):
    p = _partida(robot, dinero=20000, **kw)
    j = p.j
    j.territorios = ["t1", "t2", "t3"]
    j.banda = n
    j.banda_nombre = "Los del Puerto"
    p.banda_fichas()
    return p


def test_la_paga_de_la_banda_y_la_lealtad_cada_dia(robot):
    from juego import capo as CA, sistemas
    p = _con_banda(robot)
    j = p.j
    f = p.banda_fichas()[0]
    f["lealtad"] = 50
    f["trato"] = {"charla": p.dia}
    j.banda_paga = "baja"
    p._lealtad_del_dia()
    assert f["lealtad"] == 50 - CA.AJ.entero("lealtad_baja_resta")
    j.banda_paga = "alta"
    f["lealtad"] = 50
    p._lealtad_del_dia()
    assert f["lealtad"] == 51
    antes = j.dinero
    sistemas.paga(p)
    assert antes - j.dinero == int(p.precio("sueldo_banda", sistemas.SUELDO) * CA.AJ("paga_alta_pct") / 100) * j.banda
    # olvidado, la lealtad baja sola
    j.banda_paga = "normal"
    f["trato"] = {}
    f["alta"] = p.dia - 20
    f["lealtad"] = 50
    p._lealtad_del_dia()
    assert f["lealtad"] == 50 - CA.AJ.entero("olvido_resta")
    assert "contento" in p.estado_animo_banda({"lealtad": 70})


def test_sin_dinero_para_la_paga_se_enfadan_y_se_va_el_menos_leal(robot):
    from juego import capo as CA, sistemas
    p = _con_banda(robot, n=3)
    j = p.j
    fs = p.banda_fichas()
    fs[0]["lealtad"], fs[1]["lealtad"], fs[2]["lealtad"] = 80, 15, 60
    j.dinero = 0
    menos_leal = fs[1]["n"]
    sistemas.paga(p)
    assert j.banda == 2 and menos_leal not in [f["n"] for f in p.banda_fichas()]
    assert all(f["lealtad"] < 80 for f in p.banda_fichas())


def test_tu_gente_vende_tu_mercancia_y_cocina_en_tu_laboratorio(robot, monkeypatch):
    from juego import capo as CA
    p = _con_banda(robot)
    p.cfg["adultos"] = True
    j = p.j
    casa = j.propiedades[0]
    j.laboratorios = [casa]
    j.material = 2
    p.almacen(casa)["sust"] = {"polvo": 30}
    camello, cocinero = p.banda_fichas()
    camello.update(tarea="vender", lealtad=80)
    cocinero.update(tarea="cocinar:" + casa, lealtad=80)
    monkeypatch.setattr(CA.random, "random", lambda: 0.99)                 # ni detenciones, ni incendios, ni traiciones, ni robos
    antes, negro = j.dinero, p.hon().get("negro", 0)
    p.dia_capo()
    assert j.dinero > antes and p.hon().get("negro", 0) > negro           # te lo traen en mano, y es dinero negro
    assert j.material == 1 and j.stats.get("vendido_banda", 0) > 0 and j.stats.get("fabricado", 0) > 0
    # a uno poco leal lo detienen y canta
    camello["lealtad"] = 10
    monkeypatch.setattr(CA.random, "random", lambda: 0.0)
    p.almacen(casa)["sust"] = {"polvo": 30}
    texto, euros = "", 0
    euros, texto = p._vender_camello(camello)
    assert euros == 0 and "cantado" in texto and camello["baja"] > p.dia


def test_las_traiciones_y_los_robos_en_casa_con_caja_fuerte(robot, monkeypatch):
    from juego import capo as CA
    p = _con_banda(robot)
    j = p.j
    casa = j.propiedades[0]
    a = p.almacen(casa)
    a["dinero"] = 1000
    f = p.banda_fichas()[0]
    f["lealtad"] = 5
    monkeypatch.setattr(CA.random, "choice", lambda xs: xs[0])            # la primera traición: robo
    texto = p._traicion(f)
    assert a["dinero"] < 1000 and j.banda == 1 and "falta" in texto.lower()
    # un robo en casa, sin y con caja fuerte
    a["dinero"] = 1000
    p._robo_casa(casa)
    assert a["dinero"] == 1000 - int(1000 * CA.AJ("robo_casa_dinero_pct") / 100)
    j.muebles.setdefault(casa, []).append("caja_fuerte")
    a["dinero"] = 1000
    p._robo_casa(casa)
    assert a["dinero"] == 1000
    j.muebles[casa].append("alarma")
    assert p._mueble(casa, "contra_robos") == 75


def test_el_banco_no_admite_mucho_dinero_negro_y_se_blanquea_en_el_casino_y_con_el_gestor(robot, monkeypatch):
    from juego import capo as CA, menus_lugares
    p = _partida(robot, dinero=20000, consecuencias="normal", impuestos_facturas=True)
    j = p.j
    j.banco = 0
    p.hon()["negro"] = 15000.0
    assert p.blanqueo_activo()
    banco = next(x for x in p.lugares.values() if x.tipo == "banco")
    menus_lugares.banco(p, banco)
    n = len(robot.app.voz.registro)
    next(o for o in robot.app.pila[-1].opciones if o.texto == "Ingresar todo el efectivo").accion()
    assert j.banco == CA.AJ.entero("deposito_libre") and "Hacienda" in _dicho(robot, n)
    _cerrar_todo(robot)
    negro = p.hon()["negro"]
    blanqueado, _ = p.blanquear_casino(2000)
    assert blanqueado == 2000 and p.hon()["negro"] == negro - 2000
    monkeypatch.setattr(CA.random, "random", lambda: 0.99)
    p.blanquear_gestor(CA.AJ.entero("gestor_minimo"))
    p.dia += CA.AJ.entero("gestor_dias")
    antes = j.banco
    p.dia_capo()
    assert j.banco == antes + int(CA.AJ.entero("gestor_minimo") * (1 - CA.AJ("gestor_comision") / 100))


def test_el_dinero_se_lleva_encima_cajeros_atracos_y_la_granada(robot):
    from juego import menus_capo, combate
    p = _partida(robot, dinero=10)
    j = p.j
    j.banco = 500
    n = len(robot.app.voz.registro)
    assert not p.pagar(100)
    assert "cajero" in _dicho(robot, n)
    menus_capo._sacar(p, 100)
    assert j.dinero == 110 and j.banco == 400 and p.pagar(100)
    assert any(l.get("cajero") for l in p.lugares.values())
    # el atraco por la calle: pierdes lo que llevas, no lo del banco
    j.dinero = 1000
    p.atraco_a_ti()
    robot.app.pila[-1].opciones[0].accion()
    assert j.dinero == 300 and j.banco == 400
    # la granada habla de granadas
    g = next(a for a in p.datos["armas"] if a["id"] == "granada")
    assert combate.municion_txt(g, {"cargador": 1, "reserva": 2}) == "1 granada y 2 de reserva"


def test_los_datos_y_el_editor_cubren_la_vida_del_capo():
    from juego import capo as CA
    from editor import esquema
    d = M.cargar_datos(con_mods=False)
    campos = lambda t: {c["k"] for c in esquema.ESQUEMAS[t]["campos"]}
    for k in list(CA.AJ._n) + list(CA.AJ._l):
        assert k in d["capo"][0] and k in campos("ajuste_capo"), k
    assert {"caja_fuerte", "contra_robos"} <= campos("mueble") and "cajero" in campos("lugar") and "unidad" in campos("arma")
    assert any(m.get("caja_fuerte") for m in d["muebles"]) and any(m.get("contra_robos") for m in d["muebles"])
