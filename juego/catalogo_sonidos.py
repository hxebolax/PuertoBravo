"""Catálogo de sonidos: qué es cada archivo de data/sonidos, cómo se llama en voz alta y en qué grupo va.

Es la única clasificación del juego. De aquí salen, con los mismos grupos, los mismos nombres y el mismo orden:
Aprender los sonidos, el volumen de cada sonido de Opciones, la guía de sonidos (cambiar_sonidos.html) y la lista para
hacer packs. Un sonido nuevo se apunta aquí, en SONIDOS, dentro de su grupo, con su nombre hablado y su explicación.

Los grupos son por lo que se hace en el juego, no por cómo está hecho el sonido. Dentro de cada grupo el orden es
alfabético por el nombre que se dice, así que da igual en qué orden se escriban aquí.
"""
from .i18n import tr
import unicodedata

# clave, título que se dice, y consejo para quien cambia sonidos (solo sale en la guía)
GRUPOS = [
    (tr("Orientación y GPS"), tr("Son la base de la accesibilidad del juego. Si los cambias, que sigan siendo cortos, claros y fáciles de localizar en el espacio. "
     "Los localizadores suenan en bucle desde la posición de un objeto o de una misión."), "orientacion"),
    (tr("Sonidos de los lugares"), tr("Cada tipo de lugar emite su sonido en bucle para reconocerlo al pasar. Deben ser distintos entre sí y no cansar: piensa que se oyen muchas veces."), "lugares"),
    (tr("Moverse a pie y nadar"), tr("Hay dos variantes de los pasos de cada suelo, que se alternan pie izquierdo y pie derecho. Deben durar menos de un cuarto de segundo."), "pie"),
    (tr("Vehículos y conducción"), tr("Los motores se reproducen en bucle y el juego les sube el tono con la velocidad. Graba el motor al ralentí, a régimen constante."), "conducir"),
    (tr("Averías, taller, gasolina y robo de vehículos"), tr("Lo que le pasa a un vehículo cuando no lo estás conduciendo sin más."), "taller"),
    (tr("Barcos, helicópteros, tren, tranvía y avión"), tr("El tren, el tranvía y la cabina del avión suenan en bucle, igual que los motores."), "transporte"),
    (tr("Armas, el disparo de cada una"), tr("El disparo de cada arma debe reconocerse sin mirar: procura que no se parezcan entre sí."), "disparos"),
    (tr("Combate, puntería y heridas"), tr("Recargas, impactos, golpes, los tonos de la puntería y lo que se oye cuando hieren a alguien."), "combate"),
    (tr("Policía y emergencias"), tr("Avisos del nivel de búsqueda, sirenas y el helicóptero de la policía."), "policia"),
    (tr("Gente de la calle y animales"), tr("Voces sin palabras, pasos de otros y el perro."), "gente"),
    (tr("Casa, cocina y comida"), tr("Comer, beber, cocinar en casa y que llamen a la puerta."), "casa"),
    (tr("Tiendas, dinero y objetos"), tr("Comprar, cobrar y recoger cosas."), "dinero"),
    (tr("Menús, móvil y avisos del juego"), tr("Sonidos cortos de la interfaz. Conviene que sean breves y discretos."), "avisos"),
    (tr("Misiones, trabajo, reputación y ánimo"), tr("Lo que suena al acabar una misión, en el trabajo honrado y cuando cambia cómo te ven o cómo estás."), "trabajo"),
    (tr("Territorios y bandas"), tr("Los avisos de los barrios que son tuyos."), "territorios"),
    (tr("Jugar en línea y rol"), tr("Avisos de la partida compartida y de los canales de rol de los servidores."), "linea"),
    (tr("Pesca, casino y juegos"), tr("La pesca y los juegos del casino, de la feria y del gimnasio."), "juegos"),
    (tr("Ambientes y clima"), tr("Bucles largos que suenan de fondo en cada barrio, con la lluvia y de noche, y sonidos sueltos que aparecen de vez en cuando alrededor."), "ambientes"),
    (tr("Relaciones, solo con el contenido para adultos"), tr("Relaciones sentimentales."), "relaciones"),
    (tr("Sustancias y trapicheo, solo con el contenido para adultos"), tr("Cada sustancia tiene su sonido al tomarla, para reconocerla sin mirar."), "sustancias"),
]
OTROS = tr("Otros sonidos")            # solo para un sonido que no esté apuntado aquí: un archivo añadido a mano

