"""Golpes preparados: cada uno de tu banda con su papel (1.7.1).

Un atraco de los de siempre (un banco, un local con caja, un proveedor) se puede preparar antes si tienes a gente de tu
banda al lado: uno espera fuera con el motor en marcha, otro vigila y avisa de la policía, otro entra contigo y tiene a
raya a la gente, otro abre la caja y otro dispara desde el coche en la huida. Tú eliges también lo tuyo: abrir la caja
o cubrir a quien la abre, y conducir o ir de pasajero.

Preparado, el golpe tiene cinco fases que se dicen en voz alta (entrada, control, caja, salida y huida), la caja tarda
en abrirse y tu gente habla por la radio. Cada uno rinde según lo que vale (puntería, conducción, nervios y lealtad,
que se guardan con la partida), puede fallar y se lleva su parte del botín.

Nada de esto es obligatorio: sin banda, o sin prepararlo, el atraco es el de siempre.

Los papeles, los números y las frases están en los datos (vida.json, secciones «golpes» y «papeles_golpe»).
"""
from .i18n import tr
import math
import random

from . import gente as G
from .ajustes import Ajustes
from .entidades import Persona

AJ = Ajustes("golpes", {
    "radio_presentes": 80, "radio_vehiculo": 200,
    "atributo_min": 30, "atributo_max": 85, "exp_bono": 3, "exp_max": 5,
    "caja_min": 8, "caja_max": 16, "caja_radio": 5, "cubrir_radio": 25, "caja_ayuda": 50, "caja_nervios": 40,
    "vigilante_retraso": 22, "vigilante_aviso": 8,
    "conductor_ventaja": 12, "conductor_nivel": 70,
    "tirador_cada": 2.6, "tirador_alcance": 48, "tirador_dano": 20,
    "heroe_prob": 30, "heroe_escolta": 85, "alarma_prob": 30, "alarma_escolta": 80,
    "fallo_base": 30, "herido_prob": 18, "herido_dias_min": 2, "herido_dias_max": 5, "detenido_prob": 25,
    "delata_lealtad": 40, "delata_busqueda": 1, "tarde_min": 10, "tarde_max": 25,
    "reparto_tope": 60, "lealtad_exito": 3, "lealtad_fracaso": 6,
    "charla_lealtad": 2, "invitar_precio": 30, "invitar_lealtad": 4, "paga_precio": 150, "paga_lealtad": 8,
}, {
    "frases_charla_banda": [tr("{nombre} te cuenta que su madre quiere que deje esto y se saque el carné de camión. Se ríe, pero no del todo."), tr("{nombre} te pregunta si de verdad te fías de todos los de la banda. Dice que de ti, sí."), tr("Habláis de fútbol. {nombre} es del equipo que siempre pierde, y lo defiende como si le fuera la vida."), tr("{nombre} te enseña una foto de cuando era crío, en la playa del puerto. Nadie diría que es la misma persona."), tr("{nombre} dice que está ahorrando para irse un año fuera cuando esto se calme. No dice adónde."), tr("{nombre} te cuenta, bajando la voz, que el último golpe le quitó el sueño dos noches."),
                            tr("{nombre} te mira y se ríe: «Cuando digo en el barrio que trabajo para {alias}, la gente se aparta.»"),
                            tr("«Tú eres {alias}», te dice {nombre}, «y eso aquí pesa más que cualquier pistola.»")],
    "frases_invitar_banda": [tr("Invitas a {nombre} a una cerveza en la barra. Acaba siendo una ronda, y luego otra."), tr("Le pagas a {nombre} un bocadillo y un café. Dice que así da gusto currar contigo.")],
    "frases_paga_banda": [tr("Le das a {nombre} {euros} euros, aparte de su parte. No dice nada, pero se le nota."), tr("{nombre} se guarda los {euros} euros sin contarlos: «Esto no se me olvida».")],
    "frases_echar_banda": [tr("{nombre} recoge sus cosas y se va sin mirar atrás. Ya no es de la banda."), tr("«Tú sabrás», dice {nombre}. Deja la banda y se pierde calle abajo.")],
    "tiempos_caja": ["banco=26", "proveedor=14", "casino=20", "empenos=14", "armeria=14", "concesionario=16", "hotel=14"],
    "frases_entrada": [tr("Fase uno, entrada. Cada uno a su sitio."), tr("Fase uno, entrada. Relojes en hora: empezamos.")],
    "frases_control": [tr("Fase dos, control. Que nadie se mueva hasta que no quede guardia en pie."), tr("Fase dos, control. Primero, los que van armados.")],
    "frases_control_sin_guardia": [tr("Fase dos, control. Aquí no hay guardia: todo el mundo al suelo y nadie se hace el valiente."),
                                   tr("Fase dos, control. Sin guardia a la vista: la gente, quieta y callada.")],
    "frases_caja": [tr("Fase tres, la caja."), tr("Fase tres: a por la caja.")],
    "frases_salida": [tr("Fase cuatro, salida. Fuera de aquí con lo que llevas."), tr("Fase cuatro, salida. Ya lo tienes: a la calle.")],
    "frases_huida": [tr("Fase cinco, huida. Despista a la policía y el botín es vuestro."), tr("Fase cinco, huida. Ahora toca desaparecer.")],
    "radio_conductor_listo": [tr("En la puerta, con el motor en marcha."), tr("Aparcado delante y sin apagar el motor. Cuando salgáis, arranco.")],
    "radio_conductor_tarde": [tr("Voy con retraso, hay un atasco. Aguantad un poco."), tr("Me he tenido que dar una vuelta: había una patrulla. Llego enseguida.")],
    "radio_conductor_llega": [tr("Ya estoy en la puerta. ¡Vamos, vamos!"), tr("Aquí estoy. Subid ya.")],
    "radio_conductor_ventaja": [tr("Agárrate: me sé un callejón por el que no nos sigue nadie."), tr("Salgo por detrás del mercado. Ahí nos pierden.")],
    "radio_conductor_sin_ventaja": [tr("Se me ha calado. Ya está, ya arranca. Hemos perdido la ventaja."), tr("Me tiemblan las manos. Salimos, pero nos han visto salir.")],
    "radio_conductor_tu": [tr("El motor está en marcha. Conduces tú: yo voy mirando atrás."), tr("Todo tuyo, ya está arrancado. Yo te canto por dónde vienen.")],
    "radio_vigilante_listo": [tr("En mi sitio. Desde aquí veo las dos esquinas."), tr("Colocado. Si viene alguien, os enteráis antes que ellos.")],
    "radio_vigilante_alarma": [tr("Ha saltado la alarma. Calculo {segundos} segundos hasta que lleguen."), tr("Los han avisado. Tenéis unos {segundos} segundos, ni uno más.")],
    "radio_vigilante_cerca": [tr("¡Ya se oyen las sirenas! Os quedan {segundos} segundos."), tr("Vienen por la avenida. {segundos} segundos y los tenéis encima.")],
    "radio_vigilante_llegan": [tr("¡Ya están aquí! Me quito de en medio."), tr("¡Policía en la puerta! Salid como podáis.")],
    "radio_vigilante_falla": [tr("No... no he visto venir nada. ¡Los tenéis encima!"), tr("Se me ha pasado. ¡Están ahí mismo!")],
    "frases_vigilante_detenido": [tr("A {nombre} lo han cogido en la esquina: se lo llevan esposado."), tr("{nombre} no ha corrido lo bastante: la policía lo tiene.")],
    "frases_delata": [tr("{nombre} no ha aguantado ni el primer interrogatorio: ha dado tu nombre."), tr("{nombre} ha cantado para salvarse. La policía sabe quién ha sido.")],
    "frases_no_delata": [tr("{nombre} no ha dicho ni una palabra. De esos quedan pocos."), tr("{nombre} se come el marrón sin dar un solo nombre.")],
    "radio_escolta_control": [tr("Yo me ocupo de la gente. Tú a lo tuyo."), tr("Los tengo a todos contra la pared. Nadie se mueve.")],
    "radio_escolta_heroe": [tr("Uno quería hacerse el héroe. Ya no quiere."), tr("Quieto ahí. Le he quitado las ganas a uno que iba a por ti.")],
    "radio_escolta_alarma": [tr("Una mano iba hacia el botón de la alarma. No ha llegado."), tr("Casi pulsan la alarma. Casi.")],
    "frases_escolta_herido": [tr("¡A {nombre} le han dado! Se arrastra hacia la puerta: está fuera del golpe."), tr("{nombre} cae herido y sale como puede. No cuentes con él para lo que queda.")],
    "frases_heroe": [tr("¡Uno de los que estaban en el suelo se levanta y va a por ti!"), tr("¡Cuidado! Alguien ha sacado un arma de debajo del mostrador.")],
    "frases_alarma": [tr("¡Alguien ha pulsado la alarma antes de tiempo!"), tr("Se oye un timbre al fondo: han dado la alarma mientras abrías.")],
    "radio_caja_empieza": [tr("Me pongo con ella. Dame {segundos} segundos."), tr("Esta la conozco. {segundos} segundos y es nuestra.")],
    "radio_caja_ayuda": [tr("Yo sujeto, tú gira. Así va más deprisa."), tr("Déjame la cerradura a mí, tú vigila la puerta de la cámara.")],
    "radio_caja_mitad": [tr("Va por la mitad."), tr("Ya cede. Un poco más.")],
    "radio_caja_hecho": [tr("¡Abierta!"), tr("¡Ya está! Todo dentro de la bolsa.")],
    "radio_caja_nervios": [tr("No... no atino. Me sudan las manos. Va a tardar más."), tr("Se me ha partido la ganzúa. Empiezo otra vez.")],
    "radio_caja_solo": [tr("Si no me cubres, no sigo. Vuelve aquí."), tr("No abro con la espalda al aire. Acércate.")],
    "radio_tirador_dispara": [tr("¡Los tengo detrás! Disparo."), tr("Baja la ventanilla, que les voy a dar.")],
    "radio_tirador_acierta": [tr("¡Le he dado!"), tr("¡Ese ya no nos sigue igual!"), tr("¡Tocado!")],
    "frases_reparto": [tr("Reparto: {partes}. Para ti quedan {neto} euros de {botin}."), tr("Cada uno lo suyo: {partes}. A ti te quedan {neto} de los {botin} euros.")],
    "frases_se_va": [tr("{nombre} se harta de golpes que salen mal y deja la banda."), tr("{nombre} dice que contigo solo se gana cárcel, y se va.")],
    "vehiculos": [],
}, cero=("caja_ayuda", "caja_nervios", "vigilante_retraso", "vigilante_aviso", "conductor_ventaja", "conductor_nivel", "heroe_prob", "heroe_escolta", "alarma_prob",
         "alarma_escolta", "fallo_base", "herido_prob", "detenido_prob", "delata_lealtad", "delata_busqueda", "reparto_tope", "lealtad_exito", "lealtad_fracaso",
         "exp_bono", "exp_max", "tirador_dano"))

