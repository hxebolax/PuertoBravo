"""1.7.6: la issue 41 (comisaría más cercana, pesca de río y de mar, sucesos en los datos, rencor de la expareja) y lo que
contaron en el foro tras la 1.7.5 (reparto a casas tuyas, casas en venta ya compradas, búsqueda a tiros, helicóptero en
tierra con el GPS, mejoras de taller a lo que vuela, reclutar, encargado de los negocios)."""
import pytest

from juego import mundo as M
from juego.combate import UMBRAL
from juego.entidades import Persona
from juego.extras import agua_de, peces_de


def _partida(robot, **opciones):
    p = robot.nueva_partida()
    p.cfg["sucesos"] = False
    for k, v in opciones.items():
        p.cfg[k] = v
    p.t_evento = 1e9
    p.cancelar_gps()
    return p


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


# ------------------------------------------------------------------ 1. la comisaría más cercana por carretera
def test_los_km_por_carretera_siguen_las_salidas(robot):
    p = _partida(robot)
    km = p.km_por_tierra("fuentefria")
    assert km["fuentefria"] == 0 and km["monteferro"] == 14 and km["villaseca"] == 44 and km["puerto_bravo"] == 62
    assert "mar" not in km


def test_detenido_en_un_pueblo_sin_comisaria_te_llevan_a_la_mas_cercana_no_a_puerto_bravo(robot):
    p = _partida(robot)
    assert not [l for l in p.mapas["fuentefria"].lugares.values() if l.tipo == "comisaria"]
    p.cambiar_mapa("fuentefria", *p.mapas["fuentefria"].punto_libre(100, 100))
    robot.frames(2)
    p.j.estrellas, p.j.puntos_busqueda = 3, UMBRAL[2]
    p.detener(sin_trato=True)
    robot.frames(2)
    assert p.mundo.id == "monteferro"                                # 14 km, no los 62 hasta Puerto Bravo


def test_en_la_isla_sin_carretera_sigue_siendo_puerto_bravo(robot):
    p = _partida(robot)
    p.cambiar_mapa("isla_tortuga", *p.mapas["isla_tortuga"].punto_libre(100, 100))
    robot.frames(2)
    l = p._reaparecer("comisaria")
    assert l.mapa == "puerto_bravo"


# ------------------------------------------------------------------ 2. pesca de río, de lago y de mar
def test_cada_agua_tiene_sus_peces(robot):
    p = _partida(robot)
    peces = p.datos["peces"]
    rio = {x["nombre"] for x in peces_de(peces, "rio", "fuentefria")}
    mar = {x["nombre"] for x in peces_de(peces, "mar", "puerto_bravo")}
    assert "una trucha" in rio and "un barbo" in rio and "una sardina" not in rio and "un atún rojo" not in rio
    assert "una sardina" in mar and "una trucha" not in mar and "una carpa" not in mar
    assert "una bota vieja" in rio and "una bota vieja" in mar                # lo que no dice su agua, en cualquier sitio
    assert {x["nombre"] for x in peces_de([{"nombre": "un paiche", "aguas": ["rio"], "mapas": ["selva"]}], "rio", "fuentefria")} == {"un paiche"}   # si no queda ninguno, todos
    solo = [{"nombre": "un paiche", "aguas": ["rio"], "mapas": ["selva"]}, {"nombre": "una trucha", "aguas": ["rio"]}]
    assert [x["nombre"] for x in peces_de(solo, "rio", "fuentefria")] == ["una trucha"] and len(peces_de(solo, "rio", "selva")) == 2


def test_el_agua_de_cada_punto_de_pesca(robot):
    p = _partida(robot)
    ff = p.mapas["fuentefria"]
    assert agua_de(ff.lugares["ff_rio"], ff) == "rio"                          # suena a río
    assert agua_de(p.lugares["mirador_puerto"], p.mapas["puerto_bravo"]) == "mar"
    assert agua_de(p.mapas["mar"].lugares["mar_bajo"], p.mapas["mar"]) == "mar"
    pa = p.mapas.get("penas_altas")
    if pa is not None:
        assert agua_de(pa.lugares["pa_lago_pesca"], pa) == "lago"


def test_pescando_en_el_rio_no_sale_una_sardina(robot):
    p = _partida(robot)
    vistos = set()
    for _ in range(60):
        p.empezar_pesca(desde_muelle=True, agua="rio")
        p.pesca["fase"] = "pica"
        p.tirar_pesca()
        vistos |= {x["nombre"] for x in p.j.pescado}
    marinos = {x["nombre"] for x in p.datos["peces"] if x.get("aguas") == ["mar"]}
    assert vistos and not vistos & marinos


