"""Esquema del editor para la vida honrada y sus consecuencias: los números y las frases, los títulos, los empleos fijos,
las mejoras de los negocios, las decisiones de los puestos con responsabilidad y las situaciones de la calle."""
from juego.i18n import tr
from juego.honrado import AJ


def c(k, e, t="texto", ayuda="", **kw):
    d = {"k": k, "e": e, "t": t, "ayuda": ayuda}
    d.update(kw)
    return d


# clave: (etiqueta, pestaña, ayuda, mínimo, máximo)
_NUMEROS = {
    "factor_suave": (tr("Nivel suave: tanto por ciento de las penalizaciones"), tr("General"), tr("Respecto al nivel normal, que es cien. Las ventajas no cambian con el nivel."), 1, 100),
    "factor_exigente": (tr("Nivel exigente: tanto por ciento de las penalizaciones"), tr("General"), "", 100, 400),
    "rebaja_aprecian": (tr("Rebaja en las tiendas donde te aprecian, por ciento"), tr("Comercios"), tr("Con 40 de prestigio o más."), 0, 90),
    "rebaja_ejemplar": (tr("Rebaja al ciudadano ejemplar, por ciento"), tr("Comercios"), tr("Con 75 de prestigio o más."), 0, 90),
    "recargo_evitan": (tr("Recargo donde te evitan, por ciento"), tr("Comercios"), tr("Con menos de 10 de prestigio, en el nivel normal."), 0, 200),
    "fiado_aprecian": (tr("Lo que te fían donde te aprecian, en euros"), tr("Comercios"), "", 0, 100000),
    "fiado_ejemplar": (tr("Lo que le fían al ciudadano ejemplar"), tr("Comercios"), "", 0, 100000),
    "fiado_dias": (tr("Días tras los que el fiado se cobra con las facturas"), tr("Comercios"), "", 1, 365),
    "negativa_prob": (tr("Probabilidad de que no te atiendan, por ciento"), tr("Comercios"), tr("Solo en el nivel exigente y donde te evitan. Se decide una vez al día en cada comercio."), 0, 100),
    "encubren_prob": (tr("Probabilidad de que los vecinos encubran una falta, por ciento"), tr("Testigos y policía"), tr("Al ciudadano ejemplar; a quien aprecian, la mitad. Solo sin agentes delante."), 0, 100),
    "encubren_puntos": (tr("Gravedad máxima de la falta que encubren"), tr("Testigos y policía"), tr("En puntos de delito: un golpe a un coche es uno; un disparo, más."), 0, 20),
    "delatan_extra": (tr("Cuánto más cuenta un delito donde te evitan, por ciento"), tr("Testigos y policía"), "", 0, 300),
    "duda_puntos": (tr("Gravedad máxima con beneficio de la duda"), tr("Testigos y policía"), tr("Un agente la deja pasar una vez al día si te aprecian y tu ficha está limpia."), 0, 20),
    "fichado_extra": (tr("Cuánto más cuenta un delito por cada punto de antecedentes, por ciento"), tr("Testigos y policía"), tr("Un antecedente leve pesa uno; uno medio, dos; uno grave, cuatro."), 0, 100),
    "control_prob": (tr("Probabilidad diaria de que te pare un agente, por ciento"), tr("Testigos y policía"), tr("Con mala fama o antecedentes, en el nivel normal o exigente, si hay un agente cerca."), 0, 100),
    "control_minutos": (tr("Minutos del juego que te retiene"), tr("Testigos y policía"), "", 1, 240),
    "fama_respeto": (tr("Fama en la calle con la que las bandas respetan tus negocios"), tr("La calle"), "", 0, 1000),
    "fama_descuento": (tr("Descuento máximo de los guardaespaldas por tu fama, por ciento"), tr("La calle"), "", 0, 90),
    "fama_recargo": (tr("Recargo de los guardaespaldas si nadie te conoce, por ciento"), tr("La calle"), "", 0, 200),
    "caduca_leve": (tr("Días que dura un antecedente leve"), tr("Antecedentes"), "", 1, 3650),
    "caduca_media": (tr("Días que dura uno medio"), tr("Antecedentes"), "", 1, 3650),
    "caduca_grave": (tr("Días que dura uno grave"), tr("Antecedentes"), "", 1, 3650),
    "servicio_quita": (tr("Días que quita una sesión de servicios a la comunidad"), tr("Antecedentes"), "", 1, 365),
    "servicio_horas": (tr("Horas de cada sesión"), tr("Antecedentes"), "", 1, 24),
    "abogado_precio": (tr("Precio del recurso de un abogado, por grado"), tr("Antecedentes"), tr("Un antecedente grave cuesta el triple."), 1, 1000000),
    "chavales_fama": (tr("Fama en la calle que baja cada día con los chavales del barrio"), tr("La calle"), tr("En la ONG, sin tocar el prestigio ni el empleo."), 0, 100),
    "chavales_horas": (tr("Horas que pasas con los chavales"), tr("La calle"), "", 1, 24),
    "chavales_prestigio": (tr("Prestigio que sube cada día con los chavales"), tr("La calle"), "", 0, 100),
    "periodo_dias": (tr("Días de cada periodo de trabajo"), tr("Carrera profesional"), tr("Al acabar cada periodo llega la evaluación y la nómina."), 1, 365),
    "meritos_ascenso": (tr("Evaluaciones buenas para ascender"), tr("Carrera profesional"), "", 1, 100),
    "avisos_despido": (tr("Avisos con los que te despiden"), tr("Carrera profesional"), "", 1, 100),
    "nota_buena": (tr("Nota desde la que la evaluación es buena"), tr("Carrera profesional"), tr("De cero a cien: sesenta puntos por cumplir los turnos y cuarenta por hacerlos bien."), 1, 100),
    "nota_correcta": (tr("Nota desde la que es correcta"), tr("Carrera profesional"), "", 1, 100),
    "nota_floja": (tr("Nota desde la que es floja; por debajo, muy mala"), tr("Carrera profesional"), "", 1, 100),
    "prima_buena": (tr("Prima por una evaluación buena, por ciento de la nómina"), tr("Carrera profesional"), "", 0, 500),
    "veto_dias": (tr("Días sin poder volver a la empresa que te despide"), tr("Carrera profesional"), "", 1, 3650),
    "carta_periodos": (tr("Periodos sin avisos para irte con carta de recomendación"), tr("Carrera profesional"), "", 1, 1000),
    "incidencia_prob": (tr("Probabilidad de una decisión de responsabilidad en cada turno, por ciento"), tr("Carrera profesional"), tr("Solo en los puestos marcados con responsabilidad."), 0, 100),
    "prestigio_periodo": (tr("Prestigio que da un periodo bien evaluado"), tr("Carrera profesional"), "", 0, 100),
    "prestigio_despido": (tr("Prestigio que quita un despido"), tr("Carrera profesional"), "", 0, 100),
    "titulo_prestigio": (tr("Prestigio que da conseguir un título"), tr("Carrera profesional"), "", 0, 100),
    "empleado_sueldo": (tr("Sueldo diario de un empleado, por ciento de lo que da el negocio de base"), tr("Empresa"), "", 0, 100),
    "empleado_rinde": (tr("Lo que sube el negocio con cada empleado, por ciento"), tr("Empresa"), "", 0, 500),
    "rep_inicial": (tr("Nombre del negocio al empezar, de cero a cien"), tr("Empresa"), "", 1, 100),
    "rep_factor": (tr("Lo que sube o baja el negocio con su nombre, por ciento"), tr("Empresa"), tr("Con el nombre a cien da ese tanto más; con el nombre a cero, ese tanto menos."), 0, 200),
    "atender_horas": (tr("Horas que echas al atender el negocio"), tr("Empresa"), "", 1, 24),
    "atender_rep": (tr("Lo que sube el nombre cada vez que lo atiendes"), tr("Empresa"), "", 0, 100),
    "abandono_dias": (tr("Días sin pasar tras los que se da por abandonado"), tr("Empresa"), "", 1, 365),
    "abandono_baja": (tr("Lo que baja el nombre cada día de abandono"), tr("Empresa"), "", 0, 100),
    "encargado_sueldo": (tr("Sueldo del encargado, por ciento de lo que da el negocio de base"), tr("Empresa"), tr("Lo cobra cada día. El encargado lleva el negocio por el jugador: nunca se da por abandonado."), 0, 200),
    "encargado_rep": (tr("Lo que sube el nombre cada día con encargado"), tr("Empresa"), "", 0, 100),
    "encargado_tope": (tr("Hasta dónde sube el nombre solo con el encargado, de cero a cien"), tr("Empresa"), tr("Para pasar de ahí, el jugador tiene que atenderlo."), 0, 100),
    "precios_bajos_ingreso": (tr("Con precios bajos, lo que pierde de ingresos, por ciento"), tr("Empresa"), "", 0, 100),
    "precios_bajos_rep": (tr("Con precios bajos, lo que sube el nombre cada día"), tr("Empresa"), "", 0, 100),
    "precios_altos_ingreso": (tr("Con precios altos, lo que gana de más, por ciento"), tr("Empresa"), "", 0, 500),
    "precios_altos_rep": (tr("Con precios altos, lo que baja el nombre cada día"), tr("Empresa"), "", 0, 100),
    "horario_ingreso": (tr("Con horario ampliado, lo que gana de más, por ciento"), tr("Empresa"), "", 0, 500),
    "tapadera_capacidad": (tr("Euros al día que blanquea una tapadera, por nivel del negocio"), tr("Inspecciones y tapadera"), "", 1, 10000000),
    "tapadera_comision": (tr("Comisión del blanqueo, por ciento"), tr("Inspecciones y tapadera"), "", 0, 100),
    "negro_umbral": (tr("Dinero sin justificar desde el que una inspección lo nota"), tr("Inspecciones y tapadera"), "", 1, 100000000),
    "negro_decae": (tr("Lo que se olvida cada día del dinero sin justificar, por ciento"), tr("Inspecciones y tapadera"), "", 0, 100),
    "inspeccion_min": (tr("Días entre inspecciones, como poco"), tr("Inspecciones y tapadera"), "", 1, 3650),
    "inspeccion_max": (tr("Y como mucho"), tr("Inspecciones y tapadera"), "", 1, 3650),
    "sancion_pct": (tr("Sanción de una inspección, por ciento del precio del negocio"), tr("Inspecciones y tapadera"), "", 0, 100),
    "soborno_pct": (tr("Soborno al inspector, por ciento del precio del negocio"), tr("Inspecciones y tapadera"), "", 0, 100),
    "soborno_prob": (tr("Probabilidad de que el soborno salga bien, por ciento"), tr("Inspecciones y tapadera"), tr("Sube con la fama en la calle y baja en el nivel exigente."), 0, 100),
    "plazo_asunto": (tr("Días para decidir un asunto pendiente"), tr("Inspecciones y tapadera"), tr("Una inspección, un periodista o una extorsión. Pasado el plazo se resuelve solo."), 1, 365),
    "impuesto_negocio": (tr("Impuesto sobre lo que dan los negocios, por ciento"), tr("Impuestos y facturas"), tr("En el nivel normal."), 0, 100),
    "impuesto_casa": (tr("Contribución de las viviendas, por cada diez mil euros de precio"), tr("Impuestos y facturas"), tr("En cada cobro."), 0, 10000),
    "factura_casa": (tr("Luz y agua de cada vivienda, en euros"), tr("Impuestos y facturas"), tr("En cada cobro."), 0, 100000),
    "cobro_dias": (tr("Días entre cobros"), tr("Impuestos y facturas"), "", 1, 365),
    "aviso_dias": (tr("Días de antelación del aviso"), tr("Impuestos y facturas"), tr("Vale también para las cuotas de los créditos."), 1, 30),
    "recargo": (tr("Recargo por impago, por ciento"), tr("Impuestos y facturas"), "", 0, 200),
    "gracia_dias": (tr("Días de gracia al empezar"), tr("Impuestos y facturas"), tr("En una partida nueva y en una de antes de esta versión: hasta entonces no se cobra nada."), 1, 365),
    "impagos_embargo": (tr("Impagos seguidos que traen el embargo"), tr("Impuestos y facturas"), "", 1, 100),
    "embargo_pct": (tr("Parte de tus ingresos que se queda el embargo, por ciento"), tr("Impuestos y facturas"), "", 1, 100),
    "solvencia_prestigio": (tr("Peso del prestigio en la solvencia, por ciento"), tr("Banco"), "", 0, 100),
    "solvencia_ingresos": (tr("Euros de ingresos por semana que valen un punto de solvencia"), tr("Banco"), "", 1, 100000),
    "solvencia_ingresos_tope": (tr("Puntos de solvencia que pueden dar los ingresos, como mucho"), tr("Banco"), "", 0, 100),
    "credito_por_punto": (tr("Euros de crédito por punto de solvencia"), tr("Banco"), "", 1, 1000000),
    "credito_min_solvencia": (tr("Solvencia mínima para un crédito personal"), tr("Banco"), "", 0, 100),
    "credito_cuotas": (tr("Cuotas de un crédito personal"), tr("Banco"), "", 1, 500),
    "interes_bueno": (tr("Interés con solvencia excelente, por ciento"), tr("Banco"), "", 0, 500),
    "interes_medio": (tr("Interés con solvencia buena"), tr("Banco"), "", 0, 500),
    "interes_malo": (tr("Interés con solvencia justa"), tr("Banco"), "", 0, 500),
    "hipoteca_entrada": (tr("Entrada de una hipoteca, por ciento del precio"), tr("Hipotecas y cuotas"), "", 1, 100),
    "hipoteca_cuotas": (tr("Cuotas de una hipoteca"), tr("Hipotecas y cuotas"), "", 1, 1000),
    "hipoteca_solvencia": (tr("Solvencia mínima para una hipoteca"), tr("Hipotecas y cuotas"), "", 0, 100),
    "hipoteca_interes": (tr("Interés de una hipoteca, por ciento"), tr("Hipotecas y cuotas"), "", 0, 500),
    "cuota_dias": (tr("Días entre cuotas"), tr("Hipotecas y cuotas"), "", 1, 365),
    "reintento_dias": (tr("Días hasta que se reintenta una cuota impagada"), tr("Hipotecas y cuotas"), "", 1, 365),
    "sospecha_delito": (tr("Lo que sube el rumor por cada punto de delito visto"), tr("Doble vida"), tr("El rumor va de cero a cien."), 0, 100),
    "sospecha_detencion": (tr("Lo que sube con una detención"), tr("Doble vida"), "", 0, 100),
    "sospecha_multa": (tr("Lo que sube con una multa pagada a un agente"), tr("Doble vida"), "", 0, 100),
    "sospecha_baja": (tr("Lo que baja cada día tranquilo"), tr("Doble vida"), "", 0, 100),
    "sospecha_rumor": (tr("Nivel desde el que corre el rumor"), tr("Doble vida"), "", 1, 100),
    "sospecha_prensa": (tr("Nivel desde el que la prensa prepara un reportaje"), tr("Doble vida"), "", 1, 100),
    "prensa_prestigio": (tr("Prestigio que quita salir en el periódico"), tr("Doble vida"), "", 0, 100),
    "prensa_soborno": (tr("Lo que pide el periodista por callar"), tr("Doble vida"), "", 0, 10000000),
    "abogado_semana": (tr("Lo que cobra el abogado a la semana"), tr("Doble vida"), "", 0, 10000000),
    "abogado_factor": (tr("Con abogado, tanto por ciento de lo que sube el rumor"), tr("Doble vida"), "", 0, 100),
    "extorsion_min": (tr("Días hasta una extorsión, como poco"), tr("Extorsión y buenas acciones"), tr("Solo a quien tiene un negocio y nadie respeta en la calle."), 1, 3650),
    "extorsion_max": (tr("Y como mucho"), tr("Extorsión y buenas acciones"), "", 1, 3650),
    "extorsion_pct": (tr("Lo que piden, por ciento de lo que da el negocio a la semana"), tr("Extorsión y buenas acciones"), "", 0, 100),
    "extorsion_minimo": (tr("Lo menos que piden, en euros"), tr("Extorsión y buenas acciones"), "", 0, 10000000),
    "extorsion_semanas": (tr("Semanas que dura el pago"), tr("Extorsión y buenas acciones"), "", 1, 520),
    "extorsion_dano_prob": (tr("Probabilidad de que dañen el negocio si te niegas, por ciento"), tr("Extorsión y buenas acciones"), "", 0, 100),
    "extorsion_dano_dias": (tr("Días que el negocio da menos tras el daño"), tr("Extorsión y buenas acciones"), "", 1, 365),
    "extorsion_dano": (tr("Lo que pierde de ingresos esos días, por ciento"), tr("Extorsión y buenas acciones"), "", 0, 100),
    "buena_min": (tr("Minutos del juego entre dos situaciones de la calle, como poco"), tr("Extorsión y buenas acciones"), tr("Las situaciones en las que puedes ayudar o aprovecharte."), 1, 100000),
    "buena_max": (tr("Y como mucho"), tr("Extorsión y buenas acciones"), "", 1, 100000),
    "banda_prestigio": (tr("Prestigio desde el que las bandas te tratan como buena gente"), tr("Extorsión y buenas acciones"),
                        tr("Con defensa propia encendida: sus miembros a veces te dejan pasar, y tumbar a quien te ataca primero no trae guerra."), 0, 100),
    "banda_deja_prob": (tr("Probabilidad de que uno de una banda deje pasar a la buena gente, por ciento"), tr("Extorsión y buenas acciones"), tr("Cero: nunca."), 0, 100),
    "banda_defensa_rep": (tr("Reputación con una banda que pierdes al tumbar en defensa propia a uno de los suyos"), tr("Extorsión y buenas acciones"),
                          tr("Cuando no tienes prestigio de buena gente. Si le atacas tú primero, son cuatro puntos, como siempre."), 0, 100),
    "compromiso_afinidad": (tr("Afinidad para prometerse"), tr("Pareja"), "", 1, 100),
    "compromiso_citas": (tr("Citas para prometerse"), tr("Pareja"), "", 0, 1000),
    "boda_dias": (tr("Días entre el compromiso y la boda"), tr("Pareja"), "", 1, 3650),
    "boda_precio": (tr("Lo que cuesta la boda"), tr("Pareja"), "", 0, 10000000),
    "boda_prestigio": (tr("Prestigio que da casarse"), tr("Pareja"), "", 0, 100),
}

