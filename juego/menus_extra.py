"""Menús de la segunda ampliación: helipuertos, ruleta, marcadores, servicios, habilidades y logros."""
from .i18n import tr
import math
import random

from . import combustible as C
from . import mundo as M
from .extras2 import HABILIDADES, LOGROS
from .menus import Menu, Opcion

ROJOS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


# ==================================================================== helipuerto
def helipuerto(p, l):
    app = p.app
    j = p.j
    volando = j.veh is not None and j.veh.modelo.get("vuela")
    if volando and p.vuelo_real():                               # a bordo, con el vuelo real: plan de vuelo, combustible y hangar
        from . import vuelo_pantalla
        vuelo_pantalla.menu_campo(p, l)
        return
    if j.veh and not volando:
        app.decir(tr('{nombre}. Bájate del vehículo: aquí solo despegan helicópteros.').format(nombre=(l.nombre)), True)
        return
    if j.estrellas and not volando:
        app.son("error")
        app.decir(tr("El piloto no despega con la policía buscándote."), True)
        return
    destinos = [h for h in p.lugares.values() if h.tipo in ("helipuerto", "aeropuerto") and h.id != l.id and h.mapa != p.mundo.id]
    if not volando:
        con_heli = {h.mapa for h in destinos if h.tipo == "helipuerto"}
        # de pasajero, el helicóptero va a los helipuertos y, donde no hay, a la pista del aeródromo del pueblo
        destinos = [h for h in destinos if h.tipo == "helipuerto" or (h.get("aerodromo") and h.mapa not in con_heli)]

    def volar(h):
        def f():
            precio = 0 if volando else int(h.get("precio", p.precio("vuelo_helicoptero", 150)))
            if precio and not p.pagar(precio):
                return
            _volver_al_juego(p)

            def llegar():
                p.pasar_horas(0.4)
                p.son("motor_helicoptero", cat="interfaz", vol=0.6)
                p.cambiar_mapa(h.mapa, h.x, h.y, None,
                               tr('{v} en {nombre}, {nombre2}. Son las {hora_txt}.').format(v=(tr('Aterrizas') if not volando else tr('Llegas volando')), nombre=(h.nombre), nombre2=(p.mapas[h.mapa].nombre), hora_txt=(p.hora_txt())))
            if volando:
                llegar()                                 # pilotas tú: no hay trayecto de pasajero
            else:
                from .pantallas import viajar as trayecto
                trayecto(app, 35.0, llegar, destino=p.mapas[h.mapa].nombre, vuelo=True)
        return f
    ops = [Opcion(tr('Volar a {nombre}, en {nombre2}').format(nombre=(h.nombre), nombre2=(p.mapas[h.mapa].nombre)) + ("" if volando else tr(': {int} euros').format(int=(int(h.get('precio', p.precio('vuelo_helicoptero', 150)))))), volar(h),
                  ayuda=p.desc_localidad(p.mapas[h.mapa])) for h in destinos]
    intro = tr("Vas en tu helicóptero: el vuelo es gratis") if volando else tr("Vuelos en helicóptero con piloto")
    if not volando:
        from . import vuelo_pantalla
        ops += vuelo_pantalla.opciones_campo(p, l)
    app.abrir(Menu(app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(j.dinero)), ops, intro=intro))


# ======================================================================== ruleta
def ruleta(p):
    app = p.app

    def jugar(nombre, gana, pago, apuesta):
        def f():
            if not p.pagar(apuesta):
                return
            n = random.randint(0, 36)
            p.son("ruleta", cat="interfaz")
            color = "verde" if n == 0 else "rojo" if n in ROJOS else "negro"
            txt = tr('Sale el {n}, {color}. ').format(n=(n), color=(color))
            if gana(n):
                premio = apuesta * (pago + 1)
                p.dar_dinero(premio)
                txt += tr('¡Ganas {v} euros!').format(v=(apuesta * pago))
            else:
                txt += tr('Pierdes {apuesta} euros.').format(apuesta=(apuesta))
            app.decir(txt + tr(' Tienes {dinero}.').format(dinero=(p.j.dinero)), True)
        return f

    def mesa(apuesta):
        doble = tr('Pones una ficha de {apuesta} euros y gira la bola. Si aciertas, recuperas la ficha y ganas otro tanto. Con el cero pierdes.').format(apuesta=apuesta)
        triple = tr('Pones una ficha de {apuesta} euros. Aciertas si sale uno de esos doce números, y ganas el doble de la ficha. Con el cero pierdes.').format(apuesta=apuesta)
        pleno = tr('Pones una ficha de {apuesta} euros a un solo número de los treinta y siete. Si sale, ganas {premio} euros además de la ficha.').format(apuesta=apuesta, premio=apuesta * 35)
        ops = [Opcion(tr("Apostar al rojo, paga el doble"), jugar("rojo", lambda n: n in ROJOS, 1, apuesta), ayuda=doble),
               Opcion(tr("Apostar al negro, paga el doble"), jugar("negro", lambda n: n != 0 and n not in ROJOS, 1, apuesta), ayuda=doble),
               Opcion(tr("Apostar a par, paga el doble"), jugar("par", lambda n: n != 0 and n % 2 == 0, 1, apuesta), ayuda=doble),
               Opcion(tr("Apostar a impar, paga el doble"), jugar("impar", lambda n: n % 2 == 1, 1, apuesta), ayuda=doble),
               Opcion(tr("Apostar a la primera docena, paga el triple"), jugar("d1", lambda n: 1 <= n <= 12, 2, apuesta), ayuda=triple),
               Opcion(tr("Apostar a la segunda docena, paga el triple"), jugar("d2", lambda n: 13 <= n <= 24, 2, apuesta), ayuda=triple),
               Opcion(tr("Apostar a la tercera docena, paga el triple"), jugar("d3", lambda n: 25 <= n <= 36, 2, apuesta), ayuda=triple),
               Opcion(tr("Pleno al 7, paga treinta y cinco a uno"), jugar("7", lambda n: n == 7, 35, apuesta), ayuda=pleno),
               Opcion(tr("Pleno al 17, paga treinta y cinco a uno"), jugar("17", lambda n: n == 17, 35, apuesta), ayuda=pleno),
               Opcion(tr("Pleno al 0, paga treinta y cinco a uno"), jugar("0", lambda n: n == 0, 35, apuesta), ayuda=pleno)]
        app.abrir(Menu(app, lambda: tr('Ruleta, fichas de {apuesta} euros. Tienes {dinero}').format(apuesta=(apuesta), dinero=(p.j.dinero)), ops))
    app.abrir(Menu(app, tr("Ruleta. Elige el valor de la ficha"), [Opcion(tr('Fichas de {a} euros').format(a=(a)), (lambda a=a: mesa(a)),
                                                                          ayuda=tr('Te sientas en la mesa y cada apuesta te cuesta {a} euros. Lo que ganas depende de a qué apuestes.').format(a=a)) for a in (10, 100, 1000)]))


