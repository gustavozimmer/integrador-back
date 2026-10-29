-- Gerado com auxílio de IA (Claude). Compatível com MySQL 8 e tabelas criadas pelas migrações do Django.
-- Prefixo de tabela assumido: 'api_' (ajuste se o app label for outro).
-- Datas em UTC (USE_TZ=True).
SET NAMES utf8mb4;

-- Ordem de inserção respeitando FKs:
-- usuario, local, modeloequipamento, modelosensor -> microcontrolador -> sensor

-- Senha de todos os usuários: senha12345
INSERT INTO `api_usuario` (`id`, `password`, `last_login`, `is_superuser`, `username`, `first_name`, `last_name`, `email`, `is_staff`, `is_active`, `date_joined`, `tipo_usuario`, `foto_perfil`) VALUES
  (1, 'pbkdf2_sha256$600000$saltsensores01$FRLSqBDui+HDLZlMlRz0GwTlriNzE9DxsugHYMtbzw0=', NULL, 1, 'admin', 'Administrador', 'Sistema', 'admin@iot.local', 1, 1, '2026-10-01 12:00:00.000000', 'ADMIN', ''),
  (2, 'pbkdf2_sha256$600000$saltsensores01$FRLSqBDui+HDLZlMlRz0GwTlriNzE9DxsugHYMtbzw0=', NULL, 0, 'maria.souza', 'Maria', 'Souza', 'maria.souza@iot.local', 0, 1, '2026-10-01 12:00:00.000000', 'COMUM', ''),
  (3, 'pbkdf2_sha256$600000$saltsensores01$FRLSqBDui+HDLZlMlRz0GwTlriNzE9DxsugHYMtbzw0=', NULL, 0, 'carlos.lima', 'Carlos', 'Lima', 'carlos.lima@iot.local', 0, 1, '2026-10-01 12:00:00.000000', 'COMUM', ''),
  (4, 'pbkdf2_sha256$600000$saltsensores01$FRLSqBDui+HDLZlMlRz0GwTlriNzE9DxsugHYMtbzw0=', NULL, 0, 'ana.pereira', 'Ana', 'Pereira', 'ana.pereira@iot.local', 0, 1, '2026-10-01 12:00:00.000000', 'COMUM', ''),
  (5, 'pbkdf2_sha256$600000$saltsensores01$FRLSqBDui+HDLZlMlRz0GwTlriNzE9DxsugHYMtbzw0=', NULL, 0, 'pedro.alves', 'Pedro', 'Alves', 'pedro.alves@iot.local', 0, 0, '2026-10-01 12:00:00.000000', 'COMUM', '');

INSERT INTO `api_local` (`id`, `nome`, `descricao`, `is_active`) VALUES
  (1, 'Laboratório de Redes', 'Sala 101 - bloco A', 1),
  (2, 'Laboratório de Eletrônica', 'Sala 102 - bloco A', 1),
  (3, 'Sala de Aula 201', 'Primeiro andar - bloco B', 1),
  (4, 'Sala de Aula 202', 'Primeiro andar - bloco B', 1),
  (5, 'Biblioteca', 'Térreo - bloco C', 1),
  (6, 'Auditório', 'Térreo - bloco D', 1),
  (7, 'Data Center', 'Subsolo - bloco A', 1),
  (8, 'Almoxarifado', 'Térreo - bloco E (desativado)', 0);

INSERT INTO `api_modeloequipamento` (`id`, `nome`, `fabricante`, `descricao`) VALUES
  (1, 'ESP32 DevKit V1', 'Espressif', 'Microcontrolador dual-core com Wi-Fi e Bluetooth'),
  (2, 'ESP8266 NodeMCU', 'Espressif', 'Microcontrolador com Wi-Fi de baixo custo'),
  (3, 'Arduino Uno R3', 'Arduino', 'Placa baseada no ATmega328P'),
  (4, 'Raspberry Pi Pico W', 'Raspberry Pi', 'Microcontrolador RP2040 com Wi-Fi');

INSERT INTO `api_modelosensor` (`id`, `nome`, `fabricante`, `descricao`) VALUES
  (1, 'DHT22', 'Aosong', 'Temperatura e umidade'),
  (2, 'DS18B20', 'Maxim Integrated', 'Temperatura digital à prova d''água'),
  (3, 'LDR 5mm', 'Genérico', 'Resistor dependente de luz'),
  (4, 'BH1750', 'ROHM', 'Sensor digital de luminosidade'),
  (5, 'HC-SR501', 'Genérico', 'Sensor PIR de presença/passagem');

