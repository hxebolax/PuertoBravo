"""Atracos a cualquier local con caja y asaltos a los proveedores (1.7.1).

El atraco de las tiendas vale ahora para todo local cuyo tipo tenga caja en los datos (gente.json, cajas_locales):
talleres, gimnasios, armerías, bares, farmacias, cines, hoteles... Si la caja no tiene guardia, es como en la tienda:
se vacía y salta la alarma. Si la tiene, hay que acabar antes con ella, coger la caja y despistar a la policía. El
local te recuerda unos días: o te cierra la puerta, o te deja entrar y llama a la policía en cuanto te ve.

Los proveedores de sustancias (solo con el contenido para adultos) se asaltan: guardias, mercancía y dinero. Y tiene
consecuencias: ese proveedor deja de venderte unos días, o te sube los precios, o manda gente a por ti.

Los números y las frases están en los datos (vida.json, sección atracos).
"""
from .i18n import tr
from .cheats import text as cheat_text
import random

from . import gente as G
from .ajustes import Ajustes
from .entidades import Persona

AJ = Ajustes("atracos", {
    "recuerdo_min": 2, "recuerdo_max": 4, "hostil_prob": 40, "hostil_busqueda": 1,
    "proveedor_descanso": 3, "proveedor_veto_min": 3, "proveedor_veto_max": 6, "proveedor_caro": 60, "proveedor_caro_dias": 5,
    "proveedor_mercancia_min": 15, "proveedor_mercancia_max": 45, "proveedor_refuerzos": 2,
    "peso_veto": 40, "peso_caro": 30, "peso_represalia": 30,
    "represalia_min": 2, "represalia_max": 4, "represalia_horas_min": 1, "represalia_horas_max": 5,
}, {
    "sin_recuerdo": ["banco"],
    "no_atracables": ["banco", "proveedor"],
    "encargados": [tr("tienda=El dependiente"), tr("taller=El mecánico"), tr("gimnasio=El monitor"), tr("armeria=El armero"), tr("farmacia=La farmacéutica"), tr("comida=El camarero"),
                   tr("pizzeria=El pizzero"), tr("bar=La camarera"), tr("taberna=El tabernero"), tr("ropa=La dependienta"), tr("empenos=El prestamista"), tr("casino=El cajero"),
                   tr("loteria=La lotera"), tr("pescaderia=El pescadero"), tr("cine=La taquillera"), tr("hotel=El recepcionista"), tr("concesionario=El vendedor"), tr("club=El encargado")],
    "frases_atraco": [tr("¡Manos arriba! {quien} vacía la caja sin rechistar: {botin} euros. ¡Ha pulsado la alarma, lárgate!"),
                      tr("¡Esto es un atraco! {quien} te mira, traga saliva y te da lo que hay: {botin} euros. Al salir oyes la alarma."),
                      tr("Enseñas el arma y no hace falta decir más. {quien} llena una bolsa: {botin} euros. Ya suena la alarma.")],
    "frases_guardia": [tr("¡Esto es un atraco! Pero aquí la caja tiene quien la guarde: acaba con {guardia}."),
                       tr("Sacas el arma y {quien} se echa al suelo. Quien no se echa al suelo es {guardia}."),
                       tr("¡Todo el mundo quieto! {guardia} no piensa lo mismo: a por ti.")],
    "frases_cerrado": [tr("{lugar}. Te reconocen desde dentro y echan el cierre: después del atraco, aquí no entras en {dias}."),
                       tr("{lugar}. {quien} te ve venir y cierra la puerta con llave. Vuelve dentro de {dias}, a ver si se le ha pasado."),
                       tr("{lugar}. Hay un cartel nuevo en la puerta, con tu descripción. No te abren: prueba dentro de {dias}.")],
    "frases_hostil": [tr("{lugar}. Entras, y {quien} te reconoce: descuelga el teléfono sin quitarte ojo. Has salido justo cuando marcaba el número de la policía."),
                      tr("{lugar}. En cuanto cruzas la puerta, {quien} grita que eres tú, el del atraco, y alguien llama a la policía. Sales por donde has venido."),
                      tr("{lugar}. {quien} no te dice nada, pero pisa algo bajo el mostrador. Cuando oyes la alarma ya estás en la calle.")],
    "frases_asalto": [tr("Tiras la mesa de una patada y sacas el arma. Los de {lugar} no se lo esperaban, pero se rehacen deprisa."),
                      tr("¡Nadie se mueve! En {lugar} se mueve todo el mundo, y todos hacia sus armas."),
                      tr("Entras en {lugar} disparando al techo. Los que guardan la mercancía contestan sin preguntar.")],
    "frases_veto": [tr("Se ha corrido la voz: en {lugar} no te venden nada durante {dias}."), tr("Los de {lugar} han jurado no tratar contigo: {dias} sin poder comprarles.")],
    "frases_caro": [tr("Los de {lugar} seguirán tratando contigo, pero se lo cobran: {dias} con los precios por las nubes."),
                    tr("En {lugar} han decidido que lo que te llevaste lo vas a pagar tú, poco a poco: precios más altos durante {dias}.")],
    "frases_represalia_aviso": [tr("Los de {lugar} no olvidan: han puesto precio a darte un escarmiento. Anda con ojo las próximas horas."),
                                tr("Alguien te avisa de que los de {lugar} han mandado gente a buscarte. No tardarán.")],
    "frases_represalia_llega": [tr("¡{quienes} te han encontrado! Vienen {n} a por ti."), tr("{quienes} no olvidan: {n} de los suyos vienen a cobrárselo.")],
    "represalia_tipos": ["pandillero_motorizado", "pandillero_duro", "maton"],
    "refuerzo_tipos": ["pandillero_motorizado", "pandillero_motero"],
}, cero=("hostil_prob", "hostil_busqueda", "proveedor_refuerzos", "peso_veto", "peso_caro", "peso_represalia", "proveedor_caro"))


