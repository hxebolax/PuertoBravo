"""Las opciones del servidor, descritas una sola vez.

De esta descripción salen cuatro cosas, para que nunca se desajusten entre sí:

- los valores de serie con los que arranca el servidor (``valores_de_serie``);
- el ejemplo de ``servidor.conf`` y el archivo que se guarda desde el panel (``texto_conf``, ``guardar``);
- la comprobación de lo que escribe quien administra, con mensajes claros (``validar``, ``leer``);
- la interfaz del panel y el apartado de opciones de la documentación (``html_opciones``).

Solo usa la biblioteca de serie: el servidor tiene que poder funcionar con Python y nada más.
"""
import html
import os
import textwrap

from . import idioma
from .idioma import es, tr

TEXTO, SECRETO, ENTERO, ELECCION, SINO = "texto", "secreto", "entero", "eleccion", "sino"

SECCIONES = (
    ("general", tr("General"), tr("Cómo se llama el servidor, qué se le dice a quien entra y cuánta gente cabe.")),
    ("red", tr("Red y cifrado"), tr("Por dónde escucha el servidor y cómo protege la conexión.")),
    ("acceso", tr("Acceso y administración"), tr("Quién puede entrar, quién manda y a quién no se deja pasar.")),
    ("versiones", tr("Versiones del juego"), tr("Qué versiones del juego pueden jugar juntas en este servidor.")),
    ("datos", tr("Datos y copias de seguridad"), tr("Dónde se guarda todo, cada cuánto y cuántas copias se conservan.")),
    ("combate", tr("Combate entre jugadores"), tr("Las reglas de las peleas, los atracos y las recompensas.")),
    ("mundo", tr("Mundo vivo"), tr("El tráfico, la gente de la calle, la policía y los personajes que lleva el servidor.")),
    ("economia", tr("Economía y vehículos"), tr("El dinero que reconoce el servidor y los vehículos que se dejan en la calle.")),
    ("negocios", tr("Casas y negocios"), tr("Venderlos, perderlos por no entrar y que nadie se quede con todos los negocios.")),
    ("bandas", tr("Bandas y territorios"), tr("Lo que cuesta fundar una banda, reclamar un barrio y declarar una guerra.")),
    ("rol", tr("Rol y convivencia"), tr("Los canales de chat para interpretar a tu personaje y lo que se oye de los demás jugadores.")),
    ("vida", tr("Vida honrada"), tr("Los contratos fijos con su nómina y el trato de las tiendas según el prestigio de cada jugador.")),
)

SI_NO = (("si", "sí"), ("no", "no"))
_VERDADERO = ("si", "sí", "1", "true", "yes", "s", "verdadero")
_FALSO = ("no", "0", "false", "n", "falso")


class Opcion:
    """Una opción: su nombre en servidor.conf, dónde va en el panel, qué es y entre qué valores puede estar."""

    __slots__ = ("clave", "seccion", "etiqueta", "ayuda", "tipo", "defecto", "minimo", "maximo", "valores", "reinicio", "largo")

    def __init__(self, clave, seccion, etiqueta, ayuda, tipo, defecto, minimo=None, maximo=None, valores=(), reinicio=False, largo=200):
        self.clave, self.seccion, self.etiqueta, self.ayuda, self.tipo, self.defecto = clave, seccion, etiqueta, ayuda, tipo, defecto
        self.minimo, self.maximo, self.valores, self.reinicio, self.largo = minimo, maximo, tuple(valores), reinicio, largo

    def permitidos(self):
        """Los valores que se pueden escribir, tal como van en el archivo."""
        if self.tipo == SINO:
            return ("si", "no")
        return tuple(v for v, _ in self.valores)

    def descripcion_valores(self):
        """En una frase, qué se puede poner. Sirve para el archivo, para la ayuda del panel y para la documentación."""
        if self.tipo == SINO:
            return tr("Valores: si o no.")
        if self.tipo == ELECCION:
            return tr("Valores: %s.") % "; ".join("%s (%s)" % (v, d) for v, d in self.valores)
        if self.tipo == ENTERO:
            return tr("Un número entero entre %d y %d.") % (self.minimo, self.maximo)
        if self.tipo == SECRETO:
            return tr("Un texto de hasta %d letras. Se guarda tal cual en el archivo: no lo enseñes.") % self.largo
        return tr("Un texto de hasta %d letras.") % self.largo


def _o(*a, **k):
    return Opcion(*a, **k)


