"""Trabajo 1.7.1, tanda 11: lo que contaron los jugadores tras la 1.7.0 (segunda ronda)."""
import math
import os

import pygame
import pytest

from juego import mundo as M
from juego.menus import Menu


def _coche(p, x, y, modelo="utilitario"):
    """Te pone al volante de un coche en la calzada más cercana a ese punto."""
    px, py, d = p.mundo.plaza_en(x, y)
    v = p.crear_vehiculo(modelo, px, py, d, None)
    p._subir(v, False, callar=True)
    return v


def _elegir(robot, empieza):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(empieza))
    robot.tecla(pygame.K_RETURN)


def _conexiones(p, tipos=("salida",)):
    return [(m, l) for m in p.mapas.values() for l in m.lugares.values() if l.tipo in tipos and l.get("a_mapa")]


def _puntos_de_llegada(m, l, lejos=130.0):
    """Desde dónde se llega a una salida: por los cuatro lados, a poco más de una manzana, sin salirse del mapa."""
    pts = []
    for dx, dy in ((lejos, 0), (-lejos, 0), (0, lejos), (0, -lejos)):
        x, y = max(10.0, min(m.ancho - 10.0, l.x + dx)), max(10.0, min(m.alto - 10.0, l.y + dy))
        if math.hypot(x - l.x, y - l.y) > 50 and all(math.hypot(x - a, y - b) > 30 for a, b in pts):
            pts.append((x, y))
    return pts


def _limpio(p, m, x, y):
    if p.j.veh:
        p.salir_vehiculo(forzado=True)
    p.vehiculos[:] = []
    p.personas[:] = []
    p.j.estrellas = 0
    p.gps = None
    p.cambiar_mapa(m.id, x, y)
    p.vehiculos[:] = []
    p.personas[:] = []


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


# ------------------------------------------------------------------ A1. salir por carretera
def test_por_todas_las_salidas_se_sale_en_vehiculo_llegando_por_cualquier_lado(robot):
    """El piloto te lleva hasta cada salida del mundo desde varios lados; al llegar se dice qué hacer, Intro abre el
    viaje sin bajarse y la carretera te deja, con tu vehículo, en la otra localidad."""
    p = robot.nueva_partida()
    p.cfg["conduccion"], p.cfg["sucesos"], p.cfg["piloto_gps"] = "asistida", False, True
    salidas = _conexiones(p)
    assert len(salidas) >= 12
    malas, hechas = [], 0
    for m, l in salidas:
        dest = p.lug(l.get("a_lugar"))
        assert dest is not None and dest.tipo == "salida" and p.lug(dest.get("a_lugar")) is l, f"{l.id}: la carretera no vuelve"
        for k, (x, y) in enumerate(_puntos_de_llegada(m, l)):
            _limpio(p, m, x, y)
            v = _coche(p, x, y)
            robot.frames(5)
            n0 = len(robot.app.voz.registro)
            p.gps_a_lugar(l, callar=True)
            for _ in range(240):
                robot.frames(15)
                p.j.estrellas = 0
                if not p.gps:
                    break
            robot.frames(75)
            dicho = " | ".join(robot.app.voz.registro[n0:])
            caso = (m.id, l.id, k)
            if p.gps or abs(v.vel) > 3 or f"Has llegado a {l.nombre}. Ya estás en el sitio" not in dicho \
                    or "pulsa Intro para tomar la carretera a " + p.mapas[dest.mapa].nombre not in dicho:
                malas.append((caso, "no llega o no lo dice", round(math.hypot(l.x - v.x, l.y - v.y)), dicho[-300:]))
                continue
            assert p.lugar_al_alcance() is l, caso
            v.vel = 0.0
            n0 = len(robot.app.voz.registro)
            robot.tecla(pygame.K_RETURN)
            cima = robot.app.pila[-1]
            if not (isinstance(cima, Menu) and cima.opciones[0].texto.startswith("Tomar la carretera hasta " + p.mapas[dest.mapa].nombre)):
                malas.append((caso, "Intro no abre el viaje", " | ".join(robot.app.voz.registro[n0:])[-300:]))
                continue
            robot.tecla(pygame.K_RETURN)
            robot.frames(3)
            if p.mundo.id != dest.mapa or p.j.veh is not v or p.mundo.superficie(v.x, v.y) != "calzada":
                malas.append((caso, "no viaja", p.mundo.id))
                continue
            hechas += 1
    assert not malas, malas
    assert hechas >= len(salidas) * 2


def test_en_cualquier_punto_de_la_calzada_junto_a_una_salida_intro_es_la_salida(robot):
    """Aunque haya otro lugar un poco más cerca (un mirador, una parada), al volante y a tiro de la salida, Intro es la salida."""
    p = robot.nueva_partida()
    for m, l in _conexiones(p):
        _limpio(p, m, l.x, l.y)
        v = _coche(p, l.x, l.y)
        n = 0
        for dx in range(-16, 17, 2):
            for dy in range(-16, 17, 2):
                x, y = l.x + dx, l.y + dy
                if math.hypot(dx, dy) > 16 or m.superficie(x, y) != "calzada":
                    continue
                v.x, v.y = x, y
                assert p.lugar_al_alcance() is l, (l.id, dx, dy, p.lugar_al_alcance().id)
                n += 1
        assert n > 20, (l.id, n)                                 # hay calzada de sobra a su alcance: no hace falta subirse a la acera


def test_de_viaje_a_otra_localidad_el_gps_no_manda_al_este_cuando_ya_estas_en_la_salida(robot):
    """Lo que contaban: en coche, parado en la salida, el GPS decía «queda al este» y a pie pedía un vehículo."""
    p = robot.nueva_partida()
    m = p.mapas["puerto_bravo"]
    l = m.lugares["salida_este"]
    otro = p.lug(l.get("a_lugar"))
    final = next(x for x in p.mapas[otro.mapa].lugares.values() if x.tipo not in ("salida", "estacion"))
    _limpio(p, m, l.x - 60, l.y)
    v = _coche(p, l.x - 4, l.y + 6)
    p.gps_a_lugar(final, callar=True)
    assert p.gps["final"] == final.id and p._lugar_del_gps() is l       # al volante, por carretera
    robot.frames(40)
    dicho = robot.dicho()
    assert f"Has llegado a {l.nombre}. Ya estás en el sitio: no hace falta acercarse más. Sin bajarte del vehículo, pulsa Intro para tomar la carretera a {p.mapas[otro.mapa].nombre}." in dicho
    n0 = len(robot.app.voz.registro)
    p.repetir_gps()                                              # al pedir que lo repita, lo mismo: ni «al este» ni metros
    rep = robot.app.voz.registro[-1]
    assert rep.startswith(f"Estás en {l.nombre}.") and "pulsa Intro" in rep and "metros" not in rep and "queda" not in rep
    robot.frames(120)                                            # y no lo repite sin parar
    assert sum("Has llegado" in t for t in robot.app.voz.registro[n0:]) == 0
    # a pie en la misma salida: explica que es con vehículo y te guía al autobús
    p.salir_vehiculo(forzado=True)
    p.teletransportar(l.x, l.y)
    robot.frames(40)
    n0 = len(robot.app.voz.registro)
    robot.tecla(pygame.K_RETURN)
    t = " | ".join(robot.app.voz.registro[n0:])
    assert "solo en un vehículo" in t and "pulsa Intro sin bajarte" in t and "A pie se viaja en autobús" in t
    assert p._lugar_del_gps().tipo == "estacion" and p.gps["final"] == final.id
    # sin viaje en marcha, a pie, dice dónde está la estación
    p.gps = None
    robot.tecla(pygame.K_RETURN)
    assert "desde " + next(e.nombre for e in m.lugares.values() if e.tipo == "estacion") in robot.app.voz.registro[-1]
    # y de vuelta al volante, Intro viaja
    p._subir(v, False, callar=True)
    v.x, v.y, v.vel = l.x - 4, l.y + 6, 0.0
    robot.tecla(pygame.K_RETURN)
    _elegir(robot, "Tomar la carretera")
    assert p.mundo.id == otro.mapa and p.j.veh is v