# ------------------------------------------------------------------ 3. sucesos en los datos, por tipo y por localidad
def _un_suceso(robot, p):
    p.cfg["sucesos"] = True
    p.evento = None
    for _ in range(40):
        p.t_evento = 0.0
        p.actualizar_extras(1 / 30)
        if p.evento:
            return p.evento
        robot.frames(1)
    return None


def test_los_sucesos_salen_de_los_datos_y_se_quitan_por_tipo(robot):
    p = _partida(robot)
    assert [s["id"] for s in p.datos["sucesos"]] == ["maletin", "atraco", "banda"]
    p.cfg["sucesos_apagados"] = ["atraco", "banda"]
    assert [s["id"] for s in p.sucesos_posibles()] == ["maletin"]
    ev = _un_suceso(robot, p)
    assert ev and ev["tipo"] == "maletin" and ev["clase"] == "objeto" and "maletín" in robot.dicho()


def test_una_localidad_dice_que_sucesos_admite_y_un_mod_crea_el_suyo(robot, datos_de_serie):
    p = _partida(robot)
    p.datos["sucesos"].append({"id": "gallinas", "clase": "objeto", "nombre": "Gallinas sueltas", "peso": 1, "premio": [20, 40],
                               "aviso": "Suceso: se han escapado unas gallinas. {situar}.", "situar": "Andan", "objeto": "Gallina", "mapas": ["puerto_bravo"]})
    p.mundo.sucesos = ["gallinas"]                                   # un pueblo tranquilo: solo lo suyo
    assert [s["id"] for s in p.sucesos_posibles()] == ["gallinas"]
    ev = _un_suceso(robot, p)
    assert ev and ev["tipo"] == "gallinas" and "gallinas" in robot.dicho()
    p.mundo.sucesos = []
    assert p.sucesos_posibles() == []
    p.mundo.sucesos = None
    p.mundo.id, original = "fuentefria", p.mundo.id                   # el de un mod con «mapas» no sale en otra localidad
    try:
        assert "gallinas" not in [s["id"] for s in p.sucesos_posibles()]
    finally:
        p.mundo.id = original


def test_opciones_tiene_la_lista_de_sucesos(robot):
    from juego import menus_juego
    robot.app.cfg["sucesos_apagados"] = []
    menus_juego.menu_sucesos(robot.app)
    m = robot.app.pila[-1]
    assert [o.texto for o in m.opciones[:3]] == ["Maletín perdido: sí", "Atraco a un vecino: sí", "Pandilleros en la calle: sí"]
    m.opciones[1].ajuste(1)
    assert robot.app.cfg["sucesos_apagados"] == ["atraco"] and m.opciones[1].texto == "Atraco a un vecino: no"
    m.opciones[1].ajuste(1)
    assert robot.app.cfg["sucesos_apagados"] == []
    robot.app.cerrar(m)


# ------------------------------------------------------------------ 4. unos días de rencor de la expareja
def test_tras_romper_la_expareja_corta_una_semana(robot):
    p = _partida(robot, adultos=True)
    pers = p.dato_adulto("personas")[0]
    r = p.relacion(pers["id"])
    r["afinidad"] = 90
    p.marcar_ruptura(r)
    assert r["estado"] == "ex" and p.hielo_ex(r) == 7
    from juego.intimidad import GESTOS
    assert p.gesto(pers["id"], pers, next(iter(GESTOS))) is False
    assert pers["nombre"] in robot.dicho()
    p.dia += 6
    assert p.hielo_ex(r) == 1
    p.dia += 1
    assert p.hielo_ex(r) == 0                                        # pasada la semana, como siempre
    viejo = {"estado": "ex", "afinidad": 20}                         # una ruptura de antes de la 1.7.6: sin rencor
    assert p.hielo_ex(viejo) == 0


# ------------------------------------------------------------------ foro: reparto, casas en venta, búsqueda a tiros
def test_el_reparto_no_sale_de_una_casa_tuya(robot):
    p = _partida(robot)
    todos = [l for l in p.mundo.lugares.values() if l.tipo not in ("salida", "muelle", "embarcadero") and "xy" not in l.d]
    libre = todos[0]
    p.j.propiedades = [l.id for l in todos[1:]]
    for _ in range(20):
        assert p._destino_azar(0, 99999) is libre


