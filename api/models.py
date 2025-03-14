
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from decimal import Decimal


class Alertas(models.Model):
    idalerta = models.AutoField(db_column='idAlerta', primary_key=True)
    mensaje_condicion = models.CharField(max_length=200)
    vida_util_remanente = models.CharField(max_length=200)
    recomendacion = models.CharField(max_length=200)
    color_alerta = models.CharField(max_length=200)
    fecha_generacion = models.DateTimeField(default=timezone.now)
    mediciones_transformadores = models.ForeignKey('MedicionesTransformadores', on_delete=models.CASCADE, db_column='Mediciones_Transformadores_idMediciones_Transformadores', blank=True, null=True)
    mediciones_interruptores = models.ForeignKey('Medicionesinterruptores', on_delete=models.CASCADE, db_column='MedicionesInterruptores_idMediciones_Interruptores', blank=True, null=True)

    class Meta:
        db_table = 'alertas'


class Analisisaceitefisicoquimico(models.Model):
    idanalisisaceitefisicoquimico = models.AutoField(db_column='idAnalisisAceiteFisicoQuimico', primary_key=True)  # Field name made lowercase.
    rigidez_dieletrica = models.DecimalField(max_digits=10, decimal_places=2)
    tension_interfacial = models.DecimalField(max_digits=10, decimal_places=2)
    numero_acidez = models.DecimalField(max_digits=10, decimal_places=2)
    contenido_humedad = models.DecimalField(max_digits=10, decimal_places=2)
    color = models.DecimalField(max_digits=10, decimal_places=2)
    factor_potencia_liquido = models.DecimalField(max_digits=5, decimal_places=2)
    mediciones_transformadores_idmediciones_transformadores = models.ForeignKey('MedicionesTransformadores', on_delete=models.CASCADE, db_column='Mediciones_Transformadores_idMediciones_Transformadores')  # Field name made lowercase.

    class Meta:
        db_table = 'analisisaceitefisicoquimico'


class Analisisgasesdisueltos(models.Model):
    idanalisisgasesdisueltos = models.AutoField(db_column='idAnalisisGasesDisueltos', primary_key=True)  # Field name made lowercase.
    hidrogeno = models.DecimalField(max_digits=10, decimal_places=2)
    metano = models.DecimalField(max_digits=10, decimal_places=2)
    etano = models.DecimalField(max_digits=10, decimal_places=2)
    etileno = models.DecimalField(max_digits=10, decimal_places=2)
    acetileno = models.DecimalField(max_digits=10, decimal_places=2)
    dioxido_carbono = models.DecimalField(max_digits=10, decimal_places=2)
    monoxido_carbono = models.DecimalField(max_digits=10, decimal_places=2)
    mediciones_transformadores_idmediciones_transformadores = models.ForeignKey('MedicionesTransformadores', on_delete=models.CASCADE, db_column='Mediciones_Transformadores_idMediciones_Transformadores')  # Field name made lowercase.

    class Meta:
        db_table = 'analisisgasesdisueltos'


class Archivospruebas(models.Model):
    TIPO_ARCHIVO_CHOICES = [
        ('pdf', 'pdf'),
        ('excel', 'excel'),
    ]
    idarchivospruebas = models.IntegerField(db_column='idArchivosPruebas', primary_key=True)  # Field name made lowercase.
    nombre_archivo = models.CharField(max_length=255)
    tipo_archivo = models.CharField(max_length=5, choices=TIPO_ARCHIVO_CHOICES)
    ruta_archivo = models.CharField(max_length=255)
    fecha_carga = models.DateTimeField()

    class Meta:
        db_table = 'archivospruebas'


class Interruptores(models.Model):
    idinterruptores = models.AutoField(db_column='idInterruptores', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'interruptores'


class MedicionesTransformadores(models.Model):
    idmediciones_transformadores = models.AutoField(db_column='idMediciones_Transformadores', primary_key=True)
    haveFiles = models.BooleanField(default=False)
    fecha_hora = models.DateTimeField(default=timezone.now)
    ###  Funcional
    relacion_transformacion = models.DecimalField(max_digits=4, decimal_places=3)
    hif_relacion_transformacion = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    resistencia_devanados = models.DecimalField(max_digits=4, decimal_places=3)
    hif_resistencia_devanados = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    corriente_excitacion = models.PositiveSmallIntegerField()
    hif_corriente_excitacion = models.PositiveSmallIntegerField(blank=True, null=True)
    gases_disueltos = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    hif_gases_disueltos = models.DecimalField(max_digits=6, decimal_places=4, blank=True, null=True)
    hi_funcional = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    ## Dielectico
    factor_potencia = models.DecimalField(max_digits=4, decimal_places=3)
    hi_factor_potencia = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    inhibidor_oxidacion = models.DecimalField(max_digits=4, decimal_places=3)
    hi_inhibidor_oxidacion = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    compuestos_furanicos = models.DecimalField(max_digits=7, decimal_places=3)
    hi_compuestos_furanicos = models.DecimalField(max_digits=4, decimal_places=3, blank=True, null=True)
    calidad_aceite_humedad = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    hi_calidad_aceite_humedad = models.DecimalField(max_digits=8, decimal_places=4, blank=True, null=True)
    hi_dielectrico = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    hi_ponderado = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)

    #relación
    transformadores = models.ForeignKey('Transformadores', on_delete=models.CASCADE, db_column='Transformadores_idTransformadores')

    class Meta:
        db_table = 'mediciones_transformadores'


class Medicionesinterruptores(models.Model):
    idmediciones_interruptores = models.IntegerField(db_column='idMediciones_Interruptores', primary_key=True)  # Field name made lowercase.
    fecha = models.DateTimeField()
    corriente_nominal = models.DecimalField(max_digits=10, decimal_places=2)
    tension_operacion = models.DecimalField(max_digits=10, decimal_places=2)
    tiempo_operacion = models.DecimalField(max_digits=10, decimal_places=2)
    interruptores_idinterruptores = models.ForeignKey(Interruptores, on_delete=models.CASCADE, db_column='Interruptores_idInterruptores', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        db_table = 'medicionesinterruptores'


class Transformadores(models.Model):
    idtransformadores = models.AutoField(db_column='idTransformadores', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200)
    deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'transformadores'

class UsuarioManager(BaseUserManager):
    def create_user(self, correo, contrasena=None, **extra_fields):
        if not correo:
            raise ValueError("El usuario debe tener un correo electrónico")
        correo = self.normalize_email(correo)
        usuario = self.model(correo=correo, **extra_fields)
        usuario.set_password(contrasena)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, correo, contrasena=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(correo, contrasena, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    def get_current_time():
        return timezone.now()
    
    ROL_CHOICES = [
        ('Técnico', 'Técnico'),
        ('Administrador', 'Administrador'),
    ]
    idusuario = models.AutoField(db_column='idUsuario', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(max_length=150)
    correo = models.EmailField(unique=True, max_length=100)
    rol = models.CharField(max_length=13, choices=ROL_CHOICES)
    fecha_creacion = models.DateTimeField(default=get_current_time)
    estado = models.CharField(max_length=8)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UsuarioManager()

    groups = models.ManyToManyField(
        Group,
        related_name='usuario_set',  # Cambiar el related_name aquí
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='usuario_permissions',  # Cambiar el related_name aquí
        blank=True,
    )

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'usuario'

    def __str__(self):
        return self.correo
