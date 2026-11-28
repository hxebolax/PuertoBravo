"""Registro de la sesión, para poder depurar un fallo sin estar delante.

Cada vez que se abre el juego (o el editor) se crea una carpeta en data/logs con todo lo que hace falta para
entender qué pasó. Se conservan las cinco últimas sesiones: al abrir la sexta se borra la más antigua. Quien
tenga un fallo solo tiene que comprimir la carpeta de esa sesión y enviarla.

Qué hay en la carpeta de una sesión:

- LEEME.txt          Qué contiene la carpeta y qué no.
- sistema.txt        Versión del juego, Windows, lector de pantalla, sonido, mods, packs y opciones.
- sesion.log         Todo lo que pasa, por orden y con su hora: pantallas, teclas, lo que dice el juego,
                     estado de la partida cada pocos segundos, red, actualizaciones, avisos y errores.
- errores.log        Solo los errores, con su traza completa y el estado de la partida en ese momento.
- fallo_grave.log    Si el programa se cae de golpe, lo que Python alcanza a escribir.

Qué NO se guarda nunca: lo que se escribe en los cuadros de texto (mensajes, contraseñas, direcciones, claves),
los mensajes del chat, el nombre que usas con tus amigos y los suyos, direcciones de internet, el nombre de usuario
de Windows, el nombre del equipo, las rutas de tus carpetas, los nombres de tu música ni el contenido de tus partidas.
Antes de escribir cada línea se pasa un filtro que borra todo eso aunque llegue por descuido.
"""
from .i18n import tr
import contextlib
import datetime
import faulthandler
import os
import platform
import re
import shutil
import sys
import threading
import time
import traceback
from collections import deque

from . import rutas

MAX_SESIONES = 5
MAX_BYTES = 4 * 1024 * 1024          # al pasar de aquí, sesion.log se parte en dos y se conserva la mitad reciente
CADA_ESTADO = 15.0                   # segundos entre fotos del estado de la partida
# opciones que no se copian a sistema.txt
OPCIONES_PRIVADAS = ("red_nombre", "red_ultima", "act_url", "vol_sonidos")

_candado = threading.RLock()
_sesion = None                       # carpeta de la sesión, o None si el registro está apagado
_log = None
_errores = None
_grave = None
_t0 = 0.0
_privado = 0
_ocultos = set()
_rutas_ocultas = []
_sonidos = deque(maxlen=120)         # los últimos sonidos: se vuelcan cuando hay un error
_teclas = deque(maxlen=60)
_faltan = set()
_vistos = {}
_estado_fn = None                    # función que devuelve el estado de la partida
_programa = "juego"

_RE_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b(?::\d{2,5})?")
_RE_URL = re.compile(r"\b(?:puertobravo|https?|ftp|file)://[^\s\"'<>|]+", re.I)
_RE_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_RE_CLAVE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|[A-Fa-f0-9]{40,})\b")
_RE_UNIDAD = re.compile(r"[A-Za-z]:[\\/](?:Users|Usuarios|Documents and Settings)[\\/][^\\/\s\"']+", re.I)


# ----------------------------------------------------------------- privacidad
# Cualquier otra ruta completa de Windows (las de quien compiló el juego, las de otros programas): se deja solo el archivo.
_RE_RUTA = re.compile(r"(?<![\w<>])[A-Za-z]:[\\/](?:[^\\/\"'<>|:*?\r\n]+[\\/])*")


def limpiar(texto):
    """Quita de un texto cualquier cosa personal antes de escribirlo."""
    t = str(texto)
    for ruta, nombre in _rutas_ocultas:
        if ruta and ruta.lower() in t.lower():
            t = re.sub(re.escape(ruta), lambda m: nombre, t, flags=re.I)
            t = re.sub(re.escape(ruta.replace("\\", "/")), lambda m: nombre, t, flags=re.I)
            t = re.sub(re.escape(ruta.replace("\\", "\\\\")), lambda m: nombre, t, flags=re.I)
    t = _RE_UNIDAD.sub(tr("<carpeta de usuario>"), t)
    t = _RE_RUTA.sub("", t)
    t = _RE_URL.sub("<dirección>", t)
    t = _RE_CORREO.sub("<correo>", t)
    t = _RE_IP.sub("<ip>", t)
    t = _RE_CLAVE.sub("<clave>", t)
    for palabra in sorted(_ocultos, key=len, reverse=True):
        t = re.sub(r"(?<!\w)" + re.escape(palabra) + r"(?!\w)", "<nombre>", t, flags=re.I)
    return t.replace("\r", " ").replace("\n", " ⏎ ")


