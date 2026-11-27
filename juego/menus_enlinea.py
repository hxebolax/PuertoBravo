"""Menús para jugar en un servidor: la lista de servidores, y dentro de la partida, todo lo que se hace con los demás."""
from .i18n import tr, tr_servidor
from . import enlinea, i18n, red
from . import mundo as M
from .menus import EntradaTexto, Menu, Opcion
from .menus_online import deletrear


def _copiar(texto):
    """Copia un texto al portapapeles. Devuelve si se ha podido."""
    try:
        import pygame
        pygame.scrap.put_text(texto)
        return True
    except Exception:
        pass
    try:
        import subprocess
        subprocess.run("clip", input=texto.encode("utf-16-le"), shell=True, timeout=5, check=True)
        return True
    except Exception:
        return False


# ================================================================ antes de entrar
def servidores(app):
    cfg = app.cfg
    if not cfg["red_nombre"] and enlinea.perfil():           # en las copias de pruebas, cada instancia con su nombre
        cfg["red_nombre"] = tr("Jugador ") + enlinea.perfil()

    def entrar(s, clave="", invitacion=""):
        def f():
            app.decir(tr('Conectando con {v}.').format(v=(s.get('nombre') or tr('el servidor'))), True)
            enlace, motivo = enlinea.conectar(app, s, clave, invitacion)
            if enlace is None:
                if motivo.startswith(tr("certificado: ")):
                    return cambio_certificado(s, motivo[13:])
                crudo = i18n.original(str(motivo))                # en español, para reconocerlo en cualquier idioma
                if "contraseña" in crudo and not clave:
                    return app.abrir(EntradaTexto(app, tr("Contraseña de entrada del servidor"), lambda t: entrar(s, clave=t)(), secreto=True, maximo=60))
                if "invitación" in crudo and not invitacion:
                    return app.abrir(EntradaTexto(app, tr("Código de invitación que te ha dado quien lleva el servidor"), lambda t: entrar(s, invitacion=t)(), maximo=20))
                if getattr(motivo, "codigo", "") == "nombre":         # entra por primera vez sin nombre de jugador: se lo pide
                    app.son("error")
                    app.decir(motivo, True)
                    return pedir_nombre(lambda: entrar(s, clave, invitacion)())
                app.son("error")
                app.decir(motivo, True)
                return
            cfg.guardar()
            app.enlace = enlace
            if enlace.ok.get("partida"):
                # El personaje vive en el servidor. Si la última vez se guardó con una versión del juego más nueva que esta,
                # puede traer cosas que esta no conoce: se avisa, por si algo no va como se espera.
                from . import VERSION
                de = str(enlace.ok.get("partida_de") or "")
                if de and enlinea.version_tupla(de) > enlinea.version_tupla(VERSION):
                    app.decir(tr('Aviso: este personaje se guardó la última vez con la versión {de} del juego, más nueva que la tuya. Si notas algo raro, actualiza el juego.').format(de=(de)), True)
                app.empezar_partida(enlace.ok["partida"])
            else:
                app.decir(tr('Entras por primera vez en {get}. Elige con qué personaje vas a jugar aquí.').format(get=(s.get('nombre'))), True)
                from . import menus_vida
                menus_vida.elegir_personaje(app)
        return f

    def cambio_certificado(s, nueva):
        def aceptar():
            s["cert"] = ""
            app.cerrar(mm)
            entrar(s)()
        mm = Menu(app, tr("El servidor no presenta el mismo certificado que la otra vez"), [
            Opcion(tr("No entrar"), lambda: app.cerrar(mm), ayuda=tr("Es lo prudente si no sabes por qué ha cambiado.")),
            Opcion(tr("Quien lleva el servidor me ha dicho que lo ha cambiado: entrar y recordar el nuevo"), aceptar,
                   ayuda=tr("El certificado cambia si reinstalan el servidor. Si nadie te ha avisado, puede que alguien se esté haciendo pasar por él."))])
        app.son("error")
        app.abrir(mm)

    def anadir():
        def hecho(t):
            if red.analizar_direccion(t) is None:
                app.son("error")
                app.decir(tr("No entiendo esa dirección. Tiene que ser como puertobravo, dos puntos, barra, barra, el sitio, dos puntos y el puerto."), True)
                return
            d = t.strip()
            if not d.lower().startswith(red.PREFIJO):
                d = red.PREFIJO + d
            if ":" not in d[len(red.PREFIJO):]:
                d += f":{enlinea.PUERTO}"
            lista = list(cfg["servidores"])
            if not any(x.get("dir") == d for x in lista):
                lista.append({"nombre": tr("Servidor nuevo"), "dir": d, "cert": ""})
            cfg["servidores"] = lista
            cfg.guardar()
            app.decir(tr("Servidor añadido a tu lista. Pulsa Intro sobre él para entrar."), True)
            m.refrescar(False)
        app.abrir(EntradaTexto(app, tr("Dirección del servidor"), hecho, maximo=90,
                               ayuda=tr("Te la da quien lleva el servidor. Puedes pegarla con Control V. Si no lleva puerto, se usa el de serie.")))

    def quitar():
        def borrar(s):
            def f():
                cfg["servidores"] = [x for x in cfg["servidores"] if x is not s]
                cfg.guardar()
                app.cerrar(mq)
                app.decir(tr("Quitado de tu lista. Tu personaje sigue guardado en ese servidor."), True)
                m.refrescar(False)
            return f
        mq = Menu(app, tr("Qué servidor quitas de la lista"), [Opcion(f"{s.get('nombre')}, {deletrear(s.get('dir', ''))}", borrar(s),
                                                                     ayuda=tr("Intro lo quita de tu lista. Tu personaje sigue guardado en ese servidor y puedes volver a añadirlo."))
                                                              for s in cfg["servidores"]]
                  or [Opcion(tr("No hay ninguno"), ayuda=tr("Tu lista de servidores está vacía: no hay nada que quitar."))])
        app.abrir(mq)

    def pedir_nombre(despues=None):
        def hecho(t):
            t = " ".join(t.split())[:24]
            if len(t) < 2:
                app.son("error")
                app.decir(tr("Hace falta un nombre de al menos dos letras para entrar en un servidor."), True)
                return
            cfg["red_nombre"] = t
            cfg.guardar()
            app.decir(tr('En los servidores en los que entres por primera vez te llamarás {v}.').format(v=(t)), True)
            if despues:
                despues()
        app.abrir(EntradaTexto(app, tr("Tu nombre de jugador"), hecho, inicial=cfg["red_nombre"], maximo=24,
                               ayuda=tr("Es el nombre con el que te ven los demás, de dos a veinticuatro letras. Sin él no se entra en un servidor por primera vez. "
                                        "En un servidor donde ya tienes personaje no cambia: allí te lo cambia quien lo administra.")))

    def nombre():
        pedir_nombre()

    def identidad():
        def exportar():
            ok = _copiar(enlinea.exportar_identidad())
            app.son("menu_ok" if ok else "error")
            app.decir(tr("Tu identidad está copiada en el portapapeles. Pégala en un archivo y guárdalo donde nadie más lo vea. Quien la tenga puede entrar como tú.") if ok
                      else tr("No se pudo copiar al portapapeles."), True)

        def importar():
            def hecho(t):
                if enlinea.importar_identidad(t):
                    app.son("guardado")
                    app.decir(tr("Identidad cambiada. En los servidores donde jugabas con ella, vuelves a ser tú."), True)
                else:
                    app.son("error")
                    app.decir(tr("Eso no es una identidad de Puerto Bravo. Empieza por P B uno y un guion."), True)
            app.abrir(EntradaTexto(app, tr("Pega aquí la identidad que guardaste"), hecho, maximo=90, secreto=True, ayuda=tr("Control V pega.")))
        enlinea.identidad()
        app.abrir(Menu(app, tr("Tu identidad en los servidores"), [
            Opcion(tr("Qué es"), ayuda=tr("Sin contraseñas ni correo: la primera vez, el juego crea una llave y la guarda en tu carpeta de datos. Cada servidor te reconoce por ella. "
                                   "Si borras la carpeta de datos o cambias de ordenador, la pierdes, y con ella tus personajes, salvo que la hayas guardado antes.")),
            Opcion(tr("Copiar mi identidad para guardarla"), exportar, ayuda=tr("La copia al portapapeles. Es como una contraseña larga: no se la des a nadie.")),
            Opcion(tr("Recuperar una identidad guardada"), importar, ayuda=tr("Sustituye la de este ordenador por la que pegues.")),
        ], intro=tr("F1 explica cada opción")))

    def ops():
        lista = [Opcion(lambda s=s: f"{s.get('nombre')}, {deletrear(s.get('dir', ''))}", entrar(s), ayuda=tr("Intro entra. Si ya tienes personaje en este servidor, sigues donde lo dejaste."))
                 for s in cfg["servidores"]]
        if not lista:
            lista.append(Opcion(tr("Todavía no tienes ningún servidor en la lista"), ayuda=tr("Añade uno con la dirección que te dé quien lo lleva.")))
        lista += [Opcion(tr("Añadir un servidor"), anadir, ayuda=tr("Te pide la dirección que te ha dado quien lleva el servidor y la apunta en tu lista.")),
                  Opcion(tr("Quitar un servidor de la lista"), quitar, ayuda=tr("Eliges cuál. Tu personaje no se borra: sigue guardado en ese servidor.")),
                  Opcion(lambda: tr('Tu nombre de jugador: {v}').format(v=(cfg['red_nombre'] or tr('sin poner'))), nombre,
                         ayuda=tr("Intro para cambiarlo. Solo cuenta en los servidores en los que entres por primera vez.")),
                  Opcion(tr("Tu identidad"), identidad, ayuda=tr("Cómo te reconoce cada servidor, y cómo guardar tu identidad para no perder tus personajes.")),
                  Opcion(tr("Qué es jugar en un servidor"),
                         ayuda=tr("El mismo juego, con todo lo que haces por tu cuenta, misiones, trabajos, casas y negocios, y además jugadores de verdad: se les oye, se habla con ellos, "
                               "se les da o se les quita dinero, armas y vehículos, se forman bandas, se pelea por los barrios y se hacen misiones en grupo. "
                               "Tu personaje en línea es distinto de tus partidas de un jugador y se guarda en el servidor. La hora es la del servidor y no se para."))]
        return lista
    try:                                                     # las copias de pruebas traen su servidor apuntado
        from . import rutas
        with open(rutas.data("config", "servidor_pruebas.txt"), encoding="utf-8") as f:
            for linea in f:
                if "|" in linea:
                    n, d = [t.strip() for t in linea.split("|", 1)]
                    if d and not any(x.get("dir") == d for x in cfg["servidores"]):
                        cfg["servidores"] = list(cfg["servidores"]) + [{"nombre": n, "dir": d, "cert": ""}]
    except OSError:
        pass
    if getattr(app, "enlace", None) is not None:             # una entrada que se quedó a medias
        app.enlace.cli.cerrar()
        app.enlace = None
    m = Menu(app, tr("Jugar en un servidor"), ops, intro=tr("Elige un servidor y pulsa Intro. F1 explica cada opción"))
    app.abrir(m)


