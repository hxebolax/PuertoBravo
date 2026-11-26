"""La mochila (1.7.2): lo que llevas encima, con sitio limitado, y el armario de tus casas.

- Objetos de valor: un móvil, un reloj, una cadena de oro, un portátil... Salen al atracar a un peatón, en la guantera de
  un coche que fuerzas, del bolsillo de algunos caídos y del fondo del mar. Los robados se distinguen de los encontrados.
  Cada uno ocupa unos huecos de la mochila. Se venden en las casas de empeños: lo robado, bastante más barato.
- La mercancía (las sustancias, con el contenido para adultos) va también en la mochila: cada diez unidades, un hueco,
  además del tope de cien unidades de siempre.
- El armario de cada casa tuya guarda objetos, mercancía y armas, sin límite práctico. Lo que está en casa no te lo
  quita la policía, ni se pierde si te tumban.
- Si te detienen, la policía se queda con lo robado y con la mercancía. Si llevas algo así encima, el agente que te para
  te cachea: no vale pagar la multa en el acto.
- En una tienda de ropa se vende una mochila más grande.

Los números, las frases y el catálogo de objetos están en los datos (vida.json, secciones mochila y objetos_valor).
"""
from .i18n import tr
import random

from .ajustes import Ajustes

AJ = Ajustes("mochila", {
    "capacidad": 20, "capacidad_grande": 40, "mochila_grande_precio": 120, "unidades_por_hueco": 10,
    "encontrado_pct": 80, "robado_pct": 35, "atraco_prob": 45, "guantera_prob": 30, "caido_prob": 12, "buceo_prob": 30,
}, {
    "frases_llena": [tr("No te cabe en la mochila: {objeto}. Deja algo en casa o véndelo."), tr("La mochila va llena: {objeto} se queda donde estaba.")],
    "frases_guantera": [tr("En la guantera hay {objeto}. Te lo guardas."), tr("Rebuscando en el coche encuentras {objeto}. A la mochila.")],
    "frases_atraco": [tr("Además de la cartera, te quedas con {objeto}."), tr("Le quitas también {objeto}.")],
    "frases_cacheo": [tr("El agente te cachea y encuentra {que}. Con eso encima no hay multa que valga."),
                      tr("Te registran los bolsillos y la mochila: {que}. Esto ya no se arregla con una multa.")],
}, cero=("atraco_prob", "guantera_prob", "caido_prob", "buceo_prob"))

