import logging
import os
from os import listdir
from os.path import isfile, join

from fastapi import HTTPException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from pypdf import PdfReader

from app_v2.squema.schema import RequestSchema, ResponseSchema, BaseEnergia

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = "equatorial-credentials.json"
ID_FOLDER_EQUATORIAL = "1TX79sj4OvbZJIDNSZtHbxxIRwuSG074t"

credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)


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

