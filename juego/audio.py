"""Mezclador de audio 3D propio.

Cada sonido se coloca alrededor del oyente con panorama de potencia constante,
diferencia de tiempo entre oídos, atenuación por distancia y un filtro que
apaga los sonidos que quedan detrás o lejos. Todo se mezcla con numpy y sale
por sounddevice, de modo que también se puede variar el tono (motores, sirenas).

La salida (1.7.4): la de Windows por defecto, siguiéndola si cambia, o la que elija el jugador; si se desconecta, se
vuelve a abrir sola donde toque (salidas.py). Y, si se pide, una segunda salida con lo mismo, para grabar o retransmitir.
"""
import collections
import math
import threading
import time

import numpy as np
from . import registro

SR = 44100
ITD_MAX = 28.0      # muestras de retardo máximo entre oídos
PAD = 32


def apagar(x, corte=900.0):
    """Versión apagada de un sonido (pasa bajos por FFT)."""
    n = len(x)
    if n < 8:
        return x.copy()
    X = np.fft.rfft(x, axis=0)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    g = 1.0 / (1.0 + (f / corte) ** 2)
    if x.ndim == 2:
        g = g[:, None]
    return np.fft.irfft(X * g, n, axis=0).astype(np.float32)


# Los sonidos que son señales de ayuda para orientarse: llevan su propio volumen, aparte del de su categoría.
SENALES = ("baliza", "radar", "tono_", "loc_", "sonar", "lugar_", "semaforo", "cruce", "norte")


class Canal:
    """Un sonido en reproducción."""

    def __init__(self):
        self.nombre = ""
        self.datos = None
        self.apag = None
        self.largo = 0
        self.pos = 0.0
        self.rate = 1.0
        self.rate_obj = 1.0
        self.bucle = False
        self.vol = 1.0
        self.cat = "efectos"
        self.xy = None          # posición en el mundo o None si es 2D
        self.pan = 0.0
        self.ref = 5.0
        self.maxd = 70.0
        self.gl = self.gr = 0.0
        self.gl_obj = self.gr_obj = 0.0
        self.dl = self.dr = 0.0
        self.dl_obj = self.dr_obj = 0.0
        self.muf = self.muf_obj = 0.0
        self.parando = False
        self.fin = False
        self.estereo = False
        self.nuevo = True
        self.senal = False      # es una señal de ayuda (baliza, radar, tono de puntería): tiene su propio volumen
        self.alto = 0.0         # altura sobre el suelo, en metros (solo la usa el motor envolvente)
        self.eco = False        # que le afecte el eco del lugar aunque no sea un efecto del mundo

    def mover(self, x, y):
        self.xy = (x, y)

    def tono(self, r):
        self.rate_obj = max(0.05, float(r))

    def volumen(self, v):
        self.vol = max(0.0, float(v))

    def parar(self):
        self.parando = True

    @property
    def activo(self):
        return not self.fin and not self.parando


HOLGADO = False          # lo pone el juego al arrancar, según la opción Sonido holgado
VIGILAR_CADA = 1.5       # segundos entre cada mirada a la salida de sonido
CORTE = 1.5              # sin que la salida pida sonido en este tiempo, se ha cortado (auriculares desconectados)


