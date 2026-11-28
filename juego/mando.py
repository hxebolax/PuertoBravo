"""Soporte de mando: Xbox, PlayStation (DualShock 4 y DualSense) y compatibles.

Se usa la API de mandos de SDL (pygame._sdl2.controller), que da la misma
disposición de botones a todos los mandos conocidos. El mando se traduce a las
mismas teclas que el teclado, así que todo lo que se puede hacer con el teclado
se puede hacer con el mando, y los dos se pueden usar a la vez.

La asignación de botones se guarda en data/config/mando.json y se puede cambiar
desde Opciones, Mando.
"""
from .i18n import tr
import json
import math
import os

import pygame

from . import rutas

BOTONES_SDL = {0: "a", 1: "b", 2: "x", 3: "y", 4: "back", 5: "guide", 6: "start", 7: "l3", 8: "r3", 9: "lb", 10: "rb",
               11: "arriba", 12: "abajo", 13: "izquierda", 14: "derecha", 15: "misc", 20: "touchpad"}
EJES_SDL = {0: "lx", 1: "ly", 2: "rx", 3: "ry", 4: "lt", 5: "rt"}
ORDEN_BOTONES = ["a", "b", "x", "y", "lb", "rb", "lt", "rt", "l3", "r3", "arriba", "abajo", "izquierda", "derecha", "back", "start", "touchpad", "misc"]

NOMBRES = {
    "xbox": {"a": "A", "b": "B", "x": "X", "y": "Y", "lb": "LB", "rb": "RB", "lt": tr("gatillo izquierdo"), "rt": tr("gatillo derecho"),
             "l3": tr("pulsar la palanca izquierda"), "r3": tr("pulsar la palanca derecha"), "arriba": tr("cruceta arriba"), "abajo": tr("cruceta abajo"),
             "izquierda": tr("cruceta izquierda"), "derecha": tr("cruceta derecha"), "back": tr("botón Vista"), "start": tr("botón Menú"),
             "touchpad": tr("panel táctil"), "misc": tr("botón Compartir"), "guide": tr("botón Xbox")},
    "ps": {"a": tr("Equis"), "b": tr("Círculo"), "x": tr("Cuadrado"), "y": tr("Triángulo"), "lb": "L1", "rb": "R1", "lt": "L2", "rt": "R2",
           "l3": tr("L3, pulsar la palanca izquierda"), "r3": tr("R3, pulsar la palanca derecha"), "arriba": tr("cruceta arriba"), "abajo": tr("cruceta abajo"),
           "izquierda": tr("cruceta izquierda"), "derecha": tr("cruceta derecha"), "back": tr("botón Crear o Share"), "start": tr("botón Options"),
           "touchpad": tr("panel táctil"), "misc": tr("botón del micrófono"), "guide": tr("botón PlayStation")},
}

K = pygame
S = pygame.KMOD_SHIFT
# acción: (descripción, tecla, modificador, se mantiene pulsada)
ACCIONES = {
    "nada": (tr("sin asignar"), None, 0, False),
    "interactuar": (tr("interactuar: entrar, empezar misión, recoger, hablar"), K.K_RETURN, 0, False),
    "vehiculo": (tr("subir a un vehículo o bajarte"), K.K_f, 0, False),
    "atacar": (tr("atacar o disparar"), K.K_SPACE, 0, True),
    "fijar": (tr("fijar al enemigo más cercano"), K.K_q, 0, False),
    "recargar": (tr("recargar el arma"), K.K_r, 0, False),
    "agacharse": (tr("agacharte o levantarte"), K.K_x, 0, False),
    "arma_sig": (tr("arma siguiente"), K.K_COMMA, 0, False),
    "arma_ant": (tr("arma anterior"), K.K_COMMA, S, False),
    "armas": (tr("lista de armas"), K.K_i, 0, False),
    "botiquin": (tr("usar un botiquín"), K.K_z, 0, False),
    "donde": (tr("dónde estoy"), K.K_c, 0, False),
    "estado": (tr("estado: salud, dinero y arma"), K.K_v, 0, False),
    "radar_sig": (tr("radar: siguiente"), K.K_TAB, 0, False),
    "radar_ant": (tr("radar: anterior"), K.K_TAB, S, False),
    "baliza_radar": (tr("GPS hacia lo último que dijo el radar"), K.K_b, 0, False),
    "gps": (tr("repetir la indicación del GPS"), K.K_g, 0, False),
    "objetivo": (tr("objetivo de la misión"), K.K_o, 0, False),
    "describir": (tr("descripción del lugar"), K.K_n, 0, False),
    "rumbo": (tr("hacia dónde miro, con tono del norte"), K.K_k, 0, False),
    "hora": (tr("hora y tiempo"), K.K_t, 0, False),
    "movil": (tr("abrir el móvil"), K.K_m, 0, False),
    "lugares": (tr("lista de lugares"), K.K_l, 0, False),
    "mapa": (tr("explorador de mapa"), K.K_F9, 0, False),
    "pausa": (tr("menú de pausa"), K.K_ESCAPE, 0, False),
    "ayuda": (tr("ayuda de teclas y botones"), K.K_F1, 0, False),
    "atracar": (tr("atracar a un peatón"), K.K_e, 0, False),
    "gritar": ("gritar", K.K_h, 0, False),
    "acelerar": ("acelerar", K.K_UP, 0, True),
    "frenar": (tr("frenar y marcha atrás"), K.K_DOWN, 0, True),
    "freno_mano": (tr("freno de mano"), K.K_SPACE, 0, True),
    "claxon": ("claxon", K.K_h, 0, False),
    "radio": (tr("emisora siguiente"), K.K_r, 0, False),
    "radio_off": (tr("apagar la radio"), K.K_r, S, False),
    "media_vuelta": (tr("media vuelta"), K.K_u, 0, False),
    "disparar_veh": (tr("disparar desde el vehículo"), K.K_LCTRL, 0, True),
    "trabajo": (tr("empezar o terminar un trabajo con el vehículo"), K.K_j, 0, False),
    "piloto": (tr("piloto del GPS"), K.K_y, 0, False),
    "piloto_estilo": (tr("cómo conduce el piloto del GPS: normal, con prisa, con mucha prisa o temerario"), K.K_y, S, False),
    "paseo": (tr("caminar solo siguiendo el GPS"), K.K_u, 0, False),
    "hablar": (tr("hablar con la persona de al lado"), K.K_j, 0, False),
    "especial": (tr("pescar en el mar, o sirena en vehículos de emergencias"), K.K_p, 0, False),
    "velocidad": (tr("decir la velocidad"), K.K_w, 0, False),
    "motor": (tr("arrancar o apagar el motor"), K.K_e, S, False),
    "estado_vehiculo": (tr("estado del vehículo: cómo está, sus mejoras, el combustible y las averías"), K.K_w, S, False),
    "cruce": (tr("siguiente cruce: qué calle viene y a cuántos metros"), K.K_n, S, False),
    "necesidades": (tr("hambre, sed, sueño e higiene"), K.K_v, S, False),
    "mi_vehiculo": (tr("dónde está mi vehículo, y marcarlo en el GPS"), K.K_l, S, False),
    "mirar_jugador": (tr("cómo va vestido el jugador de al lado"), K.K_j, S, False),
    "quitar_gps": (tr("cancelar el GPS"), K.K_g, S, False),
    "walkman": (tr("reproductor con auriculares: encender y emisora siguiente"), K.K_r, S, False),
    "rendirse": (tr("rendirte ante la policía: levantar las manos"), K.K_h, S, False),
    "menu_acciones": (tr("menú de acciones: todo lo que no tiene botón propio, como dar el alto, gritar, atracar, cubrirte, el tiempo lento, los canales de rol o tu perro"), None, 0, False),
}
# El botón que, mantenido, convierte a los demás en una segunda función: Vista en Xbox, Crear o Share en PlayStation.
# Pulsado y soltado solo, hace lo suyo (de serie, abrir el móvil).
COMBINAR = "back"

