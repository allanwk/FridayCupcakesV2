import pandas as pd
import datetime
from math import ceil

box_cost = 0.36

def generate_bills(df, extra_flavor):
    """Generates a text file containing the order confirmations (bills) of each costumer,
    and also calculates finnancial metrics, returning those in the form a dictonary.
    For this it requires a DataFrame with the orders.
    """

    box_prices = {'2x': 0.27, '5x': 0.36}
    boxes = {'2x': 0, '5x': 0}
    spacers = 0
    total = 0
    cost = 0
    numCupcakes = 0

    flavors = ["Maracujá", "Limão", "Churros", "Brigadeiro", extra_flavor]
    info = pd.DataFrame({'flavor': ["Maracujá", "Limão", "Churros", "Brigadeiro", extra_flavor],
                        'perCupcake': [1.24, 0.61, 0.63, 0.83, 1]})
    info = info.set_index('flavor')

    order_confirmations = open("orders.txt", "w+", encoding='UTF-8')
    order_confirmations.write(("\n▬▬▬▬▬▬▬▬▬▬▬▬▬" + str(datetime.date.today()) + "▬▬▬▬▬▬▬▬▬▬▬▬▬\n"))

    for index, row in df.iterrows():
        order_confirmations.write("\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n")
        sum = int(row["Maracujá"]) + int(row["Limão"]) + int(row["Churros"]) + int(row["Brigadeiro"]) + int(row[extra_flavor])
        price = sum*2.5
        if (sum > 5):
            price*=0.95
        elif (sum == 5):
            price = 12.00
        if sum <= 2:
            boxes['2x'] += 1
            cost += box_prices['2x']
            spacers += sum % 2
        else:
            boxes_num = ceil(sum/5)
            boxes['5x'] += boxes_num
            cost += boxes_num*box_prices['5x']
            spacers += sum % 5
        total += price
        numCupcakes += sum

        order_confirmations.write("\n" + row["Cliente"] + "\n")
        order_confirmations.write("Oie, a hora das entregas está chegando!\n\n")
        order_confirmations.write("Vamos conferir seu pedido:\n")
        for flavor in flavors:
            cost += row[flavor] * info.at[flavor, "perCupcake"]
            if row[flavor] == 1:
                order_confirmations.write("1 cupcake de {} - R$2.50\n".format(flavor))
            elif row[flavor] > 1:
                order_confirmations.write("{:d} cupcakes de {} - R${:.2f}\n".format(row[flavor], flavor, round(2.5*row[flavor], 2)))
        if sum >= 5:
            order_confirmations.write("\nTotal com desconto aplicado: R${:.2f}\n".format(round(price,2)))
        else:
            order_confirmations.write("\nTotal: R${:.2f}\n".format(round(price, 2)))
        order_confirmations.write("(apenas em dinheiro ou transferência)\n\nVocê vai estar em casa a partir das 16h30 hoje para nós entregarmos?\n")
        if row["PedirEndereço"] == "S":
            order_confirmations.write("Além disso, em que endereço você deseja que entreguemos?\n")

    order_confirmations.close()
    print("Mensagens de confirmação geradas com sucesso")

    profit = total - cost
    return {
        'Cost': round(cost, 2), 
        'Income': round(total, 2),
        'Profit': round(profit, 2),
        'CupcakesSold': numCupcakes,
        'ProfitPerCupcake': round(profit/numCupcakes, 2),
        'Boxes': boxes,
        'Spacers': spacers
    }