# ==================================================================== marcadores
def marcadores(p):
    app = p.app
    j = p.j

    def guardar():
        x, y = p.pos()
        n = len(j.marcadores) + 1
        nombre = tr('Marcador {n}: {describir}').format(n=(n), describir=(p.mundo.describir(x, y)))
        j.marcadores.append({"nombre": nombre, "mapa": p.mundo.id, "x": x, "y": y})
        app.son("guardado")
        m.refrescar(False)
        app.decir(tr('Guardado: {nombre}.').format(nombre=(nombre)), True)

    def ir(k):
        def f():
            mk = j.marcadores[k]
            if mk["mapa"] != p.mundo.id:
                app.son("error")
                app.decir(tr('Ese marcador está en {nombre}. Viaja primero allí.').format(nombre=(p.mapas[mk['mapa']].nombre)), True)
                return
            _volver_al_juego(p)
            p.fijar_gps(mk["x"], mk["y"], mk["nombre"], radio=6)
        return f

    def borrar():
        if not j.marcadores:
            app.decir(tr("No hay marcadores."), True)
            return
        j.marcadores.pop()
        m.refrescar(False)
        app.decir(tr("Último marcador borrado."), True)

    def ops():
        lista = [Opcion(tr("Guardar un marcador en mi posición actual"), guardar, ayuda=tr("Recuerda este punto exacto para volver luego con el GPS."))]
        for k, mk in enumerate(j.marcadores):
            donde = "" if mk["mapa"] == p.mundo.id else tr(', en {nombre}').format(nombre=(p.mapas[mk['mapa']].nombre))
            lista.append(Opcion(tr('Ir a {nombre}{donde}').format(nombre=(mk['nombre']), donde=(donde)), ir(k),
                                ayuda=tr("Vuelves al juego con el GPS puesto hacia ese punto. Si está en otra localidad, primero tienes que viajar allí.")))
        lista.append(Opcion(tr("Borrar el último marcador"), borrar, ayuda=tr("Quita el marcador que guardaste el último. Los demás se quedan como están.")))
        return lista
    m = Menu(app, tr("Marcadores personales"), ops)
    app.abrir(m)


# ===================================================================== servicios
def servicios(p):
    app = p.app
    j = p.j

    def traer(pid, k):
        def f():
            lista = j.garajes.get(pid) or []
            if k < len(lista) and p.traer_mi_vehiculo(lista[k], pid) is not None:      # lo mismo que desde Mis vehículos
                _volver_al_juego(p)
        return f

    def vehiculos():
        ops = []
        for pid, lista in j.garajes.items():
            l = p.lug(pid)
            for k, d in enumerate(lista):
                ops.append(Opcion(tr('{get}, guardado en {v}: {precio} euros').format(get=(d.get('nombre', d['modelo'])), v=(p.nombre_lugar(l) if l else tr('un garaje')), precio=(p.precio('traer_vehiculo', 150))), traer(pid, k),
                                  ayuda=tr("Tu mecánico lo saca del garaje y te lo deja en la calle, a tu lado. En mitad del mar o con mucha policía buscándote no viene.")))
        app.abrir(Menu(app, tr("Que te traigan un vehículo"), ops or [Opcion(tr("No tienes vehículos guardados en ningún garaje"),
                                                                             ayuda=tr("Para tener uno aquí, guárdalo antes en el garaje de una casa tuya."))]))

    def al_garaje():
        """Que se lleven a un garaje tuyo el vehículo que llevas o el que acabas de dejar."""
        v = j.veh or p.tu_vehiculo(120)
        if v is None:
            app.son("error")
            app.decir(tr("No tienes ningún vehículo aquí. Tiene que ser el que llevas o el que acabas de dejar aparcado cerca."), True)
            return
        if v.tag or v.modelo.get("barco") or v.modelo.get("vuela") or p.mundo.tipo == "mar":
            app.son("error")
            app.decir(p.motivo_ajeno(v) if v.tag else tr("Una aeronave no cabe en el garaje de una casa: se guarda en un hangar, en un helipuerto, un aeropuerto o un aeródromo. Desde el móvil, en Mis vehículos, puedes mandarla a uno.") if v.modelo.get("vuela") else tr("Ese vehículo no se puede guardar en un garaje."), True)
            return

        def llevar(l):
            def f():
                g = j.garajes.setdefault(l.id, [])
                if len(g) >= int(l.get("garaje", 0)):
                    app.son("error")
                    app.decir(tr("Ese garaje está lleno."), True)
                    return
                if v.muerto or not p.pagar(p.precio("mandar_vehiculo", 100)):
                    return
                g.append(p._ficha_garaje(v))
                if j.veh is v:
                    p.salir_vehiculo(forzado=True)
                p.quitar_vehiculo(v)
                p.ultimo_veh = None
                _volver_al_juego(p)
                p.son("arranque", vol=0.6)
                p.decir(tr('Tu mecánico se lleva {nombre} al garaje de {nombre_lugar}.').format(nombre=(v.nombre), nombre_lugar=(p.nombre_lugar(l))) + (tr(" Te quedas a pie.") if not j.veh else ""), True)
            return f
        casas = [l for l in (p.lug(pid) for pid in j.propiedades) if l is not None and int(l.get("garaje", 0)) > 0 and not p.alquilada(l.id)]
        ops = [Opcion(tr('{nombre_lugar}: {len} de {get} plazas ocupadas').format(nombre_lugar=(p.nombre_lugar(l)), len=(len(j.garajes.get(l.id, []))), get=(l.get('garaje', 0))), llevar(l),
                      ayuda=tr('Pagas {precio} euros y tu mecánico se lleva el vehículo a este garaje. Si ibas en él, te quedas a pie. Si el garaje está lleno, no se puede.').format(precio=p.precio('mandar_vehiculo', 100))) for l in casas]
        app.abrir(Menu(app, tr('Mandar {nombre} a un garaje: {precio} euros').format(nombre=(v.nombre), precio=(p.precio('mandar_vehiculo', 100))), ops or [Opcion(tr("No tienes ninguna casa con garaje"),
                                                                                                                                                              ayuda=tr("Hace falta una casa tuya con garaje, comprada y no alquilada."))]))

    def guardaespaldas():
        n = sum(1 for e in p.personas if e.tipo == "aliado" and not e.muerto and not getattr(e, "de_banda", False))      # los de tu banda no cuentan
        if n >= 2:
            app.decir(tr("Ya llevas dos guardaespaldas."), True)
        elif p.pagar(p.precio("guardaespaldas", 350)):
            p.crear_aliado()
            app.decir(tr('Un guardaespaldas llega en un minuto y se pone a tu lado. Cobra {precio} euros cada medianoche.').format(precio=(p.precio('guardaespaldas_sueldo', 200))), True)

    def ambulancia():
        x, y = p.pos()
        if any(e.hostil and not e.muerto and e.activo and e.dist(x, y) < 45 for e in p.personas):
            app.son("error")
            app.decir(tr("La ambulancia no entra mientras haya tiros. Aléjate de los enemigos."), True)
        elif j.salud >= j.salud_max:
            app.decir(tr("No tienes heridas."), True)
        elif p.pagar(p.precio("ambulancia", 200)):
            j.salud = j.salud_max
            p.son("sirena_ambulancia", cat="interfaz", vol=0.4)
            p.son("curar", cat="interfaz")
            app.decir(tr("Los sanitarios te atienden en el sitio. Salud al máximo."), True)
    def asistencia():
        if p.asistencia_carretera():
            _volver_al_juego(p)

    def bidon():
        p.usar_bidon()

    def rueda():
        if p.cambiar_rueda():
            _volver_al_juego(p)

    def grua_rueda():
        from . import realismo as R
        v = j.veh or p.tu_vehiculo(30)
        if v is None or not getattr(v, "pinchada", False):
            app.decir(tr("No tienes ninguna rueda pinchada."), True)
        elif j.estrellas:
            app.son("error")
            app.decir(tr("Con la policía buscándote, la grúa no se acerca."), True)
        elif p.pagar(int(R.aj("precio_cambio_rueda")) * 2):
            p.pasar_horas(0.5)
            p.cambiar_rueda(v, gratis=True)
            _volver_al_juego(p)

    def taxi():
        from . import menus_juego
        if j.estrellas or p.mision:
            app.son("error")
            app.decir(tr("Ahora mismo ningún taxista quiere llevarte."), True)
        else:
            _volver_al_juego(p)
            menus_juego.menu_viaje(p)
    def despedir():
        n = 0
        for e in list(p.personas):
            if e.tipo == "aliado" and not e.muerto and not getattr(e, "de_banda", False):
                p.personas.remove(e)
                n += 1
        app.decir(tr('Despides a {v}. Ya no te cobrarán.').format(v=(tr('tu guardaespaldas') if n == 1 else tr('tus {n} guardaespaldas').format(n=(n)))) if n else tr("No llevas guardaespaldas."), True)

    app.abrir(Menu(app, lambda: tr('Servicios por teléfono. Tienes {dinero} euros').format(dinero=(j.dinero)), [
        Opcion(tr('Que te traigan un vehículo de tus garajes: {precio} euros').format(precio=(p.precio('traer_vehiculo', 150))), vehiculos,
               ayuda=tr("Eliges uno de los vehículos que guardas en tus garajes, de cualquier localidad, y tu mecánico te lo deja en la calle, a tu lado.")),
        Opcion(tr('Mandar tu vehículo a uno de tus garajes: {precio} euros').format(precio=(p.precio('mandar_vehiculo', 100))), al_garaje,
               ayuda=tr("Tu mecánico se lleva el vehículo que llevas, o el que acabas de dejar aparcado cerca, al garaje de la casa que elijas. Vale para casas de cualquier localidad.")),
        Opcion(lambda: tr("Chófer de tu banda") + (f": {p.chofer['nombre']}" if p.chofer else tr(': {precio} euros').format(precio=(p.precio('chofer', 80)))),
               lambda: __import__("juego.misvehiculos", fromlist=["x"]).menu_chofer(p),
               ayuda=tr("Alguien de tu banda viene a recogerte con un vehículo de tu garaje o con uno de la banda, y conduce él hasta el destino que marques en el GPS. "
                     "Tú vas de pasajero y puedes disparar. Hace falta tener a alguien reclutado. Desde aquí también lo despides.")),
        Opcion(tr('Llamar a un guardaespaldas: {precio} euros').format(precio=(p.precio('guardaespaldas', 350))), guardaespaldas,
               ayuda=tr('Llega uno armado con pistola, te sigue y pelea a tu lado. Además cobra {precio} euros cada medianoche. Puedes llevar dos como mucho.').format(precio=(p.precio('guardaespaldas_sueldo', 200)))),
        Opcion(lambda: tr('Despedir a tus guardaespaldas: llevas {sum}').format(sum=(sum(1 for e in p.personas if e.tipo == 'aliado' and not e.muerto and not getattr(e, 'de_banda', False)))), despedir,
               ayuda=tr('Se marchan y dejan de cobrarte los {precio} euros de cada medianoche.').format(precio=(p.precio('guardaespaldas_sueldo', 200)))),
        Opcion(tr('Pedir una ambulancia: {precio} euros').format(precio=(p.precio('ambulancia', 200))), ambulancia,
               ayuda=tr("Los sanitarios te curan donde estás y te dejan la salud al máximo. No vienen si hay enemigos cerca, y si no tienes heridas no te cobran.")),
        Opcion(tr("Pedir un taxi: viaje rápido"), taxi,
               ayuda=tr("Eliges un sitio de esta localidad y el taxi te lleva. El precio y las horas que pasan dependen de la distancia. Con la policía detrás o en mitad de una misión, no te recoge."))] + ([
        Opcion(lambda: tr('Asistencia en carretera: {LITROS_ASISTENCIA} litros de combustible por {PRECIO_ASISTENCIA} euros').format(LITROS_ASISTENCIA=(C.LITROS_ASISTENCIA), PRECIO_ASISTENCIA=(C.PRECIO_ASISTENCIA)), asistencia,
               ayuda=tr("Para cuando te quedas sin combustible lejos de una gasolinera. Tienes que estar en tu vehículo o al lado. Tarda media hora y no viene si te busca la policía.")),
        Opcion(lambda: tr('Echar un bidón de gasolina al depósito: llevas {get}').format(get=(j.objetos.get('bidon', 0))), bidon,
               ayuda=tr("Los bidones se compran en las gasolineras. Tienes que estar en tu vehículo o al lado."))] if p.combustible_activo() else []) + ([
        Opcion(lambda: tr('Cambiar la rueda pinchada con la de repuesto: llevas {get}').format(get=(j.objetos.get('rueda', 0))), rueda,
               ayuda=tr("Con el vehículo parado, estando en él o al lado. Tardas un cuarto de hora. Las ruedas de repuesto se compran en los talleres y en las gasolineras.")),
        Opcion(tr("Que venga la grúa a cambiarte la rueda"), grua_rueda,
               ayuda=tr("Si has pinchado y no llevas repuesto. Cuesta el doble que en el taller, tarda media hora y no viene si te busca la policía."))] if p.averias_activas() else [])))


