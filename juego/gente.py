"""Gente de la calle, bandas, tipos de enemigo, policía por nivel de búsqueda y caja de los locales.

Todo sale de los datos del juego (data/datos/gente.json), que un mod puede ampliar o cambiar con el editor:

- gente: las listas de nombres, apellidos, oficios, frases, apodos, nombres de perro y demás. Un mod añade a ellas o,
  si lo pide, las sustituye.
- caracteres: cómo es cada forma de ser de la gente con la que hablas.
- bandas: las bandas de la comarca y con qué tipos de enemigo pelean.
- tipos_enemigo: el catálogo de enemigos: nombre, arma, salud, puntería, si va a pie o en qué vehículo, frases y voz.
- policia_niveles: qué tipo de agente sale con cada nivel de búsqueda.
- cajas_locales: cuánto hay en la caja de cada tipo de local y quién la guarda.

Lo que hay aquí escrito es solo lo mínimo para que el juego funcione si esos datos faltan (unos datos antiguos, o un
mod que deja una lista vacía): entonces se usa esto.
"""
from .i18n import tr
import random

SECCIONES = ("gente", "caracteres", "bandas", "tipos_enemigo", "policia_niveles", "cajas_locales")
LISTAS = ("nombres_h", "nombres_m", "apellidos", "frases", "apodos", "perros", "bandas_propias", "rivales_carrera", "nombres_servidor",
          # lo que dicen los personajes de un servidor en línea, según su clase; sin ellas, el servidor usa las suyas
          "frases_servidor_paseante", "frases_servidor_ratero", "frases_servidor_pistolero", "frases_servidor_ladron", "frases_servidor_atracador",
          # frases ya escritas para el chat y los canales de rol: para quien juega con mando, o no quiere escribir
          "frases_chat", "rol_frases_ic", "rol_frases_yo", "rol_frases_ooc")
PUNTERIA = 0.42                   # la de un enemigo corriente: lo que acierta a quemarropa
HABLAS = ("amable", "hablador", "seco", "timido", "chulo")      # los caracteres para los que el juego trae frases escritas

_SERIE = {
    "nombres_h": [tr("Antonio"), tr("Manolo"), tr("Paco"), tr("Javi"), tr("Luis"), tr("Rafa")], "nombres_m": [tr("Carmen"), tr("Lola"), tr("Pilar"), tr("Marta"), tr("Lucía"), tr("Rosa")],
    "apellidos": [tr("Mora"), tr("Salas"), tr("Cano"), tr("Vidal")], "frases": [tr("Buenos días."), tr("Perdona, llevo prisa."), tr("Qué calor hace hoy.")],
    "apodos": [tr("el Chato"), tr("la Culebra"), tr("el Rubio"), tr("la Tuerta")], "perros": [tr("Canela"), tr("Trufa"), tr("Rayo"), tr("Luna")],
    "bandas_propias": [tr("Los del Puerto"), tr("La Cuadrilla")], "rivales_carrera": [tr("el coche rojo"), tr("el coche negro"), tr("la furgoneta blanca"), tr("el deportivo amarillo")],
    "nombres_servidor": [],
    "frases_chat": [tr("Hola a todos."), tr("¿Dónde estáis?"), tr("Voy para allá."), tr("Gracias."), tr("Hasta luego.")],
    "rol_frases_ic": [tr("Buenas."), tr("¿Qué tal todo?"), tr("Sígueme."), tr("Espera un momento."), tr("Gracias."), tr("Hasta luego.")],
    "rol_frases_yo": [tr("saluda con la mano"), "asiente", tr("niega con la cabeza"), tr("mira alrededor"), tr("se encoge de hombros")],
    "rol_frases_ooc": [tr("Hola."), tr("Vuelvo en un momento."), tr("Ya estoy de vuelta."), tr("Juego con mando: escribo despacio."), tr("Me tengo que ir. Hasta otra.")],
}
SIN_SERIE = ("nombres_servidor",) + tuple(l for l in LISTAS if l.startswith("frases_servidor_"))      # las que pueden venir vacías: el servidor trae las suyas
_SERIE.update({l: [] for l in SIN_SERIE})
_OFICIOS_SERIE = [{"nombre": "camarero", "femenino": "camarera", "edad_max": 66}, {"nombre": "estudiante", "edad_max": 27, "peso": 3},
                  {"nombre": "taxista", "edad_max": 66}, {"nombre": "jubilado", "femenino": "jubilada", "edad_min": 62, "peso": 6}]