POR_DEFECTO = {
    "pie": {"a": "interactuar", "b": "agacharse", "x": "recargar", "y": "vehiculo", "lb": "arma_ant", "rb": "arma_sig",
            "lt": "fijar", "rt": "atacar", "l3": "gps", "r3": "botiquin", "arriba": "donde", "abajo": "estado",
            "izquierda": "radar_ant", "derecha": "radar_sig", "back": "movil", "start": "pausa", "touchpad": "mapa", "misc": "objetivo"},
    "coche": {"a": "interactuar", "b": "freno_mano", "x": "claxon", "y": "vehiculo", "lb": "fijar", "rb": "disparar_veh",
              "lt": "frenar", "rt": "acelerar", "l3": "media_vuelta", "r3": "trabajo", "arriba": "donde", "abajo": "estado",
              "izquierda": "radar_ant", "derecha": "radar_sig", "back": "movil", "start": "pausa", "touchpad": "mapa", "misc": "objetivo"},
    # segundas funciones: manteniendo el botón de combinar y pulsando otro
    "pie_combo": {"a": "paseo", "b": "hablar", "x": "baliza_radar", "y": "mi_vehiculo", "lb": "rumbo", "rb": "hora", "lt": "rendirse", "rt": "menu_acciones", "l3": "quitar_gps", "r3": "armas",
                  "arriba": "cruce", "abajo": "necesidades", "izquierda": "lugares", "derecha": "walkman", "start": "ayuda", "misc": "mirar_jugador",
                  "touchpad": "mirar_jugador"},
    "coche_combo": {"a": "piloto", "b": "velocidad", "x": "gps", "y": "objetivo", "lb": "baliza_radar", "rb": "rumbo", "lt": "rendirse", "rt": "menu_acciones", "l3": "quitar_gps", "r3": "hora",
                    "arriba": "cruce", "abajo": "necesidades", "izquierda": "radio_off", "derecha": "radio", "start": "ayuda", "misc": "lugares",
                    "touchpad": "lugares"},
}
MENU = {"a": K.K_RETURN, "b": K.K_ESCAPE, "start": K.K_ESCAPE, "y": K.K_F1, "x": K.K_PERIOD, "lb": K.K_PAGEUP, "rb": K.K_PAGEDOWN, "back": K.K_TAB,
        "arriba": K.K_UP, "abajo": K.K_DOWN, "izquierda": K.K_LEFT, "derecha": K.K_RIGHT}
PANTALLA = {"a": K.K_RETURN, "b": K.K_ESCAPE, "start": K.K_ESCAPE, "x": K.K_TAB, "y": K.K_n, "lb": K.K_HOME, "rb": K.K_d, "back": K.K_F1,
            "arriba": K.K_UP, "abajo": K.K_DOWN, "izquierda": K.K_LEFT, "derecha": K.K_RIGHT}
PALANCAS_AYUDA = {
    "pie": [tr("Palanca izquierda: caminar; empujada a fondo, correr"), tr("Palanca derecha: escáner direccional, dice qué hay hacia donde la muevas")],
    "coche": [tr("Palanca izquierda a los lados: intermitente en conducción asistida, o volante en conducción libre, en barcos y en helicópteros"),
              tr("Palanca derecha a los lados: cambiar de carril para adelantar. Pilotando un helicóptero o una avioneta, a la derecha sube y a la izquierda baja"), tr("Palanca derecha arriba: emisora siguiente"),
              tr("Palanca derecha abajo: pescar en el mar, o sirena en vehículos de emergencias")],
    "menu": [tr("En los menús: cruceta o palanca izquierda para moverte"), tr("A o Equis para elegir"), tr("B o Círculo para volver"),
             tr("Y o Triángulo para la ayuda de la opción"), tr("X o Cuadrado para repetir"), tr("LB y RB, o L1 y R1, para repasar los mensajes anteriores"),
             tr("En la lista de lugares, el botón Vista, Crear o Share cambia el orden: alfabético, o de más cerca a más lejos"),
             tr("En la pantalla de espera de un servidor: A o Equis repite cómo va, B o Círculo deja de esperar, e Y o Triángulo lo explica"),
             tr("En una travesía en vuelo: cruceta arriba y abajo, altitud; cruceta izquierda y derecha, rumbo; X o Cuadrado, piloto automático; A o Equis, cómo va el vuelo; Y o Triángulo, acelerar; "
             "LB o L1, repetir a la torre; RB o R1, o B o Círculo, el menú de vuelo; y el botón Vista, Crear o Share, la ayuda"),
             tr("Recorriendo una tienda de comida por dentro: X o Cuadrado dice lo que llevas en la cesta. En cada pasillo, A o Equis, o cruceta derecha, echa el producto a la cesta, y cruceta izquierda lo devuelve"),
             tr("Para escribir un texto con el mando: cruceta arriba y abajo recorren las letras, cruceta derecha escribe la letra elegida y cruceta izquierda borra la última. "
             "LB o L1 pone un espacio. RB o R1 cambia entre minúsculas, mayúsculas, números y signos. X o Cuadrado pasa por las frases o los nombres propuestos, si los hay. "
             "Y o Triángulo lee lo escrito. A o Equis acepta y B o Círculo cancela")],
}
# Lo que hacen las palancas, dicho como teclas: esas teclas ya tienen su forma de hacerse con el mando.
PALANCAS = {"pie": {K.K_UP, K.K_DOWN, K.K_LEFT, K.K_RIGHT, K.K_LSHIFT, K.K_w, K.K_a, K.K_s, K.K_d},
            "coche": {K.K_LEFT, K.K_RIGHT, K.K_a, K.K_d, K.K_p, K.K_r}}
