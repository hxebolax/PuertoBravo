"""Trabajo 1.7.1, tanda 3: Mis vehículos (no se pierden, se guardan, lista en el móvil, nombre propio), las misiones y
tu vehículo, el chófer de la banda y cómo convive todo con un servidor en línea."""
import hashlib
import json
import math

import pygame
import pytest

from juego import misvehiculos as MV, mundo as M, partida as PA, sistemas
from juego.menus import EntradaTexto, Menu


def _casa_con_garaje(p, plazas=None):
    """Una casa de la localidad con garaje, ya comprada."""
    l = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and int(l.get("garaje", 0)) > 0)
    if l.id not in p.j.propiedades:
        p.j.propiedades.append(l.id)
    if plazas is not None:
        l.d["garaje"] = plazas
    return l


def _comprar(p, modelo="sedan", dx=6.0, nombre=None):
    """Un vehículo tuyo en la calle, a unos metros."""
    v = p.crear_vehiculo(modelo, p.j.x + dx, p.j.y, 1, None, nombre)
    assert p.hacer_mio(v)
    return v


def _lejos(p, metros=400.0):
    """Te vas a pie lejos y pasa el tiempo: lo que no sea tuyo desaparece."""
    m = p.mundo
    x = p.j.x + metros if p.j.x + metros < m.ancho - 20 else p.j.x - metros
    p.teletransportar(x, p.j.y)
    for _ in range(4):
        p._poblar()


def _escribir(robot, texto):
    cima = robot.app.pila[-1]
    assert isinstance(cima, EntradaTexto), cima
    for ch in texto:
        robot.tecla(pygame.K_a, unicode=ch)
    robot.tecla(pygame.K_RETURN)


def _elegir(robot, empieza):
    m = robot.app.pila[-1]
    assert isinstance(m, Menu), m
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith(empieza))
    robot.tecla(pygame.K_RETURN)


@pytest.fixture
def datos_de_serie():
    yield
    M.cargar_datos()


# ------------------------------------------------------------------ 1. no se pierden
def test_los_tuyos_no_desaparecen_y_los_demas_si(robot):
    p = robot.nueva_partida()
    mio = _comprar(p, "sedan", 6)
    robado = p.crear_vehiculo("utilitario", p.j.x + 12, p.j.y, 1, None)
    otro = p.crear_vehiculo("furgoneta", p.j.x + 18, p.j.y, 1, None)
    p._subir(robado, True, callar=True)
    p.salir_vehiculo(forzado=True)                          # el último usado: te espera, como siempre
    p._subir(otro, True, callar=True)
    p.salir_vehiculo(forzado=True)                          # ahora el último es este: el anterior ya no cuenta
    _lejos(p)
    assert mio in p.vehiculos and not mio.muerto            # el tuyo sigue ahí aunque hayas cogido otros dos
    assert robado not in p.vehiculos                        # el robado que dejaste atrás, no
    assert otro in p.vehiculos and p.tu_vehiculo() is otro
    assert p.es_mio(mio) and not p.es_mio(otro) and p.mis_en_calle() == 1
    # un vehículo de misión o un barco no pueden ser tuyos
    vm = p.crear_vehiculo("sedan", p.j.x + 5, p.j.y, 1, "aparcado", None, "mision")
    assert not p.hacer_mio(vm) and not p.es_mio(vm)
    assert PA.FORMATO == 3                                  # el formato de las partidas no cambia: las versiones anteriores siguen cargándolas


def test_lo_que_compras_mejoras_o_sacas_del_garaje_es_tuyo(robot):
    p = robot.nueva_partida()
    p.j.dinero = 200000
    casa = _casa_con_garaje(p, 4)
    # mejorar en el taller un vehículo robado lo pone a tu nombre; uno de misión se rechaza antes de cobrar
    v = p.crear_vehiculo("ambulancia" if "ambulancia" in p.modelos else "sedan", p.j.x + 6, p.j.y, 1, None)
    p._subir(v, True, callar=True)
    from juego.menus import Opcion
    ops = sistemas.opciones_taller(p, v, Opcion)
    antes = p.j.dinero
    ops[0].accion()
    assert p.j.dinero < antes and p.es_mio(v) and "queda a tu nombre" in robot.dicho()
    assert "Vale también para los vehículos de trabajo" in ops[0].ayuda
    p.salir_vehiculo(forzado=True)
    vm = p.crear_vehiculo("sedan", p.j.x + 9, p.j.y, 1, None, None, "mision")
    antes = p.j.dinero
    sistemas.opciones_taller(p, vm, Opcion)[0].accion()
    assert p.j.dinero == antes and not getattr(vm, "mejoras", {}) and "es de una misión" in robot.dicho()
    # garaje: entra con sus mejoras y su nombre; al sacarlo es tuyo
    v.nombre = "La Sirena"
    assert p.mandar_al_garaje(v, casa, cobrar=False) and v not in p.vehiculos and p.mis_en_calle() == 0 and p.mis_en_garajes() == 1
    ficha = p.j.garajes[casa.id][0]
    assert ficha["nombre"] == "La Sirena" and ficha["mejoras"]
    w = p.traer_mi_vehiculo(ficha, casa.id)
    assert w is not None and p.es_mio(w) and w.nombre == "La Sirena" and getattr(w, "mejoras", {}) == ficha["mejoras"] and not p.j.garajes[casa.id]


