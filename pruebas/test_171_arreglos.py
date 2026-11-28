"""Lo de la 1.7.1 que sale del repaso del foro: combates deportivos, ayuda y mostrador de los locales, tablones, barrios que dicen
de quién son, avisos que faltaban, la carpeta de mi música y la ficha de las armas."""
import json
import os
import random

import pygame

from juego import combate, menus_juego, sistemas
from juego.entidades import Persona
from juego.menus import Menu


def _tecla(robot, k, mod=0):
    robot.app.pila[-1].tecla(pygame.event.Event(pygame.KEYDOWN, key=k, mod=mod, unicode=""))


def _testigo(p):
    x, y = p.pos()
    t = Persona("civil", x + 6, y, "Vecina")
    t.estado = "quieto"
    p.personas.append(t)
    return t


def _gimnasio(p):
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "gimnasio")
    p.teletransportar(l.x, l.y)
    return l


# ------------------------------------------------------------------ combates deportivos
def test_los_rivales_del_gimnasio_no_son_delito(robot):
    p = robot.nueva_partida()
    assert all(c.get("deportivo") is True for c in p.datos["combates"])          # boxeo y velada, marcados en los datos
    l = _gimnasio(p)
    _testigo(p)
    # control: en las mismas condiciones, tumbar a un enemigo cualquiera sí cuenta
    malo = Persona("enemigo", l.x + 2, l.y, "Matón")
    p.personas.append(malo)
    prestigio = p.j.ciudadania
    p.danar_persona(malo, 500)
    assert p.j.puntos_busqueda > 0 and p.j.ciudadania < prestigio
    p.j.puntos_busqueda, p.j.estrellas, p.j.ciudadania = 0.0, 0, prestigio
    p.objetos[:] = [o for o in p.objetos if o.tipo != "dinero"]
    for ident, asaltos in (("boxeo", 1), ("mma", 3)):
        p.empezar_combate(l, p.combate_def(ident))
        for _ in range(asaltos):
            robot.frames(5)
            _testigo(p)
            rivales = [e for e in p.mision["enemigos"] if not e.muerto]
            assert len(rivales) == 1 and rivales[0].deportivo
            p.danar_persona(rivales[0], 5000)
            robot.frames(5)
        robot.saltar_dialogos()
        assert p.j.stats.get(ident) == 1, robot.dicho()
    assert p.j.puntos_busqueda == 0 and p.j.estrellas == 0 and p.j.ciudadania == prestigio
    assert any(f in robot.dicho() for f in combate.RIVAL_CAE)
    assert not any(o.tipo == "dinero" and o.nombre == "Dinero en el suelo" for o in p.objetos)      # un rival no suelta la cartera


def test_un_mod_puede_poner_peleas_que_si_son_delito(robot):
    p = robot.nueva_partida()
    l = _gimnasio(p)
    _testigo(p)
    # sin la marca, un combate de mod es deportivo; con «no», es una pelea ilegal
    p.empezar_combate(l, {"id": "lucha", "nombre": "Lucha", "rivales": ["el Roble"]})
    robot.frames(5)
    assert p.mision["enemigos"][0].deportivo
    p.abandonar_mision()
    _testigo(p)                                                      # el deportivo se pelea en el pabellón: al volver, la calle es otra
    p.empezar_combate(l, {"id": "clandestina", "nombre": "Pelea clandestina", "rivales": ["el Sordo"], "deportivo": False})
    robot.frames(5)
    e = p.mision["enemigos"][0]
    assert not e.deportivo
    p.danar_persona(e, 5000)
    assert p.j.puntos_busqueda > 0
    from editor import esquema
    campo = next(c for c in esquema.ESQUEMAS["combate"]["campos"] if c["k"] == "deportivo")
    assert campo["t"] == "si_no" and campo["defecto"] is True


# ------------------------------------------------------------------ dentro de los locales
def _local(robot, tipo):
    p = robot.p
    l = next(x for x in p.lugares.values() if x.tipo == tipo and x.mapa == p.mundo.id)
    menu = Menu(robot.app, l.nombre, [])
    robot.app.abrir(menu)
    local = sistemas.Local(p, l)
    robot.app.abrir(local)
    return l, menu, local


def _ir_a(robot, local, que):
    local.i = next(k for k, h in enumerate(local.habitaciones) if h[2] == que)


