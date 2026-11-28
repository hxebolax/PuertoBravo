"""Dominó, chinos, más decisiones, nadar y bucear, tren y tranvía, avioneta y los sonidos nuevos en todos los packs."""
import json
import os
import random

import pygame

from juego.menus import Menu, Opcion


def _cerrar(app, p):
    while app.pila[-1] is not p:
        app.cerrar(app.pila[-1])


def test_domino(robot):
    from juego import mesa
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    assert len(mesa._fichas()) == 28 and mesa._nombre((3, 3)) == "3 doble" and mesa._nombre((2, 5)) == "5 2" and mesa._puntos([(6, 6), (0, 1)]) == 13
    # una partida entera jugada por las reglas: siempre termina y el dinero cuadra
    for semilla in range(6):
        j.dinero = 1000
        m, est = mesa.domino(p, Menu, Opcion, azar=random.Random(semilla))
        m.i = 0                                                              # 20 euros
        robot.tecla(pygame.K_RETURN)
        assert not est["fin"] and len(est["yo"]) == 7 and len(est["rival"]) == 7 and len(est["pozo"]) == 14
        for _ in range(120):
            if est["fin"]:
                break
            m.refrescar(False)
            jugada = next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Poner el", "Robar una ficha"))), None)
            assert jugada is not None, [o.texto for o in m.opciones]         # nunca te quedas sin nada que hacer
            m.i = jugada
            robot.tecla(pygame.K_RETURN)
            todas = est["yo"] + est["rival"] + est["pozo"]
            assert len(todas) == len(set(todas)) and len(todas) <= 28        # ninguna ficha se duplica
        assert est["fin"], semilla
        assert j.dinero in (980, 1000, 1020), (semilla, j.dinero)            # pierdes, empatas o ganas
        assert any(x in app.voz.registro[-1] for x in ("Ganas", "Pierdes", "Empate"))
        app.cerrar(m)
    # las fichas que se ofrecen casan de verdad con un extremo
    m, est = mesa.domino(p, Menu, Opcion, azar=random.Random(3))
    m.i = 0
    robot.tecla(pygame.K_RETURN)
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Poner el"))
    robot.tecla(pygame.K_RETURN)
    if not est["fin"]:
        m.refrescar(False)
        for o in m.opciones:
            if o.texto.startswith("Poner el"):
                assert f"junto al {est['izq']}" in o.texto or f"junto al {est['der']}" in o.texto
    app.cerrar(m)


def test_chinos_y_juegos_en_los_bares(robot):
    from juego import menus_juego, mesa, sistemas

    class Azar:
        def __init__(self, suyas, suyo):
            self.suyas, self.suyo = suyas, suyo

        def randint(self, a, b):
            return self.suyas

        def choice(self, lista):
            return self.suyo if self.suyo in lista else lista[0]
    p = robot.nueva_partida()
    app = robot.app
    j = p.j

    def jugar(mias, digo, suyas, suyo):
        j.dinero = 500
        m, est = mesa.chinos(p, Menu, Opcion, azar=Azar(suyas, suyo))
        m.i = 0                                                              # 10 euros
        robot.tecla(pygame.K_RETURN)
        m.i = mias
        robot.tecla(pygame.K_RETURN)
        m.i = next(k for k, o in enumerate(m.opciones) if o.texto == f"Decir {digo}")
        robot.tecla(pygame.K_RETURN)
        fase = est["fase"]
        app.cerrar(m)
        return j.dinero, fase
    assert jugar(2, 3, 1, 2) == (510, "apuesta") and "Aciertas" in app.voz.registro[-1]
    assert jugar(2, 4, 1, 3) == (490, "apuesta") and "Acierta tu rival" in app.voz.registro[-1]
    assert jugar(2, 5, 0, 3) == (490, "esconder") and "No acierta nadie" in app.voz.registro[-1]      # se repite con la misma apuesta
    # en el menú de un bar están todos los juegos, una sola vez, y se abren
    bar = p.lugares["bar_gaviota"]
    p.teletransportar(bar.x, bar.y)
    menus_juego.lugar(p, bar)
    m = app.pila[-1]
    m.refrescar(False)
    textos = [o.texto for o in m.opciones]
    for t in ("Jugar a la siete y media", "Jugar al dominó", "Jugar a los chinos", "Echar unas monedas a la tragaperras", "Recorrer el local por dentro"):
        assert textos.count(t) == 1, t
    for t, titulo in (("Jugar al dominó", "Dominó"), ("Jugar a los chinos", "Los chinos"), ("Echar unas monedas a la tragaperras", "")):
        m.i = textos.index(t)
        robot.tecla(pygame.K_RETURN)
        assert app.pila[-1] is not m and (not titulo or app.pila[-1].titulo.startswith(titulo))
        app.cerrar(app.pila[-1])
    # y la máquina del rincón del bar, recorriéndolo, se puede usar
    loc = sistemas.Local(p, bar)
    assert any(h[2] == "tragaperras" for h in loc.habitaciones)