OPCIONES = (
    # ------------------------------------------------------------------ general
    _o("nombre", "general", tr("Nombre del servidor"),
       tr("El nombre con el que los jugadores ven tu servidor en su lista."), TEXTO, es("Servidor de Puerto Bravo"), largo=60),
    _o("bienvenida", "general", tr("Bienvenida"),
       tr("Lo que se le dice a cada jugador nada más entrar."), TEXTO, es("Bienvenido. Juega limpio."), largo=300),
    _o("mensaje_dia", "general", tr("Mensaje del día"),
       tr("Un aviso que oye cada jugador al entrar, después de la bienvenida: una quedada, una norma nueva. Vacío, ninguno. "
       "Se puede cambiar con el servidor en marcha."), TEXTO, "", largo=300),
    _o("max_jugadores", "general", tr("Máximo de jugadores a la vez"),
       tr("Cuántos jugadores pueden estar dentro a la vez. Con 0 no hay límite. Los administradores entran aunque esté lleno. "
       "Los personajes que lleva el servidor no cuentan."), ENTERO, 32, 0, 100000),
    _o("adultos", "general", tr("Contenido para adultos"),
       tr("Con no, quien entra juega sin el contenido para adultos aunque lo tenga activado en su juego."), SINO, "no"),
    _o("parada_aviso", "general", tr("Segundos de aviso antes de reiniciar por actualización o mantenimiento"),
       tr("Cuando el servidor se va a parar para actualizarlo o por mantenimiento (las órdenes actualizar y reiniciar, o la "
       "actualización del juego en Windows), avisa a los jugadores con esta cuenta atrás antes de cerrarse. Con 0 se cierra "
       "enseguida. Los juegos esperan y vuelven a entrar solos cuando el servidor vuelve."), ENTERO, 20, 0, 120),
    _o("parada_espera", "general", tr("Guardado final: segundos que se espera al parar"),
       tr("Al pararse, el servidor pide a cada juego que guarde su personaje y espera hasta estos segundos a que llegue. "
       "Si todos guardan antes, no espera más."), ENTERO, 6, 0, 30),
    _o("idioma", "general", tr("Idioma del servidor"),
       tr("En qué idioma escribe el servidor lo que lee quien lo administra: la consola, el registro, la ayuda de las órdenes y "
          "los comentarios de servidor.conf. Lo que oyen los jugadores no cambia: el servidor se lo manda en español y el juego de "
          "cada uno lo dice en el suyo, así que en un mismo servidor puede jugar gente de idiomas distintos. Si el servidor va "
          "dentro del panel, habla el idioma del juego."),
       ELECCION, "auto", valores=(("auto", tr("el del sistema: si está en español, español; si no, inglés, o el del sistema si hay "
                                             "traducción a él")),) + tuple(idioma.disponibles().items()), reinicio=True),
    # ---------------------------------------------------------------------- red
    _o("puerto", "red", tr("Puerto"),
       tr("El puerto en el que escucha el servidor. Es el que hay que abrir en el router para que entren desde fuera de casa. "
       "Con 0, el sistema elige uno libre cada vez, cosa que solo sirve para pruebas."), ENTERO, 47820, 0, 65535, reinicio=True),
    _o("interfaz", "red", tr("Dirección en la que escucha"),
       tr("Con 0.0.0.0 escucha en todas las conexiones del equipo, que es lo normal. Con 127.0.0.1 solo se puede entrar desde este "
       "mismo ordenador. También vale la dirección de una sola de tus conexiones de red."), TEXTO, "0.0.0.0", reinicio=True, largo=60),
    _o("cifrado", "red", tr("Cifrado de la conexión"),
       tr("Con auto, el servidor crea su propio certificado la primera vez que arranca y cifra; no hay que instalar nada."),
       ELECCION, "auto", valores=(("auto", tr("cifra si puede, y casi siempre puede")), ("si", tr("obligatorio: si no puede cifrar, no arranca")),
                                  ("no", tr("nunca cifra"))), reinicio=True),
    _o("certificado", "red", tr("Archivo del certificado"),
       tr("Solo si quieres usar un certificado tuyo: la ruta de su archivo PEM. Vacío, el servidor usa el que crea él mismo en la "
       "carpeta de datos."), TEXTO, "", reinicio=True, largo=260),
    _o("llave", "red", tr("Archivo de la llave del certificado"),
       tr("La ruta del archivo PEM con la llave privada de tu certificado. Vacío si la llave va dentro del propio certificado "
       "o si usas el que crea el servidor."), TEXTO, "", reinicio=True, largo=260),
    _o("conexiones_por_ip", "red", tr("Conexiones a la vez desde una misma dirección"),
       tr("Cuántas conexiones se admiten a la vez desde una misma dirección de red. Con 0 no hay límite. Ojo: quienes juegan "
       "desde la misma casa comparten dirección, y detrás de Docker o de un intermediario todos pueden parecer la misma."),
       ENTERO, 0, 0, 100000),
    _o("registro_ip", "red", tr("Anotar la dirección de quien se conecta"),
       tr("Con si, el registro anota la dirección de red de cada conexión y el panel la enseña. De serie, no: el servidor "
       "no guarda ningún dato personal."), SINO, "no"),
    # ------------------------------------------------------------------- acceso
    _o("entrada", "acceso", tr("Quién puede crear un personaje"),
       tr("Solo afecta a quien entra por primera vez: quien ya tiene personaje vuelve a entrar siempre."),
       ELECCION, "abierta", valores=(("abierta", tr("cualquiera que tenga la dirección")), ("clave", tr("hay que saber la contraseña de entrada")),
                                     ("invitacion", tr("hace falta un código de un solo uso")))),
    _o("clave", "acceso", tr("Contraseña de entrada"),
       tr("La contraseña que hay que saber para crear un personaje cuando la entrada es con clave."), SECRETO, "", largo=60),
    _o("admins", "acceso", tr("Administradores"),
       tr("Nombres de jugador que administran el servidor, separados por comas. Se suman a los que se nombran con la orden admin."),
       TEXTO, "", largo=600),
    _o("primer_admin", "acceso", tr("La primera cuenta es administradora"),
       tr("Con si, la primera cuenta que se crea en el servidor es administradora: lo normal es que seas tú."), SINO, "si"),
    _o("vetados", "acceso", tr("Nombres vetados"),
       tr("Nombres de jugador que no pueden entrar, separados por comas. Se suman a las cuentas vetadas con la orden vetar."),
       TEXTO, "", largo=600),
    _o("inactividad_minutos", "acceso", tr("Expulsar por inactividad, en minutos"),
       tr("Minutos sin moverse ni hacer nada tras los que se saca a un jugador, para dejar sitio. Con 0, nunca. "
       "A los administradores no se les saca."), ENTERO, 0, 0, 1440),
    _o("varias_sesiones", "acceso", tr("Permitir dos sesiones con la misma identidad"),
       tr("Solo para pruebas. De serie, no: si alguien entra con su personaje desde otro sitio, la sesión anterior se cierra."), SINO, "no"),
    _o("permitir_trampas", "acceso", tr("Permitir menú de trampas"),
       tr("Con no, que es lo de serie, los juegos anulan por completo el menú de trampas al entrar en este servidor. Con si, el servidor deja de vigilar el dinero de todos los jugadores y cualquiera podrá ponerse el dinero que quiera."), SINO, "no"),
    # ---------------------------------------------------------------- versiones
    _o("comprobar_datos", "versiones", tr("Comprobar los datos del juego de quien entra"),
       tr("Con si, el servidor mira si el mundo que trae el juego de quien entra es el suyo, el de otra versión de verdad o uno "
       "cambiado con mods, y actúa según las opciones siguientes. Con no, no mira nada: entra cualquiera con lo que traiga, "
       "y el servidor no se pone al día con el mundo de las versiones nuevas."), SINO, "si"),
    _o("mundo_distinto", "versiones", tr("Qué hacer con quien trae datos que no se pueden comprobar"),
       tr("Quien juega con mods que cambian el mundo, o con una versión cuyos datos el servidor no puede comprobar. Con una versión "
       "de verdad distinta de la del servidor se entra siempre, pongas lo que pongas aquí."),
       ELECCION, "admitir", valores=(("admitir", tr("entra y juega en lo que tiene en común con el servidor; se le dice qué no coincide, y lo "
                                                  "que afecta a los demás lo decide el servidor con su mundo")),
                                     ("rechazar", tr("no entra: solo se juega con los datos de una versión de verdad")))),
    _o("versiones", "versiones", tr("Versiones que pueden jugar juntas"),
       tr("El servidor trabaja con el mundo de la versión más nueva que ha visto, y a cada juego le habla de lo que su versión "
       "conoce: un arma o un vehículo que no tiene le llegan como el más parecido de los suyos."),
       ELECCION, "compatibles", valores=(("compatibles", tr("pueden jugar juntos quienes tengan versiones distintas del juego, cada uno "
                                                         "con lo que su versión conoce")),
                                         ("iguales", tr("solo entra quien tenga exactamente los mismos datos que el servidor")))),
    _o("version_minima", "versiones", tr("Versión mínima del juego"),
       tr("La versión más antigua del juego con la que se puede entrar, por ejemplo 1.7.0. Vacío, cualquiera."), TEXTO, "", largo=20),
    _o("actualizar_mundo", "versiones", tr("Quién puede traer un mundo nuevo"),
       tr("El mundo del juego (lugares, armas, misiones) no va atado al servidor: se lo trae el juego de quien entra. Un servidor "
       "sin mundo toma el del primero que entra; si ese no viene firmado, lo cambia por el primero firmado que llegue."),
       ELECCION, "firmado", valores=(("firmado", tr("el de una versión más nueva se acepta de cualquiera si lo firma quien publica el juego")),
                                     ("admin", tr("además, sin firma, de un administrador: para servidores con mods")),
                                     ("no", tr("nunca: el servidor se queda con el mundo que tiene")))),
    # -------------------------------------------------------------------- datos
    _o("datos", "datos", tr("Carpeta de datos"),
       tr("La carpeta donde se guarda todo: personajes, bandas, territorios, vehículos, el certificado y las copias de seguridad."),
       TEXTO, "datos_servidor", reinicio=True, largo=260),
    _o("guardado_minutos", "datos", tr("Guardar cada tantos minutos"),
       tr("Cada cuántos minutos se guarda todo en disco. Al parar el servidor se guarda siempre."), ENTERO, 1, 1, 120),
    _o("copia_auto_horas", "datos", tr("Copia de seguridad automática, cada tantas horas"),
       tr("Cada cuántas horas hace el servidor una copia de seguridad en la carpeta copias, dentro de la de datos. Con 0, no hace ninguna."),
       ENTERO, 24, 0, 720),
    _o("copias_guardar", "datos", tr("Copias de seguridad que se conservan"),
       tr("Cuántas copias automáticas se conservan: al hacer una nueva se borran las más antiguas. Las que haces tú a mano con "
       "otro nombre no se tocan."), ENTERO, 7, 1, 365),
    _o("registro_archivo", "datos", tr("Guardar el registro en un archivo"),
       tr("Con si, lo que va diciendo el servidor se escribe también en registro.txt, dentro de la carpeta de datos."), SINO, "no"),
    # ------------------------------------------------------------------ combate
    _o("pvp", "combate", tr("Combate entre jugadores"),
       tr("Con no, los jugadores no pueden herirse, atracarse ni robarse entre sí."), SINO, "si"),
    _o("zonas_seguras", "combate", tr("Zonas seguras"),
       tr("Con si, en hospitales, comisarías, casas y dentro de los locales nadie puede herir a nadie."), SINO, "si"),
    _o("modo_pasivo", "combate", tr("Permitir el modo pasivo"),
       tr("Con si, cada jugador puede ponerse en modo pasivo: ni hiere a otros jugadores ni le hieren."), SINO, "si"),
    _o("proteccion", "combate", tr("Segundos de protección al llegar"),
       tr("Segundos sin poder herir ni ser herido al entrar y al reaparecer."), ENTERO, 20, 0, 600),
    _o("botin", "combate", tr("Botín al tumbar a otro jugador, en tanto por ciento"),
       tr("El tanto por ciento del dinero de bolsillo que pierde quien cae ante otro jugador."), ENTERO, 10, 0, 100),
    _o("botin_max", "combate", tr("Botín máximo"),
       tr("Lo más que se puede perder al caer ante otro jugador, en euros."), ENTERO, 5000, 0, 100000000),
    _o("atraco", "combate", tr("Atraco a otro jugador, en tanto por ciento"),
       tr("El tanto por ciento del dinero de bolsillo que se lleva quien atraca a otro jugador."), ENTERO, 15, 0, 100),
    _o("atraco_max", "combate", tr("Atraco máximo"),
       tr("Lo más que se puede quitar en un atraco a otro jugador, en euros."), ENTERO, 1000, 0, 100000000),
    _o("robo_segundos", "combate", tr("Segundos para atracar un negocio"),
       tr("Los segundos que hay que aguantar en la puerta para vaciar la caja del negocio de otro jugador. Al dueño le salta el aviso."),
       ENTERO, 20, 1, 600),
    _o("recompensa", "combate", tr("Recompensa por tumbar a un inocente"),
       tr("Lo que sube, en euros, la recompensa por la cabeza de quien tumba a quien no se defendía."), ENTERO, 500, 0, 100000000),
    # -------------------------------------------------------------------- mundo
    _o("trafico", "mundo", tr("Tráfico común"),
       tr("Con si, los coches que circulan los lleva el servidor y son los mismos para todos. Con no, cada jugador ve su propio tráfico."),
       SINO, "si"),
    _o("trafico_max", "mundo", tr("Coches por zona con jugadores"),
       tr("Cuántos coches lleva el servidor, como mucho, por cada zona de una localidad en la que hay jugadores. Para unos amigos "
       "que van juntos es el total de coches de la localidad."), ENTERO, 8, 0, 200),
    _o("trafico_total", "mundo", tr("Coches por localidad, como mucho"),
       tr("El tope de coches en una misma localidad cuando hay jugadores repartidos por muchas zonas. Con 0 no hay tope."),
       ENTERO, 60, 0, 5000),
    _o("patrullas", "mundo", tr("Coches patrulla por localidad"),
       tr("Coches patrulla del servidor que rondan por cada localidad con jugadores. Con 0, ninguno."), ENTERO, 1, 0, 50),
    _o("policia", "mundo", tr("Policía común"),
       tr("Con si, la búsqueda, la persecución y la detención las lleva el servidor, y las ve y las oye todo el que esté cerca. "
       "Con no, las lleva el juego de cada jugador."), SINO, "si"),
    _o("peatones", "mundo", tr("Gente de la calle común"),
       tr("Con si, los peatones los lleva el servidor y son los mismos para todos."), SINO, "si"),
    _o("peatones_max", "mundo", tr("Peatones por zona con jugadores"),
       tr("Cuántos peatones lleva el servidor, como mucho, por cada zona de una localidad en la que hay jugadores."), ENTERO, 10, 0, 200),
    _o("peatones_total", "mundo", tr("Peatones por localidad, como mucho"),
       tr("El tope de peatones en una misma localidad cuando hay jugadores repartidos por muchas zonas. Con 0 no hay tope."),
       ENTERO, 80, 0, 5000),
    _o("personajes", "mundo", tr("Personajes que lleva el servidor"),
       tr("Paseantes, rateros, pistoleros, ladrones de coches y atracadores que lleva el servidor y son los mismos para todos. "
       "Salen solo donde hay jugadores. Con 0, ninguno."), ENTERO, 6, 0, 200),
    _o("radio_detalle", "mundo", tr("Metros a los que se sigue a los demás al detalle"),
       tr("A cada jugador se le cuenta diez veces por segundo dónde están los que tiene a menos de esta distancia, y una vez por "
       "segundo por dónde andan los demás de su localidad. Es lo que más red y procesador ahorra en servidores con mucha gente. "
       "Con 0, a todos al detalle y siempre, que solo conviene con poca gente."),
       ENTERO, 150, 0, 100000),
    # ----------------------------------------------------------------- economía
    _o("economia", "economia", tr("El servidor lleva la cuenta del dinero"),
       tr("Con si, el servidor lleva la cuenta del dinero de cada jugador y no da por bueno lo que no puede justificar."), SINO, "si"),
    _o("ganancia_hora", "economia", tr("Ganancia máxima por hora"),
       tr("Lo más que se puede ganar en una hora de reloj con trabajos, ventas, juego y botín de la calle, en euros. Lo que da el "
       "propio servidor no cuenta."), ENTERO, 30000, 0, 1000000000),
    _o("ganancia_acumula", "economia", tr("Horas de ganancia que se pueden acumular"),
       tr("La ganancia por hora que un jugador no usa no se pierde: se le guarda hasta este número de horas, también mientras está "
       "fuera, para que una buena racha quepa entera. Con 1, nunca tiene más margen que el de una hora."), ENTERO, 3, 1, 48),
    _o("encargos_hora", "economia", tr("Encargos repetibles reconocidos por hora, de cada tipo"),
       tr("Los contratos, los combates del gimnasio, los atracos y los encargos de coches que se cumplen de verdad no gastan la "
       "ganancia por hora: el servidor los da por buenos, hasta este número por hora de cada tipo. Con 0 no reconoce ninguno "
       "y todos cuentan contra la ganancia por hora."), ENTERO, 6, 0, 1000),
    _o("encargo_max", "economia", tr("Paga máxima reconocida por un encargo repetible"),
       tr("Lo más que se da por bueno de la paga de un solo encargo repetible, en euros. Lo que pase de ahí cuenta contra la "
       "ganancia por hora."), ENTERO, 15000, 0, 1000000000),
    _o("saldo_inicial", "economia", tr("Dinero inicial máximo"),
       tr("Lo más con que puede empezar un personaje nuevo, en euros."), ENTERO, 5000, 0, 1000000000),
    _o("venta_mercado", "negocios", tr("Venta al mercado, en tanto por ciento"),
       tr("El tanto por ciento del precio que recupera quien vende su casa o su negocio al mercado."), ENTERO, 70, 0, 100),
    _o("propiedad_dias", "negocios", tr("Días sin entrar para perder las propiedades"),
       tr("Días de verdad sin entrar tras los que las propiedades de un jugador vuelven al mercado. Se le guarda su parte."),
       ENTERO, 30, 1, 3650),
    _o("negocios_max", "negocios", tr("Negocios por jugador"),
       tr("Cuántos negocios puede tener a la vez un mismo jugador, para que nadie se quede con todos. Con 0 no hay tope. "
       "Si alguien tiene más de los que permite el tope, a medianoche vuelven al mercado los últimos que compró, y se le "
       "devuelve lo que pagó por ellos."), ENTERO, 3, 0, 1000),
    _o("compra_forzosa", "negocios", tr("Comprar a la fuerza un negocio ajeno, en tanto por ciento de su precio"),
       tr("Cualquier jugador puede quedarse con el negocio de otro pagándole este tanto por ciento de su precio, aunque no lo "
       "venda. Lo cobra su dueño. No vale con los negocios de tu banda ni de una banda aliada. Con 0 no se puede."), ENTERO, 200, 0, 10000),
    _o("forzosa_dias", "negocios", tr("Días de protección de un negocio recién comprado"),
       tr("Durante estos días de verdad después de comprarlo, nadie puede quedarse a la fuerza con ese negocio."),
       ENTERO, 3, 0, 365),
    _o("vehiculos_horas", "economia", tr("Horas que dura un vehículo en la calle"),
       tr("Horas de verdad que un vehículo dejado en la calle sigue ahí."), ENTERO, 12, 1, 8760),
    _o("vehiculos_por_jugador", "economia", tr("Vehículos aparcados por jugador"),
       tr("Cuántos vehículos puede tener aparcados en la calle cada jugador. Al dejar uno más, desaparece el más antiguo."),
       ENTERO, 3, 1, 100),
    # ------------------------------------------------------------------- bandas
    _o("precio_banda", "bandas", tr("Precio de fundar una banda"), tr("En euros."), ENTERO, 2000, 0, 1000000000),
    _o("precio_barrio", "bandas", tr("Precio de reclamar un barrio"), tr("En euros, de la caja de la banda."), ENTERO, 3000, 0, 1000000000),
    _o("renta_barrio", "bandas", tr("Renta diaria de cada barrio"),
       tr("Lo que deja cada barrio en la caja de la banda a medianoche, en euros."), ENTERO, 300, 0, 1000000000),
    _o("precio_guerra", "bandas", tr("Precio de declarar una guerra"), tr("En euros, de la caja de la banda."), ENTERO, 1000, 0, 1000000000),
    _o("guerra_espera", "bandas", tr("Minutos hasta que empieza una guerra"),
       tr("Minutos de verdad entre declarar una guerra y que empiece."), ENTERO, 20, 1, 10080),
    _o("guerra_dura", "bandas", tr("Minutos que dura una guerra"), tr("Minutos de verdad."), ENTERO, 10, 1, 1440),
    # ---------------------------------------------------------------------- rol
    _o("rol", "rol", tr("Canales de rol"),
       tr("Con si, los jugadores tienen un canal para hablar en personaje, que solo oye quien está cerca, otro para hablar fuera de "
       "personaje, que oye todo el servidor, una orden para describir lo que hace su personaje y una frase de ficha que los demás "
       "pueden leer. Con no, solo queda el chat de siempre."), SINO, "si"),
    _o("rol_metros", "rol", tr("Metros a los que llega lo dicho en personaje"),
       tr("A qué distancia se oye lo que un jugador dice en personaje y las acciones que describe. Lo dicho fuera de personaje "
       "llega siempre a todo el servidor."), ENTERO, 30, 5, 2000),
    _o("radio_coches", "rol", tr("Radio de los coches de otros jugadores"),
       tr("Con si, quien está cerca del vehículo de otro jugador oye, floja, la emisora del juego que lleva puesta. Solo se cuenta "
       "qué emisora del juego es: nunca viaja música ni nada personal. Con no, no se oye la radio de nadie."), SINO, "si"),
    # --------------------------------------------------------------------- vida
    _o("nominas", "vida", tr("Nóminas de los contratos fijos"),
       tr("Con si, quien firma un contrato fijo en la oficina de empleo cobra su nómina al acabar cada periodo. La paga el servidor: "
       "él cuenta los turnos y pone la cifra, que sale de los datos del juego y no gasta la ganancia por hora. Con no, en este "
       "servidor no hay contratos fijos. Hace falta que el mundo del servidor sea el de la versión 1.7.1 o posterior."), SINO, "si"),
    _o("nomina_max", "vida", tr("Paga máxima por nómina"),
       tr("Lo más que paga el servidor por la nómina de un periodo, en euros, diga lo que diga el mundo del juego o un mod."),
       ENTERO, 1500, 0, 1000000000),
    _o("nomina_turnos_dia", "vida", tr("Turnos de contrato que cuentan cada día"),
       tr("Cuántos turnos de un contrato fijo cuenta el servidor a un jugador en un mismo día del juego."), ENTERO, 3, 1, 50),
    _o("trato_prestigio", "vida", tr("Rebajas por prestigio en las tiendas"),
       tr("Con si, a quien tiene buen nombre entre los vecinos las tiendas le rebajan un poco, y a quien lo tiene muy malo le "
       "recargan, como al jugar sin conexión con el nivel suave. Solo lo nota quien juega con la versión 1.7.1 o posterior. "
       "Con no, todos pagan lo mismo."), SINO, "si"),
)

