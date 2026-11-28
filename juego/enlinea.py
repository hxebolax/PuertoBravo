"""Jugar en un servidor: el mismo juego de siempre, con jugadores de verdad alrededor.

Tu juego sigue llevando lo tuyo (tus misiones y tus trabajos), y el servidor lleva lo que es de todos: quién eres, tu
personaje guardado, los demás jugadores, los vehículos que dejáis en la calle, los disparos entre vosotros, las bandas,
los barrios, la hora y el tiempo, el tráfico, la gente de la calle y la policía.

Lo que decide el servidor no lo decide tu juego: si un disparo tuyo llega a otro jugador, de quién es un coche
aparcado, cuánto hay en la caja de la banda.
"""
from .i18n import tr, tr_servidor
import binascii
import hashlib
import json
import math
import os
import queue
import random
import socket
import sys
import threading
import time

from . import ed25519, red, registro, rutas
from . import mundo as M
from .entidades import Persona
from .online import Remoto

VERSION_RED = 2                   # la versión del protocolo que habla este juego
PROTOCOLO_MIN = 2                 # la más antigua con la que todavía se entiende
PUERTO = 47820
MAX_LINEA = 700 * 1024
# Lo nuevo que este juego entiende, dicho al saludar: un servidor anterior no lo mira, y uno nuevo le habla a cada juego
# según lo que sabe. Lo que sabe hacer el servidor viene de vuelta en «funciones».
SABE = ("rol", "radio", "pasajeros", "mis_vehiculos", "topes", "encargos",
        # sabe esperar a un servidor que se reinicia y volver a entrar solo: el servidor le avisa con cifras, no con un texto
        "reconexion")
CANALES_ROL = {"ic": (tr("en personaje"), "chat_personaje"), "ooc": (tr("fuera de personaje"), "chat_fuera"), "yo": (tr("acción"), "chat_accion")}
ORDENES_ROL = {"yo": "yo", "me": "yo", "ep": "ic", "ic": "ic", "fp": "ooc", "ooc": "ooc"}
MAX_FICHA = 200
RADIO_AJENA_M = 34.0              # a cuántos metros se deja de oír la radio del vehículo de otro jugador
SON_RADIO_AJENA = "radio_ajena"   # no es un sonido de los packs: es un trozo de la emisora, que se carga cuando hace falta


# ------------------------------------------------------------------ identidad
def varias_instancias():
    """Solo en las copias de pruebas: permite abrir el juego varias veces, cada una con su identidad."""
    return os.path.exists(rutas.data("config", "varias_instancias.txt"))


def perfil():
    """El perfil con el que se ha abierto esta copia (--perfil=2). Fuera de las copias de pruebas no se hace caso."""
    if not varias_instancias():
        return ""
    for a in sys.argv[1:]:
        if a.startswith("--perfil="):
            return "".join(c for c in a[9:] if c.isalnum())[:12]
    return ""


def _archivo_identidad():
    p = perfil()
    return rutas.archivo_config("identidad" + ("_" + p if p else ""))


def identidad(crear=True):
    """La llave de este juego: 32 bytes que no salen nunca de tu ordenador. Con ella te reconoce cada servidor."""
    from . import cifrado
    ruta = _archivo_identidad()
    try:
        s = binascii.unhexlify(cifrado.leer_json(ruta)["semilla"])
        if len(s) == 32:
            return s
    except (OSError, ValueError, KeyError, TypeError):
        pass
    if not crear:
        return None
    s = os.urandom(32)
    cifrado.escribir_json(ruta, {"semilla": binascii.hexlify(s).decode("ascii"), "aviso": tr("Esta es tu identidad en los servidores. No la compartas.")})
    return s


def exportar_identidad():
    return tr("PB1-") + binascii.hexlify(identidad()).decode("ascii")


def importar_identidad(texto):
    from . import cifrado
    t = "".join((texto or "").split())
    if t.upper().startswith("PB1-"):
        t = t[4:]
    try:
        s = binascii.unhexlify(t)
    except (ValueError, binascii.Error):
        return False
    if len(s) != 32:
        return False
    cifrado.escribir_json(_archivo_identidad(), {"semilla": binascii.hexlify(s).decode("ascii"), "aviso": tr("Esta es tu identidad en los servidores. No la compartas.")})
    return True


