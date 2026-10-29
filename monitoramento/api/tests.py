from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Leitura, Local, Manutencao, Microcontrolador, ModeloEquipamento, ModeloSensor, Sensor,
)


class ManutencaoAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.admin = Usuario.objects.create_superuser("admin", "a@a.com", "senha12345")
        cls.comum = Usuario.objects.create_user("comum", "c@c.com", "senha12345")

        local = Local.objects.create(nome="Lab 1")
        modelo_eq = ModeloEquipamento.objects.create(nome="ESP32")
        modelo_sensor = ModeloSensor.objects.create(nome="DHT22")
        micro = Microcontrolador.objects.create(
            modelo=modelo_eq, local=local, mac_address="AA:BB:CC:DD:EE:01",
            latitude="-23.5", longitude="-46.6",
        )
        cls.sensor = Sensor.objects.create(
            modelo=modelo_sensor, microcontrolador=micro, tipo="TEMP", unidade_medida="C",
        )

    def payload(self, **extra):
        dados = {
            "sensor": self.sensor.pk,
            "data_manutencao": (timezone.now() - timedelta(days=1)).isoformat(),
            "descricao": "Troca do sensor",
            "responsavel": "João Pereira",
        }
        dados.update(extra)
        return dados

    def test_exige_autenticacao(self):
        resposta = self.client.get("/api/manutencoes/")
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_registra_manutencao(self):
        self.client.force_authenticate(self.admin)
        resposta = self.client.post("/api/manutencoes/", self.payload(), format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)
        self.assertEqual(resposta.data["responsavel"], "João Pereira")
        self.assertEqual(Manutencao.objects.count(), 1)

    def test_data_futura_e_rejeitada(self):
        self.client.force_authenticate(self.admin)
        futura = (timezone.now() + timedelta(days=2)).isoformat()
        resposta = self.client.post(
            "/api/manutencoes/", self.payload(data_manutencao=futura), format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("data_manutencao", resposta.data)

    def test_descricao_e_responsavel_obrigatorios(self):
        self.client.force_authenticate(self.admin)
        resposta = self.client.post(
            "/api/manutencoes/", self.payload(descricao="   ", responsavel=""), format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("descricao", resposta.data)
        self.assertIn("responsavel", resposta.data)

    def test_usuario_comum_nao_cria_mas_consulta(self):
        self.client.force_authenticate(self.comum)
        self.assertEqual(
            self.client.post("/api/manutencoes/", self.payload(), format="json").status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(self.client.get("/api/manutencoes/").status_code, status.HTTP_200_OK)

    def test_filtros_de_consulta(self):
        agora = timezone.now()
        Manutencao.objects.create(
            sensor=self.sensor, data_manutencao=agora - timedelta(days=10),
            descricao="A", responsavel="Ana",
        )
        Manutencao.objects.create(
            sensor=self.sensor, data_manutencao=agora - timedelta(days=1),
            descricao="B", responsavel="Bruno",
        )
        self.client.force_authenticate(self.admin)

        todas = self.client.get(f"/api/manutencoes/?sensor={self.sensor.pk}")
        self.assertEqual([m["responsavel"] for m in todas.data], ["Bruno", "Ana"])

        por_nome = self.client.get("/api/manutencoes/?responsavel=ana")
        self.assertEqual(len(por_nome.data), 1)

        inicio = (agora - timedelta(days=3)).date().isoformat()
        recentes = self.client.get(f"/api/manutencoes/?data_inicio={inicio}")
        self.assertEqual(len(recentes.data), 1)

        invalido = self.client.get("/api/manutencoes/?sensor=abc")
        self.assertEqual(invalido.status_code, status.HTTP_400_BAD_REQUEST)


class OrdenacaoAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        Usuario = get_user_model()
        cls.usuario = Usuario.objects.create_user("leitor", "l@l.com", "senha12345")

        cls.local_b = Local.objects.create(nome="Biblioteca")
        cls.local_a = Local.objects.create(nome="Auditório")
        modelo_eq = ModeloEquipamento.objects.create(nome="ESP32")
        modelo_sensor = ModeloSensor.objects.create(nome="DHT22")

        def criar_micro(local, mac):
            return Microcontrolador.objects.create(
                modelo=modelo_eq, local=local, mac_address=mac,
                latitude="-23.5", longitude="-46.6",
            )

        micro_b = criar_micro(cls.local_b, "AA:BB:CC:DD:EE:01")
        micro_a = criar_micro(cls.local_a, "AA:BB:CC:DD:EE:02")
        cls.sensor_b = Sensor.objects.create(
            modelo=modelo_sensor, microcontrolador=micro_b, tipo="TEMP", unidade_medida="C",
        )
        cls.sensor_a = Sensor.objects.create(
            modelo=modelo_sensor, microcontrolador=micro_a, tipo="UMID", unidade_medida="%",
        )

        agora = timezone.now()
        # (sensor, valor, dias atrás)
        for sensor, valor, dias in [
            (cls.sensor_b, "20.0000", 3),
            (cls.sensor_b, "35.5000", 1),
            (cls.sensor_a, "10.2500", 2),
        ]:
            Leitura.objects.create(
                sensor=sensor, valor=valor, data_hora=agora - timedelta(days=dias)
            )

        for responsavel, dias, sensor in [
            ("Carla", 5, cls.sensor_b),
            ("Ana", 1, cls.sensor_a),
            ("Bruno", 3, cls.sensor_b),
        ]:
            Manutencao.objects.create(
                sensor=sensor, data_manutencao=agora - timedelta(days=dias),
                descricao="Revisão", responsavel=responsavel,
            )

    def setUp(self):
        self.client.force_authenticate(self.usuario)

    def valores(self, url, campo):
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK, resposta.data)
        return [str(item[campo]) for item in resposta.data]

    def test_leituras_ordem_padrao_continua_a_mais_recente_primeiro(self):
        self.assertEqual(
            self.valores("/api/leituras/", "valor"), ["35.5000", "10.2500", "20.0000"]
        )

    def test_leituras_por_valor_crescente_e_decrescente(self):
        self.assertEqual(
            self.valores("/api/leituras/?ordering=valor", "valor"),
            ["10.2500", "20.0000", "35.5000"],
        )
        self.assertEqual(
            self.valores("/api/leituras/?ordering=-valor", "valor"),
            ["35.5000", "20.0000", "10.2500"],
        )

    def test_leituras_por_data_da_leitura(self):
        self.assertEqual(
            self.valores("/api/leituras/?ordering=data_hora", "valor"),
            ["20.0000", "10.2500", "35.5000"],
        )

    def test_leituras_combina_campos_e_respeita_filtros(self):
        resposta = self.valores(
            f"/api/leituras/?ordering=sensor,-valor&sensor={self.sensor_b.pk}", "valor"
        )
        self.assertEqual(resposta, ["35.5000", "20.0000"])

        todas = self.client.get("/api/leituras/?ordering=sensor,-valor")
        self.assertEqual(
            [item["sensor"] for item in todas.data],
            [self.sensor_b.pk, self.sensor_b.pk, self.sensor_a.pk],
        )

    def test_campo_invalido_retorna_400(self):
        resposta = self.client.get("/api/leituras/?ordering=senha")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ordering", resposta.data)

    def test_ordering_vazio_usa_ordem_padrao(self):
        self.assertEqual(
            self.valores("/api/leituras/?ordering=", "valor"),
            ["35.5000", "10.2500", "20.0000"],
        )

    def test_detalhe_ignora_ordering(self):
        leitura = Leitura.objects.first()
        resposta = self.client.get(f"/api/leituras/{leitura.pk}/?ordering=campo_invalido")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)

    def test_locais_por_nome_decrescente(self):
        self.assertEqual(
            self.valores("/api/locais/?ordering=-nome", "nome"), ["Biblioteca", "Auditório"]
        )

    def test_manutencoes_por_responsavel_e_por_local(self):
        self.assertEqual(
            self.valores("/api/manutencoes/?ordering=responsavel", "responsavel"),
            ["Ana", "Bruno", "Carla"],
        )
        # Auditório (Ana) vem antes de Biblioteca (Carla, Bruno)
        por_local = self.valores("/api/manutencoes/?ordering=local_nome", "responsavel")
        self.assertEqual(por_local[0], "Ana")

    def test_sensores_por_modelo_e_tipo(self):
        resposta = self.client.get("/api/sensores/?ordering=-tipo")
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual([s["tipo"] for s in resposta.data], ["UMID", "TEMP"])
