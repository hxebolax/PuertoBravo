"""Vigilantes de los sonidos: todos los packs traen exactamente los mismos sonidos que los de serie, sus cuentas y sus
créditos cuadran con sus archivos, y todos los sonidos salen en Aprender los sonidos y en el volumen de cada sonido, con una
sola clasificación, un buscador y la forma de devolver cada sonido a su volumen de serie."""
import csv
import json
import os
import re
from pathlib import Path

import numpy as np
import pygame
import pytest

from juego import audio, ayuda, catalogo_sonidos as cat, config, menus_juego, packs, rutas, sintesis
from juego.menus import EntradaTexto, Menu, Opcion

SERIE = os.path.join(rutas.PACKS, rutas.POR_DEFECTO)
# sonidos de la 1.7.1 que en los packs son grabaciones, y los que se quedan a propósito con el sonido del juego
GRABADOS_171 = ("megafono", "emisora", "timbre", "nevera", "cocina_cortar", "cocina_freir", "cocina_hervir", "plato_servido", "cesta",
                "amenaza_barrio", "barrio_perdido", "barrio_defendido")
TONOS_171 = ("chat_personaje", "chat_fuera", "chat_accion", "espera_servidor")


def _carpetas():
    return sorted(d for d in os.listdir(rutas.PACKS) if os.path.isdir(os.path.join(rutas.PACKS, d)) and not d.startswith("_"))


def _audios(carpeta):
    """[(nombre, archivo)] de una carpeta, sin pasar por el juego: lo que hay en el disco."""
    return sorted((os.path.splitext(f)[0], f) for f in os.listdir(os.path.join(rutas.PACKS, carpeta)) if f.lower().endswith(rutas.EXT_AUDIO))


def _serie():
    return sorted(n for n, _ in _audios(rutas.POR_DEFECTO))


def _igual_al_de_serie(carpeta, nombre):
    """El sonido del pack es el de serie (se admite la diferencia de redondeo de haberlo guardado dos veces)."""
    a = sintesis.leer_audio(os.path.join(SERIE, dict(_audios(rutas.POR_DEFECTO))[nombre]))
    b = sintesis.leer_audio(os.path.join(rutas.PACKS, carpeta, dict(_audios(carpeta))[nombre]))
    return len(a) == len(b) and float(np.max(np.abs(a - b))) < 3.0 / 32768


def _creditos(carpeta):
    with open(os.path.join(rutas.PACKS, carpeta, "CREDITOS.txt"), encoding="utf-8-sig") as f:
        return f.read()


def test_todos_los_packs_tienen_exactamente_los_mismos_sonidos():
    """Ni uno de más ni uno de menos, ni un sonido en dos formatos, en ninguna carpeta de data/sonidos."""
    serie = _serie()
    assert len(serie) >= 270 and len(serie) == len(set(serie))
    carpetas = _carpetas()
    assert {"por_defecto", "realista", "alternativo", "retro", "envolvente"} <= set(carpetas)
    for carpeta in carpetas:
        nombres = [n for n, _ in _audios(carpeta)]
        repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
        assert not repetidos, f"{carpeta}: en dos formatos: {repetidos}"
        faltan, sobran = sorted(set(serie) - set(nombres)), sorted(set(nombres) - set(serie))
        assert not faltan and not sobran, f"{carpeta}: faltan {faltan}; sobran {sobran}"
        assert len(nombres) == len(serie)
        for _, archivo in _audios(carpeta):
            assert os.path.getsize(os.path.join(rutas.PACKS, carpeta, archivo)) > 200, f"{carpeta}/{archivo} está vacío"
    # y el juego ve lo mismo que hay en el disco
    for pk in packs.listar():
        if not pk["id"].startswith("_"):
            assert pk["n"] == len(serie), f"{pk['id']}: el juego cuenta {pk['n']} sonidos"


def test_las_cuentas_y_los_creditos_de_cada_pack_cuadran_con_sus_archivos():
    serie = _serie()
    marca = sintesis.FORMATO + ": "
    for carpeta in _carpetas():
        if carpeta == rutas.POR_DEFECTO:
            continue
        with open(os.path.join(rutas.PACKS, carpeta, "pack.json"), encoding="utf-8") as f:
            meta = json.load(f)
        texto = _creditos(carpeta)
        if carpeta == "estudio":  # Muestras de biblioteca con un manifiesto de origen por toma.
            raiz = Path(rutas.PACKS, carpeta)
            with (raiz / meta["fuentes"]).open(encoding="utf-8", newline="") as f:
                filas = list(csv.DictReader(f))
            assert meta["sonidos"] == len(serie)
            assert len(filas) == len(list(raiz.rglob("*.flac")))
            assert {raiz / fila["archivo"] for fila in filas} == set(raiz.rglob("*.flac"))
            assert all(fila["fuente"] and fila["edicion"] for fila in filas)
            assert meta["licencia"] and meta["fuentes"] in texto
            continue
        assert meta.get("nombre") and meta.get("descripcion") and "CC0" in meta.get("licencia", "")
        if "grabaciones" not in meta:                       # el envolvente: cuenta sonidos y ambientes en estéreo
            assert meta["sonidos"] == len(serie)
            import soundfile as sf
            estereo = [n for n, a in _audios(carpeta) if sf.info(os.path.join(rutas.PACKS, carpeta, a)).channels == 2]
            assert meta["ambientes_en_estereo"] == len(estereo)
            for n in estereo:
                assert re.search(rf"^{n}: .+ Licencia CC0 .*https://", texto, re.M), f"{carpeta}: {n} sin crédito"
            for n in GRABADOS_171:
                assert re.search(rf"^{n}: .+Licencia CC0 \(dominio público\)\. https://bigsoundbank\.com/", texto, re.M), f"{carpeta}: {n} sin crédito"
            continue
        lineas = [x for x in texto.splitlines() if x.startswith("  ") and marca in x and " " not in x.strip().split(marca)[0]]
        nombres = [x.strip().split(marca)[0] for x in lineas]
        assert len(nombres) == len(set(nombres)), f"{carpeta}: sonidos con dos líneas de crédito"
        assert not [x for x in lineas if "original del juego" in x], f"{carpeta}: los originales van en su lista, no línea a línea"
        originales = texto.split("SONIDOS ORIGINALES DEL JUEGO")[1].splitlines()[2].strip().split(", ")
        assert sorted(nombres + originales) == serie, f"{carpeta}: los créditos no nombran todos los sonidos una vez"
        assert meta["grabaciones"] == len(nombres) and meta["originales_del_juego"] == len(originales)
        assert meta["grabaciones"] + meta["originales_del_juego"] == len(serie)
        assert f"Trae los {len(serie)} sonidos del juego: {len(nombres)} son grabaciones reales descargadas y {len(originales)} son el sonido" in texto
        assert "SONIDOS AÑADIDOS DESPUÉS" not in texto
        # lo que dicen los créditos es verdad: un «original» es el sonido de serie, y una grabación no lo es
        for n in originales:
            assert _igual_al_de_serie(carpeta, n), f"{carpeta}: {n} figura como original y no lo es"
        for n in GRABADOS_171:
            assert n in nombres and not _igual_al_de_serie(carpeta, n), f"{carpeta}: {n} debería ser una grabación"
        for n in TONOS_171:
            assert n in originales
        # las grabaciones sueltas dicen título, autor, licencia y página
        for x in lineas:
            if x.strip().split(marca)[0] in GRABADOS_171:
                assert re.search(r"«.+», de .+\. Licencia CC0 \(dominio público\)\. https://bigsoundbank\.com/\S+\.html\. Dura \d+,\d\d segundos\.$", x), x
        assert "https://bigsoundbank.com" in texto.split("QUÉ SONIDO SALE DE DÓNDE")[0]