def test_la_ayuda_de_un_local_no_habla_de_tu_casa(robot):
    robot.nueva_partida()
    l, menu, local = _local(robot, "comisaria")
    _tecla(robot, pygame.K_F1)
    dicho = robot.app.voz.registro[-1]
    assert "tu casa" not in dicho and l.nombre in dicho and "Escape" in dicho and "el mostrador de guardia" in dicho
    _ir_a(robot, local, "tablon_policia")
    _tecla(robot, pygame.K_F1)
    assert "lees los carteles" in robot.app.voz.registro[-1]
    local.i = 0
    _tecla(robot, pygame.K_LEFT)
    assert "Pared" in robot.app.voz.registro[-1] and "casa" not in robot.app.voz.registro[-1]
    # la casa conserva su ayuda
    casa = sistemas.Interior(robot.p, robot.p.lugares["casa_abuela"], {})
    assert "tu casa" in casa.ayuda()


def test_el_mostrador_dice_que_te_acercas_y_vuelve_al_menu(robot):
    robot.nueva_partida()
    vistos = set()
    for tipo in sistemas.SALAS:                                   # todos los locales con recorrido tienen su mostrador
        assert sum(1 for h in sistemas.SALAS[tipo] if h[2] == "mostrador") == 1, tipo
    for _ in range(12):
        l, menu, local = _local(robot, "comisaria")
        _ir_a(robot, local, "mostrador")
        _tecla(robot, pygame.K_RETURN)
        assert robot.app.pila[-1] is menu and local not in robot.app.pila
        dicho = robot.app.voz.registro[-1]
        assert "mostrador de guardia" in dicho and dicho.index("mostrador de guardia") < dicho.index(l.nombre), dicho
        assert " a el " not in dicho
        vistos.add(dicho.split("mostrador de guardia")[0])
        robot.app.cerrar(menu)
    assert len(vistos) > 1                                       # no lo dice siempre igual
    assert menu.antes is None                                    # se dice una sola vez
    # en un bar, la barra; y «a el» nunca
    l, menu, local = _local(robot, "bar")
    _ir_a(robot, local, "mostrador")
    _tecla(robot, pygame.K_RETURN)
    assert "la barra" in robot.app.voz.registro[-1]


def test_el_tablon_de_la_comisaria_dice_algo_util_y_cambia(robot):
    p = robot.nueva_partida()
    l, menu, local = _local(robot, "comisaria")
    _ir_a(robot, local, "tablon_policia")
    _tecla(robot, pygame.K_RETURN)
    assert "no te busca" in robot.app.voz.registro[-1].lower() or "no está" in robot.app.voz.registro[-1]
    textos = {sistemas.tablon_policia(p) for _ in range(25)}
    assert len(textos) > 4
    p.j.estrellas, p.j.puntos_busqueda = 2, 5.0
    p.j.stats["detenciones"] = 3
    t = sistemas.tablon_policia(p)
    assert "búsqueda de nivel 2" in t and str(p.coste_multa()) in t and "3 detenciones" in t
    p.j.estrellas = 0
    juntos = " ".join(sistemas.tablon_policia(p) for _ in range(60))
    assert "Los Calaveras" in juntos and "Recorte del periódico" in juntos       # la banda del puerto, y las noticias
    p.j.territorios.append("puerto")
    assert "Los Calaveras" not in " ".join(sistemas.tablon_policia(p) for _ in range(60))


def test_los_otros_tablones_tambien_se_leen(robot):
    p = robot.nueva_partida()
    from juego import loteria
    p.dia, p.reloj = 5, 22 * 60
    t = sistemas.tablon_premios(p)
    assert loteria.cifras(loteria.premiado(p, 5)) in t and loteria.cifras(loteria.premiado(p, 4)) in t and "Bote" in t
    t = sistemas.tablon_ofertas(p)
    assert sum(1 for x in p.datos["jornadas"] if x["nombre"] in t) == 3 and "euros" in t
    for tipo, que in (("loteria", "tablon_premios"), ("empleo", "tablon_ofertas")):
        assert any(h[2] == que for h in sistemas.SALAS[tipo])
    assert all(h[2] in sistemas.QUE_HACE for salas in sistemas.SALAS.values() for h in salas)      # la ayuda sabe explicar cada sitio


# ------------------------------------------------------------------ barrios
def test_ningun_mapa_lleva_escrito_de_quien_es_el_barrio():
    from juego import rutas
    carpetas = [rutas.DATOS, os.path.join(rutas.DATOS, "mapas"), rutas.MODS]
    n = 0
    for c in carpetas:
        for f in os.listdir(c):
            if f.endswith(".json"):
                d = json.load(open(os.path.join(c, f), encoding="utf-8"))
                mapas = ([d] if "barrios" in d else []) + [m for m in d.get("mapas", []) if isinstance(m, dict)] if isinstance(d, dict) else []
                for m in mapas:
                    for b in m.get("barrios", []):
                        n += 1
                        assert "erritorio de" not in b.get("descripcion", ""), (f, b["id"])
    assert n > 20