C = pygame.KMOD_CTRL
# El menú de acciones: lo que el mando no tiene en un botón. Se abre con el botón de combinar y el gatillo derecho.
# (frase, tecla, modificador, dónde vale: pie, coche o ambos, condición, explicación, se queda abierto)
MENU_ACCIONES = [
    (tr("Dar el alto a los sospechosos"), K.K_h, 0, "pie", "policia", tr("De servicio como policía, das el alto a quien tengas cerca. A quien se rinde se le esposa con el botón de interactuar, a su lado."), False),
    (tr("Gritar para espantar a los peatones"), K.K_h, 0, "pie", "sin_placa", tr("Un grito: los peatones de alrededor se apartan."), False),
    (tr("Hablar en personaje, para quien está cerca"), K.K_F10, S, "ambos", "servidor", tr("En un servidor con canales de rol: lo que dice tu personaje. Lo oye solo quien está cerca."), False),
    (tr("Describir lo que hace tu personaje"), K.K_F10, C, "ambos", "servidor", tr("En un servidor con canales de rol: cuentas una acción, y los que están cerca oyen tu nombre y lo que haces."), False),
    (tr("Escribir un mensaje a los demás jugadores"), K.K_F10, 0, "ambos", "online", tr("Jugando con amigos o en un servidor: un mensaje que se lee en voz alta a los demás."), False),
    (tr("Cómo va vestido el jugador de al lado, y su ficha"), K.K_j, S, "pie", "online", tr("Dice la ropa del jugador más cercano y, en un servidor con canales de rol, su ficha si la ha escrito."), False),
    (tr("Sacar a otro jugador de su vehículo"), K.K_f, S, "pie", "servidor", tr("En un servidor: tiene que ir despacio y estar a tu lado."), False),
    (tr("Atracar al peatón que tienes al lado"), K.K_e, 0, "pie", None, tr("Con un arma en la mano."), False),
    (tr("Ponerte a cubierto, o salir"), K.K_x, S, "pie", None, tr("Tras una pared o un vehículo parado. A cubierto te alcanzan mucho menos; si te mueves, sales."), False),
    (tr("Tiempo lento: ponerlo o quitarlo"), K.K_BACKSPACE, 0, "ambos", None, tr("Todo va más despacio mientras te quede concentración."), False),
    (tr("Fijar a cualquiera, no solo a los enemigos"), K.K_q, S, "ambos", None, tr("Recorre a todos los que hay cerca, también a quien no te ha atacado."), False),
    (tr("Lista de armas"), K.K_i, 0, "ambos", None, tr("Abre la lista de tus armas para elegir una."), False),
    (tr("Usar un botiquín"), K.K_z, 0, "ambos", None, None, False),
    (tr("Tus sustancias"), K.K_z, S, "ambos", "adultos", None, False),
    (tr("Tu perro: que busque por el olfato"), K.K_y, 0, "pie", "perro", tr("Busca el objeto más cercano y te lo marca en el GPS."), False),
    (tr("Tu perro: su menú"), K.K_y, S, "pie", "perro", tr("Cómo está, acariciarlo, darle de comer, mandarlo a casa o llamarlo."), False),
    (tr("Enderezar el vehículo hacia el punto cardinal más cercano"), K.K_e, 0, "coche", "libre", tr("Solo en conducción libre."), False),
    (tr("Cómo conduce el piloto del GPS: normal, con prisa, con mucha prisa o temerario"), K.K_y, S, "coche", None,
     tr("Cada pulsación pasa al estilo siguiente. Con prisa corre más y para en rojo; con mucha prisa va a toda velocidad y no para en los semáforos; temerario, además, no frena por el que va delante."), False),
    (tr("Arrancar o apagar el motor"), K.K_e, S, "coche", None, tr("Con el vehículo parado, lo apaga: no gasta combustible ni se oye, para esperar en silencio u oír la radio aparcado. Otra vez, lo arranca."), False),
    (tr("Estado del vehículo"), K.K_w, S, "coche", None, tr("Cómo está el vehículo en el que vas: su estado, sus mejoras, el combustible y las averías."), False),
    (tr("Pescar en el mar, o sirena en vehículos de emergencias"), K.K_p, 0, "ambos", "mar_o_sirena", tr("Cuando oigas que pican, tira del sedal con el botón de atacar o el de interactuar."), False),
    (tr("Objetivo de la misión o del trabajo"), K.K_o, 0, "ambos", None, tr("Dice primero dónde está y hacia dónde va. Si el objetivo se mueve o corre el tiempo, dos pulsaciones seguidas leen la explicación entera."), False),
    (tr("Volver al objetivo de la misión: GPS y radar"), K.K_o, S, "ambos", None, tr("Deja cualquier desvío, marca en el GPS lo que pide la misión o el trabajo y, si está cerca, lo deja elegido en el radar."), False),
    (tr("Recuperar el último destino que quitaste del GPS"), K.K_g, C, "ambos", None, tr("El destino o el desvío que cancelaste por última vez vuelve al GPS, sin tener que buscarlo otra vez."), False),
    (tr("Lista de lugares, para marcar un destino"), K.K_l, 0, "ambos", None, None, False),
    (tr("Explorador de mapa"), K.K_F9, 0, "ambos", None, tr("Recorre la localidad con un cursor, cruce a cruce, sin mover al personaje."), False),
    (tr("Descripción del lugar o del barrio en el que estás"), K.K_n, 0, "ambos", None, None, False),
    (tr("Dónde está tu vehículo, y marcarlo en el GPS"), K.K_l, S, "ambos", None, tr("El último que has usado. Si tienes más, están en el móvil, en Mis vehículos."), False),
    (tr("Dónde estoy, con las coordenadas"), K.K_c, S, "ambos", None, None, False),
    (tr("Cambiar el filtro del radar"), K.K_F6, 0, "ambos", None, tr("Todo, solo lugares, solo vehículos, solo personas o solo objetos."), False),
    (tr("Repetir el último mensaje"), K.K_PERIOD, 0, "ambos", None, tr("Para repasar los anteriores, en este menú o en cualquier otro: LB y RB, o L1 y R1."), False),
    (tr("Ir al primer mensaje del historial"), K.K_PAGEUP, C, "ambos", None, tr("Desde ahí, LB y RB, o L1 y R1, dentro de cualquier menú, siguen por el historial."), False),
    (tr("Ir al último mensaje del historial"), K.K_PAGEDOWN, C, "ambos", None, None, False),
    (tr("Mensaje anterior de los jugadores y del servidor"), K.K_PAGEUP, S, "ambos", "online", tr("Solo el chat, los avisos del servidor y quién entra y sale, aparte del resto de mensajes. Con el teclado, Mayúsculas y el punto dicen el último."), True),
    (tr("Mensaje siguiente de los jugadores y del servidor"), K.K_PAGEDOWN, S, "ambos", "online", None, True),
    (tr("Cambiar entre conducción asistida y libre"), K.K_F2, 0, "ambos", None, None, False),
    (tr("Cambiar el movimiento a pie entre brújula y giros"), K.K_F3, 0, "ambos", None, None, False),
    (tr("Baliza sonora del GPS: ponerla o quitarla"), K.K_F4, 0, "ambos", None, None, False),
    (tr("Guardado rápido"), K.K_F5, 0, "ambos", None, tr("Fuera de las misiones."), False),
    (tr("Bajar la música"), K.K_F7, 0, "ambos", None, tr("Cada pulsación la baja un poco. El menú no se cierra."), True),
    (tr("Subir la música"), K.K_F8, 0, "ambos", None, tr("Cada pulsación la sube un poco. El menú no se cierra."), True),
    (tr("Poner una marca en el registro de la sesión"), K.K_F12, 0, "ambos", None, tr("Para cuando notes algo raro: quien revise el registro sabrá en qué momento fue."), False),
]
# Lo que sale en la ayuda de teclas y no necesita botón, con el porqué. Lo vigila una prueba: una tecla nueva tiene que
# tener botón, combinación o sitio en el menú de acciones, o estar aquí con su razón.
SIN_BOTON = {
    "Números del 1 al 9": tr("las armas se eligen con arma siguiente y arma anterior, o en la lista de armas"),
    "Re Pág y Av Pág": tr("los mensajes anteriores se repasan con LB y RB, o L1 y R1, dentro de cualquier menú, también en el de acciones"),
    "Frenada automática": tr("no es una tecla: es una ayuda de la conducción asistida"),
    "Helicóptero": tr("no es una tecla: explica cómo se pilota. La altura va en la palanca derecha, a los lados, y la travesía tiene sus propios botones"),
    "En el mar": tr("no es una tecla: explica cómo se llevan los barcos"),
}
# Teclas de la ayuda general que solo valen a pie, con el porqué: no hace falta que estén en el mando al volante.
SOLO_A_PIE = {"Mayúsculas F": tr("al volante esa tecla te baja del vehículo; sacar a otro jugador del suyo se hace a pie")}
# En las pantallas que se recorren, teclas que con el mando llegan como otra: la C de la cesta es X o Cuadrado, que allí es Tabulador.
ALIAS_PANTALLA = {K.K_c: K.K_TAB}


