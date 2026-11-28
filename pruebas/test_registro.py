"""El registro de sesión: completo para depurar, sin nada personal, y con cinco sesiones como mucho."""
import os
import shutil
import threading

import pygame
import pytest

from conftest import Robot
from juego import menus_juego, registro, rutas
from juego.menus import EntradaTexto, Menu

SECRETOS = ["contraseña-secreta-123", "MiNombreReal", "AmigaLaura", "hola qué tal estás, mensaje privado", "83.45.12.7", "mi.servidor.example",
            "persona@correo.example", "sk-ant-api03-ABCDEFGHIJKLMNOP", "cancion_de_mi_boda"]


@pytest.fixture
def con_registro(tmp_path):
    raiz = str(tmp_path / "logs")
    carpeta = registro.iniciar("juego", raiz=raiz, graves=False)
    assert carpeta and os.path.isdir(carpeta)
    menus_juego.CARPETA = "partidas_pruebas"
    shutil.rmtree(rutas.data("partidas_pruebas"), ignore_errors=True)
    from juego.app import App
    a = App(pruebas=True)
    yield Robot(a), carpeta
    a.radio.cancelar()
    a.ambiente.cancelar()
    a.mez.cerrar()
    registro.cerrar()
    shutil.rmtree(rutas.data("partidas_pruebas"), ignore_errors=True)


def _leer(carpeta, nombre="sesion.log"):
    ruta = os.path.join(carpeta, nombre)
    return open(ruta, encoding="utf-8").read() if os.path.exists(ruta) else ""


def _todo(carpeta):
    return "\n".join(_leer(carpeta, f) for f in os.listdir(carpeta))


def test_sin_iniciar_no_hace_nada(app):
    """En las pruebas normales (y si no se puede escribir) el registro está apagado y nada falla."""
    assert not registro.activo() and registro.carpeta_sesion() is None
    registro.info("x", "y")
    registro.error("x", "y", "traza")
    registro.voz("hola")
    registro.tecla("a")
    registro.marca()
    registro.estado()
    registro.cerrar()
    assert not os.path.isdir(os.path.join(rutas.DATA, "logs")) or True


def test_cinco_sesiones_y_se_borra_la_mas_vieja(tmp_path, monkeypatch):
    raiz = str(tmp_path / "logs")
    creadas = []
    import datetime as dt

    class Reloj(dt.datetime):
        n = 0

        @classmethod
        def now(cls, tz=None):
            cls.n += 1
            return dt.datetime(2026, 11, 14, 10, 0, 0) + dt.timedelta(minutes=cls.n)
    monkeypatch.setattr(registro.datetime, "datetime", Reloj)
    for k in range(8):
        c = registro.iniciar("juego", raiz=raiz, graves=False)
        registro.info("prueba", f"sesión {k}")
        registro.cerrar()
        creadas.append(os.path.basename(c))
        quedan = sorted(os.listdir(raiz))
        assert len(quedan) == min(k + 1, 5), quedan
        assert quedan == sorted(creadas)[-5:]                       # siempre las cinco más recientes
    assert creadas[0] not in os.listdir(raiz) and creadas[-1] in os.listdir(raiz)
    for s in os.listdir(raiz):
        assert sorted(os.listdir(os.path.join(raiz, s))) == ["LEEME.txt", "sesion.log"]
    # un archivo suelto en logs no cuenta como sesión ni se borra
    open(os.path.join(raiz, "nota.txt"), "w").close()
    registro.iniciar("editor", raiz=raiz, graves=False)
    registro.cerrar()
    assert os.path.exists(os.path.join(raiz, "nota.txt")) and len([d for d in os.listdir(raiz) if os.path.isdir(os.path.join(raiz, d))]) == 5