EFECTOS = ("conductor", "vigilante", "escolta", "caja", "tirador")
ATRIBUTOS = {"punteria": tr("puntería"), "conduccion": tr("conducción"), "nervios": tr("nervios"), "lealtad": tr("lealtad")}
# Los papeles de serie; los datos (vida.json, papeles_golpe) pueden cambiarlos, quitarlos o añadir otros con los mismos efectos.
PAPELES_SERIE = [
    {"id": "conductor", "nombre": tr("Conductor"), "efecto": "conductor", "atributo": "conduccion", "parte": 10,
     "desc": tr("Espera fuera, con el motor en marcha, en el vehículo que elijas. Al salir subes de pasajero, o al volante con el coche ya arrancado, y la huida empieza con ventaja.")},
    {"id": "vigilante", "nombre": tr("Vigilante"), "efecto": "vigilante", "atributo": "nervios", "parte": 8,
     "desc": tr("Se queda fuera. Cuando salta la alarma, entretiene a la policía un rato y te va diciendo por la radio cuánto falta para que llegue.")},
    {"id": "escolta", "nombre": tr("Escolta dentro"), "efecto": "escolta", "atributo": "punteria", "parte": 8,
     "desc": tr("Entra contigo y tiene a raya a la gente y a los guardias: es mucho más difícil que alguien se haga el héroe o pulse la alarma antes de tiempo.")},
    {"id": "caja", "nombre": tr("El de la caja"), "efecto": "caja", "atributo": "nervios", "parte": 10,
     "desc": tr("Sabe de cerraduras: contigo, la caja se abre bastante antes; y si eliges cubrirle, la abre él mientras tú vigilas.")},
    {"id": "tirador", "nombre": tr("Tirador"), "efecto": "tirador", "atributo": "punteria", "parte": 8,
     "desc": tr("Va en el vehículo de la huida y dispara por la ventanilla a los que os persiguen.")},
]
PAPELES = [dict(x) for x in PAPELES_SERIE]


def configurar(datos):
    """Los papeles de los datos. Uno sin efecto conocido no vale; sin ninguno válido, los de serie."""
    lista = []
    for x in datos.get("papeles_golpe", []) or []:
        if not isinstance(x, dict) or x.get("efecto") not in EFECTOS or not str(x.get("id") or "").strip():
            continue
        try:
            lista.append({"id": str(x["id"]), "nombre": str(x.get("nombre") or x["id"]), "efecto": x["efecto"],
                          "atributo": x.get("atributo") if x.get("atributo") in ATRIBUTOS else "nervios",
                          "parte": max(0.0, min(100.0, float(x.get("parte", 0) or 0))), "desc": str(x.get("desc") or "")})
        except (TypeError, ValueError):
            continue
    PAPELES[:] = lista or [dict(x) for x in PAPELES_SERIE]


def papel(ident):
    return next((x for x in PAPELES if x["id"] == ident), None)


def _tiempo_caja(tipo):
    for linea in AJ.lista("tiempos_caja"):
        k, _, v = linea.partition("=")
        if k.strip() == tipo:
            try:
                return max(1.0, float(v))
            except ValueError:
                break
    return AJ.entre("caja_min", "caja_max")


def _lista_txt(cosas):
    cosas = list(cosas)
    return cosas[0] if len(cosas) == 1 else ", ".join(cosas[:-1]) + tr(" y ") + cosas[-1] if cosas else ""


