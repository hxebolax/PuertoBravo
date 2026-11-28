"""Lógica del editor de mods, sin interfaz: cargar, guardar, convertir y comprobar un mod."""
from juego.i18n import tr
import copy
import json
import os
import re

from juego import mundo as M
from juego import cifrado
from juego import rutas

from .esquema import ESQUEMAS, SECCIONES

VACIOS = (None, "", [], {})


def desempaquetar(nombre_esq, crudo):
    """Convierte un dato tal como va en el archivo en su forma editable (todo listas y diccionarios planos)."""
    esq = ESQUEMAS[nombre_esq]
    d = {}
    conocidas = set()
    for cp in esq["campos"]:
        k = cp["k"]
        conocidas.add(k)
        if k not in crudo:
            continue
        v = crudo[k]
        if cp["t"] == "lista":
            sub = cp["sub"]
            if cp.get("como_dicc"):
                a, b = cp["como_dicc"]
                v = [{a: kk, b: vv} for kk, vv in (v or {}).items()]
            elif cp.get("como_pares"):
                a, b = cp["como_pares"]
                v = [{a: x[0], b: x[1]} for x in (v or []) if isinstance(x, (list, tuple)) and len(x) >= 2]
            elif cp.get("como_bloques"):
                lista = []
                for kk, vv in (v or {}).items():
                    try:
                        i, j = kk.split(",")
                        lista.append({"i": int(i), "j": int(j), "tipo": vv})
                    except ValueError:
                        pass
                v = lista
            else:
                v = [desempaquetar(sub, x) for x in (v or []) if isinstance(x, dict)]
        elif cp["t"] == "objeto":
            v = desempaquetar(cp["sub"], v) if isinstance(v, dict) else {}
        d[k] = copy.deepcopy(v)
    extra = {k: copy.deepcopy(v) for k, v in crudo.items() if k not in conocidas}
    if extra:
        d["_extra"] = extra          # claves que el editor no conoce: se conservan tal cual
    return d


def empaquetar(nombre_esq, d):
    """Convierte la forma editable en el dato que se guarda en el archivo. Omite lo que está vacío."""
    esq = ESQUEMAS[nombre_esq]
    crudo = {}
    for cp in esq["campos"]:
        k = cp["k"]
        if k not in d:
            continue
        v = d[k]
        if cp["t"] == "lista":
            sub = cp["sub"]
            if cp.get("como_dicc"):
                a, b = cp["como_dicc"]
                v = {str(x.get(a)): x.get(b) for x in v if x.get(a) not in VACIOS}
            elif cp.get("como_pares"):
                a, b = cp["como_pares"]
                v = [[x.get(a), x.get(b)] for x in v]
            elif cp.get("como_bloques"):
                v = {f"{int(x.get('i', 0))},{int(x.get('j', 0))}": x.get("tipo", "plaza") for x in v}
            else:
                v = [empaquetar(sub, x) for x in v]
        elif cp["t"] == "objeto":
            v = empaquetar(cp["sub"], v) if isinstance(v, dict) else {}
        if v in VACIOS:
            continue
        if v is False and cp.get("defecto") is not True:
            continue
        crudo[k] = v
    crudo.update(d.get("_extra", {}))
    return crudo


def nuevo_elemento(nombre_esq):
    """Elemento nuevo con los valores por defecto del esquema."""
    d = {}
    for cp in ESQUEMAS[nombre_esq]["campos"]:
        if "defecto" in cp:
            d[cp["k"]] = copy.deepcopy(cp["defecto"])
    return d


def resumen(nombre_esq, d):
    f = ESQUEMAS[nombre_esq].get("resumen")
    try:
        return f(d) if f else ESQUEMAS[nombre_esq]["titulo"]
    except Exception:
        return ESQUEMAS[nombre_esq]["titulo"]



def _localidades(b):
    """Los mapas del juego que son localidades: el pabellón de los combates del gimnasio (tipo recinto) no lo es, y no
    se ofrece para poner cosas en él."""
    return [m for m in b["mapas"] if m.get("tipo") != "recinto"]

