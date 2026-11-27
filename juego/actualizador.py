"""Actualizaciones del juego.

Cómo funciona:

1. Se lee un archivo pequeño, version.json, de la fuente que el jugador haya elegido en Opciones:
   el servidor del juego, GitHub, las dos (gana la versión más nueva; si una falla se usa la otra)
   o una dirección personalizada.
2. Ese archivo va FIRMADO (Ed25519). La firma se comprueba antes de mirar nada más, venga de donde venga:
   la fuente solo decide de dónde se descarga, no en quién se confía. Sin firma válida no se actualiza.
3. Si la versión es más nueva que la instalada, se descarga el ZIP, se comprueban su tamaño y su SHA-256
   (que también van firmados), y se extrae en una carpeta aparte, rechazando rutas peligrosas.
4. Antes de cerrar, el juego comprueba lo que suele estropear una instalación: que hay sitio en el disco (lo que
   hace falta de verdad, calculado), que se puede escribir en su carpeta y que no está abierto el editor de mods.
   Si algo no está bien, lo dice y no se cierra.
5. Si hay un servidor en línea abierto (el de consola o el panel), no hace falta cerrarlo a mano: el juego lo dice,
   pide permiso, apunta qué había abierto y con qué argumentos, y le deja al servidor la orden de pararse «para
   actualizar». El servidor avisa a los jugadores, espera sus guardados, lo guarda todo y se cierra.
6. Un pequeño .bat espera a que el juego y el servidor se cierren, guarda una copia del programa, copia la versión
   nueva, vuelve a arrancar el servidor que hubiera (tanto si ha ido bien como si no) y vuelve a abrir el juego.
   Si algo falla, restaura la copia. La copia es solo de programa: lo que el servidor guarda mientras funciona (su
   base de datos, su configuración, sus fichas) ni se copia ni se restaura, para no devolverlo nunca a un momento anterior.
7. El .bat apunta cada paso en data/logs/actualizacion.log, con el archivo que no se pudo copiar y el error de
   Windows. Si falla, el juego lee ese registro al reabrirse y dice el motivo.

Lo que nunca se toca: partidas, opciones, tu música, tus mods. Solo se admiten direcciones https.
No se envía ningún dato del jugador: son descargas normales.
"""
from .i18n import tr
import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from . import VERSION, ed25519, rutas

NOMBRE_APP = "PuertoBravo"
EJECUTABLE = "PuertoBravo.exe"
URL_SERVIDOR = "https://xebolax.synology.me/PuertoBravo/version.json"
REPOSITORIO_GITHUB = "hxebolax/PuertoBravo"
URL_GITHUB = f"https://github.com/{REPOSITORIO_GITHUB}/releases/latest/download/version.json"
# Claves públicas con las que se aceptan versiones. La privada no está en el juego, ni en el repositorio, ni en el servidor.
CLAVES_PUBLICAS = ("2793c73fefcdb5518570569e41e9ae291373c41126b30d4b3fb99359b09ca23f",)

FUENTES = ("servidor", "github", "ambas", "personalizada")
NOMBRE_FUENTE = {"servidor": tr("el servidor del juego"), "github": "GitHub", "ambas": tr("el servidor del juego y GitHub"), "personalizada": tr("una dirección personalizada")}
CAMPO_FIRMA = "firma_ed25519"
ARG_TRAS_ACTUALIZAR = "--tras-actualizar"
ARG_RELANZAR = "--relanzar-servidores"          # el instalador llama así al juego para que vuelva a arrancar los servidores que había
NOTA_SERVIDORES = "servidores_abiertos.json"    # lo que había abierto antes de actualizar, en la carpeta de trabajo
ORDEN_SERVIDOR = "parar.txt"                    # el archivo de órdenes que mira el servidor en su carpeta de datos
MAX_MANIFIESTO = 256 * 1024
MAX_DESCARGA = 3 * 1024 ** 3
MAX_EXPANDIDO = 6 * 1024 ** 3
MAX_MIEMBROS = 60000
TIEMPO = 20
# Carpetas del jugador: la actualización no las pisa ni las borra jamás.
INTOCABLES = ("partidas", "config", "mi_musica", "actualizacion", "logs", "ia_local", "propias", "voces_generadas")
# Lo vivo del servidor en línea, dentro de su carpeta servidor: las fichas de «en marcha», la carpeta de datos de serie (la
# base de datos, el certificado, el registro, sus copias), la configuración y el archivo de órdenes. Una versión no lo
# trae, la instalación no lo pisa, y ni se guarda en la copia de seguridad ni se restaura.
CARPETA_SERVIDOR = "servidor"
VIVO_SERVIDOR = ("en_marcha", "datos_servidor")
ARCHIVOS_VIVOS_SERVIDOR = ("servidor.conf", "parar.txt")
RAROS = '%"!^&'                                 # símbolos que un .bat no lleva bien en una ruta


def de_windows(nombre):
    """Una utilidad de Windows (tasklist.exe, cmd.exe) con su ruta entera, para no depender del PATH: con Git Bash o Cygwin
    por delante, «find» o «tasklist» pueden ser otros programas."""
    for raiz in (os.environ.get("SystemRoot"), os.environ.get("windir")):
        ruta = os.path.join(raiz, "System32", nombre) if raiz else ""
        if ruta and os.path.isfile(ruta):
            return ruta
    return nombre


class ErrorActualizacion(Exception):
    pass


class ErrorRed(ErrorActualizacion):
    pass


class ErrorFirma(ErrorActualizacion):
    pass


class Cancelado(ErrorActualizacion):
    pass


class Info:
    def __init__(self, version, archivo, sha256, tamano, urls, novedades, fuente):
        self.version = version
        self.archivo = archivo
        self.sha256 = sha256
        self.tamano = tamano
        self.urls = urls
        self.novedades = novedades
        self.fuente = fuente


# ------------------------------------------------------------------ versiones
def clave_version(texto):
    partes = []
    for trozo in str(texto).strip().lstrip("vV").split("."):
        digitos = "".join(c for c in trozo if c.isdigit())
        if not digitos:
            raise ValueError(tr('Versión no válida: {texto!r}').format(texto=(texto)))
        partes.append(int(digitos))
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes)


def es_mas_nueva(a, b):
    return clave_version(a) > clave_version(b)


