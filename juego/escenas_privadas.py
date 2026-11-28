"""Escenas de una noche: una vuelta por estilo antes de repetir una situación."""
import random

from . import gente
from .i18n import tr
from .laboratorio import Noche
from .menus import Menu, Opcion


def momentos_descriptivos():
    return [
        (tr("{n} deja un hueco a su lado. De la calle llega el bajo de un coche parado en el semáforo. Cuando cambia la luz, podéis oír hasta el roce de una manga."), [
            (tr("Entrelazar los dedos"), "lento", tr("Al principio solo se tocan vuestros meñiques. {n} vuelve la palma hacia arriba y encaja la mano en la tuya.")),
            (tr("Acercarte para un beso"), "intenso", tr("Os encontráis a mitad de camino. Al separaros, {n} aún tiene los dedos prendidos de tu solapa.")),
            (tr("Invitarle a bailar ese bajo que ya se va"), "jugando", tr("{n} marca el ritmo en tu hombro. El coche ya ha doblado la esquina cuando por fin os sale la vuelta."))]),
        (tr("A esta distancia distingues una pequeña cicatriz junto a la ceja de {n}. Os habéis visto muchas veces desde el otro extremo de una habitación. Desde aquí la expresión es distinta."), [
            (tr("Preguntar cómo le gustaría que siguierais"), "pregunta", ""),
            (tr("Rozarle la mejilla con los nudillos"), "lento", tr("{n} inclina la cara un poco. Te sorprende el contraste entre el aire fresco de la habitación y el calor de su mejilla.")),
            (tr("Dejar que elija el siguiente gesto"), "cede", tr("{n} te acerca con una mano en la cintura. «Aquí.» Os quedáis frente a frente, las narices casi juntas."))]),
        (tr("La chaqueta se ha quedado enganchada entre los dos. {n} consigue soltarla y la deja caer sobre el respaldo. «Así, mucho mejor.»"), [
            (tr("Hacer una reverencia y ofrecerle la mano"), "jugando", tr("{n} te concede el baile con una seriedad impecable hasta que chocáis rodilla con rodilla. La risa os pilla en pleno abrazo.")),
            (tr("Devolverle el beso con ganas"), "intenso", tr("{n} contesta con un beso largo. Te llega el tintineo de unas llaves al caer del bolsillo. Ya las buscaréis luego.")),
            (tr("Abrazarle y dejar que el momento dure"), "lento", tr("La frente de {n} encuentra el hueco de tu hombro. Notas que suelta el aire. Tenías los hombros tensos y también tú los aflojas."))]),
        (tr("{n} te besa despacio. A tientas encuentras el borde de la cama y os sentáis sin separaros del todo. Desde aquí la calle parece lejos."), [
            (tr("Recostaros juntos un rato"), "lento", tr("Buscáis sitio para dos cabezas en una almohada. Cuando por fin lo encontráis, {n} te da un beso de buenas noches aunque todavía queda mucho para dormir.")),
            (tr("Dejar que te acerque a su manera"), "cede", tr("{n} apaga la lámpara y te guía por la mano hasta que os acomodáis. En la oscuridad te llega una frase dicha con una sonrisa. «Menudo día para acabar tan bien.»")),
            (tr("Compartir un último secreto al oído"), "jugando", tr("A {n} se le escapa la risa antes de que llegues al final. Te contesta con un secreto propio, tan bajito que solo tú vas a enterarte."))]),
    ]


class NocheDescriptiva(Noche):
    privada = True

    def empezar_con(self, apertura, con_relato):
        if con_relato:
            self.momentos = momentos_descriptivos()
        self._mostrar(apertura + " ")

    def _pausa(self):
        paso = self.menu
        self.app.cerrar(paso)

        def reanudar():
            self.app.cerrar(descanso)
            self.app.abrir(paso)

        descanso = Menu(self.app, tr("Os apartáis un momento. {n} pregunta si quieres seguir o dejarlo aquí.").format(n=self.nombre),
                        [Opcion(tr("Volver cuando ambos estéis listos"), reanudar),
                         Opcion(tr("Terminar aquí"), lambda: self.app.cerrar(descanso))])
        descanso.escena_privada = True
        self.app.abrir(descanso)

    def _fin(self, antes):
        self.al_acabar(antes.strip(), self.puntos / self.maximo)


