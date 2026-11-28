"""Dos cosas del contenido para adultos que se juegan, en lugar de leerse: la noche con alguien, paso a paso,
y el laboratorio clandestino.

La noche: el jugador decide qué hace en cada momento y la otra persona responde. Sigue contándose de forma
sensual y sin escenas explícitas; lo que cambia es que ahora actúas tú, y que escuchar lo que la otra persona
quiere, y respetar un «espera», es lo que hace que la noche salga bien. Todas las personas son adultas.

El laboratorio: un oficio ilegal dentro del juego. Es un minijuego de oído, de mantener un tono en su sitio.
No describe ni se parece a ningún proceso real: las sustancias del juego son inventadas, como sus efectos.
"""
from .i18n import tr
import random

import pygame

# ============================================================================ la noche, paso a paso
# Cada persona tiene un ritmo que le gusta. No se dice: se nota en cómo responde.
RITMOS = ("lento", "intenso", "jugando")
MOMENTOS = [
    (tr("Acabáis de entrar. {n} deja las llaves y te mira."), [
        (tr("Poner música bajita y servir dos copas"), "lento", tr("{n} se quita los zapatos y se sienta muy cerca de ti.")),
        (tr("Besarle antes de que diga nada"), "intenso", tr("{n} te agarra de la camisa y no te suelta.")),
        (tr("Hacerle una broma y perseguirle por el pasillo"), "jugando", tr("{n} se escapa riéndose y se deja alcanzar."))]),
    (tr("Estáis muy cerca. Notas su respiración."), [
        (tr("Acariciarle despacio, sin prisa ninguna"), "lento", tr("{n} cierra los ojos y apoya la frente en la tuya.")),
        (tr("Abrazarle fuerte y dejar que hablen las manos"), "intenso", tr("{n} te busca la boca con hambre.")),
        (tr("Susurrarle una tontería al oído"), "jugando", tr("{n} se ríe contra tu cuello."))]),
    (tr("{n} te mira a los ojos, esperando."), [
        (tr("Preguntarle qué le apetece"), "pregunta", ""),
        (tr("Llevarle de la mano al dormitorio"), "lento", tr("{n} te sigue sin soltarte.")),
        (tr("Dejar que sea quien decida"), "cede", tr("{n} sonríe y toma la iniciativa."))]),
    (tr("La ropa empieza a sobrar."), [
        (tr("Ir despacio, mirándole"), "lento", tr("{n} te deja hacer y suspira.")),
        (tr("Con prisa, sin pensar"), "intenso", tr("{n} te ayuda, con las manos torpes de ganas.")),
        (tr("Entre risas, enredándoos"), "jugando", tr("Acabáis los dos riéndoos, hechos un lío."))]),
]
ESPERA = ["{n} te pone una mano en el pecho. «Espera. Más despacio.»", "{n} se aparta un poco. «Un momento. Así no.»"]
QUIERE = {"lento": "«Despacio. Hoy quiero que dure.»", "intenso": "«No pienses tanto. Ven aquí.»", "jugando": "«Sorpréndeme. Hazme reír.»"}


def ritmo_preferido(perfil, habitual, azar):
    """Migra el perfil la primera vez que se usa, sin tocar la afinidad ni el historial."""
    if perfil.get("ritmo") not in RITMOS:
        perfil["ritmo"] = habitual if habitual in RITMOS else azar.choice(RITMOS)
    return perfil["ritmo"]


