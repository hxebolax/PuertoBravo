"""Vida íntima, solo con el contenido para adultos activado: ligar con cualquiera, aventuras, encuentros
con la pareja, protección y salud sexual.

Todo se cuenta de forma sensual pero sin escenas explícitas: el juego describe el ambiente, el deseo y
lo que cambia después, y deja el resto a la imaginación. Todas las personas son adultas y siempre
pueden decir que no; un no se respeta y no hay ninguna opción para forzar a nadie.
"""
from .i18n import tr
import random

from . import gente
from .charla import ficha

# tipo de encuentro: (nombre, lo que se cuenta, ánimo que da, horas)
ENCUENTROS = {
    "romantico": (tr("Una noche romántica"), [tr("Cenáis despacio, con velas, y os quedáis hablando hasta que sobran las palabras."),
                                          tr("Suena música bajita. Bailáis en el salón, muy cerca, y lo demás llega solo."),
                                          tr("Os miráis un rato largo antes del primer beso. La noche se hace corta.")], 24, 8),
    "apasionado": (tr("Una noche apasionada"), [tr("No llegáis ni a encender la luz. La ropa va quedando por el pasillo."),
                                            tr("Os buscáis con prisa, como si llevarais semanas esperándolo. Nadie duerme mucho."),
                                            tr("La puerta se cierra de un golpe y ya no hay nada más en el mundo que vosotros dos.")], 26, 8),
    "jugueton": (tr("Una noche de risas y juegos"), [tr("Empezáis de broma, con cosquillas y almohadas, y acabáis sin aliento por otros motivos."),
                                                  tr("Os retáis, os provocáis, os reís. Es de esas noches en las que todo vale si lo queréis los dos."),
                                                  tr("Entre risas y susurros descubrís un par de cosas nuevas el uno del otro.")], 22, 7),
    "tranquilo": (tr("Una noche tranquila"), [tr("Un masaje lento, una ducha larga, y os dormís abrazados."),
                                          tr("Hoy no hay prisa. Caricias, la ventana abierta y el mar de fondo."),
                                          tr("Os quedáis piel con piel, hablando bajito, hasta que os vence el sueño.")], 20, 9),
}
GESTOS = {
    "beso": (tr("Darle un beso"), 4, 4, 35, tr("Le das un beso. {n} sonríe y te lo devuelve.")),
    "baile": (tr("Bailar juntos"), 5, 5, 20, tr("Bailáis pegados un par de canciones. {n} se deja llevar.")),
    "masaje": (tr("Darle un masaje"), 6, 5, 45, tr("Le das un masaje en los hombros. {n} cierra los ojos y suspira.")),
    "susurro": (tr("Decirle algo al oído"), 3, 3, 30, tr("Le dices algo al oído. {n} se ríe y te mira de otra manera.")),
}
ARTICULOS = [
    {"id": "preservativos", "nombre": tr("Caja de preservativos"), "precio": 9, "unidades": 6, "desc": tr("Seis unidades. Evitan sustos: sin ellos, cada encuentro con alguien a quien no conoces bien tiene su riesgo.")},
    {"id": "lenceria", "nombre": tr("Lencería fina"), "precio": 60, "afinidad": 9, "desc": tr("Un regalo para tu pareja, o para estrenarlo en vuestra próxima noche: la hace más especial.")},
    {"id": "aceite", "nombre": tr("Aceite de masaje"), "precio": 22, "afinidad": 5, "desc": tr("Con olor a naranja. Mejora las noches tranquilas y los masajes.")},
    {"id": "velas", "nombre": tr("Velas aromáticas"), "precio": 14, "afinidad": 4, "desc": tr("Para las noches románticas.")},
    {"id": "juguete", "nombre": tr("Un juguete para dos"), "precio": 45, "afinidad": 7, "desc": tr("Para parejas con confianza. Mejora las noches de risas y juegos.")},
]
MEJORA = {"romantico": "velas", "tranquilo": "aceite", "jugueton": "juguete", "apasionado": "lenceria"}


