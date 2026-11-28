"""Integración de las rutas acústicas, el oído del jugador y los canales del mundo."""


from juego.acustica import trayectoria


def test_difraccion_y_sombra_de_un_vehiculo(app):
    mundo = app.mundo
    i, j = next((i, j) for i in range(mundo.NX - 1) for j in range(mundo.NY - 1)
                if mundo.superficie(i * 90 + 45, j * 90 + 45) == "pared")
    x, y = i * 90, j * 90
    a, b = (x + 6, y + 30), (x + 30, y + 6)

    esquina, ganancia, filtro = trayectoria(mundo, a, b, [])
    frente = (a[0], a[1] + 12)
    directa = trayectoria(mundo, a, frente, [])
    tapada = trayectoria(mundo, a, frente, [(a[0], a[1] + 6)])

    assert esquina == (x + 9, y + 9) and 0 < ganancia < 1 and filtro > 0
    assert directa == (frente, 1., 0.)
    assert tapada[0] == frente and tapada[1] < directa[1] and tapada[2] > 0


def test_doppler_al_acercarse_y_alejarse(app):
    m = app.mez
    m.mapa_acustico = app.mundo
    c = m.sonar("motor_coche", xy=(0, 30), bucle=True)

    for t, y, sentido in ((.15, 27, 1), (.30, 30, -1), (.45, 30, 0)):
        c.mover(0, y)
        m.instante = t
        m.actualizar()
        assert (c.doppler - 1.) * sentido > 0 if sentido else c.doppler == 1.


def test_oido_y_mezcla_conservan_la_baliza(robot):
    p = robot.nueva_partida()
    m = p.mez
    p.cfg["tinnitus"] = True
    p.app.aplicar_volumenes()
    oeste = (p.pos()[0] - 4, p.pos()[1])
    motor = p.son("motor_coche", xy=oeste)
    baliza = p.son("baliza", xy=oeste)
    original = m.mezcla_escena(baliza)

    p.son("explosion")
    ganancia, _ = m.mezcla_escena(motor)

    assert motor.filtro > .6 and ganancia < 1.
    assert m.mezcla_escena(baliza) == original and baliza.filtro == 0.
    p.cfg["tinnitus"] = False
    p.app.aplicar_volumenes()
    m.mezcla_escena(motor)
    assert motor.filtro == motor.sombra


def test_lluvia_del_techo_y_fuga_en_la_puerta(robot):
    p = robot.nueva_partida()
    p.cfg["pack_sonidos"] = "estudio"
    p.app.recargar_sonidos()
    p.lluvia = True
    local = next(l for l in p.mundo.lugares.values() if l.tipo in ("bar", "casino", "comida", "club"))
    p._lugares_cercanos(local.x, local.y)
    fuga = p.canales_lugar["puerta:" + local.id]
    assert fuga.xy == (local.x, local.y) and fuga.velo > 0

    p.entrar_interior(local)
    lluvia = p.lluvia_interior
    motor = p.son("motor_coche", xy=(local.x + 8, local.y), bucle=True)
    _, puerta = p.mez.mezcla_escena(motor)

    assert lluvia.nombre == "lluvia_chapa" and lluvia.bucle
    assert puerta == p.mez.puerta_interior and motor.filtro >= .7
    p.salir_interior()
    assert lluvia.parando and p.mez.puerta_interior is None

def test_cambio_de_marcha_y_lluvia_en_la_cabina(robot):
    p = robot.nueva_partida()
    p.cfg["pack_sonidos"] = "estudio"
    p.app.recargar_sonidos()
    v = p.crear_vehiculo("utilitario", *p.pos(), 0, None)
    p._subir(v, False, callar=True)
    v.vel = .29 * v.modelo["vel_max"]
    p.lluvia = True

    p.conducir(.02)
    p._ambiente(.02)

    assert v.marcha_audio == 2 and any(c.nombre == "marcha" for c in p.mez.canales)
    assert p.lluvia_canal.nombre == "lluvia_cabina"
    assert p.rodadura.vol > 0 and v.canal.rate_obj > 0


def test_reflejo_repite_la_toma_y_respeta_el_campo_abierto(robot):
    p = robot.nueva_partida()
    p.mez.entorno = "nave"

    disparo = p.son("disparo_pistola")
    assert len(p.reflejos) == 1 and p.reflejos[0][-1] == disparo.muestra
    assert p.reflejos[0][3] < disparo.vol
    p.mez.entorno = "abierto"
    p.son("disparo_pistola")
    assert len(p.reflejos) == 1