class Mod:
    """Un mod en edición. Internamente todo está en forma editable."""

    def __init__(self):
        self.ruta = None
        self.modificado = False
        self.info = {"nombre": tr("Mi mod"), "version": "1.0"}
        self.secciones = {clave: [] for clave, _, _ in SECCIONES}
        self.extra = {}

    @classmethod
    def desde_crudo(cls, crudo):
        m = cls()
        m.info = desempaquetar("info", crudo.get("info", {})) or {"nombre": tr("Mi mod")}
        for clave, _, esq in SECCIONES:
            v = crudo.get(clave, [])
            if clave == "capitulos":
                m.secciones[clave] = [{"clave": k, "valor": t} for k, t in (v or {}).items()]
            else:
                m.secciones[clave] = [desempaquetar(esq, x) for x in v if isinstance(x, dict)]
        conocidas = {"info"} | {c for c, _, _ in SECCIONES}
        m.extra = {k: v for k, v in crudo.items() if k not in conocidas}
        return m

    @classmethod
    def cargar(cls, ruta):
        crudo = cifrado.leer_json(ruta)              # abre igual los mods protegidos que los escritos a mano
        if not isinstance(crudo, dict):
            raise ValueError(tr("El archivo no contiene un mod: debe ser un objeto JSON."))
        m = cls.desde_crudo(crudo)
        m.ruta = ruta
        return m

    def crudo(self):
        out = {"info": empaquetar("info", self.info)}
        for clave, _, esq in SECCIONES:
            items = self.secciones.get(clave, [])
            if not items:
                continue
            if clave == "capitulos":
                out[clave] = {str(x.get("clave")): x.get("valor", "") for x in items if x.get("clave") not in VACIOS}
            else:
                out[clave] = [empaquetar(esq, x) for x in items]
        out.update(self.extra)
        return out

    def guardar(self, ruta=None, protegido=True):
        """Guarda el mod. Desde el editor siempre queda protegido, con extensión .pbm: no se puede retocar
        con un editor de texto. Si el mod venía de un .json escrito a mano, ese archivo se aparta como
        .json.original para que el juego no cargue las dos versiones. Devuelve el archivo apartado, o None."""
        ruta = ruta or self.ruta
        apartado = None
        if protegido:
            destino = ruta_protegida(ruta)
            cifrado.escribir_json(destino, self.crudo(), cifrado=True)
            if os.path.normcase(destino) != os.path.normcase(ruta) and os.path.exists(ruta) and not cifrado.esta_cifrado(ruta):
                apartado = ruta + ".original"
                os.replace(ruta, apartado)
            elif os.path.normcase(destino) != os.path.normcase(ruta) and os.path.exists(ruta):
                os.remove(ruta)                   # un .json ya protegido, de una versión anterior: queda solo el .pbm
            ruta = destino
        else:
            cifrado.escribir_json(ruta, self.crudo(), cifrado=False, sangria=1)
        self.ruta = ruta
        self.modificado = False
        return apartado