def test_las_grabaciones_nuevas_tienen_duracion_y_nivel_razonables():
    """Sin oído, lo que se puede comprobar: ni largas ni mudas, sin silencio en los extremos, sin recorte, y en su sitio."""
    tope = {"cesta": 0.7, "emisora": 1.1, "plato_servido": 1.0, "megafono": 1.2, "nevera": 1.3, "cocina_cortar": 1.6, "cocina_freir": 2.5,
            "cocina_hervir": 2.5, "timbre": 2.7, "amenaza_barrio": 1.4, "barrio_perdido": 2.0, "barrio_defendido": 1.6}
    for carpeta in ("realista", "alternativo", "retro", "envolvente"):
        archivos = dict(_audios(carpeta))
        for n in GRABADOS_171:
            d = sintesis.leer_audio(os.path.join(rutas.PACKS, carpeta, archivos[n]))
            dur, pico = len(d) / sintesis.SR, float(np.max(np.abs(d)))
            assert 0.25 <= dur <= tope[n], f"{carpeta}/{n}: dura {dur:.2f}"
            assert 0.85 <= pico <= 0.91, f"{carpeta}/{n}: pico {pico:.2f}"
            assert packs.nivel(d) > 0.02, f"{carpeta}/{n}: apenas suena"
            oye = np.nonzero(np.abs(d) > 0.02 * pico)[0]
            assert oye[0] / sintesis.SR < 0.05 and (len(d) - oye[-1]) / sintesis.SR < 0.2, f"{carpeta}/{n}: silencio en los extremos"
            assert abs(float(d[0])) < 0.05 and abs(float(d[-1])) < 0.05, f"{carpeta}/{n}: empieza o acaba con chasquido"
    # el retro y el envolvente llevan aquí lo mismo que el realista
    for n in GRABADOS_171:
        a = open(os.path.join(rutas.PACKS, "realista", n + sintesis.FORMATO), "rb").read()
        for carpeta in ("retro", "envolvente"):
            assert open(os.path.join(rutas.PACKS, carpeta, n + sintesis.FORMATO), "rb").read() == a
    # cocinar: picar cabe antes de que entre el fuego, y el fuego antes del plato
    from juego import menus_cocina
    assert menus_cocina.Cocinando  # los tiempos de esa pantalla son 1,7 y 4,3 segundos
    assert tope["cocina_cortar"] <= 1.7 and tope["cocina_freir"] <= 4.3 - 1.7


# ====================================================================== la clasificación: una sola, la misma en todas partes
def _archivo(op):
    return re.match(r"Archivo (\S+)\.", op.ayuda).group(1)


def _escribir(robot, texto):
    for ch in texto:
        robot.tecla(ord(ch) if ch.isascii() else 0, unicode=ch)


def _ir(app, contiene):
    m = app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if contiene in o.texto)
    return m


