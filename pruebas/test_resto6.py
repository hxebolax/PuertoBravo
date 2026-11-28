"""Contenido para adultos que ahora se juega: la noche paso a paso y el laboratorio."""
import random

import pygame

from juego.menus import Dialogo, Menu


def _cerrar_todo(app, p):
    while app.pila[-1] is not p:
        app.cerrar(app.pila[-1])


def test_la_noche_paso_a_paso(robot):
    from juego import laboratorio as L
    p = robot.nueva_partida()
    app = robot.app
    app.cfg["adultos"] = True
    try:
        perfil = {"afinidad": 42}
        assert L.ritmo_preferido(perfil, "jugando", random.Random(0)) == "jugando"
        assert L.ritmo_preferido(perfil, "intenso", random.Random(7)) == "jugando"
        assert perfil["afinidad"] == 42
        for texto, opciones in L.MOMENTOS:
            assert len(opciones) == 3
        # escuchar y acertar: sintonía alta
        resultado = []
        n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
        n.ritmo = "lento"
        n.empezar()
        for _ in range(12):
            m = app.pila[-1]
            if isinstance(m, Dialogo):
                break
            assert isinstance(m, Menu) and m.escapable
            m.i = next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Poner música", "Acariciarle despacio", "Preguntarle", "Ir despacio"))), 0)
            robot.tecla(pygame.K_RETURN)
        assert isinstance(app.pila[-1], Dialogo) and "Se apaga la luz" in app.voz.registro[-1]
        robot.tecla(pygame.K_RETURN)                                          # la segunda frase: cómo ha ido
        robot.tecla(pygame.K_RETURN)
        assert resultado and resultado[0] >= 0.99
        texto = " ".join(app.voz.registro[-14:])
        assert "Despacio. Hoy quiero que dure." in texto and "se recuerdan" in texto
        # ir más deprisa de lo que quiere: te pide que esperes, y parar a preguntar es lo que vale
        resultado.clear()
        n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
        n.ritmo = "lento"
        n.empezar()
        m = app.pila[-1]
        m.i = 1                                                               # besarle antes de que diga nada
        robot.tecla(pygame.K_RETURN)
        m = app.pila[-1]
        assert "Espera" in m.titulo or "Un momento" in m.titulo
        assert [o.texto for o in m.opciones] == ["Parar, y preguntarle si está bien", "Mejor otro día", "Volver"]
        robot.tecla(pygame.K_RETURN)
        assert n.puntos == 0.0 and "Paras." in app.pila[-1].titulo
        _cerrar_todo(app, p)
        # Escape abandona cada decisión y el diálogo final sin consumir recursos.
        for etapa in range(5):
            resultado.clear()
            n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
            n.ritmo = "lento"
            n.empezar()
            for _ in range(etapa):
                robot.tecla(pygame.K_RETURN)
            robot.tecla(pygame.K_ESCAPE)
            assert app.pila[-1] is p and not resultado
        animo = p.j.animo = 30.0
        p.encuentro("Lucía", "romantico", "tu casa")
        robot.tecla(pygame.K_ESCAPE)
        assert p.j.animo == animo and not p.j.stats.get("noches")
        p.j.salud = 37
        app.cfg["noche_por_pasos"] = False
        p.encuentro("Lucía", "romantico", "tu casa")
        assert isinstance(app.pila[-1], Dialogo)
        robot.saltar_dialogos()
        assert p.j.stats["noches"] == 1 and p.j.salud == 37 and p.j.animo > animo
        # nada de lo que se dice es explícito
        todo = " ".join(t for t, ops in L.MOMENTOS for t in [t] + [o[0] + o[2] for o in ops]).lower()
        for palabra in ("sexo", "desnud", "pene", "vagina", "pezon", "orgasm", "follar", "penetr"):
            assert palabra not in todo
    finally:
        app.cfg["adultos"] = False
        app.cfg["noche_por_pasos"] = True