POR_CLAVE = {o.clave: o for o in OPCIONES}
assert len(POR_CLAVE) == len(OPCIONES), "hay una opción repetida"


def valores_de_serie():
    return {o.clave: o.defecto for o in OPCIONES}


def de_seccion(seccion):
    return [o for o in OPCIONES if o.seccion == seccion]


def _version_valida(t):
    partes = t.split(".")
    return 1 <= len(partes) <= 4 and all(p.isdigit() and len(p) <= 5 for p in partes)


def validar_valor(clave, valor):
    """Comprueba un valor. Devuelve (valor ya en su forma, None) o (None, por qué no vale)."""
    o = POR_CLAVE.get(clave)
    if o is None:
        return None, tr("no existe ninguna opción con ese nombre")
    if o.tipo == ENTERO:
        try:
            n = int(str(valor).strip()) if not isinstance(valor, bool) else int(valor)
        except (TypeError, ValueError):
            return None, tr("tiene que ser un número entero entre %d y %d") % (o.minimo, o.maximo)
        if not o.minimo <= n <= o.maximo:
            return None, tr("tiene que estar entre %d y %d") % (o.minimo, o.maximo)
        return n, None
    if isinstance(valor, bool):
        valor = "si" if valor else "no"
    texto = str(valor if valor is not None else "").strip()
    if o.tipo == SINO:
        bajo = texto.lower()
        if bajo in _VERDADERO:
            return "si", None
        if bajo in _FALSO:
            return "no", None
        return None, tr("tiene que ser si o no")
    if o.tipo == ELECCION:
        bajo = texto.lower().replace("ó", "o").replace("í", "i")
        if bajo in o.permitidos():
            return bajo, None
        return None, tr("tiene que ser uno de estos valores: ") + ", ".join(o.permitidos())
    if "\n" in texto or "\r" in texto:
        return None, tr("no puede tener saltos de línea")
    if len(texto) > o.largo:
        return None, tr("no puede tener más de %d letras") % o.largo
    if clave == "nombre" and len(texto) < 2:
        return None, tr("tiene que tener al menos dos letras")
    if clave == "datos" and not texto:
        return None, tr("no puede quedar vacía")
    if clave == "version_minima" and texto and not _version_valida(texto):
        return None, tr("tiene que ser un número de versión, como 1.7.0, o quedar vacía")
    return texto, None