def despedida_personal(pid):
    return {
        "lucia": tr("Lucía te pasa el pulgar por la ceja para apartarte el pelo. «Mírame. Con todo el ruido que hago cuando me gustas, igual se me ha olvidado decírtelo bajito.» Esta vez lo dice bajito."),
        "andres": tr("Andrés tiene una marca roja en el hombro de haberse apoyado en una costura. Le pasas el dedo por encima. «Esta noche me he olvidado hasta del reloj», murmura. Sigue en su muñeca, con la esfera vuelta hacia dentro."),
        "noa": tr("«Tenía una observación muy inteligente», dice Noa contra tu mejilla. Le preguntas qué ha sido de ella. «Has puesto esa mano ahí y he perdido el hilo.» La dejas justo donde está, en su cintura."),
        "valeria": tr("Valeria te suelta la mano, se quita un anillo que se os clavaba y vuelve a buscar tus dedos. «Mucho mejor.» Te sorprende lo pequeña que suena aquí esa voz que llena una tienda entera."),
        "ibai": tr("Ibai roza tu muñeca con las yemas ásperas y se detiene. «¿Raspan?» Le vuelves la mano para besarle la palma. Afuera pasa un motor. Por una vez, ni siquiera intenta adivinar qué barco es."),
        "sole": tr("Sole se aparta el pelo de la nuca para que quepa tu brazo. «Ven, que al taller ya voy yo sola.» Acomoda la cabeza en el hueco y por fin deja descansar los hombros."),
    }.get(pid, "")


def despues(tipo):
    return {
        "romantico": tr("A la luz de la mesilla, {n} te ayuda con el botón que siempre se atasca. Tu camisa resbala al suelo. Mucho después, al ir a apagar la luz, te besa en el hombro desnudo, justo donde la almohada te ha dejado una raya."),
        "apasionado": tr("Cuando recuperáis el aliento, el aire fresco en la espalda te hace buscar la sábana. {n} encuentra primero tu camisa y te la pasa. Está del revés. Os la quedáis mirando un segundo antes de echaros a reír. Fuera, el semáforo sigue cambiando para una calle vacía."),
        "jugueton": tr("Un zapato cae al suelo con tal estruendo que os da la risa en mitad del beso. El otro lo quitáis con más cuidado. Mucho después, {n} encuentra un calcetín bajo la almohada. «Conque ahí estaba.» Compartís un vaso de agua sin salir de la cama."),
        "tranquilo": tr("Al principio la sábana está fría contra tu piel. Cuando volvéis a estirarla, ya tiene el calor de los dos. Afuera alguien baja una persiana a tirones. {n} levanta la cabeza de tu pecho para escuchar. En cuanto vuelve el silencio, se acomoda otra vez."),
    }[tipo]


def acuerdos():
    return [
        (tr("«Me gustaría acostarme contigo», dice {n}. «¿A ti te apetece?»"), False),
        (tr("{n} deja la mano abierta junto a la tuya. «¿Te quedas conmigo esta noche?»"), False),
        (tr("«Me apetece ir a la cama contigo», dice {n}. «Para mí, solo con preservativo. ¿Tienes uno?»"), True),
        (tr("{n} te propone pasar la noche juntos. «Si mañana alguien pregunta, prefiero que esto quede entre nosotros.»"), False),
        (tr("«Quiero despertarme contigo», dice {n}. «Y si solo te apetece volver mañana a desayunar, también pongo café.»"), False),
        (tr("«Mañana madrugo», dice {n}, sin soltarte la mano. «Pero esta noche me gustaría que te quedaras. ¿Quieres?»"), False),
        (tr("{n} pregunta por la protección antes de decidir. «Sin preservativo, otro día.»"), True),
        (tr("«Me gustaría seguir», dice {n}. «Podemos parar cuando quieras. ¿Te apetece?»"), False),
    ]


