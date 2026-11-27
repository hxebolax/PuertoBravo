"""Menús y diálogos hablados. Todo se maneja con flechas, Intro y Escape."""
from .i18n import tr
import unicodedata

import pygame
from . import registro


def _dice_menu(app, texto):
    """Lo que se lee al abrir un menú o al moverse por él: vuelve a oírse al volver, así que no llena el historial."""
    f = getattr(app, "decir_menu", None)
    if f is not None:
        f(texto)
    else:
        app.decir(texto, True)


def _llana(letra):
    """Una letra en minúscula y sin tilde, para saltar por inicial: la eñe sigue siendo eñe."""
    letra = letra.lower()
    return letra if letra == "ñ" else unicodedata.normalize("NFD", letra)[:1]


class Opcion:
    def __init__(self, texto, accion=None, ajuste=None, ayuda=None, callado=False):
        self.callado = callado    # al elegirla no suena el toque de menú: para opciones que hacen sonar algo
        self._texto = texto
        self.accion = accion
        self.ajuste = ajuste      # función(delta) para opciones que se cambian con izquierda/derecha
        self.ayuda = ayuda

    @property
    def texto(self):
        return self._texto() if callable(self._texto) else self._texto


# Si la última opción de un menú empieza por una de estas palabras, el menú ya tiene su forma de volver.
SALIDAS = (tr("Volver"), tr("Salir"), tr("Dejarlo"), tr("Cancelar"), tr("Seguir"), tr("Cerrar"), tr("No"), tr("Despedirte"), tr("Colgar"), tr("Marcharte"), tr("Irte"), tr("Ahora no"), tr("Más tarde"),
           tr("Continuar"), tr("Levantarte"), tr("Plantarte"), tr("Retirarte"), tr("Terminar"), tr("Reanudar"))


