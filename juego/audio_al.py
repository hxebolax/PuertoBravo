"""Motor de sonido envolvente: el mismo mezclador del juego, pero reproduciendo con OpenAL Soft en binaural.

Con auriculares, el binaural permite distinguir de verdad si algo suena delante o detrás, y no solo a izquierda o
derecha. La biblioteca (soft_oal.dll, libre, LGPL) hace la mezcla en código nativo, fuera de Python, así que
tampoco sufre los tirones del motor clásico cuando hay mucho sonido a la vez.

Hereda del mezclador clásico toda la lógica (qué suena, con qué volumen, categorías, atenuación al hablar) y solo
cambia quién pone el sonido en los auriculares: en lugar de mezclar muestras en Python, mantiene una «fuente» de
OpenAL por cada sonido en marcha y la actualiza una vez por fotograma. Si la biblioteca no está o no arranca,
`crear()` devuelve el motor clásico: el juego nunca se queda sin sonido por esto.
"""
from .i18n import tr
import ctypes
import math
import os
import sys

import numpy as np

from . import registro, rutas
from .audio import SR, Mezclador

AL_POSITION, AL_GAIN, AL_PITCH, AL_LOOPING, AL_BUFFER, AL_SOURCE_STATE = 0x1004, 0x100A, 0x1003, 0x1007, 0x1009, 0x1010
AL_PLAYING, AL_PAUSED, AL_ORIENTATION, AL_SOURCE_RELATIVE = 0x1012, 0x1013, 0x100F, 0x202
AL_ROLLOFF_FACTOR, AL_FORMAT_MONO16, AL_FORMAT_STEREO16, AL_NONE = 0x1021, 0x1101, 0x1103, 0
ALC_HRTF_SOFT, ALC_HRTF_STATUS_SOFT, ALC_FREQUENCY = 0x1992, 0x1993, 0x1007
ALC_CONNECTED, ALC_ALL_DEVICES_SPECIFIER = 0x313, 0x1013
AL_SAMPLE_OFFSET = 0x1025
_CATS_MUNDO = ("efectos", "ambiente")
# Efectos (extensión EFX): un único eco, que cambia según dónde esté el oyente.
AL_EFFECT_TYPE, AL_EFFECT_REVERB, AL_EFFECTSLOT_EFFECT, AL_EFFECTSLOT_GAIN, AL_AUXILIARY_SEND_FILTER = 0x8001, 0x0001, 0x0001, 0x0002, 0x20006
AL_REVERB_GAIN, AL_REVERB_GAINHF, AL_REVERB_DECAY_TIME, AL_REVERB_REFLECTIONS_GAIN, AL_REVERB_LATE_REVERB_GAIN = 0x0003, 0x0004, 0x0005, 0x0007, 0x0009
# entorno: (cuánto eco se oye, segundos de cola, brillo, primeras reflexiones, cola)
ENTORNOS = {
    "abierto": (0.06, 0.7, 0.5, 0.02, 0.6),       # campo, playa, mar: casi nada devuelve el sonido
    "parque": (0.10, 0.9, 0.5, 0.03, 0.8),
    "calle": (0.20, 1.1, 0.7, 0.08, 1.0),         # fachadas a los lados
    "industrial": (0.30, 1.9, 0.75, 0.10, 1.2),   # naves, muelles, chapa
    "montana": (0.28, 3.2, 0.45, 0.02, 1.3),      # el eco largo de un valle
    "interior": (0.40, 0.55, 0.6, 0.35, 0.9),     # una habitación o un local
    "nave": (0.50, 2.4, 0.7, 0.20, 1.3),          # garajes, fábricas, túneles
}
DE_AMBIENTE = {"amb_ciudad": "calle", "amb_residencial": "calle", "amb_industrial": "industrial", "amb_puerto": "industrial", "amb_parque": "parque",
               "amb_campo": "abierto", "amb_playa": "abierto", "amb_mar": "abierto", "amb_montana": "montana"}


def entorno_de(ambiente):
    """El eco que corresponde al ambiente de un barrio."""
    return DE_AMBIENTE.get(ambiente, "calle")