# grupo -> [(archivo, nombre que se dice, qué significa oírlo en el juego), ...]
SONIDOS = {
    "orientacion": [
        ("baliza", tr("Baliza del GPS"), tr("Suena en la dirección del siguiente punto de la ruta. Cuanto más cerca estás, más rápido se repite.")),
        ("baliza_destino", tr("Baliza de destino"), tr("La baliza del GPS cambia a este sonido cuando lo siguiente ya es tu destino. También es el tono que marca el norte.")),
        ("llegada", tr("Llegada"), tr("Has llegado al destino o has completado un paso de la misión.")),
        ("cruce", tr("Cruce"), tr("Entras en un cruce de calles, o te acercas a uno al volante.")),
        ("radar", tr("Radar"), tr("Suena desde la posición de lo que acaba de anunciar el radar.")),
        ("tono_pared", tr("Escáner, pared"), tr("El escáner direccional ha encontrado una pared. Suena más agudo cuanto más cerca está.")),
        ("tono_libre", tr("Escáner, camino despejado"), tr("El escáner direccional no encuentra ninguna pared en esa dirección.")),
        ("semaforo_tic", tr("Semáforo, tictac rápido"), tr("Los coches de la calle están parados: puedes cruzar la calle, andando hacia el norte o hacia el sur.")),
        ("semaforo_pio", tr("Semáforo, pío lento"), tr("Los coches de la avenida están parados: puedes cruzar la avenida, andando hacia el este o hacia el oeste.")),
        ("semaforo_rojo", tr("Semáforo en rojo, al volante"), tr("Conduces tú y el semáforo del próximo cruce está en rojo, o se acaba de poner en rojo: dos notas graves que bajan.")),
        ("semaforo_verde", tr("Semáforo en verde, al volante"), tr("Conduces tú y el semáforo del próximo cruce está en verde, o se acaba de poner en verde: dos notas agudas que suben.")),
        ("cursor_mapa", tr("Cursor del explorador de mapa"), tr("El cursor del explorador de mapa ha pasado al cruce siguiente. También suena al leer un tablón dentro de un local.")),
        ("sonar", tr("Sensor de proximidad"), tr("Al volante, hay un vehículo delante: pita más rápido y más agudo cuanto más cerca está. También es el pitido de frío o caliente al buscar tesoros.")),
        ("bordillo", tr("Bordillo"), tr("En conducción libre, te sales de la calzada por el lado en el que suena.")),
        ("loc_mision", tr("Misión disponible"), tr("Suena desde un lugar donde hay una misión esperándote.")),
        ("loc_objeto", tr("Objeto que puedes recoger"), tr("Suena desde un objeto que hay en el suelo. Ponte encima y recógelo.")),
        ("loc_casete", tr("Objeto de colección"), tr("Suena desde una de las cintas de casete escondidas por la ciudad, o desde otro objeto de colección.")),
        ("loc_vehiculo", tr("Vehículo de la misión"), tr("Suena desde el vehículo que te pide la misión, y desde el de tu chófer mientras te espera.")),
        ("loc_lugar", tr("Punto de interés"), tr("Suena desde un punto de interés que no tiene sonido propio.")),
    ],
    "lugares": [
        ("puerta_entrar", tr("Entrar en un local"), tr("Entras en un local: la puerta y su campanilla. Mientras estás dentro suena de fondo el sonido del lugar.")),
        ("puerta_salir", tr("Salir de un local"), tr("Sales de un local: la campanilla y la puerta que se cierra.")),
        ("lugar_academia", tr("Academia o autoescuela"), tr("Estás junto a una academia o una autoescuela: el timbre de clase.")),
        ("lugar_aeropuerto", tr("Aeropuerto"), tr("Estás junto al aeropuerto: el aviso de megafonía, tres notas que bajan.")),
        ("lugar_armeria", tr("Armería"), tr("Estás junto a una armería: un arma que se amartilla.")),
        ("lugar_banco", tr("Banco o casa de empeños"), tr("Estás junto a un banco o una casa de empeños: los pitidos de un cajero automático.")),
        ("lugar_bar", tr("Bar, taberna o discoteca"), tr("Estás junto a un bar, una taberna, una discoteca o un negocio: graves de música a través de la pared.")),
        ("lugar_boya", tr("Muelle, boya o punto de pesca"), tr("Estás junto a un muelle, una boya, un punto de pesca o un tesoro en el mar: una campana de boya entre las olas.")),
        ("lugar_casa", tr("Casa"), tr("Estás junto a una vivienda o un hotel, tuya o que puedes comprar: campanillas de viento.")),
        ("lugar_casino", tr("Casino o feria"), tr("Estás junto a un casino o una feria: la musiquilla de las máquinas tragaperras.")),
        ("lugar_cine", tr("Cine"), tr("Estás junto a un cine: el traqueteo de un proyector.")),
        ("lugar_club", tr("Club nocturno, contenido para adultos"), tr("Estás junto a un club nocturno: música amortiguada y copas.")),
        ("lugar_comida", tr("Restaurante, pizzería o chiringuito"), tr("Estás junto a un sitio donde se come: algo friéndose.")),
        ("lugar_comisaria", tr("Comisaría"), tr("Estás junto a una comisaría: una emisora de policía.")),
        ("lugar_contacto", tr("Lugar con un contacto"), tr("Estás junto a un lugar donde te espera alguien con un encargo.")),
        ("lugar_embarcadero", tr("Embarcadero o tienda náutica"), tr("Estás junto a un embarcadero: el agua contra los pantalanes y las amarras que crujen.")),
        ("lugar_empleo", tr("Oficina de empleo"), tr("Estás junto a la oficina de empleo: teclados y el aviso de turno.")),
        ("lugar_estacion", tr("Estación de autobuses"), tr("Estás junto a la estación de autobuses: frenos de aire y megafonía.")),
        ("lugar_fuente", tr("Fuente"), tr("Estás junto a una fuente: agua cayendo.")),
        ("lugar_generico", tr("Lugar sin sonido propio"), tr("Estás junto a un lugar de un tipo que no tiene sonido propio.")),
        ("lugar_gimnasio", tr("Gimnasio"), tr("Estás junto a un gimnasio: pesas que chocan.")),
        ("lugar_helipuerto", tr("Helipuerto"), tr("Estás junto a un helipuerto: palas girando y un pitido de torre de control.")),
        ("lugar_hospital", tr("Hospital o farmacia"), tr("Estás junto a un hospital o una farmacia: el pitido de un monitor.")),
        ("lugar_iglesia", tr("Iglesia"), tr("Estás junto a una iglesia: una campana.")),
        ("lugar_mina", tr("Mina"), tr("Estás junto a una mina: picos contra la roca.")),
        ("lugar_ong", tr("Comedor social"), tr("Estás junto a un comedor social o una organización benéfica: platos y cubiertos.")),
        ("lugar_periodico", tr("Periódico o librería"), tr("Estás junto a un periódico o una librería: el tecleo de las máquinas de escribir.")),
        ("lugar_prision", tr("Prisión"), tr("Estás junto a la prisión: una reja que se cierra y una sirena lejana.")),
        ("lugar_protectora", tr("Protectora de animales"), tr("Estás junto a la protectora, donde puedes adoptar un perro: ladridos.")),
        ("lugar_proveedor", tr("Proveedor, contenido para adultos"), tr("Estás junto a un proveedor, donde se compra y se vende mercancía: dos siseos y una persiana metálica.")),
        ("lugar_rio", tr("Río"), tr("Estás junto a un río: agua corriendo entre piedras.")),
        ("lugar_salida", tr("Salida por carretera"), tr("Estás junto a una salida de la ciudad: coches que pasan deprisa. Por aquí se va a otra localidad.")),
        ("lugar_taller", tr("Taller, desguace o concesionario"), tr("Estás junto a un taller, un desguace o un concesionario: una pistola neumática.")),
        ("lugar_taxi", tr("Parada de taxis o salida de carreras"), tr("Estás junto a una parada de taxis o a la salida de una carrera: dos toques cortos de claxon.")),
        ("lugar_tienda", tr("Tienda"), tr("Estás junto a una tienda: el timbre de la puerta.")),
        ("lugar_tranvia", tr("Parada de tranvía"), tr("Estás junto a una parada de tranvía: dos toques de campana.")),
        ("lugar_tren", tr("Estación de tren"), tr("Estás junto a la estación de tren: resoplidos de locomotora.")),
    ],
    "pie": [
        ("paso_acera0", tr("Pasos en la acera, pie izquierdo"), tr("Caminas por la acera.")),
        ("paso_acera1", tr("Pasos en la acera, pie derecho"), tr("Caminas por la acera. Los dos pies suenan un poco distinto.")),
        ("paso_calzada0", tr("Pasos en la calzada, pie izquierdo"), tr("Caminas por el asfalto: cuidado con los coches.")),
        ("paso_calzada1", tr("Pasos en la calzada, pie derecho"), tr("Caminas por el asfalto, por donde van los coches.")),
        ("paso_hierba0", tr("Pasos en el césped, pie izquierdo"), tr("Caminas por el césped de un parque o por el campo.")),
        ("paso_hierba1", tr("Pasos en el césped, pie derecho"), tr("Caminas por el césped, con el otro pie.")),
        ("paso_arena0", tr("Pasos en la arena, pie izquierdo"), tr("Caminas por la arena de la playa.")),
        ("paso_arena1", tr("Pasos en la arena, pie derecho"), tr("Caminas por la arena, con el otro pie.")),
        ("paso_muelle0", tr("Pasos en el muelle, pie izquierdo"), tr("Caminas sobre los tablones de un muelle.")),
        ("paso_muelle1", tr("Pasos en el muelle, pie derecho"), tr("Caminas sobre los tablones de un muelle, con el otro pie.")),
        ("paso_plaza0", tr("Pasos en una plaza, pie izquierdo"), tr("Caminas sobre las losas de una plaza.")),
        ("paso_plaza1", tr("Pasos en una plaza, pie derecho"), tr("Caminas sobre las losas de una plaza, con el otro pie.")),
        ("paso_via0", tr("Pasos sobre las vías, pie izquierdo"), tr("Estás en medio de las vías del tranvía o del tren: un toque metálico, del raíl, con grava debajo.")),
        ("paso_via1", tr("Pasos sobre las vías, pie derecho"), tr("Sigues sobre las vías del tranvía o del tren: sal de ellas.")),
        ("choque_pared", tr("Choque con una pared"), tr("Has intentado caminar contra una pared.")),
        ("agacharse", tr("Agacharte"), tr("Te agachas: haces menos ruido y cuesta más verte.")),
        ("levantarse", tr("Levantarte"), tr("Te pones de pie después de estar agachado.")),
        ("salpicadura", tr("Chapuzón"), tr("Alguien o algo cae al agua: tú, un vehículo o lo que tiras al mar.")),
        ("brazada", tr("Brazada"), tr("Suena con cada brazada que das nadando.")),
        ("bajo_agua", tr("Bajo el agua"), tr("Estás buceando: un rumor sordo con burbujas.")),
    ],
    "conducir": [
        ("motor_coche", tr("Motor de coche"), tr("El motor de un coche. Sube de tono con la velocidad.")),
        ("motor_deportivo", tr("Motor de deportivo"), tr("El motor de un deportivo, más bronco que el de un coche normal.")),
        ("motor_moto", tr("Motor de moto"), tr("El motor de una moto.")),
        ("motor_camion", tr("Motor de camión o autobús"), tr("El motor de un camión o de un autobús, grave y pesado.")),
        ("motor_furgoneta", tr("Motor de furgoneta o todoterreno"), tr("El motor de una furgoneta o de un todoterreno.")),
        ("motor_tractor", tr("Motor de tractor"), tr("El motor de un tractor, lento y a golpes.")),
        ("motor_bici", tr("Bicicleta"), tr("Vas en bicicleta: el clic de la cadena.")),
        ("rodadura", tr("Ruedas sobre el asfalto"), tr("El ruido de los neumáticos de tu vehículo. Suena más fuerte cuanto más corres.")),
        ("arranque", tr("Arrancar el motor"), tr("Arrancas el motor de un vehículo.")),
        ("motor_apagar", tr("Apagar el motor"), tr("Giras la llave y el motor baja de vueltas hasta pararse: lo has apagado con Mayúsculas E.")),
        ("puerta_coche", tr("Puerta de un vehículo"), tr("Subes a un vehículo o te bajas de él.")),
        ("claxon", tr("Claxon de coche"), tr("Tocas el claxon, o te lo toca otro conductor. Tu chófer lo toca dos veces al llegar, y tu mecánico cuando te deja un vehículo.")),
        ("claxon_camion", tr("Bocina de camión"), tr("La bocina de un camión o de un autobús.")),
        ("claxon_bici", tr("Timbre de bicicleta"), tr("El timbre de una bicicleta.")),
        ("claxon_helados", tr("Musiquilla de la furgoneta de helados"), tr("La furgoneta de helados, en lugar de claxon, toca su musiquilla.")),
        ("frenazo", tr("Frenazo"), tr("Un vehículo frena de golpe o derrapa.")),
        ("choque", tr("Choque fuerte"), tr("Un golpe fuerte con el vehículo: se daña.")),
        ("choque_leve", tr("Choque leve"), tr("Un roce o un golpe flojo con el vehículo.")),
        ("intermitente", tr("Intermitente"), tr("Has pedido girar en el próximo cruce. Suena hasta que giras.")),
        ("radio_cambio", tr("Cambio de emisora"), tr("Cambias de emisora en la radio de un vehículo, o la apagas.")),
    ],
    "taller": [
        ("pinchazo", tr("Pinchazo"), tr("Revienta una rueda y se escapa el aire: el vehículo tira hacia un lado.")),
        ("reserva", tr("Poco combustible"), tr("Aviso de que al vehículo le queda poco combustible: busca una gasolinera.")),
        ("motor_seco", tr("Sin combustible"), tr("El motor tose y se para: te has quedado sin combustible.")),
        ("repostar", tr("Repostar"), tr("El surtidor está llenando el depósito.")),
        ("reparar", tr("Reparación en el taller"), tr("Te reparan el vehículo en un taller.")),
        ("pintura", tr("Pintar el vehículo"), tr("Te pintan el vehículo en un taller: la policía deja de reconocerlo.")),
        ("alarma", tr("Alarma de coche"), tr("Ha saltado la alarma de un vehículo o de un local.")),
        ("ganzua", tr("Ganzúa"), tr("Estás forzando la cerradura de un vehículo.")),
        ("cristal", tr("Cristales rotos"), tr("Se rompe un cristal: una ventanilla o un escaparate.")),
        ("fuego", tr("Fuego"), tr("Un vehículo o un edificio está ardiendo. Si es un vehículo, va a explotar: aléjate.")),
    ],
    "transporte": [
        ("motor_lancha", tr("Motor de lancha"), tr("El motor de una lancha o de otra embarcación rápida.")),
        ("motor_barco", tr("Motor de barco"), tr("El motor de un barco grande: un pesquero, un velero o un yate.")),
        ("sirena_barco", tr("Sirena de barco"), tr("Un barco zarpa. En el mar, también marca que anochece.")),
        ("motor_helicoptero", tr("Helicóptero"), tr("Las palas de un helicóptero en el que vas tú.")),
        ("motor_avioneta", tr("Avioneta"), tr("El zumbido de la hélice de una avioneta.")),
        ("avion", tr("Avión de pasajeros"), tr("Vas de viaje en avión: el zumbido de la cabina en vuelo.")),
        ("avion_despegue", tr("Despegue del avión"), tr("El avión acelera por la pista y despega.")),
        ("tren", tr("Tren"), tr("Vas de viaje en tren: el vagón en marcha, con el traqueteo de los raíles.")),
        ("tren_silbato", tr("Silbato del tren"), tr("El tren sale de la estación.")),
        ("tranvia", tr("Tranvía"), tr("Vas en tranvía: un zumbido eléctrico sobre raíles.")),
        ("tranvia_campana", tr("Campana del tranvía"), tr("El tranvía arranca: dos toques de campana.")),
        ("tono_altitud", tr("Tono de altitud"), tr("Pilotando, una nota que suena cada vez que cambias de altura: cuanto más aguda, más alto vuelas.")),
        ("tono_alineacion", tr("Tono de alineación"), tr("Pilotando sin piloto automático, dos chasquidos que suenan hacia el lado al que tienes que virar. Por el centro y más agudos, vas bien encarado.")),
        ("turbulencia", tr("Turbulencia"), tr("El aparato se zarandea: hay turbulencias, o estás atravesando una tormenta.")),
        ("alarma_cabina", tr("Alarma de cabina"), tr("Pilotando, cuatro pitidos apremiantes: queda muy poco combustible, hay un obstáculo o tráfico delante, o el motor se ha parado.")),
        ("aterrizaje", tr("Aterrizaje"), tr("El aparato toca tierra: un golpe, el chirrido de las ruedas y la rodadura que se apaga.")),
    ],
    "disparos": [
        ("disparo_pistola", tr("Disparo de pistola"), tr("Alguien dispara una pistola.")),
        ("disparo_revolver", tr("Disparo de revólver"), tr("Alguien dispara un revólver: más grave y rotundo que la pistola.")),
        ("disparo_silenciado", tr("Disparo de pistola con silenciador"), tr("Un disparo apagado: apenas lo oye nadie alrededor.")),
        ("disparo_rafaga", tr("Disparo de pistola de ráfagas"), tr("Un disparo seco y muy corto, que se repite muy deprisa.")),
        ("disparo_subfusil", tr("Disparo de subfusil"), tr("Alguien dispara un subfusil o una ametralladora: ráfagas rápidas.")),
        ("disparo_escopeta", tr("Disparo de escopeta"), tr("Alguien dispara una escopeta: un estampido ancho.")),
        ("disparo_corredera", tr("Disparo de escopeta de corredera"), tr("Un estampido grave y, detrás, la corredera.")),
        ("disparo_rifle", tr("Disparo de rifle"), tr("Alguien dispara un rifle de precisión o una carabina: seco y con eco.")),
        ("disparo_palanca", tr("Disparo de rifle de palanca"), tr("El disparo y, detrás, la palanca que carga el siguiente.")),
        ("disparo_fusil", tr("Disparo de fusil de asalto"), tr("Alguien dispara un fusil de asalto.")),
        ("disparo_semiautomatico", tr("Disparo de fusil semiautomático"), tr("Alguien dispara un fusil semiautomático: tiros sueltos y fuertes.")),
        ("cohete", tr("Disparo del lanzacohetes"), tr("Sale un cohete: después vendrá la explosión.")),
        ("lanzagranadas", tr("Disparo del lanzagranadas"), tr("Un golpe hueco, de tubo: sale una granada.")),
        ("lanzar", tr("Lanzamiento"), tr("Alguien lanza una granada o un cóctel molotov, o dispara una ballesta.")),
    ],
    "combate": [
        ("tono_objetivo", tr("Enemigo fijado, a tiro"), tr("Suena desde donde está el enemigo fijado: está dentro del alcance de tu arma.")),
        ("tono_apuntado", tr("Enemigo fijado, fuera de alcance"), tr("Suena desde donde está el enemigo fijado: está demasiado lejos para tu arma.")),
        ("amartillar", tr("Van a dispararte"), tr("Un enemigo prepara el arma: medio segundo después disparará. También suena cuando cambias de arma.")),
        ("bala_silbido", tr("Bala que falla"), tr("Un disparo te ha pasado rozando.")),
        ("bala_impacto", tr("Impacto de bala"), tr("Una bala da en una pared, en un vehículo o en otra cosa.")),
        ("recarga", tr("Recarga"), tr("Recargas el arma.")),
        ("sin_balas", tr("Sin balas"), tr("Aprietas el gatillo y el arma está vacía: recarga o cambia de arma.")),
        ("recoger_municion", tr("Munición recogida"), tr("Recoges munición o un arma que ha soltado un enemigo caído: un cargador que entra y el cerrojo.")),
        ("golpe", tr("Golpe que acierta"), tr("Un puñetazo, un batazo o un atropello que da en alguien.")),
        ("golpe_aire", tr("Golpe al aire"), tr("Un golpe que no da en nadie.")),
        ("navaja", tr("Tajo de navaja"), tr("Un tajo de navaja, de machete o de katana.")),
        ("hacha", tr("Golpe de hacha"), tr("Un golpe de hacha: el silbido y el golpe sordo del filo.")),
        ("explosion", tr("Explosión"), tr("Ha explotado una granada, un cohete o un vehículo.")),
        ("dolor", tr("Te han herido"), tr("Has recibido daño.")),
        ("latido", tr("Latido"), tr("Te queda muy poca salud: cúrate o ponte a cubierto.")),
        ("curar", tr("Curación"), tr("Recuperas salud, o una ambulancia atiende a los heridos.")),
        ("dolor_npc", tr("Quejido de un hombre"), tr("Has herido a un hombre.")),
        ("dolor_mujer", tr("Quejido de una mujer"), tr("Has herido a una mujer.")),
        ("muerte_npc", tr("Alguien cae"), tr("Alguien cae abatido.")),
        ("hospital_despertar", tr("Despertar en el hospital"), tr("Has perdido el conocimiento y despiertas en el hospital.")),
    ],
    "policia": [
        ("estrella_sube", tr("Sube el nivel de búsqueda"), tr("La policía te busca con más ganas.")),
        ("estrella_baja", tr("Baja el nivel de búsqueda"), tr("La policía te busca con menos ganas.")),
        ("buscando", tr("Te están buscando"), tr("Te buscan pero no te ven: sigue así unos segundos y los despistarás. Más agudo, es el helicóptero el que no te ve.")),
        ("policia_perdida", tr("Policía despistada"), tr("Ya no te buscan.")),
        ("sirena", tr("Sirena de policía"), tr("Un coche patrulla que va a por ti, o un camión de bomberos.")),
        ("sirena_ambulancia", tr("Sirena de ambulancia"), tr("Una ambulancia: la tuya, o la que acude tras un tiroteo o un atropello.")),
        ("helicoptero_policia", tr("Helicóptero de la policía"), tr("Con el nivel de búsqueda más alto, el helicóptero de la policía: se le oye llegar y dar vueltas por encima.")),
        ("megafono", tr("Altavoz del helicóptero"), tr("El helicóptero de la policía te habla por el altavoz: un acople y una voz metálica. Lo que dice se lee a continuación.")),
        ("esposas", tr("Esposas"), tr("Te detienen.")),
        ("celda", tr("Puerta del calabozo"), tr("Te han detenido y te encierran: la puerta del calabozo.")),
        ("multa", tr("Multa"), tr("Te han puesto una multa: el silbato del agente.")),
        ("emisora", tr("Emisora de la policía"), tr("Cuando trabajas de agente: el chasquido del canal y dos pitidos. Entras de servicio, llega un aviso o termina el turno.")),
    ],
    "gente": [
        ("paso_npc", tr("Pasos de otra persona"), tr("Alguien camina cerca de ti.")),
        ("murmullo", tr("Murmullo"), tr("Un peatón murmura al hablarte, o dos que pasan van hablando entre ellos.")),
        ("grito", tr("Grito"), tr("Un grito: el tuyo para espantar a la gente, o el de un enemigo que te ha visto y avisa a los suyos.")),
        ("grito_hombre", tr("Grito de un hombre asustado"), tr("Un hombre grita de susto y sale corriendo.")),
        ("grito_mujer", tr("Grito de una mujer asustada"), tr("Una mujer grita de susto y sale corriendo.")),
        ("panico", tr("Pánico en la calle"), tr("Mucha gente grita y huye a la vez: un tiroteo, una explosión o un atropello ha sembrado el pánico a tu alrededor.")),
        ("evento", tr("Suceso callejero"), tr("Algo está pasando cerca: un atraco, unos pandilleros o un maletín perdido. Ayudar es opcional.")),
        ("ladrido", tr("Ladrido"), tr("Un perro ladra. Si es el tuyo, avisa de un enemigo cercano o de que ha olfateado algo.")),
        ("perro_olfatea", tr("El perro olfatea"), tr("Tu perro busca por el olfato el objeto más cercano.")),
    ],
    "casa": [
        ("comer", tr("Comer"), tr("Comes algo: recuperas fuerzas.")),
        ("beber", tr("Beber"), tr("Bebes unos tragos.")),
        ("nevera", tr("Nevera"), tr("Abres la nevera de casa o guardas la compra: la goma de la puerta y el zumbido del motor.")),
        ("cocina_cortar", tr("Cocinar, el cuchillo"), tr("Empiezas a cocinar: el cuchillo picando sobre la tabla.")),
        ("cocina_freir", tr("Cocinar, la sartén"), tr("Cocinas a la sartén: el aceite chisporroteando.")),
        ("cocina_hervir", tr("Cocinar, la olla"), tr("Cocinas a la olla: el agua borboteando.")),
        ("plato_servido", tr("Plato servido"), tr("El plato está hecho: la loza en la mesa y los cubiertos.")),
        ("timbre", tr("Timbre de casa"), tr("Llaman al timbre de tu casa: llega la comida que has pedido a domicilio. Dos notas, din, don.")),
    ],
    "dinero": [
        ("dinero", tr("Dinero"), tr("Has ganado dinero.")),
        ("caja", tr("Caja registradora"), tr("Pagas una compra o haces una operación en el banco.")),
        ("cesta", tr("Cesta de la compra"), tr("Echas un producto a la cesta: un golpe sordo y el alambre que tiembla. Más grave, lo devuelves al estante.")),
        ("bolsa", tr("Bolsa"), tr("Has comprado acciones en la bolsa.")),
        ("recoger", tr("Objeto recogido"), tr("Recoges un objeto del suelo.")),
    ],
    "avisos": [
        ("menu_mover", tr("Menú, pasar de opción"), tr("Pasas de una opción a otra en un menú.")),
        ("menu_ok", tr("Menú, elegir"), tr("Eliges una opción de un menú.")),
        ("menu_atras", tr("Menú, volver atrás"), tr("Vuelves atrás en un menú.")),
        ("menu_borde", tr("Menú, principio o final"), tr("Has llegado al principio o al final de un menú, o al borde del mapa.")),
        ("menu_ajuste", tr("Menú, cambiar un valor"), tr("Cambias el valor de una opción con izquierda o derecha.")),
        ("error", tr("Error"), tr("Eso no se puede hacer ahora.")),
        ("notificacion", tr("Aviso"), tr("Aviso general: una misión nueva, un destino marcado o un mensaje. Lo que es se dice a continuación.")),
        ("movil", tr("Móvil"), tr("Abres el móvil, o te llega una llamada o un mensaje.")),
        ("dialogo", tr("Frase de un diálogo"), tr("Empieza una frase de un diálogo.")),
        ("guardado", tr("Partida guardada"), tr("La partida se ha guardado.")),
        ("logro", tr("Logro conseguido"), tr("Has conseguido uno de los logros del juego.")),
        ("nivel", tr("Sube una habilidad"), tr("Has mejorado en conducción, puntería, resistencia o pesca.")),
        ("reloj", tr("Cuenta atrás"), tr("Quedan menos de diez segundos: suena con cada segundo.")),
        ("pasan_horas", tr("Pasan las horas"), tr("El tiempo pasa de golpe: duermes, te escondes o esperas.")),
        ("gallo", tr("Amanece"), tr("Son las siete de la mañana: canta un gallo.")),
        ("buho", tr("Anochece"), tr("Son las nueve de la noche: un búho.")),
        ("campanadas", tr("Medianoche"), tr("Empieza un día nuevo: cobras tus negocios y cambian los precios.")),
    ],
    "trabajo": [
        ("mision_ok", tr("Misión completada"), tr("Has completado una misión.")),
        ("mision_fallo", tr("Misión fallida"), tr("Has fallado una misión, o has caído.")),
        ("jornada", tr("Jornada de trabajo"), tr("Haces una jornada de trabajo: la sirena de la fábrica y pasan las horas.")),
        ("ascenso", tr("Ascenso"), tr("Subes de rango en un oficio y cobras más, o te ascienden de puesto en tu contrato fijo.")),
        ("despido", tr("Despido"), tr("Te han despedido de tu empleo fijo: un portazo y tres notas que bajan.")),
        ("diploma", tr("Curso terminado"), tr("Has terminado un curso en una academia y sube una habilidad.")),
        ("titulo", tr("Título conseguido"), tr("Has terminado los estudios de un título: una fanfarria corta y un acorde largo.")),
        ("inspeccion", tr("Inspección"), tr("Ha pasado una inspección por uno de tus negocios: golpes de nudillos en la puerta, papeles y un sello. "
         "Si ha encontrado algo, lo tienes en el móvil, en Vida, reputación y consecuencias.")),
        ("factura", tr("Factura, impuesto o cuota"), tr("Te han cobrado las facturas, los impuestos o la cuota de un crédito: una impresora de tiques y una nota grave.")),
        ("donativo", tr("Donativo"), tr("Haces un donativo: monedas que caen.")),
        ("prestigio", tr("Prestigio ciudadano"), tr("Los vecinos te ven con mejores ojos.")),
        ("fama", tr("Cambia tu fama"), tr("Cambia cómo te ven en la calle.")),
        ("animo_sube", tr("Mejora tu ánimo"), tr("Tu ánimo sube de nivel: apuntas mejor.")),
        ("animo_baja", tr("Empeora tu ánimo"), tr("Tu ánimo baja de nivel: con el ánimo muy bajo apuntas peor y corres menos.")),
    ],
    "territorios": [
        ("territorio", tr("Territorio conquistado"), tr("Un barrio pasa a ser tuyo.")),
        ("amenaza_barrio", tr("Amenaza sobre un barrio tuyo"), tr("Una banda prepara un asalto a un barrio tuyo, o acaba de empezarlo: tambores graves, cada vez más seguidos, y dos notas tensas. "
         "Mira el móvil, en Territorios.")),
        ("barrio_defendido", tr("Barrio defendido"), tr("Has rechazado un asalto, o has arrasado el escondite de una banda: un redoble y tres notas que suben.")),
        ("barrio_perdido", tr("Barrio perdido"), tr("Una banda te ha quitado un barrio: una campana grave y notas que bajan.")),
    ],
    "linea": [
        ("amigo_entra", tr("Amigo que entra"), tr("Jugando con amigos, alguien se une a la partida, o te conectas tú. Tres notas que suben.")),
        ("amigo_sale", tr("Amigo que se va"), tr("Jugando con amigos, alguien se va, o te desconectas tú. Tres notas que bajan.")),
        ("chat", tr("Mensaje"), tr("Jugando con amigos, llega o se envía un mensaje: dos notas agudas y rápidas. Se lee en voz alta a continuación.")),
        ("chat_personaje", tr("Mensaje en personaje"), tr("En un servidor, alguien que está cerca habla como su personaje, o lo haces tú: dos notas graves y cálidas, más lentas que las del mensaje normal.")),
        ("chat_fuera", tr("Mensaje fuera de personaje"), tr("En un servidor, alguien habla como jugador y no como su personaje: dos toques secos de madera. Lo oye todo el servidor.")),
        ("chat_accion", tr("Acción de un personaje"), tr("En un servidor, alguien que está cerca cuenta lo que hace su personaje, por ejemplo que abre una puerta: un roce corto rematado con una nota.")),
        ("espera_servidor", tr("Espera al servidor"), tr("En un servidor, se ha cortado la conexión o el servidor se está actualizando, y el juego espera para volver a entrar solo: "
         "dos notas lentas y flojas, la segunda más grave. Se repite cada pocos segundos.")),
    ],
    "juegos": [
        ("pesca_lanzar", tr("Pesca, lanzar el anzuelo"), tr("Echas la caña: el anzuelo cae al agua.")),
        ("pez_pica", tr("Pesca, pican"), tr("Un pez ha mordido el anzuelo: tira enseguida, antes de un segundo.")),
        ("carrete", tr("Pesca, recoger el sedal"), tr("Recoges el sedal con el carrete.")),
        ("diana", tr("Diana de la galería de tiro"), tr("Aparece una diana: dispara hacia el lado por el que suena.")),
        ("diana_ok", tr("Diana acertada"), tr("Has acertado una diana de la galería de tiro.")),
        ("ruleta", tr("Ruleta"), tr("Gira la ruleta del casino.")),
        ("dados", tr("Dados"), tr("Ruedan los dados.")),
        ("campana_ring", tr("Campana del combate de boxeo"), tr("Empieza un combate en el gimnasio.")),
        ("simon_0", tr("Máquina de memoria, flecha arriba"), tr("La nota más aguda de la máquina de memoria de sonidos.")),
        ("simon_1", tr("Máquina de memoria, flecha derecha"), tr("La segunda nota más aguda de la máquina de memoria de sonidos.")),
        ("simon_2", tr("Máquina de memoria, flecha abajo"), tr("La nota más grave de la máquina de memoria de sonidos.")),
        ("simon_3", tr("Máquina de memoria, flecha izquierda"), tr("La segunda nota más grave de la máquina de memoria de sonidos.")),
    ],
    "ambientes": [
        ("amb_ciudad", tr("Ambiente de ciudad"), tr("Estás en el centro de la ciudad: tráfico lejano.")),
        ("amb_residencial", tr("Ambiente de barrio tranquilo"), tr("Estás en un barrio residencial.")),
        ("amb_industrial", tr("Ambiente de polígono industrial"), tr("Estás en un polígono industrial: maquinaria.")),
        ("amb_parque", tr("Ambiente de parque"), tr("Estás en un parque: pájaros.")),
        ("amb_playa", tr("Ambiente de playa"), tr("Estás en la playa: olas.")),
        ("amb_puerto", tr("Ambiente de puerto"), tr("Estás en el puerto: olas y una sirena de barco lejana.")),
        ("amb_mar", tr("Ambiente de mar abierto"), tr("Estás en el mar, lejos de la costa.")),
        ("amb_campo", tr("Ambiente de campo"), tr("Estás en el campo: pájaros y cencerros.")),
        ("amb_montana", tr("Ambiente de montaña"), tr("Estás en la montaña: viento.")),
        ("amb_noche", tr("Ambiente de noche"), tr("Es de noche: grillos.")),
        ("lluvia", tr("Lluvia"), tr("Está lloviendo: el suelo resbala más y se oye peor.")),
        ("trueno", tr("Trueno"), tr("Un trueno, cuando llueve.")),
        ("viento_playa", tr("Viento"), tr("El viento en la cara, cuando vas en helicóptero.")),
        ("multitud", tr("Murmullo de mucha gente"), tr("Hay mucha gente alrededor.")),
        ("gaviota", tr("Gaviotas"), tr("Gaviotas, en la playa y en el puerto.")),
        ("pajaro", tr("Pájaro"), tr("Un pájaro, en los parques y en los barrios tranquilos.")),
        ("martillo", tr("Martillazos de obra"), tr("Una obra a lo lejos, en el puerto y en los polígonos.")),
        ("claxon_lejano", tr("Claxon lejano"), tr("Un claxon a lo lejos, de ambiente: no es para ti.")),
        ("sirena_lejana", tr("Sirena lejana"), tr("Una sirena a lo lejos, de ambiente: no vienen a por ti.")),
    ],
    "relaciones": [
        ("afinidad_sube", tr("Sube la afinidad"), tr("Alguien te aprecia más, por una charla, una cita o un regalo.")),
        ("afinidad_baja", tr("Baja la afinidad"), tr("Alguien se ha disgustado contigo.")),
        ("cita", tr("Cita"), tr("Tienes una cita, o un momento de complicidad con tu pareja.")),
        ("regalo", tr("Regalo"), tr("Entregas un regalo: papel de envolver.")),
        ("pareja", tr("Nueva pareja"), tr("Empezáis una relación: dos latidos y un arpegio.")),
        ("noche_juntos", tr("Noche juntos"), tr("Pasáis la noche juntos. La escena se resuelve con un fundido.")),
        ("ruptura", tr("Ruptura"), tr("Se acaba una relación.")),
    ],
    "sustancias": [
        ("tomar_copa", tr("Tomar una copa"), tr("Tomas alcohol: se sirve y se brinda.")),
        ("tomar_hierba", tr("Tomar hierba"), tr("Fumas hierba: mechero, calada y humo.")),
        ("tomar_pastillas", tr("Tomar pastillas"), tr("Tomas una pastilla: el blíster y un trago.")),
        ("tomar_polvo", tr("Tomar polvo blanco"), tr("Tomas polvo blanco: una tarjeta y una inspiración.")),
        ("tomar_cristal", tr("Tomar cristal"), tr("Tomas cristal: crepita.")),
        ("bajon", tr("Bajón"), tr("Se pasa el efecto de una sustancia y llega el bajón.")),
        ("abstinencia", tr("Abstinencia"), tr("Tu cuerpo pide una sustancia de la que dependes: un temblor.")),
        ("sobredosis", tr("Sobredosis"), tr("Te has pasado: el corazón se frena, suena un pitido continuo y acabas en el hospital.")),
        ("trato", tr("Trato cerrado"), tr("Has comprado o vendido mercancía: billetes y un paquete que cambia de manos.")),
        ("rechazo", tr("Rechazo"), tr("A esa persona no le interesa lo que ofreces.")),
        ("paisano", tr("Policía de paisano"), tr("El comprador era un policía de paisano.")),
        ("precio_ganga", tr("Precio de ganga"), tr("En el proveedor, esa sustancia hoy está muy barata.")),
        ("precio_escasez", tr("Precio de escasez"), tr("En el proveedor, esa sustancia hoy está muy cara.")),
    ],
}