def _dias(n):
    n = int(n)
    return tr("un día") if n == 1 else tr('{n} días').format(n=(n))


def encargado(tipo):
    for linea in AJ.lista("encargados"):
        k, _, v = linea.partition("=")
        if k.strip() == tipo and v.strip():
            return v.strip()
    return tr("El encargado")


class Atracos:
    """Mixin de Partida."""

    # ------------------------------------------------------------------ enemigos que vienen a por ti
    def mandar_enemigos(self, clase, n, banda=None, tag="represalia", nombre=None):
        """Manda a por ti a n enemigos de un tipo: llegan en su vehículo si el tipo lo tiene (y se puede); si no, salen
        a pie a unas decenas de metros. Te atacan ellos: defenderte no es delito. Devuelve la lista."""
        if G.tipo_enemigo(clase) is None:
            clase = "maton" if G.tipo_enemigo("maton") else next(iter(G.TIPOS), None)
        gente = []
        for _ in range(max(1, int(n))):
            f = G.enemigo(G.grupo(clase, tipo=nombre or tr("Matón"), arma="pistola", salud=70))
            e = G.vestir(Persona("enemigo", *self.pos(), nombre or f["nombre"]), f)
            e.hostil, e.estado, e.activo, e.tag = True, "ataca", True, tag
            e.agresor = True
            if banda:
                e.banda = banda
            e.t_disparo = random.uniform(1.5, 3.0)
            gente.append(e)
        f = G.enemigo({"n": 1, "clase": clase}) if clase else {"vehiculo": "", "ocupantes": 2}
        a_pie = list(gente)
        if f.get("vehiculo") and not self.en_servidor:
            while a_pie:
                viajan = a_pie[:max(1, int(f.get("ocupantes", 2) or 2))]
                if self.llegar_en_vehiculo(f["vehiculo"], viajan) is None:
                    break
                a_pie = a_pie[len(viajan):]
        for e in a_pie:
            pos = self._punto_cercano(30, 55) or self.mundo.punto_libre(self.pos()[0] + random.uniform(-25, 25), self.pos()[1] + random.uniform(-25, 25))
            e.x, e.y = pos
            self.personas.append(e)
        return gente

    # ------------------------------------------------------------------ atracar un local
    def local_atracable(self, l):
        return l is not None and l.tipo not in AJ.lista("no_atracables") and G.caja_local(l.tipo) is not None

    def atraco_motivo(self, l, golpe=None):
        if self.arma()["tipo"] != "fuego":
            return tr("Para atracar tienes que empuñar un arma de fuego.")
        if self.atracadas.get(l.id) == self.dia:
            return tr("La caja está vacía: ya la atracaste hoy.")
        if self.de_servicio():
            return tr("Estás de servicio. Si atracas esto, se acabó la placa.")
        c = G.caja_local(l.tipo)
        if ((c and c.get("guardias") and c.get("guardia")) or golpe) and (self.mision or self.trabajo or self.guerra):
            return tr("Termina antes lo que tienes entre manos: ") + (tr("un golpe preparado pide toda tu atención.") if golpe else tr("aquí la caja tiene guardia."))
        return ""

    def atracar_local(self, l, golpe=None):
        """Atraca un local. Sin guardia, la caja se vacía en el acto; con guardia, primero hay que acabar con ella.
        Con un plan de golpe preparado (golpes.py), la caja tarda en abrirse siempre y cada uno de tu banda hace su papel.
        Devuelve True si el atraco ha empezado."""
        motivo = self.atraco_motivo(l, golpe)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        caja = self.caja_de_local(l)
        if caja is None:
            return False
        self.atracadas[l.id] = self.dia
        self.recordar_atraco(l)
        quien = encargado(l.tipo)
        botin = int(caja["dinero"])
        nivel = max(1, int(caja.get("busqueda") or 1))
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        self.salir_interior(silencio=True)
        self.j.stats["atracos_locales"] = self.j.stats.get("atracos_locales", 0) + 1
        if not caja["enemigos"] and not golpe:
            self.son("grito", vol=0.5)
            self.sv_encargo("atraco_local", botin)             # en un servidor: es un cobro de los que se repiten, no cuenta contra el tope por hora
            self.hon_negro(botin)
            self.dar_dinero(botin)
            self.decir(AJ.frase("frases_atraco", quien=quien, botin=botin))
            self.poner_busqueda(nivel)
            return True
        n = int(caja["guardias"] or 0)
        tipo = G.tipo_enemigo(caja["guardia"]) or {}
        guardia = (tr('{n} de guardia').format(n=(n)) if n > 1 else tr("el de guardia")) if not tipo.get("nombre") else (tr('{n} con pinta de {lower}').format(n=(n), lower=(tipo['nombre'].lower())) if n > 1 else tr('un {lower}').format(lower=(tipo['nombre'].lower())))
        self.son("grito", vol=0.5)
        pasos = [{"tipo": "eliminar", "lugar": l.id, "ya": True, "texto": AJ.frase("frases_guardia", quien=quien, guardia=guardia), "enemigos": caja["enemigos"]}] if caja["enemigos"] else []
        pasos += [{"tipo": "recoger", "lugar": l.id, "objeto": tr('La caja de {nombre}').format(nombre=(l.nombre)),
                   "texto": tr("Ya no la guarda nadie. Coge la caja.") if caja["enemigos"] else tr('{quien} levanta las manos y se aparta de la caja. Ve a por ella.').format(quien=(quien))},
                  {"tipo": "policia", "nivel": nivel, "texto": tr("¡Alguien ha avisado a la policía! Despístala para quedarte lo de la caja.")}]
        m = {"id": "atraco_local", "titulo": tr('Atraco a {nombre}').format(nombre=(l.nombre)), "lugar": l.id, "contador": "atracos_con_guardia" if caja["enemigos"] else "atracos_preparados",
             "pasos": pasos, "recompensa": {"dinero": botin}}
        if golpe:
            self.golpe_adaptar(m, l, golpe)
        self._empezar_repetible(m)
        return True

    def recordar_atraco(self, l):
        if l.tipo in AJ.lista("sin_recuerdo"):
            return
        dias = random.randint(*sorted((AJ.entero("recuerdo_min"), AJ.entero("recuerdo_max"))))
        if dias <= 0:
            return
        self.j.locales_vetados[l.id] = {"hasta": self.dia + dias, "modo": "hostil" if random.random() * 100 < AJ("hostil_prob") else "cerrado"}

    def local_te_recuerda(self, l):
        """Lo que recuerda de ti un local que has atracado: {"hasta", "modo"}, o None si ya se le ha pasado."""
        r = self.j.locales_vetados.get(l.id)
        if not r:
            return None
        if self.dia > int(r.get("hasta", 0)):
            del self.j.locales_vetados[l.id]
            return None
        return r

    def entrada_vetada(self, l):
        """Al ir a entrar en un local: si lo has atracado hace poco, no te atienden. Devuelve True si no entras."""
        r = self.local_te_recuerda(l)
        if not r:
            return False
        dias = _dias(int(r["hasta"]) - self.dia + 1)
        quien = encargado(l.tipo)
        self.app.son("error")
        if r.get("modo") == "hostil" and self.atracadas.get(l.id) != self.dia and not self.cfg["sin_policia"]:
            self.son("alarma", xy=(l.x, l.y), ref=10, maxd=120, vol=0.5)
            self.decir(AJ.frase("frases_hostil", lugar=l.nombre, quien=quien, dias=dias), True)
            if AJ("hostil_busqueda") >= 1:
                self.poner_busqueda(AJ.entero("hostil_busqueda"))
            r["modo"] = "cerrado"                               # ya saben que rondas por aquí: desde ahora, la puerta cerrada
        else:
            self.decir(AJ.frase("frases_cerrado", lugar=l.nombre, quien=quien, dias=dias), True)
        return True

    # ------------------------------------------------------------------ asaltar a un proveedor
    def proveedor_estado(self, l):
        return self.j.proveedores.setdefault(l.id, {})

    def proveedor_vetado(self, l):
        """Días que le quedan a este proveedor sin venderte nada, o 0."""
        return max(0, int(self.j.proveedores.get(l.id, {}).get("veto", 0)) - self.dia + 1)

    def factor_proveedor(self, l):
        e = self.j.proveedores.get(getattr(l, "id", l), {})
        return 1.0 + AJ("proveedor_caro") / 100.0 if self.dia <= int(e.get("caro", 0)) else 1.0

    def asalto_motivo(self, l):
        if not self.modo_adulto():
            return tr("Eso es del contenido para adultos.")
        if self.en_servidor:
            return tr("En un servidor en línea no se asalta a los proveedores.")
        if self.mision or self.trabajo or self.guerra:
            return tr("Termina antes lo que tienes entre manos.")
        if self.arma()["tipo"] not in ("fuego", "explosivo"):
            return tr("Para asaltar a esta gente tienes que empuñar un arma de fuego.")
        e = self.j.proveedores.get(l.id, {})
        if e.get("asaltado") and self.dia - int(e["asaltado"]) < AJ("proveedor_descanso"):
            return tr("Después de lo de la otra vez, aquí no han vuelto a traer género: no hay nada que llevarse todavía.")
        return ""

    def asaltar_proveedor(self, l, golpe=None):
        motivo = self.asalto_motivo(l)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        j = self.j
        caja = self.caja_de_local(l) or {"dinero": random.randint(1200, 4000), "enemigos": [G.grupo("pandillero", 3, tipo=tr("Matón del proveedor"), arma="pistola", salud=75)]}
        enemigos = list(caja["enemigos"]) or [G.grupo("pandillero", 3, tipo=tr("Matón del proveedor"), arma="pistola", salud=75)]
        n_ref = AJ.entero("proveedor_refuerzos")
        ref = next((c for c in AJ.lista("refuerzo_tipos") if G.tipo_enemigo(c) and G.tipo_enemigo(c).get("vehiculo") in self.modelos), None)
        if n_ref > 0 and ref and random.random() < 0.7:
            enemigos.append({"n": n_ref, "clase": ref})
        est = self.proveedor_estado(l)
        est["asaltado"] = self.dia
        # las consecuencias se deciden ya: aunque el asalto salga mal, no se les olvida
        pesos = [("veto", AJ("peso_veto")), ("caro", AJ("peso_caro")), ("represalia", AJ("peso_represalia"))]
        total = sum(w for _, w in pesos) or 1.0
        r, cual = random.uniform(0, total), "veto"
        for k, w in pesos:
            if r < w:
                cual = k
                break
            r -= w
        if cual == "veto":
            dias = random.randint(*sorted((AJ.entero("proveedor_veto_min"), AJ.entero("proveedor_veto_max"))))
            est["veto"] = self.dia + dias
            aviso = AJ.frase("frases_veto", lugar=l.nombre, dias=_dias(dias))
        elif cual == "caro":
            est["caro"] = self.dia + AJ.entero("proveedor_caro_dias")
            aviso = AJ.frase("frases_caro", lugar=l.nombre, dias=_dias(AJ.entero("proveedor_caro_dias")))
        else:
            horas = AJ.entre("represalia_horas_min", "represalia_horas_max")
            j.represalias.append({"cuando": self.dia * 1440.0 + self.reloj + horas * 60.0, "lugar": l.nombre,
                                  "n": random.randint(*sorted((AJ.entero("represalia_min"), AJ.entero("represalia_max"))))})
            aviso = AJ.frase("frases_represalia_aviso", lugar=l.nombre)
        est["consecuencia"] = cual

        def hecho():
            ilegales = [s for s in self.dato_adulto("sustancias") if not s.get("legal")]
            disponible = random.randint(*sorted((AJ.entero("proveedor_mercancia_min"), AJ.entero("proveedor_mercancia_max"))))
            cuanto = min(self.hueco_mercancia(disponible), disponible)
            cogido = {}
            for _ in range(cuanto if ilegales else 0):
                s = random.choice(ilegales)
                cogido[s["id"]] = cogido.get(s["id"], 0) + 1
            for ident, n in cogido.items():
                j.sustancias[ident] = j.sustancias.get(ident, 0) + n
            if cogido:
                self.son("trato", cat="interfaz")
                estado_carga = (cheat_text('. Llevas {carga} unidades, sin límite de inventario.', '. Carrying {carga} units, with unlimited inventory.')
                                if self.cheat_on("cheat_mochila") else tr('. Llevas {carga} de 100 unidades.')).format(carga=self.carga())
                self.decir(tr("Te llevas la mercancía: ") + ", ".join(tr('{n} de {lower}').format(n=(n), lower=(self.sustancia(i)['nombre'].lower())) for i, n in cogido.items()) + estado_carga)
            elif ilegales:
                self.decir(tr("La mercancía no te cabe: llevas la mochila llena."))
            self.cambiar_reputacion(3)
            self.decir(aviso)
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        self.salir_interior(silencio=True)
        self.son("grito", vol=0.5)
        m = {"id": "asalto_proveedor", "titulo": tr('Asalto a {nombre}').format(nombre=(l.nombre)), "lugar": l.id, "contador": "asaltos_proveedor", "al_completar": hecho,
             "pasos": [
                 {"tipo": "eliminar", "lugar": l.id, "ya": True, "texto": AJ.frase("frases_asalto", lugar=l.nombre), "enemigos": enemigos},
                 {"tipo": "recoger", "lugar": l.id, "objeto": tr('La mercancía y la caja de {nombre}').format(nombre=(l.nombre)), "texto": tr("Ya no queda nadie en pie. Coge la mercancía y la caja.")}],
             "recompensa": {"dinero": int(caja["dinero"])}}
        if golpe:
            self.golpe_adaptar(m, l, golpe)
        self._empezar_repetible(m)
        return True

    def actualizar_atracos(self, dt):
        """Las represalias pendientes: cuando les llega la hora y estás en la calle, vienen a por ti."""
        j = self.j
        if not j.represalias or self.en_servidor:
            return
        self._t_represalias = getattr(self, "_t_represalias", 0.0) - dt
        if self._t_represalias > 0:
            return
        self._t_represalias = 2.0
        ahora = self.dia * 1440.0 + self.reloj
        r = j.represalias[0]
        if ahora < r.get("cuando", 0):
            return
        if self.mision or self.trabajo or self.guerra or self.transicion or self.mundo.tipo in ("mar", "isla") or j.estrellas >= 3 or self.de_servicio():
            return
        j.represalias.pop(0)
        clase = next((c for c in AJ.lista("represalia_tipos") if G.tipo_enemigo(c)), "maton")
        gente = self.mandar_enemigos(clase, int(r.get("n", 2)), tag="represalia")
        self.son("evento", cat="interfaz")
        de = str(r.get("lugar") or tr("el proveedor"))
        quienes = de if de.startswith((tr("Los "), tr("Las "))) else tr('Los de {de}').format(de=(de))          # una banda ya lleva su artículo
        self.decir(AJ.frase("frases_represalia_llega", quienes=quienes, lugar=de, n=len(gente)) + tr(" Pulsa Q para fijarlos cuando los oigas."))