class Catalogo:
    """Todo lo que existe (en el juego y en el mod), para ofrecerlo en los desplegables y comprobar referencias."""

    def __init__(self, base=None):
        self.base = base or M.cargar_datos(con_mods=False, traducir=False)
        self.refrescar_sonidos()

    def refrescar_sonidos(self):
        """Los sonidos que se pueden elegir: los del juego y los propios de los mods (data/mods/sonidos)."""
        try:
            self.sonidos = sorted({os.path.splitext(f)[0] for f in os.listdir(rutas.SONIDOS) if os.path.splitext(f)[1].lower() in rutas.EXT_AUDIO})
        except OSError:
            self.sonidos = []
        if not self.sonidos:
            from juego import sintesis
            self.sonidos = sorted(sintesis.generar())
        self.sonidos_mods = sonidos_de_mods()
        self.sonidos = sorted(set(self.sonidos) | set(self.sonidos_mods))

    def opciones(self, ref, mod=None):
        """Lista de (identificador, texto) para un tipo de referencia."""
        b = self.base
        sec = mod.secciones if mod else {}
        if ref == "sonido":
            return [(s, s) for s in self.sonidos]
        if ref == "agua":
            from juego.extras import AGUAS
            return list(AGUAS)
        if ref == "habilidad":
            return [("conduccion", tr("Conducción")), ("punteria", tr("Puntería")), ("resistencia", tr("Resistencia")), ("pesca", tr("Pesca"))]
        if ref == "vendible":                                    # lo que una tienda puede vender además de comida
            out = {o["id"]: str(o.get("nombre", o["id"])) for o in b.get("objetos", []) if o.get("id") in ("botiquin", "ganzua", "walkman", "pienso")}
            for a in list(b.get("armas", [])) + list(sec.get("armas", [])):
                if a.get("id") and a.get("donde") == "tienda":
                    out[a["id"]] = str(a.get("nombre", a["id"]))
            return sorted(out.items(), key=lambda e: e[1].lower())
        if ref == "mapa":
            out = [(m["id"], m["nombre"]) for m in _localidades(b)]
            return out + [(m.get("id"), m.get("nombre", m.get("id"))) for m in sec.get("mapas", []) if m.get("id") and m.get("id") not in dict(out)]
        if ref == "lugar":
            out = {}
            nombres = {m["id"]: m["nombre"] for m in b["mapas"]}
            for m in _localidades(b):
                for l in m.get("lugares", []):
                    out[l["id"]] = tr('{nombre}, en {nombre2}').format(nombre=(l['nombre']), nombre2=(m['nombre']))
            for m in sec.get("mapas", []):
                nombres[m.get("id")] = m.get("nombre", m.get("id"))
                for l in m.get("lugares", []):
                    if l.get("id"):
                        out[l["id"]] = tr('{get}, en {get2}, del mod').format(get=(l.get('nombre', l['id'])), get2=(m.get('nombre', '')))
            for l in sec.get("lugares", []):
                if l.get("id"):
                    out[l["id"]] = tr('{get}, en {get2}, del mod').format(get=(l.get('nombre', l['id'])), get2=(nombres.get(l.get('mapa', 'puerto_bravo'), l.get('mapa', ''))))
            return sorted(out.items(), key=lambda e: e[1].lower())
        tabla = {"modelo": ("vehiculos", b["vehiculos"]), "arma": ("armas", b["armas"]), "mision": ("misiones", b["misiones"]),
                 "tipo_enemigo": ("tipos_enemigo", b.get("tipos_enemigo", [])),
                 "titulo_estudios": ("titulos", b.get("titulos", [])), "objeto": ("objetos", b.get("objetos", [])),
                 "producto": ("productos", b.get("productos", [])), "pasillo": ("pasillos", b.get("pasillos", [])), "tipo_tienda": ("tipos_tienda", b.get("tipos_tienda", [])),
                 "carta": ("cartas", b.get("cartas", [])), "suceso": ("sucesos", b.get("sucesos", [])),
                 "sustancia": ("sustancias", b["adultos"].get("sustancias", [])), "persona": ("personas", b["adultos"].get("personas", [])),
                 "actividad": ("actividades", b["adultos"].get("actividades", [])), "regalo": ("regalos", b["adultos"].get("regalos", []))}
        if ref in tabla:
            clave, lista = tabla[ref]
            campo = "titulo" if ref == "mision" else "nombre"
            out = {x["id"]: str(x.get(campo, x["id"])) for x in lista}
            for x in sec.get(clave, []):
                if x.get("id"):
                    out[x["id"]] = str(x.get(campo, x["id"])) + tr(", del mod")
            return sorted(out.items(), key=lambda e: e[1].lower())
        return []

    def elementos_base(self, clave):
        """Elementos originales del juego de una sección, para copiarlos al mod y modificarlos."""
        b = self.base
        if clave == "lugares":
            out = []
            for m in _localidades(b):
                for l in m.get("lugares", []):
                    x = dict(l)
                    x["mapa"] = m["id"]
                    out.append(x)
            return out
        if clave in ("personas", "sustancias", "actividades", "regalos"):
            return list(b["adultos"].get(clave, []))
        if clave == "capitulos":
            return [{"clave": k, "valor": v} for k, v in b["capitulos"].items()]
        if clave == "mapas":
            return list(_localidades(b))
        if clave == "personajes":
            return list(b.get("personajes", []))
        return list(b.get(clave, []))