# Los imprescindibles para orientarse y sobrevivir, en el orden en que conviene aprenderlos: el primer grupo de Aprender los sonidos.
IMPORTANTES = (
    "baliza", "baliza_destino", "llegada", "cruce", "radar", "tono_pared", "tono_libre", "choque_pared", "semaforo_tic", "semaforo_pio", "semaforo_rojo", "semaforo_verde",
    "paso_acera0", "paso_calzada0", "paso_hierba0", "paso_arena0", "paso_muelle0", "paso_via0", "paso_npc",
    "loc_mision", "loc_objeto", "loc_casete", "loc_vehiculo", "loc_lugar", "puerta_entrar", "puerta_salir",
    "lugar_casa", "lugar_armeria", "lugar_comida", "lugar_tienda", "lugar_hospital", "lugar_comisaria", "lugar_taller", "lugar_bar", "lugar_casino",
    "lugar_taxi", "lugar_periodico", "lugar_fuente", "lugar_iglesia", "lugar_banco", "lugar_estacion", "lugar_salida", "lugar_embarcadero", "lugar_boya",
    "lugar_gimnasio", "lugar_cine", "lugar_tranvia", "lugar_tren", "lugar_aeropuerto", "lugar_helipuerto", "lugar_prision", "lugar_mina", "lugar_rio",
    "lugar_protectora", "lugar_empleo", "lugar_academia", "lugar_ong", "lugar_club", "lugar_proveedor",
    "sonar", "bordillo", "intermitente", "frenazo", "choque", "alarma", "ganzua", "fuego", "explosion",
    "sirena", "estrella_sube", "buscando", "policia_perdida",
    "tono_objetivo", "tono_apuntado", "amartillar", "bala_silbido", "dolor", "latido",
    "evento", "ladrido", "perro_olfatea", "reloj", "dinero", "mision_ok", "mision_fallo", "nivel", "logro",
    "gallo", "buho", "campanadas", "cursor_mapa",
    "motor_lancha", "motor_barco", "motor_helicoptero", "motor_avioneta", "tono_altitud", "tono_alineacion", "alarma_cabina", "turbulencia", "aterrizaje", "avion", "avion_despegue", "tren", "tren_silbato", "tranvia", "tranvia_campana",
    "brazada", "bajo_agua", "pez_pica", "diana", "simon_0", "simon_2",
    "ascenso", "despido", "inspeccion", "factura", "titulo", "diploma", "prestigio", "fama", "animo_sube", "animo_baja", "bolsa",
    "territorio", "amenaza_barrio", "barrio_defendido", "barrio_perdido",
    "amigo_entra", "amigo_sale", "chat", "chat_personaje", "chat_fuera", "chat_accion", "espera_servidor",
    "afinidad_sube", "afinidad_baja", "pareja", "ruptura", "tomar_copa", "tomar_hierba", "tomar_pastillas", "tomar_polvo", "tomar_cristal",
    "bajon", "abstinencia", "sobredosis", "trato", "rechazo", "paisano",
)

