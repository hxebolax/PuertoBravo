"""Reasignar las teclas del teclado.

El juego está escrito con unas teclas fijas (C dice dónde estás, F sube al coche...). Aquí se guarda qué tecla
física quiere usar el jugador para cada una. Cambiar una tecla intercambia las dos: si pones «dónde estoy» en la
P, lo que hacía la P pasa a la C, y así ninguna función se queda sin tecla.

La traducción se aplica jugando y, si el jugador lo pide en las opciones, también en los menús y los diálogos.
Nunca en los cuadros de texto. La Mayúsculas izquierda también se puede mover: la tecla que la sustituya sirve para
correr y para todas las combinaciones con Mayúsculas.
"""
from .i18n import tr
import pygame

NOMBRES = {pygame.K_LSHIFT: tr("Mayúsculas izquierda"), pygame.K_UP: tr("flecha arriba"), pygame.K_DOWN: tr("flecha abajo"), pygame.K_LEFT: tr("flecha izquierda"), pygame.K_RIGHT: tr("flecha derecha"),
           pygame.K_SPACE: "espacio", pygame.K_TAB: "tabulador", pygame.K_COMMA: "coma", pygame.K_PERIOD: "punto", pygame.K_MINUS: "guion",
           pygame.K_RETURN: tr("Intro"), pygame.K_ESCAPE: tr("Escape"), pygame.K_BACKSPACE: "retroceso", pygame.K_HOME: "inicio", pygame.K_END: "fin",
           pygame.K_PAGEUP: tr("retroceder página"), pygame.K_PAGEDOWN: tr("avanzar página"), pygame.K_INSERT: "insertar", pygame.K_DELETE: "suprimir",
           pygame.K_SEMICOLON: "eñe", pygame.K_QUOTE: "acento", pygame.K_LEFTBRACKET: tr("acento grave"), pygame.K_RIGHTBRACKET: "más",
           pygame.K_BACKSLASH: tr("ce cedilla"), pygame.K_SLASH: "guion", pygame.K_LESS: tr("menor que")}
# Estas no se pueden cambiar ni usar como destino: son las de salir, aceptar, la ayuda, la marca del registro y los modificadores.
FIJAS = {pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_F1, pygame.K_F12, pygame.K_RSHIFT, pygame.K_LCTRL, pygame.K_RCTRL,
         pygame.K_LALT, pygame.K_RALT, pygame.K_LGUI, pygame.K_RGUI, pygame.K_CAPSLOCK, pygame.K_NUMLOCK, pygame.K_PRINTSCREEN}
ETIQUETAS = {"retroceso": pygame.K_BACKSPACE, "espacio": pygame.K_SPACE, "tabulador": pygame.K_TAB, "flecha arriba": pygame.K_UP, "flecha abajo": pygame.K_DOWN}


def nombre(k):
    if k in NOMBRES:
        return NOMBRES[k]
    if pygame.K_a <= k <= pygame.K_z or pygame.K_0 <= k <= pygame.K_9:
        return chr(k).upper()
    if pygame.K_F1 <= k <= pygame.K_F12:
        return f"F{k - pygame.K_F1 + 1}"
    try:
        return pygame.key.name(k) or tr('tecla {k}').format(k=(k))
    except Exception:
        return tr('tecla {k}').format(k=(k))


def _codigo(etiqueta):
    """El código de tecla de una etiqueta de la ayuda si nombra una sola tecla («C», «F9», «Espacio»); si no, None."""
    e = etiqueta.strip().lower()
    if len(e) == 1 and e.isalnum():
        return ord(e)
    if e.startswith("f") and e[1:].isdigit() and 2 <= int(e[1:]) <= 11:
        return pygame.K_F1 + int(e[1:]) - 1
    return ETIQUETAS.get(e)


