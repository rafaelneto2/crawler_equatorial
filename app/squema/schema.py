from pydantic import BaseModel


class RequestSchema(BaseModel):
    correlation_id: str
    uc: str
    documento: str
    data_nascimento: str = None
    codigo_auxiliar: str


class BaseEnergia(BaseModel):
    unidade: str | None
    quantidade: str | None
    preco_unit_com_tributos: str | None
    valor: str | None


class ErrorDetails(BaseModel):
    code: str
    message: str | None
    detail: str | None


class UploadSchema(BaseModel):
    correlation_id: str
    file: str


class Dados(BaseModel):
    tipo_fornecimento: str
    conta_mes: str
    vencimento: str
    total_a_pagar: str
    credito_recebido: str | None
    saldo: str | None
    qtd_energia_ativa_fornecida: BaseEnergia | None
    qtd_energia_injetada: list[BaseEnergia] | None
    media: str | None


class ResponseSchema(BaseModel):
    correlation_id: str | None
    success: bool
    error: ErrorDetails | None
    data: Dados | None