INSERT INTO `api_microcontrolador` (`id`, `modelo_id`, `local_id`, `mac_address`, `latitude`, `longitude`, `observacoes`, `data_cadastro`, `is_active`) VALUES
  (1, 1, 1, 'A4:CF:12:00:10:01', -22.90544, -47.06074, 'Nó de monitoramento 01', '2026-10-02 09:01:00.000000', 1),
  (2, 1, 1, 'A4:CF:12:00:10:02', -22.90532, -47.06065, 'Nó de monitoramento 02', '2026-10-02 09:02:00.000000', 1),
  (3, 2, 2, 'A4:CF:12:00:10:03', -22.9052, -47.06056, 'Nó de monitoramento 03', '2026-10-02 09:03:00.000000', 1),
  (4, 1, 3, 'A4:CF:12:00:10:04', -22.90508, -47.06047, 'Nó de monitoramento 04', '2026-10-02 09:04:00.000000', 1),
  (5, 4, 4, 'A4:CF:12:00:10:05', -22.90496, -47.06038, 'Nó de monitoramento 05', '2026-10-02 09:05:00.000000', 1),
  (6, 1, 5, 'A4:CF:12:00:10:06', -22.90484, -47.06029, 'Nó de monitoramento 06', '2026-10-02 09:06:00.000000', 1),
  (7, 3, 6, 'A4:CF:12:00:10:07', -22.90472, -47.0602, 'Nó de monitoramento 07', '2026-10-02 09:07:00.000000', 1),
  (8, 2, 7, 'A4:CF:12:00:10:08', -22.9046, -47.06011, 'Nó de monitoramento 08', '2026-10-02 09:08:00.000000', 1),
  (9, 1, 7, 'A4:CF:12:00:10:09', -22.90448, -47.06002, 'Nó de monitoramento 09', '2026-10-02 09:09:00.000000', 1),
  (10, 4, 2, 'A4:CF:12:00:10:0A', -22.90436, -47.05993, 'Nó de monitoramento 10', '2026-10-02 09:10:00.000000', 1),
  (11, 1, 3, 'A4:CF:12:00:10:0B', -22.90424, -47.05984, 'Nó de monitoramento 11', '2026-10-02 09:11:00.000000', 0),
  (12, 2, 8, 'A4:CF:12:00:10:0C', -22.90412, -47.05975, 'Nó de monitoramento 12', '2026-10-02 09:12:00.000000', 0);

INSERT INTO `api_sensor` (`id`, `modelo_id`, `microcontrolador_id`, `tipo`, `unidade_medida`, `is_active`, `data_cadastro`) VALUES
  (1, 1, 1, 'TEMP', 'C', 1, '2026-10-02 10:01:00.000000'),
  (2, 1, 1, 'UMID', '%', 1, '2026-10-02 10:02:00.000000'),
  (3, 1, 2, 'TEMP', 'C', 1, '2026-10-02 10:03:00.000000'),
  (4, 1, 2, 'UMID', '%', 1, '2026-10-02 10:04:00.000000'),
  (5, 3, 2, 'LUMI', 'LUX', 1, '2026-10-02 10:05:00.000000'),
  (6, 2, 3, 'TEMP', 'C', 1, '2026-10-02 10:06:00.000000'),
  (7, 1, 3, 'UMID', '%', 1, '2026-10-02 10:07:00.000000'),
  (8, 5, 3, 'PASS', 'UN', 1, '2026-10-02 10:08:00.000000'),
  (9, 1, 4, 'TEMP', 'C', 0, '2026-10-02 10:09:00.000000'),
  (10, 1, 4, 'UMID', '%', 1, '2026-10-02 10:10:00.000000'),
  (11, 3, 4, 'LUMI', 'LUX', 1, '2026-10-02 10:11:00.000000'),
  (12, 2, 5, 'TEMP', 'C', 1, '2026-10-02 10:12:00.000000'),
  (13, 1, 5, 'UMID', '%', 1, '2026-10-02 10:13:00.000000'),
  (14, 2, 6, 'TEMP', 'C', 1, '2026-10-02 10:14:00.000000'),
  (15, 1, 6, 'UMID', '%', 1, '2026-10-02 10:15:00.000000'),
  (16, 4, 6, 'LUMI', 'LUX', 1, '2026-10-02 10:16:00.000000'),
  (17, 5, 6, 'PASS', 'UN', 0, '2026-10-02 10:17:00.000000'),
  (18, 2, 7, 'TEMP', 'C', 1, '2026-10-02 10:18:00.000000'),
  (19, 1, 7, 'UMID', '%', 1, '2026-10-02 10:19:00.000000'),
  (20, 2, 8, 'TEMP', 'C', 1, '2026-10-02 10:20:00.000000'),
  (21, 1, 8, 'UMID', '%', 1, '2026-10-02 10:21:00.000000'),
  (22, 4, 8, 'LUMI', 'LUX', 1, '2026-10-02 10:22:00.000000'),
  (23, 1, 9, 'TEMP', 'C', 1, '2026-10-02 10:23:00.000000'),
  (24, 1, 9, 'UMID', '%', 1, '2026-10-02 10:24:00.000000'),
  (25, 5, 9, 'PASS', 'UN', 1, '2026-10-02 10:25:00.000000'),
  (26, 2, 10, 'TEMP', 'C', 1, '2026-10-02 10:26:00.000000'),
  (27, 1, 10, 'UMID', '%', 1, '2026-10-02 10:27:00.000000'),
  (28, 4, 10, 'LUMI', 'LUX', 1, '2026-10-02 10:28:00.000000'),
  (29, 1, 11, 'TEMP', 'C', 1, '2026-10-02 10:29:00.000000'),
  (30, 1, 11, 'UMID', '%', 1, '2026-10-02 10:30:00.000000'),
  (31, 1, 12, 'TEMP', 'C', 1, '2026-10-02 10:31:00.000000');