def sonidos_de_mods():
    """Los nombres de los sonidos propios de los mods, en data/mods/sonidos."""
    try:
        return sorted({os.path.splitext(f)[0] for f in os.listdir(rutas.SONIDOS_MODS) if os.path.splitext(f)[1].lower() in rutas.EXT_AUDIO})
    except OSError:
        return []


def anadir_sonido(origen, sonidos_del_juego=()):
    """Copia un archivo de sonido a data/mods/sonidos para usarlo en un mod. El nombre queda en minúsculas, sin tildes ni
    espacios; si coincide con un sonido del juego, lleva «mod_» delante (el juego nunca deja que un mod sustituya uno
    suyo). Devuelve el nombre con el que se elige en el editor."""
    import shutil
    import unicodedata
    base, ext = os.path.splitext(os.path.basename(origen))
    if ext.lower() not in rutas.EXT_AUDIO:
        raise ValueError(tr("Ese archivo no es un sonido que el juego sepa leer: valen WAV, OGG, FLAC y MP3."))
    nombre = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode("ascii").lower()
    nombre = re.sub(r"[^a-z0-9]+", "_", nombre).strip("_") or "sonido"
    if nombre in set(sonidos_del_juego):
        nombre = "mod_" + nombre
    os.makedirs(rutas.SONIDOS_MODS, exist_ok=True)
    for viejo in os.listdir(rutas.SONIDOS_MODS):                # el mismo nombre con otra extensión, fuera
        if os.path.splitext(viejo)[0] == nombre:
            os.remove(os.path.join(rutas.SONIDOS_MODS, viejo))
    shutil.copyfile(origen, os.path.join(rutas.SONIDOS_MODS, nombre + ext.lower()))
    return nombre


def pista_mapa(v, mod):
    """Por qué puede no existir una localidad a la que apunta algo del mod, y cómo arreglarlo, para el mensaje de F5 y F9."""
    sec = mod.secciones if mod else {}
    v = str(v)
    for m in sec.get("mapas", []):
        if str(m.get("nombre", "")).strip().lower() == v.strip().lower() and m.get("id") != v:
            return " " + tr('Es el nombre de tu localidad, no su identificador, que es «{id}». Vuelve a elegirla en ese campo.').format(id=m.get("id"))
    try:
        from juego import gestor_mods, mundo as JM
        for nombre, activo in gestor_mods.listar():
            if mod is not None and getattr(mod, "ruta", None) and os.path.basename(str(mod.ruta)) == nombre:
                continue
            otro = JM._leer_json(os.path.join(rutas.MODS, nombre))
            if any(isinstance(m, dict) and m.get("id") == v for m in otro.get("mapas", [])):
                return " " + tr('Esa localidad está en otro mod, {nombre}. Los lugares que llevan a ella tienen que ir en el mismo mod que la localidad: pásalos a ese mod, o la localidad a este.').format(nombre=nombre)
    except Exception:
        pass
    return " " + tr("Si le has cambiado el identificador a la localidad, o la has borrado y vuelto a crear, vuelve a elegirla en ese campo. "
                    "Una localidad nueva cuenta en cuanto la aceptas en su ventana y guardas el mod.")


def renombrar_referencias_mapa(mod, viejo, nuevo):
    """Una localidad del mod cambia de identificador: todo lo del mod que apuntaba a ella pasa a apuntar al nuevo
    (lugares, sus salidas, carreras y el mapa aéreo). Devuelve cuántas referencias ha cambiado."""
    if not mod or not viejo or not nuevo or viejo == nuevo:
        return 0
    n = 0
    sec = mod.secciones

    def cambiar(d, claves):
        nonlocal n
        for k in claves:
            if isinstance(d, dict) and d.get(k) == viejo:
                d[k] = nuevo
                n += 1
    for l in sec.get("lugares", []):
        cambiar(l, ("mapa", "a_mapa"))
    for m in sec.get("mapas", []):
        for l in m.get("lugares", []) or []:
            cambiar(l, ("mapa", "a_mapa"))
    for c in sec.get("carreras", []):
        cambiar(c, ("mapa",))
    for a in sec.get("mapa_aire", []):
        cambiar(a, ("mapa", "id", "destino"))
    return n