_SERIE = [
    {"id": "movil", "nombre": tr("un teléfono móvil"), "peso": 1, "valor": 120, "donde": ["atraco", "guantera", "caido"]},
    {"id": "reloj", "nombre": tr("un reloj de pulsera"), "peso": 1, "valor": 150, "donde": ["atraco", "buceo", "caido"]},
    {"id": "cadena", "nombre": tr("una cadena de oro"), "peso": 1, "valor": 220, "donde": ["atraco", "caido"]},
    {"id": "anillo", "nombre": tr("un anillo"), "peso": 1, "valor": 180, "donde": ["atraco", "buceo"]},
    {"id": "auriculares", "nombre": tr("unos auriculares inalámbricos"), "peso": 1, "valor": 70, "donde": ["atraco", "guantera"]},
    {"id": "gafas", "nombre": tr("unas gafas de sol de marca"), "peso": 1, "valor": 60, "donde": ["guantera"]},
    {"id": "perfume", "nombre": tr("un frasco de perfume caro"), "peso": 1, "valor": 50, "donde": ["guantera"]},
    {"id": "tableta", "nombre": tr("una tableta"), "peso": 2, "valor": 220, "donde": ["guantera", "atraco"]},
    {"id": "camara", "nombre": tr("una cámara de fotos"), "peso": 2, "valor": 260, "donde": ["guantera"]},
    {"id": "portatil", "nombre": tr("un ordenador portátil"), "peso": 4, "valor": 400, "donde": ["guantera"]},
    {"id": "herramientas", "nombre": tr("una caja de herramientas"), "peso": 5, "valor": 90, "donde": ["guantera"]},
    {"id": "monedas", "nombre": tr("unas monedas antiguas"), "peso": 1, "valor": 60, "donde": ["buceo"]},
    {"id": "doblon", "nombre": tr("un doblón de oro"), "peso": 1, "valor": 250, "donde": ["buceo"]},
    {"id": "aparejos", "nombre": tr("una caja de aparejos de pesca"), "peso": 3, "valor": 35, "donde": ["buceo"]},
    {"id": "cartera_piel", "nombre": tr("una cartera de piel"), "peso": 1, "valor": 45, "donde": ["atraco", "caido"]},
    {"id": "gafas_vista", "nombre": tr("unas gafas graduadas"), "peso": 1, "valor": 90, "donde": ["atraco", "guantera"]},
    {"id": "pluma", "nombre": tr("una pluma estilográfica"), "peso": 1, "valor": 130, "donde": ["guantera", "atraco"]},
    {"id": "mechero", "nombre": tr("un mechero de plata"), "peso": 1, "valor": 80, "donde": ["atraco", "caido"]},
    {"id": "colgante", "nombre": tr("un colgante de oro"), "peso": 1, "valor": 260, "donde": ["atraco", "caido"]},
    {"id": "pulsera", "nombre": tr("una pulsera de plata"), "peso": 1, "valor": 110, "donde": ["atraco"]},
    {"id": "gemelos", "nombre": tr("unos gemelos de oro"), "peso": 1, "valor": 300, "donde": ["caido"]},
    {"id": "consola", "nombre": tr("una consola portátil"), "peso": 2, "valor": 210, "donde": ["guantera", "atraco"]},
    {"id": "altavoz", "nombre": tr("un altavoz portátil"), "peso": 2, "valor": 70, "donde": ["guantera"]},
    {"id": "camara_deportiva", "nombre": tr("una cámara deportiva"), "peso": 1, "valor": 180, "donde": ["guantera"]},
    {"id": "dron", "nombre": tr("un dron pequeño"), "peso": 3, "valor": 350, "donde": ["guantera"]},
    {"id": "libro_firmado", "nombre": tr("un libro firmado por su autor"), "peso": 1, "valor": 90, "donde": ["guantera"]},
    {"id": "joyero", "nombre": tr("un joyero"), "peso": 2, "valor": 350, "donde": ["caido"]},
    {"id": "botella_antigua", "nombre": tr("una botella antigua"), "peso": 1, "valor": 70, "donde": ["buceo"]},
    {"id": "brujula", "nombre": tr("una brújula de latón"), "peso": 1, "valor": 140, "donde": ["buceo"]},
    {"id": "ancla_bronce", "nombre": tr("un ancla pequeña de bronce"), "peso": 4, "valor": 200, "donde": ["buceo"]},
]
CATALOGO = {o["id"]: dict(o) for o in _SERIE}
ORIGENES = ("atraco", "guantera", "caido", "buceo")


def configurar(datos):
    """El catálogo sale de los datos (vida.json, objetos_valor), que un mod puede cambiar o ampliar."""
    lista = [o for o in datos.get("objetos_valor", []) if isinstance(o, dict) and o.get("id") and o.get("nombre")]
    CATALOGO.clear()
    for o in (lista or _SERIE):
        try:
            CATALOGO[str(o["id"])] = {"id": str(o["id"]), "nombre": str(o["nombre"]), "peso": max(1, int(o.get("peso", 1))),
                                      "valor": max(0, int(o.get("valor", 0))), "donde": [str(x) for x in (o.get("donde") or []) if str(x) in ORIGENES]}
        except (TypeError, ValueError):
            continue
    if not CATALOGO:
        CATALOGO.update({o["id"]: dict(o) for o in _SERIE})


def de(origen):
    """Uno al azar de los que pueden salir de ese sitio, o None."""
    lista = [o for o in CATALOGO.values() if origen in o["donde"]]
    return random.choice(lista) if lista else None


def _nombre_corto(o):
    return o["nombre"]