# Los sonidos de orientación: en los packs que vienen con el juego son siempre los de serie.
_ORIENTACION = ("tono_", "semaforo_", "baliza", "loc_", "lugar_")
_ORIENTACION_SUELTOS = {"sonar", "bordillo", "cruce", "radar", "cursor_mapa"}

_CLAVES = [g[2] for g in GRUPOS]
FICHAS = {s: (_CLAVES.index(k), nombre, texto) for k, lista in SONIDOS.items() for s, nombre, texto in lista}
DESCRIPCIONES = {s: f[2] for s, f in FICHAS.items()}
_ADULTOS = {"relaciones", "sustancias"}


def es_orientacion(nombre):
    return nombre.startswith(_ORIENTACION) or nombre in _ORIENTACION_SUELTOS


def es_del_juego(nombre):
    """Las canciones de la radio y la música de ambiente comparten mezclador con los sonidos, pero no son sonidos del juego."""
    return nombre in FICHAS or not nombre.startswith(("radio_", "musica_", "_"))


def nombre(sonido):
    """El nombre que se dice. Para un archivo que no está apuntado, su nombre de archivo con espacios."""
    f = FICHAS.get(sonido)
    return f[1] if f else sonido.replace("_", " ").capitalize()


def describir(sonido):
    """Qué significa oírlo en el juego."""
    f = FICHAS.get(sonido)
    return f[2] if f else tr("Sonido del juego.")