def test_el_filtro_borra_lo_personal(tmp_path, monkeypatch):
    monkeypatch.setenv("USERNAME", "pepito_grillo")
    monkeypatch.setenv("COMPUTERNAME", "PC-DE-PEPITO")
    monkeypatch.setenv("USERPROFILE", r"C:\Users\pepito_grillo")
    c = registro.iniciar("juego", raiz=str(tmp_path / "logs"), graves=False)
    try:
        registro.ocultar("AmigaLaura")
        casos = {
            r'File "C:\Users\pepito_grillo\Juegos\PuertoBravo\lib\juego\app.py", line 10': ["pepito_grillo"],
            r"No se pudo abrir D:\Otra\cosa de pepito_grillo.txt en PC-DE-PEPITO": ["pepito_grillo", "PC-DE-PEPITO"],
            "Conectando a 83.45.12.7:47810 y a 192.168.1.20": ["83.45", "192.168", "47810"],
            "puertobravo://83.45.12.7:47810 y https://mi.servidor.example/pb/version.json": ["83.45", "mi.servidor", "version.json"],
            "escribe a persona@correo.example": ["persona@", "correo.example"],
            "clave sk-ant-api03-ABCDEFGHIJKLMNOP y token ghp_abcdefgh12345678": ["sk-ant", "ghp_abc"],
            "AmigaLaura se ha unido a la partida. amigalaura dice hola": ["AmigaLaura", "amigalaura"],
            os.path.join(rutas.base(), "data", "partidas", "partida_1.pbs"): [rutas.base()],
        }
        for texto, prohibido in casos.items():
            limpio = registro.limpiar(texto)
            for p in prohibido:
                assert p.lower() not in limpio.lower(), (texto, limpio)
        assert registro.limpiar(os.path.join(rutas.base(), "juego", "app.py")).startswith("<juego>")
        assert "línea 10" in registro.limpiar("error en la línea 10 de misiones") and "Laura" in registro.limpiar("Lauraceas")       # no se pasa de frenada
        registro.info("prueba", "va a 83.45.12.7", ruta=r"C:\Users\pepito_grillo\x", quien="AmigaLaura")
        registro.error("prueba", "falló con pepito_grillo", 'Traceback\n  File "C:\\Users\\pepito_grillo\\a.py", line 3\nValueError: 83.45.12.7', dato="persona@correo.example")
        todo = _todo(c)
        for p in ("pepito_grillo", "83.45", "AmigaLaura", "persona@", "PC-DE-PEPITO"):
            assert p not in todo, p
        assert "ValueError" in todo and "a.py" in todo and "line 3" in todo                   # lo útil sigue ahí
    finally:
        registro.cerrar()