# ------------------------------------------------------------------ guardado, cambio de localidad y partidas antiguas
def test_se_guardan_con_su_sitio_y_sobreviven_al_cambio_de_localidad(robot):
    p = robot.nueva_partida()
    a = _comprar(p, "sedan", 6, "Rayo")
    sistemas.poner(a, {"motor": 2})
    a.salud = a.salud_max * 0.5
    b = _comprar(p, "moto" if "moto" in p.modelos else "utilitario", 14)
    xa, ya = a.x, a.y
    origen = p.mundo.id
    destino = next(m for m in p.mapas.values() if m.id != origen and m.tipo not in ("mar", "recinto"))
    l = next(iter(destino.lugares.values()))
    p._subir(b, False, callar=True)
    p.salir_vehiculo(forzado=True)
    p.cambiar_mapa(destino.id, l.x, l.y)                    # te vas a pie: los dos se quedan allí
    assert len(p.mis_lejos) == 2 and not p.mis_vivos() and p.veh_fuera is None
    assert [d.get("ultimo", False) for d in sorted(p.mis_lejos, key=lambda d: d["n"])] == [False, True]
    c = _comprar(p, "utilitario", 6)                        # y compras otro aquí
    d = json.loads(json.dumps(p.a_dict()))
    assert len(d["mis_vehiculos"]) == 3 and "veh_fuera" not in d
    robot.app.empezar_partida(d)
    robot.saltar_dialogos()
    q = robot.p
    assert q is not p and q.mundo.id == destino.id
    assert len(q.mis_vivos()) == 1 and len(q.mis_lejos) == 2 and q.mis_en_calle() == 3
    assert abs(q.mis_vivos()[0].x - c.x) < 0.5 and q.mis_vivos()[0].modelo["id"] == "utilitario"
    lo = next(iter(q.mapas[origen].lugares.values()))
    q.cambiar_mapa(origen, lo.x, lo.y)
    vivos = {v.nombre: v for v in q.mis_vivos()}
    assert len(vivos) == 2 and len(q.mis_lejos) == 1 and q.mis_lejos[0]["mapa"] == destino.id
    r = vivos["Rayo"]
    assert abs(r.x - xa) < 0.5 and abs(r.y - ya) < 0.5 and r.mejoras == {"motor": 2} and abs(r.salud / r.salud_max - 0.5) < 0.02
    assert q.tu_vehiculo() is not None and q.tu_vehiculo().modelo["id"] == b.modelo["id"]      # el último usado sigue siendo el último
    _lejos(q)
    assert r in q.vehiculos


def test_el_que_llevas_puesto_se_guarda_como_tuyo(robot):
    p = robot.nueva_partida()
    v = _comprar(p, "sedan", 5, "Trueno")
    p._subir(v, False, callar=True)
    d = json.loads(json.dumps(p.a_dict()))
    assert d["veh"]["mio"] and "mis_vehiculos" not in d
    robot.app.empezar_partida(d)
    robot.saltar_dialogos()
    q = robot.p
    assert q.j.veh is not None and q.es_mio(q.j.veh) and q.j.veh.nombre == "Trueno"


def test_las_partidas_antiguas_cargan(robot):
    p = robot.nueva_partida()
    base = json.loads(json.dumps(p.a_dict()))
    assert "mis_vehiculos" not in base and "mio_sec" not in base
    x, y = p.j.x + 8, p.j.y
    # una partida de antes, con el vehículo dejado en la calle y mejorado: pasa a ser tuyo
    vieja = dict(base, veh_fuera={"modelo": "sedan", "salud": 80, "nombre": "Sedán", "rumbo": 90, "x": x, "y": y, "mapa": p.mundo.id, "mejoras": {"motor": 1}, "donde": "por ahí"})
    robot.app.empezar_partida(json.loads(json.dumps(vieja)))
    robot.saltar_dialogos()
    q = robot.p
    assert len(q.mis_vivos()) == 1 and q.mis_vivos()[0].mejoras == {"motor": 1} and q.tu_vehiculo() is q.mis_vivos()[0] and q.veh_fuera is None
    # sin mejoras, se queda como antes: el último usado, que te espera, pero no es tuyo
    vieja["veh_fuera"]["mejoras"] = {}
    robot.app.empezar_partida(json.loads(json.dumps(vieja)))
    robot.saltar_dialogos()
    q = robot.p
    assert not q.mis_vivos() and q.tu_vehiculo() is not None and not q.es_mio(q.tu_vehiculo())
    # y con el vehículo puesto y mejorado
    vieja2 = dict(base, veh={"modelo": "sedan", "salud": 80, "nombre": "Sedán", "rumbo": 90, "mejoras": {"frenos": 2}})
    robot.app.empezar_partida(json.loads(json.dumps(vieja2)))
    robot.saltar_dialogos()
    assert robot.p.es_mio(robot.p.j.veh)
    # una lista con basura o con un modelo de un mod que ya no está no rompe nada
    rara = dict(base, mis_vehiculos=[{"modelo": "no_existe", "mapa": p.mundo.id, "x": 1, "y": 1, "n": 1}, "basura", {"sin": "modelo"}], mio_sec="x")
    robot.app.empezar_partida(json.loads(json.dumps(rara)))
    robot.saltar_dialogos()
    q = robot.p
    assert not q.mis_vivos() and len(q.mis_lejos) == 1 and MV.lista_mis_vehiculos(q) == []
    json.dumps(q.a_dict())


