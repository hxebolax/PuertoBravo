"""Aplicación: ventana, bucle principal y pila de pantallas."""
from .i18n import tr
import os
import sys

import pygame

from . import NOMBRE, VERSION, rutas
from . import menus_juego, mundo, packs, registro, sintesis
from .audio import Mezclador
from .config import Config
from .mando import Mando
from .musica import MusicaAmbiente, Radio
from .voz import Voz


def al_frente():
    """Pone la ventana del juego en primer plano. Tras actualizar la abre el instalador, que va escondido, y Windows no
    deja que se ponga delante sola: quien juega con lector se quedaría en otra ventana sin saberlo."""
    if os.name != "nt":
        return
    try:
        import ctypes
        u32, k32 = ctypes.windll.user32, ctypes.windll.kernel32
        hwnd = pygame.display.get_wm_info().get("window")
        if not hwnd or u32.SetForegroundWindow(hwnd):
            return
        delante = u32.GetForegroundWindow()
        suyo = u32.GetWindowThreadProcessId(delante, None) if delante else 0
        mio = k32.GetCurrentThreadId()
        unido = bool(suyo and suyo != mio and u32.AttachThreadInput(mio, suyo, True))
        try:
            u32.ShowWindow(hwnd, 9)                           # SW_RESTORE
            u32.BringWindowToTop(hwnd)
            u32.SetForegroundWindow(hwnd)
        finally:
            if unido:
                u32.AttachThreadInput(mio, suyo, False)
        registro.info("arranque", "Ventana al frente tras actualizar", conseguido=u32.GetForegroundWindow() == hwnd)
    except Exception as e:
        registro.aviso("arranque", "No se pudo poner la ventana al frente: " + str(e))


class EventoFalso:
    def __init__(self, key, mod=0, unicode=""):
        self.key = key
        self.mod = mod
        self.unicode = unicode


