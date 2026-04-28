import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from datetime import date as date_type, timedelta
from dateutil.relativedelta import relativedelta
np.random.seed(42)
_n = 1000

# Training dataset with historical memory (Modelo_interruptor_3_historico)
_data = np.column_stack([
    np.random.normal(50, 10, _n),           # tiempo_apertura
    np.random.normal(60, 10, _n),           # tiempo_cierre
    np.random.randint(100, 10000, _n).astype(float),  # numero_operaciones
    np.random.normal(20, 5, _n),            # corriente_falla
    np.random.normal(30, 10, _n),           # resistencia_contactos
    np.random.uniform(0, 1, _n),            # IM_prev
    np.random.uniform(0, 1, _n),            # Pmant_prev
    np.random.randint(1, 48, _n).astype(float),       # tiempo_desde_mant
    np.random.normal(0, 0.05, _n),          # delta_IM
])

_y = (
    (_data[:, 0] > 65) |
    (_data[:, 1] > 75) |
    (_data[:, 2] > 8000) |
    (_data[:, 3] > 30) |
    (_data[:, 4] > 50) |
    (_data[:, 5] > 0.7) |
    (_data[:, 6] > 0.7)
).astype(int)

_X_train, _X_test, _y_train, _y_test = train_test_split(
    _data, _y, test_size=0.2, random_state=42
)

_modelo = RandomForestClassifier(
    n_estimators=150,
    random_state=42,
    oob_score=True,
    bootstrap=True,
    n_jobs=-1
)
_modelo.fit(_X_train, _y_train)


def calcular_pmant(ta, tc, no, if_, rc, im_prev, pmant_prev, meses_desde_mant, delta_im):
    entrada = np.array([[ta, tc, no, if_, rc, im_prev, pmant_prev, meses_desde_mant, delta_im]])
    return float(_modelo.predict_proba(entrada)[0, 1])


def calcular_fecha_recomendada(pmant: float, fecha_mantenimiento: date_type) -> date_type:
    """fecha_mantenimiento + round((1 - Pmant) * 36) meses. Mínimo mañana."""
    meses = max(1, round((1 - pmant) * 36))
    fecha = fecha_mantenimiento + relativedelta(months=meses)
    manana = date_type.today() + timedelta(days=1)
    return max(fecha, manana)