# ========================================================= habilidades y logros
def progreso(p):
    app = p.app
    j = p.j

    def habilidades():
        ops = []
        for h, (nombre, desc) in HABILIDADES.items():
            ops.append(Opcion(tr('{nombre}: nivel {nivel} de 10').format(nombre=(nombre), nivel=(p.nivel(h))), ayuda=desc))
        ops.append(Opcion(tr('Salud máxima: {int} de 150. Se sube entrenando en un gimnasio').format(int=(int(j.salud_max))),
                          ayuda=tr("Es lo más que llega a tener tu salud: cuanta más, más golpes y disparos aguantas. Cada entrenamiento en el gimnasio la sube cinco puntos, uno al día.")))
        app.abrir(Menu(app, tr("Habilidades"), ops, intro=tr("Mejoran solas con la práctica. F1 explica cada una")))

    def logros():
        ops = []
        for ident, nombre, desc, _ in LOGROS:
            ops.append(Opcion(f"{nombre}: {'conseguido' if ident in j.logros else 'pendiente'}. {desc}",
                              ayuda=tr("Un logro se consigue solo, en cuanto haces lo que dice, y el juego te lo anuncia con un sonido.")))
        intro = (
            tr("Los logros están desactivados en esta partida porque se han usado trampas.")
            if getattr(j, "trampas_usadas", False)
            else None
        )
        app.abrir(Menu(app, tr('Logros: {len} de {len2}').format(len=(len(j.logros)), len2=(len(LOGROS))), ops, intro=intro))
    app.abrir(Menu(app, tr("Habilidades y logros"), [
        Opcion(tr("Habilidades"), habilidades, ayuda=tr("Tu nivel en cada habilidad, del uno al diez, y tu salud máxima. Suben solas con la práctica, y F1 explica cada una.")),
        Opcion(lambda: tr('Logros: {len} de {len2}').format(len=(len(j.logros)), len2=(len(LOGROS))), logros,
               ayuda=tr("La lista de todos los logros, cuáles tienes ya y qué hace falta para cada uno."))]))


