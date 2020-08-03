import datetime
import json
import multiprocessing
import os
import sys
import typing

import dateutil.relativedelta
import pandas as pd
import yfinance
from joblib import Parallel, delayed, parallel_backend
from tqdm import tqdm

pd.options.mode.chained_assignment = None


def download_volume_data(ticker: str, month_cutoff: int = 5) -> pd.Series:
    """

    Args:
        ticker:
        month_cutoff:

    Returns:

    """
    current_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    cutoff_date = current_date - \
                  dateutil.relativedelta.relativedelta(months=month_cutoff)

    # Suppress Yahoo! Finance errors by re-directing system standard out
    sys.stdout = open(os.devnull, "w")

    data = yfinance.download(ticker, cutoff_date, current_date, progress=False, threads=False)

    # Replace re-directed system standard out back to normal
    sys.stdout = sys.__stdout__

    return data[["Volume"]]


def find_anomalies(volume_data: pd.Series, std_dev_cutoff: int = 10, days_cutoff: int = 3):
    """

    Args:
        volume_data:
        std_dev_cutoff:

    Returns:

    """
    volume_data.reset_index(level=0, inplace=True)
    volume_data.columns = ['date', 'volume']
    cutoff_date = volume_data["date"].max() - pd.Timedelta(days=days_cutoff)

    data_std_dev = volume_data['volume'].std()
    data_mean = volume_data['volume'].mean()
    anomaly_cut_off = data_mean + data_std_dev * std_dev_cutoff
    anomaly_data = volume_data[volume_data['volume'] > anomaly_cut_off]
    anomaly_data['std_devs'] = (volume_data['volume'] - data_mean) / data_std_dev
    anomaly_data = anomaly_data[anomaly_data['date'] >= cutoff_date]
    # print(anomaly_data['date'].dtype)
    anomaly_data['date'] = anomaly_data['date'].astype(str).str[:10]
    return anomaly_data, data_mean, data_std_dev


def parallel_wrapper(ticker: typing.Dict, months: int, days: int, stddev: int, found_anomalies: typing.List):
    volume_data = download_volume_data(ticker['symbol'], months)
    anomalies, mean, std_dev = find_anomalies(volume_data, stddev, days)

    if not anomalies.empty:
        found_anomalies.append(
            {**ticker, 'url': f"https://finance.yahoo.com/quote/{ticker['symbol']}", 'mean': mean, 'std_dev': std_dev, 'anomalies': json.loads(anomalies.to_json(orient='records'))})


def run_scanner(tickers: typing.List[typing.Dict], months: int, days: int, stddev: int):
    manager = multiprocessing.Manager()
    found_anomalies = manager.list()

    with parallel_backend('loky', n_jobs=multiprocessing.cpu_count()):
        Parallel()(delayed(parallel_wrapper)(ticker, months, days, stddev, found_anomalies)
                   for ticker in tqdm(tickers))

    return found_anomalies


def save_data(data: typing.List[typing.Dict], filename: str):
    """
    Saves scraped profile data to file
    Args:
        data:
        filename:

    Returns:

    """
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(f"{filename}-{now}.json", "w") as f:
        f.write(json.dumps(data))
