"""Motor de misiones. Las misiones se definen en datos/misiones.json (y en mods)."""
from .i18n import tr
import copy
import math
import random

import pygame

from . import gente as G
from . import mundo as M
from . import destinos as D
from .entidades import Objeto, Persona
from .menus import Dialogo, Menu, Opcion


def paso_seguro(pasos, k):
    """¿Se puede poner un punto de control al empezar el paso k? No, si a esas alturas llevas un vehículo de la misión
    que todavía hay que entregar: al volver, ese vehículo ya no existiría."""
    pendiente = False
    for p in pasos[:k]:
        if p["tipo"] == "robar":
            pendiente = True
        elif p["tipo"] == "entregar":
            pendiente = False
    return not pendiente


def pares_cruce(valor):
    """«concejal:1, trono:3», o una lista de eso, como pares (decisión, opción). Lo que no se entienda, se salta."""
    if not valor:
        return []
    trozos = valor.replace(";", ",").split(",") if isinstance(valor, str) else list(valor)
    pares = []
    for t in trozos:
        try:
            c, o = str(t).split(":")
            if c.strip():
                pares.append((c.strip(), int(o)))
        except ValueError:
            continue
    return pares


def grupos_alguna(valor):
    """«fd2 fd3 fd4; vd2 vd3», o una lista de listas: de cada grupo hay que haber completado al menos una misión."""
    if not valor:
        return []
    if isinstance(valor, str):
        return [g.split() for g in valor.split(";") if g.split()]
    return [g.split() if isinstance(g, str) else list(g) for g in valor if g]