def test_todo_sonido_esta_en_un_solo_grupo_con_nombre_y_explicacion():
    """Ninguno cae en «Otros sonidos», ninguno está en dos grupos, y cada uno tiene un nombre que se dice, distinto del de los
    demás, y una explicación de lo que significa oírlo."""
    serie = _serie()
    apuntados = [s for lista in cat.SONIDOS.values() for s, _, _ in lista]
    assert sorted(apuntados) == serie, (sorted(set(serie) - set(apuntados)), sorted(set(apuntados) - set(serie)))
    assert len(apuntados) == len(set(apuntados)), sorted(s for s in set(apuntados) if apuntados.count(s) > 1)
    assert set(cat.SONIDOS) == {g[2] for g in cat.GRUPOS} and len(cat.GRUPOS) == len({g[0] for g in cat.GRUPOS}) == len({g[2] for g in cat.GRUPOS})
    nombres = {}
    for n in serie:
        assert cat.grupo_de(n) < len(cat.GRUPOS), f"{n} no está en ningún grupo del catálogo"
        nombre, texto = cat.nombre(n), cat.describir(n)
        assert texto != "Sonido del juego." and len(texto) >= 12 and texto.endswith(".") and texto[0].isupper(), f"{n}: {texto!r}"
        assert len(nombre) >= 3 and nombre[0].isupper() and "_" not in nombre and ":" not in nombre and not nombre.endswith("."), f"{n}: {nombre!r}"
        for jerga in ("En bucle", "Firma sonora", "npc", "NPC", "archivo", "interfaz", "sprite", "loop"):
            assert jerga not in texto and jerga not in nombre, f"{n}: {jerga!r} en {texto!r}"
        nombres.setdefault(cat.sin_tildes(nombre), []).append(n)
    repetidos = {k: v for k, v in nombres.items() if len(v) > 1}
    assert not repetidos, f"dos sonidos se dicen igual: {repetidos}"
    grupos = menus_juego.grupos_de_sonidos(serie)
    titulos = [t for t, _ in grupos]
    assert titulos == [g[0] for g in cat.GRUPOS] and cat.OTROS not in titulos         # todos los grupos tienen algo, y en su orden
    assert sorted(s for _, lista in grupos for s in lista) == serie
    for titulo, lista in grupos:
        assert 4 <= len(lista) <= 40, f"{titulo}: {len(lista)} sonidos"
        assert ": " not in titulo
        claves = [cat.orden(cat.nombre(s)) for s in lista]
        assert claves == sorted(claves), f"{titulo} no está en orden alfabético"
    # el orden alfabético es el de un diccionario español: las tildes no cuentan y la eñe va detrás de la ene
    assert sorted(["Ñu", "Oca", "Ánimo", "Zapato", "Nuez", "baliza", "Ambiente"], key=cat.orden) == ["Ambiente", "Ánimo", "baliza", "Nuez", "Ñu", "Oca", "Zapato"]
    # las canciones de la radio y la música no son sonidos del juego; un archivo que alguien añada a mano no se pierde
    assert menus_juego.grupos_de_sonidos(["radio_x", "musica_y"]) == [] and "radio_cambio" in serie
    assert menus_juego.grupos_de_sonidos(["mi_sonido", "claxon"]) == [("Vehículos y conducción", ["claxon"]), (cat.OTROS, ["mi_sonido"])]
    assert cat.nombre("mi_sonido") == "Mi sonido" and cat.describir("mi_sonido") == "Sonido del juego."
    # los más importantes existen todos y no se repiten, y el glosario de la ayuda sale de aquí
    assert len(cat.IMPORTANTES) == len(set(cat.IMPORTANTES)) >= 100 and set(cat.IMPORTANTES) <= set(serie)
    assert ayuda.SONIDOS == [(s, cat.nombre(s), cat.describir(s)) for s in cat.IMPORTANTES]
    assert cat.IMPORTANTES[0] == "baliza" and cat.IMPORTANTES.index("tono_pared") < cat.IMPORTANTES.index("territorio")
    # los de orientación, que los packs no cambian, no dependen de en qué grupo estén
    orientacion = [s for s in serie if cat.es_orientacion(s)]
    assert len(orientacion) >= 50 and {"baliza", "tono_objetivo", "loc_mision", "lugar_casa", "radar", "semaforo_tic"} <= set(orientacion) and "claxon" not in orientacion


def test_la_misma_clasificacion_en_aprender_en_el_volumen_y_en_la_guia(app):
    """Mismos grupos, con los mismos nombres y en el mismo orden, y dentro los mismos sonidos en el mismo orden, en los tres sitios."""
    serie = _serie()
    patron = cat.clasificar(serie)
    assert sum(len(v) for _, v in patron) == len(serie)
    # 1. Aprender los sonidos
    partes = menus_juego.sonidos_aprender(serie)
    assert [(t, [s for s, _ in lista]) for t, lista in partes[1:]] == patron
    menus_juego.sonidos(app)
    principal = app.pila[-1]
    textos = [o.texto for o in principal.opciones]
    assert textos[0].startswith("Los más importantes: ") and textos[1] == "Buscar un sonido" and textos[-1] == "Volver"
    assert textos[2:-1] == [f"{t}: {len(v)} sonidos" for t, v in patron]
    app.cerrar(principal)
    # 2. el volumen de cada sonido
    app.cfg["vol_sonidos"].clear()
    menus_juego.volumen_sonidos(app)
    principal = app.pila[-1]
    textos = [o.texto for o in principal.opciones]
    assert textos[0] == "Buscar un sonido" and textos[1] == "Sonidos cambiados: 0" and textos[-2].startswith("Restablecer todos") and textos[-1] == "Volver"
    assert textos[2:-2] == [f"{t}: {len(v)} sonidos" for t, v in patron]
    visto = []
    for o in principal.opciones[2:-2]:
        o.accion()
        m = app.pila[-1]
        assert m.opciones[-1].texto == "Volver" and m.opciones[-2].texto.startswith("Restablecer este grupo")
        visto.append((o.texto.split(": ")[0], [_archivo(op) for op in m.opciones[:-2]]))
        for op in m.opciones[:-2]:
            assert op.texto == f"{cat.nombre(_archivo(op))}: 100 por ciento" and cat.describir(_archivo(op)) in op.ayuda
        app.cerrar(m)
    assert visto == patron
    app.cerrar(principal)
    # 3. la guía de sonidos
    import html as html_
    guia = open(rutas.data("docs", "cambiar_sonidos_es.html"), encoding="utf-8").read().split("Lista completa de sonidos</h2>")[1]
    trozos = guia.split("<h3>")[1:]
    assert [(html_.unescape(x.split("</h3>")[0]), re.findall(r"<li><code>(\w+)</code>: ", x)) for x in trozos] == patron
    for titulo, lista in patron:
        assert f"<li>{html_.escape(titulo)}: {len(lista)} sonidos.</li>" in guia
        for s in lista:
            assert f"<li><code>{s}</code>: {html_.escape(cat.nombre(s))}. {html_.escape(cat.describir(s))}" in guia, s
    assert cat.OTROS not in guia
    # 4. y la herramienta que hace el pack envolvente decide lo que es orientación con el catálogo, no con los nombres de los grupos
    fuente = open(os.path.join(rutas.base(), "herramientas", "crear_pack_envolvente.py"), encoding="utf-8").read()
    assert "cat.es_orientacion(nombre)" in fuente and "Firmas de los lugares" not in fuente


