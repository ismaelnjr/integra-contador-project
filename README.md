# Integra Contador - Relatório Fiscal (SITFIS)

Sistema para geração de relatórios fiscais através da API Serpro Integra Contador, implementado com arquitetura class-based seguindo melhores práticas de programação.

## Estrutura do Projeto

```
integra-contador-project/
├── integra_contador/
│   ├── config/          # Configurações (Settings)
│   ├── api/             # Integração com API Serpro
│   │   ├── auth.py      # Autenticação
│   │   ├── client.py    # Cliente HTTP base
│   │   └── sitfis.py    # Serviço SITFIS
│   ├── models/          # Modelos de dados
│   └── repositories/    # Repositórios de dados
├── tests/
│   └── test_sitfis.py   # Caso de uso de teste
├── empresas.json        # Dados de entrada
├── .env                 # Variáveis de ambiente (criar a partir de .env.example)
└── requirements.txt     # Dependências
```

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

Copie o arquivo `.env.example` para `.env` e preencha com suas credenciais:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas informações:

```env
CONSUMER_KEY=sua_consumer_key
CONSUMER_SECRET=seu_consumer_secret
CERTIFICADO_PATH=C:\\certs\\seu_certificado.pfx
CERTIFICADO_SENHA=sua_senha
CONTRATANTE_CNPJ=11491110000127
AUTOR_PEDIDO_CNPJ=11491110000127
```

## Uso

### Caso de Teste

Execute o script de teste que processa todas as empresas do arquivo `empresas.json`:

```bash
python tests/test_sitfis.py
```

O script irá:
1. Validar configurações
2. Autenticar na API Serpro
3. Para cada empresa:
   - Solicitar protocolo (se não existir)
   - Aguardar tempo necessário
   - Emitir relatório PDF
   - Salvar PDF no diretório configurado
   - Limpar protocolo após geração

### Uso Programático

```python
from integra_contador import SITFISService, SerproAuthenticator, Settings

# Valida configurações
Settings.validate()

# Inicializa serviços
authenticator = SerproAuthenticator()
sitfis = SITFISService(authenticator)

# Solicita e emite relatório
protocolo, pdf_bytes = sitfis.gerar_relatorio_completo("12345678000190")
```

## Arquivo empresas.json

Formato do arquivo de entrada:

```json
[
  {
    "idempresas": 1,
    "cnpj": "11.497.110/0001-27",
    "razao": "Nome da Empresa",
    "protocoloRelatorio": ""
  }
]
```

- `idempresas`: ID único da empresa
- `cnpj`: CNPJ (aceita com ou sem formatação)
- `razao`: Razão social
- `protocoloRelatorio`: Protocolo do relatório (deixe vazio para nova solicitação)

## Dependências

- `requests-pkcs12`: Autenticação com certificado digital
- `pycurl`: Requisições HTTP
- `python-dotenv`: Gerenciamento de variáveis de ambiente

## Funcionalidades

### Serviço SITFIS

- **Solicitar Relatório**: Solicita protocolo para geração de relatório
- **Emitir Relatório**: Gera PDF do relatório de situação fiscal
- **Fluxo Completo**: Executa solicitação e emissão em uma única chamada

### Recursos

- Tratamento de cache (status 304)
- Aguardar tempo de processamento quando necessário
- Validação de CNPJ
- Logging estruturado
- Tratamento de erros robusto
- Type hints em todo o código

## Notas

- Os PDFs gerados são salvos no diretório configurado em `PDF_OUTPUT_PATH`
- O arquivo `empresas.json` é atualizado automaticamente com os protocolos obtidos
- Após gerar o PDF, o protocolo é limpo no arquivo JSON
- O sistema suporta protocolos em cache (status 304) da API

## Desenvolvimento

O código segue os princípios SOLID e boas práticas:
- Separação de responsabilidades
- Injeção de dependências
- Type hints
- Docstrings completas
- Logging estruturado
- Tratamento de exceções customizadas
