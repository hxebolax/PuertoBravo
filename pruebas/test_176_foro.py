"""Lo que contaron en el foro tras la 1.7.5 (segunda tanda) y las issues 25, 33 y 44, para la 1.7.6."""
import json

import pygame

from juego import comunidad, encuentros, i18n, teclado
from juego.menus import Menu


def _casa_con_garaje(p, plazas=4):
    l = next(l for l in p.mundo.lugares.values() if l.tipo == "casa" and int(l.get("garaje", 0)) > 0)
    if l.id not in p.j.propiedades:
        p.j.propiedades.append(l.id)
    l.d["garaje"] = plazas
    return l


def _recargar(robot, p):
    d = json.loads(json.dumps(p.a_dict()))
    robot.app.empezar_partida(d)
    robot.saltar_dialogos()
    return robot.p


# ------------------------------------------------------------------ foro: el taxi del garaje
def test_el_taxi_guardado_sigue_siendo_un_taxi(robot):
    p = robot.nueva_partida()
    casa = _casa_con_garaje(p)
    v = p.crear_vehiculo("taxi", p.j.x + 6, p.j.y, 1, None)
    assert p.hacer_mio(v)
    assert p.mandar_al_garaje(v, casa, cobrar=False)
    q = _recargar(robot, p)
    q.j.dinero = 100000
    ficha = q.j.garajes[casa.id][0]
    assert ficha["modelo"] == "taxi"                          # al cargar ya no se vuelve «un taxi»
    w = q.traer_mi_vehiculo(ficha, casa.id)
    assert w is not None and w.modelo["id"] == "taxi" and w.modelo.get("trabajo") == "taxi"


def test_el_taxi_que_ya_se_perdio_vuelve_a_ser_taxi(robot):
    """Una partida guardada con la 1.7.5 después de cargar ya lleva «un taxi» en el garaje: al sacarlo, es un taxi."""
    p = robot.nueva_partida()
    p.j.dinero = 100000
    casa = _casa_con_garaje(p)
    ficha = {"modelo": "un taxi", "salud": 130.0, "nombre": "Taxi", "mejoras": {}}
    p.j.garajes[casa.id] = [ficha]
    w = p.traer_mi_vehiculo(ficha, casa.id)
    assert w is not None and w.modelo["id"] == "taxi"


def test_un_identificador_no_se_cambia_por_una_frase():
    d = {"modelo": "taxi", "veh": {"modelo": "taxi"}, "nombre": "Taxi"}
    i18n.al_idioma_de_ahora(d)
    assert d["modelo"] == "taxi" and d["veh"]["modelo"] == "taxi"
    assert i18n.identificador_perdido("un taxi", {"taxi": 1, "sedan": 1}) == "taxi"
    assert i18n.identificador_perdido("nada de nada", {"taxi": 1}) is None


# ------------------------------------------------------------------ foro: la búsqueda al cargar
def test_si_te_buscaban_al_guardar_te_siguen_buscando(robot):
    p = robot.nueva_partida()
    p.poner_busqueda(3)
    robot.frames(2)
    assert p.j.estrellas == 3
    q = _recargar(robot, p)
    assert q.j.puntos_busqueda > 0
    robot.frames(2)
    assert q.j.estrellas == 3 and "Nivel de búsqueda 3" in robot.dicho()


def test_sin_policia_la_partida_carga_sin_busqueda(robot):
    p = robot.nueva_partida()
    p.poner_busqueda(2)
    robot.frames(2)
    robot.app.cfg["sin_policia"] = True
    try:
        q = _recargar(robot, p)
        assert q.j.puntos_busqueda == 0 and q.j.estrellas == 0
    finally:
        robot.app.cfg["sin_policia"] = False


# ------------------------------------------------------------------ foro: seguir a alguien que empieza a tu lado
def test_seguir_a_quien_esta_a_tu_lado_no_falla_al_momento(robot):
    p = robot.nueva_partida()
    l = p.lugares["ayuntamiento"] if "ayuntamiento" in p.lugares and p.lugares["ayuntamiento"].mapa == p.mundo.id else next(iter(p.mundo.lugares.values()))
    m = {"id": "prueba_seguir", "titulo": "Prueba", "lugar": l.id, "pasos": [
        {"tipo": "seguir", "lugar": l.id, "destino": l.id, "persona": "el inspector", "texto": "Síguele."}]}
    p.teletransportar(l.x, l.y)
    p._empezar_repetible(dict(m, repetible=True))
    robot.saltar_dialogos()
    for _ in range(4 * 30):                                    # cuatro segundos pegado a él, mientras espera quieto
        robot.frames(1)
        if p.mision is None:
            break
    assert p.mision is not None, robot.dicho()
    assert "apártate unos metros antes de que salga" in robot.dicho()


# ------------------------------------------------------------------ issue 44: la pareja y los horarios
def _con_pareja_en_casa(p):
    j = p.j
    pers = p.persona_social("lucia")
    r = p.relacion("lucia")
    r.update(estado="pareja", afinidad=70, citas=5, ultimo=p.dia)
    j.pareja = j.convive = "lucia"
    j.convive_casa = "casa_abuela"
    return pers


def test_la_pareja_no_esta_en_casa_y_en_su_trabajo_a_la_vez(robot):
    p = robot.nueva_partida()
    pers = _con_pareja_en_casa(p)
    p.cfg["horarios"] = "todo"
    try:
        for dia in range(1, 8):
            for minuto in range(0, 1440, 30):
                p.dia, p.reloj = dia, float(minuto)
                if encuentros.presente(p, pers):
                    assert not p.pareja_en_casa(), (dia, minuto)
                ficha = encuentros.donde_txt(p, pers)
                assert not ("Ahora está allí" in ficha and p.pareja_en_casa())
                if p.pareja_en_casa():
                    assert "Ahora está en vuestra casa" in ficha
        p.cfg["horarios"] = "apagado"                          # con los horarios apagados, como siempre: de noche, en casa
        p.reloj = 23 * 60.0
        assert p.pareja_en_casa()
    finally:
        p.cfg["horarios"] = "apagado"


