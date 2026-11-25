"""Compilación con cx_Freeze. Lo usa compilar.bat:

    .venv\\Scripts\\python.exe setup_cx.py build_exe

El resultado queda en dist\\PuertoBravo, con cuatro programas: PuertoBravo.exe (el juego), EditorMods.exe (el editor de mods),
PuertoBravoServidorPanel.exe (el panel del servidor en línea, con ventana) y PuertoBravoServidor.exe (el servidor por consola).
La carpeta data y la carpeta servidor (lanzadores, guía, ejemplo de configuración y lo necesario para otros sistemas) las pone
compilar.bat al lado de los ejecutables; la del servidor, con herramientas\\preparar_carpeta_servidor.py.
"""
import os
import sys

from cx_Freeze import Executable, setup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from juego import NOMBRE, VERSION  # noqa: E402

opciones = {
    "build_exe": os.path.join("dist", "PuertoBravo"),
    "packages": ["juego", "editor", "servidor", "panel_servidor", "trampas", "wx", "pygame", "numpy", "sounddevice", "_sounddevice_data", "soundfile", "_soundfile_data",
                 "accessible_output2", "libloader", "platform_utils", "win32com", "pythoncom", "pywintypes"],
    "includes": ["juego.app"],
    "excludes": ["tkinter", "pytest", "_pytest", "unittest", "pydoc_data", "PyInstaller", "setuptools", "pip", "numpy.f2py", "numpy.testing", "win32comext"],
    "zip_include_packages": [],
    "zip_exclude_packages": ["*"],
    "include_msvcr": True,
    "optimize": 1,
    # Sin esto, cada módulo compilado lleva dentro la ruta completa del equipo donde se compiló, y sale en las trazas de error.
    "replace_paths": [("*", "")],
    "silent_level": 1,
    # El mundo con el que arranca un servidor nuevo va junto a su código. Lo demás del servidor (la carpeta servidor, con
    # los lanzadores, la guía y lo de otros sistemas) lo pone compilar.bat: no es código compilado.
    "include_files": [(os.path.join("servidor", "mundo.json"), os.path.join("lib", "servidor", "mundo.json"))],
}

# Opcionales: si están instalados, van en la compilación; si no, el juego funciona igual sin ellos.
import importlib.util  # noqa: E402
for _opcional in ("cryptography", "ptts"):
    if importlib.util.find_spec(_opcional) is not None:
        opciones["packages"].append(_opcional)

setup(
    name="PuertoBravo",
    version=VERSION,
    description=NOMBRE,
    options={"build_exe": opciones},
    executables=[Executable("main.py", base="gui", target_name="PuertoBravo.exe"),
                 Executable("editor_mods.py", base="gui", target_name="EditorMods.exe"),
                 Executable("servidor_panel.py", base="gui", target_name="PuertoBravoServidorPanel.exe"),
                 Executable("servidor_main.py", base="console", target_name="PuertoBravoServidor.exe"),
                 Executable("trampas_gui.py", base="gui", target_name="MenuTrampas.exe")],
)
