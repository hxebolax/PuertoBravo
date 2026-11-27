"""Menús de la vida honrada y sus consecuencias: la consulta del móvil, los contratos fijos, los estudios con título,
la dirección de un negocio, los créditos y las obligaciones, los antecedentes y los asuntos pendientes."""
from .i18n import tr
from .honrado import AJ, GRAVEDAD, NIVELES, _n
from .menus import Menu, Opcion
from .cheats import text as cheat_text

NIVEL_TXT = {"apagado": tr("apagado, como en versiones anteriores"), "suave": "suave", "normal": "normal", "exigente": "exigente"}


def _abrir(p, titulo, ops, intro=None):
    m = Menu(p.app, titulo, ops, intro=intro)
    p.app.abrir(m)
    return m


def _en_servidor_txt(p):
    """Qué de todo esto existe en el servidor en el que estás: lo decide él, igual para todos."""
    if not p.en_servidor:
        return ""
    hay = [t for clave, t in (("nominas", tr("los contratos fijos, con la nómina que paga el servidor, y los antecedentes")),
                              ("trato_prestigio", tr("el trato de las tiendas según tu prestigio"))) if p.sv_honrado(clave)]
    if not hay:
        return tr(". En un servidor en línea no cuentan")
    return tr(". En este servidor no cuenta tu nivel: lo decide el servidor, igual para todos. Aquí hay ") + tr(" y ").join(hay)


def _bloqueado(p, que=""):
    """En un servidor en línea no hay casi nada de lo que mueve dinero: lo dice y devuelve verdadero. Los contratos fijos
    («contrato») sí, donde el servidor paga las nóminas."""
    if p.hon_bloqueo(que):
        p.app.son("error")
        p.app.decir(p.hon_bloqueo(que), True)
        return True
    return False


# ====================================================================== el móvil: cómo te ven
def menu_vida(p):
    """Un solo sitio para saber cómo te ve la ciudad, cómo te ve la calle y qué ganas o pierdes por ello."""
    app, j = p.app, p.j
    h = p.hon()

    def ops():
        lista = [Opcion(p.hon_ciudad_txt, ayuda=tr("El prestigio entre los vecinos sube con el trabajo honrado, los estudios, los donativos, el voluntariado y las buenas acciones. Baja con los delitos que te ven cometer y con las detenciones.")),
                 Opcion(p.hon_calle_txt, ayuda=tr("La fama en la calle sube con las misiones, los contratos y los barrios que conquistas. Es independiente del prestigio: puedes tener las dos cosas, una o ninguna.")),
                 Opcion(lambda: tr("Antecedentes penales. ") + p.hon_antecedentes_txt(), lambda: menu_antecedentes(p),
                        ayuda=tr("Las condenas que constan en tu ficha, cuándo caducan y cómo atenuarlas. Cierran empleos de confianza, créditos y el ingreso en la policía.")),
                 Opcion(lambda: tr("Trabajo. ") + p.hon_contrato_txt(), lambda: menu_contrato(p),
                        ayuda=tr("Tu contrato fijo, si lo tienes: jefe, turnos del periodo, nómina y avisos. Los contratos se firman en las oficinas de empleo.")),
                 Opcion(lambda: tr("Estudios. ") + estudios_txt(p), lambda: menu_estudios(p, None),
                        ayuda=tr("Los títulos que tienes y los que estás sacando. Se estudian en las academias, una sesión al día, y abren puestos mejores y mejoras para tus negocios.")),
                 Opcion(lambda: tr("Negocios. ") + negocios_txt(p), lambda: menu_negocios(p), ayuda=tr("Tus negocios: nivel, empleados, nombre entre la clientela y lo que dan. Se dirigen yendo a cada uno.")),
                 Opcion(lambda: tr("Banco y obligaciones. ") + banco_txt(p), lambda: menu_banco(p, None),
                        ayuda=tr("Tus créditos e hipotecas, lo que te van a cobrar de facturas e impuestos y cuándo. Todo se cobra solo, con aviso dos días antes.")),
                 Opcion(p.hon_doble_txt, ayuda=tr("Si llevas las dos vidas a la vez, lo que se va sabiendo de ti. Sube cuando te ven delinquir, te detienen o una inspección te encuentra algo; baja con los días tranquilos.")),
                 Opcion(lambda: tr('Asuntos pendientes: {len}').format(len=(len(h['asuntos']))) + (". " + p.hon_asunto_txt(h["asuntos"][0]) if h["asuntos"] else ""), lambda: menu_asuntos(p),
                        ayuda=tr("Lo que espera una decisión tuya: una inspección con problemas, un periodista o una banda que pide dinero. Si se acaba el plazo, se resuelve solo.")),
                 Opcion(p.hon_trama_txt, lambda: _marcar_trama(p), ayuda=tr("La historia de prosperar honradamente en Puerto Bravo. Intro marca en el GPS dónde sigue, si ya cumples lo que pide."))]
        if h["fiado"]:
            lista.append(Opcion(lambda: tr('Pagar lo que debes de fiado en las tiendas: {fiado} euros').format(fiado=(h['fiado'])), p.hon_pagar_fiado, ayuda=tr("Si no lo pagas tú, se cobra solo con las facturas del periodo.")))
        if h["embargo"]:
            lista.append(Opcion(lambda: tr('Estás embargad[o|a]: debes {int} euros. Se quedan la mitad de tus nóminas y de lo que dan tus negocios').format(int=(int(h['embargo']))), lambda: _saldar_embargo(p),
                                ayuda=tr("Intro salda la deuda de una vez con lo que tengas entre la cuenta y el bolsillo. Si no te llega, el embargo sigue.")))
        if p.hon_nivel():
            lista.append(Opcion(lambda: (tr("Tu abogado: lo tienes contratado") if p.hon_abogado() else tr('Contratar a un abogado: {entero} euros a la semana').format(entero=(AJ.entero('abogado_semana')))), p.hon_contratar_abogado,
                                ayuda=tr("Mientras le pagues, lo que se sepa de tu otra vida hace la mitad de daño, frena a la prensa y puede recurrir las sanciones de una inspección. Se renueva solo cada semana; Intro otra vez lo despide.")))
        lista.append(Opcion(lambda: tr('Nivel de consecuencias: {get}').format(get=(NIVEL_TXT.get(p.cfg['consecuencias'], 'suave'))) + _en_servidor_txt(p),
                            ayuda=tr("Se cambia en Opciones, en Vida, reputación y consecuencias. Apagado deja el juego como en versiones anteriores; suave es lo de serie.")))
        return lista
    _abrir(p, tr("Vida, reputación y consecuencias"), ops, tr("Cómo te ve la ciudad, cómo te ve la calle y qué estás ganando o perdiendo por ello"))