def ocultar(nombre):
    """Desde ahora, este nombre (el tuyo en la red, el de un amigo) no aparece en el registro."""
    nombre = str(nombre or "").strip()
    if len(nombre) >= 2:
        with _candado:
            _ocultos.add(nombre)


@contextlib.contextmanager
def privado():
    """Mientras dura, lo que diga el juego no se registra: cuadros de texto y mensajes del chat."""
    global _privado
    _privado += 1
    try:
        yield
    finally:
        _privado -= 1


# ------------------------------------------------------------------- arranque
def activo():
    return _sesion is not None


def carpeta_sesion():
    return _sesion


def carpeta_logs():
    return os.path.join(rutas.DATA, "logs")


def _podar(raiz, dejar):
    try:
        sesiones = sorted(d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d)))
    except OSError:
        return
    for vieja in sesiones[:max(0, len(sesiones) - dejar)]:
        shutil.rmtree(os.path.join(raiz, vieja), ignore_errors=True)


def iniciar(programa="juego", raiz=None, version=None, graves=True):
    """Abre la carpeta de esta sesión. Si no se puede escribir, el programa sigue sin registro."""
    global _sesion, _log, _errores, _grave, _t0, _programa
    if _sesion is not None:
        return _sesion
    from . import VERSION
    raiz = raiz or carpeta_logs()
    try:
        os.makedirs(raiz, exist_ok=True)
        _podar(raiz, MAX_SESIONES - 1)                 # sitio para la nueva: quedan, como mucho, cinco
        _sanear_anteriores(raiz)
        ahora = datetime.datetime.now()
        nombre = ahora.strftime("%Y-%m-%d_%H-%M-%S") + "_" + programa
        carpeta = os.path.join(raiz, nombre)
        n = 2
        while os.path.exists(carpeta):
            carpeta = os.path.join(raiz, f"{nombre}_{n}")
            n += 1
        os.makedirs(carpeta)
        log = open(os.path.join(carpeta, "sesion.log"), "w", encoding="utf-8", buffering=1)
    except OSError:
        return None
    with _candado:
        _sesion, _log, _t0, _programa = carpeta, log, time.perf_counter(), programa
        _preparar_filtro()
    if graves:
        try:
            _grave = open(os.path.join(carpeta, "fallo_grave.log"), "w", encoding="utf-8")
            faulthandler.enable(file=_grave, all_threads=True)
        except Exception:
            _grave = None
    _escribir_leeme(carpeta)
    info("sesion", tr('Empieza la sesión de {programa}').format(programa=(programa)), version=version or VERSION, compilado=bool(getattr(sys, "frozen", False)),
         fecha=ahora.strftime("%Y-%m-%d %H:%M:%S"))
    if graves:
        sys.excepthook = _gancho
        threading.excepthook = _gancho_hilo
        try:
            sys.unraisablehook = _gancho_suelto
        except Exception:
            pass
    return carpeta


def _preparar_filtro():
    del _rutas_ocultas[:]
    try:
        _rutas_ocultas.append((rutas.base(), "<juego>"))
    except Exception:
        pass
    casa = os.path.expanduser("~")
    if casa and casa != "~":
        _rutas_ocultas.append((casa, tr("<carpeta de usuario>")))
    for var in ("TEMP", "TMP", "APPDATA", "LOCALAPPDATA", "USERPROFILE"):
        v = os.environ.get(var)
        if v and len(v) > 3:
            _rutas_ocultas.append((v, f"<{var.lower()}>"))
    _rutas_ocultas.sort(key=lambda par: len(par[0]), reverse=True)
    for var in ("USERNAME", "COMPUTERNAME", "USERDOMAIN"):
        v = os.environ.get(var)
        if v and len(v) >= 3:
            _ocultos.add(v)


