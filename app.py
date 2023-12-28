import os
from flask import Flask, request, jsonify, session
from flask.sessions import SecureCookieSessionInterface
from flask_cors import CORS
from itsdangerous import URLSafeTimedSerializer
from io import StringIO
import pandas as pd

app = Flask(__name__)
CORS(app)

# Set the secret key. Keep this really secret!
app.secret_key = os.environ.get('SECRET_KEY')

# Key not set in environment scenarios.
if not app.secret_key:
    raise ValueError("SECRET_KEY is not set in the environment variables. Secure your app.")

# Initialize session interface
session_interface = SecureCookieSessionInterface()
session_serializer = URLSafeTimedSerializer(app.secret_key)


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

    @staticmethod
    def _find_start_of_data(lines):
        for i, line in enumerate(lines):
            if line.startswith('ISSUER,CUSIP'):
                return i
        raise ValueError("Data header not found in the file")

    @staticmethod
    def _process_weight(data_frame):
        data_frame['WEIGHT'] = data_frame['WEIGHT'].str.rstrip('%')
        data_frame['WEIGHT'] = pd.to_numeric(data_frame['WEIGHT'], errors='coerce') / 100.0

    def get_session_data(self):
        session_id = session.get('id')
        if not session_id:
            session_id = session_serializer.dumps(dict())
            session['id'] = session_id
        return self.etf_holdings_dict.setdefault(session_id, {})

    def add_etf_holdings_from_csv(self, file, cusip):
        etf_holdings = self.process_csv(file)
        self.get_session_data()[cusip] = etf_holdings

    def calculate_portfolio(self, etf_data_map):
        session_data = self.get_session_data()
        portfolio_value, stock_values = self._calculate_portfolio_and_stock_values(etf_data_map, session_data)
        return self._calculate_stock_percentages(portfolio_value, stock_values)

    @staticmethod
    def _calculate_portfolio_and_stock_values(etf_data_map, session_data):
        portfolio_value = 0
        stock_values = {}
        for etf_code, investment_details in etf_data_map.items():
            etf_value = investment_details['price'] * investment_details['shares']
            portfolio_value += etf_value
            for stock, weight in session_data[etf_code].items():
                if stock not in stock_values:
                    stock_values[stock] = 0
                stock_values[stock] += etf_value * weight
        return portfolio_value, stock_values

    @staticmethod
    def _calculate_stock_percentages(portfolio_value, stock_values):
        if portfolio_value == 0:
            return "Portfolio value is zero, cannot calculate percentages"
        stock_percentages = {stock: value / portfolio_value * 100 for stock, value in stock_values.items()}
        return sorted(stock_percentages.items(), key=lambda item: item[1], reverse=True)


etf_manager = ETFManager()


@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    file = request.files.get('file')
    if file is None or file.filename == '':
        return jsonify({"message": "No file provided"}), 400
    cusip = request.form.get('cusip')
    if cusip is None or len(cusip.strip()) == 0:
        return jsonify({"message": "No cusip provided"}), 400
    # If inputs are valid
    etf_manager.add_etf_holdings_from_csv(file, cusip)
    return jsonify({"message": "File uploaded and processed successfully"})


@app.route('/calculate-portfolio', methods=['POST'])
def calculate_portfolio():
    etf_data_map = request.json
    sorted_stock_values = etf_manager.calculate_portfolio(etf_data_map)
    return jsonify(sorted_stock_values)


if __name__ == '__main__':
    app.run()
