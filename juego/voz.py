"""Salida de voz y braille mediante el lector de pantalla (NVDA, JAWS...) o SAPI."""
from .i18n import tr
import re
import sys
import threading
import time
from collections import deque

from . import genero, palabras, registro


class _SalidaPrism:
    """Screen reader output for Linux through prismatoid (``import prism``).

    Prism talks to whatever the player is using: the running screen reader (Orca, Speech Dispatcher,
    Spiel...) or a speech engine as a fallback. It is wrapped here behind the same speak/braille
    interface that accessible_output2 offers on Windows, so the rest of the class does not need to
    know which platform it is on. A Prism backend is not thread-safe, so every call is serialized
    with a lock.
    """

    def __init__(self):
        import prism
        self._contexto = prism.Context()
        self._backend = self._contexto.create_best()
        self._candado = threading.Lock()

    def speak(self, texto, interrupt=False):
        with self._candado:
            if texto:
                self._backend.speak(texto, interrupt=bool(interrupt))
            else:
                self._backend.stop()

    def braille(self, texto):
        try:
            with self._candado:
                self._backend.braille(texto)
        except Exception:
            pass

    def callar(self):
        with self._candado:
            self._backend.stop()


# Mientras repasas el historial, los mensajes que llegan no te llevan al final: si no, con el GPS o los partes del día
# hablando, Re Pág se quedaba siempre en el mismo mensaje. Se deja de repasar al llegar al último o tras este rato quieto.
REPASO_PAUSA = 20.0


# Con poco detalle se quitan las frases que solo explican qué tecla pulsar: quien ya conoce el juego no las necesita.
_INSTRUCCION = re.compile(tr(r"^(Pulsa |Usa las flechas|Abre el móvil|Con la tecla|Intro para|Escape para|Flechas |F1 |Cámbialo|Elige |Para |Puedes |Recuerda)"), re.I)


def resumir(texto):
    """El mismo mensaje sin las frases de instrucciones. Si todo eran instrucciones, se deja como estaba."""
    partes = re.split(r"(?<=[.!?])\s+", texto)
    quedan = [f for f in partes if not _INSTRUCCION.match(f)]
    return " ".join(quedan) if quedan else texto


