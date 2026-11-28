"""Saca todos los textos traducibles del juego y prepara el catálogo de cada idioma.

    python herramientas\\i18n\\extraer.py                     catálogo de origen y lotes pendientes del inglés
    python herramientas\\i18n\\extraer.py --idioma fr         lo mismo para otro idioma
    python herramientas\\i18n\\extraer.py --raiz CARPETA      leer el código de otra carpeta (para probar)

- Del código: cada tr("...") (y es("...") del servidor) de juego, editor, panel_servidor, servidor y las herramientas que
  escriben documentos (generar_datos, preparar_carpeta_servidor).
- De los datos: cada texto de data\\datos y de los mods de data\\mods que sea para personas (los identificadores no), y el
  nombre y la descripción de cada pack de sonidos (data\\sonidos\\<pack>\\pack.json).
- Escribe traduccion\\origen.json (cada texto con dónde aparece) y, para el idioma, traduccion\\<idioma>\\pendientes\\lote_NNN.json
  con los textos que aún no tienen traducción en data\\idiomas\\<idioma>.json, agrupados por archivo para dar contexto.
"""
import ast
import glob
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marcar import es_texto                                             # noqa: E402

LOTE = 220
MARCAS = ("tr", "es")             # tr: se traduce donde se dice; es: lo dice el servidor en español y lo traduce cada juego
SUELTOS = ("generar_datos.py", "preparar_carpeta_servidor.py")     # herramientas que escriben documentos para el jugador


def del_codigo(raiz):
    r = {}
    archivos = [f for carpeta in ("juego", "editor", "panel_servidor", "servidor") for f in glob.glob(os.path.join(raiz, carpeta, "**", "*.py"), recursive=True)]
    archivos += [os.path.join(raiz, "herramientas", n) for n in SUELTOS]
    if True:
        for f in archivos:
            try:
                arbol = ast.parse(open(f, encoding="utf-8").read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            rel = os.path.relpath(f, raiz).replace("\\", "/")
            for n in ast.walk(arbol):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in MARCAS and n.args \
                        and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str) and n.args[0].value.strip():
                    r.setdefault(n.args[0].value, []).append(rel)
    return r


def de_los_datos():
    r = {}

    def rec(o, rel):
        if isinstance(o, str):
            if es_texto(o):
                r.setdefault(o, []).append(rel)
        elif isinstance(o, dict):
            for v in o.values():
                rec(v, rel)
        elif isinstance(o, list):
            for v in o:
                rec(v, rel)
    for f in sorted(glob.glob(os.path.join(RAIZ, "data", "datos", "**", "*.json"), recursive=True) + glob.glob(os.path.join(RAIZ, "data", "mods", "*.json"))):
        if "voces_puente" in f:
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rel = os.path.relpath(f, RAIZ).replace("\\", "/")
        rec(d, rel)
        if os.path.basename(f) == "gente.json" and isinstance(d, dict):      # los oficios y los caracteres son una palabra en
            bloques = [d] + [g for g in d.get("gente", []) if isinstance(g, dict)]
            for o in (o for g in bloques for o in g.get("oficios", [])):      # minúscula, como un identificador, pero se leen
                for clave in ("nombre", "femenino"):
                    if isinstance(o, dict) and isinstance(o.get(clave), str) and o[clave].strip():
                        r.setdefault(o[clave], []).append(rel)
            for c in (c for g in bloques for c in g.get("caracteres", [])):
                if isinstance(c, dict) and isinstance(c.get("desc"), str) and c["desc"].strip():
                    r.setdefault(c["desc"], []).append(rel)

        def puestos(o):                                                  # los puestos de las carreras: «gerente», «operari[o|a]»
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "puestos" and isinstance(v, list):
                        for q in v:
                            if isinstance(q, dict) and isinstance(q.get("nombre"), str) and q["nombre"].strip():
                                r.setdefault(q["nombre"], []).append(rel)
                    else:
                        puestos(v)
            elif isinstance(o, list):
                for v in o:
                    puestos(v)
        puestos(d)
    for f in sorted(glob.glob(os.path.join(RAIZ, "data", "sonidos", "*", "pack.json"))):     # el nombre y la descripción de cada pack
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rel = os.path.relpath(f, RAIZ).replace("\\", "/")
        for clave in ("nombre", "descripcion"):
            if isinstance(d.get(clave), str) and d[clave].strip():
                r.setdefault(d[clave], []).append(rel)
    return r


def main(args):
    idioma = args[args.index("--idioma") + 1] if "--idioma" in args else "en"
    raiz = args[args.index("--raiz") + 1] if "--raiz" in args else RAIZ
    origen = {}
    for k, v in list(del_codigo(raiz).items()) + list(de_los_datos().items()):
        origen.setdefault(k, [])
        origen[k] += [x for x in v if x not in origen[k]]
    os.makedirs(os.path.join(RAIZ, "traduccion"), exist_ok=True)
    with open(os.path.join(RAIZ, "traduccion", "origen.json"), "w", encoding="utf-8") as f:
        json.dump(origen, f, ensure_ascii=False, indent=0, sort_keys=True)
    hecho = {}
    for cat in (os.path.join(RAIZ, "data", "idiomas", idioma, "textos.json"), os.path.join(RAIZ, "traduccion", idioma, idioma + ".json")):
        if os.path.exists(cat):
            hecho.update(json.load(open(cat, encoding="utf-8")).get("textos") or {})
    faltan = [k for k in origen if not hecho.get(k)]
    faltan.sort(key=lambda k: (origen[k][0], k))                         # por archivo: el contexto ayuda
    carpeta = os.path.join(RAIZ, "traduccion", idioma, "pendientes")
    os.makedirs(carpeta, exist_ok=True)
    for viejo in glob.glob(os.path.join(carpeta, "lote_*.json")):
        os.remove(viejo)
    n = 0
    for i in range(0, len(faltan), LOTE):
        n += 1
        trozo = faltan[i:i + LOTE]
        with open(os.path.join(carpeta, f"lote_{n:03d}.json"), "w", encoding="utf-8") as f:
            json.dump([{"es": k, "donde": origen[k][0]} for k in trozo], f, ensure_ascii=False, indent=1)
    letras = sum(len(k) for k in faltan)
    print(f"Textos: {len(origen)}. Ya traducidos al {idioma}: {len(origen) - len(faltan)}. Pendientes: {len(faltan)} en {n} lotes, {letras} letras.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