def test_si_el_juego_te_lleva_a_otra_localidad_el_tuyo_se_queda_aparcado(robot):
    p = robot.nueva_partida()
    mio = _comprar(p, "sedan", 5, "Rayo")
    p._subir(mio, False, callar=True)
    p.dejar_o_quitar(mio)                                   # lo que hace el juego al llevarte al hospital de otra localidad o al repetir una misión
    assert mio in p.vehiculos and p.j.veh is None
    ajeno = p.crear_vehiculo("utilitario", p.j.x + 5, p.j.y, 1, None)
    p._subir(ajeno, True, callar=True)
    p.dejar_o_quitar(ajeno)
    assert ajeno not in p.vehiculos                         # el que no es tuyo desaparece, como siempre
    otro = next(m for m in p.mapas.values() if m.id != p.mundo.id and m.tipo not in ("mar", "recinto"))
    l = next(iter(otro.lugares.values()))
    p.cambiar_mapa(otro.id, l.x, l.y)
    assert [d["nombre"] for d in p.mis_lejos] == ["Rayo"]
    # desde la lista, el GPS te guía hasta su localidad
    MV.menu_mis_vehiculos(p)
    _elegir(robot, "Rayo")
    _elegir(robot, "Marcar en el GPS el camino hasta su localidad")
    assert robot.app.pila[-1] is p and p.gps is not None


def test_el_ultimo_usado_sale_en_la_lista_y_se_puede_poner_a_tu_nombre(robot):
    p = robot.nueva_partida()
    v = p.crear_vehiculo("utilitario", p.j.x + 5, p.j.y, 1, None)
    p._subir(v, True, callar=True)
    p.salir_vehiculo(forzado=True)
    fichas = MV.lista_mis_vehiculos(p)
    assert [f["tipo"] for f in fichas] == ["ultimo"] and "si coges otro, se pierde" in fichas[0]["texto"]
    MV.menu_mis_vehiculos(p)
    _elegir(robot, p.modelos["utilitario"]["nombre"])
    _elegir(robot, "Ponerlo a tu nombre")
    assert p.es_mio(v) and "queda a tu nombre" in robot.dicho()
    assert [f["tipo"] for f in MV.lista_mis_vehiculos(p)] == ["calle"]


# ------------------------------------------------------------------ tope
def test_tope_en_la_calle(robot):
    p = robot.nueva_partida()
    assert MV.tope() == 6 and p.datos["vehiculos_propios"][0]["tope_calle"] == 6      # el tope está en los datos
    casa = _casa_con_garaje(p, 1)
    for l in [p.lug(x) for x in p.j.propiedades]:           # solo esa plaza de garaje
        if l is not None and l is not casa:
            l.d["garaje"] = 0
    coches = [_comprar(p, "sedan", 6 + 5 * k, f"Coche {k + 1}") for k in range(6)]
    assert p.mis_en_calle() == 6 and not p.j.garajes.get(casa.id)
    septimo = _comprar(p, "utilitario", 50)
    assert p.mis_en_calle() == 6 and coches[0] not in p.vehiculos                      # el más antiguo va solo al garaje
    assert p.j.garajes[casa.id][0]["nombre"] == "Coche 1" and "tu mecánico se lleva Coche 1" in robot.dicho()
    octavo = _comprar(p, "utilitario", 60)                                             # ya no hay sitio: se avisa y no se pierde ninguno
    assert p.mis_en_calle() == 7 and all(v in p.vehiculos for v in coches[1:] + [septimo, octavo])
    assert "No queda sitio en tus garajes" in robot.dicho()


def test_un_mod_cambia_el_tope(datos_de_serie):
    MV.configurar({"vehiculos_propios": [{"id": "general", "tope_calle": 2, "chofer_frases_llega": ["Aquí estoy."], "chofer_modelos": []}]})
    assert MV.tope() == 2 and MV.LISTAS["chofer_frases_llega"] == ["Aquí estoy."] and MV.LISTAS["chofer_modelos"]      # una lista vacía no deja al juego sin nada
    MV.configurar({})
    assert MV.tope() == 6 and len(MV.LISTAS["chofer_frases_llega"]) >= 3


