"""Contenido para adultos, música de ambiente y opciones por secciones."""
import random

import pygame

from juego import menus_adultos, menus_juego
from juego.menus import Dialogo, Menu


def _activar(robot):
    robot.app.cfg["noche_por_pasos"] = False             # aquí se prueba la noche contada; la noche paso a paso tiene su propia prueba
    robot.app.cfg["adultos"] = True
    robot.app.aplicar_adultos()


def _elegir(robot, texto):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), robot.dicho()
    for k, o in enumerate(m.opciones):
        if texto.lower() in o.texto.lower():
            m.i = k
            robot.tecla(pygame.K_RETURN)
            return
    raise AssertionError(f"no hay opción «{texto}» en {[o.texto for o in m.opciones]}")


def test_oculto_por_defecto_y_activacion(robot):
    app = robot.app
    p = robot.nueva_partida()
    assert not p.modo_adulto()
    assert "club_paraiso" not in p.lugares and "trastienda" not in app.mundo.lugares
    assert all(not m.get("adultos") for m in p.misiones_disponibles())
    menus_juego.movil(p)
    assert not any("Vida social" in o.texto or "Sustancias" in o.texto for o in app.pila[-1].opciones)
    robot.tecla(pygame.K_ESCAPE)
    # activar pide confirmar la edad
    menus_adultos.alternar_modo(app)
    assert "18" in app.pila[-1].titulo
    _elegir(robot, "No, dejarlo")
    assert not app.cfg["adultos"]
    menus_adultos.alternar_modo(app)
    _elegir(robot, "Sí, soy mayor")
    assert app.cfg["adultos"] and "club_paraiso" in p.lugares and "trastienda" in app.mundo.lugares
    menus_juego.movil(p)
    assert any("Vida social" in o.texto for o in app.pila[-1].opciones)
    robot.tecla(pygame.K_ESCAPE)
    menus_adultos.alternar_modo(app)
    assert not app.cfg["adultos"] and "club_paraiso" not in p.lugares


def test_opciones_por_secciones_con_volver(robot):
    app = robot.app
    menus_juego.opciones(app)
    raiz = app.pila[-1]
    textos = [o.texto for o in raiz.opciones]
    assert textos[-1] == "Volver" and len(textos) == 19 and textos[-2] == "Restablecer todas las opciones de serie" and "Mods: activar o desactivar" in textos and "Partidas guardadas" in textos and textos[0].startswith("Idioma: ") and "Teclado: cambiar las teclas" in textos and "Registro para informar de fallos" in textos and "Personas e inteligencia artificial" in textos and "Actualizaciones" in textos
    for k in range(1, len(textos) - 2):                 # la primera, Idioma, se cambia con las flechas: no abre nada; la penúltima, restablecer, pregunta
        raiz.i = k
        robot.tecla(pygame.K_RETURN)
        sub = app.pila[-1]
        assert sub is not raiz, textos[k]
        assert isinstance(sub, Menu) and len(sub.opciones) >= 2
        if textos[k] != "Mando":
            assert sub.opciones[-1].texto == "Volver", textos[k]
            sub.i = len(sub.opciones) - 1
            robot.tecla(pygame.K_RETURN)
        else:
            robot.tecla(pygame.K_ESCAPE)
        assert app.pila[-1] is raiz
    # restablecer: pregunta, con «No» no cambia nada, y con «Sí» todo vuelve a como viene, menos lo que es tuyo
    from juego import config
    app.cfg["vol_maestro"], app.cfg["dia_semana"], app.cfg["servidores"] = 0.3, "numero", [{"nombre": "x"}]
    raiz.i = len(textos) - 2
    robot.tecla(pygame.K_RETURN)
    pregunta = app.pila[-1]
    assert pregunta is not raiz and pregunta.opciones[0].texto.startswith("No")
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is raiz and app.cfg["vol_maestro"] == 0.3
    robot.tecla(pygame.K_RETURN)
    app.pila[-1].i = 1
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is raiz and app.cfg["vol_maestro"] == config.POR_DEFECTO["vol_maestro"] and app.cfg["dia_semana"] == "ambos"
    assert app.cfg["servidores"] == [{"nombre": "x"}]
    app.cfg["servidores"] = []
    raiz.i = len(textos) - 1
    robot.tecla(pygame.K_RETURN)
    assert raiz not in app.pila


