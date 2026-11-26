"""Mis vehículos y el chófer de la banda.

- Mis vehículos: los vehículos tuyos (comprados, mejorados en el taller, sacados de un garaje o con nombre puesto por ti)
  no desaparecen al alejarte ni al coger otro. Los que están en la calle de la localidad en la que estás son vehículos
  de verdad, marcados con `v.mio`; los de las demás localidades esperan en `Partida.mis_lejos`, como datos, hasta que
  vuelves. Todos se guardan con la partida. Hay un tope en la calle (en los datos): al pasarse, el más antiguo va solo
  a un garaje con sitio, y si no lo hay, se avisa.
- En un servidor en línea los vehículos de la calle los lleva el servidor, con su propio máximo por jugador: aquí no
  se marca ni se guarda nada, y la lista del móvil enseña lo que el servidor reconoce como tuyo.
- Chófer: alguien de tu banda viene con un vehículo de tu garaje o con uno de la banda, y conduce él hasta el destino
  que marques en el GPS, con el piloto que ya existe. Tú vas de pasajero.
- Seguro: uno solo, que cubre todos tus vehículos de tierra. Se contrata en Mis vehículos y cubre desde el día siguiente.
  Cada medianoche cobra una cuota por cada vehículo tuyo que esté en la calle (los del garaje no pagan). Si uno explota,
  la grúa del seguro se lo lleva y al día siguiente te lo devuelven reparado, con sus mejoras, en un garaje tuyo con
  sitio o a la puerta de un taller, a cambio de una franquicia. No en un servidor, ni para las aeronaves.
"""
from .i18n import tr
import math
import random

from . import mundo as M
from . import registro
from .menus import EntradaTexto, Menu, Opcion

AJUSTES = {"tope_calle": 6, "chofer_espera_min": 25, "chofer_espera_max": 75, "chofer_busqueda_max": 2,
           "seguro_cuota": 12, "seguro_franquicia_pct": 10, "seguro_franquicia_min": 150}
_MINIMOS = {"chofer_busqueda_max": 0, "seguro_cuota": 0, "seguro_franquicia_pct": 0, "seguro_franquicia_min": 0}
_LISTAS = {
    "chofer_modelos": ["sedan", "todoterreno", "utilitario"],
    "chofer_frases_sale": [tr("Voy para allá. Dame un minuto."), tr("Arranco ahora mismo. No te muevas de ahí."), tr("Hecho. Salgo ya."), tr("Cojo las llaves y voy.")],
    "chofer_frases_llega": [tr("Ya estoy aquí. Sube cuando quieras."), tr("Tu coche, jef[e|a]. Sube."), tr("Aquí me tienes. ¿Nos vamos?")],
    "chofer_frases_destino": [tr("¿A dónde vamos? Márcame el sitio."), tr("Tú dirás a dónde."), tr("Dime dónde y te llevo.")],
    "chofer_frases_marcha": [tr("Marchando."), tr("Vamos para allá."), tr("Agárrate, que salimos."), tr("Eso está hecho.")],
    "chofer_frases_llegada": [tr("Hemos llegado."), tr("Ya estamos."), tr("Aquí es.")],
    "chofer_frases_espera": [tr("Te espero aquí."), tr("Aquí me quedo, con el motor a punto."), tr("No me muevo de aquí.")],
    "chofer_frases_adios": [tr("Hasta luego, jef[e|a]."), tr("Cuando me necesites, llama."), tr("Me vuelvo con los demás.")],
    "nombres_propuestos": [tr("La Gaviota"), tr("El Rayo"), tr("La Tormenta"), tr("El Tiburón"), tr("La Centella"), tr("El Viejo"), tr("La Fiera"), tr("El Fantasma")],
}
LISTAS = {k: list(v) for k, v in _LISTAS.items()}
NOMBRE_MAX = 30


def configurar(datos):
    """El tope de vehículos en la calle y lo del chófer salen de los datos (vida.json, vehiculos_propios), que un mod puede cambiar."""
    c = next((x for x in datos.get("vehiculos_propios", []) if isinstance(x, dict)), {})
    for k, serie in (("tope_calle", 6), ("chofer_espera_min", 25), ("chofer_espera_max", 75), ("chofer_busqueda_max", 2),
                     ("seguro_cuota", 12), ("seguro_franquicia_pct", 10), ("seguro_franquicia_min", 150)):
        try:
            AJUSTES[k] = max(_MINIMOS.get(k, 1), int(c.get(k, serie)))
        except (TypeError, ValueError):
            AJUSTES[k] = serie
    for k, serie in _LISTAS.items():
        v = c.get(k)
        LISTAS[k] = [str(x) for x in v if str(x).strip()] if isinstance(v, list) and any(str(x).strip() for x in v) else list(serie)


def tope():
    return AJUSTES["tope_calle"]


def nombres_propuestos(n=6, rng=random):
    """Unos cuantos nombres al azar para un vehículo: para quien no quiere, o no puede, escribirlo (con mando, por ejemplo)."""
    lista = list(dict.fromkeys(LISTAS["nombres_propuestos"]))
    return rng.sample(lista, min(n, len(lista)))


def _modelo_nombre(p, ident):
    mo = p.modelos.get(ident)
    return mo["nombre"] if mo else str(ident)


def nombre_completo(p, nombre, modelo_id):
    """«Rayo, Deportivo Centella» si le has puesto nombre; si no, solo el modelo."""
    mod = _modelo_nombre(p, modelo_id)
    return f"{nombre}, {mod}" if nombre and nombre != mod else mod


def _mejoras_txt(mejoras):
    from . import sistemas

    class _V:
        pass
    v = _V()
    v.mejoras = dict(mejoras or {})
    return sistemas.resumen(v)