_CARACTERES_SERIE = {
    "amable": {"desc": "amable", "desc_ia": tr("amable y cordial"), "saludo": 6, "cumplido": 8, "chiste": 5, "insulto": -30, "valor": 0.2},
    "hablador": {"desc": tr("con ganas de hablar"), "desc_ia": tr("muy habladora"), "saludo": 8, "cumplido": 6, "chiste": 8, "insulto": -25, "valor": 0.3},
    "seco": {"desc": tr("de pocas palabras"), "desc_ia": tr("seca, de pocas palabras"), "saludo": 2, "cumplido": 2, "chiste": -2, "insulto": -35, "valor": 0.6},
    "timido": {"desc": tr("con timidez"), "desc_ia": tr("tímida, se corta al hablar"), "saludo": 3, "cumplido": 4, "chiste": 3, "insulto": -40, "valor": 0.05},
    "chulo": {"desc": tr("con chulería"), "desc_ia": tr("chula y presumida"), "saludo": 1, "cumplido": 9, "chiste": 4, "insulto": -45, "valor": 0.85},
}
_BANDAS_SERIE = [tr("Los Calaveras"), tr("Los Lagartos"), tr("Los Barrenos"), tr("Los Tiburones"), tr("Los Cuervos")]

G = {k: list(v) for k, v in _SERIE.items()}       # las listas en vigor
OFICIOS = [dict(o) for o in _OFICIOS_SERIE]
CARACTERES = {k: dict(v) for k, v in _CARACTERES_SERIE.items()}      # el mismo objeto siempre: otros módulos lo guardan
BANDAS = [{"id": n, "nombre": n} for n in _BANDAS_SERIE]
TIPOS = {}
POLICIA = {}
CAJAS = {}


def _textos(v):
    return [str(x).strip() for x in v if isinstance(x, str) and x.strip()] if isinstance(v, (list, tuple)) else []


def _num(v, defecto, minimo=None, maximo=None):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return defecto
    if minimo is not None:
        n = max(minimo, n)
    if maximo is not None:
        n = min(maximo, n)
    return n


def fusionar_gente(base, nuevo):
    """Lo que un mod dice de la gente de la calle, puesto sobre lo que ya había. Sin más, cada lista del mod se añade a la
    del juego; con «sustituir», las listas que el mod trae ocupan el sitio de las del juego. Lo que el mod no trae, se queda."""
    out = dict(base or {})
    if not isinstance(nuevo, dict):
        return out
    sustituir = bool(nuevo.get("sustituir"))
    for k, v in nuevo.items():
        if k in ("id", "sustituir"):
            continue
        if not isinstance(v, list) or sustituir:
            out[k] = v
        elif k == "oficios":
            lista = [dict(o) for o in (out.get(k) or []) if isinstance(o, dict)]
            for o in v:
                if isinstance(o, dict) and o.get("nombre"):
                    pos = next((n for n, x in enumerate(lista) if x.get("nombre") == o["nombre"]), None)
                    if pos is None:
                        lista.append(o)
                    else:
                        lista[pos] = o
            out[k] = lista
        else:
            viejo = list(out.get(k) or [])
            out[k] = viejo + [x for x in v if x not in viejo]
    out.setdefault("id", "general")
    return out