def test_musica_de_ambiente_cede_ante_la_radio(robot):
    app = robot.app
    app.ambiente.esperar()
    app.radio.esperar()
    robot.frames(5)
    assert app.ambiente.actual == "menu"
    p = robot.nueva_partida()
    p.reloj = 12 * 60
    robot.frames(10)
    app.ambiente.esperar_carga()                  # la pieza se lee en segundo plano
    robot.frames(120)
    assert app.ambiente.actual == "exploracion" and app.ambiente.volumen_actual() > 0.1
    assert all(len(v) >= 3 for v in app.ambiente.pistas.values())
    primera = app.ambiente.pista
    app.ambiente.t_pista = 0.0                    # la pieza se acaba: entra otra distinta de la misma situación
    robot.frames(3)
    assert app.ambiente.pista != primera and app.ambiente.actual == "exploracion"
    vistas = set()
    for _ in range(40):                           # el menú no empieza siempre por la misma
        app.ambiente.actual = None
        app.ambiente.ultima = {}
        app.ambiente.actualizar(0.01, "menu", 0.5)
        vistas.add(app.ambiente.pista)
    assert len(vistas) >= 3
    robot.frames(200)
    p.poner_busqueda(1)
    robot.frames(5)
    assert app.ambiente.actual == "tension"
    p._fin_persecucion()
    p.reloj = 23 * 60
    robot.frames(5)
    assert app.ambiente.actual == "noche"
    # al subir a un coche con la radio puesta, la música de ambiente se calla
    app.cfg["emisora"] = 1
    x, y, d = p.mundo.plaza_junto_a(p.lugares["hospital"])
    v = p.crear_vehiculo("sedan", x, y, d, None)
    p._subir(v, False, callar=True)
    robot.frames(5)
    app.radio.esperar()                           # la canción de la emisora se lee en segundo plano
    robot.frames(120)
    assert app.radio.canal is not None and app.ambiente.actual is None and not app.ambiente.canales
    # apagar la radio la devuelve
    robot.tecla(pygame.K_r, mod=pygame.KMOD_SHIFT)
    robot.frames(60)
    assert app.radio.canal is None and app.ambiente.actual == "noche"
    robot.tecla(pygame.K_r)
    robot.frames(5)
    assert app.ambiente.actual is None
    v.vel = 0
    robot.tecla(pygame.K_f)
    robot.frames(5)
    assert app.ambiente.actual == "noche"
    app.cfg["musica_ambiente"] = False
    robot.frames(90)
    assert not app.ambiente.canales


def test_relaciones(robot):
    random.seed(3)
    p = robot.nueva_partida()
    _activar(robot)
    p.cfg["vida_en_persona"] = False                 # el modo de antes, todo desde el móvil; el de ahora lo prueba test_172
    j = p.j
    j.dinero = 5000
    l = p.lugares["chiringuito"]
    j.x, j.y = l.x, l.y
    robot.frames(15)
    menus_adultos.vida_social(p)
    _elegir(robot, "Presentarte a Lucía")
    assert "lucia" in j.relaciones
    _elegir(robot, "Charlar")
    a0 = j.relaciones["lucia"]["afinidad"]
    _elegir(robot, "Charlar")                       # solo una vez al día
    assert j.relaciones["lucia"]["afinidad"] == a0
    for dia in range(12):
        p.dia += 1
        _elegir(robot, "Proponer una cita")
        _elegir(robot, "Dar un paseo")              # su plan favorito
        robot.saltar_dialogos()                     # la cita se cuenta en escenas
        while "Cita con" in getattr(robot.app.pila[-1], "titulo", ""):
            robot.tecla(pygame.K_ESCAPE)
        _elegir(robot, "Hacerle un regalo")
        _elegir(robot, "ramo de flores")
        robot.tecla(pygame.K_ESCAPE)
    assert j.relaciones["lucia"]["afinidad"] >= 60
    _elegir(robot, "Pedirle que sea tu pareja")
    assert j.pareja == "lucia" and j.relaciones["lucia"]["estado"] == "pareja"
    p.dia += 1
    j.animo = animo = 50.0
    robot.app.pila[-1].refrescar(False)
    _elegir(robot, "Pasar la noche juntos")
    assert "La noche con Lucía" in robot.app.pila[-1].titulo            # se elige cómo
    _elegir(robot, "noche romántica")
    assert isinstance(robot.app.pila[-1], Dialogo) and "noche romántica con Lucía" in robot.dicho()
    robot.saltar_dialogos()
    assert j.animo > animo and j.salud == j.salud_max and j.stats["noches"] == 1
    # descuidar la relación la rompe
    for _ in range(40):
        p.dia += 1
        p.dia_adultos()
    assert j.pareja == "" and j.relaciones["lucia"]["estado"] == "ex"


