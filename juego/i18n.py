"""Idiomas: el juego se escribe en español y se puede traducir a cualquier otro.

- El español es el idioma de origen. Cada texto que se dice o se lee va en el código envuelto en tr("..."); en los datos
  (.json) va tal cual. Cada idioma es una carpeta, data/idiomas/<código>/ (en, it, fr...), con su catálogo, textos.json,
  que dice cómo se dice cada texto español en ese idioma, y sus voces, en voces/. Lo que no esté en el catálogo se queda
  en español. Basta con copiar la carpeta de un idioma para tenerlo: el juego sabe cómo se llama por su código, aunque
  la carpeta no lo diga (o lo dice idioma.json, {"nombre": "Italiano"}).
- Qué idioma: la opción «idioma» de la configuración. Con «auto», que es lo de serie, se mira el del sistema: si es
  cualquier variante del español, español; si es otro y hay catálogo para él, ese; si no, inglés.
- Se decide una vez, al arrancar, antes de cargar ningún texto. Cambiar de idioma en las opciones vale al reiniciar.
- Los textos con huecos llevan nombre en cada hueco: tr("Tienes {dinero} euros").format(dinero=...). El catálogo dice
  «You have {dinero} euros» y el hueco se rellena igual.
- La documentación va por idioma: manual_es.html, manual_en.html... doc("manual") da la del idioma; si ese idioma aún no
  tiene sus guías, la inglesa, y si tampoco, la española.
- Las voces grabadas de las escenas van por idioma, como los documentos: data/voces/<historia>_<código>. En un idioma
  sin grabaciones, las escenas las dice el lector de pantalla.

Para el juego de las pruebas, la variable de entorno PUERTOBRAVO_IDIOMA manda sobre todo lo demás.
"""
import json
import os
import re

from . import rutas

ORIGEN = "es"
_estado = {"idioma": None, "textos": {}, "info": {}}


# Cómo se llama cada idioma en su propia lengua, por su código: así una carpeta nueva se reconoce sola.
NOMBRES = {"es": "Español", "en": "English", "it": "Italiano", "fr": "Français", "pt": "Português do Brasil", "de": "Deutsch", "ca": "Català",
           "eu": "Euskara", "gl": "Galego", "nl": "Nederlands", "pl": "Polski", "ru": "Русский", "uk": "Українська", "tr": "Türkçe",
           "ro": "Română", "sv": "Svenska", "da": "Dansk", "no": "Norsk", "nb": "Norsk bokmål", "fi": "Suomi", "cs": "Čeština", "sk": "Slovenčina",
           "hu": "Magyar", "el": "Ελληνικά", "ar": "العربية", "he": "עברית", "hi": "हिन्दी", "ja": "日本語", "ko": "한국어", "zh": "中文",
           "vi": "Tiếng Việt", "id": "Bahasa Indonesia", "eo": "Esperanto", "hr": "Hrvatski", "sr": "Српски", "bg": "Български", "sl": "Slovenščina"}


def es(texto):
    """Marca un texto español que se traduce en otro momento, no donde está escrito (los nombres de los idiomas, lo que
    dice el manifiesto de componentes): así entra en los catálogos. Devuelve el mismo texto."""
    return texto


# Cómo se llama cada idioma en español: el catálogo de cada idioma dice cómo se llama en ese idioma.
NOMBRES_ES = {"es": es("español"), "en": es("inglés"), "it": es("italiano"), "fr": es("francés"), "pt": es("portugués de Brasil"), "de": es("alemán"),
              "ca": es("catalán"), "eu": es("euskera"), "gl": es("gallego"), "nl": es("neerlandés"), "pl": es("polaco"), "ru": es("ruso"),
              "uk": es("ucraniano"), "tr": es("turco"), "ro": es("rumano"), "sv": es("sueco"), "da": es("danés"), "no": es("noruego"),
              "nb": es("noruego bokmål"), "fi": es("finés"), "cs": es("checo"), "sk": es("eslovaco"), "hu": es("húngaro"), "el": es("griego"),
              "ar": es("árabe"), "he": es("hebreo"), "hi": es("hindi"), "ja": es("japonés"), "ko": es("coreano"), "zh": es("chino"),
              "vi": es("vietnamita"), "id": es("indonesio"), "eo": es("esperanto"), "hr": es("croata"), "sr": es("serbio"), "bg": es("búlgaro"),
              "sl": es("esloveno")}
_catalogos = {}