# ------------------------------------------------------------------ 2 y 3. el móvil y el nombre
def test_mis_vehiculos_en_el_movil(robot):
    p = robot.nueva_partida()
    p.j.dinero = 5000
    casa = _casa_con_garaje(p, 3)
    a = _comprar(p, "sedan", 40, "Rayo")
    sistemas.poner(a, {"motor": 1})
    b = _comprar(p, "utilitario", 60)
    p.j.garajes.setdefault(casa.id, []).append({"modelo": "furgoneta", "salud": 100, "nombre": "La Gorda", "mejoras": {}})
    p.mis_lejos.append({"modelo": "sedan", "salud": 90, "nombre": "Sedán", "rumbo": 0, "x": 50, "y": 50, "mapa": next(m.id for m in p.mapas.values() if m.id != p.mundo.id and m.tipo not in ("mar", "recinto")),
                        "mejoras": {}, "donde": "junto a la plaza", "n": 9})
    fichas = MV.lista_mis_vehiculos(p)
    assert [f["tipo"] for f in fichas] == ["calle", "calle", "lejos", "garaje"]
    t = fichas[0]["texto"]
    assert t.startswith("Rayo, " + p.modelos["sedan"]["nombre"]) and "En la calle:" in t and "metros" in t and "Estado 100 por ciento" in t and "motor nivel 1" in t.lower()
    assert "En el garaje de" in fichas[3]["texto"] and "junto a la plaza" in fichas[2]["texto"]
    # por el menú del móvil
    robot.tecla(pygame.K_m)
    _elegir(robot, "Mis vehículos")
    m = robot.app.pila[-1]
    assert "3 en la calle, de 6, y 1 en garajes" in m.titulo
    _elegir(robot, "Rayo")
    acciones = [o.texto for o in robot.app.pila[-1].opciones]
    assert acciones[0] == "Marcarlo en el GPS" and any(x.startswith("Pedir que te lo traigan") for x in acciones) and any(x.startswith("Mandarlo a un garaje") for x in acciones) \
        and "Cambiarle el nombre" in acciones
    _elegir(robot, "Cambiarle el nombre")
    for _ in range(4):
        robot.tecla(pygame.K_BACKSPACE)
    _escribir(robot, "Centella")
    assert a.nombre == "Centella" and "Ahora se llama Centella" in robot.dicho()
    # marcar en el GPS
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    robot.tecla(pygame.K_m)
    _elegir(robot, "Mis vehículos")
    _elegir(robot, "Centella")
    _elegir(robot, "Marcarlo en el GPS")
    assert robot.app.pila[-1] is p and p.gps and p.gps["nombre"] == "Centella" and abs(p.gps["dest"][0] - a.x) < 1
    # que te lo traigan: de la calle, de otra localidad y del garaje
    dinero = p.j.dinero
    assert p.traer_mi_vehiculo(b) is b and b.dist(p.j.x, p.j.y) < 30 and p.j.dinero == dinero - p.precio("traer_vehiculo", 150)
    lejos = p.mis_lejos[0]
    v = p.traer_mi_vehiculo(lejos)
    assert v is not None and p.es_mio(v) and v.mio_n == 9 and not p.mis_lejos and v in p.vehiculos
    # mandar al garaje uno de la calle sin ir a por él
    assert p.mandar_al_garaje(a, casa) and a not in p.vehiculos and any(d["nombre"] == "Centella" for d in p.j.garajes[casa.id])
    # Mayúsculas L: va al último usado y dice cuántos más tienes
    p._subir(b, False, callar=True)
    p.salir_vehiculo(forzado=True)
    robot.tecla(pygame.K_l, pygame.KMOD_SHIFT)
    dicho = robot.dicho()
    assert p.gps["nombre"] == b.nombre and "Tienes otros 3 vehículos: están en el móvil, en Mis vehículos" in dicho, dicho[-400:]