# ============================================================== dentro de la partida
def _al_juego(p):
    app = p.app
    while len(app.pila) > 1 and app.pila[-1] is not p:
        app.pila.pop()
    app.teclas.clear()


def _numero(app, titulo, hecho, tope=10 ** 7):
    def f(t):
        try:
            n = int("".join(c for c in t if c.isdigit()) or "0")
        except ValueError:
            n = 0
        if n <= 0 or n > tope:
            app.son("error")
            app.decir(tr("Esa cantidad no vale."), True)
            return
        hecho(n)
    app.abrir(EntradaTexto(app, titulo, f, maximo=9))


TITULOS_ROL = {"ic": tr("Qué dice tu personaje. Lo oye quien esté cerca"), "yo": tr("Qué hace tu personaje. Por ejemplo: abre la puerta"),
               "ooc": tr("Mensaje fuera de personaje, para todo el servidor")}


def chat(p, canal="todos", a=None, titulo=tr("Mensaje para todo el servidor")):
    app = p.app
    if canal in TITULOS_ROL:
        if not p.sv_rol():
            app.son("error")
            return app.decir(p.sv_rol_motivo(), True)
        titulo = TITULOS_ROL[canal]
    ayuda = None
    if p.sv_rol():
        ayuda = (tr("Escribe y pulsa Intro. En cualquier mensaje, si empiezas por barra yo y un espacio, cuentas lo que hace tu personaje; con barra ep hablas en personaje, "
                 "para los que están cerca; y con barra fp, fuera de personaje, para todo el servidor."))
    from . import gente                                      # frases ya escritas: con Tabulador, o con X o Cuadrado en el mando
    frases = gente.lista("rol_frases_" + canal) if canal in TITULOS_ROL else gente.lista("frases_chat") if canal == "todos" else None
    app.abrir(EntradaTexto(app, titulo, lambda t: p.sv_enviar_chat(t, canal, a), maximo=300, ayuda=ayuda, propuestas=frases))


def ficha_propia(p):
    """Escribir tu frase de ficha: lo que los demás leen de tu personaje."""
    app = p.app
    if not p.sv_rol():
        app.son("error")
        return app.decir(p.sv_rol_motivo(), True)
    app.abrir(EntradaTexto(app, tr("Tu ficha: una frase sobre tu personaje"), p.sv_poner_ficha, inicial=p.sv.get("ficha", ""), maximo=enlinea.MAX_FICHA,
                           ayuda=tr("Quién es tu personaje, cómo es o a qué se dedica, en una frase de hasta doscientas letras. La puede leer cualquier jugador del servidor. "
                                 "Si la dejas vacía, se quita. Lo que escribas no se anota en el registro del juego.")))


