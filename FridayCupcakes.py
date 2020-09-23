import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/spreadsheets']

ORDERS_SHEET_ID = '1tDdoexzEMvBmHiFFPs9nl_UO92kfa7amWEgoyeeLWCI'

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
    orders_df = pd.DataFrame()
    labels = ['Cliente', 'Maracujá', 'Limão', 'Churros', 'Brigadeiro', 'PedirEndereço']
    for i in range(len(labels)):
        orders_df[labels[i]] = pd.Series(orders[i])
    orders_df = orders_df.fillna(0)

    stock_df = pd.DataFrame()
    stock_df['Ingrediente'] = pd.Series(stock[0], dtype=str)
    stock_df['Qty'] = pd.Series(stock[1], dtype=int)
    stock_df = stock_df.fillna(0)

if __name__ == '__main__':
    main()