def _marcar_trama(p):
    m, faltas, n, total = p.hon_trama()
    if m is None or faltas:
        return p.app.decir(p.hon_trama_txt(), True)
    while p.app.pila and p.app.pila[-1] is not p:
        p.app.cerrar(p.app.pila[-1])
    p.gps_a_lugar(p.lugares[m["lugar"]])


def _saldar_embargo(p):
    h = p.hon()
    total = int(h["embargo"])
    if total > p.j.dinero + p.j.banco:
        p.app.son("error")
        return p.app.decir(tr('Para saldar la deuda de una vez hacen falta {total} euros entre la cuenta y el bolsillo.').format(total=(total)), True)
    p.hon_cobrar_de_cuentas(total)
    h["embargo"] = 0
    p.hon_decir(AJ.frase("frases_embargo_fin"), "prestigio")


# ====================================================================== antecedentes
def menu_antecedentes(p, lugar=None):
    """La ficha: qué consta, cuándo caduca y cómo atenuarlo. En comisaría o desde el móvil."""
    app = p.app

    def ops():
        vivos = p.hon_antecedentes()
        lista = [Opcion(p.hon_antecedentes_txt, ayuda=tr("Cada detención y cada multa que pagas a un agente queda apuntada, más grave cuanto más te buscaban. Caducan solas con el tiempo."))]
        for a in vivos:
            lista.append(Opcion(p.hon_antecedente_txt(a) + tr('. Recurrirla con un abogado cuesta {hon_abogado_precio} euros').format(hon_abogado_precio=(p.hon_abogado_precio(a))), (lambda a=a: (p.hon_rebajar(a), m.refrescar(False))),
                                ayuda=tr("Intro paga a un abogado para que la recurra: baja un grado, o desaparece si era leve. Solo una vez por antecedente.")))
        if vivos:
            lista.append(Opcion(tr('Hacer servicios a la comunidad: {entero} horas').format(entero=(AJ.entero('servicio_horas'))), lambda: (p.hon_servicio_comunidad(), m.refrescar(False)),
                                ayuda=tr('Sin cobrar. Le quita {entero} días al antecedente más grave y los vecinos lo ven con buenos ojos. Una vez al día.').format(entero=(AJ.entero('servicio_quita')))))
            lista.append(Opcion(tr("Qué te cierran: ") + cierres_txt(p),
                                ayuda=tr("Mientras tengas antecedentes vivos, esto queda fuera de tu alcance. Cuando caducan o los recurres, se vuelve a abrir.")))
        elif p.hon_con_antecedentes():
            lista.append(Opcion(tr('Plazos: una falta leve caduca a los {entero} días, una media a los {entero2} y una grave a los {entero3}').format(entero=(AJ.entero('caduca_leve')), entero2=(AJ.entero('caduca_media')), entero3=(AJ.entero('caduca_grave'))),
                                ayuda=tr("Ahora tu ficha está limpia. Si te detienen, la falta es más grave cuanto más te buscaban, y se borra sola pasado su plazo.")))
        return lista
    m = _abrir(p, tr("Antecedentes penales"), ops)


