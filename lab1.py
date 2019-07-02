import pandas as pd 
import numpy as np
import math 
import matplotlib.pyplot as plt

ccm = pd.read_csv('bm.csv')

def my_strategy(num, period):
    subset1 = ccm.groupby(by = ['jdate'])[['PERMNO','lme','retadj','bm','year','month']].apply(lambda df: df.nlargest(num, 'bm')).reset_index()
    subset1 = subset1[(subset1['year']> (2018-period))&(subset1['year']<= 2018)]
    weighted_avg = lambda x: np.average(x, weights=subset1.loc[x.index, 'lme'])
    func = {'retadj' :weighted_avg}
    vwretd = subset1.groupby(by = 'jdate').agg(func).reset_index()
    vwretd['cumret'] = (vwretd['retadj'] + 1).cumprod() - 1
    ewretd = subset1.groupby(by = 'jdate')[['jdate','retadj']].mean().reset_index()
    ewretd['cumret'] = (ewretd['retadj'] + 1).cumprod() - 1
    merged = pd.merge(vwretd, ewretd, on = 'jdate')
    merged = merged.rename(index = str, columns = {'jdate': 'date',
                                                    'cumret_x' : 'cum_vwretd',
                                                    'cumret_y' : 'cum_ewretd',
                                                    'retadj_x' : 'vwretd',
                                                    'retadj_y' : 'ewretd'})
    merged.plot(x = 'date', y = ['cum_vwretd', 'cum_ewretd'],
        title = 'comparison between value-weighted portfolio and equal-weighted portfolio')
    plt.show()

my_strategy(100, 10)