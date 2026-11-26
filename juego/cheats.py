"""Optional local-game cheats. Earned growth is saved with the character."""
import math

from . import i18n


def text(es, en):
    return es if i18n.actual() == "es" else en


# Each option is independently saved by Config; the stock game starts unchanged.
OPTIONS = (
    ("cheat_recoger", "Recoger todos los objetos al instante", "Collect all loose items instantly",
     "Incluye maletines, coleccionables y objetos de misión en el mapa actual. Activa también la mochila ilimitada para recoger objetos de valor sin límite de espacio.",
     "Includes briefcases, collectibles and mission items on the current map. Enable unlimited backpack slots too to collect valuables without a space limit."),
    ("cheat_contacto", "Eliminar enemigos al contacto", "Kill enemies on contact",
     "A pie, elimina enemigos hostiles a dos metros. No afecta a civiles ni aliados.",
     "On foot, defeats hostile enemies within two metres. Leaves civilians and allies alone."),
    ("cheat_conservar", "Conservar inventario al ser detenido", "Keep inventory when arrested",
     "Conserva armas, munición, chaleco, mercancía y mochila. Las multas y condenas siguen contando.",
     "Keeps weapons, ammunition, armour, merchandise and backpack items. Fines and sentences still apply."),
    ("cheat_estudiar", "Estudiar sin espera diaria", "Study again immediately",
     "Los cursos y las sesiones de títulos se pueden repetir al terminar. Se pagan y pasa el tiempo habitual.",
     "Repeat skill courses and qualification sessions as soon as they finish. Normal fees and session time apply."),
    ("cheat_admision", "Admisión libre en academias", "Academies ignore community standing",
     "Las academias ignoran prestigio, antecedentes, búsqueda, vetos y horarios. Los títulos previos siguen siendo necesarios.",
     "Academies ignore prestige, criminal records, wanted status, bans and opening hours. Prerequisite qualifications still apply."),
    ("cheat_crecer", "Mejorar atributos base con cada baja", "Grow base stats with every kill",
     "Cada baja da dos puntos de daño, uno de salud máxima y 60 puntos de práctica por habilidad. Se guarda y pasa a la nueva partida. Apagado, los bonos quedan suspendidos.",
     "Each kill earns two damage points, one maximum-health point and 60 practice points per skill. Saved and carried into New Game Plus. Switching off suspends the bonuses."),
    ("cheat_teleport", "U: teletransportarse en vez de caminar", "U: teleport instead of walking",
     "U lleva al enemigo fijado con Q o, si no hay ninguno, al destino del GPS. A pie; los vehículos conservan sus controles.",
     "U goes to the enemy selected with Q, or otherwise the GPS destination. On foot; vehicles keep their usual controls."),
    ("cheat_atropellar", "Atropellos letales a enemigos y policías", "Lethal vehicle impacts on enemies and police",
     "Un impacto al conducir elimina al enemigo o policía. Los aliados no se atropellan.",
     "A driving impact defeats enemies and police. Allies remain protected."),
    ("cheat_borrar", "Permitir borrar antecedentes en comisaría", "Allow criminal-record expungement at police stations",
     "Añade una acción voluntaria en comisaría. No borra automáticamente los antecedentes ni las estadísticas históricas.",
     "Adds a voluntary police-station action. Never clears records automatically or erases lifetime statistics."),
    ("cheat_ngplus", "Nueva partida: conservar estudios y mejoras", "New Game Plus: keep studies and business upgrades",
     "Conserva títulos, sesiones cursadas y mejoras de empresa. Las opciones y los atributos ganados se conservan siempre.",
     "Keeps qualifications, study progress and business upgrades. Options and earned growth always carry over."),
    ("cheat_piloto_agua", "Piloto del GPS para barcos", "GPS autopilot for water vehicles",
     "Con el piloto del GPS activado con Y, navega al destino evitando islas. Las flechas y el espacio dan control manual.",
     "With GPS autopilot enabled using Y, navigates to the destination around islands. Arrow keys and Space override it."),
    ("cheat_piloto_aire", "Piloto del GPS para aeronaves", "GPS autopilot for air vehicles",
     "Con Y y un destino del GPS, despega, vuela y se detiene al llegar. Aterriza si es seguro; las avionetas necesitan pista.",
     "With Y and a GPS destination, takes off, flies and stops on arrival. Lands when safe; planes require a runway."),
    ("cheat_volar", "Volar con cualquier vehículo que ocupes", "Fly any vehicle you enter",
     "Los vehículos normales usan los controles de vuelo mientras los ocupas. Recuperan su modelo al bajarte; apagarlo en vuelo inicia el descenso.",
     "Ordinary vehicles use flight controls while occupied. Their original model is restored on exit; switching off in flight starts a safe descent."),
    ("cheat_vehiculos_aliados", "Vehículos vacíos: perseguir y embestir enemigos", "Empty vehicles pursue and ram enemies",
     "Los vehículos vacíos cercanos persiguen enemigos hostiles. No recluta vehículos ocupados ni de misión. Apagado, se detienen.",
     "Nearby empty vehicles autonomously pursue hostile enemies. Excludes occupied and mission vehicles. Switching off stops them."),
    ("cheat_municion", "Munición infinita para armas adquiridas", "Infinite ammunition for acquired firearms",
     "Dispara sin gastar las balas guardadas, incluso si están a cero. No concede armas. Puedes recoger hasta diez millones de balas por arma, contando cargador y reserva.",
     "Fire owned guns without spending stored rounds, even at zero. Grants no weapons. Collect up to ten million rounds per weapon, counting magazine and reserve."),
    ("cheat_explosivos", "Explosivos y proyectiles infinitos una vez adquiridos", "Infinite acquired throwables and rockets",
     "Granadas, cócteles, cohetes y otros explosivos adquiridos no se gastan. Puedes recoger hasta diez millones de unidades por arma; activa la conversión del sobrante para recibir dinero al llegar al límite.",
     "Owned grenades, petrol bombs, rockets and other explosives are not consumed. Collect up to ten million units per weapon; enable surplus conversion to receive money at the ceiling."),
    ("cheat_mochila", "Espacio ilimitado en la mochila", "Unlimited backpack slots",
     "La capacidad de objetos y mercancía crece con lo que recoges, sin reservar una lista enorme ni guardar infinito. Al apagarlo conservas tus cosas y vuelven los límites normales para añadir más.",
     "Item and merchandise capacity grows with actual contents, without allocating a huge list or storing infinity. Switching off keeps your items and restores normal limits for further additions."),
    ("cheat_negocios", "Mejorar negocios sin prestigio", "Business upgrades ignore community standing",
     "Todos los negocios ignoran el prestigio entre los vecinos al mejorar. Los títulos necesarios, el coste y el nivel máximo se mantienen.",
     "All business upgrades ignore community prestige. Required qualifications, normal costs and the maximum level still apply."),
    ("cheat_entrar", "F: entrar en cualquier vehículo seleccionado", "F: enter any selected vehicle",
     "F entra en el vehículo vivo fijado con Q o marcado en el GPS para U, aunque esté lejos, cerrado, ocupado, en marcha o en el aire. No revive vehículos destruidos. Cambia directamente desde tu vehículo o asiento de pasajero; sin otro vehículo seleccionado, F conserva los controles normales para salir y aterrizar.",
     "F enters the live vehicle selected with Q or marked in the GPS for U, regardless of distance, locks, occupants, speed or airborne state. Never revives destroyed vehicles. Transfers directly from your current vehicle or passenger seat; without a different selected vehicle, F keeps its normal exit and landing controls."),
    ("cheat_reflejar", "Devolver disparos a quien te ataca", "Return incoming ranged shots",
     "Los disparos dirigidos a ti o a tu vehículo ocupado vuelven al tirador, incluso si iban a fallar. Incluye armas de fuego y explosivas de los enemigos. No cambia golpes, peligros ni tus explosiones.",
     "Ranged shots aimed at you or your occupied vehicle return to their shooter, even if they would miss. Includes enemy firearm and explosive weapons. Melee, hazards and your own explosions remain unchanged."),
    ("cheat_municion_dinero", "Munición sobrante: convertir en dinero", "Convert surplus ammunition pickups into money",
     "Hasta diez millones de unidades por arma, contando cargador y reserva. Cobras unidades sobrantes del suelo multiplicadas por el precio de compra de su munición. Si no tiene precio, un euro por unidad. No paga compras, premios ni traslados del armario.",
     "Up to ten million rounds per weapon, counting magazine and reserve. Pays surplus ground rounds multiplied by the listed ammunition purchase price, or one euro each if no price is available. Never pays for purchases, rewards or storage transfers."),
    ("cheat_foco", "Concentración infinita para el tiempo lento", "Infinite focus for slow time",
     "Mantiene la concentración al cien por ciento. Retroceso activa o quita el tiempo lento, o abre el control del mundo si ese truco está activado. Al apagarlo vuelven el consumo y la recuperación normales. No se aplica con amigos conectados ni en servidores.",
     "Keeps the focus meter at one hundred percent. Backspace toggles slow time, or opens the world speed control when that cheat is enabled. Switching off restores normal drain and recharge. Disabled with connected friends and on servers."),
    ("cheat_tiempo", "Control de velocidad del mundo; jugador normal", "World speed control; normal player speed",
     "Retroceso abre el control del mundo, de 0 por ciento (detenido) a 500 por ciento (cinco veces); 100 es normal. Tus movimientos, vehículos y disparos mantienen su velocidad. Los diálogos y menús no cambian de ritmo. Valor inicial: 25 por ciento. Apagado, Retroceso vuelve a la concentración. Solo sin conexión.",
     "Backspace opens the world speed control, from 0 percent (stopped) to 500 percent (five times); 100 is normal. Your movement, vehicles and firing keep their speed. Dialogue and menus keep normal timing. Initial value: 25 percent. Switching off restores Backspace focus controls. Offline only."),
)