def test_al_volante_se_va_por_carretera_aunque_haya_que_cruzar_varias_localidades(robot):
    """Antes, si el destino no era una localidad vecina, el GPS mandaba a la estación de autobuses también en coche."""
    p = robot.nueva_partida()
    por_tierra = [m for m in p.mapas.values() if m.tipo != "mar" and any(l.tipo == "salida" for l in m.lugares.values())]
    assert len(por_tierra) >= 6
    n = 0
    for a in por_tierra:
        _limpio(p, a, a.ancho / 2, a.alto / 2)
        _coche(p, a.ancho / 2, a.alto / 2)
        for b in por_tierra:
            if b is a or p.saltos_por_tierra(a.id, b.id) is None:
                continue
            con = p.conexion_hacia(b.id)
            assert con is not None and con.tipo == "salida", (a.id, b.id, con and con.tipo)
            n += 1
        p.salir_vehiculo(forzado=True)
        for b in por_tierra:                                     # a pie, el autobús
            if b is not a and any(l.tipo == "estacion" for l in a.lugares.values()) and any(l.tipo == "estacion" for l in b.lugares.values()):
                assert p.conexion_hacia(b.id).tipo == "estacion", (a.id, b.id)
    assert n >= 30


# ------------------------------------------------------------------ A2. el camión del transporte
def _empezar_transporte(robot, p, destino=None):
    """Al volante de un camión en el centro de Puerto Bravo, con la J. Si se pide, con ese lugar de destino."""
    m = p.mapas["puerto_bravo"]
    _limpio(p, m, m.ancho / 2, m.alto / 2)
    v = _coche(p, m.ancho / 2, m.alto / 2, "camion")
    robot.frames(5)
    robot.tecla(pygame.K_j)
    t = p.trabajo
    assert t and t["tipo"] == "camion" and t["veh"] is v
    if destino is not None:
        t.update(lugar=destino, texto=f"Transporte: lleva la carga a {destino.nombre}, en {p.mapas[destino.mapa].nombre}, sin bajarte del camión.")
        p.gps_a_lugar(destino, auto=True, callar=True)
    return v, t


def test_el_camion_del_transporte_va_siempre_por_carretera_y_lo_explica(robot):
    """Lo que contaban: con destinos que no eran la localidad vecina, el GPS mandaba el camión a la estación de autobuses."""
    p = robot.nueva_partida()
    v, t = _empezar_transporte(robot, p)
    dicho = robot.dicho()
    assert "La carga ya va en el camión: no hay que recoger nada." in dicho and "sin bajarte, pulsa Intro para tomar la carretera" in dicho
    assert "Se entrega sola al parar delante del destino" in dicho and "si dejas el camión, se acaba el trabajo" in dicho
    destinos = [m for m in p.mapas.values() if m.id != "puerto_bravo" and m.tipo != "mar" and any(l.tipo == "salida" for l in m.lugares.values())]
    assert len(destinos) >= 6
    for m in destinos:                                           # a cualquier localidad con carretera, el camino empieza en una salida
        l = next(x for x in m.lugares.values() if x.tipo in ("tienda", "taller", "negocio", "comida", "desguace", "armeria", "pescaderia"))
        t.update(lugar=l)
        n0 = len(robot.app.voz.registro)
        p.gps_a_lugar(l, auto=True)
        assert p._lugar_del_gps().tipo == "salida", (m.id, p._lugar_del_gps().tipo)
        assert "Coge la carretera en un vehículo" in " ".join(robot.app.voz.registro[n0:]) and "autobús" not in " ".join(robot.app.voz.registro[n0:])
    # en la estación, con el camión, no te manda bajarte: te devuelve a la carretera
    est = p.mapas["puerto_bravo"].lugares["estacion_pb"]
    v.x, v.y, v.vel = est.x, est.y + 4, 0.0
    p.gps = None
    robot.tecla(pygame.K_RETURN)
    assert "La carga no viaja en autobús" in robot.dicho() and p.trabajo is t and p._lugar_del_gps().tipo == "salida"
    # si se quita el GPS, la G vuelve a marcar el destino del trabajo
    robot.tecla(pygame.K_g, pygame.KMOD_SHIFT)
    assert p.gps is None
    robot.tecla(pygame.K_g)
    assert p.gps and p.gps["final"] == t["lugar"].id and "Transporte: lleva la carga" in robot.dicho()
    # y si te bajas, se dice claro que el servicio se acaba
    p.salir_vehiculo(forzado=True)
    robot.frames(3)
    assert p.trabajo is None and "La carga se queda sin entregar" in robot.dicho()


def test_el_transporte_entero_hasta_otra_localidad_que_no_es_vecina(robot):
    """El trabajo jugado de punta a punta: de Puerto Bravo a San Lucero, cruzando Cala Brava, sin tocar el volante y
    pulsando Intro en cada salida. Se cobra al parar delante del destino y llega otro encargo."""
    p = robot.nueva_partida()
    p.cfg["conduccion"], p.cfg["sucesos"], p.cfg["piloto_gps"] = "asistida", False, True
    destino = next(l for l in p.mapas["san_lucero"].lugares.values() if l.tipo in ("tienda", "taller", "negocio", "comida"))
    assert p.saltos_por_tierra("puerto_bravo", "san_lucero") == 2
    v, t = _empezar_transporte(robot, p, destino)
    dinero = p.j.dinero
    recorrido = ["puerto_bravo"]
    for _ in range(1500):
        robot.frames(15)
        p.j.estrellas = 0
        if p.trabajo is None or p.trabajo.get("hechas"):
            break
        if p.mundo.id != destino.mapa and p.gps and p.gps.get("avisado") is not None and abs(v.vel) < 1:      # parado en la salida: Intro, e Intro
            assert "pulsa Intro para tomar la carretera" in robot.dicho()
            robot.tecla(pygame.K_RETURN)
            _elegir(robot, "Tomar la carretera")
            recorrido.append(p.mundo.id)
            assert p.j.veh is v and p.trabajo is t and p.gps and p.gps["auto"]
    assert len(recorrido) == 3 and recorrido[1] in ("cala_brava", "villaseca") and recorrido[2] == "san_lucero", (recorrido, robot.dicho()[-400:])
    assert p.trabajo and p.trabajo["hechas"] == 1 and p.j.dinero > dinero, robot.dicho()[-400:]
    assert f"Carga entregada en {destino.nombre}" in " | ".join(robot.app.voz.registro[-25:])
    assert p.trabajo["lugar"] is not destino and p.trabajo["lugar"].mapa != p.mundo.id       # el siguiente encargo, a otra localidad


# ------------------------------------------------------------------ A3. de quién es cada sitio
def test_los_textos_fijos_que_nombran_a_una_banda_cambian_con_el_dueno(robot):
    p = robot.nueva_partida()
    j = p.j
    m = p.mapas["puerto_bravo"]
    b = next(x for x in m.barrios if x["id"] == "puerto")
    g = m.lugares["guarida"]
    assert b.get("banda") == "Los Calaveras" and g.nombre == "Guarida de Los Calaveras" and "Mejor no acercarse" in g.desc
    assert p.barrio_desc(b).endswith("Territorio de la banda de Los Calaveras.")
    j.territorios.append("puerto")                               # lo conquistas
    assert g.nombre == "Antigua guarida de Los Calaveras" and "ya no mandan" in g.desc
    assert "Calaveras" not in p.barrio_desc(b) and "Territorio tuyo" in p.barrio_desc(b)
    j.territorios.remove("puerto")                               # te lo quita otra banda (reconquista)
    j.barrios_banda["puerto"] = "Los Cuervos"
    assert g.nombre == "Antigua guarida de Los Calaveras" and p.barrio_desc(b).endswith("Territorio de la banda de Los Cuervos.")
    j.barrios_banda["puerto"] = "Los Calaveras"                  # y si vuelven los de siempre, todo como al principio
    assert g.nombre == "Guarida de Los Calaveras" and p.barrio_desc(b).endswith("Territorio de la banda de Los Calaveras.")
    j.barrios_banda.clear()


