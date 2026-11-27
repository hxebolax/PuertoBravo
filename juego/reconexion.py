"""La espera a que vuelva un servidor en línea, y la vuelta.

Cuando el servidor avisa de que se reinicia para actualizarse o por mantenimiento, o cuando la conexión se corta sin
más, el juego no vuelve al menú: se queda en esta pantalla, con la partida tal cual y el mundo parado, y va probando a
entrar otra vez, cada vez con más calma. Cuando el servidor vuelve, entra con la misma identidad y manda su personaje
como estaba, en lugar de cargar el que el servidor tenía guardado.

Lo que se oye: una explicación al empezar, un tono flojo cada pocos segundos, y de tarde en tarde cuánto se lleva
esperando. Cualquier tecla lo repite; F1 lo explica; Escape deja de esperar y sale al menú.

Con mando, igual que en las demás pantallas del juego: A o Equis (o X o Cuadrado) repite cómo va, B o Círculo (o el
botón Menú u Options) deja de esperar, e Y o Triángulo (o el botón Vista o Share) lo explica. Con un mando conectado,
la pantalla dice los botones en lugar de las teclas.
"""
from .i18n import tr
import json
import os
import random
import threading
import time

import pygame

from . import enlinea, registro, rutas

ESPERAS = (3.0, 5.0, 8.0, 12.0, 15.0)          # segundos entre un intento y el siguiente: crecen hasta un tope
CADA_TONO = 6.0                                # cada cuánto suena el tono de espera
AVISOS = (30.0, 60.0, 120.0)                   # cuándo se dice cuánto se lleva esperando; después, cada dos minutos
ARCHIVO_VOLVER = "volver_servidor.json"       # a qué servidor volver tras actualizar el juego: solo su nombre y su dirección
VOLVER_VALE = 2 * 3600                         # segundos que vale esa nota

EXPLICA = {
    "actualizacion": (tr("El servidor se está actualizando."), tr("El servidor se ha cerrado para actualizarse.")),
    "reinicio": (tr("El servidor se está reiniciando por mantenimiento."), tr("El servidor se ha cerrado un momento por mantenimiento.")),
    "cierre": (tr("El servidor se ha cerrado."), tr("El servidor ha dejado de funcionar.")),
    "corte": (tr("Se ha cortado la conexión con el servidor."), tr("Se ha perdido la conexión con el servidor.")),
}
SIGUE = (tr("Sigo intentándolo."), tr("Sigo probando."), tr("Aún no contesta: sigo en ello."), tr("Todavía nada: sigo intentándolo."))


def tiempo_txt(segundos):
    """«40 segundos», «1 minuto», «3 minutos y medio»: lo que se lleva esperando, dicho sin cifras de más."""
    s = int(max(0, segundos))
    if s < 55:
        return tr('{max} segundos').format(max=(max(5, int(round(s / 5.0)) * 5)))
    medios = int(round(s / 30.0))
    m, medio = medios // 2, medios % 2
    if m == 0:
        return tr("medio minuto")
    return (tr("1 minuto") if m == 1 else tr('{m} minutos').format(m=(m))) + (tr(" y medio") if medio else "")


def codigo_de(motivo):
    """Por qué no se ha podido entrar, en una palabra: «red» (no contesta), «reiniciando», «lleno», «version»,
    «certificado» o nada (cualquier otro rechazo). Un servidor nuevo lo dice él; con uno anterior se deduce del texto."""
    codigo = getattr(motivo, "codigo", "")
    if codigo:
        return codigo
    t = str(motivo or "").lower()
    if t.startswith(tr("certificado: ")) or "cifraba la conexión" in t:
        return "certificado"
    if "está lleno" in t or "demasiadas conexiones" in t:
        return "lleno"
    if "pide la versión" in t or "versión más nueva del juego" in t or "demasiado antiguo" in t:
        return "version"
    if "no se pudo conectar" in t or "nie udało się połączyć" in t or "no contesta" in t or "ha cortado la conexión" in t:
        return "red"
    return ""


# ------------------------------------------------------ volver a un servidor tras actualizar el juego
def _ruta_volver():
    return rutas.data("config", ARCHIVO_VOLVER)


def anotar_vuelta(servidor):
    """Antes de cerrar el juego para actualizarlo: a qué servidor se quería volver. Solo su nombre y su dirección, que ya
    están en la lista de servidores: ni identidad ni contraseñas."""
    try:
        os.makedirs(os.path.dirname(_ruta_volver()), exist_ok=True)
        with open(_ruta_volver(), "w", encoding="utf-8") as f:
            json.dump({"dir": str(servidor.get("dir", "")), "nombre": str(servidor.get("nombre", "")), "t": int(time.time())}, f, ensure_ascii=False)
        return True
    except OSError:
        return False