# =================================================================== protectora
def protectora(p, l):
    from . import gente
    NOMBRES_PERRO = gente.lista("perros")
    app = p.app
    j = p.j

    def adoptar(nombre):
        def f():
            if p.pagar(p.precio("adoptar_perro", 200)):
                j.perro = nombre
                j.perro_hambre, j.perro_confianza = 0.0, 100.0
                p.crear_perro()
                _volver_al_juego(p)
                p.son("ladrido")
                p.decir(tr('{nombre} sale moviendo el rabo y ya no se separa de ti. Gruñe cuando hay peligro cerca y, a pie, con la tecla Y, busca por el olfato el objeto más cercano y te marca el camino. '
                           'Si quieres llamarlo de otra manera, en su menú, con Mayúsculas Y, está Ponerle otro nombre al perro.').format(nombre=(nombre)), True)
        return f

    def dejar():
        d = p.perro()
        if d in p.personas:
            p.personas.remove(d)
        nombre = j.perro
        j.perro = ""
        j.perro_en_casa = False
        j.perro_hambre, j.perro_confianza = 0.0, 100.0
        app.cerrar()
        app.decir(tr('Dejas a {nombre} en la protectora. Aquí lo cuidarán bien.').format(nombre=(nombre)), True)
    pienso = __import__("juego.menus_juego", fromlist=["x"])._comprar_objeto(p, "pienso")
    if j.perro:
        ops = [Opcion(lambda: p.perro_txt(), ayuda=tr("Dónde está tu perro, cuánta hambre tiene y cuánto confía en ti.")), pienso,
               Opcion(tr('Cómo está y qué necesita {perro}').format(perro=(j.perro)), lambda: menu_perro(p),
                      ayuda=tr("Abre el menú de tu perro: acariciarlo, darle de comer, mandarlo a buscar o mandarlo a casa.")),
               Opcion(tr('Dejar a {perro} en la protectora').format(perro=(j.perro)), dejar,
                      ayuda=tr("Te despides de tu perro para siempre y se queda aquí. No te devuelven el donativo. Luego puedes adoptar otro."))]
    else:
        ops = [Opcion(tr('Adoptar a {n}: {precio} euros de donativo').format(n=(n), precio=(p.precio('adoptar_perro', 200))), adoptar(n), ayuda=tr("Un perro te acompaña a todas partes, avisa de los enemigos y encuentra objetos por el olfato.")) for n in random.sample(NOMBRES_PERRO, min(4, len(NOMBRES_PERRO)))]
    app.abrir(Menu(app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(j.dinero)), ops))


def menu_perro(p):
    """Tu perro: cómo está, acariciarlo, darle de comer, mandarlo a casa o llamarlo. Se abre con Mayúsculas Y, o con Intro a su lado."""
    app = p.app
    j = p.j
    if not j.perro:
        app.decir(tr("No tienes perro. Puedes adoptar uno en una protectora de animales."), True)
        return

    def volver_y(f):
        def g():
            if f():
                while app.pila and app.pila[-1] is not p:
                    app.cerrar(app.pila[-1])
        return g

    def buscar():
        while app.pila and app.pila[-1] is not p:
            app.cerrar(app.pila[-1])
        p.perro_busca()

    def ops():
        if j.perro_en_casa:
            return [Opcion(p.perro_txt(), ayuda=tr("En casa tiene comida y agua, y se le pasa el miedo. Desde aquí lo llamas para que vuelva contigo.")), Opcion(tr('Llamar a {perro} para que vuelva contigo').format(perro=(j.perro)), volver_y(p.llamar_perro), ayuda=tr("Llega corriendo desde casa. En mitad del mar no puede."))]
        if p.perro() is None:
            return [Opcion(tr('{perro} no está aquí ahora mismo: vuelve contigo en cuanto pises tierra').format(perro=(j.perro)),
                           ayuda=tr("Mientras no esté a tu lado no puedes acariciarlo, darle de comer ni mandarlo a buscar."))]
        return [Opcion(p.perro_txt(), ayuda=tr("Con hambre avisa gimiendo, y sin fuerzas no busca. Si te tiene miedo, te sigue de lejos y no avisa de los enemigos ni busca.")),
                Opcion(tr("Acariciar"), lambda: (p.acariciar_perro(), m.refrescar(False)), ayuda=tr("Le sube la confianza poco a poco. Si le has hecho daño, así hacéis las paces.")),
                Opcion(lambda: tr('Dar de comer: te quedan {get} raciones de pienso').format(get=(j.objetos.get('pienso', 0))), lambda: (p.alimentar_perro(), m.refrescar(False)),
                       ayuda=tr("Una ración le quita el hambre de casi un día y le sube mucho la confianza. El pienso se compra en la protectora de animales y en las tiendas.")),
                Opcion(tr("Buscar por el olfato el objeto más cercano"), buscar, ayuda=tr("Lo mismo que la tecla Y.")),
                Opcion(tr("Mandar a casa"), volver_y(p.mandar_perro_a_casa), ayuda=tr("Se va a tu vivienda y te espera allí, con comida y agua. Hace falta tener una casa. Para que vuelva, lo llamas desde este mismo menú."))]
    def renombrar():
        poner_nombre_perro(p, al_terminar=lambda: m.refrescar(False))

    def ops_con_nombre():
        return ops() + [Opcion(tr("Ponerle otro nombre al perro"), renombrar, ayuda=tr("Le pones el nombre que quieras, de hasta veinte letras. Tabulador propone nombres de perro. "
                                                                         "Lo que escribas no se anota en el registro del juego."))]
    m = Menu(app, lambda: tr('Tu perro, {perro}').format(perro=(j.perro)), ops_con_nombre)
    app.abrir(m)


NOMBRE_PERRO_MAX = 20


def poner_nombre_perro(p, al_terminar=None):
    """Le pones nombre a tu perro: lo dice el juego al llamarlo, en su menú y cuando ladra o busca."""
    from . import gente, registro
    from .menus import EntradaTexto
    app, j = p.app, p.j
    antes = j.perro

    def hecho(t):
        t = " ".join(str(t).split())[:NOMBRE_PERRO_MAX]
        if not t or t == antes:
            app.decir(tr('Sigue llamándose {perro}.').format(perro=(antes)), True)
            return
        registro.ocultar(t)                                      # lo que escribes no se anota en el registro del juego
        j.perro = t
        d = p.perro()
        if d is not None:
            d.nombre = t
        p.son("ladrido")
        app.decir(tr('Ahora se llama {t}. Lo llamas y viene moviendo el rabo.').format(t=(t)), True)
        if al_terminar:
            al_terminar()
    app.abrir(EntradaTexto(app, tr('Nombre para tu perro, que ahora se llama {perro}').format(perro=(antes)), hecho, maximo=NOMBRE_PERRO_MAX,
                           ayuda=tr("Escribe el nombre y pulsa Intro. Tabulador propone nombres de perro. Escape lo deja como estaba."),
                           propuestas=lambda: gente.lista("perros")))


# ======================================================================== feria
def feria(p, l):
    app = p.app

    def simon():
        if p.pagar(p.precio("feria_memoria", 10)):
            from .pantallas import SimonSonoro
            _volver_al_juego(p)
            app.abrir(SimonSonoro(app, p))

    def tiro():
        if p.pagar(p.precio("feria_tiro", 20)):
            from .pantallas import TiroAlBlanco
            _volver_al_juego(p)
            app.abrir(TiroAlBlanco(app, p))

    def algodon():
        if p.pagar(p.precio("feria_algodon", 3)):
            p.j.salud = min(p.j.salud_max, p.j.salud + 6)
            p.son("comer", cat="interfaz")
            app.decir(tr('Algodón de azúcar. Salud {int}.').format(int=(int(p.j.salud))), True)
    app.abrir(Menu(app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(p.j.dinero)), [
        Opcion(tr('Máquina de memoria de sonidos: {precio} euros').format(precio=(p.precio('feria_memoria', 10))), simon,
               ayuda=tr('La máquina toca una secuencia de notas y tú la repites con las flechas. Con cinco rondas ya hay premio; con doce, {precio} euros.').format(precio=(p.precio('memoria_premio_12', 1000)))),
        Opcion(tr('Caseta de tiro: {precio} euros').format(precio=(p.precio('feria_tiro', 20))), tiro,
               ayuda=tr('Suenan diez dianas a la izquierda, al centro o a la derecha, y pulsas enseguida la flecha de ese lado. Con siete aciertos ganas {p7} euros; con nueve, {p9}.').format(p7=(p.precio('tiro_premio_7', 80)), p9=(p.precio('tiro_premio_9', 200)))),
        Opcion(tr('Algodón de azúcar: {precio} euros').format(precio=(p.precio('feria_algodon', 3))), algodon,
               ayuda=tr("Te lo comes en el sitio y te sube un poco la salud.")),
        Opcion(lambda: tr('Tu récord en la máquina de memoria: {get} rondas').format(get=(p.j.stats.get('simon', 0))),
               ayuda=tr("La secuencia más larga que has repetido sin fallar en la máquina de memoria."))]))