def grupo_de(sonido):
    """El número de su grupo en GRUPOS; len(GRUPOS) si no está apuntado."""
    f = FICHAS.get(sonido)
    return f[0] if f else len(GRUPOS)


def titulo_de(sonido):
    k = grupo_de(sonido)
    return GRUPOS[k][0] if k < len(GRUPOS) else OTROS


def sin_tildes(texto):
    """Para buscar: minúsculas y sin tildes ni diéresis. La eñe se queda como ene, para quien no la tiene a mano."""
    return "".join(c for c in unicodedata.normalize("NFD", str(texto).casefold()) if not unicodedata.combining(c))


def orden(texto):
    """Clave para ordenar como en un diccionario español: sin contar tildes ni mayúsculas, y la eñe detrás de la ene."""
    return sin_tildes(str(texto).casefold().replace("ñ", "n{")), str(texto)


def clasificar(nombres):
    """Todos los sonidos, repartidos en sus grupos: [(título, [sonido, ...]), ...], los grupos en su orden y dentro de cada
    uno por orden alfabético del nombre que se dice. Ninguno se queda fuera: el que no esté apuntado va a «Otros sonidos»."""
    grupos = {}
    for s in nombres:
        if es_del_juego(s):
            grupos.setdefault(grupo_de(s), []).append(s)
    return [(GRUPOS[k][0] if k < len(GRUPOS) else OTROS, sorted(set(v), key=lambda s: orden(nombre(s)))) for k, v in sorted(grupos.items())]


