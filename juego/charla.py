"""Hablar con cualquiera: cada persona de la calle tiene nombre, edad, oficio, carácter y memoria.

Con la tecla J, a pie, hablas con quien tengas al lado. Puedes elegir qué decir en un menú o escribir lo
que quieras: el juego entiende la intención (saludar, preguntar por un sitio, pedir un favor, hacer un
cumplido, amenazar...) y la persona responde según su carácter, su humor y la confianza que te tenga.

Modo IA (opcional): si el jugador lo activa, lo que escriba se envía a una inteligencia artificial (local o
de internet) junto con la ficha de la persona, y la respuesta es libre. Sin eso, contesta el motor propio,
sin conexión: las intenciones de este archivo y la base de respuestas por temas de respuestas.py.
"""
from .i18n import tr
import json
import math
import random

from . import gente as G
from . import mundo as M

# Los nombres, los apellidos, los oficios y los caracteres de la gente salen de los datos (data/datos/gente.json): los lleva gente.py.
CARACTERES = G.CARACTERES
SITIOS = {"comer": ("comida", "pizzeria", "taberna", "bar"), "curarme": ("hospital", "farmacia"), "dinero": ("banco", "empenos"), "armas": ("armeria",),
          "trabajo": ("empleo",), "dormir": ("hotel",), "taller": ("taller",), "policía": ("comisaria",), "comprar": ("tienda",), "fiesta": ("club", "casino", "bar")}
PALABRAS = [
    ("despedir", ("adiós", "adios", tr("hasta luego"), tr("me voy"), "chao", tr("nos vemos"))),
    ("amenazar", ("dame", tr("la cartera"), tr("te mato"), tr("te voy a"), "amenaz", tr("o te"))),
    ("insultar", ("idiota", "imbécil", "imbecil", "gilipollas", "estúpid", "estupid", "cabr", "capull", "tont", "asco")),
    ("ligar", ("guap", "ligar", tr("me gustas"), tr("tomar algo conmigo"), "cita", tr("tu número"), tr("tu numero"), "teléfono", "telefono", tr("cena conmigo"), tr("salir conmigo"))),
    ("limosna", ("toma", tr("te doy"), "quédate", "quedate", tr("para ti"), "propina")),
    ("invitar", ("invito", tr("un café"), tr("un cafe"), tr("una caña"), tr("una cana"), tr("tomar algo"))),
    ("chiste", ("chiste", tr("sabes aquel"), tr("te cuento uno"))),
    ("cumplido", (tr("qué bien"), tr("que bien"), tr("me encanta"), "bonit", "eleg", "simpátic", "simpatic", "majo", "maja", "genial")),
    ("amistad", ("amigos", "amig", tr("quedar otro día"), tr("quedar otro dia"), tr("nos vemos más"), tr("nos vemos mas"))),
    ("rumor", (tr("qué se cuenta"), tr("que se cuenta"), "novedad", "noticias", tr("qué pasa"), tr("que pasa"), "cotilleo", "rumor")),
    ("barrio", ("barrio", "zona", tr("por aquí"), tr("por aqui"), tr("este sitio"), tr("el pueblo"), tr("la ciudad"))),
    ("trabajo_npc", (tr("a qué te dedicas"), tr("a que te dedicas"), "trabajas", tr("tu trabajo"), "oficio")),
    ("saludar", ("hola", "buenas", tr("buenos días"), tr("buenos dias"), tr("qué tal"), tr("que tal"), "saludos", "hey")),
]


def oficio_para(edad, rng=random, genero="h"):
    """Un oficio que cuadre con la edad: nadie estudia a los sesenta ni se jubila a los veinte."""
    return G.oficio_para(edad, genero, rng)


def ficha(persona, rng=random):
    """Da a una persona de la calle su identidad, la primera vez que hace falta."""
    if getattr(persona, "ficha", None):
        return persona.ficha
    g = rng.choice("hm")
    if hasattr(persona, "tono"):                                 # su voz ya se ha oído: que el nombre vaya con ella
        g = "m" if persona.tono > 1.1 else "h"
    edad = rng.randint(19, 74)
    f = {"nombre": rng.choice(G.nombres(g)), "apellido": rng.choice(G.lista("apellidos")), "genero": g, "edad": edad, "oficio": oficio_para(edad, rng, g),
         "caracter": rng.choice(list(CARACTERES)), "confianza": 0, "frases": 0, "disponible": rng.random() < 0.55,
         "le_atraen": rng.choice(["h", "m", "hm"]), "invitado": False, "limosna": False, "presentado": False, "ofendido": False}
    persona.ficha = f
    return f


