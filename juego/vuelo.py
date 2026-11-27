"""Volar de verdad (1.7.1): altura, combustible, travesías entre localidades, hangares, secuestros y vuelos comerciales.

Hasta ahora volar era ir por encima de todo, y cambiar de localidad, un salto desde un helipuerto. Con la opción
«Vuelo real» (viene puesta):

- Dentro de una localidad el aparato tiene altura: despega, sube con la D y baja con la A, y aterriza con la F. Volando
  bajo, todo es como antes; volando alto, la policía de tierra te pierde, pero un radar te ve.
- Gasta combustible, que se repone en helipuertos, aeropuertos y aeródromos.
- Al salir por el borde de la localidad, o con Intro en un helipuerto o un aeropuerto, se hace una travesía de verdad
  hasta otra localidad: rumbo, altitud, viento, torre, sucesos y aproximación. La travesía es la pantalla de
  vuelo_pantalla.py.
- Las aeronaves propias se guardan en hangares, alquilados o comprados.
- Se puede secuestrar un aparato de línea: delito mayor, con radar.
- Con la licencia de piloto comercial se hacen vuelos de pasajeros y de carga, como trabajo legal.

Todo lo que es un número o una frase está en los datos (vida.json: vuelo, aeronaves y mapa_aire).
"""
from .i18n import tr
import math
import random

import pygame

from . import mundo as M
from .ajustes import Ajustes

AJ = Ajustes("vuelo", {
    # dentro de una localidad
    "alt_despegue": 60, "alt_minima": 30, "alt_alta": 150, "paso_altura": 50, "descenso": 16,
    "consumo_local": 1.2, "reserva": 20, "critico": 8, "planeo": 9,
    "pista_radio": 70, "forzoso_min": 15, "forzoso_max": 35, "caida_min": 40, "caida_max": 80, "caida_herida_min": 15, "caida_herida_max": 40,
    # la travesía
    "compresion": 12, "acelerado": 4, "viento_max": 45, "viento_lluvia": 160, "giro": 10, "paso_crucero": 100, "ascenso_crucero": 30, "nivel_km": 30,
    "aprox_km": 6, "aprox_alt": 200, "alineacion": 20, "frustradas": 2, "frustrada_km": 3, "llegada_km": 0.5, "sobrevuelo_km": 1.5,
    "suceso_cada": 28, "peso_turbulencia": 35, "peso_trafico": 25, "peso_tormenta": 20, "peso_paisaje": 20,
    "turbulencia_seg": 6, "trafico_seg": 9, "trafico_multa": 150, "tormenta_radio": 6, "tormenta_alt": 1800, "tormenta_dano": 4,
    "bajo_lento": 85, "bajo_consumo": 130, "obstaculo_cada": 9, "obstaculo_seg": 4, "obstaculo_sube": 80, "obstaculo_dano": 15,
    "duro_dano": 8,
    # radar y secuestro
    "radar_pierde": 25, "radar_pierde_crucero": 12, "secuestro_busqueda": 4, "secuestro_espera": 4, "secuestro_reconocen": 2, "secuestro_llegada": 3,
    "secuestro_gravedad": 3, "encargo_min": 3500, "encargo_max": 7000, "encargo_radio": 70,
    # hangares
    "hangar_plazas": 2, "hangar_tope": 6, "hangar_impago": 3,
    # vuelos comerciales
    "vuelo_base": 180, "vuelo_km": 9, "vuelo_ofertas": 3, "vuelo_propio": 25, "vuelo_confort": 10, "vuelo_prestigio": 1,
}, {
    "torre_despegue": [tr("{campo}, autorizado a despegar. Viento de {viento}. Rumbo {rumbo} hacia {destino}, {km} kilómetros."),
                       tr("Aquí {campo}. Pista libre. Viento de {viento}. {destino} queda a {km} kilómetros, rumbo {rumbo}.")],
    "torre_salida": [tr("Dejas {origen}. Rumbo {rumbo} hacia {destino}, {km} kilómetros. Viento de {viento}."),
                     tr("Control de {origen}: te veo salir hacia {destino}, rumbo {rumbo}, {km} kilómetros. Viento de {viento}.")],
    "torre_crucero": [tr("Nivel de crucero, {alt} metros. Buen vuelo."), tr("A {alt} metros y en rumbo. Te quedan {km} kilómetros.")],
    "torre_aprox": [tr("Torre de {campo}: te tengo a {km} kilómetros. Baja a {alt} metros y mantén rumbo {rumbo}."),
                    tr("{campo}, aproximación. Estás a {km} kilómetros: desciende a {alt} metros, rumbo {rumbo}.")],
    "torre_final": [tr("En final. Bien encarado. Autorizado a aterrizar."), tr("Pista a la vista. Sigue así: autorizado.")],
    "torre_frustrada": [tr("Demasiado {motivo}. Motor y al aire: da otra vuelta y vuelve a entrar."), tr("No así: vienes demasiado {motivo}. Aproximación frustrada, repite.")],
    "torre_guiada": [tr("Te llevo yo. Sigue mis indicaciones y no toques nada."), tr("Tranquilidad: te guío hasta el suelo.")],
    "frases_aterrizaje": [tr("Tocas tierra con suavidad en {campo}."), tr("Las ruedas besan la pista de {campo}. Buen aterrizaje.")],
    "frases_aterrizaje_duro": [tr("Tocas tierra con un golpe seco en {campo}: el aparato se resiente."), tr("Aterrizaje duro en {campo}. Algo ha crujido.")],
    "frases_sobrevuelo": [tr("Entras volando bajo sobre {destino}. Busca dónde posarte."), tr("Ya tienes {destino} debajo. Elige dónde bajas.")],
    "frases_turbulencia": [tr("Turbulencias. El aparato se zarandea."), tr("Entras en una zona de aire revuelto: agárrate.")],
    "frases_turbulencia_fin": [tr("El aire se calma."), tr("Se acabaron las turbulencias.")],
    "torre_trafico": [tr("Tráfico de frente a tu misma altitud, a pocos kilómetros. Sube o baja cien metros, ya."),
                      tr("Atención: un aparato viene hacia ti a tu altura. Cambia de nivel, cien metros arriba o abajo.")],
    "frases_trafico_libre": [tr("Separación suficiente. El otro aparato pasa de largo."), tr("Bien. Tráfico librado.")],
    "frases_trafico_susto": [tr("El otro aparato pasa rozándote. La torre te abre un expediente."), tr("Por muy poco. Lo vas a ver en un papel con membrete.")],
    "torre_tormenta": [tr("Meteorología: una tormenta en tu rumbo, a {km} kilómetros. Tú decides."), tr("Hay un frente de tormenta delante, a {km} kilómetros.")],
    "frases_tormenta_dentro": [tr("Estás dentro de la tormenta: agua, rayos y un aire que no perdona."), tr("La tormenta te envuelve. El aparato cruje.")],
    "frases_tormenta_fuera": [tr("Sales de la tormenta."), tr("La tormenta queda atrás.")],
    "frases_tormenta_encima": [tr("Pasas por encima de la tormenta: abajo se ven los relámpagos."), tr("La tormenta queda debajo de ti.")],
    "frases_paisaje": [tr("Dejas {lugar} a tu {lado}, a {km} kilómetros."), tr("A tu {lado}, a {km} kilómetros, {lugar}.")],
    "frases_obstaculo": [tr("¡Obstáculo delante! Un tendido eléctrico: sube."), tr("¡Una loma justo delante! Arriba, ya."), tr("¡Cables! Gana altura.")],
    "frases_obstaculo_libre": [tr("Lo libras por arriba."), tr("Pasas por encima. Por poco.")],
    "frases_obstaculo_roce": [tr("Rozas algo con la panza del aparato. Has perdido piezas."), tr("Un golpe seco por debajo: has tocado.")],
    "frases_reserva": [tr("Combustible en reserva: te queda un {pct} por ciento."), tr("Queda poco combustible: un {pct} por ciento.")],
    "frases_critico": [tr("¡Combustible crítico! Un {pct} por ciento. Aterriza ya."), tr("Casi sin combustible: {pct} por ciento. Busca dónde bajar.")],
    "frases_sin_motor": [tr("El motor tose y se para: no queda combustible. Planeas."), tr("Silencio. Te has quedado sin combustible y bajas planeando.")],
    "frases_forzoso": [tr("Aterrizaje forzoso: el aparato se arrastra por el suelo y se para."), tr("Te posas como puedes. No ha sido bonito.")],
    "frases_caida": [tr("El aparato cae y se estrella. Sales de los restos como puedes."), tr("Golpe brutal contra el suelo. Sigues vivo de milagro.")],
    "frases_radar": [tr("El radar te sigue: mientras vueles por encima de {alt} metros, saben dónde estás."), tr("Te tienen en la pantalla. Por debajo de {alt} metros no te ven.")],
    "frases_radar_perdido": [tr("Te han perdido en el radar."), tr("Para el radar, has desaparecido.")],
    "frases_radar_otra_vez": [tr("Vuelves a salir en el radar."), tr("Has subido demasiado: el radar te tiene otra vez.")],
    "frases_te_esperan": [tr("En {campo} te estaban esperando: coches patrulla en la pista."), tr("Nada más tocar tierra en {campo} lo ves: la policía te esperaba.")],
    "frases_reconocen": [tr("En {campo} alguien reconoce el aparato y descuelga un teléfono."), tr("El de la torre de {campo} mira dos veces la matrícula. Mala señal.")],
    "frases_secuestro": [tr("Encañonas al piloto, que salta a la pista con las manos en alto. El aparato es tuyo. Toda la comarca lo va a saber."),
                         tr("Subes de un salto y echas al piloto. Por megafonía ya están dando la alarma.")],
    "frases_encargo_hecho": [tr("Unos tipos salen de entre los árboles, miran el aparato y te pagan sin preguntar: {paga} euros."),
                             tr("El comprador cuenta los billetes mientras los suyos cubren el aparato con una lona: {paga} euros.")],
    "frases_encargo_radar": [tr("Aquí no hay nadie: te han seguido por el radar y el comprador se ha esfumado. No hay paga."),
                             tr("El comprador no aparece. Con el radar encima, nadie se acerca.")],
    "frases_piloto_oferta": [tr("{que} a {destino}: {km} kilómetros, {paga} euros.")],
    "frases_piloto_sale": [tr("Pasaje a bordo. Destino, {destino}."), tr("Carga estibada y papeles en regla. Destino, {destino}.")],
    "frases_piloto_llega": [tr("Vuelo cumplido. Cobras {paga} euros."), tr("Entregado en {destino}. La compañía te paga {paga} euros.")],
    "frases_piloto_propina": [tr("Vuelo tranquilo: te dan {extra} euros más."), tr("Ni un bache: {extra} euros de gratificación.")],
    "frases_piloto_queja": [tr("El viaje ha sido movido: te descuentan {extra} euros."), tr("Hay quejas por el vuelo: {extra} euros menos.")],
    "pasajes": [tr("Tres ejecutivos con prisa"), tr("Una familia con maletas"), tr("Un equipo de rodaje"), tr("Dos médicos con una nevera"), tr("Unos novios y su fotógrafo"), tr("Un geólogo y sus cajas")],
    "cargas": [tr("Correo urgente"), tr("Repuestos para un taller"), tr("Medicinas"), tr("Marisco en hielo"), tr("Una pieza de turbina"), tr("Instrumentos de una orquesta")],
    "sitios_discretos": ["monumento", "pesca", "tesoro", "feria", "protectora", "desguace", "taller"],
}, cero=("consumo_local", "viento_max", "frustradas", "peso_turbulencia", "peso_trafico", "peso_tormenta", "peso_paisaje", "trafico_multa", "tormenta_dano",
         "obstaculo_dano", "duro_dano", "secuestro_reconocen", "vuelo_propio", "vuelo_confort", "vuelo_prestigio", "forzoso_min", "hangar_impago"))