def cierres_txt(p):
    cosas = [tr("los empleos de confianza")]
    if p.hon_graves():
        cosas += [tr("los créditos y las hipotecas")]
    cosas.append(tr("el ingreso en la policía"))
    return ", ".join(cosas[:-1]) + tr(" y ") + cosas[-1] + tr(". Además, la policía te tiene fichad[o|a] y cada delito cuenta algo más.")


# ====================================================================== trabajo: contratos fijos
def menu_contrato(p):
    j = p.j

    def dimitir():
        def si():
            p.app.cerrar(c)
            p.hon_dimitir()
            m.refrescar(False)
        c = Menu(p.app, tr("¿Dejas tu puesto?"), [Opcion(tr("Sí, presentar la dimisión"), si, ayuda=tr('Si llevas {entero} periodos o más y ningún aviso, te llevas una carta de recomendación.').format(entero=(AJ.entero('carta_periodos')))),
                                              Opcion(tr("No, me quedo"), lambda: p.app.cerrar(c))])
        p.app.abrir(c)

    def ops():
        ct = j.contrato
        lista = [Opcion(p.hon_contrato_txt, ayuda=tr('Con contrato, al acabar cada periodo te evalúan por los turnos cumplidos y por cómo los has hecho, y cobras la nómina según la nota. Con {entero} avisos te despiden.').format(entero=(AJ.entero('avisos_despido'))))]
        if not ct:
            return lista + [Opcion(tr("Los contratos fijos se firman en las oficinas de empleo. Sin contrato, trabajas cuando quieres, como siempre"),
                                   ayuda=tr("En la oficina de empleo eliges la empresa y ves sus puestos, lo que pagan y lo que piden."))]
        c = p.hon_empleo()
        k = int(ct["puesto"])
        if c:
            lista.append(Opcion(tr("Cuentan como turno: ") + cuenta_txt(p, c), ayuda=tr("Una jornada es un turno. Con vehículo, tres servicios hacen un turno.")))
            lista.append(Opcion(tr('Tu jef[e|a], {jefe}, es {caracter}. Evaluaciones buenas que llevas para el ascenso: {meritos} de {entero}').format(jefe=(ct['jefe']), caracter=(ct['caracter']), meritos=(ct['meritos']), entero=(AJ.entero('meritos_ascenso')))
                                + (tr('. Última nota: {nota} de 100').format(nota=(ct['nota'])) if "nota" in ct else ""),
                                ayuda=tr("Con suficientes evaluaciones buenas asciendes, si cumples lo que pide el puesto. Con un jefe exigente cuesta más sacar buena nota, y con uno paciente, menos.")))
            if k + 1 < len(c["puestos"]):
                sig = c["puestos"][k + 1]
                falta = p.hon_puesto_falta(sig)
                lista.append(Opcion(tr('Siguiente puesto: {nombre}, {int} euros de nómina').format(nombre=(sig['nombre']), int=(int(_n(sig, 'sueldo')))) + (tr('. Te falta {falta}').format(falta=(falta)) if falta else tr(". Cumples lo que pide")),
                                    ayuda=tr("El puesto al que subes con las evaluaciones buenas. Si pide un título o más prestigio, no asciendes hasta tenerlo.")))
            lista += opciones_ir_a_trabajar(p, c)
        lista.append(Opcion(tr("Presentar la dimisión"), dimitir,
                            ayuda=tr("Te pregunta antes. Al dejarlo te quedas sin contrato y vuelves a trabajar por tu cuenta, cuando quieras.")))
        return lista
    m = _abrir(p, tr("Tu trabajo"), ops)


