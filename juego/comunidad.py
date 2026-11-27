"""Comunidad de jugadores, en el menú principal: grupos, foros, servidores y otros sitios que crean y llevan los propios
jugadores. No es oficial. Lo que se lista está en data/datos/comunidad.json; aquí solo está cómo se recorre.

La lista se pone al día sola, sin esperar a una versión del juego (desde la 1.7.6): se publica firmada, como los
componentes, en comunidad.json junto a componentes.json de cada fuente (herramientas/publicar_comunidad.py). El juego la
consulta en segundo plano al arrancar (si busca actualizaciones o componentes) y al entrar en la sección, guarda la
última en data/comunidad_descargada.json y usa la de «revision» más alta entre esa y la que trae. La publicada lleva
también la traducción de sus textos a cada idioma, para los que el catálogo del juego todavía no tenga."""
import copy
import json
import os
import threading

from . import actualizador as A, i18n, registro, rutas
from .i18n import tr

ARCHIVO = "comunidad.json"
DESCARGADA = "comunidad_descargada.json"          # en data: la última lista publicada que se ha bajado
_estado = {"en_marcha": False, "consultada": False}


def ruta_descargada():
    return rutas.data(DESCARGADA)


def _revision(d):
    try:
        return int((d or {}).get("revision", 0))
    except (TypeError, ValueError, AttributeError):
        return 0


def _leer_descargada():
    """La lista bajada, si está y su firma es buena; si no, None."""
    try:
        with open(ruta_descargada(), encoding="utf-8") as f:
            m = json.load(f)
        A.verificar_firma(dict(m))
    except Exception:
        return None
    return m if isinstance(m, dict) and isinstance(m.get("datos"), dict) else None


