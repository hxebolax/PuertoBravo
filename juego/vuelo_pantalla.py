"""La travesía en vuelo entre localidades, y los menús de volar: plan de vuelo, campo, hangar, vuelos comerciales y secuestro.

La travesía es una pantalla que se juega de oído. El aparato tiene posición en el mapa de la comarca, rumbo, altitud y
combustible; hay viento, la torre habla por la radio, pasan cosas (turbulencias, tráfico, tormentas) y al final hay que
bajar y encarar el campo. Con el piloto automático no hay que hacer nada, y se puede acelerar.

Teclas (las mismas que tiene el mando en cualquier pantalla): flechas arriba y abajo, altitud; izquierda y derecha,
rumbo; Tabulador, piloto automático; Intro, cómo va el vuelo; N, acelerar; Inicio, la torre; D o Escape, el menú de
vuelo; F1, la ayuda.
"""
from .i18n import tr
import math
import random

import pygame

from . import mundo as M
from . import vuelo as V
from .menus import Menu, Opcion

AJ = V.AJ
LADOS = {True: "derecha", False: "izquierda"}


def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


def _viento_txt(kmh, de):
    if kmh < 4:
        return "calma"
    return tr('{int} kilómetros por hora del {cardinal}').format(int=(int(round(kmh))), cardinal=(M.cardinal(de)))


