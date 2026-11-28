# Puerto Bravo: Ley del Asfalto

**Idioma de este documento:** Español · [English](README_en.md) · [Tiếng Việt](README_vi.md) · [Português do Brasil](README_pt.md)

> *This README is also available in English: [read it in English](README_en.md).*

Audiojuego de mundo abierto, en español, en inglés y en vietnamita, y totalmente accesible. Se juega solo con el oído: con teclado o con mando de Xbox o de PlayStation, y con lector de pantalla (NVDA, JAWS o la voz de Windows). No hace falta ver la pantalla para nada.

Es un juego original. Su ciudad, su historia, sus personajes y su música son propios.

Este documento tiene cuatro partes:

1. [Para quien quiere jugar](#1-para-quien-quiere-jugar): qué es el juego y qué te vas a encontrar.
2. [Para desarrolladores](#2-para-desarrolladores): preparar el entorno, probar, compilar y publicar.
3. [Crear mods](#3-crear-mods): ampliar el juego con contenido propio.
4. [Packs de sonidos y de música](#4-packs-de-sonidos-y-de-música): cambiar cómo suena.

---

## Una nota sobre los sonidos

Quiero ser sincero con quien llegue hasta aquí: como desarrollador, el sonido no es lo mío. Por falta de tiempo y de conocimientos, los sonidos del juego son, en su mayoría, generados por el propio programa o recogidos de páginas web de grabaciones libres de derechos. Sé que no están a la altura, y que en un audiojuego el sonido lo es casi todo: con sonidos buenos, elegidos por gente que entiende de esto y que conoce el juego, Puerto Bravo ganaría muchísimo.

Por eso estoy abierto a cualquier colaboración con packs de sonidos, completos o de unos pocos sonidos. Si te animas:

- La guía `data\docs\cambiar_sonidos_es.html` (también en inglés, `cambiar_sonidos_en.html`) dice qué es cada sonido, qué significa oírlo, cuánto dura el original y cómo se arma un pack. El apartado [Packs de sonidos y de música](#4-packs-de-sonidos-y-de-música) lo resume.
- Las grabaciones tienen que poder repartirse con el juego: propias o con una licencia libre (CC0 o parecida), indicando de dónde sale cada una.
- Para hacérmelo llegar, abre una [incidencia en GitHub](https://github.com/hxebolax/PuertoBravo/issues) con un enlace de descarga al pack (o el ZIP adjunto, si cabe), o escríbeme por Mastodon a [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). Si sabes usar Git, también vale una petición de cambios (pull request) con el pack en su carpeta de `data\sonidos`.

Cualquier ayuda, por pequeña que sea, será muy bien recibida. Y gracias de antemano.

## Este documento en otros idiomas

Cada idioma tiene su propio archivo junto a este, con el código de dos letras del idioma al final del nombre, igual que las guías del juego: `README_en.md` es el inglés, y un `README_it.md` sería el italiano. Si traduces el README a otro idioma, añade el enlace a la línea de idiomas del principio de todos los README que haya.

---

## 1. Para quien quiere jugar

### La historia

Eliges personaje, o te creas el tuyo con su nombre, sus habilidades y su ventaja de salida, y decides si te hablan en masculino o en femenino. Con el primero te llamas Dani Roca y acabas de salir de la cárcel tras cumplir tres años por un robo que no cometiste. Vuelves a tu ciudad, Puerto Bravo, que ahora controla el empresario Octavio Belmonte. A partir de ahí, haz lo que quieras: sigue la historia, gánate la vida honradamente, hazte un nombre en la calle o dedícate a pescar. El juego no te obliga a nada.

### Cómo se juega sin ver

Todo lo que ocurre tiene su sonido, colocado a tu alrededor: lo que suena a la derecha está a la derecha, y lo que suena apagado está detrás. Por eso hacen falta auriculares. Además tienes muchas ayudas, todas opcionales:

- Una tecla que dice dónde estás: calle, entre qué avenidas, barrio y hacia dónde miras.
- Un escáner direccional que hace de bastón: qué hay delante, detrás y a los lados, y a cuántos metros está la pared.
- Un radar que recorre lo que hay cerca, con distancia y dirección, haciendo sonar cada cosa desde su sitio.
- GPS hablado, con una baliza sonora que marca el camino, hasta cualquier lugar de cualquier localidad.
- Un explorador de mapa para aprenderte las calles sin mover al personaje.
- Caminar solo y piloto del GPS: el personaje o el coche siguen la ruta mientras tú escuchas.
- Conducción asistida: el coche sigue su carril; tú decides la velocidad y dónde girar.
- Semáforos acústicos, pasos que suenan distinto en cada suelo y un sonido propio para cada tipo de lugar.
- Dos asistencias para explorar sin presión: no recibir daño y jugar sin policía.

### Qué hay en el mundo

- Nueve mapas de serie: las ciudades de Puerto Bravo, San Lucero y Monteferro; los pueblos de Villaseca, Cala Brava y Fuentefría; Isla Tortuga, la Plataforma Neptuno y el Mar de Poniente, navegable. Con los mods incluidos se suman tres pueblos y una isla más.
- Más de 300 lugares de serie: casas, comercios, bancos, talleres, casinos, gimnasios, cines, hospitales, embarcaderos, helipuertos, paradas de tranvía, estaciones de tren, aeropuertos y monumentos, cada uno con su sonido y su descripción. Casi todos los locales y las casas se recorren por dentro, sala por sala.
- 75 misiones de serie entre la historia principal, las secundarias y cinco tutoriales jugables, y encargos que se repiten sin fin. Los mods añaden casi setenta. Hay misiones que se juegan de oído (seguir a alguien por sus pasos, vigilar, entrar sin hacer ruido, carreras con rivales) y decisiones que cambian lo que viene después: cuatro abren ramas distintas, con diez finales.
- 39 vehículos: coches, motos, bicicleta, camiones, vehículos de emergencias, barcos, un helicóptero y una avioneta. 22 armas, con silenciador y cargador ampliado.
- Transporte público: tranvía con paradas en todos los barrios de las ciudades y vías que se cruzan a pie, tren entre localidades, autobús, taxi y aviones de pasajeros, todos con trayecto.
- El mar se navega, y también se nada y se bucea.
- Policía con cinco niveles de búsqueda, día y noche, lluvia, tráfico con semáforos y peatones.

### Qué puedes hacer

- Vida honrada: oficina de empleo, oficios con ascensos (taxista, conductor de ambulancia y de autobús, bombero, gruista, mensajero, transportista, heladero, pescador), cursos, voluntariado y negocios propios.
- Vida delictiva: la historia, contratos, encargos de coches, atracos y guerras de territorio.
- Ocio: carreras y regatas, casino, bingo, lotería, siete y media, dominó, los chinos, boxeo, galería de tiro, pesca, búsqueda de tesoros, cine, recreativos y bolsa.
- Casas con garaje, un perro que te acompaña y busca objetos, guardaespaldas, banda propia, barrios que hay que defender, mejoras de vehículos en el taller, logros y habilidades que suben con la práctica.
- Hablar con cualquier persona de la calle: cada una tiene su nombre, su oficio y su carácter. Puedes preguntar, invitar a un café, hacer amigos o escribir lo que quieras decirle. Un modo opcional hace que contesten interpretadas por una inteligencia artificial: un modelo local gratuito y sin internet, Google AI Studio, OpenAI, Anthropic u otro servicio compatible. El juego elige solo el modelo más barato.
- Voces en las escenas: cada personaje de la historia y de los mods incluidos tiene su propia voz, generada por ordenador. Te llaman por el nombre del personaje con el que juegas y te hablan en masculino o en femenino; con un personaje creado por ti, las frases que dicen tu nombre se generan en tu equipo. Cualquiera puede poner sus propias grabaciones. Se quitan en las opciones.
- Dos motores de sonido: el clásico y uno envolvente, binaural, con eco distinto en cada sitio.
- Sin inteligencia artificial, una base de más de mil cien frases en casi setenta temas (`juego/respuestas.py`) contesta a lo que escribas, según el carácter de cada persona.
- Una ciudad que no se repite: cada día viene distinto (rebajas, mercado, fiesta, huelga, operación salida) y cambian los precios, la gente y el tráfico. Ninguna partida es igual a otra.
- Realismo a tu medida, todo opcional: hambre, sed, sueño e higiene; combustible con gasolineras; averías, pinchazos y revisiones; y normas de tráfico con multas y carné por puntos.
- Jugar en un servidor: un mundo que sigue vivo con jugadores de verdad, bandas, territorios, casas y negocios, y con el tráfico, la gente y la policía iguales para todos. Cualquiera puede montar el suyo: el servidor viene con el juego, con un panel accesible para llevarlo y una guía paso a paso.
- La radio se queda en pausa al bajarte y sigue donde quedó; con un reproductor con auriculares la oyes también a pie, y en los locales suena de fondo.
- Jugar con amigos, sin servidores de nadie: tu propio juego abre la partida, con o sin contraseña, y les das una dirección. Os oís, os encontráis con el radar y el GPS, os escribís, vais en el mismo coche, hacéis carreras con apuesta y repartos en equipo.
- Siete emisoras de radio con música original, una de noticias que comenta lo que haces y otra con tu propia música. Música de ambiente que cambia con la situación.
- Un modo opcional para mayores de 18 años, desactivado de serie: relaciones, vida nocturna, sustancias y sus consecuencias, contado sin escenas explícitas.

### Requisitos y arranque

- Windows 10 u 11.
- Auriculares estéreo.
- Un lector de pantalla abierto, como NVDA o JAWS. Si no hay ninguno, el juego habla con la voz de Windows.

Descarga la última versión, descomprime la carpeta donde quieras y ejecuta `PuertoBravo.exe`. No instala nada: es portable. Dentro del juego, `F1` dice las teclas en cualquier momento, y el menú principal abre el manual completo, que está en `data\docs\manual_es.html` (y en inglés, `manual_en.html`) y se navega por encabezados. El juego va en el idioma de Windows, en español, en inglés, en vietnamita, en portugués de Brasil, en ruso o en polaco, y se puede elegir en Opciones, Idioma. Las novedades de cada versión se escriben en español y en inglés: con el juego en español se leen en español, y con cualquier otro idioma, en inglés.

Si algo falla, el juego deja un registro de cada sesión en `data\logs`, sin datos personales: comprimes la carpeta de la sesión y la adjuntas a una [incidencia](https://github.com/hxebolax/PuertoBravo/issues), o la envías por Mastodon a [@HXeBoLaX](https://comunidad.nvda.es/@HXeBoLaX). El manual explica cómo.

El juego se actualiza desde sus propias opciones. Puedes elegir de dónde: el servidor del juego, GitHub, los dos o una dirección tuya. Tus partidas, tus opciones, tu música y tus mods no se tocan.

---

## 2. Para desarrolladores

### Requisitos

- Windows 10 u 11.
- Python 3.13 o superior. Se desarrolla con Python 3.15.

### Primeros pasos

Todo se hace con los `.bat` de la raíz:

```bat
entorno.bat    :: crea el entorno virtual .venv e instala las dependencias
jugar.bat      :: abre el juego desde el código fuente
editor.bat     :: abre el editor de mods
probar.bat     :: ejecuta las pruebas automáticas
compilar.bat   :: genera dist\PuertoBravo, portable y listo para repartir
publicar.bat   :: comprime, firma y publica la versión compilada
```

Dependencias (`requirements.txt`): pygame-ce, numpy, sounddevice, soundfile, accessible-output2, wxPython, cx_Freeze y pytest. El modo IA no necesita ningún paquete: habla con los servicios por HTTPS con la biblioteca estándar (`juego/ia.py`), pregunta a cada uno su lista de modelos y elige el de la gama barata.

El repositorio incluye el audio: los sonidos por defecto y los cuatro packs en `data/sonidos` (el pack Envolvente se monta con `herramientas/crear_pack_envolvente.py`), la música de la radio en `data/radio` y la de ambiente en `data/musica`. Si falta algún sonido por defecto, el juego lo vuelve a generar al arrancar.

### Estructura

- `juego/`: el código del juego. `app.py` es el bucle y la pila de pantallas; `partida.py` reúne la partida a partir de módulos por tema (conducción, combate, misiones, trabajos, vida honrada, conversación, juego en red, azar diario...); `sintesis.py` genera los sonidos por defecto; `audio.py` es el mezclador con sonido posicional.
- `editor/`: el editor de mods, con wxPython.
- `herramientas/`: generación de sonidos y guías, protección y comprobación de la compilación, montaje de packs, mods de serie y publicación.
- `pruebas/`: pruebas automáticas con pytest.
- `data/datos/`: mapas, lugares, misiones, armas, vehículos, personajes y la gente de la calle con sus enemigos, en JSON.
- `data/mods/`: los mods de serie, en JSON legible.
- `data/docs/`: la documentación que se reparte con el juego, pensada solo para quien juega.
- `desarrollo/`: documentación técnica que no se reparte, como el formato de los archivos de mods.

### El servidor en línea

El servidor (`servidor/`) solo usa la biblioteca de serie de Python y funciona sin el juego, en Windows, Linux, Mac, un NAS o Docker. No trae el contenido: los lugares, las armas, los vehículos y las misiones se los da el juego del primero que entra con cada versión, firmados por quien publica, y en un mismo servidor conviven versiones distintas. Sus opciones están descritas en un solo sitio, `servidor/opciones.py`, del que salen el archivo de ejemplo, la validación, el diálogo de configuración del panel y la guía. El panel (`panel_servidor/`, `servidor_panel.py`) es una ventana wxPython que reutiliza la accesibilidad del editor de mods. Se arranca en desarrollo con `servidor.bat` o `servidor_panel.bat`. La guía de quien lo monta es `data\docs\servidor.html`. `herramientas\prueba_servidor_real.py` arranca un servidor de verdad como proceso aparte y le conecta diez clientes por la red.

#### Protocolo: lo añadido en la 1.7.1

La versión del protocolo no cambia (`VERSION_RED = 2`). Todo lo nuevo es opcional: campos que se añaden a mensajes que ya existían y mensajes nuevos que un extremo anterior ignora. La regla es doble:

- El juego dice en su saludo lo que entiende: `hola.sabe`, una lista (`enlinea.SABE`: `rol`, `radio`, `pasajeros`, `mis_vehiculos`, `topes`, `encargos`). Un servidor anterior no la mira. El servidor nuevo guarda eso en `Jugador.sabe` y a quien no lo dice le habla como a un juego de la 1.7.0.
- El servidor dice lo que sabe hacer en `ok.funciones` (`nucleo.FUNCIONES`, con esas mismas seis palabras añadidas). El juego lo consulta con `Partida.sv_sabe(que)` antes de usar nada nuevo; con un servidor anterior, lo dice con una frase y no envía el mensaje.

Lo que viaja:

- **Pasajeros** (el copiloto atropellado). `estado.e.pj`: el identificador de sesión del jugador en cuyo vehículo vas. El servidor lo sabe además por los mensajes `act` con `que` igual a `sube` o `baja`, que ya mandaba la 1.7.0. `Servidor._va_con(o)` devuelve el conductor si sigue al volante, en la misma localidad y a menos de 45 metros; con eso `_m_atropello` no acepta el atropello, `_m_atraco` no deja atracarle «a pie» y `_m_ataque` y `_m_explosion` le dan la protección de la chapa. La ficha de posiciones lleva `pj` cuando procede. En el juego, quien conduce no avisa de atropello a quien lleva dentro (`sv["pasajeros"]`, que se mantiene con `act`, y `Remoto.pasajero_de`): eso vale también contra un servidor anterior.
- **Radio de los vehículos**. `estado.e.ra`: el identificador corto de la emisora, solo si es de las de serie (`Radio.comunes()`), suena y vas al volante. El servidor lo valida (texto de hasta 24 letras, números o guion bajo), lo guarda en `Jugador.radio` y lo pone en la ficha como `ra`. Nunca viaja audio, ni rutas, ni nada de «Mi música». El juego que la oye carga un trozo de su propia copia (`Radio.muestra`, en un hilo) y lo hace sonar en bucle desde el vehículo (`EnLinea._sv_radio_ajena`). Opción del juego `radio_coches`; del servidor, `radio_coches`.
- **Rol**. `chat.canal` admite además `ic` (en personaje), `yo` (acción) y `ooc` (fuera de personaje). `ic` y `yo` llegan a `rol_metros`; `ooc`, a todos. A quien no sabe de `rol` el servidor se lo manda por `cerca` o `todos` con unas palabras delante. Las órdenes `/yo`, `/me`, `/ep`, `/ic`, `/fp`, `/ooc` y `/ficha` las interpreta el servidor en cualquier mensaje de chat, antes que las de administración, así que valen desde un juego anterior. `rol_oido` (`canal`, `n`) le dice al que habla cuántos le han oído. `ficha` con `texto` pone la propia (se guarda en la columna `ficha` de `cuentas` y vuelve en `ok.ficha`); con `a`, pide la de otro, y la respuesta es `ficha` con `de`, `nombre` y `texto`.
- **Mis vehículos**. `veh_nombre` (`id`, `nombre`), `veh_traer` (`id`, `x`, `y`, `r`) y `veh_guardar` (`id`, `ref`), solo para un vehículo aparcado cuyo dueño es quien lo pide. La respuesta es `veh_mio` con `que` igual a `nombre`, `traer`, `garaje` o `no` (con `motivo`). A los demás les llegan los `veh_libre` y `veh_fuera` de siempre, así que un juego anterior lo ve bien. El garaje sigue siendo cosa del juego: el servidor devuelve la ficha y quita el vehículo de la calle; el juego la mete en `j.garajes`, cobra y guarda.
- **Topes de dinero**. `ok.servidor.economia`, el mensaje `saldo` y la respuesta a `economia` llevan `tope`, `acumula`, `horas`, `margen`, `por_minuto`, `encargos_hora` y `encargo_max`; `saldo` lleva además `ganado` y `aceptado`. El margen se guarda con la cuenta (columnas `margen` y `t_margen`) y se acumula hasta `ganancia_acumula` horas.
- **Encargos repetibles**. `mision_ok` con `encargo: 1` y `n` (la paga) para una misión que el mundo del servidor no conoce: el `id` es el tipo (`contrato`, `atraco_banco`, `atraco_local`, `asalto_proveedor`, `encargo_coche`, `conquista`, `defensa` o el identificador de un combate). El servidor reconoce hasta `encargos_hora` por hora y tipo, con el máximo que diga `mundo["encargos"]` (lo calcula `enlinea.encargos_para_servidor` con los datos del juego) o, si el mundo no lo trae, `nucleo.ENCARGOS_DE_SERIE`, y nunca más de `encargo_max`. La paga reconocida vale treinta segundos (`Jugador.fiado`).
- **La compra y el corte de conexión**. En el juego, `_sv_vigilar_gasto` manda un `guardar` a los dos segundos y medio de bajar el dinero (y no más de uno cada doce segundos si se sigue gastando). En el servidor, `Jugador.gasto_pend` suma lo que se le ve gastar por su cuenta desde el último `guardar`, y `total_guardado` es el dinero del personaje guardado; al salir (`_salida`), `_devolver_sin_guardar` devuelve al saldo el menor de los dos huecos. No cuentan ni lo que quita el servidor (`Jugador.descuento`) ni las casas ya pagadas.
- **Grupo de misión**. Los enemigos que se cuentan a los compañeros llevan además `deportivo`, `punteria` y `tono`.
- **Policía común**. La fila de cada agente lleva un sexto dato, su salud.
- **Mundo**. `mundo_servidor()` añade `encargos` y `gente.frases` (lo que dicen los personajes del servidor, por clase). No entran en la huella.

#### Versiones distintas en el mismo servidor (1.7.1)

Principio: dos personas con versiones distintas del juego tienen que poder jugar juntas, y a partir de ahí lo más igualadas posible. Solo se rechaza por versión con la opción `version_minima`. El protocolo sigue en la versión 2; el servidor añade `equivalencias` y `nominas` a `ok.funciones`. La parte del servidor que no depende del resto está en `servidor/compat.py`.

**Qué viaja del juego al servidor y qué no.** El servidor no tiene el juego: lo que sabe del mundo es el texto de `enlinea.mundo_servidor()`, que le da el juego de quien entra (`pide_mundo` y `mundo`, comprimido) o que trae de fábrica en `servidor/mundo.json`.

- Viaja: de cada localidad, sus lugares (identificador, tipo, nombre, coordenadas, precio, ingresos), sus barrios, sus calles y sus coches de tráfico; de cada arma, su tipo, daño, alcance, cadencia, precisión, radio y si es automática; de cada vehículo, su salud, velocidad, aceleración, freno y si vuela; de cada misión, su título, su paga y si se repite; los nombres y las frases de los personajes del servidor, la tabla de la policía, lo más que paga cada encargo repetible (`encargos`) y los contratos fijos con sus nóminas (`empleos`: periodo, prima y, por empleo, turnos y sueldo de cada puesto).
- No viaja: sonidos, textos de misiones, pasos y enemigos de las misiones, tiendas y precios, objetos, ropa, comida, trabajos, la vida honrada entera salvo las nóminas, las opciones de cada jugador, ni nada de su equipo. Todo eso lo pone el juego de cada uno.
- La huella (`enlinea.huella_datos`) solo cubre identificadores de localidades, lugares, barrios, vehículos y misiones, y las cifras de las armas. Lo demás que cuenta el mundo (`encargos`, `gente`, `policia`, `empleos`) no entra en ella: por eso, si el mundo guardado por el servidor (`mundo_actual.json`) y el que trae (`mundo.json`) tienen la misma huella, al arrancar vale el que trae.

**Quién pone el mundo** (`Servidor._admitir_mundo`). Se llama cuando la huella de quien entra no es la del servidor, si `comprobar_datos` está en `si` o el servidor no tiene mundo.

| Caso | Qué hace el servidor |
|---|---|
| Servidor vacío, mundo firmado | Lo adopta. |
| Servidor vacío, mundo sin firma | Con `mundo_distinto = admitir` y `actualizar_mundo` distinto de `no`, lo adopta marcado como `provisional`; lo sustituye el primero firmado que llegue, sea de la versión que sea, o el de un administrador con `actualizar_mundo = admin`. Si no, rechaza con un texto claro. |
| Mundo firmado de una versión más nueva | Lo adopta (`actualizar_mundo` en `firmado` o `admin`), lo anuncia y no echa a nadie. |
| Mundo conocido (`mundos_conocidos`, o `compat.CATALOGOS`, que son los de las versiones publicadas) | Entra sin pedirle nada. |
| Mundo firmado que no conocía, igual o más antiguo | Lo comprueba, lo recuerda y entra. |
| Mundo sin firma (mods) | Con `mundo_distinto = admitir`, de serie, entra: se le pide su mundo solo para saber qué conoce su juego en esa sesión (`Jugador.cat`), y nada de él se guarda. Con `rechazar`, o con `versiones = iguales`, no entra. |

**Equivalencias.** De cada mundo comprobado el servidor guarda un catálogo (`compat.catalogo_de`: identificadores de armas y de vehículos; `meta.catalogos`, y `compat.CATALOGOS` para las versiones publicadas). `Servidor._cat(j)` da el catálogo del juego de un jugador si su huella no es la del servidor. Con él:

- `Servidor._enviar` pasa por `_traducir` los mensajes de `TRADUCIBLES`: `tiro`, `herido` y `po_disparo` (el arma), `evento` con `d:<arma>`, `veh_ocupado`, `veh_libre`, `veh_ok` y `veh_mio` (el modelo), `ok` (los vehículos aparcados) y `grupo_msg` con los enemigos de una misión (su arma). Lo que ese juego no conoce se cambia por lo más parecido que sí conoce (`compat.arma_equivalente`: misma clase, y después cifras, nombre y si es automática; `compat.modelo_equivalente`: que vuele o no, y cifras y nombre). `_repartir_estados` hace lo mismo con el vehículo que conduce cada uno.
- El daño no se toca: `_m_ataque` y `_m_explosion` lo calculan con las cifras del mundo del servidor antes de traducir nada, y a los demás se les nombra el arma con la que ha contado el servidor, no la que diga el mensaje.
- `_m_dar` devuelve a quien la daba un arma o una munición que el otro no puede recibir.
- Si es el servidor el que no conoce algo (su mundo es anterior al del jugador), no hay equivalencia que valga: el arma cuenta como las manos, el vehículo como `utilitario` y la localidad queda fuera, con un aviso al jugador. Es igual para todos.
- Al entrar, `ok.mundo.distinto` (`faltan` y `sobran`, con nombres de armas y vehículos) y un `aviso` con el mismo contenido en una frase (`compat.texto_diferencias`).

**El personaje.** `cuentas.partida` guarda el JSON entero que manda el juego, con lo que el servidor no conozca (tope: `MAX_LINEA`, 600 KB; si no cabe, no se guarda y se avisa). `cuentas.partida_juego` es la versión más nueva del juego que ha guardado ese personaje.

- Al entrar con un juego que no conoce todo lo que lleva, `compat.adaptar_partida` le da una copia sin las armas ni los vehículos de garaje que no tiene (un juego de la 1.7.0 falla al cambiar de arma si lleva en la mano una que no conoce). La base de datos no se toca.
- Al guardar con un juego anterior a `partida_juego`, `compat.fundir_partida` repone lo que ese juego no sabe guardar: las claves de la raíz y de `jugador` que falten (el juego de la 1.7.0 descarta las que no conoce al cargar), las armas que no conoce y los vehículos de garaje que no conoce. Lo que sí conoce manda lo que él diga.

**Nóminas** (`_m_contrato`, `cuentas.contrato`). Mensaje `contrato` con `que`: `firmar` (`empleo`, `puesto` 0 o 1), `turno`, `cobrar` (`buena`, `mala`), `ascenso` y `dejar`. El servidor contesta `contrato` (`que`: `firmado`, `turno`, `puesto` o `no`, y `c` con `empleo`, `puesto`, `turnos`, `fin`, `periodo`, `tope`, `turnos_dia`) o `nomina` (`n`, `turnos`, `cupo`, `faltan`). El dinero de `nomina` se apunta como crédito justificado (`_enviar`), igual que `dinero`. Lo que decide el servidor: turnos por día (`nomina_turnos_dia`), el día de cobro (`fin`, en días del servidor), la cifra (el sueldo del puesto en `mundo["empleos"]`, en proporción a los turnos, más la prima si hay cupo y evaluación buena, con el tope `nomina_max`) y que solo se suba un puesto tras un periodo con el cupo cumplido. El juego (`honrado.py`: `_hon_sv_contrato`, `_hon_nomina`, `hon_sv_al_entrar`, `_svm_contrato`, `_svm_nomina`) vive el contrato como sin conexión y solo deja el dinero en manos del servidor. `ok.servidor.nominas` y `ok.servidor.trato_prestigio` dicen si ese servidor lleva nóminas y si las tiendas tratan según el prestigio; `Partida.sv_honrado(que)` lo consulta.

**Opciones nuevas del servidor**: `mundo_distinto` (`admitir`), `nominas` (`si`), `nomina_max` (1500), `nomina_turnos_dia` (3) y `trato_prestigio` (`si`).

**Al publicar una versión que cambie armas o vehículos**, apunta el catálogo de la versión que queda atrás en `compat.CATALOGOS`: `.venv\Scripts\python.exe herramientas\exportar_mundo_servidor.py --catalogo` escribe la entrada del mundo de ahora, lista para pegar. Así los servidores nuevos conocen esa versión sin tener que pedirle nada.

**Pruebas con la versión anterior de verdad**: `pruebas/test_171_versiones.py` saca el código publicado de la 1.7.0 con `git archive` a una carpeta temporal (`pruebas/banco_versiones.py`) y lo ejecuta en procesos aparte (`pruebas/agente_versiones.py`), nunca mezclado con el de ahora. Si no hay git o falta ese commit, esas pruebas se saltan diciendo por qué.

**Límites conocidos.** Un servidor de la 1.7.0 no traduce nada ni repone el personaje: quien entra en él con un juego anterior al mundo que tenga no oye las armas nuevas (su juego las ignora) y no ve aparcados los vehículos nuevos. Las localidades nuevas no tienen equivalente: quien no las tiene no ve a quien está en ellas. Los objetos, la ropa y la comida no están en el mundo del servidor, así que no se comprueba si quien los recibe los conoce (el juego de la 1.7.0 ya dice que no puede recibirlos). El tráfico del servidor usa los modelos de su mundo; un juego anterior pone un utilitario donde no conoce el modelo.

#### Parada ordenada, aviso de actualización y reconexión (1.7.1)

Tampoco cambia la versión del protocolo. El juego añade `reconexion` a `hola.sabe` y el servidor a `ok.funciones`.

**El servidor.** `Servidor.detener(motivo, causa, aviso, vuelve, espera, codigo)` es la única manera de parar, y ahora hace las cosas en orden:

1. Si `causa` es `actualizacion` o `reinicio` y hay `aviso`, cuenta atrás: a cada juego que sabe `reconexion` le manda `parada` (`causa`, `en` segundos, `vuelve` segundos estimados); a los demás, un `aviso` normal con el mismo contenido en texto. Se repite al quedar 60, 30 y 10 segundos (`AVISOS_PARADA`). Quien entra durante la cuenta atrás lo recibe al entrar.
2. `cerrando = True` (ya no entra nadie: `rechazo` con `codigo: "reiniciando"`) y manda a todos `cerrado` con `motivo` (texto que entiende un juego anterior), `causa` (`apagado`, `actualizacion`, `reinicio`) y `vuelve`.
3. Espera el último `guardar` con `ya` de cada juego (`_guardan`), hasta `parada_espera` segundos y nunca menos de dos décimas. Un juego, nuevo o de la 1.7.0, responde a `cerrado` guardando y despidiéndose, así que no hace falta otro mensaje.
4. Saca a cada jugador por `_salida` (vehículo aparcado, `_devolver_sin_guardar`, `_guardar_saldo`), apunta en `meta.buscados` a quién buscaba la policía, guarda todo y cierra. Deja `causa_parada` y `codigo_salida` (75, `CODIGO_VUELVE`, si se paró para volver; 0 si no).

Cómo se pide desde fuera del proceso: el archivo `parar.txt` (`ARCHIVO_ORDEN`) en la carpeta de datos, que el propio servidor mira cada segundo en `_bucle_lento` (`_mirar_orden`, `orden_externa`). Su primera palabra es `parar`, `actualizar` o `reiniciar`, y detrás pueden ir los segundos de aviso. `python -m servidor --parar | --actualizar | --reiniciar` lo escribe y espera a que lo recojan. Las órdenes de consola y de chat `actualizar` y `reiniciar` hacen lo mismo (`parar_para_volver`). La señal de terminar (systemd, Docker) y el cierre de sesión o el apagado de Windows paran con `causa="reinicio"`, sin cuenta atrás y esperando tres segundos como mucho; Control+C y cerrar la ventana, con `apagado`. El panel no usa `__main__`: con el servidor en marcha el archivo lo ve el servidor, y con él parado lo mira la ventana (`Motor.orden_pendiente`); si `Motor.causa_parada` es `actualizacion` la ventana se cierra, y si es `reinicio` vuelve a arrancar.

Otros cambios del servidor: `rechazo` lleva `codigo` (`version` con `minima`, `lleno`, `reiniciando`); `veh_no` lleva `por` (`no_esta`, `ocupado`, `lejos`); quien vuelve mientras su sesión anterior sigue como «fantasma» de pelea la sustituye, hereda `golpeado` y `agredio` y entra sin protección de llegada.

**El juego.** `enlinea.conectar` devuelve el motivo como `Motivo`, una cadena con `codigo` y `minima`. `_svm_cerrado` (con `causa` distinta de `apagado`, o sin `causa`, que es un servidor anterior) y `_svm_desconectado` llaman a `sv_cortado`: manda un último `guardar` si aún hay línea, apunta lo que habrá que recomponer en `sv_espera` (grupo, pasajero, de cuándo es el último guardado), limpia lo que ponía el servidor (`_sv_limpiar_mundo`), invalida los identificadores de los demás jugadores y abre `reconexion.Espera`. `_svm_expulsado` no espera nunca. La partida sigue en memoria con `en_servidor = True` y `red = None`.

`reconexion.Espera` reintenta con las esperas de `ESPERAS` (3, 5, 8, 12 y 15 segundos), en un hilo, durante `cfg["reconectar_minutos"]`. Según `codigo_de(motivo)`: `red`, `reiniciando` y `lleno` siguen probando; `version` deja de probar y ofrece actualizar (deja `data/config/volver_servidor.json` con el nombre y la dirección, y tras `--tras-actualizar` el juego ofrece volver); `certificado` y cualquier otro rechazo salen al menú explicándolo. Al entrar llama a `sv_entrar(enlace, vuelta=True)`: no carga `ok.partida`, no corta el dinero con `ok.saldo` (lo juzga el servidor con `_cuadrar_saldo` al recibir la posición, como siempre), manda la posición y, a las cuatro décimas, un `guardar` con la partida viva. El vehículo en el que se iba se recupera con `veh_subir` de su número (`sv["reenganche"]`): si el servidor ya no lo tiene o lo tiene lejos, se da de alta de nuevo con `veh_tomar`; si lo lleva otro, el jugador se queda a pie. El grupo se rehace por nombres (`sv["regrupo"]`): quien lo llevaba reenvía `grupo_invitar` según entran los demás, y los demás responden solos a la invitación de ese nombre, durante 180 segundos.

Lo que no se recompone: ir de pasajero (te quedas a pie), un atraco a un negocio en marcha, las invitaciones pendientes y la cuenta por hora de encargos repetibles, que vive en la memoria del servidor.

**El actualizador.** Cada servidor en marcha del juego compilado deja una ficha en `servidor\en_marcha\<pid>.json` (`servidor/enmarcha.py`): tipo (`consola` o `panel`), ejecutable, argumentos, carpeta de trabajo, carpeta de datos, configuración, si el servidor está en marcha y la sesión de Windows. `actualizador.servidores_en_marcha()` las lee, borra las de procesos muertos y marca como `servicio` las de otra sesión. `menus_actualizar._instalar` pide confirmación, y `pedir_parada_servidores()` escribe `data\actualizacion\servidores_abiertos.json` y deja `actualizar` en el `parar.txt` de cada carpeta de datos. El `.bat` espera a que los programas se cierren (hasta tres minutos), instala y, tanto si va bien como si no, llama a `PuertoBravo.exe --relanzar-servidores <nota>` antes de abrir el juego: `relanzar_servidores()` arranca cada uno con sus argumentos y su carpeta (el panel con `--arrancar` si su servidor estaba en marcha), minimizado y sin robar el foco, y apunta en `actualizacion.log` una línea `SERVIDOR relanzado tipo=...` o `SERVIDOR sin_relanzar tipo=... motivo=...`. Solo arranca `PuertoBravoServidor.exe` y `PuertoBravoServidorPanel.exe` de la propia carpeta del juego. Las pruebas pueden cambiar la carpeta de fichas con la variable de entorno `PUERTOBRAVO_EN_MARCHA`.

Límites que se quedan: en un servidor los enemigos de las misiones llegan a pie aunque su tipo vaya en vehículo, y la policía común va siempre en coche patrulla; de la tabla de la policía toma el arma, la salud y cuántos agentes.

Todo el contenido y todos los precios del juego están en los JSON de `data\datos` (lo más nuevo, en `vida.json`), y el editor de mods tiene una sección para cada cosa.

### Gente, enemigos, policía y cajas

`data/datos/gente.json` y `juego/gente.py` llevan todo lo que antes eran listas escritas en el código: los nombres, apellidos, oficios y frases de la gente, los caracteres, las bandas, el catálogo de tipos de enemigo, la tabla de la policía por nivel de búsqueda y la caja de cada tipo de local. `gente.configurar(datos)` se llama al final de `mundo.cargar_datos()`; lo que falte en los datos vale lo de serie. Lo que usa el resto del código:

- `gente.lista(cual)`, `gente.nombres(genero)`, `gente.oficio_para(edad, genero, rng)`, `gente.caracter(id)`.
- `gente.enemigo(grupo)` resuelve un grupo de un paso «eliminar» (con `clase`, o con nombre, arma y salud como siempre) y `gente.vestir(persona, ficha)` se lo pone a una `Persona`. `gente.grupo(clase, n, **serie)` escribe un grupo que vale aunque el tipo no esté en los datos.
- `gente.agentes_nivel(nivel)` da el tipo de agente de una patrulla; `gente.banda(nombre)` y `gente.tipos_de_banda(nombre)`, lo de las bandas.
- `gente.caja_local(tipo)` y, en la partida, `caja_de_local(lugar)`: lo que hay hoy en la caja y quién la guarda.
- `Partida.llegar_en_vehiculo(modelo, personas)` hace llegar a un grupo en un vehículo, con la misma conducción que las patrullas (`ia == "enemigos"`), y `bajar_enemigos(v)` los baja.

Las mejoras del taller (`juego/sistemas.py`) también salen de los datos: cada una dice su `efecto`, de la lista `sistemas.EFECTOS`, sus niveles y cuánto da cada nivel.

### Mis vehículos y el chófer

`juego/misvehiculos.py` (mixin `MisVehiculos` de la partida, y los menús del móvil):

- Un vehículo del jugador lleva `v.mio = True` y `v.mio_n` (orden de antigüedad). `Partida.hacer_mio(v)` lo marca: lo llaman la compra, la primera mejora del taller, sacar del garaje, que te lo traigan y ponerle nombre. `_poblar` no retira los marcados.
- Los de la localidad actual son vehículos vivos; los de las demás esperan como datos en `Partida.mis_lejos` (`mis_al_cambiar_mapa`, `_reponer_mis_vehiculos`). En la partida guardada van en `mis_vehiculos`, con `n` y, el último usado, `ultimo`; el que llevas puesto, en `veh` con `mio`. El número de formato no cambia: una versión anterior ignora las claves nuevas, y una partida anterior carga sin ellas (`mis_cargar`).
- `ultimo_veh` y `veh_fuera` siguen siendo «el último que has usado», sea tuyo o no; si es tuyo, no se duplica en `veh_fuera`.
- El tope (`vehiculos_propios.tope_calle` en `vida.json`) lo aplica `_tope_mis_vehiculos`.
- En un servidor no se marca ni se guarda nada (`hacer_mio` devuelve `False`): los vehículos de la calle son del servidor. El servidor añade a su respuesta de entrada `mis_vehiculos` (los identificadores de los aparcados a nombre de la cuenta) y acepta `nombre` en `veh_dejar`; un juego o un servidor anterior ignora las dos cosas. Desde la lista se puede renombrar, traer y mandar al garaje un vehículo aparcado (`veh_nombre`, `veh_traer`, `veh_guardar`; ver el protocolo, en El servidor en línea). El juego lleva la cuenta en `sv["mios"]` y `sv_mis_vehiculos()`.
- Misiones: `mision_vehiculo(m)` y `mision_vehiculo_txt(m)` dicen qué pasa con el vehículo; con `vehiculo_libre`, el paso `robar` acepta el vehículo del jugador (`ms["veh_tuyo"]`) y `entregar` no se lo quita.
- Chófer: `Partida.chofer` es `None` o un diccionario con `estado` (`espera`, `viene`, `aqui`, `contigo`). El vehículo viene con `ia == "chofer"` (`_ia_chofer`); contigo dentro, `chofer_conduce()` hace que `piloto_puesto()` y `modo_asistido()` valgan aunque el jugador no tenga el piloto ni la conducción asistida, y `conducir` ignora los pedales. El vehículo de la banda lleva `tag == "banda"`; el de tu garaje, no lleva marca y es tuyo. No se guarda con la partida.

`mundo_servidor()` le cuenta además al servidor los nombres de sus personajes (`gente`) y las armas de sus agentes por nivel (`policia`). Son dos claves de más: un servidor anterior no las mira, y uno nuevo usa lo suyo si no vienen. La huella del mundo no depende de ellas, pero sí de las armas y los vehículos: al añadir unas u otros hay que regenerar `servidor/mundo.json` con `herramientas/exportar_mundo_servidor.py`.

### La calle: defensa propia, patrullas, rendición, helicóptero y guerra de barrios

- `juego/calle.py` (mixin `Calle` de la partida) reúne lo que pasa en la calle sin que el jugador lo busque. Los números y las frases salen de `vida.json`, sección `calle`; las opciones del jugador, de `config.py` (`defensa_propia`, `frases_reacciones`, `charla_peatones`, `soltar_municion`, `soltar_armas`, `patrullas_calle`, `ambulancias`, `helicoptero_policia`).
- Defensa propia: un enemigo que ataca sin haber sido tocado queda marcado (`p.agresor`, en `marcar_agresor`, que se llama desde `actualizar_personas` en el momento del ataque). Mientras haya un agresor vivo cerca, `_ruido_disparo` no apunta delito, y tumbarlo tampoco. `agente_auxilia` hace que un agente vaya a por él; `herir_por_otro` es la baja que no cuenta para el jugador. No vale para `tag` de misión ni de guerra.
- Voces por género: `calle.genero_de(p)` (la ficha si la hay; si no, el tono de voz) y `Calle.voz_persona`. `charla.ficha` da el género según ese mismo tono. `Calle.asustar` es el único sitio por el que un peatón pasa a huir.
- Las patrullas de ronda son vehículos con `ia == "policia"` y `ronda = True`; con cero estrellas los mueve `patrulla_sin_busqueda`, y con búsqueda, lo de siempre. Las que acuden a una pelea llevan `auxilio` (el momento en que desisten).
- La ambulancia es un vehículo con `ia == "ambulancia"` y `tag == "ambulancia"`; su estado está en `Partida.ambulancia`.
- Rendirse: `Calle.rendirse` pone `Partida.rendido`; `actualizar_personas` manda a los agentes a `agente_detiene`, y `detener(rendicion=True)` aplica la pena de `_pena_rendicion`.
- El helicóptero es un vehículo con `ia == "heli_policia"` y `volando = True`, que `actualizar_vehiculos` no mueve: lo lleva `Calle._helicoptero`. Todo lo que recorre vehículos para chocar, frenar o subir se salta los que llevan `volando`. `danar_vehiculo` lo desvía a `heli_danado`.
- `juego/guerra.py` (mixin `Guerra`) es el modo de guerra de barrios en la calle (`guerra_calle`, apagado de serie; sección `guerra_barrios`). `banda_guerra` da a cada barrio de ciudad una banda estable con la semilla de la partida; `miembro_de_barrio` decide quién sale a la calle en `_poblar`; el estado de la guerra en curso está en `Partida.guerra` y no se guarda.
- En un servidor: con policía común (`sv_policia_comun()`) no hay patrullas de ronda, ni helicóptero, ni rendición; en cualquier servidor no hay ambulancias, ni armas soltadas, ni guerra de barrios. No se ha tocado `servidor/`.
- Al reintentar una misión, `Misiones._rebobinar_jugador` devuelve al jugador a como estaba pero deja los garajes como están: los vehículos no vuelven atrás.
- Viajes: `Partida.conexion_hacia` busca primero un camino solo por carretera cuando se va al volante (antes ganaba el autobús si era más corto en saltos); `lugar_al_alcance` es el lugar que abre Intro (al volante, el destino del GPS o una salida antes que otro lugar más cercano) y `pista_de_llegada` la frase de qué hacer en una salida, estación o embarcadero.
- `mundo.Lugar.nombre` y `.desc` son propiedades: con `nombre_conquistado` o `desc_conquistado` en los datos, devuelven ese texto cuando `Partida.barrio_cambiado(barrio)` dice que el barrio ya no es de la banda de serie. La partida se apunta en `Lugar.cambiado` al crearse. `Mundo._separar` impide que dos lugares compartan punto.
- `juego/escolta.py` (mixin `Escolta`, opción `escolta_misiones`: no, moderado o fuerte; sección `escolta_misiones`): `Misiones._generar_enemigos` pide `escolta_ajuste`, reparte los enemigos de más con `escolta_grupos` y sube salud y puntería con `escolta_endurecer`.
- `juego/destinos.py` (mixin `Destinos`, opción `ayuda_persecucion`, sección `persecuciones`): la tecla O (`decir_objetivo`, con `objetivo_donde` para la posición), Mayúsculas O (`enfocar_objetivo`), Mayúsculas G y Control G (`quitar_gps_jugador`, `recuperar_gps`) y los números de las persecuciones (`pers`). El modelo de destinos está en `Partida.fijar_gps`: un solo destino, `self.gps`, y debajo el que espera (`anterior`); `quitar_gps_auto` quita lo de la misión o el trabajo sin tocar lo que haya marcado el jugador, y `_gps_cosa_acabada` cierra el desvío a un vehículo, una persona o un objeto.
- Reintentar una misión (`Misiones.fallar_mision`): `_rebobinar_jugador` no devuelve atrás garajes ni barcos; `MisVehiculos.preparar_traslado` y `llevarte_a` se llevan contigo el vehículo que conducías.
- `Guerra.buscar_pelea(banda, larga)` reutiliza `Partida.guerra` con `tipo == "pelea"`: una o dos tandas, sin barrio en juego y sin exigir el modo `guerra_calle`.
- Defensa propia: `actualizar_personas` marca como agresor a quien viene a por ti a menos de 32 metros, sin esperar al primer golpe (`Calle.marcar_agresor`).
- Actualizador: `actualizador.error_de_disco` traduce un fallo de escritura de Windows a una frase (`ErrorDisco`), `copias_del_juego` cuenta las veces que está abierto, y `menus_actualizar.a_mano` son los pasos para actualizar sin él.

### Domicilio, atracos, pactos, contratos, gente que actúa, convivencia y oficio de policía

Ocho módulos de la 1.7.1, cada uno un mixin de `Partida` salvo `ajustes.py`:

- `juego/ajustes.py`: la clase `Ajustes(seccion, numeros, listas, cero)` lee de los datos una sección de un solo elemento (`{"id": "general", ...}`) con números y listas de frases, cada uno con su valor de serie. Cada módulo crea la suya (`AJ = Ajustes(...)`); `mundo.cargar_datos()` las pone al día con `ajustes.configurar_todos(d)`. `AJ("clave")` da el número, `AJ.lista("clave")` la lista y `AJ.frase("clave", hueco=valor)` una frase al azar con sus huecos rellenos.
- `juego/domicilio.py` (`Domicilio`): `casa_aqui()`, `pedir_domicilio(cosas)`, `actualizar_domicilio(dt)`. El pedido en camino va en `Jugador.pedido` y se guarda. Secciones `carta_domicilio` (lista) y `domicilio`; tarifa `domicilio_envio`.
- `juego/atracos.py` (`Atracos`): `atracar_local(l)` generaliza el atraco de las tiendas con `caja_de_local(l)`; `con_atraco()` añade la opción al menú de cualquier local con caja (lo llama `menus_juego.lugar`). `Jugador.locales_vetados` guarda lo que recuerda cada local y `entrada_vetada(l)` lo aplica al ir a entrar. `asaltar_proveedor(l)` es el asalto, con `Jugador.proveedores` (veto, precios) y `Jugador.represalias`. `mandar_enemigos(clase, n)` manda a por el jugador a enemigos de un tipo, en su vehículo si lo tienen. Sección `atracos`.
- `juego/golpes.py` (`Golpes`, tanda 19): los golpes preparados. `Jugador.banda_gente` es la lista de la gente de la banda, uno por uno (`banda_fichas()` la ajusta a `Jugador.banda`, que sigue siendo la cuenta; `banda_alta`, `banda_quitar_ficha`, `banda_echar`, `banda_ligar()` da a cada aliado presente su ficha y su nombre). `golpes.preparar(p, lugar, empezar)` es el menú; el plan (`{"papeles": {id de ficha: papel}, "yo": {"dentro", "huida"}, "veh_id", "modelo"}`) se pasa a `atracar_local(l, plan)`, `empezar_atraco_banco(l, plan)` o `asaltar_proveedor(l, plan)`, que llaman a `golpe_adaptar(m, l, plan)`: la misión repetible lleva el plan en `m["golpe"]`, así que un reintento lo repite. `iniciar_mision` llama a `golpe_al_iniciar` y `_limpiar_mision` a `golpe_fin(False)`; al completarse, `golpe_fin(True)` hace el reparto cambiando la recompensa. `Partida.golpe` (no se guarda) lleva el estado: fase, alarma, cuándo llega la policía, vehículo y lo que se ha sorteado que sale mal (`_golpe_sortear`). Secciones `golpes` y `papeles_golpe`. Solo sin conexión (`golpe_bloqueo()`).
- Motor de misiones, dos campos nuevos de paso: `tarda` en `recoger` (segundos que tarda en abrirse: `mision_abrir`, `_paso_abrir`, estado en `ms["abriendo"]`) y `retraso` en `policia` (segundos hasta que cae la búsqueda: `ms["policia_en"]`; mientras no llega, el paso no se da por cumplido). Un aliado con `puesto` (un punto) se queda en él en vez de seguir al jugador (`extras.actualizar_aliado`).
- `juego/vuelo.py` (`Vuelo`, tanda 19) y `juego/vuelo_pantalla.py`: volar de verdad. `vuelo_real()` dice si está activo (opción `vuelo_real`; en las pruebas automáticas solo con `app.vuelo_en_pruebas`, igual que los trayectos con `viajes_en_pruebas`). Cada aparato lleva `alt`, `fase` (`tierra`, `despegue`, `vuelo`, `aterrizando`, `sin_motor`) y `queroseno` (0 a 100, se guarda con el vehículo en `averias_a_dict`); `conduccion.conducir` llama a `vuelo_controles(v, dt, teclas)` antes de mover, `_entrar_salir` a `vuelo_aterrizar(v)` y `_conducir_libre`, en el borde, a `vuelo_borde(v)`. La travesía es la pantalla `vuelo_pantalla.Crucero` (posición en kilómetros en el mapa de la comarca, rumbo, altitud, viento como vector, sucesos sorteados en `_plan_sucesos`, aproximación en `_aproximacion`); al acabar llama a `vuelo_llegar(v, datos)`, que hace el `cambiar_mapa`. `vuelo.AERONAVES` y `vuelo.MAPA_AIRE` salen de las secciones `aeronaves` y `mapa_aire`; `colocar(mapas)` da sitio a las localidades que no estén apuntadas (las de los mods) según sus muelles y sus carreteras, y `punto_aire(mapa)` tiene además un último recurso fijo. Hangares: `Jugador.hangares` (`{campo: {"propia", "naves", "pagado", "debe"}}`), `hangar_guardar`, `hangar_sacar`, `mandar_al_hangar`, alquiler en `_hangares_dia`. Secuestro: `Partida.secuestro` (no se guarda), `secuestrar(l, encargo)`, `radar_te_tiene()` (lo mira `combate.actualizar_policia`), `secuestro_encargo(l)` con semilla del día. Piloto comercial: `Partida.vuelo_trabajo` (no se guarda), `piloto_ofertas(l)`, `piloto_aceptar`, `_piloto_cobrar`; el título es `piloto`, en `titulos`. En un servidor: vuelo, travesías y hangares funcionan sin tocar el servidor (la travesía es una pantalla local y el cambio de localidad es el `cambiar_mapa` de siempre); secuestro y vuelos comerciales, no (`secuestro_motivo`, `piloto_motivo`). No hay modelos de vehículo nuevos ni cambia nada de lo que se exporta al servidor: la huella del mundo es la misma.
- `juego/pactos.py` (`Pactos`): `oferta_devolver`, `oferta_comprar`, `pedir_tributo`, `regatear`, `dia_pactos` (cada medianoche). `fuerza_propia()` y `rep_banda()` deciden; el azar de cada trato sale de la semilla de la partida, el día, la banda y el asunto, así que la respuesta es la misma todo el día. `Jugador.tributos` y `Jugador.tratos`. Sección `pactos`.
- `juego/contratos.py` (`Contratos`): `ofertas_contrato(l)` da los tres encargos del día; `empezar_contrato_de(l, oferta)` monta la misión con los pasos que ya existían (`eliminar`, `perseguir`, `seguir`, `escoltar`, `recoger`, `ir`). Sección `contratos` (lista; `situacion` es una de `contratos.SITUACIONES`). `Extras2.empezar_contrato` sigue siendo el contrato clásico. Un grupo de enemigos con `intimidar` se rinde en vez de caer (`Agente.se_rinde_con`, llamado desde `danar_persona`).
- `juego/reacciones.py` (`Reacciones`): `reaccion_tras(q, intencion, antes)` e `insistir(q)` son lo que la gente hace por su cuenta (opción `gente_actua`); `pedir_favor(q)` y `reclutar_persona(q)` son las opciones nuevas de la conversación. Quien acompaña al jugador lleva `estado == "sigue"` y lo mueve `paso_seguidor` desde `actualizar_personas`. `decidir_accion_ia(q, accion)` aplica las reglas del juego a lo que propone el modelo: `ia.py` solo acepta acciones de `ACCIONES` o, con la opción `ia_acciones`, de `ACCIONES_AMPLIADAS`; cualquier otra cosa es «nada», y en la lista no hay dinero ni objetos. Sección `reacciones`.
- `juego/convivencia.py` (`Convivencia`): `pedir_convivir(pers, casa)`, `saludo_de_casa`, `comer_en_casa`, `hacer_plan`, `peticion_cumplida(que)`, `dia_convivencia` (cada medianoche), `aventura_en_casa`. Estado en `Jugador.convive`, `convive_casa`, `convive_hoy` y `peticion_pareja`. Opción `pareja_convive`; los planes no dependen de ella. Secciones `planes_pareja` (lista) y `convivencia`. Las personas admiten `convivir` (`facil`, `si`, `nunca`).
- `juego/agente.py` (`Agente`): el turno es un trabajo (`Partida.trabajo` con `tipo == "policia"`), así que todo lo que ya miraba `trabajo` lo respeta. `empezar_turno`, `_aviso_nuevo`, `actualizar_agente`, `dar_alto`, `agente_intro`. `delito_de_servicio(puntos, texto)`, llamado desde `Combate.delito` después de comprobar que hay testigos, decide si es fuerza justificada, un apercibimiento o la expulsión. Estado del puesto en `Jugador.policia`; avisos resueltos en `stats["serv_policia"]`. Opción `oficio_policia`. Secciones `policia_oficio` y `avisos_policia` (lista; `tipo` es uno de `agente.TIPOS`); tarifa `academia_policia`.
- Tutoriales: el tipo de paso `practica` (`que`: `zarpar`, `timon`, `atracar`, `trabajar` o `servicio`; `metros` y `giro` para el timón) lo lleva `Misiones._paso_practica`. Un paso `ir` con `"exige": "radar"` no se cumple al llegar si no se ha usado el radar en ese paso (`ms["radar_usado"]`). Una misión con `"explicacion": true` no se juega: `Misiones.explicacion(m)` lee seguidos sus pasos de diálogo. Las voces grabadas se siguen buscando por misión, paso y frase, así que al tocar un tutorial hay que cuidar que cada grabación siga cayendo en su frase (hay una prueba que lo vigila).
- En un servidor en línea no existen el asalto a proveedores, la negociación con las bandas, el reclutamiento en la calle, la convivencia ni el oficio de policía; lo demás funciona igual. No se ha tocado `servidor/`, y la huella del mundo no cambia.
- Sonidos nuevos: `timbre` y `emisora` (`VERSION_CACHE` 19). En los packs son grabaciones CC0 de bigsoundbank.com (véase «Sonidos de terceros»).

### La reconquista de barrios

`juego/reconquista.py` (mixin `Reconquista` de `Partida`). Solo sin conexión: `rec_nivel()` da vacío con la opción `reconquista` en `apagado`, en un servidor (`en_servidor`) o con una partida con amigos en marcha (`online_activo()`), y entonces nada avanza.

- Estado: todo en `Jugador.reconquista` (un diccionario liso, que va con la partida): `fase`, `calma`, `descanso`, `informantes`, `bandas` (fuerza, moral, derrotas, `fuera`, `tregua`, `golpe`, `umbral`, `forastera`), `barrios` (lealtad, guardia, refuerzo, `pisado`, `de`), `asalto` y `partes`. Una partida anterior carga con `{}`; `rec()` lo rellena al primer uso y `cargar_dict` marca `_rec_cargada` si ya tenía barrios bastantes (calma inicial y aviso, una vez).
- Fase (`rec_fase`): `suave` con `suave_barrios` o más, `plena` con una ciudad entera, `mundo` con todas. `reconquista_revisar()` se llama cada dos segundos y cada medianoche.
- Cada medianoche (`dia_reconquista`, desde `_cobrar_negocios`): cobros de guardias e informantes, lealtad, treguas, crecimiento (`_rec_crecer`), banda forastera, y aviso del asalto pendiente o plan de uno nuevo (`_rec_planear`, `rec_elegir_objetivo`). Con la reconquista activa (`rec_activa()`), `sistemas.sucesos_territorio` no lanza sus ataques sueltos: nunca hay dos a la vez.
- El asalto (`asalto`): `prepara` hasta su día y su hora; `en_curso` con `quedan` en minutos de juego, que baja en `actualizar_reconquista` salvo en una misión o peleando. `rec_pasar_horas` (desde `pasar_horas`) aplica la gracia una vez. La defensa en persona usa `guerra.empezar_guerra(..., rec=...)`, que no depende de la opción `guerra_calle`; `_guerra_ganada` llama a `rec_defendido("persona")`. `rec_enviar_gente` y `_rec_vence` resuelven con `_rec_calculo`.
- La tregua está en `juego/pactos.py` (`oferta_tregua`, `pactar_tregua`, `menu_tregua`), con sus números en la sección `pactos`. El golpe preventivo (`empezar_golpe`) es una misión repetible generada, con cuatro variantes.
- Menús: `menu_reconquista` y `opciones_territorios` (lo que se añade a Territorios). Números y frases: `data/datos/vida.json`, sección `reconquista` (`reconquista.AJ`); esquema del editor, `ajuste_reconquista`.
- Sonidos: `amenaza_barrio`, `barrio_perdido`, `barrio_defendido`.
- Pruebas: `pruebas/test_171_reconquista.py`, que incluye simulaciones de sesenta días con cada intensidad.

### Vida, reputación y consecuencias (1.7.1)

`juego/honrado.py` (mixin `Honrado` de `Partida`) y `juego/menus_honrado.py`. Se apoya en los dos medidores que ya había, `Jugador.ciudadania` (prestigio) y `Jugador.reputacion` (fama), que son independientes; no hay un tercero.

- Nivel: `hon_nivel()` da 0 a 3 según la opción `consecuencias` (`apagado`, `suave`, `normal`, `exigente`; de serie `suave`) y siempre 0 en un servidor (`en_servidor`). `hon_f()` es el factor de las penalizaciones (`factor_suave`, `factor_exigente`). Las ventajas no se escalan. Las otras opciones: `impuestos_facturas`, `antecedentes`, `pareja_familiar`.
- Estado, todo en el jugador y con la partida: `antecedentes` (lista), `contrato`, `titulos`, `empresa` (por negocio), `creditos` (lista) y `honra` (cobros, deuda, fiado, embargo, rumor `sospecha`, dinero sin justificar `negro`, `asuntos` pendientes, abogado, cartas, vetos). `hon()` lo crea la primera vez con el periodo de gracia; una partida anterior lleva `_hon_cargada` y recibe un aviso único.
- Ganchos: `azar.mercado` (trato en comercios, `hon_trato`), `partida.pagar` (fiado, `hon_fiar`, con `_local` puesto en `entrar_interior`), `combate.delito` (`hon_delito`: encubrir, beneficio de la duda, delatar, fichado, rumor), `combate.detener` y `_trato_policia` (`hon_antecedente`), `vida.jornada` y `vida.servicio_hecho` (`hon_turno`), `partida._cobrar_negocios` (`ingreso_negocio`, `dia_honrado`), `extras3.repartir_ingresos_negocios` (caja del periodo y embargo), `misiones` (`cumple_vida`, `hon_mision_completada`, `prestigio` en las decisiones), `partida.interactuar` (`hon_ofrecer_mision`: la misión del buen camino va como última opción del menú del lugar), `agente.ingreso_motivo`, y `hon_negro` en atracos, tributos y encargos repetibles.
- Cada medianoche (`dia_honrado`): antecedentes que caducan, evaluación del contrato, negocios (nombre, tapadera, inspección), cobro de facturas e impuestos, cuotas, rumor y prensa, extorsión y asuntos sin contestar. Cada veinte segundos (`actualizar_honrado`): el aviso de partida antigua, el de los dos caminos, los controles y las situaciones de la calle.
- Los asuntos pendientes (`honra["asuntos"]`: inspección, prensa, extorsión) se resuelven con `hon_resolver(asunto, clave)`; pasado el plazo se resuelven solos.
- La trama: `data/datos/misiones_honrada.json` (capítulo 16), misiones con `honrada`, `requiere_vida`, `epilogos`. Sus escenas llevan voz grabada como las demás (en `data/voces/historia_principal`). El final queda en `decisiones["_final_honrado"]`, aparte del de la historia principal.
- Pareja apta para todos: `vida_sentimental()` sustituye a `modo_adulto()` en las relaciones (`adultos.dia_adultos`, `convivencia`, `sistemas.personas_aqui`, `menus_adultos.vida_social`); el compromiso y la boda van en la relación (`compromiso`).
- Números y frases: `data/datos/vida.json`, secciones `vida_honrada` (`honrado.AJ`), `titulos`, `empleos_fijos`, `mejoras_negocio`, `incidencias_trabajo` y `buenas_acciones`; esquema del editor en `editor/esquema_honrado.py`.
- Sonidos: `despido`, `inspeccion`, `factura` y `titulo` (`VERSION_CACHE` 24).
- Pruebas: `pruebas/test_171_honrado.py`, con la campaña entera sin delitos y tres simulaciones de sesenta días (honrado, delincuente y doble vida).
- Servidor: nada de esto llega al servidor todavía; los campos nuevos del jugador y los ingresos y gastos nuevos están descritos en las notas de la versión para cuando se lleve.

### La compra, la despensa y la cocina

- `juego/compra.py` (mixin `Compra`, y la pantalla `Tienda`) y `juego/menus_cocina.py` (los menús y la pantalla `Cocinando`). Cinco secciones de `vida.json`: `pasillos`, `productos`, `tipos_tienda` y `recetas` (listas) y `cocina` (los `Ajustes`). Lo de serie está también en el módulo (`PASILLOS`, `PRODUCTOS`, `TIPOS_TIENDA`, `RECETAS`), por si faltan en unos datos antiguos; hay una prueba que comprueba que coinciden.
- La tienda: `tipo_tienda(l)` decide la clase de una tienda (campo `surtido` del lugar, lista `lugares` del tipo, `palabras` del nombre o el tipo con `resto`) y `surtido(l)` da sus pasillos con sus productos. `precio_producto(l, prod)` aplica el vaivén del día (`mercado`), el `recargo` del tipo y la oferta. `oferta_de(l)` y `agotado(l, prod)` salen de la semilla de la partida, el día y la tienda: son iguales todo el día. `sistemas.con_recorrido` abre `compra.Tienda` (hija de `sistemas.Local`) en las tiendas con surtido; la cesta vive en esa pantalla y no se guarda. `comprar_productos(l, cosas)` cobra y `robar_productos(l, cosas)` es el hurto (`delito`, y `Jugador.locales_vetados` como en los atracos).
- Lo comprado va a `Jugador.encima` y, al guardarlo (`guardar_compra(casa)`), a `Jugador.despensa[casa.id]`. Las dos son listas de lotes: `{"id": producto, "n": cantidad, "cad": día en que caduca, o 0}`; un plato cocinado es `{"plato": receta, "nombre", "n", "cad", "hambre", "sed", "salud", "animo"}`, con sus efectos ya calculados, para que siga valiendo aunque el mod de la receta se quite. Nevera o despensa lo decide el `sitio` del producto (`lote_info`); la capacidad, `sitio_capacidad(casa, sitio)`. `tirar_caducado(lotes)` se llama al abrir; un lote vale hasta el día `cad` incluido.
- Cocinar: `receta_falta(casa, r)` y `cocinar(casa, r, rng)`, que gasta, pasa el tiempo, sortea la calidad (`Jugador.cocina_practica`, de 0 a 100, y el mueble `cocina`), sirve una ración y guarda las demás. `sistemas.Interior` llama a `menus_cocina.usar_cocina`, que sin nada guardado ni comida encima hace lo de antes (`Interior._picar_algo`).
- Tres campos nuevos del jugador (`despensa`, `encima`, `cocina_practica`), todos con valor de serie: el formato de las partidas no sube. No hay opciones nuevas. Depende solo del jugador, así que en un servidor funciona igual (el reloj no se adelanta al cocinar) y no se ha tocado `servidor/`; la huella del mundo no cambia.
- Sonidos nuevos: `cesta`, `nevera`, `cocina_cortar`, `cocina_freir`, `cocina_hervir` y `plato_servido` (`VERSION_CACHE` 20). En los packs son grabaciones CC0 de bigsoundbank.com (véase «Sonidos de terceros»).

### El mando: nada solo con teclado (1.7.1)

- `juego/mando.py` traduce el mando a teclas. Lo que no cabe en un botón ni en una combinación va en `MENU_ACCIONES` (frase, tecla, modificador, dónde vale, condición, explicación, si el menú se queda abierto): es el menú que abre la acción `menu_acciones`, de serie en combinar más gatillo derecho, a pie y al volante. `acciones_de(p)` da las que valen en ese momento.
- Regla: una tecla nueva en `ayuda.TECLAS` necesita un botón o combinación en `POR_DEFECTO`, una entrada en `MENU_ACCIONES`, o una línea en `SIN_BOTON` con su razón (`SOLO_A_PIE` para las generales que al volante no tienen sentido). En las pantallas que no son menús (`PANTALLA`), una tecla propia necesita un alias de una de las que el mando manda allí: la C de la cesta es Tabulador (`ALIAS_PANTALLA`). Lo vigila `pruebas/test_171_mando.py`.
- Los eventos del mando llevan `mando = True` (`_Ev`): no pasan por el cambio de teclas del teclado (`App.evento_tecla`) y en `menus.EntradaTexto` mueven la rueda de letras. `EntradaTexto(..., propuestas=lista o función)` ofrece textos ya escritos con Tabulador (X o Cuadrado): las listas `frases_chat`, `rol_frases_ic`, `rol_frases_yo` y `rol_frases_ooc` de `gente.json`, y `nombres_propuestos` de `vehiculos_propios` en `vida.json`.
- Frases habladas: `textos_mando` cambia las teclas por botones también cuando la función está en una combinación. Para pantallas que hablan con `app.decir`, `Mando.boton_pantalla(tecla, nombre)` da el nombre de la tecla o el del botón.

### Pruebas

`probar.bat` ejecuta toda la batería. Las pruebas manejan el juego como una persona, con teclas y fotogramas: juegan todas las misiones, recorren los mapas con el GPS, entran en todos los menús y lugares, juegan veinte días con el tiempo acelerado, conectan dos juegos entre sí, manejan un mando simulado y revisan la accesibilidad del editor. También fallan si se añade un sonido sin describir o una tecla sin documentar. No usan la red ni la tarjeta de sonido.

### Compilar

`compilar.bat` usa cx_Freeze y deja en `dist\PuertoBravo` una carpeta portable con `PuertoBravo.exe` y `EditorMods.exe`. Antes regenera los mods de serie, los sonidos que falten y las guías. Al terminar:

- Protege los datos: cada JSON se comprime, se cifra y se firma, y cambia de extensión (`.pbd` datos, `.pbm` mods, `.pbs` partidas, `.pbc` opciones). El código lee las dos formas, así que en el código fuente todo sigue siendo JSON legible.
- Comprueba sola que la carpeta está completa, protegida y limpia: sin partidas, opciones, registros, música personal ni documentación de desarrollo.

La protección usa una clave que va dentro del propio programa. Evita la edición casual; no es una barrera frente a quien analice el ejecutable.

### Publicar una versión

El juego se actualiza leyendo un archivo `version.json` firmado con Ed25519. La fuente (el servidor, GitHub, ambos o una dirección personalizada) solo decide de dónde se descarga: lo que se instala tiene que estar firmado con la clave privada de quien publica, cuya clave pública va en `juego/actualizador.py`.

1. Sube `VERSION` en `juego/__init__.py` y añade las novedades al principio de `data/docs/novedades_es.html` y de `data/docs/novedades_en.html`.
2. Ejecuta `compilar.bat`.
3. Ejecuta `publicar.bat`. Crea en `dist\publicar` el archivo `PuertoBravo_v<versión>.zip` y su `version.json` firmado, y los copia a la carpeta escrita en `publicar_destino.txt`, que es la carpeta web del servidor.
4. Para GitHub, crea la release `v<versión>` y sube esos mismos dos archivos, con `notas_github.md` como notas: lo deja `publicar.bat` en `dist\publicar`, con lo nuevo de la versión en español y en inglés (`novedades_es.html` y `novedades_en.html`, las únicas que se escriben desde la 1.7.3), y dice la orden `gh release create` que lo hace. El `version.json` lleva también las novedades por idioma (`novedades_por_idioma`): desde la 1.7.3, con el juego en español se leen las españolas y con cualquier otro idioma las inglesas; los juegos anteriores siguen leyendo `novedades`, en español.

La clave se crea una sola vez con `.venv\Scripts\python.exe herramientas\publicar.py clave` y queda en `herramientas\claves`. Esa carpeta y `publicar_destino.txt` están en `.gitignore`: la clave privada no debe estar nunca en el repositorio ni en el servidor. Guarda una copia fuera del equipo. Si haces un fork y quieres publicar tus propias versiones, crea tu clave y cambia en `juego/actualizador.py` la clave pública, la dirección del servidor y el repositorio.

La verificación de la firma está implementada con la biblioteca estándar, siguiendo el RFC 8032, y se comprueba en las pruebas con sus vectores oficiales. Si el paquete `cryptography` está instalado, se usa ese.

### Procesadores antiguos: las dos numpy

La numpy oficial (2.4 en adelante) exige un procesador con las instrucciones de x86-64-v2 (SSE4.2, SSSE3, POPCNT y demás). En uno anterior, cargarla hace que Windows cierre el programa con el código 0xC000001D. Para Python 3.15 no hay ruedas de numpy anteriores a esa exigencia, así que el juego compilado lleva dos:

- `lib\numpy`: la oficial de PyPI, para los procesadores actuales.
- `lib_antiguo\numpy`: la misma versión, compilada sin exigencias con `-Dcpu-baseline=none` y sin BLAS. Sigue usando las instrucciones modernas cuando el procesador las tiene, porque las elige al arrancar.

`juego/procesador.py` pregunta a Windows qué instrucciones hay (`IsProcessorFeaturePresent`) antes de importar numpy y pone delante la carpeta que toca. Si la elegida no carga, prueba la otra; si no carga ninguna, el juego lo dice en voz alta y se cierra con normalidad. La variable de entorno `PUERTOBRAVO_NUMPY=antigua` (u `oficial`) fuerza una, para probar.

La rueda para procesadores antiguos está en `terceros/numpy_antiguo`, lista para usar: `compilar.bat` la coloca en la compilación con `herramientas/poner_numpy_antiguo.py`. Solo hay que rehacerla si cambia la versión de numpy o la de Python, con `herramientas\compilar_numpy_antiguo.bat`, que necesita Visual Studio con las herramientas de C++. numpy tiene licencia BSD de tres cláusulas.

### Los dos motores de sonido

`juego/audio.py` es el mezclador clásico: mezcla en Python con numpy, con paneo estéreo, retardo entre oídos y atenuación por distancia. `juego/audio_al.py` hereda de él toda la lógica y cambia solo la salida: mantiene una fuente de OpenAL Soft por cada sonido y deja que la biblioteca haga la mezcla en binaural (HRTF). Se llama por `ctypes`, sin paquetes de Python, así que no depende de la versión de Python. `audio_al.crear()` decide cuál se usa: el envolvente solo si el jugador lo ha elegido, la biblioteca está y el procesador es moderno; en cualquier otro caso, o si falla al arrancar, el clásico.

La biblioteca, `soft_oal.dll` (OpenAL Soft 1.25.2, LGPL), está en `terceros/openal_soft` con su licencia, y `compilar.bat` la copia a `lib`. `herramientas/probar_motor_envolvente.py` hace una prueba real con el dispositivo de sonido.

### El instalador de actualizaciones deja rastro

`juego/actualizador.py` escribe un `.bat` que sustituye el programa cuando el juego se ha cerrado. Ese `.bat` apunta cada paso en `data/logs/actualizacion.log`: `PASO nombre`, `RESULTADO nombre codigo=N` (el código de robocopy; 8 o más es fallo), `FALLO paso=... codigo=... motivo=...` y `TERMINADA bien` o `TERMINADA mal`. Robocopy escribe en ese mismo archivo, con `/log+`, solo los errores, con el archivo y el error de Windows. `leer_registro_instalador()` lo interpreta y `motivo_del_fallo()` lo convierte en una frase para quien juega; al reabrirse con `--actualizacion-fallida`, el juego la dice y la guarda para Opciones, Actualizaciones. `limpiar_registro_instalador()` deja cada ruta en el nombre del archivo, para que el registro se pueda enviar.

Antes de cerrar, `problemas_para_instalar()` comprueba que se puede escribir en la carpeta, que no hay otro programa del juego abierto (un servidor en línea con su ficha no cuenta: se para y se vuelve a arrancar solo, como explica el apartado del servidor) (por la lista de procesos y probando a abrir cada `.exe` para escribir) y que hay sitio: `espacio_para_instalar()` suma la copia de seguridad, lo que crece cada archivo y un margen. Antes de descargar, `problema_para_descargar()` hace la cuenta con el ZIP, la versión extraída y la copia. Las pruebas (`pruebas/test_171_red_seguridad.py`) ejecutan el `.bat` de verdad sobre carpetas de pega, también con un archivo bloqueado; ninguna sale a internet.

### El motor de voz, con red de seguridad

El motor de `juego/vozgen.py` es código nativo: si el procesador no tiene lo que pide (AVX2, FMA y F16C), puede cerrar el proceso sin dar un error de Python. Por eso `disponible()` mira primero las tres capacidades (`capacidades()`: AVX2 se lo pregunta a Windows; FMA y F16C, a numpy) y, la primera vez, prueba el motor en un proceso aparte: el propio juego lanzado con `--probar-motor-voz`, que `main.py` atiende antes de abrir nada y que termina con 0, 10 (no carga) u 11 (no genera). Compilado con cx_Freeze es `PuertoBravo.exe --probar-motor-voz`; desde el código, `python main.py --probar-motor-voz`. El resultado se guarda en `data/voces_generadas/motor_probado.json` con la versión del juego y una huella de los archivos del motor, y se repite la prueba si cambia cualquiera de las dos. La prueba corre en segundo plano: mientras dura, `disponible()` contesta que no y `cuando_se_sepa()` avisa al terminar. Además, cada vez que el juego carga el motor dentro de su proceso lo apunta, y lo borra cuando ha generado la primera frase: si se cierra dos veces seguidas a medias, deja de intentarlo. `parar_prueba()` mata el proceso de prueba al cerrar el juego y antes de actualizar.

### Registro de sesión

`juego/registro.py` crea en `data/logs` una carpeta por sesión, con un máximo de cinco. Dentro quedan `sistema.txt` (versión, Windows, lector, sonido, mods, opciones), `sesion.log` (pantallas, teclas, todo lo que dice el juego, una foto del estado de la partida cada quince segundos, red, actualizaciones, fotogramas lentos y avisos), `errores.log` (cada error con su traza, el estado de la partida y las últimas teclas y sonidos) y `fallo_grave.log` si el proceso cae de golpe. Captura también las excepciones sin tratar del hilo principal y de los demás hilos.

Todo pasa por un filtro antes de escribirse: rutas del usuario, nombre de usuario y de equipo, direcciones IP y de internet, correos, claves y los nombres de los jugadores en red se sustituyen. Lo que se teclea en los cuadros de texto y los mensajes del chat no llegan a registrarse. Hay una prueba que juega una sesión con datos señuelo y falla si alguno aparece en la carpeta. Al añadir algo que maneje datos del jugador, usa `registro.privado()` o `registro.ocultar()`.

### Accesibilidad

La accesibilidad es el requisito principal del proyecto. Todo lo que ocurre en el juego tiene sonido propio y todo texto pasa por el lector de pantalla. Todas las teclas están en la ayuda (`F1`) y en el manual, que se generan a partir del mismo código. El editor sigue pautas de accesibilidad para wxPython: etiquetas asociadas a cada control, letras de acceso sin repetir, controles nativos y ayuda contextual con `Control+H`.

---

## 3. Crear mods

Un mod añade o cambia contenido sin tocar los datos originales: lugares, misiones con todos sus pasos, armas, vehículos, carreras, comidas, objetos, peces, personajes para elegir, capítulos, mapas enteros y, para el modo adulto, personas, planes, regalos y sustancias. Los mods están en `data\mods` y se cargan al arrancar. Una misión o un paso pueden depender de varias decisiones a la vez con `si_cruce` (`"concejal:1, trono:3"`), `si_cruce_min` y `si_cruce_max`, y una misión puede pedir una de cada rama con `requiere_alguna` (`"fd2 fd3 fd4; vd2 vd3"`). Cada mapa dice por dónde va la vía del tren con `tren_eje` y `tren_n`, y un lugar de tipo `aeropuerto` con `"aerodromo": true` es la pista corta de un pueblo. En cualquier texto, lo que cambia según el protagonista sea hombre o mujer se escribe entre corchetes, con la forma masculina, una barra y la femenina: `Bienvenid[o|a]`, `[el sobrino|la sobrina]`. Lo resuelve `juego/genero.py` justo antes de decir el texto.

### Con el editor

La forma normal es `EditorMods.exe` (o `editor.bat` desde el código fuente). Es una aplicación accesible con lector de pantalla: cada cosa se crea rellenando un formulario, `Control+H` explica el campo en el que estás y `F1` abre su manual (`data\docs\editor_mods_es.html`). Antes de guardar comprueba que todo lo que cita el mod existe, y avisa de lo que falta.

El editor guarda siempre protegido, como `.pbm`, que es lo que carga el juego compilado, y abre tanto los `.pbm` como los `.json`.

### A mano

Un mod también es un archivo JSON. El formato está explicado, con ejemplos, en `desarrollo/formato_de_los_mods.html`, y `desarrollo/ejemplo_mod.json` es un mod mínimo. Desde el código fuente, el juego carga directamente los `.json` de `data\mods`. El juego compilado no: avisa al arrancar y pide que el archivo se abra con el editor y se guarde, para que quede comprobado y protegido.

### Mods de serie

Vienen ocho, ya activados, que además sirven de modelo. Se generan con `herramientas/crear_mods_ejemplo.py`, donde se puede leer cómo está hecho cada uno:

- Bahía del Ocaso: una ciudad grande de costa, con seis barrios, tres bandas y una historia de veintiuna misiones (`herramientas/mod_bahia_ocaso.py`).
- Costa Dorada: un pueblo pesquero con su historia y un ejemplo de todo lo que admite un mod.
- Valdeolmos: un pueblo de viñas, con un fraude de vino y una carrera de tractores.
- Peñas Altas: un pueblo minero de montaña, con una mina que alguien explota de noche.
- Isla de los Vientos: una isla a la que se llega navegando, con raqueros y salinas.
- Noches de neón: la noche de Puerto Bravo, sin mapa nuevo, con taxis nocturnos y vida social.
- Oficios y recados: más vida honrada en Puerto Bravo.
- Motor y asfalto: coches, una moto, carreras y misiones al volante.

Para compartir un mod, pasa su archivo `.pbm`. Quien lo recibe lo copia en su `data\mods`.

Las misiones pueden llevar voces grabadas (`juego/voces.py`): archivos de sonido en `data\voces`, uno por frase. Las frases que dependen del protagonista tienen varias formas, con una arroba detrás del nombre: `m01_1_1@alex`, `m01_1_1@m`, `m01_1_2@alex_m`. El editor escribe el guion con el nombre de cada archivo y sus formas. No se aceptan mods con material de otros juegos ni voces clonadas de personas reales.

Las voces que trae el juego están generadas con Phonon 40m, un modelo de voz de [Gradium](https://gradium.ai/phonon) con licencia Creative Commons de reconocimiento y uso no comercial (CC BY-NC 4.0). El mismo modelo va con el juego, en `data\phonon`, para generar en el equipo de quien juega las frases que nombran a un personaje creado por él (`juego/vozgen.py`), con el paquete `ptts`, que es libre. El texto de la licencia está en `data\phonon\LICENCIA.txt`. El archivo del modelo, `model.q8.gguf`, pesa 95 megas y no está en este repositorio: `herramientas\preparar_phonon.py` lo copia de una carpeta con el modelo descargado de Hugging Face (`gradium/phonon-40m-multilingual`), y `compilar.bat` lo llama. Sin el modelo el juego funciona igual; esas frases las dice el lector de pantalla.

---

## 4. Packs de sonidos y de música

La guía completa, con la descripción y la duración de cada uno de los 279 sonidos, es `data\docs\cambiar_sonidos_es.html` (en inglés, `cambiar_sonidos_en.html`). Resumen:

### Sonidos

- Todos los efectos están en `data\sonidos`, en subcarpetas. `por_defecto` tiene los de serie, un archivo por sonido; si borras alguno, el juego lo vuelve a crear. Cada una de las demás subcarpetas es un pack.
- El pack se elige dentro del juego, en Opciones, Sonido y música, y se oye al momento.
- Vienen cuatro packs completos: Realista y Alternativo, con grabaciones reales de dominio público; Retro, con sonido de consola antigua, y Envolvente, para el motor de sonido envolvente. Los cuatro conservan el original en los sonidos de orientación (balizas, tonos, semáforos, radar y sonidos de los lugares), porque de ellos depende moverse por el juego.
- Para hacer el tuyo, crea una carpeta en `data\sonidos` y copia dentro tus grabaciones con el nombre exacto del sonido que sustituyen: `claxon.wav`, `paso_acera0.ogg`. Los sonidos del juego están en FLAC, sin pérdida; los tuyos pueden ser WAV, OGG, FLAC o MP3. No hace falta traerlos todos: lo que falte suena con el original. Se admiten WAV, OGG, FLAC y MP3.
- Un archivo `pack.json` opcional da al pack su nombre, autor, licencia y retoques de volumen por sonido.
- El volumen se iguala solo: cada sonido cambiado se lleva al nivel del original, y el jugador puede subir o bajar cualquiera por separado desde Opciones.

### Música

- Radio: cada emisora tiene su archivo en `data\radio`. Una emisora puede tener varias canciones (`bravo.mp3`, `bravo_1.mp3`, `bravo_2.mp3`...), que van rotando. Cualquier otro archivo de audio que dejes ahí es una emisora nueva, y `data\radio\mi_musica` es la emisora con tu propia música. Las canciones de más de cinco minutos se leen y suenan por tramos de un minuto (`juego/musica.py`), así que una grabación de varias horas no ocupa más memoria que una canción corta.
- Ambiente: `data\musica` tiene una carpeta por situación (`menu`, `exploracion`, `noche`, `mar` y `tension`). Se usan todas las piezas que haya en cada una, al azar, se llamen como se llamen.
- Toda la música se nivela sola al cargarla, así que ninguna pista suena más fuerte que otra.

### Sonidos de terceros

Los packs Realista y Alternativo se montan con grabaciones de dominio público (licencia CC0) de kenney.nl, opengameart.org, freesound.org y bigsoundbank.com. Cada pack lleva un archivo `CREDITOS.txt` con el origen de cada sonido.

Reglas de los packs, con sus pruebas vigilantes en `pruebas/test_171_sonidos.py`:

- Las cinco carpetas de `data/sonidos` (`por_defecto`, `realista`, `alternativo`, `retro` y `envolvente`) tienen exactamente los mismos sonidos, con los mismos nombres y sin ninguno en dos formatos. Un sonido nuevo se añade a `sintesis.generar()` (al final, subiendo `VERSION_CACHE`), a `catalogo_sonidos` (grupo y descripción) y a los packs con `herramientas/crear_packs.py anadir <nombres>`.
- `crear_packs.py anadir` sirve también para cambiar un sonido ya instalado: pone la grabación que diga la tabla del pack (`PACKS`, `EXTRA`, `CALLE`, `V171`, `PROPIAS`) o, si no hay, el sonido de serie; el pack Retro hereda del Realista lo que no tiene sonido de consola y el Envolvente copia del Realista lo que no es orientación ni un ambiente suyo. Después reescribe `CREDITOS.txt` (una línea por grabación, la lista de los que son el sonido de serie y la cuenta de la cabecera) y las cuentas de `pack.json`, de modo que siempre cuadran con los archivos.
- Las grabaciones sueltas llevan en `DETALLE` su título, su autor y su página, y así salen en `CREDITOS.txt`. Las de la 1.7.1 son de bigsoundbank.com, todas CC0 y de Joseph SARDIN salvo las que se indican: megáfono («Megaphone, larsen» 9 y 4), emisora («Walkie talkie: Start» y «Keypad tones»), timbre («Doorbell house #1»; «Doorbell #6», de Dorian CLAIR), nevera («Fridge door»), cocina («Cutting board, zucchini» 2 y 1, «Frying pan» 3 y 2, «Boiling water», «Small Broth in a Pot»), plato («Large Plate, set on Table», «Small plate, set on table»), cesta («Pack of chips, manipulation #2»; «Tin can #1», de DenisChardonnet) y barrios («Bass Tom, #1», repetido tres veces; «Church Bell»; «Drum roll 3 S» y «Drum Roll 1 L»). Los originales descargados se guardan fuera del repositorio, en `adjuntos/fuentes/bigsoundbank_171`, con su `LEEME.txt`.
- Recortes de `crear_packs.py`: además de `dur`, `golpe`, `bucle` y `desde`, admite `entrada` y `fundido` (segundos de fundido al principio y al final, para ruidos continuos que se cortan) y `veces` (la misma toma repetida en esos instantes).
- `chat_personaje`, `chat_fuera`, `chat_accion` y `espera_servidor` son en todos los packs el sonido de serie: son un código de tonos, no el ruido de una cosa.
- Los sonidos de orientación de los packs son los de `por_defecto`, byte a byte en lo que importa: la prueba compara las muestras.
- La clasificación de los sonidos es una sola y está en `juego/catalogo_sonidos.py`: `GRUPOS` (título, consejo para la guía y clave, en el orden en que se enseñan) y `SONIDOS` (por cada grupo, archivo, nombre que se dice y explicación de lo que significa oírlo). De ahí salen, con los mismos grupos, nombres y orden, Aprender los sonidos (`menus_juego.sonidos`), Opciones, Ajustar el volumen de cada sonido (`menus_juego.volumen_sonidos`), la guía de sonidos y la lista para packs (`generar_datos.py`); todos pasan por `catalogo_sonidos.clasificar`, que ordena cada grupo alfabéticamente por el nombre hablado (`orden`: sin tildes y con la eñe tras la ene). Los grupos son 20, por lo que se hace en el juego: orientación y GPS; sonidos de los lugares; moverse a pie y nadar; vehículos y conducción; averías, taller, gasolina y robo de vehículos; barcos, helicópteros, tren, tranvía y avión; armas, el disparo de cada una; combate, puntería y heridas; policía y emergencias; gente de la calle y animales; casa, cocina y comida; tiendas, dinero y objetos; menús, móvil y avisos del juego; misiones, trabajo, reputación y ánimo; territorios y bandas; jugar en línea y rol; pesca, casino y juegos; ambientes y clima; relaciones, solo con el contenido para adultos; sustancias y trapicheo, solo con el contenido para adultos. Ninguno puede caer en «Otros sonidos», que solo existe para un archivo añadido a mano.
- `IMPORTANTES` es el orden del grupo «Los más importantes» y el glosario `ayuda.SONIDOS` se deriva de él. `es_orientacion` dice qué sonidos conservan los packs (no depende de los grupos). `buscar` es el buscador de los dos menús (`menus_juego.buscar_sonido`): todas las palabras, en nombre, explicación, grupo o nombre de archivo, sin tildes ni mayúsculas.
- El volumen por sonido se guarda en `vol_sonidos` por nombre de archivo, así que reclasificar no pierde nada. `packs.factor`, `packs.cambiado` y `packs.restablecer` dan el ajuste que de verdad se aplica, si está cambiado y lo devuelven al de serie; el menú (`MenuVolumenes`) añade Suprimir, la lista «Sonidos cambiados» y restablecer un grupo.

## Colaboradores y menciones

Gracias a todas las personas que han ayudado a mejorar Puerto Bravo desde GitHub. Cada vez que alguien nuevo colabora, se añade aquí, en este documento y en su versión en inglés.

### Con código, traducciones y mods

- [patricus3](https://github.com/patricus3): el estilo temerario del piloto automático del GPS y el mod El Diablo, una agencia de sicarios con sus misiones y sus contratos. Además, sus avisos y propuestas trajeron las novedades en inglés y los estilos de conducción con prisa, la compilación en cualquier Windows, el arreglo de pruebas que fallaban, que cada partida guarde en su propia ranura, que el desguace pague las mejoras de tus vehículos, la lista de lugares de más cerca a más lejos, el arreglo de la comprobación de la compilación, el laboratorio sin su minijuego, que el juego diga por qué sube el nivel de búsqueda, que el piloto con mucha prisa vaya a toda velocidad que una misión pueda pedir contratos del tablón cumplidos que tus explosivos no hieran a quien va contigo en el coche y que los combates del gimnasio se peleen en su propio pabellón. Además, creó el grupo de Telegram de la comunidad en inglés y lleva el servidor de jugadores Patricus productions.
- [Daoductrung](https://github.com/Daoductrung): la traducción al vietnamita del juego, de toda su documentación y del mod Marisma Negra, y el arreglo para que la ficha de los mods y las mejoras del taller salgan en el idioma del juego.
- [leoguimaoficial](https://github.com/leoguimaoficial): la traducción completa al portugués de Brasil y sus correcciones.
- [dimasya34](https://github.com/dimasya34): la traducción al ruso del juego, su README y sus correcciones, el arreglo del instalador de las actualizaciones, que con el juego en ruso no se podía ejecutar, y los nombres del mando en ruso.
- [MichalBrajer123](https://github.com/MichalBrajer123): la traducción al polaco del juego, de sus guías y del mod Marisma Negra, con las voces de las escenas en polaco, y la propuesta de arrancar y apagar el motor del vehículo.

### Con avisos de fallos y propuestas

- [lishi-lg](https://github.com/lishi-lg): el primer fallo avisado, con su registro de error, y las propuestas de bajar la fama en la calle con los chavales del barrio y de hacer más cosas con tu acompañante: invitarle a algo, regalarle un décimo, llegar juntos a casa y usar el móvil sin salir de ella; y las de llevarte a la comisaría más cercana, distinguir la pesca de río y de mar, elegir los sucesos callejeros y crearlos en los mods, y unos días de rencor de la expareja; el aviso de que quien vive contigo estaba en casa y en su trabajo a la vez, la propuesta de consultar el horario de un local desde la lista de lugares, y un tutorial de iniciación en audio para la Comunidad de jugadores.
- [zeoltan](https://github.com/zeoltan): dos cierres inesperados del juego, el todoterreno que no aparecía y la propuesta de un pack de sonidos.
- [aaronalostiza](https://github.com/aaronalostiza): el cierre del juego al entrar a un servidor y otro error.
- [jgudino013-ship-it](https://github.com/jgudino013-ship-it): que las bandas no te ataquen en oleadas cuando solo te defiendes.
- [amirh123123](https://github.com/amirh123123): la petición de más idiomas, empezando por el inglés.
- [cmjh](https://github.com/cmjh): un juego que no llegaba a arrancar.
- [retrochiptuner](https://github.com/retrochiptuner): la misión de la llave del polvorín, que seguía saliendo como disponible.
- [UnDuende](https://github.com/UnDuende): el grupo de Telegram de la comunidad en español.
- [ebram212131](https://github.com/ebram212131): la petición de que el juego funcione también en Linux y en Mac.
- [matheus-raeski](https://github.com/matheus-raeski): el servidor de jugadores RP Brasil, de rol y en portugués.
- [SeanTerry01](https://github.com/SeanTerry01): el aviso de que la ficha de Marisma Negra salía en español con el juego en inglés, y la propuesta de traducir el nombre del juego.
- [Selak998](https://github.com/Selak998): la propuesta de la ficha técnica de los vehículos, para compararlos antes de comprar.

---

## Licencia

Licencia MIT: puedes usar, modificar y distribuir cualquier parte del juego, con la única condición de conservar el aviso de derechos y la licencia. Está en el archivo `LICENSE`.