def ruta_dll():
    """Dónde está la biblioteca: junto al ejecutable en el juego compilado, o en terceros en el código fuente."""
    base = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) else rutas.base()
    for r in (os.path.join(base, "lib", "soft_oal.dll"), os.path.join(base, "soft_oal.dll"), os.path.join(rutas.base(), "terceros", "openal_soft", "soft_oal.dll")):
        if os.path.exists(r):
            return r
    return ""


def disponible():
    return bool(ruta_dll()) and os.name == "nt"


def _cargar(ruta):
    al = ctypes.CDLL(ruta)
    vp, ci, cu, cf = ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_float
    firmas = {
        "alcOpenDevice": (vp, [ctypes.c_char_p]), "alcCloseDevice": (ctypes.c_char, [vp]), "alcCreateContext": (vp, [vp, ctypes.POINTER(ci)]),
        "alcMakeContextCurrent": (ctypes.c_char, [vp]), "alcDestroyContext": (None, [vp]), "alcGetIntegerv": (None, [vp, ci, ci, ctypes.POINTER(ci)]),
        "alcGetError": (ci, [vp]), "alGetError": (ci, []), "alDistanceModel": (None, [ci]),
        "alcGetString": (vp, [vp, ci]), "alcGetProcAddress": (vp, [vp, ctypes.c_char_p]),
        "alGenSources": (None, [ci, ctypes.POINTER(cu)]), "alDeleteSources": (None, [ci, ctypes.POINTER(cu)]),
        "alGenBuffers": (None, [ci, ctypes.POINTER(cu)]), "alDeleteBuffers": (None, [ci, ctypes.POINTER(cu)]),
        "alBufferData": (None, [cu, ci, vp, ci, ci]), "alSourcei": (None, [cu, ci, ci]), "alSourcef": (None, [cu, ci, cf]),
        "alSource3f": (None, [cu, ci, cf, cf, cf]), "alGetSourcei": (None, [cu, ci, ctypes.POINTER(ci)]),
        "alSourcePlay": (None, [cu]), "alSourceStop": (None, [cu]), "alSourcePause": (None, [cu]),
        "alListener3f": (None, [ci, cf, cf, cf]), "alListenerfv": (None, [ci, ctypes.POINTER(cf)]), "alListenerf": (None, [ci, cf]),
    }
    for nombre, (res, args) in firmas.items():
        f = getattr(al, nombre)
        f.restype, f.argtypes = res, args
    efx = {"alGenEffects": (None, [ci, ctypes.POINTER(cu)]), "alDeleteEffects": (None, [ci, ctypes.POINTER(cu)]), "alEffecti": (None, [cu, ci, ci]),
           "alEffectf": (None, [cu, ci, cf]), "alGenAuxiliaryEffectSlots": (None, [ci, ctypes.POINTER(cu)]),
           "alDeleteAuxiliaryEffectSlots": (None, [ci, ctypes.POINTER(cu)]), "alAuxiliaryEffectSloti": (None, [cu, ci, ci]),
           "alAuxiliaryEffectSlotf": (None, [cu, ci, cf]), "alSource3i": (None, [cu, ci, ci, ci, ci])}
    al.con_efx = True
    for nombre, (res, args) in efx.items():
        try:
            f = getattr(al, nombre)
            f.restype, f.argtypes = res, args
        except AttributeError:                           # una biblioteca sin efectos: el motor funciona igual, sin eco
            al.con_efx = False
    return al


