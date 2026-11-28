"""Base de respuestas de la gente de la calle, para cuando no se usa el modo IA.

El jugador escribe lo que quiera. El juego busca de qué está hablando (el tiempo, el fútbol, la familia, la
policía, el trabajo, el barrio...) y la persona contesta con una frase de la base, según su carácter, la
confianza que le tenga y la situación. Las frases se montan con piezas (una entrada, el cuerpo y una coletilla)
y cada persona recuerda lo que ya ha dicho, así que es muy difícil oír dos veces lo mismo.

Los temas están en respuestas_datos1.py y respuestas_datos2.py. Para añadir uno basta con una línea T(...).
En las frases se pueden usar: {yo} nombre de quien habla, {oficio}, {barrio}, {ciudad}, {tu} nombre del jugador,
{o} terminación de género de quien habla (cansad{o}) y {hora}.
"""
from .i18n import tr
import random
import unicodedata

CARACTERES = ("amable", "hablador", "seco", "timido", "chulo")
TEMAS = []
_POR_ID = {}


def T(ident, claves, generales, amable=(), hablador=(), seco=(), timido=(), chulo=(), poca=(), mucha=(), confianza=1, flojo=False):
    """Da de alta un tema. claves: palabras o trozos separados por |, sin tildes. poca/mucha: frases para poca o mucha confianza."""
    tema = {"id": ident, "claves": tuple(("*" if c.startswith("*") else "") + normal(c.lstrip("*")).strip() + (" " if c.endswith(" ") else "") for c in claves.split("|") if c.strip()), "r": tuple(generales), "amable": tuple(amable),
            "hablador": tuple(hablador), "seco": tuple(seco), "timido": tuple(timido), "chulo": tuple(chulo), "poca": tuple(poca), "mucha": tuple(mucha),
            "confianza": confianza, "flojo": flojo}      # flojo: tema comodín, que cede ante cualquier otro
    TEMAS.append(tema)
    _POR_ID[ident] = tema
    return tema


# Piezas que dan a cada frase el aire del carácter de quien habla. La cadena vacía cuenta: muchas veces no se pone nada.
ENTRADAS = {
    "amable": ("", "", "", tr("Pues mira, "), tr("Ay, "), tr("Mira, "), tr("Pues la verdad, "), tr("Hombre, "), tr("Te digo una cosa: "), tr("Si te soy sincer{o}, "), tr("Qué quieres que te diga, "), tr("Pues verás, ")),
    "hablador": ("", "", tr("Uy, "), tr("Calla, calla, "), tr("Pues mira, te cuento: "), tr("No me tires de la lengua. "), tr("¿Tú sabes lo que te digo? "), tr("Mira que te diga, "), tr("Anda que no. "),
                 tr("Fíjate lo que te voy a decir: "), tr("Pues eso mismo decía yo ayer. "), tr("Ahora que lo dices, ")),
    "seco": ("", "", "", "", "", tr("Mira, "), tr("A ver, "), tr("Pues "), tr("Bah. "), tr("En fin. ")),
    "timido": ("", "", tr("Eh... "), tr("Pues... "), tr("Bueno... "), tr("No sé... "), tr("Yo... "), tr("A ver... "), tr("Esto... "), tr("Perdona, es que... ")),
    "chulo": ("", "", tr("Mira, chaval[|a], "), tr("Te lo digo yo: "), tr("A mí me lo vas a contar. "), tr("Escucha, "), tr("Venga ya. "), tr("Eso lo sé yo de sobra. "), tr("Tú apunta: "), tr("Mira lo que te digo, ")),
}
COLETILLAS = {
    "amable": ("", "", "", tr(" ¿Y tú qué tal?"), tr(" Así es la vida."), tr(" Pero bien, ¿eh?"), tr(" Gracias por preguntar."), tr(" No nos podemos quejar."), tr(" Ya ves tú."), tr(" Qué le vamos a hacer."),
               tr(" Poquito a poco."), tr(" Y que no falte.")),
    "hablador": ("", tr(" Y no te cuento más porque no acabamos."), tr(" Que luego dicen que hablo mucho."), tr(" ¿A que sí?"), tr(" Y eso que no sabes ni la mitad."), tr(" Ya te contaré otro día con calma."),
                 tr(" Bueno, ya sabes cómo es esto."), tr(" Y así todo."), tr(" Pero vamos, que es lo que hay."), tr(" Que yo de esto podría escribir un libro."), tr(" ¿Tú qué opinas?"), tr(" Lo que yo te diga.")),
    "seco": ("", "", "", "", "", tr(" Y ya."), tr(" Punto."), tr(" Nada más."), tr(" Es lo que hay."), tr(" Pues eso.")),
    "timido": ("", "", "", tr(" Creo."), tr(" O eso me parece."), tr(" No sé si me explico."), tr(" Perdona."), tr(" Bueno, tú sabrás más."), tr(" Digo yo."), tr(" Si no te importa.")),
    "chulo": ("", "", tr(" Y el que diga otra cosa, miente."), tr(" Como te lo cuento."), tr(" Para que te enteres."), tr(" Y a mucha honra."), tr(" Que aquí me conoce todo el mundo."), tr(" Apréndetelo."),
              tr(" Yo no hablo por hablar."), tr(" Tú hazme caso.")),
}
# Cuando el jugador vuelve sobre lo mismo
REPETIDO = (tr("Ya te lo he dicho antes, pero bueno. "), tr("¿Otra vez con eso? "), tr("Como te decía, "), tr("Sigues con lo mismo, ¿eh? "), tr("Te lo repito: "), tr("Lo mismo que antes: "), tr("Y dale. "))
# Lo que dice quien no se fía de ti, a cualquier pregunta
DESCONFIANZA = (tr("No sé por qué te lo iba a contar a ti."), tr("Eso no es asunto tuyo."), tr("Prefiero no hablar de eso contigo."), tr("Mira, mejor lo dejamos."), tr("¿Y a ti qué más te da?"),
                tr("No te conozco tanto como para eso."), tr("Pregúntale a otro."), tr("Tengo prisa."), tr("Yo no sé nada."), tr("Déjame en paz, anda."))