def test_con_todo_conquistado_ningun_texto_dice_que_manda_otro(robot):
    """Descripciones de barrios y de lugares, la tecla N y el tablón de la comisaría, en todas las localidades."""
    import re
    from juego import sistemas
    p = robot.nueva_partida()
    j = p.j
    j.banda_nombre = "Los Nuestros"
    antes = {l.id: (l.nombre, l.desc) for l in p.lugares.values()}
    for m in p.mapas.values():
        for b in m.barrios:
            if b["id"] not in j.territorios:
                j.territorios.append(b["id"])
    presente = re.compile(r"Territorio de la banda|[Aa]quí manda (?!Los Nuestros)|Es el barrio de |Lo controla |se juntan las motos|suben y bajan las motos|^Guarida de |El desguace de la Peña|Se busca a miembros")
    cambiados = 0
    for m in p.mapas.values():
        if m.tipo == "mar":
            continue
        _limpio(p, m, m.ancho / 2, m.alto / 2)
        textos = [p.barrio_desc(b, m) for b in m.barrios]
        textos += [l.nombre for l in m.lugares.values()] + [l.desc for l in m.lugares.values()]
        textos += sistemas.tablon_policia(p)
        for b in m.barrios:
            n0 = len(robot.app.voz.registro)
            p.teletransportar((b["i"][0] + 0.5) * M.B, (b["j"][0] + 0.5) * M.B)
            p.describir_aqui()
            textos += robot.app.voz.registro[n0:]
            if m.tipo == "ciudad":
                assert "Territorio tuyo: aquí manda Los Nuestros." in p.barrio_desc(b, m)
        malos = [t for t in textos if presente.search(t)]
        assert not malos, (m.id, malos)
        cambiados += sum(1 for l in m.lugares.values() if (l.nombre, l.desc) != antes[l.id])
    assert cambiados >= 4                                         # la guarida, el bingo y los dos de Bahía del Ocaso
    j.territorios.clear()
    assert all((l.nombre, l.desc) == antes[l.id] for l in p.lugares.values())


def test_dos_lugares_no_comparten_puerta(robot):
    """Un mod ponía su salida por carretera en el mismo punto que un mirador, y una carrera en el de una mansión: Intro solo abría uno."""
    p = robot.nueva_partida()
    for m in p.mapas.values():
        ls = list(m.lugares_todos.values())
        for a in range(len(ls)):
            for b in range(a + 1, len(ls)):
                assert math.hypot(ls[a].x - ls[b].x, ls[a].y - ls[b].y) >= 3.0, (m.id, ls[a].id, ls[b].id)


# ------------------------------------------------------------------ A4. «no se me actualiza»
class _Lectura:
    """Una descarga simulada: nunca se sale a la red."""

    def __init__(self, datos, cortar=None):
        self.datos, self.pos, self.cortar, self.status = datos, 0, cortar, 200

    def read(self, n=-1):
        if self.cortar is not None and self.pos >= self.cortar:
            raise OSError("conexión cortada")
        trozo = self.datos[self.pos:self.pos + (n if n and n > 0 else len(self.datos))]
        self.pos += len(trozo)
        return trozo

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _info_falsa(datos):
    import hashlib
    from juego import actualizador as A
    return A.Info("99.0.0", "PuertoBravo_v99.0.0.zip", hashlib.sha256(datos).hexdigest(), len(datos), ["https://ejemplo.invalid/a.zip", "https://ejemplo.invalid/b.zip"], "", "servidor")


def _zip_juego(con_exe=True):
    import io
    import zipfile
    from juego import actualizador as A
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        if con_exe:
            z.writestr(A.EJECUTABLE, b"MZ" + b"x" * 2000)
        z.writestr("data/datos/ciudad.json", "{}")
    return b.getvalue()


def test_actualizar_cada_fallo_corriente_dice_su_motivo_y_que_hacer(tmp_path, monkeypatch):
    """Antivirus, carpeta sin permiso, disco lleno, descarga cortada y filtro de red: cada uno con su frase, y ninguno
    culpa a la conexión cuando el problema está en el disco. Todo simulado: ni red ni carpetas reales."""
    import builtins
    from juego import actualizador as A
    datos = _zip_juego()
    info = _info_falsa(datos)
    carpeta = str(tmp_path / "actualizacion")
    abrir = lambda url, tiempo=0, desde=0: _Lectura(datos)       # noqa: E731
    # lo normal: baja, comprueba y deja el ZIP
    assert os.path.isfile(A.descargar(info, carpeta, abrir=abrir))
    de_verdad = builtins.open

    def abrir_con(error):
        def falso(ruta, modo="r", *a, **k):
            if str(ruta).endswith(".parcial") and ("w" in modo or "a" in modo):
                raise error
            return de_verdad(ruta, modo, *a, **k)
        return falso
    # 1. carpeta protegida o acceso controlado a carpetas: Windows no deja escribir
    monkeypatch.setattr(builtins, "open", abrir_con(PermissionError(13, "Acceso denegado")))
    with pytest.raises(A.ErrorDisco) as e:
        A.descargar(info, carpeta, abrir=abrir)
    monkeypatch.setattr(builtins, "open", de_verdad)
    assert "Windows no deja escribir en la carpeta del juego" in str(e.value) and "Documentos" in str(e.value) and "Actualizar a mano" in str(e.value) and "conexión" not in str(e.value)
    # 2. el antivirus retiene el archivo (otro programa lo está usando)
    en_uso = PermissionError(13, "en uso")
    en_uso.winerror = 32
    monkeypatch.setattr(builtins, "open", abrir_con(en_uso))
    with pytest.raises(A.ErrorDisco) as e:
        A.descargar(info, carpeta, abrir=abrir)
    monkeypatch.setattr(builtins, "open", de_verdad)
    assert "antivirus" in str(e.value) and "abierto dos veces" in str(e.value)

    # 3. el disco se llena a media descarga
    class _Lleno:
        def __init__(self, f):
            self.f = f

        def write(self, b):
            raise OSError(28, "No queda espacio en el dispositivo")

        def __enter__(self):
            return self

        def __exit__(self, *a):
            self.f.close()
            return False

    def abrir_lleno(ruta, modo="r", *a, **k):
        f = de_verdad(ruta, modo, *a, **k)
        return _Lleno(f) if str(ruta).endswith(".parcial") and modo == "wb" else f
    monkeypatch.setattr(builtins, "open", abrir_lleno)
    with pytest.raises(A.ErrorDisco) as e:
        A.descargar(info, carpeta, abrir=abrir)
    monkeypatch.setattr(builtins, "open", de_verdad)
    assert "El disco se ha llenado" in str(e.value) and "Libera espacio" in str(e.value)
    assert not os.path.exists(os.path.join(carpeta, info.archivo + ".parcial"))        # no deja restos
    # 4. la descarga se corta siempre en el mismo punto y no se puede retomar
    with pytest.raises(A.ErrorRed) as e:
        A.descargar(info, carpeta, abrir=lambda url, tiempo=0, desde=0: _Lectura(datos, cortar=0))
    assert "Comprueba la conexión a internet" in str(e.value) and "AdGuard" in str(e.value) and "excepciones" in str(e.value)

    # 5. un filtro de red bloquea la consulta de versión
    def bloqueado(url, tiempo=0, desde=0):
        raise OSError("bloqueado por el filtro")
    with pytest.raises(A.ErrorRed) as e:
        A.comprobar("ambas", abrir=bloqueado)
    assert "AdGuard" in str(e.value) and "antivirus" in str(e.value)
    # 6. el antivirus pone en cuarentena el programa recién sacado del paquete
    ruta_zip = str(tmp_path / "v.zip")
    with open(ruta_zip, "wb") as f:
        f.write(datos)
    quitar = os.path.isfile
    monkeypatch.setattr(os.path, "isfile", lambda r: False if str(r).endswith(A.EJECUTABLE) else quitar(r))
    with pytest.raises(A.ErrorDisco) as e:
        A.extraer(ruta_zip, str(tmp_path / "nueva"))
    monkeypatch.setattr(os.path, "isfile", quitar)
    assert "cuarentena" in str(e.value) and "excepciones del antivirus" in str(e.value)
    # ... y un paquete que de verdad no trae el juego sigue siendo otra cosa
    with open(ruta_zip, "wb") as f:
        f.write(_zip_juego(con_exe=False))
    with pytest.raises(A.ErrorFirma):
        A.extraer(ruta_zip, str(tmp_path / "nueva2"))