class Cheats:
    def cheat_on(self, key):
        return not getattr(self, "en_servidor", False) and bool(self.cfg.v.get(key, False))

    def cheat_infinite_ammo(self, ident=None):
        ident = self.j.arma if ident is None else ident
        if ident not in self.j.armas:
            return False
        kind = self.armas_d.get(ident, {}).get("tipo")
        option = {"fuego": "cheat_municion", "explosivo": "cheat_explosivos"}.get(kind)
        return bool(option and self.cheat_on(option))

    def cheat_ammo_capacity(self, ident):
        """Finite total ammunition ceiling, counted separately for each weapon."""
        return 10_000_000

    def cheat_ammo_room(self, ident):
        if ident not in self.j.armas or self.armas_d.get(ident, {}).get("tipo") not in ("fuego", "explosivo"):
            return None
        if not (self.cheat_infinite_ammo(ident) or self.cheat_on("cheat_municion_dinero")):
            return None
        m = self.j.armas[ident]
        stored = max(0, int(m.get("cargador", 0))) + max(0, int(m.get("reserva", 0)))
        # Previously acquired surplus is never deleted by enabling a toggle.
        return max(0, self.cheat_ammo_capacity(ident) - stored)

    def cheat_ammo_shop_full(self, ident):
        if self.cheat_ammo_room(ident) != 0:
            return False
        self.decir(text("Ya llevas el máximo de diez millones de unidades de esta munición; no necesitas comprar más.",
                        "You already carry the ten-million-round limit for this weapon; no purchase is needed."), True)
        return True

    def cheat_ammo_overflow_value(self, ident, quantity):
        """Price only discarded ground loot; callers never use this for grants."""
        a = self.armas_d.get(ident, {})
        if not self.cheat_on("cheat_municion_dinero") or ident not in self.j.armas or a.get("tipo") not in ("fuego", "explosivo"):
            return 0
        quantity = max(0, int(quantity))
        listed_price = max(1, int(a.get("precio_balas", 0) or 0))
        return quantity * listed_price

    def cheat_growth(self):
        return max(0, int(self.j.cheat_bajas)) if self.cheat_on("cheat_crecer") else 0

    def cheat_sync_growth(self):
        j = self.j
        bonus = self.cheat_growth()
        old = max(0, int(j.cheat_salud_aplicada))
        if bonus != old:
            j.salud_max = max(1.0, j.salud_max + bonus - old)
            j.salud = min(j.salud_max, max(0.0, j.salud + max(0, bonus - old)))
            j.cheat_salud_aplicada = bonus

    def cheat_kill(self, person):
        if not self.cheat_on("cheat_crecer") or getattr(person, "inofensivo", False) or getattr(person, "deportivo", False):
            return
        self.j.cheat_bajas += 1
        self.cheat_sync_growth()

    def cheat_repair(self, vehicle):
        if vehicle is not self.j.veh or not self.cheat_on("invulnerable"):
            return False
        vehicle.salud = vehicle.salud_max
        vehicle.muerto = False
        vehicle.ardiendo = -1.0
        vehicle.pinchada = False
        vehicle.revision_debida = False
        vehicle.km_revision = getattr(vehicle, "km", 0.0)
        if vehicle.fuego is not None:
            vehicle.fuego.parar()
            vehicle.fuego = None
        return True

    def cheat_sync_flight(self, exiting=False):
        v = self.j.veh
        if v is None:
            return
        original = getattr(v, "_cheat_ground_model", None)
        enabled = self.cheat_on("cheat_volar") and not exiting
        if enabled and original is None and not v.modelo.get("vuela"):
            # Copy the individual model; never change the shared data/model of
            # other cars, traffic, garages or the next saved game load.
            v._cheat_ground_model = v.modelo
            v.modelo = dict(v.modelo, vuela=True)
            v.fase, v.alt = "tierra", 0.0
            self.vuelo_prep(v)
            self.libre_temp = False
            return
        if original is None or enabled:
            return
        if not exiting and self.vuelo_real() and getattr(v, "alt", 0) > 0:
            if self.mundo.tipo == "mar" and not original.get("barco"):
                if not getattr(v, "_cheat_waiting_for_land", False):
                    v._cheat_waiting_for_land = True
                    self.decir(text("El vuelo terminará al llegar a tierra firme.", "Flight will switch off after you reach land."), True)
                return
            # The model stays airborne only long enough to land safely.
            v.x, v.y = self.mundo.punto_libre(v.x, v.y)
            v.fase, v.bajar_al_tocar, v.vel = "aterrizando", False, 0.0
            self._cheat_landing = True
            return
        v.modelo = original
        del v._cheat_ground_model
        v.alt, v.fase, v.vel = 0.0, "tierra", 0.0
        self._cheat_landing = False
        if not exiting:
            v.x, v.y = self.mundo.punto_libre(v.x, v.y)
            self.preparar_conduccion()

    def cheat_drive(self, v, dt, keys):
        """Water/air GPS controller. Normal player input has priority."""
        import pygame
        from .cheat_vehicles import toward, water_route
        air = bool(v.modelo.get("vuela"))
        water = not air and (v.modelo.get("barco") or self.mundo.tipo == "mar")
        option = "cheat_piloto_aire" if air else "cheat_piloto_agua"
        active = (air or water) and self.cheat_on(option) and self.piloto_puesto() and self.gps
        if not active:
            if getattr(v, "_cheat_piloting", False):
                v.vel = 0.0
                v._cheat_piloting = False
            return False
        if any(k in keys for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE, pygame.K_a, pygame.K_d)):
            return False
        g = self.gps
        moving = g.get("sigue") or g.get("cosa")
        goal = (moving.x, moving.y) if moving is not None and hasattr(moving, "x") else g["dest"]
        key = (self.mundo.id, round(goal[0], 1), round(goal[1], 1), air)
        radius = g.get("radio") or 12.0
        if getattr(v, "_cheat_route_key", None) != key:
            v._cheat_route = [self.mundo.punto_libre(*goal)] if air else water_route(self.mundo, (v.x, v.y), goal)
            v._cheat_route_key = key
            v._cheat_pilot_arrived = None
        route = v._cheat_route
        v._cheat_piloting = True
        if air and self.vuelo_real():
            from .vuelo import aeronave
            self.vuelo_prep(v)
            automatic = set()
            if v.fase in ("tierra", "despegue") and v._cheat_pilot_arrived != key:
                automatic.add(pygame.K_UP)
            self.vuelo_controles(v, dt, automatic)
            if v.fase in ("aterrizando", "sin_motor") or (v.fase in ("tierra", "despegue") and not aeronave(v.modelo)["pista"]):
                v.vel = 0.0
                return True
        while len(route) > 1 and math.dist((v.x, v.y), route[0]) < 0.2:
            route.pop(0)
        if not route:
            v.vel = 0.0
            if getattr(v, "_cheat_no_route", None) != key:
                v._cheat_no_route = key
                self.decir(text("No hay una ruta navegable segura hasta ese destino.", "No safe navigable route to that destination was found."), True)
            return True
        arrived = v._cheat_pilot_arrived == key or (len(route) == 1 and math.dist((v.x, v.y), route[0]) <= radius
                   and (not air or not self.vuelo_real() or v.fase == "vuelo"))
        if arrived:
            v.vel = 0.0
            if v._cheat_pilot_arrived != key:
                v._cheat_pilot_arrived = key
                self.app.son("llegada")
                self.decir(text("El piloto se detiene en ", "Autopilot stopped at ") + g["nombre"] + ".", True)
                if air and self.vuelo_real() and v.fase == "vuelo":
                    from .vuelo import aeronave
                    boat_flyer = bool(getattr(v, "_cheat_ground_model", {}).get("barco"))
                    safe = self.mundo.transitable(v.x, v.y) and (self.mundo.tipo != "mar" or boat_flyer)
                    if safe and (not aeronave(v.modelo)["pista"] or self._campo_cerca(v, pista=True)):
                        v.fase, v.bajar_al_tocar = "aterrizando", False
            return True
        if not air and not self.gastar_combustible(v, dt):
            v.vel = 0.0
            return True
        remaining = sum(math.dist(route[n - 1], route[n]) for n in range(1, len(route))) + math.dist((v.x, v.y), route[0])
        speed = min(self.velocidad_maxima(v) * 0.7, max(1.0, math.sqrt(2 * v.modelo["freno"] * max(0.0, remaining - radius))))
        if air and self.vuelo_real() and v.fase == "despegue":
            speed = max(speed, v.modelo["vel_max"] * 0.5)
        old = (v.x, v.y)
        nx, ny = toward(v, route[0], dt, speed, v.modelo["acel"])
        if air or self.mundo.superficie(nx, ny) == "agua":
            v.x, v.y = nx, ny
        else:
            v.vel = 0.0
            v._cheat_route_key = None
        moved = math.dist(old, (v.x, v.y))
        self.j.stats["metros_coche"] += moved
        self.ganar_xp("conduccion", moved / 60.0)
        if v.canal:
            v.canal.tono(v.modelo["tono"] * (0.6 + 1.3 * abs(v.vel) / max(1, v.modelo["vel_max"])))
        return True

    def cheat_empty_vehicle(self, v, dt):
        """An opted-in empty vehicle is an ally, never an occupied car."""
        from .cheat_vehicles import segment_distance, toward, water_route
        was_active = getattr(v, "_cheat_autonomous", False)
        parked = v.ia in (None, "aparcado") or (v.ia == "policia" and v.desplegado)
        eligible = (self.cheat_on("cheat_vehiculos_aliados") and v is not self.j.veh and not v.muerto
                    and v.ardiendo < 0 and not v.tag and not v.ocupado
                    and (not v.hostil or (v.ia == "policia" and v.desplegado)) and parked
                    and not any(not q.muerto for q in getattr(v, "pasajeros", [])) and v.dist(*self.pos()) < 250)
        if not eligible:
            if was_active:
                v.vel = 0.0
                v._cheat_autonomous = False
                v.hostil = getattr(v, "_cheat_old_hostil", v.hostil)
            return False
        targets = [q for q in self.personas if not q.muerto and q.hostil and q.tipo not in ("civil", "aliado", "perro")
                   and not getattr(q, "inofensivo", False) and not getattr(q, "deportivo", False) and q.dist(v.x, v.y) < 250]
        if not targets:
            if was_active:
                v.vel = 0.0
                v._cheat_autonomous = False
                v.hostil = getattr(v, "_cheat_old_hostil", v.hostil)
            return False
        q = min(targets, key=lambda q: q.dist(v.x, v.y))
        key = (q.id, int(q.x // 4), int(q.y // 4), self.mundo.id)
        if getattr(v, "_cheat_enemy_key", None) != key:
            if v.modelo.get("vuela"):
                route = [(q.x, q.y)]
            elif v.modelo.get("barco") or self.mundo.tipo == "mar":
                route = water_route(self.mundo, (v.x, v.y), (q.x, q.y))
            else:
                route = self.mundo.ruta(v.x, v.y, q.x, q.y)
            v._cheat_enemy_route, v._cheat_enemy_key = list(route), key
        route = v._cheat_enemy_route
        while len(route) > 1 and math.dist((v.x, v.y), route[0]) < 0.2:
            route.pop(0)
        if not route:
            v.vel = 0.0
            return True
        if not was_active:
            v._cheat_old_hostil = v.hostil
        v._cheat_autonomous = True
        v.hostil = False
        old = (v.x, v.y)
        new = toward(v, route[0], dt, min(20.0, v.modelo["vel_max"]), v.modelo["acel"])
        if v.modelo.get("vuela") or self.mundo.transitable(*new):
            v.x, v.y = new
        else:
            v.vel = 0.0
            v._cheat_enemy_key = None
        for target in list(targets):
            if segment_distance((target.x, target.y), old, (v.x, v.y)) <= 2.5:
                self.son("golpe", xy=(target.x, target.y))
                self.danar_persona(target, max(1.0, target.salud), atropello=True)
        if v.canal is None:
            self._motor(v, False)
        if v.canal:
            v.canal.mover(v.x, v.y)
            v.canal.tono(v.modelo["tono"] * (0.7 + v.vel / max(1, v.modelo["vel_max"])))
        return True

    def cheat_collect(self):
        if not self.cheat_on("cheat_recoger") or self.transicion:
            return
        # A snapshot permits normal pickup code to remove objects safely. The
        # mission's own recoger handler records progress; no duplicate awards.
        for obj in list(self.objetos):
            if obj in self.objetos and not getattr(obj, "recogido", False) and obj.tipo in ("dinero", "municion", "arma", "valor", "casete", "mision"):
                if obj.tipo == "valor" and not self.cheat_on("cheat_mochila"):
                    from .mochila import CATALOGO
                    item = CATALOGO.get(getattr(obj, "item", ""))
                    if item and self.moc_libre() < item["peso"]:
                        continue  # a full bag must not announce an error every frame
                self.recoger(obj)

    def cheat_step(self):
        self.cheat_sync_growth()
        if self.j.veh:
            self.cheat_repair(self.j.veh)
        self.cheat_collect()
        if not self.j.veh and not self.transicion and self.cheat_on("cheat_contacto"):
            x, y = self.pos()
            for person in list(self.personas):
                if (not person.muerto and person.tipo not in ("civil", "aliado", "perro")
                        and (person.hostil or person.tipo == "enemigo")
                        and not getattr(person, "inofensivo", False) and not getattr(person, "deportivo", False)
                        and person.dist(x, y) <= 2.0):
                    self.danar_persona(person, max(1.0, person.salud))
            self.cheat_collect()

    def cheat_travel(self):
        if self.j.veh or self.transicion:
            return
        target = getattr(self, "objetivo", None)
        if target is not None and not target.muerto and target in self.personas + self.vehiculos:
            x, y = target.x, target.y
            name = target.nombre
        elif self.gps:
            moving = self.gps.get("sigue") or self.gps.get("cosa")
            if moving is not None and hasattr(moving, "x"):
                x, y = moving.x, moving.y
            else:
                x, y = self.gps["dest"]
            name = self.gps["nombre"]
        else:
            self.app.son("error")
            self.decir(text("Fija un enemigo con Q o marca un destino en el GPS.", "Select an enemy with Q or set a GPS destination."), True)
            return
        self.parar_paseo()
        self.teletransportar(x, y)
        self.app.son("menu_ok")
        self.decir(text("Te teletransportas a ", "Teleported to ") + name + ".", True)

    def cheat_expunge(self):
        if not self.cheat_on("cheat_borrar"):
            return
        self.j.antecedentes.clear()
        self.j.cargos_helicoptero = 0
        self._fin_persecucion()
        self.son("menu_ok", cat="interfaz")
        self.decir(text("Tus antecedentes penales quedan borrados. Ya no te buscan.", "Your criminal record has been expunged. You are no longer wanted."), True)


def menu_option(app):
    from .menus import Menu, Opcion

    def open_menu():
        def option(key, es, en, help_es, help_en):
            def change(delta):
                app.cfg[key] = not app.cfg[key]
                p = getattr(app, "partida", None)
                if p:
                    p.cheat_sync_growth()
                    p.cheat_sync_focus()
                    p.cheat_sync_flight()
                    if p.j.veh:
                        p.cheat_repair(p.j.veh)
                app.cfg.guardar()
            return Opcion(lambda: text(es, en) + ": " + (text("sí", "yes") if app.cfg[key] else text("no", "no")),
                          ajuste=change, ayuda=text(help_es, help_en))
        options = [option(*row) for row in OPTIONS]
        from .cheat_time import open_speed_menu, speed_label
        options.append(Opcion(lambda: speed_label(app.cfg), lambda: open_speed_menu(app),
                              ayuda=text("Ajusta el mundo entre cero y quinientos por ciento. Solo actúa al activar el truco del tiempo. Retroceso abre este control durante la partida.",
                                         "Set world speed from zero to five hundred percent. Takes effect only with the world-time cheat enabled. Backspace opens this control in game.")))
        p = getattr(app, "partida", None)
        if p:
            options.append(Opcion(lambda: text("Bajas que mejoran atributos: ", "Kills earned toward base stats: ") + str(p.j.cheat_bajas)
                                  + text(". Daño base: +", ". Base damage: +") + str(2 * p.j.cheat_bajas)
                                  + text(". Salud máxima: +", ". Maximum health: +") + str(p.j.cheat_bajas),
                                  ayuda=text("Los puntos ganados no se pierden al apagar el truco.", "Earned points are retained when the cheat is switched off.")))
        options.append(Opcion(text("Volver", "Back"), lambda: app.cerrar(menu)))
        menu = Menu(app, text("Trucos", "Cheats"), options, al_cerrar=app.cfg.guardar,
                    intro=text("Izquierda y derecha para alternar. Solo en partidas locales.", "Left and right to toggle. Local games only."))
        app.abrir(menu)
    return Opcion(text("Trucos", "Cheats"), open_menu,
                  ayuda=text("Trucos independientes y guardados. F1 explica cada uno.", "Independent saved cheat toggles. F1 explains each option."))