def leer_vuelta(borrar=True):
    """La nota de «volver a este servidor», si la hay y es reciente. Se borra al leerla: vale una vez."""
    ruta = _ruta_volver()
    try:
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    finally:
        if borrar:
            try:
                os.remove(ruta)
            except OSError:
                pass
    if not isinstance(d, dict) or not d.get("dir") or time.time() - float(d.get("t") or 0) > VOLVER_VALE:
        return None
    return d


def ofrecer_vuelta(app, nota):
    """Tras actualizar el juego porque un servidor lo pedía: se ofrece volver a ese servidor."""
    from .menus import Menu, Opcion
    lista = app.cfg["servidores"]
    s = next((x for x in lista if x.get("dir") == nota.get("dir")), None)
    if s is None:
        return False
    nombre = s.get("nombre") or nota.get("nombre") or tr("el servidor")

    def volver():
        app.cerrar(m)
        app.decir(tr('Conectando con {nombre}.').format(nombre=(nombre)), True)
        enlace, motivo = enlinea.conectar(app, s)
        if enlace is None:
            app.son("error")
            app.decir(str(motivo) + tr(" Puedes probar otra vez desde el menú principal, Jugar en un servidor."), True)
            return
        app.cfg.guardar()
        app.enlace = enlace
        if enlace.ok.get("partida"):
            app.empezar_partida(enlace.ok["partida"])
        else:
            from . import menus_vida
            menus_vida.elegir_personaje(app)
    m = Menu(app, tr('El juego ya está actualizado. Antes de actualizar estabas en {nombre}').format(nombre=(nombre)), [
        Opcion(tr('Volver a entrar en {nombre}').format(nombre=(nombre)), volver, ayuda=tr("Entra con tu personaje, tal como quedó guardado en el servidor.")),
        Opcion(tr("Ahora no"), lambda: app.cerrar(m), ayuda=tr("Te quedas en el menú principal. El servidor sigue en tu lista, en Jugar en un servidor."))])
    app.abrir(m)
    return True


