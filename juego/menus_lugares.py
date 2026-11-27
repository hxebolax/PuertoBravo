"""Menús de los lugares de la ampliación: viajes, barcos, banco, ocio y comercios."""
from .i18n import tr
import math
import random

from . import ficha_vehiculo, mundo as M
from .extras import agua_de
from .menus import Menu, Opcion

PELICULAS = [
    tr("«El último tranvía»: un drama lentísimo en el que no pasa nada, pero pasa muy bien."),
    tr("«Tiburones en la Gran Vía»: tan mala que el público aplaude de pie."),
    tr("«Amor en el desguace»: lloras, y no sabes si de pena o de risa."),
    tr("«El comisario honrado»: ciencia ficción, según el señor de la butaca de al lado."),
    tr("«Rápidos y jubilados»: persecuciones en utilitario a cuarenta por hora. Una joya."),
    tr("«La venganza del boquerón»: cine de terror marinero. Sales con hambre."),
]
def _menu(p, l, ops, intro=None):
    m = Menu(p.app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(p.j.dinero)), ops, intro=intro)
    p.app.abrir(m)
    return m


def _policia_cerca(p, radio=60):
    x, y = p.pos()
    return any(e.tipo == "policia" and not e.muerto and e.dist(x, y) < radio for e in p.personas) or \
        any(p.es_patrulla(o) and o.dist(x, y) < radio for o in p.vehiculos)


# ======================================================================== viajes
def salida(p, l):
    app = p.app
    j = p.j
    dest = p.lug(l.get("a_lugar"))
    if dest is None:
        app.decir(tr('{nombre}. La carretera está cortada.').format(nombre=(l.nombre)), True)
        return
    mapa = p.mapas[dest.mapa]
    horas = float(l.get("horas", 1))
    if not j.veh:
        final = p.lug(p.gps["final"]) if p.gps and p.gps.get("final") else None
        estacion_aqui = next((e for e in p.mundo.lugares.values() if e.tipo == "estacion"), None)
        texto = (tr('{nombre}. Por aquí se va a {nombre2}, pero solo en un vehículo: llega hasta aquí al volante, de cualquier coche o moto, y pulsa Intro sin bajarte.').format(nombre=(l.nombre), nombre2=(mapa.nombre)))
        if estacion_aqui is None:
            app.decir(texto + tr(" Aquí no hay estación de autobuses."), True)
        elif final is not None and p.conexion_hacia(final.mapa) is not l:        # ibas de viaje: a pie, el GPS te lleva al autobús
            app.decir(texto + tr(" A pie se viaja en autobús."), True)
            p.gps_a_lugar(final, callar=True)
        else:
            app.decir(texto + tr(' A pie se viaja en autobús, desde {nombre}: márcala con la tecla L, en Viajes.').format(nombre=(estacion_aqui.nombre)), True)
        return
    if j.estrellas and _policia_cerca(p):
        app.son("error")
        app.decir(tr("¡Con la policía pegada no puedes salir a la carretera! Despístalos primero."), True)
        return

    def ir():
        app.cerrar(m)
        x, y, d = mapa.plaza_junto_a(dest)
        x, y = (x, mapa.carril("H", mapa._idx(y, mapa.NY), d)) if d in (1, 3) else (mapa.carril("V", mapa._idx(x, mapa.NX), d), y)
        p.pasar_horas(horas)
        p.son("lugar_salida", cat="interfaz")
        p.cambiar_mapa(mapa.id, x, y, d * 90.0,
                       tr('Tras {get} kilómetros de carretera llegas a {nombre}. Son las {hora_txt}. Vas hacia el {v} por {describir}.').format(get=(l.get('km', 20)), nombre=(mapa.nombre), hora_txt=(p.hora_txt()), v=(M.NOMBRE_DIR[d]), describir=(mapa.describir(x, y))))
    m = _menu(p, l, [Opcion(tr('Tomar la carretera hasta {nombre}, {get} kilómetros').format(nombre=(mapa.nombre), get=(l.get('km', 20))), ir, ayuda=p.desc_localidad(mapa))])


def estacion(p, l):
    app = p.app
    if p.j.veh:
        if p.trabajo and p.trabajo.get("tipo") == "camion" and p.trabajo.get("veh") is p.j.veh:
            app.decir(tr('{nombre}. La carga no viaja en autobús: se lleva con el camión, por carretera. Pulsa G y el GPS te guía hasta la salida.').format(nombre=(l.nombre)), True)
            p.gps_a_lugar(p.trabajo["lugar"], auto=True, callar=True)
            return
        app.decir(tr('{nombre}. Bájate del vehículo para coger el autobús.').format(nombre=(l.nombre)), True)
        return
    if p.j.estrellas:
        app.son("error")
        app.decir(tr("El conductor te mira, mira el cartel de se busca y cierra la puerta."), True)
        return

    def viajar(dest):
        def f():
            precio = int(dest.get("precio", p.precio("autobus", 20)))
            if not p.pagar(precio):
                return
            app.cerrar(m)
            p.son("lugar_estacion", cat="interfaz")

            def llegar():
                p.pasar_horas(1.5)
                p.cambiar_mapa(dest.mapa, dest.x, dest.y, None,
                               tr('El autobús te deja en {nombre}, {nombre2}. Son las {hora_txt}.').format(nombre=(dest.nombre), nombre2=(p.mapas[dest.mapa].nombre), hora_txt=(p.hora_txt())))
            from .pantallas import viajar as trayecto
            trayecto(app, 50.0, llegar, autobus=True, destino=p.mapas[dest.mapa].nombre)
        return f
    ops = [Opcion(tr('Autobús a {nombre}: {int} euros').format(nombre=(p.mapas[e.mapa].nombre), int=(int(e.get('precio', p.precio('autobus', 20))))), viajar(e), ayuda=p.desc_localidad(p.mapas[e.mapa]))
           for e in p.lugares.values() if e.tipo == "estacion" and e.mapa != p.mundo.id]
    m = _menu(p, l, ops or [Opcion(tr("Hoy no sale ningún autobús"), ayuda=tr("Ninguna otra localidad tiene estación de autobuses. Para salir de aquí, prueba el tren o tu propio vehículo."))])