class Noche:
    """Una noche con alguien, decidida paso a paso. Al terminar llama a al_acabar(sintonia), de 0 a 1."""

    momentos = MOMENTOS
    privada = False

    def __init__(self, p, nombre, donde, al_acabar, azar=None, perfil=None, habitual=None):
        self.p, self.app, self.nombre, self.donde, self.al_acabar = p, p.app, nombre, donde, al_acabar
        self.azar = azar or random
        self.ritmo = ritmo_preferido(perfil if perfil is not None else {}, habitual, self.azar)
        if p.reloj < 5 * 60:
            self.ritmo = "lento"
        self.paso = 0
        self.puntos = 0.0
        self.maximo = 0.0
        self.espera = False            # te ha pedido que pares: lo siguiente decide mucho
        self.menu = None

    def empezar(self):
        saludo = {"lento": tr("Hoy me apetece estar contigo sin prisas."),
                  "intenso": tr("Tenía ganas de verte. ¿Qué te apetece hacer?"),
                  "jugando": tr("He tenido un día largo. ¿Me cuentas algo que me haga reír?")}
        self._mostrar(f"{self.donde.capitalize()}. {self.nombre}: {saludo[self.ritmo]} ")

    def _mostrar(self, antes=""):
        from .menus import Menu, Opcion
        n = self.nombre
        if self.menu is not None:
            self.app.cerrar(self.menu)
            self.menu = None
        if self.espera:
            titulo = antes + tr(self.azar.choice(ESPERA)).format(n=n)
            ops = [Opcion(tr("Parar, y preguntarle si está bien"), self._responde_espera, ayuda=tr("Un espera se respeta. Parar y escuchar es lo que más os acerca.")),
                   Opcion(tr("Mejor otro día"), lambda: self.app.cerrar(self.menu))]
        elif self.paso >= len(self.momentos):
            self._fin(antes)
            return
        else:
            texto, opciones = self.momentos[self.paso]
            titulo = antes + texto.format(n=n)
            ayuda = titulo if self.privada else tr("No hay una respuesta correcta para todo el mundo: fíjate en cómo responde.")
            ops = [Opcion(t, (lambda r=r, d=d: self._elegir(r, d)), ayuda=ayuda) for t, r, d in opciones]
        if self.privada and not self.espera:
            ops.append(Opcion(tr("Pedir una pausa"), self._pausa, ayuda=titulo))
        self.menu = Menu(self.app, titulo, ops)
        self.menu.escena_privada = self.privada
        self.app.abrir(self.menu)

    def _elegir(self, ritmo, dice):
        n = self.nombre
        self.paso += 1
        self.maximo += 1.0
        if ritmo == "pregunta":                              # preguntar siempre acierta, y además te dice lo que quiere
            self.puntos += 1.0
            self._mostrar(tr('{n} te lo dice al oído: {v} ').format(n=n, v=tr(QUIERE[self.ritmo])))
            return
        if ritmo == "cede":
            self.puntos += 0.7
            self._mostrar(dice.format(n=n) + " ")
            return
        if ritmo == self.ritmo:
            self.puntos += 1.0
            self.app.son("afinidad_sube", vol=0.5)
            self._mostrar(dice.format(n=n) + tr(" Es justo lo que quería. "))
        elif ritmo == "intenso" and self.ritmo == "lento":   # ir más deprisa de lo que quiere: te frena
            self.espera = True
            self._mostrar()
        else:
            self.puntos += 0.4
            self._mostrar(dice.format(n=n) + tr(" Aunque notas que hoy le apetecía otra cosa. "))

    def _responde_espera(self):
        self.espera = False
        self._mostrar(tr('Paras. {n} respira, te sonríe y te lo dice: {v} ').format(n=self.nombre, v=tr(QUIERE[self.ritmo])))

    def _fin(self, antes):
        from .menus import Dialogo
        s = self.puntos / self.maximo if self.maximo else 0.5
        como = (tr("Ha sido una de esas noches que se recuerdan: os habéis entendido sin palabras.") if s >= 0.8 else
                tr("Ha estado bien. Os vais conociendo.") if s >= 0.5 else tr("No habéis acabado de encontraros. Otra vez será mejor si le escuchas."))
        self.menu = None
        self.app.abrir(Dialogo(self.app, [(tr("Narrador"), antes + tr("Se apaga la luz. Lo que pasa después es solo vuestro.")), (tr("Narrador"), como)],
                               lambda: self.al_acabar(s), cancelar_con_escape=True))


# ============================================================================ el laboratorio
PRECIO_LAB = 9000
PRECIO_MATERIAL = 180
PRODUCTOS = ("pastillas", "polvo", "cristal")
DURA = 24.0
CALIDAD_SIN_MINIJUEGO = 0.5       # sin el minijuego (opción minijuego_laboratorio), cada tanda sale normal: ni limpia ni floja, y no arde


def puede_montar(p, lugar):
    return p.modo_adulto() and lugar.tipo == "casa" and lugar.id in p.j.propiedades


