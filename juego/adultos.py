"""Contenido para mayores de 18 años: relaciones, compañía de pago, sustancias, adicción y trapicheo.

Solo funciona con la opción «Contenido para adultos» activada. Nada es explícito: las escenas
íntimas se resuelven con un fundido. Lo importante son las consecuencias: todo afecta al ánimo,
a la salud, a la reputación en la calle y a las relaciones.

El ánimo y la reputación existen siempre, con o sin esta opción, y también dependen del resto del juego.
"""
from .i18n import tr
import math
import random

from . import mundo as M

CAPACIDAD = 100         # unidades de mercancía que caben en la mochila


class Adultos:
    # ------------------------------------------------------------ utilidades
    def modo_adulto(self):
        return bool(self.cfg["adultos"])

    def dato_adulto(self, clave):
        datos = self.datos.get("adultos", {}).get(clave, [])
        if clave == "personas":
            return datos + [r["contacto"] for r in self.j.relaciones.values() if isinstance(r.get("contacto"), dict)]
        return datos

    def sustancia(self, ident):
        return next((s for s in self.dato_adulto("sustancias") if s["id"] == ident), None)

    def persona_social(self, ident):
        return next((p for p in self.dato_adulto("personas") if p["id"] == ident), None)

    # ------------------------------------------------------ ánimo y reputación
    def animo_txt(self):
        a = self.j.animo
        return tr("por los suelos") if a < 20 else "bajo" if a < 40 else "normal" if a < 65 else "bueno" if a < 85 else tr("por las nubes")

    def reputacion_txt(self):
        r = self.j.reputacion
        return tr("nadie te conoce") if r < 5 else tr("empiezan a conocerte") if r < 20 else tr("te respetan") if r < 50 else tr("te temen") if r < 90 else tr("eres una leyenda")

    def cambiar_animo(self, n, motivo=None):
        j = self.j
        antes = self.animo_txt()
        j.animo = max(0.0, min(100.0, j.animo + n))
        ahora = self.animo_txt()
        if ahora != antes:
            self.son("animo_sube" if n > 0 else "animo_baja", cat="interfaz")
            self.decir((f"{motivo}. " if motivo else "") + tr('Tu ánimo ahora es {ahora}.').format(ahora=(ahora)))

    def cambiar_reputacion(self, n):
        antes = self.reputacion_txt()
        self.j.reputacion = max(0.0, self.j.reputacion + n)
        if self.reputacion_txt() != antes:
            self.son("fama", cat="interfaz")
            self.decir(tr('Tu fama en la calle cambia: {reputacion_txt}.').format(reputacion_txt=(self.reputacion_txt())))

    def mod_punteria(self):
        m = 0.04 if self.j.animo >= 75 else -0.06 if self.j.animo <= 25 else 0.0
        for e in self.j.efectos:
            m += e.get("punteria", 0.0)
        if self._abstinencia():
            m -= 0.06
        return m

    def mod_velocidad(self):
        m = 0.9 if self.j.animo <= 25 else 1.0
        for e in self.j.efectos:
            m *= e.get("velocidad", 1.0)
        return m

    def mod_dano(self):
        m = 1.0
        for e in self.j.efectos:
            m *= e.get("dano", 1.0)
        if self._abstinencia():
            m *= 1.2
        return m

    def deriva(self):
        return sum(e.get("deriva", 0.0) for e in self.j.efectos)

    # ---------------------------------------------------------------- consumo
    def _abstinencia(self):
        j = self.j
        return any(nivel >= 40 and self.dia - j.ultima_dosis.get(s, self.dia) >= 1 for s, nivel in j.adiccion.items())

    def consumir(self, ident, de_inventario=True):
        j = self.j
        s = self.sustancia(ident)
        if s is None:
            return
        if de_inventario:
            if j.sustancias.get(ident, 0) <= 0:
                self.decir(tr('No te queda {lower}.').format(lower=(s['nombre'].lower())), True)
                return
            j.sustancias[ident] -= 1
        activas = sum(1 for e in j.efectos if e["id"] == ident and not e.get("bajon"))
        j.efectos.append({"id": ident, "t": float(s["duracion"]), "punteria": s.get("punteria", 0.0), "velocidad": s.get("velocidad", 1.0),
                          "dano": s.get("dano", 1.0), "deriva": s.get("deriva", 0.0), "tono": s.get("tono", 0.0)})
        j.adiccion[ident] = min(100.0, j.adiccion.get(ident, 0.0) + s.get("adiccion", 0))
        j.ultima_dosis[ident] = self.dia
        j.stats["consumos"] = j.stats.get("consumos", 0) + 1
        sonido = {"alcohol": "tomar_copa"}.get(ident, "tomar_" + ident)
        self.son(sonido if sonido in self.mez.sonidos else "comer", cat="interfaz")
        self.decir(tr('Tomas {unidad} de {lower}.').format(unidad=(s['unidad']), lower=(s['nombre'].lower())), True)
        self.cambiar_animo(s.get("animo", 0))
        if activas + 1 >= s.get("sobredosis", 99):
            self.sobredosis(s)
            return
        if activas + 1 == s.get("sobredosis", 99) - 1:
            self.decir(tr("Notas que te has pasado. Una más y acabas en el hospital."))
        nivel = j.adiccion[ident]
        if nivel >= 40 and nivel - s.get("adiccion", 0) < 40:
            self.son("abstinencia", cat="interfaz")
            self.decir(tr('Empiezas a necesitar {lower}. Si pasas un día sin tomar, lo notarás: peor puntería, peor ánimo y más daño. En un hospital pueden desintoxicarte.').format(lower=(s['nombre'].lower())))

    def sobredosis(self, s):
        if self.transicion:
            return
        from .menus import Dialogo
        j = self.j
        self.transicion = True
        j.efectos = []
        j.stats["sobredosis"] = j.stats.get("sobredosis", 0) + 1
        self.son("sobredosis", cat="interfaz")
        self.app.vibrar(1.0, 0.3, 900)
        if j.veh:
            self.salir_vehiculo(forzado=True)
        self._fin_persecucion()
        if self.trabajo:
            self.terminar_trabajo(None)
        coste = min(j.dinero, self.precio("hospital_sobredosis", 400))
        j.dinero -= coste
        h = self._reaparecer("hospital")
        j.salud = max(20.0, j.salud_max * 0.4)
        self.pasar_horas(12)
        j.animo = max(0.0, j.animo - 25)
        self.cancelar_gps()

        def fin():
            self.transicion = False
            if self.mision and not self.mision_en_escena():
                self.fallar_mision(tr("Has perdido el conocimiento."))
        self.app.abrir(Dialogo(self.app, [(tr("Narrador"), tr('El mundo se apaga de golpe. Demasiado {lower}. Despiertas doce horas después en {nombre} con un gotero en el brazo, {coste} euros menos y la peor resaca de tu vida.').format(lower=(s['nombre'].lower()), nombre=(h.nombre), coste=(coste)))], fin))

    def actualizar_adultos(self, dt):
        j = self.j
        base = 0.72 if getattr(self, "lento", False) else 1.0          # con el tiempo lento, todo suena más grave
        if not j.efectos:
            if self.mez.tono_mundo != base:
                self.mez.tono_mundo = base
            return
        tono = 0.0
        for e in list(j.efectos):
            e["t"] -= dt
            tono += e.get("tono", 0.0)
            if e["t"] <= 0:
                j.efectos.remove(e)
                if not e.get("bajon"):
                    s = self.sustancia(e["id"])
                    b = (s or {}).get("bajon")
                    if b and not any(x["id"] == e["id"] and not x.get("bajon") for x in j.efectos):
                        j.efectos.append({"id": e["id"], "bajon": True, "t": float(b.get("duracion", 60)), "punteria": b.get("punteria", 0.0)})
                        self.son("bajon", cat="interfaz")
                        self.decir(tr('Se pasa el efecto de {lower} y llega el bajón.').format(lower=(s['nombre'].lower())))
                        self.cambiar_animo(b.get("animo", 0))
                        if b.get("salud"):
                            j.salud = max(5.0, j.salud + b["salud"])
        self.mez.tono_mundo = (1.0 + tono * math.sin(self.t * 1.7) if tono else 1.0) * base

    def dia_adultos(self):
        """Lo que cambia cada medianoche: ánimo, adicciones y relaciones."""
        j = self.j
        # el ánimo tiende a 55, con ayuda de la pareja y del perro
        j.animo += (55 - j.animo) * 0.12 + (2 if j.perro else 0)
        if not self.vida_sentimental():
            j.animo = max(0.0, min(100.0, j.animo))
            return
        for ident in list(j.adiccion) if self.modo_adulto() else ():
            if self.dia - j.ultima_dosis.get(ident, self.dia) >= 1:
                if j.adiccion[ident] >= 40:
                    self.son("abstinencia", cat="interfaz")
                    s = self.sustancia(ident)
                    self.cambiar_animo(-10, tr('Tu cuerpo pide {v}').format(v=(s['nombre'].lower() if s else ident)))
                j.adiccion[ident] = max(0.0, j.adiccion[ident] - 3)
                if j.adiccion[ident] <= 0:
                    del j.adiccion[ident]
        for pid, r in list(j.relaciones.items()):
            p = self.persona_social(pid)
            if p is None:
                continue
            dias = self.dia - r.get("ultimo", self.dia)
            if r["estado"] == "pareja":
                if dias >= 3:
                    r["afinidad"] = max(0, r["afinidad"] - 3)
                    if dias in (3, 6):
                        self.decir(tr('{nombre} te escribe: hace días que no sabe de ti.').format(nombre=(p['nombre'])))
                else:
                    j.animo += 3
                    if random.random() < 0.12:
                        self.dar_dinero(random.randint(20, 80), tr('{nombre} te ha dejado un detalle en casa').format(nombre=(p['nombre'])))
                if r["afinidad"] < 30:
                    self.marcar_ruptura(r)
                    r.pop("compromiso", None)
                    j.pareja = ""
                    self.son("ruptura", cat="interfaz")
                    self.cambiar_animo(-25, tr('{nombre} te ha dejado').format(nombre=(p['nombre'])))
            elif dias >= 4 and r["estado"] != "ex":
                r["afinidad"] = max(0, r["afinidad"] - 1)
        j.animo = max(0.0, min(100.0, j.animo))
        from .encuentros import invitacion_diaria
        invitacion_diaria(self)

    # -------------------------------------------------------------- relaciones
    def marcar_ruptura(self, r):
        """Se acaba una relación, la dejes tú o te deje: pasa a ex y se apunta el día, para los días de hielo (hielo_ex)."""
        r["estado"] = "ex"
        r["ruptura_dia"] = self.dia

    def hielo_ex(self, r):
        """Cuántos días le quedan a la expareja de resentimiento tras la ruptura (issue 41): mientras tanto corta al
        charlar, cuelga, no contesta, rechaza los gestos, las citas y volver. 0 si no es ex o ya se le ha pasado. Cuánto dura
        está en los datos (encuentros, hielo_ex_dias); a cero, nunca. Una ruptura de antes de la 1.7.6 no tiene día: nada."""
        from .encuentros import AJ
        if not r or r.get("estado") != "ex" or r.get("ruptura_dia") is None:
            return 0
        try:
            return max(0, int(r["ruptura_dia"]) + AJ.entero("hielo_ex_dias") - int(self.dia))
        except (TypeError, ValueError):
            return 0

    def frase_hielo(self, que, pers):
        """La frase cortante de la expareja para charlar, llamada, mensaje, gesto, cita o pedir."""
        from .encuentros import AJ
        return AJ.frase("frases_hielo_" + que, n=pers["nombre"])

    def relacion(self, pid):
        return self.j.relaciones.setdefault(pid, {"estado": "conocida", "afinidad": 5, "ultimo": self.dia, "hoy": {}})

    def afinidad_txt(self, r):
        a = r["afinidad"]
        return tr("os acabáis de conocer") if a < 15 else tr("os caéis bien") if a < 35 else tr("hay confianza") if a < 55 else tr("hay mucha química") if a < 80 else tr("estáis locos el uno por el otro")

    def _hecho_hoy(self, r, que):
        hoy = r.setdefault("hoy", {})
        if hoy.get(que) == self.dia:
            return True
        hoy[que] = self.dia
        return False

    def sumar_afinidad(self, pid, n):
        r = self.relacion(pid)
        if n > 0 and self.j.pareja == pid and int(r.get("desconfia_hasta", 0)) > self.dia:
            n = max(1, n // 2)                                   # mientras no se fía de ti, lo que hacéis juntos acerca la mitad (encuentros.py)
        r["afinidad"] = max(0, min(100, r["afinidad"] + n))
        r["ultimo"] = self.dia
        self.son("afinidad_sube" if n >= 0 else "afinidad_baja", cat="interfaz")
        return r

    def celos(self, con_quien=None):
        """Si tienes pareja y haces algo a sus espaldas, puede enterarse."""
        j = self.j
        if not j.pareja or j.pareja == con_quien:
            return False
        if random.random() < 0.35:
            from . import encuentros
            p = self.persona_social(j.pareja)
            r = self.relacion(j.pareja)
            reincide = encuentros.herir(self, j.pareja)          # la herida dura días; si vuelve a pasar mientras tanto, se acabó
            r["afinidad"] = max(0, r["afinidad"] - 35)
            self.son("afinidad_baja", cat="interfaz")
            self.cambiar_animo(-15)
            if reincide:
                r["afinidad"] = min(r["afinidad"], 25)
            if r["afinidad"] < 30:
                self.son("ruptura", cat="interfaz")
                self.marcar_ruptura(r)
                j.pareja = ""
                self.decir(tr('{nombre} se ha enterado de todo y no quiere volver a verte.').format(nombre=(p['nombre'])))
            else:
                self.decir(tr('{nombre} se ha enterado y le has hecho mucho daño. Vas a tener que ganarte otra vez su confianza: unos días en los que lo que hagáis juntos acerca la mitad. Pedirle perdón en persona ayuda. Si vuelve a pasar mientras tanto, se acabó.').format(nombre=(p['nombre'])))
            return True
        return False

    # ---------------------------------------------------------------- trapicheo
    def carga(self):
        return sum(n for s, n in self.j.sustancias.items() if s != "alcohol")

    def precio_sustancia(self, ident, lugar):
        """Precio del día en un proveedor. Cambia cada día y con cada sitio; a veces hay ganga o escasez."""
        s = self.sustancia(ident)
        rng = random.Random(f"{self.dia}:{lugar.id}:{ident}")
        f = float(lugar.get("factor", {}).get(ident, 1.0)) * rng.uniform(0.75, 1.3)
        suerte = rng.random()
        nota = ""
        if suerte < 0.08:
            f *= 0.45
            nota = "ganga"
        elif suerte > 0.92:
            f *= 1.9
            nota = "escasez"
        f *= 1.0 - min(0.15, self.j.reputacion / 600.0)
        f *= self.factor_proveedor(lugar)                        # si le has asaltado, puede que te cobre más una temporada
        return max(1, int(round(s["precio"] * f))), nota

    def precio_calle(self, ident):
        s = self.sustancia(ident)
        x, y = self.pos()
        extra = 1.2 if self.mundo.barrio(x, y)["id"] in self.j.territorios else 1.0
        return int(s["precio"] * 1.7 * extra)

    def ofrecer_mercancia(self):
        """Vender al menudeo al peatón que tienes al lado."""
        j = self.j
        cerca = [p for p in self.personas if p.tipo == "civil" and not p.muerto and p.dist(j.x, j.y) < 4.5]
        if not cerca:
            self.decir(tr("No hay nadie a tu lado a quien ofrecer."), True)
            return
        tengo = [s for s, n in j.sustancias.items() if n > 0 and s != "alcohol"]
        if not tengo:
            self.decir(tr("No llevas mercancía encima."), True)
            return
        p = min(cerca, key=lambda p: p.dist(j.x, j.y))
        if getattr(p, "ofrecido", False):
            self.decir(tr("A ese ya le has ofrecido."), True)
            return
        p.ofrecido = True
        azar = random.random()
        if azar < 0.08:
            self.son("paisano", xy=(p.x, p.y))
            self.app.vibrar(0.8, 0.8, 300)
            self.decir(tr("¡Era un policía de paisano! Saca la placa."), True)
            self.poner_busqueda(2)
            self.cambiar_reputacion(-1)
            return
        if azar < 0.2:
            p.estado = "huye"
            p.t_estado = 10
            self.son("rechazo", xy=(p.x, p.y))
            self.decir(tr("Se indigna y se aleja amenazando con llamar a la policía."), True)
            self.delito(1, tr("venta de sustancias"), siempre=random.random() < 0.5)
            return
        if azar < 0.2 + 0.42 + min(0.2, j.reputacion / 300.0):
            ident = random.choice(tengo)
            s = self.sustancia(ident)
            n = min(j.sustancias[ident], random.randint(1, 3))
            cobro = self.precio_calle(ident) * n
            j.sustancias[ident] -= n
            j.stats["vendido"] = j.stats.get("vendido", 0) + cobro
            self.son("trato", xy=(p.x, p.y))
            self.dar_dinero(cobro)
            self.hon_negro(cobro)                                # lo de la droga no se puede justificar (capo.py)
            self.cambiar_reputacion(0.4)
            self.decir(tr('Te compra {n} de {lower} por {cobro} euros. Te quedan {v}.').format(n=(n), lower=(s['nombre'].lower()), cobro=(cobro), v=(j.sustancias[ident])), True)
            self.delito(0.5, tr("venta de sustancias"))
            return
        self.son("rechazo", xy=(p.x, p.y), vol=0.6)
        self.decir(tr("No le interesa."), True)

    def perder_mercancia(self, todo=True):
        j = self.j
        n = self.carga()
        if n <= 0:
            return 0
        for s in list(j.sustancias):
            if s != "alcohol":
                j.sustancias[s] = 0 if todo else j.sustancias[s] // 2
        return n