# ------------------------------------------------------------------ tranvía: para moverse dentro de la ciudad
PRECIO_TRANVIA = 2


def linea_tranvia(p, mapa=None):
    """Las paradas de tranvía de una ciudad, en el orden en que las recorre la línea: dando la vuelta a la ciudad."""
    m = p.mapas[mapa] if mapa else p.mundo
    return m.linea_tranvia() if hasattr(m, "linea_tranvia") else []


def recorrido_tranvia(p, origen, destino):
    """Las paradas por las que pasa el tranvía de una a otra, por el lado más corto de la línea, sin la de origen."""
    linea = linea_tranvia(p, origen.mapa)
    a, b = linea.index(origen), linea.index(destino)
    n = len(linea)
    adelante = [linea[(a + k) % n] for k in range(1, (b - a) % n + 1)]
    atras = [linea[(a - k) % n] for k in range(1, (a - b) % n + 1)]
    return adelante if len(adelante) <= len(atras) else atras


def tranvia(p, l):
    app = p.app
    if p.j.veh:
        app.decir(tr('{nombre}. Bájate del vehículo para coger el tranvía.').format(nombre=(l.nombre)), True)
        return
    if p.j.estrellas:
        app.son("error")
        app.decir(tr("El conductor del tranvía te reconoce y no abre las puertas."), True)
        return
    linea = linea_tranvia(p)
    corto = lambda x: x.nombre.replace("Parada de tranvía de ", "")           # noqa: E731

    def ir(dest):
        def f():
            if not p.pagar(p.precio("tranvia", PRECIO_TRANVIA)):
                return
            app.cerrar(m)
            paradas = recorrido_tranvia(p, l, dest)
            from . import transporte
            transporte.subir(p, l)                              # el tranvía que te recoge es uno de los que circulan por la línea

            def bajar(parada, cuantas):
                p.pasar_horas(0.05 * max(1, cuantas))
                p.teletransportar(parada.x, parada.y)
                transporte.bajar(p, parada)
                p.j.stats["tranvias"] = p.j.stats.get("tranvias", 0) + 1
                p.decir(tr('Te bajas del tranvía en {corto}. {describir}. Son las {hora_txt}.').format(corto=(corto(parada)), describir=(p.mundo.describir(parada.x, parada.y)), hora_txt=(p.hora_txt())))
            from . import pantallas
            if pantallas.con_trayecto(app):
                app.abrir(pantallas.LineaTranvia(app, paradas, bajar, corto))
            else:
                bajar(dest, len(paradas))
        return f
    otras = [x for x in linea if x is not l]
    otras.sort(key=lambda x: len(recorrido_tranvia(p, l, x)))
    ops = [Opcion(tr('Ir a {corto}: {len} {v}, {precio} euros').format(corto=(corto(x)), len=(len(recorrido_tranvia(p, l, x))), v=(tr('parada') if len(recorrido_tranvia(p, l, x)) == 1 else tr('paradas')), precio=(p.precio('tranvia', PRECIO_TRANVIA))), ir(x),
                  ayuda=tr("El tranvía va parando en cada parada y la anuncia. Durante el viaje, con Intro te bajas en la próxima, aunque no sea la que habías elegido. ")
                        + p.mundo.describir(x.x, x.y) + ".") for x in otras]
    m = _menu(p, l, ops or [Opcion(tr("Esta es la única parada de la línea"), ayuda=tr("El tranvía no tiene otra parada a la que llevarte desde aquí."))],
              intro=tr('El tranvía recorre {nombre}. Hay {len} paradas. Elige en cuál quieres bajarte').format(nombre=(p.mundo.nombre), len=(len(linea))))


# ------------------------------------------------------------------ tren: para ir a otras localidades por tierra
def tren(p, l):
    app = p.app
    if p.j.veh:
        app.decir(tr('{nombre}. Bájate del vehículo para coger el tren.').format(nombre=(l.nombre)), True)
        return
    if p.j.estrellas:
        app.son("error")
        app.decir(tr("En la taquilla hay un cartel con tu cara. Mejor no."), True)
        return

    def ir(dest, saltos):
        def f():
            if not p.pagar(precio(saltos)):
                return
            app.cerrar(m)

            def llegar():
                p.pasar_horas(0.5 * saltos)
                p.j.stats["trenes"] = p.j.stats.get("trenes", 0) + 1
                p.cambiar_mapa(dest.mapa, dest.x, dest.y, None, tr('El tren te deja en {nombre}. Son las {hora_txt}.').format(nombre=(dest.nombre), hora_txt=(p.hora_txt())))
            from .pantallas import viajar as trayecto
            trayecto(app, min(60.0, 25.0 + 10.0 * saltos), llegar, destino=p.mapas[dest.mapa].nombre, medio="tren")
        return f

    def precio(saltos):
        return p.precio("tren_base", 10) + p.precio("tren_salto", 12) * saltos
    ops = []
    for e in sorted((x for x in p.lugares.values() if x.tipo == "tren" and x.mapa != p.mundo.id), key=lambda x: (p.saltos_por_tierra(p.mundo.id, x.mapa) or 99, x.mapa)):
        saltos = p.saltos_por_tierra(p.mundo.id, e.mapa)
        if saltos:
            ops.append(Opcion(tr('Tren a {nombre}: {precio} euros').format(nombre=(p.mapas[e.mapa].nombre), precio=(precio(saltos))), ir(e, saltos),
                              ayuda=(tr("Es la localidad vecina. ") if saltos == 1 else tr('Está a {saltos} localidades de aquí. ').format(saltos=(saltos))) + p.desc_localidad(p.mapas[e.mapa])))
    intro = tr("El tren llega a todas las localidades a las que se puede ir por tierra")
    if p.mundo.tren_donde():
        intro += tr('. La vía cruza {nombre} por {tren_donde}: cada minuto y medio, más o menos, pasa un tren, y se le oye venir').format(nombre=(p.mundo.nombre), tren_donde=(p.mundo.tren_donde()))
    m = _menu(p, l, ops or [Opcion(tr("De esta estación no sale ningún tren"), ayuda=tr("Desde esta localidad no se llega por tierra a ninguna otra estación de tren."))], intro=intro)


