"""Escenas privadas de una noche con alguien (contenido para adultos, opción «Escenas privadas con lenguaje directo»).

Antes de la noche, la otra persona propone y tú dices que sí o que no; después hay un momento a solas, que con cada persona
de la vida social puede ser uno de sus relatos, y la noche, paso a paso si esa opción está activada. Todo el contenido está
en data/datos/escenas_privadas.json (las escenas de cada tipo de noche, las propuestas y los momentos de la noche paso a
paso) y en data/datos/relatos_privados.json (los relatos de cada persona por su id, o de la gente de la calle por su
carácter); la despedida de cada persona va en su ficha de adultos.json. Los mods los suman o los sustituyen por id.

Las escenas no se repiten hasta haber salido todas: cada tipo de noche y cada persona tienen su rueda, barajada con la
semilla de la partida, y por dónde va se guarda en la partida (Jugador.turnos_escena). Todas las personas son adultas,
todo es consentido y cualquiera de los dos puede parar.
"""
import random

from . import gente
from .ajustes import hueco
from .i18n import tr
from .laboratorio import Noche
from .menus import Menu, Opcion


def _por_id(p, seccion):
    return {x["id"]: x for x in p.datos.get(seccion, []) if isinstance(x, dict) and x.get("id")}


def _pares(lista):
    """Las parejas de textos bien formadas de una lista de los datos (escenas o relatos)."""
    return [(str(x[0]), str(x[1])) for x in lista or [] if isinstance(x, (list, tuple)) and len(x) >= 2]


def escena_de(p, tipo):
    """Lo que dicen los datos de un tipo de noche (romantico, apasionado...), o None si no hay escenas para él."""
    e = _por_id(p, "escenas_privadas").get(tipo)
    return e if e and _pares(e.get("escenas")) else None


def acuerdos(p):
    """Las propuestas con las que empieza la noche: (texto, si pide preservativo)."""
    out = [(str(a["texto"]), bool(a.get("proteccion"))) for a in p.datos.get("acuerdos_privados", []) if isinstance(a, dict) and a.get("texto")]
    return out or [(tr("{n} te pregunta si te apetece pasar la noche juntos."), False)]


def momentos(p):
    """Los momentos de la noche paso a paso en una escena privada, con la forma de laboratorio.MOMENTOS."""
    out = []
    for m in p.datos.get("momentos_privados", []):
        if not isinstance(m, dict) or not m.get("texto"):
            continue
        ops = [(str(o["texto"]), o.get("ritmo", "lento"), str(o.get("respuesta", ""))) for o in m.get("opciones", []) if isinstance(o, dict) and o.get("texto")]
        if ops:
            out.append((str(m["texto"]), ops))
    return out


def relatos(p, pid, participante):
    """Los relatos de esa persona: los suyos por su id o, si no tiene, los de su carácter al hablar."""
    banco = _por_id(p, "relatos_privados")
    propios = _pares((banco.get(pid) or {}).get("relatos")) if pid else []
    if propios:
        return pid, propios
    caracter = gente.habla_de((participante or {}).get("caracter", "amable"))
    return caracter, _pares((banco.get(caracter) or {}).get("relatos"))


def _turno(p, clave, n):
    """El siguiente de una rueda de n elementos, barajada con la semilla de la partida: no repite hasta haberlos dado todos."""
    orden = list(range(n))
    random.Random(f"{p.j.semilla}-{clave}").shuffle(orden)
    vuelta = p.j.turnos_escena.get(clave, 0)
    p.j.turnos_escena[clave] = vuelta + 1
    return orden[vuelta % n], vuelta


class NocheDescriptiva(Noche):
    """La noche paso a paso de una escena privada: sus momentos salen de los datos y se puede pedir una pausa."""
    privada = True

    def empezar_con(self, apertura, propios=None):
        if propios:
            self.momentos = propios
        self._mostrar(apertura + " ")

    def _fin(self, antes):
        self.al_acabar(antes.strip(), self.puntos / self.maximo if self.maximo else 0.5)


