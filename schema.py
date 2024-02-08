from pydantic import BaseModel


class RequestSchema(BaseModel):
    uc: str
    documento: str
    data_nascimento: str = None


class BaseEnergia(BaseModel):
    unidade: str
    quantidade: str
    preco_unit_com_tributos: str
    valor: str


class ResponseSchema(BaseModel):
    tipo_fornecimento: str
    vencimento: str
    total_a_pagar: str
    credito_recebido: str
    saldo: str
    qtd_energia_ativa_fornecida: BaseEnergia
    qtd_energia_injetada: BaseEnergia
    media: str
