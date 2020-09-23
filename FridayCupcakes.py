import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import datetime
from generate_bills import generate_bills

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/spreadsheets']
ORDERS_SHEET_ID = '1tDdoexzEMvBmHiFFPs9nl_UO92kfa7amWEgoyeeLWCI'

recipes = {
    'maracujá': {
        'farinha': 14.595, 'açúcar': 17.764, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625,
        'chocolate branco': 29.19, 'creme de leite': 1.901, 'maracujá': 0.083
        },
    'limão': {
        'farinha': 14.595, 'açúcar': 14.595, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625,
        'leite condensado': 7.005, 'creme de leite': 3.544, 'limão': 0.145, 'margarina': 4.587,
        'açúcar de confeiteiro': 16.68
        },
    'churros': {
        'farinha': 14.595, 'açúcar': 14.595, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625,
        'canela': 0.2, 'leite condensado lata': 32.916
        },
    'brigadeiro': {
        'farinha': 14.595, 'açúcar': 17.764, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625,
        'chantilly': 8.333, 'chocolate em pó': 1.25, 'leite condensado': 16.471, 'creme de leite': 8.34,
        'chocolate meio amargo': 2.502, 'chocolate ao leite': 1.668, 'margarina': 0.667
        }
}

def main():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    #Call the sheets API for orders and stock
    sheet = sheets_service.spreadsheets()
    orders_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='A2:G24',
        majorDimension='COLUMNS').execute()
    orders = orders_result.get('values', [])

    stock_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='K2:L23',
        majorDimension='COLUMNS').execute()
    stock = stock_result.get('values', [])

    #Converting data obtained to dataframes
    labels = ['Cliente', 'Maracujá', 'Limão', 'Churros', 'Brigadeiro', 'PedirEndereço']
    orders_df = pd.DataFrame(columns=labels)
    for i in range(len(labels)):
        if i != 0 and i != 5:
            orders_df[labels[i]] = pd.Series(orders[i], dtype=int)
        else:
            orders_df[labels[i]] = pd.Series(orders[i], dtype=str)
    orders_df = orders_df.fillna(int(0))
    
    stock_df = pd.DataFrame()
    stock_df['Ingrediente'] = pd.Series(stock[0], dtype=str)
    stock_df['Qty'] = pd.Series(stock[1], dtype=int)
    stock_df = stock_df.fillna(0)

    #Analisando pedidos
    print(generate_bills(orders_df))

if __name__ == '__main__':
    main()