# ================================================================== comprobación
def _recorrer(nombre_esq, d, cat, mod, donde, errores, avisos):
    esq = ESQUEMAS[nombre_esq]
    for cp in esq["campos"]:
        k, t = cp["k"], cp["t"]
        visible = cp.get("si") is None or cp["si"](d)
        v = d.get(k)
        if not visible:
            continue
        if cp.get("req") and v in VACIOS:
            errores.append(tr('{donde}: falta «{e}».').format(donde=(donde), e=(cp['e'])))
            continue
        if v in VACIOS:
            continue
        if t in ("entero", "decimal"):
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                errores.append(tr('{donde}: «{e}» tiene que ser un número.').format(donde=(donde), e=(cp['e'])))
            else:
                if "minimo" in cp and v < cp["minimo"]:
                    errores.append(tr('{donde}: «{e}» no puede ser menor que {minimo}.').format(donde=(donde), e=(cp['e']), minimo=(cp['minimo'])))
                if "maximo" in cp and v > cp["maximo"]:
                    errores.append(tr('{donde}: «{e}» no puede ser mayor que {maximo}.').format(donde=(donde), e=(cp['e']), maximo=(cp['maximo'])))
        elif t == "opcion":
            if v not in [o[0] for o in cp["ops"]]:
                errores.append(tr('{donde}: «{e}» tiene un valor desconocido: {v}.').format(donde=(donde), e=(cp['e']), v=(v)))
        elif t == "ref":
            if v not in dict(cat.opciones(cp["ref"], mod)):
                errores.append(tr('{donde}: «{e}» apunta a «{v}», que no existe.').format(donde=(donde), e=(cp['e']), v=(v))
                               + (pista_mapa(v, mod) if cp["ref"] == "mapa" else ""))
        elif t == "refs":
            validos = dict(cat.opciones(cp["ref"], mod))
            for x in v:
                if x not in validos:
                    errores.append(tr('{donde}: «{e}» incluye «{x}», que no existe.').format(donde=(donde), e=(cp['e']), x=(x)))
        elif t == "lista":
            for n, x in enumerate(v, 1):
                _recorrer(cp["sub"], x, cat, mod, tr('{donde}, {lower}, elemento {n}').format(donde=(donde), lower=(cp['e'].lower()), n=(n)), errores, avisos)
        elif t == "objeto":
            _recorrer(cp["sub"], v, cat, mod, f"{donde}, {cp['e'].lower()}", errores, avisos)


def _mapa_crudo(cat, mod, ident):
    for m in mod.secciones.get("mapas", []):
        if m.get("id") == ident:
            return empaquetar("mapa", m)
    return next((copy.deepcopy(m) for m in cat.base["mapas"] if m["id"] == ident), None)


