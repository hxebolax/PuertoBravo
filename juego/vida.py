"""Personajes, prestigio ciudadano y vida honrada: empleos con ascensos, jornadas, cursos y voluntariado.

El juego se puede jugar como una persona de bien o como un delincuente. El prestigio entre los
vecinos sube con el trabajo honrado y baja con los delitos; la fama en la calle va por otro lado.
"""
from .i18n import tr
import math
import random
import re

from . import genero, registro

PROPIO = "propio"            # el id del personaje que se hace el jugador
MAX_NOMBRE = 20
PUNTOS = 8                   # niveles de habilidad que reparte quien se hace su personaje
MAX_NIVEL = 5                # y lo más que puede poner en una sola
# Con qué empieza un personaje propio, a elegir una: igual de fuertes que las de los personajes de la lista.
VENTAJAS = [
    ("ninguna", tr("Ninguna"), tr("Empiezas con lo puesto y un botiquín. Para quien quiere la partida más cuesta arriba."), {}),
    ("ahorros", tr("Ahorros"), tr("Empiezas con ochocientos euros."), {"dinero": 800}),
    ("fortaleza", tr("Fortaleza"), tr("Empiezas con más salud, veinte puntos más, y dos botiquines."), {"salud_max": 120, "botiquines": 2}),
    ("manitas", tr("Manos rápidas"), tr("Empiezas con tres juegos de ganzúas, para abrir vehículos sin romper el cristal."), {"ganzuas": 3}),
    ("navaja", tr("Una navaja en el bolsillo"), tr("Empiezas con una navaja y dos botiquines."), {"arma": "navaja", "botiquines": 2}),
    ("vecinos", tr("Don de gentes"), tr("Empiezas con buen ánimo, algo de fama y el aprecio de los vecinos: cobras más en los trabajos honrados "
                                 "y la policía te pasa por alto las faltas pequeñas."), {"animo": 75, "reputacion": 10, "ciudadania": 45}),
]


def limpiar_nombre(texto):
    """Un nombre escrito por el jugador, sin nada raro: letras, espacios, guiones y apóstrofos, con la primera en mayúscula."""
    t = "".join(c for c in str(texto or "") if c.isalpha() or c in " -'")
    t = " ".join(t.split())[:MAX_NOMBRE].strip(" -'")
    return t[:1].upper() + t[1:] if t else ""


def personaje_propio(nombre, apellido="", gen="h", niveles=None, ventaja="ninguna", voz="dani", dicho=""):
    """El diccionario de un personaje hecho por el jugador, ya saneado: es lo que recibe aplicar_personaje."""
    pj = {"id": PROPIO, "nombre": limpiar_nombre(nombre) or tr("Dani"), "apellido": limpiar_nombre(apellido), "genero": gen if gen in genero.GENEROS else "h",
          "botiquines": 1, "ventaja": ventaja, "voz": voz if voz in ("dani", "alex", "sam", "cris") else "dani", "dicho": limpiar_nombre(dicho)}
    quedan = PUNTOS
    for h in HAB_NOMBRE:
        n = max(0, min(MAX_NIVEL, quedan, int((niveles or {}).get(h, 0))))
        quedan -= n
        if n:
            pj[h] = n
    pj.update(next((v[3] for v in VENTAJAS if v[0] == ventaja), {}))
    return pj


RANGOS = [tr("aprendiz"), tr("oficial"), tr("veteran[o|a]"), tr("maestr[o|a]"), tr("leyenda")]      # solo se dicen
HAB_NOMBRE = {"conduccion": tr("conducción"), "punteria": tr("puntería"), "resistencia": tr("resistencia"), "pesca": tr("pesca")}
# Las jornadas de trabajo sin vehículo están en los datos (vida.json, jornadas).


