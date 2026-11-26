"""Más realismo, todo opcional: averías y pinchazos, y normas de tráfico con carné por puntos.

- Averías (opción «averias»): cada vehículo cuenta los kilómetros que rueda. De vez en cuando pincha una rueda: se oye,
  el coche tira y no pasa de media velocidad hasta que se cambia. Se arregla en un taller, con una rueda de repuesto que
  lleves encima, o con la asistencia en carretera. Y cada cierto número de kilómetros toca revisión: si no se pasa, los
  frenos van perdiendo.
- Normas de tráfico (opción «normas_trafico»): saltarse un semáforo en rojo o ir muy por encima del límite, a la vista
  de la policía, cuesta una multa y puntos del carné. Sin puntos te lo retiran: conducir sin carné delante de un agente
  ya es un delito. Los puntos se recuperan con un curso en una academia. Con la sirena puesta, o cuando ya te buscan,
  no hay multas: bastante tienes.

Los números salen de los datos del juego (data/datos/vida.json, sección realismo), que un mod puede cambiar.
"""
from .i18n import tr
import random

AJUSTES = {
    "sed_horas": 9, "higiene_horas": 30,
    "pinchazo_km": 35, "revision_km": 50, "precio_rueda": 80, "precio_revision": 150, "precio_cambio_rueda": 60,
    "limite_ciudad": 50, "margen_velocidad": 30, "multa_semaforo": 90, "multa_velocidad": 120,
    "puntos_carne": 12, "puntos_semaforo": 4, "puntos_velocidad": 3, "precio_carne": 300, "puntos_curso": 8,
}


def configurar(datos):
    c = next((x for x in datos.get("realismo", []) if isinstance(x, dict)), None)
    if not c:
        return
    for k, v in AJUSTES.items():
        try:
            n = float(c.get(k, v))
            AJUSTES[k] = n if n > 0 else v
        except (TypeError, ValueError):
            pass


def aj(k):
    return AJUSTES[k]