class Misiones:
    def misiones_disponibles(self):
        hechas = set(self.completadas)
        return [m for m in self.datos["misiones"]
                if m["id"] not in hechas and (self.cfg["adultos"] or not m.get("adultos")) and all(r in hechas for r in m.get("requiere", []))
                and all(any(r in hechas for r in grupo) for grupo in grupos_alguna(m.get("requiere_alguna")))
                and m.get("lugar") in self.lugares and self.cumple_decision(m) and self.cumple_vida(m)]

    def cumple_decision(self, cosa):
        """¿Vale esta misión o este paso con lo que has decidido? Sin condición, siempre.

        `si_clave` y `si_opcion` miran una decisión. `si_cruce` mira varias a la vez, de ramas distintas: es una lista de
        «decisión:opción», y vale cuando se cumplen todas, o entre `si_cruce_min` y `si_cruce_max` de ellas."""
        clave = cosa.get("si_clave")
        if clave:
            hecho = self.decisiones.get(clave)
            if not (isinstance(hecho, dict) and hecho.get("opcion") == int(cosa.get("si_opcion", 1))):
                return False
        pares = pares_cruce(cosa.get("si_cruce"))
        if pares:
            n = sum(1 for c, o in pares if isinstance(self.decisiones.get(c), dict) and self.decisiones[c].get("opcion") == o)
            minimo = cosa.get("si_cruce_min")
            maximo = cosa.get("si_cruce_max")
            if minimo is None and maximo is None:
                minimo = len(pares)                              # sin más, hacen falta todas
            if minimo is not None and n < int(minimo):
                return False
            if maximo is not None and n > int(maximo):
                return False
        return True

    def rentas_decisiones(self):
        """Cada medianoche: lo que te dejan, o te cuestan, las decisiones que tomaste en la historia."""
        total = sum(int(d.get("renta", 0)) for d in self.decisiones.values() if isinstance(d, dict))
        if total > 0:
            self.dar_dinero(total, tr("Lo que decidiste en su día te deja"))
        elif total < 0:
            pago = min(self.j.dinero, -total)
            self.j.dinero -= pago
            self.decir(tr('Lo que decidiste en su día te cuesta {pago} euros.').format(pago=(pago)))
        return total

    def rep_banda(self, banda):
        return float(self.j.rep_bandas.get(banda, 0))

    def cambiar_rep_banda(self, banda, n, hablar=True):
        """Cómo te llevas con una banda, de -100 a 100. Con 30 o más te dejan en paz; con -30 o menos van a por ti."""
        if not banda or not n:
            return
        antes = self.rep_banda(banda)
        ahora = max(-100.0, min(100.0, antes + n))
        self.j.rep_bandas[banda] = ahora
        if hablar and self.rep_banda_txt(antes) != self.rep_banda_txt(ahora):
            self.son("fama", cat="interfaz")
            self.decir(f"{banda}: {self.rep_banda_txt(ahora)}.")

    @staticmethod
    def rep_banda_txt(x):
        return tr("sois aliados") if x >= 60 else tr("te respetan y te dejan en paz") if x >= 30 else tr("te la tienen jurada") if x <= -60 else tr("van a por ti") if x <= -30 else tr("ni amigos ni enemigos")

    def misiones_en_lugar(self, lugar_id):
        """Las misiones que se pueden empezar en ese lugar. Los tutoriales, salvo el primero, se empiezan desde el móvil:
        no deben estorbar en la oficina de empleo o en el embarcadero."""
        return [m for m in self.misiones_disponibles()
                if m["lugar"] == lugar_id and (not m.get("tutorial") or m["id"] == "tut01") and not m.get("explicacion")]

    def mision_en_lugar(self, lugar_id):
        ms = self.misiones_en_lugar(lugar_id)
        marcada = next((m for m in ms if m["id"] == getattr(self, "mision_marcada", None)), None)
        return marcada or (ms[0] if ms else None)

    def objetivo_txt(self, sugerir=False):
        """Lo que toca hacer ahora. Con ``sugerir``, sin misión en curso, la siguiente se dice como consejo («Deberías
        pasarte por...»), que es como lo dice la gente del juego."""
        if self.guerra:
            return self.guerra_txt()
        if not self.mision and self.rec_asalto_txt():            # te están asaltando un barrio: es lo urgente
            return self.rec_asalto_txt()
        if self.mision:
            p = self.mision["def"]["pasos"][self.mision["paso"]]
            donde = self.objetivo_posicion_txt()                 # lo primero, dónde está: con prisa no hay tiempo para oír lo demás
            t = (donde + " " if donde else "") + tr('Misión {titulo}. {get}').format(titulo=(self.mision['def']['titulo']), get=(p.get('texto', '')))
            if self.mision.get("limite") is not None:
                t += tr(' Te quedan {int} segundos.').format(int=(int(self.mision['limite'])))
            x, y = self.pos()
            o = self.mision.get("movil")
            if p["tipo"] == "seguir" and o:
                t += tr(" Síguele por el sonido de sus pasos, sin acercarte a menos de seis metros.")
            if p["tipo"] == "sigilo" and self.mision.get("guardias"):
                t += tr(" Si te agachas con la X, te oyen mucho menos. No corras.")
            vg = self.mision.get("vigia")
            if p["tipo"] == "vigilar" and vg:
                t += (tr(' Estás en tu puesto. Te quedan {max} segundos. Si oyes pasos que se acercan, quédate quiet[o|a] o agáchate con la X.').format(max=(max(0, int(float(p.get('segundos', 45)) - vg['t']))))
                      if vg["dentro"] else tr(" Todavía no has llegado al puesto."))
            ca = self.mision.get("carrera")
            if p["tipo"] == "carrera" and ca:
                if ca["fase"] == "corre":
                    t += tr(' Vas por el punto {v} de {len}. {_carrera_puesto_txt}').format(v=(self.mision.get('ruta_i', 0) + 1), len=(len(p.get('puntos', []))), _carrera_puesto_txt=(self._carrera_puesto_txt(ca)))
                else:
                    t += tr(" Ve a la salida con un vehículo y detente allí.")
            if p["tipo"] == "ruta":
                t += tr(' Vas por el punto {v} de {len}.').format(v=(self.mision.get('ruta_i', 0) + 1), len=(len(p.get('puntos', []))))
            if p["tipo"] == "eliminar" and self.mision.get("generado"):
                t += tr(' Quedan {sum} enemigos.').format(sum=(sum(1 for e in self.mision['enemigos'] if not e.muerto and not getattr(e, 'rendido', False))))
            ab = self.mision.get("abriendo")
            if p["tipo"] == "recoger" and ab:
                t += tr(' Se está abriendo: faltan unos {max} segundos. No te apartes.').format(max=(max(1, int(ab['total'] - ab['t']))))
            elif p["tipo"] == "recoger" and self._segundos_recoger(p) > 0 and not self.mision.get("recogido"):
                t += tr(" Tarda en abrirse: quédate al lado hasta que ceda.")
            if p["tipo"] == "policia" and self.mision.get("policia_en") is not None:
                t += tr(' La policía tarda aún unos {max} segundos en llegar: aprovecha para alejarte.').format(max=(max(1, int(self.mision['policia_en'] - self.t))))
            if getattr(self, "golpe", None):
                t += " " + self.golpe_estado_txt()
            return t
        if self.vuelo_objetivo_txt():                            # un vuelo comercial o un aparato secuestrado
            return self.vuelo_objetivo_txt()
        if self.trabajo:
            g = self.gps if self.gps is None or self.gps["auto"] else self.gps.get("anterior")
            donde = tr(' Destino: {situar}.').format(situar=(self.situar(g['dest'][0], g['dest'][1], g['nombre']))) if g is not None and g["auto"] else ""
            return self.trabajo.get("texto", tr("Estás trabajando.")) + donde
        disp = [m for m in self.misiones_disponibles() if not m.get("explicacion")]
        if disp:
            m = disp[0]
            l = self.lugares[m["lugar"]]
            if sugerir:
                return tr('Deberías pasarte por: {titulo}, en {nombre_lugar}. Abre el móvil con M para marcarla en el GPS.').format(titulo=(m['titulo']), nombre_lugar=(self.nombre_lugar(l)))
            return tr('No tienes ninguna misión en curso. Disponible: {titulo}, en {nombre_lugar}. Abre el móvil con M para marcarla en el GPS.').format(titulo=(m['titulo']), nombre_lugar=(self.nombre_lugar(l)))
        return tr("Has completado todas las misiones de la historia. La ciudad es tuya.")

    # ----------------------------------------------------------------- inicio
    def iniciar_mision(self, m, reintento=False, repeticion=False):
        if self.trabajo:
            self.terminar_trabajo(tr("Dejas el trabajo para empezar la misión."))
        self.guerra_retirada(tr("Dejas la pelea para empezar la misión."))
        self.cancelar_gps()
        from . import vozgen
        vozgen.al_jugar(self, m.get("id"))                       # con un personaje propio: las voces de esta misión, lo primero
        self.mision = {"def": m, "paso": -1, "veh": None, "enemigos": [], "objeto": None, "limite": None,
                       "copia": copy.deepcopy(self.j.a_dict()), "reloj": self.reloj, "dia": self.dia,
                       "generado": False, "recogido": False, "restos": None, "avisos": set(), "quedan": None, "repeticion": bool(repeticion)}
        self.app.son("notificacion")
        self.decir(tr('Misión: {titulo}.').format(titulo=(m['titulo'])) + (tr(" La repites: no cuenta ni da recompensa.") if repeticion else ""), True)
        self._llevar_al_tutorial(m)
        if m.get("golpe"):                                       # un golpe preparado con la banda: cada uno a su puesto (golpes.py)
            self.golpe_al_iniciar(m)
        self._siguiente_paso()

    def _llevar_al_tutorial(self, m):
        """Los tutoriales se empiezan desde el móvil, estés donde estés, pero sus frases dan por hecho que estás en su
        punto de partida («estás en el club de tiro», «estás en un embarcadero», «junto a la oficina hay un taxi»).
        Si estás lejos o en otra localidad, te lleva. El de combate, además, pone los muñecos nada más empezar: sin esto,
        la Q decía que no había enemigos cerca, porque estaban a cientos de metros."""
        if not m.get("tutorial"):
            return
        l = self.lugares.get(m.get("lugar", ""))
        paso = next((q for q in m["pasos"] if q["tipo"] not in ("dialogo", "dar", "decision")), None)
        justo = bool(paso and paso["tipo"] == "eliminar" and paso.get("ya"))          # hay que estar en la misma puerta
        if justo:
            l = self._lugar_paso(paso) or l
        if l is None:
            return
        x, y = self.pos()
        cerca = 20 if justo else 150
        if l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) < cerca and (not justo or (not self.j.veh and getattr(self, "interior", None) is None)):
            return
        if self.j.veh:
            self.salir_vehiculo(forzado=True)
        self.salir_interior(silencio=True)
        if l.mapa != self.mundo.id:
            self.cambiar_mapa(l.mapa, l.x, l.y)
        self.teletransportar(l.x, l.y)
        self.decir(tr('Para este tutorial te llevo a {nombre}, en {describir}.').format(nombre=(l.nombre), describir=(self.mundo.describir(self.j.x, self.j.y))))

    def _lugar_paso(self, p):
        return self.lugares.get(p.get("lugar", ""))

    # ------------------------------------------------- explicaciones y prácticas de los tutoriales
    def explicacion(self, m):
        """Una explicación: una misión de los datos marcada como tal, que no se juega; se lee entera, con sus voces si las
        tiene. La primera vez que se llega al final cuenta como hecha y da su recompensa."""
        from . import voces
        if isinstance(m, str):
            m = next((x for x in self.datos["misiones"] if x["id"] == m), None)
        if m is None:
            return False
        lineas, grabadas = [], []
        for k, paso in enumerate(m.get("pasos", [])):
            if paso.get("tipo") != "dialogo":
                continue
            lineas += [(self.txt(q), self.txt(tx)) for q, tx in paso["lineas"]]
            grabadas += (voces.de_dialogo(m["id"], k, paso["lineas"], self.j) if self.voces_activas() else None) or [None] * len(paso["lineas"])

        def fin():
            if m["id"] in self.completadas:
                return
            self.completadas.append(m["id"])
            paga = int((m.get("recompensa") or {}).get("dinero", 0))
            if paga:
                self.dar_dinero(paga, tr("Por leerla entera"))
        if not lineas:
            return False
        self.app.abrir(Dialogo(self.app, lineas, fin, voces=grabadas if any(grabadas) else None))
        return True

    def practica_de(self, *cuales):
        """¿El paso actual de la misión es una práctica de un tutorial de esas? (zarpar, timon, atracar, trabajar, servicio)"""
        ms = self.mision
        if not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return False
        p = ms["def"]["pasos"][ms["paso"]]
        return p["tipo"] == "practica" and p.get("que") in cuales

    def practica_evento(self, que):
        """El jugador acaba de hacer algo que una práctica comprueba (atracar en un muelle, por ejemplo)."""
        if self.practica_de(que) and self.mision.get("practica") is not None:
            self.mision["practica"]["evento"] = que

    def _practica_hecha(self):
        """Como _paso_hecho, pero sin tocar el GPS: en una práctica, el destino lo ha puesto el jugador o su trabajo."""
        self.app.son("llegada")
        self._siguiente_paso()

    def _paso_practica(self, ms, p, x, y, dt):
        """Un tutorial que comprueba lo que haces: no vale llegar a un sitio, hay que hacer lo que se enseña."""
        pr = ms.get("practica")
        if pr is None:
            return
        j, v, que = self.j, self.j.veh, p.get("que")
        en_mar = self.mundo.tipo == "mar"
        pr["t"] += dt
        if que == "zarpar":
            if en_mar and v is not None:
                self._practica_hecha()
        elif que == "timon":
            if not en_mar or v is None:
                if pr["t"] > pr["t_aviso"]:
                    pr["t_aviso"] = pr["t"] + 25.0
                    self.decir(tr("Para este ejercicio tienes que estar en el mar, al timón de un barco. Vuelve al embarcadero y zarpa."))
                pr["x"] = None
                return
            if pr["x"] is not None:
                paso = math.hypot(x - pr["x"], y - pr["y"])
                if paso < 30:
                    pr["metros"] += paso
                pr["giro"] += abs(M.norm180(v.rumbo - pr["rumbo"]))
            pr["x"], pr["y"], pr["rumbo"] = x, y, v.rumbo
            metros, giro = float(p.get("metros", 200)), float(p.get("giro", 90))
            if pr["giro"] >= giro and "giro" not in pr["dicho"]:
                pr["dicho"].add("giro")
                if pr["metros"] < metros:
                    self.decir(tr('Bien: el barco gira como tú quieres. Sigue navegando, te faltan unos {int} metros.').format(int=(int(metros - pr['metros']))))
            if pr["metros"] >= metros and "metros" not in pr["dicho"]:
                pr["dicho"].add("metros")
                if pr["giro"] < giro:
                    self.decir(tr("Ya has navegado bastante en línea recta. Ahora lleva el timón: gira con las flechas izquierda y derecha hasta cambiar de rumbo."))
            if pr["metros"] >= metros and pr["giro"] >= giro:
                self._practica_hecha()
        elif que == "atracar":
            if pr.get("evento") == "atracar" and not en_mar:
                self._practica_hecha()
            elif not en_mar and pr["t"] > pr["t_aviso"]:           # ha llegado a tierra de otra manera: nadando, o porque se ha hundido
                pr["t_aviso"] = pr["t"] + 30.0
                self.decir(tr("Para terminar este ejercicio hay que atracar: zarpa de un embarcadero, llega con el barco hasta un muelle, frena y pulsa Intro."))
        elif que == "trabajar":
            if self.trabajo and "veh" in self.trabajo:
                self._practica_hecha()
        elif que == "servicio":
            if j.stats.get("servicios", 0) > pr["servicios"]:
                veh = ms.get("veh")
                if veh is not None:                              # el vehículo de prácticas deja de ser de la misión: puedes seguir trabajando con él
                    veh.tag = None
                    ms["veh"] = None
                self._practica_hecha()
            elif not self.trabajo and pr["t"] > pr["t_aviso"]:
                pr["t_aviso"] = pr["t"] + 25.0
                self.decir(tr("Has dejado de trabajar. Sube al vehículo de prácticas y pulsa la J para empezar otra vez: hay que completar un servicio."))

    def nombre_lugar(self, l):
        """Nombre del lugar, añadiendo la localidad si está en otro mapa."""
        if l.mapa != self.mundo.id:
            return tr('{nombre}, en {nombre2}').format(nombre=(l.nombre), nombre2=(self.mapas[l.mapa].nombre))
        return l.nombre

    def mision_cambio_mapa(self):
        ms = self.mision
        if not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        if tipo == "perseguir" and ms.get("veh_objetivo") is not None:
            self.fallar_mision(tr("Has dejado escapar al objetivo."))
            return
        if tipo == "carrera" and (ms.get("carrera") or {}).get("fase") in ("cuenta", "corre"):
            self.fallar_mision(tr("Has abandonado la carrera."))
            return
        v = ms.get("veh")
        if v is not None and v is not self.j.veh:
            if tipo != "robar" and not paso_seguro(ms["def"]["pasos"], ms["paso"]):      # ya lo tenías y aún hay que entregarlo
                self.fallar_mision(tr("Has dejado atrás el vehículo de la misión."))
                return
            ms["veh"] = None
        ms["enemigos"] = []
        ms["veh_enemigos"] = []
        ms["generado"] = False
        if (ms.get("abriendo") or {}).get("canal") is not None:
            ms["abriendo"]["canal"].parar()
        ms["abriendo"] = None
        if not ms["recogido"]:
            ms["objeto"] = None
        if tipo in ("dialogo", "dar", "policia"):
            return
        ms["pendiente"] = True
        self._materializar()

    def voces_activas(self):
        """Las voces grabadas suenan si el jugador las quiere. Cada frase tiene la grabación que corresponde a su personaje y
        a cómo le hablan; la que no la tenga, la dice el lector."""
        return bool(self.cfg["voces_grabadas"])

    def _siguiente_paso(self):
        ms = self.mision
        if not ms:
            return
        ms["paso"] += 1
        pasos = ms["def"]["pasos"]
        if ms["paso"] >= len(pasos):
            self._completar_mision()
            return
        p = pasos[ms["paso"]]
        if not self.cumple_decision(p):                          # este paso es de otra rama de la historia
            self._siguiente_paso()
            return
        ms["limite"] = p.get("limite")
        ms["gps_callado"] = False
        ms["abriendo"], ms["abierto"], ms["policia_en"] = None, False, None
        ms["t_sin_gps"] = 0.0
        ms["avisos"] = set()
        ms["generado"] = False
        ms["recogido"] = False
        ms["radar_usado"] = False
        tipo = p["tipo"]
        l = self._lugar_paso(p)
        if (tipo not in ("dialogo", "dar", "decision") and not ms.get("reanudando") and paso_seguro(pasos, ms["paso"])
                and any(q["tipo"] not in ("dialogo", "dar", "decision") for q in pasos[:ms["paso"]])):          # con algo ya hecho: si no, es el principio
            # Punto de control: si fallas más adelante, puedes volver aquí en lugar de al principio.
            x, y = self.pos()
            ms["control"] = {"paso": ms["paso"], "copia": copy.deepcopy(self.j.a_dict()), "reloj": self.reloj, "dia": self.dia,
                             "mapa": self.mundo.id, "x": x, "y": y}
        ms["reanudando"] = False
        if tipo == "dialogo":
            from . import voces
            ms["pantalla"] = Dialogo(self.app, [(self.txt(q), self.txt(tx)) for q, tx in p["lineas"]], self._seguir_si(ms),
                                     voces=voces.de_dialogo(ms["def"]["id"], ms["paso"], p["lineas"], self.j) if self.voces_activas() else None)
            self.app.abrir(ms["pantalla"])
            return
        if tipo == "decision":
            self._paso_decision(ms, p)
            return
        if tipo == "dar":
            if "arma" in p:
                self.dar_arma(p["arma"], p.get("balas", 0))
            if "balas_arma" in p and p["balas_arma"] in self.j.armas:
                self.j.armas[p["balas_arma"]]["reserva"] += p.get("balas", 0)
                self.decir(tr('Recibes {get} balas.').format(get=(p.get('balas', 0))))
            if "dinero" in p:
                self.dar_dinero(p["dinero"], tr("Recibes"))
            if "sustancia" in p and self.sustancia(p["sustancia"]):
                self.j.sustancias[p["sustancia"]] = self.j.sustancias.get(p["sustancia"], 0) + int(p.get("cantidad", 1))
                self.decir(tr('Recibes {get} de {lower}.').format(get=(p.get('cantidad', 1)), lower=(self.sustancia(p['sustancia'])['nombre'].lower())))
            self._siguiente_paso()
            return
        if p.get("texto"):
            self.decir(self.txt(p["texto"]))
        if tipo == "robar":                                      # la misión te da vehículo: qué pasa con el tuyo
            self.aviso_vehiculo_mision(ms["def"], p)
        ms["pendiente"] = True
        self._materializar()
        self.sv_mision_paso()

    def _seguir_si(self, ms):
        """Lo que hace una escena de la misión al terminar: pasar al paso siguiente, pero solo si la misión sigue siendo
        esa y sigue en ese paso. Una escena que se quedó abierta debajo de otra pantalla (te detienen en el mismo instante
        en que cae el último enemigo) no puede hacer avanzar una misión que ya se falló o se volvió a empezar."""
        k = ms["paso"]

        def f():
            if self.mision is ms and ms["paso"] == k:
                self._siguiente_paso()
        return f

    def mision_en_escena(self):
        """¿La misión está en una escena o en una decisión, esperando a que la leas? Entonces lo que había que hacer ya
        está hecho: que te detengan o te tumben en ese momento no la falla."""
        ms = self.mision
        if not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return False
        return ms["def"]["pasos"][ms["paso"]]["tipo"] in ("dialogo", "decision") and ms.get("pantalla") in self.app.pila

    def _cerrar_escena(self, ms):
        pan = ms.get("pantalla")
        ms["pantalla"] = None
        if pan is not None and pan in self.app.pila:
            if hasattr(pan, "al_terminar"):
                pan.al_terminar = None
            if hasattr(pan, "_callar_voz"):
                pan._callar_voz()
            self.app.pila.remove(pan)

    def gps_mision(self, hablar=True):
        """Vuelve a marcar en el GPS lo que pide el paso actual de la misión. Sirve cuando te has desviado a otra cosa
        (has marcado otro sitio, has seguido algo con el radar) y el GPS se ha quedado sin destino. No crea nada."""
        ms = self.mision
        if not ms or not (0 <= ms["paso"] < len(ms["def"]["pasos"])) or ms.get("pendiente"):
            return False
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        l = self._lugar_paso(p)
        antes = self.gps
        v = ms.get("veh")
        if tipo == "robar" and v is not None and not v.muerto and self.j.veh is not v:
            self.fijar_gps(v.x, v.y, v.nombre, auto=True, radio=4, callar=True)
        elif tipo == "entregar" and v is not None and not v.muerto and self.j.veh is not v:
            self.fijar_gps(v.x, v.y, v.nombre, auto=True, radio=4, callar=True)
        elif tipo in ("ir", "entregar", "eliminar", "sigilo") and l:
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "recoger" and ms.get("objeto") is not None and not ms["recogido"]:
            o = ms["objeto"]
            self.fijar_gps(o.x, o.y, p["objeto"], auto=True, radio=2, callar=True)
        elif tipo == "perseguir" and ms.get("veh_objetivo") is not None:
            vo = ms["veh_objetivo"]
            self.fijar_gps(vo.x, vo.y, vo.nombre, sigue=vo, auto=True, callar=True)
        elif tipo == "escoltar" and ms.get("escolta"):
            d = self.lugares.get(p.get("destino", "")) if ms["escolta"]["contigo"] else l
            if d:
                self.gps_a_lugar(d, auto=True, callar=True)
        elif tipo == "vigilar" and l and ms.get("vigia") and not ms["vigia"]["dentro"]:
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "carrera" and l and (ms.get("carrera") or {}).get("fase") == "ir":
            self.gps_a_lugar(l, auto=True, callar=True)
        elif tipo == "ruta" or (tipo == "carrera" and (ms.get("carrera") or {}).get("fase") == "corre"):
            puntos = p.get("puntos", [])
            q = self.lugares.get(puntos[ms.get("ruta_i", 0)]) if ms.get("ruta_i", 0) < len(puntos) else None
            if q:
                self.gps_a_lugar(q, auto=True, callar=True)
        if self.gps is None or self.gps is antes:
            return False
        ms["gps_callado"] = False
        if hablar:
            self.app.son("notificacion")
            self.decir(tr('El GPS vuelve a la misión: {nombre}.').format(nombre=(self.gps['nombre'])))
            self.repetir_gps_suave()
        return True

    def _materializar(self):
        """Crea lo que necesita el paso actual (vehículos, enemigos, objetos) y orienta el GPS."""
        ms = self.mision
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        l = self._lugar_paso(p)
        if tipo == "policia":
            ms["pendiente"] = False
            # la policía puede tardar en llegar: lo que diga el paso, y en un golpe preparado, lo que la entretenga el vigilante
            espera = self.golpe_retraso_policia(p.get("nivel", 2)) if getattr(self, "golpe", None) else self._num_paso(p, "retraso")
            if espera > 0 and self.j.estrellas == 0 and not self.cfg["sin_policia"]:
                ms["policia_en"] = self.t + espera
                if not getattr(self, "golpe", None):
                    self.decir(tr('La policía tardará unos {int} segundos en llegar.').format(int=(int(round(espera)))))
            else:
                ms["policia_en"] = None
                self.poner_busqueda(p.get("nivel", 2))
            self.quitar_gps_auto()
            return
        if tipo == "practica":                                   # una práctica de un tutorial: no crea nada, solo vigila lo que haces
            ms["pendiente"] = False
            if ms.get("practica_paso") != ms["paso"]:
                ms["practica_paso"] = ms["paso"]
                ms["practica"] = {"metros": 0.0, "giro": 0.0, "x": None, "y": None, "rumbo": 0.0, "t": 0.0, "t_aviso": 20.0, "dicho": set(), "evento": None,
                                  "servicios": self.j.stats.get("servicios", 0)}
            return
        if tipo == "entregar" and ms.get("veh") is not None and self.j.veh is not ms["veh"] and not ms["veh"].muerto:
            ms["pendiente"] = False
            return
        if l and l.mapa != self.mundo.id and not p.get("aqui"):
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        ms["pendiente"] = False
        if tipo == "seguir" and l:
            d = self.lugares.get(p.get("destino", ""))
            ruta = self.mundo.ruta(l.x, l.y, d.x, d.y) if d is not None and d.mapa == l.mapa else [(l.x, l.y)]
            ms["movil"] = {"x": l.x, "y": l.y, "ruta": list(ruta), "i": 0, "t_paso": 0.0, "cerca": 0.0, "lejos": 0.0, "t_aviso": 0.0,
                           "vel": float(p.get("velocidad", 2.3)), "nombre": self.txt(p.get("persona") or tr("tu objetivo")), "espera": 6.0,
                           "visto": False, "rumbo": None,
                           "aguante": 9.0 + 3.0 * min(3, self.fallos.get(ms["def"]["id"], 0)) + (D.AJ("ayuda_seguir_aguante") if self.ayuda_persecucion() else 0.0)}
            self.gps_a_lugar(l, auto=True, callar=True)           # todavía no ha salido: el GPS te lleva hasta donde está
            return
        if tipo == "escoltar" and l:
            ms["escolta"] = {"x": l.x, "y": l.y, "t_paso": 0.0, "t_aviso": 0.0, "nombre": self.txt(p.get("persona") or tr("tu acompañante")), "contigo": False}
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo == "sigilo" and l:
            n = max(1, int(p.get("guardias", 3)))
            guardias = []
            for k in range(n):
                a = 2 * math.pi * k / n + 0.6
                r = 9.0 + 3.0 * (k % 2)
                gx, gy = l.x + math.sin(a) * r, l.y + math.cos(a) * r
                if not self.mundo.transitable(gx, gy):
                    gx, gy = self.mundo.punto_libre(gx, gy)
                guardias.append({"x": gx, "y": gy, "x0": gx, "y0": gy, "a": a + math.pi / 2, "fase": k * 1.7, "t_paso": 0.3 * k})
            ms["guardias"] = guardias
            ms["t_aviso"] = 0.0
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo == "ruta":
            ms["ruta_i"] = 0
            self._ruta_siguiente(p, primero=True)
            return
        if tipo == "vigilar" and l:
            ms["vigia"] = {"t": 0.0, "dentro": False, "fuera": 0.0, "t_aviso": 0.0, "ronda": None, "t_ronda": 9.0, "rondas": 0,
                           "t_suceso": 5.0, "sucesos": 0, "visto": 0.0}
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo == "carrera" and l:
            self._parar_rivales(ms)
            ms["carrera"] = {"fase": "ir", "t": 0.0, "rivales": [], "puesto": 0}
            ms["ruta_i"] = 0
            self.gps_a_lugar(l, auto=True, callar=True)
            return
        if tipo in ("ir", "entregar") and l:
            self.gps_a_lugar(l, auto=True)
        elif tipo == "robar" and l:
            if ms.get("veh") is not None and not ms["veh"].muerto:
                return
            x, y, d = self.mundo.plaza_junto_a(l)
            self._despejar_plaza(x, y)
            v = self.crear_vehiculo(p["modelo"], x, y, d, "aparcado", p.get("nombre"), "mision")
            v.cerrado = not p.get("abierto", False)
            v.con_alarma = bool(p.get("busqueda"))
            v.sirena = self.son("loc_vehiculo", bucle=True, xy=(x, y), ref=5, maxd=70)
            ms["veh"] = v
            self.fijar_gps(x, y, v.nombre, auto=True, radio=4)
        elif tipo == "eliminar" and l:
            self.gps_a_lugar(l, auto=True)
            if p.get("ya"):
                self._generar_enemigos(p, l)
        elif tipo == "recoger":
            if ms["recogido"]:
                return
            if p.get("aqui") or not l:
                x, y = ms["restos"] or self.pos()
                x, y = self.mundo.punto_libre(x, y)
            else:
                x, y = l.x, l.y
            o = Objeto("mision", p["objeto"], x, y, "loc_objeto")
            self.objetos.append(o)
            ms["objeto"] = o
            self.fijar_gps(x, y, p["objeto"], auto=True, radio=2)
        elif tipo == "perseguir" and l:
            x, y, d = self.mundo.plaza_junto_a(l)
            x, y = (x, self.mundo.carril("H", self.mundo._idx(y, self.mundo.NY), d)) if d in (1, 3) else (self.mundo.carril("V", self.mundo._idx(x, self.mundo.NX), d), y)
            v = self.crear_vehiculo(p["modelo"], x, y, d, "huida", p.get("nombre"), "objetivo")
            v.salud = v.salud_max = float(p.get("salud", 120))
            v.ocupado = True
            v.hostil = True
            # Quien huye no va a fondo: se le tiene que poder alcanzar con un coche corriente. Más despacio en fácil y en normal.
            ms["vel_huida"] = v.vel_obj = min(v.modelo["vel_max"] * {"facil": 0.45, "normal": 0.54}.get(self.cfg["dificultad"], 0.62), 21.0)
            veces = min(3, self.fallos.get(ms["def"]["id"], 0))
            if veces:                                            # ya se te ha escapado antes: esta vez va más nervioso y comete más errores
                ms["vel_huida"] = v.vel_obj = ms["vel_huida"] * (1.0 - 0.09 * veces)
                if ms.get("limite") is not None:
                    ms["limite"] = ms["limite"] * (1.0 + 0.15 * veces)
                self.decir(tr("Ya se te escapó antes, y lo sabe: va más nervioso y no corre tanto.") + (tr(" Tienes algo más de tiempo.") if ms.get("limite") is not None else ""))
            if self.ayuda_persecucion() and ms.get("limite") is not None and D.AJ("ayuda_tiempo") > 0:
                ms["limite"] = ms["limite"] * (1.0 + D.AJ("ayuda_tiempo") / 100.0)
            ms["t_canta"] = self.pers("canta_cada")
            ms["rumbo_obj"] = None
            ms["veh_objetivo"] = v
            self.objetivo = v
            self.fijar_gps(x, y, v.nombre, sigue=v, auto=True)
            self.pers_explicar(v)

    def _despejar_plaza(self, x, y):
        """Quita los vehículos aparcados que estorban donde va a aparecer uno de misión."""
        for o in list(self.vehiculos):
            if o.ia == "aparcado" and not o.tag and o is not self.j.veh and not getattr(o, "mio", False) and o.dist(x, y) < 9:
                if o.plaza is not None:
                    self.plazas_usadas.add(o.plaza)
                self.quitar_vehiculo(o)
        for l in self.mundo.lugares.values():
            if l.get("vehiculo"):
                px, py, _ = self.mundo.plaza_junto_a(l)
                if math.hypot(px - x, py - y) < 9:
                    self.plazas_usadas.add(tr("L:") + l.id)

    def _crear_enemigo(self, grupo, x, y):
        """Un enemigo de un grupo de una misión. El grupo dice su tipo («clase», del catálogo de tipos de enemigo) o, como
        siempre, su nombre, su arma y su salud; lo que el grupo diga manda sobre lo que diga el tipo."""
        f = G.enemigo(grupo)
        e = G.vestir(Persona("enemigo", x, y, f["nombre"]), f)
        e.salud = e.salud * (1.5 if self.cfg["mod_enemigos"] else 1.0) * (1.0 + 0.15 * min(4, self.j.ciclo))
        e.banda = G.banda_en(e.nombre)
        e.hostil = True
        e.estado = "ataca"
        e.inofensivo = bool(grupo.get("inofensivo"))          # un muñeco de prácticas: se le puede fijar, pero no ataca
        e.deportivo = bool(grupo.get("deportivo"))            # un rival del gimnasio: tumbarlo no es delito
        e.intimidar = bool(grupo.get("intimidar"))            # a este no hay que matarle: se rinde cuando ha recibido bastante
        e.salud_entera = e.salud
        e.tag = "mision"
        e.t_disparo = random.uniform(1.5, 3.0)
        return e

    def _generar_enemigos(self, p, l):
        ms = self.mision
        ms["generado"] = True
        en_coche = 0
        escolta = self.escolta_ajuste()                          # con la opción: más oposición si vienes con los tuyos
        for grupo, n in self.escolta_grupos(p["enemigos"], escolta):
            f = G.enemigo(grupo)
            a_pie = None
            # Un grupo cuyo tipo va en vehículo llega en él: viene por la calle, para cerca de ti y se bajan. En un servidor, a pie.
            if f["vehiculo"] and n > 0 and not self.en_servidor and not grupo.get("inofensivo") and not grupo.get("deportivo"):
                a_pie = [self._crear_enemigo(grupo, l.x, l.y) for _ in range(n)]
                while a_pie:
                    viajan = a_pie[:f["ocupantes"]]
                    v = self.llegar_en_vehiculo(f["vehiculo"], viajan)
                    if v is None:                                # aquí no puede venir un vehículo: van a pie, como los demás
                        break
                    a_pie = a_pie[len(viajan):]
                    ms.setdefault("veh_enemigos", []).append(v)
                    ms["enemigos"] += viajan
                    en_coche += len(viajan)
                n = len(a_pie)
            for k in range(n):
                for _ in range(20):
                    a = random.uniform(0, 2 * math.pi)
                    r = random.uniform(5, 16)
                    x, y = l.x + math.sin(a) * r, l.y + math.cos(a) * r
                    if self.mundo.transitable(x, y):
                        break
                else:
                    x, y = l.x, l.y
                if a_pie is None:
                    e = self._crear_enemigo(grupo, x, y)
                else:
                    e = a_pie[k]
                    e.x, e.y = x, y
                self.personas.append(e)
                ms["enemigos"].append(e)
                if e.dist(*self.pos()) > 60:                      # más lejos que nunca (con un rifle): esperan quietos a que te acerques o les dispares
                    e.activo = False
        n = ms["quedan"] = len(ms["enemigos"])
        self.escolta_endurecer(ms["enemigos"], escolta)
        if all(getattr(e, "inofensivo", False) for e in ms["enemigos"]):         # muñecos y dianas: no son enemigos
            x, y = self.pos()
            cerca = min(ms["enemigos"], key=lambda e: e.dist(x, y))
            self.decir((tr('Hay un objetivo de prácticas, {metros}.').format(metros=(M.metros(cerca.dist(x, y)))) if n == 1 else tr('Hay {n} objetivos de prácticas; el más cercano, {metros}.').format(n=(n), metros=(M.metros(cerca.dist(x, y)))))
                       + tr(" Pulsa Q para fijarlo."))
        else:
            llegan = ""
            if en_coche:
                llegan = (tr(" Viene en un vehículo: escucha el motor.") if n == 1 else tr(" Vienen en un vehículo: escucha el motor.") if en_coche == n
                          else tr(' {en_coche} de ellos vienen en un vehículo: escucha el motor.').format(en_coche=(en_coche))) + tr(" Con Q fijas también el vehículo: si lo destruyes antes de que se bajen, caen con él.")
            self.decir((tr("Hay un enemigo. Pulsa Q para fijarlo.") if n == 1 else tr('Hay {n} enemigos. Pulsa Q para fijar al más cercano.').format(n=(n))) + llegan)
        if self.cfg["punteria"] == "completa":
            self.fijar(callar=True)
        self.sv_mision_enemigos()                                # en grupo, los enemigos son de todos

    # ------------------------------------------------------------ actualización
    def actualizar_mision(self, dt):
        ms = self.mision
        if not ms or ms["paso"] < 0 or ms["paso"] >= len(ms["def"]["pasos"]):
            return
        j = self.j
        p = ms["def"]["pasos"][ms["paso"]]
        tipo = p["tipo"]
        if tipo in ("dialogo", "dar", "decision"):
            return
        x, y = self.pos()
        if ms["limite"] is not None:
            antes = ms["limite"]
            ms["limite"] -= dt
            for marca in (120, 60, 30, 10):
                if antes > marca >= ms["limite"]:
                    self.decir(tr('Quedan {marca} segundos.').format(marca=(marca)))
            if ms["limite"] < 10 and int(antes) != int(ms["limite"]):
                self.son("reloj", cat="interfaz")
            if ms["limite"] <= 0:
                self.fallar_mision(tr("Se ha acabado el tiempo."))
                return
        v = ms.get("veh")
        if v is not None and tipo in ("robar", "entregar"):
            if v.muerto or v.ardiendo >= 0:
                self.fallar_mision(tr("El vehículo ha quedado destruido."))
                return
            if tipo == "entregar" and 100.0 * v.salud / v.salud_max < p.get("salud_min", 0):
                self.fallar_mision(tr("El vehículo ha sufrido demasiados daños."))
                return
        l = self._lugar_paso(p)
        # Te has desviado y el GPS se ha quedado sin destino: a los dos segundos vuelve solo a lo que pide la misión.
        if self.gps is None and not ms.get("gps_callado") and not ms.get("pendiente"):
            ms["t_sin_gps"] = ms.get("t_sin_gps", 0.0) + dt
            if ms["t_sin_gps"] > 2.0:
                ms["t_sin_gps"] = -20.0                           # si no hay nada que marcar, no insiste a cada momento
                self.gps_mision()
        elif self.gps is not None:
            ms["t_sin_gps"] = 0.0
        if ms.get("pendiente"):
            if tipo != "policia" and (l is None or l.mapa == self.mundo.id):
                self._materializar()
            if ms.get("pendiente"):
                if tipo == "robar" and j.veh is not None and j.veh is ms.get("veh"):
                    self._paso_hecho()
                return
        if tipo == "seguir":
            self._paso_seguir(ms, p, x, y, dt)
        elif tipo == "escoltar":
            self._paso_escoltar(ms, p, x, y, dt)
        elif tipo == "sigilo":
            self._paso_sigilo(ms, p, l, x, y, dt)
        elif tipo == "vigilar":
            self._paso_vigilar(ms, p, l, x, y, dt)
        elif tipo == "carrera":
            self._paso_carrera(ms, p, l, x, y, dt)
        elif tipo == "practica":
            self._paso_practica(ms, p, x, y, dt)
        elif tipo == "ruta":
            punto = self.lugares.get(p.get("puntos", [""])[min(ms.get("ruta_i", 0), len(p.get("puntos", [""])) - 1)])
            if punto and punto.mapa == self.mundo.id and math.hypot(punto.x - x, punto.y - y) <= (20 if j.veh else 10):
                ms["ruta_i"] += 1
                if ms["ruta_i"] >= len(p["puntos"]):
                    self._paso_hecho()
                else:
                    self.app.son("llegada")
                    self._ruta_siguiente(p)
        elif tipo == "ir":
            radio = 28 if self.mundo.tipo == "mar" else 17 if j.veh else p.get("radio", 8)
            if l and math.hypot(l.x - x, l.y - y) <= radio and (not j.veh or abs(j.veh.vel) < 3):
                if p.get("exige") == "radar" and not ms.get("radar_usado"):      # el ejercicio era usar el radar: haber llegado de otra manera no lo cumple
                    if "exige" not in ms["avisos"]:
                        ms["avisos"].add("exige")
                        self.app.son("notificacion")
                        self.decir(tr("Has llegado, pero este ejercicio es para aprender el radar. Pulsa Tabulador para oír lo que tienes cerca: con eso queda hecho."))
                else:
                    self._paso_hecho()
        elif tipo == "robar":
            if j.veh is v:
                if p.get("busqueda"):
                    self.poner_busqueda(p["busqueda"])
                self._paso_hecho()
            elif (v is not None and j.veh is not None and ms["def"].get("vehiculo_libre") and self.vale_para_mision(j.veh, p)
                  and j.veh.dist(v.x, v.y) < 25 and abs(j.veh.vel) < 3):
                # la misión no exige su vehículo y has venido con el tuyo hasta donde está el suyo: la haces con el tuyo
                self.quitar_vehiculo(v)
                ms["veh"], ms["veh_tuyo"] = j.veh, True
                self.hacer_mio(j.veh, callar=True)
                self.son("puerta_coche")
                self.decir(tr('Haces la misión con {nombre}: lo que hay que llevar va contigo.').format(nombre=(j.veh.nombre)))
                self._paso_hecho()
        elif tipo == "entregar":
            if v is None:
                self.fallar_mision(tr("Has perdido el vehículo de la misión."))
            elif j.veh is v:
                cerca = 32 if v.modelo.get("vuela") else 18
                if l and l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) <= cerca and abs(v.vel) < 2.5:
                    if not ms.get("veh_tuyo"):                   # el de la misión se entrega; el tuyo te lo quedas, y sigues en él
                        self.salir_vehiculo(forzado=True)
                        self.j.x, self.j.y = l.x, l.y
                        self.quitar_vehiculo(v)
                    ms["veh"] = None
                    self.son("puerta_coche")
                    self._paso_hecho()
                elif l and l.mapa == self.mundo.id and math.hypot(l.x - x, l.y - y) <= cerca and "frena" not in ms["avisos"]:
                    ms["avisos"].add("frena")
                    self.decir(tr("Has llegado. Detén el vehículo."))
            elif "fuera" not in ms["avisos"] and v is not None and v.dist(x, y) > 30:
                ms["avisos"].add("fuera")
                self.fijar_gps(v.x, v.y, v.nombre, auto=True, radio=4, callar=True)
                self.decir(tr('Has dejado atrás {nombre}. Vuelve a por él.').format(nombre=(v.nombre)))
            elif j.veh is None and v is not None and "fuera" in ms["avisos"] and v.dist(x, y) < 6:
                ms["avisos"].discard("fuera")
        elif tipo == "eliminar":
            if not ms["generado"]:
                if l and math.hypot(l.x - x, l.y - y) < self.alcance_avistar():      # con un rifle se les ve llegar desde más lejos
                    self._generar_enemigos(p, l)
            else:
                if any(e.muerto and getattr(e, "intimidar", False) for e in ms["enemigos"]):
                    self.fallar_mision(tr("Te has pasado: le querían asustado, no muerto."))
                    return
                vivos = sum(1 for e in ms["enemigos"] if not e.muerto and not getattr(e, "rendido", False))
                if vivos != ms["quedan"]:
                    ms["quedan"] = vivos
                    if vivos > 0:
                        self.decir(tr("Queda uno. Pulsa Q para fijarlo.") if vivos == 1 else tr('Quedan {vivos}.').format(vivos=(vivos)))
                if vivos == 0:
                    ms["enemigos"] = []
                    self._paso_hecho()
        elif tipo == "recoger":
            if ms["recogido"]:
                self._paso_hecho()
            else:
                self._paso_abrir(ms, p, dt)
        elif tipo == "policia":
            if ms.get("policia_en") is not None:                 # aún no ha llegado: no se da por despistada
                if getattr(self, "golpe", None):
                    ms["policia_en"] = self.golpe["llegan"] if not self.golpe["llegado"] else None      # la lleva el golpe: el vigilante y el conductor la retrasan
                elif self.t >= ms["policia_en"]:
                    ms["policia_en"] = None
                    self.poner_busqueda(p.get("nivel", 2))
            elif j.estrellas == 0 and j.puntos_busqueda < 1:
                self._paso_hecho()
        elif tipo == "perseguir":
            vo = ms.get("veh_objetivo")
            if vo is None or vo.muerto:
                if ms["restos"] is None and vo is not None:
                    ms["restos"] = (vo.x, vo.y)
                self.decir(tr('¡{get} destruido!').format(get=(p.get('nombre', tr('El objetivo')))))
                ms["veh_objetivo"] = None
                self._paso_hecho()
            else:
                lejos = vo.dist(x, y)
                # si se te escapa mucho, afloja: se oye que aminora y vuelves a tener ocasión
                a_lejos, a_medio = self.pers("afloja_lejos"), self.pers("afloja_medio")
                vo.vel_obj = ms.get("vel_huida", vo.vel_obj) * (self.pers("factor_lejos") / 100.0 if lejos > a_lejos else self.pers("factor_medio") / 100.0 if lejos > a_medio else 1.0)
                if lejos > a_lejos and "lejos" not in ms["avisos"]:
                    ms["avisos"].add("lejos")
                    self.decir(tr('{nombre} te saca ventaja, pero se confía y afloja. Va {pers_donde}.').format(nombre=(vo.nombre), pers_donde=(self.pers_donde(vo))))
                elif lejos < min(60, a_medio):
                    ms["avisos"].discard("lejos")
                self.pers_giros(ms, vo, dt)                      # con la ayuda puesta, cada giro
                ms["t_canta"] = ms.get("t_canta", 12.0) - dt
                if ms["t_canta"] <= 0 and lejos > self.pers("canta_desde"):      # cada poco, por dónde va: sin eso, de oído se le pierde enseguida
                    ms["t_canta"] = self.pers("canta_cada")
                    self.decir(f"{vo.nombre}: {self.pers_donde(vo)}.")
                elif lejos < 22 and "atiro" not in ms["avisos"] and j.veh:
                    ms["avisos"].add("atiro")
                    self.decir(tr('Tienes {nombre} a tiro. Fíjalo con la Q y dispara con Control, o embístelo: cada golpe y cada bala le restan.').format(nombre=(vo.nombre)))
                if j.veh and self.gps is None:
                    self.fijar_gps(vo.x, vo.y, vo.nombre, sigue=vo, auto=True, callar=True)

    # ------------------------------------------------- pasos de oído: seguir, escoltar, sigilo y ruta
    def _ruta_siguiente(self, p, primero=False):
        ms = self.mision
        puntos = p.get("puntos", [])
        l = self.lugares.get(puntos[ms["ruta_i"]]) if ms["ruta_i"] < len(puntos) else None
        if l is None:
            return
        self.gps_a_lugar(l, auto=True, callar=True)
        self.decir(tr('Punto {v} de {len}: {nombre_lugar}.').format(v=(ms['ruta_i'] + 1), len=(len(puntos)), nombre_lugar=(self.nombre_lugar(l))) if not primero else
                   tr('Son {len} puntos. El primero: {nombre_lugar}.').format(len=(len(puntos)), nombre_lugar=(self.nombre_lugar(l))))

    def _paso_seguir(self, ms, p, x, y, dt):
        """Seguir a alguien de oído: ni tan cerca que te vea, ni tan lejos que lo pierdas."""
        o = ms.get("movil")
        if o is None:
            return
        j = self.j
        d = math.hypot(o["x"] - x, o["y"] - y)
        if not o.get("visto", True):                          # no echa a andar hasta que das con él: da igual lo lejos que te pille la misión
            o["t_paso"] -= dt
            if o["t_paso"] <= 0:
                o["t_paso"] = 0.9
                self.son("paso_npc", xy=(o["x"], o["y"]), ref=5, maxd=75, vol=1.0)
            if d > 42:
                return
            o["visto"] = True
            self.quitar_gps_auto()
            self.app.son("notificacion")
            pegado = d < (12.0 if j.veh else 6.0) + 4
            if pegado:                                        # la misión empieza donde está él (el inspector del ayuntamiento): tiempo para apartarse
                o["espera"] = max(o["espera"], 10.0)
            self.decir(tr('Ahí está {nombre}, a {int} metros, {direccion_txt}. Todavía no se ha movido: en unos segundos echa a andar. Síguele de oído, sin pegarte a él y sin perderle.').format(nombre=(o['nombre']), int=(int(d)), direccion_txt=(self.direccion_txt(o['x'], o['y'])))
                       + (tr(" Estás a su lado: apártate unos metros antes de que salga, o te verá.") if pegado else ""))
            return
        if o["espera"] > 0:                                   # al principio se queda quieto un momento: te da tiempo a localizarlo
            o["espera"] -= dt
        elif o["i"] < len(o["ruta"]):
            tx, ty = o["ruta"][o["i"]]
            r = math.hypot(tx - o["x"], ty - o["y"])
            paso = o["vel"] * dt
            if r <= paso:
                o["x"], o["y"] = tx, ty
                o["i"] += 1
            else:
                o["x"] += (tx - o["x"]) / r * paso
                o["y"] += (ty - o["y"]) / r * paso
        o["t_paso"] -= dt
        if o["t_paso"] <= 0:
            o["t_paso"] = 0.55
            self.son("paso_npc", xy=(o["x"], o["y"]), ref=5, maxd=75, vol=1.0)
        limite_cerca = 12.0 if j.veh else 3.5 if j.agachado else 6.0
        # mientras espera quieto, todavía no mira a su alrededor: solo cuenta que te pegues a él cuando ya anda
        o["cerca"] = o["cerca"] + dt if d < limite_cerca and o["espera"] <= 0 else 0.0
        tope = self.pers("seguir_lejos")
        o["lejos"] = o["lejos"] + dt if d > tope else 0.0
        o["t_aviso"] -= dt
        if self.ayuda_persecucion() and o["espera"] <= 0 and o["i"] < len(o["ruta"]):      # con la ayuda puesta, cada vez que dobla una esquina
            tx, ty = o["ruta"][o["i"]]
            if math.hypot(tx - o["x"], ty - o["y"]) > 2:
                rumbo = M.cardinal(M.rumbo_a(tx - o["x"], ty - o["y"]))
                if o.get("rumbo") is not None and rumbo != o["rumbo"]:
                    calle = self._calle_de(tx, ty)
                    self.decir(tr('{capitalize} tuerce hacia el {rumbo}').format(capitalize=(o['nombre'].capitalize()), rumbo=(rumbo)) + (tr(' por {calle}').format(calle=(calle)) if calle else "") + tr('. Va a {int} metros, {direccion_txt}.').format(int=(int(d)), direccion_txt=(self.direccion_txt(o['x'], o['y']))))
                    o["t_aviso"] = max(o["t_aviso"], 2.5)
                o["rumbo"] = rumbo
        if o["t_aviso"] <= 0 and (d < limite_cerca + 4 or d > tope - 15):
            o["t_aviso"] = self.pers("seguir_aviso")
            self.decir(tr("Estás demasiado cerca. Quédate atrás.") if d < limite_cerca + 4 else tr('Se te aleja: va a {int} metros, {direccion_txt}.').format(int=(int(d)), direccion_txt=(self.direccion_txt(o['x'], o['y']))))
        if o["cerca"] > 1.5:
            self.fallar_mision(tr('{capitalize} se ha dado cuenta de que le seguías.').format(capitalize=(o['nombre'].capitalize())))
        elif o["lejos"] > o.get("aguante", 9.0):
            self.fallar_mision(tr('Has perdido de vista a {nombre}.').format(nombre=(o['nombre'])))
        elif o["i"] >= len(o["ruta"]) and d < 55:
            self._paso_hecho()

    def _paso_escoltar(self, ms, p, x, y, dt):
        """Llevar a alguien hasta un sitio: te sigue a pie y sube contigo si coges un vehículo."""
        e = ms.get("escolta")
        if e is None:
            return
        j = self.j
        d = math.hypot(e["x"] - x, e["y"] - y)
        dest = self.lugares.get(p.get("destino", ""))
        if not e["contigo"]:
            if d < 6:
                e["contigo"] = True
                self.app.son("llegada")
                self.decir(tr('{capitalize} va contigo. Te sigue a pie y sube al vehículo que cojas.').format(capitalize=(e['nombre'].capitalize())) +
                           (tr(' Llévale a {nombre_lugar}.').format(nombre_lugar=(self.nombre_lugar(dest))) if dest else ""))
                if dest:
                    self.gps_a_lugar(dest, auto=True, callar=True)
            return
        if j.veh:
            e["x"], e["y"] = x, y                             # va de pasajero
        elif d > 3.0:
            paso = min(d - 2.5, (6.5 if d > 12 else 4.0) * dt)
            e["x"] += (x - e["x"]) / d * paso
            e["y"] += (y - e["y"]) / d * paso
            e["t_paso"] -= dt
            if e["t_paso"] <= 0:
                e["t_paso"] = 0.45
                self.son("paso_npc", xy=(e["x"], e["y"]), ref=4, maxd=40, vol=0.8)
        if dest and dest.mapa == self.mundo.id and math.hypot(dest.x - x, dest.y - y) <= (17 if j.veh else p.get("radio", 9)) \
                and (not j.veh or abs(j.veh.vel) < 3) and math.hypot(e["x"] - x, e["y"] - y) < 15:
            self._paso_hecho()

    def _paso_sigilo(self, ms, p, l, x, y, dt):
        """Llegar a un punto vigilado sin que te oigan: agachado se te oye menos; corriendo, mucho más."""
        j = self.j
        t = self.app.teclas
        corriendo = self.corriendo_ahora()
        oido = 22.0 if j.veh else 2.6 if j.agachado else 11.0 if corriendo else 6.0
        cerca = 999.0
        for g in ms.get("guardias", []):
            g["fase"] += dt * 0.35                             # cada guardia pasea de un lado a otro de su puesto
            k = math.sin(g["fase"]) * 5.0
            nx, ny = g["x0"] + math.sin(g["a"]) * k, g["y0"] + math.cos(g["a"]) * k
            if self.mundo.transitable(nx, ny):
                g["x"], g["y"] = nx, ny
            g["t_paso"] -= dt
            if g["t_paso"] <= 0:
                g["t_paso"] = 0.8
                self.son("paso_npc", xy=(g["x"], g["y"]), ref=3, maxd=35, vol=1.0)
            cerca = min(cerca, math.hypot(g["x"] - x, g["y"] - y))
        ms["t_aviso"] = ms.get("t_aviso", 0.0) - dt
        if cerca <= oido:
            self.son("grito", xy=(x, y), vol=0.6)
            self.fallar_mision(tr("Un vigilante te ha oído."))
            return
        if cerca < oido + 4 and ms["t_aviso"] <= 0:
            ms["t_aviso"] = 4.0
            self.son("buscando", cat="interfaz", vol=0.6)
            self.decir(tr('Tienes un vigilante a {int} metros. ').format(int=(int(cerca))) + (tr("Agáchate con la X.") if not j.agachado else tr("No te muevas hacia él.")))
        if l and math.hypot(l.x - x, l.y - y) <= 2.5 and not j.veh:
            if p.get("objeto"):
                self.son("recoger", cat="interfaz")
                self.decir(tr('Tienes {txt}.').format(txt=(self.txt(p['objeto']))))
            self._paso_hecho()

    def _paso_decision(self, ms, p):
        """Una decisión de la historia: se elige en un menú, queda apuntada y tiene consecuencias."""
        opciones = p.get("opciones") or []
        clave = p.get("clave") or f"{ms['def']['id']}_{ms['paso']}"
        if not opciones:
            self._siguiente_paso()
            return

        def elegir(n, o):
            def f():
                self.app.cerrar(menu)
                if self.mision is not ms:
                    return
                if not ms.get("repeticion"):                     # al repetir una misión, lo decidido no cambia
                    self.decisiones[clave] = {"opcion": n + 1, "texto": self.txt(o.get("texto", "")), "mision": ms["def"]["id"]}
                    if o.get("dinero"):
                        self.dar_dinero(int(o["dinero"]), tr("Recibes")) if o["dinero"] > 0 else self.pagar(min(self.j.dinero, -int(o["dinero"])))
                    if o.get("fama"):
                        self.cambiar_reputacion(o["fama"])
                    if o.get("animo"):
                        self.cambiar_animo(o["animo"])
                    if o.get("prestigio"):
                        self.cambiar_ciudadania(o["prestigio"])
                    if o.get("banda"):
                        self.cambiar_rep_banda(o["banda"], o.get("banda_puntos", 0))
                    if o.get("renta"):                           # una consecuencia que dura: dinero cada medianoche, para siempre
                        self.decisiones[clave]["renta"] = int(o["renta"])
                        self.decir(tr('Desde hoy, esto te deja {int} euros cada medianoche.').format(int=(int(o['renta']))) if o["renta"] > 0 else
                                   tr('Desde hoy, esto te cuesta {v} euros cada medianoche.').format(v=(-int(o['renta']))))
                if o.get("dice"):
                    self.decir(self.txt(o["dice"]))
                seguir()
            return f
        self.app.son("notificacion")
        seguir = self._seguir_si(ms)
        menu = ms["pantalla"] = Menu(self.app, self.txt(p.get("pregunta") or tr("¿Qué haces?")),
                    [Opcion(self.txt(o.get("texto", "")), elegir(n, o), ayuda=self.txt(o.get("ayuda", "")) or None) for n, o in enumerate(opciones)],
                    escapable=False, intro=tr("Es una decisión de la historia y no se puede deshacer. F1 explica cada opción"))
        self.app.abrir(menu)

    def _paso_vigilar(self, ms, p, l, x, y, dt):
        """Vigilar un sitio sin que te vean: quedarte cerca un rato y no moverte cuando pasa la ronda."""
        vg = ms.get("vigia")
        if vg is None or l is None:
            return
        j = self.j
        radio = float(p.get("radio", 25))
        d = math.hypot(l.x - x, l.y - y)
        if not vg["dentro"]:
            if d <= radio and (not j.veh or abs(j.veh.vel) < 2):
                vg["dentro"] = True
                if self.gps:
                    self.quitar_gps_auto()
                self.app.son("llegada")
                self.decir(tr('Estás en tu puesto. Quédate a menos de {int} metros durante {int2} segundos y escucha. Cuando oigas pasos que se acercan, quédate quiet[o|a] o agáchate con la X.').format(int=(int(radio)), int2=(int(float(p.get('segundos', 45))))))
            return
        vg["t"] += dt
        if d > radio:
            vg["fuera"] += dt
            vg["t_aviso"] -= dt
            if vg["t_aviso"] <= 0:
                vg["t_aviso"] = 3.0
                self.decir(tr('Te alejas del puesto. Vuelve: está a {int} metros, {direccion_txt}.').format(int=(int(d)), direccion_txt=(self.direccion_txt(l.x, l.y))))
            if vg["fuera"] > 7:
                self.fallar_mision(tr("Has dejado el puesto de vigilancia."))
                return
        else:
            vg["fuera"] = 0.0
        vg["t_suceso"] -= dt
        if vg["t_suceso"] <= 0:                                   # lo que pasa en el sitio vigilado se oye desde él
            vg["t_suceso"] = 6.5
            vg["sucesos"] += 1
            self.son(("puerta_entrar", "puerta_coche", "paso_npc")[vg["sucesos"] % 3], xy=(l.x, l.y), ref=6, maxd=80, vol=1.0)
        r = vg["ronda"]
        if r is None:
            vg["t_ronda"] -= dt
            if vg["t_ronda"] <= 0:
                vg["rondas"] += 1
                vg["ronda"] = {"t": 0.0, "x": l.x, "y": l.y, "t_paso": 0.0}
                self.son("buscando", cat="interfaz", vol=0.5)
                if vg["rondas"] == 1:
                    self.decir(tr("Sale alguien a dar una vuelta. Quédate quiet[o|a] o agáchate hasta que se vaya."))
        else:
            r["t"] += dt
            f = min(1.0, r["t"] / 4.0) if r["t"] < 7.0 else max(0.0, 1.0 - (r["t"] - 7.0) / 3.0)     # se acerca, se para y se va
            dx, dy = x - l.x, y - l.y
            k = f * max(0.0, 1.0 - 5.0 / max(5.0, math.hypot(dx, dy)))                              # se queda a cinco metros de ti
            r["x"], r["y"] = l.x + dx * k, l.y + dy * k
            r["t_paso"] -= dt
            if r["t_paso"] <= 0:
                r["t_paso"] = 0.6
                self.son("paso_npc", xy=(r["x"], r["y"]), ref=3, maxd=45, vol=1.0)
            cerca = math.hypot(r["x"] - x, r["y"] - y) < 12
            t = self.app.teclas
            moviendote = (abs(j.veh.vel) > 1.0) if j.veh else (not j.agachado and any(k2 in t for k2 in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)))
            vg["visto"] = vg["visto"] + dt if cerca and moviendote else 0.0
            if vg["visto"] > 0.6:
                self.son("grito", xy=(r["x"], r["y"]), vol=0.6)
                self.fallar_mision(tr("Te han visto moverte."))
                return
            if r["t"] >= 10.0:
                vg["ronda"] = None
                vg["t_ronda"] = 11.0
        if vg["t"] >= float(p.get("segundos", 45)):
            if p.get("resultado"):
                self.decir(self.txt(p["resultado"]))
            self._paso_hecho()


    def _parar_rivales(self, ms):
        for r in (ms.get("carrera") or {}).get("rivales", []):
            if r.get("canal") is not None:
                r["canal"].parar()
                r["canal"] = None

    def _carrera_puesto_txt(self, ca):
        orden = ("primer[o|a]", "segund[o|a]", "tercer[o|a]", "cuart[o|a]", "quint[o|a]")
        return tr('Vas {v} de {v2}.').format(v=(orden[max(0, min(ca['puesto'], 4))]), v2=(len(ca['rivales']) + 1))

    def _carrera_punto_en(self, ca, s):
        """El punto del recorrido que está a s metros de la salida."""
        pts, cum = ca["pts"], ca["cum"]
        s = max(0.0, min(s, cum[-1]))
        for n in range(1, len(pts)):
            if s <= cum[n] or n == len(pts) - 1:
                tramo = cum[n] - cum[n - 1]
                f = (s - cum[n - 1]) / tramo if tramo > 0 else 0.0
                return pts[n - 1][0] + (pts[n][0] - pts[n - 1][0]) * f, pts[n - 1][1] + (pts[n][1] - pts[n - 1][1]) * f
        return pts[-1]

    def _paso_carrera(self, ms, p, l, x, y, dt):
        """Carrera con rivales: llegar al último punto antes que ellos. Se les oye el motor desde donde van."""
        ca = ms.get("carrera")
        if ca is None or l is None:
            return
        j = self.j
        puntos = [self.lugares.get(q) for q in p.get("puntos", [])]
        puntos = [q for q in puntos if q is not None]
        if not puntos:
            self._paso_hecho()
            return
        if ca["fase"] == "ir":
            if math.hypot(l.x - x, l.y - y) <= 17:
                if not j.veh:
                    if "sin_coche" not in ms["avisos"]:
                        ms["avisos"].add("sin_coche")
                        self.decir(tr("Estás en la salida, pero para correr necesitas un vehículo. Consigue uno y vuelve."))
                elif abs(j.veh.vel) < 3:
                    pts = [(l.x, l.y)]
                    marcas = []                                    # a cuántos metros de la salida queda cada punto de control
                    largo = 0.0
                    for q in puntos:
                        for pt in self.mundo.ruta(pts[-1][0], pts[-1][1], q.x, q.y):
                            largo += math.hypot(pt[0] - pts[-1][0], pt[1] - pts[-1][1])
                            pts.append((float(pt[0]), float(pt[1])))
                        marcas.append(largo)
                    rectos, antes = [], (l.x, l.y)                 # la distancia en línea recta de cada tramo, para saber cuánto llevas
                    for q in puntos:
                        rectos.append(max(1.0, math.hypot(q.x - antes[0], q.y - antes[1])))
                        antes = (q.x, q.y)
                    cum = [0.0]
                    for n in range(1, len(pts)):
                        cum.append(cum[-1] + math.hypot(pts[n][0] - pts[n - 1][0], pts[n][1] - pts[n - 1][1]))
                    n_riv = max(1, min(4, int(p.get("rivales", 2))))
                    base = float(p.get("velocidad", 10))
                    ca.update({"fase": "cuenta", "t": 3.0, "pts": pts, "cum": cum, "marcas": marcas, "rectos": rectos, "puesto": -1,
                               "rivales": [{"s": 5.0 + 5.0 * k, "vel": base * (1.0 - 0.07 * k), "nombre": G.lista("rivales_carrera")[k % len(G.lista("rivales_carrera"))], "canal": None, "k": k} for k in range(n_riv)]})
                    if self.gps:
                        self.quitar_gps_auto()
                    self.app.son("reloj", cat="interfaz")
                    self.decir(tr('En la salida, con {n_riv} {v}. Son {len} puntos. Preparad[o|a].').format(n_riv=(n_riv), v=(tr('rival') if n_riv == 1 else tr('rivales')), len=(len(puntos))))
            return
        if ca["fase"] == "cuenta":
            antes = ca["t"]
            ca["t"] -= dt
            if int(antes) != int(ca["t"]) and ca["t"] > 0:
                self.app.son("reloj", cat="interfaz")
            if ca["t"] <= 0:
                ca["fase"] = "corre"
                ca["t"] = 0.0
                self.son("claxon", vol=0.6)
                for r in ca["rivales"]:
                    rx, ry = self._carrera_punto_en(ca, r["s"])
                    r["canal"] = self.son("motor_coche", bucle=True, xy=(rx, ry), ref=8, maxd=110, vol=0.8, tono=1.0 + 0.08 * r["k"])
                self.decir(tr("¡Ya!"), True)
                self._ruta_siguiente(p, primero=True)
            return
        # en carrera
        ca["t"] += dt
        i = min(ms.get("ruta_i", 0), len(puntos) - 1)
        punto = puntos[i]
        d = math.hypot(punto.x - x, punto.y - y)
        if punto.mapa == self.mundo.id and d <= 20:
            ms["ruta_i"] = i + 1
            if ms["ruta_i"] >= len(puntos):
                self._parar_rivales(ms)
                self.decir(tr("¡Has ganado la carrera!"))
                self._paso_hecho()
                return
            self.app.son("llegada")
            self._ruta_siguiente(p)
            i, punto = ms["ruta_i"], puntos[ms["ruta_i"]]
            d = math.hypot(punto.x - x, punto.y - y)
        previo = ca["marcas"][i - 1] if i else 0.0                               # cuánto llevas recorrido, más o menos
        mio = previo + (ca["marcas"][i] - previo) * max(0.0, 1.0 - d / ca["rectos"][i])
        delante = 0
        for r in ca["rivales"]:
            r["s"] += r["vel"] * (1.0 + 0.1 * math.sin(ca["t"] * 0.35 + 2.0 * r["k"])) * dt
            rx, ry = self._carrera_punto_en(ca, r["s"])
            if r["canal"] is not None:
                r["canal"].mover(rx, ry)
            if r["s"] >= ca["cum"][-1]:
                self._parar_rivales(ms)
                self.fallar_mision(tr('Ha ganado {nombre}.').format(nombre=(r['nombre'])))
                return
            if r["s"] > mio:
                delante += 1
        if delante != ca["puesto"]:
            ca["puesto"] = delante
            self.decir(self._carrera_puesto_txt(ca))

    def _paso_hecho(self):
        if self.gps:
            self.quitar_gps_auto()
        self.app.son("llegada")
        self._siguiente_paso()

    # ------------------------------------------------- cajas que tardan en abrirse
    @staticmethod
    def _num_paso(p, clave):
        try:
            return max(0.0, float(p.get(clave) or 0))
        except (TypeError, ValueError):
            return 0.0

    def _segundos_recoger(self, p):
        return self._num_paso(p, "tarda") if p.get("tipo") == "recoger" else 0.0

    def mision_abrir(self, o):
        """Intro sobre el objeto de la misión. Si el paso dice que tarda en abrirse (una caja fuerte, una cámara), no se
        coge al momento: empieza a abrirse y hay que quedarse al lado. True si este objeto es de los que tardan."""
        ms = self.mision
        if not ms or ms.get("objeto") is not o or not (0 <= ms["paso"] < len(ms["def"]["pasos"])):
            return False
        p = ms["def"]["pasos"][ms["paso"]]
        total = self._segundos_recoger(p)
        if total <= 0 or ms.get("abierto"):
            return False
        if ms.get("abriendo"):
            ab = ms["abriendo"]
            self.decir(tr('Se está abriendo: faltan unos {max} segundos. No te apartes.').format(max=(max(1, int(ab['total'] - ab['t'])))), True)
            return True
        self._empezar_a_abrir(ms, p, total)
        return True

    def _empezar_a_abrir(self, ms, p, total):
        g = self.golpe_caja() if getattr(self, "golpe", None) else None
        total = total * (g["factor"] if g else 1.0)
        ms["abriendo"] = {"t": 0.0, "total": total, "canal": None, "pausa": False, "mitad": False}
        solo = self.golpe_caja_evento("empieza", total) if g else False
        if not solo:
            self.decir(tr('Empiezas a abrir: {txt}. Tardará unos {int} segundos. Quédate al lado; si te apartas, se para.').format(txt=(self.txt(p['objeto'])), int=(int(round(total)))), True)

    def _paso_abrir(self, ms, p, dt):
        """La caja se va abriendo mientras estés al lado (o, en un golpe, mientras cubras a quien la abre)."""
        o = ms.get("objeto")
        total = self._segundos_recoger(p)
        if o is None or total <= 0:
            return
        g = self.golpe_caja() if getattr(self, "golpe", None) else None
        ab = ms.get("abriendo")
        if ab is None:
            if g and g["solo"] and o.dist(*self.pos()) <= g["radio"]:      # la abre uno de los tuyos: no hace falta tocarla
                self._empezar_a_abrir(ms, p, total)
            return
        cerca = o.dist(*self.pos()) <= (g["radio"] if g else 5.0) and self.j.veh is None
        if not cerca:
            if not ab["pausa"]:
                ab["pausa"] = True
                if ab["canal"] is not None:
                    ab["canal"].parar()
                    ab["canal"] = None
                if not (g and self.golpe_caja_evento("pausa")):
                    self.decir(tr("Te has apartado y la caja deja de abrirse. Vuelve junto a ella."))
            return
        if ab["pausa"]:
            ab["pausa"] = False
            self.decir(tr("Sigue abriéndose."))
        if ab["canal"] is None:
            ab["canal"] = self.son("ganzua", bucle=True, xy=(o.x, o.y), ref=6, maxd=40, vol=0.7)
        ab["t"] += dt
        f = min(1.0, ab["t"] / ab["total"])
        ab["canal"].tono(0.8 + 0.6 * f)                           # se oye avanzar: cada vez más agudo
        if not ab["mitad"] and f >= 0.5:
            ab["mitad"] = True
            if not (g and self.golpe_caja_evento("mitad")):
                self.decir(tr("Va por la mitad."))
        if f >= 1.0:
            ab["canal"].parar()
            ms["abriendo"] = None
            ms["abierto"] = True
            if g:
                self.golpe_caja_evento("hecho")
            self.recoger(o)

    # ------------------------------------------------------------------- final
    def _limpiar_mision(self):
        ms = self.mision
        if not ms:
            return
        if (ms.get("abriendo") or {}).get("canal") is not None:
            ms["abriendo"]["canal"].parar()
        if getattr(self, "golpe", None):                         # el golpe preparado se deshace con la misión
            self.golpe_fin(False)
        v = ms.get("veh")
        if v is not None and not v.muerto and not ms.get("veh_tuyo"):      # si la hacías con el tuyo, el tuyo se queda
            if self.j.veh is v:
                self.salir_vehiculo(forzado=True)
            self.quitar_vehiculo(v)
        vo = ms.get("veh_objetivo")
        if vo is not None and not vo.muerto:
            self.quitar_vehiculo(vo)
        self._parar_rivales(ms)
        self._cerrar_escena(ms)
        for e in ms["enemigos"]:
            if e in self.personas:
                self.personas.remove(e)
        for ve in ms.get("veh_enemigos", []):                    # los vehículos en los que venían, si aún no se habían bajado
            if not ve.muerto and not ve.desplegado:
                self.quitar_vehiculo(ve)
        o = ms.get("objeto")
        if o is not None and o in self.objetos:
            if o.canal:
                o.canal.parar()
            self.objetos.remove(o)
        if self.gps:
            self.quitar_gps_auto(fin=True)
        self.objetivo = None
        self.mision = None

    def _completar_mision(self):
        ms = self.mision
        m = ms["def"]
        antes = {x["id"] for x in self.misiones_disponibles()}
        self.mision = None
        if self.gps and not self.trabajo:      # si sigues trabajando (el tutorial de los trabajos), el destino es el del trabajo
            self.quitar_gps_auto(fin=True)
        if ms.get("repeticion"):                               # repetir una misión ya hecha es por gusto: no cambia nada
            self.app.son("mision_ok")
            self.decir(tr('Has repetido {titulo}.').format(titulo=(m['titulo'])))
            return
        self.fallos.pop(m["id"], None)
        self.sv_mision_ok(m)
        self.sv_mision_fin(True, m)
        if m.get("territorio") and m["territorio"] not in self.j.territorios:
            self.j.territorios.append(m["territorio"])
            self.j.barrios_banda.pop(m["territorio"], None)
            self.son("territorio", cat="interfaz")
            self.decir(tr('El barrio es tuyo. Te pagará {precio} euros cada medianoche.').format(precio=(self.precio('tributo_territorio', 300))))
            # quedarse con un barrio se sabe en toda la ciudad: el primero da mucha fama; los siguientes, cada vez menos
            self.cambiar_reputacion(max(3, 15 - 3 * (len(self.j.territorios) - 1)))
        if callable(m.get("al_completar")):
            m["al_completar"]()
        if m.get("repetible"):
            if m.get("contador"):
                self.j.stats[m["contador"]] = self.j.stats.get(m["contador"], 0) + 1
                if m["contador"] == "contratos" and m.get("lugar"):       # y los de cada tablón, para las misiones que piden contratos de un sitio (issue 33)
                    por_tablon = self.j.stats.get("contratos_tablon")
                    if not isinstance(por_tablon, dict):
                        por_tablon = self.j.stats["contratos_tablon"] = {}
                    por_tablon[m["lugar"]] = int(por_tablon.get(m["lugar"], 0)) + 1
                if m["contador"] in ("contratos", "atracos", "conquistas", "encargos"):
                    self.hon_negro(int((m.get("recompensa") or {}).get("dinero", 0)))      # dinero que no podrías justificar
        else:
            self.completadas.append(m["id"])
            self.j.stats["misiones"] += 1
        r = m.get("recompensa", {})
        self.app.son("mision_ok")
        txt = f"{tr('Encargo cumplido') if m.get('repetible') else tr('Misión completada')}: {m['titulo']}."
        if r.get("dinero"):
            paga = int(r["dinero"] * (0.5 if self.cfg["mod_dinero"] else 1.0))
            self.j.dinero += paga
            self.j.stats["dinero_ganado"] += paga
            txt += tr(' Recompensa: {paga} euros.').format(paga=(paga))
        self.decir(txt)
        if r.get("arma"):
            self.dar_arma(r["arma"], r.get("balas", 0))
        self.cambiar_animo(4 if m.get("repetible") else 8)
        if m.get("honrada"):                                     # el buen camino da prestigio entre los vecinos, no fama en la calle
            self.hon_mision_completada(m)
        else:
            self.cambiar_reputacion(1 if m.get("repetible") else 2)
        for pid, n in (r.get("afinidad") or {}).items():
            if self.persona_social(pid):
                self.sumar_afinidad(pid, n)
        if r.get("chaleco"):
            self.j.blindaje = 100.0
            self.decir(tr("Te pones un chaleco antibalas."))
        if r.get("barco"):
            b = r["barco"]
            mo = self.modelos.get(b["modelo"])
            e = self.lug(b.get("en"))
            if mo and e:
                self.j.barcos.append({"modelo": mo["id"], "nombre": mo["nombre"], "salud": mo["salud"], "en": e.id})
                self.decir(tr('Ahora es tuyo: {nombre}. Está amarrado en {nombre_lugar}.').format(nombre=(mo['nombre']), nombre_lugar=(self.nombre_lugar(e))))
        if m.get("final") and not m.get("repetible"):          # esta misión cierra la historia de una manera
            self.decisiones["_final"] = {"opcion": 0, "texto": self.txt(m.get("final_titulo") or m["titulo"]), "mision": m["id"]}
            self.app.son("logro" if "logro" in self.mez.sonidos else "mision_ok")
            self.decir(tr("Final de la historia. ") + self.txt(m["final"]))
        nuevas = [x for x in self.misiones_disponibles() if x["id"] not in antes]
        if len(nuevas) > 3:
            self.decir(tr('Hay {len} misiones nuevas disponibles, algunas en otras localidades. Míralas en el móvil con M.').format(len=(len(nuevas))))
        else:
            for x in nuevas:
                self.decir(tr('Nueva misión disponible: {titulo}, en {nombre_lugar}. Abre el móvil con M para marcarla en el GPS.').format(titulo=(x['titulo']), nombre_lugar=(self.nombre_lugar(self.lugares[x['lugar']]))))
        from . import menus_juego
        menus_juego.autoguardar(self)

    def _rebobinar_jugador(self, copia):
        """Devuelve al jugador a como estaba al empezar la misión (o en el punto de control), menos sus vehículos. Los
        vehículos no vuelven atrás: los de la calle nunca lo han hecho, así que los garajes y los barcos amarrados tampoco.
        Si no, el que sacaste del garaje durante la misión quedaba duplicado (en el garaje y en la calle), y el que
        mandaste al garaje con la misión ya empezada se perdía: ni en la calle ni en el garaje. Lo mismo un barco tuyo
        que amarraste, o con el que zarpaste, durante la misión."""
        j = self.j
        stats = dict(j.stats)
        garajes, barcos, barco_actual = j.garajes, j.barcos, j.barco_actual
        antecedentes = j.antecedentes                            # una detención es una detención: lo que consta en tu ficha no se borra al reintentar
        j.de_dict(copy.deepcopy(copia))
        j.stats.update({k: stats[k] for k in ("muertes", "detenciones", "tiempo", "antecedentes") if k in stats})
        j.antecedentes = antecedentes
        j.garajes, j.barcos, j.barco_actual = garajes, barcos, barco_actual
        for pid in [k for k, fichas in garajes.items() if fichas and k not in j.propiedades]:
            casa_perdida = self.lug(pid)
            for ficha in list(garajes[pid]):                     # la casa la compraste durante la misión y vuelve a no ser tuya
                casa = self.garaje_con_sitio()
                garajes[pid].remove(ficha)
                if casa is not None:
                    garajes.setdefault(casa.id, []).append(ficha)
                else:                                            # sin sitio en ningún garaje: a la calle, a tu nombre, delante de esa casa
                    self.ficha_a_la_calle(ficha, casa_perdida)
            garajes.pop(pid, None)

    def fallar_mision(self, motivo):
        ms = self.mision
        if not ms:
            return
        m = ms["def"]
        copia = ms["copia"]
        reloj, dia = ms["reloj"], ms["dia"]
        control = ms.get("control")
        repeticion = bool(ms.get("repeticion"))
        self._limpiar_mision()
        self.sv_mision_fin(False)
        self.app.son("mision_fallo")
        if not repeticion:
            self.fallos[m["id"]] = self.fallos.get(m["id"], 0) + 1

        def saltar():
            self.app.cerrar(menu)
            antes = {x["id"] for x in self.misiones_disponibles()}
            self.completadas.append(m["id"])
            self.saltadas.append(m["id"])
            self.fallos.pop(m["id"], None)
            self.app.son("notificacion")
            self.decir(tr('Te saltas {titulo}. Cuenta como hecha, sin recompensa. Puedes repetirla cuando quieras desde el diario del móvil.').format(titulo=(m['titulo'])))
            for x in [x for x in self.misiones_disponibles() if x["id"] not in antes][:3]:
                self.decir(tr('Nueva misión disponible: {titulo}, en {nombre_lugar}.').format(titulo=(x['titulo']), nombre_lugar=(self.nombre_lugar(self.lugares[x['lugar']]))))
            from . import menus_juego
            menus_juego.autoguardar(self)

        def desde_control():
            self.app.cerrar(menu)
            lleva = self.preparar_traslado(control["mapa"])      # antes de rebobinar: el vehículo que llevas va contigo
            self._rebobinar_jugador(control["copia"])
            self.reloj, self.dia = control["reloj"], control["dia"]
            self._fin_persecucion()
            self.llevarte_a(control["mapa"], control["x"], control["y"], lleva)      # si no puede ir, el tuyo se queda donde estaba
            if self.trabajo:
                self.terminar_trabajo("")
            self.cancelar_gps()
            self.mision = {"def": m, "paso": control["paso"] - 1, "veh": None, "enemigos": [], "objeto": None, "limite": None, "repeticion": repeticion,
                           "copia": copia, "reloj": reloj, "dia": dia, "generado": False, "recogido": False, "restos": None,
                           "avisos": set(), "quedan": None, "control": control, "reanudando": True}
            self.app.son("notificacion")
            self.decir(tr('Vuelves al último punto de control de {titulo}.').format(titulo=(m['titulo'])), True)
            self._siguiente_paso()

        def reintentar():
            self.app.cerrar(menu)
            l = self.lugares[m["lugar"]]
            lleva = self.preparar_traslado(l.mapa)               # antes de rebobinar: el vehículo que llevas va contigo
            self._rebobinar_jugador(copia)
            self.reloj, self.dia = reloj, dia
            self._fin_persecucion()
            self.llevarte_a(l.mapa, l.x, l.y, lleva)             # y queda aparcado a tu lado
            self.iniciar_mision(m, True, repeticion)
            self.decir(self.vehiculos_tras_reintento_txt())

        def abandonar():
            self.app.cerrar(menu)
            self.decir(tr("Misión abandonada. Puedes volver a intentarla cuando quieras desde el mismo lugar."))

        extra = [Opcion(tr("Reintentar desde el último punto de control"), desde_control,
                        ayuda=tr("Vuelves al momento en que empezó el último tramo que habías alcanzado, con lo que tenías entonces. No repites lo anterior."))] if control else []
        if not repeticion and not m.get("repetible") and self.fallos.get(m["id"], 0) >= 3:
            extra.append(Opcion(tr("Saltarte esta misión"), saltar,
                                ayuda=tr("La has fallado tres veces o más. Si te la saltas, cuenta como hecha y la historia sigue, pero no cobras la recompensa. Luego puedes repetirla desde el diario del móvil.")))
        menu = Menu(self.app, tr('Misión fallida: {titulo}. {motivo}').format(titulo=(m['titulo']), motivo=(motivo)),
                    extra + [Opcion(tr("Reintentar desde el principio de la misión"), reintentar, ayuda=tr("Vuelves al lugar donde empieza la misión, con el dinero, la salud y las armas que tenías al aceptarla.")),
                     Opcion(tr("Dejarlo por ahora"), abandonar, ayuda=tr("Sigues jugando sin la misión. Queda pendiente: puedes volver a intentarla cuando quieras desde el mismo lugar."))], escapable=False)
        self.app.abrir(menu)

    def abandonar_mision(self):
        if not self.mision:
            return
        self._limpiar_mision()
        self.sv_mision_fin(False)
        self.decir(tr("Misión abandonada."), True)
