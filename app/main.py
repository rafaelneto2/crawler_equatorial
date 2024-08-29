import logging
import os
import time

import requests
from azure.servicebus import ServiceBusClient
from dotenv import load_dotenv

from event.producer import producer_result, create_result_obj
from squema.schema import GetInfoBoleto
from useCase.fileUseCase import get_infos, verify_path_and_files

load_dotenv()

conn_str = os.getenv('CONNECTION_STR')
queue_consumer = os.getenv('QUEUE_NAME_CONSUMER')
queue_consumer_get_info = os.getenv('QUEUE_NAME_CONSUMER_GET_INFO')


def main_get_info():
    with ServiceBusClient.from_connection_string(
            conn_str=conn_str,
            logging_enable=True) as servicebus_client:

        receiver = servicebus_client.get_queue_receiver(queue_name=queue_consumer_get_info, max_wait_time=5)

        with receiver:
            for msg in receiver:
                print("Mensagem recebida: " + str(msg))

                try:
                    req = GetInfoBoleto.parse_raw(str(msg))
                except Exception as e:
                    producer_result(create_result_obj(
                        None,
                        '107',
                        'Erro ao traduzir mensagem.',
                        str(e))
                    )
                    continue

                verify_path_and_files('temp_get_info')

                try:
                    response = requests.get(req.file_url)
                    if response.status_code == 200:
                        with open(f'temp_get_info/{req.correlation_id}.pdf', 'wb') as f:
                            f.write(response.content)
                        print('Download concluído com sucesso!')
                    else:
                        print(f'Falha no download. Status code: {response.status_code}')
                        # receiver.complete_message(msg)
                        continue
                except:
                    print(f'Falha ao entrar no link: {req.file_url}')
                    continue

                if get_infos(req=req, receiver=receiver, message=msg, dir='temp_get_info'):
                    receiver.complete_message(msg)


while True:
    time.sleep(1)
    try:
        main_get_info()
    except Exception as e:
        logging.error(str(e))
        pass