def catalogo(cod):
    """El catálogo de un idioma, {español: traducción}, leído una vez. El del español está vacío."""
    if cod == ORIGEN:
        return {}
    if cod not in _catalogos:
        try:
            with open(os.path.join(carpeta(cod), "textos.json"), encoding="utf-8") as f:
                d = json.load(f)
            _catalogos[cod] = {k: v for k, v in (d.get("textos", d) or {}).items() if isinstance(v, str) and v}
        except (OSError, ValueError, AttributeError):
            _catalogos[cod] = {}
    return _catalogos[cod]


def en_idioma(texto, cod):
    """Un texto español dicho en el idioma ``cod``, haya o no arrancado el juego en él. Tal cual si no está traducido."""
    return catalogo(cod).get(texto, texto) if isinstance(texto, str) else texto


def idioma_en(cod, idioma=None):
    """Cómo se llama el idioma ``cod`` dicho en ``idioma`` (el del juego, si no se dice), en minúscula y sin más:
    «vietnamita», «Vietnamese», «tiếng Việt». Si no se sabe, su propio nombre."""
    idioma = idioma or actual()
    if cod not in NOMBRES_ES:
        return nombre_de(cod)
    local = NOMBRES_ES[cod] if idioma == ORIGEN else catalogo(idioma).get(NOMBRES_ES[cod])
    return local or nombre_de(cod)


def nombre_en(cod, idioma=None):
    """Cómo se presenta un idioma en una lista: en el idioma de quien lee y, entre paréntesis, en el suyo, para que cada uno
    encuentre el suyo aunque no entienda el del juego: «vietnamita (Tiếng Việt)». El propio, solo con su nombre."""
    idioma = idioma or actual()
    propio = nombre_de(cod)
    if cod == idioma:
        return propio
    local = idioma_en(cod, idioma)
    return propio if local.lower() == propio.lower() else f"{local} ({propio})"


def carpeta(cod=None):
    return rutas.data("idiomas", cod) if cod else rutas.data("idiomas")


def nombre_de(cod):
    """El nombre del idioma en su propia lengua: el que le corresponde por su código o, si el juego no lo conoce, el de su
    idioma.json. (Hasta la 1.7.2 mandaba el de idioma.json: por eso el del vietnamita lleva también vietnamita y
    Vietnamese, para que se entienda en esa versión.)"""
    if cod in NOMBRES:
        return NOMBRES[cod]
    try:
        with open(os.path.join(carpeta(cod), "idioma.json"), encoding="utf-8") as f:
            n = json.load(f).get("nombre")
            if n:
                return str(n)
    except (OSError, ValueError, AttributeError):
        pass
    return NOMBRES.get(cod, cod)


def disponibles():
    """Los idiomas que hay: {código: nombre}. El español siempre; los demás, cada carpeta con su catálogo."""
    r = {"es": NOMBRES["es"]}
    try:
        for cod in sorted(os.listdir(carpeta())):
            if os.path.isfile(os.path.join(carpeta(cod), "textos.json")):
                r[cod] = nombre_de(cod)
    except OSError:
        pass
    return r


def idioma_del_sistema():
    """El código de dos letras del idioma de Windows (o del sistema), en minúsculas. Cadena vacía si no se sabe."""
    try:
        import ctypes
        import locale
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        nombre = locale.windows_locale.get(lcid, "")
        if nombre:
            return nombre.split("_")[0].lower()
    except Exception:
        pass
    try:
        import locale
        nombre = (locale.getlocale()[0] or "") or (os.environ.get("LANG", ""))
        return nombre.replace("-", "_").split("_")[0].lower()[:2]
    except Exception:
        return ""


def _de_la_configuracion():
    """La opción «idioma» de la configuración, leída sin cargar nada más del juego. «auto» si no hay."""
    try:
        from . import cifrado
        ruta = rutas.archivo_config("config")
        otra = ruta[:-4] + (".json" if ruta.endswith(".pbc") else ".pbc")
        for r in (ruta, otra):
            if os.path.exists(r):
                return str(cifrado.leer_json(r).get("idioma", "auto") or "auto")
    except Exception:
        pass
    return "auto"


def elegir(preferido=None):
    """El idioma que toca: el pedido, si existe; si es «auto», el del sistema; si no hay catálogo, inglés; y si tampoco, español."""
    hay = disponibles()
    pedido = (os.environ.get("PUERTOBRAVO_IDIOMA") or preferido or _de_la_configuracion() or "auto").lower()
    if pedido != "auto":
        return pedido if pedido in hay else ORIGEN
    sistema = idioma_del_sistema()
    if sistema == "es" or not sistema:
        return ORIGEN
    if sistema in hay:
        return sistema
    return "en" if "en" in hay else ORIGEN


