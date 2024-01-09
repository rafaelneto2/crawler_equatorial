import os
import time
from os import listdir
from os.path import isfile, join

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from pypdf import PdfReader
from selenium import webdriver
from selenium.webdriver.common.by import By

from schema import RequestSchema, ResponseSchema, BaseEnergia

app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": str(exc)},
    )


@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error":
                     {"message": str(exc)}
                 },
    )


@app.post('/', response_model=ResponseSchema)
def get_info(req: RequestSchema):
    download_boleto(req)
    resp = get_infos()
    return resp


def get_infos():
    file_name = f'temp/{[f for f in listdir('temp') if isfile(join('temp', f))][0]}'

    pdf = open(file_name, 'rb')
    reader = PdfReader(pdf)
    text = reader.pages[0].extract_text()

    resp = ResponseSchema

    for idx, item in enumerate(text.split('\n')):
        if 'Tipo de fornecimento' in item:
            resp.tipo_fornecimento = item.split('Classificação')[0].split(' ')[-1]

        if 'R$***' in item:
            values = item.split(' ')
            total_a_pagar = values[0].replace('*', '').split('R$')
            resp.total_a_pagar = 'R$ ' + total_a_pagar[1]
            resp.vencimento = item.split(' ')[1][:10]

        if 'CRÉDITO RECEBIDO KWH' in item:
            resp.credito_recebido = item.split('CRÉDITO RECEBIDO KWH: ')[1].split(' ')[0][0:-1]

        if 'ENERGIA ATIVA FORNECIDA' in item:
            values = item.split(' ')
            base_energia_ativa = BaseEnergia(
                unidade=values[3],
                preco_unit_com_tributos=values[4],
                quantidade=values[5],
                valor=values[7]
            )
            resp.qtd_energia_ativa_fornecida = base_energia_ativa

        if 'ENERGIA INJETADA' in item:
            values = item.split(' ')
            base_energia_injetada = BaseEnergia(
                unidade=values[2],
                preco_unit_com_tributos=values[3],
                quantidade=values[4],
                valor=values[5]
            )
            resp.qtd_energia_injetada = base_energia_injetada

        if 'CONSUMO FATURADO(kWh) MÊS/ANO' in item:
            resp.media = text.split('\n')[idx + 1]

    pdf.close()
    os.remove(file_name)
    return resp


def download_boleto(req):
    absolute_path = os.path.abspath("main.py").replace("main.py", "temp")
    op = webdriver.ChromeOptions()
    op.add_experimental_option("prefs", {
        "download.default_directory": absolute_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    driver = webdriver.Chrome(options=op)
    driver.get('https://equatorialgoias.com.br/LoginGO.aspx')

    try:
        driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtUC').send_keys(req.uc)
        driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtDocumento').send_keys(req.documento)
        driver.find_element(by=By.XPATH, value='//*[@id="WEBDOOR_headercorporativogo_divLogin"]/div[2]/button').click()
        time.sleep(5)
    except Exception as e:
        driver.close()
        raise HTTPException(status_code=500, detail='Não foi possível realizar o login\nErro: ' + str(e))

    if len(req.documento) < 12 or req.data_nascimento is not None:
        try:
            time.sleep(3)
            driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtData').send_keys(req.data_nascimento)
            driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_btnValidar').click()
            time.sleep(3)
        except Exception as e:
            driver.close()
            raise HTTPException(status_code=500, detail='Não foi possível inserir a data\nErro: ' + str(e))

    try:
        driver.get('https://equatorialgoias.com.br/AgenciaGO/Servi%C3%A7os/aberto/SegundaVia.aspx')
        driver.find_element(by=By.XPATH, value='//*[@id="CONTENT_cbTipoEmissao"]/option[2]').click()
        driver.find_element(by=By.XPATH, value='//*[@id="CONTENT_cbMotivo"]/option[7]').click()
        driver.find_element(by=By.ID, value='CONTENT_btEnviar').click()
        time.sleep(3)
    except Exception as e:
        driver.close()
        raise HTTPException(status_code=500, detail='Não foi possível emitir o boleto\nErro: ' + str(e))

    try:
        driver.find_element(by=By.XPATH, value='//*[@id="ContentPage"]/div[3]/div/table/thead/tr[2]/td[2]/a').click()
        driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
        time.sleep(3)
    except Exception as e:
        driver.close()
        raise HTTPException(status_code=500, detail='Não foi possível baixar o boleto\nErro: ' + str(e))

    driver.close()


if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True, log_level="info")