def test_actualizar_antes_de_empezar_avisa_de_la_carpeta_protegida_y_del_juego_abierto_dos_veces(robot, tmp_path, monkeypatch):
    from juego import actualizador as A, menus_actualizar
    app = robot.app
    programa = tmp_path / "PuertoBravo"
    (programa / "data" / "actualizacion" / "nueva").mkdir(parents=True)
    monkeypatch.setattr(A, "puede_instalar", lambda: True)
    monkeypatch.setattr(A, "carpeta_programa", lambda: str(programa))
    info = _info_falsa(_zip_juego())
    # carpeta en la que no se puede escribir: se dice antes de descargar nada
    app.act_libre, app.act_escribible = 10 * 1024 ** 3, False
    menus_actualizar.ofrecer(app, info)
    oferta = app.pila[-1]
    _elegir(robot, "Descargar e instalar")
    dicho = robot.app.voz.registro[-1]
    assert app.pila[-1] is oferta and "Windows no deja escribir en la carpeta del juego" in dicho and "Actualizar a mano" in dicho
    robot.tecla(pygame.K_ESCAPE)
    # el juego abierto dos veces: no se cierra para instalar, y la descarga se conserva
    assert A.copias_del_juego(["PuertoBravo.exe", "explorer.exe", "puertobravo.exe"]) == 2 and A.copias_del_juego(["explorer.exe"]) == 1
    nueva = str(programa / "data" / "actualizacion" / "nueva")
    problemas = A.problemas_para_instalar(nueva, str(programa), libre=10 * 1024 ** 3, tareas=set(), servidores=[], copias=2)
    assert len(problemas) == 1 and "abierto dos veces" in problemas[0] and "cierra la otra ventana" in problemas[0]
    assert A.problemas_para_instalar(nueva, str(programa), libre=10 * 1024 ** 3, tareas=set(), servidores=[], copias=1) == []
    app.act_comprobar = lambda carpeta: problemas
    app.act_version = "99.0.0"
    bat = str(programa / "data" / "actualizacion" / "instalar_actualizacion.bat")
    menus_actualizar._instalar(app, bat)
    assert app.activo is not False and "abierto dos veces" in robot.app.voz.registro[-1] and app.act_lista == (bat, "99.0.0")


def test_actualizar_a_mano_esta_en_el_menu_con_sus_pasos_y_en_el_manual(robot, monkeypatch):
    from juego import actualizador as A, menus_actualizar, rutas
    app = robot.app
    abiertos = []
    monkeypatch.setattr(os, "startfile", lambda r: abiertos.append(r), raising=False)
    app.act_sin_red = "No se pudo conectar con el servidor del juego."
    menus_actualizar.opciones(app)
    m = app.pila[-1]
    assert any(o.texto.startswith("Aviso: al abrir el juego no se pudo buscar") for o in m.opciones)
    _elegir(robot, "Actualizar a mano")
    pasos = app.pila[-1]
    textos = [o.texto for o in pasos.opciones]
    assert textos[0].startswith("Uno.") and textos[1].startswith("Dos.") and textos[2].startswith("Tres.") and textos[3].startswith("Cuatro.")
    assert "reemplazar" in textos[2] and "tus partidas" in textos[2]
    _elegir(robot, "Abrir la página de descargas")
    assert abiertos == [A.PAGINA_DESCARGAS] and A.PAGINA_DESCARGAS.startswith("https://github.com/")
    _elegir(robot, "Abrir la carpeta del juego")
    assert abiertos[-1] == A.carpeta_programa()
    manual = open(os.path.join(rutas.DOCS, "manual_es.html"), encoding="utf-8").read()
    assert "Actualizar a mano" in manual and "releases/latest" in manual and "reemplazar" in manual


# ------------------------------------------------------------------ B5. disparar desde un vehículo
def _calle_vacia(robot, **opciones):
    p = robot.nueva_partida()
    for k, v in dict(sucesos=False, patrullas_calle=False, ambulancias=False, charla_peatones="nada", **opciones).items():
        p.cfg[k] = v
    p.t_evento = 1e9
    for v in [v for v in p.vehiculos if v is not p.j.veh]:
        p.quitar_vehiculo(v)
    p.personas = []
    p.t_poblar = 1e9
    return p


def _persona(p, tipo, dx, dy=0.0, nombre=None, **attrs):
    from juego.entidades import Persona
    x, y = p.pos()
    q = Persona(tipo, *p.mundo.punto_libre(x + dx, y + dy), nombre)
    for k, v in attrs.items():
        setattr(q, k, v)
    p.personas.append(q)
    return q


def test_disparar_desde_el_vehiculo_se_explica_cuando_viene_a_cuento(robot):
    from juego import ayuda
    p = _calle_vacia(robot, invulnerable=True)
    v = _coche(p, *p.pos())
    e = _persona(p, "enemigo", 30, nombre="Matón", arma="pistola", hostil=True, estado="ataca", t_disparo=99.0, tag="mision")
    robot.frames(30)
    assert "sin bajarte" not in robot.dicho()                    # sin un arma de fuego no viene a cuento
    robot.tecla(pygame.K_LCTRL)                                  # y si lo intentas a puñetazos, te dice cómo es
    assert "pulsa I para elegir una, Q para fijar a quien tengas cerca y Control para disparar" in robot.app.voz.registro[-1]
    p.dar_arma("pistola", 50)
    robot.frames(30)
    dicho = robot.dicho()
    assert "Tienes enemigos cerca y vas al volante. Puedes responder sin bajarte: pulsa Q para fijar a quien tengas cerca y Control para disparar desde el vehículo" in dicho
    assert "disparo_veh" in p.j.recordado
    robot.frames(90)
    assert robot.dicho().count("Puedes responder sin bajarte") == 1          # una vez por partida
    # y funciona: Q fija y Control dispara, sin bajarse
    p.j.arma = "pistola"
    robot.tecla(pygame.K_q)
    assert p.objetivo is e
    balas = p.j.armas["pistola"]["cargador"]
    robot.tecla(pygame.K_LCTRL)
    assert p.j.armas["pistola"]["cargador"] == balas - 1 and p.j.veh is v
    # la ayuda de F1 al volante lo cuenta entero, y el tutorial también
    control = next(que for tecla, que in ayuda.TECLAS["coche"] if tecla == "Control")
    assert "la Q fija" in control and "sin bajarte" in control
    assert any("Desde un vehículo también puedes disparar sin bajarte" in t for _, t in ayuda.TUTORIAL)


def test_disparar_desde_el_vehiculo_con_mando(robot):
    from test_171_mando import Md
    p = _calle_vacia(robot, invulnerable=True)
    md = Md(robot, "xbox")
    _coche(p, *p.pos())
    p.dar_arma("pistola", 50)
    p.j.arma = "pistola"
    e = _persona(p, "enemigo", 25, nombre="Matón", arma="pistola", hostil=True, estado="ataca", t_disparo=99.0, tag="mision")
    robot.frames(30)
    aviso = next(t for t in robot.app.voz.registro if "Puedes responder sin bajarte" in t)
    assert "pulsa Q" not in aviso and "Control" not in aviso     # con mando, la frase dice los botones
    from juego import mando
    fijar = next(b for b, a in robot.app.mando.mapa["coche"].items() if a == "fijar")
    disparar = next(b for b, a in robot.app.mando.mapa["coche"].items() if a == "disparar_veh")
    md.pulsar(fijar)
    assert p.objetivo is e
    balas = p.j.armas["pistola"]["cargador"]
    md.pulsar(disparar)
    robot.frames(2)
    assert p.j.armas["pistola"]["cargador"] < balas and mando.ACCIONES["disparar_veh"][0] == "disparar desde el vehículo"