def opciones_casa(p, lugar, Menu, Opcion):
    """Lo que añade el laboratorio al menú de una casa tuya."""
    if not puede_montar(p, lugar):
        return []
    j = p.j
    app = p.app
    if lugar.id not in j.laboratorios:
        def montar():
            if p.pagar(p.precio("laboratorio", PRECIO_LAB)):
                j.laboratorios.append(lugar.id)
                p.son("reparar", cat="interfaz")
                app.decir(tr("Montas un laboratorio en el cuarto del fondo. Para trabajar en él hace falta material: lo vende cualquier proveedor."), True)
        return [Opcion(tr('Montar un laboratorio clandestino aquí: {precio} euros').format(precio=(p.precio('laboratorio', PRECIO_LAB))), montar,
                       ayuda=tr("Un cuarto preparado para fabricar mercancía. Da mucho dinero y muchos problemas: los vecinos huelen cosas, la policía pregunta, y si te equivocas puede arder."))]

    def trabajar(s):
        def f():
            if j.material <= 0:
                app.son("error")
                app.decir(tr("No te queda material. Lo vende cualquier proveedor."), True)
                return
            if p.carga() >= 100:
                app.son("error")
                app.decir(tr("No te cabe más mercancía encima. Vende antes."), True)
                return
            j.material -= 1
            if p.cfg["minijuego_laboratorio"]:
                app.abrir(Coccion(p, lugar, s))
            else:
                Coccion(p, lugar, s).sin_minijuego()
        return f
    if p.cfg["minijuego_laboratorio"]:
        ayuda_fabricar = tr("Un minijuego de oído. Suenan dos tonos: uno fijo, que es el punto bueno, y otro que se te va. Con flecha arriba y flecha abajo llevas el tuyo "
                            "hasta igualarlo al fijo, y lo mantienes ahí. Cuanto más tiempo estén iguales, mejor sale la tanda y más unidades sacas. "
                            "Si lo dejas irse muy arriba mucho rato, puede arder.")
    else:
        ayuda_fabricar = tr("La tanda sale al momento, normal: ni limpia ni floja, y sin peligro de que arda. El minijuego se vuelve a poner en Opciones, Contenido para adultos.")
    ops = [Opcion(lambda: tr('Laboratorio. Tienes material para {material} {v}').format(material=(j.material), v=(tr('tanda') if j.material == 1 else tr('tandas'))),
                  ayuda=tr("Cada tanda que fabricas gasta una de material. El material lo vende cualquier proveedor."))]
    for s in p.dato_adulto("sustancias"):
        if s["id"] in PRODUCTOS:
            ops.append(Opcion(tr('Fabricar {lower}').format(lower=(s['nombre'].lower())), trabajar(s), ayuda=ayuda_fabricar))
    return [Opcion(tr("Entrar en el laboratorio"), lambda: app.abrir(Menu(app, tr("Laboratorio"), ops)),
                   ayuda=tr("Fabricar mercancía para venderla después a los proveedores o por la calle."))]


def opcion_proveedor(p, Opcion):
    """En los proveedores se compra el material."""
    j = p.j

    def comprar():
        if p.pagar(p.precio("material_laboratorio", PRECIO_MATERIAL)):
            j.material += 1
            p.son("trato", cat="interfaz")
            p.app.decir(tr('Material para una tanda. Tienes para {material}.').format(material=(j.material)), True)
    return Opcion(lambda: tr('Material de laboratorio, una tanda: {precio} euros. Tienes {material}').format(precio=(p.precio('material_laboratorio', PRECIO_MATERIAL)), material=(j.material)), comprar,
                  ayuda=tr("Hace falta para trabajar en un laboratorio. El laboratorio se monta en una casa tuya, desde su menú."))