class Menu:
    pausa_mundo = True
    antes = None                           # una frase que se dice una sola vez, delante del título, al volver a este menú

    def __init__(self, app, titulo, opciones, al_cerrar=None, escapable=True, intro=None):
        self.app = app
        self._titulo = titulo
        self._fuente = opciones            # lista o función que devuelve la lista
        self.opciones = []
        self.i = 0
        self.al_cerrar = al_cerrar
        self.escapable = escapable
        self.intro = intro
        self.refrescar(False)

    @property
    def titulo(self):
        return self._titulo() if callable(self._titulo) else self._titulo

    def refrescar(self, hablar=True):
        self.opciones = list(self._fuente() if callable(self._fuente) else self._fuente)
        # Todo menú del que se puede salir con Escape tiene también, al final, una opción para volver.
        if self.escapable and not any(o.texto.startswith(SALIDAS) for o in self.opciones[-2:]):
            self.opciones.append(Opcion(tr("Volver"), self._volver, ayuda=tr("Vuelve atrás. También sirve Escape.")))
        self.i = max(0, min(self.i, len(self.opciones) - 1))
        if hablar:
            self.leer()

    def _volver(self):
        self.app.cerrar(self)

    def al_entrar(self):
        self.refrescar(False)
        partes = [self.titulo]
        if self.antes:
            partes.insert(0, self.antes)
            self.antes = None
        if self.intro:
            partes.append(self.intro)
            self.intro = None
        if self.opciones:
            partes.append(tr('{texto}. {v} de {len}').format(texto=(self.opciones[self.i].texto), v=(self.i + 1), len=(len(self.opciones))))
        _dice_menu(self.app, ". ".join(partes))

    def leer(self):
        if self.opciones:
            pos = tr('. {v} de {len}').format(v=(self.i + 1), len=(len(self.opciones))) if self.app.cfg["menu_posicion"] else ""
            o = self.opciones[self.i]
            extra = f". {o.ayuda}" if self.app.cfg["detalle_voz"] == "mucho" and getattr(o, "ayuda", None) else ""      # con mucho detalle, la explicación va detrás
            _dice_menu(self.app, o.texto + pos + extra)

    def _mover(self, nuevo):
        n = len(self.opciones)
        if n == 0:
            return
        if nuevo < 0 or nuevo >= n:
            self.app.son("menu_borde")
            nuevo %= n
        else:
            self.app.son("menu_mover")
        self.i = nuevo
        self.leer()

    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_DOWN:
            self._mover(self.i + 1)
        elif k == pygame.K_UP:
            self._mover(self.i - 1)
        elif k == pygame.K_HOME:
            self.app.son("menu_mover")
            self.i = 0
            self.leer()
        elif k == pygame.K_END:
            self.app.son("menu_mover")
            self.i = max(0, len(self.opciones) - 1)
            self.leer()
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if not self.opciones:
                return
            o = self.opciones[self.i]
            if o.accion:
                if not o.callado:
                    self.app.son("menu_ok")
                o.accion()
            elif o.ajuste:
                self.app.son("menu_ajuste")
                o.ajuste(1)
                self.leer()
            else:
                self.leer()
        elif k in (pygame.K_LEFT, pygame.K_RIGHT):
            if self.opciones and self.opciones[self.i].ajuste:
                self.app.son("menu_ajuste")
                self.opciones[self.i].ajuste(1 if k == pygame.K_RIGHT else -1)
                self.leer()
        elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            if self.escapable:
                self.app.son("menu_atras")
                self.app.cerrar(self)
        elif k == pygame.K_F1:
            if self.opciones and self.opciones[self.i].ayuda:
                _dice_menu(self.app, self.opciones[self.i].ayuda)
            elif self.opciones and self.opciones[self.i].texto.startswith(SALIDAS):
                _dice_menu(self.app, tr("Sale de este menú y vuelve a donde estabas. También sirve Escape."))
            else:
                _dice_menu(self.app, tr("Flechas arriba y abajo para moverte, Intro para elegir, izquierda y derecha para cambiar un valor, Escape para volver."))
        elif k in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) and getattr(ev, "mod", 0) & pygame.KMOD_CTRL:
            self.app.voz.repasar_extremo(k == pygame.K_PAGEDOWN)
        elif k in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) and getattr(ev, "mod", 0) & pygame.KMOD_SHIFT:
            self.app.voz.repasar_mensajes(-1 if k == pygame.K_PAGEUP else 1)
        elif k == pygame.K_PAGEUP:
            self.app.voz.repasar(-1)
        elif k == pygame.K_PAGEDOWN:
            self.app.voz.repasar(1)
        elif k == pygame.K_PERIOD:
            self.leer()
        else:
            letra = _llana((getattr(ev, "unicode", "") or "")[:1])
            if letra and letra.isalnum():
                n = len(self.opciones)
                for d in range(1, n + 1):
                    q = (self.i + d) % n
                    if _llana(self.opciones[q].texto[:1]) == letra:           # la A lleva también a lo que empieza por Á
                        self.app.son("menu_mover")
                        self.i = q
                        self.leer()
                        break

    def actualizar(self, dt):
        pass

    def cerrado(self):
        if self.al_cerrar:
            self.al_cerrar()


