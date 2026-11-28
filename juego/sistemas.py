"""Tres sistemas de juego: mejoras de vehículos, banda propia e interior recorrible de las casas.

- Mejoras: en cualquier taller se mejora el vehículo que traigas, en motor, frenos y blindaje, con tres niveles
  cada una. Van con ese vehículo: se conservan al guardarlo en un garaje y al pedir que te lo traigan.
- Banda propia: quien tiene al menos un territorio puede ponerle nombre a su banda y reclutar gente. Cobran un
  sueldo cada medianoche y acuden cuando los llamas.
- Interior de las casas: en una casa tuya puedes recorrer las habitaciones y hacer en cada una lo suyo.
"""
from .i18n import tr
import random

import pygame

from .entidades import Persona

# ============================================================ mejoras de vehículos
# Lo que puede hacer una mejora, y cuánto da cada nivel de serie, en tanto por ciento. Cada mejora de los datos dice cuál
# de estos efectos tiene, cuántos niveles y cuánto da cada uno: así un mod puede poner las suyas.
EFECTOS = {
    "motor": 7.0,          # más velocidad punta y más aceleración; el motor suena más agudo
    "frenos": 15.0,        # frena en menos metros
    "blindaje": 25.0,      # más resistencia
    "neumaticos": 25.0,    # frena mejor con lluvia, pincha menos y rueda con menos ruido
    "suspension": 15.0,    # los choques hacen menos daño
    "escape": 30.0,        # el motor suena más bajo y la policía te oye de menos lejos
    "deposito": 30.0,      # caben más litros
}
_SERIE = (("motor", tr("Motor"), 900, tr("Más velocidad punta y más aceleración. Se oye: el motor suena más agudo.")),
          ("frenos", tr("Frenos"), 500, tr("Frena en menos metros.")),
          ("blindaje", tr("Blindaje"), 700, tr("Aguanta más golpes y más disparos.")))
NIVEL_MAX = 3                     # los niveles de una mejora que no diga los suyos
MEJORAS = {}                      # identificador -> {"nombre", "precio", "desc", "efecto", "niveles", "por_nivel"}


def _mejora(ident, nombre, precio_, desc, efecto=None, niveles=None, por_nivel=None, aeronaves=None):
    efecto = efecto if efecto in EFECTOS else (ident if ident in EFECTOS else "")
    try:
        niveles = max(1, min(5, int(niveles or NIVEL_MAX)))
    except (TypeError, ValueError):
        niveles = NIVEL_MAX
    try:
        por_nivel = max(0.0, min(100.0, float(por_nivel if por_nivel not in (None, "") else EFECTOS.get(efecto, 0.0))))
    except (TypeError, ValueError):
        por_nivel = EFECTOS.get(efecto, 0.0)
    if aeronaves is None:                                       # a lo que vuela, de serie, solo el motor y el blindaje
        aeronaves = efecto in ("motor", "blindaje")
    return {"nombre": str(nombre or ident), "precio": int(precio_ or 0), "desc": str(desc or ""), "efecto": efecto, "niveles": niveles, "por_nivel": por_nivel,
            "aeronaves": bool(aeronaves)}


for _m in _SERIE:
    MEJORAS[_m[0]] = _mejora(*_m)


def configurar(datos):
    """Las mejoras del taller y los muebles de la casa salen de los datos del juego (vida.json), que un mod puede cambiar.
    Cada mejora dice su nombre, su precio, cuántos niveles tiene, qué efecto hace de los que el juego sabe hacer y cuánto
    da cada nivel. Una mejora sin efecto se puede comprar y se describe, pero no cambia nada. Lo que hace cada mueble lo
    decide su identificador, aquí en el código."""
    mej = [m for m in datos.get("mejoras", []) if isinstance(m, dict) and m.get("id")]
    MEJORAS.clear()
    for m in mej:
        serie = next((x for x in _SERIE if x[0] == m["id"]), (m["id"], m["id"], 0, ""))
        MEJORAS[str(m["id"])] = _mejora(m["id"], m.get("nombre") or serie[1], m.get("precio", serie[2]) or serie[2], m.get("desc") or serie[3],
                                         m.get("efecto"), m.get("niveles"), m.get("por_nivel"), m.get("aeronaves"))
    for x in _SERIE:                                           # las tres de siempre no faltan nunca
        MEJORAS.setdefault(x[0], _mejora(*x))
    mue = [m for m in datos.get("muebles", []) if isinstance(m, dict) and m.get("id") and m.get("habitacion")]
    if mue:
        MUEBLES[:] = [(m["id"], m["habitacion"], str(m.get("nombre", m["id"])), int(m.get("precio", 0) or 0), str(m.get("desc", "")), str(m.get("efecto", "")))
                      for m in mue]


def nivel(v, cual):
    return int(getattr(v, "mejoras", {}).get(cual, 0))


def niveles(cual):
    """Cuántos niveles tiene una mejora."""
    return MEJORAS[cual]["niveles"] if cual in MEJORAS else NIVEL_MAX


def precio(v, cual):
    return MEJORAS[cual]["precio"] * (nivel(v, cual) + 1)


def efecto(v, cual):
    """Cuánto lleva ganado un vehículo en un efecto, en tanto por uno: la suma de sus mejoras con ese efecto."""
    return sum(n * MEJORAS[k]["por_nivel"] / 100.0 for k, n in getattr(v, "mejoras", {}).items() if n and k in MEJORAS and MEJORAS[k]["efecto"] == cual)


def factor_velocidad(v):
    return 1.0 + efecto(v, "motor")


def factor_aceleracion(v):
    return 1.0 + efecto(v, "motor") * 12.0 / 7.0


def factor_frenada(v):
    return 1.0 + efecto(v, "frenos")


def factor_tono(v):
    return 1.0 + efecto(v, "motor") * 4.0 / 7.0


def factor_blindaje(v):
    return 1.0 + efecto(v, "blindaje")


def factor_lluvia(v):
    """Lo que frena con lluvia respecto a en seco: 0,6 con ruedas corrientes; con neumáticos reforzados, casi como en seco."""
    return 0.6 + 0.4 * min(1.0, efecto(v, "neumaticos"))


def factor_pinchazo(v):
    """Cuánto pincha respecto a unas ruedas corrientes."""
    return max(0.1, 1.0 - efecto(v, "neumaticos"))


def factor_rodadura(v):
    """(volumen, tono) del ruido de las ruedas: unos neumáticos mejores ruedan más bajo y más graves."""
    e = min(1.0, efecto(v, "neumaticos"))
    return 1.0 - 0.45 * e, 1.0 - 0.18 * e


def factor_golpes(v):
    """El daño que le hace un choque respecto a un vehículo de serie."""
    return max(0.2, 1.0 - efecto(v, "suspension"))


def factor_motor_volumen(v):
    """A qué volumen suena el motor respecto a uno de serie."""
    return max(0.3, 1.0 - efecto(v, "escape"))


def factor_oido_policia(v):
    """Desde cuánto te oye la policía respecto a un vehículo de serie: con el escape silenciado, de menos lejos."""
    return max(0.6, 1.0 - 0.5 * efecto(v, "escape"))


def factor_deposito(v):
    return 1.0 + efecto(v, "deposito")


def poner(v, mejoras):
    """Deja el vehículo con las mejoras dadas (al comprarlas o al sacarlo de un garaje)."""
    mejoras = {k: max(0, min(niveles(k), int(n))) for k, n in dict(mejoras or {}).items() if k in MEJORAS}
    antes = factor_blindaje(v)
    v.mejoras = mejoras
    base = float(v.modelo["salud"])
    nueva = base * factor_blindaje(v)
    if nueva != v.salud_max:
        v.salud = min(nueva, v.salud + max(0.0, nueva - base * antes))
        v.salud_max = nueva


def resumen(v):
    partes = [tr('{lower} nivel {n}').format(lower=(tr(MEJORAS[k]['nombre']).lower()), n=(n)) for k, n in getattr(v, "mejoras", {}).items() if n and k in MEJORAS]
    return tr("Mejoras: ") + ", ".join(partes) if partes else tr("Sin mejoras")


def opciones_taller(p, v, Opcion):
    """Las opciones de mejora que se añaden al menú del taller."""
    app = p.app

    def comprar(cual):
        def f():
            n = nivel(v, cual)
            if v.tag:                                            # no te lo puedes quedar: se avisa antes de cobrar nada
                app.son("error")
                app.decir(p.motivo_ajeno(v), True)
            elif n >= niveles(cual):
                app.decir(tr('{nombre} ya está al máximo.').format(nombre=(tr(MEJORAS[cual]['nombre']))), True)
            elif p.pagar(precio(v, cual)):
                m = dict(getattr(v, "mejoras", {}))
                m[cual] = n + 1
                poner(v, m)
                p.son("reparar", cat="interfaz")
                if v.canal and v is p.j.veh:                     # el escape nuevo se oye ya: el motor baja de volumen
                    v.canal.volumen(0.42 * factor_motor_volumen(v))
                suyo = not p.es_mio(v) and p.hacer_mio(v, callar=True)      # lo que mejoras es tuyo: ya no se pierde en la calle
                v.robado = False                                 # y a tu nombre: el desguace te lo paga como tuyo
                app.decir(tr('{nombre} mejorado al nivel {v} de {niveles}. {resumen}.').format(nombre=(tr(MEJORAS[cual]['nombre'])), v=(n + 1), niveles=(niveles(cual)), resumen=(resumen(v)))
                          + (tr(' {nombre} queda a tu nombre: no desaparece aunque lo dejes en la calle, y lo tienes en el móvil, en Mis vehículos.').format(nombre=(v.nombre)) if suyo else ""), True)
        return f

    def texto(cual):
        def f():
            n = nivel(v, cual)
            return tr('Mejorar {lower}: nivel {n} de {niveles}').format(lower=(tr(MEJORAS[cual]['nombre']).lower()), n=(n), niveles=(niveles(cual))) + (tr('. Subir cuesta {precio} euros').format(precio=(precio(v, cual))) if n < niveles(cual) else tr(". Al máximo"))
        return f
    return [Opcion(texto(k), comprar(k), ayuda=tr(MEJORAS[k]["desc"]) + tr(" Las mejoras van con este vehículo, que desde la primera queda a tu nombre: no se pierde aunque lo dejes en la calle o cojas otro, "
                                                              "y se conservan en el garaje. Vale también para los vehículos de trabajo.")) for k in MEJORAS
            if not v.modelo.get("vuela") or MEJORAS[k].get("aeronaves")]      # a un helicóptero, nada de neumáticos ni frenos (foro, 1.7.6)