# Excepciones de Windows que el programa recoge y sigue como si nada, pero que Python anota igual en fallo_grave.log:
# 0xe0000002 la lanza por dentro la voz de Windows (SAPI) al hablar. No son caídas: se quitan para no confundir.
INOFENSIVAS = ("0xe0000002",)


def _sin_inofensivas(lineas):
    """Quita los bloques de excepciones de Windows que no tiraron el programa."""
    fuera, salta = [], False
    for l in lineas:
        if l.startswith(tr("Windows fatal exception:")):
            salta = any(c in l.lower() for c in INOFENSIVAS)
        elif l.startswith(tr("Fatal Python error")) or (l and not l[0].isspace() and not l.startswith((tr("Thread "), tr("Current thread "), tr("Stack "), tr("Extension modules")))):
            salta = False
        if not salta:
            fuera.append(l)
    return fuera if any(l.strip() for l in fuera) else []


def _sanear(ruta):
    """fallo_grave.log lo escribe Python directamente, sin pasar por el filtro: se limpia después, línea a línea.
    Si solo traía excepciones inofensivas de Windows, se borra."""
    try:
        with open(ruta, encoding="utf-8", errors="replace") as f:
            lineas = f.read().splitlines()
        lineas_sin = _sin_inofensivas(lineas)
        if not lineas_sin:
            os.remove(ruta)
            return
        if lineas_sin != lineas:
            with open(ruta, "w", encoding="utf-8", newline="\r\n") as f:
                f.write("\n".join(lineas_sin) + "\n")
            lineas = lineas_sin
        limpio = [limpiar(l) for l in lineas]
        if limpio != lineas:
            with open(ruta, "w", encoding="utf-8", newline="\r\n") as f:
                f.write("\n".join(limpio) + "\n")
    except OSError:
        pass


def _sanear_anteriores(raiz):
    """Si una sesión anterior se cerró de golpe, su fallo_grave.log quedó sin limpiar: se limpia ahora."""
    try:
        for nombre in os.listdir(raiz):
            grave = os.path.join(raiz, nombre, "fallo_grave.log")
            if os.path.isfile(grave) and os.path.join(raiz, nombre) != _sesion and os.path.getsize(grave) > 0:
                _sanear(grave)
    except OSError:
        pass


def _escribir_leeme(carpeta):
    texto = tr("""REGISTRO DE UNA SESIÓN DE PUERTO BRAVO: LEY DEL ASFALTO

Si el juego te ha dado un fallo, comprime esta carpeta entera en un ZIP y envíala a quien hace el juego.
Con ella se puede ver qué pasó sin estar delante.

QUÉ CONTIENE
  sistema.txt       Versión del juego, versión de Windows, lector de pantalla, sonido, mods, packs y opciones.
  sesion.log        Lo que ha pasado en esta sesión, por orden: pantallas abiertas, teclas pulsadas en el juego,
                    lo que el juego ha dicho, el estado de la partida cada pocos segundos, avisos y errores.
  errores.log       Los errores, con su detalle técnico.
  fallo_grave.log   Solo tiene algo si el programa se cerró de golpe.

QUÉ NO CONTIENE
  Nada de lo que escribes en los cuadros de texto: mensajes, contraseñas, direcciones ni claves.
  Ni los mensajes del chat, ni tu nombre en la red, ni el de tus amigos.
  Ni direcciones de internet, ni tu nombre de usuario de Windows, ni el nombre de tu equipo, ni las rutas de tus carpetas.
  Ni los nombres de tu música, ni tus partidas guardadas.

Son archivos de texto: puedes abrirlos y leerlos antes de enviarlos.
Se guardan las cinco últimas sesiones; las más antiguas se borran solas.
""")
    try:
        with open(os.path.join(carpeta, "LEEME.txt"), "w", encoding="utf-8", newline="\r\n") as f:
            f.write(texto)
    except OSError:
        pass