def test_escenas_privadas_consentimiento_rotacion_y_guardado(robot):
    import json
    p = robot.nueva_partida()
    app = p.app
    assert not p.cfg["escenas_directas"]
    assert not p.encuentro("Lucía", "romantico", "tu casa", pid="lucia")
    from juego import menus_juego
    menus_juego.opciones(app)
    next(o for o in app.pila[-1].opciones if o.texto == "Contenido para adultos").accion()
    opcion = next(o for o in app.pila[-1].opciones if o.texto.startswith("Escenas privadas"))
    opcion.ajuste(1)
    assert not p.cfg["escenas_directas"]
    _cerrar_todo(app, p)
    p.cfg["adultos"] = p.cfg["escenas_directas"] = True
    p.j.intimos["preservativos"] = 1
    assert not p.encuentro("Alguien", "romantico", "tu casa", perfil={"edad": 17})
    for tipo, banco in p.datos["escenas_privadas"].items():
        titulos = set()
        for i in range(len(banco) * 8):
            assert p.encuentro("Lucía", tipo, "tu casa", pid="lucia")
            titulo = app.pila[-1].titulo
            assert titulo in app._subtitulo() and titulo not in app.voz.ultimo()
            assert titulo not in titulos
            titulos.add(titulo)
            robot.tecla(pygame.K_ESCAPE)
            if i == 2:
                p.cargar_dict(json.loads(json.dumps(p.a_dict())))
        assert len(titulos) == 48
    assert not p.j.stats.get("noches") and p.j.intimos["preservativos"] == 1
    p.encuentro("Lucía", "romantico", "tu casa", pid="lucia")
    robot.tecla(pygame.K_RETURN)
    assert "límites" in app.pila[-1].titulo
    p.cfg["adultos"] = False
    app.aplicar_adultos()
    assert app.pila[-1] is p and not p.cfg["escenas_directas"] and not p.j.stats.get("noches")
    p.cfg["adultos"] = p.cfg["escenas_directas"] = True
    p.cfg["noche_por_pasos"] = False
    p.encuentro("Lucía", "romantico", "tu casa", pid="lucia")
    robot.tecla(pygame.K_RETURN)
    assert isinstance(app.pila[-1], Menu)
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_DOWN)
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is p and p.j.intimos["preservativos"] == 1 and not p.j.stats.get("noches")
    p.encuentro("Lucía", "romantico", "tu casa", pid="lucia")
    robot.tecla(pygame.K_RETURN)
    robot.tecla(pygame.K_RETURN)
    assert isinstance(app.pila[-1], Dialogo) and app.pila[-1].escena_privada
    assert p.j.stats["noches"] == 1 and p.j.intimos["preservativos"] == 0
    robot.saltar_dialogos()
    for _ in range(48):
        p.encuentro("Lucía", "romantico", "tu casa", pid="lucia")
        if "preservativo" in app.pila[-1].titulo.lower():
            robot.tecla(pygame.K_RETURN)
            break
        robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is p and p.j.stats["noches"] == 1