def _con_textos(obj, textos, clave=None):
    """Traduce en el sitio con los textos que trae la lista publicada (los identificadores no)."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                if v in textos and not i18n.es_identificador(v, k):
                    obj[k] = textos[v]
            else:
                _con_textos(v, textos, k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                if v in textos and not i18n.es_identificador(v, clave):
                    obj[i] = textos[v]
            else:
                _con_textos(v, textos, clave)
    return obj


def descargar(fuente="servidor", url_personalizada="", abrir=None, claves=None):
    """Baja la lista publicada de cada fuente, se queda con la de revisión más alta y, si es más nueva que la guardada, la
    guarda. Devuelve la publicada (o None si ninguna fuente responde con una lista firmada)."""
    from . import componentes as C
    abrir = abrir or A.abrir_red
    mejor = None
    for nombre, url in C.fuentes(fuente if fuente in A.FUENTES else "servidor", url_personalizada):
        u = url.rsplit("/", 1)[0] + "/" + ARCHIVO
        try:
            m = A._leer_manifiesto(u, A.NOMBRE_FUENTE[nombre], abrir)
            A.verificar_firma(dict(m), claves)
        except (A.ErrorActualizacion, ValueError) as e:
            registro.info("comunidad", "Lista de la comunidad sin bajar", fuente=nombre, motivo=f"{type(e).__name__}: {e}")
            continue
        if isinstance(m.get("datos"), dict) and (mejor is None or _revision(m["datos"]) > _revision(mejor["datos"])):
            mejor = m
    if mejor is None:
        return None
    guardada = _leer_descargada()
    if guardada is None or _revision(mejor["datos"]) > _revision(guardada["datos"]):
        ruta = ruta_descargada()
        with open(ruta + ".tmp", "w", encoding="utf-8") as f:
            json.dump(mejor, f, ensure_ascii=False, indent=1)
        os.replace(ruta + ".tmp", ruta)
        registro.info("comunidad", "Lista de la comunidad al día", revision=_revision(mejor["datos"]))
    return mejor


def poner_al_dia(app, en_segundo_plano=True):
    """Consulta la lista publicada con la fuente de las actualizaciones. Nunca molesta: sin red, se queda la que hay."""
    if _estado["en_marcha"] or getattr(app, "pruebas", False):
        return

    def f():
        _estado["en_marcha"] = True
        try:
            descargar(app.cfg["act_fuente"], app.cfg["act_url"])
        except Exception as e:                                       # la sección funciona igual con la lista que ya hay
            registro.info("comunidad", "Lista de la comunidad sin consultar", motivo=f"{type(e).__name__}: {e}")
        finally:
            _estado["en_marcha"] = False
            _estado["consultada"] = True
    if en_segundo_plano:
        threading.Thread(target=f, daemon=True).start()
    else:
        f()


def cargar():
    """Los datos de la sección, en el idioma del juego. Si el archivo falta o está roto, una sección vacía con los avisos.
    En el juego compilado el archivo va protegido (comunidad.pbd): se lee como los demás datos, con mundo._leer_json."""
    from .mundo import _leer_json
    try:
        d = _leer_json(os.path.join(rutas.DATOS, ARCHIVO))
    except Exception:
        d = {}
    if not isinstance(d, dict):
        d = {}
    d = copy.deepcopy(d)
    bajada = _leer_descargada()
    if bajada and _revision(bajada["datos"]) > _revision(d):        # la publicada, si es más nueva que la que trae el juego
        d = copy.deepcopy(bajada["datos"])
        textos = (bajada.get("textos") or {}).get(i18n.actual())
        if isinstance(textos, dict) and not i18n.es_origen():
            _con_textos(d, textos)
    d = i18n.traducir_datos(d)
    d.setdefault("titulo", tr("Comunidad de jugadores, sección no oficial"))
    d.setdefault("aviso", tr("Esta sección no es oficial."))
    d.setdefault("responsabilidad", "")
    d.setdefault("secciones", [])
    return d


def _abrir_url(app, url, que):
    try:
        os.startfile(url)
        app.decir(tr('Abriendo {que} en tu navegador.').format(que=que), True)
    except (OSError, AttributeError):
        app.son("error")
        app.decir(tr('No se pudo abrir el navegador. La dirección es {url}').format(url=url), True)


def anadir_servidor(app, nombre, direccion):
    """Lo añade a la lista de Jugar en un servidor, con su nombre. Devuelve si lo ha añadido (False si ya estaba)."""
    lista = list(app.cfg["servidores"])
    if any(str(x.get("dir", "")).lower() == direccion.lower() for x in lista):
        app.decir(tr('{nombre} ya está en tu lista de servidores. Entra desde el menú principal, Jugar en un servidor.').format(nombre=nombre), True)
        return False
    lista.append({"nombre": nombre, "dir": direccion, "cert": ""})
    app.cfg["servidores"] = lista
    app.cfg.guardar()
    app.son("menu_ok")
    app.decir(tr('{nombre} añadido a tu lista de servidores. Para entrar, en el menú principal, Jugar en un servidor.').format(nombre=nombre), True)
    return True


def _opcion_enlace(app, e, Opcion, con_idioma=True):
    nombre = e.get("nombre", "")
    idioma = e.get("idioma", "")
    if e.get("tipo"):                                                # tutorial en audio, vídeo, pódcast, manual...
        nombre_tipo = tr('{nombre}: {tipo}').format(nombre=nombre, tipo=e["tipo"])
    else:
        nombre_tipo = nombre
    texto = tr('{nombre}, en {idioma}').format(nombre=nombre_tipo, idioma=idioma) if idioma and con_idioma else nombre_tipo
    desc = e.get("desc", "")
    if e.get("servidor"):
        return Opcion(texto, lambda: anadir_servidor(app, nombre, e["servidor"]),
                      ayuda=(desc + " " if desc else "") + tr('La dirección es {dir}. Intro lo añade a tu lista de Jugar en un servidor.').format(dir=e["servidor"]))
    url = e.get("url", "")
    return Opcion(texto, lambda: _abrir_url(app, url, nombre), ayuda=(desc + " " if desc else "") + tr("Intro lo abre en tu navegador."))


def menu(app):
    from .menus import Menu, Opcion
    d = cargar()
    if not _estado["consultada"]:                                    # lo nuevo sale la próxima vez que se entre
        poner_al_dia(app)

    def vacio():
        return [Opcion(tr("Todavía no hay nada aquí"), ayuda=d.get("apuntar") or tr("Si creas algo para los jugadores, avisa al autor para que salga aquí."))]

    def seccion(s):
        def f():
            enlaces = s.get("enlaces", [])
            if s.get("por_idioma") and enlaces:
                return por_idioma(s, enlaces)
            ops = [_opcion_enlace(app, e, Opcion) for e in enlaces] or vacio()
            app.abrir(Menu(app, s.get("nombre", ""), ops, intro=s.get("ayuda") or None))
        return f

    def por_idioma(s, enlaces):
        """Primero el idioma, y dentro, lo que hay en él (issue 25). El del juego va el primero."""
        grupos = {}
        for e in enlaces:
            grupos.setdefault(e.get("idioma") or tr("sin idioma indicado"), []).append(e)
        mio = tr(i18n.NOMBRES_ES.get(i18n.actual(), "")) if i18n.NOMBRES_ES.get(i18n.actual()) else ""
        orden = sorted(grupos, key=lambda n: (n.lower() != mio.lower(), n.lower()))

        def abrir_idioma(idioma):
            def g():
                app.abrir(Menu(app, tr('{nombre}, en {idioma}').format(nombre=s.get("nombre", ""), idioma=idioma),
                               [_opcion_enlace(app, e, Opcion, con_idioma=False) for e in grupos[idioma]]))
            return g
        ops = [Opcion(tr('En {idioma}: {n}').format(idioma=idioma, n=len(grupos[idioma])), abrir_idioma(idioma),
                      ayuda=tr("Lo que hay en este idioma. Intro lo abre.")) for idioma in orden]
        app.abrir(Menu(app, s.get("nombre", ""), ops, intro=s.get("ayuda") or None))
    ops = [Opcion(d["aviso"], ayuda=d["responsabilidad"] or None)]
    if d["responsabilidad"]:
        ops.append(Opcion(d["responsabilidad"], ayuda=tr("Cada sitio tiene sus propias normas, que ponen quienes lo llevan.")))
    for s in d["secciones"]:
        n = len(s.get("enlaces", []))
        ops.append(Opcion(tr('{nombre}: {n}').format(nombre=s.get("nombre", ""), n=n), seccion(s), ayuda=s.get("ayuda") or None))
    if d.get("apuntar") and d.get("apuntar_url"):
        ops.append(Opcion(tr("Apuntar un grupo, un foro, un servidor o cualquier otro recurso"), lambda: _abrir_url(app, d["apuntar_url"], tr("la issue de la comunidad")),
                          ayuda=d["apuntar"]))
    app.abrir(Menu(app, d["titulo"], ops, intro=d["aviso"] + (" " + d["responsabilidad"] if d["responsabilidad"] else "")))