class Coccion:
    """El minijuego: mantener tu tono igual al tono fijo durante unos segundos."""
    pausa_mundo = True

    def __init__(self, p, lugar, sustancia, azar=None):
        self.p, self.app, self.l, self.s = p, p.app, lugar, sustancia
        self.azar = azar or random
        self.t = 0.0
        self.valor = 0.0               # dónde está tu tono: 0 es el punto bueno
        self.deriva = self.azar.choice((-1, 1)) * 0.25
        self.bien = 0.0                # segundos con el tono en su sitio
        self.alto = 0.0                # segundos muy por encima: peligro
        self.t_tono = 0.0
        self.hecho = False

    def sin_minijuego(self):
        """La tanda sin jugar: sale con CALIDAD_SIN_MINIJUEGO y sin estar nunca muy arriba, así que no arde. Lo demás
        (lo que cabe en la mochila, el armario, el vecino que nota el olor) es igual que al jugarla."""
        self.bien = DURA * CALIDAD_SIN_MINIJUEGO
        self.alto = 0.0
        self._fin()

    def al_entrar(self):
        self.app.decir(tr('Empiezas una tanda de {lower}. Oirás un tono fijo y otro que se mueve. Con flecha arriba y flecha abajo, iguala el tuyo al fijo y mantenlo. Dura {int} segundos. Escape lo deja a medias.').format(lower=(self.s['nombre'].lower()), int=(int(DURA))), True)

    def tecla(self, ev):
        if ev.key == pygame.K_ESCAPE:
            self._fin(abandonada=True)

    def actualizar(self, dt):
        if self.hecho:
            return
        self.t += dt
        t = self.app.teclas
        if pygame.K_UP in t:
            self.valor += 0.9 * dt
        if pygame.K_DOWN in t:
            self.valor -= 0.9 * dt
        if self.azar.random() < dt * 0.5:                    # de vez en cuando cambia hacia dónde se te va
            self.deriva = self.azar.choice((-1, 1)) * self.azar.uniform(0.15, 0.4)
        self.valor = max(-1.5, min(1.5, self.valor + self.deriva * dt))
        if abs(self.valor) < 0.18:
            self.bien += dt
        if self.valor > 0.9:
            self.alto += dt
        self.t_tono -= dt
        if self.t_tono <= 0:
            self.t_tono = 0.45
            self.app.son("tono_libre", vol=0.45, pan=-0.6)                                   # el fijo, a la izquierda
            self.app.son("tono_libre", vol=0.6, pan=0.6, tono=2.0 ** (self.valor * 0.6))     # el tuyo, a la derecha
        if self.t >= DURA:
            self._fin()

    def _fin(self, abandonada=False):
        if self.hecho:
            return
        self.hecho = True
        p, j, app = self.p, self.p.j, self.app
        app.cerrar(self)
        calidad = 0.0 if abandonada else self.bien / DURA
        if not abandonada and self.alto > 6.0 and self.azar.random() < 0.6:
            j.laboratorios.remove(self.l.id) if self.l.id in j.laboratorios else None
            p.son("explosion", cat="interfaz", vol=0.8)
            p.danar_jugador(45, None)
            p.delito(6, tr("incendio en un laboratorio"), siempre=True)
            app.decir(tr("Se te va de las manos y arde. Sales tosiendo, con quemaduras. El laboratorio se ha perdido, y medio barrio ha llamado a la policía."), True)
            return
        if abandonada:
            app.decir(tr("Lo dejas a medias. La tanda se ha echado a perder."), True)
            return
        unidades = max(1, int(round(4 + 12 * calidad)))
        encima = min(unidades, p.hueco_mercancia())             # lo que cabe en la mochila; el resto, al armario de esta casa (mochila.py)
        j.sustancias[self.s["id"]] = j.sustancias.get(self.s["id"], 0) + encima
        resto = unidades - encima
        if resto:
            a = p.almacen(self.l.id)["sust"]
            a[self.s["id"]] = a.get(self.s["id"], 0) + resto
        j.stats["fabricado"] = j.stats.get("fabricado", 0) + unidades
        p.son("trato", cat="interfaz")
        nota = tr("Una tanda limpia") if calidad >= 0.6 else tr("Una tanda normal") if calidad >= 0.3 else tr("Una tanda floja")
        app.decir(tr('{nota}: {unidades} de {lower}. Llevas {v}.').format(nota=(nota), unidades=(unidades), lower=(self.s['nombre'].lower()), v=(j.sustancias[self.s['id']]))
                  + (tr(' No te cabe todo en la mochila: {resto} se quedan en el armario de la casa.').format(resto=(resto)) if resto else "") + tr(" Véndelo a un proveedor o por la calle."), True)
        if self.azar.random() < 0.15:
            p.delito(3, tr("olores sospechosos"), siempre=True)
            p.decir(tr("Un vecino ha notado el olor y ha llamado a la policía."))

    def cerrado(self):
        pass