def test_intro_lee_la_despedida_de_cada_escena_en_ingles(robot, monkeypatch):
    from juego import i18n, mundo
    p = robot.nueva_partida()
    app = p.app
    idioma = i18n.actual()
    monkeypatch.delenv("PUERTOBRAVO_IDIOMA", raising=False)
    try:
        i18n.cargar("en")
        traducidos = mundo.cargar_datos()
        p.datos["escenas_privadas"] = traducidos["escenas_privadas"]
        p.datos["relatos_privados"] = traducidos["relatos_privados"]
        p.cfg["adultos"] = p.cfg["escenas_directas"] = True
        p.j.intimos["preservativos"] = 24
        for tipo, banco in p.datos["escenas_privadas"].items():
            for i in range(len(banco)):
                p.cfg["noche_por_pasos"] = bool(i % 2)
                assert p.encuentro("Lucía", tipo, "hotel", pid="lucia")
                menu = app.pila[-1]
                final = next(fin for entrada, fin in banco if entrada.format(n="Lucía") in menu.titulo)
                if p.cfg["noche_por_pasos"]:
                    robot.tecla(pygame.K_RETURN)
                robot.tecla(pygame.K_RETURN)
                assert isinstance(app.pila[-1], Menu)
                assert any(app.pila[-1].titulo == inicio for inicio, _ in p.datos["relatos_privados"]["lucia"])
                if i % 2:
                    momento = app.pila[-1].titulo
                    robot.tecla(pygame.K_DOWN)
                    robot.tecla(pygame.K_DOWN)
                    robot.tecla(pygame.K_RETURN)
                    assert "whether you’d like to continue" in app._subtitulo()
                    robot.tecla(pygame.K_RETURN)
                    assert app.pila[-1].titulo == momento
                    robot.tecla(pygame.K_DOWN)
                robot.tecla(pygame.K_RETURN)
                if i % 2:
                    assert "listens until you finish" in app._subtitulo()
                    for paso in range(4):
                        assert app.pila[-1].escena_privada
                        if paso == 1:
                            momento = app.pila[-1].titulo
                            for _ in range(3):
                                robot.tecla(pygame.K_DOWN)
                            robot.tecla(pygame.K_RETURN)
                            robot.tecla(pygame.K_RETURN)
                            assert app.pila[-1].titulo == momento
                            robot.tecla(pygame.K_HOME)
                        robot.tecla(pygame.K_RETURN)
                escena = app.pila[-1]
                assert ("Lucía brushes the hair" if i % 2 else "You hold each other") in app._subtitulo()
                assert "You were careful." in app._subtitulo()
                robot.tecla(pygame.K_RETURN)
                robot.frames(3)
                from juego.escenas_privadas import despues
                assert app._subtitulo() == despues(tipo).format(n="Lucía")
                robot.tecla(pygame.K_RETURN)
                robot.frames(3)
                assert app.pila[-1] is escena and app._subtitulo() == final.format(n="Lucía")
                assert app.voz.registro[-1] == app._subtitulo()
                robot.tecla(pygame.K_RETURN)
                assert app.pila[-1] is p
    finally:
        i18n.cargar(idioma)


def test_espera_en_noche_descriptiva(robot):
    p = robot.nueva_partida()
    p.cfg["adultos"] = p.cfg["escenas_directas"] = p.cfg["noche_por_pasos"] = True
    p.j.intimos["preservativos"] = 1
    afinidad = p.relacion("andres")["afinidad"]
    for terminar in (False, True):
        assert p.encuentro("Andrés", "romantico", "hotel", pid="andres")
        robot.tecla(pygame.K_DOWN)  # aceptar la invitación
        robot.tecla(pygame.K_RETURN)
        robot.tecla(pygame.K_RETURN)
        robot.tecla(pygame.K_DOWN)  # beso, más deprisa de lo que quiere
        robot.tecla(pygame.K_RETURN)
        menu = p.app.pila[-1]
        assert menu.escena_privada and menu.opciones[0].texto == "Parar, y preguntarle si está bien"
        assert p.relacion("andres")["afinidad"] == afinidad
        assert not p.j.stats.get("noches") and p.j.intimos["preservativos"] == 1
        if not terminar:
            robot.tecla(pygame.K_ESCAPE)
            assert p.app.pila[-1] is p
        else:
            robot.tecla(pygame.K_RETURN)
            assert "Despacio" in p.app._subtitulo()
            for _ in range(3):
                robot.tecla(pygame.K_RETURN)
            assert p.j.stats["noches"] == 1 and p.j.intimos["preservativos"] == 0
            assert p.relacion("andres")["afinidad"] > afinidad


def test_relatos_privados_por_persona_y_caracter(robot):
    import json

    p = robot.nueva_partida()
    p.cfg["adultos"] = p.cfg["escenas_directas"] = True
    p.cfg["noche_por_pasos"] = False
    p.j.intimos["preservativos"] = 50
    personas = {q["id"]: q for q in p.datos["adultos"]["personas"]}
    for clave, relatos in p.datos["relatos_privados"].items():
        pid = clave if clave in personas else None
        perfil = personas.get(clave, {"edad": 32, "caracter": clave, "nombre": clave.title()})
        nombre = perfil["nombre"]
        vistos = set()
        for i in range(len(relatos)):
            assert p.encuentro(nombre, "tranquilo", "hotel", pid=pid, perfil=perfil)
            robot.tecla(pygame.K_RETURN)
            momento = p.app.pila[-1].titulo
            inicio, fin = next((a, b) for a, b in relatos if a.format(n=nombre) in momento)
            assert inicio not in vistos
            vistos.add(inicio)
            robot.tecla(pygame.K_RETURN)
            assert fin.format(n=nombre) in p.app._subtitulo()
            robot.saltar_dialogos()
            if i == 0:
                p.cargar_dict(json.loads(json.dumps(p.a_dict())))


