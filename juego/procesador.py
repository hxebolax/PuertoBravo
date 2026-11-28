"""Qué procesador tiene el equipo y con qué biblioteca de cálculo (numpy) puede arrancar el juego.

La numpy oficial exige un procesador con las instrucciones SSE4.2 y compañía (lo que se llama x86-64-v2), que
tienen casi todos los fabricados desde 2009 o 2010. En uno más antiguo, cargarla hace que Windows cierre el
programa. Por eso el juego compilado lleva dos:

- lib\\numpy          la oficial, para los procesadores actuales.
- lib_antiguo\\numpy  la misma versión, compilada sin esa exigencia (herramientas\\compilar_numpy_antiguo.bat).

Antes de cargar ninguna, se pregunta a Windows qué instrucciones tiene el procesador y se elige. Si aun así
la elegida no carga, se prueba con la otra. Y si no carga ninguna, el juego lo dice en voz alta y se cierra
con normalidad, en lugar de desaparecer sin más.

Este módulo no puede importar numpy ni nada que lo use.
"""
from .i18n import tr
import os
import sys

# Constantes de IsProcessorFeaturePresent. De la 36 en adelante solo contestan bien desde Windows 10 de mayo de 2020.
INSTRUCCIONES = (("SSE3", 13), ("CX16", 14), ("SSSE3", 36), (tr("SSE4.1"), 37), (tr("SSE4.2"), 38), ("AVX", 39), ("AVX2", 40))
NECESARIAS = ("SSE3", "CX16", "SSSE3", tr("SSE4.1"), tr("SSE4.2"))
# The same flags, with the name each one takes in the «flags» line of /proc/cpuinfo on Linux. SSE3 appears as
# «pni» in older kernels and as «sse3» in newer ones, so both names are accepted.
INSTRUCCIONES_LINUX = {("sse3", "pni"): "SSE3", ("cx16",): "CX16", ("ssse3",): "SSSE3", ("sse4_1",): tr("SSE4.1"), ("sse4_2",): tr("SSE4.2"), ("avx",): "AVX", ("avx2",): "AVX2"}
estado = {"numpy": "", "motivo": "", "instrucciones": {}}

AVISO = (tr("Puerto Bravo no puede funcionar en este ordenador. Su procesador es demasiado antiguo: le faltan instrucciones "
         "que el motor de sonido del juego necesita. No es un fallo de la instalación ni se arregla volviendo a descargarlo. "
         "Hace falta un ordenador con un procesador fabricado, más o menos, de 2009 en adelante."))


def instrucciones():
    """Qué instrucciones dice Windows que tiene el procesador. Diccionario vacío si no se puede preguntar."""
    if sys.platform == "linux":
        return _instrucciones_linux()
    if os.name != "nt":
        return {}
    try:
        import ctypes
        k = ctypes.windll.kernel32
        return {nombre: bool(k.IsProcessorFeaturePresent(codigo)) for nombre, codigo in INSTRUCCIONES}
    except Exception:
        return {}


def _instrucciones_linux():
    """The same processor instruction flags on Linux, read from /proc/cpuinfo. Empty dict if it cannot be read."""
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8", errors="replace") as f:
            for linea in f:
                if linea.split(":", 1)[0].strip() == "flags":
                    hay = set(linea.split(":", 1)[1].split())
                    return {nombre: any(bandera in hay for bandera in banderas) for banderas, nombre in INSTRUCCIONES_LINUX.items()}
    except Exception:
        pass
    return {}


def moderno(ins=None):
    """¿Tiene todo lo que exige la numpy oficial? Si el sistema no sabe contestar, se toma como que no: lo seguro."""
    ins = instrucciones() if ins is None else ins
    return bool(ins) and all(ins.get(n) for n in NECESARIAS)


def carpeta_antigua():
    return os.path.join(os.path.dirname(os.path.abspath(sys.executable)), "lib_antiguo")


def _usar_antigua(usar):
    """Pone o quita la carpeta de la numpy para procesadores antiguos al principio de la búsqueda de módulos."""
    c = carpeta_antigua()
    while c in sys.path:
        sys.path.remove(c)
    if usar:
        sys.path.insert(0, c)


def _olvidar_numpy():
    for nombre in [m for m in sys.modules if m == "numpy" or m.startswith("numpy.")]:
        del sys.modules[nombre]


def _cargar():
    import numpy                              # noqa: F401
    return True


def preparar(cargar=None):
    """Elige la numpy que toca y comprueba que carga. Devuelve True si el juego puede seguir.

    Fuera del juego compilado no hay nada que elegir: se usa la del entorno.
    """
    cargar = cargar or _cargar
    ins = instrucciones()
    estado["instrucciones"] = ins
    hay_antigua = bool(getattr(sys, "frozen", False)) and os.path.isdir(os.path.join(carpeta_antigua(), "numpy"))
    forzada = os.environ.get("PUERTOBRAVO_NUMPY", "").lower()            # para pruebas: «antigua» u «oficial»
    if not hay_antigua:
        orden = ["oficial"]
    elif forzada in ("antigua", "oficial"):
        orden = [forzada]
    else:
        orden = ["oficial", "antigua"] if moderno(ins) else ["antigua", "oficial"]
    errores = []
    for cual in orden:
        _usar_antigua(cual == "antigua")
        try:
            cargar()
            estado["numpy"] = cual
            estado["motivo"] = (tr("forzada para pruebas") if forzada in ("antigua", "oficial") and hay_antigua else
                                tr("no hay otra") if not hay_antigua else
                                tr("el procesador tiene todas las instrucciones") if cual == "oficial" and not errores else
                                tr("al procesador le faltan instrucciones") if cual == "antigua" and not errores else
                                tr("la otra no ha cargado: ") + "; ".join(errores))
            return True
        except Exception as e:                                           # sobre todo ImportError: «DLL load failed»
            errores.append(f"{cual}: {type(e).__name__}")
            _olvidar_numpy()
    _usar_antigua(False)
    estado["numpy"] = "ninguna"
    estado["motivo"] = "; ".join(errores)
    return False


def resumen():
    """Para sistema.txt: qué instrucciones hay y qué biblioteca se ha cargado."""
    ins = estado["instrucciones"] or instrucciones()
    return {"instrucciones del procesador": ", ".join(f"{n} {'sí' if v else 'no'}" for n, v in ins.items()) or tr("no se han podido consultar"),
            "biblioteca de cálculo": f"{estado['numpy'] or 'oficial'} ({estado['motivo'] or tr('sin elegir')})"}


def avisar_incompatible(registro=None):
    """Dice en voz alta, y en un cuadro que lee el lector de pantalla, que este ordenador no puede con el juego."""
    faltan = [n for n in NECESARIAS if estado["instrucciones"] and not estado["instrucciones"].get(n)]
    if registro is not None:
        registro.error("arranque", "El procesador no es compatible con el juego", traza="",
                       faltan=", ".join(faltan) or "no se sabe", detalle=estado["motivo"])
    try:
        from .voz import Voz
        Voz().decir(AVISO, True)
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, AVISO, tr("Puerto Bravo: Ley del Asfalto"), 0x10 | 0x10000)     # icono de error, en primer plano
    except Exception:
        pass
