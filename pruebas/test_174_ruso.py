"""Idiomas (1.7.4): el ruso, que llega como componente para la 1.7.3 y viene de serie desde la 1.7.4.

Lo que tiene que cumplir, como cualquier idioma: el catálogo entero, los mismos huecos que el español, la clave de delante
del «=» intacta, las marcas de género con dos formas y en ruso (no las del español pegadas detrás), «Dani» en latino para
que el juego ponga el nombre del protagonista, y las letras de las teclas en latino, como en el teclado.
"""
import json
import os
import re
import string
import subprocess
import sys

from juego import i18n

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARCA = re.compile(r"\[([^\[\]|]*)\|([^\[\]|]*)\]")
MARCA_ES = re.compile(r"\[[a-záéíóúñ]*\|[a-záéíóúñ]*\]")


def _catalogo():
    return json.load(open(os.path.join(RAIZ, "data", "idiomas", "ru", "textos.json"), encoding="utf-8"))["textos"]


def _huecos(t):
    return {f for _, f, _, _ in string.Formatter().parse(t) if f is not None}


def test_el_ruso_esta_completo_y_se_reconoce():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "i18n"))
    import fusionar
    cat = _catalogo()
    origen = json.load(open(os.path.join(RAIZ, "traduccion", "origen.json"), encoding="utf-8"))
    faltan = [k for k in origen if not cat.get(k)]
    assert not faltan, f"{len(faltan)} textos sin traducir: {faltan[:10]}"
    assert not [k for k, v in cat.items() if fusionar.problema(k, v)]
    assert i18n.disponibles().get("ru") == "Русский"
    assert i18n.nombre_en("ru", "es") == "ruso (Русский)" and i18n.nombre_en("ru", "en") == "Russian (Русский)"


def test_cada_traduccion_rusa_vale_en_el_juego():
    malos = []
    for k, v in _catalogo().items():
        if _huecos(v) - _huecos(k) - {"o", "a", "e", "os", "as"}:
            malos.append(("hueco", k))
        if ("%s" in k or "%d" in k) and re.findall(r"%[sd]", k.replace("%%", "")) != re.findall(r"%[sd]", v.replace("%%", "")):
            malos.append(("%", k))
        m = re.match(r"^([a-z_0-9]+)=", k)
        if m and not v.startswith(m.group(1) + "="):
            malos.append(("clave", k))
        if any("|" in b and not MARCA.fullmatch(b) for b in re.findall(r"\[[^\[\]]*\]", v)):
            malos.append(("género", k))
        if MARCA.search(k) and MARCA_ES.search(v):
            malos.append(("marca del español", k))
        if re.search(r"\bDani\b", k) and not re.search(r"\bDani\b", v):
            malos.append(("Dani", k))
    assert not malos, malos[:10]


def test_las_teclas_van_en_latino():
    cat = _catalogo()
    for es in ("Mayúsculas O", "Mayúsculas H", "Mayúsculas L", "F1", "F7 y F8", "A y D", "Retroceso", "Escape", "Control G"):
        assert not re.search(r"(?<![\w])[А-ЯЁ](?![\w])|Ф\d", cat[es]), (es, cat[es])
    assert "Побег" not in "".join(v for k, v in cat.items() if "Escape" in k)          # «huida»: Escape es una tecla
    assert cat["Mayúsculas W"] == "Shift W"