# Cuando no se reconoce de qué habla: una pregunta
NO_SE_PREGUNTA = {
    "": (tr("Pues no sabría decirte."), tr("Ni idea, la verdad."), tr("Eso habría que preguntárselo a otro."), tr("No lo sé. De eso no entiendo."), tr("Buena pregunta. No tengo ni idea."), tr("A saber."),
         tr("Eso depende de a quién le preguntes."), tr("No me lo había planteado nunca."), tr("Pues ahora que lo dices, no lo sé."), tr("Vete tú a saber."), tr("No te lo sé decir seguro."),
         tr("Eso pregúntalo en {barrio}, que allí lo saben todo."), tr("Yo de eso sé lo justo."), tr("No me hagas mucho caso, pero creo que no."), tr("Yo diría que sí, pero no pongo la mano en el fuego."),
         tr("Quién sabe."), tr("Eso mismo me pregunto yo."), tr("Uf, me pillas fuera de juego."), tr("No sabría ni por dónde empezar."), tr("Pregunta en el bar, que allí se enteran de todo.")),
    "amable": (tr("Ojalá pudiera ayudarte, pero no lo sé."), tr("Lo siento, de eso no sé nada. Pregunta a ver si alguien te dice."), tr("Ay, pues no te sé decir. Perdona."), tr("No lo sé, pero si me entero te lo digo.")),
    "hablador": (tr("No lo sé, pero conozco a uno que seguro que sí. Bueno, lo conocía."), tr("De eso no sé, y mira que yo sé de casi todo."), tr("Pues no, y eso que le he dado vueltas. A otras cosas, pero vueltas."),
                 tr("Ni idea, pero te puedo contar otra cosa si quieres.")),
    "seco": (tr("No sé."), tr("Ni idea."), tr("No."), tr("A mí no me preguntes."), tr("Sabe Dios.")),
    "timido": (tr("No... no lo sé. Perdona."), tr("Yo de eso no sé nada, lo siento."), tr("Creo que no lo sé."), tr("Mejor pregúntale a otra persona.")),
    "chulo": (tr("Si lo supiera no te lo iba a decir gratis."), tr("Eso no lo sabe ni el alcalde."), tr("Yo sé muchas cosas, pero esa no."), tr("¿Me has visto cara de oficina de información?")),
}
# Cuando no se reconoce de qué habla: un comentario
NO_SE_COMENTARIO = {
    "": (tr("Ya, ya."), tr("Puede ser."), tr("Si tú lo dices."), tr("Mira qué bien."), tr("Eso dicen."), tr("Pues vaya."), tr("No te digo que no."), tr("Cada uno lo ve a su manera."), tr("Qué cosas."), tr("Ajá."),
         tr("Vaya por Dios."), tr("Pues mira, no lo había pensado así."), tr("Tú sabrás."), tr("Eso es verdad."), tr("Ya ves."), tr("Hombre, visto así."), tr("Algo de eso he oído."), tr("No me extraña nada."),
         tr("Pues qué bien, ¿no?"), tr("Así están las cosas."), tr("Será eso."), tr("Lo que tú digas."), tr("Me lo creo."), tr("Pues anda que no."), tr("Menuda historia.")),
    "amable": (tr("Qué interesante lo que cuentas."), tr("Me alegro por ti, de verdad."), tr("Pues mira, eso está muy bien."), tr("Qué bien que me lo cuentes.")),
    "hablador": (tr("Eso mismo le decía yo a mi vecina el otro día, que no me dejó ni terminar."), tr("Uy, de eso tengo yo una historia, pero es larga."), tr("Pues igualito que lo que me pasó a mí. Bueno, parecido."),
                 tr("¡No me digas! Sigue, sigue.")),
    "seco": (tr("Ya."), tr("Bueno."), tr("Vale."), tr("Ah."), tr("Si tú lo dices.")),
    "timido": (tr("Ah... vale."), tr("Sí, supongo."), tr("Claro, claro."), tr("No sabía.")),
    "chulo": (tr("Eso ya lo sabía yo."), tr("Me lo vas a contar a mí."), tr("Bah, eso no es nada."), tr("Qué me vas a contar.")),
}