def rol(p):
    """El menú de rol: hablar en personaje, describir una acción, hablar fuera de personaje, la ficha y lo dicho."""
    app, sv = p.app, p.sv

    def repasar(canales, titulo):
        def abrir():
            lineas = [t for c, t in reversed(sv["historial"]) if c in canales]
            app.abrir(Menu(app, titulo, [Opcion(t, ayuda=tr("Una línea de lo dicho. La más reciente va primero.")) for t in lineas]
                           or [Opcion(tr("Todavía no hay nada"), ayuda=tr("Cuando alguien diga algo por estos canales, aparecerá aquí."))], intro=tr("Lo último, primero")))
        return abrir

    def ops():
        if not p.sv_rol():
            return [Opcion(p.sv_rol_motivo(), ayuda=tr("Sin canales de rol, los mensajes van por el chat de siempre: para todos, para los que están cerca, para tu banda o para tu grupo."))]
        metros = sv["info"].get("rol_metros", 30)
        return [Opcion(tr("Hablar en personaje"), lambda: chat(p, "ic"),
                       ayuda=tr('Lo que dice tu personaje. Lo oye quien esté a menos de {metros} metros. También con Mayúsculas F10 durante el juego y, con mando, en el menú de acciones. Hay frases ya escritas: Tabulador, o el botón X o Cuadrado, pasa por ellas.').format(metros=(metros))),
                Opcion(tr("Describir lo que hace tu personaje"), lambda: chat(p, "yo"),
                       ayuda=tr('Escribes, por ejemplo, abre la puerta, y los que están a menos de {metros} metros oyen tu nombre y abre la puerta. También con Control F10 y, con mando, en el menú de acciones. Hay acciones ya escritas: Tabulador, o el botón X o Cuadrado, pasa por ellas.').format(metros=(metros))),
                Opcion(tr("Hablar fuera de personaje"), lambda: chat(p, "ooc"),
                       ayuda=tr("Para hablar como jugador y no como tu personaje: dudas, avisos, quedar. Lo oye todo el servidor.")),
                Opcion(lambda: tr("Tu ficha: ") + (sv.get("ficha") or tr("sin escribir")), lambda: ficha_propia(p),
                       ayuda=tr("Una frase sobre tu personaje que cualquier jugador puede leer: en Quién hay, eligiéndote, o con Mayúsculas J si te tiene cerca.")),
                Opcion(tr("Repasar lo dicho en personaje y las acciones"), repasar(("ic", "yo"), tr("En personaje y acciones")),
                       ayuda=tr("Lo último que se ha dicho en personaje y las acciones que se han contado, lo más reciente primero.")),
                Opcion(tr("Repasar lo dicho fuera de personaje"), repasar(("ooc",), tr("Fuera de personaje")),
                       ayuda=tr("Lo último que se ha dicho fuera de personaje en el servidor, lo más reciente primero.")),
                Opcion(tr("Cómo se rolea aquí"),
                       ayuda=tr('Hay tres canales, cada uno con su sonido. En personaje: habla tu personaje, y lo oye quien esté a menos de {metros} metros. Acción: cuentas lo que hace, y se oye tu nombre seguido de lo que escribas. Fuera de personaje: hablas tú, y lo oye todo el servidor. En cualquier mensaje puedes empezar por barra yo, barra ep o barra fp para elegir el canal, y barra ficha y una frase cambia tu ficha. Para hablar de viva voz, usad un programa de voz aparte.').format(metros=(metros)))]

    app.abrir(Menu(app, tr("Rol"), ops, intro=tr("F1 explica cada opción")))


def jugador(p, r):
    """Lo que puedes hacer con otro jugador."""
    app, j, sv = p.app, p.j, p.sv

    def dinero():
        def hecho(n):
            if p.dar_dinero_a(r, n):
                app.cerrar(m)
        _numero(app, tr('Cuánto dinero le das a {nombre}. Tienes {dinero}').format(nombre=(r.nombre), dinero=(j.dinero)), hecho, tope=max(1, j.dinero))

    def dar():
        def arma(ident):
            def f():
                if r.mapa != p.mundo.id or r.dist(*p.pos()) > 12:
                    app.son("error")
                    return app.decir(tr('Para darle algo en mano, {nombre} tiene que estar a tu lado.').format(nombre=(r.nombre)), True)
                if ident == j.arma:
                    j.arma = "punos"
                del j.armas[ident]
                p.red.enviar({"t": "dar", "a": r.id, "clase": "arma", "id": ident, "n": 1})
                app.cerrar(md)
            return f

        def balas(ident):
            def f():
                def hecho(n):
                    n = min(n, j.armas[ident]["reserva"])
                    if n <= 0 or r.mapa != p.mundo.id or r.dist(*p.pos()) > 12:
                        app.son("error")
                        return app.decir(tr('Para darle algo en mano, {nombre} tiene que estar a tu lado.').format(nombre=(r.nombre)), True)
                    j.armas[ident]["reserva"] -= n
                    p.red.enviar({"t": "dar", "a": r.id, "clase": "balas", "id": ident, "n": n})
                    app.cerrar(md)
                _numero(app, tr('Cuántas balas de reserva le das. Tienes {reserva}').format(reserva=(j.armas[ident]['reserva'])), hecho, tope=max(1, j.armas[ident]["reserva"]))
            return f

        def objeto(ident):
            def f():
                if j.objetos.get(ident, 0) <= 0 or r.mapa != p.mundo.id or r.dist(*p.pos()) > 12:
                    app.son("error")
                    return app.decir(tr('Para darle algo en mano, {nombre} tiene que estar a tu lado.').format(nombre=(r.nombre)), True)
                j.objetos[ident] -= 1
                p.red.enviar({"t": "dar", "a": r.id, "clase": "objeto", "id": ident, "n": 1})
                md.refrescar(False)
            return f

        def lista():
            out = []
            for ident, d in j.armas.items():
                if ident == "punos" or ident not in p.armas_d:
                    continue
                out.append(Opcion(tr('El arma: {nombre}').format(nombre=(p.armas_d[ident]['nombre'])), arma(ident),
                                  ayuda=tr("Se la das y dejas de tenerla. Tiene que estar a tu lado.")))
                if d.get("reserva", 0) > 0:
                    out.append(Opcion(lambda ident=ident: tr('Balas de {lower}: tienes {reserva} de reserva').format(lower=(p.armas_d[ident]['nombre'].lower()), reserva=(j.armas[ident]['reserva'])), balas(ident),
                                      ayuda=tr("Escribes cuántas balas de reserva le das. Tiene que estar a tu lado.")))
            nombres = {o["id"]: o["nombre"] for o in p.datos["objetos"]}
            for ident, n in j.objetos.items():
                if n > 0 and ident in nombres:
                    out.append(Opcion(lambda ident=ident: tr('{v}: tienes {get}').format(v=(nombres[ident]), get=(j.objetos.get(ident, 0))), objeto(ident),
                                      ayuda=tr("Cada Intro le das uno. Tiene que estar a tu lado.")))
            return out or [Opcion(tr("No llevas nada que dar"), ayuda=tr("No tienes armas, balas de reserva ni objetos que se puedan dar."))]
        md = Menu(app, tr('Qué le das a {nombre}. Tiene que estar a tu lado').format(nombre=(r.nombre)), lista)
        app.abrir(md)

    def ops():
        rel = p.sv_relacion(r)
        out = [Opcion(lambda: p.donde_esta(r) + (f", {rel}" if rel else "") + (tr(", en modo pasivo") if getattr(r, "pasivo", False) else "")
                      + (tr(", en zona segura") if getattr(r, "segura", False) else ""),
                      ayuda=tr("Dónde está, si va a pie o al volante, si es de tu banda o de tu grupo y si está en modo pasivo o en zona segura.")),
               Opcion(tr("Marcarle en el GPS"), lambda: (_al_juego(p), p.gps_a_amigo(r)),
                      ayuda=tr("Vuelves al juego con el GPS hacia esta persona. Si está en otra localidad, te lleva al sitio más cercano a donde está. Si se mueve, vuelve a marcarla."))]
        if p.sv_rol() and not getattr(r, "ia", False):
            out.append(Opcion(tr("Leer su ficha"), lambda: p.sv_pedir_ficha(r), ayuda=tr("La frase que ha escrito sobre su personaje.")))
        out += [
               Opcion(tr("Mensaje solo para él o ella"), lambda: chat(p, "priv", r.id, tr('Mensaje privado para {nombre}').format(nombre=(r.nombre))),
                      ayuda=tr("Lo lee solo esta persona, esté donde esté en el servidor.")),
               Opcion(tr("Darle dinero"), dinero, ayuda=tr("Escribes cuánto. Sale de lo que llevas encima y le llega esté donde esté.")),
               Opcion(tr("Darle un arma, balas o un objeto"), dar, ayuda=tr("En mano: tiene que estar a tu lado."))]
        if sv["info"].get("pvp"):
            out.append(Opcion(tr("Fijarle como objetivo"), lambda: (_al_juego(p), setattr(p, "objetivo", r), p.decir(tr('Fijado: {donde_esta}.').format(donde_esta=(p.donde_esta(r))), True)),
                              ayuda=tr("Durante el juego, la Q fija a quien te ha atacado, y Mayúsculas Q recorre a todos los que hay cerca, también a los demás jugadores.")))
        if sv["banda"] and sv["rango"] in ("jefe", "mano") and getattr(r, "banda", None) is None:
            out.append(Opcion(tr('Invitarle a tu banda, {nombre}').format(nombre=(sv['banda']['nombre'])), lambda: p.red.enviar({"t": "banda_invitar", "a": r.id}),
                              ayuda=tr("Le llega la invitación y tiene tres minutos para aceptarla. Entraría como miembro.")))
        if sv["grupo"] in (None, p.red.id):
            out.append(Opcion(tr("Invitarle a tu grupo de misión"), lambda: p.red.enviar({"t": "grupo_invitar", "a": r.id, "mision": p.mision["def"]["titulo"] if p.mision else ""}),
                              ayuda=tr("En grupo, los enemigos de tus misiones son de todos, no os podéis herir entre vosotros, y quien te ayuda cobra la mitad de la recompensa.")))
        return out
    m = Menu(app, f"{r.nombre}", ops)
    app.abrir(m)