def test_en_ruso_las_guias_son_las_inglesas_mientras_no_esten_traducidas():
    env = dict(os.environ, PUERTOBRAVO_IDIOMA="ru", PYTHONIOENCODING="utf-8", SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYGAME_HIDE_SUPPORT_PROMPT="1")
    r = subprocess.run([sys.executable, "-c", "from juego import i18n\nprint(i18n.actual(), i18n.doc('manual').replace(chr(92), '/').rsplit('/', 1)[-1], i18n.doc('teclas').replace(chr(92), '/').rsplit('/', 1)[-1])\n"],
                       cwd=RAIZ, env=env, capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, r.stderr[-2000:]
    cod, manual, teclas = r.stdout.split()
    assert cod == "ru" and manual in ("manual_ru.html", "manual_en.html") and teclas == "teclas_ru.html"


def test_los_mods_que_llegan_como_componente_estan_en_ruso():
    for carpeta, mod in (("mod_marisma_negra", "marisma_negra"), ("mod_el_diablo", "el_diablo")):
        spec = json.load(open(os.path.join(RAIZ, "componentes_extra", carpeta, "componente.json"), encoding="utf-8"))
        assert spec["nombres"].get("ru") and spec["descripciones"].get("ru")
        assert {"origen": f"../../traduccion/ru/mods/{mod}.json", "destino": f"data/idiomas/ru/mods/{mod}.json"} in spec["archivos"]
        ru = json.load(open(os.path.join(RAIZ, "traduccion", "ru", "mods", f"{mod}.json"), encoding="utf-8"))["textos"]
        en = json.load(open(os.path.join(RAIZ, "traduccion", "en", "mods", f"{mod}.json"), encoding="utf-8"))["textos"]
        assert set(en) <= set(ru), [k for k in en if k not in ru][:5]
        assert not [k for k, v in ru.items() if MARCA_ES.search(v) or (re.search(r"\bDani\b", k) and "Dani" not in v)]


def test_el_componente_del_ruso_dice_que_es_en_cada_idioma():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
    import publicar_componentes as P
    d = P.presentar("idioma-ru", "idioma", RAIZ)
    assert d["nombres"]["es"] == "ruso (Русский)" and d["nombres"]["en"] == "Russian (Русский)" and d["nombres"]["ru"] == "Русский"
    assert "Opciones, Idioma" in d["descripcion"]


def test_el_instalador_no_traduce_sintaxis_de_windows(tmp_path):
    from juego import actualizador as A
    prog = tmp_path / "prog"
    nueva = tmp_path / "actualizacion" / "nueva"
    prog.mkdir(parents=True)
    nueva.mkdir(parents=True)
    (nueva / "PuertoBravo.exe").write_bytes(b"exe")
    antiguo = os.environ.get("PUERTOBRAVO_IDIOMA")
    os.environ["PUERTOBRAVO_IDIOMA"] = "ru"
    try:
        i18n.cargar("ru")
        bat = A.escribir_instalador(str(nueva), str(prog), pid=1, version="1.7.5")
        texto = open(bat, encoding="utf-8").read()
        assert "@echo off" in texto
        assert "setlocal" in texto
        assert "goto fin" in texto
        assert "goto copiar" in texto
        assert "if errorlevel 1 goto programas" in texto
        assert 'set "APP=' in texto
        assert 'set "NUEVA=' in texto
        assert 'set "COPIA=' in texto
        assert '(goto) 2>nul & del "%~f0"' in texto
        for prohibido in ("установите", "перейдите", "если уровень ошибки", "иди подожди", ">ноль", "«%REG%»", "%CОПИЯ%"):
            assert prohibido not in texto, f"Texto traducido indebido en el .bat: {prohibido}"
    finally:
        if antiguo is None:
            os.environ.pop("PUERTOBRAVO_IDIOMA", None)
        else:
            os.environ["PUERTOBRAVO_IDIOMA"] = antiguo
        i18n.cargar("es")


def test_traduccion_mando_y_botones_en_ruso():
    cat = _catalogo()
    assert cat["Mando"] == "Контроллер"
    assert cat["Mando, a pie"] == "Контроллер, пешком"
    assert cat["Mando, al volante"] == "Контроллер, за рулём"
    assert cat["cruceta arriba"] == "крестовина вверх"
    assert cat["Cuadrado"] == "Квадрат"
    assert cat["Equis"] == "Крест"
    assert "команда" not in cat["Mando"].lower()
    assert "командир" not in cat["Mando, al volante"].lower()



def test_ningun_texto_del_mando_lleva_los_nombres_viejos():
    """Lo que dice qué botón pulsar usa los nombres de la PR 40 en todos los textos, no solo en los que tocó: Крест, Квадрат,
    крестовина y стик, y no «Эквис», «траверса», «перекрестие» ni «рычаг». Los trozos que solo sustituyen frases en
    español (mando.py, con \1 o cortados) no cuentan: en ruso nunca se usan."""
    cat = _catalogo()
    viejos = re.compile(r"Эквис|Equis|Square|Circulo|травер|перекладин|перекрест|рычаг|D-pad", re.I)
    trozos = {r"\1on la palanca izquierda", "a palanca izquierda", "mpuja a fondo la palanca izquierda"}
    malos = [k for k, v in cat.items() if k not in trozos and re.search(r"Equis|Cuadrado|cruceta|palanca (izquierda|derecha)", k)
             and viejos.search(v)]
    assert not malos, malos[:5]
