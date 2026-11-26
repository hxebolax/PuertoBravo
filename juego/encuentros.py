"""Quedar en persona, horarios y confianza (1.7.2): que la vida social se viva en el sitio, no solo desde el móvil.

- En persona o por teléfono. Con la opción «La vida social se vive en persona» (de serie, sí), desde el móvil se llama,
  se escribe, se queda, se manda un regalo a domicilio, que se agradece algo menos que en mano, se da dinero y se
  rompe. Lo demás (charlar en persona, una cita, un regalo en mano, un beso, un baile, la noche, un plan, pedir salir,
  prometerse, pedir perdón) se hace cara a cara: en el sitio donde está esa persona, en vuestra casa si vivís juntos,
  o mientras va contigo. Con la opción en no, todo desde el móvil, como antes.
- Quedar. Desde el móvil se queda para un plan, a una hora, en un sitio que sirve para ese plan. Media hora antes se
  avisa. Si llegas a tiempo, te espera y el plan se vive allí, en escenas; si no apareces, plantón: le sienta mal.
- Las citas se viven: proponer una cita en persona hace que se venga contigo, y el plan pasa al llegar al sitio.
- Horarios, opcional (Opciones, Ser buena persona..., Horarios): con «la gente», cada persona de tu vida social está
  en su sitio solo en sus horas, y libra un día a la semana; con «la gente y los locales», además los locales abren y
  cierran, cada uno con su horario y sus días de cierre. Lo que pide una misión o un trabajo en curso está siempre
  abierto, y tus casas y tus negocios también.
- Confianza. Cuando tu pareja se entera de que hay alguien más, la herida dura: unos días en los que lo que hagáis
  juntos acerca la mitad, y si vuelve a pasar en esos días, se acabó. Pedir perdón en persona, una vez al día, lo acorta.
  Los besos y los bailes con otra persona también pueden llegarle.
- Conocidos: a la gente de la calle con la que te has dado el número se le puede proponer quedar a tomar algo.

Los números, las frases, los horarios de los locales y las escenas de cada plan están en los datos (vida.json,
secciones encuentros y horarios_locales; adultos.json, las actividades).
"""
from .i18n import tr
import math
import random

from .ajustes import Ajustes

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