class MisVehiculos:
    """Mixin de Partida."""

    def mis_iniciar(self):
        self.mis_lejos = []              # tus vehículos aparcados en otras localidades: datos, hasta que vuelves
        self.mio_sec = 0                 # para saber cuál es el más antiguo
        self.chofer = None

    # ------------------------------------------------------------------ cuáles son tuyos
    def es_mio(self, v):
        return v is not None and bool(getattr(v, "mio", False))

    def puede_ser_mio(self, v):
        """¿Se puede quedar el jugador con este vehículo? No los de una misión o de la banda, ni los barcos (van por su lado)."""
        return v is not None and not v.muerto and not v.tag and not v.modelo.get("barco") and self.mundo.tipo != "mar"

    def hacer_mio(self, v, callar=False):
        """Desde ahora este vehículo es tuyo: no desaparece, se guarda con la partida y sale en Mis vehículos."""
        if getattr(self, "en_servidor", False) or not self.puede_ser_mio(v):
            return False
        if self.es_mio(v):
            return True
        self.mio_sec += 1
        v.mio, v.mio_n, v.propio = True, self.mio_sec, True
        v.cerrado = False
        if v.plaza is not None:                                  # deja de ser un coche de esa plaza: no vuelve a salir otro encima
            self.plazas_usadas.add(v.plaza)
            self.plazas_activas.pop(v.plaza, None)
            v.plaza = None
        self._tope_mis_vehiculos(v, callar)
        return True

    def mis_vivos(self):
        """Tus vehículos que están en la calle de esta localidad (también el que llevas)."""
        return sorted((v for v in self.vehiculos if self.es_mio(v) and not v.muerto), key=lambda v: getattr(v, "mio_n", 0))

    def mis_en_calle(self):
        """Cuántos vehículos tuyos hay fuera de los garajes, en todas las localidades."""
        return len(self.mis_vivos()) + len(self.mis_lejos)

    def mis_en_garajes(self):
        return sum(len(g) for g in self.j.garajes.values())

    def garaje_con_sitio(self):
        """Una casa tuya con plaza libre; antes, las de esta localidad."""
        casas = [l for l in (self.lug(pid) for pid in self.j.propiedades) if l is not None and int(l.get("garaje", 0)) > len(self.j.garajes.get(l.id, [])) and not self.alquilada(l.id)]
        casas.sort(key=lambda l: l.mapa != self.mundo.id)
        return casas[0] if casas else None

    def _ficha_garaje(self, v):
        d = {"modelo": v.modelo["id"], "salud": v.salud, "nombre": v.nombre, "mejoras": dict(getattr(v, "mejoras", {}))}
        if getattr(v, "litros", None) is not None:
            d["litros"] = round(v.litros, 1)
        return self.averias_a_dict(v, d)

    def _tope_mis_vehiculos(self, nuevo, callar=False):
        """Con más vehículos en la calle que el tope, el más antiguo va solo a un garaje con sitio. Sin sitio, se avisa."""
        n = self.mis_en_calle()
        if n <= tope():
            return
        vuela = lambda ident: bool((self.modelos.get(ident) or {}).get("vuela"))      # noqa: E731  (las aeronaves no van a un garaje: van a un hangar)
        viejos = sorted([(getattr(v, "mio_n", 0), v) for v in self.mis_vivos() if v is not nuevo and v is not self.j.veh and not getattr(v, "con_chofer", False) and not v.modelo.get("vuela")]
                        + [(int(d.get("n", 0)), d) for d in self.mis_lejos if not vuela(d.get("modelo"))], key=lambda e: e[0])
        casa = self.garaje_con_sitio()
        if not viejos or casa is None:
            if not callar:
                self.son("notificacion", cat="interfaz", vol=0.5)
                self.decir(tr('Tienes {n} vehículos en la calle y lo razonable son {tope}. No queda sitio en tus garajes: siguen todos a salvo, pero vende alguno o compra una casa con garaje. Los tienes en el móvil, en Mis vehículos.').format(n=(n), tope=(tope())))
            return
        viejo = viejos[0][1]
        if isinstance(viejo, dict):
            self.mis_lejos.remove(viejo)
            ficha = {k: viejo[k] for k in ("modelo", "salud", "nombre", "mejoras", "litros", "km", "pinchada", "revision") if k in viejo}
            nombre = viejo.get("nombre") or _modelo_nombre(self, viejo["modelo"])
        else:
            ficha, nombre = self._ficha_garaje(viejo), viejo.nombre
            if self.ultimo_veh is viejo:
                self.ultimo_veh = None
            self.quitar_vehiculo(viejo)
        self.j.garajes.setdefault(casa.id, []).append(ficha)
        if not callar:
            self.son("notificacion", cat="interfaz", vol=0.5)
            self.decir(tr('Tienes más de {tope} vehículos en la calle: tu mecánico se lleva {nombre}, el que más tiempo llevaba aparcado, al garaje de {nombre_lugar}.').format(tope=(tope()), nombre=(nombre), nombre_lugar=(self.nombre_lugar(casa))))

    # ------------------------------------------------------------------ el seguro
    def seguro_cubre(self):
        """¿Tienes el seguro y ya cubre? Cubre desde el día siguiente a contratarlo."""
        desde = int(getattr(self.j, "seguro_desde", 0) or 0)
        return 0 < desde <= self.dia and not getattr(self, "en_servidor", False)

    def _seguro_cubre_modelo(self, ident):
        return not bool((self.modelos.get(ident) or {}).get("vuela"))

    def seguro_en_calle(self):
        """Cuántos vehículos tuyos de tierra hay en la calle: por cada uno se paga la cuota."""
        return (sum(1 for v in self.mis_vivos() if not v.modelo.get("vuela"))
                + sum(1 for d in self.mis_lejos if self._seguro_cubre_modelo(d.get("modelo"))))

    def seguro_franquicia(self, ident):
        mo = self.modelos.get(ident) or {}
        return max(AJUSTES["seguro_franquicia_min"], int(int(mo.get("precio", 0) or 0) * AJUSTES["seguro_franquicia_pct"] / 100.0))

    def seguro_contratar(self, si=True):
        j = self.j
        if getattr(self, "en_servidor", False):
            return False
        self.son("menu_ok", cat="interfaz")
        if si:
            j.seguro_desde = self.dia + 1
            self.decir(tr('Seguro contratado. Cubre a todos tus vehículos de tierra desde mañana. Cada medianoche se cobran {seguro_cuota} euros por cada uno que tengas en la calle; los del garaje no pagan. Si uno explota, te lo devuelven reparado y con sus mejoras al día siguiente, pagando la franquicia.').format(seguro_cuota=(AJUSTES['seguro_cuota'])), True)
        else:
            j.seguro_desde = 0
            self.decir(tr("Seguro dado de baja. Lo que esté ya en manos del seguro te lo devuelven igual."), True)
        return True

    def seguro_siniestro(self, v):
        """Un vehículo tuyo ha explotado. Con seguro, la grúa se lo lleva; sin él, se pierde, y se dice que el seguro existe."""
        if getattr(self, "en_servidor", False) or v.modelo.get("vuela"):
            return False
        if not self.seguro_cubre():
            self.decir(tr('{nombre} se ha perdido con todas sus mejoras. Con el seguro de tus vehículos, que se contrata en el móvil, en Mis vehículos, te lo habrían devuelto.').format(nombre=(v.nombre)))
            return False
        ficha = self._ficha_garaje(v)
        ficha["salud"] = float(v.salud_max)
        ficha.pop("pinchada", None)
        pend = {"ficha": ficha, "dia": self.dia + 1, "franquicia": self.seguro_franquicia(v.modelo["id"])}
        self.j.seguro_pend = list(getattr(self.j, "seguro_pend", None) or []) + [pend]
        self.decir(tr('La grúa de tu seguro se lleva lo que queda de {nombre}. Mañana te lo devuelven reparado, con sus mejoras, por {franquicia} euros de franquicia.').format(nombre=(v.nombre), franquicia=(pend['franquicia'])))
        return True

    def _seguro_cobrar(self, n):
        """Cobra del bolsillo y, si no llega, del banco. False si entre los dos no hay bastante."""
        j = self.j
        if j.dinero + j.banco < n:
            return False
        quita = min(j.dinero, n)
        j.dinero -= quita
        j.banco -= n - quita
        return True

    def dia_seguro(self):
        """Cada medianoche: la cuota del seguro y los vehículos que el seguro tiene ya reparados."""
        j = self.j
        if getattr(self, "en_servidor", False):
            return
        if int(getattr(j, "seguro_desde", 0) or 0) > 0:
            cuota = AJUSTES["seguro_cuota"] * self.seguro_en_calle()
            if cuota > 0:
                if self._seguro_cobrar(cuota):
                    j.stats["seguro_pagado"] = j.stats.get("seguro_pagado", 0) + cuota
                else:
                    j.seguro_desde = 0
                    self.son("error", cat="interfaz")
                    self.decir(tr('No tienes los {cuota} euros de la cuota del seguro, ni en el bolsillo ni en el banco: te dan de baja. Puedes volver a contratarlo en Mis vehículos.').format(cuota=(cuota)))
        for pend in list(getattr(j, "seguro_pend", None) or []):
            if pend.get("dia", 0) > self.dia:
                continue
            ficha = pend["ficha"]
            nombre = ficha.get("nombre") or _modelo_nombre(self, ficha.get("modelo"))
            casa = self.garaje_con_sitio()
            if casa is None and (self.mundo.tipo == "mar" or ficha.get("modelo") not in self.modelos):
                continue                                         # en mitad del mar no te lo pueden dejar: mañana
            franquicia = int(pend.get("franquicia", 0))
            if not self._seguro_cobrar(franquicia):
                if not pend.get("avisado"):
                    pend["avisado"] = True
                    self.decir(tr('El seguro ya tiene {nombre} reparado, pero te faltan los {franquicia} euros de la franquicia. Te lo guardan hasta que los tengas.').format(nombre=(nombre), franquicia=(franquicia)))
                continue
            j.seguro_pend.remove(pend)
            j.stats["seguro_pagado"] = j.stats.get("seguro_pagado", 0) + franquicia
            self.son("notificacion", cat="interfaz", vol=0.6)
            if casa is not None:
                j.garajes.setdefault(casa.id, []).append(ficha)
                self.decir(tr('Pagas {franquicia} euros de franquicia y el seguro te deja {nombre} reparado en el garaje de {nombre_lugar}.').format(franquicia=(franquicia), nombre=(nombre), nombre_lugar=(self.nombre_lugar(casa))))
                continue
            talleres = [l for l in self.mundo.lugares.values() if l.tipo == "taller"]
            x0, y0 = self.pos()
            taller = min(talleres, key=lambda l: math.hypot(l.x - x0, l.y - y0)) if talleres else None
            if taller is not None:
                x, y, d = self.mundo.plaza_junto_a(taller)
                donde = tr('a la puerta de {nombre}').format(nombre=(taller.nombre))
            else:
                x, y, d = self.plaza_cercana()
                donde = tr("aparcado a tu lado")
            v = self._veh_de_dict(dict(ficha, rumbo=d * 90.0), x, y)
            self.hacer_mio(v, callar=True)
            self.decir(tr('Pagas {franquicia} euros de franquicia y el seguro te deja {nombre} reparado {donde}, porque no tenías sitio en tus garajes.').format(franquicia=(franquicia), nombre=(nombre), donde=(donde)))

    def seguro_txt(self):
        j = self.j
        n = self.seguro_en_calle()
        pend = len(getattr(j, "seguro_pend", None) or [])
        espera = tr(' El seguro tiene {pend} {v} en reparación.').format(pend=(pend), v=(tr('vehículo tuyo') if pend == 1 else tr('vehículos tuyos'))) if pend else ""
        if int(getattr(j, "seguro_desde", 0) or 0) <= 0:
            return tr('Seguro de tus vehículos: sin contratar. Costaría {v} euros al día con los que tienes ahora en la calle.{espera}').format(v=(AJUSTES['seguro_cuota'] * n), espera=(espera))
        cubre = tr("cubre desde mañana") if not self.seguro_cubre() else "contratado"
        return (tr('Seguro de tus vehículos: {cubre}. Pagas {seguro_cuota} euros al día por cada uno en la calle; ahora, {v}. Llevas pagados {int} euros, franquicias incluidas.{espera}').format(cubre=(cubre), seguro_cuota=(AJUSTES['seguro_cuota']), v=(AJUSTES['seguro_cuota'] * n), int=(int(j.stats.get('seguro_pagado', 0))), espera=(espera)))

    # ------------------------------------------------------------------ guardar y cargar
    def _veh_de_dict(self, d, x=None, y=None):
        """Pone en la calle un vehículo guardado como datos, con su estado, sus mejoras, su combustible y su desgaste."""
        from . import sistemas
        v = self.crear_vehiculo(d["modelo"], float(d.get("x", self.j.x)) if x is None else x, float(d.get("y", self.j.y)) if y is None else y,
                                M.dir_de_rumbo(d.get("rumbo", 0)), None, d.get("nombre"))
        sistemas.poner(v, d.get("mejoras"))
        v.salud = min(v.salud_max, float(d.get("salud", v.salud_max)))
        v.rumbo = float(d.get("rumbo", 0))
        v.propio = True
        if v.nombre != v.modelo["nombre"]:
            registro.ocultar(v.nombre)                           # un nombre escrito por el jugador no se anota en el registro
        if "litros" in d:
            v.litros = float(d["litros"])
        self.averias_de_dict(v, d)
        return v

    def mis_a_dict(self, d, ultimo=None):
        """Añade a la partida que se guarda tus vehículos de la calle, de esta localidad y de las demás."""
        if getattr(self, "en_servidor", False):
            return
        lista = []
        for v in self.mis_vivos():
            if v is self.j.veh:
                continue
            f = dict(self._veh_fuera_dict(v), n=int(getattr(v, "mio_n", 0)))
            if v is ultimo:
                f["ultimo"] = True
            lista.append(f)
        lista += [dict(x) for x in self.mis_lejos]
        if lista:
            d["mis_vehiculos"] = lista
        if self.mio_sec:
            d["mio_sec"] = self.mio_sec

    def mis_cargar(self, d):
        """Lee tus vehículos de una partida guardada. Las partidas anteriores no traen la lista: el vehículo que tenían
        guardado, si llevaba mejoras del taller, pasa a ser tuyo, que para eso las pagaste."""
        self.mis_lejos = [dict(x) for x in (d.get("mis_vehiculos") or []) if isinstance(x, dict) and x.get("modelo")]
        try:
            self.mio_sec = max([int(d.get("mio_sec", 0) or 0)] + [int(x.get("n", 0) or 0) for x in self.mis_lejos])
        except (TypeError, ValueError):
            self.mio_sec = len(self.mis_lejos)
        f = self.veh_fuera
        if isinstance(f, dict) and f.get("modelo") and any((f.get("mejoras") or {}).values()) and "mis_vehiculos" not in d:
            self.mio_sec += 1
            self.mis_lejos.append(dict(f, n=self.mio_sec, ultimo=True))
            self.veh_fuera = None

    def _reponer_mis_vehiculos(self):
        """Vuelve a poner en la calle tus vehículos aparcados en esta localidad, al cargar la partida o al volver a ella."""
        if getattr(self, "en_servidor", False):
            return []
        puestos = []
        for d in list(self.mis_lejos):
            if d.get("mapa") != self.mundo.id or d.get("modelo") not in self.modelos:
                continue
            self.mis_lejos.remove(d)
            v = self._veh_de_dict(d)
            v.mio, v.mio_n = True, int(d.get("n", 0) or 0)
            if d.get("ultimo") and not self.j.veh and self.ultimo_veh is None:
                self.ultimo_veh = v
            puestos.append(v)
        return puestos

    def mis_al_cambiar_mapa(self, ultimo=None):
        """Antes de dejar una localidad: tus vehículos aparcados en ella se quedan apuntados, y allí estarán al volver."""
        if getattr(self, "en_servidor", False):
            return
        if ultimo is not None:                                   # el último que has usado es uno de aquí: los de antes ya no lo son
            for d in self.mis_lejos:
                d.pop("ultimo", None)
        for v in self.mis_vivos():
            if v is self.j.veh:
                continue
            f = dict(self._veh_fuera_dict(v), n=int(getattr(v, "mio_n", 0)))
            if v is ultimo:
                f["ultimo"] = True
            self.mis_lejos.append(f)

    def mis_al_servidor(self):
        """Al entrar en un servidor: allí los vehículos de la calle los lleva el servidor."""
        self.mis_lejos = []
        for v in self.vehiculos:
            if getattr(v, "mio", False):
                v.mio = False

    def dejar_o_quitar(self, v):
        """Te quedas sin el vehículo que llevas porque el juego te lleva a otro sitio: si es tuyo, se queda aparcado donde
        estaba; si no, desaparece, como siempre."""
        if v is None:
            return
        if self.j.veh is v:
            self.salir_vehiculo(forzado=True)
        if not self.es_mio(v):
            self.quitar_vehiculo(v)

    # ------------------------------------------------------------------ cuando el juego te lleva a otro sitio
    def vehiculo_para_llevar(self):
        """El vehículo que va contigo cuando el juego te devuelve a otro sitio: el que conduces o el que acabas de dejar
        al lado, si es de calle (ni de una misión ni de la banda, ni un barco, ni algo que vuela, ni con chófer)."""
        v = self.j.veh or self.tu_vehiculo(120)
        if v is None or v.muerto or v.tag or v.ardiendo >= 0 or v.modelo.get("barco") or v.modelo.get("vuela") or self.mundo.tipo == "mar" \
                or getattr(v, "con_chofer", False) or getattr(self, "en_servidor", False):
            return None
        return v

    def _plaza_al_lado(self, x, y):
        """Un hueco junto al bordillo cerca de ese punto, sin nada aparcado encima y sin tapar la puerta (ahí aparca el
        vehículo que dé la misión)."""
        px, py, _ = self.mundo.plaza_en(x, y)
        for dx, dy in ((13, 0), (-13, 0), (0, 13), (0, -13), (26, 0), (-26, 0), (0, 26), (0, -26), (39, 0), (-39, 0), (0, 39), (0, -39)):
            qx, qy, d = self.mundo.plaza_en(x + dx, y + dy)
            if math.hypot(qx - px, qy - py) >= 8 and all(o.muerto or o.dist(qx, qy) > 7 for o in self.vehiculos):
                return qx, qy, d
        return self.mundo.plaza_en(x + 13, y)

    def remolcar_barco(self, mapa=None, comprobar=True):
        """Tu barco se ha quedado en el mar sin ti: has saltado al agua y has llegado nadando a tierra, te han rescatado o
        has despertado en el hospital. No se pierde: lo remolcan hasta un amarre, en la localidad a la que llegas si tiene
        embarcadero. Solo se pierde si se ha hundido o ha ardido (con `comprobar`, se mira si sigue a flote). Devuelve la
        frase que lo cuenta, o cadena vacía si no ibas con tu barco."""
        j = self.j
        b = j.barco_actual
        if not b:
            return ""
        j.barco_actual = None
        v = next((o for o in self.vehiculos if o.modelo.get("barco") and getattr(o, "propio", False)), None)
        if comprobar and self.mundo.tipo == "mar" and (v is None or v.muerto):
            return tr('Tu barco, {nombre}, se ha hundido: lo has perdido.').format(nombre=(b.get("nombre") or tr("el tuyo")))
        emb = None
        if mapa in self.mapas:
            emb = next((l for l in self.mapas[mapa].lugares.values() if l.tipo == "embarcadero"), None)
        emb = emb or next((l for m in self.mapas.values() for l in m.lugares.values() if l.tipo == "embarcadero"), None)
        if emb is None:
            return ""
        salud = v.salud if v is not None and not v.muerto else b.get("salud", 100)
        j.barcos.append({"modelo": b["modelo"], "nombre": b.get("nombre"), "salud": salud, "en": emb.id})
        if v is not None and v is not j.veh:
            self.quitar_vehiculo(v)
        return tr('A tu barco, {nombre}, lo remolcan hasta un amarre de {nombre_lugar}: allí puedes volver a zarpar con él.').format(
            nombre=(b.get("nombre") or (v.nombre if v is not None else tr("el tuyo"))), nombre_lugar=(self.nombre_lugar(emb)))

    def preparar_traslado(self, mapa):
        """Antes de que el juego te lleve a otro sitio (y antes de rebobinar al jugador, que le quita el vehículo de las
        manos): qué vehículo va contigo, y tu barco, si ibas en él, a un amarre. Devuelve {"veh": vehículo o None}."""
        j = self.j
        u = j.veh
        if j.barco_actual and u is not None and u.modelo.get("barco"):      # ibas en tu barco: no se pierde, vuelve a puerto
            emb = next((l for l in self.mapas[mapa].lugares.values() if l.tipo == "embarcadero"), None) or \
                next((l for m in self.mapas.values() for l in m.lugares.values() if l.tipo == "embarcadero"), None)
            if emb is not None:
                j.barcos.append({"modelo": j.barco_actual["modelo"], "nombre": j.barco_actual.get("nombre"), "salud": u.salud, "en": emb.id})
                self.decir(tr('Tu barco, {nombre}, queda amarrado en {nombre_lugar}.').format(nombre=(u.nombre), nombre_lugar=(self.nombre_lugar(emb))))
            j.barco_actual = None
            self.salir_vehiculo(forzado=True)
            self.quitar_vehiculo(u)
            return {"veh": None}
        v = self.vehiculo_para_llevar()
        if v is not None and self.mapas[mapa].tipo == "mar":
            v = None
        if u is not None:
            self.salir_vehiculo(forzado=True)
            if u is not v and mapa != self.mundo.id and not self.es_mio(u):
                self.quitar_vehiculo(u)                          # el que no es tuyo y no puede venir desaparece, como siempre
        return {"veh": v}

    def llevarte_a(self, mapa, x, y, lleva=None):
        """El juego te devuelve a un sitio: al reintentar o repetir una misión, o al volver a un punto de control. Tu
        vehículo, el que llevabas o el que acababas de dejar al lado, va contigo y queda aparcado junto a ti, que es donde
        estaba cuando empezaste. Si no puede ir (uno de misión, un barco, algo que vuela), el tuyo se queda donde estaba y
        sale en Mis vehículos. Un barco tuyo vuelve a un amarre. `lleva` es lo que devolvió `preparar_traslado`, si hubo
        que llamarlo antes. Devuelve el vehículo que ha venido contigo, o None."""
        if lleva is None:
            lleva = self.preparar_traslado(mapa)
        v = lleva.get("veh")
        if v is not None and (v.muerto or v not in self.vehiculos):
            v = None
        if v is None:
            if mapa != self.mundo.id:
                self.cambiar_mapa(mapa, x, y)
            self.teletransportar(x, y)
            return None
        if mapa != self.mundo.id:                                # a otra localidad: viaja como datos y vuelve a la calle allí
            ficha = dict(self._veh_fuera_dict(v), n=int(getattr(v, "mio_n", 0)))
            mio = self.es_mio(v)
            self.quitar_vehiculo(v)
            self.ultimo_veh = None
            self.cambiar_mapa(mapa, x, y)
            px, py, d = self._plaza_al_lado(x, y)
            v = self._veh_de_dict(ficha, px, py)
            if mio:
                v.mio, v.mio_n = True, ficha["n"]
        else:
            px, py, d = self._plaza_al_lado(x, y)
            v.x, v.y = px, py
        v.dir, v.rumbo, v.vel, v.ia = d, d * 90.0, 0.0, None
        self.ultimo_veh = v
        self.teletransportar(x, y)
        self.decir(tr('{nombre} viene contigo: queda aparcado a tu lado, {direccion_txt}.').format(nombre=(v.nombre), direccion_txt=(self.direccion_txt(v.x, v.y))))
        return v

    def ficha_a_la_calle(self, ficha, casa=None):
        """Saca a la calle, a tu nombre, un vehículo guardado como ficha de garaje: delante de esa casa, o junto a ti.
        En otra localidad queda apuntado y allí estará cuando vuelvas."""
        self.mio_sec += 1
        mapa = casa.mapa if casa is not None else self.mundo.id
        x, y = (casa.x, casa.y) if casa is not None else self.pos()
        if mapa == self.mundo.id and self.mundo.tipo != "mar":
            px, py, d = self._plaza_al_lado(x, y)
            v = self._veh_de_dict(dict(ficha, rumbo=d * 90.0), px, py)
            v.mio, v.mio_n = True, self.mio_sec
            return v
        px, py, d = self.mapas[mapa].plaza_en(x, y)
        self.mis_lejos.append(dict(ficha, x=px, y=py, rumbo=d * 90.0, mapa=mapa, n=self.mio_sec, donde=self.mapas[mapa].describir(px, py)))
        return None

    def vehiculos_tras_reintento_txt(self):
        """Tras reintentar: dónde están tus vehículos, en una frase, para que no parezca que falta ninguno."""
        if getattr(self, "en_servidor", False):
            return ""
        calle = self.mis_en_calle() - (1 if self.es_mio(self.tu_vehiculo(60)) else 0)
        garaje = self.mis_en_garajes()
        if calle <= 0 and garaje <= 0:
            return ""
        partes = []
        if garaje:
            partes.append(tr('{garaje} en {v}').format(garaje=(garaje), v=(tr('tu garaje') if len([g for g in self.j.garajes.values() if g]) == 1 else tr('tus garajes'))))
        if calle > 0:
            partes.append(tr('{calle} en la calle').format(calle=(calle)))
        return tr("Tus vehículos siguen donde estaban: ") + tr(" y ").join(partes) + tr(". Los tienes en el móvil, en Mis vehículos.")

    def mas_vehiculos_txt(self, menos=None):
        """Lo que añade Mayúsculas L: cuántos vehículos más tienes y dónde mirarlos."""
        if getattr(self, "en_servidor", False):
            n = len(self.sv_mis_vehiculos()) - (1 if menos is not None else 0)
        else:
            n = self.mis_en_calle() - (1 if menos is not None and self.es_mio(menos) else 0) - (1 if self.es_mio(self.j.veh) else 0)
        n += self.mis_en_garajes()
        if n <= 0:
            return ""
        return tr(' Tienes {v}: {v2} en el móvil, en Mis vehículos.').format(v=(tr('otro vehículo') if n == 1 else tr('otros {n} vehículos').format(n=(n))), v2=(tr('está') if n == 1 else tr('están')))

    # ------------------------------------------------------------------ en un servidor
    def sv_mis_vehiculos(self):
        """Los vehículos de la calle que el servidor reconoce como tuyos: [(datos del servidor, vehículo de tu juego o None)]."""
        if not getattr(self, "en_servidor", False):
            return []
        mios = self.sv.setdefault("mios", set())
        fuera = []
        vistos = set()
        for v in self.vehiculos:
            ident = getattr(v, "id_red", None)
            if ident is None or v.muerto:
                continue
            if getattr(v, "red_mio", False) or getattr(v, "red_dueno", False) or ident in mios:
                vistos.add(ident)
                d = self.sv["vehs"].get(ident) or {"id": ident, "modelo": v.modelo["id"], "nombre": v.nombre, "m": self.mundo.id, "x": v.x, "y": v.y, "salud": v.salud}
                fuera.append((d, v))
        for ident in sorted(mios - vistos):
            d = self.sv["vehs"].get(ident)
            if d is not None and d.get("por") is None:
                fuera.append((d, None))
        return fuera

    # ------------------------------------------------------------------ nombre propio
    def renombrar_vehiculo(self, cosa, al_terminar=None):
        """Le pone nombre a un vehículo tuyo. «cosa» es un vehículo de la calle o la ficha de uno guardado."""
        app = self.app
        es_ficha = isinstance(cosa, dict)
        modelo = cosa["modelo"] if es_ficha else cosa.modelo["id"]
        actual = (cosa.get("nombre") if es_ficha else cosa.nombre) or _modelo_nombre(self, modelo)

        def hecho(t):
            t = " ".join(str(t).split())[:NOMBRE_MAX] or _modelo_nombre(self, modelo)
            if t != _modelo_nombre(self, modelo):
                registro.ocultar(t)                              # lo que escribes no se anota en el registro del juego
            if es_ficha:
                cosa["nombre"] = t
            else:
                cosa.nombre = t
                self.hacer_mio(cosa)
            app.son("menu_ok")
            app.decir(tr('Ahora se llama {t}.').format(t=(t)) if t != _modelo_nombre(self, modelo) else tr('Vuelve a llamarse {t}, como el modelo.').format(t=(t)), True)
            if al_terminar:
                al_terminar()
        app.abrir(EntradaTexto(app, tr('Nombre para {actual}').format(actual=(actual)), hecho, inicial="" if actual == _modelo_nombre(self, modelo) else actual, maximo=NOMBRE_MAX,
                               ayuda=tr('Hasta {NOMBRE_MAX} letras. El juego lo dirá al subir, al localizarlo y en las listas. Si lo dejas vacío, vuelve a llamarse como el modelo. Tabulador propone nombres al azar. Lo que escribas aquí no se anota en el registro del juego.').format(NOMBRE_MAX=(NOMBRE_MAX)), propuestas=nombres_propuestos()))

    # ------------------------------------------------------------------ que te lo traigan, o al garaje
    def traer_mi_vehiculo(self, cosa, garaje=None):
        """Tu mecánico te trae un vehículo tuyo: de la calle (de esta localidad o de otra) o de un garaje. Devuelve el vehículo."""
        if self.mundo.tipo == "mar":
            self.app.son("error")
            self.decir(tr("En mitad del mar no te pueden traer un vehículo."), True)
            return None
        if self.j.estrellas > AJUSTES["chofer_busqueda_max"]:
            self.app.son("error")
            self.decir(tr("Con tanta policía buscándote, tu mecánico no se acerca."), True)
            return None
        if isinstance(cosa, dict):
            if garaje is not None and cosa not in self.j.garajes.get(garaje, []):
                return None
            if garaje is None and cosa not in self.mis_lejos:
                return None
        elif cosa.muerto or cosa is self.j.veh:
            return None
        if not self.pagar(self.precio("traer_vehiculo", 150)):
            return None
        x, y, di = self.plaza_cercana()
        self._despejar_plaza(x, y)                               # que no quede encima de otro: la F cogería el de al lado
        if isinstance(cosa, dict):
            (self.j.garajes[garaje] if garaje is not None else self.mis_lejos).remove(cosa)
            v = self._veh_de_dict(dict(cosa, rumbo=di * 90.0), x, y)
            if garaje is None:
                v.mio, v.mio_n = True, int(cosa.get("n", 0) or 0)
            else:
                self.hacer_mio(v)
        else:
            v = cosa
            v.x, v.y, v.dir, v.rumbo, v.vel = x, y, di, di * 90.0, 0.0
        self.vehiculo_traido(v)
        self.son(v.modelo.get("claxon", "claxon"), xy=(x, y))
        self.decir(tr('Tu mecánico te deja {nombre} en la calle. {situar}.').format(nombre=(v.nombre), situar=(self.situar(x, y, tr('Está')))), True)
        self.gps_tras_traer(cosa, v)
        return v

    def gps_tras_traer(self, cosa, v):
        """Te han traído el vehículo al que te llevaba el GPS: ya no hay que ir a buscarlo. Si el destino era el propio
        vehículo, pasa a donde lo han dejado (y se acaba al subir); si era la casa de su garaje o su localidad, se quita."""
        g = self.gps
        if g is None:
            return
        if g.get("cosa") is v or g.get("sigue") is v:
            g["dest"], g["ruta"], g["clave"] = (v.x, v.y), [], None
            self._recalcular_gps()
        elif g.get("para") is not None and g.get("para") is cosa:
            if not self._volver_del_desvio(tr('Ya tienes {nombre} a tu lado.').format(nombre=(v.nombre))):
                self.gps = None
                self.decir(tr('Ya tienes {nombre} a tu lado. El GPS se queda sin destino.').format(nombre=(v.nombre)))

    def vehiculo_traido(self, v):
        """Tu mecánico te acaba de dejar este vehículo: es el tuyo de ahora. Mayúsculas L y Servicios lo encuentran, no
        desaparece al alejarte y, en un servidor, queda apuntado como tuyo en su calle (antes se perdía con su plaza de garaje)."""
        v.traido = True
        if self.j.veh is None:
            self.ultimo_veh = v
        if getattr(self, "en_servidor", False):
            self.sv_traido(v)

    def mandar_al_garaje(self, cosa, casa, cobrar=True):
        """Tu mecánico se lleva a un garaje tuyo un vehículo de la calle. True si se lo ha llevado."""
        g = self.j.garajes.setdefault(casa.id, [])
        if len(g) >= int(casa.get("garaje", 0)):
            self.app.son("error")
            self.decir(tr("Ese garaje está lleno."), True)
            return False
        es_ficha = isinstance(cosa, dict)
        if es_ficha and cosa not in self.mis_lejos:
            return False
        modelo = self.modelos.get(cosa.get("modelo")) if es_ficha else cosa.modelo
        if modelo is not None and modelo.get("vuela"):
            self.app.son("error")
            self.decir(tr("Una aeronave no cabe en el garaje de una casa: se guarda en un hangar, en un helipuerto, un aeropuerto o un aeródromo."), True)
            return False
        if not es_ficha and (cosa.muerto or cosa.tag or cosa.modelo.get("barco")):
            self.app.son("error")
            self.decir(self.motivo_ajeno(cosa) if not es_ficha and cosa.tag else tr("Ese vehículo no se puede guardar en un garaje."), True)
            return False
        if cobrar and not self.pagar(self.precio("mandar_vehiculo", 100)):
            return False
        if es_ficha:
            self.mis_lejos.remove(cosa)
            g.append({k: cosa[k] for k in ("modelo", "salud", "nombre", "mejoras", "litros", "km", "pinchada", "revision") if k in cosa})
            nombre = cosa.get("nombre") or _modelo_nombre(self, cosa["modelo"])
        else:
            g.append(self._ficha_garaje(cosa))
            nombre = cosa.nombre
            if self.chofer and self.chofer.get("veh") is cosa:
                self.despedir_chofer(callar=True)
            if self.j.veh is cosa:
                self.salir_vehiculo(forzado=True)
            if self.ultimo_veh is cosa:
                self.ultimo_veh = None
            self.quitar_vehiculo(cosa)
        self.son("arranque", vol=0.6)
        self.decir(tr('Tu mecánico se lleva {nombre} al garaje de {nombre_lugar}.').format(nombre=(nombre), nombre_lugar=(self.nombre_lugar(casa))) + (tr(" Te quedas a pie.") if not es_ficha and not self.j.veh else ""), True)
        return True

    def motivo_ajeno(self, v):
        """Por qué no se puede guardar, vender ni mejorar un vehículo que no puede ser tuyo."""
        if v.tag == "banda":
            return tr("Ese vehículo es de tu banda, y lo lleva tu chófer: no se puede guardar, vender ni mejorar.")
        if v.tag == "secuestro":
            return tr("Ese aparato es robado y está denunciado en toda la comarca: no te lo puedes quedar, ni guardarlo, venderlo o mejorarlo.")
        if v.tag in ("compania", "compania_devolver"):
            return tr("Ese aparato es de la compañía para la que vuelas: no te lo puedes quedar, ni guardarlo, venderlo o mejorarlo.")
        return tr("Ese vehículo es de una misión: no te lo puedes quedar, ni guardarlo, venderlo o mejorarlo.")

    # ------------------------------------------------------------------ misiones
    def mision_vehiculo(self, m):
        """Qué pasa con el vehículo en una misión: (None, None) si no lleva ninguno; si no, («da», «roba», «tuyo» o
        «trae», nombre del vehículo). «da»: te dejan uno. «roba»: hay que llevarse uno concreto. «tuyo»: te dejan uno,
        pero vale el tuyo. «trae»: tienes que venir con uno."""
        for q in m.get("pasos", []):
            if q.get("tipo") == "robar":
                nombre = q.get("nombre") or _modelo_nombre(self, q.get("modelo"))
                if m.get("vehiculo_libre"):
                    return "tuyo", nombre
                return ("da" if q.get("abierto") else "roba"), nombre
            if q.get("tipo") == "carrera":
                return "trae", None
            if q.get("tipo") == "perseguir":                      # hay que alcanzar a un vehículo: sin uno no hay nada que hacer
                return "persigue", q.get("nombre") or _modelo_nombre(self, q.get("modelo"))
        return None, None

    def mision_vehiculo_txt(self, m):
        """La frase que se añade al resumen de una misión, antes de aceptarla."""
        que, nombre = self.mision_vehiculo(m)
        if que == "da":
            return tr('Te dan vehículo: {nombre}. El tuyo se queda aparcado y a salvo.').format(nombre=(nombre))
        if que == "roba":
            return tr('Hay que llevarse un vehículo concreto: {nombre}. El tuyo se queda aparcado y a salvo.').format(nombre=(nombre))
        if que == "tuyo":
            return tr('Te dejan un vehículo, {nombre}, pero puedes hacerla con el tuyo: tú eliges.').format(nombre=(nombre))
        if que == "trae":
            return tr("Tienes que ir con un vehículo: vale el tuyo.")
        if que == "persigue":
            return tr("Hay una persecución en vehículo: ve con uno rápido, el que tú quieras.")
        return ""

    def vale_para_mision(self, v, paso):
        """¿Sirve tu vehículo para una misión que no exige el suyo? Tiene que ser de la misma clase: si el de la misión vuela, el tuyo también."""
        mo = self.modelos.get(paso.get("modelo")) or {}
        return (v is not None and not v.tag and not v.muerto and bool(v.modelo.get("vuela")) == bool(mo.get("vuela"))
                and bool(v.modelo.get("barco")) == bool(mo.get("barco")) and v.modelo.get("motor") != "motor_bici")

    def aviso_vehiculo_mision(self, m, paso):
        """Al empezar el paso en el que la misión te da vehículo: qué pasa con el tuyo. Si llevas uno, o lo acabas de dejar,
        queda a tu nombre para que no se pierda al coger el de la misión."""
        x, y = self.pos()
        v = self.j.veh or self.tu_vehiculo(150) or min((o for o in self.mis_vivos() if o.dist(x, y) < 150), key=lambda o: o.dist(x, y), default=None)
        if m.get("vehiculo_libre") and v is not None and not v.tag and self.vale_para_mision(v, paso):
            self.decir(tr('Esta misión se puede hacer con tu vehículo: tú eliges. {v} {nombre} y detente junto al que te dejan, o coge el que te dejan. También vale otro de los tuyos: pídelo en el móvil, en Mis vehículos.').format(v=(tr('Sigue en') if self.j.veh is v else tr('Sube a')), nombre=(v.nombre)))
            return
        if m.get("vehiculo_libre") and not getattr(self, "en_servidor", False) and (self.mis_vivos() or self.mis_en_garajes()):
            self.decir(tr("Esta misión se puede hacer con el vehículo que te dejan o con uno de los tuyos: tú eliges. Para ir con uno tuyo, pídelo en el móvil, en Mis vehículos, y detente con él junto al que te dejan."))
        if v is None or v.tag:
            return
        if getattr(self, "en_servidor", False):
            return
        if self.hacer_mio(v, callar=True):
            self.decir(tr('{nombre} se queda aparcado y a salvo: lo tienes en el móvil, en Mis vehículos, y desde ahí lo puedes mandar al garaje.').format(nombre=(v.nombre)))

    # ------------------------------------------------------------------ chófer de la banda
    def chofer_conduce(self):
        c = getattr(self, "chofer", None)
        return bool(c and c["estado"] == "contigo" and self.j.veh is c.get("veh"))

    def chofer_nombre(self):
        return self.chofer["nombre"] if self.chofer else ""

    def _chofer_dice(self, cual, despues=""):
        c = self.chofer
        self.decir(f"{c['nombre']}: {random.choice(LISTAS[cual])}" + (" " + despues if despues else ""))

    def chofer_modelos(self):
        """Los vehículos de la banda con los que puede venir tu chófer, los que digan los datos."""
        return [x for x in LISTAS["chofer_modelos"] if x in self.modelos and not self.modelos[x].get("barco") and not self.modelos[x].get("vuela")] or ["utilitario"]

    def pedir_chofer(self, garaje=None, ficha=None, modelo=None):
        """Pides que alguien de la banda venga a recogerte: con un vehículo de tu garaje (garaje y ficha) o con uno de la
        banda, el que elijas (modelo) o el que tengan a mano."""
        from . import gente
        j = self.j
        motivo = ""
        if not j.banda:
            motivo = tr("Para tener chófer necesitas a alguien reclutado en tu banda. Se recluta en el móvil, en Territorios, Tu banda.")
        elif self.chofer:
            motivo = tr('{nombre} ya está en ello. Si quieres otro, despídelo antes.').format(nombre=(self.chofer['nombre']))
        elif self.mundo.tipo == "mar":
            motivo = tr("En mitad del mar no puede venir nadie a recogerte.")
        elif j.estrellas > AJUSTES["chofer_busqueda_max"]:
            motivo = tr("Con tanta policía buscándote, nadie de la banda se acerca. Despístalos antes.")
        elif getattr(self, "pasajero", None) is not None:
            motivo = tr("Ya vas de pasajero con otro jugador.")
        elif ficha is not None and ficha not in j.garajes.get(garaje, []):
            motivo = tr("Ese vehículo ya no está en el garaje.")
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        if not self.pagar(self.precio("chofer", 80)):
            return False
        a, b = sorted((AJUSTES["chofer_espera_min"], AJUSTES["chofer_espera_max"]))
        espera = random.uniform(a, b) * (1.25 if self.lluvia else 1.0) * (0.85 if self.es_noche() else 1.0)      # con lluvia tarda más; de noche hay menos tráfico
        modelos = self.chofer_modelos()
        genero = random.choice("hm")
        self.chofer = {"estado": "espera", "t": espera, "garaje": garaje, "ficha": ficha, "modelo": modelo if modelo in modelos else random.choice(modelos), "veh": None, "propio": False,
                       "nombre": tr('{choice}, de {v}').format(choice=(random.choice(gente.nombres(genero))), v=(j.banda_nombre or tr('tu banda'))), "intentos": 0, "sin_destino": 0.0}
        cuanto = tr("menos de un minuto") if espera < 45 else tr("cosa de un minuto") if espera < 80 else tr("un par de minutos")
        self.son("movil", cat="interfaz", vol=0.5)
        self._chofer_dice("chofer_frases_sale", tr('Tardará {cuanto}. Cuando llegue, oirás el claxon.').format(cuanto=(cuanto)))
        return True

    def _chofer_sale(self):
        """Se acabó la espera: el vehículo aparece a un par de manzanas y viene hacia ti por la calle."""
        c = self.chofer
        x, y = self.pos()
        pos = self._punto_llegada(x, y)
        if pos is None:
            c["intentos"] += 1
            c["t"] = 6.0
            if c["intentos"] >= 5:
                self.chofer = None
                self.j.dinero += self.precio("chofer", 80)
                self.decir(tr("Tu chófer no encuentra cómo llegar hasta aquí. Te devuelven el dinero."))
            return
        ficha = c["ficha"]
        if ficha is not None and ficha in self.j.garajes.get(c["garaje"], []):
            self.j.garajes[c["garaje"]].remove(ficha)
            v = self._veh_de_dict(dict(ficha, rumbo=pos[2] * 90.0), pos[0], pos[1])
            v.dir = pos[2]
            c["propio"] = True
            self.hacer_mio(v, callar=True)
        else:
            if ficha is not None:
                self.decir(tr('{nombre} no ha encontrado ese vehículo en el garaje: viene con uno de la banda.').format(nombre=(c['nombre'])))
            v = self.crear_vehiculo(c["modelo"], pos[0], pos[1], pos[2], None, tr('{_modelo_nombre} de {v}').format(_modelo_nombre=(_modelo_nombre(self, c['modelo'])), v=(self.j.banda_nombre or tr('tu banda'))), "banda")
            v.propio = True
        v.ia, v.ocupado, v.vel, v.con_chofer = "chofer", True, 9.0, True
        c.update(estado="viene", veh=v, t_limite=self.t + 75.0)
        self.decir(tr('{nombre} ya viene con {nombre2}. {situar}.').format(nombre=(c['nombre']), nombre2=(v.nombre), situar=(self.situar(v.x, v.y, tr('Está')))))

    def _ia_chofer(self, v, d, dt):
        """El chófer viene a por ti como cualquiera que conoce la ciudad: sin correr, y parando a tu lado."""
        j = self.j
        vel_j = abs(j.veh.vel) if j.veh else 0.0
        if d < 15 and vel_j < 4:
            if v.vel < 1.0:
                self._chofer_llega(v)
            return 0.0, self._decidir_policia
        px, py = self.pos()
        dx, dy = M.DIRS[v.dir]
        a = (px - v.x) * dx + (py - v.y) * dy
        lat = abs((px - v.x) * dy - (py - v.y) * dx)
        if a < -15 and lat < 20 and self.t > v.t_giro:           # te ha pasado de largo: da la vuelta
            v.t_giro = self.t + 3
            v.dir = (v.dir + 2) % 4
        lim = min(v.modelo["vel_max"] * 0.6, 14.0)
        if d < 40:
            lim = min(lim, max(4.0, d * 0.3))
        return lim, self._decidir_policia

    def _chofer_llega(self, v):
        c = self.chofer
        v.ia, v.ocupado, v.vel = None, False, 0.0
        if v.canal:
            v.canal.parar()
            v.canal = None
        c["estado"] = "aqui"
        claxon = v.modelo.get("claxon", "claxon")
        self.son(claxon, xy=(v.x, v.y), ref=8, maxd=120)
        self.son(claxon, xy=(v.x, v.y), ref=8, maxd=120, tono=1.04, vol=0.8)
        if v.sirena is None:
            v.sirena = self.son("loc_vehiculo", bucle=True, xy=(v.x, v.y), ref=5, maxd=70)      # se le oye, para encontrarlo
        self._chofer_dice("chofer_frases_llega", tr('{situar}. Sube con F.').format(situar=(self.situar(v.x, v.y, v.nombre))))

    def chofer_al_subir(self, v):
        """Te subes al vehículo que trae el chófer: vas de pasajero. Se llama desde _subir, antes de preparar la conducción."""
        c = self.chofer
        if c and c.get("veh") is v and c["estado"] in ("aqui", "viene"):
            c["estado"] = "contigo"
            c["sin_destino"] = 0.0
            c["tenia_gps"] = None
            return True
        return False

    def chofer_texto_subir(self, v):
        c = self.chofer
        return (tr('Subes a {nombre} de pasajero: conduce {nombre2}. Marca un destino con la L y te lleva. Con Q fijas y con Control disparas. Con F te bajas, y te espera. Para despedirlo, el móvil, en Servicios.').format(nombre=(v.nombre), nombre2=(c['nombre'])))

    def chofer_tecla(self, k):
        """Las teclas de conducir, cuando conduce el chófer. True si la tecla era de esas."""
        import pygame
        if not self.chofer_conduce() or k not in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_u, pygame.K_y, pygame.K_j, pygame.K_e):
            return False
        self.decir(tr('Conduce {nombre}: tú vas de pasajero. ').format(nombre=(self.chofer['nombre'])) + (tr('Vais a {nombre}.').format(nombre=(self.gps['nombre'])) if self.gps else tr("Marca un destino con la L.")), True)
        return True

    def actualizar_chofer(self, dt):
        c = getattr(self, "chofer", None)
        if not c:
            return
        v = c.get("veh")
        if c["estado"] == "espera":
            c["t"] -= dt
            if c["t"] <= 0:
                if not self.j.banda:
                    self.chofer = None
                    self.decir(tr("Ya no queda nadie en tu banda para venir a recogerte."))
                else:
                    self._chofer_sale()
            return
        if v is None or v.muerto or v not in self.vehiculos:
            self.chofer = None
            self.son("notificacion", cat="interfaz", vol=0.5)
            self.decir(tr('Te has quedado sin chófer: {v} y el vehículo ya no están.').format(v=(c['nombre'].split(',')[0])))
            return
        if c["estado"] == "viene":
            if self.t > c["t_limite"]:                           # se ha liado con el tráfico: aparece en la calle más cercana
                x, y, di = self.plaza_cercana()
                v.x, v.y, v.dir, v.rumbo, v.vel = x, y, di, di * 90.0, 0.0
                self._chofer_llega(v)
        elif c["estado"] == "contigo":
            if self.j.veh is not v:
                c["estado"] = "aqui"
                if v.sirena is None:
                    v.sirena = self.son("loc_vehiculo", bucle=True, xy=(v.x, v.y), ref=5, maxd=70)
                self._chofer_dice("chofer_frases_espera")
                return
            dest = self.gps["dest"] if self.gps else None
            antes = c.get("tenia_gps")
            if dest != antes:
                c["tenia_gps"] = dest
                c["sin_destino"] = 0.0
                if dest is not None:
                    self._chofer_dice("chofer_frases_marcha")
                elif antes is not None and math.hypot(antes[0] - v.x, antes[1] - v.y) < 45:      # el GPS se ha apagado porque habéis llegado
                    self._chofer_dice("chofer_frases_llegada", tr("Con F te bajas, y te espera."))
                    c["sin_destino"] = 45.0
            if dest is None:
                c["sin_destino"] -= dt
                if c["sin_destino"] <= 0:
                    c["sin_destino"] = 40.0
                    self._chofer_dice("chofer_frases_destino", tr("La L abre la lista de lugares."))

    def despedir_chofer(self, callar=False):
        """Despides al chófer en cualquier momento. Si el vehículo es tuyo, se queda contigo; si es de la banda, se lo lleva."""
        c = getattr(self, "chofer", None)
        if not c:
            if not callar:
                self.decir(tr("No tienes chófer ahora mismo."), True)
            return False
        self.chofer = None
        v = c.get("veh")
        frase = f"{c['nombre']}: {random.choice(LISTAS['chofer_frases_adios'])} "
        if c["estado"] == "espera" or v is None or v.muerto:
            if not callar:
                self.decir(frase + tr("Se da la vuelta antes de llegar."), True)
            return True
        v.con_chofer = False
        dentro = self.j.veh is v
        if v.sirena is not None:
            v.sirena.parar()
            v.sirena = None
        if c.get("propio"):
            if not dentro:
                v.ia, v.ocupado, v.vel = None, False, 0.0
                if v.canal:
                    v.canal.parar()
                    v.canal = None
            if not callar:
                self.son("puerta_coche", xy=(v.x, v.y))
                self.decir(frase + (tr('Se baja y te deja {nombre}: ahora conduces tú.').format(nombre=(v.nombre)) if dentro else tr('{nombre} se queda aparcado. {situar}.').format(nombre=(v.nombre), situar=(self.situar(v.x, v.y, tr('Está'))))), True)
            return True
        if dentro:
            self.salir_vehiculo(forzado=True)
        x, y = v.x, v.y
        if self.ultimo_veh is v:
            self.ultimo_veh = None
        self.quitar_vehiculo(v)
        if not callar:
            self.son("arranque", xy=(x, y), vol=0.6)
            self.decir(frase + (tr("Te deja en la acera y se lleva el vehículo. Te quedas a pie.") if dentro else tr("Se lleva el vehículo.")), True)
        return True

    def chofer_al_cambiar_mapa(self):
        """Cambias de localidad: si vas con él, sigue contigo; si no, se vuelve."""
        c = getattr(self, "chofer", None)
        if not c or c["estado"] == "espera" or self.chofer_conduce():
            return
        self.chofer = None
        v = c.get("veh")
        if v is not None:
            v.con_chofer = False
        self.decir(tr('{v} no te sigue a otra localidad').format(v=(c['nombre'].split(',')[0])) + (tr(': deja {nombre} aparcado donde estaba.').format(nombre=(v.nombre)) if c.get("propio") and v is not None else tr(" y se vuelve con los demás.")))


