from io import StringIO
import pandas as pd
from flask import Flask, request, jsonify

app = Flask(__name__)


class ETFManager:
    def __init__(self):
        self.etf_holdings_dict = {}

    def process_csv(self, file):
        file_content = file.read().decode('utf-8')
        lines = file_content.split('\n')
        start_of_data = self._find_start_of_data(lines)
        csv_data = '\n'.join(lines[start_of_data:])
        data_frame = pd.read_csv(StringIO(csv_data))
        self._process_weight(data_frame)
        etf_holdings = data_frame.set_index('CUSIP')['WEIGHT'].to_dict()
        return etf_holdings

    def _find_start_of_data(self, lines):
        for i, line in enumerate(lines):
            if line.startswith('ISSUER,CUSIP'):
                return i
        raise ValueError("Data header not found in the file")

    def _process_weight(self, data_frame):
        data_frame['WEIGHT'] = data_frame['WEIGHT'].str.rstrip('%')
        data_frame['WEIGHT'] = pd.to_numeric(data_frame['WEIGHT'], errors='coerce') / 100.0

    def add_etf_holdings_from_csv(self, file, cusip):
        etf_holdings = self.process_csv(file)
        self.etf_holdings_dict[cusip] = etf_holdings

    def calculate_portfolio(self, etf_data_map):
        portfolio_value, stock_values = self._calculate_portfolio_and_stock_values(etf_data_map)
        return self._calculate_stock_percentages(portfolio_value, stock_values)

    def _calculate_portfolio_and_stock_values(self, etf_data_map):
        portfolio_value = 0
        stock_values = {}
        for etf_code, investment_details in etf_data_map.items():
            etf_value = investment_details['price'] * investment_details['shares']
            portfolio_value += etf_value
            for stock, weight in self.etf_holdings_dict[etf_code].items():
                if stock not in stock_values:
                    stock_values[stock] = 0
                stock_values[stock] += etf_value * weight
        return portfolio_value, stock_values

    def _calculate_stock_percentages(self, portfolio_value, stock_values):
        stock_percentages = {stock: value / portfolio_value * 100 for stock, value in stock_values.items()}
        return sorted(stock_percentages.items(), key=lambda item: item[1], reverse=True)


etf_manager = ETFManager()


@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    cusip = request.form['cusip']
    etf_manager.add_etf_holdings_from_csv(file, cusip)
    return jsonify({"message": "File uploaded and processed successfully"})


@app.route('/calculate-portfolio', methods=['POST'])
def calculate_portfolio():
    etf_data_map = request.json
    sorted_stock_values = etf_manager.calculate_portfolio(etf_data_map)
    return jsonify(sorted_stock_values)


if __name__ == '__main__':
    app.run()
