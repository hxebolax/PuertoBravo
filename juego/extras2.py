"""Segunda ampliación: habilidades, logros, eventos callejeros, encargos repetibles y noticias."""
from .i18n import tr
import math
import random

from . import gente as G
from . import mundo as M
from .entidades import Objeto, Persona

HABILIDADES = {
    "conduccion": (tr("Conducción"), tr("Cada nivel sube un uno por ciento la velocidad máxima y reduce los daños de tu vehículo.")),
    "punteria": (tr("Puntería"), tr("Cada nivel sube tu probabilidad de acertar.")),
    "resistencia": (tr("Resistencia"), tr("Cada nivel te hace correr más y recibir menos daño.")),
    "pesca": (tr("Pesca"), tr("Cada nivel hace que piquen antes y que tus capturas valgan más.")),
}

MODELOS_ENCARGO = ["sedan", "deportivo", "todoterreno", "furgoneta", "moto", "descapotable", "pickup", "utilitario", "buggy", "limusina"]

LOGROS = [
    ("primera", tr("De vuelta a casa"), tr("Completa tu primera misión."), lambda p: len(p.completadas) >= 1),
    ("historia", tr("Ley del asfalto"), tr("Completa la historia principal."), lambda p: "m20" in p.completadas),
    ("todas", tr("Leyenda de la comarca"), tr("Completa todas las misiones."), lambda p: len(p.completadas) >= len(p.datos["misiones"])),
    ("rico", tr("Primer millón de céntimos"), tr("Reúne 10000 euros entre efectivo y banco."), lambda p: p.j.dinero + p.j.banco >= 10000),
    ("millonario", tr("Magnate"), tr("Reúne 250000 euros entre efectivo y banco."), lambda p: p.j.dinero + p.j.banco >= 250000),
    ("casero", tr("Casero"), tr("Ten tres viviendas."), lambda p: sum(1 for i in p.j.propiedades if p.lug(i) and p.lug(i).tipo == "casa") >= 3),
    ("empresario", tr("Empresario"), tr("Ten tres negocios."), lambda p: sum(1 for i in p.j.propiedades if p.lug(i) and p.lug(i).tipo == "negocio") >= 3),
    ("viajero", tr("Trotamundos"), tr("Visita todas las localidades."), lambda p: all(any(b["id"] in p.j.barrios_vistos for b in m.barrios) for m in p.mapas.values())),
    ("explorador", tr("Explorador"), tr("Visita cien lugares."), lambda p: len(p.j.visitados) >= 100),
    ("cartografo", tr("Cartógraf[o|a]"), tr("Visita todos los lugares del juego."), lambda p: len(p.j.visitados) >= len(p.lugares)),
    ("coleccionista", tr("Coleccionista"), tr("Encuentra diez objetos de colección."), lambda p: len(p.j.casetes) >= 10),
    ("completista", tr("Lo tengo todo"), tr("Encuentra todos los objetos de colección."), lambda p: len(p.j.casetes) >= p.total_casetes()),
    ("pescador", tr("Lobo de mar"), tr("Pesca veinticinco peces."), lambda p: p.j.stats.get("peces", 0) >= 25),
    ("capitan", tr("Armador[|a]"), tr("Ten dos barcos."), lambda p: len(p.j.barcos) >= 2),
    ("piloto", tr("Piloto"), tr("Recorre cien kilómetros al volante."), lambda p: p.j.stats["metros_coche"] >= 100000),
    ("caminante", tr("Caminante"), tr("Recorre diez kilómetros a pie."), lambda p: p.j.stats["metros_pie"] >= 10000),
    ("ladron", tr("Manos rápidas"), tr("Roba veinticinco vehículos."), lambda p: p.j.stats["vehiculos_robados"] >= 25),
    ("taxista", tr("Taxista de toda la vida"), tr("Completa veinte servicios de trabajo."), lambda p: p.j.stats.get("servicios", 0) >= 20),
    ("campeon", tr("[Campeón|Campeona]"), tr("Gana todas las carreras."), lambda p: len(p.j.stats["carreras"]) >= len(p.datos["carreras"])),
    ("boxeador", tr("Guantes de oro"), tr("Gana cinco combates de boxeo."), lambda p: p.j.stats.get("boxeo", 0) >= 5),
    ("sicario", tr("Profesional"), tr("Cumple cinco contratos del tablón."), lambda p: p.j.stats.get("contratos", 0) >= 5),
    ("butron", tr("Butroner[o|a]"), tr("Atraca un banco."), lambda p: p.j.stats.get("atracos", 0) >= 1),
    ("forzudo", tr("En plena forma"), tr("Sube tu salud máxima a 150."), lambda p: p.j.salud_max >= 150),
    ("maestro", tr("Maestría"), tr("Sube una habilidad al nivel diez."), lambda p: any(p.nivel(h) >= 10 for h in HABILIDADES)),
    ("heroe", tr("Buen[|a] vecin[o|a]"), tr("Resuelve diez sucesos callejeros."), lambda p: p.j.stats.get("eventos", 0) >= 10),
    ("arsenal", tr("Arsenal"), tr("Ten quince armas distintas."), lambda p: len(p.j.armas) >= 15),
    ("amigo", tr("Amistad de cuatro patas"), tr("Adopta un perro."), lambda p: bool(p.j.perro)),
    ("jefe", tr("[Jefe|Jefa] de barrio"), tr("Conquista tres territorios."), lambda p: len(p.j.territorios) >= 3),
    ("amo", tr("La comarca es tuya"), tr("Conquista todos los barrios de todas las ciudades."), lambda p: len(p.j.territorios) >= sum(len(m.barrios) for m in p.mapas.values() if m.tipo == "ciudad")),
    ("buzo", tr("Cazatesoros"), tr("Encuentra cinco tesoros buceando o con el detector."), lambda p: p.j.stats.get("tesoros", 0) >= 5),
    ("memoria", tr("Memoria de elefante"), tr("Aguanta ocho rondas en la máquina de memoria de sonidos."), lambda p: p.j.stats.get("simon", 0) >= 8),
    ("inversor", tr("Lobo de la bolsa"), tr("Ten acciones por valor de 20000 euros."), lambda p: sum(n * p.precio_accion(i) for i, n in p.j.acciones.items()) >= 20000),
    # la vida honrada, la doble vida y sus consecuencias (versión 1.7.1)
    ("ficha_limpia", tr("Ficha limpia"), tr("Llega al día treinta sin una sola condena en toda la partida."), lambda p: p.dia >= 30 and not p.en_servidor and p.cfg["antecedentes"] and not p.j.stats.get("antecedentes") and not p.j.stats["detenciones"]),
    ("ejemplar", tr("Ciudadan[o|a] ejemplar"), tr("Alcanza los 90 de prestigio entre los vecinos sin antecedentes en vigor."), lambda p: p.j.ciudadania >= 90 and not p.hon_antecedentes()),
    ("doble_vida", tr("Dos caras"), tr("Ten a la vez 60 de prestigio y 50 de fama en la calle, sin antecedentes en vigor y sin que te hayan descubierto nunca."),
     lambda p: p.j.ciudadania >= 60 and p.j.reputacion >= 50 and not p.hon_antecedentes() and not p.j.stats.get("descubierto") and p.hon_nivel() > 0),
    ("gran_empresa", tr("Casa con nombre"), tr("Lleva un negocio tuyo al nivel más alto."), lambda p: any(int(e.get("nivel", 1)) >= 1 + len(p.hon_mejoras()) for e in p.j.empresa.values()) and len(p.hon_mejoras()) > 0),
    ("carrera", tr("Carrera completa"), tr("Llega al puesto más alto de un empleo fijo."), lambda p: bool(p.j.contrato) and p.hon_empleo() is not None and int(p.j.contrato.get("puesto", 0)) >= len(p.hon_empleo()["puestos"]) - 1),
    ("titulado", tr("Con todas las letras"), tr("Consigue tres títulos."), lambda p: len(p.hon_titulos()) >= 3),
    ("buen_camino", tr("El buen camino"), tr("Termina la historia del buen camino con el final honrado."), lambda p: (p.decisiones.get("_final_honrado") or {}).get("clase") == "honrado"),
    ("samaritano", tr("Buen[|a] samaritan[o|a]"), tr("Haz diez buenas acciones por la calle."), lambda p: p.j.stats.get("buenas_acciones", 0) >= 10),
]


