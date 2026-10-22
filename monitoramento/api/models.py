from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Usuario(AbstractUser):

    class TipoUsuario(models.TextChoices):
        ADMINISTRADOR = "ADMIN", "Administrador"
        USUARIO = "USER", "Usuário"

    tipo_usuario = models.CharField(max_length=5, choices=TipoUsuario.choices, default=TipoUsuario.USUARIO,)

    foto_perfil = models.ImageField(upload_to="usuarios/", blank=True, null=True,)



class Local(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "locais"
        ordering = ["nome"]

    def __str__(self):
        return self.nome
    
class ModeloEquipamento(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    fabricante = models.CharField(max_length=100, blank=True)
    descricao = models.TextField(blank=True)

    class Meta:
        db_table = "modelos_equipamentos"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Microcontrolador(models.Model):
    modelo = models.ForeignKey(ModeloEquipamento, on_delete=models.PROTECT, related_name="microcontroladores",)

    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="microcontroladores",)

    mac_address = models.CharField(max_length=17,unique=True,)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90),],)

    longitude = models.DecimalField(max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180),],)

    observacoes = models.TextField(blank=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "microcontroladores"
        ordering = ["id"]

    def __str__(self):
        return self.mac_address


class ModeloSensor(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    fabricante = models.CharField(max_length=100, blank=True)
    descricao = models.TextField(blank=True)

    class Meta:
        db_table = "modelos_sensores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Sensor(models.Model):

    class TipoSensor(models.TextChoices):
        TEMPERATURA = "TEMP", "Temperatura"
        UMIDADE = "UMID", "Umidade"
        LUMINOSIDADE = "LUMI", "Luminosidade"
        CONTAGEM_PASSAGENS = "PASS", "Contagem de passagens"

    class UnidadeMedida(models.TextChoices):
        CELSIUS = "C", "Graus Celsius"
        PORCENTAGEM = "%", "Porcentagem"
        LUX = "LUX", "Lux"
        UNIDADES = "UN", "Unidades"

    modelo = models.ForeignKey(ModeloSensor, on_delete=models.PROTECT, related_name="sensores",)

    microcontrolador = models.ForeignKey(Microcontrolador, on_delete=models.PROTECT, related_name="sensores",
    )

    tipo = models.CharField(max_length=4, choices=TipoSensor.choices,)

    unidade_medida = models.CharField(max_length=3, choices=UnidadeMedida.choices,)

    is_active = models.BooleanField(default=True)

    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sensores"
        ordering = ["id"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.id}"
    
    
class Leitura(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.PROTECT, related_name="leituras",)

    valor = models.DecimalField(max_digits=12, decimal_places=4,)

    data_hora = models.DateTimeField(db_index=True,)

    criado_em = models.DateTimeField(auto_now_add=True,)

    class Meta:
        db_table = "leitura"
        ordering = ["-data_hora"]
        indexes = [
            models.Index(fields=["sensor", "data_hora"]),
        ]

    def __str__(self):
        return f"{self.sensor_id} - {self.valor} - {self.data_hora}"