AJ = Ajustes("encuentros", {
    "desconfianza_dias": 10, "perdon_dias": 4, "regalo_envio": 15, "regalo_envio_pct": 60, "planton_afinidad": 8,
    "llamada_afinidad": 2, "aviso_minutos": 30, "espera_minutos": 30, "persona_abre": 10, "persona_cierra": 20, "variacion_horas": 1,
    "conocido_precio": 8, "conocido_animo": 5, "conocido_amistad": 10, "planton_dias": 3, "planton_amistad": 15,
    "hielo_ex_dias": 7,
}, {
    "frases_planton": [tr("{n} te escribe: «Te he estado esperando en {lugar}. Ya me voy.» No le ha sentado nada bien."),
                       tr("{n} se ha cansado de esperarte en {lugar}. No contesta a tus mensajes.")],
    "frases_llega": [tr("{n} ya está en {lugar}, esperándote. Te saluda con un beso."), tr("Ahí está {n}, en la puerta de {lugar}. Llegas a tiempo.")],
    "frases_planton_no": [tr("{n} lee tu mensaje y tarda en contestar: «Después del plantón del otro día, mejor lo dejamos para más adelante.» Prueba dentro de {d} días."),
                          tr("«¿Otra vez? La última vez me dejaste esperando», te contesta {n}. Todavía no quiere quedar contigo: dale {d} días.")],
    "frases_aviso": [tr("Recuerda: a las {hora} has quedado con {n} en {lugar}."), tr("Dentro de un rato, a las {hora}, te espera {n} en {lugar}.")],
    "frases_no_esta": [tr("{n} no está ahora en {lugar}. {cuando}"), tr("Hoy no ves a {n} por {lugar}. {cuando}")],
    "frases_perdon_si": [tr("{n} te escucha sin interrumpir. Al final te coge la mano: «No me lo vuelvas a hacer.»"),
                         tr("Le pides perdón a {n} sin excusas. Se le escapa una media sonrisa. Algo se arregla.")],
    "frases_perdon_no": [tr("{n} te mira un momento y aparta la vista: «Hoy no, de verdad.»"), tr("«No me sirve que me lo digas», dice {n}. «Demuéstramelo.»")],
    "frases_desconfia": [tr("Todavía no se fía de ti desde que se enteró. Quedan unos {d} días."), tr("La herida sigue abierta: unos {d} días para que se le pase.")],
    "escenas_generica": [tr("Llegáis y os buscáis un buen sitio."), tr("La conversación va sola: {n} te cuenta algo de su semana y tú le cuentas algo de la tuya."),
                         tr("En algún momento os quedáis callados, y no es incómodo.")],
    "escenas_cena": [tr("Os sentáis en una mesa junto a la ventana. {n} pide sin mirar la carta: ya ha estado aquí."), tr("Entre plato y plato te cuenta lo que le gustaría hacer dentro de unos años."),
                     tr("Pedís un postre para los dos y os peleáis en broma por la última cucharada.")],
    "escenas_cine": [tr("Elegís la película en la cola, entre risas, por descarte."), tr("A mitad de la película, {n} se acerca a comentarte algo al oído."),
                     tr("Al salir, la discutís de camino a la calle: no os ha gustado lo mismo, y eso también tiene su gracia.")],
    "escenas_copas": [tr("Pedís en la barra y os vais a una esquina tranquila."), tr("La segunda ronda la paga {n}, que insiste."), tr("Os reís de alguien que canta fatal al fondo del local.")],
    "escenas_baile": [tr("La música está alta y la pista, llena."), tr("{n} baila sin vergüenza ninguna y te saca de la esquina."), tr("Salís sudando, con las orejas zumbando y sin ganas de iros.")],
    "escenas_paseo": [tr("Echáis a andar sin rumbo."), tr("{n} te enseña un rincón que no conocías."), tr("Volvéis despacio, alargando el camino.")],
    "frases_hielo_charla": [tr("{n} te mira de arriba abajo: «No tengo nada que hablar contigo.» Y se da la vuelta."), tr("«¿Ahora quieres charlar?», te suelta {n}. «Déjame en paz una temporada.»"), tr("{n} contesta con monosílabos y no deja de mirar el móvil. Todavía le duele.")],
    "frases_hielo_llamada": [tr("Llamas a {n}. Lo coge, oye tu voz y cuelga sin decir nada."), tr("El teléfono de {n} da dos tonos y salta el buzón. Te ha colgado."), tr("«No me llames», te dice {n}, y cuelga.")],
    "frases_hielo_mensaje": [tr("{n} lee tu mensaje y no contesta."), tr("«No me escribas, de momento», te responde {n}. Y nada más.")],
    "frases_hielo_gesto": [tr("{n} se aparta en seco: «Ni se te ocurra.»"), tr("«¿En serio?», dice {n}, y da un paso atrás.")],
    "frases_hielo_cita": [tr("«¿Quedar? No, gracias. Todavía no», te contesta {n}."), tr("{n} ni se lo piensa: «No voy a ir a ningún sitio contigo.»")],
    "frases_hielo_pedir": [tr("{n} se ríe sin ganas: «¿Volver? Hace nada que lo dejamos. Ni lo sueñes.»"), tr("«Dame tiempo. Mucho tiempo», te dice {n}.")],
    "frases_conocido": [tr("{n} llega puntual. Te cuenta cosas del barrio mientras os tomáis algo."), tr("Con {n} se te pasa la hora volando. Al despedirse, te cuenta un chisme.")],
}, cero=("hielo_ex_dias", "planton_afinidad", "variacion_horas", "regalo_envio", "conocido_precio", "planton_dias", "planton_amistad"))

# Horarios de los locales de serie: el tipo de lugar abre y cierra a esas horas, y cierra esos días. Lo que no está aquí,
# abre siempre (hospitales, comisarías, hoteles, estaciones, casas...). Una hora de cierre menor que la de apertura es de madrugada.
_HORARIOS = [
    {"tipo": "tienda", "abre": 9, "cierra": 21, "cierra_dias": ["domingo"]},
    {"tipo": "ropa", "abre": 10, "cierra": 21, "cierra_dias": ["domingo"]},
    {"tipo": "farmacia", "abre": 9, "cierra": 22, "cierra_dias": []},
    {"tipo": "comida", "abre": 12, "cierra": 24, "cierra_dias": []},
    {"tipo": "pizzeria", "abre": 12, "cierra": 24, "cierra_dias": []},
    {"tipo": "bar", "abre": 8, "cierra": 2, "cierra_dias": []},
    {"tipo": "taberna", "abre": 12, "cierra": 2, "cierra_dias": ["lunes"]},
    {"tipo": "cine", "abre": 16, "cierra": 1, "cierra_dias": []},
    {"tipo": "casino", "abre": 18, "cierra": 5, "cierra_dias": []},
    {"tipo": "club", "abre": 22, "cierra": 6, "cierra_dias": ["lunes", "martes"]},
    {"tipo": "feria", "abre": 17, "cierra": 1, "cierra_dias": []},
    {"tipo": "armeria", "abre": 10, "cierra": 20, "cierra_dias": ["domingo"]},
    {"tipo": "banco", "abre": 9, "cierra": 14, "cierra_dias": ["sábado", "domingo"]},
    {"tipo": "concesionario", "abre": 10, "cierra": 20, "cierra_dias": ["domingo"]},
    {"tipo": "taller", "abre": 8, "cierra": 20, "cierra_dias": ["domingo"]},
    {"tipo": "loteria", "abre": 9, "cierra": 21, "cierra_dias": []},
    {"tipo": "pescaderia", "abre": 7, "cierra": 14, "cierra_dias": ["domingo"]},
    {"tipo": "gimnasio", "abre": 7, "cierra": 23, "cierra_dias": []},
    {"tipo": "empenos", "abre": 10, "cierra": 20, "cierra_dias": ["domingo"]},
    {"tipo": "academia", "abre": 9, "cierra": 21, "cierra_dias": ["sábado", "domingo"]},
    {"tipo": "empleo", "abre": 9, "cierra": 14, "cierra_dias": ["sábado", "domingo"]},
    {"tipo": "nautica", "abre": 9, "cierra": 19, "cierra_dias": []},
    {"tipo": "desguace", "abre": 8, "cierra": 19, "cierra_dias": ["domingo"]},
    {"tipo": "periodico", "abre": 9, "cierra": 19, "cierra_dias": []},
    {"tipo": "ong", "abre": 9, "cierra": 19, "cierra_dias": []},
    {"tipo": "protectora", "abre": 10, "cierra": 18, "cierra_dias": []},
]
HORARIOS = {h["tipo"]: dict(h) for h in _HORARIOS}