# ============================================================ banda propia
PRECIO_RECLUTA = 400
SUELDO = 60
TOPE_BANDA = 10                  # de serie, si los datos no dicen otra cosa (vida.json, capo, banda_tope)


def tope_banda():
    """Lo más que puede mantener un jefe, tenga los barrios que tenga (vida.json, capo, banda_tope)."""
    from .capo import AJ as CAPO
    try:
        return max(1, CAPO.entero("banda_tope"))
    except (KeyError, TypeError, ValueError):
        return TOPE_BANDA


def cupo(j):
    """Cuánta gente puede tener la banda: uno más por cada territorio, hasta el tope. Sin territorios, no hay banda."""
    return min(tope_banda(), len(j.territorios) + 1) if j.territorios else 0


def sin_sitio_en_banda(j):
    """Por qué no cabe nadie más en la banda: le faltan barrios, o ya está al completo."""
    if cupo(j) >= tope_banda():
        return tr('Tu banda ya está al completo: {tope} es lo más que puede mantener un jefe, tengas los barrios que tengas.').format(tope=tope_banda())
    return tr('Con {len} territorios no puedes mantener a más de {cupo}. Conquista otro barrio.').format(len=(len(j.territorios)), cupo=(cupo(j)))


def miembros_presentes(p):
    return [e for e in p.personas if e.tipo == "aliado" and getattr(e, "de_banda", False) and not e.muerto]


def reclutar(p):
    j = p.j
    if not j.territorios:
        return False, tr("Para tener banda necesitas un territorio. Conquista un barrio primero.")
    if j.banda >= cupo(j):
        return False, sin_sitio_en_banda(j)
    if not p.pagar(p.precio("recluta", PRECIO_RECLUTA)):
        return False, ""
    j.banda += 1
    if not j.banda_nombre:
        from . import gente
        j.banda_nombre = random.choice(gente.lista("bandas_propias"))
    nuevo = p.banda_alta()
    p.son("pareja", cat="interfaz", vol=0.5)
    return True, (tr('{n} entra en {banda_nombre}.').format(n=(nuevo['n']), banda_nombre=(j.banda_nombre)) if nuevo else tr('Uno más en {banda_nombre}.').format(banda_nombre=(j.banda_nombre))) + tr(' Ya sois {banda} además de ti. Cada uno cobra {precio} euros cada medianoche.').format(banda=(j.banda), precio=(p.precio('sueldo_banda', SUELDO)))


def llamar(p):
    """Acuden los de la banda que no estén ya contigo. Devuelve cuántos llegan y la frase."""
    j = p.j
    if not j.banda:
        return 0, tr("No tienes a nadie en la banda todavía.")
    if j.veh and p.mundo.tipo == "mar":
        return 0, tr("En mitad del mar no pueden llegar hasta ti.")
    aqui = {getattr(e, "bid", None) for e in miembros_presentes(p)}
    de_baja = sum(1 for f in p.banda_fichas() if f.get("baja", 0) >= p.dia and f["id"] not in aqui)      # los heridos en un golpe no acuden hasta curarse
    faltan = j.banda - len(miembros_presentes(p)) - de_baja
    if faltan <= 0:
        return 0, tr("Ya está toda tu gente contigo.") + (tr(' {v} de baja, curándose.').format(v=(tr('Falta uno, que está') if de_baja == 1 else tr('Faltan {de_baja}, que están').format(de_baja=(de_baja)))) if de_baja else "")
    for _ in range(faltan):
        a = p.crear_aliado()
        a.nombre = tr('Uno de {banda_nombre}').format(banda_nombre=(j.banda_nombre))
        a.salud = 95.0
        a.arma = random.choice(["pistola", "pistola", "bate", "navaja"])
        a.de_banda = True
    p.banda_ligar()                                              # cada uno es alguien de tu gente, con su nombre
    p.son("notificacion", cat="interfaz", vol=0.5)
    return faltan, tr('{v} {faltan} de {banda_nombre} y se {v2} a tu lado.').format(v=(tr('Llega') if faltan == 1 else tr('Llegan')), faltan=(faltan), banda_nombre=(j.banda_nombre), v2=(tr('pone') if faltan == 1 else tr('ponen')))


def despedir(p):
    for a in miembros_presentes(p):
        p.personas.remove(a)
    return tr("Tu gente se dispersa. Vuelven cuando los llames.")


def paga(p):
    """Cada medianoche: sueldo de la banda. Si no hay dinero, se va uno."""
    j = p.j
    if not j.banda:
        return
    if not j.territorios:
        j.banda = 0
        despedir(p)
        p.decir(tr("Te has quedado sin territorios y tu banda se ha disuelto."))
        return
    j.banda = min(j.banda, cupo(j))
    total = int(p.precio("sueldo_banda", SUELDO) * p.banda_paga_factor()) * j.banda      # la paga que hayas elegido (capo.py)
    if j.dinero >= total:
        j.dinero -= total
        p.decir(tr('Pagas {total} euros a {banda_nombre}.').format(total=(total), banda_nombre=(j.banda_nombre)))
    else:
        p.decir(p.banda_impago() + tr(' Quedan {banda}.').format(banda=(j.banda)))         # se va el menos leal, y los demás se enfadan (capo.py)
        p.rec_impago()


def alias_de(j):
    """Cómo te llaman los tuyos y la calle cuando eres jefe de banda: tu alias, o tu nombre si no tienes."""
    return getattr(j, "alias", "") or j.nombre


def menu_banda(p, Menu, Opcion, EntradaTexto):
    app = p.app
    j = p.j

    def apodar():
        from . import gente, registro

        def hecho(t):
            t = " ".join(t.split())[:30]
            j.alias = t
            if t:
                registro.ocultar(t)
                app.decir(tr('Desde hoy, en la calle eres {t}. Los tuyos te llamarán así.').format(t=(t)), True)
            else:
                app.decir(tr("Sin alias: te llaman por tu nombre."), True)
        app.abrir(EntradaTexto(app, tr("Tu alias en la calle"), hecho, inicial=getattr(j, "alias", ""), maximo=30,
                               ayuda=tr("El mote con el que te conocen como jefe: lo dicen los de tu banda al hablarte y quien se une a ella. "
                                        "Tabulador propone motes. Si lo dejas vacío, te llaman por tu nombre."),
                               propuestas=lambda: gente.lista("apodos")))

    def nombrar():
        def hecho(t):
            t = " ".join(t.split())[:30]
            if t:
                j.banda_nombre = t
                app.decir(tr('Tu banda se llama ahora {t}.').format(t=(t)), True)
        app.abrir(EntradaTexto(app, tr("Nombre de tu banda"), hecho, maximo=30, ayuda=tr("Así la llamarán en la calle.")))

    def hacer(f):
        def g():
            r = f(p)
            texto = r[1] if isinstance(r, tuple) else r
            if isinstance(r, tuple) and r[0] is False and texto:
                app.son("error")
            if texto:
                app.decir(texto, True)
        return g
    m = Menu(app, lambda: tr('Tu banda: {v}. {banda} de {cupo}').format(v=(j.banda_nombre or tr('sin nombre')), banda=(j.banda), cupo=(cupo(j)))
             + (tr('. Tu alias: {alias}').format(alias=(j.alias)) if getattr(j, "alias", "") else ""), [
        Opcion(lambda: tr('Reclutar a alguien: {precio} euros. Tienes {dinero}').format(precio=(p.precio('recluta', PRECIO_RECLUTA)), dinero=(j.dinero)), hacer(reclutar),
               ayuda=tr('Cada territorio te deja mantener a uno más, hasta {TOPE_BANDA}. Cada miembro cobra cada medianoche lo que diga la paga de la banda; si no puedes pagar, el menos leal se va y los demás se enfadan.').format(TOPE_BANDA=(tope_banda()))),
        Opcion(tr("Llamar a tu banda"), hacer(llamar), ayuda=tr("Acuden a donde estés, te siguen a pie, suben contigo al vehículo y pelean a tu lado.")),
        Opcion(tr("Tu gente, uno por uno: lo que vale cada cual"), lambda: __import__("juego.golpes", fromlist=["x"]).menu_gente(p),
               ayuda=tr("El nombre de cada uno y su puntería, su conducción, sus nervios y su lealtad. Es lo que cuenta cuando preparas un golpe.")),
        Opcion(tr("Cómo funcionan los golpes preparados"), lambda: __import__("juego.golpes", fromlist=["x"]).como_funciona(p),
               ayuda=tr("Antes de atracar un banco, un local o un proveedor puedes repartir papeles entre los tuyos: conductor, vigilante, escolta, el de la caja y tirador.")),
        Opcion(lambda: tr("Chófer: ") + (f"{p.chofer['nombre']}" if p.chofer else tr('que venga uno de los tuyos a recogerte, {precio} euros').format(precio=(p.precio('chofer', 80)))),
               lambda: __import__("juego.misvehiculos", fromlist=["x"]).menu_chofer(p),
               ayuda=tr("Uno de tu banda viene con un vehículo de tu garaje o con uno de la banda y conduce él hasta el destino que marques en el GPS. Tú vas de pasajero y puedes disparar.")),
        Opcion(lambda: p.banda_paga_txt(), lambda: app.decir(p.banda_cambiar_paga(), True),
               ayuda=tr("Intro cambia entre baja, normal y alta. Con la baja ahorras, pero se te van enfriando; con la alta, cada día te son algo más leales. "
                     "Si un día no te llega para pagar, el menos leal se va y los demás se enfadan. Alguien muy poco leal puede traicionarte.")),
        Opcion(tr("Mandarlos a casa"), hacer(despedir), ayuda=tr("Los que van contigo se dispersan. Siguen en tu banda y cobrando, y vuelven cuando los llames.")),
        Opcion(tr("Cambiar el nombre de la banda"), nombrar, ayuda=tr("Escribes el nombre nuevo, de hasta treinta letras. Es como te llaman en la calle.")),
        Opcion(lambda: tr('Tu alias en la calle: {v}').format(v=(j.alias or tr('ninguno, te llaman por tu nombre'))), apodar,
               ayuda=tr("Tu mote como jefe, de hasta treinta letras: los de tu banda te llaman así, y quien se une a ella también. Vacío, te llaman por tu nombre.")),
    ])
    app.abrir(m)


# ============================================================ interior de las casas
HABITACIONES = [
    (tr("la entrada"), tr("Un perchero y las llaves colgadas. Por aquí se sale a la calle."), "salir"),
    (tr("el salón"), tr("Un sofá, la tele y una ventana a la calle."), "salon"),
    (tr("la cocina"), tr("La nevera zumba. Huele a café."), "cocina"),
    (tr("el baño"), tr("Un espejo y una ducha."), "bano"),
    (tr("el dormitorio"), tr("La cama está hecha. Aquí se duerme y se guarda la partida."), "dormitorio"),
]