def cargar(idioma=None):
    """Fija el idioma y carga su catálogo. Se llama sola la primera vez que hace falta."""
    cod = elegir(idioma)
    textos, info = {}, {}
    if cod != ORIGEN:
        try:
            with open(os.path.join(carpeta(cod), "textos.json"), encoding="utf-8") as f:
                d = json.load(f)
            textos = {k: v for k, v in (d.get("textos", d) or {}).items() if isinstance(v, str) and v and not k.startswith("_")}
            info = {"codigo": cod, "nombre": nombre_de(cod)}
        except (OSError, ValueError, AttributeError):
            cod = ORIGEN
        if cod != ORIGEN:                                  # la traducción de los mods que llegan como componente, cada uno la suya
            textos.update(_textos_de_mods(cod, textos))
    _estado.update(idioma=cod, textos=textos, info=info)
    return cod


def _textos_de_mods(cod, ya):
    """Lo que traen data/idiomas/<código>/mods/*.json: la traducción de un mod que no viene con el juego. No pisa el catálogo."""
    r = {}
    carpeta_mods = os.path.join(carpeta(cod), "mods")
    try:
        nombres = sorted(n for n in os.listdir(carpeta_mods) if n.lower().endswith(".json"))
    except OSError:
        return r
    for n in nombres:
        try:
            with open(os.path.join(carpeta_mods, n), encoding="utf-8") as f:
                d = json.load(f)
            r.update({k: v for k, v in (d.get("textos", d) or {}).items() if isinstance(v, str) and v and k not in ya})
        except (OSError, ValueError, AttributeError):
            continue
    return r


def actual():
    if _estado["idioma"] is None:
        cargar()
    return _estado["idioma"]


def es_origen():
    return actual() == ORIGEN


def tr(texto):
    """El texto en el idioma del juego. En español, o si no está en el catálogo, tal cual."""
    if _estado["idioma"] is None:
        cargar()
    if not _estado["textos"] or not isinstance(texto, str):
        return texto
    return _estado["textos"].get(texto, texto)


# ------------------------------------------------------------------ lo que dice el servidor
# El servidor en línea manda sus textos siempre en español, porque en él juega gente de idiomas distintos: cada juego los
# dice en el suyo. Los que llevan huecos («%s compra %s, en %s.») llegan ya rellenos, así que se reconocen por su
# plantilla: cada texto del catálogo con %s o %d se convierte una vez en una expresión regular.
_HUECO_SRV = re.compile(r"(%%|%s|%d)")
_LETRA = re.compile(r"[^\W\d_]")
_plantillas_srv = {"de": None, "por_palabra": {}, "abiertas": [], "hechos": {}}


def _plantillas_servidor():
    """Las plantillas del catálogo, compiladas y ordenadas de la más concreta a la menos: (letras, abierta, expresión,
    traducción, huecos). Las que empiezan por una palabra entera van también por esa palabra, para mirar menos."""
    t = _estado["textos"]
    c = _plantillas_srv
    if c["de"] is t:
        return c
    por_palabra, abiertas = {}, []
    for k, v in t.items():
        if "%s" not in k and "%d" not in k:
            continue
        partes = [p for p in _HUECO_SRV.split(k) if p != ""]
        huecos = [p for p in partes if p in ("%s", "%d")]
        if [h for h in _HUECO_SRV.findall(v) if h != "%%"] != huecos:      # la traducción, con los mismos huecos y en el mismo orden
            continue
        literal = "".join(p for p in partes if p not in ("%s", "%d"))
        letras = len(_LETRA.findall(literal))
        if letras < 2:
            continue
        patron = "".join("(.+?)" if p == "%s" else r"(-?\d+)" if p == "%d" else re.escape("%" if p == "%%" else p) for p in partes)
        abierta = partes[0] in ("%s", "%d") and partes[-1] in ("%s", "%d")
        p = (letras, abierta, re.compile(patron + r"\Z", re.S), v, huecos)
        inicio = partes[0]
        if inicio not in ("%s", "%d", "%%") and " " in inicio:
            por_palabra.setdefault(inicio.split(" ", 1)[0], []).append(p)
        else:
            abiertas.append(p)
    for lista in list(por_palabra.values()) + [abiertas]:
        lista.sort(key=lambda p: -p[0])
    c.update(de=t, por_palabra=por_palabra, abiertas=abiertas, hechos={})
    return c