def _condicion(p, cual):
    """¿Tiene sentido ofrecer ahora esa acción del menú de acciones?"""
    j = p.j
    if cual == "policia":
        return bool(p.de_servicio())
    if cual == "sin_placa":
        return not p.de_servicio()
    if cual == "servidor":
        return bool(getattr(p, "en_servidor", False))
    if cual == "online":
        return bool(p.online_activo())
    if cual == "adultos":
        return bool(p.modo_adulto())
    if cual == "perro":
        return bool(j.perro)
    if cual == "libre":
        return not p.modo_asistido()
    if cual == "mar_o_sirena":
        return p.mundo.tipo == "mar" or bool(j.veh and j.veh.modelo.get("sirena"))
    return True


def acciones_de(p):
    """Las entradas del menú de acciones que valen ahora mismo: según vayas a pie o en un vehículo, y según lo que haya."""
    ctx = "coche" if p.j.veh else "pie"
    out = []
    for e in MENU_ACCIONES:
        try:
            vale = e[3] in ("ambos", ctx) and _condicion(p, e[4])
        except Exception:
            vale = e[3] in ("ambos", ctx)
        if vale:
            out.append(e)
    return out


def menu_acciones(app):
    """El menú de acciones del mando: cada cosa que con el teclado es una tecla y en el mando no tiene botón."""
    from .menus import Menu, Opcion
    p = app.pila[-1]

    def hacer(key, mod, queda):
        def f():
            if queda:                                            # el menú sigue abierto: la tecla va derecha a la partida
                p.tecla(_Ev(key, mod))
                return
            app.cerrar(menu)
            app.evento_tecla(_Ev(key, mod))
            app.teclas.discard(key)
        return f
    ops = [Opcion(frase, hacer(key, mod, queda), ayuda=ayuda) for frase, key, mod, _, _, ayuda, queda in acciones_de(p)]
    menu = Menu(app, tr("Acciones"), ops, intro=tr("Lo que no tiene botón propio en el mando"))
    app.abrir(menu)


