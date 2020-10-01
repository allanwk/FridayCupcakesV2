import pandas
import datetime
from math import ceil

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
        },
    'Amora': {
        'farinha': 14.595, 'açúcar': 17.764, 'óleo':11.008, 'ovos': 14.595, 'fermento': 0.625, 'forminha': 1,
        'chantilly': 8.333
        }
}

def generate_helper(orders_df, stock_df, metrics, extra_flavor):
    """Gera o arquivo helper.txt, contendo a lista de compras
    e informações sobre as fornadas necessárias.
    Requer dois DataFrames, um de estoque e outro de pedidos
    """

    #Calculando ingredientes utilizados
    qtys = {
        extra_flavor: orders_df[extra_flavor].sum(),
        'Maracujá': orders_df['Maracujá'].sum(),
        'Limão': orders_df['Limão'].sum(),
        'Churros': orders_df['Churros'].sum(),
        'Brigadeiro': orders_df['Brigadeiro'].sum(),
    }
    for flavor, quantity in qtys.items():
        for ingredient, qty in recipes[flavor].items():
            stock_df.at[ingredient, "Needed"] += round(qty * quantity, 2)

    #Gerando lista de compras
    helper = open("helper.txt", "w+", encoding="UTF-8")
    helper.write(("▬▬▬▬▬▬▬▬▬▬▬▬▬" + str(datetime.date.today()) + "▬▬▬▬▬▬▬▬▬▬▬▬▬\n"))
    print(stock_df)
    for index, row in stock_df.iterrows():

        #Quando a quantidade por embalagem é 0, significa que é um ingrediente medido
        #em unidades (ovos, maraujá ou limão)

        ignore = ["ovos", "caixas", "amoras"]
        buy_qty = 0
        if index in ignore:
            continue
        if int(row["Qty per Package"]) == 0:
            if row["Needed"] >= row["Qty"]:
                buy_qty = ceil((row["Needed"] - row["Qty"]))
        elif (row["Needed"] >= row["Qty"] or row["Qty"] <= 11):
            buy_qty = ceil((row["Needed"] - row["Qty"]) / row["Qty per Package"])
        if buy_qty != 0:
            helper.write("{} x{}\n".format(index, buy_qty))
    
    helper.write("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")

    #Informações sobre as caixas
    helper.write("Caixas usadas (2x): {}\n".format(metrics['Boxes']['2x']))
    helper.write("Caixas usadas (5x): {}\n".format(metrics['Boxes']['5x']))
    helper.write("Espaçadores necessários: {}\n".format(metrics['Spacers']))
    helper.write("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")

    #Informações adicionais sobre as fornadas necessárias
    regular_batter = int(qtys["Maracujá"] + qtys["Limão"] + qtys["Brigadeiro"] + qtys[extra_flavor])
    cinnamon_batter = int(qtys["Churros"])
    regular_batches = ceil(regular_batter / 12)
    cinnamon_batches = ceil(cinnamon_batter / 12)
    #time = datetime.time(minute=((regular_batches+cinnamon_batches)*27))

    helper.write("Massas comuns: {}\nMassas com canela: {}\n".format(regular_batter, cinnamon_batter))
    helper.write("Fornadas comuns: {}\nFornadas com canela: {}\n".format(regular_batches, cinnamon_batches))
    #helper.write("Tempo estimado (melhor caso): {}\n".format(str(time)))
    helper.write("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")

    helper.write("Gastos: R${:.2f}\n".format(metrics['Cost']))
    helper.write("Lucro: R${:.2f}\n".format(metrics['Profit']))
    helper.write("Lucro por cupcake: R${:.2f}\n".format(metrics['ProfitPerCupcake']))
    helper.write("Cupcakes vendidos: {}\n".format(metrics['CupcakesSold']))

    helper.write("▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")

    helper.close()
    print("Arquivo informativo criado com sucesso.")