def opciones_ir_a_trabajar(p, c):
    """Una opción por cada cosa que cuenta como turno: marca en el GPS dónde hacerla. Las jornadas, en la oficina de
    empleo más cercana; los oficios con vehículo, donde hay uno aparcado."""
    from .menus_vida import DONDE
    from .trabajos import NOMBRE_TRABAJO
    jornadas = {x["id"]: x["nombre"].lower() for x in p.datos.get("jornadas", [])}

    def ir(lugar, frase):
        app = p.app
        while len(app.pila) > 1 and app.pila[-1] is not p:
            app.pila.pop()
        app.teclas.clear()
        p.salir_interior()
        p.gps_a_lugar(lugar)
        p.decir(frase)

    def oficina():
        x, y = p.pos()
        ls = [l for l in p.mundo.lugares.values() if l.tipo == "empleo"]
        if not ls:
            p.app.son("error")
            p.app.decir(tr("En esta localidad no hay oficina de empleo. Las jornadas se hacen en la de otra localidad."), True)
            return
        l = min(ls, key=lambda l: (l.x - x) ** 2 + (l.y - y) ** 2)
        ir(l, tr('Destino: {nombre}. Allí, en el menú de la oficina, eliges la jornada y cuenta como turno.').format(nombre=l.nombre))

    def oficio(tipo):
        def f():
            if tipo == "mensajeria":
                p.app.decir(tr("Para la mensajería del mar, zarpa en cualquier barco desde un embarcadero y pulsa J."), True)
                return
            donde = p.vehiculo_de_trabajo_cercano(tipo)
            if donde is None:
                p.app.son("error")
                p.app.decir(tr('En esta localidad no hay ningún sitio fijo donde encontrar {v}.').format(v=DONDE.get(tipo, tipo)), True)
                return
            ir(donde, tr('Hay {v} aparcado junto a {nombre}. Sube con F y pulsa J para empezar a trabajar.').format(v=DONDE.get(tipo, tipo), nombre=donde.nombre))
        return f
    ops = []
    if any(cl.startswith("jornada:") for cl in c.get("cuenta") or []):
        nombres = ", ".join(jornadas.get(cl.partition(":")[2], cl.partition(":")[2]) for cl in c["cuenta"] if cl.startswith("jornada:"))
        ops.append(Opcion(tr('Ir a hacer un turno: {nombres}, en la oficina de empleo').format(nombres=nombres), oficina,
                          ayuda=tr("Marca en el GPS la oficina de empleo más cercana. Allí eliges la jornada, y cuenta como turno de tu contrato.")))
    for cl in c.get("cuenta") or []:
        tipo, _, ident = cl.partition(":")
        if tipo == "oficio":
            ops.append(Opcion(tr('Ir a hacer un turno de {nombre}').format(nombre=NOMBRE_TRABAJO.get(ident, ident)), oficio(ident),
                              ayuda=tr("Marca en el GPS dónde hay aparcado un vehículo de ese oficio. Tres servicios hacen un turno.")))
    return ops


def cuenta_txt(p, c):
    from .trabajos import NOMBRE_TRABAJO
    jornadas = {x["id"]: x["nombre"].lower() for x in p.datos.get("jornadas", [])}
    partes = []
    for clave in c.get("cuenta") or []:
        tipo, _, ident = clave.partition(":")
        partes.append(jornadas.get(ident, ident) if tipo == "jornada" else tr('servicios de {get}').format(get=(NOMBRE_TRABAJO.get(ident, ident))))
    return ", ".join(partes) or "nada"