class Mando:
    ZONA = 0.35

    def __init__(self, app):
        self.app = app
        self.ctrl = None
        self.modulo = None
        self.tipo = "xbox"
        self.nombre = ""
        self.simulado = False
        self.ejes = {"lx": 0.0, "ly": 0.0, "rx": 0.0, "ry": 0.0, "lt": 0.0, "rt": 0.0}
        self.pulsados = set()
        self.mis_teclas = set()
        self.flick = {}             # estado de los «toques» de palanca
        self._combinar_pendiente = False     # el botón de combinar está pulsado y aún no se sabe si es para una combinación
        self._combinar_usado = False
        self._de_combo = set()               # botones pulsados como segunda función: no cuentan como la primera hasta soltarlos
        self.t_rep = 0.0
        self.rep_tecla = None
        self.mapa = {c: dict(m) for c, m in POR_DEFECTO.items()}
        self._cargar_mapa()
        try:
            from pygame._sdl2 import controller
            controller.init()
            self.modulo = controller
            for i in range(controller.get_count()):
                if controller.is_controller(i):
                    self.conectar(i, anunciar=False)
                    break
        except Exception:
            self.modulo = None

    # ------------------------------------------------------------ asignación
    def _archivo(self):
        propio = rutas.archivo_config("mando")
        if not os.path.exists(propio):                    # botones guardados con la otra forma
            base = os.path.splitext(propio)[0]
            for ext in (".json", rutas.EXT_CONFIG):
                if os.path.exists(base + ext) and not getattr(self, "_guardando", False):
                    return base + ext
        return propio

    def _cargar_mapa(self):
        try:
            from . import cifrado
            d = cifrado.leer_json(self._archivo())
            for c in self.mapa:
                for b, a in d.get(c, {}).items():
                    if b in ORDEN_BOTONES and a in ACCIONES:
                        self.mapa[c][b] = a
        except (OSError, ValueError):
            pass

    def guardar_mapa(self):
        if self.app.pruebas:
            return
        try:
            from . import cifrado
            cifrado.escribir_json(rutas.archivo_config("mando"), self.mapa, sangria=2)
        except OSError:
            pass

    def restablecer(self):
        self.mapa = {c: dict(m) for c, m in POR_DEFECTO.items()}
        self.guardar_mapa()

    def textos(self, texto):
        """Con un mando conectado, y si la opción está puesta, las teclas que nombra una frase se dicen como botones."""
        if not self.conectado or not self.app.cfg["mando_textos"]:
            return texto
        p = getattr(self.app, "partida", None)
        try:
            return textos_mando(texto, self.mapa, self.tipo, "coche" if p is not None and p.j.veh else "pie")
        except Exception:
            return texto

    def nombre_boton(self, b):
        return NOMBRES[self.tipo].get(b, b)

    def habla_botones(self):
        """¿Hay que decir botones en vez de teclas? Con un mando conectado y la opción puesta."""
        return self.conectado and bool(self.app.cfg["mando_textos"])

    def boton_pantalla(self, key, tecla, tabla=None):
        """Cómo se dice, en una pantalla del juego, la tecla que hace algo: su nombre o, jugando con mando, el botón
        que hace lo mismo allí, con el nombre de ese mando («el botón X», «el botón Cuadrado»)."""
        if self.habla_botones():
            b = next((b for b in ORDEN_BOTONES if (tabla or PANTALLA).get(b) == key), None)
            if b is not None:
                return _frase_boton(self.tipo, b)
        return tecla

    # --------------------------------------------------------------- conexión
    @property
    def conectado(self):
        return self.simulado or self.ctrl is not None

    def conectar(self, indice, anunciar=True):
        if self.modulo is None or self.ctrl is not None:
            return
        try:
            self.ctrl = self.modulo.Controller(indice)
            self.nombre = str(self.ctrl.name or "mando")
        except Exception:
            self.ctrl = None
            return
        n = self.nombre.lower()
        self.tipo = "ps" if any(x in n for x in ("ps3", "ps4", "ps5", "dualshock", "dualsense", "playstation", "sony", tr("wireless controller"))) else "xbox"
        if anunciar:
            self.app.son("notificacion")
            b = next((b for b in ORDEN_BOTONES if self.mapa["pie_combo"].get(b) == "menu_acciones"), None)
            self.app.decir(tr('Mando conectado: {nombre}. En cualquier momento, la ayuda dice qué hace cada botón.').format(nombre=(self.nombre))
                           + (tr(' Lo que no tiene botón propio está en el menú de acciones: {_frase}.').format(_frase=(_frase(self.tipo, '+' + b))) if b else ""))

    def desconectar(self, anunciar=True):
        if self.ctrl is None:
            return
        self.ctrl = None
        self._soltar_todo()
        if anunciar:
            self.app.son("menu_atras")
            self.app.decir(tr("Mando desconectado. Puedes seguir con el teclado."))

    def _soltar_todo(self):
        for k in self.mis_teclas:
            self.app.teclas.discard(k)
        self.mis_teclas.clear()
        self.pulsados.clear()
        for e in self.ejes:
            self.ejes[e] = 0.0
        self.flick.clear()

    # --------------------------------------------------------------- vibración
    def vibrar(self, grave, agudo, ms):
        if not self.app.cfg["mando_vibracion"] or self.ctrl is None:
            return
        try:
            f = max(0.2, min(1.0, float(self.app.cfg["vibracion_fuerza"])))
            self.ctrl.rumble(max(0.0, min(1.0, grave * f)), max(0.0, min(1.0, agudo * f)), int(ms))
        except Exception:
            pass

    # ---------------------------------------------------------------- contexto
    def contexto(self):
        from .menus import Dialogo, Menu
        from .partida import Partida
        if not self.app.pila:
            return "menu"
        cima = self.app.pila[-1]
        if isinstance(cima, Partida):
            return "coche" if cima.j.veh else "pie"
        if isinstance(cima, (Menu, Dialogo)):
            return "menu"
        return "pantalla"

    def _tecla(self, key, mod=0):
        self.app.evento_tecla(_Ev(key, mod))
        self.app.teclas.discard(key)

    # ------------------------------------------------------------------ eventos
    def evento(self, ev):
        """Procesa un evento de pygame. Devuelve True si era del mando."""
        t = ev.type
        if t == pygame.CONTROLLERDEVICEADDED:
            self.conectar(ev.device_index)
        elif t == pygame.CONTROLLERDEVICEREMOVED:
            self.desconectar()
        elif t == pygame.CONTROLLERBUTTONDOWN:
            self.boton(BOTONES_SDL.get(ev.button), True)
        elif t == pygame.CONTROLLERBUTTONUP:
            self.boton(BOTONES_SDL.get(ev.button), False)
        elif t == pygame.CONTROLLERAXISMOTION:
            self.eje(EJES_SDL.get(ev.axis), ev.value / 32767.0)
        else:
            return False
        return True

    def eje(self, nombre, valor):
        if nombre not in self.ejes:
            return
        valor = max(-1.0, min(1.0, valor))
        antes = self.ejes[nombre]
        self.ejes[nombre] = valor
        if nombre in ("lt", "rt"):              # los gatillos se tratan como botones
            if antes < 0.3 <= valor:
                self.boton(nombre, True)
            elif antes >= 0.15 > valor:
                self.boton(nombre, False)

    def boton(self, b, abajo):
        if b is None:
            return
        ctx = self.contexto()
        if not abajo:
            self.pulsados.discard(b)
            self._de_combo.discard(b)
            if b == COMBINAR and self._combinar_pendiente:
                # Soltado sin haber pulsado nada más: hace lo suyo. Si entre medias se usó para una combinación, nada.
                self._combinar_pendiente = False
                if ctx in ("pie", "coche") and not self._combinar_usado:
                    self._accion(self.mapa[ctx].get(b, "nada"), ctx)
            return
        self.pulsados.add(b)
        if ctx in ("pie", "coche"):
            if b == COMBINAR:
                self._combinar_pendiente, self._combinar_usado = True, False
                return
            if COMBINAR in self.pulsados and self._combinar_pendiente:
                self._combinar_usado = True
                self._de_combo.add(b)                            # mientras siga pulsado no cuenta como su función normal
                self._accion(self.mapa[ctx + "_combo"].get(b, "nada"), ctx)
                return
        if ctx == "menu":
            k = MENU.get(b)
            if k:
                self._tecla(k)
            return
        if ctx == "pantalla":
            k = PANTALLA.get(b)
            if k:
                self._tecla(k)
            return
        self._accion(self.mapa[ctx].get(b, "nada"), ctx)

    def _accion(self, accion, ctx):
        p = self.app.pila[-1]
        if accion == "menu_acciones":
            menu_acciones(self.app)
            return
        if ctx == "coche":
            if accion == "interactuar" and p.pesca:
                self._tecla(K.K_SPACE)              # con la caña echada, el botón de interactuar tira del sedal
                return
            if accion == "claxon" and p.j.veh and p.j.veh.modelo.get("sirena"):
                accion = "especial"
            if accion == "recargar" and hasattr(p, "recargar"):     # al volante la R es la radio: el botón recarga de verdad
                p.recargar()
                return
        _, key, mod, _ = ACCIONES[accion]
        if key is not None:
            self.app.evento_tecla(_Ev(key, mod))
            self.app.teclas.discard(key)

    # ------------------------------------------------------------- por fotograma
    def _toque(self, clave, valor, tecla_neg, tecla_pos, umbral=0.6):
        """Convierte un movimiento de palanca en una sola pulsación (hasta que vuelve al centro)."""
        est = self.flick.get(clave, 0)
        nuevo = -1 if valor <= -umbral else 1 if valor >= umbral else 0 if abs(valor) < 0.3 else est
        if nuevo != est:
            self.flick[clave] = nuevo
            if nuevo:
                self._tecla(tecla_neg if nuevo < 0 else tecla_pos)
            return nuevo
        return 0

    def actualizar(self, dt):
        if not self.conectado:
            return
        app = self.app
        ctx = self.contexto()
        lx, ly, rx, ry = self.ejes["lx"], -self.ejes["ly"], self.ejes["rx"], -self.ejes["ry"]     # arriba positivo
        quiero = set()
        if ctx in ("menu", "pantalla"):
            # palanca izquierda como cruceta, con repetición al mantenerla
            d = None
            if abs(ly) >= 0.6 and abs(ly) >= abs(lx):
                d = K.K_UP if ly > 0 else K.K_DOWN
            elif abs(lx) >= 0.6:
                d = K.K_RIGHT if lx > 0 else K.K_LEFT
            if d is None:
                self.rep_tecla = None
            elif d != self.rep_tecla:
                self.rep_tecla = d
                self.t_rep = 0.45
                self._tecla(d)
            else:
                self.t_rep -= dt
                if self.t_rep <= 0 and d in (K.K_UP, K.K_DOWN):
                    self.t_rep = 0.14
                    self._tecla(d)
        elif ctx == "pie":
            p = app.pila[-1]
            mag = math.hypot(lx, ly)
            if p.cfg["movimiento"] == "brujula":
                if mag >= self.ZONA:
                    ang = math.degrees(math.atan2(lx, ly)) % 360
                    sector = int((ang + 22.5) // 45) % 8
                    if sector in (7, 0, 1):
                        quiero.add(K.K_UP)
                    if sector in (1, 2, 3):
                        quiero.add(K.K_RIGHT)
                    if sector in (3, 4, 5):
                        quiero.add(K.K_DOWN)
                    if sector in (5, 6, 7):
                        quiero.add(K.K_LEFT)
            else:
                if ly >= self.ZONA:
                    quiero.add(K.K_UP)
                elif ly <= -self.ZONA:
                    quiero.add(K.K_DOWN)
                self._toque("giro", lx, K.K_LEFT, K.K_RIGHT)
            if mag >= 0.92:
                quiero.add(K.K_LSHIFT)
            # palanca derecha: escáner direccional
            if abs(ry) >= abs(rx):
                self._toque("ry", ry, K.K_s, K.K_w)
                self._toque("rx", 0.0, K.K_a, K.K_d)
            else:
                self._toque("rx", rx, K.K_a, K.K_d)
                self._toque("ry", 0.0, K.K_s, K.K_w)
        elif ctx == "coche":
            p = app.pila[-1]
            if p.modo_asistido():
                self._toque("lx", lx, K.K_LEFT, K.K_RIGHT)
            else:
                if lx <= -self.ZONA:
                    quiero.add(K.K_LEFT)
                elif lx >= self.ZONA:
                    quiero.add(K.K_RIGHT)
            if rx <= -0.5:
                quiero.add(K.K_a)
            elif rx >= 0.5:
                quiero.add(K.K_d)
            if abs(ry) > abs(rx):
                n = self._toque("vry", ry, K.K_p, K.K_r)
        # botones que se mantienen (acelerar, frenar, disparar...)
        if ctx in ("pie", "coche"):
            for b in self.pulsados:
                if b in self._de_combo or (b == COMBINAR and self._combinar_pendiente):
                    continue
                accion = self.mapa[ctx].get(b, "nada")
                _, key, mod, mantener = ACCIONES[accion]
                if mantener and key is not None:
                    quiero.add(key)
        for k in self.mis_teclas - quiero:
            app.teclas.discard(k)
        for k in quiero:
            app.teclas.add(k)
        self.mis_teclas = quiero

    # -------------------------------------------------------------------- ayuda
    def lineas_ayuda(self, contextos=("pie", "coche", "menu")):
        titulos = {"pie": tr("Mando, a pie"), "coche": tr("Mando, al volante"), "menu": tr("Mando")}
        out = []
        for c in contextos:
            if c in self.mapa:
                for b in ORDEN_BOTONES:
                    a = self.mapa[c].get(b, "nada")
                    if a != "nada":
                        out.append(f"{titulos[c]}. {self.nombre_boton(b).capitalize()}: {ACCIONES[a][0]}.")
            for linea in PALANCAS_AYUDA.get(c, []):
                out.append(f"{titulos[c]}. {linea}.")
            if c + "_combo" in self.mapa:
                mod = self.nombre_boton(COMBINAR).capitalize()
                vistas = set()
                for b in ORDEN_BOTONES:
                    a = self.mapa[c + "_combo"].get(b, "nada")
                    if a != "nada" and b != COMBINAR and (a, b in ("touchpad", "misc")) not in vistas:
                        vistas.add((a, b in ("touchpad", "misc")))
                        out.append(tr('{v}. {mod}, mantenido, más {nombre_boton}: {v2}.').format(v=(titulos[c]), mod=(mod), nombre_boton=(self.nombre_boton(b)), v2=(ACCIONES[a][0])))
        return out


class _Ev:
    def __init__(self, key, mod=0):
        self.key = key
        self.mod = mod
        self.unicode = ""
        self.mando = True                # viene del mando: no pasa por el cambio de teclas del teclado, y en un cuadro de texto mueve la rueda de letras


# ------------------------------------------------------------- las teclas, dichas como botones
# Con un mando conectado, lo que el juego cuenta («pulsa Q para fijarlo») se dice con el botón que hace eso mismo.
_TECLAS_TXT = {"intro": K.K_RETURN, "espacio": K.K_SPACE, "tabulador": K.K_TAB, "escape": K.K_ESCAPE, "f1": K.K_F1, "f9": K.K_F9,
               "coma": K.K_COMMA, "control": K.K_LCTRL,
               "enter": K.K_RETURN, "space": K.K_SPACE, "tab": K.K_TAB, "comma": K.K_COMMA}         # sus nombres en inglés
# Cuando una tecla hace dos cosas, según vayas a pie o en un vehículo, la frase dice cuál de las dos es.
_PISTAS = {"freno_mano": r"freno\sde\smano|handbrake", "atacar": "dispar|atac|golpe|pega|shoot|fire|attack|hit|strike|punch",
           "recargar": "recarg|reload", "radio": "emisora|radio|station", "claxon": "claxon|pita|horn|honk",
           "gritar": "grit|shout|yell", "media_vuelta": r"media\svuelta|u-turn|turn\saround", "paseo": "camina|pasea|paseo|walk|stroll",
           "trabajo": "trabajo|turno|servicio|work|shift|duty", "hablar": "habl|charl|convers|talk|chat", "interactuar": ""}
_BOTON_SOLO = ("a", "b", "x", "y", "lb", "rb")


def _frase_boton(tipo, b):
    """«el botón A», «el gatillo derecho», «la cruceta arriba»: el botón, con su artículo."""
    n = NOMBRES[tipo].get(b, b)
    if b in ("lt", "rt"):
        return (tr("el ") + n) if tipo == "xbox" else tr("el botón {n}").format(n=n)
    if b in ("arriba", "abajo", "izquierda", "derecha"):
        return tr("la ") + n
    if b in ("l3", "r3"):
        return tr("la palanca izquierda pulsada") if b == "l3" else tr("la palanca derecha pulsada")
    if b in ("back", "start", "misc", "guide"):
        return tr("el ") + n
    if b == "touchpad":
        return tr("el panel táctil")
    return tr("el botón {n}").format(n=n)


def _boton_de(mapa, key, mod, contexto, frase, tipo):
    """El botón que hace lo mismo que esa tecla. None si ninguno, o si no se sabe cuál de sus dos usos es."""
    acciones = [a for a, d in ACCIONES.items() if d[1] == key and (d[2] & S) == (mod & S) and a != "nada"]
    if not acciones:
        return None
    if len(acciones) > 1:
        f = frase.lower()
        con_pista = [a for a in acciones if _PISTAS.get(a) and __import__("re").search(_PISTAS[a], f)]
        if len(con_pista) == 1:
            acciones = con_pista
    orden = [contexto, "coche" if contexto == "pie" else "pie"] if len(acciones) == 1 else [contexto]
    for c in orden:
        for b in ORDEN_BOTONES:
            if mapa.get(c, {}).get(b) in acciones:
                return b
        if c == contexto:                                        # sin botón propio, su combinación: «+botón»
            for b in ORDEN_BOTONES:
                if b != COMBINAR and not (b == "touchpad" and tipo == "xbox") and mapa.get(c + "_combo", {}).get(b) in acciones:
                    return "+" + b
    return None


def _frase(tipo, b):
    """Un botón o una combinación («+botón»), dichos con su artículo."""
    if b.startswith("+"):
        return tr('{_frase_boton} mantenido más {_frase_boton2}').format(_frase_boton=(_frase_boton(tipo, COMBINAR)), _frase_boton2=(_frase_boton(tipo, b[1:])))
    return _frase_boton(tipo, b)


def textos_mando(texto, mapa, tipo="xbox", contexto="pie"):
    """Cambia en una frase las teclas por los botones del mando que hacen lo mismo. Lo que no tiene botón se deja como está,
    porque el teclado sigue funcionando con el mando conectado."""
    import re
    if not texto or not isinstance(texto, str):
        return texto
    from . import i18n
    if not i18n.es_origen():
        return _textos_mando_en(texto, mapa, tipo, contexto)

    def una_frase(frase):
        def tecla_de(nombre):
            n = nombre.lower()
            if n in _TECLAS_TXT:
                return _TECLAS_TXT[n]
            if len(n) == 1 and n.isalpha():
                return getattr(K, "K_" + n, None)
            return None

        def cambia(m):
            verbo, mayus, nombre = m.group("verbo"), m.group("mayus"), m.group("tecla")
            key = tecla_de(nombre)
            if key is None:
                return m.group(0)
            b = _boton_de(mapa, key, S if mayus else 0, contexto, frase, tipo)
            if b is None:
                return m.group(0)
            return f"{verbo} {_frase(tipo, b)}"

        # «pulsa Q», «con la X», «con la tecla J», «Pulsa Mayúsculas Y», «tecla M»
        frase = re.sub(r"(?P<verbo>\b(?:[Pp]uls(?:a|ar|as|ando|es|ada)|[Cc]on|[Uu]sa|[Mm]antén(?: pulsad[ao])?|[Tt]oca))"
                       r" (?:(?:la|el) )?(?:tecla )?(?P<mayus>Mayúsculas (?:más |\+ )?(?:la )?)?"
                       r"(?P<tecla>Intro|Espacio|Tabulador|Escape|Control|F1|F9|coma|[A-ZÑ])(?![\wáéíóúñ])", cambia, frase)

        def suelta(m):                                           # «pulsa Espacio para disparar y R para recargar»
            key = tecla_de(m.group("tecla"))
            b = _boton_de(mapa, key, 0, contexto, frase, tipo) if key is not None else None
            return m.group(0) if b is None else tr('{group} {_frase} para').format(group=(m.group(1)), _frase=(_frase(tipo, b)))
        frase = re.sub(r"(?<![\wáéíóúñ])(y|o|ni) (?:la )?(?P<tecla>Intro|Espacio|Tabulador|Escape|Control|[A-ZÑ]) para(?![\wáéíóúñ])", suelta, frase)

        def solo_tecla(m):                                       # «la tecla M abre el móvil»
            key = tecla_de(m.group("tecla"))
            b = _boton_de(mapa, key, 0, contexto, frase, tipo) if key is not None else None
            if b is None:
                return m.group(0)
            f = _frase(tipo, b)
            return f[0].upper() + f[1:] if m.group(0)[0].isupper() else f
        frase = re.sub(r"\b(?:[Ll]a|[Ee]l) tecla (?P<tecla>Intro|Espacio|Tabulador|Escape|Control|F1|F9|[A-ZÑ])(?![\wáéíóúñ])", solo_tecla, frase)
        # las flechas son la palanca izquierda; en un vehículo, arriba y abajo son los gatillos
        f = frase.lower()
        acel = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "acelerar"), None)
        fren = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "frenar"), None)
        if acel and re.search(r"aceler", f):
            frase = re.sub(r"\b(?:la )?flecha (?:de )?arriba\b", _frase_boton(tipo, acel), frase)
        if fren and re.search(tr(r"fren|marcha atrás"), f):
            frase = re.sub(r"\b(?:la )?flecha (?:de )?abajo\b", _frase_boton(tipo, fren), frase)
        frase = re.sub(r"\blas flechas izquierda y derecha\b", tr("la palanca izquierda a los lados"), frase)
        frase = re.sub(r"\b(?:la )?flecha (?:de )?arriba\b", tr("la palanca izquierda hacia delante"), frase)
        frase = re.sub(r"\b(?:la )?flecha (?:de )?abajo\b", tr("la palanca izquierda hacia atrás"), frase)
        frase = re.sub(r"\b[Ll]as flechas\b", lambda m: ("L" if m.group(0)[0] == "L" else "l") + tr("a palanca izquierda"), frase)
        frase = re.sub(r"\b([Cc])on flechas\b", tr(r"\1on la palanca izquierda"), frase)
        frase = re.sub(r"\b([Mm])antén Mayúsculas\b", lambda m: ("E" if m.group(1) == "M" else "e") + tr("mpuja a fondo la palanca izquierda"), frase)
        return frase

    return "".join(una_frase(t) for t in re.split(r"(?<=[.!?:;])(\s+)", texto))