def test_el_barrio_dice_de_quien_es_ahora(robot):
    p = robot.nueva_partida()
    puerto = next(b for b in p.mundo.barrios if b["id"] == "puerto")
    otro = next(b for b in p.mundo.barrios if not b.get("banda"))
    assert puerto["banda"] == "Los Calaveras" and p.barrio_dueno_txt(otro) == ""
    assert p.barrio_desc(puerto).endswith("Territorio de la banda de Los Calaveras.")
    # la tecla N lo dice
    sitios = [(l.x + dx, l.y + dy) for l in p.mundo.lugares.values() for dx in (-30, 30) for dy in (-30, 30)]
    x, y = next((x, y) for x, y in sitios if p.mundo.barrio(x, y)["id"] == "puerto" and p.mundo.transitable(x, y)
                and not any(abs(l.x - x) + abs(l.y - y) < 40 for l in p.mundo.lugares.values()))
    p.teletransportar(x, y)
    assert p.mundo.barrio(*p.pos())["id"] == "puerto" and not p.lugar_cercano(16)
    _tecla(robot, pygame.K_n)
    assert "Territorio de la banda de Los Calaveras" in robot.app.voz.registro[-1]
    # en guerra: lo estás conquistando
    p.empezar_conquista(puerto)
    assert p.mision["def"]["banda"] == "Los Calaveras"                    # se pelea contra quien manda allí
    assert p.barrio_dueno_txt(puerto) == "En guerra: se lo estás disputando a Los Calaveras."
    p.abandonar_mision()
    # tuyo
    p.j.territorios.append("puerto")
    assert p.barrio_dueno_txt(puerto) == "Territorio tuyo."
    p.j.banda_nombre = "Los Gavilanes"
    assert "Los Gavilanes" in p.barrio_dueno_txt(puerto) and "Calaveras" not in p.barrio_desc(puerto)
    # te lo atacan
    p.j.amenaza = {"territorio": "puerto", "banda": "Los Cuervos", "dia": p.dia}
    assert p.barrio_dueno_txt(puerto) == "En guerra: es territorio tuyo, pero Los Cuervos lo está atacando."
    # no lo defiendes: pasa a ser de quien te lo quitó, y se guarda con la partida
    p.dia += 1
    sistemas.sucesos_territorio(p, random.Random(1))
    assert "puerto" not in p.j.territorios
    assert p.barrio_dueno_txt(puerto) == "Territorio de la banda de Los Cuervos."
    d = json.loads(json.dumps(p.j.a_dict(), default=str))
    assert d["barrios_banda"] == {"puerto": "Los Cuervos"}
    # y el menú de barrios del móvil lo dice igual, también para otra ciudad
    marina = next(b for b in p.mapas["san_lucero"].barrios if b["id"] == "sl_marina")
    assert p.barrio_desc(marina, p.mapas["san_lucero"]).endswith("Territorio de la banda de Los Lagartos.")
    from editor import esquema
    assert any(c["k"] == "banda" for c in esquema.ESQUEMAS["barrio"]["campos"])


# ------------------------------------------------------------------ lo que no se encontraba
def test_el_desvio_dice_siempre_como_se_cancela(robot):
    p = robot.nueva_partida()
    x, y = p.pos()
    p.fijar_gps(x + 200, y + 100, "el destino de antes")
    p.radar_lista = [("un portal", x + 40, y, None)]              # algo que no se mueve
    p.radar_idx = 0
    p.baliza_radar()
    assert "Desvío a un portal" in robot.dicho() and "Mayúsculas G" in robot.app.voz.registro[-1]
    p.cancelar_gps(hablar=True)
    assert p.gps["nombre"] == "el destino de antes"


def test_la_primera_vez_que_te_disparan_en_un_vehiculo_se_recuerda_como_responder(robot):
    p = robot.nueva_partida()
    x, y, d = p.plaza_cercana()
    v = p.crear_vehiculo("sedan", x, y, d, None)
    p.j.x, p.j.y = x + 2, y
    p._subir(v, False, callar=True)
    p.j.salud_max = p.j.salud = 100000.0

    def tiroteo():
        e = Persona("enemigo", x + 12, y, "Pistolero")
        e.arma, e.hostil, e.estado, e.activo, e.t_disparo = "pistola", True, "ataca", True, 0.1
        p.personas.append(e)
        antes = len(robot.app.voz.registro)
        robot.frames(90)
        e.muerto = True
        return " | ".join(robot.app.voz.registro[antes:])
    dicho = tiroteo()
    assert "Control para disparar desde el vehículo" in dicho and "Q para fijar" in dicho
    assert p.j.recordado.count("disparo_veh") == 1                               # (desde la tanda 4 se recuerda también la defensa propia)
    assert "Control para disparar desde el vehículo" not in tiroteo()            # solo la primera vez
    assert "disparo_veh" in p.j.a_dict()["recordado"]                            # y se guarda con la partida


