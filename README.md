# Como Rodar a Aplicação Python

Este repositório contém uma aplicação Python que fornece informações sobre o consumo de energia elétrica com base nos
dados coletados do boleto. Siga as instruções abaixo para executar a aplicação.

## Pré-requisitos

Certifique-se de ter o Python instalado em seu sistema. Recomendamos a versão 3.11.

## Instalação

1. Clone este repositório:

   ```bash
   git clone https://github.com/seu-usuario/nome-do-repositorio.git
   ```

2. Acesse o diretório do projeto:

    ```bash
   cd get-info-boleto
   ```

3. Instale as dependências:

    ```bash
   pip install -r requirements.txt
   ```

## Execução

1. Execute o script Python:

   ```bash
   python main.py
   ```

2. A aplicação estará acessível em **http://localhost:8000** por padrão.

## Documentação da API

### Endpoint: `/`

#### Método: `POST`

**Dados de Request:**

Caso seja uma pessoa física:

```json
{
   "uc": "unidade consumidora",
   "documento": "documento CPF",
   "data_nascimento": "data no formato dd/MM/yyyy"
}
```

Caso seja uma pessoa jurídica:

```json
{
   "uc": "unidade consumidora",
   "documento": "documento CNPJ"
}
```

**Exemplo de Dados de Response:**

```json
{
   "tipo_fornecimento": "BIFÁSICO",
   "vencimento": "07/12/2023",
   "total_a_pagar": "R$ 131,86",
   "credito_recebido": "ATV=213,60",
   "qtd_energia_ativa_fornecida": {
      "unidade": "kWh",
      "quantidade": "284,00",
      "preco_unit_com_tributos": "0,899595",
      "valor": "255,48"
   },
   "qtd_energia_injetada": {
      "unidade": "kWh",
      "quantidade": "213,60",
      "preco_unit_com_tributos": "0,710630",
      "valor": "-151,79"
   },
   "media": "224,38"
}
```

**Certifique-se de fornecer os dados corretos no formato especificado para obter resultados precisos.**