class Dialogo:
    """Escena de texto: Intro avanza, flecha arriba repite, Escape la salta entera."""
    pausa_mundo = True

    def __init__(self, app, lineas, al_terminar=None, voces=None):
        self.app = app
        self.lineas = [tuple(l) for l in lineas]
        self.i = 0
        self.al_terminar = al_terminar
        self.primera = True
        self.voces = voces              # una grabación por frase, o None donde no hay
        self.canal = None

    def _callar_voz(self):
        if self.canal is not None:
            self.canal.parar()
            self.canal = None

    def _decir(self):
        quien, texto = self.lineas[self.i]
        self._callar_voz()
        self.app.son("dialogo")
        extra = ""
        if self.primera:
            extra = tr(" Pulsa Intro para continuar.")
            self.primera = False
        frase = (texto if quien in ("Narrador", tr("Narrador")) else f"{quien}: {texto}") + extra
        md = getattr(self.app, "mando", None)
        original = frase
        if md is not None:
            frase = md.textos(frase)                 # con mando: «pulsa Q» se dice con el botón que hace lo mismo
        from . import teclado
        frase = teclado.textos(self.app.cfg, frase)  # y con tus teclas, si has cambiado alguna
        grabada = self.voces[self.i] if self.voces and self.i < len(self.voces) else None
        if frase != original:
            grabada = None                           # la grabación nombra la tecla: esta frase la lee el lector, con el botón
        if grabada and self.app.cfg["voces_grabadas"]:
            from . import voces
            self.canal = voces.sonar(self.app, grabada)
            if self.canal is not None:
                self.app.voz.mostrar(frase)          # la voz es la grabación; el texto va al braille y al historial
                return
        self.app.decir(frase, True)

    def al_entrar(self):
        if self.i < len(self.lineas):
            self._decir()
        else:
            self._fin()

    def _fin(self):
        self._callar_voz()
        self.app.cerrar(self)

    def cerrado(self):
        self._callar_voz()
        if self.al_terminar:
            f = self.al_terminar
            self.al_terminar = None
            f()

    def tecla(self, ev):
        k = ev.key
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_DOWN, pygame.K_RIGHT):
            self.i += 1
            if self.i >= len(self.lineas):
                self._fin()
            else:
                self._decir()
        elif k in (pygame.K_UP, pygame.K_r, pygame.K_PERIOD):
            self._decir()
        elif k == pygame.K_LEFT:
            self.i = max(0, self.i - 1)
            self._decir()
        elif k == pygame.K_ESCAPE:
            self.app.voz.callar()
            self._fin()
        elif k in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) and getattr(ev, "mod", 0) & pygame.KMOD_CTRL:
            self.app.voz.repasar_extremo(k == pygame.K_PAGEDOWN)
        elif k in (pygame.K_PAGEUP, pygame.K_PAGEDOWN) and getattr(ev, "mod", 0) & pygame.KMOD_SHIFT:
            self.app.voz.repasar_mensajes(-1 if k == pygame.K_PAGEUP else 1)
        elif k == pygame.K_PAGEUP:
            self.app.voz.repasar(-1)
        elif k == pygame.K_PAGEDOWN:
            self.app.voz.repasar(1)

    def actualizar(self, dt):
        pass


