"""Opciones del juego: JSON con valores por defecto y escritura atómica."""
import json
import os

from . import rutas

from .cheats import OPTIONS as CHEAT_OPTIONS

POR_DEFECTO = {
    "cheat_velocidad_mundo": 0.25,  # world multiplier, bounded 0..5; cheat_tiempo enables it
    "vol_maestro": 0.8,
    "vol_efectos": 1.0,
    "vol_ambiente": 0.6,
    "vol_musica": 0.5,
    "vol_interfaz": 0.8,
    "musica_ambiente": True,
    "vol_ambiente_musical": 0.6,
    "pack_sonidos": "",            # subcarpeta de data/sonidos; vacío = los sonidos por defecto
    "igualar_volumen": True,       # lleva los sonidos cambiados al nivel de los originales
    "vol_sonidos": {},             # ajuste del jugador por sonido: nombre -> factor
    "adultos": False,
    "movimiento": "brujula",       # brujula | giro
    "conduccion": "asistida",      # asistida | libre
    "punteria": "completa",        # completa | manual
    "dificultad": "normal",        # facil | normal | dificil
    "direcciones": "cardinal",     # cardinal | reloj | relativa
    "anunciar_cruces": True,
    "anunciar_lugares": True,
    "anunciar_barrios": True,
    "anunciar_superficie": False,
    "piloto_gps": False,
    "piloto_estilo": "normal",     # normal | prisa | mucha_prisa | temerario: cómo conduce el piloto del GPS
    "semaforos_coche": True,       # al conducir tú, el semáforo del próximo cruce: si está en rojo o en verde
    "frenada_auto": True,
    "sucesos": True,
    "sucesos_apagados": [],        # los sucesos callejeros que no quieres que salgan, por su id (Opciones, La calle)
    "servidores": [],
    "comp_sin_interes": [],        # categorías de componentes que no quieres ver ni que te avisen: idioma, voces, documentacion, sonidos, mod              # servidores en línea guardados: nombre, dirección y huella de su certificado
    "mando_vibracion": True,
    "mando_textos": True,          # con un mando conectado, decir los botones en lugar de las teclas
    "invulnerable": False,
    "sin_policia": False,
    "baliza": True,
    "gps_voz": True,
    "sonar": True,
    "semaforos": True,
    "localizador": True,
    "voz_sapi": False,
    "voz_velocidad": 0,            # con la voz de Windows: de -10 a 10
    "voz_tono": 0,                 # de -10 a 10
    "voz_volumen": 100,            # de 0 a 100
    "detalle_voz": "normal",       # cuánto explica el juego al hablar: mucho, normal o poco
    "guardado_por_ranura": True,
    "orden_lugares": "alfabetico", # la lista de lugares del móvil: alfabetico | cercania (de lo más cerca a lo más lejos)
    "dia_semana": "ambos",         # cómo se dicen los días: numero (día 22) | nombre (lunes) | ambos (lunes, día 22)
    "pasos_alternos": True,        # tus pasos, uno a cada lado (izquierda y derecha); con no, todos al centro
    "callar_sin_foco": True,       # con el juego en segundo plano no habla: no interrumpe a tu lector en otra ventana
    "act_instalar_solo": False,    # al arrancar, si hay versión nueva, se descarga e instala sin preguntar
    "comp_instalar_solo": False,   # al arrancar, los componentes nuevos de las categorías que te interesan se instalan solos   # desde la 1.7.4: cada partida en su ranura, con su guardado automático y el rápido dentro
    "historial_menus": False,      # lo que se lee al moverse por los menús también va al historial (antes de la 1.7.3, siempre)
    "historial_al_final": True,    # cada mensaje nuevo lleva el historial (Re Pág y Av Pág) al final; con no, se queda donde lo dejaste
    "vol_senales": 1.0,            # volumen propio de balizas, radar, tonos de puntería y sonidos de los lugares
    "red_upnp": True,              # al abrir tu partida, intentar abrir el puerto del router automáticamente
    "mod_enemigos": False,         # modificador: los enemigos aguantan la mitad más
    "mod_policia": False,          # modificador: los delitos cuentan la mitad más
    "mod_dinero": False,           # modificador: las misiones pagan la mitad
    "noche_por_pasos": True,       # contenido para adultos: la noche con alguien se juega paso a paso
    "minijuego_laboratorio": True,  # contenido para adultos: cada tanda del laboratorio se juega con el minijuego de oído; con no, sale al momento
    "multas": True,                # con poca búsqueda, al cogerte puedes pagar la multa o intentar un soborno
    "fuego_amigo": True,           # tus balas y tus explosivos hieren también a tu perro, a tus guardaespaldas y a tu banda
    "aviso_acierto": True,         # un toque y una vibración cuando das en el blanco
    "correr_alternar": False,      # correr con una pulsación de Mayúsculas en vez de mantenerla
    "tutorial_visto": False,
    "radar_filtro": "todo",
    "emisora": 1,
    "radio_pausa": True,           # al bajarte o cambiar de emisora, la canción se queda en pausa y sigue luego por donde iba;
                                   # con no, la emisora sigue «sonando» sin ti, como una radio de verdad
    "ia_activa": False,            # modo IA al hablar con la gente
    "ia_servicio": "auto",         # auto | local | gemini | otro | openai | anthropic
    "ia_url_otro": "",             # dirección de un servicio compatible con OpenAI; vacío = OpenRouter
    "ia_modelo_otro": "",          # modelo de ese servicio; vacío = lo elige el juego
    "teclas_menus": False,         # las teclas cambiadas valen también en los menús y los diálogos
    "teclas": {},                  # teclas cambiadas: función original -> tecla física
    "viajes_trayecto": True,       # en taxi y autobús se oye el trayecto durante un rato; con no, se llega al momento
    "motor_sonido": "clasico",
    "recoger_al_pasar": True,      # lo que sueltan los enemigos (dinero, armas, munición y objetos de valor) se recoge al pasar por encima; con no, con Intro
    "salida_sonido": "",           # por dónde suena el juego: vacío = la salida de Windows, siguiéndola si cambia; o el nombre de una
    "salida_extra": "",            # una segunda salida con lo mismo, para grabar o retransmitir (solo con el motor clásico)
    "eco_lugares": True,           # con el motor envolvente, cada sitio tiene su eco: calle, nave, interior, campo     # clasico | envolvente (binaural con OpenAL Soft; se aplica al abrir el juego)
    "sonido_mono": False,          # los dos oídos oyen lo mismo
    "sonido_holgado": False,       # con el motor clásico, un búfer de sonido más grande: quita chasquidos y cortes en equipos justos
    "atenuar_al_hablar": True,     # bajar ambiente y música mientras habla la voz
    "describir_zonas": True,       # la primera vez que entras en un barrio, lo describe
    "menu_posicion": False,        # decir «3 de 9» al moverse por los menús
    "vibracion_fuerza": 1.0,       # intensidad de la vibración del mando, de 0.2 a 1
    "voces_grabadas": True,        # en las escenas, usar las voces grabadas que haya en data/voces
    "voces_propias": True,         # con un personaje propio, generar en este equipo las frases que dicen su nombre
    "atraccion": "todos",          # contenido para adultos: quién te atrae
    "mi_genero": "x",              # contenido para adultos: cómo te ven los demás (x = no dicho)
    "vida_realista": False,        # hambre y sueño
    "combustible": False,          # los vehículos gastan combustible y hay que repostar
    "averias": False,              # pinchazos y revisiones: los vehículos se desgastan con los kilómetros
    "normas_trafico": False,       # multas y carné por puntos por saltarte semáforos o correr delante de la policía
    "defensa_propia": True,        # defenderte de quien te ataca primero no es delito, y los agentes van también a por él
    "frases_reacciones": True,     # el lector dice cuándo alguien huye o se aparta (sin saturar)
    "charla_peatones": "pocas",    # frases que se oyen al pasar junto a dos personas: nada | pocas | algunas | muchas
    "soltar_municion": True,       # los enemigos caídos sueltan munición del arma que llevaban, si tú llevas una igual
    "soltar_armas": False,         # dificultad: a veces sueltan el arma entera
    "patrullas_calle": True,       # coches patrulla que circulan aunque no te busquen
    "ambulancias": True,           # tras un tiroteo o un atropello acude una ambulancia
    "helicoptero_policia": False,  # con el nivel de búsqueda más alto, un helicóptero te localiza desde el aire
    "guerra_calle": False,         # modo: las bandas se ven por la calle y los barrios se conquistan peleando allí
    "gente_actua": True,           # la gente con la que hablas puede seguirte un rato, pegarte tras una discusión, denunciarte o hacerte un favor
    "ia_acciones": False,          # con el modo IA: el modelo puede proponer una acción de una lista cerrada, y el juego decide si pasa
    "pareja_convive": False,       # contenido para adultos: poder pedirle a tu pareja que se venga a vivir contigo
    "escolta_misiones": "moderado",  # las misiones se ajustan a tu escolta: no | moderado | fuerte
    "ayuda_persecucion": True,     # persecuciones: avisos más seguidos de por dónde va quien huye, cada giro, y afloja antes si te quedas atrás
    "vuelo_real": True,            # helicópteros y avionetas con altura, y travesías de verdad entre localidades; con no, como antes: un salto desde el helipuerto
    "vuelo_asistido": True,        # en una travesía, al acercarte al campo el aparato baja y se encara solo
    "vuelo_combustible": True,     # con el vuelo real, las aeronaves gastan combustible y hay que repostar
    "reconquista": "normal",       # sin conexión, las bandas vencidas intentan recuperar tus barrios: apagado | tranquilo | normal | duro
    "consecuencias": "suave",      # vida, reputación y consecuencias: apagado | suave | normal | exigente
    "impuestos_facturas": True,    # facturas de tus casas e impuestos de tus propiedades y negocios, cada cierto tiempo y con aviso
    "antecedentes": True,          # las detenciones y las multas dejan antecedentes penales, que caducan
    "vida_en_persona": True,       # la vida social se vive en persona: desde el móvil se llama, se escribe y se queda (encuentros.py)
    "idioma": "auto",              # idioma del juego: auto (el del sistema) o un código, es, en... (i18n.py); vale al reiniciar
    "horarios": "apagado",         # horarios: apagado, solo de la gente, o de la gente y de los locales
    "pareja_familiar": True,       # relaciones sentimentales aptas para todos: conocerse, citas, compromiso, convivir y boda
    "oficio_policia": False,       # modo: poder ingresar en la policía y trabajar de agente
    "radio_coches": True,          # en un servidor, oír floja la emisora del juego que lleva el vehículo de otro jugador que está cerca
    "reconectar": True,            # en un servidor: si se corta o se reinicia, esperar y volver a entrar solo, con la partida tal cual
    "reconectar_minutos": 10,      # cuánto se le espera como mucho
    "red_nombre": "",              # cómo te ven tus amigos; vacío = el nombre de tu personaje
    "red_puerto": 47810,
    "red_ultima": "",              # última dirección a la que te uniste
    "comp_auto": True,             # buscar componentes nuevos al arrancar: idiomas, voces, packs... (solo avisa)
    "act_auto": True,              # buscar una versión nueva al arrancar (solo avisa)
    "act_fuente": "servidor",      # servidor | github | ambas | personalizada
    "act_url": "",                 # dirección de version.json para la fuente personalizada
}