def validar(cfg, completar=True):
    """Comprueba un juego de opciones. Devuelve (opciones ya en su forma, lista de problemas).

    Lo que no vale se sustituye por su valor de serie y se cuenta en la lista. Lo que no se conoce se deja fuera."""
    limpio = valores_de_serie() if completar else {}
    problemas = []
    for clave, valor in (cfg or {}).items():
        o = POR_CLAVE.get(clave)
        if o is None:
            problemas.append(tr("%s: no existe ninguna opción con ese nombre; no se le hace caso.") % clave)
            continue
        v, error = validar_valor(clave, valor)
        if error:
            problemas.append(tr("%s (%s): %s. Se usa el valor de serie, %s.") % (o.etiqueta, clave, error, o.defecto if o.defecto != "" else tr("vacío")))
            limpio[clave] = o.defecto
        else:
            limpio[clave] = v
    final = dict(valores_de_serie(), **limpio)
    if final.get("entrada") == "clave" and not final.get("clave"):
        problemas.append(tr("La entrada es con clave pero la contraseña de entrada está vacía: no podrá crear personaje nadie nuevo."))
    if final.get("cifrado") == "si" and bool(final.get("llave")) and not final.get("certificado"):
        problemas.append(tr("Has puesto la llave de un certificado pero no el certificado."))
    return limpio, problemas