# ------------------------------------------------------------------ B6. poner música propia
def test_mi_musica_se_encuentra_en_la_pausa_y_lleva_a_la_carpeta(robot, tmp_path, monkeypatch):
    from juego import menus_juego, rutas
    app = robot.app
    p = robot.nueva_partida()
    carpeta = tmp_path / "radio" / "mi_musica"
    monkeypatch.setattr(app.radio, "usuario", str(carpeta))
    abiertas = []
    monkeypatch.setattr(os, "startfile", lambda r: abiertas.append(r), raising=False)
    # la emisora vacía dice por dónde se llega, sin nombres de carpetas internas
    i = next(k for k, e in enumerate(app.radio.emisoras) if e["id"] == "usuario")
    t = app.radio.sintonizar(i)
    app.radio.apagar()
    assert "pulsa Escape y elige Mi música" in t and "data" not in t and "mi_musica" not in t
    robot.tecla(pygame.K_ESCAPE)                                 # la pausa
    _elegir(robot, "Mi música")
    m = app.pila[-1]
    textos = [o.texto for o in m.opciones]
    assert textos[0].startswith("Uno.") and textos[1].startswith("Dos.") and textos[2].startswith("Tres.") and textos[3].startswith("Cuatro.")
    assert not any("data" in t.split() or "mi_musica" in t or "\\" in t for t in textos)         # sin tecnicismos
    assert "mp3" in textos[1] and "Control V" in textos[1] and "Mi música" in textos[3]
    _elegir(robot, "Abrir la carpeta de mi música")
    assert abiertas == [str(carpeta)] and carpeta.is_dir() and "Explorador" in robot.app.voz.registro[-1]
    (carpeta / "una.mp3").write_bytes(b"x")
    assert "tiene una canción" in next(o.texto for o in m.opciones if o.texto.startswith("Abrir la carpeta"))
    # también desde Opciones, Sonido y música, y contado paso a paso en el manual
    robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_ESCAPE)
    menus_juego.opciones(app)
    _elegir(robot, "Sonido")
    assert any(o.texto.startswith("Mi música: cómo poner tus canciones") for o in app.pila[-1].opciones)
    manual = open(os.path.join(rutas.DOCS, "manual_es.html"), encoding="utf-8").read()
    assert "Poner tu propia música, paso a paso" in manual


def test_mi_musica_con_mando(robot, tmp_path, monkeypatch):
    from test_171_mando import Md
    app = robot.app
    robot.nueva_partida()
    md = Md(robot, "ps")
    monkeypatch.setattr(app.radio, "usuario", str(tmp_path / "mi_musica"))
    abiertas = []
    monkeypatch.setattr(os, "startfile", lambda r: abiertas.append(r), raising=False)
    md.pulsar("start")                                           # la pausa
    md.elegir("Mi música", empieza=True)
    md.elegir("Abrir la carpeta de mi música", empieza=True)
    assert abiertas == [str(tmp_path / "mi_musica")]


# ------------------------------------------------------------------ B7. territorios: cómo funciona
def test_territorios_explica_como_funciona_con_las_cifras_de_la_partida(robot):
    from juego import menus_extra, rutas
    p = robot.nueva_partida()
    menus_extra.territorios(p)
    m = robot.app.pila[-1]
    assert m.opciones[0].texto.startswith("Cómo funciona esto")              # lo primero del menú
    robot.tecla(pygame.K_RETURN)
    exp = robot.app.pila[-1]
    textos = " ".join(o.texto for o in exp.opciones)
    tributo = p.precio("tributo_territorio", 300)
    for trozo in ("Qué es.", f"te paga {tributo} euros cada medianoche", "Sin territorios no hay banda", "Cómo se conquista.", "oleadas de pandilleros",
                  "Cómo se defiende.", "Reconquista.", "Si pierdes un barrio.", "Buscar pelea con una banda", "Negociar con las bandas"):
        assert trozo in textos, trozo
    assert "elige Conquistar" in textos                          # con la guerra en la calle apagada, desde el móvil
    robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_ESCAPE)
    p.cfg["guerra_calle"] = True                                 # y con ella encendida, lo cuenta como es
    menus_extra.como_funcionan_territorios(p)
    assert "planta cara a la banda allí" in " ".join(o.texto for o in robot.app.pila[-1].opciones)
    robot.tecla(pygame.K_ESCAPE)
    p.cfg["guerra_calle"] = False
    # con algo urgente (un ataque a un barrio tuyo), eso sigue arriba del todo y la explicación va detrás
    p.j.territorios.append("puerto")
    p.j.amenaza = {"territorio": "puerto", "banda": "Los Calaveras", "dia": p.dia}
    menus_extra.territorios(p)
    ops = [o.texto for o in robot.app.pila[-1].opciones]
    assert not ops[0].startswith("Cómo funciona") and any(t.startswith("Cómo funciona esto") for t in ops[:4])
    manual = open(os.path.join(rutas.DOCS, "manual_es.html"), encoding="utf-8").read()
    assert "Cómo funciona esto" in manual and "Buscar pelea con una banda" in manual


def test_territorios_como_funciona_con_mando(robot):
    from test_171_mando import Md
    p = robot.nueva_partida()
    md = Md(robot, "xbox")
    md.pulsar("back")                                            # el móvil
    md.elegir("Territorios", empieza=True)
    md.elegir("Cómo funciona esto", empieza=True)
    m = robot.app.pila[-1]
    assert str(m.titulo).startswith("Territorios: cómo funciona")
    md.pulsar("abajo")
    assert m.i == 1
    md.pulsar("b")
    assert str(robot.app.pila[-1].titulo).startswith("Territorios de")


# ------------------------------------------------------------------ C8. pelear contra atracadores con la policía delante
def _pelea(robot, p, malos, segundos=25, primero=False):
    """Juegas la pelea con las teclas: Q fija y Espacio dispara, hasta que no quede ninguno."""
    if not primero:
        robot.frames(45)
    for k in range(int(segundos * 30)):
        vivos = [e for e in malos if not e.muerto]
        if vivos and k % 12 == 0:
            if p.objetivo not in vivos:
                p.objetivo = None
                robot.tecla(pygame.K_q)
            robot.tecla(pygame.K_SPACE)
        robot.frames(1)
        assert p.j.estrellas == 0, robot.dicho()[-300:]
    assert all(e.muerto for e in malos)


def _armado(robot, **opciones):
    p = _calle_vacia(robot, **opciones)
    p.dar_arma("pistola", 300)
    p.j.arma = "pistola"
    p.j.salud = p.j.salud_max = 100000.0
    return p


def test_defenderte_a_tiros_de_un_atracador_con_un_agente_delante_no_es_delito(robot, datos_de_serie):
    """Lo que contaban: peleas con un atracador, llega la policía y va a por ti. Quedaba un caso: si disparabas antes de
    que te alcanzara con la navaja, el delito era tuyo."""
    from juego import calle as C
    C.AJUSTES["auxilio_prob"] = 0
    p = _armado(robot)
    e = _persona(p, "enemigo", 9, nombre="Atracador", arma="navaja", hostil=True, estado="ataca", t_disparo=0.05, salud=120.0)
    _persona(p, "civil", -8, estado="quieto")                    # un testigo
    poli = _persona(p, "policia", 14, 3, nombre="Policía", arma="pistola", hostil=False, estado="quieto", t_disparo=0.2)
    robot.frames(3)
    assert e.agresor                                             # viene a por ti: no hace falta esperar al primer navajazo
    _pelea(robot, p, [e], primero=True)
    assert p.j.puntos_busqueda == 0 and not poli.hostil and "Delito" not in robot.dicho()
    assert "defenderte de quien te ataca no cuenta como delito" in " | ".join(robot.app.voz.registro)


def test_parar_al_atracador_de_un_suceso_disparando_tu_primero_tampoco(robot, datos_de_serie):
    import random
    from juego import calle as C
    C.AJUSTES["auxilio_prob"] = 0
    p = _armado(robot)
    original = random.choice
    p.cfg["sucesos"] = True
    p.t_evento = 0.0
    p.cfg["sucesos_apagados"] = ["maletin", "banda"]                # desde la 1.7.6 los sucesos son datos: solo queda el atraco
    try:
        for _ in range(300):
            p.actualizar_extras(1 / 30)
            if p.evento:
                break
    finally:
        random.choice = original
    assert p.evento and p.evento["tipo"] == "atraco"
    malos = [q for q in p.evento["personas"] if q.tipo == "enemigo"]
    x, y = p.pos()
    for k, q in enumerate(p.evento["personas"]):
        q.x, q.y = p.mundo.punto_libre(x + 10 + k, y + 1)
    poli = _persona(p, "policia", 14, 3, nombre="Policía", arma="pistola", hostil=False, estado="quieto", t_disparo=0.2)
    _pelea(robot, p, malos, primero=True)
    assert p.j.puntos_busqueda == 0 and not poli.hostil and "Delito" not in robot.dicho()
    assert "La víctima te da las gracias" in " | ".join(robot.app.voz.registro)