# ============================================================================ la pantalla de espera
class Espera:
    """La pantalla de espera. El mundo queda parado debajo, con la partida tal cual."""
    pausa_mundo = True
    cerrado_al_final = True

    def __init__(self, app, partida, causa="corte", motivo="", vuelve=0):
        self.app, self.p = app, partida
        self.causa = causa if causa in EXPLICA else "corte"
        self.motivo = str(motivo or "")
        self.servidor = partida._sv_servidor
        self.nombre = str(self.servidor.get("nombre") or tr("el servidor"))
        self.maximo = 60.0 * max(1, int(app.cfg["reconectar_minutos"]))
        self.t = 0.0                           # lo que se lleva esperando
        self.t_tono = 2.0
        self.n = 0                             # intentos hechos
        # Si el servidor ha dicho cuánto calcula que tarda, el primer intento espera un poco más: antes no va a estar.
        self.t_prox = 6.0 if self.causa in ("actualizacion", "reinicio") else ESPERAS[0]
        self.vuelve = max(0, int(vuelve or 0))
        self.avisos = list(AVISOS)
        self.hilo = None
        self.resultado = None                  # (enlace, motivo) del intento en marcha, cuando termina
        self.estado = "esperando"              # esperando | version | fin
        self.version_txt = ""
        self.final = ""                        # lo que se dice al cerrarse la pantalla
        self.ultimo = ""                       # lo último que pasó en un intento, para repetirlo
        self.dejada = False
        registro.info("red", "Empieza la espera a que vuelva el servidor", causa=self.causa)

    # ------------------------------------------------------------------- lo que se dice
    def _con(self):
        """Con qué se hace cada cosa en esta pantalla, dicho para quien juega: las teclas o, con un mando conectado y la
        opción de decir los botones puesta, los botones de ese mando."""
        md = getattr(self.app, "mando", None)
        if md is not None and md.conectado and self.app.cfg["mando_textos"]:
            n = md.nombre_boton
            return {"salir": tr('El botón {n}').format(n=(n('b'))), "repetir": tr('El botón {n}').format(n=(n('a'))), "ayuda": tr('El botón {n}').format(n=(n('y'))), "intro": tr('el botón {n}').format(n=(n('a'))),
                    "salir_min": tr('el botón {n}').format(n=(n('b')))}
        return {"salir": tr("Escape"), "repetir": tr("Cualquier tecla"), "ayuda": "F1", "intro": tr("Intro"), "salir_min": tr("Escape")}

    def _explicacion(self):
        que = EXPLICA[self.causa][0]
        if self.causa in ("actualizacion", "reinicio"):
            cuanto = tr(' Suele tardar {tiempo_txt}.').format(tiempo_txt=(tiempo_txt(self.vuelve))) if self.vuelve >= 30 else ""
            return tr('{que}{cuanto} Te reconectaré en cuanto vuelva y seguirás donde estabas, con todo lo que llevabas.').format(que=(que), cuanto=(cuanto))
        return tr('{que} Voy a intentar volver a entrar yo solo. Si lo consigo, sigues donde estabas, con todo lo que llevabas.').format(que=(que))

    def _estado_txt(self):
        if self.estado == "version":
            c = self._con()
            return (tr('{nombre} ha vuelto, pero {version_txt} Pulsa {intro} para buscar la actualización del juego e instalarla, o {salir_min} para salir al menú principal. Tu personaje está guardado en el servidor.').format(nombre=(self.nombre), version_txt=(self.version_txt), intro=(c['intro']), salir_min=(c['salir_min'])))
        falta = max(0.0, self.maximo - self.t)
        return (tr('{v} Llevas esperando {tiempo_txt}. ').format(v=(EXPLICA[self.causa][0]), tiempo_txt=(tiempo_txt(self.t)))
                + (f"{self.ultimo} " if self.ultimo else "")
                + (tr('Vuelvo a probar dentro de {max} segundos. ').format(max=(max(1, int(round(self.t_prox))))) if self.hilo is None else tr("Estoy probando ahora mismo. "))
                + tr('Esperaré {tiempo_txt} más como mucho. {salir} deja de esperar y sale al menú principal.').format(tiempo_txt=(tiempo_txt(falta)), salir=(self._con()['salir'])))

    def al_entrar(self):
        if self.estado == "version":
            self.app.decir(self._estado_txt(), True)
            return
        if self.t < 1.0:
            self.app.son("notificacion")
            c = self._con()
            self.app.decir(self._explicacion() + tr(' Espera. {repetir} dice cómo va. {ayuda} lo explica. {salir} deja de esperar y sale al menú principal.').format(repetir=(c['repetir']), ayuda=(c['ayuda']), salir=(c['salir'])), True)
        else:
            self.app.decir(self._estado_txt(), True)

    def ayuda(self):
        return (tr("Pantalla de espera del servidor. El juego está parado tal como lo dejaste: tu sitio, tu vehículo, tu salud, tu dinero y tu misión no cambian "
                "mientras esperas. El juego prueba a entrar otra vez cada pocos segundos, cada vez con más calma, y cuando el servidor vuelve entra solo "
                "con tu identidad de siempre, sin pedirte nada. El tono de dos notas flojas quiere decir que sigue esperando. De vez en cuando dice cuánto llevas. "
                "Cualquier tecla repite cómo va. Escape deja de esperar y sale al menú principal: tu personaje se queda en el servidor como estaba en su último guardado. "
                "Con mando: A o Equis repite cómo va, B o Círculo deja de esperar, e Y o Triángulo da esta explicación. "
                "Cuánto se espera como mucho, y si se espera o no, se elige en Opciones, Jugar en línea."))

    # ------------------------------------------------------------------------- teclas
    def tecla(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            self.abandonar()
        elif k in (pygame.K_F1, pygame.K_n):      # F1; con mando, el botón Vista o Share, y también Y o Triángulo (que aquí llega como N)
            self.app.decir(self.ayuda(), True)
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.estado == "version":
            self.buscar_actualizacion()
        else:
            self.app.decir(self._estado_txt(), True)

    def abandonar(self):
        self.dejada = True
        guardado = self.p.sv_guardado_txt()
        self._salir(tr('Dejas de esperar a {nombre}. {guardado} Para volver, entra otra vez desde Jugar en un servidor.').format(nombre=(self.nombre), guardado=(guardado)))

    def _salir(self, texto, sonido=None):
        """Se acabó la espera sin volver: al menú principal, diciendo por qué. La partida viva se deja."""
        self.estado = "fin"
        registro.info("red", "Termina la espera sin volver al servidor", segundos=int(self.t), intentos=self.n)
        if sonido:
            self.app.son(sonido)
        self.p.sv_salir(texto, al_menu=True)

    def buscar_actualizacion(self):
        from . import menus_actualizar
        anotar_vuelta(self.servidor)             # tras actualizar, el juego ofrece volver a este servidor
        menus_actualizar.buscar(self.app)

    # ---------------------------------------------------------------------- intentos
    def _conectar(self):
        propio = getattr(self.app, "reconexion_conectar", None)      # las pruebas pueden poner aquí su manera de conectar
        if propio is not None:
            return propio(self.app, self.servidor)
        return enlinea.conectar(self.app, self.servidor)

    def _intentar(self):
        self.n += 1
        if self.app.pruebas:                     # en las pruebas, sin hilos: el resultado, al momento
            self.resultado = self._conectar()
            return

        def trabajo():
            try:
                r = self._conectar()
            except Exception as e:               # un fallo raro al conectar no tumba la espera: cuenta como que no contesta
                registro.excepcion("red", "Fallo al intentar volver al servidor")
                r = (None, enlinea.Motivo(tr('No se pudo conectar: {__name__}.').format(__name__=(type(e).__name__)), "red"))
            if self.estado == "fin":             # se dejó de esperar mientras conectaba: esa conexión no se usa
                if r[0] is not None:
                    r[0].cli.cerrar()
                return
            self.resultado = r
        self.hilo = threading.Thread(target=trabajo, daemon=True)
        self.hilo.start()

    def _atender(self, enlace, motivo):
        self.hilo = None
        if enlace is not None:
            return self._volver(enlace)
        codigo = codigo_de(motivo)
        registro.info("red", "Intento de volver al servidor sin éxito", intento=self.n, codigo=codigo or "rechazo")
        if codigo in ("red", "reiniciando", "lleno"):
            self.ultimo = {"red": tr("El servidor todavía no contesta."), "reiniciando": tr("El servidor está arrancando."),
                           "lleno": tr("El servidor ha vuelto, pero ahora mismo está lleno.")}[codigo]
            self.t_prox = ESPERAS[min(self.n, len(ESPERAS) - 1)]
            return
        if codigo == "version":
            minima = getattr(motivo, "minima", "")
            self.estado = "version"
            self.version_txt = (tr('ahora pide la versión {minima} del juego o una posterior, y tú tienes una anterior.').format(minima=(minima)) if minima
                                else tr("ahora pide una versión del juego más nueva que la tuya."))
            self.app.son("error")
            self.app.decir(self._estado_txt(), True)
            return
        if codigo == "certificado":
            return self._salir(tr('{nombre} ha vuelto, pero no presenta el mismo certificado que antes, y por seguridad no entro solo. Si quien lo lleva te ha dicho que lo ha cambiado, entra desde Jugar en un servidor y acéptalo allí. ').format(nombre=(self.nombre))
                               + self.p.sv_guardado_txt(), "error")
        self._salir(tr('{nombre} ha vuelto, pero no te deja entrar como antes: {rstrip}. No puedo seguir con la partida que tenías abierta. ').format(nombre=(self.nombre), rstrip=(str(motivo).rstrip('.')))
                    + self.p.sv_guardado_txt(), "error")

    def _volver(self, enlace):
        """El servidor ha vuelto y nos ha dejado entrar: la partida sigue, tal cual."""
        self.estado = "fin"
        registro.info("red", "Vuelve al servidor tras la espera", segundos=int(self.t), intentos=self.n)
        p = self.p
        self.final = p.sv_entrar(enlace, vuelta=True) or ""
        self.app.cerrar(self)

    def cerrado(self):
        if self.final:
            self.app.decir(self.final)

    # ------------------------------------------------------------------ cada fotograma
    def actualizar(self, dt):
        if self.estado != "esperando":
            return
        self.t += dt
        if self.resultado is not None:
            r, self.resultado = self.resultado, None
            self._atender(*r)
            if self.estado != "esperando":
                return
        self.t_tono -= dt
        if self.t_tono <= 0:
            self.t_tono = CADA_TONO
            self.app.son("espera_servidor", vol=0.5)
        if self.avisos and self.t >= self.avisos[0]:
            self.avisos.pop(0)
            if not self.avisos:
                self.avisos.append(self.t + 120.0)
            self.app.decir(tr('Llevas esperando {tiempo_txt}. {choice}').format(tiempo_txt=(tiempo_txt(self.t)), choice=(random.choice(SIGUE))))
        if self.t >= self.maximo and self.hilo is None:
            return self._salir(tr('{nombre} no ha vuelto en {tiempo_txt}, que es lo más que tienes puesto que espere, y dejo de intentarlo. ').format(nombre=(self.nombre), tiempo_txt=(tiempo_txt(self.maximo)))
                               + self.p.sv_guardado_txt() + tr(" Cuando el servidor vuelva, entra otra vez desde Jugar en un servidor. "
                               "El tiempo de espera se cambia en Opciones, Jugar en línea."), "error")
        if self.hilo is None:
            self.t_prox -= dt
            if self.t_prox <= 0:
                self.t_prox = ESPERAS[min(self.n + 1, len(ESPERAS) - 1)]
                self._intentar()
