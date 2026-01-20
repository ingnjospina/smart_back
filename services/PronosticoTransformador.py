"""
Servicio de Pronóstico para Transformadores de Potencia
========================================================
Calcula el Índice de Salud (HI), Índice de Riesgo de Mantenimiento (RM)
y fecha óptima de mantenimiento.

Basado en:
- Documento: "Cálculo del índice de salud en transformadores de potencia"
- Notebook: Transformador_HI_Mantenimiento_v3_5_1.ipynb
- Normas: CIGRE TB 761, IEEE C57.104, IEEE C57.91, IEC 60422

Versión simplificada sin pandas.
"""

import os
import csv
import math
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from dateutil.relativedelta import relativedelta


# =====================================================
# CONFIGURACIÓN DE PESOS Y UMBRALES
# =====================================================

WEIGHTS_FUNC = {
    'relacion_transformacion': 8,
    'resistencia_devanados': 6,
    'corriente_excitacion': 5,
    'gases_disueltos': 10
}

WEIGHTS_DIEL = {
    'factor_potencia': 10,
    'calidad_aceite': 6,
    'inhibidor_oxidacion': 3,
    'grado_polimerizacion': 8
}

WEIGHTS_DGA = {
    'hidrogeno': 2,
    'metano': 3,
    'etano': 1,
    'etileno': 3,
    'acetileno': 5,
    'dioxido_carbono': 1,
    'monoxido_carbono': 1
}

WEIGHTS_OQF = {
    'rigidez_dielectrica': 3,
    'tension_interfacial': 2,
    'numero_acidez': 1,
    'contenido_humedad': 4,
    'color': 2,
    'factor_potencia_liquido': 3  # Corregido según Tabla 13 del documento
}

RISK_CONFIG = {
    'alpha': 0.50,
    'beta': 0.35,
    'gamma': 0.15,
    'umbral_RM': 0.70
}

THERMAL_CONFIG = {
    'FAA_norm_lo': 1.0,
    'FAA_norm_hi': 4.0
}


@dataclass
class ResultadoPronostico:
    """Estructura para almacenar todos los resultados del pronóstico"""
    hif_relacion_transformacion: int
    hif_resistencia_devanados: int
    hif_corriente_excitacion: int
    dgaf_porcentaje: float
    hif_gases_disueltos: int
    hif_factor_potencia: int
    oqf_porcentaje: float
    hif_calidad_aceite: int
    hif_inhibidor_oxidacion: int
    hif_grado_polimerizacion: int
    hi_funcional: float
    hi_dielectrico: float
    hi_total: float
    faa_p95: float
    estres_termico: float
    rm_actual: float
    tendencia_hi: float
    fecha_cruce_rm: Optional[datetime]  # DateTimeField en modelo
    fecha_programada: date  # DateField en modelo
    fecha_optima_sugerida: date  # DateField en modelo
    criterio_fecha: str
    condicion_hi: str
    vida_util_remanente: str
    recomendacion: str
    color_alerta: str


