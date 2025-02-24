import pickle
import os.path
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import datetime
from math import ceil
import warnings
from dotenv import load_dotenv

#Carregando variáveis de ambiente
load_dotenv()
ORDERS_SHEET_ID = os.environ.get("ORDERS_SHEET_ID")
PARENT_FOLDER_ID = os.environ.get("PARENT_FOLDER_ID")

#Módulos particulares
from generate_bills import generate_bills
from generate_helper import generate_helper

#Requisitando que o script ignore o FutureWarning do numpy
warnings.simplefilter(action='ignore', category=FutureWarning)

# Definição de escopos necessários do Google Cloud
# Se forem modificados deletar o arquivo PICKLE
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

def create_drive_file(name, path, parent_id, drive_service):
    metadata = {'name': name, 'parents': [parent_id]}
    media = MediaFileUpload(path)
    file = drive_service.files().create(
        body=metadata,
        media_body=media,
        fields='id').execute()
    return file

def main():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    print("Acessando informações do drive.")
    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    #Chamar a Sheets API para pegar as informações de pedidos e estoque
    sheet = sheets_service.spreadsheets()
    orders_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='A2:G24',
        majorDimension='COLUMNS').execute()
    orders = orders_result.get('values', [])

    extra_flavor_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='F1',
    ).execute()
    extra_flavor = extra_flavor_result.get('values', [])[0][0]

    stock_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='K2:M22',
        majorDimension='COLUMNS').execute()
    stock = stock_result.get('values', [])

    #Convertendo dados para DataFrames
    labels = ['Cliente', 'Maracujá', 'Limão', 'Churros', 'Brigadeiro', extra_flavor, 'PedirEndereço']
    orders_df = pd.DataFrame(columns=labels)
    for i in range(len(labels)):
        if i != 0 and i != len(labels) - 1:
            orders_df[labels[i]] = pd.Series(orders[i], dtype=int)
        else:
            orders_df[labels[i]] = pd.Series(orders[i], dtype=str)
    orders_df = orders_df.fillna(int(0))
    
    stock_df = pd.DataFrame()
    stock_df['Ingrediente'] = pd.Series(stock[0], dtype=str)
    stock_df['Qty'] = pd.Series(stock[1], dtype=int)
    stock_df['Qty per Package'] = pd.Series(stock[2], dtype=int)
    stock_df['Needed'] = [float(0)]*len(stock_df.index)
    stock_df = stock_df.set_index('Ingrediente')
    stock_df = stock_df.fillna(0)

    #Analisando pedidos / geração de métricas
    metrics = generate_bills(orders_df, extra_flavor)

    #Gerando o arquivo helper.txt
    generate_helper(orders_df, stock_df, metrics, extra_flavor)

    #Chamando a Drive API para atualizar as informações
    needed_files = {
        'helper.txt': '', 
        'orders.txt': ''
        }

    for path in needed_files.keys():
        response = drive_service.files().list(
                                            q="name='{}'".format(path),
                                            spaces='drive',
                                            fields='files(id)').execute()
        if len(response['files']) == 0:
            print("Criando o arquivo {} no drive.".format(path))
            response = create_drive_file(path, "./" + path, PARENT_FOLDER_ID, drive_service)
            needed_files[path] = response['id']
        else:
            needed_files[path] = response['files'][0]['id']

        media = MediaFileUpload("./" + path)
        file = drive_service.files().update(
                                        media_body=media,
                                        fileId=needed_files[path],
                                        fields='id').execute()

    print("Informações salvas no drive com sucesso.")

if __name__ == '__main__':
    main()