def normal(texto):
    """Minúsculas y sin tildes, con un espacio delante y detrás, para buscar palabras."""
    t = unicodedata.normalize("NFD", ((texto or "").lower().replace("ł", "l") if _pl() else (texto or "").lower()))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")          # sin tildes; la ñ queda como n
    t = " " + " ".join("".join(c if c.isalnum() else " " for c in t).split()) + " "
    return t.replace(" del ", " de el ").replace(" al ", " a el ")          # así «del alcalde» casa con «el alcalde»


def tema_de(texto):
    """El tema del que habla el jugador, o None. Gana el que más y más largas palabras clave acierte."""
    _cargar()
    t = normal(texto)
    for relleno in (tr(" muy "), tr(" tan "), tr(" bastante "), tr(" un poco "), tr(" super "), tr(" realmente "), tr(" de verdad "), tr(" oye "), tr(" pues ")):
        t = t.replace(relleno, " ")                 # «estoy muy triste» es «estoy triste»
    mejor, nota = None, 0
    for tema in TEMAS:
        n = 0
        for clave in tema["claves"]:
            if (" " + clave if not clave.startswith("*") else clave[1:]) in t:
                n += len(clave)
        if tema["flojo"]:
            n *= 0.4
        if n > nota:
            mejor, nota = tema, n
    return mejor


def _cargar():
    if not TEMAS:
        from . import respuestas_datos1, respuestas_datos2      # noqa: F401  (al importarse dan de alta sus temas)


def cuantas():
    """Cuántos temas y cuántas frases distintas hay en la base, sin contar las combinaciones."""
    _cargar()
    frases = sum(len(t["r"]) + sum(len(t[c]) for c in CARACTERES) + len(t["poca"]) + len(t["mucha"]) for t in TEMAS)
    frases += sum(len(v) for v in NO_SE_PREGUNTA.values()) + sum(len(v) for v in NO_SE_COMENTARIO.values()) + len(DESCONFIANZA)
    return len(TEMAS), frases


PROPIOS = (tr("Belmonte"), tr("Bravo"), tr("Dios"), tr("Capitán"), "{yo}", "{barrio}", "{ciudad}", "{hora}")


def _unir(entrada, frase):
    """Pone una entrada delante de una frase, con la mayúscula donde toca."""
    if not entrada:
        return frase
    if entrada.rstrip().endswith((".", "?", "!")) or frase.startswith(("¿", "¡") + PROPIOS):
        return entrada + frase
    return entrada + frase[0].lower() + frase[1:]


def _elegir(opciones, dichas, rng):
    """Una frase que esta persona no haya dicho hace poco."""
    nuevas = [o for o in opciones if o not in dichas]
    return rng.choice(nuevas or list(opciones))


def _poner_datos(frase, ficha, ctx):
    datos = {"yo": ficha.get("nombre", ""), "oficio": ficha.get("oficio", ""), "o": "a" if ficha.get("genero") == "m" else ("y" if _pl() else "o"),
             "barrio": ctx.get("barrio", tr("el barrio")), "ciudad": ctx.get("ciudad", tr("la ciudad")), "hora": ctx.get("hora", ""), "tu": ctx.get("tu", "")}
    for k, v in datos.items():
        frase = frase.replace("{" + k + "}", v)
    return frase[0].upper() + frase[1:]