def menu_empleos(p, l):
    """En la oficina de empleo: los contratos fijos."""
    if _bloqueado(p, "contrato"):
        return
    j = p.j

    def ficha(c):
        def ops():
            lista = [Opcion(tr('{nombre}, en {empresa}. {get}').format(nombre=(c['nombre']), empresa=(c['empresa']), get=(c.get('desc', ''))),
                            ayuda=tr("Debajo están los puestos, de menos a más, con lo que pide y paga cada uno. Se empieza siempre por el primero.")),
                     Opcion(tr("Cuentan como turno: ") + cuenta_txt(p, c), ayuda=tr("Una jornada es un turno. Con vehículo, tres servicios hacen un turno."))]
            for k, pu in enumerate(c["puestos"]):
                pide = tr(" y ").join(x for x in ((tr('título de {hon_titulo_nombre}').format(hon_titulo_nombre=(p.hon_titulo_nombre(pu['titulo']))) if pu.get("titulo") else ""), (tr('prestigio {int}').format(int=(int(_n(pu, 'prestigio')))) if _n(pu, "prestigio") else "")) if x)
                lista.append(Opcion(tr('Puesto {v}: {nombre}. {int} turnos por periodo, {int2} euros de nómina').format(v=(k + 1), nombre=(pu['nombre']), int=(int(_n(pu, 'cupo', 3))), int2=(int(_n(pu, 'sueldo')))) + (tr('. Pide {pide}').format(pide=(pide)) if pide else "")
                                    + (tr(". Con decisiones de responsabilidad") if pu.get("mando") else ""),
                                    ayuda=tr("A este puesto se llega ascendiendo con evaluaciones buenas. En los de responsabilidad, a veces un turno trae una decisión que cuenta en la evaluación.")))
            motivo = p.hon_firma_motivo(c)
            lista.append(Opcion(tr("Firmar el contrato") + (tr('. Ahora no puedes: {motivo}').format(motivo=(motivo)) if motivo else ""), lambda: p.hon_firmar(c) and (p.app.cerrar(mf), m.refrescar(False)),
                                ayuda=tr('Te comprometes a un número de turnos cada {entero} días. Cobras cada turno como siempre y, al acabar el periodo, la nómina según tu evaluación. Faltar o hacerlo mal trae avisos, y con {entero2} avisos te despiden.').format(entero=(AJ.entero('periodo_dias')), entero2=(AJ.entero('avisos_despido')))))
            return lista
        mf = _abrir(p, c["nombre"], ops)

    def ops():
        lista = [Opcion(lambda: tr("Tu situación: ") + p.hon_contrato_txt(), lambda: menu_contrato(p),
                        ayuda=tr("Intro abre tu trabajo: el contrato que tienes, tu jefe, el siguiente puesto y la dimisión."))]
        for c in p.hon_empleos():
            pu = c["puestos"][0]
            lista.append(Opcion(tr('{nombre}, en {empresa}: empiezas de {nombre2}, con {int} euros de nómina por periodo').format(nombre=(c['nombre']), empresa=(c['empresa']), nombre2=(pu['nombre']), int=(int(_n(pu, 'sueldo')))) + (tr(". Empleo de confianza") if c.get("confianza") else ""),
                                (lambda c=c: ficha(c)), ayuda=c.get("desc")))
        return lista
    m = _abrir(p, tr("Contratos fijos"), ops, tr("Con un contrato tienes jefe, turnos que cumplir, nómina, evaluaciones y ascensos. Sin contrato, todo sigue como siempre")
               + (tr(". En este servidor los turnos los cuenta el servidor y la nómina la paga él, con su calendario") if p.en_servidor else ""))


# ====================================================================== estudios
def estudios_txt(p):
    tengo = [p.hon_titulo_nombre(k) for k in p.hon_titulos()]
    cursando = [tr('{hon_titulo_nombre}, {get} sesiones').format(hon_titulo_nombre=(p.hon_titulo_nombre(k)), get=(v.get('s', 0))) for k, v in p.j.titulos.items() if isinstance(v, dict) and not v.get("ok") and p.hon_titulo(k)]
    t = (tr("Tienes: ") + ", ".join(tengo)) if tengo else tr("No tienes ningún título")
    return t + (tr(". Estás sacando: ") + "; ".join(cursando) if cursando else "")