def test_aprender_los_sonidos_los_tiene_todos(app):
    """Todo archivo de los sonidos de serie sale en Aprender los sonidos, con nombre y explicación, y suena él solo."""
    serie = _serie()
    partes = menus_juego.sonidos_aprender(serie)
    assert partes[0][0] == "Los más importantes" and [s for s, _ in partes[0][1]] == list(cat.IMPORTANTES)
    vistos = {}
    for titulo, lista in partes[1:]:
        assert titulo != cat.OTROS
        for s, texto in lista:
            assert s not in vistos, f"{s} sale dos veces"
            vistos[s] = texto
            assert texto == f"{cat.nombre(s)}. {cat.describir(s)}"
    assert sorted(vistos) == serie
    for s, texto in partes[0][1]:                                # un sonido se llama igual en los dos sitios; fuera de su grupo, los de adultos lo dicen
        assert texto == (vistos[s].replace(". ", ", contenido para adultos. ", 1) if cat.es_de_adultos(s) else vistos[s]), s
    assert sum(1 for s in cat.IMPORTANTES if cat.es_de_adultos(s)) >= 10 and not cat.es_de_adultos("lugar_club") and not cat.es_de_adultos("mi_sonido")
    for s in GRABADOS_171 + TONOS_171:
        assert len(vistos[s]) > 20
    # el menú de verdad: grupos, y dentro cada sonido; Intro hace sonar ese y no el toque del menú
    menus_juego.sonidos(app)
    principal = app.pila[-1]
    assert principal.titulo == "Aprender los sonidos" and f"El juego tiene {len(serie)} sonidos" in app.voz.registro[-1] and "Buscar un sonido" in app.voz.registro[-1]
    grupos = [o for o in principal.opciones if o.texto.endswith(" sonidos")]
    assert len(grupos) == len(partes) and sum(int(o.texto.split(": ")[1].split()[0]) for o in grupos[1:]) == len(serie)
    sonados, original, total = [], app.mez.sonar, 0
    app.mez.sonar = lambda n, **k: (sonados.append((n, k.get("cat"))), original(n, **k))[1]
    try:
        for (titulo, lista), o in zip(partes, grupos):
            o.accion()
            m = app.pila[-1]
            assert m is not principal and m.opciones[-1].texto == "Volver"
            assert m.titulo == f"{titulo}, {len(lista)} sonidos" and app.voz.registro[-1].startswith(m.titulo)        # al entrar dice cuántos tiene
            if o is grupos[0]:
                app.cerrar(m)
                continue
            for op in m.opciones[:-1]:
                assert op.callado
                del sonados[:]
                op.accion()
                assert len(sonados) == 1 and sonados[0][1] == "interfaz" and vistos[sonados[0][0]] == op.texto
                total += 1
            app.cerrar(m)
    finally:
        app.mez.sonar = original
    assert total == len(serie)
    app.cerrar(principal)


def test_una_letra_salta_al_siguiente_que_empieza_por_ella_con_tilde_o_sin_ella(robot):
    app = robot.app
    m = Menu(app, "Prueba", [Opcion(t) for t in ("Zapato", "Árbol", "Barco", "Ñandú", "Nube", "Ánimo")])
    app.abrir(m)
    for letra, espera in (("a", "Árbol"), ("a", "Ánimo"), ("a", "Árbol"), ("n", "Nube"), ("ñ", "Ñandú"), ("Á", "Ánimo"), ("z", "Zapato"), ("N", "Nube")):
        robot.tecla(ord(letra) if letra.isascii() else 0, unicode=letra)
        assert m.opciones[m.i].texto == espera, (letra, m.opciones[m.i].texto)
    robot.tecla(pygame.K_x, unicode="x")                         # ninguna empieza por equis: se queda donde estaba
    assert m.opciones[m.i].texto == "Nube"
    app.cerrar(m)
    # en un grupo de Aprender los sonidos, la letra lleva al primero que empieza por ella
    menus_juego.sonidos(app)
    _ir(app, "Policía y emergencias")
    robot.tecla(pygame.K_RETURN)
    m = app.pila[-1]
    robot.tecla(pygame.K_s, unicode="s")
    assert m.opciones[m.i].texto.startswith("Sirena de ambulancia.")
    robot.tecla(pygame.K_s, unicode="s")
    assert m.opciones[m.i].texto.startswith("Sirena de policía.")
    robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_ESCAPE)