class MezcladorAL(Mezclador):
    """El mezclador del juego con salida binaural por OpenAL Soft."""
    envolvente = True

    def __init__(self, salida=""):
        super().__init__(dispositivo=False)              # sin el flujo de sonido de Python: de la salida se ocupa OpenAL
        self.salida = str(salida or "")
        self.al = _cargar(ruta_dll())
        nombre = self._nombre_al(self.salida) if self.salida else None
        self.dev = self.al.alcOpenDevice(nombre) or (self.al.alcOpenDevice(None) if nombre else None)
        if not self.dev:
            raise OSError(tr("OpenAL no ha podido abrir el dispositivo de sonido"))
        atributos = (ctypes.c_int * 3)(ALC_HRTF_SOFT, 1, 0)
        self.ctx = self.al.alcCreateContext(self.dev, atributos)
        if not self.ctx or not self.al.alcMakeContextCurrent(self.ctx):
            self.al.alcCloseDevice(self.dev)
            raise OSError(tr("OpenAL no ha podido crear el contexto de sonido"))
        v = ctypes.c_int(0)
        self.al.alcGetIntegerv(self.dev, ALC_HRTF_STATUS_SOFT, 1, ctypes.byref(v))
        self.binaural = v.value == 1
        self.al.alcGetIntegerv(self.dev, ALC_FREQUENCY, 1, ctypes.byref(v))
        self.frecuencia = v.value
        self.al.alDistanceModel(AL_NONE)                 # la distancia la calcula el juego, igual que en el motor clásico
        self._buffers = {}                               # nombre -> (id de buffer, id del array con el que se hizo)
        self._pausados = False
        self._eco_slot = self._eco_efecto = 0
        self._eco_puesto = None                          # el entorno que tiene ahora el eco
        self._eco_g = 0.0
        self.eco_activo = True                           # el jugador puede quitar el eco en las opciones
        self._preparar_eco()
        self.nombre_salida = self._salida_actual()
        from . import salidas
        self._defecto_visto = salidas.por_defecto()
        registro.info("sonido", "Motor de sonido envolvente", binaural="sí" if self.binaural else "no", frecuencia=self.frecuencia,
                      eco="sí" if self._eco_slot else "no", salida=self.nombre_salida)

    # ------------------------------------------------------------------ la salida: seguirla, recuperarla y cambiarla
    def _dispositivos_al(self):
        """Los nombres de las salidas que ve OpenAL ahora mismo."""
        p = self.al.alcGetString(None, ALC_ALL_DEVICES_SPECIFIER)
        out = []
        while p:
            s = ctypes.string_at(p)
            if not s:
                break
            out.append(s.decode("utf-8", "replace"))
            p += len(s) + 1
        return out

    def _nombre_al(self, corto):
        from . import salidas
        return next((n.encode("utf-8") for n in self._dispositivos_al() if salidas.coincide(corto, n)), None)

    def _salida_actual(self):
        p = self.al.alcGetString(self.dev, ALC_ALL_DEVICES_SPECIFIER) if self.dev else None
        return ctypes.string_at(p).decode("utf-8", "replace") if p else ""

    def reabrir(self, motivo="", nombre=None):
        """Cambia de salida sin cortar lo que suena: OpenAL Soft lleva la mezcla a otro dispositivo (ALC_SOFT_reopen_device)."""
        f = self.al.alcGetProcAddress(self.dev, b"alcReopenDeviceSOFT")
        if not f:
            return False
        reabrir = ctypes.CFUNCTYPE(ctypes.c_char, ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int))(f)
        antes = self.nombre_salida
        destino = self._nombre_al(self.salida) if (nombre is None and self.salida) else nombre
        ok = bool(ord(reabrir(self.dev, destino, (ctypes.c_int * 3)(ALC_HRTF_SOFT, 1, 0))))
        if not ok and destino:
            ok = bool(ord(reabrir(self.dev, None, (ctypes.c_int * 3)(ALC_HRTF_SOFT, 1, 0))))
        self.nombre_salida = self._salida_actual()
        registro.info("sonido", "Salida de sonido abierta de nuevo", motivo=motivo, antes=antes, ahora=self.nombre_salida, motor="envolvente")
        return ok

    def vigilar(self, ahora=None):
        import time
        ahora = time.monotonic() if ahora is None else ahora
        if ahora - self._t_vigila < 1.5:
            return False
        self._t_vigila = ahora
        from . import salidas
        conectado = ctypes.c_int(1)
        self.al.alcGetIntegerv(self.dev, ALC_CONNECTED, 1, ctypes.byref(conectado))
        defecto = salidas.por_defecto()
        motivo = None
        if not conectado.value:
            motivo = "se ha cortado"
        elif not self.salida and defecto and self._defecto_visto and defecto != self._defecto_visto:
            motivo = "ha cambiado la de Windows"
        elif self.salida and not salidas.coincide(self.salida, self.nombre_salida) and salidas.presente(self.salida):
            motivo = "ha vuelto la elegida"
        if defecto:
            self._defecto_visto = defecto
        return self.reabrir(motivo) if motivo else False

    def poner_salida(self, nombre="", extra=None):
        self.salida = str(nombre or "")
        if extra is not None:
            self.extra = str(extra or "")                # en el motor envolvente no hay segunda salida: la mezcla es de OpenAL
        return self.reabrir("cambiada en las opciones")

    # ------------------------------------------------------------------ eco según el lugar
    def _preparar_eco(self):
        al = self.al
        if not getattr(al, "con_efx", False):
            return
        try:
            e, s = ctypes.c_uint(0), ctypes.c_uint(0)
            al.alGetError()
            al.alGenEffects(1, ctypes.byref(e))
            al.alEffecti(e.value, AL_EFFECT_TYPE, AL_EFFECT_REVERB)
            al.alGenAuxiliaryEffectSlots(1, ctypes.byref(s))
            if al.alGetError() or not e.value or not s.value:
                return
            al.alAuxiliaryEffectSlotf(s.value, AL_EFFECTSLOT_GAIN, 0.0)
            self._eco_efecto, self._eco_slot = e.value, s.value
        except Exception:
            self._eco_slot = self._eco_efecto = 0

    def _actualizar_eco(self):
        if not self._eco_slot:
            return
        al = self.al
        nombre = self.entorno if self.entorno in ENTORNOS else "calle"
        cuanto, cola, brillo, primeras, tardias = ENTORNOS[nombre]
        if nombre != self._eco_puesto:
            self._eco_puesto = nombre
            al.alEffectf(self._eco_efecto, AL_REVERB_DECAY_TIME, float(cola))
            al.alEffectf(self._eco_efecto, AL_REVERB_GAINHF, float(brillo))
            al.alEffectf(self._eco_efecto, AL_REVERB_REFLECTIONS_GAIN, float(primeras))
            al.alEffectf(self._eco_efecto, AL_REVERB_LATE_REVERB_GAIN, float(tardias))
            al.alEffectf(self._eco_efecto, AL_REVERB_GAIN, 0.5)
            al.alAuxiliaryEffectSloti(self._eco_slot, AL_EFFECTSLOT_EFFECT, self._eco_efecto)     # hay que volver a cargarlo para que cambie
            al.alGetError()
        objetivo = cuanto if self.eco_activo else 0.0
        self._eco_g += (objetivo - self._eco_g) * 0.15
        al.alAuxiliaryEffectSlotf(self._eco_slot, AL_EFFECTSLOT_GAIN, float(max(0.0, min(1.0, self._eco_g))))

    # ------------------------------------------------------------------ buffers y fuentes
    def _buffer(self, nombre):
        datos = self.sonidos.get(nombre)
        if datos is None:
            return 0
        hecho = self._buffers.get(nombre)
        if hecho and hecho[1] == id(datos):
            return hecho[0]
        b = ctypes.c_uint(0)
        self.al.alGenBuffers(1, ctypes.byref(b))
        pcm = np.ascontiguousarray(np.clip(datos, -1.0, 1.0) * 32767.0, dtype=np.int16)
        formato = AL_FORMAT_STEREO16 if datos.ndim == 2 else AL_FORMAT_MONO16
        self.al.alBufferData(b.value, formato, pcm.ctypes.data_as(ctypes.c_void_p), pcm.nbytes, SR)
        if hecho:                                        # el sonido ha cambiado (otro pack, otra pista de radio): el viejo sobra
            viejo = ctypes.c_uint(hecho[0])
            self.al.alDeleteBuffers(1, ctypes.byref(viejo))
            self.al.alGetError()                         # si aún lo usa alguna fuente no se borra; no pasa nada
        self._buffers[nombre] = (b.value, id(datos))
        return b.value

    def _crear_fuente(self, c):
        b = self._buffer(c.nombre)
        if not b:
            c.fin = True
            return
        s = ctypes.c_uint(0)
        self.al.alGenSources(1, ctypes.byref(s))
        if self.al.alGetError() or not s.value:          # sin fuentes libres: ese sonido no suena
            c.fin = True
            return
        c._src = s.value
        c._g = 0.0 if c.bucle else None                  # los bucles entran con fundido
        self.al.alSourcei(c._src, AL_BUFFER, b)
        self.al.alSourcei(c._src, AL_LOOPING, 1 if c.bucle else 0)
        if c.pos > 0:                                    # empieza a mitad: es la continuación de otro sonido
            self.al.alSourcei(c._src, AL_SAMPLE_OFFSET, int(c.pos))
            self.al.alGetError()
        self.al.alSourcef(c._src, AL_ROLLOFF_FACTOR, 0.0)
        if self._eco_slot and (c.cat == "efectos" or c.eco):          # lo que suena en el mundo lleva el eco del lugar
            self.al.alSource3i(c._src, AL_AUXILIARY_SEND_FILTER, self._eco_slot, 0, 0)
            self.al.alGetError()
        self._poner(c)
        self.al.alSourcePlay(c._src)

    def _soltar(self, c):
        s = getattr(c, "_src", 0)
        if s:
            self.al.alSourceStop(s)
            u = ctypes.c_uint(s)
            self.al.alDeleteSources(1, ctypes.byref(u))
            c._src = 0
        c.fin = True

    def _poner(self, c):
        """Lleva a la fuente de OpenAL el volumen, el tono y la posición que el juego quiere para este sonido."""
        g = c.vol * self.vols.get(c.cat, 1.0)
        if c.senal:
            g *= self.vols["senales"]
        if c.cat in ("ambiente", "musica"):
            g *= self.duck
        ox, oy, _ = self.oyente
        if c.xy is None:
            self.al.alSourcei(c._src, AL_SOURCE_RELATIVE, 1)
            self.al.alSource3f(c._src, AL_POSITION, float(max(-1.0, min(1.0, c.pan))), 0.0, -0.4 if c.pan else 0.0)
        else:
            dx, dy = c.xy[0] - ox, c.xy[1] - oy
            d = math.hypot(dx, dy)
            if self.altura > 0 and c.cat in ("efectos", "ambiente"):    # volando, la calle queda abajo (ver audio.py)
                d = math.hypot(d, self.altura - c.alto)
            if d >= c.maxd:
                g = 0.0
            else:
                if d > c.ref:
                    g *= c.ref / (c.ref + 1.2 * (d - c.ref))
                borde = c.maxd * 0.25
                if d > c.maxd - borde:
                    g *= (c.maxd - d) / borde
            self.al.alSourcei(c._src, AL_SOURCE_RELATIVE, 0)
            # el volumen por distancia ya está aplicado: a OpenAL solo le interesa la dirección, así que se le da a un metro
            dz = c.alto - self.altura                    # por encima o por debajo del oyente
            d3 = math.hypot(d, dz)
            k = 1.0 / d3 if d3 > 1.0 else 1.0
            self.al.alSource3f(c._src, AL_POSITION, float(ox + dx * k), float(dz * k), float(-(oy + dy * k)))
        if c.parando:
            g = 0.0
        if c._g is None:
            c._g = g
        else:
            c._g += (g - c._g) * (0.5 if g < c._g else 0.3)
        self.al.alSourcef(c._src, AL_GAIN, float(max(0.0, min(4.0, c._g))))
        c.rate += (c.rate_obj - c.rate) * 0.4
        tono = c.rate * self.tono_mundo if c.cat in _CATS_MUNDO else c.rate
        self.al.alSourcef(c._src, AL_PITCH, float(max(0.05, min(8.0, tono))))

    # ------------------------------------------------------------------ interfaz del mezclador
    def posicion(self, c):
        s = getattr(c, "_src", 0)
        if not s:
            return float(c.pos)
        v = ctypes.c_int(0)
        self.al.alGetSourcei(s, AL_SAMPLE_OFFSET, ctypes.byref(v))
        return float(v.value)

    def sonar(self, nombre, **kw):
        c = super().sonar(nombre, **kw)
        c._src = 0
        c._g = None
        return c

    def actualizar(self):
        self.vigilar()
        with self._lock:
            lista = list(self.canales)
        import time
        objetivo = 0.45 if self.atenuar and time.time() < self.duck_hasta else 1.0
        self.duck += (objetivo - self.duck) * (0.35 if objetivo < self.duck else 0.08)
        ox, oy, rumbo = self.oyente
        r = math.radians(rumbo)
        self.al.alListener3f(AL_POSITION, float(ox), 0.0, float(-oy))
        self.al.alListenerfv(AL_ORIENTATION, (ctypes.c_float * 6)(math.sin(r), 0.0, -math.cos(r), 0.0, 1.0, 0.0))
        self.al.alListenerf(AL_GAIN, float(self.vols["maestro"]))
        self._actualizar_eco()
        estado = ctypes.c_int(0)
        pausar = bool(self.mundo_pausado)
        for c in lista:
            if c.fin:
                if getattr(c, "_src", 0):
                    self._soltar(c)
                continue
            if not getattr(c, "_src", 0):
                self._crear_fuente(c)
                if c.fin:
                    continue
            self._poner(c)
            if c.parando and c._g < 0.01:
                self._soltar(c)
                continue
            if c.cat in _CATS_MUNDO and pausar != self._pausados:
                (self.al.alSourcePause if pausar else self.al.alSourcePlay)(c._src)
            elif not c.bucle and not (pausar and c.cat in _CATS_MUNDO):
                self.al.alGetSourcei(c._src, AL_SOURCE_STATE, ctypes.byref(estado))
                if estado.value not in (AL_PLAYING, AL_PAUSED):
                    self._soltar(c)
        self._pausados = pausar
        with self._lock:
            self.canales = [c for c in self.canales if not c.fin]

    def render(self, n):
        return np.zeros((n, 2), np.float32)              # la mezcla la hace OpenAL; esto solo existe por compatibilidad

    def cerrar(self):
        try:
            with self._lock:
                lista, self.canales = list(self.canales), []
            for c in lista:
                self._soltar(c)
            for b, _ in self._buffers.values():
                u = ctypes.c_uint(b)
                self.al.alDeleteBuffers(1, ctypes.byref(u))
            self._buffers.clear()
            if self._eco_slot:
                s, e = ctypes.c_uint(self._eco_slot), ctypes.c_uint(self._eco_efecto)
                self.al.alDeleteAuxiliaryEffectSlots(1, ctypes.byref(s))
                self.al.alDeleteEffects(1, ctypes.byref(e))
                self._eco_slot = 0
            self.al.alcMakeContextCurrent(None)
            self.al.alcDestroyContext(self.ctx)
            self.al.alcCloseDevice(self.dev)
        except Exception:
            pass