def menu_estudios(p, l):
    """En una academia (o desde el móvil, solo para consultar): los títulos."""
    j = p.j

    def ops():
        lista = [Opcion(lambda: estudios_txt(p), ayuda=tr("Los títulos que ya tienes son tuyos para siempre. Los que estás sacando se terminan sesión a sesión, una al día."))]
        for t in p.datos.get("titulos", []):
            e = j.titulos.get(t["id"], {})
            total = int(_n(t, "sesiones", 4))
            if e.get("ok"):
                estado = tr("ya lo tienes")
            else:
                estado = tr('llevas {int} de {total} sesiones; cada una, {int2} euros y {int3} horas').format(int=(int(e.get('s', 0))), total=(total), int2=(int(_n(t, 'precio'))), int3=(int(_n(t, 'horas', 3))))
            pide = tr(" y ").join(x for x in ((tr('el título de {hon_titulo_nombre}').format(hon_titulo_nombre=(p.hon_titulo_nombre(t['requiere']))) if t.get("requiere") else ""), (tr('prestigio {int}').format(int=(int(_n(t, 'prestigio')))) if _n(t, "prestigio") else "")) if x)
            texto = f"{t['nombre']}: {estado}" + (tr('. Pide {pide}').format(pide=(pide)) if pide and not e.get("ok") else "")
            accion = (lambda t=t: (p.hon_estudiar(t), m.refrescar(False))) if l is not None else (lambda: p.app.decir(tr("Las clases se dan en las academias: ve a una."), True))
            lista.append(Opcion(texto, accion, ayuda=(f"{t.get('desc', '')} {t.get('abre', '')} " + tr("Una sesión al día; se puede estudiar y trabajar el mismo día.")).strip()))
        return lista
    m = _abrir(p, tr("Estudios con título") if l is not None else tr("Tus estudios"), ops, tr("Cada título lleva varias sesiones, una al día. Al completarlas, es tuyo para siempre") if l is not None else None)


# ====================================================================== la empresa
def negocios_txt(p):
    negocios = p.negocios_tuyos()
    if not negocios:
        return tr("No tienes ninguno. Se compran yendo a ellos, al contado o con hipoteca")
    return tr('Tienes {len}, que dan {sum} euros al día').format(len=(len(negocios)), sum=(sum(p.ingreso_negocio(l) for l in negocios)))


def menu_negocios(p):
    negocios = p.negocios_tuyos()
    ops = [Opcion(lambda l=l: f"{p.nombre_lugar(l)}. {p.hon_negocio_txt(l)}", (lambda l=l: (p.app.cerrar(m), p.gps_a_lugar(l)) if l.mapa == p.mundo.id else p.app.decir(tr("Está en otra localidad."), True)),
                  ayuda=tr("Intro lo marca en el GPS. Un negocio se dirige yendo a él.")) for l in negocios]
    m = _abrir(p, tr("Tus negocios"), ops or [Opcion(tr("No tienes negocios"), ayuda=tr("Se compran yendo a ellos, al contado o con hipoteca. Cuando tengas alguno, aparecerá aquí."))])


