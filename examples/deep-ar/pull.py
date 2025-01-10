# write a script that will use the yfinance library to get stock prices for a given stock symbol
import sys
import os
import yfinance as yf

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from common.aws_utils import create_bucket, upload_data, create_role


def get_stock_price(stock_symbol):
    stock = yf.Ticker(stock_symbol)
    hist = stock.history(period="5d")
    return hist


# load it into an s3 bucket
def save_stock_price(stock_symbol, training_path):
    stock = yf.Ticker(stock_symbol)
    hist = stock.history(period="5d")
    hist.to_csv(training_path, header=False)
    return hist


def main():
    stock_symbol = "AAPL"
    bucket_name = "stock-86589a88-8765-41e7-9019-865601"
    create_bucket(bucket_name)

    training_path = f"{stock_symbol}.csv"

    save_stock_price(stock_symbol, training_path)

    with open(training_path, "rb") as f:
        data = f.read().decode("utf-8")
    upload_data(bucket_name, training_path, data)


if __name__ == "__main__":
    main()
