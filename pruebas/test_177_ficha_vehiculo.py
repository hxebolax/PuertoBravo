"""Issue 45: la ficha técnica de los vehículos y la comparación con el tuyo."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import ficha_vehiculo as F, sistemas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _modelos():
    with open(os.path.join(RAIZ, "data", "datos", "vehiculos.json"), encoding="utf-8") as f:
        return {m["id"]: m for m in json.load(f)["vehiculos"]}


def test_cifras_salen_de_los_datos():
    mo = _modelos()["utilitario"]
    c = F.valores(mo)
    assert c["kmh"] == round(mo["vel_max"] * 3.6)
    assert c["salud"] == mo["salud"]
    assert abs(c["segundos"] - (50 / 3.6) / mo["acel"]) < 0.01
    assert abs(c["metros"] - (50 / 3.6) ** 2 / (2 * mo["freno"])) < 0.01


def test_ficha_nombra_todo():
    t = F.ficha(_modelos()["sedan"])
    for palabra in ("Velocidad máxima", "Aceleración", "Frenada", "Resistencia", "Depósito"):
        assert palabra in t


def test_bici_sin_combustible_y_hasta_su_punta():
    mo = _modelos()["bici"]
    t = F.ficha(mo)
    assert "No gasta combustible" in t
    assert F.valores(mo)["ref_kmh"] == round(mo["vel_max"] * 3.6)


def test_aeronave_sin_aceleracion_ni_frenada():
    t = F.ficha(_modelos()["helicoptero"])
    assert "Aceleración" not in t and "Frenada" not in t and "Velocidad máxima" in t


def test_barco_sin_en_seco():
    assert "en seco" not in F.ficha(_modelos()["lancha"])


def test_comparar_dice_solo_lo_que_cambia():
    m = _modelos()
    t = F.comparar(m["deportivo"], "Brisa", m["utilitario"])
    assert t.startswith("Frente a tu Brisa:")
    assert "más de punta" in t and "más rápido" in t and "menos de resistencia" in t
    assert F.comparar(m["utilitario"], "Brisa", m["utilitario"]) == "Frente a tu Brisa: va igual en todo."


def test_mejoras_cuentan():
    mo = _modelos()["sedan"]
    motor = next((k for k, d in sistemas.MEJORAS.items() if d["efecto"] == "motor"), None)
    if motor is None:
        return
    con = F.valores(mo, {motor: 1})
    assert con["kmh"] > F.valores(mo)["kmh"]
    assert "Con las mejoras" in F.ficha(mo, {motor: 1})
    assert "menos de punta" in F.comparar(mo, "Atlas", mo, {motor: 1})


def test_numero_con_coma():
    assert F._num(2.25) in ("2,2", "2,3", "2.2", "2.3")
    assert F._num(7.0) == "7"


class _V:
    def __init__(self, modelo, nombre):
        self.modelo, self.nombre, self.tag, self.mejoras = modelo, nombre, None, {}


class _J:
    def __init__(self, veh=None, barcos=None):
        self.veh, self.barcos = veh, barcos or []


class _P:
    def __init__(self, j, ultimo=None):
        self.j, self.modelos, self._u = j, _modelos(), ultimo

    def tu_vehiculo(self):
        return self._u


def test_compara_con_el_que_llevas():
    m = _modelos()
    p = _P(_J(veh=_V(m["sedan"], "Mi Atlas")))
    assert F.tuyo_para_comparar(p)[0] == "Mi Atlas"
    assert "Frente a tu Mi Atlas" in F.ayuda_compra(p, m["deportivo"])


def test_a_pie_compara_con_el_ultimo_y_en_el_agua_con_tu_barco():
    m = _modelos()
    p = _P(_J(barcos=[{"modelo": "lancha", "nombre": "La Gaviota"}]), ultimo=_V(m["moto"], "Rayo"))
    assert F.tuyo_para_comparar(p)[0] == "Rayo"
    assert F.tuyo_para_comparar(p, barco=True)[0] == "La Gaviota"


def test_sin_vehiculo_no_compara():
    p = _P(_J())
    p.mis_vivos = lambda: []
    t = F.ayuda_compra(p, _modelos()["sedan"])
    assert "Velocidad máxima" in t and "Frente a tu" not in t