def ofrecer(p, nombre, tipo, donde, completar, *, participante=None, pid=None):
    """Empieza la escena privada de una noche. completar(lineas, sintonia) la cuenta y aplica sus efectos.

    Devuelve False si no hay escena para ese tipo o la opción no vale ahora (sin contenido para adultos, o en un servidor):
    entonces la noche se cuenta como siempre."""
    escena = escena_de(p, tipo)
    if escena is None or not p.modo_adulto() or not p.cfg["escenas_directas"] or p.en_servidor:
        return False
    banco = _pares(escena["escenas"])
    i, vuelta = _turno(p, tipo, len(banco))
    entrada, final = banco[i]
    propuestas = acuerdos(p)
    orden = list(range(len(propuestas)))
    random.Random(f"{p.j.semilla}-{tipo}-acuerdos").shuffle(orden)
    propuesta, con_preservativo = propuestas[orden[(i + vuelta // len(banco)) % len(propuestas)]]
    pregunta = hueco(propuesta, n=nombre)
    inicio = f"{donde[:1].upper()}{donde[1:]}. {hueco(entrada, n=nombre)} {pregunta}"
    sin_preservativo = tr("Lo dejáis para otro día.")
    participante = participante or {}

    def juntos(relato):
        momento = hueco(relato[0] if relato else escena.get("momento") or tr("{n} se acomoda a tu lado."), n=nombre)

        def elegir(respuesta):
            p.app.cerrar(menu)
            if relato:
                respuesta += " " + relato[1]
            respuesta = hueco(respuesta, n=nombre)

            def terminar(reaccion, sintonia=None):
                lineas = [reaccion]
                if relato:
                    despedida = hueco(participante.get("despedida", ""), n=nombre)
                    if despedida:
                        lineas[0] = reaccion + " " + despedida
                    if escena.get("despues"):
                        lineas.append(hueco(escena["despues"], n=nombre))
                lineas.append(hueco(final, n=nombre))
                completar(tuple(lineas), sintonia)

            if p.cfg["noche_por_pasos"]:
                noche = NocheDescriptiva(p, nombre, donde, terminar, habitual=participante.get("ritmo"))
                noche.empezar_con(respuesta, momentos(p))
            else:
                terminar(respuesta)

        def pausa():
            p.app.cerrar(menu)

            def reanudar():
                p.app.cerrar(descanso)
                juntos(relato)
            descanso = Menu(p.app, tr("Os apartáis un momento. {n} pregunta si quieres seguir o dejarlo aquí.").format(n=nombre),
                            [Opcion(tr("Volver cuando los dos estéis listos"), reanudar, ayuda=tr("Seguís justo donde lo habíais dejado.")),
                             Opcion(tr("Terminar aquí"), lambda: p.app.cerrar(descanso), ayuda=tr("Lo dejáis aquí. Esta noche no cuenta."))],
                            escapable=False)
            p.app.abrir(descanso)

        menu = Menu(p.app, momento, [
            Opcion(tr("Quedaros cerca en silencio"), lambda: elegir(tr("Os quedáis abrazados. {n} espera contigo hasta que te apetece hablar.")), ayuda=momento),
            Opcion(tr("Decir lo que este momento significa para ti"), lambda: elegir(tr("{n} escucha hasta el final. «Me alegra que me lo hayas contado.»")), ayuda=momento),
            Opcion(tr("Pedir una pausa"), pausa, ayuda=tr("Os apartáis un momento. Podéis volver cuando estéis listos o dejarlo aquí, sin que pase nada.")),
            Opcion(tr("Terminar aquí"), lambda: p.app.cerrar(menu), ayuda=tr("Lo dejáis aquí. Esta noche no cuenta."))])
        p.app.abrir(menu)

    def mostrar(texto, hablar):
        def conversar():
            p.app.cerrar(menu)
            mostrar(tr("Habláis de vuestros límites y de protección. Podéis cambiar de idea.") + " " + pregunta, False)

        def aceptar():
            p.app.cerrar(menu)
            if con_preservativo and not p.j.intimos.get("preservativos", 0):
                p.app.decir(sin_preservativo, True)
                return
            clave, banco_propio = relatos(p, pid, participante)
            relato = None
            if banco_propio:
                k, _ = _turno(p, "persona:" + (pid or clave), len(banco_propio))
                relato = banco_propio[k]
            juntos(relato)

        opciones = [Opcion(tr("Hablar de lo que quiere cada uno"), conversar, ayuda=tr("Antes de decidir, habláis de lo que os apetece, de vuestros límites y de protección."))] if hablar else []
        opciones += [Opcion(tr("Decir que sí"), aceptar, ayuda=texto),
                     Opcion(tr("No, despedirte por hoy"), lambda: p.app.cerrar(menu), ayuda=tr("Un no se respeta. Os despedís y esta noche no pasa nada."))]
        menu = Menu(p.app, texto, opciones)
        p.app.abrir(menu)

    mostrar(inicio, p.cfg["noche_por_pasos"])
    return True
