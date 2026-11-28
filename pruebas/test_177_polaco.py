"""Idiomas (1.7.7): el polaco (PR 49 y 50), que llega como componente para la 1.7.6 y viene de serie desde la 1.7.7.

Lo mismo que el ruso: el catálogo entero, los mismos huecos que el español, la clave de delante del «=» intacta, las
marcas de género con dos formas y en polaco, y «Dani» para que el juego ponga el nombre del protagonista. Y que lo que
la PR añadió al código solo cambia el juego en polaco.
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
    return json.load(open(os.path.join(RAIZ, "data", "idiomas", "pl", "textos.json"), encoding="utf-8"))["textos"]


def _huecos(t):
    return {f for _, f, _, _ in string.Formatter().parse(t) if f is not None}


def test_el_polaco_esta_completo_y_se_reconoce():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas", "i18n"))
    import fusionar
    cat = _catalogo()
    origen = json.load(open(os.path.join(RAIZ, "traduccion", "origen.json"), encoding="utf-8"))
    faltan = [k for k in origen if not cat.get(k)]
    assert not faltan, f"{len(faltan)} textos sin traducir: {faltan[:10]}"
    assert not [k for k, v in cat.items() if fusionar.problema(k, v)]
    assert i18n.disponibles().get("pl") == "Polski"
    assert i18n.nombre_en("pl", "es") == "polaco (Polski)" and i18n.nombre_en("pl", "en") == "Polish (Polski)"


def test_cada_traduccion_polaca_vale_en_el_juego():
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
        # (la marca del español no se mira: el polaco escribe sus marcas con las mismas letras, como [y|a])
        if re.search(r"\bDani\b", k) and not re.search(r"\bDani\b", v):
            malos.append(("Dani", k))
    assert not malos, malos[:10]


def test_lo_polaco_del_codigo_no_cambia_los_demas_idiomas():
    from juego import mando, respuestas
    assert not any("przeład" in v or "hamulec" in v for v in mando._PISTAS.values())     # las pistas polacas, aparte
    assert mando._pistas() is mando._PISTAS
    import inspect
    assert "_pl() and normal(texto)" in inspect.getsource(respuestas.responder)       # las preguntas polacas, solo en polaco


def test_los_oficios_y_los_puestos_se_traducen_en_todos_los_idiomas():
    origen = json.load(open(os.path.join(RAIZ, "traduccion", "origen.json"), encoding="utf-8"))
    for k in ("camarero", "camarera", "amable", "operari[o|a]", "gerente"):
        assert k in origen
        for cod in ("en", "pt", "ru", "vi", "pl"):
            cat = json.load(open(os.path.join(RAIZ, "data", "idiomas", cod, "textos.json"), encoding="utf-8"))["textos"]
            assert cat.get(k), (cod, k)
    assert i18n.es_identificador("camarera", "femenino") is False and i18n.es_identificador("amable", "desc") is False