# ---------------------------------------------------------------------- firma
def serializar_canonico(manifiesto):
    """Los bytes que se firman: el JSON ordenado, con separadores fijos y sin el campo de la firma."""
    datos = {k: v for k, v in manifiesto.items() if k != CAMPO_FIRMA}
    return json.dumps(datos, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def verificar_firma(manifiesto, claves=None):
    claves = CLAVES_PUBLICAS if claves is None else claves
    firma_b64 = manifiesto.get(CAMPO_FIRMA)
    if not isinstance(firma_b64, str) or not firma_b64:
        raise ErrorFirma(tr("La información de la versión no está firmada."))
    try:
        firma = base64.b64decode(firma_b64, validate=True)
    except ValueError:
        raise ErrorFirma(tr("La firma de la versión está dañada.")) from None
    mensaje = serializar_canonico(manifiesto)
    for clave in claves:
        try:
            pub = bytes.fromhex(clave)
        except ValueError:
            continue
        if ed25519.verificar(pub, mensaje, firma):
            return
    raise ErrorFirma(tr("La firma de la versión no es válida. No se actualiza."))


# ------------------------------------------------------------------------ red
def comprobar_url(url):
    p = urllib.parse.urlsplit(str(url))
    if p.scheme != "https" or not p.hostname:
        raise ErrorActualizacion(tr("La dirección tiene que empezar por https."))
    if p.username or p.password:
        raise ErrorActualizacion(tr("La dirección no puede llevar usuario ni contraseña."))


class _SoloHttps(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        comprobar_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def abrir_red(url, tiempo=TIEMPO, desde=0):
    """Abre una dirección https y devuelve el objeto de lectura. Es lo único que toca la red.
    Con `desde`, pide el archivo a partir de ese byte, para seguir una descarga que se cortó."""
    comprobar_url(url)
    abridor = urllib.request.build_opener(_SoloHttps)
    cabeceras = {"User-Agent": "PuertoBravo-Actualizador", "Accept": "*/*"}
    if desde:
        cabeceras["Range"] = f"bytes={int(desde)}-"
    pet = urllib.request.Request(url, headers=cabeceras)
    return abridor.open(pet, timeout=tiempo)


REINTENTOS = 5          # veces que se retoma una descarga cortada, por cada dirección
PAGINA_DESCARGAS = f"https://github.com/{REPOSITORIO_GITHUB}/releases/latest"       # de donde se baja el ZIP para actualizar a mano
BLOQUEO_RED = (tr("Si tu conexión funciona para lo demás, puede que un filtro de red como AdGuard, un antivirus o un cortafuegos esté bloqueando al juego: "
               "añade Puerto Bravo a sus excepciones, o prueba la otra fuente en Actualizar desde."))
A_MANO = tr("Si no hay manera, se puede actualizar a mano: lo explica Opciones, Actualizaciones, Actualizar a mano.")


class ErrorDisco(ErrorActualizacion):
    """No se ha podido escribir en el disco: no es cosa de la conexión."""


def error_de_disco(e, que=tr("guardar la descarga")):
    """Un fallo de Windows al escribir, dicho para quien juega: carpeta protegida, disco lleno, antivirus u otro programa."""
    cod = getattr(e, "winerror", None)
    if cod in _SIN_SITIO or getattr(e, "errno", None) == 28:
        return ErrorDisco(tr('El disco se ha llenado y no se ha podido {que}. Libera espacio y vuelve a intentarlo.').format(que=(que)))
    if cod in _ANTIVIRUS:
        return ErrorDisco(tr('El antivirus ha bloqueado un archivo y no se ha podido {que}. Añade la carpeta del juego a las excepciones del antivirus y vuelve a intentarlo. ').format(que=(que)) + A_MANO)
    if cod in _EN_USO:
        return ErrorDisco(tr('No se ha podido {que} porque otro programa estaba usando el archivo. Suele ser el antivirus, que lo está examinando, o el juego abierto dos veces. Cierra las demás ventanas de Puerto Bravo, espera un momento y vuelve a intentarlo.').format(que=(que)))
    if isinstance(e, PermissionError) or cod in _DENEGADO:
        return ErrorDisco(tr('Windows no deja escribir en la carpeta del juego y no se ha podido {que}. Suele pasar si el juego está en una carpeta protegida, como Archivos de programa, o si un antivirus o el acceso controlado a carpetas lo impiden. Mueve el juego a otra carpeta, por ejemplo dentro de Documentos, o añade una excepción en el antivirus. ').format(que=(que)) + A_MANO)
    return ErrorDisco(tr('No se ha podido {que}: Windows dio el error {v}. Puede ser el antivirus. ').format(que=(que), v=(cod or getattr(e, 'errno', None) or type(e).__name__)) + A_MANO)


def _abrir_desde(abrir, url, desde):
    """Abre la descarga para seguirla desde un byte. Devuelve la lectura y el byte por el que empieza de verdad:
    si el servidor no sabe continuar, manda el archivo entero y se empieza de cero."""
    if not desde:
        return abrir(url), 0
    try:
        r = abrir(url, desde=desde)
    except TypeError:
        return abrir(url), 0
    return r, (desde if getattr(r, "status", None) == 206 else 0)


def _leer_manifiesto(url, nombre, abrir):
    try:
        with abrir(url) as r:
            crudo = r.read(MAX_MANIFIESTO + 1)
    except ErrorActualizacion:
        raise
    except urllib.error.HTTPError as e:
        raise ErrorRed(tr('Al consultar {nombre}, respondió con el error {code}.').format(nombre=(nombre), code=(e.code))) from None
    except (OSError, ValueError) as e:
        raise ErrorRed(tr('No se pudo conectar con {nombre}. Comprueba la conexión a internet. Si usas AdGuard, un antivirus o un cortafuegos, puede estar bloqueando al juego.').format(nombre=(nombre))) from e
    if len(crudo) > MAX_MANIFIESTO:
        raise ErrorFirma(tr('La información de versión de {nombre} es demasiado grande.').format(nombre=(nombre)))
    try:
        m = json.loads(crudo.decode("utf-8-sig"))
    except (ValueError, UnicodeDecodeError):
        raise ErrorFirma(tr('La información de versión de {nombre} está dañada.').format(nombre=(nombre))) from None
    if not isinstance(m, dict):
        raise ErrorFirma(tr('La información de versión de {nombre} está dañada.').format(nombre=(nombre)))
    return m


def fuentes_a_consultar(fuente, url_personalizada=""):
    if fuente == "github":
        return [("github", URL_GITHUB)]
    if fuente == "ambas":
        return [("servidor", URL_SERVIDOR), ("github", URL_GITHUB)]
    if fuente == "personalizada":
        url = str(url_personalizada or "").strip()
        if not url:
            raise ErrorActualizacion(tr("Has elegido una dirección personalizada, pero no has escrito ninguna. Escríbela en Opciones, Actualizaciones."))
        comprobar_url(url)
        return [("personalizada", url)]
    return [("servidor", URL_SERVIDOR)]


def _info(m, url_manifiesto, fuente, ambas):
    version = str(m.get("version", ""))
    archivo = str(m.get("file", ""))
    sha = str(m.get("sha256", "")).lower()
    tamano = m.get("size")
    clave_version(version)
    if not archivo or os.path.basename(archivo) != archivo or not archivo.lower().endswith(".zip"):
        raise ErrorFirma(tr("El nombre del archivo de la versión no es válido."))
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ErrorFirma(tr("La huella del archivo de la versión no es válida."))
    if not isinstance(tamano, int) or isinstance(tamano, bool) or not 0 < tamano <= MAX_DESCARGA:
        raise ErrorFirma(tr("El tamaño del archivo de la versión no es válido."))
    junto = urllib.parse.urljoin(url_manifiesto, urllib.parse.quote(archivo))
    principal = str(m.get("url") or "")
    espejos = m.get("espejos") if isinstance(m.get("espejos"), dict) else {}
    github = str(espejos.get("github") or "")
    if fuente == "github":
        orden = [github or junto] + ([principal] if ambas else [])
    elif fuente == "personalizada":
        orden = [junto, principal, github]          # el ZIP junto al version.json; si no está, las direcciones firmadas
    else:
        orden = [principal or junto] + ([github] if ambas else [])
    urls = []
    for u in orden:
        if u and u not in urls:
            try:
                comprobar_url(u)
                urls.append(u)
            except ErrorActualizacion:
                pass
    if not urls:
        raise ErrorFirma(tr("La versión no indica de dónde descargarla."))
    return Info(version, archivo, sha, tamano, urls, notas_en_mi_idioma(m), fuente)


def notas_en_mi_idioma(m):
    """Las novedades de la versión en el idioma del juego. Desde la 1.7.3 el version.json las trae por idioma en
    novedades_por_idioma; un idioma que no las tiene oye las inglesas, y si tampoco, las españolas de novedades, que es
    lo único que traen las versiones anteriores y lo que leen los juegos anteriores."""
    from . import i18n
    por_idioma = m.get("novedades_por_idioma") if isinstance(m.get("novedades_por_idioma"), dict) else {}
    actual = i18n.idioma_novedades()                       # desde la 1.7.3, las novedades son en español o en inglés
    for cod in dict.fromkeys((actual, "en" if actual != i18n.ORIGEN else i18n.ORIGEN)):
        if isinstance(por_idioma.get(cod), str) and por_idioma[cod].strip():
            return por_idioma[cod]
    return str(m.get("novedades") or "")


def comprobar(fuente="servidor", url_personalizada="", abrir=None, claves=None, version_actual=None):
    """Consulta la fuente elegida. Devuelve la Info de la versión nueva, o None si ya tienes la última."""
    abrir = abrir or abrir_red
    actual = version_actual or VERSION
    lista = fuentes_a_consultar(fuente if fuente in FUENTES else "servidor", url_personalizada)
    ambas = len(lista) > 1
    encontradas, errores = [], []
    for nombre, url in lista:
        donde = NOMBRE_FUENTE[nombre]
        try:
            m = _leer_manifiesto(url, donde, abrir)
            verificar_firma(m, claves)                 # antes de mirar ningún otro campo
            encontradas.append(_info(m, url, nombre, ambas))
        except ErrorActualizacion as e:
            errores.append(e)
        except ValueError as e:
            errores.append(ErrorFirma(str(e)))
    if not encontradas:
        if len(errores) > 1:
            grave = next((e for e in errores if isinstance(e, ErrorFirma)), errores[0])
            raise type(grave)(tr("No se pudo comprobar en ninguna de las dos fuentes. ") + " ".join(str(e) for e in errores))
        raise errores[0]
    mejor = max(encontradas, key=lambda i: clave_version(i.version))
    return mejor if es_mas_nueva(mejor.version, actual) else None


# ------------------------------------------------------------------- descarga
def carpeta_trabajo():
    return os.path.join(rutas.DATA, "actualizacion")


def sha256_de(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def descargar(info, carpeta=None, progreso=None, cancelado=None, abrir=None):
    """Descarga el ZIP probando las direcciones en orden y comprueba tamaño y SHA-256. Devuelve su ruta."""
    abrir = abrir or abrir_red
    carpeta = carpeta or carpeta_trabajo()
    destino = os.path.join(carpeta, info.archivo)
    try:                                                   # antes de pedir nada a la red: ¿se puede escribir ahí?
        os.makedirs(carpeta, exist_ok=True)
        with open(destino + ".parcial", "ab"):
            pass
    except OSError as e:
        raise error_de_disco(e) from e
    ultimo = None
    for url in info.urls:
        try:
            hecho = 0
            # Si la conexión se corta a medias, no se empieza otra vez: se retoma por donde iba, varias veces.
            for intento in range(REINTENTOS + 1):
                antes = hecho
                try:
                    r, hecho = _abrir_desde(abrir, url, hecho)
                    try:
                        f = open(destino + ".parcial", "ab" if hecho else "wb")
                    except OSError as e:
                        r.close()
                        raise error_de_disco(e) from e
                    with r, f:
                        while True:
                            if cancelado and cancelado():
                                raise Cancelado(tr("Descarga cancelada."))
                            bloque = r.read(64 * 1024)                # trozos pequeños: Escape corta enseguida aunque la red vaya lenta
                            if not bloque:
                                break
                            hecho += len(bloque)
                            if hecho > info.tamano:
                                raise ErrorFirma(tr("El archivo descargado es más grande de lo que debería."))
                            try:
                                f.write(bloque)
                            except OSError as e:           # el disco, no la red: no tiene sentido reintentar ni culpar a la conexión
                                raise error_de_disco(e) from e
                            if progreso:
                                progreso(hecho, info.tamano)
                except (OSError, ValueError):
                    if intento == REINTENTOS or (hecho <= antes and intento >= 2):       # ni avanza: no insistir más con esta dirección
                        raise
                    time.sleep(min(4.0, 0.5 * (intento + 1)) if abrir is abrir_red else 0)
                    continue
                if hecho >= info.tamano or (hecho <= antes and intento >= 2):
                    break
            if hecho != info.tamano:
                raise ErrorRed(tr("La descarga se ha cortado antes de terminar, y no se ha podido retomar. Prueba otra vez dentro de un rato. ") + BLOQUEO_RED)
            try:
                suma = sha256_de(destino + ".parcial")
            except OSError as e:                           # estaba entero y ya no se puede leer: lo ha retirado o lo retiene otro programa
                raise ErrorDisco(tr("La descarga terminó, pero el archivo ha desaparecido o no se deja leer: casi siempre es el antivirus, que lo ha apartado. "
                                 "Añade la carpeta del juego a sus excepciones y vuelve a intentarlo. ") + A_MANO) from e
            if not hmac.compare_digest(suma, info.sha256):
                raise ErrorFirma(tr("El archivo descargado no coincide con el que se publicó. No se instala."))
            try:
                os.replace(destino + ".parcial", destino)
            except OSError as e:
                raise error_de_disco(e) from e
            return destino
        except Cancelado:
            _quitar(destino + ".parcial")
            raise
        except ErrorDisco:                                 # con otra dirección pasaría lo mismo
            _quitar(destino + ".parcial")
            raise
        except ErrorActualizacion as e:
            ultimo = e
        except (OSError, ValueError) as e:
            ultimo = ErrorRed(tr("No se pudo descargar la versión nueva. Comprueba la conexión a internet. ") + BLOQUEO_RED)
            ultimo.__cause__ = e
        _quitar(destino + ".parcial")
    raise ultimo or ErrorRed(tr("No se pudo descargar la versión nueva."))


def _quitar(ruta):
    try:
        os.remove(ruta)
    except OSError:
        pass


def extraer(ruta_zip, carpeta):
    """Extrae el ZIP en una carpeta vacía, rechazando cualquier ruta que intente salirse de ella."""
    if os.path.isdir(carpeta):
        shutil.rmtree(carpeta, ignore_errors=True)
    try:
        os.makedirs(carpeta, exist_ok=True)
    except OSError as e:
        raise error_de_disco(e, tr("preparar la versión nueva")) from e
    raiz = os.path.realpath(carpeta)
    traia_el_juego = False
    try:
        with zipfile.ZipFile(ruta_zip) as z:
            miembros = z.infolist()
            traia_el_juego = any(m.filename.replace("\\", "/").strip("/") == EJECUTABLE for m in miembros)
            if len(miembros) > MAX_MIEMBROS or sum(m.file_size for m in miembros) > MAX_EXPANDIDO:
                raise ErrorFirma(tr("El paquete de la versión es demasiado grande."))
            for m in miembros:
                nombre = m.filename.replace("\\", "/")
                partes = [p for p in nombre.split("/") if p]
                if nombre.startswith("/") or ":" in nombre or ".." in partes or (m.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ErrorFirma(tr("El paquete de la versión contiene rutas no permitidas. No se instala."))
                destino = os.path.realpath(os.path.join(raiz, *partes))
                if destino != raiz and not destino.startswith(raiz + os.sep):
                    raise ErrorFirma(tr("El paquete de la versión contiene rutas no permitidas. No se instala."))
                if m.is_dir():
                    os.makedirs(destino, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                with z.open(m) as origen, open(destino, "wb") as f:
                    shutil.copyfileobj(origen, f, 1024 * 1024)
    except zipfile.BadZipFile:
        raise ErrorFirma(tr("El paquete de la versión está dañado.")) from None
    except ErrorActualizacion:
        raise
    except OSError as e:
        raise error_de_disco(e, tr("preparar la versión nueva")) from e
    if not os.path.isfile(os.path.join(raiz, EJECUTABLE)):
        if traia_el_juego:                                 # venía en el paquete y, recién sacado, ya no está: alguien lo ha quitado
            raise ErrorDisco(tr("El programa del juego venía en la descarga, pero ha desaparecido nada más sacarlo: casi siempre es el antivirus, que lo ha puesto en cuarentena. "
                             "Añade la carpeta del juego a las excepciones del antivirus y vuelve a intentarlo. ") + A_MANO)
        raise ErrorFirma(tr("El paquete de la versión no contiene el juego."))
    for base, dirs, _ in os.walk(raiz):               # por si acaso: lo personal no viaja en una versión
        for d in list(dirs):
            if d in INTOCABLES and os.path.basename(base) in ("data", "radio"):
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)
                dirs.remove(d)
    for d in VIVO_SERVIDOR:                           # ni lo de un servidor: sus datos, su configuración, sus fichas
        shutil.rmtree(os.path.join(raiz, CARPETA_SERVIDOR, d), ignore_errors=True)
    for n in ARCHIVOS_VIVOS_SERVIDOR:
        _quitar(os.path.join(raiz, CARPETA_SERVIDOR, n))
    return raiz


# ----------------------------------------------------------------- instalación
def puede_instalar():
    """Solo el juego compilado se sustituye a sí mismo. Desde el código fuente se puede comprobar y avisar."""
    return bool(getattr(sys, "frozen", False))


def carpeta_programa():
    return os.path.dirname(os.path.abspath(sys.executable)) if puede_instalar() else rutas.base()


REGISTRO_INSTALADOR = "actualizacion.log"
# Los pasos del instalador, como se apuntan en su registro y como se le cuentan al jugador.
PASOS = {"esperar_cierre": tr("esperar a que el juego se cerrara"), "esperar_programas": tr("esperar a que se cerraran los demás programas del juego"),
         "copia_seguridad": tr("guardar una copia de la versión que tenías"), "copiar_nueva": tr("copiar la versión nueva"),
         "copiar_lib": tr("copiar el programa nuevo"), "copiar_datos": tr("copiar los datos nuevos del juego"), "restaurar": tr("volver a dejar la versión anterior")}
# Los otros programas del juego: con uno abierto, Windows no deja sustituir su archivo.
OTROS_PROGRAMAS = {"EditorMods.exe": tr("el editor de mods"), "PuertoBravoServidor.exe": tr("el servidor en línea"), "PuertoBravoServidorPanel.exe": tr("el panel del servidor en línea")}
PROGRAMAS_SERVIDOR = ("PuertoBravoServidor.exe", "PuertoBravoServidorPanel.exe")
MARGEN_DISCO = 48 * 1024 ** 2


def ruta_registro_instalador(programa=None):
    """Dónde apunta el instalador lo que hace: en la carpeta de registros, junto a los de las sesiones."""
    return os.path.join(programa, "data", "logs", REGISTRO_INSTALADOR) if programa else os.path.join(rutas.DATA, "logs", REGISTRO_INSTALADOR)


def plan_copia(nueva):
    """Qué guarda el instalador antes de copiar, que es lo único que devuelve si falla: [(subcarpeta, archivos)], con
    ``archivos`` None si va la subcarpeta entera. Es justo lo que la versión nueva va a sustituir, nombre a nombre, y nada
    más: lo que haya en la carpeta del juego que la versión no trae (la configuración y los datos de un servidor en línea,
    estén donde estén) ni se copia ni se restaura. De la carpeta servidor, solo sus programas y su guía; ``data`` va aparte."""
    def mirar(sub):
        base = os.path.join(nueva, sub)
        try:
            nombres = sorted(n for n in os.listdir(base) if not any(c in n for c in RAROS))
        except OSError:
            return [], []
        return [n for n in nombres if os.path.isfile(os.path.join(base, n))], [n for n in nombres if os.path.isdir(os.path.join(base, n))]

    archivos, carpetas = mirar("")
    plan = [("", archivos)] if archivos else []
    for c in carpetas:
        if c.lower() == "data":
            continue
        if c.lower() != CARPETA_SERVIDOR:
            plan.append((c, None))
            continue
        suyos, dentro = mirar(c)
        suyos = [n for n in suyos if n.lower() not in ARCHIVOS_VIVOS_SERVIDOR]
        if suyos:
            plan.append((c, suyos))
        plan += [(os.path.join(c, d), None) for d in dentro if d.lower() not in VIVO_SERVIDOR]
    return plan


def escribir_instalador(nueva, programa=None, pid=None, version=""):
    """Escribe el .bat que sustituye el programa cuando el juego se haya cerrado. Devuelve su ruta.
    El .bat apunta cada paso en data\\logs\\actualizacion.log: qué hace, con qué resultado y, si falla, qué archivo y por qué."""
    programa = programa or carpeta_programa()
    pid = os.getpid() if pid is None else pid
    for ruta in (nueva, programa):
        if any(c in ruta for c in '%"!^&'):
            raise ErrorActualizacion(tr("El juego está en una carpeta con símbolos especiales en el nombre y no se puede actualizar solo. Descarga la versión nueva a mano."))
    trabajo = os.path.dirname(nueva)
    copia = os.path.join(trabajo, "anterior")
    excluir = " ".join(INTOCABLES + VIVO_SERVIDOR)           # lo vivo de un servidor no lo trae una versión; si lo trajera, no se copia
    callado = '/njh /njs /ndl /nfl /np /log+:"%REG%"'        # robocopy no lista lo que va bien: en el registro solo quedan los errores
    # Las utilidades de Windows, con su ruta entera: con otro «find» por delante en el PATH (Git Bash, Cygwin), las esperas no esperaban.
    robocopy, tasklist, find, ping = ('"%SYS%\\' + n + '"' for n in ("robocopy.exe", "tasklist.exe", "find.exe", "ping.exe"))

    def apunta(texto):
        return f'>>"%REG%" echo {texto}'

    def paso(nombre, orden, vital=True, si=None):
        """Un paso con robocopy: se apunta que empieza, se hace, y se apunta el código con el que termina (8 o más es fallo)."""
        lineas = [f'set PASO={nombre}', apunta(f'PASO {nombre}'), orden, "set RC=%errorlevel%", apunta(f'RESULTADO {nombre} codigo=%RC%')]
        if vital:
            lineas.append("if %RC% geq 8 goto fallo")
        if si:                                               # solo si existe esa carpeta en la versión nueva
            salto = f"sin_{nombre}"
            lineas = [f'if not exist "{si}" goto {salto}'] + lineas + [f":{salto}"]
        return lineas

    lineas = [
        "@echo off", "setlocal", 'set "SYS=%SystemRoot%\\System32"', 'if not exist "%SYS%\\robocopy.exe" set "SYS=%windir%\\System32"',
        '"%SYS%\\chcp.com" 65001 >nul',
        f'set "APP={programa}"', f'set "NUEVA={nueva}"', f'set "COPIA={copia}"', f'set "NOTA={os.path.join(trabajo, NOTA_SERVIDORES)}"',
        'set "REG=%APP%\\data\\logs\\' + REGISTRO_INSTALADOR + '"', "set PASO=empezar", "set RC=0",
        'if not exist "%APP%\\data\\logs" mkdir "%APP%\\data\\logs"',
        f'>"%REG%" echo Instalador de Puerto Bravo. Actualizacion a la version {version}.',
        apunta("EMPIEZA %date% %time%"),
        f'echo Actualizando Puerto Bravo a la version {version}. No cierres esta ventana.',
        "set PASO=esperar_cierre", apunta("PASO esperar_cierre"),
        "set /a N=0", ":espera",
        f'{tasklist} /fi "PID eq {pid}" 2>nul | {find} " {pid} " >nul',
        "if errorlevel 1 goto programas",
        "set /a N+=1", "if %N% geq 90 goto no_cierra",
        f'{ping} -n 2 127.0.0.1 >nul', "goto espera",
        # Si el editor de mods, el servidor en línea o su panel están en marcha, sus programas no se pueden sustituir: se
        # espera a que se cierren, y si no se cierran, no se actualiza a medias.
        ":programas",
        "set PASO=esperar_programas", apunta("PASO esperar_programas"), "set /a N=0",
        ":mirar",
    ]
    for exe in OTROS_PROGRAMAS:
        # En CSV (/fo csv): en su tabla de siempre, tasklist recorta el nombre del programa a 25 letras, y con eso el panel
        # del servidor (PuertoBravoServidorPanel.exe, 28) no se encontraba nunca: se copiaba con él todavía abierto.
        lineas += [f'{tasklist} /fi "IMAGENAME eq {exe}" /fo csv /nh 2>nul | {find} /i "{exe}" >nul', "if not errorlevel 1 goto ocupado"]
    lineas += [
        "goto copiar",
        ":ocupado",
        "if %N%==0 echo Esperando a que se cierren el servidor en linea o el editor de mods de Puerto Bravo. El servidor avisa a los jugadores y se cierra solo.",
        "set /a N+=1", "if %N% geq 180 goto no_cierra",
        f'{ping} -n 2 127.0.0.1 >nul', "goto mirar",
        ":no_cierra",
        apunta("FALLO paso=%PASO% codigo=0 motivo=sigue_abierto"),
        "goto abrir",
        ":copiar",
        'if exist "%COPIA%" rmdir /s /q "%COPIA%"',
    ]
    # La copia de seguridad: solo programa, y solo lo que la versión nueva va a sustituir (plan_copia). De data, los datos del
    # juego, los mods y los manuales. No entran data\sonidos, musica, radio ni phonon, y es a propósito: son cientos de megas,
    # llevan archivos de quien juega que no se tocan jamás, y son solo audio y modelos de voz, que se cargan por su nombre y
    # con tolerancia (un sonido de otra versión suena igual, y los originales que falten se vuelven a crear). Si la instalación
    # falla, la versión anterior funciona con ellos, y la siguiente actualización que salga bien los deja al día.
    lineas += ["set PASO=copia_seguridad", apunta("PASO copia_seguridad"), "set RC=0"]
    copias = []
    for sub_, archivos in plan_copia(nueva):
        origen, destino = ("%APP%\\" + sub_, "%COPIA%\\" + sub_) if sub_ else ("%APP%", "%COPIA%")
        if archivos is None:
            copias.append(f'if exist "{origen}\\" {robocopy} "{origen}" "{destino}" /e /r:2 /w:1 {callado}')
        for k in range(0, len(archivos or ()), 12):          # por tandas: una línea de .bat no puede ser muy larga
            nombres = " ".join(f'"{n}"' for n in archivos[k:k + 12])
            copias.append(f'{robocopy} "{origen}" "{destino}" {nombres} /r:2 /w:1 {callado}')
    copias += [f'if exist "%APP%\\data\\{sub_}\\" {robocopy} "%APP%\\data\\{sub_}" "%COPIA%\\data\\{sub_}" /e /r:2 /w:1 {callado}' for sub_ in ("datos", "mods", "docs")]
    for orden in copias:
        lineas += [orden, "if %errorlevel% gtr %RC% set RC=%errorlevel%"]
    lineas.append(apunta("RESULTADO copia_seguridad codigo=%RC%"))
    lineas += paso("copiar_nueva", f'{robocopy} "%NUEVA%" "%APP%" /e /xd {excluir} /xf {" ".join(ARCHIVOS_VIVOS_SERVIDOR)} /r:3 /w:1 {callado}')
    lineas += paso("copiar_lib", f'{robocopy} "%NUEVA%\\lib" "%APP%\\lib" /mir /r:3 /w:1 {callado}', si="%NUEVA%\\lib")
    lineas += paso("copiar_datos", f'{robocopy} "%NUEVA%\\data\\datos" "%APP%\\data\\datos" /mir /r:3 /w:1 {callado}', si="%NUEVA%\\data\\datos")
    lineas += [
        'if exist "%APP%\\data\\voces_serie" rmdir /s /q "%APP%\\data\\voces_serie"',     # las voces van ahora en data\voces
        'rmdir /s /q "%NUEVA%"',
        'rmdir /s /q "%COPIA%"',
        apunta("TERMINADA bien %date% %time%"),
        # Si antes de actualizar había un servidor en línea abierto, se vuelve a arrancar igual que estaba. Lo hace el
        # propio juego, ya actualizado, que sabe leer la nota y lo apunta en este mismo registro.
        f'if exist "%NOTA%" start "" /wait "%APP%\\{EJECUTABLE}" {ARG_RELANZAR} "%NOTA%"',
        f'start "" "%APP%\\{EJECUTABLE}" {ARG_TRAS_ACTUALIZAR}',
        "goto fin",
        ":fallo",
        apunta("FALLO paso=%PASO% codigo=%RC% motivo=copia"),
        "echo La actualizacion ha fallado. Se restaura la version anterior.",
    ]
    # Se devuelve lo que se guardó, que es solo programa: lo que el servidor guardó al cerrarse se queda como lo dejó.
    lineas += paso("restaurar", f'{robocopy} "%COPIA%" "%APP%" /e /r:3 /w:1 {callado}', vital=False)
    lineas += [
        ":abrir",
        apunta("TERMINADA mal %date% %time%"),
        # La instalación ha fallado, pero el servidor que hubiera abierto vuelve a arrancar igualmente, con la versión de antes.
        f'if exist "%NOTA%" start "" /wait "%APP%\\{EJECUTABLE}" {ARG_RELANZAR} "%NOTA%"',
        f'start "" "%APP%\\{EJECUTABLE}" --actualizacion-fallida',
        ":fin",
        "endlocal",
        '(goto) 2>nul & del "%~f0"',
    ]
    ruta = os.path.join(trabajo, "instalar_actualizacion.bat")
    with open(ruta, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    return ruta


# ------------------------------------------------- el registro del instalador
# Errores de Windows que salen al copiar, y lo que quieren decir para quien juega.
_EN_USO = (32, 33)
_DENEGADO = (5, 19, 1920)
_SIN_SITIO = (39, 112)
_ANTIVIRUS = (225, 226)


_RE_ERROR_COPIA = r"(ERROR\s+(\d+)\s+\(0x[0-9A-Fa-f]+\)\s+)(.*)$"
_RE_CAMINO = r"(?:[A-Za-z]:[\\/]|\\\\|<)[^\r\n]*$"


def _texto_registro(ruta):
    """El registro del instalador, como texto. Lo que apunta el .bat va sin tildes; lo de robocopy, en la codificación de la consola de Windows."""
    with open(ruta, "rb") as f:
        crudo = f.read(2 * 1024 * 1024)
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError:
        return "\n".join(_linea_de_windows(l) for l in crudo.replace(b"\r\n", b"\n").split(b"\n"))


_LETRAS = tr("áéíóúüñÁÉÍÓÚÜÑ¿¡")


def _linea_de_windows(crudo):
    """Una línea que ha escrito robocopy. No usa siempre la misma página de códigos: el error de Windows («está siendo
    utilizado») va en la de la consola, y sus propios avisos («se superó el límite de reintentos»), en la de Windows. Se
    prueba línea a línea y se queda la lectura con más letras nuestras; así ninguna sale con las letras cambiadas."""
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError:
        pass
    lecturas = []
    for pagina in (("oem", "mbcs") if os.name == "nt" else ("latin-1",)):
        try:
            lecturas.append(crudo.decode(pagina, errors="replace"))
        except LookupError:
            pass
    return max(lecturas, key=lambda t: sum(t.count(c) for c in _LETRAS)) if lecturas else crudo.decode("latin-1")


def _archivo_de(resto):
    """De lo que robocopy escribe tras el error («Copiando archivo D:\\Juegos\\PB\\EditorMods.exe»), el nombre del archivo."""
    import re
    camino = re.search(_RE_CAMINO, resto)
    if camino:
        return re.split(r"[\\/]", camino.group(0).rstrip("\\/ "))[-1]
    ultimo = resto.split()[-1] if resto.split() else ""
    return ultimo if "." in ultimo else ""


def limpiar_registro_instalador(ruta=None):
    """Quita del registro del instalador las carpetas de quien juega: de cada archivo que no se pudo copiar queda solo el nombre.
    Lo hace el juego al reabrirse, para que el registro se pueda enviar sin dar datos personales."""
    import re
    ruta = ruta or ruta_registro_instalador()
    try:
        lineas = _texto_registro(ruta).splitlines()
        limpias = []
        for linea in lineas:
            if not linea.strip():                              # robocopy deja líneas en blanco entre aviso y aviso
                continue
            m = re.search(_RE_ERROR_COPIA, linea)
            if m and re.search(_RE_CAMINO, m.group(3)):
                linea = linea[:m.start(3)] + re.sub(_RE_CAMINO, lambda c: _archivo_de(m.group(3)), m.group(3))
            limpias.append(linea)
        with open(ruta, "w", encoding="utf-8", newline="\r\n") as f:
            f.write("\n".join(limpias) + "\n")
    except OSError:
        pass


def leer_registro_instalador(ruta=None):
    """Lo que dejó apuntado el instalador: {"existe", "bien", "paso", "codigo", "motivo", "error", "archivo"}. Nunca falla."""
    import re
    r = {"existe": False, "bien": None, "paso": "", "codigo": 0, "motivo": "", "error": 0, "archivo": "", "relanzados": [], "sin_relanzar": []}
    try:
        texto = _texto_registro(ruta or ruta_registro_instalador())
    except OSError:
        return r
    r["existe"] = True
    paso_actual = ""
    for linea in texto.splitlines():
        linea = linea.strip()
        if linea.startswith("PASO ") or linea.startswith(tr("PASO ")):
            prefijo = "PASO " if linea.startswith("PASO ") else tr("PASO ")
            paso_actual = linea[len(prefijo):].strip()
        elif linea.startswith("TERMINADA ") or linea.startswith(tr("TERMINADA ")):
            r["bien"] = linea.split()[1] == "bien"          # «TERMINADA bien» lo escribe el .bat, siempre en español
        elif linea.startswith("SERVIDOR ") or linea.startswith(tr("SERVIDOR ")):
            # «SERVIDOR relanzado tipo=consola» o «SERVIDOR sin_relanzar tipo=panel motivo=servicio»
            m = re.search(r"SERVIDOR\s+(\S+)\s+tipo=(\S+)(?:\s+motivo=(\S+))?", linea)
            if m and m.group(1) in ("relanzado", tr("relanzado")):
                r["relanzados"].append(m.group(2))
                if "estado=parado" in linea or ("estado=" + tr("parado")) in linea:                   # un panel que estaba con el servidor parado, y así ha vuelto
                    r["parados"] = r.get("parados", 0) + 1
            elif m:
                r["sin_relanzar"].append((m.group(2), m.group(3) or ""))
        elif linea.startswith("FALLO ") or linea.startswith(tr("FALLO ")):
            m = re.search(r"paso=(\S+)\s+codigo=(-?\d+)(?:\s+motivo=(\S+))?", linea)
            if m:
                r["paso"], r["codigo"], r["motivo"] = m.group(1), int(m.group(2)), m.group(3) or ""
        else:
            # robocopy: «2026/11/18 10:00:00 ERROR 32 (0x00000020) Copiando archivo D:\Juegos\Puerto Bravo\EditorMods.exe»
            m = re.search(_RE_ERROR_COPIA, linea)
            if m and not r["error"] and paso_actual != "copia_seguridad":
                r["error"] = int(m.group(2))
                r["archivo"] = _archivo_de(m.group(3))            # vale con la ruta entera y con el registro ya limpio de rutas
                r.setdefault("paso_error", paso_actual)
    return r


def motivo_del_fallo(ruta=None):
    """Por qué no se instaló la última actualización, dicho para quien juega, a partir del registro del instalador."""
    r = leer_registro_instalador(ruta)
    if not r["existe"]:
        return tr("El instalador no dejó apuntado el motivo.")
    que = tr('el archivo {archivo}').format(archivo=(r['archivo'])) if r["archivo"] else tr("un archivo del juego")
    paso = PASOS.get(r["paso"] or r.get("paso_error", ""), "")
    if r["motivo"] == "sigue_abierto":
        if r["paso"] == "esperar_cierre":
            texto = tr("El juego no terminó de cerrarse a tiempo. Vuelve a intentarlo, y si se repite, reinicia el ordenador antes.")
        else:
            texto = (tr("El editor de mods, el servidor en línea o su panel seguían abiertos, y Windows no deja sustituir un programa en marcha. "
                     "Ciérralos y vuelve a intentarlo."))
    elif r["error"] in _EN_USO:
        texto = (tr('No se pudo sustituir {que} porque lo estaba usando otro programa. Cierra el editor de mods, el servidor en línea y cualquier otra ventana de Puerto Bravo, y vuelve a intentarlo. Si no tienes nada abierto, puede ser el antivirus, que lo estaba examinando.').format(que=(que)))
    elif r["error"] in _DENEGADO:
        texto = (tr('Windows no dejó escribir {que}: acceso denegado. Suele pasar si el juego está en una carpeta protegida, como Archivos de programa, si está activado el acceso controlado a carpetas de Windows, o si un antivirus lo impide. Mueve el juego a otra carpeta, por ejemplo dentro de Documentos, o añade una excepción en el antivirus.').format(que=(que)))
    elif r["error"] in _SIN_SITIO:
        texto = tr("No había sitio suficiente en el disco. Libera espacio y vuelve a intentarlo.")
    elif r["error"] in _ANTIVIRUS:
        texto = tr('El antivirus bloqueó {que}. Añade la carpeta del juego a las excepciones del antivirus y vuelve a intentarlo.').format(que=(que))
    elif r["error"]:
        texto = tr('No se pudo copiar {que}: Windows dio el error {error}.').format(que=(que), error=(r['error']))
    elif paso:
        texto = tr('Falló el paso de {paso}, y el instalador no apuntó con qué archivo.').format(paso=(paso))
    else:
        texto = tr("El instalador no llegó a apuntar en qué paso falló.")
    if paso and (r["error"] or r["motivo"] == "sigue_abierto"):
        texto += tr(' Fue al {paso}.').format(paso=(paso))
    return texto


# ------------------------------------------- comprobaciones antes de instalar
def _tareas():
    """Los nombres de los programas en marcha, en minúsculas. Vacío si no se puede preguntar."""
    try:
        sin_ventana = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        # en bytes y descodificando con manga ancha: tasklist escribe en la página de códigos de la consola, y un programa
        # con tilde en el nombre no puede hacer fallar la comprobación
        salida = subprocess.run([de_windows("tasklist.exe"), "/fo", "csv", "/nh"], capture_output=True, timeout=10, creationflags=sin_ventana).stdout.decode("utf-8", "replace").lower()
    except (OSError, subprocess.SubprocessError):
        return set()
    return {linea.split('","')[0].strip('"') for linea in salida.splitlines() if linea.startswith('"')}


def servidor_abierto():
    """¿Está en marcha el servidor en línea, o su panel? Con ellos abiertos no se pueden sustituir sus programas."""
    tareas = _tareas()
    return any(nombre.lower() in tareas for nombre in PROGRAMAS_SERVIDOR)


def carpeta_escribible(programa):
    """¿Se puede crear un archivo en la carpeta del juego? En una carpeta protegida, o con un antivirus estricto, no."""
    prueba = os.path.join(programa, f"prueba_de_escritura_{os.getpid()}.tmp")
    try:
        with open(prueba, "wb") as f:
            f.write(b"x")
        os.remove(prueba)
        return True
    except OSError:
        return False


def programas_abiertos(programa=None, tareas=None, salvo=()):
    """Los otros programas del juego que están abiertos, con el nombre que entiende quien juega. Se mira de dos maneras:
    por la lista de programas en marcha, y probando si Windows deja abrir para escribir cada programa de la carpeta.
    ``salvo`` son los programas que no cuentan: los servidores a los que se les puede pedir que se cierren solos."""
    programa = programa or carpeta_programa()
    tareas = _tareas() if tareas is None else {t.lower() for t in tareas}
    salvo = {e.lower() for e in salvo}
    abiertos = [nombre for exe, nombre in OTROS_PROGRAMAS.items() if exe.lower() in tareas and exe.lower() not in salvo]
    propio = os.path.normcase(os.path.abspath(sys.executable))
    try:
        ejecutables = [n for n in os.listdir(programa) if n.lower().endswith(".exe")]
    except OSError:
        ejecutables = []
    for n in ejecutables:
        ruta = os.path.join(programa, n)
        nombre = OTROS_PROGRAMAS.get(n, tr('el programa {n}').format(n=(n)))
        if os.path.normcase(os.path.abspath(ruta)) == propio or nombre in abiertos or n.lower() in salvo:
            continue
        try:
            with open(ruta, "r+b"):                           # un programa en marcha no se deja abrir para escribir
                pass
        except PermissionError:
            abiertos.append(nombre)
        except OSError:
            pass
    return abiertos


def tamano(ruta, excluir=()):
    """Bytes que ocupa una carpeta, sin contar las subcarpetas llamadas como diga `excluir`."""
    total = 0
    for base, dirs, archivos in os.walk(ruta):
        dirs[:] = [d for d in dirs if d not in excluir]
        for n in archivos:
            try:
                total += os.path.getsize(os.path.join(base, n))
            except OSError:
                pass
    return total


def _tamano_archivos(carpeta, nombres=None):
    """Bytes de los archivos sueltos de una carpeta, sin entrar en las de dentro: todos, o solo los que se nombran."""
    total = 0
    try:
        for n in (os.listdir(carpeta) if nombres is None else nombres):
            ruta = os.path.join(carpeta, n)
            if os.path.isfile(ruta):
                total += os.path.getsize(ruta)
    except OSError:
        pass
    return total


def tamano_copia(programa, nueva=None):
    """Lo que ocupará la copia de seguridad que hace el instalador: el programa sin data, más los datos, los mods y los
    manuales. Con la versión nueva ya extraída se cuenta justo lo que se va a guardar (plan_copia); antes de descargarla,
    el programa entero, y de la carpeta servidor solo sus archivos sueltos: los datos de un servidor nunca van en la copia."""
    de_data = sum(tamano(os.path.join(programa, "data", s)) for s in ("datos", "mods", "docs"))
    if nueva is None:
        return tamano(programa, excluir=("data", CARPETA_SERVIDOR)) + _tamano_archivos(os.path.join(programa, CARPETA_SERVIDOR)) + de_data
    return de_data + sum(tamano(os.path.join(programa, sub)) if archivos is None else _tamano_archivos(os.path.join(programa, sub), archivos)
                         for sub, archivos in plan_copia(nueva))


def espacio_para_instalar(nueva, programa=None):
    """Los bytes libres que hacen falta para instalar una versión ya extraída: la copia de seguridad de la anterior, lo que
    crece el juego al ponerle la nueva (archivo a archivo) y un margen para el archivo más grande mientras se escribe."""
    programa = programa or carpeta_programa()
    crece, mayor = 0, 0
    raiz = os.path.abspath(nueva)
    for base, dirs, archivos in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in INTOCABLES]
        for n in archivos:
            origen = os.path.join(base, n)
            try:
                nuevo = os.path.getsize(origen)
            except OSError:
                continue
            try:
                viejo = os.path.getsize(os.path.join(programa, os.path.relpath(origen, raiz)))
            except OSError:
                viejo = 0
            crece += max(0, nuevo - viejo)
            mayor = max(mayor, nuevo)
    return tamano_copia(programa, nueva) + crece + mayor + MARGEN_DISCO


def espacio_para_descargar(info, programa=None):
    """Los bytes libres que hacen falta antes de empezar: el ZIP, la versión nueva extraída (que ocupará más o menos lo que
    ocupa hoy el programa, y nunca menos que el ZIP) y, cuando el ZIP ya se ha borrado, la copia de seguridad."""
    programa = programa or carpeta_programa()
    instalado = tamano(programa, excluir=INTOCABLES)
    extraida = max(instalado, int(info.tamano * 1.15))
    return extraida + max(info.tamano, tamano_copia(programa) + extraida // 10) + MARGEN_DISCO


def espacio_libre(ruta):
    try:
        return shutil.disk_usage(ruta).free
    except OSError:
        return None


def megas_txt(n):
    """«850 megas» o «1,6 gigas»."""
    m = n / 1024 ** 2
    return tr('{v:.1f} gigas').format(v=(m / 1024)).replace(".", ",") if m >= 1000 else tr('{max} megas').format(max=(max(1, int(round(m)))))


def _falta_sitio(hace_falta, programa, libre=None):
    libre = espacio_libre(programa) if libre is None else libre
    if libre is None or libre >= hace_falta:
        return ""
    disco = os.path.splitdrive(os.path.abspath(programa))[0].rstrip(":").upper()
    return (tr('No hay sitio suficiente en el disco{v}: hacen falta {megas_txt} libres y hay {megas_txt2}. Libera al menos {megas_txt3} y vuelve a intentarlo.').format(v=(' ' + disco if disco else ''), megas_txt=(megas_txt(hace_falta)), megas_txt2=(megas_txt(libre)), megas_txt3=(megas_txt(hace_falta - libre))))


SIN_PERMISO = (tr("Windows no deja escribir en la carpeta del juego. Suele pasar si está en una carpeta protegida, como Archivos de programa, "
               "o si un antivirus o el acceso controlado a carpetas lo impiden. Mueve el juego a otra carpeta, por ejemplo dentro de Documentos, "
               "o añade una excepción en el antivirus."))


def copias_del_juego(tareas=None):
    """Cuántas veces está abierto el juego ahora mismo, contando esta. Uno si no se puede saber."""
    if tareas is None:
        try:
            sin_ventana = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            salida = subprocess.run([de_windows("tasklist.exe"), "/fo", "csv", "/nh"], capture_output=True, timeout=10, creationflags=sin_ventana).stdout.decode("utf-8", "replace").lower()
        except (OSError, subprocess.SubprocessError):
            return 1
        tareas = [linea.split('","')[0].strip('"') for linea in salida.splitlines() if linea.startswith('"')]
    return max(1, sum(1 for t in tareas if str(t).lower() == EJECUTABLE.lower()))


def problema_para_descargar(info, programa=None, libre=None, escribible=None):
    """Antes de descargar: si no se va a poder escribir o no va a caber, se dice ya. Cadena vacía si todo está bien."""
    programa = programa or carpeta_programa()
    if not (carpeta_escribible(programa) if escribible is None else escribible):
        return SIN_PERMISO + " " + A_MANO
    return _falta_sitio(espacio_para_descargar(info, programa), programa, libre)


def problemas_para_instalar(nueva, programa=None, libre=None, tareas=None, servidores=None, copias=None):
    """Antes de cerrar el juego para actualizar: lo que haría fallar la instalación, dicho con claridad. Lista vacía si todo está bien.
    Un servidor en línea abierto ya no es un problema si ha dejado su ficha: se le pide que se cierre solo y se vuelve a
    arrancar al terminar (``servidores`` son esas fichas; si no se dan, se buscan)."""
    programa = programa or carpeta_programa()
    servidores = servidores_en_marcha(programa) if servidores is None else servidores
    controlados = {os.path.basename(f["exe"]) for f in servidores}
    problemas = []
    if (copias_del_juego() if copias is None else copias) > 1:
        problemas.append(tr("El juego está abierto dos veces. Windows no deja sustituir un programa en marcha: cierra la otra ventana de Puerto Bravo antes de actualizar."))
    if not carpeta_escribible(programa):
        problemas.append(SIN_PERMISO)
    else:
        abiertos = programas_abiertos(programa, tareas, salvo=controlados)
        if abiertos:
            lista = abiertos[0] if len(abiertos) == 1 else ", ".join(abiertos[:-1]) + tr(" y ") + abiertos[-1]
            problemas.append(tr('Está abierto {lista}. Windows no deja sustituir un programa en marcha: ciérralo antes de actualizar.').format(lista=(lista))
                             if len(abiertos) == 1 else tr('Están abiertos {lista}. Windows no deja sustituir un programa en marcha: ciérralos antes de actualizar.').format(lista=(lista)))
    falta = _falta_sitio(espacio_para_instalar(nueva, programa), programa, libre)
    if falta:
        problemas.append(falta)
    mal = datos_en_zona_de_programa(servidores, nueva, programa)
    if mal:
        problemas.append(tr('La carpeta de datos del servidor en línea está dentro de la carpeta {mal}, que es del programa y la actualización sustituye: podría borrar lo que hay guardado. Cierra el servidor, mueve su carpeta de datos a otro sitio, por ejemplo dentro de la carpeta servidor, cambia la carpeta de datos en la configuración del servidor y vuelve a arrancarlo.').format(mal=(mal)))
    return problemas


def datos_en_zona_de_programa(fichas, nueva, programa=None):
    """Si algún servidor abierto tiene su carpeta de datos dentro de una carpeta que la versión nueva trae (lib, data\\datos,
    servidor\\otros_sistemas...), devuelve esa carpeta, como se la diría a quien juega; si no, cadena vacía. Lo normal es que
    los datos estén en servidor\\datos_servidor o donde su dueño haya querido, y ahí la actualización ni copia ni borra."""
    programa = os.path.normcase(os.path.abspath(programa or carpeta_programa()))
    for f in fichas or ():
        datos = os.path.normcase(os.path.abspath(f["datos"])) if f.get("datos") else ""
        if not datos.startswith(programa + os.sep):
            continue
        partes = os.path.relpath(datos, programa).split(os.sep)
        for k in range(1, len(partes) + 1):
            sub = os.path.join(*partes[:k])
            if sub not in ("data", CARPETA_SERVIDOR) and partes[k - 1] not in INTOCABLES + VIVO_SERVIDOR and os.path.isdir(os.path.join(nueva, sub)):
                return sub
    return ""


# ------------------------------------- los servidores en línea abiertos: pararlos y volver a arrancarlos
TIPO_DE = {"PuertoBravoServidor.exe": "consola", "PuertoBravoServidorPanel.exe": "panel"}
NOMBRE_TIPO = {"consola": tr("el servidor en línea"), "panel": tr("el panel del servidor en línea")}


def carpeta_fichas(programa=None):
    """Donde cada servidor en marcha deja su ficha: servidor\\en_marcha, dentro de la carpeta del juego."""
    return os.path.join(programa or carpeta_programa(), "servidor", "en_marcha")


def _mi_sesion():
    """La sesión de Windows de este proceso. None si no se puede saber."""
    try:
        import ctypes
        n = ctypes.c_ulong(0)
        if ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(n)):
            return int(n.value)
    except Exception:
        pass
    return None


def proceso_vivo(pid, exe=""):
    """¿Sigue en marcha ese proceso, y es ese programa? Se pregunta a Windows por su número."""
    try:
        sin_ventana = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        salida = subprocess.run([de_windows("tasklist.exe"), "/fi", 'PID eq {int}'.format(int=(int(pid))), "/fo", "csv", "/nh"], capture_output=True, timeout=10,
                                creationflags=sin_ventana).stdout.decode("utf-8", "replace").lower()
    except (OSError, subprocess.SubprocessError, ValueError):
        return False
    for linea in salida.splitlines():
        campos = [c.strip('"') for c in linea.split('","')]
        if len(campos) > 1 and campos[1].strip('"') == str(int(pid)):
            return not exe or campos[0] == os.path.basename(exe).lower()
    return False


def servidores_en_marcha(programa=None, vivo=None, sesion=None):
    """Los servidores en línea de esta carpeta del juego que están abiertos ahora, según las fichas que dejan al arrancar:
    [{"pid", "tipo", "exe", "args", "cwd", "datos", "conf", "activo", "servicio"}]. Las fichas de procesos que ya no
    existen se borran. Solo valen los programas del servidor que están en la propia carpeta del juego."""
    programa = programa or carpeta_programa()
    vivo = vivo or proceso_vivo
    sesion = _mi_sesion() if sesion is None else sesion
    carpeta = carpeta_fichas(programa)
    fichas = []
    try:
        nombres = sorted(os.listdir(carpeta))
    except OSError:
        return fichas
    for n in nombres:
        if not n.endswith(".json"):
            continue
        ruta = os.path.join(carpeta, n)
        try:
            with open(ruta, encoding="utf-8") as f:
                d = json.load(f)
            pid, exe = int(d["pid"]), str(d["exe"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        tipo = TIPO_DE.get(os.path.basename(exe))
        if tipo is None or os.path.normcase(os.path.abspath(os.path.dirname(exe))) != os.path.normcase(os.path.abspath(programa)):
            continue                                     # no es un programa del servidor de esta carpeta: no se toca
        if not vivo(pid, exe):
            _quitar(ruta)                                # se cerró sin borrar su ficha
            continue
        suya = d.get("sesion")
        fichas.append({"pid": pid, "tipo": tipo, "exe": exe, "args": [str(a) for a in d.get("args") or [] if isinstance(a, str)][:20],
                       "cwd": str(d.get("cwd") or ""), "datos": str(d.get("datos") or ""), "conf": str(d.get("conf") or ""),
                       "activo": bool(d.get("activo", True)),
                       # Arrancado por un servicio o una tarea de Windows (otra sesión): quien lo arrancó lo volverá a arrancar,
                       # o no; desde aquí no se puede repetir igual.
                       "servicio": isinstance(suya, int) and (suya == 0 or (sesion is not None and suya != sesion))})
    return fichas


def texto_servidores(fichas):
    """Qué hay abierto, dicho para quien juega: «el servidor en línea», «el panel del servidor en línea, con el servidor parado»."""
    partes = []
    for f in fichas:
        t = NOMBRE_TIPO[f["tipo"]]
        if f["tipo"] == "panel" and not f["activo"]:
            t += tr(", con el servidor parado")
        if t not in partes:
            partes.append(t)
    return partes[0] if len(partes) == 1 else ", ".join(partes[:-1]) + tr(" y ") + partes[-1] if partes else ""


def sin_servidor_en_marcha(fichas):
    """¿Lo único abierto son paneles con el servidor parado? Entonces no hay jugadores a los que avisar ni servidor que parar:
    solo hay que cerrar el panel y volver a abrirlo."""
    return bool(fichas) and all(f["tipo"] == "panel" and not f.get("activo", True) for f in fichas)


def pedir_parada_servidores(fichas, trabajo=None):
    """Apunta qué servidores había abiertos (para volver a arrancarlos igual) y les deja en su carpeta de datos la orden de
    pararse para actualizar: avisan a los jugadores, esperan sus guardados, lo guardan todo y se cierran solos.
    Devuelve la ruta de la nota. Si a alguno no se le puede dejar la orden, no se le deja a ninguno."""
    trabajo = trabajo or carpeta_trabajo()
    os.makedirs(trabajo, exist_ok=True)
    for f in fichas:
        if f.get("datos") and f["tipo"] == "panel" and not os.path.isdir(f["datos"]):
            # Un panel que no ha arrancado nunca su servidor todavía no tiene carpeta de datos, y es ahí donde mira la orden
            # de cerrarse: se le crea, vacía. Es la que crearía él mismo al arrancar el servidor por primera vez.
            try:
                os.makedirs(f["datos"], exist_ok=True)
            except OSError:
                pass
        if not f.get("datos") or not os.path.isdir(f["datos"]):
            que = NOMBRE_TIPO[f["tipo"]]
            raise ErrorActualizacion(tr("No encuentro la carpeta de datos ") + ((": " + que) if _pl() else ("del" + que[2:] if que.startswith(tr("el ")) else tr("de ") + que))
                                     + tr(" para pedirle que se cierre. Ciérralo tú y vuelve a intentarlo."))
    nota = os.path.join(trabajo, NOTA_SERVIDORES)
    with open(nota, "w", encoding="utf-8") as fo:
        json.dump({"version": 1, "momento": int(time.time()), "servidores": fichas}, fo, ensure_ascii=False, indent=1)
    hechas = []
    try:
        for carpeta in sorted({f["datos"] for f in fichas}):
            ruta = os.path.join(carpeta, ORDEN_SERVIDOR)
            with open(ruta, "w", encoding="utf-8") as fo:
                fo.write("actualizar\n")
            hechas.append(ruta)
    except OSError as e:
        for ruta in hechas:
            _quitar(ruta)
        _quitar(nota)
        raise ErrorActualizacion(tr("No se pudo dejar al servidor en línea la orden de cerrarse. Ciérralo tú y vuelve a intentarlo.")) from e
    return nota


def orden_de_arranque(ficha):
    """Con qué se vuelve a arrancar: el mismo programa, con los mismos argumentos y en la misma carpeta. El panel, además,
    con --arrancar si su servidor estaba en marcha, para que vuelva a funcionar solo."""
    args = [a for a in ficha.get("args") or [] if a != "--arrancar"]
    if ficha["tipo"] == "panel" and ficha.get("activo"):
        args.append("--arrancar")
    cwd = ficha.get("cwd") if ficha.get("cwd") and os.path.isdir(ficha["cwd"]) else os.path.dirname(ficha["exe"])
    return [ficha["exe"]] + args, cwd


def _lanzar_servidor(orden, cwd, tipo):
    """Arranca el programa minimizado y sin quitarle el foco al juego, que se abre a continuación. El de consola, en su propia consola."""
    banderas = getattr(subprocess, "CREATE_NEW_CONSOLE", 0) if tipo == "consola" else 0
    info = None
    if hasattr(subprocess, "STARTUPINFO"):
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 7                                      # SW_SHOWMINNOACTIVE
    subprocess.Popen(orden, cwd=cwd, creationflags=banderas, close_fds=True, startupinfo=info)


def relanzar_servidores(nota, programa=None, lanzar=None, vivo=None, registro=None):
    """Vuelve a arrancar los servidores que había abiertos antes de actualizar, según la nota. Lo llama el instalador al
    terminar, haya ido bien o mal. Apunta en el registro del instalador lo que hace con cada uno, sin rutas, y borra la
    nota. Devuelve [(tipo, relanzado, motivo)]. Solo arranca los programas del servidor de la propia carpeta del juego."""
    programa = programa or carpeta_programa()
    lanzar = lanzar or _lanzar_servidor
    vivo = vivo or proceso_vivo
    registro = registro or ruta_registro_instalador(programa)
    hecho = []
    try:
        with open(nota, encoding="utf-8") as f:
            fichas = json.load(f).get("servidores") or []
    except (OSError, ValueError, AttributeError):
        fichas = []
    for f in fichas:
        try:
            exe, tipo = str(f["exe"]), TIPO_DE.get(os.path.basename(str(f["exe"])))
            en_casa = os.path.normcase(os.path.abspath(os.path.dirname(exe))) == os.path.normcase(os.path.abspath(programa))
        except (KeyError, TypeError):
            continue
        if tipo is None or not en_casa:
            hecho.append((tipo or "desconocido", False, "ajeno"))
        elif f.get("servicio"):
            hecho.append((tipo, False, "servicio"))          # lo arrancó un servicio o una tarea: le toca a quien lo montó
        elif vivo(int(f.get("pid") or 0), exe):
            hecho.append((tipo, False, "sigue_abierto"))     # no llegó a cerrarse: no se arranca dos veces
        elif not os.path.isfile(exe):
            hecho.append((tipo, False, "no_esta"))
        else:
            try:
                orden, cwd = orden_de_arranque(dict(f, tipo=tipo))
                lanzar(orden, cwd, tipo)
                hecho.append((tipo, True, "" if tipo != "panel" or f.get("activo", True) else "parado"))      # el panel vuelve como estaba
            except (OSError, ValueError) as e:
                hecho.append((tipo, False, "error_" + type(e).__name__))
    try:
        if hecho:
            os.makedirs(os.path.dirname(registro), exist_ok=True)
            with open(registro, "a", encoding="utf-8", newline="\r\n") as f:
                for tipo, bien, motivo in hecho:
                    f.write(f'SERVIDOR {"relanzado" if bien else "sin_relanzar"} tipo={tipo}' + (f" {'estado' if bien else 'motivo'}={motivo}" if motivo else "") + "\n")
    except OSError:
        pass
    _quitar(nota)
    return hecho


MOTIVO_SIN_RELANZAR = {
    "servicio": tr("lo había arrancado un servicio o una tarea programada de Windows, y desde aquí no se puede arrancar igual: si no ha vuelto solo, arráncalo como lo tengas montado"),
    "sigue_abierto": tr("no llegó a cerrarse y sigue en marcha"),
    "no_esta": tr("no se encuentra su programa"),
    "ajeno": tr("no era un programa del servidor de esta carpeta"),
}


def texto_relanzados(r):
    """Lo que pasó con los servidores tras actualizar, a partir del registro del instalador, dicho para quien juega. Vacío si no había ninguno."""
    partes = []
    if r.get("relanzados") and r.get("parados", 0) >= len(r["relanzados"]):
        # Solo había paneles con el servidor parado: no hay jugadores esperando ni servidor que haya arrancado.
        partes.append(tr("El panel del servidor en línea que tenías abierto ha vuelto a abrirse, con el servidor parado, como estaba."))
    elif r.get("relanzados"):
        tipos = sorted(set(r["relanzados"]))
        que = tr(" y ").join(NOMBRE_TIPO.get(t, tr("el servidor")) for t in tipos)
        partes.append(tr('{upper}{v} que tenías {v2} a arrancar solo: los jugadores que estaban esperando volverán a entrar.').format(upper=(que[0].upper()), v=(que[1:]), v2=(tr('abierto ha vuelto') if len(tipos) == 1 else tr('abiertos han vuelto'))))
    for tipo, motivo in r.get("sin_relanzar") or []:
        que = NOMBRE_TIPO.get(tipo, tr("el servidor en línea"))
        partes.append(tr('{upper}{v} no se ha vuelto a arrancar: ').format(upper=(que[0].upper()), v=(que[1:])) + MOTIVO_SIN_RELANZAR.get(motivo, tr("no se pudo abrir su programa: ábrelo tú")) + ".")
    return " ".join(partes)


def lanzar_instalador(ruta_bat):
    """Arranca el instalador en su propia consola, pero escondida: no se ve ninguna ventana mientras se actualiza."""
    banderas = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    info = None
    if hasattr(subprocess, "STARTUPINFO"):
        info = subprocess.STARTUPINFO()
        info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        info.wShowWindow = 0                                      # SW_HIDE
        try:                                                      # el juego que se abra al final podrá ponerse delante
            import ctypes
            ctypes.windll.user32.AllowSetForegroundWindow(-1)     # ASFW_ANY
        except Exception:
            pass
    subprocess.Popen([de_windows("cmd.exe"), "/c", ruta_bat], cwd=os.path.dirname(ruta_bat), creationflags=banderas, close_fds=True, startupinfo=info)


def limpiar():
    """Borra los restos de una actualización ya instalada o abandonada."""
    shutil.rmtree(carpeta_trabajo(), ignore_errors=True)


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False