def test_con_tu_banda_ayudando_tampoco_te_buscan(robot, datos_de_serie):
    from juego import calle as C, sistemas
    C.AJUSTES["auxilio_prob"] = 0
    p = _armado(robot)
    p.j.territorios.append("puerto")
    p.j.banda, p.j.banda_nombre = 2, "Los Nuestros"
    llegan, _ = sistemas.llamar(p)
    assert llegan == 2
    for a in sistemas.miembros_presentes(p):
        a.arma = "pistola"
    malos = [_persona(p, "enemigo", 10 + k, nombre="Atracador", arma="navaja", hostil=True, estado="ataca", t_disparo=0.05, salud=90.0) for k in range(2)]
    _persona(p, "civil", -8, estado="quieto")
    poli = _persona(p, "policia", 16, 3, nombre="Policía", arma="pistola", hostil=False, estado="quieto", t_disparo=0.2)
    _pelea(robot, p, malos, segundos=30)
    assert p.j.puntos_busqueda == 0 and not poli.hostil and "Delito" not in robot.dicho()


# ------------------------------------------------------------------ C9. las misiones avisan del vehículo antes de aceptarlas
def test_toda_mision_con_vehiculo_lo_avisa_antes_de_aceptarla(robot):
    p = robot.nueva_partida()
    con_veh = [m for m in p.datos["misiones"] if any(q.get("tipo") in ("robar", "carrera", "perseguir") for q in m.get("pasos", []))]
    assert len(con_veh) >= 40
    for m in con_veh:
        t = p.mision_vehiculo_txt(m)
        tipos = [q["tipo"] for q in m["pasos"]]
        assert t, m["id"]
        if "robar" in tipos:
            assert t.startswith(("Te dan vehículo", "Hay que llevarse un vehículo concreto", "Te dejan un vehículo")), (m["id"], t)
        elif "perseguir" in tipos:
            assert "persecución en vehículo" in t, (m["id"], t)
    sin = [m for m in p.datos["misiones"] if m not in con_veh]
    assert all(p.mision_vehiculo_txt(m) == "" for m in sin)
    # se dice en la lista del móvil y también al llegar a la puerta del contacto, antes de pulsar Intro
    m = next(x for x in p.datos["misiones"] if x["id"] == "m06")
    p.completadas = [x["id"] for x in p.datos["misiones"] if x["id"] != "m06"]
    assert m in p.misiones_disponibles()
    l = p.lugares[m["lugar"]]
    assert p.mision_en_lugar(l.id) is m
    p.teletransportar(l.x + 30, l.y)
    robot.frames(15)
    p.j.x, p.j.y = l.x, l.y                                      # llegas andando a su puerta
    robot.frames(15)
    aviso = next(t for t in robot.app.voz.registro if "Misión disponible: Entrega urgente" in t)
    assert "Te dejan un vehículo, Furgoneta de reparto, pero puedes hacerla con el tuyo" in aviso and aviso.endswith("Pulsa Intro para empezarla.")


# ------------------------------------------------------------------ C10. buscar pelea con una banda, sin conquistar
def test_buscar_pelea_con_una_banda_sin_conquistar_nada(robot, datos_de_serie):
    from juego import guerra as GU, menus_extra
    p = _armado(robot)
    assert not p.cfg["guerra_calle"]                             # vale con el modo de guerra en la calle apagado
    j = p.j
    barrio = p.mundo.barrio(*p.pos())
    territorios = list(j.territorios)
    menus_extra.territorios(p)
    _elegir(robot, "Buscar pelea con una banda")
    m = robot.app.pila[-1]
    banda = p.bandas_para_pelea()[0]
    assert m.opciones[0].texto.startswith(banda) and "No se gana ningún barrio" in m.opciones[0].ayuda
    antes = p.rep_banda(banda)
    robot.tecla(pygame.K_RETURN)
    assert "vienen 3 de una vez" in robot.app.pila[-1].opciones[0].texto
    _elegir(robot, "Una pelea corta")
    assert robot.app.pila[-1] is p and p.guerra and p.guerra["tipo"] == "pelea" and p.guerra["total"] == 1
    assert p.rep_banda(banda) == antes - GU.aj("pelea_enfado") and "No hay barrio en juego" in robot.dicho()
    robot.tecla(pygame.K_o)
    assert f"Pelea con {banda}" in robot.app.voz.registro[-1] and "sin barrio en juego" in robot.app.voz.registro[-1]
    for _ in range(400):
        robot.frames(1)
        if p.guerra["vivos"]:
            break
    vivos = p.guerra["vivos"]
    assert len(vivos) == 3 and all(e.tag == "guerra" and e.banda == banda for e in vivos) and "Ya están aquí: 3 de " + banda in robot.dicho()
    for e in vivos:
        p.danar_persona(e, 9999)
    robot.frames(5)
    assert p.guerra is None and j.territorios == territorios and barrio["id"] not in j.territorios
    dicho = " | ".join(robot.app.voz.registro[-12:])
    assert "No has ganado ningún barrio" in dicho and j.stats["peleas_banda"] == 1
    assert p.rep_banda(banda) < antes - GU.aj("pelea_enfado")     # y cada baja, además, se la apuntan
    # enseguida no se puede otra: hay que esperar un poco
    assert "Espera" in p.pelea_motivo()
    p.t_guerra_enfria = -99.0
    # la larga: dos tandas, y si te vas del barrio, se da por perdida sin más consecuencias
    assert p.pelea_tamano(True) == [3, 4] and p.buscar_pelea(banda, True) and p.guerra["total"] == 2
    p.guerra_retirada()
    assert p.guerra is None and "se queda sin su pelea" in robot.app.voz.registro[-1]
    # ni en una misión, ni con la policía detrás, ni en un servidor
    p.t_guerra_enfria = -99.0
    j.estrellas = 2
    assert "policía" in p.pelea_motivo() and not p.buscar_pelea(banda)
    j.estrellas = 0
    p.en_servidor = True
    try:
        assert "servidor" in p.pelea_motivo()
    finally:
        p.en_servidor = False


def test_buscar_pelea_con_mando(robot, datos_de_serie):
    from test_171_mando import Md
    p = _armado(robot)
    md = Md(robot, "ps")
    robot.tecla(pygame.K_m)
    md.elegir("Territorios", empieza=True)
    md.elegir("Buscar pelea con una banda", empieza=True)
    md.pulsar("a")                                               # la primera banda
    md.elegir("Una pelea larga", empieza=True)
    assert robot.app.pila[-1] is p and p.guerra and p.guerra["tipo"] == "pelea" and p.guerra["total"] == 2


# ------------------------------------------------------------------ D11. las misiones se ajustan a tu escolta
def _con_escolta(p, n):
    for e in [e for e in p.personas if e.tipo == "aliado"]:
        p.personas.remove(e)
    return [p.crear_aliado() for _ in range(n)]