def cerrar():
    """Cierre normal: lo anota y suelta los archivos."""
    global _sesion, _log, _errores, _grave, _estado_fn
    if _sesion is None:
        return
    info("sesion", tr("Fin de la sesión: cierre normal"))
    with _candado:
        if _grave is not None:
            try:
                faulthandler.disable()
            except Exception:
                pass
        for f in (_log, _errores, _grave):
            try:
                if f is not None:
                    f.close()
            except Exception:
                pass
        try:
            grave = os.path.join(_sesion, "fallo_grave.log")
            if os.path.getsize(grave) == 0:
                os.remove(grave)
            else:
                _sanear(grave)
        except OSError:
            pass
        _sesion = _log = _errores = _grave = _estado_fn = None
        _ocultos.clear()
        _faltan.clear()
        _vistos.clear()
        _sonidos.clear()
        _teclas.clear()


# -------------------------------------------------------------------- escribir
def _linea(nivel, cat, mensaje, datos=None):
    if _sesion is None:
        return
    try:
        ahora = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        t = time.perf_counter() - _t0
        texto = limpiar(mensaje)
        if datos:
            texto += " | " + ", ".join(f"{k}={limpiar(v)}" for k, v in datos.items())
        linea = f"{ahora} {t:9.2f} {nivel:<5} [{cat}] {texto}\n"
        with _candado:
            if _log is None:
                return
            _log.write(linea)
            if _log.tell() > MAX_BYTES:
                _partir()
    except Exception:
        pass                        # el registro nunca puede tirar el juego


def _partir():
    """sesion.log ha crecido demasiado: lo anterior pasa a sesion_anterior.log y se sigue en uno nuevo."""
    global _log
    try:
        _log.close()
        actual = os.path.join(_sesion, "sesion.log")
        os.replace(actual, os.path.join(_sesion, "sesion_anterior.log"))
        _log = open(actual, "w", encoding="utf-8", buffering=1)
        _log.write(tr("(continúa de sesion_anterior.log)\n"))
    except OSError:
        _log = None


def info(cat, mensaje, **datos):
    _linea("INFO", cat, mensaje, datos)


def aviso(cat, mensaje, **datos):
    _linea("AVISO", cat, mensaje, datos)


def una_vez(cat, mensaje, **datos):
    """Un aviso que puede repetirse mil veces: se escribe la primera y se cuenta el resto."""
    clave = (cat, mensaje)
    with _candado:
        _vistos[clave] = _vistos.get(clave, 0) + 1
        primera = _vistos[clave] == 1
    if primera:
        _linea("AVISO", cat, mensaje, datos)


def error(cat, mensaje, traza=None, **datos):
    """Un error: va a sesion.log y, con todo el detalle, a errores.log."""
    global _errores
    if _sesion is None:
        return
    _linea("ERROR", cat, mensaje, datos)
    try:
        with _candado:
            if _errores is None:
                _errores = open(os.path.join(_sesion, "errores.log"), "w", encoding="utf-8", buffering=1)
            f = _errores
            f.write("=" * 78 + "\n")
            f.write(tr('{strftime}  a los {v:.1f} s  [{cat}] {limpiar}\n').format(strftime=(datetime.datetime.now().strftime('%H:%M:%S')), v=(time.perf_counter() - _t0), cat=(cat), limpiar=(limpiar(mensaje))))
            for k, v in datos.items():
                f.write(f"  {k}: {limpiar(v)}\n")
            if traza:
                f.write(tr("\nTraza:\n"))
                for l in str(traza).rstrip().splitlines():
                    f.write("  " + limpiar(l) + "\n")
            estado = _foto()
            if estado:
                f.write(tr("\nEstado de la partida:\n"))
                for k, v in estado.items():
                    f.write(f"  {k}: {limpiar(v)}\n")
            if _teclas:
                f.write(tr("\nÚltimas teclas: ") + " ".join(_teclas) + "\n")
            if _sonidos:
                f.write(tr("Últimos sonidos: ") + " ".join(_sonidos) + "\n")
            f.write("\n")
    except Exception:
        pass


def excepcion(cat, mensaje=tr("Error inesperado"), **datos):
    """Registra la excepción que se está tratando ahora mismo."""
    error(cat, mensaje, traceback.format_exc(), **datos)


