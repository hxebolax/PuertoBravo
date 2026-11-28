"""Monta los packs de sonidos a partir de las colecciones libres descargadas en adjuntos/fuentes.

    .venv\\Scripts\\python.exe herramientas\\crear_packs.py            monta los packs en adjuntos/packs
    .venv\\Scripts\\python.exe herramientas\\crear_packs.py instalar   y además los copia a data/sonidos
    .venv\\Scripts\\python.exe herramientas\\crear_packs.py anadir hacha disparo_corredera
                                        añade solo esos sonidos a los packs ya instalados en data/sonidos, sin rehacerlos

Cada pack es una tabla: sonido del juego -> archivo de una colección y cómo recortarlo.
Para añadir o cambiar un sonido basta con tocar su línea y volver a ejecutar.
El volumen no hace falta ajustarlo aquí: el juego iguala cada sonido al nivel del original.

Formas de recortar:
    ("carpeta", "archivo")                    entero, quitando el silencio de los extremos
    ("carpeta", "archivo", {"dur": 0.3})      como mucho esa duración, con fundido al final
    ("carpeta", "archivo", {"golpe": 0.6})    desde el primer golpe fuerte (grabaciones con varios disparos)
    ("carpeta", "archivo", {"bucle": 6.0, "desde": 2.0})   tramo que se repite sin corte
    ("carpeta", "archivo", {"desde": 2.0, "dur": 0.6})     una toma de una grabación que trae varias seguidas
    ... {"dur": 2.4, "entrada": 0.1, "fundido": 0.3}       con la entrada y la salida más suaves (ruidos continuos que se cortan)
    ... {"dur": 0.5, "veces": (0.0, 0.42, 0.72)}           la misma toma repetida en esos instantes (tres golpes de un tambor)
    ... {"dur": 2.4, "mezcla": [(col, archivo, {op}, t0, ganancia), ...]}
                                              encima, otras grabaciones en esos instantes (la gente que grita a la vez)
"""
import json
import os
import shutil
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from juego import rutas, sintesis          # noqa: E402

SR = sintesis.SR
FUENTES = os.path.join(rutas.base(), "adjuntos", "fuentes")
DESTINO = os.path.join(rutas.base(), "adjuntos", "packs")

# colección: (carpeta dentro de adjuntos/fuentes, nombre, página de origen). Todas con licencia CC0.
COL = {
    "FS162": ("freesound_162", "Freesound, grabaciones CC0 de gecop, Bidone, ccovi, 16HPanskaWillheimova_Sara, TRP, Fission9, swordofkings128, TicAshfield y freemaster2", "https://freesound.org"),
    "K": ("kenney_impact-sounds/Audio", "Impact Sounds, de Kenney", "https://kenney.nl/assets/impact-sounds"),
    "RK": ("RPGsounds_Kenney/OGG", "50 RPG sound effects, de Kenney", "https://opengameart.org/content/50-rpg-sound-effects"),
    "UI": ("UI_SFX_Set", "51 UI sound effects, de Kenney", "https://opengameart.org/content/51-ui-sound-effects-buttons-switches-and-clicks"),
    "C100": ("100-CC0-SFX_0", "100 CC0 SFX", "https://opengameart.org/content/100-cc0-sfx"),
    "V2": ("sfx_100_v2", "100 CC0 SFX #2", "https://opengameart.org/content/100-cc0-sfx-2"),
    "BF": ("sfx_breaking_and_falling", "75 CC0 breaking, falling, hit SFX", "https://opengameart.org/content/75-cc0-breaking-falling-hit-sfx"),
    "BANG": ("25-CC0-bang-sfx", "25 CC0 bang, firework SFX", "https://opengameart.org/content/25-cc0-bang-firework-sfx"),
    "LOOPS": ("sfx_loops", "30 CC0 SFX loops", "https://opengameart.org/content/30-cc0-sfx-loops"),
    "WAT": ("water-splash-slime-sfx", "40 CC0 water, splash, slime SFX", "https://opengameart.org/content/40-cc0-water-splash-slime-sfx"),
    "CAR": ("car_sound_effects_pack", "Car Sound Effects Pack", "https://opengameart.org/content/car-sound-effects-pack-low-quality"),
    "BICI": ("bicycle_sounds", "Bicycle sounds", "https://opengameart.org/content/bicycle-sounds"),
    "DOG": ("dog/Dog", "Dog sounds", "https://opengameart.org/content/dog-sounds"),
    "FAN": ("Fantozzi-footsteps/Fantozzi-footsteps/flac", "Fantozzi's Footsteps", "https://opengameart.org/content/fantozzis-footsteps-grasssand-stone"),
    "KDD": ("kdd_DifferentSteps_0", "Different steps on wood, stone, leaves, gravel and mud", "https://opengameart.org/content/different-steps-on-wood-stone-leaves-gravel-and-mud"),
    "HITS": ("independent_nu_ljudbank-hits_and_punches/hits", "37 hits and punches", "https://opengameart.org/content/37-hitspunches"),
    "DOOR": ("qubodup-DoorSet/qubodup-DoorSet/flac", "Door Open, Door Close Set", "https://opengameart.org/content/door-open-door-close-set"),
    "RAIN": ("Rain_OGG", "Rain (loopable)", "https://opengameart.org/content/rain-loopable"),
    "RPG": ("rpg_sound_pack/RPG Sound Pack", "RPG Sound Pack", "https://opengameart.org/content/rpg-sound-pack"),
    "IF": ("kenney_interfaceSounds/Audio", "Interface Sounds, de Kenney", "https://opengameart.org/content/interface-sounds"),
    "CAS": ("kenney_casino-audio/Audio", "Casino Audio, de Kenney", "https://kenney.nl/assets/casino-audio"),
    "SCR": ("slightscreams", "15 vocal male strain, hurt, pain, jump sounds", "https://opengameart.org/content/15-vocal-male-strainhurtpainjump-sounds"),
    "SND": ("sndfx", "War on Water sound effects", "https://opengameart.org/content/war-on-water-sndfx"),
    "CRU": ("crunch_-_tito", "7 eating crunches", "https://opengameart.org/content/7-eating-crunches"),
    "REL": ("gun_reload_-_starninjas", "2 gun reloads", "https://opengameart.org/content/2-gun-reloads"),
    "SHG": ("shotgunsounds/ShotgunSounds", "Shotgun reload sound effects", "https://opengameart.org/content/shotgun-reload-sound-effects"),
    "WIND": ("wind/wind", "Wind", "https://opengameart.org/content/wind"),
    "BIRD": ("birdsCrickets/birdsCrickets", "Bird, cricket, frog and mosquito sounds", "https://opengameart.org/content/birdcricketfrog-and-mosquito-sounds"),
    "TICK": ("ticks", "Ticking clock", "https://opengameart.org/content/ticking-clock"),
    "R80": ("80-CC0-RPG-SFX_0", "80 CC0 RPG SFX", "https://opengameart.org/content/80-cc0-rpg-sfx"),
    "UIS": ("UISoundEffects", "7 assorted sound effects, menu and level up", "https://opengameart.org/content/7-assorted-sound-effects-menu-level-up"),
    "CHI": ("oga2/chimey-ui-sounds/mousebyte_chimeyui", "Chimey UI sounds", "https://opengameart.org/content/chimey-ui-sounds"),
    "S16": ("oga2/sfx-the-ultimate-2017-16-bit-mini-pack/SFX-_The_Ultimate_2017_16_bit_Mini_pack/SFX- The Ultimate 2017 16 bit Mini pack", "SFX: The Ultimate 2017 16 bit Mini pack", "https://opengameart.org/content/sfx-the-ultimate-2017-16-bit-mini-pack"),
    "S8": ("oga2/sfx-the-ultimate-2017-8-bit-mini-pack/SFX-_The_Ultimate_2017_8_bit_Mini_pack/SFX- The Ultimate 2017 8 bit sound Mini pack", "SFX: The Ultimate 2017 8 bit Mini pack", "https://opengameart.org/content/sfx-the-ultimate-2017-8-bit-mini-pack"),
    "UO": ("ui_ogg/ui_ogg", "UI sound effects: button clicks, user feedback, notifications", "https://opengameart.org/content/ui-sound-effects-button-clicks-user-feedback-notifications"),
    "BSB": ("bigsoundbank", "BigSoundBank.com y LaSonotheque.org", "https://bigsoundbank.com"),
    "ARM": ("Prepared_SFX_Library/Prepared SFX Library", "The Free Firearm Sound Library", "https://opengameart.org/content/the-free-firearm-sound-library"),
    "YELL": ("yelling_sounds/yelling sounds", "Male grunt and yelling sounds", "https://opengameart.org/content/male-gruntyelling-sounds"),
    "B171": ("bigsoundbank_171", "BigSoundBank.com, grabaciones CC0 bajadas para la versión 1.7.1", "https://bigsoundbank.com"),
}

