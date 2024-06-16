import asyncio
import time
import json

from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from azure.identity.aio import DefaultAzureCredential

from squema.schema import RequestSchema, ResponseSchema
from useCase.scrapyUseCase import download_boleto, verify_path_and_files

from useCase.fileUseCase import get_infos

CONNECTION_STR = "Endpoint=sb://rc-energy.servicebus.windows.net/;SharedAccessKeyName=ConnectSendAndListen;SharedAccessKey=juNyQCg3mAG8AnemU2PMF1TXWCGJVlRFB+ASbN0eslY="
QUEUE_NAME_CONSUMER = "customers-to-run"
# QUEUE_NAME_PRODUCER = "run-results"
QUEUE_NAME_PRODUCER = "customers-to-run"

credential = DefaultAzureCredential()


async def send_single_message(sender, msg):
    message = ServiceBusMessage(msg)
    await sender.send_messages(message)
    print("Sent a single message")


async def producer():
    async with ServiceBusClient.from_connection_string(
            conn_str=CONNECTION_STR,
            logging_enable=True) as servicebus_client:

        sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME_PRODUCER)
        async with sender:
            await send_single_message(sender, 'Mensagem Teste!')


async def main():
    async with ServiceBusClient.from_connection_string(
            conn_str=CONNECTION_STR,
            logging_enable=True) as servicebus_client:

        receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME_CONSUMER, max_wait_time=5)
        sender = servicebus_client.get_queue_sender(queue_name=QUEUE_NAME_PRODUCER)

        async with receiver, sender:
            async for msg in receiver:
                print("Mensagem recebida: " + str(msg))
                verify_path_and_files()
                req = RequestSchema.parse_raw(str(msg))
                download_boleto(req)
                resp = get_infos(req)
                await send_single_message(sender, json.dumps(resp))
                await receiver.complete_message(msg)


while True:
    # asyncio.run(producer())
    time.sleep(1)
    asyncio.run(main())