def _por_plantilla(texto, nivel):
    """El texto traducido por su plantilla, o None si no encaja en ninguna. ``nivel`` 0 es el texto entero, que tiene que
    encajar en una plantilla con letras de sobra; dentro de un hueco (nivel 1) basta con menos."""
    c = _plantillas_servidor()
    t = c["de"]
    candidatas = c["por_palabra"].get(texto.split(" ", 1)[0], []) + c["abiertas"]
    for letras, abierta, expr, traduccion, huecos in candidatas:
        if nivel == 0 and letras < (10 if abierta else 4):
            continue
        m = expr.match(texto)
        if m is None:
            continue
        valores = []
        for hueco, valor in zip(huecos, m.groups()):
            if hueco == "%d":
                valores.append(int(valor))
            elif valor in t:                                     # lugares, bandas, armas: salen de los datos, en español
                valores.append(t[valor])
            else:
                dentro = _por_plantilla(valor, nivel + 1) if nivel < 2 else None
                valores.append(valor if dentro is None else dentro)
        try:
            return traduccion % tuple(valores)
        except (TypeError, ValueError):
            continue
    return None


def tr_servidor(texto):
    """Un texto que manda el servidor en línea (un aviso, por qué no te deja entrar, por qué te saca), en el idioma del
    juego: el del catálogo si está tal cual; si no, por su plantilla, con cada hueco rellenado como llegó (y traducido si es
    un nombre del mundo); y si no se reconoce, tal cual. Nunca para lo que escriben los jugadores."""
    if _estado["idioma"] is None:
        cargar()
    t = _estado["textos"]
    if not t or not isinstance(texto, str) or not texto:
        return texto
    if texto in t:
        return t[texto]
    hechos = _plantillas_servidor()["hechos"]
    if texto not in hechos:
        if len(hechos) > 500:
            hechos.clear()
        r = _por_plantilla(texto, 0)
        hechos[texto] = texto if r is None else r
    return hechos[texto]


# Un identificador de los datos va en minúscula, sin espacios ni tildes («pesca», «puerto», «agente»). Muchos son también
# palabras que el catálogo traduce, así que no se traducen nunca, salvo en los campos que son texto para leer, como el
# nombre de algo o los rangos de la policía: si no, el código ya no los encontraría («fishing» en vez de «pesca»).
_IDENTIFICADOR = re.compile(r"[a-z0-9_]+\Z")
CAMPOS_DE_TEXTO = frozenset(("nombre", "nombres", "rangos", "texto", "titulo", "descripcion", "frases", "femenino", "desc"))     # femenino y desc: los oficios y caracteres de gente.json


def es_identificador(valor, clave):
    """Si el valor de ese campo es un identificador de los datos, que no se traduce."""
    return isinstance(valor, str) and clave not in CAMPOS_DE_TEXTO and _IDENTIFICADOR.match(valor) is not None


def traducir_datos(obj):
    """Traduce, en el sitio, todos los textos de unos datos (.json ya cargados) que estén en el catálogo, menos los
    identificadores (es_identificador). Devuelve el mismo objeto."""
    if _estado["idioma"] is None:
        cargar()
    t = _estado["textos"]
    if not t:
        return obj

    def rec(o, clave=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, str):
                    if v in t and not es_identificador(v, k):
                        o[k] = t[v]
                else:
                    rec(v, k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str):
                    if v in t and not es_identificador(v, clave):
                        o[i] = t[v]
                else:
                    rec(v, clave)
    rec(obj)
    return obj


SOLO_ES_EN = ("novedades",)      # se escriben en español y en inglés: con el juego en español, en español; en cualquier otro, en inglés


def idioma_novedades():
    """En qué idioma se leen las novedades: español con el juego en español, inglés con cualquier otro."""
    return ORIGEN if actual() == ORIGEN else "en"


def doc(nombre):
    """Ruta de un documento en el idioma del juego: data/docs/<nombre>_<idioma>.html. Un idioma que aún no tiene sus guías
    traducidas abre las inglesas, como el juego cuando no tiene el idioma del sistema; y si tampoco, las españolas.
    Las novedades solo están en español y en inglés (SOLO_ES_EN)."""
    primero = idioma_novedades() if nombre in SOLO_ES_EN else actual()
    for cod in dict.fromkeys((primero, "en" if primero != ORIGEN else ORIGEN, ORIGEN)):
        r = rutas.data("docs", f"{nombre}_{cod}.html")
        if os.path.exists(r):
            return r
    return rutas.data("docs", f"{nombre}.html")


