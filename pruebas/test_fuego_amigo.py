"""Fuego amigo opcional, el cuidado del perro, el cobro de los negocios y los coches que ya no arden por nada."""
import pygame

from juego import sistemas
from juego.menus import Menu


def _con_perro(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    j = p.j
    j.dinero = 5000
    j.perro = "Canela"
    return p, j, p.crear_perro()


def test_con_fuego_amigo_el_perro_coge_miedo_y_se_hacen_las_paces(robot):
    p, j, d = _con_perro(robot)
    assert p.cfg["fuego_amigo"] is True                              # de serie, lo realista
    assert d in p._objetivos(True) and d not in p._objetivos(False)
    p.danar_persona(d, 30)
    assert not d.hostil and not d.muerto and j.perro_confianza == 65 and not p.perro_asustado()
    assert "Le has dado a Canela" in robot.dicho()
    p.danar_persona(d, 30)
    assert p.perro_asustado() and not d.hostil and d in p.personas   # nunca se vuelve enemigo ni desaparece
    assert "no te avisará ni buscará" in robot.dicho()
    robot.tecla(pygame.K_y)
    assert "te tiene miedo" in robot.dicho() and "olfateado" not in robot.dicho()
    # asustado no avisa de los enemigos, y te sigue de lejos
    from juego.entidades import Persona
    e = Persona("enemigo", j.x + 15, j.y, "Matón")
    e.hostil = True
    e.inofensivo = True
    p.personas.append(e)
    n = len(robot.app.voz.registro)
    robot.frames(40)
    assert not any("gruñe" in f for f in robot.app.voz.registro[n:])
    p.personas.remove(e)
    # las paces: una caricia no basta, con comida sí
    robot.tecla(pygame.K_y, pygame.KMOD_SHIFT)
    m = robot.app.pila[-1]
    assert isinstance(m, Menu) and "Canela" in m.titulo
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Acariciar"))
    robot.tecla(pygame.K_RETURN)
    assert round(j.perro_confianza) == 39 and "Todavía te tiene miedo" in robot.dicho()
    robot.tecla(pygame.K_RETURN)
    assert round(j.perro_confianza) == 39 and "Dale un momento" in robot.dicho()         # no se arregla a base de aporrear la tecla
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Dar de comer"))
    robot.tecla(pygame.K_RETURN)
    assert "No te queda pienso" in robot.dicho()
    j.objetos["pienso"] = 2
    j.perro_hambre = 80
    robot.tecla(pygame.K_RETURN)
    assert j.objetos["pienso"] == 1 and j.perro_hambre == 20 and round(j.perro_confianza) == 64 and "Habéis hecho las paces" in robot.dicho()
    robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_y)
    assert "te tiene miedo" not in robot.dicho().split("|")[-1]
    # y el tiempo también cura
    j.perro_confianza = 10
    p.pasar_perro(12 * 60)
    assert j.perro_confianza == 46


def test_sin_fuego_amigo_no_se_les_puede_apuntar_ni_herir(robot):
    p, j, d = _con_perro(robot)
    a = p.crear_aliado()
    d.x, d.y, a.x, a.y = j.x + 1, j.y, j.x - 1, j.y                  # los dos a un paso, dentro de la explosión
    p.cfg["fuego_amigo"] = False
    assert d not in p._objetivos(True) and a not in p._objetivos(True)
    salud = a.salud
    p.danar_persona(d, 50)
    p.danar_persona(a, 50)
    p._estallar({"x": j.x, "y": j.y, "radio": 12, "dano": 80})
    assert j.perro_confianza == 100 and a.salud == salud and not a.hostil and not d.hostil
    # con fuego amigo, la explosión sí les llega
    p.cfg["fuego_amigo"] = True
    p.cfg["invulnerable"] = True
    p._estallar({"x": j.x, "y": j.y, "radio": 12, "dano": 20})
    assert j.perro_confianza < 100 and a.salud < salud
    # la opción está en el menú, con su explicación
    from juego import menus_juego
    import inspect
    assert '"fuego_amigo"' in inspect.getsource(menus_juego)