# ------------------------------------------------------------------ aeropuerto: trayectos largos, avionetas y helicópteros
ALQUILER = {"avioneta": 600, "helicoptero": 900}


def aeropuerto(p, l):
    app = p.app
    j = p.j
    if j.veh is not None and j.veh.modelo.get("vuela"):
        from . import menus_extra
        menus_extra.helipuerto(p, l)                        # llegas pilotando: vuelas tú adonde quieras
        return
    if j.veh:
        app.decir(tr('{nombre}. Bájate del vehículo para entrar en la terminal.').format(nombre=(l.nombre)), True)
        return
    if j.estrellas:
        app.son("error")
        app.decir(tr("En el control de seguridad hay dos agentes mirando una foto tuya. Vuelve cuando no te busquen."), True)
        return

    def volar(dest, medio):
        def f():
            precio = precio_de(dest, medio)
            if not p.pagar(precio):
                return
            app.cerrar(m)

            def llegar():
                p.pasar_horas({"avion": 1.0, "avioneta": 0.7, "helicoptero": 0.5}[medio])
                j.stats["vuelos"] = j.stats.get("vuelos", 0) + 1
                p.cambiar_mapa(dest.mapa, dest.x, dest.y, None, (tr('Aterrizas en el {nombre}.').format(nombre=(dest.nombre)) if dest.tipo == "aeropuerto" else tr('Aterrizas en {nombre}, {nombre2}.').format(nombre=(dest.nombre), nombre2=(p.mapas[dest.mapa].nombre))) + tr(' Son las {hora_txt}.').format(hora_txt=(p.hora_txt())))
            from .pantallas import viajar as trayecto
            if medio == "helicoptero":
                trayecto(app, 35.0, llegar, destino=p.mapas[dest.mapa].nombre, vuelo=True)
            else:
                trayecto(app, 45.0 if medio == "avion" else 38.0, llegar, destino=p.mapas[dest.mapa].nombre, medio=medio)
        return f

    def precio_de(dest, medio):
        return int(dest.get("precio", p.precio("vuelo_avion", 180) if medio == "avion" else p.precio("vuelo_avioneta", 120) if medio == "avioneta" else p.precio("vuelo_helicoptero", 150)))

    def alquilar(modelo):
        def f():
            if any(v.modelo["id"] == modelo and not v.muerto and v.dist(l.x, l.y) < 40 and v is not j.veh for v in p.vehiculos):
                app.decir(tr("Ya tienes uno esperando en la pista. Sal de la terminal y súbete con F."), True)
                return
            if not p.pagar(p.precio("alquiler_" + modelo, ALQUILER[modelo])):
                return
            x, y, d = p.mundo.plaza_junto_a(l)
            v = p.crear_vehiculo(modelo, x, y, d, "aparcado")
            v.cerrado = False
            v.propio = True
            v.alquilado = True                                   # no es tuyo para venderlo en un desguace
            p.son("llegada", cat="interfaz")
            app.cerrar(m)
            p.fijar_gps(x, y, v.nombre, auto=True, radio=4, callar=True)
            p.decir(tr('Alquilado: {nombre}. Te espera en la pista, {situar}. Súbete con F. Se pilota a mano y aterriza en cualquier aeropuerto, helipuerto o espacio abierto.').format(nombre=(v.nombre), situar=(p.situar(x, y, 'está'))))
        return f
    pequeno = bool(l.get("aerodromo"))
    ops = []
    con_pista = set()
    for a in sorted((x for x in p.lugares.values() if x.tipo == "aeropuerto" and x.mapa != p.mundo.id), key=lambda x: (bool(x.get("aerodromo")), x.mapa)):
        con_pista.add(a.mapa)
        # el avión grande solo va de aeropuerto a aeropuerto; a un aeródromo, o desde él, se va en avioneta de línea
        medio = "avioneta" if pequeno or a.get("aerodromo") else "avion"
        ops.append(Opcion(tr('{v} a {nombre}: {precio_de} euros').format(v=(tr('Vuelo') if medio == 'avion' else tr('Avioneta de línea')), nombre=(p.mapas[a.mapa].nombre), precio_de=(precio_de(a, medio))), volar(a, medio),
                          ayuda=(tr("Avión de pasajeros, para los trayectos largos entre ciudades. ") if medio == "avion"
                                 else tr("Una avioneta de ocho plazas con piloto, que aterriza en las pistas cortas de los pueblos. ")) + p.desc_localidad(p.mapas[a.mapa])))
    # a las islas, donde no cabe una pista, se llega en helicóptero de línea
    for h in sorted((x for x in p.lugares.values() if x.tipo == "helipuerto" and x.mapa != p.mundo.id and x.mapa not in con_pista), key=lambda x: x.mapa):
        ops.append(Opcion(tr('Helicóptero de línea a {nombre}, en {nombre2}: {precio_de} euros').format(nombre=(h.nombre), nombre2=(p.mapas[h.mapa].nombre), precio_de=(precio_de(h, 'helicoptero'))), volar(h, "helicoptero"),
                          ayuda=tr("Allí no hay pista: se llega en helicóptero con piloto. ") + p.desc_localidad(p.mapas[h.mapa])))
    ops.append(Opcion(tr('Alquilar una avioneta: {precio} euros').format(precio=(p.precio('alquiler_avioneta', ALQUILER['avioneta']))), alquilar("avioneta"),
                      ayuda=tr("Te la dejan en la pista y la pilotas tú. Más rápida que el helicóptero. Con ella puedes ir a cualquier aeropuerto, aeródromo o helipuerto pulsando Intro al llegar.")))
    if not pequeno:
        ops.append(Opcion(tr('Alquilar un helicóptero: {precio} euros').format(precio=(p.precio('alquiler_helicoptero', ALQUILER['helicoptero']))), alquilar("helicoptero"),
                          ayuda=tr("Te lo dejan en la pista y lo pilotas tú. Más lento que la avioneta, pero se detiene en el aire y aterriza en menos sitio.")))
    from . import vuelo_pantalla
    ops += vuelo_pantalla.opciones_campo(p, l)
    m = _menu(p, l, ops, intro=tr("Avionetas de línea a las ciudades, a los otros pueblos y helicópteros a las islas, y avionetas de alquiler") if pequeno
              else tr("Aviones de pasajeros a las otras ciudades, avionetas de línea a los pueblos, helicópteros a las islas, y avionetas y helicópteros de alquiler"))