def banda(p):
    app, j, sv = p.app, p.j, p.sv
    env = p.red.enviar

    def crear():
        precio = sv["info"].get("precios", {}).get("precio_banda", 2000)

        def hecho(t):
            env({"t": "banda_crear", "nombre": t.strip()[:30]})
            app.cerrar(m)
        app.abrir(EntradaTexto(app, tr('Nombre de tu banda. Fundarla cuesta {precio} euros').format(precio=(precio)), hecho, maximo=30))

    def miembro(q):
        def f():
            def rango(r):
                return lambda: (env({"t": "banda_rango", "cuenta": q["cuenta"], "rango": r}), app.cerrar(mm))
            mm = Menu(app, f"{q['nombre']}, {q['rango']}", [
                Opcion(tr("Hacerle mano derecha"), rango("mano"), ayuda=tr("Puede invitar, sacar de la caja, reclamar barrios y declarar guerras.")),
                Opcion(tr("Dejarle de miembro"), rango("miembro"),
                       ayuda=tr("Le quitas el rango de mano derecha, si lo tenía: ya no podrá invitar, sacar de la caja, reclamar barrios ni declarar guerras.")),
                Opcion(tr("Cederle el mando de la banda"), rango("jefe"), ayuda=tr("Pasa a ser el jefe y tú quedas de mano derecha.")),
                Opcion(tr("Echarle de la banda"), lambda: (env({"t": "banda_expulsar", "cuenta": q["cuenta"]}), app.cerrar(mm)),
                       ayuda=tr("Sale de la banda al momento y se avisa a los demás de la banda."))])
            app.abrir(mm)
        return f

    def ver_gente():
        b = sv["banda"]
        jefe = sv["rango"] == "jefe"
        nombres = {"jefe": "jefe", "mano": tr("mano derecha"), "miembro": "miembro"}
        app.abrir(Menu(app, tr('Gente de {nombre}').format(nombre=(b['nombre'])), lambda: [
            Opcion(f"{q['nombre']}, {nombres.get(q['rango'], q['rango'])}, {tr('en línea') if q['en_linea'] else 'fuera'}",
                   miembro(q) if jefe and q["cuenta"] != sv.get("cuenta") else None,
                   ayuda=tr("Intro para cambiarle el rango, cederle el mando o echarle de la banda.") if jefe and q["cuenta"] != sv.get("cuenta")
                   else tr("Su rango en la banda y si está conectado ahora.")) for q in sv["banda"]["miembros"]] if sv["banda"]
            else [Opcion(tr("Ya no estás en la banda"), ayuda=tr("Has dejado la banda o te han echado: ya no puedes ver su gente ni su caja."))]))

    def caja():
        def ops():
            b = sv["banda"]
            if not b:
                return [Opcion(tr("Ya no estás en la banda"), ayuda=tr("Has dejado la banda o te han echado: ya no puedes ver su gente ni su caja."))]
            out = [Opcion(tr('En la caja hay {caja} euros').format(caja=(b['caja'])),
                          ayuda=tr("El dinero común de la banda. Lo meten los miembros y los barrios cada medianoche, y con él se pagan los barrios y las guerras.")),
                   Opcion(tr("Ingresar dinero"), lambda: _numero(app, tr('Cuánto ingresas. Llevas {dinero}').format(dinero=(j.dinero)), lambda n: env({"t": "banda_ingresar", "n": n}), tope=max(1, j.dinero)),
                          ayuda=tr("Escribes cuánto metes de lo que llevas encima. Ingresar puede cualquiera de la banda; sacar, solo el jefe y su mano derecha."))]
            if sv["rango"] in ("jefe", "mano"):
                out.append(Opcion(tr("Sacar dinero"), lambda: _numero(app, tr('Cuánto sacas. Hay {caja}').format(caja=(b['caja'])), lambda n: env({"t": "banda_sacar", "n": n}), tope=max(1, b["caja"])),
                                  ayuda=tr("Escribes cuánto y te lo llevas encima. Queda apuntado en la caja con tu nombre.")))
            out += [Opcion(tr('{nombre}: {v} {abs} euros, {motivo}').format(nombre=(tr_servidor(str(a['nombre']))), v=(tr('más') if a['cantidad'] >= 0 else tr('menos')), abs=(abs(a['cantidad'])), motivo=(tr_servidor(str(a['motivo'])))),
                           ayuda=tr("Un apunte de la caja: quién metió o sacó dinero, cuánto y por qué.")) for a in b["apuntes"]]
            return out
        app.abrir(Menu(app, tr("La caja de la banda"), ops, intro=tr("Debajo están los últimos apuntes")))

    def alianza():
        def con(nombre, romper=False):
            return lambda: (env({"t": "alianza", "banda": nombre, "romper": romper}), app.cerrar(ma))
        b = sv["banda"]
        otras = [x for x in sv["bandas"] if x["nombre"] != b["nombre"]]
        ma = Menu(app, tr("Alianzas"), [Opcion(tr('Romper la alianza con {n}').format(n=(n)), con(n, True),
                                               ayuda=tr("Se rompe al momento y se avisa a esa banda. Desde entonces os podéis herir y declarar la guerra.")) for n in b["aliadas"]]
                  + [Opcion(tr('Proponer una alianza a {nombre}').format(nombre=(x['nombre'])), con(x["nombre"]),
                            ayuda=tr("Se lo dices a esa banda. Si su jefe ya os la había propuesto, queda cerrada; si no, se cierra cuando lo haga.")) for x in otras if x["nombre"] not in b["aliadas"]]
                  or [Opcion(tr("No hay más bandas en el servidor"), ayuda=tr("Cuando alguien funde otra banda, podrás proponerle una alianza aquí."))],
                  intro=tr("Una alianza se cierra cuando los dos jefes se la proponen el uno al otro. Los aliados no se pueden herir"))
        app.abrir(ma)

    def salir():
        mm = Menu(app, tr("¿Seguro que dejas la banda?"), [Opcion(tr("No"), lambda: app.cerrar(mm)), Opcion(tr("Sí, la dejo"), lambda: (env({"t": "banda_salir"}), app.cerrar(mm), app.cerrar(m)),
                                                                                   ayuda=tr("Sales de la banda. Si eras el jefe, el mando pasa a otro miembro; si no queda nadie, la banda se disuelve."))])
        app.abrir(mm)

    def disolver():
        mm = Menu(app, tr("¿Seguro que disuelves la banda? Los barrios quedan libres y la caja te la llevas tú"),
                  [Opcion(tr("No"), lambda: app.cerrar(mm)), Opcion(tr("Sí, se acabó"), lambda: (env({"t": "banda_disolver"}), app.cerrar(mm), app.cerrar(m)),
                                                            ayuda=tr("La banda desaparece para todos: sus miembros se quedan sin banda, sus barrios quedan libres y lo que haya en la caja pasa a tu bolsillo."))])
        app.abrir(mm)

    def responder(si):
        def f():
            env({"t": "banda_resp", "si": si})
            sv["inv_banda"] = None
            m.refrescar(False)
        return f

    def ops():
        b = sv["banda"]
        pr = sv["info"].get("precios", {})
        if not b:
            out = []
            if sv["inv_banda"]:
                out += [Opcion(tr('{de} te invita a la banda {nombre}: aceptar').format(de=(sv['inv_banda']['de']), nombre=(sv['inv_banda']['nombre'])), responder(True),
                               ayuda=tr("Entras en la banda como miembro. La invitación caduca a los tres minutos.")),
                        Opcion(tr("Rechazar la invitación"), responder(False), ayuda=tr("Dices que no. Para entrar más adelante, tendrán que volver a invitarte."))]
            out += [Opcion(tr("No estás en ninguna banda"), ayuda=tr("Puedes fundar la tuya aquí debajo, o esperar a que el jefe o la mano derecha de otra banda te invite.")),
                    Opcion(tr('Fundar una banda: {get} euros').format(get=(pr.get('precio_banda', 2000))), crear,
                           ayuda=tr("Eres el jefe. Puedes invitar a otros jugadores, llevar una caja común, quedaros con barrios, que dejan dinero en la caja cada medianoche, y declarar guerras."))]
            return out
        x, y = p.pos()
        try:
            barrio = p.mundo.barrio(x, y)
        except Exception:
            barrio = None
        dueno = p.sv_dueno_barrio(p.mundo.id, barrio["id"]) if barrio else None
        out = [Opcion(tr('{nombre}. Eres {get}. Sois {len}, con {len2} barrios y {caja} euros en la caja').format(nombre=(b['nombre']), get=(({'jefe': tr('el jefe'), 'mano': tr('la mano derecha')}).get(sv['rango'], tr('miembro'))), len=(len(b['miembros'])), len2=(len(b['barrios'])), caja=(b['caja'])),
                      ayuda=tr("Tu rango, cuántos sois, cuántos barrios tenéis y el dinero de la caja.")),
               Opcion(tr("La gente de la banda"), ver_gente,
                      ayuda=tr("Cada miembro con su rango y si está conectado.") + (tr(" Como jefe, Intro sobre uno cambia su rango o lo echa.") if sv["rango"] == "jefe" else "")),
               Opcion(tr('La caja: {caja} euros').format(caja=(b['caja'])), caja, ayuda=tr("Lo que hay, ingresar o sacar dinero y los últimos apuntes.")),
               Opcion(tr("Mensaje para la banda"), lambda: chat(p, "banda", None, tr("Mensaje para tu banda")),
                      ayuda=tr("Lo leen solo los de tu banda que estén conectados, estén donde estén."))]
        if barrio and sv["rango"] in ("jefe", "mano"):
            nombre_b = barrio.get("nombre", barrio["id"])
            if dueno is None:
                out.append(Opcion(tr('Reclamar este barrio, {nombre_b}: {get} euros de la caja').format(nombre_b=(nombre_b), get=(pr.get('precio_barrio', 3000))), lambda: env({"t": "barrio_reclamar"}),
                                  ayuda=tr('No es de nadie. Dejará {get} euros en la caja cada medianoche del servidor. Podéis tener un barrio más que miembros sois.').format(get=(pr.get('renta_barrio', 300)))))
            elif dueno["banda"] != b["id"]:
                out.append(Opcion(tr('Declarar la guerra por {nombre_b}, que es de {nombre}: {get} euros de la caja').format(nombre_b=(nombre_b), nombre=(dueno['nombre']), get=(pr.get('precio_guerra', 1000))),
                                  lambda: env({"t": "barrio_guerra"}),
                                  ayuda=tr('No empieza ya: empieza a los {get} minutos, para que a nadie le quiten un barrio mientras duerme, y dura {get2}. Gana la banda que más gente tenga dentro del barrio y más rivales tumbe. Si empatáis, se lo queda quien lo tenía.').format(get=(pr.get('guerra_espera', 20)), get2=(pr.get('guerra_dura', 10)))))
            else:
                out.append(Opcion(tr('Este barrio, {nombre_b}, es vuestro').format(nombre_b=(nombre_b)),
                                  ayuda=tr("Deja dinero en la caja cada medianoche. Otra banda os lo puede quitar declarándoos la guerra.")))
        if sv["rango"] == "jefe":
            out += [Opcion(lambda: tr('Fuego amigo dentro de la banda: {v}').format(v=(tr('sí') if sv['banda'] and sv['banda']['fuego'] else tr('no'))),
                           lambda: env({"t": "banda_fuego", "si": not sv["banda"]["fuego"]}), ayuda=tr("Con no, los de la banda no os podéis herir entre vosotros.")),
                    Opcion(tr("Alianzas con otras bandas"), lambda: (env({"t": "banda_lista"}), alianza()),
                           ayuda=tr("Proponer una alianza a otra banda o romper una que tengáis. Entre aliados no os podéis herir ni declararos la guerra.")),
                    Opcion(tr("Disolver la banda"), disolver, ayuda=tr("Te pregunta antes. La banda desaparece, los barrios quedan libres y la caja te la llevas tú."))]
        out.append(Opcion(tr("Dejar la banda"), salir, ayuda=tr("Te pregunta antes. Si eres el jefe, el mando pasa a otro miembro.")))
        return out
    m = Menu(app, tr("Tu banda"), ops)
    app.abrir(m)