def opciones_negocio(p, l, refrescar):
    """Las opciones de dirección de un negocio tuyo, para su menú."""
    if p.en_servidor:
        return []
    e = p.hon_emp(l)
    p.hon_visitar(l)

    def mejora_txt():
        mj = p.hon_mejora(int(e["nivel"]) + 1)
        if not mj:
            return tr("Mejoras: el negocio ya está en su nivel más alto")
        motivo = p.hon_mejora_motivo(l)
        return tr('Mejorar: {nombre}, por {hon_mejora_coste} euros. Sube lo que da un {int} por ciento sobre la base y admite un empleado más').format(nombre=tr(mj['nombre']), hon_mejora_coste=(p.hon_mejora_coste(l, mj)), int=(int(_n(mj, 'ingresos')))) + (f". {motivo}" if motivo else "")

    def hacer(f, *a):
        return lambda: (f(l, *a), refrescar())
    ops = [Opcion(lambda: tr("Dirección. ") + p.hon_negocio_txt(l), ayuda=tr("Un negocio atendido rinde más y uno abandonado, menos. Su nombre entre la clientela sube si pasas por aquí, si echas horas y con precios bajos.")),
           Opcion(tr('Echar {entero} horas en el negocio').format(entero=(AJ.entero('atender_horas'))), hacer(p.hon_atender), ayuda=tr("Atiendes tú: sube el nombre del negocio. Una vez al día en cada negocio.")),
           Opcion(mejora_txt, hacer(p.hon_mejorar), ayuda=(cheat_text(
               "Cada nivel hace que el negocio dé más y admita más gente. Con el truco activado, ningún negocio pide prestigio para mejorar. Los títulos y el coste siguen siendo necesarios.",
               "Each level increases income and staff capacity. With this cheat enabled, all business upgrades ignore prestige. Qualifications and the normal cost still apply.")
               if p.cheat_on("cheat_negocios") else tr("Cada nivel hace que el negocio dé más y admita más gente. Los niveles altos piden un título de gestión y buen prestigio."))),
           Opcion(lambda: tr('Contratar a un empleado. Tienes {emp} de {hon_max_empleados}').format(emp=(e['emp']), hon_max_empleados=(p.hon_max_empleados(e))), hacer(p.hon_empleado, 1),
                  ayuda=tr('Cada empleado cobra al día un {entero} por ciento de lo que da el negocio de base y hace que dé un {entero2} por ciento más. Con gente contratada, el negocio aguanta aunque tú no pases.').format(entero=(AJ.entero('empleado_sueldo')), entero2=(AJ.entero('empleado_rinde')))),
           Opcion(tr("Despedir a un empleado"), hacer(p.hon_empleado, -1),
                  ayuda=tr("Te ahorras su sueldo, pero el negocio da menos. Si te quedas sin nadie, el horario ampliado vuelve a ser normal.")),
           Opcion(lambda: (tr('Encargado: sí. Cobra {sueldo} euros al día') if e.get("encargado") else tr('Encargado: no. Contratarlo cuesta {sueldo} euros al día')).format(sueldo=(int(int(l.get("ingresos", 0)) * AJ("encargado_sueldo") / 100.0))),
                  hacer(p.hon_encargado),
                  ayuda=tr('Intro lo contrata o lo despide. El encargado lleva el negocio por ti: no hace falta que pases ni que eches horas, nunca se da por abandonado y su nombre sube solo hasta un {entero} sobre 100. Cobra al día un {entero2} por ciento de lo que da el negocio de base. Cómo va cada negocio lo ves en el móvil, en Vida, reputación y consecuencias, Negocios.').format(entero=(AJ.entero('encargado_tope')), entero2=(AJ.entero('encargado_sueldo')))),
           Opcion(lambda: tr('Precios: {precios}').format(precios=(e['precios'])), hacer(p.hon_precios), ayuda=tr("Intro cambia entre bajos, normales y altos. Bajos: ganas menos y sube el nombre. Altos: ganas más y baja.")),
           Opcion(lambda: tr('Horario: {horario}').format(horario=(e['horario'])), hacer(p.hon_horario), ayuda=tr('Con horario ampliado da un {entero} por ciento más, pero necesitas al menos un empleado.').format(entero=(AJ.entero('horario_ingreso'))))]
    if p.hon_nivel():
        ops.append(Opcion(lambda: tr("Tapadera: ") + (tr("sí, blanquea tu dinero sin justificar") if e["tapadera"] else tr("no, es un negocio limpio")), hacer(p.hon_tapadera),
                          ayuda=tr("Para quien lleva doble vida. Cada medianoche pasa por la caja parte del dinero que no podrías justificar, a cambio de una comisión. "
                                "Si una inspección lo encuentra: sanción, y si intentas sobornar y sale mal, antecedentes y portada en el periódico.")))
    return ops


def opcion_hipoteca(p, l, al_comprar):
    """La opción de comprar una casa o un negocio con hipoteca, para su menú de compra."""
    if p.en_servidor or int(l.get("precio", 0)) <= 0:
        return []

    def comprar():
        if p.hon_hipoteca(l):
            if l.tipo == "negocio":
                p.hon_emp(l)
            al_comprar()

    def texto():
        entrada, cuota, n = p.hon_hipoteca_datos(l)
        motivo = p.hon_credito_motivo("hipoteca")
        return tr('Comprar con hipoteca: {entrada} euros de entrada y {n} cuotas de {cuota}').format(entrada=(entrada), n=(n), cuota=(cuota)) + (tr(". Ahora no te la dan") if motivo else "")
    return [Opcion(texto, comprar, ayuda=tr('El banco pone el resto y lo devuelves en cuotas, una cada {entero} días, con aviso antes de cada una. Hace falta buena solvencia: prestigio, una nómina o un negocio, y nada de antecedentes graves.').format(entero=(AJ.entero('cuota_dias'))))]


# ====================================================================== banco y obligaciones
def banco_txt(p):
    j, h = p.j, p.hon()
    partes = []
    if j.creditos:
        partes.append(tr('{len} {v} en marcha').format(len=(len(j.creditos)), v=(tr('crédito') if len(j.creditos) == 1 else tr('créditos'))))
    partes.append(p.hon_cobro_txt().rstrip("."))
    if h["embargo"]:
        partes.append(tr('embargo de {int} euros').format(int=(int(h['embargo']))))
    return ". ".join(partes)