# Grabaciones sueltas: de cada archivo, su título, su autor y su página, tal como figuran en ella. Todas CC0 (dominio público).
# Así los créditos de cada pack dicen de dónde sale cada una, y no solo la colección.
DETALLE = {
    "megafono_3147": ("Megaphone, larsen #9", "Joseph SARDIN", "https://bigsoundbank.com/megaphone-larsen-9-s3147.html"),
    "megafono_3142": ("Megaphone, larsen #4", "Joseph SARDIN", "https://bigsoundbank.com/megaphone-larsen-4-s3142.html"),
    "walkie_inicio_0589": ("Walkie talkie: Start", "Joseph SARDIN", "https://bigsoundbank.com/walkie-talkie-start-s0589.html"),
    "walkie_tonos_0590": ("Walkie talkie: Keypad tones", "Joseph SARDIN", "https://bigsoundbank.com/walkie-talkie-keypad-tones-s0590.html"),
    "timbre_casa_0159": ("Doorbell house #1", "Joseph SARDIN", "https://bigsoundbank.com/doorbell-house-1-s0159.html"),
    "timbre_2365": ("Doorbell #6", "Dorian CLAIR", "https://bigsoundbank.com/doorbell-6-s2365.html"),
    "nevera_puerta_1158": ("Fridge door", "Joseph SARDIN", "https://bigsoundbank.com/fridge-door-s1158.html"),
    "tabla_calabacin_2069": ("Cutting board, zucchini #2", "Joseph SARDIN", "https://bigsoundbank.com/cutting-board-zucchini-2-s2069.html"),
    "tabla_calabacin_2068": ("Cutting board, zucchini #1", "Joseph SARDIN", "https://bigsoundbank.com/cutting-board-zucchini-1-s2068.html"),
    "sarten_0145": ("Frying pan #3", "Joseph SARDIN", "https://bigsoundbank.com/frying-pan-3-s0145.html"),
    "sarten_0144": ("Frying pan #2", "Joseph SARDIN", "https://bigsoundbank.com/frying-pan-2-s0144.html"),
    "agua_hirviendo_0149": ("Boiling water", "Joseph SARDIN", "https://bigsoundbank.com/boiling-water-s0149.html"),
    "caldo_0492": ("Small Broth in a Pot", "Joseph SARDIN", "https://bigsoundbank.com/small-broth-in-a-pot-s0492.html"),
    "plato_grande_1189": ("Large Plate, set on Table", "Joseph SARDIN", "https://bigsoundbank.com/large-plate-set-on-table-s1189.html"),
    "plato_pequeno_1190": ("Small plate, set on table", "Joseph SARDIN", "https://bigsoundbank.com/small-plate-set-on-table-s1190.html"),
    "bolsa_patatas_1434": ("Pack of chips, manipulation #2", "Joseph SARDIN", "https://bigsoundbank.com/pack-of-chips-manipulation-2-s1434.html"),
    "lata_0246": ("Tin can #1", "DenisChardonnet", "https://bigsoundbank.com/tin-1-s0246.html"),
    "timbal_2338": ("Bass Tom, #1", "Joseph SARDIN", "https://bigsoundbank.com/bass-tom-1-s2338.html"),
    "campana_0135": ("Church Bell", "Joseph SARDIN", "https://bigsoundbank.com/church-bell-s0135.html"),
    "redoble_2406": ("Drum roll 3 S", "Joseph SARDIN", "https://bigsoundbank.com/drum-roll-3-s-s2406.html"),
    "redoble_2402": ("Drum Roll 1 L", "Joseph SARDIN", "https://bigsoundbank.com/drum-roll-1-l-s2402.html"),
}

