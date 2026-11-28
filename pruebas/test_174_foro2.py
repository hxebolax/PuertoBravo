"""1.7.4, segunda tanda: lo del hilo tras la primera, las issues 28, 29, 31 y 32 y la salida de sonido en caliente."""
import inspect

import pygame
import pytest

from juego import conduccion, convivencia as CV, honrado as HO, menus_juego, salidas, sistemas
from juego.entidades import Objeto
from juego.menus import Menu, Opcion


def _texto(o):
    return o.texto


def _cerrar_menus(robot):
    while robot.app.pila[-1] is not robot.p:
        robot.app.cerrar(robot.app.pila[-1])


def _con_adultos(robot):
    robot.app.cfg["adultos"] = True
    robot.app.aplicar_adultos()
    p = robot.nueva_partida()
    p.t_evento = 1e9
    return p


def _paseo(robot):
    p = _con_adultos(robot)
    pers = p.persona_social("lucia")
    assert sistemas.empezar_paseo(p, pers)
    return p, pers, p.acompanante


# ============================================================ misiones: varias en el mismo sitio
def test_varias_misiones_en_un_sitio_se_elige_cual_y_la_marcada_empieza_sola(robot):
    p = robot.nueva_partida()
    p.objetos = []
    l = next(iter(p.mundo.lugares.values()))
    ms = [m for m in p.datos["misiones"] if not m.get("tutorial")][:2]
    empezadas = []
    p.lugar_al_alcance = lambda: l
    p.misiones_en_lugar = lambda lid: ms
    p.iniciar_mision = lambda m: empezadas.append(m["id"])
    p.interactuar()
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu) and "2 misiones" in menu.titulo and not empezadas
    assert any(_texto(o).startswith("Entrar en") for o in menu.opciones)
    menu.i = 1
    robot.tecla(pygame.K_RETURN)
    assert empezadas == [ms[1]["id"]]
    # marcada en el móvil: Intro empieza esa, sin preguntar
    p.mision_marcada = ms[1]["id"]
    p.interactuar()
    assert empezadas == [ms[1]["id"]] * 2 and robot.app.pila[-1] is p and p.mision_marcada is None


# ============================================================ el paseo con tu acompañante (issue 29)
def test_pasos_del_acompanante_siguen_su_posicion_y_su_ritmo(robot, monkeypatch):
    p, _, a = _paseo(robot)
    x, y = p.pos()
    pasos = []
    monkeypatch.setattr(p, "son", lambda sonido, **kw: pasos.append((sonido, kw["xy"])))
    monkeypatch.setattr(p.mundo, "superficie", lambda x, y: "arena")
    monkeypatch.setattr(p.mundo, "sobre_vias", lambda x, y: False)
    for pie in (0, 1):
        monkeypatch.setitem(p.mez.sonidos, f"paso_arena{pie}", True)
    a["x"] = x + 20
    sistemas.paso_acompanante(p, .03)
    rapido = a["t_paso"]
    assert pasos[0] == ("paso_arena1", (a["x"], a["y"]))
    assert pasos[1][1] == pasos[0][1]
    a.update(x=x + 5, t_paso=0)
    sistemas.paso_acompanante(p, .03)
    assert pasos[2] == ("paso_arena0", (a["x"], a["y"]))
    assert a["t_paso"] > rapido
    a.update(x=x, y=y, t_paso=0)
    sistemas.paso_acompanante(p, .03)
    assert len(pasos) == 4