# clave: (etiqueta, pestaña, huecos que admite la frase)
_FRASES = {
    "caracteres_jefe": (tr("Caracteres de los jefes"), tr("Frases del trabajo"), tr("Uno al azar al firmar. Si empieza por exigente, evalúa más duro; por paciente, más blando.")),
    "frases_dos_caminos": (tr("Lo que se dice al empezar: hay dos caminos"), tr("Frases generales"), ""),
    "frases_partida_antigua": (tr("Aviso a una partida de antes de esta versión"), tr("Frases generales"), tr("{dias} son los días de gracia.")),
    "frases_encubren": (tr("Los vecinos te encubren"), tr("Frases generales"), ""),
    "frases_duda": (tr("Un agente te da el beneficio de la duda"), tr("Frases generales"), ""),
    "frases_delatan": (tr("Los vecinos te delatan"), tr("Frases generales"), ""),
    "frases_control": (tr("Un agente te para"), tr("Frases generales"), ""),
    "frases_fiado": (tr("Te fían en una tienda"), tr("Frases generales"), "{euros}."),
    "frases_negativa": (tr("No te atienden"), tr("Frases generales"), ""),
    "frases_firma": (tr("Firmas un contrato"), tr("Frases del trabajo"), "{empresa}, {jefe}, {caracter}, {puesto}, {cupo}, {dias}, {sueldo}."),
    "frases_turno": (tr("Turno apuntado"), tr("Frases del trabajo"), "{jefe}, {hechos}, {cupo}."),
    "frases_falta_turnos": (tr("Aviso de que te faltan turnos"), tr("Frases del trabajo"), "{jefe}, {dias}, {faltan}."),
    "frases_eval_buena": (tr("Evaluación buena"), tr("Frases del trabajo"), "{jefe}, {sueldo}, {prima}."),
    "frases_eval_correcta": (tr("Evaluación correcta"), tr("Frases del trabajo"), "{jefe}, {sueldo}."),
    "frases_eval_floja": (tr("Evaluación floja"), tr("Frases del trabajo"), "{jefe}, {sueldo}, {avisos}, {tope}."),
    "frases_eval_mala": (tr("Evaluación muy mala"), tr("Frases del trabajo"), "{jefe}, {avisos}, {tope}."),
    "frases_ascenso": (tr("Ascenso"), tr("Frases del trabajo"), "{jefe}, {puesto}, {cupo}, {sueldo}."),
    "frases_ascenso_falta": (tr("Ascenso que espera a que cumplas lo que pide"), tr("Frases del trabajo"), "{jefe}, {puesto}, {falta}."),
    "frases_despido": (tr("Despido"), tr("Frases del trabajo"), "{jefe}, {empresa}, {motivo}."),
    "frases_aviso_antecedente": (tr("Tu jefe se entera de un antecedente"), tr("Frases del trabajo"), "{empresa}, {jefe}, {avisos}, {tope}."),
    "frases_dimision": (tr("Dimisión"), tr("Frases del trabajo"), "{jefe}, {empresa}."),
    "frases_carta": (tr("Carta de recomendación"), tr("Frases del trabajo"), "{jefe}."),
    "frases_titulo_sesion": (tr("Sesión de un título"), tr("Frases de estudios y negocios"), "{nombre}, {hechas}, {total}, {quedan}, {horas}, {hora}."),
    "frases_titulo": (tr("Título conseguido"), tr("Frases de estudios y negocios"), "{nombre}, {abre}."),
    "frases_atender": (tr("Atiendes tu negocio"), tr("Frases de estudios y negocios"), "{negocio}, {horas}, {hora}."),
    "frases_abandono": (tr("Un negocio abandonado"), tr("Frases de estudios y negocios"), "{negocio}."),
    "frases_inspeccion_limpia": (tr("Inspección sin faltas"), tr("Frases de estudios y negocios"), "{negocio}."),
    "frases_inspeccion_falta": (tr("Inspección con irregularidades"), tr("Frases de estudios y negocios"), "{negocio}, {dias}."),
    "frases_soborno_ok": (tr("El soborno al inspector sale bien"), tr("Frases de estudios y negocios"), ""),
    "frases_soborno_mal": (tr("El soborno sale mal"), tr("Frases de estudios y negocios"), ""),
    "frases_cobro_aviso": (tr("Aviso del cobro de facturas e impuestos"), tr("Frases del banco"), "{dias}, {euros}."),
    "frases_cobro": (tr("Cobro de facturas e impuestos"), tr("Frases del banco"), "{euros}, {detalle}."),
    "frases_impago": (tr("No llega para las facturas"), tr("Frases del banco"), "{falta}."),
    "frases_embargo": (tr("Embargo"), tr("Frases del banco"), "{euros}."),
    "frases_embargo_fin": (tr("Fin del embargo"), tr("Frases del banco"), ""),
    "frases_cuota_aviso": (tr("Aviso de una cuota"), tr("Frases del banco"), "{dias}, {tipo}, {euros}."),
    "frases_cuota": (tr("Cuota pagada"), tr("Frases del banco"), "{tipo}, {euros}, {quedan}."),
    "frases_cuota_fin": (tr("Última cuota"), tr("Frases del banco"), "{tipo}."),
    "frases_cuota_impago": (tr("Cuota sin pagar"), tr("Frases del banco"), "{tipo}, {euros}, {dias}, {impagos}, {tope}."),
    "frases_rumor": (tr("Empieza a correr el rumor"), tr("Frases de la doble vida"), ""),
    "frases_prensa_aviso": (tr("Un periodista prepara un reportaje"), tr("Frases de la doble vida"), "{dias}."),
    "frases_prensa": (tr("Sale en el periódico"), tr("Frases de la doble vida"), "{nombre}."),
    "frases_prensa_callada": (tr("Pagas al periodista"), tr("Frases de la doble vida"), ""),
    "frases_prensa_abogado": (tr("Tu abogado frena el reportaje"), tr("Frases de la doble vida"), ""),
    "frases_abogado": (tr("Contratas a un abogado"), tr("Frases de la doble vida"), "{euros}."),
    "frases_abogado_fin": (tr("Te quedas sin abogado"), tr("Frases de la doble vida"), ""),
    "frases_extorsion": (tr("Una banda te pide dinero"), tr("Frases de la extorsión"), "{banda}, {negocio}, {euros}, {dias}."),
    "frases_extorsion_vecino": (tr("Un vecino te avisa"), tr("Frases de la extorsión"), "{banda}."),
    "frases_extorsion_pago": (tr("Pagas"), tr("Frases de la extorsión"), "{banda}, {euros}, {semanas}."),
    "frases_extorsion_denuncia": (tr("Denuncias y sale bien"), tr("Frases de la extorsión"), "{banda}."),
    "frases_extorsion_denuncia_mal": (tr("Denuncias y sale mal"), tr("Frases de la extorsión"), "{negocio}."),
    "frases_extorsion_plantas": (tr("Les plantas cara"), tr("Frases de la extorsión"), ""),
    "frases_extorsion_nada": (tr("Te niegas y no pasa nada"), tr("Frases de la extorsión"), ""),
    "frases_extorsion_dano": (tr("Te niegas y dañan el negocio"), tr("Frases de la extorsión"), "{negocio}."),
    "frases_buena_nada": (tr("Sigues tu camino ante una situación"), tr("Frases de la extorsión"), ""),
    "frases_banda_deja": (tr("Uno de una banda deja pasar a la buena gente"), tr("Frases de la extorsión"), tr("{nombre} es el de la banda.")),
    "frases_defensa_buena": (tr("Tumbas en defensa propia siendo buena gente"), tr("Frases de la extorsión"), ""),
    "frases_chavales": (tr("Una tarde con los chavales del barrio"), tr("Frases de la extorsión"), tr("Con {horas} y {hora}.")),
    "frases_compromiso": (tr("Os prometéis"), tr("Frases de la pareja"), tr("{n} es su nombre.")),
    "frases_compromiso_pronto": (tr("Todavía es pronto para prometerse"), tr("Frases de la pareja"), "{n}."),
    "frases_boda": (tr("La boda"), tr("Frases de la pareja"), "{n}."),
}