PACKS = {
    "realista": {
        "nombre": "Realista",
        "descripcion": "Grabaciones reales para pasos, puertas, armas, golpes, cristales, coche, lluvia, agua y monedas.",
        "sonidos": {
            "paso_acera0": ("FAN", "Fantozzi-StoneL1"), "paso_acera1": ("FAN", "Fantozzi-StoneR1"),
            "paso_plaza0": ("FAN", "Fantozzi-StoneL2"), "paso_plaza1": ("FAN", "Fantozzi-StoneR2"),
            "paso_calzada0": ("K", "footstep_concrete_000"), "paso_calzada1": ("K", "footstep_concrete_001"),
            "paso_arena0": ("FAN", "Fantozzi-SandL1"), "paso_arena1": ("FAN", "Fantozzi-SandR1"),
            "paso_hierba0": ("K", "footstep_grass_000", {"dur": 0.3}), "paso_hierba1": ("K", "footstep_grass_001", {"dur": 0.3}),
            "paso_muelle0": ("K", "footstep_wood_000"), "paso_muelle1": ("K", "footstep_wood_001"),
            "paso_npc": ("K", "footstep_concrete_002"),
            "choque_pared": ("K", "impactSoft_medium_000"), "golpe": ("K", "impactPunch_medium_000"),
            "golpe_aire": ("RPG", "battle/swing"), "lanzar": ("RPG", "battle/swing2"), "navaja": ("RK", "knifeSlice", {"dur": 0.3}),
            "disparo_pistola": ("ARM", "Walther PPQ/X_31P", {"golpe": 0.6}), "disparo_revolver": ("ARM", "Smith & Wesson 642/V_22P", {"golpe": 0.7}),
            "disparo_subfusil": ("ARM", "Carl Gustav M45/G_24P", {"golpe": 0.22}), "disparo_escopeta": ("ARM", "Mossberg/N_26P", {"golpe": 0.9}),
            "disparo_rifle": ("ARM", "Tikka/W_24P", {"golpe": 1.0}), "disparo_fusil": ("ARM", "AK-47/C_27P", {"golpe": 0.35}),
            "disparo_silenciado": ("ARM", "Savage 10 .300 Blackout/T_17P", {"golpe": 0.3}),
            "disparo_rafaga": ("ARM", "Bersa/F_41P", {"golpe": 0.2}), "disparo_corredera": ("ARM", "Model 12/K_17P", {"golpe": 0.9}),
            "disparo_palanca": ("ARM", "Marlin 336/I_17P", {"golpe": 0.9}), "disparo_semiautomatico": ("ARM", "SKS/U_14P", {"golpe": 0.45}),
            "lanzagranadas": ("BANG", "shot_01", {"dur": 0.6}), "hacha": ("K", "impactPlank_medium_000", {"dur": 0.4}),
            "recarga": ("REL", "gun_reload.1"), "amartillar": ("RK", "metalLatch"), "sin_balas": ("UI", "switch12"),
            "sirena": ("@sirens-and-alarm-noise", "siren_0", {"bucle": 4.0, "desde": 2.0}), "sirena_lejana": ("@sirens-and-alarm-noise", "siren_0", {"dur": 2.0}),
            "sirena_barco": ("@their-coming-generic-horn-sound", "theircoming3_0", {"dur": 2.5}),
            "motor_deportivo": ("@racing-car-engine-sound-loops", "loop_0", {"bucle": 0.7, "desde": 0.02}),
            "motor_moto": ("@motor-sound-effect", "motor_looping_0", {"bucle": 0.75, "desde": 0.02}),
            "motor_tractor": ("@enginemechanic-working-sound", "loop", {"bucle": 1.5, "desde": 0.05}),
            "motor_helicoptero": ("@helicopter-sfx", "heli_0", {"bucle": 4.0, "desde": 8.0}),
            "intermitente": ("@car-blinker-sfx", "blinker02", {"bucle": 0.74, "desde": 0.0}),
            "latido": ("@heartbeat-sounds", "heartbeat_slow_0", {"bucle": 1.6, "desde": 0.0}),
            "gaviota": ("@solo-seagull-sound-effects", "Seagull_Ambient_2"),
            "multitud": ("@crowd-shoutingspeaking-ambience", "crowd_shouting_0", {"bucle": 6.0, "desde": 5.0}),
            "fuego": ("@fire-crackling", "fire-1", {"bucle": 2.4, "desde": 0.2}),
            "amb_parque": ("@ambient-bird-sounds", "birds-isaiah658_0", {"bucle": 9.0, "desde": 3.0}),
            "amb_campo": ("@forest-bird-sounds", "forest_birds/Forest Birds/Forest Birds 2", {"bucle": 4.5, "desde": 0.2}),
            "amb_noche": ("@crickets-ambient-noise-loopable", "crickets_1", {"bucle": 8.0, "desde": 1.0}),
            "amb_playa": ("@beach-ocean-waves", "wave_01_cc0-18363__jasinski__alkaibeach", {"bucle": 3.5, "desde": 0.2}),
            "amb_montana": ("@random-sfx", "SFX/SFX/Background/Hollow Wind", {"bucle": 8.0, "desde": 1.0}),
            "carrete": ("@fisheefects", "reel", {"dur": 0.9}), "pintura": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/compressed-air-spray-02", {"dur": 1.2}),
            "cohete": ("@50-cc0-sci-fi-sfx", "sci-fi-sfx/rocket_01", {"dur": 1.0}), "bala_silbido": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/tin-whistle-whoosh-01", {"dur": 0.25}),
            "celda": ("@100-cc0-metal-and-wood-sfx", "100-CC0-wood-metal-SFX/metal_close_01"),
            "guardado": ("CHI", "Chime_Save"), "nivel": ("CHI", "Chime_LevelUp"), "pasan_horas": ("CHI", "Chime_Sleep"),
            "notificacion": ("@alertnotification-sound", "alert"), "mision_ok": ("@classic-fanfare-lick", "fanfare_3"),
            "logro": ("@16bit-success-sound", "sfx_-_success", {"dur": 1.6}), "campanadas": ("@bell-dingschimes", "bell_ding4"),
            "tomar_pastillas": ("@fantasy-accessory-sfx-library", "accessory/sfx/bottle-pills-shake-02"),
            "tomar_hierba": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/lighter-light-01"),
            "amb_mar": ("@beach-ocean-waves", "wave_02_cc0-18363__jasinski__alkaibeach", {"bucle": 2.1, "desde": 0.1}),
            "amb_puerto": ("V2", "sfx100v2_loop_water_03", {"bucle": 8.0, "desde": 0.5}),
            "motor_camion": ("@enginemechanic-working-sound", "loop", {"bucle": 1.5, "desde": 0.1}),
            "motor_bici": ("BICI", "bicycle_spokes-1", {"bucle": 0.9, "desde": 0.02}),
            "sirena_ambulancia": ("@sirens-and-alarm-noise", "siren_0", {"bucle": 3.0, "desde": 30.0}),
            "claxon_lejano": ("CAR", "Car_Horn"), "curar": ("CHI", "Chime_Confirm"), "llegada": ("@correct-bell", "bell"),
            "ascenso": ("@hyper-ultra-fanfare", "sboe", {"dur": 1.6}), "diploma": ("UIS", "Ability Learn", {"dur": 1.5}),
            "regalo": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/cover-paper-tear-01", {"dur": 0.6}),
            "trato": ("RK", "handleCoins2"), "rechazo": ("IF", "error_001"), "bolsa": ("C100", "paper_01"),
            "dolor": ("SCR", "slightscream-01"), "dolor_npc": ("SCR", "slightscream-03"), "muerte_npc": ("SCR", "slightscream-10"),
            "grito": ("SND", "Pirates/scream1"), "comer": ("CRU", "crunch.4"), "dados": ("CAS", "dice-throw-1"),
            "motor_lancha": ("SND", "Pirates/motorboat1", {"bucle": 0.8, "desde": 0.05}), "motor_barco": ("SND", "Ships/ship1", {"bucle": 2.0, "desde": 0.2}),
            "viento_playa": ("WIND", "Wind", {"bucle": 6.0, "desde": 0.2}), "pajaro": ("BIRD", "bird"), "reloj": ("TICK", "ticking clock - tick1"),
            "alarma": ("LOOPS", "alarm_01", {"bucle": 1.7, "desde": 0.05}), "esposas": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/handcuffs-metal-lock-01"),
            "menu_mover": ("IF", "tick_001"), "menu_ok": ("IF", "confirmation_001"), "menu_atras": ("IF", "back_001"),
            "menu_borde": ("IF", "bong_001"), "menu_ajuste": ("IF", "toggle_001"), "error": ("IF", "error_004"),
            "movil": ("IF", "open_001"), "dialogo": ("IF", "pluck_001"), "radio_cambio": ("IF", "switch_001", {"dur": 0.3}),
            "explosion": ("BANG", "cannon_02"), "bala_impacto": ("K", "impactMetal_medium_001"),
            "cristal": ("BF", "bfh1_glass_breaking_01"), "choque": ("BF", "bfh1_metal_falling_01"), "choque_leve": ("BF", "bfh1_metal_hit_02"),
            "puerta_coche": ("CAR", "Car_Door_Close"), "arranque": ("CAR", "Car_Engine_Start_Up"), "claxon": ("CAR", "Car_Horn"),
            "claxon_bici": ("BICI", "rotating_bicycle_bell-1"),
            "motor_coche": ("CAR", "Car_Engine_Loop", {"bucle": 2.4, "desde": 0.2}), "motor_furgoneta": ("CAR", "Car_Engine_Loop_2", {"bucle": 3.2, "desde": 0.3}),
            "puerta_entrar": ("DOOR", "qubodup-DoorOpen01"), "puerta_salir": ("DOOR", "qubodup-DoorClose01"),
            "ladrido": ("DOG", "Dog Bark 2"),
            "lluvia": ("RAIN", "1", {"bucle": 7.0, "desde": 3.0}), "trueno": ("V2", "sfx100v2_thunder_01"),
            "salpicadura": ("WAT", "splash_01"), "pesca_lanzar": ("C100", "plop_01"), "pez_pica": ("WAT", "splash_09"),
            "campana_ring": ("K", "impactBell_heavy_000"), "martillo": ("K", "impactMining_000"), "reparar": ("C100", "tools_01"),
            "caja": ("@cugzilia-ii-prototype-sound-effects", "cugzilia_ii_prototype_sound_effects/cashier"), "dinero": ("RPG", "inventory/coin"), "donativo": ("RK", "handleCoins"),
            "recoger": ("RK", "handleSmallLeather"), "tomar_copa": ("@liquid-bottle-drink-set", "qubodup-bottle-and-drink-sounds/qubodup-bottle-and-drink-sounds/bottle-open-01"),
            "agacharse": ("RK", "cloth3", {"dur": 0.25}), "levantarse": ("RK", "cloth4", {"dur": 0.25}),
            "lugar_fuente": ("V2", "sfx100v2_loop_water_01", {"bucle": 5.0, "desde": 0.5}), "lugar_rio": ("V2", "sfx100v2_loop_water_02", {"bucle": 6.0, "desde": 1.0}),
            "amb_industrial": ("V2", "sfx100v2_loop_construction_site", {"bucle": 9.0, "desde": 2.0}),
            "amb_ciudad": ("V2", "sfx100v2_loop_highway", {"bucle": 9.0, "desde": 3.0}),
        },
    },
    "alternativo": {
        "nombre": "Alternativo",
        "descripcion": "Otra selección de grabaciones para los mismos sonidos, con otras armas y con clics reales en los menús.",
        "sonidos": {
            "paso_acera0": ("V2", "sfx100v2_footstep_01"), "paso_acera1": ("V2", "sfx100v2_footstep_02"),
            "paso_plaza0": ("FAN", "Fantozzi-StoneL3"), "paso_plaza1": ("FAN", "Fantozzi-StoneR3"),
            "paso_calzada0": ("K", "footstep_concrete_003"), "paso_calzada1": ("K", "footstep_concrete_004"),
            "paso_arena0": ("FAN", "Fantozzi-SandL2"), "paso_arena1": ("FAN", "Fantozzi-SandR2"),
            "paso_hierba0": ("KDD", "leaves01", {"dur": 0.3}), "paso_hierba1": ("KDD", "leaves02", {"dur": 0.3}),
            "paso_muelle0": ("V2", "sfx100v2_footstep_wood_01"), "paso_muelle1": ("V2", "sfx100v2_footstep_wood_02"),
            "paso_npc": ("RK", "footstep00"),
            "choque_pared": ("K", "impactSoft_heavy_000", {"dur": 0.2}), "golpe": ("HITS", "hit09", {"dur": 0.4}),
            "golpe_aire": ("RPG", "battle/swing3"), "lanzar": ("RPG", "battle/swing"), "navaja": ("RK", "drawKnife1", {"dur": 0.3}),
            "disparo_pistola": ("ARM", "1911/A_34P", {"golpe": 0.6}), "disparo_revolver": ("ARM", "Ruger Single Six/S_11P", {"golpe": 0.7}),
            "disparo_subfusil": ("ARM", "PPSh/P_22P", {"golpe": 0.22}), "disparo_escopeta": ("ARM", "Nova/O_17P", {"golpe": 0.9}),
            "disparo_rifle": ("ARM", "Mosin Nagant/M_21P", {"golpe": 1.0}), "disparo_fusil": ("ARM", "AR-15/D_24P", {"golpe": 0.35}),
            "disparo_silenciado": ("ARM", "Ruger Mark III/R_30P", {"golpe": 0.3}),
            "disparo_rafaga": ("ARM", "Bersa/F_47P", {"golpe": 0.2}), "disparo_corredera": ("ARM", "Model 12/K_22P", {"golpe": 0.9}),
            "disparo_palanca": ("ARM", "Model 1894/L_17P", {"golpe": 0.9}), "disparo_semiautomatico": ("ARM", "SKS/U_19P", {"golpe": 0.45}),
            "lanzagranadas": ("BANG", "shot_02", {"dur": 0.6}), "hacha": ("K", "impactPlank_medium_002", {"dur": 0.4}),
            "recarga": ("SHG", "Rack"), "amartillar": ("RK", "metalClick", {"dur": 0.3}), "sin_balas": ("SND", "Guns/gunempty"),
            "sirena": ("@sirens-and-alarm-noise", "siren_0", {"bucle": 4.0, "desde": 14.0}), "sirena_lejana": ("@sirens-and-alarm-noise", "siren_0", {"bucle": 1.9, "desde": 24.0}),
            "sirena_ambulancia": ("@sirens-and-alarm-noise", "siren_0", {"bucle": 3.0, "desde": 30.0}),
            "sirena_barco": ("@steam-whistle", "steam_whistle"),
            "motor_deportivo": ("@racing-car-engine-sound-loops", "loop_2_0", {"bucle": 0.6, "desde": 0.02}),
            "motor_camion": ("@enginemechanic-working-sound", "loop", {"bucle": 1.5, "desde": 0.1}),
            "motor_helicoptero": ("@helicopter-sounds", "helicopter_0", {"bucle": 4.0, "desde": 10.0}),
            "intermitente": ("@car-blinker-sfx", "blinker03", {"bucle": 0.74, "desde": 0.0}),
            "latido": ("@heartbeat-sounds", "heartbeat_fast_0", {"bucle": 1.0, "desde": 0.0}),
            "gaviota": ("@solo-seagull-sound-effects", "Seagull_Ambient_5"),
            "multitud": ("@crowd-shoutingspeaking-ambience", "crowd_shouting_0", {"bucle": 6.0, "desde": 15.0}),
            "fuego": ("@fireplace-sound-loop", "fire", {"bucle": 5.0, "desde": 3.0}),
            "amb_parque": ("@ambient-bird-sounds", "birds-isaiah658_0", {"bucle": 9.0, "desde": 16.0}),
            "amb_noche": ("@swamp-environment-audio", "swamp_sounds/cricket_1", {"bucle": 8.0, "desde": 2.0}),
            "amb_playa": ("@18-random-video-game-sound-effects", "sound_effects/sound_effects/beach", {"bucle": 3.5, "desde": 0.2}),
            "amb_montana": ("@short-wind-sound", "short_wind_sound", {"bucle": 3.6, "desde": 0.3}),
            "carrete": ("@fisheefects", "reel", {"dur": 0.9}), "pintura": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/compressed-air-spray-01"),
            "bala_silbido": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/tube-plastic-whoosh-01", {"dur": 0.25}),
            "guardado": ("CHI", "Chime_Load"), "nivel": ("@7-assorted-sound-effects-menu-level-up", "UISoundEffects/Level Up", {"dur": 1.5}),
            "notificacion": ("@patreon-menu-soundpacks", "PatreonMenuSound/lowRing"), "mision_ok": ("@16bit-success-sound", "sfx_-_success"),
            "campanadas": ("@bell-dingschimes", "bell_ding1"), "tomar_hierba": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/match-light-01"),
            "dolor": ("SCR", "slightscream-05"), "dolor_npc": ("SCR", "slightscream-07"), "muerte_npc": ("SCR", "slightscream-15"),
            "grito": ("SND", "Pirates/scream2"), "comer": ("CRU", "crunch.5"), "dados": ("CAS", "dice-shake-1"),
            "motor_lancha": ("SND", "Pirates/motorboat2", {"bucle": 0.75, "desde": 0.05}), "motor_barco": ("SND", "Ships/friendlyboat", {"bucle": 2.2, "desde": 0.3}),
            "viento_playa": ("WIND", "Wind2", {"bucle": 6.0, "desde": 0.2}), "pajaro": ("BIRD", "bird2"), "reloj": ("TICK", "ticking clock - tick2"),
            "alarma": ("LOOPS", "alarm_03", {"bucle": 0.85, "desde": 0.05}),
            "error": ("UIS", "Menu Error", {"dur": 0.5}), "movil": ("IF", "maximize_001"), "dialogo": ("IF", "drop_001"),
            "radio_cambio": ("IF", "scratch_004"),
            "explosion": ("BANG", "cannon_01"), "bala_impacto": ("K", "impactMetal_light_000", {"dur": 0.2}),
            "cristal": ("BF", "bfh1_glass_breaking_03"), "choque": ("BF", "bfh1_breaking_01"), "choque_leve": ("BF", "bfh1_metal_hit_03"),
            "puerta_coche": ("CAR", "Car_Hood_Close", {"dur": 0.5}), "claxon_bici": ("BICI", "bicycle_horn-1"),
            "puerta_entrar": ("RK", "doorOpen_1"), "puerta_salir": ("RK", "doorClose_1"),
            "ladrido": ("DOG", "Dog Bark 3"),
            "lluvia": ("WAT", "loop_rain", {"bucle": 6.0, "desde": 0.4}), "trueno": ("V2", "sfx100v2_thunder_01"),
            "salpicadura": ("WAT", "splash_05"), "pesca_lanzar": ("C100", "plop_02"), "pez_pica": ("WAT", "splash_10"),
            "campana_ring": ("K", "impactBell_heavy_001"), "martillo": ("K", "impactMining_002"), "reparar": ("C100", "tools_03"),
            "caja": ("RPG", "inventory/coin3"), "dinero": ("RK", "handleCoins2"), "donativo": ("RPG", "inventory/coin"),
            "recoger": ("UIS", "Item Pickup", {"dur": 0.5}), "tomar_copa": ("RPG", "inventory/bottle"), "esposas": ("R80", "chain_02"),
            "agacharse": ("RK", "cloth2", {"dur": 0.25}), "levantarse": ("RK", "cloth1", {"dur": 0.25}),
            "lugar_fuente": ("WAT", "loop_water_01", {"bucle": 2.8, "desde": 0.2}), "lugar_rio": ("WAT", "loop_water_02", {"bucle": 6.0, "desde": 0.4}),
            "amb_industrial": ("LOOPS", "machine_11", {"bucle": 5.0, "desde": 0.2}),
            "menu_mover": ("UI", "rollover2"), "menu_ok": ("UI", "switch2"), "menu_atras": ("UI", "switch7"),
            "menu_borde": ("UI", "switch13"), "menu_ajuste": ("UI", "click3"),
        },
    },
    "retro": {
        "nombre": "Retro",
        "descripcion": "Sonidos de consola antigua, de 8 y 16 bits, para pasos, golpes, disparos, explosiones, monedas, avisos y menús; el resto, grabaciones reales.",
        "sonidos": {
            "paso_acera0": ("S16", "Footstep/Wav/Footstep__001"), "paso_acera1": ("S16", "Footstep/Wav/Footstep__002"),
            "paso_calzada0": ("S16", "Footstep/Wav/Footstep__003"), "paso_calzada1": ("S16", "Footstep/Wav/Footstep__004"),
            "paso_plaza0": ("S16", "Footstep/Wav/Footstep__005"), "paso_plaza1": ("S16", "Footstep/Wav/Footstep__006"),
            "paso_arena0": ("S16", "Footstep/Wav/Footstep__007"), "paso_arena1": ("S16", "Footstep/Wav/Footstep__008"),
            "paso_hierba0": ("S16", "Footstep/Wav/Footstep__009"), "paso_hierba1": ("S16", "Footstep/Wav/Footstep__010"),
            "paso_muelle0": ("S8", "Footstep1/Wav/Footstep1__001"), "paso_muelle1": ("S8", "Footstep1/Wav/Footstep1__002"),
            "paso_npc": ("S8", "Footstep1/Wav/Footstep1__003"),
            "golpe": ("S16", "Punch/Wav/Punch__001"), "choque_pared": ("S16", "Punch2/Wav/Punch2__005", {"dur": 0.2}), "navaja": ("S16", "Punch/Wav/Punch__004"),
            "golpe_aire": ("S16", "Jump/Wav/Jump__004", {"dur": 0.15}), "lanzar": ("S16", "Jump/Wav/Jump__001"),
            "agacharse": ("S16", "Jump/Wav/Jump__003", {"dur": 0.2}), "levantarse": ("S16", "Jump/Wav/Jump__002"),
            "disparo_pistola": ("S16", "Pew/Wav/Pew__001"), "disparo_revolver": ("S16", "Pew/Wav/Pew__002"), "disparo_rifle": ("S16", "Pew/Wav/Pew__003"),
            "disparo_subfusil": ("S16", "Pew/Wav/Pew__004", {"dur": 0.2}), "disparo_fusil": ("S16", "Pew/Wav/Pew__007", {"dur": 0.3}),
            "disparo_silenciado": ("S16", "Pew/Wav/Pew__006", {"dur": 0.15}), "disparo_escopeta": ("S16", "Explosion/Wav/Explosion__001"),
            "disparo_rafaga": ("S16", "Pew/Wav/Pew__005", {"dur": 0.15}), "disparo_corredera": ("S16", "Explosion/Wav/Explosion__004"),
            "disparo_palanca": ("S16", "Pew/Wav/Pew__008"), "disparo_semiautomatico": ("S16", "Pew/Wav/Pew__009", {"dur": 0.3}),
            "lanzagranadas": ("S16", "Explosion3/Wav/Explosion3__001", {"dur": 0.5}), "hacha": ("S16", "Punch/Wav/Punch__006"),
            "explosion": ("S16", "Explosion2/Wav/Explosion2__001"), "cohete": ("S16", "Explosion3/Wav/Explosion3__003"),
            "cristal": ("S16", "Explosion/Wav/Explosion__003"), "choque": ("S16", "Explosion/Wav/Explosion__002"), "choque_leve": ("S16", "Explosion/Wav/Explosion__005"),
            "dolor": ("S16", "Ouch/Wav/Ouch__001"), "dolor_npc": ("S16", "Ouch/Wav/Ouch__004"), "muerte_npc": ("S16", "Ouch/Wav/Ouch__002"),
            "recoger": ("S16", "Pickup/Wav/Pickup__001"), "movil": ("S16", "Pickup/Wav/Pickup__003"),
            "dinero": ("@10-8bit-coin-sounds", "coin_sounds/coin1"), "caja": ("@10-8bit-coin-sounds", "coin_sounds/coin2"), "donativo": ("@10-8bit-coin-sounds", "coin_sounds/coin3"),
            "nivel": ("S16", "Powerup/Wav/Powerup__001"), "curar": ("S16", "Powerup/Wav/Powerup__002"), "logro": ("S16", "Starpower/Wav/Starpower__002"),
            "llegada": ("S16", "Teleport/Wav/Teleport__003"), "pasan_horas": ("S16", "Teleport2/Wav/Teleport2_001"),
            "mision_ok": ("@8bit-fanfare-jingle-the-lick", "life"), "mision_fallo": ("@retro-shooter-sound-effects", "Misc_Lasers/Game Over"),
            "menu_mover": ("S16", "Menu/Wav/Menu__003"), "menu_ok": ("S16", "Menu/Wav/Menu__001"), "menu_atras": ("S16", "Menu/Wav/Menu__002"),
            "menu_borde": ("S16", "Menu/Wav/Menu__005"), "menu_ajuste": ("S16", "Menu/Wav/Menu__006"),
            "error": ("@3-ping-pong-sounds-8-bit-style", "sounds_ping_pong_8bit/sounds_ping_pong_8bit/ping_pong_8bit_peeeeeep"),
            "notificacion": ("@8bit-menu-select", "vgmenuselect"), "guardado": ("CHI", "Chime_Save"),
        },
    },
}