TEXTO_GOLPE = tr("Preparar el golpe con tu banda: repartir los papeles antes de atracar")
AYUDA_GOLPE = (tr("Con gente de tu banda al lado, cada uno hace un papel: conductor con el motor en marcha, vigilante que entretiene a la policía, escolta que tiene a raya a la gente, "
               "el de la caja y tirador para la huida. La caja tarda en abrirse y cada uno se lleva su parte. Dentro, la primera opción lo explica. El atraco de siempre sigue en su opción."))


def con_atraco(p, lugar, menu, Opcion):
    """Añade al menú de un local con caja la opción de atracarlo, antes de la de salir."""
    if not p.local_atracable(lugar):
        return
    fuente = menu._fuente
    from .menus import SALIDAS
    caja = G.caja_local(lugar.tipo) or {}
    n = int(caja.get("guardias") or 0)
    ayuda = tr("Necesitas un arma de fuego en la mano. ") + (
        tr('La caja tiene guardia: {n} {v}. Hay que acabar con ella, coger la caja y despistar a la policía. ').format(n=(n), v=(tr('personas') if n > 1 else tr('persona')))
        if n and caja.get("guardia") else tr("Aquí no hay guardia: la caja se vacía en el acto, y salta la alarma. ")) + \
        tr('La policía te buscará con nivel {max}. Una vez al día, y el local te recuerda: durante unos días no te dejan entrar, o llaman a la policía en cuanto te ven.').format(max=(max(1, int(caja.get('busqueda') or 1))))
    texto = tr("Atracar la tienda") if lugar.tipo == "tienda" else tr('Atracar este local: {nombre}').format(nombre=(lugar.nombre))

    def preparar():
        from . import golpes
        golpes.preparar(p, lugar, lambda plan: p.atracar_local(lugar, plan), tr("el golpe"))

    def ops():
        lista = list(fuente() if callable(fuente) else fuente)
        if any(o.texto == texto for o in lista):
            return lista
        nuevas = [Opcion(texto, lambda: p.atracar_local(lugar), ayuda=ayuda)]
        if p.j.banda and not p.en_servidor:                      # con gente en la banda, se puede preparar antes
            nuevas.append(Opcion(TEXTO_GOLPE, preparar, ayuda=AYUDA_GOLPE))
        pos = len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista)
        lista[pos:pos] = nuevas
        return lista
    menu._fuente = ops
    menu.refrescar(False)
