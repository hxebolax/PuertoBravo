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
        assert L.ritmo_de("Lucía", 1) in L.RITMOS and len({L.ritmo_de("Lucía", d) for d in range(3)}) == 3      # cambia de un día a otro
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
            assert isinstance(m, Menu) and not m.escapable
            robot.tecla(pygame.K_ESCAPE)
            assert app.pila[-1] is m                                          # de la escena no se sale a medias
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
        assert [o.texto for o in m.opciones] == ["Parar, y preguntarle si está bien", "Bajar el ritmo sin decir nada"]
        robot.tecla(pygame.K_RETURN)
        assert n.puntos == 1.0 and "Paras." in app.pila[-1].titulo
        _cerrar_todo(app, p)
        # no escuchar: sintonía baja
        resultado.clear()
        n = L.Noche(p, "Lucía", "tu casa", resultado.append, azar=random.Random(1))
        n.ritmo = "lento"
        n.empezar()
        for _ in range(14):
            m = app.pila[-1]
            if isinstance(m, Dialogo):
                break
            m.i = 1 if len(m.opciones) == 2 else next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Besarle antes", "Abrazarle fuerte", "Con prisa"))), 1)
            robot.tecla(pygame.K_RETURN)
        robot.saltar_dialogos()
        assert resultado and resultado[0] < 0.5
        # en el juego: la noche por pasos da más o menos ánimo según cómo haya ido; con la opción quitada, va como antes
        animo = p.j.animo = 30.0
        p.encuentro("Lucía", "romantico", "tu casa")
        assert isinstance(app.pila[-1], Menu)
        robot.saltar_dialogos()
        assert p.j.animo > animo and p.j.stats.get("noches", 0) == 1
        app.cfg["noche_por_pasos"] = False
        p.encuentro("Lucía", "romantico", "tu casa")
        assert isinstance(app.pila[-1], Dialogo)
        robot.saltar_dialogos()
        assert p.j.stats["noches"] == 2
        # nada de lo que se dice es explícito
        todo = " ".join(t for t, ops in L.MOMENTOS for t in [t] + [o[0] + o[2] for o in ops]).lower()
        for palabra in ("sexo", "desnud", "pene", "vagina", "pezon", "orgasm", "follar", "penetr"):
            assert palabra not in todo
    finally:
        app.cfg["adultos"] = False
        app.cfg["noche_por_pasos"] = True


# ============================================================ las escenas privadas (escenas_privadas.py)
import contextlib


@contextlib.contextmanager
def _escenas(robot, por_pasos=False):
    """Una partida con el contenido para adultos y las escenas privadas; deja las opciones como venían."""
    p = robot.nueva_partida()
    cfg = p.cfg
    antes = {k: cfg[k] for k in ("adultos", "escenas_directas", "noche_por_pasos", "pareja_familiar")}
    cfg["adultos"], cfg["escenas_directas"], cfg["noche_por_pasos"] = True, True, por_pasos
    try:
        yield p
    finally:
        _cerrar_todo(p.app, p)
        for k, v in antes.items():
            cfg[k] = v


def _opcion(app, texto):
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(texto))
    app.inyectar(pygame.K_RETURN, 0, "")


def test_ritmo_habitual_se_suma_al_del_dia(robot):
    from juego import laboratorio as L
    p = robot.nueva_partida()
    assert len({L.ritmo_de("Lucía", d) for d in range(3)}) == 3                # el del día sigue cambiando
    lucia = p.persona_social("lucia")
    assert lucia["ritmo"] in L.RITMOS and lucia["despedida"]
    try:
        for habitual, puntos in (("jugando", 0.6), (None, 0.4)):
            n = L.Noche(p, "Lucía", "tu casa", lambda s: None, azar=random.Random(1), habitual=habitual)
            n.ritmo = "intenso"
            n.empezar()
            n._elegir("jugando", "{n} se ríe.")
            assert n.puntos == puntos
            _cerrar_todo(p.app, p)
    finally:
        _cerrar_todo(p.app, p)