# Amueblar la casa: cada mueble va a una habitación, cambia cómo es y mejora lo que se hace en ella.
# (id, habitación, nombre, precio, cómo queda la habitación, qué mejora)
MUEBLES = [
    ("recibidor", "salir", tr("Plantas, cuadros y una alfombra"), 300, tr("Hay plantas, cuadros en las paredes y una alfombra que da gusto pisar."),
     tr("La casa es más acogedora: al dormir aquí te levantas con algo más de ánimo.")),
    ("sofa", "salon", tr("Un sofá grande y una tele nueva"), 600, tr("Un sofá en el que caben cuatro y una tele enorme."),
     tr("Ver la tele te sube el ánimo el doble.")),
    ("cocina", "cocina", tr("Cocina equipada y nevera grande"), 700, tr("Cocina nueva, con horno, y una nevera grande y llena."),
     tr("Lo que te preparas en casa te da el doble de salud, se te quema menos y en la nevera cabe más.")),
    ("banera", "bano", tr("Baño reformado, con bañera"), 500, tr("Azulejos nuevos y una bañera en la que te puedes estirar."),
     tr("Un baño largo te sube más el ánimo y te quita algún golpe.")),
    ("cama", "dormitorio", tr("Una cama de las buenas"), 800, tr("Una cama ancha, con un colchón de los caros."),
     tr("Dormir aquí te sube bastante el ánimo.")),
    ("taller", "garaje", tr("Un banco de herramientas"), 900, tr("En la pared, un banco de herramientas bien surtido."),
     tr("Mientras duermes, los vehículos guardados en este garaje se quedan reparados.")),
]


def muebles_de(j, lugar):
    return j.muebles.get(lugar.id, [])


def menu_muebles(p, lugar, Menu, Opcion):
    """Comprar muebles para una casa tuya."""
    app, j = p.app, p.j
    tengo = j.muebles.setdefault(lugar.id, [])

    def comprar(mueble):
        def f():
            if mueble[0] in tengo:
                return app.decir(tr("Eso ya lo tienes puesto."), True)
            if not p.pagar(mueble[3]):
                return
            tengo.append(mueble[0])
            p.cambiar_animo(3)
            app.decir(tr('Te lo traen y lo dejan puesto. {v} {v2}').format(v=tr(mueble[4]), v2=tr(mueble[5])), True)
            comun = p.casa_comun() if hasattr(p, "casa_comun") else None
            if comun is not None and comun.id == lugar.id:       # te lo había pedido quien vive contigo: se entera al momento
                p.peticion_cumplida("mueble")
            m.refrescar(False)
        return f

    def ops():
        lista = []
        for mu in MUEBLES:
            if mu[1] == "garaje" and not int(lugar.get("garaje", 0)):
                continue
            if mu[0] in tengo:
                lista.append(Opcion(tr('{v}: ya lo tienes. {v2}').format(v=tr(mu[2]), v2=tr(mu[5])), ayuda=tr("Ya está puesto en esta casa. No hace falta comprarlo otra vez.")))
            else:
                lista.append(Opcion(tr('{v}: {v2} euros').format(v=tr(mu[2]), v2=(mu[3])), comprar(mu), ayuda=tr(mu[5])))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
        return lista
    m = Menu(app, lambda: tr('Amueblar {nombre}. Tienes {dinero} euros').format(nombre=(lugar.nombre), dinero=(j.dinero)), ops,
             intro=tr("Cada mueble va a una habitación y mejora lo que haces en ella. Se quedan en esta casa"))
    app.abrir(m)


def al_dormir_en_casa(p, lugar):
    """Lo que añaden los muebles a una noche en casa. Devuelve el texto que se suma al de haber dormido."""
    j = p.j
    tengo = muebles_de(j, lugar)
    texto = ""
    extra = (8 if "cama" in tengo else 0) + (3 if "recibidor" in tengo else 0)
    if extra:
        p.cambiar_animo(extra)
        texto += tr(" Has dormido de maravilla.")
    if "taller" in tengo:
        arreglados = 0
        from types import SimpleNamespace
        for d in j.garajes.get(lugar.id, []):
            modelo = p.modelos.get(d.get("modelo"))
            if not modelo:
                continue
            # al máximo de verdad: con el blindaje del taller, más que el modelo de serie (antes salía por debajo del cien por cien)
            maximo = float(modelo["salud"]) * factor_blindaje(SimpleNamespace(mejoras=dict(d.get("mejoras") or {})))
            if float(d.get("salud", 0)) < maximo:
                d["salud"] = maximo
                arreglados += 1
        if arreglados:
            texto += tr(' En el garaje, {arreglados} {v}.').format(arreglados=(arreglados), v=(tr('vehículo ha quedado reparado') if arreglados == 1 else tr('vehículos han quedado reparados')))
    return texto


class Interior:
    """Recorrer una casa tuya: flechas izquierda y derecha para ir de una habitación a otra, Intro para usarla."""
    pausa_mundo = True
    pared = tr("Pared. No hay más casa por ahí.")

    def ayuda(self):
        return tr("Estás dentro de tu casa. Flechas izquierda y derecha para ir de una habitación a otra, Intro para usar la habitación en la que estás y Escape para salir. "
                  "Sin salir, la M abre el móvil, la V dice cómo estás y la T la hora.")

    def __init__(self, p, lugar, acciones):
        self.p, self.app, self.l, self.acciones = p, p.app, lugar, acciones
        self.habitaciones = list(HABITACIONES)
        if int(lugar.get("garaje", 0)):
            self.habitaciones.append((tr("el garaje"), tr('Sitio para {int} vehículos. Huele a gasolina.').format(int=(int(lugar.get('garaje', 0)))), "garaje"))
        self.muebles = muebles_de(p.j, lugar)
        for mu in MUEBLES:                                # lo que has comprado se nota al entrar en cada habitación
            if mu[0] in self.muebles:
                self.habitaciones = [(n, d + " " + tr(mu[4]), q) if q == mu[1] else (n, d, q) for n, d, q in self.habitaciones]
        self.i = 0

    def al_entrar(self):
        self.app.mez.entorno = "interior"
        nombre, desc, _ = self.habitaciones[self.i]
        if getattr(self, "ya_dentro", False):                    # al volver del menú de la cocina: solo dónde estás
            self.app.decir(f"{nombre.capitalize()}.", True)
            return
        self.ya_dentro = True
        self.app.decir(tr('{nombre}, por dentro. Estás en {nombre2}. {desc} Flechas izquierda y derecha para moverte por la casa, Intro para usar la habitación, Escape para salir.').format(nombre=(self.l.nombre), nombre2=(nombre), desc=(desc)), True)

    def _decir(self):
        nombre, desc, _ = self.habitaciones[self.i]
        self.app.decir(tr('{capitalize}. {desc} {v} de {len}.').format(capitalize=(nombre.capitalize()), desc=(desc), v=(self.i + 1), len=(len(self.habitaciones))), True)

    def tecla(self, ev):
        k = ev.key
        if k in (pygame.K_RIGHT, pygame.K_DOWN, pygame.K_LEFT, pygame.K_UP):
            paso = 1 if k in (pygame.K_RIGHT, pygame.K_DOWN) else -1
            nuevo = self.i + paso
            if not 0 <= nuevo < len(self.habitaciones):
                self.app.son("menu_borde")
                self.app.decir(self.pared, True)
                return
            self.i = nuevo
            for n in range(3):                          # tres pasos sobre el suelo de casa
                self.app.son(("paso_acera0", "paso_acera1")[n % 2], vol=0.5, pan=0.5 * paso).eco = True
            self._decir()
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self._usar()
        elif k == pygame.K_ESCAPE:
            self.app.son("puerta_entrar")
            self.app.cerrar(self)
        elif k == pygame.K_F1:
            self.app.decir(self.ayuda(), True)
        elif k == pygame.K_m:                           # sin salir de casa: el móvil, cómo estás y la hora (issue 29)
            from . import menus_juego
            self.app.son("movil")
            menus_juego.movil(self.p)
        elif k == pygame.K_v:
            if getattr(ev, "mod", 0) & pygame.KMOD_SHIFT:
                self.app.decir(self.p.necesidades_txt().strip() or tr("La vida realista está desactivada: no pasas hambre, sed ni sueño. Se activa en Opciones, Combate y dificultad."), True)
            else:
                self.p.estado()
        elif k == pygame.K_t:
            p = self.p
            self.app.decir(tr("Son las {hora}, {fecha}. {cielo} {dia_txt}").format(hora=p.hora_txt(), fecha=p.fecha_txt(), cielo=tr('Llueve.') if p.lluvia else tr('Cielo despejado.'), dia_txt=p.dia_txt()).strip(), True)
        else:
            self._decir()

    def _usar(self):
        p, j, app = self.p, self.p.j, self.app
        que = self.habitaciones[self.i][2]
        if que == "salir":
            app.son("puerta_entrar")
            app.cerrar(self)
        elif que == "salon":
            p.pasar_horas(1)
            p.cambiar_animo(8 if "sofa" in self.muebles else 4)
            app.son("pasan_horas")
            app.decir(tr('Te {v} a ver la tele. Te sube el ánimo. Son las {hora_txt}.').format(v=(tr('hundes en el sofá') if 'sofa' in self.muebles else tr('sientas un rato')), hora_txt=(p.hora_txt())), True)
        elif que == "cocina":
            from . import menus_cocina                           # con algo en la despensa o comida encima, el menú de la cocina; sin nada, lo de siempre
            menus_cocina.usar_cocina(p, self.l, self._picar_algo)
        elif que == "bano":
            app.son("salpicadura", vol=0.5)
            p.ha_duchado()
            p.ha_bebido(100)
            if "banera" in self.muebles:
                p.cambiar_animo(5)
                j.salud = min(j.salud_max, j.salud + 10)
                app.decir(tr("Un baño largo, con el agua bien caliente. Sales como nuev[o|a]."), True)
            else:
                p.cambiar_animo(2)
                app.decir(tr("Una ducha caliente. Sales como nuev[o|a]."), True)
        elif que == "dormitorio":
            self.acciones["descansar"]()
        elif que == "garaje":
            self.acciones["garaje"]()

    def _picar_algo(self, extra=""):
        """Lo de siempre en la cocina: una vez al día, comer algo de lo que haya por casa. No gasta nada de la despensa."""
        p, j, app = self.p, self.p.j, self.app
        if getattr(j, "dia_nevera", -1) == p.dia:
            app.decir(tr("Hoy ya te has comido lo que había por casa. Mañana habrá más.") + extra, True)
        else:
            j.dia_nevera = p.dia
            j.salud = min(j.salud_max, j.salud + (50 if "cocina" in self.muebles else 25))
            p.son("comer", cat="interfaz")
            p.ha_bebido(100)                                 # en casa, el agua del grifo no falta
            app.decir(tr('Te preparas {v}. Salud {int}.{necesidades_txt}{extra}').format(v=(tr('una buena comida en tu cocina nueva') if 'cocina' in self.muebles else tr('algo con lo que hay en la nevera')), int=(int(j.salud)), necesidades_txt=(p.necesidades_txt()), extra=(extra)), True)

    def actualizar(self, dt):
        pass

    def cerrado(self):
        pass