# ====================================================================== menús
def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


def _estado_txt(salud, salud_max):
    return tr('estado {int} por ciento').format(int=(int(100 * max(0.0, float(salud)) / max(1.0, float(salud_max)))))


def _salud_max(p, modelo_id, mejoras):
    from . import sistemas

    class _V:
        pass
    v = _V()
    v.mejoras = {k: n for k, n in dict(mejoras or {}).items() if k in sistemas.MEJORAS}
    mo = p.modelos.get(modelo_id) or {"salud": 100}
    return float(mo["salud"]) * sistemas.factor_blindaje(v)


def lista_mis_vehiculos(p):
    """Todos tus vehículos, como fichas para el menú: [{"texto", "tipo", ...}]. Tipos: llevas, calle, lejos, garaje, ultimo, servidor."""
    j = p.j
    fichas = []

    def ficha_v(v, tipo, donde, **kw):
        fichas.append(dict(kw, tipo=tipo, veh=v, nombre=v.nombre,
                           texto=f"{nombre_completo(p, v.nombre, v.modelo['id'])}. {donde}. {_estado_txt(v.salud, v.salud_max).capitalize()}. {_mejoras_txt(getattr(v, 'mejoras', {}))}"))

    def ficha_d(d, tipo, donde, **kw):
        nombre = d.get("nombre") or _modelo_nombre(p, d["modelo"])
        smax = _salud_max(p, d["modelo"], d.get("mejoras"))
        fichas.append(dict(kw, tipo=tipo, datos=d, nombre=nombre,
                           texto=f"{nombre_completo(p, nombre, d['modelo'])}. {donde}. {_estado_txt(d.get('salud', smax), smax).capitalize()}. {_mejoras_txt(d.get('mejoras'))}"))

    def en_calle(v):
        return tr('En la calle: {describir}, {v}').format(describir=(p.mundo.describir(v.x, v.y)), v=(p.situar(v.x, v.y, 'está').split(', ', 1)[-1]))

    if getattr(p, "en_servidor", False):
        for d, v in p.sv_mis_vehiculos():
            if v is not None and v is j.veh:
                ficha_v(v, "llevas", tr("Vas en él"))
            elif v is not None:
                ficha_v(v, "servidor", en_calle(v))
            elif d.get("modelo") in p.modelos:
                mapa = p.mapas.get(d.get("m"))
                ficha_d(d, "servidor", tr('En la calle, en {v}').format(v=(mapa.nombre if mapa else tr('otra localidad'))))
    else:
        v = j.veh
        if v is not None and not v.tag and not v.modelo.get("barco"):
            ficha_v(v, "llevas", tr("Vas en él") + ("" if p.es_mio(v) else tr(", pero todavía no está a tu nombre")))
        for o in p.mis_vivos():
            if o is not v:
                ficha_v(o, "calle", en_calle(o))
        for d in sorted(p.mis_lejos, key=lambda d: int(d.get("n", 0) or 0)):
            if d.get("modelo") in p.modelos:
                mapa = p.mapas.get(d.get("mapa"))
                ficha_d(d, "lejos", tr('En la calle, en {v}: {v2}').format(v=(mapa.nombre if mapa else tr('otra localidad')), v2=(d.get('donde') or tr('donde lo dejaste'))))
        u = p.tu_vehiculo()
        if u is not None and not p.es_mio(u):
            ficha_v(u, "ultimo", en_calle(u) + tr(". Es el último que has usado y no está a tu nombre: si coges otro, se pierde"))
    for pid, lista in j.garajes.items():
        l = p.lug(pid)
        for d in lista:
            if d.get("modelo") in p.modelos:
                ficha_d(d, "garaje", tr('En el garaje de {v}').format(v=(p.nombre_lugar(l) if l else tr('una casa'))), garaje=pid)
    for l, h, d in p.hangares_naves():                            # las aeronaves guardadas en tus hangares (vuelo.py)
        if d.get("modelo") in p.modelos:
            ficha_d(d, "hangar", tr('En el hangar de {nombre_lugar}').format(nombre_lugar=(p.nombre_lugar(l))) + (tr('. Combustible, {int} por ciento').format(int=(int(float(d.get('queroseno', 100))))) if p.vuelo_con_combustible() else ""), hangar=l.id)
    return fichas