class Mochila:
    """Mixin de Partida."""

    # ------------------------------------------------------------------ sitio
    def moc_capacidad(self):
        base = AJ.entero("capacidad_grande") if getattr(self.j, "mochila_grande", False) else AJ.entero("capacidad")
        if self.cheat_on("cheat_mochila"):
            headroom = max(1, max((o["peso"] for o in CATALOGO.values()), default=1))
            return max(base, self.moc_usado() + headroom)
        return base

    def moc_huecos_mercancia(self):
        carga = self.carga()
        por = max(1, AJ.entero("unidades_por_hueco"))
        return (carga + por - 1) // por if carga > 0 else 0

    def moc_usado(self):
        return sum(CATALOGO.get(x["id"], {"peso": 1})["peso"] for x in self.j.mochila) + self.moc_huecos_mercancia()

    def moc_libre(self):
        return max(0, self.moc_capacidad() - self.moc_usado())

    def hueco_mercancia(self, cantidad=None):
        """Sitio para la tanda; normalmente limitado a cien unidades y los huecos de la mochila."""
        if self.cheat_on("cheat_mochila"):
            # Give this batch finite headroom without inventing inventory or saving infinity.
            return max(100, int(cantidad or 0))
        por = max(1, AJ.entero("unidades_por_hueco"))
        sobra = self.moc_huecos_mercancia() * por - self.carga()           # lo que queda del último hueco empezado
        return max(0, min(100 - self.carga(), self.moc_libre() * por + sobra))

    def moc_txt(self):
        if self.cheat_on("cheat_mochila"):
            from .cheats import text
            return text("Mochila sin límite de huecos; ocupados: ", "Unlimited backpack slots; occupied: ") + str(self.moc_usado())
        return tr('Mochila: {moc_usado} de {moc_capacidad} huecos ocupados').format(moc_usado=(self.moc_usado()), moc_capacidad=(self.moc_capacidad()))

    # ------------------------------------------------------------------ meter y sacar
    def moc_meter(self, ident, robado=False, callar=False):
        o = CATALOGO.get(ident)
        if o is None:
            return False
        if self.moc_libre() < o["peso"]:
            if not callar:
                self.son("error", cat="interfaz")
                self.decir(AJ.frase("frases_llena", objeto=o["nombre"]))
            return False
        self.j.mochila.append({"id": ident, "robado": bool(robado)})
        return True

    def moc_soltar(self, x, y, ident, robado):
        """Un objeto de valor queda en el suelo, para recogerlo."""
        from .entidades import Objeto
        o = CATALOGO.get(ident)
        if o is None:
            return None
        ob = Objeto("valor", o["nombre"][:1].upper() + o["nombre"][1:], *self.mundo.punto_libre(x, y))
        ob.item, ob.robado, ob.valor = ident, bool(robado), o["valor"]
        self.objetos.append(ob)
        return ob

    def moc_recoger(self, ob):
        """Recoges del suelo un objeto de valor. Si no cabe, se queda donde estaba."""
        if not self.moc_meter(ob.item, getattr(ob, "robado", False)):
            ob.recogido = False
            self.objetos.append(ob)
            return False
        self.son("recoger", cat="interfaz")
        robado = tr(" Es robado: en una casa de empeños dan menos por él, y si te detienen, te lo quitan.") if getattr(ob, "robado", False) else ""
        self.decir(tr('A la mochila: {nombre}. {moc_txt}.').format(nombre=(CATALOGO[ob.item]['nombre']), moc_txt=(self.moc_txt())) + robado)
        return True

    # ------------------------------------------------------------------ de dónde salen
    def moc_botin(self, origen, x=None, y=None):
        """A veces sale un objeto: al atracar a alguien, en la guantera, del bolsillo de un caído o del fondo del mar.
        Devuelve el objeto del catálogo, o None."""
        if getattr(self, "en_servidor", False) and origen == "caido":
            return None
        prob = {"atraco": "atraco_prob", "guantera": "guantera_prob", "caido": "caido_prob", "buceo": "buceo_prob"}[origen]
        if random.random() * 100 >= AJ(prob):
            return None
        o = de(origen)
        if o is None:
            return None
        robado = origen != "buceo"
        if origen == "caido":
            self.moc_soltar(x, y, o["id"], robado)
            return o
        if not self.moc_meter(o["id"], robado):
            return None
        if origen == "guantera":
            self.decir(AJ.frase("frases_guantera", objeto=o["nombre"]))
        elif origen == "atraco":
            self.decir(AJ.frase("frases_atraco", objeto=o["nombre"]))
        return o

    # ------------------------------------------------------------------ precios y policía
    def moc_precio(self, x, l=None):
        o = CATALOGO.get(x["id"], {"valor": 0})
        pct = AJ("robado_pct") if x.get("robado") else AJ("encontrado_pct")
        mult = self.mercado("empenos", l.id if l is not None else "") if l is not None else 1.0
        return max(1, int(o["valor"] * pct / 100.0 * mult))

    def moc_robados(self):
        return [x for x in self.j.mochila if x.get("robado")]

    def moc_comprometido(self):
        """Lo que un agente encuentra si te cachea: texto, o cadena vacía si no llevas nada que te comprometa."""
        partes = []
        if self.carga() > 0:
            partes.append(tr('{carga} unidades de mercancía').format(carga=(self.carga())))
        n = len(self.moc_robados())
        if n:
            partes.append(tr("un objeto robado") if n == 1 else tr('{n} objetos robados').format(n=(n)))
        return tr(" y ").join(partes)

    def moc_requisar(self):
        """La policía se queda con lo robado. Devuelve cuántos objetos."""
        n = len(self.moc_robados())
        self.j.mochila = [x for x in self.j.mochila if not x.get("robado")]
        return n

    # ------------------------------------------------------------------ el armario de casa
    def almacen(self, casa):
        a = self.j.almacen.setdefault(casa, {})
        a.setdefault("objetos", [])
        a.setdefault("sust", {})
        a.setdefault("armas", {})
        a.setdefault("dinero", 0)
        return a

    def limpiar_almacenes(self):
        """Las casas que ya no son tuyas se llevan lo que había en el armario."""
        for cid in [c for c in self.j.almacen if c not in self.j.propiedades]:
            del self.j.almacen[cid]

    def almacen_txt(self, casa):
        a = self.almacen(casa)
        sust = sum(a["sust"].values())
        partes = [f"{len(a['objetos'])} {'objeto' if len(a['objetos']) == 1 else 'objetos'}"]
        if sust:
            partes.append(tr('{sust} unidades de mercancía').format(sust=(sust)))
        if a["armas"]:
            partes.append(f"{len(a['armas'])} {'arma' if len(a['armas']) == 1 else 'armas'}")
        if int(a.get("dinero", 0)):
            partes.append(tr('{int} euros').format(int=(int(a['dinero']))))
        return ", ".join(partes)