def test_mas_decisiones_en_la_historia_y_en_los_mods(robot):
    p = robot.nueva_partida()
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    claves = set()
    con = [i for i, m in por_id.items() if any(x["tipo"] == "decision" for x in m["pasos"])]
    for ident in ("m04", "m09", "m12", "e03", "v03", "x03", "s04", "fd1", "cdo1", "voo1", "pao1", "ivo1", "nno1", "ocs6"):
        assert ident in con, ident
        m = por_id[ident]
        k = next(n for n, x in enumerate(m["pasos"]) if x["tipo"] == "decision")
        d = m["pasos"][k]
        assert d["clave"] not in claves and 2 <= len(d["opciones"]) <= 4 and d["pregunta"].endswith("?")
        claves.add(d["clave"])
        for o in d["opciones"]:
            assert o["texto"] and o["ayuda"] and o["dice"]
            assert not o.get("banda") or o["banda"] in ("Los Calaveras", "Los Lagartos", "Los Barrenos", "Los Tiburones", "Los Cuervos")
        if ident != "fd1":
            assert k == len(m["pasos"]) - 2 and m["pasos"][-1]["tipo"] == "dialogo"       # justo antes de la escena final
    assert len(con) >= 14
    # una de ellas, jugada: no cobrar al proveedor da fama y no dinero
    m04 = por_id["m04"]
    p.cfg["sucesos"] = False
    p.mision = {"def": m04, "paso": len(m04["pasos"]) - 3, "veh": None, "enemigos": [], "objeto": None, "limite": None, "generado": False, "recogido": False,
                "restos": None, "avisos": set(), "quedan": None, "copia": p.j.a_dict(), "reloj": p.reloj, "dia": p.dia}
    dinero, fama = p.j.dinero, p.j.reputacion
    p._siguiente_paso()
    menu = robot.app.pila[-1]
    assert isinstance(menu, Menu) and not menu.escapable and menu.opciones[0].texto == "No cobrarle nada"
    robot.tecla(pygame.K_RETURN)
    assert p.decisiones["morosos"]["opcion"] == 1 and p.j.dinero == dinero and p.j.reputacion == fama + 2