def _comprobar_tranvia(mod, m, crudo, mm, donde, errores, avisos):
    """Las vías del tranvía: los cruces tienen que existir, y las paradas quedar cerca de las vías."""
    import math
    eje, n = crudo.get("tren_eje"), crudo.get("tren_n")
    if eje in ("H", "V"):
        tope = (mm.NY if eje == "H" else mm.NX) - 1
        if not isinstance(n, int) or isinstance(n, bool) or not (0 <= n <= tope):
            errores.append(tr('{donde}: la vía del tren va por una {v} que no existe. Tiene que ser un número de 0 a {tope}.').format(donde=(donde), v=(tr('calle') if eje == 'H' else tr('avenida')), tope=(tope)))
        elif not any(l.tipo == "tren" for l in mm.lugares_todos.values()) and crudo.get("transporte") is False:
            avisos.append(tr('{donde}: tiene vía del tren pero no estación de tren: sin estación, no pasa ningún tren.').format(donde=(donde)))
    elif n is not None and eje is None:
        avisos.append(tr('{donde}: la vía del tren tiene número pero no dice si va por una calle o por una avenida; el juego la pondrá delante de la estación.').format(donde=(donde)))
    for n, cruce in enumerate(crudo.get("vias") or [], 1):
        try:
            i, j = (cruce["a"], cruce["b"]) if isinstance(cruce, dict) else (cruce[0], cruce[1])
            if not (0 <= int(i) < mm.NX and 0 <= int(j) < mm.NY):
                errores.append(tr('{donde}: el cruce {n} de las vías, avenida {i} y calle {v}, no existe. Las avenidas van de 0 a {v2} y las calles de 0 a {v3}.').format(donde=(donde), n=(n), i=(i), v=(j), v2=(mm.NX - 1), v3=(mm.NY - 1)))
        except (KeyError, IndexError, TypeError, ValueError):
            errores.append(tr('{donde}: el cruce {n} de las vías no tiene avenida y calle.').format(donde=(donde), n=(n)))
    paradas = [empaquetar("lugar", l) for l in mod.secciones.get("lugares", []) if l.get("mapa") == m.get("id") and l.get("tipo") == "tranvia"]
    paradas += [l for l in crudo.get("lugares", []) if l.get("tipo") == "tranvia"]
    if not paradas:
        return
    if len(paradas) == 1:
        avisos.append(tr('{donde}: solo hay una parada de tranvía; hacen falta al menos dos para que haya línea.').format(donde=(donde)))
    ordenes = [l.get("orden") for l in paradas if l.get("orden") is not None]
    if ordenes and len(ordenes) != len(paradas):
        avisos.append(tr('{donde}: unas paradas de tranvía tienen orden en la línea y otras no; el juego las ordenará él, dando la vuelta a la ciudad.').format(donde=(donde)))
    if len(set(ordenes)) != len(ordenes):
        avisos.append(tr('{donde}: hay paradas de tranvía con el mismo orden en la línea.').format(donde=(donde)))
    try:
        c2 = dict(crudo)
        c2["lugares"] = [{k: v for k, v in l.items() if k != "mapa"} for l in paradas]
        c2["transporte"] = False
        m2 = M.Mundo(c2)
        for l in m2.linea_tranvia():
            s = m2.via_marca(l)
            if s is not None:
                px, py = m2.via_punto(s)
                lejos = math.hypot(px - l.x, py - l.y)
                if lejos > 60:
                    avisos.append(tr('{donde}: la parada «{nombre}» queda a {int} metros de las vías; el tranvía parará lejos de ella.').format(donde=(donde), nombre=(l.nombre), int=(int(lejos))))
    except Exception:
        pass