# ======================================================================= tesoro
def tesoro(p, l):
    app = p.app
    j = p.j
    buceo = p.mundo.tipo == "mar"
    if buceo and j.veh and abs(j.veh.vel) > 1.5:
        app.decir(tr("Detén el barco antes de bucear."), True)
        return
    if not buceo and j.veh:
        app.decir(tr('{nombre}. Bájate del vehículo.').format(nombre=(l.nombre)), True)
        return
    clave = "tesoro:" + l.id
    hechos = p.atracadas.get(clave, [0, 0])
    if hechos[0] != p.dia:
        hechos = [p.dia, 0]

    def buscar():
        if hechos[1] >= 3:
            app.son("error")
            app.decir(tr("Hoy ya has removido todo esto tres veces. Vuelve mañana."), True)
            return
        if p.pagar(p.precio("tesoro_alquiler", 25)):
            hechos[1] += 1
            p.atracadas[clave] = hechos
            from .pantallas import BuscaTesoro
            _volver_al_juego(p)
            app.abrir(BuscaTesoro(app, p, buceo))
    que = tr('Alquilar botellas y bucear: {precio} euros').format(precio=(p.precio('tesoro_alquiler', 25))) if buceo else tr('Alquilar un detector de metales: {precio} euros').format(precio=(p.precio('tesoro_alquiler', 25)))
    app.abrir(Menu(app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(j.dinero)), [
        Opcion(que, buscar, ayuda=tr("Un juego de frío o caliente con el oído. El pitido se acelera y se agudiza al acercarte al tesoro. Tres búsquedas al día en cada sitio.")),
        Opcion(tr("Descripción"), lambda: app.decir(l.desc, True), ayuda=tr("Te cuenta cómo es este sitio.")),
        Opcion(lambda: tr('Tesoros encontrados: {get}').format(get=(j.stats.get('tesoros', 0))),
               ayuda=tr("Los tesoros que has sacado en toda la partida, en todos los sitios de búsqueda."))]))


# ======================================================================== bolsa
def bolsa(p):
    """La bolsa, en los bancos: precios, cuánto han cambiado, lo que tienes, lo que ganas o pierdes, noticias y dividendos (bolsa.py)."""
    from . import bolsa as B
    app = p.app
    j = p.j

    def cambio_txt(ident):
        hoy, ayer = p.precio_accion(ident), p.precio_ayer(ident)
        if ayer <= 0 or abs(hoy - ayer) / ayer < 0.005:
            return tr("igual que ayer")
        pct = int(round(abs(hoy - ayer) / ayer * 100)) or 1
        return tr('{v} un {pct} por ciento desde ayer').format(v=(tr('sube') if hoy > ayer else tr('baja')), pct=(pct))

    def tuyo_txt(ident):
        n = j.acciones.get(ident, 0)
        if not n:
            return tr("No tienes")
        p.cartera_coste()
        coste = float(j.coste_acciones.get(ident, 0.0))
        valor = n * p.precio_accion(ident)
        return tr('Tienes {n}, que valen {int} euros: {balance_txt}').format(n=(n), int=(int(valor)), balance_txt=(p.balance_txt(valor - coste)))

    def operar(ident):
        e = B.EMPRESAS[ident]

        def comprar(n):
            def f():
                precio = p.comprar_acciones(ident, n)
                if precio:
                    p.son("bolsa", cat="interfaz")
                    app.decir(tr('Compras {n} acciones por {precio} euros. Tienes {v}.').format(n=(n), precio=(precio), v=(j.acciones[ident])), True)
                    mm.refrescar(False)
            return f

        def vender(n):
            def f():
                k, ganado = p.vender_acciones(ident, n)
                if k <= 0:
                    app.son("error")
                    app.decir(tr("No tienes acciones de esta empresa."), True)
                    return
                app.decir(tr('Vendes {k} acciones. Con esta venta, {balance_txt}. Te quedan {v}.').format(k=(k), balance_txt=(p.balance_txt(ganado)), v=(j.acciones[ident])), True)
                mm.refrescar(False)
            return f
        div = tr(' Reparte un {dividendo:g} por ciento del precio cada {entero} días.').format(dividendo=(e['dividendo']), entero=(B.AJ.entero('dividendo_dias'))) if e["dividendo"] > 0 else tr(" No reparte dividendos.")
        mm = Menu(app, lambda: tr('{nombre}. {precio_accion:.2f} euros la acción, {cambio_txt}. {tuyo_txt}. Tienes {dinero} euros').format(nombre=(e['nombre']), precio_accion=(p.precio_accion(ident)), cambio_txt=(cambio_txt(ident)), tuyo_txt=(tuyo_txt(ident)), dinero=(j.dinero)), lambda: [
            Opcion(tr("Comprar 10 acciones"), comprar(10),
                   ayuda=tr('Pagas diez veces el precio de hoy: unos {precio} euros.').format(precio=int(round(p.precio_accion(ident) * 10)))),
            Opcion(tr("Comprar 100 acciones"), comprar(100),
                   ayuda=tr('Pagas cien veces el precio de hoy: unos {precio} euros.').format(precio=int(round(p.precio_accion(ident) * 100)))),
            Opcion(tr("Vender 10 acciones"), vender(10),
                   ayuda=tr("Las vendes al precio de hoy y te dice si con ellas ganas o pierdes respecto a lo que te costaron. Si tienes menos de diez, vendes las que tengas.")),
            Opcion(tr("Vender todas"), vender(None),
                   ayuda=tr("Vendes todas las que tienes de esta empresa al precio de hoy, y te dice cuánto ganas o pierdes con la venta.")),
            Opcion(e["desc"] + div, ayuda=tr("A qué se dedica esta empresa y si reparte dividendos."))])
        app.abrir(mm)

    def ops():
        lista = []
        if any(j.acciones.values()):
            valor = p.cartera_valor()
            lista.append(Opcion(tr('Tu cartera vale {int} euros: {balance_txt}. Dividendos cobrados: {get} euros').format(int=(int(valor)), balance_txt=(p.balance_txt(valor - p.cartera_coste())), get=(j.stats.get('dividendos', 0))),
                                ayuda=tr("Lo que te darían hoy por todas tus acciones, y lo que ganas o pierdes comparado con lo que pagaste por ellas.")))
        lista += [Opcion((lambda i=i: tr('{nombre}: {precio_accion:.2f} euros, {cambio_txt}. {tuyo_txt}').format(nombre=(B.EMPRESAS[i]['nombre']), precio_accion=(p.precio_accion(i)), cambio_txt=(cambio_txt(i)), tuyo_txt=(tuyo_txt(i)))), (lambda i=i: operar(i)), ayuda=B.EMPRESAS[i]["desc"])
                  for i in B.EMPRESAS]
        noticias = list(getattr(j, "bolsa_noticias", None) or [])
        if noticias:
            lista.append(Opcion(tr('Noticias de la bolsa: {len}').format(len=(len(noticias))), lambda: app.abrir(Menu(app, tr("Noticias de la bolsa"),
                [Opcion(tr('Día {dia}: {texto}').format(dia=(x['dia']), texto=(x['texto'])), ayuda=tr("Una noticia de una empresa, del día que dice. Las noticias mueven su precio.")) for x in noticias] + [Opcion(tr("Volver"), lambda: app.cerrar())])),
                ayuda=tr("Lo último que ha pasado en las empresas, con el día de cada noticia.")))
        lista.append(Opcion(tr("Cómo funciona la bolsa"), lambda: app.decir(B.como_funciona(), True),
                            ayuda=tr("Te explica de una vez cómo se mueven los precios, cómo se gana y cómo se cobran los dividendos.")))
        return lista
    app.abrir(Menu(app, tr("Bolsa de la comarca"), ops, intro=tr("Los precios cambian cada medianoche. Ganas si vendes más caro de lo que compraste; algunas empresas reparten dividendos")))