def test_nadar_y_bucear(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    mar = next(m for m in p.mapas.values() if m.tipo == "mar")
    muelle = next(l for l in mar.lugares.values() if l.get("a_mapa") in p.mapas and p.lug(l.get("a_lugar")))
    # en barco: F te tira al agua y el barco se queda
    p.cambiar_mapa(mar.id, muelle.x + 120, muelle.y + 120)
    v = p.crear_vehiculo("lancha", j.x, j.y, 0, None)
    p._subir(v, False, callar=True)
    robot.frames(3)
    robot.tecla(pygame.K_f)
    assert j.veh is None and p.nadando and v in p.vehiculos and "Estás en el agua" in robot.dicho()
    # nadar: se avanza despacio, se oyen las brazadas y se gastan fuerzas
    sonidos = []
    original = p.son
    p.son = lambda n, **k: (sonidos.append(n), original(n, **k))[1]
    x0, fuerzas = j.x, p.aguante
    robot.frames(90, mantener=(pygame.K_RIGHT,))
    p.son = original
    assert 3 < j.x - x0 < 8 and "brazada" in sonidos and p.aguante < fuerzas and p.mundo.id == mar.id
    robot.tecla(pygame.K_v)
    assert "Estás nadando" in app.voz.registro[-1]
    # bucear: suena el fondo, se gasta el aire, y al acabarse subes a la fuerza
    robot.tecla(pygame.K_x)
    assert p.buceando and p.agua_canal is not None and p.agua_canal.nombre == "bajo_agua" and not j.agachado
    aire = p.aire
    robot.frames(60)
    assert p.aire < aire - 5
    robot.tecla(pygame.K_x)
    assert not p.buceando and p.agua_canal is None and "Sales a la superficie" in app.voz.registro[-1]
    robot.frames(30 * 4)
    assert p.aire > aire - 5 or p.aire > 60                                   # en la superficie se recupera
    robot.tecla(pygame.K_x)
    p.aire = 0.5
    salud = j.salud
    robot.frames(10)
    assert not p.buceando and j.salud < salud
    # volver al barco con F
    j.x, j.y = v.x + 2, v.y
    robot.tecla(pygame.K_f)
    assert j.veh is v and not p.nadando
    # llegar nadando a un muelle te saca a tierra
    robot.tecla(pygame.K_f)
    assert p.nadando
    j.x, j.y = muelle.x + 5, muelle.y
    robot.frames(3)
    assert p.mundo.id != mar.id and not p.nadando and "Llegas nadando" in robot.dicho()
    # quedarte sin fuerzas: te rescatan, como en un naufragio
    p.cambiar_mapa(mar.id, muelle.x + 150, muelle.y + 150)
    robot.frames(2)
    assert p.nadando
    p.aguante = 0.2
    robot.frames(30)
    assert p.mundo.id != mar.id and not p.nadando and "medio ahogado" in robot.dicho()


def test_avioneta(robot):
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    modelo = p.modelos["avioneta"]
    assert modelo["vuela"] and modelo["motor"] == "motor_avioneta" and modelo["vel_max"] > p.modelos["helicoptero"]["vel_max"]
    a = p.crear_vehiculo("avioneta", j.x, j.y, 0, None)
    p._subir(a, False, callar=True)
    robot.frames(5)
    assert j.veh is a and a.canal is not None and a.canal.nombre == "motor_avioneta" and app.mez.altura > 0


def test_sonidos_nuevos_en_todos_los_packs():
    from juego import ayuda, catalogo_sonidos as cat, rutas, sintesis
    nuevos = ("tren", "tren_silbato", "tranvia", "tranvia_campana", "motor_avioneta", "bajo_agua", "brazada", "avion", "avion_despegue",
              "lugar_tranvia", "lugar_tren", "lugar_aeropuerto")
    base = os.path.dirname(rutas.carpeta_sonidos()) if os.path.basename(rutas.carpeta_sonidos()) == "por_defecto" else os.path.join(rutas.DATA, "sonidos")
    cuentas = {}
    for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
        archivos = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(base, pack)) if f.lower().endswith((".wav", ".ogg", ".flac", ".mp3"))}
        cuentas[pack] = len(archivos)
        for n in nuevos:
            assert n in archivos, (pack, n)
    assert len(set(cuentas.values())) == 1 and cuentas["por_defecto"] == 284, cuentas       # todos los packs, los mismos archivos
    # en los packs de grabaciones son grabaciones de verdad, no el sonido de serie
    for n in ("lugar_tranvia", "lugar_tren", "lugar_aeropuerto"):                 # las firmas de los lugares son las de serie en todos los packs
        assert open(os.path.join(base, "por_defecto", n + ".flac"), "rb").read() == open(os.path.join(base, "realista", n + ".flac"), "rb").read()
    for n in ("tren", "tranvia", "bajo_agua", "avion", "avion_despegue"):
        serie = open(os.path.join(base, "por_defecto", n + ".flac"), "rb").read()
        assert open(os.path.join(base, "realista", n + ".flac"), "rb").read() != serie
    creditos = open(os.path.join(base, "realista", "CREDITOS.txt"), encoding="utf-8-sig").read()
    assert "Freesound" in creditos and "tren.flac" in creditos
    # están en el catálogo, con descripción, y en Aprender los sonidos
    grupos = ("Barcos, helicópteros, tren, tranvía y avión", "Moverse a pie y nadar", "Sonidos de los lugares")
    for n in nuevos:
        assert cat.describir(n) != "Sonido del juego.", n
        assert cat.titulo_de(n) in grupos and (not n.startswith("lugar_") or cat.titulo_de(n) == grupos[2])
    aprendidos = {s for s, _, _ in ayuda.SONIDOS}
    assert set(nuevos) <= aprendidos
    assert sintesis.es_bucle("tren") and sintesis.es_bucle("tranvia") and sintesis.es_bucle("bajo_agua") and sintesis.es_bucle("avion") and not sintesis.es_bucle("brazada")
    doc = open(os.path.join(rutas.DATA, "docs", "cambiar_sonidos_es.html"), encoding="utf-8").read()
    for n in nuevos:
        assert f"<code>{n}</code>" in doc, n