# ============================================================ interior del resto de lugares
# Cada sala: (nombre, descripción, qué hace Intro). Las acciones:
#   salir: a la calle del menú.  mostrador: vuelve al menú del lugar, que es donde se compra o se pide.
#   sentarse: pasa media hora y sube el ánimo.  escuchar: oyes una conversación.  aseo: te refrescas.  mirar: solo se describe.
#   tablon_policia, tablon_premios, tablon_ofertas: tablones que se leen, y dicen lo que hay hoy.
_PUERTA = (tr("la puerta"), tr("Por aquí se sale."), "salir")
_ASEO = (tr("los aseos"), tr("Un lavabo y un espejo."), "aseo")
SALAS = {
    "bar": [_PUERTA, (tr("la barra"), tr("Tazas, botellas y la cafetera silbando. Aquí se pide."), "mostrador"), (tr("las mesas"), tr("Cuatro mesas y gente hablando bajo."), "escuchar"),
            (tr("la máquina del rincón"), tr("Una tragaperras que canta sola. Intro para echar unas monedas."), "tragaperras"), _ASEO],
    "taberna": [_PUERTA, (tr("la barra"), tr("Madera vieja y barriles. Aquí se pide."), "mostrador"), (tr("las mesas del fondo"), tr("Bancos corridos y partidas de cartas."), "escuchar"), _ASEO],
    "comida": [_PUERTA, (tr("el mostrador"), tr("La carta colgada y la caja. Aquí se pide."), "mostrador"), (tr("el comedor"), tr("Mesas con mantel de papel. Huele a fritura."), "sentarse"), _ASEO],
    "pizzeria": [_PUERTA, (tr("el mostrador"), tr("El horno al fondo y la caja. Aquí se pide."), "mostrador"), (tr("el comedor"), tr("Mesas pequeñas y una tele encendida."), "sentarse"), _ASEO],
    "tienda": [_PUERTA, (tr("el mostrador"), tr("La caja y el tendero. Aquí se compra."), "mostrador"), (tr("los pasillos"), tr("Estanterías hasta el techo, latas y cajas."), "mirar"), (tr("la trastienda"), tr("Una cortina y cajas apiladas. No te dejan pasar."), "escuchar")],
    "farmacia": [_PUERTA, (tr("el mostrador"), tr("Batas blancas y cajas de medicinas. Aquí se compra."), "mostrador"), (tr("la zona de espera"), tr("Dos sillas y una báscula."), "sentarse")],
    "armeria": [_PUERTA, (tr("el mostrador"), tr("Un cristal grueso y el armero detrás. Aquí se compra."), "mostrador"), (tr("las vitrinas"), tr("Armas colgadas tras un cristal. Huele a aceite."), "mirar"),
                (tr("la galería de tiro"), tr("Un pasillo largo con dianas al fondo."), "mirar")],
    "hospital": [_PUERTA, (tr("la recepción"), tr("Un mostrador y gente esperando. Aquí te atienden."), "mostrador"), (tr("la sala de espera"), tr("Sillas de plástico y una máquina de café."), "sentarse"),
                 (tr("el pasillo de consultas"), tr("Puertas numeradas y pasos rápidos."), "escuchar"), _ASEO],
    "comisaria": [_PUERTA, (tr("el mostrador de guardia"), tr("Un agente tras una mampara. Aquí te atienden."), "mostrador"), (tr("los bancos de espera"), tr("Un banco atornillado al suelo."), "escuchar"),
                  (tr("el tablón"), tr("Carteles de personas buscadas y avisos. Intro para leerlo."), "tablon_policia")],
    "taller": [_PUERTA, (tr("la oficina"), tr("Un mostrador con facturas. Aquí se encarga el trabajo."), "mostrador"), (tr("el foso"), tr("Un coche levantado y herramientas por el suelo."), "mirar"),
               (tr("el almacén de piezas"), tr("Neumáticos apilados y cajas de recambios."), "escuchar")],
    "desguace": [_PUERTA, (tr("la caseta"), tr("Una mesa y una báscula. Aquí se trata."), "mostrador"), (tr("el patio de chatarra"), tr("Coches apilados de tres en tres."), "mirar")],
    "casino": [_PUERTA, (tr("las mesas de juego"), tr("Fichas, cartas y la ruleta girando. Aquí se juega."), "mostrador"), (tr("la sala de máquinas"), tr("Filas de tragaperras con sus musiquillas."), "mirar"),
               (tr("el bar del casino"), tr("Sillones y copas. Aquí se habla de dinero."), "escuchar"), _ASEO],
    "negocio": [_PUERTA, (tr("el despacho"), tr("Una mesa y los libros de cuentas. Aquí se trata."), "mostrador"), (tr("el local"), tr("El negocio en marcha, con su gente."), "escuchar")],
    "periodico": [_PUERTA, (tr("la redacción"), tr("Teclados, teléfonos y prisas. Aquí te atienden."), "mostrador"), (tr("la sala de rotativas"), tr("Máquinas enormes y olor a tinta."), "mirar"),
                  (tr("el archivo"), tr("Estanterías con periódicos viejos."), "escuchar")],
    "banco": [_PUERTA, (tr("la ventanilla"), tr("Un cristal y un empleado. Aquí se opera."), "mostrador"), (tr("la cola"), tr("Gente esperando con papeles en la mano."), "escuchar"),
              (tr("la puerta de la cámara"), tr("Acero, y un guardia delante."), "mirar")],
    "loteria": [_PUERTA, (tr("la ventanilla"), tr("Décimos colgados y un bombo pequeño. Aquí se compra."), "mostrador"), (tr("el tablón de premios"), tr("Los números premiados de la semana. Intro para leerlo."), "tablon_premios")],
    "empenos": [_PUERTA, (tr("el mostrador"), tr("Una reja y una lupa. Aquí se trata."), "mostrador"), (tr("las estanterías"), tr("Relojes, guitarras y televisores de otros."), "mirar")],
    "pescaderia": [_PUERTA, (tr("el mostrador"), tr("Hielo picado y pescado fresco. Aquí se vende y se compra."), "mostrador"), (tr("la cámara"), tr("Frío y cajas de corcho."), "mirar")],
    "gimnasio": [_PUERTA, (tr("la recepción"), tr("Un mostrador con toallas. Aquí te apuntas."), "mostrador"), (tr("la sala de pesas"), tr("Hierros que suenan y gente resoplando."), "escuchar"),
                 (tr("el ring"), tr("Lona, cuerdas y un saco colgado."), "mirar"), (tr("los vestuarios"), tr("Bancos, taquillas y duchas."), "aseo")],
    "ropa": [_PUERTA, (tr("la caja"), tr("El mostrador y las bolsas. Aquí se paga."), "mostrador"), (tr("los percheros"), tr("Filas de ropa colgada."), "mirar"), (tr("los probadores"), tr("Cortinas y espejos."), "mirar")],
    "cine": [_PUERTA, (tr("la taquilla"), tr("La cartelera y las entradas. Aquí se compra."), "mostrador"), (tr("el vestíbulo"), tr("Huele a palomitas. Hay gente esperando."), "escuchar"), _ASEO],
    "hotel": [_PUERTA, (tr("la recepción"), tr("Un mostrador con campanilla. Aquí te atienden."), "mostrador"), (tr("el salón"), tr("Sillones y un piano que nadie toca."), "sentarse"),
              (tr("el pasillo de habitaciones"), tr("Moqueta y puertas numeradas."), "escuchar"), _ASEO],
    "concesionario": [_PUERTA, (tr("la mesa del vendedor"), tr("Catálogos y un bolígrafo listo. Aquí se compra."), "mostrador"), (tr("la exposición"), tr("Coches nuevos, brillantes, con olor a tapicería."), "mirar")],
    "nautica": [_PUERTA, (tr("el mostrador"), tr("Cartas de navegación y cabos. Aquí se compra."), "mostrador"), (tr("la exposición"), tr("Motores fueraborda y un velero pequeño en seco."), "mirar")],
    "club": [_PUERTA, (tr("la barra"), tr("Luces bajas y música fuerte. Aquí te atienden."), "mostrador"), (tr("la pista"), tr("Gente bailando apretada."), "escuchar"), _ASEO],
    "proveedor": [_PUERTA, (tr("la mesa"), tr("Una mesa, una silla y pocas palabras. Aquí se trata."), "mostrador"), (tr("el cuarto de atrás"), tr("Una puerta cerrada. Mejor no preguntar."), "mirar")],
    "empleo": [_PUERTA, (tr("la mesa de atención"), tr("Un ordenador y un montón de impresos. Aquí te atienden."), "mostrador"), (tr("el tablón de ofertas"), tr("Papeles con trabajos, sujetos con chinchetas. Intro para leerlo."), "tablon_ofertas"),
               (tr("la sala de espera"), tr("Sillas en fila y gente con carpetas."), "escuchar")],
    "academia": [_PUERTA, (tr("la secretaría"), tr("Matrículas y horarios. Aquí te apuntas."), "mostrador"), (tr("el aula"), tr("Pupitres y una pizarra."), "sentarse"), (tr("el pasillo"), tr("Alumnos comentando el examen."), "escuchar")],
    "ong": [_PUERTA, (tr("la mesa de acogida"), tr("Una voluntaria con una lista. Aquí te atienden."), "mostrador"), (tr("el almacén"), tr("Cajas de comida y ropa doblada."), "mirar")],
    "protectora": [_PUERTA, (tr("la oficina"), tr("Fichas de animales y una mesa. Aquí te atienden."), "mostrador"), (tr("las jaulas"), tr("Ladridos y rabos golpeando la reja."), "mirar")],
}
OIDO = [
    tr("Dos hombres discuten de fútbol sin escucharse."), tr("Una mujer cuenta que le han subido el alquiler otra vez."), tr("Alguien dice en voz baja que anoche hubo jaleo en el puerto."),
    tr("Hablan de un coche robado que apareció quemado en las afueras."), tr("Un viejo asegura que antes esto era otra cosa."), tr("Una pareja decide adónde ir de vacaciones, sin ponerse de acuerdo."),
    tr("Dicen que la policía anda preguntando por el barrio."), tr("Alguien cuenta que al del estanco le tocó un pellizco en la lotería."), tr("Dos chavales hablan de una carrera de coches de esta noche."),
    tr("Una señora se queja de que ya no se puede aparcar en ningún sitio."), tr("Comentan que va a llover toda la semana."), tr("Alguien busca trabajo y pregunta si saben de algo."),
    tr("Un hombre presume de lo que pescó el domingo. Nadie le cree."), tr("Hablan de un negocio que cambió de dueño de un día para otro."), tr("Dos amigas se ríen de algo que no llegas a oír."),
    tr("Alguien dice que no se fía de los bancos, que el dinero, en casa."),
]