class Crucero:
    """La travesía. Se abre con el aparato ya en el aire, o despegando de un campo."""
    pausa_mundo = True

    def __init__(self, p, v, destino, modo="campo", campo_origen=None):
        self.p, self.app, self.v = p, p.app, v
        self.a = V.aeronave(v.modelo)
        p.vuelo_prep(v)
        self.origen = p.mundo
        self.pos = list(V.punto_aire(p.mundo.id))
        self.km_hechos = 0.0
        self.t = 0.0                     # segundos de verdad
        self.t_vuelo = 0.0               # segundos de vuelo, ya comprimidos
        self.despega = campo_origen
        self.alt = float(v.alt) if v.fase == "vuelo" else 0.0
        self.viento_kmh = random.uniform(0, AJ("viento_max")) * (AJ("viento_lluvia") / 100.0 if p.lluvia else 1.0)
        self.viento_de = random.uniform(0, 360)                  # de dónde sopla
        self.auto = True
        self.asistido = bool(p.cfg["vuelo_asistido"])
        self.rapido = False
        self.hecho = False
        self.fase = "ascenso"
        self.frustradas = 0
        self.guiada = False
        self.duro = False
        self.confort = 0
        self.ultima_torre = ""
        self.canales = []
        self.motor = None
        self.t_baliza = 0.0
        self.suceso = None               # lo que está pasando ahora: {"tipo", ...}
        self.tormenta = None             # {"c": (x, y), "r": km, "dentro": bool, "modo"}
        self.via = None                  # un punto de paso para rodear algo
        self.t_obstaculo = None
        self.obstaculo = None
        self.paisajes = set()
        self.bajo_dicho = False
        self.sin_motor = False
        self._poner_destino(destino, modo)
        self.rumbo = V.rumbo_entre(self.pos, self.meta)
        self.alt_obj = self._nivel()
        self._plan_sucesos()

    # ------------------------------------------------------------- destino y sucesos
    def _poner_destino(self, destino, modo):
        self.destino = destino           # {"mapa", "campo", "campos", "km", "rumbo"}
        self.meta = V.punto_aire(destino["mapa"].id)
        self.modo = modo if destino.get("campo") is not None else "bajo"
        self.campo = destino.get("campo")
        self.fase = "ascenso" if self.fase in ("ascenso",) else "crucero"
        self.aprox_dicha = False
        self.final_dicho = False

    def _nivel(self):
        """La altitud de crucero para este tramo: la del aparato, o menos si el trayecto es corto y no da tiempo a subir tanto."""
        paso = AJ("paso_crucero")
        corto = max(AJ("alt_alta") + paso, round(V.distancia(self.pos, self.meta) * AJ("nivel_km") / paso) * paso)
        return min(self.a["alt_crucero"], self.a["techo"], corto)

    def _plan_sucesos(self):
        """Lo que va a pasar en este tramo, sorteado: a qué distancia de la salida ocurre cada cosa."""
        total = V.distancia(self.pos, self.meta)
        vel = self.a["crucero"] / 3600.0 * AJ("compresion")      # km por segundo de verdad
        n = int(total / max(0.01, vel) / max(5.0, AJ("suceso_cada")) + random.random())
        pesos = [("turbulencia", AJ("peso_turbulencia")), ("trafico", AJ("peso_trafico")), ("tormenta", AJ("peso_tormenta") * (2.0 if self.p.lluvia else 1.0))]
        suma = sum(w for _, w in pesos)
        self.plan = []
        hay_tormenta = False
        margen = AJ("aprox_km") + 3
        for _ in range(n):
            if suma <= 0 or total <= margen + 4:
                break
            r, cual = random.uniform(0, suma), pesos[0][0]
            for k, w in pesos:
                if r < w:
                    cual = k
                    break
                r -= w
            if cual == "tormenta":
                if hay_tormenta:
                    cual = "turbulencia"
                hay_tormenta = True
            self.plan.append((random.uniform(3.0, max(3.5, total - margen)), cual))
        self.plan.sort()

    # ------------------------------------------------------------- hablar y sonar
    def decir(self, texto, interrumpir=False):
        self.app.decir(texto, interrumpir)

    def torre(self, texto):
        self.ultima_torre = texto
        self.app.son("emisora", vol=0.5)
        self.decir(texto)

    def _tono_alt(self):
        self.app.son("tono_altitud", vol=0.6, tono=0.6 + 1.2 * max(0.0, min(1.0, self.alt / max(300.0, self.a["techo"]))))

    def _tecla_txt(self, key, nombre):
        return self.app.mando.boton_pantalla(key, nombre)

    def al_entrar(self):
        app, p = self.app, self.p
        if self.motor is not None:
            return
        for c in (self.v.canal, getattr(p, "rodadura", None)):
            if c is not None:
                c.volumen(0.0)
        self.motor = app.son(self.v.modelo.get("motor", "motor_helicoptero"), bucle=True, vol=0.4, tono=self.v.modelo.get("tono", 1.0))
        self.canales = [self.motor, app.son("viento_playa", bucle=True, vol=0.1)]
        km = V.distancia(self.pos, self.meta)
        datos = dict(campo=self.despega.nombre if self.despega else self.origen.nombre, origen=self.origen.nombre, destino=self.destino["mapa"].nombre,
                     km=V.km_txt(km), rumbo=V.rumbo_txt(self.rumbo), viento=_viento_txt(self.viento_kmh, self.viento_de))
        self.torre(AJ.frase("torre_despegue" if self.despega else "torre_salida", **datos))
        minutos = km / self.a["crucero"] * 60.0
        self.decir(tr('Unos {max} minutos de vuelo. El piloto automático lleva el rumbo y la altitud: no tienes que hacer nada. {_tecla_txt} lo quita y lo pone, {_tecla_txt2} acelera la travesía, {_tecla_txt3} dice cómo va y {_tecla_txt4} lo explica todo.').format(max=(max(1, int(round(minutos)))), _tecla_txt=(self._tecla_txt(pygame.K_TAB, tr('Tabulador'))), _tecla_txt2=(self._tecla_txt(pygame.K_n, tr('la N'))), _tecla_txt3=(self._tecla_txt(pygame.K_RETURN, tr('Intro'))), _tecla_txt4=(self._tecla_txt(pygame.K_F1, 'F1')))
                   + ("" if not p.vuelo_con_combustible() else tr(' Combustible, {int} por ciento.').format(int=(int(self.v.queroseno)))))
        if p.vuelo_con_combustible() and km > p.vuelo_alcance(self.v):
            app.son("alarma_cabina", vol=0.6)
            self.decir(tr('Atención: con lo que llevas solo puedes hacer unos {int} kilómetros. No llegas.').format(int=(int(p.vuelo_alcance(self.v)))))

    def cerrado(self):
        if not self.hecho:                                       # si algo cierra la pantalla por fuera, se llega igual
            self._llegar(forzado=True)

    def _callar(self):
        for c in self.canales:
            c.parar()
        self.canales = []
        if self.v.canal is not None:
            self.v.canal.volumen(0.42)

    # ------------------------------------------------------------- lo que se dice al preguntar
    def km_falta(self):
        return V.distancia(self.pos, self.meta)

    def aire_kmh(self):
        """La velocidad del aparato respecto al aire: la de crucero, menos si vuelas bajo o sin motor."""
        return self.a["crucero"] * (AJ("bajo_lento") / 100.0 if self.alt < AJ("alt_alta") else 1.0) * (0.55 if self.sin_motor else 1.0)

    def rumbo_bueno(self):
        """El rumbo que hay que llevar para ir derecho al destino (o al punto por el que se rodea): hacia él, y un poco
        contra el viento, para que no te saque."""
        hacia = V.rumbo_entre(self.pos, self.via or self.meta)
        cruz = self.viento_kmh * math.sin(math.radians(self.viento_de - hacia))
        return (hacia + math.degrees(math.asin(max(-0.7, min(0.7, cruz / max(40.0, self.aire_kmh())))))) % 360

    def desvio(self):
        """Grados que hay que virar para ir derecho al destino, contando el viento: negativo, a la izquierda."""
        return M.norm180(self.rumbo_bueno() - self.rumbo)

    def suelo(self):
        """Lo que avanza sobre el suelo, en kilómetros por hora hacia el este y hacia el norte: el aparato más el viento."""
        rad, de = math.radians(self.rumbo), math.radians(self.viento_de)
        aire = self.aire_kmh()
        return aire * math.sin(rad) - self.viento_kmh * math.sin(de), aire * math.cos(rad) - self.viento_kmh * math.cos(de)

    def velocidad(self):
        """Kilómetros por hora sobre el suelo."""
        return max(20.0, math.hypot(*self.suelo()))

    def estado_txt(self):
        km = self.km_falta()
        minutos = km / max(30.0, self.velocidad()) * 60.0
        d = self.desvio()
        encarado = tr("bien encarado") if abs(d) < 5 else tr('tienes que virar {int} grados a la {v}').format(int=(int(abs(d))), v=(LADOS[d > 0]))
        t = (tr('A {km_txt} kilómetros de {nombre}, unos {max} minutos. Rumbo {rumbo_txt}, {encarado}. Altitud {int} metros. Viento, {_viento_txt}.').format(km_txt=(V.km_txt(km)), nombre=(self.destino['mapa'].nombre), max=(max(1, int(round(minutos)))), rumbo_txt=(V.rumbo_txt(self.rumbo)), encarado=(encarado), int=(int(round(self.alt / 10.0) * 10)), _viento_txt=(_viento_txt(self.viento_kmh, self.viento_de))))
        if self.p.vuelo_con_combustible():
            t += tr(' Combustible {int} por ciento, para unos {int2} kilómetros.').format(int=(int(self.v.queroseno)), int2=(int(self.p.vuelo_alcance(self.v))))
        t += tr(" Piloto automático puesto.") if self.auto else tr(" Pilotas a mano.")
        if self.rapido:
            t += tr(" Travesía acelerada.") if self.acelerada() else tr(" Travesía acelerada, ahora a su ritmo.")
        if self.p.secuestro and self.p.secuestro["veh"] is self.v:
            t += tr(" El radar te sigue.") if self.p.secuestro["radar"] else tr(" El radar te ha perdido.")
        return t

    def ayuda_txt(self):
        k = self._tecla_txt
        return (tr('Travesía en vuelo. {k} y {k2} suben y bajan cien metros. {k3} y {k4} viran diez grados. {k5} pone o quita el piloto automático, que lleva solo el rumbo y la altitud. {k6} dice cuánto falta, el rumbo, la altitud, el viento y el combustible. {k7} acelera la travesía o la deja a su ritmo. {k8} repite lo último que dijo la torre. {k9}, o {k10}, abre el menú de vuelo: cambiar de destino, cómo quieres llegar y el aterrizaje asistido. Sin piloto automático, dos chasquidos te dicen hacia qué lado virar: por el centro y agudos, vas encarado. Una nota suena al cambiar de altitud: cuanto más aguda, más alto. Por debajo de {entero} metros el piloto automático no vuela: el aparato va más despacio, gasta más y hay obstáculos que saltar, pero el radar no te ve.').format(k=(k(pygame.K_UP, tr('Flecha arriba'))), k2=(k(pygame.K_DOWN, tr('flecha abajo'))), k3=(k(pygame.K_LEFT, tr('Flecha izquierda'))), k4=(k(pygame.K_RIGHT, tr('flecha derecha'))), k5=(k(pygame.K_TAB, tr('Tabulador'))), k6=(k(pygame.K_RETURN, tr('Intro'))), k7=(k(pygame.K_n, tr('La N'))), k8=(k(pygame.K_HOME, tr('Inicio'))), k9=(k(pygame.K_d, tr('La D'))), k10=(k(pygame.K_ESCAPE, tr('Escape'))), entero=(AJ.entero('alt_alta'))))

    # ------------------------------------------------------------- teclas
    def tecla(self, ev):
        k = ev.key
        if self.hecho:
            return
        if k == pygame.K_F1:
            self.decir(self.ayuda_txt(), True)
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.decir(self.estado_txt(), True)
        elif k == pygame.K_TAB:
            self._alternar_auto()
        elif k == pygame.K_n:
            self.rapido = not self.rapido
            self.decir((tr("Travesía acelerada: cuando pase algo irá a su ritmo, y después seguirá acelerada.") if self.auto else
                        tr("Travesía acelerada, pero solo con el piloto automático puesto: ahora pilotas tú.")) if self.rapido else tr("Travesía a su ritmo."), True)
        elif k == pygame.K_HOME:
            self.app.son("emisora", vol=0.5)
            self.decir(self.ultima_torre or tr("La torre no ha dicho nada todavía."), True)
        elif k in (pygame.K_d, pygame.K_ESCAPE):
            menu_de_vuelo(self)
        elif k in (pygame.K_UP, pygame.K_DOWN):
            self._cambiar_altitud(1 if k == pygame.K_UP else -1)
        elif k in (pygame.K_LEFT, pygame.K_RIGHT):
            self._virar(1 if k == pygame.K_RIGHT else -1)
        else:
            self.decir(self.estado_txt(), True)

    def _alternar_auto(self, forzar=None, callar=False):
        nuevo = (not self.auto) if forzar is None else forzar
        if nuevo and self.sin_motor:
            return self.decir(tr("Sin motor no hay piloto automático."), True)
        if nuevo and self.alt_obj < AJ("alt_alta") and self.fase not in ("aprox", "final"):
            self.alt_obj = AJ("alt_alta")
            if not callar:
                self.decir(tr('Piloto automático puesto. No vuela tan bajo: sube a {int} metros.').format(int=(int(self.alt_obj))), True)
        elif not callar:
            self.decir(tr("Piloto automático puesto: lleva el rumbo y la altitud.") if nuevo else
                       tr("Piloto automático quitado: pilotas tú. Los chasquidos te dicen hacia dónde virar."), True)
        self.auto = nuevo

    def _cambiar_altitud(self, sentido):
        if self.sin_motor:
            return self.decir(tr("Sin motor, el aparato baja solo. Dirígelo con izquierda y derecha."), True)
        paso = AJ("paso_crucero")
        nueva = max(AJ("alt_minima"), min(self.a["techo"], (round(self.alt_obj / paso) + sentido) * paso))
        if nueva == self.alt_obj:
            return self.decir(tr('Techo del aparato: {int} metros.').format(int=(int(self.a['techo']))) if sentido > 0 else tr('No se puede volar más bajo: {int} metros.').format(int=(int(self.alt_obj))), True)
        self.alt_obj = nueva
        if self.fase == "ascenso":
            self.fase = "crucero"                                # has cogido tú la altitud: ya no es la subida de salida
        if nueva < AJ("alt_alta") and self.auto and self.fase not in ("aprox", "final"):
            self.auto = False
            self.decir(tr('Bajas a {int} metros. Tan bajo no vuela el piloto automático: pilotas tú.').format(int=(int(nueva))), True)
        else:
            self.decir(tr('{v} a {int} metros.').format(v=(tr('Subes') if sentido > 0 else tr('Bajas')), int=(int(nueva))), True)

    def _virar(self, sentido):
        if self.auto:
            self._alternar_auto(False, callar=True)
            self.decir(tr("Piloto automático quitado: pilotas tú."), True)
        self.rumbo = (self.rumbo + sentido * AJ("giro")) % 360
        d = self.desvio()
        self.decir(tr('Rumbo {rumbo_txt}.').format(rumbo_txt=(V.rumbo_txt(self.rumbo))) + (tr(" Encarado.") if abs(d) < 5 else tr(' Te faltan {int} grados a la {v}.').format(int=(int(abs(d))), v=(LADOS[d > 0]))), True)

    def acelerada(self):
        """¿Va ahora la travesía acelerada? Solo si lo has pedido, con el piloto automático y mientras no pase nada: en cuanto
        hay un suceso, una tormenta o empieza la aproximación, va a su ritmo, y al acabar vuelve a acelerarse sola."""
        return bool(self.rapido and self.auto and not self.sin_motor and self.suceso is None and self.obstaculo is None and self.fase in ("crucero", "ascenso")
                    and not (self.tormenta and self.tormenta.get("dentro")))

    # ------------------------------------------------------------- por fotograma
    def actualizar(self, dt):
        if self.hecho:
            return
        p, v = self.p, self.v
        self.t += dt
        factor = AJ("acelerado") if self.acelerada() else 1.0
        sdt = dt * AJ("compresion") * factor                     # segundos de vuelo que pasan
        self.t_vuelo += sdt
        # ---- altitud
        antes = self.alt
        if self.sin_motor:
            self.alt = max(0.0, self.alt - AJ("planeo") * 0.35 * sdt)
            self.alt_obj = self.alt
        else:
            paso = AJ("ascenso_crucero") * dt * factor * (1.6 if self.a["pista"] else 1.0)
            self.alt += max(-paso * 1.3, min(paso, self.alt_obj - self.alt))
        marca = AJ("paso_crucero")
        if int(antes // marca) != int(self.alt // marca):
            self._tono_alt()
        if self.fase == "ascenso" and abs(self.alt - self.alt_obj) < 5:
            self.fase = "crucero"
            self.torre(AJ.frase("torre_crucero", alt=int(round(self.alt / 10.0) * 10), km=V.km_txt(self.km_falta())))
        # ---- rumbo
        if self.auto and not self.sin_motor:                     # el piloto automático lleva el rumbo bueno, con su corrección de viento
            giro = self.desvio()
            self.rumbo = (self.rumbo + max(-40 * dt * factor, min(40 * dt * factor, giro))) % 360
        # ---- avanzar: el aparato y el viento
        vx, vy = self.suelo()
        self.pos[0] += vx / 3600.0 * sdt
        self.pos[1] += vy / 3600.0 * sdt
        dkm = self.aire_kmh() / 3600.0 * sdt                     # lo volado, que es lo que gasta
        self.km_hechos += dkm
        if self.via is not None and V.distancia(self.pos, self.via) < 1.5:
            self.via = None
        # ---- combustible
        if p.vuelo_con_combustible() and not self.sin_motor:
            gasto = dkm / self.a["autonomia"] * 100.0 * (AJ("bajo_consumo") / 100.0 if self.alt < AJ("alt_alta") else 1.0)
            fase_real = v.fase
            v.fase = "tierra"                                    # los avisos, sí; lo de quedarse sin motor lo lleva esta pantalla
            queda = p._vuelo_gastar(v, gasto)
            v.fase = fase_real
            if not queda:
                self._sin_motor()
        # ---- sonido
        if self.motor is not None:
            self.motor.tono(v.modelo.get("tono", 1.0) * (0.35 if self.sin_motor else 0.95 + 0.1 * math.sin(self.t * 1.3) + (0.15 if self.alt < self.alt_obj - 5 else 0.0)))
            self.motor.volumen(0.12 if self.sin_motor else 0.4)
        if len(self.canales) > 1:
            self.canales[1].volumen(min(0.5, 0.08 + self.viento_kmh / 200.0 + (0.2 if self.tormenta and self.tormenta.get("dentro") else 0.0) + (0.15 if self.sin_motor else 0.0)))
        self._baliza(dt)
        # ---- lo que pasa
        self._radar(dt)
        self._sucesos(dt)
        self._vuelo_bajo(dt)
        self._paisaje()
        if self.hecho:
            return
        if self.sin_motor:
            if self.alt <= 0:
                self._forzoso()
            return
        self._aproximacion()

    def _baliza(self, dt):
        """Los chasquidos de alineación: suenan hacia el lado al que hay que virar. Con el piloto automático, solo al acercarse."""
        if self.auto and self.fase not in ("aprox", "final"):
            return
        self.t_baliza -= dt
        if self.t_baliza > 0:
            return
        d = self.desvio()
        self.t_baliza = 0.6 if abs(d) < 6 else 1.1
        self.app.son("tono_alineacion", vol=0.55, pan=max(-1.0, min(1.0, d / 45.0)), tono=1.35 if abs(d) < 6 else 1.0)

    # ------------------------------------------------------------- radar (un aparato secuestrado)
    def _radar(self, dt):
        s = self.p.secuestro
        if not s or s["veh"] is not self.v:
            return
        alta = self.alt >= AJ("alt_alta")
        if s["radar"]:
            s["bajo"] = 0.0 if alta else s["bajo"] + dt
            if s["bajo"] >= AJ("radar_pierde_crucero"):
                self.p.radar_perdido()
        elif alta:
            s["radar"], s["bajo"] = True, 0.0
            self.app.son("alarma_cabina", vol=0.5)
            self.decir(AJ.frase("frases_radar_otra_vez"))

    # ------------------------------------------------------------- volar bajo: obstáculos
    def _vuelo_bajo(self, dt):
        if self.sin_motor or self.fase in ("aprox", "final", "ascenso"):
            self.obstaculo = None
            return
        bajo = self.alt < AJ("alt_alta")
        if bajo and not self.bajo_dicho:
            self.bajo_dicho = True
            self.decir(tr('Vuelas bajo: el radar no te ve por debajo de {entero} metros, pero hay que saltar lo que salga al paso. Cuando oigas la alarma, sube.').format(entero=(AJ.entero('alt_alta'))))
            self.t_obstaculo = self.t + random.uniform(0.6, 1.4) * AJ("obstaculo_cada")
        if not bajo:
            self.bajo_dicho = False
            self.obstaculo = None
            self.t_obstaculo = None
            return
        o = self.obstaculo
        if o is None:
            if self.t_obstaculo is not None and self.t >= self.t_obstaculo and self.suceso is None:
                self.obstaculo = {"t": AJ("obstaculo_seg"), "alt": self.alt}
                self.app.son("alarma_cabina", vol=0.8)
                self.app.vibrar(0.6, 0.6, 200)
                self.decir(AJ.frase("frases_obstaculo") + f" {self._tecla_txt(pygame.K_UP, tr('Flecha arriba'))}.", True)
            return
        o["t"] -= dt
        if self.alt >= o["alt"] + AJ("obstaculo_sube") * 0.5 or self.alt_obj >= o["alt"] + AJ("obstaculo_sube"):
            self.obstaculo = None
            self.t_obstaculo = self.t + random.uniform(0.6, 1.4) * AJ("obstaculo_cada")
            self.decir(AJ.frase("frases_obstaculo_libre"))
        elif o["t"] <= 0:
            self.obstaculo = None
            self.t_obstaculo = self.t + random.uniform(0.6, 1.4) * AJ("obstaculo_cada")
            self._dano(AJ("obstaculo_dano"), AJ.frase("frases_obstaculo_roce"))
            self.confort += 1

    def _dano(self, pct, texto):
        v = self.v
        if self.p.cheat_repair(v):
            return
        v.salud = max(1.0, v.salud - v.salud_max * pct / 100.0)
        self.app.son("choque_leve", vol=0.8)
        self.app.vibrar(0.9, 0.7, 350)
        self.decir(texto + tr(' Estado del aparato, {int} por ciento.').format(int=(int(100 * v.salud / v.salud_max))))

    # ------------------------------------------------------------- sucesos de la travesía
    def _sucesos(self, dt):
        s = self.suceso
        if s is None:
            if self.plan and self.km_hechos >= self.plan[0][0] and self.fase == "crucero" and self.obstaculo is None and not self.sin_motor:
                _, cual = self.plan.pop(0)
                getattr(self, "_empieza_" + cual)()
        elif s["tipo"] == "turbulencia":
            s["t"] -= dt
            s["t_son"] -= dt
            if s["t_son"] <= 0:
                s["t_son"] = 1.2
                self.app.son("turbulencia", vol=0.7)
                self.app.vibrar(0.7, 0.4, 400)
                if not self.auto:
                    self.rumbo = (self.rumbo + random.uniform(-6, 6)) % 360
                self.alt = max(AJ("alt_minima"), min(self.a["techo"], self.alt + random.uniform(-25, 25)))
            if s["t"] <= 0:
                self.suceso = None
                self.decir(AJ.frase("frases_turbulencia_fin"))
        elif s["tipo"] == "trafico":
            s["t"] -= dt
            if abs(self.alt_obj - s["alt"]) >= 95:
                self.suceso = None
                self.decir(AJ.frase("frases_trafico_libre"))
            elif self.auto and s["t"] <= s["total"] * 0.55:
                sube = s["alt"] + 100 <= self.a["techo"]
                self.alt_obj = s["alt"] + (100 if sube else -100)
                self.suceso = None
                self.decir(tr('El piloto automático {v} cien metros para dejarle paso. ').format(v=(tr('sube') if sube else tr('baja'))) + AJ.frase("frases_trafico_libre"))
            elif s["t"] <= 0:
                self.suceso = None
                self.app.son("alarma_cabina", vol=0.8)
                self.app.vibrar(1.0, 1.0, 300)
                self.confort += 1
                multa = AJ.entero("trafico_multa") if not (self.p.secuestro and self.p.secuestro["veh"] is self.v) else 0
                texto = AJ.frase("frases_trafico_susto")
                if multa:
                    cobrado = min(multa, max(0, self.p.j.dinero))
                    self.p.j.dinero -= cobrado
                    texto += tr(' Sanción de {cobrado} euros.').format(cobrado=(cobrado))
                self.decir(texto)
        t = self.tormenta
        if t is not None:
            d = V.distancia(self.pos, t["c"])
            dentro = d <= t["r"]
            encima = self.alt >= AJ("tormenta_alt")
            if dentro and not t["dentro"]:
                t["dentro"] = True
                if encima:
                    self.decir(AJ.frase("frases_tormenta_encima"))
                else:
                    self.app.son("trueno", vol=0.8)
                    self.decir(AJ.frase("frases_tormenta_dentro"))
                    self.confort += 1
            elif not dentro and t["dentro"]:
                self.tormenta = None
                self.app.son("pajaro", vol=0.3)
                self.decir(AJ.frase("frases_tormenta_fuera"))
            elif dentro and not encima:
                t["t"] = t.get("t", 0.0) - dt
                if t["t"] <= 0:
                    t["t"] = random.uniform(1.6, 3.0)
                    self.app.son(random.choice(("trueno", "turbulencia", "turbulencia")), vol=0.8)
                    self.app.vibrar(0.9, 0.5, 400)
                    self.alt = max(AJ("alt_minima"), min(self.a["techo"], self.alt + random.uniform(-45, 45)))
                    if not self.auto:
                        self.rumbo = (self.rumbo + random.uniform(-10, 10)) % 360
                    if AJ("tormenta_dano") > 0 and random.random() < 0.45:
                        self._dano(AJ("tormenta_dano"), tr("Un golpe de aire sacude el aparato."))
            elif d > t["r"] + 25 and V.distancia(self.pos, self.meta) < V.distancia(t["c"], self.meta):
                self.tormenta = None                             # ha quedado atrás sin pisarla

    def _empieza_turbulencia(self):
        self.suceso = {"tipo": "turbulencia", "t": AJ("turbulencia_seg") * random.uniform(0.7, 1.3), "t_son": 0.0}
        self.confort += 0 if self.alt >= self.a["alt_crucero"] else 0
        self.decir(AJ.frase("frases_turbulencia"))

    def _empieza_trafico(self):
        self.suceso = {"tipo": "trafico", "t": AJ("trafico_seg"), "total": AJ("trafico_seg"), "alt": self.alt_obj}
        self.app.son("alarma_cabina", vol=0.6)
        self.torre(AJ.frase("torre_trafico"))

    def _empieza_tormenta(self):
        """Una tormenta en el rumbo: la torre avisa y tú decides, en un menú, qué haces."""
        rumbo = V.rumbo_entre(self.pos, self.meta)
        r = AJ("tormenta_radio")
        lejos = min(r + 16.0, self.km_falta() - AJ("aprox_km") - r - 1.0)
        if lejos < r + 5.0:                                      # no cabe una tormenta en lo que queda: se queda en turbulencias
            return self._empieza_turbulencia()
        rad = math.radians(rumbo)
        centro = (self.pos[0] + math.sin(rad) * lejos, self.pos[1] + math.cos(rad) * lejos)
        self.tormenta = {"c": centro, "r": r, "dentro": False, "t": 0.0}
        self.app.son("trueno", vol=0.5)
        self.torre(AJ.frase("torre_tormenta", km=V.km_txt(lejos - r)))
        menu_tormenta(self)

    def rodear_tormenta(self):
        t = self.tormenta
        if t is None:
            return
        rumbo = V.rumbo_entre(self.pos, t["c"])
        lado = random.choice((-1, 1))
        rad = math.radians(rumbo + 90 * lado)
        d = t["r"] + 2.5
        self.via = (t["c"][0] + math.sin(rad) * d, t["c"][1] + math.cos(rad) * d)
        self.decir(tr('La rodeas por la {v}.').format(v=(LADOS[lado > 0])) + ("" if self.auto else tr(" Sigue los chasquidos: te llevan por fuera.")))

    def subir_sobre_tormenta(self):
        self.alt_obj = min(self.a["techo"], max(self.alt_obj, AJ("tormenta_alt") + 100))
        self.decir(tr('Subes a {int} metros para pasarla por encima.').format(int=(int(self.alt_obj))))

    def _paisaje(self):
        """Al pasar cerca de otra localidad, se dice: es como se sabe por dónde se va."""
        if self.fase not in ("crucero", "ascenso") or AJ("peso_paisaje") <= 0:
            return
        for m in self.p.mapas.values():
            if m.id in self.paisajes or m.id in (self.origen.id, self.destino["mapa"].id) or m.tipo == "mar":
                continue
            pt = V.punto_aire(m.id)
            d = V.distancia(self.pos, pt)
            if d <= 12.0:
                self.paisajes.add(m.id)
                lado = M.norm180(V.rumbo_entre(self.pos, pt) - self.rumbo)
                self.decir(AJ.frase("frases_paisaje", lugar=m.nombre, lado=LADOS[lado > 0], km=V.km_txt(d)))
                return

    # ------------------------------------------------------------- sin combustible
    def _sin_motor(self):
        if self.sin_motor:
            return
        self.sin_motor = True
        self.auto = False
        self.suceso = None
        self.app.son("motor_seco", vol=0.8)
        self.app.son("alarma_cabina", vol=0.8)
        alcance = self.alt / 1000.0 * 10.0                        # planea unos diez kilómetros por cada mil metros
        self.decir(AJ.frase("frases_sin_motor") + tr(' Desde {int} metros planeas unos {km_txt} kilómetros. ').format(int=(int(self.alt)), km_txt=(V.km_txt(alcance)))
                   + (tr("Llegas a ") + self.destino["mapa"].nombre + tr(" si no te desvías.") if alcance >= self.km_falta() else tr("No llegas a ningún campo: te vas a posar donde puedas.")), True)

    def _forzoso(self):
        """Te quedas sin altura lejos de un campo: te posas donde puedes, y apareces en la localidad más cercana."""
        p, v = self.p, self.v
        cerca = min((m for m in p.mapas.values() if m.tipo != "mar"), key=lambda m: V.distancia(self.pos, V.punto_aire(m.id)))
        self.hecho = True
        self._callar()
        self.app.cerrar(self)
        pct = random.uniform(*sorted((AJ("caida_min"), AJ("caida_max"))))
        if not p.cheat_repair(v):
            v.salud = max(1.0, v.salud - v.salud_max * pct / 100.0)
        rumbo = V.rumbo_entre(self.pos, V.punto_aire(cerca.id))
        rad = math.radians(rumbo)
        cx, cy = cerca.ancho / 2.0, cerca.alto / 2.0
        k = min((cx - 14) / max(1e-6, abs(math.sin(rad))), (cy - 14) / max(1e-6, abs(math.cos(rad))))
        x, y = cerca.punto_libre(cx - math.sin(rad) * k, cy - math.cos(rad) * k)
        p.pasar_horas(self.t_vuelo / 3600.0 + 2.0)
        p.cambiar_mapa(cerca.id, x, y, rumbo)
        v.alt, v.fase, v.vel = 0.0, "tierra", 0.0
        self.app.son("choque", vol=0.9)
        self.app.vibrar(1.0, 0.8, 600)
        p.vuelo_herida(v)
        p.j.stats["aterrizajes_forzosos"] = p.j.stats.get("aterrizajes_forzosos", 0) + 1
        if p.vuelo_trabajo and p.vuelo_trabajo.get("veh") is v:
            p.piloto_dejar("")
            p.decir(tr("El vuelo comercial se da por perdido."))
        p.decir(AJ.frase("frases_caida") + tr(' Un tractor arrastra lo que queda del aparato hasta las afueras de {nombre}. Estado, {int} por ciento. No queda combustible: se pide desde el móvil, en Mis vehículos.').format(nombre=(cerca.nombre), int=(int(100 * v.salud / v.salud_max))))
        p.vuelo_al_posarse(v, None)

    # ------------------------------------------------------------- aproximación y llegada
    def _aproximacion(self):
        km = self.km_falta()
        if self.modo == "bajo":
            if km <= AJ("sobrevuelo_km"):
                self._llegar()
            return
        if self.fase in ("crucero", "ascenso") and km <= AJ("aprox_km"):
            self.fase = "aprox"
            self.suceso = None
            if self.asistido or self.auto or self.guiada:
                self.alt_obj = min(self.alt_obj, AJ("aprox_alt"))
            self.torre(AJ.frase("torre_aprox", campo=self.campo.nombre, km=V.km_txt(km), alt=AJ.entero("aprox_alt"), rumbo=V.rumbo_txt(V.rumbo_entre(self.pos, self.meta))))
            if not (self.asistido or self.auto):
                self.decir(tr('Aterrizaje a mano: baja con {_tecla_txt} hasta {entero} metros o menos y mantén los chasquidos en el centro.').format(_tecla_txt=(self._tecla_txt(pygame.K_DOWN, tr('flecha abajo'))), entero=(AJ.entero('aprox_alt'))))
            elif self.asistido and not self.auto:
                self.auto = True
                self.decir(tr("Aterrizaje asistido: el aparato baja y se encara solo."))
        if self.fase == "aprox" and km <= AJ("aprox_km") * 0.4:
            self.fase = "final"
        if self.fase == "final" and not self.final_dicho and abs(self.desvio()) <= AJ("alineacion") and self.alt <= AJ("aprox_alt") + 60:
            self.final_dicho = True                              # en cuanto estás bajo y encarado, la torre te lo confirma
            self.torre(AJ.frase("torre_final"))
        if self.fase in ("aprox", "final") and km <= AJ("llegada_km"):
            alto = self.alt > AJ("aprox_alt") + 60
            torcido = abs(self.desvio()) > AJ("alineacion") and km > 0.15
            if (alto or torcido) and not (self.auto or self.guiada):
                self._frustrada("alto" if alto else "torcido")
                return
            self.duro = not (self.auto or self.guiada) and (self.alt > AJ("aprox_alt") or abs(self.desvio()) > AJ("alineacion") * 0.6)
            self._llegar()
        elif self.fase in ("aprox", "final") and not (self.auto or self.guiada):
            self.cerca = min(getattr(self, "cerca", 1e9), km)
            if self.cerca < 2.5 and km > self.cerca + 0.4:       # has pasado de largo sin tocar el campo
                self._frustrada("alto" if self.alt > AJ("aprox_alt") + 60 else "torcido")

    def _frustrada(self, motivo):
        self.frustradas += 1
        self.confort += 1
        self.app.son("alarma_cabina", vol=0.6)
        self.torre(AJ.frase("torre_frustrada", motivo=motivo))
        # das la vuelta: quedas otra vez a unos kilómetros, encarado
        rumbo = V.rumbo_entre(self.pos, self.meta) if V.distancia(self.pos, self.meta) > 0.05 else self.rumbo
        rad = math.radians(rumbo + 180)
        self.pos = [self.meta[0] + math.sin(rad) * AJ("frustrada_km"), self.meta[1] + math.cos(rad) * AJ("frustrada_km")]
        self.rumbo = rumbo
        self.fase, self.final_dicho, self.cerca = "aprox", False, 1e9
        if self.p.vuelo_con_combustible():
            self.p._vuelo_gastar(self.v, 2 * AJ("frustrada_km") / self.a["autonomia"] * 100.0) if self.v.queroseno > 0.5 else None
        if self.frustradas >= AJ("frustradas"):
            self.guiada = True
            self.auto = True
            self.alt_obj = min(self.alt_obj, AJ("aprox_alt"))
            self.torre(AJ.frase("torre_guiada"))

    def _llegar(self, forzado=False):
        if self.hecho:
            return
        self.hecho = True
        self._callar()
        if not forzado:
            self.app.cerrar(self)
        s = self.p.secuestro
        self.p.vuelo_llegar(self.v, {"mapa": self.destino["mapa"], "campo": self.campo if self.modo == "campo" else None, "modo": self.modo, "rumbo": self.rumbo,
                                     "alt": max(AJ("alt_minima"), min(self.alt, 140.0 if s and s["veh"] is self.v and not s["radar"] else 250.0)),
                                     "horas": self.t_vuelo / 3600.0, "segundos": self.t, "duro": self.duro, "km": self.km_hechos, "confort": self.confort})

    def cambiar_destino(self, destino, modo):
        self._poner_destino(destino, modo)
        self.fase = "crucero"
        self.via = None
        self._plan_sucesos()
        self.plan = [(self.km_hechos + d, c) for d, c in self.plan]
        km = self.km_falta()
        self.torre(tr('Recibido: nuevo destino, {nombre}. {km_txt} kilómetros, rumbo {rumbo_txt}.').format(nombre=(destino['mapa'].nombre), km_txt=(V.km_txt(km)), rumbo_txt=(V.rumbo_txt(V.rumbo_entre(self.pos, self.meta)))))
        if self.p.vuelo_con_combustible() and km > self.p.vuelo_alcance(self.v):
            self.app.son("alarma_cabina", vol=0.6)
            self.decir(tr('Atención: solo te queda para unos {int} kilómetros.').format(int=(int(self.p.vuelo_alcance(self.v)))))


# ====================================================================== menús de la travesía
def _destinos_desde(c):
    """Los destinos posibles desde donde está ahora el aparato en la travesía."""
    p, v = c.p, c.v
    out = []
    pista = c.a["pista"]
    for m in p.mapas.values():
        if m.tipo == "mar":
            continue
        campos = [l for l in m.lugares.values() if l.tipo in V.CAMPOS]
        if not campos:
            continue
        validos = [l for l in campos if l.tipo == "aeropuerto"] if pista else sorted(campos, key=lambda l: l.tipo != "helipuerto")
        pt = V.punto_aire(m.id)
        out.append({"mapa": m, "campo": validos[0] if validos else None, "campos": validos, "km": V.distancia(c.pos, pt), "rumbo": V.rumbo_entre(c.pos, pt)})
    return sorted(out, key=lambda d: d["km"])


def _modo_txt(modo, destino):
    if destino.get("campo") is None:
        return tr("entrar volando bajo: allí no hay campo para este aparato")
    return tr('aterrizar en {nombre}').format(nombre=(destino['campo'].nombre)) if modo == "campo" else tr("entrar volando bajo sobre la localidad, sin pasar por el campo")


def menu_de_vuelo(c):
    app, p = c.app, c.p

    def seguir():
        app.cerrar(m)

    def cambiar_modo():
        if c.campo is None:
            app.son("error")
            return app.decir(tr("Allí no hay campo para este aparato: solo puedes entrar volando bajo."), True)
        c.modo = "bajo" if c.modo == "campo" else "campo"
        m.refrescar()

    def asistido():
        c.asistido = not c.asistido
        p.cfg["vuelo_asistido"] = c.asistido
        m.refrescar()

    def campo_sig():
        campos = c.destino.get("campos") or []
        if len(campos) < 2:
            return
        c.campo = campos[(campos.index(c.campo) + 1) % len(campos)] if c.campo in campos else campos[0]
        m.refrescar()

    def destino(d):
        def f():
            app.cerrar(sub)
            app.cerrar(m)
            c.cambiar_destino(d, c.modo if d.get("campo") is not None else "bajo")
        return f

    def otro():
        nonlocal sub
        ops = [Opcion(tr('{nombre}: {km_txt} kilómetros, rumbo {rumbo_txt}').format(nombre=(d['mapa'].nombre), km_txt=(V.km_txt(d['km'])), rumbo_txt=(V.rumbo_txt(d['rumbo']))) + ("" if d.get("campo") is not None else tr(". Sin campo para este aparato")),
                      destino(d), ayuda=p.desc_localidad(d["mapa"])) for d in _destinos_desde(c)]
        sub = Menu(app, tr("Cambiar de destino. El primero es el más cercano"), ops)
        app.abrir(sub)
    sub = None

    def ops():
        lista = [Opcion(tr("Seguir volando"), seguir),
                 Opcion(lambda: c.estado_txt(), ayuda=tr("Cuánto falta, el rumbo, la altitud, el viento y el combustible. Lo mismo te dice Intro mientras vuelas.")),
                 Opcion(lambda: tr("Cómo llegas: ") + _modo_txt(c.modo, c.destino if c.campo is None else dict(c.destino, campo=c.campo)), cambiar_modo,
                        ayuda=tr("Intro cambia. Aterrizar en el campo te deja en tierra, en el helipuerto o en la pista. Entrar volando bajo te deja en el aire sobre la localidad, para posarte donde quieras: "
                              "es lo que conviene si llevas un aparato que no debe ver nadie."))]
        if len(c.destino.get("campos") or []) > 1 and c.modo == "campo":
            lista.append(Opcion(lambda: tr('Campo: {nombre}').format(nombre=(c.campo.nombre)), campo_sig, ayuda=tr("Intro pasa al siguiente campo de esa localidad.")))
        lista += [Opcion(lambda: tr("Aterrizaje asistido: ") + (tr("sí") if c.asistido else tr("no")), asistido,
                         ayuda=tr("Con sí, al acercarte el aparato baja y se encara solo. Con no, y sin piloto automático, lo haces tú: baja a la altitud que dice la torre y mantén los chasquidos en el centro. "
                               "Si entras alto o torcido, la torre te manda dar otra vuelta; a la segunda, te guía ella.")),
                  Opcion(tr("Cambiar de destino"), otro, ayuda=tr("Vale también para desviarte a un campo más cercano si no te llega el combustible.")),
                  Opcion(tr("Cómo se pilota: la ayuda de esta pantalla"), lambda: app.decir(c.ayuda_txt(), True),
                         ayuda=tr("Te dice las teclas de la travesía: subir y bajar, virar, el piloto automático, acelerar y lo que dice la torre."))]
        return lista
    m = Menu(app, tr("Menú de vuelo"), ops)
    app.abrir(m)


def menu_tormenta(c):
    app = c.app
    t = c.tormenta
    r = t["r"] if t else 6

    def hacer(f):
        def g():
            app.cerrar(m)
            f()
        return g
    ops = [Opcion(tr('Rodearla: unos {int} kilómetros más').format(int=(int(round(r * 1.2)))), hacer(c.rodear_tormenta), ayuda=tr("Das un rodeo por fuera. Gastas algo más de combustible y de tiempo, y no pasa nada."))]
    if c.a["techo"] >= AJ("tormenta_alt") + 100:
        ops.append(Opcion(tr('Pasarla por encima, subiendo a {v} metros').format(v=(AJ.entero('tormenta_alt') + 100)), hacer(c.subir_sobre_tormenta),
                          ayuda=tr("Este aparato puede: por encima de la tormenta el aire está en calma.")))
    ops.append(Opcion(tr("Atravesarla"), hacer(lambda: c.decir(tr("Sigues recto, hacia la tormenta."))),
                      ayuda=tr("El camino más corto. Dentro hay turbulencias fuertes, el aparato puede sufrir daños y, si llevas pasaje, se quejará.")))
    m = Menu(app, tr("Tormenta en tu rumbo. Qué haces"), ops, escapable=False)
    app.abrir(m)


# ====================================================================== plan de vuelo
def plan_de_vuelo(p, campo):
    """El menú para empezar una travesía: adónde. Desde un campo (con Intro) o desde el borde de la localidad."""
    app, j = p.app, p.j
    v = j.veh
    if v is None or not v.modelo.get("vuela"):
        return
    p.vuelo_prep(v)
    alcance = p.vuelo_alcance(v)
    destinos = p.vuelo_destinos(v)
    # el primero, hacia donde miras: así, saliendo por un borde, Intro es «sigo hacia allá»
    destinos.sort(key=lambda d: abs(M.norm180(d["rumbo"] - v.rumbo)) if campo is None else d["km"])
    trab, s = p.vuelo_trabajo, p.secuestro
    marcado = trab["destino_mapa"] if trab and trab.get("veh") is v else (s["encargo"]["mapa"] if s and s["veh"] is v and s.get("encargo") else None)
    destinos.sort(key=lambda d: d["mapa"].id != marcado)

    def ir(d, modo):
        def f():
            if p.vuelo_con_combustible() and v.queroseno <= 0:
                app.son("error")
                return app.decir(tr("No queda combustible."), True)
            _volver_al_juego(p)
            if trab and trab.get("veh") is v and d["mapa"].id == trab["destino_mapa"]:
                d2 = dict(d)
                dest = p.lug(trab["destino"])
                if dest in (d.get("campos") or []):
                    d2["campo"] = dest
                app.abrir(Crucero(p, v, d2, modo, campo))
            else:
                app.abrir(Crucero(p, v, d, modo, campo))
        return f

    def texto(d, modo):
        t = tr('{nombre}: {km_txt} kilómetros, rumbo {rumbo_txt}, unos {max} minutos. ').format(nombre=(d['mapa'].nombre), km_txt=(V.km_txt(d['km'])), rumbo_txt=(V.rumbo_txt(d['rumbo'])), max=(max(1, int(round(d['km'] / V.aeronave(v.modelo)['crucero'] * 60)))))
        modo_t = _modo_txt(modo, d)
        t += modo_t[0].upper() + modo_t[1:]
        if d["mapa"].id == marcado:
            t += tr(". Es adonde tienes que ir")
        if d["km"] > alcance:
            t += tr('. No te llega el combustible: tienes para {int} kilómetros').format(int=(int(alcance)))
        return t
    ops = []
    for d in destinos:
        if d.get("campo") is not None:
            ops.append(Opcion(texto(d, "campo"), ir(d, "campo"), ayuda=p.desc_localidad(d["mapa"]) + tr(" Aterrizas en el campo, con la torre.")))
        ops.append(Opcion(texto(d, "bajo"), ir(d, "bajo"),
                          ayuda=p.desc_localidad(d["mapa"]) + tr(" Llegas en el aire, volando bajo sobre la localidad, y te posas donde quieras.")))
    if not ops:
        ops.append(Opcion(tr("No hay ninguna otra localidad con helipuerto ni aeropuerto"), ayuda=tr("Con este aparato no hay ningún destino al que volar desde aquí.")))
    titulo = tr('Plan de vuelo desde {v}').format(v=(campo.nombre if campo else p.mundo.nombre)) + (tr('. Combustible, {int} por ciento').format(int=(int(v.queroseno))) if p.vuelo_con_combustible() else "")
    m = Menu(app, titulo, ops, intro=tr("Elige adónde vuelas y cómo llegas. La travesía se hace de verdad, con piloto automático si quieres"))
    app.abrir(m)


# ====================================================================== el campo: helipuerto, aeropuerto o aeródromo
def menu_campo(p, l):
    """Con Intro en un campo, a bordo de un aparato: plan de vuelo, combustible, hangar y lo demás."""
    app, j = p.app, p.j
    v = j.veh
    p.vuelo_prep(v)
    if getattr(v, "fase", "tierra") != "tierra":
        ops = [Opcion(tr("Plan de vuelo: volar a otra localidad"), lambda: plan_de_vuelo(p, None), ayuda=tr("Estás en el aire sobre el campo: eliges destino y empieza la travesía.")),
               Opcion(tr("Para repostar o usar el hangar, aterriza antes: frena y pulsa F"), ayuda=tr("Ya en tierra, con Intro en el campo tienes el combustible, el hangar y los vuelos comerciales."))]
        app.abrir(Menu(app, tr('{nombre}. Estás a {int} metros').format(nombre=(l.nombre), int=(int(v.alt))), ops))
        return

    def ops():
        lista = [Opcion(tr("Plan de vuelo: volar a otra localidad"), lambda: plan_de_vuelo(p, l), ayuda=tr("Eliges destino, la torre te da salida y empieza la travesía."))]
        if p.vuelo_con_combustible():
            lista.append(Opcion(lambda: tr('Repostar: {int} por ciento. Llenar cuesta {vuelo_precio_repostar} euros').format(int=(int(v.queroseno)), vuelo_precio_repostar=(p.vuelo_precio_repostar(v))), lambda: (p.vuelo_repostar(v), m.refrescar(False)),
                                ayuda=tr('Con el depósito lleno, {nombre} hace unos {int} kilómetros.').format(nombre=(v.nombre), int=(int(V.aeronave(v.modelo)['autonomia'])))))
        lista += opciones_campo(p, l)
        return lista
    m = Menu(app, lambda: tr('{nombre}. A bordo de {nombre2}. Tienes {dinero} euros').format(nombre=(l.nombre), nombre2=(v.nombre), dinero=(j.dinero)), ops)
    app.abrir(m)


def opciones_campo(p, l):
    """Lo que un campo ofrece además de sus vuelos: hangar, vuelos comerciales y, con un arma en la mano, lo otro."""
    lista = [Opcion(lambda: _hangar_txt(p, l), lambda: menu_hangar(p, l),
                    ayuda=tr("Una plaza de hangar, alquilada o comprada, para guardar tus aeronaves: allí no se pierden, se revisan y se repostan. Salen en el móvil, en Mis vehículos."))]
    if p.hon_titulo("piloto") is not None or p.vuelo_trabajo:
        lista.append(Opcion(lambda: tr("Vuelos comerciales: ") + (p.piloto_txt() if p.vuelo_trabajo else tr("pasaje y carga para pilotos con licencia")), lambda: menu_piloto(p, l),
                            ayuda=tr("Trabajo legal de piloto: llevas pasaje o carga a otra localidad, volando de verdad, y cobras al aterrizar. Hace falta la licencia de piloto comercial, que se saca en una academia.")))
    if not p.j.veh and not p.en_servidor and p.vuelo_real():
        lista.append(Opcion(tr("Secuestrar el aparato de línea que está a punto de salir"), lambda: menu_secuestro(p, l),
                            ayuda=tr("Con un arma de fuego en la mano. Es un delito mayor: búsqueda muy alta, un antecedente grave y el radar siguiéndote. Dentro se explica.")))
    lista.append(Opcion(tr("Cómo funciona volar: la travesía, la altura, el combustible, los hangares y el radar"), lambda: como_funciona(p),
                        ayuda=tr("Abre la explicación completa, por apartados, para leerla con las flechas.")))
    return lista


def _hangar_txt(p, l):
    h = p.hangar(l)
    if h is None:
        return tr('Hangar: no tienes plaza aquí. Alquilarla cuesta {precio} euros al día; comprarla, {hangar_precio_compra}').format(precio=(p.precio('hangar_alquiler', 120)), hangar_precio_compra=(p.hangar_precio_compra(l)))
    t = tr('Hangar: plaza {v}, con {len} de {entero} aeronaves').format(v=(tr('tuya') if h['propia'] else tr('alquilada')), len=(len(h['naves'])), entero=(AJ.entero('hangar_plazas')))
    return t + (tr('. Debes {debe} euros').format(debe=(h['debe'])) if h["debe"] > 0 else "")


def menu_hangar(p, l):
    app, j = p.app, p.j
    from . import misvehiculos as MV

    def cerca():
        """Tus aeronaves que están en este campo, fuera del hangar: la que llevas y las aparcadas al lado."""
        return [v for v in p.vehiculos if v.modelo.get("vuela") and not v.muerto and (v is j.veh or (v.dist(l.x, l.y) <= 90 and v.ia in (None, "aparcado")))
                and getattr(v, "ia", None) != "heli_policia" and not getattr(v, "volando", False)]

    def nave(d):
        def abrir():
            nombre = MV.nombre_completo(p, d.get("nombre"), d["modelo"])
            sub_ops = [Opcion(tr('Sacarla a la pista'), lambda: (p.hangar_sacar(l, d) is not None) and _volver_al_juego(p),
                              ayuda=tr("La dejas fuera, lista para subir y volar. Si debes alquiler de este hangar, no te dejan sacarla hasta pagar.")),
                       Opcion(lambda: tr('Repostar: {int} por ciento. Llenar cuesta {vuelo_precio_repostar} euros').format(int=(int(float(d.get('queroseno', 100)))), vuelo_precio_repostar=(p.vuelo_precio_repostar(float(d.get('queroseno', 100))))),
                              lambda: (p.hangar_repostar(d), sub.refrescar(False)), ayuda=tr("Le llenas el depósito sin sacarla del hangar.")),
                       Opcion(lambda: tr('Revisarla y repararla: {hangar_precio_revision} euros').format(hangar_precio_revision=(p.hangar_precio_revision(d))), lambda: (p.hangar_revisar(d), sub.refrescar(False)),
                              ayuda=tr("El mantenimiento la deja como nueva. Cuesta según el daño que tenga.")),
                       Opcion(tr("Cambiarle el nombre"), lambda: p.renombrar_vehiculo(d, lambda: (app.cerrar(sub), m.refrescar(False))),
                              ayuda=tr("Escribes el nombre que quieras y así la reconoces en tus listas. Si lo dejas en blanco, recupera el del modelo."))]
            sub = Menu(app, nombre, sub_ops)
            app.abrir(sub)
        return abrir

    def ops():
        h = p.hangar(l)
        lista = []
        if h is None:
            lista.append(Opcion(tr('Alquilar una plaza: {precio} euros al día').format(precio=(p.precio('hangar_alquiler', 120))), lambda: (p.hangar_contratar(l, False), m.refrescar(False)),
                                ayuda=tr("Pagas hoy el primer día, y después se cobra cada medianoche. Si un día no te llega, se apunta la deuda: no pierdes las aeronaves, pero no te dejan sacarlas hasta pagar.")))
            lista.append(Opcion(tr('Comprar una plaza: {hangar_precio_compra} euros').format(hangar_precio_compra=(p.hangar_precio_compra(l))), lambda: (p.hangar_contratar(l, True), m.refrescar(False)),
                                ayuda=tr("Es tuya para siempre: no paga alquiler.")))
            return lista
        if h["debe"] > 0:
            lista.append(Opcion(tr('Pagar lo que debes: {debe} euros').format(debe=(h['debe'])), lambda: (p.hangar_pagar_deuda(l), m.refrescar(False)),
                                ayuda=tr("Es el alquiler que no pudiste pagar. Hasta saldarlo, no te dejan sacar ninguna aeronave de aquí.")))
        from . import misvehiculos
        for d in h["naves"]:
            smax = misvehiculos._salud_max(p, d["modelo"], d.get("mejoras"))
            lista.append(Opcion(tr('{nombre_completo}. Estado {int} por ciento, combustible {int2} por ciento').format(nombre_completo=(MV.nombre_completo(p, d.get('nombre'), d['modelo'])), int=(int(100 * float(d.get('salud', smax)) / smax)), int2=(int(float(d.get('queroseno', 100))))),
                                nave(d), ayuda=tr("Intro: sacarla, repostarla, revisarla o cambiarle el nombre.")))
        for v in cerca():
            lista.append(Opcion(tr('Guardar {nombre} en el hangar').format(nombre=(v.nombre)), (lambda v=v: (p.hangar_guardar(l, v), m.refrescar(False))),
                                ayuda=tr("Queda a salvo, a tu nombre. La sacas cuando quieras desde este mismo menú.")))
        if not h["naves"] and not cerca():
            lista.append(Opcion(tr("El hangar está vacío. Trae una aeronave hasta este campo para guardarla"),
                                ayuda=tr("Cuando tengas una aeronave tuya aquí al lado, o a bordo, aparece en este menú para guardarla.")))
        if not h["propia"]:
            lista.append(Opcion(tr('Comprar la plaza: {hangar_precio_compra} euros').format(hangar_precio_compra=(p.hangar_precio_compra(l))), lambda: (p.hangar_contratar(l, True), m.refrescar(False)), ayuda=tr("Dejas de pagar alquiler.")))
            lista.append(Opcion(tr("Dejar de alquilar la plaza"), lambda: (p.hangar_dejar(l), m.refrescar(False)), ayuda=tr("Solo si está vacía.")))
        return lista
    m = Menu(app, lambda: tr('Hangar de {nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(j.dinero)), ops,
             intro=tr('Caben {entero} aeronaves. Lo que guardas aquí no se pierde').format(entero=(AJ.entero('hangar_plazas'))))
    app.abrir(m)


def menu_piloto(p, l):
    app = p.app
    if p.vuelo_trabajo:
        ops = [Opcion(p.piloto_txt(), ayuda=tr("El vuelo que llevas: qué transportas, adónde y lo que pagan. Se cobra al aterrizar en el campo de destino.")), Opcion(tr("Dejar este vuelo"), lambda: (p.piloto_dejar(), app.cerrar(m)), ayuda=tr("No cobras, y el aparato de la compañía se queda aquí."))]
        m = Menu(app, tr("Vuelo comercial en curso"), ops)
        app.abrir(m)
        return
    motivo = p.piloto_motivo(l)
    if motivo:
        app.son("error")
        app.decir(motivo, True)
        return

    def aceptar(o):
        return lambda: p.piloto_aceptar(l, o)

    def ops():
        lista = []
        for o in p.piloto_ofertas(l):
            if p.atracadas.get(f"vuelo:{l.id}:{o['n']}") == p.dia:
                lista.append(Opcion(tr('{que} a {nombre}: ya lo has hecho hoy').format(que=(o['que']), nombre=(p.mapas[o['destino_mapa']].nombre)),
                                    ayuda=tr("Cada vuelo se hace una vez al día. Mañana habrá otros encargos.")))
                continue
            dest = p.lug(o["destino"])
            lista.append(Opcion(AJ.frase("frases_piloto_oferta", que=o["que"], destino=p.nombre_lugar(dest), km=V.km_txt(o["km"]), paga=o["paga"]).rstrip("."), aceptar(o),
                                ayuda=(tr("Pasaje: si el vuelo es tranquilo, hay gratificación; si es movido, descuento. ") if o["pasaje"] else tr("Carga. "))
                                + (tr("Hace falta un helicóptero. ") if o["heli"] else "") + tr("Si tienes en este campo una aeronave tuya que valga, vuelas con ella y cobras un suplemento; si no, la compañía te deja una.")))
        return lista or [Opcion(tr("Hoy no hay vuelos desde este campo"), ayuda=tr("Prueba en otro campo, o vuelve otro día."))]
    m = Menu(app, tr('Vuelos comerciales desde {nombre}').format(nombre=(l.nombre)), ops, intro=tr("Tres encargos al día, distintos en cada campo. Se cobra al aterrizar en el campo de destino"))
    app.abrir(m)


def menu_secuestro(p, l):
    app = p.app
    motivo = p.secuestro_motivo(l)
    if motivo:
        app.son("error")
        app.decir(motivo, True)
        return
    modelo = p.secuestro_modelo(l)
    e = p.secuestro_encargo(l)
    nivel = AJ.entero("secuestro_busqueda")
    ops = [Opcion(tr('Secuestrar el {nombre} de línea y quedártelo').format(nombre=(p.modelos[modelo]['nombre'])), lambda: p.secuestrar(l),
                  ayuda=tr('Nivel de búsqueda {nivel}, un antecedente grave y el radar siguiéndote. No puede ser tuyo ni guardarse en un hangar: está denunciado.').format(nivel=(nivel)))]
    if e:
        dest = p.lug(e["lugar"])
        ops.append(Opcion(tr('Secuestrarlo por encargo: dejarlo junto a {nombre}, en {nombre2}, a {km_txt} kilómetros, por {paga} euros').format(nombre=(dest.nombre), nombre2=(p.mapas[e['mapa']].nombre), km_txt=(V.km_txt(e['km'])), paga=(e['paga'])), lambda: p.secuestrar(l, e),
                          ayuda=tr("Alguien paga por el aparato, entregado en un sitio discreto de otra localidad. Tienes que llegar sin el radar encima: vuela bajo un rato para que te pierda, "
                                "entra volando bajo sobre la localidad y pósate junto a ese sitio. Cada día y en cada campo hay un encargo distinto.")))
    ops.append(Opcion(tr("Cómo funciona: el radar, dónde aterrizar y qué te espera"), lambda: como_funciona(p, "secuestro"),
                      ayuda=tr("Abre la explicación del secuestro, por apartados, para leerla con las flechas antes de decidir.")))
    m = Menu(app, tr('Secuestrar un aparato en {nombre}').format(nombre=(l.nombre)), ops, intro=tr("Es un delito mayor. Piénsalo antes"))
    app.abrir(m)


def como_funciona(p, solo=None):
    app = p.app
    alta = AJ.entero("alt_alta")
    secuestro = [
        tr('Secuestrar un aparato. En un helipuerto, un aeropuerto o un aeródromo, a pie y con un arma de fuego en la mano, puedes quedarte con el aparato de línea que iba a salir. Es un delito mayor: nivel de búsqueda {entero}, un antecedente grave y, si tienes encendido el helicóptero de la policía, viene a por ti.').format(entero=(AJ.entero('secuestro_busqueda'))),
        tr('El radar. Mientras vueles por encima de {alta} metros, el radar te sigue: no puedes despistar a la policía, y si aterrizas en un helipuerto o un aeropuerto, te están esperando. Para que te pierda, vuela por debajo de {alta} metros: {entero} segundos seguidos sobre una localidad, o {entero2} en una travesía. Si vuelves a subir, te ve otra vez.').format(alta=(alta), entero=(AJ.entero('radar_pierde')), entero2=(AJ.entero('radar_pierde_crucero'))),
        tr("Dónde aterrizar. Lejos de los campos: en el plan de vuelo elige entrar volando bajo sobre la localidad, y pósate en una calle o un descampado. En un campo, aunque el radar te haya perdido, reconocen el aparato."),
        tr("El encargo. Cada día, en cada campo, alguien paga por un aparato entregado junto a un sitio discreto de otra localidad. Solo paga si llegas sin el radar encima."),
        tr("Un aparato secuestrado no puede ser tuyo ni guardarse en un hangar. En un servidor en línea no se puede secuestrar."),
    ]
    lineas = [
        tr("Qué cambia. Con el vuelo real, que viene puesto y se quita en Opciones, Movimiento y conducción, un helicóptero o una avioneta tienen altura, gastan combustible y viajan de verdad entre localidades. Con la opción quitada, todo es como antes."),
        tr('Despegar y la altura. Al subir estás en tierra. Flecha arriba despega. En el aire, la D sube y la A baja; con mando, la palanca derecha hacia los lados. Una nota suena al cambiar de altura: cuanto más aguda, más alto. Por debajo de {alta} metros vuelas bajo, como siempre. Por encima, la policía de tierra te pierde de vista.').format(alta=(alta)),
        tr("Aterrizar. Frena y pulsa F: el aparato baja solo y, al tocar tierra, te bajas. Un helicóptero se posa en un helipuerto, una calle o un espacio abierto. "
        "Una avioneta necesita la pista de un aeropuerto o un aeródromo; en otro sitio es un aterrizaje forzoso, que el juego te hace confirmar y que daña el aparato."),
        tr('Combustible. Cada aparato tiene su depósito: un helicóptero hace unos {int} kilómetros y una avioneta unos {int2}. Se reposta con Intro en un helipuerto, un aeropuerto o un aeródromo. El juego avisa en la reserva y cuando queda muy poco. Si se acaba, el motor se para y planeas hasta donde llegues. Se puede quitar en Opciones.').format(int=(int(V.aeronave({'id': 'helicoptero'})['autonomia'])), int2=(int(V.aeronave({'id': 'avioneta'})['autonomia']))),
        tr("La travesía. Al llegar volando al borde de la localidad, o con Intro en un campo, eliges destino y cómo llegar. Entonces vuelas de verdad: la torre te da el viento y el rumbo, subes a tu nivel y cruzas la comarca. "
        "El piloto automático lo hace todo si quieres, y la N acelera el viaje. Intro te dice en cualquier momento cuánto falta."),
        tr("Lo que pasa en el aire. Turbulencias, otro aparato a tu altura al que hay que dejar paso subiendo o bajando, y tormentas que puedes rodear, pasar por encima si tu aparato sube lo bastante, o atravesar. Con lluvia hay más viento y más tormentas."),
        tr("Llegar. O aterrizas en el campo, con la torre guiándote, o entras volando bajo sobre la localidad y te posas donde quieras. Con el aterrizaje asistido, que viene puesto, el aparato baja y se encara solo. "
        "A mano, baja a la altitud que dice la torre y mantén en el centro los chasquidos de alineación."),
        tr('Hangares. En cada campo puedes alquilar una plaza, a {precio} euros al día, o comprarla. Caben {entero} aeronaves. Lo guardado no se pierde, y allí se reposta y se repara. Tus aeronaves salen en el móvil, en Mis vehículos: desde allí las marcas en el GPS o mandas una al hangar por {precio2} euros.').format(precio=(p.precio('hangar_alquiler', 120)), entero=(AJ.entero('hangar_plazas')), precio2=(p.precio('mandar_hangar', 250))),
        tr("Piloto comercial. Con la licencia, que se saca en una academia, cada campo ofrece tres vuelos al día de pasaje o de carga. Vuelas hasta el campo de destino y cobras al aterrizar. Es trabajo legal."),
    ]
    if solo == "secuestro":
        lineas = secuestro
    elif not p.en_servidor:
        lineas += secuestro
    else:
        lineas.append(tr("En un servidor en línea se vuela igual y los hangares funcionan, pero no hay secuestros ni vuelos comerciales."))
    ops = [Opcion(t.rstrip("."), ayuda=tr("Un apartado de la explicación. Con las flechas pasas al siguiente o vuelves al anterior.")) for t in lineas]
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, tr("Volar: cómo funciona. Recorre la explicación con las flechas"), ops)
    app.abrir(m)
