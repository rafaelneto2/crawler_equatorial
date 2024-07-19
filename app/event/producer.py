import os

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from dotenv import load_dotenv

from app.squema.schema import ResponseSchema, ErrorDetails

load_dotenv()

conn_str = os.getenv('CONNECTION_STR')
queue_producer = os.getenv('QUEUE_NAME_PRODUCER')


def send_single_message(sender, msg):
    message = ServiceBusMessage(msg)
    sender.send_messages(message)
    print("Mensagem enviada com sucesso: {}".format(msg))


def producer(msg: str):
    with ServiceBusClient.from_connection_string(
            conn_str=conn_str,
            logging_enable=True) as servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=queue_producer)
        with sender:
            send_single_message(sender, msg)


def create_result_obj(
        correlation_id,
        status_code: str,
        msg: str,
        stack_trace: str = None
):
    error = ErrorDetails(
        code=status_code,
        message=msg,
        detail=stack_trace
    )
    return ResponseSchema(
        correlation_id=correlation_id,
        success=False,
        error=error,
        data=None
    ).model_dump_json()
