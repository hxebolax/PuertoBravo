"""Vida, reputación y consecuencias: ser buena persona, delincuente o las dos cosas, y lo que trae cada camino.

Todo se apoya en los dos medidores de siempre, que son independientes: el prestigio entre los vecinos (`j.ciudadania`) y la
fama en la calle (`j.reputacion`). Aquí está lo que cuelga de ellos: el trato en los comercios, los testigos y la policía,
los antecedentes penales, el contrato fijo con jefe y evaluaciones, los estudios con título, la empresa que crece, los
créditos, las facturas y los impuestos, las buenas acciones, la extorsión al honrado sin protección y la doble vida.

Los números y las frases están en los datos (vida.json: vida_honrada, titulos, empleos_fijos, mejoras_negocio,
incidencias_trabajo y buenas_acciones). La opción «Nivel de consecuencias» decide cuánto aprieta: apagado deja el juego como
estaba; lo que se elige (un contrato, un título, un crédito) sigue disponible con cualquier nivel. En un servidor en línea
no cuenta nada de lo que mueve dinero.
"""
from .i18n import tr, tr_servidor
import random

from . import gente as G
from .ajustes import Ajustes

NIVELES = ("apagado", "suave", "normal", "exigente")
GRAVEDAD = {1: "leve", 2: "media", 3: "grave"}
COMERCIOS = ("tienda", "comida", "pizzeria", "farmacia", "ropa")
PRECIOS = {"bajos": "bajos", "normales": "normales", "altos": "altos"}

AJ = Ajustes("vida_honrada", {
    # cuánto aprieta cada nivel: tanto por ciento de las penalizaciones respecto al nivel normal
    "factor_suave": 60, "factor_exigente": 150,
    # trato en los comercios
    "rebaja_aprecian": 5, "rebaja_ejemplar": 10, "recargo_evitan": 12, "fiado_aprecian": 60, "fiado_ejemplar": 150, "fiado_dias": 7, "negativa_prob": 30,
    # testigos, vecinos y policía
    "encubren_prob": 35, "encubren_puntos": 2, "delatan_extra": 25, "duda_puntos": 1, "fichado_extra": 10, "control_prob": 15, "control_minutos": 10,
    # la fama en la calle
    "fama_respeto": 20, "fama_descuento": 12, "fama_recargo": 15,
    # antecedentes penales
    "caduca_leve": 10, "caduca_media": 25, "caduca_grave": 50, "servicio_quita": 5, "servicio_horas": 4, "abogado_precio": 1200,
    "chavales_fama": 4, "chavales_horas": 4, "chavales_prestigio": 1,
    # carrera profesional
    "periodo_dias": 7, "meritos_ascenso": 3, "avisos_despido": 3, "nota_buena": 75, "nota_correcta": 50, "nota_floja": 25, "prima_buena": 10,
    "veto_dias": 10, "carta_periodos": 3, "incidencia_prob": 40, "prestigio_periodo": 2, "prestigio_despido": 6, "titulo_prestigio": 4,
    # la empresa
    "empleado_sueldo": 8, "empleado_rinde": 14, "rep_inicial": 50, "rep_factor": 25, "atender_horas": 2, "atender_rep": 4, "abandono_dias": 5, "abandono_baja": 3,
    "encargado_sueldo": 25, "encargado_rep": 1.5, "encargado_tope": 80,
    "precios_bajos_ingreso": 10, "precios_bajos_rep": 1, "precios_altos_ingreso": 15, "precios_altos_rep": 2, "horario_ingreso": 20,
    "tapadera_capacidad": 400, "tapadera_comision": 15, "negro_umbral": 3000, "negro_decae": 4,
    "inspeccion_min": 10, "inspeccion_max": 18, "sancion_pct": 5, "soborno_pct": 3, "soborno_prob": 55, "plazo_asunto": 3,
    # impuestos y facturas
    "impuesto_negocio": 6, "impuesto_casa": 15, "factura_casa": 35, "cobro_dias": 7, "aviso_dias": 2, "recargo": 10, "gracia_dias": 14,
    "impagos_embargo": 3, "embargo_pct": 50,
    # el banco
    "solvencia_prestigio": 50, "solvencia_ingresos": 25, "solvencia_ingresos_tope": 30, "credito_por_punto": 150, "credito_min_solvencia": 25, "credito_cuotas": 8, "interes_bueno": 10, "interes_medio": 16, "interes_malo": 24,
    "hipoteca_entrada": 30, "hipoteca_cuotas": 16, "hipoteca_solvencia": 40, "hipoteca_interes": 14, "cuota_dias": 7, "reintento_dias": 3,
    # la doble vida
    "sospecha_delito": 3, "sospecha_detencion": 25, "sospecha_multa": 8, "sospecha_baja": 2, "sospecha_rumor": 40, "sospecha_prensa": 70,
    "prensa_prestigio": 15, "prensa_soborno": 1500, "abogado_semana": 350, "abogado_factor": 50,
    # la extorsión
    "extorsion_min": 8, "extorsion_max": 14, "extorsion_pct": 12, "extorsion_minimo": 150, "extorsion_semanas": 4, "extorsion_dano_prob": 50,
    "extorsion_dano_dias": 3, "extorsion_dano": 30,
    # hacer el bien
    "buena_min": 360, "buena_max": 720,
    # las bandas con la buena gente (1.7.2): con este prestigio, sus miembros a veces te dejan pasar, y defenderte de ellos no trae guerra
    "banda_prestigio": 40, "banda_deja_prob": 65, "banda_defensa_rep": 1,
    # pareja apta para todos
    "compromiso_afinidad": 85, "compromiso_citas": 6, "boda_dias": 3, "boda_precio": 1500, "boda_prestigio": 5,
}, {
    "caracteres_jefe": ["exigente", "paciente", "sec[o|a]", "campechan[o|a]", "justo"],
    "frases_banda_deja": [tr("{nombre} te mira de arriba abajo y escupe al suelo, pero te deja pasar: en el barrio saben que eres buena gente."),
                          tr("{nombre} se te queda mirando. Alguien le dice algo al oído y se aparta: contigo no va la cosa, mientras no les toques."),
                          tr("{nombre} te reconoce y se encoge de hombros: «Sigue tu camino». No quiere líos con quien no se mete en los suyos.")],
    "frases_chavales": [tr("Pasas {horas} horas con los chavales del barrio: deberes, un partido y una charla de las que no se olvidan. En la calle se habla menos de ti y más de lo que haces. Son las {hora}."), tr("{horas} horas en el local de la ONG con los chicos que tienen la calle demasiado cerca. Les cuentas cómo acaba aquello. Tu fama en la calle baja un poco. Son las {hora}.")],
    "frases_defensa_buena": [tr("Lo has hecho en defensa propia y en el barrio lo saben: su banda no te lo tendrá en cuenta."),
                             tr("Te atacaron primero y hay testigos que lo cuentan así: esto no va a empezar ninguna guerra.")],
    "frases_dos_caminos": [tr("Desde aquí puedes llevar la vida que quieras. La calle: los encargos de tu tía te llevan al Chispas y a negocios cada vez más turbios, que dan dinero rápido y traen a la policía detrás. "
                           "El buen camino: en la Oficina de empleo te espera Aurora, la orientadora, con trabajo, estudios y una historia propia que se hace entera sin cometer un delito. Y nadie te impide llevar las dos. "
                           "Lo tienes todo en el móvil, en Vida, reputación y consecuencias.")],
    "frases_partida_antigua": [tr("Novedad de esta versión: la vida tiene ahora consecuencias. Empiezas en neutro: sin antecedentes por lo hecho hasta hoy. "
                               "Dentro de {dias} días empezarán a llegar facturas de tus casas e impuestos de tus negocios, suaves y siempre con aviso. "
                               "Míralo en el móvil, en Vida, reputación y consecuencias; se ajusta o se apaga en Opciones, en la sección del mismo nombre.")],
    "frases_encubren": [tr("Te han visto, pero aquí te aprecian: los vecinos miran a otro lado."), tr("Una vecina lo ha visto todo y baja la persiana sin decir nada. Por ser tú."),
                        tr("Alguien iba a llamar a la policía y otro le ha dicho que lo deje, que eres de fiar.")],
    "frases_duda": [tr("Un agente te ha visto, te reconoce y lo deja pasar por esta vez."), tr("El agente te mira, niega con la cabeza y sigue su ronda: hoy te da el beneficio de la duda.")],
    "frases_delatan": [tr("Aquí no te quieren: alguien ha llamado a la policía en cuanto te ha visto."), tr("Varios vecinos te señalan a gritos. Lo cuentan todo, y con ganas.")],
    "frases_control": [tr("Un agente te para: «Documentación». Te tiene diez minutos contra la pared, mirando tus papeles, y te deja ir de mala gana."),
                       tr("«Tú, ven aquí». Te registran los bolsillos sin prisa. No encuentran nada y te sueltan con una advertencia.")],
    "frases_fiado": [tr("No te llega, pero te conocen: «Ya me lo pagarás». Te apuntan {euros} euros de fiado."), tr("«Tranquil[o|a], que tú eres de casa». Quedan {euros} euros apuntados en la libreta.")],
    "frases_negativa": [tr("«Aquí no te atendemos. Haz el favor de salir»."), tr("El dependiente se cruza de brazos: «Para ti está cerrado».")],
    "frases_firma": [tr("Firmas el contrato con {empresa}. Tu jef[e|a] es {jefe}, que tiene fama de {caracter}. Empiezas de {puesto}: {cupo} turnos cada {dias} días y {sueldo} euros de nómina por periodo, además de lo que cobras por cada turno."),
                     tr("{jefe}, de {empresa}, te da la mano: «Bienvenid[o|a]». Eres {puesto}. Te piden {cupo} turnos cada {dias} días y te pagan {sueldo} euros de nómina por periodo, aparte de cada turno.")],
    "frases_turno": [tr("Turno apuntado en tu contrato: llevas {hechos} de {cupo} este periodo."), tr("{jefe} anota tu turno: {hechos} de {cupo}.")],
    "frases_falta_turnos": [tr("{jefe} te escribe: «Quedan {dias} días y te faltan {faltan} turnos. No me falles».")],
    "frases_eval_buena": [tr("{jefe}: «Así da gusto. Buen trabajo». Evaluación buena: cobras la nómina, {sueldo} euros, con una prima de {prima}."),
                          tr("Evaluación de {jefe}: buena. «Sigue así y hablaremos de un ascenso». Nómina de {sueldo} euros y {prima} de prima.")],
    "frases_eval_correcta": [tr("Evaluación de {jefe}: correcta. Cobras la nómina, {sueldo} euros."), tr("{jefe}: «Cumples. Ni más ni menos». Nómina de {sueldo} euros.")],
    "frases_eval_floja": [tr("Evaluación de {jefe}: floja. «Esto no es lo que firmamos». Te llevas un aviso, el {avisos} de {tope}, y solo {sueldo} euros de nómina."),
                          tr("{jefe} te llama al despacho: «Has faltado o lo has hecho a medias». Aviso número {avisos} de {tope}. Nómina recortada: {sueldo} euros.")],
    "frases_eval_mala": [tr("Evaluación de {jefe}: muy mala. «No has aparecido». Sanción sin nómina y un aviso: llevas {avisos} de {tope}."),
                         tr("{jefe} no levanta la voz: «Un periodo entero sin dar golpe. Sin sueldo, y a la próxima, a la calle». Aviso {avisos} de {tope}.")],
    "frases_ascenso": [tr("¡Ascenso! {jefe} te ofrece el puesto de {puesto}: más responsabilidad, {cupo} turnos por periodo y {sueldo} euros de nómina."),
                       tr("{jefe}: «Te lo has ganado». Desde hoy eres {puesto}: {sueldo} euros de nómina y {cupo} turnos por periodo.")],
    "frases_ascenso_falta": [tr("{jefe} quiere ascenderte a {puesto}, pero te falta {falta}. El puesto te espera.")],
    "frases_despido": [tr("{jefe} te da una carta: estás despedid[o|a] de {empresa}. Motivo: {motivo}."), tr("«Recoge tus cosas». {empresa} te despide. Motivo: {motivo}.")],
    "frases_aviso_antecedente": [tr("En {empresa} se han enterado de tu problema con la policía. {jefe} te apunta un aviso: llevas {avisos} de {tope}.")],
    "frases_dimision": [tr("Dejas tu puesto en {empresa}. {jefe} te desea suerte."), tr("Presentas la dimisión. {jefe}: «Aquí tienes la puerta abierta».")],
    "frases_carta": [tr("{jefe} te firma una carta de recomendación: te abrirá puertas en tu próximo empleo y en el banco.")],
    "frases_titulo_sesion": [tr("Sesión de {nombre}: llevas {hechas} de {total}. Son las {hora}."), tr("{horas} horas de clase de {nombre}. Te quedan {quedan} sesiones. Son las {hora}.")],
    "frases_titulo": [tr("¡Título conseguido! {nombre}. {abre}"), tr("Te entregan el diploma: {nombre}. {abre}")],
    "frases_atender": [tr("Pasas {horas} horas en {negocio}: atiendes, ordenas y hablas con la clientela. Se nota. Son las {hora}."),
                       tr("Te remangas en {negocio}: {horas} horas detrás del mostrador. Los clientes agradecen ver al dueño. Son las {hora}.")],
    "frases_abandono": [tr("En {negocio} hace días que no te ven. La clientela lo nota y el negocio pierde nombre."), tr("{negocio} va a peor: nadie lo atiende como debe.")],
    "frases_inspeccion_limpia": [tr("Inspección en {negocio}: todo en regla. El inspector firma y se va. El negocio gana nombre."), tr("Han pasado inspección por {negocio}: ni una falta. Así da gusto.")],
    "frases_inspeccion_falta": [tr("Inspección en {negocio}: han encontrado irregularidades. Tienes {dias} días para decidir qué haces; está en el móvil, en Vida, reputación y consecuencias, Asuntos pendientes.")],
    "frases_soborno_ok": [tr("El inspector se guarda el sobre y rompe el acta. Aquí no ha pasado nada."), tr("«Por esta vez». El acta desaparece en su maletín, y el sobre también.")],
    "frases_soborno_mal": [tr("El inspector levanta la vista: «¿Me está usted sobornando?». Llama a la policía. Te cae la sanción, una denuncia y sale en el periódico.")],
    "frases_cobro_aviso": [tr("Dentro de {dias} días te pasan las facturas y los impuestos: unos {euros} euros. Se cobran solos, primero de tu cuenta del banco.")],
    "frases_cobro": [tr("Facturas e impuestos del periodo: {euros} euros. {detalle}."), tr("Te cobran {euros} euros de facturas e impuestos. {detalle}.")],
    "frases_impago": [tr("No tienes para las facturas y los impuestos: faltan {falta} euros. Quedan a deber con un recargo. Si se repite, te embargarán parte de lo que ganes.")],
    "frases_embargo": [tr("Embargo: debes {euros} euros. Desde hoy se quedan la mitad de tus nóminas y de lo que den tus negocios hasta saldar la deuda, y los vecinos lo comentan.")],
    "frases_embargo_fin": [tr("Deuda saldada: se levanta el embargo.")],
    "frases_cuota_aviso": [tr("Dentro de {dias} días vence una cuota de tu {tipo}: {euros} euros.")],
    "frases_cuota": [tr("Cuota de tu {tipo} pagada: {euros} euros. Te quedan {quedan}."), tr("El banco te cobra la cuota de tu {tipo}, {euros} euros. Quedan {quedan}.")],
    "frases_cuota_fin": [tr("Última cuota pagada: tu {tipo} está liquidado. El banco toma nota de que cumples.")],
    "frases_cuota_impago": [tr("No has podido pagar la cuota de tu {tipo}: {euros} euros. Te ponen un recargo y lo vuelven a intentar en {dias} días. Llevas {impagos} impagos; con {tope} hay embargo.")],
    "frases_rumor": [tr("Empieza a correr el rumor de que llevas una doble vida. Mientras dure, te costará más ganarte a los vecinos.")],
    "frases_prensa_aviso": [tr("Un periodista prepara un reportaje sobre tu otra vida. Tienes {dias} días para decidir qué haces; está en el móvil, en Vida, reputación y consecuencias, Asuntos pendientes.")],
    "frases_prensa": [tr("Sale en el periódico: «La doble vida de {nombre}». Los vecinos ya saben quién eres de noche."), tr("El Faro lo publica en portada: {nombre} no es quien decía ser.")],
    "frases_prensa_callada": [tr("El periodista coge el sobre y el reportaje se queda en un cajón."), tr("«Nunca hemos hablado». El reportaje no saldrá.")],
    "frases_prensa_abogado": [tr("Tu abogado hace dos llamadas y el periódico se lo piensa mejor: el reportaje no sale.")],
    "frases_extorsion": [tr("Dos de {banda} han pasado por {negocio}: quieren {euros} euros cada semana «por protección». Tienes {dias} días para contestar; está en el móvil, en Vida, reputación y consecuencias, Asuntos pendientes.")],
    "frases_extorsion_vecino": [tr("Un vecino te avisa en voz baja: los de {banda} andan preguntando por tu negocio.")],
    "frases_extorsion_pago": [tr("Pagas. {banda} cobrará {euros} euros cada semana durante {semanas} semanas, y tu negocio no tendrá problemas.")],
    "frases_extorsion_denuncia": [tr("Denuncias la extorsión en comisaría. La policía pone vigilancia y los de {banda} no vuelven. Los vecinos te lo agradecen."),
                                  tr("La inspectora te escucha y actúa: dos detenidos de {banda}. En el barrio se habla bien de ti.")],
    "frases_extorsion_denuncia_mal": [tr("Denuncias la extorsión, pero la policía no te hace mucho caso. Esa noche te rompen el escaparate de {negocio}: unos días de pérdidas.")],
    "frases_extorsion_plantas": [tr("Les dices que no, mirándoles a los ojos. Saben quién eres en la calle y no insisten.")],
    "frases_extorsion_nada": [tr("Les dices que no. Por esta vez se van sin más."), tr("No pagas, y no pasa nada. De momento.")],
    "frases_extorsion_dano": [tr("Les dices que no. Esa noche arde un contenedor delante de {negocio} y aparece el cierre reventado: unos días de pérdidas.")],
    "frases_buena_nada": [tr("Sigues tu camino.")],
    "frases_abogado": [tr("Contratas a un abogado de confianza por {euros} euros a la semana. Mientras le pagues, lo que se sepa de ti hará la mitad de daño y él se encargará de la prensa.")],
    "frases_abogado_fin": [tr("No has podido pagar a tu abogado y deja de llevar tus asuntos.")],
    "frases_compromiso": [tr("{n} se queda sin palabras un segundo. Luego dice que sí. Estáis prometidos."), tr("«Sí. Claro que sí». {n} te abraza. Desde hoy estáis prometidos.")],
    "frases_compromiso_pronto": [tr("{n} te coge la mano: «Todavía no. Dame tiempo». Necesitáis más confianza y más tiempo juntos.")],
    "frases_boda": [tr("Una boda sencilla: la familia, cuatro amigos y la tía Encarna llorando en primera fila. {n} y tú ya estáis casados."),
                    tr("Firmáis en el ayuntamiento y lo celebráis con una comida larga. {n} lleva el anillo y no deja de mirarlo. Estáis casados.")],
}, cero=("banda_deja_prob", "banda_defensa_rep"))