_ENTEROS = ("_dias", "_min", "_max", "_horas", "_cuotas", "_semanas", "_periodos", "_minutos", "_despido", "_ascenso", "_embargo", "_precio", "_semana", "_soborno", "_minimo",
            "_capacidad", "_umbral", "_citas", "_asunto", "_aprecian", "_ejemplar")


def _campos_ajuste():
    campos = [c("id", tr("Identificador"), req=True, defecto="general", ayuda=tr("Déjalo en general: solo se usa el primero."))]
    for k, serie in AJ._n.items():
        e, grupo, ayuda, minimo, maximo = _NUMEROS[k]
        campos.append(c(k, e, "entero" if k.endswith(_ENTEROS) else "decimal", ayuda, minimo=minimo, maximo=maximo,
                        defecto=int(serie) if float(serie).is_integer() else serie, **({} if grupo == "General" else {"grupo": grupo})))
    for k in AJ._l:
        e, grupo, huecos = _FRASES[k]
        campos.append(c(k, e, "textos", (tr("Una por línea; se dice una al azar. ") + (tr("Huecos: ") + huecos if huecos.startswith("{") else huecos)).strip(), grupo=grupo))
    return campos


_EFECTOS = [
    c("prestigio", tr("Prestigio que da o quita"), "decimal", tr("Entre los vecinos. Negativo, si lo quita."), minimo=-100, maximo=100),
    c("fama", tr("Fama en la calle que da o quita"), "decimal", minimo=-100, maximo=100),
    c("dinero", tr("Dinero que da, o que cuesta si es negativo"), "entero"),
    c("animo", tr("Ánimo que da o quita"), "decimal", minimo=-100, maximo=100),
    c("salud", tr("Salud que da o quita"), "decimal", minimo=-100, maximo=100),
    c("dice", tr("Lo que se cuenta"), "largo", req=True),
]