def _zarpar(p, l, modelo, salud=None, nombre=None, propio=None):
    j = p.j
    muelle = p.lug(l.get("a_lugar"))
    mar = p.mapas[muelle.mapa]
    x, y, d = mar.plaza_junto_a(muelle)
    p.cambiar_mapa(mar.id, x, y)
    v = p.crear_vehiculo(modelo, x, y, d, None, nombre)
    if salud is not None:
        v.salud = min(v.salud_max, float(salud))
    v.rumbo = M.rumbo_a(mar.ancho / 2 - x, mar.alto / 2 - y)
    v.propio = True
    j.barco_actual = propio
    p._subir(v, False, callar=True)
    p.son("sirena_barco", cat="interfaz", vol=0.5)
    p.decir(tr('Sueltas amarras a bordo de {nombre} y sales a {nombre2}. Proa al {cardinal}. En el mar llevas el timón tú: izquierda y derecha giran, arriba acelera. Pulsa P para pescar, Tabulador para oír qué hay cerca y L para elegir un rumbo.').format(nombre=(v.nombre), nombre2=(mar.nombre), cardinal=(M.cardinal(v.rumbo))))


def embarcadero(p, l):
    app = p.app
    j = p.j
    if j.veh:
        app.decir(tr('{nombre}. Bájate del vehículo para subir a un barco.').format(nombre=(l.nombre)), True)
        return
    if not p.lug(l.get("a_lugar")):
        app.decir(f"{l.nombre}. {l.desc}", True)
        return

    def con_propio(k):
        def f():
            b = j.barcos.pop(k)
            app.cerrar(m)
            _zarpar(p, l, b["modelo"], b.get("salud"), b.get("nombre"), {"modelo": b["modelo"], "nombre": b.get("nombre")})
        return f

    def alquilar():
        if p.pagar(p.precio("alquiler_lancha", 60)):
            app.cerrar(m)
            _zarpar(p, l, "lancha", nombre=tr("Lancha de alquiler"))

    def robar():
        app.cerrar(m)
        p.son("ganzua", cat="interfaz")
        modelo = random.choice(["lancha", "lancha", "pesquero", "lancha_rapida"])
        if random.random() < 0.5:
            p.decir(tr("¡Un marinero te ha visto y da la voz de alarma!"))
            p.delito(2, tr("robo de una embarcación"), siempre=True)
        p.j.stats["vehiculos_robados"] += 1
        _zarpar(p, l, modelo)

    def pescar():
        app.cerrar(m)
        p.empezar_pesca(desde_muelle=True, agua=agua_de(l, p.mundo))

    def practicas():
        app.cerrar(m)
        _zarpar(p, l, "lancha", nombre=tr("Lancha de prácticas"))

    def ops():
        lista = []
        if p.practica_de("zarpar", "timon", "atracar"):          # el tutorial de navegar presta una lancha
            lista.append(Opcion(tr("Zarpar con la lancha de prácticas del tutorial: gratis"), practicas, ayuda=tr("Para los ejercicios del tutorial de navegar. Se devuelve sola al atracar en cualquier muelle.")))
        for k, b in enumerate(j.barcos):
            if b.get("en") == l.id:
                lista.append(Opcion(tr('Zarpar con tu barco: {get}').format(get=(b.get('nombre', b['modelo']))), con_propio(k),
                                    ayuda=tr("Sales al mar con tu barco, gratis y con el estado en que lo dejaste. Al atracar en otro muelle, queda amarrado allí.")))
        lista.append(Opcion(tr('Alquilar una lancha: {precio} euros').format(precio=(p.precio('alquiler_lancha', 60))), alquilar, ayuda=tr("La lancha de alquiler se devuelve sola al atracar en cualquier muelle.")))
        lista.append(Opcion(tr("Robar una embarcación amarrada"), robar, ayuda=tr("Gratis, pero puede que te vean.")))
        lista.append(Opcion(tr("Pescar desde el muelle"), pescar, ayuda=tr("Desde tierra solo pican peces pequeños. Los grandes están mar adentro.")))
        otros = [b for b in j.barcos if b.get("en") != l.id]
        for b in otros:
            e = p.lug(b.get("en"))
            lista.append(Opcion(tr('Tu barco {get} está amarrado en {v}').format(get=(b.get('nombre', b['modelo'])), v=(p.nombre_lugar(e) if e else tr('otro puerto'))),
                                ayuda=tr("Solo puedes zarpar con él desde el muelle donde está amarrado.")))
        return lista
    m = _menu(p, l, ops)


def muelle(p, l):
    app = p.app
    j = p.j
    v = j.veh
    dest = p.lug(l.get("a_lugar"))
    if dest is None or v is None:
        app.decir(f"{l.nombre}. {l.desc}", True)
        return
    if abs(v.vel) > 3:
        app.decir(tr("Reduce la velocidad para atracar."), True)
        return

    def atracar():
        app.cerrar(m)
        extra = ""
        if j.barco_actual:
            j.barcos.append({"modelo": j.barco_actual["modelo"], "nombre": j.barco_actual.get("nombre"), "salud": v.salud, "en": dest.id})
            extra = tr(' Tu barco queda amarrado en {nombre}.').format(nombre=(dest.nombre))
        j.barco_actual = None
        p.salir_vehiculo(forzado=True)
        p.quitar_vehiculo(v)
        p.son("lugar_embarcadero", cat="interfaz")
        p.cambiar_mapa(dest.mapa, dest.x, dest.y, None, tr('Atracas y saltas a tierra en {nombre}, {nombre2}.{extra}').format(nombre=(dest.nombre), nombre2=(p.mapas[dest.mapa].nombre), extra=(extra)))
        p.practica_evento("atracar")                             # el tutorial de navegar comprueba que has atracado de verdad
    m = _menu(p, l, [Opcion(tr('Atracar y desembarcar en {nombre}').format(nombre=(p.mapas[dest.mapa].nombre)), atracar, ayuda=l.desc)])