def configurar(datos):
    """Toma de los datos ya cargados, con los mods encima, todo lo de este módulo. Lo que falte o venga vacío se queda de serie."""
    g = next((x for x in datos.get("gente", []) if isinstance(x, dict)), {})
    for k in LISTAS:
        G[k] = _textos(g.get(k)) or list(_SERIE[k])
    ofi = [dict(o, nombre=str(o["nombre"]).strip()) for o in (g.get("oficios") or []) if isinstance(o, dict) and str(o.get("nombre", "")).strip()]
    OFICIOS[:] = ofi or [dict(o) for o in _OFICIOS_SERIE]
    car = {}
    for c in datos.get("caracteres", []):
        if isinstance(c, dict) and c.get("id"):
            base = _CARACTERES_SERIE.get(c.get("habla") if c.get("habla") in HABLAS else c["id"], _CARACTERES_SERIE["amable"])
            car[str(c["id"])] = {"desc": str(c.get("desc") or base["desc"]), "desc_ia": str(c.get("desc_ia") or c.get("desc") or base["desc_ia"]),
                                 "saludo": _num(c.get("saludo"), base["saludo"]), "cumplido": _num(c.get("cumplido"), base["cumplido"]),
                                 "chiste": _num(c.get("chiste"), base["chiste"]), "insulto": _num(c.get("insulto"), base["insulto"]),
                                 "valor": _num(c.get("valor"), base["valor"], 0.0, 1.0),
                                 "habla": c.get("habla") if c.get("habla") in HABLAS else (c["id"] if c["id"] in HABLAS else "amable")}
    CARACTERES.clear()
    CARACTERES.update(car or {k: dict(v, habla=k) for k, v in _CARACTERES_SERIE.items()})
    ban = [dict(b, nombre=str(b["nombre"]).strip()) for b in datos.get("bandas", []) if isinstance(b, dict) and str(b.get("nombre", "")).strip()]
    BANDAS[:] = ban or [{"id": n, "nombre": n} for n in _BANDAS_SERIE]
    TIPOS.clear()
    for t in datos.get("tipos_enemigo", []):
        if isinstance(t, dict) and t.get("id"):
            TIPOS[str(t["id"])] = t
    POLICIA.clear()
    for n in datos.get("policia_niveles", []):
        if isinstance(n, dict):
            nivel = int(_num(n.get("nivel"), 0))
            if 1 <= nivel <= 5:
                POLICIA[nivel] = n
    CAJAS.clear()
    for c in datos.get("cajas_locales", []):
        if isinstance(c, dict) and c.get("id"):
            CAJAS[str(c["id"])] = c


# ------------------------------------------------------------------ gente de la calle
def lista(cual):
    """Una de las listas de la gente de la calle: nombres_h, nombres_m, apellidos, frases, apodos, perros, bandas_propias,
    rivales_carrera, nombres_servidor, frases_servidor_ y una clase, o las frases ya escritas del chat y del rol. Nunca viene vacía, salvo las del servidor (SIN_SERIE)."""
    return G.get(cual) or list(_SERIE.get(cual, []))


def nombres(genero):
    return lista("nombres_m" if genero == "m" else "nombres_h")


def oficio_para(edad, genero="h", rng=random):
    """Un oficio que cuadre con la edad: nadie estudia a los sesenta ni se jubila a los veinte. Cada oficio dice en los datos
    entre qué edades se tiene y cuánto abunda."""
    ops, pesos = [], []
    for o in OFICIOS:
        if _num(o.get("edad_min"), 0) <= edad <= _num(o.get("edad_max"), 200):
            ops.append(o)
            pesos.append(max(0.01, _num(o.get("peso"), 1.0)))
    if not ops:
        ops, pesos = list(OFICIOS), [1.0] * len(OFICIOS)
    o = rng.choices(ops, weights=pesos)[0]
    return _oficio_pl(str(o.get("femenino") or o["nombre"]) if genero == "m" else o["nombre"], genero)


def caracter(ident):
    """Los números y los textos de un carácter. Si ya no existe (era de un mod que se quitó), vale el primero."""
    return CARACTERES.get(ident) or next(iter(CARACTERES.values()))


def habla_de(ident):
    """Con las frases de cuál de los caracteres del juego habla este: el suyo, si es de los de serie."""
    return ident if ident in HABLAS else caracter(ident).get("habla", "amable")


# ------------------------------------------------------------------------- bandas
def nombres_bandas():
    return [b["nombre"] for b in BANDAS]


def banda(nombre):
    """Los datos de una banda por su nombre o su identificador. None si no existe."""
    return next((b for b in BANDAS if nombre and nombre in (b.get("nombre"), b.get("id"))), None)


def banda_en(texto):
    """La banda cuyo nombre aparece en un texto (el nombre de un enemigo, por ejemplo). None si ninguna."""
    return next((b["nombre"] for b in BANDAS if b["nombre"] in (texto or "")), None)


def tipos_de_banda(nombre):
    """(tipos de enemigo con los que pelea a pie, tipo de los refuerzos que llegan en vehículo o None)."""
    b = banda(nombre) or {}
    tipos = [t for t in (b.get("tipos") or []) if t in TIPOS] or [t for t in ("pandillero", "pandillero_duro") if t in TIPOS]
    ref = b.get("refuerzo") if b.get("refuerzo") in TIPOS else None
    return tipos, ref


