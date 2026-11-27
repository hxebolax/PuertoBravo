"""Vivir en pareja y planes nuevos juntos (1.7.1). Solo con el contenido para adultos activado, que es donde están las
relaciones; lo de mudarse, además, con su propia opción, que viene apagada.

Cada persona decide: a tu pareja le puedes pedir que se venga a vivir contigo, y dice que sí o que no según cómo estéis
y según cómo sea ella (hay quien no deja su casa por nadie). Si acepta, vive en una de tus casas: te la encuentras
allí, cocina para ti o te pide que cocines tú, te pide cosas de vez en cuando y se nota si no apareces. Se le puede
pedir que se vaya.

Los planes nuevos (un paseo, el cine, una cena, una travesía en barco...) son para cualquier pareja, viva o no contigo:
cada uno se cuenta con una escena hablada distinta cada vez. Los planes están en los datos (vida.json, planes_pareja) y
los números y las frases, en la sección convivencia.
"""
from .i18n import tr
import random
import zlib

from .ajustes import Ajustes

AJ = Ajustes("convivencia", {
    "afinidad_minima": 70, "citas_minimas": 3, "nunca_prob": 20, "espera_dias": 5, "ausencia_dias": 2,
    "peticion_prob": 30, "peticion_dias": 2, "peticion_repite_dias": 3, "peticion_premio": 6, "peticion_castigo": 5, "cocina_salud": 30, "cocina_hambre": 70,
    "dinero_afinidad": 2, "dinero_tope": 10, "dinero_minimo": 50,
}, {
    "frases_si": [tr("{n} se queda en silencio un momento, y luego sonríe: Creía que no me lo ibas a pedir nunca. Sí."),
                  tr("{n}: ¿Vivir juntos? Dame dos días para recoger mis cosas. Claro que sí."), tr("{n} te abraza antes de contestar. Es que sí.")],
    "frases_no_pronto": [tr("{n}: Me gustas mucho, pero es pronto. Vamos poco a poco."), tr("{n}: Todavía no. No quiero que lo estropeemos por correr."),
                         tr("{n} te coge la mano: Aún no estamos ahí. Pregúntamelo más adelante.")],
    "frases_no_nunca": [tr("{n}: Te quiero, pero mi casa es mi casa. No me pidas eso."), tr("{n}: Yo no valgo para vivir con nadie, y no es por ti. Así estamos bien."),
                        tr("{n} niega despacio: Cada uno en su casa. Es como mejor me va.")],
    "frases_llega": [tr("{n} llega con dos maletas y una planta. {casa} ya no es solo tuya."), tr("Ayudas a {n} a subir las cajas a {casa}. Desde hoy vivís bajo el mismo techo."),
                     tr("{n} deja su cepillo de dientes junto al tuyo, en {casa}. Ya está hecho.")],
    "frases_llegais": [tr("Llegáis juntos. {n} deja las llaves en el recibidor y se quita los zapatos: por fin en casa."), tr("Entráis los dos. {n} enciende la luz del salón y se deja caer en el sofá."), tr("{n} abre la puerta, cuelga el abrigo y te pregunta si cenáis algo.")],
    "frases_recibe": [tr("{n} te oye llegar: ¿Qué tal el día?"), tr("{n} está en el sofá, con los pies en alto, y te hace sitio."), tr("{n} canturrea en la cocina. Te da un beso al pasar."),
                      tr("{n} levanta la vista del móvil y sonríe al verte."), tr("Huele a café recién hecho. {n} te sirve una taza sin preguntar.")],
    "frases_ausente_fuera": [tr("En casa no hay nadie. {n} anda con sus cosas: luego vuelve."), tr("Hay una nota en la nevera: «He salido a hacer unos recados. Luego nos vemos»."), tr("{n} no está, y en su sitio de siempre tampoco: anda a lo suyo.")],
    "frases_ausente": [tr("En casa no hay nadie: {n} está en {lugar}."), tr("Hay una nota en la nevera: «Estoy en {lugar}. Luego nos vemos»."), tr("{n} no está: a estas horas anda por {lugar}.")],
    "frases_charla": [tr("Os contáis el día sin prisa."), tr("{n} te cuenta un cotilleo del barrio y acabáis riendo."), tr("Habláis de lo que haréis el fin de semana."),
                      tr("{n} te pregunta en qué andas metid[o|a]. Cambias de tema, y lo nota."), tr("Os quedáis un rato en silencio, a gusto.")],
    "frases_cocina": [tr("{n} ha hecho la cena: arroz con lo que había, y está buenísimo."), tr("{n} saca del horno algo que huele de maravilla."),
                      tr("{n} ha preparado tortilla y una ensalada. Coméis en la cocina, de pie, picando del mismo plato."), tr("Hoy {n} se ha lucido: guiso de los de mojar pan.")],
    "frases_cocinas_tu": [tr("{n}: Hoy te toca a ti. Te pones el delantal y sale algo decente."), tr("{n} te tiende la sartén: Sorpréndeme. Lo consigues, a medias."),
                          tr("Cocinas tú. {n} dice que está rico y repite, que es lo que cuenta.")],
    "frases_se_va": [tr("{n} recoge sus cosas en silencio. Dice que lo entiende, pero no te mira al irse."), tr("{n}: Si es lo que quieres... Mañana no quedará nada mío aquí."),
                     tr("{n} mete su ropa en una maleta. La planta se la lleva.")],
    "frases_se_va_sola": [tr("{n} ha recogido sus cosas y se ha ido de {casa}."), tr("Al volver, los armarios de {n} están vacíos.")],
    "frases_ausencia": [tr("{n} te escribe: hace días que no pasas por casa. No le hace gracia."), tr("{n}: ¿Vives aquí o solo recibes el correo? Hace días que no te veo.")],
    "frases_peticion_cena": [tr("{n}: Hoy no tengo ganas de cocinar. ¿Pides algo a domicilio y cenamos aquí?"), tr("{n}: ¿Y si esta noche cenamos algo de encargo, aquí en casa?")],
    "frases_peticion_plan": [tr("{n}: Hace mucho que no salimos. Llévame a algún sitio, anda."), tr("{n}: Necesito que me dé el aire. Hagamos algo juntos estos días.")],
    "frases_peticion_dormir": [tr("{n}: Casi no paras en casa. Quédate a dormir esta noche."), tr("{n}: Me gustaría despertarme contigo mañana, para variar.")],
    "frases_peticion_mueble": [tr("{n}: Esta casa necesita un arreglo. ¿Por qué no compramos algún mueble?"), tr("{n}: Si vamos a vivir aquí, habrá que amueblarlo un poco mejor.")],
    "frases_peticion_regalo": [tr("{n}: No te pido mucho, pero un detalle de vez en cuando..."), tr("{n} suspira: Antes me traías cosas.")],
    "frases_peticion_ok": [tr("{n} lo agradece de verdad: se le nota."), tr("{n}: Gracias. Estas cosas son las que cuentan."), tr("A {n} se le ilumina la cara.")],
    "frases_peticion_mal": [tr("{n} no dice nada, pero lleva la cuenta: no hiciste lo que te pidió."), tr("{n}: Te lo pedí hace días. Da igual, déjalo.")],
    "frases_celos_casa": [tr("{n} estaba en casa. No hay nada que explicar: coge el abrigo y se va dando un portazo."),
                          tr("Abres la puerta y {n} está en el salón. Os mira a los dos, recoge el bolso y sale sin decir palabra.")],
    "cosas_compra": [tr("unas zapatillas nuevas"), tr("un libro que tenía pendiente"), tr("unos auriculares"), tr("una planta para el balcón"), tr("entradas para un concierto"), tr("ropa para el invierno"), tr("una cafetera como las de los bares"), tr("un perfume"), tr("unas gafas de sol"), tr("material para su afición")],
    "frases_dinero": [tr("{n} coge el dinero con cara de sorpresa: «¿Para mí? Pues me voy a comprar {cosa}»."), tr("{n} te da un beso por la cara de pena que pones al soltar los billetes. Dice que se va a comprar {cosa}."), tr("{n} cuenta los billetes dos veces y sonríe: ya sabe en qué se lo va a gastar, en {cosa}.")],
    "frases_compra": [tr("{n} te enseña {cosa} que se compró con lo que le diste. No para de darte las gracias."), tr("{n} no se quita {cosa} de encima desde que se lo compró: se nota que le hacía ilusión."), tr("{n}: «¿Has visto {cosa}? Gracias otra vez». Lo dice de corazón.")],
    "frases_mudanza": [tr("Cargáis las cajas entre los dos y dejáis {antes}. Desde hoy vivís en {casa}."), tr("{n} elige el dormitorio de {casa} antes de deshacer la primera maleta. Ya vivís allí."), tr("Una furgoneta, dos viajes y una planta que casi no sobrevive: la mudanza a {casa} está hecha.")],
    "frases_peticion_dinero": [tr("{n}: Este mes voy justo de dinero. ¿Me echas una mano?"), tr("{n}: He visto algo que me encantaría comprarme, pero no me llega. Si me ayudas, te lo agradezco.")],
}, cero=("nunca_prob", "peticion_prob", "peticion_repite_dias", "peticion_premio", "peticion_castigo", "citas_minimas", "dinero_afinidad"))