def test_escenas_privadas_no_se_repiten_y_un_no_es_un_no(robot):
    import json
    from juego.escenas_privadas import escena_de
    from juego.config import POR_DEFECTO
    assert not POR_DEFECTO["escenas_directas"]                                 # de serie, apagadas
    with _escenas(robot) as p:
        app = p.app
        assert p.encuentro("Alguien", "romantico", "tu casa", perfil={"edad": 17}) is False and app.pila[-1] is p
        for tipo in ("romantico", "tranquilo"):
            banco = escena_de(p, tipo)["escenas"]
            vistas = set()
            for i in range(len(banco)):
                assert p.encuentro("Lucía", tipo, "tu casa", pid="lucia")
                titulo = app.pila[-1].titulo
                entrada = next(e for e, _ in banco if e.replace("{n}", "Lucía") in titulo)
                assert entrada not in vistas
                vistas.add(entrada)
                robot.tecla(pygame.K_ESCAPE)                                    # decir que no: no pasa nada
                assert app.pila[-1] is p
                if i == 1:                                                      # la rueda se guarda con la partida
                    p.cargar_dict(json.loads(json.dumps(p.a_dict())))
            assert len(vistas) == len(banco)
        assert not p.j.stats.get("noches")


def test_escena_privada_cura_va_al_historial_y_escape_no_la_anula(robot):
    with _escenas(robot) as p:
        app, j = p.app, p.j
        j.intimos["preservativos"] = 3
        j.salud, j.animo = 30, 30.0
        relatos = next(x["relatos"] for x in p.datos["relatos_privados"] if x["id"] == "lucia")
        p.encuentro("Lucía", "tranquilo", "tu casa", pid="lucia")
        _opcion(app, "Decir que sí")
        assert any(inicio in app.pila[-1].titulo for inicio, _ in relatos)       # el momento a solas es uno de sus relatos
        _opcion(app, "Quedaros cerca")
        assert isinstance(app.pila[-1], Dialogo) and j.stats["noches"] == 1
        assert j.salud == j.salud_max and j.intimos["preservativos"] == 2      # pasar la noche cura, como siempre
        assert p.persona_social("lucia")["despedida"][:30] in robot.dicho()
        robot.tecla(pygame.K_ESCAPE)                                            # saltar el texto no deshace la noche
        assert app.pila[-1] is p and j.stats["noches"] == 1 and j.animo > 30
        despedida = p.persona_social("lucia")["despedida"][:30]
        assert any(despedida in x for x in app.voz.historial)                  # la escena se puede repasar con Re Pág


def test_noche_descriptiva_paso_a_paso_con_pausa_y_sin_escape(robot):
    with _escenas(robot, por_pasos=True) as p:
        app, j = p.app, p.j
        j.intimos["preservativos"] = 3
        afinidad = p.relacion("andres")["afinidad"]
        p.encuentro("Andrés", "romantico", "un hotel", pid="andres")
        assert app.pila[-1].opciones[0].texto == "Hablar de lo que quiere cada uno"
        _opcion(app, "Decir que sí")
        _opcion(app, "Decir lo que")
        paso = app.pila[-1]
        assert isinstance(paso, Menu) and not paso.escapable and any(o.texto == "Pedir una pausa" for o in paso.opciones)
        robot.tecla(pygame.K_ESCAPE)
        assert app.pila[-1] is paso                                             # de la noche no se sale con Escape
        _opcion(app, "Pedir una pausa")
        _opcion(app, "Volver cuando")
        assert app.pila[-1] is paso
        for _ in range(12):
            m = app.pila[-1]
            if isinstance(m, Dialogo):
                break
            m.i = next((k for k, o in enumerate(m.opciones) if o.texto.startswith(("Preguntar", "Parar"))), 0)
            robot.tecla(pygame.K_RETURN)
        assert isinstance(app.pila[-1], Dialogo) and j.stats["noches"] == 1
        assert p.relacion("andres")["afinidad"] > afinidad
        robot.tecla(pygame.K_ESCAPE)
        assert app.pila[-1] is p and j.stats["noches"] == 1