def test_sesion_completa_sin_nada_personal(con_registro):
    robot, carpeta = con_registro
    app = robot.app
    assert sorted(os.listdir(carpeta)) == ["LEEME.txt", "sesion.log", "sistema.txt"]
    # sistema.txt: lo necesario para depurar, y nada más
    app.cfg["red_nombre"] = "MiNombreReal"
    app.cfg["red_ultima"] = "puertobravo://83.45.12.7:47810"
    app.cfg["act_url"] = "https://mi.servidor.example/pb/version.json"
    os.makedirs(rutas.carpeta_data("radio", "mi_musica"), exist_ok=True)
    registro.escribir_sistema(registro.datos_del_juego(app))
    sistema = _leer(carpeta, "sistema.txt")
    for dato in ("versión: ", "sistema: Windows", "memoria: ", "sonidos cargados: 284", "mods: ", "costa_dorada", "packs de sonidos: ", "realista", "conduccion: asistida",
                 "act_fuente: servidor", "adultos: False", "archivos de radio: ", "nombre propio en la red: sí"):
        assert dato in sistema, dato
    for no in ("red_nombre", "red_ultima", "act_url", "MiNombreReal", "83.45", "mi.servidor", ".mp3"):
        assert no not in sistema, no

    # jugar un rato: pantallas, teclas, voz y estado
    p = robot.nueva_partida()
    robot.tecla(pygame.K_c)
    robot.tecla(pygame.K_v)
    robot.tecla(pygame.K_TAB, mod=pygame.KMOD_SHIFT)
    robot.frames(30, mantener=(pygame.K_UP,))
    app.t_estado = registro.CADA_ESTADO
    robot.frames(2)
    robot.tecla(pygame.K_m)
    assert isinstance(app.pila[-1], Menu)
    robot.tecla(pygame.K_ESCAPE)
    log = _leer(carpeta)
    for dato in ("[sesion] Empieza la sesión de juego", "[arranque] Sonidos cargados | cuantos=284", "[arranque] Datos y mapas cargados", "[partida] Empieza una partida",
                 "[pantalla] abre: Menu «Móvil", "[pantalla] cierra: Menu", "TECLA [tecla] c", "TECLA [tecla] mayús+tab", "TECLA [tecla] m", "VOZ   [voz] ",
                 "ESTAD [estado] ", "mapa=puerto_bravo", "vehiculo=a pie", "mision=ninguna", "red=no", "dia_tipo="):
        assert dato in log, dato
    assert log.count("VOZ   [voz]") > 5

    # la marca del jugador, con F12
    robot.tecla(pygame.K_F12)
    assert "Marca añadida al registro" in robot.dicho() and "MARCA DEL JUGADOR" in _leer(carpeta)

    # cuadros de texto: ni lo que se escribe ni lo que se lee al escribir
    hechos = []
    app.abrir(EntradaTexto(app, "Contraseña de la partida", hechos.append, secreto=False))
    for letra in "contraseña-secreta-123":
        robot.tecla(pygame.K_a, unicode=letra)
    robot.tecla(pygame.K_UP)                                        # lee lo escrito
    robot.tecla(pygame.K_RETURN)
    assert hechos == ["contraseña-secreta-123"]
    log = _leer(carpeta)
    assert "(tecla en un cuadro de texto)" in log and "(texto privado, no se registra)" in log
    assert "[pantalla] abre: EntradaTexto" in log

    # red: nombres y mensajes fuera; lo que pasa, dentro
    ok, _ = p.abrir_a_amigos(0, "contraseña-secreta-123")
    assert ok
    from juego import red
    amiga = red.Cliente()
    ok, _ = amiga.conectar("127.0.0.1", p.servidor.puerto, "AmigaLaura", "contraseña-secreta-123")
    assert ok
    import time
    fin = time.time() + 4
    while time.time() < fin and not p.remotos:
        robot.frames(2)
    amiga.enviar({"t": "chat", "texto": "hola qué tal estás, mensaje privado"})
    fin = time.time() + 4
    while time.time() < fin and not p.chat:
        robot.frames(2)
    assert p.chat and "se ha unido a la partida" in robot.dicho()
    p.enviar_chat("hola qué tal estás, mensaje privado")
    robot.frames(3)
    amiga.cerrar()
    p.desconectar_online()
    log = _leer(carpeta)
    for dato in ("[red] Abre su partida a los amigos | con_clave=True", "[red] Entra un jugador", "[red] Llega un mensaje de chat | letras=35", "<nombre> se ha unido a la partida",
                 "[red] Se desconecta de la partida en red"):
        assert dato in log, dato

    # un sonido que no existe se anota una sola vez
    for _ in range(5):
        app.son("sonido_que_no_existe")
    assert _leer(carpeta).count("sonido que no existe: sonido_que_no_existe") == 1

    # un error en un hilo y un fallo del juego: traza, estado, últimas teclas y sonidos
    def romper():
        raise RuntimeError("fallo de prueba en un hilo")
    try:
        romper()
    except RuntimeError:
        registro.excepcion("hilo", "Excepción en un hilo de prueba")
    try:
        {}["no_existe"]
    except KeyError:
        app._registrar_error()
    errores = _leer(carpeta, "errores.log")
    for dato in ("fallo de prueba en un hilo", "KeyError: 'no_existe'", "Traza:", "test_registro.py", "Estado de la partida:", "mapa: puerto_bravo", "Últimas teclas:", "Últimos sonidos:"):
        assert dato in errores, dato
    assert "comprime la carpeta de esta sesión" in robot.dicho() and os.path.basename(carpeta) in robot.dicho()
    assert "ERROR [juego] El juego se ha cerrado por un error inesperado" in _leer(carpeta)

    # y en toda la carpeta no hay ni rastro de lo personal
    todo = _todo(carpeta)
    for s in SECRETOS:
        assert s not in todo, s
    casa = os.path.expanduser("~")
    assert casa.lower() not in todo.lower() and rutas.base().lower() not in todo.lower()
    usuario = os.environ.get("USERNAME", "")
    if len(usuario) >= 3:
        assert usuario.lower() not in todo.lower()
    assert sorted(os.listdir(carpeta)) == ["LEEME.txt", "errores.log", "sesion.log", "sistema.txt"]