# A qué sitios se va para cada plan de serie, si la actividad de los datos no lo dice.
_SITIOS = {"cine": ["cine"], "copas": ["bar", "taberna", "club"], "baile": ["club", "feria"], "cena": ["comida", "pizzeria", "hotel"]}


def configurar(datos):
    lista = [h for h in datos.get("horarios_locales", []) if isinstance(h, dict) and h.get("tipo")]
    HORARIOS.clear()
    for h in (lista or _HORARIOS):
        try:
            HORARIOS[str(h["tipo"])] = {"tipo": str(h["tipo"]), "abre": int(h.get("abre", 0)) % 24, "cierra": int(h.get("cierra", 24)),
                                        "cierra_dias": [str(d) for d in (h.get("cierra_dias") or []) if str(d) in DIAS]}
        except (TypeError, ValueError):
            continue


# ====================================================================== el calendario
def dia_semana(p, dia=None):
    """0 es lunes. El primer día de la partida es lunes."""
    return ((p.dia if dia is None else dia) - 1) % 7


def hoy_txt(p):
    return DIAS[dia_semana(p)]


def ahora(p):
    """Minuto absoluto de la partida."""
    return p.dia * 1440 + p.reloj


def _hora(m):
    m = int(m) % 1440
    return f"{m // 60}" + (tr(' y {v:02d}').format(v=(m % 60)) if m % 60 else "")


def modo(p):
    return p.cfg["horarios"] if p.cfg["horarios"] in ("apagado", "gente", "todo") else "apagado"


def en_persona_activo(p):
    return bool(p.cfg["vida_en_persona"])


def _en_franja(hora, abre, cierra):
    """¿Está la hora (en minutos del día) entre abre y cierra (en horas)? Un cierre menor que la apertura pasa de medianoche."""
    a, c = abre * 60, cierra * 60
    if c > 1440:
        c -= 1440
    if a == c or (a == 0 and c == 1440):
        return True
    return a <= hora < c if a < c else (hora >= a or hora < c)


# ====================================================================== los locales
def horario_local(p, l):
    """(abre, cierra, días de cierre) de este local, con su vaivén propio de una hora arriba o abajo; None si abre siempre."""
    h = HORARIOS.get(l.tipo)
    if h is None:
        return None
    rng = random.Random(f"{getattr(p.j, 'semilla', 0)}-horario-{l.id}")
    v = AJ.entero("variacion_horas")
    abre = max(0, min(23, h["abre"] + rng.randint(-v, v))) if v else h["abre"]
    cierra = h["cierra"] + (rng.randint(-v, v) if v else 0)
    return abre, cierra, [DIAS.index(d) for d in h["cierra_dias"]]


