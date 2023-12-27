from flask import Flask

app = Flask(__name__)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

import pandas as pd

def add_etf_holdings_from_csv(etf_holdings_dict, file_path):
    # Read the file to find the ETF name
    with open(file_path, 'r') as file:
        lines = file.readlines()
        etf_name_line = [line for line in lines if line.startswith('Fund Name')][0]
        etf_name = etf_name_line.split(',')[1].strip()

    # Find the start of the data
    start_of_data = None
    for i, line in enumerate(lines):
        if line.startswith('ISSUER,CUSIP'):
            start_of_data = i
            break

    if start_of_data is None:
        raise ValueError("Data header not found in the file")

    # Read the holdings data
    holdings_df = pd.read_csv(file_path, skiprows=start_of_data)
    holdings_df['WEIGHT'] = pd.to_numeric(holdings_df['WEIGHT'].str.rstrip('%'), errors='coerce') / 100.0

    # Create the dictionary for this ETF
    etf_holdings = {}
    for _, row in holdings_df.iterrows():
        stock_name = row['ISSUER']
        stock_weight = row['WEIGHT']
        etf_holdings[stock_name] = stock_weight

    # Add the dictionary to the existing holdings
    etf_holdings_dict[etf_name] = etf_holdings

# Usage example
etf_holdings_dict = {}  # Initialize an empty dictionary
add_etf_holdings_from_csv(etf_holdings_dict, 'AVRE.csv')
add_etf_holdings_from_csv(etf_holdings_dict, 'AVUS.csv')
add_etf_holdings_from_csv(etf_holdings_dict, 'AVUV.csv')

print(etf_holdings_dict)

def calculate_etf_portfolio(etf_info, stock_weights):
    """
    Calculate the value of individual stocks in a portfolio of ETFs.

    :param etf_info: A dictionary containing the price and shares of each ETF.
                     For example: {'ETF One': {'price': 50, 'shares': 2}, 'ETF Two': {'price': 100, 'shares': 1}}
    :param stock_weights: A dictionary of dictionaries containing the weights of stocks in each ETF.
                          For example: {'ETF One': {'AAPL': 0.8, 'MSFT': 0.2}, 'ETF Two': {'AAPL': 0.25, 'MSFT': 0.25, 'TSLA': 0.25, 'AMZN': 0.25}}
    :return: A sorted list of tuples with stock names and their percentage of the total portfolio value.
    """
    # Initialize the portfolio value and stock values
    portfolio_value = 0
    stock_values = {}

    # Calculate the value of each ETF and add it to the total portfolio value
    for etf, info in etf_info.items():
        etf_value = info['price'] * info['shares']
        portfolio_value += etf_value

        # For each stock in the ETF, calculate its value based on the ETF value and weight
        for stock, weight in stock_weights[etf].items():
            if stock not in stock_values:
                stock_values[stock] = 0
            stock_values[stock] += etf_value * weight

    # Calculate the percentage of each stock's value in relation to the total portfolio value
    stock_percentages = {stock: value / portfolio_value * 100 for stock, value in stock_values.items()}

    # Sort the stock values by their percentage of the total portfolio value
    sorted_stock_values = sorted(stock_percentages.items(), key=lambda item: item[1], reverse=True)

    return sorted_stock_values

# Example usage:
etf_info_example = {
    'Avantis Real Estate ETF': {'price': 50, 'shares': 2},
    'Avantis U.S. Equity ETF': {'price': 50, 'shares': 2},
    'Avantis U.S. Small Cap Value ETF': {'price': 100, 'shares': 1}
}



# Call the function with the example inputs
temp = calculate_etf_portfolio(etf_info_example, etf_holdings_dict)
print(calculate_etf_portfolio(etf_info_example, etf_holdings_dict))










if __name__ == '__main__':
    app.run()
