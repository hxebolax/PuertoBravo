"""Ficha técnica de un vehículo (issue 45): lo que corre, lo que acelera, lo que frena, lo que aguanta y lo que le cabe de
combustible, en cifras que se entienden de oído, y cómo queda frente al vehículo que tienes.

Las cifras salen de los datos del modelo (vehiculos.json: vel_max, acel, freno, salud, deposito o el depósito de su motor)
y, en un vehículo tuyo, de las mejoras del taller que lleva (sistemas.py), las mismas cuentas que usa la conducción. Aquí
no hay ningún número propio: si un mod cambia un modelo, la ficha cambia con él.
"""
from .i18n import tr
from . import combustible, i18n, sistemas

REF_KMH = 50                                   # la velocidad de referencia para acelerar y frenar: la de la ciudad


class _ConMejoras:
    """Lo mínimo que necesitan las cuentas de sistemas.py: un objeto con sus mejoras."""

    def __init__(self, mejoras):
        self.mejoras = dict(mejoras or {})


def valores(mo, mejoras=None):
    """Las cifras de un modelo, con las mejoras dadas: km/h de punta, segundos y metros para la velocidad de referencia,
    puntos de resistencia y litros de depósito (0 si no gasta)."""
    o = _ConMejoras(mejoras)
    vel = float(mo.get("vel_max", 0)) * sistemas.factor_velocidad(o)
    acel = max(0.1, float(mo.get("acel", 1)) * sistemas.factor_aceleracion(o))
    freno = max(0.1, float(mo.get("freno", 1)) * sistemas.factor_frenada(o))
    ref = min(REF_KMH / 3.6, vel)                              # una bici no llega a 50: se cuenta hasta su punta
    return {"kmh": int(round(vel * 3.6)), "ref_kmh": int(round(ref * 3.6)), "segundos": ref / acel, "metros": ref * ref / (2 * freno),
            "salud": int(round(float(mo.get("salud", 100)) * sistemas.factor_blindaje(o))),
            "litros": int(round(combustible.deposito(mo) * sistemas.factor_deposito(o))), "vuela": bool(mo.get("vuela")),
            "barco": bool(mo.get("barco"))}


def _num(x):
    """Un decimal si hace falta: 2,5 segundos; 7 metros. En inglés, con punto."""
    x = round(x, 1)
    return str(int(x)) if x == int(x) else f"{x:.1f}".replace(".", "." if i18n.actual() == "en" else ",")


def ficha(mo, mejoras=None):
    """La ficha en una frase por dato."""
    c = valores(mo, mejoras)
    partes = [tr('Velocidad máxima: {kmh} kilómetros por hora.').format(kmh=c["kmh"])]
    if not c["vuela"]:
        partes.append(tr('Aceleración: de parado a {ref} kilómetros por hora en {seg} segundos.').format(ref=c["ref_kmh"], seg=_num(c["segundos"])))
        partes.append((tr('Frenada: de {ref} kilómetros por hora a parado en {m} metros.') if c["barco"] else
                       tr('Frenada: de {ref} kilómetros por hora a parado en {m} metros, en seco.')).format(ref=c["ref_kmh"], m=_num(c["metros"])))
    partes.append(tr('Resistencia: {salud} puntos.').format(salud=c["salud"]))
    if c["litros"] > 0:
        partes.append(tr('Depósito: {litros} litros.').format(litros=c["litros"]))
    elif not c["vuela"] and not c["barco"]:
        partes.append(tr("No gasta combustible."))
    if mejoras and any(mejoras.values()):
        partes.append(tr("Con las mejoras del taller que lleva."))
    return " ".join(partes)


def comparar(mo, nombre_tuyo, mo_tuyo, mejoras_tuyas=None):
    """Cómo queda el modelo mo frente al tuyo, dato a dato, solo lo que cambia."""
    a, b = valores(mo), valores(mo_tuyo, mejoras_tuyas)
    partes = []
    d = a["kmh"] - b["kmh"]
    if d:
        partes.append((tr('{n} kilómetros por hora más de punta') if d > 0 else tr('{n} kilómetros por hora menos de punta')).format(n=abs(d)))
    if not a["vuela"] and not b["vuela"]:
        d = round(a["segundos"] - b["segundos"], 1)                       # misma referencia para los dos: la más baja de las dos puntas
        if a["ref_kmh"] == b["ref_kmh"] and d:
            partes.append((tr('acelera {n} segundos más lento') if d > 0 else tr('acelera {n} segundos más rápido')).format(n=_num(abs(d))))
        d = round(a["metros"] - b["metros"], 1)
        if a["ref_kmh"] == b["ref_kmh"] and d:
            partes.append((tr('necesita {n} metros más para frenar') if d > 0 else tr('frena en {n} metros menos')).format(n=_num(abs(d))))
    d = a["salud"] - b["salud"]
    if d:
        partes.append((tr('{n} puntos más de resistencia') if d > 0 else tr('{n} puntos menos de resistencia')).format(n=abs(d)))
    d = a["litros"] - b["litros"]
    if d and a["litros"] and b["litros"]:
        partes.append((tr('{n} litros más de depósito') if d > 0 else tr('{n} litros menos de depósito')).format(n=abs(d)))
    if not partes:
        return tr('Frente a tu {nombre}: va igual en todo.').format(nombre=nombre_tuyo)
    return tr('Frente a tu {nombre}: {cambios}.').format(nombre=nombre_tuyo, cambios=", ".join(partes))


def tuyo_para_comparar(p, barco=False):
    """El vehículo tuyo con el que comparar: (nombre, modelo, mejoras), o None. En tierra, el que llevas; si no, el último
    que has usado; si no, el primero de Mis vehículos. En el agua, tu primera embarcación."""
    if barco:
        for b in getattr(p.j, "barcos", None) or []:
            mo = p.modelos.get(b.get("modelo"))
            if mo:
                return b.get("nombre") or mo["nombre"], mo, b.get("mejoras")
        return None
    for v in (getattr(p.j, "veh", None), p.tu_vehiculo() if hasattr(p, "tu_vehiculo") else None):
        if v is not None and not v.tag and not v.modelo.get("barco"):
            return v.nombre, v.modelo, getattr(v, "mejoras", None)
    try:
        from .misvehiculos import lista_mis_vehiculos
        for f in lista_mis_vehiculos(p):
            v, d = f.get("veh"), f.get("datos")
            if v is not None and not v.modelo.get("barco"):
                return v.nombre, v.modelo, getattr(v, "mejoras", None)
            if d is not None and d.get("modelo") in p.modelos:
                return f["nombre"], p.modelos[d["modelo"]], d.get("mejoras")
    except Exception:
        pass
    return None


def ayuda_compra(p, mo):
    """Lo que dice F1 (o el botón Y) sobre un modelo a la venta: la descripción, la ficha y la comparación con el tuyo."""
    partes = [mo.get("desc", ""), ficha(mo)]
    tuyo = tuyo_para_comparar(p, barco=bool(mo.get("barco")))
    if tuyo is not None:
        partes.append(comparar(mo, *tuyo))
    return " ".join(x for x in partes if x)