def test_el_nombre_se_dice_al_subir_y_se_pone_en_el_garaje_y_en_el_taller(robot):
    p = robot.nueva_partida()
    p.j.dinero = 5000
    casa = _casa_con_garaje(p, 3)
    v = _comprar(p, "sedan", 5, "Rayo")
    p.j.x, p.j.y = v.x + 2, v.y
    robot.tecla(pygame.K_f)
    assert p.j.veh is v and f"Subes a Rayo, tu {p.modelos['sedan']['nombre']}" in robot.dicho()
    p.salir_vehiculo(forzado=True)
    # en el garaje de casa: opción de poner nombre, al de la calle y a los guardados
    p.j.garajes.setdefault(casa.id, []).append({"modelo": "furgoneta", "salud": 100, "nombre": p.modelos["furgoneta"]["nombre"], "mejoras": {}})
    p.teletransportar(casa.x, casa.y)
    v.x, v.y = p.j.x + 10, p.j.y
    p.ultimo_veh = v
    from juego import menus_juego
    menus_juego.lugar(p, casa)
    _elegir(robot, "Ponerle nombre a un vehículo")
    textos = [o.texto for o in robot.app.pila[-1].opciones]
    assert any("Rayo" in t and "en la calle" in t for t in textos) and any("en el garaje" in t for t in textos)
    _elegir(robot, p.modelos["furgoneta"]["nombre"])
    _escribir(robot, "La Gorda")
    assert p.j.garajes[casa.id][0]["nombre"] == "La Gorda"
    while robot.app.pila[-1] is not p:
        robot.tecla(pygame.K_ESCAPE)
    # en el taller: poner nombre a un vehículo robado lo deja a tu nombre
    taller = next(l for l in p.mundo.lugares.values() if l.tipo == "taller")
    r = p.crear_vehiculo("utilitario", taller.x, taller.y, 1, None)
    p._subir(r, True, callar=True)
    menus_juego.lugar(p, taller)
    _elegir(robot, "Ponerle nombre")
    _escribir(robot, "Chispa")
    assert r.nombre == "Chispa" and p.es_mio(r)
    # dejarlo vacío devuelve el nombre del modelo
    p.renombrar_vehiculo(r)
    for _ in range(8):
        robot.tecla(pygame.K_BACKSPACE)
    robot.tecla(pygame.K_RETURN)
    assert r.nombre == p.modelos["utilitario"]["nombre"]


# ------------------------------------------------------------------ 4. misiones
def test_el_resumen_de_la_mision_dice_lo_del_vehiculo(robot):
    p = robot.nueva_partida()
    por_id = {m["id"]: m for m in p.datos["misiones"]}
    assert p.mision_vehiculo_txt(por_id["m11"]).startswith("Te dan vehículo: Platino GT de Belmonte")
    assert p.mision_vehiculo_txt(por_id["m06"]).startswith("Te dejan un vehículo, Furgoneta de reparto, pero puedes hacerla con el tuyo")
    assert p.mision_vehiculo_txt(por_id["m03"]).startswith("Hay que llevarse un vehículo concreto: Sedán del moroso")
    assert "puedes hacerla con el tuyo" in p.mision_vehiculo_txt(por_id["v02"]) and "puedes hacerla con el tuyo" in p.mision_vehiculo_txt(por_id["x05"])
    assert p.mision_vehiculo_txt(por_id["eo6"]) == "Tienes que ir con un vehículo: vale el tuyo."
    assert p.mision_vehiculo_txt(por_id["m01"]) == ""
    # las que ya había exigen su vehículo, salvo aquellas en las que da igual con qué se lleve la carga (tres más desde la tanda 11)
    assert sorted(m["id"] for m in p.datos["misiones"] if m.get("vehiculo_libre")) == ["cd02", "m06", "of01", "v02", "x05"]
    # y se dice en la lista de misiones del móvil, antes de aceptarla
    p.completadas = [m["id"] for m in p.datos["misiones"] if m["id"] not in ("m06",) and m["id"] in por_id["m06"].get("requiere", [])]
    if por_id["m06"] in p.misiones_disponibles():
        robot.tecla(pygame.K_m)
        _elegir(robot, "Misiones disponibles")
        assert any("Te dejan un vehículo, Furgoneta de reparto" in o.texto for o in robot.app.pila[-1].opciones)


def _mision_reparto(p, libre):
    l = min((l for l in p.mundo.lugares.values() if l.tipo not in ("casa",)), key=lambda l: (l.x - p.j.x) ** 2 + (l.y - p.j.y) ** 2)
    dest = max(p.mundo.lugares.values(), key=lambda q: min(400, math.hypot(q.x - l.x, q.y - l.y)))
    m = {"id": "prueba_reparto", "titulo": "Reparto", "lugar": l.id, "recompensa": {"dinero": 5},
         "pasos": [{"tipo": "robar", "lugar": l.id, "modelo": "furgoneta", "abierto": True, "nombre": "Furgoneta de reparto", "texto": "Sube a la furgoneta."},
                   {"tipo": "entregar", "lugar": dest.id, "texto": "Llévala."}]}
    if libre:
        m["vehiculo_libre"] = True
    return m, l, dest


def test_mision_que_exige_su_vehiculo_deja_el_tuyo_a_salvo(robot):
    p = robot.nueva_partida()
    m, l, dest = _mision_reparto(p, False)
    p.teletransportar(l.x, l.y)
    robado = p.crear_vehiculo("sedan", p.j.x + 20, p.j.y, 1, None)
    p._subir(robado, True, callar=True)
    p.salir_vehiculo(forzado=True)
    assert not p.es_mio(robado)
    p._empezar_repetible(m)
    assert p.es_mio(robado) and "se queda aparcado y a salvo" in robot.dicho()
    vm = p.mision["veh"]
    p._subir(vm, False, callar=True)
    robot.frames(3)
    assert p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "entregar"
    # con tu vehículo no vale: la misión exige el suyo
    p.abandonar_mision() if hasattr(p, "abandonar_mision") else p._limpiar_mision()
    _lejos(p)
    assert robado in p.vehiculos and vm not in p.vehiculos