class Mezclador:
    def __init__(self, dispositivo=True, bloque=1024, holgado=False, salida="", extra=""):
        self.holgado = bool(holgado or HOLGADO)     # búfer grande y sin prisas: algo más de retardo a cambio de no dar chasquidos
        self.con_dispositivo = bool(dispositivo)     # sin él (las pruebas, o el motor envolvente) no se vigila ninguna salida
        self.salida = str(salida or "")             # la elegida en las opciones (nombre corto de Windows); vacío = la de Windows
        self.extra = str(extra or "")               # segunda salida, con lo mismo, para grabar o retransmitir
        self.nombre_salida = ""                     # la que está sonando de verdad
        self.bloque = bloque
        self._t_cb = 0.0                            # cuándo pidió sonido la salida por última vez
        self._t_vigila = 0.0
        self._defecto_visto = ""
        self.stream_extra = None
        self.nombre_extra = ""
        self._cola_extra = collections.deque()
        self._lock_extra = threading.Lock()
        self.sonidos = {}
        self._var = {}
        self.canales = []
        self._lock = threading.Lock()
        self._ar = np.arange(8192 + PAD, dtype=np.float64)
        self.oyente = (0.0, 0.0, 0.0)
        self.vols = {"maestro": 0.8, "efectos": 1.0, "ambiente": 0.6, "musica": 0.5, "interfaz": 0.8, "senales": 1.0}
        self._lock_cadena = threading.Lock()
        self.diferidos = {}         # sonidos largos que se cargan cuando hacen falta: nombre -> función que los lee
        self._provisional = {}      # lo que suena mientras tanto: el sonido de serie
        self._dif_estado = {}       # nombre -> "cargando" o "listo"
        self.sincrono = False       # en las pruebas se carga al momento, sin hilo
        self.mundo_pausado = False
        self.entorno = "calle"      # dónde está el oyente: decide el eco en el motor envolvente
        self.altura = 0.0           # altura del oyente sobre el suelo: en helicóptero, lo demás suena por debajo
        self.mono = False           # los dos oídos oyen lo mismo: para quien oye por uno solo
        self.atenuar = True         # bajar el ambiente y la música mientras habla la voz
        self.duck = 1.0             # cuánto están bajados ahora mismo (1 = nada)
        self.duck_hasta = 0.0
        self.tono_mundo = 1.0       # multiplica el tono de todos los sonidos del mundo (efectos de sustancias)
        self.stream = None
        self.error = None
        if dispositivo:
            self._abrir(bloque)

    @staticmethod
    def _wasapi(sd, nombre=""):
        """El índice WASAPI de esa salida (por su nombre corto de Windows), o el de la de por defecto si no se da nombre."""
        from . import salidas
        try:
            for h in sd.query_hostapis():
                if "WASAPI" not in h["name"]:
                    continue
                if not nombre:
                    return h["default_output_device"] if h["default_output_device"] >= 0 else None
                for d in h["devices"]:
                    info = sd.query_devices(d)
                    if info["max_output_channels"] > 0 and salidas.coincide(nombre, info["name"]):
                        return d
        except Exception:
            pass
        return None

    def _abrir(self, bloque):
        """Abre la salida de audio: la elegida, si está; si no, la de Windows por WASAPI (unos 20 ms de latencia); y si
        falla, la de por defecto de PortAudio."""
        try:
            import sounddevice as sd
        except Exception as e:
            self.error = str(e)
            return
        from . import salidas
        self._defecto_visto = salidas.por_defecto()
        intentos = []
        try:
            elegida = self._wasapi(sd, self.salida) if self.salida else None
            if elegida is not None:
                intentos.append((elegida, sd.WasapiSettings(auto_convert=True), 2048 if self.holgado else 512))
            defecto = self._wasapi(sd)
            if defecto is not None and defecto != elegida:
                intentos.append((defecto, sd.WasapiSettings(auto_convert=True), 2048 if self.holgado else 512))
        except Exception:
            pass
        intentos.append((None, None, 4096 if self.holgado else bloque))
        for dispositivo, extra, tam in intentos:
            try:
                self.stream = sd.OutputStream(samplerate=SR, channels=2, dtype="float32", blocksize=tam,
                                              callback=self._cb, latency="high" if self.holgado else "low", device=dispositivo, extra_settings=extra)
                self.stream.start()
                self.error = None
                self._t_cb = time.monotonic()
                try:
                    self.nombre_salida = sd.query_devices(self.stream.device)["name"]
                except Exception:
                    self.nombre_salida = ""
                self._abrir_extra(sd)
                return
            except Exception as e:  # sin tarjeta de sonido: el juego sigue, mudo
                self.error = str(e)
                self.stream = None
                registro.aviso("sonido", "No se pudo abrir la salida de sonido con esta configuración", error=e, bloque=tam, exclusivo=bool(extra))

    # ---------------------------------------------------------------- sonidos
    def registrar(self, nombre, datos):
        self.sonidos[nombre] = np.ascontiguousarray(datos, dtype=np.float32)
        for k in [k for k in list(self._var) if k[0] == nombre]:
            self._var.pop(k, None)

    # ---------------------------------------------------------------- sonidos que se cargan cuando hacen falta
    def diferir(self, nombre, leer):
        """Deja un sonido largo sin cargar. Hasta que haga falta, con ese nombre suena el que ya hubiera."""
        if nombre in self.sonidos:
            self._provisional[nombre] = self.sonidos[nombre]
            self.diferidos[nombre] = leer
            self._dif_estado.pop(nombre, None)

    def pedir(self, nombre):
        """Pide un sonido diferido. Devuelve True cuando ya se puede usar; mientras se carga, False."""
        if nombre not in self.diferidos or self._dif_estado.get(nombre) == "listo":
            return True
        if self._dif_estado.get(nombre) != "cargando":
            self._dif_estado[nombre] = "cargando"
            if self.sincrono:
                self._cargar_diferido(nombre)
                return True
            threading.Thread(target=self._cargar_diferido, args=(nombre,), daemon=True).start()
        return False

    def _cargar_diferido(self, nombre):
        try:
            d = self.diferidos[nombre]()
            if d is not None and len(d) > 8:
                self.registrar(nombre, d)
        except Exception:
            registro.excepcion("sonido", "No se pudo cargar un sonido bajo demanda")
        self._dif_estado[nombre] = "listo"                # si falla, se queda con el de serie y no se reintenta

    def soltar(self, salvo=()):
        """Libera la memoria de los sonidos diferidos que ya no suenan, salvo los indicados."""
        with self._lock:
            en_uso = {c.nombre for c in self.canales if not c.fin}
        for nombre in list(self.diferidos):
            if self._dif_estado.get(nombre) == "listo" and nombre not in salvo and nombre not in en_uso:
                self.registrar(nombre, self._provisional[nombre])
                self._dif_estado.pop(nombre, None)

    def memoria_diferidos(self):
        """Megas que ocupan ahora los sonidos diferidos ya cargados."""
        return sum(self.sonidos[n].nbytes for n in self.diferidos if self._dif_estado.get(n) == "listo") / 1048576.0

    def _variante(self, nombre, bucle, apagado):
        clave = (nombre, bucle, apagado)
        v = self._var.get(clave)
        if v is None:
            d = self.sonidos[nombre]
            if apagado:
                d = apagar(d)
            if bucle:
                v = np.concatenate([d, d[:2]])
            else:
                v = np.concatenate([d, np.zeros((2,) + d.shape[1:], np.float32)])
            self._var[clave] = v
        return v

    def duracion(self, nombre):
        d = self.sonidos.get(nombre)
        return 0.0 if d is None else len(d) / SR

    # ------------------------------------------------------------ reproducir
    def posicion(self, c):
        """Por qué muestra va un canal."""
        return float(c.pos)

    def encadenar(self, viejo, nombre, corte, **kw):
        """Hace sonar `nombre` a continuación de un canal que ya suena, alineado con él: la muestra `corte` del viejo es
        la muestra cero del nuevo. Sirve para tocar una canción larga por tramos sin que se note la costura."""
        with self._lock_cadena:
            desde = max(0.0, self.posicion(viejo) - corte) if viejo is not None and not viejo.fin else 0.0
            c = self.sonar(nombre, **kw)
            if not c.fin:
                c.pos = min(desde, max(0.0, c.largo - 1.0))
        return c

    def sonar(self, nombre, vol=1.0, tono=1.0, bucle=False, xy=None, pan=0.0,
              ref=5.0, maxd=70.0, cat="efectos"):
        c = Canal()
        d = self.sonidos.get(nombre)
        if d is None:
            registro.sonido_falta(nombre)
            c.fin = True
            return c
        registro.sonido(nombre)
        with self._lock:
            if len(self.canales) >= 56 and not bucle and cat != "interfaz":
                c.fin = True
                return c
        c.nombre = nombre
        c.senal = nombre.startswith(SENALES)
        c.estereo = d.ndim == 2
        c.largo = len(d)
        c.datos = self._variante(nombre, bucle, False)
        if xy is not None and not c.estereo:
            c.apag = self._variante(nombre, bucle, True)
        c.rate = c.rate_obj = max(0.05, float(tono))
        c.bucle = bucle
        c.vol = vol
        c.cat = cat
        c.xy = xy
        c.pan = pan
        c.ref = ref
        c.maxd = maxd
        self._calcular(c)
        c.gl, c.gr, c.dl, c.dr, c.muf = c.gl_obj, c.gr_obj, c.dl_obj, c.dr_obj, c.muf_obj
        if bucle:
            c.gl = c.gr = 0.0      # los bucles entran con fundido
        with self._lock:
            self.canales.append(c)
        return c

    def situar_oyente(self, x, y, rumbo):
        self.oyente = (x, y, rumbo)

    def hablando(self, texto):
        """La voz va a decir algo: durante lo que tarde, el ambiente y la música bajan para que se entienda."""
        self.duck_hasta = max(self.duck_hasta, time.time() + min(9.0, 0.7 + len(str(texto)) / 15.0))

    def _calcular(self, c):
        g = c.vol * self.vols.get(c.cat, 1.0)
        if c.senal:
            g *= self.vols["senales"]
        if c.cat in ("ambiente", "musica"):
            g *= self.duck
        if c.xy is None:
            p = max(-1.0, min(1.0, c.pan))
            a = (p + 1.0) * math.pi / 4.0
            if c.estereo:
                c.gl_obj = g * min(1.0, 1.0 - p)
                c.gr_obj = g * min(1.0, 1.0 + p)
            else:
                c.gl_obj = g * math.cos(a) * 1.3
                c.gr_obj = g * math.sin(a) * 1.3
            c.dl_obj = c.dr_obj = 0.0
            c.muf_obj = 0.0
            return
        ox, oy, rumbo = self.oyente
        dx = c.xy[0] - ox
        dy = c.xy[1] - oy
        d = math.hypot(dx, dy)
        if self.altura > 0 and c.cat in ("efectos", "ambiente"):    # volando, la calle queda abajo: más lejos cuanto más alto
            d = math.hypot(d, self.altura - c.alto)                  # (las señales y la interfaz, no: con ellas te orientas)
        if d >= c.maxd:
            c.gl_obj = c.gr_obj = 0.0
            return
        if d > c.ref:
            g *= c.ref / (c.ref + 1.2 * (d - c.ref))
        borde = c.maxd * 0.25
        if d > c.maxd - borde:
            g *= (c.maxd - d) / borde
        if d < 0.5:
            p = 0.0
            detras = 0.0
        else:
            rel = math.radians(math.degrees(math.atan2(dx, dy)) - rumbo)
            p = math.sin(rel)
            detras = max(0.0, -math.cos(rel))
            cerca = min(1.0, d / 2.0)
            p *= cerca
            detras *= cerca
        a = (p + 1.0) * math.pi / 4.0
        g *= 1.0 - 0.3 * detras
        c.gl_obj = g * math.cos(a) * 1.3
        c.gr_obj = g * math.sin(a) * 1.3
        c.dl_obj = ITD_MAX * p if p > 0 else 0.0
        c.dr_obj = -ITD_MAX * p if p < 0 else 0.0
        c.muf_obj = min(0.95, 0.7 * detras + 0.45 * min(1.0, d / c.maxd))

    def actualizar(self):
        """Recalcula la posición relativa de todos los sonidos. Una vez por fotograma."""
        self.vigilar()
        with self._lock:
            self.canales = [c for c in self.canales if not c.fin]
            lista = list(self.canales)
        objetivo = 0.45 if self.atenuar and time.time() < self.duck_hasta else 1.0
        self.duck += (objetivo - self.duck) * (0.35 if objetivo < self.duck else 0.08)      # baja rápido y vuelve despacio
        for c in lista:
            self._calcular(c)

    def parar_todo(self, cats=("efectos", "ambiente")):
        with self._lock:
            for c in self.canales:
                if c.cat in cats:
                    c.parando = True

    # ----------------------------------------------------------------- mezcla
    def _leer(self, d, idx, L, bucle):
        if bucle:
            idx = np.mod(idx, L)
        else:
            idx = np.clip(idx, 0.0, float(L))
        i0 = idx.astype(np.int64)
        fr = (idx - i0).astype(np.float32)
        if d.ndim == 2:
            fr = fr[:, None]
        a = d[i0]
        return a + (d[i0 + 1] - a) * fr

    def render(self, n):
        mix = np.zeros((n, 2), np.float32)
        with self._lock:
            lista = list(self.canales)
        rampa = self._ar[:n].astype(np.float32) / max(1, n)
        for c in lista:
            if c.fin:
                continue
            if self.mundo_pausado and c.cat in ("efectos", "ambiente"):
                continue
            c.rate += (c.rate_obj - c.rate) * 0.4
            r = c.rate * self.tono_mundo if c.cat in ("efectos", "ambiente") else c.rate
            L = c.largo
            gl1, gr1 = (0.0, 0.0) if c.parando else (c.gl_obj, c.gr_obj)
            if c.gl < 1e-4 and c.gr < 1e-4 and gl1 < 1e-4 and gr1 < 1e-4 and not c.parando:
                # No se oye (está lejos o con el volumen a cero): avanza sin gastar cálculo. Con muchas sirenas y motores, esto es lo que evita los tirones.
                c.pos += n * r
                if c.bucle:
                    c.pos %= L
                elif c.pos >= L:
                    c.fin = True
                c.dl, c.dr, c.muf = c.dl_obj, c.dr_obj, c.muf_obj
                continue
            if c.estereo or c.xy is None:
                idx = c.pos + self._ar[:n] * r
                s = self._leer(c.datos, idx, L, c.bucle)
                if c.estereo:
                    mix[:, 0] += s[:, 0] * (c.gl + (gl1 - c.gl) * rampa)
                    mix[:, 1] += s[:, 1] * (c.gr + (gr1 - c.gr) * rampa)
                else:
                    mix[:, 0] += s * (c.gl + (gl1 - c.gl) * rampa)
                    mix[:, 1] += s * (c.gr + (gr1 - c.gr) * rampa)
            else:
                idx = c.pos + (self._ar[:n + PAD] - PAD) * r
                s = self._leer(c.datos, idx, L, c.bucle)
                if c.muf > 0.02 or c.muf_obj > 0.02:
                    sm = self._leer(c.apag, idx, L, c.bucle)
                    m = np.empty(n + PAD, np.float32)
                    m[:PAD] = c.muf
                    m[PAD:] = c.muf + (c.muf_obj - c.muf) * rampa
                    s = s + (sm - s) * m
                base = s[PAD:]
                if c.dl > 0.01 or c.dl_obj > 0.01:
                    q = PAD + self._ar[:n] - (c.dl + (c.dl_obj - c.dl) * rampa)
                    izq = np.interp(q, self._ar[:n + PAD], s)
                else:
                    izq = base
                if c.dr > 0.01 or c.dr_obj > 0.01:
                    q = PAD + self._ar[:n] - (c.dr + (c.dr_obj - c.dr) * rampa)
                    der = np.interp(q, self._ar[:n + PAD], s)
                else:
                    der = base
                mix[:, 0] += izq * (c.gl + (gl1 - c.gl) * rampa)
                mix[:, 1] += der * (c.gr + (gr1 - c.gr) * rampa)
                c.dl, c.dr, c.muf = c.dl_obj, c.dr_obj, c.muf_obj
            c.gl, c.gr = gl1, gr1
            c.pos += n * r
            if c.bucle:
                c.pos %= L
            elif c.pos >= L:
                c.fin = True
            if c.parando and gl1 == 0.0:
                c.fin = True
        mix *= self.vols["maestro"]
        if self.mono:
            m = mix.mean(axis=1)
            mix[:, 0] = m
            mix[:, 1] = m
        np.tanh(mix, out=mix)
        return mix

    def _cb(self, salida, frames, tiempo, estado):
        self._t_cb = time.monotonic()
        try:
            salida[:] = self.render(frames)
        except Exception:
            salida.fill(0)
        if self.stream_extra is not None:                # lo mismo, para la segunda salida
            with self._lock_extra:
                self._cola_extra.append(salida.copy())
                while sum(len(b) for b in self._cola_extra) > SR // 4:     # sin acumular retraso: lo viejo se tira
                    self._cola_extra.popleft()

    def _cb_extra(self, salida, frames, tiempo, estado):
        pos = 0
        with self._lock_extra:
            while pos < frames and self._cola_extra:
                b = self._cola_extra[0]
                k = min(frames - pos, len(b))
                salida[pos:pos + k] = b[:k]
                if k == len(b):
                    self._cola_extra.popleft()
                else:
                    self._cola_extra[0] = b[k:]
                pos += k
        if pos < frames:
            salida[pos:] = 0

    def _abrir_extra(self, sd):
        """La segunda salida: otra tarjeta, unos auriculares o un cable virtual para grabar o retransmitir."""
        self._cerrar_extra()
        if not self.extra or self.stream is None:
            return
        d = self._wasapi(sd, self.extra)
        if d is None or d == getattr(self.stream, "device", None):
            return
        try:
            self.stream_extra = sd.OutputStream(samplerate=SR, channels=2, dtype="float32", blocksize=self.stream.blocksize or 512,
                                                callback=self._cb_extra, latency="high", device=d, extra_settings=sd.WasapiSettings(auto_convert=True))
            self.stream_extra.start()
            self.nombre_extra = sd.query_devices(d)["name"]
        except Exception as e:
            self.stream_extra = None
            self.nombre_extra = ""
            registro.aviso("sonido", "No se pudo abrir la segunda salida de sonido", error=e)

    def _cerrar_extra(self):
        s, self.stream_extra = self.stream_extra, None
        self.nombre_extra = ""
        if s is not None:
            try:
                s.stop()
                s.close()
            except Exception:
                pass
        with self._lock_extra:
            self._cola_extra.clear()

    # ---------------------------------------------------------------- la salida: seguirla, recuperarla y cambiarla
    def vigilar(self, ahora=None):
        """Cada poco: si la salida se ha cortado (auriculares desconectados), si la de Windows ha cambiado y la seguimos,
        o si ha vuelto la que eligió el jugador, se vuelve a abrir donde toca. Devuelve si la ha reabierto."""
        if not self.con_dispositivo:
            return False
        ahora = time.monotonic() if ahora is None else ahora
        if ahora - self._t_vigila < VIGILAR_CADA:
            return False
        self._t_vigila = ahora
        from . import salidas
        defecto = salidas.por_defecto()
        motivo = None
        if self.stream is None:
            motivo = "sin salida"
        elif ahora - self._t_cb > CORTE:
            motivo = "se ha cortado"
        elif not self.salida and defecto and self._defecto_visto and defecto != self._defecto_visto:
            motivo = "ha cambiado la de Windows"
        elif self.salida and not salidas.coincide(self.salida, self.nombre_salida) and salidas.presente(self.salida):
            motivo = "ha vuelto la elegida"
        elif self.extra and self.stream_extra is None and salidas.presente(self.extra):
            motivo = "ha vuelto la segunda"
        if defecto:
            self._defecto_visto = defecto
        if motivo is None:
            return False
        return self.reabrir(motivo)

    def reabrir(self, motivo=""):
        """Cierra la salida y la vuelve a abrir, con la lista de dispositivos al día. Lo que estaba sonando sigue."""
        antes = self.nombre_salida
        self.cerrar()
        try:
            import sounddevice as sd
            sd._terminate()                              # PortAudio solo ve los dispositivos nuevos si se reinicia
            sd._initialize()
        except Exception:
            pass
        self._abrir(self.bloque)
        registro.info("sonido", "Salida de sonido abierta de nuevo", motivo=motivo, antes=antes, ahora=self.nombre_salida, extra=self.nombre_extra)
        return self.stream is not None

    def poner_salida(self, nombre="", extra=None):
        """Cambia en caliente la salida (vacío: la de Windows) y, si se da, la segunda salida (vacío: ninguna)."""
        self.salida = str(nombre or "")
        if extra is not None:
            self.extra = str(extra or "")
        if self.con_dispositivo:
            return self.reabrir("cambiada en las opciones")
        return False

    def cerrar(self):
        self._cerrar_extra()
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