class Golpes:
    """Mixin de Partida."""

    def golpes_iniciar(self):
        self.golpe = None

    # ------------------------------------------------------------------ la gente de tu banda, uno por uno
    def _ficha_banda(self, nombre=None, genero=None, nervios=None, lealtad=None):
        a, b = sorted((AJ.entero("atributo_min"), AJ.entero("atributo_max")))
        j = self.j
        genero = genero or random.choice("hm")
        usados = {f.get("n") for f in j.banda_gente if isinstance(f, dict)}
        if not nombre:
            libres = [n for n in G.nombres(genero) if n not in usados] or list(G.nombres(genero))
            nombre = random.choice(libres)
        return {"id": max([int(f.get("id", 0)) for f in j.banda_gente if isinstance(f, dict)] or [0]) + 1, "n": nombre, "g": genero,
                "punteria": random.randint(a, b), "conduccion": random.randint(a, b),
                "nervios": int(nervios) if nervios is not None else random.randint(a, b),
                "lealtad": int(lealtad) if lealtad is not None else random.randint(max(a, 40), max(b, 60)), "exp": 0, "baja": 0, "alta": self.dia}

    def banda_fichas(self):
        """La gente de tu banda, uno por uno, con su nombre y lo que vale. Siempre tantos como diga la banda: una partida
        anterior, que solo sabía cuántos erais, les da nombre y aptitudes la primera vez."""
        j = self.j
        if not isinstance(j.banda_gente, list):
            j.banda_gente = []
        j.banda_gente[:] = [f for f in j.banda_gente if isinstance(f, dict) and f.get("n")]
        for f in j.banda_gente:
            for k in ("punteria", "conduccion", "nervios", "lealtad"):
                try:
                    f[k] = max(0, min(100, int(f.get(k, 50))))
                except (TypeError, ValueError):
                    f[k] = 50
            f.setdefault("exp", 0)
            f.setdefault("baja", 0)
            f.setdefault("g", "h")
            f.setdefault("id", 0)
        n = max(0, int(j.banda))
        while len(j.banda_gente) < n:
            j.banda_gente.append(self._ficha_banda())
        del j.banda_gente[n:]
        return j.banda_gente

    def banda_ficha(self, bid):
        return next((f for f in self.banda_fichas() if f["id"] == bid), None)

    def banda_alta(self, nombre=None, genero=None, nervios=None, lealtad=None):
        """Alguien acaba de entrar en la banda (la cuenta ya está subida): se le apunta con su nombre."""
        j = self.j
        if not isinstance(j.banda_gente, list):
            j.banda_gente = []
        if len(j.banda_gente) < j.banda:
            del j.banda_gente[max(0, j.banda - 1):]
            j.banda_gente.append(self._ficha_banda(nombre, genero, nervios, lealtad))
        self.banda_fichas()
        return j.banda_gente[-1] if j.banda_gente else None

    def banda_quitar_ficha(self, bid=None):
        """Uno deja la banda (la cuenta ya está bajada): si se sabe quién, se borra a ese; si no, al último en llegar."""
        j = self.j
        if not isinstance(j.banda_gente, list):
            j.banda_gente = []
        f = next((x for x in j.banda_gente if isinstance(x, dict) and x.get("id") == bid), None) if bid is not None else None
        if f is not None:
            j.banda_gente.remove(f)
        self.banda_fichas()

    def banda_echar(self, bid, callar=False):
        """Uno de la banda se va o se lo llevan: baja la cuenta, se borra su ficha y desaparece de tu lado."""
        j = self.j
        if self.banda_ficha(bid) is None:
            return
        for e in [e for e in self.personas if getattr(e, "bid", None) == bid]:
            self.personas.remove(e)
        j.banda = max(0, j.banda - 1)
        self.banda_quitar_ficha(bid)

    def banda_ligar(self):
        """Cada uno de los tuyos que tienes al lado es alguien de la lista: se le da su nombre. Devuelve [(persona, ficha)]."""
        from . import sistemas
        fichas = self.banda_fichas()
        presentes = sistemas.miembros_presentes(self)
        usados = set()
        pares = []
        for e in presentes:
            f = self.banda_ficha(getattr(e, "bid", None))
            if f is not None and f["id"] not in usados:
                usados.add(f["id"])
                pares.append((e, f))
            else:
                e.bid = None
        for e in presentes:
            if getattr(e, "bid", None) is not None:
                continue
            nombre = e.nombre.split(",")[0]
            libres = [f for f in fichas if f["id"] not in usados and f.get("baja", 0) < self.dia] or [f for f in fichas if f["id"] not in usados]
            f = next((x for x in libres if x["n"] == nombre), None) or (libres[0] if libres else None)
            if f is None:
                continue
            e.bid = f["id"]
            usados.add(f["id"])
            e.nombre = tr('{n}, de {v}').format(n=(f['n']), v=(self.j.banda_nombre or tr('tu banda')))
            pares.append((e, f))
        return pares

    def aptitud(self, f, atributo):
        """Lo que vale alguien para algo, de 0 a 1: su atributo, más lo que ha aprendido en los golpes que lleva."""
        if not f:
            return 0.5
        v = float(f.get(atributo, 50)) + AJ("exp_bono") * min(float(f.get("exp", 0)), AJ("exp_max"))
        return max(0.05, min(1.0, v / 100.0))

    def ficha_banda_txt(self, f):
        t = tr('{n}: puntería {punteria}, conducción {conduccion}, nervios {nervios} y lealtad {lealtad}, de 100. ').format(n=(f['n']), punteria=(f['punteria']), conduccion=(f['conduccion']), nervios=(f['nervios']), lealtad=(f['lealtad']))
        t += tr("Aún no ha dado ningún golpe contigo") if not f.get("exp") else tr("Lleva un golpe contigo") if f["exp"] == 1 else tr('Lleva {exp} golpes contigo').format(exp=(f['exp']))
        if f.get("baja", 0) >= self.dia:
            dias = f["baja"] - self.dia + 1
            t += tr('. Está {v}: le queda{v2} {dias} día{v3}').format(v=(tr('detenido') if f.get('detenido') else tr('de baja, herido')), v2=('' if _pl() else (tr('n') if dias != 1 else '')), dias=(_dni_pl(dias) if _pl() else dias), v3=('' if _pl() else (tr('s') if dias != 1 else '')))
        t += f". {self.estado_animo_banda(f).capitalize()}. {self.tarea_txt(f)}"      # cómo está y qué hace (capo.py)
        return t

    # ------------------------------------------------------------------ ¿se puede preparar?
    def golpe_bloqueo(self):
        """Por qué no se puede preparar un golpe ahora, o una cadena vacía."""
        if self.en_servidor:
            return tr("En un servidor en línea los golpes no se preparan con la banda: allí tu gente son los demás jugadores, y el botín y la policía los lleva el servidor. El atraco de siempre sigue funcionando.")
        if self.online_activo():
            return tr("Jugando con amigos los golpes no se preparan con la banda. El atraco de siempre sigue funcionando.")
        if not self.j.banda:
            return tr("Para preparar un golpe necesitas gente en tu banda. Se recluta en el móvil, en Territorios, Tu banda, o hablando con la gente de la calle.")
        return ""

    def golpe_presentes(self):
        """Los de tu banda que tienes cerca y pueden trabajar: [(persona, ficha)]."""
        x, y = self.pos()
        return [(e, f) for e, f in self.banda_ligar() if e.dist(x, y) <= AJ("radio_presentes") and f.get("baja", 0) < self.dia]

    def golpe_vehiculos(self):
        """Con qué puede esperar el conductor: tus vehículos de tierra que estén cerca, y los de la banda."""
        x, y = self.pos()
        u = self.tu_vehiculo()
        ops = []
        for v in self.vehiculos:
            if v.muerto or v.tag or v.ardiendo >= 0 or v.ia not in (None, "aparcado") or v.modelo.get("barco") or v.modelo.get("vuela") or getattr(v, "con_chofer", False):
                continue
            if (self.es_mio(v) or v is u or v is self.j.veh) and v.dist(x, y) <= AJ("radio_vehiculo"):
                ops.append(("veh", v, tr('{nombre}, que está a {int} metros').format(nombre=(v.nombre), int=(int(v.dist(x, y))))))
        modelos = [m for m in AJ.lista("vehiculos") if m in self.modelos and not self.modelos[m].get("barco") and not self.modelos[m].get("vuela")] or self.chofer_modelos()
        for m in modelos:
            ops.append(("modelo", m, tr('{nombre} de {v}').format(nombre=(self.modelos[m]['nombre']), v=(self.j.banda_nombre or tr('tu banda')))))
        return ops

    # ------------------------------------------------------------------ empezar
    def golpe_adaptar(self, m, l, plan):
        """Convierte la misión de un atraco en un golpe preparado: la caja tarda, y el plan va con la misión (así un
        reintento lo repite igual)."""
        tipo = "banco" if m.get("id") == "atraco_banco" else "proveedor" if m.get("id") == "asalto_proveedor" else l.tipo
        segundos = round(_tiempo_caja(tipo), 1)
        for p in m["pasos"]:
            if p["tipo"] == "recoger":
                p["tarda"] = segundos
            elif p["tipo"] == "eliminar":
                p["texto"] = AJ.frase("frases_control") + " " + p["texto"]
        m["golpe"] = dict(plan, lugar=l.id, segundos=segundos)
        m["botin_bruto"] = int((m.get("recompensa") or {}).get("dinero", 0))
        antes = m.get("al_completar")

        def hecho():
            if callable(antes):
                antes()
            self.golpe_fin(True)
        m["al_completar"] = hecho
        return m

    def golpe_al_iniciar(self, m):
        """Empieza (o se reintenta) la misión de un golpe preparado: cada uno a su puesto."""
        plan = m.get("golpe")
        if not plan:
            return
        l = self.lug(plan.get("lugar"))
        pares = {f["id"]: (e, f) for e, f in self.banda_ligar()}
        g = {"lugar": l, "plan": plan, "mision": m, "fase": None, "papeles": {}, "alarma": None, "llegan": None, "avisado_cerca": False, "llegado": False,
             "veh": None, "veh_tuyo": False, "subido": False, "t_tirador": 0.0, "t0": self.t, "detenidos": [], "heridos": [], "fallos": {},
             "caja_dicho": set(), "heroe": None, "alarma_antes": None, "tarde": None, "nivel": 1, "botin": int(m.get("botin_bruto", 0))}
        g["nivel"] = next((int(p.get("nivel", 1)) for p in m["pasos"] if p["tipo"] == "policia"), 0)
        g["guardias"] = any(p["tipo"] == "eliminar" for p in m["pasos"])
        for bid, pid in (plan.get("papeles") or {}).items():
            par = pares.get(int(bid))
            pp = papel(pid)
            if par is None or pp is None:
                continue
            e, f = par
            g["papeles"][f["id"]] = {"papel": pp, "persona": e, "ficha": f, "efecto": pp["efecto"], "fuera": False}
            e.papel = pp["efecto"]
        self.golpe = g
        yo = plan.get("yo") or {}
        g["cubrir"] = yo.get("dentro") == "cubrir" and self._golpe_de("caja") is not None
        g["pasajero"] = yo.get("huida") == "pasajero" and self._golpe_de("conductor") is not None
        self._golpe_sortear(g)
        self._golpe_fase("entrada")
        self._golpe_puestos(g, plan)

    def _golpe_de(self, efecto):
        """Quien tiene ese papel y sigue en el golpe: su entrada, o None."""
        g = self.golpe
        if not g:
            return None
        return next((r for r in g["papeles"].values() if r["efecto"] == efecto and not r["fuera"]), None)

    def _golpe_radio(self, r, cual, **kw):
        """Uno de los tuyos habla por la radio."""
        self.son("emisora", cat="interfaz", vol=0.5)
        self.decir(tr('{n}, por la radio: {frase}').format(n=(r['ficha']['n']), frase=(AJ.frase(cual, **kw))))

    def _golpe_fallo(self, r, base=None):
        """¿Le pueden los nervios? Cuanto más temple y más golpes a la espalda, menos."""
        p = (AJ("fallo_base") if base is None else base) / 100.0 * (1.0 - self.aptitud(r["ficha"], "nervios"))
        return random.random() < p

    def _golpe_sortear(self, g):
        """Lo que va a salir mal se decide al empezar, cada vez distinto, según lo que vale cada uno."""
        esc = self._golpe_de("escolta")
        cubre = self.aptitud(esc["ficha"], esc["papel"]["atributo"]) if esc else 0.0
        heroe, alarma = random.random() * 100 < AJ("heroe_prob"), random.random() * 100 < AJ("alarma_prob")
        para_heroe = heroe and esc is not None and random.random() * 100 < AJ("heroe_escolta") * cubre
        para_alarma = alarma and esc is not None and random.random() * 100 < AJ("alarma_escolta") * cubre
        # en qué momento de la caja ocurre, de 0 a 1
        g["heroe"] = random.uniform(0.2, 0.7) if heroe and not para_heroe else None
        g["alarma_antes"] = random.uniform(0.3, 0.8) if alarma and not para_alarma and g["nivel"] else None
        g["evitado"] = {"heroe": para_heroe, "alarma": para_alarma}
        for r in g["papeles"].values():
            ef = r["efecto"]
            if ef == "conductor":
                if self._golpe_fallo(r):
                    g["fallos"]["conductor"] = random.choice(("tarde", "calado"))
            elif ef == "vigilante":
                if self._golpe_fallo(r):
                    g["fallos"]["vigilante"] = "dormido"
                if g["nivel"] and random.random() < AJ("detenido_prob") / 100.0 * (1.2 - self.aptitud(r["ficha"], "nervios")):
                    g["fallos"]["vigilante_detenido"] = True
            elif ef == "caja":
                if self._golpe_fallo(r):
                    g["fallos"]["caja"] = "nervios"
            elif ef == "escolta":
                if g["guardias"] and random.random() < AJ("herido_prob") / 100.0 * (1.3 - self.aptitud(r["ficha"], "punteria")):
                    g["fallos"]["escolta"] = random.uniform(4.0, 12.0)

    def _golpe_puestos(self, g, plan):
        """Cada uno a su sitio: el vigilante a la esquina, el conductor al vehículo, y los demás contigo."""
        l = g["lugar"]
        x, y = (l.x, l.y) if l is not None else self.pos()
        vig = self._golpe_de("vigilante")
        if vig:
            vig["persona"].puesto = self._golpe_esquina(x, y)
            vig["persona"].x, vig["persona"].y = vig["persona"].puesto
            self._golpe_radio(vig, "radio_vigilante_listo")
        con = self._golpe_de("conductor")
        if con:
            if g["fallos"].get("conductor") == "tarde":
                g["tarde"] = AJ.entre("tarde_min", "tarde_max")
                self._golpe_radio(con, "radio_conductor_tarde")
                con["persona"].puesto = self._golpe_esquina(x, y)
            else:
                self._golpe_poner_vehiculo(g, con)
        esc = self._golpe_de("escolta")
        if esc:
            self._golpe_radio(esc, "radio_escolta_control")

    def _golpe_esquina(self, x, y):
        """Un sitio en la acera, a unos metros de la puerta, desde donde vigilar."""
        for _ in range(40):
            a = random.uniform(0, 2 * math.pi)
            d = random.uniform(14, 24)
            px, py = x + math.sin(a) * d, y + math.cos(a) * d
            if self.mundo.superficie(px, py) == "acera":
                return px, py
        return self.mundo.punto_libre(x, y)

    def _golpe_poner_vehiculo(self, g, con, llega=False):
        """El conductor arrima el vehículo de la huida a la puerta, con el motor en marcha."""
        l = g["lugar"]
        plan = g["plan"]
        px, py, d = self.mundo.plaza_junto_a(l) if l is not None else self.plaza_cercana()
        v = next((x for x in self.vehiculos if getattr(x, "id_golpe", None) == plan.get("veh_id") and not x.muerto), None) if plan.get("veh_id") else None
        if v is not None and (self.j.veh is v or v.ia not in (None, "aparcado")):
            v = None
        if v is not None:
            v.x, v.y, v.dir, v.rumbo, v.vel = px, py, d, d * 90.0, 0.0
            g["veh_tuyo"] = True
        else:
            modelo = plan.get("modelo") if plan.get("modelo") in self.modelos else random.choice(self.chofer_modelos())
            v = self.crear_vehiculo(modelo, px, py, d, None, tr('{nombre} de {v}').format(nombre=(self.modelos[modelo]['nombre']), v=(self.j.banda_nombre or tr('tu banda'))), "banda")
            v.propio = True
        v.cerrado = False
        v.en_marcha = True
        if v.canal is None:
            v.canal = self.son(v.modelo["motor"], bucle=True, xy=(v.x, v.y), ref=7, maxd=95, vol=0.7, tono=v.modelo["tono"] * 0.6)
        if v.sirena is None:
            v.sirena = self.son("loc_vehiculo", bucle=True, xy=(v.x, v.y), ref=5, maxd=70)
        g["veh"] = v
        con["persona"].puesto = (v.x, v.y)
        con["persona"].x, con["persona"].y = self.mundo.punto_libre(v.x, v.y)
        if self.chofer:                                          # si ya tenías chófer, se retira: hoy conduce el del golpe
            self.despedir_chofer(callar=True)
        if g["pasajero"]:
            self.chofer = {"estado": "aqui", "t": 0.0, "garaje": None, "ficha": None, "modelo": v.modelo["id"], "veh": v, "propio": g["veh_tuyo"],
                           "nombre": tr('{n}, de {v}').format(n=(con['ficha']['n']), v=(self.j.banda_nombre or tr('tu banda'))), "intentos": 0, "sin_destino": 0.0, "golpe": True}
            v.con_chofer = True
        self._golpe_radio(con, "radio_conductor_llega" if llega else "radio_conductor_listo")
        self.decir(f"{self.situar(v.x, v.y, v.nombre)}." + (tr(" Irás de pasajero.") if g["pasajero"] else tr(" Conducirás tú.")))

    # ------------------------------------------------------------------ las fases
    def _golpe_fase(self, fase):
        g = self.golpe
        if not g or g["fase"] == fase:
            return
        g["fase"] = fase
        if fase == "control" and g["guardias"]:
            return                                               # la frase va con el texto del paso, que ya la lleva delante
        clave = "frases_control_sin_guardia" if fase == "control" else "frases_" + fase
        self.son("emisora", cat="interfaz", vol=0.4)
        self.decir(AJ.frase(clave))

    def golpe_fase_txt(self):
        g = self.golpe
        nombres = {"entrada": "entrada", "control": "control", "caja": tr("la caja"), "salida": "salida", "huida": "huida"}
        orden = ["entrada", "control", "caja", "salida", "huida"]
        if not g or g["fase"] not in nombres:
            return ""
        return tr('Golpe preparado, fase {v} de 5: {v2}.').format(v=(orden.index(g['fase']) + 1), v2=(nombres[g['fase']]))

    def golpe_caja(self):
        """Cómo se abre la caja en este golpe: cuánto se alarga o se acorta, a qué distancia vale estar, y si la abre uno de
        los tuyos sin que tú la toques. None si no hay golpe preparado."""
        g = self.golpe
        if not g:
            return None
        r = self._golpe_de("caja")
        factor = 1.0
        if r:
            if g["fallos"].get("caja") == "nervios":
                factor = 1.0 + AJ("caja_nervios") / 100.0
            else:
                factor = max(0.25, 1.0 - AJ("caja_ayuda") / 100.0 * self.aptitud(r["ficha"], r["papel"]["atributo"]))
        solo = bool(g["cubrir"] and r)
        return {"factor": factor, "radio": AJ("cubrir_radio") if solo else AJ("caja_radio"), "solo": solo, "quien": r}

    def golpe_caja_evento(self, cual, segundos=0):
        """La caja empieza a abrirse, va por la mitad, se para o se abre: lo dice quien la abre."""
        g = self.golpe
        if not g:
            return False
        r = self._golpe_de("caja")
        if cual == "empieza":
            self._golpe_fase("caja")
            if r:
                self._golpe_radio(r, "radio_caja_nervios" if g["fallos"].get("caja") == "nervios" else "radio_caja_empieza" if g["cubrir"] else "radio_caja_ayuda", segundos=int(round(segundos)))
                return bool(g["cubrir"])
            return False
        if r is None:
            return False
        if cual == "mitad":
            self._golpe_radio(r, "radio_caja_mitad")
        elif cual == "hecho":
            self._golpe_radio(r, "radio_caja_hecho")
        elif cual == "pausa":
            self._golpe_radio(r, "radio_caja_solo")
        return True

    def golpe_retraso_policia(self, nivel):
        """Al acabar la caja: cuánto tarda aún la policía en llegar. Con un golpe preparado la alarma salta y el vigilante,
        si lo hay, la entretiene; devuelve los segundos que faltan (0, ya)."""
        g = self.golpe
        if not g:
            return 0.0
        g["nivel"] = max(g["nivel"], int(nivel or 1))
        self._golpe_fase("salida")
        if g["alarma"] is None:
            self._golpe_alarma(g)
        return max(0.0, (g["llegan"] or self.t) - self.t)

    def _golpe_alarma(self, g, antes=False):
        """Salta la alarma. Desde aquí, la policía llega cuando el vigilante deje de poder entretenerla."""
        g["alarma"] = self.t
        r = self._golpe_de("vigilante")
        retraso = 0.0
        if r:
            if g["fallos"].get("vigilante") == "dormido":
                self._golpe_radio(r, "radio_vigilante_falla")
            else:
                retraso = AJ("vigilante_retraso") * (0.5 + 0.75 * self.aptitud(r["ficha"], r["papel"]["atributo"]))
                self._golpe_radio(r, "radio_vigilante_alarma", segundos=int(round(retraso)))
        g["llegan"] = self.t + retraso
        if antes:
            self.son("alarma", vol=0.4)

    def _golpe_llegan(self, g):
        """La policía ya está aquí: cae la búsqueda, y al vigilante lo pueden coger."""
        if g["llegado"]:
            return
        g["llegado"] = True
        r = self._golpe_de("vigilante")
        if r and g["fallos"].get("vigilante") != "dormido":
            self._golpe_radio(r, "radio_vigilante_llegan")
        if g["nivel"]:
            self.poner_busqueda(g["nivel"])
        if r and g["fallos"].get("vigilante_detenido"):
            f = r["ficha"]
            r["fuera"] = True
            g["detenidos"].append(f["n"])
            self.son("esposas", cat="interfaz", vol=0.6)
            self.decir(AJ.frase("frases_vigilante_detenido", nombre=f["n"]))
            delata = f["lealtad"] < AJ("delata_lealtad")
            self.banda_echar(f["id"])
            self.j.stats["banda_detenidos"] = self.j.stats.get("banda_detenidos", 0) + 1
            if delata:
                self.decir(AJ.frase("frases_delata", nombre=f["n"]) + tr(' Quedáis {banda} en la banda.').format(banda=(self.j.banda)))
                if AJ("delata_busqueda") >= 1 and g["nivel"]:
                    self.poner_busqueda(min(5, g["nivel"] + AJ.entero("delata_busqueda")))
                self.hon_antecedente(2, tr('señalado por un detenido tras el atraco a {v}').format(v=(g['lugar'].nombre if g['lugar'] else tr('un local'))))
                self.j.stats["banda_delaciones"] = self.j.stats.get("banda_delaciones", 0) + 1
            else:
                self.decir(AJ.frase("frases_no_delata", nombre=f["n"]) + tr(' Quedáis {banda} en la banda.').format(banda=(self.j.banda)))

    def actualizar_golpe(self, dt):
        g = self.golpe
        if not g:
            return
        ms = self.mision
        if not ms or not ms["def"].get("golpe"):
            self.golpe_fin(False, callar=True)
            return
        pasos = ms["def"]["pasos"]
        if not (0 <= ms["paso"] < len(pasos)):
            return
        tipo = pasos[ms["paso"]]["tipo"]
        j = self.j
        if tipo == "eliminar":
            self._golpe_fase("control")
            t_herido = g["fallos"].get("escolta")
            esc = self._golpe_de("escolta")
            if esc and t_herido is not None and ms.get("generado") and self.t - g.setdefault("t_control", self.t) >= t_herido:
                g["fallos"].pop("escolta")
                self._golpe_herido(g, esc)
        elif tipo == "recoger":
            if g["fase"] in ("entrada", None):
                self._golpe_fase("control")
                g["fase_t"] = self.t
            ab = ms.get("abriendo")
            hecho = float(ab["t"]) / max(0.1, float(ab["total"])) if ab else 0.0      # cuánto va de caja, de 0 a 1
            esc = self._golpe_de("escolta")
            if g["heroe"] is not None and hecho >= g["heroe"]:
                g["heroe"] = None
                self._golpe_heroe(g)
            elif g["evitado"].get("heroe") and esc and hecho >= 0.4:
                g["evitado"]["heroe"] = False
                self._golpe_radio(esc, "radio_escolta_heroe")
            if g["alarma_antes"] is not None and hecho >= g["alarma_antes"] and g["alarma"] is None:
                g["alarma_antes"] = None
                self.decir(AJ.frase("frases_alarma"))
                self._golpe_alarma(g, antes=True)
            elif g["evitado"].get("alarma") and esc and hecho >= 0.7:
                g["evitado"]["alarma"] = False
                self._golpe_radio(esc, "radio_escolta_alarma")
        elif tipo == "policia":
            if g["llegado"] and (j.veh is not None or (g["lugar"] is not None and math.hypot(g["lugar"].x - self.pos()[0], g["lugar"].y - self.pos()[1]) > 45)):
                self._golpe_fase("huida")
        # la policía viene de camino: el vigilante lo va cantando
        if g["alarma"] is not None and not g["llegado"]:
            falta = g["llegan"] - self.t
            vig = self._golpe_de("vigilante")
            if falta <= 0:
                self._golpe_llegan(g)
            elif vig and not g["avisado_cerca"] and falta <= AJ("vigilante_aviso") and g["fallos"].get("vigilante") != "dormido":
                g["avisado_cerca"] = True
                self._golpe_radio(vig, "radio_vigilante_cerca", segundos=max(1, int(round(falta))))
        # el conductor que llegaba tarde
        if g["tarde"] is not None and tipo == "policia":
            g["tarde"] -= dt
            con = self._golpe_de("conductor")
            if con is None:
                g["tarde"] = None
            elif g["tarde"] <= 0:
                g["tarde"] = None
                self._golpe_poner_vehiculo(g, con, llega=True)
        v = g["veh"]
        if v is not None and (v.muerto or v not in self.vehiculos):
            g["veh"] = v = None
        if v is not None and j.veh is v and not g["subido"]:
            g["subido"] = True
            self._golpe_subes(g)
        self._golpe_tirador(g, dt)

    def _golpe_herido(self, g, r):
        f = r["ficha"]
        r["fuera"] = True
        g["heridos"].append(f["n"])
        dias = random.randint(*sorted((AJ.entero("herido_dias_min"), AJ.entero("herido_dias_max"))))
        f["baja"] = self.dia + dias
        e = r["persona"]
        self.son("dolor_npc", xy=(e.x, e.y), ref=6, tono=e.tono)
        if e in self.personas:
            self.personas.remove(e)
        self.decir(AJ.frase("frases_escolta_herido", nombre=f["n"]) + tr(' Estará de baja {dias} días.').format(dias=(dias)))
        # sin él, lo que tenía a raya puede volver a pasar
        if g["evitado"].get("heroe"):
            g["evitado"]["heroe"], g["heroe"] = False, random.uniform(0.2, 0.7)
        if g["evitado"].get("alarma"):
            g["evitado"]["alarma"], g["alarma_antes"] = False, random.uniform(0.3, 0.8)

    def _golpe_heroe(self, g):
        x, y = self.pos()
        pos = self._punto_cercano(7, 14, acera=False) or self.mundo.punto_libre(x + random.uniform(-10, 10), y + random.uniform(-10, 10))
        e = Persona("enemigo", pos[0], pos[1], tr("El que se hace el héroe"))
        e.salud, e.arma = 55.0, "pistola"
        e.hostil, e.estado, e.activo, e.tag = True, "ataca", True, "golpe"
        e.t_disparo = random.uniform(1.5, 2.5)
        self.personas.append(e)
        g["heroe_persona"] = e
        self.son("grito", xy=pos, vol=0.6)
        self.decir(AJ.frase("frases_heroe") + tr(" Pulsa Q para fijarlo."))

    def _golpe_subes(self, g):
        """Subes al vehículo de la huida: el motor ya estaba en marcha, y el conductor te da ventaja."""
        con = self._golpe_de("conductor")
        if con is None:
            return
        j = self.j
        apt = self.aptitud(con["ficha"], con["papel"]["atributo"])
        if g["fallos"].get("conductor") == "calado":
            self._golpe_radio(con, "radio_conductor_sin_ventaja")
        elif not g["llegado"] and g["alarma"] is not None:
            extra = AJ("conductor_ventaja") * (0.5 + 0.75 * apt)
            g["llegan"] += extra
            g["avisado_cerca"] = False
            self._golpe_radio(con, "radio_conductor_ventaja")
            self.decir(tr('Ventaja: la policía tardará unos {int} segundos más en dar contigo.').format(int=(int(round(extra)))))
        elif j.estrellas > 1 and random.random() * 100 < AJ("conductor_nivel") * (0.4 + 0.6 * apt):
            from .combate import UMBRAL
            j.puntos_busqueda = float(UMBRAL[j.estrellas - 2])
            j.estrellas -= 1
            self.sv_busqueda(j.estrellas)
            self._golpe_radio(con, "radio_conductor_ventaja")
            self.son("estrella_baja", cat="interfaz")
            self.decir(tr('Ventaja: sale por donde no os esperan. Nivel de búsqueda {estrellas}.').format(estrellas=(j.estrellas)))
        elif not g["pasajero"]:
            self._golpe_radio(con, "radio_conductor_tu")
        if g["pasajero"] and self.chofer_conduce() and not self.gps:
            dest = self._destino_azar(280, 700, g["lugar"])
            self.gps_a_lugar(dest, callar=True)
            self.decir(tr('{n} pone rumbo a {nombre}, lejos de aquí. Con la L eliges tú otro destino.').format(n=(con['ficha']['n']), nombre=(dest.nombre)))

    def _golpe_tirador(self, g, dt):
        r = self._golpe_de("tirador")
        j = self.j
        if r is None or j.veh is None or j.estrellas <= 0:
            return
        g["t_tirador"] -= dt
        if g["t_tirador"] > 0:
            return
        g["t_tirador"] = AJ("tirador_cada") * random.uniform(0.8, 1.3)
        x, y = self.pos()
        alcance = AJ("tirador_alcance")
        blancos = [v for v in self.vehiculos if v.ia == "policia" and not v.muerto and getattr(v, "hostil", True) and v.dist(x, y) <= alcance]
        gente = [p for p in self.personas if p.tipo == "policia" and p.hostil and not p.muerto and p.dist(x, y) <= alcance]
        if not blancos and not gente:
            return
        if not g.get("tirador_dicho"):
            g["tirador_dicho"] = True
            self._golpe_radio(r, "radio_tirador_dispara")
        self.son("disparo_pistola", vol=0.6)
        apt = self.aptitud(r["ficha"], r["papel"]["atributo"])
        if random.random() > 0.25 + 0.6 * apt:
            return
        dano = AJ("tirador_dano") * (0.7 + 0.6 * apt)
        if blancos:
            v = min(blancos, key=lambda v: v.dist(x, y))
            self.danar_vehiculo(v, dano)
        else:
            self.danar_persona(min(gente, key=lambda p: p.dist(x, y)), dano)
        g["tirador_aciertos"] = g.get("tirador_aciertos", 0) + 1
        if g["tirador_aciertos"] % 3 == 1:
            self.decir(f"{r['ficha']['n']}: {AJ.frase('radio_tirador_acierta')}")

    # ------------------------------------------------------------------ el final
    def golpe_reparto(self, botin, g=None):
        """Cuánto se lleva cada uno de los que han cumplido: [(nombre, papel, euros)] y lo que te queda."""
        g = g or self.golpe
        if not g:
            return [], botin
        partes = [(r["ficha"]["n"], r["papel"]["nombre"], float(r["papel"]["parte"])) for r in g["papeles"].values()
                  if r["ficha"]["n"] not in g["detenidos"] and self.banda_ficha(r["ficha"]["id"]) is not None]
        total = sum(p for _, _, p in partes)
        tope = AJ("reparto_tope")
        escala = tope / total if total > tope > 0 else 1.0 if tope > 0 else 0.0
        lista = [(n, papel_n, int(botin * p * escala / 100.0)) for n, papel_n, p in partes]
        return lista, max(0, botin - sum(e for _, _, e in lista))

    def golpe_fin(self, exito, callar=False):
        """Se acaba el golpe: bien (reparto, experiencia y lealtad) o mal (cada uno por su lado, y la confianza baja)."""
        g = self.golpe
        if not g:
            return
        self.golpe = None
        m = g.get("mision")
        for e in self.personas:
            if getattr(e, "puesto", None) is not None:
                e.puesto = None
            if getattr(e, "papel", None):
                e.papel = None
        h = g.get("heroe_persona")
        if h is not None and h in self.personas and not exito:
            self.personas.remove(h)
        v = g["veh"]
        if v is not None and not v.muerto:
            v.en_marcha = False
            if self.j.veh is not v:
                if v.canal is not None:
                    v.canal.parar()
                    v.canal = None
                if not (self.chofer and self.chofer.get("veh") is v):
                    if v.sirena is not None:
                        v.sirena.parar()
                        v.sirena = None
                    if v.tag == "banda":                         # el coche de la banda se va con quien lo trajo
                        self.quitar_vehiculo(v)
        fichas = [r["ficha"] for r in g["papeles"].values() if self.banda_ficha(r["ficha"]["id"]) is not None]
        if exito:
            botin = int(g["botin"])
            lista, neto = self.golpe_reparto(botin, g) if m is not None else ([], botin)
            if m is not None and botin:
                m.setdefault("recompensa", {})["dinero"] = neto
            for f in fichas:
                f["exp"] = int(f.get("exp", 0)) + 1
                f["lealtad"] = min(100, f["lealtad"] + AJ.entero("lealtad_exito"))
            self.j.stats["golpes_preparados"] = self.j.stats.get("golpes_preparados", 0) + 1
            if lista and botin and not callar:
                self.son("dinero", cat="interfaz", vol=0.5)
                self.decir(AJ.frase("frases_reparto", partes=_lista_txt(f"{n}, {e} euros" for n, _, e in lista), neto=neto, botin=botin))
            if g["heridos"] and not callar:
                self.decir(tr('{_lista_txt} cobra igual, pero no podrá trabajar hasta que se cure.').format(_lista_txt=(_lista_txt(g['heridos']))))
            return
        if m is not None and g["botin"]:
            m.setdefault("recompensa", {})["dinero"] = int(g["botin"])       # un reintento empieza con el botín entero
        se_van = []
        for f in fichas:
            f["lealtad"] = max(0, f["lealtad"] - AJ.entero("lealtad_fracaso"))
            if f["lealtad"] <= 0:
                se_van.append(f)
        for f in se_van:
            self.banda_echar(f["id"])
            if not callar:
                self.decir(AJ.frase("frases_se_va", nombre=f["n"]) + tr(' Quedáis {banda}.').format(banda=(self.j.banda)))
        self.j.stats["golpes_fallidos"] = self.j.stats.get("golpes_fallidos", 0) + 1

    def golpe_estado_txt(self):
        """Para la tecla del objetivo: en qué fase va el golpe y quién hace qué."""
        g = self.golpe
        if not g:
            return ""
        t = self.golpe_fase_txt()
        quien = [f"{r['ficha']['n']}, {r['papel']['nombre'].lower()}" for r in g["papeles"].values() if not r["fuera"]]
        if quien:
            t += " " + _lista_txt(quien) + "."
        if g["alarma"] is not None and not g["llegado"]:
            t += tr(' La policía llega en unos {max} segundos.').format(max=(max(1, int(g['llegan'] - self.t))))
        return t


