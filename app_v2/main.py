import asyncio
import json
import os
import time

from azure.servicebus import ServiceBusClient
from dotenv import load_dotenv

from squema.schema import RequestSchema
from useCase.fileUseCase import get_infos
from useCase.scrapyUseCase import download_boleto, verify_path_and_files
from event.producer import producer, create_result_obj

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
                # receiver.complete_message(msg)

                try:
                    req = RequestSchema.parse_raw(str(msg))
                except Exception as e:
                    producer(create_result_obj(
                        None,
                        '107',
                        'Erro ao traduzir mensagem.',
                        str(e))
                    )
                    continue

                verify_path_and_files()
                if download_boleto(req, receiver, msg) and get_infos(req):
                # if get_infos(req):
                    receiver.complete_message(msg)


while True:
    time.sleep(1)
    main()