def menu_banco(p, l):
    """Créditos, hipotecas y lo que hay que pagar. En un banco se piden; desde el móvil, solo se consulta y se liquida."""
    j = p.j

    def pedir(n):
        return lambda: (p.hon_pedir_credito(n), m.refrescar(False))

    def ops():
        lista = [Opcion(lambda: tr('Tu solvencia para el banco es {hon_solvencia_txt}. Ingresos estables: {hon_ingresos_semana} euros por semana').format(hon_solvencia_txt=(p.hon_solvencia_txt()), hon_ingresos_semana=(p.hon_ingresos_semana())),
                        ayuda=tr("Sube con el prestigio entre los vecinos, con una nómina, con negocios y con créditos devueltos. Baja con antecedentes, impagos y embargos.")),
                 Opcion(p.hon_cobro_txt, ayuda=tr('Cada {entero} días se cobran la luz y el agua de tus casas, su contribución y el impuesto de lo que han dado tus negocios. Se cobra solo, primero del banco. Si no llega, queda a deber con recargo; a los tres impagos, embargo.').format(entero=(AJ.entero('cobro_dias'))))]
        for c in j.creditos:
            lista.append(Opcion((lambda c=c: p.hon_credito_txt(c) + tr('. Liquidarlo ahora cuesta {int} euros').format(int=(int(c['cuota'] * c['quedan'] * 0.95 + c.get('atraso', 0))))),
                                (lambda c=c: (p.hon_liquidar(c), m.refrescar(False))), ayuda=tr("Intro paga de una vez lo que queda, con un cinco por ciento de rebaja.")))
        if l is not None and not p.hon_bloqueo():
            motivo = p.hon_credito_motivo()
            if motivo:
                lista.append(Opcion(tr("Crédito personal: ") + motivo, ayuda=tr("Por eso ahora el banco no te presta. Cuando se arregle, aquí aparecen los créditos que te ofrece.")))
            else:
                maximo = p.hon_credito_maximo()
                interes, n = int(p.hon_interes()), AJ.entero("credito_cuotas")
                for importe in sorted({maximo // 4 // 100 * 100, maximo // 2 // 100 * 100, maximo}):
                    if importe >= 300:
                        cuota = int(importe * (1.0 + interes / 100.0) / n) + 1
                        lista.append(Opcion(tr('Pedir un crédito de {importe} euros: {n} cuotas de {cuota}').format(importe=(importe), n=(n), cuota=(cuota)), pedir(importe),
                                            ayuda=tr('Interés del {interes} por ciento, según tu solvencia. Una cuota cada {entero} días, que se cobra sola.').format(interes=(interes), entero=(AJ.entero('cuota_dias')))))
            lista.append(Opcion(tr("Las hipotecas se piden al comprar: ve a la casa o al negocio que quieras y elige comprar con hipoteca"),
                                ayuda=tr("Pagas una entrada y el resto en cuotas. Hace falta buena solvencia y nada de antecedentes graves.")))
        elif l is None:
            lista.append(Opcion(tr("Los créditos se piden en un banco"),
                                ayuda=tr("Desde el móvil solo se consultan y se liquidan. Para pedir uno, entra en cualquier banco y elige Créditos, hipotecas y obligaciones.")))
        return lista
    m = _abrir(p, tr("Créditos, hipotecas y obligaciones"), ops)


# ====================================================================== asuntos pendientes
def menu_asuntos(p):
    h = p.hon()

    def abrir(a):
        def hacer(clave):
            def f():
                p.app.cerrar(ma)
                p.hon_resolver(a, clave)
                m.refrescar(False)
            return f
        ma = _abrir(p, p.hon_asunto_txt(a), [Opcion(texto, hacer(clave), ayuda=ayuda) for clave, texto, ayuda in p.hon_asunto_opciones(a)], tr("F1 explica cada salida"))

    def ops():
        return [Opcion(p.hon_asunto_txt(a), (lambda a=a: abrir(a)), ayuda=tr("Intro para decidir qué haces.")) for a in h["asuntos"]] or [Opcion(tr("No tienes ningún asunto pendiente"),
                                                                                                                   ayuda=tr("Aquí aparecen las decisiones que te esperan, como una inspección con problemas, un periodista o una banda que pide dinero."))]
    m = _abrir(p, tr("Asuntos pendientes"), ops)


__all__ = ["menu_vida", "menu_antecedentes", "menu_contrato", "menu_empleos", "menu_estudios", "menu_negocios", "opciones_negocio", "opcion_hipoteca", "menu_banco", "menu_asuntos",
           "GRAVEDAD", "NIVELES"]