# ====================================================================== menús
def como_funciona(p):
    """«Cómo funciona esto»: los golpes preparados, con los números de verdad de los datos."""
    from .menus import Menu, Opcion
    app = p.app
    lineas = [
        tr("Qué es. Un atraco de los de siempre, a un banco, a un local con caja o a un proveedor, lo puedes preparar antes si tienes a gente de tu banda al lado. No es obligatorio: sin prepararlo, el atraco es el de siempre."),
        tr("Antes de empezar repartes los papeles: eliges a cada uno de los tuyos y le das uno. A quien no le des ninguno, viene contigo y pelea a tu lado, como siempre. Quien tiene un papel está en lo suyo."),
    ]
    for x in PAPELES:
        lineas.append(tr('{nombre}. {desc} Rinde según su {v}. Se lleva el {int} por ciento del botín.').format(nombre=(x['nombre']), desc=(x['desc']), v=(ATRIBUTOS[x['atributo']]), int=(int(x['parte']))))
    lineas += [
        tr("Tu papel. Dentro, o abres tú la caja, o cubres a quien la abre y te ocupas de lo que venga. En la huida, o conduces tú, o vas de pasajero y disparas con la Q y Control."),
        tr('Las fases. Un golpe preparado tiene cinco, y el juego las dice: entrada, control, caja, salida y huida. La tecla O te dice en cuál vas. La caja ya no se coge al momento: tarda entre {entero} y {entero2} segundos según el local, y más en un banco. Se oye cómo avanza. Si te apartas, se para.').format(entero=(AJ.entero('caja_min')), entero2=(AJ.entero('caja_max'))),
        tr("Lo que vale cada uno. Cada persona de tu banda tiene puntería, conducción, nervios y lealtad, de 0 a 100, distintas en cada partida. Las ves en el móvil, en Territorios, Tu banda, Tu gente. Con cada golpe que sale bien aprenden y te son más leales."),
        tr("Lo que puede salir mal. A quien le fallan los nervios llega tarde, no avisa o tarda más con la caja. Al de dentro le pueden herir y está de baja unos días. Al vigilante lo pueden detener, y si su lealtad es baja, da tu nombre: "
        "sube la búsqueda y te queda un antecedente. Si el golpe fracasa, todos pierden confianza en ti, y quien se queda sin ninguna se va."),
        tr('El reparto. Cada uno cobra su parte del botín al acabar; entre todos, como mucho el {entero} por ciento. Lo demás es tuyo. Antes de empezar, el menú te dice cuánto te va a quedar.').format(entero=(AJ.entero('reparto_tope'))),
        tr("En un servidor en línea y jugando con amigos los golpes no se preparan con la banda: el atraco de siempre sigue funcionando."),
    ]
    ops = [Opcion(t.rstrip("."), ayuda=tr("Una parte de la explicación. Las demás, con las flechas arriba y abajo.")) for t in lineas]
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, tr("Golpes preparados: cómo funciona. Recorre la explicación con las flechas"), ops)
    app.abrir(m)