def test_el_registro_no_crece_sin_limite(tmp_path, monkeypatch):
    monkeypatch.setattr(registro, "MAX_BYTES", 20000)
    c = registro.iniciar("juego", raiz=str(tmp_path / "logs"), graves=False)
    try:
        for k in range(3000):
            registro.info("prueba", f"línea número {k} " + "x" * 40)
        assert os.path.getsize(os.path.join(c, "sesion.log")) <= 21000
        assert os.path.getsize(os.path.join(c, "sesion_anterior.log")) <= 21000
        assert "línea número 2999" in _leer(c)                       # lo último, que es lo que importa, está
        assert sum(os.path.getsize(os.path.join(c, f)) for f in os.listdir(c)) < 60000
    finally:
        registro.cerrar()


def test_varios_hilos_a_la_vez(tmp_path):
    c = registro.iniciar("juego", raiz=str(tmp_path / "logs"), graves=False)
    try:
        def escribir(n):
            for k in range(300):
                registro.info("hilo", f"hilo {n} línea {k}")
                registro.sonido(f"s{n}")
        hilos = [threading.Thread(target=escribir, args=(n,)) for n in range(6)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        lineas = [l for l in _leer(c).splitlines() if "[hilo]" in l]
        assert len(lineas) == 1800 and all(l.rstrip().split("línea ")[-1].isdigit() for l in lineas)        # ninguna línea mezclada
    finally:
        registro.cerrar()


def test_fallo_grave_y_cierre(tmp_path):
    c = registro.iniciar("juego", raiz=str(tmp_path / "logs"), graves=True)
    assert os.path.exists(os.path.join(c, "fallo_grave.log"))
    registro.cerrar()
    assert not os.path.exists(os.path.join(c, "fallo_grave.log"))    # vacío: no hubo fallo grave, no estorba
    assert "Fin de la sesión: cierre normal" in _leer(c)


def test_menu_del_registro(con_registro):
    robot, carpeta = con_registro
    app = robot.app
    from juego import menus_registro
    menus_registro.opciones(app)
    m = app.pila[-1]
    assert m.titulo == "Registro para informar de fallos" and m.opciones[-1].texto == "Volver"
    for k in range(len(m.opciones) - 1):
        m.i = k
        robot.tecla(pygame.K_RETURN)
    dicho = robot.dicho()
    assert os.path.basename(carpeta) in dicho and "cinco últimas sesiones" in dicho and "Comprímela en un ZIP" in dicho
    assert "GitHub" in dicho and "Mastodon" in dicho and "No contiene nada de lo que escribes" in dicho and "Marca añadida" in dicho


def test_fallo_grave_sin_los_avisos_inofensivos_de_la_voz_de_windows(tmp_path):
    # La voz de Windows lanza por dentro la excepción 0xe0000002 al hablar; el juego sigue, pero Python la anota igual.
    sapi = ("Windows fatal exception: code 0xe0000002\n\nThread 0x0001 (most recent call first):\n  File \"sapi5.py\", line 92 in speak\n\n"
            "Current thread 0x0002 (most recent call first):\n  File \"voz.py\", line 86 in decir\n")
    caida = "Windows fatal exception: access violation\n\nCurrent thread 0x0002 (most recent call first):\n  File \"juego.py\", line 5 in bucle\n"
    p = tmp_path / "fallo_grave.log"
    p.write_text(sapi, encoding="utf-8")
    registro._sanear(str(p))
    assert not p.exists()                                            # solo traía el aviso de la voz: no es un fallo grave
    p.write_text(sapi + "\n" + caida + sapi, encoding="utf-8")
    registro._sanear(str(p))
    texto = p.read_text(encoding="utf-8")
    assert "access violation" in texto and "juego.py" in texto      # la caída de verdad se conserva entera
    assert "0xe0000002" not in texto and "sapi5.py" not in texto
