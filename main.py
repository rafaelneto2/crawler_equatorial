import logging
import os
import time
from os import listdir
from os.path import isfile, join

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from pypdf import PdfReader
from selenium.webdriver.common.by import By
from seleniumwire import webdriver

from schema import RequestSchema, ResponseSchema, BaseEnergia

app = FastAPI()
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "equatorial-credentials.json"
ID_FOLDER_EQUATORIAL = "1TX79sj4OvbZJIDNSZtHbxxIRwuSG074t"

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)


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
    verify_path_and_files()
    download_boleto(req)
    resp = get_infos()
    return resp[0]


@app.post('/v2', response_model=list[ResponseSchema])
def get_info(req: RequestSchema):
    verify_path_and_files()
    download_boleto(req)
    resp = get_infos(req)
    return resp


def get_infos(req: RequestSchema):
    global qtd_energia_injetada, qtd_energia_ativa_fornecida, tipo_fornecimento, conta_mes, vencimento, total_a_pagar, credito_recebido, saldo, media
    try:
        response = []
        for file in [f for f in listdir("temp") if isfile(join("temp", f))]:

            file_name = f'temp/{file}'

            pdf = open(file_name, 'rb')
            reader = PdfReader(pdf)
            text = reader.pages[0].extract_text()

            flag_valor = True

            for idx, item in enumerate(text.split('\n')):
                if 'Tipo de fornecimento' in item:
                    tipo_fornecimento = item.split('Classificação')[0].strip().split(' ')[-1]

                if 'R$***' in item and flag_valor:
                    values = item.split(' ')
                    total_a_pagar = values[0].replace('*', '').split('R$')
                    total_a_pagar = total_a_pagar[1]
                    vencimento = item.split(' ')[1][:10]
                    conta_mes = text.split('\n')[idx + 1][0:8]
                    flag_valor = False

                if 'CRÉDITO RECEBIDO KWH' in item:
                    credito_recebido = item.split('CRÉDITO RECEBIDO KWH: ATV=')[1].split(' ')[0][0:-1]
                    saldo = item.split('SALDO KWH: ATV=')[1].split(' ')[0][0:-1]

                if 'ENERGIA ATIVA FORNECIDA' in item:
                    values = item.split(' ')
                    base_energia_ativa = BaseEnergia(
                        unidade=values[3],
                        preco_unit_com_tributos=values[4],
                        quantidade=values[5],
                        valor=values[7]
                    )
                    qtd_energia_ativa_fornecida = base_energia_ativa

                if 'ENERGIA INJETADA' in item:
                    values = item.split(' ')

                    if len(values) > 6:
                        valor_energia_injetada = values[6]
                    else:
                        valor_energia_injetada = values[5]

                    base_energia_injetada = BaseEnergia(
                        unidade=values[2],
                        preco_unit_com_tributos=values[3],
                        quantidade=values[4],
                        valor=valor_energia_injetada
                    )
                    qtd_energia_injetada = base_energia_injetada

                if 'CONSUMO FATURADO(kWh) MÊS/ANO' in item:
                    media = text.split('\n')[idx + 1]

            link_download_file = upload_file(f'{req.codigo_auxiliar}_{req.uc}_{conta_mes}.pdf', file_name, ID_FOLDER_EQUATORIAL)

            boleto_info = ResponseSchema(
                tipo_fornecimento=tipo_fornecimento,
                conta_mes=conta_mes,
                vencimento=vencimento,
                total_a_pagar=total_a_pagar,
                credito_recebido=credito_recebido,
                saldo=saldo,
                qtd_energia_ativa_fornecida=qtd_energia_ativa_fornecida,
                qtd_energia_injetada=qtd_energia_injetada,
                media=media,
                url_fatura=link_download_file
            )
            response.append(boleto_info)
            pdf.close()
            os.remove(file_name)

    except Exception as e:
        logging.error(str(e))
        raise HTTPException(status_code=500, detail='Erro ao recuperar informações do boleto.')

    return response


