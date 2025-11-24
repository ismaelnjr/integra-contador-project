# Integra Contador - API Serpro

Sistema para integração com a API Serpro Integra Contador, implementado com arquitetura class-based seguindo melhores práticas de programação Python.

## Estrutura do Projeto

```
integra-contador-project/
├── integra_contador/
│   ├── api/             # Integração com API Serpro
│   │   ├── auth.py      # Autenticação
│   │   ├── client.py    # Cliente HTTP base
│   │   ├── sitfis.py    # Serviço SITFIS (Relatórios Fiscais)
│   │   ├── pgdasd.py    # Serviço PGDASD (DAS Simples Nacional)
│   │   ├── dctfweb.py   # Serviço DCTFWEB (Guias de Pagamento)
│   │   └── validators.py # Validadores de dados da API
│   ├── models/          # Modelos de dados
│   │   ├── empresa.py   # Modelo Empresa
│   │   ├── das.py       # Modelo DAS
│   │   └── guia.py      # Modelo Guia DCTFWEB
│   ├── settings.py      # Configurações centralizadas
│   └── __init__.py
├── app/
│   ├── gerar_relatorio_fiscal.py  # Script para gerar relatórios SITFIS
│   ├── gerar_das.py               # Script para gerar DAS
│   ├── gerar_guia_dctfweb.py      # Script para gerar guias DCTFWEB
│   └── repositories/
│       └── empresa_repository.py  # Repositório de empresas
├── empresas.json        # Dados de entrada
├── .env                 # Variáveis de ambiente (criar a partir de env_example.txt)
└── requirements.txt     # Dependências
```

## Endpoints Implementados

### 1. SITFIS - Relatório de Situação Fiscal

**Serviço:** `integra_contador.api.sitfis.SITFISService`

**Endpoints:**

- `POST /Apoiar` - Solicitar protocolo do relatório

  - Serviço: `SOLICITARPROTOCOLO91`
  - Retorna: protocolo e tempo de espera
- `POST /Emitir` - Emitir relatório em PDF

  - Serviço: `RELATORIOSITFIS92`
  - Parâmetro: protocolo do relatório
  - Retorna: PDF do relatório em base64

**Métodos disponíveis:**

- `solicitar_relatorio(cnpj)` - Solicita protocolo
- `emitir_relatorio(cnpj, protocolo)` - Emite PDF
- `gerar_relatorio_completo(cnpj)` - Executa fluxo completo (solicitar + emitir)

**Script:** `app/gerar_relatorio_fiscal.py`

### 2. PGDASD - DAS do Simples Nacional

**Serviço:** `integra_contador.api.pgdasd.PGDASDService`

**Endpoints:**

- `POST /Emitir` - Gerar DAS
  - Serviço: `GERARDAS12`
  - Parâmetros: período de apuração (AAAAMM), data de consolidação (opcional)
  - Retorna: Lista de DAS gerados com PDFs

**Métodos disponíveis:**

- `gerar_das(cnpj, periodo_apuracao, data_consolidacao=None)` - Gera DAS para período

**Script:** `app/gerar_das.py`

### 3. DCTFWEB - Guias de Pagamento

**Serviço:** `integra_contador.api.dctfweb.DCTFWEBService`

**Endpoints:**

- `POST /Emitir` - Gerar guia de pagamento
  - Serviço: `GERARGUIA31`
  - Parâmetros: anoPA, mesPA, categoria (opcional)
  - Retorna: Guia de pagamento com PDF

**Métodos disponíveis:**

- `gerar_guia(cnpj, dados_guia)` - Gera guia de pagamento
  - `dados_guia` deve conter: `anoPA`, `mesPA`, `categoria` (opcional)

**Script:** `app/gerar_guia_dctfweb.py`

## Pré-requisitos

- Python 3.8 ou superior
- Certificado digital (.pfx ou .p12) da Serpro
- Credenciais da API Serpro (consumer_key e consumer_secret)

## Configuração do Ambiente

### 1. Criar ambiente virtual

```bash
python -m venv venv
```

### 2. Ativar ambiente virtual

**Windows (PowerShell):**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**

```bash
source venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

Copie o arquivo `env_example.txt` para `.env` e preencha com suas credenciais:

```bash
cp env_example.txt .env
```

Edite o arquivo `.env` com suas informações:

```env
CONSUMER_KEY=sua_consumer_key
CONSUMER_SECRET=seu_consumer_secret
CERTIFICADO_PATH=C:\\certs\\seu_certificado.pfx
CERTIFICADO_SENHA=sua_senha
CONTRATANTE_CNPJ=seu_cnpj
AUTOR_PEDIDO_CNPJ=seu_cnpj
PDF_OUTPUT_PATH=C:\\integracontador\\
```

## Uso

### Scripts de Linha de Comando

#### Gerar Relatórios de Situação Fiscal (SITFIS)

```bash
python app/gerar_relatorio_fiscal.py
```

Processa todas as empresas do arquivo `empresas.json` e gera relatórios de situação fiscal.

#### Gerar DAS do Simples Nacional

```bash
python app/gerar_das.py
```

Solicita período de apuração e gera DAS para todas as empresas.

#### Gerar Guias de Pagamento (DCTFWEB)

```bash
python app/gerar_guia_dctfweb.py
```

Solicita dados da guia (ano, mês) e gera guias para todas as empresas.

### Uso Programático

#### Exemplo: Gerar Relatório SITFIS

```python
from integra_contador.api.sitfis import SITFISService
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.settings import Settings