def punto_pesca(p, l):
    if p.j.veh and p.mundo.tipo != "mar":
        p.app.decir(tr('{nombre}. Bájate del vehículo para pescar.').format(nombre=(l.nombre)), True)
        return
    p.app.decir(f"{l.nombre}. {l.desc}", True)
    if not p.pesca:
        p.empezar_pesca(desde_muelle=p.mundo.tipo != "mar", agua=agua_de(l, p.mundo))


def nautica(p, l):
    app = p.app
    j = p.j
    emb = p.lug(l.get("embarcadero")) or next((e for e in p.mundo.lugares.values() if e.tipo == "embarcadero"), None)

    def comprar(mo):
        def f():
            if emb is None:
                app.decir(tr("No hay amarre disponible."), True)
                return
            if p.pagar(int(mo["precio"])):
                j.barcos.append({"modelo": mo["id"], "nombre": mo["nombre"], "salud": mo["salud"], "en": emb.id})
                app.son("mision_ok")
                app.decir(tr('¡{nombre} es tuyo! Te espera amarrado en {nombre2}.').format(nombre=(mo['nombre']), nombre2=(emb.nombre)), True)
        return f
    ops = [Opcion(tr('{nombre}: {precio} euros').format(nombre=(mo['nombre']), precio=(mo['precio'])), comprar(mo), ayuda=ficha_vehiculo.ayuda_compra(p, mo)) for mo in p.datos["vehiculos"] if mo.get("barco") and mo.get("precio")]
    _menu(p, l, ops, tr("F1 dice cómo es cada embarcación, su ficha técnica y cómo queda frente a la tuya"))


def concesionario(p, l):
    app = p.app

    def comprar(mo):
        def f():
            if p.pagar(int(mo["precio"])):
                x, y, d = p.mundo.plaza_junto_a(l)
                v = p.crear_vehiculo(mo["id"], x, y, d, None)
                v.propio = True
                app.cerrar(m)
                app.son("mision_ok")
                app.decir(tr('¡{nombre} es tuyo, con papeles y todo! {situar}. ').format(nombre=(mo['nombre']), situar=(p.situar(x, y, tr('Te espera')))) + (tr("Guárdalo en el garaje de una de tus casas.") if p.en_servidor else
                          tr("No se pierde aunque lo dejes en la calle: lo tienes en el móvil, en Mis vehículos.")), True)
                p.hacer_mio(v)
        return f
    def vender():
        app.cerrar(m)
        p.jornada_vendedor(l)

    def elegir_para_llevarse():
        """Antes te llevabas siempre el mismo, el de precio medio: ahora eliges cuál pides para «probarlo»."""
        caros = sorted((mo for mo in p.datos["vehiculos"] if mo.get("precio") and not mo.get("barco") and (not marcas or mo["id"] in marcas)), key=lambda mo: mo["precio"])
        if not caros:
            return
        if p.mision:
            app.son("error")
            app.decir(tr("Durante una misión no te la juegas con esto."), True)
            return
        if len(caros) == 1:
            return llevarse(caros[0], caros)

        def con(mo):
            def f():
                app.cerrar(sub)
                llevarse(mo, caros)
            return f
        sub = Menu(app, tr("¿De cuál pides las llaves? Cuanto más caro, con más ganas te busca la policía"),
                   [Opcion(tr('{nombre}, que vale {precio} euros').format(nombre=(mo['nombre']), precio=(mo['precio'])), con(mo), ayuda=ficha_vehiculo.ayuda_compra(p, mo)) for mo in caros] + [Opcion(tr("Dejarlo"), lambda: app.cerrar(sub))])
        app.abrir(sub)

    def llevarse(mo, caros):
        x, y, d = p.mundo.plaza_junto_a(l)
        v = p.crear_vehiculo(mo["id"], x, y, d, None)
        app.cerrar(m)
        p.salir_interior()
        p.j.x, p.j.y = p.mundo.punto_libre(x + 3, y)
        p.son("cristal", xy=(x, y))
        puntos = 3 if caros.index(mo) <= len(caros) // 2 else 4          # los de la mitad cara del escaparate, un nivel más de búsqueda
        p.delito(puntos, tr('Pides las llaves de un {nombre} para probarlo y sales con él sin pagar. Salta la alarma del concesionario.').format(nombre=(mo['nombre'])), siempre=True)
        p.j.stats["vehiculos_robados"] = p.j.stats.get("vehiculos_robados", 0) + 1
        p.cambiar_ciudadania(-2.0)
        app.decir(tr('{situar}. Sube con F y sal de aquí.').format(situar=(p.situar(v.x, v.y, tr('El coche está')))))
    marcas = l.get("modelos")
    ops = [Opcion(tr('{nombre}: {precio} euros').format(nombre=(mo['nombre']), precio=(mo['precio'])), comprar(mo), ayuda=ficha_vehiculo.ayuda_compra(p, mo))
           for mo in p.datos["vehiculos"] if mo.get("precio") and not mo.get("barco") and (not marcas or mo["id"] in marcas)]
    ops.append(Opcion(lambda: tr('Trabajar aquí de vendedor[|a]: ocho horas, sueldo y comisión. Llevas {get} coches vendidos').format(get=(p.j.stats.get('coches_vendidos', 0))), vender,
                      ayuda=tr("Una jornada atendiendo clientes. Cobras un sueldo fijo y una comisión por cada coche que vendas: vendes más cuanto mejor sea tu labia y tu prestigio entre los vecinos. Una jornada al día.")))
    ops.append(Opcion(tr("Pedir las llaves para una prueba y no volver"), elegir_para_llevarse,
                      ayuda=tr("Te llevas un coche de exposición sin pagarlo: eliges cuál. Es un robo a la vista de todos: salta la alarma y la policía sale a por ti con fuerza, más cuanto más caro sea.")))
    m = _menu(p, l, ops, tr("F1 dice cómo es cada vehículo, su ficha técnica y cómo queda frente al tuyo"))