def comprobar(mod, cat):
    """Revisa el mod entero. Devuelve (errores, avisos), listas de frases."""
    errores, avisos = [], []
    for clave, titulo, esq in SECCIONES:
        vistos = set()
        for d in mod.secciones.get(clave, []):
            ident = d.get("id") or d.get("clave") or d.get("nombre") or tr("sin nombre")
            donde = f"{titulo}, «{ident}»"
            if "id" in [cp["k"] for cp in ESQUEMAS[esq]["campos"]]:
                if d.get("id") in vistos:
                    errores.append(tr('{donde}: el identificador está repetido dentro del mod.').format(donde=(donde)))
                vistos.add(d.get("id"))
                if d.get("id") and not re.fullmatch(r"[a-z0-9_]+", str(d["id"])):
                    avisos.append(tr('{donde}: conviene que el identificador solo tenga minúsculas, números y guiones bajos.').format(donde=(donde)))
            _recorrer(esq, d, cat, mod, donde, errores, avisos)
    # un vehículo sin precio no se vende en ningún sitio: quien lo crea suele esperar poder comprarlo
    otros = {k: v for k, v in mod.secciones.items() if k != "vehiculos"}
    usados = json.dumps(otros, ensure_ascii=False)                  # si el mod lo usa en una misión, un barrio o un lugar, no es para venderse
    for d in mod.secciones.get("vehiculos", []):
        if not d.get("precio") and not d.get("vuela") and f'"{d.get("id")}"' not in usados:
            avisos.append(tr('Vehículos, «{ident}»: no tiene precio, así que no se vende en ningún concesionario ni náutica y el jugador no podrá comprarlo. '
                             'Ponle un precio para que salga en todos los que no limitan sus modelos.').format(ident=d.get("id") or d.get("nombre") or tr("sin nombre")))
    # mapas: tienen que poder construirse
    for m in mod.secciones.get("mapas", []):
        donde = tr('Localidades y mapas, «{get}»').format(get=(m.get('id', tr('sin nombre'))))
        crudo = empaquetar("mapa", m)
        crudo.setdefault("lugares", [])
        try:
            if crudo.get("tipo") == "mar":
                M.Mar(crudo)
            else:
                if len(crudo.get("avenidas", [])) < 2 or len(crudo.get("calles", [])) < 2:
                    errores.append(tr('{donde}: hacen falta al menos dos avenidas y dos calles.').format(donde=(donde)))
                    continue
                if not crudo.get("barrios"):
                    errores.append(tr('{donde}: hace falta al menos un barrio.').format(donde=(donde)))
                    continue
                mm = M.Mundo(dict(crudo, transporte=False, lugares=list(crudo["lugares"])))      # al revisar no se añade nada: se mira lo que hay
                for bi in range(mm.NX - 1):
                    for bj in range(mm.NY - 1):
                        if (bi, bj) not in mm._barrio_de:
                            avisos.append(tr('{donde}: la manzana {bi}, {bj} no pertenece a ningún barrio; usará el primero.').format(donde=(donde), bi=(bi), bj=(bj)))
                _comprobar_tranvia(mod, m, crudo, mm, donde, errores, avisos)
        except Exception as e:
            errores.append(tr('{donde}: no se puede construir el mapa: {e}').format(donde=(donde), e=(e)))
    # lugares: su posición tiene que existir y poder pisarse
    lugares = [(l, l.get("mapa", "puerto_bravo")) for l in mod.secciones.get("lugares", [])]
    for m in mod.secciones.get("mapas", []):
        lugares += [(l, m.get("id")) for l in m.get("lugares", [])]
    for l, mapa_id in lugares:
        donde = tr('Lugares, «{get}»').format(get=(l.get('id', tr('sin nombre'))))
        crudo = _mapa_crudo(cat, mod, mapa_id)
        if crudo is None:
            continue
        lc = empaquetar("lugar", l)
        lc.pop("mapa", None)
        try:
            crudo = dict(crudo)
            crudo["lugares"] = []
            crudo["casetes"] = []
            mm = M.Mar(crudo) if crudo.get("tipo") == "mar" else M.Mundo(crudo)
            if mm.tipo == "mar":
                if "xy" not in lc:
                    errores.append(tr('{donde}: en el mar hay que indicar la posición con coordenadas.').format(donde=(donde)))
                    continue
            else:
                if "bloque" not in lc:
                    errores.append(tr('{donde}: falta la manzana.').format(donde=(donde)))
                    continue
                bi, bj = lc["bloque"]
                if not (0 <= bi < mm.NX - 1 and 0 <= bj < mm.NY - 1):
                    errores.append(tr('{donde}: la manzana {bi}, {bj} no existe en {nombre}. Hay {v} de oeste a este y {v2} de sur a norte.').format(donde=(donde), bi=(bi), bj=(bj), nombre=(mm.nombre), v=(mm.NX - 1), v2=(mm.NY - 1)))
                    continue
                if "xy" not in lc and "lado" not in lc:
                    errores.append(tr('{donde}: indica la fachada o una posición interior.').format(donde=(donde)))
                    continue
            lug = M.Lugar(lc, mm)
            if mm.tipo == "mar":
                if mm.superficie(lug.x, lug.y) != "agua":
                    errores.append(tr('{donde}: esa posición no es agua navegable.').format(donde=(donde)))
            elif not mm.transitable(lug.x, lug.y):
                errores.append(tr('{donde}: la posición cae dentro de un edificio. Una posición interior solo vale en plazas, parques, playas y muelles.').format(donde=(donde)))
        except Exception as e:
            errores.append(tr('{donde}: posición incorrecta: {e}').format(donde=(donde), e=(e)))
    # misiones: coherencia de los pasos
    for mi in mod.secciones.get("misiones", []):
        donde = tr('Misiones, «{get}»').format(get=(mi.get('id', tr('sin nombre'))))
        hay_vehiculo = False
        for n, p in enumerate(mi.get("pasos", []), 1):
            t = p.get("tipo")
            if t == "robar":
                hay_vehiculo = True
            if t == "entregar" and not hay_vehiculo:
                errores.append(tr('{donde}, paso {n}: para entregar un vehículo hace falta antes un paso de conseguirlo.').format(donde=(donde), n=(n)))
            if t == "dialogo" and not p.get("lineas"):
                errores.append(tr('{donde}, paso {n}: el diálogo no tiene frases.').format(donde=(donde), n=(n)))
            if t == "eliminar" and not p.get("enemigos"):
                errores.append(tr('{donde}, paso {n}: no hay enemigos que eliminar.').format(donde=(donde), n=(n)))
            for k, g in enumerate(p.get("enemigos") or [] if t == "eliminar" else [], 1):
                if not g.get("clase") and not (g.get("tipo") and g.get("arma")):
                    errores.append(tr('{donde}, paso {n}, grupo de enemigos {k}: elige un tipo de enemigo, o escribe su nombre y su arma.').format(donde=(donde), n=(n), k=(k)))
            if t in ("ir", "robar", "entregar", "eliminar", "perseguir", "seguir", "escoltar", "sigilo", "vigilar", "carrera") and not p.get("lugar"):
                errores.append(tr('{donde}, paso {n}: falta el lugar.').format(donde=(donde), n=(n)))
            if t in ("seguir", "escoltar") and not p.get("destino"):
                errores.append(tr('{donde}, paso {n}: falta el lugar de destino.').format(donde=(donde), n=(n)))
            if t == "decision" and len(p.get("opciones") or []) < 2:
                errores.append(tr('{donde}, paso {n}: una decisión necesita al menos dos opciones.').format(donde=(donde), n=(n)))
            if t == "decision" and not p.get("clave"):
                avisos.append(tr('{donde}, paso {n}: la decisión no tiene nombre; ninguna misión podrá depender de ella.').format(donde=(donde), n=(n)))
            if t == "carrera" and not p.get("puntos"):
                errores.append(tr('{donde}, paso {n}: una carrera necesita al menos un lugar de paso, que hace de meta.').format(donde=(donde), n=(n)))
            if t == "ruta" and len(p.get("puntos") or []) < 2:
                errores.append(tr('{donde}, paso {n}: una ruta necesita al menos dos lugares.').format(donde=(donde), n=(n)))
            if t == "recoger" and not p.get("lugar") and not p.get("aqui"):
                errores.append(tr('{donde}, paso {n}: indica un lugar o marca que el objeto aparece donde esté el jugador.').format(donde=(donde), n=(n)))
            if t == "recoger" and not p.get("objeto"):
                errores.append(tr('{donde}, paso {n}: falta el nombre del objeto.').format(donde=(donde), n=(n)))
            if t in ("robar", "perseguir") and not p.get("modelo"):
                errores.append(tr('{donde}, paso {n}: falta el modelo de vehículo.').format(donde=(donde), n=(n)))
            if t not in ("dialogo", "dar", "decision") and not p.get("texto"):
                avisos.append(tr('{donde}, paso {n}: no tiene texto; el jugador no sabrá qué hacer.').format(donde=(donde), n=(n)))
        if mi.get("id") in (mi.get("requiere") or []):
            errores.append(tr('{donde}: no puede exigirse a sí misma.').format(donde=(donde)))
    for pe in mod.secciones.get("personas", []):
        if isinstance(pe.get("edad"), (int, float)) and pe["edad"] < 18:
            errores.append(tr('Personas, «{get}»: tiene que ser una persona adulta, de 18 años o más.').format(get=(pe.get('id', ''))))
    return errores, avisos


EXT_MODS = (".json", rutas.EXT_MOD)


def ruta_protegida(ruta):
    """Nombre con el que el editor guarda un mod: siempre .pbm (o .pbm.desactivado)."""
    baja = ruta.lower()
    if baja.endswith(".json.desactivado"):
        return ruta[:-len(".json.desactivado")] + rutas.EXT_MOD + ".desactivado"
    if baja.endswith(".json"):
        return ruta[:-5] + rutas.EXT_MOD
    if baja.endswith((rutas.EXT_MOD, rutas.EXT_MOD + ".desactivado")):
        return ruta
    return ruta + rutas.EXT_MOD


def listar_mods():
    """[(nombre de archivo, activo)] de la carpeta de mods. Lo mismo que Opciones, Mods del juego (juego/gestor_mods.py)."""
    from juego import gestor_mods
    return gestor_mods.listar()


def activar_mod(nombre, activo):
    from juego import gestor_mods
    return gestor_mods.activar(nombre, activo)
