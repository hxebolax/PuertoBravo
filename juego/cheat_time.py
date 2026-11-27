"""Saved, accessible world speed control for optional offline cheats."""
import math

import pygame

from .cheats import text
from .menus import Menu, Opcion

DEFAULT_RATE = 0.25
SETTING = "cheat_velocidad_mundo"


def _valid_rate(value):
    if isinstance(value, bool):
        return DEFAULT_RATE
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return DEFAULT_RATE
    return max(0.0, min(5.0, value)) if math.isfinite(value) else DEFAULT_RATE


def configured_rate(cfg):
    """Read a finite 0..5 rate without changing saved options."""
    return _valid_rate(cfg.v.get(SETTING, DEFAULT_RATE))


def world_rate(p):
    """Return the offline world multiplier, or None for ordinary game timing."""
    if not p.cheat_on("cheat_tiempo") or p.online_activo():
        return None
    return configured_rate(p.cfg)


def speed_label(cfg):
    percent = format(configured_rate(cfg) * 100, ".6g")
    return text("Velocidad del mundo: {p} por ciento; jugador a velocidad normal",
                "World speed: {p} percent; player at normal speed").format(p=percent)


class WorldSpeedMenu(Menu):
    """A normal spoken menu with a bounded slider and explicit presets."""
    def __init__(self, app):
        self.cfg = app.cfg
        self.cfg[SETTING] = configured_rate(self.cfg)
        help_text = text(
            "Izquierda y derecha: cinco puntos porcentuales. Inicio: cero, mundo detenido. Fin: quinientos por ciento. Cien es velocidad normal; el jugador conserva su velocidad normal. Intro confirma y vuelve; Escape también conserva el cambio.",
            "Left and right: five percentage points. Home: zero, world stopped. End: five hundred percent. One hundred is normal speed; the player keeps normal speed. Enter confirms and returns; Escape also keeps the change.")
        options = [Opcion(lambda: speed_label(self.cfg), self._volver, self.adjust, ayuda=help_text)]
        for rate, es, en in (
                (DEFAULT_RATE, "Un cuarto de velocidad: 25 por ciento", "Quarter speed: 25 percent"),
                (1.0, "Restablecer velocidad normal: 100 por ciento", "Reset to normal speed: 100 percent"),
                (0.0, "Detener el mundo: cero por ciento", "Stop the world: zero percent")):
            options.append(Opcion(text(es, en), lambda rate=rate: self.preset(rate), ayuda=help_text))
        options.append(Opcion(text("Volver", "Back"), self._volver, ayuda=help_text))
        super().__init__(app, text("Velocidad del mundo", "World speed"), options,
                         al_cerrar=self.cfg.guardar,
                         intro=text("Se guarda cada cambio. Solo actúa con el truco del tiempo activado y sin conexión.",
                                    "Each change is saved. Applies only with the world-time cheat enabled and offline."))

    def set_position(self, position):
        self.cfg[SETTING] = max(0, min(100, int(position))) / 20.0
        self.cfg.guardar()

    def adjust(self, delta):
        position = round(configured_rate(self.cfg) * 20)
        self.set_position(position + delta)

    def preset(self, rate):
        self.cfg[SETTING] = _valid_rate(rate)
        self.cfg.guardar()
        self.app.cerrar(self)

    def tecla(self, ev):
        if self.i == 0 and ev.key in (pygame.K_HOME, pygame.K_END):
            self.set_position(0 if ev.key == pygame.K_HOME else 100)
            self.app.son("menu_ajuste")
            self.leer()
        else:
            super().tecla(ev)


def open_speed_menu(app):
    p = getattr(app, "partida", None)
    if p is not None:
        p.cheat_sync_focus()
    menu = WorldSpeedMenu(app)
    app.abrir(menu)
    return menu