def quitar_docs_sin_idioma():
    """Hasta la 1.7.1 las guías se llamaban manual.html, teclas.html...; ahora llevan su idioma (manual_es.html). La vieja,
    si ya está la española, sobra: se quita para que nadie abra una guía atrasada. Devuelve cuántas ha quitado."""
    import re
    n = 0
    try:
        carpeta_docs = rutas.data("docs")
        for f in os.listdir(carpeta_docs):
            base, ext = os.path.splitext(f)
            if ext.lower() == ".html" and not re.search(r"_[a-z]{2}$", base) and os.path.exists(os.path.join(carpeta_docs, f"{base}_es.html")):
                os.remove(os.path.join(carpeta_docs, f))
                n += 1
    except OSError:
        pass
    return n


def quitar_leemes_viejos():
    """Hasta la 1.7.2 el LEEME de cada idioma se llamaba LEEME_en.txt, LEEME_vi.txt; desde la 1.7.3 lleva un nombre que se
    entiende en inglés, README_en.txt, y el de los mods README_mods_en.txt. Al actualizar el viejo se queda: si ya está el
    nuevo, sobra. El español sigue siendo LEEME.txt. Devuelve cuántos ha quitado."""
    import re
    n = 0
    for carpeta, viejo, nuevo in ((rutas.base(), "LEEME_{}.txt", "README_{}.txt"),
                                  (rutas.data("mods"), "LEEME_mods_{}.txt", "README_mods_{}.txt")):
        try:
            for f in os.listdir(carpeta):
                m = re.fullmatch(nuevo.replace(".", r"\.").format(r"([a-z]{2,3})"), f)
                if m and os.path.isfile(os.path.join(carpeta, viejo.format(m.group(1)))):
                    os.remove(os.path.join(carpeta, viejo.format(m.group(1))))
                    n += 1
        except OSError:
            pass
    return n


def original(texto):
    """El texto español del que sale una traducción de cualquier idioma instalado; el mismo si no sale de ninguno."""
    if not isinstance(texto, str):
        return texto
    return _inverso_de_todos().get(texto, texto)


_inverso = {}


def _inverso_de_todos():
    """De cada texto traducido de cualquier idioma instalado, el español del que sale. Si dos textos españoles dan la misma
    traducción, ese texto no se puede devolver con seguridad y no entra."""
    if _inverso.get("hecho"):
        return _inverso["mapa"]
    mapa, dudosos = {}, set()
    for cod in disponibles():
        if cod == ORIGEN:
            continue
        try:
            with open(os.path.join(carpeta(cod), "textos.json"), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        for es, otro in (d.get("textos", d) or {}).items():
            if not isinstance(otro, str) or not otro or otro == es:
                continue
            if otro in mapa and mapa[otro] != es:
                dudosos.add(otro)
            mapa[otro] = es
    for x in dudosos:
        mapa.pop(x, None)
    _inverso.update(hecho=True, mapa=mapa)
    return mapa


def identificador_perdido(texto, validos):
    """El identificador que una partida guardada perdió al cargarse (hasta la 1.7.5, «taxi» se volvía «un taxi», porque
    en un catálogo «un taxi» se traduce «taxi»): el de `validos` que sea la traducción de ese texto. None si no hay."""
    for cod in disponibles():
        if cod == ORIGEN:
            continue
        try:
            with open(os.path.join(carpeta(cod), "textos.json"), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        w = (d.get("textos", d) or {}).get(texto)
        if isinstance(w, str) and w in validos:
            return w
    return None


def al_idioma_de_ahora(obj, respetar=()):
    """Pone en el idioma del juego los textos de una partida guardada en cualquier idioma: lo que se guarda por nombre
    (la ropa, los objetos, la gente que conoces) se busca después en los datos, que están en el idioma de ahora. Cada texto
    se lleva primero a su español y de ahí al idioma de ahora. Las claves de `respetar` (como el nombre que te pusiste) no
    se tocan. Devuelve el mismo objeto."""
    if _estado["idioma"] is None:
        cargar()
    inv = _inverso_de_todos()
    t = _estado["textos"]
    if not inv and not t:
        return obj

    def uno(v, clave):
        es = v if v in t or not inv else inv.get(v, v)
        if es_identificador(es, clave):                # un identificador, en español como en los datos (y el de una partida
            return es                                  # guardada antes de la 1.7.3, traducido entonces, vuelve a serlo)
        if es_identificador(v, clave):                 # un identificador que en algún idioma es la traducción de una frase
            return v                                   # («taxi», de «un taxi»): sigue siendo el identificador (foro, 1.7.6)
        return t.get(es, es)

    def rec(o, clave=None):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in respetar:
                    continue
                if isinstance(v, str):
                    o[k] = uno(v, k)
                else:
                    rec(v, k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str):
                    o[i] = uno(v, clave)
                else:
                    rec(v, clave)
    rec(obj)
    return obj