# ---------------------------------------------------------------- tipos de enemigo
def tipo_enemigo(ident):
    """Un tipo de enemigo del catálogo, o None."""
    return TIPOS.get(ident) if ident else None


def enemigo(grupo, rng=random):
    """Lo que vale para un enemigo de un grupo de una misión: lo de su tipo («clase»), y por encima lo que el grupo diga.

    Un grupo sin tipo, como los de siempre (nombre, arma y salud), sigue valiendo igual. Devuelve un diccionario con
    nombre, arma, salud, punteria, vehiculo (vacío, a pie), ocupantes, frases, voz y clase."""
    grupo = grupo or {}
    t = TIPOS.get(grupo.get("clase")) or {}
    armas = [a for a in (t.get("armas") or []) if a]
    return {"nombre": str(grupo.get("tipo") or t.get("nombre") or tr("Enemigo")),
            "arma": grupo.get("arma") or (rng.choice(armas) if armas else t.get("arma")) or "pistola",
            "salud": _num(grupo.get("salud", t.get("salud")), 60.0, 1.0),
            "punteria": _num(grupo.get("punteria", t.get("punteria")), PUNTERIA, 0.02, 1.0),
            "vehiculo": "" if grupo.get("a_pie") else str(grupo.get("vehiculo") or t.get("vehiculo") or ""),
            "ocupantes": int(_num(grupo.get("ocupantes", t.get("ocupantes")), 4, 1, 8)),
            "frases": _textos(grupo.get("frases")) or _textos(t.get("frases")),
            "voz": grupo.get("voz") or t.get("voz") or "", "clase": grupo.get("clase") or ""}


def grupo(clase, n=1, **serie):
    """Un grupo de enemigos para un paso «eliminar»: n del tipo dado. Si ese tipo no está en los datos, vale lo que se
    pase como de serie (tipo, que es el nombre, arma y salud), que es como se escribían antes."""
    return {"n": int(n), "clase": clase} if clase in TIPOS else dict(serie, n=int(n))


def vestir(p, e, rng=random):
    """Pone a una persona lo que dice su ficha de enemigo: arma, salud, puntería, frases y voz."""
    p.arma = e["arma"]
    p.salud = float(e["salud"])
    p.punteria = float(e["punteria"])
    p.frases = list(e["frases"])
    p.clase = e["clase"]
    if e["voz"] == "grave":
        p.tono = rng.uniform(0.78, 0.92)
    elif e["voz"] == "aguda":
        p.tono = rng.uniform(1.25, 1.42)
    return p


# ------------------------------------------------------ policía por nivel de búsqueda
def agentes_nivel(nivel, rng=random):
    """El tipo de agente que sale en una patrulla con ese nivel de búsqueda: uno al azar de los que diga la tabla de los datos.
    Devuelve su ficha, como enemigo(). Sin tabla, lo de siempre: pistola, y subfusil desde el nivel 4."""
    n = POLICIA.get(max(1, min(5, int(nivel or 1)))) or {}
    tipos = [t for t in (n.get("tipos") or []) if t in TIPOS]
    if tipos:
        e = enemigo({"clase": rng.choice(tipos)}, rng)
    else:
        e = enemigo({"tipo": tr("Policía"), "arma": "subfusil" if nivel >= 4 else "pistola", "salud": 80, "ocupantes": 2}, rng)
    e["vehiculo"] = e["vehiculo"] or "patrulla"
    return e


def aviso_nivel(nivel):
    """Lo que se dice de más al llegar a ese nivel de búsqueda, si los datos traen algo."""
    return str((POLICIA.get(nivel) or {}).get("aviso") or "").strip()


def policia_para_servidor(armas):
    """La tabla de la policía, resumida para un servidor en línea: por cada nivel, las armas y la salud de los agentes."""
    out = {}
    for nivel, n in sorted(POLICIA.items()):
        ops = []
        for ident in n.get("tipos") or []:
            t = TIPOS.get(ident)
            if t and t.get("arma") in armas:
                ops.append({"arma": t["arma"], "salud": _num(t.get("salud"), 80.0, 1.0), "agentes": int(_num(t.get("ocupantes"), 2, 1, 4))})
        if ops:
            out[str(nivel)] = ops
    return out