def ofrecer(p, nombre, tipo, donde, completar, *, participante, pid):
    banco = p.datos.get("escenas_privadas", {}).get(tipo)
    if not banco or not p.modo_adulto() or not p.cfg["escenas_directas"] or p.en_servidor:
        return False
    orden = list(range(len(banco)))
    random.Random(f"{p.j.semilla}-{tipo}").shuffle(orden)
    turno = p.j.turnos_escena.get(tipo, 0)
    entrada, final = banco[orden[turno % len(orden)]]
    p.j.turnos_escena[tipo] = turno + 1
    propuestas = acuerdos()
    random.Random(f"{p.j.semilla}-{tipo}-acuerdos").shuffle(propuestas)
    propuesta, requiere_proteccion = propuestas[(turno % len(orden) + turno // len(orden)) % len(propuestas)]
    pregunta = propuesta.format(n=nombre)
    inicio = f"{donde.capitalize()}. {entrada.format(n=nombre)} {pregunta}"

    def juntos(relato):
        momentos = {
            "romantico": tr("{n} te toma de la mano. «Quiero acordarme de esta noche. ¿Dejamos la luz así?»"),
            "apasionado": tr("Al quedaros a solas, {n} se detiene a escucharte. «Ahora tenemos tiempo. ¿Qué te apetece?»"),
            "jugueton": tr("Os da la risa a la vez. «Me gusta que podamos reírnos de esto», dice {n}."),
            "tranquilo": tr("{n} se acomoda a tu lado. Durante un rato solo se oye vuestra respiración."),
        }
        momento = relato[0] if relato else momentos[tipo]
        titulo = momento.format(n=nombre)

        def elegir(respuesta):
            p.app.cerrar(menu)
            if relato:
                respuesta += " " + relato[1]
            respuesta = respuesta.format(n=nombre)
            despedida = final.format(n=nombre)

            def terminar(reaccion, sintonia=None):
                if requiere_proteccion and not p.j.intimos.get("preservativos", 0):
                    p.app.decir(tr("Lo dejáis para otro día."), True)
                    return
                if relato:
                    if sintonia is not None:
                        reaccion = (reaccion + " " + despedida_personal(pid)).strip()
                    completar((reaccion, despues(tipo).format(n=nombre), despedida), sintonia)
                else:
                    completar((reaccion, despedida), sintonia)

            if p.cfg["noche_por_pasos"]:
                perfil = p.relacion(pid) if pid else participante
                noche = NocheDescriptiva(p, nombre, donde, terminar, perfil=perfil, habitual=participante.get("ritmo"))
                noche.empezar_con(respuesta, bool(relato))
            else:
                terminar(respuesta)

        def pausa():
            p.app.cerrar(menu)
            def reanudar():
                p.app.cerrar(descansar)
                juntos(relato)
            descansar = Menu(p.app, tr("Os apartáis un momento. {n} pregunta si quieres seguir o dejarlo aquí.").format(n=nombre),
                             [Opcion(tr("Volver cuando ambos estéis listos"), reanudar),
                              Opcion(tr("Terminar aquí"), lambda: p.app.cerrar(descansar))])
            descansar.escena_privada = True
            p.app.abrir(descansar)

        menu = Menu(p.app, titulo, [
            Opcion(tr("Quedaros cerca en silencio"), lambda: elegir(tr("Os quedáis abrazados. {n} espera contigo hasta que te apetece hablar.")), ayuda=titulo),
            Opcion(tr("Decir lo que este momento significa para ti"), lambda: elegir(tr("{n} escucha hasta el final. «Me alegra que me lo hayas contado.»")), ayuda=titulo),
            Opcion(tr("Pedir una pausa"), pausa),
            Opcion(tr("Terminar aquí"), lambda: p.app.cerrar(menu))])
        menu.escena_privada = True
        p.app.abrir(menu)

    def mostrar(texto, hablar):
        def conversar():
            p.app.cerrar(menu)
            mostrar(tr("Habláis de vuestros límites y de protección. Podéis cambiar de idea.") + " " + pregunta, False)

        def aceptar():
            p.app.cerrar(menu)
            if p.modo_adulto() and p.cfg["escenas_directas"] and not p.en_servidor:
                if requiere_proteccion and not p.j.intimos.get("preservativos", 0):
                    p.app.decir(tr("Lo dejáis para otro día."), True)
                    return
                relatos = p.datos.get("relatos_privados", {})
                banco_personal = relatos.get(pid)
                if not banco_personal:
                    banco_personal = relatos.get(gente.habla_de(participante.get("caracter", "amable")))
                relato = None
                if banco_personal:
                    clave = f"persona:{pid or nombre}"
                    indice = p.j.turnos_escena.get(clave, 0)
                    orden_personal = list(range(len(banco_personal)))
                    random.Random(f"{p.j.semilla}-{clave}").shuffle(orden_personal)
                    relato = banco_personal[orden_personal[indice % len(orden_personal)]]
                    p.j.turnos_escena[clave] = indice + 1
                juntos(relato)

        opciones = [Opcion(tr("Hablar de lo que quiere cada uno"), conversar, ayuda=texto)] if hablar else []
        opciones.extend([Opcion(tr("Decir que sí"), aceptar, ayuda=texto),
                         Opcion(tr("Decir que no y despedirte"), lambda: p.app.cerrar(menu))])
        menu = Menu(p.app, texto, opciones)
        menu.escena_privada = True
        p.app.abrir(menu)

    mostrar(inicio, p.cfg["noche_por_pasos"])
    return True