def huella_datos(datos):
    """Una huella de lo que tiene que ser igual en todos: localidades, lugares, barrios, armas, vehículos y misiones.
    Solo entra lo que no cambia mientras se juega: identificadores y las cifras de las armas."""
    partes = [["formato", 2]]                    # cambia cuando el juego le cuenta al servidor más cosas del mismo mundo
    for m in sorted(datos.get("mapas", []), key=lambda m: str(m.get("id"))):
        if m.get("tipo") == "recinto":           # el pabellón de los combates: solo para jugar sin conexión, y la huella no cambia
            continue
        partes.append(["mapa", m.get("id"), sorted(str(l.get("id")) for l in m.get("lugares", [])), sorted(str(b.get("id")) for b in m.get("barrios", []))])
    for a in sorted(datos.get("armas", []), key=lambda a: str(a.get("id"))):
        partes.append(["arma", a.get("id"), a.get("dano"), a.get("alcance"), a.get("cadencia"), a.get("precision")])
    partes.append(["vehiculos", sorted(str(v.get("id")) for v in datos.get("vehiculos", []))])
    partes.append(["misiones", sorted(str(m.get("id")) for m in datos.get("misiones", []) if not callable(m.get("al_completar")) and not m.get("generada") and not m.get("honrada"))])
    return hashlib.sha256(json.dumps(partes, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def mundo_servidor():
    """Lo que un servidor necesita saber del mundo de esta versión del juego, sin tener el juego: los lugares de cada
    localidad con sus coordenadas, los barrios, las cifras de las armas, los modelos y lo que paga cada misión.

    El servidor no trae esto de fábrica atado a una versión: se lo da el juego. Así un mismo servidor vale para las
    versiones que vayan saliendo, sin tener que actualizarlo."""
    from . import VERSION
    datos = M.cargar_datos(traducir=False)
    mapas = M.crear_mapas(datos)
    out = {"version": VERSION, "huella": huella_datos(datos), "mapas": {}, "armas": {}, "modelos": {}, "misiones": {}}
    for ident, m in mapas.items():
        if m.tipo == "recinto":
            continue
        c = next(x for x in datos["mapas"] if x.get("id") == ident)
        out["mapas"][ident] = {
            "nombre": m.nombre, "tipo": m.tipo, "ancho": round(float(m.ancho), 1), "alto": round(float(m.alto), 1),
            "lugares": [{"id": l.id, "tipo": l.tipo, "nombre": l.nombre, "x": round(float(l.x), 1), "y": round(float(l.y), 1), "adultos": bool(l.get("adultos")),
                         "precio": int(l.get("precio", 0) or 0), "ingresos": int(l.get("ingresos", 0) or 0)}
                        for l in m.lugares.values()],
            # para el tráfico común: cuántas calles hay a lo largo y a lo ancho, cuánto tráfico y qué coches
            "nx": int(getattr(m, "NX", 0)) if m.tipo != "mar" else 0, "ny": int(getattr(m, "NY", 0)) if m.tipo != "mar" else 0,
            "trafico": int(getattr(m, "trafico", 0)) if m.tipo != "mar" else 0,
            "peatones": int(getattr(m, "peatones", 0)) if m.tipo != "mar" else 0, "policia": int(bool(getattr(m, "policia", True))),
            "coches": sorted({v for b in c.get("barrios", []) for v in b.get("vehiculos", [])}),
            # para los agentes a pie: las manzanas por las que se puede andar (parques, plazas, descampados)
            "abiertos": sorted([int(k[0]), int(k[1])] for k, v in getattr(m, "bloques", {}).items() if v != "pared") if m.tipo != "mar" else [],
            "barrios": [{"id": b["id"], "nombre": b.get("nombre", b["id"])} for b in c.get("barrios", [])]}
    for a in datos["armas"]:
        out["armas"][a["id"]] = {"nombre": a["nombre"], "tipo": a.get("tipo", "cuerpo"), "dano": a.get("dano", 0), "alcance": a.get("alcance", 2),
                                 "cadencia": a.get("cadencia", 0.5), "precision": a.get("precision", 0.8), "radio": a.get("radio", 0), "automatica": bool(a.get("automatica"))}
    for v in datos["vehiculos"]:
        out["modelos"][v["id"]] = {"nombre": v["nombre"], "salud": v.get("salud", 100), "vel_max": v.get("vel_max", 25), "acel": v.get("acel", 6.0),
                                   "freno": v.get("freno", 12), "vuela": bool(v.get("vuela"))}
    for mi in datos["misiones"]:
        if mi.get("honrada"):                # el buen camino se juega sin conexión: pide contrato, estudios y negocio, que en un servidor no hay
            continue
        r = mi.get("recompensa") or {}
        out["misiones"][mi["id"]] = {"titulo": mi["titulo"], "dinero": int(r.get("dinero", 0) or 0), "repetible": bool(mi.get("repetible"))}
    # La gente que lleva el servidor y sus agentes salen también de los datos del juego. Un servidor anterior no mira
    # estas dos claves; uno nuevo, si no vienen (un juego anterior), usa lo que trae él.
    from . import gente
    nombres = gente.lista("nombres_servidor")
    if nombres:
        out["gente"] = {"nombres": list(nombres)}
    policia = gente.policia_para_servidor(out["armas"])
    if policia:
        out["policia"] = policia
    frases = {c: list(gente.lista("frases_servidor_" + c)) for c in ("paseante", "ratero", "pistolero", "ladron", "atracador") if gente.lista("frases_servidor_" + c)}
    if frases:
        out["gente"] = dict(out.get("gente") or {}, frases=frases)
    encargos = encargos_para_servidor(datos)
    if encargos:
        out["encargos"] = encargos
    empleos = empleos_para_servidor(datos)
    if empleos:
        out["empleos"] = empleos
    return out


def empleos_para_servidor(datos):
    """Los contratos fijos, para que un servidor pueda pagar sus nóminas con las cifras del juego y no con las que diga el
    juego de cada cual: cada cuántos días se cobra, la prima por una buena evaluación y, de cada empleo, los turnos que
    pide y lo que paga cada puesto. Un servidor anterior no lo mira; uno nuevo, si no viene, no paga nóminas."""
    from .honrado import AJ
    puestos = {}
    try:
        for c in datos.get("empleos_fijos") or []:
            lista = [[max(1, int(p.get("cupo", 3))), max(0, int(p.get("sueldo", 0)))] for p in c.get("puestos") or []]
            if lista and isinstance(c.get("id"), str):
                puestos[c["id"][:40]] = lista
        return {"periodo": AJ.entero("periodo_dias"), "prima": AJ.entero("prima_buena"), "puestos": puestos} if puestos else {}
    except (KeyError, TypeError, ValueError, AttributeError):
        return {}


def encargos_para_servidor(datos):
    """Lo más que puede pagar cada encargo repetible, según los datos del juego: con esto un servidor que lleva la cuenta
    del dinero sabe hasta dónde creerse la paga de un contrato, un combate, un atraco o un encargo de coche. Un servidor
    anterior no lo mira; uno nuevo, si no viene, usa unas cifras suyas."""
    from . import gente
    out = {}
    try:
        contratos = [int(c.get("paga", 600)) + 5 * int(c.get("paga_escolta", 380)) for c in datos.get("contratos") or []]
        out["contrato"] = max(contratos + [2500])
        for c in datos.get("combates") or []:                   # la bolsa sube con cada victoria: se cuenta hasta cuarenta
            out[str(c["id"])[:40]] = int(c.get("premio", 150)) + 40 * int(c.get("premio_victoria", 100))
        banco = gente.caja_local("banco")
        out["atraco_banco"] = max(13000, int(banco["maximo"]) if banco else 0)
        cajas = [int(v.get("maximo", 0) or 0) for k, v in gente.CAJAS.items() if k not in ("banco", "proveedor")]
        if cajas:
            out["atraco_local"] = max(cajas)
        proveedor = gente.caja_local("proveedor")
        if proveedor:
            out["asalto_proveedor"] = int(proveedor["maximo"])
        from .extras2 import MODELOS_ENCARGO
        valores = [int(v.get("valor", 0) or 0) for v in datos.get("vehiculos") or [] if v.get("id") in MODELOS_ENCARGO]
        if valores:
            out["encargo_coche"] = int(max(valores) * 1.5) + 350
    except (KeyError, TypeError, ValueError, AttributeError):
        pass
    return {k: int(v) for k, v in out.items() if isinstance(v, (int, float)) and v > 0}


def version_tupla(texto):
    """Una versión del juego, lista para compararla con otra: «1.7.0» va antes que «1.10.0»."""
    out = []
    for trozo in str(texto or "0").split("."):
        num = "".join(c for c in trozo if c.isdigit())
        out.append(int(num) if num else 0)
    return tuple(out)


def mundo_canonico(d):
    """El texto exacto que se firma y se envía: el mismo mundo da siempre el mismo texto."""
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def firma_del_mundo(huella):
    """La firma con la que quien publica el juego avala el mundo de esta versión. Vacía si no la hay o no es de estos datos."""
    try:
        with open(rutas.data("datos", "mundo.firma"), encoding="utf-8") as f:
            d = json.load(f)
        return str(d["firma"]) if d.get("huella") == huella else ""
    except (OSError, ValueError, KeyError):
        return ""


# -------------------------------------------------------------------- conexión
class Motivo(str):
    """Por qué no se ha podido entrar en un servidor: el texto que se le dice al jugador y, además, una palabra que el
    juego entiende sin leerlo. «red»: no contesta. «reiniciando», «lleno», «version»: lo dice el propio servidor.
    «certificado»: no presenta el de la otra vez. Vacío: cualquier otro rechazo."""
    codigo = ""
    minima = ""

    def __new__(cls, texto, codigo="", minima=""):
        m = super().__new__(cls, texto)
        m.codigo, m.minima = str(codigo or ""), str(minima or "")
        return m


class _Lineas:
    def __init__(self, sock):
        self.sock = sock
        self.buf = b""

    def leer(self):
        while b"\n" not in self.buf:
            if len(self.buf) > MAX_LINEA:
                raise ValueError(tr("mensaje demasiado largo"))
            trozo = self.sock.recv(65536)
            if not trozo:
                return None
            self.buf += trozo
        linea, self.buf = self.buf.split(b"\n", 1)
        try:
            m = json.loads(linea.decode("utf-8"))
        except ValueError:
            return {}
        return m if isinstance(m, dict) else {}


class ClienteServidor(red.Cliente):
    """La conexión con un servidor: cifrada si el servidor cifra, y con tu identidad demostrada con una firma."""

    def __init__(self):
        super().__init__()
        self.cifrado = False
        self.huella_cert = ""
        self.protocolo = VERSION_RED             # la versión del protocolo acordada con el servidor

    @staticmethod
    def _respuesta(lineas, esperados, tope=12):
        """El siguiente mensaje de los que se esperan en el saludo. Lo que no se conoce se deja pasar: un servidor de una
        versión posterior puede decir cosas que este juego no entiende, y eso no es motivo para no entrar."""
        for _ in range(tope):
            r = lineas.leer()
            if r is None:
                return None
            if r.get("t") in esperados:
                return r
        return None

    def _abrir(self, host, puerto, timeout, tls):
        s = socket.create_connection((host, puerto), timeout=timeout)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if not tls:
            return s, ""
        import ssl
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False               # el certificado es del propio servidor: lo que se comprueba es que no cambie
        ctx.verify_mode = ssl.CERT_NONE
        s.settimeout(4)
        try:
            ss = ctx.wrap_socket(s, server_hostname=None)
        except Exception:
            try:
                s.close()
            except OSError:
                pass
            raise
        ss.settimeout(timeout)
        return ss, hashlib.sha256(ss.getpeercert(True)).hexdigest()

    def conectar_servidor(self, host, puerto, nombre, semilla, huella, clave="", invitacion="", huella_cert="", timeout=10, mundo=None, firmado=False):
        """Devuelve (True, bienvenida) o (False, motivo). Si el certificado no es el de la otra vez, motivo empieza por «certificado»."""
        s = None
        aviso = ""
        enviado_mundo = False
        # Cifrado, y si el servidor no cifra, sin cifrar. Y todo ello dos veces: los filtros de red (AdGuard, antivirus con
        # protección web, cortafuegos) a veces se tragan la primera conexión de un programa que no conocen.
        for intento, tls in enumerate((True, False, True, False)):
            ultimo = intento == 3
            try:
                s, fp = self._abrir(host, puerto, timeout, tls)
            except (OSError, ValueError) as e:
                if isinstance(e, (socket.gaierror, ConnectionRefusedError)) or ultimo:
                    return False, Motivo(tr("No se pudo conectar con el servidor. Comprueba la dirección y que el servidor esté encendido. ") + red.AVISO_FILTROS, "red")
                continue                         # el servidor no cifra, o se ha cortado: se prueba de la otra forma
            except Exception:
                if ultimo:
                    return False, Motivo(tr("No se pudo conectar con el servidor."), "red")
                continue
            if tls and huella_cert and fp != huella_cert:
                s.close()
                return False, Motivo(tr("certificado: ") + fp, "certificado")
            self.cifrado, self.huella_cert = tls, fp
            try:
                s.settimeout(timeout if intento >= 2 else min(timeout, 5))
                lineas = _Lineas(s)
                pub = binascii.hexlify(ed25519.publica(semilla)).decode("ascii")
                from . import VERSION
                # v es la versión más nueva del protocolo que habla este juego y vmin la más antigua con la que se entiende:
                # el servidor elige la más nueva que hablen los dos. Así se puede jugar con un servidor más nuevo o más antiguo.
                red._enviar(s, self.lock, {"t": "hola", "v": VERSION_RED, "vmin": PROTOCOLO_MIN, "nombre": nombre, "pub": pub, "huella": huella, "juego": VERSION,
                                           "firmado": bool(firmado), "clave": red.huella(clave) if clave else "", "invitacion": invitacion, "sabe": list(SABE)})
                r = self._respuesta(lineas, ("reto", "rechazo", "ok"), tope=3)
                if not tls and huella_cert and r and r.get("t") in ("reto", "rechazo", "ok"):
                    s.close()
                    return False, Motivo(tr("Este servidor cifraba la conexión y ahora no lo hace. Por seguridad no entro. "
                                         "Si lo ha cambiado quien lo lleva, bórralo de tu lista y añádelo otra vez."), "certificado")
                if r and r.get("t") == "reto":
                    try:
                        minimo = int(r.get("vmin") or 0)
                    except (TypeError, ValueError):
                        minimo = 0
                    if minimo > VERSION_RED:                     # el servidor ya no habla con juegos como este
                        s.close()
                        return False, Motivo(tr("Este servidor necesita una versión más nueva del juego. Actualiza el juego para entrar."), "version")
                    s.settimeout(timeout)
                    f = ed25519.firmar(semilla, ("puertobravo-entrada|" + str(r.get("n", ""))).encode("ascii"))
                    red._enviar(s, self.lock, {"t": "firma", "f": binascii.hexlify(f).decode("ascii")})
                    r = self._respuesta(lineas, ("ok", "rechazo", "pide_mundo"))
                    if r and r.get("t") == "pide_mundo":         # el servidor no conoce el mundo de esta versión: se lo damos
                        texto, firma_m = mundo() if mundo is not None else ("", "")
                        import base64
                        import zlib
                        red._enviar(s, self.lock, {"t": "mundo", "z": base64.b64encode(zlib.compress(texto.encode("utf-8"), 9)).decode("ascii"), "firma": firma_m})
                        enviado_mundo = True
                        s.settimeout(max(timeout, 30))
                        r = self._respuesta(lineas, ("ok", "rechazo"))
            except (OSError, ValueError):
                r = None
            if not r or r.get("t") not in ("ok", "rechazo"):
                try:
                    s.close()
                except OSError:
                    pass
                if enviado_mundo:
                    return False, tr("El servidor no ha aceptado los datos de tu versión del juego, o ha cortado la conexión al recibirlos. Prueba otra vez dentro de un momento.")
                if not ultimo:
                    continue
                return False, Motivo(tr("Lo que hay en esa dirección no es un servidor de Puerto Bravo, o no contesta. ") + red.AVISO_FILTROS, "red")
            if r["t"] == "rechazo":
                s.close()
                # El servidor lo dice en español: el código se saca de su texto (un servidor anterior no lo manda) y se dice traducido.
                texto = str(r.get("motivo") or "") or tr("El servidor no te deja entrar.")
                codigo = r.get("codigo") if isinstance(r.get("codigo"), str) else ""
                if not codigo:
                    from .reconexion import codigo_de
                    codigo = codigo_de(texto)
                return False, Motivo(tr_servidor(texto), codigo, r.get("minima") if isinstance(r.get("minima"), str) else "")
            s.settimeout(None)
            self.sock, self.conectado, self.id, self.nombre = s, True, r.get("id"), r.get("nombre", nombre)
            self.host, self.puerto = host, puerto
            try:
                self.protocolo = max(PROTOCOLO_MIN, min(VERSION_RED, int(r.get("protocolo") or VERSION_RED)))
            except (TypeError, ValueError):
                self.protocolo = VERSION_RED
            threading.Thread(target=self._leer, args=(lineas,), daemon=True).start()
            return True, r
        return False, Motivo(aviso or tr("No se pudo conectar con el servidor."), "red")


class Enlace:
    """Una conexión ya aceptada por un servidor, a la espera de que empiece la partida."""

    def __init__(self, cli, ok, servidor):
        self.cli, self.ok, self.servidor = cli, ok, servidor


def conectar(app, servidor, clave="", invitacion=""):
    """Conecta con un servidor de la lista. Devuelve (Enlace, texto) o (None, motivo)."""
    d = red.analizar_direccion(servidor.get("dir", ""))
    if d is None:
        return None, tr("No entiendo esa dirección.")
    host, puerto = d
    if ":" not in servidor.get("dir", "").replace(red.PREFIJO, ""):
        puerto = PUERTO
    if not hasattr(app, "_huella_datos"):
        app._huella_datos = huella_datos(app.datos)
    nombre = (app.cfg["red_nombre"] or "").strip()[:24]          # sin nombre, el servidor no deja entrar por primera vez
    registro.ocultar(nombre)
    cli = ClienteServidor()
    semilla = getattr(app, "semilla_identidad", None)        # las pruebas automáticas traen la suya y no tocan la del jugador
    if semilla is None:
        semilla = hashlib.sha256(b"identidad de pruebas").digest() if app.pruebas else identidad()
    firma_m = firma_del_mundo(app._huella_datos)
    ok, r = cli.conectar_servidor(host, puerto, nombre, semilla, app._huella_datos, clave, invitacion, servidor.get("cert", ""),
                                  mundo=lambda: (mundo_canonico(mundo_servidor()), firma_m), firmado=bool(firma_m))
    registro.info("red", "Intenta entrar en un servidor", conseguido=ok, cifrado=cli.cifrado)
    if not ok:
        return None, r
    servidor["cert"] = cli.huella_cert
    servidor["nombre"] = str((r.get("servidor") or {}).get("nombre") or servidor.get("nombre") or tr("Servidor"))[:60]
    return Enlace(cli, r, servidor), ""


# =========================================================== dentro de la partida
class EnLinea:
    """Mixin de Partida: lo que cambia cuando la partida es de un servidor."""

    en_servidor = False
    sv_espera = None                 # mientras se espera a que vuelva el servidor: por qué se fue y lo que habrá que recomponer
    _sv_servidor = None              # el servidor de la lista en el que se está, para volver a entrar solo

    def sv_entrar(self, enlace, vuelta=False):
        """Entra en la partida de un servidor. Con ``vuelta``, es una reconexión tras un corte o un reinicio del servidor:
        la partida que hay en memoria sigue tal cual, y es ella la que se manda al servidor, no al revés. Devuelve
        entonces lo que hay que decirle al jugador."""
        ok = enlace.ok
        antes = self.sv if vuelta else {}
        espera = getattr(self, "sv_espera", None) or {}
        self.sv_espera = None
        self.red = enlace.cli
        self.en_servidor = True
        self._sv_servidor = enlace.servidor              # el de la lista: para volver a entrar solo si se corta
        self.sv = {"info": ok.get("servidor") or {}, "admin": bool(ok.get("admin")), "pasivo": False, "banda": ok.get("banda"), "rango": None,
                   "territorios": ok.get("territorios") or {"barrios": [], "guerras": []}, "grupo": None, "miembros": [], "vehs": {},
                   "recompensa": int(ok.get("recompensa") or 0), "agresor": None, "t_agresor": -999.0, "t_guardar": 20.0, "inv_banda": None,
                   "inv_grupo": None, "segura": False, "protegido": time.time() + float((ok.get("servidor") or {}).get("proteccion", 0)),
                   "ecos": {}, "mision_grupo": None, "quien": [], "bandas": [], "nombre_servidor": enlace.servidor.get("nombre", "Servidor"),
                   "t_atropello": 0.0, "t_dicho": {}, "cifrado": enlace.cli.cifrado, "props": ok.get("props") or {}, "robo": None, "trafico": {}, "peatones": {},
                   "agentes": {}, "id": ok.get("id"), "t_desfase": None,
                   # con qué mundo trabaja el servidor y qué sabe hacer: puede ser de otra versión del juego que la tuya
                   "mundo": ok.get("mundo") if isinstance(ok.get("mundo"), dict) else {},
                   "funciones": [f for f in ok.get("funciones") or [] if isinstance(f, str)],
                   "protocolo": getattr(enlace.cli, "protocolo", VERSION_RED),
                   # lo de la 1.7.1; con un servidor anterior, todo esto se queda vacío y el juego lo dice cuando hace falta
                   "ficha": str(ok.get("ficha") or "")[:MAX_FICHA], "fichas": {}, "historial": [], "pasajeros": set(), "radio_ajena": None,
                   "economia": (ok.get("servidor") or {}).get("economia") if isinstance((ok.get("servidor") or {}).get("economia"), dict) else None,
                   "veh_pend": {}, "dinero_visto": None, "t_gasto": None, "t_guardado_real": None, "reenganche": None, "regrupo": None}
        for clave in ("historial", "radio_ajena_dicha"):                     # al volver, lo dicho por los canales de rol sigue ahí
            if clave in antes:
                self.sv[clave] = antes[clave]
        if self.sv["info"].get("policia") and self.cfg["sin_policia"]:      # aquí la policía es de todos: la asistencia no vale
            self._sv_sin_policia = True
            self.cfg.v["sin_policia"] = False
        if not vuelta:
            self.j.puntos_busqueda, self.j.estrellas = 0.0, 0                # si te buscaban al salir, el servidor te lo dirá
        if self.sv["banda"]:
            yo = next((m for m in self.sv["banda"]["miembros"] if m["cuenta"] == ok.get("cuenta")), None)
            self.sv["rango"] = yo["rango"] if yo else None
        self.sv["cuenta"] = ok.get("cuenta")
        self.remotos = {}
        for q in ok.get("jugadores", []):
            registro.ocultar(q["nombre"])
            r = Remoto(q["id"], tr(str(q["nombre"])) if q.get("ia") else q["nombre"])      # los personajes del servidor, en tu idioma
            r.banda, r.ia = q.get("banda"), bool(q.get("ia"))
            self.remotos[q["id"]] = r
        h = ok.get("hora") or {}
        self.reloj, self.dia, self.lluvia = float(h.get("reloj", self.reloj)), int(h.get("dia", self.dia)), bool(h.get("lluvia"))
        for mapa in self.mapas.values():                         # los semáforos, iguales para todos
            mapa.desfase_luces = float(h.get("luces", 0.0)) - self.t
        self.j.semilla = int(ok.get("semilla") or self.j.semilla or 1)       # la misma suerte para todos: precios, sucesos y lotería
        try:
            self.sortear_dia(anunciar=False)
        except Exception:
            pass
        self.cfg.temporales = {"sin_policia": True} if getattr(self, "_sv_sin_policia", False) else {}
        if not self.sv["info"].get("adultos", True) and self.cfg["adultos"]:
            self._sv_adultos = True
            self.cfg.temporales["adultos"] = True
            self.cfg.v["adultos"] = False            # solo mientras dura la sesión: no se guarda
            self.app.aplicar_adultos()
        elif vuelta and getattr(self, "_sv_adultos", False):
            self.cfg.temporales["adultos"] = True    # ya estaba quitado desde antes del corte: sigue sin guardarse
        for v in ok.get("vehiculos", []):
            self.sv["vehs"][v["id"]] = v
        # Los vehículos de la calle que el servidor reconoce como tuyos. Un servidor anterior no lo dice: entonces solo se
        # sabe de los que dejes en esta sesión.
        self.sv["mios"] = {i for i in (ok.get("mis_vehiculos") or []) if isinstance(i, int)}
        self.mis_al_servidor()
        if vuelta:
            self._sv_vehiculos_de_vuelta()
        self.sv_poner_vehiculos()
        if not vuelta:
            self.hon_sv_al_entrar(ok.get("contrato"))               # tu contrato fijo, como lo tiene apuntado el servidor
        self.sv_al_dia(int(ok.get("dias_fuera") or 0))
        for cosa in ok.get("pendientes", []):                    # lo que pasó con tus propiedades mientras no estabas
            if cosa.get("que") in ("venta", "caducada", "forzada", "tope"):
                l = self.lugares.get(cosa.get("lugar"))
                if l is not None and l.id in self.j.propiedades:
                    self.j.propiedades.remove(l.id)
                n = max(0, int(cosa.get("n", 0)))
                self.j.dinero += n
                nombre = l.nombre if l is not None else tr("una propiedad")
                self.decir({"venta": tr('{get} te ha comprado {nombre} por {n} euros.'),
                            "forzada": tr('{get} se ha quedado a la fuerza con {nombre} y te ha pagado {n} euros.'),
                            "tope": tr('{nombre} ha vuelto al mercado, porque pasabas del tope de negocios de este servidor. Te devuelven {n} euros.'),
                            "caducada": tr('Llevabas tanto sin entrar que {nombre} ha vuelto al mercado. Te quedan {n} euros de su valor.')}[cosa["que"]]
                           .format(get=(cosa.get('por', 'Alguien')), nombre=(nombre), n=(n)))
        if ok.get("saldo") is not None and not vuelta:           # el dinero lo lleva el servidor: manda lo que él tiene apuntado
            self._sv_ajustar_saldo(self.j.dinero + self.j.banco - int(ok["saldo"]), callar=True)
        # Al volver no se corta aquí: tu juego manda lo que tiene y el servidor lo juzga con sus reglas de siempre (lo que
        # te dio él, tu margen por hora), como cualquier dinero que aparece. Lo que no reconozca, lo retira y lo dice.
        self._sv_cuadrar_propiedades()
        self._sv_descontar_robos(int(ok.get("robos") or 0))
        for cosa in ok.get("pendientes", []):
            if cosa.get("que") == "coche":
                self.decir(tr('Mientras no estabas, {get} se llevó tu {get2} de donde lo dejaste.').format(get=(cosa.get('por', tr('alguien'))), get2=(cosa.get('nombre', tr('vehículo')))))
            if cosa.get("que") == "caido":
                n = min(self.j.dinero, int(cosa.get("pierde", 0)))
                self.j.dinero -= n
                self.decir(tr('Mientras te desconectabas en plena pelea, {get} te tumbó. Has perdido {n} euros.').format(get=(cosa.get('por', tr('alguien'))), n=(n)))
        info = self.sv["info"]
        quienes = ", ".join(x.nombre for x in self.remotos.values())
        self.son("amigo_entra", cat="interfaz")
        if vuelta:
            return self._sv_de_vuelta(espera, quienes)
        self.decir(tr('Estás en {nombre_servidor} como {nombre}. ').format(nombre_servidor=(self.sv['nombre_servidor']), nombre=(self.red.nombre)) + (tr_servidor(str(info.get("bienvenida", ""))) + " " if info.get("bienvenida") else "")
                   + (tr('Están: {quienes}. ').format(quienes=(quienes)) if quienes else tr("De momento no hay nadie más. "))
                   + (tr("La conexión va cifrada. ") if self.sv["cifrado"] else tr("Este servidor no cifra la conexión. "))
                   + (tr("Hay combate entre jugadores") + (tr(", con zonas seguras en hospitales, comisarías y casas. ") if info.get("seguras") else ". ") if info.get("pvp") else tr("Aquí no hay combate entre jugadores. "))
                   + self.sv_aviso_version()
                   + tr("Abre el móvil con M y entra en En línea para verlo todo."))
        self.sv_guardar()

    # ------------------------------------------------- cuando el servidor se va y vuelve
    def sv_guardado_txt(self):
        """Cómo está tu personaje en el servidor, dicho al dejar de esperarle."""
        e = getattr(self, "sv_espera", None) or {}
        if e.get("avisado"):
            return tr("Tu personaje quedó guardado en el servidor justo antes de que se cerrara.")
        seg = e.get("sin_guardar")
        if seg is None:
            return tr("Tu personaje está guardado en el servidor como estaba en su último guardado.")
        from .reconexion import tiempo_txt
        return tr('Tu personaje está guardado en el servidor como estaba {tiempo_txt} antes del corte: lo que hicieras después no se ha guardado.').format(tiempo_txt=(tiempo_txt(seg)))

    def sv_cortado(self, causa, motivo="", vuelve=0):
        """El servidor se ha ido: se cierra para actualizarse o reiniciarse («actualizacion», «reinicio»), se ha cerrado sin
        decir por qué («cierre», un servidor anterior) o la conexión se ha cortado («corte»). La partida no se deja: se
        queda como está, con el mundo parado, y se abre la pantalla de espera, que vuelve a entrar sola. True si se espera."""
        if not self.en_servidor or getattr(self, "sv_espera", None) is not None:
            return False
        if not self.cfg["reconectar"] or getattr(self, "_sv_servidor", None) is None:
            return False
        avisado = False
        if self.red is not None and self.red.conectado:          # aún hay línea: el servidor espera este último guardado
            avisado = self.sv_guardar(ya=True)
            time.sleep(0.15)
        guardado = self.sv.get("t_guardado_real")
        self.sv_espera = {"causa": causa, "avisado": bool(avisado), "sin_guardar": None if guardado is None or avisado else max(0.0, time.time() - guardado),
                          "grupo": None, "pasajero": None}
        if self.sv.get("grupo") is not None:                     # el grupo de misión: se intentará rehacer al volver, por los nombres
            yo = getattr(self.red, "id", None)
            miembros = [q for q in self.sv.get("miembros") or [] if isinstance(q, dict)]
            lider = next((str(q.get("nombre", "")) for q in miembros if q.get("id") == self.sv["grupo"]), "")
            self.sv_espera["grupo"] = {"lidero": self.sv["grupo"] == yo, "lider": lider,
                                       "otros": [str(q.get("nombre", "")) for q in miembros if q.get("id") != yo]}
        if self.pasajero is not None:                            # ibas en el vehículo de otro: te quedas a pie donde estabais
            r = self.remotos.get(self.pasajero)
            self.sv_espera["pasajero"] = r.nombre if r is not None else tr("otro jugador")
            self.pasajero = None
            self.j.x, self.j.y = self.mundo.punto_libre(self.j.x + 2, self.j.y + 2)
        self._sv_limpiar_mundo()
        for r in self.remotos.values():
            r.id = None              # un menú que se quedara abierto con este jugador elegido ya no puede mandar nada a nadie
        self.desconectar_online()
        registro.aviso("red", "El servidor se ha ido: se espera a que vuelva", causa=causa)
        from . import reconexion
        self.app.abrir(reconexion.Espera(self.app, self, causa, motivo, vuelve))
        return True

    def _sv_vehiculos_de_vuelta(self):
        """Al volver al servidor: de las copias de vehículos aparcados que había en tu calle, se quitan las que el
        servidor ya no tiene. El que conduces no se toca: se vuelve a enganchar aparte."""
        mio = self.j.veh
        for v in list(self.vehiculos):
            ident = getattr(v, "id_red", None)
            if ident is None or v is mio or v.muerto:
                continue
            d = self.sv["vehs"].get(ident)
            if d is None or d.get("por") is not None or d.get("m") != self.mundo.id:
                v.red_mio = v.red_dueno = False
                self.quitar_vehiculo(v)
        if mio is not None and not getattr(mio, "tag", None):
            # El vehículo en el que ibas. Para el servidor quedó aparcado al cerrarse: se le pide otra vez, por su número,
            # cuando ya sepa dónde estás. Si no lo tenía apuntado todavía, se da de alta como la primera vez.
            if getattr(mio, "id_red", None) is not None:
                self.sv["reenganche"] = {"id": mio.id_red, "pedido": False}
            else:
                mio.red_ref = None
                self.sv["reenganche"] = {"id": None, "pedido": False}

    def _sv_reenganche_paso(self):
        """Tras volver, y con tu posición ya enviada: pide al servidor el vehículo en el que ibas."""
        re = self.sv.get("reenganche")
        if not re:
            return
        if re["pedido"]:
            if time.time() - re.get("t", 0) > 8:                 # el servidor no ha dicho ni que sí ni que no: no se espera más
                self.sv["reenganche"] = None
            return
        re["pedido"], re["t"] = True, time.time()
        v = self.j.veh
        if v is None:
            self.sv["reenganche"] = None
        elif re["id"] is None:
            self.sv["reenganche"] = None
            v.id_red, v.red_mio = None, False
            self.sv_subido(v)
        else:
            self.red.enviar({"t": "veh_subir", "id": re["id"]})

    def _sv_reenganche_no(self, m):
        """El servidor no devuelve el vehículo en el que ibas. Si ya no lo tiene, o lo tiene apuntado lejos (se cayó sin
        guardar lo último), se da de alta otra vez; si se lo ha llevado otro mientras tanto, te quedas a pie."""
        self.sv["reenganche"] = None
        v = self.j.veh
        if v is None:
            return
        por = m.get("por")
        if not por:                                              # un servidor anterior solo lo dice con palabras
            texto = str(m.get("motivo") or "").lower()
            por = "ocupado" if "adelantado" in texto else ("lejos" if "lejos" in texto else "no_esta")
        if por == "ocupado":
            v.red_mio = v.red_dueno = False
            self.salir_vehiculo(forzado=True)
            v.red_dueno = False
            self.quitar_vehiculo(v)
            self.son("puerta_coche")
            self.decir(tr("Mientras el servidor volvía, otro jugador se ha llevado el vehículo en el que ibas: te quedas a pie."), True)
            return
        if por == "lejos":
            self.red.enviar({"t": "veh_fin", "id": v.id_red})    # el que el servidor tenía apuntado en otro sitio, fuera: es este
        v.id_red, v.red_mio, v.red_ref = None, False, None
        self.sv_subido(v)

    def _sv_de_vuelta(self, espera, quienes):
        """Lo que se hace y se dice nada más volver: mandar tu personaje tal como está, y contar lo que haya cambiado."""
        self.t_red = 1.0                                         # tu posición, ya: el servidor te pone donde estás
        self._aspecto_enviado = None                             # y cómo vas vestido, otra vez: el servidor no se acuerda
        self.sv["t_guardar"] = 0.4                               # y enseguida tu personaje, tal como está
        partes = [tr('Reconectado a {nombre_servidor}. Sigues donde estabas').format(nombre_servidor=(self.sv['nombre_servidor']))
                  + (tr(', al volante de tu {nombre}').format(nombre=(self.j.veh.nombre)) if self.j.veh is not None else "") + "."]
        if espera.get("pasajero"):
            partes.append(tr('Ibas de pasajero con {pasajero}: te has quedado a pie donde estabais.').format(pasajero=(espera['pasajero'])))
        g = espera.get("grupo")
        if g and g.get("otros"):
            self.sv["regrupo"] = dict(g, hasta=self.t + 180.0, invitados=set())
            partes.append(tr("Ibas en un grupo de misión: ") + (tr("lo rehago yo en cuanto vuelvan los demás.") if g["lidero"]
                          else tr('vuelves a él en cuanto {v} entre y lo rehaga.').format(v=(g['lider'] or tr('quien lo llevaba')))))
        if self.sv["info"].get("policia") and (self.j.estrellas or self.j.puntos_busqueda):
            partes.append(tr("Tu nivel de búsqueda es el que diga ahora la policía del servidor."))
        aviso = self.sv_aviso_version()
        if aviso:
            partes.append(aviso.strip())
        if quienes:
            partes.append(tr('Están: {quienes}.').format(quienes=(quienes)))
        registro.info("red", "De vuelta en el servidor con la partida que había en memoria")
        return " ".join(partes)

    def _sv_regrupo_paso(self):
        """Rehacer el grupo de misión tras volver: quien lo llevaba invita otra vez, por su nombre, a quienes iban con él
        según van entrando; los demás aceptan solos. Si en tres minutos no se ha podido, se dice quién falta."""
        g = self.sv.get("regrupo")
        if not g:
            return
        presentes = {q.get("nombre") for q in self.sv.get("miembros") or [] if isinstance(q, dict)} if self.sv.get("grupo") is not None else set()
        faltan = [n for n in g["otros"] if n not in presentes]
        if not faltan:
            self.sv["regrupo"] = None
            self.decir(tr("El grupo de misión está otra vez completo."))
            return
        if self.t >= g["hasta"]:
            self.sv["regrupo"] = None
            lista = faltan[0] if len(faltan) == 1 else ", ".join(faltan[:-1]) + tr(" y ") + faltan[-1]
            self.decir(tr('No se ha podido rehacer del todo el grupo de misión: {lista} no {v} vuelto al servidor a tiempo. Cuando entre, se le invita otra vez desde el móvil, En línea, Quién hay.').format(lista=(lista), v=(tr('ha') if len(faltan) == 1 else tr('han'))))
            return
        if g["lidero"]:
            for r in self.remotos.values():
                if r.nombre in faltan and r.nombre not in g["invitados"] and r.id is not None:
                    g["invitados"].add(r.nombre)
                    self.red.enviar({"t": "grupo_invitar", "a": r.id, "mision": self.mision["def"]["titulo"] if self.mision else ""})

    def sv_aviso_version(self):
        """Lo que hay que saber cuando el servidor trabaja con los datos de otra versión del juego que la tuya.
        Se juega igual, cada uno con lo que su versión conoce; aquí se dice qué se va a notar. Vacío si es la misma."""
        from . import VERSION
        m = self.sv.get("mundo") or {}
        if not m or m.get("igual", True) or not m.get("version"):
            return ""
        suya, mia = version_tupla(m.get("version")), version_tupla(VERSION)
        if suya > mia:
            if self.sv_sabe("equivalencias"):                    # el servidor le pone a tu juego lo más parecido de lo que conoce
                return (tr('Este servidor va con los datos de la versión {version} del juego y tú tienes la {VERSION}: puedes jugar con todos. Las armas y los vehículos que tu versión no tiene los oirás y los verás como lo más parecido de lo que conoces; los lugares nuevos no los verás hasta que actualices. ').format(version=(m['version']), VERSION=(VERSION)))
            return (tr('Este servidor va con los datos de la versión {version} del juego y tú tienes la {VERSION}: puedes jugar, pero no verás los lugares, vehículos y armas nuevos de otros jugadores hasta que actualices. ').format(version=(m['version']), VERSION=(VERSION)))
        if suya < mia:
            return (tr('Este servidor va con los datos de la versión {version} del juego, anterior a la tuya: puedes jugar, pero lo nuevo de tu versión no lo verán los demás, las armas nuevas cuentan contra otros jugadores como ir con las manos, y en las localidades nuevas no te verán a ti. ').format(version=(m['version'])))
        return tr("Los datos de tu juego no son exactamente los de este servidor: puedes jugar, pero lo que tengas distinto no lo verán los demás. ")

    def sv_distinto_txt(self):
        """Qué no coincide entre tu juego y el mundo del servidor, con nombres, como lo cuenta el propio servidor (desde la
        1.7.1). Vacío si no lo dice o si no hay diferencias de armas ni de vehículos."""
        d = (self.sv.get("mundo") or {}).get("distinto")
        if not isinstance(d, dict):
            return ""

        def lista(grupo, clave, uno, varios):
            nombres = [str(n) for n in ((d.get(grupo) or {}).get(clave) or []) if n][:40]
            if not nombres:
                return ""
            cabeza = uno if len(nombres) == 1 else f"{len(nombres)} {varios}"
            return f"{cabeza}: " + ", ".join(nombres[:6]) + (tr(' y {v} más').format(v=(len(nombres) - 6)) if len(nombres) > 6 else "")
        out = ""
        faltan = [t for t in (lista("faltan", "armas", tr("un arma"), "armas"), lista("faltan", "vehiculos", tr("un vehículo"), "vehículos")) if t]
        if faltan:
            out += tr(". El servidor tiene y tu juego no, ") + "; ".join(faltan) + tr(". Los oirás y los verás como lo más parecido de lo que tu juego conoce")
        sobran = [t for t in (lista("sobran", "armas", tr("un arma"), "armas"), lista("sobran", "vehiculos", tr("un vehículo"), "vehículos")) if t]
        if sobran:
            out += tr(". Tu juego tiene y el servidor no, ") + "; ".join(sobran) + tr(". Contra otros jugadores esas armas cuentan como ir con las manos, y esos vehículos los ven como un utilitario")
        return out

    def sv_al_dia(self, dias):
        """Has estado fuera: pasan las medianoches que te has perdido, con un tope de tres."""
        if dias <= 0:
            return
        n = min(3, dias)
        self.decir(tr('Has estado {dias} {v} del servidor sin entrar.').format(dias=(dias), v=(tr('día') if dias == 1 else tr('días'))) + (tr(" Cuentan tres.") if dias > 3 else ""))
        for _ in range(n):
            self._cobrar_negocios()
        self.pasar_perro(60.0 * 24 * n)

    def sv_salir(self, motivo=None, al_menu=False):
        if not self.en_servidor:
            return
        if self.red is not None and self.red.conectado:
            v = self.j.veh
            if v is not None and getattr(v, "red_mio", False):
                self.red.enviar({"t": "veh_dejar", "id": v.id_red, "x": round(v.x, 1), "y": round(v.y, 1), "r": round(v.rumbo), "salud": round(v.salud, 1)})
            self.sv_guardar(ya=True)
            time.sleep(0.15)
        self.en_servidor = False
        if getattr(self, "_sv_sin_policia", False):
            self._sv_sin_policia = False
            self.cfg.v["sin_policia"] = True
        if getattr(self, "_sv_adultos", False):
            self._sv_adultos = False
            self.cfg.v["adultos"] = True
            self.app.aplicar_adultos()
        self.cfg.temporales = {}
        self.sv_espera = None
        self._sv_limpiar_mundo()
        self.desconectar_online(motivo)
        if al_menu:
            texto = motivo or tr("Has salido del servidor.")
            self.app.volver_al_menu()
            self.app.decir(texto, True)

    def _sv_limpiar_mundo(self):
        """Quita de tu mundo lo que ponía el servidor: sus agentes, su tráfico, su gente, los ecos del grupo y la radio ajena."""
        for p in list(self.sv.get("agentes", {}).values()):
            if p in self.personas:
                self.personas.remove(p)
        self.sv["agentes"] = {}
        self._sv_parar_radio_ajena()
        for e in list(self.sv.get("ecos", {}).values()):
            if e in self.personas:
                self.personas.remove(e)
        for r in self.remotos.values():
            if getattr(r, "sirena", None) is not None:
                r.sirena.parar()
        for mapa in self.mapas.values():
            mapa.desfase_luces = 0.0
        for r in self.remotos.values():
            self._sv_quitar_policia(r)
        for v in list(self.sv.get("trafico", {}).values()):
            if v is not self.j.veh and not v.muerto:
                self.quitar_vehiculo(v)
        self.sv["trafico"] = {}
        for p in list(self.sv.get("peatones", {}).values()):
            if p in self.personas:
                self.personas.remove(p)
        self.sv["peatones"] = {}
        self.sv["ecos"] = {}

    def sv_guardar(self, ya=False):
        if self.en_servidor and self.red is not None and self.red.conectado:
            d = self.a_dict()
            d.pop("veh_fuera", None)                 # en un servidor, los vehículos de la calle los lleva el servidor
            d.pop("mis_vehiculos", None)
            self.red.enviar({"t": "guardar", "p": d, "ya": bool(ya)})
            self.sv["t_guardar"] = 45.0
            self.sv["t_gasto"] = None
            self.sv["dinero_visto"] = int(self.j.dinero + self.j.banco)
            self.sv["t_guardado_real"] = time.time()
            return True
        return False

    def sv_sabe(self, que):
        """¿Sabe hacer eso el servidor en el que estás? Uno anterior a la 1.7.1 no sabe de rol, ni de radios, ni de traerte vehículos."""
        return self.en_servidor and que in self.sv.get("funciones", ())

    def _sv_vigilar_gasto(self, dt):
        """Lo que compras se guarda en el servidor a los pocos segundos, sin esperar al guardado de cada tres cuartos de
        minuto: así, si se corta la conexión nada más comprar, lo comprado no se pierde."""
        sv = self.sv
        total = int(self.j.dinero + self.j.banco)
        visto = sv.get("dinero_visto")
        sv["dinero_visto"] = total
        if visto is not None and total < visto and sv.get("t_gasto") is None:
            # un momento, por si son varias compras seguidas; y si no paras de gastar (en el casino, por ejemplo), no más de
            # un guardado cada doce segundos: el personaje entero pesa lo suyo
            sv["t_gasto"] = max(2.5, 12.0 - (self.t - sv.get("t_guardado_gasto", -99.0)))
        if sv.get("t_gasto") is not None:
            sv["t_gasto"] -= dt
            if sv["t_gasto"] <= 0 and not self.transicion:
                sv["t_guardado_gasto"] = self.t
                self.sv_guardar()

    def sv_estado(self):
        """Lo que se añade a tu posición en cada envío: salud, dinero, arma, barrio y demás."""
        j = self.j
        x, y = self.pos()
        v = j.veh
        try:
            barrio = self.mundo.barrio(x, y)["id"]
        except Exception:
            barrio = None
        e = {"sa": round(max(0.0, j.salud), 1), "di": int(j.dinero), "ba": int(j.banco), "ar": j.arma, "b": barrio, "ag": int(bool(j.agachado)),
             "in": int(getattr(self, "interior", None) is not None), "es": int(j.estrellas), "po": self._sv_mi_policia(), "vi": getattr(v, "id_red", None) if v is not None and getattr(v, "red_mio", False) else None}
        if getattr(self, "pasajero", None) is not None:          # vas en el vehículo de otro: que no te tomen por alguien a pie
            e["pj"] = self.pasajero
        emisora = self.sv_emisora()
        if emisora:
            e["ra"] = emisora
        return e

    def sv_emisora(self):
        """La emisora del juego que llevas puesta al volante, para que la oiga quien esté cerca. Solo sale su nombre corto,
        y solo si es una de las emisoras de serie: de «Mi música» y de las emisoras hechas con archivos tuyos no sale nada."""
        if self.j.veh is None or not self.sv_sabe("radio") or not self.sv["info"].get("radio_coches"):
            return ""
        radio = self.app.radio
        ident = radio.id_actual()
        return ident if ident in radio.comunes() and radio.sonando_ahora() else ""

    def _sv_parar_radio_ajena(self):
        ra = self.sv.get("radio_ajena")
        if ra is not None and ra.get("canal") is not None:
            ra["canal"].parar()
        self.sv["radio_ajena"] = None

    def _sv_radio_ajena(self):
        """La radio del vehículo de otro jugador: si está cerca y lleva una emisora de las de serie, se oye desde su
        vehículo, floja y apagada. Solo una a la vez, la más cercana, y nunca encima de tu propia radio."""
        sv = self.sv
        ra = sv.get("radio_ajena")
        mejor = None
        radio = self.app.radio
        if self.cfg["radio_coches"] and not self.transicion and getattr(self, "interior", None) is None and not radio.sonando_ahora():
            x, y = self.pos()
            listas = radio.comunes()
            cerca = [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and r.veh and getattr(r, "radio", "") in listas
                     and r.dist(x, y) < RADIO_AJENA_M]
            if cerca:
                mejor = min(cerca, key=lambda r: r.dist(x, y))
        if ra is not None and (mejor is None or ra["de"] != mejor.id or ra["emisora"] != mejor.radio):
            self._sv_parar_radio_ajena()
            ra = None
        if mejor is None:
            return
        if ra is None:
            ra = sv["radio_ajena"] = {"de": mejor.id, "emisora": mejor.radio, "canal": None, "datos": None, "listo": False}
            guardadas = self.app.__dict__.setdefault("_radio_muestras", {})
            if mejor.radio in guardadas:
                ra["datos"], ra["listo"] = guardadas[mejor.radio], True
            else:
                def cargar(ra=ra, ident=mejor.radio):
                    d = radio.muestra(ident)
                    if d is not None:
                        if len(guardadas) >= 2:
                            guardadas.clear()
                        guardadas[ident] = d
                    ra["datos"], ra["listo"] = d, True
                ra["hilo"] = threading.Thread(target=cargar, daemon=True)
                ra["hilo"].start()
        if ra["canal"] is None and ra["listo"] and ra["datos"] is not None:
            self.mez.registrar(SON_RADIO_AJENA, ra["datos"])
            ra["canal"] = self.son(SON_RADIO_AJENA, bucle=True, xy=(mejor.x, mejor.y), ref=5, maxd=RADIO_AJENA_M, vol=0.45, cat="musica")
            if not sv.get("radio_ajena_dicha"):                  # la primera vez se explica qué es y cómo se quita
                sv["radio_ajena_dicha"] = True
                self.decir(tr('Lo que suena es la radio del vehículo de {nombre}. Si no quieres oír las radios de los demás, se quita en Opciones, Sonido y música.').format(nombre=(mejor.nombre)))
        elif ra["canal"] is not None:
            ra["canal"].mover(mejor.x, mejor.y)

    def sv_dicho(self, clave, texto, cada=4.0, interrumpir=False):
        """Dice algo, pero no la misma cosa a cada momento."""
        if self.t - self.sv["t_dicho"].get(clave, -999.0) >= cada:
            self.sv["t_dicho"][clave] = self.t
            self.decir(texto, interrumpir)

    def sv_segura(self):
        if not self.sv["info"].get("seguras"):
            return False
        if getattr(self, "interior", None) is not None:
            return True
        x, y = self.pos()
        return any(l.tipo in ("hospital", "comisaria", "casa", "ong", "protectora") and math.hypot(l.x - x, l.y - y) <= 16 for l in self.mundo.lugares.values())

    # ---------------------------------------------------------- cada fotograma
    def sv_paso(self, dt):
        if not self.en_servidor:
            return
        sv = self.sv
        if sv.get("reenganche"):
            self._sv_reenganche_paso()
        if sv.get("regrupo"):
            self._sv_regrupo_paso()
        sv["t_guardar"] -= dt
        if sv["t_guardar"] <= 0 and not self.transicion:
            self.sv_guardar()
        self._sv_vigilar_gasto(dt)
        self._sv_radio_ajena()
        if sv["info"].get("pvp"):
            segura = self.sv_segura()
            if segura != sv["segura"]:
                sv["segura"] = segura
                self.son("llegada" if segura else "menu_atras", cat="interfaz", vol=0.5)
                self.sv_dicho("segura", tr("Zona segura: aquí nadie puede herir a nadie.") if segura else tr("Sales de la zona segura."), 6.0)
            if sv["protegido"] and time.time() >= sv["protegido"]:
                sv["protegido"] = 0
                self.decir(tr("Se acaba la protección de llegada."))
        x0, y0 = self.pos()
        for r in self.remotos.values():              # quien te atacó deja de contar como enemigo al cabo de un rato
            if r.hostil and self.t - getattr(r, "t_hostil", 0.0) > 90:
                r.hostil = False
            # a quien persigue la policía se le oye venir: las sirenas van con él
            perseguido = getattr(r, "estrellas", 0) > 0 and r.mapa == self.mundo.id and r.visto and r.dist(x0, y0) < 220 and not self.sv_policia_comun()
            sirena = getattr(r, "sirena", None)
            if perseguido and sirena is None:
                r.sirena = self.son("sirena_lejana", bucle=True, xy=(r.x, r.y), ref=12, maxd=220, vol=0.5)
            elif perseguido:
                sirena.mover(r.x, r.y)
            elif sirena is not None:
                sirena.parar()
                r.sirena = None
        # atropellar a otro jugador
        v = self.j.veh
        sv["t_atropello"] -= dt
        if v is not None and abs(v.vel) > 4 and sv["t_atropello"] <= 0 and sv["info"].get("pvp"):
            for r in self.remotos.values():
                # quien va de pasajero, contigo o con otro, no está en la calzada: su posición es la del vehículo que le lleva
                if getattr(r, "pasajero_de", None) is not None or r.id in sv["pasajeros"]:
                    continue
                if r.mapa == self.mundo.id and r.visto and not r.veh and r.dist(v.x, v.y) < 3.2:
                    sv["t_atropello"] = 1.2
                    self.red.enviar({"t": "atropello", "a": r.id})
                    break
        self._sv_grupo_paso(dt)

    # ----------------------------------------------------------------- mensajes
    def sv_mensaje(self, m):
        """Devuelve True si el mensaje era del servidor y ya está atendido."""
        if not self.en_servidor:
            return False
        f = getattr(self, "_svm_" + str(m.get("t")), None)
        if f is None:
            return False                         # un mensaje que este juego no conoce: quien lo recibe después lo deja pasar
        try:
            f(m)
        except (KeyError, TypeError, ValueError, AttributeError, IndexError):
            # Un servidor de otra versión puede mandar un mensaje conocido con otra forma. No es motivo para que el juego
            # se caiga: se anota y se sigue.
            registro.excepcion("red", "Un mensaje del servidor no tiene la forma que este juego espera", tipo=str(m.get("t"))[:30])
        return True

    def _svm_aviso(self, m):
        if m.get("son") and m["son"] in self.mez.sonidos:
            self.son(m["son"], cat="interfaz", vol=0.6)
        self.decir(tr_servidor(str(m.get("texto", ""))))
        self.voz.apuntar_mensaje(tr_servidor(str(m.get("texto", ""))))

    def _svm_pong(self, m):
        pass

    def _svm_guardado(self, m):
        pass

    def _svm_hora(self, m):
        h = m.get("h") or {}
        try:
            reloj, dia = float(h.get("reloj", self.reloj)), int(h.get("dia", self.dia))
        except (TypeError, ValueError):
            return
        llueve = bool(h.get("lluvia"))
        if llueve != self.lluvia:
            self.lluvia = llueve
            self.son("trueno" if llueve else "pajaro", cat="ambiente")
            self.decir(tr("Empieza a llover. El asfalto mojado alarga las frenadas.") if llueve else tr("Deja de llover."))
        if dia != self.dia:
            self.dia = dia
            self.plazas_usadas.clear()
            self._cobrar_negocios()
            self.sortear_dia()
        self.reloj = reloj
        if "luces" in h:                                         # los semáforos, iguales para todos
            for mapa in self.mapas.values():
                mapa.desfase_luces = float(h["luces"]) - self.t

    def _svm_aspecto(self, m):
        self._aspecto_recibido(m.get("de"), m.get("texto"))

    def _svm_entra(self, m):
        self._aspecto_enviado = None                             # que el que llega sepa también cómo vas
        registro.ocultar(m.get("nombre"))
        r = Remoto(m["id"], tr(str(m.get("nombre", "Alguien"))) if m.get("ia") else str(m.get("nombre", "Alguien")))
        r.banda, r.ia = m.get("banda"), bool(m.get("ia"))
        self.remotos[m["id"]] = r
        if r.ia:
            return                               # los personajes del servidor van y vienen sin anunciarse
        self.son("amigo_entra", cat="interfaz")
        self.decir(tr('{nombre} entra en el servidor.').format(nombre=(r.nombre)))
        self.voz.apuntar_mensaje(tr('{nombre} entra en el servidor.').format(nombre=(r.nombre)))

    def _svm_sale(self, m):
        r = self.remotos.pop(m.get("id"), None)
        self.sv["pasajeros"].discard(m.get("id"))
        if r:
            r.callar()
            self._sv_quitar_policia(r)
            if getattr(r, "sirena", None) is not None:
                r.sirena.parar()
            if self.objetivo is r:
                self.objetivo = None
            if getattr(r, "ia", False):
                return
            self.son("amigo_sale", cat="interfaz")
            self.decir(tr('{nombre} sale del servidor.').format(nombre=(r.nombre)))
            self.voz.apuntar_mensaje(tr('{nombre} sale del servidor.').format(nombre=(r.nombre)))

    def _svm_estados(self, m):
        if "tr" in m:
            self._sv_trafico(m.get("tr") or [])
        if "lu" in m:
            self.mundo.desfase_luces = float(m["lu"]) - self.t
        if "pe" in m:
            self._sv_peatones(m.get("pe") or [])
        if "po" in m:
            self._sv_agentes(m.get("po") or [])
        if "es" in m:
            self._sv_cuadrar_busqueda(m.get("es"))
        for clave, e in (m.get("e") or {}).items():
            try:
                ident = int(clave)
            except ValueError:
                continue
            r = self.remotos.get(ident)
            if r is None or not isinstance(e, dict):
                continue
            try:
                r.tx, r.ty = float(e.get("x") or 0), float(e.get("y") or 0)
                r.rumbo, r.vel = float(e.get("r") or 0), float(e.get("s") or 0)
            except (TypeError, ValueError):
                continue
            if e.get("m") != r.mapa or not r.visto:
                r.x, r.y = r.tx, r.ty
                r.visto = True
            r.mapa = e.get("m")
            r.veh = e.get("v") if e.get("v") in self.modelos else ("utilitario" if e.get("v") else None)
            if "vi" in e:
                r.vid, r.agachado, r.pasivo, r.segura, r.dentro = e.get("vi"), bool(e.get("ag")), bool(e.get("pa")), bool(e.get("sg")), bool(e.get("in"))
                r.estrellas = int(e.get("es") or 0)
                r.pasajero_de = e.get("pj") if isinstance(e.get("pj"), int) else None      # de quién va de pasajero, si va
                r.radio = e.get("ra") if isinstance(e.get("ra"), str) else ""               # la emisora del juego que lleva puesta
                self._sv_policia_de(r, e.get("po") or [])

    # ------------------------------------------------------------ policía común
    def _sv_mi_policia(self):
        """La policía que te persigue en tu juego: se la cuentas al servidor para que la tengan también los que están cerca."""
        if not self.j.estrellas or self.sv_policia_comun():
            return []
        out = []
        for v in self.vehiculos:
            if v.ia == "policia" and not v.muerto and len(out) < 4:
                out.append(["v", v.id, v.modelo["id"], round(v.x, 1), round(v.y, 1), int(v.rumbo)])
        for p in self.personas:
            if p.tipo == "policia" and not p.muerto and len(out) < 9:
                out.append(["p", p.id, round(p.x, 1), round(p.y, 1)])
        return out

    def _sv_policia_de(self, r, lista):
        """Patrullas y agentes que persiguen a otro jugador, puestos en tu juego donde están en el suyo."""
        ecos = getattr(r, "poli", None)
        if ecos is None:
            ecos = r.poli = {}
        if not lista and not ecos:
            return
        vistos = set()
        for f in lista:
            try:
                clave = (f[0], int(f[1]))
                if f[0] == "v":
                    modelo, x, y, rumbo = f[2], float(f[3]), float(f[4]), float(f[5])
                else:
                    x, y = float(f[2]), float(f[3])
            except (TypeError, ValueError, IndexError):
                continue
            o = ecos.get(clave)
            if o is None or o.muerto:
                if f[0] == "v":
                    if modelo not in self.modelos:
                        continue
                    o = self.crear_vehiculo(modelo, x, y, M.dir_de_rumbo(rumbo), "servidor", tr("Coche patrulla"))
                    o.eco_poli, o.ocupado = True, True
                    o.sirena = self.son("sirena", bucle=True, xy=(x, y), ref=14, maxd=260, vol=0.5)
                else:
                    o = Persona("civil", x, y, tr("Policía"))
                    o.estado, o.tag, o.eco_poli, o.eco_de = "quieto", "eco", clave[1], r.id
                    self.personas.append(o)
                ecos[clave] = o
            if f[0] == "v":
                o.tx, o.ty, o.rumbo, o.vel = x, y, rumbo, 8.0
            else:
                o.x, o.y = x, y
            o.t_visto = self.t
            vistos.add(clave)
        for clave, o in list(ecos.items()):
            if clave not in vistos and self.t - getattr(o, "t_visto", 0.0) > 1.2:
                self._sv_quitar_eco_poli(o)
                del ecos[clave]

    def _sv_quitar_eco_poli(self, o):
        if isinstance(o, Persona):
            if o in self.personas:
                self.personas.remove(o)
            if self.objetivo is o:
                self.objetivo = None
        elif not o.muerto:
            self.quitar_vehiculo(o)

    def _sv_quitar_policia(self, r):
        for o in list(getattr(r, "poli", {}).values()):
            self._sv_quitar_eco_poli(o)
        r.poli = {}

    def sv_golpe_policia(self, p, dano):
        """Le has dado a un agente de los que persiguen a otro jugador: el golpe va también a su juego."""
        if self.en_servidor and getattr(p, "eco_de", None) is not None and not getattr(self, "_sv_aplicando", False):
            self.red.enviar({"t": "po_golpe", "a": p.eco_de, "k": p.eco_poli, "dano": round(float(dano), 1)})

    def _svm_po_golpe(self, m):
        p = next((q for q in self.personas if q.tipo == "policia" and q.id == m.get("k") and not q.muerto), None)
        if p is not None:
            self._sv_aplicando = True
            try:
                self.danar_persona(p, float(m.get("dano", 0)))
            finally:
                self._sv_aplicando = False

    def _svm_patrulla_llega(self, m):
        """Una patrulla del servidor que rondaba cerca viene a por ti: desde ahora es de las que te persiguen."""
        if m.get("ya"):                                          # la sigue llevando el servidor: solo te enteras
            self.sv_dicho("patrulla", tr("Una patrulla que rondaba por aquí viene a por ti."), 8.0)
            return
        if not self.j.estrellas or "patrulla" not in self.modelos:
            return
        v = self.crear_vehiculo("patrulla", float(m.get("x", 0)), float(m.get("y", 0)), int(m.get("d", 0)) % 4, "policia")
        v.ocupado, v.hostil, v.vel = True, True, 12.0
        self.sv_dicho("patrulla", tr("Una patrulla que rondaba por aquí viene a por ti."), 8.0)

    def _svm_visto(self, m):
        self.decir(tr("Te ha visto una patrulla."))
        self.delito(2, tr("disparos delante de una patrulla"), siempre=True)

    # --------------------------------------------- la policía que lleva el servidor
    def sv_policia_comun(self):
        """¿La búsqueda, la persecución y la detención las lleva el servidor? Entonces tu juego no pone su policía."""
        return self.en_servidor and bool(self.sv["info"].get("policia"))

    def sv_delito(self, puntos):
        if self.sv_policia_comun() and puntos > 0:
            self.red.enviar({"t": "delito", "n": round(float(puntos), 2)})

    def sv_busqueda(self, nivel, fin=False):
        """Tu juego pone un nivel de búsqueda, o la da por terminada: pintar el coche, pagar la multa, acabar en comisaría."""
        if self.sv_policia_comun() and not getattr(self, "_sv_busqueda_suya", False):
            self.red.enviar({"t": "busqueda", "nivel": int(nivel), "fin": bool(fin)})

    def _sv_limpiar_busqueda(self, hablar):
        self._sv_busqueda_suya = True                            # lo dice el servidor: no hace falta contárselo de vuelta
        try:
            self.limpiar_busqueda(hablar)
        finally:
            self._sv_busqueda_suya = False

    def _svm_nivel_busqueda(self, m):
        from .combate import UMBRAL
        try:
            es, pu = max(0, min(5, int(m.get("es") or 0))), float(m.get("pu") or 0)
        except (TypeError, ValueError):
            return
        self.sv["t_desfase"] = None
        if es == 0:
            if self.j.estrellas or self.j.puntos_busqueda:
                self._sv_limpiar_busqueda(m.get("motivo") == "perdida")
            return
        if m.get("motivo") == "vuelve":
            self.decir(tr("La policía no se ha olvidado de ti: te siguen buscando."))
        self.j.puntos_busqueda = max(pu, float(UMBRAL[es - 1]))

    def _sv_cuadrar_busqueda(self, es):
        """El nivel de búsqueda que vale es el del servidor. Si el tuyo lleva unos segundos sin coincidir, se corrige."""
        from .combate import UMBRAL
        try:
            es = max(0, min(5, int(es or 0)))
        except (TypeError, ValueError):
            return
        mio = sum(1 for u in UMBRAL if self.j.puntos_busqueda >= u)
        if es == mio:
            self.sv["t_desfase"] = None
        elif self.sv["t_desfase"] is None:
            self.sv["t_desfase"] = self.t
        elif self.t - self.sv["t_desfase"] > 3.0:
            self.sv["t_desfase"] = None
            if es == 0:
                self._sv_limpiar_busqueda(False)
            else:
                self.j.puntos_busqueda = float(UMBRAL[es - 1])
                if es < self.j.estrellas:
                    self.j.estrellas = es

    def sv_buscando(self, dt):
        """Mientras te buscan: el tic de que no tienes a nadie cerca. Despistarlos lo decide el servidor."""
        j = self.j
        x, y = self.pos()
        r_p, r_v = (70, 80) if j.veh else (38, 45)
        cerca = any(p.tipo == "policia" and not p.muerto and p.dist(x, y) < r_p for p in self.personas) or \
            any(self.es_patrulla(v) and not v.muerto and v.dist(x, y) < r_v for v in self.vehiculos)
        if not cerca:
            self.t_buscando -= dt
            if self.t_buscando <= 0:
                self.t_buscando = 1.0
                self.son("buscando", vol=0.6, cat="interfaz")

    def es_patrulla(self, v):
        """Un coche de policía: de los de tu juego, o de los que lleva el servidor."""
        return v.ia == "policia" or bool(getattr(v, "tr_poli", False))

    def _sv_agentes(self, lista):
        """Los agentes a pie que lleva el servidor: están donde él dice, y van a por quien él dice."""
        gente = self.sv["agentes"]
        vistos = set()
        for f in lista:
            try:
                ident, x, y, obj, arma = f[0], float(f[1]), float(f[2]), f[3], str(f[4])
            except (TypeError, ValueError, IndexError):
                continue
            vistos.add(ident)
            p = gente.get(ident)
            if p is None:
                p = Persona("policia", x, y)
                p.po_id, p.tag, p.salud, p.estado, p.activo = ident, "comun", 80, "ataca", True
                try:                                         # la salud que dice el servidor, según el nivel de búsqueda; uno anterior no la manda
                    p.salud = max(1.0, min(1000.0, float(f[5]))) if len(f) > 5 else 80
                except (TypeError, ValueError):
                    p.salud = 80
                self.personas.append(p)
                gente[ident] = p
            p.tx, p.ty, p.t_visto = x, y, self.t
            p.arma = arma if arma in self.armas_d else "pistola"
            p.hostil = obj == self.sv.get("id") and not p.muerto
        for ident, p in list(gente.items()):
            if ident not in vistos and self.t - getattr(p, "t_visto", 0.0) > 1.2:
                del gente[ident]
                if p.muerto:
                    p.tag = None                         # el caído se queda un rato y luego lo retira tu juego
                elif p in self.personas:
                    self.personas.remove(p)
                    if self.objetivo is p:
                        self.objetivo = None

    def sv_agente_paso(self, p, d, dt):
        """Un agente del servidor en tu juego: va hacia donde dice el servidor, y se le oye andar."""
        tx, ty = getattr(p, "tx", p.x), getattr(p, "ty", p.y)
        falta = math.hypot(tx - p.x, ty - p.y)
        f = min(1.0, dt * 10.0)
        p.x += (tx - p.x) * f
        p.y += (ty - p.y) * f
        if falta > 0.15 and d < 30:
            p.t_paso -= dt
            if p.t_paso <= 0:
                p.t_paso = 0.33
                self.son("paso_npc", xy=(p.x, p.y), ref=3, maxd=30, vol=0.9, tono=0.85)

    def sv_golpe_agente(self, p, dano):
        """Le has dado a un agente del servidor: lo que le pase, le pasa para todos."""
        if self.en_servidor and getattr(p, "po_id", None) is not None and not p.muerto:
            self.red.enviar({"t": "po_dano", "id": p.po_id, "n": round(float(dano), 1), "cae": p.salud - dano <= 0})

    def _svm_po_cae(self, m):
        p = self.sv["agentes"].get(m.get("id"))
        if p is not None and not p.muerto:
            p.muerto, p.hostil, p.t_estado = True, False, self.t
            self.son("muerte_npc", xy=(p.x, p.y), ref=6, tono=p.tono)
            if self.objetivo is p:
                self.objetivo = None

    def _svm_po_apunta(self, m):
        self.son("amartillar", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=5, maxd=50)

    def _svm_po_disparo(self, m):
        """Un agente dispara. Lo oyen todos los que están cerca; le da, si le da, a quien persigue."""
        try:
            x, y, da = float(m.get("x", 0)), float(m.get("y", 0)), float(m.get("da") or 0)
        except (TypeError, ValueError):
            return
        a = self.armas_d.get(m.get("arma")) or self.armas_d.get("pistola") or self.armas_d["punos"]
        self.son(a["sonido"], xy=(x, y), ref=14, maxd=220, vol=0.9)
        if m.get("a") != self.sv.get("id") or self.transicion:
            return
        j = self.j
        if da <= 0:
            self.son("bala_silbido", pan=random.uniform(-0.9, 0.9), vol=0.5)
        elif j.veh:
            self.son("bala_impacto", vol=0.6)
            self.danar_vehiculo(j.veh, da)
            if random.random() < 0.3:
                self.danar_jugador(da * 0.5, (x, y))
        else:
            self.danar_jugador(da, (x, y))

    def _svm_po_embiste(self, m):
        v = self.j.veh
        if v is None:
            return
        self.son("choque_leve")
        self.danar_vehiculo(v, float(m.get("n") or 7))
        v.vel *= 0.75

    def _svm_detenido(self, m):
        """Un agente te ha echado el guante. Lo que venga después (la multa, el soborno, el calabozo) es lo de siempre."""
        if self.j.estrellas == 0:
            self.j.estrellas = 1
        self.detener()

    # ------------------------------------------------------- gente de la calle
    def sv_peatones_comunes(self):
        """¿La gente de la calle la pone el servidor? Entonces tu juego no pone la suya."""
        return self.en_servidor and bool(self.sv["info"].get("peatones"))

    def _sv_peatones(self, lista):
        gente = self.sv["peatones"]
        vuelta = 4 * (M.B - 15)
        vistos = set()
        for f in lista:
            try:
                ident, bi, bj, u, s, huye, vel = f[0], int(f[1]), int(f[2]), float(f[3]), int(f[4]), bool(f[5]), float(f[6])
                atracado = bool(f[7]) if len(f) > 7 else False
            except (TypeError, ValueError, IndexError):
                continue
            vistos.add(ident)
            p = gente.get(ident)
            if p is None:
                p = Persona("civil", 0, 0)
                p.bloque, p.u, p.pe_id, p.tag = (bi, bj), u, ident, "comun"
                self._pos_perimetro(p)
                self.personas.append(p)
                gente[ident] = p
            p.t_visto = self.t
            if p.muerto:
                continue
            if abs(((p.u - u + vuelta / 2) % vuelta) - vuelta / 2) > 3:       # se ha desviado de donde dice el servidor
                p.u = u
            p.sentido, p.vel = s, vel
            if huye:
                p.estado, p.t_estado, p.t_voz = "huye", 3.0, 5.0
            elif p.estado == "huye" and getattr(p, "t_susto", -99) < self.t - 1.5:
                p.estado = "pasea"
            if atracado:
                p.atracado = True
        for ident, p in list(gente.items()):
            if ident not in vistos and self.t - getattr(p, "t_visto", 0.0) > 1.5:
                del gente[ident]
                if p.muerto:
                    p.tag = None                         # el caído se queda un rato y luego lo retira tu juego
                elif p in self.personas:
                    self.personas.remove(p)
                    if self.objetivo is p:
                        self.objetivo = None

    def sv_golpe_peaton(self, p, dano):
        """Le has dado a alguien de la calle que es de todos: lo que le pase, le pasa para todos."""
        if self.en_servidor and getattr(p, "pe_id", None) is not None and not p.muerto:
            p.t_susto = self.t
            self.red.enviar({"t": "pe_dano", "id": p.pe_id, "n": round(float(dano), 1), "cae": p.salud - dano <= 0})

    def sv_peaton_atracado(self, p):
        if self.en_servidor and getattr(p, "pe_id", None) is not None:
            p.t_susto = self.t
            self.red.enviar({"t": "pe_atraco", "id": p.pe_id})

    def _svm_pe_cae(self, m):
        p = self.sv["peatones"].get(m.get("id"))
        if p is not None and not p.muerto:
            p.muerto, p.t_estado = True, self.t
            self.son("muerte_npc", xy=(p.x, p.y), ref=6, tono=p.tono)
            if self.objetivo is p:
                self.objetivo = None

    # ------------------------------------------------------------ tráfico común
    def sv_trafico_comun(self):
        """¿Los coches que circulan los pone el servidor? Entonces tu juego no pone los suyos."""
        return self.en_servidor and bool(self.sv["info"].get("trafico"))

    def _sv_trafico(self, lista):
        vistos = set()
        for fila in lista:
            try:
                ident, modelo, x, y, rumbo, vel = fila[0], fila[1], float(fila[2]), float(fila[3]), float(fila[4]), float(fila[5])
                poli = int(fila[6]) if len(fila) > 6 else 0
            except (TypeError, ValueError, IndexError):
                continue
            v = self.sv["trafico"].get(ident)
            if v is None or v.muerto:
                if modelo not in self.modelos:
                    continue
                v = self.crear_vehiculo(modelo, x, y, M.dir_de_rumbo(rumbo), "servidor")
                v.tr_id, v.ocupado, v.cerrado, v.tr_poli = ident, True, False, bool(poli)
                if poli:
                    v.nombre = tr("Coche patrulla")
                self.sv["trafico"][ident] = v
            if poli >= 2 and v.sirena is None:                   # persigue a alguien: con la sirena puesta
                otras = sum(1 for o in self.vehiculos if o is not v and o.sirena is not None)
                v.sirena = self.son("sirena", bucle=True, xy=(x, y), ref=14, maxd=260, vol=0.8 / (1 + 0.6 * otras))
            elif poli < 2 and v.sirena is not None and v.tr_poli:
                v.sirena.parar()
                v.sirena = None
            if poli == 3 and not v.desplegado:                   # para y se bajan los agentes
                v.desplegado, v.ocupado = True, False
                self.son("puerta_coche", xy=(x, y))
            elif poli == 2 and v.desplegado:                     # se les escapa: se suben otra vez y siguen
                v.desplegado, v.ocupado = False, True
                self.son("puerta_coche", xy=(x, y))
            v.tx, v.ty, v.rumbo, v.vel, v.t_visto = x, y, rumbo, vel, self.t
            v.dir = M.dir_de_rumbo(rumbo)
            vistos.add(ident)
        for ident, v in list(self.sv["trafico"].items()):
            if ident not in vistos and self.t - getattr(v, "t_visto", 0.0) > 1.2:
                del self.sv["trafico"][ident]
                if v is not self.j.veh and not v.muerto:
                    self.quitar_vehiculo(v)

    def sv_trafico_paso(self, v, d, dt):
        """Un coche del tráfico común en tu juego: se mueve hacia donde dice el servidor y suena donde está."""
        f = min(1.0, dt * 10.0)
        v.x += (getattr(v, "tx", v.x) - v.x) * f
        v.y += (getattr(v, "ty", v.y) - v.y) * f
        if d < 100:
            self._motor(v, False)
            v.canal.mover(v.x, v.y)
            v.canal.tono(v.modelo["tono"] * (0.6 + 1.3 * abs(v.vel) / v.modelo["vel_max"]))
        elif v.canal:
            v.canal.parar()
            v.canal = None
        j = self.j
        if v.sirena:
            v.sirena.mover(v.x, v.y)
        # te atropella, como cualquier coche; pero no si vas de pasajero en el vehículo de otro jugador
        if not j.veh and v.vel > 3 and d < 2.4 and self.t > v.t_choque and not getattr(v, "eco_poli", False) and getattr(self, "pasajero", None) is None:
            v.t_choque = self.t + 1.5
            self.son("golpe")
            self.danar_jugador(v.vel * 2.2, (v.x, v.y))
            self.decir(tr("¡Te ha atropellado un vehículo!"))

    def _svm_tr_revienta(self, m):
        v = self.sv["trafico"].pop(m.get("id"), None)
        if v is not None and not v.muerto and v is not self.j.veh:
            v.tr_id, v.ia = None, None
            self.explotar(v)
        elif m.get("m") == self.mundo.id:
            self.son("explosion", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=30, maxd=400)

    def _svm_chat(self, m):
        de = self.remotos.get(m.get("de"))
        if de is not None and getattr(de, "ia", False):          # lo que dice un personaje del servidor: en tu idioma
            m = dict(m, nombre=de.nombre, texto=tr_servidor(str(m.get("texto", ""))))
        if m.get("canal") in CANALES_ROL:
            return self._sv_chat_rol(m.get("canal"), str(m.get("nombre", "Alguien")), str(m.get("texto", "")), m.get("de"))
        canal = {"cerca": tr(" aquí cerca"), "banda": tr(" a la banda"), "priv": tr(" solo a ti"), "grupo": tr(" al grupo")}.get(m.get("canal"), "")
        linea = f"{m.get('nombre', 'Alguien')}{canal}: {m.get('texto', '')}"
        self.chat.append(linea)
        del self.chat[:-40]
        self.son("chat", cat="interfaz")
        with registro.privado():
            dicho_chat = tr('{get} dice{canal}: {get2}').format(get=(m.get('nombre', tr('Alguien'))), canal=(canal), get2=(m.get('texto', '')))
            self.decir(dicho_chat)
            self.voz.apuntar_mensaje(dicho_chat)

    # --------------------------------------------------------------------- rol
    def sv_rol(self):
        """¿Hay canales de rol en este servidor? No los hay en uno anterior a la 1.7.1, ni si quien lo lleva los ha apagado."""
        return self.sv_sabe("rol") and bool(self.sv["info"].get("rol"))

    def sv_rol_motivo(self):
        if not self.sv_sabe("rol"):
            return tr("Este servidor va con una versión anterior y no tiene canales de rol: usa el chat de siempre.")
        return tr("Quien lleva este servidor tiene apagados los canales de rol: usa el chat de siempre.")

    def _sv_apuntar_rol(self, canal, linea):
        self.sv["historial"].append((canal, linea))
        del self.sv["historial"][:-80]
        self.chat.append(linea)
        del self.chat[:-40]

    def _sv_chat_rol(self, canal, nombre, texto, de=None):
        """Llega algo por un canal de rol: cada canal suena distinto y se dice de una manera. Lo dicho en personaje y las
        acciones suenan además desde donde está quien habla, para saber por dónde anda."""
        nombre_canal, sonido = CANALES_ROL[canal]
        if canal == "yo":
            linea = dicho = f"{nombre} {texto}"
        elif canal == "ic":
            linea, dicho = tr('{nombre}, en personaje: {texto}').format(nombre=(nombre), texto=(texto)), tr('{nombre} dice: {texto}').format(nombre=(nombre), texto=(texto))
        else:
            linea = dicho = tr('{nombre}, fuera de personaje: {texto}').format(nombre=(nombre), texto=(texto))
        self._sv_apuntar_rol(canal, linea)
        r = self.remotos.get(de)
        cerca = canal != "ooc" and r is not None and r.visto and r.mapa == self.mundo.id
        self.son(sonido if sonido in self.mez.sonidos else "chat", cat="interfaz", xy=(r.x, r.y) if cerca else None, ref=12, maxd=400)
        with registro.privado():
            self.decir(dicho)
            self.voz.apuntar_mensaje(dicho)

    def sv_enviar_chat(self, texto, canal="todos", a=None):
        """Manda un mensaje por un canal. Si empieza por una orden de rol (barra yo, barra ep, barra fp), va por ese canal.
        Devuelve si se ha enviado."""
        texto = (texto or "").strip()[:300]
        if texto.startswith("/"):
            orden, _, resto = texto[1:].partition(" ")
            if orden.lower() == "ficha":
                self.sv_poner_ficha(resto)
                return True
            if orden.lower() in ORDENES_ROL:
                canal, texto = ORDENES_ROL[orden.lower()], resto.strip()
        if not texto:
            return False
        if canal in CANALES_ROL:
            if not self.sv_rol():
                self.app.son("error")
                self.decir(self.sv_rol_motivo(), True)
                return False
            self.red.enviar({"t": "chat", "texto": texto, "canal": canal})
            linea = tr('Tú {texto}').format(texto=(texto)) if canal == "yo" else tr('Tú, {v}: {texto}').format(v=(CANALES_ROL[canal][0]), texto=(texto))
            self._sv_apuntar_rol(canal, linea)
            self.son(CANALES_ROL[canal][1] if CANALES_ROL[canal][1] in self.mez.sonidos else "chat", cat="interfaz", vol=0.6)
            self.decir(f"{self.red.nombre} {texto}" if canal == "yo" else tr("Enviado."), True)
            return True
        self.red.enviar({"t": "chat", "texto": texto, "canal": canal, "a": a})
        self.chat.append(tr('Tú: {texto}').format(texto=(texto)))
        self.voz.apuntar_mensaje(tr('Tú: {texto}').format(texto=(texto)))
        del self.chat[:-40]
        self.son("chat", cat="interfaz", vol=0.6)
        self.decir(tr("Enviado."), True)
        return True

    def _svm_rol_oido(self, m):
        if not m.get("n") and m.get("canal") != "ooc":
            self.decir(tr("No hay nadie lo bastante cerca para oírlo."))

    def sv_poner_ficha(self, texto):
        """Tu frase de ficha: la que los demás leen cuando te miran. Vacía, la quita."""
        if not self.sv_rol():
            self.app.son("error")
            self.decir(self.sv_rol_motivo(), True)
            return False
        texto = " ".join("".join(c for c in str(texto or "") if c.isprintable()).split())[:MAX_FICHA]
        registro.ocultar(texto) if texto else None
        self.red.enviar({"t": "ficha", "texto": texto})
        return True

    def sv_pedir_ficha(self, r, de_paso=False):
        """Pide al servidor la ficha de otro jugador; al llegar, se lee. Con «de_paso» (al mirarle con Mayúsculas J) no dice
        nada si no hay canales de rol ni si no ha escrito ninguna."""
        if not self.sv_rol():
            if not de_paso:
                self.app.son("error")
                self.decir(self.sv_rol_motivo(), True)
            return False
        self.sv["ficha_pedida"], self.sv["ficha_de_paso"] = r.id, bool(de_paso)
        self.red.enviar({"t": "ficha", "a": r.id})
        return True

    def _svm_ficha(self, m):
        texto = "".join(c for c in str(m.get("texto") or "") if c.isprintable())[:MAX_FICHA]
        nombre = str(m.get("nombre", "Alguien"))
        if m.get("tuya") or m.get("de") == self.sv.get("id"):
            self.sv["ficha"] = texto
            self.app.son("menu_ok")
            with registro.privado():
                self.decir(tr('Tu ficha dice ahora: {texto}').format(texto=(texto)) if texto else tr("Has quitado tu ficha."), True)
            return
        self.sv["fichas"][m.get("de")] = texto
        r = self.remotos.get(m.get("de"))
        if r is not None:
            r.ficha = texto
        if self.sv.pop("ficha_pedida", None) == m.get("de"):
            de_paso = self.sv.pop("ficha_de_paso", False)
            with registro.privado():
                if texto:
                    self.decir(tr('Ficha de {nombre}: {texto}').format(nombre=(nombre), texto=(texto)), not de_paso)
                elif not de_paso:
                    self.decir(tr('{nombre} no ha escrito ninguna ficha.').format(nombre=(nombre)), True)

    def _svm_cobro(self, m):
        n = min(self.j.dinero, max(0, int(m.get("n", 0))))
        self.j.dinero -= n
        self.son("caja" if "caja" in self.mez.sonidos else "dinero", cat="interfaz", vol=0.6)
        self.decir(tr('Pagas {n} euros: {get}. Te quedan {dinero}.').format(n=(n), get=(tr_servidor(str(m.get('motivo', '')))), dinero=(self.j.dinero)))

    def _svm_recibe(self, m):
        clase, ident, n = m.get("clase"), str(m.get("id", "")), max(1, int(m.get("n", 1)))
        nombre = tr_servidor(str(m.get("nombre", "Alguien")))
        if clase == "arma" and ident in self.armas_d:
            self.dar_arma(ident, 0)
            self.decir(tr('{nombre} te da: {nombre2}.').format(nombre=(nombre), nombre2=(self.armas_d[ident]['nombre'])))
        elif clase == "balas" and ident in self.j.armas:
            self.j.armas[ident]["reserva"] += n
            self.son("recarga", vol=0.6)
            self.decir(tr('{nombre} te da {n} balas de {lower}.').format(nombre=(nombre), n=(n), lower=(self.armas_d[ident]['nombre'].lower())))
        elif clase == "objeto" and ident in {o["id"] for o in self.datos["objetos"]}:
            self.j.objetos[ident] = self.j.objetos.get(ident, 0) + n
            self.son("recoger", cat="interfaz")
            self.decir(tr('{nombre} te da {n} de {lower}.').format(nombre=(nombre), n=(n), lower=(next(o['nombre'] for o in self.datos['objetos'] if o['id'] == ident).lower())))
        elif clase in ("arma", "objeto"):        # algo de otra versión del juego, o de un mod, que tu juego no tiene
            self.decir(tr('{nombre} te quiere dar algo que no existe en tu versión del juego, y no lo puedes recibir.').format(nombre=(nombre)))

    def _svm_dado(self, m):
        self.son("recoger", cat="interfaz", vol=0.5)
        self.decir(tr('Entregado a {get}.').format(get=(m.get('nombre', tr('tu compañero')))))

    def _svm_quien(self, m):
        self.sv["quien"] = m.get("e") or []

    def _svm_pasivo(self, m):
        self.sv["pasivo"] = bool(m.get("si"))
        self.son("notificacion", cat="interfaz", vol=0.5)
        self.decir(tr("Modo pasivo activado: no puedes herir a otros jugadores ni ellos a ti.") if self.sv["pasivo"] else tr("Modo pasivo quitado: vuelves a estar expuesto."))

    def _svm_expulsado(self, m):
        self.sv_salir(tr_servidor(str(m.get("motivo") or "")) or tr("Te han sacado del servidor."), al_menu=True)

    def _svm_parada(self, m):
        """El servidor avisa de que se va a reiniciar, con su cuenta atrás."""
        try:
            en = max(0, int(m.get("en") or 0))
        except (TypeError, ValueError):
            en = 0
        que = tr("para actualizarse") if m.get("causa") == "actualizacion" else tr("por mantenimiento")
        self.son("notificacion", cat="interfaz", vol=0.7)
        if not self.sv.get("parada_dicha"):
            self.sv["parada_dicha"] = True
            vuelta = (tr("No tienes que hacer nada: tu personaje se guarda solo y, en cuanto el servidor vuelva, te reconecto y sigues donde estabas.")
                      if self.cfg["reconectar"] else tr("Tu personaje se guarda solo. Cuando el servidor vuelva, entra otra vez desde Jugar en un servidor."))
            self.decir(tr('Aviso del servidor: dentro de {en} segundos se reinicia {que}. {vuelta}').format(en=(en), que=(que), vuelta=(vuelta)), True)
        else:
            self.decir(tr('El servidor se reinicia dentro de {en} segundos.').format(en=(en)))

    def _svm_cerrado(self, m):
        # Un servidor nuevo dice por qué se cierra: si es para actualizarse o por mantenimiento, se le espera; si lo han
        # apagado, no. Uno anterior no lo dice: no se sabe si va a volver, así que se le espera igual, por si acaso.
        causa = m.get("causa")
        motivo = tr_servidor(str(m.get("motivo") or "")) or tr("El servidor se ha cerrado.")
        if causa != "apagado" and self.sv_cortado(causa if causa in ("actualizacion", "reinicio") else "cierre", motivo, m.get("vuelve")):
            return
        self.sv_salir(motivo + tr(" Tu personaje está guardado."), al_menu=True)

    def _svm_desconectado(self, m):
        registro.aviso("red", "Se ha cortado la conexión con el servidor")
        if self.sv_cortado("corte"):
            return
        self.sv_salir(tr("Se ha perdido la conexión con el servidor. Tu personaje se guardó hace menos de un minuto: vuelve a entrar para seguir."), al_menu=True)

    # ----------------------------------------------------------------- economía
    def _sv_ajustar_saldo(self, sobra, callar=False, datos=None):
        """Quita lo que el servidor no reconoce: primero del bolsillo y luego del banco."""
        if sobra <= 0:
            return
        j = self.j
        de_mano = min(j.dinero, sobra)
        j.dinero -= de_mano
        j.banco -= min(j.banco, sobra - de_mano)
        if not callar:
            self.app.son("error")
            self.decir(self._sv_texto_tope(sobra, datos))

    def _sv_texto_tope(self, sobra, d=None):
        """Lo que se dice cuando el servidor retira dinero, con las cifras que mande. Uno anterior no manda ninguna."""
        if not d or d.get("tope") is None:
            return (tr('El servidor no reconoce {sobra} euros de lo que llevas, y se retiran. En un servidor no se puede ganar más de un tanto por hora fuera de las misiones y de lo que te dan otros jugadores.').format(sobra=(sobra)))
        try:
            tope, acumula, margen, por_minuto = int(d["tope"]), int(d.get("acumula") or d["tope"]), int(d.get("margen") or 0), int(d.get("por_minuto") or 0)
            ganado, aceptado = int(d.get("ganado") or 0), int(d.get("aceptado") or 0)
        except (TypeError, ValueError):
            return tr('El servidor no reconoce {sobra} euros de lo que llevas, y se retiran.').format(sobra=(sobra))
        texto = (tr('De los {ganado} euros que acabas de ganar, el servidor acepta {aceptado} y retira {sobra}. ').format(ganado=(ganado), aceptado=(aceptado), sobra=(sobra)) if ganado else
                 tr('El servidor retira {sobra} euros que no reconoce. ').format(sobra=(sobra)))
        texto += tr('Aquí se pueden ganar por cuenta propia hasta {tope} euros por hora').format(tope=(tope))
        if acumula > tope:
            texto += tr(', y lo que no uses se te guarda hasta {acumula}').format(acumula=(acumula))
        texto += ". "
        if margen <= 0 and por_minuto > 0:
            texto += tr('Ahora mismo has llegado al tope: recuperas {por_minuto} euros de margen cada minuto. ').format(por_minuto=(por_minuto))
        elif margen > 0:
            texto += tr('Te quedan {margen} euros de margen. ').format(margen=(margen))
        texto += tr("No cuentan contra el tope las misiones de la historia, lo que te dan otros jugadores")
        if int(d.get("encargos_hora") or 0) > 0:
            texto += tr(', ni los encargos repetibles, como contratos, combates y atracos, hasta {int} por hora de cada tipo').format(int=(int(d['encargos_hora'])))
        return texto + tr(". Cómo vas de margen está en el móvil, En línea, Datos y reglas de este servidor.")

    def _svm_saldo(self, m):
        self.sv["economia"] = {k: m.get(k) for k in ("tope", "acumula", "horas", "margen", "por_minuto", "encargos_hora", "encargo_max")} if m.get("tope") is not None else self.sv.get("economia")
        self._sv_ajustar_saldo(max(0, int(m.get("quita", 0))), datos=m)

    def _svm_economia(self, m):
        self.sv["economia"] = m.get("e") if isinstance(m.get("e"), dict) else None

    def sv_economia_txt(self):
        """Cómo va el tope de dinero de este servidor, en una frase, para el menú."""
        d = self.sv.get("economia")
        if not self.sv_sabe("topes"):
            return tr("Este servidor puede poner un tope a lo que ganas por hora, pero su versión no dice cuál")
        if not d:
            return tr("En este servidor no hay tope de ganancias: el dinero lo lleva tu juego")
        try:
            texto = tr('Ganancia por tu cuenta: hasta {int} euros por hora').format(int=(int(d['tope'])))
            if int(d.get("acumula") or 0) > int(d["tope"]):
                texto += tr(', que se acumulan hasta {int} si no los usas').format(int=(int(d['acumula'])))
            texto += tr('. Ahora te quedan {int} de margen').format(int=(int(d.get('margen') or 0)))
            if int(d.get("encargos_hora") or 0) > 0:
                texto += tr('. Aparte, se reconocen {int} encargos repetibles por hora de cada tipo, hasta {int2} euros cada uno').format(int=(int(d['encargos_hora'])), int2=(int(d.get('encargo_max') or 0)))
            return texto
        except (TypeError, ValueError, KeyError):
            return tr("Este servidor pone un tope a lo que ganas por hora")

    def sv_mision_ok(self, m):
        """Has completado una misión tuya: se lo dices al servidor para que dé por buena la recompensa. Si es un encargo
        repetible (un contrato, un combate, un atraco), le dices además cuánto paga: el servidor lo reconoce hasta un número
        de veces por hora, sin que gaste tu ganancia por hora. Un servidor anterior no hace caso de eso."""
        if self.en_servidor and not m.get("generada"):
            d = {"t": "mision_ok", "id": m["id"]}
            if m.get("repetible"):
                paga = int(((m.get("recompensa") or {}).get("dinero") or 0) * (0.5 if self.cfg["mod_dinero"] else 1.0))
                d.update(encargo=1, n=paga)
            self.red.enviar(d)

    def sv_encargo(self, tipo, paga):
        """Un cobro de los que se repiten y no pasan por una misión (la caja de un local sin guardia)."""
        if self.en_servidor and paga > 0:
            self.red.enviar({"t": "mision_ok", "id": str(tipo), "encargo": 1, "n": int(paga)})

    # -------------------------------------------------------------- propiedades
    def sv_dueno(self, l):
        """El nombre del jugador dueño de una casa o un negocio, si es de otro. None si es tuyo o de nadie."""
        if not self.en_servidor:
            return None
        d = self.sv["props"].get(l.id)
        return d["nombre"] if d is not None and d.get("cuenta") != self.sv.get("cuenta") else None

    def sv_comprado(self, l):
        """Has comprado una casa o un negocio: en un servidor queda a tu nombre para todos."""
        if self.en_servidor and int(l.get("precio", 0) or 0) > 0:
            self.sv["props"][l.id] = {"cuenta": self.sv.get("cuenta"), "nombre": self.red.nombre}
            self.red.enviar({"t": "prop_comprar", "lugar": l.id})

    def _sv_cuadrar_propiedades(self):
        """Al entrar: lo tuyo que el servidor aún no tiene apuntado se apunta, y lo que ya es de otro se te devuelve."""
        for pid in list(self.j.propiedades):
            l = self.lugares.get(pid)
            if l is None or int(l.get("precio", 0) or 0) <= 0 or l.tipo not in ("casa", "negocio"):
                continue
            d = self.sv["props"].get(pid)
            if d is None:
                self.sv_comprado(l)
            elif d.get("cuenta") != self.sv.get("cuenta"):
                self._sv_devolver(l, d.get("nombre", tr("otro jugador")))

    def _sv_devolver(self, l, nombre):
        if l.id in self.j.propiedades:
            self.j.propiedades.remove(l.id)
            precio = int(l.get("precio", 0) or 0)
            self.j.dinero += precio
            self.app.son("error")
            self.decir(tr('{nombre} ya es de {nombre2}: se te ha adelantado. Te devuelven los {precio} euros.').format(nombre=(l.nombre), nombre2=(nombre), precio=(precio)))

    def _svm_prop(self, m):
        yo = self.sv.get("cuenta")
        l = self.lugares.get(m.get("lugar"))
        if m.get("cuenta") is None:
            self.sv["props"].pop(m.get("lugar"), None)
        else:
            self.sv["props"][m.get("lugar")] = {"cuenta": m.get("cuenta"), "nombre": str(m.get("nombre", "")), "oferta": int(m.get("oferta") or 0)}
        if l is None:
            return
        if m.get("antes") == yo and m.get("cuenta") != yo:       # era tuyo y lo has vendido: el dinero llega aparte
            if l.id in self.j.propiedades:
                self.j.propiedades.remove(l.id)
        elif m.get("cuenta") == yo:
            if l.id not in self.j.propiedades:                   # se lo has comprado a otro jugador
                self.j.propiedades.append(l.id)
                self.son("mision_ok", cat="interfaz")
                self.decir(tr('¡{nombre} es tuyo!').format(nombre=(l.nombre)))
        elif m.get("cuenta") is not None:
            self._sv_devolver(l, str(m.get("nombre", tr("otro jugador"))))

    def sv_oferta(self, l):
        """Por cuánto vende su dueño esta propiedad a otros jugadores. Cero si no la vende."""
        d = self.sv["props"].get(l.id) if self.en_servidor else None
        return int(d.get("oferta") or 0) if d else 0

    def _svm_prop_no(self, m):
        l = self.lugares.get(m.get("lugar"))
        if l is not None and m.get("tope"):                      # el tope de negocios del servidor: sigue en venta para otros
            if l.id in self.j.propiedades:
                self.j.propiedades.remove(l.id)
                self.j.dinero += int(l.get("precio", 0) or 0)
            self.app.son("error")
            self.decir(tr('En este servidor nadie puede tener más de {n} negocios. {nombre} no es tuyo: te devuelven lo que pagaste.').format(n=int(m["tope"]), nombre=l.nombre))
            return
        if l is not None:
            self.sv["props"][l.id] = {"cuenta": -1, "nombre": str(m.get("nombre", ""))}
            self._sv_devolver(l, str(m.get("nombre", tr("otro jugador"))))

    def sv_tope_negocios(self):
        """Cuántos negocios deja tener este servidor a cada jugador. Cero sin tope, o fuera de un servidor."""
        return int(self.sv["info"].get("negocios_max") or 0) if self.en_servidor else 0

    def sv_sin_sitio_negocio(self, l, callar=False):
        """¿Te impide el tope del servidor comprar este negocio? Lo dice, salvo con callar, y devuelve True."""
        tope = self.sv_tope_negocios()
        if not tope or l.tipo != "negocio" or sum(1 for i in self.j.propiedades if (self.lug(i) is not None and self.lug(i).tipo == "negocio")) < tope:
            return False
        if callar:
            return True
        self.app.son("error")
        self.decir(tr('En este servidor nadie puede tener más de {n} negocios, y tú ya los tienes. Vende uno antes de comprar otro.').format(n=tope), True)
        return True

    def sv_forzosa(self, l):
        """Lo que cuesta quedarte a la fuerza con este negocio de otro jugador. Cero si el servidor no lo permite."""
        pct = int(self.sv["info"].get("forzosa") or 0) if self.en_servidor else 0
        return int(l.get("precio", 0) or 0) * pct // 100

    def sv_forzar_negocio(self, l):
        if self.sv_sin_sitio_negocio(l):
            return
        self.red.enviar({"t": "prop_forzar", "lugar": l.id})

    def sv_robar_negocio(self, l):
        self.red.enviar({"t": "robo", "lugar": l.id})

    def _svm_robo_empieza(self, m):
        l = self.lugares.get(m.get("lugar"))
        self.sv["robo"] = m.get("lugar")
        self.son("alarma", xy=(l.x, l.y) if l else None, vol=0.7)
        self.delito(3, tr("atraco a un negocio"), siempre=True)
        self.decir(tr('¡Atraco! Salta la alarma y a {get} le llega el aviso. Aguanta en la puerta {get2} segundos, a pie, sin alejarte.').format(get=(m.get('nombre', tr('su dueño'))), get2=(m.get('segundos', 20))), True)

    def _svm_robo_fin(self, m):
        self.sv["robo"] = None
        if m.get("ok"):
            n = max(0, int(m.get("botin", 0)))
            self.j.dinero += n
            self.j.stats["dinero_ganado"] += n
            self.son("dinero", cat="interfaz")
            self.decir(tr('Caja vaciada: {n} euros. Lárgate antes de que llegue su dueño.').format(n=(n)), True)
        else:
            self.app.son("error")
            self.decir(tr_servidor(str(m.get("motivo") or "")) or tr("El atraco ha fallado."), True)

    def _svm_robo_aviso(self, m):
        l = self.lugares.get(m.get("lugar"))
        r = self.remotos.get(m.get("de"))
        if r is not None:
            r.hostil, r.t_hostil = True, self.t           # quien te roba es enemigo: la Q le fija
        self.son("alarma", cat="interfaz", vol=0.7)
        self.app.vibrar(0.8, 0.8, 500)
        de_quien = tr("tu negocio") if m.get("tuyo") else tr("un negocio de tu banda")
        self.decir(tr('¡{get} está atracando {de_quien}, {v}! Tienes {get2} segundos para impedirlo.').format(get=(m.get('nombre', 'Alguien')), de_quien=(de_quien), v=(self.nombre_lugar(l) if l else ''), get2=(m.get('segundos', 20))), True)
        if l is not None and not self.mision and self.gps is None:
            self.gps_a_lugar(l, callar=True)

    def _sv_descontar_robos(self, total):
        if total <= 0:
            return
        j = self.j
        de_mano = min(j.dinero, total)
        j.dinero -= de_mano
        del_banco = min(j.banco, total - de_mano)
        j.banco -= del_banco
        self.son("animo_baja", cat="interfaz")
        self.decir(tr('A tus negocios les han robado {total} euros de la caja. Se te descuentan {v}.').format(total=(total), v=(de_mano + del_banco)))

    def _svm_robos_dia(self, m):
        self._sv_descontar_robos(int(m.get("total") or 0))

    # ------------------------------------------------------------------ combate
    def sv_objetivos(self, todos):
        """Los otros jugadores a los que se puede apuntar: con la Q, los que te han atacado; con Mayúsculas, todos."""
        if not self.en_servidor or not self.sv["info"].get("pvp"):
            return []
        x, y = self.pos()
        return [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and (r.hostil or todos) and r.dist(x, y) < 90]

    def sv_atacar(self, o, arma):
        """Disparas o golpeas a otro jugador: el servidor dice si llega."""
        self.red.enviar({"t": "ataque", "a": o.id, "arma": arma["id"]})

    def _sv_jugador_al_lado(self, radio):
        x, y = self.pos()
        cerca = [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and not r.veh and r.dist(x, y) <= radio]
        return min(cerca, key=lambda r: r.dist(x, y)) if cerca else None

    def sv_atracar_cerca(self):
        """La E junto a otro jugador: le atracas, como a cualquiera. True si había alguien."""
        if not self.en_servidor or not self.sv["info"].get("pvp"):
            return False
        r = self._sv_jugador_al_lado(4.5)
        if r is None:
            return False
        if self.arma()["id"] == "punos":
            self.decir(tr("Para atracar a alguien tienes que empuñar un arma."), True)
            return True
        self.son("grito", vol=0.5)
        self.red.enviar({"t": "atraco", "a": r.id})
        return True

    def sv_hablar_cerca(self):
        """La J junto a otro jugador, sin nadie más a quien hablar: le escribes a él. True si había alguien."""
        if not self.en_servidor:
            return False
        r = self._sv_jugador_al_lado(8.0)
        if r is None:
            return False
        from . import menus_enlinea
        menus_enlinea.chat(self, "priv", r.id, tr('Qué le dices a {nombre}').format(nombre=(r.nombre)))
        return True

    def _svm_atracado(self, m):
        n = min(self.j.dinero, max(0, int(m.get("pierde", 0))))
        self.j.dinero -= n
        self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
        self.son("grito", vol=0.6)
        self.app.vibrar(0.6, 0.6, 300)
        self.decir(tr('¡{get} te atraca a punta de arma! Te quita {n} euros. Pulsa Q para fijarle.').format(get=(m.get('nombre', 'Alguien')), n=(n)), True)

    def _svm_atraco_ok(self, m):
        n = max(0, int(m.get("botin", 0)))
        self.j.dinero += n
        self.j.stats["dinero_ganado"] += n
        self.son("dinero", cat="interfaz")
        self.delito(1.5, "atraco")
        self.decir(tr('Atracas a {get}: {n} euros.').format(get=(m.get('nombre', 'otro jugador')), n=(n)) if n else tr('Atracas a {get}, pero no lleva nada encima.').format(get=(m.get('nombre', 'otro jugador'))), True)

    def sv_explosion(self, x, y, arma_id):
        if self.en_servidor and arma_id:
            self.red.enviar({"t": "explosion", "x": round(x, 1), "y": round(y, 1), "arma": arma_id})

    def _sv_agresor(self, ident, nombre):
        self.sv["agresor"], self.sv["t_agresor"] = ident, self.t
        r = self.remotos.get(ident)
        if r is not None:
            if not r.hostil:
                self.sv_dicho("ataca", tr('¡{nombre} te ataca! Pulsa Q para fijarlo.').format(nombre=(nombre)), 5.0)
            r.hostil, r.t_hostil = True, self.t

    def _svm_herido(self, m):
        self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
        a = self.armas_d.get(m.get("arma"))
        ox, oy = float(m.get("x", self.j.x)), float(m.get("y", self.j.y))
        if a is not None:
            self.son(a["sonido"], xy=(ox, oy), ref=18 if a["tipo"] == "fuego" else 6, maxd=260)
        dano = float(m.get("dano", 0))
        if self.j.veh is not None:
            self.danar_vehiculo(self.j.veh, dano * 0.6)
        factor = self.dificultad() or 1.0        # entre jugadores no cuenta la dificultad que cada uno tenga puesta
        self.danar_jugador(dano / factor, (ox, oy))

    def _svm_silbido(self, m):
        self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
        self.son("bala_silbido", vol=0.8)

    def _svm_tiro(self, m):
        pass                                         # el disparo ya se oye por el aviso de ruido de quien dispara

    def sv_ruido(self, que):
        """Lo que haces y se oye: un disparo, un grito. Los demás jugadores de la localidad lo oyen donde estás."""
        if self.en_servidor:
            self.red.enviar({"t": "evento", "que": que[:20]})

    def _svm_evento(self, m):
        r = self.remotos.get(m.get("de"))
        if r is None or r.mapa != self.mundo.id:
            return
        que = str(m.get("que", ""))
        if que == "claxon":
            modelo = self.modelos.get(r.veh or "utilitario", {})
            self.son(modelo.get("claxon", "claxon"), xy=(r.x, r.y), ref=10, maxd=220, vol=0.8)
            return
        if que.startswith("d:"):
            a = self.armas_d.get(que[2:])
            if a is None:
                return
            self.son(a["sonido"], xy=(r.x, r.y), ref=18, maxd=260)
            radio = 40
        elif que == "grito":
            self.son("grito", xy=(r.x, r.y), ref=8, maxd=90, vol=0.7)
            radio = 15
        else:
            return
        for p in self.personas:                      # la gente de tu calle se asusta igual que si lo hubieras hecho tú
            if p.tipo == "civil" and not p.muerto and p.estado == "pasea" and p.dist(r.x, r.y) < radio:
                p.estado, p.t_estado = "huye", 8

    def _svm_estalla(self, m):
        self.son("explosion", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=30, maxd=400)

    def _svm_impacto(self, m):
        if self.cfg["aviso_acierto"]:
            self.son("tono_objetivo", cat="interfaz", vol=0.45, tono=2.0)
            self.app.vibrar(0.15, 0.8, 90)
        r = self.remotos.get(m.get("a"))
        if r is not None:
            self.son("dolor_npc", xy=(r.x, r.y), ref=6)
        self.sv_dicho("impacto", tr('Atropellas a {get}.').format(get=(m.get('nombre', tr('alguien')))) if m.get("atropello") else tr('Le das a {get}.').format(get=(m.get('nombre', tr('alguien')))), 3.0)

    def _svm_fallo(self, m):
        if m.get("motivo"):
            self.sv_dicho("motivo", tr_servidor(str(m["motivo"])), 3.0, True)
        elif m.get("lejos"):
            self.sv_dicho("lejos", tr("Fuera de alcance."), 2.5)

    def sv_al_morir(self):
        """Has caído. Si ha sido ante otro jugador, el servidor reparte el botín."""
        if self.en_servidor and self.sv["agresor"] is not None and self.t - self.sv["t_agresor"] < 15:
            self.red.enviar({"t": "caido", "por": self.sv["agresor"]})
        if self.en_servidor:
            self.sv["agresor"] = None
            self.sv["protegido"] = time.time() + float(self.sv["info"].get("proteccion", 0))

    def _svm_caes(self, m):
        n = min(self.j.dinero, max(0, int(m.get("pierde", 0))))
        self.j.dinero -= n
        self.decir(tr('Has caído ante {get}. Se lleva {n} euros de lo que llevabas encima.').format(get=(m.get('nombre', 'otro jugador')), n=(n)))

    def _svm_baja(self, m):
        n = max(0, int(m.get("botin", 0)))
        self.j.dinero += n
        self.j.stats["dinero_ganado"] += n
        r = self.remotos.get(m.get("a"))
        if r is not None:
            r.hostil = False
            if self.objetivo is r:
                self.objetivo = None
        self.son("mision_ok", cat="interfaz", vol=0.5)
        self.decir(tr('Has tumbado a {get}. Te llevas {n} euros.{get2}').format(get=(m.get('nombre', 'otro jugador')), n=(n), get2=(tr_servidor(str(m.get('texto', ''))))))

    def _svm_buscado(self, m):
        self.sv["recompensa"] = int(m.get("recompensa", 0))
        self.decir(tr('Has tumbado a alguien que no se defendía. Ofrecen {recompensa} euros por tu cabeza, y la policía te busca.').format(recompensa=(self.sv['recompensa'])))
        if self.mundo.policia:
            self.poner_busqueda(2)

    def _svm_muerte(self, m):
        self.sv_dicho("muerte", tr('{get} ha tumbado a {get2}.').format(get=(m.get('por', 'Alguien')), get2=(m.get('quien', tr('alguien')))), 1.0)

    # ---------------------------------------------------------------- vehículos
    def sv_poner_vehiculos(self):
        """Pone en tu calle los vehículos que otros jugadores han dejado aparcados en esta localidad."""
        if not self.en_servidor:
            return
        self.sv["trafico"] = {k: v for k, v in self.sv["trafico"].items() if not v.muerto and v in self.vehiculos}
        for r in self.remotos.values():              # al cambiar de localidad, lo que había de otros ya no está
            r.poli = {}
        self.sv["peatones"] = {}
        presentes = {getattr(v, "id_red", None) for v in self.vehiculos if not v.muerto}
        for d in self.sv["vehs"].values():
            if d.get("por") is None and d.get("m") == self.mundo.id and d["id"] not in presentes:
                self._sv_crear_copia(d)

    def _sv_crear_copia(self, d):
        if d.get("modelo") not in self.modelos:
            return None
        v = self.crear_vehiculo(d["modelo"], float(d["x"]), float(d["y"]), M.dir_de_rumbo(float(d.get("r", 0))), None, d.get("nombre"))
        v.rumbo = float(d.get("r", 0))
        v.salud = min(v.salud_max, float(d.get("salud", v.salud_max)))
        v.id_red, v.red_mio, v.cerrado = d["id"], False, False
        if d.get("mejoras"):
            from . import sistemas
            sistemas.poner(v, d.get("mejoras"))
        return v

    def _sv_copia(self, ident):
        return next((v for v in self.vehiculos if getattr(v, "id_red", None) == ident and not v.muerto), None)

    def sv_subido(self, v):
        """Te has subido a un vehículo: si era de tu mundo, desde ahora es de todos."""
        if not self.en_servidor or v.tag or getattr(v, "id_red", None) is not None:
            return
        v.red_ref = v.id
        self.red.enviar({"t": "veh_tomar", "modelo": v.modelo["id"], "nombre": v.nombre, "salud": round(v.salud, 1), "ref": v.id,
                         "mejoras": dict(getattr(v, "mejoras", {}) or {})})

    def sv_bajado(self, v):
        if self.en_servidor and getattr(v, "red_mio", False) and not v.muerto:
            v.red_mio, v.red_dueno = False, True
            d = {"id": v.id_red, "modelo": v.modelo["id"], "nombre": v.nombre, "m": self.mundo.id, "x": round(v.x, 1), "y": round(v.y, 1),
                 "r": round(v.rumbo), "salud": round(v.salud, 1), "por": None}
            self.sv["vehs"][v.id_red] = d
            self.sv.setdefault("mios", set()).add(v.id_red)
            self.red.enviar(dict(d, t="veh_dejar"))
            self._sv_traidos_pendientes()

    def sv_traido(self, v):
        """Tu mecánico te ha traído un vehículo de tu garaje: el servidor lo apunta como tuyo, aparcado en su calle, igual
        que si te hubieras bajado de él. Si vas conduciendo otro, se apunta en cuanto te bajes de ese."""
        if not self.en_servidor or v.tag or getattr(v, "id_red", None) is not None:
            return
        if self.j.veh is not None and getattr(self.j.veh, "id_red", None) is not None:
            self.sv.setdefault("traidos", []).append(v)
            return
        self.sv_subido(v)

    def _sv_traidos_pendientes(self):
        for v in self.sv.pop("traidos", None) or []:
            if not v.muerto and v in self.vehiculos and v is not self.j.veh:
                self.sv_subido(v)

    def sv_quitado(self, v):
        """Un vehículo tuyo deja de existir: al garaje, vendido o reventado."""
        if self.en_servidor and getattr(v, "id_red", None) is not None and (getattr(v, "red_mio", False) or getattr(v, "red_dueno", False)):
            v.red_mio = v.red_dueno = False
            self.sv["vehs"].pop(v.id_red, None)
            self.sv.setdefault("mios", set()).discard(v.id_red)
            self.red.enviar({"t": "veh_fin", "id": v.id_red})

    def sv_pedir_vehiculo(self, v):
        """F junto a un vehículo aparcado de otro jugador: se lo pides al servidor. True si hay que esperar la respuesta."""
        if self.en_servidor and (getattr(v, "eco_poli", False) or (getattr(v, "tr_poli", False) and not v.desplegado)):
            self.decir(tr("Ese coche patrulla está lleno de policías."), True)
            return True
        if self.en_servidor and getattr(v, "tr_id", None) is not None and v.ia == "servidor":      # un coche del tráfico común
            if abs(v.vel) > 6:
                self.decir(tr("Va demasiado rápido para abrir la puerta. Ponte delante: frenará."), True)
            else:
                self.red.enviar({"t": "tr_robar", "id": v.tr_id})
            return True
        if not self.en_servidor or getattr(v, "id_red", None) is None or getattr(v, "red_mio", False):
            return False
        self.red.enviar({"t": "veh_subir", "id": v.id_red})
        return True

    def sv_asaltar_cerca(self):
        """F junto al vehículo que conduce otro jugador: intentas sacarle. True si había alguien."""
        if not self.en_servidor:
            return False
        x, y = self.pos()
        cerca = [r for r in self.remotos.values() if r.mapa == self.mundo.id and r.visto and r.veh and getattr(r, "vid", None) and r.dist(x, y) <= 6]
        if not cerca:
            return False
        r = min(cerca, key=lambda r: r.dist(x, y))
        self.red.enviar({"t": "veh_asaltar", "id": r.vid})
        return True

    def sv_dano_copia(self, v, dano):
        """Le das a un vehículo aparcado de otro jugador: el daño lo lleva el servidor. True si era uno de esos."""
        if self.en_servidor and getattr(v, "eco_poli", False):
            return True                              # la patrulla de otro jugador: en tu juego es solo su presencia
        if self.en_servidor and getattr(v, "tr_id", None) is not None and v.ia == "servidor":
            self.red.enviar({"t": "tr_dano", "id": v.tr_id, "n": round(dano, 1)})
            return True
        if self.en_servidor and getattr(v, "id_red", None) is not None and not getattr(v, "red_mio", False):
            self.red.enviar({"t": "veh_dano", "id": v.id_red, "n": round(dano, 1)})
            return True
        return False

    def _svm_veh_tuyo(self, m):
        v = next((x for x in self.vehiculos if getattr(x, "red_ref", None) == m.get("ref") and getattr(x, "id_red", None) is None), None)
        if v is not None:
            v.id_red, v.red_mio = m["id"], self.j.veh is v
            if not v.red_mio:                        # ya se había bajado antes de que llegara la respuesta
                v.red_mio = True
                self.sv_bajado(v)

    def _svm_veh_ocupado(self, m):
        d = m.get("v") or {}
        if d.get("id") is not None:
            self.sv["vehs"][d["id"]] = d
            self.sv.setdefault("mios", set()).discard(d["id"])   # lo lleva otro: ya no es tuyo
        if m.get("tr") is not None:                              # otro jugador se ha quedado un coche del tráfico
            t = self.sv["trafico"].pop(m["tr"], None)
            if t is not None and not t.muerto and t is not self.j.veh:
                self.quitar_vehiculo(t)
        v = self._sv_copia(m.get("id"))
        if v is not None and v is not self.j.veh:
            v.red_dueno = False                      # ya no es tuyo: se lo ha llevado otro
            self.quitar_vehiculo(v)

    def _svm_veh_libre(self, m):
        d = m.get("v") or {}
        if d.get("id") is None:
            return
        self.sv["vehs"][d["id"]] = d
        v = self._sv_copia(d["id"])
        if d.get("m") == self.mundo.id and v is None:
            self._sv_crear_copia(d)
        elif v is not None and d.get("nombre") and v is not self.j.veh:      # su dueño le ha cambiado el nombre
            v.nombre = str(d["nombre"])[:40]

    # ------------------------------------------- tus vehículos aparcados, desde la lista del móvil
    def sv_veh_orden(self, que, d, **mas):
        """Pide al servidor algo para un vehículo tuyo que está aparcado: ponerle nombre, que te lo traigan o mandarlo a un
        garaje. Devuelve False, y lo dice, si el servidor es anterior y no sabe hacerlo."""
        if not self.sv_sabe("mis_vehiculos"):
            self.app.son("error")
            self.decir(tr("Este servidor va con una versión anterior y no sabe hacer eso con un vehículo aparcado. Ve hasta él: puedes cambiarle el nombre "
                       "al subir, y mandarlo al garaje desde Servicios con el vehículo al lado."), True)
            return False
        self.red.enviar(dict(mas, t="veh_" + que, id=d["id"]))
        return True

    def _svm_veh_mio(self, m):
        que, d = m.get("que"), m.get("v") or {}
        ident = m.get("id")
        pend = self.sv["veh_pend"].pop(ident, None) or {}
        if que == "no":
            self.sv["vehs"].pop(ident, None)
            self.sv.setdefault("mios", set()).discard(ident)
            self.app.son("error")
            self.decir(tr_servidor(str(m.get("motivo") or "")) or tr("No se ha podido."), True)
            return
        if d.get("id") is None:
            return
        v = self._sv_copia(d["id"])
        if que == "nombre":
            self.sv["vehs"][d["id"]] = d
            if v is not None:
                v.nombre = str(d.get("nombre") or v.nombre)[:40]
            self.app.son("menu_ok")
            self.decir(tr('Ahora se llama {get}.').format(get=(d.get('nombre'))), True)
        elif que == "traer":
            self.pagar(int(pend.get("precio", 0)))
            self.sv["vehs"][d["id"]] = d
            self.sv.setdefault("mios", set()).add(d["id"])
            if v is not None and v is not self.j.veh:
                v.x, v.y, v.vel, v.rumbo = float(d["x"]), float(d["y"]), 0.0, float(d.get("r", 0))
                v.dir = M.dir_de_rumbo(v.rumbo)
            elif v is None and d.get("m") == self.mundo.id:
                v = self._sv_crear_copia(d)
            if v is not None:
                v.red_dueno = True
                if self.j.veh is None:
                    self.ultimo_veh = v                          # Mayúsculas L y Servicios lo encuentran
                self.son(v.modelo.get("claxon", "claxon"), xy=(v.x, v.y))
                self.decir(tr('Tu mecánico te deja {nombre} en la calle. {situar}.').format(nombre=(v.nombre), situar=(self.situar(v.x, v.y, tr('Está')))), True)
                self.gps_tras_traer(v, v)                        # si el GPS te llevaba a él, ahora va adonde lo han dejado
        elif que == "garaje":
            casa = self.lug(m.get("ref") or pend.get("casa") or "")
            self.sv["vehs"].pop(d["id"], None)
            self.sv.setdefault("mios", set()).discard(d["id"])
            if v is not None and v is not self.j.veh:
                v.red_dueno = False
                self.quitar_vehiculo(v)
            if casa is None or d.get("modelo") not in self.modelos:
                return
            self.pagar(int(pend.get("precio", 0)))
            ficha = {"modelo": d["modelo"], "salud": float(d.get("salud") or self.modelos[d["modelo"]]["salud"]), "nombre": d.get("nombre") or self.modelos[d["modelo"]]["nombre"],
                     "mejoras": dict(d.get("mejoras") or {})}
            self.j.garajes.setdefault(casa.id, []).append(ficha)
            self.son("arranque", vol=0.6)
            self.decir(tr('Tu mecánico se lleva {nombre} al garaje de {nombre_lugar}.').format(nombre=(ficha['nombre']), nombre_lugar=(self.nombre_lugar(casa))), True)
            self.sv_guardar()                                    # ya no está en la calle del servidor: que conste en tu personaje cuanto antes

    def _svm_veh_ok(self, m):
        d = m.get("v") or {}
        if m.get("tr") is not None:                              # era un coche del tráfico: el conductor sale corriendo
            t = self.sv["trafico"].pop(m["tr"], None)
            if t is not None and not t.muerto:
                t.ia, t.ocupado, t.tr_id, t.id_red, t.red_mio = None, False, None, m["id"], False
                if getattr(t, "tr_poli", False):                 # una patrulla con los agentes fuera: nadie al volante
                    t.tr_poli, t.desplegado = False, False
                    if t.sirena is not None:
                        t.sirena.parar()
                        t.sirena = None
                    self.delito(3, tr("robo de un coche patrulla"), siempre=True)
                else:
                    c = Persona("civil", *self.mundo.punto_libre(t.x + 2, t.y + 2), nombre=tr("Conductor"))
                    c.estado, c.t_estado = "huye", 12
                    self.personas.append(c)
                    self.son("grito", xy=(c.x, c.y), tono=c.tono)
                    self.delito(2, tr("robo de vehículo con violencia"))
        v = self._sv_copia(m.get("id"))
        re = self.sv.get("reenganche")
        if re and re.get("id") == m.get("id") and v is not None and v is self.j.veh:
            # Es el vehículo en el que ibas cuando el servidor se fue: vuelve a ser tuyo, sin subirte otra vez ni contar
            # como robo. Si el servidor ha dado ese número a otro vehículo mientras tanto, no es este: se suelta y se da de alta.
            self.sv["reenganche"] = None
            if d.get("modelo") not in (None, v.modelo["id"]):
                self.red.enviar({"t": "veh_dejar", "id": m.get("id")})
                v.id_red, v.red_mio, v.red_ref = None, False, None
                self.sv_subido(v)
                return
            v.red_mio = True
            self.sv["vehs"].pop(v.id_red, None)
            return
        x, y = self.pos()
        if v is None:
            d = dict(d, x=x, y=y)
            v = self._sv_crear_copia(d)
            if v is None:
                return
        if m.get("asalto"):
            v.x, v.y = x, y
            self.son("grito", xy=(x, y), vol=0.6)
            self.decir(tr('Sacas a {asalto} del vehículo y te lo quedas.').format(asalto=(m['asalto'])))
            self.delito(2, tr("robo de vehículo con violencia"))
        elif m.get("robado"):
            self.delito(0.5, tr("robo de vehículo"))
        v.red_mio = True
        self.sv["vehs"].pop(v.id_red, None)
        self._subir(v, bool(m.get("robado")))

    def _svm_veh_no(self, m):
        re = self.sv.get("reenganche")
        if re and re.get("pedido") and re.get("id") == m.get("id"):
            return self._sv_reenganche_no(m)
        if m.get("motivo"):
            self.app.son("error")
            self.decir(tr_servidor(str(m["motivo"])), True)

    def _svm_sacado(self, m):
        v = self.j.veh
        if v is not None:
            v.red_mio = v.red_dueno = False
            self.salir_vehiculo(forzado=True)
            v.red_dueno = False
            self.quitar_vehiculo(v)
        self._sv_agresor(m.get("por"), str(m.get("nombre", "Alguien")))
        self.son("puerta_coche")
        self.decir(tr('¡{get} te saca del vehículo y se lo lleva!').format(get=(m.get('nombre', 'Alguien'))), True)

    def _svm_veh_golpe(self, m):
        if self.j.veh is not None and getattr(self.j.veh, "id_red", None) == m.get("id"):
            self._sv_agresor(m.get("de"), str(m.get("nombre", "Alguien")))
            self.danar_vehiculo(self.j.veh, float(m.get("n", 0)))

    def _svm_veh_salud(self, m):
        d = self.sv["vehs"].get(m.get("id"))
        if d is not None:
            d["salud"] = m.get("salud")
        v = self._sv_copia(m.get("id"))
        if v is not None:
            v.salud = min(v.salud_max, float(m.get("salud", v.salud)))
            self.son("bala_impacto", xy=(v.x, v.y), ref=10, maxd=150)

    def _svm_veh_revienta(self, m):
        self.sv["vehs"].pop(m.get("id"), None)
        self.sv.setdefault("mios", set()).discard(m.get("id"))
        v = self._sv_copia(m.get("id"))
        if v is not None and v is not self.j.veh:
            v.id_red = None
            self.explotar(v)
        elif m.get("m") == self.mundo.id:
            self.son("explosion", xy=(float(m.get("x", 0)), float(m.get("y", 0))), ref=30, maxd=400)

    def _svm_veh_fuera(self, m):
        self.sv["vehs"].pop(m.get("id"), None)
        self.sv.setdefault("mios", set()).discard(m.get("id"))
        v = self._sv_copia(m.get("id"))
        if v is not None and v is not self.j.veh:
            v.red_dueno = False
            self.quitar_vehiculo(v)

    # ------------------------------------------------------------------- bandas
    def _svm_banda(self, m):
        antes = self.sv["banda"]
        self.sv["banda"], self.sv["rango"] = m.get("b"), m.get("rango")
        if antes and not self.sv["banda"]:
            self.decir(tr("Ya no estás en ninguna banda."))
        elif self.sv["banda"] and not antes:
            self.son("territorio", cat="interfaz", vol=0.6)
            self.decir(tr('Estás en la banda {nombre}.').format(nombre=(self.sv['banda']['nombre'])))

    def _svm_banda_invita(self, m):
        self.sv["inv_banda"] = {"nombre": str(m.get("nombre", "")), "de": str(m.get("de", ""))}
        self.son("notificacion", cat="interfaz")
        self.decir(tr('{get} te invita a la banda {get2}. Abre el móvil con M, En línea, para aceptar o rechazar.').format(get=(m.get('de', 'Alguien')), get2=(m.get('nombre', ''))))

    def _svm_de_banda(self, m):
        r = self.remotos.get(m.get("id"))
        if r is not None:
            r.banda = m.get("banda")

    def _svm_territorios(self, m):
        self.sv["territorios"] = m.get("e") or {"barrios": [], "guerras": []}

    def _svm_bandas(self, m):
        self.sv["bandas"] = m.get("e") or []
        if m.get("territorios"):
            self.sv["territorios"] = m["territorios"]

    def sv_dueno_barrio(self, mapa, barrio):
        return next((t for t in self.sv["territorios"].get("barrios", []) if t["mapa"] == mapa and t["barrio"] == barrio), None)

    def sv_relacion(self, r):
        """Qué es para ti otro jugador: de tu banda, del grupo, o nada."""
        if self.sv["grupo"] is not None and any(q["id"] == r.id for q in self.sv["miembros"]):
            return tr("de tu grupo")
        b = self.sv["banda"]
        if b and getattr(r, "banda", None) == b["id"]:
            return tr("de tu banda")
        return ""

    # --------------------------------------------------------- misiones en grupo
    def _svm_grupo(self, m):
        antes = self.sv["grupo"]
        self.sv["grupo"], self.sv["miembros"] = m.get("lider"), m.get("miembros") or []
        if self.sv["grupo"] is None:
            self._sv_quitar_ecos()
            if antes is not None:
                self.decir(tr("El grupo se ha deshecho."))
        else:
            nombres = ", ".join(q["nombre"] for q in self.sv["miembros"] if q["id"] != self.red.id)
            self.decir(tr('Grupo de misión: vas con {nombres}.').format(nombres=(nombres)) + (tr(" Lo llevas tú: lo que consigas en tus misiones lo compartís.") if self.sv["grupo"] == self.red.id else ""))
            if self.sv["grupo"] == self.red.id and self.mision:
                self.sv_mision_paso()
                self.sv_mision_enemigos()

    def _svm_grupo_invita(self, m):
        g = self.sv.get("regrupo")
        if g and not g["lidero"] and g["lider"] and str(m.get("nombre", "")) == g["lider"] and self.sv.get("grupo") is None:
            # Es quien llevaba tu grupo antes de que el servidor se fuera, que lo está rehaciendo: se acepta sin preguntar.
            self.sv["regrupo"] = None
            self.red.enviar({"t": "grupo_resp", "si": True})
            self.decir(tr('{lider} rehace el grupo de misión y vuelves a él.').format(lider=(g['lider'])))
            return
        self.sv["inv_grupo"] = {"de": m.get("de"), "nombre": str(m.get("nombre", "")), "mision": str(m.get("mision", ""))}
        self.son("notificacion", cat="interfaz")
        self.decir(tr('{get} te invita a su grupo').format(get=(m.get('nombre', 'Alguien'))) + (tr(' para la misión {mision}').format(mision=(m['mision'])) if m.get("mision") else "")
                   + tr(". Abre el móvil con M, En línea, para aceptar o rechazar."))

    def _svm_paga_mision(self, m):
        n = max(0, int(m.get("n", 0)))
        self.j.dinero += n
        self.j.stats["dinero_ganado"] += n
        self.son("mision_ok", cat="interfaz")
        self.decir(tr('Misión completada con {get}: {get2}. Tu parte: {n} euros.').format(get=(m.get('de', tr('tu grupo'))), get2=(m.get('titulo', '')), n=(n)))
        self._sv_quitar_ecos()

    def sv_lidero(self):
        return self.en_servidor and self.sv["grupo"] is not None and self.sv["grupo"] == self.red.id

    def sv_mision_paso(self):
        """Quien lleva el grupo cuenta a los demás en qué paso está su misión y dónde es."""
        ms = self.mision
        if not self.sv_lidero() or not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return
        p = ms["def"]["pasos"][ms["paso"]]
        if p["tipo"] in ("dialogo", "dar", "decision"):
            return
        l = self.lugares.get(p.get("destino") or p.get("lugar") or "")
        self.red.enviar({"t": "grupo_msg", "d": {"que": "paso", "titulo": ms["def"]["titulo"], "texto": self.txt(p.get("texto", "")), "tipo": p["tipo"],
                                               "lugar": l.id if l else None}})

    def sv_mision_enemigos(self):
        """Los enemigos de tu misión pasan a ser de todo el grupo: lo que le quite uno, se lo quita para todos."""
        ms = self.mision
        if not self.sv_lidero() or not ms or not ms.get("enemigos"):
            return
        lista = []
        for k, e in enumerate(ms["enemigos"]):
            e.eco_k = k
            if not e.muerto:
                # deportivo (un rival del gimnasio: tumbarlo no es delito) y la puntería de su tipo viajan desde la 1.7.1
                lista.append({"k": k, "nombre": e.nombre, "salud": round(e.salud, 1), "arma": e.arma, "x": round(e.x, 1), "y": round(e.y, 1),
                              "inofensivo": bool(getattr(e, "inofensivo", False)), "deportivo": bool(getattr(e, "deportivo", False)),
                              "punteria": round(float(getattr(e, "punteria", 0) or 0), 2), "tono": round(float(getattr(e, "tono", 1.0) or 1.0), 2)})
        self.red.enviar({"t": "grupo_msg", "d": {"que": "enemigos", "mapa": self.mundo.id, "e": lista}})

    def sv_mision_fin(self, hecha, m=None):
        if not self.sv_lidero():
            return
        self.red.enviar({"t": "grupo_msg", "d": {"que": "fin", "hecha": bool(hecha), "titulo": (m or {}).get("titulo", "")}})
        if hecha and m is not None:
            self.red.enviar({"t": "mision_hecha", "id": m["id"]})

    def sv_golpe_eco(self, p, dano):
        """Has dado a un enemigo que es de todo el grupo: se lo cuentas a los demás."""
        if self.en_servidor and self.sv["grupo"] is not None and getattr(p, "eco_k", None) is not None and not getattr(self, "_sv_aplicando", False):
            self.red.enviar({"t": "grupo_msg", "d": {"que": "golpe", "k": p.eco_k, "dano": round(float(dano), 1)}})

    def _sv_quitar_ecos(self):
        for e in list(self.sv["ecos"].values()):
            if e in self.personas:
                self.personas.remove(e)
            if self.objetivo is e:
                self.objetivo = None
        self.sv["ecos"] = {}
        self.sv["mision_grupo"] = None

    def _svm_grupo_msg(self, m):
        d = m.get("d") or {}
        que = d.get("que")
        nombre = str(m.get("nombre", tr("tu compañero")))
        if que == "paso":
            self.sv["mision_grupo"] = {"titulo": str(d.get("titulo", "")), "texto": str(d.get("texto", "")), "lugar": d.get("lugar")}
            self.son("notificacion", cat="interfaz", vol=0.6)
            self.decir(tr('Misión de {nombre}, {get}: {get2}').format(nombre=(nombre), get=(d.get('titulo', '')), get2=(d.get('texto', ''))))
            l = self.lugares.get(d.get("lugar") or "")
            if l is not None and not self.mision and (self.gps is None or self.gps.get("grupo")):
                self.gps_a_lugar(l, callar=True)
                if self.gps:
                    self.gps["grupo"] = True
        elif que == "enemigos" and m.get("de") == self.sv["grupo"]:
            if d.get("mapa") != self.mundo.id:
                return
            nuevos = 0
            for q in d.get("e") or []:
                k = q.get("k")
                if k in self.sv["ecos"]:
                    continue
                x, y = self.mundo.punto_libre(float(q.get("x", self.j.x)), float(q.get("y", self.j.y)))
                e = Persona("enemigo", x, y, str(q.get("nombre", "Enemigo")))
                e.salud = float(q.get("salud", 60))
                e.arma = q.get("arma") if q.get("arma") in self.armas_d else "pistola"
                e.hostil, e.estado, e.tag = True, "ataca", "grupo"
                e.inofensivo = bool(q.get("inofensivo"))
                e.deportivo = bool(q.get("deportivo"))               # un juego anterior no lo manda: como hasta ahora
                try:
                    if float(q.get("punteria") or 0) > 0:
                        e.punteria = max(0.02, min(1.0, float(q["punteria"])))
                    if float(q.get("tono") or 0) > 0:
                        e.tono = max(0.5, min(2.0, float(q["tono"])))
                except (TypeError, ValueError):
                    pass
                e.eco_k = k
                e.t_disparo = 2.5
                self.personas.append(e)
                self.sv["ecos"][k] = e
                nuevos += 1
            if nuevos:
                self.decir(tr('Los enemigos de la misión de {nombre} son también tuyos: hay {nuevos}. Pulsa Q para fijar al más cercano.').format(nombre=(nombre), nuevos=(nuevos)))
        elif que == "golpe":
            k = d.get("k")
            e = self.sv["ecos"].get(k)
            if e is None and self.mision:
                e = next((x for x in self.mision.get("enemigos", []) if getattr(x, "eco_k", None) == k), None)
            if e is not None and not e.muerto:
                self._sv_aplicando = True                # este golpe viene de otro: no se vuelve a contar
                try:
                    self.danar_persona(e, float(d.get("dano", 0)))
                finally:
                    self._sv_aplicando = False
        elif que == "fin":
            self._sv_quitar_ecos()
            if self.gps and self.gps.get("grupo"):
                self.cancelar_gps()
            if not d.get("hecha"):
                self.decir(tr('La misión de {nombre} se ha quedado sin terminar.').format(nombre=(nombre)))

    def _sv_grupo_paso(self, dt):
        """Los enemigos del grupo que ya han caído se retiran de tu lista."""
        for k, e in list(self.sv["ecos"].items()):
            if e.muerto and self.t - e.t_estado > 20:
                if e in self.personas:
                    self.personas.remove(e)
                del self.sv["ecos"][k]