def test_celos_y_club(robot):
    p = robot.nueva_partida()
    _activar(robot)
    j = p.j
    j.dinero = 100000
    r = p.relacion("lucia")
    r.update(estado="pareja", afinidad=90)
    j.pareja = "lucia"
    club = p.lugares["club_paraiso"]
    j.x, j.y = club.x, club.y
    robot.frames(15)
    descubierto = False
    for semilla in range(40):
        random.seed(semilla)
        p._fin_persecucion()
        robot.tecla(pygame.K_RETURN)
        _elegir(robot, "Pagar por compañía")
        robot.saltar_dialogos()
        assert robot.app.pila[-1] is p
        if j.pareja == "" or j.relaciones["lucia"]["afinidad"] < 90:
            descubierto = True
            break
    assert descubierto and j.stats["pagos"] >= 1 and "puerta se cierra" in " ".join(robot.app.voz.registro)


def test_sustancias_adiccion_y_sobredosis(robot):
    p = robot.nueva_partida()
    _activar(robot)
    j = p.j
    j.dinero = 5000
    j.sustancias["polvo"] = 10
    base_v, base_p = p.mod_velocidad(), p.mod_punteria()
    p.consumir("polvo")
    assert p.mod_velocidad() > base_v and p.mod_punteria() > base_p and j.sustancias["polvo"] == 9
    robot.frames(30 * 95)                    # se pasa el efecto y llega el bajón
    assert any(e.get("bajon") for e in j.efectos) and p.mod_punteria() < base_p and "bajón" in " ".join(robot.app.voz.registro)
    robot.frames(30 * 125)
    assert not j.efectos and robot.app.mez.tono_mundo == 1.0
    # alcohol: tambaleo
    p.consumir("alcohol", de_inventario=False)
    assert p.deriva() > 0
    j.efectos = []
    # adicción y abstinencia
    for _ in range(6):
        j.efectos = []
        p.consumir("polvo")
    assert j.adiccion["polvo"] >= 40 and not p._abstinencia()
    j.efectos = []
    p.dia += 2
    assert p._abstinencia() and p.mod_dano() > 1.0
    animo = j.animo
    p.dia_adultos()
    assert j.animo < animo
    # desintoxicación en el hospital
    h = p.lugares["hospital"]
    j.x, j.y = h.x, h.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Desintoxicación")
    assert not j.adiccion and not p._abstinencia()
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    # sobredosis: tres dosis seguidas
    j.sustancias["polvo"] = 5
    for _ in range(3):
        p.consumir("polvo")
    assert isinstance(robot.app.pila[-1], Dialogo) and j.stats["sobredosis"] == 1
    robot.saltar_dialogos()
    assert robot.app.pila[-1] is p and not j.efectos