def info(col):
    """(carpeta, nombre, página) de una colección. Las que empiezan por @ son páginas de OpenGameArt
    bajadas a adjuntos/fuentes/oga2/<página>."""
    if col.startswith("@"):
        return ("oga2/" + col[1:], col[1:].replace("-", " "), "https://opengameart.org/content/" + col[1:])
    return COL[col]


# Sonidos que comparten los packs de grabaciones: avisos y señales del juego para los que solo hay una buena
# candidata entre lo descargado. Cada pack usa la suya si la tiene y, si no, esta.
EXTRA = {
    # combustible, averías, multas y beber (1.7.0)
    "repostar": ("WAT", "loop_water_01", {"dur": 1.6}), "beber": ("WAT", "bubble_01"), "motor_seco": ("CAR", "Car_Engine_Turning_Off"),
    "motor_apagar": ("CAR", "Car_Engine_Turning_Off", {"dur": 1.6}),      # el motor que se apaga con la llave (issue 48)
    "pinchazo": ("BANG", "bang_03", {"dur": 0.9}), "reserva": ("IF", "error_004"), "multa": ("@steam-whistle", "steamwhistle_0", {"dur": 0.35}),
    "buho": ("BIRD", "birdNight"), "claxon_camion": ("@steam-whistle", "steamwhistle_0", {"dur": 0.8}),
    "claxon_helados": ("@bell-arpeggio-24", "24", {"dur": 1.6}),
    "ganzua": ("@58-random-sound-effects", "Sound_Effects/Small_Chain_Rattle_01", {"bucle": 1.2, "desde": 0.1}),
    "hospital_despertar": ("@nhfea-sound", "sound/sound/as_h_breath"),
    "murmullo": ("@crowd-shoutingspeaking-ambience", "crowd_shouting_0", {"bucle": 0.4, "desde": 9.0}),
    "perro_olfatea": ("@80-cc0-creature-sfx", "80-CC0-creature-SFX_0/breath", {"dur": 0.45}),
    "ruleta": ("@bowling-ball-rolling", "qubodup-bowling-roll/qubodup-bowling-roll/qubodup-bowling_roll", {"dur": 2.4}),
    "diana": ("K", "impactWood_light_000"), "diana_ok": ("@pleasing-bell-sound-effect", "pleasing-bell"),
    "simon_0": ("S16", "Instrument/Wav/Instrument__001", {"dur": 0.5}), "simon_1": ("S16", "Instrument/Wav/Instrument__002", {"dur": 0.5}),
    "simon_2": ("S16", "Instrument/Wav/Instrument__003", {"dur": 0.5}), "simon_3": ("S16", "Instrument/Wav/Instrument__004", {"dur": 0.5}),
    "estrella_sube": ("@short-alarm", "alarm_0", {"dur": 0.5}), "estrella_baja": ("CHI", "Chime_Cancel", {"dur": 0.8}),
    "policia_perdida": ("CHI", "Chime_Exit"), "buscando": ("UI", "click2"),
    "evento": ("@modern-ringtone-chirptone", "chirptone", {"dur": 0.8}),
    "fama": ("@applause-in-a-large-hall-or-church", "applause-clapping-church-crowd-immersive", {"bucle": 0.8, "desde": 8.0}),
    "prestigio": ("@bell-dingschimes", "bell_ding2", {"dur": 0.9}), "territorio": ("C100", "gong_01"),
    "jornada": ("@clock-wind-sounds", "tickloop-amp"), "mision_fallo": ("UO", "negative_sound"),
    "animo_sube": ("UO", "Ding", {"dur": 0.6}), "animo_baja": ("UO", "dum"),
    "afinidad_sube": ("UO", "chimes", {"dur": 1.1}), "afinidad_baja": ("UO", "negative_sound2"),
    "cita": ("C100", "glass_02"), "pareja": ("@bell-dingschimes", "bell_ding3", {"dur": 1.6}),
    "ruptura": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/cover-paper-tear-02"),
    "noche_juntos": ("UO", "ding_deep"), "paisano": ("UO", "alarm2", {"dur": 1.0}),
    "precio_ganga": ("RPG", "inventory/coin3"), "precio_escasez": ("IF", "error_005"),
    "bajon": ("@ghost-breath", "ghostbreath", {"dur": 1.6}), "abstinencia": ("@old-man-cough", "old-man-cough", {"dur": 1.2}),
    "sobredosis": ("@heartbeat-sounds", "heartbeat_fast_reverb"),
    "tomar_cristal": ("@58-random-sound-effects", "Sound_Effects/Cigarette_Lighter_04"),
    "tomar_polvo": ("@80-cc0-creture-sfx-2", "80-CC0-creature-sfx-2/breath_02"),
    "amb_residencial": ("@ambient-bird-sounds", "birds-isaiah658_0", {"bucle": 6.0, "desde": 23.0}),
    "trato": ("RK", "handleCoins2"), "rechazo": ("IF", "error_001"), "bolsa": ("C100", "paper_01"),
    "regalo": ("@fantasy-sound-effects-tinysized-sfx", "tinysized/sfx-cc0/cover-paper-tear-01", {"dur": 0.6}),
    "curar": ("CHI", "Chime_Confirm"), "llegada": ("@correct-bell", "bell"), "ascenso": ("@hyper-ultra-fanfare", "sboe", {"dur": 1.6}),
    "diploma": ("UIS", "Ability Learn", {"dur": 1.5}), "claxon_lejano": ("CAR", "Car_Horn"),
    "motor_bici": ("BICI", "bicycle_spokes-1", {"bucle": 0.9, "desde": 0.02}), "motor_moto": ("@motor-sound-effect", "motor_looping_0", {"bucle": 0.75, "desde": 0.02}),
    "motor_tractor": ("@enginemechanic-working-sound", "loop", {"bucle": 1.5, "desde": 0.05}), "motor_camion": ("@enginemechanic-working-sound", "loop", {"bucle": 1.5, "desde": 0.1}),
    "amb_mar": ("@beach-ocean-waves", "wave_02_cc0-18363__jasinski__alkaibeach", {"bucle": 2.1, "desde": 0.1}),
    "amb_puerto": ("V2", "sfx100v2_loop_water_03", {"bucle": 8.0, "desde": 0.5}),
    "amb_campo": ("@forest-bird-sounds", "forest_birds/Forest Birds/Forest Birds 2", {"bucle": 4.5, "desde": 0.2}),
    "amb_ciudad": ("V2", "sfx100v2_loop_highway", {"bucle": 9.0, "desde": 3.0}),
    "cohete": ("@50-cc0-sci-fi-sfx", "sci-fi-sfx/rocket_01", {"dur": 1.0}), "celda": ("@100-cc0-metal-and-wood-sfx", "100-CC0-wood-metal-SFX/metal_close_01"),
    "logro": ("@16bit-success-sound", "sfx_-_success", {"dur": 1.6}), "pasan_horas": ("CHI", "Chime_Sleep"),
    "tomar_pastillas": ("@fantasy-accessory-sfx-library", "accessory/sfx/bottle-pills-shake-02"),
    "arranque": ("CAR", "Car_Engine_Start_Up"), "claxon": ("CAR", "Car_Horn"), "motor_coche": ("CAR", "Car_Engine_Loop", {"bucle": 2.4, "desde": 0.2}),
    "motor_furgoneta": ("CAR", "Car_Engine_Loop_2", {"bucle": 3.2, "desde": 0.3}),
    "rodadura": ("LOOPS", "rolling", {"bucle": 0.85, "desde": 0.02}),
    "amigo_entra": ("IF", "maximize_004"), "amigo_sale": ("IF", "minimize_004"), "chat": ("IF", "confirmation_002"),
    "gallo": ("BSB", "gallo_0283"), "frenazo": ("BSB", "frenazo_2370", {"dur": 1.2}),
}
# La calle (1.7.1): gritos y quejas con voz de hombre y de mujer, la munición que se recoge y el helicóptero de la policía.
# El megáfono se queda en todos los packs con el sonido del juego: lo que dice lo lee el lector, y una grabación con palabras estorbaría.
CALLE = {
    # el pánico (1.7.3): una multitud que grita y, encima, gritos sueltos de hombres y de mujeres a destiempo
    "realista": {"panico": ("@crowd-shoutingspeaking-ambience", "crowd_shouting_0", {"desde": 9.0, "dur": 2.4, "entrada": 0.15, "fundido": 0.6, "mezcla": [
                     ("@girly-scream", "wscream_2_0", {}, 0.05, 0.8), ("YELL", "2yell3", {}, 0.3, 0.6), ("YELL", "1yell5", {}, 0.75, 0.5),
                     ("@girly-scream", "wscream_2_0", {}, 1.2, 0.45), ("YELL", "3yell4", {}, 1.5, 0.4)]}),
                 "grito_hombre": ("YELL", "2yell3"), "grito_mujer": ("@girly-scream", "wscream_2_0"),
                 "dolor_mujer": ("@female-hurt-grunts-groans", "female_hurt_grunts_groans_1", {"desde": 2.05, "dur": 0.65}),
                 "recoger_municion": ("@gun-reload-sound-effects", "clipload1"),
                 "helicoptero_policia": ("@helicopter-sounds", "helicopter_0", {"bucle": 4.0, "desde": 22.0})},
    "alternativo": {"panico": ("@crowd-shoutingspeaking-ambience", "crowd_shouting_0", {"desde": 19.0, "dur": 2.4, "entrada": 0.15, "fundido": 0.6, "mezcla": [
                        ("YELL", "3yell4", {}, 0.05, 0.7), ("@girly-scream", "wscream_2_0", {}, 0.35, 0.75), ("YELL", "1yell9", {}, 0.8, 0.5),
                        ("YELL", "2yell6", {}, 1.3, 0.45)]}),
                    "grito_hombre": ("YELL", "3yell4"), "grito_mujer": ("@girly-scream", "wscream_2_0"),
                    "dolor_mujer": ("@female-hurt-grunts-groans", "female_hurt_grunts_groans_1", {"desde": 7.3, "dur": 0.75}),
                    "recoger_municion": ("SND", "Interface/cartriges"),
                    "helicoptero_policia": ("@helicopter-sfx", "heli_0", {"bucle": 4.0, "desde": 14.0})},
}
for _clave, _tabla in CALLE.items():
    PACKS[_clave]["sonidos"].update(_tabla)
