"""Todos los efectos de sonido del juego, sintetizados con numpy.

No hay ni un archivo de audio: cada sonido se genera al arrancar (y se guarda
en caché). Para sustituir uno por una grabación propia basta con dejar un WAV
con el mismo nombre en la carpeta mods/sonidos.
"""
import math
import os

import numpy as np

SR = 44100
VERSION_CACHE = 26
PI2 = 2 * np.pi


def _t(d):
    return np.arange(int(SR * d)) / SR


def _filtro(x, lo=None, hi=None, orden=4):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1.0 / SR)
    g = np.ones_like(f)
    if hi:
        g *= 1.0 / (1.0 + (f / hi) ** orden)
    if lo:
        r = (f / lo) ** orden
        g *= r / (1.0 + r)
    return np.fft.irfft(X * g, len(x))


def _norm(x, pico=0.8):
    m = np.max(np.abs(x)) if len(x) else 0
    if m > 0:
        x = x * (pico / m)
    return x.astype(np.float32)


def _bordes(x, ms=4):
    n = min(int(SR * ms / 1000), len(x) // 2)
    if n > 0:
        r = np.linspace(0, 1, n)
        x = x.copy()
        x[:n] *= r
        x[-n:] *= r[::-1]
    return x


def _decae(d, tau, ataque=0.003):
    t = _t(d)
    return np.minimum(1.0, t / ataque) * np.exp(-t / tau)


def _bucle(x, ms=60):
    """Funde el final con el principio para que el bucle no haga clic."""
    n = min(int(SR * ms / 1000), len(x) // 3)
    r = np.linspace(0, 1, n)
    cuerpo = x[:-n].copy()
    cuerpo[:n] = cuerpo[:n] * r + x[-n:] * (1 - r)
    return cuerpo


def _seno(f, d, fase=0.0):
    return np.sin(PI2 * f * _t(d) + fase)


def _barrido(f0, f1, d, forma="seno"):
    t = _t(d)
    f = f0 + (f1 - f0) * (t / d)
    fase = PI2 * np.cumsum(f) / SR
    if forma == "sierra":
        return 2 * ((fase / PI2) % 1.0) - 1
    if forma == "cuadrada":
        return np.sign(np.sin(fase))
    return np.sin(fase)


def _sierra(f, d):
    return 2 * ((f * _t(d)) % 1.0) - 1


def _cuadrada(f, d):
    return np.sign(np.sin(PI2 * f * _t(d)))


def _nota(f, d, tau=0.25, arm=(1, 0.4, 0.2)):
    x = sum(a * _seno(f * (k + 1), d) for k, a in enumerate(arm))
    return x * _decae(d, tau)


def _poner(dest, x, t0, g=1.0):
    i = int(t0 * SR)
    if i >= len(dest):
        return
    n = min(len(x), len(dest) - i)
    dest[i:i + n] += x[:n] * g


def _sec(notas, paso, d_nota, tau=0.2, arm=(1, 0.4, 0.2)):
    out = np.zeros(int(SR * (paso * len(notas) + d_nota)))
    for k, f in enumerate(notas):
        if f:
            _poner(out, _nota(f, d_nota, tau, arm), k * paso)
    return out


def generar(semilla=7):
    rng = np.random.default_rng(semilla)
    S = {}

    def ruido(d):
        return rng.standard_normal(int(SR * d))

    # ------------------------------------------------------------ interfaz
    S["menu_mover"] = _norm(_seno(1100, 0.03) * _decae(0.03, 0.01), 0.35)
    S["menu_ok"] = _norm(_sec([880, 1320], 0.06, 0.15, 0.06), 0.5)
    S["menu_atras"] = _norm(_sec([660, 440], 0.06, 0.15, 0.06), 0.5)
    S["menu_borde"] = _norm(_seno(180, 0.08) * _decae(0.08, 0.03), 0.5)
    S["menu_ajuste"] = _norm(_seno(1500, 0.03) * _decae(0.03, 0.012), 0.35)
    S["error"] = _norm(_filtro(_cuadrada(140, 0.22), hi=1200) * _decae(0.22, 0.12), 0.5)
    S["notificacion"] = _norm(_sec([988, 1319, 1568], 0.08, 0.3, 0.12), 0.5)
    S["mision_ok"] = _norm(_sec([523, 659, 784, 1047, 784, 1047], 0.11, 0.7, 0.3, (1, 0.5, 0.3, 0.2)), 0.7)
    S["mision_fallo"] = _norm(_sec([392, 370, 330, 262], 0.2, 0.8, 0.4, (1, 0.6, 0.4)), 0.7)
    S["dinero"] = _norm(_sec([2093, 2637, 0, 2093, 3136], 0.05, 0.3, 0.08, (1, 0.3)), 0.5)
    S["guardado"] = _norm(_sec([659, 784, 1047], 0.09, 0.4, 0.15), 0.5)
    S["movil"] = _norm(_sec([1319, 1760], 0.05, 0.12, 0.04), 0.4)
    S["dialogo"] = _norm(_seno(700, 0.05) * _decae(0.05, 0.02), 0.3)
    S["pasan_horas"] = _norm(_sec([440, 554, 659, 554, 440], 0.25, 0.6, 0.3), 0.4)

    # --------------------------------------------------------------- pasos
    def paso(lo, hi, d, tau, g):
        return _norm(_filtro(ruido(d), lo, hi) * _decae(d, tau, 0.002), g)

    for k in range(2):
        S[f"paso_acera{k}"] = paso(700, 3200, 0.09, 0.02, 0.45)
        S[f"paso_calzada{k}"] = paso(250, 1300, 0.1, 0.03, 0.5)
        S[f"paso_hierba{k}"] = paso(2000, 7000, 0.16, 0.05, 0.3)
        S[f"paso_arena{k}"] = paso(500, 3000, 0.2, 0.07, 0.35)
        S[f"paso_plaza{k}"] = paso(1200, 4500, 0.08, 0.018, 0.45)
        S[f"paso_muelle{k}"] = _norm(_filtro(ruido(0.14), 90, 600) * _decae(0.14, 0.04), 0.6)
    S["paso_npc"] = paso(500, 2200, 0.08, 0.02, 0.3)
    S["choque_pared"] = _norm(_filtro(ruido(0.12), 80, 500) * _decae(0.12, 0.04), 0.6)

    # ------------------------------------------------------------- personas
    def vocal(f0, f1, d, formantes, tau):
        x = _barrido(f0, f1, d, "sierra")
        y = sum(_filtro(x, fo * 0.8, fo * 1.25, 6) for fo in formantes)
        return y * _decae(d, tau, 0.02)

    S["dolor"] = _norm(vocal(150, 95, 0.3, (650, 1100), 0.15), 0.6)
    S["dolor_npc"] = _norm(vocal(190, 120, 0.28, (700, 1250), 0.14), 0.6)
    S["muerte_npc"] = _norm(vocal(170, 70, 0.7, (600, 1000), 0.35), 0.6)
    S["grito"] = _norm(np.concatenate([vocal(450, 760, 0.25, (900, 1900), 0.4),
                                       vocal(760, 380, 0.5, (900, 1900), 0.3)]), 0.55)
    S["murmullo"] = _norm(vocal(130, 115, 0.35, (500, 1400), 0.3) + 0.6 * np.roll(vocal(160, 140, 0.35, (450, 1500), 0.3), 4000), 0.3)
    S["golpe"] = _norm(_filtro(ruido(0.1), 60, 900) * _decae(0.1, 0.03) + _seno(90, 0.1) * _decae(0.1, 0.04), 0.8)
    S["golpe_aire"] = _norm(_filtro(ruido(0.15), 800, 4000) * np.sin(np.pi * _t(0.15) / 0.15) ** 2, 0.3)
    lat = _seno(55, 0.16) * _decae(0.16, 0.05)
    lz = np.zeros(SR)
    _poner(lz, lat, 0.0)
    _poner(lz, lat, 0.28, 0.7)
    S["latido"] = _norm(lz, 0.8)
    cr = np.zeros(int(SR * 0.6))
    for k in range(4):
        _poner(cr, _filtro(ruido(0.07), 1500, 6000) * _decae(0.07, 0.02), 0.14 * k)
    S["comer"] = _norm(cr, 0.4)
    S["curar"] = _norm(_sec([523, 659, 784, 1047], 0.07, 0.5, 0.25), 0.5)

    # ---------------------------------------------------------------- armas
    def disparo(lo, hi, d, tau, grave):
        x = _filtro(ruido(d), lo, hi) * _decae(d, tau, 0.0008)
        x += grave * _barrido(160, 50, d) * _decae(d, tau * 0.8, 0.001)
        return _norm(np.tanh(x * 3), 0.95)

    S["disparo_pistola"] = disparo(300, 5000, 0.35, 0.05, 0.6)
    S["disparo_revolver"] = disparo(200, 3500, 0.5, 0.08, 1.0)
    S["disparo_subfusil"] = disparo(500, 6000, 0.2, 0.03, 0.4)
    S["disparo_escopeta"] = disparo(120, 3000, 0.7, 0.12, 1.2)
    S["disparo_rifle"] = disparo(250, 7000, 0.8, 0.1, 0.8)
    S["sin_balas"] = _norm(_filtro(ruido(0.04), 2000, 8000) * _decae(0.04, 0.008), 0.4)
    rc = np.zeros(int(SR * 0.7))
    _poner(rc, _filtro(ruido(0.06), 1500, 6000) * _decae(0.06, 0.015), 0.0)
    _poner(rc, _filtro(ruido(0.08), 800, 4000) * _decae(0.08, 0.02), 0.3)
    _poner(rc, _filtro(ruido(0.06), 2000, 7000) * _decae(0.06, 0.012), 0.5)
    S["recarga"] = _norm(rc, 0.5)
    S["amartillar"] = _norm(rc[int(SR * 0.28): int(SR * 0.6)], 0.45)
    S["bala_impacto"] = _norm(_filtro(ruido(0.12), 1500, 7000) * _decae(0.12, 0.02) + 0.5 * _barrido(3000, 1200, 0.12) * _decae(0.12, 0.04), 0.5)
    S["bala_silbido"] = _norm(_barrido(4200, 1500, 0.18) * np.sin(np.pi * _t(0.18) / 0.18) ** 2, 0.5)
    ex = _filtro(ruido(1.8), 30, 1800) * _decae(1.8, 0.45, 0.002) + 1.5 * _barrido(90, 30, 1.8) * _decae(1.8, 0.3)
    S["explosion"] = _norm(np.tanh(ex * 2.5), 0.98)
    S["navaja"] = _norm(_filtro(ruido(0.12), 2500, 9000) * np.sin(np.pi * _t(0.12) / 0.12) ** 3, 0.4)

    # ------------------------------------------------------------ vehículos
    def motor(f0, n_arm, brillo, rugoso):
        d = 1.0
        t = _t(d)
        x = np.zeros_like(t)
        for k in range(1, n_arm + 1):
            x += np.sin(PI2 * f0 * k * t + rng.uniform(0, PI2)) / (k ** brillo)
        x *= 1.0 + 0.35 * np.sin(PI2 * (f0 / 2) * t) + 0.15 * np.sin(PI2 * (f0 / 4) * t)
        x += rugoso * _filtro(ruido(d), 100, 1200)
        return _norm(np.tanh(x * 1.2), 0.55)

    S["motor_coche"] = motor(56, 12, 1.0, 0.25)
    S["motor_deportivo"] = motor(80, 16, 0.7, 0.2)
    S["motor_moto"] = motor(96, 14, 0.5, 0.35)
    S["motor_camion"] = motor(40, 10, 1.1, 0.5)
    S["motor_furgoneta"] = motor(48, 10, 1.0, 0.4)
    rod = _filtro(ruido(1.5), 300, 2500)
    S["rodadura"] = _norm(_bucle(rod), 0.4)
    S["claxon"] = _norm(_bordes(_filtro(_cuadrada(420, 0.45) + _cuadrada(530, 0.45), hi=2500), 10), 0.6)
    S["claxon_camion"] = _norm(_bordes(_filtro(_cuadrada(170, 0.7) + _cuadrada(215, 0.7), hi=1500), 15), 0.7)
    fr = _filtro(ruido(0.9), 900, 2600, 6) + 0.5 * _barrido(1100, 850, 0.9, "sierra")
    S["frenazo"] = _norm(_bordes(fr * (1 - 0.6 * _t(0.9) / 0.9), 20), 0.5)
    ch = _filtro(ruido(0.6), 80, 2500) * _decae(0.6, 0.12, 0.001)
    for f in (310, 470, 830, 1240):
        ch += 0.25 * _seno(f, 0.6) * _decae(0.6, 0.1)
    S["choque"] = _norm(np.tanh(ch * 2), 0.9)
    S["choque_leve"] = _norm(ch[: int(SR * 0.3)] * _decae(0.3, 0.06), 0.6)
    pu = _seno(110, 0.18) * _decae(0.18, 0.04) + 0.5 * _filtro(ruido(0.18), 1000, 4000) * _decae(0.18, 0.012)
    S["puerta_coche"] = _norm(pu, 0.7)
    al = np.concatenate([_cuadrada(900, 0.25), _cuadrada(1250, 0.25)])
    S["alarma"] = _norm(_filtro(np.tile(al, 2), hi=4000), 0.5)
    arr = _filtro(_sierra(38, 0.9) * (0.6 + 0.4 * np.sin(PI2 * 9 * _t(0.9))), hi=900)
    S["arranque"] = _norm(_bordes(arr, 20), 0.6)
    # el motor que se para al girar la llave: baja de vueltas, tiembla y se calla, con el clic de la llave al final (issue 48)
    tap = _t(1.2)
    fap = 52 * (1 - 0.62 * tap / 1.2)
    fase = np.cumsum(fap) / SR
    ap = (2 * (fase % 1) - 1) * (0.55 + 0.45 * np.sin(PI2 * 7 * tap)) * (1 - tap / 1.2) ** 1.6
    ap = _filtro(ap, hi=850)
    clic = _filtro(np.random.default_rng(48).standard_normal(int(SR * 0.04)), 1500, 5000) * _decae(0.04, 0.008)      # semilla propia: no cambia los sonidos que vienen después
    S["motor_apagar"] = _norm(_bordes(np.concatenate([ap, np.zeros(int(SR * 0.05)), 0.5 * clic]), 15), 0.55)
    tw = _t(2.0)
    fw = 650 + 650 * (0.5 - 0.5 * np.cos(PI2 * tw / 2.0))
    S["sirena"] = _norm(_filtro(np.sign(np.sin(PI2 * np.cumsum(fw) / SR)), hi=3500), 0.5)
    S["sirena_lejana"] = _norm(_filtro(S["sirena"].astype(np.float64), hi=800), 0.25)
    cris = _filtro(ruido(0.7), 3000, 12000) * _decae(0.7, 0.1, 0.001)
    for _ in range(14):
        _poner(cris, _seno(rng.uniform(3000, 9000), 0.3) * _decae(0.3, rng.uniform(0.02, 0.1)), rng.uniform(0, 0.3), 0.2)
    S["cristal"] = _norm(cris, 0.6)
    gz = np.zeros(SR)
    for k in range(9):
        _poner(gz, _seno(rng.uniform(2500, 5000), 0.03) * _decae(0.03, 0.006), k * 0.11 + rng.uniform(0, 0.03), rng.uniform(0.4, 1))
    S["ganzua"] = _norm(gz, 0.4)
    it = np.zeros(int(SR * 0.8))
    _poner(it, _seno(1800, 0.02) * _decae(0.02, 0.005), 0.0)
    _poner(it, _seno(1300, 0.02) * _decae(0.02, 0.005), 0.4)
    S["intermitente"] = _norm(it, 0.35)
    S["radio_cambio"] = _norm(_bordes(_filtro(ruido(0.3), 1000, 6000), 20), 0.3)
    S["reparar"] = _norm(np.concatenate([_filtro(_sierra(180, 0.25) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 30 * _t(0.25)))), hi=3000)] * 3), 0.5)
    S["pintura"] = _norm(_bordes(_filtro(ruido(1.2), 3000, 10000), 80), 0.4)
    S["fuego"] = _norm(_bucle(_filtro(ruido(2.0), 200, 3000) * (0.6 + 0.4 * _filtro(ruido(2.0), hi=12))), 0.5)

    # --------------------------------------------------- ayudas de orientación
    S["baliza"] = _norm(_nota(880, 0.35, 0.1, (1, 0.5, 0.25)) + _nota(1320, 0.35, 0.12, (0.6, 0.2)), 0.6)
    S["baliza_destino"] = _norm(_sec([1047, 1568], 0.09, 0.35, 0.12, (1, 0.4, 0.2)), 0.6)
    S["sonar"] = _norm(_bordes(_seno(1500, 0.05), 3), 0.45)
    S["tono_objetivo"] = _norm(_bordes(_seno(660, 0.07) + 0.4 * _seno(1980, 0.07), 6), 0.45)
    S["tono_apuntado"] = _norm(_bordes(_seno(1320, 0.04), 4), 0.4)
    S["tono_pared"] = _norm(_bordes(_seno(440, 0.15), 10), 0.4)
    S["tono_libre"] = _norm(_bordes(_seno(880, 0.08), 8), 0.3)
    S["bordillo"] = _norm(_bordes(_filtro(_cuadrada(85, 0.12), hi=500), 8), 0.6)
    S["cruce"] = _norm(_sec([784, 988], 0.07, 0.25, 0.09), 0.4)
    S["llegada"] = _norm(_sec([784, 988, 1175, 1568], 0.08, 0.5, 0.2), 0.6)
    S["radar"] = _norm(_bordes(_seno(1000, 0.06) * (1 + 0.5 * _seno(2000, 0.06)), 5), 0.45)
    S["estrella_sube"] = _norm(_filtro(_barrido(300, 900, 0.4, "sierra"), hi=3000) * _decae(0.4, 0.5, 0.01), 0.6)
    S["estrella_baja"] = _norm(_sec([880, 659, 523], 0.1, 0.4, 0.2), 0.45)
    S["policia_perdida"] = _norm(_sec([523, 659, 784, 1047], 0.12, 0.9, 0.5, (1, 0.5, 0.3)), 0.6)
    S["buscando"] = _norm(_seno(70, 0.12) * _decae(0.12, 0.04), 0.6)
    S["reloj"] = _norm(_seno(2000, 0.03) * _decae(0.03, 0.008), 0.4)
    S["semaforo_pio"] = _norm(_barrido(2900, 1900, 0.09) * _decae(0.09, 0.05, 0.005), 0.4)
    S["semaforo_tic"] = _norm(_seno(1000, 0.03) * _decae(0.03, 0.01), 0.4)
    # al volante (versión 1.7.3): el semáforo del próximo cruce. Rojo, dos notas graves que bajan; verde, dos agudas que suben
    S["semaforo_rojo"] = _norm(_sec([494, 370], 0.11, 0.3, 0.12, (1, 0.5, 0.25)), 0.45)
    S["semaforo_verde"] = _norm(_sec([880, 1319], 0.08, 0.25, 0.1, (1, 0.3)), 0.4)
    S["recoger"] = _norm(_barrido(600, 1800, 0.18) * _decae(0.18, 0.2, 0.01), 0.5)
    S["esposas"] = _norm(np.concatenate([S["ganzua"][: int(SR * 0.35)], _filtro(ruido(0.1), 1500, 6000) * _decae(0.1, 0.02)]), 0.5)

    # --------------------------------------------- localizadores (en bucle)
    ob = np.zeros(int(SR * 1.2))
    _poner(ob, _nota(1568, 0.2, 0.05, (1, 0.3)), 0.0)
    _poner(ob, _nota(2093, 0.2, 0.05, (1, 0.3)), 0.12)
    S["loc_objeto"] = _norm(ob, 0.5)
    cs = np.zeros(int(SR * 1.6))
    for k, f in enumerate([1319, 1568, 1976, 2637, 1976, 1568]):
        _poner(cs, _nota(f, 0.3, 0.1, (1, 0.2)), k * 0.12)
    S["loc_casete"] = _norm(cs, 0.45)
    mi = np.zeros(int(SR * 1.5))
    _poner(mi, (_seno(392, 0.9) + _seno(587, 0.9) + 0.5 * _seno(784, 0.9)) * np.sin(np.pi * _t(0.9) / 0.9) ** 2, 0.1)
    S["loc_mision"] = _norm(mi, 0.5)
    lu = np.zeros(int(SR * 2.0))
    _poner(lu, _nota(523, 0.4, 0.15, (1, 0.5, 0.2)), 0.0)
    S["loc_lugar"] = _norm(lu, 0.4)
    vp = np.zeros(int(SR * 1.8))
    _poner(vp, _filtro(ruido(0.05), 2500, 7000) * _decae(0.05, 0.012), 0.0)
    _poner(vp, _filtro(ruido(0.05), 2500, 7000) * _decae(0.05, 0.012), 0.2)
    S["loc_vehiculo"] = _norm(vp, 0.3)

    # ---------------------------------------------------- firmas de lugares
    def bucle_eventos(d, eventos):
        out = np.zeros(int(SR * d))
        for x, t0, g in eventos:
            _poner(out, x, t0, g)
        return out

    S["lugar_armeria"] = _norm(bucle_eventos(2.6, [(S["amartillar"].astype(np.float64), 0.2, 1), (S["sin_balas"].astype(np.float64), 1.4, 0.8)]), 0.45)
    fri = _filtro(ruido(2.0), 3500, 11000) * (0.5 + 0.5 * np.abs(_filtro(ruido(2.0), hi=25)) * 6)
    S["lugar_comida"] = _norm(_bucle(fri), 0.3)
    S["lugar_hospital"] = _norm(bucle_eventos(1.0, [(_bordes(_seno(1000, 0.09), 4), 0.0, 1)]), 0.4)
    com = np.zeros(int(SR * 3.0))
    for t0, dd in ((0.1, 0.5), (0.9, 0.3), (1.6, 0.7)):
        _poner(com, _bordes(_filtro(ruido(dd), 700, 2600, 6) * (0.4 + np.abs(_filtro(ruido(dd), hi=14)) * 5), 8), t0)
    _poner(com, _bordes(_seno(1700, 0.06), 4), 2.4, 0.5)
    S["lugar_comisaria"] = _norm(com, 0.4)
    ta = np.zeros(int(SR * 3.0))
    for t0 in (0.2, 0.7, 1.9):
        _poner(ta, _bordes(_filtro(_sierra(170, 0.35) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 28 * _t(0.35)))), hi=2800), 6), t0)
    S["lugar_taller"] = _norm(ta, 0.45)
    cam = np.zeros(int(SR * 4.0))
    for _ in range(9):
        _poner(cam, _nota(rng.choice([1047, 1175, 1319, 1568, 1760, 2093]), 0.9, 0.4, (1, 0.3, 0.1)), rng.uniform(0, 3.0), rng.uniform(0.3, 1))
    S["lugar_casa"] = _norm(cam, 0.4)
    bar = np.zeros(int(SR * 2.0))
    for k in range(4):
        _poner(bar, _barrido(120, 45, 0.25) * _decae(0.25, 0.08), k * 0.5)
        _poner(bar, _filtro(_sierra([55, 55, 65.4, 49][k], 0.22), hi=300) * _decae(0.22, 0.2), k * 0.5 + 0.25, 0.6)
    S["lugar_bar"] = _norm(_filtro(bar, hi=500), 0.6)
    cas = np.zeros(int(SR * 2.4))
    for k in range(16):
        _poner(cas, _nota([1047, 1319, 1568, 2093][k % 4] * (1 + (k // 8) * 0.122), 0.12, 0.04, (1, 0.5)), k * 0.09)
    _poner(cas, S["dinero"].astype(np.float64), 1.6, 0.8)
    S["lugar_casino"] = _norm(cas, 0.4)
    S["lugar_tienda"] = _norm(bucle_eventos(3.2, [(_nota(1319, 0.7, 0.3, (1, 0.3)), 0.1, 1), (_nota(1047, 0.9, 0.4, (1, 0.3)), 0.55, 1)]), 0.4)
    S["lugar_banco"] = _norm(bucle_eventos(2.4, [(_bordes(_seno(1400, 0.05), 3), 0.1 + 0.16 * k, 1) for k in range(4)] + [(_bordes(_seno(1900, 0.2), 5), 1.1, 0.8)]), 0.35)
    camp = sum(a * _seno(f, 3.5) * _decae(3.5, tau) for f, a, tau in ((220, 1, 1.4), (440.5, 0.6, 1.0), (594, 0.45, 0.8), (880, 0.3, 0.5), (1175, 0.2, 0.3)))
    S["lugar_iglesia"] = _norm(camp, 0.5)
    ag = _filtro(ruido(3.0), 900, 6000) * (0.6 + 0.4 * np.abs(_filtro(ruido(3.0), hi=18)) * 5)
    S["lugar_fuente"] = _norm(_bucle(ag), 0.35)
    S["lugar_contacto"] = S["loc_mision"]
    S["lugar_generico"] = S["loc_lugar"]
    tx = np.zeros(int(SR * 2.5))
    _poner(tx, S["claxon"].astype(np.float64)[: int(SR * 0.12)], 0.1, 0.5)
    _poner(tx, S["claxon"].astype(np.float64)[: int(SR * 0.12)], 0.3, 0.5)
    S["lugar_taxi"] = _norm(tx, 0.3)
    S["lugar_periodico"] = _norm(bucle_eventos(2.0, [(_filtro(ruido(0.03), 1500, 5000) * _decae(0.03, 0.006), t0, g) for t0, g in zip(np.sort(rng.uniform(0, 1.9, 14)), rng.uniform(0.4, 1, 14))]), 0.35)

    # ------------------------------------------------------------- ambiente
    def olas(d):
        n = ruido(d)
        t = _t(d)
        env = (0.5 - 0.5 * np.cos(PI2 * t / (d / 2))) ** 1.5
        return _filtro(n, 150, 2500) * (0.25 + env) + 0.4 * _filtro(n, 2000, 7000) * env ** 3

    S["amb_playa"] = _norm(_bucle(olas(9.0), 300), 0.5)

    def gaviota():
        d = 0.45
        t = _t(d)
        f = 1500 - 500 * t / d + 60 * np.sin(PI2 * 25 * t)
        x = np.sin(PI2 * np.cumsum(f) / SR)
        x = x + 0.5 * np.sin(2 * PI2 * np.cumsum(f) / SR)
        return x * np.sin(np.pi * t / d)

    gv = np.zeros(int(SR * 2.0))
    for k in range(3):
        _poner(gv, gaviota(), 0.1 + 0.5 * k, 1 - 0.2 * k)
    S["gaviota"] = _norm(gv, 0.5)
    pu_ = olas(9.0) * 0.7
    _poner(pu_, _seno(98, 2.0) * np.sin(np.pi * _t(2.0) / 2.0) ** 2, 3.0, 0.5)   # sirena de barco lejana
    S["amb_puerto"] = _norm(_bucle(pu_, 300), 0.5)
    ciu = _filtro(ruido(8.0), 40, 350) + 0.3 * _filtro(ruido(8.0), 300, 1500) * (0.5 + 0.5 * _filtro(ruido(8.0), hi=0.7) * 20).clip(0, 2)
    S["amb_ciudad"] = _norm(_bucle(ciu, 300), 0.45)
    ind = _filtro(ruido(6.0), 40, 500) + 0.5 * _seno(50, 6.0) + 0.25 * _seno(100, 6.0) + 0.15 * _seno(150, 6.0)
    for t0 in (0.8, 2.9, 4.4):
        _poner(ind, sum(_seno(f, 0.5) * _decae(0.5, 0.08) for f in (520, 833, 1370)), t0, 0.35)
    S["amb_industrial"] = _norm(_bucle(ind, 300), 0.45)

    def pajaro():
        n = rng.integers(2, 6)
        out = np.zeros(int(SR * 0.9))
        f = rng.uniform(2800, 5200)
        for k in range(n):
            _poner(out, _barrido(f, f * rng.uniform(0.7, 1.4), 0.07) * np.sin(np.pi * _t(0.07) / 0.07), k * 0.13)
        return out

    par = 0.35 * _filtro(ruido(10.0), 300, 3000) * (0.6 + 0.4 * _filtro(ruido(10.0), hi=0.5) * 25).clip(0, 2)
    for _ in range(14):
        _poner(par, pajaro(), rng.uniform(0, 9.0), rng.uniform(0.2, 0.7))
    S["amb_parque"] = _norm(_bucle(par, 300), 0.45)
    S["pajaro"] = _norm(pajaro(), 0.4)
    res = 0.5 * _filtro(ruido(8.0), 40, 300)
    for _ in range(4):
        _poner(res, pajaro(), rng.uniform(0, 7.0), 0.25)
    S["amb_residencial"] = _norm(_bucle(res, 300), 0.35)
    tg = _t(6.0)
    gr = _seno(4400, 6.0) * (np.sin(PI2 * 32 * tg) > 0.3) * (np.sin(PI2 * 1.6 * tg) > -0.2)
    S["amb_noche"] = _norm(_bucle(gr + 0.3 * _filtro(ruido(6.0), 40, 250), 200), 0.3)
    S["lluvia"] = _norm(_bucle(_filtro(ruido(5.0), 1200, 9000) + 0.5 * _filtro(ruido(5.0), 200, 900), 300), 0.4)
    trab = _filtro(ruido(3.5), 25, 180) * _decae(3.5, 0.9, 0.05) * (1 + 0.5 * _filtro(ruido(3.5), hi=6) * 8)
    S["trueno"] = _norm(trab, 0.9)
    lad = np.zeros(int(SR * 1.0))
    for k in range(3):
        _poner(lad, vocal(520, 300, 0.12, (800, 1600), 0.08), k * 0.28)
    S["ladrido"] = _norm(lad, 0.5)
    mart = np.zeros(int(SR * 1.2))
    for k in range(4):
        _poner(mart, (sum(_seno(f, 0.2) for f in (640, 1130, 2210)) + _filtro(ruido(0.2), 800, 4000)) * _decae(0.2, 0.03), k * 0.28)
    S["martillo"] = _norm(mart, 0.5)
    S["claxon_lejano"] = _norm(_filtro(S["claxon"].astype(np.float64), hi=900), 0.25)
    mu = _filtro(ruido(6.0), 250, 1300) * (0.4 + np.abs(_filtro(ruido(6.0), hi=5)) * 7)
    S["multitud"] = _norm(_bucle(mu, 300), 0.35)
    # el pabellón de los combates: público murmurando bajo un techo alto, con su reverberación y algún grito suelto.
    # Con su propia semilla, para no cambiar los sonidos que vienen después.
    rp = np.random.default_rng(77)
    dp = 8.0
    mp = _filtro(rp.standard_normal(int(SR * dp)), 220, 1500) * (0.45 + np.abs(_filtro(rp.standard_normal(int(SR * dp)), hi=4)) * 6)
    for t0 in (1.3, 4.6, 6.2):                                   # «¡dale!» lejano: un golpe de voces que sube y baja
        grito = _filtro(rp.standard_normal(int(SR * 0.6)), 400, 2200) * np.sin(np.pi * np.linspace(0, 1, int(SR * 0.6))) ** 2
        _poner(mp, grito, t0, 1.6)
    ir = rp.standard_normal(int(SR * 1.4)) * np.exp(-np.linspace(0, 1.4, int(SR * 1.4)) / 0.45)      # la sala: casi un segundo y medio de cola
    ir[0] = 6.0
    sala = np.fft.irfft(np.fft.rfft(mp, len(mp) + len(ir)) * np.fft.rfft(ir, len(mp) + len(ir)))[:len(mp)]
    S["amb_pabellon"] = _norm(_bucle(_filtro(sala, 120, 4200), 400), 0.3)
    S["viento_playa"] = S["amb_playa"]

    # ------------------------------------------------- ampliación: mar y más
    mar = olas(10.0) * 0.8 + 0.5 * _filtro(ruido(10.0), 60, 400) * (0.6 + 0.4 * np.sin(PI2 * _t(10.0) / 5.0))
    S["amb_mar"] = _norm(_bucle(mar, 300), 0.5)
    campo = 0.3 * _filtro(ruido(10.0), 200, 1500) * (0.5 + 0.5 * _filtro(ruido(10.0), hi=0.4) * 25).clip(0, 2)
    for _ in range(8):
        _poner(campo, pajaro(), rng.uniform(0, 9.0), rng.uniform(0.2, 0.6))
    for t0 in (2.0, 6.5):
        _poner(campo, _nota(660, 0.5, 0.2, (1, 0.6, 0.5, 0.3)), t0, 0.25)      # cencerro lejano
    S["amb_campo"] = _norm(_bucle(campo, 300), 0.4)
    t1 = _t(1.0)
    lan = sum(np.sin(PI2 * 110 * k * t1 + rng.uniform(0, PI2)) / k ** 0.6 for k in range(1, 14))
    lan = lan * (1 + 0.4 * np.sin(PI2 * 55 * t1)) + 1.2 * _filtro(ruido(1.0), 800, 5000)
    S["motor_lancha"] = _norm(np.tanh(lan * 0.8), 0.5)
    bar_ = sum(np.sin(PI2 * 32 * k * t1 + rng.uniform(0, PI2)) / k for k in range(1, 10))
    bar_ = bar_ * (1 + 0.7 * np.sign(np.sin(PI2 * 8 * t1))) + 0.8 * _filtro(ruido(1.0), 200, 2000)
    S["motor_barco"] = _norm(np.tanh(bar_), 0.55)
    S["motor_tractor"] = _norm(np.tanh(bar_ * 1.5 + 0.5 * _filtro(ruido(1.0), 100, 900)), 0.55)
    sal = _filtro(ruido(0.9), 600, 7000) * _decae(0.9, 0.25, 0.02)
    S["salpicadura"] = _norm(sal, 0.5)
    S["pesca_lanzar"] = _norm(np.concatenate([_filtro(ruido(0.35), 2500, 9000) * np.sin(np.pi * _t(0.35) / 0.35) ** 2, np.zeros(int(SR * 0.4)), sal[: int(SR * 0.4)] * 0.5]), 0.45)
    pica = np.zeros(int(SR * 0.6))
    for k in range(5):
        _poner(pica, _nota(1760, 0.08, 0.02, (1, 0.5)), k * 0.09)
    _poner(pica, sal[: int(SR * 0.3)], 0.1, 0.4)
    S["pez_pica"] = _norm(pica, 0.6)
    car = np.zeros(int(SR * 0.9))
    for k in range(22):
        _poner(car, _filtro(ruido(0.012), 2500, 8000) * _decae(0.012, 0.004), k * 0.04)
    S["carrete"] = _norm(car, 0.4)
    boya = np.zeros(int(SR * 3.5))
    _poner(boya, sum(a * _seno(f, 2.5) * _decae(2.5, tau) for f, a, tau in ((520, 1, 0.9), (1043, 0.5, 0.5), (1570, 0.3, 0.3))), 0.2)
    _poner(boya, sal * 0.25, 2.0)
    S["lugar_boya"] = _norm(boya, 0.5)
    emb = _filtro(ruido(4.0), 300, 2500) * (0.3 + 0.7 * (0.5 - 0.5 * np.cos(PI2 * _t(4.0) / 2.0)) ** 2)
    for t0 in (0.9, 2.8):
        _poner(emb, _barrido(180, 240, 0.5, "sierra") * np.sin(np.pi * _t(0.5) / 0.5) * 0.25, t0)     # crujido de amarras
    S["lugar_embarcadero"] = _norm(_bucle(_filtro(emb, hi=3500), 200), 0.45)
    gim = np.zeros(int(SR * 3.0))
    for t0 in (0.2, 1.6):
        _poner(gim, (sum(_seno(f, 0.4) for f in (310, 742, 1190, 2030)) + _filtro(ruido(0.4), 500, 3000)) * _decae(0.4, 0.07), t0)
        _poner(gim, _filtro(ruido(0.5), 300, 1500) * np.sin(np.pi * _t(0.5) / 0.5) ** 2 * 0.3, t0 + 0.6)
    S["lugar_gimnasio"] = _norm(gim, 0.45)
    cine = _filtro(ruido(2.0), 1500, 6000) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 24 * _t(2.0)))) * 0.5
    _poner(cine, _sec([523, 659, 784], 0.15, 0.5, 0.25), 0.3, 0.6)
    S["lugar_cine"] = _norm(_bucle(cine, 80), 0.35)
    est = np.zeros(int(SR * 4.0))
    _poner(est, _bordes(_filtro(ruido(0.8), 1500, 9000) * np.linspace(1, 0.1, int(SR * 0.8)), 10), 0.2)       # frenos de aire
    _poner(est, _sec([659, 523], 0.3, 0.6, 0.3), 1.6, 0.6)                                                    # megafonía
    S["lugar_estacion"] = _norm(est, 0.4)
    sal_ = np.zeros(int(SR * 3.0))
    for k in range(3):
        _poner(sal_, _bordes(_filtro(ruido(0.7), 150, 1200) * np.sin(np.pi * _t(0.7) / 0.7) ** 2, 20), 0.2 + k * 0.9, 1 - k * 0.2)   # coches pasando
    S["lugar_salida"] = _norm(sal_, 0.4)
    S["disparo_fusil"] = disparo(350, 6500, 0.3, 0.045, 0.7)
    S["disparo_silenciado"] = _norm(_filtro(ruido(0.12), 900, 3500) * _decae(0.12, 0.02, 0.001), 0.35)
    S["lanzar"] = _norm(_filtro(ruido(0.3), 700, 3500) * np.sin(np.pi * _t(0.3) / 0.3) ** 2, 0.4)
    coh = _filtro(ruido(1.0), 300, 5000) * np.linspace(1, 0.2, SR) + 0.6 * _barrido(900, 250, 1.0, "sierra") * np.linspace(1, 0, SR)
    S["cohete"] = _norm(_bordes(coh, 15), 0.7)
    ta = _t(1.6)
    S["sirena_ambulancia"] = _norm(_filtro(np.where((ta % 0.8) < 0.4, np.sign(np.sin(PI2 * 960 * ta)), np.sign(np.sin(PI2 * 770 * ta))), hi=3500), 0.5)
    dad = np.zeros(int(SR * 0.8))
    for k in range(7):
        _poner(dad, _filtro(ruido(0.03), 1200, 5000) * _decae(0.03, 0.008), 0.05 + k * 0.09 + rng.uniform(0, 0.03), rng.uniform(0.5, 1))
    S["dados"] = _norm(dad, 0.5)
    S["caja"] = _norm(np.concatenate([_nota(1568, 0.12, 0.04, (1, 0.4)), S["dinero"].astype(np.float64)]), 0.5)
    S["sirena_barco"] = _norm(_bordes(_filtro(_sierra(98, 1.8) + _sierra(147, 1.8), hi=900), 80), 0.6)

    # ----------------------------------------------- segunda ampliación
    th = _t(1.0)
    pala = (0.5 + 0.5 * np.sign(np.sin(PI2 * 12 * th))) * np.exp(-((th * 12) % 1.0) * 4)
    heli = _filtro(ruido(1.0), 60, 900) * pala * 2.5 + 0.5 * sum(np.sin(PI2 * 180 * k * th + rng.uniform(0, PI2)) / k for k in range(1, 8))
    S["motor_helicoptero"] = _norm(np.tanh(heli), 0.6)
    bici = np.zeros(SR)
    for k in range(10):
        _poner(bici, _filtro(ruido(0.02), 3000, 9000) * _decae(0.02, 0.005), k * 0.1, 0.8)
    bici += 0.25 * _filtro(ruido(1.0), 500, 2500)
    S["motor_bici"] = _norm(bici, 0.3)
    S["claxon_bici"] = _norm(_sec([2637, 2637], 0.12, 0.3, 0.15, (1, 0.5, 0.3)), 0.5)
    S["claxon_helados"] = _norm(_sec([784, 988, 1175, 988, 784, 988, 1175, 1568], 0.14, 0.35, 0.18, (1, 0.6, 0.2)), 0.5)
    S["diana"] = _norm(_nota(1175, 0.25, 0.08, (1, 0.5, 0.3)), 0.7)
    dok = _nota(1760, 0.2, 0.06)
    _poner(dok, _filtro(ruido(0.08), 1500, 6000) * _decae(0.08, 0.02), 0.0)
    S["diana_ok"] = _norm(dok, 0.6)
    rul = np.zeros(int(SR * 2.4))
    tt = 0.05
    pos = 0.0
    while pos < 2.2:
        _poner(rul, _filtro(ruido(0.015), 2000, 7000) * _decae(0.015, 0.004), pos)
        pos += tt
        tt *= 1.12
    S["ruleta"] = _norm(rul, 0.5)
    # jugar con amigos
    S["amigo_entra"] = _norm(_sec([523, 784, 1047], 0.09, 0.5, 0.25, (1, 0.4)), 0.5)
    S["amigo_sale"] = _norm(_sec([1047, 784, 523], 0.09, 0.5, 0.25, (1, 0.4)), 0.45)
    S["chat"] = _norm(_sec([1568, 2093], 0.045, 0.2, 0.09, (1, 0.6)), 0.45)
    S["logro"] = _norm(_sec([784, 1047, 1319, 1568, 2093], 0.09, 0.6, 0.3, (1, 0.5, 0.25)), 0.6)
    S["nivel"] = _norm(_sec([659, 880, 1319], 0.1, 0.5, 0.25, (1, 0.4)), 0.5)
    S["campana_ring"] = _norm(sum(a * _seno(f, 1.2) * _decae(1.2, tau) for f, a, tau in ((1320, 1, 0.4), (2650, 0.5, 0.25), (3990, 0.3, 0.15))), 0.6)
    # combustible
    gor = _filtro(np.random.default_rng(31).standard_normal(int(SR * 1.6)), lo=180, hi=1400)
    S["repostar"] = _norm(_bordes(gor * (0.55 + 0.45 * np.sin(PI2 * 7 * _t(1.6))) * (0.7 + 0.3 * np.sin(PI2 * 1.3 * _t(1.6))), 40), 0.5)
    S["reserva"] = _norm(_sec([392, 392, 330], 0.16, 0.14, 0.09, (1, 0.5)), 0.5)
    tos = np.concatenate([_filtro(_sierra(70 - 9 * k, 0.16) * _decae(0.16, 0.07), hi=900) for k in range(4)] + [np.zeros(int(SR * 0.05))])
    S["motor_seco"] = _norm(tos, 0.55)
    # averías y multas
    aire = _filtro(np.random.default_rng(47).standard_normal(int(SR * 1.3)), lo=1500, hi=7000) * _decae(1.3, 0.45)
    pum = _filtro(np.random.default_rng(48).standard_normal(int(SR * 0.12)), hi=900) * _decae(0.12, 0.03)
    pin = np.zeros(int(SR * 1.3))
    _poner(pin, pum, 0.0, 1.0)
    _poner(pin, aire[:len(pin) - int(SR * 0.05)], 0.05, 0.6)
    S["pinchazo"] = _norm(pin, 0.6)
    pito = _seno(2350, 0.32) * (0.6 + 0.4 * np.sign(np.sin(PI2 * 38 * _t(0.32)))) * _decae(0.32, 0.5)
    S["multa"] = _norm(np.concatenate([_bordes(pito, 8), np.zeros(int(SR * 0.12)), _bordes(pito, 8)]), 0.5)
    trago = np.concatenate([_barrido(260 + 40 * k, 520 + 60 * k, 0.11) * _decae(0.11, 0.05) for k in range(3)])
    S["beber"] = _norm(_filtro(trago, hi=1800), 0.45)
    S["evento"] = _norm(_sec([988, 784, 988, 784], 0.11, 0.3, 0.12), 0.55)
    S["cursor_mapa"] = _norm(_seno(900, 0.04) * _decae(0.04, 0.015), 0.4)
    for k, f in enumerate((784, 587, 392, 494)):          # arriba, derecha, abajo, izquierda
        S[f"simon_{k}"] = _norm(_nota(f, 0.45, 0.18, (1, 0.5, 0.25, 0.12)), 0.7)
    prot = np.zeros(int(SR * 4.0))
    _poner(prot, S["ladrido"].astype(np.float64), 0.2, 1.0)
    _poner(prot, np.interp(np.arange(0, len(S["ladrido"]), 1.35), np.arange(len(S["ladrido"])), S["ladrido"].astype(np.float64)), 2.1, 0.7)
    S["lugar_protectora"] = _norm(prot, 0.4)

    # ------------------------------------------- vida social, sustancias y negocios
    club = np.zeros(int(SR * 2.0))
    for k in range(4):
        _poner(club, _barrido(110, 42, 0.22) * _decae(0.22, 0.07), k * 0.5)
        _poner(club, _filtro(ruido(0.05), 5000, 11000) * _decae(0.05, 0.012), k * 0.5 + 0.25, 0.3)
    club = _filtro(club, hi=700) + 0.25 * _filtro(ruido(2.0), 400, 1800) * (0.5 + np.abs(_filtro(ruido(2.0), hi=4)) * 6)
    _poner(club, _nota(2350, 0.25, 0.05, (1, 0.6)), 1.3, 0.25)          # copas que chocan
    S["lugar_club"] = _norm(_bucle(club, 40), 0.5)
    prov = np.zeros(int(SR * 3.5))
    for k in range(2):                                                    # «pst, pst»
        _poner(prov, _filtro(ruido(0.16), 3500, 9000) * np.sin(np.pi * _t(0.16) / 0.16) ** 2, 0.2 + k * 0.32, 0.8)
    _poner(prov, (sum(_seno(f, 0.5) for f in (190, 430, 910)) + _filtro(ruido(0.5), 300, 2500)) * _decae(0.5, 0.1), 1.6, 0.5)   # persiana metálica
    S["lugar_proveedor"] = _norm(prov, 0.4)
    S["afinidad_sube"] = _norm(_sec([523, 659, 784], 0.13, 0.7, 0.35, (1, 0.6, 0.3, 0.15)), 0.5)
    S["afinidad_baja"] = _norm(_sec([440, 415, 349], 0.2, 0.8, 0.4, (1, 0.5, 0.25)), 0.5)
    cor = np.zeros(int(SR * 1.6))
    for k, t0 in enumerate((0.0, 0.22, 0.75, 0.97)):
        _poner(cor, _seno(62, 0.16) * _decae(0.16, 0.05), t0, 1.0 if k % 2 == 0 else 0.7)
    _poner(cor, _sec([784, 988, 1175, 1568], 0.1, 0.6, 0.3, (1, 0.4)), 0.3, 0.35)
    S["pareja"] = _norm(cor, 0.6)
    S["ruptura"] = _norm(_sec([392, 370, 311, 262, 196], 0.28, 1.2, 0.6, (1, 0.6, 0.3)), 0.55)
    S["noche_juntos"] = _norm(_sec([392, 494, 587, 784, 587, 784, 988], 0.22, 1.4, 0.8, (1, 0.5, 0.25)), 0.45)
    S["animo_sube"] = _norm(_sec([659, 880], 0.09, 0.3, 0.14, (1, 0.3)), 0.4)
    S["animo_baja"] = _norm(_sec([440, 330], 0.11, 0.35, 0.16, (1, 0.5)), 0.4)
    S["fama"] = _norm(_sec([330, 440, 554, 659], 0.07, 0.4, 0.2, (1, 0.7, 0.5, 0.3)), 0.5)
    copa = np.zeros(int(SR * 1.3))
    _poner(copa, _filtro(ruido(0.6), 1500, 6000) * np.linspace(0.2, 1, int(SR * 0.6)) * (0.6 + 0.4 * np.sin(PI2 * 14 * _t(0.6))), 0.0, 0.6)   # servir
    _poner(copa, _nota(2100, 0.4, 0.12, (1, 0.5, 0.2)) + _nota(2790, 0.4, 0.1, (0.6, 0.2)), 0.75)                                            # brindis
    S["tomar_copa"] = _norm(copa, 0.5)
    hum = np.zeros(int(SR * 1.6))
    _poner(hum, _filtro(ruido(0.05), 2500, 9000) * _decae(0.05, 0.01), 0.0)                                       # mechero
    _poner(hum, _filtro(ruido(0.7), 700, 3000) * np.sin(np.pi * _t(0.7) / 0.7) ** 2, 0.25, 0.7)                   # calada
    _poner(hum, _filtro(ruido(0.5), 300, 1500) * np.sin(np.pi * _t(0.5) / 0.5) ** 2, 1.05, 0.5)                   # soltar el humo
    S["tomar_hierba"] = _norm(hum, 0.45)
    past = np.zeros(int(SR * 0.9))
    _poner(past, _filtro(ruido(0.04), 3000, 9000) * _decae(0.04, 0.008), 0.0)                                     # blíster
    _poner(past, _filtro(ruido(0.04), 3000, 9000) * _decae(0.04, 0.008), 0.12, 0.7)
    _poner(past, _barrido(260, 150, 0.18) * _decae(0.18, 0.06), 0.5, 0.9)                                         # tragar
    S["tomar_pastillas"] = _norm(past, 0.5)
    esn = np.zeros(int(SR * 1.0))
    for k in range(3):
        _poner(esn, _filtro(ruido(0.02), 2000, 7000) * _decae(0.02, 0.005), k * 0.09, 0.6)                        # picar con una tarjeta
    _poner(esn, _filtro(ruido(0.4), 1800, 8000) * np.linspace(0.3, 1, int(SR * 0.4)) ** 2, 0.45)                 # inspirar
    S["tomar_polvo"] = _norm(esn, 0.45)
    cri = np.zeros(int(SR * 1.5))
    _poner(cri, _filtro(ruido(0.05), 2500, 9000) * _decae(0.05, 0.01), 0.0)
    _poner(cri, _filtro(ruido(0.8), 2500, 9000) * (0.4 + 0.6 * np.abs(_filtro(ruido(0.8), hi=30)) * 4), 0.15, 0.5)   # crepitar
    _poner(cri, _filtro(ruido(0.4), 500, 2500) * np.sin(np.pi * _t(0.4) / 0.4) ** 2, 1.0, 0.6)
    S["tomar_cristal"] = _norm(cri, 0.45)
    S["bajon"] = _norm(_filtro(_barrido(330, 90, 1.6, "sierra"), hi=900) * np.sin(np.pi * _t(1.6) / 1.6), 0.5)
    tem = _seno(140, 1.2) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 11 * _t(1.2)))) * np.sin(np.pi * _t(1.2) / 1.2)
    S["abstinencia"] = _norm(tem + 0.3 * _filtro(ruido(1.2), 200, 900), 0.5)
    sob = np.zeros(int(SR * 3.2))
    for k, t0 in enumerate((0.0, 0.5, 1.15, 1.95)):
        _poner(sob, _seno(58, 0.18) * _decae(0.18, 0.06), t0, 1.0 - 0.15 * k)
    _poner(sob, _bordes(_seno(1000, 1.0), 20), 2.2, 0.35)                                                         # pitido continuo de monitor
    S["sobredosis"] = _norm(sob, 0.7)
    trato = np.zeros(int(SR * 0.9))
    for k in range(5):
        _poner(trato, _filtro(ruido(0.05), 1500, 6000) * _decae(0.05, 0.015), k * 0.09, 0.7)                      # contar billetes
    _poner(trato, _filtro(ruido(0.12), 400, 2000) * _decae(0.12, 0.04), 0.55, 0.8)                                # el paquete cambia de manos
    S["trato"] = _norm(trato, 0.5)
    S["rechazo"] = _norm(vocal(170, 120, 0.22, (500, 1300), 0.12), 0.4)
    plc = np.zeros(int(SR * 1.1))
    _poner(plc, _bordes(_filtro(ruido(0.25), 700, 2600, 6), 8), 0.0)                                             # emisora
    _poner(plc, _bordes(_seno(1700, 0.08), 4), 0.3, 0.6)
    _poner(plc, S["esposas"].astype(np.float64), 0.45, 0.7)
    S["paisano"] = _norm(plc, 0.5)
    S["precio_ganga"] = _norm(_sec([1319, 1047, 784], 0.07, 0.3, 0.12, (1, 0.3)), 0.4)
    S["precio_escasez"] = _norm(_sec([784, 1047, 1319], 0.07, 0.3, 0.12, (1, 0.3)), 0.4)
    S["perro_olfatea"] = _norm(np.concatenate([_filtro(ruido(0.09), 1500, 6000) * np.sin(np.pi * _t(0.09) / 0.09) for _ in range(4)]), 0.4)
    S["bolsa"] = _norm(_sec([988, 988, 1319], 0.08, 0.25, 0.08, (1, 0.5)), 0.4)
    S["territorio"] = _norm(_sec([196, 247, 294, 392, 494, 587], 0.11, 0.9, 0.5, (1, 0.8, 0.6, 0.4)), 0.65)
    S["cita"] = _norm(_sec([587, 740, 880, 740, 1175], 0.14, 0.6, 0.3, (1, 0.4, 0.2)), 0.45)
    S["regalo"] = _norm(_filtro(ruido(0.3), 2500, 9000) * np.sin(np.pi * _t(0.3) / 0.3) * 0.5, 0.35)

    # ------------------------------------------- puertas, horas del día y vida honrada
    pt = np.zeros(int(SR * 1.1))
    _poner(pt, _filtro(ruido(0.25), 150, 1200) * np.sin(np.pi * _t(0.25) / 0.25), 0.0, 0.7)            # la puerta se abre
    _poner(pt, _nota(1976, 0.5, 0.2, (1, 0.4)), 0.2, 0.8)                                              # campanilla
    _poner(pt, _nota(2349, 0.5, 0.2, (1, 0.4)), 0.33, 0.6)
    S["puerta_entrar"] = _norm(pt, 0.5)
    ps = np.zeros(int(SR * 0.7))
    _poner(ps, _nota(2349, 0.3, 0.1, (1, 0.4)), 0.0, 0.5)
    _poner(ps, _seno(105, 0.2) * _decae(0.2, 0.05) + 0.6 * _filtro(ruido(0.2), 300, 2000) * _decae(0.2, 0.03), 0.3)   # se cierra
    S["puerta_salir"] = _norm(ps, 0.5)
    cam2 = np.zeros(int(SR * 4.2))
    for k in range(3):
        _poner(cam2, sum(a * _seno(f, 2.2) * _decae(2.2, tau) for f, a, tau in ((262, 1, 0.9), (525, 0.6, 0.6), (790, 0.4, 0.4), (1050, 0.25, 0.25))), k * 1.0)
    S["campanadas"] = _norm(cam2, 0.45)
    ga = np.concatenate([vocal(600, 900, 0.18, (1100, 2200), 0.3), vocal(900, 950, 0.12, (1200, 2400), 0.3), vocal(950, 1100, 0.3, (1300, 2600), 0.4), vocal(1100, 500, 0.5, (1100, 2200), 0.3)])
    S["gallo"] = _norm(ga, 0.4)
    bu = np.zeros(int(SR * 1.6))
    for t0, d_ in ((0.0, 0.25), (0.4, 0.2), (0.7, 0.5)):
        _poner(bu, _seno(330, d_) * np.sin(np.pi * _t(d_) / d_) * (1 + 0.3 * _seno(6, d_)), t0)
    S["buho"] = _norm(bu, 0.35)
    S["agacharse"] = _norm(_filtro(ruido(0.25), 300, 2500) * np.linspace(1, 0.1, int(SR * 0.25)), 0.3)
    S["levantarse"] = _norm(_filtro(ruido(0.25), 300, 2500) * np.linspace(0.1, 1, int(SR * 0.25)), 0.3)
    hd = np.zeros(int(SR * 2.6))
    for k in range(3):
        _poner(hd, _bordes(_seno(1000, 0.09), 4), 0.2 + k * 0.8, 0.8)
    _poner(hd, _filtro(ruido(0.8), 300, 1500) * np.sin(np.pi * _t(0.8) / 0.8) ** 2 * 0.4, 1.4)        # una respiración
    S["hospital_despertar"] = _norm(hd, 0.45)
    ce = (sum(_seno(f, 0.9) for f in (160, 370, 910, 1730)) + 1.5 * _filtro(ruido(0.9), 150, 2500)) * _decae(0.9, 0.16, 0.001)
    S["celda"] = _norm(np.tanh(ce), 0.7)
    S["ascenso"] = _norm(_sec([392, 523, 659, 784, 1047], 0.12, 0.8, 0.45, (1, 0.7, 0.4, 0.2)), 0.6)
    S["diploma"] = _norm(_sec([523, 659, 784, 659, 784, 1047], 0.13, 0.6, 0.3, (1, 0.4, 0.2)), 0.5)
    don = np.zeros(int(SR * 0.9))
    for k in range(4):
        _poner(don, _nota(float(rng.uniform(2800, 4200)), 0.2, 0.05, (1, 0.5)), 0.05 + k * 0.13 + float(rng.uniform(0, 0.03)), 0.8)   # monedas
    S["donativo"] = _norm(don, 0.45)
    S["prestigio"] = _norm(_sec([659, 784, 988], 0.11, 0.5, 0.25, (1, 0.5, 0.25)), 0.45)
    S["jornada"] = _norm(np.concatenate([_filtro(_cuadrada(520, 0.5), hi=2500) * _decae(0.5, 0.6, 0.02), np.zeros(int(SR * 0.15)), S["pasan_horas"].astype(np.float64)]), 0.45)   # sirena de fábrica y pasan las horas
    of = np.zeros(int(SR * 3.0))
    for t0, g in zip(np.sort(rng.uniform(0, 2.2, 10)), rng.uniform(0.4, 1, 10)):
        _poner(of, _filtro(ruido(0.03), 1500, 5000) * _decae(0.03, 0.006), float(t0), float(g))        # teclado
    _poner(of, _bordes(_seno(880, 0.12), 5) + _bordes(_seno(1100, 0.12), 5), 2.5, 0.5)                 # turno siguiente
    S["lugar_empleo"] = _norm(of, 0.4)
    ac = np.zeros(int(SR * 3.5))
    _poner(ac, sum(a * _seno(f, 1.2) * _decae(1.2, 0.4) for f, a in ((1568, 1), (3140, 0.4))), 0.1)    # timbre de clase
    _poner(ac, _filtro(ruido(1.2), 300, 1400) * (0.4 + np.abs(_filtro(ruido(1.2), hi=6)) * 6) * 0.5, 1.6)   # murmullo
    S["lugar_academia"] = _norm(ac, 0.4)
    ong = np.zeros(int(SR * 3.0))
    for k in range(4):
        _poner(ong, _nota(float(rng.uniform(1500, 2600)), 0.25, 0.06, (1, 0.5)), 0.2 + k * 0.45, 0.7)   # platos y cubiertos
    _poner(ong, _filtro(ruido(1.5), 300, 1200) * 0.25, 1.2)
    S["lugar_ong"] = _norm(ong, 0.4)
    hp = np.zeros(int(SR * 3.0))
    _poner(hp, _filtro(ruido(1.6), 80, 700) * (0.5 + 0.5 * np.sign(np.sin(PI2 * 11 * _t(1.6)))) * np.sin(np.pi * _t(1.6) / 1.6) ** 2, 0.2)
    _poner(hp, _bordes(_seno(1100, 0.12), 6), 2.2, 0.5)
    S["lugar_helipuerto"] = _norm(hp, 0.45)
    pris = np.zeros(int(SR * 4.0))
    _poner(pris, (sum(_seno(f, 0.6) for f in (240, 610, 1390)) + _filtro(ruido(0.6), 300, 2500)) * _decae(0.6, 0.12), 0.3)      # reja
    _poner(pris, S["sirena_lejana"].astype(np.float64)[: int(SR * 1.2)], 2.2, 1.5)
    S["lugar_prision"] = _norm(pris, 0.45)
    mina = np.zeros(int(SR * 3.0))
    for t0 in (0.2, 0.9, 1.6):
        _poner(mina, (sum(_seno(f, 0.25) for f in (830, 1670, 2900)) + _filtro(ruido(0.25), 1000, 5000)) * _decae(0.25, 0.04), t0)   # pico
    _poner(mina, _filtro(ruido(0.8), 60, 500) * _decae(0.8, 0.3), 2.1, 0.8)                                                           # derrumbe
    S["lugar_mina"] = _norm(mina, 0.45)
    rio = _filtro(ruido(4.0), 500, 5000) * (0.7 + 0.3 * np.abs(_filtro(ruido(4.0), hi=10)) * 5)
    S["lugar_rio"] = _norm(_bucle(rio, 200), 0.4)
    mont = 0.5 * _filtro(ruido(10.0), 100, 900) * (0.4 + 0.6 * (0.5 - 0.5 * np.cos(PI2 * _t(10.0) / 5.0)))
    for _ in range(3):
        _poner(mont, pajaro(), rng.uniform(0, 9.0), 0.25)
    S["amb_montana"] = _norm(_bucle(mont, 300), 0.4)
    # ----------------------------------------------- tren, tranvía, avioneta y agua (versión 1.6.2)
    tt = _t(2.0)
    tren = _filtro(ruido(2.0), 30, 420) * (0.75 + 0.25 * np.sin(PI2 * 0.5 * tt))             # el rodar grave del vagón
    for t0 in (0.0, 0.16, 1.0, 1.16):                                                        # el traqueteo doble de las juntas del raíl
        _poner(tren, _filtro(ruido(0.07), 300, 2600) * _decae(0.07, 0.018), t0, 3.2)
    S["tren"] = _norm(tren, 0.5)
    ts = _t(1.6)
    silbato = sum(np.sin(PI2 * f * ts * (1.0 - 0.012 * np.exp(-ts * 5))) for f in (370.0, 466.0, 554.0)) + 0.25 * _filtro(ruido(1.6), 800, 5000)
    S["tren_silbato"] = _norm(silbato * np.minimum(1.0, ts / 0.06) * np.minimum(1.0, (1.6 - ts) / 0.35), 0.45)
    tv = _t(2.0)
    tranvia = 0.5 * np.sin(PI2 * 110 * tv) * (1 + 0.3 * np.sin(PI2 * 220 * tv)) + 0.8 * _filtro(ruido(2.0), 120, 1500) * (0.8 + 0.2 * np.sin(PI2 * 1.0 * tv))
    for t0 in (0.5, 1.5):
        _poner(tranvia, _filtro(ruido(0.05), 500, 3500) * _decae(0.05, 0.012), t0, 2.0)
    S["tranvia"] = _norm(tranvia, 0.45)
    camp = np.zeros(int(SR * 0.9))
    for t0 in (0.0, 0.32):
        _poner(camp, sum(np.sin(PI2 * f * _t(0.5)) * a for f, a in ((1568.0, 1.0), (2093.0, 0.5), (3136.0, 0.25))) * _decae(0.5, 0.16), t0)
    S["tranvia_campana"] = _norm(camp, 0.45)
    ta = _t(1.0)
    helice = np.tanh(2.2 * sum(np.sin(PI2 * 92 * k * ta + rng.uniform(0, PI2)) / k for k in range(1, 10))) * (0.75 + 0.25 * np.sin(PI2 * 46 * ta))
    S["motor_avioneta"] = _norm(helice + 0.35 * _filtro(ruido(1.0), 400, 3000), 0.55)
    tb = _t(3.0)
    fondo_agua = _filtro(ruido(3.0), 20, 260) * (0.7 + 0.3 * np.sin(PI2 * (1 / 3.0) * tb))    # el rumor sordo de estar bajo el agua
    for t0 in rng.uniform(0.1, 2.7, 9):                                                      # burbujas que suben
        d_ = float(rng.uniform(0.05, 0.12))
        _poner(fondo_agua, _barrido(float(rng.uniform(350, 700)), float(rng.uniform(900, 1600)), d_) * _decae(d_, d_ / 3), float(t0), 0.5)
    S["bajo_agua"] = _norm(fondo_agua, 0.5)
    braz = _filtro(ruido(0.45), 250, 5000) * np.sin(np.pi * _t(0.45) / 0.45) ** 2 + 0.5 * _filtro(ruido(0.45), 80, 500) * _decae(0.45, 0.12)
    S["brazada"] = _norm(braz, 0.45)
    # ----------------------------------------------- paradas, estaciones y aeropuerto (versión 1.6.2)
    par = np.zeros(int(SR * 2.4))                                # parada de tranvía: dos toques de campana y silencio
    for t0 in (0.0, 0.28):
        _poner(par, sum(np.sin(PI2 * f * _t(0.45)) * a for f, a in ((1319.0, 1.0), (1976.0, 0.4))) * _decae(0.45, 0.14), t0)
    S["lugar_tranvia"] = _norm(par, 0.35)
    est = np.zeros(int(SR * 2.4))                                # estación de tren: cuatro resoplidos de locomotora
    for k in range(4):
        _poner(est, _filtro(ruido(0.22), 150, 1800) * _decae(0.22, 0.07, 0.02), 0.1 + 0.3 * k, 1.0 - 0.12 * k)
    S["lugar_tren"] = _norm(est, 0.35)
    aer = np.zeros(int(SR * 3.0))                                # aeropuerto: el aviso de megafonía, tres notas que bajan
    for k, f in enumerate((880.0, 698.5, 587.3)):
        _poner(aer, (np.sin(PI2 * f * _t(0.6)) + 0.3 * np.sin(PI2 * 2 * f * _t(0.6))) * _decae(0.6, 0.25), 0.1 + 0.42 * k)
    S["lugar_aeropuerto"] = _norm(aer, 0.35)
    tc = _t(3.0)
    cabina = _filtro(ruido(3.0), 60, 900) * (0.85 + 0.15 * np.sin(PI2 * (1 / 3.0) * tc)) + 0.25 * np.sin(PI2 * 120 * tc) + 0.15 * np.sin(PI2 * 240 * tc)
    S["avion"] = _norm(cabina, 0.5)
    td = _t(4.0)
    subida = td / 4.0
    desp = _filtro(ruido(4.0), 80, 3500) * (0.25 + 0.75 * subida) + 0.5 * np.sin(PI2 * np.cumsum(90 + 260 * subida) / SR) * subida
    S["avion_despegue"] = _norm(desp * np.minimum(1.0, td / 0.3) * np.minimum(1.0, (4.0 - td) / 0.5), 0.55)
    for pie, f0 in ((0, 2300.0), (1, 2050.0)):                   # pisar las vías: el raíl suena a metal, y debajo cruje la grava
        tp = _t(0.2)
        rail = (np.sin(PI2 * f0 * tp) + 0.5 * np.sin(PI2 * f0 * 1.52 * tp)) * _decae(0.2, 0.035, 0.001)
        S[f"paso_via{pie}"] = _norm(rail + 0.8 * _filtro(ruido(0.2), 900, 5000) * _decae(0.2, 0.05), 0.4)
    # ----------------------------------------------- armas nuevas (versión 1.7.1): cada una, su sonido
    S["disparo_rafaga"] = disparo(450, 5600, 0.16, 0.024, 0.45)               # pistola de ráfagas: seco y muy corto, para que se repita deprisa
    caza = np.zeros(int(SR * 1.1))                                            # escopeta de corredera: un estampido grave y, detrás, la corredera: atrás y adelante
    _poner(caza, disparo(90, 2400, 0.6, 0.13, 1.4), 0.0)
    _poner(caza, _filtro(ruido(0.09), 700, 3800) * _decae(0.09, 0.03), 0.66, 0.4)
    _poner(caza, _filtro(ruido(0.08), 1000, 5200) * _decae(0.08, 0.022), 0.86, 0.45)
    S["disparo_corredera"] = _norm(caza, 0.95)
    pal = np.zeros(int(SR * 1.0))                                             # rifle de palanca: el disparo y, detrás, la palanca: dos chasquidos de metal
    _poner(pal, disparo(220, 5200, 0.5, 0.085, 0.9), 0.0)
    _poner(pal, _filtro(ruido(0.05), 1800, 7000) * _decae(0.05, 0.012), 0.55, 0.35)
    _poner(pal, _filtro(ruido(0.06), 1200, 5000) * _decae(0.06, 0.015), 0.72, 0.4)
    S["disparo_palanca"] = _norm(pal, 0.95)
    S["disparo_semiautomatico"] = disparo(280, 6800, 0.42, 0.06, 0.75)        # fusil semiautomático: entre la carabina y el fusil de asalto
    ha = np.zeros(int(SR * 0.42))                                             # hacha: el silbido del arco y el golpe sordo del filo
    _poner(ha, _filtro(ruido(0.16), 500, 2600) * np.sin(np.pi * _t(0.16) / 0.16) ** 2, 0.0, 0.5)
    _poner(ha, _filtro(ruido(0.2), 50, 650) * _decae(0.2, 0.05) + _seno(70, 0.2) * _decae(0.2, 0.06), 0.15)
    _poner(ha, _filtro(ruido(0.05), 2500, 8000) * _decae(0.05, 0.01), 0.15, 0.4)
    S["hacha"] = _norm(ha, 0.8)
    lg = np.zeros(int(SR * 0.6))                                              # lanzagranadas: un «pum» hueco, de tubo, y el siseo de la granada al salir
    _poner(lg, (_barrido(280, 80, 0.22) + 0.6 * _filtro(ruido(0.22), 150, 1500)) * _decae(0.22, 0.05, 0.002), 0.0)
    _poner(lg, _filtro(ruido(0.4), 1500, 6000) * _decae(0.4, 0.12, 0.03), 0.08, 0.25)
    S["lanzagranadas"] = _norm(np.tanh(lg * 2.0), 0.9)
    # ----------------------------------------------- la calle (versión 1.7.1): voces de hombre y de mujer, botín y helicóptero
    S["grito_hombre"] = _norm(np.concatenate([vocal(210, 330, 0.18, (700, 1300), 0.4), vocal(330, 170, 0.45, (700, 1300), 0.28)]), 0.55)      # un grito grave, de susto
    S["grito_mujer"] = _norm(np.concatenate([vocal(520, 900, 0.22, (1000, 2300), 0.4), vocal(900, 560, 0.5, (1000, 2300), 0.3)]), 0.55)      # el mismo susto, agudo
    S["dolor_mujer"] = _norm(vocal(330, 230, 0.3, (950, 1900), 0.15), 0.6)
    # el pánico en la calle (versión 1.7.3): varios gritos de hombres y mujeres a destiempo, sobre un tropel de pasos y voces
    pa = np.zeros(int(SR * 2.2))
    _poner(pa, _filtro(ruido(2.2), 250, 2200) * (0.25 + 0.2 * np.abs(_seno(5.5, 2.2))) * np.minimum(1.0, _t(2.2) / 0.2) * _decae(2.2, 1.6, 0.05), 0.0, 0.5)
    for t0, f0, f1, f2, form, g in ((0.0, 520, 950, 600, (1000, 2300), 0.9), (0.18, 230, 340, 180, (700, 1300), 0.8),
                                    (0.45, 640, 1050, 700, (1100, 2500), 0.7), (0.7, 280, 380, 200, (750, 1400), 0.6),
                                    (1.0, 580, 900, 520, (1000, 2300), 0.5), (1.3, 250, 320, 190, (700, 1300), 0.4)):
        _poner(pa, np.concatenate([vocal(f0, f1, 0.18, form, 0.4), vocal(f1, f2, 0.4, form, 0.28)]), t0, g)
    S["panico"] = _norm(pa, 0.6)                                                               # la queja de una mujer al recibir un golpe
    rm = np.zeros(int(SR * 0.5))                                 # recoger munición: el cargador que entra y el cerrojo, dos golpes de metal
    _poner(rm, _filtro(ruido(0.07), 900, 4500) * _decae(0.07, 0.02), 0.0, 0.8)
    _poner(rm, (_seno(1900, 0.05) + _filtro(ruido(0.05), 2500, 8000)) * _decae(0.05, 0.012), 0.16)
    _poner(rm, _filtro(ruido(0.09), 500, 3000) * _decae(0.09, 0.025), 0.3, 0.9)
    S["recoger_municion"] = _norm(rm, 0.5)
    tp = _t(2.0)                                                 # helicóptero de la policía: más grande que el civil; palas lentas y graves, y la turbina silbando encima
    pala = (0.5 + 0.5 * np.sign(np.sin(PI2 * 9 * tp))) * np.exp(-((tp * 9) % 1.0) * 3.2)
    helip = _filtro(ruido(2.0), 40, 600) * pala * 3.0 + 0.35 * sum(np.sin(PI2 * 117 * k * tp + rng.uniform(0, PI2)) / k for k in range(1, 6)) \
        + 0.12 * _filtro(ruido(2.0), 2600, 5200)
    S["helicoptero_policia"] = _norm(np.tanh(helip), 0.6)
    mg = np.zeros(int(SR * 1.1))                                 # megáfono: el acople al abrirse y dos sílabas de voz metálica, sin palabras: lo que dice lo dice el lector
    _poner(mg, _barrido(2400, 3100, 0.16) * _decae(0.16, 0.07, 0.02), 0.0, 0.5)
    for t0, f0, f1 in ((0.24, 190, 150), (0.62, 170, 120)):
        _poner(mg, _filtro(np.tanh(3.0 * vocal(f0, f1, 0.32, (800, 1700), 0.2)), 500, 2800), t0)
    S["megafono"] = _norm(mg, 0.55)
    # ----------------------------------------------- en casa y de servicio (versión 1.7.1): el timbre y la emisora de la policía
    tb = np.zeros(int(SR * 1.3))                                 # timbre de casa: «din, don», dos notas con su cola
    for t0, f in ((0.0, 659.3), (0.42, 523.3)):
        tt = _t(0.85)
        _poner(tb, (np.sin(PI2 * f * tt) + 0.35 * np.sin(PI2 * 2 * f * tt) + 0.12 * np.sin(PI2 * 3.01 * f * tt)) * _decae(0.85, 0.28), t0)
    S["timbre"] = _norm(tb, 0.5)
    em = np.zeros(int(SR * 0.75))                                # emisora de la policía: el chasquido al abrirse el canal, dos pitidos y el soplido de fondo
    _poner(em, _filtro(ruido(0.09), 400, 3200) * _decae(0.09, 0.03), 0.0, 0.9)
    _poner(em, _seno(1250, 0.09) * np.sin(np.pi * _t(0.09) / 0.09), 0.14, 0.7)
    _poner(em, _seno(930, 0.11) * np.sin(np.pi * _t(0.11) / 0.11), 0.27, 0.7)
    _poner(em, _filtro(ruido(0.3), 600, 2600) * _decae(0.3, 0.12, 0.02), 0.4, 0.3)
    S["emisora"] = _norm(em, 0.45)
    # ----------------------------------------------- la compra y la cocina (versión 1.7.1): la cesta, la nevera, picar, freír, hervir y el plato en la mesa
    ce = np.zeros(int(SR * 0.4))                                 # un producto que cae en la cesta: el golpe sordo y el alambre que tiembla
    _poner(ce, _filtro(ruido(0.09), 120, 900) * _decae(0.09, 0.03), 0.0)
    for t0, f0 in ((0.03, 2300), (0.07, 3100), (0.12, 2700)):
        _poner(ce, _seno(f0, 0.14) * _decae(0.14, 0.035), t0, 0.22)
    S["cesta"] = _norm(ce, 0.45)
    nv = np.zeros(int(SR * 1.0))                                 # la nevera: la goma de la puerta que se despega, y el zumbido del motor mientras está abierta
    _poner(nv, _filtro(ruido(0.07), 200, 1800) * _decae(0.07, 0.02), 0.0, 0.9)
    _poner(nv, _filtro(ruido(0.12), 60, 400) * _decae(0.12, 0.05), 0.05, 0.7)
    tn = _t(0.8)
    _poner(nv, (np.sin(PI2 * 100 * tn) + 0.5 * np.sin(PI2 * 200 * tn) + 0.2 * np.sin(PI2 * 300 * tn)) * np.minimum(1.0, tn / 0.1) * np.minimum(1.0, (0.8 - tn) / 0.3), 0.15, 0.35)
    S["nevera"] = _norm(nv, 0.45)
    ct = np.zeros(int(SR * 1.5))                                 # picar en la tabla: seis golpes de cuchillo, cada vez más seguidos
    for k, t0 in enumerate((0.0, 0.3, 0.56, 0.78, 0.97, 1.14)):
        _poner(ct, _filtro(ruido(0.05), 900, 6000) * _decae(0.05, 0.008), t0, 0.7)             # el filo
        _poner(ct, _seno(190 + 12 * (k % 2), 0.12) * _decae(0.12, 0.03), t0 + 0.004)           # la madera
    S["cocina_cortar"] = _norm(ct, 0.5)
    fr = _filtro(ruido(2.4), 2500, 9000) * 0.5                   # freír: el aceite chisporroteando, con sus saltos
    tf = _t(2.4)
    fr = fr * (0.55 + 0.45 * np.abs(_filtro(ruido(2.4), hi=14))) * np.minimum(1.0, tf / 0.15) * np.minimum(1.0, (2.4 - tf) / 0.5)
    for _ in range(26):
        _poner(fr, _filtro(ruido(0.012), 3000, 10000) * _decae(0.012, 0.003), float(rng.uniform(0.1, 2.1)), float(rng.uniform(0.6, 1.6)))
    S["cocina_freir"] = _norm(fr, 0.45)
    hv = np.zeros(int(SR * 2.4))                                 # hervir: la olla borboteando, burbujas graves que suben y revientan
    for _ in range(34):
        f0 = float(rng.uniform(140, 420))
        d = float(rng.uniform(0.05, 0.11))
        _poner(hv, _barrido(f0, f0 * 1.9, d) * np.sin(np.pi * _t(d) / d), float(rng.uniform(0.0, 2.2)), float(rng.uniform(0.5, 1.0)))
    th = _t(2.4)
    hv = (hv + 0.12 * _filtro(ruido(2.4), 500, 3000)) * np.minimum(1.0, th / 0.2) * np.minimum(1.0, (2.4 - th) / 0.5)
    S["cocina_hervir"] = _norm(hv, 0.45)
    pl = np.zeros(int(SR * 0.9))                                 # el plato en la mesa: la loza que se posa y el tintineo de los cubiertos
    _poner(pl, _filtro(ruido(0.05), 150, 1200) * _decae(0.05, 0.015), 0.0, 0.8)
    for f0, a in ((1650, 1.0), (2480, 0.5), (3900, 0.25)):
        _poner(pl, _seno(f0, 0.5) * _decae(0.5, 0.11), 0.01, 0.35 * a)
    for t0, f0 in ((0.34, 4200), (0.43, 5100)):
        _poner(pl, (_seno(f0, 0.3) + 0.4 * _seno(f0 * 1.51, 0.3)) * _decae(0.3, 0.07), t0, 0.3)
    S["plato_servido"] = _norm(pl, 0.5)
    # ----------------------------------------------- canales de rol de los servidores (versión 1.7.1): cada canal, su aviso
    S["chat_personaje"] = _norm(_sec([392, 523], 0.11, 0.42, 0.2, (1, 0.5, 0.25)), 0.45)        # en personaje: dos notas graves y cálidas, como una voz cercana
    fp = np.zeros(int(SR * 0.3))                                 # fuera de personaje: dos toques secos de madera, como abrir y cerrar un paréntesis
    for t0, f0 in ((0.0, 880), (0.13, 880)):
        _poner(fp, _seno(f0, 0.07) * _decae(0.07, 0.016), t0)
        _poner(fp, _filtro(ruido(0.02), 1500, 5000) * _decae(0.02, 0.006), t0, 0.35)
    S["chat_fuera"] = _norm(fp, 0.42)
    ac = np.zeros(int(SR * 0.45))                                # una acción: el roce de un movimiento y una nota que lo remata
    ta = _t(0.22)
    _poner(ac, _filtro(ruido(0.22), 500, 3500) * np.sin(np.pi * ta / 0.22) ** 2, 0.0, 0.6)
    _poner(ac, (_seno(659, 0.22) + 0.3 * _seno(1318, 0.22)) * _decae(0.22, 0.07), 0.18)
    S["chat_accion"] = _norm(ac, 0.45)
    # ----------------------------------------------- la espera a que vuelva un servidor: dos notas lentas y flojas, como una llamada que da tono
    S["espera_servidor"] = _norm(_sec([330, 247], 0.42, 0.8, 0.38, (1, 0.3, 0.1)), 0.3)
    # ----------------------------------------------- la reconquista de barrios (versión 1.7.1): la amenaza, el barrio perdido y el barrio defendido
    am = np.zeros(int(SR * 1.15))                                # amenaza: tres golpes de tambor grave, cada vez más seguidos, y dos notas tensas, casi juntas
    for t0 in (0.0, 0.3, 0.52):
        _poner(am, _barrido(120, 62, 0.22) * _decae(0.22, 0.07), t0)
        _poner(am, _filtro(ruido(0.04), 300, 1800) * _decae(0.04, 0.012), t0, 0.35)
    _poner(am, (_nota(311.1, 0.45, 0.2, (1, 0.5, 0.3)) + _nota(329.6, 0.45, 0.2, (1, 0.5, 0.3))) * 0.5, 0.68, 0.7)
    S["amenaza_barrio"] = _norm(am, 0.5)
    bp = np.zeros(int(SR * 1.6))                                 # barrio perdido: una campana grave y cuatro notas que bajan, cada una más apagada, y la persiana que cae
    _poner(bp, (_seno(98, 1.2) + 0.5 * _seno(196.5, 1.2) + 0.3 * _seno(247, 1.2)) * _decae(1.2, 0.45), 0.0, 0.8)
    for k, f0 in enumerate((392.0, 349.2, 311.1, 261.6)):
        _poner(bp, _nota(f0, 0.5, 0.2, (1, 0.35, 0.15)), 0.12 + 0.24 * k, 0.75 - 0.12 * k)
    _poner(bp, _filtro(ruido(0.3), 200, 2400) * _decae(0.3, 0.1, 0.02), 1.15, 0.5)
    S["barrio_perdido"] = _norm(bp, 0.5)
    bd = np.zeros(int(SR * 1.25))                                # barrio defendido: redoble corto y tres notas que suben, la última sostenida con su quinta
    for k in range(5):
        _poner(bd, _filtro(ruido(0.035), 400, 3000) * _decae(0.035, 0.01), 0.045 * k, 0.4 + 0.1 * k)
    for k, f0 in enumerate((392.0, 493.9, 587.3)):
        _poner(bd, _nota(f0, 0.3, 0.14, (1, 0.5, 0.25)), 0.26 + 0.14 * k, 0.8)
    _poner(bd, _nota(784.0, 0.6, 0.28, (1, 0.5, 0.25)) + 0.6 * _nota(587.3, 0.6, 0.28, (1, 0.4, 0.2)), 0.66)
    S["barrio_defendido"] = _norm(bd, 0.5)
    # ----------------------------------------------- la vida honrada y sus consecuencias (versión 1.7.1): despido, inspección, factura y título
    de = np.zeros(int(SR * 1.2))                                 # despido: un portazo seco y tres notas que bajan, la última más larga
    _poner(de, _barrido(160, 55, 0.16) * _decae(0.16, 0.045), 0.0)
    _poner(de, _filtro(ruido(0.09), 150, 2200) * _decae(0.09, 0.02), 0.0, 0.7)
    for k, f0 in enumerate((440.0, 370.0, 277.2)):
        _poner(de, _nota(f0, 0.5 if k == 2 else 0.24, 0.22 if k == 2 else 0.1, (1, 0.3, 0.12)), 0.26 + 0.2 * k, 0.75)
    S["despido"] = _norm(de, 0.5)
    ins = np.zeros(int(SR * 1.15))                               # inspección: tres golpes de nudillos en la puerta, un roce de papeles y el sello
    for t0 in (0.0, 0.16, 0.32):
        _poner(ins, _barrido(420, 260, 0.05) * _decae(0.05, 0.014), t0, 0.9)
        _poner(ins, _filtro(ruido(0.03), 800, 3000) * _decae(0.03, 0.008), t0, 0.3)
    tp = _t(0.28)
    _poner(ins, _filtro(ruido(0.28), 2500, 7000) * np.sin(np.pi * tp / 0.28) ** 2, 0.5, 0.35)
    _poner(ins, _barrido(140, 70, 0.14) * _decae(0.14, 0.04), 0.86)
    _poner(ins, _filtro(ruido(0.05), 300, 1500) * _decae(0.05, 0.015), 0.86, 0.5)
    S["inspeccion"] = _norm(ins, 0.5)
    fa = np.zeros(int(SR * 0.95))                                # factura: la impresora de tiques, seis rayas cortas, el papel que se corta y una nota grave
    for k in range(6):
        _poner(fa, _filtro(ruido(0.045), 1800, 5200) * _decae(0.045, 0.02, 0.004), 0.06 * k, 0.5)
    _poner(fa, _filtro(ruido(0.08), 3000, 8000) * _decae(0.08, 0.02), 0.42, 0.6)
    _poner(fa, _nota(196.0, 0.42, 0.18, (1, 0.45, 0.2)), 0.52, 0.8)
    S["factura"] = _norm(fa, 0.45)
    ti = np.zeros(int(SR * 1.5))                                 # título: cuatro notas de fanfarria y un acorde largo con su octava
    for k, f0 in enumerate((392.0, 392.0, 523.3, 659.3)):
        _poner(ti, _nota(f0, 0.2, 0.09, (1, 0.6, 0.35, 0.15)), (0.0, 0.14, 0.24, 0.4)[k], 0.8)
    _poner(ti, (_nota(523.3, 0.9, 0.42, (1, 0.5, 0.25)) + _nota(659.3, 0.9, 0.42, (1, 0.4, 0.2)) + _nota(784.0, 0.9, 0.42, (1, 0.4, 0.2)) + 0.5 * _nota(1046.5, 0.9, 0.35, (1, 0.2))) * 0.4, 0.58)
    S["titulo"] = _norm(ti, 0.5)
    # ----------------------------------------------- volar de verdad (versión 1.7.1): tonos de altitud y de alineación, turbulencia, alarma de cabina y aterrizaje
    S["tono_altitud"] = _norm((_seno(660, 0.13) + 0.25 * _seno(1320, 0.13)) * np.sin(np.pi * _t(0.13) / 0.13) ** 0.6, 0.4)      # una nota limpia: el juego la sube y la baja con la altitud
    ta = np.zeros(int(SR * 0.11))                                # alineación: dos chasquidos secos muy seguidos, fáciles de situar a un lado o a otro
    for t0 in (0.0, 0.055):
        _poner(ta, _seno(1250, 0.04) * _decae(0.04, 0.009), t0)
        _poner(ta, _filtro(ruido(0.012), 2500, 7000) * _decae(0.012, 0.004), t0, 0.35)
    S["tono_alineacion"] = _norm(ta, 0.4)
    tt = _t(1.3)                                                 # turbulencia: un zarandeo grave que tiembla, con golpes de aire
    tu = _filtro(ruido(1.3), 35, 240) * (0.55 + 0.45 * np.sin(2 * np.pi * 7.5 * tt)) * np.sin(np.pi * tt / 1.3) ** 0.5
    for t0 in (0.12, 0.47, 0.83):
        _poner(tu, _barrido(95, 45, 0.14) * _decae(0.14, 0.05), t0, 0.8)
        _poner(tu, _filtro(ruido(0.1), 300, 1800) * _decae(0.1, 0.03), t0, 0.25)
    S["turbulencia"] = _norm(np.tanh(1.6 * tu), 0.6)
    al = np.zeros(int(SR * 0.62))                                # alarma de cabina: cuatro pitidos apremiantes, alto y bajo
    for k in range(4):
        f0 = 980.0 if k % 2 == 0 else 740.0
        _poner(al, (_seno(f0, 0.11) + 0.35 * _seno(f0 * 2, 0.11) + 0.15 * _seno(f0 * 3, 0.11)) * np.sin(np.pi * _t(0.11) / 0.11) ** 0.4, 0.15 * k)
    S["alarma_cabina"] = _norm(al, 0.5)
    at = np.zeros(int(SR * 1.25))                                # aterrizaje: el golpe del tren en el suelo, el chirrido de las ruedas y la rodadura que se apaga
    _poner(at, _barrido(110, 48, 0.2) * _decae(0.2, 0.06), 0.0)
    _poner(at, _filtro(ruido(0.08), 200, 1500) * _decae(0.08, 0.025), 0.0, 0.6)
    tc = _t(0.3)
    _poner(at, (_barrido(1900, 1350, 0.3) * 0.5 + _filtro(ruido(0.3), 1500, 4500) * 0.6) * np.sin(np.pi * tc / 0.3) ** 1.5, 0.05, 0.45)
    tr2 = _t(0.95)
    _poner(at, _filtro(ruido(0.95), 60, 700) * np.exp(-tr2 / 0.35) * (0.8 + 0.2 * np.sin(2 * np.pi * 11 * tr2)), 0.28, 0.7)
    S["aterrizaje"] = _norm(at, 0.55)
    return S