def test_abrir_la_carpeta_de_mi_musica(robot, tmp_path, monkeypatch):
    app = robot.app
    carpeta = tmp_path / "radio" / "mi_musica"
    monkeypatch.setattr(app.radio, "usuario", str(carpeta))
    abiertas = []
    monkeypatch.setattr(os, "startfile", lambda r: abiertas.append(r), raising=False)
    # la emisora vacía lo explica con palabras, sin nombres de carpetas con guion bajo
    i = next(k for k, e in enumerate(app.radio.emisoras) if e["id"] == "usuario")
    t = app.radio.sintonizar(i)
    assert "mi_musica" not in t and "Abrir la carpeta de mi música" in t and "Opciones" in t
    app.radio.apagar()
    menus_juego.opciones(app)
    seccion = app.pila[-1]
    seccion.i = next(k for k, o in enumerate(seccion.opciones) if o.texto.startswith("Sonido"))
    robot.tecla(pygame.K_RETURN)
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Abrir la carpeta de mi música"))
    assert "está vacía" in m.opciones[m.i].texto and "mp3" in m.opciones[m.i].ayuda
    robot.tecla(pygame.K_RETURN)
    assert abiertas == [str(carpeta)] and carpeta.is_dir()                       # la crea si falta
    assert "Explorador" in robot.app.voz.registro[-1]
    (carpeta / "una.mp3").write_bytes(b"x")
    (carpeta / "notas.txt").write_bytes(b"x")
    m.refrescar(False)
    assert "tiene una canción" in m.opciones[m.i].texto


# ------------------------------------------------------------------ armas
def test_la_ficha_de_cada_arma_con_palabras_y_cifras(robot):
    p = robot.nueva_partida()
    d = p.armas_d
    f = combate.ficha_arma(d["pistola"])
    assert "Daño medio: 25 puntos por bala" in f and "Alcance medio: 35 metros" in f and "un disparo cada 0,4 segundos" in f and "acierta 85 de cada cien" in f
    assert "Cargador de 12 balas" in f and "Hace ruido" in f
    assert "cuerpo a cuerpo, 2,5 metros" in combate.ficha_arma(d["navaja"]) and "por golpe" in combate.ficha_arma(d["navaja"])
    assert "automática" in combate.ficha_arma(d["subfusil"]) and "disparos por segundo" in combate.ficha_arma(d["subfusil"])
    assert "La explosión alcanza 8 metros" in combate.ficha_arma(d["granada"]) and "Precisión" not in combate.ficha_arma(d["granada"])
    assert "No hace ruido" in combate.ficha_arma(d["silenciada"]) and "cada segundo" in combate.ficha_arma(d["escopeta"])
    for a in p.datos["armas"]:                                    # todas, también las que añada un mod: sin puntos decimales ni errores
        t = combate.ficha_arma(a)
        assert "Daño" in t and "Cadencia" in t and not any(c.isdigit() and t[k + 1:k + 2] == "." and t[k + 2:k + 3].isdigit() for k, c in enumerate(t))
    assert combate.ficha_arma({"tipo": "fuego"})                  # un arma de mod a medio hacer no rompe el menú
    # en la armería, cada arma dice daño y alcance, y F1 da la ficha entera
    arm = next(l for l in p.lugares.values() if l.tipo == "armeria")
    menus_juego._armeria(p, arm)
    m = robot.app.pila[-1]
    o = next(o for o in m.opciones if o.texto.startswith("Revólver"))
    assert "Daño 48, alcance 40 metros" in o.texto and "Cadencia" in o.ayuda and d["revolver"]["desc"] in o.ayuda
    robot.app.cerrar(m)
    # y en la lista de tus armas
    p.dar_arma("rifle", 10)
    menus_juego.menu_armas(p)
    m = robot.app.pila[-1]
    assert "daño, alcance, cadencia y precisión" in robot.app.voz.registro[-1]
    o = next(o for o in m.opciones if o.texto.startswith("Rifle"))
    assert "daño 95, alcance 90 metros" in o.texto and "Precisión muy buena" in o.ayuda
    assert "cuerpo a cuerpo" in next(o for o in m.opciones if o.texto.startswith("Puños")).texto