def menu_mis_vehiculos(p):
    """Móvil, Mis vehículos: todos, dónde está cada uno y qué se puede hacer con él."""
    app, j = p.app, p.j
    servidor = getattr(p, "en_servidor", False)

    def casas():
        return [l for l in (p.lug(pid) for pid in j.propiedades) if l is not None and int(l.get("garaje", 0)) > 0 and not p.alquilada(l.id)]

    def acciones(f):
        def abrir():
            v, d, tipo = f.get("veh"), f.get("datos"), f["tipo"]
            cosa = v if v is not None else d

            def gps():
                _volver_al_juego(p)
                # Como Mayúsculas L: el destino es el vehículo, no el sitio. Si te lo traen, el GPS va adonde lo dejan, y al
                # subir se acaba; antes se quedaba en el sitio de antes y el piloto del GPS te llevaba allí con él.
                p.fijar_gps(v.x, v.y, v.nombre, desvio=True, cosa=v)
                antes = (p.gps or {}).get("anterior")
                p.decir(tr('{situar}. {describir}. Marcado en el GPS.').format(situar=(p.situar(v.x, v.y, v.nombre)), describir=(p.mundo.describir(v.x, v.y)))
                        + (tr(' Al llegar, el GPS vuelve a {nombre}.').format(nombre=(antes['nombre'])) if antes is not None else ""), True)

            def gps_casa():
                l = p.lug(f["garaje"])
                if l is not None:
                    _volver_al_juego(p)
                    p.gps_a_lugar(l)
                    if p.gps is not None:
                        p.gps["para"] = cosa                     # se va a por este vehículo: si te lo traen, sobra

            def gps_lejos():
                mapa = p.mapas.get(d.get("mapa"))
                if mapa is None or not mapa.lugares:
                    return
                l = min(mapa.lugares.values(), key=lambda q: math.hypot(q.x - float(d.get("x", 0)), q.y - float(d.get("y", 0))))
                _volver_al_juego(p)
                p.gps_a_lugar(l)                                 # el GPS dice cómo se llega a esa localidad; allí, Mayúsculas L o esta lista
                if p.gps is not None:
                    p.gps["para"] = cosa

            def traer():
                if p.traer_mi_vehiculo(cosa, f.get("garaje")) is not None:
                    _volver_al_juego(p)

            AY_GARAJE = tr("Pagas y tu mecánico lo deja en el garaje de esta casa, donde queda a salvo. Si está lleno, no se puede.")
            AY_SIN_GARAJE = tr("Los garajes vienen con algunas casas. Compra una que lo tenga y podrás guardar allí tus vehículos.")

            def al_garaje():
                def llevar(l):
                    def g():
                        if p.mandar_al_garaje(cosa, l):
                            _volver_al_juego(p)
                    return g
                ops = [Opcion(tr('{nombre_lugar}: {len} de {get} plazas ocupadas').format(nombre_lugar=(p.nombre_lugar(l)), len=(len(j.garajes.get(l.id, []))), get=(l.get('garaje', 0))), llevar(l), ayuda=AY_GARAJE) for l in casas()]
                app.abrir(Menu(app, tr('Mandar {nombre} a un garaje: {precio} euros').format(nombre=(f['nombre']), precio=(p.precio('mandar_vehiculo', 100))), ops or [Opcion(tr("No tienes ninguna casa con garaje"), ayuda=AY_SIN_GARAJE)]))

            def renombrar():
                p.renombrar_vehiculo(cosa, lambda: (app.cerrar(mm), m.refrescar(False)))

            def quedar():
                if p.hacer_mio(v):
                    app.son("menu_ok")
                    app.decir(tr('{nombre} queda a tu nombre: ya no se pierde aunque cojas otro.').format(nombre=(v.nombre)), True)
                    app.cerrar(mm)
                    m.refrescar(False)

            def chofer():
                if p.pedir_chofer(f["garaje"], d):
                    _volver_al_juego(p)

            # En un servidor, un vehículo tuyo aparcado en la calle lo guarda el servidor: estas tres cosas se le piden a él.
            def sv_datos():
                if d is not None:
                    return d
                return p.sv["vehs"].get(v.id_red) or {"id": v.id_red, "modelo": v.modelo["id"], "nombre": v.nombre, "salud": v.salud, "mejoras": dict(getattr(v, "mejoras", {}) or {})}

            def sv_traer():
                if p.mundo.tipo == "mar":
                    app.son("error")
                    return p.decir(tr("En mitad del mar no te pueden traer un vehículo."), True)
                if j.estrellas > AJUSTES["chofer_busqueda_max"]:
                    app.son("error")
                    return p.decir(tr("Con tanta policía buscándote, tu mecánico no se acerca."), True)
                precio = p.precio("traer_vehiculo", 150)
                if j.dinero < precio:
                    app.son("error")
                    return p.decir(tr('No tienes suficiente dinero. Cuesta {precio} euros y tienes {dinero}.').format(precio=(precio), dinero=(j.dinero)), True)
                x, y, di = p.plaza_cercana()
                dd = sv_datos()
                if p.sv_veh_orden("traer", dd, x=round(x, 1), y=round(y, 1), r=di * 90):
                    p.sv["veh_pend"][dd["id"]] = {"precio": precio}
                    _volver_al_juego(p)

            def sv_al_garaje():
                dd = sv_datos()
                precio = p.precio("mandar_vehiculo", 100)

                def llevar(l):
                    def g():
                        if len(j.garajes.get(l.id, [])) >= int(l.get("garaje", 0)):
                            app.son("error")
                            return p.decir(tr("Ese garaje está lleno."), True)
                        if j.dinero < precio:
                            app.son("error")
                            return p.decir(tr('No tienes suficiente dinero. Cuesta {precio} euros y tienes {dinero}.').format(precio=(precio), dinero=(j.dinero)), True)
                        if p.sv_veh_orden("guardar", dd, ref=l.id):
                            p.sv["veh_pend"][dd["id"]] = {"precio": precio, "casa": l.id}
                            _volver_al_juego(p)
                    return g
                if (p.modelos.get(dd.get("modelo")) or {}).get("barco"):
                    app.son("error")
                    return p.decir(tr("Ese vehículo no se puede guardar en un garaje."), True)
                lista = [Opcion(tr('{nombre_lugar}: {len} de {get} plazas ocupadas').format(nombre_lugar=(p.nombre_lugar(l)), len=(len(j.garajes.get(l.id, []))), get=(l.get('garaje', 0))), llevar(l), ayuda=AY_GARAJE) for l in casas()]
                app.abrir(Menu(app, tr('Mandar {nombre} a un garaje: {precio} euros').format(nombre=(f['nombre']), precio=(precio)), lista or [Opcion(tr("No tienes ninguna casa con garaje"), ayuda=AY_SIN_GARAJE)]))

            def sv_renombrar():
                dd = sv_datos()

                def hecho(t):
                    t = " ".join(str(t).split())[:NOMBRE_MAX] or _modelo_nombre(p, dd["modelo"])
                    if t != _modelo_nombre(p, dd["modelo"]):
                        registro.ocultar(t)
                    if p.sv_veh_orden("nombre", dd, nombre=t):
                        app.cerrar(mm)
                        m.refrescar(False)
                app.abrir(EntradaTexto(app, tr('Nombre para {nombre}').format(nombre=(f['nombre'])), hecho, inicial="" if f["nombre"] == _modelo_nombre(p, dd["modelo"]) else f["nombre"], maximo=NOMBRE_MAX,
                                       ayuda=tr('Hasta {NOMBRE_MAX} letras. Lo guarda el servidor y lo ven también los demás jugadores. Si lo dejas vacío, vuelve a llamarse como el modelo. Tabulador propone nombres al azar.').format(NOMBRE_MAX=(NOMBRE_MAX)), propuestas=nombres_propuestos()))
            ops = []
            modelo = p.modelos.get(d["modelo"]) if d is not None else v.modelo
            aerea = bool(modelo and modelo.get("vuela"))         # una aeronave: no se trae ni va a un garaje; va a un hangar

            def al_hangar():
                def llevar(l):
                    def g():
                        if p.mandar_al_hangar(cosa, l):
                            _volver_al_juego(p)
                    return g
                lista = [Opcion(tr('{nombre_lugar}: {len} de {int} plazas ocupadas').format(nombre_lugar=(p.nombre_lugar(l)), len=(len(p.hangar(l)['naves'])), int=(int(p.hangar_plazas()))), llevar(l),
                                ayuda=tr("Pagas y un piloto de la casa la deja en este hangar, donde queda a salvo. Allí la sacas a la pista cuando quieras."))
                         for l in p.hangar_destinos(cosa)]
                app.abrir(Menu(app, tr('Mandar {nombre} a un hangar: {precio} euros').format(nombre=(f['nombre']), precio=(p.precio('mandar_hangar', 250))),
                               lista or [Opcion(tr("No tienes plaza de hangar donde quepa. Se alquilan y se compran en los helipuertos, los aeropuertos y los aeródromos"),
                                                ayuda=tr("En el hangar de uno de esos campos contratas la plaza. Luego podrás mandarla allí desde aquí."))]))

            def gps_hangar():
                l = p.lug(f["hangar"])
                if l is not None:
                    _volver_al_juego(p)
                    p.gps_a_lugar(l)

            def queroseno():
                if p.vuelo_traer_queroseno(v):
                    app.cerrar(mm)
                    m.refrescar(False)
            if tipo == "hangar":
                ops.append(Opcion(tr("Marcar en el GPS el campo donde está"), gps_hangar, ayuda=tr("El GPS te lleva hasta el helipuerto, el aeropuerto o el aeródromo. Allí, en el hangar, la sacas a la pista.")))
            if aerea and tipo in ("calle", "lejos", "ultimo", "llevas") and not servidor:
                ops.append(Opcion(tr('Mandarla a un hangar: {precio} euros').format(precio=(p.precio('mandar_hangar', 250))), al_hangar,
                                  ayuda=tr("Un piloto de la casa se la lleva a una plaza de hangar tuya, esté donde esté la aeronave. Una aeronave no se trae a la puerta: se va a buscar al campo.")))
            if aerea and v is not None and tipo in ("calle", "ultimo", "llevas") and not servidor and p.vuelo_con_combustible() and float(getattr(v, "queroseno", 100.0)) < 50:
                ops.append(Opcion(tr('Que le traigan combustible: {precio} euros').format(precio=(p.precio('queroseno_domicilio', 450))), queroseno,
                                  ayuda=tr("Un camión cisterna llega hasta la aeronave y le echa medio depósito, para que puedas despegar y repostar en un campo.")))
            if tipo in ("calle", "ultimo") or (tipo == "servidor" and v is not None):
                ops.append(Opcion(tr("Marcarlo en el GPS"), gps, ayuda=tr("El GPS te lleva hasta él. Sin abrir el móvil, Mayúsculas L hace lo mismo con el último que has usado.")))
            if tipo == "garaje":
                ops.append(Opcion(tr("Marcar en el GPS la casa donde está"), gps_casa,
                                  ayuda=tr("El GPS te lleva hasta la casa de ese garaje. Allí lo sacas y te lo llevas.")))
            if tipo == "lejos":
                ops.append(Opcion(tr("Marcar en el GPS el camino hasta su localidad"), gps_lejos,
                                  ayuda=tr("El GPS te guía hasta el sitio más cercano a donde lo dejaste. Cuando estés en esa localidad, márcalo otra vez desde esta lista y te lleva hasta el vehículo.")))
            if tipo in ("calle", "lejos", "garaje") and not aerea:
                ops.append(Opcion(tr('Pedir que te lo traigan: {precio} euros').format(precio=(p.precio('traer_vehiculo', 150))), traer,
                                  ayuda=tr("Tu mecánico lo deja aparcado en la calle, a tu lado, esté donde esté. No viene si te busca mucho la policía.")))
            if tipo == "garaje" and j.banda and not servidor:
                ops.append(Opcion(tr('Que venga un chófer de tu banda con él: {precio} euros').format(precio=(p.precio('chofer', 80))), chofer,
                                  ayuda=tr("Alguien de tu banda lo saca del garaje, viene a recogerte y conduce él hasta donde marques en el GPS.")))
            if tipo in ("calle", "lejos", "ultimo", "llevas") and not servidor and not aerea:
                ops.append(Opcion(tr('Mandarlo a un garaje: {precio} euros').format(precio=(p.precio('mandar_vehiculo', 100))), al_garaje,
                                  ayuda=tr("Tu mecánico se lo lleva al garaje de la casa que elijas, esté donde esté el vehículo.")))
            if tipo == "ultimo" or (tipo == "llevas" and not servidor and not p.es_mio(v)):
                ops.append(Opcion(tr("Ponerlo a tu nombre"), quedar, ayuda=tr("Desde ese momento es tuyo: no desaparece al alejarte ni al coger otro, y se guarda con la partida.")))
            if not servidor or tipo in ("llevas", "garaje", "hangar"):
                ops.append(Opcion(tr("Cambiarle el nombre"), renombrar, ayuda=tr("El juego dirá ese nombre al subir, al localizarlo y en las listas.")))
            if tipo == "servidor":
                viejo = "" if p.sv_sabe("mis_vehiculos") else tr(" Este servidor va con una versión anterior y todavía no sabe hacerlo: al pulsar, el juego te dice qué puedes hacer en su lugar.")
                ops += [Opcion(tr('Pedir que te lo traigan: {precio} euros').format(precio=(p.precio('traer_vehiculo', 150))), sv_traer,
                               ayuda=tr("Tu mecánico lo deja aparcado en la calle, a tu lado, esté donde esté, también si está en otra localidad. No viene si te busca mucho la policía.") + viejo),
                        Opcion(tr('Mandarlo a un garaje: {precio} euros').format(precio=(p.precio('mandar_vehiculo', 100))), sv_al_garaje,
                               ayuda=tr("Tu mecánico se lo lleva al garaje de la casa que elijas, y deja de estar en la calle del servidor: ya no caduca ni se lo puede llevar nadie.") + viejo),
                        Opcion(tr("Cambiarle el nombre"), sv_renombrar, ayuda=tr("El nombre lo guarda el servidor, y lo ven también los demás jugadores.") + viejo)]
            ops.append(Opcion(f["texto"], ayuda=tr("Su nombre, dónde está, cómo está de daños y las mejoras que lleva.")))
            mm = Menu(app, f["nombre"], ops)
            app.abrir(mm)
        return abrir

    def seguro():
        p.seguro_contratar(int(getattr(j, "seguro_desde", 0) or 0) <= 0)
        m.refrescar(False)

    def ops():
        fichas = lista_mis_vehiculos(p)
        lista = [Opcion(f["texto"], acciones(f), ayuda=tr("Intro abre lo que puedes hacer con él: marcarlo en el GPS, que te lo traigan, mandarlo a un garaje o cambiarle el nombre.")) for f in fichas]
        if not lista:
            lista.append(Opcion(tr("No tienes ningún vehículo. Son tuyos los que compras, los que mejoras en un taller, los que sacas de un garaje y los que bautizas con un nombre"),
                                ayuda=tr("Cuando tengas alguno, aparece aquí y lo puedes marcar en el GPS, pedir que te lo traigan o mandarlo a un garaje.")))
        if not servidor:
            lista.append(Opcion(p.seguro_txt(), seguro, ayuda=(
                tr('Intro lo contrata o lo da de baja. Cubre a todos tus vehículos de tierra desde el día siguiente a contratarlo, no a las aeronaves. Cada medianoche cobra {seguro_cuota} euros por cada vehículo tuyo en la calle, del bolsillo o del banco; los del garaje no pagan. Si uno explota, al día siguiente te lo devuelven reparado y con sus mejoras, en un garaje tuyo con sitio o a la puerta de un taller, pagando una franquicia: el {seguro_franquicia_pct} por ciento de lo que cuesta el modelo, y como poco {seguro_franquicia_min} euros.').format(seguro_cuota=(AJUSTES['seguro_cuota']), seguro_franquicia_pct=(AJUSTES['seguro_franquicia_pct']), seguro_franquicia_min=(AJUSTES['seguro_franquicia_min'])))))
        if servidor:
            lista.append(Opcion(tr("En un servidor, los vehículos de la calle los guarda el servidor"),
                                ayuda=tr("El servidor recuerda los últimos vehículos que has dejado en la calle, hasta el máximo por jugador que tenga puesto, y durante las horas que tenga puestas. "
                                      "Otro jugador puede llevárselos. Lo que quieras conservar, mételo en un garaje.")))
        return lista

    def titulo():
        if servidor:
            return tr('Mis vehículos: {len} en la calle del servidor y {mis_en_garajes} en garajes').format(len=(len(p.sv_mis_vehiculos())), mis_en_garajes=(p.mis_en_garajes()))
        naves = len(p.hangares_naves())
        return tr('Mis vehículos: {mis_en_calle} en la calle, de {tope}, y {mis_en_garajes} en garajes').format(mis_en_calle=(p.mis_en_calle()), tope=(tope()), mis_en_garajes=(p.mis_en_garajes())) + (tr(', y {naves} en hangares').format(naves=(naves)) if naves else "")
    m = Menu(app, titulo, ops, intro=tr("Intro sobre un vehículo abre lo que puedes hacer con él"))
    app.abrir(m)