QUE_HACE = {"salir": tr("sales del recorrido"), "mostrador": tr("te atienden: vuelves al menú del lugar, donde están las opciones para comprar o pedir"),
            "sentarse": tr("te sientas un rato"), "escuchar": tr("pones el oído a lo que se habla"), "aseo": tr("te refrescas"), "tragaperras": tr("echas unas monedas"),
            "mirar": tr("te lo describe"), "tablon_policia": tr("lees los carteles y los avisos de hoy"), "tablon_premios": tr("lees los números premiados"),
            "tablon_ofertas": tr("lees las ofertas de trabajo")}
ACERCARSE = (tr("Te acercas a {}"), tr("Vas hasta {}"), tr("Te plantas ante {}"), tr("Caminas hasta {}"))
ATIENDEN = (tr(": aquí te atienden"), tr(". Te atienden"), tr(": te toca"))


def _con_a(frase):
    """«a el mostrador» se dice «al mostrador»."""
    return frase.replace(" a el ", " al ")


def tablon_policia(p):
    """Lo que dice hoy el tablón de la comisaría: si te buscan y lo que te costaría, las bandas de la ciudad y los sucesos del día."""
    j, s = p.j, p.j.stats
    if p.en_servidor and p.sv.get("recompensa"):
        yo = tr('Hay un cartel con tu cara: ofrecen {recompensa} euros por tu cabeza.').format(recompensa=(p.sv['recompensa']))
    elif j.estrellas:
        yo = random.choice([tr("En el cartel más reciente reconoces tu cara"), tr("Hay un cartel nuevo, y el del retrato eres tú"), tr("Uno de los carteles lleva tu descripción")]) + \
            tr(': búsqueda de nivel {estrellas}. Si te cogen ahora, la multa rondaría los {coste_multa} euros.').format(estrellas=(j.estrellas), coste_multa=(p.coste_multa()))
    else:
        yo = random.choice([tr("Repasas las caras de los carteles: ninguna es la tuya. No te busca nadie."), tr("Ningún cartel lleva tu cara: no te buscan."),
                            tr("Buscas tu nombre en la lista de personas buscadas y no está: no te buscan.")])
    if s.get("detenciones"):
        yo += tr(' Tu ficha: {detenciones} {v}.').format(detenciones=(s['detenciones']), v=(tr('detención') if s['detenciones'] == 1 else tr('detenciones')))
    avisos = []
    if not p.en_servidor:
        for b in p.mundo.barrios:
            banda = b["id"] not in j.territorios and p.banda_de_barrio(b)
            if banda:
                avisos.append(tr('Se busca a miembros de {banda}, que se mueven por {nombre}.').format(banda=(banda), nombre=(b['nombre'])))
        if j.amenaza:
            avisos.append(tr('Aviso de la jefatura: se esperan enfrentamientos entre bandas en {v}.').format(v=(_nombre_barrio(p, j.amenaza['territorio'])[0])))
    ev = getattr(p, "evento", None)
    if ev:
        avisos.append({"atraco": tr("Aviso de última hora: están atracando a alguien cerca de aquí."), "banda": tr("Aviso de última hora: pandilleros alborotando en una calle cercana."),
                       "maletin": tr("Objetos perdidos: alguien ha denunciado hoy la pérdida de un maletín por esta zona.")}.get(ev.get("tipo"))
                       or (tr('Aviso de última hora: {nombre}, cerca de aquí.').format(nombre=(ev["suceso"]["nombre"])) if (ev.get("suceso") or {}).get("nombre") else ""))
    if p.dia_txt():
        avisos.append(tr("Parte del día: ") + p.dia_txt())
    if s.get("vehiculos_robados", 0) > 2:
        avisos.append(tr('Robos de vehículos sin resolver: {vehiculos_robados}.').format(vehiculos_robados=(s['vehiculos_robados'])))
    if s.get("atracos", 0):
        avisos.append(tr("Se recuerda a los comercios que refuercen sus alarmas tras los últimos atracos."))
    avisos.append(tr("Recorte del periódico: ") + p.noticia())
    avisos.append(random.choice([tr("Recuerda: la multa, pagada en el acto, sale más barata que la de comisaría."), tr("Un aviso pide testigos de una carrera ilegal nocturna."),
                                 tr("Se han encontrado unas llaves: preguntar en el mostrador de guardia."), tr("La policía local busca voluntarios para la verbena. Nadie se ha apuntado."),
                                 tr("Campaña de tráfico: este mes, más controles de velocidad."), tr("Un cartel descolorido ofrece recompensa por un loro que sabe decir palabrotas.")]))
    avisos = [a for a in avisos if a]
    random.shuffle(avisos)
    return yo + " " + " ".join(avisos[:2])


def tablon_premios(p):
    """El tablón de la administración de lotería: los números que han salido de verdad en los últimos sorteos, y el bote."""
    from . import loteria
    ult = loteria.ultimo_celebrado(p)
    salidos = [tr('{v}, el {cifras}').format(v=(tr('hoy') if d == p.dia else tr('ayer') if d == p.dia - 1 else tr('hace ') + str(p.dia - d) + tr(' días')), cifras=(loteria.cifras(loteria.premiado(p, d))))
               for d in range(ult, max(0, ult - 3), -1)]
    return (tr("Números premiados: ") + "; ".join(salidos) + ". " if salidos else tr("Todavía no se ha celebrado ningún sorteo. ")) + loteria.estado_txt(p) + "."


def tablon_ofertas(p):
    """El tablón de la oficina de empleo: unas cuantas jornadas de las que hay, con su paga de verdad."""
    ofertas = [x for x in p.datos.get("jornadas", []) if x.get("nombre")]
    if not ofertas:
        return tr("Hoy el tablón está vacío.")
    return (tr("Lees algunas ofertas. ") + " ".join(tr('{nombre}: {int} euros.').format(nombre=(x['nombre']), int=(int(x.get('paga', 0)))) for x in random.sample(ofertas, min(3, len(ofertas))))
            + tr(" Para apuntarte, en la mesa de atención."))


TABLONES = {"tablon_policia": tablon_policia, "tablon_premios": tablon_premios, "tablon_ofertas": tablon_ofertas}


def salas_de(lugar):
    return SALAS.get(getattr(lugar, "tipo", ""))


class Local(Interior):
    """Recorrer por dentro una tienda, un bar, un banco o cualquier otro local: de sala en sala con las flechas."""

    def __init__(self, p, lugar):
        self.p, self.app, self.l, self.acciones = p, p.app, lugar, {}
        self.habitaciones = list(salas_de(lugar) or [_PUERTA])
        for pers in personas_aqui(p, lugar):                  # la gente de tu vida social está en su sitio, no solo en el móvil
            if not (p.acompanante and p.acompanante["pid"] == pers["id"]):
                self.habitaciones.insert(2, (tr('donde está {nombre}').format(nombre=(pers['nombre'])), pers["desc"], ("persona", pers["id"])))
        self.i = 0
        self.oidas = 0
        self.pared = random.choice((tr("Pared. El local no sigue por ahí."), tr("Pared. No hay más local por ese lado."), tr("Pared. Por ahí no hay nada más.")))

    def ayuda(self):
        nombre, _, que = self.habitaciones[self.i]
        aqui = tr("te acercas a hablar") if isinstance(que, tuple) else QUE_HACE.get(que, tr("te lo describe"))
        atiende = next((n for n, _, q in self.habitaciones if q == "mostrador"), None)
        return (tr('Estás recorriendo {nombre} por dentro. Flechas izquierda y derecha para ir de un sitio a otro, Intro para usar el sitio donde estás y Escape para volver al menú del lugar. Ahora estás en {nombre2}: con Intro, {aqui}.').format(nombre=(self.l.nombre), nombre2=(nombre), aqui=(aqui))
                + (tr(' Para comprar, pedir o que te atiendan, ve a {atiende} y pulsa Intro, o sal con Escape: las opciones están en el menú del lugar.').format(atiende=(atiende)) if atiende and que != "mostrador" else ""))

    def al_entrar(self):
        self.app.mez.entorno = "nave" if self.l.tipo in ("taller", "desguace", "concesionario", "nautica", "gimnasio") else "interior"
        nombre, desc, _ = self.habitaciones[self.i]
        self.app.decir(tr('{nombre}, por dentro. Estás en {nombre2}. {desc} Flechas izquierda y derecha para moverte, Intro para usar el sitio donde estás, Escape para volver.').format(nombre=(self.l.nombre), nombre2=(nombre), desc=(desc)), True)

    def _usar(self):
        p, app = self.p, self.app
        nombre, desc, que = self.habitaciones[self.i]
        if isinstance(que, tuple):
            from . import menus_adultos
            menus_adultos.vida_social(p, directo=que[1])
        elif que == "mostrador":                                 # donde te atienden: se dice, y se vuelve al menú del lugar
            for n in range(2):
                app.son(("paso_acera0", "paso_acera1")[n % 2], vol=0.5).eco = True
            k = app.pila.index(self) if self in app.pila else 0
            debajo = app.pila[k - 1] if k > 0 else None
            frase = _con_a(random.choice(ACERCARSE).format(nombre)) + random.choice(ATIENDEN)
            if debajo is not None and hasattr(debajo, "antes"):
                debajo.antes = frase                              # el menú del lugar lo dice delante de su título
                app.cerrar(self)
            else:
                app.cerrar(self)
                app.decir(frase + ".")
        elif que == "salir":
            app.son("menu_atras")
            app.cerrar(self)
        elif que in TABLONES:
            app.son("cursor_mapa", vol=0.6)
            app.decir(TABLONES[que](p), True)
        elif que == "sentarse":
            p.pasar_horas(0.5)
            p.cambiar_animo(2)
            app.son("pasan_horas")
            app.decir(tr('Te sientas un rato. Son las {hora_txt}.').format(hora_txt=(p.hora_txt())), True)
        elif que == "escuchar":
            self.oidas += 1
            app.son("murmullo", vol=0.5)
            app.decir(tr("Pones el oído. ") + random.choice(OIDO), True)
        elif que == "aseo":
            p.cambiar_animo(1)
            app.son("salpicadura", vol=0.5)
            app.decir(tr("Te lavas la cara. Mejor."), True)
        elif que == "tragaperras":
            from . import menus_juego
            menus_juego._tragaperras(p)
        else:
            app.decir(f"{nombre.capitalize()}. {desc}", True)