ESQUEMAS = {
    "ajuste_honrado": {"titulo": tr("Vida, reputación y consecuencias: números y frases"),
                       "resumen": lambda d: tr('Suave al {get} por ciento; cobros cada {get2} días; periodos de trabajo de {get3} días').format(get=(d.get('factor_suave', 60)), get2=(d.get('cobro_dias', 7)), get3=(d.get('periodo_dias', 7))),
                       "campos": _campos_ajuste()},
    "titulo_estudios": {"titulo": tr("Título de estudios"), "resumen": lambda d: tr('{get}: {get2} sesiones de {get3} euros').format(get=(d.get('nombre', '?')), get2=(d.get('sesiones', '?')), get3=(d.get('precio', '?'))), "campos": [
        c("id", tr("Identificador"), req=True, ayuda=tr("Único. Los puestos y las mejoras de negocio lo usan para pedir este título.")),
        c("nombre", tr("Nombre"), req=True),
        c("sesiones", tr("Sesiones que lleva"), "entero", tr("Una al día."), req=True, minimo=1, maximo=100, defecto=4),
        c("precio", tr("Precio de cada sesión"), "entero", req=True, minimo=0, defecto=120),
        c("horas", tr("Horas de cada sesión"), "entero", minimo=1, maximo=12, defecto=3),
        c("prestigio", tr("Prestigio mínimo para matricularse"), "entero", minimo=0, maximo=100),
        c("requiere", tr("Título que hay que tener antes"), "ref", ref="titulo_estudios"),
        c("desc", tr("Descripción"), "largo"),
        c("abre", tr("Qué abre"), "largo", tr("Se dice al conseguirlo y en la ayuda: qué puestos o qué mejoras permite."))]},
    "empleo_fijo": {"titulo": tr("Empleo fijo"), "resumen": lambda d: tr('{get}, en {get2}: {len} puestos').format(get=(d.get('nombre', '?')), get2=(d.get('empresa', '?')), len=(len(d.get('puestos') or []))), "campos": [
        c("id", tr("Identificador"), req=True),
        c("nombre", tr("Nombre del oficio"), req=True),
        c("empresa", tr("Empresa"), req=True),
        c("desc", tr("Descripción"), "largo"),
        c("confianza", tr("Empleo de confianza: pide la ficha limpia"), "si_no", tr("Con sí, no contratan con antecedentes graves, y un antecedente nuevo puede costar el puesto.")),
        c("cuenta", tr("Trabajos que cuentan como turno"), "textos", tr("Uno por línea. Una jornada se escribe jornada, dos puntos y su identificador: jornada:camarero. "
          "Un oficio con vehículo, oficio, dos puntos y su tipo: oficio:taxi. Tres servicios con vehículo hacen un turno."), req=True),
        c("puestos", tr("Puestos, del primero al más alto"), "lista", sub="puesto_fijo", req=True)]},
    "puesto_fijo": {"titulo": tr("Puesto"), "resumen": lambda d: tr('{get}: {get2} euros por periodo, {get3} turnos').format(get=(d.get('nombre', '?')), get2=(d.get('sueldo', '?')), get3=(d.get('cupo', '?'))), "campos": [
        c("nombre", tr("Nombre del puesto"), req=True, ayuda=tr("En minúscula. Admite las marcas de género: camarer[o|a].")),
        c("sueldo", tr("Nómina por periodo"), "entero", req=True, minimo=0, defecto=200),
        c("cupo", tr("Turnos que pide por periodo"), "entero", req=True, minimo=1, maximo=50, defecto=3),
        c("titulo", tr("Título que pide"), "ref", ref="titulo_estudios"),
        c("prestigio", tr("Prestigio mínimo"), "entero", minimo=0, maximo=100),
        c("mando", tr("Con responsabilidad: trae decisiones que cuentan en la evaluación"), "si_no")]},
    "mejora_negocio": {"titulo": tr("Mejora de un negocio"), "resumen": lambda d: tr('Nivel {get}: {get2}').format(get=(d.get('nivel', '?')), get2=(d.get('nombre', '?'))), "campos": [
        c("id", tr("Identificador"), req=True),
        c("nivel", tr("Nivel al que lleva"), "entero", tr("El primero es el dos; un negocio recién comprado está en el uno."), req=True, minimo=2, maximo=20, defecto=2),
        c("nombre", tr("Nombre"), req=True),
        c("coste", tr("Lo que cuesta, por ciento del precio del negocio"), "entero", req=True, minimo=0, maximo=1000, defecto=35),
        c("ingresos", tr("Lo que sube lo que da, por ciento sobre la base"), "entero", req=True, minimo=0, maximo=1000, defecto=25),
        c("titulo", tr("Título que pide"), "ref", ref="titulo_estudios"),
        c("prestigio", tr("Prestigio mínimo"), "entero", minimo=0, maximo=100)]},
    "incidencia_trabajo": {"titulo": tr("Decisión de un puesto con responsabilidad"), "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("id", tr("Identificador"), req=True),
        c("texto", tr("La situación"), "largo", req=True),
        c("opciones", tr("Lo que puedes hacer"), "lista", tr("De dos a cuatro."), sub="opcion_incidencia", req=True)]},
    "opcion_incidencia": {"titulo": tr("Opción"), "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("texto", tr("Lo que elige el jugador"), req=True),
        c("ayuda", tr("Explicación con F1"), "largo"),
        c("calidad", tr("Lo que suma o resta a la calidad del turno"), "decimal", tr("La calidad va de cero a cien y cuenta el cuarenta por ciento de la evaluación."), minimo=-100, maximo=100),
        c("dice", tr("Lo que se cuenta al elegirla"), "largo", req=True)]},
    "buena_accion": {"titulo": tr("Situación de la calle: ayudar o aprovecharse"), "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("id", tr("Identificador"), req=True),
        c("texto", tr("La situación"), "largo", req=True),
        c("opciones", tr("Lo que puedes hacer"), "lista", tr("De una a cuatro. Seguir tu camino está siempre."), sub="opcion_buena", req=True)]},
    "opcion_buena": {"titulo": tr("Opción"), "resumen": lambda d: d.get("texto", "")[:70], "campos": [
        c("texto", tr("Lo que elige el jugador"), req=True),
        c("ayuda", tr("Explicación con F1"), "largo"),
        c("tentacion", tr("Es una tentación: aprovecharse"), "si_no", grupo=tr("Requisitos")),
        c("pide", tr("Objeto que hace falta y se gasta"), "ref", ref="objeto", grupo=tr("Requisitos")),
        c("sin", tr("Lo que se dice si no lo llevas"), "largo", grupo=tr("Requisitos")),
        c("coste", tr("Dinero que cuesta"), "entero", minimo=0, grupo=tr("Requisitos")),
        c("horas", tr("Horas que lleva"), "decimal", minimo=0, maximo=24, grupo=tr("Requisitos")),
        c("delito", tr("Cuánto da que hablar, en puntos de delito"), "decimal", tr("Sube lo que se sabe de tu otra vida."), minimo=0, maximo=20, grupo=tr("Requisitos")),
        c("riesgo", tr("Probabilidad de que salga mal, por ciento"), "decimal", minimo=0, maximo=100, grupo=tr("Si sale mal")),
        c("mal", tr("Lo que pasa si sale mal"), "objeto", sub="resultado_buena", grupo=tr("Si sale mal")),
    ] + [dict(x, grupo=tr("Si sale bien")) for x in _EFECTOS]},
    "resultado_buena": {"titulo": tr("Si sale mal"), "campos": [dict(x) for x in _EFECTOS]},
    "requisitos_vida": {"titulo": tr("Lo que la misión pide de tu vida"), "campos": [
        c("contrato", tr("Tener un contrato fijo"), "entero", tr("Uno, si hace falta."), minimo=0, maximo=1),
        c("turnos", tr("Turnos trabajados con contrato, en total"), "entero", minimo=0),
        c("titulos", tr("Títulos conseguidos"), "entero", minimo=0),
        c("prestigio", tr("Prestigio entre los vecinos"), "entero", minimo=0, maximo=100),
        c("negocios", tr("Negocios propios"), "entero", minimo=0),
        c("sin_antecedentes", tr("No tener antecedentes en vigor"), "entero", tr("Uno, si hace falta."), minimo=0, maximo=1)]},
    "epilogo": {"titulo": tr("Epílogo del buen camino"), "resumen": lambda d: d.get("titulo", "")[:70], "campos": [
        c("titulo", tr("Nombre de este final"), req=True),
        c("clase", tr("Clase de final"), ayuda=tr("Una palabra: honrado, prudente, doble, redimido. El logro del buen camino pide la clase honrado.")),
        c("texto", tr("Texto del final"), "largo", req=True),
        c("si_clave", tr("Solo si se tomó la decisión"), ayuda=tr("Vacío, vale siempre. Con el nombre de una decisión, este final es el de quien eligió la opción de debajo.")),
        c("si_opcion", tr("Número de la opción elegida"), "entero", minimo=1, maximo=4, defecto=1)]},
}