class Realismo:
    """Mixin de Partida."""

    # ------------------------------------------------------------------ averías
    def averias_activas(self):
        return bool(self.cfg["averias"]) and not getattr(self, "en_servidor", False)

    def _con_averias(self, v):
        from .combustible import deposito
        return not (v is self.j.veh and self.cheat_on("invulnerable")) and self.averias_activas() and v is not None and not v.tag and (deposito(v.modelo) > 0 or v.modelo.get("id") == "bici")

    def rodar(self, v, dt):
        """Se llama mientras conduces: cuenta kilómetros y, de tarde en tarde, pincha."""
        if not self._con_averias(v):
            return
        metros = abs(v.vel) * dt
        if metros <= 0:
            return
        antes = getattr(v, "km", 0.0)
        v.km = antes + metros / 1000.0
        rev = aj("revision_km")
        if int(antes // rev) < int(v.km // rev) and not getattr(v, "revision_debida", False):
            v.revision_debida = True
            self.son("reserva", cat="interfaz")
            self.decir(tr('{nombre} lleva {int} kilómetros: le toca revisión. Si no la pasas en un taller, los frenos irán a peor.').format(nombre=(v.nombre), int=(int(v.km))))
        if not getattr(v, "pinchada", False) and abs(v.vel) > 4 and random.random() < metros / (aj("pinchazo_km") * 1000.0) * self._riesgo_pinchazo(v):
            self.pinchar(v)

    @staticmethod
    def _riesgo_pinchazo(v):
        """Con neumáticos reforzados, del taller, se pincha menos."""
        from . import sistemas
        return sistemas.factor_pinchazo(v)

    def pinchar(self, v):
        if self.cheat_repair(v):
            return
        v.pinchada = True
        self.son("pinchazo", xy=(v.x, v.y))
        if v is self.j.veh:
            self.decir(tr("¡Has pinchado! El coche tira hacia un lado y no corre. ") +
                       (tr("Llevas rueda de repuesto: párate y cámbiala desde el móvil, en Servicios.") if self.j.objetos.get("rueda")
                        else tr("Ve despacio a un taller, o llama a la asistencia en carretera desde el móvil, en Servicios.")))

    def factor_averia_velocidad(self, v):
        return 0.45 if self._con_averias(v) and getattr(v, "pinchada", False) else 1.0

    def factor_averia_frenos(self, v):
        if not self._con_averias(v):
            return 1.0
        f = 0.7 if getattr(v, "pinchada", False) else 1.0
        if getattr(v, "revision_debida", False):
            pasado = getattr(v, "km", 0.0) % aj("revision_km")
            f *= max(0.6, 1.0 - 0.4 * pasado / aj("revision_km"))
        return f

    def cambiar_rueda(self, v=None, gratis=False):
        """Pone la de repuesto. Hay que estar parado, en el vehículo o al lado."""
        j = self.j
        v = v or j.veh or self.tu_vehiculo(12)
        if v is None or not getattr(v, "pinchada", False):
            self.decir(tr("No tienes ninguna rueda pinchada."), True)
            return False
        if abs(v.vel) > 1:
            self.app.son("error")
            self.decir(tr("Para el vehículo primero."), True)
            return False
        if not gratis:
            if not j.objetos.get("rueda"):
                self.app.son("error")
                self.decir(tr("No llevas rueda de repuesto. Se compran en los talleres y en las gasolineras."), True)
                return False
            j.objetos["rueda"] -= 1
        v.pinchada = False
        self.pasar_horas(0.25)
        self.son("reparar", cat="interfaz")
        self.decir(tr('Un cuarto de hora de gato y llave: rueda cambiada. {nombre} vuelve a rodar bien.').format(nombre=(v.nombre)), True)
        return True

    def pasar_revision(self, v):
        v.revision_debida = False
        v.pinchada = False
        v.km_revision = getattr(v, "km", 0.0)

    def averias_txt(self, v):
        if not self._con_averias(v):
            return ""
        t = tr(' Lleva {int} kilómetros.').format(int=(int(getattr(v, 'km', 0.0))))
        if getattr(v, "pinchada", False):
            t += tr(" Tiene una rueda pinchada.")
        if getattr(v, "revision_debida", False):
            t += tr(" Le toca revisión.")
        return t

    def averias_a_dict(self, v, d):
        """Lo que se guarda del desgaste con el vehículo."""
        if getattr(v, "km", None):
            d["km"] = round(v.km, 2)
        if getattr(v, "pinchada", False):
            d["pinchada"] = True
        if getattr(v, "revision_debida", False):
            d["revision"] = True
        if getattr(v, "queroseno", None) is not None:            # el combustible de una aeronave (vuelo.py)
            d["queroseno"] = round(float(v.queroseno), 1)
        if getattr(v, "robado", False):                          # para el desguace (1.7.4)
            d["robado"] = True
        if getattr(v, "alquilado", False):
            d["alquilado"] = True
        return d

    def averias_de_dict(self, v, d):
        if d.get("km"):
            v.km = float(d["km"])
        v.pinchada = bool(d.get("pinchada"))
        v.revision_debida = bool(d.get("revision"))
        if "queroseno" in d:
            try:
                v.queroseno = max(0.0, min(100.0, float(d["queroseno"])))
            except (TypeError, ValueError):
                pass
        v.robado = bool(d.get("robado"))
        v.alquilado = bool(d.get("alquilado"))

    # ------------------------------------------------------------------ normas de tráfico
    def normas_activas(self):
        return bool(self.cfg["normas_trafico"]) and not getattr(self, "en_servidor", False) and not self.cfg["sin_policia"]

    def _policia_mirando(self, radio=85):
        x, y = self.pos()
        if any(self.es_patrulla(o) and not o.muerto and o.dist(x, y) < radio for o in self.vehiculos):
            return True
        return any(e.tipo == "policia" and not e.muerto and e.dist(x, y) < radio * 0.6 for e in self.personas)

    def _exento(self, v):
        """Con sirena, en un vehículo de misión, con la policía ya detrás o en un tutorial, no hay multa que valga."""
        return bool(self.sirena_propia) or self.j.estrellas > 0 or (self.mision and self.mision["def"].get("tutorial")) \
            or self.mundo.tipo == "mar" or v.modelo.get("vuela") or v.modelo.get("barco")

    def multar(self, motivo, importe, puntos):
        j = self.j
        importe = int(importe)
        pagado = min(j.dinero, importe)
        j.dinero -= pagado
        resto = importe - pagado
        if resto and j.banco:
            de_banco = min(j.banco, resto)
            j.banco -= de_banco
            resto -= de_banco
        j.stats["multas_trafico"] = j.stats.get("multas_trafico", 0) + 1
        antes = j.carne_puntos
        j.carne_puntos = max(0, j.carne_puntos - int(puntos))
        self.son("multa", cat="interfaz")
        t = tr('Multa por {motivo}: {importe} euros y {int} puntos del carné.').format(motivo=(motivo), importe=(importe), int=(int(puntos)))
        if resto:
            t += tr(' No te llega: quedan {resto} euros a deber, y eso no gusta entre los vecinos.').format(resto=(resto))
            self.cambiar_ciudadania(-1.0)
        if j.carne_puntos <= 0 and antes > 0:
            t += tr(" Te has quedado sin puntos: te retiran el carné. Si un agente te ve conducir, irá a por ti. Se recupera con un curso en una academia.")
        else:
            t += tr(' Te quedan {carne_puntos}.').format(carne_puntos=(j.carne_puntos))
        self.decir(t)

    def infraccion_semaforo(self, v, i, jj):
        """Al entrar en un cruce conduciendo: si estaba en rojo para ti y hay policía mirando, multa."""
        if not self.normas_activas() or self._exento(v):
            return False
        verde_v = self.mundo.verde_vertical(i, jj, self.t)
        en_rojo = (not verde_v) if v.dir in (0, 2) else verde_v
        if not en_rojo or abs(v.vel) < 3 or self.t - getattr(self, "t_multa", -99) < 20:
            return False
        if not self._policia_mirando():
            return False
        self.t_multa = self.t
        self.multar(tr("saltarte un semáforo en rojo"), aj("multa_semaforo"), aj("puntos_semaforo"))
        return True

    def vigilar_velocidad(self, v, dt):
        """Mientras conduces: ir muy por encima del límite durante unos segundos, con la policía mirando, es multa.
        Y conducir sin carné delante de un agente, un delito."""
        if not self.normas_activas() or self._exento(v):
            self.t_exceso = 0.0
            return
        if self.j.carne_puntos <= 0 and abs(v.vel) > 2 and self.t - getattr(self, "t_sin_carne", -99) > 60 and self._policia_mirando(60):
            self.t_sin_carne = self.t
            self.delito(2, tr("Un agente te reconoce: conduces sin carné."), siempre=True)
            return
        limite = aj("limite_ciudad") * (1.0 + aj("margen_velocidad") / 100.0) / 3.6
        if abs(v.vel) <= limite:
            # frenar un momento para una curva no borra lo que llevas corriendo: se va olvidando poco a poco
            self.t_exceso = max(0.0, getattr(self, "t_exceso", 0.0) - 2.0 * dt)
            return
        self.t_exceso = getattr(self, "t_exceso", 0.0) + dt
        # Cuanto más corres, antes te ven y desde más lejos: a quien va muy rápido no lo salva pasar volando.
        exceso = (abs(v.vel) - limite) * 3.6                         # kilómetros por hora por encima de lo tolerado
        hace_falta = max(1.5, 4.0 - exceso / 20.0)
        radio = min(220.0, 85.0 + 2.0 * exceso)
        if self.t_exceso > hace_falta and self.t - getattr(self, "t_multa", -99) > 30 and self._policia_mirando(radio):
            self.t_exceso = 0.0
            self.t_multa = self.t
            kmh = int(abs(v.vel) * 3.6)
            grave = kmh >= 2 * aj("limite_ciudad")                    # al doble del límite, la multa y los puntos, dobles
            self.multar((tr('exceso de velocidad muy grave, a {int} por hora donde el límite es {int2}') if grave else
                         tr('exceso de velocidad, a {int} por hora donde el límite es {int2}')).format(int=(kmh), int2=(int(aj('limite_ciudad')))),
                        aj("multa_velocidad") * (2 if grave else 1), aj("puntos_velocidad") * (2 if grave else 1))

    def carne_txt(self):
        if not self.normas_activas():
            return ""
        p = self.j.carne_puntos
        return tr(" Te han retirado el carné de conducir.") if p <= 0 else tr(' Carné de conducir: {v} puntos.').format(v=(p))

    def recuperar_carne(self):
        """El curso de recuperación de puntos, en una academia."""
        j = self.j
        tope = int(aj("puntos_carne"))
        if j.carne_puntos >= tope:
            self.decir(tr("Tienes todos los puntos del carné."), True)
            return False
        if not self.pagar(int(aj("precio_carne"))):
            return False
        j.carne_puntos = min(tope, max(j.carne_puntos, 0) + int(aj("puntos_curso")))
        self.pasar_horas(4)
        self.son("jornada", cat="interfaz")
        self.decir(tr('Cuatro horas de clase y un examen. Vuelves a tener {carne_puntos} puntos en el carné.').format(carne_puntos=(j.carne_puntos)), True)
        return True