def _gancho(tipo, valor, tb):
    error("python", tr('Excepción sin tratar: {__name__}: {valor}').format(__name__=(tipo.__name__), valor=(valor)), "".join(traceback.format_exception(tipo, valor, tb)))
    try:
        sys.__excepthook__(tipo, valor, tb)
    except Exception:
        pass


def _gancho_hilo(args):
    if args.exc_type is SystemExit:
        return
    nombre = getattr(args.thread, "name", "?")
    error("hilo", tr('Excepción en un hilo ({nombre}): {__name__}: {exc_value}').format(nombre=(nombre), __name__=(args.exc_type.__name__), exc_value=(args.exc_value)),
          "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)))


def _gancho_suelto(args):
    error("python", tr('Excepción al liberar un objeto: {getattr}: {exc_value}').format(getattr=(getattr(args.exc_type, '__name__', '?')), exc_value=(args.exc_value)),
          "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback)) if args.exc_traceback else None)


# ------------------------------------------------------------- lo que se anota
def voz(texto):
    """Lo que el juego dice en voz alta: es el relato de la sesión."""
    if _sesion is None:
        return
    if _privado:
        _linea("VOZ", "voz", tr("(texto privado, no se registra)"))
    else:
        _linea("VOZ", "voz", texto)


def tecla(nombre, en_texto=False):
    if _sesion is None:
        return
    if en_texto or _privado:
        nombre = tr("(tecla en un cuadro de texto)")
    _teclas.append(nombre)
    _linea("TECLA", "tecla", nombre)


def sonido(nombre):
    if _sesion is not None:
        _sonidos.append(nombre)


def sonido_falta(nombre):
    if _sesion is not None and nombre not in _faltan:
        _faltan.add(nombre)
        _linea("AVISO", "sonido", tr('Se ha pedido un sonido que no existe: {nombre}').format(nombre=(nombre)))


def pantalla(que, pantalla_):
    if _sesion is None:
        return
    titulo = "" if getattr(pantalla_, "escena_privada", False) else getattr(pantalla_, "titulo", "")
    if callable(titulo):
        try:
            titulo = titulo()
        except Exception:
            titulo = ""
    _linea("INFO", "pantalla", f"{que}: {type(pantalla_).__name__}" + (f" «{titulo}»" if titulo and not _privado else ""))


def marca():
    """El jugador señala que aquí ha pasado algo raro."""
    _linea("MARCA", "marca", tr("########## MARCA DEL JUGADOR: aquí ha pasado algo ##########"))
    estado(forzar=True)


def vigilar_estado(funcion):
    """Qué función da el estado de la partida (o None al salir de ella)."""
    global _estado_fn
    _estado_fn = funcion


def _foto():
    fn = _estado_fn
    if fn is None:
        return None
    try:
        return fn()
    except Exception as e:
        return {"estado": tr('no se pudo leer: {__name__}: {e}').format(__name__=(type(e).__name__), e=(e))}


def estado(forzar=False):
    if _sesion is None:
        return
    d = _foto()
    if d:
        _linea("ESTAD", "estado", ", ".join(f"{k}={v}" for k, v in d.items()))


# ------------------------------------------------------------------ sistema.txt
def _memoria():
    try:
        import ctypes

        class Estado(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        e = Estado()
        e.dwLength = ctypes.sizeof(Estado)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e))
        return tr('{v:.1f} GB en total, {v2:.1f} GB libres').format(v=(e.ullTotalPhys / 2 ** 30), v2=(e.ullAvailPhys / 2 ** 30))
    except Exception:
        return "desconocida"


def _contar(carpeta, extensiones):
    n = 0
    for _, _, archivos in os.walk(carpeta):
        n += sum(1 for f in archivos if f.lower().endswith(extensiones))
    return n


def escribir_sistema(secciones):
    """Escribe sistema.txt. `secciones` es una lista de (título, {dato: valor}) que añade el programa."""
    if _sesion is None:
        return
    from . import VERSION
    from . import procesador
    base = [(tr("Programa"), {"programa": _programa, "versión": VERSION, "compilado": "sí" if getattr(sys, "frozen", False) else tr("no, código fuente"),
                          "Python": platform.python_version()}),
            (tr("Procesador"), procesador.resumen()),
            (tr("Equipo"), {"sistema": platform.platform(), "arquitectura": platform.machine(), "procesadores": os.cpu_count(), "memoria": _memoria()})]
    try:
        libre = shutil.disk_usage(rutas.DATA).free
        base[1][1]["disco libre donde está el juego"] = tr('{v:.1f} GB').format(v=(libre / 2 ** 30))
    except OSError:
        pass
    try:
        with open(os.path.join(_sesion, "sistema.txt"), "w", encoding="utf-8", newline="\r\n") as f:
            for titulo, datos in base + list(secciones):
                f.write(titulo.upper() + "\n")
                for k, v in datos.items():
                    f.write(f"  {k}: {limpiar(v)}\n")
                f.write("\n")
    except OSError:
        pass


def datos_del_juego(app):
    """Las secciones de sistema.txt propias del juego: voz, sonido, contenido y opciones."""
    secciones = []
    salida = getattr(app.voz, "salida", None)
    motor = type(salida).__name__ if salida is not None else "ninguna"
    try:
        primero = salida.get_first_available_output()
        motor += f" ({type(primero).__name__})"
    except Exception:
        pass
    secciones.append((tr("Voz"), {"salida": motor, "voz de Windows forzada": "sí" if app.cfg["voz_sapi"] else "no"}))
    mez = app.mez
    envolvente = bool(getattr(mez, "envolvente", False))
    sonido_ = {"motor": tr("envolvente, OpenAL Soft") + (tr(", binaural") if getattr(mez, "binaural", False) else tr(", sin binaural")) if envolvente else "clásico",
               "abierto": "sí" if envolvente else "no" if mez.error or getattr(mez, "stream", None) is None else "sí", "error": mez.error or "ninguno",
               "sonidos cargados": len(mez.sonidos)}
    if envolvente:
        sonido_["frecuencia"] = getattr(mez, "frecuencia", 0)
    try:
        st = mez.stream
        sonido_["frecuencia"] = int(st.samplerate)
        sonido_["canales"] = st.channels
        sonido_["latencia"] = tr('{v:.0f} ms').format(v=(float(st.latency) * 1000))
        sonido_["bloque"] = st.blocksize
    except Exception:
        pass
    try:
        import sounddevice as sd
        sonido_["sistema de audio"] = sd.query_hostapis(sd.query_devices(mez.stream.device)["hostapi"])["name"]
    except Exception:
        pass
    secciones.append((tr("Sonido"), sonido_))
    datos = app.datos
    mods = sorted(f for f in os.listdir(rutas.carpeta_data("mods")) if f.lower().endswith((".pbm", ".json")))
    packs = sorted(d for d in os.listdir(rutas.carpeta_data("sonidos")) if os.path.isdir(os.path.join(rutas.carpeta_data("sonidos"), d)))
    audio = (".mp3", ".ogg", ".wav", ".flac")
    secciones.append((tr("Contenido"), {
        "mapas": len(app.mapas), "lugares": sum(len(m.lugares) for m in app.mapas.values()), "misiones": len(datos.get("misiones", [])),
        "vehículos": len(datos.get("vehiculos", [])), "armas": len(datos.get("armas", [])),
        "mods": ", ".join(mods) or "ninguno", "errores al cargar mods": len(datos.get("errores_mods", [])),
        "packs de sonidos": ", ".join(packs), "pack elegido": app.cfg["pack_sonidos"] or tr("por defecto"),
        "archivos de radio": _contar(rutas.carpeta_data("radio"), audio), "archivos de música de ambiente": _contar(rutas.carpeta_data("musica"), audio),
        "mando": getattr(getattr(app, "mando", None), "nombre_tipo", lambda: "")() if hasattr(getattr(app, "mando", None), "nombre_tipo") else tr("ver sesion.log"),
    }))
    opciones = {k: v for k, v in sorted(app.cfg.v.items()) if k not in OPCIONES_PRIVADAS}
    opciones["sonidos con volumen retocado"] = len(app.cfg.v.get("vol_sonidos") or {})
    opciones["nombre propio en la red"] = "sí" if app.cfg.v.get("red_nombre") else "no"
    secciones.append((tr("Opciones"), opciones))
    return secciones