# Lo demás de la 1.7.1, con grabaciones CC0 de BigSoundBank hechas de lo que representan: el acople de un megáfono, un
# walkie-talkie, timbres de casa, la puerta de una nevera, un cuchillo en la tabla, una sartén, una olla, un plato en la mesa,
# un producto que se echa a la cesta, y para los barrios un timbal (tres golpes), una campana de iglesia y un redoble.
# El pack retro los hereda del realista, como todo lo que no tiene sonido de consola, y el envolvente también.
# Los tres canales de rol (chat_personaje, chat_fuera, chat_accion) y espera_servidor se quedan en todos los packs con el
# sonido del juego: son un código de tonos, no el ruido de una cosa, y lo que los distingue es justo lo que dice la ayuda.
V171 = {
    "realista": {"megafono": ("B171", "megafono/megafono_3147", {"dur": 0.9, "fundido": 0.15}),
                 "emisora": ("B171", "emisora/walkie_inicio_0589", {"desde": 0.6, "dur": 0.6}),
                 "timbre": ("B171", "timbre/timbre_casa_0159", {"dur": 2.6, "fundido": 0.4}),
                 "nevera": ("B171", "nevera/nevera_puerta_1158", {"desde": 2.35, "dur": 1.1, "fundido": 0.3}),
                 "cocina_cortar": ("B171", "cocina_cortar/tabla_calabacin_2069", {"dur": 1.5}),
                 "cocina_freir": ("B171", "cocina_freir/sarten_0145", {"desde": 1.0, "dur": 2.4, "entrada": 0.08, "fundido": 0.3}),
                 "cocina_hervir": ("B171", "cocina_hervir/agua_hirviendo_0149", {"desde": 2.0, "dur": 2.4, "entrada": 0.08, "fundido": 0.3}),
                 "plato_servido": ("B171", "plato_servido/plato_grande_1189", {"desde": 13.1, "dur": 0.7}),
                 "cesta": ("B171", "cesta/bolsa_patatas_1434", {"desde": 3.6, "dur": 0.5, "fundido": 0.08}),
                 "amenaza_barrio": ("B171", "amenaza_barrio/timbal_2338", {"dur": 0.5, "fundido": 0.1, "veces": (0.0, 0.42, 0.72)}),
                 "barrio_perdido": ("B171", "barrio_perdido/campana_0135", {"desde": 1.96, "dur": 1.9, "fundido": 0.4}),
                 "barrio_defendido": ("B171", "barrio_defendido/redoble_2406", {"desde": 0.9, "dur": 1.5})},
    "alternativo": {"megafono": ("B171", "megafono/megafono_3142", {"dur": 0.8, "fundido": 0.15}),
                    "emisora": ("B171", "emisora/walkie_tonos_0590", {"desde": 1.0, "dur": 1.1}),
                    "timbre": ("B171", "timbre/timbre_2365", {"dur": 1.8, "fundido": 0.3}),
                    "nevera": ("B171", "nevera/nevera_puerta_1158", {"desde": 18.3, "dur": 1.1, "fundido": 0.3}),
                    "cocina_cortar": ("B171", "cocina_cortar/tabla_calabacin_2068", {"desde": 1.9, "dur": 1.5}),
                    "cocina_freir": ("B171", "cocina_freir/sarten_0144", {"desde": 2.0, "dur": 2.4, "entrada": 0.08, "fundido": 0.3}),
                    "cocina_hervir": ("B171", "cocina_hervir/caldo_0492", {"desde": 2.0, "dur": 2.4, "entrada": 0.08, "fundido": 0.3}),
                    "plato_servido": ("B171", "plato_servido/plato_pequeno_1190", {"desde": 15.4, "dur": 0.7}),
                    "cesta": ("B171", "cesta/lata_0246", {"dur": 0.6, "fundido": 0.08}),
                    "amenaza_barrio": ("B171", "amenaza_barrio/timbal_2338", {"dur": 0.5, "fundido": 0.1, "veces": (0.0, 0.5, 0.82)}),
                    "barrio_perdido": ("B171", "barrio_perdido/campana_0135", {"desde": 3.96, "dur": 1.9, "fundido": 0.4}),
                    "barrio_defendido": ("B171", "barrio_defendido/redoble_2402", {"desde": 2.9, "dur": 1.5})},
}
for _clave, _tabla in V171.items():
    PACKS[_clave]["sonidos"].update(_tabla)