def test_trapicheo(robot):
    p = robot.nueva_partida()
    _activar(robot)
    j = p.j
    j.dinero = 20000
    barato = p.lugares["vs_cultivo"]          # la hierba se cultiva en Villaseca
    caro = p.lugares["trastienda"]
    medias = []
    for l in (barato, caro):
        precios = []
        for d in range(1, 40):
            p.dia = d
            precios.append(p.precio_sustancia("hierba", l)[0])
        medias.append(sum(precios) / len(precios))
    assert medias[0] < medias[1] * 0.7
    # comprar en el proveedor
    j.x, j.y = caro.x, caro.y
    robot.frames(15)
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Hierba")
    _elegir(robot, "Comprar 10")
    assert j.sustancias["hierba"] == 10 and j.dinero < 20000
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    assert p.carga() == 10
    # vender en la calle con la tecla E, sin arma en la mano
    from juego.entidades import Persona
    vendido = poli = False
    for semilla in range(60):
        random.seed(semilla)
        p._fin_persecucion()
        c = Persona("civil", j.x + 1, j.y)
        c.estado = "quieto"
        p.personas.append(c)
        antes = j.sustancias.get("hierba", 0)
        robot.tecla(pygame.K_e)
        robot.frames(2)
        vendido = vendido or j.sustancias.get("hierba", 0) < antes
        poli = poli or j.estrellas >= 2
        if c in p.personas:
            p.personas.remove(c)
        if j.sustancias.get("hierba", 0) == 0:
            j.sustancias["hierba"] = 10
    assert vendido and poli and j.stats.get("vendido", 0) > 0
    # si te detienen, lo pierdes todo
    p._fin_persecucion()
    j.sustancias["hierba"] = 20
    p.detener()
    robot.saltar_dialogos()
    assert p.carga() == 0


def test_misiones_para_adultos(robot):
    import test_misiones
    p = robot.nueva_partida()
    _activar(robot)
    for previa in ("m01", "m02", "m03", "m04", "m05", "x01"):
        p.completadas.append(previa)
    for ident in ("a01", "a02", "a03"):
        m = next(m for m in p.datos["misiones"] if m["id"] == ident)
        assert m in p.misiones_disponibles(), ident
        test_misiones._jugar_mision(robot, m)
        robot.saltar_dialogos()
        p._fin_persecucion()
    assert p.j.sustancias.get("hierba") == 10 and p.j.relaciones["lucia"]["afinidad"] >= 25


def test_contacto_de_calle_e_invitacion_sobreviven_al_guardado(robot, monkeypatch):
    import json
    import random
    from juego import encuentros
    from juego.charla import ficha
    from juego.entidades import Persona

    p = robot.nueva_partida()
    p.cfg["adultos"] = False
    p.cfg["pareja_familiar"] = True
    p.cfg["atraccion"] = "todos"
    p.cfg["mi_genero"] = "x"
    monkeypatch.setitem(encuentros.AJ.n, "invitacion_pct", 100)
    persona = Persona("civil", *p.pos())
    f = ficha(persona)
    f.update(confianza=45, disponible=True, le_atraen="hm", interes=True, calabazas=True)
    assert not p.intercambiar_numero(persona)                     # te dijo que no: no hay número
    f["calabazas"] = False
    assert p.intercambiar_numero(persona) and p.intercambiar_numero(persona)
    pid = f["contacto_id"]
    assert sum(x["id"] == pid for x in p.dato_adulto("personas")) == 1
    perfil = p.persona_social(pid).copy()
    assert perfil["edad"] >= 18 and not p.lug(perfil["lugar"]).d.get("adultos")
    r = p.relacion(pid)
    r.update(afinidad=48, ultimo=p.dia)
    p.dia += 2
    p.reloj = 8 * 60
    encuentros.invitacion_diaria(p, random.Random(1))
    plan = r["invitacion"].copy()
    encuentros.invitacion_diaria(p, random.Random(1))
    assert not p.j.quedadas and r["invitacion"] == plan            # una sola invitación a la vez

    p.cargar_dict(json.loads(json.dumps(p.a_dict())))
    assert p.persona_social(pid) == perfil and p.relacion(pid)["invitacion"] == plan
    encuentros.responder_invitacion(p, perfil, True)
    encuentros.responder_invitacion(p, perfil, True)
    assert len(p.j.quedadas) == 1 and p.j.quedadas[0]["con"] == pid
    assert p.j.quedadas[0]["min"] == plan["min"] and p.j.quedadas[0]["act"] in perfil["gustos"]
    p.en_servidor = True
    try:
        otra = Persona("civil", *p.pos())
        ficha(otra).update(confianza=45, disponible=True, le_atraen="hm", interes=True)
        assert not p.intercambiar_numero(otra)                    # en un servidor, no
    finally:
        p.en_servidor = False