class PronosticoTransformador:
    """Clase para calcular el pronóstico de mantenimiento de transformadores."""

    def __init__(self, datos_entrada: Dict, fecha_ultimo_mantenimiento: Union[str, date, datetime]):
        self.datos = datos_entrada
        if isinstance(fecha_ultimo_mantenimiento, str):
            self.fecha_ultimo_mant = datetime.strptime(fecha_ultimo_mantenimiento, '%Y-%m-%d').date()
        elif isinstance(fecha_ultimo_mantenimiento, datetime):
            self.fecha_ultimo_mant = fecha_ultimo_mantenimiento.date()
        else:
            self.fecha_ultimo_mant = fecha_ultimo_mantenimiento
        self.temperaturas_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'temperaturas_30min.csv'
        )

    # =====================================================
    # CÁLCULO DE HIF PARA ÍNDICE FUNCIONAL
    # =====================================================

    def calcular_hif_relacion_transformacion(self, error_pct: float) -> int:
        if error_pct <= 0.1:
            return 4
        elif error_pct <= 0.5:
            return 3
        elif error_pct <= 1.0:
            return 2
        elif error_pct <= 2.0:
            return 1
        return 0

    def calcular_hif_resistencia_devanados(self, error_pct: float) -> int:
        if error_pct <= 1:
            return 4
        elif error_pct <= 2:
            return 3
        elif error_pct <= 3:
            return 2
        elif error_pct <= 5:
            return 1
        return 0

    def calcular_hif_corriente_excitacion(self, patron: int) -> int:
        return 4 if patron in (2, 5) else 0

    def calcular_puntaje_gas(self, gas: str, valor: float) -> int:
        limites = {
            'hidrogeno': [100, 200, 300, 500, 700],
            'metano': [75, 125, 200, 400, 600],
            'etano': [65, 80, 100, 120, 150],
            'etileno': [50, 80, 100, 150, 200],
            'acetileno': [3, 7, 35, 50, 80],
            'dioxido_carbono': [350, 700, 900, 1100, 1400],
            'monoxido_carbono': [2500, 3000, 4000, 5000, 6000]
        }
        lims = limites.get(gas, [])
        if not lims:
            return 1
        for i, lim in enumerate(lims):
            if valor <= lim:
                return i + 1
        return 6

    def calcular_dgaf(self, gases: Dict) -> Tuple[float, int]:
        puntajes = {gas: self.calcular_puntaje_gas(gas, gases.get(gas, 0)) for gas in WEIGHTS_DGA}
        max_puntaje = max(puntajes.values())
        numerador = sum(WEIGHTS_DGA[g] * puntajes[g] for g in puntajes)
        denominador = sum(WEIGHTS_DGA[g] * max_puntaje for g in WEIGHTS_DGA)
        dgaf_pct = (numerador / denominador) * 100 if denominador > 0 else 0

        if dgaf_pct <= 20:
            hif = 4
        elif dgaf_pct <= 30:
            hif = 3
        elif dgaf_pct <= 40:
            hif = 2
        elif dgaf_pct <= 50:
            hif = 1
        else:
            hif = 0
        return round(dgaf_pct, 2), hif

    # =====================================================
    # CÁLCULO DE HIF PARA ÍNDICE DIELÉCTRICO
    # =====================================================

    def calcular_hif_factor_potencia(self, fp_pct: float) -> int:
        if fp_pct <= 0.5:
            return 4
        elif fp_pct <= 0.7:
            return 3
        elif fp_pct <= 1.0:
            return 2
        elif fp_pct <= 2.0:
            return 1
        return 0

    def calcular_puntaje_aceite(self, parametro: str, valor: float) -> int:
        if parametro == 'rigidez_dielectrica':
            if valor >= 45: return 1
            elif valor >= 35: return 2
            elif valor >= 30: return 3
            return 4
        elif parametro == 'tension_interfacial':
            if valor >= 25: return 1
            elif valor >= 20: return 2
            elif valor >= 15: return 3
            return 4
        elif parametro == 'numero_acidez':
            if valor <= 0.05: return 1
            elif valor <= 0.1: return 2
            elif valor <= 0.2: return 3
            return 4
        elif parametro == 'contenido_humedad':
            if valor <= 15: return 1
            elif valor <= 20: return 2
            elif valor <= 25: return 3
            return 4
        elif parametro == 'color':
            if valor <= 1.5: return 1
            elif valor <= 2.0: return 2
            elif valor <= 2.5: return 3
            return 4
        elif parametro == 'factor_potencia_liquido':
            fp = valor * 0.25
            if fp <= 0.1: return 1
            elif fp <= 0.5: return 2
            elif fp <= 1.0: return 3
            return 4
        return 1

    def calcular_oqf(self, aceite: Dict) -> Tuple[float, int]:
        puntajes = {p: self.calcular_puntaje_aceite(p, aceite.get(p, 0)) for p in WEIGHTS_OQF}
        numerador = sum(WEIGHTS_OQF[p] * puntajes[p] for p in puntajes)
        denominador = sum(WEIGHTS_OQF.values())
        oqf_pct = (numerador / denominador) if denominador > 0 else 0

        if oqf_pct <= 1.2:
            hif = 4
        elif oqf_pct <= 1.5:
            hif = 3
        elif oqf_pct <= 2.0:
            hif = 2
        elif oqf_pct <= 3.0:
            hif = 1
        else:
            hif = 0
        return round(oqf_pct, 2), hif

    def calcular_hif_inhibidor(self, inh_pct: float) -> int:
        if inh_pct > 0.25: return 4
        elif inh_pct > 0.2: return 3
        elif inh_pct > 0.15: return 2
        elif inh_pct > 0.1: return 1
        return 0

    def calcular_hif_furanos(self, dp: float) -> int:
        """
        Calcula HIF basado en DP (Grado de Polimerización).
        Según Tabla 16 del documento Word.
        DP indica la degradación del papel aislante.
        """
        if dp > 700:
            return 4  # Muy bueno - papel nuevo/excelente
        elif dp > 560:
            return 3  # Bueno - envejecimiento leve
        elif dp > 425:
            return 2  # Regular - envejecimiento moderado
        elif dp > 250:
            return 1  # Pobre - envejecimiento significativo
        return 0  # Muy pobre - fin de vida útil del papel

    # =====================================================
    # CÁLCULO DE ÍNDICES DE SALUD
    # =====================================================

    def calcular_hi_funcional(self, hifs: Dict) -> float:
        numerador = sum(WEIGHTS_FUNC[k] * hifs[k] for k in WEIGHTS_FUNC)
        denominador = sum(4 * WEIGHTS_FUNC[k] for k in WEIGHTS_FUNC)
        return round((numerador / denominador) * 100, 2) if denominador > 0 else 0

    def calcular_hi_dielectrico(self, hifs: Dict) -> float:
        numerador = sum(WEIGHTS_DIEL[k] * hifs[k] for k in WEIGHTS_DIEL)
        denominador = sum(4 * WEIGHTS_DIEL[k] for k in WEIGHTS_DIEL)
        return round((numerador / denominador) * 100, 2) if denominador > 0 else 0

    def calcular_hi_total(self, hi_func: float, hi_diel: float) -> float:
        return round(0.5 * hi_func + 0.5 * hi_diel, 2)

    # =====================================================
    # CÁLCULO DE ESTRÉS TÉRMICO (sin pandas)
    # =====================================================

    def cargar_temperaturas(self) -> List[float]:
        """Carga el archivo de temperaturas y retorna lista de valores."""
        if not os.path.exists(self.temperaturas_path):
            return []

        temperaturas = []
        with open(self.temperaturas_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    temp = float(row.get('Temp_C', 0))
                    temperaturas.append(temp)
                except (ValueError, TypeError):
                    continue
        return temperaturas

    def calcular_faa(self, theta_h: float) -> float:
        """Calcula el Factor de Aceleración de Envejecimiento (FAA)."""
        return math.exp(15000/383.0 - 15000.0/(theta_h + 273.0))

    def percentil(self, datos: List[float], p: float) -> float:
        """Calcula el percentil p de una lista de datos."""
        if not datos:
            return 0
        sorted_data = sorted(datos)
        k = (len(sorted_data) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_data[int(k)]
        return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)

    def calcular_estres_termico(self) -> Tuple[float, float]:
        """Calcula el estrés térmico normalizado (0-1)."""
        temps = self.cargar_temperaturas()
        if not temps:
            return 1.0, 0.0

        # Calcular FAA para cada temperatura
        faas = [self.calcular_faa(t) for t in temps]

        # Percentil 95 de FAA
        faa_p95 = self.percentil(faas, 95)

        # Normalizar a 0-1
        lo = THERMAL_CONFIG['FAA_norm_lo']
        hi = THERMAL_CONFIG['FAA_norm_hi']
        estres = max(0, min(1, (faa_p95 - lo) / (hi - lo)))

        return round(faa_p95, 4), round(estres, 4)

    # =====================================================
    # CÁLCULO DE ÍNDICE DE RIESGO DE MANTENIMIENTO
    # =====================================================

    def calcular_rm(self, hi_total: float, estres_termico: float, tendencia_hi: float = 0.0) -> float:
        """
        Calcula el Índice de Riesgo de Mantenimiento (RM).

        NOTA: Como en este servicio HI alto = transformador bueno,
        invertimos el HI para que RM bajo = bajo riesgo (consistente con notebook).

        Fórmula: RM = α×(1-HI/100) + β×TS + γ×tendencia
        - HI=100 (perfecto) → hi_invertido=0 → RM bajo
        - HI=0 (malo) → hi_invertido=1 → RM alto
        """
        alpha = RISK_CONFIG['alpha']
        beta = RISK_CONFIG['beta']
        gamma = RISK_CONFIG['gamma']
        # Invertir HI: hi_total alto (bueno) → hi_invertido bajo
        hi_invertido = (100 - hi_total) / 100.0
        tendencia_scaled = max(0, min(1, tendencia_hi))
        rm = alpha * hi_invertido + beta * estres_termico + gamma * tendencia_scaled
        return round(max(0, min(1, rm)), 4)

    # =====================================================
    # CÁLCULO DE FECHAS DE MANTENIMIENTO
    # =====================================================

    def calcular_fecha_cruce_rm(self, rm_actual: float, tendencia: float = 0.01) -> Optional[datetime]:
        """Retorna datetime para compatibilidad con DateTimeField de Django."""
        umbral = RISK_CONFIG['umbral_RM']
        if rm_actual >= umbral:
            return datetime.now()
        if tendencia <= 0:
            return None
        dias_hasta_cruce = (umbral - rm_actual) / tendencia
        if dias_hasta_cruce > 365 * 20:
            return None
        return datetime.now() + timedelta(days=int(dias_hasta_cruce))

    def calcular_fechas_mantenimiento(self, rm_actual: float, tendencia: float = 0.01) -> Tuple[Optional[datetime], date, date, str]:
        # Fecha por intervalo (3 años) - retorna date
        fecha_programada = self.fecha_ultimo_mant + relativedelta(years=3)

        # Fecha por cruce de RM - retorna datetime o None
        fecha_cruce = self.calcular_fecha_cruce_rm(rm_actual, tendencia)

        if fecha_cruce is not None:
            # Convertir a date para comparación
            fecha_condicion = (fecha_cruce - timedelta(days=21)).date()
            if fecha_condicion < fecha_programada:
                fecha_optima = fecha_condicion
                criterio = 'condicion'
            else:
                fecha_optima = fecha_programada
                criterio = 'tiempo'
        else:
            fecha_optima = fecha_programada
            criterio = 'tiempo'

        # No sugerir fecha anterior a hoy + 14 días
        fecha_minima = date.today() + timedelta(days=14)
        if fecha_optima < fecha_minima:
            fecha_optima = fecha_minima

        return fecha_cruce, fecha_programada, fecha_optima, criterio

    # =====================================================
    # CLASIFICACIÓN Y ALERTA
    # =====================================================

    def clasificar_condicion(self, hi_total: float) -> Tuple[str, str, str, str]:
        if hi_total > 85:
            return ("Muy Bueno", "Más de 15 años", "Continuar mantenimiento normal", "azul")
        elif hi_total > 70:
            return ("Bueno", "Más de 10 años", "Continuar mantenimiento normal", "verde")
        elif hi_total > 50:
            return ("Regular", "Hasta 10 años", "Incrementar frecuencia de pruebas de rutina", "amarillo")
        elif hi_total > 30:
            return ("Pobre", "Menos de 10 años", "Aumentar pruebas de rutina y programar posible cambio", "naranja")
        return ("Muy Pobre", "Fin de vida útil", "Programar cambio lo antes posible", "rojo")

    # =====================================================
    # MÉTODO PRINCIPAL
    # =====================================================

    def calcular_pronostico(self) -> ResultadoPronostico:
        gases = {k: float(self.datos.get(k, 0)) for k in WEIGHTS_DGA}
        aceite = {
            'rigidez_dielectrica': float(self.datos.get('rigidez_dielectrica', 0)),
            'tension_interfacial': float(self.datos.get('tension_interfacial', 0)),
            'numero_acidez': float(self.datos.get('numero_acidez', 0)),
            'contenido_humedad': float(self.datos.get('contenido_humedad', 0)),
            'color': float(self.datos.get('color', 0)),
            'factor_potencia_liquido': float(self.datos.get('factor_potencia_liquido', 0))
        }

        # HIF Funcionales
        hif_relacion = self.calcular_hif_relacion_transformacion(float(self.datos.get('relacion_transformacion', 0)))
        hif_resistencia = self.calcular_hif_resistencia_devanados(float(self.datos.get('resistencia_devanados', 0)))
        hif_corriente = self.calcular_hif_corriente_excitacion(int(self.datos.get('corriente_excitacion', 0)))
        dgaf_pct, hif_dga = self.calcular_dgaf(gases)

        # HIF Dieléctricos
        hif_fp = self.calcular_hif_factor_potencia(float(self.datos.get('factor_potencia', 0)))
        oqf_pct, hif_aceite = self.calcular_oqf(aceite)
        hif_inhibidor = self.calcular_hif_inhibidor(float(self.datos.get('inhibidor_oxidacion', 0)))
        hif_furanos = self.calcular_hif_furanos(float(self.datos.get('grado_polimerizacion', 0)))

        # Índices de Salud
        hifs_func = {
            'relacion_transformacion': hif_relacion,
            'resistencia_devanados': hif_resistencia,
            'corriente_excitacion': hif_corriente,
            'gases_disueltos': hif_dga
        }
        hifs_diel = {
            'factor_potencia': hif_fp,
            'calidad_aceite': hif_aceite,
            'inhibidor_oxidacion': hif_inhibidor,
            'grado_polimerizacion': hif_furanos
        }

        hi_funcional = self.calcular_hi_funcional(hifs_func)
        hi_dielectrico = self.calcular_hi_dielectrico(hifs_diel)
        hi_total = self.calcular_hi_total(hi_funcional, hi_dielectrico)

        # Estrés Térmico
        faa_p95, estres_termico = self.calcular_estres_termico()

        # RM
        tendencia_hi = 0.005
        rm_actual = self.calcular_rm(hi_total, estres_termico, tendencia_hi)

        # Fechas
        fecha_cruce, fecha_prog, fecha_optima, criterio = self.calcular_fechas_mantenimiento(rm_actual, tendencia_hi)

        # Clasificación
        condicion, vida_util, recomendacion, color = self.clasificar_condicion(hi_total)

        return ResultadoPronostico(
            hif_relacion_transformacion=hif_relacion,
            hif_resistencia_devanados=hif_resistencia,
            hif_corriente_excitacion=hif_corriente,
            dgaf_porcentaje=dgaf_pct,
            hif_gases_disueltos=hif_dga,
            hif_factor_potencia=hif_fp,
            oqf_porcentaje=oqf_pct,
            hif_calidad_aceite=hif_aceite,
            hif_inhibidor_oxidacion=hif_inhibidor,
            hif_grado_polimerizacion=hif_furanos,
            hi_funcional=hi_funcional,
            hi_dielectrico=hi_dielectrico,
            hi_total=hi_total,
            faa_p95=faa_p95,
            estres_termico=estres_termico,
            rm_actual=rm_actual,
            tendencia_hi=tendencia_hi,
            fecha_cruce_rm=fecha_cruce,
            fecha_programada=fecha_prog,
            fecha_optima_sugerida=fecha_optima,
            criterio_fecha=criterio,
            condicion_hi=condicion,
            vida_util_remanente=vida_util,
            recomendacion=recomendacion,
            color_alerta=color
        )
