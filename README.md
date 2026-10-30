# API de Monitoramento de Sensores

API REST em **Django + Django REST Framework** para cadastro e consulta de locais, microcontroladores, sensores, leituras e manutenções de sensores IoT, com autenticação JWT, perfis de acesso, auditoria das operações e documentação Swagger.

## Sumário

1. [Requisitos](#1-requisitos)
2. [Instalação](#2-instalação)
3. [Configuração](#3-configuração)
4. [População do banco](#4-população-do-banco)
5. [Execução da API](#5-execução-da-api)
6. [Autenticação e perfis](#6-autenticação-e-perfis)
7. [Funcionalidades extras](#7-funcionalidades-extras)
8. [Resumo dos endpoints](#8-resumo-dos-endpoints)
9. [Estrutura do projeto](#9-estrutura-do-projeto)

---

## 1. Requisitos

- **Python 3.10 ou superior** (exigência do Django 5.2)
- **MySQL 8** (ou MariaDB compatível) em execução
- `pip` e `venv`
- Para instalar o `mysqlclient` no Windows, use uma versão do Python para a qual exista pacote pronto (wheel); no Linux/macOS podem ser necessários os cabeçalhos de desenvolvimento do MySQL (`libmysqlclient-dev` / `mysql-client`).

## 2. Instalação

Na pasta do projeto (a que contém o `manage.py`):

**Windows (PowerShell)**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuração

### 3.1 Criar o banco de dados

No MySQL:

```sql
CREATE DATABASE monitoramento CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3.2 Variáveis de ambiente (`.env`)

O projeto lê as variáveis de conexão com o banco de um arquivo `.env` que deve ficar **na pasta do `manage.py`** (a raiz do projeto, não dentro da pasta `monitoramento/monitoramento/`). Crie-o com o conteúdo abaixo, ajustando usuário e senha:

```env
DB_NAME=monitoramento
DB_USER=root
DB_PASSWORD=sua_senha
DB_HOST=127.0.0.1
DB_PORT=3306
```

Se o arquivo não existir, valem estes padrões: banco `monitoramento`, usuário `root`, senha `root`, host `127.0.0.1`, porta `3306`.

### 3.3 Criar as tabelas

```powershell
py .\manage.py migrate
```

## 4. População do banco

### 4.1 Dados de exemplo (cadastros e leituras)

Os CSVs ficam em `data/`. O comando abaixo importa usuários, locais, modelos, microcontroladores, sensores e leituras, **respeitando a ordem das chaves estrangeiras**:

```powershell
py .\manage.py importar_csv --pasta data
```

- Os dados passam pelos **mesmos serializers da API**, então todas as regras de validação (MAC válido e único, nomes únicos, tipo × unidade, sensor ativo para leituras) são aplicadas na importação.
- O comando é **idempotente**: registros que já existem são ignorados, então pode ser executado mais de uma vez.
- Se qualquer linha tiver erro, **toda a carga é desfeita** e os erros são exibidos por arquivo e linha.
- Os usuários do `usuarios.csv` são criados com a senha `senha12345`.

> Alternativa: os arquivos `data/01_cadastros.sql` e `data/02_leituras.sql` trazem a mesma carga em SQL, para importar direto no MySQL (executar nessa ordem).

### 4.2 Usuários da avaliação

Para o ambiente de desenvolvimento/avaliação, um comando cria um usuário de cada perfil:

```powershell
py .\manage.py criar_usuarios_avaliacao
```

| Perfil | Username | Senha | O que pode fazer |
|---|---|---|---|
| Superusuário (Django) | `lin` | `123` | Tudo, inclusive o `/admin/` |
| Administrador (`ADMIN`) | `senai.admin` | `123456` | Consultar, criar, alterar e excluir na API |
| Usuário comum (`USER`) | `senai` | `123456` | Somente consultar (GET) |

> As senhas são definidas diretamente, sem passar pelos validadores de senha do Django (que recusariam `123`). **Use apenas em desenvolvimento.** O comando também é idempotente.

## 5. Execução da API

```powershell
py .\manage.py runserver
```

A API sobe em `http://127.0.0.1:8000/`:

| Recurso | URL |
|---|---|
| Swagger UI (documentação interativa) | http://127.0.0.1:8000/api/docs/ |
| ReDoc | http://127.0.0.1:8000/api/redoc/ |
| Esquema OpenAPI | http://127.0.0.1:8000/api/schema/ |
| Painel administrativo do Django | http://127.0.0.1:8000/admin/ |
| Raiz da API | http://127.0.0.1:8000/api/ |

## 6. Autenticação e perfis

A API usa **JWT**. Todos os endpoints (exceto login, refresh e verify) exigem token.

1. Obtenha o token em `POST /api/auth/login/` com `username` e `password`.
2. Envie o `access` no cabeçalho `Authorization: Bearer <access>`.
3. O `access` dura 25 minutos; renove com `POST /api/auth/refresh/` usando o `refresh` (válido por 12 horas).

**Pelo Swagger:** faça o login em *Autenticação → Login*, copie o valor de `access`, clique em **Authorize** e cole o token (o prefixo `Bearer` é adicionado automaticamente).

**Pelo PowerShell:**

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/auth/login/ `
  -ContentType "application/json" -Body '{"username":"lin","password":"123"}'
$h = @{ Authorization = "Bearer $($login.access)" }

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/sensores/" -Headers $h
```

**Pelo curl:**

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"lin","password":"123"}' | python -c "import sys,json; print(json.load(sys.stdin)['access'])")

curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/sensores/
```

**Permissões:** superusuário e usuários `ADMIN` têm acesso total; usuários `USER` só consultam (GET). Sem token a resposta é `401`; sem permissão, `403`.

---

## 7. Funcionalidades extras

Foram implementadas **seis** funcionalidades extras:

| # | Funcionalidade | Onde está |
|---|---|---|
| 1 | [Ordenação nas consultas](#71-ordenação-nas-consultas) | `api/ordenacao.py`, `api/views.py` |
| 2 | [Resumo estatístico por sensor](#72-resumo-estatístico-por-sensor) | `SensorResumoEstatisticoView` em `api/views.py` |
| 3 | [Testes automatizados](#73-testes-automatizados) | `api/tests.py` |
| 4 | [Documentação automática com Swagger](#74-documentação-automática-com-swagger) | `drf-spectacular`, `api/docs.py` |
| 5 | [Registro de manutenção](#75-registro-de-manutenção) | `Manutencao` em `api/models.py`, `/api/manutencoes/` |
| 6 | [Auditoria de operações](#76-auditoria-de-operações) | `AuditLog`, `api/services.py`, `/api/auditoria/` |

Para as demonstrações abaixo, execute antes as etapas 4 (população) e 5 (execução) e faça login (seção 6). Os exemplos usam a URL base `http://127.0.0.1:8000`.

### 7.1 Ordenação nas consultas

**Descrição:** todas as listagens aceitam o parâmetro `ordering` para ordenar o resultado por campos pertinentes: nome, data da leitura, valor medido, responsável, MAC etc. O prefixo `-` inverte a ordem e a vírgula combina campos. Campo inexistente retorna `400` com a lista de campos aceitos. Sem o parâmetro, vale a ordem padrão de cada listagem (por exemplo, leituras da mais recente para a mais antiga). Os filtros existentes continuam funcionando junto com a ordenação.

**Campos aceitos:**

| Endpoint | Campos |
|---|---|
| `/api/leituras/` | `data_hora`, `valor`, `sensor`, `criado_em`, `id` |
| `/api/manutencoes/` | `data_manutencao`, `responsavel`, `sensor`, `local_nome`, `criado_em`, `id` |
| `/api/sensores/` | `tipo`, `unidade_medida`, `modelo_nome`, `microcontrolador_mac`, `data_cadastro`, `is_active`, `id` |
| `/api/microcontroladores/` | `mac_address`, `modelo_nome`, `local_nome`, `data_cadastro`, `is_active`, `id` |
| `/api/locais/` | `nome`, `is_active`, `id` |
| `/api/modelos-equipamentos/`, `/api/modelos-sensores/` | `nome`, `fabricante`, `id` |
| `/api/usuarios/` | `username`, `first_name`, `last_name`, `email`, `tipo_usuario`, `id` |
| `/api/auditoria/` | `timestamp`, `action`, `model_name`, `user_id`, `id` |

**Como demonstrar** (no Swagger, o parâmetro `ordering` aparece em cada listagem):

```text
GET /api/leituras/?ordering=-valor                 maior valor medido primeiro
GET /api/leituras/?ordering=valor                  menor valor medido primeiro
GET /api/leituras/?ordering=data_hora              leituras mais antigas primeiro
GET /api/leituras/?ordering=sensor,-data_hora      por sensor e, dentro dele, da mais recente
GET /api/locais/?ordering=-nome                    nomes em ordem alfabética inversa
GET /api/manutencoes/?ordering=responsavel         por responsável
GET /api/leituras/?ordering=senha                  400: campo inválido
```

### 7.2 Resumo estatístico por sensor

**Descrição:** endpoint que retorna, para um sensor, a **quantidade de leituras e os valores mínimo, máximo e médio** (arredondados em 2 casas) em um período. As datas são opcionais; sem elas, considera todas as leituras. Aceita data (`AAAA-MM-DD`) ou data e hora ISO 8601. Sem leituras no período, a quantidade é `0` e os valores são `null`. A data final não pode ser anterior à inicial (`400`).

**Como demonstrar:**

```text
GET /api/sensores/1/resumo/
GET /api/sensores/1/resumo/?data_inicio=2026-10-23&data_fim=2026-10-25
GET /api/sensores/1/resumo/?data_inicio=2026-10-23T08:00:00Z
GET /api/sensores/1/resumo/?data_inicio=2026-10-30&data_fim=2026-10-01     400: período inválido
GET /api/sensores/9999/resumo/                                              404: sensor inexistente
```

Resposta (exemplo):

```json
{
  "sensor": 1,
  "tipo": "TEMP",
  "tipo_display": "Temperatura",
  "unidade_medida": "C",
  "unidade_medida_display": "Graus Celsius",
  "modelo_nome": "DHT22",
  "microcontrolador_mac": "A4:CF:12:9B:3E:01",
  "data_inicio": "2026-10-23T00:00:00Z",
  "data_fim": "2026-10-25T23:59:59.999999Z",
  "quantidade_leituras": 48,
  "valor_minimo": 18.2,
  "valor_maximo": 31.7,
  "valor_medio": 24.85
}
```

### 7.3 Testes automatizados

**Descrição:** testes com `APITestCase` do Django REST Framework que verificam regras de negócio, autenticação e permissões:

- **Autenticação:** requisição sem token retorna `401`.
- **Permissões:** usuário comum consulta (GET) mas recebe `403` ao criar; usuário administrador (não superusuário) consegue criar; superusuário tem acesso total.
- **Regras de negócio:** manutenção com data futura é rejeitada; descrição e responsável são obrigatórios (texto em branco é recusado); filtros de consulta (sensor, responsável, período) e validação de identificador inválido.
- **Ordenação:** ordem padrão preservada, crescente/decrescente por valor, por data, combinação de campos junto com filtros, campo inválido (`400`), parâmetro vazio e detalhe de registro ignorando o parâmetro.

**Como demonstrar:**

```powershell
py .\manage.py test api -v 2
```

> O Django cria um banco temporário `test_monitoramento` e o remove ao final; o usuário do MySQL precisa ter permissão para criar bancos (o `root` tem).

### 7.4 Documentação automática com Swagger

**Descrição:** todos os endpoints são documentados automaticamente com **drf-spectacular** (OpenAPI 3): agrupados por tag, com descrição de cada operação, parâmetros de consulta (filtros e `ordering`), corpo enviado e recebido com exemplos, e as respostas de erro (`400`, `401`, `403`, `404`). A interface permite autenticar e testar as chamadas.

**Como demonstrar:**

1. Abra http://127.0.0.1:8000/api/docs/.
2. Execute *Autenticação → Login* com `lin` / `123` e copie o `access`.
3. Clique em **Authorize**, cole o token e confirme.
4. Expanda *Leituras → Listar leituras*, veja os parâmetros (`sensor`, `local`, `data_inicio`, `data_fim`, `ordering`) e clique em **Try it out → Execute**.
5. Alternativas: http://127.0.0.1:8000/api/redoc/ (leitura) e http://127.0.0.1:8000/api/schema/ (arquivo OpenAPI).

### 7.5 Registro de manutenção

**Descrição:** permite registrar e consultar as intervenções feitas nos sensores, com **sensor, data, descrição e responsável**. A data não pode estar no futuro, e descrição e responsável são obrigatórios. A listagem vem da mais recente para a mais antiga e aceita filtros combináveis por sensor, local, responsável (contém o texto) e período, além de ordenação. O cadastro, a alteração e a exclusão passam pela auditoria. O modelo também está disponível no `/admin/`.

**Como demonstrar** (com um usuário `ADMIN` ou superusuário):

```text
POST /api/manutencoes/
{
  "sensor": 1,
  "data_manutencao": "2026-10-29T09:00:00Z",
  "descricao": "Substituição do sensor por desgaste e recalibração.",
  "responsavel": "João Pereira"
}
```

```text
GET /api/manutencoes/                                  todas, da mais recente para a mais antiga
GET /api/manutencoes/?sensor=1                         histórico de um sensor
GET /api/manutencoes/?responsavel=joão                 por responsável
GET /api/manutencoes/?data_inicio=2026-10-01&data_fim=2026-10-31
GET /api/manutencoes/?ordering=responsavel             ordenado por responsável
```

Para demonstrar as regras: repita o `POST` com uma `data_manutencao` futura (retorna `400`) e com `descricao` em branco (retorna `400`). Entrando como `senai` (usuário comum), o `POST` retorna `403` e o `GET` funciona.

### 7.6 Auditoria de operações

**Descrição:** toda criação, alteração, ativação, desativação e exclusão feita pela API é registrada com o **usuário, a ação, o registro afetado (modelo, id e descrição), os campos alterados, o IP, o método, o caminho e a data e hora**. Exclusões de registros que possuem `is_active` (usuários, locais, microcontroladores e sensores) fazem **desativação lógica** e registram a ação `DEACTIVATE`. A consulta é somente leitura, paginada (10 por página, até 100) e filtrável.

**Filtros:** `user_id`, `action` (`CREATE`, `UPDATE`, `DELETE`, `ACTIVATE`, `DEACTIVATE`), `model_name` (ex.: `api.Sensor`), `object_id`, `date_from`, `date_to`, além de `ordering` e `page_size`.

**Como demonstrar:**

1. Como `lin`, crie um local: `POST /api/locais/` com `{"nome": "Sala de Testes"}`.
2. Altere-o: `PATCH /api/locais/<id>/` com `{"descricao": "Teste de auditoria"}`.
3. Desative-o: `DELETE /api/locais/<id>/`.
4. Consulte o histórico:

```text
GET /api/auditoria/                                          mais recentes primeiro
GET /api/auditoria/?model_name=api.Local&object_id=<id>      histórico desse local
GET /api/auditoria/?action=DEACTIVATE
GET /api/auditoria/?user_id=<id do lin>&page_size=50
```

---

## 8. Resumo dos endpoints

| Método | Rota | Descrição |
|---|---|---|
| POST | `/api/auth/login/` | Obtém os tokens JWT |
| POST | `/api/auth/refresh/` | Renova o token de acesso |
| POST | `/api/auth/verify/` | Verifica um token |
| CRUD | `/api/usuarios/` | Usuários (envio `multipart/form-data`) |
| CRUD | `/api/locais/` | Locais |
| CRUD | `/api/modelos-equipamentos/` | Modelos de equipamento |
| CRUD | `/api/microcontroladores/` | Microcontroladores (filtro `is_active`) |
| CRUD | `/api/modelos-sensores/` | Modelos de sensor |
| CRUD | `/api/sensores/` | Sensores (filtro `is_active`) |
| GET | `/api/sensores/<id>/resumo/` | Resumo estatístico do sensor |
| CRUD | `/api/leituras/` | Leituras (filtros `sensor`, `local`, `data_inicio`, `data_fim`; não paginada) |
| CRUD | `/api/manutencoes/` | Manutenções dos sensores |
| GET | `/api/auditoria/` | Histórico de auditoria (paginado) |

"CRUD" = listar, detalhar, criar, substituir (PUT), atualizar parcialmente (PATCH) e excluir. Todas as listagens aceitam `ordering`.

## 9. Estrutura do projeto

```text
monitoramento/
├── manage.py
├── requirements.txt
├── .env                        # variáveis de conexão com o banco (você cria)
├── monitoramento/              # configuração do projeto (settings, urls)
├── api/
│   ├── models.py               # Usuario, Local, Microcontrolador, Sensor, Leitura, Manutencao, AuditLog...
│   ├── serializers.py          # validações das regras de negócio
│   ├── views.py                # viewsets, filtros e resumo estatístico
│   ├── ordenacao.py            # ordenação reutilizável (parâmetro ordering)
│   ├── permissions.py          # perfis de acesso
│   ├── services.py             # auditoria (AuditMixin)
│   ├── docs.py                 # documentação OpenAPI
│   ├── tests.py                # testes automatizados
│   └── management/commands/
│       ├── importar_csv.py             # população do banco a partir dos CSVs
│       └── criar_usuarios_avaliacao.py # usuários lin, senai.admin e senai
├── data/                       # CSVs e scripts SQL de carga inicial
└── media/                      # fotos de perfil enviadas
```