# Sonidos que el juego reproduce en bucle: si los sustituyes, el final debe empalmar con el principio.
PREFIJOS_BUCLE = ("amb_", "motor_", "lugar_", "loc_")
BUCLES = {"amb_pabellon", "avion", "tren", "tranvia", "bajo_agua", "rodadura", "alarma", "sirena", "sirena_ambulancia", "fuego", "ganzua", "intermitente", "lluvia", "latido", "multitud", "helicoptero_policia"}


def es_bucle(nombre):
    return nombre in BUCLES or nombre.startswith(PREFIJOS_BUCLE)


# Sonidos de fondo: no vienen de ningún punto, así que se dejan en estéreo, tal como se grabaron.
FONDOS = {"lluvia"}
MAX_EFECTO = 60                   # segundos: un efecto de sonido más largo se recorta. Nadie pone un claxon de una hora a propósito
MAX_FONDO = 90                    # segundos: un ambiente más largo se recorta, para no llenar la memoria


def es_fondo(nombre):
    return nombre.startswith("amb_") or nombre in FONDOS


def _remuestrear(d, sr):
    """Cambia la frecuencia de muestreo sin estropear los agudos, en el dominio de la frecuencia.

    Un sonido corto se convierte de una vez. Uno largo, una canción, por tramos que se solapan y se funden: convertir
    de golpe tres minutos de música costaba varios segundos, y era lo que hacía esperar a la música del menú."""
    g = math.gcd(int(sr), SR)
    a, b = int(sr) // g, SR // g                          # cada a muestras de entrada son b de salida, exactas
    if len(d) > 4 * 51200 and a <= 2048:
        return _remuestrear_tramos(d, a, b)
    return _remuestrear_entero(d, sr)