for _clave in ("realista", "alternativo"):
    for _sonido, _origen in EXTRA.items():
        PACKS[_clave]["sonidos"].setdefault(_sonido, _origen)
# El pack retro pone sonido de consola donde lo hay; para el resto usa las grabaciones del pack realista,
# de modo que también él sustituye todos los sonidos que no son de orientación.
for _sonido, _origen in PACKS["realista"]["sonidos"].items():
    PACKS["retro"]["sonidos"].setdefault(_sonido, _origen)

# Grabaciones hechas a propósito de lo que representan (BigSoundBank): mandan sobre cualquier aproximación.
PROPIAS = {
    "buho": ("BSB", "buho_1763", {"dur": 2.2}), "claxon_camion": ("BSB", "claxon_camion_2721", {"dur": 1.0}),
    "sirena": ("BSB", "policia_0886", {"bucle": 4.0, "desde": 3.0}), "sirena_lejana": ("BSB", "policia_0886", {"bucle": 1.9, "desde": 9.0}),
    "sirena_ambulancia": ("BSB", "ambulancia_1463", {"bucle": 3.0, "desde": 3.0}),
    "perro_olfatea": ("BSB", "perro_respira_1547", {"bucle": 0.45, "desde": 0.5}), "tomar_polvo": ("BSB", "esnifar_0784", {"dur": 1.0}),
    "cita": ("BSB", "beso_2196"), "motor_camion": ("BSB", "motor_camion_1442", {"bucle": 1.5, "desde": 3.0}),
    "motor_tractor": ("BSB", "tractor_0132", {"bucle": 1.5, "desde": 8.0}),
    "amb_ciudad": ("BSB", "calle_1713", {"bucle": 9.0, "desde": 20.0}), "amb_residencial": ("BSB", "pueblo_1347", {"bucle": 8.0, "desde": 20.0}),
    "amb_puerto": ("BSB", "puerto_2571", {"bucle": 9.0, "desde": 20.0}),
    "hospital_despertar": ("BSB", "monitor_0457", {"bucle": 2.4, "desde": 1.0}),
    "murmullo": ("BSB", "charla_2968", {"bucle": 0.4, "desde": 20.0}), "multitud": ("BSB", "charla_2968", {"bucle": 6.0, "desde": 30.0}),
    "ganzua": ("BSB", "llave_1320", {"bucle": 1.2, "desde": 0.3}),
    # tren, tranvía, avioneta y agua: grabaciones CC0 de Freesound bajadas para la versión 1.6.2
    "tren": ("FS162", "tren", {"bucle": 8.0, "desde": 10.0}), "tren_silbato": ("FS162", "tren_silbato", {"dur": 3.0}),
    "tranvia": ("FS162", "tranvia", {"bucle": 8.0, "desde": 10.0}), "tranvia_campana": ("FS162", "tranvia_campana", {"dur": 2.0}),
    "motor_avioneta": ("FS162", "motor_avioneta", {"bucle": 4.0, "desde": 3.0}),
    "bajo_agua": ("FS162", "bajo_agua", {"bucle": 8.0, "desde": 5.0}), "brazada": ("FS162", "brazada", {"dur": 0.9}),
    "paso_via0": ("K", "impactMetal_light_000", {"dur": 0.25}), "paso_via1": ("K", "impactMetal_light_001", {"dur": 0.25}),
    "avion": ("FS162", "avion", {"bucle": 8.0, "desde": 6.0}), "avion_despegue": ("FS162", "avion_despegue", {"dur": 8.0}),
}
for _pack in PACKS.values():
    _pack["sonidos"].update(PROPIAS)