# ======================================================================= dinero
def banco(p, l):
    app = p.app
    j = p.j

    def mover(n, ingresar):
        def f():
            cant = (j.dinero if ingresar else j.banco) if n is None else n
            if cant <= 0 or cant > (j.dinero if ingresar else j.banco):
                app.son("error")
                app.decir(tr("No tienes tanto."), True)
                return
            if ingresar:
                ok = p.ingreso_admitido(cant)                    # con dinero negro, solo hasta un tope al día (capo.py)
                aviso = ""
                if ok < cant:
                    aviso = " " + p.sospecha_bancaria(ok)
                    cant = ok
                if cant <= 0:
                    app.son("error")
                    app.decir(aviso.strip(), True)
                    return
                j.dinero -= cant
                j.banco += cant
                p.apuntar_ingreso(cant)
                if aviso:
                    p.son("caja", cat="interfaz")
                    app.decir(tr('Ingresas {cant} euros.{aviso} En la cuenta hay {banco} y llevas encima {dinero}.').format(cant=(cant), aviso=(aviso), banco=(j.banco), dinero=(j.dinero)), True)
                    return
            else:
                j.dinero += cant
                j.banco -= cant
            p.son("caja", cat="interfaz")
            app.decir(tr('Hecho. En la cuenta hay {banco} euros y llevas encima {dinero}.').format(banco=(j.banco), dinero=(j.dinero)), True)
        return f
    def atracar(plan=None):
        if p.mision or p.trabajo:
            app.son("error")
            app.decir(tr("Termina antes lo que tienes entre manos."), True)
        elif p.arma()["tipo"] not in ("fuego", "explosivo"):
            app.son("error")
            app.decir(tr("Para atracar un banco tienes que empuñar un arma de fuego."), True)
        elif p.atracadas.get("banco:" + l.id) == p.dia:
            app.son("error")
            app.decir(tr("La cámara acorazada está vacía y llena de policías: ya lo atracaste hoy."), True)
        else:
            p.empezar_atraco_banco(l, plan)
            return True
        return False

    def preparar_golpe():
        from . import golpes
        golpes.preparar(p, l, atracar, tr("el golpe al banco"))
    AY_INGRESAR = tr("Pasas esa cantidad del efectivo a tu cuenta, si la llevas encima. Con dinero negro, el banco solo admite cada día hasta cierta cantidad sin preguntar.")
    AY_RETIRAR = tr("Sacas esa cantidad de tu cuenta, si la tienes, y la llevas encima, donde no está a salvo si te detienen o acabas en el hospital.")
    ops = [Opcion(lambda: tr('Saldo de tu cuenta: {banco} euros').format(banco=(j.banco)), ayuda=tr("El dinero del banco no se pierde si te detienen o acabas en el hospital, y da un pequeño interés cada día.")),
           Opcion(tr("Ingresar todo el efectivo"), mover(None, True), ayuda=tr("Con dinero negro, el banco solo admite cada día hasta cierta cantidad sin preguntar: por encima, pide explicaciones, "
                                                                          "no te lo admite y avisa a Hacienda. Ingresar poco a poco, día a día, es una manera de blanquear.")),
           Opcion(tr("Ingresar 100 euros"), mover(100, True), ayuda=AY_INGRESAR), Opcion(tr("Ingresar 500 euros"), mover(500, True), ayuda=AY_INGRESAR),
           Opcion(tr("Ingresar 1000 euros"), mover(1000, True), ayuda=AY_INGRESAR),
           Opcion(tr("Retirar 100 euros"), mover(100, False), ayuda=AY_RETIRAR), Opcion(tr("Retirar 500 euros"), mover(500, False), ayuda=AY_RETIRAR),
           Opcion(tr("Retirar 1000 euros"), mover(1000, False), ayuda=AY_RETIRAR),
           Opcion(tr("Retirar todo"), mover(None, False), ayuda=tr("Sacas todo el saldo de la cuenta y lo llevas encima, donde no está a salvo si te detienen o acabas en el hospital.")),
           Opcion(tr("Bolsa: comprar y vender acciones"), lambda: __import__("juego.menus_extra", fromlist=["x"]).bolsa(p), ayuda=tr("Cinco empresas de la comarca. Los precios cambian cada medianoche.")),
           Opcion(tr("Atracar el banco"), lambda: atracar(), ayuda=tr("Necesitas un arma de fuego. Cinco vigilantes, un botín enorme y cuatro niveles de búsqueda. Una vez al día por banco."))]
    if j.banda and not p.en_servidor:
        from .atracos import AYUDA_GOLPE, TEXTO_GOLPE
        ops.append(Opcion(TEXTO_GOLPE, preparar_golpe, ayuda=AYUDA_GOLPE))
    if not p.en_servidor:
        from . import menus_honrado as mh
        ops.insert(10, Opcion(lambda: tr("Créditos, hipotecas y obligaciones. ") + mh.banco_txt(p), lambda: mh.menu_banco(p, l),
                             ayuda=tr("Pedir un crédito personal, ver tus cuotas y liquidarlas, y consultar lo que te van a cobrar de facturas e impuestos. "
                                   "Lo que te prestan depende de tu prestigio, de tus ingresos estables y de tus antecedentes.")))
    _menu(p, l, ops)


def loteria(p, l):
    from . import loteria as lot
    m = _menu(p, l, lambda: lot.opciones_venta(p, l, lambda: m.refrescar(False)),
              intro=tr("Administración de lotería. El sorteo es cada día a las nueve de la noche"))