def test_tu_explosivo_no_hiere_a_los_que_van_contigo_en_el_coche(robot):
    """Un cóctel molotov contra un coche patrulla pegado al tuyo: el que va de copiloto está donde tú, y el vehículo le
    protege como a ti. A pie, con el fuego amigo puesto, la explosión sí le llega."""
    p, j, d = _con_perro(robot)
    a = p.crear_aliado()
    v = p.crear_vehiculo("deportivo", j.x + 3, j.y, 0, None)
    v.cerrado = False
    p._subir(v, False, callar=True)
    robot.frames(2)                                                  # van de copilotos: donde estás tú
    px, py = p.pos()
    assert a.dist(px, py) < 0.5 and d.dist(px, py) < 0.5
    salud = a.salud
    p.cfg["fuego_amigo"] = True
    p._estallar({"x": px + 3, "y": py, "radio": 6, "dano": 70, "arma": "molotov"})
    assert a.salud == salud and j.perro_confianza == 100 and not a.hostil
    a.puesto = (px, py)                                              # en un golpe preparado está en su sitio, no en tu coche
    p._estallar({"x": px + 3, "y": py, "radio": 6, "dano": 20, "arma": "molotov"})
    assert a.salud < salud


def test_tu_gente_avisa_dos_veces_y_a_la_tercera_se_vuelve_contra_ti(robot):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    j = p.j
    a = p.crear_aliado()
    a.salud = 500
    p.danar_persona(a, 10)
    assert "soy de los tuyos" in robot.dicho() and a.tipo == "aliado" and not a.hostil
    p.danar_persona(a, 10)
    assert "Una más y no respondo" in robot.dicho() and a.tipo == "aliado"
    p.danar_persona(a, 10)
    assert a.tipo == "enemigo" and a.hostil and a.estado == "ataca" and "se vuelve contra ti" in robot.dicho()
    # con el tiempo, un accidente se olvida
    b = p.crear_aliado()
    b.salud = 500
    p.danar_persona(b, 10)
    p.danar_persona(b, 10)
    p.t += 200
    p.danar_persona(b, 10)
    assert b.tipo == "aliado" and b.agravios == 1
    # matar a uno de la banda: uno menos, y no cuenta como enemigo abatido
    j.territorios = ["puerto"]
    j.banda, j.banda_nombre = 2, "Los Nuestros"
    sistemas.llamar(p)
    c = sistemas.miembros_presentes(p)[0]
    antes = j.stats["enemigos"]
    p.danar_persona(c, 9999)
    assert c.muerto and j.banda == 1 and j.stats["enemigos"] == antes and "de los tuyos" in robot.dicho()
    # al guardar, la banda no se apunta como guardaespaldas, ni cobra dos veces
    assert p.a_dict()["jugador"]["guardaespaldas"] == sum(1 for e in p.personas if e.tipo == "aliado" and not e.muerto and not getattr(e, "de_banda", False))


def test_el_perro_pasa_hambre_va_a_casa_y_vuelve(robot):
    p, j, d = _con_perro(robot)
    p.pasar_perro(22 * 60)
    assert 70 <= j.perro_hambre < 100 and "Canela tiene hambre" in robot.dicho()
    p.pasar_perro(10 * 60)
    assert j.perro_hambre == 100 and "ya no tiene fuerzas" in robot.dicho()
    robot.tecla(pygame.K_y)
    assert "no tiene fuerzas para buscar" in robot.dicho()
    # sin casa no se le puede mandar
    j.propiedades = [x for x in j.propiedades if p.lugares[x].tipo != "casa"]
    assert not p.mandar_perro_a_casa() and "No tienes casa" in robot.dicho() and d in p.personas
    casa = next(l for l in p.mundo.lugares.values() if l.tipo == "casa")
    j.propiedades.append(casa.id)
    robot.tecla(pygame.K_y, pygame.KMOD_SHIFT)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Mandar a casa"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and j.perro_en_casa and p.perro() is None and "se va trotando" in robot.dicho()
    robot.tecla(pygame.K_y)
    assert "está en casa" in robot.dicho()
    # en casa come y se tranquiliza, y la partida guardada lo recuerda
    j.perro_confianza = 20
    p.pasar_perro(8 * 60)
    assert j.perro_hambre == 0 and j.perro_confianza == 100
    d2 = p.a_dict()["jugador"]
    assert d2["perro_en_casa"] is True and d2["perro"] == "Canela"
    robot.tecla(pygame.K_y, pygame.KMOD_SHIFT)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Llamar a Canela"))
    robot.tecla(pygame.K_RETURN)
    assert robot.app.pila[-1] is p and not j.perro_en_casa and p.perro() is not None and "llega corriendo" in robot.dicho()
    # el pienso se compra en la protectora
    assert any(o["id"] == "pienso" for o in p.datos["objetos"])
    from juego import menus_extra
    prot = next(l for l in p.lugares.values() if l.tipo == "protectora")
    menus_extra.protectora(p, prot)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if "pienso" in o.texto)
    robot.tecla(pygame.K_RETURN)
    assert j.objetos["pienso"] == 1 and j.dinero == 5000 - 12