def leer(ruta):
    """Lee un servidor.conf. Devuelve (opciones, avisos). Si el archivo no existe, las de serie y ningún aviso.

    Una opción por línea: nombre = valor. Las líneas que empiezan por almohadilla son comentarios."""
    crudo, avisos = {}, []
    if ruta and os.path.exists(ruta):
        with open(ruta, "rb") as f:
            bruto = f.read()
        try:
            texto = bruto.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Guardado con un editor que no usa UTF-8 (el ANSI de Windows o Latin-1): se lee igual en vez de no arrancar.
            try:
                texto = bruto.decode("cp1252")
            except UnicodeDecodeError:
                texto = bruto.decode("latin-1")
            avisos.append(tr("El archivo %s no está guardado en UTF-8; se ha leído igual, pero conviene guardarlo en UTF-8 "
                          "(al guardar la configuración desde el panel ya queda bien).") % os.path.basename(ruta))
        for n, linea in enumerate(texto.splitlines(), 1):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            if "=" not in linea:
                avisos.append(tr("Línea %d: no la entiendo, le falta el signo igual. No se le hace caso.") % n)
                continue
            k, v = linea.split("=", 1)
            k = k.strip().lower()
            if k not in POR_CLAVE:
                avisos.append(tr("Línea %d: no existe la opción %s. No se le hace caso; puede ser de otra versión del servidor.") % (n, k))
                continue
            crudo[k] = v.strip()
    limpio, problemas = validar(crudo)
    return limpio, avisos + problemas