def test_la_escolta_sube_la_oposicion_dentro_de_los_topes(robot, datos_de_serie):
    from juego import config, escolta as ES
    p = _calle_vacia(robot)
    assert config.POR_DEFECTO["escolta_misiones"] == "moderado" and config.OPCIONES["escolta_misiones"] == ["no", "moderado", "fuerte"]
    normal = {"id": "x", "pasos": []}
    grupos = [{"tipo": "Matón", "n": 3, "arma": "pistola", "salud": 80}, {"tipo": "Jefe", "n": 1, "arma": "escopeta", "salud": 150},
              {"tipo": "Muñeco", "n": 2, "inofensivo": True}]
    base = 4
    # solo, o con un único acompañante, nada cambia
    for n in (0, 1):
        _con_escolta(p, n)
        assert p.escolta_ajuste(normal) is None and [k for _, k in p.escolta_grupos(grupos, None)] == [3, 1, 2]
    for nivel, tope_n, tope_salud, tope_punt in (("moderado", 1.5, 1.4, 1.15), ("fuerte", 2.0, 1.8, 1.30)):
        p.cfg["escolta_misiones"] = nivel
        for n in (2, 4, 8):                                      # hasta toda la banda y dos guardaespaldas
            _con_escolta(p, n)
            aj = p.escolta_ajuste(normal)
            assert aj and aj["n"] == n and 1.0 < aj["salud"] <= tope_salud + 1e-9 and 1.0 < aj["punteria"] <= tope_punt + 1e-9
            for _ in range(30):                                  # con su parte de azar, nunca se pasa del tope ni baja de lo que había
                reparto = p.escolta_grupos(grupos, aj)
                total = sum(k for g, k in reparto if not g.get("inofensivo"))
                assert base <= total <= base * tope_n and reparto[2][1] == 2 and reparto[0][1] >= 3 and reparto[1][1] >= 1
        _con_escolta(p, 8)
        aj = p.escolta_ajuste(normal)
        assert aj["salud"] == pytest.approx(1 + min(ES.AJ(nivel + "_salud_max"), ES.AJ(nivel + "_salud") * 7) / 100) and aj["punteria"] == pytest.approx(tope_punt)
        assert max(sum(k for g, k in p.escolta_grupos(grupos, aj) if not g.get("inofensivo")) for _ in range(30)) == int(base * tope_n)
    # los tutoriales no se tocan, ni con la opción en «no», ni en un servidor
    assert p.escolta_ajuste({"id": "t", "tutorial": True, "pasos": []}) is None
    p.cfg["escolta_misiones"] = "no"
    assert p.escolta_ajuste(normal) is None
    p.cfg["escolta_misiones"] = "fuerte"
    p.en_servidor = True
    try:
        assert p.escolta_ajuste(normal) is None
    finally:
        p.en_servidor = False
    # los que están lejos no cuentan
    for a in [e for e in p.personas if e.tipo == "aliado"][:7]:
        a.x += 400
    assert p.escolta_presente() == 1 and p.escolta_ajuste(normal) is None
    # y los números salen de los datos
    assert set(ES.AJ.n) >= {"radio", "aliados_gratis", "moderado_extra_max", "fuerte_extra_max", "fuerte_salud_max"}


def test_ninguna_mision_se_dispara_con_la_escolta_al_maximo(robot, datos_de_serie):
    """En todas las misiones del juego y de los mods: con ocho de escolta y en fuerte, cada paso tiene como mucho el doble
    de enemigos y como poco los de siempre; y las de tutorial, exactamente los de siempre."""
    p = _calle_vacia(robot)
    p.cfg["escolta_misiones"] = "fuerte"
    _con_escolta(p, 8)
    pasos = 0
    for m in p.datos["misiones"]:
        aj = p.escolta_ajuste(m)
        assert (aj is None) == bool(m.get("tutorial")), m["id"]
        for q in m.get("pasos", []):
            if q.get("tipo") != "eliminar":
                continue
            pasos += 1
            base = sum(int(g.get("n", 1)) for g in q["enemigos"])
            normales = sum(int(g.get("n", 1)) for g in q["enemigos"] if not (g.get("inofensivo") or g.get("deportivo") or g.get("intimidar")))
            for _ in range(5):
                total = sum(k for _, k in p.escolta_grupos(q["enemigos"], aj))
                assert base <= total <= base + normales, (m["id"], base, total)
                if aj is None:
                    assert total == base
    assert pasos >= 40


def test_una_mision_de_verdad_con_toda_la_escolta_se_puede_acabar(robot, datos_de_serie):
    """Jugada: una misión con enemigos, en fuerte y con ocho de los tuyos. Vienen más, aguantan más, el juego lo dice, y
    al caer todos el paso se da por hecho, igual que siempre."""
    from juego.menus import Dialogo
    p = _calle_vacia(robot, invulnerable=True)
    m = next(x for x in p.datos["misiones"] if not x.get("tutorial") and x.get("lugar") in p.lugares
             and any(q["tipo"] == "eliminar" and sum(int(g.get("n", 1)) for g in q["enemigos"]) >= 3 and not any(g.get("intimidar") for g in q["enemigos"])
                     for q in x["pasos"]) and all(q["tipo"] in ("dialogo", "eliminar", "dar", "ir") for q in x["pasos"][:3]))
    paso = next(q for q in m["pasos"] if q["tipo"] == "eliminar")
    base = sum(int(g.get("n", 1)) for g in paso["enemigos"])

    def jugar(nivel, escolta):
        p.cfg["escolta_misiones"] = nivel
        if p.mision:
            p._limpiar_mision()
        p.personas = []
        l = p.lugares[m["lugar"]]
        if l.mapa != p.mundo.id:
            p.cambiar_mapa(l.mapa, l.x, l.y)
        p.teletransportar(l.x, l.y)
        p.completadas = [x for x in p.completadas if x != m["id"]]
        for a in _con_escolta(p, escolta):
            a.x, a.y = p.pos()
        p.iniciar_mision(m)
        for _ in range(300):
            c = robot.app.pila[-1]
            ms = p.mision
            if isinstance(c, Dialogo):
                robot.tecla(pygame.K_ESCAPE)
                continue
            q = ms["def"]["pasos"][ms["paso"]]
            lugar = p.lugares.get(q.get("lugar", ""))
            if lugar is not None:
                if lugar.mapa != p.mundo.id:
                    p.cambiar_mapa(lugar.mapa, lugar.x, lugar.y)
                p.teletransportar(lugar.x + 3, lugar.y)
            if not ms["generado"]:
                for a in _con_escolta(p, escolta):               # los tuyos, a tu lado
                    a.x, a.y = p.pos()
            if q["tipo"] == "eliminar":
                for _ in range(30):
                    robot.frames(1)
                    if ms["generado"]:
                        break
                return ms
            robot.frames(3)
        raise AssertionError("no se llega al paso de los enemigos")
    ms = jugar("no", 8)
    assert len(ms["enemigos"]) == base
    salud_base = sorted(e.salud for e in ms["enemigos"])
    ms = jugar("fuerte", 8)
    n = len(ms["enemigos"])
    assert base < n <= 2 * base, (base, n)
    assert max(e.salud for e in ms["enemigos"]) > max(salud_base) * 1.5 and all(e.punteria <= 0.95 for e in ms["enemigos"])
    assert "Las misiones se ajustan a tu escolta" in " | ".join(robot.app.voz.registro[-8:])
    indice = ms["paso"]
    for e in ms["enemigos"]:
        p.danar_persona(e, 99999)
    robot.frames(10)
    assert p.mision is None or p.mision["paso"] > indice         # el paso se cumple como siempre


def test_la_opcion_de_la_escolta_esta_en_el_menu_y_en_el_editor(robot, datos_de_serie):
    from editor import esquema
    from juego import menus_juego
    app = robot.app
    menus_juego.opciones(app)
    _elegir(robot, "Combate y dificultad")
    m = app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Las misiones se ajustan a tu escolta"))
    assert "moderado" in m.opciones[m.i].texto and "ninguna misión se vuelva imposible" in m.opciones[m.i].ayuda
    robot.tecla(pygame.K_RIGHT)
    assert app.cfg["escolta_misiones"] == "fuerte" and "fuerte" in m.opciones[m.i].texto
    robot.tecla(pygame.K_RIGHT)
    assert app.cfg["escolta_misiones"] == "no"
    robot.tecla(pygame.K_RIGHT)
    assert app.cfg["escolta_misiones"] == "moderado"
    campos = {c["k"] for c in esquema.ESQUEMAS["ajuste_escolta"]["campos"]}
    assert {"radio", "aliados_gratis", "moderado_extra", "moderado_extra_max", "fuerte_salud_max", "fuerte_punteria_max", "frases"} <= campos
    assert any(s[0] == "escolta_misiones" for s in esquema.SECCIONES)


# ------------------------------------------------------------------ E12. elegir qué vehículo quieres
def test_en_el_concesionario_eliges_cual_comprar_y_cual_te_llevas_sin_pagar(robot):
    from juego import menus_juego
    p = _calle_vacia(robot)
    l = next(x for x in p.mundo.lugares.values() if x.tipo == "concesionario")
    p.teletransportar(l.x, l.y)
    p.j.dinero = 0
    menus_juego.lugar(p, l)
    m = robot.app.pila[-1]
    en_venta = [o for o in m.opciones if " euros" in o.texto and ":" in o.texto and not o.texto.startswith(("Trabajar", "Pedir"))]
    assert len(en_venta) >= 4                                    # al comprar ya se elegía modelo
    _elegir(robot, "Pedir las llaves para una prueba y no volver")
    sub = robot.app.pila[-1]
    assert str(sub.titulo).startswith("¿De cuál pides las llaves?") and len(sub.opciones) == len(en_venta) + 1
    caro = sub.opciones[-2].texto.split(",")[0]
    sub.i = len(sub.opciones) - 2
    robot.tecla(pygame.K_RETURN)
    robot.frames(3)
    assert robot.app.pila[-1] is p and p.j.puntos_busqueda > 0
    assert any(v.modelo["nombre"] == caro for v in p.vehiculos) and f"Pides las llaves de un {caro}" in " | ".join(robot.app.voz.registro[-6:])


