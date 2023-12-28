from io import StringIO
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/')
def hello_world():
    """
    Returns a greeting message.

    :return: a string containing the message "Hello World!"
    """
    return 'Hello World!'


etf_holdings_dict = {}



def process_csv(file):
    """
    Process a CSV file and extract ETF holdings.

    :param file: The file object representing the CSV file.
    :type file: file-like object
    :return: A dictionary mapping CUSIPs to their corresponding weights in the ETF.
    :rtype: dict
    :raises ValueError: If the data header is not found in the file.
    """
    file_content = file.read().decode('utf-8')
    lines = file_content.split('\n')
    start_of_data = None
    for i, line in enumerate(lines):
        if line.startswith('ISSUER,CUSIP'):
            start_of_data = i
            break
    if start_of_data is None:
        raise ValueError("Data header not found in the file")
    csv_data = '\n'.join(lines[start_of_data:])
    df = pd.read_csv(StringIO(csv_data))
    df['WEIGHT'] = pd.to_numeric(df['WEIGHT'].str.rstrip('%'), errors='coerce') / 100.0
    etf_holdings = df.set_index('CUSIP')['WEIGHT'].to_dict()
    return etf_holdings


def add_etf_holdings_from_csv(etf_holdings_dict, file, cusip):
    """
    Add ETF holdings from a CSV file to the provided dictionary.

    :param etf_holdings_dict: A dictionary to store the ETF holdings.
    :type etf_holdings_dict: dict
    :param file: The path to the CSV file containing the ETF holdings.
    :type file: str
    :param cusip: The CUSIP (Committee on Uniform Securities Identification Procedures) for the ETF.
    :type cusip: str
    :return: None


    This method reads the CSV file, processes it, and adds the ETF holdings to the provided dictionary
    using the specified CUSIP as the key.

    Example:
    >>> etf_holdings_dict = {'ABC123': {'StockA': 100, 'StockB': 150}}
    >>> add_etf_holdings_from_csv(etf_holdings_dict, '/path/to/etf_holdings.csv', 'XYZ456')
    >>> print(etf_holdings_dict)
    {'ABC123': {'StockA': 100, 'StockB': 150}, 'XYZ456': {'StockC': 200, 'StockD': 300}}
    """
    etf_holdings = process_csv(file)
    etf_holdings_dict[cusip] = etf_holdings


@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    """
    Uploads a CSV file and adds ETF holdings to the etf_holdings_dict.

    :return: A JSON response indicating the successful upload and processing of the file.
    """
    file = request.files['file']
    cusip = request.form['cusip']
    add_etf_holdings_from_csv(etf_holdings_dict, file, cusip)
    return jsonify({"message": "File uploaded and processed successfully"})


@app.route('/calculate-portfolio', methods=['POST'])
def calculate_portfolio():
    """
    Calculate portfolio based on the ETF information provided in the request body.

    :return: A JSON response containing the sorted list of tuples containing the CUSIP and their corresponding percentage of the total portfolio value.
    """
    etf_info = request.json
    sorted_stock_values = calculate_etf_portfolio(etf_info, etf_holdings_dict)
    return jsonify(sorted_stock_values)


def calculate_etf_portfolio(etf_info, stock_weights):
    """
    Calculate ETF Portfolio

    :param etf_info: A dictionary containing information about the ETFs in the portfolio.
                      The keys of the dictionary are the ETF names, and the values are dictionaries
                      with keys 'price' and 'shares'. 'price' represents the current price of the ETF,
                      and 'shares' represents the number of shares held in the portfolio.
                      Example: {'etf1': {'price': 100, 'shares': 50}, 'etf2': {'price': 150, 'shares': 30}}

    :param stock_weights: A nested dictionary containing the weightage of each stock in each ETF.
                          The keys of the outer dictionary are the ETF names, and the values are dictionaries
                          with keys as stock names, and corresponding values as the weightage of the stock in that ETF.
                          Example: {'etf1': {'stock1': 0.4, 'stock2': 0.6}, 'etf2': {'stock3': 0.7, 'stock4': 0.3}}

    :return: A sorted list of tuples containing the stock names and their corresponding percentage of the total portfolio value.
             The list is sorted in descending order of stock percentage.
             Example: [('stock2', 50.0), ('stock3', 30.0), ('stock1', 20.0)]
    """
    portfolio_value = 0
    stock_values = {}
    for etf, info in etf_info.items():
        etf_value = info['price'] * info['shares']
        portfolio_value += etf_value
        for stock, weight in stock_weights[etf].items():
            if stock not in stock_values:
                stock_values[stock] = 0
            stock_values[stock] += etf_value * weight
    stock_percentages = {stock: value / portfolio_value * 100 for stock, value in stock_values.items()}
    sorted_stock_values = sorted(stock_percentages.items(), key=lambda item: item[1], reverse=True)
    return sorted_stock_values


if __name__ == '__main__':
    app.run()