class Fijo:
    """Un azar que no se mueve: la deriva siempre hacia arriba y ningún suceso."""

    def __init__(self, tiro=0.99):
        self.tiro = tiro

    def choice(self, lista):
        return lista[-1]

    def random(self):
        return self.tiro

    def uniform(self, a, b):
        return a


def test_laboratorio(robot):
    from juego import laboratorio as L, menus_adultos, menus_juego
    p = robot.nueva_partida()
    app = robot.app
    j = p.j
    casa = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and l.id != "casa_abuela")
    j.propiedades.append(casa.id)
    j.dinero = 50000
    assert L.opciones_casa(p, casa, Menu, menus_juego.Opcion) == []           # sin el contenido para adultos no existe
    app.cfg["adultos"] = True
    app.aplicar_adultos()
    try:
        ops = L.opciones_casa(p, casa, Menu, menus_juego.Opcion)
        assert len(ops) == 1 and ops[0].texto.startswith("Montar un laboratorio")
        ops[0].accion()
        assert casa.id in j.laboratorios and j.dinero == 50000 - L.PRECIO_LAB
        # el material se compra en los proveedores
        o = L.opcion_proveedor(p, menus_juego.Opcion)
        o.accion()
        o.accion()
        assert j.material == 2 and "Tienes 2" in o.texto
        prov = p.lugares.get("trastienda")
        if prov is not None:
            p.teletransportar(prov.x, prov.y)
            menus_adultos.proveedor(p, prov)
            assert any(x.texto.startswith("Material de laboratorio") for x in app.pila[-1].opciones)
            _cerrar_todo(app, p)
        # sin material no se trabaja
        cristal = next(s for s in p.dato_adulto("sustancias") if s["id"] == "cristal")
        # una tanda bien llevada: corriges la deriva y sacas muchas unidades
        j.material = 1
        c = L.Coccion(p, casa, cristal, azar=Fijo())
        app.abrir(c)
        for _ in range(int(L.DURA * 30) + 5):
            if c.hecho:
                break
            (app.teclas.add if c.valor < -0.05 else app.teclas.discard)(pygame.K_UP)
            (app.teclas.add if c.valor > 0.05 else app.teclas.discard)(pygame.K_DOWN)
            app.paso(1 / 30)
        app.teclas.clear()
        assert c.hecho and c.bien > 0.8 * L.DURA and j.sustancias.get("cristal", 0) >= 14 and "Una tanda limpia" in robot.dicho()
        assert app.pila[-1] is p and j.stats["fabricado"] >= 14
        # dejarlo irse arriba: arde, pierdes el laboratorio y viene la policía
        c = L.Coccion(p, casa, cristal, azar=Fijo(0.0))
        c.deriva = 0.4
        app.abrir(c)
        salud = j.salud
        for _ in range(int(L.DURA * 30) + 5):
            if c.hecho:
                break
            c.deriva = 0.4
            app.paso(1 / 30)
        assert c.hecho and casa.id not in j.laboratorios and j.salud < salud and "arde" in robot.dicho() and (j.puntos_busqueda > 0 or j.estrellas > 0)
        # abandonar con Escape echa a perder la tanda
        j.laboratorios.append(casa.id)
        antes = j.sustancias.get("cristal", 0)
        c = L.Coccion(p, casa, cristal, azar=Fijo())
        app.abrir(c)
        robot.tecla(pygame.K_ESCAPE)
        assert c.hecho and j.sustancias.get("cristal", 0) == antes and "a medias" in app.voz.registro[-1]
        # está en el menú de la casa, y se guarda con la partida
        j.material = 3
        p.teletransportar(casa.x, casa.y)
        menus_juego._casa(p, casa)
        assert any(o.texto == "Entrar en el laboratorio" for o in app.pila[-1].opciones)
        _cerrar_todo(app, p)
        d = p.a_dict()
        app.empezar_partida(d)
        assert app.partida.j.laboratorios == [casa.id] and app.partida.j.material == 3
    finally:
        app.cfg["adultos"] = False
        app.aplicar_adultos()