def opciones_propiedad(p, l):
    """En un servidor, lo que el dueño puede hacer con su casa o su negocio: venderlo al mercado o a otros jugadores."""
    if not getattr(p, "en_servidor", False) or int(l.get("precio", 0) or 0) <= 0:
        return []
    app = p.app
    pct = 70

    def al_mercado():
        mm = Menu(app, tr('¿Vendes {nombre} al mercado por {v} euros? Vuelve a estar en venta para cualquiera').format(nombre=(l.nombre), v=(int(l.get('precio', 0)) * pct // 100)), [
            Opcion(tr("No"), lambda: app.cerrar(mm)),
            Opcion(tr("Sí, vender"), lambda: (p.red.enviar({"t": "prop_soltar", "lugar": l.id}), _al_juego(p)),
                   ayuda=tr("Vuelves al juego y la propiedad sale a la venta para cualquiera. Si al servidor no le consta que la pagaras aquí, no te da dinero."))])
        app.abrir(mm)

    def a_jugadores():
        def hecho(t):
            n = int("".join(c for c in t if c.isdigit()) or "0")
            p.red.enviar({"t": "prop_oferta", "lugar": l.id, "precio": n})
            app.decir(tr('En venta por {n} euros. Quien lo quiera, lo compra en la puerta.').format(n=(n)) if n else tr("Retirado de la venta."), True)
        app.abrir(EntradaTexto(app, tr("Precio para otros jugadores. Cero para no venderlo"), hecho, maximo=9))
    return [Opcion(lambda: tr("En venta para otros jugadores: ") + (tr('{sv_oferta} euros').format(sv_oferta=(p.sv_oferta(l))) if p.sv_oferta(l) else tr("no")), a_jugadores,
                   ayuda=tr("Pones tu precio. Otro jugador lo compra en la puerta y el dinero te llega a ti, estés conectado o no.")),
            Opcion(tr('Vender al mercado por {v} euros').format(v=(int(l.get('precio', 0)) * pct // 100)), al_mercado,
                   ayuda=tr("Recuperas una parte de lo que costó y la propiedad vuelve a estar en venta para cualquiera. Saca antes los vehículos del garaje."))]


def en_venta(p):
    """Casas y negocios de esta localidad: los que están libres, los que vende un jugador y de quién es cada uno."""
    app = p.app

    def ops():
        libres, ofertas, ocupados = [], [], []
        for l in p.mundo.lugares.values():
            if l.tipo not in ("casa", "negocio") or int(l.get("precio", 0) or 0) <= 0:
                continue
            ir = (lambda l=l: (_al_juego(p), p.gps_a_lugar(l)))
            que = tr("Casa") if l.tipo == "casa" else tr("Negocio")
            d = p.sv["props"].get(l.id)
            if d is None:
                libres.append(Opcion(tr('{que} en venta: {nombre}, {int} euros').format(que=(que), nombre=(l.nombre), int=(int(l.get('precio')))) + (tr(', da {int} al día').format(int=(int(l.get('ingresos', 0)))) if l.tipo == "negocio" else ""), ir,
                                     ayuda=tr("No es de nadie. Intro marca el sitio en el GPS, y se compra en la puerta.")))
            elif d.get("cuenta") == p.sv.get("cuenta"):
                ocupados.append(Opcion(tr('{que} tuyo: {nombre}').format(que=(que), nombre=(l.nombre)), ir, ayuda=tr("Intro marca en el GPS dónde está.")))
            elif d.get("oferta"):
                ofertas.append(Opcion(tr('{que} que vende {nombre}: {nombre2}, {oferta} euros').format(que=(que), nombre=(d['nombre']), nombre2=(l.nombre), oferta=(d['oferta'])), ir,
                                      ayuda=tr("Intro marca el sitio en el GPS. Se compra en la puerta, al precio que ha puesto, y el dinero le llega a ese jugador.")))
            else:
                ocupados.append(Opcion(tr('{que} de {nombre}: {nombre2}').format(que=(que), nombre=(d['nombre']), nombre2=(l.nombre)), ir,
                                       ayuda=tr("No está en venta. Intro marca en el GPS dónde está.")))
        return (libres + ofertas + ocupados) or [Opcion(tr("En esta localidad no hay casas ni negocios que se puedan comprar"),
                                                        ayuda=tr("Las casas y los negocios que se compran están en otras localidades."))]
    app.abrir(Menu(app, tr('Casas y negocios de {nombre}').format(nombre=(p.mundo.nombre)), ops, intro=tr("Primero lo que está en venta. Intro marca el sitio en el GPS")))


def tablon(p):
    """Bandas, barrios y guerras del servidor."""
    app, sv = p.app, p.sv
    p.red.enviar({"t": "banda_lista"})

    def ops():
        out = []
        for g in sv["territorios"].get("guerras", []):
            mapa = p.mapas.get(g["mapa"])
            barrio = next((b.get("nombre", b["id"]) for b in getattr(mapa, "barrios", []) if b["id"] == g["barrio"]), g["barrio"]) if mapa else g["barrio"]
            cuando = tr('empieza en {max} minutos').format(max=(max(1, g.get('falta', 0) // 60))) if g.get("fase") == "espera" else tr('en marcha, {int} a {int2}, quedan {max} minutos').format(int=(int(g.get('pa', 0))), int2=(int(g.get('pd', 0))), max=(max(1, g.get('queda', 0) // 60)))
            out.append(Opcion(tr('Guerra: {get} contra {get2} por {barrio}, en {v}: {cuando}').format(get=(g.get('ataca_n')), get2=(g.get('defiende_n')), barrio=(barrio), v=(mapa.nombre if mapa else g['mapa']), cuando=(cuando)),
                              ayuda=tr("Una guerra declarada por un barrio. Gana la banda que más gente tenga dentro del barrio y más rivales tumbe; si empatan, se lo queda quien lo tenía.")))
        for b in sv["bandas"]:
            out.append(Opcion(tr('{nombre}: {miembros} miembros, {barrios} barrios').format(nombre=(b['nombre']), miembros=(b['miembros']), barrios=(b['barrios'])),
                              ayuda=tr("Una banda del servidor, con cuántos miembros tiene y cuántos barrios controla.")))
        for t in sv["territorios"].get("barrios", []):
            mapa = p.mapas.get(t["mapa"])
            barrio = next((b.get("nombre", b["id"]) for b in getattr(mapa, "barrios", []) if b["id"] == t["barrio"]), t["barrio"]) if mapa else t["barrio"]
            out.append(Opcion(tr('{barrio}, en {v}: de {nombre}').format(barrio=(barrio), v=(mapa.nombre if mapa else t['mapa']), nombre=(t['nombre'])),
                              ayuda=tr("Un barrio con dueño. Le deja dinero a esa banda cada medianoche del servidor.")))
        return out or [Opcion(tr("Todavía no hay bandas en este servidor"), ayuda=tr("Cualquiera puede fundar una en En línea, Tu banda."))]
    app.abrir(Menu(app, tr("Bandas, barrios y guerras"), ops, intro=tr("Primero las guerras, luego las bandas y luego de quién es cada barrio")))


def grupo(p):
    app, sv = p.app, p.sv

    def responder(si):
        def f():
            p.red.enviar({"t": "grupo_resp", "si": si})
            sv["inv_grupo"] = None
            m.refrescar(False)
        return f

    def ops():
        out = []
        if sv["inv_grupo"]:
            inv = sv["inv_grupo"]
            out += [Opcion(tr('{nombre} te invita a su grupo').format(nombre=(inv['nombre'])) + (tr(' para la misión {mision}').format(mision=(inv['mision'])) if inv["mision"] else "") + tr(": aceptar"), responder(True),
                           ayuda=tr("Entras en su grupo de misión: le ayudas en sus misiones y cobras la mitad de la recompensa.")),
                    Opcion(tr("Rechazar la invitación"), responder(False), ayuda=tr("Dices que no. Para unirte más adelante, tendrá que volver a invitarte."))]
        if sv["grupo"] is None:
            out.append(Opcion(tr("No vas en ningún grupo"), ayuda=tr("Para formar uno, abre En línea, Quién hay, elige a alguien e invítale a tu grupo de misión. Caben cuatro.")))
        else:
            lider = next((q["nombre"] for q in sv["miembros"] if q["id"] == sv["grupo"]), tr("alguien"))
            out.append(Opcion(tr("Vas en un grupo. Lo lleva ") + (tr("tú") if sv["grupo"] == p.red.id else lider) + tr(". Sois: ") + ", ".join(q["nombre"] for q in sv["miembros"]),
                              ayuda=tr("Quién lleva el grupo y quiénes vais en él. Caben cuatro.")))
            if sv["mision_grupo"]:
                out.append(Opcion(tr('Misión del grupo, {titulo}: {texto}').format(titulo=(sv['mision_grupo']['titulo']), texto=(sv['mision_grupo']['texto'])),
                                  lambda: (_al_juego(p), p.gps_a_lugar(p.lugares[sv["mision_grupo"]["lugar"]])) if p.lugares.get(sv["mision_grupo"].get("lugar") or "") else None,
                                  ayuda=tr("Intro marca en el GPS el sitio de la misión.")))
            out += [Opcion(tr("Mensaje para el grupo"), lambda: chat(p, "grupo", None, tr("Mensaje para tu grupo")),
                           ayuda=tr("Lo leen solo los de tu grupo de misión, estén donde estén.")),
                    Opcion(tr("Dejar el grupo") if sv["grupo"] != p.red.id else tr("Deshacer el grupo"), lambda: (p.red.enviar({"t": "grupo_salir"}), app.cerrar(m)),
                           ayuda=tr("Sales del grupo y los demás siguen juntos.") if sv["grupo"] != p.red.id else tr("El grupo se deshace para todos y se avisa a los demás."))]
        out.append(Opcion(tr("Cómo funcionan las misiones en grupo"),
                          ayuda=tr("Quien lleva el grupo empieza una misión suya, de las de siempre. Los demás oís qué pide cada paso y el GPS os lleva al sitio. "
                                "Los enemigos de la misión aparecen también en vuestro juego, y lo que le quitáis a uno se lo quitáis para todos. "
                                "Entre los del grupo no os podéis herir. Al completarla, quien la llevaba cobra su recompensa y cada uno de los demás, la mitad, una vez por misión.")))
        return out
    m = Menu(app, tr("Grupo de misión"), ops, intro=tr("F1 explica cada opción"))
    app.abrir(m)


def actividades(p):
    """Carrera con apuesta y reparto en equipo: lo mismo que en Jugar con amigos."""
    app = p.app

    def hecho(resultado, salir=False):
        ok, texto = resultado
        if texto:
            app.son("menu_ok" if ok else "error")
            app.decir(texto, True)
        m.refrescar(False)
        if ok and salir:
            _al_juego(p)

    def carrera():
        from . import menus_juego
        menus_juego.lista_lugares(p, al_elegir=lambda l: hecho(p.proponer_carrera(l)), titulo=tr("Destino de la carrera"), otras=False)

    def ops():
        out = [Opcion(lambda: p.coop_txt(), ayuda=tr("Además, a pie junto al vehículo parado de otro jugador, Intro te sube de pasajero."))]
        c = p.coop
        if c is None:
            out += [Opcion(tr("Proponer una carrera hasta un lugar: 100 euros de apuesta"), carrera, ayuda=tr("Eliges el destino. Quien llega primero se lleva las apuestas.")),
                    Opcion(tr("Proponer un reparto en equipo"), lambda: hecho(p.proponer_reparto()), ayuda=tr("Cuatro entregas por esta localidad en seis minutos. Si las hacéis entre todos, cobráis todos."))]
        else:
            if c["estado"] == "propuesta" and c["de"] == p.red.id:
                out.append(Opcion(tr("Empezar ya"), lambda: hecho(p.empezar_coop(), True),
                                  ayuda=tr("Arranca la actividad con los que han aceptado y vuelves al juego. Hace falta que haya aceptado al menos uno.")))
            elif c["estado"] == "propuesta" and p.red.id not in c["participantes"]:
                out.append(Opcion(tr("Aceptar y participar"), lambda: hecho(p.aceptar_coop()),
                                  ayuda=tr("Te apuntas. Si es una carrera, tienes que llevar encima el dinero de la apuesta. Empieza cuando lo diga quien la ha propuesto.")))
            if c["de"] == p.red.id:
                out.append(Opcion(tr("Cancelar la actividad"), lambda: (p.cancelar_coop(), m.refrescar(False)), ayuda=tr("La anulas para todos y se quita el GPS.")))
        return out
    m = Menu(app, tr("Actividades en común"), ops)
    app.abrir(m)


def menu(p):
    """El menú En línea del móvil, cuando la partida es de un servidor."""
    app, sv = p.app, p.sv

    def quien():
        def ops():
            x, y = p.pos()
            gente = sorted(p.remotos.values(), key=lambda r: (r.mapa != p.mundo.id, r.dist(x, y)))
            return [Opcion(lambda r=r: p.donde_esta(r) + (f", {p.sv_relacion(r)}" if p.sv_relacion(r) else "") + (tr(", personaje del servidor") if getattr(r, "ia", False) else ""),
                           lambda r=r: jugador(p, r), ayuda=tr("Intro abre lo que puedes hacer con esta persona: el GPS, un mensaje, darle cosas o invitarla.")) for r in gente] \
                or [Opcion(tr("No hay nadie más en el servidor ahora mismo"), ayuda=tr("Cuando entre alguien, aparecerá aquí con dónde está."))]
        app.abrir(Menu(app, tr("Quién hay"), ops, intro=tr("Intro sobre alguien abre lo que puedes hacer con él o con ella")))

    def repasar():
        app.abrir(Menu(app, tr("Últimos mensajes"), [Opcion(t, ayuda=tr("Un mensaje del servidor. El más reciente va primero.")) for t in reversed(p.chat)]
                       or [Opcion(tr("No hay mensajes"), ayuda=tr("Cuando alguien escriba, sus mensajes aparecerán aquí."))]))

    def pasivo():
        p.red.enviar({"t": "pasivo", "si": not sv["pasivo"]})

    def guardar():
        p.sv_guardar(ya=True)
        app.son("guardado")
        app.decir(tr("Personaje guardado en el servidor."), True)

    def salir():
        mm = Menu(app, tr("¿Sales del servidor? Tu personaje queda guardado"), [
            Opcion(tr("No, sigo jugando"), lambda: app.cerrar(mm)),
            Opcion(tr("Sí, salir al menú principal"), lambda: p.sv_salir(al_menu=True), ayuda=tr("Se guarda tu personaje en el servidor y vuelves al menú principal."))])
        app.abrir(mm)

    def version_servidor():
        from . import VERSION
        m = sv.get("mundo") or {}
        if not m.get("version"):
            return tr('Tu juego es la versión {VERSION}').format(VERSION=(VERSION))
        if m.get("igual", True):
            return tr('El servidor va con los datos de la versión {version} del juego, los mismos que tienes tú').format(version=(m['version']))
        return tr('El servidor va con los datos de la versión {version} del juego y tú tienes la {VERSION}: jugáis juntos, cada uno con lo que su versión conoce').format(version=(m['version']), VERSION=(VERSION)) + p.sv_distinto_txt()

    def info():
        i = sv["info"]
        pr = i.get("precios", {})
        if p.sv_sabe("topes"):
            p.red.enviar({"t": "economia"})                      # cómo vas de margen ahora mismo
        app.abrir(Menu(app, tr('Servidor {nombre_servidor}').format(nombre_servidor=(sv['nombre_servidor'])), [
            Opcion(tr('Te llamas {nombre}').format(nombre=(p.red.nombre)) + (tr(". Eres administrador") if sv["admin"] else ""),
                   ayuda=tr("El nombre con el que te ven los demás en este servidor, y si eres de los que lo administran.")),
            Opcion(tr("La conexión va cifrada") if sv["cifrado"] else tr("La conexión no va cifrada"),
                   ayuda=tr("Con la conexión cifrada, nadie que esté entre tú y el servidor puede leer lo que os enviáis.")),
            Opcion(version_servidor(), ayuda=tr("En un mismo servidor pueden jugar juntos jugadores con versiones distintas del juego. Cada uno ve y usa "
                                             "lo que su versión conoce: lo que solo tiene una versión más nueva no lo ven quienes van con una anterior.")),
            Opcion(tr("Caben ") + (tr('{get} jugadores a la vez').format(get=(i.get('max_jugadores'))) if i.get("max_jugadores") else tr("todos los jugadores que entren: no hay límite")),
                   ayuda=tr("Cuántos jugadores pueden estar dentro del servidor a la vez.")),
            Opcion(tr("Combate entre jugadores: ") + (tr("sí") if i.get("pvp") else tr("no")),
                   ayuda=tr("Con sí, los jugadores pueden herirse y tumbarse entre ellos, y quien tumba a otro se lleva parte del dinero que llevaba encima.")),
            Opcion(tr("Zonas seguras en hospitales, comisarías, casas y dentro de los locales: ") + (tr("sí") if i.get("seguras") else tr("no")),
                   ayuda=tr("Con sí, en esos sitios ningún jugador puede herirte ni tú a ellos.")),
            Opcion(tr("Modo pasivo permitido: ") + (tr("sí") if i.get("pasivo") else tr("no")),
                   ayuda=tr("Con sí, y si hay combate entre jugadores, puedes ponerte en modo pasivo desde el menú En línea: ni hieres ni te hieren.")),
            Opcion(tr("Contenido para adultos: ") + (tr("sí") if i.get("adultos") else tr("no")),
                   ayuda=tr("Si quien lleva el servidor permite el contenido para adultos del juego.")),
            Opcion(tr('Al llegar y al reaparecer, {get} segundos de protección').format(get=(i.get('proteccion', 0))),
                   ayuda=tr("Durante ese tiempo, al entrar en el servidor y después de que te tumben, nadie puede herirte.")),
            Opcion(tr('Fundar una banda: {get} euros. Reclamar un barrio: {get2}. Declarar una guerra: {get3}').format(get=(pr.get('precio_banda')), get2=(pr.get('precio_barrio')), get3=(pr.get('precio_guerra'))),
                   ayuda=tr("Fundar la banda lo pagas de tu bolsillo; los barrios y las guerras se pagan con la caja de la banda.")),
            Opcion(tr('Una guerra empieza a los {get} minutos de declararla y dura {get2}').format(get=(pr.get('guerra_espera')), get2=(pr.get('guerra_dura'))),
                   ayuda=tr("La espera da tiempo a la otra banda para prepararse. Gana quien más gente tenga dentro del barrio y más rivales tumbe.")),
            Opcion(tr('Ofrecen {recompensa} euros por tu cabeza').format(recompensa=(sv['recompensa'])) if sv["recompensa"] else tr("Nadie ofrece nada por tu cabeza"),
                   ayuda=tr("Sube cuando tumbas a alguien que no te había atacado. Quien te tumbe se lleva lo que ofrecen.")),
            Opcion(lambda: p.sv_economia_txt(),
                   ayuda=tr("En un servidor que lleva la cuenta del dinero, lo que ganas por tu cuenta tiene un tope por hora. No cuentan contra él las misiones de la historia, "
                         "lo que te da el servidor o te dan otros jugadores, ni los encargos repetibles que el servidor reconoce. Lo que pase del tope se retira, y el juego te dice cuánto.")),
            Opcion(tr("Canales de rol: ") + ((tr('sí; lo dicho en personaje llega a {get} metros').format(get=(i.get('rol_metros', 30)))) if p.sv_rol() else tr("no")),
                   ayuda=tr("Si se puede hablar en personaje, contar lo que hace tu personaje y escribir una ficha. Está en En línea, Rol.")),
            Opcion(tr("Radio de los vehículos de otros jugadores: ") + (tr("sí, la de las emisoras del juego") if p.sv_sabe("radio") and i.get("radio_coches") else tr("no")),
                   ayuda=tr("Con sí, cerca del vehículo de otro jugador oyes floja la emisora que lleva puesta. En las opciones del juego puedes dejar de oírla.")),
        ] + ([Opcion(tr("Órdenes de administrador"), ayuda=tr("Escríbelas en el chat general con una barra delante: barra ayuda las dice todas. Por ejemplo, barra jugadores, barra aviso y el texto, "
                                                         "barra expulsar y el nombre, barra vetar y el nombre, barra invitar, barra guardar."))] if sv["admin"] else [])))

    def ops():
        out = [Opcion(lambda: tr('Estás en {nombre_servidor}. Hay {sum} jugadores además de ti').format(nombre_servidor=(sv['nombre_servidor']), sum=(sum(1 for r in p.remotos.values() if not getattr(r, 'ia', False))))
                      + (tr(' y {sum} personajes del servidor').format(sum=(sum(1 for r in p.remotos.values() if getattr(r, 'ia', False)))) if any(getattr(r, 'ia', False) for r in p.remotos.values()) else "")
                      + (tr(". Estás en modo pasivo") if sv["pasivo"] else "") + (tr(". Estás en zona segura") if sv["segura"] else ""),
                      ayuda=tr("Cuántos hay conectados, y si estás en modo pasivo o en zona segura.")),
               Opcion(tr("Quién hay"), quien, ayuda=tr("Dónde está cada uno y todo lo que puedes hacer con él: marcarle en el GPS, escribirle, darle dinero o cosas, invitarle a tu banda o a tu grupo.")),
               Opcion(tr("Mensaje para todos"), lambda: chat(p), ayuda=tr("También con F10 durante el juego.")),
               Opcion(tr("Mensaje para los que están cerca"), lambda: chat(p, "cerca", None, tr("Mensaje para quien esté a menos de ochenta metros")),
                      ayuda=tr("Lo leen solo los jugadores que estén a menos de ochenta metros de ti, en la misma localidad.")),
               Opcion(tr("Rol: hablar en personaje, acciones y tu ficha") if p.sv_rol() else tr("Rol: este servidor no tiene canales de rol"), lambda: rol(p),
                      ayuda=tr("Un canal para hablar como tu personaje, que oye quien está cerca; otro para hablar fuera de personaje, que oye todo el servidor; "
                            "una orden para contar lo que hace tu personaje; y una frase de ficha que los demás pueden leer. Depende de que el servidor los tenga.")),
               Opcion(tr("Repasar los últimos mensajes"), repasar, ayuda=tr("Los últimos mensajes del servidor, del más reciente al más antiguo."))]
        if sv["inv_banda"] or sv["inv_grupo"]:
            out.insert(1, Opcion(tr("Tienes invitaciones pendientes: están en Tu banda y en Grupo de misión"),
                                 ayuda=tr("Alguien te ha invitado a su banda o a su grupo. Entra en esas opciones para aceptar o rechazar.")))
        out += [Opcion(lambda: tr("Tu banda: ") + (sv["banda"]["nombre"] if sv["banda"] else "ninguna"), lambda: banda(p),
                       ayuda=tr("Fundar una banda o, si ya tienes una, su gente, su caja, sus barrios y sus alianzas.")),
                Opcion(tr("Bandas, barrios y guerras del servidor"), lambda: tablon(p),
                       ayuda=tr("Las guerras en marcha o a punto de empezar, todas las bandas y de quién es cada barrio.")),
                Opcion(tr("Casas y negocios: en venta y de quién son"), lambda: en_venta(p),
                       ayuda=tr("En un servidor, cada casa y cada negocio es de un solo jugador. Aquí está lo que queda libre, lo que vende otro jugador a su precio y de quién es lo demás.")),
                Opcion(lambda: tr("Grupo de misión: ") + (tr("sí") if sv["grupo"] is not None else tr("no")), lambda: grupo(p),
                       ayuda=tr("Tu grupo, las invitaciones que tengas, la misión del grupo y cómo funcionan las misiones en grupo."))]
        if sv["info"].get("pvp") and sv["info"].get("pasivo"):
            out.append(Opcion(lambda: tr('Modo pasivo: {v}').format(v=(tr('sí') if sv['pasivo'] else tr('no'))), pasivo,
                              ayuda=tr("En modo pasivo no puedes herir a otros jugadores ni ellos a ti. No se puede cambiar en mitad de una pelea, ni más de una vez cada dos minutos.")))
        out += [Opcion(tr("Actividades en común: carrera y reparto en equipo"), lambda: actividades(p),
                       ayuda=tr("Proponer a los demás jugadores una carrera con apuesta o un reparto en equipo, o apuntarte a la que hayan propuesto.")),
                Opcion(tr("Guardar ahora"), guardar, ayuda=tr("El personaje se guarda solo cada minuto y al salir. Esto lo guarda ya.")),
                Opcion(tr("Datos y reglas de este servidor"), info,
                       ayuda=tr("Lo que ha decidido quien lleva el servidor: combate, zonas seguras, precios de las bandas, tope de ganancias y más.")),
                Opcion(tr("Salir del servidor"), salir, ayuda=tr("Te pregunta antes. Tu personaje se guarda y vuelves al menú principal."))]
        return out
    app.abrir(Menu(app, tr("En línea"), ops, intro=tr("F1 explica cada opción")))