# Lo que hay que cumplir para una misión con «requiere_vida»: clave -> (¿se cumple?, lo que falta dicho)
REQUISITOS_VIDA = {
    "contrato": (lambda p, v: bool(p.j.contrato), lambda p, v: tr("tener un contrato fijo, que se firma en una oficina de empleo")),
    "turnos": (lambda p, v: p.j.stats.get("turnos_contrato", 0) >= v, lambda p, v: tr('trabajar {int} turnos con tu contrato; llevas {get}').format(int=(int(v)), get=(p.j.stats.get('turnos_contrato', 0)))),
    "titulos": (lambda p, v: len(p.hon_titulos()) >= v, lambda p, v: tr("sacarte un título en una academia") if v <= 1 else tr('tener {int} títulos').format(int=(int(v)))),
    "prestigio": (lambda p, v: p.j.ciudadania >= v, lambda p, v: tr('más prestigio entre los vecinos: {int} de {int2}').format(int=(int(p.j.ciudadania)), int2=(int(v)))),
    "negocios": (lambda p, v: len(p.negocios_tuyos()) >= v, lambda p, v: tr("tener un negocio propio") if v <= 1 else tr('tener {int} negocios').format(int=(int(v)))),
    "sin_antecedentes": (lambda p, v: not p.hon_antecedentes(), lambda p, v: tr("no tener antecedentes penales en vigor")),
    # contratos del tablón cumplidos (issue 33): en total o, con «tablon», solo los de ese sitio o ese tipo de sitio
    "contratos": (lambda p, v, t=None: p.contratos_cumplidos(t) >= v,
                  lambda p, v, t=None: (tr('cumplir {int} contratos del tablón de {sitio}; llevas {hechos}').format(int=(int(v)), sitio=(p.tablon_txt(t)), hechos=(p.contratos_cumplidos(t))) if t
                                        else tr('cumplir {int} contratos del tablón; llevas {hechos}').format(int=(int(v)), hechos=(p.contratos_cumplidos(t))))),
}
# Lo que no se cuenta: matiza a otro requisito
MATICES_VIDA = ("tablon",)


def _n(d, k, defecto=0.0):
    try:
        return float(d.get(k, defecto))
    except (TypeError, ValueError):
        return float(defecto)


