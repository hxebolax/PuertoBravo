"""Menús del contenido para adultos: activación, vida social, sustancias, clubes y proveedores."""
from .i18n import tr
import random

from .menus import Dialogo, Menu, Opcion


def _volver_al_juego(p):
    while len(p.app.pila) > 1 and p.app.pila[-1] is not p:
        p.app.pila.pop()
    p.app.teclas.clear()


# ================================================================== activación
def alternar_modo(app):
    cfg = app.cfg
    if cfg["adultos"]:
        cfg["adultos"] = False
        app.aplicar_adultos()
        app.decir(tr("Contenido para adultos desactivado. Esos lugares y opciones desaparecen del juego."), True)
        return

    def si():
        cfg["adultos"] = True
        cfg.guardar()
        app.aplicar_adultos()
        app.cerrar(m)
        app.decir(tr("Contenido para adultos activado. En el móvil aparecen Vida social y Sustancias, y en las ciudades hay clubes nocturnos y proveedores. "
                  "Con Mayúsculas Z abres tus sustancias."), True)

    m = Menu(app, tr("El contenido para adultos incluye relaciones sentimentales y sexuales, compañía de pago, drogas y venta de drogas, siempre sin escenas explícitas. ¿Eres mayor de 18 años y quieres activarlo?"),
             [Opcion(tr("No, dejarlo desactivado"), lambda: app.cerrar(m),
                     ayuda=tr("Todo sigue como está: sin relaciones sexuales, compañía de pago ni drogas. Puedes activarlo cuando quieras desde las opciones.")),
              Opcion(tr("Sí, soy mayor de 18 años: activarlo"), si,
                     ayuda=tr("En el móvil aparecen Vida social y Sustancias, y en las ciudades, clubes nocturnos y proveedores. Se desactiva desde las opciones cuando quieras."))])
    app.abrir(m)