def literal(t):
    """Un texto que va tal cual, sin traducir: las piezas inglesas con que se reconocen las teclas en inglés."""
    return t


def _textos_mando_en(texto, mapa, tipo="xbox", contexto="pie"):
    """Lo mismo que textos_mando, para las frases en inglés (y en cualquier idioma que diga las teclas como el inglés):
    «press Q», «with the X key», «Shift Y», «the up arrow»..."""
    import re
    TECLA = r"(?P<tecla>Enter|Space|Tab|Escape|Control|F1|F9|comma|[A-Z])"

    def tecla_de(nombre):
        n = nombre.lower()
        if n in _TECLAS_TXT:
            return _TECLAS_TXT[n]
        if len(n) == 1 and n.isalpha():
            return getattr(K, "K_" + n, None)
        return None

    def una_frase(frase):
        def cambia(m):
            key = tecla_de(m.group("tecla"))
            if key is None:
                return m.group(0)
            b = _boton_de(mapa, key, S if m.group("mayus") else 0, contexto, frase, tipo)
            return m.group(0) if b is None else f"{m.group('verbo')} {_frase(tipo, b)}"
        # «press Q», «with the X», «use the J key», «press Shift Y», «hold Control»
        frase = re.sub(r"(?P<verbo>\b(?:[Pp]ress(?:ing|es|ed)?|[Ww]ith|[Uu]se|[Hh]old(?:ing)?(?: down)?|[Tt]ap))"
                       r" (?:the )?(?P<mayus>Shift (?:\+ |plus )?)?" + TECLA + r"(?: key)?(?![\w])", cambia, frase)

        def suelta(m):                                           # «press Space to shoot and R to reload»
            key = tecla_de(m.group("tecla"))
            b = _boton_de(mapa, key, 0, contexto, frase, tipo) if key is not None else None
            return m.group(0) if b is None else literal("{g} {f} to").format(g=m.group(1), f=_frase(tipo, b))
        frase = re.sub(r"(?<![\w])(and|or|nor) (?:the )?" + TECLA + r"(?: key)? to(?![\w])", suelta, frase)

        def solo_tecla(m):                                       # «the M key opens the phone»
            key = tecla_de(m.group("tecla"))
            b = _boton_de(mapa, key, 0, contexto, frase, tipo) if key is not None else None
            if b is None:
                return m.group(0)
            f = _frase(tipo, b)
            return f[0].upper() + f[1:] if m.group(0)[0].isupper() else f
        frase = re.sub(literal(r"\b[Tt]he ") + TECLA + literal(r" key\b"), solo_tecla, frase)
        f = frase.lower()
        acel = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "acelerar"), None)
        fren = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "frenar"), None)
        arriba = r"\b(?:the )?[Uu]p [Aa]rrow\b"
        abajo = r"\b(?:the )?[Dd]own [Aa]rrow\b"
        if acel and re.search(r"accelerat", f):
            frase = re.sub(arriba, _frase_boton(tipo, acel), frase)
        if fren and re.search(r"brak|revers", f):
            frase = re.sub(abajo, _frase_boton(tipo, fren), frase)
        frase = re.sub(r"\b(?:the )?[Ll]eft and [Rr]ight [Aa]rrows\b", tr("la palanca izquierda a los lados"), frase)
        frase = re.sub(arriba, tr("la palanca izquierda hacia delante"), frase)
        frase = re.sub(abajo, tr("la palanca izquierda hacia atrás"), frase)
        frase = re.sub(r"\b[Tt]he arrow(?: key)?s\b|\b[Tt]he arrows\b", lambda m: ("T" if m.group(0)[0] == "T" else "t") + literal("he left stick"), frase)
        frase = re.sub(r"\b([Hh])old Shift\b", lambda m: ("P" if m.group(1) == "H" else "p") + literal("ush the left stick all the way"), frase)
        return frase

    return "".join(una_frase(t) for t in re.split(r"(?<=[.!?:;])(\s+)", texto))


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False

