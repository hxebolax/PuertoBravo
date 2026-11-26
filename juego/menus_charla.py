"""Menú de conversación con una persona de la calle, conocidos y opciones del modo IA."""
from .i18n import tr
from .charla import SITIOS, ficha
from .menus import EntradaTexto, Menu, Opcion


def conversar(p, q):
    app = p.app
    f = ficha(q)
    primera = not f["presentado"]
    intro = p.presentacion(q)

    def decir(intencion, dato=None):
        def hacer():
            antes = f["confianza"]
            texto = p.responder(q, intencion, dato)
            extra = p.reaccion_tras(q, intencion, antes)         # a veces, además de contestar, hace algo
            app.decir(texto + (" " + extra if extra else ""), True)
            if q.estado in ("huye", "ataca", "sigue") or q.hostil:
                app.cerrar(menu)
        return hacer

    def favor():
        app.decir(p.pedir_favor(q), True)

    def reclutar():
        ok, frase = p.reclutar_persona(q)
        if not ok:
            app.son("error")
        app.decir(frase, True)
        if ok:
            app.cerrar(menu)

    def sitios():
        ops = [Opcion(tr('Dónde puedo {c}').format(c=(c)) if c in ("comer", "curarme", "dormir", "comprar") else tr('Dónde hay {c}').format(c=(c)) if c != "policía" else tr("Dónde está la policía"),
                      (lambda c=c: (app.cerrar(m), app.decir(p.responder(q, "sitio", c), True))),
                      ayuda=tr("Te dice cuál es el más cercano, a cuántos metros y hacia dónde, y te lo marca en el GPS. Si en esta localidad no hay, te lo dice.")) for c in SITIOS]
        m = Menu(app, tr("Preguntar por un sitio"), ops + [Opcion(tr("Volver"), lambda: app.cerrar(m))])
        app.abrir(m)

    def libre():
        def hecho(texto):
            if not texto.strip():
                return
            if p.ia_disponible():
                app.decir(tr("Espera un momento."), True)
            r = p.responder_libre(q, texto)
            app.decir(r, True)
            if q.estado in ("huye", "ataca", "sigue") or q.hostil or q not in p.personas or q.tipo != "civil":
                app.cerrar(menu)
        app.abrir(EntradaTexto(app, tr('Qué le dices a {nombre}').format(nombre=(f['nombre'])), hecho, maximo=200,
                               ayuda=tr("Escribe con tus palabras: saludar, preguntar por un sitio, contar algo, hacer un cumplido. ") +
                                     (tr("Con el modo IA, contesta con libertad.") if p.ia_disponible() else tr("El juego entiende la intención de lo que escribes."))))

    def ligar():
        app.decir(p.ligar(q), True)

    def proponer(hotel):
        def hacer():
            if not p.proponer_aventura(q, en_hotel=hotel):
                if q.estado == "huye":
                    app.cerrar(menu)
        return hacer

    def ops():
        lista = [Opcion(lambda: tr('{nombre}, {edad} años, {oficio}. {capitalize}').format(nombre=(f['nombre']), edad=(f['edad']), oficio=(f['oficio']), capitalize=(p.confianza_txt(f).capitalize())),
                        ayuda=tr("Quién es y cuánta confianza te tiene. Con más confianza acepta más cosas: ser amigos, hacerte un favor o unirse a tu banda.")),
                 Opcion(tr("Saludar"), decir("saludar"), ayuda=tr("Al principio de la charla sube la confianza, más o menos según su carácter. Repetirlo ya da poco.")),
                 Opcion(tr("Preguntar por el barrio"), decir("barrio"), ayuda=tr("Te dice en qué barrio estás y cómo es. Sube un poco la confianza.")),
                 Opcion(tr("Preguntar qué se cuenta"), decir("rumor"), ayuda=tr("Lo que te diga sale de lo que de verdad está pasando en tu partida.")),
                 Opcion(tr("Preguntar por un sitio"), sitios, ayuda=tr("Te dice dónde está lo más cercano y te lo marca en el GPS.")),
                 Opcion(tr("Preguntar a qué se dedica"), decir("trabajo_npc"), ayuda=tr("Te cuenta su oficio. Sube un poco la confianza.")),
                 Opcion(tr("Hacer un cumplido"), decir("cumplido"), ayuda=tr("Sube la confianza, más o menos según su carácter, y te alegra un poco el ánimo. Si ya lleváis mucho rato hablando, da poco.")),
                 Opcion(tr("Contar un chiste"), decir("chiste"), ayuda=tr("Si le hace gracia, sube la confianza y tu ánimo; si no, baja un poco. Depende de su carácter.")),
                 Opcion(tr('Invitar a un café: {precio} euros').format(precio=(p.precio('cafe_invitar', 4))), decir("invitar"), ayuda=tr("Sube mucho la confianza. Una vez por persona.")),
                 Opcion(tr('Darle {precio} euros').format(precio=(p.precio('limosna', 10))), decir("limosna"), ayuda=tr("Sube la confianza y, la primera vez, tu prestigio entre los vecinos.")),
                 Opcion(tr("Pedirle el número y ser amigos"), decir("amistad"), ayuda=tr("Hace falta que le caigas bien. Tus conocidos están en el móvil y te cuentan cosas.")),
                 Opcion(tr("Pedirle un favor"), favor, ayuda=tr("Hace falta confianza, y uno al día por persona. Lo que haga depende de cómo estés: si te busca la policía con poco nivel, te esconde; "
                                                         "si vienes con poca salud, te apaña; si no, te da una pista de algo que hay cerca o habla bien de ti en el barrio.")),
                 Opcion(tr("Escribir lo que quieras decirle"), libre, ayuda=tr("Con el modo IA activado en Opciones, la persona contesta con total libertad a lo que escribas."))]
        if not p.en_servidor:
            lista.append(Opcion(lambda: tr('Proponerle que se una a tu banda: prima de {prima_recluta} euros').format(prima_recluta=(p.prima_recluta())), reclutar,
                                ayuda=tr("Necesitas un territorio y hueco en la banda. Además, que te tenga confianza, que tu nombre suene en la calle y que tenga carácter para ello: "
                                      "la gente mayor no se une nunca, ni quien te habla así: {lista}. El carácter se nota en cómo te habla al saludar. Si acepta, cobra la prima, se queda contigo con su nombre y pelea a tu lado como los demás de tu banda.").format(
                                    lista=(", ".join(p.nunca_reclutan()) or tr("nadie")))))
        if p.modo_adulto():
            lista.append(Opcion(tr("Coquetear"), ligar, ayuda=tr("Puede salir bien o mal, según la confianza, tu ánimo y lo que busque la otra persona. Un no es un no.")))
            if p.puede_proponer(q):
                lista.append(Opcion(tr("Proponerle ir a tu casa"), proponer(False), ayuda=tr('Si no tienes casa en esta localidad, vais a un hotel por {precio} euros.').format(precio=(p.precio('hotel_cita', 70)))))
                lista.append(Opcion(tr('Proponerle ir a un hotel: {precio} euros').format(precio=(p.precio('hotel_cita', 70))), proponer(True),
                                    ayuda=tr("Pagas tú la habitación, aunque tengas casa. Puede decir que no, según la confianza y lo que busque.")))
        lista += [Opcion(tr("Insultar"), decir("insultar"), ayuda=tr("Puede marcharse, o plantarte cara. Baja tu prestigio.")),
                  Opcion(tr("Amenazar para que te dé dinero"), decir("amenazar"), ayuda=tr("Es un delito. Puede darte lo que lleve, o gritar pidiendo ayuda.")),
                  Opcion(tr("Despedirte"), lambda: (app.decir(p.responder(q, "despedir"), True), app.cerrar(menu)))]
        return lista
    menu = Menu(app, tr('Hablas con {nombre}').format(nombre=(f['nombre'])), ops, intro=intro if primera else None)
    app.abrir(menu)