def local_abierto(p, l):
    """(abierto, texto) para entrar en un local ahora. Con los horarios de los locales apagados, todo abre siempre."""
    if modo(p) != "todo" or l.id in p.j.propiedades or p.mision or p.trabajo:
        return True, ""
    h = horario_local(p, l)
    if h is None:
        return True, ""
    abre, cierra, cierra_dias = h
    ds = dia_semana(p)
    madrugada = cierra < abre or cierra > 24
    # de madrugada, lo que abrió ayer sigue abierto hasta su hora
    if madrugada and p.reloj < (cierra % 24) * 60:
        if (ds - 1) % 7 not in cierra_dias:
            return True, ""
    elif ds not in cierra_dias and _en_franja(p.reloj, abre, cierra):
        return True, ""
    # cuándo abre
    for k in range(0, 8):
        d = (ds + k) % 7
        if d in cierra_dias:
            continue
        if k == 0 and p.reloj >= abre * 60:
            continue
        cuando = tr("hoy") if k == 0 else tr("mañana") if k == 1 else tr('el {v}').format(v=(tr(DIAS[d])))
        return False, tr('{nombre}. Está cerrado. Abre {cuando} a las {_hora}').format(nombre=(l.nombre), cuando=(cuando), _hora=(_hora(abre * 60))) + (tr(', y cierra los {join}').format(join=(', '.join(tr(DIAS[x]) for x in cierra_dias))) if cierra_dias else "") + "."
    return False, tr('{nombre}. Está cerrado.').format(nombre=(l.nombre))


def horario_txt(p, l):
    h = horario_local(p, l)
    if h is None:
        return tr("Abre siempre.")
    abre, cierra, cierra_dias = h
    return tr('Abre de {_hora} a {_hora2}').format(_hora=(_hora(abre * 60)), _hora2=(_hora((cierra % 24) * 60))) + (tr(', menos los {join}').format(join=(', '.join(tr(DIAS[x]) for x in cierra_dias))) if cierra_dias else tr(", todos los días")) + "."


# ====================================================================== la gente
def horario_persona(p, pers):
    """(desde, hasta, día libre) en que esta persona está en su sitio. Sale de los datos o, si no, de la semilla de la partida."""
    rng = random.Random(f"{getattr(p.j, 'semilla', 0)}-persona-{pers['id']}")
    l = p.lug(pers.get("lugar"))
    h = horario_local(p, l) if l is not None else None
    desde = int(pers.get("desde", h[0] if h else AJ.entero("persona_abre")))
    hasta = int(pers.get("hasta", min(h[1], 23) if h else AJ.entero("persona_cierra")))
    if "desde" not in pers:
        desde = max(0, min(22, desde + rng.randint(0, 2)))
    libre = DIAS.index(pers["libre"]) if pers.get("libre") in DIAS else rng.randrange(7)
    return desde, hasta, libre


def presente(p, pers):
    """¿Está ahora en su sitio? Con los horarios apagados, siempre, como antes."""
    if modo(p) == "apagado":
        return True
    if quedada_en_curso(p, pers["id"]) is not None:
        return False                                             # ha salido a verte
    desde, hasta, libre = horario_persona(p, pers)
    return dia_semana(p) != libre and _en_franja(p.reloj, desde, hasta)


def donde_txt(p, pers):
    """Dónde anda ahora, dicho para la ficha."""
    l = p.lug(pers.get("lugar"))
    nom = p.nombre_lugar(l) if l is not None else tr("su sitio")
    if modo(p) == "apagado":
        return tr('Suele estar en {nom}.').format(nom=(nom))
    desde, hasta, libre = horario_persona(p, pers)
    base = tr('Suele estar en {nom} de {_hora} a {_hora2}, y libra los {v}.').format(nom=(nom), _hora=(_hora(desde * 60)), _hora2=(_hora((hasta % 24) * 60)), v=(tr(DIAS[libre])))
    if p.acompanante and p.acompanante.get("pid") == pers["id"]:
        return base + tr(" Ahora va contigo.")
    if presente(p, pers):
        return base + tr(" Ahora está allí.")
    return base + tr(" Ahora no está allí: anda a lo suyo. Puedes llamarle o proponerle quedar.")


def cara_a_cara(p, pers):
    """¿Estáis juntos ahora mismo? En su sitio y a su hora, en vuestra casa si vivís juntos y está, mientras va contigo, o en vuestra cita."""
    if not en_persona_activo(p):
        return True
    pid = pers["id"]
    if p.acompanante and p.acompanante.get("pid") == pid:
        return True
    aqui = p.lugar_cercano(16)
    if aqui is None:
        return False
    if aqui.id == pers.get("lugar") and presente(p, pers):
        return True
    j = p.j
    if j.convive == pid and aqui.id == j.convive_casa and p.pareja_en_casa():
        return True
    q = quedada_en_curso(p, pid)
    return q is not None and q.get("estado") == "juntos" and aqui.id == q["lugar"]


def lejos_txt(p, pers):
    l = p.lug(pers.get("lugar"))
    return (tr('Eso se hace en persona, y {nombre} no está contigo. ').format(nombre=(pers['nombre'])) + donde_txt(p, pers) +
            tr(" Desde el móvil puedes llamarle, escribirle, quedar o mandarle un regalo."))


