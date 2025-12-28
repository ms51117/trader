import pandas as pd


def load_data(path):
    df = pd.read_csv(path, parse_dates=True, index_col=0)
    return df