def empenos(p, l):
    app = p.app
    j = p.j

    def vender(a):
        def f():
            precio = int(a["precio"] * 0.4)
            del j.armas[a["id"]]
            if j.arma == a["id"]:
                j.arma = "punos"
            p.dar_dinero(precio)
            m.refrescar(False)
            app.decir(tr('Vendes {nombre} por {precio} euros.').format(nombre=(a['nombre']), precio=(precio)), True)
        return f

    def ops():
        from .menus_juego import armas_en_venta
        lista = [Opcion(tr('Vender {nombre} por {int} euros').format(nombre=(a['nombre']), int=(int(a['precio'] * 0.4))), vender(a),
                        ayuda=tr("Te paga el 40 por ciento de lo que cuesta nueva. El arma deja de ser tuya y, si la llevabas en la mano, te quedas con los puños."))
                 for a in p.datos["armas"] if a["id"] in j.armas and a["precio"] > 0]
        venta = armas_en_venta(p, l)                              # lo que el prestamista tiene de segunda mano
        from . import mochila
        lista += mochila.opciones_empenos(p, l, lambda: m.refrescar(False))      # y lo que llevas en la mochila
        return venta + (lista or [Opcion(tr("No tienes nada que le interese al prestamista"),
                                         ayuda=tr("Compra las armas que hayas pagado y lo que lleves de valor en la mochila. Ahora no llevas nada de eso."))])
    m = _menu(p, l, ops)


def pescaderia(p, l):
    app = p.app
    j = p.j

    def vender():
        if not j.pescado:
            app.decir(tr("No traes pescado. Sal al mar en barco y pulsa P para pescar."), True)
            return
        total = sum(x["valor"] for x in j.pescado)
        n = len(j.pescado)
        j.pescado = []
        p.dar_dinero(total)
        app.decir(tr('Vendes {n} capturas por {total} euros.').format(n=(n), total=(total)), True)
    _menu(p, l, [Opcion(lambda: tr('Vender tu pesca: {len} capturas por {sum} euros').format(len=(len(j.pescado)), sum=(sum(x['valor'] for x in j.pescado))), vender,
                        ayuda=tr("Vendes todo lo que has pescado de una vez y cobras al momento. Se pesca en barco, pulsando P, o desde un muelle.")),
                 Opcion(lambda: tr("Tus capturas: ") + (", ".join(x["nombre"] for x in j.pescado) or "ninguna"),
                        ayuda=tr("Lo que has pescado y aún no has vendido. Desde tierra solo pican peces pequeños; los grandes están mar adentro."))])


# ========================================================================= ocio
def gimnasio(p, l):
    j = p.j

    def entrenar():
        if j.gimnasio_dia == p.dia:
            p.app.decir(tr("Ya has entrenado hoy. Tienes agujetas hasta en las pestañas."), True)
        elif j.salud_max >= 150:
            p.app.decir(tr("Estás en tu mejor forma. Ya no puedes mejorar más."), True)
        elif p.pagar(p.precio("gimnasio", 60)):
            j.gimnasio_dia = p.dia
            j.salud_max = min(150.0, j.salud_max + 5)
            j.salud = j.salud_max
            p.pasar_horas(2)
            p.son("lugar_gimnasio", cat="interfaz")
            p.app.decir(tr('Dos horas de pesas y saco. Tu salud máxima sube a {int}.').format(int=(int(j.salud_max))), True)
    def combate(c):
        def f():
            if p.mision or p.trabajo:
                p.app.son("error")
                p.app.decir(tr("Termina antes lo que tienes entre manos."), True)
            elif p.pagar(int(c.get("inscripcion", 0))):
                p.empezar_combate(l, c)
        return f
    def ducha():
        from .necesidades import AJ as NEC
        precio = 0 if j.gimnasio_dia == p.dia else NEC.entero("ducha_gimnasio_precio")
        if p.pagar(precio):
            p.pasar_horas(0.25)
            p.son("salpicadura", vol=0.5)
            p.ha_duchado()
            p.ha_bebido(40)
            p.app.decir(tr("Te duchas en los vestuarios") + (tr(", gratis después de entrenar") if not precio else tr(', por {precio} euros').format(precio=(precio))) + tr(". Sales como nuevo."), True)
    vestuario = [Opcion(lambda: tr("Ducharte en los vestuarios") + (tr(": gratis, has entrenado hoy") if j.gimnasio_dia == p.dia else tr(': {entero} euros').format(entero=(__import__('juego.necesidades', fromlist=['x']).AJ.entero('ducha_gimnasio_precio')))),
                        ducha, ayuda=tr("Te deja limpio, como la ducha de casa. Después de entrenar, gratis."))] if p.vida_realista() else []
    _menu(p, l, vestuario + [Opcion(lambda: tr('Entrenar dos horas: {precio} euros. Salud máxima actual {int}').format(precio=(p.precio('gimnasio', 60)), int=(int(j.salud_max))), entrenar, ayuda=tr("Cada entrenamiento sube cinco puntos tu salud máxima, hasta 150. Uno al día."))] +
          [Opcion((lambda c=c: tr('{nombre}: inscripción de {get} euros. Llevas {get2} victorias').format(nombre=(c['nombre']), get=(c.get('inscripcion', 0)), get2=(j.stats.get(c['id'], 0)))), combate(c), ayuda=c.get("ayuda", ""))
           for c in p.datos.get("combates", [])])


def ropa(p, l):
    """La tienda de ropa: ropa por estilos, calzado y complementos (vestuario.py), y la mochila grande."""
    from . import mochila, vestuario
    ops = vestuario.menu_tienda(p, l, Menu, Opcion, _menu)
    ops.append(Opcion(tr("Vestirte con lo que ya tienes"), lambda: vestuario.menu_vestirte(p, l),
                      ayuda=tr("Lo que has comprado alguna vez es tuyo: aquí, o en tus casas, te lo pones sin pagar.")))
    ops += mochila.opcion_mochila_grande(p, lambda: None)
    ops.append(Opcion(lambda: p.aspecto_txt(), ayuda=tr("Lo que llevas puesto ahora. Hay quien se fija en tu estilo, y en una cita se nota si vas a su gusto.")))
    _menu(p, l, ops)