def menu_gente(p):
    """Tu gente, uno por uno: lo que vale cada cual. Intro sobre alguien abre lo que puedes hacer con esa persona."""
    from .menus import Menu, Opcion
    app = p.app
    p.banda_ligar()

    def ops():
        lista = [Opcion((lambda f=f: p.ficha_banda_txt(f)), (lambda f=f: menu_miembro(p, f, lambda: m.refrescar(False))),
                        ayuda=tr("Intro para hablar con esta persona, invitarla, darle una paga o echarla. Puntería, para disparar y tener a raya a la gente; conducción, para la huida; "
                              "nervios, para no fallar cuando aprieta; lealtad, para no delatarte si lo detienen. Suben con cada golpe preparado que sale bien.")) for f in p.banda_fichas()]
        return lista or [Opcion(tr("Todavía no hay nadie en tu banda"), ayuda=tr("Se recluta gente en Territorios, Tu banda. Hace falta tener al menos un territorio."))]
    m = Menu(app, lambda: tr('Tu gente: {banda} en {v}').format(banda=(p.j.banda), v=(p.j.banda_nombre or tr('tu banda'))), ops, intro=tr("Intro sobre alguien para tratar con esa persona"))
    app.abrir(m)


def menu_miembro(p, f, al_cambiar=None):
    """Tratar con alguien de tu banda, por su nombre: hablar, invitarle, darle una paga o echarle. Lo que le das le hace más leal."""
    from .menus import Menu, Opcion
    app = p.app
    n = f["n"]

    def hoy(que):
        return f.get("trato", {}).get(que) == p.dia

    def apuntar(que):
        f.setdefault("trato", {})[que] = p.dia

    def leal(puntos):
        f["lealtad"] = max(0, min(100, int(f.get("lealtad", 50)) + int(puntos)))

    def hecho(texto):
        app.decir(texto + tr(' Lealtad {lealtad} de 100.').format(lealtad=(f['lealtad'])), True)
        mm.refrescar(False)
        if al_cambiar:
            al_cambiar()

    def hablar():
        if hoy("charla"):
            return app.decir(tr('Hoy ya has hablado un rato con {n}.').format(n=(n)), True)
        apuntar("charla")
        leal(AJ("charla_lealtad"))
        p.pasar_horas(0.5)
        from .sistemas import alias_de
        hecho(AJ.frase("frases_charla_banda", nombre=n, alias=alias_de(p.j)))

    def invitar():
        if hoy("invitar"):
            return app.decir(tr('Hoy ya has invitado a {n}.').format(n=(n)), True)
        if not p.pagar(AJ.entero("invitar_precio")):
            return
        apuntar("invitar")
        leal(AJ("invitar_lealtad"))
        p.cambiar_animo(2)
        p.pasar_horas(1)
        hecho(AJ.frase("frases_invitar_banda", nombre=n))

    def paga():
        if hoy("paga"):
            return app.decir(tr('Hoy ya le has dado una paga a {n}.').format(n=(n)), True)
        euros = AJ.entero("paga_precio")
        if not p.pagar(euros):
            return
        apuntar("paga")
        leal(AJ("paga_lealtad"))
        p.son("dinero", cat="interfaz")
        from .sistemas import alias_de
        hecho(AJ.frase("frases_paga_banda", nombre=n, euros=euros, alias=alias_de(p.j)))

    def echar():
        def si():
            app.cerrar(conf)
            app.cerrar(mm)
            p.banda_echar(f["id"])
            app.decir(AJ.frase("frases_echar_banda", nombre=n), True)
            if al_cambiar:
                al_cambiar()
        conf = Menu(app, tr('¿Echas a {n} de la banda? No vuelve').format(n=(n)), [Opcion(tr("No, que se quede"), lambda: app.cerrar(conf)), Opcion(tr('Sí, echar a {n}').format(n=(n)), si, ayuda=tr("Se va de la banda para siempre y deja de cobrar su paga."))])
        app.abrir(conf)
    ops = [Opcion(lambda: p.ficha_banda_txt(f), ayuda=tr("Puntería, para disparar; conducción, para la huida; nervios, para no fallar cuando aprieta; lealtad, para no delatarte si lo detienen. Lo que le das aquí le hace más leal.")),
           Opcion(tr('Hablar un rato con {n}').format(n=(n)), hablar, ayuda=tr("Media hora de charla: te cuenta cosas suyas y gana algo de lealtad. Una vez al día.")),
           Opcion(tr('Invitar a {n} a algo: {entero} euros').format(n=(n), entero=(AJ.entero('invitar_precio'))), invitar, ayuda=tr("Una cerveza, un café, un bocadillo. Gana más lealtad que hablando. Una vez al día.")),
           Opcion(tr('Darle una paga extra a {n}: {entero} euros').format(n=(n), entero=(AJ.entero('paga_precio'))), paga,
                  ayuda=tr("Dinero aparte de lo que se lleva en los golpes. Es lo que más lealtad da, y alguien leal no te delata si lo detienen. Una vez al día.")),
           Opcion(lambda: tr('Tarea: {tarea_txt}. Intro para cambiarla').format(tarea_txt=(p.tarea_txt(f))), lambda: menu_tarea(p, f, lambda: mm.refrescar(False)),
                  ayuda=tr("Vender en la calle la mercancía que guardas en el armario de tus casas, o cocinar en uno de tus laboratorios con el material que tengas. "
                        "Al final del día te traen lo vendido, menos su parte. A un camello lo pueden detener, y uno poco leal se queda con algo más.")),
           Opcion(tr('Echar a {n} de la banda').format(n=(n)), echar, ayuda=tr("Se va y no vuelve. Tu banda tiene una persona menos.")),
           Opcion(tr("Volver"), lambda: app.cerrar(mm))]
    mm = Menu(app, n, ops)
    app.abrir(mm)


