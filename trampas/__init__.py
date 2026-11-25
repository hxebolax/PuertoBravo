"""Paquete independiente para el Menú de Trampas externo de Puerto Bravo."""
from __future__ import annotations

import ctypes
import json
import os
import tempfile

PROTOCOLO = 1
NOMBRE = "Menú de Trampas — Puerto Bravo"


def carpeta_fichas() -> str:
    """Carpeta temporal donde cada instancia del juego anuncia su puente IPC."""
    forzada = os.environ.get("PUERTOBRAVO_TRAMPAS_DIR")
    if forzada:
        return forzada
    return os.path.join(tempfile.gettempdir(), "PuertoBravoTrampas")


def proceso_vivo(pid: int) -> bool:
    """Comprueba si un PID sigue activo sin depender de paquetes externos."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            codigo = ctypes.c_ulong(0)
            if not k32.GetExitCodeProcess(handle, ctypes.byref(codigo)):
                return False
            return codigo.value == STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def descubrir_instancias(carpeta: str | None = None) -> list[dict]:
    """Lee las fichas activas y limpia automáticamente las de procesos ya cerrados."""
    raiz = carpeta or carpeta_fichas()
    if not os.path.isdir(raiz):
        return []
    vivas: list[dict] = []
    try:
        nombres = sorted(os.listdir(raiz))
    except OSError:
        return []
    for nombre in nombres:
        if not nombre.endswith(".json"):
            continue
        ruta = os.path.join(raiz, nombre)
        try:
            with open(ruta, encoding="utf-8") as f:
                ficha = json.load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(ficha, dict):
            continue
        pid = ficha.get("pid")
        puerto = ficha.get("puerto")
        token = ficha.get("token")
        if not isinstance(pid, int) or not isinstance(puerto, int) or not isinstance(token, str):
            continue
        if not proceso_vivo(pid):
            try:
                os.remove(ruta)
            except OSError:
                pass
            continue
        ficha = dict(ficha)
        ficha["_ruta"] = ruta
        vivas.append(ficha)
    vivas.sort(key=lambda x: (int(x.get("inicio", 0)), int(x.get("pid", 0))), reverse=True)
    return vivas