# Valida configurações
Settings.validate()

# Inicializa serviços
authenticator = SerproAuthenticator()
sitfis = SITFISService(authenticator)

# Gera relatório completo
protocolo, pdf_bytes = sitfis.gerar_relatorio_completo("12345678000190")
```

#### Exemplo: Gerar DAS

```python
from integra_contador.api.pgdasd import PGDASDService
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.settings import Settings

Settings.validate()
authenticator = SerproAuthenticator()
pgdasd = PGDASDService(authenticator)

# Gera DAS para período
das_list = pgdasd.gerar_das(
    cnpj="12345678000190",
    periodo_apuracao="202509",
    data_consolidacao="20250930"  # opcional
)
```

#### Exemplo: Gerar Guia DCTFWEB

```python
from integra_contador.api.dctfweb import DCTFWEBService
from integra_contador.api.auth import SerproAuthenticator
from integra_contador.settings import Settings

Settings.validate()
authenticator = SerproAuthenticator()
dctfweb = DCTFWEBService(authenticator)

# Gera guia
guia = dctfweb.gerar_guia(
    cnpj="12345678000190",
    dados_guia={
        "anoPA": "2025",
        "mesPA": "10",
        "categoria": "GERAL_MENSAL"  # opcional
    }
)
```

## Arquivo empresas.json

Crie o arquivo `empresas.json` na raiz do projeto com a lista de empresas que deseja processar.

**Importante:** Este arquivo contém dados sensíveis e está no `.gitignore` para não ser versionado.

### Criar o arquivo

Crie um arquivo chamado `empresas.json` na raiz do projeto com o seguinte formato:

```json
[
  {
    "idempresas": 1,
    "cnpj": "11.111.111/0001-91",
    "razao": "Nome da Empresa",
    "protocoloRelatorio": ""
  }
]
```

### Campos do arquivo

- `idempresas`: ID único da empresa (número inteiro)
- `cnpj`: CNPJ da empresa (aceita com ou sem formatação, ex: "11.111.111/0001-91" ou "11111111000191")
- `razao`: Razão social da empresa
- `protocoloRelatorio`: Protocolo do relatório SITFIS (deixe vazio `""` para nova solicitação)

### Exemplo com múltiplas empresas

```json
[
  {
    "idempresas": 1,
    "cnpj": "11.111.111/0001-91",
    "razao": "Empresa A Ltda",
    "protocoloRelatorio": ""
  },
  {
    "idempresas": 2,
    "cnpj": "22.333.444/0001-55",
    "razao": "Empresa B ME",
    "protocoloRelatorio": ""
  }
]
```

**Nota:** O arquivo é atualizado automaticamente pelos scripts com os protocolos obtidos durante o processamento.

## Dependências

- `requests-pkcs12`: Autenticação com certificado digital
- `pycurl`: Requisições HTTP
- `python-dotenv`: Gerenciamento de variáveis de ambiente

## Funcionalidades

### Recursos Comuns

- Tratamento de cache (status 304)
- Aguardar tempo de processamento quando necessário
- Validação de dados de entrada
- Logging estruturado
- Tratamento de erros robusto
- Type hints em todo o código
- Suporte a processamento em lote

### Validações

- Validação de CNPJ
- Validação de período de apuração (AAAAMM)
- Validação de data de consolidação (AAAAMMDD)
- Validação de ano e mês de apuração
- Verificação de mensagens da API

## Notas sobre Nomenclatura

Os modelos de dados (`integra_contador/models/`) utilizam atributos em **camelCase** (ex: `protocoloRelatorio`, `cnpjCompleto`, `periodoApuracao`) para manter compatibilidade direta com:

- A API Serpro que retorna dados neste formato
- O arquivo `empresas.json` que usa este formato
- Evita necessidade de mapeamento/conversão nos métodos `from_dict`/`to_dict`

Embora o padrão Python (PEP 8) recomende `snake_case`, a escolha por `camelCase` foi feita para simplificar a integração e evitar conversões desnecessárias.

## Notas

- Os PDFs gerados são salvos no diretório configurado em `PDF_OUTPUT_PATH`
- O arquivo `empresas.json` é atualizado automaticamente com os protocolos obtidos
- Após gerar o PDF, o protocolo é limpo no arquivo JSON (quando aplicável)
- O sistema suporta protocolos em cache (status 304) da API
- Todos os scripts podem ser executados de qualquer diretório (ajuste automático de PYTHONPATH)

## Desenvolvimento

O código segue os princípios SOLID e boas práticas:

- Separação de responsabilidades
- Injeção de dependências
- Type hints
- Docstrings completas
- Logging estruturado
- Tratamento de exceções customizadas
- Arquitetura modular e extensível