# ---------------------------------------------------------------- łatka polskiej wersji (latki/pad_polski.py)
_TECLAS_TXT.update({"enter": K.K_RETURN, "spacja": K.K_SPACE, "spację": K.K_SPACE, "spacji": K.K_SPACE, "tab": K.K_TAB,
                    "ctrl": K.K_LCTRL, "przecinek": K.K_COMMA})
_PISTAS_PL = {"freno_mano": "hamulec ręczn|ręczn", "atacar": "strzel|atak|uderz|bij", "recargar": "przeład",
              "radio": "stacj|radio", "claxon": "klakson|trąb", "gritar": "krzyk|krzycz", "media_vuelta": "zawr",
              "paseo": "spacer|chodz|idź|przejdź", "trabajo": "prac|zmian|służb", "hablar": "rozm|mów|pogad|zagad|powiedz"}
for _k, _v in _PISTAS_PL.items():
    if _PISTAS.get(_k):
        _PISTAS[_k] = _PISTAS[_k] + "|" + _v

_NARZEDNIK_PL = (("przycisk ", "przyciskiem "), ("lewy spust", "lewym spustem"), ("prawy spust", "prawym spustem"),
                 ("krzyżak ", "krzyżakiem "), ("panel dotykowy", "panelem dotykowym"), ("wciśnięcie ", "wciśnięciem "))