def test_noche_paso_a_paso_escape_en_la_narracion_cuenta(robot):
    p = robot.nueva_partida()
    app = p.app
    app.cfg["adultos"], app.cfg["noche_por_pasos"] = True, True
    try:
        p.j.salud = 25
        p.encuentro("Lucía", "romantico", "tu casa", pid="lucia")
        for _ in range(12):
            m = app.pila[-1]
            if isinstance(m, Dialogo):
                break
            m.i = 0
            robot.tecla(pygame.K_RETURN)
        assert isinstance(app.pila[-1], Dialogo) and not p.j.stats.get("noches")
        robot.tecla(pygame.K_ESCAPE)                                            # Escape salta el texto, el resultado cuenta
        while isinstance(app.pila[-1], Dialogo):
            robot.tecla(pygame.K_ESCAPE)
        assert p.j.stats["noches"] == 1 and p.j.salud == p.j.salud_max
    finally:
        _cerrar_todo(app, p)
        app.cfg["adultos"] = False


def test_aventura_en_hotel_se_cobra_al_empezar_y_usa_los_relatos_de_su_caracter(robot):
    from juego.charla import ficha
    from juego.entidades import Persona
    with _escenas(robot) as p:
        app = p.app
        q = Persona("civil", *p.pos())
        p.personas.append(q)
        f = ficha(q)
        f.update(confianza=95, interes=True, calabazas=False, caracter="seco", edad=30)
        p.j.dinero = dinero = 1000
        p.j.intimos["preservativos"] = 2
        assert p.proponer_aventura(q, en_hotel=True)
        assert p.j.dinero == dinero - p.precio("hotel_cita", 70)               # el hotel, al empezar, como siempre
        _opcion(app, "Decir que sí")
        relatos = next(x["relatos"] for x in p.datos["relatos_privados"] if x["id"] == "seco")
        assert any(inicio.replace("{n}", f["nombre"]) in app.pila[-1].titulo for inicio, _ in relatos)
        robot.tecla(pygame.K_ESCAPE)                                            # lo dejáis: el hotel no se devuelve
        assert app.pila[-1] is p and p.j.dinero == dinero - p.precio("hotel_cita", 70)


def test_modo_familiar_sin_coquetear(robot):
    from juego import menus_charla
    from juego.entidades import Persona
    p = robot.nueva_partida()
    cfg = p.cfg
    antes = cfg["adultos"], cfg["pareja_familiar"]
    cfg["adultos"], cfg["pareja_familiar"] = False, True
    try:
        q = Persona("civil", *p.pos())
        menus_charla.conversar(p, q)
        textos = [o.texto for o in p.app.pila[-1].opciones]
        assert "Coquetear" not in textos and not any(t.startswith("Proponerle ir") for t in textos)
    finally:
        _cerrar_todo(p.app, p)
        cfg["adultos"], cfg["pareja_familiar"] = antes


def test_un_mod_anade_y_sustituye_relatos_y_escenas(monkeypatch, tmp_path):
    import json
    import os
    from juego import mundo as M, rutas
    mod = {"relatos_privados": [{"id": "lucia", "relatos": [["Relato del mod con {n}.", "Y sigue."]]},
                                {"id": "persona_del_mod", "relatos": [["Otro relato.", "Fin."]]}],
           "escenas_privadas": [{"id": "romantico", "escenas": [["Entrada del mod.", "Final del mod."]]}],
           "acuerdos_privados": [{"id": "del_mod", "texto": "¿Seguimos, {n}?"}],
           "personas": [{"id": "lucia", "nombre": "Lucía", "edad": 29, "lugar": "chiringuito", "desc": "x", "ritmo": "lento", "despedida": "Adiós del mod."}]}
    with open(os.path.join(tmp_path, "relatos.json"), "w", encoding="utf-8") as fh:
        json.dump(mod, fh)
    monkeypatch.setattr(rutas, "MODS", str(tmp_path))
    d = M.cargar_datos(traducir=False)
    relatos = {x["id"]: x["relatos"] for x in d["relatos_privados"]}
    assert relatos["lucia"] == [["Relato del mod con {n}.", "Y sigue."]] and "persona_del_mod" in relatos and "andres" in relatos
    escenas = {x["id"]: x for x in d["escenas_privadas"]}
    assert escenas["romantico"]["escenas"] == [["Entrada del mod.", "Final del mod."]] and len(escenas["tranquilo"]["escenas"]) > 1
    assert any(a["id"] == "del_mod" for a in d["acuerdos_privados"]) and len(d["acuerdos_privados"]) > 1
    lucia = next(x for x in d["adultos"]["personas"] if x["id"] == "lucia")
    assert lucia["ritmo"] == "lento" and lucia["despedida"] == "Adiós del mod."


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
