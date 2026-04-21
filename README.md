# 💸 Expense Tracker API

![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)
![Django Ninja](https://img.shields.io/badge/Django%20Ninja-1.3-000000?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SQLite%20%2F%20PostgreSQL](https://img.shields.io/badge/DB-SQLite%20%7C%20PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)

Backend da aplicacao mobile **Expense Tracker**, construido com Django e Django Ninja. A API expoe operacoes para listar, criar, atualizar e remover transacoes financeiras, servindo como camada de sincronizacao para o app React Native.

O projeto foi pensado para funcionar bem com uma arquitetura **local-first** no mobile: o app continua utilizavel offline e sincroniza com esta API quando houver conectividade.

> Frontend mobile: [expense-tracker](https://github.com/luan-sampaio/expense-tracker)

## ✨ Funcionalidades

- API REST para transacoes financeiras
- Endpoints documentados com Swagger via Django Ninja
- Validacao de payload com schemas tipados
- Suporte a receitas e despesas
- Persistencia com SQLite em desenvolvimento e PostgreSQL em producao
- Configuracao simples via variaveis de ambiente

## 📂 Estrutura do Projeto

```text
back-expense-tracker/
├── core/
│   ├── settings.py       # Configuracoes do Django
│   ├── urls.py           # Registro da API e das rotas base
│   ├── asgi.py
│   └── wsgi.py
├── transactions/
│   ├── api.py            # Endpoints REST de transacoes
│   ├── models.py         # Model Transaction
│   ├── schemas.py        # Schemas de entrada e saida
│   └── migrations/
├── manage.py
├── requirements.txt
└── README.md
```

## 🛠️ Tecnologias Utilizadas

- Python 3.10+
- Django 5.1
- Django Ninja 1.3
- django-cors-headers
- python-decouple
- dj-database-url
- SQLite e PostgreSQL

## 💻 Pre-requisitos

- Python 3.10 ou superior
- `pip`
- Git
- Opcionalmente, PostgreSQL para ambiente de producao

## 🚀 Como executar o projeto

### 1. Clone o repositorio

```bash
git clone https://github.com/luan-sampaio/expense-tracker-api.git
cd expense-tracker-api
```

### 2. Crie e ative um ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

No Windows:

```bash
.venv\Scripts\activate
```

### 3. Instale as dependencias

```bash
pip install -r requirements.txt
```

### 4. Configure as variaveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=sua-chave-segura

# Em desenvolvimento com Expo/dispositivo fisico, "*" permite acesso pelo IP local
ALLOWED_HOSTS=*

# Em desenvolvimento, pode omitir DATABASE_URL para usar SQLite
# DATABASE_URL=postgresql://usuario:senha@localhost:5432/expense_tracker

# Em desenvolvimento, pode manter CORS aberto para Expo Web e IP local
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOWED_ORIGINS=http://localhost:8081,http://127.0.0.1:8081
CORS_ALLOWED_ORIGIN_REGEXES=^http://192\\.168\\.\\d{1,3}\\.\\d{1,3}:8081$,^http://10\\.0\\.2\\.2:8081$
```

### 5. Rode as migracoes

```bash
python3 manage.py migrate
```

### 6. Inicie o servidor

```bash
python3 manage.py runserver
```

API disponivel em:

```text
http://localhost:8000/api/
```

Documentacao interativa:

```text
http://localhost:8000/api/docs
```

## 🔗 Integracao com o App Mobile

O app React Native usa esta API como backend de sincronizacao. A estrategia esperada e:

- o mobile persiste os dados localmente primeiro;
- ao abrir o app, busca as transacoes com `GET /api/transactions/`;
- ao criar uma transacao, envia os dados para `POST /api/transactions/`;
- ao editar uma transacao existente, usa `PUT /api/transactions/{id}`;
- ao excluir, usa `DELETE /api/transactions/{id}`.
- quando estiver offline ou o backend falhar, guarda as mutacoes locais em uma fila e reenvia com `POST /api/transactions/sync` quando a conexao voltar.

Para desenvolvimento com Expo:

- em emulador Android, a URL normalmente sera `http://10.0.2.2:8000/api`;
- em dispositivo fisico, use o IP local da maquina, por exemplo `http://192.168.x.x:8000/api`.

## 📘 Contrato da API

### Base URL

```text
/api
```

### Endpoints de transacoes

#### `GET /transactions/`

Lista todas as transacoes ordenadas por data decrescente.

Resposta:

```json
[
  {
    "id": "txn_001",
    "amount": "125.50",
    "date": "2026-04-09T12:00:00Z",
    "category": "food",
    "type": "expense",
    "description": "Almoco",
    "created_at": "2026-04-09T12:00:00Z",
    "updated_at": "2026-04-09T12:00:00Z"
  }
]
```

#### `POST /transactions/`

Cria uma nova transacao.

Payload:

```json
{
  "id": "txn_001",
  "amount": "2500.00",
  "date": "2026-04-09T09:00:00Z",
  "category": "salary",
  "type": "income",
  "description": "Salario"
}
```

Respostas:

- `201 Created`: transacao criada com sucesso
- `409 Conflict`: ja existe uma transacao com o mesmo `id`

Exemplo de erro:

```json
{
  "message": "Transaction with this id already exists."
}
```

#### `PUT /transactions/{id}`

Atualiza uma transacao existente pelo identificador.

Payload:

```json
{
  "id": "txn_001",
  "amount": "230.00",
  "date": "2026-04-09T18:30:00Z",
  "category": "transport",
  "type": "expense",
  "description": "Combustivel"
}
```

Observacao:

- o `id` enviado no corpo e ignorado na atualizacao;
- o registro atualizado e definido pelo parametro da rota.

#### `DELETE /transactions/{id}`

Remove uma transacao existente.

Resposta:

- `204 No Content`

#### `POST /transactions/sync`

Aplica uma fila de mutacoes offline em lote. Este endpoint foi desenhado para retry: `add` e `update` funcionam como upsert pelo `id` da transacao, e `remove` e considerado aplicado mesmo quando a transacao ja foi removida.

Payload:

```json
{
  "operations": [
    {
      "client_operation_id": "op_001",
      "operation": "add",
      "transaction": {
        "id": "txn_001",
        "amount": "2500.00",
        "date": "2026-04-09T09:00:00Z",
        "category": "salary",
        "type": "income",
        "description": "Salario"
      }
    },
    {
      "client_operation_id": "op_002",
      "operation": "remove",
      "transaction_id": "txn_002"
    }
  ]
}
```

Resposta:

```json
{
  "results": [
    {
      "operation": "add",
      "transaction_id": "txn_001",
      "client_operation_id": "op_001",
      "status": "applied",
      "message": ""
    },
    {
      "operation": "remove",
      "transaction_id": "txn_002",
      "client_operation_id": "op_002",
      "status": "applied",
      "message": ""
    }
  ],
  "transactions": [
    {
      "id": "txn_001",
      "amount": "2500.00",
      "date": "2026-04-09T09:00:00Z",
      "category": "salary",
      "type": "income",
      "description": "Salario",
      "created_at": "2026-04-09T09:00:00Z",
      "updated_at": "2026-04-09T09:00:00Z"
    }
  ]
}
```

Observacoes:

- `operation` aceita `add`, `update` ou `remove`;
- `add` e `update` exigem `transaction`;
- `remove` aceita `transaction_id` ou o `id` dentro de `transaction`;
- `client_operation_id` e opcional e serve para o app correlacionar a resposta com a fila local.

## 🧾 Modelo de Dados

Cada transacao possui os seguintes campos:

- `id`: identificador unico definido pelo cliente mobile
- `amount`: valor monetario da transacao
- `date`: data e hora da transacao
- `category`: categoria livre definida pelo app
- `type`: `income` ou `expense`
- `description`: descricao opcional
- `created_at`: data de criacao no backend
- `updated_at`: data da ultima atualizacao no backend

## 🔐 Configuracao de Ambiente

Variaveis suportadas atualmente:

- `ENVIRONMENT`: `development` ou `production`
- `SECRET_KEY`: chave secreta do Django
- `DEBUG`: habilita modo de desenvolvimento; em producao deve ser `False`
- `ALLOWED_HOSTS`: lista de hosts permitidos, separados por virgula
- `DATABASE_URL`: URL de conexao com o banco; se ausente, usa SQLite
- `DB_CONN_MAX_AGE`: tempo de reuso de conexao do banco, em segundos
- `DB_SSL_REQUIRE`: exige SSL na conexao do banco quando suportado
- `CORS_ALLOW_ALL_ORIGINS`: libera todas as origens quando `True`
- `CORS_ALLOWED_ORIGINS`: origens permitidas para CORS, separadas por virgula
- `CORS_ALLOWED_ORIGIN_REGEXES`: regexes de origens permitidas, separadas por virgula

Comportamento por ambiente:

- em `development`, o projeto usa `ALLOWED_HOSTS=*` e `CORS_ALLOW_ALL_ORIGINS=True` por padrao, facilitando Expo em emulador e dispositivo fisico;
- em `production`, `DEBUG` precisa ser `False`, `ALLOWED_HOSTS` deve ser explicito e `CORS_ALLOW_ALL_ORIGINS` precisa ser `False`;
- em producao, use `CORS_ALLOWED_ORIGINS` para liberar o dominio real do frontend.

Exemplo de producao:

```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=sua-chave-longa-e-segura
ALLOWED_HOSTS=api.seudominio.com
DATABASE_URL=postgresql://usuario:senha@host:5432/expense_tracker
DB_CONN_MAX_AGE=600
DB_SSL_REQUIRE=True
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://app.seudominio.com
```

## 🧪 Comandos uteis

```bash
python3 manage.py migrate
python3 manage.py runserver
python3 manage.py createsuperuser
python3 manage.py check
```

## 👨‍💻 Autor

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/luan-sampaio">
        <img src="https://avatars.githubusercontent.com/luan-sampaio" width="100px;" alt="Foto de Luan Sampaio no GitHub"/>
        <br>
        <sub>
          <b>Luan Sampaio</b>
        </sub>
      </a>
    </td>
  </tr>
</table>