def interpretar(texto):
    """Qué quiere decir el jugador con lo que ha escrito. Devuelve (intención, dato)."""
    t = " " + (texto or "").lower().strip() + " "
    if not t.strip():
        return "nada", None
    if any(x in t for x in ("dónde", "donde", tr("cómo llego"), tr("como llego"), "busco", tr("hay algún"), tr("hay algun"), "necesito")):
        for clave, tipos in SITIOS.items():
            if clave in t or any(tp in t for tp in tipos) or (clave == "comer" and any(x in t for x in ("restaurante", "hambre", "cenar", "bar"))) \
                    or (clave == "curarme" and any(x in t for x in ("médico", "medico", "herid"))) or (clave == "dinero" and "cajero" in t):
                return "sitio", clave
        return "sitio", None
    for intencion, claves in PALABRAS:
        if any(c in t for c in claves):
            return intencion, None
    return "otra", None


class Charla:
    """Mixin de Partida."""

    def persona_para_hablar(self):
        j = self.j
        if j.veh:
            return None
        cerca = [q for q in self.personas if q.tipo == "civil" and not q.muerto and not q.hostil and q.dist(j.x, j.y) < 5.0]
        return min(cerca, key=lambda q: q.dist(j.x, j.y)) if cerca else None

    def hablar(self):
        j = self.j
        if j.veh:
            return
        q = self.persona_para_hablar()
        if q is None and self.sv_hablar_cerca():                 # en un servidor: hablarle al jugador que tienes al lado
            return
        if q is None:
            self.decir(tr("No tienes a nadie al lado para hablar. Acércate a alguien: el radar, con Tabulador, te dice quién hay cerca."), True)
            return
        f = ficha(q)
        if f["ofendido"]:
            self.son("rechazo", cat="interfaz")
            extra = self.insistir(q)                             # si insistes, según su carácter, puede acabar mal
            self.decir(tr('{v} no quiere saber nada de ti.').format(v=(f['nombre'] if f['presentado'] else tr('Esa persona'))) + (" " + extra if extra else ""), True)
            return
        if q.estado == "huye":
            self.decir(tr("Está huyendo y no se para a hablar."), True)
            return
        from . import menus_charla
        menus_charla.conversar(self, q)

    def _trato(self, f, n):
        if n > 0 and self.apesta():                              # oliendo mal, la gente se acerca menos (necesidades.py)
            n = n // 2
            if random.random() < 0.3:
                from .necesidades import AJ as NEC
                self.decir(NEC.frase("frases_charla_sucio"))
        antes = f["confianza"]
        f["confianza"] = max(-100, min(100, f["confianza"] + n))
        if n and (f["confianza"] // 20) != (antes // 20):
            self.son("afinidad_sube" if n > 0 else "afinidad_baja", cat="interfaz", vol=0.6)

    def confianza_txt(self, f):
        c = f["confianza"]
        return (tr("te mira con desconfianza") if c < -10 else tr("apenas te conoce") if c < 15 else tr("le caes bien") if c < 40 else tr("te tiene confianza") if c < 70 else tr("te considera de los suyos"))

    def presentacion(self, q):
        f = ficha(q)
        if not f["presentado"]:
            f["presentado"] = True
            q.nombre = f["nombre"]
            self.j.stats["charlas"] = self.j.stats.get("charlas", 0) + 1
        return tr('{nombre}{v}, {edad} años, {oficio}. Te habla {desc}').format(nombre=(f['nombre']), v=(' ' + f['apellido'] if f.get('apellido') else ''), edad=(f['edad']), oficio=(f['oficio']), desc=(G.caracter(f['caracter'])['desc']))

    def responder(self, q, intencion, dato=None):
        """Lo que contesta una persona a una intención. Devuelve el texto y aplica las consecuencias."""
        j = self.j
        f = ficha(q)
        c = G.caracter(f["caracter"])
        nombre = f["nombre"]
        f["frases"] += 1
        self.son("murmullo", xy=(q.x, q.y), vol=0.5)
        if intencion == "saludar":
            self._trato(f, c["saludo"] if f["frases"] <= 2 else 1)
            return random.choice([tr('{nombre}: Hola, ¿qué tal? Aquí andamos.').format(nombre=(nombre)), tr('{nombre}: Buenas. ¿Nos conocemos?').format(nombre=(nombre)), tr('{nombre}: Hombre, muy buenas.').format(nombre=(nombre)), tr('{nombre}: Hola. Soy {nombre}, {oficio}.').format(nombre=(nombre), oficio=(f['oficio']))])
        if intencion == "trabajo_npc":
            self._trato(f, 2)
            return tr('{nombre}: Soy {oficio}. ').format(nombre=(nombre), oficio=(f['oficio'])) + random.choice([tr("No me quejo."), tr("Se hace lo que se puede."), tr("Y con lo que pagan, ya ves."), tr("Me gusta, la verdad.")])
        if intencion == "barrio":
            x, y = self.pos()
            b = self.mundo.barrio(x, y)
            self._trato(f, 3)
            return tr('{nombre}: Esto es {nombre2}. {barrio_desc}').format(nombre=(nombre), nombre2=(b['nombre']), barrio_desc=(self.barrio_desc(b))).strip()
        if intencion == "rumor":
            self._trato(f, 2)
            return f"{nombre}: " + self.rumor()
        if intencion == "sitio":
            tipos = SITIOS.get(dato) if dato else None
            if not tipos:
                return tr('{nombre}: ¿Qué buscas exactamente? Dime si quieres comer, curarte, sacar dinero, trabajo, dormir, un taller, comprar o la policía.').format(nombre=(nombre))
            x, y = self.pos()
            cand = [l for l in self.mundo.lugares.values() if l.tipo in tipos]
            if not cand:
                return tr('{nombre}: Aquí no hay nada de eso. Tendrás que ir a otra localidad.').format(nombre=(nombre))
            l = min(cand, key=lambda l: math.hypot(l.x - x, l.y - y))
            self.gps_a_lugar(l, callar=True)
            self._trato(f, 2)
            return tr('{nombre}: Lo más cerca es {nombre2}, {metros}, {direccion_txt}. Te lo marco en el GPS.').format(nombre=(nombre), nombre2=(l.nombre), metros=(M.metros(math.hypot(l.x - x, l.y - y))), direccion_txt=(self.direccion_txt(l.x, l.y)))
        if intencion == "cumplido":
            self._trato(f, c["cumplido"] if f["frases"] <= 6 else 1)
            self.cambiar_animo(1)
            return random.choice([tr('{nombre}: Vaya, muchas gracias. No me lo esperaba.').format(nombre=(nombre)), tr('{nombre}: Qué cosas dices. Gracias.').format(nombre=(nombre)), tr('{nombre}: Se agradece, que hoy no era mi día.').format(nombre=(nombre))])
        if intencion == "chiste":
            gracia = random.random() < 0.6 + c["chiste"] / 40.0
            self._trato(f, c["chiste"] if gracia else -2)
            if gracia:
                self.cambiar_animo(2)
            return f"{nombre}: " + (random.choice([tr("¡Ja! Ese no me lo sabía."), tr("Qué malo eres, pero me he reído."), tr("Buenísimo. Se lo cuento a mi cuñado.")]) if gracia
                                    else random.choice([tr("Ya. Muy gracioso."), tr("No lo pillo."), tr("Ese es más viejo que el puerto.")]))
        if intencion == "invitar":
            if f["invitado"]:
                return tr('{nombre}: Ya me has invitado antes. Otro día me toca a mí.').format(nombre=(nombre))
            if j.dinero < self.precio("cafe_invitar", 4):
                return tr('{nombre}: Si no llevas ni para ti. Déjalo.').format(nombre=(nombre))
            j.dinero -= self.precio("cafe_invitar", 4)
            f["invitado"] = True
            self.son("caja", cat="interfaz", vol=0.5)
            self.pasar_horas(0.3)
            self._trato(f, 12)
            self.cambiar_animo(3)
            return tr('Le invitas a un café por {precio} euros. {nombre}: Pues mira, te lo acepto. ').format(precio=(self.precio('cafe_invitar', 4)), nombre=(nombre)) + random.choice([tr("Me cuenta su vida durante un rato."), tr("Habláis de todo un poco."), tr("Resulta que conoce a media ciudad.")])
        if intencion == "limosna":
            if j.dinero < self.precio("limosna", 10):
                return tr('{nombre}: Guárdate eso, que te hace más falta a ti.').format(nombre=(nombre))
            j.dinero -= self.precio("limosna", 10)
            self.son("donativo", cat="interfaz", vol=0.6)
            self._trato(f, 10 if not f["limosna"] else 2)
            if not f["limosna"]:
                self.cambiar_ciudadania(1.5)
            f["limosna"] = True
            return tr('Le das {precio} euros. {nombre}: ').format(precio=(self.precio('limosna', 10)), nombre=(nombre)) + random.choice([tr("Gracias, de verdad. No hay mucha gente así."), tr("No hacía falta, pero gracias."), tr("Que te lo paguen con salud.")])
        if intencion == "amistad":
            if any(k["nombre"] == nombre and k["oficio"] == f["oficio"] for k in j.conocidos):
                return tr('{nombre}: Si ya tienes mi número. Llámame cuando quieras.').format(nombre=(nombre))
            if f["confianza"] < 30:
                return tr('{nombre}: Bueno, ya nos iremos viendo. Aún no te conozco tanto.').format(nombre=(nombre))
            j.conocidos.append({"nombre": nombre, "genero": f["genero"], "edad": f["edad"], "oficio": f["oficio"], "caracter": f["caracter"], "mapa": self.mundo.id, "dia": self.dia, "ultimo": 0})
            del j.conocidos[:-30]
            self.son("pareja", cat="interfaz", vol=0.5)
            self.cambiar_animo(4)
            return tr('{nombre}: Venga, apunta mi número. Ya tienes a {nombre} entre tus conocidos, en el móvil.').format(nombre=(nombre))
        if intencion == "insultar":
            self._trato(f, c["insulto"])
            f["ofendido"] = True
            self.cambiar_ciudadania(-1.0)
            if random.random() < c["valor"] * 0.5:
                q.hostil, q.estado, q.tipo, q.arma = True, "ataca", "enemigo", None
                return tr('{nombre}: ¿Qué me has llamado? ¡Te vas a enterar! Se te echa encima.').format(nombre=(nombre))
            q.estado, q.t_estado = "huye", 8
            return f"{nombre}: " + random.choice([tr("Menudo personaje. Ahí te quedas."), tr("No tengo por qué aguantar esto."), tr("Vete a paseo.")]) + tr(" Se marcha.")
        if intencion == "amenazar":
            f["ofendido"] = True
            self._trato(f, -60)
            self.cambiar_ciudadania(-2.0)
            self.cambiar_reputacion(1)
            if random.random() < c["valor"]:
                self.delito(1, "amenazas")
                q.estado, q.t_estado = "huye", 12
                self.son("grito", xy=(q.x, q.y), vol=0.6, tono=getattr(q, "tono", 1.0))
                return tr('{nombre}: ¡Socorro! ¡Policía! Sale corriendo dando voces.').format(nombre=(nombre))
            botin = random.randint(8, 45)
            j.dinero += botin
            q.atracado = True
            q.estado, q.t_estado = "huye", 12
            self.delito(1, "amenazas")
            return tr('{nombre}, con miedo, te tira {botin} euros y echa a correr.').format(nombre=(nombre), botin=(botin))
        if intencion == "despedir":
            return f"{nombre}: " + random.choice([tr("Hasta luego."), tr("Venga, que te vaya bien."), tr("Nos vemos."), tr("Cuídate.")])
        return f"{nombre}: " + random.choice([tr("No sé qué decirte."), tr("Ya. Bueno."), tr("Puede ser, puede ser."), tr("Mira, de eso no entiendo."), tr("¿Tú crees?")])

    def rumor(self):
        """Algo que se cuenta por la calle: sale de lo que de verdad pasa en la partida."""
        j = self.j
        ops = [tr("Dicen que va a cambiar el tiempo.") if not self.lluvia else tr("Con esta lluvia no hay quien salga."),
               tr('Hoy es el día {dia} desde que volviste, que se dice pronto.').format(dia=(self.dia))]
        if self.dia_txt():
            ops += [self.dia_txt()] * 2
        if j.estrellas:
            ops.append(tr("La policía anda buscando a alguien por aquí. Yo no he visto nada."))
        if len(self.completadas) >= 5:
            ops.append(tr("Se oye que hay alguien moviendo los hilos en el puerto. Gente nueva."))
        if j.ciudadania >= 45:
            ops.append(tr("Hablan bien de ti en el barrio. Dicen que eres de fiar."))
        if j.reputacion >= 40:
            ops.append(tr("Contigo no quiero líos, que ya sé quién eres."))
        if j.territorios:
            ops.append(tr("Desde que cambió de manos el barrio, la cosa está más tranquila."))
        disp = self.misiones_disponibles()
        if disp:
            l = self.lugares.get(disp[0]["lugar"])
            if l is not None:
                ops.append(tr('En {nombre_lugar} buscan a alguien para un trabajo. Yo no me metería.').format(nombre_lugar=(self.nombre_lugar(l))))
        return random.choice(ops)

    def llamar_conocido(self, k):
        """Un conocido te cuenta algo útil, una vez al día."""
        if k.get("ultimo") == self.dia:
            return tr('{nombre} ya te ha contado hoy todo lo que sabía.').format(nombre=(k['nombre']))
        k["ultimo"] = self.dia
        self.cambiar_animo(2)
        return f"{k['nombre']}: {self.rumor()}"

    # ------------------------------------------------------------------ modo IA
    def ia_disponible(self):
        from . import ia
        return self.cfg["ia_activa"] and ia.disponible(self.cfg)

    def responder_libre(self, q, texto):
        """Respuesta a un texto libre: con el modo IA si está activo; si no, con el motor propio."""
        f = ficha(q)
        if self.ia_disponible():
            from . import ia
            r = ia.responder(self, q, texto)
            if r is not None:
                self.son("murmullo", xy=(q.x, q.y), vol=0.5)
                self._trato(f, max(-15, min(15, int(r.get("confianza", 0)))))
                hecho = self.decidir_accion_ia(q, r.get("accion"))      # el modelo propone; lo que pasa lo decide el juego
                f.setdefault("memoria", []).append((texto, r["respuesta"]))
                del f["memoria"][:-6]
                return f"{f['nombre']}: {r['respuesta']}" + (" " + hecho if hecho else "")
        intencion, dato = interpretar(texto)
        if intencion == "nada":
            return tr("No has dicho nada.")
        if intencion in ("otra", "saludar", "cumplido", "barrio", "invitar", "limosna"):
            # Sin modo IA: la base de respuestas. Si lo escrito toca un tema conocido, manda el tema antes que una intención floja.
            from . import respuestas
            if intencion == "otra" or respuestas.tema_de(texto) is not None:
                x, y = self.pos()
                frase, cambio, _ = respuestas.responder(texto, f, {"barrio": self.mundo.barrio(x, y)["nombre"], "ciudad": self.mundo.nombre,
                                                                    "hora": self.hora_txt(), "tu": self.j.nombre})
                f["frases"] += 1
                self.son("murmullo", xy=(q.x, q.y), vol=0.5)
                if cambio:
                    self._trato(f, cambio if f["frases"] <= 12 else 0)
                return f"{f['nombre']}: {frase}"
        if intencion == "ligar":
            return self.ligar(q) if self.modo_adulto() else f"{f['nombre']}: " + random.choice([tr("Gracias, pero no."), tr("Qué cosas tienes.")])
        return self.responder(q, intencion, dato)


def descripcion_json(f):
    return json.dumps({k: f[k] for k in ("nombre", "genero", "edad", "oficio", "caracter", "confianza")}, ensure_ascii=False)


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False

# ---------------------------------------------------------------- łatka polskiej wersji (latki/rozmowy_zamiary_pl.py)
import unicodedata as _ud


def _bez_znakow(s):
    s = _ud.normalize("NFD", (s or "").lower().replace("ł", "l"))
    return "".join(c for c in s if _ud.category(c) != "Mn")


_PALABRAS_PL = {
    "despedir": ("do widzenia", "na razie", " pa ", "nara", "ide juz", "musze isc", "musze leciec", "do zobaczenia", "zegnaj", "trzymaj sie"),
    "amenazar": ("dawaj", "portfel", "zabije", "bo cie", "groze", "pozalujesz", "oddawaj", "kase albo"),
    "insultar": ("idiot", "debil", "kretyn", "glup", "palant", "dupek", "frajer", "spierdal", "kurw", "chuj", "smiec", "cymbal", "baran"),
    "ligar": ("ladn", "przystojn", "podobasz mi sie", "randk", "twoj numer", "numer telefonu", "telefon", "kolacje ze mna",
              "umowisz sie", "wyjdziesz ze mna", "sliczn", "flirt"),
    "limosna": ("masz,", "wez to", "daje ci", "to dla ciebie", "dla ciebie", "napiwek", "trzymaj,"),
    "invitar": ("zapraszam", "kawe", "kawy", "kawk", "piwo", "piwa", "piwk", "na drinka", "postawie", "stawiam"),
    "chiste": ("kawal", "dowcip", "znasz ten", "opowiem ci jeden", "zart"),
    "cumplido": ("super", "swietn", "ekstra", "fajn", "mily", "mila", "sympatyczn", "elegancko", "pieknie", "wspaniale", "uwielbiam", "fajowo"),
    "amistad": ("przyjaci", "kumpl", "przyjazn", "spotkajmy sie", "zobaczymy sie jeszcze"),
    "rumor": ("co slychac", "co nowego", "plotk", "wiesci", "nowin", "co sie dzieje"),
    "barrio": ("dzielnic", "okolic", "tutaj", "to miejsce", "miasto", "miasteczk"),
    "trabajo_npc": ("czym sie zajmujesz", "gdzie pracujesz", "pracujesz", "twoja praca", "zawod", "co robisz"),
    "saludar": ("czesc", "dzien dobry", "witaj", "siema", "hej", "dobry wieczor", "jak sie masz", " elo "),
}
_SITIOS_PL = {"comer": ("jedz", "jesc", " bar", "tawern", "restaurac", "glod", "kolac", "obiad", "knajp", "pizz"), "curarme": ("szpital", "aptek", "lekarz", "rann", "lecz", "przychodni"),
              "dinero": ("bank", "lombard", "pieniad", "wyplac", "bankomat"), "armas": ("bron", "rusznik"), "trabajo": ("prac", "urzad pracy", "robot"),
              "dormir": ("hotel", "spac", "nocleg"), "taller": ("warsztat", "mechanik"), "policía": ("policj", "komisariat"),
              "comprar": ("sklep", "kupi", "zakup"), "fiesta": ("klub", "kasyn", "impreza", "dyskotek")}
_PYTANIE_O_SITIO = ("gdzie", "jak dojsc", "jak dojechac", "jak trafic", "szukam",
                    "jest tu jakis", "jest tu jakas", "jest tu jakies", "potrzebuje")


def _interpretar_pl(texto):
    """Tylko polskie słowa: hiszpańskie skróty (maja, zona, o te) pasowałyby do polskich wyrazów (mają, żona, o tej)."""
    t = " " + _bez_znakow(texto).strip() + " "
    if not t.strip():
        return "nada", None
    if any(c in t for c in _PALABRAS_PL["trabajo_npc"]):
        return "trabajo_npc", None
    if any(x in t for x in _PYTANIE_O_SITIO):
        for clave in SITIOS:
            if any(x in t for x in _SITIOS_PL.get(clave, ())):
                return "sitio", clave
        return "sitio", None
    for intencion, _claves in PALABRAS:
        if any(c in t for c in _PALABRAS_PL.get(intencion, ())):
            return intencion, None
    return "otra", None


_interpretar_es = interpretar


def interpretar(texto):
    return (_interpretar_pl if _pl() else _interpretar_es)(texto)