def con_recorrido(p, lugar, menu, Opcion):
    """Añade al menú de un local la opción de recorrerlo por dentro, antes de la de salir."""
    if not salas_de(lugar):
        return
    fuente = menu._fuente
    from .menus import SALIDAS

    def ops():
        lista = list(fuente() if callable(fuente) else fuente)
        if any(o.texto.startswith(tr("Recorrer")) for o in lista):
            return lista
        for pers in personas_aqui(p, lugar):
            if not (p.acompanante and p.acompanante["pid"] == pers["id"]):
                from . import menus_adultos
                # con el contenido para adultos va la primera, como siempre; sin él, al final, para no descolocar el menú de nadie
                pos = 0 if p.modo_adulto() else (len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista))
                lista.insert(pos, Opcion(tr('{nombre} está aquí: acercarte a hablar').format(nombre=(pers['nombre'])), lambda pid=pers["id"]: menus_adultos.vida_social(p, directo=pid),
                                       ayuda=tr("Lo mismo que desde el móvil, pero en persona: charlar, quedar, hacerle un regalo o proponerle salir a dar una vuelta contigo.")))
        if p.surtido(lugar):                                     # una tienda de comida: se recorre pasillo a pasillo, con cesta y caja
            from . import compra
            o = Opcion(tr("Recorrer el local por dentro: los pasillos, con una cesta"), lambda: p.app.abrir(compra.Tienda(p, lugar)),
                       ayuda=tr("Entras, coges una cesta y vas de un pasillo a otro con las flechas izquierda y derecha. Cada pasillo tiene lo suyo: Intro lo abre y echas a la cesta lo que quieras. "
                             "Se paga en la caja. Lo comprado te lo llevas encima, para guardarlo y cocinarlo en una casa tuya. Dentro, F1 te explica dónde estás y C te dice qué llevas en la cesta."))
        else:
            o = Opcion(tr("Recorrer el local por dentro"), lambda: p.app.abrir(Local(p, lugar)),
                       ayuda=tr("Entras y vas de una sala a otra con las flechas izquierda y derecha. En el mostrador te atienden: vuelves a este menú, que es donde se compra o se pide. Dentro, F1 te explica dónde estás."))
        lista.insert(len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista), o)
        return lista
    menu._fuente = ops
    menu.refrescar(False)


# ============================================================ sucesos de territorio
# Tener barrios llama la atención: otras bandas los quieren, alguna prefiere pactar, y la policía te pone en su lista.
def _nombre_barrio(p, ident):
    for m in p.mapas.values():
        for b in m.barrios:
            if b["id"] == ident:
                return b["nombre"], m
    return ident, None


def sucesos_territorio(p, azar=None):
    """Cada medianoche: se cumplen los plazos pendientes y, a veces, pasa algo nuevo."""
    import random
    from . import gente
    BANDAS = gente.nombres_bandas()
    azar = azar or random
    j = p.j
    # --- plazos que vencen
    a = j.amenaza
    if a and p.dia > a["dia"]:
        j.amenaza = None
        if a["territorio"] in j.territorios:
            j.territorios.remove(a["territorio"])
            j.barrios_banda[a["territorio"]] = a["banda"]          # desde ahora ese barrio es de ellos
            p.son("mision_fallo", cat="interfaz")
            p.decir(tr('No defendiste {v} y {banda} se lo ha quedado. Ya no te paga.').format(v=(_nombre_barrio(p, a['territorio'])[0]), banda=(a['banda'])))
            p.cambiar_reputacion(-4)
    r = j.redada
    if r and p.dia > r["dia"]:
        j.redada = None
        perdido = min(j.dinero, p.precio("redada_territorio", 300) * len(j.territorios))
        j.dinero -= perdido
        p.decir(tr('No arreglaste lo de la policía: una redada en tus barrios te cuesta {perdido} euros.').format(perdido=(perdido)))
    o = j.oferta_pacto
    if o and p.dia > o["dia"]:
        j.oferta_pacto = None
    if not j.territorios or not p.cfg["sucesos"] or j.amenaza or j.redada or j.oferta_pacto:
        return
    n = len(j.territorios)
    if azar.random() > 0.12 + 0.05 * min(n, 5):
        return
    banda = azar.choice(BANDAS)
    tipo = azar.choice(["ataque", "ataque", "policia"] + (["pacto", "pacto"] if n >= 3 else []))
    if tipo == "ataque" and p.rep_banda(banda) >= 30:
        return                                                    # esa banda te respeta: no toca lo tuyo
    if tipo == "ataque" and p.dia <= j.pacto_hasta:
        return                                                    # hay un pacto en vigor: nadie ataca
    if tipo == "ataque" and p.rec_activa():
        return                                                    # con la reconquista en marcha, los asaltos los lleva ella (reconquista.py): nunca dos a la vez
    if tipo == "ataque" and p.cfg["reconquista"] == "apagado" and not getattr(p, "en_servidor", False) and not p.online_activo():
        return                                                    # con la reconquista apagada nadie intenta quitarte un barrio: es lo que promete la opción
    if tipo == "ataque" and banda in j.tributos:
        return                                                    # esa banda te paga por estar tranquila: no va a atacarte
    if tipo == "ataque" and hasattr(p, "en_tregua") and p.en_tregua(banda):
        return                                                    # tienes una tregua con esa banda: la respeta mientras dure
    if tipo == "ataque":
        t = azar.choice(j.territorios)
        nombre = _nombre_barrio(p, t)[0]
        if j.banda >= 2 and azar.random() < min(0.9, 0.25 + 0.15 * j.banda):
            p.son("territorio", cat="interfaz")
            p.decir(tr('{banda} ha intentado quedarse con {nombre}, pero {v} los ha echado sin que tuvieras que ir.').format(banda=(banda), nombre=(nombre), v=(j.banda_nombre or tr('tu banda'))))
            p.cambiar_reputacion(2)
            return
        j.amenaza = {"territorio": t, "banda": banda, "dia": p.dia}
        p.son("notificacion", cat="interfaz")
        p.decir(tr('{banda} está atacando {nombre}. Tienes hasta la próxima medianoche para defenderlo: ').format(banda=(banda), nombre=(nombre))
                + (tr("ve allí en persona, la defensa empieza al entrar en el barrio; el móvil, en Territorios, te marca el camino.") if p.guerra_activa() else tr("en el móvil, Territorios.")) + tr(" Si no vas, lo pierdes."))
    elif tipo == "pacto":
        j.oferta_pacto = {"banda": banda, "precio": p.precio("pacto_territorio", 500) * n, "dia": p.dia}
        p.son("notificacion", cat="interfaz")
        p.decir(tr('{banda} te propone un pacto: te pagan {precio} euros y durante una semana nadie toca los barrios de nadie. Contesta en el móvil, en Territorios, antes de medianoche.').format(banda=(banda), precio=(j.oferta_pacto['precio'])))
    else:
        j.redada = {"precio": p.precio("soborno_inspector", 250) * n, "dia": p.dia}
        p.son("notificacion", cat="interfaz")
        p.decir(tr('Un inspector te hace saber que estás en su lista. Por {precio} euros mirará hacia otro lado. Si no, habrá redada. Arréglalo en el móvil, en Territorios, antes de medianoche.').format(precio=(j.redada['precio'])))


def defender(p):
    """Ir a defender el territorio atacado: dos grupos de la banda rival en ese barrio."""
    import random
    j = p.j
    a = j.amenaza
    if not a:
        return
    nombre, mapa = _nombre_barrio(p, a["territorio"])
    if mapa is None or mapa.id != p.mundo.id:
        p.app.son("error")
        p.decir(tr('{nombre} está en {v}. Tienes que ir allí para defenderlo.').format(nombre=(nombre), v=(mapa.nombre if mapa else tr('otra localidad'))), True)
        return
    ls = [l for l in p.mundo.lugares.values() if p.mundo.barrio(l.x, l.y)["id"] == a["territorio"] and l.tipo not in ("salida", "embarcadero")]
    if len(ls) < 1:
        j.amenaza = None
        return
    random.shuffle(ls)
    pasos = []
    for k, n in enumerate((3, 4)):
        l = ls[k % len(ls)]
        pasos.append({"tipo": "eliminar", "lugar": l.id, "texto": tr('{v} grupo de {banda}: {n} pandilleros junto a {nombre}.').format(v=([tr('Primer'), tr('Último')][k]), banda=(a['banda']), n=(n), nombre=(l.nombre)),
                      "enemigos": [{"n": n, "tipo": tr('Pandillero de {banda}').format(banda=(a['banda'])), "arma": random.choice(["pistola", "pistola", "subfusil"]), "salud": 70 + 8 * k}]})

    def hecho():
        j.amenaza = None
        p.cambiar_reputacion(3)
        p.decir(tr('{nombre} sigue siendo tuyo.').format(nombre=(nombre)))
    p._empezar_repetible({"id": "defensa", "titulo": tr('Defensa de {nombre}').format(nombre=(nombre)), "lugar": ls[0].id, "contador": "defensas", "pasos": pasos,
                          "recompensa": {"dinero": 800}, "al_completar": hecho})