def menu_tarea(p, f, al_cambiar=None):
    """La tarea de uno de tu banda: ninguna, vender tu mercancía o cocinar en uno de tus laboratorios (capo.py)."""
    from .menus import Menu, Opcion
    from . import capo
    app, j = p.app, p.j

    def poner(t, texto):
        def g():
            f["tarea"] = t
            app.cerrar(m)
            app.decir(texto, True)
            if al_cambiar:
                al_cambiar()
        return g
    ops = [Opcion(tr("Ninguna: que solo te acompañe cuando le llames"), poner("", tr('{n} deja lo que hacía.').format(n=(f['n']))),
                  ayuda=tr("Deja de vender o de cocinar. Sigue en tu banda y viene contigo cuando llamas a los tuyos."))]
    if p.modo_adulto() and p.capo_activo():
        tt = capo.tareas()
        if "vender" in tt:
            ops.append(Opcion(tt["vender"].capitalize(), poner("vender", tr('{n} saldrá cada día a vender lo que guardas en el armario de tus casas. Al final del día te trae lo suyo.').format(n=(f['n']))),
                              ayuda=tr("Coge la mercancía de los armarios de tus casas. Sin mercancía guardada, no hay nada que vender.")))
        if "cocinar" in tt:
            for cid in j.laboratorios:
                l = p.lug(cid)
                if l is not None:
                    ops.append(Opcion(tr('{capitalize}: el de {nombre_lugar}').format(capitalize=(tt['cocinar'].capitalize()), nombre_lugar=(p.nombre_lugar(l))), poner("cocinar:" + cid, tr('{n} cocinará cada día en {nombre_lugar}, mientras haya material.').format(n=(f['n']), nombre_lugar=(p.nombre_lugar(l)))),
                                      ayuda=tr("Cada día gasta una tanda de material, que se compra a un proveedor, y deja la mercancía en el armario de esa casa. Puede salir mal.")))
    else:
        ops.append(Opcion(tr("Las tareas de vender y cocinar necesitan el contenido para adultos, y no hay en un servidor"),
                          ayuda=tr("El contenido para adultos se activa en Opciones, en una partida que no sea en un servidor.")))
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, tr('Tarea para {n}').format(n=(f['n'])), ops)
    app.abrir(m)