# ====================================================================== los planes
def sitios_de(act):
    return list(act.get("lugares") or _SITIOS.get(act["id"], []))


def sitio_para(p, act, cerca_de):
    """El sitio más cercano a `cerca_de` (un lugar) que sirve para el plan, en su misma localidad; para un paseo, el propio lugar."""
    tipos = sitios_de(act)
    if not tipos or cerca_de is None:
        return cerca_de
    cand = [l for l in p.lugares.values() if l.tipo in tipos and l.mapa == cerca_de.mapa and l.id != cerca_de.id] or         [l for l in p.lugares.values() if l.tipo in tipos and l.mapa == cerca_de.mapa]      # mejor otro sitio que donde trabaja
    if not cand:
        return cerca_de
    return min(cand, key=lambda l: math.hypot(l.x - cerca_de.x, l.y - cerca_de.y))


def escenas(p, pers, act, gusta):
    lista = AJ.lista("escenas_" + act["id"]) if ("escenas_" + act["id"]) in AJ.l else AJ.lista("escenas_generica")
    lineas = [(tr("Narrador"), t.replace("{n}", pers["nombre"])) for t in lista]
    lineas.append((tr("Narrador"), (tr("Lo pasáis en grande: es justo lo que le gusta a ") + pers["nombre"] + "." if gusta
                                else tr("Pasáis un rato agradable, aunque no es su plan favorito.")) + tr(' Ahora {afinidad_txt}. Son las {hora_txt}.').format(afinidad_txt=(p.afinidad_txt(p.relacion(pers['id']))), hora_txt=(p.hora_txt()))))
    return lineas


def vivir_cita(p, pers, act, lugar=None, cobrar=True):
    """El plan pasa de verdad: se paga, pasa el tiempo, os acerca y se cuenta en escenas. False si no se pudo pagar."""
    from .menus import Dialogo
    pid = pers["id"]
    r = p.relacion(pid)
    if cobrar and act.get("precio") and not p.pagar(int(act["precio"])):
        return False
    gusta = act["id"] in pers.get("gustos", [])
    r.setdefault("hoy", {})["cita"] = p.dia
    from . import vestuario
    from .necesidades import AJ as NEC
    extra, frase_ropa = vestuario.bono_cita(p, pers)             # si vas con el estilo que le gusta (vestuario.py)
    gana = (13 if gusta else 5) + extra
    if p.sucio():                                                # sin ducharte, se nota (necesidades.py)
        gana = max(1, int(gana * NEC("cita_sucio_pct") / 100.0))
        frase_ropa = (frase_ropa + " " if frase_ropa else "") + NEC.frase("frases_cita_sucio", n=pers["nombre"])
    p.sumar_afinidad(pid, gana)
    r["citas"] = r.get("citas", 0) + 1
    p.pasar_horas(act["horas"])
    p.cambiar_animo(8 if gusta else 3)
    p.son("cita", cat="interfaz")
    lineas = [(tr("Narrador"), tr('{nombre} con {nombre2}').format(nombre=(act['nombre']), nombre2=(pers['nombre'])) + (tr(', en {nombre}').format(nombre=(lugar.nombre)) if lugar is not None else "") + ".")]
    if frase_ropa:
        lineas.append((tr("Narrador"), frase_ropa))
    p.app.abrir(Dialogo(p.app, lineas + escenas(p, pers, act, gusta)))
    p.celos(pid)
    return True


# ====================================================================== quedar
def quedadas(p):
    q = getattr(p.j, "quedadas", None)
    if not isinstance(q, list):
        q = p.j.quedadas = []
    return q


def quedada_en_curso(p, pid):
    """La quedada con esta persona que está ahora en marcha (ya es la hora o estáis juntos), o None."""
    t = ahora(p)
    for q in quedadas(p):
        if q["con"] == pid and (q.get("estado") == "juntos" or q["min"] - AJ.entero("espera_minutos") <= t <= q["min"] + AJ.entero("espera_minutos")):
            return q
    return None