def importantes(nombres):
    disponibles = set(nombres)
    return [s for s in IMPORTANTES if s in disponibles]


def es_de_adultos(sonido):
    """Solo se oye con el contenido para adultos activado: los dos últimos grupos."""
    k = grupo_de(sonido)
    return k < len(GRUPOS) and GRUPOS[k][2] in _ADULTOS


def texto_aprender(sonido, suelto=False):
    """Lo que se dice de un sonido en Aprender los sonidos: su nombre y qué significa. Con suelto, fuera de su grupo,
    los del contenido para adultos lo dicen detrás del nombre, porque ahí no lo dice el título del grupo."""
    aparte = tr(", contenido para adultos") if suelto and es_de_adultos(sonido) else ""
    return f"{nombre(sonido)}{aparte}. {describir(sonido)}"


def buscar(texto, nombres):
    """Los sonidos que tienen todas las palabras buscadas en el nombre, en la explicación, en el grupo o en el nombre del archivo,
    sin contar tildes ni mayúsculas. Primero los que las tienen en el nombre. Devuelve [(sonido, título de su grupo), ...]."""
    palabras = sin_tildes(texto).replace("_", " ").split()
    if not palabras:
        return []
    salida = []
    for titulo, lista in clasificar(nombres):
        for s in lista:
            corto = sin_tildes(nombre(s))
            largo = " ".join((corto, sin_tildes(describir(s)), sin_tildes(titulo), s.replace("_", " ")))
            if all(p in largo for p in palabras):
                salida.append((0 if all(p in corto for p in palabras) else 1, len(salida), s, titulo))
    return [(s, titulo) for _, _, s, titulo in sorted(salida)]
