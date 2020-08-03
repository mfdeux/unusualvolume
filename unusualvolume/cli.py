import re
import typing

import click

from .scanner import run_scanner, save_data
from .tickers import download_tickers, load_tickers


def print_result(data: typing.Dict):
    click.echo(click.style(data['symbol'], fg='green', bold=True))
    click.echo(data['name'])
    click.echo(data['url'])
    click.echo(f"Mean: {data['mean']:,.0f} | StdDev: {data['std_dev']:,.0f}")
    for anomaly in data['anomalies']:
        click.echo(f"Date: {anomaly['date']} | Volume: {anomaly['volume']:,.0f} | StdDevs: {anomaly['std_devs']:,.1f}")

@click.group()
def cli():
    """
    Extract Venmo transactions from a profile with one command


    """
    pass


@cli.command()
@click.option('--months', default=5, type=click.INT, help='Months of volume history')
@click.option('--days', default=3, type=click.INT, help='Continuous days of anomalies')
@click.option('--stddev', default=5, type=click.INT, help='Standard deviation cutoff')
@click.option('--save/--no-save', default=False, help='Whether to save anomaly data')
@click.option('--filename', default='anomalies', help='Filename of which to save anomaly data')
@click.option('--filter', help='Filter on ticker symbol')
def scan(months: int, days: int, stddev: int, save: bool, filename: str, filter: str = None):
    """
    Extract Venmo transactions from a profile with one command


    """
    tickers = load_tickers()

    if filter:
        filtered_tickers = []
        compiled_filter = re.compile(filter, re.IGNORECASE)
        for ticker in tickers:
            if compiled_filter.search(f"{ticker['symbol']} - {ticker['name']}"):
                filtered_tickers.append(ticker)
        click.echo(f"Running filtered anomaly scanner on {len(filtered_tickers)} stocks")
        anomalies = run_scanner(filtered_tickers, months, days, stddev)
    else:
        click.echo(f"Running anomaly scanner on {len(tickers)} stocks")
        anomalies = run_scanner(tickers, months, days, stddev)

    if anomalies:
        for anomaly in anomalies:
            print_result(anomaly)
    else:
        click.echo(click.style('No anomalies were found', fg='red', bold=True))

    if anomalies and save:
        save_data(list(anomalies), filename)


@cli.command()
@click.option('--filter', help='Filter on ticker symbol')
def list_tickers(filter: str = None):
    """
    List ticker information (saved in package data directory)
    """
    tickers = load_tickers()
    if filter:
        compiled_filter = re.compile(filter, re.IGNORECASE)
    for ticker in tickers:
        if filter:
            if compiled_filter.search(f"{ticker['symbol']} - {ticker['name']}"):
                click.echo(f"{ticker['symbol']} - {ticker['name']}")
        else:
            click.echo(f"{ticker['symbol']} - {ticker['name']}")


@cli.command()
def update_tickers():
    """
    Update ticker information (saved in package data directory)
    """
    download_tickers()
    click.echo('Successfully updated ticker information')


if __name__ == '__main__':
    cli()