def conocidos(p):
    app = p.app
    j = p.j

    def ops():
        from . import encuentros
        lista = []
        for k in reversed(j.conocidos):
            amistad = int(k.get("amistad", 0))
            lista.append(Opcion(tr('{nombre}, {oficio}, de {v}. Os conocisteis el día {dia}').format(nombre=(k['nombre']), oficio=(k['oficio']), v=(p.mapas[k['mapa']].nombre if k['mapa'] in p.mapas else tr('por ahí')), dia=(k['dia']))
                                + (tr('. Amistad {amistad} de 100').format(amistad=(amistad)) if amistad else ""),
                                (lambda k=k: app.decir(p.llamar_conocido(k), True)), ayuda=tr("Intro para llamar. Cada día te cuenta una cosa.")))
            lista.append(Opcion(tr('Quedar con {nombre} para tomar algo').format(nombre=(k['nombre'])), (lambda k=k: encuentros.menu_quedar_conocido(p, k)),
                                ayuda=tr("Eliges la hora y quedáis en un bar de su localidad. Si vas, invitas tú, os hacéis más amigos, se te sube el ánimo y te cuenta lo que se dice por ahí.")))
        if not lista:
            lista = [Opcion(tr("Aún no tienes conocidos. Habla con la gente de la calle con la tecla J y, cuando le caigas bien a alguien, pídele el número"),
                            ayuda=tr("Tus conocidos aparecen aquí: puedes llamarlos y quedar con ellos para tomar algo."))]
        return lista + [Opcion(tr("Volver"), lambda: app.cerrar(m))]
    m = Menu(app, tr("Tus conocidos"), ops)
    app.abrir(m)


