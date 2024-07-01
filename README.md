
# Equatorial Goiás Invoice Downloader

Esta aplicação Python acessa o site [Equatorial Goiás](https://equatorialgoias.com.br/) para realizar o download de faturas, extrair informações e fazer o upload dos arquivos no Google Drive. A aplicação está integrada ao Azure Service Bus para processar mensagens que chegam na fila de execução.

## Funcionalidades

- **Download de Faturas:** Acessa o site da Equatorial Goiás, realiza login, navega até a área de faturas e faz o download.
- **Extração de Informações:** Processa as faturas baixadas e extrai dados importantes.
- **Upload para Google Drive:** Faz o upload das faturas processadas para uma conta do Google Drive.
- **Integração com Azure Service Bus:** Observa o tópico `customers-to-run` e processa mensagens JSON para realizar o download e processamento das faturas. Envia resultados para o tópico `run-results`.

## Estrutura das Mensagens

### Mensagem de Entrada (Fila `customers-to-run`)

Exemplo:
```json
{
    "correlation_id":"35755509-4aba-486d-b42d-7bfb90be7a16",
    "uc":"15293750",
    "documento":"331.764.851-15",
    "data_nascimento":"12/05/1965",
    "codigo_auxiliar":"12"
}
```

### Mensagem de Saída (Fila `run-results`)

#### Sucesso
```json
{
    "correlation_id":"868cfedc-9222-4174-9e04-05246b2983e2",
    "success":true,
    "error":null,
    "data":{
        "tipo_fornecimento":"MONOFÁSICO",
        "conta_mes":"MAI/2024",
        "vencimento":"14/06/2024",
        "total_a_pagar":"110,70",
        "credito_recebido":"123",
        "saldo":"123",
        "qtd_energia_ativa_fornecida":{
            "unidade":"kWh",
            "quantidade":"440,00",
            "preco_unit_com_tributos":"0,922683",
            "valor":"405,98"
        },
        "qtd_energia_injetada":[
            {
                "unidade":"kWh",
                "quantidade":"259,93",
                "preco_unit_com_tributos":"0,922683",
                "valor":"-239,83"
            },
            {
                "unidade":"kWh",
                "quantidade":"72,62",
                "preco_unit_com_tributos":"0,922683",
                "valor":"-67,01"
            }
        ],
        "media":"141,15",
        "url_fatura":"https://drive.usercontent.google.com/u/0/uc?id=1ivIA7vlG9c2vh8m0rwygzttb6QdCY3dz&export=download"
    }
}
```

#### Erro
```json
{
    "correlation_id": "3B52447D-AFBF-4958-BC7F-AB549D0ADC2F",
    "success": false,
    "data": {},
    "error": {
        "code": "102",
        "message": "Mensagem",
        "detail": "Detail"
    }
}
```

### Códigos de Erro

| Código | Mensagem de Erro |
|--------|------------------|
| `101`  | Erro ao realizar o login. (Ou a mensagem informada na página do navegador) |
| `102`  | Erro inesperado ao inserir a data, por favor tente novamente. (Ou a mensagem informada na página do navegador) |
| `103`  | Não há boleto disponível para download. (Ou a mensagem informada na página do navegador) |
| `104`  | Erro ao fazer download do boleto. (Ou a mensagem informada na página do navegador) |
| `105`  | Erro inesperado ao emitir fatura. (Ou a mensagem informada na página do navegador) |
| `106`  | Erro ao recuperar informações do boleto. |
| `107`  | Erro ao traduzir mensagem. |

## Como Executar

### Pré-requisitos

- Docker
- Conta no Azure Service Bus
- Credenciais de acesso ao Google Drive

### Executando com Docker

1. **Pull da Imagem Docker:**
   ```bash
   docker pull SEU_USUARIO_DOCKER_HUB/equatorial-goias-invoice-downloader
   ```

2. **Configuração das Variáveis de Ambiente:**

   Crie um arquivo `.env` com as seguintes variáveis:
   ```
   AZURE_SERVICE_BUS_CONNECTION_STRING=YOUR_CONNECTION_STRING
   AZURE_TOPIC_CUSTOMERS_TO_RUN=customers-to-run
   AZURE_TOPIC_RUN_RESULTS=run-results
   GOOGLE_DRIVE_API_CREDENTIALS=YOUR_GOOGLE_DRIVE_CREDENTIALS_JSON
   ```

3. **Executar o Container Docker:**
   ```bash
   docker run --env-file .env SEU_USUARIO_DOCKER_HUB/equatorial-goias-invoice-downloader
   ```
