"""Pruebas del Menú de Trampas y su puente IPC en tiempo real."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import os
import time

import pytest

from trampas import descubrir_instancias
from trampas.protocolo import ClienteTrampas, ErrorPuente
from trampas import puente


def _llamar_vivo(app, cliente: ClienteTrampas, cmd: str, **args):
    """Ejecuta una llamada TCP real contra el puente mientras App.paso drena la cola."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(cliente.llamar, cmd, **args)
        limite = time.monotonic() + 4.0
        while not fut.done() and time.monotonic() < limite:
            app.paso(1 / 60)
            time.sleep(0.002)
        return fut.result(timeout=1.0)


def _conectar_vivo(app, carpeta: str):
    """Ejecuta conectar_auto en segundo plano mientras App.paso atiende el saludo 'hola'."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(ClienteTrampas.conectar_auto, carpeta=carpeta)
        limite = time.monotonic() + 4.0
        while not fut.done() and time.monotonic() < limite:
            app.paso(1 / 60)
            time.sleep(0.002)
        return fut.result(timeout=1.0)


@pytest.fixture
def puente_activo(robot, tmp_path, monkeypatch):
    monkeypatch.setenv("PUERTOBRAVO_TRAMPAS_DIR", str(tmp_path))
    p = robot.nueva_partida()
    srv = puente.iniciar(robot.app, forzar=True, carpeta=str(tmp_path))
    assert srv is not None
    cli, info = _conectar_vivo(robot.app, str(tmp_path))
    yield robot, p, srv, cli, info, tmp_path
    puente.detener(robot.app)


def test_puente_descubrimiento_auth_y_cierre(robot, tmp_path, monkeypatch):
    monkeypatch.setenv("PUERTOBRAVO_TRAMPAS_DIR", str(tmp_path))
    assert robot.app.cfg["permitir_trampas"] is False
    assert getattr(robot.app, "_puente_trampas", None) is None  # apagado por defecto en pruebas
    assert descubrir_instancias(str(tmp_path)) == []

    # Enciende al activar la opción del juego y limpia todo al apagarla
    robot.app.cfg["permitir_trampas"] = True
    robot.app.actualizar_puente_trampas()
    srv = getattr(robot.app, "_puente_trampas", None)
    assert srv is not None and srv._activo is True
    assert len(descubrir_instancias(str(tmp_path))) == 1

    robot.app.cfg["permitir_trampas"] = False
    robot.app.actualizar_puente_trampas()
    assert getattr(robot.app, "_puente_trampas", None) is None
    assert srv._sock is None
    assert descubrir_instancias(str(tmp_path)) == []

    srv = puente.iniciar(robot.app, forzar=True, carpeta=str(tmp_path))
    instancias = descubrir_instancias(str(tmp_path))
    assert len(instancias) == 1
    assert instancias[0]["pid"] == os.getpid()

    cli_malo = ClienteTrampas(srv.puerto, "token-invalido")
    with pytest.raises(ErrorPuente, match="Token"):
        cli_malo.llamar("hola")

    cli_ok, info = _conectar_vivo(robot.app, str(tmp_path))
    assert info["info"]["pid"] == os.getpid()
    assert info["info"]["en_partida"] is False

    puente.detener(robot.app)
    assert getattr(robot.app, "_puente_trampas", None) is None
    assert descubrir_instancias(str(tmp_path)) == []


def test_puente_limite_conexiones_simultaneas(robot, tmp_path, monkeypatch):
    import json
    import socket
    from trampas.protocolo import leer_linea_socket

    monkeypatch.setenv("PUERTOBRAVO_TRAMPAS_DIR", str(tmp_path))
    srv = puente.iniciar(robot.app, forzar=True, carpeta=str(tmp_path))
    retenidos = []
    try:
        for _ in range(puente.MAX_CONEXIONES):
            s = socket.create_connection(("127.0.0.1", srv.puerto), timeout=2.0)
            retenidos.append(s)
        # Esperar brevemente a que el bucle acepte los sockets hasta llenar el semáforo
        limite = time.monotonic() + 2.0
        while srv._sem_conns._value > 0 and time.monotonic() < limite:
            time.sleep(0.01)
        assert srv._sem_conns._value == 0

        # Las conexiones extra se rechazan al instante sin crear más hilos
        rechazadas = 0
        for _ in range(4):
            extra = socket.create_connection(("127.0.0.1", srv.puerto), timeout=2.0)
            with extra:
                extra.settimeout(2.0)
                linea = leer_linea_socket(extra)
                if linea:
                    resp = json.loads(linea)
                    if not resp.get("ok") and "Demasiadas conexiones" in resp.get("error", ""):
                        rechazadas += 1
        assert rechazadas == 4
    finally:
        for s in retenidos:
            try:
                s.close()
            except OSError:
                pass

    # Tras liberar conexiones, el puente atiende normalmente
    cli_ok, _ = _conectar_vivo(robot.app, str(tmp_path))
    assert cli_ok is not None
    puente.detener(robot.app)


def test_catalogos_dinamicos(robot):
    robot.nueva_partida()
    cat = puente.despachar(robot.app, "catalogos", {})
    assert len(cat["vehiculos"]) >= 39
    assert len(cat["armas"]) >= 28
    assert len(cat["tipos_enemigo"]) >= 10
    assert len(cat["bandas"]) >= 5
    assert len(cat["mapas"]) >= 8
    assert "motor" in cat["mejoras"]
    assert len(cat["objetos"]) >= 5
    assert len(cat["objetos_valor"]) >= 20
    assert len(cat["dias_azar"]) >= 5


def test_jugador_habilidades_y_teletransporte(robot):
    p = robot.nueva_partida()
    res = puente.despachar(
        robot.app, "jugador.set",
        {
            "dinero_delta": 5000, "banco": 12000, "salud_max": 150, "salud": 140, "blindaje": 90,
            "hambre": 80, "sed": 70, "sueno": 60, "suciedad": 50, "carne_puntos": 7,
        },
    )
    assert res["jugador"]["dinero"] == 5050
    assert res["jugador"]["banco"] == 12000
    assert res["jugador"]["salud"] == 140.0
    assert p.j.carne_puntos == 7

    puente.despachar(robot.app, "jugador.set", {"accion": "llenar_necesidades"})
    assert p.j.hambre == 0.0 and p.j.sed == 0.0 and p.j.sueno == 0.0 and p.j.suciedad == 0.0

    hab = puente.despachar(robot.app, "jugador.habilidad", {"habilidad": "conduccion", "nivel": 8})
    assert hab["nivel"] == 8 and p.nivel("conduccion") == 8

    # Teletransporte a otra localidad
    san_lugar = next(l for l in p.lugares.values() if l.mapa == "san_lucero")
    tp = puente.despachar(robot.app, "jugador.teletransportar", {"lugar_id": san_lugar.id})
    assert tp["mapa"] == "san_lucero"
    assert p.mundo.id == "san_lucero"


def test_inventario_completo(robot):
    p = robot.nueva_partida()
    puente.despachar(
        robot.app, "inventario.arma",
        {"accion": "dar", "arma_id": "fusil", "balas": 400, "silenciador": True, "ampliado": True},
    )
    assert "fusil" in p.j.armas
    assert p.j.armas["fusil"]["silenciador"] is True
    assert p.j.armas["fusil"]["ampliado"] is True
    assert p.j.arma == "fusil"

    puente.despachar(robot.app, "inventario.arma", {"accion": "quitar", "arma_id": "fusil"})
    assert "fusil" not in p.j.armas
    assert p.j.arma == "punos"

    puente.despachar(robot.app, "inventario.objeto", {"tipo": "objeto", "id": "botiquin", "cantidad": 5})
    assert p.j.objetos["botiquin"] >= 6

    puente.despachar(robot.app, "inventario.objeto", {"tipo": "mochila_grande", "valor": True})
    assert p.j.mochila_grande is True

    puente.despachar(robot.app, "inventario.objeto", {"tipo": "valor", "id": "dron", "cantidad": 1, "robado": True})
    assert any(x["id"] == "dron" and x["robado"] for x in p.j.mochila)

    puente.despachar(robot.app, "inventario.objeto", {"tipo": "vaciar_robados"})
    assert all(not x["robado"] for x in p.j.mochila)


def test_vehiculos_crear_y_editar_aislado(robot):
    p = robot.nueva_partida()
    vel_proto_original = p.modelos["sedan"]["vel_max"]

    c1 = puente.despachar(
        robot.app, "vehiculos.crear",
        {"modelo_id": "sedan", "nombre": "Mi Rayo", "hacer_mio": True, "subir_ahora": True, "mejoras_max": True},
    )["vehiculo"]
    assert p.j.veh is not None and p.j.veh.id == c1["id"]
    assert p.j.veh.mio is True

    # Crear un segundo sedan distinto para verificar aislamiento al editar solo este ejemplar
    c2 = puente.despachar(
        robot.app, "vehiculos.crear",
        {"modelo_id": "sedan", "hacer_mio": False, "subir_ahora": False},
    )["vehiculo"]

    edit = puente.despachar(
        robot.app, "vehiculos.editar",
        {
            "id": c1["id"], "solo_este": True, "reparar": True, "llenar_combustible": True,
            "specs": {"vel_max": 95.0, "acel": 30.0, "freno": 40.0},
        },
    )["vehiculo"]
    assert edit["vel_max"] == 95.0
    assert p.modelos["sedan"]["vel_max"] == vel_proto_original
    v2 = next(v for v in p.vehiculos if v.id == c2["id"])
    assert v2.modelo["vel_max"] == vel_proto_original

    puente.despachar(robot.app, "vehiculos.accion", {"id": c2["id"], "accion": "eliminar"})
    assert all(v.id != c2["id"] for v in p.vehiculos)


def test_npcs_y_bandas(robot):
    p = robot.nueva_partida()
    cre = puente.despachar(
        robot.app, "npcs.crear",
        {
            "modo": "pandillero", "clase": "pandillero_duro", "banda": "Los Calaveras",
            "arma": "escopeta", "cantidad": 2, "salud": 120, "hostil": True, "en_vehiculo": False,
        },
    )
    ids = [x["id"] for x in cre["creados"]]
    assert len(ids) == 2

    ed = puente.despachar(robot.app, "npcs.editar", {"id": ids[0], "salud": 250, "punteria": 0.85, "hostil": False})["persona"]
    assert ed["salud"] == 250.0 and ed["punteria"] == 0.85 and ed["hostil"] is False

    puente.despachar(robot.app, "npcs.accion", {"id": ids[0], "accion": "matar"})
    assert next(x for x in p.personas if x.id == ids[0]).muerto is True

    puente.despachar(robot.app, "npcs.accion", {"id": ids[0], "accion": "eliminar"})
    assert all(x.id != ids[0] for x in p.personas)

    rep = puente.despachar(robot.app, "policia.set", {"rep_banda": {"banda": "Los Calaveras", "valor": 75}})
    assert rep["rep_bandas"]["Los Calaveras"] == 75.0


def test_policia_y_eventos(robot):
    p = robot.nueva_partida()
    pol = puente.despachar(robot.app, "policia.set", {"estrellas": 4})
    assert pol["estrellas"] == 4 and p.j.estrellas == 4

    pol2 = puente.despachar(robot.app, "policia.set", {"estrellas": 2})
    assert pol2["estrellas"] == 2 and p.j.estrellas == 2

    puente.despachar(robot.app, "policia.set", {"estrellas": 0})
    assert p.j.estrellas == 0

    ev = puente.despachar(robot.app, "eventos.lanzar", {"tipo": "suceso_atraco"})
    assert ev["evento"] == "atraco" and p.evento is not None

    pers = puente.despachar(robot.app, "eventos.lanzar", {"tipo": "persecucion_vehiculo", "modelo_id": "deportivo", "vel_obj": 30})
    assert pers["vehiculo"]["ia"] == "huida" and p.gps is not None

    puente.despachar(robot.app, "eventos.lanzar", {"tipo": "buscar_pelea", "banda": "Los Calaveras"})
    assert p.guerra is not None and p.guerra["tipo"] == "pelea"
    puente.despachar(robot.app, "eventos.lanzar", {"tipo": "terminar_guerra"})
    assert p.guerra is None

    tiempo = puente.despachar(robot.app, "mundo.set", {"hora": 22, "dia": 5, "lluvia": True, "dia_azar": "fiesta"})
    assert tiempo["dia"] == 5 and tiempo["lluvia"] is True and tiempo["dia_azar"]["id"] == "fiesta"


def test_inspector_generico(robot, tmp_path):
    from juego import cifrado
    from juego.entidades import Jugador

    p = robot.nueva_partida()
    respaldo_ruta = tmp_path / "respaldo_antes_trampas.json"
    p._ruta_respaldo_inspector = str(respaldo_ruta)

    res = puente.despachar(robot.app, "inspector.escribir", {"objetivo": "jugador", "clave": "alias", "valor": "El Jefe"})
    assert p.j.alias == "El Jefe"
    assert respaldo_ruta.exists()
    assert res["respaldo"] == str(respaldo_ruta)
    copia = cifrado.leer_json(str(respaldo_ruta))
    assert copia["jugador"]["alias"] == ""

    campos = puente.despachar(robot.app, "inspector.leer", {"objetivo": "jugador"})["campos"]
    assert campos["alias"] == "El Jefe"
    assert "bolsa" not in campos and "reconquista" not in campos and "contrato" not in campos

    # Comprobar que el jugador tras ediciones sigue cargando sin errores en Jugador.de_dict
    j2 = Jugador()
    j2.de_dict(p.j.a_dict())
    assert j2.alias == "El Jefe"


def test_anulacion_total_multijugador(puente_activo, tmp_path):
    """En servidor o partida con amigos, el puente cierra socket, borra ficha y anula toda comunicación."""
    robot, p, srv, cli, _, _ = puente_activo

    # 1. Modo servidor (en_servidor = True)
    p.en_servidor = True
    robot.app.paso(1 / 60)
    assert srv._activo is False
    assert srv._sock is None
    assert descubrir_instancias(str(tmp_path)) == []
    with pytest.raises(ErrorPuente):
        cli.llamar("hola")
    with pytest.raises(ErrorPuente):
        cli.llamar("estado")
    with pytest.raises(ValueError, match="multijugador"):
        puente.despachar(robot.app, "hola", {})

    # Vuelve a un jugador: se reanuda automáticamente con nuevo puerto/ficha
    p.en_servidor = False
    robot.app.paso(1 / 60)
    assert srv._activo is True
    assert len(descubrir_instancias(str(tmp_path))) == 1
    cli2, _ = _conectar_vivo(robot.app, str(tmp_path))

    # 2. Modo amigos (anfitrión: p.servidor / invitado: p.red)
    class _FalsoRed:
        conectado = True

    p.red = _FalsoRed()
    robot.app.paso(1 / 60)
    assert srv._activo is False
    assert descubrir_instancias(str(tmp_path)) == []
    with pytest.raises(ErrorPuente):
        cli2.llamar("estado")

    p.red = None
    p.servidor = object()
    robot.app.paso(1 / 60)
    assert srv._activo is False
    assert descubrir_instancias(str(tmp_path)) == []

    p.servidor = None
    robot.app.paso(1 / 60)
    assert srv._activo is True
    assert len(descubrir_instancias(str(tmp_path))) == 1


def test_ganchos_y_gui_wx_sincronizada(puente_activo):
    import threading
    robot, p, srv, _, _, tmp_path = puente_activo

    p.j.dinero = 7777
    p.j.banco = 12345
    p.j.salud = 82.0
    p.j.blindaje = 45.0
    p.j.estrellas = 3
    p.j.hab["conduccion"] = 6000.0
    p.reloj = 15 * 60.0
    p.dia = 9
    p.lluvia = True

    wx = pytest.importorskip("wx")
    try:
        app_wx = wx.App(False)
    except Exception as exc:
        pytest.skip(f"Sin entorno gráfico wx disponible: {exc}")
    from trampas.ventana import VentanaTrampas

    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    v = VentanaTrampas(auto_conectar=False, intervalo_ms=0)
    parar = threading.Event()

    def bombear_puente():
        while not parar.is_set():
            srv.atender()
            time.sleep(0.002)

    hilo = threading.Thread(target=bombear_puente, daemon=True)
    hilo.start()
    try:
        assert v.libro.GetPageCount() == 8
        assert v.btn_conectar.GetLabel() == "&2 Conectar"
        assert v.conectar(False) is True
        assert v.btn_conectar.GetLabel() == "&2 Desconectar"
        cli_inicial = v.cliente
        assert cli_inicial is not None
        # No debe abrir una segunda conexión si ya está enlazado
        assert v.conectar(False) is True
        assert v.cliente is cli_inicial
        assert "Ya estás conectado" in v.GetStatusBar().GetStatusText()
        assert v.btn_conectar.GetLabel() == "&2 Desconectar"

        assert v.sp_dinero.GetValue() == 7777
        assert v.sp_banco.GetValue() == 12345
        assert v.sp_salud.GetValue() == 82
        assert v.sp_blindaje.GetValue() == 45
        assert v.sp_estrellas.GetValue() == 3
        assert v.sp_hora.GetValue() == 15
        assert v.sp_dia.GetValue() == 9
        assert v.chk_lluvia.GetValue() is True

        # Alternar botón a desconectar y volver a conectar limpiamente
        v._alternar_conexion()
        assert v.cliente is None
        assert v.btn_conectar.GetLabel() == "&2 Conectar"
        v._alternar_conexion()
        assert v.cliente is not None
        assert v.btn_conectar.GetLabel() == "&2 Desconectar"
    finally:
        parar.set()
        hilo.join(timeout=1.0)
        v.Close()
        v.Destroy()
        app_wx.ProcessPendingEvents()
        app_wx.Destroy()


def test_inspector_blindado_contra_errores_y_sintaxis(puente_activo, monkeypatch):
    import threading
    robot, p, srv, _, _, _ = puente_activo
    puente.despachar(robot.app, "npcs.crear", {"modo": "aliado", "cantidad": 1})
    if not p.vehiculos:
        puente.despachar(robot.app, "vehiculos.crear", {"modelo_id": "sedan", "hacer_mio": True, "subir_ahora": False})
    p.j.dinero = 500
    p.j.salud = 90.0
    p.j.objetos["botiquin"] = 2

    dinero_orig = p.j.dinero
    salud_orig = p.j.salud
    objetos_orig = dict(p.j.objetos)
    armas_orig = dict(p.j.armas)
    stats_orig = dict(p.j.stats)
    cfg_orig = dict(robot.app.cfg.v)
    per = p.personas[0]
    per_salud_orig = per.salud
    veh = p.vehiculos[0]
    modelo_orig_ref = veh.modelo

    casos_invalidos = [
        ("jugador", "objetos", '{"botiquin": 5,'),
        ("jugador", "objetos", "{'botiquin': 5}"),
        ("jugador", "objetos", '{"botiquin": "muchos"}'),
        ("jugador", "armas", '{"pistola": {}}'),  # excluido de lista blanca para proteger partida
        ("jugador", "bolsa", '{"bravo": 5}'),
        ("jugador", "reconquista", "{}"),
        ("jugador", "contrato", "{}"),
        ("jugador", "salud", "NaN"),
        ("jugador", "salud", "inf"),
        ("jugador", "salud", "0"),
        ("jugador", "dinero", "12.5"),
        ("jugador", "dinero", "-10"),
        ("jugador", "estrellas", "9"),
        ("jugador", "animo", "200"),
        ("jugador", "atributo_inventado", "123"),
        ("jugador", "_oculto", "1"),
        ("stats", "nueva_stat", "[1, 2,"),
        ("stats", "nueva_stat", "42"),  # claves inventadas rechazadas
        ("stats", "enemigos", "-5"),
        ("stats", "carreras", "[123]"),
        ("vehiculo_actual", "vel_max", "abc"),
        ("vehiculo_actual", "vel_max", "-5"),
        ("vehiculo_actual", "campo_inexistente", "42"),
        ("persona", "campo_inexistente", "99"),
        ("persona", "punteria", "2.5"),
        ("cfg", "opcion_inexistente", "true"),
        ("cfg", "servidores", "[]"),
    ]
    for objetivo, clave, valor in casos_invalidos:
        extra = {"id": per.id} if objetivo == "persona" else ({"id": veh.id} if objetivo == "vehiculo_actual" else {})
        with pytest.raises(ValueError) as exc_info:
            puente.despachar(robot.app, "inspector.escribir", {"objetivo": objetivo, "clave": clave, "valor": valor, **extra})
        assert exc_info.value

    # Verificación estricta: ningún error de sintaxis o validación modificó ni añadió nada ni creó respaldo aún
    assert p.j.dinero == dinero_orig
    assert p.j.salud == salud_orig
    assert p.j.objetos == objetos_orig
    assert p.j.armas == armas_orig
    assert {k: v for k, v in p.j.stats.items() if k != "tiempo"} == {k: v for k, v in stats_orig.items() if k != "tiempo"}
    assert "nueva_stat" not in p.j.stats
    assert not hasattr(p.j, "atributo_inventado")
    assert not hasattr(p.j, "_oculto")
    assert not hasattr(veh, "campo_inexistente")
    assert veh.modelo is modelo_orig_ref
    assert per.salud == per_salud_orig
    assert not hasattr(per, "campo_inexistente")
    assert robot.app.cfg.v == cfg_orig
    assert getattr(p, "_respaldo_inspector_hecho", False) is False

    # Una escritura válida en stats permitidos y en objetos sí funciona
    res_stat = puente.despachar(robot.app, "inspector.escribir", {"objetivo": "stats", "clave": "enemigos", "valor": "42"})
    assert res_stat["ok"] is True and p.j.stats["enemigos"] == 42
    res_obj = puente.despachar(robot.app, "inspector.escribir", {"objetivo": "jugador", "clave": "objetos", "valor": '{"botiquin": 4}'})
    assert res_obj["ok"] is True and p.j.objetos == {"botiquin": 4}
    assert getattr(p, "_respaldo_inspector_hecho", False) is True

    # También desde la GUI wx: bloquea localmente errores de sintaxis, informa al usuario y no altera el juego
    wx = pytest.importorskip("wx")
    try:
        app_wx = wx.App(False)
    except Exception as exc:
        pytest.skip(f"Sin entorno gráfico wx disponible: {exc}")
    import trampas.ventana as V
    errores_gui = []
    monkeypatch.setattr(V, "mostrar_error", lambda padre, msg, tit="Error": errores_gui.append((tit, msg)))

    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    v = V.VentanaTrampas(auto_conectar=False, intervalo_ms=0)
    parar = threading.Event()

    def bombear():
        while not parar.is_set():
            srv.atender()
            time.sleep(0.002)

    hilo = threading.Thread(target=bombear, daemon=True)
    hilo.start()
    try:
        assert v.conectar(False) is True
        v.sel_insp_obj.SetStringSelection("stats")
        v._leer_inspector()
        stats_antes = dict(p.j.stats)

        v.txt_insp_clave.SetValue("enemigos")
        v.txt_insp_valor.SetValue('{"x": [1, 2')
        v._escribir_inspector()

        assert len(errores_gui) == 1
        assert "sintaxis" in errores_gui[0][1].lower()
        assert "No se modificó ni añadió nada" in errores_gui[0][1]
        assert v.txt_insp_estado.GetValue() == errores_gui[0][1]
        assert v.txt_insp_valor.GetValue() == '{"x": [1, 2'
        assert {k: val for k, val in p.j.stats.items() if k != "tiempo"} == {k: val for k, val in stats_antes.items() if k != "tiempo"}
    finally:
        parar.set()
        hilo.join(timeout=1.0)
        v.Close()
        v.Destroy()
        app_wx.ProcessPendingEvents()
        app_wx.Destroy()


def test_servidor_permite_trampas_solo_si_dueno_habilita(puente_activo, tmp_path):
    from servidor import nucleo, opciones
    from test_servidor import mundo

    # 1. Opción del servidor por defecto bloqueada ("no")
    assert opciones.POR_CLAVE["permitir_trampas"].defecto == "no"
    assert opciones.validar_valor("permitir_trampas", "si") == ("si", None)
    assert opciones.validar_valor("permitir_trampas", "no") == ("no", None)

    srv_dir = tmp_path / "srv_datos"
    sv_net = nucleo.Servidor({"datos": str(srv_dir), "puerto": 0, "cifrado": "no", "personajes": 0}, mundo())
    enviados = []
    sv_net._a_todos = lambda m, menos=None: enviados.append(m)

    # Un administrador desde el chat del juego NO puede activar trampas; solo dueño desde consola/panel
    r_chat = sv_net.orden("trampas si", "AdminJuego")
    assert "consola o el panel" in r_chat
    assert sv_net.cfg["permitir_trampas"] == "no"

    r_on = sv_net.orden("trampas si", "consola")
    assert "permitido" in r_on
    assert sv_net.cfg["permitir_trampas"] == "si"
    assert {"t": "trampas", "permitir": True} in enviados

    r_off = sv_net.orden("trampas no", "consola")
    assert "bloqueado" in r_off
    assert sv_net.cfg["permitir_trampas"] == "no"
    assert {"t": "trampas", "permitir": False} in enviados

    # 2. En el juego conectado a un servidor: bloqueado por defecto, habilitado solo si el servidor lo permite
    robot, p, srv, _, _, carpeta_fichas = puente_activo
    p.en_servidor = True
    p.sv = {"info": {"permitir_trampas": False}}
    robot.app.paso(1 / 60)
    assert srv._activo is False
    assert descubrir_instancias(str(carpeta_fichas)) == []
    with pytest.raises(ValueError, match="multijugador"):
        puente.despachar(robot.app, "hola", {})

    # El dueño del servidor permite trampas en vivo (_svm_trampas)
    p._svm_trampas({"t": "trampas", "permitir": True})
    robot.app.paso(1 / 60)
    assert srv._activo is True
    assert len(descubrir_instancias(str(carpeta_fichas))) == 1
    cli, conn_info = _conectar_vivo(robot.app, str(carpeta_fichas))
    assert conn_info["info"]["en_servidor"] is True
    assert conn_info["info"]["trampas_servidor_permitidas"] is True

    antes = p.j.dinero
    res = _llamar_vivo(robot.app, cli, "jugador.set", dinero_delta=250)
    assert res["jugador"]["dinero"] == antes + 250

    # El dueño vuelve a bloquearlas en vivo: anulación inmediata
    p._svm_trampas({"t": "trampas", "permitir": False})
    robot.app.paso(1 / 60)
    assert srv._activo is False
    assert descubrir_instancias(str(carpeta_fichas)) == []
    with pytest.raises(ErrorPuente):
        _llamar_vivo(robot.app, cli, "jugador.set", dinero_delta=100)

    # En modo con amigos (p.servidor / p.red), permanece siempre bloqueado
    p.en_servidor = False
    p.servidor = object()
    p.sv = {"info": {"permitir_trampas": True}}
    robot.app.paso(1 / 60)
    assert srv._activo is False
    assert descubrir_instancias(str(carpeta_fichas)) == []


def test_servidor_real_tcp_transmision_y_restricciones(tmp_path):
    import hashlib
    from conftest import Robot
    from juego import enlinea
    from juego.app import App
    from test_servidor import Banco

    srv_dir = tmp_path / "srv_real"
    carpeta_a = str(tmp_path / "fichas_a")
    carpeta_b = str(tmp_path / "fichas_b")
    banco = Banco(srv_dir, economia="si", saldo_inicial=5000, ganancia_hora=1000, ganancia_acumula=1)
    app_a = App(pruebas=True)
    app_b = App(pruebas=True)
    robot_a, robot_b = Robot(app_a), Robot(app_b)

    def entrar(robot, nombre, carpeta):
        app = robot.app
        app.cfg["red_nombre"] = nombre
        app.semilla_identidad = hashlib.sha256(("tcp-" + nombre).encode()).digest()
        srv_puente = puente.iniciar(app, forzar=True, carpeta=carpeta)
        s = {"nombre": "", "dir": f"puertobravo://127.0.0.1:{banco.puerto}", "cert": ""}
        enlace, motivo = enlinea.conectar(app, s)
        assert enlace is not None, motivo
        app.enlace = enlace
        if enlace.ok.get("partida"):
            app.empezar_partida(enlace.ok["partida"])
        else:
            app.empezar_partida(None, personaje={"id": app.datos["personajes"][0]["id"], "genero": "h"})
        robot.saltar_dialogos()
        p = app.partida
        p.cfg["sucesos"] = False
        return p, srv_puente

    def esperar(cond, *robots, seg=8.0):
        fin = time.monotonic() + seg
        while time.monotonic() < fin:
            for r in robots:
                r.frames(2)
            if cond():
                return True
            time.sleep(0.01)
        return False

    try:
        # 1. Por defecto (permitir_trampas="no"): al entrar, el servidor transmite permiso=False y el puente se anula ya mismo
        p_a, srv_a = entrar(robot_a, "Ana", carpeta_a)
        assert p_a.sv["info"]["permitir_trampas"] is False
        assert p_a.sv["admin"] is True  # primera cuenta es admin del servidor, aun así no puede habilitar trampas
        assert srv_a._activo is False
        assert srv_a._sock is None
        assert descubrir_instancias(carpeta_a) == []
        with pytest.raises(ValueError, match="multijugador"):
            puente.despachar(app_a, "estado", {})

        # 2. Un admin desde el chat (/trampas si, /cheats si) o enviando mensajes falsos NO puede activar trampas
        p_a.red.enviar({"t": "chat", "canal": "todos", "texto": "/trampas si"})
        assert esperar(lambda: "consola o el panel" in robot_a.dicho(), robot_a)
        p_a.red.enviar({"t": "chat", "canal": "todos", "texto": "/cheats si"})
        p_a.red.enviar({"t": "trampas", "permitir": True})  # intento de suplantación desde el cliente
        for _ in range(15):
            robot_a.frames(1)
            time.sleep(0.01)
        assert banco.srv.cfg["permitir_trampas"] == "no"
        assert p_a.sv["info"]["permitir_trampas"] is False
        assert srv_a._activo is False
        assert descubrir_instancias(carpeta_a) == []

        # 3. Con trampas desactivadas, el servidor recorta dinero ilegítimo por la economía
        p_a.j.dinero = 99999
        p_a.j.banco = 0
        p_a.t_red = 1.0
        assert esperar(lambda: (p_a.j.dinero + p_a.j.banco) <= 2500, robot_a)

        # 4. Dueño habilita desde consola ("trampas si"): transmisión real TCP y puente activo + economía liberada
        resp = banco.hacer(banco.srv.orden, "trampas si")
        assert "permitido" in resp
        assert esperar(lambda: p_a.sv["info"].get("permitir_trampas") is True and srv_a._activo is True, robot_a)
        assert len(descubrir_instancias(carpeta_a)) == 1
        cli_a, info_a = _conectar_vivo(app_a, carpeta_a)
        assert info_a["info"]["en_servidor"] is True
        assert info_a["info"]["trampas_servidor_permitidas"] is True

        dinero_antes = p_a.j.dinero
        res_din = _llamar_vivo(app_a, cli_a, "jugador.set", dinero_delta=50000)
        assert res_din["jugador"]["dinero"] == dinero_antes + 50000
        p_a.t_red = 1.0
        for _ in range(25):
            robot_a.frames(2)
            time.sleep(0.01)
        assert p_a.j.dinero == dinero_antes + 50000  # el servidor no lo confisca mientras trampas=si

        # 5. Segundo jugador entra después y recibe permitir_trampas=True en el saludo "ok"
        p_b, srv_b = entrar(robot_b, "Blas", carpeta_b)
        assert p_b.sv["info"]["permitir_trampas"] is True
        assert srv_b._activo is True
        assert len(descubrir_instancias(carpeta_b)) == 1
        cli_b, info_b = _conectar_vivo(app_b, carpeta_b)
        assert info_b["info"]["trampas_servidor_permitidas"] is True
        res_b = _llamar_vivo(app_b, cli_b, "jugador.set", salud=75)
        assert res_b["jugador"]["salud"] == 75.0

        # 6. Dueño deshabilita en vivo mediante aplicar_config (como desde el panel del servidor)
        al_momento, con_reinicio = banco.hacer(banco.srv.aplicar_config, {"permitir_trampas": "no"})
        assert "permitir_trampas" in al_momento and con_reinicio == []
        assert esperar(
            lambda: (
                p_a.sv["info"].get("permitir_trampas") is False
                and p_b.sv["info"].get("permitir_trampas") is False
                and srv_a._activo is False
                and srv_b._activo is False
            ),
            robot_a,
            robot_b,
        )
        assert descubrir_instancias(carpeta_a) == []
        assert descubrir_instancias(carpeta_b) == []
        with pytest.raises(ErrorPuente):
            _llamar_vivo(app_a, cli_a, "jugador.set", dinero_delta=100)
        with pytest.raises(ErrorPuente):
            _llamar_vivo(app_b, cli_b, "jugador.set", dinero_delta=100)
        # Lo ganado legítimamente mientras estaba habilitado se conserva, pero nuevo dinero sin respaldo se recorta
        assert p_a.j.dinero == dinero_antes + 50000
        saldo_legitimo = p_a.j.dinero + p_a.j.banco
        p_a.j.dinero += 99999
        p_a.t_red = 1.0
        assert esperar(lambda: (p_a.j.dinero + p_a.j.banco) <= saldo_legitimo + 1500, robot_a)

        # 7. Recarga desde archivo servidor.conf en disco vuelve a habilitarlo en vivo
        conf_ruta = srv_dir / "servidor.conf"
        conf = dict(banco.srv.cfg, permitir_trampas="si")
        from servidor import opciones
        assert opciones.guardar(str(conf_ruta), conf) == []
        banco.srv.ruta_conf = str(conf_ruta)
        r_rec = banco.hacer(banco.srv.orden, "recargar")
        assert "Permitir menú de trampas" in r_rec
        assert esperar(lambda: srv_a._activo is True and srv_b._activo is True, robot_a, robot_b)

        # 8. Durante reconexión (sv_espera) vuelve a bloquearse; al salir del servidor vuelve a solitario y funciona
        p_a.sv_espera = {"causa": "reinicio"}
        robot_a.frames(1)
        assert srv_a._activo is False
        p_a.sv_espera = None
        p_a.sv_salir()
        robot_a.frames(1)
        assert srv_a._activo is True
        cli_a2, info_a2 = _conectar_vivo(app_a, carpeta_a)
        assert info_a2["info"]["en_servidor"] is False
    finally:
        for a in (app_a, app_b):
            if a.partida is not None:
                try:
                    a.partida.sv_salir()
                    a.partida.desconectar_online()
                except Exception:
                    pass
            puente.detener(a)
            a.radio.cancelar()
            a.ambiente.cancelar()
            a.mez.cerrar()
        banco.parar()


def test_inspector_y_cfg_atomicidad_exhaustiva(robot, tmp_path):
    p = robot.nueva_partida()
    puente.iniciar(robot.app, forzar=True, carpeta=str(tmp_path))
    try:
        puente.despachar(robot.app, "npcs.crear", {"modo": "aliado", "cantidad": 1})
        if not p.vehiculos:
            puente.despachar(robot.app, "vehiculos.crear", {"modelo_id": "sedan", "hacer_mio": True, "subir_ahora": False})
        per = p.personas[0]
        veh = p.vehiculos[0]

        dinero_orig = p.j.dinero
        salud_orig = p.j.salud
        objetos_orig = dict(p.j.objetos)
        armas_orig = dict(p.j.armas)
        mochila_orig = list(p.j.mochila)
        stats_orig = dict(p.j.stats)
        cfg_orig = dict(robot.app.cfg.v)
        per_dict_orig = dict(per.__dict__)
        veh_dict_orig = {k: v for k, v in veh.__dict__.items() if k != "modelo"}
        modelo_ref = veh.modelo

        fallos = [
            ("jugador", "objetos", '{"botiquin": NaN}'),
            ("jugador", "objetos", '{"botiquin": 5,}'),
            ("jugador", "objetos", '{"botiquin": true}'),
            ("jugador", "mochila", "[1, 2, ]"),
            ("jugador", "bolsa", '{"algo": 1}'),
            ("jugador", "dinero", True),
            ("jugador", "salud", False),
            ("jugador", "salud", "-10"),
            ("jugador", "a_dict", "1"),
            ("jugador", "dinero\n", "10"),
            ("jugador", "x" * 81, "10"),
            ("jugador", "perro", "abc\x00def"),
            ("stats", "nueva_inf", "[1, Infinity]"),
            ("stats", "clave\tTab", "5"),
            ("stats", "enemigos", "-1"),
            ("vehiculo_actual", "modelo", "{}"),
            ("vehiculo_actual", "canal", "1"),
            ("vehiculo_actual", "pasajeros", "[]"),
            ("persona", "dist", "0"),
        ]
        for objetivo, clave, valor in fallos:
            extra = {"id": per.id} if objetivo == "persona" else ({"id": veh.id} if objetivo == "vehiculo_actual" else {})
            with pytest.raises(ValueError, match="."):
                puente.despachar(robot.app, "inspector.escribir", {"objetivo": objetivo, "clave": clave, "valor": valor, **extra})

        # Atomicidad estricta en cfg.set: si una clave falla, ninguna del lote se aplica
        fuego_antes = robot.app.cfg["fuego_amigo"]
        with pytest.raises(ValueError):
            puente.despachar(robot.app, "cfg.set", {"cambios": {"fuego_amigo": not fuego_antes, "inexistente": 1}})
        with pytest.raises(ValueError):
            puente.despachar(robot.app, "cfg.set", {"cambios": {"fuego_amigo": not fuego_antes, "velocidad_voz": "no_numero"}})

        assert p.j.dinero == dinero_orig
        assert p.j.salud == salud_orig
        assert p.j.objetos == objetos_orig
        assert p.j.armas == armas_orig
        assert p.j.mochila == mochila_orig
        assert p.j.stats == stats_orig
        assert robot.app.cfg.v == cfg_orig
        assert robot.app.cfg["fuego_amigo"] == fuego_antes
        assert per.__dict__ == per_dict_orig
        assert {k: v for k, v in veh.__dict__.items() if k != "modelo"} == veh_dict_orig
        assert veh.modelo is modelo_ref
    finally:
        puente.detener(robot.app)


def test_trampas_marca_partida_y_desactiva_logros(robot):
    p = robot.nueva_partida()
    from juego.entidades import Jugador
    from juego.menus_extra import progreso

    assert p.j.trampas_usadas is False
    # Comando de solo lectura no debe marcar la partida
    estado_leido = puente.despachar(robot.app, "estado", {})
    assert estado_leido["jugador"]["trampas_usadas"] is False
    assert p.j.trampas_usadas is False

    # Una orden de escritura marca trampas_usadas=True y desactiva nuevos logros
    res = puente.despachar(robot.app, "jugador.set", {"dinero": 60000})
    assert p.j.trampas_usadas is True
    assert res["jugador"]["trampas_usadas"] is True

    logros_antes = list(p.j.logros)
    p.j.dinero = 100000
    p.comprobar_logros()
    assert p.j.logros == logros_antes

    # Persistencia en a_dict / de_dict y aviso en el menú de logros
    datos_j = p.j.a_dict()
    assert datos_j["trampas_usadas"] is True
    j_cargado = Jugador()
    j_cargado.de_dict(datos_j)
    assert j_cargado.trampas_usadas is True

    # Partidas antiguas sin el campo cargan con False
    datos_legado = dict(datos_j)
    datos_legado.pop("trampas_usadas", None)
    j_legado = Jugador()
    j_legado.de_dict(datos_legado)
    assert j_legado.trampas_usadas is False

    progreso(p)
    menu_stats = robot.app.pila[-1]
    op_logros = next(
        op for op in menu_stats.opciones
        if "Logros" in (op._texto() if callable(op._texto) else str(op._texto))
    )
    op_logros.accion()
    assert "desactivados" in robot.dicho().lower()


def test_ventana_trampas_accesibilidad_y_teclado():
    try:
        import wx
        app_wx = wx.App(False)
    except Exception as exc:
        pytest.skip(f"Sin entorno gráfico wx disponible: {exc}")

    import trampas.ventana as V
    from editor.accesibilidad import revision_teclado

    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    v = V.VentanaTrampas(auto_conectar=False, intervalo_ms=0)
    try:
        problemas = revision_teclado.revisar_teclado(v, teclas_propias=["F5"])
        assert problemas == [], revision_teclado.informe(problemas)

        sp_dobles = []
        busquedas = []
        sin_ayuda = []

        def recorrer(w):
            for c in w.GetChildren():
                if isinstance(c, wx.SpinCtrlDouble):
                    sp_dobles.append(c.GetName())
                if isinstance(c, wx.SearchCtrl):
                    busquedas.append(c.GetName())
                if isinstance(c, (wx.Button, wx.CheckBox, wx.ListBox, wx.TextCtrl, wx.Choice, wx.SpinCtrl)):
                    if not c.GetHelpText().strip():
                        sin_ayuda.append((type(c).__name__, c.GetName()))
                recorrer(c)

        recorrer(v)
        assert sp_dobles == []
        assert busquedas == []
        assert sin_ayuda == []
    finally:
        v.Close()
        v.Destroy()
        app_wx.ProcessPendingEvents()
        app_wx.Destroy()


def test_ventana_trampas_i18n_ingles(monkeypatch):
    try:
        import wx
        app_wx = wx.App(False)
    except Exception as exc:
        pytest.skip(f"Sin entorno gráfico wx disponible: {exc}")

    from juego import i18n
    import trampas.ventana as V
    from editor.accesibilidad import revision_teclado

    previo = i18n.actual()
    monkeypatch.setenv("PUERTOBRAVO_IDIOMA", "en")
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    i18n.cargar("en")
    v = V.VentanaTrampas(auto_conectar=False, intervalo_ms=0)
    try:
        assert v.GetTitle() == "Cheat Menu — Puerto Bravo"
        assert v.libro.GetPageText(0) == "Player"
        problemas = revision_teclado.revisar_teclado(v, teclas_propias=["F5"])
        assert problemas == [], revision_teclado.informe(problemas)
    finally:
        v.Close()
        v.Destroy()
        app_wx.ProcessPendingEvents()
        app_wx.Destroy()
        monkeypatch.undo()
        i18n.cargar(previo)


def test_ventana_trampas_teclado_todos_idiomas(monkeypatch):
    try:
        import wx
        app_wx = wx.App(False)
    except Exception as exc:
        pytest.skip(f"Sin entorno gráfico wx disponible: {exc}")

    from juego import i18n
    import trampas.ventana as V
    from editor.accesibilidad import revision_teclado

    previo = i18n.actual()
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    try:
        for idi in ("es", "en", "pt", "ru", "vi"):
            monkeypatch.setenv("PUERTOBRAVO_IDIOMA", idi)
            i18n.cargar(idi)
            v = V.VentanaTrampas(auto_conectar=False, intervalo_ms=0)
            try:
                problemas = revision_teclado.revisar_teclado(v, teclas_propias=["F5"])
                errores = [p for p in problemas if not p.aviso]
                assert errores == [], f"[{idi}]\n" + revision_teclado.informe(errores)
                if idi != "ru":
                    assert problemas == [], f"[{idi}]\n" + revision_teclado.informe(problemas)
            finally:
                v.Close()
                v.Destroy()
                app_wx.ProcessPendingEvents()
    finally:
        app_wx.Destroy()
        monkeypatch.undo()
        i18n.cargar(previo)


def test_guia_menu_trampas_idiomas_y_enlaces(monkeypatch):
    import sys
    from html.parser import HTMLParser
    from pathlib import Path
    from juego import i18n, rutas

    raiz = Path(__file__).resolve().parent.parent
    docs = raiz / "data" / "docs"
    sys.path.insert(0, str(raiz / "herramientas" / "i18n"))
    import fugas

    class _Parser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.etiquetas = []
            self.enlaces = []

        def handle_starttag(self, tag, attrs):
            self.etiquetas.append(tag)
            for k, v in attrs:
                if k == "href":
                    self.enlaces.append(v)

        def handle_endtag(self, tag):
            self.etiquetas.append(f"/{tag}")

    parsers = {}
    for cod in ("es", "en", "pt", "vi"):
        guia = docs / f"menu_trampas_{cod}.html"
        assert guia.is_file(), f"Falta {guia}"
        manual = (docs / f"manual_{cod}.html").read_text(encoding="utf-8")
        assert f"menu_trampas_{cod}.html" in manual, f"El manual {cod} no enlaza menu_trampas_{cod}.html"

        p = _Parser()
        texto = guia.read_text(encoding="utf-8")
        p.feed(texto)
        parsers[cod] = (p, texto)
        for href in p.enlaces:
            if ":" in href or href.startswith("//"):
                continue
            archivo = href.split("#", 1)[0]
            if archivo:
                assert (docs / archivo).is_file(), (cod, href)

    assert 'lang="pt-BR"' in parsers["pt"][1]
    assert parsers["en"][0].etiquetas == parsers["pt"][0].etiquetas
    malas = fugas.fugas(parsers["en"][1], es_html=True)
    assert malas == [], f"Español colado en menu_trampas_en.html: {malas}"

    previo = i18n.actual()
    try:
        for cod, esperado in (("es", "menu_trampas_es.html"), ("en", "menu_trampas_en.html"), ("pt", "menu_trampas_pt.html"), ("vi", "menu_trampas_vi.html"), ("ru", "menu_trampas_en.html")):
            monkeypatch.setenv("PUERTOBRAVO_IDIOMA", cod)
            i18n.cargar(cod)
            assert i18n.doc("menu_trampas").endswith(esperado)
            assert os.path.exists(rutas.data("docs", esperado))
    finally:
        monkeypatch.undo()
        i18n.cargar(previo)