# ====================================================================== buscar
def test_buscar_un_sonido_sin_contar_tildes_ni_mayusculas():
    serie = _serie()
    con, sin, mayus = cat.buscar("policía", serie), cat.buscar("policia", serie), cat.buscar("POLICIA", serie)
    assert con == sin == mayus and len(con) >= 12
    assert con[0][0] in ("emisora", "helicoptero_policia", "policia_perdida", "sirena", "paisano") and con[0][1]          # primero, los que lo llevan en el nombre
    hallados = dict(con)
    assert hallados["sirena"] == "Policía y emergencias" and hallados["lugar_comisaria"] == "Sonidos de los lugares" and "paisano" in hallados
    assert [s for s, _ in cat.buscar("semaforo", serie)] == ["semaforo_rojo", "semaforo_verde", "semaforo_pio", "semaforo_tic"]
    assert [s for s, _ in cat.buscar("Semáforo", serie)] == ["semaforo_rojo", "semaforo_verde", "semaforo_pio", "semaforo_tic"]
    assert [s for s, _ in cat.buscar("acera derecho", serie)] == ["paso_acera1"]                 # varias palabras: las tiene todas
    assert [s for s, _ in cat.buscar("montana", serie)] == ["amb_montana"] == [s for s, _ in cat.buscar("montaña", serie)]
    assert ("timbre", "Casa, cocina y comida") in cat.buscar("timb", serie)                       # vale un trozo
    assert [s for s, _ in cat.buscar("chat_fuera", serie)] == ["chat_fuera"]                      # y el nombre del archivo
    assert "plato_servido" in dict(cat.buscar("cubiertos", serie))                                # y lo que dice la explicación
    assert cat.buscar("xyzzy", serie) == [] and cat.buscar("   ", serie) == [] and cat.buscar("", serie) == []
    assert not [s for s, _ in cat.buscar("radio", serie + ["radio_bravo"]) if s == "radio_bravo"]
    # todo sonido se encuentra por su propio nombre
    for s in serie:
        assert s in dict(cat.buscar(cat.nombre(s), serie)), s


def test_buscar_en_aprender_los_sonidos_con_el_teclado(robot):
    app = robot.app
    menus_juego.sonidos(app)
    principal = _ir(app, "Buscar un sonido")
    robot.tecla(pygame.K_RETURN)
    e = app.pila[-1]
    assert isinstance(e, EntradaTexto) and "Buscar un sonido" in app.voz.registro[-1]
    _escribir(robot, "SIRÉNA")
    robot.tecla(pygame.K_RETURN)
    m = app.pila[-1]
    esperados = cat.buscar("sirena", app.mez.sonidos)
    assert isinstance(m, Menu) and m is not principal and m.titulo == f"Sonidos con SIRÉNA, {len(esperados)} sonidos" and len(esperados) >= 4
    assert [o.texto for o in m.opciones[:-1]] == [f"{cat.nombre(s)}, del grupo {t}. {cat.describir(s)}" for s, t in esperados]
    assert any(", del grupo Policía y emergencias. " in o.texto for o in m.opciones) and any(", del grupo Ambientes y clima. " in o.texto for o in m.opciones)
    sonados, original = [], app.mez.sonar
    app.mez.sonar = lambda n, **k: (sonados.append(n), original(n, **k))[1]
    try:
        m.i = 0
        robot.tecla(pygame.K_RETURN)
    finally:
        app.mez.sonar = original
    assert sonados == [esperados[0][0]]                           # suena ese, y no el toque del menú
    robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is principal
    # lo que no existe: lo dice y se queda en el menú
    robot.tecla(pygame.K_RETURN)
    _escribir(robot, "xyzzy")
    robot.tecla(pygame.K_RETURN)
    assert app.pila[-1] is principal and "Ningún sonido tiene xyzzy" in app.voz.registro[-1]
    # cancelar la búsqueda no abre nada
    robot.tecla(pygame.K_RETURN)
    _escribir(robot, "si")
    robot.tecla(pygame.K_ESCAPE)
    assert app.pila[-1] is principal
    app.cerrar(principal)


class _Mando:
    """Un mando simulado: botones y la rueda de letras."""

    def __init__(self, app, tipo):
        self.app, self.md = app, app.mando
        self.md.simulado = True
        self.md.tipo = tipo

    def pulsar(self, b):
        self.md.boton(b, True)
        self.md.boton(b, False)

    def hasta(self, contiene):
        m = self.app.pila[-1]
        assert isinstance(m, Menu), m
        for _ in range(len(m.opciones) + 1):
            if contiene in m.opciones[m.i].texto:
                return m
            self.pulsar("abajo")
        raise AssertionError((contiene, [o.texto for o in m.opciones]))

    def escribir(self, texto):
        e = self.app.pila[-1]
        assert isinstance(e, EntradaTexto), e
        for ch in texto:
            g = next(k for k, (_, letras) in enumerate(e.GRUPOS) if ch in letras)
            while e.grupo != g:
                self.pulsar("rb")
            destino = e.GRUPOS[g][1].index(ch)
            while e.letra != destino:
                self.pulsar("abajo")
            self.pulsar("derecha")


@pytest.mark.parametrize("tipo", ("xbox", "ps"))
def test_buscar_y_ajustar_un_sonido_solo_con_el_mando(robot, tipo):
    """Con el mando, sin tocar el teclado: buscar con la rueda de letras, en los dos menús, oír, ajustar y restablecer."""
    app = robot.app
    md = _Mando(app, tipo)
    app.cfg["vol_sonidos"].clear()
    app.recargar_sonidos()
    try:
        # en Aprender los sonidos
        menus_juego.sonidos(app)
        principal = md.hasta("Buscar un sonido")
        md.pulsar("a")
        assert isinstance(app.pila[-1], EntradaTexto) and app.mando.contexto() == "pantalla" and "cruceta" in app.voz.registro[-1]
        md.escribir("gallo")
        md.pulsar("a")
        m = app.pila[-1]
        assert isinstance(m, Menu) and m.opciones[0].texto.startswith("Amanece, del grupo Menús, móvil y avisos del juego. ")
        md.pulsar("b")
        md.pulsar("b")
        assert principal not in app.pila
        # en el volumen de cada sonido
        menus_juego.volumen_sonidos(app)
        principal = md.hasta("Buscar un sonido")
        md.pulsar("a")
        md.escribir("timbre")
        md.pulsar("a")
        m = md.hasta("Timbre de casa, del grupo Casa, cocina y comida: 100 por ciento")
        antes = packs.nivel(app.mez.sonidos["timbre"])
        md.pulsar("derecha")
        md.pulsar("derecha")
        assert app.cfg["vol_sonidos"]["timbre"] == 1.2 and m.opciones[m.i].texto.endswith(": 120 por ciento, cambiado")
        assert abs(packs.nivel(app.mez.sonidos["timbre"]) / antes - 1.2) < 0.02
        md.pulsar("a")                                           # A o Equis lo hace sonar y no lo cambia
        assert app.cfg["vol_sonidos"]["timbre"] == 1.2
        md.pulsar("b")
        assert app.pila[-1] is principal
        # restablecer uno, sin teclado: la lista de los cambiados
        m = md.hasta("Sonidos cambiados: 1")
        md.pulsar("a")
        m = app.pila[-1]
        assert m.titulo == "Sonidos cambiados, 1 sonido" and m.opciones[0].texto == "Restablecer Timbre de casa, del grupo Casa, cocina y comida: está al 120 por ciento"
        md.pulsar("a")
        assert "timbre" not in app.cfg["vol_sonidos"] and app.pila[-1] is principal and "Ya no queda ningún sonido cambiado" in app.voz.registro[-1]
        assert abs(packs.nivel(app.mez.sonidos["timbre"]) / antes - 1.0) < 0.02
        md.pulsar("b")
    finally:
        app.cfg["vol_sonidos"].clear()
        app.cfg.guardar()
        app.recargar_sonidos()