def download_boleto(req):
    absolute_path = os.path.abspath("main.py").replace("main.py", "temp")
    username = "hy1zz0azv0regqx-country-br-state-goias"
    password = "fulcfr23i0jjhn8"
    proxy = "rp.proxyscrape.com:6060"
    # username = "sh1al1yp0ekpzwb-country-br"
    # password = "ee6qa47ecjbtw7r"
    # proxy = "rp.proxyscrape.com:6060"
    seleniumwire_options = {
        'proxy': {
            'http': f'https://{username}:{password}@{proxy}',
            'verify_ssl': False,
        },
    }

    op = webdriver.ChromeOptions()
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Mobile Safari/537.36'
    op.add_experimental_option("prefs", {
        "download.default_directory": absolute_path,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    })
    op.add_argument(f'user-agent={user_agent}')
    # op.add_argument(f'--proxy-server={proxy}')
    op.add_argument("--headless=new")
    op.add_argument("--disable-gpu")
    op.add_argument("--no-sandbox")
    op.add_argument("--disable-infobars")
    op.add_argument("--disable-dev-shm-usage")
    # driver = webdriver.Chrome(seleniumwire_options=seleniumwire_options, options=op)
    driver = webdriver.Chrome(options=op)
    driver.get('https://equatorialgoias.com.br/LoginGO.aspx')

    time.sleep(3)

    try:
        driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtUC').send_keys(req.uc)
        driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtDocumento').send_keys(req.documento)
        driver.find_element(by=By.XPATH, value='//*[@id="WEBDOOR_headercorporativogo_divLogin"]/div[2]/button').click()
        time.sleep(3)
    except Exception as e:
        driver.close()
        logging.error(str(e))
        if hasattr(e, 'alert_text'):
            msg = e.alert_text
        else:
            msg = 'Erro ao realizar o login.'
        raise HTTPException(status_code=500, detail=msg)

    if len(req.documento) < 12:
        try:
            time.sleep(3)
            driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtData').send_keys(req.data_nascimento)
            driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_btnValidar').click()
            time.sleep(3)
        except Exception as e:
            driver.close()
            logging.error(str(e))
            if hasattr(e, 'alert_text'):
                msg = e.alert_text
            else:
                msg = 'Erro inesperado ao inserir a data, por favor tente novamente.'
            raise HTTPException(status_code=500, detail=msg)

    select_options(driver)

    try:
        boletos = driver.find_elements(by=By.XPATH, value='//*[@id="ContentPage"]/div[3]/div/table/thead/tr/td[2]/a')
        if len(boletos) > 1:
            for i in range(len(boletos)):
                if i == 0:
                    boletos[0].click()
                    driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
                    time.sleep(3)
                else:
                    select_options(driver)
                    novos_boletos = driver.find_elements(by=By.XPATH,
                                                         value='//*[@id="ContentPage"]/div[3]/div/table/thead/tr/td[2]/a')
                    novos_boletos[i].click()
                    driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
                    time.sleep(3)
        elif len(boletos) == 1:
            boletos[0].click()
            driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
            time.sleep(3)
        else:
            msg = 'Não há boleto disponível para download.'
            raise HTTPException(status_code=503, detail=msg)

    except Exception as e:
        driver.close()
        logging.error(str(e))
        if hasattr(e, 'alert_text'):
            msg = {e.alert_text}
        else:
            msg = 'Não há boleto disponível para download.'
        raise HTTPException(status_code=503, detail=msg)

    driver.close()


def select_options(driver):
    try:
        driver.get('https://equatorialgoias.com.br/AgenciaGO/Servi%C3%A7os/aberto/SegundaVia.aspx')
        driver.find_element(by=By.XPATH, value='//*[@id="CONTENT_cbTipoEmissao"]/option[2]').click()
        driver.find_element(by=By.XPATH, value='//*[@id="CONTENT_cbMotivo"]/option[7]').click()
        driver.find_element(by=By.ID, value='CONTENT_btEnviar').click()
        time.sleep(3)
    except Exception as e:
        driver.close()
        logging.error(str(e))
        if hasattr(e, 'alert_text'):
            msg = e.alert_text
        else:
            msg = 'Erro inesperado ao emitir o boleto, por favor tente novamente.'
        raise HTTPException(status_code=500, detail=msg)


def verify_path_and_files():
    if not os.path.exists('temp'):
        # Create the directory
        os.makedirs('temp')
        print("Directory created successfully!")
    else:
        print("Directory already exists!")
    for file in [f for f in listdir('temp') if isfile(join('temp', f))]:
        os.remove(f'temp/{file}')


def upload_file(file_name, file_path, id_folder):
    url_download_file = 'https://drive.usercontent.google.com/u/0/uc?id={id_file}&export=download'
    try:
        file_metadata = {
            'name': file_name,
            'parents': [id_folder]
        }

        media = MediaFileUpload(file_path, mimetype='application/pdf')
        file = (
            drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id')
            .execute()
        )

        print('Arquivo enviado com sucesso. ID: %s' % file.get('id'))

        return url_download_file.format(id_file=file.get('id'))

    except HttpError as error:
        print(f"Ocorreu um erro ao fazer upload do arquivo: {error}")


if __name__ == "__main__":
    uvicorn.run("main:app", host='127.0.0.1', port=8000)