def test_mision_que_no_exige_modelo_se_hace_con_el_tuyo(robot):
    p = robot.nueva_partida()
    m, l, dest = _mision_reparto(p, True)
    p.teletransportar(l.x, l.y)
    mio = _comprar(p, "pickup" if "pickup" in p.modelos else "sedan", 4, "La Mula")
    p._empezar_repetible(m)
    assert "se puede hacer con tu vehículo" in robot.dicho()
    vm = p.mision["veh"]
    assert vm is not None and vm.tag == "mision"
    p._subir(mio, False, callar=True)
    mio.x, mio.y = vm.x + 6, vm.y                            # llegas con el tuyo junto al de la misión y te detienes
    robot.frames(3)
    assert p.mision["veh"] is mio and vm not in p.vehiculos and "Haces la misión con La Mula" in robot.dicho()
    assert p.mision["def"]["pasos"][p.mision["paso"]]["tipo"] == "entregar"
    mio.x, mio.y, mio.vel = dest.x, dest.y, 0.0
    robot.frames(3)
    robot.saltar_dialogos()
    assert p.mision is None and mio in p.vehiculos and not mio.muerto and p.j.veh is mio and p.es_mio(mio)      # entregado: el tuyo te lo quedas
    # una bici no vale para llevar la carga, ni un coche para una misión de helicóptero
    bici = p.crear_vehiculo("bici", p.j.x, p.j.y, 1, None)
    assert not p.vale_para_mision(bici, {"modelo": "furgoneta"}) and p.vale_para_mision(mio, {"modelo": "furgoneta"})
    if "helicoptero" in p.modelos:
        assert not p.vale_para_mision(mio, {"modelo": "helicoptero"})


def test_fallar_una_mision_hecha_con_tu_vehiculo_no_te_lo_quita(robot):
    p = robot.nueva_partida()
    m, l, dest = _mision_reparto(p, True)
    p.teletransportar(l.x, l.y)
    mio = _comprar(p, "sedan", 4)
    p._empezar_repetible(m)
    vm = p.mision["veh"]
    p._subir(mio, False, callar=True)
    mio.x, mio.y = vm.x + 6, vm.y
    robot.frames(3)
    assert p.mision["veh"] is mio
    p._limpiar_mision()
    assert p.mision is None and mio in p.vehiculos and not mio.muerto and p.j.veh is mio


# ------------------------------------------------------------------ 5. chófer
def _con_banda(p):
    p.j.territorios = [p.mundo.barrios[0]["id"]]
    p.j.banda, p.j.banda_nombre = 2, "Los Mirlos"
    p.j.dinero = 5000
    p.cfg["sucesos"] = False
    p.cfg.v["sin_policia"] = True


def _esperar(robot, cond, segundos=100):
    for _ in range(int(segundos * 30 / 10)):
        robot.frames(10)
        if cond():
            return True
    return False


def test_chofer_requisitos(robot):
    p = robot.nueva_partida()
    p.j.dinero = 5000
    assert not p.pedir_chofer() and p.chofer is None and "necesitas a alguien reclutado" in robot.dicho() and p.j.dinero == 5000
    _con_banda(p)
    p.j.estrellas = 4
    assert not p.pedir_chofer() and "nadie de la banda se acerca" in robot.dicho()
    p.j.estrellas = 0
    p.j.dinero = 10
    assert not p.pedir_chofer() and p.chofer is None                                   # cuesta dinero
    p.j.dinero = 5000
    assert p.pedir_chofer() and p.j.dinero == 5000 - p.precio("chofer", 80) and p.chofer["estado"] == "espera"
    assert MV.AJUSTES["chofer_espera_min"] * 0.8 <= p.chofer["t"] <= MV.AJUSTES["chofer_espera_max"] * 1.3
    assert not p.pedir_chofer() and "ya está en ello" in robot.dicho()                  # uno cada vez
    assert p.despedir_chofer() and p.chofer is None and "Se da la vuelta" in robot.dicho()
    esperas = set()
    for _ in range(6):                                                                 # la espera cambia cada vez
        p.pedir_chofer()
        esperas.add(round(p.chofer["t"], 1))
        p.despedir_chofer(callar=True)
    assert len(esperas) >= 4