DINEROS = (50, 100, 250, 500)

PLANES = [
    {"id": "paseo_barrio", "nombre": tr("Dar una vuelta por el barrio, sin rumbo"), "precio": 0, "horas": 2, "afinidad": 6, "animo": 5,
     "escenas": [tr("Salís sin rumbo. {n} se para en todos los escaparates y tú finges que te interesan."), tr("Camináis despacio, del brazo. {n} saluda a medio barrio."),
                 tr("Acabáis en un banco, viendo pasar a la gente e inventándole una vida a cada cual."), tr("{n} te enseña el portal donde se crió. No se lo había contado a nadie.")]},
    {"id": "cine_juntos", "nombre": tr("Ir al cine"), "precio": 30, "horas": 3, "afinidad": 7, "animo": 6, "requiere": "cine",
     "escenas": [tr("Elegís la película a suertes. Pierdes tú, pero acaba gustándote."), tr("{n} se come sus palomitas y la mitad de las tuyas."),
                 tr("A media película {n} te coge la mano y ya no la suelta."), tr("Salís discutiendo el final. {n} tiene razón, pero no se la das.")]},
    {"id": "cena_fuera", "nombre": tr("Cenar fuera"), "precio": 60, "horas": 3, "afinidad": 9, "animo": 7, "requiere": "comida",
     "escenas": [tr("El camarero os da la mesa del rincón. {n} pide por los dos y acierta."), tr("Compartís el postre. {n} se queda con la última cucharada."),
                 tr("La cena se alarga. Cierran el restaurante con vosotros dentro, y ni os dais cuenta."), tr("{n} brinda por vosotros. Tú brindas por que no se acabe.")]},
    {"id": "barco", "nombre": tr("Una travesía en barco al atardecer"), "precio": 90, "horas": 4, "afinidad": 12, "animo": 9, "requiere": "embarcadero",
     "escenas": [tr("Alquiláis una lancha y salís despacio. {n} quiere llevar el timón, y le dejas."), tr("Paráis el motor mar adentro. Solo se oye el agua contra el casco."),
                 tr("El sol se mete en el mar y {n} apoya la cabeza en tu hombro."), tr("Volvéis a puerto con las luces ya encendidas, con sal en la piel y sin decir nada.")]},
    {"id": "playa", "nombre": tr("Una tarde de playa"), "precio": 10, "horas": 4, "afinidad": 8, "animo": 8,
     "escenas": [tr("Extendéis las toallas donde rompe la brisa. {n} se duerme al sol."), tr("{n} te mete en el agua a traición. Está helada."),
                 tr("Coméis pipas mirando a los que pescan desde el espigón."), tr("Os quedáis hasta que refresca, con arena hasta en los bolsillos.")]},
    {"id": "compras", "nombre": tr("Ir de compras"), "precio": 80, "horas": 3, "afinidad": 7, "animo": 4, "requiere": "ropa",
     "escenas": [tr("{n} se prueba media tienda. Tú sujetas las perchas."), tr("Te convence para llevarte una camisa que no te habrías puesto nunca."),
                 tr("Salís con dos bolsas y la sensación de haber gastado de más."), tr("{n} te pregunta cuál le queda mejor. Aciertas de milagro.")]},
    {"id": "feria_juntos", "nombre": tr("Una noche de feria"), "precio": 25, "horas": 3, "afinidad": 8, "animo": 8, "requiere": "feria",
     "escenas": [tr("{n} te gana en la caseta de tiro y no deja de recordártelo."), tr("Compartís un algodón de azúcar que se os pega a todo."),
                 tr("Subís a la noria. Arriba del todo, {n} te besa."), tr("Os reís hasta que os duele la tripa en los coches de choque.")]},
    {"id": "baile_juntos", "nombre": tr("Salir a bailar"), "precio": 40, "horas": 4, "afinidad": 9, "animo": 8, "requiere": "club", "adultos": True,
     "escenas": [tr("La pista está llena, pero {n} baila como si no hubiera nadie más."), tr("Bailáis muy cerca hasta que cierran."),
                 tr("{n} te arrastra a la pista con la canción que le gusta."), tr("Volvéis a casa andando, con los zapatos en la mano.")]},
    {"id": "noche_casa", "nombre": tr("Una noche de sofá, película y manta"), "precio": 0, "horas": 3, "afinidad": 6, "animo": 6, "en_casa": True,
     "escenas": [tr("Empezáis tres películas y no acabáis ninguna."), tr("{n} se duerme en tu hombro a los diez minutos."),
                 tr("Pedís perdón al vecino por las risas."), tr("La manta es pequeña para dos. Mejor.")]},
]


