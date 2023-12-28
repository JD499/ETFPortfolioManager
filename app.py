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

    def add_etf_holdings_from_csv(self, file, cusip):
        etf_holdings = self.process_csv(file)
        self.etf_holdings_dict[cusip] = etf_holdings

    def calculate_portfolio(self, etf_info):
        portfolio_value = 0
        stock_values = {}
        for etf, info in etf_info.items():
            etf_value = info['price'] * info['shares']
            portfolio_value += etf_value
            for stock, weight in self.etf_holdings_dict[etf].items():
                if stock not in stock_values:
                    stock_values[stock] = 0
                stock_values[stock] += etf_value * weight
        stock_percentages = {stock: value / portfolio_value * 100 for stock, value in stock_values.items()}
        sorted_stock_values = sorted(stock_percentages.items(), key=lambda item: item[1], reverse=True)
        return sorted_stock_values


etf_manager = ETFManager()


@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    file = request.files['file']
    cusip = request.form['cusip']
    etf_manager.add_etf_holdings_from_csv(file, cusip)
    return jsonify({"message": "File uploaded and processed successfully"})


@app.route('/calculate-portfolio', methods=['POST'])
def calculate_portfolio():
    etf_info = request.json
    sorted_stock_values = etf_manager.calculate_portfolio(etf_info)
    return jsonify(sorted_stock_values)


if __name__ == '__main__':
    app.run()
