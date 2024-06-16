import logging
import os
import time
from os import listdir
from os.path import isfile, join

from fastapi import HTTPException
from selenium.webdriver.common.by import By
from seleniumwire import webdriver


def download_boleto(req):
    absolute_path = os.path.abspath("main.py").replace("main.py", "temp")
    username = "hy1zz0azv0regqx-country-br"
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
        time.sleep(5)
        driver.get('https://equatorialgoias.com.br/AgenciaGO/Servi%C3%A7os/aberto/SegundaVia.aspx')
        time.sleep(3)
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