class Honrado:
    """Mixin de Partida."""

    # ------------------------------------------------------------------ estado y niveles
    def hon(self):
        """Lo suelto del sistema, guardado con el jugador. Se crea la primera vez, con el periodo de gracia."""
        h = self.j.honra
        if not h.get("v"):
            gracia = self.dia + AJ.entero("gracia_dias")
            h.update({"v": 1, "gracia": gracia, "cobro": gracia, "sospecha": 0.0, "negro": 0.0, "fiado": 0, "deuda": 0, "impagos": 0, "embargo": 0,
                      "asuntos": [], "cartas": [], "vetos": {}, "caja": 0})
        return h

    def hon_nivel(self):
        """0 apagado, 1 suave, 2 normal, 3 exigente. En un servidor en línea, siempre apagado."""
        if self.en_servidor:
            return 0
        v = self.cfg["consecuencias"]
        return NIVELES.index(v) if v in NIVELES else 1

    def hon_f(self):
        """Cuánto aprietan las penalizaciones con el nivel elegido: 1 es lo normal."""
        return {0: 0.0, 1: AJ("factor_suave") / 100.0, 3: AJ("factor_exigente") / 100.0}.get(self.hon_nivel(), 1.0)

    def sv_honrado(self, que):
        """En un servidor: ¿lleva él esa parte de la vida honrada? «nominas» (los contratos fijos, que paga el servidor) o
        «trato_prestigio» (las rebajas de las tiendas). Un servidor anterior a la 1.7.1 no lleva ninguna."""
        return bool(self.en_servidor and ((getattr(self, "sv", None) or {}).get("info") or {}).get(que))

    def hon_bloqueo(self, que=""):
        """Por qué no se puede usar lo que mueve dinero (contratos, créditos, empresa): en un servidor lo arbitra él.
        Los contratos fijos sí se pueden donde el servidor paga las nóminas; lo demás, en ninguno."""
        if not self.en_servidor:
            return ""
        if not self.sv_honrado("nominas"):
            return tr("En un servidor en línea no hay contratos fijos, créditos, impuestos ni dirección de negocios: el dinero lo arbitra el servidor.")
        if que == "contrato":
            return ""
        return tr("En un servidor en línea no hay créditos, impuestos ni dirección de negocios: el dinero lo arbitra el servidor. Sí hay contratos fijos, con la nómina que paga el servidor.")

    def hon_impuestos(self):
        return bool(self.cfg["impuestos_facturas"]) and not self.en_servidor

    def hon_con_antecedentes(self):
        """En un servidor solo se llevan donde hay contratos fijos, que es para lo único que cuentan allí: son del personaje."""
        return bool(self.cfg["antecedentes"]) and (not self.en_servidor or self.sv_honrado("nominas"))

    def hon_buena_gente(self):
        """¿Tienes prestigio para que las bandas te traten como buena gente? Solo con la defensa propia encendida."""
        return bool(self.cfg["defensa_propia"]) and self.j.ciudadania >= AJ("banda_prestigio")

    def hon_banda_deja_pasar(self, p):
        """Un miembro de una banda te acaba de ver en su barrio. Con prestigio de buena gente, y si no le has tocado, a veces
        te deja pasar. Se decide una vez por persona: si le provocas después, va a por ti como siempre. True si te deja."""
        if not self.hon_buena_gente() or getattr(p, "provocado", False) or p.tag not in (None, "evento"):
            return False
        if getattr(p, "deja_pasar", None) is None:
            p.deja_pasar = random.random() * 100 < AJ("banda_deja_prob")
            if p.deja_pasar:
                self.decir(AJ.frase("frases_banda_deja", nombre=p.nombre))
        return bool(p.deja_pasar)

    def hon_baja_defensa(self, p, banda):
        """Has tumbado en defensa propia a uno de una banda que te atacó primero. Pierdes poca reputación con su banda y,
        siendo buena gente, ninguna, y no cuenta para que empiece una guerra de barrio. True si no cuenta para la guerra."""
        if self.hon_buena_gente():
            if not getattr(self, "_hon_defensa_dicha", False):
                self._hon_defensa_dicha = True
                self.decir(AJ.frase("frases_defensa_buena"))
            return True
        if banda:
            self.cambiar_rep_banda(banda, -AJ.entero("banda_defensa_rep"))
        return False

    def hon_abs(self):
        return self.dia * 1440.0 + self.reloj

    def hon_tramo(self):
        """El prestigio en cuatro tramos: 0 te evitan, 1 uno más, 2 te aprecian, 3 ejemplar."""
        c = self.j.ciudadania
        return 0 if c < 10 else 1 if c < 40 else 2 if c < 75 else 3

    def hon_decir(self, texto, sonido=None):
        if sonido:
            self.son(sonido, cat="interfaz")
        self.decir(texto)

    def honrado_iniciar(self):
        self._local = None                    # el comercio en el que estás dentro: para el fiado
        self._hon_cargada = False
        self.t_honrado = 20.0

    # ------------------------------------------------------------------ cómo te ven: comercios, testigos y policía
    def hon_trato(self, categoria=""):
        """Multiplicador de precio en los comercios según cómo te ven los vecinos. En un servidor que lo tenga puesto vale
        para todos por igual, como con el nivel suave, tengas la opción que tengas: lo decide el servidor, no cada juego."""
        if self.en_servidor:
            if not self.sv_honrado("trato_prestigio"):
                return 1.0
            f = AJ("factor_suave") / 100.0
        elif not self.hon_nivel():
            return 1.0
        else:
            f = self.hon_f()
        t = self.hon_tramo()
        pct = AJ("recargo_evitan") * f if t == 0 else -AJ("rebaja_aprecian") if t == 2 else -AJ("rebaja_ejemplar") if t == 3 else 0.0
        return round(1.0 + pct / 100.0, 3)

    def hon_fama_factor(self):
        """Multiplicador de lo que cobra la gente de la calle por trabajar contigo: menos con fama, más si nadie te conoce."""
        if not self.hon_nivel():
            return 1.0
        r = self.j.reputacion
        if r < 5:
            return round(1.0 + AJ("fama_recargo") * self.hon_f() / 100.0, 3)
        return round(1.0 - min(AJ("fama_descuento"), r * AJ("fama_descuento") / 50.0) / 100.0, 3)

    def hon_fiado_limite(self):
        t = self.hon_tramo()
        return AJ.entero("fiado_ejemplar") if t == 3 else AJ.entero("fiado_aprecian") if t == 2 else 0

    def hon_fiar(self, precio):
        """No te llega en un comercio donde te aprecian: te lo apuntan. Devuelve si se ha fiado."""
        j = self.j
        l = getattr(self, "_local", None)
        if not self.hon_nivel() or l is None or l.tipo not in COMERCIOS or j.estrellas:
            return False
        h = self.hon()
        falta = int(precio - j.dinero)
        if falta <= 0 or h["fiado"] + falta > self.hon_fiado_limite():
            return False
        if not h["fiado"]:
            h["fiado_dia"] = self.dia
        h["fiado"] += falta
        j.dinero = 0
        self.son("caja", cat="interfaz", vol=0.6)
        self.decir(AJ.frase("frases_fiado", euros=falta) + tr(' Debes {fiado} de fiado: se paga en el móvil, en Vida, reputación y consecuencias.').format(fiado=(h['fiado'])))
        return True

    def hon_pagar_fiado(self):
        h = self.hon()
        if not h["fiado"]:
            return self.decir(tr("No debes nada de fiado."), True)
        if self.pagar_sin_fiar(h["fiado"]):
            self.decir(tr('Pagas los {fiado} euros que debías de fiado. Cuentas claras.').format(fiado=(h['fiado'])), True)
            h["fiado"] = 0
            self.cambiar_ciudadania(0.5)

    def pagar_sin_fiar(self, n):
        local, self._local = getattr(self, "_local", None), None
        try:
            return self.pagar(n)
        finally:
            self._local = local

    def hon_negativa(self, l):
        """Con el nivel exigente, donde te evitan, algún comercio se niega a atenderte ese día. Devuelve si te echan."""
        if self.hon_nivel() < 3 or l.tipo not in COMERCIOS or self.hon_tramo() != 0:
            return False
        if random.Random(f"{self.j.semilla}-{self.dia}-veto-{l.id}").random() * 100 >= AJ("negativa_prob"):
            return False
        self.app.son("error")
        self.decir(f"{l.nombre}. " + AJ.frase("frases_negativa") + tr(" Los vecinos te evitan: mañana, quizá."), True)
        return True

    def hon_delito(self, puntos, policia, forzado=False):
        """Lo que hacen los testigos según cómo te ven. Devuelve los puntos que cuentan; cero si lo dejan pasar.
        Un delito que el juego da por visto pase lo que pase (`forzado`) no lo tapa nadie."""
        if not self.hon_nivel() or puntos <= 0:
            return puntos
        j, h, t = self.j, self.hon(), self.hon_tramo()
        limpio = not self.hon_antecedentes() and not forzado
        if not policia and t >= 2 and puntos <= AJ("encubren_puntos") and not j.estrellas and random.random() * 100 < AJ("encubren_prob") * (1.0 if t == 3 else 0.5):
            self._hon_frase_rara("frases_encubren")
            return 0.0
        if policia and t >= 2 and limpio and puntos <= AJ("duda_puntos") and not j.estrellas and h.get("duda_dia") != self.dia:
            h["duda_dia"] = self.dia
            self.decir(AJ.frase("frases_duda"))
            return 0.0
        f = self.hon_f()
        if t == 0:
            puntos *= 1.0 + AJ("delatan_extra") * f / 100.0
            if not policia:
                self._hon_frase_rara("frases_delatan")
        peso = self.hon_peso()
        if peso:
            puntos *= 1.0 + min(60.0, AJ("fichado_extra") * peso) * f / 100.0
        self.hon_sospechar(puntos * AJ("sospecha_delito"))
        return puntos

    def _hon_frase_rara(self, lista, cada=45.0):
        """Una frase de ambiente que no se repite a cada delito."""
        ultimo = self.__dict__.setdefault("_hon_frases", {})
        if self.t - ultimo.get(lista, -999.0) >= cada:
            ultimo[lista] = self.t
            self.decir(AJ.frase(lista))

    def _hon_control(self):
        """Con mala fama entre los vecinos o con antecedentes, la policía te para de vez en cuando (nivel normal o exigente)."""
        j, h = self.j, self.hon()
        if self.hon_nivel() < 2 or h.get("control_dia") == self.dia or j.veh or j.estrellas or self.mision or self.trabajo or self.mundo.tipo == "mar":
            return
        if self.hon_tramo() != 0 and self.hon_peso() < 2:
            return
        x, y = self.pos()
        if not any(p.tipo == "policia" and not p.muerto and p.dist(x, y) < 25 for p in self.personas) or j.policia.get("alta"):
            return
        h["control_dia"] = self.dia
        if random.random() * 100 < AJ("control_prob") * self.hon_f():
            self.reloj += AJ("control_minutos")
            self.son("emisora", cat="interfaz", vol=0.5)
            self.decir(AJ.frase("frases_control"))

    # ------------------------------------------------------------------ antecedentes penales
    def hon_antecedentes(self):
        """Los antecedentes en vigor, del más grave al más leve."""
        if not self.hon_con_antecedentes():
            return []
        return sorted((a for a in self.j.antecedentes if a.get("c", 0) > self.dia), key=lambda a: (-a["g"], a["d"]))

    def hon_peso(self):
        """Cuánto pesan tus antecedentes: 1 cada leve, 2 cada medio, 4 cada grave."""
        return sum({1: 1, 2: 2}.get(a["g"], 4) for a in self.hon_antecedentes())

    def hon_graves(self):
        return any(a["g"] >= 3 for a in self.hon_antecedentes())

    def hon_antecedente(self, gravedad, texto):
        """Apunta una condena. Trae consecuencias en el trabajo y en lo que se sabe de ti."""
        if not self.hon_con_antecedentes():
            return None
        g = max(1, min(3, int(gravedad)))
        dias = AJ.entero({1: "caduca_leve", 2: "caduca_media"}.get(g, "caduca_grave"))
        a = {"d": self.dia, "g": g, "t": texto, "c": self.dia + dias}
        self.j.antecedentes.append(a)
        self.j.stats["antecedentes"] = self.j.stats.get("antecedentes", 0) + 1
        self.decir(tr('Queda apuntado en tus antecedentes penales: {texto}, falta {v}. Caduca en {dias} días si no hay más.').format(texto=(texto), v=(GRAVEDAD[g]), dias=(dias)))
        self.hon_sospechar(AJ("sospecha_multa") if g == 1 else AJ("sospecha_detencion"))
        self._hon_trabajo_y_antecedente(a)
        return a

    def hon_antecedente_txt(self, a):
        quedan = a["c"] - self.dia
        return tr('Día {d}: {t}. Falta {v}. Caduca en {quedan} {v2}').format(d=(a['d']), t=(a['t']), v=(GRAVEDAD[a['g']]), quedan=(quedan), v2=(tr('día') if quedan == 1 else tr('días'))) + (tr(". Ya rebajada por tu abogado") if a.get("ab") else "")

    def hon_antecedentes_txt(self):
        if not self.hon_con_antecedentes():
            return tr("Los antecedentes penales están desactivados en Opciones.") if not self.en_servidor else tr("En un servidor en línea no se llevan antecedentes.")
        v = self.hon_antecedentes()
        if not v:
            return tr("No tienes antecedentes penales en vigor.")
        return tr('Tienes {len} {v} en vigor; el más grave, {v2}.').format(len=(len(v)), v=(tr('antecedente') if len(v) == 1 else tr('antecedentes')), v2=(GRAVEDAD[v[0]['g']]))

    def hon_servicio_comunidad(self):
        """Cuatro horas de servicios a la comunidad: acortan el antecedente más grave. Una vez al día."""
        h = self.hon()
        v = self.hon_antecedentes()
        if not v:
            return self.decir(tr("No tienes antecedentes que atenuar."), True)
        if h.get("servicio_dia") == self.dia:
            return self.decir(tr("Hoy ya has hecho servicios a la comunidad. Vuelve mañana."), True)
        if self.j.estrellas:
            self.app.son("error")
            return self.decir(tr("Con la policía buscándote, no."), True)
        h["servicio_dia"] = self.dia
        horas = AJ.entero("servicio_horas")
        self.pasar_horas(horas)
        a = v[0]
        a["c"] = max(self.dia, a["c"] - AJ.entero("servicio_quita"))
        self.j.stats["servicios_comunidad"] = self.j.stats.get("servicios_comunidad", 0) + 1
        self.son("lugar_ong", cat="interfaz")
        self.cambiar_ciudadania(1.5)
        resto = a["c"] - self.dia
        self.decir(tr('{horas} horas limpiando parques y pintando bancos. ').format(horas=(horas)) + (tr('A tu antecedente más grave le quedan {resto} días.').format(resto=(resto)) if resto > 0 else tr("Con esto, tu antecedente más grave queda cancelado."))
                   + tr(' Son las {hora_txt}.').format(hora_txt=(self.hora_txt())), True)

    def hon_chavales(self):
        """Bajar la fama en la calle sin tocar el prestigio ni el empleo: unas horas con los chavales del barrio en la ONG,
        para que no acaben en la calle. Una vez al día, y sin que te busque la policía (issue 28)."""
        h, j = self.hon(), self.j
        if j.reputacion <= 0:
            return self.decir(tr("En la calle no te conoce nadie: no hay fama que bajar."), True)
        if h.get("chavales_dia") == self.dia:
            return self.decir(tr("Hoy ya has estado con los chavales. Vuelve mañana."), True)
        if j.estrellas:
            self.app.son("error")
            return self.decir(tr("Con la policía buscándote, no."), True)
        h["chavales_dia"] = self.dia
        horas = AJ.entero("chavales_horas")
        self.pasar_horas(horas)
        self.son("lugar_ong", cat="interfaz")
        j.stats["chavales"] = j.stats.get("chavales", 0) + 1
        self.decir(AJ.frase("frases_chavales", horas=horas, hora=self.hora_txt()), True)
        self.cambiar_reputacion(-AJ("chavales_fama"))
        self.cambiar_ciudadania(AJ("chavales_prestigio"))

    def hon_abogado_precio(self, a):
        return AJ.entero("abogado_precio") * a["g"]

    def hon_rebajar(self, a):
        """Un abogado recurre una condena: baja un grado, o desaparece si era leve. Una vez por antecedente."""
        if a.get("ab"):
            return self.decir(tr("Ese antecedente ya lo recurrió tu abogado: no se puede rebajar más."), True)
        if not self.pagar_sin_fiar(self.hon_abogado_precio(a)):
            return None
        a["ab"] = True
        if a["g"] <= 1:
            a["c"] = self.dia
            self.decir(tr("Tu abogado consigue que se archive: ese antecedente desaparece."), True)
        else:
            a["g"] -= 1
            a["c"] = min(a["c"], self.dia + AJ.entero({1: "caduca_leve", 2: "caduca_media"}[a["g"]]))
            self.decir(tr('Tu abogado recurre y gana: la falta pasa a ser {v} y caduca en {v2} días.').format(v=(GRAVEDAD[a['g']]), v2=(a['c'] - self.dia)), True)

    def _hon_dia_antecedentes(self):
        j = self.j
        if not j.antecedentes:
            return
        caducados = [a for a in j.antecedentes if a.get("c", 0) <= self.dia]
        if caducados:
            j.antecedentes = [a for a in j.antecedentes if a.get("c", 0) > self.dia]
            if self.hon_con_antecedentes():
                self.hon_decir(tr("Ha caducado un antecedente penal.") if len(caducados) == 1 else tr('Han caducado {len} antecedentes penales.').format(len=(len(caducados)))
                               + ("" if j.antecedentes else tr(" Tu ficha vuelve a estar limpia.")), "prestigio")

    # ------------------------------------------------------------------ estudios con título
    def hon_titulos(self):
        """Los títulos que ya tienes: sus identificadores."""
        return [k for k, v in self.j.titulos.items() if isinstance(v, dict) and v.get("ok")]

    def hon_titulo(self, ident):
        return next((t for t in self.datos.get("titulos", []) if t.get("id") == ident), None)

    def hon_titulo_nombre(self, ident):
        t = self.hon_titulo(ident)
        return str(t["nombre"]) if t else str(ident)

    def hon_titulo_motivo(self, t):
        """Por qué no puedes matricularte o seguir, o vacío."""
        j = self.j
        if t["id"] in self.hon_titulos():
            return tr("Ya tienes ese título.")
        if t.get("requiere") and t["requiere"] not in self.hon_titulos():
            return tr('Antes hay que tener el título de {hon_titulo_nombre}.').format(hon_titulo_nombre=(self.hon_titulo_nombre(t['requiere'])))
        if j.ciudadania < _n(t, "prestigio") and not self.cheat_on("cheat_admision"):
            return tr('No te admiten todavía: piden que los vecinos hablen mejor de ti. Tu prestigio es {int} y hacen falta {int2}.').format(int=(int(j.ciudadania)), int2=(int(_n(t, 'prestigio'))))
        if self.hon().get("estudio_dia") == self.dia and not self.cheat_on("cheat_estudiar"):
            return tr("Hoy ya has ido a clase del título. Una sesión al día.")
        if j.estrellas and not self.cheat_on("cheat_admision"):
            return tr("Con la policía buscándote no puedes sentarte en clase.")
        return ""

    def hon_estudiar(self, t):
        """Una sesión de un título. Al completar las sesiones, el título es tuyo."""
        j = self.j
        motivo = self.hon_titulo_motivo(t)
        if motivo:
            self.app.son("error")
            return self.decir(motivo, True)
        if not self.pagar_sin_fiar(int(_n(t, "precio"))):
            return None
        self.hon()["estudio_dia"] = self.dia
        e = j.titulos.setdefault(t["id"], {"s": 0, "ok": 0})
        e["s"] += 1
        horas, total = int(_n(t, "horas", 3)), int(_n(t, "sesiones", 4))
        self.pasar_horas(horas)
        if e["s"] < total:
            self.son("diploma", cat="interfaz")
            return self.decir(AJ.frase("frases_titulo_sesion", nombre=t["nombre"], hechas=e["s"], total=total, quedan=total - e["s"], horas=horas, hora=self.hora_txt()), True)
        e["ok"] = self.dia
        j.stats["titulos"] = j.stats.get("titulos", 0) + 1
        self.son("titulo", cat="interfaz")
        self.cambiar_ciudadania(AJ("titulo_prestigio"))
        self.cambiar_animo(8)
        self.decir(AJ.frase("frases_titulo", nombre=t["nombre"], abre=t.get("abre", "")) + self.hon_titulo_donde(t), True)

    def hon_titulo_donde(self, t):
        """Dónde sirve un título: en qué contratos fijos hace falta para ascender, y dónde se firman. Antes el título
        decía lo que abría y no dónde, y había quien buscaba un negocio que abrir."""
        empresas = []
        for c in self.hon_empleos():
            if any(isinstance(q, dict) and q.get("titulo") == t.get("id") for q in c.get("puestos", [])):
                nombre = str(c.get("empresa") or c.get("nombre") or "")
                if nombre and nombre not in empresas:
                    empresas.append(nombre)
        if not empresas:
            return ""
        lista = empresas[0] if len(empresas) == 1 else ", ".join(empresas[:-1]) + tr(" y ") + empresas[-1]
        return (tr(' Sirve en el contrato fijo de {lista}, que se firma en la Oficina de empleo. Si ya trabajas allí, el ascenso llega con las buenas evaluaciones; si no, empiezas desde abajo y subes con él.').format(lista=(lista)))

    # ------------------------------------------------------------------ carrera profesional: el contrato fijo
    def hon_empleos(self):
        return [c for c in self.datos.get("empleos_fijos", []) if isinstance(c, dict) and c.get("puestos")]

    def hon_empleo(self, ident=None):
        ident = ident or self.j.contrato.get("empleo")
        return next((c for c in self.hon_empleos() if c.get("id") == ident), None)

    def hon_puesto(self, c=None, k=None):
        c = c or self.hon_empleo()
        if not c:
            return None
        k = int(self.j.contrato.get("puesto", 0)) if k is None else k
        return c["puestos"][max(0, min(len(c["puestos"]) - 1, k))]

    def hon_puesto_falta(self, puesto):
        """Lo que te falta para ocupar un puesto, dicho; vacío si lo cumples."""
        faltas = []
        if puesto.get("titulo") and puesto["titulo"] not in self.hon_titulos():
            faltas.append(tr('el título de {hon_titulo_nombre}').format(hon_titulo_nombre=(self.hon_titulo_nombre(puesto['titulo']))))
        if self.j.ciudadania < _n(puesto, "prestigio"):
            faltas.append(tr('más prestigio entre los vecinos, {int} y tienes {int2}').format(int=(int(_n(puesto, 'prestigio'))), int2=(int(self.j.ciudadania))))
        return tr(" y ").join(faltas)

    def hon_firma_motivo(self, c):
        j, h = self.j, self.hon()
        if self.hon_bloqueo("contrato"):
            return self.hon_bloqueo("contrato")
        if j.contrato:
            return tr("Ya tienes un contrato fijo. Para firmar otro, deja antes el que tienes.")
        if j.estrellas:
            return tr("Con la policía buscándote no te contratan.")
        if j.policia.get("alta"):
            return tr("Eres agente de policía: no puedes firmar otro contrato mientras lleves la placa.")
        if int(h["vetos"].get(c["id"], 0)) > self.dia:
            return tr('En {empresa} no quieren saber de ti hasta el día {int}.').format(empresa=(c['empresa']), int=(int(h['vetos'][c['id']])))
        if c.get("confianza") and (self.hon_graves() or (self.hon_nivel() >= 2 and self.hon_peso())):
            return tr("Es un empleo de confianza y piden el certificado de antecedentes penales. Con los que tienes en vigor, no te contratan.")
        if self.hon_graves() and self.hon_nivel() >= 3:
            return tr("Con antecedentes graves en vigor no te contrata nadie de fijo.")
        falta = self.hon_puesto_falta(c["puestos"][0])
        return tr('Para entrar te falta {falta}.').format(falta=(falta)) if falta else ""

    def hon_firmar(self, c):
        motivo = self.hon_firma_motivo(c)
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        j, h = self.j, self.hon()
        g = random.choice("hm")
        jefe = f"{random.choice(G.nombres(g))} {random.choice(G.lista('apellidos'))}"
        from . import genero
        caracter = genero.resolver(random.choice(AJ.lista("caracteres_jefe")), g)
        k = 0
        if c["id"] in h["cartas"] or h["cartas"]:                # con carta de recomendación entras un puesto más arriba, si cumples lo que pide
            if len(c["puestos"]) > 1 and not self.hon_puesto_falta(c["puestos"][1]):
                k = 1
            h["cartas"] = []
        j.contrato = {"empleo": c["id"], "puesto": k, "jefe": jefe, "caracter": caracter, "desde": self.dia, "fin": self.dia + AJ.entero("periodo_dias"),
                      "turnos": 0, "calidad": [], "avisos": 0, "meritos": 0, "periodos": 0}
        p = c["puestos"][k]
        self._hon_sv_contrato("firmar", empleo=c["id"], puesto=k)       # en un servidor, la nómina la paga él: que lo sepa
        self.son("mision_ok", cat="interfaz")
        self.decir(AJ.frase("frases_firma", empresa=c["empresa"], jefe=jefe, caracter=caracter, puesto=p["nombre"], cupo=int(_n(p, "cupo", 3)),
                            dias=AJ.entero("periodo_dias"), sueldo=int(_n(p, "sueldo"))) + (tr(" Tu carta de recomendación te ha ahorrado el primer escalón.") if k else ""), True)
        return True

    def hon_cuenta_turno(self, clave):
        """¿Ese trabajo cuenta como turno de tu contrato? clave: «jornada:camarero» u «oficio:taxi»."""
        c = self.hon_empleo() if self.j.contrato else None
        return bool(c) and clave in (c.get("cuenta") or [])

    def hon_turno(self, clave):
        """Has hecho un turno o un servicio: si es de tu contrato, se apunta, con su calidad."""
        j = self.j
        if not j.contrato or (self.en_servidor and not self.sv_honrado("nominas")) or not self.hon_cuenta_turno(clave):
            return
        ct = j.contrato
        c, p = self.hon_empleo(), self.hon_puesto()
        if clave.startswith("oficio:"):                          # con vehículo, tres servicios hacen un turno
            ct["servicios"] = int(ct.get("servicios", 0)) + 1
            if ct["servicios"] % 3:
                return self.decir(tr('Servicio apuntado: {v} de 3 para completar un turno de tu contrato.').format(v=(ct['servicios'] % 3)))
        calidad = 60 + (j.animo - 50) * 0.3 + random.uniform(-12, 12) + (8 if p.get("titulo") else 0) + min(10, ct["periodos"])
        if self.vida_realista() and (j.hambre > 70 or j.sueno > 70 or j.sed > 70):
            calidad -= 15
        if self.sucio():                                         # sin ducharte, tu jefe lo nota (necesidades.py)
            from .necesidades import AJ as NEC
            calidad -= NEC("turno_sucio")
        ct["calidad"].append(max(0.0, min(100.0, calidad)))
        ct["turnos"] += 1
        self._hon_sv_contrato("turno")                                # en un servidor, los turnos que valen para la nómina los cuenta él
        j.stats["turnos_contrato"] = j.stats.get("turnos_contrato", 0) + 1
        self.decir(AJ.frase("frases_turno", jefe=ct["jefe"], hechos=ct["turnos"], cupo=int(_n(p, "cupo", 3))))
        if p.get("mando") and random.random() * 100 < AJ("incidencia_prob"):
            self._hon_incidencia(c, ct)

    def _hon_incidencia(self, c, ct):
        """Un puesto con responsabilidad trae decisiones: lo que elijas cuenta en la evaluación."""
        lista = [x for x in self.datos.get("incidencias_trabajo", []) if isinstance(x, dict) and x.get("opciones")]
        if not lista:
            return
        inc = random.choice(lista)
        from .menus import Menu, Opcion

        def elegir(o):
            def f():
                self.app.cerrar(m)
                if self.j.contrato is ct and ct["calidad"]:
                    ct["calidad"][-1] = max(0.0, min(100.0, ct["calidad"][-1] + _n(o, "calidad")))
                self.decir(str(o.get("dice", "")), True)
            return f
        self.app.son("notificacion")
        m = Menu(self.app, tr('Tu puesto tiene responsabilidad. {texto}').format(texto=(inc['texto'])), [Opcion(str(o["texto"]), elegir(o), ayuda=o.get("ayuda")) for o in inc["opciones"]],
                 escapable=False, intro=tr("Lo que decidas cuenta en tu evaluación. F1 explica cada opción"))
        self.app.abrir(m)

    def hon_contrato_txt(self):
        j = self.j
        ct = j.contrato
        if not ct:
            return tr("No tienes contrato fijo: trabajas por tu cuenta, cuando quieres.")
        c, p = self.hon_empleo(), self.hon_puesto()
        if not c:
            return tr("Tu contrato es de una empresa que ya no existe en estos datos.")
        quedan = max(0, ct["fin"] - self.dia)
        return (tr('{capitalize} en {empresa}. Jef[e|a]: {jefe}. Este periodo llevas {turnos} de {int} turnos y quedan {quedan} {v}. Nómina: {int2} euros por periodo. Avisos: {avisos} de {entero}').format(capitalize=(p['nombre'].capitalize()), empresa=(c['empresa']), jefe=(ct['jefe']), turnos=(ct['turnos']), int=(int(_n(p, 'cupo', 3))), quedan=(quedan), v=(tr('día') if quedan == 1 else tr('días')), int2=(int(_n(p, 'sueldo'))), avisos=(ct['avisos']), entero=(AJ.entero('avisos_despido'))))

    def hon_sueldo_semana(self):
        p = self.hon_puesto() if self.j.contrato else None
        return int(_n(p, "sueldo")) if p else 0

    def hon_ingresar(self, n, texto=None):
        """Un ingreso legal por el banco (nóminas). Si hay embargo, se queda su parte."""
        j = self.j
        n = int(n)
        if n <= 0:
            return 0
        n -= self._hon_embargar(n)
        j.banco += n
        j.stats["dinero_ganado"] += n
        self.son("dinero", cat="interfaz", vol=0.6)
        if texto:
            self.decir(texto)
        return n

    # En un servidor el contrato se vive igual (el jefe, la evaluación, los avisos, el ascenso), pero el dinero lo pone el
    # servidor: él cuenta los turnos, él sabe cuándo acaba el periodo y él paga la nómina con sus cifras y sus topes.
    def _hon_sv_contrato(self, que, **mas):
        if self.en_servidor and self.sv_honrado("nominas") and self.red is not None and self.red.conectado:
            self.red.enviar(dict(mas, t="contrato", que=que))

    def _hon_nomina(self, n, texto=None, buena=False, mala=False):
        """La nómina de un periodo. Sin conexión, la ingresa el juego; en un servidor, se le pide a él y llega aparte."""
        if not self.en_servidor:
            return self.hon_ingresar(n, texto) if n > 0 else 0
        self._hon_sv_contrato("cobrar", buena=bool(buena), mala=bool(mala))
        if texto:
            self.decir(texto)
        return 0

    def hon_sv_al_entrar(self, c):
        """Al entrar en un servidor: lo que él tiene apuntado de tu contrato. Si tienes uno y él no lo conoce (o es otro), se
        le da de alta; si ya lo llevaba, mandan su fecha de cobro y sus turnos. Y si el periodo acabó mientras no estabas,
        la evaluación llega ahora."""
        ct = self.j.contrato
        if not ct or not self.sv_honrado("nominas"):
            return
        if isinstance(c, dict) and c.get("empleo") == ct.get("empleo"):
            self._svm_contrato({"que": "firmado", "c": c})
            if int(ct.get("fin", 0)) <= self.dia:
                self._hon_dia_contrato()
        else:
            self._hon_sv_contrato("firmar", empleo=ct.get("empleo"), puesto=min(1, int(ct.get("puesto", 0))))

    def _svm_contrato(self, m):
        """El servidor contesta sobre tu contrato: lo que vale es lo que él tiene apuntado."""
        ct = self.j.contrato
        if m.get("que") == "no":
            if ct and m.get("motivo"):
                self.decir(tr_servidor(str(m["motivo"])[:300]))
            return
        c = m.get("c")
        if not ct or not isinstance(c, dict) or c.get("empleo") != ct.get("empleo"):
            return
        ct["fin"] = int(c.get("fin", ct.get("fin", self.dia)))
        if m.get("que") in ("firmado", "puesto"):
            empleo = self.hon_empleo()
            if empleo:
                ct["puesto"] = max(0, min(len(empleo["puestos"]) - 1, int(c.get("puesto", ct.get("puesto", 0)))))

    def _svm_nomina(self, m):
        """El servidor paga la nómina del periodo: la cifra es la suya."""
        n = max(0, int(m.get("n", 0) or 0))
        self._svm_contrato({"que": "cobro", "c": m.get("c")})
        if n > 0:
            corto = "turnos" in m and "cupo" in m and int(m["turnos"]) < int(m["cupo"])
            self.hon_ingresar(n, tr('El servidor te ingresa la nómina en el banco: {n} euros').format(n=(n)) + (tr(', por {int} de {int2} turnos.').format(int=(int(m['turnos'])), int2=(int(m['cupo']))) if corto else "."))
        elif m.get("faltan"):
            self.decir(tr('El servidor todavía no paga esta nómina: según su calendario faltan {int} días.').format(int=(int(m['faltan']))))

    def _hon_embargar(self, n):
        """La parte de un ingreso que se queda el embargo."""
        h = self.hon()
        if h["embargo"] <= 0 or n <= 0:
            return 0
        parte = min(int(h["embargo"]), int(n * AJ("embargo_pct") / 100.0))
        h["embargo"] -= parte
        if h["embargo"] <= 0:
            h["embargo"] = 0
            self.hon_decir(AJ.frase("frases_embargo_fin"), "prestigio")
        else:
            self.decir(tr('El embargo se queda {parte} euros. Aún debes {int}.').format(parte=(parte), int=(int(h['embargo']))))
        return parte

    def _hon_dia_contrato(self):
        j = self.j
        ct = j.contrato
        if not ct or (self.en_servidor and not self.sv_honrado("nominas")):
            return
        c, p = self.hon_empleo(), self.hon_puesto()
        if not c:
            j.contrato = {}
            return
        cupo = max(1, int(_n(p, "cupo", 3)))
        quedan = ct["fin"] - self.dia
        if quedan == 2 and ct["turnos"] < cupo and ct.get("avisado") != ct["fin"]:
            ct["avisado"] = ct["fin"]
            self.hon_decir(AJ.frase("frases_falta_turnos", jefe=ct["jefe"], dias=quedan, faltan=cupo - ct["turnos"]), "notificacion")
        if quedan > 0:
            return
        # fin del periodo: la evaluación
        cumplimiento = min(1.0, ct["turnos"] / cupo)
        calidad = sum(ct["calidad"]) / len(ct["calidad"]) if ct["calidad"] else 0.0
        nota = 60.0 * cumplimiento + 0.4 * calidad
        duro = 5 if ct["caracter"].startswith("exigente") else -5 if ct["caracter"].startswith("paciente") else 0
        sueldo = int(_n(p, "sueldo"))
        tope = AJ.entero("avisos_despido")
        kw = {"jefe": ct["jefe"], "tope": tope}
        ct["periodos"] += 1
        ct["nota"] = round(nota)
        j.stats["evaluaciones"] = j.stats.get("evaluaciones", 0) + 1
        if nota >= AJ("nota_buena") + duro:
            prima = int(sueldo * AJ("prima_buena") / 100.0)
            ct["meritos"] += 1
            ct["avisos"] = max(0, ct["avisos"] - 1)
            j.stats["evaluaciones_buenas"] = j.stats.get("evaluaciones_buenas", 0) + 1
            self._hon_nomina(sueldo + prima, AJ.frase("frases_eval_buena", sueldo=sueldo, prima=prima, **kw), buena=True)
            self.cambiar_ciudadania(AJ("prestigio_periodo"))
        elif nota >= AJ("nota_correcta") + duro:
            self._hon_nomina(sueldo, AJ.frase("frases_eval_correcta", sueldo=sueldo, **kw))
            self.cambiar_ciudadania(AJ("prestigio_periodo") / 2.0)
        elif nota >= AJ("nota_floja") + duro:
            ct["avisos"] += 1
            sueldo = int(sueldo * cumplimiento)
            self.son("animo_baja", cat="interfaz")
            self._hon_nomina(sueldo)
            self.decir(AJ.frase("frases_eval_floja", sueldo=sueldo, avisos=ct["avisos"], **kw))
        else:
            ct["avisos"] += 1 if self.hon_nivel() <= 1 else 2
            ct["meritos"] = max(0, ct["meritos"] - 1)
            self.son("animo_baja", cat="interfaz")
            self._hon_nomina(0, mala=True)
            self.decir(AJ.frase("frases_eval_mala", avisos=min(tope, ct["avisos"]), **kw))
        ct.update(turnos=0, calidad=[], fin=self.dia + AJ.entero("periodo_dias"))
        if ct["avisos"] >= tope:
            return self.hon_despedir(tr("demasiados avisos por faltar o por hacerlo mal"))
        self._hon_ascenso(c, ct)

    def _hon_ascenso(self, c, ct):
        k = int(ct["puesto"])
        if ct["meritos"] < AJ("meritos_ascenso") or k + 1 >= len(c["puestos"]):
            return
        nuevo = c["puestos"][k + 1]
        falta = self.hon_puesto_falta(nuevo)
        if falta:
            if ct.get("ascenso_dicho") != k:
                ct["ascenso_dicho"] = k
                self.decir(AJ.frase("frases_ascenso_falta", jefe=ct["jefe"], puesto=nuevo["nombre"], falta=falta))
            return
        ct["puesto"], ct["meritos"] = k + 1, 0
        self._hon_sv_contrato("ascenso")
        self.j.stats["ascensos"] = self.j.stats.get("ascensos", 0) + 1
        self.son("ascenso", cat="interfaz")
        self.cambiar_ciudadania(2.0)
        self.cambiar_animo(10)
        self.decir(AJ.frase("frases_ascenso", jefe=ct["jefe"], puesto=nuevo["nombre"], cupo=int(_n(nuevo, "cupo", 3)), sueldo=int(_n(nuevo, "sueldo"))))

    def hon_despedir(self, motivo):
        j, h = self.j, self.hon()
        ct, c = j.contrato, self.hon_empleo()
        if not ct:
            return
        j.contrato = {}
        self._hon_sv_contrato("dejar")
        if c:
            h["vetos"][c["id"]] = self.dia + AJ.entero("veto_dias")
        j.stats["despidos"] = j.stats.get("despidos", 0) + 1
        self.son("despido", cat="interfaz")
        self.decir(AJ.frase("frases_despido", jefe=ct["jefe"], empresa=c["empresa"] if c else "la empresa", motivo=motivo))
        self.cambiar_ciudadania(-AJ("prestigio_despido") * max(0.5, self.hon_f()))
        self.cambiar_animo(-10)

    def hon_dimitir(self):
        j, h = self.j, self.hon()
        ct, c = j.contrato, self.hon_empleo()
        if not ct:
            return
        j.contrato = {}
        self._hon_sv_contrato("dejar")
        empresa = c["empresa"] if c else tr("la empresa")
        self.decir(AJ.frase("frases_dimision", jefe=ct["jefe"], empresa=empresa), True)
        if ct["periodos"] >= AJ("carta_periodos") and not ct["avisos"] and c:
            h["cartas"] = [c["id"]]
            j.stats["cartas"] = j.stats.get("cartas", 0) + 1
            self.hon_decir(AJ.frase("frases_carta", jefe=ct["jefe"]), "diploma")

    def _hon_trabajo_y_antecedente(self, a):
        """Un antecedente nuevo llega a oídos de tu jefe."""
        ct, c = self.j.contrato, self.hon_empleo() if self.j.contrato else None
        if not ct or not c or not self.hon_nivel():
            return
        if a["g"] >= 3 or (c.get("confianza") and (a["g"] >= 2 or self.hon_nivel() >= 2)):
            return self.hon_despedir(tr("tus antecedentes penales") if not c.get("confianza") else tr("un empleo de confianza no admite antecedentes"))
        if a["g"] >= 2 or self.hon_nivel() >= 2:
            ct["avisos"] += 1
            tope = AJ.entero("avisos_despido")
            if ct["avisos"] >= tope:
                return self.hon_despedir(tr("tus problemas con la policía, que ya son demasiados"))
            self.hon_decir(AJ.frase("frases_aviso_antecedente", empresa=c["empresa"], jefe=ct["jefe"], avisos=ct["avisos"], tope=tope), "animo_baja")

    # ------------------------------------------------------------------ la empresa: tus negocios
    def hon_emp(self, l):
        """El estado de un negocio tuyo."""
        return self.j.empresa.setdefault(l.id, {"nivel": 1, "emp": 0, "rep": AJ("rep_inicial"), "precios": "normales", "horario": "normal", "tapadera": False,
                                                 "visto": self.dia, "dano": 0})

    def hon_mejoras(self):
        return sorted((m for m in self.datos.get("mejoras_negocio", []) if isinstance(m, dict) and _n(m, "nivel") >= 2), key=lambda m: _n(m, "nivel"))

    def hon_mejora(self, nivel):
        return next((m for m in self.hon_mejoras() if int(_n(m, "nivel")) == nivel), None)

    def hon_nivel_txt(self, nivel):
        m = self.hon_mejora(nivel)
        return str(m["nombre"]) if m else tr("Negocio de barrio")

    def hon_max_empleados(self, e):
        return int(e["nivel"]) + 1

    def hon_rep_factor(self, e):
        """Lo que multiplica el nombre del negocio: de menos a más alrededor de 1. Con las consecuencias apagadas, 1."""
        if not self.hon_nivel():
            return 1.0
        d = (e["rep"] - 50.0) / 50.0 * AJ("rep_factor") / 100.0
        return 1.0 + (d if d >= 0 else d * self.hon_f())

    def ingreso_negocio(self, l, detalle=False):
        """Lo que da un negocio tuyo al día: la base de los datos por sus mejoras, su gente, su nombre y tus decisiones."""
        base = int(l.get("ingresos", 0))
        if self.en_servidor or l.id not in self.j.empresa:
            return (base, 0) if detalle else base
        e = self.hon_emp(l)
        m = self.hon_mejora(int(e["nivel"]))
        bruto = base * (1.0 + (_n(m, "ingresos") if m else 0.0) / 100.0)
        bruto *= 1.0 + e["emp"] * AJ("empleado_rinde") / 100.0
        bruto *= self.hon_rep_factor(e)
        bruto *= 1.0 + {"bajos": -AJ("precios_bajos_ingreso"), "altos": AJ("precios_altos_ingreso")}.get(e["precios"], 0.0) / 100.0
        if e["horario"] == "ampliado" and e["emp"]:
            bruto *= 1.0 + AJ("horario_ingreso") / 100.0
        if e.get("dano", 0) > 0:
            bruto *= 1.0 - AJ("extorsion_dano") / 100.0
        sueldos = int(e["emp"] * base * AJ("empleado_sueldo") / 100.0)
        if e.get("encargado"):
            sueldos += int(base * AJ("encargado_sueldo") / 100.0)
        neto = max(0, int(bruto) - sueldos)
        return (neto, sueldos) if detalle else neto

    def hon_negocio_txt(self, l):
        e = self.hon_emp(l)
        rep = e["rep"]
        nombre = tr("por los suelos") if rep < 20 else "flojo" if rep < 40 else "normal" if rep < 60 else "bueno" if rep < 85 else "excelente"
        dias = self.dia - e["visto"]
        return (tr('{hon_nivel_txt}, nivel {int}. Da {ingreso_negocio} euros al día. Empleados: {emp} de {hon_max_empleados}. Su nombre entre la clientela es {nombre}. Precios {precios}, horario {horario}. ').format(hon_nivel_txt=(self.hon_nivel_txt(int(e['nivel']))), int=(int(e['nivel'])), ingreso_negocio=(self.ingreso_negocio(l)), emp=(e['emp']), hon_max_empleados=(self.hon_max_empleados(e)), nombre=(nombre), precios=(e['precios']), horario=(e['horario']))
                + (tr("Lo has atendido hoy") if dias <= 0 else tr('Hace {dias} {v} que no pasas por aquí').format(dias=(dias), v=(tr('día') if dias == 1 else tr('días'))))
                + (tr(". Lo lleva un encargado") if e.get("encargado") else "") + (tr(". Sirve de tapadera") if e["tapadera"] else ""))

    def hon_visitar(self, l):
        if not self.en_servidor and l.id in self.j.propiedades:
            self.hon_emp(l)["visto"] = self.dia

    def hon_atender(self, l):
        """Echar unas horas en tu negocio: sube su nombre. Una vez al día cada uno."""
        e = self.hon_emp(l)
        if e.get("atendido") == self.dia:
            return self.decir(tr("Hoy ya has echado tus horas aquí. Vuelve mañana."), True)
        e["atendido"] = e["visto"] = self.dia
        horas = AJ.entero("atender_horas")
        self.pasar_horas(horas)
        e["rep"] = min(100.0, e["rep"] + AJ("atender_rep"))
        self.j.stats["negocio_atendido"] = self.j.stats.get("negocio_atendido", 0) + 1
        self.son("jornada", cat="interfaz")
        self.cambiar_ciudadania(0.5)
        self.decir(AJ.frase("frases_atender", negocio=l.nombre, horas=horas, hora=self.hora_txt()), True)

    def hon_encargado(self, l):
        """Contratar o despedir al encargado de un negocio tuyo (foro, 1.7.6): lo lleva por ti. Cobra cada día de la caja, el
        negocio no se da nunca por abandonado y su nombre sube solo, poco a poco, hasta encargado_tope. Atender tú sigue
        subiéndolo más."""
        e = self.hon_emp(l)
        sueldo = int(int(l.get("ingresos", 0)) * AJ("encargado_sueldo") / 100.0)
        e["encargado"] = not e.get("encargado")
        if e["encargado"]:
            return self.decir(tr('Contratas a un encargado para {nombre}: cobra {sueldo} euros al día, que salen de la caja. Ya no hace falta que pases a diario: el negocio no se descuida y su nombre sube solo, poco a poco. Cómo va lo ves en el móvil, en Vida, reputación y consecuencias, Negocios. Ahora da {ingreso_negocio} euros al día.').format(
                nombre=(l.nombre), sueldo=(sueldo), ingreso_negocio=(self.ingreso_negocio(l))), True)
        return self.decir(tr('Despides al encargado de {nombre}. Si no pasas por aquí, el negocio se resentirá. Ahora da {ingreso_negocio} euros al día.').format(nombre=(l.nombre), ingreso_negocio=(self.ingreso_negocio(l))), True)

    def hon_mejora_coste(self, l, m):
        return int(int(l.get("precio", 0)) * _n(m, "coste") / 100.0)

    def hon_mejora_motivo(self, l):
        e = self.hon_emp(l)
        m = self.hon_mejora(int(e["nivel"]) + 1)
        if not m:
            return tr("Este negocio ya no puede crecer más.")
        if m.get("titulo") and m["titulo"] not in self.hon_titulos():
            return tr('Para esa mejora hace falta el título de {hon_titulo_nombre}: se saca en una academia.').format(hon_titulo_nombre=(self.hon_titulo_nombre(m['titulo'])))
        if self.j.ciudadania < _n(m, "prestigio") and not self.cheat_on("cheat_negocios"):
            return tr('Para esa mejora los vecinos tienen que hablar mejor de ti: hacen falta {int} de prestigio y tienes {int2}.').format(int=(int(_n(m, 'prestigio'))), int2=(int(self.j.ciudadania)))
        return ""

    def hon_mejorar(self, l):
        e = self.hon_emp(l)
        motivo = self.hon_mejora_motivo(l)
        if motivo:
            self.app.son("error")
            return self.decir(motivo, True)
        m = self.hon_mejora(int(e["nivel"]) + 1)
        if not self.pagar_sin_fiar(self.hon_mejora_coste(l, m)):
            return None
        e["nivel"] = int(e["nivel"]) + 1
        self.j.stats["mejoras_negocio"] = self.j.stats.get("mejoras_negocio", 0) + 1
        self.son("mision_ok", cat="interfaz")
        self.decir(tr('{nombre}: {nombre2} sube al nivel {nivel}. Ahora da {ingreso_negocio} euros al día y admite {hon_max_empleados} empleados.').format(nombre=tr(m['nombre']), nombre2=(l.nombre), nivel=(e['nivel']), ingreso_negocio=(self.ingreso_negocio(l)), hon_max_empleados=(self.hon_max_empleados(e))), True)

    def hon_empleado(self, l, d):
        """Contratar (1) o despedir (-1) a un empleado de un negocio tuyo."""
        e = self.hon_emp(l)
        n = e["emp"] + d
        if n < 0 or n > self.hon_max_empleados(e):
            self.app.son("menu_borde")
            return self.decir(tr("No tienes a nadie contratado.") if n < 0 else tr('Con este nivel no caben más de {hon_max_empleados}. Mejora el negocio para contratar más.').format(hon_max_empleados=(self.hon_max_empleados(e))), True)
        e["emp"] = n
        if not n and e["horario"] == "ampliado":
            e["horario"] = "normal"
        sueldo = int(int(l.get("ingresos", 0)) * AJ("empleado_sueldo") / 100.0)
        self.decir((tr('Contratas a una persona: cobra {sueldo} euros al día, que salen de la caja. ').format(sueldo=(sueldo)) if d > 0 else tr("Despides a una persona. ")) + tr('Tienes {n}. El negocio da ahora {ingreso_negocio} euros al día.').format(n=(n), ingreso_negocio=(self.ingreso_negocio(l))), True)

    def hon_precios(self, l):
        e = self.hon_emp(l)
        orden = list(PRECIOS)
        e["precios"] = orden[(orden.index(e["precios"]) + 1) % len(orden)] if e["precios"] in orden else "normales"
        ayuda = {"bajos": tr("Se gana menos en cada venta, pero la clientela lo agradece: el nombre del negocio sube poco a poco."), "normales": tr("Lo de siempre."),
                 "altos": tr("Se gana más en cada venta, pero la clientela protesta: el nombre del negocio baja poco a poco.")}[e["precios"]]
        self.decir(tr('Precios {precios}. {ayuda} Ahora da {ingreso_negocio} euros al día.').format(precios=(e['precios']), ayuda=(ayuda), ingreso_negocio=(self.ingreso_negocio(l))), True)

    def hon_horario(self, l):
        e = self.hon_emp(l)
        if e["horario"] == "normal" and not e["emp"]:
            self.app.son("error")
            return self.decir(tr("Para abrir más horas necesitas al menos un empleado."), True)
        e["horario"] = "ampliado" if e["horario"] == "normal" else "normal"
        self.decir(tr('Horario {horario}. Ahora da {ingreso_negocio} euros al día.').format(horario=(e['horario']), ingreso_negocio=(self.ingreso_negocio(l))), True)

    def hon_tapadera(self, l):
        """Usar el negocio de tapadera: blanquea cada día parte de tu dinero sin justificar, con su comisión y su riesgo."""
        e = self.hon_emp(l)
        e["tapadera"] = not e["tapadera"]
        cap = int(AJ("tapadera_capacidad") * e["nivel"])
        if e["tapadera"]:
            self.decir(tr('{nombre} hace ahora de tapadera: cada medianoche pasa por su caja hasta {cap} euros de tu dinero sin justificar, y te cuesta un {entero} por ciento de lo que blanquea. Si cae una inspección mientras tanto, tendrás un problema serio.').format(nombre=(l.nombre), cap=(cap), entero=(AJ.entero('tapadera_comision'))), True)
        else:
            self.decir(tr('{nombre} vuelve a ser un negocio limpio.').format(nombre=(l.nombre)), True)

    def hon_negro(self, n):
        """Dinero que no puedes justificar (atracos, tributos, contratos): se apunta por si Hacienda mira."""
        if n > 0 and not self.en_servidor:
            h = self.hon()
            h["negro"] = h.get("negro", 0.0) + float(n)

    def hon_vida_formal(self):
        """¿Tienes algo que perder? Un contrato, un negocio, un crédito o el aprecio de los vecinos."""
        j = self.j
        return bool(j.contrato or j.creditos or self.negocios_tuyos() or j.ciudadania >= 40)

    def _hon_dia_empresa(self):
        j, h = self.j, self.hon()
        if self.en_servidor:
            return
        nivel = self.hon_nivel()
        h["negro"] = max(0.0, h.get("negro", 0.0) * (1.0 - AJ("negro_decae") / 100.0))
        for l in self.negocios_tuyos():
            e = self.hon_emp(l)
            if e.get("dano", 0) > 0:
                e["dano"] -= 1
            if nivel and self.dia > h["gracia"]:                 # durante el periodo de gracia, el nombre del negocio no se mueve
                dias = 0 if e.get("encargado") else self.dia - max(e["visto"], h["gracia"])       # con encargado, nunca está abandonado
                d = {"bajos": AJ("precios_bajos_rep"), "altos": -AJ("precios_altos_rep")}.get(e["precios"], 0.0)
                if e.get("encargado") and e["rep"] < AJ("encargado_tope"):
                    d += AJ("encargado_rep")
                if dias > AJ("abandono_dias"):
                    suelo = 45.0 if e["emp"] else 15.0           # con gente contratada el negocio aguanta sin ti; solo, se hunde
                    if e["rep"] > suelo:
                        d -= AJ("abandono_baja") * self.hon_f()
                        if dias == AJ.entero("abandono_dias") + 1:
                            self.decir(AJ.frase("frases_abandono", negocio=l.nombre)
                                       + ("" if e["emp"] else tr(" Con alguien contratado, aguantaría sin ti.")))
                elif e["emp"]:
                    d += 0.5
                e["rep"] = max(0.0, min(100.0, e["rep"] + d))
            if e["tapadera"] and h["negro"] > 0:
                lava = min(h["negro"], AJ("tapadera_capacidad") * e["nivel"])
                comision = min(j.dinero + j.banco, int(lava * AJ("tapadera_comision") / 100.0))
                quita = min(j.dinero, comision)
                j.dinero -= quita
                j.banco -= comision - quita
                h["negro"] -= lava
                j.stats["blanqueado"] = j.stats.get("blanqueado", 0) + int(lava)
        self._hon_inspeccion()

    def _hon_inspeccion(self):
        """De vez en cuando, una inspección a uno de tus negocios. Limpio, suma; con tapadera o dinero sin justificar, es un asunto pendiente."""
        h = self.hon()
        negocios = self.negocios_tuyos()
        if not negocios or not self.hon_impuestos() or not self.hon_nivel():
            return
        if not h.get("inspeccion"):
            h["inspeccion"] = max(h["gracia"], self.dia) + random.randint(AJ.entero("inspeccion_min"), AJ.entero("inspeccion_max"))
        if self.dia < h["inspeccion"] or any(a["tipo"] == "inspeccion" for a in h["asuntos"]):
            return
        h["inspeccion"] = self.dia + int(random.randint(AJ.entero("inspeccion_min"), AJ.entero("inspeccion_max")) / max(0.6, self.hon_f()))
        sucios = [l for l in negocios if self.hon_emp(l)["tapadera"]]
        l = random.choice(sucios) if sucios and random.random() < 0.7 else random.choice(negocios)
        e = self.hon_emp(l)
        self.j.stats["inspecciones"] = self.j.stats.get("inspecciones", 0) + 1
        if not e["tapadera"] and h["negro"] < AJ("negro_umbral"):
            e["rep"] = min(100.0, e["rep"] + 5)
            self.j.stats["inspecciones_limpias"] = self.j.stats.get("inspecciones_limpias", 0) + 1
            self.hon_decir(AJ.frase("frases_inspeccion_limpia", negocio=l.nombre), "inspeccion")
            return self.cambiar_ciudadania(1.0)
        sancion = int(int(l.get("precio", 0)) * AJ("sancion_pct") / 100.0 * max(0.6, self.hon_f())) + int(h["negro"] * 0.1)
        plazo = AJ.entero("plazo_asunto")
        h["asuntos"].append({"tipo": "inspeccion", "lugar": l.id, "dia": self.dia, "plazo": self.dia + plazo, "euros": sancion})
        self.hon_decir(AJ.frase("frases_inspeccion_falta", negocio=l.nombre, dias=plazo), "inspeccion")

    # ------------------------------------------------------------------ impuestos y facturas
    def hon_cobro_detalle(self):
        """Lo que toca pagar en el próximo cobro: [(concepto, euros)]."""
        j, h = self.j, self.hon()
        if not self.hon_impuestos():
            return []
        f = max(0.6, self.hon_f()) if self.hon_nivel() else 0.6
        casas = [l for l in (self.lugares.get(pid) for pid in j.propiedades) if l is not None and l.tipo == "casa"]
        partes = []
        if casas:
            partes.append((tr('luz y agua de {len} {v}').format(len=(len(casas)), v=(tr('vivienda') if len(casas) == 1 else tr('viviendas'))), int(len(casas) * AJ("factura_casa") * f)))
        ibi = int(sum(int(l.get("precio", 0)) for l in casas) * AJ("impuesto_casa") / 10000.0 * f)
        if ibi:
            partes.append((tr("contribución de tus viviendas"), ibi))
        neg = int(h.get("caja", 0) * AJ("impuesto_negocio") / 100.0 * f)
        if neg:
            partes.append((tr("impuesto de tus negocios"), neg))
        if h["deuda"]:
            partes.append((tr("deuda atrasada, con su recargo"), int(h["deuda"])))
        if h["fiado"] and self.dia - h.get("fiado_dia", self.dia) >= AJ("fiado_dias"):
            partes.append((tr("lo que debes de fiado en las tiendas"), int(h["fiado"])))
        return [x for x in partes if x[1] > 0]

    def hon_cobro_txt(self):
        if not self.hon_impuestos():
            return tr("Los impuestos y las facturas están desactivados.") if not self.en_servidor else tr("En un servidor en línea no hay impuestos ni facturas.")
        h = self.hon()
        partes = self.hon_cobro_detalle()
        total = sum(n for _, n in partes)
        quedan = max(0, h["cobro"] - self.dia)
        if not total:
            return tr('Próximo cobro de facturas e impuestos, dentro de {quedan} días: de momento, nada.').format(quedan=(quedan))
        return tr('Próximo cobro, dentro de {quedan} {v}: unos {total} euros. ').format(quedan=(quedan), v=(tr('día') if quedan == 1 else tr('días')), total=(total)) + "; ".join(f"{c}, {n}" for c, n in partes).capitalize()

    def hon_cobrar_de_cuentas(self, n):
        """Cobra primero del banco y luego del bolsillo. Devuelve lo que no se ha podido cobrar."""
        j = self.j
        del_banco = min(j.banco, n)
        j.banco -= del_banco
        del_bolsillo = min(j.dinero, n - del_banco)
        j.dinero -= del_bolsillo
        return n - del_banco - del_bolsillo

    def _hon_dia_cobro(self):
        j, h = self.j, self.hon()
        if not self.hon_impuestos():
            return
        quedan = h["cobro"] - self.dia
        if quedan == AJ.entero("aviso_dias"):
            total = sum(n for _, n in self.hon_cobro_detalle())
            if total:
                self.hon_decir(AJ.frase("frases_cobro_aviso", dias=quedan, euros=total), "notificacion")
        if quedan > 0:
            return
        partes = self.hon_cobro_detalle()
        total = sum(n for _, n in partes)
        h["cobro"] = self.dia + AJ.entero("cobro_dias")
        h["caja"] = 0
        if not total:
            return
        fiado_cobrado = any(c.startswith(tr("lo que debes de fiado")) for c, _ in partes)
        falta = self.hon_cobrar_de_cuentas(total)
        j.stats["impuestos_pagados"] = j.stats.get("impuestos_pagados", 0) + total - falta
        detalle = "; ".join(f"{c}, {n}" for c, n in partes)
        if fiado_cobrado:
            h["fiado"] = 0
        if not falta:
            h["deuda"], h["impagos"] = 0, 0
            return self.hon_decir(AJ.frase("frases_cobro", euros=total, detalle=detalle.capitalize()), "factura")
        h["impagos"] += 1
        h["deuda"] = int(falta * (1.0 + AJ("recargo") / 100.0))
        self.hon_decir(AJ.frase("frases_impago", falta=falta), "factura")
        self.cambiar_ciudadania(-2.0 * self.hon_f())
        if h["impagos"] >= AJ("impagos_embargo"):
            self.hon_embargo(h["deuda"])
            h["deuda"], h["impagos"] = 0, 0

    def hon_embargo(self, euros):
        h = self.hon()
        h["embargo"] += int(euros)
        self.j.stats["embargos"] = self.j.stats.get("embargos", 0) + 1
        self.hon_decir(AJ.frase("frases_embargo", euros=int(h["embargo"])), "factura")
        self.cambiar_ciudadania(-8.0 * max(0.5, self.hon_f()))

    # ------------------------------------------------------------------ el banco: créditos e hipotecas
    def hon_ingresos_semana(self):
        """Lo que entra de forma estable cada periodo: nómina y negocios."""
        return self.hon_sueldo_semana() + 7 * sum(self.ingreso_negocio(l) for l in self.negocios_tuyos())

    def hon_solvencia(self):
        """De 0 a 100: lo que el banco se fía de ti. Prestigio, ingresos estables y antecedentes."""
        j, h = self.j, self.hon()
        s = j.ciudadania * AJ("solvencia_prestigio") / 100.0 + min(AJ("solvencia_ingresos_tope"), self.hon_ingresos_semana() / AJ("solvencia_ingresos")) + (6 if h["cartas"] else 0) + min(10.0, j.stats.get("creditos_pagados", 0) * 5.0)
        s -= self.hon_peso() * 8.0 + sum(int(c.get("impagos", 0)) for c in j.creditos) * 10.0 + (25 if h["embargo"] else 0) + (10 if h["deuda"] else 0)
        return max(0.0, min(100.0, s))

    def hon_solvencia_txt(self):
        s = self.hon_solvencia()
        return tr("muy baja") if s < 20 else "baja" if s < AJ("credito_min_solvencia") else "justa" if s < AJ("hipoteca_solvencia") else "buena" if s < 70 else "excelente"

    def hon_interes(self):
        s = self.hon_solvencia()
        return AJ("interes_bueno") if s >= 70 else AJ("interes_medio") if s >= AJ("hipoteca_solvencia") else AJ("interes_malo")

    def hon_credito_maximo(self):
        s = self.hon_solvencia()
        if s < AJ("credito_min_solvencia") or self.hon_bloqueo():
            return 0
        return int((s - AJ("credito_min_solvencia") + 10) * AJ("credito_por_punto") / 100.0) * 100

    def hon_credito_motivo(self, tipo="personal"):
        j, h = self.j, self.hon()
        if self.hon_bloqueo():
            return self.hon_bloqueo()
        if h["embargo"]:
            return tr("Estás embargad[o|a]: el banco no te presta nada hasta que saldes la deuda.")
        if any(c["tipo"] == tipo for c in j.creditos) and tipo == "personal":
            return tr("Ya tienes un crédito personal en marcha. Termina de pagarlo antes de pedir otro.")
        if self.hon_graves():
            return tr("Con antecedentes graves en vigor, el banco no te presta.")
        minimo = AJ("credito_min_solvencia") if tipo == "personal" else AJ("hipoteca_solvencia")
        if self.hon_solvencia() < minimo:
            return (tr("El banco no se fía lo bastante: tu solvencia es ") + self.hon_solvencia_txt() + tr(". Sube con prestigio entre los vecinos, con una nómina o un negocio, "
                    "y baja con antecedentes e impagos."))
        return ""

    def hon_pedir_credito(self, importe):
        j = self.j
        motivo = self.hon_credito_motivo()
        if motivo or importe > self.hon_credito_maximo() or importe <= 0:
            self.app.son("error")
            self.decir(motivo or tr('El banco no te presta tanto. Como mucho, {hon_credito_maximo} euros.').format(hon_credito_maximo=(self.hon_credito_maximo())), True)
            return False
        n = AJ.entero("credito_cuotas")
        cuota = int(importe * (1.0 + self.hon_interes() / 100.0) / n) + 1
        j.creditos.append({"tipo": "personal", "cuota": cuota, "quedan": n, "prox": self.dia + AJ.entero("cuota_dias"), "impagos": 0, "atraso": 0})
        j.banco += importe
        j.stats["creditos"] = j.stats.get("creditos", 0) + 1
        self.son("dinero", cat="interfaz")
        self.decir(tr('Crédito concedido: {importe} euros, ingresados en tu cuenta. Lo devuelves en {n} cuotas de {cuota} euros, una cada {entero} días. Se cobran solas, con aviso dos días antes.').format(importe=(importe), n=(n), cuota=(cuota), entero=(AJ.entero('cuota_dias'))), True)
        return True

    def hon_hipoteca_datos(self, l):
        """(entrada, cuota, número de cuotas) de comprar con hipoteca una casa o un negocio."""
        precio = int(l.get("precio", 0))
        entrada = int(precio * AJ("hipoteca_entrada") / 100.0)
        n = AJ.entero("hipoteca_cuotas")
        cuota = int((precio - entrada) * (1.0 + (AJ("hipoteca_interes") + (self.hon_interes() - AJ("interes_bueno")) / 2.0) / 100.0) / n) + 1
        return entrada, cuota, n

    def hon_hipoteca(self, l):
        """Compra una casa o un negocio pagando la entrada y el resto en cuotas."""
        j = self.j
        motivo = self.hon_credito_motivo("hipoteca")
        if motivo:
            self.app.son("error")
            self.decir(motivo, True)
            return False
        entrada, cuota, n = self.hon_hipoteca_datos(l)
        if not self.pagar_sin_fiar(entrada):
            return False
        j.creditos.append({"tipo": "hipoteca", "lugar": l.id, "cuota": cuota, "quedan": n, "prox": self.dia + AJ.entero("cuota_dias"), "impagos": 0, "atraso": 0})
        j.propiedades.append(l.id)
        j.stats["hipotecas"] = j.stats.get("hipotecas", 0) + 1
        self.app.son("mision_ok")
        self.decir(tr('Firmas la hipoteca: {nombre} es {v}. Has pagado {entrada} euros de entrada y quedan {n} cuotas de {cuota} euros, una cada {entero} días.').format(nombre=(l.nombre), v=(tr('tuya') if l.tipo == 'casa' else tr('tuyo')), entrada=(entrada), n=(n), cuota=(cuota), entero=(AJ.entero('cuota_dias'))), True)
        return True

    def hon_credito_nombre(self, c):
        l = self.lugares.get(c.get("lugar"))
        return tr('hipoteca de {nombre}').format(nombre=(l.nombre)) if c["tipo"] == "hipoteca" and l else "hipoteca" if c["tipo"] == "hipoteca" else tr("crédito personal")

    def hon_credito_txt(self, c):
        quedan = max(0, c["prox"] - self.dia)
        nombre = self.hon_credito_nombre(c)
        return (tr('{v}: quedan {quedan} cuotas de {cuota} euros. La próxima, dentro de {quedan2} {v2}').format(v=(nombre[:1].upper() + nombre[1:]), quedan=(c['quedan']), cuota=(c['cuota']), quedan2=(quedan), v2=(tr('día') if quedan == 1 else tr('días')))
                + (tr('. Atrasos y recargos: {int} euros; impagos seguidos, {impagos}').format(int=(int(c['atraso'])), impagos=(c['impagos'])) if c.get("atraso") else ""))

    def hon_liquidar(self, c):
        """Pagar de una vez lo que queda de un crédito: se perdona el cinco por ciento."""
        total = int((c["cuota"] * c["quedan"]) * 0.95 + c.get("atraso", 0))
        if total > self.j.dinero + self.j.banco:
            self.app.son("error")
            return self.decir(tr('Liquidarlo cuesta {total} euros y entre la cuenta y el bolsillo no los tienes.').format(total=(total)), True)
        self.hon_cobrar_de_cuentas(total)
        self._hon_credito_fin(c)

    def _hon_credito_fin(self, c):
        j = self.j
        if c in j.creditos:
            j.creditos.remove(c)
        j.stats["creditos_pagados"] = j.stats.get("creditos_pagados", 0) + 1
        self.hon_decir(AJ.frase("frases_cuota_fin", tipo=self.hon_credito_nombre(c)), "prestigio")
        self.cambiar_ciudadania(2.0)

    def _hon_dia_creditos(self):
        j = self.j
        for c in list(j.creditos):
            nombre = self.hon_credito_nombre(c)
            quedan = c["prox"] - self.dia
            importe = int(c["cuota"] + c.get("atraso", 0))
            if quedan == AJ.entero("aviso_dias"):
                self.hon_decir(AJ.frase("frases_cuota_aviso", dias=quedan, tipo=nombre, euros=importe), "notificacion")
            if quedan > 0:
                continue
            if j.banco + j.dinero >= importe:
                self.hon_cobrar_de_cuentas(importe)
                c.update(quedan=c["quedan"] - 1, atraso=0, impagos=0, prox=self.dia + AJ.entero("cuota_dias"))
                if c["quedan"] <= 0:
                    self._hon_credito_fin(c)
                else:
                    self.hon_decir(AJ.frase("frases_cuota", tipo=nombre, euros=importe, quedan=c["quedan"]), "factura")
                continue
            c["impagos"] += 1
            c["atraso"] = int(c.get("atraso", 0) + c["cuota"] * AJ("recargo") / 100.0)
            c["prox"] = self.dia + AJ.entero("reintento_dias")
            j.stats["impagos"] = j.stats.get("impagos", 0) + 1
            tope = AJ.entero("impagos_embargo")
            self.hon_decir(AJ.frase("frases_cuota_impago", tipo=nombre, euros=importe, dias=AJ.entero("reintento_dias"), impagos=c["impagos"], tope=tope), "factura")
            self.cambiar_ciudadania(-3.0 * max(0.5, self.hon_f()))
            if c["impagos"] >= tope:
                j.creditos.remove(c)
                self.hon_embargo(c["cuota"] * c["quedan"] + c["atraso"])

    # ------------------------------------------------------------------ la doble vida
    def hon_abogado(self):
        return int(self.hon().get("abogado", 0)) > self.dia

    def hon_contratar_abogado(self):
        h = self.hon()
        if self.hon_abogado():
            h["abogado"] = 0
            return self.decir(tr("Prescindes de tu abogado."), True)
        precio = AJ.entero("abogado_semana")
        if not self.pagar_sin_fiar(precio):
            return None
        h["abogado"] = self.dia + 7
        self.decir(AJ.frase("frases_abogado", euros=precio), True)

    def hon_sospechar(self, n):
        """Lo que se va sabiendo de tu otra vida. Solo cuenta si tienes algo que perder."""
        if n <= 0 or not self.hon_nivel() or not self.hon_vida_formal():
            return
        h = self.hon()
        antes = h["sospecha"]
        n *= self.hon_f() * (AJ("abogado_factor") / 100.0 if self.hon_abogado() else 1.0)
        h["sospecha"] = min(100.0, antes + n)
        if antes < AJ("sospecha_rumor") <= h["sospecha"]:
            self.hon_decir(AJ.frase("frases_rumor"), "animo_baja")

    def hon_sospecha_txt(self):
        s = self.hon()["sospecha"]
        return (tr("nadie sospecha nada") if s < 15 else tr("hay quien se hace preguntas") if s < AJ("sospecha_rumor") else tr("corre el rumor de que llevas una doble vida") if s < AJ("sospecha_prensa")
                else tr("medio barrio lo da por hecho y la prensa está al acecho"))

    def hon_doble_vida(self):
        """¿Llevas las dos vidas a la vez? Aprecio de los vecinos y respeto en la calle."""
        return self.j.ciudadania >= 40 and self.j.reputacion >= 20

    def hon_descubrir(self, texto=None):
        """Sale a la luz: se hunde el prestigio, tu jefe se entera y tus negocios pierden nombre."""
        j, h = self.j, self.hon()
        f = max(0.5, self.hon_f())
        j.stats["descubierto"] = j.stats.get("descubierto", 0) + 1
        h["sospecha"] = 30.0
        self.hon_decir(texto or AJ.frase("frases_prensa", nombre=f"{j.nombre} {j.apellido}".strip()), "animo_baja")
        self.cambiar_ciudadania(-AJ("prensa_prestigio") * f)
        for l in self.negocios_tuyos():
            e = self.hon_emp(l)
            e["rep"] = max(0.0, e["rep"] - 15 * f)
        ct, c = j.contrato, self.hon_empleo() if j.contrato else None
        if ct and c:
            if c.get("confianza") or self.hon_nivel() >= 3:
                self.hon_despedir(tr("lo que ha salido en el periódico"))
            else:
                ct["avisos"] += 1
                if ct["avisos"] >= AJ("avisos_despido"):
                    self.hon_despedir(tr("lo que ha salido en el periódico"))
                else:
                    self.decir(tr('{jefe} ha leído el periódico. Te apunta un aviso: llevas {avisos} de {entero}.').format(jefe=(ct['jefe']), avisos=(ct['avisos']), entero=(AJ.entero('avisos_despido'))))

    def _hon_dia_doble(self):
        j, h = self.j, self.hon()
        if not self.hon_nivel():
            return
        if h.get("abogado") and h["abogado"] <= self.dia:        # el abogado se renueva solo cada semana, si hay con qué
            if self.hon_cobrar_de_cuentas(AJ.entero("abogado_semana")) == 0:
                h["abogado"] = self.dia + 7
            else:
                h["abogado"] = 0
                self.decir(AJ.frase("frases_abogado_fin"))
        h["sospecha"] = max(0.0, h["sospecha"] - AJ("sospecha_baja"))
        fachada = j.ciudadania >= 25 or bool(j.contrato)         # a quien no tiene buen nombre que perder, la prensa no le dedica un reportaje
        if fachada and h["sospecha"] >= AJ("sospecha_prensa") and not any(a["tipo"] == "prensa" for a in h["asuntos"]) and h.get("prensa_dia", -99) + 5 <= self.dia:
            h["prensa_dia"] = self.dia
            plazo = AJ.entero("plazo_asunto")
            h["asuntos"].append({"tipo": "prensa", "dia": self.dia, "plazo": self.dia + plazo, "euros": int(AJ("prensa_soborno") * max(0.6, self.hon_f()))})
            self.hon_decir(AJ.frase("frases_prensa_aviso", dias=plazo), "notificacion")

    # ------------------------------------------------------------------ la extorsión al honrado sin protección
    def hon_protegido(self):
        """¿Te respetan lo bastante en la calle como para no pedirte dinero? Fama, banda propia, escolta o un pacto."""
        j = self.j
        return (j.reputacion >= AJ("fama_respeto") or j.banda > 0 or j.territorios or j.pacto_hasta >= self.dia
                or any(p.tipo == "aliado" and not p.muerto for p in self.personas) or any(v >= 30 for v in j.rep_bandas.values()))

    def _hon_dia_extorsion(self):
        j, h = self.j, self.hon()
        negocios = self.negocios_tuyos()
        ex = h.get("extorsion")
        if ex and ex.get("pago"):                                # estás pagando: cada semana, hasta que acabe
            if self.dia >= ex["prox"]:
                if self.hon_cobrar_de_cuentas(ex["pago"]) == 0:
                    ex["quedan"] -= 1
                    ex["prox"] = self.dia + 7
                    self.decir(tr('{banda} cobra su semana: {pago} euros.').format(banda=(ex['banda']), pago=(ex['pago'])) + (tr(" Era la última.") if ex["quedan"] <= 0 else tr(' Quedan {quedan}.').format(quedan=(ex['quedan']))))
                    if ex["quedan"] <= 0:
                        h["extorsion"] = None
                else:
                    h["extorsion"] = None
                    self._hon_extorsion_dano(negocios, ex["banda"])
            return
        if not negocios or not self.hon_nivel() or self.hon_protegido():
            h["prox_extorsion"] = 0
            return
        if not h.get("prox_extorsion"):
            h["prox_extorsion"] = max(h["gracia"], self.dia) + int(random.randint(AJ.entero("extorsion_min"), AJ.entero("extorsion_max")) / max(0.6, self.hon_f()))
            return
        if self.dia == h["prox_extorsion"] - 1 and j.ciudadania >= 40:
            self.decir(AJ.frase("frases_extorsion_vecino", banda=self._hon_banda()))
        if self.dia < h["prox_extorsion"] or any(a["tipo"] == "extorsion" for a in h["asuntos"]):
            return
        h["prox_extorsion"] = 0
        l = random.choice(negocios)
        banda = self._hon_banda(l)
        euros = max(AJ.entero("extorsion_minimo"), int(7 * self.ingreso_negocio(l) * AJ("extorsion_pct") / 100.0 * max(0.6, self.hon_f())))
        plazo = AJ.entero("plazo_asunto")
        h["asuntos"].append({"tipo": "extorsion", "lugar": l.id, "banda": banda, "dia": self.dia, "plazo": self.dia + plazo, "euros": euros})
        j.stats["extorsiones"] = j.stats.get("extorsiones", 0) + 1
        self.hon_decir(AJ.frase("frases_extorsion", banda=banda, negocio=l.nombre, euros=euros, dias=plazo), "amenaza_barrio")

    def _hon_banda(self, l=None):
        if l is not None:
            mapa = self.mapas.get(l.mapa)
            b = mapa.barrio(l.x, l.y) if mapa is not None else None
            banda = self.banda_de_barrio(b) if b and b["id"] not in self.j.territorios else None
            if banda:
                return banda
        nombres = G.nombres_bandas()
        return random.Random(f"{self.j.semilla}-extorsion").choice(nombres) if nombres else tr("una banda")

    def _hon_extorsion_dano(self, negocios, banda, frase="frases_extorsion_dano"):
        if not negocios:
            return
        l = random.choice(negocios)
        e = self.hon_emp(l)
        e["dano"] = AJ.entero("extorsion_dano_dias")
        e["rep"] = max(0.0, e["rep"] - 8)
        self.hon_decir(AJ.frase(frase, negocio=l.nombre, banda=banda), "amenaza_barrio")

    # ------------------------------------------------------------------ asuntos pendientes: inspección, prensa y extorsión
    def hon_asunto_txt(self, a):
        l = self.lugares.get(a.get("lugar"))
        quedan = max(0, a["plazo"] - self.dia)
        plazo = tr('Te {v} {quedan} {v2}').format(v=(tr('queda') if quedan == 1 else tr('quedan')), quedan=(quedan), v2=(tr('día') if quedan == 1 else tr('días')))
        if a["tipo"] == "inspeccion":
            return tr('Inspección con irregularidades en {v}: sanción de {euros} euros. {plazo}').format(v=(l.nombre if l else tr('tu negocio')), euros=(a['euros']), plazo=(plazo))
        if a["tipo"] == "prensa":
            return tr('Un periodista prepara un reportaje sobre tu otra vida. {plazo}').format(plazo=(plazo))
        return tr('{banda} te pide {euros} euros a la semana por «proteger» {v}. {plazo}').format(banda=(a['banda']), euros=(a['euros']), v=(l.nombre if l else tr('tu negocio')), plazo=(plazo))

    def hon_asunto_opciones(self, a):
        """Lo que puedes hacer con un asunto: [(clave, texto, ayuda)]."""
        h = self.hon()
        if a["tipo"] == "inspeccion":
            l = self.lugares.get(a.get("lugar"))
            soborno = int(int(l.get("precio", 0)) * AJ("soborno_pct") / 100.0) if l else a["euros"] // 2
            prob = int(max(15, min(90, AJ("soborno_prob") + self.j.reputacion / 4.0 - 10 * (self.hon_nivel() - 2))))
            ops = [("pagar", tr('Pagar la sanción: {euros} euros').format(euros=(a['euros'])), tr("Lo limpio. Pagas, el negocio deja de ser tapadera y lo que no podías justificar queda regularizado.")),
                   ("sobornar", tr('Intentar sobornar al inspector: {soborno} euros').format(soborno=(soborno)),
                    tr('Más barato, y sigues como estabas. Sale bien unas {prob} veces de cada cien, más cuanta más fama tengas en la calle. Si sale mal: la sanción, un antecedente grave y la portada del periódico.').format(prob=(prob)))]
            if self.hon_abogado():
                ops.append(("abogado", tr('Que recurra tu abogado: {v} euros').format(v=(a['euros'] // 2)), tr("Tu abogado encuentra defectos de forma: pagas la mitad y no queda nada apuntado.")))
            return ops
        if a["tipo"] == "prensa":
            ops = [("pagar", tr('Pagar al periodista para que lo guarde en un cajón: {euros} euros').format(euros=(a['euros'])), tr("El reportaje no sale y los rumores se calman. Es un soborno: en la calle se sabrá que pagas.")),
                   ("dejar", tr("Dejar que lo publique"), tr("Sale en el periódico: pierdes prestigio, tu jefe se entera y tus negocios pierden nombre. A cambio, en la calle todos sabrán quién eres."))]
            if self.hon_abogado():
                ops.insert(0, ("abogado", tr("Que lo frene tu abogado"), tr("Va incluido en lo que le pagas: el reportaje no sale.")))
            return ops
        ops = [("pagar", tr('Pagar: {euros} euros cada semana, durante {entero} semanas').format(euros=(a['euros']), entero=(AJ.entero('extorsion_semanas'))), tr("Sales del paso sin más, y tu negocio no tendrá problemas mientras pagues.")),
               ("denunciar", tr("Denunciarlo a la policía"), tr("Lo honrado. Funciona mejor cuanto más te aprecian los vecinos: con buen prestigio, la policía actúa y la banda no vuelve. Si casi nadie te conoce, puede salir mal.")),
               ("negarte", tr("Negarte y aguantar"), tr("No pagas. Puede que se cansen, o puede que tu negocio amanezca con el cierre reventado y pierda unos días de caja."))]
        if self.j.reputacion >= 10 or any(p.tipo == "aliado" and not p.muerto for p in self.personas):
            ops.append(("plantar", tr("Plantarles cara"), tr("Con algo de fama en la calle o con escolta, se lo piensan y te dejan en paz.")))
        return ops

    def hon_resolver(self, a, clave):
        """Resuelve un asunto pendiente de una de las maneras posibles."""
        j, h = self.j, self.hon()
        if a not in h["asuntos"]:
            return
        l = self.lugares.get(a.get("lugar"))
        e = self.hon_emp(l) if l is not None and l.id in j.propiedades else None
        if a["tipo"] == "inspeccion":
            if clave == "abogado" and not self.hon_abogado():   # el abogado dejó de llevar tus asuntos entre medias: se paga entera
                clave = "pagar"
            if clave == "sobornar":
                soborno = int(int(l.get("precio", 0)) * AJ("soborno_pct") / 100.0) if l else a["euros"] // 2
                if not self.pagar_sin_fiar(soborno):
                    return
                prob = max(15, min(90, AJ("soborno_prob") + j.reputacion / 4.0 - 10 * (self.hon_nivel() - 2)))
                if random.random() * 100 < prob:
                    h["asuntos"].remove(a)
                    self.cambiar_reputacion(1)
                    return self.decir(AJ.frase("frases_soborno_ok"), True)
                self.decir(AJ.frase("frases_soborno_mal"), True)
                self.hon_cobrar_de_cuentas(a["euros"])
                h["asuntos"].remove(a)
                if e:
                    e["tapadera"] = False
                h["negro"] = 0.0
                self.hon_antecedente(3, tr("Intento de soborno a un inspector y blanqueo"))
                return self.hon_descubrir()
            coste = a["euros"] // 2 if clave == "abogado" else a["euros"]
            falta = self.hon_cobrar_de_cuentas(coste)
            h["asuntos"].remove(a)
            if e:
                e["tapadera"] = False
                e["rep"] = max(0.0, e["rep"] - (3 if clave == "abogado" else 8))
            h["negro"] = 0.0
            if falta:
                h["deuda"] += int(falta * (1.0 + AJ("recargo") / 100.0))
            self.hon_decir(tr('Sanción pagada: {v} euros.').format(v=(coste - falta)) + (tr(' Lo que falta, {falta}, queda a deber con recargo.').format(falta=(falta)) if falta else "")
                           + (tr(" Tu abogado ha dejado la cosa en la mitad y sin nada apuntado.") if clave == "abogado" else tr(" El negocio queda limpio y regularizado.")), "factura")
            if clave != "abogado":
                self.hon_sospechar(10)
                self.cambiar_ciudadania(-2.0 * self.hon_f())
            return
        if a["tipo"] == "prensa":
            if clave == "abogado" and self.hon_abogado():
                h["asuntos"].remove(a)
                h["sospecha"] = min(h["sospecha"], AJ("sospecha_rumor"))
                return self.decir(AJ.frase("frases_prensa_abogado"), True)
            if clave == "pagar":
                if not self.pagar_sin_fiar(a["euros"]):
                    return
                h["asuntos"].remove(a)
                h["sospecha"] = min(h["sospecha"], AJ("sospecha_rumor") - 5)
                self.cambiar_reputacion(1)
                return self.decir(AJ.frase("frases_prensa_callada"), True)
            h["asuntos"].remove(a)
            self.hon_descubrir()
            return self.cambiar_reputacion(4)
        # extorsión
        banda = a.get("banda", tr("la banda"))
        negocios = self.negocios_tuyos()
        h["asuntos"].remove(a)
        if clave == "pagar":
            h["extorsion"] = {"banda": banda, "pago": a["euros"], "quedan": AJ.entero("extorsion_semanas"), "prox": self.dia}
            j.stats["extorsion_pagada"] = j.stats.get("extorsion_pagada", 0) + 1
            return self.decir(AJ.frase("frases_extorsion_pago", banda=banda, euros=a["euros"], semanas=AJ.entero("extorsion_semanas")), True)
        if clave == "denunciar":
            j.stats["denuncias"] = j.stats.get("denuncias", 0) + 1
            self.cambiar_rep_banda(banda, -15, hablar=False)
            if random.random() * 100 < 35 + j.ciudadania * 0.9:
                self.hon_decir(AJ.frase("frases_extorsion_denuncia", banda=banda), "prestigio")
                self.cambiar_ciudadania(4.0)
                return self.cambiar_reputacion(-1)
            self.cambiar_ciudadania(1.0)
            return self._hon_extorsion_dano(negocios, banda, "frases_extorsion_denuncia_mal")
        if clave == "plantar":
            self.cambiar_reputacion(2)
            return self.decir(AJ.frase("frases_extorsion_plantas", banda=banda), True)
        if random.random() * 100 < AJ("extorsion_dano_prob"):
            return self._hon_extorsion_dano(negocios, banda)
        self.decir(AJ.frase("frases_extorsion_nada"), True)

    def _hon_dia_asuntos(self):
        """Un asunto que se queda sin contestar se resuelve solo, de la manera menos mala."""
        h = self.hon()
        for a in list(h["asuntos"]):
            if self.dia <= a["plazo"]:
                continue
            # Con abogado contratado, lo menos malo es que se encargue él: la inspección, a la mitad; la prensa, sin coste.
            clave = {"inspeccion": "pagar", "prensa": "dejar"}.get(a["tipo"], "negarte")
            if self.hon_abogado() and a["tipo"] in ("inspeccion", "prensa"):
                clave = "abogado"
            if a["tipo"] == "inspeccion":                        # se dice cuál: puede ser otra inspección, después de la que ya arreglaste
                l = self.lugares.get(a.get("lugar"))
                self.decir(tr('No contestaste a tiempo a la inspección de {negocio}, y se resuelve sin ti.').format(negocio=(l.nombre if l else tr("tu negocio")))
                           + (tr(" Se encarga tu abogado.") if clave == "abogado" else ""))
            else:
                self.decir(tr("Se ha acabado el plazo de un asunto pendiente y se resuelve sin ti."))
            self.hon_resolver(a, clave)

    # ------------------------------------------------------------------ hacer el bien (y las tentaciones)
    def hon_buenas(self):
        return [b for b in self.datos.get("buenas_acciones", []) if isinstance(b, dict) and b.get("opciones")]

    def _hon_buena_toca(self):
        """¿Toca cruzarse con algo? A pie, en la calle, sin nada entre manos, y solo de tarde en tarde."""
        j, h = self.j, self.hon()
        if not self.cfg["sucesos"] or self.en_servidor or self.online_activo() or not self.hon_buenas():
            return False
        if not h.get("prox_buena"):
            h["prox_buena"] = self.hon_abs() + AJ.entre("buena_min", "buena_max")
            return False
        if self.hon_abs() < h["prox_buena"]:
            return False
        if (j.veh or j.estrellas or self.mision or self.trabajo or self.evento or self.mundo.tipo == "mar" or self.nadando or self.acompanante
                or self.app.pila[-1] is not self or self.guerra_activa() or j.policia.get("turno")):
            return False
        h["prox_buena"] = self.hon_abs() + AJ.entre("buena_min", "buena_max")
        return True

    def hon_buena(self, b=None):
        """Te cruzas con una situación: ayudar, pasar de largo o aprovecharte. Se decide en un menú."""
        from .menus import Menu, Opcion
        b = b or random.choice(self.hon_buenas())

        def elegir(o):
            def f():
                self.app.cerrar(m)
                self.hon_buena_resolver(b, o)
            return f
        self.app.son("notificacion")
        m = Menu(self.app, str(b["texto"]), [Opcion(str(o["texto"]), elegir(o), ayuda=o.get("ayuda")) for o in b["opciones"]]
                 + [Opcion(tr("Seguir tu camino"), lambda: (self.app.cerrar(m), self.decir(AJ.frase("frases_buena_nada"))), ayuda=tr("No haces nada. No pasa nada."))],
                 intro=tr("Decide qué haces. F1 explica cada opción; Escape, sigues tu camino"))
        self.app.abrir(m)
        return m

    def hon_buena_resolver(self, b, o):
        """Aplica lo que elegiste: puede pedir algo (un botiquín, dinero), salir bien o mal, y cambia cómo te ven."""
        j = self.j
        pide = o.get("pide")
        if pide and j.objetos.get(pide, 0) <= 0:
            self.app.son("error")
            return self.decir(str(o.get("sin") or tr("No llevas lo que hace falta.")), True)
        if _n(o, "coste") > 0 and not self.pagar_sin_fiar(int(_n(o, "coste"))):
            return None
        if pide:
            j.objetos[pide] -= 1
        if _n(o, "horas") > 0:
            self.pasar_horas(_n(o, "horas"))
        mal = random.random() * 100 < _n(o, "riesgo")
        r = (o.get("mal") or {}) if mal else o
        if _n(r, "dinero"):
            self.dar_dinero(int(_n(r, "dinero"))) if _n(r, "dinero") > 0 else self.hon_cobrar_de_cuentas(int(-_n(r, "dinero")))
        if _n(r, "prestigio"):
            self.cambiar_ciudadania(_n(r, "prestigio"))
        if _n(r, "fama"):
            self.cambiar_reputacion(_n(r, "fama"))
        if _n(r, "animo"):
            self.cambiar_animo(_n(r, "animo"))
        if _n(r, "salud"):
            j.salud = max(5.0, min(j.salud_max, j.salud + _n(r, "salud")))
        if _n(r, "delito"):
            self.hon_sospechar(_n(r, "delito") * AJ("sospecha_delito"))
            if o.get("tentacion"):
                j.stats["tentaciones"] = j.stats.get("tentaciones", 0) + 1
        if not mal and _n(o, "prestigio") > 0:
            j.stats["buenas_acciones"] = j.stats.get("buenas_acciones", 0) + 1
            self.son("donativo", cat="interfaz")
        self.decir(str(r.get("dice") or ""), True)

    # ------------------------------------------------------------------ la trama del buen camino
    def cumple_vida(self, m):
        """¿Cumples lo que una misión pide de tu vida (requiere_vida)? Sin condición, siempre. El buen camino, solo sin conexión."""
        if self.en_servidor and m.get("honrada"):
            return False
        return not self.falta_vida(m)

    def falta_vida(self, m):
        """Lo que te falta de «requiere_vida» para una misión, dicho; lista vacía si nada."""
        req = m.get("requiere_vida")
        if not isinstance(req, dict):
            return []
        faltas = []
        for k, v in req.items():
            if k in MATICES_VIDA:
                continue
            cond = REQUISITOS_VIDA.get(k)
            try:
                v = float(v)
            except (TypeError, ValueError):
                v = 1.0
            extra = (str(req.get("tablon") or "").strip() or None,) if k == "contratos" else ()
            if cond and v and not cond[0](self, v, *extra):
                faltas.append(cond[1](self, v, *extra))
        return faltas

    def contratos_cumplidos(self, tablon=None):
        """Contratos del tablón cumplidos: todos o, con tablon, los colgados en ese sitio (por su identificador o su tipo)."""
        if not tablon:
            return int(self.j.stats.get("contratos", 0))
        por = self.j.stats.get("contratos_tablon")
        if not isinstance(por, dict):
            return 0
        total = 0
        for lid, n in por.items():
            l = self.lugares.get(lid)
            if lid == tablon or (l is not None and l.tipo == tablon):
                total += int(n or 0)
        return total

    def tablon_txt(self, tablon):
        """El sitio de un tablón dicho para el jugador: su nombre, o el tipo de sitio si no es uno concreto."""
        l = self.lugares.get(tablon)
        return self.nombre_lugar(l) if l is not None else tablon

    def hon_trama(self):
        """Por dónde vas en el buen camino: (misión siguiente o None, lo que falta, hechas, total)."""
        todas = [m for m in self.datos["misiones"] if m.get("honrada")]
        hechas = set(self.completadas)
        n = sum(1 for m in todas if m["id"] in hechas)
        total = len({m.get("orden", m["id"]) for m in todas})
        for m in todas:
            if m["id"] in hechas or m.get("lugar") not in self.lugares or not self.cumple_decision(m):
                continue
            if all(r in hechas for r in m.get("requiere", [])):
                return m, self.falta_vida(m), n, total
        return None, [], n, total

    def hon_trama_txt(self):
        if self.en_servidor:
            return tr("El buen camino: es una historia para jugar sin conexión. En un servidor en línea no avanza.")
        m, faltas, n, total = self.hon_trama()
        final = self.decisiones.get("_final_honrado")
        if isinstance(final, dict):
            return tr('El buen camino: terminado. {get}').format(get=(final.get('texto', '')))
        if m is None:
            return tr("El buen camino: empieza cuando hayas visto a tu tía Encarna en el Bar La Gaviota.") if not n else tr('El buen camino: {n} capítulos hechos.').format(n=(n))
        l = self.lugares[m["lugar"]]
        if faltas:
            return tr('El buen camino, {n} de {total}. Para «{titulo}» te falta ').format(n=(n), total=(total), titulo=(m['titulo'])) + "; ".join(faltas) + "."
        return tr('El buen camino, {n} de {total}. Te esperan en {nombre_lugar}: «{titulo}».').format(n=(n), total=(total), nombre_lugar=(self.nombre_lugar(l)), titulo=(m['titulo']))

    def hon_mision_completada(self, m):
        """Una misión del buen camino da prestigio, y la última, su epílogo."""
        if not m.get("honrada"):
            return
        self.cambiar_ciudadania(_n(m, "prestigio", 2))
        for ep in m.get("epilogos") or []:
            if isinstance(ep, dict) and self.cumple_decision(ep):
                self.decisiones["_final_honrado"] = {"opcion": 0, "texto": self.txt(ep.get("titulo", "")), "mision": m["id"], "clase": ep.get("clase", "")}
                self.j.stats["final_" + str(ep.get("clase") or "honrado")] = 1
                self.app.son("logro" if "logro" in self.mez.sonidos else "mision_ok")
                self.decir(tr('Final del buen camino: {txt}. ').format(txt=(self.txt(ep.get('titulo', '')))) + self.txt(ep.get("texto", "")))
                break

    def hon_ofrecer_mision(self, m, l):
        """Una misión del buen camino te espera en un sitio. No empieza sola: entras como siempre y la misión es una opción
        más del menú del sitio, la última antes de salir. En un sitio sin menú (un monumento), se pregunta."""
        from . import menus_juego as mj
        from .menus import SALIDAS, Menu, Opcion
        app = self.app
        texto = tr('El buen camino: «{titulo}». {txt}').format(titulo=(m['titulo']), txt=(self.txt(m.get('resumen', ''))))
        ayuda = tr("Empieza esta misión del buen camino. Es una historia aparte, que se hace sin cometer delitos: nadie te obliga a seguirla, y seguirá esperándote aquí.")

        def empezar():
            while app.pila and app.pila[-1] is not self:
                app.cerrar(app.pila[-1])
            self.salir_interior(silencio=True)
            if not self.mision:
                self.iniciar_mision(m)
        if l.tipo == "monumento":                                # aquí no hay nada más que hacer: se pregunta
            def no():
                app.cerrar(menu)
                mj.lugar(self, l)
            menu = Menu(app, tr('{nombre}. Aquí te esperan para «{titulo}», del buen camino').format(nombre=(l.nombre), titulo=(m['titulo'])),
                        [Opcion(tr("Empezar la misión"), empezar, ayuda=ayuda), Opcion(tr("Ahora no"), no, ayuda=tr("La misión seguirá esperándote aquí."))])
            return app.abrir(menu)
        antes = app.pila[-1]
        mj.lugar(self, l)
        menu = app.pila[-1]
        if menu is antes or not isinstance(menu, Menu):          # no se ha podido entrar (cerrado, en un vehículo...): ya lo ha dicho
            return None
        fuente = menu._fuente

        def ops():
            lista = list(fuente() if callable(fuente) else fuente)
            if self.mision or m["id"] in self.completadas:
                return lista
            lista.insert(len(lista) - 1 if lista and lista[-1].texto.startswith(SALIDAS) else len(lista), Opcion(texto, empezar, ayuda=ayuda))
            return lista
        menu._fuente = ops
        menu.refrescar(False)
        self.decir(tr('Aquí te esperan para «{titulo}», del buen camino: es la última opción de este menú.').format(titulo=(m['titulo'])))

    def hon_dos_caminos(self):
        """Tras ver a tu tía por primera vez, el juego dice una vez que hay dos caminos."""
        if "dos_caminos" in self.j.recordado or "m01" not in self.completadas or not any(m.get("honrada") for m in self.datos["misiones"]):
            return
        self.j.recordado.append("dos_caminos")
        self.decir(AJ.frase("frases_dos_caminos"))

    # ------------------------------------------------------------------ pareja apta para todos: compromiso y boda
    def vida_sentimental(self):
        """¿Hay relaciones sentimentales? Con el contenido para adultos, o con la opción apta para todos."""
        return self.modo_adulto() or bool(self.cfg["pareja_familiar"])

    def hon_estado_pareja(self):
        """«», «prometidos» o «casados», de tu pareja actual."""
        r = self.j.relaciones.get(self.j.pareja) if self.j.pareja else None
        return str(r.get("compromiso", "")) if r else ""

    def hon_comprometerse(self, pers):
        j = self.j
        r = self.relacion(pers["id"])
        if j.pareja != pers["id"]:
            return self.decir(tr('{nombre} y tú no sois pareja.').format(nombre=(pers['nombre'])), True)
        if r.get("compromiso"):
            return self.decir(tr('Ya estáis {compromiso}.').format(compromiso=(r['compromiso'])), True)
        if r["afinidad"] < AJ("compromiso_afinidad") or r.get("citas", 0) < AJ("compromiso_citas"):
            self.son("afinidad_baja", cat="interfaz", vol=0.5)
            return self.decir(AJ.frase("frases_compromiso_pronto", n=pers["nombre"]), True)
        r["compromiso"], r["compromiso_dia"], r["ultimo"] = "prometidos", self.dia, self.dia
        j.stats["compromisos"] = j.stats.get("compromisos", 0) + 1
        self.son("pareja", cat="interfaz")
        self.cambiar_animo(15)
        self.decir(AJ.frase("frases_compromiso", n=pers["nombre"]) + tr(' La boda puede ser dentro de {entero} días.').format(entero=(AJ.entero('boda_dias'))), True)

    def hon_casarse(self, pers):
        j = self.j
        r = self.relacion(pers["id"])
        if r.get("compromiso") == "casados":
            return self.decir(tr("Ya estáis casados."), True)
        if r.get("compromiso") != "prometidos" or j.pareja != pers["id"]:
            return self.decir(tr("Antes tenéis que estar prometidos."), True)
        faltan = int(r.get("compromiso_dia", self.dia)) + AJ.entero("boda_dias") - self.dia
        if faltan > 0:
            return self.decir(tr('Una boda no se prepara en un día: podréis casaros dentro de {faltan} {v}.').format(faltan=(faltan), v=(tr('día') if faltan == 1 else tr('días'))), True)
        if j.estrellas:
            self.app.son("error")
            return self.decir(tr("Con la policía buscándote no hay boda que valga."), True)
        if not self.pagar_sin_fiar(AJ.entero("boda_precio")):
            return None
        r["compromiso"], r["boda_dia"], r["ultimo"] = "casados", self.dia, self.dia
        r["afinidad"] = 100
        j.stats["bodas"] = j.stats.get("bodas", 0) + 1
        self.pasar_horas(6)
        self.son("pareja", cat="interfaz")
        self.cambiar_animo(25)
        self.cambiar_ciudadania(AJ("boda_prestigio"))
        self.decir(AJ.frase("frases_boda", n=pers["nombre"]) + tr(' Son las {hora_txt}.').format(hora_txt=(self.hora_txt())), True)

    # ------------------------------------------------------------------ el paso de los días y el tic
    def dia_honrado(self):
        """Cada medianoche: antecedentes que caducan, evaluación, negocios, cobros, cuotas, rumores, extorsión y asuntos.
        En un servidor, solo lo que allí existe: los antecedentes y el contrato fijo, si él paga las nóminas."""
        if self.en_servidor:
            if self.sv_honrado("nominas"):
                self.hon()
                self._hon_dia_antecedentes()
                self._hon_dia_contrato()
            return
        self.hon()
        self._hon_dia_antecedentes()
        self._hon_dia_contrato()
        self._hon_dia_empresa()
        self._hon_dia_cobro()
        self._hon_dia_creditos()
        self._hon_dia_doble()
        self._hon_dia_extorsion()
        self._hon_dia_asuntos()

    def actualizar_honrado(self, dt):
        self.t_honrado -= dt
        if self.t_honrado > 0 or self.en_servidor:
            return
        self.t_honrado = 20.0
        h = self.hon()
        if self._hon_cargada:                                    # una partida de antes de esta versión: se explica una vez
            self._hon_cargada = False
            self.hon_decir(AJ.frase("frases_partida_antigua", dias=AJ.entero("gracia_dias")), "notificacion")
        self.hon_dos_caminos()
        self._hon_control()
        if self._hon_buena_toca():
            self.hon_buena()

    # ------------------------------------------------------------------ cómo te ven: los textos de la consulta
    def hon_ciudad_txt(self):
        """Cómo te ve la ciudad y qué ganas o pierdes por ello, en frases."""
        j = self.j
        t = self.hon_tramo()
        nivel = self.hon_nivel()
        partes = [tr('Cómo te ve la ciudad: {ciudadania_txt}. Prestigio, {int} de 100').format(ciudadania_txt=(self.ciudadania_txt()), int=(int(j.ciudadania)))]
        paga = tr("cobras un veinte por ciento más en los trabajos honrados") if t == 3 else tr("cobras un diez por ciento más en los trabajos honrados") if t == 2 else ""
        if paga:
            partes.append(tr("Ganas: ") + paga + (tr(", el banco te da el doble de interés") if t == 3 else ""))
        if j.ciudadania >= 50:
            partes.append(tr("La policía te pasa por alto parte de las faltas"))
        if nivel:
            if t >= 2:
                partes.append(tr('En las tiendas te rebajan un {entero} por ciento y te fían hasta {hon_fiado_limite} euros; los vecinos a veces miran a otro lado, y si tu ficha está limpia un agente te da el beneficio de la duda una vez al día').format(entero=(AJ.entero('rebaja_ejemplar' if t == 3 else 'rebaja_aprecian')), hon_fiado_limite=(self.hon_fiado_limite())))
            elif t == 0:
                partes.append(tr('Pierdes: en las tiendas te cobran un {int} por ciento más, los testigos te denuncian con más ganas').format(int=(int(round(AJ('recargo_evitan') * self.hon_f()))))
                              + (tr(" y la policía te para de vez en cuando") if nivel >= 2 else "") + (tr(", y algún comercio se niega a atenderte") if nivel >= 3 else ""))
            else:
                partes.append(tr("Ni te rebajan ni te recargan en las tiendas: eres uno más. Con 40 de prestigio empiezan las ventajas"))
        else:
            partes.append(tr("Las consecuencias están apagadas: el prestigio solo cuenta en la paga, el banco y la policía, como antes"))
        return ". ".join(partes) + "."

    def hon_calle_txt(self):
        """Cómo te ve la calle y qué ganas o pierdes por ello, en frases."""
        j = self.j
        partes = [tr('Cómo te ve la calle: {reputacion_txt}. Fama, {int}').format(reputacion_txt=(self.reputacion_txt()), int=(int(j.reputacion)))]
        if not self.hon_nivel():
            return partes[0] + tr(". Las consecuencias están apagadas: la fama cuenta como antes.")
        f = self.hon_fama_factor()
        if f > 1:
            partes.append(tr('Pierdes: como nadie te conoce, los guardaespaldas te cobran un {int} por ciento más').format(int=(int(round((f - 1) * 100)))))
        elif f < 1:
            partes.append(tr('Ganas: los guardaespaldas te cobran un {int} por ciento menos y los sobornos salen mejor').format(int=(int(round((1 - f) * 100)))))
        if self.negocios_tuyos():
            partes.append(tr("Las bandas respetan tus negocios y no te piden dinero") if self.hon_protegido()
                          else tr('Sin fama, sin banda y sin escolta, tus negocios son presa fácil: alguna banda intentará cobrarte «protección». Con {entero} de fama te dejan en paz').format(entero=(AJ.entero('fama_respeto'))))
        return ". ".join(partes) + "."

    def hon_doble_txt(self):
        j, h = self.j, self.hon()
        if not self.hon_nivel():
            return tr("Doble vida: con las consecuencias apagadas, nadie ata cabos.")
        negro = int(h.get("negro", 0))
        t = tr('Doble vida: {hon_sospecha_txt}.').format(hon_sospecha_txt=(self.hon_sospecha_txt()))
        if not self.hon_vida_formal():
            return t + tr(" Ahora mismo no tienes nada que perder: ni contrato, ni negocio, ni el aprecio de los vecinos.")
        if negro >= 100:
            t += tr(' Dinero que no podrías justificar: unos {negro} euros').format(negro=(negro)) + (tr(", bastante para que una inspección lo note.") if negro >= AJ("negro_umbral") else ".")
        t += tr(" Te protege tu abogado.") if self.hon_abogado() else tr(" No tienes abogado.")
        return t