# Los sonidos de orientación no se sustituyen nunca: de ellos depende poder jugar sin ver.
ORIENTACION = ("baliza", "tono_", "semaforo_", "lugar_", "loc_", "radar", "sonar", "cruce", "bordillo", "cursor_mapa")


def credito(sonido, col, archivo, dur):
    """La línea de CREDITOS.txt de una grabación. Si el archivo está en DETALLE, con su título, autor, licencia y página."""
    det = DETALLE.get(os.path.splitext(archivo)[0])
    de = f"«{det[0]}», de {det[1]}. Licencia CC0 (dominio público). {det[2]}" if det else f"de {info(col)[1]}"
    return f"  {sonido}{sintesis.FORMATO}: {archivo}, {de}. Dura " + f"{dur:.2f}".replace(".", ",") + " segundos."


def buscar(col, nombre):
    carpeta = os.path.join(FUENTES, *info(col)[0].split("/"), *nombre.split("/")[:-1])
    base = nombre.split("/")[-1]
    if not os.path.isdir(carpeta):
        return None
    for f in sorted(os.listdir(carpeta)):
        if f.lower().endswith(rutas.EXT_AUDIO) and (os.path.splitext(f)[0] == base or f.startswith(base + ".")) and not f.startswith("._"):
            return os.path.join(carpeta, f)
    return None