def _comentario(texto, ancho=110):
    return "\n".join("# " + l for l in textwrap.wrap(texto, ancho - 2)) if texto else ""


def texto_conf(cfg=None):
    """El texto de un servidor.conf completo y comentado, con estos valores o con los de serie."""
    valores = dict(valores_de_serie(), **(cfg or {}))
    out = ["# " + tr("Servidor en línea de Puerto Bravo: Ley del Asfalto"),
           "# " + tr("Una opción por línea: nombre = valor. Las líneas que empiezan por almohadilla no cuentan."),
           "# " + tr("Este archivo se puede cambiar con un editor de texto o desde el panel del servidor, en Configuración."),
           "# " + tr("Las opciones marcadas con «necesita reiniciar» solo se aplican al parar y volver a arrancar el servidor."), ""]
    for ident, titulo, que in SECCIONES:
        out += ["# " + "=" * 76, "# " + titulo.upper(), _comentario(que), "# " + "=" * 76, ""]
        for o in de_seccion(ident):
            out.append(_comentario("%s. %s" % (o.etiqueta, o.ayuda)))
            if o.tipo == ELECCION:
                out += ["\n".join(textwrap.wrap("%s: %s." % (v, d), 108, initial_indent="#   ", subsequent_indent="#     ")) for v, d in o.valores]
            else:
                out.append(_comentario(o.descripcion_valores()))
            serie = tr("De serie: %s.") % (o.defecto if o.defecto != "" else tr("vacío"))
            out.append("# " + serie + (tr(" Necesita reiniciar.") if o.reinicio else ""))
            out += [("%s = %s" % (o.clave, valores.get(o.clave, o.defecto))).rstrip(), ""]
    return "\n".join(out)