# ================================================================== territorios
def como_funcionan_territorios(p):
    """«Cómo funciona esto»: qué son los territorios, para qué sirven y cómo se ganan, se defienden y se pierden. Con las
    cifras de verdad de esta partida, que salen de los datos y de las opciones."""
    from . import guerra as GU, sistemas
    app, j = p.app, p.j
    tributo = p.precio("tributo_territorio", 300)
    ciudades = [m.nombre for m in p.mapas.values() if m.tipo == "ciudad" and m.barrios]
    en_ciudades = ", ".join(ciudades[:-1]) + tr(" y ") + ciudades[-1] if len(ciudades) > 1 else (ciudades[0] if ciudades else tr("las ciudades"))
    oleadas = int(GU.aj("oleadas"))
    lineas = [
        tr('Qué es. Cada barrio de las ciudades, que son {en_ciudades}, puede ser tuyo. Un barrio tuyo es un territorio. Los pueblos y las islas no tienen barrios que conquistar. No hace falta para seguir la historia: es otra manera de ganar dinero y de hacerte fuerte.').format(en_ciudades=(en_ciudades)),
        tr('Para qué sirve, uno: dinero. Cada territorio te paga {tributo} euros cada medianoche, sin hacer nada. Con {max} serían {v} euros al día.').format(tributo=(tributo), max=(max(2, len(j.territorios))), v=(tributo * max(2, len(j.territorios)))),
        tr('Para qué sirve, dos: tu banda. Sin territorios no hay banda. Con el primero puedes reclutar a dos personas, y cada territorio más te deja mantener a una más, hasta {TOPE_BANDA}. Los tuyos te siguen, suben a tu vehículo, pelean a tu lado, y uno puede hacerte de chófer. Se reclutan aquí mismo, en Tu banda.').format(TOPE_BANDA=(sistemas.tope_banda())),
        tr("Para qué sirve, tres: fama y calle. Conquistar sube tu reputación, en tus barrios no andan los pandilleros de la banda que echaste, y la tecla N, el mapa y los tablones dicen que el barrio es tuyo."),
        (tr("Cómo se conquista. Tienes activada la guerra de barrios en la calle: ve al barrio, con el GPS desde este menú, y planta cara a la banda allí, tumbando a dos de los suyos o eligiendo el barrio en este menú cuando ya estés dentro. ")
         if p.guerra_activa() else
         tr("Cómo se conquista. En este menú, elige Conquistar y el nombre del barrio, estando en esa ciudad. Empieza en el acto, estés donde estés. "))
        + tr('Vienen a por ti {oleadas} oleadas de pandilleros, cada una más dura. Si tienes banda, acude a ayudarte. Si caes o te vas, no pierdes nada más que la ocasión: puedes volver a intentarlo. Lleva un arma de fuego, munición de sobra y botiquines. La tecla O dice cómo va la pelea.').format(oleadas=(oleadas)),
        tr("Otra manera, sin pegar un tiro: en Negociar con las bandas puedes comprarles un barrio, devolverles uno tuyo a cambio de dinero o cobrarles un tributo por dejarles estar. Depende de tu fuerza y de cómo te lleves con ellos."),
        tr("Cómo se defiende. De vez en cuando una banda ataca un barrio tuyo: suena un aviso de tambores y te lo dice el juego. Tienes hasta la medianoche: arriba del todo en este menú aparece la opción de defenderlo, "
        "en persona o enviando a tu banda. Si no haces nada, lo pierdes y deja de pagarte."),
        (tr("Reconquista. La tienes activada: cuando tienes muchos barrios, o una ciudad entera, las bandas vencidas se rehacen e intentan recuperarlos, con aviso y con plazo. "
         "En Defensa de tus barrios ves la amenaza, la lealtad y la defensa de cada uno, y pones guardias, refuerzos, informantes y treguas. Dentro, la primera opción lo explica con detalle.")
         if p.rec_nivel() else
         tr("Reconquista. Es una opción, en Opciones, La calle: Las bandas intentan reconquistar tus barrios. Con ella, las bandas vencidas se rehacen e intentan recuperar lo suyo, y tú preparas la defensa con guardias, refuerzos y treguas. "
         "Ahora la tienes apagada o estás en un servidor: solo hay los ataques sueltos de siempre.")),
        tr("Si pierdes un barrio. Deja de pagarte, pasa a ser de la banda que te lo quitó, y si te quedas sin ninguno, tu banda se queda sin sitio. Se puede volver a conquistar igual que la primera vez."),
        tr("Pelear por pelear. Si lo que quieres es una pelea con una banda sin conquistar nada, en este menú está Buscar pelea con una banda: vienen a por ti donde estés y no hay barrio en juego.")
        if not p.en_servidor else
        tr("En un servidor en línea es distinto: los barrios son de las bandas de los jugadores, y se disputan entre bandas desde el menú del servidor. Lo de este menú es para jugar sin conexión."),
    ]
    ops = [Opcion(t.rstrip("."), ayuda=tr("Una parte de la explicación. Con flecha abajo pasas a la siguiente.")) for t in lineas]              # el menú pone el punto
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, tr("Territorios: cómo funciona. Recorre la explicación con las flechas"), ops)
    app.abrir(m)


def buscar_pelea(p):
    """Retar a una banda, sin conquistar nada: eliges cuál y cuánta pelea quieres."""
    app = p.app

    def empezar(banda, larga):
        def f():
            motivo = p.pelea_motivo()
            if motivo:
                app.son("error")
                app.decir(motivo, True)
                return
            while app.pila and app.pila[-1] is not p:
                app.cerrar(app.pila[-1])
            p.buscar_pelea(banda, larga)
        return f

    def elegir(banda):
        def f():
            corta, larga = p.pelea_tamano(False), p.pelea_tamano(True)
            app.abrir(Menu(app, tr('Pelea con {banda}. Con ellos, {rep_banda_txt}').format(banda=(banda), rep_banda_txt=(p.rep_banda_txt(p.rep_banda(banda)))), [
                Opcion(tr('Una pelea corta: vienen {v} de una vez').format(v=(corta[0])), empezar(banda, False),
                       ayuda=tr("Vuelves al juego y llegan todos juntos a por ti, en una sola tanda.")),
                Opcion(tr('Una pelea larga: {len} tandas, de {join}').format(len=(len(larga)), join=(tr(' y ').join(str(n) for n in larga))), empezar(banda, True),
                       ayuda=tr("Entre una tanda y otra hay unos segundos para recargar y curarte.")),
                Opcion(tr("Dejarlo"), lambda: app.cerrar())]))
        return f
    motivo = p.pelea_motivo()
    if motivo:
        app.son("error")
        app.decir(motivo, True)
        return
    ayuda = (tr("Vienen a por ti donde estás ahora, a pie, y hay que quedarse en el barrio hasta acabar. No se gana ningún barrio ni dinero, salvo lo que suelten al caer. "
             "Tu banda acude a ayudarte. La relación con esa banda empeora, y si hay disparos, la policía puede presentarse, como en cualquier pelea."))
    ops = [Opcion(lambda b=b: f"{b}: {p.rep_banda_txt(p.rep_banda(b))}", elegir(b), ayuda=ayuda) for b in p.bandas_para_pelea()]
    ops.append(Opcion(tr("Dejarlo"), lambda: app.cerrar()))
    app.abrir(Menu(app, tr("Buscar pelea con una banda, sin conquistar nada. ¿Con cuál?"), ops, intro=tr("F1 explica las consecuencias")))