# ================================================================== vida social
def vida_social(p, directo=None):
    app = p.app
    j = p.j
    aqui = p.lugar_cercano(16)

    def ficha(pers):
        pid = pers["id"]
        nuevo = pid not in j.relaciones
        from . import encuentros

        def en_persona():
            return encuentros.cara_a_cara(p, pers)

        def exige(f, mision=False):
            """Lo que se hace cara a cara: si no estáis juntos, se dice dónde anda y qué se puede hacer por teléfono."""
            def g(*a):
                if not en_persona():
                    app.son("error")
                    app.decir(encuentros.lejos_txt(p, pers), True)
                    return None
                if mision and p.mision:
                    app.son("error")
                    app.decir(tr("Estás en mitad de una misión. Esto, mejor cuando acabes."), True)
                    return None
                return f(*a)
            return g

        def en_mi_mapa():
            l = p.lug(pers["lugar"])
            return l is not None and l.mapa == p.mundo.id

        def lejos():
            l = p.lug(pers["lugar"])
            app.son("error")
            app.decir(tr('{nombre} está en {v}. Para quedar tenéis que estar en la misma localidad.').format(nombre=(pers['nombre']), v=(p.nombre_lugar(l) if l else tr('otra localidad'))), True)

        def charlar():
            r = p.relacion(pid)
            cara = en_persona()
            if not cara and not encuentros.en_persona_activo(p) and not en_mi_mapa():
                return lejos()
            if p._hecho_hoy(r, "charla"):
                app.decir(tr('Ya habéis hablado hoy. {nombre} tiene cosas que hacer.').format(nombre=(pers['nombre'])), True)
                return
            if p.hielo_ex(r):                                    # recién rota la relación: corta o cuelga, y no acerca nada
                if not cara:
                    p.son("movil", cat="interfaz", vol=0.6)
                app.decir(p.frase_hielo("charla" if cara else "llamada", pers), True)
                return
            if cara:
                p.sumar_afinidad(pid, 3)
                p.cambiar_animo(2)
                app.decir(tr('Charláis un rato. {choice} Ahora {afinidad_txt}.').format(choice=(random.choice([tr('Te cuenta cómo le ha ido el día.'), tr('Os reís de una tontería.'), tr('Te pregunta por tu vida.'), tr('Te habla de sus planes.')])), afinidad_txt=(p.afinidad_txt(r))), True)
                return
            p.son("movil", cat="interfaz", vol=0.6)
            p.sumar_afinidad(pid, encuentros.AJ.entero("llamada_afinidad"))
            p.cambiar_animo(1)
            app.decir(tr('Llamas a {nombre}. {choice} Ahora {afinidad_txt}.').format(nombre=(pers['nombre']), choice=(random.choice([tr('Habláis un rato de nada en particular.'), tr('Te cuenta en dos frases cómo va su día.'), tr('Se alegra de oírte.'), tr('Os reís por teléfono de una tontería.')])), afinidad_txt=(p.afinidad_txt(r))), True)

        def cita(act):
            def f():
                r = p.relacion(pid)
                if p.hielo_ex(r):
                    app.son("error")
                    app.decir(p.frase_hielo("cita", pers), True)
                    return
                if encuentros.en_persona_activo(p):              # cara a cara: se viene contigo y el plan pasa al llegar al sitio
                    if not en_persona():
                        app.son("error")
                        app.decir(encuentros.lejos_txt(p, pers) + tr(" Para una cita, propón quedar."), True)
                        return
                    if p.mision:
                        app.son("error")
                        app.decir(tr("Estás en mitad de una misión. La cita, mejor cuando acabes."), True)
                        return
                    if j.estrellas:
                        app.son("error")
                        app.decir(tr("Con la policía detrás no es momento de citas."), True)
                        return
                    if r["afinidad"] < 10:
                        app.decir(tr('{nombre} apenas te conoce. Charlad primero algún día.').format(nombre=(pers['nombre'])), True)
                        return
                    if r.get("hoy", {}).get("cita") == p.dia:
                        app.decir(tr("Ya habéis quedado hoy. Mejor otro día."), True)
                        return
                    from . import sistemas
                    if p.acompanante and p.acompanante.get("pid") == pid:
                        if not encuentros.sitios_de(act):
                            app.decir(tr('Ya vais juntos. Seguid paseando.'), True)
                            return
                        p.acompanante["plan"] = act["id"]
                        sitio = encuentros.sitio_para(p, act, p.lugar_cercano(16) or p.lug(pers["lugar"]))
                        _volver_al_juego(p)
                        if sitio is not None:
                            p.gps_a_lugar(sitio)
                        p.decir(tr('{nombre}: el plan pasa al llegar a {v}.').format(nombre=(act['nombre']), v=(sitio.nombre if sitio else tr('un sitio que sirva'))), True)
                        return
                    if sistemas.empezar_paseo(p, pers, plan=act if encuentros.sitios_de(act) else None):
                        _volver_al_juego(p)
                    return
                if not en_mi_mapa():
                    return lejos()
                if j.estrellas:
                    app.son("error")
                    app.decir(tr("Con la policía detrás no es momento de citas."), True)
                    return
                if r["afinidad"] < 10:
                    app.decir(tr('{nombre} apenas te conoce. Charlad primero algún día.').format(nombre=(pers['nombre'])), True)
                    return
                if p._hecho_hoy(r, "cita"):
                    app.decir(tr("Ya habéis quedado hoy. Mejor otro día."), True)
                    return
                r["hoy"].pop("cita", None)
                encuentros.iniciar_cita(p, pers, act)
            return f

        def menu_cita():
            app.abrir(Menu(app, tr('Cita con {nombre}. Tienes {dinero} euros').format(nombre=(pers['nombre']), dinero=(j.dinero)),
                           [Opcion(tr('{nombre}: {precio} euros').format(nombre=(a['nombre']), precio=(a['precio'])), cita(a),
                                   ayuda=tr('Dura {horas} horas. Si es uno de sus planes favoritos, os acerca mucho más y te sube más el ánimo. Una cita al día, y hace falta que ya os conozcáis un poco.').format(horas=(a['horas'])))
                            for a in p.dato_adulto("actividades")] + [Opcion(tr("Volver"), lambda: app.cerrar())],
                           intro=tr("Cada persona tiene sus planes favoritos. Descúbrelos") + (tr(". Se viene contigo y el plan pasa al llegar al sitio") if encuentros.en_persona_activo(p) else "")))

        def regalo(g):
            def f():
                r = p.relacion(pid)
                mano = en_persona()
                if not mano and not encuentros.en_persona_activo(p) and not en_mi_mapa():
                    return lejos()
                if p._hecho_hoy(r, "regalo"):
                    app.decir(tr("Ya le has hecho un regalo hoy. No hay que agobiar."), True)
                    return
                envio = 0 if mano else encuentros.AJ.entero("regalo_envio")
                if not p.pagar(g["precio"] + envio):
                    r["hoy"].pop("regalo", None)
                    return
                favorito = pers.get("regalo") == g["id"]
                p.son("regalo", cat="interfaz")
                afin = g["afinidad"] * (2 if favorito else 1)
                if not mano:                                     # a domicilio se agradece, pero no es lo mismo que en mano
                    afin = max(1, int(round(afin * encuentros.AJ("regalo_envio_pct") / 100.0)))
                p.sumar_afinidad(pid, afin)
                if j.convive == pid:
                    p.peticion_cumplida("regalo")
                if mano:
                    app.decir(tr('Le regalas {lower}. {v} Ahora {afinidad_txt}.').format(lower=(g['nombre'].lower()), v=(tr('¡Le encanta! Has acertado de lleno.') if favorito else tr('Lo agradece con una sonrisa.')), afinidad_txt=(p.afinidad_txt(r))), True)
                else:
                    app.decir(tr('Le mandas {lower} a domicilio, con {envio} euros de envío. {nombre} te escribe para darte las gracias{v}. En mano le habría hecho más ilusión. Ahora {afinidad_txt}.').format(lower=(g['nombre'].lower()), envio=(envio), nombre=(pers['nombre']), v=(tr(': ha acertado de lleno') if favorito else ''), afinidad_txt=(p.afinidad_txt(r))), True)
            return f

        def menu_regalo():
            mano = en_persona() or not encuentros.en_persona_activo(p)
            app.abrir(Menu(app, tr('Regalo para {nombre}').format(nombre=(pers['nombre'])) + ("" if mano else tr(', a domicilio, con {entero} euros de envío').format(entero=(encuentros.AJ.entero('regalo_envio')))) + tr('. Tienes {dinero} euros').format(dinero=(j.dinero)),
                           [Opcion(tr('{nombre}: {precio} euros').format(nombre=(g['nombre']), precio=(g['precio'])), regalo(g),
                                   ayuda=tr("Si es su regalo favorito, le encanta y os acerca el doble. Un regalo al día; a domicilio se paga el envío y se agradece menos."))
                            for g in p.dato_adulto("regalos")] + [Opcion(tr("Volver"), lambda: app.cerrar())]))

        def pedir():
            r = p.relacion(pid)
            if not en_persona():
                app.son("error")
                app.decir(encuentros.lejos_txt(p, pers) + tr(" Algo así se pide a la cara."), True)
                return
            if j.pareja == pid:
                app.decir(tr("Ya sois pareja."), True)
            elif j.pareja:
                otra = p.persona_social(j.pareja)
                app.decir(tr('Ya tienes pareja: {nombre}. Tendrías que romper antes.').format(nombre=(otra['nombre'])), True)
            elif p.hielo_ex(r):
                app.decir(p.frase_hielo("pedir", pers), True)
            elif r["afinidad"] < 60:
                app.decir(tr('{nombre} sonríe, pero te dice que aún es pronto. Necesitáis más tiempo juntos.').format(nombre=(pers['nombre'])), True)
            else:
                r["estado"] = "pareja"
                j.pareja = pid
                r["ultimo"] = p.dia
                p.son("pareja", cat="interfaz")
                p.cambiar_animo(20)
                app.decir(tr('{nombre} dice que sí. Desde hoy sois pareja. Cuida la relación: si pasas días sin dar señales, o si se entera de que hay alguien más, lo vuestro se resentirá.').format(nombre=(pers['nombre'])), True)

        def noche():
            r = p.relacion(pid)
            if encuentros.en_persona_activo(p) and not en_persona():
                app.son("error")
                app.decir(encuentros.lejos_txt(p, pers), True)
                return
            if p.mision:
                app.son("error")
                app.decir(tr("Estás en mitad de una misión. Mejor cuando acabes."), True)
                return
            if p.apesta():                                       # primero, una ducha (necesidades.py)
                from .necesidades import AJ as NEC
                app.decir(NEC.frase("frases_gesto_sucio", n=pers["nombre"]), True)
                return
            if not en_mi_mapa():
                return lejos()
            if r["afinidad"] < 55 and j.pareja != pid:
                app.decir(tr('{nombre} te dice que prefiere ir despacio.').format(nombre=(pers['nombre'])), True)
                return
            if j.estrellas:
                app.son("error")
                app.decir(tr("Con la policía detrás, mejor otro día."), True)
                return
            casa = next((l for l in p.mundo.lugares.values() if l.tipo == "casa" and l.id in j.propiedades), None)
            if casa is None:
                donde = tr("un hotel")
            else:
                donde = casa.nombre
            if r.get("hoy", {}).get("noche") == p.dia:
                app.decir(tr("Hoy ya habéis estado juntos."), True)
                return
            from .intimidad import ENCUENTROS

            def elegir(tipo):
                def f():
                    gusta = tipo == pers.get("noche", "romantico")
                    def confirmar():
                        if casa is None and not p.pagar(p.precio("hotel_cita", 70)):
                            return False
                        p._hecho_hoy(r, "noche")
                        p.sumar_afinidad(pid, 9 if gusta else 5)
                        p.celos(pid)
                        return True
                    p.encuentro(pers["nombre"], tipo, donde, pid=pid, confirmar=confirmar)
                return f
            mm = Menu(app, tr('La noche con {nombre}').format(nombre=(pers['nombre'])),
                      [Opcion(ENCUENTROS[t][0], elegir(t), ayuda=tr("Pasáis la noche y pasan unas horas. Si es la manera que prefiere, os acerca más. Lo que compraste para la ocasión se gasta y se nota."))
                       for t in ENCUENTROS]
                      + [Opcion(tr("Mejor otro día"), lambda: app.cerrar(mm))],
                      intro=tr("Cada persona tiene su manera preferida. Lo que hayas comprado para la ocasión se nota"))
            app.abrir(mm)

        def romper():
            r = p.relacion(pid)
            p.marcar_ruptura(r)
            r["afinidad"] = max(0, r["afinidad"] - 40)
            r.pop("compromiso", None)
            if j.pareja == pid:
                j.pareja = ""
            if j.convive == pid:                                 # y si vivía contigo, se va de casa
                p.fin_convivencia("sola", callar=True)
            p.son("ruptura", cat="interfaz")
            p.cambiar_animo(-10)
            app.cerrar()
            app.decir(tr('Lo dejas con {nombre}. No ha sido agradable.').format(nombre=(pers['nombre'])), True)

        def hablar():
            """Hablarle con tus palabras, como a cualquiera de la calle, pero a alguien que ya conoces. Si no estáis juntos, por teléfono."""
            from .charla import interpretar
            from .entidades import Persona
            from .menus import EntradaTexto
            r = p.relacion(pid)
            fichas = p.__dict__.setdefault("_fichas_conocidos", {})          # lo que os habéis dicho hoy: se recuerda mientras dure la sesión
            f = fichas.get(pid)
            if f is None:
                mujer = pers.get("genero", "m" if pers["nombre"].lower().endswith(("a", "e")) and pers["id"] not in ("andres", "ibai") else "h") == "m"
                oficio = pers["desc"].split(".")[0].split(" de ")[0].split(" del ")[0].strip().lower()
                f = fichas[pid] = {"nombre": pers["nombre"], "genero": "m" if mujer else "h", "edad": pers["edad"], "oficio": oficio or "vecino",
                                   "caracter": "hablador", "confianza": 0, "frases": 0, "disponible": True, "le_atraen": "hm", "invitado": True,
                                   "limosna": False, "presentado": True, "ofendido": False}
            f["confianza"] = int(min(60, r["afinidad"] * 0.6)) + (15 if j.pareja == pid else 0)
            f["caracter"] = pers.get("caracter") or ("amable" if r["afinidad"] >= 40 or j.pareja == pid else "hablador")
            x, y = p.pos()
            q = Persona("civil", x, y, pers["nombre"])
            q.ficha = f

            def hecho(texto):
                if not texto.strip():
                    return
                if p.hielo_ex(r):                                # recién rota la relación: no contesta, o te corta
                    return app.decir(p.frase_hielo("mensaje", pers), True)
                antes = f["confianza"]
                if not p.ia_disponible() and interpretar(texto)[0] == "ligar":
                    return app.decir(f"{pers['nombre']}: " + random.choice([tr("Eso me lo dices en persona, y con una cena delante."), tr("Qué cosas tienes. Anda, proponme un plan."), tr("Mira que eres. Luego hablamos.")]), True)
                if p.ia_disponible():
                    app.decir(tr("Espera un momento."), True)
                app.decir(p.responder_libre(q, texto), True)
                if f["confianza"] > antes and not p._hecho_hoy(r, "hablar"):
                    p.sumar_afinidad(pid, 2)                             # hablar acerca, pero una vez al día
                    p.cambiar_animo(1)
                elif f["confianza"] < antes - 5:
                    p.sumar_afinidad(pid, -3)
            donde = "" if (aqui is not None and aqui.id == pers["lugar"]) else tr(" por teléfono")
            app.abrir(EntradaTexto(app, tr('Qué le dices a {nombre}{donde}').format(nombre=(pers['nombre']), donde=(donde)), hecho, maximo=200,
                                   ayuda=tr("Escribe con tus palabras: cómo te ha ido, una pregunta, un cumplido, lo que quieras. ") +
                                         (tr("Con el modo IA, contesta con libertad.") if p.ia_disponible() else tr("El juego entiende de qué va lo que escribes y contesta a eso."))))

        def ops():
            r = j.relaciones.get(pid)
            l = p.lug(pers["lugar"])
            from . import vestuario
            lista = [Opcion(tr('{nombre}, {edad} años. {desc} ').format(nombre=(pers['nombre']), edad=(pers['edad']), desc=(pers['desc'])) + encuentros.donde_txt(p, pers)
                            + (" " + vestuario.estilo_sabido(p, pers) if vestuario.estilo_sabido(p, pers) else ""),
                            ayuda=tr("Quién es, dónde suele estar y, si ya lo sabes, el estilo de ropa que le gusta. Ir vestido a su gusto se nota en las citas."))]
            if r is None:
                return lista + [Opcion(tr("Aún no os conocéis. Ve a ese lugar y preséntate desde este mismo menú"),
                                       ayuda=tr("Cuando estés en el sitio donde suele estar, abre su ficha desde Vida social y os presentáis. Hasta entonces no podéis hacer nada juntos.")),
                                Opcion(tr("Volver"), lambda: app.cerrar())]
            estado = {"pareja": tr("Sois pareja"), "ex": tr("Lo dejasteis")}.get(r["estado"], tr("Os estáis conociendo"))
            if p.hielo_ex(r):
                d = p.hielo_ex(r)
                estado += tr(", y aún no quiere saber nada de ti: se le pasará en un día") if d == 1 else tr(', y aún no quiere saber nada de ti: se le pasará en unos {d} días').format(d=(d))
            if r["estado"] == "pareja" and r.get("compromiso"):
                estado = tr("Estáis prometidos") if r["compromiso"] == "prometidos" else tr("Estáis casados") if r["compromiso"] == "casados" else tr("Estáis ") + r["compromiso"]
            herida = encuentros.desconfianza(p, pid) if j.pareja == pid else 0
            lista.append(Opcion(lambda: tr('{estado}. {capitalize}. Habéis tenido {get} citas').format(estado=(estado), capitalize=(p.afinidad_txt(p.relacion(pid)).capitalize()), get=(p.relacion(pid).get('citas', 0)))
                                + (". " + encuentros.AJ.frase("frases_desconfia", d=encuentros.desconfianza(p, pid)) if j.pareja == pid and encuentros.desconfianza(p, pid) else ""),
                                ayuda=tr("Cómo va vuestra relación y cuántas citas lleváis. Las charlas, las citas y los regalos os acercan; si pasas días sin dar señales, se resiente.")))
            from .intimidad import GESTOS
            cara = en_persona()
            lista += [Opcion(tr("Charlar un rato") if cara else tr("Llamarle por teléfono"), charlar,
                             ayuda=tr("En persona, charlar os acerca más que una llamada. Una vez al día.")),
                      Opcion(tr("Hablarle con tus palabras"), hablar, ayuda=tr("Le escribes lo que quieras y te contesta, igual que al hablar con la gente de la calle. Si no estáis en el mismo sitio, por teléfono. "
                                                                         "Hablar a menudo os acerca un poco, una vez al día.")),
                      Opcion(tr("Proponer una cita"), menu_cita, ayuda=tr("En persona: elige el plan y se viene contigo; el plan pasa al llegar al sitio. Si no estáis juntos, propón quedar.")),
                      Opcion(tr("Quedar en un sitio a una hora"), lambda: encuentros.menu_quedar(p, pers, al_terminar=lambda: mf.refrescar(False)),
                             ayuda=tr("Desde el móvil: eliges el plan y la hora, y el juego busca un sitio que sirva. Media hora antes te lo recuerda. "
                                   "Si llegas a tiempo, el plan se vive allí; si no apareces, plantón, y le sienta mal.")),
                      Opcion(tr("Hacerle un regalo") if cara else tr("Mandarle un regalo a domicilio"), menu_regalo,
                             ayuda=tr("En mano, como siempre. A domicilio cuesta el envío y se agradece algo menos."))]
            if herida:
                lista.append(Opcion(tr("Pedirle perdón"), exige(lambda: (encuentros.pedir_perdon(p, pers), mf.refrescar(False))),
                                    ayuda=tr("En persona, una vez al día. Si te escucha, la herida se cierra antes; si no, insistir hoy no sirve.")))
            from . import sistemas
            if p.acompanante and p.acompanante["pid"] == pid:
                lista.append(Opcion(tr("Despedirte: el paseo termina aquí"), lambda: (app.cerrar(), sistemas.terminar_paseo(p)),
                                    ayuda=tr("Se despide y vuelve a lo suyo. Si lo habéis pasado bien, os acerca, te sube el ánimo y cuenta como una cita.")))
            elif aqui is not None and aqui.id == pers["lugar"]:
                lista.append(Opcion(tr("Proponerle salir contigo a dar una vuelta"), lambda: sistemas.empezar_paseo(p, pers) and [app.cerrar(x) for x in list(app.pila) if x is not p],
                                    ayuda=tr("Se viene contigo de verdad: te sigue a pie y sube al vehículo que lleves. Pasear, llevarle a comer, a un bar, al cine o a la feria le gusta y os acerca. "
                                          "Si te metes en líos con la policía, no. Una vez al día; dura como mucho tres horas del juego.")))
            adulto = p.modo_adulto()                             # sin el contenido para adultos: un beso, un baile, y nada de noches
            atrae = te_atrae(p, pers) or j.pareja == pid         # a quien no te atrae (Opciones, Me atraen) solo se le trata como amistad
            lista += [Opcion(GESTOS[g][0], exige(lambda g=g: p.gesto(pid, pers, g)), ayuda=tr("Un gesto de cariño, cara a cara. Hace falta cierta confianza, y cada uno se puede repetir una vez al día."))
                      for g in GESTOS if atrae and (adulto or g in ("beso", "baile"))]
            if adulto and atrae:
                lista += [
                      Opcion(tr("Pasar la noche juntos"), noche, ayuda=tr('Necesitáis mucha confianza. Vais a una de tus casas en esta localidad o, si no tienes, a un hotel por {precio} euros.').format(precio=(p.precio('hotel_cita', 70))))]
            if j.pareja == pid:
                from . import convivencia
                lista.append(Opcion(tr("Hacer un plan juntos"), exige(lambda: convivencia.menu_planes(p, pers), mision=True),
                                    ayuda=tr("Planes para parejas: un paseo sin rumbo, el cine, una cena, una travesía en barco, una tarde de playa... Cada uno se cuenta con una escena distinta cada vez. Uno al día.")))
                lista.append(Opcion(tr('Darle dinero a {nombre} para que se compre algo').format(nombre=(pers['nombre'])), lambda: convivencia.menu_dinero(p, pers, al_terminar=lambda: mf.refrescar(False)),
                                    ayuda=tr("Le das algo de dinero, a tu elección. Os acerca más cuanto más le das, una vez al día, y al día siguiente te cuenta qué se compró.")))
                if j.convive == pid:
                    casa = p.casa_comun()
                    lista.append(Opcion(tr('Vive contigo, en {v}').format(v=(p.nombre_lugar(casa) if casa else tr('tu casa'))) + (". " + p.peticion_txt() if p.peticion_txt() else "") + tr(". Intro para mudaros a otra casa tuya"),
                                        lambda: convivencia.menu_mudanza(p, pers, al_terminar=lambda: mf.refrescar(False)),
                                        ayuda=tr("Te la encuentras en esa casa: en su menú puedes hablar, comer en compañía, hacer planes o pedirle que se vaya. "
                                              "Intro aquí elige otra de tus casas, de esta localidad o de otra, para iros a vivir allí los dos.")))
                elif p.convivencia_activa():
                    def mudarse():
                        casas = p.casas_para_vivir()
                        if len(casas) > 1:                       # con varias casas, eliges tú a cuál
                            convivencia.menu_mudanza(p, pers, al_terminar=lambda: mf.refrescar(False), pedir=True)
                            return
                        ok, frase = p.pedir_convivir(pers, (casas or [None])[0])
                        app.decir(frase, True)
                    lista.append(Opcion(tr("Pedirle que se venga a vivir contigo"), exige(mudarse),
                                        ayuda=tr("Cada persona decide. Hace falta que la relación vaya muy bien y haber tenido varias citas, y hay quien no deja su casa por nadie. "
                                              "Si tienes varias casas, eliges en cuál vivís, de esta localidad o de otra; luego os podéis mudar a otra.")))
                from .honrado import AJ as HON
                comp = p.relacion(pid).get("compromiso", "")
                if not comp:
                    lista.append(Opcion(tr("Pedirle que os prometáis"), exige(lambda: (p.hon_comprometerse(pers), mf.refrescar(False))),
                                        ayuda=tr("Hace falta que estéis muy unidos y haber tenido bastantes citas. Prometidos, podéis vivir juntos y preparar la boda.")))
                elif comp == "prometidos":
                    lista.append(Opcion(tr('Casaros: una boda sencilla, {entero} euros').format(entero=(HON.entero('boda_precio'))), exige(lambda: (p.hon_casarse(pers), mf.refrescar(False)), mision=True),
                                        ayuda=tr('Unos días después de prometeros. Una ceremonia sencilla con la familia y los amigos. Los vecinos lo ven con buenos ojos.')))
                else:
                    lista.append(Opcion(tr('Estáis casados desde el día {get}').format(get=(p.relacion(pid).get('boda_dia', p.dia))),
                                        ayuda=tr("Es el último paso de la relación. Si rompéis, se acaba también el matrimonio.")))
                lista.append(Opcion(tr("Romper la relación"), romper,
                                    ayuda=tr("Lo dejáis al momento, sin pedir confirmación. La relación cae mucho, tu ánimo baja y, si vivíais juntos, se va de casa.")))
            elif atrae:
                lista.append(Opcion(tr("Pedirle que sea tu pareja"), pedir, ayuda=tr("Hace falta mucha química. Tener pareja sube tu ánimo cada día, pero hay que cuidarla.")))
            if j.pareja != pid:
                lista.append(Opcion(tr('Quitar a {nombre} de tu móvil').format(nombre=pers["nombre"]), lambda: quitar_del_movil(pers),
                                    ayuda=tr("Deja de salir en Vida social. No se pierde lo que habéis vivido: al final de la lista, en Personas que has quitado, la puedes recuperar.")))
            lista.append(Opcion(tr("Volver"), lambda: app.cerrar()))
            return lista
        if nuevo and aqui is not None and aqui.id == pers["lugar"]:
            p.relacion(pid)
            j.stats["conocidos"] = j.stats.get("conocidos", 0) + 1
            app.decir(tr('Te presentas a {nombre}. {desc}').format(nombre=(pers['nombre']), desc=(pers['desc'])), True)
        mf = Menu(app, pers["nombre"], ops)
        app.abrir(mf)

    def quitar_del_movil(pers):
        if pers["id"] not in j.ocultos_social:
            j.ocultos_social.append(pers["id"])
        app.cerrar()
        app.son("menu_atras")
        app.decir(tr('{nombre} ya no sale en tu móvil. La puedes recuperar al final de la lista.').format(nombre=pers["nombre"]), True)
        if app.pila and getattr(app.pila[-1], "es_vida_social", False):
            app.pila[-1].refrescar(False)

    def recuperar():
        def ops_ocultos():
            lista = []
            for pers in p.dato_adulto("personas"):
                if pers["id"] in j.ocultos_social:
                    lista.append(Opcion(pers["nombre"], (lambda pers=pers: (j.ocultos_social.remove(pers["id"]), app.decir(tr('{nombre} vuelve a salir en tu móvil.').format(nombre=pers["nombre"]), True),
                                                                           mo.refrescar(False))), ayuda=tr("Intro la vuelve a poner en Vida social.")))
            return lista + [Opcion(tr("Volver"), lambda: app.cerrar())]
        mo = Menu(app, tr("Personas que has quitado de tu móvil"), ops_ocultos, al_cerrar=lambda: m_social.refrescar(False) if m_social else None)
        app.abrir(mo)

    m_social = None

    def ops():
        lista = []
        ocultas = 0
        for pers in p.dato_adulto("personas"):
            l = p.lug(pers["lugar"])
            if l is None:
                continue
            if pers["id"] in j.ocultos_social:
                ocultas += 1
                continue
            r = j.relaciones.get(pers["id"])
            if r is None and not te_atrae(p, pers):              # a quien no conoces y no te atrae no se te ofrece como relación
                continue
            if r is None:
                if aqui is not None and aqui.id == pers["lugar"]:
                    lista.append(Opcion(tr('Presentarte a {nombre}, que está aquí mismo').format(nombre=(pers['nombre'])), (lambda pers=pers: ficha(pers)),
                                        ayuda=tr("Te presentas y se abre su ficha: desde ahí podéis charlar, quedar o haceros regalos.")))
                else:
                    lista.append(Opcion(tr('Alguien a quien no conoces suele estar en {nombre_lugar}').format(nombre_lugar=(p.nombre_lugar(l))), (lambda pers=pers: ficha(pers)),
                                        ayuda=tr("Abre lo que sabes de esa persona. Para conoceros, ve a ese lugar y preséntate desde este menú.")))
            else:
                marca = tr(", tu pareja") if j.pareja == pers["id"] else tr(", ex") if r["estado"] == "ex" else ""
                lista.append(Opcion(f"{pers['nombre']}{marca}: {p.afinidad_txt(r)}", (lambda pers=pers: ficha(pers)),
                                    ayuda=tr("Abre su ficha: cómo va lo vuestro y lo que podéis hacer, en persona o por teléfono.")))
                from . import encuentros
                plan = r.get("invitacion")
                if plan and plan["min"] > encuentros.ahora(p) and r.get("estado") != "ex":
                    detalle = encuentros.texto_invitacion(p, plan)
                    if detalle:
                        titulo = tr("Invitación de {n}").format(n=pers["nombre"]) + ": " + detalle
                        lista.append(Opcion(titulo, lambda pers=pers: encuentros.atender_invitacion(p, pers)))
        from . import encuentros
        if encuentros.quedadas(p):
            lista.append(Opcion(tr('Tus quedadas: {len}').format(len=(len(encuentros.quedadas(p)))), lambda: encuentros.menu_quedadas(p),
                                ayuda=tr("Con quién has quedado, dónde y a qué hora. Intro marca el sitio en el GPS; también puedes anularla.")))
        lista.append(Opcion(lambda: tr('Tu ánimo es {animo_txt}. En la calle, {reputacion_txt}').format(animo_txt=(p.animo_txt()), reputacion_txt=(p.reputacion_txt())),
                            ayuda=tr("Cómo estás de ánimo y lo que se dice de ti en la calle. Tener pareja sube el ánimo cada día; las citas y los buenos ratos también, y romper lo baja.")))
        if ocultas:
            lista.append(Opcion(tr('Personas que has quitado de tu móvil: {n}').format(n=ocultas), recuperar,
                                ayuda=tr("Intro abre la lista para volver a poner a alguien en Vida social.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar()))
        return lista
    if directo:                                              # desde el propio local, vas derecho a la persona
        pers = next((x for x in p.dato_adulto("personas") if x["id"] == directo), None)
        if pers is not None:
            ficha(pers)
        return
    m_social = Menu(app, tr("Vida social") if p.modo_adulto() else tr("Vida sentimental"), ops, intro=tr("Aquí están las personas con las que puedes tener una relación"))
    m_social.es_vida_social = True
    app.abrir(m_social)


def te_atrae(p, pers):
    """¿Te puede atraer esa persona, según la opción Me atraen? Sin género en sus datos (un mod antiguo), sí."""
    g = pers.get("genero")
    return g not in ("h", "m") or p.me_atrae(g)


# =================================================================== sustancias
def menu_sustancias(p):
    app = p.app
    j = p.j
    if not p.modo_adulto():
        return

    def tomar(ident):
        def f():
            p.consumir(ident)
            if app.pila and app.pila[-1] is m:
                m.refrescar(False)
        return f

    def ops():
        lista = []
        for s in p.dato_adulto("sustancias"):
            n = j.sustancias.get(s["id"], 0)
            if n > 0:
                lista.append(Opcion(tr('Tomar {lower}: tienes {n}').format(lower=(s['nombre'].lower()), n=(n)), tomar(s["id"]), ayuda=s["desc"]))
        if not lista:
            lista.append(Opcion(tr("No llevas nada encima"), ayuda=tr("Lo que compres a un proveedor aparece aquí para tomarlo.")))
        activos = [p.sustancia(e["id"])["nombre"] + (tr(", bajón") if e.get("bajon") else "") + tr(', {int} segundos').format(int=(int(e['t']))) for e in j.efectos if p.sustancia(e["id"])]
        lista.append(Opcion(tr("Efectos ahora mismo: ") + ("; ".join(activos) if activos else "ninguno"),
                            ayuda=tr("Lo que tienes en el cuerpo y los segundos que le quedan a cada efecto. Detrás de algunos llega un bajón.")))
        enganches = [tr('{nombre} {int} de 100').format(nombre=(p.sustancia(s)['nombre']), int=(int(n))) for s, n in j.adiccion.items() if p.sustancia(s)]
        lista.append(Opcion(tr("Dependencia: ") + (", ".join(enganches) if enganches else "ninguna") + (tr(". Tienes síndrome de abstinencia") if p._abstinencia() else ""),
                            ayuda=tr("A partir de 40 necesitas tomar cada día o sufres abstinencia. Baja sola poco a poco, y en un hospital te desintoxican.")))
        lista.append(Opcion(tr('Llevas {carga} de {v} unidades de mercancía; te caben {hueco_mercancia} más. {moc_txt}. Para vender, ponte junto a un peatón sin arma en la mano y pulsa E').format(carga=(p.carga()), v=(100), hueco_mercancia=(p.hueco_mercancia()), moc_txt=(p.moc_txt())),
                            ayuda=tr("La mercancía va en la mochila: cada diez unidades ocupan un hueco. Lo que no quieras llevar encima, guárdalo en el armario de una de tus casas.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar()))
        return lista
    m = Menu(app, tr("Sustancias"), ops, intro=tr("F1 explica el efecto de cada una"))
    app.abrir(m)


# ========================================================================= club
def club(p, l):
    app = p.app
    j = p.j

    def copa():
        if p.pagar(p.precio("club_copa", 15)):
            p.consumir("alcohol", de_inventario=False)

    def espectaculo():
        if p.pagar(p.precio("club_espectaculo", 20)):
            p.pasar_horas(1)
            p.cambiar_animo(5)
            app.decir(tr('Ves el espectáculo desde la barra. Sales una hora después, a las {hora_txt}.').format(hora_txt=(p.hora_txt())), True)

    def compania():
        if j.estrellas:
            app.son("error")
            app.decir(tr("El portero te ha reconocido de las noticias y no te deja pasar al reservado."), True)
            return
        if not p.pagar(p.precio("club_compania", 150)):
            return
        p.pasar_horas(1)
        j.stats["pagos"] = j.stats.get("pagos", 0) + 1
        p.son("pasan_horas", cat="interfaz")
        _volver_al_juego(p)
        app.abrir(Dialogo(app, [(tr("Narrador"), tr('Pagas, subís a una habitación y la puerta se cierra. Una hora después estás otra vez en la calle. Son las {hora_txt}.').format(hora_txt=(p.hora_txt())))]))
        p.cambiar_animo(14)
        if j.intimos.get("preservativos", 0) > 0:
            j.intimos["preservativos"] -= 1
        elif not j.its and random.random() < 0.15:
            j.its = p.dia
        azar = random.random()
        if azar < 0.08 and p.mundo.policia:
            multa = min(j.dinero, p.precio("club_redada", 300))
            j.dinero -= multa
            p.decir(tr('¡Redada! La policía entra en el club y te cae una multa de {multa} euros.').format(multa=(multa)))
            p.poner_busqueda(1)
        elif azar < 0.14:
            robo = int(j.dinero * 0.1)
            j.dinero -= robo
            p.decir(tr('Al salir notas la cartera más ligera: te faltan {robo} euros.').format(robo=(robo)))
        p.celos()
    def bailar():
        if not p.pagar(p.precio("club_baile", 5)):
            return
        p.pasar_horas(1)
        p.cambiar_animo(6)
        p.son("cita", cat="interfaz")
        if random.random() < 0.45:
            from .charla import ficha
            from .entidades import Persona
            x, y = p.mundo.punto_libre(j.x + random.uniform(-3, 3), j.y + random.uniform(-3, 3))
            q = Persona("civil", x, y)
            q.estado = "quieto"
            f = ficha(q)
            f["confianza"], f["disponible"] = 25, True
            if p.cfg["mi_genero"] != "x" and p.cfg["mi_genero"] not in f["le_atraen"]:
                f["le_atraen"] += p.cfg["mi_genero"]
            p.personas.append(q)
            app.decir(tr('Bailas una hora en la pista. Alguien no deja de mirarte: al salir está a tu lado. Háblale con la tecla J. Son las {hora_txt}.').format(hora_txt=(p.hora_txt())), True)
        else:
            app.decir(tr('Bailas una hora en la pista y sales con otra cara. Son las {hora_txt}.').format(hora_txt=(p.hora_txt())), True)

    def privado():
        if p.pagar(p.precio("club_privado", 60)):
            p.pasar_horas(0.5)
            p.cambiar_animo(9)
            p.son("cita", cat="interfaz")
            app.decir(tr("Pase privado. Luces bajas, música lenta y un baile solo para ti, a un palmo y sin tocar. Sales con el pulso acelerado."), True)

    def tienda():
        mt = Menu(app, lambda: tr('Tienda discreta del club. Tienes {dinero} euros').format(dinero=(j.dinero)),
                  [Opcion((lambda a=a: tr('{nombre}: {precio} euros. Tienes {get}').format(nombre=(a['nombre']), precio=(a['precio']), get=(j.intimos.get(a['id'], 0)))), (lambda a=a: p.comprar_articulo(a)), ayuda=a["desc"]) for a in p.articulos_intimos()]
                  + [Opcion(tr("Volver"), lambda: app.cerrar(mt))])
        app.abrir(mt)
    m = Menu(app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(j.dinero)), [
        Opcion(tr('Tomar una copa: {precio} euros').format(precio=(p.precio('club_copa', 15))), copa, ayuda=tr("Es alcohol: sube el ánimo, pero cada copa te hace caminar más torcido y apuntar peor.")),
        Opcion(tr('Bailar en la pista: {precio} euros').format(precio=(p.precio('club_baile', 5))), bailar, ayuda=tr("Sube el ánimo, y es buen sitio para conocer a alguien.")),
        Opcion(tr('Ver el espectáculo: {precio} euros').format(precio=(p.precio('club_espectaculo', 20))), espectaculo, ayuda=tr("Lo ves desde la barra: pasa una hora y te sube un poco el ánimo.")),
        Opcion(tr('Pase privado: {precio} euros').format(precio=(p.precio('club_privado', 60))), privado, ayuda=tr("Un baile sensual solo para ti. Sube el ánimo.")),
        Opcion(tr("Tienda discreta: preservativos, lencería y más"), tienda, ayuda=tr("Lo que compres aquí mejora tus noches y sirve de regalo.")),
        Opcion(tr('Pagar por compañía: {precio} euros').format(precio=(p.precio('club_compania', 150))), compania, ayuda=tr("Sube el ánimo. Puede haber redada, pueden robarte y, si tienes pareja, puede enterarse. Sin preservativos hay riesgo para tu salud.")),
        Opcion(tr("Volver"), lambda: app.cerrar())])
    app.abrir(m)


# ==================================================================== proveedor
def proveedor(p, l):
    app = p.app
    j = p.j
    ilegales = [s for s in p.dato_adulto("sustancias") if not s.get("legal")]

    def comprar(s, n):
        def f():
            precio, _ = p.precio_sustancia(s["id"], l)
            if n > p.hueco_mercancia():                          # el tope de cien y el sitio de la mochila (mochila.py)
                app.son("error")
                app.decir(tr('No te cabe: llevas {carga} de 100 unidades y te caben {hueco_mercancia} más. {moc_txt}.').format(carga=(p.carga()), hueco_mercancia=(p.hueco_mercancia()), moc_txt=(p.moc_txt())), True)
                return
            if p.pagar(precio * n):
                j.sustancias[s["id"]] = j.sustancias.get(s["id"], 0) + n
                p.son("trato", cat="interfaz")
                app.decir(tr('Compras {n} de {lower} por {v} euros. Llevas {v2}.').format(n=(n), lower=(s['nombre'].lower()), v=(precio * n), v2=(j.sustancias[s['id']])), True)
        return f

    def vender(s, n):
        def f():
            tengo = j.sustancias.get(s["id"], 0)
            k = tengo if n is None else min(n, tengo)
            if k <= 0:
                app.son("error")
                app.decir(tr("No llevas de eso."), True)
                return
            precio, _ = p.precio_sustancia(s["id"], l)
            cobro = int(precio * 0.85) * k
            j.sustancias[s["id"]] = tengo - k
            j.stats["vendido"] = j.stats.get("vendido", 0) + cobro
            p.son("trato", cat="interfaz")
            p.dar_dinero(cobro)
            p.hon_negro(cobro)                                   # dinero negro (capo.py)
            p.cambiar_reputacion(0.02 * k)
            app.decir(tr('Vendes {k} de {lower} por {cobro} euros. Te quedan {v}.').format(k=(k), lower=(s['nombre'].lower()), cobro=(cobro), v=(j.sustancias[s['id']])), True)
        return f

    def tratar(s):
        def titulo():
            precio, nota = p.precio_sustancia(s["id"], l)
            extra = {"ganga": tr(" Hoy está tirado de precio."), "escasez": tr(" Hoy hay escasez: está carísimo.")}.get(nota, "")
            if nota:
                p.son("precio_" + nota, cat="interfaz")
            return tr('{nombre}: {precio} euros la unidad.{extra} Llevas {get}. Tienes {dinero} euros').format(nombre=(s['nombre']), precio=(precio), extra=(extra), get=(j.sustancias.get(s['id'], 0)), dinero=(j.dinero))
        app.abrir(Menu(app, titulo, [Opcion(tr("Comprar 1"), comprar(s, 1), ayuda=tr("Pagas una unidad al precio de hoy en este proveedor. Va a la mochila, si te cabe.")),
                                     Opcion(tr("Comprar 10"), comprar(s, 10), ayuda=tr("Pagas diez unidades al precio de hoy. Tienen que caberte: cada diez unidades ocupan un hueco de la mochila, y llevas cien como mucho.")),
                                     Opcion(tr("Vender 10 al 85 por ciento del precio"), vender(s, 10), ayuda=tr("Si llevas menos de diez, vendes las que tengas. Te pagan en dinero negro y sube tu fama en la calle.")),
                                     Opcion(tr("Vender todo"), vender(s, None), ayuda=tr("Vendes todo lo que llevas de esto al 85 por ciento del precio de hoy, en dinero negro. Sube tu fama en la calle.")),
                                     Opcion(s["desc"], ayuda=tr("Lo que hace al tomarla. Lo que llevas se toma desde tus sustancias, con Mayúsculas Z.")),
                                     Opcion(tr("Volver"), lambda: app.cerrar())]))

    def ops():
        lista = []
        veto = p.proveedor_vetado(l)
        if veto:                                                 # le asaltaste: no te vende nada hasta que se le pase
            lista.append(Opcion(tr('Aquí no te venden nada: no han olvidado el asalto. Vuelve dentro de {veto} {v}').format(veto=(veto), v=(tr('día') if veto == 1 else tr('días'))),
                                ayuda=tr("Mientras dure el veto, compra a otro proveedor. Cuando pase, te vuelven a vender.")))
        elif p.factor_proveedor(l) > 1.0:
            lista.append(Opcion(tr("Te siguen vendiendo, pero más caro: es lo que tiene haberles asaltado"),
                                ayuda=tr("Durante unos días este proveedor te cobra más. Los demás te venden a su precio de siempre.")))
        for s in ilegales if not veto else []:
            precio, nota = p.precio_sustancia(s["id"], l)
            marca = {"ganga": tr(", ganga"), "escasez": tr(", escasez")}.get(nota, "")
            lista.append(Opcion(tr('{nombre}: {precio} euros{marca}. Llevas {get}').format(nombre=(s['nombre']), precio=(precio), marca=(marca), get=(j.sustancias.get(s['id'], 0))), (lambda s=s: tratar(s)), ayuda=s["desc"]))
        from . import laboratorio
        if not veto:
            lista.append(laboratorio.opcion_proveedor(p, Opcion))
        lista.append(Opcion(tr("Asaltar a este proveedor"), lambda: p.asaltar_proveedor(l),
                            ayuda=tr("Necesitas un arma de fuego en la mano. Tienen guardia, y a veces refuerzos que llegan en un vehículo. Si acabas con ellos te llevas la mercancía que te quepa y el dinero de la caja. "
                                  "Pero no se les olvida: ese proveedor deja de venderte unos días, o te sube los precios, o manda gente a por ti.")))
        if j.banda and not p.en_servidor:
            from . import golpes
            from .atracos import AYUDA_GOLPE, TEXTO_GOLPE
            lista.append(Opcion(TEXTO_GOLPE, lambda: golpes.preparar(p, l, lambda plan: p.asaltar_proveedor(l, plan), tr("el asalto")), ayuda=AYUDA_GOLPE))
        lista.append(Opcion(tr('Mochila: {carga} de 100 unidades. En la calle, {reputacion_txt}').format(carga=(p.carga()), reputacion_txt=(p.reputacion_txt())),
                            ayuda=tr("Los precios cambian cada día y en cada localidad: compra donde esté barato y vende donde esté caro, o al menudeo en la calle, que se paga mejor pero es más arriesgado.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar()))
        return lista
    app.abrir(Menu(app, lambda: tr('{nombre}. Tienes {dinero} euros').format(nombre=(l.nombre), dinero=(j.dinero)), ops, intro=tr("Los precios cambian cada día y son distintos en cada localidad")))


def desintoxicar(p):
    j = p.j
    if not j.adiccion:
        p.app.decir(tr("No tienes ninguna dependencia."), True)
    elif p.pagar(p.precio("desintoxicacion", 800)):
        j.adiccion = {}
        j.efectos = []
        p.pasar_horas(48)
        p.cambiar_animo(10)
        p.son("curar", cat="interfaz")
        p.app.decir(tr('Dos días en la clínica. Sales limpi[o|a] y con la cabeza despejada. Es el día {dia}, las {hora_txt}.').format(dia=(p.dia), hora_txt=(p.hora_txt())), True)