def test_chofer_viene_te_recoge_y_te_lleva(robot):
    p = robot.nueva_partida()
    _con_banda(p)
    p.cfg["conduccion"] = "libre"                           # aunque conduzcas tú a mano, el chófer lleva el coche por la calle
    p.cfg["piloto_gps"] = False
    assert p.pedir_chofer()
    nombre = p.chofer["nombre"]
    assert nombre.endswith(", de Los Mirlos") and "oirás el claxon" in robot.dicho()
    p.chofer["t"] = 0.2
    robot.frames(10)
    assert p.chofer["estado"] == "viene"
    v = p.chofer["veh"]
    assert v.tag == "banda" and v.ia == "chofer" and v.dist(p.j.x, p.j.y) > 100 and "ya viene" in robot.dicho()
    assert _esperar(robot, lambda: p.chofer["estado"] == "aqui"), (p.chofer, v.dist(p.j.x, p.j.y))
    assert v.dist(p.j.x, p.j.y) < 40 and v.vel == 0 and v.sirena is not None and "Sube con F" in robot.dicho()
    # no se puede guardar ni vender: es de la banda
    assert "es de tu banda" in p.motivo_ajeno(v)
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 2.5, v.y)
    p.cancelar_gps()
    robot.tecla(pygame.K_f)
    assert p.j.veh is v and p.chofer["estado"] == "contigo" and p.chofer_conduce() and "de pasajero" in robot.dicho() and v.sirena is None
    # sin destino no se mueve, y lo pide; las teclas de conducir no hacen nada
    robot.frames(30, mantener=(pygame.K_UP,))
    assert v.vel == 0 and "La L abre la lista de lugares" in robot.dicho()
    robot.tecla(pygame.K_y)
    assert p.cfg["piloto_gps"] is False and "tú vas de pasajero" in robot.dicho()
    # marcas un destino y te lleva él
    dest = min((l for l in p.mundo.lugares.values() if 180 < math.hypot(l.x - v.x, l.y - v.y) < 450), key=lambda l: math.hypot(l.x - v.x, l.y - v.y))
    p.gps_a_lugar(dest)
    x0, y0 = v.x, v.y
    robot.frames(90)
    assert v.vel > 2 and math.hypot(v.x - x0, v.y - y0) > 5, (v.vel, p.libre_temp, p.modo_asistido())
    assert _esperar(robot, lambda: math.hypot(dest.x - v.x, dest.y - v.y) < 30 and v.vel < 0.6, 240), (math.hypot(dest.x - v.x, dest.y - v.y), v.vel, robot.dicho()[-300:])
    assert _esperar(robot, lambda: "Con F te bajas, y te espera" in robot.dicho(), 10), robot.dicho()[-400:]
    assert f"Has llegado a {dest.nombre}" in robot.dicho() and any(f in robot.dicho() for f in MV.LISTAS["chofer_frases_marcha"])
    # te bajas: te espera
    robot.tecla(pygame.K_f)
    robot.frames(3)
    assert p.j.veh is None and p.chofer["estado"] == "aqui" and v in p.vehiculos
    _lejos(p, 300)
    assert v in p.vehiculos                                  # no se va aunque te alejes
    # lo despides: se lleva el coche de la banda
    assert p.despedir_chofer() and p.chofer is None and v not in p.vehiculos and "Se lleva el vehículo" in robot.dicho()


def test_chofer_con_un_vehiculo_de_tu_garaje(robot):
    p = robot.nueva_partida()
    _con_banda(p)
    casa = _casa_con_garaje(p, 2)
    ficha = {"modelo": "todoterreno" if "todoterreno" in p.modelos else "sedan", "salud": 120, "nombre": "El Tanque", "mejoras": {"blindaje": 1}}
    p.j.garajes.setdefault(casa.id, []).append(ficha)
    # por el menú: Servicios, Chófer
    from juego import menus_extra
    menus_extra.servicios(p)
    _elegir(robot, "Chófer de tu banda")
    _elegir(robot, "Que venga con El Tanque")
    assert robot.app.pila[-1] is p and p.chofer["estado"] == "espera" and ficha in p.j.garajes[casa.id]      # hasta que sale, sigue en el garaje
    d = json.loads(json.dumps(p.a_dict()))
    assert d["jugador"]["garajes"][casa.id][0]["nombre"] == "El Tanque"                 # si guardas mientras esperas, no se pierde
    p.chofer["t"] = 0.1
    robot.frames(10)
    v = p.chofer["veh"]
    assert v.nombre == "El Tanque" and not v.tag and p.es_mio(v) and v.mejoras == {"blindaje": 1} and not p.j.garajes[casa.id]
    assert _esperar(robot, lambda: p.chofer["estado"] == "aqui")
    p.j.x, p.j.y = p.mundo.punto_libre(v.x + 2.5, v.y)
    robot.tecla(pygame.K_f)
    assert p.chofer_conduce()
    # despedirlo yendo dentro: te quedas con tu vehículo, al volante
    menus_extra.servicios(p)
    _elegir(robot, "Chófer de tu banda")
    assert "va al volante" in robot.app.pila[-1].opciones[0].texto
    _elegir(robot, "Despedir al chófer")
    assert p.chofer is None and p.j.veh is v and not p.chofer_conduce() and "ahora conduces tú" in robot.dicho()
    robot.frames(40, mantener=(pygame.K_UP,))
    assert v.vel > 1                                          # y ya conduces tú
    # si el chófer está viniendo y cambias de localidad a pie, tu vehículo se queda allí, a tu nombre
    p.salir_vehiculo(forzado=True)
    p.mandar_al_garaje(v, casa, cobrar=False)
    assert p.pedir_chofer(casa.id, p.j.garajes[casa.id][0])
    p.chofer["t"] = 0.1
    robot.frames(10)
    assert p.chofer["estado"] == "viene"
    otro = next(m for m in p.mapas.values() if m.id != p.mundo.id and m.tipo not in ("mar", "recinto"))
    l = next(iter(otro.lugares.values()))
    p.cambiar_mapa(otro.id, l.x, l.y)
    assert p.chofer is None and len(p.mis_lejos) == 1 and p.mis_lejos[0]["nombre"] == "El Tanque"
    robot.frames(5)