def opciones_sucesos(p, Menu, Opcion):
    """Lo que hay pendiente en tus territorios, para el menú de Territorios."""
    j = p.j
    app = p.app
    ops = []

    def cerrar_menus():
        """Resuelto un asunto, se cierran su menú y el de Territorios, que se quedaba con la oferta escrita. Nada más que eso."""
        for _ in range(2):
            cima = app.pila[-1] if app.pila else None
            titulo = getattr(cima, "titulo", "")
            titulo = titulo() if callable(titulo) else str(titulo)
            if isinstance(cima, Menu) and (titulo.startswith(tr("Territorios")) or "propone un pacto" in titulo):
                app.cerrar(cima)
    if j.amenaza:
        a = j.amenaza

        def ir():
            if p.mision or p.trabajo:
                app.son("error")
                app.decir(tr("Termina antes lo que tienes entre manos."), True)
                return
            while app.pila and app.pila[-1] is not p:
                app.cerrar(app.pila[-1])
            if p.guerra_activa():                                # con la guerra en la calle se defiende en persona: basta con entrar en el barrio
                nombre, mapa = _nombre_barrio(p, a["territorio"])
                b = next((x for x in mapa.barrios if x["id"] == a["territorio"]), None) if mapa else None
                l = p.lugar_de_barrio(b, mapa) if b else None
                if l is not None:
                    p.gps_a_lugar(l)
                app.decir(tr('{banda} está en {nombre}').format(banda=(a['banda']), nombre=(nombre)) + (tr(', en {nombre}').format(nombre=(mapa.nombre)) if mapa and mapa.id != p.mundo.id else "") + tr(". Ve allí: la defensa empieza en cuanto entres en el barrio."), True)
                return
            defender(p)
        ops.append(Opcion(tr('Defender {v}: lo ataca {banda}').format(v=(_nombre_barrio(p, a['territorio'])[0]), banda=(a['banda'])), ir,
                          ayuda=tr("Dos grupos de pandilleros. Si los echas, el barrio sigue siendo tuyo. Si llega la medianoche sin haber ido, lo pierdes. Tu banda pelea a tu lado. "
                                "Con el modo de guerra de barrios en la calle, se defiende yendo allí: el GPS te lleva y la pelea empieza al entrar en el barrio.")))
    if j.oferta_pacto:
        o = j.oferta_pacto

        def resuelto():
            """El menú de Territorios sigue abierto con la oferta escrita: que no se pueda cobrar dos veces."""
            if j.oferta_pacto is o:
                return False
            app.son("error")
            app.decir(tr("Eso ya está resuelto."), True)
            return True

        def aceptar():
            if resuelto():
                return app.cerrar()
            j.oferta_pacto = None
            j.pacto_hasta = p.dia + 7
            p.cambiar_rep_banda(o["banda"], 15)
            p.dar_dinero(o["precio"], tr("Cobras"))
            app.decir(tr('Pacto cerrado con {banda}. Una semana sin ataques.').format(banda=(o['banda'])), True)
            cerrar_menus()

        def rechazar():
            if resuelto():
                return app.cerrar()
            j.oferta_pacto = None
            p.cambiar_rep_banda(o["banda"], -8)
            p.cambiar_reputacion(1)
            app.decir(tr('Le dices a {banda} que no pactas con nadie. En la calle gusta, pero pueden volver.').format(banda=(o['banda'])), True)
            cerrar_menus()
        ops.append(Opcion(tr('Pacto con {banda}: te pagan {precio} euros por una semana de paz').format(banda=(o['banda']), precio=(o['precio'])),
                          lambda: None if resuelto() else app.abrir(Menu(app, tr('{banda} propone un pacto').format(banda=(o['banda'])), [Opcion(tr("Aceptar el pacto"), aceptar, ayuda=tr("Cobras lo que ofrecen y durante siete días nadie ataca tus barrios. Esa banda te respeta algo más.")),
                                                                                                                     Opcion(tr("Rechazarlo"), rechazar, ayuda=tr("No cobras nada y pueden volver a atacarte. Esa banda te coge algo de manía, pero en la calle ganas algo de fama."))])),
                          ayuda=tr("Si aceptas, cobras y durante siete días nadie ataca tus barrios. Si lo rechazas, ganas algo de fama.")))
    if j.redada:
        r = j.redada

        def pagar():
            if j.redada is not r:                        # ya se pagó: el menú seguía con la opción escrita
                app.son("error")
                return app.decir(tr("Eso ya está resuelto."), True)
            if p.pagar(r["precio"]):
                j.redada = None
                app.decir(tr("El inspector se guarda el sobre. Por ahora, no ha visto nada."), True)
                cerrar_menus()
        ops.append(Opcion(tr('Arreglar lo de la policía: {precio} euros').format(precio=(r['precio'])), pagar,
                          ayuda=tr("Si pagas, no hay redada. Si llega la medianoche sin pagar, una redada te cuesta el tributo de un día de todos tus barrios.")))
    if p.dia <= j.pacto_hasta:
        ops.append(Opcion(tr('Pacto en vigor: nadie ataca tus barrios hasta el día {pacto_hasta}').format(pacto_hasta=(j.pacto_hasta)),
                          ayuda=tr("Lo cerraste aceptando el dinero de una banda. Cuando pase ese día, pueden volver los ataques.")))
    conocidas = [(b, x) for b, x in sorted(j.rep_bandas.items()) if abs(x) >= 1]
    if conocidas:
        ops.append(Opcion(tr("Cómo te llevas con las bandas: ") + ". ".join(f"{b}, {p.rep_banda_txt(x)}" for b, x in conocidas),
                          ayuda=tr("Con una banda que te respeta, sus pandilleros no te atacan por la calle y no intentan quitarte barrios. Con una que va a por ti, pasa lo contrario. "
                                "Cambia con las decisiones de la historia, con los pactos y cada vez que matas a uno de los suyos.")))
    return ops


# ============================================================ salir a dar una vuelta con alguien de tu vida social
def personas_aqui(p, lugar):
    """La gente de tu vida social que suele estar en este lugar (solo con el contenido para adultos)."""
    if not p.vida_sentimental():
        return []
    from . import encuentros                                     # con horarios, solo la que está ahora (encuentros.py)
    return [x for x in p.dato_adulto("personas") if x.get("lugar") == lugar.id and encuentros.presente(p, x)]


def empezar_paseo(p, pers, plan=None):
    """Se viene contigo. Con `plan` (una actividad), es una cita: el plan pasa al llegar a un sitio que sirve para él."""
    j = p.j
    r = p.relacion(pers["id"])
    if p.acompanante:
        p.decir(tr('Ya vas con {nombre}.').format(nombre=(p.acompanante['nombre'])), True)
        return False
    if p._hecho_hoy(r, "paseo"):
        p.decir(tr('Hoy ya habéis salido. {nombre} tiene cosas que hacer.').format(nombre=(pers['nombre'])), True)
        return False
    x, y = p.pos()
    p.acompanante = {"pid": pers["id"], "nombre": pers["nombre"], "lugar": pers["lugar"], "x": x, "y": y, "t_paso": 0.0, "metros": 0.0, "puntos": 0,
                     "px": x, "py": y, "hasta": p.dia * 1440 + p.reloj + 180, "sitios": [], "plan": plan["id"] if plan else None}
    p.app.son("llegada")
    if plan is not None:
        from . import encuentros
        sitio = encuentros.sitio_para(p, plan, p.lugar_cercano(16) or p.lug(pers["lugar"]))
        if sitio is not None and encuentros.sitios_de(plan):
            p.gps_a_lugar(sitio)
            p.decir(tr('{nombre} se viene contigo: {lower}. El GPS te lleva a {nombre2}; también vale otro sitio parecido. El plan pasa al llegar.').format(nombre=(pers['nombre']), lower=(plan['nombre'].lower()), nombre2=(sitio.nombre)), True)
            return True
    p.decir(tr('{nombre} se viene contigo. Te sigue a pie y sube al vehículo que cojas. Llévale a dar una vuelta, a comer o al cine; para despedirte, vuelve a dejarle donde estaba o díselo desde su ficha.').format(nombre=(pers['nombre'])), True)
    return True


def terminar_paseo(p, motivo=""):
    a = p.acompanante
    if not a:
        return
    p.acompanante = None
    if a["puntos"]:
        p.sumar_afinidad(a["pid"], a["puntos"])
        p.cambiar_animo(3)
    r = p.relacion(a["pid"])
    r["citas"] = r.get("citas", 0) + (1 if a["puntos"] >= 4 else 0)
    p.decir((motivo + " " if motivo else "") + (tr('{nombre} se despide. Lo ha pasado bien contigo.').format(nombre=(a['nombre'])) if a["puntos"] >= 4 else tr('{nombre} se despide.').format(nombre=(a['nombre']))))


def paso_acompanante(p, dt):
    """Cada fotograma: te sigue, cuenta el paseo y reacciona a los sitios a los que le llevas."""
    import math
    a = p.acompanante
    j = p.j
    x, y = p.pos()
    d = math.hypot(a["x"] - x, a["y"] - y)
    if j.veh:
        a["x"], a["y"] = x, y
    elif d > 3.0:
        paso = min(d - 2.5, (6.5 if d > 12 else 4.0) * dt)
        a["x"] += (x - a["x"]) / d * paso
        a["y"] += (y - a["y"]) / d * paso
        a["t_paso"] -= dt
        if a["t_paso"] <= 0:
            if "andar" not in a:
                a["andar"] = sum(map(ord, a["pid"])) % 9
            andar = a["andar"]
            a["t_paso"] = (.31 if d > 12 else .42) + .008 * andar
            a["pie"] = 1 - a.get("pie", 0)
            xy = (a["x"], a["y"])
            suelo = "via" if p.mundo.tipo != "mar" and p.mundo.sobre_vias(*xy) else p.mundo.superficie(*xy)
            sonido = f"paso_{suelo}{a['pie']}"
            if sonido not in p.mez.sonidos:
                sonido = "paso_npc"
            tono = .94 + .015 * andar
            p.son(sonido, xy=xy, ref=4, maxd=40, vol=.56, tono=tono)
            suela = ("suela_bota", "suela_dura", "suela_blanda")[andar % 3]
            p.son(p.mez.capa(suela, "paso_npc"), xy=xy, ref=4, maxd=25, vol=.17, tono=tono)
    a["metros"] += math.hypot(x - a["px"], y - a["py"]) if math.hypot(x - a["px"], y - a["py"]) < 30 else 0.0
    a["px"], a["py"] = x, y
    if a["metros"] >= 400 and a["puntos"] < 8:                       # el paseo en sí también cuenta
        a["metros"] = 0.0
        a["puntos"] += 1
    if j.estrellas >= 2 and "susto" not in a["sitios"]:
        a["sitios"].append("susto")
        a["puntos"] -= 3
        p.decir(tr('{nombre} se asusta con la policía detrás. No era el plan.').format(nombre=(a['nombre'])))
    if p.dia * 1440 + p.reloj > a["hasta"]:
        if j.veh is not None and abs(j.veh.vel) > 1.0:          # nadie se baja de un coche en marcha: espera a que pares
            if not a.get("aviso_tarde"):
                a["aviso_tarde"] = True
                p.decir(tr('{nombre}: Se me está haciendo tarde. En cuanto pares, me bajo.').format(nombre=(a['nombre'])))
            return
        terminar_paseo(p, tr("Se ha hecho tarde."))


