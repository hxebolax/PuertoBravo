"""Escribe en data/mods los mods completos de ejemplo y los comprueba con el mismo revisor del editor.

    .venv\\Scripts\\python.exe herramientas\\crear_mods_ejemplo.py

- costa_dorada.json: un pueblo nuevo entero, con su historia, y un ejemplo de TODO lo que admite un mod:
  mapa, lugares de casi todos los tipos, misiones con los nueve tipos de paso, armas de los tres tipos,
  coche, barco y aeronave, carrera, comidas, objeto, peces, personajes, capítulos y, para el modo adulto,
  club, proveedor, persona, plan, regalo, sustancia y misión.
- oficios_y_recados.json: un mod pequeño de vida honrada en las ciudades que ya existen.
- valdeolmos.json: otro pueblo nuevo, de interior, con su historia, su río y su carrera de tractores.
- motor_y_asfalto.json: coches, una moto, carreras y dos misiones al volante.
- penas_altas.json: un pueblo minero de montaña, con su historia, su lago y contenido para el modo adulto.
- isla_de_los_vientos.json: una isla a la que se llega navegando, con raqueros, salinas y un catamarán.
- noches_de_neon.json: la noche de Puerto Bravo, sin mapa nuevo: locales, taxis nocturnos y vida social.
- bahia_del_ocaso.json: una ciudad grande de costa, con seis barrios, tres bandas y una historia de veintiuna misiones.

Todos se pueden abrir con el editor de mods para ver cómo están hechos.
"""
import copy
import json
import os
import sys

os.environ["PUERTOBRAVO_IDIOMA"] = "es"          # escribe datos del juego: en español, el idioma de origen, sea cual sea el de Windows

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from juego import rutas          # noqa: E402


def _base(archivo):
    from juego import cifrado
    return cifrado.leer_json(os.path.join(rutas.DATOS, archivo))


ARMAS = {a["id"]: a for a in _base("armas.json")["armas"]}
VEHICULOS = {v["id"]: v for v in _base("vehiculos.json")["vehiculos"]}
SUSTANCIAS = {s["id"]: s for s in _base("adultos.json")["sustancias"]}


def clon(tabla, origen, **cambios):
    d = copy.deepcopy(tabla[origen])
    d.update(cambios)
    return d


def primero(tabla, cond):
    return next(k for k, v in tabla.items() if cond(v))


def D(*lineas):
    return {"tipo": "dialogo", "lineas": [list(l) for l in lineas]}


