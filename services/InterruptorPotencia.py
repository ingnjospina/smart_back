class InterruptorPotencia:
    def __init__(self, N_O, T_A, T_C, I_F, R_C):
        # Convertir Decimal a float antes de hacer operaciones
        self.N_O = float(N_O)  # Número de operaciones
        self.T_A = float(T_A)  # Tiempo de apertura (ms)
        self.T_C = float(T_C)  # Tiempo de cierre (ms)
        self.I_F = float(I_F)  # Corriente de falla (A)
        self.R_C = float(R_C)  # Resistencia de contactos (Ω)

        # Parámetros de referencia
        self.N_O_max = 10000.0
        self.T_A_ref = 50.0     # ms
        self.T_C_ref = 50.0     # ms
        self.I_F_max = 40000.0  # A  (= 40 kA)
        self.R_C_ref = 0.00005  # Ω  (= 50 µΩ)

        # Factores de ponderación
        self.alpha_0 = 0.5
        self.alpha_1 = 0.25
        self.alpha_2 = 0.25
        self.beta_1 = 0.5
        self.beta_2 = 0.5
        self.gamma_1 = 0.5
        self.gamma_2 = 0.5
        self.I_M_umbral = 1.5  # Límite para determinar si se necesita mantenimiento

    def calcular_indices(self):
        # Índice de desgaste mecánico
        I_DM = (self.alpha_0 * (self.N_O / self.N_O_max)) + \
               (self.alpha_1 * (abs(self.T_A - self.T_A_ref) / self.T_A_ref)) + \
               (self.alpha_2 * (abs(self.T_C - self.T_C_ref) / self.T_C_ref))

        # Índice de estrés eléctrico
        I_EE = self.beta_1 * (self.I_F / self.I_F_max) + \
               self.beta_2 * (abs(self.R_C - self.R_C_ref) / self.R_C_ref)

        # Índice general de mantenimiento (índice de salud, escala 0-1).
        # Se almacena normalizado: el modelo de pronóstico espera IM en 0-1
        # y la clasificación de alertas / la UI lo expresan como porcentaje.
        I_M = self.gamma_1 * (1 - I_DM) + self.gamma_2 * (1 - I_EE)

        return I_DM, I_EE, I_M