def cine(p, l):
    def ver():
        if p.pagar(p.precio("cine", 12)):
            p.pasar_horas(2)
            p.j.salud = min(p.j.salud_max, p.j.salud + 10)
            p.son("lugar_cine", cat="interfaz")
            p.app.decir(tr('Hoy ponen {choice} Sales dos horas después, a las {hora_txt}.').format(choice=(random.choice(PELICULAS)), hora_txt=(p.hora_txt())), True)
    _menu(p, l, [Opcion(tr('Ver la película de hoy: {precio} euros').format(precio=(p.precio('cine', 12))), ver, ayuda=tr("Pasan dos horas y recuperas un poco de salud."))])


def hotel(p, l):
    j = p.j

    def dormir():
        if j.estrellas:
            p.app.son("error")
            p.app.decir(tr("El recepcionista no admite huéspedes con la policía detrás."), True)
        elif p.pagar(int(l.get("precio_noche", p.precio("hotel_noche", 70)))):
            p.pasar_horas(8, dormir=True)
            j.salud = j.salud_max
            p.ha_duchado()                                       # la habitación tiene ducha
            p.ha_bebido(100)
            p.son("pasan_horas", cat="interfaz")
            p.app.decir(tr('Duermes ocho horas en una cama estupenda. Salud al máximo. Son las {hora_txt} del día {dia}.').format(hora_txt=(p.hora_txt()), dia=(p.dia)), True)
    _menu(p, l, [Opcion(tr('Pasar la noche: {int} euros').format(int=(int(l.get('precio_noche', p.precio('hotel_noche', 70))))), dormir,
                        ayuda=tr("Duermes ocho horas y sales con la salud al máximo, duchado y sin sed. Con la policía detrás no te admiten."))])


def taberna(p, l):
    app = p.app
    j = p.j
    from .menus_juego import opcion_pedir_carta

    def beber():
        if p.pagar(p.precio("cana_tapa", 4)):
            p.ha_bebido(50)
            j.salud = min(j.salud_max, j.salud + 10)
            p.son("comer", cat="interfaz")
            app.decir(tr('Una caña y una tapa. Salud {int}.').format(int=(int(j.salud))), True)

    def dados(apuesta):
        def f():
            if not p.pagar(apuesta):
                return
            p.son("dados", cat="interfaz")
            yo = random.randint(1, 6) + random.randint(1, 6)
            casa = random.randint(1, 6) + random.randint(1, 6)
            if yo > casa:
                p.dar_dinero(apuesta * 2)
                txt = tr('Sacas {yo} contra {casa}. ¡Ganas {apuesta} euros!').format(yo=(yo), casa=(casa), apuesta=(apuesta))
            elif yo == casa:
                j.dinero += apuesta
                txt = tr('Empate a {yo}. Recuperas la apuesta.').format(yo=(yo))
            else:
                txt = tr('Sacas {yo} contra {casa}. Pierdes {apuesta} euros.').format(yo=(yo), casa=(casa), apuesta=(apuesta))
            app.decir(txt + tr(' Tienes {dinero}.').format(dinero=(j.dinero)), True)
        return f

    def contratar():
        n = sum(1 for e in p.personas if e.tipo == "aliado" and not e.muerto)
        if n >= 2:
            app.decir(tr("Ya llevas dos guardaespaldas. Más sería un desfile."), True)
        elif p.pagar(int(p.precio("guardaespaldas_taberna", 300) * p.hon_fama_factor())):
            p.crear_aliado()
            app.decir(tr('Un tipo enorme deja la cerveza y se levanta. Desde ahora te sigue y dispara a quien te ataque. Cobra {precio} euros cada medianoche.').format(precio=(p.precio('guardaespaldas_sueldo', 200))), True)

    def contrato():
        if p.mision or p.trabajo:
            app.son("error")
            app.decir(tr("Termina antes lo que tienes entre manos."), True)
        else:
            from . import contratos
            contratos.menu_contratos(p, l)

    def despedir():
        n = sum(1 for e in p.personas if e.tipo == "aliado")
        p.personas = [e for e in p.personas if e.tipo != "aliado"]
        app.decir(tr("Despides a tus guardaespaldas.") if n else tr("No tienes guardaespaldas."), True)
    AY_DADOS = tr("Tiras dos dados contra la casa. Si sacas más, ganas lo apostado; si empatáis, lo recuperas; si sacas menos, lo pierdes.")
    ops = ([Opcion(tr('Tomar una copa: {precio} euros').format(precio=(p.precio('copa_bar', 6))), lambda: p.consumir("alcohol", de_inventario=False) if p.pagar(p.precio("copa_bar", 6)) else None, ayuda=tr("Alcohol: sube el ánimo, pero caminas torcido y apuntas peor."))] if p.modo_adulto() else []) + \
          [Opcion(tr('Tomar una caña con tapa: {precio} euros').format(precio=(p.precio('cana_tapa', 4))), beber, ayuda=tr("Te quita la sed y recuperas un poco de salud."))] +           opcion_pedir_carta(p, l) +           [Opcion(tr("Jugar a los dados: 20 euros"), dados(20), ayuda=AY_DADOS), Opcion(tr("Jugar a los dados: 200 euros"), dados(200), ayuda=AY_DADOS),
           Opcion(lambda: tr('Contratar un guardaespaldas: {int} euros').format(int=(int(p.precio('guardaespaldas_taberna', 300) * p.hon_fama_factor()))), contratar, ayuda=tr("Te sigue a pie, sube contigo a los vehículos y dispara a tus enemigos. Máximo dos.")),
           Opcion(tr("Despedir a los guardaespaldas"), despedir, ayuda=tr("Se van todos los que llevas y dejan de cobrarte cada medianoche.")),
           Opcion(tr("Tablón de encargos: ver los contratos de hoy"), contrato, ayuda=tr("Tres encargos para elegir, cada uno de una manera: quitar de en medio a alguien con sus guardaespaldas, cazar a uno que huye en coche, "
                  "entrar a buscarle a un local, seguir a su recadero hasta la guarida, dar un escarmiento sin matar, recuperar algo robado o proteger a alguien. Cada contrato cumplido hace los siguientes más difíciles y mejor pagados."))]
    from . import loteria as lot
    ops.append(lot.opcion_en_local(p, l))
    _menu(p, l, ops)
