"""Propagación horizontal por las calles y las puertas del mapa."""
import math

from .mundo import ACERA, B


def pared(mundo, a, b):
    """Primer punto sólido del segmento. Las alturas se resuelven en el llamante."""
    distancia = math.dist(a, b)
    pasos = max(1, math.ceil(distancia / 2.5))
    for i in range(1, pasos):
        t = i / pasos
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        if mundo.superficie(x, y) == "pared":
            return x, y
    return None


def trayectoria(mundo, oyente, fuente, coches, altura_oyente=0., altura_fuente=0.):
    """Punto aparente, ganancia directa y cantidad de filtrado."""
    d = math.dist(oyente, fuente)
    if d < 1 or mundo.tipo == "mar":
        return fuente, 1., 0.
    obstaculo = pared(mundo, oyente, fuente)
    if obstaculo:
        i, j = mundo.bloque(*obstaculo)
        esquinas = [(x, y) for x in (i * B + ACERA, (i + 1) * B - ACERA)
                    for y in (j * B + ACERA, (j + 1) * B - ACERA)]
        for esquina in sorted(esquinas, key=lambda p: math.dist(oyente, p) + math.dist(p, fuente)):
            longitud = math.dist(oyente, esquina) + math.dist(esquina, fuente)
            if longitud < d + 55 and not pared(mundo, oyente, esquina) and not pared(mundo, esquina, fuente):
                return esquina, .62 * d / max(d, longitud), .55
        return fuente, .24, .82
    dx, dy = fuente[0] - oyente[0], fuente[1] - oyente[1]
    cobertura = 0.
    for x, y in coches:
        t = ((x - oyente[0]) * dx + (y - oyente[1]) * dy) / (d * d)
        if not 1.8 < t * d < d - 1.8 or altura_oyente + t * (altura_fuente - altura_oyente) > 1.5:
            continue
        lateral = math.hypot(x - oyente[0] - t * dx, y - oyente[1] - t * dy)
        # Aproximación conservadora de la carrocería: borde suave dentro de su anchura.
        cobertura = max(cobertura, min(1., (.95 - lateral) / .55))
    return fuente, 1. - .32 * cobertura, .5 * cobertura


def imagen_fachada(mundo, origen):
    """Fuente virtual reflejada por la fachada cercana al disparo."""
    x, y = origen
    for distancia in (3, 6, 10, 16, 24):
        for dx, dy in ((distancia, 0), (-distancia, 0), (0, distancia), (0, -distancia)):
            if mundo.superficie(x + dx, y + dy) == "pared":
                return x + 2 * dx, y + 2 * dy
    return origen
