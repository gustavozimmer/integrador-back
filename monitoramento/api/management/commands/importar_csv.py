"""
Comando de importação de CSVs para a API de sensores IoT.

Instalação: copie este arquivo para
    <seu_app>/management/commands/importar_csv.py
(crie também os arquivos vazios __init__.py em management/ e em management/commands/).

Uso:
    python manage.py importar_csv                      # lê <seu_app>/dados_csv/
    python manage.py importar_csv --pasta C:/caminho/dados_csv

Os dados passam pelos MESMOS serializers da API, então todas as regras
(MAC válido e único, nomes únicos, tipo x unidade, sensor/microcontrolador
ativo para leituras) são validadas na importação. O script é idempotente:
registros que já existem são ignorados.
"""
import csv
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from api.models import (
    Leitura,
    Local,
    Microcontrolador,
    ModeloEquipamento,
    ModeloSensor,
    Sensor,
)
from api.serializers import (
    LeituraSerializer,
    LocalSerializer,
    MicrocontroladorSerializer,
    ModeloEquipamentoSerializer,
    ModeloSensorSerializer,
    SensorSerializer,
    UsuarioSerializer,
)

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Importa os CSVs de carga inicial respeitando a ordem das chaves estrangeiras."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pasta",
            default=None,
            help="Pasta com os CSVs (padrão: <app>/dados_csv).",
        )

    def handle(self, *args, **opcoes):
        app_dir = Path(__file__).resolve().parents[2]
        self.pasta = Path(opcoes["pasta"]) if opcoes["pasta"] else app_dir / "dados_csv"
        if not self.pasta.is_dir():
            raise CommandError(f"Pasta não encontrada: {self.pasta}")

        self.resumo = []
        with transaction.atomic():
            self.importar_usuarios()
            self.importar_locais()
            self.importar_modelos_equipamento()
            self.importar_modelos_sensor()
            self.importar_microcontroladores()
            self.importar_sensores()
            self.importar_leituras()
            if any(erros for _, _, _, erros in self.resumo):
                # qualquer erro desfaz a carga inteira para não deixar dados pela metade
                transaction.set_rollback(True)

        self.stdout.write("")
        total_erros = 0
        for rotulo, criados, ignorados, erros in self.resumo:
            total_erros += erros
            self.stdout.write(
                f"{rotulo:<22} criados={criados:<4} ignorados={ignorados:<4} erros={erros}"
            )
        if total_erros:
            raise CommandError("Importação desfeita: corrija os erros acima e rode novamente.")
        self.stdout.write(self.style.SUCCESS("Importação concluída."))

    # ------------------------------------------------------------------ util
    def ler(self, nome):
        caminho = self.pasta / nome
        if not caminho.is_file():
            raise CommandError(f"Arquivo não encontrado: {caminho}")
        with open(caminho, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def processar(self, rotulo, arquivo, serializer_cls, preparar, ja_existe):
        criados = ignorados = erros = 0
        for numero, linha in enumerate(self.ler(arquivo), start=2):
            linha = {k: (v or "").strip() for k, v in linha.items()}
            try:
                dados = preparar(linha)
            except ObjectDoesNotExist as e:
                erros += 1
                self.stderr.write(f"[{arquivo}:{numero}] referência não encontrada: {e}")
                continue
            if ja_existe(dados):
                ignorados += 1
                continue
            serializer = serializer_cls(data=dados)
            if serializer.is_valid():
                serializer.save()
                criados += 1
            else:
                erros += 1
                self.stderr.write(f"[{arquivo}:{numero}] {dict(serializer.errors)}")
        self.resumo.append((rotulo, criados, ignorados, erros))

    # ------------------------------------------------------------ importações
    def importar_usuarios(self):
        self.processar(
            "usuarios", "usuarios.csv", UsuarioSerializer,
            preparar=lambda l: dict(l),
            ja_existe=lambda d: Usuario.objects.filter(username=d["username"]).exists(),
        )

    def importar_locais(self):
        self.processar(
            "locais", "locais.csv", LocalSerializer,
            preparar=lambda l: dict(l),
            ja_existe=lambda d: Local.objects.filter(nome__iexact=d["nome"]).exists(),
        )

    def importar_modelos_equipamento(self):
        self.processar(
            "modelos_equipamento", "modelos_equipamento.csv", ModeloEquipamentoSerializer,
            preparar=lambda l: dict(l),
            ja_existe=lambda d: ModeloEquipamento.objects.filter(nome__iexact=d["nome"]).exists(),
        )

    def importar_modelos_sensor(self):
        self.processar(
            "modelos_sensor", "modelos_sensor.csv", ModeloSensorSerializer,
            preparar=lambda l: dict(l),
            ja_existe=lambda d: ModeloSensor.objects.filter(nome__iexact=d["nome"]).exists(),
        )

    def importar_microcontroladores(self):
        def preparar(l):
            return {
                "modelo": ModeloEquipamento.objects.get(nome__iexact=l["modelo_nome"]).pk,
                "local": Local.objects.get(nome__iexact=l["local_nome"]).pk,
                "mac_address": l["mac_address"],
                "latitude": l["latitude"],
                "longitude": l["longitude"],
                "observacoes": l["observacoes"],
                "is_active": l["is_active"],
            }

        self.processar(
            "microcontroladores", "microcontroladores.csv", MicrocontroladorSerializer,
            preparar=preparar,
            ja_existe=lambda d: Microcontrolador.objects.filter(
                mac_address__iexact=d["mac_address"]
            ).exists(),
        )

    def importar_sensores(self):
        def preparar(l):
            return {
                "modelo": ModeloSensor.objects.get(nome__iexact=l["modelo_sensor_nome"]).pk,
                "microcontrolador": Microcontrolador.objects.get(
                    mac_address__iexact=l["microcontrolador_mac"]
                ).pk,
                "tipo": l["tipo"],
                "unidade_medida": l["unidade_medida"],
                "is_active": l["is_active"],
            }

        self.processar(
            "sensores", "sensores.csv", SensorSerializer,
            preparar=preparar,
            ja_existe=lambda d: Sensor.objects.filter(
                microcontrolador_id=d["microcontrolador"], tipo=d["tipo"]
            ).exists(),
        )

    def importar_leituras(self):
        def preparar(l):
            # leituras.csv tem sensor_id, valor, data_hora
            sensor_id = l["sensor_id"]
            # Verifica se o sensor existe
            Sensor.objects.get(pk=sensor_id)
            return {"sensor": sensor_id, "valor": l["valor"], "data_hora": l["data_hora"]}

        # a checagem de duplicidade compara sensor + data_hora (valor não entra na chave)
        def ja_existe(d):
            from django.utils.dateparse import parse_datetime

            return Leitura.objects.filter(
                sensor_id=d["sensor"], data_hora=parse_datetime(d["data_hora"])
            ).exists()

        self.processar(
            "leituras", "leituras.csv", LeituraSerializer,
            preparar=preparar, ja_existe=ja_existe,
        )