POR_DEFECTO.update({row[0]: False for row in CHEAT_OPTIONS})

OPCIONES = {
    "movimiento": ["brujula", "giro"],
    "conduccion": ["asistida", "libre"],
    "piloto_estilo": ["normal", "prisa", "mucha_prisa", "temerario"],
    "dia_semana": ["ambos", "numero", "nombre"],
    "orden_lugares": ["alfabetico", "cercania"],
    "punteria": ["completa", "manual"],
    "dificultad": ["facil", "normal", "dificil"],
    "direcciones": ["cardinal", "reloj", "relativa"],
    "radar_filtro": ["todo", "lugares", "vehiculos", "personas", "objetos"],
    "atraccion": ["todos", "mujeres", "hombres"],
    "mi_genero": ["x", "h", "m"],
    "charla_peatones": ["nada", "pocas", "algunas", "muchas"],
    "reconquista": ["apagado", "tranquilo", "normal", "duro"],
    "consecuencias": ["apagado", "suave", "normal", "exigente"],
    "horarios": ["apagado", "gente", "todo"],
    "escolta_misiones": ["no", "moderado", "fuerte"],
    "act_fuente": ["servidor", "github", "ambas", "personalizada"],
    "motor_sonido": ["clasico", "envolvente"],
    "ia_servicio": ["auto", "local", "gemini", "otro", "openai", "anthropic"],
}


