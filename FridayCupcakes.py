import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import datetime
from generate_bills import generate_bills
from math import ceil
import warnings

#Requisitando que o script ignore o FutureWarning do numpy
warnings.simplefilter(action='ignore', category=FutureWarning)

# Definição de escopos necessários do Google Cloud
# Se forem modificados deletar o arquivo PICKLE
SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly', 'https://www.googleapis.com/auth/spreadsheets']
ORDERS_SHEET_ID = '1tDdoexzEMvBmHiFFPs9nl_UO92kfa7amWEgoyeeLWCI'

#Informações sobre as receitas para calcular os ingredientes usados.
#A maioria dos valores está em gramas.
recipes = {
    'Maracujá': {
        'farinha': 14.595, 'açúcar': 17.764, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625, 'forminha': 1,
        'chocolate branco': 29.19, 'creme de leite': 1.901, 'maracujá': 0.083
        },
    'Limão': {
        'farinha': 14.595, 'açúcar': 14.595, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625, 'forminha': 1,
        'leite condensado': 7.005, 'creme de leite': 3.544, 'limão': 0.145, 'margarina': 4.587,
        'açúcar de confeiteiro': 16.68
        },
    'Churros': {
        'farinha': 14.595, 'açúcar': 14.595, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625, 'forminha': 1,
        'canela': 0.2, 'leite condensado lata': 32.916
        },
    'Brigadeiro': {
        'farinha': 14.595, 'açúcar': 17.764, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625, 'forminha': 1,
        'chantilly': 8.333, 'chocolate em pó': 1.25, 'leite condensado': 16.471, 'creme de leite': 8.34,
        'chocolate meio amargo': 2.502, 'chocolate ao leite': 1.668, 'margarina': 0.667
        }
}

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

    drive_service = build('drive', 'v3', credentials=creds)
    sheets_service = build('sheets', 'v4', credentials=creds)

    #Chamar a Sheets API para pegar as informações de pedidos e estoque
    sheet = sheets_service.spreadsheets()
    orders_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='A2:G24',
        majorDimension='COLUMNS').execute()
    orders = orders_result.get('values', [])

    stock_result = sheet.values().get(
        spreadsheetId=ORDERS_SHEET_ID,
        range='K2:M21',
        majorDimension='COLUMNS').execute()
    stock = stock_result.get('values', [])

    #Convertendo dados para DataFrames
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
    stock_df['Qty per Package'] = pd.Series(stock[2], dtype=int)
    stock_df['Needed'] = [float(0)]*len(stock_df.index)
    stock_df = stock_df.set_index('Ingrediente')
    stock_df = stock_df.fillna(0)

    #Analisando pedidos / geração de métricas
    metrcis = generate_bills(orders_df)

    #Calculando ingredientes utilizados
    qtys = {
        'Maracujá': orders_df['Maracujá'].sum(),
        'Limão': orders_df['Limão'].sum(),
        'Churros': orders_df['Churros'].sum(),
        'Brigadeiro': orders_df['Brigadeiro'].sum(),
    }
    for flavor, quantity in qtys.items():
        for ingredient, qty in recipes[flavor].items():
            stock_df.at[ingredient, "Needed"] = round(qty * quantity, 2)

    #Gerando lista de compras
    helper = open("helper.txt", "w+", encoding="UTF-8")
    helper.write(("▬▬▬▬▬▬▬▬▬▬▬▬▬" + str(datetime.date.today()) + "▬▬▬▬▬▬▬▬▬▬▬▬▬\n"))
    for index, row in stock_df.iterrows():

        #Quando a quantidade por embalagem é 0, significa que é um ingrediente medido
        #em unidades (ovos, maraujá ou limão)

        ignore = ["ovos"]
        buy_qty = 0
        if index in ignore:
            continue
        if int(row["Qty per Package"]) == 0:
            buy_qty = ceil((row["Needed"] - row["Qty"]))
        elif (row["Needed"] >= row["Qty"] or row["Qty"] <= 11):
            buy_qty = ceil((row["Needed"] - row["Qty"]) / row["Qty per Package"])
        if buy_qty != 0:
            helper.write("{} x{}\n".format(index, buy_qty))
    
    helper.write("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")

    #Informações adicionais sobre as fornadas necessárias
    regular_batter = int(qtys["Maracujá"] + qtys["Limão"] + qtys["Brigadeiro"])
    cinnamon_batter = int(qtys["Churros"])
    regular_batches = ceil(regular_batter / 12)
    cinnamon_batches = ceil(cinnamon_batter / 12)
    time = datetime.time(minute=((regular_batches+cinnamon_batches)*27))

    helper.write("Massas comuns: {}\nMassas com canela: {}\n".format(regular_batter, cinnamon_batter))
    helper.write("Fornadas comuns: {}\nFornadas com canela: {}\n".format(regular_batches, cinnamon_batches))
    helper.write("Tempo estimado (melhor caso): {}\n".format(str(time)))
    helper.write("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")
    helper.close()
    print("Arquivo informativo criado com sucesso.")

if __name__ == '__main__':
    main()