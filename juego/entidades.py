"""Entidades del mundo: jugador, vehículos, personas y objetos."""
from .i18n import tr
import math
import random


class Jugador:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.rumbo = 0.0
        self.salud = 100.0
        self.salud_max = 100.0
        self.mapa = "puerto_bravo"
        self.banco = 0
        self.barcos = []            # [{"modelo", "salud", "nombre", "en": id del embarcadero}]
        self.barco_actual = None    # barco con el que has zarpado (None si es alquilado o robado)
        self.pescado = []           # [{"nombre", "valor"}]
        self.loteria = 0            # de las partidas antiguas: ya no se usa
        self.boletos = []           # lotería: [{"n": "04712", "sorteo": día, "donde": lugar}]
        self.lot_bote = 20000       # el bote del próximo sorteo
        self.lot_ultimo = -1        # último sorteo celebrado; -1, todavía sin poner en hora
        self.lot_botes = {}         # el bote que había en cada sorteo reciente, para pagar a quien lo acierte
        self.ropa = tr("ropa de calle")
        self.calzado = tr("zapatillas de calle")
        self.vestuario = {}              # lo que tienes: {"prendas", "calzado", "complementos"} (vestuario.py)
        self.walkman = False             # llevas el reproductor encendido: la radio suena también a pie
        self.accesorios = {}             # complementos que llevas: clase (gafas, cadena...) -> nombre
        self.guardaespaldas = 0
        self.hab = {"conduccion": 0.0, "punteria": 0.0, "resistencia": 0.0, "pesca": 0.0}
        self.logros = []
        self.marcadores = []
        self.perro = ""
        self.perro_hambre = 0.0      # de 0, recién comido, a 100
        self.perro_confianza = 100.0  # de 0 a 100: baja si le haces daño o pasa hambre
        self.perro_en_casa = False
        self.cobro_negocios = "mano"  # mano: te lo traen cada medianoche; banco: te lo ingresan; recoger: se queda en la caja y vas tú
        self.cajas = {}              # lo que espera en la caja de cada negocio cuando cobras yendo tú
        self.animo = 55.0
        self.personaje = "dani"
        self.nombre = tr("Dani")
        self.apellido = tr("Roca")
        self.genero = "h"            # cómo le hablan: "h" en masculino, "m" en femenino
        self.muebles = {}            # lo que has puesto en cada casa tuya: {id de la casa: [muebles]}
        self.voz = "dani"            # un personaje propio: con cuál de las voces de protagonista habla en las escenas
        self.nombre_dicho = ""       # y cómo se pronuncia su nombre, si no es como se escribe
        self.ciudadania = 20.0
        self.jornada_dia = 0
        self.curso_dia = 0
        self.voluntario_dia = 0
        self.reputacion = 0.0
        self.relaciones = {}
        self.turnos_escena = {}
        self.ocultos_social = []     # personas de la vida social que has quitado del móvil: no salen hasta que las recuperes
        self.conocidos = []          # gente de la calle que te ha dado su número
        self.intimos = {}            # artículos íntimos (contenido para adultos): preservativos, velas...
        self.its = 0                 # día en que te contagiaste, o 0
        self.semilla = 0             # la suerte propia de esta partida: precios y cómo viene cada día
        self.hambre = 0.0            # vida realista: de 0 a 100
        self.sueno = 0.0
        self.sed = 0.0
        self.suciedad = 0.0          # de 0, recién duchado, a 100
        self.carne_puntos = 12       # puntos del carné de conducir; con 0, retirado
        self.cargos_helicoptero = 0  # helicópteros de la policía que has derribado y aún no has pagado
        self.pareja = ""
        self.sustancias = {}
        self.efectos = []
        self.adiccion = {}
        self.ultima_dosis = {}
        self.territorios = []
        self.barrios_banda = {}      # barrios que una banda te ha quitado: {barrio: banda}
        self.banda = 0               # cuánta gente tienes en tu banda
        self.banda_nombre = ""
        self.alias = ""
        self.cajero_ingresos = [0, 0]   # [día, euros] ingresados hoy en los cajeros: tienen tope al día             # tu mote en la calle como jefe de banda; vacío, te llaman por tu nombre
        self.laboratorios = []       # casas tuyas con laboratorio (contenido para adultos)
        self.material = 0            # tandas de material de laboratorio que te quedan
        self.ciclo = 0               # cuántas veces has vuelto a empezar conservando lo ganado
        self.amenaza = None          # una banda rival ataca un territorio tuyo: {"territorio", "banda", "dia"}
        self.oferta_pacto = None     # una banda te ofrece un pacto: {"banda", "precio", "dia"}
        self.pacto_hasta = 0         # día hasta el que dura el pacto
        self.redada = None           # la policía te aprieta: {"precio", "dia"}
        self.rep_bandas = {}         # cómo te llevas con cada banda: de -100 a 100
        self.foco = 100.0            # medidor del tiempo lento
        self.dia_nevera = -1         # último día que comiste de la nevera de casa
        self.acciones = {}
        self.coste_acciones = {}     # lo que te han costado las acciones que tienes de cada empresa (bolsa.py)
        self.bolsa_ayer = {}         # los precios de ayer, para saber cuánto han cambiado
        self.bolsa_noticias = []     # las últimas noticias de la bolsa
        self.bolsa = {}
        self.gimnasio_dia = 0
        self.blindaje = 0.0
        self.dinero = 50
        self.armas = {"punos": {"cargador": 0, "reserva": 0}}
        self.arma = "punos"
        self.objetos = {"botiquin": 1, "ganzua": 0}
        self.puntos_busqueda = 0.0
        self.estrellas = 0
        self.veh = None
        self.agachado = False
        self.t_ataque = 0.0
        self.propiedades = ["casa_abuela"]
        self.garajes = {}
        self.casetes = []
        self.visitados = []
        self.barrios_vistos = []
        self.recordado = []          # recordatorios que el juego ya te ha dado una vez (disparar desde el vehículo...)
        self.pedido = None           # comida a domicilio en camino: {"casa", "cosas", "llega", "estado", "local", "nombre"}
        self.locales_vetados = {}    # locales que has atracado y aún te recuerdan: {lugar: {"hasta": día, "modo": cerrado u hostil}}
        self.proveedores = {}        # lo que te guarda cada proveedor que has asaltado: {lugar: {"asaltado", "veto", "caro"}}
        self.represalias = []        # gente que viene a por ti: [{"cuando", "lugar", "n"}]
        self.banda_gente = []        # la gente de tu banda, uno por uno: [{"id", "n", "g", "punteria", "conduccion", "nervios", "lealtad", "exp", "baja"}] (golpes.py)
        self.hangares = {}           # tus plazas de hangar: {campo: {"propia", "naves": [fichas], "pagado": día, "debe": euros}} (vuelo.py)
        self.tributos = {}           # bandas que te pagan por dejarles estar: {banda: {"euros", "hasta"}}
        self.tratos = {}             # último día que negociaste cada cosa con cada banda: {"banda:asunto": día}
        self.banda_paga = "normal"   # lo que cobra tu gente: baja, normal o alta (capo.py)
        self.deposito_hoy = {}       # el efectivo ingresado hoy en el banco: {"dia", "n"}
        self.casino_hoy = {}         # lo blanqueado hoy en fichas del casino
        self.gestor_pend = []        # lo que tiene el gestor: [{"dia", "euros", "bruto", "estafa"}]
        self.alquiladas = {}         # tus casas alquiladas: {casa: {"desde", "renta", "inquilino", "cobrado", "debe"}} (alquiler.py)
        self.quedadas = []           # con quién has quedado, dónde y a qué hora (encuentros.py)
        self.mochila = []            # lo que llevas en la mochila: [{"id", "robado"}] (mochila.py)
        self.mochila_grande = False
        self.almacen = {}            # el armario de cada casa tuya: {casa: {"objetos", "sust", "armas"}}
        self.desguace = {}           # lo vendido en los desguaces: {"ventas": [[día, modelo]], "hoy": {desguace: [día, n]}} (desguace.py)
        self.seguro_desde = 0        # el seguro de tus vehículos: desde qué día cubre; 0, sin contratar (misvehiculos.py)
        self.seguro_pend = []        # lo que el seguro tiene en reparación: [{"ficha", "dia", "franquicia", "avisado"}]
        self.convive = ""            # la persona de tu vida social que vive contigo (contenido para adultos)
        self.convive_casa = ""       # y en cuál de tus casas
        self.convive_desde = 0
        self.convive_hoy = {}        # lo que ya habéis hecho hoy en casa: {cosa: día}
        self.peticion_pareja = None  # algo que te ha pedido quien vive contigo: {"que", "dia", ...}
        self.despensa = {}           # lo guardado en la cocina de cada casa tuya: {casa: [{"id" o "plato", "n", "cad": día en que caduca o 0}]}
        self.encima = []             # la comida y la compra que llevas encima, con el mismo formato
        self.cocina_practica = 0.0   # tu mano en la cocina, de 0 a 100: sube con cada plato
        self.reconquista = {}        # las bandas que intentan recuperar tus barrios: fuerzas, lealtades, guardias, treguas y el asalto en curso (reconquista.py)
        self.antecedentes = []       # antecedentes penales: [{"d": día, "g": gravedad de 1 a 3, "t": texto, "c": día en que caduca}] (honrado.py)
        self.contrato = {}           # tu contrato fijo: empleo, puesto, jefe, turnos del periodo, avisos y méritos
        self.titulos = {}            # estudios: {título: {"s": sesiones hechas, "ok": día en que lo conseguiste o 0}}
        self.empresa = {}            # cómo llevas cada negocio tuyo: {lugar: {"nivel", "emp", "rep", "precios", "horario", "tapadera", "visto"}}
        self.creditos = []           # créditos e hipotecas: [{"tipo", "lugar", "cuota", "quedan", "prox", "impagos", "atraso"}]
        self.honra = {}              # lo demás de la vida y sus consecuencias: cobros, deudas, fiado, rumores, asuntos pendientes, abogado
        self.policia = {}            # el oficio de policía: {"alta": día, "expulsado": día, "detenciones", "multas", "avisos", "bajas"}
        self.stats = {"muertes": 0, "detenciones": 0, "enemigos": 0, "vehiculos_robados": 0,
                      "metros_pie": 0.0, "metros_coche": 0.0, "dinero_ganado": 0, "misiones": 0,
                      "carreras_taxi": 0, "pizzas": 0, "carreras": [], "tiempo": 0.0, "vendidos": 0}

    def a_dict(self):
        d = dict(self.__dict__)
        d.pop("veh", None)
        d.pop("t_ataque", None)
        return d

    def de_dict(self, d):
        base = Jugador()
        for k, v in d.items():
            if k in base.__dict__ and k not in ("veh",):
                setattr(self, k, v)
        for k, v in base.stats.items():
            self.stats.setdefault(k, v)
        self.veh = None