def guardar(ruta, cfg):
    """Escribe servidor.conf, comentado, sin dejarlo a medias si algo falla. Devuelve los problemas que tenía lo pedido."""
    limpio, problemas = validar(cfg)
    carpeta = os.path.dirname(os.path.abspath(ruta))
    os.makedirs(carpeta, exist_ok=True)
    temporal = ruta + ".nuevo"
    with open(temporal, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto_conf(limpio))
    os.replace(temporal, ruta)
    return problemas


def cambios(antes, despues):
    """Las opciones que cambian entre dos juegos de valores: (las que se aplican al momento, las que piden reiniciar)."""
    al_momento, con_reinicio = [], []
    for o in OPCIONES:
        if str(antes.get(o.clave, o.defecto)) != str(despues.get(o.clave, o.defecto)):
            (con_reinicio if o.reinicio else al_momento).append(o.clave)
    return al_momento, con_reinicio


def html_opciones(nivel=3):
    """El apartado de opciones de la guía, en HTML limpio: un encabezado por grupo y otro por opción."""
    e = html.escape
    out = []
    for ident, titulo, que in SECCIONES:
        out.append("<h%d>%s</h%d>" % (nivel, e(titulo), nivel))
        out.append("<p>%s</p>" % e(que))
        for o in de_seccion(ident):
            out.append("<h%d>%s: <code>%s</code></h%d>" % (nivel + 1, e(o.etiqueta), e(o.clave), nivel + 1))
            out.append("<p>%s</p>" % e(o.ayuda))
            out.append("<ul>")
            if o.tipo == ELECCION:
                out.append("<li>%s<ul>" % e(tr("Valores:")))
                out += ["<li><code>%s</code>: %s.</li>" % (e(v), e(d)) for v, d in o.valores]
                out.append("</ul></li>")
            else:
                out.append("<li>%s</li>" % e(o.descripcion_valores()))
            out.append("<li>%s</li>" % (e(tr("De serie: %s.")) % (("<code>%s</code>" % e(str(o.defecto))) if o.defecto != "" else e(tr("vacío")))))
            out.append("<li>%s</li>" % (tr("Necesita reiniciar el servidor.") if o.reinicio else tr("Se aplica sin reiniciar el servidor.")))
            out.append("</ul>")
    return "\n".join(out)