# ====================================================================== el volumen de cada sonido
def test_el_volumen_de_cada_sonido_los_tiene_todos(app):
    """En Opciones, Ajustar el volumen de cada sonido están todos, cada uno en su grupo, y se pueden oír y ajustar."""
    serie = _serie()
    assert set(serie) <= set(app.mez.sonidos)
    app.cfg["vol_sonidos"].clear()
    menus_juego.volumen_sonidos(app)
    principal = app.pila[-1]
    assert "mismos grupos que en Aprender los sonidos" in app.voz.registro[-1] and "volúmenes generales" in app.voz.registro[-1]
    grupos = [o for o in principal.opciones if ": " in o.texto and o.texto.endswith(" sonidos")]
    assert not [o for o in grupos if o.texto.startswith(cat.OTROS)]
    assert sum(int(o.texto.split(": ")[1].split()[0]) for o in grupos) == len([s for s in app.mez.sonidos if cat.es_del_juego(s)]) == len(serie)
    archivos = set()
    for o in grupos:
        o.accion()
        m = app.pila[-1]
        assert app.voz.registro[-1].startswith(o.texto.replace(": ", ", "))                 # al entrar dice el grupo y cuántos tiene
        for op in m.opciones[:-2]:
            assert op.ajuste is not None and op.accion is not None and op.callado and "por ciento" in op.texto
            archivos.add(_archivo(op))
        app.cerrar(m)
    assert set(serie) == archivos
    app.cerrar(principal)
    # cada sonido, en el grupo que le toca
    grupo = {s: t for t, lista in menus_juego.grupos_de_sonidos(serie) for s in lista}
    for s in ("nevera", "cocina_cortar", "cocina_freir", "cocina_hervir", "plato_servido", "timbre", "comer", "beber"):
        assert grupo[s] == "Casa, cocina y comida"
    assert grupo["cesta"] == grupo["caja"] == "Tiendas, dinero y objetos"
    for s in TONOS_171:
        assert grupo[s] == "Jugar en línea y rol"
    for s in ("megafono", "emisora", "sirena", "multa"):
        assert grupo[s] == "Policía y emergencias"
    for s in ("amenaza_barrio", "barrio_perdido", "barrio_defendido", "territorio"):
        assert grupo[s] == "Territorios y bandas"
    for s in ("despido", "inspeccion", "factura", "titulo", "ascenso", "diploma"):
        assert grupo[s] == "Misiones, trabajo, reputación y ánimo"
    assert grupo["claxon"] == grupo["radio_cambio"] == "Vehículos y conducción" and grupo["disparo_pistola"] == "Armas, el disparo de cada una"
    assert all(grupo[s] == "Sonidos de los lugares" for s in serie if s.startswith("lugar_"))