class Vehiculo:
    n = 0

    def __init__(self, modelo, x, y, d=0, ia=None):
        Vehiculo.n += 1
        self.id = Vehiculo.n
        self.modelo = modelo
        self.nombre = modelo["nombre"]
        self.x = x
        self.y = y
        self.dir = d
        self.rumbo = d * 90.0
        self.vel = 0.0
        self.salud = float(modelo["salud"])
        self.salud_max = float(modelo["salud"])
        self.ia = ia                # None, 'trafico', 'policia', 'huida', 'aparcado'
        self.giro = 0               # -1 izquierda, 1 derecha, 2 media vuelta
        self.lat = 0.0
        self.canal = None
        self.sirena = None
        self.alarma = None
        self.fuego = None
        self.cerrado = False
        self.con_alarma = False
        self.tag = None
        self.plaza = None
        self.ocupado = False
        self.desplegado = False
        self.t_parado = 0.0
        self.t_choque = 0.0
        self.t_giro = 0.0
        self.t_claxon = 0.0
        self.ardiendo = -1.0
        self.muerto = False
        self.hostil = False
        self.aviso_cruce = None
        self.vel_obj = 11.0

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)

    def callar(self):
        for c in (self.canal, self.sirena, self.alarma, self.fuego):
            if c is not None:
                c.parar()
        self.canal = self.sirena = self.alarma = self.fuego = None