class Vida:
    # ----------------------------------------------------------------- tarifas
    def precio(self, clave, defecto):
        """El precio de una tarifa del juego (vida.json, tarifas), que un mod puede cambiar. Si no está, o no es un número, `defecto`.

        Se busca en un índice por identificador, que se rehace solo cuando cambia la lista de tarifas. El índice guarda cada
        tarifa, no su precio: si alguien le cambia el precio a una, se nota al momento."""
        lista = self.datos.get("tarifas")
        cache = self.__dict__.get("_tarifas")
        if cache is None or cache[0] is not lista or cache[1] != len(lista or ()):
            cache = (lista, len(lista or ()), {t["id"]: t for t in (lista or ()) if isinstance(t, dict) and t.get("id")})
            self._tarifas = cache
        valor = cache[2].get(clave, {}).get("precio")
        return valor if isinstance(valor, (int, float)) and not isinstance(valor, bool) else defecto

    # -------------------------------------------------------------- personajes
    def personajes(self):
        return self.datos.get("personajes", [])

    def aplicar_personaje(self, ident):
        """Pone al protagonista como el personaje elegido. `ident` es el id de uno de la lista o un diccionario: el de un
        personaje hecho por el jugador (id "propio"), o {"id": ..., "genero": ...} para uno de la lista con el género elegido."""
        j = self.j
        propio = dict(ident) if isinstance(ident, dict) else {}
        if propio:
            ident = propio.get("id")
        pj = next((x for x in self.personajes() if x["id"] == ident), None)
        if pj is None and propio.get("id") == PROPIO:
            pj = {"id": PROPIO}
        if pj is None:
            pj = (self.personajes() or [{"id": "dani", "nombre": tr("Dani"), "apellido": tr("Roca")}])[0]
        pj = dict(pj)
        fijo = pj.get("genero")                          # un personaje con el género escrito en sus datos no cambia
        pj.update(propio)
        if fijo in genero.GENEROS:
            pj["genero"] = fijo
        j.personaje = pj["id"]
        j.nombre = str(pj.get("nombre") or tr("Dani"))[:MAX_NOMBRE]
        j.apellido = str(pj.get("apellido") or ("" if pj["id"] == PROPIO else tr("Roca")))[:MAX_NOMBRE]
        j.genero = genero.poner(pj.get("genero"))
        j.voz = pj.get("voz") if pj.get("voz") in ("dani", "alex", "sam", "cris") else "dani"
        j.nombre_dicho = limpiar_nombre(pj.get("dicho", "")) if pj["id"] == PROPIO else ""
        if pj["id"] == PROPIO:
            registro.ocultar(j.nombre)                   # un nombre escrito por el jugador no se anota en el registro
            if j.apellido:
                registro.ocultar(j.apellido)
        j.dinero = int(pj.get("dinero", j.dinero))
        j.salud_max = float(pj.get("salud_max", 100))
        j.salud = j.salud_max
        j.animo = float(pj.get("animo", j.animo))
        j.reputacion = float(pj.get("reputacion", 0))
        j.ciudadania = float(pj.get("ciudadania", 20))
        j.objetos["botiquin"] = int(pj.get("botiquines", 1))
        j.objetos["ganzua"] = int(pj.get("ganzuas", 0))
        for h in HAB_NOMBRE:
            j.hab[h] = 60.0 * int(pj.get(h, 0)) ** 2
        if pj.get("arma") in self.armas_d:
            a = self.armas_d[pj["arma"]]
            j.armas[a["id"]] = {"cargador": a.get("cargador", 0), "reserva": int(pj.get("balas", a.get("balas", 0)) or 0)}

    def txt(self, texto):
        """Pone el nombre del personaje elegido en los textos de la historia, escritos para Dani Roca."""
        j = self.j
        if not isinstance(texto, str) or (j.nombre == "Dani" and j.apellido == "Roca") or "Dani" not in texto:
            return texto
        texto = texto.replace("Dani Roca", f"{j.nombre} {j.apellido}".strip())
        return re.sub(r"\bDani\b", j.nombre, texto)

    # ------------------------------------------------------ prestigio ciudadano
    def ciudadania_txt(self):
        c = self.j.ciudadania
        return tr("los vecinos te evitan") if c < 10 else tr("eres [un vecino|una vecina] más") if c < 40 else tr("los vecinos te aprecian") if c < 75 else tr("eres [un ciudadano|una ciudadana] ejemplar")

    def cambiar_ciudadania(self, n):
        antes = self.ciudadania_txt()
        self.j.ciudadania = max(0.0, min(100.0, self.j.ciudadania + n))
        ahora = self.ciudadania_txt()
        if ahora != antes:
            self.son("prestigio" if n > 0 else "animo_baja", cat="interfaz")
            self.decir(tr('Cambia cómo te ven en el barrio: {ahora}.').format(ahora=(ahora)))

    # ------------------------------------------------------------------ empleos
    def servicios_de(self, tipo):
        return int(self.j.stats.get("serv_" + tipo, 0))

    def rango(self, tipo):
        return min(len(RANGOS) - 1, self.servicios_de(tipo) // 8)

    def mult_trabajo(self, tipo):
        c = self.j.ciudadania
        return (1.0 + 0.12 * self.rango(tipo)) * (1.2 if c >= 75 else 1.1 if c >= 40 else 1.0)

    def servicio_hecho(self, tipo, nombre):
        antes = self.rango(tipo)
        self.j.stats["serv_" + tipo] = self.servicios_de(tipo) + 1
        self.cambiar_ciudadania(0.5)
        if tipo != "jornada":
            self.hon_turno("oficio:" + str(tipo))
        if self.rango(tipo) > antes:
            self.son("ascenso", cat="interfaz")
            self.decir(tr('¡Ascenso! Ya eres {nombre} {v}: cobras un {v2} por ciento más.').format(nombre=(nombre), v=(RANGOS[self.rango(tipo)]), v2=(12 * self.rango(tipo))))

    def jornada(self, clave, nombre, paga, salud):
        j = self.j
        if j.jornada_dia == self.dia:
            self.app.son("error")
            self.decir(tr("Hoy ya has trabajado una jornada. Vuelve mañana."), True)
            return
        if j.estrellas:
            self.app.son("error")
            self.decir(tr("Con la policía buscándote no te contratan."), True)
            return
        j.jornada_dia = self.dia
        cobro = int(paga * self.mult_trabajo("jornada"))
        self.pasar_horas(8)
        j.salud = max(10.0, j.salud + salud)
        self.son("jornada", cat="interfaz")
        self.dar_dinero(cobro)
        self.servicio_hecho("jornada", "trabajador")
        self.cambiar_ciudadania(1.0)
        self.cambiar_animo(-2)
        self.decir(tr('{nombre}: ocho horas de trabajo y {cobro} euros. Son las {hora_txt}.').format(nombre=(nombre), cobro=(cobro), hora_txt=(self.hora_txt())), True)
        self.hon_turno("jornada:" + str(clave))                  # si es de tu contrato fijo, cuenta como turno

    def jornada_vendedor(self, l):
        """Una jornada vendiendo coches en un concesionario: sueldo fijo y comisión por cada venta."""
        j = self.j
        if j.jornada_dia == self.dia:
            self.app.son("error")
            self.decir(tr("Hoy ya has trabajado una jornada. Vuelve mañana."), True)
            return
        if j.estrellas:
            self.app.son("error")
            self.decir(tr("Con la policía buscándote no te contratan."), True)
            return
        j.jornada_dia = self.dia
        # se vende más con buena fama entre los vecinos, con experiencia y yendo bien arreglado
        prob = min(0.85, 0.22 * self.mult_trabajo("jornada") + 0.02 * min(10, j.stats.get("coches_vendidos", 0)) + (0.1 if j.accesorios else 0.0)
                   + __import__("juego.vestuario", fromlist=["x"]).bono_vendedor(self)      # y más con ropa elegante (vestuario.py)
                   - (__import__("juego.necesidades", fromlist=["x"]).AJ("vendedor_sucio") / 100.0 if self.sucio() else 0.0))      # y menos sin ducharte
        marcas = l.get("modelos")
        modelos = [mo for mo in self.datos["vehiculos"] if mo.get("precio") and not mo.get("barco") and (not marcas or mo["id"] in marcas)]
        vendidos = [random.choice(modelos) for _ in range(4) if modelos and random.random() < prob]
        comision = sum(int(mo["precio"] * 0.02) for mo in vendidos)
        sueldo = int(self.precio("sueldo_vendedor", 90) * self.mult_trabajo("jornada"))
        self.pasar_horas(8)
        self.son("jornada", cat="interfaz")
        self.dar_dinero(sueldo + comision)
        j.stats["coches_vendidos"] = j.stats.get("coches_vendidos", 0) + len(vendidos)
        self.servicio_hecho("jornada", "trabajador")
        self.cambiar_ciudadania(1.0)
        self.cambiar_animo(2 if vendidos else -2)
        if vendidos:
            nombres = ", ".join(mo["nombre"] for mo in vendidos)
            self.decir(tr('Ocho horas en la exposición. Has vendido {len}: {nombres}. Sueldo de {sueldo} euros y {comision} de comisión. Son las {hora_txt}.').format(len=(len(vendidos)), nombres=(nombres), sueldo=(sueldo), comision=(comision), hora_txt=(self.hora_txt())), True)
        else:
            self.decir(tr('Ocho horas en la exposición y nadie se ha decidido. Cobras el sueldo, {sueldo} euros. Son las {hora_txt}.').format(sueldo=(sueldo), hora_txt=(self.hora_txt())), True)

    def aspecto_txt(self):
        """Lo que llevas puesto: la ropa y los complementos."""
        j = self.j
        t = tr('Llevas puesto: {ropa}').format(ropa=(j.ropa))
        if getattr(j, "calzado", "") and j.calzado != "zapatillas de calle":      # las de serie no se dicen
            t += f", {j.calzado}"
        if j.accesorios:
            cosas = [n.lower() for n in j.accesorios.values()]
            t += tr(", con ") + (", ".join(cosas[:-1]) + tr(" y ") + cosas[-1] if len(cosas) > 1 else cosas[0])
        return t + "."

    def curso(self, hab):
        j = self.j
        if j.curso_dia == self.dia:
            self.app.son("error")
            self.decir(tr("Ya has ido a clase hoy. La cabeza no da para más."), True)
            return
        if self.nivel(hab) >= 10:
            self.decir(tr("Ya no pueden enseñarte nada más: tienes el nivel máximo."), True)
            return
        if not self.pagar(self.precio("curso", 250)):
            return
        j.curso_dia = self.dia
        self.pasar_horas(4)
        self.son("diploma", cat="interfaz")
        self.decir(tr('Cuatro horas de clase de {v}. Son las {hora_txt}.').format(v=(HAB_NOMBRE[hab]), hora_txt=(self.hora_txt())), True)
        self.ganar_xp(hab, 320)
        self.cambiar_ciudadania(1.0)

    def donar(self, cantidad):
        if not self.pagar(cantidad):
            return
        self.son("donativo", cat="interfaz")
        self.cambiar_ciudadania(cantidad / 40.0)
        self.cambiar_animo(2 + cantidad / 100.0)
        self.j.stats["donado"] = self.j.stats.get("donado", 0) + cantidad
        self.decir(tr('Donas {cantidad} euros. Te dan las gracias de corazón.').format(cantidad=(cantidad)), True)

    def voluntariado(self):
        j = self.j
        if j.voluntario_dia == self.dia:
            self.decir(tr("Hoy ya has echado una mano. Vuelve mañana."), True)
            return
        j.voluntario_dia = self.dia
        self.pasar_horas(4)
        self.son("lugar_ong", cat="interfaz")
        j.stats["voluntariado"] = j.stats.get("voluntariado", 0) + 1
        self.cambiar_ciudadania(3.0)
        self.cambiar_animo(6)
        self.decir(tr('Pasas cuatro horas sirviendo comidas. Sales cansad[o|a] y content[o|a]. Son las {hora_txt}.').format(hora_txt=(self.hora_txt())), True)

    def vehiculo_de_trabajo_cercano(self, tipo):
        """Lugar de este mapa que tiene siempre aparcado un vehículo de ese oficio."""
        modelos = {m["id"] for m in self.datos["vehiculos"] if m.get("trabajo") == tipo}
        x, y = self.pos()
        ops = [l for l in self.mundo.lugares.values() if l.get("vehiculo") in modelos]
        return min(ops, key=lambda l: math.hypot(l.x - x, l.y - y)) if ops else None

    # --------------------------------------------------------------- interiores
    def entrar_interior(self, l):
        """Al entrar en un local: la puerta y su ambiente de fondo mientras estés dentro."""
        self.salir_interior(silencio=True)
        self._local = l                                          # el comercio donde estás: si te aprecian, te fían
        self.son("puerta_entrar", cat="interfaz", vol=0.7)
        self.interior = self.mez.sonar(l.sonido, bucle=True, cat="interfaz", vol=0.22)
        # Al recorrer un local el oyente está dentro; la calle entra por la puerta.
        (ax, ay), _ = self.mundo.ancla(l.x, l.y)
        dx, dy = ax - l.x, ay - l.y
        norma = max(1., math.hypot(dx, dy))
        self.mez.puerta_interior = (l.x + 2 * dx / norma, l.y + 2 * dy / norma)
        self.mez.entorno = "nave" if l.tipo in ("taller", "desguace", "gimnasio") else "interior"
        if self.lluvia:
            self.lluvia_interior = self.mez.sonar(self.mez.capa("lluvia_chapa", "lluvia"), bucle=True, cat="interfaz", vol=.23)
            self.lluvia_interior.grupo = "ambiente"
            self.lluvia_interior.velo = .65
        self.hilo_musical(l)

    def salir_interior(self, silencio=False):
        self._local = None
        self.mez.puerta_interior = None
        if getattr(self, "lluvia_interior", None):
            self.lluvia_interior.parar()
            self.lluvia_interior = None
        c = getattr(self, "interior", None)
        if c is not None:
            c.parar()
            self.interior = None
            self.fin_hilo_musical()
            if not silencio:
                self.son("puerta_salir", cat="interfaz", vol=0.6)
