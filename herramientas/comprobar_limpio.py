"""Comprueba que una carpeta compilada está lista para distribuir: completa y sin nada personal.

    .venv\\Scripts\\python.exe herramientas\\comprobar_limpio.py dist\\PuertoBravo

Sale con código 1 si encuentra partidas, opciones, registros, música personal o si falta algo necesario.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


MODS_DE_SERIE = ("costa_dorada.pbm", "oficios_y_recados.pbm", "valdeolmos.pbm", "motor_y_asfalto.pbm",
                 "penas_altas.pbm", "isla_de_los_vientos.pbm", "noches_de_neon.pbm", "bahia_del_ocaso.pbm", "el_diablo.pbm")
# La documentación que se reparte es para quien juega: nada de programación.
SOLO_DESARROLLO = (("data", "docs", "crear_mods.html"), ("data", "actualizacion"), ("data", "logs"), ("data", "error.log"), ("data", "comunidad_descargada.json"), ("herramientas",), ("pruebas",))


def rutas_de_este_equipo(raiz):
    """Ningún módulo compilado debe llevar dentro la ruta del equipo donde se compiló: saldría en los registros de los jugadores."""
    proyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    marcas = [m.encode("utf-8") for m in {proyecto, proyecto.replace("\\", "/"), os.path.expanduser("~")} if len(m) > 3]
    marcas += [m.lower() for m in marcas]
    malos = []
    for base, _, archivos in os.walk(raiz):
        for a in archivos:
            if a.endswith((".pyc", ".zip")):
                try:
                    with open(os.path.join(base, a), "rb") as f:
                        datos = f.read()
                except OSError:
                    continue
                if any(m in datos or m in datos.lower() for m in marcas):
                    malos.append(os.path.relpath(os.path.join(base, a), raiz))
    if malos:
        return [f"{len(malos)} módulos llevan dentro rutas de este equipo, por ejemplo {malos[0]}"]
    return []


def servidor_completo_y_limpio(raiz):
    """La carpeta del servidor trae todo lo necesario para montarlo de cualquier manera, con el ejemplo de configuración y
    la guía al día, y nada de nadie: ni configuración, ni datos, ni certificados, ni claves."""
    from herramientas import preparar_carpeta_servidor as carpeta
    problemas = carpeta.comprobar(raiz)
    if os.path.exists(os.path.join(raiz, "servidor_despliegue")):
        problemas.append("Sobra la carpeta servidor_despliegue: lo del servidor va ahora en la carpeta servidor")
    for base, dirs, archivos in os.walk(raiz):               # en ningún sitio de lo que se reparte
        for nombre in dirs + archivos:
            if nombre in ("datos_servidor", "servidor.conf", "puertobravo.db", "firma_ed25519.key", "certificado.pem", "llave.pem", "claves"):
                problemas.append("Dato de un servidor o clave que no debe repartirse: " + os.path.relpath(os.path.join(base, nombre), raiz))
    return problemas


def comprobar(raiz):
    problemas = []
    data = os.path.join(raiz, "data")

    def hay(*partes):
        return os.path.exists(os.path.join(raiz, *partes))

    for necesario in (("PuertoBravo.exe",), ("EditorMods.exe",), ("data", "datos", "ciudad.pbd"), ("data", "docs", "manual_es.html"),
                      ("data", "docs", "teclas_es.html"), ("data", "docs", "cambiar_sonidos_es.html"), ("data", "docs", "editor_mods_es.html"),
                      ("data", "docs", "novedades_es.html"), ("data", "docs", "servidor_es.html"),
                      ("data", "docs", "manual_en.html"), ("data", "docs", "teclas_en.html"), ("data", "docs", "cambiar_sonidos_en.html"),
                      ("data", "docs", "editor_mods_en.html"), ("data", "docs", "novedades_en.html"), ("data", "docs", "servidor_en.html"),
                      ("data", "idiomas", "en", "textos.json"), ("PuertoBravoServidor.exe",), ("PuertoBravoServidorPanel.exe",),
                      ("lib", "servidor", "mundo.json"), ("lib", "servidor", "opciones.pyc"), ("lib", "panel_servidor"), ("data", "sonidos", "por_defecto"), ("data", "sonidos", "realista"), ("data", "sonidos", "alternativo"), ("data", "sonidos", "retro"),
                      ("data", "radio"), ("data", "musica"), ("lib", "numpy"), ("lib_antiguo", "numpy"), ("lib", "soft_oal.dll"), ("LICENCIA_OpenAL_Soft.txt",)) + tuple(("data", "mods", m) for m in MODS_DE_SERIE):
        if not hay(*necesario):
            problemas.append("Falta " + os.path.join(*necesario))
    problemas += rutas_de_este_equipo(raiz)
    problemas += servidor_completo_y_limpio(raiz)
    for sobra in SOLO_DESARROLLO:
        if hay(*sobra):
            problemas.append("Es solo para desarrollo y no debe repartirse: " + os.path.join(*sobra))
    for carpeta in ("partidas", "config", os.path.join("radio", "mi_musica")):
        ruta = os.path.join(data, carpeta)
        if os.path.isdir(ruta):
            for base, _, archivos in os.walk(ruta):
                for f in archivos:
                    problemas.append("Dato personal: " + os.path.relpath(os.path.join(base, f), raiz))
    for base, dirs, archivos in os.walk(raiz):
        for d in dirs:
            if d in ("partidas_pruebas", "__pycache__") and base.startswith(data):
                problemas.append("Sobra la carpeta " + os.path.relpath(os.path.join(base, d), raiz))
        for f in archivos:
            if f.lower().endswith((".log", ".bak", ".tmp")):
                problemas.append("Sobra " + os.path.relpath(os.path.join(base, f), raiz))
    # sonidos en FLAC (sin pérdida) y voces en data\voces, por historias: nada de los formatos y carpetas anteriores
    for base, _, archivos in os.walk(os.path.join(data, "sonidos")):
        for f in archivos:
            if f.lower().endswith(".wav"):
                problemas.append("Sonido en el formato anterior, debería ser FLAC: " + os.path.relpath(os.path.join(base, f), raiz))
    if os.path.isdir(os.path.join(data, "voces_serie")):
        problemas.append("Sobra la carpeta de voces de versiones anteriores: " + os.path.join("data", "voces_serie"))
    # las voces viajan en data\datos\voces_puente y el juego las coloca al arrancar: en data\voces no va nada
    puente = os.path.join(data, "datos", "voces_puente")
    if os.path.isdir(os.path.join(puente, "propias")) or os.path.isdir(os.path.join(data, "voces", "propias")):
        problemas.append("Voces personales: una carpeta propias entre las voces")
    if os.path.isdir(os.path.join(data, "voces")) and any(archivos for _, _, archivos in os.walk(os.path.join(data, "voces"))):
        problemas.append("Hay voces en data\\voces: deben ir solo en data\\datos\\voces_puente")
    if os.path.isdir(os.path.join(data, "voces_generadas")):
        problemas.append("Voces generadas para un personaje propio: " + os.path.join("data", "voces_generadas"))
    # una carpeta por historia y por idioma: historia_principal_es, historia_principal_en...
    for cod, deben in (("es", ("m01_1_1", "m01_1_1@alex", "m01_1_2@cris_m")), ("en", ("m01_1_1",)), ("pl", ("m01_1_1", "m01_1_1@alex"))):
        principal = os.path.join(puente, "historia_principal_" + cod)
        if not os.path.isdir(principal):
            problemas.append("Faltan las voces de la historia principal en " + cod + ": " + principal)
            continue
        nombres = {os.path.splitext(f)[0].lower() for f in os.listdir(principal)}
        if len(nombres) < 900:
            problemas.append("Faltan voces de la historia principal en " + cod + ": solo hay " + str(len(nombres)))
        for hace_falta in deben:
            if hace_falta not in nombres:
                problemas.append("Falta la voz " + hace_falta + " de la historia principal en " + cod + ": las de esta versión llevan una por personaje y género")
    if os.path.isdir(puente) and any(not os.path.isdir(os.path.join(puente, d)) or not d.rsplit("_", 1)[-1] in ("es", "en", "pl") for d in os.listdir(puente)):
        problemas.append("Hay en las voces carpetas sin idioma en el nombre: " + ", ".join(d for d in os.listdir(puente) if d.rsplit("_", 1)[-1] not in ("es", "en", "pl")))
    if not os.path.exists(os.path.join(data, "phonon", "reparto_en.json")) or not os.path.isdir(os.path.join(data, "phonon", "voces_en")):
        problemas.append("Faltan las voces inglesas del generador del personaje propio: data\\phonon\\voces_en y reparto_en.json")
    for n in ("config.json", "tokenizer.json", "model.q8.gguf", "reparto.json", "LICENCIA.txt"):
        if not os.path.exists(os.path.join(data, "phonon", n)):
            problemas.append("Falta el generador de voces: " + os.path.join("data", "phonon", n))
    if not hay("LICENCIA_Phonon_Gradium.txt"):
        problemas.append("Falta LICENCIA_Phonon_Gradium.txt")
    # cuántos sonidos tiene el juego lo dicen los de serie del código fuente: así no hay que tocar esto en cada versión
    def _sonidos(ruta):
        return {os.path.splitext(f)[0] for f in os.listdir(ruta) if f.lower().endswith((".flac", ".ogg", ".wav", ".mp3"))}
    fuente = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sonidos", "por_defecto")
    esperados = _sonidos(fuente) if os.path.isdir(fuente) else None
    for pack in ("por_defecto", "realista", "alternativo", "retro", "envolvente"):
        ruta = os.path.join(data, "sonidos", pack)
        if os.path.isdir(ruta) and esperados:
            tiene = _sonidos(ruta)
            if tiene != esperados:
                problemas.append(f"El pack {pack} tiene {len(tiene)} sonidos y deberían ser {len(esperados)}"
                                 + (": faltan " + ", ".join(sorted(esperados - tiene)[:8]) if esperados - tiene else "")
                                 + (": sobran " + ", ".join(sorted(tiene - esperados)[:8]) if tiene - esperados else ""))
    mods = os.path.join(data, "mods")
    if os.path.isdir(mods):
        for f in os.listdir(mods):
            if not (f.upper().startswith(("LEEME", "README")) or f in MODS_DE_SERIE):
                problemas.append("Mod personal: " + os.path.join("data", "mods", f))
    # los datos del juego y los mods deben ir protegidos
    from juego import cifrado
    for sub in ("datos", "mods", "sonidos", "radio", "musica", "docs"):
        for base, _, archivos in os.walk(os.path.join(data, sub)):
            for f in archivos:
                ruta = os.path.join(base, f)
                if f.lower().endswith((".json", ".json.desactivado")):
                    problemas.append("Sin proteger, sigue siendo un .json: " + os.path.relpath(ruta, raiz))
                elif f.lower().endswith((".pbd", ".pbm")):
                    if not cifrado.esta_cifrado(ruta):
                        problemas.append("Sin proteger: " + os.path.relpath(ruta, raiz))
                    else:
                        try:
                            cifrado.leer_json(ruta)
                        except Exception as e:
                            problemas.append(f"No se puede leer {os.path.relpath(ruta, raiz)}: {e}")
    return problemas


if __name__ == "__main__":
    carpeta = sys.argv[1] if len(sys.argv) > 1 else os.path.join("dist", "PuertoBravo")
    fallos = comprobar(carpeta)
    for p in fallos:
        print("  " + p)
    if fallos:
        sys.exit(1)
    print("  Compilacion limpia y completa.")