def huecos(p, pers=None):
    """Las horas a las que se puede quedar, desde ahora: [(texto, minuto absoluto)]. Si tiene horario, fuera de sus horas de trabajo."""
    t = ahora(p)
    hoy = p.dia * 1440
    cand = [(tr("Dentro de una hora"), (t // 60 + 2) * 60)]
    for base, nombre in ((hoy, tr("Hoy")), (hoy + 1440, tr("Mañana"))):
        for h in (13, 18, 21):
            m = base + h * 60
            if m > t + 45:
                cand.append((tr('{nombre} a las {h}').format(nombre=(nombre), h=(h)), m))
    vistos, lista = set(), []
    for txt, m in cand:
        if m in vistos:
            continue
        vistos.add(m)
        if pers is not None and modo(p) != "apagado":
            desde, hasta, libre = horario_persona(p, pers)
            d = (m // 1440 - 1) % 7
            if d != libre and _en_franja(m % 1440, desde, hasta):
                continue                                         # a esa hora está trabajando
        if txt == tr("Dentro de una hora"):
            txt = tr('Dentro de un rato, a las {_hora}').format(_hora=(_hora(m)))
        lista.append((txt, m))
    return lista


def quedar(p, con, nombre, lugar, minuto, act_id=None):
    """Apunta una quedada. `con` es el id de la persona, o «c:» y el nombre de un conocido."""
    quedadas(p)[:] = [q for q in quedadas(p) if q["con"] != con]
    quedadas(p).append({"con": con, "nombre": nombre, "lugar": lugar.id, "min": int(minuto), "act": act_id, "estado": "pendiente", "avisado": False})
    p.son("movil", cat="interfaz", vol=0.6)
    p.decir(tr('Quedáis {v} a las {_hora} en {nombre}. Media hora antes te lo recuerdo. Ve con tiempo: si no apareces, se lo tomará mal.').format(v=(tr('hoy') if minuto // 1440 == p.dia else tr('mañana')), _hora=(_hora(minuto)), nombre=(lugar.nombre)), True)


def actualizar(p, dt):
    """Cada poco: avisos, llegadas y plantones de las quedadas."""
    p._t_quedadas = getattr(p, "_t_quedadas", 0.0) - dt
    if p._t_quedadas > 0:
        return
    p._t_quedadas = 1.0
    lista = quedadas(p)
    if not lista:
        return
    t = ahora(p)
    aqui = p.lugar_cercano(16)
    for q in list(lista):
        l = p.lug(q["lugar"])
        if l is None:
            lista.remove(q)
            continue
        if not q.get("avisado") and q["min"] - AJ.entero("aviso_minutos") <= t < q["min"]:
            q["avisado"] = True
            p.son("movil", cat="interfaz", vol=0.6)
            p.decir(AJ.frase("frases_aviso", hora=_hora(q["min"]), n=q["nombre"], lugar=p.nombre_lugar(l)))
        if q.get("estado") == "pendiente" and aqui is not None and aqui.id == l.id and q["min"] - AJ.entero("espera_minutos") <= t <= q["min"] + AJ.entero("espera_minutos"):
            q["estado"] = "juntos"
            lista.remove(q)
            _encuentro(p, q, l)
            continue
        if q.get("estado") == "pendiente" and t > q["min"] + AJ.entero("espera_minutos"):
            lista.remove(q)
            _planton(p, q, l)


def _planton(p, q, l):
    """No has ido: se acuerda. Pierde afinidad (o amistad, si es un conocido) y durante unos días no quiere volver a quedar."""
    p.son("afinidad_baja", cat="interfaz")
    if q["con"].startswith("c:"):
        c = next((x for x in p.j.conocidos if x.get("nombre") == q["con"][2:]), None)
        if c is not None:
            c["amistad"] = max(0, int(c.get("amistad", 0)) - AJ.entero("planton_amistad"))
            c["planton"] = p.dia
        p.decir(tr('{nombre} te ha esperado en {nombre2} y no has aparecido. No creo que vuelva a quedar contigo pronto.').format(nombre=(q['nombre']), nombre2=(l.nombre)))
        return
    r = p.relacion(q["con"])
    r["planton"] = p.dia
    r["plantones"] = int(r.get("plantones", 0)) + 1
    p.sumar_afinidad(q["con"], -AJ.entero("planton_afinidad"))
    p.cambiar_animo(-3)
    p.decir(AJ.frase("frases_planton", n=q["nombre"], lugar=l.nombre))


def dias_de_planton(p, ficha):
    """Los días que le quedan a alguien para volver a querer quedar contigo tras un plantón; cero si ya se le ha pasado.
    `ficha` es su relación (vida social) o su ficha de conocido."""
    dia = ficha.get("planton") if isinstance(ficha, dict) else None
    if dia is None:
        return 0
    return max(0, int(dia) + AJ.entero("planton_dias") - p.dia)


def rechaza_por_planton(p, nombre, ficha):
    """Si todavía está dolido por el plantón, lo dice y devuelve True."""
    d = dias_de_planton(p, ficha)
    if not d:
        return False
    p.app.son("rechazo", cat="interfaz")
    p.app.decir(AJ.frase("frases_planton_no", n=nombre, d=d), True)
    return True


def _encuentro(p, q, l):
    if q["con"].startswith("c:"):
        return _con_conocido(p, q, l)
    pers = p.persona_social(q["con"])
    if pers is None:
        return
    p.decir(AJ.frase("frases_llega", n=pers["nombre"], lugar=l.nombre))
    act = next((a for a in p.dato_adulto("actividades") if a["id"] == q.get("act")), None)
    if act is None or act["id"] == "paseo":
        from . import sistemas
        sistemas.empezar_paseo(p, pers)
        return
    if p.j.estrellas:
        p.decir(tr('Con la policía detrás, {nombre} prefiere dejarlo para otro día.').format(nombre=(pers['nombre'])))
        return
    vivir_cita(p, pers, act, l)


def _con_conocido(p, q, l):
    nombre = q["nombre"]
    c = next((x for x in p.j.conocidos if x.get("nombre") == nombre), None)
    precio = AJ.entero("conocido_precio")
    if precio and not p.pagar(precio):
        p.decir(tr('No tienes ni para invitar a {nombre}. Os tomáis un vaso de agua y poco más.').format(nombre=(nombre)))
        return
    p.pasar_horas(1)
    p.cambiar_animo(AJ.entero("conocido_animo"))
    if c is not None:
        c["amistad"] = min(100, int(c.get("amistad", 0)) + AJ.entero("conocido_amistad"))
        c["ultimo"] = p.dia
    p.son("cita", cat="interfaz", vol=0.6)
    p.decir(AJ.frase("frases_conocido", n=nombre) + " " + p.rumor())


# ====================================================================== confianza
def desconfianza(p, pid):
    """Días que le quedan a tu pareja para volver a fiarse de ti; 0 si no hay herida."""
    r = p.j.relaciones.get(pid) or {}
    return max(0, int(r.get("desconfia_hasta", 0)) - p.dia)


def herir(p, pid):
    """Se ha enterado. Si ya estaba herida, se acabó. Devuelve True si rompe."""
    r = p.relacion(pid)
    if desconfianza(p, pid) > 0:
        return True
    r["desconfia_hasta"] = p.dia + AJ.entero("desconfianza_dias")
    r["enganos"] = int(r.get("enganos", 0)) + 1
    return False


def pedir_perdon(p, pers):
    pid = pers["id"]
    r = p.relacion(pid)
    if desconfianza(p, pid) <= 0:
        p.decir(tr('No hay nada que perdonar. {nombre} no sabe a qué te refieres.').format(nombre=(pers['nombre'])), True)
        return False
    if p._hecho_hoy(r, "perdon"):
        p.decir(tr("Hoy ya se lo has pedido. Dale tiempo."), True)
        return False
    if random.random() < max(0.2, min(0.85, r["afinidad"] / 110.0)):
        r["desconfia_hasta"] = max(p.dia, int(r.get("desconfia_hasta", p.dia)) - AJ.entero("perdon_dias"))
        p.relacion(pid)["afinidad"] = min(100, r["afinidad"] + 2)
        p.son("afinidad_sube", cat="interfaz")
        p.decir(AJ.frase("frases_perdon_si", n=pers["nombre"]) + (" " + AJ.frase("frases_desconfia", d=desconfianza(p, pid)) if desconfianza(p, pid) else tr(" Te ha perdonado.")), True)
        return True
    r["afinidad"] = max(0, r["afinidad"] - 2)
    p.son("afinidad_baja", cat="interfaz")
    p.decir(AJ.frase("frases_perdon_no", n=pers["nombre"]), True)
    return False


# ====================================================================== menús
def menu_quedar(p, pers, al_terminar=None):
    """Desde el móvil: eliges el plan y la hora; el sitio, el que sirve para ese plan cerca de donde suele estar."""
    from .menus import Menu, Opcion
    app = p.app
    pid = pers["id"]
    r = p.relacion(pid)
    if r["afinidad"] < 10 and p.j.pareja != pid:
        app.son("error")
        app.decir(tr('{nombre} apenas te conoce. Charlad primero algún día.').format(nombre=(pers['nombre'])), True)
        return
    if rechaza_por_planton(p, pers["nombre"], r):
        return
    base = p.lug(pers.get("lugar"))

    def hora(act):
        def abrir():
            sitio = sitio_para(p, act, base)
            lista = huecos(p, pers)

            def fijar(m):
                def f():
                    quedar(p, pid, pers["nombre"], sitio, m, act["id"])
                    for x in list(app.pila):
                        if x is mm or x is mh:
                            app.cerrar(x)
                    if al_terminar:
                        al_terminar()
                return f
            mh = Menu(app, tr('{nombre} con {nombre2}, en {v}: ¿a qué hora?').format(nombre=(act['nombre']), nombre2=(pers['nombre']), v=(sitio.nombre if sitio else tr('su sitio'))),
                      [Opcion(t, fijar(m), ayuda=tr("Quedáis a esa hora. Media hora antes te lo recuerdan. Si no apareces, se lo toma mal. Si ya habías quedado con esa persona, esta quedada sustituye a la otra."))
                       for t, m in lista] + [Opcion(tr("Volver"), lambda: app.cerrar(mh))] if lista else
                      [Opcion(tr('{nombre} no tiene ningún hueco libre hoy ni mañana').format(nombre=(pers['nombre'])), ayuda=tr("A esas horas está trabajando. Prueba otro día.")),
                       Opcion(tr("Volver"), lambda: app.cerrar(mh))])
            app.abrir(mh)
        return abrir
    mm = Menu(app, tr('Quedar con {nombre}: ¿para qué?').format(nombre=(pers['nombre'])),
              [Opcion(f"{a['nombre']}" + (tr(': {precio} euros').format(precio=(a['precio'])) if a.get("precio") else ""), hora(a),
                      ayuda=tr("Después eliges la hora. Es en un sitio que sirve para este plan, cerca de donde suele estar, y se paga allí, cuando lo vivís. Si es de los planes que le gustan, os acerca más."))
               for a in p.dato_adulto("actividades")] + [Opcion(tr("Volver"), lambda: app.cerrar(mm))],
              intro=tr("El plan se vive allí: id a la hora. Si no apareces, se lo tomará mal"))
    app.abrir(mm)


def menu_quedar_conocido(p, c):
    from .menus import Menu, Opcion
    app = p.app
    tipos = ("bar", "taberna", "comida", "pizzeria")
    mapa = c.get("mapa") or p.mundo.id
    cand = [l for l in p.lugares.values() if l.tipo in tipos and l.mapa == mapa]
    if not cand:
        app.son("error")
        app.decir(tr('{nombre} vive en otra parte y allí no hay dónde tomar algo.').format(nombre=(c['nombre'])), True)
        return
    if rechaza_por_planton(p, c["nombre"], c):
        return

    def fijar(m):
        def f():
            sitio = random.Random(f"{c['nombre']}-{p.dia}").choice(cand)
            quedar(p, "c:" + c["nombre"], c["nombre"], sitio, m)
            app.cerrar(mm)
        return f
    mm = Menu(app, tr('Quedar con {nombre} para tomar algo: ¿a qué hora?').format(nombre=(c['nombre'])), [Opcion(t, fijar(m), ayuda=tr("Quedáis a esa hora en un bar o un sitio de comidas de su localidad. Media hora antes te lo recuerdan. Si no apareces, tardará en querer quedar contigo."))
                                                                                                for t, m in huecos(p)] + [Opcion(tr("Volver"), lambda: app.cerrar(mm))],
              intro=tr('Invitas tú: unos {entero} euros. Os hacéis más amigos y te cuenta lo que se dice por ahí').format(entero=(AJ.entero('conocido_precio'))))
    app.abrir(mm)


def menu_quedadas(p):
    """Tus quedadas pendientes, con la opción de marcar el sitio en el GPS o anularlas."""
    from .menus import Menu, Opcion
    app = p.app

    def ops():
        lista = []
        for q in list(quedadas(p)):
            l = p.lug(q["lugar"])
            if l is None:
                continue

            def gps(l=l):
                from . import menus_extra
                menus_extra._volver_al_juego(p)
                p.gps_a_lugar(l)

            def anular(q=q):
                quedadas(p).remove(q)
                if not q["con"].startswith("c:"):
                    p.sumar_afinidad(q["con"], -2)
                app.decir(tr('Le dices a {nombre} que no puedes. Lo entiende, pero no le hace gracia.').format(nombre=(q['nombre'])), True)
                m.refrescar(False)
            dia = "hoy" if q["min"] // 1440 == p.dia else "mañana" if q["min"] // 1440 == p.dia + 1 else tr('el día {v}').format(v=(q['min'] // 1440))
            lista.append(Opcion(tr('Con {nombre}, {dia} a las {_hora}, en {nombre_lugar}. Intro lo marca en el GPS').format(nombre=(q['nombre']), dia=(dia), _hora=(_hora(q['min'])), nombre_lugar=(p.nombre_lugar(l))), gps,
                                ayuda=tr("Vuelves al juego con el GPS apuntando al sitio. Llega a tiempo: si no apareces, se lo toma mal.")))
            lista.append(Opcion(tr('Anular la quedada con {nombre}').format(nombre=(q['nombre'])), anular, ayuda=tr("Avisar con tiempo sienta mucho mejor que un plantón, pero algo sienta.")))
        if not lista:
            lista.append(Opcion(tr("No has quedado con nadie"), ayuda=tr("Para quedar, abre la ficha de alguien de tu vida social en el móvil.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
        return lista
    m = Menu(app, tr("Tus quedadas"), ops)
    app.abrir(m)