def suelta(ficha, ctx, temas=None, rng=random):
    """Una frase suelta de una persona sin que nadie le pregunte: lo que se le oye a alguien que pasa hablando con otro.
    «temas» son los temas que valen para eso; vacío, cualquiera de los que no piden confianza."""
    _cargar()
    from . import gente
    caracter = gente.habla_de(ficha.get("caracter", "amable"))
    cand = [t for t in TEMAS if t["id"] in temas] if temas else []
    tema = rng.choice(cand or [t for t in TEMAS if t["confianza"] == 1 and not t["flojo"]] or TEMAS)
    ops = [f for f in list(tema["r"]) + list(tema[caracter]) * 2 if "{tu}" not in f and "{yo}" not in f and "[" not in f]      # nada que vaya dirigido a ti
    cuerpo = rng.choice(ops or list(tema["r"]))
    if len(cuerpo) < 110:
        cuerpo = _unir(rng.choice([e for e in ENTRADAS[caracter] if "[" not in e]), cuerpo)
    return _poner_datos(cuerpo, ficha, ctx)


def comentario(ficha, rng=random):
    """Lo que contesta quien va al lado: un comentario corto, con el aire de su carácter."""
    from . import gente
    caracter = gente.habla_de(ficha.get("caracter", "amable"))
    return _poner_datos(rng.choice(NO_SE_COMENTARIO[""] + NO_SE_COMENTARIO[caracter] * 2), ficha, {})


def responder(texto, ficha, ctx, rng=random):
    """Lo que contesta la persona a un texto libre. Devuelve (frase, cambio de confianza, id del tema o None).

    ctx: diccionario con barrio, ciudad, hora y tu (nombre del jugador).
    """
    _cargar()
    from . import gente
    caracter = gente.habla_de(ficha.get("caracter", "amable"))       # un carácter de un mod habla con las frases de uno de los de serie
    conf = ficha.get("confianza", 0)
    dichas = ficha.setdefault("dichas", [])
    tema = tema_de(texto)
    repetido = ""
    if tema is None:
        tabla = NO_SE_PREGUNTA if "?" in (texto or "") or normal(texto).split()[:1] in (["que"], ["como"], ["cuando"], ["donde"], ["quien"], ["por"], ["cual"], ["cuanto"]) or _pl() and normal(texto).split()[:1] in (["co"], ["jak"], ["kiedy"], ["gdzie"], ["kto"], ["dlaczego"], ["czemu"], ["ile"], ["ktory"], ["ktora"], ["czy"], ["skad"], ["dokad"], ["jaki"], ["jaka"]) else NO_SE_COMENTARIO
        cuerpo = _elegir(tabla[""] + tabla[caracter] * 3, dichas, rng)
        cambio, ident = 0, None
    else:
        ident = tema["id"]
        if ficha.get("ultimo_tema") == ident and rng.random() < 0.5:
            repetido = rng.choice(REPETIDO)
        if conf < -10 and tema["confianza"] >= 0 and rng.random() < 0.6:
            cuerpo = _elegir(tema["poca"] or DESCONFIANZA, dichas, rng)
        else:
            opciones = list(tema["r"]) + list(tema[caracter]) * 3            # las de su carácter salen más
            if conf >= 30:
                opciones += list(tema["mucha"]) * 3
            cuerpo = _elegir(opciones, dichas, rng)
        cambio = tema["confianza"]
    ficha["ultimo_tema"] = ident
    dichas.append(cuerpo)
    del dichas[:-40]
    frase = cuerpo
    if len(cuerpo) < 120 and not repetido:
        frase = _unir(rng.choice(ENTRADAS[caracter]), frase)
    if tema is not None and len(frase) < 140 and not cuerpo.endswith("?") and rng.random() < 0.45:
        frase += rng.choice(COLETILLAS[caracter])
    frase = _unir(repetido, frase)
    datos = {"yo": ficha.get("nombre", ""), "oficio": ficha.get("oficio", ""), "o": "a" if ficha.get("genero") == "m" else ("y" if _pl() else "o"),
             "barrio": ctx.get("barrio", tr("el barrio")), "ciudad": ctx.get("ciudad", tr("la ciudad")), "hora": ctx.get("hora", ""), "tu": ctx.get("tu", "")}
    for k, v in datos.items():
        frase = frase.replace("{" + k + "}", v)
    return frase[0].upper() + frase[1:], cambio, ident


def _pl():
    """Łatka działa tylko przy języku polskim: po hiszpańsku i angielsku gra zostaje jak u autora."""
    try:
        from .i18n import actual
        return actual() == "pl"
    except Exception:  # noqa: BLE001
        return False