# Lo que vuela, y cómo: lo que diga la sección «aeronaves» de los datos; para un modelo que no esté, se deduce.
AERONAVES_SERIE = [
    {"id": "helicoptero", "crucero": 170, "alt_crucero": 500, "techo": 900, "autonomia": 260, "ascenso": 10, "pista": False},
    {"id": "avioneta", "crucero": 250, "alt_crucero": 1500, "techo": 2600, "autonomia": 520, "ascenso": 14, "pista": True},
]
# Dónde está cada localidad en el mapa de la comarca, en kilómetros: x hacia el este, y hacia el norte.
MAPA_SERIE = [
    {"id": "puerto_bravo", "x": 0, "y": 0}, {"id": "cala_brava", "x": 22, "y": 2}, {"id": "san_lucero", "x": 44, "y": 4}, {"id": "villaseca", "x": 16, "y": 24},
    {"id": "monteferro", "x": 14, "y": 52}, {"id": "fuentefria", "x": 18, "y": 74}, {"id": "isla_tortuga", "x": 27, "y": -22}, {"id": "plataforma", "x": 2, "y": -25},
    {"id": "mar", "x": 20, "y": -13},
]
AERONAVES = {}
MAPA_AIRE = {}
CAMPOS = ("helipuerto", "aeropuerto")
FASES = ("tierra", "despegue", "vuelo", "aterrizando", "sin_motor")


def _num(d, k, serie):
    try:
        return float(d.get(k, serie))
    except (TypeError, ValueError):
        return float(serie)


def configurar(datos):
    AERONAVES.clear()
    for x in list(AERONAVES_SERIE) + [x for x in (datos.get("aeronaves") or []) if isinstance(x, dict) and x.get("id")]:
        serie = AERONAVES.get(x["id"], AERONAVES_SERIE[0])
        AERONAVES[str(x["id"])] = {"id": str(x["id"]), "crucero": max(40.0, _num(x, "crucero", serie["crucero"])), "alt_crucero": max(100.0, _num(x, "alt_crucero", serie["alt_crucero"])),
                                   "techo": max(200.0, _num(x, "techo", serie["techo"])), "autonomia": max(20.0, _num(x, "autonomia", serie["autonomia"])),
                                   "ascenso": max(2.0, _num(x, "ascenso", serie["ascenso"])), "pista": bool(x.get("pista", False))}
    MAPA_AIRE.clear()
    for x in list(MAPA_SERIE) + [x for x in (datos.get("mapa_aire") or []) if isinstance(x, dict) and x.get("id")]:
        MAPA_AIRE[str(x["id"])] = (_num(x, "x", 0), _num(x, "y", 0))


def aeronave(modelo):
    """Cómo vuela un modelo: lo que digan los datos o, si no está, algo razonable sacado de su velocidad."""
    a = AERONAVES.get(modelo.get("id"))
    if a:
        return a
    return {"id": modelo.get("id"), "crucero": max(60.0, float(modelo.get("vel_max", 46)) * 3.6), "alt_crucero": 600.0, "techo": 1200.0, "autonomia": 300.0, "ascenso": 10.0, "pista": False}