def test_disparar_sin_herir_a_nadie_no_sube_la_busqueda_de_dos(robot):
    p = _partida(robot)
    x, y = p.pos()
    p.personas.append(Persona("civil", x + 3, y, "Testigo"))
    p.en_defensa_propia = lambda: False
    for k in range(200):
        p.t = 10.0 + k * 6                                           # una ráfaga cada seis segundos, durante veinte minutos
        p._ruido_disparo(x, y)
    assert 0 < p.j.puntos_busqueda < UMBRAL[2]
    antes = p.j.puntos_busqueda
    p.j.puntos_busqueda = 0
    p.t += 100
    for _ in range(10):                                              # diez tiros seguidos: un solo delito
        p._ruido_disparo(x, y)
    assert p.j.puntos_busqueda <= 0.4 * 1.5 and antes > 0


# ------------------------------------------------------------------ foro: lo que vuela
def test_en_un_helicoptero_en_tierra_el_gps_dice_que_despegues(robot):
    robot.app.vuelo_en_pruebas = True
    try:
        p = _partida(robot, vuelo_real=True)
        x, y = p.pos()
        v = p.crear_vehiculo("helicoptero", x + 4, y, 1, None, "Colibrí de prueba")
        p._subir(v, False, callar=True)
        l = next(l for l in p.mundo.lugares.values() if l.tipo == "hospital")
        p.gps_a_lugar(l, callar=True)
        clave, texto = p._instruccion()
        assert clave == "tierra" and "despega" in texto and "gira" not in texto
        v.fase = "crucero"
        clave, texto = p._instruccion()
        assert clave[0] == "aire" and "en línea recta" in texto
    finally:
        robot.app.vuelo_en_pruebas = False


def test_el_taller_no_pone_neumaticos_a_un_helicoptero(robot):
    from juego import sistemas
    from juego.menus import Opcion
    p = _partida(robot)
    x, y = p.pos()
    heli = p.crear_vehiculo("helicoptero", x + 4, y, 1, None, "Colibrí")
    coche = p.crear_vehiculo("sedan", x + 8, y, 1, None, "Brisa")
    de_heli = " ".join(o.texto for o in sistemas.opciones_taller(p, heli, Opcion))
    de_coche = " ".join(o.texto for o in sistemas.opciones_taller(p, coche, Opcion))
    assert "motor" in de_heli and "blindaje" in de_heli and "neumáticos" not in de_heli and "frenos" not in de_heli
    assert "neumáticos" in de_coche and "frenos" in de_coche


def test_al_bajarte_de_un_helicoptero_robado_te_dice_que_no_es_tuyo(robot):
    p = _partida(robot)
    x, y = p.pos()
    v = p.crear_vehiculo("helicoptero", x + 4, y, 1, None, "Colibrí")
    p._subir(v, False, callar=True)
    p.salir_vehiculo()
    assert "No es tuyo" in robot.dicho() and "Mis vehículos" in robot.dicho()


# ------------------------------------------------------------------ foro: reclutar y el encargado de los negocios
def test_quien_no_se_une_nunca_lo_dice(robot):
    from juego import gente as G
    p = _partida(robot)
    assert "con timidez" in p.nunca_reclutan() and "con chulería" not in p.nunca_reclutan()
    p.j.territorios = ["x"]
    q = Persona("civil", 0, 0, "Tímida")
    from juego.charla import ficha
    f = ficha(q)
    f.update(caracter="timido", edad=30, confianza=90)
    clave, explicacion = p.recluta_motivo(q)
    assert clave == "frases_recluta_no_caracter" and "no se unirá nunca" in explicacion and G.caracter("timido")["desc"] in explicacion


def test_un_encargado_lleva_el_negocio_sin_que_pases(robot):
    p = _partida(robot, consecuencias="normal")
    l = p.lugares["bar_puerto"]
    p.j.propiedades.append(l.id)
    p.hon()["gracia"] = 0
    e = p.hon_emp(l)
    sin = p.ingreso_negocio(l)
    p.hon_encargado(l)
    assert e["encargado"] and p.ingreso_negocio(l) == sin - int(int(l.get("ingresos", 0)) * 0.25)
    assert "Lo lleva un encargado" in p.hon_negocio_txt(l)
    rep = e["rep"]
    for _ in range(20):                                              # veinte días sin pasar
        p.dia += 1
        p._hon_dia_empresa()
    assert e["rep"] > rep and e["rep"] <= 80 + 1.5
    con = p.ingreso_negocio(l)
    p.hon_encargado(l)
    assert not e["encargado"] and p.ingreso_negocio(l) == con + int(int(l.get("ingresos", 0)) * 0.25)     # su sueldo deja de salir de la caja