def test_cambiados_y_restablecer_uno_un_grupo_o_todos(robot):
    """Se sabe qué está cambiado (en el menú, en cada grupo y en cada sonido) y se puede devolver a su volumen de serie
    un sonido solo, un grupo entero o todos."""
    app = robot.app
    app.cfg["vol_sonidos"].clear()
    app.recargar_sonidos()
    base = {s: packs.nivel(app.mez.sonidos[s]) for s in ("claxon", "frenazo", "sirena", "esposas", "lluvia")}

    def igual(s, f):
        return abs(packs.nivel(app.mez.sonidos[s]) / base[s] - f) < 0.02
    try:
        menus_juego.volumen_sonidos(app)
        principal = app.pila[-1]
        _ir(app, "Vehículos y conducción")
        robot.tecla(pygame.K_RETURN)
        m = app.pila[-1]
        assert app.voz.registro[-1].startswith("Vehículos y conducción, 19 sonidos.")
        m.i = next(k for k, o in enumerate(m.opciones) if o.ayuda and o.ayuda.startswith("Archivo claxon."))
        robot.tecla(pygame.K_RIGHT)
        robot.tecla(pygame.K_RIGHT)
        assert m.opciones[m.i].texto == "Claxon de coche: 120 por ciento, cambiado" and igual("claxon", 1.2)
        m.i = next(k for k, o in enumerate(m.opciones) if o.ayuda and o.ayuda.startswith("Archivo frenazo."))
        robot.tecla(pygame.K_LEFT)
        assert m.opciones[m.i].texto == "Frenazo: 90 por ciento, cambiado" and igual("frenazo", 0.9)
        assert m.titulo == "Vehículos y conducción, 19 sonidos, cambiados: 2" and m.opciones[-2].texto == "Restablecer este grupo. Cambiados: 2"
        # Suprimir devuelve uno a su volumen de serie; sobre uno que no está cambiado, lo dice
        robot.tecla(pygame.K_DELETE)
        assert "frenazo" not in app.cfg["vol_sonidos"] and igual("frenazo", 1.0) and m.opciones[m.i].texto == "Frenazo: 100 por ciento"
        assert "Frenazo vuelve al 100 por ciento" in app.voz.registro[-1]
        robot.tecla(pygame.K_DELETE)
        assert "ya está al 100 por ciento" in app.voz.registro[-1] and app.cfg["vol_sonidos"] == {"claxon": 1.2}
        m.i = len(m.opciones) - 1
        robot.tecla(pygame.K_DELETE)                               # sobre Volver no hace nada
        assert app.pila[-1] is m and app.cfg["vol_sonidos"] == {"claxon": 1.2}
        robot.tecla(pygame.K_ESCAPE)
        # otro grupo
        _ir(app, "Policía y emergencias")
        robot.tecla(pygame.K_RETURN)
        m = app.pila[-1]
        for archivo in ("sirena", "esposas"):
            m.i = next(k for k, o in enumerate(m.opciones) if o.ayuda and o.ayuda.startswith(f"Archivo {archivo}."))
            robot.tecla(pygame.K_LEFT)
            robot.tecla(pygame.K_LEFT)
        robot.tecla(pygame.K_ESCAPE)
        assert app.pila[-1] is principal and app.cfg["vol_sonidos"] == {"claxon": 1.2, "sirena": 0.8, "esposas": 0.8}
        textos = [o.texto for o in principal.opciones]
        assert "Sonidos cambiados: 3" in textos and "Vehículos y conducción: 19 sonidos, cambiados: 1" in textos and "Policía y emergencias: 12 sonidos, cambiados: 2" in textos
        assert "Ambientes y clima: 19 sonidos" in textos and "Restablecer todos. Tienes 3 sonidos ajustados" in textos
        # restablecer un grupo entero no toca los demás
        _ir(app, "Policía y emergencias")
        robot.tecla(pygame.K_RETURN)
        m = app.pila[-1]
        assert app.voz.registro[-1].startswith("Policía y emergencias, 12 sonidos, cambiados: 2.")
        m.i = len(m.opciones) - 2
        robot.tecla(pygame.K_RETURN)
        assert app.cfg["vol_sonidos"] == {"claxon": 1.2} and igual("sirena", 1.0) and igual("esposas", 1.0) and igual("claxon", 1.2)
        assert "2 sonidos de este grupo vuelven a su volumen de serie" in app.voz.registro[-1] and m.opciones[-2].texto == "Restablecer este grupo. Cambiados: 0"
        robot.tecla(pygame.K_RETURN)
        assert "no hay ningún sonido cambiado" in app.voz.registro[-1]
        robot.tecla(pygame.K_ESCAPE)
        # la lista de los cambiados, de todos los grupos: Intro devuelve uno
        packs.ajustar(app.mez, app.cfg, "lluvia", 3)
        _ir(app, "Sonidos cambiados: 2")
        robot.tecla(pygame.K_RETURN)
        m = app.pila[-1]
        assert [o.texto for o in m.opciones] == ["Restablecer Claxon de coche, del grupo Vehículos y conducción: está al 120 por ciento",
                                                 "Restablecer Lluvia, del grupo Ambientes y clima: está al 130 por ciento", "Restablecerlos todos", "Volver"]
        robot.tecla(pygame.K_RETURN)
        assert app.pila[-1] is m and app.cfg["vol_sonidos"] == {"lluvia": 1.3} and igual("claxon", 1.0) and len(m.opciones) == 3
        assert "Claxon de coche vuelve al 100 por ciento. Restablecer Lluvia" in app.voz.registro[-1]
        robot.tecla(pygame.K_ESCAPE)
        # restablecer todos
        packs.ajustar(app.mez, app.cfg, "claxon", -2)
        _ir(app, "Restablecer todos. Tienes 2 sonidos ajustados")
        robot.tecla(pygame.K_RETURN)
        assert app.cfg["vol_sonidos"] == {} and all(igual(s, 1.0) for s in base) and "Todos los sonidos vuelven a su volumen normal" in app.voz.registro[-1]
        assert "Sonidos cambiados: 0" in [o.texto for o in principal.opciones]
        _ir(app, "Sonidos cambiados: 0")
        robot.tecla(pygame.K_RETURN)
        assert app.pila[-1] is principal and "No tienes ningún sonido cambiado" in app.voz.registro[-1]
        robot.tecla(pygame.K_ESCAPE)
    finally:
        app.cfg["vol_sonidos"].clear()
        app.cfg.guardar()
        app.recargar_sonidos()