def preparar(p, l, empezar, que=tr("el golpe")):
    """El menú «Preparar el golpe»: quién hace qué, tu papel, el vehículo y empezar. `empezar(plan)` lanza el atraco de
    ese sitio con el plan; devuelve True si ha empezado."""
    from .menus import Menu, Opcion
    from . import sistemas
    app = p.app
    motivo = p.golpe_bloqueo()
    if motivo:
        app.son("error")
        app.decir(motivo, True)
        return
    plan = {"papeles": {}, "yo": {"dentro": "caja", "huida": "conducir"}, "veh_id": None, "modelo": None}
    caja = p.caja_de_local(l) or {}
    botin = int(caja.get("dinero", 0) or 0)

    def presentes():
        return p.golpe_presentes()

    def limpiar():
        vivos = {f["id"] for _, f in presentes()}
        for bid in [b for b in plan["papeles"] if b not in vivos]:
            del plan["papeles"][bid]
        efectos = {papel(pid)["efecto"] for pid in plan["papeles"].values() if papel(pid)}
        if "caja" not in efectos:
            plan["yo"]["dentro"] = "caja"
        if "conductor" not in efectos:
            plan["yo"]["huida"] = "conducir"

    def partes_txt():
        total = sum(papel(pid)["parte"] for pid in plan["papeles"].values() if papel(pid))
        tope = AJ("reparto_tope")
        total = min(total, tope)
        if not plan["papeles"]:
            return tr("Reparto: nadie tiene papel todavía, así que todo el botín sería para ti")
        return tr('Reparto: tu gente se lleva el {int} por ciento y tú el {int2}').format(int=(int(total)), int2=(int(100 - total))) + (tr('. Hoy, de unos {botin} euros, te quedarían {int}').format(botin=(botin), int=(int(botin * (100 - total) / 100))) if botin else "")

    def elegir_papel(f):
        def abrir():
            def poner(pid):
                def h():
                    if pid is None:
                        plan["papeles"].pop(f["id"], None)
                    else:
                        ef = papel(pid)["efecto"]
                        for b in [b for b, x in plan["papeles"].items() if papel(x) and papel(x)["efecto"] == ef and b != f["id"]]:
                            del plan["papeles"][b]              # cada papel lo hace uno solo: el anterior se queda sin él
                        plan["papeles"][f["id"]] = pid
                    limpiar()
                    app.cerrar(sub)
                    app.decir(f"{f['n']}: {papel(pid)['nombre'].lower() if pid else tr('sin papel, viene contigo')}.", True)
                return h
            ops = [Opcion(tr('{nombre}. {n} tiene {v} de 100 en {v2}').format(nombre=(x['nombre']), n=(f['n']), v=(f[x['atributo']]), v2=(ATRIBUTOS[x['atributo']])), poner(x["id"]),
                          ayuda=tr('{desc} Se lleva el {int} por ciento del botín.').format(desc=(x['desc']), int=(int(x['parte'])))) for x in PAPELES]
            ops.append(Opcion(tr("Sin papel: viene contigo y pelea a tu lado, como siempre"), poner(None), ayuda=tr("No cobra parte del botín.")))
            sub = Menu(app, tr('Papel de {n}. {ficha_banda_txt}').format(n=(f['n']), ficha_banda_txt=(p.ficha_banda_txt(f))), ops)
            app.abrir(sub)
        return abrir

    def texto_miembro(f):
        return lambda: f"{f['n']}: " + (papel(plan["papeles"][f["id"]])["nombre"].lower() if papel(plan["papeles"].get(f["id"])) else tr("sin papel, viene contigo"))

    def cambiar_dentro():
        if not any(papel(x) and papel(x)["efecto"] == "caja" for x in plan["papeles"].values()):
            app.son("error")
            app.decir(tr("Para cubrir tiene que haber alguien que abra la caja: dale ese papel a uno de los tuyos."), True)
            return
        plan["yo"]["dentro"] = "cubrir" if plan["yo"]["dentro"] == "caja" else "caja"
        m.refrescar()

    def cambiar_huida():
        if not any(papel(x) and papel(x)["efecto"] == "conductor" for x in plan["papeles"].values()):
            app.son("error")
            app.decir(tr("Para ir de pasajero tiene que haber conductor: dale ese papel a uno de los tuyos."), True)
            return
        plan["yo"]["huida"] = "pasajero" if plan["yo"]["huida"] == "conducir" else "conducir"
        m.refrescar()

    def veh_txt():
        if plan["veh_id"] is not None:
            v = next((x for x in p.vehiculos if getattr(x, "id_golpe", None) == plan["veh_id"] and not x.muerto), None)
            if v is not None:
                return tr('Vehículo de la huida: {nombre}').format(nombre=(v.nombre))
            plan["veh_id"] = None
        return tr('Vehículo de la huida: {nombre} de la banda').format(nombre=(p.modelos[plan['modelo']]['nombre'])) if plan["modelo"] in p.modelos else tr("Vehículo de la huida: el que tenga la banda a mano")

    def elegir_veh():
        def poner(tipo, cosa):
            def h():
                if tipo == "veh":
                    cosa.id_golpe = cosa.id
                    plan["veh_id"], plan["modelo"] = cosa.id, None
                else:
                    plan["veh_id"], plan["modelo"] = None, cosa
                app.cerrar(sub)
                app.decir(veh_txt() + ".", True)
            return h
        ops = [Opcion(t, poner(tipo, cosa), ayuda=tr("El conductor lo arrima a la puerta y te espera en él con el motor en marcha.") if tipo == "veh"
                      else tr("Lo trae la banda: no tiene que ser tuyo ni estar cerca. El conductor te espera en él con el motor en marcha."))
               for tipo, cosa, t in p.golpe_vehiculos()]
        sub = Menu(app, tr("Con qué vehículo espera el conductor"), ops, intro=tr("Los tuyos que estén cerca y los de la banda"))
        app.abrir(sub)

    def llamar():
        n, frase = sistemas.llamar(p)
        p.banda_ligar()
        if not n:
            app.son("error")
        m.refrescar(False)
        app.decir(frase, True)

    def lanzar():
        limpiar()
        if not plan["papeles"]:
            app.son("error")
            app.decir(tr("Nadie tiene papel todavía. Da al menos uno, o vuelve atrás y empieza el atraco de siempre."), True)
            return
        copia = {"papeles": {str(b): pid for b, pid in plan["papeles"].items()}, "yo": dict(plan["yo"]), "veh_id": plan["veh_id"], "modelo": plan["modelo"]}
        empezar(copia)

    def ops():
        limpiar()
        pres = presentes()
        lista = [Opcion(tr("Cómo funciona esto: los papeles, las fases y el reparto"), lambda: como_funciona(p),
                        ayuda=tr("La explicación entera de los golpes preparados, con sus números."))]
        for _, f in pres:
            lista.append(Opcion(texto_miembro(f), elegir_papel(f), ayuda=p.ficha_banda_txt(f) + tr(". Intro para darle un papel o quitárselo.")))
        if len(pres) < len([f for f in p.banda_fichas() if f.get("baja", 0) < p.dia]):
            lista.append(Opcion(tr("Llamar a los de tu banda que faltan"), llamar, ayuda=tr("Acuden a donde estés. Los que están de baja, heridos, no vienen.")))
        if not pres:
            lista.append(Opcion(tr("No tienes a nadie de tu banda al lado: llámalos"),
                                ayuda=tr("Solo se les puede dar papel a los que están contigo. Llámalos desde este menú o desde Territorios, Tu banda.")))
        lista.append(Opcion(lambda: tr("Tú, dentro: ") + (tr("cubres a quien abre la caja") if plan["yo"]["dentro"] == "cubrir" else tr("abres tú la caja")), cambiar_dentro,
                            ayuda=tr("Intro cambia. Si abres tú, tienes que estar junto a la caja hasta que ceda. Si cubres, la abre el de la caja y tú te quedas cerca, libre para pelear.")))
        lista.append(Opcion(lambda: tr("Tú, en la huida: ") + (tr("vas de pasajero") if plan["yo"]["huida"] == "pasajero" else tr("conduces tú")), cambiar_huida,
                            ayuda=tr("Intro cambia. De pasajero conduce el conductor y tú disparas con la Q y Control. Si conduces tú, te encuentras el motor en marcha.")))
        if any(papel(x) and papel(x)["efecto"] == "conductor" for x in plan["papeles"].values()):
            lista.append(Opcion(veh_txt, elegir_veh, ayuda=tr("El conductor lo arrima a la puerta y te espera con el motor en marcha. Vale un vehículo tuyo que esté cerca, o uno de la banda.")))
        lista.append(Opcion(partes_txt, ayuda=tr("Cada uno cobra su parte al acabar, si el golpe sale bien. A quien detienen no cobra.")))
        lista.append(Opcion(tr('Empezar {que}').format(que=(que)), lanzar, ayuda=tr("Con el plan como está. Hace falta que al menos uno de los tuyos tenga papel.")))
        return lista
    m = Menu(app, lambda: tr('Preparar {que}: {nombre}. Tienes al lado a {len} de {v}').format(que=(que), nombre=(l.nombre), len=(len(presentes())), v=(p.j.banda_nombre or tr('tu banda'))), ops,
             intro=tr("Da un papel a cada uno. A quien no le des ninguno, viene contigo"))
    app.abrir(m)


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False


def _dni_pl(d):
    if d == 1:
        return "został 1 dzień"
    if d % 10 in (2, 3, 4) and d % 100 not in (12, 13, 14):
        return f"zostały {d} dni"
    return f"zostało {d} dni"