def territorios(p):
    app = p.app
    j = p.j

    def conquistar(b):
        def f():
            if p.mision or p.trabajo:
                app.son("error")
                app.decir(tr("Termina antes lo que tienes entre manos."), True)
            elif j.estrellas:
                app.son("error")
                app.decir(tr("Con la policía detrás no es momento de empezar una guerra."), True)
            else:
                p.empezar_conquista(b)
        return f

    def en_la_calle(b):
        """Con la guerra de barrios en la calle: aquí no se conquista nada. Si ya estás en el barrio, plantas cara; si no, el GPS te lleva."""
        def f():
            if p.mundo.barrio(*p.pos())["id"] == b["id"]:
                if p.mision or p.trabajo:
                    app.son("error")
                    return app.decir(tr("Termina antes lo que tienes entre manos."), True)
                while app.pila and app.pila[-1] is not p:
                    app.cerrar(app.pila[-1])
                p.empezar_guerra(b)
                return
            l = p.lugar_de_barrio(b)
            if l is not None:
                p.gps_a_lugar(l)
            app.decir(tr('{nombre} es de {banda_de_barrio}. Ve allí: el GPS te lleva a {v}. Cuando estés dentro, tumba a dos de los suyos o vuelve a este menú para plantarles cara, y empezará la guerra.').format(nombre=(b['nombre']), banda_de_barrio=(p.banda_de_barrio(b)), v=(l.nombre if l else tr('ese barrio'))), True)
        return f
    ops = []
    guerra = p.guerra_activa()
    for b in p.mundo.barrios if p.mundo.tipo == "ciudad" else []:
        if b["id"] in j.territorios:
            if p.rec_activa():                                   # con la reconquista: cómo está el barrio, que siempre se puede consultar
                ops.append(Opcion(lambda b=b: tr('{nombre}: es tuyo. Te da {precio} euros al día. Lealtad {int} de 100, defensa {int2} de 100. Amenaza: {rec_amenaza_txt}').format(nombre=(b['nombre']), precio=(p.precio('tributo_territorio', 300)), int=(int(p.rec_barrio(b['id'])['lealtad'])), int2=(int(p.rec_defensa(b['id']))), rec_amenaza_txt=(p.rec_amenaza_txt(b['id']))),
                                  ayuda=tr("Las bandas vencidas intentan recuperar tus barrios. La lealtad baja si pasan días sin que pises el barrio; la defensa sube con guardias, refuerzos, lealtad y tu banda; "
                                        "y la amenaza dice si se prepara algo contra él. Todo se maneja más abajo, en Defensa de tus barrios.")))
                continue
            ops.append(Opcion(tr('{nombre}: es tuyo. Te da {precio} euros al día').format(nombre=(b['nombre']), precio=(p.precio('tributo_territorio', 300))),
                              ayuda=tr("Te paga cada medianoche sin hacer nada. Si una banda lo ataca, tienes hasta la medianoche para defenderlo o lo pierdes.")))
        elif guerra:
            ops.append(Opcion(lambda b=b: tr('{nombre}: de {banda_de_barrio}. ').format(nombre=(b['nombre']), banda_de_barrio=(p.banda_de_barrio(b))) + (tr("Estás aquí: plantarles cara") if p.mundo.barrio(*p.pos())["id"] == b["id"] else tr("Se conquista en la calle: marcar en el GPS")),
                              en_la_calle(b), ayuda=tr('Tienes activado el modo de guerra de barrios en la calle: los barrios no se conquistan desde el móvil. Ve al barrio y planta cara a la banda allí: vienen a por ti en oleadas, cada una más dura, y tu banda acude a ayudarte. Si ganas, el barrio te paga {precio} euros cada medianoche.').format(precio=(p.precio('tributo_territorio', 300)))))
        else:
            ops.append(Opcion(tr('Conquistar {nombre}').format(nombre=(b['nombre'])), conquistar(b), ayuda=tr('Tres oleadas de pandilleros, cada una más dura. Si ganas, el barrio te paga {precio} euros cada medianoche.').format(precio=(p.precio('tributo_territorio', 300)))))
    if not ops:
        ops = [Opcion(tr("Aquí no hay barrios que conquistar. Las guerras de territorio son cosa de las ciudades: Puerto Bravo, San Lucero y Monteferro"),
                      ayuda=tr("Ve a una de esas ciudades y vuelve a abrir este menú para ver sus barrios."))]
    ops.append(Opcion(lambda: tr('Territorios en tu poder: {len}').format(len=(len(j.territorios))),
                      ayuda=tr("Los barrios que son tuyos, sumando todas las ciudades. Cada uno te paga cada medianoche y te deja mantener a más gente en tu banda.")))
    from . import sistemas
    urgente = sistemas.opciones_sucesos(p, Menu, Opcion)
    ops[0:0] = urgente
    from . import reconquista
    arriba, abajo = reconquista.opciones_territorios(p, Opcion)
    ops[0:0] = arriba
    ops += abajo
    from .menus import EntradaTexto
    if not p.en_servidor:
        ops.append(Opcion(lambda: tr("Negociar con las bandas") + (tr(': {len} te {v} tributo').format(len=(len(j.tributos)), v=(tr('paga') if len(j.tributos) == 1 else tr('pagan'))) if j.tributos else ""),
                          lambda: __import__("juego.pactos", fromlist=["x"]).menu_pactos(p),
                          ayuda=tr("Tres tratos que propones tú: devolverles un barrio tuyo a cambio de dinero, comprarles uno sin pegar un tiro, o cobrarles un tributo diario por dejarles estar. "
                                "Lo que contestan depende de tu fuerza y de cómo te lleves con ellos, y no es igual cada día.")))
    ops.append(Opcion(lambda: tr('Tu banda: {v}, {banda} de {cupo}').format(v=(j.banda_nombre or tr('sin nombre')), banda=(j.banda), cupo=(sistemas.cupo(j))) if j.territorios else tr("Tu banda: necesitas un territorio para tenerla"),
                      lambda: sistemas.menu_banda(p, Menu, Opcion, EntradaTexto),
                      ayuda=tr("Con un territorio puedes reclutar gente. Te siguen, suben a tu vehículo y pelean a tu lado. Cada territorio te deja mantener a uno más.")))
    if not p.en_servidor:
        ops.append(Opcion(tr("Buscar pelea con una banda, sin conquistar nada"), lambda: buscar_pelea(p),
                          ayuda=tr("Para pelear por pelear: eliges una banda y vienen a por ti donde estés. No hay barrio en juego ni premio, y esa banda te cogerá más manía.")))
    # la explicación va la primera, salvo que haya algo que atender ya (un ataque, un asalto, un pacto): eso sigue arriba del todo
    ops.insert(len(arriba) + len(urgente), Opcion(tr("Cómo funciona esto: para qué sirven los territorios y cómo se ganan y se defienden"), lambda: como_funcionan_territorios(p),
                         ayuda=tr("Una explicación corta, con las cifras de tu partida: lo que paga cada barrio, la banda, cómo se conquista, cómo se defiende y qué pasa si lo pierdes.")))
    app.abrir(Menu(app, tr('Territorios de {nombre}').format(nombre=(p.mundo.nombre)), ops))