def test_voz_grabada_y_baliza_con_el_mezclador_lleno(app):
    import numpy as np
    m = app.mez
    m.registrar("_voz_escena", np.ones(4410, dtype=np.float32) * .1)
    m.vol_grupos["dialogo"] = .5
    voz = m.sonar("_voz_escena", cat="interfaz")
    m.actualizar()
    assert m.mezcla_escena(voz)[0] == .5 and m.duck < 1.
    for _ in range(60):
        m.sonar("pajaro", cat="ambiente")

    radar = m.sonar("radar", xy=(0, 1))
    assert radar.activo and radar.filtro == 0.


def test_pasos_del_jugador_combinan_terreno_y_calzado(robot):
    import pygame
    p = robot.nueva_partida()
    p.cfg["pack_sonidos"] = "estudio"
    p.app.recargar_sonidos()
    p.j.x, p.j.y = 7.5, 30.
    p.j.calzado = "botas de trabajo con puntera"
    p.dist_paso = 2.
    p.app.teclas.add(pygame.K_UP)

    p.caminar(.04)
    nombres = {c.nombre for c in p.mez.canales}

    assert "suela_bota" in nombres
    assert nombres.intersection(("paso_acera0", "paso_acera1"))


def test_multitud_reacciona_desde_la_posicion_de_un_peaton(robot):
    from juego.entidades import Persona
    p = robot.nueva_partida()
    x, y = p.pos()
    p.personas = [Persona("civil", x + 4, y), Persona("civil", x + 2, y)]
    for persona in p.personas:
        persona.estado = "huye"
    p.t_multitud = 0.

    p._ambiente(.03)
    gritos = [c for c in p.mez.canales if c.nombre == "grito" and c.cat == "ambiente"]

    assert gritos and gritos[-1].xy in {(s.x, s.y) for s in p.personas}
    assert p.t_multitud > 0.


def test_un_coche_no_tapa_su_motor_ni_una_linea_libre(app):
    from types import SimpleNamespace

    m = app.mez
    m.mapa_acustico = app.mundo
    c = m.sonar("motor_coche", xy=(0., 20.), bucle=True)
    veh = SimpleNamespace(x=0., y=16., canal=c, alarma=None, fuego=None, sirena=None, muerto=False)
    m.obstaculos = [veh]
    m.instante += .15
    m.mezcla_escena(c)
    assert c.sombra_obj == 0. and c.ganancia_obj == 1.

    a, b = (0., 0.), (0., 20.)
    for coches in ([(1.1, 10.)], [(0., -3.)], [(0., 24.)], [b], [a]):
        assert trayectoria(app.mundo, a, b, coches) == (b, 1., 0.)
    assert trayectoria(app.mundo, a, b, [(0., 10.)], 0., 6.) == (b, 1., 0.)


def test_el_motor_entra_y_sale_gradualmente_de_la_sombra(app, monkeypatch):
    from juego import audio
    m = app.mez
    m.mapa_acustico = app.mundo
    mundo = app.mundo
    i, j = next((i, j) for i in range(mundo.NX - 1) for j in range(mundo.NY - 1)
                if mundo.superficie(i * 90 + 45, j * 90 + 45) == "pared")
    x, y = i * 90, j * 90
    m.situar_oyente(x + 6, y + 30, 0)
    reloj = [100.]
    monkeypatch.setattr(audio.time, "monotonic", lambda: reloj[0])
    c = m.sonar("motor_coche", xy=(x + 6, y + 6), bucle=True)
    c.mover(x + 30, y + 6)
    m.instante += .15

    def avanzar():
        reloj[0] += 1 / 60
        m.mezcla_escena(c)
        return c.transmision, c.sombra, c.aparente

    entrada = [avanzar() for _ in range(40)]
    assert all(actual[0] < previo[0] and actual[1] > previo[1] for previo, actual in zip(entrada, entrada[1:]))
    assert abs(1 - entrada[0][0]) < .06
    assert entrada[0][2] != c.destino_acustico and entrada[-1][0] < .65

    c.mover(x + 6, y + 6)
    m.instante += .15
    salida = [avanzar() for _ in range(60)]
    assert all(actual[0] > previo[0] and actual[1] < previo[1] for previo, actual in zip(salida, salida[1:]))
    assert salida[-1][0] > .99 and salida[-1][1] < .01