def planes(p):
    lista = [x for x in p.datos.get("planes_pareja", []) if isinstance(x, dict) and x.get("nombre")]
    return lista or PLANES


class Convivencia:
    """Mixin de Partida."""

    def convivencia_activa(self):
        if self.en_servidor or not self.vida_sentimental():
            return False
        return (self.modo_adulto() and bool(self.cfg["pareja_convive"])) or bool(self.hon_estado_pareja())      # prometidos o casados, siempre

    def conviviente(self):
        """Los datos de quien vive contigo, o None."""
        j = self.j
        return self.persona_social(j.convive) if j.convive and self.vida_sentimental() else None

    def casa_comun(self):
        return self.lug(self.j.convive_casa) if self.j.convive else None

    def _disposicion(self, pers):
        """Cómo es cada persona con lo de vivir juntos: «nunca», o el nivel de afinidad con el que se anima. Es fija en cada partida."""
        quiere = str(pers.get("convivir") or "").strip()
        rng = random.Random(zlib.crc32(f"convivir:{self.j.semilla}:{pers['id']}".encode("utf-8")))
        if quiere == "nunca" or (quiere not in ("si", "facil") and rng.random() * 100 < AJ("nunca_prob")):
            return None
        return AJ("afinidad_minima") + (-8 if quiere == "facil" else rng.uniform(-6, 12))

    def pedir_convivir(self, pers, casa):
        """Le pides a tu pareja que se venga a vivir a una casa tuya. Devuelve (acepta, frase)."""
        j = self.j
        pid, n = pers["id"], pers["nombre"]
        r = self.relacion(pid)
        if not self.convivencia_activa():
            return False, (tr("Vivir en pareja está desactivado. Se activa en Opciones, Contenido para adultos.") if self.modo_adulto()
                           else tr("Para vivir juntos, primero tenéis que estar prometidos."))
        if j.pareja != pid:
            return False, tr('{n} y tú no sois pareja.').format(n=(n))
        if j.convive == pid:
            return False, tr('{n} ya vive contigo.').format(n=(n))
        if casa is None:
            return False, tr("Necesitas una casa tuya en la que vivir los dos.")
        falta = int(r.get("pidio_convivir", -99)) + AJ.entero("espera_dias") - self.dia
        if falta > 0:
            return False, tr('{n} ya te contestó hace poco. Dale tiempo: vuelve a preguntárselo dentro de {falta} {v}.').format(n=(n), falta=(falta), v=(tr('día') if falta == 1 else tr('días')))
        r["pidio_convivir"] = self.dia
        umbral = self._disposicion(pers)
        if umbral is None:
            self.son("afinidad_baja", cat="interfaz", vol=0.5)
            return False, AJ.frase("frases_no_nunca", n=n)
        if r["afinidad"] < umbral or r.get("citas", 0) < AJ("citas_minimas"):
            return False, AJ.frase("frases_no_pronto", n=n)
        j.convive, j.convive_casa, j.convive_desde = pid, casa.id, self.dia
        j.convive_hoy = {"visto": self.dia}
        j.peticion_pareja = None
        r["ultimo"] = self.dia
        self.son("pareja", cat="interfaz")
        self.cambiar_animo(12)
        j.stats["convivencias"] = j.stats.get("convivencias", 0) + 1
        return True, AJ.frase("frases_si", n=n) + " " + AJ.frase("frases_llega", n=n, casa=casa.nombre)

    def fin_convivencia(self, motivo="pedido", callar=False):
        """Deja de vivir contigo: porque se lo pides, porque lo habéis dejado o porque se ha ido ella."""
        j = self.j
        pers = self.persona_social(j.convive) if j.convive else None
        casa = self.lug(j.convive_casa)
        pid = j.convive
        j.convive, j.convive_casa, j.peticion_pareja, j.convive_hoy = "", "", None, {}
        if pers is None:
            return ""
        n = pers["nombre"]
        if motivo == "pedido":
            r = self.relacion(pid)
            r["afinidad"] = max(0, r["afinidad"] - 15)
            r["pidio_convivir"] = self.dia
            self.son("afinidad_baja", cat="interfaz")
            self.cambiar_animo(-6)
            texto = AJ.frase("frases_se_va", n=n)
        else:
            texto = AJ.frase("frases_se_va_sola", n=n, casa=casa.nombre if casa else "tu casa")
        if not callar:
            self.decir(texto)
        return texto

    def pareja_en_casa(self):
        """¿Está ahora en casa quien vive contigo? De noche, siempre; de día, a ratos: tiene su vida.
        Con los horarios de la gente, en sus horas de trabajo está en su sitio y no en casa, y si ha salido a veros
        en otro sitio, tampoco (issue 44): así la casa, la ficha del móvil y la nota de la cocina dicen lo mismo."""
        pers = self.conviviente()
        if not pers:
            return False
        from . import encuentros
        q = encuentros.quedada_en_curso(self, pers["id"])
        if q is not None:
            return q.get("lugar") == self.j.convive_casa
        if encuentros.modo(self) != "apagado" and self.lug(pers.get("lugar")) is not None and encuentros.presente(self, pers):
            return False
        h = int(self.reloj // 60) % 24
        if h >= 19 or h < 9:
            return True
        return random.Random(f"encasa:{self.j.semilla}:{self.dia}:{h // 3}").random() < 0.35

    def saludo_de_casa(self, casa):
        """Al entrar en la casa donde vivís: lo que te encuentras. Cadena vacía si allí no vive nadie contigo."""
        j = self.j
        pers = self.conviviente()
        if pers is None or casa.id != j.convive_casa:
            return ""
        n = pers["nombre"]
        if not self.pareja_en_casa() and getattr(self, "_llegais_juntos", None) != j.convive:
            from . import encuentros
            l = self.lug(pers.get("lugar"))
            if l is None or not encuentros.presente(self, pers):  # si tampoco está en su sitio, no se dice uno donde no la encontrarías (issue 29)
                return AJ.frase("frases_ausente_fuera", n=n)
            return AJ.frase("frases_ausente", n=n, lugar=self.nombre_lugar(l))
        primera = j.convive_hoy.get("visto") != self.dia
        j.convive_hoy["visto"] = self.dia
        self.relacion(j.convive)["ultimo"] = self.dia
        juntos = getattr(self, "_llegais_juntos", None) == j.convive      # habéis llegado los dos: nada de «te oye llegar» (issue 29)
        self._llegais_juntos = None
        texto = AJ.frase("frases_llegais" if juntos else "frases_recibe", n=n)
        pet = self._peticion_nueva(pers) if primera else ""
        return texto + (" " + pet if pet else "")

    # ------------------------------------------------------------------ lo que te pide
    def _peticion_nueva(self, pers):
        j = self.j
        if j.peticion_pareja or random.random() * 100 >= AJ("peticion_prob"):
            return ""
        from . import sistemas
        casa = self.casa_comun()
        ops = ["cena", "plan", "dormir", "regalo", "dinero"]
        if casa is not None and len(sistemas.muebles_de(j, casa)) < len(sistemas.MUEBLES) - 1:
            ops.append("mueble")
        ultima = j.convive_hoy.get("ultima_peticion") if isinstance(j.convive_hoy, dict) else None
        if ultima and self.dia - int(ultima[1]) < AJ.entero("peticion_repite_dias") and len(ops) > 1 and ultima[0] in ops:
            ops.remove(ultima[0])                                # lo que acabas de hacerle no te lo vuelve a pedir enseguida
        que = random.choice(ops)
        j.peticion_pareja = {"que": que, "dia": self.dia, "hasta": self.dia + AJ.entero("peticion_dias"),
                             "muebles": len(sistemas.muebles_de(j, casa)) if casa is not None else 0}
        return AJ.frase("frases_peticion_" + que, n=pers["nombre"])

    def peticion_txt(self):
        pet, pers = self.j.peticion_pareja, self.conviviente()
        if not pet or not pers:
            return ""
        que = {"cena": tr("que pidas cena a domicilio para los dos, en casa"), "plan": tr("que hagáis algún plan juntos"), "dormir": tr("que te quedes a dormir en casa"),
               "mueble": tr("que compres algún mueble nuevo para {casa}").format(casa=self.nombre_lugar(self.casa_comun()) if self.casa_comun() else tr("vuestra casa")),
               "regalo": tr("un detalle: un regalo"),
               "dinero": tr("que le des algo de dinero, al menos {n} euros").format(n=AJ.entero('dinero_minimo'))}.get(pet["que"], tr("algo"))
        return tr('{nombre} te ha pedido {que}. Tienes hasta el día {hasta}.').format(nombre=(pers['nombre']), que=(que), hasta=(pet['hasta']))

    def peticion_cumplida(self, que):
        """Has hecho algo de lo que te pide quien vive contigo (cena, plan, dormir, mueble o regalo)."""
        j = self.j
        pet, pers = j.peticion_pareja, self.conviviente()
        if not pet or not pers or pet.get("que") != que:
            return False
        j.peticion_pareja = None
        if isinstance(j.convive_hoy, dict):
            j.convive_hoy["ultima_peticion"] = [que, self.dia]
        self.sumar_afinidad(j.convive, AJ.entero("peticion_premio"))
        self.cambiar_animo(3)
        self.decir(AJ.frase("frases_peticion_ok", n=pers["nombre"]))
        return True

    # ------------------------------------------------------------------ elegir casa, mudarse y dinero (1.7.2)
    def casas_para_vivir(self):
        """Tus casas en las que se puede vivir en pareja, primero las de esta localidad."""
        casas = [c for c in (self.lug(i) for i in self.j.propiedades) if c is not None and c.tipo == "casa" and not self.alquilada(c.id)]
        return sorted(casas, key=lambda c: c.mapa != self.mundo.id)

    def mudar_convivencia(self, casa):
        """Os mudáis juntos a otra casa tuya, de esta localidad o de otra. Devuelve la frase."""
        j = self.j
        pers = self.conviviente()
        if pers is None:
            return tr("No vives con nadie.")
        if casa is None or casa.id not in j.propiedades:
            return tr("Esa casa no es tuya.")
        if casa.id == j.convive_casa:
            return tr('Ya vivís en {nombre_lugar}.').format(nombre_lugar=(self.nombre_lugar(casa)))
        antes = self.casa_comun()
        j.convive_casa = casa.id
        j.convive_hoy["visto"] = self.dia
        pet = j.peticion_pareja
        if pet and pet.get("que") == "mueble":                   # el mueble que pedía, ahora para la casa nueva
            from . import sistemas
            pet["muebles"] = len(sistemas.muebles_de(j, casa))
        self.son("pareja", cat="interfaz")
        self.cambiar_animo(4)
        return AJ.frase("frases_mudanza", n=pers["nombre"], casa=self.nombre_lugar(casa), antes=self.nombre_lugar(antes) if antes else tr("la casa de antes"))

    def dar_dinero_pareja(self, pers, euros):
        """Le das dinero a tu pareja para que se compre algo. Os acerca según lo que le das, una vez al día; al día
        siguiente te cuenta qué se compró. Cuenta como lo que te había pedido, si te pidió dinero. Devuelve la frase."""
        j = self.j
        pid, n = pers["id"], pers["nombre"]
        r = self.relacion(pid)
        if j.pareja != pid:
            return tr('{n} y tú no sois pareja.').format(n=(n))
        if r.get("hoy", {}).get("dinero") == self.dia:
            return tr('Hoy ya le has dado dinero a {n}. No hace falta más.').format(n=(n))
        if not self.pagar_sin_fiar(int(euros)):
            return ""
        r.setdefault("hoy", {})["dinero"] = self.dia
        cosa = random.choice(AJ.lista("cosas_compra") or [tr("algo que le hacía ilusión")])
        r["compra"] = {"cosa": cosa, "dia": self.dia}
        self.sumar_afinidad(pid, min(AJ.entero("dinero_tope"), int(round(AJ("dinero_afinidad") * euros / 100.0)) + 1))
        self.son("dinero", cat="interfaz")
        texto = AJ.frase("frases_dinero", n=n, cosa=cosa)
        if euros >= AJ("dinero_minimo") and (j.peticion_pareja or {}).get("que") == "dinero" and j.convive == pid:
            self.peticion_cumplida("dinero")
        return texto

    def compra_de_pareja(self):
        """Lo que se compró tu pareja con el dinero que le diste, dicho un día después. Cadena vacía si no hay nada que contar."""
        j = self.j
        if not j.pareja:
            return ""
        pers = self.persona_social(j.pareja)
        r = self.relacion(j.pareja) if pers is not None else {}
        c = r.get("compra")
        if not c or self.dia <= int(c.get("dia", self.dia)):
            return ""
        r.pop("compra", None)
        return AJ.frase("frases_compra", n=pers["nombre"], cosa=c.get("cosa", "algo"))

    # ------------------------------------------------------------------ en casa
    def charla_en_casa(self):
        j = self.j
        pers = self.conviviente()
        r = self.relacion(j.convive)
        if j.convive_hoy.get("charla") == self.dia:
            return tr('Ya habéis hablado un buen rato hoy. {nombre} está a lo suyo.').format(nombre=(pers['nombre']))
        j.convive_hoy["charla"] = self.dia
        self.sumar_afinidad(j.convive, 2)
        self.cambiar_animo(3)
        return AJ.frase("frases_charla", n=pers["nombre"]) + tr(' Ahora {afinidad_txt}.').format(afinidad_txt=(self.afinidad_txt(r)))

    def comer_en_casa(self):
        """Quien vive contigo cocina para los dos o, a veces, te pide que cocines tú. Una vez al día."""
        j = self.j
        pers = self.conviviente()
        if j.convive_hoy.get("comida") == self.dia:
            return tr("Hoy ya habéis comido juntos. Queda algo en la nevera para mañana.")
        j.convive_hoy["comida"] = self.dia
        tu = random.random() < 0.3
        j.salud = min(j.salud_max, j.salud + AJ("cocina_salud"))
        self.ha_comido(AJ("cocina_hambre"))
        self.ha_bebido(60)
        self.mez.sonar("comer", cat="interfaz")
        self.pasar_horas(1)
        self.sumar_afinidad(j.convive, 4 if tu else 2)
        self.cambiar_animo(4)
        return AJ.frase("frases_cocinas_tu" if tu else "frases_cocina", n=pers["nombre"]) + tr(' Salud {int}.{necesidades_txt}').format(int=(int(j.salud)), necesidades_txt=(self.necesidades_txt()))

    def aventura_en_casa(self, casa):
        """Traes a otra persona a la casa donde vive tu pareja. Si está, se acabó. Devuelve True si os ha visto."""
        j = self.j
        pers = self.conviviente()
        if pers is None or casa is None or casa.id != j.convive_casa or not self.pareja_en_casa():
            return False
        pid = j.convive
        r = self.relacion(pid)
        r["afinidad"] = max(0, r["afinidad"] - 45)
        self.marcar_ruptura(r)
        j.pareja = ""
        self.fin_convivencia("sola", callar=True)
        self.son("ruptura", cat="interfaz")
        self.cambiar_animo(-20)
        self.decir(AJ.frase("frases_celos_casa", n=pers["nombre"]))
        return True

    # ------------------------------------------------------------------ planes juntos
    def planes_para(self, pers):
        """Los planes que se pueden hacer ahora con esa persona: (plan, por qué no se puede o cadena vacía)."""
        out = []
        for pl in planes(self):
            motivo = ""
            req = pl.get("requiere")
            if pl.get("en_casa") and not (self.j.convive == pers["id"] and self.casa_aqui() is not None and self.casa_aqui().id == self.j.convive_casa):
                continue                                         # los planes de casa, solo en la casa en la que vivís
            if req and not any(l.tipo == req or (req == "comida" and l.tipo in ("comida", "pizzeria")) for l in self.mundo.lugares.values()):
                motivo = tr("en esta localidad no hay dónde")
            out.append((pl, motivo))
        return out

    def hacer_plan(self, pers, pl):
        """Un plan con tu pareja: se cuenta con una escena hablada, distinta cada vez. Devuelve True si se ha hecho."""
        from .menus import Dialogo
        j = self.j
        pid, n = pers["id"], pers["nombre"]
        r = self.relacion(pid)
        l = self.lug(pers.get("lugar"))
        junto = j.convive == pid or (l is not None and l.mapa == self.mundo.id)
        if not junto:
            self.app.son("error")
            self.decir(tr('{n} está en {v}. Para hacer planes tenéis que estar en la misma localidad.').format(n=(n), v=(self.nombre_lugar(l) if l else tr('otra localidad'))), True)
            return False
        if j.estrellas:
            self.app.son("error")
            self.decir(tr("Con la policía detrás no es momento de planes."), True)
            return False
        if r.get("hoy", {}).get("plan") == self.dia:
            self.decir(tr('Hoy ya habéis hecho un plan. {n} quiere dejar algo para mañana.').format(n=(n)), True)
            return False
        if not self.pagar(int(pl.get("precio", 0))):
            return False
        r.setdefault("hoy", {})["plan"] = self.dia
        r["planes"] = r.get("planes", 0) + 1
        r["citas"] = r.get("citas", 0) + 1
        escenas = [str(e) for e in pl.get("escenas", []) if str(e).strip()] or [tr("Pasáis un buen rato juntos.")]
        vistas = list(r.setdefault("escenas", {}).get(pl["id"], []))
        frescas = [e for e in escenas if e not in vistas]                     # no se repite una escena hasta haberlas oído todas
        if len(frescas) < min(2, len(escenas)):
            vistas, frescas = [], list(escenas)
        elegidas = random.sample(frescas, min(2, len(frescas)))
        r["escenas"][pl["id"]] = vistas + elegidas
        self.pasar_horas(float(pl.get("horas", 2)))
        self.sumar_afinidad(pid, int(pl.get("afinidad", 6)))
        self.cambiar_animo(int(pl.get("animo", 5)))
        j.stats["planes_pareja"] = j.stats.get("planes_pareja", 0) + 1
        self.son("cita", cat="interfaz")
        while len(self.app.pila) > 1 and self.app.pila[-1] is not self:
            self.app.pila.pop()
        self.app.teclas.clear()
        lineas = [(tr("Narrador"), tr('{nombre}, con {n}.').format(nombre=(pl['nombre']), n=(n)))] + [(tr("Narrador"), e.replace("{n}", n)) for e in elegidas]
        lineas.append((tr("Narrador"), tr('Son las {hora_txt}. Ahora {afinidad_txt}.').format(hora_txt=(self.hora_txt()), afinidad_txt=(self.afinidad_txt(r)))))
        self.app.abrir(Dialogo(self.app, lineas, lambda: (self.peticion_cumplida("plan"), self.celos(pid))))
        return True

    # ------------------------------------------------------------------ cada día
    def dia_convivencia(self):
        """Cada medianoche, si alguien vive contigo: se nota si has pasado por casa y si has hecho lo que te pidió."""
        j = self.j
        if not j.convive:
            return
        pers = self.persona_social(j.convive)
        if pers is None or not self.vida_sentimental():
            return
        n = pers["nombre"]
        if j.pareja != j.convive:                                # lo habéis dejado: no se queda
            self.fin_convivencia("sola")
            return
        if j.convive_casa not in j.propiedades or self.lug(j.convive_casa) is None:
            otra = next((l for l in (self.lug(i) for i in j.propiedades) if l is not None and l.tipo == "casa"), None)
            if otra is None:
                self.fin_convivencia("sola")
                return
            j.convive_casa = otra.id
            self.decir(tr('{n} se muda contigo a {nombre_lugar}.').format(n=(n), nombre_lugar=(self.nombre_lugar(otra))))
        r = self.relacion(j.convive)
        visto = j.convive_hoy.get("visto", j.convive_desde)
        if self.dia - 1 - int(visto) >= AJ("ausencia_dias"):
            r["afinidad"] = max(0, r["afinidad"] - 2)
            if (self.dia - 1 - int(visto)) % max(1, AJ.entero("ausencia_dias")) == 0:
                self.decir(AJ.frase("frases_ausencia", n=n))
        else:
            r["ultimo"] = self.dia                               # vivís juntos: os veis sin tener que quedar
            j.animo = min(100.0, j.animo + 2)
        pet = j.peticion_pareja
        if pet and pet.get("que") == "mueble":
            from . import sistemas
            casa = self.casa_comun()
            if casa is not None and len(sistemas.muebles_de(j, casa)) > int(pet.get("muebles", 0)):
                self.peticion_cumplida("mueble")
                pet = None
        compra = self.compra_de_pareja()
        if compra:
            self.decir(compra)
        if pet and self.dia > int(pet.get("hasta", self.dia)):
            j.peticion_pareja = None
            r["afinidad"] = max(0, r["afinidad"] - AJ.entero("peticion_castigo"))
            self.son("afinidad_baja", cat="interfaz", vol=0.5)
            self.decir(AJ.frase("frases_peticion_mal", n=n))

    def actualizar_convivencia(self, dt):
        pass


def opciones_casa(p, casa, Menu, Opcion):
    """Lo que añade al menú de una casa quien vive en ella contigo."""
    pers = p.conviviente()
    j = p.j
    if pers is None or casa.id != j.convive_casa:
        return []
    app = p.app
    n = pers["nombre"]
    if not p.pareja_en_casa():
        from . import encuentros
        l = p.lug(pers.get("lugar"))
        if l is not None and encuentros.presente(p, pers):
            donde = tr('{n} no está en casa ahora: anda por {v}').format(n=(n), v=(p.nombre_lugar(l)))
        else:
            donde = tr('{n} no está en casa ahora: ha salido a sus cosas').format(n=(n))
        ayuda = (tr("Vive aquí contigo, pero tiene su vida. En sus horas de trabajo está en su sitio; fuera de ellas, de noche está siempre y de día, a ratos.")
                 if encuentros.modo(p) != "apagado" else tr("Vive aquí contigo, pero tiene su vida. De noche está siempre; de día, a ratos."))
        return [Opcion(donde + (". " + p.peticion_txt() if p.peticion_txt() else ""), ayuda=ayuda)]

    def abrir():
        def decir(f):
            return lambda: (app.decir(f(), True), m.refrescar(False))

        def planear():
            menu_planes(p, pers)

        def social():
            from . import menus_adultos
            menus_adultos.vida_social(p, directo=pers["id"])

        def irse():
            def si():
                app.cerrar(mm)
                app.cerrar(m)
                app.decir(p.fin_convivencia("pedido", callar=True), True)
            mm = Menu(app, tr('¿Le pides a {n} que se vaya de casa? Le va a doler, y tardará en querer volver').format(n=(n)),
                      [Opcion(tr("No, dejarlo como está"), lambda: app.cerrar(mm)),
                       Opcion(tr("Sí, pedirle que se vaya"), si, ayuda=tr("Deja de vivir contigo. Seguís siendo pareja, pero la relación se enfría mucho y tardará en querer volver."))])
            app.abrir(mm)

        def mudarse():
            menu_mudanza(p, pers, al_terminar=lambda: app.cerrar(m))

        def dinero():
            menu_dinero(p, pers)
        ops = [Opcion(tr("Hablar un rato"), decir(p.charla_en_casa), ayuda=tr("Os acerca un poco. Una vez al día.")),
               Opcion(tr("Comer juntos"), decir(p.comer_en_casa), ayuda=tr("Cocina para los dos o, a veces, te toca a ti. Da salud y quita el hambre y la sed de la vida realista. Una vez al día.")),
               Opcion(tr("Hacer un plan juntos"), planear, ayuda=tr("Un paseo, el cine, una cena, una travesía en barco... Cada plan se cuenta con una escena distinta. Uno al día.")),
               Opcion(tr('Todo lo demás con {n}: regalos, gestos, pasar la noche').format(n=(n)), social, ayuda=tr("Abre su ficha, la misma que tienes en el móvil, en Vida social.")),
               Opcion(lambda: p.peticion_txt() or tr('{n} no te ha pedido nada estos días').format(n=(n)),
                      ayuda=tr("De vez en cuando te pide algo: una cena a domicilio, un plan, que duermas en casa, un mueble o un detalle. Si lo haces, os acerca; si lo dejas pasar, se resiente.")),
               Opcion(tr('Darle dinero a {n} para que se compre algo').format(n=(n)), dinero,
                      ayuda=tr("Le das algo de dinero, a tu elección. Os acerca más cuanto más le das, una vez al día, y al día siguiente te cuenta qué se compró.")),
               Opcion(tr("Mudaros a otra casa tuya"), mudarse, ayuda=tr("Elige otra de tus casas, de esta localidad o de otra, y os vais a vivir allí los dos.")),
               Opcion(tr("Pedirle que se vaya de casa"), irse, ayuda=tr("Deja de vivir contigo. No rompe la relación, pero la enfría mucho.")),
               Opcion(tr("Volver"), lambda: app.cerrar(m))]
        m = Menu(app, lambda: tr('{n}, en casa. {capitalize}').format(n=(n), capitalize=(p.afinidad_txt(p.relacion(pers['id'])).capitalize())), ops)
        app.abrir(m)
    return [Opcion(tr('{n} está en casa: estar con {n}').format(n=(n)), abrir, ayuda=tr("Vive aquí contigo. Hablar, comer juntos, hacer planes o pedirle que se vaya."))]


def menu_mudanza(p, pers, al_terminar=None, pedir=False):
    """Elegir casa: para pedirle a tu pareja que se venga a vivir contigo (`pedir`) o para mudaros juntos a otra."""
    from .menus import Menu, Opcion
    app = p.app
    j = p.j
    casas = [c for c in p.casas_para_vivir() if pedir or c.id != j.convive_casa]

    def elegir(c):
        def f():
            app.cerrar(m)
            if pedir:
                ok, frase = p.pedir_convivir(pers, c)
            else:
                frase = p.mudar_convivencia(c)
            app.decir(frase, True)
            if al_terminar:
                al_terminar()
        return f
    ops = []
    for c in casas:
        donde = "" if c.mapa == p.mundo.id else tr(', en {nombre}').format(nombre=(p.mapas[c.mapa].nombre)) if c.mapa in p.mapas else ""
        ops.append(Opcion(f"{p.nombre_lugar(c)}{donde}", elegir(c),
                          ayuda=tr("Se lo pides para esta casa. Dice que sí si os lleváis bastante bien y habéis tenido citas; si no, tendrás que esperar unos días para volver a pedírselo.") if pedir
                          else tr("Os vais a vivir allí los dos. A partir de ahora es en esa casa donde está.")))
    if not ops:
        ops.append(Opcion(tr("No tienes otra casa en la que vivir") if not pedir else tr("No tienes ninguna casa en la que vivir los dos"),
                          ayuda=tr("Las casas se compran en las inmobiliarias. Hace falta una casa, no un negocio.")))
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    titulo = tr('¿A qué casa le pides a {nombre} que se venga?').format(nombre=(pers['nombre'])) if pedir else tr('¿A qué casa os mudáis {nombre} y tú?').format(nombre=(pers['nombre']))
    m = Menu(app, titulo, ops)
    app.abrir(m)


def menu_dinero(p, pers, al_terminar=None):
    """Darle dinero a tu pareja: unas cantidades a elegir."""
    from .menus import Menu, Opcion
    app = p.app

    def dar(euros):
        def f():
            frase = p.dar_dinero_pareja(pers, euros)
            app.cerrar(m)
            if frase:
                app.decir(frase, True)
            if al_terminar:
                al_terminar()
        return f
    ops = [Opcion(tr('{e} euros').format(e=(e)), dar(e), ayuda=tr("Se lo das ahora, si te llega. Cuanto más, más os acerca. Una vez al día.")) for e in DINEROS]
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, lambda: tr('¿Cuánto le das a {nombre}? Tienes {dinero} euros').format(nombre=(pers['nombre']), dinero=(p.j.dinero)), ops,
             intro=tr("Cuanto más le das, más os acerca, una vez al día. Al día siguiente te cuenta qué se compró"))
    app.abrir(m)


def menu_planes(p, pers):
    from .menus import Menu, Opcion
    app = p.app
    ops = []
    for pl, motivo in p.planes_para(pers):
        if pl.get("adultos") and not p.modo_adulto():
            continue
        if motivo:
            ops.append(Opcion(f"{pl['nombre']}: {motivo}", ayuda=tr("Este plan no se puede hacer aquí. Prueba en otra localidad.")))
        else:
            ops.append(Opcion(tr('{nombre}: {int} euros, {get} horas').format(nombre=(pl['nombre']), int=(int(pl.get('precio', 0))), get=(pl.get('horas', 2))), (lambda pl=pl: p.hacer_plan(pers, pl)),
                              ayuda=tr("Se cuenta con una escena, distinta cada vez. Os acerca y te sube el ánimo. Un plan al día.")))
    ops.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
    m = Menu(app, lambda: tr('Planes con {nombre}. Tienes {dinero} euros').format(nombre=(pers['nombre']), dinero=(p.j.dinero)), ops, intro=tr("Cada plan se cuenta de una manera, y no siempre igual"))
    app.abrir(m)
