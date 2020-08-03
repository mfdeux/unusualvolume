import json
import os
from ftplib import FTP
import typing

# Location of package-included ticker symbols
DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data')
TICKER_FILE = os.path.join(DATA_DIR, 'tickers.json')


def download_tickers():
    """
    Download stock ticker symbols from NASDAQ website

    Returns:

    """
    filenames = ["otherlisted.txt", "nasdaqlisted.txt"]

    ftp = FTP("ftp.nasdaqtrader.com")
    ftp.login()
    ftp.cwd("SymbolDirectory")

    tickers = []

    for filename in filenames:
        lines = []
        ftp.retrlines(f'RETR {filename}', lines.append)

        for line in lines[1:]:
            line_split = line.strip().split("|")
            if line_split[0] == "" or line_split[1] == "" or (
                    filename == 'nasdaqlisted.txt' and line_split[6] == 'Y') or (
                    filename == 'otherlisted.txt' and line_split[4] == 'Y'):
                continue

            tickers.append({'symbol': line_split[0], 'name': line_split[1],
                            'exchange': 'other' if filename == 'otherlisted.txt' else 'nasdaq'})

        # with open(os.path.join(DATA_DIR, filename), 'wb') as fp:
        #     ftp.retrbinary(f'RETR {filename}', fp.write)

    with open(TICKER_FILE, 'w') as fw:
        json.dump(tickers, fw)


def load_tickers() -> typing.List[typing.Dict]:
    """
    Loads list of user agents
    Args:
        filepath: path to user agent file

    Returns:
        List of user agents

    """
    user_agents = []

    with open(TICKER_FILE) as f:
        tickers = json.load(f)

    return tickers