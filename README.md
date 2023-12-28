# ETFPortfolioManager

ETFPortfolioManager is a Python-based web application that allows users to manage their Exchange Traded Funds (ETFs) and calculate portfolio values. The application is built using Flask, a lightweight WSGI web application framework.

## Features

- Upload ETF holdings data via CSV files.
- Calculate the portfolio value based on the uploaded ETF holdings data.
- The application uses sessions to manage ETF data for each user.

## Installation

1. Clone the repository to your local machine.
2. Install the required dependencies using pip:
    ```
    pip install -r requirements.txt
    ```
3. Set the `SECRET_KEY` environment variable. This is used for session management in Flask.
4. Run the application:
    ```
    python app.py
    ```

## Usage

The application provides two main endpoints:

- `POST /upload-csv`: This endpoint is used to upload a CSV file containing ETF holdings data. The CSV file should be sent as a file in the request body. The `cusip` should be sent as a form data in the request body.

- `POST /calculate-portfolio`: This endpoint is used to calculate the portfolio value. The ETF data map should be sent as JSON in the request body.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.