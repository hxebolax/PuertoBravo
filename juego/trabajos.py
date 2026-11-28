"""Trabajos secundarios: taxi, ambulancia, autobús, vigilante, transporte, pizzas y carreras."""
from .i18n import tr
import math
import random

from . import mundo as M

NOMBRE_TRABAJO = {"taxi": tr("taxista"), "ambulancia": tr("conductor[|a] de ambulancia"), "autobus": tr("conductor[|a] de autobús"),
                  "vigilante": tr("vigilante"), "camion": tr("transportista"), "helados": tr("helader[o|a]"), "mensajeria": tr("mensajer[o|a] del mar"),
                  "bomberos": tr("bomber[o|a]"), "grua": tr("conductor[|a] de grúa"), "paqueteria": tr("mensajer[o|a]")}


def _agotado(t):
    """¿Se ha acabado el tiempo del servicio? Un servicio sin tiempo límite (None) no se agota nunca."""
    return t.get("limite") is not None and t["limite"] <= 0


def _resto(t):
    """Segundos que quedan, para calcular la propina. Sin límite, o ya pasado, cero."""
    return max(0, t.get("limite") or 0)

class Trabajos:
    def _destino_azar(self, minimo=150, maximo=650, excluir=None, sin_tipos=()):
        x, y = self.pos()
        mias = set(self.j.propiedades)                           # nadie pide una pizza desde una casa tuya donde no vive nadie
        todos = [l for l in self.mundo.lugares.values() if l.tipo not in ("salida", "muelle", "embarcadero") + tuple(sin_tipos) and "xy" not in l.d and l.id not in mias]
        ops = [l for l in todos if minimo <= math.hypot(l.x - x, l.y - y) <= maximo and l is not excluir]
        return random.choice(ops or todos or list(self.mundo.lugares.values()))

    def _dist(self, l):
        """Distancia al lugar, o infinito si está en otro mapa."""
        if l.mapa != self.mundo.id:
            return 1e9
        x, y = self.pos()
        return math.hypot(l.x - x, l.y - y)

    def _parado_en(self, l, radio=18):
        v = self.j.veh
        return self._dist(l) <= radio and (v is None or abs(v.vel) < 2.5)

    def terminar_trabajo(self, texto):
        if not self.trabajo:
            return
        t = self.trabajo
        self.trabajo = None
        if t.get("tipo") == "policia":                           # fin del turno: se retira lo del aviso y se devuelve el coche patrulla
            self.fin_turno_limpieza(t)
        if self.gps:
            self.quitar_gps_auto(fin=True)
        o = t.get("objetivo")
        if o is not None and not o.muerto:
            self.quitar_vehiculo(o)
        if t.get("canal") is not None:
            t["canal"].parar()
        if texto:
            resumen = ""
            if t.get("hechas"):
                resumen = tr(' Has completado {hechas} servicios y ganado {ganado} euros.').format(hechas=(t['hechas']), ganado=(t['ganado']))
            self.decir(texto + resumen)

    # ----------------------------------------------- trabajos con vehículo (J)
    def alternar_trabajo(self):
        j = self.j
        v = j.veh
        if self.de_servicio():                                   # de policía: la J termina el turno
            self.terminar_turno()
            return
        if self.trabajo and self.trabajo.get("veh") is v:
            self.terminar_trabajo(tr("Fin del servicio."))
            return
        tipo = v.modelo.get("trabajo") if v else None
        if not tipo:
            self.decir(tr("Este vehículo no sirve para trabajar. Prueba con un taxi, una ambulancia, un autobús, un coche patrulla o un camión."), True)
            return
        if tipo == "vigilante" and self.es_agente():             # con placa, el coche patrulla es para el turno de policía
            self.empezar_turno(veh=v)
            return
        if self.mision and not self.practica_de("trabajar", "servicio"):
            self.decir(tr("No puedes trabajar durante una misión."), True)
            return
        if j.estrellas:
            self.decir(tr("No puedes trabajar mientras te busca la policía."), True)
            return
        if tipo == "mensajeria" and self.mundo.tipo != "mar":
            self.decir(tr("Zarpa primero: los repartos se hacen por mar."), True)
            return
        if tipo == "ambulancia" and not any(l.tipo == "hospital" for l in self.mundo.lugares.values()):
            self.decir(tr("Aquí no hay hospital al que llevar a los heridos."), True)
            return
        if self.trabajo:
            self.terminar_trabajo(None)
        self.trabajo = {"tipo": tipo, "veh": v, "hechas": 0, "ganado": 0, "limite": None}
        self.decir(tr('Empiezas a trabajar de {v}. Pulsa J otra vez para terminar.').format(v=(NOMBRE_TRABAJO[tipo])))
        self._servicio_nuevo()

    def _servicio_nuevo(self):
        t = self.trabajo
        tipo = t["tipo"]
        if tipo == "taxi":
            l = self._destino_azar(80, 350)
            t.update(fase="recoger", lugar=l, limite=None, texto=tr('Taxi: recoge al cliente en {nombre}.').format(nombre=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "ambulancia":
            l = self._destino_azar(120, 500, sin_tipos=("hospital",))       # el herido nunca está ya en un hospital
            d = self._dist(l)
            t.update(fase="recoger", lugar=l, limite=45 + d / 6.0, texto=tr('Ambulancia: hay un herido en {nombre}. ¡Date prisa!').format(nombre=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo in ("autobus", "helados"):
            if not t.get("paradas"):
                t["paradas"] = [self._destino_azar(100, 900) for _ in range(5)]
                t["n"] = 0
            l = t["paradas"][t["n"]]
            d = self._dist(l)
            que = tr("Autobús") if tipo == "autobus" else tr("Helados")
            t.update(lugar=l, limite=50 + d / 5.0, texto=tr('{que}: parada {v} de {len}, {nombre}.').format(que=(que), v=(t['n'] + 1), len=(len(t['paradas'])), nombre=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "mensajeria":
            x, y = self.pos()
            ops = [l for l in self.mundo.lugares.values() if math.hypot(l.x - x, l.y - y) > 350 and l.id not in self.j.propiedades]
            l = random.choice(ops or list(self.mundo.lugares.values()))
            d = self._dist(l)
            t.update(lugar=l, limite=None, dist=d, texto=tr('Mensajería del mar: lleva el paquete a {nombre}.').format(nombre=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "vigilante":
            l = self._destino_azar(150, 450)
            x, y, d = self.mundo.plaza_junto_a(l)
            m = self.mundo
            x, y = (x, m.carril("H", m._idx(y, m.NY), d)) if d in (1, 3) else (m.carril("V", m._idx(x, m.NX), d), y)
            modelo = random.choice(["sedan", "utilitario", "deportivo", "furgoneta"])
            o = self.crear_vehiculo(modelo, x, y, d, "huida", tr("Vehículo del sospechoso"), "objetivo")
            o.ocupado = True
            o.hostil = True
            o.vel_obj = min(o.modelo["vel_max"] * 0.6, 19.0)
            t.update(objetivo=o, limite=200.0, texto=tr('Vigilante: detén el vehículo del sospechoso, visto junto a {nombre}. Embístelo o dispárale.').format(nombre=(l.nombre)))
            self.objetivo = o
            self.fijar_gps(o.x, o.y, o.nombre, sigue=o, auto=True, callar=True)
        elif tipo == "bomberos":
            l = self._destino_azar(150, 700)
            d = self._dist(l)
            if t.get("canal") is not None:
                t["canal"].parar()
            t.update(lugar=l, limite=60 + d / 6.0, apagando=0.0, canal=self.son("fuego", bucle=True, xy=(l.x, l.y), ref=10, maxd=120),
                     texto=tr('Bomberos: hay un incendio en {nombre}. ¡Corre!').format(nombre=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "grua":
            l = self._destino_azar(120, 600)
            x, y, d = self.mundo.plaza_junto_a(l)
            self._despejar_plaza(x, y)
            mo = random.choice(["utilitario", "sedan", "furgoneta", "deportivo"])
            o = self.crear_vehiculo(mo, x, y, d, "aparcado", None, "grua")
            o.cerrado = True
            t.update(fase="recoger", lugar=l, objetivo=o, limite=None, texto=tr('Grúa: retira el {nombre} mal aparcado junto a {nombre2}.').format(nombre=(o.nombre), nombre2=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "paqueteria":
            l = self._destino_azar(120, 500)
            d = self._dist(l)
            t.update(lugar=l, limite=35 + d / 4.0, texto=tr('Mensajería: entrega el paquete en {nombre}.').format(nombre=(l.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "camion":
            otros = [m for m in self.mapas.values() if m.id != self.mundo.id and m.tipo not in ("mar", "recinto")
                     and any(l.tipo == "salida" for l in m.lugares.values()) and self.saltos_por_tierra(self.mundo.id, m.id) is not None]
            if not otros or not any(l.tipo == "salida" for l in self.mundo.lugares.values()):
                self.terminar_trabajo(tr("Desde aquí no sale ninguna carretera para los camiones."))
                return
            m = random.choice(otros)
            ops = [l for l in m.lugares.values() if l.tipo in ("tienda", "taller", "negocio", "comida", "desguace", "armeria", "pescaderia")]
            l = random.choice(ops or list(m.lugares.values()))
            saltos = self.saltos_por_tierra(self.mundo.id, m.id) or 1
            camino = tr("es la localidad vecina") if saltos == 1 else tr('hay que cruzar {v} {v2} por el camino').format(v=(saltos - 1), v2=(tr('localidad') if saltos == 2 else tr('localidades')))
            t.update(lugar=l, limite=None, texto=tr('Transporte: lleva la carga a {nombre}, en {nombre2}, sin bajarte del camión.').format(nombre=(l.nombre), nombre2=(m.nombre)))
            self.gps_a_lugar(l, auto=True, callar=True)
            if not t.get("explicado"):                           # la primera vez de cada turno, cómo va esto de principio a fin
                t["explicado"] = True
                self.decir(tr('La carga ya va en el camión: no hay que recoger nada. Se lleva por carretera a {nombre}: {camino}. El GPS te guía hasta la salida de la localidad; allí, sin bajarte, pulsa Intro para tomar la carretera, y al llegar te sigue guiando. Se entrega sola al parar delante del destino. No cojas el autobús ni te bajes: si dejas el camión, se acaba el trabajo.').format(nombre=(m.nombre), camino=(camino)))
        self.decir(t["texto"])
        if self.trabajo and self.gps:
            self.repetir_gps_suave()

    def _cobrar(self, paga, texto):
        t = self.trabajo
        paga = int(paga * self.mult_trabajo(t["tipo"]))
        t["hechas"] += 1
        t["ganado"] += paga
        self.j.stats["servicios"] = self.j.stats.get("servicios", 0) + 1
        self.dar_dinero(paga, texto)
        self.servicio_hecho(t["tipo"], NOMBRE_TRABAJO.get(t["tipo"], "trabajador[|a]"))

    # ----------------------------------------------------------------- pizzas
    def empezar_pizzas(self):
        if self.mision:
            self.decir(tr("No puedes trabajar durante una misión."), True)
            return
        if self.trabajo:
            self.terminar_trabajo(None)
        self.trabajo = {"tipo": "pizza", "quedan": 4, "ganado": 0, "limite": None}
        self.decir(tr("Reparto de pizzas: entrega cuatro pizzas antes de que se enfríen. Puedes ir a pie o en cualquier vehículo."))
        self._pizza_siguiente()

    def _pizza_siguiente(self):
        t = self.trabajo
        l = self._destino_azar(120, 420)
        d = self._dist(l)
        t.update(lugar=l, limite=40 + d / 3.0, texto=tr('Pizzas: entrega en {nombre}. Quedan {quedan}.').format(nombre=(l.nombre), quedan=(t['quedan'])))
        self.decir(t["texto"])
        self.gps_a_lugar(l, auto=True)

    # --------------------------------------------------------------- carreras
    def empezar_carrera(self, c):
        j = self.j
        if not j.veh:
            self.decir(tr("Necesitas un vehículo para correr."), True)
            return
        if self.mision:
            self.decir(tr("No puedes correr durante una misión."), True)
            return
        if self.trabajo:
            self.terminar_trabajo(None)
        if c.get("xy"):
            pts = [(float(x), float(y)) for x, y in c["puntos"]]
        else:
            pts = [(i * M.B, jj * M.B) for i, jj in c["puntos"]]
        self.trabajo = {"tipo": "carrera", "def": c, "puntos": pts, "idx": 1, "limite": float(c["tiempo"]),
                        "total": float(c["tiempo"]), "texto": tr('Carrera {nombre}.').format(nombre=(c['nombre']))}
        self.decir(tr('Carrera {nombre}: {v} puntos de control y {tiempo} segundos. ¡Ya!').format(nombre=(c['nombre']), v=(len(pts) - 1), tiempo=(c['tiempo'])))
        self.son("claxon", vol=0.6)
        self._carrera_punto()

    def _carrera_punto(self):
        t = self.trabajo
        x, y = t["puntos"][t["idx"]]
        nombre = tr('punto {idx} de {v}').format(idx=(t['idx']), v=(len(t['puntos']) - 1))
        if not t["def"].get("xy"):
            i, jj = int(round(x / M.B)), int(round(y / M.B))
            nombre += tr(', cruce de {v} con {v2}').format(v=(self.mundo.calles[jj]), v2=(self.mundo.avenidas[i]))
        t["texto"] = tr('Carrera {nombre}: {nombre2}.').format(nombre=(t['def']['nombre']), nombre2=(nombre))
        self.fijar_gps(x, y, nombre, auto=True, radio=14)

    # ------------------------------------------------------------ actualización
    def actualizar_trabajo(self, dt):
        t = self.trabajo
        if not t:
            return
        j = self.j
        x, y = self.pos()
        if t.get("limite") is not None:
            antes = t["limite"]
            t["limite"] -= dt
            for marca in (60, 30, 10):
                if antes > marca >= t["limite"]:
                    self.decir(tr('Quedan {marca} segundos.').format(marca=(marca)))
            if t["limite"] < 10 and int(antes) != int(t["limite"]):
                self.son("reloj", cat="interfaz")
        tipo = t["tipo"]
        if "veh" in t:
            if j.veh is not t["veh"]:
                self.terminar_trabajo(tr("Has dejado el vehículo de trabajo: se acaba el servicio.") + (tr(" La carga se queda sin entregar. Para volver a empezar, sube al camión y pulsa J.") if tipo == "camion" else ""))
                return
            if j.estrellas >= 2:
                self.terminar_trabajo(tr("Con la policía detrás se acabó el trabajo."))
                return
        if tipo == "taxi":
            l = t["lugar"]
            if t["fase"] == "recoger" and self._parado_en(l):
                self.son("puerta_coche")
                dest = self._destino_azar(200, 700, l)
                d = math.hypot(dest.x - l.x, dest.y - l.y)
                t.update(fase="llevar", lugar=dest, limite=35 + d / 7.0, dist=d, texto=tr('Taxi: lleva al cliente a {nombre}.').format(nombre=(dest.nombre)))
                self.decir(tr('El cliente sube. Quiere ir a {nombre}.').format(nombre=(dest.nombre)))
                self.gps_a_lugar(dest, auto=True)
            elif t["fase"] == "llevar":
                if self._parado_en(l):
                    j.stats["carreras_taxi"] += 1
                    self.son("puerta_coche")
                    self._cobrar(int(self.precio("paga_taxi", 15) + t["dist"] * 0.12 + _resto(t) * 1.5), tr("Carrera cobrada"))
                    self._servicio_nuevo()
                elif _agotado(t):
                    self.son("puerta_coche")
                    self.decir(tr("El cliente se ha hartado de esperar y se baja sin pagar."))
                    self._servicio_nuevo()
        elif tipo == "ambulancia":
            l = t["lugar"]
            if _agotado(t):
                self.decir(tr("Has llegado tarde. Otra ambulancia se ha hecho cargo."))
                self._servicio_nuevo()
            elif self._parado_en(l):
                self.son("puerta_coche")
                if t["fase"] == "recoger":
                    hospitales = [q for q in self.mundo.lugares.values() if q.tipo == "hospital"]
                    otros = [q for q in hospitales if q is not l] or hospitales              # a otro hospital que el sitio del herido
                    h = min(otros, key=lambda q: math.hypot(q.x - x, q.y - y))
                    d = self._dist(h)
                    t.update(fase="llevar", lugar=h, limite=40 + d / 6.0, dist=d, texto=tr('Ambulancia: lleva al herido a {nombre}.').format(nombre=(h.nombre)))
                    self.decir(tr('Herido a bordo. Llévalo a {nombre} cuanto antes.').format(nombre=(h.nombre)))
                    self.gps_a_lugar(h, auto=True)
                else:
                    self._cobrar(int(self.precio("paga_ambulancia", 60) + t["dist"] * 0.15 + _resto(t) * 2), tr("Herido entregado en urgencias"))
                    self._servicio_nuevo()
        elif tipo == "mensajeria":
            l = t["lugar"]
            if self._parado_en(l, 32):
                self.son("salpicadura", vol=0.5)
                self._cobrar(int(self.precio("paga_mensajeria", 40) + t["dist"] * 0.22), tr("Paquete entregado"))
                self._servicio_nuevo()
        elif tipo in ("autobus", "helados"):
            l = t["lugar"]
            if self._parado_en(l):
                self.son("lugar_estacion" if tipo == "autobus" else "claxon_helados", vol=0.5)
                self._cobrar(int(self.precio("paga_parada", 18) + _resto(t) * 0.6), tr("Parada hecha"))
                t["n"] += 1
                if t["n"] >= len(t["paradas"]):
                    self.dar_dinero(self.precio("prima_linea", 100), tr("Línea completa, prima"))
                    t["paradas"] = None
                self._servicio_nuevo()
            elif _agotado(t):
                self.decir(tr("Vas con retraso y los viajeros protestan. Siguiente parada."))
                t["n"] += 1
                if t["n"] >= len(t["paradas"]):
                    t["paradas"] = None
                self._servicio_nuevo()
        elif tipo == "vigilante":
            o = t.get("objetivo")
            if o is None or o.muerto:
                t["objetivo"] = None
                self._cobrar(int(self.precio("paga_vigilante", 220) + _resto(t)), tr("Sospechoso detenido"))
                self._servicio_nuevo()
            elif _agotado(t) or o.dist(x, y) > 700:
                self.quitar_vehiculo(o)
                t["objetivo"] = None
                self.decir(tr("El sospechoso se ha escapado."))
                self._servicio_nuevo()
        elif tipo == "camion":
            l = t["lugar"]
            if self._parado_en(l):
                self.son("puerta_coche")
                self._cobrar(random.randint(350, 600), tr('Carga entregada en {nombre}').format(nombre=(l.nombre)))
                self._servicio_nuevo()
        elif tipo == "bomberos":
            l = t["lugar"]
            if self._parado_en(l, 22):
                if t["apagando"] == 0.0:
                    self.decir(tr("Mangueras fuera. Aguanta junto al fuego unos segundos."))
                t["apagando"] += dt
                if t["apagando"] >= 5.0:
                    t["canal"].parar()
                    t["canal"] = None
                    self.son("salpicadura", vol=0.6)
                    self._cobrar(int(self.precio("paga_bomberos", 90) + _resto(t) * 1.5), tr("Incendio apagado"))
                    self._servicio_nuevo()
            elif _agotado(t):
                self.decir(tr("Has llegado tarde: el edificio ha ardido entero."))
                self._servicio_nuevo()
        elif tipo == "grua":
            l = t["lugar"]
            if t["fase"] == "recoger" and self._parado_en(l, 16):
                o = t.get("objetivo")
                if o is not None and not o.muerto:
                    self.quitar_vehiculo(o)
                t["objetivo"] = None
                self.son("reparar", vol=0.6)
                des = [q for q in self.mundo.lugares.values() if q.tipo == "desguace"]
                dest = min(des, key=lambda q: math.hypot(q.x - x, q.y - y)) if des else self._destino_azar(200, 700, l)
                t.update(fase="llevar", lugar=dest, dist=self._dist(dest), texto=tr('Grúa: lleva el coche enganchado a {nombre}.').format(nombre=(dest.nombre)))
                self.decir(tr('Coche enganchado. Llévalo a {nombre}.').format(nombre=(dest.nombre)))
                self.gps_a_lugar(dest, auto=True)
            elif t["fase"] == "llevar" and self._parado_en(l):
                self.son("reparar", vol=0.6)
                self._cobrar(int(self.precio("paga_grua", 110) + t["dist"] * 0.18), tr("Coche entregado en el depósito"))
                self._servicio_nuevo()
        elif tipo == "paqueteria":
            l = t["lugar"]
            if self._parado_en(l):
                self._cobrar(int(self.precio("paga_paqueteria", 15) + _resto(t) * 0.8), tr("Paquete entregado"))
                self._servicio_nuevo()
            elif _agotado(t):
                self.decir(tr("Vas tarde: este paquete ya no tiene propina."))
                t["limite"] = None
        elif tipo == "pizza":
            l = t["lugar"]
            if self._dist(l) <= (18 if j.veh else 7) and (not j.veh or abs(j.veh.vel) < 2.5):
                paga = int(self.precio("paga_pizza", 20) + _resto(t) * 0.8)
                t["quedan"] -= 1
                t["ganado"] += paga
                j.stats["pizzas"] += 1
                self.dar_dinero(paga, tr("Pizza entregada"))
                if t["quedan"] <= 0:
                    propina = self.precio("propina_reparto", 60)
                    self.dar_dinero(propina, tr("Propina por completar el reparto"))
                    self.terminar_trabajo(tr('Reparto terminado. Has ganado {v} euros.').format(v=(t['ganado'] + propina)))
                else:
                    self._pizza_siguiente()
            elif _agotado(t):
                self.terminar_trabajo(tr("La pizza se ha enfriado. Te quedas sin trabajo por hoy."))
        elif tipo == "carrera":
            if not j.veh:
                self.terminar_trabajo(tr("Te has bajado del vehículo: carrera abandonada."))
                return
            px, py = t["puntos"][t["idx"]]
            if math.hypot(px - x, py - y) <= (25 if t["def"].get("xy") else 14):
                t["idx"] += 1
                self.son("llegada", cat="interfaz")
                if t["idx"] >= len(t["puntos"]):
                    c = t["def"]
                    tiempo = t["total"] - t["limite"]
                    primera = c["id"] not in j.stats["carreras"]
                    premio = c["premio"] if primera else c["premio"] // 3
                    if primera:
                        j.stats["carreras"].append(c["id"])
                    self.trabajo = None
                    self.cancelar_gps()
                    self.app.son("mision_ok")
                    self.decir(tr('¡Meta! Has terminado {nombre} en {int} segundos.').format(nombre=(c['nombre']), int=(int(tiempo))))
                    self.dar_dinero(premio, tr("Premio"))
                else:
                    self._carrera_punto()
            elif _agotado(t):
                self.terminar_trabajo(tr("Se acabó el tiempo. Has perdido la carrera."))


def _pl():
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False


if _pl():
    NOMBRE_TRABAJO.update({"taxi": "[taksówkarz|taksówkarka]", "vigilante": "[strażnik|strażniczka]", "camion": "[przewoźnik|przewoźniczka]"})