# ====================================================================== menús
def menu_mochila(p, l=None):
    """Lo que llevas en la mochila. Con `l` (una casa tuya), cada objeto se puede dejar en el armario."""
    from .menus import Menu, Opcion
    app, j = p.app, p.j

    def tirar(k):
        def f():
            x = j.mochila.pop(k)
            px, py = p.pos()
            ob = p.moc_soltar(px + 1.0, py, x["id"], x.get("robado"))
            if ob is not None:
                ob.no_auto = True                                # lo has dejado tú: se recoge con Intro, no al pasar
            app.son("menu_ok")
            app.decir(tr('Dejas en el suelo {nombre}.').format(nombre=(CATALOGO[x['id']]['nombre'])), True)
            m.refrescar(False)
        return f

    def guardar(k):
        def f():
            x = j.mochila.pop(k)
            p.almacen(l.id)["objetos"].append(x)
            app.son("menu_ok")
            app.decir(tr('Guardas en el armario {nombre}.').format(nombre=(CATALOGO[x['id']]['nombre'])), True)
            m.refrescar(False)
        return f

    def ops():
        lista = [Opcion(p.moc_txt(), ayuda=tr("Cada objeto ocupa unos huecos; la mercancía, uno por cada diez unidades. En las tiendas de ropa venden una mochila más grande. "
                                          "Lo que no quieras llevar, déjalo en el armario de una de tus casas o véndelo en una casa de empeños."))]
        for k, x in enumerate(j.mochila):
            o = CATALOGO.get(x["id"])
            if o is None:
                continue
            t = f"{o['nombre'][:1].upper() + o['nombre'][1:]}, {'robado' if x.get('robado') else 'encontrado'}, {o['peso']} {'hueco' if o['peso'] == 1 else 'huecos'}"
            if l is not None:
                lista.append(Opcion(t + tr(". Intro lo guarda en el armario"), guardar(k),
                                    ayuda=tr("Lo dejas en el armario de esta casa y te quedan libres sus huecos. Lo sacas cuando quieras desde el mismo armario.")))
            else:
                lista.append(Opcion(t + tr(". Intro lo deja en el suelo"), tirar(k),
                                    ayuda=tr("Lo sueltas a tu lado y te quedan libres sus huecos. Si lo quieres otra vez, ponte junto a él y pulsa Intro.")))
        if p.carga() > 0:
            lista.append(Opcion(tr('Mercancía: {carga} unidades, {moc_huecos_mercancia} huecos').format(carga=(p.carga()), moc_huecos_mercancia=(p.moc_huecos_mercancia())),
                                ayuda=tr("Las sustancias que llevas: cada diez unidades ocupan un hueco. Se guardan en el armario de una casa tuya.")))
        if len(lista) == 1 and not j.mochila:
            lista.append(Opcion(tr("La mochila está vacía"), ayuda=tr("Lo que encuentres o robes por ahí va a la mochila, si te cabe.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
        return lista
    m = Menu(app, tr("Mochila"), ops)
    app.abrir(m)


def menu_armario(p, l):
    """El armario de una casa tuya: guardar y sacar objetos, mercancía y armas."""
    from .menus import Menu, Opcion
    app, j = p.app, p.j

    def sacar(k):
        def f():
            a = p.almacen(l.id)
            x = a["objetos"][k]
            if not p.moc_meter(x["id"], x.get("robado")):
                return
            a["objetos"].pop(k)
            app.son("menu_ok")
            app.decir(tr('Sacas del armario {nombre}. {moc_txt}.').format(nombre=(CATALOGO[x['id']]['nombre']), moc_txt=(p.moc_txt())), True)
            m.refrescar(False)
        return f

    def guardar_mercancia():
        a = p.almacen(l.id)
        n = 0
        for s, c in list(j.sustancias.items()):
            if s != "alcohol" and c > 0:
                a["sust"][s] = a["sust"].get(s, 0) + c
                n += c
                j.sustancias[s] = 0
        app.son("menu_ok")
        app.decir(tr('Guardas en el armario {n} unidades de mercancía.').format(n=(n)), True)
        m.refrescar(False)

    def sacar_mercancia():
        a = p.almacen(l.id)
        n = 0
        for s, c in list(a["sust"].items()):
            cabe = min(c, p.hueco_mercancia(c))
            if cabe <= 0:
                break
            j.sustancias[s] = j.sustancias.get(s, 0) + cabe
            a["sust"][s] = c - cabe
            n += cabe
        a["sust"] = {s: c for s, c in a["sust"].items() if c > 0}
        if not n:
            app.son("error")
            app.decir(tr("No te cabe más mercancía en la mochila."), True)
            return
        app.son("menu_ok")
        app.decir(tr('Sacas {n} unidades de mercancía.').format(n=(n)) + (tr(" No te cabe el resto.") if a["sust"] else ""), True)
        m.refrescar(False)

    def mover_dinero(cant, guardar):
        a = p.almacen(l.id)
        tengo = j.dinero if guardar else int(a.get("dinero", 0))
        n = tengo if cant is None else min(cant, tengo)
        if n <= 0:
            app.son("error")
            app.decir(tr("No hay dinero que mover."), True)
            return
        if guardar:
            j.dinero -= n
            a["dinero"] = int(a.get("dinero", 0)) + n
        else:
            j.dinero += n
            a["dinero"] = int(a.get("dinero", 0)) - n
        app.son("caja")
        app.decir(tr('{v} {n} euros. En el armario hay {int} y llevas encima {dinero}.').format(v=(tr('Guardas') if guardar else tr('Sacas')), n=(n), int=(int(a['dinero'])), dinero=(j.dinero)), True)
        m.refrescar(False)

    def guardar_arma(ident):
        def f():
            weapons = p.almacen(l.id)["armas"]
            carried = j.armas.pop(ident)
            stored = weapons.get(ident)
            if stored is not None:
                carried["reserva"] += int(stored.get("cargador", 0)) + int(stored.get("reserva", 0))
                for upgrade in ("ampliado", "silenciador"):
                    if stored.get(upgrade):
                        carried[upgrade] = True
            weapons[ident] = carried
            if j.arma == ident:
                j.arma = "punos"
            app.son("menu_ok")
            app.decir(tr('Guardas en el armario {nombre}.').format(nombre=(p.armas_d[ident]['nombre'])), True)
            m.refrescar(False)
        return f

    def sacar_arma(ident):
        def f():
            a = p.almacen(l.id)["armas"]
            m_ = a[ident]
            if ident in j.armas:                                 # ya llevas una igual: te quedas con las balas
                total = int(m_.get("cargador", 0)) + int(m_.get("reserva", 0))
                remaining = total - p.sumar_municion(ident, total)
                if remaining:
                    loaded = min(int(m_.get("cargador", 0)), remaining)
                    m_["cargador"], m_["reserva"] = loaded, remaining - loaded
                else:
                    a.pop(ident)
            else:
                j.armas[ident] = a.pop(ident)
            app.son("menu_ok")
            if ident in a:
                from .cheats import text
                app.decir(text("La munición que supera la carga máxima se queda en el armario.",
                               "Ammunition beyond the maximum loadout stays in storage."), True)
            else:
                app.decir(tr('Sacas del armario {nombre}.').format(nombre=(p.armas_d[ident]['nombre'])), True)
            m.refrescar(False)
        return f

    def ops():
        a = p.almacen(l.id)
        lista = [Opcion(tr('En el armario: {almacen_txt}. {moc_txt}').format(almacen_txt=(p.almacen_txt(l.id)), moc_txt=(p.moc_txt())),
                        ayuda=tr("Lo que está en el armario de casa no te lo quita la policía ni se pierde si te tumban. Guarda aquí lo que no quieras llevar encima."))]
        lista.append(Opcion(tr("Guardar objetos de la mochila"), lambda: menu_mochila(p, l), ayuda=tr("Abre la mochila: Intro sobre un objeto lo deja en el armario.")))
        for cant, texto in ((None, tr("Guardar todo el dinero que llevas")), (500, tr("Guardar 500 euros"))):
            lista.append(Opcion(tr('{texto}: llevas {dinero}').format(texto=(texto), dinero=(j.dinero)), (lambda c=cant: mover_dinero(c, True)),
                                ayuda=tr("El dinero de casa no lo pierdes si te atracan o te detienen, pero en una casa pueden entrar a robar, salvo lo que esté en una caja fuerte.")))
        if int(a.get("dinero", 0)):
            lista.append(Opcion(tr('Sacar el dinero del armario: hay {int} euros').format(int=(int(a['dinero']))), (lambda: mover_dinero(None, False)),
                                ayuda=tr("Te lo llevas todo encima, donde ya no está a salvo si te atracan o te detienen.")))
        for k, x in enumerate(a["objetos"]):
            o = CATALOGO.get(x["id"])
            if o is not None:
                lista.append(Opcion(tr('Sacar {nombre}, {v}').format(nombre=(o['nombre']), v=(tr('robado') if x.get('robado') else tr('encontrado'))), sacar(k),
                                    ayuda=tr("Vuelve a la mochila, si te caben sus huecos.")))
        if p.carga() > 0:
            lista.append(Opcion(tr('Guardar toda la mercancía que llevas: {carga} unidades').format(carga=(p.carga())), guardar_mercancia,
                                ayuda=tr("Dejas en el armario todas las sustancias que llevas, menos el alcohol, y te quedan libres sus huecos.")))
        if a["sust"]:
            lista.append(Opcion(tr('Sacar mercancía: hay {sum} unidades').format(sum=(sum(a['sust'].values()))), sacar_mercancia,
                                ayuda=tr("Te llevas toda la que te quepa en la mochila; lo que no quepa se queda en el armario.")))
        for ident in p.orden_armas:
            if ident in j.armas and ident != "punos":
                lista.append(Opcion(tr('Guardar {nombre}').format(nombre=(p.armas_d[ident]['nombre'])), guardar_arma(ident),
                                    ayuda=tr("La dejas en el armario con su munición. Si la llevabas en la mano, te quedas con los puños.")))
        for ident in list(a["armas"]):
            if ident in p.armas_d:
                lista.append(Opcion(tr('Sacar {nombre}').format(nombre=(p.armas_d[ident]['nombre'])), sacar_arma(ident),
                                    ayuda=tr("Vuelve a tus armas con su munición. Si ya llevas una igual, te quedas con sus balas.")))
        lista.append(Opcion(tr("Volver"), lambda: app.cerrar(m)))
        return lista
    m = Menu(app, tr('Armario de {nombre_lugar}').format(nombre_lugar=(p.nombre_lugar(l))), ops)
    app.abrir(m)


def opciones_empenos(p, l, refrescar):
    """Lo que añade la mochila al menú de una casa de empeños: vender tus objetos."""
    from .menus import Opcion
    j = p.j

    def vender(k):
        def f():
            x = j.mochila.pop(k)
            n = p.moc_precio(x, l)
            if x.get("robado"):
                p.hon_negro(n)                                    # lo robado es dinero que no puedes justificar
            p.dar_dinero(n, tr('Vendes {nombre}').format(nombre=(CATALOGO[x['id']]['nombre'])))
            refrescar()
        return f

    def todo():
        total = 0
        negro = 0
        for x in list(j.mochila):
            n = p.moc_precio(x, l)
            total += n
            negro += n if x.get("robado") else 0
        j.mochila = []
        if negro:
            p.hon_negro(negro)
        p.dar_dinero(total, tr("Vendes todo lo de la mochila"))
        refrescar()

    lista = []
    for k, x in enumerate(j.mochila):
        o = CATALOGO.get(x["id"])
        if o is not None:
            lista.append(Opcion(tr('Vender {nombre}, {v}, por {moc_precio} euros').format(nombre=(o['nombre']), v=(tr('robado') if x.get('robado') else tr('encontrado')), moc_precio=(p.moc_precio(x, l))), vender(k),
                                ayuda=tr("Por lo robado el prestamista paga mucho menos: sabe de dónde viene.")))
    if len(lista) > 1:
        lista.append(Opcion(tr('Vender todo lo de la mochila por {sum} euros').format(sum=(sum(p.moc_precio(x, l) for x in j.mochila))), todo,
                            ayuda=tr("Vendes todos los objetos de una vez y cobras al momento. Lo que saques por lo robado es dinero negro, que no puedes justificar.")))
    return lista


def opcion_mochila_grande(p, refrescar):
    """En una tienda de ropa: una mochila más grande."""
    from .menus import Opcion
    j = p.j
    if getattr(j, "mochila_grande", False):
        return []

    def comprar():
        if p.pagar(AJ.entero("mochila_grande_precio")):
            j.mochila_grande = True
            p.son("menu_ok", cat="interfaz")
            p.decir(tr('Te llevas una mochila grande: ahora caben {entero} huecos.').format(entero=(AJ.entero('capacidad_grande'))), True)
            refrescar()
    return [Opcion(tr('Comprar una mochila grande: {entero} euros').format(entero=(AJ.entero('mochila_grande_precio'))), comprar,
                   ayuda=tr('La de serie tiene {entero} huecos; esta, {entero2}. Lo que lleves pasa a la nueva.').format(entero=(AJ.entero('capacidad')), entero2=(AJ.entero('capacidad_grande'))))]