SECCIONES = [
    ("vida_honrada", tr("Vida, reputación y consecuencias: números y frases"), "ajuste_honrado"), ("titulos", tr("Títulos de estudios"), "titulo_estudios"),
    ("empleos_fijos", tr("Empleos fijos y sus puestos"), "empleo_fijo"), ("mejoras_negocio", tr("Mejoras de los negocios"), "mejora_negocio"),
    ("incidencias_trabajo", tr("Decisiones de los puestos con responsabilidad"), "incidencia_trabajo"), ("buenas_acciones", tr("Situaciones de la calle: ayudar o aprovecharse"), "buena_accion"),
]

# Lo que se añade a los formularios que ya había
CAMPOS_MISION = [
    c("honrada", tr("Es del buen camino: da prestigio en vez de fama y se ofrece sin obligar"), "si_no", tr("Con sí, al completarla sube el prestigio entre los vecinos, no la fama en la calle; "
      "y no empieza sola al llegar a su lugar: aparece como la última opción del menú de ese sitio, o se pregunta si el sitio no tiene menú.")),
    c("orden", tr("Capítulo del buen camino"), "entero", tr("Para contar por dónde va el jugador. Dos misiones de ramas distintas pueden llevar el mismo número."), minimo=1, si=lambda d: d.get("honrada")),
    c("prestigio", tr("Prestigio que da al completarla"), "entero", tr("Vacío, dos."), minimo=0, maximo=100, si=lambda d: d.get("honrada")),
    c("requiere_vida", tr("Lo que pide de la vida del jugador"), "objeto", tr("Además de las misiones anteriores: un contrato, turnos trabajados, títulos, prestigio, negocios o la ficha limpia. "
      "Mientras falte algo, la misión no aparece, y el móvil dice qué falta."), sub="requisitos_vida"),
    c("epilogos", tr("Epílogos: los finales del buen camino"), "lista", tr("Si esta misión cierra el buen camino. Se dice el primero cuya condición se cumpla."), sub="epilogo", si=lambda d: d.get("honrada")),
]
CAMPO_DECISION = c("prestigio", tr("Prestigio que da o quita"), "entero", tr("Entre los vecinos. Es independiente de la fama."), minimo=-100, maximo=100)


def aplicar(esquemas, secciones):
    """Mete todo esto en el esquema general del editor."""
    esquemas.update(ESQUEMAS)
    esquemas["mision"]["campos"].extend(CAMPOS_MISION)       # al final: así las páginas del formulario de misión que ya había no cambian
    dec = esquemas["opcion_decision"]["campos"]
    dec.insert(next(k for k, x in enumerate(dec) if x["k"] == "animo") + 1, CAMPO_DECISION)
    pos = next(k for k, x in enumerate(secciones) if x[0] == "contratos")
    secciones[pos:pos] = SECCIONES