def funciones():
    """Las funciones que se pueden cambiar de tecla: (código original, contexto, descripción). Salen de la ayuda del juego."""
    from .ayuda import TECLAS
    titulos = {"general": tr("En cualquier momento"), "pie": tr("A pie"), "coche": tr("Al volante")}
    vistas, lista = {}, []
    for ctx in ("general", "pie", "coche"):
        for etiqueta, que in TECLAS[ctx]:
            k = _codigo(etiqueta)
            if k is None or k in FIJAS:
                continue
            if k in vistas:                           # la misma tecla hace una cosa a pie y otra al volante: una sola entrada
                n = vistas[k]
                lista[n] = (k, tr("A pie y al volante"), f"{lista[n][1].lower()}, {lista[n][2]}. {titulos[ctx]}, {que}")
            else:
                vistas[k] = len(lista)
                lista.append((k, titulos[ctx], que))
    for k, que in ((pygame.K_UP, tr("caminar al norte o hacia delante, y acelerar al volante")), (pygame.K_DOWN, tr("caminar al sur o hacia atrás, y frenar al volante")),
                   (pygame.K_LEFT, tr("caminar al oeste o girar a la izquierda, e intermitente izquierdo")),
                   (pygame.K_RIGHT, tr("caminar al este o girar a la derecha, e intermitente derecho")), (pygame.K_SPACE, tr("atacar o disparar, y freno de mano")),
                   (pygame.K_TAB, tr("radar")), (pygame.K_w, tr("escáner: delante. Al volante, la velocidad")), (pygame.K_a, tr("escáner: izquierda. Al volante, cambiar de carril")),
                   (pygame.K_s, tr("escáner: detrás")), (pygame.K_d, tr("escáner: derecha. Al volante, arrimarte a la acera")), (pygame.K_COMMA, tr("arma siguiente")),
                   (pygame.K_PERIOD, tr("repetir el último mensaje")),
                   (pygame.K_LSHIFT, tr("correr a pie, y hacer las combinaciones con Mayúsculas, como Mayúsculas Tabulador. La Mayúsculas derecha no cambia, y sirve para las combinaciones pero no para correr"))):
        if k not in vistas:
            vistas[k] = len(lista)
            lista.append((k, tr("Movimiento y acciones"), que))
    return lista


def _mapa(cfg):
    """{función original: tecla física que la hace}, solo con lo cambiado y saneado."""
    m = {}
    for a, b in dict(cfg["teclas"]).items():
        try:
            a, b = int(a), int(b)
        except (TypeError, ValueError):
            continue
        if a != b and a not in FIJAS and b not in FIJAS:
            m[a] = b
    return m


def traducir(cfg, k):
    """Qué función hace la tecla física k. Sin cambios, ella misma."""
    if not cfg["teclas"]:
        return k
    for funcion, fisica in _mapa(cfg).items():
        if fisica == k:
            return funcion
    return k


def modificadores(cfg, mod, pulsadas):
    """Los modificadores de una pulsación cuando la Mayúsculas izquierda está en otra tecla: cuenta la tecla que la sustituye."""
    if pygame.K_LSHIFT not in _mapa(cfg):
        return mod
    mod &= ~pygame.KMOD_SHIFT
    if pygame.K_LSHIFT in pulsadas or pygame.K_RSHIFT in pulsadas:
        mod |= pygame.KMOD_LSHIFT
    return mod


def tecla_de(cfg, funcion):
    """Con qué tecla física se hace ahora una función."""
    return _mapa(cfg).get(funcion, funcion)


def cambiar(cfg, funcion, fisica):
    """Pone la función en la tecla física dada e intercambia lo que hubiera allí. Devuelve la función desplazada, o None."""
    if funcion in FIJAS or fisica in FIJAS:
        return None
    m = _mapa(cfg)
    antes = m.get(funcion, funcion)               # la tecla que hacía esta función
    otra = traducir(cfg, fisica)                  # la función que hacía la tecla elegida
    m[funcion] = fisica
    desplazada = None
    if otra != funcion:
        m[otra] = antes
        desplazada = otra
    cfg["teclas"] = {str(a): str(b) for a, b in m.items() if a != b}
    return desplazada


def restablecer(cfg):
    cfg["teclas"] = {}


_TXT = {"intro": pygame.K_RETURN, "espacio": pygame.K_SPACE, "tabulador": pygame.K_TAB, "coma": pygame.K_COMMA,
        "enter": pygame.K_RETURN, "space": pygame.K_SPACE, "tab": pygame.K_TAB, "comma": pygame.K_COMMA}


def _codigo_txt(n):
    n = n.lower()
    if n in _TXT:
        return _TXT[n]
    if len(n) == 1 and ("a" <= n <= "z" or n == "ñ"):
        return ord(n) if n != "ñ" else None
    if n.startswith("f") and n[1:].isdigit() and 2 <= int(n[1:]) <= 11:
        return pygame.K_F1 + int(n[1:]) - 1
    return None


