# User API - FastAPI + MongoDB

API REST completa para gerenciar usuários com FastAPI e MongoDB, incluindo validação de dados, tratamento de erros e documentação automática.

## 🚀 Funcionalidades

- ✅ **CRUD Completo** - Criar, listar, buscar, atualizar e deletar usuários
- ✅ **Validação de Dados** - Validação automática com Pydantic
- ✅ **Tratamento de Erros** - Respostas HTTP padronizadas
- ✅ **Documentação Automática** - Swagger UI e ReDoc
- ✅ **Containerização** - Docker e Docker Compose
- ✅ **Banco de Dados** - MongoDB com Motor (async)

## 📋 Modelo de Usuário

```json
{
  "nome": "João Silva",
  "email": "joao@email.com",
  "data_nascimento": "1990-01-15"
}
```

### Validações:
- **Nome**: Obrigatório, entre 1-100 caracteres
- **Email**: Formato válido, único no sistema
- **Data de Nascimento**: Formato ISO date (YYYY-MM-DD)

## 🔧 Configuração

### Variáveis de Ambiente
Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

```env
MONGO_URL=mongodb://localhost:27017
DATABASE_NAME=user_db
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
```

## 🐳 Como Executar

### 1. Usando Docker Compose (Recomendado)

```bash
# Clonar/acessar o diretório do projeto
cd user-api

# Executar com Docker Compose
docker-compose up --build

# A API estará disponível em: http://localhost:8000
```

### 2. Executar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar MongoDB localmente (necessário)
# Depois executar a API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 Endpoints da API

### Base URL: `http://localhost:8000/api/v1`

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST   | `/users` | Criar usuário |
| GET    | `/users` | Listar todos os usuários |
| GET    | `/users/{id}` | Buscar usuário por ID |
| PUT    | `/users/{id}` | Atualizar usuário |
| DELETE | `/users/{id}` | Deletar usuário |

### Exemplos de Uso

#### Criar Usuário
```bash
curl -X POST "http://localhost:8000/api/v1/users" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "email": "joao@email.com",
    "data_nascimento": "1990-01-15"
  }'
```

#### Listar Usuários
```bash
curl "http://localhost:8000/api/v1/users"
```

#### Buscar Usuário por ID
```bash
curl "http://localhost:8000/api/v1/users/{user_id}"
```

#### Atualizar Usuário
```bash
curl -X PUT "http://localhost:8000/api/v1/users/{user_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Santos",
    "email": "joao.santos@email.com"
  }'
```

#### Deletar Usuário
```bash
curl -X DELETE "http://localhost:8000/api/v1/users/{user_id}"
```

## 📖 Documentação

Após executar a API, acesse:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

## 🏗️ Estrutura do Projeto

```
user-api/
├── app/
│   ├── __init__.py         # Inicialização do pacote
│   ├── main.py             # Aplicação FastAPI principal
│   ├── models.py           # Modelos Pydantic
│   ├── database.py         # Conexão MongoDB
│   └── routes.py           # Endpoints da API
├── requirements.txt        # Dependências Python
├── Dockerfile             # Container da API
├── docker-compose.yml     # Orquestração de containers
├── .env.example           # Exemplo de variáveis de ambiente
└── README.md              # Documentação do projeto
```

## 🛠️ Tecnologias Utilizadas

- **FastAPI** 0.115.5 - Framework web moderno
- **MongoDB** 7.0 - Banco de dados NoSQL
- **Motor** 3.6.0 - Driver MongoDB assíncrono
- **Pydantic** 2.10.3 - Validação de dados
- **Docker** - Containerização
- **Uvicorn** - Servidor ASGI

## 🛑 Parar os Serviços

```bash
docker-compose down
```

## 📝 Notas de Desenvolvimento

- Todas as operações são assíncronas para melhor performance
- Validação automática de ObjectId do MongoDB
- Tratamento de erros padronizado (400, 404, etc.)
- Configuração flexível via variáveis de ambiente
- Logs de conexão com MongoDB