# ======================================================================== mando
def opciones_mando(app):
    from .mando import ACCIONES, COMBINAR, ORDEN_BOTONES
    md = app.mando
    cfg = app.cfg

    def vib(d):
        cfg["mando_vibracion"] = not cfg["mando_vibracion"]
        if cfg["mando_vibracion"]:
            md.vibrar(0.7, 0.7, 300)

    def fuerza(d):
        cfg["vibracion_fuerza"] = round(max(0.2, min(1.0, cfg["vibracion_fuerza"] + 0.2 * (d or 1))), 1)
        md.vibrar(0.7, 0.7, 300)

    def probar():
        if not md.conectado:
            app.decir(tr("No hay ningún mando conectado."), True)
        else:
            md.vibrar(1.0, 0.0, 350)
            app.decir(tr("Vibración de prueba. Si no notas nada, tu mando no la admite o está desactivada."), True)

    def reasignar(ctx, titulo):
        def elegir(b):
            def f():
                def poner(a):
                    def g():
                        md.mapa[ctx][b] = a
                        md.guardar_mapa()
                        app.cerrar()
                        app.decir(f"{md.nombre_boton(b).capitalize()}: {ACCIONES[a][0]}.", True)
                    return g
                app.abrir(Menu(app, tr('Acción para {nombre_boton}').format(nombre_boton=(md.nombre_boton(b))), [Opcion(ACCIONES[a][0].capitalize(), poner(a), ayuda=tr("Este botón pasa a hacer esto, y el cambio se guarda al momento.")) for a in ACCIONES],
                               intro=tr("Elige qué hará este botón")))
            return f
        botones = [b for b in ORDEN_BOTONES if not (ctx.endswith("_combo") and b == COMBINAR)]     # en una combinación, el botón que se mantiene no cuenta
        app.abrir(Menu(app, titulo, lambda: [Opcion(f"{md.nombre_boton(b).capitalize()}: {ACCIONES[md.mapa[ctx].get(b, 'nada')][0]}", elegir(b),
                                                    ayuda=tr("El botón y lo que hace ahora. Con Intro eliges otra acción para él.")) for b in botones],
                       intro=tr("Pulsa Intro sobre un botón para cambiar lo que hace")))

    def restablecer():
        md.restablecer()
        app.decir(tr("Botones restablecidos a su asignación original."), True)

    def ayuda_mando():
        app.abrir(Menu(app, tr("Qué hace cada botón del mando"), [Opcion(t, ayuda=tr("Un botón y lo que hace. Se cambia en Reasignar, en el menú del mando.")) for t in md.lineas_ayuda()]))

    def tipo(d):
        md.tipo = "ps" if md.tipo == "xbox" else "xbox"
    estado = (lambda: tr('Mando conectado: {nombre}').format(nombre=(md.nombre)) if md.ctrl is not None else tr("No hay ningún mando conectado. Conéctalo por cable o Bluetooth y se detecta solo"))
    app.abrir(Menu(app, tr("Mando"), [
        Opcion(estado, ayuda=tr("Si hay un mando conectado y cuál es. Se detecta solo al conectarlo, sin salir del juego.")),
        Opcion(tr("Qué hace cada botón"), ayuda_mando, ayuda=tr("La lista de lo que hace cada botón a pie, al volante y en los menús, con tu asignación de ahora.")),
        Opcion(lambda: tr('Fuerza de la vibración: {int} por ciento').format(int=(int(cfg['vibracion_fuerza'] * 100))), ajuste=fuerza,
               ayuda=tr("Izquierda y derecha la bajan y la suben, del veinte al cien por cien. Cada cambio hace vibrar el mando para que la notes.")),
        Opcion(lambda: tr('Decir los botones del mando en lugar de las teclas: {v}').format(v=(tr('sí') if cfg['mando_textos'] else tr('no'))),
               ajuste=lambda d: cfg.__setitem__("mando_textos", not cfg["mando_textos"]),
               ayuda=tr("Con un mando conectado, lo que el juego cuenta mientras juegas y lo que explican los tutoriales y las escenas nombra el botón que hace cada cosa: "
                     "pulsa el gatillo izquierdo, en vez de pulsa Q. Lo que va en una combinación se dice con ella. Lo que no tiene botón se sigue diciendo con su tecla, y está en el menú de acciones. Sin mando conectado no cambia nada. "
                     "Las frases que cambian las lee tu lector de pantalla, no la voz grabada.")),
        Opcion(lambda: tr('Vibración: {v}').format(v=(tr('sí') if cfg['mando_vibracion'] else tr('no'))), ajuste=vib, ayuda=tr("El mando vibra con los golpes, los disparos que recibes, las explosiones y cuando pica un pez.")),
        Opcion(tr("Probar la vibración"), probar, ayuda=tr("El mando vibra un momento para que compruebes que la nota. Hace falta tenerlo conectado.")),
        Opcion(lambda: tr('Nombres de los botones: {v}').format(v=(tr('PlayStation') if md.tipo == 'ps' else tr('Xbox'))), ajuste=tipo, ayuda=tr("Se detecta solo al conectar el mando, pero puedes cambiarlo a mano.")),
        Opcion(tr("Reasignar los botones a pie"), lambda: reasignar("pie", tr("Botones a pie")),
               ayuda=tr("Eliges qué hace cada botón cuando vas andando. Los cambios se guardan al momento.")),
        Opcion(tr("Reasignar los botones al volante"), lambda: reasignar("coche", tr("Botones al volante")),
               ayuda=tr("Eliges qué hace cada botón cuando conduces. Los cambios se guardan al momento.")),
        Opcion(tr("Reasignar las combinaciones a pie"), lambda: reasignar("pie_combo", tr("Combinaciones a pie: ") + md.nombre_boton("back") + tr(" mantenido, más otro botón")),
               ayuda=tr("Las segundas funciones: mantienes pulsado el botón Vista, Crear o Share y pulsas otro. De serie: siguiente cruce, dónde está tu vehículo, "
                     "hambre y sueño, caminar solo, hablar, hora, rumbo, rendirte con el gatillo izquierdo y, con el gatillo derecho, el menú de acciones, que tiene todo lo que no cabe en un botón.")),
        Opcion(tr("Reasignar las combinaciones al volante"), lambda: reasignar("coche_combo", tr("Combinaciones al volante: ") + md.nombre_boton("back") + tr(" mantenido, más otro botón")),
               ayuda=tr("De serie: piloto del GPS, repetir la indicación del GPS con la distancia que falta, objetivo, velocidad, siguiente cruce, emisora, rendirte con el gatillo izquierdo "
                     "y, con el gatillo derecho, el menú de acciones, que tiene todo lo que no cabe en un botón.")),
        Opcion(tr("Restablecer los botones originales"), restablecer,
               ayuda=tr("Deshace todos tus cambios de botones y combinaciones, a pie y al volante, y vuelve a la asignación de serie. No pregunta antes."))], al_cerrar=cfg.guardar))
