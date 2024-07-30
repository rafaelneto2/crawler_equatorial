import logging
import os
import time

from azure.servicebus import ServiceBusClient
from dotenv import load_dotenv

from event.producer import producer_result, create_result_obj
from squema.schema import RequestSchema
from useCase.fileUseCase import get_infos
from useCase.scrapyUseCase import verify_path_and_files, download_boleto

load_dotenv()

conn_str = os.getenv('CONNECTION_STR')
queue_consumer = os.getenv('QUEUE_NAME_CONSUMER')
queue_producer = os.getenv('QUEUE_NAME_PRODUCER')


def main():
    with ServiceBusClient.from_connection_string(
            conn_str=conn_str,
            logging_enable=True) as servicebus_client:

        receiver = servicebus_client.get_queue_receiver(queue_name=queue_consumer, max_wait_time=5)

        with receiver:
            for msg in receiver:
                print("Mensagem recebida: " + str(msg))
                return_msg = True if msg.delivery_count >= 9 else False

                try:
                    req = RequestSchema.parse_raw(str(msg))
                except Exception as e:
                    producer_result(create_result_obj(
                        None,
                        '107',
                        'Erro ao traduzir mensagem.',
                        str(e))
                    )
                    continue

                verify_path_and_files()
                if download_boleto(req, receiver, msg, return_msg) and get_infos(req, return_msg, receiver, msg):
                # if get_infos(req, return_msg, receiver, msg):
                    receiver.complete_message(msg)


while True:
    time.sleep(1)
    try:
        main()
    except Exception as e:
        logging.error(str(e))
        pass
