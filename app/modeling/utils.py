
import numpy as np
import pandas as pd
from app.indicators import find_swings
from app.indicators import classify_swings

def adding_target_to_data(data):
    # add HH, LL, LH, HL and NP targets to the dataframe
    target_df = classify_swings(find_swings(data))
    # concat databases
    data = pd.concat([data, target_df], axis="columns")
    data.drop(columns=[
        'c_ts',
        'CSLS',
        'Support',
        'Resistance',
        'Strong_lows',
        'Strong_highs',
        'FSL',
        'FSH',
        'Highs',
        'Lows',
        'Last',
        'Trend',
        'o_date'
        ], inplace=True)
    data[['HH','HL','LL','LH']] = data[['HH','HL','LL','LH']] * 1
    data['sum'] = data[['HH','HL','LL','LH']].sum(axis=1)
    data['NP'] = data['sum'].apply(lambda x: 1 if x==0 else 0)
    data.drop(columns='sum',inplace=True)
    return data

def subsample_sequence(df, length):
    """
    Given the initial dataframe `df`, return a shorter dataframe sequence of length `length`.
    This shorter sequence should be selected at random
    """
    last_possible = df.shape[0] - length

    random_start = np.random.randint(0, last_possible)
    df_sample = df[random_start: random_start+length]
    return df_sample

def split_subsample_sequence(df, length):
    '''Create one single random (X,y) pair'''
    df_subsample = subsample_sequence(df, length)
    y_sample = df_subsample.iloc[length -1][['LL','HL','HH','LH','NP']]

    X_sample = df_subsample[0:length -1]
    X_sample = X_sample.values
    return np.array(X_sample), np.array(y_sample)