def punto_aire(mapa_id):
    """Dónde está una localidad en el mapa de la comarca. Una que no esté apuntada (la de un mod) se coloca sola, siempre en el mismo sitio."""
    if mapa_id in MAPA_AIRE:
        return MAPA_AIRE[mapa_id]
    h = sum((k + 1) * ord(c) for k, c in enumerate(str(mapa_id)))
    ang = (h % 360) * math.pi / 180.0
    d = 55.0 + (h // 360) % 30
    return (round(math.sin(ang) * d, 1), round(math.cos(ang) * d, 1))


def colocar(mapas):
    """Da sitio en el mapa de la comarca a las localidades que no lo traen apuntado (las de los mods), mirando por dónde
    se llega a ellas: una que tiene muelle queda donde esté su muelle en el mar; una a la que se llega por carretera,
    a unos kilómetros de su vecina, hacia el lado por el que sale esa carretera. La que no se pueda deducir se queda
    donde la ponga punto_aire."""
    mar = next((m for m in mapas.values() if m.tipo == "mar"), None)
    faltan = [m for m in mapas.values() if m.id not in MAPA_AIRE and m.tipo != "mar"]
    for _ in range(len(faltan) + 1):
        puestos = 0
        for m in [m for m in faltan if m.id not in MAPA_AIRE]:
            pos = None
            por_tierra = any(l.tipo == "salida" for l in m.lugares.values())
            if not por_tierra and mar is not None:               # una isla: queda donde esté su muelle en el mar
                muelle = next((l for l in mar.lugares.values() if l.get("a_mapa") == m.id), None)
                if muelle is not None:
                    pos = (round((muelle.x - 300.0) * 0.0244, 1), round((muelle.y - 1440.0) * 0.025, 1))
            if pos is None:
                for o in mapas.values():
                    if o.id not in MAPA_AIRE or o.tipo == "mar":
                        continue
                    sale = next((l for l in o.lugares.values() if l.get("a_mapa") == m.id), None)
                    if sale is None:
                        entra = next((l for l in m.lugares.values() if l.get("a_mapa") == o.id), None)
                        if entra is None:
                            continue
                        dx, dy = m.ancho / 2.0 - entra.x, m.alto / 2.0 - entra.y      # se entra por ese lado: la localidad queda al lado contrario de su vecina
                    else:
                        dx, dy = sale.x - o.ancho / 2.0, sale.y - o.alto / 2.0
                    n = math.hypot(dx, dy) or 1.0
                    base = MAPA_AIRE[o.id]
                    pos = (round(base[0] + dx / n * 24.0, 1), round(base[1] + dy / n * 24.0, 1))
                    break
            if pos is not None:
                base, k = pos, 0
                while any(distancia(pos, q) < 12.0 for q in MAPA_AIRE.values()) and k < 40:      # que no caiga encima de otra: se aparta en espiral
                    k += 1
                    ang = k * 2.4
                    pos = (round(base[0] + math.sin(ang) * 4.0 * k, 1), round(base[1] + math.cos(ang) * 4.0 * k, 1))
                MAPA_AIRE[m.id] = pos
                puestos += 1
        if not puestos:
            break


def distancia(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def rumbo_entre(a, b):
    return M.rumbo_a(b[0] - a[0], b[1] - a[1]) % 360


def rumbo_txt(grados):
    g = int(round(grados)) % 360
    return f"{g:03d}, {M.cardinal(g)}"


def km_txt(km):
    return f"{km:.1f}".replace(".", ",") if km < 10 else str(int(round(km)))


def escribir_datos(poner, ajuste, lista):
    """Para la herramienta que escribe las secciones de serie en vida.json."""
    poner([("vuelo", ajuste(AJ)), ("aeronaves", lista(AERONAVES_SERIE)), ("mapa_aire", lista(MAPA_SERIE))])


class Vuelo:
    """Mixin de Partida."""

    def vuelo_iniciar(self):
        self.secuestro = None            # el aparato que has secuestrado: {"veh", "radar", "bajo", "encargo"}
        self.vuelo_trabajo = None        # un vuelo comercial en curso: {"destino", "paga", "que", "km", "veh", "confort"}
        self._vuelo_dia = None
        self._vuelo_borde_t = -99.0
        colocar(self.mapas)                                      # las localidades de los mods, en el mapa de la comarca

    # ------------------------------------------------------------------ lo básico
    def vuelo_real(self):
        """¿Se vuela de verdad? Con la opción puesta. En las pruebas automáticas solo si la prueba lo pide, como los trayectos."""
        return bool(self.cfg["vuelo_real"]) and (not self.app.pruebas or getattr(self.app, "vuelo_en_pruebas", False))

    def vuelo_con_combustible(self):
        return self.vuelo_real() and bool(self.cfg["vuelo_combustible"])

    def volando(self, v=None):
        v = v if v is not None else self.j.veh
        return v is not None and bool(v.modelo.get("vuela"))

    def vuelo_prep(self, v):
        """Lo que lleva de más un aparato cuando se vuela de verdad: altura, fase y combustible."""
        if getattr(v, "fase", None) not in FASES:
            v.fase = "tierra"
            v.alt = 0.0
        if getattr(v, "queroseno", None) is None:
            v.queroseno = 100.0
        return v

    def vuelo_alt(self):
        """A qué altura va el jugador, en metros; 0 si no vuela o está en tierra."""
        v = self.j.veh
        if v is None or not v.modelo.get("vuela"):
            return 0.0
        if not self.vuelo_real():
            return 35.0
        return float(getattr(v, "alt", 0.0))

    def vuelo_alto(self):
        """Vuelas por encima de donde te ve la policía de tierra (y por donde te ve el radar)."""
        return self.vuelo_real() and self.vuelo_alt() >= AJ("alt_alta")

    def _tono_alt(self, alt, techo=2600.0):
        self.son("tono_altitud", cat="interfaz", vol=0.6, tono=0.6 + 1.2 * max(0.0, min(1.0, alt / max(300.0, techo))))

    def vuelo_texto_subir(self, v):
        self.vuelo_prep(v)
        a = aeronave(v.modelo)
        t = tr(" Estás en tierra. Flecha arriba despega; en el aire, izquierda y derecha giran, la D sube y la A baja. Para aterrizar, frena y pulsa F")
        t += tr(": con este aparato hace falta una pista, la de un aeropuerto o un aeródromo.") if a["pista"] else tr(" sobre una calle, un helipuerto o un espacio abierto.")
        if self.vuelo_con_combustible():
            t += tr(' Combustible, {int} por ciento.').format(int=(int(v.queroseno)))
        return t + tr(" En el borde de la localidad, o con Intro en un helipuerto o un aeropuerto, empiezas una travesía a otra localidad.")

    # ------------------------------------------------------------------ volar dentro de una localidad
    def vuelo_controles(self, v, dt, t):
        """Cada fotograma, antes de mover el aparato: despegue, altura, combustible y motor parado. Devuelve las teclas
        que valen (en tierra o aterrizando, ninguna de las de moverse)."""
        self.vuelo_prep(v)
        a = aeronave(v.modelo)
        fase = v.fase
        sin = frozenset(k for k in t if k not in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE))
        if fase == "tierra":
            v.alt = 0.0
            if pygame.K_UP in t:
                if self.vuelo_con_combustible() and v.queroseno <= 0:
                    v.vel = 0.0
                    if self.t - getattr(self, "t_aviso_seco", -99) > 6:
                        self.t_aviso_seco = self.t
                        self.son("motor_seco", cat="interfaz")
                        self.decir(tr("El motor no arranca: no queda combustible. Se reposta en un helipuerto, un aeropuerto o un aeródromo, o desde el móvil, en Mis vehículos."))
                    return sin
                v.fase = "despegue"
                self.decir(tr("Coges carrera: mantén flecha arriba hasta que se levante.") if a["pista"] else tr("Despegas."), True)
                self._tono_alt(10, a["techo"])
                return t
            v.vel = 0.0
            return sin
        if fase == "despegue":
            if a["pista"]:                                       # con carrera: sube mientras lleve velocidad; si la pierdes en el suelo, no has despegado
                if abs(v.vel) >= 0.3 * v.modelo["vel_max"]:
                    v.alt += a["ascenso"] * dt
                elif v.alt <= 0 and pygame.K_UP not in t and abs(v.vel) < 1.0:
                    v.fase = "tierra"
                    self.decir(tr("Despegue abortado. Mantén flecha arriba hasta que el aparato se levante."))
                    return sin
            else:
                v.alt += a["ascenso"] * dt
            if v.alt >= AJ("alt_despegue"):
                v.alt = AJ("alt_despegue")
                v.fase = "vuelo"
                self._tono_alt(v.alt, a["techo"])
                self.decir(tr('En el aire, a {int} metros. La D sube y la A baja.').format(int=(int(v.alt))))
            return t if v.alt >= 12 or a["pista"] else sin       # el helicóptero sube en vertical; la avioneta coge carrera
        if fase == "aterrizando":
            v.vel = max(0.0, v.vel - 12 * dt)
            antes = v.alt
            v.alt = max(0.0, v.alt - AJ("descenso") * dt)
            paso = AJ("paso_altura")
            if int(antes // paso) != int(v.alt // paso):
                self._tono_alt(v.alt, a["techo"])
            if v.alt <= 0:
                self._vuelo_toca_tierra(v)
            return sin
        if fase == "sin_motor":
            v.alt = max(0.0, v.alt - AJ("planeo") * dt)
            v.vel = max(v.vel - 2.5 * dt, min(v.vel, 14.0))
            if v.alt <= 0:
                self._vuelo_caida(v)
            return frozenset(k for k in t if k not in (pygame.K_UP,))
        # en vuelo
        antes = v.alt
        if pygame.K_d in t:
            v.alt = min(a["techo"], v.alt + a["ascenso"] * dt)
        elif pygame.K_a in t:
            v.alt = max(AJ("alt_minima"), v.alt - a["ascenso"] * 1.3 * dt)
        if v.alt != antes:
            paso = AJ("paso_altura")
            if int(antes // paso) != int(v.alt // paso):
                self._tono_alt(v.alt, a["techo"])
                m = int(round(v.alt / paso) * paso)
                if m % 100 == 0:
                    self.decir(tr('{m} metros.').format(m=(m)), True)
            alta = AJ("alt_alta")
            if antes < alta <= v.alt:
                self.decir(tr("Vuelo alto: desde el suelo ya no te siguen.") + (tr(" Pero el radar te ve.") if self.secuestro else ""))
            elif v.alt < alta <= antes:
                self.decir(tr("Vuelo bajo."))
            if v.alt >= a["techo"] and antes < a["techo"]:
                self.decir(tr('Techo del aparato: {int} metros. No sube más.').format(int=(int(a['techo']))))
            elif v.alt <= AJ("alt_minima") and antes > AJ("alt_minima"):
                self.decir(tr('{int} metros: más abajo, solo para aterrizar, con la F.').format(int=(int(v.alt))))
        if self.vuelo_con_combustible():
            self._vuelo_gastar(v, AJ("consumo_local") * dt / 60.0 * (0.4 + 0.6 * min(1.0, abs(v.vel) / max(1.0, v.modelo["vel_max"]))))
        return t

    def _vuelo_gastar(self, v, pct):
        """Gasta combustible, con sus avisos. Devuelve False cuando se acaba."""
        antes = v.queroseno
        v.queroseno = max(0.0, v.queroseno - pct)
        for umbral, clave, alarma in ((AJ("reserva"), "frases_reserva", False), (AJ("critico"), "frases_critico", True)):
            if antes > umbral >= v.queroseno:
                self.son("alarma_cabina" if alarma else "reserva", cat="interfaz", vol=0.7)
                self.decir(AJ.frase(clave, pct=int(round(v.queroseno))))
        if v.queroseno <= 0 and antes > 0 and getattr(v, "fase", "") in ("vuelo", "despegue"):
            v.fase = "sin_motor"
            self.son("motor_seco", cat="interfaz")
            self.son("alarma_cabina", cat="interfaz", vol=0.7)
            self.decir(AJ.frase("frases_sin_motor") + tr(" Dirige el aparato con izquierda y derecha hacia una calle o un espacio abierto."))
        return v.queroseno > 0

    def _campo_cerca(self, v, radio=None, pista=False):
        """El helipuerto, aeropuerto o aeródromo que el aparato tiene debajo, o None."""
        r = AJ("pista_radio") if radio is None else radio
        campos = [l for l in self.mundo.lugares.values() if l.tipo in CAMPOS and (not pista or l.tipo == "aeropuerto") and math.hypot(l.x - v.x, l.y - v.y) <= r]
        return min(campos, key=lambda l: math.hypot(l.x - v.x, l.y - v.y)) if campos else None

    def vuelo_aterrizar(self, v):
        """La F en el aire. Devuelve True si se ha encargado (aterriza, o dice por qué no)."""
        self.vuelo_prep(v)
        if v.fase == "tierra":
            return False
        if v.fase in ("aterrizando", "sin_motor"):
            self.decir(tr("Ya estás bajando."), True)
            return True
        if v.fase == "despegue":
            self.decir(tr("Estás despegando: espera a estar en el aire."), True)
            return True
        if abs(v.vel) > 3:
            self.decir(tr("Frena antes de aterrizar."), True)
            return True
        a = aeronave(v.modelo)
        if not self.mundo.transitable(v.x, v.y) and self.mundo.tipo != "mar":
            self.decir(tr("No puedes aterrizar aquí: debajo hay un edificio. Busca una calle o un espacio abierto; la tecla C te dice sobre qué estás."), True)
            return True
        if self.mundo.tipo == "mar" and not getattr(v, "_cheat_ground_model", {}).get("barco"):
            self.decir(tr("No puedes posarte sobre el mar."), True)
            return True
        v.forzoso = False
        if a["pista"] and self._campo_cerca(v, pista=True) is None:
            if self.t - getattr(v, "t_forzoso", -99) > 8:
                v.t_forzoso = self.t
                self.son("alarma_cabina", cat="interfaz", vol=0.6)
                self.decir(tr('Aquí no hay pista. {nombre} necesita la de un aeropuerto o un aeródromo; si bajas aquí será un aterrizaje forzoso y el aparato sufrirá. Pulsa F otra vez para hacerlo de todos modos.').format(nombre=(v.nombre)), True)
                return True
            v.forzoso = True
        v.fase = "aterrizando"
        v.bajar_al_tocar = True
        self.decir(tr('Desciendes desde {int} metros.').format(int=(int(v.alt))), True)
        return True

    def _vuelo_toca_tierra(self, v):
        v.alt, v.fase, v.vel = 0.0, "tierra", 0.0
        self.son("aterrizaje", vol=0.8)
        self.app.vibrar(0.5, 0.3, 250)
        if getattr(v, "forzoso", False):
            v.forzoso = False
            dano = v.salud_max * random.uniform(*sorted((AJ("forzoso_min"), AJ("forzoso_max")))) / 100.0
            if not self.cheat_repair(v):
                v.salud = max(1.0, v.salud - dano)
            self.son("choque", vol=0.7)
            self.decir(AJ.frase("frases_forzoso") + tr(' Estado, {int} por ciento.').format(int=(int(100 * v.salud / v.salud_max))))
        campo = self._campo_cerca(v)
        self.vuelo_al_posarse(v, campo)
        if getattr(v, "bajar_al_tocar", False) and self.j.veh is v:
            v.bajar_al_tocar = False
            self.salir_vehiculo()

    def _vuelo_caida(self, v):
        """Sin motor y sin altura: te posas como puedas o te estrellas, según lo que haya debajo."""
        v.alt, v.fase, v.vel = 0.0, "tierra", 0.0
        libre = self.mundo.transitable(v.x, v.y) and self.mundo.tipo != "mar"
        if not libre:
            v.x, v.y = self.mundo.punto_libre(v.x, v.y)
        pct = random.uniform(*sorted((AJ("forzoso_min"), AJ("forzoso_max")))) if libre else random.uniform(*sorted((AJ("caida_min"), AJ("caida_max"))))
        if not self.cheat_repair(v):
            v.salud = max(1.0, v.salud - v.salud_max * pct / 100.0)
        self.son("choque", vol=0.9)
        self.son("aterrizaje", vol=0.7)
        self.app.vibrar(1.0, 0.8, 600)
        self.decir(AJ.frase("frases_forzoso" if libre else "frases_caida") + tr(' Estado del aparato, {int} por ciento. No queda combustible: se pide desde el móvil, en Mis vehículos.').format(int=(int(100 * v.salud / v.salud_max))))
        if not libre:
            self.vuelo_herida(v)
        self.vuelo_al_posarse(v, None)

    def vuelo_herida(self, v):
        """Lo que te llevas tú en una caída: duele, pero no te mata."""
        dano = random.uniform(*sorted((AJ("caida_herida_min"), AJ("caida_herida_max"))))
        self.danar_jugador(min(dano, max(0.0, self.j.salud - 5.0)), (v.x, v.y))

    def vuelo_al_posarse(self, v, campo):
        """El aparato acaba de tocar tierra: lo que eso significa para un secuestro o para un vuelo comercial."""
        s = self.secuestro
        if s and s["veh"] is v:
            self._secuestro_al_posarse(v, campo)
        trab = self.vuelo_trabajo
        if trab and trab.get("veh") is v and campo is not None and campo.mapa == trab["destino_mapa"]:
            self._piloto_cobrar(campo)

    def vuelo_borde(self, v):
        """Has llegado volando al borde de la localidad: empieza la travesía, si quieres."""
        v.vel = 0.0
        if self.t - self._vuelo_borde_t < 4.0:
            return
        self._vuelo_borde_t = self.t
        if v.fase != "vuelo":
            self.decir(tr("Fin del mapa."))
            return
        from . import vuelo_pantalla
        vuelo_pantalla.plan_de_vuelo(self, None)

    def vuelo_destinos(self, v):
        """Las localidades a las que se puede volar con este aparato: [{"mapa", "campo", "km", "rumbo"}]. El campo es
        donde puede aterrizar (None si allí no hay sitio para él: solo se puede entrar volando bajo)."""
        a = aeronave(v.modelo)
        aqui = punto_aire(self.mundo.id)
        out = []
        for m in self.mapas.values():
            if m.id == self.mundo.id or m.tipo == "mar":
                continue
            campos = [l for l in m.lugares.values() if l.tipo in CAMPOS]
            if not campos:
                continue
            validos = [l for l in campos if l.tipo == "aeropuerto"] if a["pista"] else sorted(campos, key=lambda l: l.tipo != "helipuerto")
            alla = punto_aire(m.id)
            out.append({"mapa": m, "campo": validos[0] if validos else None, "campos": validos, "km": distancia(aqui, alla), "rumbo": rumbo_entre(aqui, alla)})
        return out

    def vuelo_alcance(self, v):
        """Kilómetros que puede hacer con lo que lleva."""
        if not self.vuelo_con_combustible():
            return 1e9
        self.vuelo_prep(v)
        return aeronave(v.modelo)["autonomia"] * v.queroseno / 100.0

    def vuelo_llegar(self, v, d):
        """Fin de la travesía (lo llama la pantalla de vuelo). d: {"mapa", "campo", "modo", "rumbo", "alt", "horas", "duro", "radar", "confort"}."""
        m, campo, modo = d["mapa"], d.get("campo"), d.get("modo", "campo")
        self.pasar_horas(max(0.05, float(d.get("horas", 0.3))))
        for cosa in (self.mision, self.trabajo):                 # una misión o un trabajo contra el reloj: la travesía también cuenta
            if cosa and cosa.get("limite") is not None:
                cosa["limite"] -= float(d.get("segundos", 0.0))
        s = self.secuestro
        if s and s["veh"] is v and not s["radar"] and self.j.estrellas:      # te perdió el radar por el camino: adonde llegas, nadie te busca
            self.limpiar_busqueda(hablar=False)
            self.decir(tr("Aquí nadie sabe nada de ti: has dejado atrás a los que te buscaban."))
        self.j.stats["travesias"] = self.j.stats.get("travesias", 0) + 1
        self.j.stats["km_volados"] = round(self.j.stats.get("km_volados", 0) + float(d.get("km", 0)), 1)
        self.vuelo_prep(v)
        if self.vuelo_trabajo and self.vuelo_trabajo.get("veh") is v:
            self.vuelo_trabajo["confort"] = self.vuelo_trabajo.get("confort", 0) + int(d.get("confort", 0))
        if modo == "campo" and campo is not None:
            x, y, di = m.plaza_junto_a(campo)
            self.cambiar_mapa(m.id, x, y, di * 90.0)
            v.alt, v.fase, v.vel = 0.0, "tierra", 0.0
            self.son("aterrizaje", vol=0.8)
            self.app.vibrar(0.5, 0.3, 250)
            if d.get("duro"):
                v.salud = max(1.0, v.salud - v.salud_max * AJ("duro_dano") / 100.0)
                self.decir(AJ.frase("frases_aterrizaje_duro", campo=campo.nombre) + tr(' Estado, {int} por ciento. Son las {hora_txt}.').format(int=(int(100 * v.salud / v.salud_max)), hora_txt=(self.hora_txt())))
            else:
                self.decir(AJ.frase("frases_aterrizaje", campo=campo.nombre) + tr(' Son las {hora_txt}. Con F te bajas; con Intro, el menú del campo.').format(hora_txt=(self.hora_txt())))
            self.vuelo_al_posarse(v, campo)
            return
        # entras volando bajo por el lado del que vienes
        rumbo = float(d.get("rumbo", 0)) % 360
        rad = math.radians(rumbo)
        cx, cy = m.ancho / 2.0, m.alto / 2.0
        k = min((cx - 12) / max(1e-6, abs(math.sin(rad))), (cy - 12) / max(1e-6, abs(math.cos(rad))))
        x, y = cx - math.sin(rad) * k, cy - math.cos(rad) * k
        self.cambiar_mapa(m.id, max(8.0, min(m.ancho - 8.0, x)), max(8.0, min(m.alto - 8.0, y)), rumbo)
        v.alt = max(AJ("alt_minima"), min(float(d.get("alt", 100)), aeronave(v.modelo)["techo"]))
        v.fase = "vuelo"
        v.vel = v.modelo["vel_max"] * 0.4
        s = self.secuestro
        if s and s["veh"] is v and s["radar"] and AJ("secuestro_llegada") >= 1:
            self.poner_busqueda(AJ.entero("secuestro_llegada"))
        self.decir(AJ.frase("frases_sobrevuelo", destino=m.nombre) + tr(' Vas a {int} metros, hacia el {cardinal}. Son las {hora_txt}.').format(int=(int(v.alt)), cardinal=(M.cardinal(rumbo)), hora_txt=(self.hora_txt())))

    # ------------------------------------------------------------------ combustible en tierra
    def vuelo_repostar(self, v):
        """Llena el depósito en un campo. Devuelve True si ha repostado."""
        self.vuelo_prep(v)
        falta = 100.0 - v.queroseno
        if falta < 1:
            self.decir(tr("El depósito está lleno."), True)
            return False
        precio = self.vuelo_precio_repostar(v)
        if not self.pagar(precio):
            return False
        v.queroseno = 100.0
        self.son("repostar", cat="interfaz")
        self.decir(tr('Depósito lleno. Con él puedes hacer unos {int} kilómetros. Te quedan {dinero} euros.').format(int=(int(aeronave(v.modelo)['autonomia'])), dinero=(self.j.dinero)), True)
        return True

    def vuelo_precio_repostar(self, v_o_pct):
        pct = v_o_pct if isinstance(v_o_pct, (int, float)) else getattr(v_o_pct, "queroseno", 100.0)
        return int(math.ceil((100.0 - float(pct)) / 10.0) * self.precio("queroseno", 60))

    def vuelo_traer_queroseno(self, v):
        """Desde el móvil: te traen combustible adonde esté el aparato, para poder despegar."""
        self.vuelo_prep(v)
        if v.queroseno >= 50:
            self.decir(tr("Todavía le queda más de medio depósito."), True)
            return False
        if not self.pagar(self.precio("queroseno_domicilio", 450)):
            return False
        v.queroseno = 50.0
        self.son("repostar", cat="interfaz")
        self.decir(tr('Un camión cisterna llega hasta {nombre} y le echa medio depósito.').format(nombre=(v.nombre)), True)
        return True

    # ------------------------------------------------------------------ hangares
    def hangar(self, l, crear=False):
        h = self.j.hangares.get(l.id)
        if not isinstance(h, dict):
            if not crear:
                return None
            h = self.j.hangares[l.id] = {"propia": False, "naves": [], "pagado": self.dia, "debe": 0}
        h.setdefault("propia", False)
        h.setdefault("debe", 0)
        h.setdefault("pagado", self.dia)
        h["naves"] = [x for x in (h.get("naves") if isinstance(h.get("naves"), list) else []) if isinstance(x, dict) and x.get("modelo")]
        return h

    def hangares_naves(self):
        """Todas tus aeronaves guardadas: [(lugar, hangar, ficha)]."""
        out = []
        for pid in list(self.j.hangares):
            l = self.lug(pid)
            h = self.hangar(l) if l is not None else None
            if h:
                out += [(l, h, d) for d in h["naves"]]
        return out

    def hangar_precio_compra(self, l):
        return int(l.get("hangar_precio", 0) or 0) or self.precio("hangar_compra", 26000)

    def hangar_plazas(self):
        return AJ.entero("hangar_plazas")

    def hangar_motivo(self, l, v=None):
        """Por qué no cabe una aeronave más en ese hangar, o vacío."""
        h = self.hangar(l)
        if h is None:
            return tr("Aquí no tienes plaza de hangar: alquílala o cómprala en este mismo campo.")
        if h["debe"] > 0:
            return tr('Debes {debe} euros de alquiler de este hangar. Págalos antes.').format(debe=(h['debe']))
        if len(h["naves"]) >= AJ.entero("hangar_plazas"):
            return tr("El hangar está lleno.")
        if len(self.hangares_naves()) >= AJ.entero("hangar_tope"):
            return tr('No puedes tener más de {entero} aeronaves guardadas entre todos tus hangares.').format(entero=(AJ.entero('hangar_tope')))
        if v is not None:
            if not v.modelo.get("vuela"):
                return tr("En un hangar solo se guardan aeronaves.")
            if v.tag or getattr(v, "secuestrado", False):
                return self.motivo_ajeno(v) if v.tag != "secuestro" else tr("Un aparato robado no se puede guardar aquí: está denunciado en toda la comarca.")
            if aeronave(v.modelo)["pista"] and l.tipo != "aeropuerto":
                return tr('{nombre} necesita pista: no cabe en un helipuerto.').format(nombre=(v.nombre))
        return ""

    def hangar_contratar(self, l, comprar):
        h = self.hangar(l)
        if h is not None and (h["propia"] or not comprar):
            return False
        precio = self.hangar_precio_compra(l) if comprar else self.precio("hangar_alquiler", 120)
        if not self.pagar(precio):
            return False
        h = self.hangar(l, crear=True)
        h["propia"], h["pagado"], h["debe"] = bool(comprar), self.dia, 0
        self.son("caja", cat="interfaz")
        self.j.stats["hangares"] = len(self.j.hangares)
        self.decir((tr('La plaza de hangar de {nombre} es tuya.').format(nombre=(l.nombre)) if comprar else tr('Plaza de hangar alquilada en {nombre}: {precio} euros al día, que se cobran cada medianoche.').format(nombre=(l.nombre), precio=(precio)))
                   + tr(' Caben {entero} aeronaves.').format(entero=(AJ.entero('hangar_plazas'))), True)
        return True

    def hangar_dejar(self, l):
        """Dejas de alquilar una plaza vacía."""
        h = self.hangar(l)
        if h is None or h["propia"]:
            return False
        if h["naves"]:
            self.app.son("error")
            self.decir(tr("Saca antes las aeronaves que tienes dentro."), True)
            return False
        if h["debe"] > 0 and not self.pagar(h["debe"]):
            return False
        del self.j.hangares[l.id]
        self.decir(tr('Dejas la plaza de hangar de {nombre}.').format(nombre=(l.nombre)), True)
        return True

    def _ficha_nave(self, v):
        d = self._ficha_garaje(v)
        d["queroseno"] = round(float(getattr(v, "queroseno", 100.0)), 1)
        return d

    def hangar_guardar(self, l, v, callar=False):
        """Mete en el hangar una aeronave que está en el campo (o la que llevas). True si queda guardada."""
        motivo = self.hangar_motivo(l, v)
        if motivo:
            if not callar:
                self.app.son("error")
                self.decir(motivo, True)
            return False
        self.vuelo_prep(v)
        if self.j.veh is v:
            if getattr(v, "fase", "tierra") != "tierra":
                if not callar:
                    self.app.son("error")
                    self.decir(tr("Aterriza antes."), True)
                return False
            self.salir_vehiculo(forzado=True)
        self.hangar(l)["naves"].append(self._ficha_nave(v))
        if self.ultimo_veh is v:
            self.ultimo_veh = None
        self.quitar_vehiculo(v)
        if not callar:
            self.son("puerta_entrar", cat="interfaz")
            self.decir(tr('{nombre} queda en el hangar de {nombre2}. Aquí no se pierde.').format(nombre=(v.nombre), nombre2=(l.nombre)), True)
        return True

    def hangar_sacar(self, l, d):
        """Saca una aeronave del hangar a la pista. Devuelve el vehículo."""
        h = self.hangar(l)
        if h is None or d not in h["naves"]:
            return None
        if h["debe"] > 0:
            self.app.son("error")
            self.decir(tr('Debes {debe} euros de alquiler de este hangar. Hasta que pagues, no te dejan sacar nada.').format(debe=(h['debe'])), True)
            return None
        if l.mapa != self.mundo.id:
            self.app.son("error")
            self.decir(tr('Esa aeronave está en {nombre_lugar}: ve allí a por ella.').format(nombre_lugar=(self.nombre_lugar(l))), True)
            return None
        h["naves"].remove(d)
        x, y, di = self.mundo.plaza_junto_a(l)
        v = self._veh_de_dict(dict(d, rumbo=di * 90.0), x, y)
        v.dir = di
        v.cerrado = False
        self.vuelo_prep(v)
        self.hacer_mio(v, callar=True)
        self.son("puerta_salir", cat="interfaz")
        self.fijar_gps(x, y, v.nombre, auto=True, radio=4, callar=True)
        self.decir(tr('Sacan {nombre} a la pista. {situar}. Sube con F.').format(nombre=(v.nombre), situar=(self.situar(x, y, tr('Está')))), True)
        return v

    def hangar_revisar(self, d):
        """Mantenimiento de una aeronave guardada: la repara. Cobra según el daño."""
        from . import misvehiculos
        smax = misvehiculos._salud_max(self, d["modelo"], d.get("mejoras"))
        falta = max(0.0, 1.0 - float(d.get("salud", smax)) / smax)
        if falta < 0.01:
            self.decir(tr("Está en perfecto estado."), True)
            return False
        if not self.pagar(self.hangar_precio_revision(d)):
            return False
        d["salud"] = smax
        self.son("reparar", cat="interfaz")
        self.decir(tr('Revisada y reparada: como nueva. Te quedan {dinero} euros.').format(dinero=(self.j.dinero)), True)
        return True

    def hangar_precio_revision(self, d):
        from . import misvehiculos
        smax = misvehiculos._salud_max(self, d["modelo"], d.get("mejoras"))
        falta = max(0.0, 1.0 - float(d.get("salud", smax)) / smax)
        return int(math.ceil(falta * 10.0) * self.precio("hangar_revision", 90))

    def hangar_repostar(self, d):
        pct = float(d.get("queroseno", 100.0))
        if pct >= 99:
            self.decir(tr("El depósito está lleno."), True)
            return False
        if not self.pagar(self.vuelo_precio_repostar(pct)):
            return False
        d["queroseno"] = 100.0
        self.son("repostar", cat="interfaz")
        self.decir(tr('Depósito lleno. Te quedan {dinero} euros.').format(dinero=(self.j.dinero)), True)
        return True

    def hangar_destinos(self, cosa):
        """Los hangares tuyos adonde se puede mandar esa aeronave (un vehículo o su ficha)."""
        modelo = self.modelos.get(cosa["modelo"]) if isinstance(cosa, dict) else cosa.modelo
        pista = bool(modelo) and aeronave(modelo)["pista"]
        out = []
        for pid in self.j.hangares:
            l = self.lug(pid)
            if l is not None and self.hangar(l) is not None and (not pista or l.tipo == "aeropuerto"):
                out.append(l)
        return out

    def mandar_al_hangar(self, cosa, l):
        """Un piloto de la casa se lleva tu aeronave a un hangar tuyo, esté donde esté. True si se la lleva."""
        es_ficha = isinstance(cosa, dict)
        h = self.hangar(l)
        if not es_ficha and cosa is self.j.veh and getattr(cosa, "fase", "tierra") != "tierra":
            self.app.son("error")
            self.decir(tr("Aterriza antes."), True)
            return False
        motivo = self.hangar_motivo(l, None if es_ficha else cosa)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        if not self.pagar(self.precio("mandar_hangar", 250)):
            return False
        if es_ficha:
            if cosa in self.mis_lejos:
                self.mis_lejos.remove(cosa)
            d = {k: cosa[k] for k in ("modelo", "salud", "nombre", "mejoras", "queroseno", "km", "pinchada", "revision") if k in cosa}
            d.setdefault("queroseno", 100.0)
            h["naves"].append(d)
            nombre = cosa.get("nombre") or self.modelos[cosa["modelo"]]["nombre"]
        else:
            self.vuelo_prep(cosa)
            if self.j.veh is cosa:
                self.salir_vehiculo(forzado=True)
            h["naves"].append(self._ficha_nave(cosa))
            if self.ultimo_veh is cosa:
                self.ultimo_veh = None
            nombre = cosa.nombre
            self.quitar_vehiculo(cosa)
        self.son("motor_avioneta" if (self.modelos.get(h["naves"][-1]["modelo"]) or {}).get("motor") == "motor_avioneta" else "motor_helicoptero", vol=0.4, cat="interfaz")
        self.decir(tr('Un piloto de la casa se lleva {nombre} al hangar de {nombre_lugar}.').format(nombre=(nombre), nombre_lugar=(self.nombre_lugar(l))), True)
        return True

    def _hangares_dia(self):
        """Cada medianoche: el alquiler de las plazas. Si no llega, se apunta la deuda y, pasados unos días, no te dejan sacar nada hasta pagar."""
        j = self.j
        for pid in list(j.hangares):
            l = self.lug(pid)
            h = self.hangar(l) if l is not None else None
            if h is None:
                j.hangares.pop(pid, None)
                continue
            if h["propia"]:
                continue
            dias = max(0, self.dia - int(h.get("pagado", self.dia)))
            if dias <= 0:
                continue
            h["pagado"] = self.dia
            cuota = dias * self.precio("hangar_alquiler", 120)
            if h["debe"] <= 0 and j.dinero >= cuota:
                j.dinero -= cuota
                self.decir(tr('Pagas {cuota} euros por la plaza de hangar de {nombre_lugar}.').format(cuota=(cuota), nombre_lugar=(self.nombre_lugar(l))))
            else:
                h["debe"] += cuota
                self.son("factura", cat="interfaz", vol=0.5)
                self.decir(tr('No has pagado el hangar de {nombre_lugar}: debes {debe} euros. Tus aeronaves siguen allí, pero no te dejan sacarlas hasta que pagues.').format(nombre_lugar=(self.nombre_lugar(l)), debe=(h['debe'])))
                if not h["naves"] and h["debe"] >= AJ("hangar_impago") * self.precio("hangar_alquiler", 120) and AJ("hangar_impago") > 0:
                    del j.hangares[pid]
                    self.decir(tr('Te quitan la plaza de {nombre_lugar}, que estaba vacía.').format(nombre_lugar=(self.nombre_lugar(l))))

    def hangar_pagar_deuda(self, l):
        h = self.hangar(l)
        if h is None or h["debe"] <= 0 or not self.pagar(h["debe"]):
            return False
        h["debe"] = 0
        self.son("caja", cat="interfaz")
        self.decir(tr("Deuda pagada. Ya puedes sacar tus aeronaves."), True)
        return True

    # ------------------------------------------------------------------ radar y secuestro
    def radar_te_tiene(self):
        """Has secuestrado un aparato y el radar te sigue: mientras sea así, no hay quien despiste a la policía."""
        s = self.secuestro
        return bool(s and s["radar"] and self.j.veh is s["veh"] and getattr(s["veh"], "fase", "tierra") != "tierra")

    def secuestro_motivo(self, l):
        if self.en_servidor or self.online_activo():
            return tr("En un servidor en línea y jugando con amigos no se secuestran aeronaves: la policía y el dinero los lleva el servidor.")
        if not self.vuelo_real():
            return tr("Para secuestrar un aparato hace falta el vuelo real, que tienes apagado en Opciones, Movimiento y conducción.")
        if self.secuestro:
            return tr("Ya tienes un aparato secuestrado.")
        if self.j.veh:
            return tr("Bájate del vehículo.")
        if self.mision or self.trabajo or self.guerra or self.vuelo_trabajo:
            return tr("Termina antes lo que tienes entre manos.")
        if self.de_servicio():
            return tr("Estás de servicio. Si haces eso, se acabó la placa.")
        if self.arma()["tipo"] != "fuego":
            return tr("Para secuestrar un aparato tienes que empuñar un arma de fuego.")
        if self.j.stats.get("secuestro_dia") == self.dia and self.j.stats.get("secuestro_en") == l.id:
            return tr("Después de lo de hoy, aquí hay más policías que pasajeros. Vuelve otro día.")
        return ""

    def secuestro_modelo(self, l):
        """Qué aparato de línea sale de ese campo."""
        candidatos = ["helicoptero"] if l.tipo == "helipuerto" else ["avioneta", "helicoptero"]
        return next((m for m in candidatos if m in self.modelos), next((m["id"] for m in self.modelos.values() if m.get("vuela")), None))

    def secuestro_encargo(self, l):
        """El encargo del día en ese campo: alguien paga por el aparato entregado en un sitio discreto de otra localidad.
        Siempre el mismo ese día y en ese campo. None si no hay adónde llevarlo."""
        rng = random.Random(f"secuestro:{self.j.semilla}:{self.dia}:{l.id}")
        modelo = self.modelos.get(self.secuestro_modelo(l) or "")
        if modelo is None:
            return None
        tipos = AJ.lista("sitios_discretos")
        ops = []
        for m in self.mapas.values():
            if m.id == self.mundo.id or m.tipo == "mar" or not any(q.tipo in CAMPOS for q in m.lugares.values()):
                continue
            campos = [q for q in m.lugares.values() if q.tipo in CAMPOS]
            sitios = [q for q in m.lugares.values() if q.tipo in tipos and all(math.hypot(q.x - c.x, q.y - c.y) > 120 for c in campos)]
            sitios = sitios or [q for q in m.lugares.values() if q.tipo not in CAMPOS + ("comisaria", "salida", "muelle", "embarcadero") and all(math.hypot(q.x - c.x, q.y - c.y) > 120 for c in campos)]
            if sitios:
                ops.append((m, sorted(sitios, key=lambda q: q.id)))
        if not ops:
            return None
        ops.sort(key=lambda e: e[0].id)
        m, sitios = rng.choice(ops)
        sitio = rng.choice(sitios)
        km = distancia(punto_aire(self.mundo.id), punto_aire(m.id))
        paga = int(rng.uniform(*sorted((AJ("encargo_min"), AJ("encargo_max")))) // 50 * 50)
        return {"mapa": m.id, "lugar": sitio.id, "paga": paga, "km": km}

    def secuestrar(self, l, encargo=None):
        """Secuestras el aparato de línea que iba a salir. Devuelve el vehículo, o None."""
        motivo = self.secuestro_motivo(l)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return None
        modelo = self.secuestro_modelo(l)
        if modelo is None:
            return None
        j = self.j
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        self.salir_interior(silencio=True)
        x, y, di = self.mundo.plaza_junto_a(l)
        v = self.crear_vehiculo(modelo, x, y, di, None, tr('{nombre} de línea').format(nombre=(self.modelos[modelo]['nombre'])), "secuestro")
        v.propio, v.cerrado, v.secuestrado = True, False, True
        self.vuelo_prep(v)
        v.queroseno = random.uniform(70, 100)
        self.son("grito", vol=0.5)
        self._subir(v, False, callar=True)
        nivel = AJ.entero("secuestro_busqueda")
        if self.heli_activo():                                   # con el helicóptero de la policía encendido, viene a por ti
            from . import calle
            nivel = max(nivel, int(calle.aj("helicoptero_nivel")))
        self.secuestro = {"veh": v, "radar": True, "bajo": 0.0, "encargo": dict(encargo) if encargo else None, "origen": l.id}
        j.stats["secuestros"] = j.stats.get("secuestros", 0) + 1
        j.stats["secuestro_dia"], j.stats["secuestro_en"] = self.dia, l.id
        self.cambiar_reputacion(4)
        self.hon_antecedente(AJ.entero("secuestro_gravedad"), tr('secuestro de una aeronave en {nombre}').format(nombre=(l.nombre)))
        self.decir(AJ.frase("frases_secuestro") + " " + self.vuelo_texto_subir(v).strip(), True)
        self.poner_busqueda(min(5, nivel))
        self.son("alarma", xy=(l.x, l.y), ref=10, maxd=160, vol=0.5)
        self.decir(AJ.frase("frases_radar", alt=AJ.entero("alt_alta")) + tr(" Si aterrizas en un helipuerto o en un aeropuerto mientras te siga, te estarán esperando."))
        if encargo:
            dest = self.lug(encargo["lugar"])
            self.decir(tr('El encargo: déjalo junto a {nombre}, en {nombre2}, sin el radar encima. Pagan {paga} euros. La tecla O te lo recuerda.').format(nombre=(dest.nombre), nombre2=(self.mapas[encargo['mapa']].nombre), paga=(encargo['paga'])))
        return v

    def secuestro_txt(self):
        s = self.secuestro
        if not s:
            return ""
        t = tr("Llevas un aparato secuestrado. ") + (tr("El radar te sigue: vuela por debajo de ") + str(AJ.entero("alt_alta")) + tr(" metros un rato para que te pierda. ") if s["radar"] else tr("El radar te ha perdido. "))
        e = s.get("encargo")
        if e:
            dest = self.lug(e["lugar"])
            if dest is not None:
                donde = self.situar(dest.x, dest.y, tr("Queda")) if dest.mapa == self.mundo.id else tr('Está en {nombre}').format(nombre=(self.mapas[e['mapa']].nombre))
                t += tr('Encargo: dejarlo junto a {nombre}, sin el radar encima, por {paga} euros. {donde}.').format(nombre=(dest.nombre), paga=(e['paga']), donde=(donde))
        else:
            t += tr("Aterriza lejos de helipuertos y aeropuertos, o te reconocerán.")
        return t

    def _secuestro_paso(self, dt):
        s = self.secuestro
        if not s:
            return
        v = s["veh"]
        j = self.j
        if v.muerto or v not in self.vehiculos:
            self.secuestro = None
            return
        if j.veh is not v:
            if v.dist(*self.pos()) > 90:                         # lo has abandonado: ya no es cosa tuya
                self.secuestro = None
                if v.sirena is not None:
                    v.sirena.parar()
                self.quitar_vehiculo(v)
            return
        if getattr(v, "fase", "tierra") in ("tierra",):
            return
        alta = v.alt >= AJ("alt_alta")
        if s["radar"]:
            s["bajo"] = 0.0 if alta else s["bajo"] + dt
            if s["bajo"] >= AJ("radar_pierde"):
                self.radar_perdido()
        elif alta:
            s["radar"], s["bajo"] = True, 0.0
            self.son("alarma_cabina", cat="interfaz", vol=0.5)
            self.decir(AJ.frase("frases_radar_otra_vez"))

    def radar_perdido(self):
        s = self.secuestro
        if s and s["radar"]:
            s["radar"], s["bajo"] = False, 0.0
            self.son("policia_perdida", cat="interfaz", vol=0.6)
            self.decir(AJ.frase("frases_radar_perdido") + tr(" No subas por encima de ") + str(AJ.entero("alt_alta")) + tr(" metros o volverán a verte."))

    def _secuestro_al_posarse(self, v, campo):
        s = self.secuestro
        e = s.get("encargo")
        if campo is not None:                                    # en un campo oficial: con el radar encima te esperan; sin él, reconocen el aparato
            if s["radar"]:
                self.son("sirena", xy=(campo.x, campo.y), ref=12, maxd=200, vol=0.6)
                self.decir(AJ.frase("frases_te_esperan", campo=campo.nombre))
                self.poner_busqueda(min(5, AJ.entero("secuestro_espera")))
                self.j.stats["secuestros_esperado"] = self.j.stats.get("secuestros_esperado", 0) + 1
            elif AJ("secuestro_reconocen") >= 1:
                self.decir(AJ.frase("frases_reconocen", campo=campo.nombre))
                self.poner_busqueda(min(5, AJ.entero("secuestro_reconocen")))
        if e:
            dest = self.lug(e["lugar"])
            if dest is not None and dest.mapa == self.mundo.id and math.hypot(dest.x - v.x, dest.y - v.y) <= AJ("encargo_radio"):
                if s["radar"]:
                    self.son("error")
                    self.decir(AJ.frase("frases_encargo_radar"))
                    s["encargo"] = None
                else:
                    self.secuestro = None
                    if self.j.veh is v:
                        self.salir_vehiculo(forzado=True)
                    self.quitar_vehiculo(v)
                    self.hon_negro(e["paga"])
                    self.dar_dinero(int(e["paga"]))
                    self.j.stats["secuestros_entregados"] = self.j.stats.get("secuestros_entregados", 0) + 1
                    self.app.son("mision_ok")
                    self.cambiar_reputacion(3)
                    self.decir(AJ.frase("frases_encargo_hecho", paga=e["paga"]) + tr(' Tienes {dinero}.').format(dinero=(self.j.dinero)))

    # ------------------------------------------------------------------ vuelos comerciales
    def piloto_motivo(self, l=None):
        if self.en_servidor or self.online_activo():
            return tr("En un servidor en línea y jugando con amigos no hay vuelos comerciales: el dinero lo arbitra el servidor.")
        if not self.vuelo_real():
            return tr("Los vuelos comerciales necesitan el vuelo real, que tienes apagado en Opciones, Movimiento y conducción.")
        if "piloto" not in self.hon_titulos() and self.hon_titulo("piloto") is not None:
            return tr('Para volar con pasaje o con carga hace falta la {lower}. Se saca en una academia, sesión a sesión.').format(lower=(self.hon_titulo_nombre('piloto').lower()))
        if self.j.estrellas:
            return tr("Con la policía buscándote, la compañía no te deja ni acercarte a la pista.")
        if self.mision or self.trabajo or self.guerra or self.secuestro:
            return tr("Termina antes lo que tienes entre manos.")
        return ""

    def piloto_ofertas(self, l):
        """Los vuelos que ofrece hoy ese campo: los mismos todo el día, distintos cada día y en cada campo."""
        rng = random.Random(f"piloto:{self.j.semilla}:{self.dia}:{l.id}")
        aqui = punto_aire(self.mundo.id)
        destinos = []
        for m in self.mapas.values():
            if m.id == self.mundo.id or m.tipo == "mar":
                continue
            campos = sorted((q for q in m.lugares.values() if q.tipo in CAMPOS), key=lambda q: q.id)
            if campos:
                destinos.append((m, campos))
        destinos.sort(key=lambda e: e[0].id)
        out = []
        rng.shuffle(destinos)
        for k, (m, campos) in enumerate(destinos[:AJ.entero("vuelo_ofertas")]):
            campo = rng.choice(campos)
            pasaje = rng.random() < 0.55
            que = rng.choice(AJ.lista("pasajes" if pasaje else "cargas"))
            km = distancia(aqui, punto_aire(m.id))
            paga = int((AJ("vuelo_base") + AJ("vuelo_km") * km) * rng.uniform(0.9, 1.25) // 10 * 10)
            # a un helipuerto solo llega un helicóptero; desde un helipuerto solo sale un helicóptero
            heli = campo.tipo == "helipuerto" or l.tipo == "helipuerto"
            out.append({"n": k, "pasaje": pasaje, "que": que, "destino": campo.id, "destino_mapa": m.id, "km": km, "paga": paga, "heli": heli})
        return out

    def piloto_aceptar(self, l, o):
        motivo = self.piloto_motivo(l)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        if self.vuelo_trabajo:
            self.app.son("error")
            self.decir(tr("Ya tienes un vuelo comercial entre manos."), True)
            return False
        dest = self.lug(o["destino"])
        mio = self.j.veh if self.volando() else next((v for v in self.vehiculos if v.modelo.get("vuela") and self.es_mio(v) and not v.muerto and v.dist(l.x, l.y) <= 90), None)
        if mio is not None and ((o["heli"] and aeronave(mio.modelo)["pista"]) or (aeronave(mio.modelo)["pista"] and dest.tipo != "aeropuerto")):
            mio = None                                           # el tuyo no vale para ese trayecto: te dejan uno de la compañía
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        self.salir_interior(silencio=True)
        propio = mio is not None
        if mio is None:
            modelo = "helicoptero" if o["heli"] or "avioneta" not in self.modelos else "avioneta"
            x, y, di = self.mundo.plaza_junto_a(l)
            mio = self.crear_vehiculo(modelo, x, y, di, None, tr('{nombre} de la compañía').format(nombre=(self.modelos[modelo]['nombre'])), "compania")
            mio.propio, mio.cerrado = True, False
            self.vuelo_prep(mio)
            mio.sirena = self.son("loc_vehiculo", bucle=True, xy=(x, y), ref=5, maxd=70)
            self.fijar_gps(x, y, mio.nombre, auto=True, radio=4, callar=True)
        self.vuelo_prep(mio)
        self.vuelo_trabajo = {"destino": dest.id, "destino_mapa": dest.mapa, "paga": int(o["paga"]), "que": o["que"], "pasaje": bool(o["pasaje"]), "km": o["km"], "veh": mio,
                              "propio": propio, "confort": 0, "origen": l.id, "n": o["n"], "dia": self.dia}
        self.son("notificacion", cat="interfaz")
        self.decir(tr('{que}: {v} para {nombre}, en {nombre2}. ').format(que=(o['que']), v=(tr('pasaje') if o['pasaje'] else tr('carga')), nombre=(dest.nombre), nombre2=(self.mapas[dest.mapa].nombre))
                   + AJ.frase("frases_piloto_sale", destino=self.mapas[dest.mapa].nombre)
                   + (tr(" Vuelas con tu aparato: te pagan un suplemento.") if propio else tr(' Te dejan {nombre}: {situar}. Sube con F.').format(nombre=(mio.nombre), situar=(self.situar(mio.x, mio.y, 'está'))))
                   + tr(" Despega, sal de la localidad y aterriza en ese campo. La tecla O te lo recuerda."), True)
        return True

    def piloto_txt(self):
        trab = self.vuelo_trabajo
        if not trab:
            return ""
        dest = self.lug(trab["destino"])
        if dest is None:
            return ""
        donde = self.situar(dest.x, dest.y, tr("Queda")) if dest.mapa == self.mundo.id else tr('Está a {km_txt} kilómetros, rumbo {rumbo_txt}').format(km_txt=(km_txt(distancia(punto_aire(self.mundo.id), punto_aire(dest.mapa)))), rumbo_txt=(rumbo_txt(rumbo_entre(punto_aire(self.mundo.id), punto_aire(dest.mapa)))))
        return tr('Vuelo comercial: {lower}, hasta {nombre_lugar}. {donde}. Pagan {paga} euros al aterrizar allí.').format(lower=(trab['que'].lower()), nombre_lugar=(self.nombre_lugar(dest)), donde=(donde), paga=(trab['paga']))

    def piloto_dejar(self, texto=tr("Dejas el vuelo comercial. La compañía busca a otro piloto.")):
        trab = self.vuelo_trabajo
        if not trab:
            return
        self.vuelo_trabajo = None
        v = trab["veh"]
        if not trab["propio"] and v is not None and not v.muerto and v in self.vehiculos:
            if self.j.veh is v and getattr(v, "fase", "tierra") == "tierra":
                self.salir_vehiculo(forzado=True)
            if self.j.veh is not v:
                self.quitar_vehiculo(v)
            else:
                v.tag = "compania_devolver"
        if texto:
            self.decir(texto, True)

    def _piloto_cobrar(self, campo):
        trab = self.vuelo_trabajo
        if campo.id != trab["destino"] and campo.mapa == trab["destino_mapa"]:
            self.decir(tr('Este no es el campo: el encargo es para {nombre}.').format(nombre=(self.lug(trab['destino']).nombre)))
            return
        self.vuelo_trabajo = None
        v = trab["veh"]
        paga = trab["paga"]
        if trab["propio"]:
            paga += int(paga * AJ("vuelo_propio") / 100.0)
        extra = int(trab["paga"] * AJ("vuelo_confort") / 100.0)
        texto = AJ.frase("frases_piloto_llega", paga=paga, destino=campo.nombre)
        if extra and trab.get("confort", 0) == 0:
            paga += extra
            texto += " " + AJ.frase("frases_piloto_propina", extra=extra)
        elif extra and trab.get("confort", 0) >= 2:
            paga -= extra
            texto += " " + AJ.frase("frases_piloto_queja", extra=extra)
        self.dar_dinero(paga)
        self.j.stats["vuelos_comerciales"] = self.j.stats.get("vuelos_comerciales", 0) + 1
        self.atracadas[f"vuelo:{trab['origen']}:{trab['n']}"] = trab["dia"]      # ese encargo, hoy, ya está hecho
        if AJ("vuelo_prestigio") > 0:
            self.cambiar_ciudadania(AJ("vuelo_prestigio"))
        self.app.son("mision_ok")
        self.decir(texto + tr(' Tienes {dinero}.').format(dinero=(self.j.dinero)))
        if not trab["propio"] and v is not None and not v.muerto:
            if self.j.veh is v:
                self.salir_vehiculo(forzado=True)
            self.quitar_vehiculo(v)
            self.decir(tr("Entregas el aparato de la compañía en el hangar."))

    def _piloto_paso(self, dt):
        trab = self.vuelo_trabajo
        if not trab:
            return
        v = trab["veh"]
        if v is None or v.muerto or v not in self.vehiculos:
            self.vuelo_trabajo = None
            self.son("mision_fallo", cat="interfaz")
            self.decir(tr("Te has quedado sin aparato: el vuelo comercial se cancela."))
            return
        if self.j.estrellas >= 2:
            self.piloto_dejar(tr("Con la policía detrás, la compañía te quita el vuelo."))

    # ------------------------------------------------------------------ cada fotograma y cada día
    def actualizar_vuelo(self, dt):
        if self._vuelo_dia != self.dia:
            if self._vuelo_dia is not None:
                self._hangares_dia()
            self._vuelo_dia = self.dia
        self._secuestro_paso(dt)
        self._piloto_paso(dt)
        for o in [o for o in self.vehiculos if o.tag == "compania_devolver" and o is not self.j.veh]:
            self.quitar_vehiculo(o)

    def vuelo_objetivo_txt(self):
        """Lo que añade la tecla del objetivo cuando llevas un secuestro o un vuelo comercial."""
        return self.piloto_txt() or self.secuestro_txt()
