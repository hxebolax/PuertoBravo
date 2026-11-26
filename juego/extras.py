"""Actividades libres: pesca, atracos a peatones, guardaespaldas, sirenas y lotería."""
from .i18n import tr
import math
import random

from . import mundo as M
from .entidades import Persona

# Las aguas donde se pesca (issue 41). Un punto de pesca dice la suya en «agua»; un pez, en «aguas», dónde vive, y en
# «mapas», si solo vive en unas localidades. Un pez sin ellas pica en cualquier sitio, como antes de la 1.7.6.
AGUAS = (("mar", tr("Mar")), ("rio", tr("Río")), ("lago", tr("Lago o laguna")))


def agua_de(lugar, mundo):
    """Qué agua es la de un punto de pesca o un embarcadero: la que diga su campo «agua»; sin él, el mar en el mapa del mar,
    el río si suena a río, y si no, el mar, que es lo que había antes."""
    a = lugar.get("agua") if lugar is not None else None
    if a in dict(AGUAS):
        return a
    if mundo.tipo == "mar":
        return "mar"
    return "rio" if lugar is not None and lugar.get("sonido") == "lugar_rio" else "mar"


def peces_de(peces, agua, mapa):
    """Los peces que pican en esa agua y en esa localidad. Si ninguno, todos, para que siempre pique algo."""
    def vale(p):
        aguas, mapas = p.get("aguas") or [], p.get("mapas") or []
        return (not aguas or agua in aguas) and (not mapas or mapa in mapas)
    return [p for p in peces if vale(p)] or list(peces)