# Las clases de suceso callejero que sabe llevar el juego; cada suceso de los datos (sección sucesos) es de una.
CLASES_SUCESO = ("objeto", "atraco", "banda")


def _rango(v, lo, hi):
    """Un [mínimo, máximo] de los datos como dos enteros, o los de serie si no vale."""
    try:
        a, b = int(v[0]), int(v[1])
        return (a, b) if a <= b else (b, a)
    except (TypeError, ValueError, IndexError, KeyError):
        return lo, hi


class Extras2:
    # -------------------------------------------------------------- habilidades
    def nivel(self, hab):
        return min(10, int(((self.j.hab.get(hab, 0.0) + 60.0 * self.cheat_growth()) / 60.0) ** 0.5))

    def ganar_xp(self, hab, n):
        antes = self.nivel(hab)
        n *= 1.0 + 0.25 * sum(1 for k in ("mod_enemigos", "mod_policia", "mod_dinero") if self.cfg[k])      # jugar más difícil enseña más deprisa
        self.j.hab[hab] = self.j.hab.get(hab, 0.0) + n
        ahora = self.nivel(hab)
        if ahora > antes:
            self.son("nivel", cat="interfaz")
            self.decir(tr('Tu habilidad de {lower} sube al nivel {ahora}.').format(lower=(HABILIDADES[hab][0].lower()), ahora=(ahora)))

    # ------------------------------------------------------------------- logros
    def comprobar_logros(self):
        for ident, nombre, desc, cond in LOGROS:
            if ident in self.j.logros:
                continue
            try:
                ok = cond(self)
            except Exception:
                ok = False
            if ok:
                self.j.logros.append(ident)
                self.son("logro", cat="interfaz")
                self.decir(tr('Logro conseguido: {nombre}. {desc}').format(nombre=(nombre), desc=(desc)))

    # -------------------------------------------------------- actualización
    def actualizar_extras(self, dt):
        self.t_logros -= dt
        if self.t_logros <= 0:
            self.t_logros = 4.0
            self.comprobar_logros()
        self._noticias(dt)
        self._eventos(dt)

    # ----------------------------------------------------------------- noticias
    def _noticias(self, dt):
        if not self.j.veh or self.app.radio.id_actual() != "noticias":
            return
        self.t_noticia -= dt
        if self.t_noticia > 0:
            return
        self.t_noticia = random.uniform(18, 28)
        self.decir(tr("El Faro Noticias. ") + self.noticia())

    def noticia(self):
        j = self.j
        s = j.stats
        ops = [
            tr('Son las {hora_txt}. ').format(hora_txt=(self.hora_txt())) + (tr("Llueve en toda la comarca: precaución en las carreteras.") if self.lluvia else tr("Cielos despejados en toda la comarca.")) + (" " + self.dia_txt() if self.dia_txt() else ""),
            tr("El Atlético Bravo empata a cero y sigue soñando con el ascenso."),
            tr("El Ayuntamiento de Puerto Bravo promete arreglar el reloj de la plaza. Otra vez."),
            tr("Los pescadores de Cala Brava denuncian que cada vez hay más botas viejas en el mar."),
            tr("El balneario de Fuentefría cuelga el cartel de completo."),
            tr("La Universidad de San Lucero investiga por qué los estudiantes duermen tan poco."),
        ]
        if s["vehiculos_robados"] > 5:
            ops.append(tr('Ola de robos de vehículos: ya van {vehiculos_robados} denuncias. La policía busca a un único sospechoso.').format(vehiculos_robados=(s['vehiculos_robados'])))
        if s.get("atracos", 0):
            ops.append(tr("Los bancos refuerzan su seguridad tras los últimos atracos."))
        if s.get("eventos", 0) > 2:
            ops.append(tr("Vecinos de la comarca hablan de una persona misteriosa que aparece cuando hay problemas y se va sin decir su nombre."))
        if j.estrellas:
            ops.append(tr("Última hora: la policía persigue a un individuo peligroso. Se recomienda no salir a la calle."))
        if "m20" in self.completadas:
            ops.append(tr("Octavio Belmonte pasa su primera semana en prisión. Sus empresas, intervenidas por la jueza."))
        elif "m10" in self.completadas:
            ops.append(tr("El empresario Octavio Belmonte niega cualquier relación con la banda de Los Calaveras."))
        if "t06" in self.completadas:
            ops.append(tr("Monteferro celebra el fin de la huelga minera con una verbena en la plaza."))
        if "s06" in self.completadas:
            ops.append(tr("San Lucero respira tranquila tras la caída de la banda de Los Lagartos."))
        if s.get("peces", 0) > 10:
            ops.append(tr("La lonja registra capturas récord esta semana."))
        return random.choice(ops)

    # --------------------------------------------------------- sucesos callejeros
    def _punto_cercano(self, minimo, maximo, acera=True):
        x, y = self.pos()
        for _ in range(30):
            a = random.uniform(0, 2 * math.pi)
            d = random.uniform(minimo, maximo)
            px, py = x + math.sin(a) * d, y + math.cos(a) * d
            s = self.mundo.superficie(px, py)
            if s == "acera" or (not acera and s not in ("pared", "fuera", "calzada", "agua")):
                return px, py
        return None

    def _fin_evento(self, texto=None, premio=0):
        ev = self.evento
        self.evento = None
        self.t_evento = random.uniform(100, 220)
        if not ev:
            return
        for p in ev.get("personas", []):
            if p in self.personas and (not p.muerto or p.tipo == "civil"):
                p.tag = None
                if p.tipo != "civil":
                    self.personas.remove(p)
        o = ev.get("objeto")
        if o is not None and o in self.objetos:
            if o.canal:
                o.canal.parar()
            self.objetos.remove(o)
        if premio:
            self.j.stats["eventos"] = self.j.stats.get("eventos", 0) + 1
            self.dar_dinero(premio)
            self.cambiar_ciudadania(2.0)
        if texto:
            self.decir(texto)

    def sucesos_posibles(self):
        """Los sucesos callejeros que pueden salir aquí (issue 41): los de la sección sucesos de los datos, donde un mod añade
        los suyos, menos los que el jugador ha quitado en Opciones, los que esta localidad no admite (su campo sucesos) y
        los que son de otras localidades (el campo mapas del suceso)."""
        apagados = set(self.cfg["sucesos_apagados"] or [])
        admite = getattr(self.mundo, "sucesos", None)
        out = []
        for s in self.datos.get("sucesos") or []:
            if not isinstance(s, dict) or s.get("clase") not in CLASES_SUCESO or s.get("id") in apagados:
                continue
            if admite is not None and s.get("id") not in admite:
                continue
            if s.get("mapas") and self.mundo.id not in s["mapas"]:
                continue
            out.append(s)
        return out

    def _eventos(self, dt):
        j = self.j
        ev = self.evento
        if ev:
            ev["t"] -= dt
            s = ev.get("suceso") or {}
            malos = [p for p in ev.get("personas", []) if p.tipo == "enemigo"]
            if ev.get("clase", ev["tipo"]) in ("atraco", "banda") and malos and all(p.muerto for p in malos):
                self._fin_evento(s.get("gracias") or tr("Los vecinos, agradecidos, hacen una colecta para ti."), ev["premio"])
            elif ev.get("clase", ev["tipo"]) in ("objeto", "maletin") and ev["objeto"] not in self.objetos:
                self.j.stats["eventos"] = self.j.stats.get("eventos", 0) + 1
                self._fin_evento()
            elif ev["t"] <= 0:
                self._fin_evento(s.get("pierdes") or tr("Ya no hay nada que hacer: el suceso ha terminado."))
            return
        if self.mision or self.trabajo or self.guerra or j.estrellas or self.mundo.tipo in ("mar", "isla") or self.transicion or not self.cfg["sucesos"]:
            return
        self.t_evento -= dt
        if self.t_evento > 0:
            return
        posibles = self.sucesos_posibles()
        if not posibles:
            self.t_evento = 60
            return
        s = random.choices(posibles, weights=[max(0.0, float(x.get("peso", 1) or 0)) or 0.01 for x in posibles])[0]
        pos = self._punto_cercano(45, 80)
        if pos is None:
            self.t_evento = 20
            return
        x, y = pos
        self.son(s.get("sonido") or "evento", cat="interfaz")
        tipo = s["clase"]
        lo, hi = _rango(s.get("premio"), 150, 400)
        aviso = str(s.get("aviso") or s.get("nombre") or "")
        if tipo == "objeto":
            o = Objeto("dinero", str(s.get("objeto") or s.get("nombre") or tr("Maletín perdido")), x, y)
            o.valor = random.randint(lo, hi)
            self.objetos.append(o)
            self.evento = {"tipo": s.get("id", tipo), "clase": tipo, "t": float(s.get("duracion", 150)), "objeto": o, "suceso": s}
            self.decir(aviso.replace("{situar}", self.situar(x, y, str(s.get("situar") or tr("Está")))))
            return
        personas = []
        if tipo == "atraco":
            v = Persona("civil", x, y, str(s.get("victima") or tr("Víctima del atraco")))
            v.estado = "quieto"
            v.tag = "evento"
            personas.append(v)
        a, b = _rango(s.get("cuantos"), 1 if tipo == "atraco" else 2, 1 if tipo == "atraco" else 3)
        n = max(1, min(6, random.randint(a, b)))
        clase = str(s.get("enemigo") or ("atracador" if tipo == "atraco" else "pandillero_calle"))
        nombre = str(s.get("nombre_enemigo") or (tr("Atracador") if tipo == "atraco" else tr("Pandillero")))
        armas = [x for x in (s.get("armas") or ["navaja", "pistola", "bate"]) if x in self.armas_d] or ["navaja"]
        for _ in range(n):
            f = G.enemigo(G.grupo(clase, tipo=nombre, arma=random.choice(armas), salud=int(s.get("salud", 55))))
            e = G.vestir(Persona("enemigo", *self.mundo.punto_libre(x + random.uniform(-3, 3), y + random.uniform(-3, 3)), f["nombre"]), f)
            e.hostil = True
            e.estado = "ataca"
            e.activo = False
            e.tag = "evento"
            e.agresor = True                                     # están atracando o amenazando a alguien: pararles los pies no es delito
            personas.append(e)
        self.personas += personas
        self.evento = {"tipo": s.get("id", tipo), "clase": tipo, "t": float(s.get("duracion", 110)), "personas": personas, "premio": random.randint(lo, hi) * n, "suceso": s}
        if tipo == "atraco":
            self.son("grito", xy=(x, y), ref=10, maxd=120)
        self.decir(aviso.replace("{situar}", self.situar(x, y, str(s.get("situar") or tr("Ocurre")))))

    # ------------------------------------------------------ encargos repetibles
    def _empezar_repetible(self, m):
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        m["repetible"] = True
        m.setdefault("requiere", [])
        self.iniciar_mision(m)

    def empezar_contrato(self, l):
        dest = self._destino_azar(150, 900, l)
        n = min(5, 1 + self.j.stats.get("contratos", 0) // 2)
        quien = random.choice(G.lista("apodos"))
        armas = ["pistola", "pistola", "subfusil", "escopeta", "navaja"]
        objetivo = dict(G.grupo("objetivo_contrato", arma="pistola", salud=95), tipo=tr('Objetivo, {quien}').format(quien=(quien)))
        # con escolta numerosa, a veces parte de ella llega en un vehículo
        moto = G.tipo_enemigo("escolta_motorizada") if n >= 3 and random.random() < 0.5 else None
        en_coche = min(n - 1, int(moto.get("ocupantes", 3) or 3)) if moto and moto.get("vehiculo") in self.modelos and not self.en_servidor else 0
        escolta = [G.grupo("guardaespaldas", tipo=tr("Guardaespaldas"), arma=random.choice(armas), salud=70) for _ in range(n - en_coche)]
        if en_coche:
            escolta.append({"n": en_coche, "clase": "escolta_motorizada"})
        self._empezar_repetible({
            "id": "contrato", "titulo": tr('Contrato: {quien}').format(quien=(quien)), "lugar": l.id, "contador": "contratos",
            "pasos": [
                {"tipo": "eliminar", "lugar": dest.id, "texto": tr('El objetivo, {quien}, está en {nombre} con {n} guardaespaldas. Ve allí y cumple el contrato.').format(quien=(quien), nombre=(dest.nombre), n=(n))
                 + (tr(" Parte de la escolta ronda la zona en un vehículo.") if en_coche else ""),
                 "enemigos": [objetivo] + escolta},
                {"tipo": "ir", "lugar": l.id, "texto": tr('Contrato cumplido. Vuelve a {nombre} a cobrar.').format(nombre=(l.nombre))}],
            "recompensa": {"dinero": 600 + 380 * n}})

    def empezar_atraco_banco(self, l, golpe=None):
        caja = self.caja_de_local(l) or {"dinero": random.randint(7000, 13000), "guardias": 5, "busqueda": 4}
        self.atracadas["banco:" + l.id] = self.dia
        n = max(1, int(caja["guardias"]) or 5)
        armados = n * 2 // 5                                     # de cada cinco vigilantes, dos llevan subfusil
        m = {
            "id": "atraco_banco", "titulo": tr('Atraco a {nombre}').format(nombre=(l.nombre)), "lugar": l.id, "contador": "atracos",
            "pasos": [
                {"tipo": "eliminar", "lugar": l.id, "ya": True, "texto": tr("¡Esto es un atraco! Acaba con los vigilantes de seguridad."),
                 "enemigos": [g for g in (G.grupo(caja.get("guardia") or "vigilante", n - armados, tipo=tr("Vigilante de seguridad"), arma="pistola", salud=80),
                                          G.grupo("vigilante_armado", armados, tipo=tr("Vigilante de seguridad"), arma="subfusil", salud=85)) if g["n"] > 0]},
                {"tipo": "recoger", "lugar": l.id, "objeto": tr("Botín de la cámara acorazada"), "texto": tr("La cámara acorazada está abierta. Recoge el botín.")},
                {"tipo": "policia", "nivel": max(1, int(caja["busqueda"]) or 4), "texto": tr("¡Ha saltado la alarma silenciosa! Despista a la policía para quedarte el botín.")}],
            "recompensa": {"dinero": int(caja["dinero"])}}
        if golpe:
            self.golpe_adaptar(m, l, golpe)                      # preparado con la banda: la cámara tarda en abrirse y cada uno hace su papel
        self._empezar_repetible(m)

    def caja_de_local(self, l):
        """Lo que hay hoy en la caja de un local y quién la guarda, según los datos (sección «Caja de los locales»).

        Devuelve None si ese tipo de local no tiene caja que llevarse, o un diccionario con: «dinero», lo que hay hoy (la
        misma cifra todo el día, distinta cada día, cada local y cada partida); «guardias», cuántos la guardan; «guardia»,
        su tipo de enemigo; «busqueda», el nivel de búsqueda que cae al atracarla; y «enemigos», los grupos ya listos para
        un paso «eliminar» de una misión (vacío si no hay guardia)."""
        c = G.caja_local(getattr(l, "tipo", l))
        if c is None:
            return None
        rng = random.Random(f"caja:{self.j.semilla}:{self.dia}:{getattr(l, 'id', l)}")
        c = dict(c, dinero=rng.randint(c["minimo"], c["maximo"]))
        c["enemigos"] = [{"n": c["guardias"], "clase": c["guardia"]}] if c["guardias"] and c["guardia"] else []
        return c

    def empezar_encargo_coche(self, l):
        ids = [i for i in MODELOS_ENCARGO if i in self.modelos]
        mo = self.modelos[random.choice(ids)]
        donde = self._destino_azar(150, 800, l)
        self._empezar_repetible({
            "id": "encargo_coche", "titulo": tr('Encargo: {nombre}').format(nombre=(mo['nombre'])), "lugar": l.id, "contador": "encargos",
            "pasos": [
                {"tipo": "robar", "modelo": mo["id"], "lugar": donde.id, "nombre": tr('{nombre} de encargo').format(nombre=(mo['nombre'])), "busqueda": 1,
                 "texto": tr('Un cliente quiere un {nombre}. Hay uno aparcado junto a {nombre2}. Róbalo.').format(nombre=(mo['nombre']), nombre2=(donde.nombre))},
                {"tipo": "entregar", "lugar": l.id, "salud_min": 50, "texto": tr('Lleva el vehículo a {nombre} en buen estado.').format(nombre=(l.nombre))}],
            "recompensa": {"dinero": int(mo["valor"] * 1.5) + 350}})

    def combate_def(self, ident):
        return next((c for c in self.datos.get("combates", []) if c.get("id") == ident), None)

    def empezar_combate(self, l, c):
        """Un combate del gimnasio, definido en los datos: uno o varios asaltos seguidos, solo con los puños."""
        # Cada victoria sube el premio y la dureza del rival, hasta un tope (victorias_tope, en los datos): después, ya no.
        g = min(self.j.stats.get(c["id"], 0), max(0, int(c.get("victorias_tope", 10))))
        asaltos = max(1, int(c.get("asaltos", 1)))
        nombres = list(c.get("rivales") or [tr("el Rival")])
        rivales = random.sample(nombres, asaltos) if len(nombres) >= asaltos else [random.choice(nombres) for _ in range(asaltos)]
        self.j.arma = "punos"
        pasos = []
        for n, rival in enumerate(rivales):
            if asaltos == 1:
                entrada = tr("¡Suena la campana!")
            else:
                entrada = tr("¡Se cierra la jaula! Primer asalto.") if n == 0 else tr("Último asalto: el combate estelar.") if n == asaltos - 1 else tr('Asalto {v}, sin descanso.').format(v=(n + 1))
            pasos.append({"tipo": "eliminar", "lugar": l.id, "ya": True,
                          "texto": tr('{entrada} Tu rival es {rival}. Pulsa Q para fijarlo y Espacio para golpear.').format(entrada=(entrada), rival=(rival)),
                          "enemigos": [{"n": 1, "tipo": rival[0].upper() + rival[1:], "arma": "punos", "deportivo": bool(c.get("deportivo", True)),
                                        "salud": int(c.get("salud", 60)) + int(c.get("salud_asalto", 0)) * n + int(c.get("salud_victoria", 20)) * g}]})
        self._empezar_repetible({"id": c["id"], "titulo": tr('{nombre} contra {v}').format(nombre=(c['nombre']), v=(rivales[0])) if asaltos == 1 else c["nombre"], "lugar": l.id, "contador": c["id"],
                                 "pasos": pasos, "solo_punos": True, "recompensa": {"dinero": int(c.get("premio", 150)) + int(c.get("premio_victoria", 100)) * g}})
        self.son("campana_ring", cat="interfaz")

    def empezar_boxeo(self, l):
        self.empezar_combate(l, self.combate_def("boxeo") or {"id": "boxeo", "nombre": tr("Combate de boxeo")})

    def empezar_mma(self, l):
        self.empezar_combate(l, self.combate_def("mma") or {"id": "mma", "nombre": tr("Velada de artes marciales mixtas"), "asaltos": 3})

    # --------------------------------------------------------------- servicios
    def plaza_cercana(self):
        """Hueco junto al bordillo de la calle más cercana al jugador."""
        x, y = self.pos()
        return self.mundo.plaza_en(x, y)
