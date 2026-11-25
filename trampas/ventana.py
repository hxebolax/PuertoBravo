"""Interfaz gráfica accesible (wxPython) del Menú de Trampas para Puerto Bravo."""
from __future__ import annotations

import json
import wx

from juego.i18n import tr

from . import NOMBRE, descubrir_instancias
from .protocolo import ClienteTrampas, ErrorPuente
from .puente import parsear_valor_inspector, validar_clave_inspector

_IDS_VEH_IA = ("None", "aparcado", "trafico", "huida", "policia", "barco")
_IDS_NPC_MODO = ("enemigo", "pandillero", "policia", "civil", "aliado", "perro")
_IDS_NPC_ESTADO = ("pasea", "quieto", "huye", "ataca", "sigue")

try:
    from editor.accesibilidad import voz as _voz
    from editor.accesibilidad.ayuda import asegurar_ayudas, habilitar_ayuda_contextual
    from editor.accesibilidad.dialogos import mostrar_error
    from editor.accesibilidad.idioma import fijar_idioma_espanol
    from editor.accesibilidad.nombres import crear_campo
except Exception:  # pragma: no cover - respaldo ante cambios futuros en editor.accesibilidad
    class _VozFallback:
        NAVEGACION = "navegacion"
        AVISOS = "avisos"

        @staticmethod
        def hablar(texto: str, interrumpir: bool = True, canal: str = "navegacion") -> None:
            pass

    _voz = _VozFallback()

    def habilitar_ayuda_contextual(ventana: wx.Window) -> None:
        pass

    def asegurar_ayudas(ventana: wx.Window) -> None:
        pass

    def fijar_idioma_espanol(*args, **kwargs):
        return None

    def mostrar_error(padre: wx.Window | None, mensaje: str, titulo: str = "Error") -> None:
        wx.MessageBox(mensaje, titulo, wx.OK | wx.ICON_ERROR, parent=padre)

    def crear_campo(padre, etiqueta, fabrica, *args, ayuda="", sizer=None, horizontal=False, expandir=True, **kwargs):
        lbl = wx.StaticText(padre, label=etiqueta)
        ctrl = fabrica(padre, *args, **kwargs)
        if ayuda:
            ctrl.SetHelpText(ayuda)
        if sizer is not None:
            if horizontal:
                fila = wx.BoxSizer(wx.HORIZONTAL)
                fila.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
                fila.Add(ctrl, 1 if expandir else 0, wx.EXPAND if expandir else 0)
                sizer.Add(fila, 0, wx.EXPAND | wx.ALL, 4)
            else:
                sizer.Add(lbl, 0, wx.LEFT | wx.RIGHT | wx.TOP, 4)
                sizer.Add(ctrl, 0, (wx.EXPAND if expandir else 0) | wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)
        return lbl, ctrl


def _hablar(texto: str) -> None:
    try:
        _voz.hablar(texto, interrumpir=True, canal=_voz.AVISOS)
    except Exception:
        pass


def _tiene_foco(ctrl: wx.Window | None) -> bool:
    """True si ``ctrl`` o alguno de sus subcontroles internos (p. ej. SpinCtrl) tiene el foco."""
    if ctrl is None:
        return False
    foco = wx.Window.FindFocus()
    while foco is not None:
        if foco is ctrl:
            return True
        foco = foco.GetParent()
    return False


def _campo_grid(padre, grid, etiqueta, fabrica, *args, ayuda="", **kwargs):
    """Crea etiqueta + control dentro de un FlexGridSizer respetando el orden Z accesible."""
    lbl = wx.StaticText(padre, label=etiqueta)
    kwargs.setdefault("name", etiqueta.replace("&", "").strip().rstrip(":"))
    ctrl = fabrica(padre, *args, **kwargs)
    if ayuda:
        ctrl.SetHelpText(ayuda)
    grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
    grid.Add(ctrl, 1, wx.EXPAND)
    return ctrl


