import logging
import os
import time
from os import listdir
from os.path import isfile, join

from azure.servicebus import ServiceBusReceiver
from selenium.webdriver.common.by import By
from seleniumwire import webdriver

from event.producer import producer_result, create_result_obj
from squema.schema import RequestSchema


def download_boleto(req: RequestSchema, receiver: ServiceBusReceiver, message, return_msg: bool):
    try:
        absolute_path = os.path.abspath("main.py").replace("main.py", "temp")
        username = "sh1al1yp0ekpzwb-country-br-state-goias"
        password = "ee6qa47ecjbtw7r"
        proxy = "rp.proxyscrape.com:6060"
        proxy_url = f'https://{username}:{password}@{proxy}'
        seleniumwire_options = {
            'proxy': {
                'http': f'https://{username}:{password}@{proxy}',
                'verify_ssl': False,
            },
        }

        op = webdriver.ChromeOptions()
        user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.90 Mobile Safari/537.36'
        op.add_argument("--no-sandbox")
        op.add_argument("--headless=new")
        op.add_argument("--disable-gpu")
        op.add_argument("--disable-infobars")
        op.add_argument("--disable-dev-shm-usage")
        op.add_argument(f'user-agent={user_agent}')
        op.add_experimental_option("prefs", {
            "download.default_directory": absolute_path,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        # op.add_argument(f'--proxy-server={proxy_url}')

        driver = webdriver.Chrome(seleniumwire_options=seleniumwire_options, options=op)
        # driver = webdriver.Chrome(options=op)

        driver.get('https://equatorialgoias.com.br/LoginGO.aspx')
    except Exception as e:
        logging.error(str(e))
        if return_msg:
            producer_result(create_result_obj(
                req.correlation_id,
                '101',
                'Site indisponível.',
                str(e))
            )
            receiver.complete_message(message)
        return False

    time.sleep(3)

    try:
        driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtUC').send_keys(req.uc)
        driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtDocumento').send_keys(req.documento)
        driver.find_element(by=By.XPATH, value='//*[@id="WEBDOOR_headercorporativogo_divLogin"]/div[2]/button').click()
        time.sleep(3)
    except Exception as e:
        driver.quit()
        logging.error(str(e))
        if hasattr(e, 'alert_text'):
            msg = e.alert_text
        else:
            msg = 'Erro ao realizar o login.'
        if return_msg:
            producer_result(create_result_obj(req.correlation_id, '101', msg, str(e)))
            receiver.complete_message(message)
        return False

    if len(req.documento) < 12:
        try:
            time.sleep(3)
            driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_txtData').send_keys(req.data_nascimento)
            driver.find_element(by=By.ID, value='WEBDOOR_headercorporativogo_btnValidar').click()
            time.sleep(3)
        except Exception as e:
            driver.quit()
            logging.error(str(e))
            if hasattr(e, 'alert_text'):
                msg = e.alert_text
            else:
                msg = 'Erro inesperado ao inserir a data, por favor tente novamente.'
            if return_msg:
                producer_result(create_result_obj(req.correlation_id, '102', msg, str(e)))
                receiver.complete_message(message)
            return False

    if select_options(driver, req, return_msg, receiver, message) is False:
        return False

    try:
        boletos = driver.find_elements(by=By.XPATH, value='//*[@id="ContentPage"]/div[3]/div/table/thead/tr/td[2]/a')
        if len(boletos) > 1:
            for i in range(len(boletos)):
                if i == 0:
                    boletos[0].click()
                    time.sleep(3)
                    driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
                    time.sleep(3)
                else:
                    select_options(driver, req, return_msg, receiver, message)
                    novos_boletos = driver.find_elements(by=By.XPATH,
                                                         value='//*[@id="ContentPage"]/div[3]/div/table/thead/tr/td[2]/a')
                    novos_boletos[i].click()
                    time.sleep(3)
                    driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
                    time.sleep(3)
        elif len(boletos) == 1:
            boletos[0].click()
            time.sleep(3)
            driver.find_element(by=By.ID, value='CONTENT_btnModal').click()
            time.sleep(3)
        else:
            msg = 'Não há boleto disponível para download.'
            producer_result(create_result_obj(req.correlation_id, '103', msg))
            receiver.complete_message(message)
            return False

    except Exception as e:
        driver.quit()
        logging.error(str(e))
        if hasattr(e, 'alert_text'):
            msg = {e.alert_text}
        else:
            msg = 'Erro fazer download do boleto.'
        if return_msg:
            producer_result(create_result_obj(req.correlation_id, '104', msg, str(e)))
            receiver.complete_message(message)
        return False

    driver.quit()
    return True


def select_options(driver, req, return_msg, receiver, message):
    try:
        time.sleep(5)
        driver.get('https://goias.equatorialenergia.com.br/AgenciaGO/Servi%C3%A7os/aberto/SegundaVia.aspx')
        time.sleep(3)
        driver.find_element(by=By.XPATH, value='//*[@id="CONTENT_cbTipoEmissao"]/option[2]').click()
        driver.find_element(by=By.XPATH, value='//*[@id="CONTENT_cbMotivo"]/option[7]').click()
        driver.find_element(by=By.ID, value='CONTENT_btEnviar').click()
        time.sleep(3)
    except Exception as e:
        driver.quit()
        logging.error(str(e))
        if hasattr(e, 'alert_text'):
            msg = e.alert_text
        else:
            msg = 'Erro inesperado ao emitir fatura.'
        if return_msg:
            producer_result(create_result_obj(req.correlation_id, '105', msg, str(e)))
            receiver.complete_message(message)
        return False


def verify_path_and_files():
    if not os.path.exists('temp'):
        os.makedirs('temp')
        print("Directory created successfully!")
    else:
        print("Directory already exists!")
    for file in [f for f in listdir('temp') if isfile(join('temp', f))]:
        os.remove(f'temp/{file}')