class Extras:
    # ------------------------------------------------------------------ pesca
    def empezar_pesca(self, desde_muelle=False, agua=None):
        """Lanza el anzuelo. «agua»: mar, río o lago (AGUAS), que decide qué peces pican; sin ella, el mar."""
        j = self.j
        if self.pesca:
            self.pesca = None
            self.son("carrete", vol=0.5)
            self.decir(tr("Recoges el sedal."), True)
            return
        if j.veh and abs(j.veh.vel) > 1.5:
            self.decir(tr("Detén el barco para pescar."), True)
            return
        self.pesca = {"fase": "espera", "t": random.uniform(3, 10) * (1 - 0.05 * self.nivel("pesca")), "muelle": desde_muelle, "agua": agua or "mar", "mapa": self.mundo.id, "x": self.pos()[0], "y": self.pos()[1]}
        self.son("pesca_lanzar", vol=0.7)
        self.decir(tr("Lanzas el anzuelo. Cuando oigas que pican, pulsa Espacio enseguida. No te muevas."), True)

    def actualizar_pesca(self, dt):
        ps = self.pesca
        x, y = self.pos()
        if math.hypot(x - ps["x"], y - ps["y"]) > 4:
            self.pesca = None
            self.decir(tr("Al moverte pierdes el sedal."))
            return
        ps["t"] -= dt
        if ps["t"] > 0:
            return
        if ps["fase"] == "espera":
            ps["fase"] = "pica"
            ps["t"] = 1.3
            self.son("pez_pica", vol=0.9, cat="interfaz")
            self.app.vibrar(0.3, 1.0, 500)
        else:
            self.pesca = None
            self.son("salpicadura", vol=0.5)
            self.decir(tr("Se te ha escapado. Pulsa P para lanzar otra vez."))

    def tirar_pesca(self):
        ps = self.pesca
        if ps["fase"] != "pica":
            self.pesca = None
            self.son("carrete", vol=0.5)
            self.decir(tr("Has tirado antes de tiempo y espantas a los peces."), True)
            return
        self.pesca = None
        peces = peces_de(self.datos.get("peces") or [{"nombre": tr("Sardina"), "valor": 5, "peso": 10}], ps.get("agua", "mar"), ps.get("mapa"))
        if ps["muelle"]:
            peces = [p for p in peces if p.get("valor", 0) <= 40] or peces
        pez = random.choices(peces, weights=[p.get("peso", 1) for p in peces])[0]
        self.son("carrete", vol=0.6)
        self.son("salpicadura", vol=0.6)
        if pez.get("valor", 0) <= 0:
            self.decir(tr('Sacas {nombre}. No vale nada.').format(nombre=(pez['nombre'])), True)
            return
        self.j.pescado.append({"nombre": pez["nombre"], "valor": int(pez["valor"] * random.uniform(0.8, 1.3) * (1 + 0.05 * self.nivel("pesca")))})
        self.ganar_xp("pesca", 25)
        self.j.stats["peces"] = self.j.stats.get("peces", 0) + 1
        self.decir(tr('¡Has pescado {nombre}! Llevas {len} capturas. Véndelas en una pescadería o en la lonja.').format(nombre=(pez['nombre']), len=(len(self.j.pescado))), True)

    # ------------------------------------------------------ atracar peatones
    def atracar_peaton(self):
        j = self.j
        if j.veh:
            return
        if self.sv_atracar_cerca():                              # en un servidor: el que tienes al lado es otro jugador
            return
        cerca = [p for p in self.personas if p.tipo == "civil" and not p.muerto and p.dist(j.x, j.y) < 4.5]
        if self.modo_adulto() and self.arma()["id"] == "punos" and self.carga() > 0:
            self.ofrecer_mercancia()
            return
        if not cerca:
            self.decir(tr("No hay ningún peatón a tu lado."), True)
            return
        if self.arma()["id"] == "punos":
            self.decir(tr("Para atracar a alguien tienes que empuñar un arma."), True)
            return
        p = min(cerca, key=lambda p: p.dist(j.x, j.y))
        if getattr(p, "atracado", False):
            self.decir(tr("A ese ya le has quitado todo."), True)
            return
        p.atracado = True
        self.sv_peaton_atracado(p)
        p.provocado = True                                       # has empezado tú: si se revuelve, lo suyo no es una agresión
        self.asustar(p, 14, grito=1.0, callar=True)
        if random.random() < 0.12:
            p.hostil = True
            p.estado = "ataca"
            p.arma = "navaja"
            p.tipo = "enemigo"
            p.nombre = tr("Peatón armado")
            self.decir(tr("¡Este no se deja! Saca una navaja."), True)
            return
        botin = random.randint(5, 70)
        self.hon_negro(botin)
        self.dar_dinero(botin)
        self.decir(tr('El peatón te da la cartera: {botin} euros, y sale corriendo.').format(botin=(botin)), True)
        self.moc_botin("atraco")                                 # a veces, algo más: un móvil, un reloj... (mochila.py)
        self.delito(2, "atraco", siempre=random.random() < 0.3)

    # ---------------------------------------------------------- guardaespaldas
    def crear_aliado(self):
        x, y = self.pos()
        px, py = self.mundo.punto_libre(x + random.uniform(-2, 2), y + random.uniform(-2, 2))
        a = Persona("aliado", px, py, tr("Guardaespaldas"))
        a.salud = 140.0
        a.arma = "pistola"
        a.estado = "sigue"
        self.personas.append(a)
        return a

    def actualizar_aliado(self, a, dt):
        j = self.j
        px, py = self.pos()
        puesto = getattr(a, "puesto", None)
        if puesto is not None:          # en un golpe preparado: está en su sitio, no contigo
            if a.dist(*puesto) > 1.5:
                self._andar_hacia(a, puesto[0], puesto[1], 5.6, dt)
        elif j.veh:
            a.x, a.y = px, py           # va de copiloto
        else:
            d = a.dist(px, py)
            if d > 60:
                a.x, a.y = self.mundo.punto_libre(px - 2, py - 2)
            elif d > 3.5:
                self._andar_hacia(a, px, py, 5.6 if d > 10 else 3.0, dt)
                a.t_paso -= dt
                if a.t_paso <= 0:
                    a.t_paso = 0.4
                    self.son("paso_npc", xy=(a.x, a.y), ref=3, maxd=25, vol=0.6, tono=0.8)
        a.t_disparo -= dt
        if a.t_disparo > 0:
            return
        enemigos = [p for p in self.personas if p.hostil and not p.muerto and p.activo and p.dist(a.x, a.y) < 28
                    and (p.tipo != "banda" or p.avisado)]
        if not enemigos:
            a.t_disparo = 0.4
            return
        e = min(enemigos, key=lambda p: p.dist(a.x, a.y))
        a.t_disparo = random.uniform(0.9, 1.5)
        self.son("disparo_pistola", xy=(a.x, a.y), ref=10, maxd=150, vol=0.7)
        if random.random() < 0.5:
            self.danar_persona(e, 22)

    # ------------------------------------------------------------------ sirena
    def alternar_sirena(self):
        if self.sirena_propia:
            self.sirena_propia.parar()
            self.sirena_propia = None
            self.decir(tr("Sirena apagada."), True)
        else:
            self.sirena_propia = self.son(self.j.veh.modelo.get("sirena"), bucle=True, vol=0.35)
            self.decir(tr("Sirena encendida."), True)

    # ----------------------------------------------------------------- lotería
    def sorteo_loteria(self):
        """Celebra los sorteos de la lotería que toquen: uno cada día, a las nueve de la noche. Está en loteria.py."""
        from . import loteria
        loteria.al_dia(self)

    def cobrar_banco(self):
        j = self.j
        if j.banco > 0:
            interes = int(j.banco * (0.01 if j.ciudadania >= 75 else 0.005))
            if interes:
                j.banco += interes