def textos(cfg, texto):
    """Las teclas que nombra una frase («pulsa Q», «la tecla M», «press F»), dichas con la que has puesto tú si la
    cambiaste (foro, 1.7.6): el tutorial, las misiones y los avisos nombran tu tecla, no la de serie."""
    import re
    if not texto or not isinstance(texto, str) or not cfg["teclas"]:
        return texto
    m = _mapa(cfg)
    if not m:
        return texto
    tecla = r"(?P<tecla>Intro|Espacio|Tabulador|coma|Enter|Space|Tab|comma|F(?:[2-9]|1[01])|[A-ZÑ])(?![\wáéíóúñ])"
    puestas = []                       # lo ya cambiado queda apartado: con dos teclas intercambiadas no se deshace

    def cambia(x):
        k = _codigo_txt(x.group("tecla"))
        nueva = m.get(k) if k is not None else None
        if nueva is None:
            return x.group(0)
        n = nombre(nueva)
        puestas.append(n[:1].upper() + n[1:])
        return x.group(0)[:x.start("tecla") - x.start(0)] + f"\x00{len(puestas) - 1}\x00" + x.group(0)[x.end("tecla") - x.start(0):]
    patrones = (
        r"\b(?:[Pp]uls(?:a|ar|as|ando|es|ada)|[Cc]on|[Uu]sa|[Mm]antén(?: pulsad[ao])?|[Tt]oca) (?:(?:la|el) )?(?:tecla )?(?:Mayúsculas (?:más |\+ )?(?:la )?)?" + tecla,
        r"\b(?:[Ll]a|[Ee]l) tecla " + tecla,
        r"(?<![\wáéíóúñ])(?:y|o|ni) (?:la )?" + tecla.replace(r"(?![\wáéíóúñ])", "") + r" para(?![\wáéíóúñ])",
        r"\b(?:[Pp]ress(?:ing|es|ed)?|[Ww]ith|[Uu]se|[Hh]old(?:ing)?(?: down)?|[Tt]ap) (?:the )?(?:Shift (?:\+ |plus )?)?" + tecla,
        r"\b[Tt]he " + tecla.replace(r"(?![\wáéíóúñ])", "") + r" key\b",
        r"(?<![\w])(?:and|or|nor) (?:the )?" + tecla.replace(r"(?![\wáéíóúñ])", "") + r"(?: key)? to(?![\w])",
    )
    original = texto
    try:
        for pat in patrones:
            texto = re.sub(pat, cambia, texto)
    except re.error:
        return original
    return re.sub("\x00(\\d+)\x00", lambda x: puestas[int(x.group(1))], texto)


def cambios(cfg):
    """Frases con lo cambiado, para la ayuda: «La función de la C está ahora en la P»."""
    return [tr('Lo que hacía {nombre} se hace ahora con {nombre2}').format(nombre=(nombre(a)), nombre2=(nombre(b))) for a, b in sorted(_mapa(cfg).items())]


class Captura:
    """Pantalla que espera a que el jugador pulse la tecla que quiere usar. Escape cancela."""
    pausa_mundo = True

    def __init__(self, app, titulo, al_elegir):
        self.app, self.titulo, self.al_elegir = app, titulo, al_elegir

    def al_entrar(self):
        self.app.decir(tr('{titulo}. Pulsa la tecla que quieres usar. Escape cancela.').format(titulo=(self.titulo)), True)

    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            self.app.son("menu_atras")
            self.app.cerrar(self)
            self.app.decir(tr("Cancelado."), True)
            return
        if k in FIJAS:
            self.app.son("error")
            self.app.decir(tr('{capitalize} no se puede usar: está reservada. Pulsa otra, o Escape para cancelar.').format(capitalize=(nombre(k).capitalize())), True)
            return
        self.app.cerrar(self)
        self.al_elegir(k)

    def actualizar(self, dt):
        pass

    def cerrado(self):
        pass


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False


if _pl():
    NOMBRES.update({pygame.K_SPACE: "spacja", pygame.K_TAB: "Tab", pygame.K_BACKSPACE: "Backspace", pygame.K_COMMA: "przecinek",
                    pygame.K_PERIOD: "kropka", pygame.K_MINUS: "myślnik", pygame.K_SLASH: "ukośnik", pygame.K_HOME: "Home",
                    pygame.K_END: "End", pygame.K_INSERT: "Insert", pygame.K_DELETE: "Delete", pygame.K_QUOTE: "akcent",
                    pygame.K_RIGHTBRACKET: "plus"})
    ETIQUETAS.update({"spacja": pygame.K_SPACE, "tab": pygame.K_TAB, "backspace": pygame.K_BACKSPACE,
                      "strzałka w górę": pygame.K_UP, "strzałka w dół": pygame.K_DOWN})