class Config:
    def __init__(self, archivo=None):
        self.archivo = archivo or rutas.archivo_config("config")
        self.v = {k: (dict(v) if isinstance(v, dict) else v) for k, v in POR_DEFECTO.items()}
        self.cargar()

    def cargar(self):
        try:
            from . import cifrado
            origen = self.archivo
            if not os.path.exists(origen):                # opciones guardadas con la otra forma (antes o después de compilar)
                base = os.path.splitext(origen)[0]
                origen = next((base + e for e in (".json", rutas.EXT_CONFIG) if os.path.exists(base + e)), origen)
            datos = cifrado.leer_json(origen)
            for k, val in datos.items():
                if k in POR_DEFECTO and isinstance(val, type(POR_DEFECTO[k])):
                    self.v[k] = val
                elif k in POR_DEFECTO and isinstance(POR_DEFECTO[k], float) and isinstance(val, (int, float)):
                    self.v[k] = float(val)
            for k, ops in OPCIONES.items():
                if self.v[k] not in ops:
                    self.v[k] = POR_DEFECTO[k]
        except (OSError, ValueError):
            pass

    def guardar(self):
        try:
            from . import cifrado
            v = dict(self.v)
            v.update(getattr(self, "temporales", {}))            # lo que se ha cambiado solo para esta sesión no se guarda
            cifrado.escribir_json(self.archivo, v, sangria=2)          # protegido en el juego compilado
        except OSError:
            pass

    # Lo que es tuyo y no una preferencia: no se toca al restablecer las opciones de serie.
    CONSERVAR = ("idioma", "servidores", "red_nombre", "red_ultima", "act_url", "ia_url_otro", "ia_modelo_otro", "ia_servicio", "tutorial_visto")

    def restablecer(self):
        """Todas las opciones como vienen de serie, menos lo de CONSERVAR."""
        guardado = {k: self.v[k] for k in self.CONSERVAR if k in self.v}
        self.v = {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in POR_DEFECTO.items()}
        self.v.update(guardado)

    def __getitem__(self, k):
        return self.v[k]

    def __setitem__(self, k, val):
        self.v[k] = val
