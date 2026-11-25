"""Protocolo NDJSON local y cliente síncrono para comunicarse con Puerto Bravo."""
from __future__ import annotations

import json
import socket

from juego.i18n import tr

from . import descubrir_instancias

MAX_MENSAJE = 4 * 1024 * 1024  # 4 MiB


class ErrorPuente(RuntimeError):
    """Error de comunicación o rechazo devuelto por el puente del juego."""


def leer_linea_socket(sock: socket.socket, max_bytes: int = MAX_MENSAJE) -> str:
    """Lee una línea UTF-8 terminada en '\\n' desde un socket TCP."""
    trozos: list[bytes] = []
    total = 0
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            break
        nl = chunk.find(b"\n")
        if nl != -1:
            trozos.append(chunk[:nl])
            break
        total += len(chunk)
        if total > max_bytes:
            raise ErrorPuente(tr("Mensaje recibido demasiado grande."))
        trozos.append(chunk)
    return b"".join(trozos).decode("utf-8", errors="replace").strip()


class ClienteTrampas:
    """Cliente TCP local autenticado por token contra el puente del juego."""

    def __init__(self, puerto: int, token: str, host: str = "127.0.0.1", timeout: float = 4.0) -> None:
        self.host = host
        self.puerto = int(puerto)
        self.token = str(token)
        self.timeout = float(timeout)

    @classmethod
    def desde_ficha(cls, ficha: dict, timeout: float = 4.0) -> "ClienteTrampas":
        return cls(int(ficha["puerto"]), str(ficha["token"]), timeout=timeout)

    @classmethod
    def conectar_auto(cls, carpeta: str | None = None, timeout: float = 4.0) -> tuple["ClienteTrampas", dict]:
        """Descubre instancias vivas del juego y conecta a la más reciente que responda."""
        instancias = descubrir_instancias(carpeta)
        if not instancias:
            raise ErrorPuente(
                tr("No se encontró ninguna instancia de Puerto Bravo en ejecución con el puente de trampas activo.")
            )
        ultimo_error: Exception | None = None
        for ficha in instancias:
            cliente = cls.desde_ficha(ficha, timeout=timeout)
            try:
                info = cliente.llamar("hola")
                return cliente, dict(ficha, info=info)
            except Exception as exc:
                ultimo_error = exc
        raise ErrorPuente(tr("No se pudo conectar con Puerto Bravo: {exc}").format(exc=ultimo_error))

    def llamar(self, cmd: str, **args):
        """Envía una orden JSON-RPC al juego y devuelve ``datos`` o lanza ErrorPuente."""
        payload = json.dumps({"token": self.token, "cmd": cmd, "args": args}, ensure_ascii=False).encode("utf-8") + b"\n"
        try:
            with socket.create_connection((self.host, self.puerto), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(payload)
                linea = leer_linea_socket(sock)
        except OSError as exc:
            raise ErrorPuente(tr("Sin conexión con el juego ({exc}).").format(exc=exc)) from exc
        if not linea:
            raise ErrorPuente(tr("El juego cerró la conexión sin responder."))
        try:
            resp = json.loads(linea)
        except ValueError as exc:
            raise ErrorPuente(tr("Respuesta inválida del juego: {exc}").format(exc=exc)) from exc
        if not isinstance(resp, dict):
            raise ErrorPuente(tr("Formato de respuesta inesperado."))
        if not resp.get("ok"):
            raise ErrorPuente(str(resp.get("error") or tr("Error desconocido en el juego.")))
        return resp.get("datos")