def test_el_acompanante_no_se_baja_del_coche_en_marcha(robot):
    p, pers, a = _paseo(robot)
    x, y = p.pos()
    m = next(m for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela"))
    v = p.crear_vehiculo(m["id"], x, y, 0, None)
    p.j.veh, v.vel = v, 12.0
    a["hasta"] = 0
    sistemas.paso_acompanante(p, 0.03)
    sistemas.paso_acompanante(p, 0.03)
    assert p.acompanante is a and robot.dicho().count("Se me está haciendo tarde") == 1
    v.vel = 0.0
    sistemas.paso_acompanante(p, 0.03)
    assert p.acompanante is None and "Se ha hecho tarde" in robot.dicho()


@pytest.mark.parametrize("tipo,empieza,clave", [("bar", "Invitar a", "invitado"), ("loteria", "Regalarle un décimo", "decimo")])
def test_invitar_al_acompanante_o_regalarle_un_decimo(robot, tipo, empieza, clave):
    p, pers, a = _paseo(robot)
    l = next(l for l in p.lugares.values() if l.tipo == tipo)
    menu = Menu(robot.app, "local", [Opcion("Salir", lambda: None)])
    sistemas.con_acompanante_en_local(p, l, menu, Opcion)
    op = next(o for o in menu._fuente() if o.texto.startswith(empieza))
    assert pers["nombre"] in op.texto and op.ayuda
    p.j.dinero = 100
    puntos = a["puntos"]
    op.accion()
    assert a["puntos"] == puntos + 2 and clave in a["detalles"] and p.j.dinero < 100
    dinero = p.j.dinero
    op.accion()                                              # una vez por paseo
    assert p.j.dinero == dinero and "Ya has tenido ese detalle" in robot.dicho()


def test_al_llegar_juntos_a_casa_no_te_oye_llegar(robot):
    p, pers, a = _paseo(robot)
    p.cfg["pareja_convive"] = True
    j = p.j
    casa = p.lugares["casa_abuela"]
    r = p.relacion(pers["id"])
    r.update(estado="pareja", afinidad=90, citas=5, ultimo=p.dia)
    j.pareja = pers["id"]
    j.convive, j.convive_casa, j.convive_desde = pers["id"], casa.id, p.dia
    if casa.id not in j.propiedades:
        j.propiedades.append(casa.id)
    a["puntos"] = 3
    CV.AJ.n["peticion_prob"] = 0
    p.reloj = 12 * 60.0
    sistemas.visita_con_acompanante(p, casa)
    assert p.acompanante is None and "Llegáis juntos a casa" in robot.dicho()
    saludo = p.saludo_de_casa(casa)
    assert any(f.replace("{n}", pers["nombre"]) == saludo for f in CV.AJ.lista("frases_llegais"))
    # otro día, sin llegar juntos: si no está en casa ni en su sitio, no se dice dónde está
    from juego import encuentros
    original = encuentros.presente
    encuentros.presente = lambda p_, pers_: False
    try:
        p.pareja_en_casa = lambda: False
        saludo = p.saludo_de_casa(casa)
    finally:
        encuentros.presente = original
    assert any(f.replace("{n}", pers["nombre"]) == saludo for f in CV.AJ.lista("frases_ausente_fuera"))


def test_en_casa_la_m_abre_el_movil_y_la_v_y_la_t_informan(robot):
    p = robot.nueva_partida()
    casa = p.lugares["casa_abuela"]
    interior = sistemas.Interior(p, casa, {"descansar": lambda: None, "garaje": lambda: None})
    robot.app.abrir(interior)
    robot.tecla(pygame.K_t)
    assert "Son las" in robot.app.voz.registro[-1]
    robot.tecla(pygame.K_m)
    assert isinstance(robot.app.pila[-1], Menu) and robot.app.pila[-2] is interior
    robot.app.cerrar(robot.app.pila[-1])
    n = len(robot.app.voz.registro)
    robot.tecla(pygame.K_v)
    assert len(robot.app.voz.registro) > n and robot.app.pila[-1] is interior
    assert "la M abre el móvil" in interior.ayuda()
    _cerrar_menus(robot)


# ============================================================ la fama en la calle (issue 28)
def test_con_los_chavales_del_barrio_baja_la_fama_una_vez_al_dia(robot):
    p = robot.nueva_partida()
    j = p.j
    j.reputacion, j.estrellas = 30.0, 0
    prestigio = j.ciudadania
    hora = p.reloj
    p.hon_chavales()
    assert j.reputacion == 30.0 - HO.AJ("chavales_fama") and j.ciudadania >= prestigio
    assert p.reloj != hora and any(f.split("{")[0][:20] in robot.dicho() for f in HO.AJ.lista("frases_chavales"))
    p.hon_chavales()
    assert j.reputacion == 30.0 - HO.AJ("chavales_fama") and "Vuelve mañana" in robot.dicho()
    p.dia += 1
    j.estrellas = 2
    p.hon_chavales()
    assert j.reputacion == 30.0 - HO.AJ("chavales_fama") and "policía" in robot.dicho()


# ============================================================ recoger al pasar
def test_recoger_al_pasar_se_puede_apagar(robot):
    p = robot.nueva_partida()
    assert p.cfg["recoger_al_pasar"] is True
    x, y = p.pos()
    o = Objeto("dinero", "Billetes", x, y)
    o.valor = 50
    p.cfg["recoger_al_pasar"] = False
    p.objetos.append(o)
    robot.frames(20)                                         # se mira cada 0,3 segundos
    assert o in p.objetos                                    # no se mete solo
    p.cfg["recoger_al_pasar"] = True
    robot.frames(20)
    assert o not in p.objetos


# ============================================================ la policía dice por qué (issue 31)
def test_cuando_sube_la_busqueda_se_dice_el_delito(robot):
    p = robot.nueva_partida()
    j = p.j
    j.estrellas, j.puntos_busqueda = 1, 1.0
    p.delito(10, "chocar contra un coche patrulla", siempre=True)
    p.actualizar_policia(0.03)
    assert j.estrellas >= 2 and "Delito: chocar contra un coche patrulla" in robot.dicho()
    assert 'tr("chocar contra un coche patrulla")' in inspect.getsource(conduccion)


# ============================================================ el piloto con mucha prisa va a toda velocidad (issue 32)
def test_el_piloto_con_mucha_prisa_va_a_toda_la_velocidad_del_vehiculo(robot):
    p = robot.nueva_partida()
    m = next(m for m in p.datos["vehiculos"] if not m.get("barco") and not m.get("vuela"))
    v = p.crear_vehiculo(m["id"], *p.pos(), 0, None)
    motor = next(k for k, x in sistemas.MEJORAS.items() if x["efecto"] == "motor")
    sistemas.poner(v, {motor: sistemas.niveles(motor)})
    p.j.veh = v
    p.cfg["piloto_estilo"] = "mucha_prisa"
    p.gps = {"dest": (v.x + 5000, v.y), "ruta": [], "sigue": None, "nombre": "lejos", "clave": None, "auto": True}
    p._piloto_curva = lambda v, freno: 999.0
    v.vel = 0.0
    for _ in range(4000):
        p._pilotar(v, 0.05, 10.0)
    assert abs(v.vel - p.velocidad_maxima(v)) < 0.5 and v.vel > m["vel_max"] * 1.05


# ============================================================ el mando al volante
def test_el_boton_de_recargar_recarga_al_volante_y_no_cambia_la_radio(robot):
    p = robot.nueva_partida()
    llamado = []
    p.recargar = lambda: llamado.append(True)
    robot.app.mando._accion("recargar", "coche")
    assert llamado == [True]


# ============================================================ la salida de sonido
def test_elegir_la_salida_de_sonido_y_la_segunda(robot, monkeypatch):
    app = robot.app
    monkeypatch.setattr(salidas, "disponibles", lambda: ["Altavoces (Realtek)", "CABLE Input (VB-Audio)"])
    monkeypatch.setattr(salidas, "por_defecto", lambda: "Altavoces (Realtek)")
    puestas = []
    monkeypatch.setattr(app.mez, "poner_salida", lambda nombre="", extra=None: puestas.append((nombre, extra)), raising=False)
    app.cfg["salida_sonido"] = app.cfg["salida_extra"] = ""
    assert "la de Windows, ahora Altavoces" in menus_juego._salida_txt(app)
    menus_juego._cambiar_salida(app, "salida_sonido", 1)
    assert app.cfg["salida_sonido"] == "Altavoces (Realtek)" and puestas[-1][0] == "Altavoces (Realtek)"
    menus_juego._cambiar_salida(app, "salida_sonido", 1)
    assert app.cfg["salida_sonido"] == "CABLE Input (VB-Audio)"
    menus_juego._cambiar_salida(app, "salida_sonido", 1)
    assert app.cfg["salida_sonido"] == ""                    # y vuelta a la de Windows
    # la segunda no ofrece la que ya suena
    menus_juego._cambiar_salida(app, "salida_extra", 1)
    assert app.cfg["salida_extra"] == "CABLE Input (VB-Audio)" and puestas[-1][1] == "CABLE Input (VB-Audio)"
    assert "CABLE Input" in menus_juego._salida_extra_txt(app)
    menus_juego._cambiar_salida(app, "salida_extra", 1)
    assert app.cfg["salida_extra"] == "" and "ninguna" in menus_juego._salida_extra_txt(app)
    monkeypatch.setattr(salidas, "presente", lambda nombre: False)
    app.cfg["salida_sonido"] = "Auriculares USB"
    assert "desconectada" in menus_juego._salida_txt(app)
    app.cfg["salida_sonido"] = ""


def test_los_nombres_cortos_de_windows_casan_con_los_largos():
    assert salidas.coincide("Altavoces (Realtek(R) Audio)", "OpenAL Soft on Altavoces (Realtek(R) Audio)")
    assert salidas.coincide("Auriculares (2- Arctis 7 Game", "Auriculares (2- Arctis 7 Game Audio)")
    assert not salidas.coincide("Altavoces", "CABLE Input (VB-Audio Virtual Cable)")
    assert not salidas.coincide("", "Altavoces")


def test_el_sonido_vuelve_a_abrirse_si_se_corta_o_cambia_la_de_windows(monkeypatch):
    from juego.audio import Mezclador
    m = Mezclador(dispositivo=False)
    motivos = []
    defecto = ["Altavoces"]
    monkeypatch.setattr(salidas, "por_defecto", lambda: defecto[0])
    monkeypatch.setattr(salidas, "presente", lambda nombre: True)
    m.reabrir = lambda motivo="": motivos.append(motivo) or True
    m.con_dispositivo, m.stream, m._t_cb, m._t_vigila = True, object(), 100.0, 0.0
    try:
        assert not m.vigilar(ahora=100.5)                    # todo bien: nada
        defecto[0] = "Auriculares"
        m._t_cb = 102.0
        assert m.vigilar(ahora=102.5) and motivos[-1] == "ha cambiado la de Windows"
        assert not m.vigilar(ahora=103.0)                    # no se mira más que cada poco
        assert m.vigilar(ahora=110.0) and motivos[-1] == "se ha cortado"
        m.stream = None
        assert m.vigilar(ahora=120.0) and motivos[-1] == "sin salida"
    finally:
        m.con_dispositivo, m.stream = False, None
        m.cerrar()


# ============================================================ la comunidad de jugadores (issue 25)
def test_la_comunidad_de_jugadores_avisa_que_no_es_oficial_y_lista_sus_sitios(robot, monkeypatch):
    from juego import comunidad, menus_juego as mj
    app = robot.app
    principal = app.pila[-1]
    textos = [o.texto for o in principal.opciones]
    i = textos.index("Comunidad de jugadores, no oficial")
    assert textos[i - 1] == "Abrir el manual" and textos[i + 1] == "Acerca de"
    abiertos = []
    monkeypatch.setattr(comunidad.os, "startfile", lambda url: abiertos.append(url), raising=False)
    servidores = list(app.cfg["servidores"])
    try:
        comunidad.menu(app)
        m = app.pila[-1]
        assert isinstance(m, Menu) and "no oficial" in m.titulo
        assert "no es oficial" in m.opciones[0].texto and "no se hace responsable" in m.opciones[1].texto
        d = comunidad.cargar()
        assert [s["id"] for s in d["secciones"]] == ["comunicacion", "foros", "servidores", "aprender", "otros"]
        tele = d["secciones"][0]["enlaces"]
        assert {e["idioma"] for e in tele} == {"inglés", "español"} and all(e["url"].startswith("https://t.me/") for e in tele)
        # cada sección, con cuántos sitios tiene; un enlace se abre en el navegador
        op = next(o for o in m.opciones if o.texto.startswith("Comunicación"))
        assert op.texto.endswith(": 2")
        op.accion()
        sub = app.pila[-1]
        assert sub.opciones[0].texto.endswith(", en inglés")
        sub.opciones[0].accion()
        assert abiertos == [tele[0]["url"]] and "Abriendo" in robot.dicho()
        app.cerrar(sub)
        # un servidor se añade a tu lista, una sola vez
        next(o for o in m.opciones if o.texto.startswith("Servidores")).accion()
        sv = app.pila[-1].opciones[0]
        assert "godeano" in sv.texto and "puertobravo://godeano.vip:47820" in sv.ayuda
        app.cfg["servidores"] = [x for x in servidores if "godeano" not in x.get("dir", "")]
        sv.accion()
        assert any(x["dir"] == "puertobravo://godeano.vip:47820" for x in app.cfg["servidores"])
        n = len(app.cfg["servidores"])
        sv.accion()
        assert len(app.cfg["servidores"]) == n and "ya está en tu lista" in robot.dicho()
        app.cerrar(app.pila[-1])
        # una sección vacía lo dice, y cómo apuntar algo
        next(o for o in m.opciones if o.texto.startswith("Otros recursos")).accion()
        assert app.pila[-1].opciones[0].texto == "Todavía no hay nada aquí"
    finally:
        app.cfg["servidores"] = servidores
        while app.pila[-1] is not principal:
            app.cerrar(app.pila[-1])


def test_los_objetos_de_coleccion_ya_no_suben_la_fama(robot):
    """Issue 28: la fama subía a quien jugaba limpio solo por ir encontrando objetos de colección."""
    p = robot.nueva_partida()
    j = p.j
    assert p.total_casetes() > 5
    j.casetes = [f"x{k}" for k in range(4)]
    j.reputacion, dinero = 10.0, j.dinero
    o = Objeto("casete", "Cinta", *p.pos())
    o.tag = "x4"
    p.objetos.append(o)
    p.recoger(o)
    assert len(j.casetes) == 5 and j.reputacion == 10.0 and j.dinero > dinero
    assert "Un coleccionista te adelanta" in robot.dicho()


def test_la_comunidad_se_lee_tambien_protegida_como_en_el_juego_compilado(tmp_path, monkeypatch):
    """En la 1.7.4 compilada solo salía el aviso: el archivo va protegido (comunidad.pbd) y se leía como .json."""
    import json
    import os
    from juego import cifrado, comunidad, rutas
    with open(os.path.join(rutas.DATOS, "comunidad.json"), encoding="utf-8") as f:
        original = json.load(f)
    with open(tmp_path / ("comunidad" + rutas.EXT_DATOS), "wb") as f:
        f.write(cifrado.cifrar(original))
    monkeypatch.setattr(rutas, "DATOS", str(tmp_path))
    assert not (tmp_path / "comunidad.json").exists()
    d = comunidad.cargar()
    assert [s["id"] for s in d["secciones"]] == ["comunicacion", "foros", "servidores", "aprender", "otros"]
    assert d["responsabilidad"] and sum(len(s["enlaces"]) for s in d["secciones"]) >= 5