# ------------------------------------------------------------------ issue 44: el horario de un local con F2
def test_f2_dice_el_horario_de_un_local_en_la_lista_de_lugares(robot):
    p = robot.nueva_partida()
    p.cfg["horarios"] = "todo"
    try:
        banco = next(l for l in p.mundo.lugares.values() if l.tipo == "banco")
        txt = encuentros.horario_consulta(p, banco)
        assert txt and txt.startswith("Abre de") and ("abierto" in txt or "cerrado" in txt)
        from juego import menus_juego
        menus_juego.lista_lugares(p)
        grupos = robot.app.pila[-1]
        grupos.i = 0
        robot.tecla(pygame.K_RETURN)                           # Todos los lugares
        lista = robot.app.pila[-1]
        lista.i = next(k for k, o in enumerate(lista.opciones) if getattr(o, "lugar", None) is banco)
        robot.tecla(pygame.K_F2)
        assert txt in robot.dicho()
        assert txt in lista.opciones[lista.i].ayuda             # F1, y el botón Y del mando, lo dicen también
        p.cfg["horarios"] = "apagado"
        assert encuentros.horario_consulta(p, banco) is None
        robot.tecla(pygame.K_F2)
        assert "con los horarios de los locales apagados" in robot.dicho()
    finally:
        p.cfg["horarios"] = "apagado"


# ------------------------------------------------------------------ issue 33: misiones que piden contratos
def test_una_mision_puede_pedir_contratos_del_tablon(robot):
    p = robot.nueva_partida()
    taberna = next(l for l in p.mundo.lugares.values() if l.tipo == "taberna")
    otra = next(l for l in p.mundo.lugares.values() if l.tipo != "taberna" and l is not taberna)
    m = {"id": "pide_contratos", "titulo": "Pide contratos", "lugar": otra.id, "requiere": [],
         "requiere_vida": {"contratos": 2, "tablon": taberna.id}, "pasos": [{"tipo": "ir", "lugar": otra.id, "texto": "Ve."}]}
    p.datos["misiones"].append(m)
    try:
        assert m not in p.misiones_disponibles()
        assert p.falta_vida(m) == [f"cumplir 2 contratos del tablón de {p.nombre_lugar(taberna)}; llevas 0"]
        for _ in range(2):                                     # dos contratos de ese tablón, cumplidos
            o = p.ofertas_contrato(taberna)[0]
            p.empezar_contrato_de(taberna, o)
            p._completar_mision()
        assert p.j.stats["contratos_tablon"][taberna.id] == 2 and p.contratos_cumplidos() >= 2
        assert m in p.misiones_disponibles() and "Nueva misión disponible: Pide contratos" in robot.dicho()
        # sin tablón, cuentan todos; y por tipo de sitio, también
        m["requiere_vida"] = {"contratos": 3}
        assert p.falta_vida(m) == ["cumplir 3 contratos del tablón; llevas 2"]
        assert p.contratos_cumplidos("taberna") == 2
    finally:
        p.datos["misiones"].remove(m)


def test_el_editor_edita_los_contratos_que_pide_una_mision():
    from editor.esquema import ESQUEMAS
    campos = {c["k"] for c in ESQUEMAS["requisitos_vida"]["campos"]}
    assert {"contratos", "tablon"} <= campos


# ------------------------------------------------------------------ foro: las teclas cambiadas en lo que se dice
def test_las_frases_nombran_tus_teclas(robot):
    cfg = robot.app.cfg
    antes = dict(cfg["teclas"])
    try:
        teclado.restablecer(cfg)
        assert teclado.textos(cfg, "Pulsa Q para fijarlo.") == "Pulsa Q para fijarlo."
        teclado.cambiar(cfg, pygame.K_q, pygame.K_p)           # la Q pasa a la P, y la P a la Q
        assert teclado.textos(cfg, "Pulsa Q para fijarlo.") == "Pulsa P para fijarlo."
        assert teclado.textos(cfg, "La tecla Q fija y la tecla P pausa.") == "La tecla P fija y la tecla Q pausa."
        assert teclado.textos(cfg, "Press Q to lock on.") == "Press P to lock on."
        assert teclado.textos(cfg, "Quiero ir a Quintana.") == "Quiero ir a Quintana."      # una Q que no es una tecla
        p = robot.nueva_partida()
        p.decir("Pulsa Q para fijarlo.")
        assert "Pulsa P para fijarlo." in robot.dicho()
    finally:
        cfg["teclas"] = antes


# ------------------------------------------------------------------ issue 25: aprender a jugar, por idiomas
def test_la_comunidad_tiene_aprender_a_jugar_por_idiomas(robot):
    d = comunidad.cargar()
    s = next(s for s in d["secciones"] if s["id"] == "aprender")
    assert s.get("por_idioma") and any(e.get("tipo") for e in s["enlaces"])
    comunidad.menu(robot.app)
    m = robot.app.pila[-1]
    m.i = next(k for k, o in enumerate(m.opciones) if o.texto.startswith("Aprender a jugar"))
    robot.tecla(pygame.K_RETURN)
    idiomas = robot.app.pila[-1]
    assert isinstance(idiomas, Menu) and idiomas.opciones[0].texto.startswith("En español:")      # el del juego, el primero
    robot.tecla(pygame.K_RETURN)
    lista = robot.app.pila[-1]
    assert lista.opciones[0].texto == "Tutorial de iniciación a Puerto Bravo: tutorial en audio"