def test_los_negocios_se_cobran_de_tres_maneras(robot):
    p = robot.nueva_partida()
    j = p.j
    negocios = [l for l in p.lugares.values() if l.tipo == "negocio"][:2]
    j.propiedades += [l.id for l in negocios]
    total = sum(int(l.get("ingresos", 0)) for l in negocios)
    assert total > 0 and j.cobro_negocios == "mano"
    j.dinero, j.banco = 0, 0
    p.repartir_ingresos_negocios(total)
    assert j.dinero == total and "Ingresos de tus negocios" in robot.dicho()
    p.cambiar_cobro()
    assert j.cobro_negocios == "banco" and "ingresan en el banco" in robot.dicho()
    p.repartir_ingresos_negocios(total)
    assert j.dinero == total and j.banco == total and "en tu cuenta del banco" in robot.dicho()
    p.cambiar_cobro()
    assert j.cobro_negocios == "recoger"
    for _ in range(9):
        p.repartir_ingresos_negocios(total)
    assert j.dinero == total and j.banco == total
    assert all(j.cajas[l.id] == 7 * int(l.get("ingresos", 0)) for l in negocios)          # caben siete días
    assert "caja llena" in robot.dicho()
    # vas tú al negocio: el menú tiene la caja, con el diez por ciento de más
    from juego import menus_juego
    l = negocios[0]
    menus_juego._negocio(p, l)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Recoger la caja"))
    robot.tecla(pygame.K_RETURN)
    caja = 7 * int(l.get("ingresos", 0))
    assert j.dinero == total + caja + caja // 10 and j.cajas[l.id] == 0
    robot.tecla(pygame.K_RETURN)
    assert "La caja está vacía" in robot.dicho()
    # al cambiar de forma, lo que quedaba en las otras cajas no se pierde
    resto = j.cajas[negocios[1].id]
    antes = j.dinero
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Forma de cobro"))
    robot.tecla(pygame.K_RETURN)
    assert j.cobro_negocios == "mano" and j.dinero == antes + resto and not j.cajas
    assert not any(o.texto.startswith("Recoger la caja") for o in m.opciones)


def test_el_tranvia_no_embiste_a_los_coches_y_el_tuyo_aguanta_mas(robot):
    from juego import transporte
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    j = p.j
    m = p.mundo
    v = p.crear_vehiculo("deportivo", j.x + 3, j.y, 0, None)
    v.cerrado = False
    p._subir(v, False, callar=True)
    # en normal, el daño a tu vehículo se queda en tres cuartos; en fácil, en la mitad; en difícil, entero
    for dif, queda in (("normal", 90 - 15), ("facil", 90 - 10), ("dificil", 90 - 20)):
        p.cfg["dificultad"] = dif
        v.salud = 90.0
        p.danar_vehiculo(v, 20)
        assert v.salud == queda, dif
    p.cfg["dificultad"] = "normal"
    v.salud = 90.0
    # parado en las vías, con el tranvía viniendo: frena y espera, sin tocarte
    if not p.tranvias:
        transporte.preparar(p)
    t = p.tranvias[0]
    for otro in p.tranvias[1:]:
        otro["s"] = t["s"] + m.via_largo / 2
    v.x, v.y = m.via_punto(t["s"] + 12)
    v.vel = 0.0
    t["espera"] = 0
    n = len(robot.app.voz.registro)
    for _ in range(30 * 20):
        robot.frames(1)
    oido = " ".join(robot.app.voz.registro[n:])
    assert v.salud == 90.0 and "embiste" not in oido and "frena detrás de ti" in oido
    # el coche arde a cero, pero da tiempo a salir
    p.danar_vehiculo(v, 9999)
    assert v.ardiendo == 7.0