def test_una_configuracion_antigua_conserva_sus_volumenes(app, tmp_path):
    """Los volúmenes que el jugador tenía cambiados se guardan por nombre de archivo, no por grupo: reclasificar no los pierde."""
    antigua = {"vol_sonidos": {"claxon": 1.4, "lugar_casa": 0.5, "pasan_horas": 1.2, "campanadas": 0.7, "fama": 1.6, "amb_ciudad": 0.6,
                               "sonido_que_ya_no_existe": 1.5, "paso_acera0": "estropeado"},
               "vol_efectos": 0.7, "vol_interfaz": 0.4, "pack_sonidos": ""}
    archivo = tmp_path / "config.json"
    archivo.write_text(json.dumps(antigua), encoding="utf-8")
    cfg = config.Config(str(archivo))
    assert cfg["vol_sonidos"] == antigua["vol_sonidos"] and cfg["vol_efectos"] == 0.7 and cfg["vol_interfaz"] == 0.4
    app.cfg["vol_sonidos"].clear()
    app.recargar_sonidos()
    reales = ("claxon", "lugar_casa", "pasan_horas", "campanadas", "fama", "amb_ciudad")
    base = {s: packs.nivel(app.mez.sonidos[s]) for s in reales + ("paso_acera0",)}
    guardado, app.cfg.v["vol_sonidos"] = app.cfg.v["vol_sonidos"], cfg["vol_sonidos"]
    try:
        app.recargar_sonidos()
        for s in reales:                                         # cada uno suena al volumen que el jugador le puso
            assert abs(packs.nivel(app.mez.sonidos[s]) / base[s] - antigua["vol_sonidos"][s]) < 0.02, s
        assert abs(packs.nivel(app.mez.sonidos["paso_acera0"]) / base["paso_acera0"] - 1.0) < 0.02          # lo que no es un número no rompe nada
        assert packs.factor(app.cfg, "paso_acera0") == 1.0 and not packs.cambiado(app.cfg, "paso_acera0") and packs.factor(app.cfg, "claxon") == 1.4
        # y el menú nuevo los enseña como cambiados, cada uno en su grupo de ahora
        menus_juego.volumen_sonidos(app)
        principal = app.pila[-1]
        textos = [o.texto for o in principal.opciones]
        assert "Sonidos cambiados: 6" in textos
        for linea in ("Vehículos y conducción: 19 sonidos, cambiados: 1", "Sonidos de los lugares: 37 sonidos, cambiados: 1", "Menús, móvil y avisos del juego: 17 sonidos, cambiados: 2",
                      "Misiones, trabajo, reputación y ánimo: 14 sonidos, cambiados: 1", "Ambientes y clima: 19 sonidos, cambiados: 1"):
            assert linea in textos, linea
        _ir(app, "Sonidos de los lugares")
        principal.opciones[principal.i].accion()
        m = app.pila[-1]
        assert "Casa: 50 por ciento, cambiado" in [o.texto for o in m.opciones]
        app.cerrar(m)
        app.cerrar(principal)
        # al guardar no se pierde ninguno, tampoco el de un sonido que este juego no tiene
        cfg.guardar()
        assert config.Config(str(archivo))["vol_sonidos"] == antigua["vol_sonidos"]
    finally:
        app.cfg.v["vol_sonidos"] = guardado
        app.cfg["vol_sonidos"].clear()
        app.cfg.guardar()
        app.recargar_sonidos()


def test_ningun_sonido_queda_fuera_de_los_volumenes_de_opciones(app):
    """Todo lo que suena pasa por una de las cuatro clases de volumen del mezclador, cada una con su control en Opciones
    (además del volumen general y del de las señales de ayuda), y no hay en el código ninguna clase que no exista."""
    clases = {"efectos", "ambiente", "musica", "interfaz"}
    assert clases | {"maestro", "senales"} == set(app.mez.vols)
    for clave in ("vol_maestro", "vol_efectos", "vol_ambiente", "vol_musica", "vol_interfaz", "vol_senales"):
        assert clave in config.POR_DEFECTO
    assert audio.Canal().cat in clases                      # la clase de quien no dice ninguna
    usadas = set()
    carpeta = os.path.dirname(audio.__file__)
    for f in os.listdir(carpeta):
        if f.endswith(".py"):
            with open(os.path.join(carpeta, f), encoding="utf-8") as fh:
                usadas |= set(re.findall(r'\bcat="([^"]*)"', fh.read()))
    assert usadas and usadas <= clases, usadas - clases
    # y Opciones, Sonido y música, tiene un control para cada una
    fuente = open(menus_juego.__file__, encoding="utf-8").read()
    for clave in ("vol_maestro", "vol_efectos", "vol_ambiente", "vol_musica", "vol_interfaz", "vol_senales"):
        assert f'vol("{clave}"' in fuente, clave
    assert "Ajustar el volumen de cada sonido" in fuente
    # un sonido ajustado por el jugador cambia de verdad, también uno de los nuevos
    antes = packs.nivel(app.mez.sonidos["timbre"])
    packs.ajustar(app.mez, app.cfg, "timbre", -1)
    assert packs.nivel(app.mez.sonidos["timbre"]) < antes
    app.cfg["vol_sonidos"].clear()
    app.recargar_sonidos()
    assert abs(packs.nivel(app.mez.sonidos["timbre"]) / antes - 1.0) < 0.02


def test_la_documentacion_cuenta_lo_de_los_sonidos():
    manual = open(rutas.data("docs", "manual_es.html"), encoding="utf-8").read()
    guia = open(rutas.data("docs", "cambiar_sonidos_es.html"), encoding="utf-8").read()
    novedades = open(rutas.data("docs", "novedades_es.html"), encoding="utf-8").read()
    leeme = open(os.path.join(rutas.base(), "README.md"), encoding="utf-8").read()
    assert "Aprender los sonidos" in manual and "Los más importantes" in manual
    assert "BigSoundBank" in guia or "bigsoundbank" in guia
    for n in _serie():
        assert f"<code>{n}</code>" in guia, f"la guía de sonidos no nombra {n}"
    assert "Otros sonidos" not in guia
    # los grupos, con su nombre de ahora, en el manual; y cómo se busca y cómo se restablece
    import html as html_
    for titulo, _, _ in cat.GRUPOS:
        assert html_.escape(titulo) in manual or titulo in manual, f"el manual no nombra el grupo {titulo}"
    for frase in ("Buscar un sonido", "Sonidos cambiados", "Restablecer este grupo", "Restablecer todos", "orden alfabético", "rueda de letras", "Suprimir"):
        assert frase in manual, frase
    for viejo in ("Firmas de los lugares", "Puertas, horas del día y vida honrada", "La compra y la cocina", "Jugar con amigos y en un servidor"):
        assert viejo not in manual and viejo not in guia and viejo not in leeme, viejo
    assert "Buscar un sonido" in guia and "Buscar un sonido" in novedades
    assert "catalogo_sonidos" in leeme and "Suprimir" in open(rutas.data("docs", "teclas_es.html"), encoding="utf-8").read()