def menu_chofer(p):
    """Pedir un chófer de la banda, o despedirlo."""
    app, j = p.app, p.j

    def pedir(garaje=None, ficha=None, modelo=None):
        def f():
            if p.pedir_chofer(garaje, ficha, modelo):
                _volver_al_juego(p)
        return f

    def despedir():
        p.despedir_chofer()
        _volver_al_juego(p)

    def ops():
        c = p.chofer
        if c:
            estado = {"espera": tr("está en camino"), "viene": tr("está llegando"), "aqui": tr("te espera con el vehículo"), "contigo": tr("va al volante")}[c["estado"]]
            return [Opcion(f"{c['nombre']} {estado}", ayuda=tr("Viene a recogerte y conduce él hasta lo que marques en el GPS. Tú vas de pasajero.")), Opcion(tr("Despedir al chófer"), despedir,
                                                             ayuda=tr("Si el vehículo es tuyo, se queda contigo. Si es de la banda, se lo lleva, y si ibas dentro te deja en la acera."))]
        lista = [Opcion(tr('Que venga con un vehículo de la banda: {precio} euros').format(precio=(p.precio('chofer', 80))), pedir(),
                        ayuda=tr("Viene con un coche de la banda, el que tengan a mano. Cuando lo despidas, se lo lleva. Más abajo puedes elegir cuál."))]
        if len(p.chofer_modelos()) > 1:                          # y si quieres uno en concreto de los de la banda, lo eliges
            for mid in p.chofer_modelos():
                lista.append(Opcion(tr('Que venga con el {nombre} de la banda: {precio} euros').format(nombre=(p.modelos[mid]['nombre']), precio=(p.precio('chofer', 80))), pedir(modelo=mid),
                                    ayuda=(p.modelos[mid].get("desc", "") + tr(" Cuando despidas al chófer, se lo lleva.")).strip()))
        for pid, fichas in j.garajes.items():
            l = p.lug(pid)
            for d in fichas:
                if d.get("modelo") in p.modelos and not p.modelos[d["modelo"]].get("barco") and not p.modelos[d["modelo"]].get("vuela"):
                    lista.append(Opcion(tr('Que venga con {nombre_completo}, del garaje de {v}: {precio} euros').format(nombre_completo=(nombre_completo(p, d.get('nombre'), d['modelo'])), v=(p.nombre_lugar(l) if l else tr('una casa')), precio=(p.precio('chofer', 80))),
                                        pedir(pid, d), ayuda=tr("Lo saca de tu garaje. Cuando despidas al chófer, el vehículo se queda contigo, en la calle.")))
        return lista
    if not j.banda and not p.chofer:
        app.son("error")
        app.decir(tr("Para tener chófer necesitas a alguien reclutado en tu banda. Se recluta en el móvil, en Territorios, Tu banda."), True)
        return
    app.abrir(Menu(app, tr("Chófer de tu banda"), ops,
                   intro=tr("Viene a recogerte, tú subes de pasajero y él conduce hasta el destino que marques en el GPS. Tarda en llegar según el tráfico")))