def _fundir(d, entrada=0.003, salida=0.03):
    d = d.copy()
    entrada, salida = entrada or 0.003, salida or 0.03
    a, b = min(len(d) // 2, int(entrada * SR)), min(len(d) // 2, int(salida * SR))
    if a:
        d[:a] *= np.linspace(0, 1, a)
    if b:
        d[-b:] *= np.linspace(1, 0, b)
    return d


def preparar(d, op):
    pico = float(np.max(np.abs(d))) or 1.0
    if "bucle" in op:
        ini = int(op.get("desde", 0.0) * SR)
        n = int(op["bucle"] * SR)
        x = int(0.2 * SR)
        tramo = d[ini:ini + n + x]
        if len(tramo) < x * 3:
            tramo = d
            n, x = len(d) - len(d) // 5, len(d) // 5
        n = min(n, len(tramo) - x)
        cuerpo = tramo[:n].copy()
        r = np.linspace(0, 1, x)
        cuerpo[:x] = cuerpo[:x] * r + tramo[n:n + x] * (1 - r)        # el final se funde con el principio: no hay salto
        d = cuerpo
    elif "golpe" in op:
        fuerte = np.nonzero(np.abs(d) > 0.3 * pico)[0]
        ini = max(0, int(fuerte[0]) - int(0.004 * SR)) if len(fuerte) else 0
        d = _fundir(d[ini:ini + int(op["golpe"] * SR)], 0.001, 0.06)
    else:
        if "desde" in op:                                        # una grabación con varias tomas seguidas: se empieza en la que se quiere
            d = d[int(op["desde"] * SR):]
            if "dur" in op:
                d = d[:int(op["dur"] * SR) + int(0.1 * SR)]
            pico = float(np.max(np.abs(d))) or 1.0
        oye = np.nonzero(np.abs(d) > 0.02 * pico)[0]
        if len(oye):
            d = d[max(0, int(oye[0]) - int(0.002 * SR)):int(oye[-1]) + int(0.02 * SR)]
        if "dur" in op:
            d = d[:int(op["dur"] * SR)]
        d = _fundir(d, op.get("entrada"), op.get("fundido"))
        if "veces" in op:                                        # la misma toma, repetida en esos instantes
            largo = np.zeros(int(max(op["veces"]) * SR) + len(d), dtype=np.float32)
            for t in op["veces"]:
                largo[int(t * SR):int(t * SR) + len(d)] += d
            d = largo
        if "mezcla" in op:                                       # otras grabaciones encima, cada una en su instante
            d = d * (0.9 / (float(np.max(np.abs(d))) or 1.0))
            for col, archivo, op2, t0, g in op["mezcla"]:
                ruta = buscar(col, archivo)
                if ruta is None:
                    continue
                x = preparar(sintesis.leer_audio(ruta), op2)
                i = int(t0 * SR)
                if i + len(x) > len(d):
                    d = np.concatenate([d, np.zeros(i + len(x) - len(d), dtype=np.float32)])
                d[i:i + len(x)] += x * g
    p = float(np.max(np.abs(d))) or 1.0
    return (d * (0.9 / p)).astype(np.float32)


def montar(clave, pack):
    dest = os.path.join(DESTINO, clave)
    shutil.rmtree(dest, ignore_errors=True)
    os.makedirs(dest)
    hechos, faltan, usadas = [], [], {}
    for sonido, origen in sorted(pack["sonidos"].items()):
        col, nombre = origen[0], origen[1]
        op = origen[2] if len(origen) > 2 else {}
        ruta = buscar(col, nombre)
        if ruta is None:
            faltan.append(f"{sonido}: no se encuentra {info(col)[0]}/{nombre}")
            continue
        try:
            d = preparar(sintesis.leer_audio(ruta), op)
        except Exception as e:
            faltan.append(f"{sonido}: {e}")
            continue
        if len(d) < 64:
            faltan.append(f"{sonido}: queda vacío")
            continue
        sintesis.escribir_audio(os.path.join(dest, sonido), d)
        hechos.append((sonido, col, os.path.basename(ruta), len(d) / SR))
        usadas[col] = True
    # el pack queda completo: los sonidos para los que no hay grabación llevan el sonido original del juego
    originales = []
    for sonido, d in sorted(ORIGINALES.items()):
        if not os.path.exists(os.path.join(dest, sonido + sintesis.FORMATO)):
            sintesis.escribir_audio(os.path.join(dest, sonido), d)
            originales.append(sonido)
    with open(os.path.join(dest, "pack.json"), "w", encoding="utf-8") as f:
        json.dump({"nombre": pack["nombre"], "descripcion": pack["descripcion"], "licencia": "CC0, dominio público",
                   "grabaciones": len(hechos), "originales_del_juego": len(originales),
                   "autor": "Montado para Puerto Bravo con sonidos libres de kenney.nl y opengameart.org", "igualar": True}, f, ensure_ascii=False, indent=2)
    lineas = [f"PACK DE SONIDOS «{pack['nombre'].upper()}» PARA PUERTO BRAVO", "", pack["descripcion"], "",
              f"Trae los {len(hechos) + len(originales)} sonidos del juego: {len(hechos)} son grabaciones reales descargadas y {len(originales)} son el sonido",
              "original del juego, para los que no hay una grabación libre que encaje o que conviene no tocar",
              "(balizas, tonos, semáforos, radar y firmas de los lugares: de ellos depende orientarse sin ver).",
              "Todos proceden de colecciones con licencia CC0 (dominio público): se pueden usar, modificar y",
              "redistribuir sin pedir permiso y sin obligación de citar al autor. Aun así, aquí queda de dónde sale cada uno.", "",
              "INSTALAR", "  Copia esta carpeta entera dentro de data\\sonidos del juego y elígela en",
              "  Opciones, Sonido y música, Pack de sonidos.", "", "COLECCIONES USADAS"]
    lineas += [f"  {info(c)[1]}: {info(c)[2]}" for c in usadas]
    lineas += ["", "QUÉ SONIDO SALE DE DÓNDE"]
    lineas += [credito(s, c, a, dur) for s, c, a, dur in hechos]
    lineas += ["", "SONIDOS ORIGINALES DEL JUEGO INCLUIDOS PARA QUE EL PACK ESTÉ COMPLETO",
               "  Sustituye cualquiera de ellos por una grabación tuya con el mismo nombre.", "  " + ", ".join(originales)]
    with open(os.path.join(dest, "CREDITOS.txt"), "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    return hechos, faltan


def _linea_cuenta(total, grab, orig):
    return f"Trae los {total} sonidos del juego: {grab} son grabaciones reales descargadas y {orig} son el sonido"


def reescribir_creditos(dest, nuevas=None, colecciones=()):
    """Deja CREDITOS.txt de un pack ya instalado al día y en orden: una sola línea por sonido (la última manda), las
    grabaciones juntas y por orden alfabético, la lista de los que son el sonido original del juego y la cuenta de la
    cabecera. `nuevas` son líneas que sustituyen a las que hubiera de esos sonidos. Devuelve (grabaciones, originales)."""
    ruta = os.path.join(dest, "CREDITOS.txt")
    with open(ruta, encoding="utf-8-sig") as f:
        lineas = f.read().splitlines()
    marca = sintesis.FORMATO + ": "
    cabecera, cols, creditos, en = [], [], {}, "cabecera"
    for linea in lineas:
        if linea.strip() == "COLECCIONES USADAS":
            en = "cols"
        elif linea.strip() == "QUÉ SONIDO SALE DE DÓNDE":
            en = "resto"
        elif en == "cabecera":
            cabecera.append(linea)
        elif en == "cols" and linea.strip():
            cols.append(linea)
        elif linea.startswith("  ") and marca in linea and " " not in linea.strip().split(marca)[0]:
            creditos[linea.strip().split(marca)[0]] = linea
    creditos.update(nuevas or {})
    todos = sorted(n for n in sintesis.archivos_de(dest))
    grab = {n: creditos[n] for n in todos if n in creditos and "sonido original del juego" not in creditos[n]}
    orig = [n for n in todos if n not in grab]
    for col in colecciones:
        linea = f"  {info(col)[1]}: {info(col)[2]}"
        if linea not in cols:
            cols.append(linea)
    cabecera = [_linea_cuenta(len(todos), len(grab), len(orig)) if c.startswith("Trae los ") else c for c in cabecera]
    while cabecera and not cabecera[-1].strip():
        cabecera.pop()
    salida = cabecera + ["", "COLECCIONES USADAS"] + cols + ["", "QUÉ SONIDO SALE DE DÓNDE"] + [grab[n] for n in sorted(grab)]
    salida += ["", "SONIDOS ORIGINALES DEL JUEGO INCLUIDOS PARA QUE EL PACK ESTÉ COMPLETO",
               "  Sustituye cualquiera de ellos por una grabación tuya con el mismo nombre.", "  " + ", ".join(orig)]
    with open(ruta, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(salida) + "\n")
    return len(grab), len(orig)


MARCA_171 = "SONIDOS DE LA VERSIÓN 1.7.1, LOS MISMOS DEL PACK REALISTA"


def creditos_envolvente(env, real):
    """El pack envolvente dice, de las grabaciones sueltas que toma del realista (las que tienen título y autor), de dónde salen."""
    marca = sintesis.FORMATO + ": "
    with open(os.path.join(real, "CREDITOS.txt"), encoding="utf-8-sig") as f:
        suyas = [linea.strip() for linea in f.read().splitlines() if marca in linea and "Licencia CC0 (dominio público). https://bigsoundbank.com/" in linea]
    ruta = os.path.join(env, "CREDITOS.txt")
    with open(ruta, encoding="utf-8-sig") as f:
        lineas = f.read().splitlines()
    if MARCA_171 in lineas:
        lineas = lineas[:lineas.index(MARCA_171)]
    while lineas and not lineas[-1].strip():
        lineas.pop()
    if suyas:
        lineas += ["", MARCA_171] + [linea.replace(marca, ": ", 1) for linea in suyas]
    with open(ruta, "w", encoding="utf-8-sig", newline="\r\n") as f:
        f.write("\n".join(lineas) + "\n")
    return len(suyas)


def anadir(sonidos):
    """Añade o cambia unos sonidos sueltos en los packs que ya están en data/sonidos, sin rehacerlos: la grabación que diga
    la tabla de cada pack o, si no la hay, el sonido original del juego. El pack envolvente, que parte del realista, los toma
    de él (salvo los de orientación y los suyos en estéreo, que no se tocan).
    Deja al día la cuenta de pack.json y CREDITOS.txt, con de dónde sale cada uno. Devuelve lo hecho, pack a pack."""
    hecho = {}
    for clave, pack in PACKS.items():
        dest = os.path.join(rutas.PACKS, clave)
        if not os.path.isdir(dest):
            continue
        lineas, usadas = {}, []
        for sonido in sonidos:
            origen = pack["sonidos"].get(sonido)
            ruta = buscar(origen[0], origen[1]) if origen else None
            if ruta is not None:
                d = preparar(sintesis.leer_audio(ruta), origen[2] if len(origen) > 2 else {})
                sintesis.escribir_audio(os.path.join(dest, sonido), d)
                lineas[sonido] = credito(sonido, origen[0], os.path.basename(ruta), len(d) / SR)
                usadas.append(origen[0])
            else:
                sintesis.escribir_audio(os.path.join(dest, sonido), ORIGINALES[sonido])
                lineas[sonido] = f"  {sonido}{sintesis.FORMATO}: sonido original del juego."
            hecho.setdefault(clave, []).append((sonido, ruta is not None))
        try:
            grab, orig = reescribir_creditos(dest, lineas, usadas)
            with open(os.path.join(dest, "pack.json"), encoding="utf-8") as f:
                meta = json.load(f)
            meta["grabaciones"], meta["originales_del_juego"] = grab, orig
            with open(os.path.join(dest, "pack.json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except (OSError, ValueError):
            pass
    env = os.path.join(rutas.PACKS, "envolvente")              # el envolvente lleva los del realista
    real = os.path.join(rutas.PACKS, "realista")
    if os.path.isdir(env) and os.path.isdir(real):
        for sonido in sonidos:
            origen = os.path.join(real, sonido + sintesis.FORMATO)
            suyo = any(os.path.exists(os.path.join(env, sonido + e)) for e in rutas.EXT_AUDIO if e != sintesis.FORMATO)
            if os.path.exists(origen) and not suyo and not sonido.startswith(ORIENTACION):
                shutil.copy2(origen, os.path.join(env, sonido + sintesis.FORMATO))
                hecho.setdefault("envolvente", []).append((sonido, True))
        try:
            creditos_envolvente(env, real)
            with open(os.path.join(env, "pack.json"), encoding="utf-8") as f:
                meta = json.load(f)
            meta["sonidos"] = len(sintesis.archivos_de(env))
            with open(os.path.join(env, "pack.json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except (OSError, ValueError):
            pass
    return hecho


ORIGINALES = {}


if __name__ == "__main__":
    instalar = "instalar" in sys.argv[1:]
    ORIGINALES.update(sintesis.generar())
    if "anadir" in sys.argv[1:]:
        nombres = [a for a in sys.argv[1:] if a != "anadir"]
        desconocidos = [n for n in nombres if n not in ORIGINALES]
        if desconocidos or not nombres:
            print("Indica sonidos del juego. No existen:", ", ".join(desconocidos) or "ninguno indicado")
            sys.exit(1)
        for clave, lista in anadir(nombres).items():
            print(f"Pack {clave}: " + ", ".join(f"{s} ({'grabación' if g else 'original del juego'})" for s, g in lista))
        sys.exit(0)
    for clave, pack in PACKS.items():
        hechos, faltan = montar(clave, pack)
        print(f"Pack {clave}: {len(hechos)} grabaciones y {len(ORIGINALES) - len(hechos)} originales, {len(ORIGINALES)} en total")
        sin = sorted(s for s in ORIGINALES if s not in pack["sonidos"] and not s.startswith(ORIENTACION))
        print(f"   de orientacion, que no se tocan: {sum(1 for s in ORIGINALES if s.startswith(ORIENTACION))}. Sin grabacion: {', '.join(sin) or 'ninguno'}")
        for f in faltan:
            print("   FALTA", f)
        if instalar:
            rutas.carpeta_sonidos()
            dest = os.path.join(rutas.PACKS, clave)
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(os.path.join(DESTINO, clave), dest, dirs_exist_ok=True)
            print("   instalado en", dest)