def opciones_ia(app):
    from . import ia
    from .config import OPCIONES
    cfg = app.cfg

    def alternar(d):
        if not cfg["ia_activa"] and not ia.disponible(cfg):
            app.son("error")
            app.decir(ia.por_que_no(cfg), True)
            return
        cfg["ia_activa"] = not cfg["ia_activa"]
        ia.ajustar_local(cfg)                 # el modelo local solo está en marcha mientras se va a usar

    def servicio(d):
        ops = OPCIONES["ia_servicio"]
        cfg["ia_servicio"] = ops[(ops.index(cfg["ia_servicio"]) + (d or 1)) % len(ops)]
        ia.ajustar_local(cfg)

    def pedir_clave(s):
        def abrir():
            def hecho(t):
                ia.guardar_clave(t, s)
                app.decir(tr("Clave guardada, cifrada, en la carpeta de configuración.") if t.strip() else tr("Clave borrada."), True)
            app.abrir(EntradaTexto(app, tr('Clave de {v}. Déjala vacía para borrarla').format(v=(ia.NOMBRES[s])), hecho, secreto=True, maximo=300,
                                   ayuda=ia.DONDE_CLAVE[s] + tr(" Se guarda cifrada en tu ordenador y solo se usa para hablar con los personajes. Puedes pegarla con Control V.")))
        return abrir

    def estado_clave(s):
        def txt():
            if ia.clave_guardada(s):
                return tr('Clave de {v}: guardada').format(v=(ia.NOMBRES[s]))
            return tr('Clave de {v}: ').format(v=(ia.NOMBRES[s])) + (tr("tomada de una variable de entorno") if ia.clave(s) else tr("sin poner"))
        return txt

    def texto(clave_cfg, titulo, ayuda):
        def abrir():
            def hecho(t):
                cfg[clave_cfg] = t.strip()
                ia.olvidar_modelos("otro")
                app.decir(tr("Guardado.") if t.strip() else tr("Borrado."), True)
            app.abrir(EntradaTexto(app, titulo, hecho, maximo=200, ayuda=ayuda))
        return abrir

    def estado_local():
        if ia.local_instalado():
            k = ia.modelo_instalado()
            nombre = ia.MODELOS_LOCALES[k]["nombre"].split(",")[0].lower() if k in ia.MODELOS_LOCALES else k
            return tr('Modelo local: instalado, el {nombre}. ').format(nombre=(nombre)) + (tr("Está en marcha") if ia.local_en_marcha() else tr("Ahora está parado"))
        if ia._buscar_local():
            return tr("Modelo local: hay un programa de modelos abierto en este ordenador y el juego lo usará")
        return tr("Modelo local: sin instalar. Intro para descargarlo")

    def info_local():
        local(app)

    def probar():
        if not ia.disponible(cfg):
            app.son("error")
            app.decir(ia.por_que_no(cfg), True)
            return
        app.decir(tr("Probando. Espera un momento."), True)
        app.decir(ia.probar(cfg), True)

    def cual():
        u = ia.ultimo_uso
        if not u["servicio"]:
            return tr("Todavía no se ha usado ningún servicio en esta sesión")
        return tr('Lo último lo contestó {v}, con el modelo {modelo}, en {segundos} segundos').format(v=(ia.NOMBRES[u['servicio']]), modelo=(u['modelo']), segundos=(u['segundos']))

    def ops():
        lista = [
            Opcion(lambda: tr('Modo IA al hablar con la gente: {v}').format(v=(tr('sí') if cfg['ia_activa'] else tr('no'))), ajuste=alternar,
                   ayuda=tr("Con el modo IA, cuando escribes lo que quieres decirle a alguien con la tecla J, contesta una inteligencia artificial interpretando a esa persona, "
                         "y nunca contesta dos veces igual. Sin modo IA, el juego usa su propio motor de conversación, sin conexión.")),
            Opcion(lambda: tr('Servicio: {v}').format(v=(ia.NOMBRES[cfg['ia_servicio']])), ajuste=servicio,
                   ayuda=tr("Izquierda y derecha para cambiar. En automático, el juego prueba primero lo gratuito: el modelo local y luego Google AI Studio. "
                         "Después, los demás servicios que tengan clave. Si uno falla, pasa al siguiente. En cada servicio elige solo el modelo más barato.")),
            Opcion(estado_local, info_local, ayuda=tr("Gratis, sin internet y sin clave. Intro para descargar, cambiar o quitar el modelo.")),
            Opcion(estado_clave("gemini"), pedir_clave("gemini"), ayuda=tr("Google AI Studio tiene un nivel gratuito. Intro para escribir o borrar la clave.")),
            Opcion(estado_clave("openai"), pedir_clave("openai"), ayuda=tr("De pago: unos céntimos por cada mil frases. Intro para escribir o borrar la clave.")),
            Opcion(estado_clave("anthropic"), pedir_clave("anthropic"), ayuda=tr("De pago: unos céntimos por cada mil frases. Intro para escribir o borrar la clave.")),
            Opcion(estado_clave("otro"), pedir_clave("otro"), ayuda=tr("Para otros servicios compatibles con el formato de OpenAI, como OpenRouter o Groq. Algunos tienen modelos gratuitos.")),
            Opcion(lambda: tr('Dirección del otro servicio: {v}').format(v=(cfg['ia_url_otro'] or tr('la de OpenRouter'))),
                   texto("ia_url_otro", tr("Dirección del servicio, empezando por https. Vacía, la de OpenRouter"), tr("Es la dirección base del servicio, la que termina en barra v1.")),
                   ayuda=tr("Solo hace falta si usas un servicio que no sea OpenRouter.")),
            Opcion(lambda: tr('Modelo del otro servicio: {v}').format(v=(cfg['ia_modelo_otro'] or tr('lo elige el juego'))),
                   texto("ia_modelo_otro", tr("Nombre del modelo. Vacío, lo elige el juego"), tr("Si lo dejas vacío, el juego busca un modelo gratuito y, si no hay, usa el primero de la lista.")),
                   ayuda=tr("Solo para el otro servicio. En los demás, el modelo lo elige siempre el juego.")),
            Opcion(lambda: tr('La IA puede proponer acciones, y el juego decide: {v}').format(v=(tr('sí') if cfg['ia_acciones'] else tr('no'))), ajuste=lambda d: cfg.__setitem__("ia_acciones", not cfg["ia_acciones"]),
                   ayuda=tr("Solo cuenta con el modo IA activado. Con sí, además de contestar, el modelo puede proponer que el personaje te acompañe un rato, se vaya, se enfade o se una a tu banda. "
                         "Es una lista cerrada y el modelo no decide nada: lo decide el juego, con las mismas reglas que sin IA, así que no sirve de nada escribirle que te obedezca. "
                         "En esa lista no hay dinero ni objetos: ningún personaje te da nada por lo que escribas. Con no, que es como viene, la IA solo puede irse o enfadarse, como antes. No funciona con el modelo local.")),
            Opcion(tr("Probar ahora"), probar, ayuda=tr("Hace una pregunta de prueba y te dice qué servicio y qué modelo han contestado y cuánto han tardado.")),
            Opcion(cual, ayuda=tr("Qué servicio y qué modelo contestaron la última vez en esta sesión, y cuánto tardaron.")),
            Opcion(tr("Volver a buscar el modelo más barato"), lambda: (ia.olvidar_modelos(), app.decir(tr("Hecho. En la próxima conversación se vuelve a preguntar a cada servicio."), True)),
                   ayuda=tr("El juego lo hace solo cada semana, y cuando un modelo deja de existir. Úsalo si quieres forzarlo.")),
            Opcion(tr("Qué se envía"), accion=lambda: app.decir(tr("Se envía lo que escribes, la ficha de la persona con la que hablas, la hora, el barrio y si llueve, y cómo te ven los vecinos. "
                                                            "No se envían tu partida, tus archivos ni ningún dato tuyo. Con el modelo local no sale nada de tu ordenador. "
                                                            "En el nivel gratuito de Google, lo enviado puede usarse para mejorar sus productos."), True),
                   ayuda=tr("Te cuenta qué datos salen de tu ordenador cuando hablas con la gente usando el modo IA.")),
            Opcion(tr("Volver"), lambda: app.cerrar(m)),
        ]
        return lista

    m = Menu(app, tr("Personas e inteligencia artificial"), ops, al_cerrar=cfg.guardar)
    app.abrir(m)