class VentanaTrampas(wx.Frame):
    """Ventana principal del menú de trampas conectado en tiempo real a Puerto Bravo."""

    def __init__(self, padre=None, auto_conectar: bool = True, intervalo_ms: int = 2000) -> None:
        titulo_ventana = tr("Menú de Trampas — Puerto Bravo")
        super().__init__(padre, title=titulo_ventana, size=(960, 760), name=titulo_ventana)
        self.cliente: ClienteTrampas | None = None
        self.instancias: list[dict] = []
        self.catalogos: dict = {}
        self.estado: dict = {}
        self._vehiculos_vivos: list[dict] = []
        self._personas_vistas: list[dict] = []
        self._inspector_campos: dict = {}
        self._valores_juego: dict = {}
        self._ultimo_resumen: str = ""
        self._ultimas_claves_veh: list[str] = []
        self._ultimas_claves_npc: list[str] = []
        self._ultimo_error_puente: str = ""

        panel = wx.Panel(self)
        raiz = wx.BoxSizer(wx.VERTICAL)

        # Barra superior de conexión
        barra = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_instancia = crear_campo(
            panel, tr("&1 Instancia del juego:"), wx.Choice, choices=[tr("(ninguna detectada)")],
            ayuda=tr("Elige qué proceso de Puerto Bravo quieres controlar."),
            sizer=barra, horizontal=True,
        )
        self.btn_conectar = wx.Button(panel, label=tr("&2 Conectar"))
        self.btn_conectar.SetHelpText(tr("Busca y conecta con el proceso de Puerto Bravo seleccionado."))
        self.btn_refrescar = wx.Button(panel, label=tr("&3 Actualizar (F5)"))
        self.btn_refrescar.SetHelpText(tr("Recarga y sincroniza todos los valores actuales desde la partida."))
        barra.Add(self.btn_conectar, 0, wx.ALL, 4)
        barra.Add(self.btn_refrescar, 0, wx.ALL, 4)
        raiz.Add(barra, 0, wx.EXPAND | wx.ALL, 4)

        _, self.txt_conexion = crear_campo(
            panel, tr("&4 Estado de conexión:"), wx.TextCtrl, style=wx.TE_READONLY,
            ayuda=tr("Indica si hay conexión con el juego y si hay una partida en solitario activa."),
            sizer=raiz, horizontal=True,
        )
        self.txt_conexion.SetValue(tr("Sin conectar. Pulsa Conectar cuando Puerto Bravo esté en modo un jugador."))

        self.libro = wx.Notebook(panel, name=tr("Categorías de trampas"))
        self.libro.SetHelpText(tr("Categorías principales de trampas. Cambia con Control+Tab o las flechas."))
        self._construir_tab_jugador()
        self._construir_tab_inventario()
        self._construir_tab_vehiculos()
        self._construir_tab_npcs()
        self._construir_tab_policia()
        self._construir_tab_eventos()
        self._construir_tab_mundo()
        self._construir_tab_inspector()
        raiz.Add(self.libro, 1, wx.EXPAND | wx.ALL, 4)

        panel.SetSizer(raiz)
        self.CreateStatusBar()
        self.SetStatusText(tr("Listo. Ctrl+H lee la ayuda; F5 sincroniza todos los campos con el juego."))

        self.btn_conectar.Bind(wx.EVT_BUTTON, lambda e: self._alternar_conexion())
        self.btn_refrescar.Bind(wx.EVT_BUTTON, lambda e: self.refrescar_todo(anunciar=True))
        self.Bind(wx.EVT_CHAR_HOOK, self._tecla_global)
        self.Bind(wx.EVT_CLOSE, self._al_cerrar)

        habilitar_ayuda_contextual(self)
        asegurar_ayudas(self)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self._al_timer, self.timer)
        if intervalo_ms > 0:
            self.timer.Start(intervalo_ms)

        self.Centre()
        if auto_conectar:
            wx.CallAfter(self._auto_conectar_silencioso)

    # ------------------------------------------------------------------ sincronización
    def _sinc_control(self, clave: str, ctrl: wx.Window, valor, forzar: bool = False) -> None:
        """Sincroniza un control con el valor real del juego sin pisar un campo en edición activa."""
        previo = self._valores_juego.get(clave, "__SIN_VALOR__")
        self._valores_juego[clave] = valor
        if not forzar and (valor == previo or _tiene_foco(ctrl)):
            return
        if isinstance(ctrl, wx.CheckBox):
            val_b = bool(valor)
            if ctrl.GetValue() != val_b:
                ctrl.SetValue(val_b)
        elif isinstance(ctrl, wx.SpinCtrl):
            val_i = max(ctrl.GetMin(), min(ctrl.GetMax(), int(round(float(valor)))))
            if ctrl.GetValue() != val_i:
                ctrl.SetValue(val_i)
        elif isinstance(ctrl, wx.TextCtrl):
            val_s = str(valor if valor is not None else "")
            if ctrl.GetValue() != val_s:
                ctrl.SetValue(val_s)
        elif isinstance(ctrl, wx.Choice):
            val_s = str(valor)
            pos = ctrl.FindString(val_s)
            if pos != wx.NOT_FOUND and ctrl.GetSelection() != pos:
                ctrl.SetSelection(pos)

    def _sincronizar_todo(self, forzar: bool = False) -> None:
        est = self.estado or {}
        if not est.get("en_partida"):
            return
        j = est.get("jugador", {})
        t = est.get("tiempo", {})
        cfg = est.get("cfg", {})

        # Jugador -> Combate
        self._sinc_control("salud", self.sp_salud, j.get("salud", 100), forzar)
        self._sinc_control("salud_max", self.sp_salud_max, j.get("salud_max", 100), forzar)
        self._sinc_control("blindaje", self.sp_blindaje, j.get("blindaje", 0), forzar)
        self._sinc_control("foco", self.sp_foco, j.get("foco", 100), forzar)
        self._sinc_control("cfg.invulnerable", self.chk_invulnerable, cfg.get("invulnerable", False), forzar)

        # Jugador -> Economía y Progreso
        self._sinc_control("dinero", self.sp_dinero, j.get("dinero", 0), forzar)
        self._sinc_control("banco", self.sp_banco, j.get("banco", 0), forzar)
        self._sinc_control("animo", self.sp_animo, j.get("animo", 55), forzar)
        self._sinc_control("ciudadania", self.sp_ciudadania, j.get("ciudadania", 20), forzar)
        self._sinc_control("reputacion", self.sp_reputacion, j.get("reputacion", 0), forzar)
        self._sinc_control("carne_puntos", self.sp_carne, j.get("carne_puntos", 12), forzar)
        self._sinc_control("guardaespaldas", self.sp_guardaespaldas, j.get("guardaespaldas", 0), forzar)

        # Jugador -> Necesidades y Habilidades
        self._sinc_control("hambre", self.sp_hambre, j.get("hambre", 0), forzar)
        self._sinc_control("sed", self.sp_sed, j.get("sed", 0), forzar)
        self._sinc_control("sueno", self.sp_sueno, j.get("sueno", 0), forzar)
        self._sinc_control("suciedad", self.sp_suciedad, j.get("suciedad", 0), forzar)
        self._sinc_control("cocina_practica", self.sp_cocina, j.get("cocina_practica", 0), forzar)
        self._sincronizar_habilidad_actual(forzar)

        # Jugador -> Banda y Perro
        self._sinc_control("banda_nombre", self.txt_banda_nombre, j.get("banda_nombre", ""), forzar)
        self._sinc_control("alias", self.txt_alias, j.get("alias", ""), forzar)
        self._sinc_control("banda", self.sp_banda_num, j.get("banda", 0), forzar)
        self._sinc_control("perro", self.txt_perro_nombre, j.get("perro", ""), forzar)
        self._sinc_control("perro_hambre", self.sp_perro_hambre, j.get("perro_hambre", 0), forzar)
        self._sinc_control("perro_confianza", self.sp_perro_confianza, j.get("perro_confianza", 100), forzar)

        # Inventario
        self._sincronizar_arma_actual(forzar)
        self._sincronizar_objeto_actual(forzar)
        self._sinc_control("mochila_grande", self.chk_mochila_grande, j.get("mochila_grande", False), forzar)
        self._sincronizar_sustancia_actual(forzar)

        # Policía y Bandas
        self._sinc_control("estrellas", self.sp_estrellas, j.get("estrellas", 0), forzar)
        self._sinc_control("cfg.sin_policia", self.chk_sin_policia, cfg.get("sin_policia", False), forzar)
        self._sinc_control("cfg.helicoptero_policia", self.chk_pol_heli, cfg.get("helicoptero_policia", False), forzar)
        self._sincronizar_rep_banda_actual(forzar)

        # Mundo y Opciones
        reloj = float(t.get("reloj", 720.0))
        hora_actual = int(reloj // 60) % 24
        self._sinc_control("hora", self.sp_hora, hora_actual, forzar)
        self._sinc_control("dia", self.sp_dia, t.get("dia", 1), forzar)
        self._sinc_control("lluvia", self.chk_lluvia, t.get("lluvia", False), forzar)
        dia_id = (t.get("dia_azar") or {}).get("id")
        if dia_id and dia_id in getattr(self, "_ids_dias", []):
            idx_d = self._ids_dias.index(dia_id)
            if forzar or (self._valores_juego.get("dia_azar") != dia_id and not _tiene_foco(self.sel_dia_azar)):
                self.sel_dia_azar.SetSelection(idx_d)
            self._valores_juego["dia_azar"] = dia_id
        for k, chk in self._chks_cfg.items():
            if k in cfg:
                self._sinc_control(f"cfg.{k}", chk, cfg[k], forzar)

    # ------------------------------------------------------------------ pestañas
    def _construir_tab_jugador(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Jugador"))
        s = wx.BoxSizer(wx.VERTICAL)

        _, self.txt_resumen_jug = crear_campo(
            pag, tr("&5 Resumen de partida:"), wx.TextCtrl,
            style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 86),
            ayuda=tr("Resumen vivo de tu partida. Recórrelo con las flechas."),
            sizer=s,
        )

        sub = wx.Notebook(pag, name=tr("Subcategorías de Jugador"))
        sub.SetHelpText(tr("Subcategorías del jugador: Combate, Economía, Necesidades y Banda."))

        # 1.1 Combate y Estado Vital
        p_comb = wx.Panel(sub, name=tr("Combate y Estado"))
        sc = wx.BoxSizer(wx.VERTICAL)
        gc = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        gc.AddGrowableCol(1, 1)
        gc.AddGrowableCol(3, 1)
        self.sp_salud = _campo_grid(p_comb, gc, tr("&Salud:"), wx.SpinCtrl, min=1, max=9999, initial=100, ayuda=tr("Salud actual."))
        self.sp_salud_max = _campo_grid(p_comb, gc, tr("Salud má&xima:"), wx.SpinCtrl, min=10, max=9999, initial=100, ayuda=tr("Salud máxima."))
        self.sp_blindaje = _campo_grid(p_comb, gc, tr("&Blindaje:"), wx.SpinCtrl, min=0, max=1000, initial=0, ayuda=tr("Puntos de chaleco antibalas."))
        self.sp_foco = _campo_grid(p_comb, gc, tr("Con&centración (foco):"), wx.SpinCtrl, min=0, max=100, initial=100, ayuda=tr("Medidor del tiempo lento."))
        sc.Add(gc, 0, wx.EXPAND | wx.ALL, 8)
        self.chk_invulnerable = wx.CheckBox(p_comb, label=tr("Modo &invulnerable (sin daño)"))
        sc.Add(self.chk_invulnerable, 0, wx.LEFT | wx.BOTTOM, 8)
        bc = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_aplicar_comb = wx.Button(p_comb, label=tr("&Aplicar combate"))
        self.btn_curar = wx.Button(p_comb, label=tr("Cu&rar y restaurar todo"))
        bc.Add(self.btn_aplicar_comb, 0, wx.ALL, 4)
        bc.Add(self.btn_curar, 0, wx.ALL, 4)
        sc.Add(bc, 0, wx.LEFT | wx.RIGHT, 4)
        p_comb.SetSizer(sc)
        sub.AddPage(p_comb, tr("Combate y Estado"))

        # 1.2 Economía y Progreso
        p_eco = wx.Panel(sub, name=tr("Economía y Progreso"))
        se = wx.BoxSizer(wx.VERTICAL)
        ge = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        ge.AddGrowableCol(1, 1)
        ge.AddGrowableCol(3, 1)
        self.sp_dinero = _campo_grid(p_eco, ge, tr("&Dinero en mano:"), wx.SpinCtrl, min=0, max=99999999, initial=50, ayuda=tr("Efectivo actual."))
        self.sp_banco = _campo_grid(p_eco, ge, tr("Dinero en &banco:"), wx.SpinCtrl, min=0, max=99999999, initial=0, ayuda=tr("Saldo bancario actual."))
        self.sp_animo = _campo_grid(p_eco, ge, tr("Á&nimo (0-100):"), wx.SpinCtrl, min=0, max=100, initial=55)
        self.sp_ciudadania = _campo_grid(p_eco, ge, tr("&Prestigio vecinal (0-100):"), wx.SpinCtrl, min=0, max=100, initial=20)
        self.sp_reputacion = _campo_grid(p_eco, ge, tr("&Fama callejera (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0)
        self.sp_carne = _campo_grid(p_eco, ge, tr("Puntos &carné (0-12):"), wx.SpinCtrl, min=0, max=12, initial=12)
        self.sp_guardaespaldas = _campo_grid(p_eco, ge, tr("&Guardaespaldas:"), wx.SpinCtrl, min=0, max=20, initial=0)
        se.Add(ge, 0, wx.EXPAND | wx.ALL, 8)
        be = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_aplicar_eco = wx.Button(p_eco, label=tr("&Aplicar economía y progreso"))
        self.btn_dinero5k = wx.Button(p_eco, label=tr("+5.000 &euros"))
        self.btn_dinero50k = wx.Button(p_eco, label=tr("+50.000 e&uros"))
        self.btn_antecedentes = wx.Button(p_eco, label=tr("Borrar an&tecedentes"))
        self.btn_propiedades = wx.Button(p_eco, label=tr("Todas las p&ropiedades"))
        for b in (self.btn_aplicar_eco, self.btn_dinero5k, self.btn_dinero50k, self.btn_antecedentes, self.btn_propiedades):
            be.Add(b, 0, wx.ALL, 4)
        se.Add(be, 0, wx.LEFT | wx.RIGHT, 4)
        p_eco.SetSizer(se)
        sub.AddPage(p_eco, tr("Economía y Progreso"))

        # 1.3 Necesidades y Habilidades
        p_nh = wx.Panel(sub, name=tr("Necesidades y Habilidades"))
        snh = wx.BoxSizer(wx.VERTICAL)
        box_nec = wx.StaticBoxSizer(wx.VERTICAL, p_nh, tr("Necesidades (vida realista)"))
        np = box_nec.GetStaticBox()
        gn = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        gn.AddGrowableCol(1, 1)
        gn.AddGrowableCol(3, 1)
        self.sp_hambre = _campo_grid(np, gn, tr("Ha&mbre (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0)
        self.sp_sed = _campo_grid(np, gn, tr("&Sed (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0)
        self.sp_sueno = _campo_grid(np, gn, tr("S&ueño (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0)
        self.sp_suciedad = _campo_grid(np, gn, tr("Suc&iedad (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0)
        box_nec.Add(gn, 0, wx.EXPAND | wx.ALL, 4)
        bn = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_aplicar_nec = wx.Button(np, label=tr("&Aplicar necesidades"))
        self.btn_necesidades = wx.Button(np, label=tr("Llenar necesida&des (0)"))
        bn.Add(self.btn_aplicar_nec, 0, wx.ALL, 4)
        bn.Add(self.btn_necesidades, 0, wx.ALL, 4)
        box_nec.Add(bn, 0)
        snh.Add(box_nec, 0, wx.EXPAND | wx.ALL, 4)

        box_hab = wx.StaticBoxSizer(wx.VERTICAL, p_nh, tr("Habilidades y cocina"))
        hp = box_hab.GetStaticBox()
        fh = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_hab = crear_campo(
            hp, tr("&Habilidad:"), wx.Choice, choices=[tr("Conducción"), tr("Puntería"), tr("Resistencia"), tr("Pesca")],
            sizer=fh, horizontal=True,
        )
        _, self.sp_hab_nivel = crear_campo(
            hp, tr("Nive&l (0-10):"), wx.SpinCtrl, min=0, max=10, initial=0,
            sizer=fh, horizontal=True, expandir=False,
        )
        self.btn_hab = wx.Button(hp, label=tr("&Fijar habilidad"))
        fh.Add(self.btn_hab, 0, wx.ALL, 4)
        box_hab.Add(fh, 0, wx.EXPAND | wx.ALL, 2)

        fc = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sp_cocina = crear_campo(
            hp, tr("&Cocina práctica (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0,
            sizer=fc, horizontal=True, expandir=False,
        )
        self.btn_cocina = wx.Button(hp, label=tr("Fijar c&ocina"))
        self.btn_max_habs = wx.Button(hp, label=tr("Má&x. todas las habilidades"))
        fc.Add(self.btn_cocina, 0, wx.ALL, 4)
        fc.Add(self.btn_max_habs, 0, wx.ALL, 4)
        box_hab.Add(fc, 0, wx.EXPAND | wx.ALL, 2)
        snh.Add(box_hab, 0, wx.EXPAND | wx.ALL, 4)
        p_nh.SetSizer(snh)
        sub.AddPage(p_nh, tr("Necesidades y Habilidades"))

        # 1.4 Banda y Perro
        p_bp = wx.Panel(sub, name=tr("Banda y Perro"))
        sbp = wx.BoxSizer(wx.VERTICAL)
        box_ban = wx.StaticBoxSizer(wx.VERTICAL, p_bp, tr("Banda propia y territorios"))
        bp = box_ban.GetStaticBox()
        gb = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        gb.AddGrowableCol(1, 1)
        gb.AddGrowableCol(3, 1)
        self.txt_banda_nombre = _campo_grid(bp, gb, tr("&Nombre banda:"), wx.TextCtrl)
        self.txt_alias = _campo_grid(bp, gb, tr("Alias de &jefe:"), wx.TextCtrl)
        self.sp_banda_num = _campo_grid(bp, gb, tr("&Miembros:"), wx.SpinCtrl, min=0, max=50, initial=0)
        box_ban.Add(gb, 0, wx.EXPAND | wx.ALL, 4)
        bb = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_aplicar_banda = wx.Button(bp, label=tr("&Aplicar banda"))
        self.btn_banda = wx.Button(bp, label=tr("&Llamar banda"))
        self.btn_conq_barrio = wx.Button(bp, label=tr("&Conquistar barrio actual"))
        self.btn_conq_todos = wx.Button(bp, label=tr("Conquistar &todos los barrios"))
        for b in (self.btn_aplicar_banda, self.btn_banda, self.btn_conq_barrio, self.btn_conq_todos):
            bb.Add(b, 0, wx.ALL, 4)
        box_ban.Add(bb, 0, wx.EXPAND)
        sbp.Add(box_ban, 0, wx.EXPAND | wx.ALL, 4)

        box_per = wx.StaticBoxSizer(wx.VERTICAL, p_bp, tr("Perro compañero"))
        pp = box_per.GetStaticBox()
        gpe = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        gpe.AddGrowableCol(1, 1)
        gpe.AddGrowableCol(3, 1)
        self.txt_perro_nombre = _campo_grid(pp, gpe, tr("Nombre &perro:"), wx.TextCtrl)
        self.sp_perro_hambre = _campo_grid(pp, gpe, tr("&Hambre perro (0-100):"), wx.SpinCtrl, min=0, max=100, initial=0)
        self.sp_perro_confianza = _campo_grid(pp, gpe, tr("Con&fianza perro (0-100):"), wx.SpinCtrl, min=0, max=100, initial=100)
        box_per.Add(gpe, 0, wx.EXPAND | wx.ALL, 4)
        bpe = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_aplicar_perro = wx.Button(pp, label=tr("Apl&icar perro"))
        self.btn_perro = wx.Button(pp, label=tr("Ad&optar / traer perro"))
        bpe.Add(self.btn_aplicar_perro, 0, wx.ALL, 4)
        bpe.Add(self.btn_perro, 0, wx.ALL, 4)
        box_per.Add(bpe, 0)
        sbp.Add(box_per, 0, wx.EXPAND | wx.ALL, 4)
        p_bp.SetSizer(sbp)
        sub.AddPage(p_bp, tr("Banda y Perro"))

        s.Add(sub, 1, wx.EXPAND | wx.ALL, 4)

        # Eventos Jugador
        self.chk_invulnerable.Bind(wx.EVT_CHECKBOX, lambda e: self._toggle_cfg("invulnerable", self.chk_invulnerable.GetValue()))
        self.btn_aplicar_comb.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar(
            "jugador.set",
            {
                "salud": self.sp_salud.GetValue(),
                "salud_max": self.sp_salud_max.GetValue(),
                "blindaje": self.sp_blindaje.GetValue(),
                "foco": self.sp_foco.GetValue(),
            },
            tr("Estadísticas de combate aplicadas."),
        ))
        self.btn_curar.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("curar_todo", tr("Salud, blindaje y foco restaurados.")))
        self.btn_aplicar_eco.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar(
            "jugador.set",
            {
                "dinero": self.sp_dinero.GetValue(),
                "banco": self.sp_banco.GetValue(),
                "animo": self.sp_animo.GetValue(),
                "ciudadania": self.sp_ciudadania.GetValue(),
                "reputacion": self.sp_reputacion.GetValue(),
                "carne_puntos": self.sp_carne.GetValue(),
                "guardaespaldas": self.sp_guardaespaldas.GetValue(),
            },
            tr("Economía y progreso actualizados."),
        ))
        self.btn_dinero5k.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("jugador.set", {"dinero_delta": 5000}, tr("Añadidos 5000 euros en mano.")))
        self.btn_dinero50k.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("jugador.set", {"dinero_delta": 50000}, tr("Añadidos 50000 euros en mano.")))
        self.btn_antecedentes.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("borrar_antecedentes", tr("Antecedentes, sospechas y dinero negro limpiados.")))
        self.btn_propiedades.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("desbloquear_propiedades", tr("Todas las casas y negocios añadidos a tus propiedades.")))
        self.btn_aplicar_nec.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar(
            "jugador.set",
            {
                "hambre": self.sp_hambre.GetValue(),
                "sed": self.sp_sed.GetValue(),
                "sueno": self.sp_sueno.GetValue(),
                "suciedad": self.sp_suciedad.GetValue(),
            },
            tr("Necesidades actualizadas."),
        ))
        self.btn_necesidades.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("llenar_necesidades", tr("Necesidades rellenadas al máximo.")))
        self.sel_hab.Bind(wx.EVT_CHOICE, lambda e: self._sincronizar_habilidad_actual(True))
        self.btn_hab.Bind(wx.EVT_BUTTON, lambda e: self._fijar_habilidad())
        self.btn_cocina.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("jugador.set", {"cocina_practica": self.sp_cocina.GetValue()}, tr("Cocina práctica actualizada.")))
        self.btn_max_habs.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("max_habilidades", tr("Todas las habilidades al nivel máximo.")))
        self.btn_aplicar_banda.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar(
            "jugador.set",
            {
                "banda_nombre": self.txt_banda_nombre.GetValue().strip(),
                "alias": self.txt_alias.GetValue().strip(),
                "banda": self.sp_banda_num.GetValue(),
            },
            tr("Datos de tu banda actualizados."),
        ))
        self.btn_banda.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("llamar_banda", tr("Tu banda acude a tu lado.")))
        self.btn_conq_barrio.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("conquistar_barrio_actual", tr("Barrio actual conquistado.")))
        self.btn_conq_todos.Bind(wx.EVT_BUTTON, lambda e: self._accion_jugador("conquistar_todos_barrios", tr("Todos los barrios conquistados.")))
        self.btn_aplicar_perro.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar(
            "jugador.set",
            {
                "perro": self.txt_perro_nombre.GetValue().strip(),
                "perro_hambre": self.sp_perro_hambre.GetValue(),
                "perro_confianza": self.sp_perro_confianza.GetValue(),
            },
            tr("Datos del perro actualizados."),
        ))
        self.btn_perro.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("jugador.set", {"accion": "adoptar_perro", "nombre": self.txt_perro_nombre.GetValue().strip()}, tr("Perro compañero activado junto a ti.")))

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("Jugador"))

    def _construir_tab_inventario(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Inventario"))
        s = wx.BoxSizer(wx.VERTICAL)
        sub = wx.Notebook(pag, name=tr("Subcategorías de Inventario"))

        # 2.1 Armas
        p_arm = wx.Panel(sub, name=tr("Armas"))
        sa = wx.BoxSizer(wx.VERTICAL)
        _, self.sel_arma = crear_campo(
            p_arm, tr("&Arma del catálogo:"), wx.Choice, choices=[],
            ayuda=tr("Al elegir un arma se muestran su cargador, reserva, silenciador y cargador ampliado actuales."),
            sizer=sa,
        )
        _, self.txt_arma_estado = crear_campo(
            p_arm, tr("Es&tado actual:"), wx.TextCtrl, style=wx.TE_READONLY,
            sizer=sa, horizontal=True,
        )
        ga = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        ga.AddGrowableCol(1, 1)
        ga.AddGrowableCol(3, 1)
        self.sp_arma_cargador = _campo_grid(p_arm, ga, tr("&Cargador:"), wx.SpinCtrl, min=0, max=9999, initial=0)
        self.sp_balas = _campo_grid(p_arm, ga, tr("Munición de &reserva:"), wx.SpinCtrl, min=0, max=99999, initial=250)
        sa.Add(ga, 0, wx.EXPAND | wx.ALL, 6)
        fa_chk = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_silenciador = wx.CheckBox(p_arm, label=tr("&Silenciador"))
        self.chk_ampliado = wx.CheckBox(p_arm, label=tr("Cargador am&pliado"))
        fa_chk.Add(self.chk_silenciador, 0, wx.ALL, 6)
        fa_chk.Add(self.chk_ampliado, 0, wx.ALL, 6)
        sa.Add(fa_chk, 0)
        b_armas = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_dar_arma = wx.Button(p_arm, label=tr("&Dar / aplicar arma"))
        self.btn_equipar_arma = wx.Button(p_arm, label=tr("&Equipar"))
        self.btn_quitar_arma = wx.Button(p_arm, label=tr("&Quitar arma"))
        self.btn_dar_todas = wx.Button(p_arm, label=tr("Dar t&odas las armas"))
        for b in (self.btn_dar_arma, self.btn_equipar_arma, self.btn_quitar_arma, self.btn_dar_todas):
            b_armas.Add(b, 0, wx.ALL, 4)
        sa.Add(b_armas, 0, wx.EXPAND | wx.ALL, 4)
        p_arm.SetSizer(sa)
        sub.AddPage(p_arm, tr("Armas"))

        # 2.2 Objetos y Mochila
        p_obj = wx.Panel(sub, name=tr("Objetos y Mochila"))
        so = wx.BoxSizer(wx.VERTICAL)
        box_o = wx.StaticBoxSizer(wx.VERTICAL, p_obj, tr("Objetos útiles del inventario"))
        op = box_o.GetStaticBox()
        fo1 = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_objeto = crear_campo(op, tr("&Objeto útil:"), wx.Choice, choices=[], sizer=fo1, horizontal=True)
        _, self.sp_obj_cant = crear_campo(op, tr("&Cantidad:"), wx.SpinCtrl, min=0, max=9999, initial=1, sizer=fo1, horizontal=True, expandir=False)
        box_o.Add(fo1, 0, wx.EXPAND | wx.ALL, 2)
        bo = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_fijar_objeto = wx.Button(op, label=tr("&Fijar cantidad"))
        self.btn_dar_objeto = wx.Button(op, label=tr("&Sumar cantidad"))
        bo.Add(self.btn_fijar_objeto, 0, wx.ALL, 4)
        bo.Add(self.btn_dar_objeto, 0, wx.ALL, 4)
        box_o.Add(bo, 0)
        so.Add(box_o, 0, wx.EXPAND | wx.ALL, 4)

        box_m = wx.StaticBoxSizer(wx.VERTICAL, p_obj, tr("Mochila y objetos de valor"))
        mp = box_m.GetStaticBox()
        fm = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_valor = crear_campo(mp, tr("Objeto de &valor:"), wx.Choice, choices=[], sizer=fm, horizontal=True)
        self.btn_dar_valor = wx.Button(mp, label=tr("Me&ter en mochila"))
        fm.Add(self.btn_dar_valor, 0, wx.ALL, 4)
        box_m.Add(fm, 0, wx.EXPAND | wx.ALL, 2)
        bm = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_mochila_grande = wx.CheckBox(mp, label=tr("Mochila &grande (40 huecos)"))
        self.btn_blanquear_mochila = wx.Button(mp, label=tr("&Limpiar marca de robado"))
        bm.Add(self.chk_mochila_grande, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        bm.Add(self.btn_blanquear_mochila, 0, wx.ALL, 4)
        box_m.Add(bm, 0)
        so.Add(box_m, 0, wx.EXPAND | wx.ALL, 4)
        p_obj.SetSizer(so)
        sub.AddPage(p_obj, tr("Objetos y Mochila"))

        # 2.3 Sustancias y Comida
        p_sc = wx.Panel(sub, name=tr("Sustancias y Comida"))
        ssc = wx.BoxSizer(wx.VERTICAL)
        box_su = wx.StaticBoxSizer(wx.VERTICAL, p_sc, tr("Sustancias (contenido +18)"))
        sup = box_su.GetStaticBox()
        fsu = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_sustancia = crear_campo(sup, tr("&Sustancia:"), wx.Choice, choices=[], sizer=fsu, horizontal=True)
        _, self.sp_sust_cant = crear_campo(sup, tr("&Unidades:"), wx.SpinCtrl, min=0, max=999, initial=0, sizer=fsu, horizontal=True, expandir=False)
        self.btn_fijar_sustancia = wx.Button(sup, label=tr("&Fijar unidades"))
        self.btn_dar_sustancia = wx.Button(sup, label=tr("Su&mar +10"))
        fsu.Add(self.btn_fijar_sustancia, 0, wx.ALL, 4)
        fsu.Add(self.btn_dar_sustancia, 0, wx.ALL, 4)
        box_su.Add(fsu, 0, wx.EXPAND | wx.ALL, 2)
        ssc.Add(box_su, 0, wx.EXPAND | wx.ALL, 4)

        box_pr = wx.StaticBoxSizer(wx.VERTICAL, p_sc, tr("Comida y productos de cocina"))
        prp = box_pr.GetStaticBox()
        fpr = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_producto = crear_campo(prp, tr("&Producto:"), wx.Choice, choices=[], sizer=fpr, horizontal=True)
        _, self.sp_prod_cant = crear_campo(prp, tr("&Cantidad:"), wx.SpinCtrl, min=1, max=99, initial=5, sizer=fpr, horizontal=True, expandir=False)
        self.btn_dar_producto = wx.Button(prp, label=tr("Añadir al &bolsillo"))
        fpr.Add(self.btn_dar_producto, 0, wx.ALL, 4)
        box_pr.Add(fpr, 0, wx.EXPAND | wx.ALL, 2)
        ssc.Add(box_pr, 0, wx.EXPAND | wx.ALL, 4)
        p_sc.SetSizer(ssc)
        sub.AddPage(p_sc, tr("Sustancias y Comida"))

        s.Add(sub, 1, wx.EXPAND | wx.ALL, 4)

        self.sel_arma.Bind(wx.EVT_CHOICE, lambda e: self._sincronizar_arma_actual(True))
        self.btn_dar_arma.Bind(wx.EVT_BUTTON, lambda e: self._accion_arma("dar"))
        self.btn_equipar_arma.Bind(wx.EVT_BUTTON, lambda e: self._accion_arma("equipar"))
        self.btn_quitar_arma.Bind(wx.EVT_BUTTON, lambda e: self._accion_arma("quitar"))
        self.btn_dar_todas.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar(
            "inventario.arma",
            {"accion": "dar_todas", "balas": self.sp_balas.GetValue(), "silenciador": self.chk_silenciador.GetValue(), "ampliado": self.chk_ampliado.GetValue()},
            tr("Todas las armas añadidas al arsenal."),
        ))
        self.sel_objeto.Bind(wx.EVT_CHOICE, lambda e: self._sincronizar_objeto_actual(True))
        self.btn_fijar_objeto.Bind(wx.EVT_BUTTON, lambda e: self._dar_objeto(fijar=True))
        self.btn_dar_objeto.Bind(wx.EVT_BUTTON, lambda e: self._dar_objeto(fijar=False))
        self.btn_dar_valor.Bind(wx.EVT_BUTTON, lambda e: self._dar_valor())
        self.chk_mochila_grande.Bind(wx.EVT_CHECKBOX, lambda e: self._ejecutar(
            "inventario.objeto", {"tipo": "mochila_grande", "valor": self.chk_mochila_grande.GetValue()},
            tr("Tamaño de mochila actualizado."),
        ))
        self.btn_blanquear_mochila.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("inventario.objeto", {"tipo": "vaciar_robados"}, tr("Objetos de la mochila marcados como legítimos.")))
        self.sel_sustancia.Bind(wx.EVT_CHOICE, lambda e: self._sincronizar_sustancia_actual(True))
        self.btn_fijar_sustancia.Bind(wx.EVT_BUTTON, lambda e: self._dar_sustancia(fijar=True, cantidad=self.sp_sust_cant.GetValue()))
        self.btn_dar_sustancia.Bind(wx.EVT_BUTTON, lambda e: self._dar_sustancia(fijar=False, cantidad=10))
        self.btn_dar_producto.Bind(wx.EVT_BUTTON, lambda e: self._dar_producto())

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("Inventario"))

    def _construir_tab_vehiculos(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Vehículos"))
        s = wx.BoxSizer(wx.VERTICAL)
        sub = wx.Notebook(pag, name=tr("Subcategorías de Vehículos"))

        # 3.1 Generar
        p_gen = wx.Panel(sub, name=tr("Generar vehículo"))
        sg = wx.BoxSizer(wx.VERTICAL)
        _, self.sel_modelo_veh = crear_campo(p_gen, tr("&Modelo a generar:"), wx.Choice, choices=[], sizer=sg)
        _, self.txt_veh_nombre = crear_campo(p_gen, tr("&Nombre propio (opcional):"), wx.TextCtrl, sizer=sg)
        fg = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_veh_mio = wx.CheckBox(p_gen, label=tr("&Hacer mío"))
        self.chk_veh_mio.SetValue(True)
        self.chk_veh_subir = wx.CheckBox(p_gen, label=tr("&Subir al instante"))
        self.chk_veh_subir.SetValue(True)
        self.chk_veh_mejoras_max = wx.CheckBox(p_gen, label=tr("Me&joras al máximo"))
        fg.Add(self.chk_veh_mio, 0, wx.ALL, 6)
        fg.Add(self.chk_veh_subir, 0, wx.ALL, 6)
        fg.Add(self.chk_veh_mejoras_max, 0, wx.ALL, 6)
        sg.Add(fg, 0)
        self.btn_crear_veh = wx.Button(p_gen, label=tr("&Generar vehículo junto a mí"))
        sg.Add(self.btn_crear_veh, 0, wx.ALL, 6)
        p_gen.SetSizer(sg)
        sub.AddPage(p_gen, tr("Generar"))

        # 3.2 Activos y acciones
        p_act = wx.Panel(sub, name=tr("Vehículos activos"))
        sa = wx.BoxSizer(wx.VERTICAL)
        _, self.lista_vehiculos = crear_campo(
            p_act, tr("&Vehículos vivos en la localidad:"), wx.ListBox, choices=[], size=(-1, 210),
            ayuda=tr("Elige un vehículo para actuar sobre él o editar sus especificaciones en la subpestaña siguiente."),
            sizer=sa,
        )
        b_veh = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_veh_subir = wx.Button(p_act, label=tr("&Subir"))
        self.btn_veh_traer = wx.Button(p_act, label=tr("&Traer aquí"))
        self.btn_veh_reparar = wx.Button(p_act, label=tr("&Reparar"))
        self.btn_veh_combustible = wx.Button(p_act, label=tr("Llenar &depósito"))
        self.btn_veh_averias = wx.Button(p_act, label=tr("Quitar &averías"))
        self.btn_veh_mejoras = wx.Button(p_act, label=tr("&Mejoras máx."))
        self.btn_veh_mio = wx.Button(p_act, label=tr("Hacer &propio"))
        self.btn_veh_explotar = wx.Button(p_act, label=tr("E&xplotar"))
        self.btn_veh_eliminar = wx.Button(p_act, label=tr("E&liminar"))
        self.btn_veh_limpiar = wx.Button(p_act, label=tr("Limpiar tráf&ico"))
        for b in (
            self.btn_veh_subir, self.btn_veh_traer, self.btn_veh_reparar, self.btn_veh_combustible,
            self.btn_veh_averias, self.btn_veh_mejoras, self.btn_veh_mio, self.btn_veh_explotar,
            self.btn_veh_eliminar, self.btn_veh_limpiar,
        ):
            b_veh.Add(b, 0, wx.ALL, 4)
        sa.Add(b_veh, 0, wx.EXPAND | wx.ALL, 4)
        p_act.SetSizer(sa)
        sub.AddPage(p_act, tr("Vehículos activos"))

        # 3.3 Especificaciones y Taller
        p_ed = wx.Panel(sub, name=tr("Especificaciones y Taller"))
        sed = wx.BoxSizer(wx.VERTICAL)
        _, self.txt_veh_ed_info = crear_campo(p_ed, tr("&Vehículo seleccionado:"), wx.TextCtrl, style=wx.TE_READONLY, sizer=sed, horizontal=True)
        grid_v = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        grid_v.AddGrowableCol(1, 1)
        grid_v.AddGrowableCol(3, 1)

        def _vnum(etq, minimo, maximo, inicial):
            return _campo_grid(p_ed, grid_v, etq, wx.SpinCtrl, min=int(minimo), max=int(maximo), initial=int(inicial))

        self.txt_veh_ed_nombre = _campo_grid(p_ed, grid_v, tr("&Nombre:"), wx.TextCtrl)
        self.sel_veh_ia = _campo_grid(
            p_ed, grid_v, tr("Modo &IA:"), wx.Choice,
            choices=[tr("Sin IA"), tr("Aparcado"), tr("Tráfico"), tr("Huida"), tr("Policía"), tr("Barco")],
        )
        self.sp_veh_vel = _vnum(tr("Velocidad &máx. (m/s):"), 1, 250, 25)
        self.sp_veh_acel = _vnum(tr("&Aceleración:"), 1, 100, 6)
        self.sp_veh_freno = _vnum(tr("&Freno:"), 1, 100, 12)
        self.sp_veh_salud = _vnum(tr("&Salud actual:"), 1, 50000, 100)
        self.sp_veh_salud_max = _vnum(tr("Salud má&xima:"), 10, 50000, 100)
        sed.Add(grid_v, 0, wx.EXPAND | wx.ALL, 6)

        fila_chk_v = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_veh_hostil = wx.CheckBox(p_ed, label=tr("&Hostil"))
        self.chk_veh_cerrado = wx.CheckBox(p_ed, label=tr("&Cerrado"))
        self.chk_veh_solo_este = wx.CheckBox(p_ed, label=tr("Solo este e&jemplar"))
        self.chk_veh_solo_este.SetValue(True)
        self.btn_veh_guardar_specs = wx.Button(p_ed, label=tr("A&plicar especificaciones"))
        fila_chk_v.Add(self.chk_veh_hostil, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        fila_chk_v.Add(self.chk_veh_cerrado, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        fila_chk_v.Add(self.chk_veh_solo_este, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)
        fila_chk_v.Add(self.btn_veh_guardar_specs, 0, wx.ALL, 4)
        sed.Add(fila_chk_v, 0)

        box_tal = wx.StaticBoxSizer(wx.HORIZONTAL, p_ed, tr("Mejoras de taller del vehículo"))
        tp = box_tal.GetStaticBox()
        _, self.sel_veh_mejora = crear_campo(tp, tr("M&ejora:"), wx.Choice, choices=[], sizer=box_tal, horizontal=True)
        _, self.sp_veh_mejora_niv = crear_campo(tp, tr("Nive&l:"), wx.SpinCtrl, min=0, max=5, initial=0, sizer=box_tal, horizontal=True, expandir=False)
        self.btn_veh_mejora_aplicar = wx.Button(tp, label=tr("Aj&ustar mejora"))
        box_tal.Add(self.btn_veh_mejora_aplicar, 0, wx.ALL, 4)
        sed.Add(box_tal, 0, wx.EXPAND | wx.ALL, 4)
        p_ed.SetSizer(sed)
        sub.AddPage(p_ed, tr("Especificaciones y Taller"))

        s.Add(sub, 1, wx.EXPAND | wx.ALL, 4)

        self.btn_crear_veh.Bind(wx.EVT_BUTTON, lambda e: self._crear_vehiculo())
        self.lista_vehiculos.Bind(wx.EVT_LISTBOX, lambda e: self._cargar_vehiculo_seleccionado(forzar=True))
        self.btn_veh_subir.Bind(wx.EVT_BUTTON, lambda e: self._accion_vehiculo("subir", tr("Has subido al vehículo.")))
        self.btn_veh_traer.Bind(wx.EVT_BUTTON, lambda e: self._accion_vehiculo("traer_aqui", tr("Vehículo traído junto a ti.")))
        self.btn_veh_reparar.Bind(wx.EVT_BUTTON, lambda e: self._editar_vehiculo({"reparar": True}, tr("Vehículo reparado.")))
        self.btn_veh_combustible.Bind(wx.EVT_BUTTON, lambda e: self._editar_vehiculo({"llenar_combustible": True}, tr("Depósito lleno.")))
        self.btn_veh_averias.Bind(wx.EVT_BUTTON, lambda e: self._editar_vehiculo({"quitar_averias": True}, tr("Averías y pinchazos eliminados.")))
        self.btn_veh_mejoras.Bind(wx.EVT_BUTTON, lambda e: self._editar_vehiculo({"mejoras_max": True}, tr("Todas las mejoras de taller aplicadas.")))
        self.btn_veh_mio.Bind(wx.EVT_BUTTON, lambda e: self._accion_vehiculo("hacer_mio", tr("Vehículo marcado como tuyo.")))
        self.btn_veh_explotar.Bind(wx.EVT_BUTTON, lambda e: self._accion_vehiculo("explotar", tr("Vehículo detonado.")))
        self.btn_veh_eliminar.Bind(wx.EVT_BUTTON, lambda e: self._accion_vehiculo("eliminar", tr("Vehículo eliminado.")))
        self.btn_veh_limpiar.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("vehiculos.accion", {"accion": "limpiar_trafico"}, tr("Tráfico de la calle limpiado.")))
        self.btn_veh_guardar_specs.Bind(wx.EVT_BUTTON, lambda e: self._guardar_specs_vehiculo())
        self.sel_veh_mejora.Bind(wx.EVT_CHOICE, lambda e: self._sincronizar_mejora_vehiculo(True))
        self.btn_veh_mejora_aplicar.Bind(wx.EVT_BUTTON, lambda e: self._aplicar_mejora_vehiculo())

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("Vehículos"))

    def _construir_tab_npcs(self) -> None:
        pag = wx.Panel(self.libro, name=tr("NPCs y Bandas"))
        s = wx.BoxSizer(wx.VERTICAL)
        sub = wx.Notebook(pag, name=tr("Subcategorías de NPCs y Bandas"))

        # 4.1 Generar
        p_gen = wx.Panel(sub, name=tr("Generar NPCs"))
        sg = wx.BoxSizer(wx.VERTICAL)
        g1 = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        g1.AddGrowableCol(1, 1)
        g1.AddGrowableCol(3, 1)
        self.sel_npc_modo = _campo_grid(
            p_gen, g1, tr("&Tipo de entidad:"), wx.Choice,
            choices=[tr("Enemigo"), tr("Pandillero"), tr("Policía"), tr("Civil"), tr("Aliado"), tr("Perro")],
        )
        self.sel_npc_clase = _campo_grid(p_gen, g1, tr("&Clase (catálogo):"), wx.Choice, choices=[])
        self.sel_npc_banda = _campo_grid(p_gen, g1, tr("&Banda:"), wx.Choice, choices=[tr("(ninguna)")])
        self.sel_npc_arma = _campo_grid(p_gen, g1, tr("Ar&ma:"), wx.Choice, choices=[tr("(por defecto)")])
        self.sp_npc_cant = _campo_grid(p_gen, g1, tr("Ca&ntidad:"), wx.SpinCtrl, min=1, max=20, initial=1)
        self.sp_npc_salud = _campo_grid(p_gen, g1, tr("&Salud:"), wx.SpinCtrl, min=1, max=5000, initial=75)
        sg.Add(g1, 0, wx.EXPAND | wx.ALL, 6)
        fg = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_npc_veh = wx.CheckBox(p_gen, label=tr("Llegan en &vehículo"))
        self.chk_npc_hostil = wx.CheckBox(p_gen, label=tr("&Hostil"))
        self.chk_npc_hostil.SetValue(True)
        self.btn_npc_crear = wx.Button(p_gen, label=tr("&Generar NPC(s) aquí"))
        fg.Add(self.chk_npc_veh, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        fg.Add(self.chk_npc_hostil, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 6)
        fg.Add(self.btn_npc_crear, 0, wx.ALL, 4)
        sg.Add(fg, 0)
        p_gen.SetSizer(sg)
        sub.AddPage(p_gen, tr("Generar NPCs"))

        # 4.2 Personas activas y editor
        p_act = wx.Panel(sub, name=tr("Personas activas"))
        sa = wx.BoxSizer(wx.VERTICAL)
        _, self.lista_npcs = crear_campo(p_act, tr("&Personas en la zona actual:"), wx.ListBox, choices=[], size=(-1, 160), sizer=sa)
        gn = wx.FlexGridSizer(cols=4, vgap=6, hgap=10)
        gn.AddGrowableCol(1, 1)
        gn.AddGrowableCol(3, 1)
        self.txt_npc_ed_nombre = _campo_grid(p_act, gn, tr("&Nombre:"), wx.TextCtrl)
        self.sp_npc_ed_salud = _campo_grid(p_act, gn, tr("&Salud:"), wx.SpinCtrl, min=0, max=10000, initial=80)
        self.sp_npc_ed_punt = _campo_grid(p_act, gn, tr("P&untería (0-100):"), wx.SpinCtrl, min=0, max=100, initial=42, ayuda=tr("Precisión al disparar, en porcentaje."))
        self.sel_npc_ed_estado = _campo_grid(
            p_act, gn, tr("&Estado:"), wx.Choice,
            choices=[tr("Pasea"), tr("Quieto"), tr("Huye"), tr("Ataca"), tr("Sigue")],
        )
        self.sp_npc_ed_conf = _campo_grid(p_act, gn, tr("&Confianza civil (-100..100):"), wx.SpinCtrl, min=-100, max=100, initial=0)
        self.chk_npc_ed_hostil = wx.CheckBox(p_act, label=tr("&Hostil ahora"))
        gn.Add(wx.StaticText(p_act, label=tr("Hostilidad:")), 0, wx.ALIGN_CENTER_VERTICAL)
        gn.Add(self.chk_npc_ed_hostil, 0, wx.ALIGN_CENTER_VERTICAL)
        sa.Add(gn, 0, wx.EXPAND | wx.ALL, 6)

        b_npc = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_npc_aplicar = wx.Button(p_act, label=tr("&Aplicar a NPC"))
        self.btn_npc_traer = wx.Button(p_act, label=tr("&Traer aquí"))
        self.btn_npc_curar = wx.Button(p_act, label=tr("Cu&rar"))
        self.btn_npc_matar = wx.Button(p_act, label=tr("&Matar"))
        self.btn_npc_eliminar = wx.Button(p_act, label=tr("El&iminar"))
        self.btn_npc_limp_hostiles = wx.Button(p_act, label=tr("Eliminar h&ostiles"))
        self.btn_npc_limp_muertos = wx.Button(p_act, label=tr("Limpiar caí&dos"))
        for b in (
            self.btn_npc_aplicar, self.btn_npc_traer, self.btn_npc_curar, self.btn_npc_matar,
            self.btn_npc_eliminar, self.btn_npc_limp_hostiles, self.btn_npc_limp_muertos,
        ):
            b_npc.Add(b, 0, wx.ALL, 3)
        sa.Add(b_npc, 0, wx.EXPAND | wx.ALL, 2)
        p_act.SetSizer(sa)
        sub.AddPage(p_act, tr("Personas activas"))

        # 4.3 Reputación con bandas
        p_rep = wx.Panel(sub, name=tr("Reputación con Bandas"))
        sr = wx.BoxSizer(wx.VERTICAL)
        fr = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_rep_banda = crear_campo(p_rep, tr("&Banda:"), wx.Choice, choices=[tr("Todas las bandas")], sizer=fr, horizontal=True)
        _, self.sp_rep_val = crear_campo(p_rep, tr("&Reputación (-100 a 100):"), wx.SpinCtrl, min=-100, max=100, initial=0, sizer=fr, horizontal=True, expandir=False)
        sr.Add(fr, 0, wx.EXPAND | wx.ALL, 6)
        br = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_rep_aplicar = wx.Button(p_rep, label=tr("&Fijar reputación"))
        self.btn_rep_aliados = wx.Button(p_rep, label=tr("&Aliados (+100)"))
        self.btn_rep_neutral = wx.Button(p_rep, label=tr("&Neutral (0)"))
        self.btn_rep_hostil = wx.Button(p_rep, label=tr("&Enemigos (-100)"))
        for b in (self.btn_rep_aplicar, self.btn_rep_aliados, self.btn_rep_neutral, self.btn_rep_hostil):
            br.Add(b, 0, wx.ALL, 4)
        sr.Add(br, 0, wx.LEFT, 4)
        p_rep.SetSizer(sr)
        sub.AddPage(p_rep, tr("Reputación con Bandas"))

        s.Add(sub, 1, wx.EXPAND | wx.ALL, 4)

        self.btn_npc_crear.Bind(wx.EVT_BUTTON, lambda e: self._crear_npc())
        self.lista_npcs.Bind(wx.EVT_LISTBOX, lambda e: self._cargar_npc_seleccionado(forzar=True))
        self.btn_npc_aplicar.Bind(wx.EVT_BUTTON, lambda e: self._aplicar_npc())
        self.btn_npc_traer.Bind(wx.EVT_BUTTON, lambda e: self._accion_npc("traer_aqui", tr("NPC traído junto a ti.")))
        self.btn_npc_curar.Bind(wx.EVT_BUTTON, lambda e: self._accion_npc("curar", tr("NPC curado.")))
        self.btn_npc_matar.Bind(wx.EVT_BUTTON, lambda e: self._accion_npc("matar", tr("NPC abatido.")))
        self.btn_npc_eliminar.Bind(wx.EVT_BUTTON, lambda e: self._accion_npc("eliminar", tr("NPC eliminado.")))
        self.btn_npc_limp_hostiles.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("npcs.accion", {"accion": "eliminar_hostiles"}, tr("Hostiles eliminados.")))
        self.btn_npc_limp_muertos.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("npcs.accion", {"accion": "eliminar_muertos"}, tr("NPCs caídos limpiados.")))
        self.sel_rep_banda.Bind(wx.EVT_CHOICE, lambda e: self._sincronizar_rep_banda_actual(True))
        self.btn_rep_aplicar.Bind(wx.EVT_BUTTON, lambda e: self._fijar_rep_banda())
        self.btn_rep_aliados.Bind(wx.EVT_BUTTON, lambda e: self._fijar_rep_banda(100))
        self.btn_rep_neutral.Bind(wx.EVT_BUTTON, lambda e: self._fijar_rep_banda(0))
        self.btn_rep_hostil.Bind(wx.EVT_BUTTON, lambda e: self._fijar_rep_banda(-100))

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("NPCs y Bandas"))

    def _construir_tab_policia(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Policía"))
        s = wx.BoxSizer(wx.VERTICAL)

        box_b = wx.StaticBoxSizer(wx.VERTICAL, pag, tr("Nivel de búsqueda"))
        bp = box_b.GetStaticBox()
        fila = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sp_estrellas = crear_campo(
            bp, tr("&Estrellas actuales (0 a 5):"), wx.SpinCtrl, min=0, max=5, initial=0,
            ayuda=tr("Nivel de búsqueda policial de 0 a 5, sincronizado con la partida."),
            sizer=fila, horizontal=True, expandir=False,
        )
        self.btn_estrellas = wx.Button(bp, label=tr("&Fijar estrellas"))
        self.btn_limpiar_busq = wx.Button(bp, label=tr("&Limpiar búsqueda y persecución"))
        fila.Add(self.btn_estrellas, 0, wx.ALL, 4)
        fila.Add(self.btn_limpiar_busq, 0, wx.ALL, 4)
        box_b.Add(fila, 0, wx.EXPAND | wx.ALL, 2)
        s.Add(box_b, 0, wx.EXPAND | wx.ALL, 6)

        box_d = wx.StaticBoxSizer(wx.VERTICAL, pag, tr("Despliegue y opciones policiales"))
        dp = box_d.GetStaticBox()
        b_pol = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_patrulla = wx.Button(dp, label=tr("Mandar &patrulla"))
        self.btn_patrulla_ronda = wx.Button(dp, label=tr("Patrulla de &ronda"))
        self.btn_heli_on = wx.Button(dp, label=tr("Lanzar &helicóptero"))
        self.btn_heli_off = wx.Button(dp, label=tr("Re&tirar helicóptero"))
        for b in (self.btn_patrulla, self.btn_patrulla_ronda, self.btn_heli_on, self.btn_heli_off):
            b_pol.Add(b, 0, wx.ALL, 4)
        box_d.Add(b_pol, 0, wx.EXPAND)
        fc = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_sin_policia = wx.CheckBox(dp, label=tr("Jugar &sin policía"))
        self.chk_pol_heli = wx.CheckBox(dp, label=tr("Activar helicóptero policial en &nivel 5"))
        fc.Add(self.chk_sin_policia, 0, wx.ALL, 6)
        fc.Add(self.chk_pol_heli, 0, wx.ALL, 6)
        box_d.Add(fc, 0)
        s.Add(box_d, 0, wx.EXPAND | wx.ALL, 6)

        self.btn_estrellas.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("policia.set", {"estrellas": self.sp_estrellas.GetValue()}, tr("Nivel de búsqueda fijado a {n}.").format(n=self.sp_estrellas.GetValue())))
        self.btn_limpiar_busq.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("policia.set", {"estrellas": 0, "limpiar_policias": True}, tr("Búsqueda limpiada y agentes retirados.")))
        self.btn_patrulla.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("policia.set", {"lanzar_patrulla": True}, tr("Patrulla enviada.")))
        self.btn_patrulla_ronda.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("policia.set", {"lanzar_patrulla_ronda": True}, tr("Patrulla de ronda generada.")))
        self.btn_heli_on.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("policia.set", {"lanzar_helicoptero": True}, tr("Helicóptero de la policía desplegado.")))
        self.btn_heli_off.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("policia.set", {"quitar_helicoptero": True}, tr("Helicóptero retirado.")))
        self.chk_sin_policia.Bind(wx.EVT_CHECKBOX, lambda e: self._toggle_cfg("sin_policia", self.chk_sin_policia.GetValue()))
        self.chk_pol_heli.Bind(wx.EVT_CHECKBOX, lambda e: self._toggle_cfg("helicoptero_policia", self.chk_pol_heli.GetValue()))

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("Policía"))

    def _construir_tab_eventos(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Eventos"))
        s = wx.BoxSizer(wx.VERTICAL)

        box_suc = wx.StaticBoxSizer(wx.HORIZONTAL, pag, tr("Sucesos callejeros aleatorios"))
        sp_suc = box_suc.GetStaticBox()
        self.btn_ev_atraco = wx.Button(sp_suc, label=tr("Suceso: &Atraco a peatón"))
        self.btn_ev_banda = wx.Button(sp_suc, label=tr("Suceso: &Pandilleros"))
        self.btn_ev_maletin = wx.Button(sp_suc, label=tr("Suceso: &Maletín perdido"))
        self.btn_ev_cancelar = wx.Button(sp_suc, label=tr("&Cancelar suceso"))
        for b in (self.btn_ev_atraco, self.btn_ev_banda, self.btn_ev_maletin, self.btn_ev_cancelar):
            box_suc.Add(b, 0, wx.ALL, 4)
        s.Add(box_suc, 0, wx.EXPAND | wx.ALL, 4)

        box_pers = wx.StaticBoxSizer(wx.HORIZONTAL, pag, tr("Persecución en vehículo"))
        pp = box_pers.GetStaticBox()
        _, self.sel_pers_modelo = crear_campo(pp, tr("M&odelo fugitivo:"), wx.Choice, choices=[], sizer=box_pers, horizontal=True)
        _, self.sp_pers_vel = crear_campo(pp, tr("&Velocidad objetivo:"), wx.SpinCtrl, min=8, max=80, initial=24, sizer=box_pers, horizontal=True, expandir=False)
        self.btn_ev_pers = wx.Button(pp, label=tr("&Lanzar persecución"))
        box_pers.Add(self.btn_ev_pers, 0, wx.ALL, 4)
        s.Add(box_pers, 0, wx.EXPAND | wx.ALL, 4)

        box_gue = wx.StaticBoxSizer(wx.HORIZONTAL, pag, tr("Guerras y peleas de banda"))
        gp = box_gue.GetStaticBox()
        _, self.sel_ev_banda = crear_campo(gp, tr("&Banda rival:"), wx.Choice, choices=[], sizer=box_gue, horizontal=True)
        self.btn_ev_guerra = wx.Button(gp, label=tr("Iniciar &guerra de barrio"))
        self.btn_ev_pelea = wx.Button(gp, label=tr("Buscar p&elea"))
        self.btn_ev_fin_guerra = wx.Button(gp, label=tr("&Terminar guerra"))
        for b in (self.btn_ev_guerra, self.btn_ev_pelea, self.btn_ev_fin_guerra):
            box_gue.Add(b, 0, wx.ALL, 4)
        s.Add(box_gue, 0, wx.EXPAND | wx.ALL, 4)

        box_otr = wx.StaticBoxSizer(wx.HORIZONTAL, pag, tr("Atracos, encargos y calle"))
        op = box_otr.GetStaticBox()
        b_otros = wx.WrapSizer(wx.HORIZONTAL)
        self.btn_ev_atr_local = wx.Button(op, label=tr("At&racar local cercano"))
        self.btn_ev_atr_banco = wx.Button(op, label=tr("Atracar ba&nco cercano"))
        self.btn_ev_vetos = wx.Button(op, label=tr("Limp&iar vetos de locales"))
        self.btn_ev_ambu = wx.Button(op, label=tr("Man&dar ambulancia"))
        self.btn_ev_dinero = wx.Button(op, label=tr("&Soltar maletín de 1.000 €"))
        self.btn_ev_contrato = wx.Button(op, label=tr("&Hacer contrato"))
        self.btn_ev_encargo = wx.Button(op, label=tr("B&uscar encargo de coche"))
        for b in (
            self.btn_ev_atr_local, self.btn_ev_atr_banco, self.btn_ev_vetos,
            self.btn_ev_ambu, self.btn_ev_dinero, self.btn_ev_contrato, self.btn_ev_encargo,
        ):
            b_otros.Add(b, 0, wx.ALL, 4)
        box_otr.Add(b_otros, 1, wx.EXPAND)
        s.Add(box_otr, 0, wx.EXPAND | wx.ALL, 4)

        self.btn_ev_atraco.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "suceso_atraco"}, tr("Suceso de atraco generado cerca.")))
        self.btn_ev_banda.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "suceso_banda"}, tr("Suceso de pandilleros generado cerca.")))
        self.btn_ev_maletin.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "suceso_maletin"}, tr("Maletín perdido generado cerca.")))
        self.btn_ev_cancelar.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "cancelar_suceso"}, tr("Suceso cancelado.")))
        self.btn_ev_pers.Bind(wx.EVT_BUTTON, lambda e: self._lanzar_persecucion())
        self.btn_ev_guerra.Bind(wx.EVT_BUTTON, lambda e: self._lanzar_guerra("guerra_barrio"))
        self.btn_ev_pelea.Bind(wx.EVT_BUTTON, lambda e: self._lanzar_guerra("buscar_pelea"))
        self.btn_ev_fin_guerra.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "terminar_guerra"}, tr("Guerra o pelea terminada.")))
        self.btn_ev_atr_local.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "atraco_local_cercano"}, tr("Atraco al local cercano iniciado.")))
        self.btn_ev_atr_banco.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "atraco_banco_cercano"}, tr("Atraco al banco cercano iniciado.")))
        self.btn_ev_vetos.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "limpiar_vetos"}, tr("Vetos de locales y proveedores limpiados.")))
        self.btn_ev_ambu.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "ambulancia"}, tr("Ambulancia en camino.")))
        self.btn_ev_dinero.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "soltar_dinero", "valor": 1000}, tr("Maletín de 1000 euros soltado junto a ti.")))
        self.btn_ev_contrato.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "contrato"}, tr("Contrato iniciado.")))
        self.btn_ev_encargo.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("eventos.lanzar", {"tipo": "encargo_coche"}, tr("Encargo de vehículo iniciado.")))

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("Eventos"))

    def _construir_tab_mundo(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Mundo y Teletransporte"))
        s = wx.BoxSizer(wx.VERTICAL)

        box_tp = wx.StaticBoxSizer(wx.VERTICAL, pag, tr("Teletransporte"))
        tp = box_tp.GetStaticBox()
        _, self.sel_mapa = crear_campo(tp, tr("&Zona / Localidad:"), wx.Choice, choices=[], sizer=box_tp)
        _, self.txt_filtro_lugar = crear_campo(tp, tr("&Filtrar lugares:"), wx.TextCtrl, sizer=box_tp)
        _, self.sel_lugar = crear_campo(tp, tr("&Lugar de destino:"), wx.Choice, choices=[], sizer=box_tp)
        self.btn_tp = wx.Button(tp, label=tr("&Teletransportar al lugar elegido"))
        box_tp.Add(self.btn_tp, 0, wx.ALL, 4)
        s.Add(box_tp, 0, wx.EXPAND | wx.ALL, 4)

        box_ti = wx.StaticBoxSizer(wx.HORIZONTAL, pag, tr("Tiempo y clima (sincronizados)"))
        tip = box_ti.GetStaticBox()
        _, self.sp_hora = crear_campo(tip, tr("&Hora (0-23):"), wx.SpinCtrl, min=0, max=23, initial=12, sizer=box_ti, horizontal=True, expandir=False)
        _, self.sp_dia = crear_campo(tip, tr("&Día:"), wx.SpinCtrl, min=1, max=99999, initial=1, sizer=box_ti, horizontal=True, expandir=False)
        self.chk_lluvia = wx.CheckBox(tip, label=tr("Ll&uvia"))
        box_ti.Add(self.chk_lluvia, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 8)
        _, self.sel_dia_azar = crear_campo(tip, tr("T&ipo de día:"), wx.Choice, choices=[], sizer=box_ti, horizontal=True)
        self.btn_aplicar_tiempo = wx.Button(tip, label=tr("&Aplicar tiempo"))
        self.btn_mas_hora = wx.Button(tip, label=tr("+1 h&ora"))
        box_ti.Add(self.btn_aplicar_tiempo, 0, wx.ALL, 4)
        box_ti.Add(self.btn_mas_hora, 0, wx.ALL, 4)
        s.Add(box_ti, 0, wx.EXPAND | wx.ALL, 4)

        box_cfg = wx.StaticBoxSizer(wx.VERTICAL, pag, tr("Opciones rápidas de jugabilidad (cfg)"))
        cp = box_cfg.GetStaticBox()
        wrap_cfg = wx.WrapSizer(wx.HORIZONTAL)
        self._chks_cfg: dict[str, wx.CheckBox] = {}
        for clave, etiqueta in (
            ("adultos", tr("&Contenido +18")),
            ("fuego_amigo", tr("Fue&go amigo")),
            ("guerra_calle", tr("Guerra de &barrios")),
            ("vida_realista", tr("&Vida realista")),
            ("combustible", tr("Combustibl&e")),
            ("averias", tr("Ave&rías")),
            ("normas_trafico", tr("&Normas de tráfico")),
            ("soltar_armas", tr("&Soltar armas")),
            ("mod_enemigos", tr("Ene&migos duros")),
            ("mod_policia", tr("&Policía estricta")),
        ):
            chk = wx.CheckBox(cp, label=etiqueta)
            chk.Bind(wx.EVT_CHECKBOX, lambda e, k=clave, c=chk: self._toggle_cfg(k, c.GetValue()))
            self._chks_cfg[clave] = chk
            wrap_cfg.Add(chk, 0, wx.ALL, 5)
        box_cfg.Add(wrap_cfg, 0, wx.EXPAND)
        s.Add(box_cfg, 0, wx.EXPAND | wx.ALL, 4)

        self.sel_mapa.Bind(wx.EVT_CHOICE, lambda e: self._poblar_lugares())
        self.txt_filtro_lugar.Bind(wx.EVT_TEXT, lambda e: self._poblar_lugares())
        self.btn_tp.Bind(wx.EVT_BUTTON, lambda e: self._teletransportar())
        self.btn_aplicar_tiempo.Bind(wx.EVT_BUTTON, lambda e: self._aplicar_tiempo())
        self.btn_mas_hora.Bind(wx.EVT_BUTTON, lambda e: self._ejecutar("mundo.set", {"pasar_horas": 1}, tr("Avanzada una hora.")))

        pag.SetSizer(s)
        self.libro.AddPage(pag, tr("Mundo"))

    def _construir_tab_inspector(self) -> None:
        pag = wx.Panel(self.libro, name=tr("Inspector Avanzado"))
        s = wx.BoxSizer(wx.VERTICAL)

        fila = wx.BoxSizer(wx.HORIZONTAL)
        _, self.sel_insp_obj = crear_campo(
            pag, tr("Á&mbito:"), wx.Choice, choices=["jugador", "stats", "cfg", "vehiculo_actual"],
            ayuda=tr("Permite inspeccionar y modificar cualquier atributo en vivo, incluso de futuras actualizaciones."),
            sizer=fila, horizontal=True,
        )
        _, self.txt_insp_filtro = crear_campo(pag, tr("&Filtrar clave:"), wx.TextCtrl, sizer=fila, horizontal=True)
        self.btn_insp_leer = wx.Button(pag, label=tr("&Leer ámbito"))
        fila.Add(self.btn_insp_leer, 0, wx.ALL, 4)
        s.Add(fila, 0, wx.EXPAND | wx.ALL, 4)

        _, self.lista_insp = crear_campo(pag, tr("&Campos disponibles:"), wx.ListBox, choices=[], size=(-1, 260), sizer=s)

        fila_ed = wx.BoxSizer(wx.HORIZONTAL)
        _, self.txt_insp_clave = crear_campo(pag, tr("Cla&ve:"), wx.TextCtrl, sizer=fila_ed, horizontal=True)
        _, self.txt_insp_valor = crear_campo(pag, tr("&Nuevo valor (texto o JSON):"), wx.TextCtrl, sizer=fila_ed, horizontal=True)
        self.btn_insp_escribir = wx.Button(pag, label=tr("&Aplicar cambio"))
        fila_ed.Add(self.btn_insp_escribir, 0, wx.ALL, 4)
        s.Add(fila_ed, 0, wx.EXPAND | wx.ALL, 4)

        _, self.txt_insp_estado = crear_campo(
            pag, tr("&Estado del inspector:"), wx.TextCtrl, style=wx.TE_READONLY,
            ayuda=tr("Muestra errores de sintaxis o confirmación de cambios del inspector."),
            sizer=s, horizontal=True,
        )
        self.txt_insp_estado.SetValue(tr("Listo. Selecciona un ámbito y pulsa Leer ámbito."))

        self.btn_insp_leer.Bind(wx.EVT_BUTTON, lambda e: self._leer_inspector())
        self.sel_insp_obj.Bind(wx.EVT_CHOICE, lambda e: self._leer_inspector())
        self.txt_insp_filtro.Bind(wx.EVT_TEXT, lambda e: self._filtrar_inspector())
        self.lista_insp.Bind(wx.EVT_LISTBOX, lambda e: self._seleccionar_clave_inspector())
        self.btn_insp_escribir.Bind(wx.EVT_BUTTON, lambda e: self._escribir_inspector())

        pag.SetSizer(s)
        self.libro.AddPage(pag, "Inspector")

    # ------------------------------------------------------------------ red y datos
    def _tecla_global(self, evento: wx.KeyEvent) -> None:
        if evento.GetKeyCode() == wx.WXK_F5 and evento.GetModifiers() == wx.MOD_NONE:
            self.refrescar_todo(anunciar=True)
            return
        evento.Skip()

    def _al_cerrar(self, evento: wx.CloseEvent) -> None:
        if self.timer.IsRunning():
            self.timer.Stop()
        evento.Skip()

    def _al_timer(self, evento: wx.TimerEvent) -> None:
        if self.cliente is not None:
            self.refrescar_estado(anunciar_error=False, forzar_sync=False)

    def _auto_conectar_silencioso(self) -> None:
        try:
            self.conectar(anunciar=False)
        except Exception:
            pass

    def _actualizar_boton_conexion(self) -> None:
        if self.cliente is not None:
            self.btn_conectar.SetLabel(tr("&2 Desconectar"))
            self.btn_conectar.SetHelpText(tr("Cierra la conexión actual con Puerto Bravo."))
        else:
            self.btn_conectar.SetLabel(tr("&2 Conectar"))
            self.btn_conectar.SetHelpText(tr("Busca y conecta con el proceso de Puerto Bravo seleccionado."))

    def _alternar_conexion(self) -> None:
        if self.cliente is not None:
            self.desconectar(anunciar=True)
        else:
            self.conectar(anunciar=True)

    def desconectar(self, anunciar: bool = True) -> None:
        self.cliente = None
        self.estado = {}
        self._ultimo_resumen = ""
        self._ultimas_claves_veh = []
        self._ultimas_claves_npc = []
        self._actualizar_boton_conexion()
        msg = tr("Desconectado. Pulsa Conectar cuando quieras volver a enlazar con Puerto Bravo.")
        self.txt_conexion.SetValue(msg)
        self.SetStatusText(msg)
        if anunciar:
            _hablar(msg)

    def conectar(self, anunciar: bool = True) -> bool:
        if self.cliente is not None:
            self._actualizar_boton_conexion()
            msg = tr("Ya estás conectado con Puerto Bravo. Pulsa Desconectar si quieres cerrar la conexión actual.")
            self.SetStatusText(msg)
            if anunciar:
                _hablar(msg)
            return True
        self.instancias = descubrir_instancias()
        if not self.instancias:
            self.cliente = None
            self._actualizar_boton_conexion()
            self.sel_instancia.Set([tr("(ninguna detectada)")])
            self.sel_instancia.SetSelection(0)
            self.txt_conexion.SetValue(
                tr("Sin conexión con Puerto Bravo (el juego está cerrado o en multijugador sin permiso del dueño del servidor).")
            )
            if anunciar:
                _hablar(tr("No se encontró Puerto Bravo con el puente habilitado."))
            return False
        etiquetas = [
            tr("PID {pid} — v{ver} (puerto {puerto})").format(pid=f["pid"], ver=f.get("version", "?"), puerto=f["puerto"])
            for f in self.instancias
        ]
        sel_idx = max(0, min(self.sel_instancia.GetSelection(), len(self.instancias) - 1))
        self.sel_instancia.Set(etiquetas)
        self.sel_instancia.SetSelection(sel_idx)
        ficha = self.instancias[sel_idx]
        try:
            cli = ClienteTrampas.desde_ficha(ficha)
            hola = cli.llamar("hola")
            self.cliente = cli
            self._actualizar_boton_conexion()
            self.catalogos = cli.llamar("catalogos")
            self._poblar_catalogos()
            self.refrescar_estado(anunciar_error=False, forzar_sync=True)
            self.SetStatusText(tr("Conectado a PID {pid} (Puerto Bravo v{ver}).").format(pid=hola["pid"], ver=hola.get("version", "?")))
            if anunciar:
                _hablar(tr("Conectado y sincronizado con Puerto Bravo."))
            return True
        except ErrorPuente as exc:
            self.cliente = None
            self._actualizar_boton_conexion()
            self.txt_conexion.SetValue(str(exc))
            if anunciar:
                mostrar_error(self, str(exc), tr("Error de conexión"))
            return False

    def _ejecutar(self, cmd: str, args: dict | None = None, mensaje_voz: str = ""):
        self._ultimo_error_puente = ""
        if self.cliente is None:
            if not self.conectar(anunciar=False):
                self._ultimo_error_puente = tr("Conecta primero con Puerto Bravo (un jugador o servidor con trampas permitidas).")
                mostrar_error(self, self._ultimo_error_puente, tr("Sin conexión"))
                return None
        try:
            res = self.cliente.llamar(cmd, **(args or {}))
            if mensaje_voz:
                self.SetStatusText(mensaje_voz)
                _hablar(mensaje_voz)
            self.refrescar_estado(anunciar_error=False, forzar_sync=True)
            return res
        except ErrorPuente as exc:
            self._ultimo_error_puente = str(exc)
            bajo = str(exc).lower()
            if (
                "multijugador" in bajo
                or "sin conexión" in bajo
                or tr("multijugador").lower() in bajo
                or tr("Comunicación anulada: modo multijugador activo.").lower() in bajo
                or tr("Sin conexión").lower() in bajo
            ):
                self.cliente = None
                self._actualizar_boton_conexion()
                self.txt_conexion.SetValue(str(exc))
            mostrar_error(self, str(exc), tr("No se pudo aplicar"))
            return None

    def refrescar_todo(self, anunciar: bool = False) -> None:
        if self.cliente is None:
            self.conectar(anunciar=anunciar)
            return
        try:
            self.catalogos = self.cliente.llamar("catalogos")
            self._poblar_catalogos()
            self.refrescar_estado(anunciar_error=True, forzar_sync=True)
            if anunciar:
                _hablar(tr("Datos y controles sincronizados con el juego."))
        except ErrorPuente as exc:
            self.cliente = None
            self._actualizar_boton_conexion()
            self.txt_conexion.SetValue(str(exc))

    def refrescar_estado(self, anunciar_error: bool = False, forzar_sync: bool = False) -> None:
        if self.cliente is None:
            return
        try:
            est = self.cliente.llamar("estado")
            self.estado = est
            en_partida = bool(est.get("en_partida"))
            if not en_partida:
                self.txt_conexion.SetValue(
                    tr("Conectado (pantalla: {pantalla}). Esperando a que empieces o cargues una partida.").format(
                        pantalla=est.get("pantalla")
                    )
                )
                return
            mapa = est.get("mapa", {})
            j = est.get("jugador", {})
            t = est.get("tiempo", {})
            estado_txt = tr("Conectado — {mapa} ({barrio}) | Día {dia} {hora} | Salud {salud}/{salud_max} | {dinero} € | {estrellas}★").format(
                mapa=mapa.get("nombre"),
                barrio=mapa.get("barrio"),
                dia=t.get("dia"),
                hora=t.get("hora_txt"),
                salud=j.get("salud"),
                salud_max=j.get("salud_max"),
                dinero=j.get("dinero"),
                estrellas=j.get("estrellas"),
            )
            if est.get("en_servidor") and est.get("trampas_servidor_permitidas"):
                estado_txt += tr(" | Servidor (trampas permitidas)")
            if self.txt_conexion.GetValue() != estado_txt:
                self.txt_conexion.SetValue(estado_txt)

            resumen = tr(
                "{nombre} {apellido} — Salud {salud}/{salud_max}, Blindaje {blindaje}\n"
                "Dinero: {dinero} € en mano, {banco} € en banco | Búsqueda: {estrellas} estrellas\n"
                "Ánimo {animo}, Prestigio {ciudadania}, Fama {reputacion} | Arma: {arma}\n"
                "Entidades vivas: {vehs} vehículos, {pers} personas"
            ).format(
                nombre=j.get("nombre"),
                apellido=j.get("apellido"),
                salud=j.get("salud"),
                salud_max=j.get("salud_max"),
                blindaje=j.get("blindaje"),
                dinero=j.get("dinero"),
                banco=j.get("banco"),
                estrellas=j.get("estrellas"),
                animo=j.get("animo"),
                ciudadania=j.get("ciudadania"),
                reputacion=j.get("reputacion"),
                arma=j.get("arma"),
                vehs=est.get("conteos", {}).get("vehiculos", 0),
                pers=est.get("conteos", {}).get("personas", 0),
            )
            if resumen != self._ultimo_resumen:
                self._ultimo_resumen = resumen
                self.txt_resumen_jug.SetValue(resumen)

            self._sincronizar_todo(forzar=forzar_sync)

            vehs = self.cliente.llamar("vehiculos.listar").get("vehiculos", [])
            self._actualizar_lista_vehiculos(vehs, forzar=forzar_sync)
            npcs = self.cliente.llamar("npcs.listar").get("personas", [])
            self._actualizar_lista_npcs(npcs, forzar=forzar_sync)
        except ErrorPuente as exc:
            self.cliente = None
            self._actualizar_boton_conexion()
            self.txt_conexion.SetValue(
                tr("Desconectado ({exc}). En multijugador el puente se anula salvo que el dueño del servidor habilite permitir_trampas.").format(
                    exc=exc
                )
            )
            if anunciar_error:
                mostrar_error(self, str(exc), tr("Error al actualizar"))

    def _poblar_catalogos(self) -> None:
        cat = self.catalogos
        armas = cat.get("armas", [])
        self._ids_armas = [a["id"] for a in armas]
        self.sel_arma.Set([tr("{nombre} ({id}, daño {dano})").format(nombre=a["nombre"], id=a["id"], dano=a["dano"]) for a in armas])
        if armas:
            self.sel_arma.SetSelection(0)
        self.sel_npc_arma.Set([tr("(por defecto)")] + [f"{a['nombre']} ({a['id']})" for a in armas])
        self.sel_npc_arma.SetSelection(0)

        objs = cat.get("objetos", [])
        self._ids_objetos = [o["id"] for o in objs]
        self.sel_objeto.Set([f"{o['nombre']} ({o['id']})" for o in objs])
        if objs:
            self.sel_objeto.SetSelection(0)

        vals = cat.get("objetos_valor", [])
        self._ids_valor = [v["id"] for v in vals]
        self.sel_valor.Set([f"{v['nombre']} ({v['valor']} €)" for v in vals])
        if vals:
            self.sel_valor.SetSelection(0)

        susts = cat.get("sustancias", [])
        self._ids_sust = [x["id"] for x in susts]
        self.sel_sustancia.Set([f"{x['nombre']} ({x['id']})" for x in susts] or [tr("(ninguna)")])
        self.sel_sustancia.SetSelection(0)

        prods = cat.get("productos", [])
        self._ids_prod = [x["id"] for x in prods]
        self.sel_producto.Set([f"{x['nombre']} ({x['id']})" for x in prods] or [tr("(ninguno)")])
        self.sel_producto.SetSelection(0)

        vehs = cat.get("vehiculos", [])
        self._ids_vehiculos = [v["id"] for v in vehs]
        etq_v = [f"{v['nombre']} ({v['id']} — {v['vel_max']} m/s)" for v in vehs]
        self.sel_modelo_veh.Set(etq_v)
        self.sel_pers_modelo.Set(etq_v)
        if vehs:
            self.sel_modelo_veh.SetSelection(0)
            self.sel_pers_modelo.SetSelection(0)

        mejs = cat.get("mejoras", {})
        self._ids_mejoras = list(mejs.keys())
        self.sel_veh_mejora.Set([tr("{nombre} ({k}, máx {niv})").format(nombre=v.get("nombre", k), k=k, niv=v.get("niveles", 3)) for k, v in mejs.items()])
        if self._ids_mejoras:
            self.sel_veh_mejora.SetSelection(0)

        tipos_e = cat.get("tipos_enemigo", [])
        self._ids_tipos_enemigo = [""] + [t["id"] for t in tipos_e]
        self.sel_npc_clase.Set([tr("(genérico)")] + [f"{t.get('nombre', t['id'])} ({t['id']})" for t in tipos_e])
        self.sel_npc_clase.SetSelection(0)

        bandas = [b["nombre"] for b in cat.get("bandas", [])]
        self._nombres_bandas = bandas
        self.sel_npc_banda.Set([tr("(ninguna)")] + bandas)
        self.sel_npc_banda.SetSelection(0)
        self.sel_rep_banda.Set([tr("Todas las bandas")] + bandas)
        self.sel_rep_banda.SetSelection(0)
        self.sel_ev_banda.Set(bandas or ["Los Calaveras"])
        self.sel_ev_banda.SetSelection(0)

        dias = cat.get("dias_azar", [])
        self._ids_dias = [d["id"] for d in dias]
        self.sel_dia_azar.Set([d["id"] for d in dias] or ["normal"])
        self.sel_dia_azar.SetSelection(0)

        mapas = cat.get("mapas", [])
        self._mapas = mapas
        self.sel_mapa.Set([f"{m['nombre']} ({m['id']})" for m in mapas])
        if mapas:
            self.sel_mapa.SetSelection(0)
            self._poblar_lugares()

        habs = cat.get("habilidades", {})
        if habs:
            self._ids_habs = list(habs.keys())
            self.sel_hab.Set([f"{v['nombre']} ({k})" for k, v in habs.items()])
            self.sel_hab.SetSelection(0)

    def _poblar_lugares(self) -> None:
        idx = self.sel_mapa.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_mapas", [])):
            return
        lugares = self._mapas[idx].get("lugares", [])
        filtro = self.txt_filtro_lugar.GetValue().strip().lower()
        filtrados = [l for l in lugares if not filtro or filtro in l["nombre"].lower() or filtro in l["tipo"].lower() or filtro in l["id"].lower()]
        self._lugares_filtrados = filtrados
        self.sel_lugar.Set([f"{l['nombre']} [{l['tipo']}]" for l in filtrados] or [tr("(sin coincidencias)")])
        self.sel_lugar.SetSelection(0)

    def _actualizar_lista_vehiculos(self, vehs: list[dict], forzar: bool = False) -> None:
        sel_id = self._veh_seleccionado_id()
        claves = [f"{v['id']}:{v['nombre']}:{int(v['salud'])}:{v['es_actual']}:{v['mio']}:{v['ia']}:{v.get('vel_max')}" for v in vehs]
        self._vehiculos_vivos = vehs
        if claves != self._ultimas_claves_veh:
            self._ultimas_claves_veh = claves
            etiquetas = [
                f"{tr('[ACTUAL] ') if v['es_actual'] else ''}{tr('[MÍO] ') if v['mio'] else ''}"
                f"{tr('{nombre} (#{id}, {salud}/{salud_max} HP, {dist} m, ia={ia})').format(nombre=v['nombre'], id=v['id'], salud=int(v['salud']), salud_max=int(v['salud_max']), dist=v['dist'], ia=v['ia'])}"
                for v in vehs
            ]
            self.lista_vehiculos.Set(etiquetas)
            if sel_id is not None:
                for i, v in enumerate(vehs):
                    if v["id"] == sel_id:
                        self.lista_vehiculos.SetSelection(i)
                        break
            elif vehs:
                self.lista_vehiculos.SetSelection(0)
        self._cargar_vehiculo_seleccionado(forzar=forzar)

    def _actualizar_lista_npcs(self, npcs: list[dict], forzar: bool = False) -> None:
        sel_id = self._npc_seleccionado_id()
        claves = [f"{n['id']}:{n['nombre']}:{int(n['salud'])}:{n['hostil']}:{n['muerto']}" for n in npcs]
        self._personas_vistas = npcs
        if claves != self._ultimas_claves_npc:
            self._ultimas_claves_npc = claves
            etiquetas = [
                f"{tr('[MUERTO] ') if n['muerto'] else ''}{tr('[HOSTIL] ') if n['hostil'] else ''}"
                f"{tr('{nombre} (#{id}, {tipo}, {salud} HP, {dist} m)').format(nombre=n['nombre'], id=n['id'], tipo=n['tipo'], salud=int(n['salud']), dist=n['dist'])}"
                for n in npcs
            ]
            self.lista_npcs.Set(etiquetas)
            if sel_id is not None:
                for i, n in enumerate(npcs):
                    if n["id"] == sel_id:
                        self.lista_npcs.SetSelection(i)
                        break
            elif npcs:
                self.lista_npcs.SetSelection(0)
        self._cargar_npc_seleccionado(forzar=forzar)

    # ------------------------------------------------------------------ sincs por selector
    def _sincronizar_habilidad_actual(self, forzar: bool = False) -> None:
        ids = getattr(self, "_ids_habs", [])
        idx = self.sel_hab.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(ids):
            return
        hab = ids[idx]
        datos_h = (self.estado.get("jugador", {}).get("hab") or {}).get(hab) or {}
        self._sinc_control(f"hab.{hab}", self.sp_hab_nivel, datos_h.get("nivel", 0), forzar)

    def _sincronizar_arma_actual(self, forzar: bool = False) -> None:
        ids = getattr(self, "_ids_armas", [])
        idx = self.sel_arma.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(ids):
            return
        aid = ids[idx]
        j = self.estado.get("jugador", {})
        armas = j.get("armas") or {}
        if aid in armas:
            ent = armas[aid]
            txt = tr("En inventario (EQUIPADA)") if j.get("arma") == aid else tr("En inventario")
            self._sinc_control("arma.txt", self.txt_arma_estado, txt, forzar)
            self._sinc_control(f"arma.{aid}.carg", self.sp_arma_cargador, ent.get("cargador", 0), forzar)
            self._sinc_control(f"arma.{aid}.res", self.sp_balas, ent.get("reserva", 0), forzar)
            self._sinc_control(f"arma.{aid}.sil", self.chk_silenciador, ent.get("silenciador", False), forzar)
            self._sinc_control(f"arma.{aid}.amp", self.chk_ampliado, ent.get("ampliado", False), forzar)
        else:
            cat_a = next((a for a in self.catalogos.get("armas", []) if a["id"] == aid), {})
            self._sinc_control("arma.txt", self.txt_arma_estado, tr("No la tienes todavía"), forzar)
            self._sinc_control(f"arma.{aid}.carg", self.sp_arma_cargador, cat_a.get("cargador", 0), forzar)
            self._sinc_control(f"arma.{aid}.res", self.sp_balas, 200, forzar)
            self._sinc_control(f"arma.{aid}.sil", self.chk_silenciador, False, forzar)
            self._sinc_control(f"arma.{aid}.amp", self.chk_ampliado, False, forzar)

    def _sincronizar_objeto_actual(self, forzar: bool = False) -> None:
        ids = getattr(self, "_ids_objetos", [])
        idx = self.sel_objeto.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(ids):
            return
        oid = ids[idx]
        cant = (self.estado.get("jugador", {}).get("objetos") or {}).get(oid, 0)
        self._sinc_control(f"obj.{oid}", self.sp_obj_cant, cant, forzar)

    def _sincronizar_sustancia_actual(self, forzar: bool = False) -> None:
        ids = getattr(self, "_ids_sust", [])
        idx = self.sel_sustancia.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(ids):
            return
        sid = ids[idx]
        cant = (self.estado.get("jugador", {}).get("sustancias") or {}).get(sid, 0)
        self._sinc_control(f"sust.{sid}", self.sp_sust_cant, cant, forzar)

    def _sincronizar_rep_banda_actual(self, forzar: bool = False) -> None:
        idx = self.sel_rep_banda.GetSelection()
        if idx == wx.NOT_FOUND or idx == 0:
            return
        bandas = getattr(self, "_nombres_bandas", [])
        if (idx - 1) >= len(bandas):
            return
        banda = bandas[idx - 1]
        rep = (self.estado.get("jugador", {}).get("rep_bandas") or {}).get(banda, 0)
        self._sinc_control(f"rep.{banda}", self.sp_rep_val, int(round(float(rep))), forzar)

    def _sincronizar_mejora_vehiculo(self, forzar: bool = False) -> None:
        v = self._vehiculo_activo_edicion()
        ids = getattr(self, "_ids_mejoras", [])
        idx = self.sel_veh_mejora.GetSelection()
        if v is None or idx == wx.NOT_FOUND or idx >= len(ids):
            return
        mid = ids[idx]
        mejs = self.catalogos.get("mejoras", {})
        tope = int((mejs.get(mid) or {}).get("niveles", 3))
        self.sp_veh_mejora_niv.SetRange(0, tope)
        actual = int((v.get("mejoras") or {}).get(mid, 0))
        self._sinc_control(f"veh.{v['id']}.mej.{mid}", self.sp_veh_mejora_niv, actual, forzar)

    # ------------------------------------------------------------------ acciones UI
    def _toggle_cfg(self, clave: str, valor: bool) -> None:
        msg = tr("{clave} activado.").format(clave=clave) if valor else tr("{clave} desactivado.").format(clave=clave)
        self._ejecutar("cfg.set", {"clave": clave, "valor": bool(valor)}, msg)

    def _accion_jugador(self, accion: str, voz: str) -> None:
        self._ejecutar("jugador.set", {"accion": accion}, voz)

    def _fijar_habilidad(self) -> None:
        ids = getattr(self, "_ids_habs", ["conduccion", "punteria", "resistencia", "pesca"])
        idx = self.sel_hab.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(ids):
            return
        hab = ids[idx]
        niv = self.sp_hab_nivel.GetValue()
        self._ejecutar("jugador.habilidad", {"habilidad": hab, "nivel": niv}, tr("Habilidad {hab} al nivel {niv}.").format(hab=hab, niv=niv))

    def _accion_arma(self, accion: str) -> None:
        idx = self.sel_arma.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_ids_armas", [])):
            return
        aid = self._ids_armas[idx]
        self._ejecutar(
            "inventario.arma",
            {
                "accion": accion,
                "arma_id": aid,
                "cargador": self.sp_arma_cargador.GetValue(),
                "balas": self.sp_balas.GetValue(),
                "reserva": self.sp_balas.GetValue(),
                "silenciador": self.chk_silenciador.GetValue(),
                "ampliado": self.chk_ampliado.GetValue(),
            },
            tr("Arma {aid}: acción {accion} aplicada.").format(aid=aid, accion=accion),
        )

    def _dar_objeto(self, fijar: bool = False) -> None:
        idx = self.sel_objeto.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_ids_objetos", [])):
            return
        oid = self._ids_objetos[idx]
        self._ejecutar(
            "inventario.objeto",
            {"tipo": "objeto", "id": oid, "cantidad": self.sp_obj_cant.GetValue(), "fijar": fijar},
            tr("Objeto {oid} actualizado.").format(oid=oid),
        )

    def _dar_valor(self) -> None:
        idx = self.sel_valor.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_ids_valor", [])):
            return
        vid = self._ids_valor[idx]
        self._ejecutar("inventario.objeto", {"tipo": "valor", "id": vid, "cantidad": 1}, tr("Guardado en mochila: {vid}.").format(vid=vid))

    def _dar_sustancia(self, fijar: bool = False, cantidad: int = 10) -> None:
        idx = self.sel_sustancia.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_ids_sust", [])):
            return
        sid = self._ids_sust[idx]
        self._ejecutar(
            "inventario.objeto",
            {"tipo": "sustancia", "id": sid, "cantidad": cantidad, "fijar": fijar},
            tr("Sustancia {sid} actualizada.").format(sid=sid),
        )

    def _dar_producto(self) -> None:
        idx = self.sel_producto.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_ids_prod", [])):
            return
        pid = self._ids_prod[idx]
        self._ejecutar(
            "inventario.objeto",
            {"tipo": "producto", "id": pid, "cantidad": self.sp_prod_cant.GetValue()},
            tr("Añadido {pid} al bolsillo.").format(pid=pid),
        )

    def _crear_vehiculo(self) -> None:
        idx = self.sel_modelo_veh.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_ids_vehiculos", [])):
            return
        mid = self._ids_vehiculos[idx]
        self._ejecutar(
            "vehiculos.crear",
            {
                "modelo_id": mid,
                "nombre": self.txt_veh_nombre.GetValue().strip(),
                "hacer_mio": self.chk_veh_mio.GetValue(),
                "subir_ahora": self.chk_veh_subir.GetValue(),
                "mejoras_max": self.chk_veh_mejoras_max.GetValue(),
            },
            tr("Vehículo {mid} generado.").format(mid=mid),
        )

    def _veh_seleccionado_id(self) -> int | None:
        idx = self.lista_vehiculos.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(self._vehiculos_vivos):
            return None
        return int(self._vehiculos_vivos[idx]["id"])

    def _vehiculo_activo_edicion(self) -> dict | None:
        idx = self.lista_vehiculos.GetSelection()
        if idx != wx.NOT_FOUND and idx < len(self._vehiculos_vivos):
            return self._vehiculos_vivos[idx]
        return next((v for v in self._vehiculos_vivos if v.get("es_actual")), None) or (self._vehiculos_vivos[0] if self._vehiculos_vivos else None)

    def _cargar_vehiculo_seleccionado(self, forzar: bool = False) -> None:
        v = self._vehiculo_activo_edicion()
        if v is None:
            self._sinc_control("veh.info", self.txt_veh_ed_info, tr("(ninguno)"), forzar)
            return
        vid = v["id"]
        self._sinc_control("veh.info", self.txt_veh_ed_info, f"#{vid} — {v.get('nombre')} ({v.get('modelo_id')})", forzar)
        self._sinc_control(f"veh.{vid}.nombre", self.txt_veh_ed_nombre, v.get("nombre", ""), forzar)
        self._sinc_control(f"veh.{vid}.vel", self.sp_veh_vel, int(round(float(v.get("vel_max", 25.0)))), forzar)
        self._sinc_control(f"veh.{vid}.acel", self.sp_veh_acel, int(round(float(v.get("acel", 6.0)))), forzar)
        self._sinc_control(f"veh.{vid}.freno", self.sp_veh_freno, int(round(float(v.get("freno", 12.0)))), forzar)
        self._sinc_control(f"veh.{vid}.salud", self.sp_veh_salud, int(round(float(v.get("salud", 100.0)))), forzar)
        self._sinc_control(f"veh.{vid}.salud_max", self.sp_veh_salud_max, int(round(float(v.get("salud_max", 100.0)))), forzar)
        self._sinc_control(f"veh.{vid}.hostil", self.chk_veh_hostil, v.get("hostil", False), forzar)
        self._sinc_control(f"veh.{vid}.cerrado", self.chk_veh_cerrado, v.get("cerrado", False), forzar)
        ia_str = str(v.get("ia")) if v.get("ia") is not None else "None"
        ia_idx = _IDS_VEH_IA.index(ia_str) if ia_str in _IDS_VEH_IA else 0
        clave_ia = f"veh.{vid}.ia"
        previo_ia = self._valores_juego.get(clave_ia, "__SIN_VALOR__")
        self._valores_juego[clave_ia] = ia_str
        if (forzar or (ia_str != previo_ia and not _tiene_foco(self.sel_veh_ia))) and self.sel_veh_ia.GetSelection() != ia_idx:
            self.sel_veh_ia.SetSelection(ia_idx)
        self._sincronizar_mejora_vehiculo(forzar)

    def _accion_vehiculo(self, accion: str, voz: str) -> None:
        vid = self._veh_seleccionado_id()
        if vid is None:
            mostrar_error(self, tr("Selecciona primero un vehículo de la lista."), tr("Sin selección"))
            return
        self._ejecutar("vehiculos.accion", {"id": vid, "accion": accion}, voz)

    def _editar_vehiculo(self, payload: dict, voz: str) -> None:
        vid = self._veh_seleccionado_id()
        if vid is None:
            mostrar_error(self, tr("Selecciona primero un vehículo de la lista."), tr("Sin selección"))
            return
        datos = dict(payload, id=vid)
        self._ejecutar("vehiculos.editar", datos, voz)

    def _guardar_specs_vehiculo(self) -> None:
        v = self._vehiculo_activo_edicion()
        if v is None:
            mostrar_error(self, tr("No hay ningún vehículo seleccionado."), tr("Sin selección"))
            return
        ia_idx = self.sel_veh_ia.GetSelection()
        ia_val = _IDS_VEH_IA[ia_idx] if ia_idx != wx.NOT_FOUND and ia_idx < len(_IDS_VEH_IA) else "None"
        self._ejecutar(
            "vehiculos.editar",
            {
                "id": v["id"],
                "solo_este": self.chk_veh_solo_este.GetValue(),
                "nombre": self.txt_veh_ed_nombre.GetValue().strip(),
                "salud": self.sp_veh_salud.GetValue(),
                "salud_max": self.sp_veh_salud_max.GetValue(),
                "ia": ia_val,
                "hostil": self.chk_veh_hostil.GetValue(),
                "cerrado": self.chk_veh_cerrado.GetValue(),
                "specs": {
                    "vel_max": self.sp_veh_vel.GetValue(),
                    "acel": self.sp_veh_acel.GetValue(),
                    "freno": self.sp_veh_freno.GetValue(),
                },
            },
            tr("Especificaciones del vehículo aplicadas."),
        )

    def _aplicar_mejora_vehiculo(self) -> None:
        v = self._vehiculo_activo_edicion()
        ids = getattr(self, "_ids_mejoras", [])
        idx = self.sel_veh_mejora.GetSelection()
        if v is None or idx == wx.NOT_FOUND or idx >= len(ids):
            return
        mid = ids[idx]
        mejs = dict(v.get("mejoras") or {})
        mejs[mid] = self.sp_veh_mejora_niv.GetValue()
        self._ejecutar("vehiculos.editar", {"id": v["id"], "mejoras": mejs}, tr("Mejora {mid} aplicada.").format(mid=mid))

    def _crear_npc(self) -> None:
        m_idx = self.sel_npc_modo.GetSelection()
        modo_val = _IDS_NPC_MODO[m_idx] if m_idx != wx.NOT_FOUND and m_idx < len(_IDS_NPC_MODO) else "enemigo"
        c_idx = self.sel_npc_clase.GetSelection()
        clase = self._ids_tipos_enemigo[c_idx] if c_idx != wx.NOT_FOUND and c_idx < len(getattr(self, "_ids_tipos_enemigo", [])) else ""
        b_idx = self.sel_npc_banda.GetSelection()
        banda = self._nombres_bandas[b_idx - 1] if b_idx > 0 and (b_idx - 1) < len(getattr(self, "_nombres_bandas", [])) else None
        a_idx = self.sel_npc_arma.GetSelection()
        arma = self._ids_armas[a_idx - 1] if a_idx > 0 and (a_idx - 1) < len(getattr(self, "_ids_armas", [])) else None
        self._ejecutar(
            "npcs.crear",
            {
                "modo": modo_val,
                "clase": clase,
                "banda": banda,
                "arma": arma,
                "cantidad": self.sp_npc_cant.GetValue(),
                "salud": self.sp_npc_salud.GetValue(),
                "en_vehiculo": self.chk_npc_veh.GetValue(),
                "hostil": self.chk_npc_hostil.GetValue(),
            },
            tr("NPC generado en la partida."),
        )

    def _npc_seleccionado_id(self) -> int | None:
        idx = self.lista_npcs.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(self._personas_vistas):
            return None
        return int(self._personas_vistas[idx]["id"])

    def _cargar_npc_seleccionado(self, forzar: bool = False) -> None:
        idx = self.lista_npcs.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(self._personas_vistas):
            return
        n = self._personas_vistas[idx]
        nid = n["id"]
        self._sinc_control(f"npc.{nid}.nombre", self.txt_npc_ed_nombre, n.get("nombre", ""), forzar)
        self._sinc_control(f"npc.{nid}.salud", self.sp_npc_ed_salud, int(max(0, n.get("salud", 50))), forzar)
        self._sinc_control(f"npc.{nid}.punt", self.sp_npc_ed_punt, int(round(float(n.get("punteria", 0.42)) * 100)), forzar)
        est_str = str(n.get("estado", "quieto"))
        est_idx = _IDS_NPC_ESTADO.index(est_str) if est_str in _IDS_NPC_ESTADO else 1
        clave_est = f"npc.{nid}.estado"
        previo_est = self._valores_juego.get(clave_est, "__SIN_VALOR__")
        self._valores_juego[clave_est] = est_str
        if (forzar or (est_str != previo_est and not _tiene_foco(self.sel_npc_ed_estado))) and self.sel_npc_ed_estado.GetSelection() != est_idx:
            self.sel_npc_ed_estado.SetSelection(est_idx)
        self._sinc_control(f"npc.{nid}.hostil", self.chk_npc_ed_hostil, n.get("hostil", False), forzar)
        conf = (n.get("ficha") or {}).get("confianza", 0)
        self._sinc_control(f"npc.{nid}.conf", self.sp_npc_ed_conf, int(conf or 0), forzar)

    def _aplicar_npc(self) -> None:
        pid = self._npc_seleccionado_id()
        if pid is None:
            mostrar_error(self, tr("Selecciona primero una persona de la lista."), tr("Sin selección"))
            return
        e_idx = self.sel_npc_ed_estado.GetSelection()
        est_val = _IDS_NPC_ESTADO[e_idx] if e_idx != wx.NOT_FOUND and e_idx < len(_IDS_NPC_ESTADO) else "quieto"
        self._ejecutar(
            "npcs.editar",
            {
                "id": pid,
                "nombre": self.txt_npc_ed_nombre.GetValue().strip(),
                "salud": self.sp_npc_ed_salud.GetValue(),
                "punteria": round(self.sp_npc_ed_punt.GetValue() / 100.0, 2),
                "estado": est_val,
                "hostil": self.chk_npc_ed_hostil.GetValue(),
                "confianza": self.sp_npc_ed_conf.GetValue(),
            },
            tr("Atributos del NPC actualizados."),
        )

    def _accion_npc(self, accion: str, voz: str) -> None:
        pid = self._npc_seleccionado_id()
        if pid is None:
            mostrar_error(self, tr("Selecciona primero una persona de la lista."), tr("Sin selección"))
            return
        self._ejecutar("npcs.accion", {"id": pid, "accion": accion}, voz)

    def _fijar_rep_banda(self, valor: int | None = None) -> None:
        idx = self.sel_rep_banda.GetSelection()
        if idx == wx.NOT_FOUND:
            return
        banda = "__todas__" if idx == 0 else self._nombres_bandas[idx - 1]
        val = self.sp_rep_val.GetValue() if valor is None else int(valor)
        self._ejecutar("policia.set", {"rep_banda": {"banda": banda, "valor": val}}, tr("Reputación de banda fijada a {val}.").format(val=val))

    def _lanzar_persecucion(self) -> None:
        idx = self.sel_pers_modelo.GetSelection()
        mid = self._ids_vehiculos[idx] if idx != wx.NOT_FOUND and idx < len(getattr(self, "_ids_vehiculos", [])) else "deportivo"
        self._ejecutar(
            "eventos.lanzar",
            {"tipo": "persecucion_vehiculo", "modelo_id": mid, "vel_obj": self.sp_pers_vel.GetValue(), "marcar_gps": True},
            tr("Persecución lanzada y marcada en tu GPS."),
        )

    def _lanzar_guerra(self, tipo: str) -> None:
        idx = self.sel_ev_banda.GetSelection()
        banda = self._nombres_bandas[idx] if idx != wx.NOT_FOUND and idx < len(getattr(self, "_nombres_bandas", [])) else None
        self._ejecutar("eventos.lanzar", {"tipo": tipo, "banda": banda}, tr("Enfrentamiento de banda iniciado."))

    def _teletransportar(self) -> None:
        lugares = getattr(self, "_lugares_filtrados", [])
        idx = self.sel_lugar.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(lugares):
            return
        l = lugares[idx]
        self._ejecutar("jugador.teletransportar", {"lugar_id": l["id"]}, tr("Teletransportado a {lugar}.").format(lugar=l["nombre"]))

    def _aplicar_tiempo(self) -> None:
        idx_d = self.sel_dia_azar.GetSelection()
        dia_azar = self._ids_dias[idx_d] if idx_d != wx.NOT_FOUND and idx_d < len(getattr(self, "_ids_dias", [])) else None
        self._ejecutar(
            "mundo.set",
            {
                "hora": self.sp_hora.GetValue(),
                "dia": self.sp_dia.GetValue(),
                "lluvia": self.chk_lluvia.GetValue(),
                "dia_azar": dia_azar,
            },
            tr("Hora, día y clima actualizados."),
        )

    def _leer_inspector(self) -> None:
        if self.cliente is None:
            return
        try:
            res = self.cliente.llamar("inspector.leer", objetivo=self.sel_insp_obj.GetStringSelection())
            self._inspector_campos = res.get("campos", {})
            self._filtrar_inspector()
        except ErrorPuente as exc:
            mostrar_error(self, str(exc), tr("Inspector"))

    def _filtrar_inspector(self) -> None:
        filtro = self.txt_insp_filtro.GetValue().strip().lower()
        claves = [k for k in sorted(self._inspector_campos.keys()) if not filtro or filtro in k.lower()]
        self._inspector_claves = claves
        self.lista_insp.Set([f"{k} = {json.dumps(self._inspector_campos[k], ensure_ascii=False)}" for k in claves])
        if claves:
            self.lista_insp.SetSelection(0)
            self._seleccionar_clave_inspector()

    def _seleccionar_clave_inspector(self) -> None:
        idx = self.lista_insp.GetSelection()
        if idx == wx.NOT_FOUND or idx >= len(getattr(self, "_inspector_claves", [])):
            return
        clave = self._inspector_claves[idx]
        val = self._inspector_campos[clave]
        self.txt_insp_clave.SetValue(clave)
        self.txt_insp_valor.SetValue(val if isinstance(val, str) else json.dumps(val, ensure_ascii=False))

    def _error_inspector(self, mensaje: str, titulo: str, foco: wx.Window) -> None:
        self.txt_insp_estado.SetValue(mensaje)
        self.SetStatusText(mensaje)
        _hablar(mensaje)
        mostrar_error(self, mensaje, titulo)
        foco.SetFocus()

    def _escribir_inspector(self) -> None:
        objetivo = self.sel_insp_obj.GetStringSelection()
        raw_clave = self.txt_insp_clave.GetValue()
        raw_val = self.txt_insp_valor.GetValue()
        try:
            clave = validar_clave_inspector(objetivo, raw_clave)
        except ValueError as exc:
            self._error_inspector(str(exc), tr("Error en el Inspector"), self.txt_insp_clave)
            return

        campos = getattr(self, "_inspector_campos", {}) or {}
        existe = clave in campos
        if campos and not existe:
            if not (objetivo == "vehiculo_actual" and clave in ("vel_max", "acel", "freno", "tono")):
                self._error_inspector(
                    tr("El campo {clave} no está disponible en el Inspector de {objetivo}. No se modificó ni añadió nada.").format(
                        clave=repr(clave), objetivo=objetivo
                    ),
                    tr("Campo no editable en el Inspector"),
                    self.txt_insp_clave,
                )
                return

        ref = campos.get(clave) if existe else None
        try:
            parsear_valor_inspector(raw_val, ref, es_nuevo=not existe, objetivo=objetivo)
        except ValueError as exc:
            self._error_inspector(str(exc), tr("Error de sintaxis en el Inspector"), self.txt_insp_valor)
            return

        res = self._ejecutar(
            "inspector.escribir",
            {"objetivo": objetivo, "clave": clave, "valor": raw_val},
            tr("Campo {clave} actualizado.").format(clave=clave),
        )
        if res is not None:
            aviso_resp = tr(" (copia de seguridad creada)") if res.get("respaldo") else ""
            self.txt_insp_estado.SetValue(
                tr("Aplicado correctamente: {clave} = {valor}{aviso}").format(
                    clave=clave, valor=json.dumps(res.get("valor"), ensure_ascii=False), aviso=aviso_resp
                )
            )
            self._leer_inspector()
        elif self._ultimo_error_puente:
            self.txt_insp_estado.SetValue(self._ultimo_error_puente)
            self.txt_insp_valor.SetFocus()


def ejecutar() -> None:
    app = wx.App(False)
    try:
        from juego import i18n
        if i18n.actual() == "es":
            app._idioma = fijar_idioma_espanol()
    except Exception:
        pass
    wx.HelpProvider.Set(wx.SimpleHelpProvider())
    v = VentanaTrampas()
    v.Show()
    app.MainLoop()