def _remuestrear_tramos(d, a, b):
    m = max(1, round(40960 / a))
    paso_e, paso_s = a * m, b * m                         # lo que avanza cada tramo, en la entrada y en la salida
    sol_e, sol_s = a * max(1, m // 4), b * max(1, m // 4)  # lo que se solapa con el siguiente
    n_e, n_s = paso_e + sol_e, paso_s + sol_s
    canales = d[:, None] if d.ndim == 1 else d
    total = int(math.ceil(len(canales) / paso_e))
    salida = np.zeros((total * paso_s + sol_s, canales.shape[1]), np.float32)
    sube = np.linspace(0.0, 1.0, sol_s, dtype=np.float32)[:, None]
    k = min(n_s // 2 + 1, n_e // 2 + 1)
    for i in range(total):
        trozo = canales[i * paso_e:i * paso_e + n_e]
        if len(trozo) < n_e:
            trozo = np.concatenate([trozo, np.zeros((n_e - len(trozo), canales.shape[1]), trozo.dtype)])
        espectro = np.fft.rfft(trozo, axis=0)
        nuevo = np.zeros((n_s // 2 + 1, canales.shape[1]), espectro.dtype)
        nuevo[:k] = espectro[:k]
        y = (np.fft.irfft(nuevo, n_s, axis=0) * (n_s / n_e)).astype(np.float32)
        if i:
            y[:sol_s] *= sube                             # entra fundiéndose con la cola del anterior
        if i < total - 1:
            y[paso_s:] *= 1.0 - sube
        salida[i * paso_s:i * paso_s + n_s] += y
    salida = salida[:max(2, int(round(len(canales) * b / a)))]
    return salida[:, 0] if d.ndim == 1 else salida


def _remuestrear_entero(d, sr):
    n = max(2, int(round(len(d) * SR / sr)))
    canales = d[:, None] if d.ndim == 1 else d
    salida = np.empty((n, canales.shape[1]), np.float32)
    for c in range(canales.shape[1]):
        espectro = np.fft.rfft(canales[:, c].astype(np.float64))
        m = n // 2 + 1
        nuevo = np.zeros(m, np.complex128)
        k = min(m, len(espectro))
        nuevo[:k] = espectro[:k]
        salida[:, c] = np.fft.irfft(nuevo, n) * (n / len(d))
    return salida[:, 0] if d.ndim == 1 else salida


def duracion_audio(ruta):
    """Segundos que dura un archivo de audio, sin leerlo. Cero si no se puede saber."""
    import soundfile as sf
    try:
        i = sf.info(ruta)
        return i.frames / float(i.samplerate) if i.samplerate else 0.0
    except Exception:
        return 0.0


def a_mono(d):
    """Pasa a mono un sonido de varios canales. Con la media de los canales, una grabación estéreo de verdad (dos
    micrófonos, con los canales algo desfasados) se anula en parte: pierde volumen y suena hueca. Si la media se queda en
    menos de las tres cuartas partes del canal más fuerte, se usa ese canal solo."""
    if d.ndim == 1 or d.shape[1] == 1:
        return d.reshape(-1)
    media = d.mean(axis=1)
    fuerza = np.sqrt(np.mean(np.square(d.astype(np.float64)), axis=0))
    if fuerza.max() > 1e-6 and np.sqrt(np.mean(np.square(media.astype(np.float64)))) < 0.75 * fuerza.max():
        return np.ascontiguousarray(d[:, int(np.argmax(fuerza))])
    return media


def leer_audio(ruta, mono=True, maximo=None, desde=0.0):
    """Lee un archivo de audio y lo adapta al motor: 44100 Hz, y mono o estéreo según se pida.

    Con `maximo` se leen como mucho esos segundos, y con `desde`, a partir de ese segundo. Del disco solo sale lo que
    se pide: un archivo de una hora no se carga entero para quedarse con un minuto.
    """
    import soundfile as sf
    with sf.SoundFile(ruta) as f:
        sr = f.samplerate
        if desde > 0:
            f.seek(min(int(desde * sr), f.frames))
        d = f.read(frames=int(maximo * sr) if maximo else -1, dtype="float32", always_2d=True)
    if mono:
        d = a_mono(d)
    elif d.shape[1] == 1:
        d = d[:, 0]                                  # un archivo mono se queda mono: no se gana nada duplicándolo
    else:
        d = d[:, :2]
    if sr != SR and len(d) > 1:
        d = _remuestrear(d, sr)
    return np.ascontiguousarray(d, dtype=np.float32)


def escribir_wav(ruta, datos):
    import soundfile as sf
    sf.write(ruta, np.clip(datos, -1.0, 1.0), SR, subtype="PCM_16")


# Desde la versión 1.6.2 los sonidos del juego se guardan en FLAC en lugar de WAV. FLAC comprime sin pérdida:
# al leerlo salen exactamente las mismas muestras que del WAV, pero el archivo ocupa menos de la mitad.
# OGG y MP3 ocupan aún menos, pero pierden calidad; por eso solo se usan donde el original ya venía así.
FORMATO = ".flac"
EXT_AUDIO = (".wav", ".ogg", ".flac", ".mp3")


def escribir_audio(ruta_sin_extension, datos):
    """Guarda un sonido en el formato del juego (FLAC, sin pérdida). Devuelve la ruta escrita."""
    ruta = ruta_sin_extension + FORMATO
    escribir_wav(ruta, datos)
    return ruta


def archivos_de(carpeta):
    """{nombre: ruta} de los sonidos de una carpeta. Si un sonido está en dos formatos, manda el que no es FLAC:
    es el que ha puesto el jugador para sustituir al de serie."""
    out = {}
    try:
        nombres = sorted(os.listdir(carpeta))
    except OSError:
        return out
    for f in nombres:
        nombre, ext = os.path.splitext(f)
        ext = ext.lower()
        if ext in EXT_AUDIO and (nombre not in out or (out[nombre].lower().endswith(FORMATO) and ext != FORMATO)):
            out[nombre] = os.path.join(carpeta, f)
    return out


def limpiar_formato_anterior(carpeta):
    """Tras actualizar desde una versión anterior quedan los WAV antiguos junto a los FLAC nuevos. Aquí se borran los
    que son el mismo sonido, para que no ocupen sitio sin usarse. Un WAV distinto del FLAC es un sonido que el jugador
    cambió a mano: ese no se toca, y es el que suena. Devuelve cuántos archivos ha borrado."""
    import soundfile as sf
    try:
        nombres = os.listdir(carpeta)
    except OSError:
        return 0
    flac = {os.path.splitext(f)[0] for f in nombres if f.lower().endswith(FORMATO)}
    borrados = 0
    for f in nombres:
        nombre, ext = os.path.splitext(f)
        if ext.lower() != ".wav" or nombre not in flac:
            continue
        try:
            viejo, sr1 = sf.read(os.path.join(carpeta, f), dtype="int16")
            nuevo, sr2 = sf.read(os.path.join(carpeta, nombre + FORMATO), dtype="int16")
            if sr1 == sr2 and viejo.shape == nuevo.shape and np.array_equal(viejo, nuevo):
                os.remove(os.path.join(carpeta, f))
                borrados += 1
        except Exception:
            continue
    return borrados


def cargar(mezclador, carpeta):
    """Carga todos los sonidos de data/sonidos. Los que falten se generan y se guardan en FLAC.

    Cada sonido es un archivo con su nombre: para cambiar uno basta con poner al lado un archivo con el mismo
    nombre (WAV, OGG, FLAC o MP3). Si se borra un archivo, el juego vuelve a crear el original.
    """
    os.makedirs(carpeta, exist_ok=True)
    limpiar_formato_anterior(carpeta)
    S = {}
    for nombre, ruta in archivos_de(carpeta).items():
        try:
            d = leer_audio(ruta, mono=not es_fondo(nombre), maximo=MAX_FONDO if es_fondo(nombre) else MAX_EFECTO)
            if len(d) > 8:
                S[nombre] = d
        except Exception:
            pass
    marca = os.path.join(carpeta, "_version.txt")
    try:
        al_dia = open(marca, encoding="utf-8").read().strip() == str(VERSION_CACHE)
    except OSError:
        al_dia = False
    if not al_dia or not S:
        originales = generar()
        for nombre, d in originales.items():
            if nombre not in S:
                S[nombre] = d
                try:
                    escribir_audio(os.path.join(carpeta, nombre), d)
                except Exception:
                    pass
        try:
            open(marca, "w", encoding="utf-8").write(str(VERSION_CACHE))
        except OSError:
            pass
    else:
        # si el jugador ha borrado algún archivo, se recupera el original
        faltan = None
        for nombre in NOMBRES_BASICOS:
            if nombre not in S:
                faltan = faltan or generar()
                if nombre in faltan:
                    S[nombre] = faltan[nombre]
                    try:
                        escribir_audio(os.path.join(carpeta, nombre), faltan[nombre])
                    except Exception:
                        pass
        if faltan:
            for nombre, d in faltan.items():
                if nombre not in S:
                    S[nombre] = d
                    try:
                        escribir_audio(os.path.join(carpeta, nombre), d)
                    except Exception:
                        pass
    for k, v in S.items():
        mezclador.registrar(k, v)
    return S


# Sonidos sin los que el juego no puede funcionar bien: si falta alguno, se regeneran todos los que falten.
NOMBRES_BASICOS = ("menu_mover", "menu_ok", "baliza", "paso_acera0", "motor_coche", "disparo_pistola", "amb_ciudad", "cruce", "radar", "llegada")