def crear(cfg, pruebas=False):
    """El mezclador que toca: el envolvente si el jugador lo ha elegido y este equipo puede; si no, el clásico."""
    if pruebas:
        m = Mezclador(dispositivo=False)
        m.sincrono = True
        return m
    forzado = os.environ.get("PUERTOBRAVO_MOTOR", "")              # para pruebas: «envolvente» o «clasico»
    _c = dict(getattr(cfg, "v", cfg))                              # las salidas pueden faltar en una configuración antigua
    salida, extra = str(_c.get("salida_sonido", "") or ""), str(_c.get("salida_extra", "") or "")
    if (cfg["motor_sonido"] == "envolvente" or forzado == "envolvente") and forzado != "clasico" and not cfg["sonido_mono"]:
        from . import procesador
        if not disponible():
            registro.aviso("sonido", "No está la biblioteca del motor envolvente; se usa el clásico")
        elif not procesador.moderno():
            registro.aviso("sonido", "Procesador antiguo: se usa el motor de sonido clásico")
        else:
            try:
                return MezcladorAL(salida=salida)
            except Exception as e:
                registro.aviso("sonido", "El motor envolvente no ha arrancado; se usa el clásico", error=type(e).__name__)
    from . import audio
    audio.HOLGADO = bool(dict(getattr(cfg, "v", cfg)).get("sonido_holgado", False))      # búfer grande, para equipos donde el sonido da chasquidos
    return Mezclador(dispositivo=True, salida=salida, extra=extra)