def test_el_chofer_viene_con_el_vehiculo_de_la_banda_que_elijas(robot, datos_de_serie):
    from juego import misvehiculos as MV
    p = _calle_vacia(robot)
    p.j.territorios.append("puerto")
    p.j.banda, p.j.banda_nombre, p.j.dinero = 2, "Los Nuestros", 5000
    modelos = p.chofer_modelos()
    assert len(modelos) >= 2
    MV.menu_chofer(p)
    m = robot.app.pila[-1]
    textos = [o.texto for o in m.opciones]
    assert textos[0].startswith("Que venga con un vehículo de la banda") and sum(1 for t in textos if t.startswith("Que venga con el ")) == len(modelos)
    elegido = modelos[-1]
    _elegir(robot, f"Que venga con el {p.modelos[elegido]['nombre']} de la banda")
    assert p.chofer and p.chofer["modelo"] == elegido and robot.app.pila[-1] is p
    p.despedir_chofer(callar=True)
    assert p.pedir_chofer(modelo="no_existe") and p.chofer["modelo"] in modelos       # uno que no tienen: el que haya


def test_en_las_misiones_de_reparto_eliges_entre_el_vehiculo_que_te_dan_y_el_tuyo(robot):
    """Además de las dos de la tanda 3, las tres en las que el vehículo solo lleva la carga. Jugada una: con tu coche."""
    from juego.menus import Dialogo
    p = _calle_vacia(robot)
    libres = sorted(m["id"] for m in p.datos["misiones"] if m.get("vehiculo_libre"))
    assert libres == ["cd02", "m06", "of01", "v02", "x05"]
    for m in p.datos["misiones"]:                                # y en todas ellas el vehículo se da abierto: no hay que robarlo
        if m.get("vehiculo_libre"):
            assert all(q.get("abierto") for q in m["pasos"] if q["tipo"] == "robar"), m["id"]
    m = next(x for x in p.datos["misiones"] if x["id"] == "m06")
    l = p.lugares[m["lugar"]]
    p.teletransportar(l.x, l.y)
    mio = _coche(p, l.x, l.y, "sedan")
    assert p.hacer_mio(mio)
    p.iniciar_mision(m)
    for _ in range(20):
        if isinstance(robot.app.pila[-1], Dialogo):
            robot.tecla(pygame.K_ESCAPE)
    ms = p.mision
    assert ms["def"]["pasos"][ms["paso"]]["tipo"] == "robar" and "Esta misión se puede hacer con tu vehículo: tú eliges" in robot.dicho()
    v = ms["veh"]
    mio.x, mio.y, mio.vel = v.x + 6, v.y, 0.0
    robot.frames(5)
    assert p.mision["veh"] is mio and p.mision.get("veh_tuyo") and v not in p.vehiculos and "Haces la misión con" in robot.dicho()


# ------------------------------------------------------------------ A1, lo demás: embarcaderos, muelles y estaciones
def test_todos_los_embarcaderos_y_estaciones_dicen_que_hacer_a_pie_y_en_vehiculo(robot):
    """La misma vuelta que a las salidas, a lo que no es carretera: en cada embarcadero se zarpa a pie y se vuelve a
    atracar en su muelle; en cada estación se abre la taquilla a pie; y al volante, las dos dicen que hay que bajarse."""
    p = robot.nueva_partida()
    embarcaderos = _conexiones(p, ("embarcadero",))
    estaciones = [(m, l) for m in p.mapas.values() for l in m.lugares.values() if l.tipo == "estacion"]
    assert len(embarcaderos) >= 5 and len(estaciones) >= 6
    for m, l in embarcaderos:
        muelle = p.lug(l.get("a_lugar"))
        assert muelle is not None and muelle.tipo == "muelle" and p.lug(muelle.get("a_lugar")) is l, l.id
        _limpio(p, m, l.x, l.y)
        p.teletransportar(l.x, l.y)
        p.j.dinero = 500
        assert p.pista_de_llegada(l) == "Pulsa Intro para elegir barco y zarpar."
        robot.tecla(pygame.K_RETURN)
        _elegir(robot, "Alquilar una lancha")
        assert p.mundo.tipo == "mar" and p.j.veh is not None and p.j.veh.dist(muelle.x, muelle.y) < 26, l.id
        assert p.lugar_al_alcance() is muelle and "Pulsa Intro para atracar en " + m.nombre in p.pista_de_llegada(muelle)
        p.j.veh.vel = 0.0
        robot.tecla(pygame.K_RETURN)
        _elegir(robot, "Atracar y desembarcar")
        assert p.mundo is m and p.j.veh is None and math.hypot(p.j.x - l.x, p.j.y - l.y) < 12, l.id
        if m.tipo in ("ciudad", "pueblo"):                      # al volante: hay que bajarse, y lo dice
            _coche(p, l.x, l.y)
            assert "Bájate del vehículo con F" in p.pista_de_llegada(l)
            robot.tecla(pygame.K_RETURN)
            assert "Bájate del vehículo para subir a un barco" in robot.app.voz.registro[-1]
    for m, l in estaciones:
        _limpio(p, m, l.x, l.y)
        p.teletransportar(l.x, l.y)
        robot.tecla(pygame.K_RETURN)
        cima = robot.app.pila[-1]
        assert isinstance(cima, Menu) and any(o.texto.startswith("Autobús a ") for o in cima.opciones), l.id
        robot.tecla(pygame.K_ESCAPE)
        _coche(p, l.x, l.y)
        assert p.lugar_al_alcance() is l or p.lugar_al_alcance().tipo == "salida"
        if p.lugar_al_alcance() is l:
            robot.tecla(pygame.K_RETURN)
            assert "Bájate del vehículo para coger el autobús" in robot.app.voz.registro[-1], l.id
            assert p.pista_de_llegada(l).startswith("Bájate del vehículo con F y pulsa Intro")


# ------------------------------------------------------------------ lo mismo, con mando
@pytest.mark.parametrize("tipo", ("xbox", "ps"))
def test_salir_por_carretera_y_el_camion_con_mando(robot, tipo):
    """Sin tocar el teclado: el trabajo del camión se empieza con su botón, la frase de la salida dice el botón del
    mando y no «Intro», y con ese botón se abre el viaje y se toma la carretera."""
    from test_171_mando import BOTON, Md
    p = robot.nueva_partida()
    md = Md(robot, tipo)
    m = p.mapas["puerto_bravo"]
    l = m.lugares["salida_este"]
    otro = p.lug(l.get("a_lugar"))
    _limpio(p, m, l.x - 60, l.y)
    v = _coche(p, l.x - 4, l.y + 6, "camion")
    md.pulsar("r3")                                              # empezar a trabajar
    t = p.trabajo
    assert t and t["tipo"] == "camion" and "La carga ya va en el camión" in robot.dicho()
    destino = next(x for x in p.mapas[otro.mapa].lugares.values() if x.tipo in ("tienda", "comida", "pescaderia", "taller"))
    t.update(lugar=destino)
    p.gps_a_lugar(destino, auto=True, callar=True)
    assert p._lugar_del_gps() is l
    robot.frames(40)
    aviso = next(x for x in reversed(robot.app.voz.registro) if x.startswith("Has llegado a " + l.nombre))
    assert "Intro" not in aviso and BOTON[tipo]["a"] in aviso and "tomar la carretera a " + p.mapas[otro.mapa].nombre in aviso
    v.vel = 0.0
    md.pulsar("a")
    cima = robot.app.pila[-1]
    assert isinstance(cima, Menu) and cima.opciones[0].texto.startswith("Tomar la carretera")
    md.pulsar("a")
    assert p.mundo.id == otro.mapa and p.j.veh is v and p.trabajo is t and p.gps
