import os

from azure.servicebus import ServiceBusClient, ServiceBusMessage
from dotenv import load_dotenv

from squema.schema import ResponseSchema, ErrorDetails, UploadSchema

load_dotenv()

conn_str = os.getenv('CONNECTION_STR')
queue_producer_result = os.getenv('QUEUE_NAME_PRODUCER_RESULTS')
queue_producer_upload = os.getenv('QUEUE_NAME_PRODUCER_UPLOAD')


def send_single_message(sender, msg):
    message = ServiceBusMessage(msg)
    sender.send_messages(message)
    print("Mensagem enviada com sucesso: {}".format(msg))


def producer_result(msg: str):
    with ServiceBusClient.from_connection_string(
            conn_str=conn_str,
            logging_enable=True) as servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=queue_producer_result)
        with sender:
            send_single_message(sender, msg)


def producer_upload(msg: str):
    with ServiceBusClient.from_connection_string(
            conn_str=conn_str,
            logging_enable=True) as servicebus_client:
        sender = servicebus_client.get_queue_sender(queue_name=queue_producer_upload)
        with sender:
            send_single_message(sender, msg)


def create_upload_obj(
        correlation_id: str,
        file_path: str,
        conta_mes: str
):
    return UploadSchema(
        correlation_id=correlation_id,
        file=file_path,
        conta_mes=conta_mes
    ).model_dump_json()


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