class Intimidad:
    """Mixin de Partida."""

    def me_atrae(self, genero):
        pref = self.cfg["atraccion"]
        return pref == "todos" or (pref == "mujeres" and genero == "m") or (pref == "hombres" and genero == "h")

    def articulos_intimos(self):
        return ARTICULOS

    def comprar_articulo(self, art):
        j = self.j
        if not self.pagar(art["precio"]):
            return False
        j.intimos[art["id"]] = j.intimos.get(art["id"], 0) + art.get("unidades", 1)
        self.decir(tr('Compras {lower}. Tienes {v}. Te quedan {dinero} euros.').format(lower=(art['nombre'].lower()), v=(j.intimos[art['id']]), dinero=(j.dinero)), True)
        return True

    # ------------------------------------------------------------- ligar
    def ligar(self, q):
        """Coquetear con una persona de la calle. Puede salir bien, regular o mal; un no es un no."""
        j = self.j
        f = ficha(q)
        n = f["nombre"]
        if not self.me_atrae(f["genero"]):
            return tr('{n} no es tu tipo. Lo puedes cambiar en Opciones, Contenido para adultos.').format(n=(n))
        if f.get("calabazas"):
            return tr('{n} ya te dijo que no. Déjalo estar.').format(n=(n))
        mi_genero = self.cfg["mi_genero"]
        compatible = f["disponible"] and (mi_genero == "x" or mi_genero in f["le_atraen"])
        encanto = f["confianza"] + (j.animo - 50) * 0.3 + min(20, j.reputacion * 0.15) + j.ciudadania * 0.1 + random.uniform(-15, 15)
        self.son("murmullo", xy=(q.x, q.y), vol=0.5)
        f["coqueteos"] = f.get("coqueteos", 0) + 1
        if not compatible or (f["coqueteos"] > 4 and f["confianza"] < 30):
            f["calabazas"] = True
            self._trato(f, -3)
            self.cambiar_animo(-2)
            return f"{n}: " + random.choice([tr("Eres muy amable, pero no estoy por la labor."), tr("Gracias, pero tengo pareja."), tr("No eres mi tipo, lo siento. Sin malos rollos.")])
        if encanto < 12:
            self._trato(f, 2)
            return f"{n}: " + random.choice([tr("Uy, qué directo. Primero invítame a algo, ¿no?"), tr("Ja. Tú no pierdes el tiempo. Ya veremos."), tr("No vayas tan deprisa, que acabamos de conocernos.")])
        self._trato(f, 9 if gente.caracter(f["caracter"])["cumplido"] > 5 else 6)
        self.cambiar_animo(3)
        f["interes"] = True
        return f"{n}: " + random.choice([tr("Pues tú tampoco estás nada mal."), tr("Me gusta cómo me miras. Sigue hablando."), tr("¿Siempre eres así, o es que hoy te has levantado con suerte?")]) + tr(" Le gustas.")

    def mostrar_interes(self, q):
        """Sin el contenido para adultos, con la vida sentimental apta para todos: decirle a alguien de la calle que te
        gustaría tener una cita. Lo mismo que coquetear en cuanto a quién puede decir que sí, pero contado sin nada de
        coqueteo, con las frases de los datos (vida.json, encuentros). Un no es un no."""
        from .encuentros import AJ
        j = self.j
        f = ficha(q)
        n = f["nombre"]
        if not self.me_atrae(f["genero"]):
            return tr('{n} no es tu tipo.').format(n=n)
        if f.get("calabazas"):
            return tr('{n} ya te dijo que no. Déjalo estar.').format(n=(n))
        mi_genero = self.cfg["mi_genero"]
        compatible = f["disponible"] and (mi_genero == "x" or mi_genero in f["le_atraen"])
        encanto = f["confianza"] + (j.animo - 50) * 0.3 + min(20, j.reputacion * 0.15) + j.ciudadania * 0.1 + random.uniform(-15, 15)
        self.son("murmullo", xy=(q.x, q.y), vol=0.5)
        f["coqueteos"] = f.get("coqueteos", 0) + 1
        if not compatible or (f["coqueteos"] > 4 and f["confianza"] < 30):
            f["calabazas"] = True
            self._trato(f, -3)
            self.cambiar_animo(-2)
            return AJ.frase("frases_interes_no", n=n)
        if encanto < 12:
            self._trato(f, 2)
            return AJ.frase("frases_interes_pronto", n=n)
        self._trato(f, 6)
        self.cambiar_animo(2)
        f["interes"] = True
        return AJ.frase("frases_interes_si", n=n)

    def _interes_mutuo(self, f):
        genero = self.cfg["mi_genero"]
        return (f["edad"] >= 18 and f["disponible"] and self.me_atrae(f["genero"])
                and (genero == "x" or genero in f["le_atraen"])
                and bool(f.get("interes")) and not f.get("calabazas") and not f.get("ofendido"))

    def intercambiar_numero(self, q):
        """Daros el número para una cita: esa persona pasa a tu Vida social, con una ficha hecha de lo que sabes de ella
        (nunca lo que habéis hablado), y desde ahí podéis quedar y te puede llamar para invitarte. True si ya lo tenéis."""
        from uuid import uuid4
        from .encuentros import AJ
        f = ficha(q)
        if not self.vida_sentimental() or f["edad"] < 18:
            return False
        if self.en_servidor:
            self.decir(tr("En un servidor en línea no se pueden intercambiar números para una cita."), True)
            return False
        if f.get("contacto_id") in self.j.relaciones:
            return True
        if not self._interes_mutuo(f) or f["confianza"] < AJ.entero("numero_confianza"):
            self.decir(AJ.frase("frases_numero_no", n=f["nombre"]), True)
            return False
        lugares = [l for l in self.mundo.lugares.values() if not l.d.get("adultos") and l.id not in self.j.propiedades]
        publicos = [l for l in lugares if l.tipo in ("bar", "taberna", "comida", "pizzeria", "tienda", "ropa", "cine", "gimnasio", "farmacia", "feria", "loteria", "plaza")]
        lugares = publicos or lugares
        if not lugares:
            return False
        lugar = min(lugares, key=lambda l: (l.x - q.x) ** 2 + (l.y - q.y) ** 2)
        acts = [a["id"] for a in self.dato_adulto("actividades")]
        regalos = [g["id"] for g in self.dato_adulto("regalos")]
        from .laboratorio import RITMOS
        pid = "contacto_" + uuid4().hex
        pers = {"id": pid, "nombre": f["nombre"] + " " + f["apellido"], "edad": f["edad"], "genero": f["genero"], "oficio": f["oficio"],
                "caracter": f["caracter"], "lugar": lugar.id, "desc": f["oficio"],
                "gustos": random.sample(acts, min(2, len(acts))), "ritmo": random.choice(RITMOS)}
        if regalos:
            pers["regalo"] = random.choice(regalos)
        r = self.relacion(pid)
        r.update(contacto=pers, afinidad=min(AJ.entero("numero_afinidad"), max(5, int(f["confianza"]))))
        f["contacto_id"] = pid
        self.son("movil", cat="interfaz", vol=0.5)
        self.decir(AJ.frase("frases_numero_si", n=pers["nombre"]), True)
        return True

    def puede_proponer(self, q):
        f = ficha(q)
        return bool(f.get("interes")) and f["confianza"] >= 35 and not f.get("calabazas")

    def proponer_aventura(self, q, en_hotel=False):
        """Proponerle a alguien que acaba de conocer pasar la noche juntos. Devuelve True si acepta."""
        j = self.j
        f = ficha(q)
        n = f["nombre"]
        if j.estrellas:
            self.app.son("error")
            self.decir(tr("Con la policía detrás no es momento."), True)
            return False
        if not self.puede_proponer(q):
            self.decir(f"{n}: " + random.choice([tr("Para, para. Todavía no."), tr("No tan rápido. Conóceme un poco más."), tr("Me caes bien, pero no.")]), True)
            self._trato(f, -4)
            return False
        if f["confianza"] + random.uniform(-10, 20) < 45:
            self.decir(tr('{n}: Hoy no. Pero quédate con mi número.').format(n=(n)), True)
            return False
        casa = next((l for l in self.mundo.lugares.values() if l.tipo == "casa" and l.id in j.propiedades), None)
        if casa is None or en_hotel:
            if not self.pagar(self.precio("hotel_cita", 70)):
                return False
            donde = tr("un hotel")
        else:
            donde = casa.nombre
            if self.aventura_en_casa(casa):                      # tu pareja vive ahí, y estaba en casa
                return False
        j.stats["aventuras"] = j.stats.get("aventuras", 0) + 1
        self.personas = [x for x in self.personas if x is not q]
        self.encuentro(n, random.choice(["apasionado", "jugueton", "romantico"]), donde, desconocido=True, perfil=f)
        self.cambiar_reputacion(1)
        if j.pareja:
            self.celos()
        return True

    # --------------------------------------------------------- encuentros
    def _proteccion(self, desconocido):
        """Usa un preservativo si lo llevas. Sin él, con alguien a quien no conoces hay riesgo."""
        j = self.j
        if j.intimos.get("preservativos", 0) > 0:
            j.intimos["preservativos"] -= 1
            return tr(" Habéis tenido cuidado.")
        if desconocido and not j.its and random.random() < 0.12:
            j.its = self.dia
            return tr(" No habéis usado protección.")
        return tr(" No lleváis protección.") if desconocido else ""

    def encuentro(self, nombre, tipo, donde, desconocido=False, pid=None, sintonia=None, perfil=None, escena=None):
        """Una noche con alguien. Se cuenta sin detalles explícitos y tiene efectos en el ánimo, la salud y la relación.

        Con la opción «la noche, paso a paso», antes se juega: decides tú qué haces y la otra persona responde. Lo bien
        que os entendáis (sintonía, de 0 a 1) cambia el ánimo que te deja y lo que os acerca.

        Con la opción «escenas privadas con lenguaje directo», antes hay una escena (escenas_privadas.py): la otra persona
        propone, tú decides, y con cada persona puede salir uno de sus relatos. `perfil` es la ficha de alguien de la calle
        (su carácter elige sus relatos) y `escena`, las líneas que cuenta la escena al acabar. Devuelve True si empieza algo.
        """
        from .menus import Dialogo
        j = self.j
        participante = (self.persona_social(pid) if pid else None) or perfil or {}
        if participante.get("edad", 18) < 18:                  # nunca con menores, por si un mod o unos datos lo intentan
            return False
        if escena is None and sintonia is None and self.cfg["escenas_directas"] and self.modo_adulto() and not self.en_servidor:
            from .escenas_privadas import escena_de, ofrecer
            if escena_de(self, tipo) is not None:
                self._a_la_partida()
                self.son("puerta_entrar", cat="interfaz", vol=0.6)
                if ofrecer(self, nombre, tipo, donde, lambda lineas, s: self.encuentro(nombre, tipo, donde, desconocido, pid, sintonia=s, perfil=perfil, escena=lineas),
                           participante=participante, pid=pid):
                    return True
        if self.cfg["noche_por_pasos"] and sintonia is None and escena is None:
            from .laboratorio import Noche
            self._a_la_partida()
            self.son("puerta_entrar", cat="interfaz", vol=0.6)
            Noche(self, nombre, donde, lambda s: self.encuentro(nombre, tipo, donde, desconocido, pid, sintonia=s, perfil=perfil),
                  habitual=participante.get("ritmo")).empezar()
            return True
        titulo, frases, animo, horas = ENCUENTROS[tipo]
        if sintonia is not None:
            animo = int(animo * (0.6 + 0.6 * sintonia))
            if pid:
                self.sumar_afinidad(pid, int(round(6 * sintonia)))
        extra = ""
        mejora = MEJORA.get(tipo)
        if mejora and j.intimos.get(mejora, 0) > 0:
            j.intimos[mejora] -= 1
            animo += 6
            extra = " " + {"velas": tr("Las velas hacen su parte."), "aceite": tr("El aceite de naranja lo cambia todo."), "juguete": tr("Estrenáis lo que compraste, entre risas."),
                           "lenceria": tr("La lencería dura puesta muy poco.")}[mejora]
            if pid:
                self.sumar_afinidad(pid, 4)
        proteccion = self._proteccion(desconocido)
        self.pasar_horas(horas, dormir=True)
        j.salud = j.salud_max
        self.cambiar_animo(animo)
        j.stats["noches"] = j.stats.get("noches", 0) + 1
        self.son("puerta_entrar", cat="interfaz", vol=0.6)
        self.son("noche_juntos", cat="interfaz")
        self._a_la_partida()
        if escena:                                              # la escena privada: lo que ha contado, y la mañana
            primera, *resto = escena
            lineas = [primera + proteccion + extra, *resto,
                      tr('Por la mañana, son las {hora_txt} y te sientes {animo_txt}.').format(hora_txt=self.hora_txt(), animo_txt=self.animo_txt())]
            self.app.abrir(Dialogo(self.app, [(tr("Narrador"), x) for x in lineas]))
            return True
        self.app.abrir(Dialogo(self.app, [
            (tr("Narrador"), tr('{titulo} con {nombre}, en {donde}. {choice}{extra}').format(titulo=(titulo), nombre=(nombre), donde=(donde), choice=(random.choice(frases)), extra=(extra))),
            (tr("Narrador"), tr('Lo que pasa después es solo vuestro.{proteccion} Por la mañana, son las {hora_txt} y te sientes {animo_txt}.').format(proteccion=(proteccion), hora_txt=(self.hora_txt()), animo_txt=(self.animo_txt())))]))
        return True

    def _a_la_partida(self):
        """Cierra los menús abiertos (el móvil, la charla) para que la noche se cuente sobre el juego."""
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()

    def gesto(self, pid, pers, clave):
        """Un gesto de cariño con alguien con quien tienes una relación: beso, baile, masaje o un susurro."""
        nombre, afin, animo, minimo, frase = GESTOS[clave]
        r = self.relacion(pid)
        if self.hielo_ex(r):                                     # recién rota la relación, ni se te ocurra (issue 41)
            self.decir(self.frase_hielo("gesto", pers), True)
            return False
        if r["afinidad"] < minimo and self.j.pareja != pid:
            self.decir(tr('{nombre} se aparta con una sonrisa. Todavía es pronto para eso.').format(nombre=(pers['nombre'])), True)
            return False
        if self.apesta():                                        # oliendo mal, nada de besos (necesidades.py)
            from .necesidades import AJ as NEC
            self.decir(NEC.frase("frases_gesto_sucio", n=pers["nombre"]), True)
            return False
        if self._hecho_hoy(r, "gesto_" + clave):
            self.decir(tr("Eso ya lo habéis hecho hoy. No hay que gastarlo."), True)
            return False
        if clave == "masaje" and self.j.intimos.get("aceite", 0) > 0:
            self.j.intimos["aceite"] -= 1
            afin += 3
        self.sumar_afinidad(pid, afin)
        self.cambiar_animo(animo)
        self.son("cita" if clave != "beso" else "afinidad_sube", cat="interfaz", vol=0.7)
        self.decir(frase.format(n=pers["nombre"]) + tr(' Ahora {afinidad_txt}.').format(afinidad_txt=(self.afinidad_txt(r))), True)
        if clave != "susurro":                                   # un beso o un baile con otra persona también se ven (encuentros.py)
            self.celos(pid)
        return True

    # ------------------------------------------------------------- salud
    def dia_intimidad(self):
        """Cada medianoche: una infección sin tratar baja el ánimo y, si tienes pareja, acaba sabiéndose."""
        j = self.j
        if not j.its:
            return
        dias = self.dia - j.its
        if dias >= 2:
            self.cambiar_animo(-4)
            if dias == 2:
                self.decir(tr("Notas molestias desde hace un par de días. Deberías pasar por una farmacia o un hospital a hacerte una prueba."))
            if dias >= 5 and j.pareja:
                pers = self.persona_social(j.pareja)
                if pers:
                    self.sumar_afinidad(j.pareja, -20)
                    self.decir(tr('{nombre} se ha enterado de lo tuyo y no le ha hecho ninguna gracia.').format(nombre=(pers['nombre'])))

    def prueba_y_tratamiento(self):
        """En farmacias y hospitales: prueba gratuita y, si hace falta, tratamiento."""
        j = self.j
        if not j.its:
            self.decir(tr("Te haces la prueba. Todo está bien."), True)
            return True
        coste = self.precio("tratamiento_its", 120)
        if not self.pagar(coste):
            return False
        j.its = 0
        self.son("curar", cat="interfaz")
        self.cambiar_animo(5)
        self.decir(tr('La prueba da positivo. Te ponen tratamiento por {coste} euros y en unos días estarás bien. La próxima vez, con protección.').format(coste=(coste)), True)
        return True

    def estado_intimo_txt(self):
        j = self.j
        partes = []
        if j.intimos.get("preservativos", 0):
            partes.append(tr('llevas {preservativos} preservativos').format(preservativos=(j.intimos['preservativos'])))
        if j.its and self.dia - j.its >= 2:
            partes.append(tr("tienes molestias que deberías mirarte"))
        return ". ".join(partes).capitalize() + "." if partes else ""