_voces = random.Random()            # aparte del azar del juego: la voz de cada cual no cambia lo que pasa


class Persona:
    n = 0

    def __init__(self, tipo, x, y, nombre=None):
        Persona.n += 1
        self.id = Persona.n
        self.tipo = tipo            # civil, banda, policia, enemigo
        self.nombre = nombre or {"civil": tr("Peatón"), "banda": tr("Calavera"), "policia": tr("Policía")}.get(tipo, tr("Enemigo"))
        self.x = x
        self.y = y
        self.salud = 50.0
        self.arma = None
        self.hostil = False
        self.estado = "pasea"       # pasea, huye, ataca, quieto
        self.tag = None
        self.muerto = False
        self.bloque = None
        self.u = 0.0
        self.sentido = 1
        self.vel = 1.3
        self.t_paso = 0.0
        self.t_disparo = 1.0
        self.t_aviso = 0.0
        self.avisado = False
        self.t_estado = 0.0
        self.t_voz = 0.0
        self.t_arresto = 0.0
        self.activo = True
        # cada persona tiene su voz: unas más graves y otras más agudas. Con ella suenan sus quejas y sus gritos
        self.tono = _voces.uniform(0.80, 0.98) if _voces.random() < 0.5 else _voces.uniform(1.22, 1.42)

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)


class Objeto:
    n = 0

    def __init__(self, tipo, nombre, x, y, sonido="loc_objeto"):
        Objeto.n += 1
        self.id = Objeto.n
        self.tipo = tipo            # mision, casete, botiquin, dinero
        self.nombre = nombre
        self.x = x
        self.y = y
        self.sonido = sonido
        self.canal = None
        self.tag = None
        self.valor = 0

    def dist(self, x, y):
        return math.hypot(self.x - x, self.y - y)