def local(app):
    """Descargar, cambiar o quitar el modelo de inteligencia artificial que funciona en el propio ordenador."""
    from . import ia
    from .menus_actualizar import Tarea
    cfg = app.cfg

    def instalar(clave):
        def empezar():
            estado = {"decimo": 0}

            def trabajo(tarea):
                def progreso(hecho, total):
                    from .menus_actualizar import texto_progreso
                    tarea.estado = texto_progreso(hecho, total)
                    decimo = int(10 * hecho / max(1, total))
                    if decimo > estado["decimo"] and decimo < 10:
                        estado["decimo"] = decimo
                        tarea.decir(tr('{v} por ciento.').format(v=(decimo * 10)))
                return ia.instalar_local(clave, progreso=progreso, cancelado=lambda: tarea.cancelada, decir=tarea.decir, abrir=getattr(app, "ia_abrir", None))

            def fin(ok, error):
                if error is not None:
                    if isinstance(error, ia.Cancelado) or type(error).__name__ == "Cancelado":
                        app.decir(tr("Descarga cancelada. No se ha instalado nada nuevo."), True)
                    else:
                        app.son("error")
                        app.decir(tr("No se ha podido descargar. Comprueba la conexión y el espacio en el disco, y vuelve a intentarlo."), True)
                    ia.ajustar_local(cfg)
                    return
                app.son("guardado")
                if not cfg["ia_activa"]:
                    cfg["ia_activa"] = True
                ia.ajustar_local(cfg)
                app.decir(tr("Modelo instalado y modo IA activado. El modelo se está cargando: en unos segundos puedes usar Probar ahora, en el menú anterior."), True)
            t = Tarea(app, tr('Descargando el modelo {lower}').format(lower=(ia.MODELOS_LOCALES[clave]['nombre'].split(',')[0].lower())), trabajo, fin)
            t.fondo = True
            app.abrir(t)
        return empezar

    def quitar():
        def si():
            ia.quitar_local()
            app.cerrar(c)
            app.decir(tr("Modelo local quitado. Se ha borrado la carpeta data, ia local."), True)
        c = Menu(app, tr("Vas a borrar el programa y el modelo local de tu disco. Podrás volver a descargarlos cuando quieras"),
                 [Opcion(tr("No, dejarlo como está"), lambda: app.cerrar(c), ayuda=tr("No se borra nada y vuelves al menú del modelo local.")),
                  Opcion(tr("Sí, quitarlo"), si, ayuda=tr("Borra la carpeta data, ia local, con el programa y el modelo. Puedes volver a descargarlo cuando quieras."))])
        app.abrir(c)

    def ops():
        puesto = ia.modelo_instalado()
        lista = [Opcion(tr("Qué es"), accion=lambda: app.decir(
            tr("Un modelo local es una inteligencia artificial pequeña que funciona en tu propio ordenador: es gratis, no necesita internet ni clave, y nada de lo que escribes sale de tu equipo. "
            "Contesta más despacio y con menos gracia que los servicios de internet, y cuanto más antiguo es el ordenador, más tarda. "
            "El juego descarga dos cosas a la carpeta data, ia local: el programa llama punto c p p, de código abierto, y el modelo que elijas. "
            "Mientras el modo IA lo use, el juego lo arranca al abrirse y lo cierra siempre al salir: nunca queda nada abierto."), True),
                        ayuda=tr("Te explica qué es un modelo local, qué descarga el juego y cuánto tarda en contestar."))]
        for clave, m in ia.MODELOS_LOCALES.items():
            marca = tr(", instalado") if clave == puesto else ""
            lista.append(Opcion(tr('{v} el modelo {lower}: {v2} megas{marca}').format(v=(tr('Volver a comprobar') if marca else tr('Descargar')), lower=(m['nombre'].lower()), v2=(m['tamano'] // 2 ** 20), marca=(marca)),
                                instalar(clave), ayuda=m["desc"] + (tr(" Sustituye al que tengas instalado.") if puesto and not marca else "")))
        if ia.local_instalado():
            lista.append(Opcion(tr("Quitar el modelo local"), quitar, ayuda=tr("Borra el programa y el modelo de tu disco.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar(m_)))
        return lista

    m_ = Menu(app, tr("Modelo local"), ops, al_cerrar=cfg.guardar)
    app.abrir(m_)