# ============================================================ Costa Dorada
def costa_dorada():
    cuerpo = primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    explosivo = primero(ARMAS, lambda a: a["tipo"] == "explosivo")
    lancha = primero(VEHICULOS, lambda v: v.get("barco"))
    aeronave = primero(VEHICULOS, lambda v: v.get("vuela"))
    furgo = "furgoneta" if "furgoneta" in VEHICULOS else "utilitario"
    mapa = {
        "id": "costa_dorada", "tipo": "pueblo", "nombre": "Costa Dorada", "trafico": 2, "peatones": 4,
        "avenidas": ["Avenida del Espigón", "Calle de las Redes", "Calle del Azafrán", "Avenida de los Naranjos", "Camino del Faro Viejo"],
        "calles": ["Paseo de la Costa", "Calle de la Lonja", "Calle del Mercado", "Carretera de Puerto Bravo"],
        "barrios": [
            {"id": "cd_marina", "nombre": "La Marina", "i": [0, 3], "j": [0, 0], "ambiente": "amb_playa", "vehiculos": ["utilitario", "bici", "cd_buggy"],
             "descripcion": "La Marina de Costa Dorada: redes tendidas al sol, olor a brea y barcas varadas en la arena."},
            {"id": "cd_pueblo", "nombre": "El Pueblo", "i": [0, 3], "j": [1, 2], "ambiente": "amb_residencial", "vehiculos": ["utilitario", furgo, "cd_reparto"],
             "descripcion": "El Pueblo: casas encaladas, naranjos en las aceras y una plaza con mercado todas las mañanas."}],
        "bloques": {"0,0": "arena", "1,0": "arena", "3,0": "muelle", "1,1": "plaza", "3,2": "hierba"},
        "lugares": [
            {"id": "cd_salida", "nombre": "Salida norte, carretera de Puerto Bravo", "tipo": "salida", "bloque": [2, 2], "lado": "N", "pos": 36, "a_mapa": "puerto_bravo", "a_lugar": "pb_salida_costa", "km": 22, "horas": 0.6, "desc": "La carretera de la costa, que lleva a Puerto Bravo."},
            {"id": "cd_estacion", "nombre": "Parada del autobús de Costa Dorada", "tipo": "estacion", "bloque": [0, 2], "lado": "S", "pos": 36, "precio": 15, "desc": "Una marquesina junto al mercado."},
            {"id": "cd_embarcadero", "nombre": "Embarcadero de Costa Dorada", "tipo": "embarcadero", "bloque": [3, 0], "lado": "S", "pos": 36, "a_mapa": "mar", "a_lugar": "mar_costa", "desc": "Un muelle de tablones con cuatro barcas."},
            {"id": "cd_taberna", "nombre": "Taberna El Ancla", "tipo": "taberna", "bloque": [2, 0], "lado": "N", "pos": 20, "desc": "Vino de la tierra, dados y un tablón con encargos."},
            {"id": "cd_lonja", "nombre": "Lonja de Costa Dorada", "tipo": "pescaderia", "bloque": [2, 0], "lado": "E", "pos": 36, "sonido": "lugar_tienda", "desc": "Aquí se subasta el pescado al amanecer. Compran todo lo que traigas."},
            {"id": "cd_restaurante", "nombre": "Arrocería La Barraca", "tipo": "comida", "bloque": [0, 1], "lado": "S", "pos": 36, "desc": "El mejor arroz de la costa."},
            {"id": "cd_tienda", "nombre": "Ultramarinos Azafrán", "tipo": "tienda", "surtidor": True, "bloque": [2, 1], "lado": "O", "pos": 36, "desc": "De todo un poco, y amuletos de pescador."},
            {"id": "cd_armeria", "nombre": "Efectos Navales Poniente", "tipo": "armeria", "bloque": [3, 1], "lado": "S", "pos": 36, "desc": "Arpones, remos, bengalas y lo que haga falta en la mar."},
            {"id": "cd_farmacia", "nombre": "Farmacia del Mercado", "tipo": "farmacia", "bloque": [0, 1], "lado": "E", "pos": 36, "desc": "Tiritas, botiquines y consejos de la boticaria."},
            {"id": "cd_taller", "nombre": "Taller Mecánico Naranjo", "tipo": "taller", "bloque": [3, 1], "lado": "N", "pos": 36, "desc": "Repara, pinta y no pregunta."},
            {"id": "cd_banco", "nombre": "Caja Rural de la Costa", "tipo": "banco", "bloque": [2, 1], "lado": "N", "pos": 36, "desc": "Una sucursal pequeña con un cajero de los de antes."},
            {"id": "cd_gimnasio", "nombre": "Club de Remo", "tipo": "gimnasio", "bloque": [2, 2], "lado": "S", "pos": 20, "desc": "Remo en seco, pesas y combates los viernes."},
            {"id": "cd_hostal", "nombre": "Hostal La Marea", "tipo": "hotel", "bloque": [0, 2], "lado": "E", "pos": 36, "precio_noche": 35, "desc": "Sábanas limpias y el mar de fondo."},
            {"id": "cd_casa", "nombre": "Casa del pescador", "tipo": "casa", "bloque": [2, 0], "lado": "O", "pos": 36, "precio": 4800, "garaje": 2, "desc": "Una casita encalada frente a la playa, con cobertizo para dos vehículos."},
            {"id": "cd_conservera", "nombre": "Conservera La Dorada", "tipo": "negocio", "bloque": [3, 1], "lado": "O", "pos": 36, "sonido": "lugar_taller", "precio": 22000, "ingresos": 520, "desc": "Una fábrica de conservas en venta. Da dinero cada medianoche."},
            {"id": "cd_empleo", "nombre": "Cofradía de pescadores, bolsa de trabajo", "tipo": "empleo", "bloque": [1, 2], "lado": "S", "pos": 36, "desc": "Aquí se reparten las jornadas y los oficios del pueblo."},
            {"id": "cd_escuela", "nombre": "Escuela Náutica", "tipo": "academia", "bloque": [1, 2], "lado": "E", "pos": 36, "cursos": ["pesca", "resistencia"], "desc": "Cursos de pesca y de resistencia."},
            {"id": "cd_caritas", "nombre": "Despensa Solidaria", "tipo": "ong", "bloque": [0, 2], "lado": "N", "pos": 20, "desc": "Reparten comida a quien la necesita. Siempre faltan manos."},
            {"id": "cd_concesionario", "nombre": "Automóviles de Ocasión Levante", "tipo": "concesionario", "bloque": [2, 2], "lado": "E", "pos": 36, "modelos": ["cd_buggy", "cd_reparto", "utilitario"], "desc": "Coches de segunda mano y los buggies de la playa."},
            {"id": "cd_nautica", "nombre": "Náutica Costa Dorada", "tipo": "nautica", "bloque": [2, 0], "lado": "S", "pos": 60, "embarcadero": "cd_embarcadero", "desc": "Venden veleros y los dejan amarrados en el embarcadero."},
            {"id": "cd_taxi", "nombre": "Parada de taxis del Mercado", "tipo": "taxi", "bloque": [1, 2], "lado": "O", "pos": 36, "vehiculo": "taxi", "desc": "Dos taxis y un taxista dormido."},
            {"id": "cd_circuito", "nombre": "Salida del circuito de la playa", "tipo": "carrera", "bloque": [0, 1], "lado": "O", "pos": 36, "desc": "Los domingos se corre con buggies."},
            {"id": "cd_helipuerto", "nombre": "Helipuerto del Faro Viejo", "tipo": "helipuerto", "bloque": [3, 2], "lado": "S", "pos": 36, "vehiculo": "cd_autogiro", "precio": 120, "desc": "Una explanada con una manga de viento."},
            {"id": "cd_plaza", "nombre": "Plaza del Mercado", "tipo": "monumento", "bloque": [1, 1], "xy": [36, 36], "sonido": "lugar_fuente", "desc": "Una fuente, cuatro naranjos y los puestos del mercado."},
            {"id": "cd_faro", "nombre": "El Faro Viejo", "tipo": "monumento", "bloque": [3, 2], "xy": [45, 50], "sonido": "lugar_iglesia", "desc": "Un faro apagado hace cuarenta años. Dicen que quien sube ve hasta Isla Tortuga."},
            {"id": "cd_espigon", "nombre": "Espigón de Costa Dorada", "tipo": "pesca", "bloque": [1, 0], "xy": [40, 20], "desc": "El mejor sitio para la dorada de roca."},
            {"id": "cd_cala", "nombre": "Cala de los Detectores", "tipo": "tesoro", "bloque": [0, 0], "xy": [30, 20], "desc": "Los turistas pierden aquí de todo."},
            {"id": "cd_club", "nombre": "Sala Marejada", "tipo": "club", "bloque": [3, 1], "lado": "E", "pos": 36, "adultos": True, "desc": "Copas, espectáculo y la gente guapa de la costa."},
            {"id": "cd_bodeguero", "nombre": "Almacén del Bodeguero", "tipo": "proveedor", "bloque": [0, 1], "lado": "N", "pos": 36, "adultos": True, "factor": {"hierba": 0.8, "polvo": 1.3, "pastillas": 1.0, "cristal": 1.4, "cd_licor": 0.7}, "desc": "Orujo de hierbas de contrabando y lo que traigan las lanchas."},
        ],
        "casetes": [[50, 110], [300, 200]],
    }
    lugares = [
        {"id": "pb_salida_costa", "mapa": "puerto_bravo", "nombre": "Salida oeste, carretera de Costa Dorada", "tipo": "salida", "bloque": [0, 4], "lado": "O", "pos": 36, "a_mapa": "costa_dorada", "a_lugar": "cd_salida", "km": 22, "horas": 0.6, "desc": "La carretera de la costa, que lleva a Costa Dorada."},
        {"id": "mar_costa", "mapa": "mar", "nombre": "Embarcadero de Costa Dorada, desde el mar", "tipo": "muelle", "xy": [60, 1100], "a_mapa": "costa_dorada", "a_lugar": "cd_embarcadero", "desc": "El muelle de tablones de Costa Dorada, al oeste de Puerto Bravo."},
    ]
    armas = [
        clon(ARMAS, "rifle", id="cd_arpon", nombre="Fusil de arpones", dano=85, alcance=28, cadencia=1.6, precision=0.9, cargador=1, precio=900, balas=6, precio_balas=60, ruido=1,
             desc="Un solo arpón por disparo y tarda en recargar, pero casi no hace ruido y donde da, se queda."),
        clon(ARMAS, cuerpo, id="cd_remo", nombre="Remo de madera", dano=30, alcance=3.2, cadencia=0.8, precio=40, desc="Largo, pesado y siempre a mano en un pueblo de pescadores."),
        clon(ARMAS, explosivo, id="cd_bengala", nombre="Bengala de señales", dano=60, precio=180, desc="Se lanza como una granada. Arde, asusta y hace menos daño que una de verdad."),
    ]
    vehiculos = [
        clon(VEHICULOS, "utilitario", id="cd_buggy", nombre="Buggy de playa", vel_max=30, acel=8.5, freno=15, salud=80, tono=1.4, valor=700, precio=5200, desc="Ligero y nervioso. Acelera como un demonio y se rompe con mirarlo."),
        clon(VEHICULOS, furgo, id="cd_reparto", nombre="Furgoneta de reparto del pescado", salud=140, valor=600, precio=4200, trabajo="paqueteria", desc="Huele a lonja. Con la tecla J haces el reparto de paquetes."),
        clon(VEHICULOS, lancha, id="cd_velero", nombre="Velero Tramontana", vel_max=17, acel=3.5, salud=180, precio=16000, trabajo="mensajeria", desc="Un velero de dos palos. Silencioso y marinero."),
        clon(VEHICULOS, aeronave, id="cd_autogiro", nombre="Autogiro Libélula", vel_max=34, salud=110, precio=52000, desc="Un autogiro de dos plazas. Vuela por encima de todo, como el helicóptero, pero más despacio."),
    ]
    misiones = [
        {"id": "cd01", "titulo": "Bienvenido a Costa Dorada", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["m01"],
         "resumen": "En la Taberna El Ancla, Amparo necesita a alguien que no sea del pueblo.",
         "pasos": [D(("Amparo", "Tú no eres de aquí. Mejor. Aquí todos son primos de alguien y nadie quiere líos."),
                     ("Amparo", "Eres Dani, ¿no? Me han hablado de ti. Sube al Faro Viejo y mira si es verdad que alguien ha roto el candado. Yo no puedo dejar la barra.")),
                   {"tipo": "ir", "lugar": "cd_faro", "radio": 14, "texto": "Sube al Faro Viejo, al noreste del pueblo, y mira el candado."},
                   D(("Narrador", "El candado está cortado con una cizalla. Dentro hay cajas de madera sin marcar, y huele a gasóleo."),
                     ("Narrador", "Alguien usa el faro de almacén. Vuelves a contárselo a Amparo."))],
         "recompensa": {"dinero": 250}},
        {"id": "cd02", "titulo": "La furgoneta del pescado", "vehiculo_libre": True, "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd01"],
         "resumen": "La furgoneta de la lonja lleva dos días sin repartir y el arroz no espera.",
         "pasos": [D(("Amparo", "El chaval del reparto no aparece y la furgoneta sigue en la lonja, con las llaves puestas. Llévala a La Barraca antes de que se eche a perder el género."),
                     ("Amparo", "Y con cuidado, que si llega abollada el Sento no te paga.")),
                   {"tipo": "robar", "lugar": "cd_lonja", "modelo": "cd_reparto", "nombre": "la furgoneta del pescado", "abierto": True, "texto": "Recoge la furgoneta del pescado junto a la Lonja. Está abierta."},
                   {"tipo": "entregar", "lugar": "cd_restaurante", "salud_min": 60, "limite": 240, "texto": "Lleva la furgoneta a la Arrocería La Barraca en cuatro minutos y sin destrozarla."},
                   D(("Sento", "¡Por fin! Otro día sin gamba y cierro. Toma, y dile a Amparo que le debo una paella."))],
         "recompensa": {"dinero": 400}},
        {"id": "cd03", "titulo": "Los de la lancha", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd02"],
         "resumen": "Los dueños de las cajas del faro han venido a por el chaval del reparto.",
         "pasos": [D(("Amparo", "Ya sé dónde está el chaval. Lo tienen los de la lancha negra en el embarcadero, porque vio lo que no debía."),
                     ("Amparo", "Toma el fusil de arpones de mi difunto marido. Un tiro cada vez, así que apunta.")),
                   {"tipo": "dar", "arma": "cd_arpon", "balas": 8},
                   {"tipo": "eliminar", "lugar": "cd_embarcadero", "texto": "Ve al embarcadero y acaba con los de la lancha negra.",
                    "enemigos": [{"n": 2, "tipo": "Contrabandista", "arma": "pistola", "salud": 60}, {"n": 1, "tipo": "Patrón de la lancha", "arma": "cd_remo", "salud": 90}]},
                   {"tipo": "recoger", "lugar": "cd_embarcadero", "objeto": "el cuaderno de entregas", "texto": "Recoge el cuaderno de entregas que ha quedado en el muelle."},
                   D(("Narrador", "El chaval sale de debajo de una lona, blanco como la cal, y echa a correr hacia el pueblo."),
                     ("Narrador", "El cuaderno tiene fechas, matrículas y un nombre que se repite: el Bodeguero."))],
         "recompensa": {"dinero": 600, "arma": "cd_arpon", "balas": 6}},
        {"id": "cd04", "titulo": "Sirenas en el paseo", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd03"],
         "resumen": "Hay que sacar las cajas del faro antes de que alguien avise a la Guardia Civil.",
         "pasos": [D(("Amparo", "Si encuentran esas cajas en el faro, cierran el pueblo entero. Hay un buggy cargado junto al helipuerto. Tíralo todo al desguace del Naranjo."),
                     ("Amparo", "Te van a ver, eso seguro. Piérdelos antes de entregar.")),
                   {"tipo": "robar", "lugar": "cd_helipuerto", "modelo": "cd_buggy", "nombre": "el buggy cargado", "busqueda": 2, "texto": "Hazte con el buggy cargado que hay junto al Helipuerto del Faro Viejo."},
                   {"tipo": "policia", "nivel": 2, "texto": "Te han visto. Despista a la policía."},
                   {"tipo": "entregar", "lugar": "cd_taller", "salud_min": 30, "texto": "Lleva el buggy al Taller Mecánico Naranjo."},
                   D(("Naranjo", "Mañana esto es chatarra y aquí no ha pasado nada."))],
         "recompensa": {"dinero": 900, "chaleco": True}},
        {"id": "cd05", "titulo": "El Bodeguero se escapa", "capitulo": 20, "contacto": "Amparo", "lugar": "cd_taberna", "requiere": ["cd04"],
         "resumen": "El Bodeguero ha cargado lo que le queda y sale del pueblo por la carretera.",
         "pasos": [D(("Amparo", "Se va. Ha cargado su todoterreno y tira para la carretera de Puerto Bravo. Si llega, vuelve con más gente.")),
                   {"tipo": "dar", "balas_arma": "cd_arpon", "balas": 6},
                   {"tipo": "dar", "arma": "cd_bengala", "balas": 3},
                   {"tipo": "perseguir", "lugar": "cd_salida", "modelo": "todoterreno" if "todoterreno" in VEHICULOS else "utilitario", "nombre": "el todoterreno del Bodeguero", "salud": 220, "limite": 300,
                    "texto": "Alcanza y destroza el todoterreno del Bodeguero antes de que pasen cinco minutos."},
                   {"tipo": "recoger", "aqui": True, "objeto": "la llave del almacén", "texto": "Recoge la llave del almacén que ha saltado del todoterreno."},
                   D(("Narrador", "Costa Dorada vuelve a oler solo a brea y a arroz."),
                     ("Amparo", "El pueblo te debe una, Dani. El velero de mi marido es tuyo: está amarrado en el embarcadero.")),
                   {"tipo": "dar", "dinero": 500}],
         "recompensa": {"dinero": 2000, "barco": {"modelo": "cd_velero", "en": "cd_embarcadero"}}},
        {"id": "cd06", "titulo": "Un día de mercado", "capitulo": 21, "contacto": "La boticaria", "lugar": "cd_farmacia", "requiere": ["m01"],
         "resumen": "Trabajo honrado: recados por el pueblo antes de que cierre el mercado.",
         "pasos": [D(("La boticaria", "¿Tú haces recados? Tres cosas, y rápido, que cierro a las dos."),
                     ("La boticaria", "Lleva este jarabe a la Despensa Solidaria, pasa por la Cofradía a por mis papeles y tráeme azafrán de los ultramarinos.")),
                   {"tipo": "ir", "lugar": "cd_caritas", "limite": 150, "texto": "Lleva el jarabe a la Despensa Solidaria en dos minutos y medio."},
                   {"tipo": "ir", "lugar": "cd_empleo", "texto": "Pasa por la Cofradía de pescadores."},
                   {"tipo": "recoger", "lugar": "cd_tienda", "objeto": "el azafrán", "texto": "Recoge el azafrán en Ultramarinos Azafrán."},
                   {"tipo": "ir", "lugar": "cd_farmacia", "texto": "Vuelve a la Farmacia del Mercado."},
                   D(("La boticaria", "Así da gusto. Toma, y un botiquín de regalo, que con la vida que llevas te hará falta."))],
         "recompensa": {"dinero": 350}},
        {"id": "cda1", "titulo": "Orujo de hierbas", "capitulo": 22, "adultos": True, "contacto": "Marina", "lugar": "cd_club", "requiere": ["cd01"],
         "resumen": "En la Sala Marejada, Marina necesita que alguien lleve una caja sin hacer preguntas.",
         "pasos": [D(("Marina", "El orujo del Bodeguero es lo único que se vende aquí en invierno. Llévale estas botellas a Amparo, a El Ancla, y quédate dos para ti.")),
                   {"tipo": "dar", "sustancia": "cd_licor", "cantidad": 2},
                   {"tipo": "ir", "lugar": "cd_taberna", "texto": "Lleva las botellas a la Taberna El Ancla."},
                   D(("Amparo", "Dile a Marina que la próxima vez venga ella, que hace un mes que no la veo."))],
         "recompensa": {"dinero": 300, "afinidad": {"cd_marina": 15}}},
    ]
    return {
        "info": {"nombre": "Costa Dorada", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Un pueblo pesquero nuevo al oeste de Puerto Bravo, con su historia en cinco misiones, trabajo honrado, armas, vehículos, un velero, un autogiro, una carrera y dos personajes. Sirve de ejemplo de todo lo que puede llevar un mod."},
        "capitulos": {"20": "Costa Dorada", "21": "Costa Dorada: vida honrada", "22": "Costa Dorada: historias para adultos"},
        "mapas": [mapa], "lugares": lugares, "misiones": misiones, "armas": armas, "vehiculos": vehiculos,
        "carreras": [{"id": "cd_c1", "nombre": "Vuelta a Costa Dorada", "mapa": "costa_dorada", "premio": 350, "tiempo": 80, "puntos": [[0, 1], [0, 3], [4, 3], [4, 1], [0, 1]]}],
        "comidas": [{"nombre": "Arroz a banda", "precio": 14, "salud": 45}, {"nombre": "Horchata con fartons", "precio": 5, "salud": 12}],
        "objetos": [{"id": "cd_amuleto", "nombre": "Amuleto de pescador", "precio": 25, "desc": "Una caracola con un cordel. No sirve para nada, pero da conversación."}],
        "peces": [{"nombre": "una dorada de roca", "valor": 38, "peso": 12, "aguas": ["mar"], "mapas": ["costa_dorada"]}, {"nombre": "un pulpo de Costa Dorada", "valor": 55, "peso": 6, "aguas": ["mar"], "mapas": ["costa_dorada"]}],
        "personajes": [
            {"id": "cd_vicenta", "nombre": "Vicenta", "genero": "m", "apellido": "Ribera", "pesca": 5, "resistencia": 2, "dinero": 300, "ciudadania": 30, "arma": "cd_remo", "botiquines": 1,
             "desc": "Patrona de pesca de Costa Dorada. Empieza con la pesca al nivel cinco, buena resistencia, un remo, trescientos euros y el respeto de los vecinos."},
            {"id": "cd_quico", "nombre": "Quico", "genero": "h", "apellido": "Marí", "conduccion": 3, "punteria": 2, "reputacion": 20, "ganzuas": 2, "botiquines": 1,
             "desc": "Hizo de todo en las lanchas del contrabando. Empieza con conducción al nivel tres, algo de puntería, fama en la calle y dos juegos de ganzúas."}],
        "personas": [{"id": "cd_marina", "nombre": "Marina", "edad": 33, "lugar": "cd_club", "gustos": ["cd_velada", "paseo"], "regalo": "cd_perla",
                      "desc": "Lleva la Sala Marejada desde que murió su tío. Seria de día, otra persona de noche. Conoce todos los secretos del pueblo y no cuenta ninguno."}],
        "actividades": [{"id": "cd_velada", "nombre": "Cenar arroz en La Barraca", "precio": 40, "horas": 3}],
        "regalos": [{"id": "cd_perla", "nombre": "Una perla de la lonja", "precio": 120, "afinidad": 12}],
        "sustancias": [clon(SUSTANCIAS, "alcohol", id="cd_licor", nombre="Orujo de hierbas", unidad="botella", precio=18, animo=9, adiccion=2.0, sobredosis=4,
                            desc="Orujo de hierbas de contrabando. Sube el ánimo más que una copa y tumba antes: a la cuarta seguida acabas en el hospital.")],
    }


# ============================================================ Oficios y recados
def oficios():
    return {
        "info": {"nombre": "Oficios y recados", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Más vida honrada en Puerto Bravo: una academia de puntería deportiva, un banco de alimentos, una casa, un negocio, una moto de mensajería, un personaje y dos encargos de recadero."},
        "capitulos": {"23": "Oficios y recados"},
        "lugares": [
            {"id": "of_tiro", "mapa": "puerto_bravo", "nombre": "Club de Tiro Olímpico", "tipo": "academia", "bloque": [6, 5], "lado": "S", "pos": 20, "cursos": ["punteria"], "desc": "Tiro deportivo con monitor. Aquí la puntería se aprende sin hacer daño a nadie."},
            {"id": "of_alimentos", "mapa": "puerto_bravo", "nombre": "Banco de Alimentos del Barrio Viejo", "tipo": "ong", "bloque": [2, 4], "lado": "S", "pos": 20, "desc": "Voluntarios, cajas de fruta y mucha cola a final de mes."},
            {"id": "of_mensajeria", "mapa": "puerto_bravo", "nombre": "Mensajería Relámpago", "tipo": "negocio", "bloque": [4, 5], "lado": "S", "pos": 20, "sonido": "lugar_empleo", "precio": 9000, "ingresos": 260, "vehiculo": "of_moto", "desc": "Una empresa de mensajería en venta. En la puerta hay siempre una moto de reparto: súbete y pulsa J."},
            {"id": "of_piso", "mapa": "puerto_bravo", "nombre": "Piso de la calle de los Herreros", "tipo": "casa", "bloque": [3, 5], "lado": "S", "pos": 50, "precio": 3900, "garaje": 1, "desc": "Un tercero sin ascensor, pequeño y luminoso, con una plaza de garaje."},
        ],
        "vehiculos": [clon(VEHICULOS, "moto" if "moto" in VEHICULOS else "utilitario", id="of_moto", nombre="Moto de mensajería", vel_max=27, salud=75, valor=350, precio=1900, trabajo="paqueteria",
                           desc="Una moto de reparto con un cajón detrás. Con la tecla J haces de mensajero.")],
        "personajes": [{"id": "of_noa", "nombre": "Noa", "genero": "m", "apellido": "Santos", "ciudadania": 60, "animo": 80, "resistencia": 3, "dinero": 150, "botiquines": 2,
                        "desc": "Trabajó diez años de mensajera en bicicleta. Empieza con muy buen nombre entre los vecinos, buen ánimo, resistencia al nivel tres y dos botiquines: ideal para una vida honrada."}],
        "misiones": [
            {"id": "of01", "titulo": "Cajas para el banco de alimentos", "vehiculo_libre": True, "capitulo": 23, "contacto": "Reme", "lugar": "of_alimentos", "requiere": ["m01"],
             "resumen": "Trabajo honrado: el Banco de Alimentos necesita un transportista.",
             "pasos": [D(("Reme", "Tenemos una donación esperando en el mercado y nadie con carné. ¿Tú conduces?")),
                       {"tipo": "robar", "lugar": "of_mensajeria", "modelo": "furgoneta" if "furgoneta" in VEHICULOS else "utilitario", "nombre": "la furgoneta prestada", "abierto": True, "texto": "Recoge la furgoneta que os presta Mensajería Relámpago. Está abierta."},
                       {"tipo": "entregar", "lugar": "of_alimentos", "salud_min": 70, "texto": "Lleva la furgoneta con las cajas al Banco de Alimentos, sin golpes."},
                       D(("Reme", "Con esto comen cuarenta familias. Gracias, de verdad."))],
             "recompensa": {"dinero": 150}},
            {"id": "of02", "titulo": "Contrarreloj", "capitulo": 23, "contacto": "El encargado", "lugar": "of_mensajeria", "requiere": ["of01"],
             "resumen": "Trabajo honrado: un sobre urgente tiene que llegar al hospital.",
             "pasos": [D(("El encargado", "Sobre urgente para el hospital. Si llegas en tres minutos, hay propina.")),
                       {"tipo": "ir", "lugar": "hospital", "limite": 180, "texto": "Lleva el sobre al Hospital General en tres minutos."},
                       D(("Narrador", "Una doctora firma el recibo sin levantar la vista. Trabajo hecho."))],
             "recompensa": {"dinero": 220}},
        ],
    }


# ============================================================ Valdeolmos
def valdeolmos():
    escopeta = "escopeta" if "escopeta" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    cuerpo = primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    tractor = "tractor" if "tractor" in VEHICULOS else "utilitario"
    todo = "todoterreno" if "todoterreno" in VEHICULOS else "utilitario"
    mapa = {
        "id": "valdeolmos", "tipo": "pueblo", "nombre": "Valdeolmos", "trafico": 1, "peatones": 3,
        "avenidas": ["Camino de las Viñas", "Calle del Lagar", "Calle de la Vendimia", "Carretera de la Bodega"],
        "calles": ["Carretera de Puerto Bravo", "Calle de la Plaza", "Calle de los Olmos", "Camino del Río"],
        "barrios": [
            {"id": "vo_pueblo", "nombre": "Valdeolmos", "i": [0, 2], "j": [0, 1], "ambiente": "amb_campo", "vehiculos": [tractor, todo, "vo_remolque", "bici"],
             "descripcion": "Valdeolmos, un pueblo de viñas y bodegas. Huele a mosto en septiembre y a leña el resto del año."},
            {"id": "vo_ribera", "nombre": "La Ribera", "i": [0, 2], "j": [2, 2], "ambiente": "amb_parque", "vehiculos": [todo, "bici"],
             "descripcion": "La Ribera: huertas, olmos viejos y el río Olmedilla, que baja frío y con truchas."}],
        "bloques": {"1,0": "plaza", "0,2": "hierba", "1,2": "hierba", "2,2": "hierba"},
        "lugares": [
            {"id": "vo_salida", "nombre": "Salida sur, carretera de Puerto Bravo", "tipo": "salida", "bloque": [1, 0], "lado": "S", "pos": 36, "a_mapa": "puerto_bravo", "a_lugar": "pb_salida_valdeolmos", "km": 31, "horas": 0.8, "desc": "La carretera que baja hasta Puerto Bravo entre viñedos."},
            {"id": "vo_estacion", "nombre": "Parada del autobús de Valdeolmos", "tipo": "estacion", "bloque": [0, 0], "lado": "N", "pos": 20, "precio": 22, "desc": "Una parada con un banco de piedra bajo un olmo."},
            {"id": "vo_bodega", "nombre": "Bodegas Hermanos Olmedo", "tipo": "taberna", "bloque": [2, 1], "lado": "S", "pos": 36, "desc": "Vino de la casa, partidas de dados y gente que sabe todo lo que pasa en el valle."},
            {"id": "vo_cooperativa", "nombre": "Cooperativa Vinícola", "tipo": "negocio", "bloque": [2, 0], "lado": "N", "pos": 36, "sonido": "lugar_taller", "precio": 18000, "ingresos": 430, "desc": "La cooperativa del pueblo, en venta desde que se jubiló el presidente."},
            {"id": "vo_meson", "nombre": "Mesón del Lagar", "tipo": "comida", "bloque": [0, 0], "lado": "E", "pos": 36, "desc": "Cordero asado y vino del año."},
            {"id": "vo_tienda", "nombre": "Colmado de la Plaza", "tipo": "tienda", "surtidor": True, "bloque": [0, 1], "lado": "S", "pos": 36, "desc": "Una tienda de pueblo donde hay de todo y se fía hasta fin de mes."},
            {"id": "vo_armeria", "nombre": "Armería del Coto", "tipo": "armeria", "bloque": [1, 1], "lado": "S", "pos": 36, "desc": "Escopetas de caza, cartuchos y hoces bien afiladas."},
            {"id": "vo_botica", "nombre": "Botica de Valdeolmos", "tipo": "farmacia", "bloque": [0, 1], "lado": "E", "pos": 36, "desc": "La botica de siempre, con su báscula de hierro."},
            {"id": "vo_taller", "nombre": "Taller Agrícola Ruedas", "tipo": "taller", "bloque": [2, 0], "lado": "O", "pos": 36, "desc": "Arreglan tractores, y lo que les lleves."},
            {"id": "vo_casa", "nombre": "Casa del viñador", "tipo": "casa", "bloque": [1, 1], "lado": "O", "pos": 36, "precio": 5200, "garaje": 3, "desc": "Una casa de piedra con lagar y cochera para tres vehículos."},
            {"id": "vo_empleo", "nombre": "Sindicato Agrario, bolsa de trabajo", "tipo": "empleo", "bloque": [1, 1], "lado": "E", "pos": 36, "desc": "Jornadas de vendimia y oficios del campo."},
            {"id": "vo_escuela", "nombre": "Escuela de Capataces", "tipo": "academia", "bloque": [2, 1], "lado": "O", "pos": 36, "cursos": ["conduccion", "resistencia"], "desc": "Cursos de conducción de maquinaria y de resistencia."},
            {"id": "vo_parroquia", "nombre": "Despensa de la Parroquia", "tipo": "ong", "bloque": [0, 1], "lado": "N", "pos": 36, "desc": "Reparten comida y ropa. Siempre hacen falta manos."},
            {"id": "vo_hostal", "nombre": "Posada del Olmo", "tipo": "hotel", "bloque": [2, 1], "lado": "N", "pos": 36, "precio_noche": 30, "desc": "Camas de lana y silencio de pueblo."},
            {"id": "vo_circuito", "nombre": "Salida de la carrera de tractores", "tipo": "carrera", "bloque": [0, 0], "lado": "O", "pos": 36, "desc": "En fiestas se corre con lo que tenga ruedas."},
            {"id": "vo_plaza", "nombre": "Plaza del Olmo", "tipo": "monumento", "bloque": [1, 0], "xy": [36, 40], "sonido": "lugar_fuente", "desc": "Un olmo centenario y un caño de agua helada."},
            {"id": "vo_ermita", "nombre": "Ermita de San Roque", "tipo": "monumento", "bloque": [2, 2], "xy": [45, 45], "sonido": "lugar_iglesia", "desc": "Una ermita blanca entre viñas, con una campana que avisa de las tormentas."},
            {"id": "vo_rio", "nombre": "Poza del río Olmedilla", "tipo": "pesca", "bloque": [0, 2], "xy": [40, 40], "sonido": "lugar_rio", "agua": "rio", "desc": "Truchas y barbos en agua limpia."},
            {"id": "vo_vina", "nombre": "Viña Vieja", "tipo": "monumento", "bloque": [1, 2], "xy": [36, 36], "desc": "Las cepas más viejas del valle, retorcidas como manos."},
        ],
        "casetes": [[60, 120], [200, 230]],
    }
    misiones = [
        {"id": "vo01", "titulo": "Vendimia", "capitulo": 24, "contacto": "Aurelio", "lugar": "vo_bodega", "requiere": ["m01"],
         "resumen": "En Bodegas Hermanos Olmedo falta gente para sacar la uva antes de la tormenta.",
         "pasos": [D(("Aurelio", "Viene tormenta y tengo media cosecha en la Viña Vieja. ¿Sabes llevar un tractor? Da igual, se aprende."),
                     ("Aurelio", "Coge el tractor con el remolque en la Cooperativa y tráelo entero al Taller, que hay que cambiarle una rueda antes de cargar.")),
                   {"tipo": "robar", "lugar": "vo_cooperativa", "modelo": "vo_remolque", "nombre": "el tractor con remolque", "abierto": True, "texto": "Recoge el tractor con remolque junto a la Cooperativa Vinícola."},
                   {"tipo": "entregar", "lugar": "vo_taller", "salud_min": 70, "texto": "Llévalo al Taller Agrícola Ruedas sin golpearlo."},
                   {"tipo": "ir", "lugar": "vo_vina", "radio": 16, "limite": 200, "texto": "Corre a la Viña Vieja antes de que empiece a llover. Tienes poco más de tres minutos."},
                   D(("Narrador", "Llegas con los primeros goterones. Entre seis cargáis las últimas cajas."),
                     ("Aurelio", "Buena mano tienes. Pásate mañana, que tengo otro asunto menos limpio."))],
         "recompensa": {"dinero": 350}},
        {"id": "vo02", "titulo": "Vino aguado", "capitulo": 24, "contacto": "Aurelio", "lugar": "vo_bodega", "requiere": ["vo01"],
         "resumen": "Alguien está vendiendo vino falso con la etiqueta de los Olmedo.",
         "pasos": [D(("Aurelio", "Me están hundiendo. Sale de aquí un camión con vino de garrafa y mi etiqueta. Carga en la ermita, de noche."),
                     ("Aurelio", "Toma la escopeta de mi padre. No quiero muertos si se puede evitar, pero tampoco quiero que te maten.")),
                   {"tipo": "dar", "arma": "vo_escopeta", "balas": 10},
                   {"tipo": "eliminar", "lugar": "vo_ermita", "texto": "Ve a la Ermita de San Roque y acaba con los que cargan el vino falso.",
                    "enemigos": [{"n": 2, "tipo": "Mozo de carga", "arma": "vo_hoz", "salud": 55}, {"n": 1, "tipo": "Capataz", "arma": "pistola", "salud": 80}]},
                   {"tipo": "recoger", "lugar": "vo_ermita", "objeto": "el rollo de etiquetas falsas", "texto": "Recoge el rollo de etiquetas falsas."},
                   D(("Narrador", "Las etiquetas llevan el sello de una imprenta de Puerto Bravo. Alguien de la ciudad paga todo esto."))],
         "recompensa": {"dinero": 700, "arma": "vo_escopeta", "balas": 8}},
        {"id": "vo03", "titulo": "El camión de las garrafas", "capitulo": 24, "contacto": "Aurelio", "lugar": "vo_bodega", "requiere": ["vo02"],
         "resumen": "El último camión de vino falso sale hoy del valle.",
         "pasos": [D(("Aurelio", "Sale el último camión, por la carretera de Puerto Bravo. Si lo paras, se acabó. La Guardia Civil va a preguntar, así que no te quedes cerca.")),
                   {"tipo": "dar", "balas_arma": "vo_escopeta", "balas": 12},
                   {"tipo": "perseguir", "lugar": "vo_salida", "modelo": "camion" if "camion" in VEHICULOS else "utilitario", "nombre": "el camión de las garrafas", "salud": 260, "limite": 320,
                    "texto": "Alcanza y destroza el camión de las garrafas antes de que salga del valle."},
                   {"tipo": "policia", "nivel": 2, "texto": "Han dado el aviso. Despista a la Guardia Civil."},
                   {"tipo": "recoger", "aqui": True, "objeto": "el albarán del camión", "texto": "Recoge el albarán que ha quedado en la cuneta."},
                   D(("Aurelio", "El valle es de quien lo trabaja. Toma, y la escopeta te la quedas."),
                     ("Narrador", "En el albarán hay un nombre conocido: Belmonte.")),
                   {"tipo": "dar", "dinero": 300}],
         "recompensa": {"dinero": 1500, "chaleco": True}},
        {"id": "vo04", "titulo": "Reparto de la cooperativa", "capitulo": 25, "contacto": "La presidenta", "lugar": "vo_cooperativa", "requiere": ["m01"],
         "resumen": "Trabajo honrado: llevar pedidos por el pueblo.",
         "pasos": [D(("La presidenta", "Tres cajas: una al Mesón, otra a la Posada y otra a la Despensa de la Parroquia, que esa va de regalo.")),
                   {"tipo": "ir", "lugar": "vo_meson", "texto": "Lleva la primera caja al Mesón del Lagar."},
                   {"tipo": "ir", "lugar": "vo_hostal", "texto": "Lleva la segunda a la Posada del Olmo."},
                   {"tipo": "ir", "lugar": "vo_parroquia", "limite": 150, "texto": "Y la tercera a la Despensa de la Parroquia, antes de que cierren."},
                   D(("Narrador", "El cura te da las gracias y una bendición que no has pedido."))],
         "recompensa": {"dinero": 280}},
    ]
    return {
        "info": {"nombre": "Valdeolmos", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Un pueblo de viñas al norte de Puerto Bravo: tres misiones sobre un fraude de vino, un encargo honrado, una carrera de tractores, pesca de río, una escopeta de caza, una hoz, un tractor con remolque, un todoterreno de campo y un personaje."},
        "capitulos": {"24": "Valdeolmos", "25": "Valdeolmos: vida honrada"},
        "mapas": [mapa],
        "lugares": [{"id": "pb_salida_valdeolmos", "mapa": "puerto_bravo", "nombre": "Salida noreste, carretera de Valdeolmos", "tipo": "salida", "bloque": [9, 6], "lado": "E", "pos": 36,
                     "a_mapa": "valdeolmos", "a_lugar": "vo_salida", "km": 31, "horas": 0.8, "desc": "La carretera que sube entre viñedos hasta Valdeolmos."}],
        "misiones": misiones,
        "armas": [clon(ARMAS, escopeta, id="vo_escopeta", nombre="Escopeta de caza paralela", dano=62, alcance=22, cadencia=0.9, precio=950, desc="Dos cañones, largo alcance para ser escopeta y un retroceso que se nota."),
                  clon(ARMAS, cuerpo, id="vo_hoz", nombre="Hoz de vendimia", dano=26, alcance=2.4, cadencia=0.5, precio=30, desc="Corta racimos y lo que haga falta.")],
        "vehiculos": [clon(VEHICULOS, tractor, id="vo_remolque", nombre="Tractor con remolque", vel_max=13, salud=260, valor=900, precio=6000, desc="Lento como una procesión y duro como una piedra."),
                      clon(VEHICULOS, todo, id="vo_campero", nombre="Todoterreno campero", vel_max=26, salud=200, valor=1200, precio=7800, desc="Un todoterreno viejo de los que arrancan siempre.")],
        "carreras": [{"id": "vo_c1", "nombre": "Carrera de las viñas", "mapa": "valdeolmos", "premio": 300, "tiempo": 85, "puntos": [[0, 1], [3, 1], [3, 3], [0, 3], [0, 1]]}],
        "comidas": [{"nombre": "Cordero asado", "precio": 16, "salud": 50}, {"nombre": "Vaso de mosto", "precio": 2, "salud": 6}],
        "peces": [{"nombre": "una trucha del Olmedilla", "valor": 30, "peso": 14, "aguas": ["rio"], "mapas": ["valdeolmos"]}, {"nombre": "un barbo", "valor": 18, "peso": 20, "aguas": ["rio"]}],
        "personajes": [{"id": "vo_ines", "nombre": "Inés", "genero": "m", "apellido": "Olmedo", "conduccion": 2, "resistencia": 4, "salud_max": 110, "ciudadania": 35, "arma": "vo_hoz", "botiquines": 1,
                        "desc": "Hija de viñadores, acostumbrada a trabajar de sol a sol. Empieza con resistencia al nivel cuatro, algo más de salud, una hoz y buen nombre entre los vecinos."}],
    }


# ============================================================ Motor y asfalto
def motor():
    dep = "deportivo" if "deportivo" in VEHICULOS else "utilitario"
    moto = "moto" if "moto" in VEHICULOS else "utilitario"
    return {
        "info": {"nombre": "Motor y asfalto", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Para quien solo quiere conducir: tres coches y una moto nuevos, un concesionario y un taller de preparación, tres carreras por Puerto Bravo, un piloto para elegir y dos misiones al volante."},
        "capitulos": {"26": "Motor y asfalto"},
        "lugares": [
            {"id": "ma_escuderia", "mapa": "puerto_bravo", "nombre": "Escudería Viento Sur", "tipo": "concesionario", "bloque": [8, 5], "lado": "S", "pos": 20, "modelos": ["ma_gt", "ma_rally", "ma_clasico", "ma_cafe"], "desc": "Coches preparados para correr. Se oye un motor al ralentí en el taller del fondo."},
            {"id": "ma_boxes", "mapa": "puerto_bravo", "nombre": "Boxes de la Escudería", "tipo": "taller", "bloque": [8, 5], "lado": "E", "pos": 36, "desc": "Reparan y pintan en lo que tardas en tomarte un café."},
            {"id": "ma_parrilla", "mapa": "puerto_bravo", "nombre": "Parrilla de salida de la Ronda", "tipo": "carrera", "bloque": [8, 6], "lado": "S", "pos": 36, "desc": "Aquí se queda para las carreras de la Escudería."},
            {"id": "ma_autoescuela", "mapa": "puerto_bravo", "nombre": "Escuela de Pilotos Viento Sur", "tipo": "academia", "bloque": [8, 6], "lado": "O", "pos": 36, "cursos": ["conduccion"], "desc": "Cursos de conducción deportiva en circuito cerrado."},
        ],
        "vehiculos": [
            clon(VEHICULOS, dep, id="ma_gt", nombre="Viento GT", vel_max=46, acel=11.5, freno=20, salud=110, tono=1.3, valor=9000, precio=78000, desc="El coche más rápido de la comarca. Frena tarde y acelera pronto."),
            clon(VEHICULOS, "utilitario", id="ma_rally", nombre="Brisa Rally", vel_max=34, acel=10.0, freno=19, salud=150, tono=1.35, valor=2500, precio=16500, desc="Un utilitario preparado: no corre tanto, pero sale de las curvas como un tiro."),
            clon(VEHICULOS, "utilitario", id="ma_clasico", nombre="Clásico Seiscientos Especial", vel_max=22, acel=5.0, freno=11, salud=90, tono=1.5, valor=3000, precio=9000, desc="Pequeño, ruidoso y con más encanto que caballos."),
            clon(VEHICULOS, moto, id="ma_cafe", nombre="Moto Café Racer", vel_max=40, acel=12.0, salud=65, valor=2200, precio=14000, desc="Una moto ligera y rapidísima. Un golpe y al suelo."),
        ],
        "carreras": [
            {"id": "ma_c1", "nombre": "Gran Premio de la Ronda", "mapa": "puerto_bravo", "premio": 900, "tiempo": 110, "puntos": [[8, 6], [10, 6], [10, 2], [6, 2], [6, 6], [8, 6]]},
            {"id": "ma_c2", "nombre": "Contrarreloj del Paseo Marítimo", "mapa": "puerto_bravo", "premio": 600, "tiempo": 70, "puntos": [[8, 6], [8, 1], [1, 1], [1, 3]]},
            {"id": "ma_c3", "nombre": "Vuelta larga a Puerto Bravo", "mapa": "puerto_bravo", "premio": 1500, "tiempo": 170, "puntos": [[8, 6], [10, 6], [10, 1], [0, 1], [0, 8], [8, 8], [8, 6]]},
        ],
        "personajes": [{"id": "ma_leo", "nombre": "Leo", "genero": "h", "apellido": "Carrasco", "conduccion": 6, "dinero": 100, "ganzuas": 1, "botiquines": 1,
                        "desc": "Probador de la Escudería Viento Sur hasta que estrelló el coche del jefe. Empieza con la conducción al nivel seis: nadie conduce mejor. A cambio, casi no tiene dinero."}],
        "misiones": [
            {"id": "ma01", "titulo": "Coche de pruebas", "capitulo": 26, "contacto": "Paula", "lugar": "ma_escuderia", "requiere": ["m01"],
             "resumen": "La jefa de la Escudería Viento Sur busca un probador.",
             "pasos": [D(("Paula", "¿Tú eres Dani? Dicen que conduces sin romper nada. Tengo un Brisa Rally recién montado y un cliente esperando en el concesionario Autos Platino."),
                         ("Paula", "Llévaselo en tres minutos y sin un rasguño. Si llega bien, hay más trabajo.")),
                       {"tipo": "robar", "lugar": "ma_boxes", "modelo": "ma_rally", "nombre": "el Brisa Rally de pruebas", "abierto": True, "texto": "Recoge el Brisa Rally junto a los Boxes de la Escudería."},
                       {"tipo": "entregar", "lugar": "concesionario", "salud_min": 85, "limite": 180, "texto": "Llévalo a Autos Platino en tres minutos y casi intacto."},
                       D(("Narrador", "El cliente da una vuelta alrededor del coche, pasa un dedo por el capó y asiente."))],
             "recompensa": {"dinero": 500}},
            {"id": "ma02", "titulo": "El que no paga", "capitulo": 26, "contacto": "Paula", "lugar": "ma_escuderia", "requiere": ["ma01"],
             "resumen": "Un cliente se ha llevado un Viento GT sin pagar.",
             "pasos": [D(("Paula", "El del Viento GT se ha ido sin pagar. Sale por la carretera del norte. No quiero el coche roto, pero prefiero roto a perdido.")),
                       {"tipo": "perseguir", "lugar": "salida_norte", "modelo": "ma_gt", "nombre": "el Viento GT robado", "salud": 180, "limite": 240, "texto": "Alcanza el Viento GT y páralo a golpes antes de cuatro minutos."},
                       {"tipo": "ir", "lugar": "ma_escuderia", "texto": "Vuelve a la Escudería Viento Sur."},
                       D(("Paula", "Chapa y pintura, tres días. Mejor eso que nada. Toma lo tuyo."))],
             "recompensa": {"dinero": 1200}},
        ],
    }

# ============================================================ Peñas Altas
def penas_altas():
    cuerpo = primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    explosivo = "granada" if "granada" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "explosivo")
    carabina = "carabina" if "carabina" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    quad = "quad" if "quad" in VEHICULOS else "utilitario"
    camion = "camion" if "camion" in VEHICULOS else "utilitario"
    cross = "cross" if "cross" in VEHICULOS else "utilitario"
    todo = "todoterreno" if "todoterreno" in VEHICULOS else "utilitario"
    mapa = {
        "id": "penas_altas", "tipo": "pueblo", "nombre": "Peñas Altas", "trafico": 1, "peatones": 3, "nombre_objeto": "Pepita de pirita",
        "avenidas": ["Cuesta de la Mina", "Calle de los Barreneros", "Calle del Castillete", "Camino del Collado"],
        "calles": ["Carretera de Puerto Bravo", "Calle de la Fragua", "Calle del Lavadero", "Senda del Lago"],
        "barrios": [
            {"id": "pa_pueblo", "nombre": "Peñas Altas", "i": [0, 2], "j": [0, 1], "ambiente": "amb_montana", "vehiculos": [todo, "pa_quad", "pa_volquete", "utilitario"],
             "descripcion": "Peñas Altas, un pueblo minero colgado de la sierra. Casas de pizarra, humo de chimenea y un castillete de hierro que se ve desde todo el valle."},
            {"id": "pa_lago", "nombre": "El Lago Negro", "i": [0, 2], "j": [2, 2], "ambiente": "amb_montana", "vehiculos": [todo, "pa_trial"],
             "descripcion": "El Lago Negro: agua quieta y fría entre pinos, con la bocamina vieja en la ladera de enfrente."}],
        "bloques": {"1,0": "plaza", "0,2": "hierba", "1,2": "hierba", "2,2": "hierba"},
        "lugares": [
            {"id": "pa_salida", "nombre": "Salida sur, carretera de Puerto Bravo", "tipo": "salida", "bloque": [1, 0], "lado": "S", "pos": 36, "a_mapa": "puerto_bravo", "a_lugar": "pb_salida_penas", "km": 44, "horas": 1.1, "desc": "La carretera de curvas que baja de la sierra hasta Puerto Bravo."},
            {"id": "pa_estacion", "nombre": "Parada del autobús de Peñas Altas", "tipo": "estacion", "bloque": [0, 0], "lado": "N", "pos": 20, "precio": 28, "desc": "Una marquesina de pizarra frente a la fragua."},
            {"id": "pa_cantina", "nombre": "Cantina del Barrenero", "tipo": "taberna", "bloque": [2, 0], "lado": "N", "pos": 36, "desc": "Vino caliente, dados y mineros jubilados que lo saben todo."},
            {"id": "pa_fonda", "nombre": "Fonda La Pizarra", "tipo": "comida", "bloque": [0, 0], "lado": "E", "pos": 36, "desc": "Potaje de la sierra y pan de horno de leña."},
            {"id": "pa_economato", "nombre": "Economato Minero", "tipo": "tienda", "surtidor": True, "bloque": [0, 1], "lado": "S", "pos": 36, "desc": "El economato de la antigua compañía. Sigue vendiendo de todo."},
            {"id": "pa_polvorin", "nombre": "Ferretería El Polvorín", "tipo": "armeria", "bloque": [1, 1], "lado": "S", "pos": 36, "desc": "Picos, carabinas de monte y, bajo el mostrador, lo que sobró de la mina."},
            {"id": "pa_botica", "nombre": "Botica de la Sierra", "tipo": "farmacia", "bloque": [0, 1], "lado": "E", "pos": 36, "desc": "Una botica pequeña con olor a eucalipto."},
            {"id": "pa_taller", "nombre": "Taller del Castillete", "tipo": "taller", "bloque": [2, 0], "lado": "O", "pos": 36, "desc": "Arreglan volquetes, quads y lo que suba hasta aquí."},
            {"id": "pa_banco", "nombre": "Caja de la Sierra", "tipo": "banco", "bloque": [1, 1], "lado": "N", "pos": 36, "desc": "Una ventanilla y un cajero que tarda en despertar."},
            {"id": "pa_casa", "nombre": "Casa del capataz", "tipo": "casa", "bloque": [1, 1], "lado": "O", "pos": 36, "precio": 4400, "garaje": 2, "desc": "Una casa de pizarra con estufa de leña y cochera para dos vehículos."},
            {"id": "pa_cantera", "nombre": "Cantera de pizarra", "tipo": "negocio", "bloque": [2, 1], "lado": "S", "pos": 36, "sonido": "lugar_mina", "precio": 26000, "ingresos": 610, "vehiculo": "pa_volquete", "desc": "La cantera sigue dando losa. Está en venta, con su volquete en la puerta: súbete y pulsa J para hacer portes."},
            {"id": "pa_empleo", "nombre": "Hermandad Minera, bolsa de trabajo", "tipo": "empleo", "bloque": [1, 1], "lado": "E", "pos": 36, "desc": "Jornadas en la cantera y oficios de la sierra."},
            {"id": "pa_escuela", "nombre": "Escuela de Montaña", "tipo": "academia", "bloque": [2, 1], "lado": "O", "pos": 36, "cursos": ["resistencia", "punteria"], "desc": "Cursos de resistencia y de tiro de montaña."},
            {"id": "pa_gimnasio", "nombre": "Frontón Cubierto", "tipo": "gimnasio", "bloque": [0, 1], "lado": "N", "pos": 36, "desc": "Pelota, pesas de hierro fundido y combates en fiestas."},
            {"id": "pa_cocina", "nombre": "Cocina de la Hermandad", "tipo": "ong", "bloque": [2, 1], "lado": "N", "pos": 36, "desc": "Dan de comer a los viejos mineros. Siempre faltan manos."},
            {"id": "pa_refugio", "nombre": "Refugio del Collado", "tipo": "hotel", "bloque": [2, 0], "lado": "E", "pos": 36, "precio_noche": 28, "desc": "Literas, mantas gordas y una chimenea que no se apaga."},
            {"id": "pa_motos", "nombre": "Motos y Quads Sierra Alta", "tipo": "concesionario", "bloque": [0, 0], "lado": "O", "pos": 36, "modelos": ["pa_quad", "pa_trial", "pa_volquete"], "desc": "Todo lo que sube por un pedregal."},
            {"id": "pa_circuito", "nombre": "Salida de la subida al Collado", "tipo": "carrera", "bloque": [2, 1], "lado": "E", "pos": 36, "desc": "Una carrera de montaña entre pinos."},
            {"id": "pa_helipuerto", "nombre": "Helipuerto de rescate", "tipo": "helipuerto", "bloque": [2, 2], "xy": [20, 20], "precio": 150, "desc": "Una losa de hormigón con una H pintada."},
            {"id": "pa_plaza", "nombre": "Plaza del Castillete", "tipo": "monumento", "bloque": [1, 0], "xy": [36, 40], "sonido": "lugar_fuente", "desc": "El castillete de la mina, oxidado, y una fuente de agua de deshielo."},
            {"id": "pa_bocamina", "nombre": "Bocamina de La Encantada", "tipo": "monumento", "bloque": [2, 2], "xy": [50, 50], "sonido": "lugar_mina", "desc": "La entrada de la mina vieja. Sale un aire frío que huele a hierro."},
            {"id": "pa_lago_pesca", "nombre": "Orilla del Lago Negro", "tipo": "pesca", "bloque": [0, 2], "xy": [40, 40], "sonido": "lugar_rio", "agua": "lago", "desc": "Truchas de lago y, con suerte, un lucio."},
            {"id": "pa_escombrera", "nombre": "Escombrera vieja", "tipo": "tesoro", "bloque": [1, 2], "xy": [36, 36], "desc": "Entre la escoria aún aparecen herramientas, monedas y alguna pepita."},
            {"id": "pa_lumbre", "nombre": "Bar de copas La Lumbre", "tipo": "club", "bloque": [0, 1], "lado": "O", "pos": 36, "adultos": True, "desc": "El único sitio abierto de noche en toda la sierra."},
            {"id": "pa_alambique", "nombre": "El Alambique", "tipo": "proveedor", "bloque": [2, 0], "lado": "S", "pos": 36, "adultos": True, "factor": {"hierba": 0.9, "polvo": 1.5, "pastillas": 1.2, "cristal": 1.5, "pa_endrinas": 0.7}, "desc": "Licor de endrinas casero y lo poco que sube de la ciudad."},
        ],
        "casetes": [[60, 60], [210, 130], [130, 230]],
    }
    misiones = [
        {"id": "pa01", "titulo": "Aire de sierra", "capitulo": 27, "contacto": "Fermín", "lugar": "pa_cantina", "requiere": ["m01"],
         "resumen": "En la Cantina del Barrenero, un minero jubilado dice que por la noche hay luces en la mina cerrada.",
         "pasos": [D(("Fermín", "Cuarenta años bajé a La Encantada, y te digo que esa mina está cerrada. Pues anoche había luces en la bocamina."),
                     ("Fermín", "A mí ya no me dan las piernas. Sube tú, mira y vuelve. Pago el vino.")),
                   {"tipo": "ir", "lugar": "pa_bocamina", "radio": 14, "texto": "Sube a la Bocamina de La Encantada, al noreste, junto al lago."},
                   {"tipo": "recoger", "lugar": "pa_bocamina", "objeto": "una lámpara de carburo todavía caliente", "texto": "Recoge la lámpara que hay en la entrada."},
                   D(("Narrador", "La lámpara está tibia y los raíles brillan: por aquí han pasado vagonetas esta misma noche."))],
         "recompensa": {"dinero": 220}},
        {"id": "pa02", "titulo": "El volquete de noche", "capitulo": 27, "contacto": "Fermín", "lugar": "pa_cantina", "requiere": ["pa01"],
         "resumen": "Un volquete baja cargado de la mina cuando el pueblo duerme.",
         "pasos": [D(("Fermín", "Sacan mineral a escondidas y lo bajan en un volquete de la cantera. Está aparcado en el Taller, cargado hasta arriba."),
                     ("Fermín", "Llévatelo a la puerta de la Hermandad Minera, que allí lo verá todo el pueblo por la mañana. Despacio, que pesa.")),
                   {"tipo": "robar", "lugar": "pa_taller", "modelo": "pa_volquete", "nombre": "el volquete cargado", "busqueda": 1, "texto": "Hazte con el volquete cargado junto al Taller del Castillete."},
                   {"tipo": "policia", "nivel": 1, "texto": "Alguien ha dado el aviso. Despista a la patrulla."},
                   {"tipo": "entregar", "lugar": "pa_empleo", "salud_min": 50, "texto": "Lleva el volquete a la Hermandad Minera sin destrozarlo."},
                   D(("Narrador", "Dejas el volquete atravesado delante de la puerta. Bajo la lona hay mineral, sí, y unas cajas con el sello de una naviera de Puerto Bravo."))],
         "recompensa": {"dinero": 550}},
        {"id": "pa03", "titulo": "Los de la galería tres", "capitulo": 27, "contacto": "Fermín", "lugar": "pa_cantina", "requiere": ["pa02"],
         "resumen": "Los que explotan la mina a escondidas han bajado al pueblo a buscar al que les robó el volquete.",
         "pasos": [D(("Fermín", "Han venido preguntando por ti. Están en la escombrera, esperando a que oscurezca."),
                     ("Fermín", "Toma mi carabina y dos cartuchos de los de antes. Con mecha corta, así que no te duermas.")),
                   {"tipo": "dar", "arma": "pa_carabina", "balas": 12},
                   {"tipo": "dar", "arma": "pa_dinamita", "balas": 2},
                   {"tipo": "eliminar", "lugar": "pa_escombrera", "texto": "Ve a la escombrera vieja y acaba con los de la galería tres.",
                    "enemigos": [{"n": 3, "tipo": "Barrenero furtivo", "arma": "pa_pico", "salud": 60}, {"n": 1, "tipo": "Encargado", "arma": "revolver", "salud": 90}]},
                   {"tipo": "recoger", "lugar": "pa_escombrera", "objeto": "el plano de las galerías", "texto": "Recoge el plano de las galerías."},
                   D(("Narrador", "El plano marca una galería nueva que pasa justo por debajo del lago. Si la abren, se inunda media mina y medio pueblo."))],
         "recompensa": {"dinero": 800, "arma": "pa_carabina", "balas": 10}},
        {"id": "pa04", "titulo": "Antes de que revienten el lago", "capitulo": 27, "contacto": "Fermín", "lugar": "pa_cantina", "requiere": ["pa03"],
         "resumen": "El ingeniero que dirige las voladuras huye sierra abajo con los detonadores.",
         "pasos": [D(("Fermín", "El ingeniero se ha asustado y se va con los detonadores en su todoterreno. Si llega abajo, vuelve con otra cuadrilla."),
                     ("Fermín", "Párale en la carretera. Después tira lo que lleve al lago.")),
                   {"tipo": "dar", "balas_arma": "pa_carabina", "balas": 10},
                   {"tipo": "perseguir", "lugar": "pa_salida", "modelo": todo, "nombre": "el todoterreno del ingeniero", "salud": 230, "limite": 300,
                    "texto": "Alcanza y destroza el todoterreno del ingeniero antes de cinco minutos."},
                   {"tipo": "recoger", "aqui": True, "objeto": "la caja de detonadores", "texto": "Recoge la caja de detonadores."},
                   {"tipo": "ir", "lugar": "pa_lago_pesca", "texto": "Lleva los detonadores a la orilla del Lago Negro y tíralos al agua."},
                   D(("Narrador", "La caja se hunde despacio. Arriba, en la bocamina, ya no hay luces."),
                     ("Fermín", "La Encantada vuelve a dormir. El quad de mi nieto es tuyo: está en el concesionario, pregunta por él.")),
                   {"tipo": "dar", "dinero": 400}],
         "recompensa": {"dinero": 1800, "chaleco": True}},
        {"id": "pa05", "titulo": "Losa para el tejado", "capitulo": 28, "contacto": "La hermana mayor", "lugar": "pa_cocina", "requiere": ["m01"],
         "resumen": "Trabajo honrado: la Cocina de la Hermandad tiene goteras y la cantera regala la pizarra.",
         "pasos": [D(("La hermana mayor", "Llueve dentro del comedor. La cantera nos da la losa, pero hay que ir a por ella."),
                     ("La hermana mayor", "Pasa por la cantera, luego por la ferretería a por clavos y vuelve antes de que empiece a nevar.")),
                   {"tipo": "ir", "lugar": "pa_cantera", "texto": "Ve a la Cantera de pizarra."},
                   {"tipo": "recoger", "lugar": "pa_polvorin", "objeto": "una caja de clavos de pizarrero", "texto": "Recoge los clavos en la Ferretería El Polvorín."},
                   {"tipo": "ir", "lugar": "pa_cocina", "limite": 170, "texto": "Vuelve a la Cocina de la Hermandad antes de que nieve. Tienes casi tres minutos."},
                   D(("Narrador", "Entre cuatro subís al tejado. A media tarde ya no gotea, y huele a potaje."))],
         "recompensa": {"dinero": 260}},
        {"id": "paa1", "titulo": "Endrinas para la ciudad", "capitulo": 29, "adultos": True, "contacto": "Olalla", "lugar": "pa_lumbre", "requiere": ["pa01"],
         "resumen": "En La Lumbre, Olalla quiere que alguien de fuera pruebe su licor.",
         "pasos": [D(("Olalla", "Lo destilo yo. Si gusta abajo, dejo de servir copas a cuatro mineros. Llévale estas botellas al del Refugio y quédate dos.")),
                   {"tipo": "dar", "sustancia": "pa_endrinas", "cantidad": 2},
                   {"tipo": "ir", "lugar": "pa_refugio", "texto": "Lleva las botellas al Refugio del Collado."},
                   D(("Narrador", "El guarda prueba un trago, tose y pide otra caja."))],
         "recompensa": {"dinero": 280, "afinidad": {"pa_olalla": 15}}},
    ]
    return {
        "info": {"nombre": "Peñas Altas", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Un pueblo minero en lo alto de la sierra: cuatro misiones sobre una mina que alguien explota a escondidas, un encargo honrado, una historia para adultos, carabina, pico y dinamita, un quad, una moto de trial y un volquete con el que hacer portes, una subida de montaña, pesca en el lago, búsqueda de tesoros y dos personajes."},
        "capitulos": {"27": "Peñas Altas", "28": "Peñas Altas: vida honrada", "29": "Peñas Altas: historias para adultos"},
        "mapas": [mapa],
        "lugares": [{"id": "pb_salida_penas", "mapa": "puerto_bravo", "nombre": "Salida norte, carretera de Peñas Altas", "tipo": "salida", "bloque": [7, 7], "lado": "N", "pos": 36,
                     "a_mapa": "penas_altas", "a_lugar": "pa_salida", "km": 44, "horas": 1.1, "desc": "La carretera de curvas que sube a la sierra, hasta Peñas Altas."}],
        "misiones": misiones,
        "armas": [clon(ARMAS, carabina, id="pa_carabina", nombre="Carabina de monte", dano=58, alcance=34, precision=0.88, precio=1100, desc="Ligera y precisa a mucha distancia. La de los guardas de la sierra."),
                  clon(ARMAS, cuerpo, id="pa_pico", nombre="Pico de minero", dano=34, alcance=2.6, cadencia=0.9, precio=45, desc="Pesa lo suyo y tarda en volver, pero donde cae, cae."),
                  clon(ARMAS, explosivo, id="pa_dinamita", nombre="Cartucho de dinamita", dano=130, precio=320, desc="De los que sobraron en el polvorín. Más potente que una granada: aléjate después de lanzarlo.")],
        "vehiculos": [clon(VEHICULOS, quad, id="pa_quad", nombre="Quad de montaña", vel_max=27, acel=8.0, salud=120, valor=900, precio=5600, desc="Sube por donde no sube nada más."),
                      clon(VEHICULOS, cross, id="pa_trial", nombre="Moto de trial", vel_max=29, acel=9.5, salud=70, valor=800, precio=4300, desc="Ligera como una bicicleta y con un motor que no se cala nunca."),
                      clon(VEHICULOS, camion, id="pa_volquete", nombre="Volquete de la cantera", vel_max=17, salud=320, valor=1500, precio=11000, trabajo="camion", desc="Un camión volquete lento y durísimo. Con la tecla J haces portes entre localidades.")],
        "carreras": [{"id": "pa_c1", "nombre": "Subida al Collado", "mapa": "penas_altas", "premio": 380, "tiempo": 90, "puntos": [[3, 1], [3, 3], [0, 3], [0, 1], [3, 1]]}],
        "comidas": [{"nombre": "Potaje de la sierra", "precio": 11, "salud": 42}, {"nombre": "Vino caliente con miel", "precio": 4, "salud": 9}],
        "objetos": [{"id": "pa_lampara", "nombre": "Lámpara de minero", "precio": 35, "desc": "Una lámpara de carburo restaurada. De recuerdo."}],
        "peces": [{"nombre": "una trucha del Lago Negro", "valor": 34, "peso": 14, "aguas": ["lago"], "mapas": ["penas_altas"]}, {"nombre": "un lucio", "valor": 70, "peso": 4, "aguas": ["lago", "rio"]}],
        "personajes": [
            {"id": "pa_berta", "nombre": "Berta", "genero": "m", "apellido": "Lombao", "resistencia": 5, "salud_max": 115, "ciudadania": 25, "arma": "pa_pico", "botiquines": 1, "dinero": 120,
             "desc": "Barrenera, como su madre. Empieza con resistencia al nivel cinco, más salud de lo normal, un pico de minero y poco dinero."},
            {"id": "pa_goyo", "nombre": "Goyo", "genero": "h", "apellido": "Peñalba", "punteria": 4, "conduccion": 2, "arma": "pa_carabina", "balas": 12, "dinero": 200,
             "desc": "Guarda de la sierra hasta que cerraron el coto. Empieza con puntería al nivel cuatro, una carabina de monte con doce balas y doscientos euros."}],
        "personas": [{"id": "pa_olalla", "nombre": "Olalla", "edad": 37, "lugar": "pa_lumbre", "gustos": ["pa_lago_noche", "copas"], "regalo": "pa_manta",
                      "desc": "Volvió de la ciudad para llevar el bar de su padre. Destila su propio licor, lee en la barra cuando no hay nadie y dice las cosas una sola vez."}],
        "actividades": [{"id": "pa_lago_noche", "nombre": "Ver las estrellas desde el Lago Negro", "precio": 10, "horas": 3}],
        "regalos": [{"id": "pa_manta", "nombre": "Una manta de lana de la sierra", "precio": 90, "afinidad": 11}],
        "sustancias": [clon(SUSTANCIAS, "alcohol", id="pa_endrinas", nombre="Licor de endrinas", unidad="botella", precio=16, animo=8, adiccion=1.8, sobredosis=4,
                            desc="Licor casero de endrinas de la sierra. Dulce, engañoso y más fuerte de lo que parece.")],
    }


# ============================================================ Isla de los Vientos
def isla_vientos():
    cuerpo = primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    ballesta = "ballesta" if "ballesta" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    cat = "catamaran" if "catamaran" in VEHICULOS else primero(VEHICULOS, lambda v: v.get("barco"))
    moto_agua = "moto_agua" if "moto_agua" in VEHICULOS else primero(VEHICULOS, lambda v: v.get("barco"))
    mapa = {
        "id": "isla_vientos", "tipo": "isla", "nombre": "Isla de los Vientos", "trafico": 0, "peatones": 2, "policia": False, "aparcados": False, "nombre_objeto": "Concha nacarada",
        "avenidas": ["Sendero de Barlovento", "Sendero del Aljibe", "Sendero de Sotavento"],
        "calles": ["Senda del Muelle", "Senda de las Salinas", "Senda del Semáforo"],
        "barrios": [{"id": "iv_isla", "nombre": "Isla de los Vientos", "i": [0, 1], "j": [0, 1], "ambiente": "amb_playa", "vehiculos": [],
                     "descripcion": "La Isla de los Vientos: salinas abandonadas, dunas, cuatro casas de pescadores y un viento que no para nunca. Sin coches y sin policía."}],
        "bloques": {"0,0": "muelle", "1,0": "arena", "0,1": "hierba", "1,1": "arena"},
        "lugares": [
            {"id": "iv_muelle", "nombre": "Muelle de las Salinas", "tipo": "embarcadero", "bloque": [0, 0], "lado": "S", "pos": 36, "a_mapa": "mar", "a_lugar": "mar_vientos", "desc": "Un muelle de piedra donde antes cargaban la sal."},
            {"id": "iv_cantina", "nombre": "Cantina del Salinero", "tipo": "taberna", "bloque": [1, 0], "lado": "N", "pos": 36, "desc": "Dados, ron de caña y los cuatro vecinos de la isla."},
            {"id": "iv_fogon", "nombre": "El Fogón de Barlovento", "tipo": "comida", "bloque": [0, 0], "lado": "N", "pos": 36, "desc": "Pescado a la sal, como se ha hecho siempre aquí."},
            {"id": "iv_almacen", "nombre": "Almacén de la Isla", "tipo": "tienda", "bloque": [0, 0], "lado": "E", "pos": 36, "desc": "Lo que trae la barca del martes, y poco más."},
            {"id": "iv_efectos", "nombre": "Efectos de pesca Sotavento", "tipo": "armeria", "bloque": [1, 0], "lado": "O", "pos": 36, "desc": "Garfios, fusiles de pesca submarina y cuchillos de desescamar."},
            {"id": "iv_casa", "nombre": "Casa del salinero", "tipo": "casa", "bloque": [0, 1], "lado": "S", "pos": 36, "precio": 9500, "garaje": 0, "desc": "Una casa baja de piedra, encalada, con un aljibe y vistas a todo el mar."},
            {"id": "iv_salinas", "nombre": "Salinas de Poniente", "tipo": "negocio", "bloque": [1, 1], "lado": "S", "pos": 36, "sonido": "gaviota", "precio": 14000, "ingresos": 340, "desc": "Las salinas se pueden volver a poner en marcha. Dan dinero cada medianoche."},
            {"id": "iv_posada", "nombre": "Posada del Semáforo", "tipo": "hotel", "bloque": [0, 1], "lado": "E", "pos": 36, "precio_noche": 40, "desc": "El antiguo semáforo marítimo, convertido en posada de seis camas."},
            {"id": "iv_nautica", "nombre": "Varadero de la Isla", "tipo": "nautica", "bloque": [0, 0], "lado": "O", "pos": 36, "embarcadero": "iv_muelle", "desc": "Venden y reparan barcos. Los dejan amarrados en el muelle."},
            {"id": "iv_helipuerto", "nombre": "Explanada del Semáforo", "tipo": "helipuerto", "bloque": [0, 1], "xy": [20, 20], "precio": 220, "desc": "Una explanada de tierra batida por el viento."},
            {"id": "iv_semaforo", "nombre": "Torre del Semáforo", "tipo": "monumento", "bloque": [0, 1], "xy": [50, 50], "sonido": "lugar_iglesia", "desc": "Desde aquí se avisaba a los barcos con banderas. La campana de niebla sigue sonando."},
            {"id": "iv_aljibe", "nombre": "El Aljibe", "tipo": "monumento", "bloque": [1, 1], "xy": [20, 50], "sonido": "lugar_fuente", "desc": "La única agua dulce de la isla."},
            {"id": "iv_rompiente", "nombre": "Rompiente de Barlovento", "tipo": "pesca", "bloque": [1, 0], "xy": [55, 15], "desc": "Sargos, lubinas y, en noches de luna, alguna morena."},
            {"id": "iv_dunas", "nombre": "Dunas del Naufragio", "tipo": "tesoro", "bloque": [1, 1], "xy": [50, 20], "desc": "Aquí encalló un mercante hace cien años. La arena aún devuelve cosas."},
        ],
        "casetes": [[30, 140], [150, 40], [150, 150]],
    }
    misiones = [
        {"id": "iv01", "titulo": "La barca del martes", "capitulo": 30, "contacto": "Chelo", "lugar": "iv_cantina", "requiere": ["m01"],
         "resumen": "En la Cantina del Salinero, Chelo dice que la barca de los víveres lleva dos semanas sin venir.",
         "pasos": [D(("Chelo", "La barca del martes no viene desde hace dos martes. Y anoche vi un fuego en las dunas."),
                     ("Chelo", "Tú que tienes piernas, acércate a mirar. Yo de aquí no me muevo, que alguien tiene que guardar el ron.")),
                   {"tipo": "ir", "lugar": "iv_dunas", "radio": 14, "texto": "Ve a las Dunas del Naufragio, al este de la isla."},
                   {"tipo": "recoger", "lugar": "iv_dunas", "objeto": "un bidón con el nombre de la barca", "texto": "Recoge el bidón medio enterrado."},
                   D(("Narrador", "El bidón es de la barca de los víveres. Alguien la ha vaciado aquí, y no fueron las gaviotas."))],
         "recompensa": {"dinero": 240}},
        {"id": "iv02", "titulo": "Raqueros", "capitulo": 30, "contacto": "Chelo", "lugar": "iv_cantina", "requiere": ["iv01"],
         "resumen": "Unos raqueros asaltan las barcas pequeñas y esconden el botín en la isla.",
         "pasos": [D(("Chelo", "Raqueros. Mi abuelo los colgaba del semáforo. Tú no hace falta que llegues a tanto."),
                     ("Chelo", "Duermen en las salinas. Toma el fusil de pesca de mi marido: no hace ruido.")),
                   {"tipo": "dar", "arma": "iv_fusil", "balas": 10},
                   {"tipo": "eliminar", "lugar": "iv_salinas", "texto": "Ve a las Salinas de Poniente y acaba con los raqueros.",
                    "enemigos": [{"n": 2, "tipo": "Raquero", "arma": "iv_garfio", "salud": 55}, {"n": 1, "tipo": "Patrón raquero", "arma": "pistola", "salud": 85}]},
                   {"tipo": "recoger", "lugar": "iv_salinas", "objeto": "la llave del pañol", "texto": "Recoge la llave que llevaba el patrón."},
                   D(("Narrador", "La llave abre el pañol del semáforo. Dentro están los víveres de dos semanas y el barquero, atado y furioso."))],
         "recompensa": {"dinero": 650, "arma": "iv_fusil", "balas": 8}},
        {"id": "iv03", "titulo": "Campana de niebla", "capitulo": 30, "contacto": "Chelo", "lugar": "iv_cantina", "requiere": ["iv02"],
         "resumen": "Vuelven más raqueros, de noche y con niebla.",
         "pasos": [D(("Chelo", "Vuelven los que faltaban, y con esta niebla no se ve ni el muelle. Sube al semáforo y toca la campana: los vecinos saben lo que significa."),
                     ("Chelo", "Después baja al muelle y recíbelos como se merecen.")),
                   {"tipo": "ir", "lugar": "iv_semaforo", "limite": 120, "texto": "Sube a la Torre del Semáforo y toca la campana. Tienes dos minutos."},
                   {"tipo": "dar", "balas_arma": "iv_fusil", "balas": 10},
                   {"tipo": "eliminar", "lugar": "iv_muelle", "texto": "Baja al Muelle de las Salinas y rechaza el desembarco.",
                    "enemigos": [{"n": 3, "tipo": "Raquero", "arma": "iv_garfio", "salud": 60}, {"n": 1, "tipo": "El Sordo", "arma": "escopeta", "salud": 110}]},
                   D(("Narrador", "Cuando levanta la niebla, la barca de los raqueros se aleja a la deriva, vacía."),
                     ("Chelo", "Ya puedes decir que eres de la isla. El catamarán del varadero es tuyo: lo dejó a deber uno que ya no va a volver.")),
                   {"tipo": "dar", "dinero": 300}],
         "recompensa": {"dinero": 1400, "barco": {"modelo": "iv_catamaran", "en": "iv_muelle"}}},
        {"id": "iv04", "titulo": "Sal para el fogón", "capitulo": 31, "contacto": "El cocinero", "lugar": "iv_fogon", "requiere": ["m01"],
         "resumen": "Trabajo honrado: recados por la isla antes de que llegue la barca de los turistas.",
         "pasos": [D(("El cocinero", "Me quedo sin sal en una isla de salinas, tiene gracia. Tráeme un saco de las salinas y agua del aljibe.")),
                   {"tipo": "recoger", "lugar": "iv_salinas", "objeto": "un saco de sal gorda", "texto": "Recoge un saco de sal en las Salinas de Poniente."},
                   {"tipo": "ir", "lugar": "iv_aljibe", "texto": "Pasa por El Aljibe a llenar la garrafa."},
                   {"tipo": "ir", "lugar": "iv_fogon", "limite": 150, "texto": "Vuelve a El Fogón de Barlovento antes de que atraque la barca."},
                   D(("El cocinero", "Justo a tiempo. Siéntate, que hoy comes aquí y no pagas."))],
         "recompensa": {"dinero": 230}},
    ]
    return {
        "info": {"nombre": "Isla de los Vientos", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "Una isla nueva en el Mar de Poniente, a la que se llega navegando: tres misiones contra unos raqueros, un encargo honrado, una casa, unas salinas que dan dinero, pesca, búsqueda de tesoros, un fusil de pesca silencioso, un garfio, un catamarán, una moto de agua y un personaje marinero."},
        "capitulos": {"30": "Isla de los Vientos", "31": "Isla de los Vientos: vida honrada"},
        "mapas": [mapa],
        "lugares": [{"id": "mar_vientos", "mapa": "mar", "nombre": "Muelle de la Isla de los Vientos, desde el mar", "tipo": "muelle", "xy": [2000, 700], "a_mapa": "isla_vientos", "a_lugar": "iv_muelle",
                     "desc": "El muelle de piedra de la Isla de los Vientos, mar adentro, al este."}],
        "misiones": misiones,
        "armas": [clon(ARMAS, ballesta, id="iv_fusil", nombre="Fusil de pesca submarina", dano=70, alcance=20, precio=700, balas=8, precio_balas=45, desc="Dispara varillas de acero. Silencioso y lento de recargar."),
                  clon(ARMAS, cuerpo, id="iv_garfio", nombre="Garfio de estibador", dano=28, alcance=2.2, cadencia=0.55, precio=35, desc="Para mover fardos. Y para lo que haga falta.")],
        "vehiculos": [clon(VEHICULOS, cat, id="iv_catamaran", nombre="Catamarán Alisio", vel_max=21, salud=170, precio=19000, trabajo="mensajeria", desc="Dos cascos, mucha vela y casi nada de ruido. Con la tecla J haces mensajería entre muelles."),
                      clon(VEHICULOS, moto_agua, id="iv_moto", nombre="Moto de agua Levante", vel_max=31, salud=60, precio=6800, desc="Rápida, nerviosa y frágil.")],
        "comidas": [{"nombre": "Lubina a la sal", "precio": 15, "salud": 48}, {"nombre": "Ron de caña con limón", "precio": 4, "salud": 8}],
        "objetos": [{"id": "iv_sal", "nombre": "Saquito de flor de sal", "precio": 12, "desc": "Sal de la isla. De regalo queda muy bien."}],
        "peces": [{"nombre": "una lubina de rompiente", "valor": 44, "peso": 10, "aguas": ["mar"], "mapas": ["isla_vientos"]}, {"nombre": "una morena", "valor": 62, "peso": 4, "aguas": ["mar"]}, {"nombre": "un sargo", "valor": 20, "peso": 18, "aguas": ["mar"]}],
        "personajes": [{"id": "iv_telmo", "nombre": "Telmo", "genero": "h", "apellido": "Barlovento", "pesca": 4, "resistencia": 3, "arma": "iv_garfio", "dinero": 180, "botiquines": 2,
                        "desc": "Nacido en la isla y criado en una barca. Empieza con la pesca al nivel cuatro, resistencia al tres, un garfio y dos botiquines."}],
    }


# ============================================================ Noches de neón
def noches_neon():
    cuerpo = "bate" if "bate" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "cuerpo" and a["id"] != "punos")
    corta = "revolver" if "revolver" in ARMAS else primero(ARMAS, lambda a: a["tipo"] == "fuego")
    taxi = "taxi" if "taxi" in VEHICULOS else "utilitario"
    limu = "limusina" if "limusina" in VEHICULOS else "utilitario"
    scooter = "scooter" if "scooter" in VEHICULOS else "utilitario"
    return {
        "info": {"nombre": "Noches de neón", "autor": "Puerto Bravo", "version": "1.0",
                 "descripcion": "La noche de Puerto Bravo: un barrio de locales nuevo con una sala de conciertos, una churrería de madrugada, un hotel, un ático, una empresa de taxis nocturnos con su taxi para trabajar, una limusina, tres misiones de chófer y portero, y, con el modo adulto, una sala de fiestas, dos personas a las que conocer, planes, regalos, un cóctel y dos historias."},
        "capitulos": {"32": "Noches de neón", "33": "Noches de neón: historias para adultos"},
        "lugares": [
            {"id": "nn_sotano", "mapa": "puerto_bravo", "nombre": "Sala de conciertos El Sótano", "tipo": "monumento", "bloque": [6, 6], "lado": "O", "pos": 36, "sonido": "lugar_bar", "desc": "Un sótano con buen sonido y mala ventilación. Toca alguien casi todas las noches."},
            {"id": "nn_churreria", "mapa": "puerto_bravo", "nombre": "Churrería La Madrugada", "tipo": "comida", "bloque": [7, 7], "lado": "S", "pos": 36, "desc": "Abre cuando cierran los demás. Churros, chocolate y caldo."},
            {"id": "nn_hotel", "mapa": "puerto_bravo", "nombre": "Hotel Medianoche", "tipo": "hotel", "bloque": [6, 6], "lado": "E", "pos": 36, "precio_noche": 70, "desc": "Moqueta gruesa, recepcionista discreto y desayuno hasta las doce."},
            {"id": "nn_atico", "mapa": "puerto_bravo", "nombre": "Ático de la calle de los Neones", "tipo": "casa", "bloque": [6, 6], "lado": "S", "pos": 36, "precio": 12500, "garaje": 2, "desc": "Un ático con terraza sobre los letreros luminosos. Dos plazas de garaje."},
            {"id": "nn_radiotaxi", "mapa": "puerto_bravo", "nombre": "Radio Taxi Luna", "tipo": "negocio", "bloque": [7, 6], "lado": "E", "pos": 36, "sonido": "lugar_taxi", "precio": 15000, "ingresos": 380, "vehiculo": "nn_taxi", "desc": "Una cooperativa de taxis nocturnos en venta. En la puerta hay siempre un taxi: súbete y pulsa J."},
            {"id": "nn_seguridad", "mapa": "puerto_bravo", "nombre": "Seguridad Búho", "tipo": "armeria", "bloque": [7, 6], "lado": "N", "pos": 36, "desc": "Material para porteros y escoltas."},
            {"id": "nn_luna", "mapa": "puerto_bravo", "nombre": "Sala de fiestas Luna Llena", "tipo": "club", "bloque": [7, 6], "lado": "S", "pos": 36, "adultos": True, "desc": "Dos plantas, espectáculo a medianoche y la cola más larga de la ciudad."},
            {"id": "nn_trastienda", "mapa": "puerto_bravo", "nombre": "La Trastienda", "tipo": "proveedor", "bloque": [6, 6], "lado": "N", "pos": 36, "adultos": True, "factor": {"hierba": 1.1, "polvo": 0.9, "pastillas": 0.8, "cristal": 1.1, "nn_coctel": 0.8}, "desc": "Detrás de una tienda de discos. Aquí se abastece media noche de Puerto Bravo."},
        ],
        "vehiculos": [
            clon(VEHICULOS, taxi, id="nn_taxi", nombre="Taxi nocturno", salud=130, valor=900, precio=7200, trabajo="taxi", desc="Un taxi con luz verde y radio de la cooperativa. Con la tecla J llevas pasajeros."),
            clon(VEHICULOS, limu, id="nn_limusina", nombre="Limusina Medianoche", vel_max=27, salud=190, valor=4000, precio=42000, desc="Larga, negra y con los cristales tintados."),
            clon(VEHICULOS, scooter, id="nn_vespa", nombre="Scooter de neón", vel_max=24, salud=60, valor=450, precio=2300, desc="Un scooter con luces de colores bajo el chasis."),
        ],
        "armas": [clon(ARMAS, cuerpo, id="nn_porra", nombre="Porra extensible", dano=24, alcance=2.3, cadencia=0.45, precio=85, desc="Rápida y discreta. La de los porteros."),
                  clon(ARMAS, corta, id="nn_derringer", nombre="Derringer de bolsillo", dano=48, alcance=12, cargador=2, precio=520, balas=10, precio_balas=40, desc="Dos tiros y a recargar. Cabe en cualquier bolsillo.")],
        "comidas": [{"nombre": "Churros con chocolate", "precio": 5, "salud": 20}, {"nombre": "Caldo de madrugada", "precio": 3, "salud": 12}],
        "objetos": [{"id": "nn_pulsera", "nombre": "Pulsera de la sala El Sótano", "precio": 15, "desc": "La entrada del concierto de esta noche. De recuerdo."}],
        "carreras": [{"id": "nn_c1", "nombre": "Nocturna de los Neones", "mapa": "puerto_bravo", "premio": 750, "tiempo": 95, "puntos": [[7, 6], [7, 8], [4, 8], [4, 5], [7, 5], [7, 6]]}],
        "personajes": [{"id": "nn_vera", "nombre": "Vera", "genero": "m", "apellido": "Montoya", "conduccion": 4, "reputacion": 15, "ciudadania": 15, "dinero": 400, "arma": "nn_porra", "botiquines": 1,
                        "desc": "Diez años de taxista de noche. Empieza con conducción al nivel cuatro, cuatrocientos euros, una porra y algo de nombre tanto entre los vecinos como en la calle."}],
        "misiones": [
            {"id": "nn01", "titulo": "Turno de noche", "capitulo": 32, "contacto": "Mari Cruz", "lugar": "nn_radiotaxi", "requiere": ["m01"],
             "resumen": "En Radio Taxi Luna falta un chófer para un servicio especial.",
             "pasos": [D(("Mari Cruz", "Se me ha puesto malo el de la limusina y tengo a un cantante esperando en el Hotel Medianoche. ¿Tú conduces fino?"),
                         ("Mari Cruz", "La limusina está en la puerta de la sala El Sótano. Recógela y llévala al casino sin un rasguño, que es alquilada.")),
                       {"tipo": "robar", "lugar": "nn_sotano", "modelo": "nn_limusina", "nombre": "la limusina alquilada", "abierto": True, "texto": "Recoge la limusina junto a la sala El Sótano. Está abierta."},
                       {"tipo": "ir", "lugar": "nn_hotel", "texto": "Pasa por el Hotel Medianoche a recoger al cantante."},
                       {"tipo": "entregar", "lugar": "casino", "salud_min": 85, "limite": 200, "texto": "Llévalo al casino en poco más de tres minutos y sin golpes."},
                       D(("Narrador", "El cantante baja sin dar las gracias. La propina, eso sí, es de las buenas."))],
             "recompensa": {"dinero": 450}},
            {"id": "nn02", "titulo": "Los de la puerta", "capitulo": 32, "contacto": "Mari Cruz", "lugar": "nn_radiotaxi", "requiere": ["nn01"],
             "resumen": "Una banda cobra a los taxistas por dejarles parar delante de los locales.",
             "pasos": [D(("Mari Cruz", "Nos piden cincuenta euros por noche y taxi. Al que no paga le rajan las ruedas. Están en la churrería, que es donde cuentan la caja."),
                         ("Mari Cruz", "Toma, la porra de mi cuñado, que era portero. Si se ponen tontos, tú más.")),
                       {"tipo": "dar", "arma": "nn_porra"},
                       {"tipo": "eliminar", "lugar": "nn_churreria", "texto": "Ve a la Churrería La Madrugada y échalos de allí.",
                        "enemigos": [{"n": 3, "tipo": "Matón de puerta", "arma": "navaja", "salud": 55}, {"n": 1, "tipo": "El Cobrador", "arma": "nn_derringer", "salud": 85}]},
                       {"tipo": "recoger", "lugar": "nn_churreria", "objeto": "la libreta de cobros", "texto": "Recoge la libreta de cobros."},
                       D(("Narrador", "En la libreta están todos los taxis de la ciudad, y al final una matrícula subrayada dos veces."))],
             "recompensa": {"dinero": 700, "arma": "nn_derringer", "balas": 10}},
            {"id": "nn03", "titulo": "Bajada de bandera", "capitulo": 32, "contacto": "Mari Cruz", "lugar": "nn_radiotaxi", "requiere": ["nn02"],
             "resumen": "El jefe de los cobradores huye con la caja de un mes.",
             "pasos": [D(("Mari Cruz", "La matrícula es de un sedán negro. Se va con la caja de todo el mes por la salida del este. Ese dinero es de los compañeros.")),
                       {"tipo": "perseguir", "lugar": "salida_este", "modelo": "sedan" if "sedan" in VEHICULOS else "utilitario", "nombre": "el sedán negro", "salud": 200, "limite": 260, "texto": "Alcanza y destroza el sedán negro antes de que salga de la ciudad."},
                       {"tipo": "recoger", "aqui": True, "objeto": "la caja del mes", "texto": "Recoge la caja del mes."},
                       {"tipo": "policia", "nivel": 2, "texto": "Te han visto. Despista a la policía antes de volver."},
                       {"tipo": "ir", "lugar": "nn_radiotaxi", "texto": "Devuelve la caja a Radio Taxi Luna."},
                       D(("Mari Cruz", "Aquí no se olvida esto. Llévate el scooter de las luces, que era del Cobrador y ya no lo va a necesitar.")),
                       {"tipo": "dar", "dinero": 300}],
             "recompensa": {"dinero": 1600, "chaleco": True}},
            {"id": "nna1", "titulo": "Lista de invitados", "capitulo": 33, "adultos": True, "contacto": "Darío", "lugar": "nn_luna", "requiere": ["nn01"],
             "resumen": "En la Luna Llena, Darío necesita que alguien recoja un encargo antes de que abra la sala.",
             "pasos": [D(("Darío", "Esta noche viene medio Ayuntamiento y me falta lo del cóctel de la casa. Pásate por La Trastienda y tráemelo. Quédate dos para ti.")),
                       {"tipo": "ir", "lugar": "nn_trastienda", "texto": "Pasa por La Trastienda."},
                       {"tipo": "dar", "sustancia": "nn_coctel", "cantidad": 2},
                       {"tipo": "ir", "lugar": "nn_luna", "limite": 150, "texto": "Vuelve a la Luna Llena antes de que abran las puertas."},
                       D(("Darío", "Puntual. Eso aquí vale más que el dinero. Estás en la lista, para siempre."))],
             "recompensa": {"dinero": 320, "afinidad": {"nn_dario": 15}}},
            {"id": "nna2", "titulo": "Después del último pase", "capitulo": 33, "adultos": True, "contacto": "Irene", "lugar": "nn_luna", "requiere": ["nna1"],
             "resumen": "Irene, la cantante de la sala, tiene a un admirador que no entiende un no.",
             "pasos": [D(("Irene", "Me espera cada noche en la puerta de atrás. Le he dicho que no de todas las maneras. Hoy ha venido con dos amigos."),
                         ("Irene", "No quiero que le pase nada grave. Solo que entienda.")),
                       {"tipo": "eliminar", "lugar": "nn_sotano", "texto": "Están junto a la sala El Sótano. Haz que lo entiendan.",
                        "enemigos": [{"n": 2, "tipo": "Amigo del pesado", "arma": "punos", "salud": 45}, {"n": 1, "tipo": "El pesado", "arma": "punos", "salud": 60}]},
                       {"tipo": "ir", "lugar": "nn_luna", "texto": "Vuelve a la Luna Llena."},
                       D(("Irene", "Gracias. De verdad. La primera copa de cada noche, para ti, mientras yo cante aquí."))],
             "recompensa": {"dinero": 400, "afinidad": {"nn_irene": 18}}},
        ],
        "personas": [
            {"id": "nn_dario", "nombre": "Darío", "edad": 41, "lugar": "nn_luna", "gustos": ["nn_concierto", "cena"], "regalo": "nn_vinilo",
             "desc": "Encargado de la Luna Llena. Traje impecable, memoria de elefante y un sentido del humor muy seco. Fue bailarín antes de que le fallara una rodilla."},
            {"id": "nn_irene", "nombre": "Irene", "edad": 30, "lugar": "nn_luna", "gustos": ["nn_churros", "paseo"], "regalo": "nn_vinilo",
             "desc": "Canta boleros a medianoche y rock cuando nadie mira. Tímida fuera del escenario, y en él no hay quien le quite los ojos de encima."}],
        "actividades": [{"id": "nn_concierto", "nombre": "Ir a un concierto en El Sótano", "precio": 30, "horas": 3},
                        {"id": "nn_churros", "nombre": "Churros al amanecer en La Madrugada", "precio": 12, "horas": 1}],
        "regalos": [{"id": "nn_vinilo", "nombre": "Un vinilo de primera edición", "precio": 110, "afinidad": 12},
                    {"id": "nn_entradas", "nombre": "Dos entradas de palco", "precio": 160, "afinidad": 15}],
        "sustancias": [clon(SUSTANCIAS, "alcohol", id="nn_coctel", nombre="Cóctel Luna Llena", unidad="copa", precio=14, animo=10, adiccion=1.5, sobredosis=5,
                            desc="El cóctel de la casa. Entra solo y sube el ánimo más que una copa normal.")],
    }


def bahia_ocaso():
    import mod_bahia_ocaso
    return mod_bahia_ocaso.crear(ARMAS, VEHICULOS, SUSTANCIAS, clon)


DE_OIDO = {
    "costa_dorada.json": {"id": "cdo1", "titulo": "El patrón de la lancha", "capitulo": 21, "contacto": "La boticaria", "lugar": "cd_farmacia", "requiere": ["m01"],
        "resumen": "La boticaria quiere saber dónde se mete el patrón de una lancha que no pesca nada.",
        "pasos": [D(("La boticaria", "Hay un patrón que sale cada tarde de la lonja con las manos vacías y los bolsillos llenos. Síguele de lejos y dime adónde va."),
                    ("La boticaria", "A pie y sin acercarte. Se le oye andar: con eso te basta.")),
                  {"tipo": "seguir", "lugar": "cd_lonja", "destino": "cd_taberna", "persona": "el patrón",
                   "texto": "Ve a la Lonja de Costa Dorada y sigue al patrón sin que te descubra. Guíate por sus pasos."},
                  D(("Narrador", "El patrón entra en la Taberna El Ancla y se sienta al fondo, de espaldas a la puerta."),
                    ("La boticaria", "En El Ancla. Pues ya sé con quién tengo que hablar. Gracias."))],
        "recompensa": {"dinero": 300}},
    "valdeolmos.json": {"id": "voo1", "titulo": "La madrina", "capitulo": 24, "contacto": "El mesonero", "lugar": "vo_meson", "requiere": ["m01"],
        "resumen": "La madrina de la boda está en la bodega y la ceremonia empieza ya.",
        "pasos": [D(("El mesonero", "La madrina se ha quedado en la bodega probando el vino y la boda empieza en la parroquia. Ve a por ella y tráela, que yo no puedo dejar los fogones."),
                    ("El mesonero", "Va con tacones, así que paciencia. Si llevas coche, mejor.")),
                  {"tipo": "escoltar", "lugar": "vo_bodega", "destino": "vo_parroquia", "persona": "la madrina",
                   "texto": "Recoge a la madrina en la bodega y acompáñala hasta la parroquia."},
                  D(("La madrina", "¡Llegamos! Y con el peinado en su sitio. Ven luego al convite, que te has ganado un plato."))],
        "recompensa": {"dinero": 250}},
    "penas_altas.json": {"id": "pao1", "titulo": "La llave del polvorín", "capitulo": 27, "contacto": "El cantinero", "lugar": "pa_cantina", "requiere": ["m01"],
        "resumen": "Alguien ha puesto vigilantes en el polvorín viejo, y el pueblo quiere saber qué guardan.",
        "pasos": [D(("El cantinero", "El polvorín lleva veinte años cerrado y desde el lunes hay dos tipos dando vueltas. Nadie se atreve a mirar."),
                    ("El cantinero", "Acércate sin que te oigan y tráeme lo que haya en la puerta. Agachado y sin prisa.")),
                  {"tipo": "sigilo", "lugar": "pa_polvorin", "guardias": 2, "objeto": "un albarán de explosivos",
                   "texto": "Ve al polvorín y llega hasta la puerta sin que te oigan los vigilantes. Agáchate con la X y no corras."},
                  D(("El cantinero", "Explosivos, y con fecha de la semana pasada. Esto no es para la cantera. Ya sé a quién enseñárselo."))],
        "recompensa": {"dinero": 450}},
    "isla_de_los_vientos.json": {"id": "ivo1", "titulo": "La ronda del farero", "capitulo": 30, "contacto": "Chelo", "lugar": "iv_cantina", "requiere": ["m01"],
        "resumen": "Antes de que cambie la marea hay que encender las cuatro luces de la isla.",
        "pasos": [D(("Chelo", "El farero está con fiebre y hoy sube la marea fuerte. Hay que encender las cuatro luces de la isla antes de que oscurezca."),
                    ("Chelo", "Aquí no hay coches: a pie y corriendo. La torre, el aljibe, la rompiente y el muelle, por ese orden.")),
                  {"tipo": "ruta", "puntos": ["iv_semaforo", "iv_aljibe", "iv_rompiente", "iv_muelle"], "limite": 420,
                   "texto": "Enciende las luces de la Torre del Semáforo, el Aljibe, la Rompiente y el Muelle, por ese orden, en siete minutos. A pie."},
                  D(("Chelo", "Las cuatro encendidas y con luz de sobra. Esta noche no encalla nadie. La casa invita."))],
        "recompensa": {"dinero": 350}},
    "noches_de_neon.json": {"id": "nno1", "titulo": "El cobrador", "capitulo": 32, "contacto": "La churrera", "lugar": "nn_churreria", "requiere": ["m01"],
        "resumen": "Un cobrador pasa cada noche por los locales, y la churrera quiere saber para quién trabaja.",
        "pasos": [D(("La churrera", "Todas las noches pasa un tipo cobrando a los locales. Nadie sabe para quién. Hoy sale de la sala de conciertos: síguele y dime dónde entrega."),
                    ("La churrera", "De lejos. De noche se oyen bien los pasos.")),
                  {"tipo": "seguir", "lugar": "nn_sotano", "destino": "nn_hotel", "persona": "el cobrador",
                   "texto": "Ve a la sala de conciertos El Sótano y sigue al cobrador sin que te descubra. Guíate por sus pasos."},
                  D(("Narrador", "El cobrador entra en el hotel y sube sin pasar por recepción."),
                    ("La churrera", "En el hotel. Ya sé en qué habitación preguntar. Te debo una docena de churros."))],
        "recompensa": {"dinero": 400}},
}


def _dec(clave, pregunta, *opciones):
    return {"tipo": "decision", "clave": clave, "pregunta": pregunta,
            "opciones": [dict(zip(("texto", "ayuda", "dice"), o[:3]), **o[3]) for o in opciones]}


# Una decisión con consecuencias en una misión de cada mod, justo antes de su escena final.
DECISIONES = {
    "cdo1": _dec("cd_patron", "Sabes dónde se mete el patrón. Antes de volver a la botica, el patrón te ve y te hace una seña. ¿Qué haces?",
                 ("Contárselo todo a la boticaria", "Lo que te encargaron. Ganas fama en Costa Dorada.", "Pasas de largo y vuelves a la botica.", {"fama": 2}),
                 ("Aceptar 200 euros del patrón por callar parte", "Cobras, y la boticaria se queda con media verdad.", "El patrón te desliza los billetes por debajo de la mesa.", {"dinero": 200, "fama": -2})),
    "voo1": _dec("vo_madrina", "La madrina te invita al convite. El mesonero, por su parte, te debe el porte. ¿Qué haces?",
                 ("Quedarte al convite", "Comes, bailas y te sube el ánimo. No cobras.", "Te sientan entre los primos del novio. Hay cordero para tres días.", {"animo": 9}),
                 ("Cobrar los 100 euros y seguir tu camino", "Dinero en mano.", "El mesonero te paga sin dejar de remover la olla.", {"dinero": 100})),
    "pao1": _dec("pa_albaran", "Tienes el albarán de los explosivos. El capataz de la cantera te ofrece comprártelo. ¿Qué haces?",
                 ("Llevárselo al cantinero, como quedasteis", "El pueblo sabrá qué se guarda en el polvorín. Ganas fama.", "Le dices al capataz que no está en venta.", {"fama": 4}),
                 ("Vendérselo al capataz por 700 euros", "Cobras bien, y en Peñas Altas nadie sabrá nunca lo que había.", "El capataz quema el papel delante de ti, sin prisa.", {"dinero": 700, "fama": -3})),
    "ivo1": _dec("iv_luces", "Las cuatro luces están encendidas. Chelo quiere agradecértelo. ¿Qué le pides?",
                 ("Nada: una copa y conversación", "Te sube el ánimo y en la isla te tendrán por [uno|una] de los suyos.", "Chelo saca la botella buena, la que no enseña a los de fuera.", {"animo": 7, "fama": 2}),
                 ("Que te pague el trabajo: 150 euros", "Dinero en mano.", "Chelo abre la caja, cuenta los billetes y no dice nada más.", {"dinero": 150})),
    "nno1": _dec("nn_cobrador", "Sabes dónde entrega el cobrador. Un hombre del hotel te ha visto y te ofrece dinero por olvidarlo. ¿Qué haces?",
                 ("Decírselo al portero", "Lo que te encargaron. Ganas fama entre los locales.", "Le dices que tienes mala memoria para las caras, pero buena para los hoteles.", {"fama": 3}),
                 ("Aceptar 400 euros y decir que lo perdiste", "Cobras, y el portero se queda sin saberlo.", "El hombre del hotel te mete el sobre en el bolsillo de la chaqueta.", {"dinero": 400, "fama": -2})),
    "ocs6": _dec("oc_nombre", "Tienes el nombre de quien firma los pedidos del agua. ¿Qué haces con él?",
                 ("Dárselo al periódico para que lo publique", "Ganas mucha fama en Bahía del Ocaso. No cobras nada.", "Lo escribes en un papel y lo dejas encima de la mesa de la redacción.", {"fama": 6, "animo": 5}),
                 ("Guardártelo y hacerle una visita: 2500 euros", "Cobras por callar, y trescientos euros más cada medianoche, para siempre. El agua seguirá igual de cara.",
                  "El hombre no discute el precio. Tiene el dinero preparado.", {"dinero": 2500, "fama": -4, "animo": -4, "renta": 300})),
}

# Las dos ramas que abre esa decisión en Bahía del Ocaso, cada una con su final.
RAMAS = {
    "bahia_del_ocaso.json": [
        {"id": "ocs7", "titulo": "Portada del Ocaso", "capitulo": 46, "contacto": "Nerea", "lugar": "oc_periodico", "requiere": ["ocs6"], "si_clave": "oc_nombre", "si_opcion": 1,
         "resumen": "El periódico va a publicar el nombre, y en la Sede de Aguas del Ocaso están destruyendo papeles.",
         "final_titulo": "Bahía del Ocaso: el agua vuelve a ser de todos",
         "final": "La portada sale con el nombre y la firma. A la semana, la Sede de Aguas del Ocaso está precintada y los camiones cisterna reparten sin cobrar. Llueve, por fin, un jueves por la tarde, y media ciudad sale a la calle a mojarse.",
         "pasos": [D(("Nerea", "Mañana sale el nombre. Esta noche están quemando papeles en la Sede de Aguas. Necesito saber cuántas cajas sacan y adónde las llevan."),
                     ("Nerea", "Vigila la sede sin que te vean. Luego, si puedes, quédate con lo que saquen.")),
                   {"tipo": "vigilar", "lugar": "oc_sede", "segundos": 40, "radio": 25, "resultado": "Han sacado cuatro cajas de archivo y las han cargado en una furgoneta, camino del ayuntamiento.",
                    "texto": "Vigila la Sede de Aguas del Ocaso sin que te vean. Cuando oigas pasos, quédate quiet[o|a] o agáchate con la X."},
                   {"tipo": "eliminar", "lugar": "oc_ayuntamiento", "enemigos": [{"n": 3, "tipo": "Guardia de la compañía", "arma": "pistola", "salud": 75}],
                    "texto": "Ve al ayuntamiento y quítales las cajas a los guardias de la compañía."},
                   D(("Nerea", "Cuatro cajas. Contratos, sobres, hasta las fechas. Con esto no hay quien lo tape."))],
         "recompensa": {"dinero": 2500}},
        {"id": "ocs8", "titulo": "Agua turbia", "capitulo": 46, "contacto": "El hombre de los pedidos", "lugar": "oc_sede", "requiere": ["ocs6"], "si_clave": "oc_nombre", "si_opcion": 2,
         "resumen": "El que firma los pedidos paga bien por callar, y ahora quiere que le hagas un favor.",
         "final_titulo": "Bahía del Ocaso: socio del agua",
         "final": "El agua sigue igual de cara y tú cobras tu parte cada noche. En el Cauce Seco hay quien te saluda con miedo y quien ya no te saluda. El periódico publicó otra cosa en portada.",
         "pasos": [D(("El hombre de los pedidos", "Ya que nos entendemos: esta noche salen tres cisternas que no deben cruzarse con nadie. Abra usted camino."),
                     ("El hombre de los pedidos", "Embotelladora, depósito y sede. Cuatro minutos.")),
                   {"tipo": "ruta", "puntos": ["oc_embotelladora", "oc_deposito", "oc_sede"], "limite": 240, "texto": "Pasa por la embotelladora, el depósito de cisternas y la sede, por ese orden, en cuatro minutos."},
                   D(("El hombre de los pedidos", "Limpio. A partir de hoy, usted y yo somos socios. No lo vaya contando."))],
         "recompensa": {"dinero": 5000}},
    ],
}


def escribir(nombre, crudo):
    extra = DE_OIDO.get(nombre)
    if extra and not any(m["id"] == extra["id"] for m in crudo.get("misiones", [])):
        crudo.setdefault("misiones", []).append(extra)
    for rama in RAMAS.get(nombre, []):
        if not any(m["id"] == rama["id"] for m in crudo.get("misiones", [])):
            crudo.setdefault("misiones", []).append(rama)
    # el transporte público de cada localidad del mod queda escrito en el propio mod, para que se pueda editar
    import escribir_transporte
    escribir_transporte.completar_mod(crudo)
    for mi in crudo.get("misiones", []):
        paso = DECISIONES.get(mi.get("id"))
        if paso and not any(x.get("tipo") == "decision" for x in mi["pasos"]):
            mi["pasos"].insert(len(mi["pasos"]) - 1, paso)
    from editor import modelo
    mod = modelo.Mod.desde_crudo(crudo)
    ruta = os.path.join(rutas.carpeta_data("mods"), nombre)
    if os.path.exists(ruta):
        os.remove(ruta)                              # para que el revisor no lo vea como «otro mod» con los mismos identificadores
    errores, avisos = modelo.comprobar(mod, modelo.Catalogo())
    mod.guardar(ruta, protegido=False)          # en el código fuente quedan legibles; compilar.bat los protege
    return ruta, errores, avisos


MODS = (("costa_dorada.json", costa_dorada), ("oficios_y_recados.json", oficios), ("valdeolmos.json", valdeolmos), ("motor_y_asfalto.json", motor),
        ("penas_altas.json", penas_altas), ("isla_de_los_vientos.json", isla_vientos), ("noches_de_neon.json", noches_neon), ("bahia_del_ocaso.json", bahia_ocaso))

if __name__ == "__main__":
    mal = False
    for nombre, hacer in MODS:
        ruta, errores, avisos = escribir(nombre, hacer())
        print(f"{nombre}: {len(errores)} errores, {len(avisos)} avisos")
        for e in errores:
            print("   ERROR", e)
            mal = True
        for a in avisos:
            print("   aviso", a)
    sys.exit(1 if mal else 0)