class App:
    def __init__(self, pruebas=False):
        self.pruebas = pruebas
        from . import enlinea
        _perfil = enlinea.perfil()                          # solo en las copias de pruebas: cada instancia, sus opciones
        self.cfg = Config(os.path.join(rutas.DATA, "config_pruebas.json") if pruebas else (rutas.archivo_config("config_" + _perfil) if _perfil else None))
        if pruebas:
            from .config import POR_DEFECTO
            self.cfg.v = dict(POR_DEFECTO)
            self.cfg.guardar = lambda: None
        self.voz = Voz(self.cfg["voz_sapi"], muda=pruebas)
        self.voz.cfg = self.cfg                             # para la opción del historial
        if not pruebas:
            from . import voces
            voces.recoger_puente()                            # las voces que llegan tras actualizar desde una versión anterior
            voces.limpiar_antigua()                           # la carpeta de voces de las versiones anteriores ya no se usa
            voces.quitar_sin_idioma()                         # y las carpetas de historia sin idioma, de antes de la 1.7.2
            from . import i18n
            i18n.quitar_docs_sin_idioma()                     # manual.html y los demás, de antes de la 1.7.2: ahora van por idioma
            i18n.quitar_leemes_viejos()                       # LEEME_en.txt y los demás, de antes de la 1.7.3: ahora README_en.txt
        from . import audio_al
        self.mez = audio_al.crear(self.cfg, pruebas)          # el motor envolvente si se ha elegido y se puede; si no, el clásico
        self.aplicar_volumenes()
        self.pila = []
        self.teclas = set()
        self.activo = True
        self.partida = None
        self.pantalla = None
        self.fuente = None
        self.fuente_g = None
        pygame.init()
        if not pruebas:
            self.pantalla = pygame.display.set_mode((900, 420))
            pygame.display.set_caption(NOMBRE)
            if "--tras-actualizar" in sys.argv or "--actualizacion-fallida" in sys.argv:
                al_frente()                                   # lo abre el instalador: sin esto, Windows lo deja detrás
            pygame.key.set_repeat(0)
            self.fuente = pygame.font.SysFont("segoeui,arial", 26)
            self.fuente_g = pygame.font.SysFont("segoeui,arial", 38, bold=True)
            self._dibujar(tr("Cargando sonidos..."))
            self.voz.decir(tr('{NOMBRE}. Cargando, espera un momento.').format(NOMBRE=(NOMBRE)), True)
        registro.info("arranque", "Voz y mezclador listos", error_de_sonido=self.mez.error or "ninguno")
        self.info_sonidos = packs.cargar(self.mez, self.cfg)
        registro.info("arranque", "Sonidos cargados", cuantos=len(self.mez.sonidos), pack=self.cfg["pack_sonidos"] or "por defecto")
        self.radio = Radio(self.mez, rutas.carpeta_data("radio"))
        self.ambiente = MusicaAmbiente(self.mez, rutas.carpeta_data("musica"))
        self.datos = mundo.cargar_datos()
        self.mapas = mundo.crear_mapas(self.datos)
        self.mundo = self.mapas.get("puerto_bravo") or next(iter(self.mapas.values()))
        self.aplicar_adultos()
        registro.info("arranque", "Datos y mapas cargados", mapas=len(self.mapas), misiones=len(self.datos.get("misiones", [])),
                      errores_de_mods=len(self.datos["errores_mods"]))
        for e in self.datos["errores_mods"]:
            registro.aviso("mods", "Error en un mod: " + str(e))
        self.reloj = pygame.time.Clock()
        self.mando = Mando(self)
        self.t_estado = 0.0
        self.lentos = 0
        if registro.activo():
            try:
                registro.escribir_sistema(registro.datos_del_juego(self))
            except Exception:
                registro.excepcion("registro", "No se pudo escribir sistema.txt")
            registro.vigilar_estado(self.estado_registro)
        if self.mez.error and not pruebas:
            self.voz.decir(tr("Aviso: no se ha podido abrir la tarjeta de sonido. El juego funcionará sin audio."))
        for e in self.datos["errores_mods"]:
            self.voz.decir(tr("Error en un mod: ") + e)
        menus_juego.principal(self)
        from . import menus_actualizar
        menus_actualizar.al_arrancar(self)
        if self.cfg["ia_activa"] and self.cfg["ia_servicio"] in ("auto", "local") and not self.pruebas:
            from . import ia
            ia.ajustar_local(self.cfg)           # si el modo IA usa el modelo local, que vaya cargando; al salir se cierra siempre
        try:
            self.actualizar_puente_trampas()
        except Exception:
            pass

    def actualizar_puente_trampas(self):
        """Enciende o apaga el puente IPC del menú de trampas según la opción en juego."""
        from trampas import puente as _puente_trampas
        if self.cfg["permitir_trampas"] or os.environ.get("PUERTOBRAVO_TRAMPAS") == "1":
            _puente_trampas.iniciar(self)
        else:
            _puente_trampas.detener(self)

    # ------------------------------------------------------------------ audio
    def aplicar_volumenes(self):
        for k in ("maestro", "efectos", "ambiente", "musica", "interfaz", "senales"):
            self.mez.vols[k] = self.cfg["vol_" + k]
        self.voz.ajustar_sapi(self.cfg["voz_velocidad"], self.cfg["voz_tono"], self.cfg["voz_volumen"])
        self.mez.mono = bool(self.cfg["sonido_mono"])
        self.mez.atenuar = bool(self.cfg["atenuar_al_hablar"])
        self.mez.eco_activo = bool(self.cfg["eco_lugares"])
        self.voz.al_hablar = self.mez.hablando

    def son(self, nombre, **kw):
        kw.setdefault("cat", "interfaz")
        return self.mez.sonar(nombre, **kw)

    def decir(self, texto, interrumpir=False, guardar=True):
        self.voz.detalle = self.cfg["detalle_voz"]
        # En segundo plano, con la opción de serie, no habla: no interrumpe a tu lector en otra ventana. Lo dicho va igual
        # al historial, así que al volver lo repasas con Re Pág.
        hablar = getattr(self, "con_foco", True) or not self.cfg["callar_sin_foco"]
        self.voz.decir(texto, interrumpir, guardar, hablar=hablar)

    def decir_menu(self, texto):
        """Lo que se lee al abrir un menú o al moverse por él: se vuelve a oír volviendo, así que no llena el historial."""
        self.decir(texto, True, guardar=bool(self.cfg["historial_menus"]))

    def recargar_sonidos(self):
        """Vuelve a cargar los sonidos: tras elegir otro pack o cambiar el igualado de volumen."""
        self.info_sonidos = packs.cargar(self.mez, self.cfg)
        return self.info_sonidos

    def aplicar_adultos(self):
        """Muestra u oculta en todos los mapas los lugares del contenido para adultos."""
        for m in self.mapas.values():
            m.filtrar(self.cfg["adultos"])
        p = getattr(self, "partida", None)
        if p is not None:
            p.reconstruir_lugares()

    def _musica(self, dt):
        """Decide qué música de ambiente toca: ninguna si suena la radio del vehículo."""
        deseada = None
        if self.cfg["musica_ambiente"]:
            p = self.partida
            if p is None or p not in self.pila:
                deseada = "menu"
            elif not self.radio.sonando_ahora():                # con la radio puesta, en el vehículo, por los auriculares o en un local, calla
                deseada = p.estado_musica()
        self.ambiente.actualizar(dt, deseada, self.cfg["vol_ambiente_musical"] * 0.7)
        self.radio.actualizar(dt)

    def vibrar(self, grave, agudo, ms):
        self.mando.vibrar(grave, agudo, ms)

    # ------------------------------------------------------------------- pila
    def estado_registro(self):
        """Foto del estado para el registro: sin nada personal."""
        cima = self.pila[-1] if self.pila else None
        d = {"pantalla": type(cima).__name__ if cima is not None else "ninguna", "pila": len(self.pila), "canales_de_sonido": len(self.mez.canales)}
        p = self.partida
        if p is not None:
            d.update(p.estado_registro())
        else:
            d["partida"] = "no"
        return d

    def abrir(self, pantalla):
        registro.pantalla("abre", pantalla)
        self.pila.append(pantalla)
        self.teclas.clear()
        pantalla.al_entrar()

    def cerrar(self, pantalla=None):
        if not self.pila:
            return
        if pantalla is None:
            pantalla = self.pila[-1]
        if pantalla not in self.pila:
            return
        era_cima = self.pila[-1] is pantalla
        registro.pantalla("cierra", pantalla)
        self.pila.remove(pantalla)
        self.teclas.clear()
        cima = self.pila[-1] if self.pila else None
        despues = getattr(pantalla, "cerrado_al_final", False)
        if hasattr(pantalla, "cerrado") and not despues:
            pantalla.cerrado()
        if era_cima and self.pila and self.pila[-1] is cima:
            cima.al_entrar()
        if despues:
            pantalla.cerrado()             # lo que diga la respuesta se oye después del menú, no tapado por él

    def empezar_partida(self, guardado, personaje=None):
        from .partida import Partida, PartidaMasNueva, migrar
        if guardado:
            try:
                guardado = migrar(guardado)            # las partidas de versiones anteriores se convierten al cargar
            except PartidaMasNueva as e:
                self.son("error")
                self.decir(str(e), True)
                return
        if self.partida:
            self.partida.silenciar()
        self.pila.clear()
        registro.info("partida", "Empieza una partida", cargada=bool(guardado), personaje=(personaje or {}).get("id", "") if isinstance(personaje, dict) else str(personaje or ""))
        if self.partida:
            self.partida.sv_salir()
        self.partida = Partida(self, guardado, personaje)
        from . import vozgen
        vozgen.al_jugar(self.partida)                    # con un personaje propio, se le van generando las voces que le nombran
        self.mez.mundo_pausado = False
        self.pila.append(self.partida)
        enlace, self.enlace = getattr(self, "enlace", None), None
        if enlace is not None:                               # la partida es de un servidor en línea
            self.partida.sv_entrar(enlace)
        if guardado:
            self.son("guardado")
            p = self.partida
            self.decir(tr('Partida cargada. {describir}. Son las {hora_txt}. {objetivo_txt}').format(describir=(p.mundo.describir(p.j.x, p.j.y)), hora_txt=(p.hora_txt()), objetivo_txt=(p.objetivo_txt())), True)
        self.partida.al_entrar()

    def volver_al_menu(self):
        registro.info("partida", "Vuelta al menú principal")
        from . import vozgen
        vozgen.generador.detener()
        if self.partida:
            self.partida.sv_salir()
            self.partida.silenciar()
        self.partida = None
        self.pila.clear()
        self.cfg.guardar()
        menus_juego.principal(self)

    def salir(self):
        self.activo = False

    # ------------------------------------------------------------------ bucle
    def _jugando(self):
        return bool(self.pila) and type(self.pila[-1]).__name__ == "Partida"

    def _teclas_propias(self):
        """¿Se aplican aquí las teclas cambiadas? Jugando, siempre. En menús y diálogos, si el jugador lo ha pedido.
        Nunca al escribir texto ni al elegir una tecla nueva."""
        if self._jugando():
            return True
        if not self.cfg["teclas_menus"] or not self.pila:
            return False
        return type(self.pila[-1]).__name__ not in ("EntradaTexto", "Captura")

    def evento_tecla(self, ev):
        if self.cfg["teclas"] and not getattr(ev, "mando", False) and self._teclas_propias():      # lo del mando ya viene como función, no como tecla física
            # cada tecla hace la función que el jugador le haya puesto
            from . import teclado
            k = teclado.traducir(self.cfg, ev.key)
            mod = getattr(ev, "mod", 0) or 0
            mod2 = teclado.modificadores(self.cfg, mod, self.teclas | {k})
            if k != ev.key or mod2 != mod:
                ev = EventoFalso(k, mod2, getattr(ev, "unicode", ""))
        self.teclas.add(ev.key)
        if registro.activo():
            from .menus import EntradaTexto
            if ev.key == pygame.K_F12 and not (self.pila and isinstance(self.pila[-1], EntradaTexto)):
                registro.marca()
                self.son("guardado")
                self.decir(tr("Marca añadida al registro de la sesión."), True)
                return
            en_texto = bool(self.pila) and isinstance(self.pila[-1], EntradaTexto)
            try:
                nombre = pygame.key.name(ev.key) or str(ev.key)
            except Exception:
                nombre = str(ev.key)
            mod = getattr(ev, "mod", 0) or 0
            prefijo = ("ctrl+" if mod & pygame.KMOD_CTRL else "") + ("mayús+" if mod & pygame.KMOD_SHIFT else "") + ("alt+" if mod & pygame.KMOD_ALT else "")
            registro.tecla(prefijo + nombre.replace(" ", "_"), en_texto)
        if self.pila:
            self.pila[-1].tecla(ev)

    def evento_texto(self, texto):
        """Lo que escribe el teclado como texto. Con teclas muertas (los acentos), con algunas distribuciones de teclado o
        con un método de entrada, la letra llega solo así, y no con la pulsación: antes el cuadro de texto se quedaba vacío."""
        if self.pila and hasattr(self.pila[-1], "texto_tecleado"):
            self.pila[-1].texto_tecleado(texto)

    def paso(self, dt):
        if registro.activo():
            if dt > 0.25:
                self.lentos += 1
                if self.lentos <= 40:
                    registro.aviso("rendimiento", f"Fotograma lento: {dt * 1000:.0f} ms")
            self.t_estado += dt
            if self.t_estado >= registro.CADA_ESTADO:
                self.t_estado = 0.0
                registro.estado()
        for tarea in list(getattr(self, "tareas_fondo", ())):    # descargas que siguen mientras juegas
            if tarea.paso_fondo():
                self.tareas_fondo.remove(tarea)
        prueba = getattr(self, "voz_prueba", None)
        if prueba is not None:                           # una prueba de voz pedida desde un menú, ya generada
            self.voz_prueba = None
            from . import voces
            if not prueba or voces.sonar(self, prueba) is None:
                self.son("error")
                self.decir(tr("No se ha podido generar la prueba."), True)
        if self.pila:
            cima = self.pila[-1]
            self.mez.mundo_pausado = getattr(cima, "pausa_mundo", True)
            self.mando.actualizar(dt)
            cima.actualizar(dt)
            if self.partida is not None:
                self.partida.red_paso(dt)          # los amigos conectados siguen oyéndote aunque tengas un menú abierto
            self._musica(dt)
            if getattr(self, "act_aviso", None) is not None:
                from . import menus_actualizar
                menus_actualizar.paso(self)
        self.mez.actualizar()
        if getattr(self, "_puente_trampas", None) is not None:
            self._puente_trampas.atender()

    def inyectar(self, key, mod=0, unicode="", soltar=True):
        """Simula una pulsación (pruebas automáticas)."""
        self.evento_tecla(EventoFalso(key, mod, unicode))
        if soltar:
            self.teclas.discard(key)
            if self.cfg["teclas"]:
                from . import teclado
                self.teclas.discard(teclado.traducir(self.cfg, key))

    def _dibujar(self, forzar=None):
        if not self.pantalla:
            return
        self.pantalla.fill((0, 0, 0))
        self.pantalla.blit(self.fuente_g.render(NOMBRE, True, (255, 220, 0)), (20, 14))
        texto = forzar or self.voz.ultimo()
        y = 80
        palabras = texto.split(" ")
        linea = ""
        for w in palabras:
            if self.fuente.size(linea + " " + w)[0] > 860:
                self.pantalla.blit(self.fuente.render(linea, True, (255, 255, 255)), (20, y))
                y += 32
                linea = w
                if y > 380:
                    break
            else:
                linea = (linea + " " + w).strip()
        if linea and y <= 380:
            self.pantalla.blit(self.fuente.render(linea, True, (255, 255, 255)), (20, y))
        pygame.display.flip()

    def bucle(self):
        ultimo = None
        try:
            while self.activo:
                dt = self.reloj.tick(60) / 1000.0
                for ev in pygame.event.get():
                    if self.mando.evento(ev):
                        continue
                    if ev.type == pygame.QUIT:
                        self.activo = False
                    elif ev.type == pygame.KEYDOWN:
                        self.evento_tecla(ev)
                    elif ev.type == pygame.TEXTINPUT:
                        self.evento_texto(ev.text)
                    elif ev.type == pygame.KEYUP:
                        self.teclas.discard(ev.key)
                        if self.cfg["teclas"]:
                            from . import teclado
                            self.teclas.discard(teclado.traducir(self.cfg, ev.key))
                    elif ev.type in (pygame.WINDOWFOCUSLOST,):
                        self.teclas.clear()
                        self.con_foco = False
                    elif ev.type in (pygame.WINDOWFOCUSGAINED,):
                        self.con_foco = True
                self.paso(dt)
                if self.voz.ultimo() != ultimo:
                    ultimo = self.voz.ultimo()
                    self._dibujar()
        except Exception:
            self._registrar_error()
        finally:
            self.cerrar_todo()

    def _registrar_error(self):
        registro.excepcion("juego", "El juego se ha cerrado por un error inesperado")
        if self.partida and not self.partida.mision:
            try:
                menus_juego.guardar_por_si_acaso(self.partida)      # a la ranura de la partida, con su copia anterior
            except Exception:
                pass
        sesion = os.path.basename(registro.carpeta_sesion() or "")
        self.voz.decir(tr("Ha ocurrido un error inesperado y el juego debe cerrarse. Tu partida se ha guardado automáticamente. "
                       "Para ayudar a arreglarlo, comprime la carpeta de esta sesión, que está dentro de data, logs") + (tr(', y se llama {sesion}').format(sesion=(sesion)) if sesion else "") +
                       tr(", y envíala. No contiene datos personales."), True)
        if not self.pruebas:
            pygame.time.wait(9000)

    def cerrar_todo(self):
        try:
            if getattr(self, "_puente_trampas", None) is not None:
                self._puente_trampas.detener()
                self._puente_trampas = None
        except Exception:
            pass
        try:
            if self.partida:
                self.partida.sv_salir()                  # en un servidor: guardar y despedirse
        except Exception:
            pass
        registro.estado()
        registro.vigilar_estado(None)
        try:
            from . import vozgen
            vozgen.parar_prueba()                            # si se estaba probando el motor de voz en un proceso aparte, no se queda abierto
        except Exception:
            pass
        self.cfg.guardar()
        for cargador in (self.radio, self.ambiente):       # si aún están cargando música, se paran antes de cerrar
            try:
                cargador.cancelar()
            except Exception:
                pass
        try:
            from . import ia
            ia.parar_local()
        except Exception:
            pass
        self.mez.cerrar()
        pygame.quit()
        if not self.pruebas:
            registro.cerrar()