# ------------------------------------------------------------------ caja de los locales
def caja_local(tipo):
    """Lo que dicen los datos de la caja de un tipo de local: {"minimo", "maximo", "guardias", "guardia", "busqueda"}.
    None si ese tipo de local no tiene caja que llevarse."""
    c = CAJAS.get(tipo)
    if not c:
        return None
    minimo = int(_num(c.get("minimo"), 0, 0))
    maximo = max(minimo, int(_num(c.get("maximo"), minimo, 0)))
    guardia = c.get("guardia") if c.get("guardia") in TIPOS else ""
    return {"minimo": minimo, "maximo": maximo, "guardias": int(_num(c.get("guardias"), 0, 0, 12)) if guardia else 0, "guardia": guardia,
            "busqueda": int(_num(c.get("busqueda"), 2, 0, 5))}


def botin_local(tipo, rng=random, minimo=0, maximo=0):
    """Cuánto hay hoy en la caja de un local de ese tipo: un número al azar entre el mínimo y el máximo de los datos.
    Si ese tipo no tiene caja en los datos, entre los dos números que se le pasen."""
    c = caja_local(tipo) or {"minimo": int(minimo), "maximo": max(int(minimo), int(maximo))}
    return rng.randint(c["minimo"], c["maximo"])


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False

# ---------------------------------------------------------------- łatka polskiej wersji (latki/zawody_przechodniow.py)
_OFICIOS_PL = {
    "camarero": ("kelner", "kelnerka"), "camarera": ("kelner", "kelnerka"), "pescador": ("rybak", "rybaczka"), "pescadora": ("rybak", "rybaczka"),
    "estudiante": ("student", "studentka"), "taxista": ("taksówkarz", "taksówkarka"), "[taksówkarz|taksówkarka]": ("taksówkarz", "taksówkarka"),
    "[strażnik|strażniczka]": ("ochroniarz", "ochroniarka"), "enfermero": ("pielęgniarz", "pielęgniarka"),
    "enfermera": ("pielęgniarz", "pielęgniarka"), "albañil": ("murarz", "murarka"), "murarz": ("murarz", "murarka"),
    "funcionario": ("urzędnik", "urzędniczka"), "funcionaria": ("urzędnik", "urzędniczka"), "mecánico": ("mechanik", "mechaniczka"),
    "mecánica": ("mechanik", "mechaniczka"), "mechanik": ("mechanik", "mechaniczka"), "panadero": ("piekarz", "piekarka"),
    "panadera": ("piekarz", "piekarka"), "jubilado": ("emeryt", "emerytka"), "jubilada": ("emeryt", "emerytka"),
    "dependiente": ("sprzedawca", "sprzedawczyni"), "dependienta": ("sprzedawca", "sprzedawczyni"), "músico": ("muzyk", "muzyczka"),
    "música": ("muzyk", "muzyczka"), "muzyk": ("muzyk", "muzyczka"), "repartidor": ("dostawca", "dostawczyni"),
    "repartidora": ("dostawca", "dostawczyni"), "profesor": ("nauczyciel", "nauczycielka"), "profesora": ("nauczyciel", "nauczycielka"),
    "electricista": ("elektryk", "elektryczka"), "peluquero": ("fryzjer", "fryzjerka"), "peluquera": ("fryzjer", "fryzjerka"),
    "vigilante": ("ochroniarz", "ochroniarka"), "cocinero": ("kucharz", "kucharka"), "cocinera": ("kucharz", "kucharka"),
    "administrativo": ("pracownik biurowy", "pracownica biurowa"), "administrativa": ("pracownik biurowy", "pracownica biurowa"),
    "fontanero": ("hydraulik", "hydrauliczka"), "fontanera": ("hydraulik", "hydrauliczka"), "estibador": ("doker", "dokerka"),
    "estibadora": ("doker", "dokerka"), "socorrista": ("ratownik", "ratowniczka"),
}


def _oficio_pl(nombre, genero):
    if not _pl():
        return nombre
    para = _OFICIOS_PL.get(nombre)
    return (para[1] if genero == "m" else para[0]) if para else nombre


# Charakter „amable”: jego opis to samo słowo co identyfikator, więc słownik go nie tłumaczy.
_caracter_es = caracter


def caracter(ident):
    c = _caracter_es(ident)
    if _pl() and c.get("desc") == "amable":
        c = dict(c, desc="uprzejmie")
    return c