def test_chofer_si_revienta_el_vehiculo_te_quedas_sin_el(robot):
    p = robot.nueva_partida()
    _con_banda(p)
    assert p.pedir_chofer()
    p.chofer["t"] = 0.1
    robot.frames(10)
    v = p.chofer["veh"]
    p.quitar_vehiculo(v)
    robot.frames(3)
    assert p.chofer is None and "Te has quedado sin chófer" in robot.dicho()


# ------------------------------------------------------------------ 6. en un servidor
def test_en_un_servidor_manda_el_servidor(app, tmp_path):
    from conftest import Robot
    from test_enlinea import entrar
    from test_servidor import Banco, lejos_de_todo
    banco = Banco(tmp_path)
    robot = Robot(app)
    try:
        p = entrar(robot, banco, "Ana")
        x, y = lejos_de_todo(p.mundo.id)
        p.teletransportar(x, y)
        robot.frames(20)
        v = p.crear_vehiculo("sedan", x + 4, y, 1, None)
        assert not p.hacer_mio(v) and not p.es_mio(v)       # en un servidor no hay vehículos «tuyos» locales
        p._subir(v, False)

        def hasta(cond, segundos=8.0):
            import time
            fin = time.time() + segundos
            while time.time() < fin:
                robot.frames(2)
                if cond():
                    return True
                time.sleep(0.01)
            return False
        assert hasta(lambda: getattr(v, "id_red", None) is not None)
        assert [f["tipo"] for f in MV.lista_mis_vehiculos(p)] == ["llevas"]
        v.nombre = "Rayo"                                   # le pones nombre y lo dejas: el servidor lo apunta con ese nombre
        p.salir_vehiculo(forzado=True)
        assert hasta(lambda: banco.srv.vehiculos.get(v.id_red, {}).get("nombre") == "Rayo" and banco.srv.vehiculos[v.id_red]["por"] is None)
        fichas = MV.lista_mis_vehiculos(p)
        assert [f["tipo"] for f in fichas] == ["servidor"] and fichas[0]["texto"].startswith("Rayo, ")
        d = p.a_dict()
        assert "mis_vehiculos" not in d
        ident = v.id_red
        # al volver a entrar, el servidor dice cuáles son tuyos
        p.sv_salir()
        p.desconectar_online()
        p = entrar(robot, banco, "Ana")
        assert p.sv["mios"] == {ident}
        fichas = MV.lista_mis_vehiculos(p)
        assert len(fichas) == 1 and fichas[0]["tipo"] == "servidor" and "Rayo" in fichas[0]["texto"]
        # el móvil lo enseña, con el aviso de que los guarda el servidor
        MV.menu_mis_vehiculos(p)
        m = robot.app.pila[-1]
        assert "1 en la calle del servidor" in m.titulo and any("los guarda el servidor" in o.texto for o in m.opciones)
        # si el servidor lo retira, deja de salir
        banco.srv._quitar_vehiculo(ident)
        assert hasta(lambda: not MV.lista_mis_vehiculos(p))
    finally:
        if app.partida is not None:
            app.partida.sv_salir()
            app.partida.desconectar_online()
        banco.parar()


def test_un_servidor_anterior_no_dice_cuales_son_tuyos(robot):
    """Con un servidor que no manda la lista, solo se sabe de los que dejas en esta sesión: nada se rompe."""
    p = robot.nueva_partida()
    p.en_servidor = True
    p.sv = {"vehs": {7: {"id": 7, "modelo": "sedan", "nombre": "Sedán", "m": p.mundo.id, "x": 1, "y": 1, "salud": 100, "por": None}}}
    try:
        assert p.sv_mis_vehiculos() == [] and MV.lista_mis_vehiculos(p) == []
        p.sv["mios"] = {7, 99}
        assert [d["id"] for d, v in p.sv_mis_vehiculos()] == [7]
        p.sv["vehs"][7]["por"] = 3                           # se lo ha llevado otro
        assert p.sv_mis_vehiculos() == []
    finally:
        p.en_servidor = False


def test_el_servidor_sigue_valiendo_para_python_38():
    import ast
    import os
    raiz = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "servidor")
    for nombre in os.listdir(raiz):
        if nombre.endswith(".py"):
            with open(os.path.join(raiz, nombre), encoding="utf-8") as f:
                ast.parse(f.read(), feature_version=(3, 8))