class EntradaTexto:
    """Pide un texto por teclado, diciendo en voz alta cada letra que se escribe.

    Intro acepta, Escape cancela, Retroceso borra, flecha arriba o F1 leen lo escrito y Control V pega.
    Con secreto=True (contraseñas) no se dicen las letras.

    Con «propuestas» (una lista de textos, o una función que la da), Tabulador pasa de una a otra y la deja escrita:
    frases hechas, nombres al azar. Sirve para no tener que escribir.

    Con mando se escribe con una rueda de letras: cruceta arriba y abajo recorren las letras, derecha escribe la elegida
    e izquierda borra la última; LB o L1 pone un espacio, RB o R1 cambia de grupo (minúsculas, mayúsculas, números y
    signos), X o Cuadrado pasa por las propuestas, Y o Triángulo lee lo escrito, A o Equis acepta y B o Círculo cancela.
    """
    pausa_mundo = True
    cerrado_al_final = True
    GRUPOS = (("minúsculas", "abcdefghijklmnñopqrstuvwxyzáéíóúü"), ("mayúsculas", tr("ABCDEFGHIJKLMNÑOPQRSTUVWXYZÁÉÍÓÚÜ")), ("números", "0123456789"),
              ("signos", ".,?!¿¡/-:;@_'\"()+="))

    def __init__(self, app, titulo, al_aceptar, inicial="", secreto=False, maximo=120, ayuda=None, propuestas=None):
        self.app = app
        self.titulo = titulo
        self.al_aceptar = al_aceptar
        self.texto = inicial or ""
        self.secreto = secreto
        self.maximo = maximo
        self.ayuda = ayuda
        self.aceptado = False
        self._propuestas = propuestas
        self.i_prop = -1
        self.grupo = 0               # la rueda de letras del mando: en qué grupo y en qué letra está
        self.letra = 0

    def _leer(self):
        if not self.texto:
            return tr("Vacío")
        return tr('{len} caracteres escritos').format(len=(len(self.texto))) if self.secreto else self.texto

    def propuestas(self):
        try:
            p = self._propuestas() if callable(self._propuestas) else self._propuestas
        except Exception:
            p = None
        return [str(t)[:self.maximo] for t in (p or []) if str(t).strip()]

    def _con_mando(self):
        md = getattr(self.app, "mando", None)
        return md if md is not None and md.conectado else None

    def ayuda_mando(self):
        """Cómo se escribe con el mando, con los nombres de sus botones."""
        md = self._con_mando()
        n = md.nombre_boton if md else (lambda b: {"a": tr("A o Equis"), "b": tr("B o Círculo"), "x": tr("X o Cuadrado"), "y": tr("Y o Triángulo"), "lb": tr("LB o L1"), "rb": tr("RB o R1")}[b])
        return (tr('Con el mando: cruceta arriba y abajo recorren las letras, cruceta derecha escribe la letra elegida y cruceta izquierda borra la última. {n} pone un espacio. {n2} cambia entre minúsculas, mayúsculas, números y signos. ').format(n=(n('lb')), n2=(n('rb')))
                + (tr('{n} pasa por las propuestas. ').format(n=(n('x'))) if self.propuestas() else "")
                + tr('{n} lee lo escrito. {n2} acepta y {n3} cancela.').format(n=(n('y')), n2=(n('a')), n3=(n('b'))))

    def al_entrar(self):
        with registro.privado():
            self._al_entrar()

    def _al_entrar(self):
        hay = len(self.propuestas())
        md = self._con_mando()
        if md is not None and md.habla_botones():
            n = md.nombre_boton
            como = (tr('Elige cada letra con la cruceta arriba y abajo y escríbela con cruceta derecha. {n} acepta y {n2} cancela. ').format(n=(n('a')), n2=(n('b')))
                    + (tr('{n} pasa por {hay} propuestas ya escritas. ').format(n=(n('x')), hay=(hay)) if hay else "") + tr('El {n} dice todos los botones.').format(n=(n('back'))))
        else:
            como = tr("Escribe y pulsa Intro. Escape cancela.") + (tr(' Tabulador pasa por {hay} propuestas ya escritas.').format(hay=(hay)) if hay else "")
        _dice_menu(self.app, f"{self.titulo}. {como} {self._leer()}")

    def tecla(self, ev):
        with registro.privado():               # lo que se escribe y lo que se lee al escribir no se registra
            self._tecla(ev)

    def _proponer(self, paso=1):
        lista = self.propuestas()
        if not lista:
            self.app.son("menu_borde")
            _dice_menu(self.app, tr("Aquí no hay propuestas: hay que escribirlo."))
            return
        self.i_prop = (self.i_prop + paso) % len(lista)
        self.texto = lista[self.i_prop]
        self.app.son("menu_ajuste")
        _dice_menu(self.app, tr('{texto}. {v} de {len}').format(texto=(self.texto), v=(self.i_prop + 1), len=(len(lista))))

    def _poner(self, letra):
        if len(self.texto) >= self.maximo:
            self.app.son("menu_borde")
            _dice_menu(self.app, tr("No cabe más."))
            return
        self.texto += letra
        self.app.son("menu_mover")
        _dice_menu(self.app, "asterisco" if self.secreto else self._nombre(letra))

    def _borrar(self):
        if self.texto:
            quitada = self.texto[-1]
            self.texto = self.texto[:-1]
            self.app.son("menu_ajuste")
            _dice_menu(self.app, tr("Borrado") if self.secreto else tr('Borrado {_nombre}').format(_nombre=(self._nombre(quitada))))
        else:
            self.app.son("menu_borde")
            _dice_menu(self.app, tr("Vacío"))

    def _rueda(self, k):
        """Las teclas que llegan del mando: la rueda de letras. Devuelve False si esa no es de la rueda."""
        letras = self.GRUPOS[self.grupo][1]
        if k in (pygame.K_UP, pygame.K_DOWN):
            self.letra = (self.letra + (1 if k == pygame.K_DOWN else -1)) % len(letras)
            self.app.son("menu_mover")
            _dice_menu(self.app, self._nombre(letras[self.letra]))
        elif k == pygame.K_RIGHT:
            self._poner(letras[self.letra])
        elif k == pygame.K_LEFT:
            self._borrar()
        elif k == pygame.K_HOME:                                 # LB o L1
            self._poner(" ")
        elif k == pygame.K_d:                                    # RB o R1
            self.grupo = (self.grupo + 1) % len(self.GRUPOS)
            self.letra = 0
            self.app.son("menu_ajuste")
            _dice_menu(self.app, f"{self.GRUPOS[self.grupo][0].capitalize()}. {self._nombre(self.GRUPOS[self.grupo][1][0])}")
        elif k == pygame.K_n:                                    # Y o Triángulo
            _dice_menu(self.app, self._leer())
        elif k == pygame.K_F1:                                   # Vista, Crear o Share
            _dice_menu(self.app, (self.ayuda + " " if self.ayuda else "") + self.ayuda_mando() + " " + self._leer())
        else:
            return False
        return True

    def _tecla(self, ev):
        k = ev.key
        mod = getattr(ev, "mod", 0)
        if getattr(ev, "mando", False) and self._rueda(k):
            return
        if k == pygame.K_TAB:
            self._proponer(-1 if mod & pygame.KMOD_SHIFT else 1)
            return
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.aceptado = True
            self.app.son("menu_ok")
            self.app.cerrar(self)
        elif k == pygame.K_ESCAPE:
            self.app.son("menu_atras")
            _dice_menu(self.app, tr("Cancelado."))
            self.app.cerrar(self)
        elif k == pygame.K_BACKSPACE:
            if self.texto:
                quitada = self.texto[-1]
                self.texto = self.texto[:-1]
                self.app.son("menu_ajuste")
                _dice_menu(self.app, tr("Borrado") if self.secreto else tr('Borrado {_nombre}').format(_nombre=(self._nombre(quitada))))
            else:
                self.app.son("menu_borde")
                _dice_menu(self.app, tr("Vacío"))
        elif k in (pygame.K_UP, pygame.K_F1):
            _dice_menu(self.app, (self.ayuda + " " if self.ayuda and k == pygame.K_F1 else "") + self._leer())
        elif k == pygame.K_v and mod & pygame.KMOD_CTRL:
            try:
                pegado = pygame.scrap.get_text() or ""
            except Exception:
                pegado = ""
            pegado = "".join(c for c in pegado if c.isprintable())
            if pegado:
                self.texto = (self.texto + pegado)[:self.maximo]
                _dice_menu(self.app, tr("Pegado. ") + self._leer())
            else:
                self.app.son("error")
                _dice_menu(self.app, tr("No hay texto en el portapapeles."))
        else:
            letra = getattr(ev, "unicode", "") or ""
            if letra and letra.isprintable() and not (mod & (pygame.KMOD_CTRL | pygame.KMOD_ALT) and not (mod & pygame.KMOD_MODE)):
                if len(self.texto) >= self.maximo:
                    self.app.son("menu_borde")
                    return
                self.texto += letra
                self._eco = letra                    # el mismo carácter llegará enseguida como texto: no se escribe dos veces
                self.app.son("menu_mover")
                _dice_menu(self.app, "asterisco" if self.secreto else self._nombre(letra))

    def texto_tecleado(self, texto):
        """El texto que manda el teclado aparte de la pulsación (ver App.evento_texto). Lo que ya se escribió con la
        pulsación llega aquí repetido y se ignora; lo demás (una vocal con tilde, una letra de un método de entrada) se escribe."""
        with registro.privado():
            eco, self._eco = getattr(self, "_eco", None), None
            if not texto or texto == eco:
                return
            texto = "".join(c for c in texto if c.isprintable())
            if not texto:
                return
            if len(self.texto) >= self.maximo:
                self.app.son("menu_borde")
                return
            texto = texto[:self.maximo - len(self.texto)]
            self.texto += texto
            self.app.son("menu_mover")
            _dice_menu(self.app, "asterisco" if self.secreto else (self._nombre(texto) if len(texto) == 1 else texto))

    @staticmethod
    def _nombre(c):
        return {" ": "espacio", ".": "punto", ":": tr("dos puntos"), "/": "barra", ",": "coma", "-": "guion", "_": tr("guion bajo"), "@": "arroba",
                "?": "interrogación", "!": "exclamación", "¿": tr("abre interrogación"), "¡": tr("abre exclamación"), ";": tr("punto y coma"), "'": "apóstrofo",
                '"': "comillas", "(": tr("abre paréntesis"), ")": tr("cierra paréntesis"), "+": "más", "=": "igual"}.get(c, tr('{c} mayúscula').format(c=(c)) if c.isupper() else c)

    def actualizar(self, dt):
        pass

    def cerrado(self):
        if self.aceptado and self.al_aceptar:
            f = self.al_aceptar
            self.al_aceptar = None
            f(self.texto)