def _nazwa_pl(tipo, b):
    """Przycisk w mianowniku: „przycisk A”, „lewy spust”, „krzyżak w górę”."""
    if b.startswith("+"):
        return f"{NOMBRES[tipo].get(COMBINAR, COMBINAR)} + {NOMBRES[tipo].get(b[1:], b[1:])}"
    n = NOMBRES[tipo].get(b, b)
    if "," in n:                                              # „L3, wciśnięcie lewej gałki”
        n = n.split(",", 1)[0]
    return "przycisk " + n if " " not in n else n


def _biernik_pl(tipo, b):
    n = _nazwa_pl(tipo, b)
    return {"wciśnięcie lewej gałki": "lewą gałkę, wciskając ją", "wciśnięcie prawej gałki": "prawą gałkę, wciskając ją"}.get(n, n)


def _narzednik_pl(tipo, b):
    n = _nazwa_pl(tipo, b)
    for a, z in _NARZEDNIK_PL:
        if n.startswith(a):
            return z + n[len(a):]
    return n


def _textos_mando_pl(texto, mapa, tipo="xbox", contexto="pie"):
    import re
    if not texto or not isinstance(texto, str):
        return texto
    TECLA = r"(?P<tecla>Enter|Spacj[aęi]|Tab|Escape|Ctrl|F1|F9|przecinek|[A-ZŃ])(?![\wąćęłńóśźż+])"

    def una_frase(frase):
        def tecla_de(nombre):
            n = nombre.lower()
            if n in _TECLAS_TXT:
                return _TECLAS_TXT[n]
            if len(n) == 1 and "a" <= n <= "z":
                return getattr(K, "K_" + n, None)
            return None

        def boton(m, mayus=False):
            key = tecla_de(m.group("tecla"))
            if key is None:
                return None
            return _boton_de(mapa, key, S if mayus else 0, contexto, frase, tipo)

        def z_czasownikiem(m):                                   # „naciśnij Q”, „Naciśnij Shift+Y”
            b = boton(m, bool(m.group("mayus")))
            return m.group(0) if b is None else f"{m.group('verbo')} {_biernik_pl(tipo, b)}"
        frase = re.sub(r"(?P<verbo>\b[Nn]aciśnij|\b[Nn]aciśnięcie|\b[Nn]aciskasz|\b[Pp]rzytrzymaj) (?:klawisz )?(?P<mayus>Shift\+)?" + TECLA,
                       z_czasownikiem, frase)

        def narzednik(m):                                        # „klawiszem F”, „Klawiszem L”
            b = boton(m, bool(m.group("mayus")))
            if b is None:
                return m.group(0)
            t = _narzednik_pl(tipo, b)
            return t[0].upper() + t[1:] if m.group(0)[0].isupper() else t
        frase = re.sub(r"\b[Kk]lawiszem (?P<mayus>Shift\+)?" + TECLA, narzednik, frase)

        def mianownik(m):                                        # „klawisz O mówi”, „Klawisz P włącza syrenę”
            b = boton(m, bool(m.group("mayus")))
            if b is None:
                return m.group(0)
            t = _nazwa_pl(tipo, b)
            return t[0].upper() + t[1:] if m.group(0)[0].isupper() else t
        frase = re.sub(r"\b[Kk]lawisz (?P<mayus>Shift\+)?" + TECLA, mianownik, frase)

        def luzem(m):                                            # „i Spację, żeby uderzyć”, „strzelaj Ctrl”
            b = boton(m)
            return m.group(0) if b is None else f"{m.group(1)} {_biernik_pl(tipo, b)}"
        frase = re.sub(r"(?<![\wąćęłńóśźż])(i|albo|ani|strzelaj) " + TECLA + r"(?=,? żeby| i | albo |\.|,|$)", luzem, frase)

        f = frase.lower()
        acel = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "acelerar"), None)
        fren = next((b for b in ORDEN_BOTONES if mapa.get("coche", {}).get(b) == "frenar"), None)
        if acel and re.search(r"przyspiesz|gaz", f):
            frase = re.sub(r"\bstrzałk[aęi] w górę\b", _biernik_pl(tipo, acel), frase)
        if fren and re.search(r"hamuj|hamow|wsteczn", f):
            frase = re.sub(r"\bstrzałk[aęi] w dół\b", _biernik_pl(tipo, fren), frase)
        frase = re.sub(r"\b([Ss])trzałkami w lewo i w prawo\b", lambda m: ("L" if m.group(1) == "S" else "l") + "ewą gałką na boki", frase)
        frase = re.sub(r"\b([Ss])trzałki w lewo i w prawo\b", lambda m: ("L" if m.group(1) == "S" else "l") + "ewa gałka na boki", frase)
        frase = re.sub(r"\bstrzałkę w górę\b", "lewą gałkę do przodu", frase)
        frase = re.sub(r"\bstrzałkę w dół\b", "lewą gałkę do tyłu", frase)
        frase = re.sub(r"\bstrzałka w górę\b", "lewa gałka do przodu", frase)
        frase = re.sub(r"\bstrzałka w dół\b", "lewa gałka do tyłu", frase)
        frase = re.sub(r"\b([Ss])trzałkami\b", lambda m: ("L" if m.group(1) == "S" else "l") + "ewą gałką", frase)
        frase = re.sub(r"\b([Ss])trzałki\b", lambda m: ("L" if m.group(1) == "S" else "l") + "ewa gałka", frase)
        frase = re.sub(r"\b([Tt]rzymaj|[Pp]rzytrzymaj) Shift\b", lambda m: m.group(1) + " lewą gałkę wychyloną do końca", frase)
        return frase

    return "".join(una_frase(t) for t in re.split(r"(?<=[.!?:;])(\s+)", texto))


_textos_mando_es = textos_mando


def textos_mando(texto, mapa, tipo="xbox", contexto="pie"):
    """Po polsku – polskie zwroty; w innych językach – oryginał autora."""
    return (_textos_mando_pl if _pl() else _textos_mando_es)(texto, mapa, tipo, contexto)