def con_acompanante_en_local(p, lugar, menu, Opcion):
    """Con tu acompañante en un local: invitarle a tomar algo o, en la administración de lotería, regalarle un décimo.
    Cada cosa, una vez por paseo, y le gusta (issue 29)."""
    a = p.acompanante
    if not a:
        return
    if lugar.tipo in ("comida", "pizzeria", "bar", "taberna", "heladeria"):
        clave, precio = "invitado", p.precio("invitar_acompanante", 12)
        texto = tr('Invitar a {nombre} a tomar algo: {precio} euros').format(nombre=a["nombre"], precio=precio)
        ayuda = tr("Pides algo para tu acompañante. Le gusta el detalle y suma al paseo. Una vez por paseo.")
        hecho = tr('{nombre} elige algo de la carta y brindáis. Le ha gustado el detalle.')
    elif lugar.tipo == "loteria":
        clave, precio = "decimo", p.precio("regalo_decimo", 20)
        texto = tr('Regalarle un décimo a {nombre}: {precio} euros').format(nombre=a["nombre"], precio=precio)
        ayuda = tr("Un décimo para tu acompañante, como regalo: si toca, es suyo. Le hace ilusión y suma al paseo. Una vez por paseo.")
        hecho = tr('{nombre} guarda el décimo en la cartera y te dice que, si toca, os vais de viaje.')
    else:
        return

    def hacer():
        if clave in a.get("detalles", []):
            p.app.decir(tr("Ya has tenido ese detalle en este paseo."), True)
            return
        if not p.pagar(precio):
            return
        a.setdefault("detalles", []).append(clave)
        a["puntos"] += 2
        p.cambiar_animo(1)
        p.son("trato", cat="interfaz")
        p.app.decir(hecho.format(nombre=a["nombre"]), True)
    pos = max(0, len(menu.opciones) - 1)
    menu.opciones.insert(pos, Opcion(texto, hacer, ayuda=ayuda))
    fuente = menu._fuente                                        # que siga ahí si el menú se refresca

    def ops():
        lista = list(fuente() if callable(fuente) else fuente)
        if not any(o.texto == texto for o in lista):
            lista.insert(max(0, len(lista) - 1), Opcion(texto, hacer, ayuda=ayuda))
        return lista
    menu._fuente = ops


def visita_con_acompanante(p, lugar):
    """Al entrar en un sitio con tu acompañante: si es un buen plan, le gusta. Si es donde estaba, se queda."""
    a = p.acompanante
    if not a:
        return
    if a.get("plan"):                                            # una cita en persona: el plan pasa al llegar a un sitio que sirve (encuentros.py)
        from . import encuentros
        act = next((x for x in p.dato_adulto("actividades") if x["id"] == a["plan"]), None)
        pers = p.persona_social(a["pid"])
        if act is not None and pers is not None and lugar.tipo in encuentros.sitios_de(act):
            def confirmar():
                a["plan"] = None
                a["sitios"].append(lugar.id)
                a["hasta"] += int(act.get("horas", 0)) * 60
                a["puntos"] += 2
            encuentros.iniciar_cita(p, pers, act, lugar, al_confirmar=confirmar)
            return
    if lugar.tipo == "casa" and lugar.id in p.j.propiedades and (a["puntos"] or a["metros"] > 60):
        # a casa juntos: si vivís aquí, el paseo termina dentro; si no, se despide en la puerta (issue 29)
        vive = getattr(p.j, "convive", None) == a["pid"] and getattr(p.j, "convive_casa", None) == lugar.id
        p._llegais_juntos = a["pid"] if vive else None
        terminar_paseo(p, tr("Llegáis juntos a casa.") if vive else tr('{nombre} te acompaña hasta la puerta de casa.').format(nombre=(a['nombre'])))
        return
    if lugar.id == a["lugar"] and (a["puntos"] or a["metros"] > 60):
        terminar_paseo(p, tr('Dejas a {nombre} donde estaba.').format(nombre=(a['nombre'])))
        return
    if lugar.tipo in ("comida", "pizzeria", "bar", "taberna", "cine", "feria", "casino", "hotel") and lugar.id not in a["sitios"] and lugar.id != a["lugar"]:
        a["sitios"].append(lugar.id)
        a["puntos"] += 4
        p.cambiar_animo(2)
        p.decir(tr('A {nombre} le gusta el plan: {nombre2}.').format(nombre=(a['nombre']), nombre2=(lugar.nombre)))


# ============================================================ la siete y media, en bares y tabernas
PALOS = ("oros", "copas", "espadas", "bastos")
FIGURAS = {10: "sota", 11: "caballo", 12: "rey"}


def baraja(azar):
    """Baraja española de cuarenta cartas, barajada: (nombre, valor). Las figuras valen medio punto."""
    cartas = [(tr('{v} de {palo}').format(v=(tr('as') if n == 1 else FIGURAS.get(n, str(n))), palo=(palo)), 0.5 if n >= 10 else float(n)) for palo in PALOS for n in (1, 2, 3, 4, 5, 6, 7, 10, 11, 12)]
    azar.shuffle(cartas)
    return cartas


def _puntos_txt(x):
    entero, medio = int(x), x - int(x) > 0.1
    return (tr('{entero} y media').format(entero=(entero)) if entero else "media") if medio else str(entero)


def siete_y_media(p, Menu, Opcion, azar=None):
    """Una mano contra la banca: pedir cartas sin pasarse de siete y media. La banca gana los empates."""
    import random
    azar = azar or random
    app = p.app
    j = p.j
    est = {"apuesta": 0, "mazo": [], "mias": 0.0, "fin": True}

    def cerrar_mano(texto, gano):
        est["fin"] = True
        if gano > 0:
            p.dar_dinero(gano)
            app.son("dinero")
        else:
            app.son("error")
        app.decir(texto + tr(' Tienes {dinero} euros.').format(dinero=(j.dinero)), True)
        m.refrescar(False)

    def apostar(n):
        def f():
            if not est["fin"]:
                return
            if not p.pagar(n):
                return
            est.update({"apuesta": n, "mazo": baraja(azar), "mias": 0.0, "fin": False})
            carta()
        return f

    def carta():
        if est["fin"]:
            return
        nombre, valor = est["mazo"].pop()
        est["mias"] += valor
        app.son("menu_mover")
        if est["mias"] > 7.5:
            cerrar_mano(tr('{capitalize}. Llevas {_puntos_txt}: te has pasado. Pierdes {apuesta} euros.').format(capitalize=(nombre.capitalize()), _puntos_txt=(_puntos_txt(est['mias'])), apuesta=(est['apuesta'])), 0)
        else:
            app.decir(tr('{capitalize}. Llevas {_puntos_txt}.').format(capitalize=(nombre.capitalize()), _puntos_txt=(_puntos_txt(est['mias']))), True)
            m.refrescar(False)

    def plantarse():
        if est["fin"]:
            return
        banca, cartas = 0.0, []
        while banca < est["mias"] and banca <= 7.5:
            nombre, valor = est["mazo"].pop()
            banca += valor
            cartas.append(nombre)
        relato = tr('Te plantas con {_puntos_txt}. La banca saca {join}: {_puntos_txt2}.').format(_puntos_txt=(_puntos_txt(est['mias'])), join=(', '.join(cartas)), _puntos_txt2=(_puntos_txt(banca)))
        if banca > 7.5:
            doble = est["mias"] == 7.5
            cerrar_mano(relato + tr(' Se pasa. Ganas {v} euros').format(v=(est['apuesta'] * (3 if doble else 2))) + (tr(", el doble por hacer siete y media.") if doble else "."), est["apuesta"] * (3 if doble else 2))
        else:
            cerrar_mano(relato + tr(' La banca gana. Pierdes {apuesta} euros.').format(apuesta=(est['apuesta'])), 0)

    def ops():
        if est["fin"]:
            return [Opcion(tr('Apostar {n} euros').format(n=(n)), apostar(n), ayuda=tr("Te dan una carta. Pide más o plántate. Las figuras valen medio punto y las demás, su número. Si pasas de siete y media, pierdes. "
                           "Cuando te plantas, la banca saca cartas hasta igualarte o pasarse: si te iguala, gana ella. Ganar paga el doble de lo apostado; ganar con siete y media justas, el triple."))
                    for n in (10, 50, 200)] + [Opcion(tr("Levantarte de la mesa"), lambda: app.cerrar(m))]
        return [Opcion(lambda: tr('Pedir carta. Llevas {_puntos_txt}').format(_puntos_txt=(_puntos_txt(est['mias']))), carta,
                       ayuda=tr("Te dan otra carta y se suma a lo que llevas. Las figuras valen medio punto. Si pasas de siete y media, pierdes la apuesta.")),
                Opcion(tr("Plantarte"), plantarse, ayuda=tr("Te quedas con lo que llevas y juega la banca. Si se pasa, ganas; si te iguala o te supera, gana ella."))]
    m = Menu(app, lambda: tr('Siete y media. Tienes {dinero} euros').format(dinero=(j.dinero)), ops, intro=tr("Baraja española. Elige cuánto apuestas"))
    app.abrir(m)
    return m, est


def con_cartas(p, menu, Menu, Opcion):
    """Añade la mesa de cartas al menú de un bar o una taberna."""
    fuente = menu._fuente
    from .menus import SALIDAS

    def ops():
        lista = list(fuente() if callable(fuente) else fuente)
        if any(o.texto.startswith(tr("Jugar a la siete y media")) for o in lista):
            return lista
        o = Opcion(tr("Jugar a la siete y media"), lambda: siete_y_media(p, Menu, Opcion),
                   ayuda=tr("Un juego de cartas con baraja española contra la banca. Se apuestan diez, cincuenta o doscientos euros."))
        from . import menus_juego, mesa
        nuevas = [o,
                  Opcion(tr("Jugar al dominó"), lambda: mesa.domino(p, Menu, Opcion),
                         ayuda=tr("Dominó de dos contra un parroquiano. Se apuestan veinte o cien euros.")),
                  Opcion(tr("Jugar a los chinos"), lambda: mesa.chinos(p, Menu, Opcion),
                         ayuda=tr("Cada uno esconde monedas en el puño y dice cuántas hay entre los dos. Se apuestan diez o cincuenta euros.")),
                  Opcion(tr("Echar unas monedas a la tragaperras"), lambda: menus_juego._tragaperras(p),
                         ayuda=tr("La máquina del rincón. La misma que hay en el casino."))]
        donde = len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista)
        lista[donde:donde] = nuevas
        return lista
    menu._fuente = ops
    menu.refrescar(False)