class Voz:
    def __init__(self, sapi=False, muda=False):
        self.historial = deque(maxlen=300)
        self.cursor = 0
        self.repaso_t = -1e9         # cuándo se pulsó por última vez Re Pág o Av Pág
        # Aparte, solo lo que dicen los demás jugadores y el servidor (chat, avisos, quién entra y sale): se repasa con
        # Mayúsculas Re Pág y Av Pág sin que se mezcle con las teclas y los menús.
        self.mensajes = deque(maxlen=100)
        self.cursor_msj = 0
        self.muda = muda
        self.salida = None
        self.registro = []          # usado por las pruebas
        self.al_hablar = None       # función(texto): el juego baja el ambiente mientras se habla
        self.detalle = "normal"     # mucho, normal o poco
        self.sapi = sapi
        self._ajustes = (0, 0, 100)
        if not muda:
            self._iniciar(sapi)

    def _iniciar(self, sapi):
        try:
            if sys.platform == "linux":
                # Linux: prismatoid talks to the running screen reader (or a speech engine as a fallback).
                self.salida = _SalidaPrism()
                self.sapi = False
            elif sapi:
                from accessible_output2.outputs.sapi5 import SAPI5
                self.salida = SAPI5()
                self.sapi = True
                self.ajustar_sapi(*self._ajustes)
            else:
                from accessible_output2.outputs.auto import Auto
                self.salida = Auto()
                self.sapi = False
        except Exception:
            registro.excepcion("voz", "No se pudo abrir la salida de voz")
            self.salida = None

    def cambiar(self, sapi):
        self._iniciar(sapi)

    def ajustar_sapi(self, velocidad, tono, volumen):
        """Velocidad, tono y volumen de la voz de Windows. Con un lector de pantalla no hace nada: eso se ajusta en el lector."""
        self._ajustes = (velocidad, tono, volumen)
        s = self.salida
        if not self.sapi or s is None or self.muda:
            return
        for poner, valor, minimo, maximo in ((getattr(s, "set_rate", None), velocidad, -10, 10), (getattr(s, "set_pitch", None), tono, -10, 10),
                                             (getattr(s, "set_volume", None), volumen, 0, 100)):
            try:
                if poner is not None:
                    poner(max(minimo, min(maximo, int(valor))))
            except Exception:
                pass

    def decir(self, texto, interrumpir=False, guardar=True, hablar=True):
        """Dice un texto. Los avisos del juego no interrumpen; los menús sí."""
        if not texto:
            return
        texto = genero.resolver(str(texto))          # «Bienvenid[o|a]» queda como le corresponde al protagonista
        texto = palabras.pulir(texto)                # en otro idioma, ninguna palabra suelta en español
        if self.detalle == "poco":
            texto = resumir(texto)
        registro.voz(texto)
        if self.al_hablar is not None:
            self.al_hablar(texto)
        if guardar:
            self._guardar(texto)
        if self.muda:
            self.registro.append(texto)
            if len(self.registro) > 2000:
                del self.registro[:1000]
            return
        if self.salida is None or not hablar:
            return
        try:
            self.salida.speak(texto, interrupt=interrumpir)
            try:
                self.salida.braille(texto)
            except Exception:
                pass
        except Exception:
            pass

    def mostrar(self, texto):
        """Para cuando suena una voz grabada: el texto no se lee, pero va al braille, al historial y al registro."""
        texto = genero.resolver(str(texto))
        texto = palabras.pulir(texto)
        registro.voz(texto)
        self._guardar(texto)
        if self.muda:
            self.registro.append(texto)
            return
        self.callar()
        if self.salida is not None:
            try:
                self.salida.braille(texto)
            except Exception:
                pass

    def callar(self):
        if self.salida is not None and not self.muda:
            try:
                self.salida.speak("", interrupt=True)
            except Exception:
                pass

    def _guardar(self, texto):
        """Un mensaje al historial. Con la opción de seguir al final (la de siempre), el repaso salta a él; si no, y
        estabas repasando, te quedas en el mismo mensaje."""
        al_final = self.cursor >= len(self.historial) - 1
        lleno = len(self.historial) == self.historial.maxlen
        self.historial.append(texto)
        cfg = getattr(self, "cfg", None)
        if self.repasando():
            if lleno:
                self.cursor = max(0, self.cursor - 1)           # el más antiguo se ha ido: el tuyo está un puesto antes
        elif al_final or cfg is None or cfg["historial_al_final"]:
            self.cursor = len(self.historial) - 1
        elif lleno:
            self.cursor = max(0, self.cursor - 1)               # el más antiguo se ha ido: el tuyo está un puesto antes

    def apuntar_mensaje(self, texto):
        """Un mensaje de otro jugador o del servidor, a su historial aparte. Se dice como siempre; esto solo lo guarda."""
        if not texto:
            return
        texto = palabras.pulir(genero.resolver(str(texto)))
        al_final = self.cursor_msj >= len(self.mensajes) - 1
        self.mensajes.append(texto)
        if al_final:
            self.cursor_msj = len(self.mensajes) - 1

    def repasar_mensajes(self, delta):
        """Mayúsculas Re Pág, Av Pág y punto: el anterior, el siguiente o el último de los mensajes de los jugadores y del
        servidor. Lo que se dice al repasar no entra en ningún historial."""
        if not self.mensajes:
            self.decir(tr("Todavía no hay mensajes de otros jugadores ni del servidor."), True, False)
            return
        if delta == 0:
            self.cursor_msj = len(self.mensajes) - 1
            self.decir(tr("Último mensaje. ") + self.mensajes[self.cursor_msj], True, False)
            return
        nuevo = self.cursor_msj + delta
        if nuevo < 0 or nuevo >= len(self.mensajes):
            self.decir((tr("Primer mensaje. ") if nuevo < 0 else tr("Último mensaje. ")) + self.mensajes[self.cursor_msj], True, False)
            return
        self.cursor_msj = nuevo
        self.decir(self.mensajes[nuevo], True, False)

    def repasando(self):
        return time.monotonic() - self.repaso_t < REPASO_PAUSA

    def _marcar_repaso(self):
        """Al llegar al último mensaje dejas de repasar: los nuevos vuelven a llevarte al final."""
        self.repaso_t = -1e9 if self.cursor >= len(self.historial) - 1 else time.monotonic()

    def repasar_extremo(self, al_final):
        """Control Re Pág y Control Av Pág: el primer mensaje del historial, o el último."""
        if not self.historial:
            self.decir(tr("No hay mensajes."), True, False)
            return
        self.cursor = len(self.historial) - 1 if al_final else 0
        self._marcar_repaso()
        self.decir((tr("Último. ") if al_final else tr("Primero. ")) + self.historial[self.cursor], True, False)

    def repasar(self, delta):
        """Recorre el historial de mensajes (delta -1 anterior, +1 siguiente, 0 repetir)."""
        if not self.historial:
            self.decir(tr("No hay mensajes."), True, False)
            return
        nuevo = self.cursor + delta
        self.cursor = max(0, min(len(self.historial) - 1, nuevo))
        self._marcar_repaso()
        # Si ya no hay más, se dice: así se sabe que la tecla ha llegado al borde y no que no responde.
        borde = tr("Primero. ") if nuevo < 0 else tr("Último. ") if delta > 0 and nuevo > self.cursor else ""
        self.decir(borde + self.historial[self.cursor], True, False)

    def ultimo(self):
        return self.historial[-1] if self.historial else ""
