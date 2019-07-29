import pandas as pd 
import numpy as np
import math 
import matplotlib.pyplot as plt

ccm = pd.read_csv('bm.csv')
mkt = pd.read_csv('ff3.csv', skiprows= 3, nrows= 1114)
mkt['date'] = pd.to_datetime(mkt['date'], format = '%Y%m')
mkt['year'] = mkt['date'].dt.year
mkt['month'] = mkt['date'].dt.month
mkt['mkt_vwretd'] = (mkt['Mkt-RF'] + mkt['RF'])/100
mkt = mkt[['mkt_vwretd', 'year','month']]

def my_strategy(num, period):
    subset1 = ccm.groupby(by = ['jdate'])[['PERMNO','lme','retadj','bm','year','month']].apply(lambda df: df.nlargest(num, 'bm')).reset_index()
    subset1 = subset1[(subset1['year']> (2018-period))&(subset1['year']<= 2018)]
    weighted_avg = lambda x: np.average(x, weights=subset1.loc[x.index, 'lme'])
    func = {'retadj' :weighted_avg}
    vwretd = subset1.groupby(by = 'jdate').agg(func).reset_index()
    vwretd['cumret'] = (vwretd['retadj'] + 1).cumprod()
    ewretd = subset1.groupby(by = 'jdate')[['jdate','retadj']].mean().reset_index()
    ewretd['cumret'] = (ewretd['retadj'] + 1).cumprod() 
    merged = pd.merge(vwretd, ewretd, on = 'jdate')
    merged = merged.rename(index = str, columns = {'jdate': 'date',
                                                    'cumret_x' : 'cum_vwretd',
                                                    'cumret_y' : 'cum_ewretd',
                                                    'retadj_x' : 'vwretd',
                                                    'retadj_y' : 'ewretd'})
    merged.plot(x = 'date', y = ['cum_vwretd', 'cum_ewretd'],
        title = 'comparison between value-weighted portfolio and equal-weighted portfolio')
    plt.show()

def compare_market(num, period, str_type):
    subset1 = ccm.groupby(by = ['jdate'])[['PERMNO','lme','retadj','bm','year','month']].apply(lambda df: df.nlargest(num, 'bm')).reset_index()
    subset1 = subset1[(subset1['year']> (2018-period))&(subset1['year']<= 2018)]
    weighted_avg = lambda x: np.average(x, weights=subset1.loc[x.index, 'lme'])
    func = {'retadj' :weighted_avg}
    vwretd = subset1.groupby(by = ['year','month']).agg(func).reset_index()
    vwretd['cumret'] = (vwretd['retadj'] + 1).cumprod()
    ewretd = subset1.groupby(by = ['year', 'month'])[['retadj']].mean().reset_index()
    ewretd['cumret'] = (ewretd['retadj'] + 1).cumprod()
    merged = pd.merge(vwretd, ewretd, on = ['year', 'month'])
    merged = merged.rename(index = str, columns = {'jdate': 'date',
                                                    'cumret_x' : 'cum_vwretd',
                                                    'cumret_y' : 'cum_ewretd',
                                                    'retadj_x' : 'vwretd',
                                                    'retadj_y' : 'ewretd'})
    merged_mkt = pd.merge(merged, mkt, how = 'left', on = ['year', 'month'])
    merged_mkt['cum_mkt_vw'] = (merged_mkt['mkt_vwretd'] + 1).cumprod()
    merged_mkt['day'] = 1
    merged_mkt['date'] = pd.to_datetime(merged_mkt[['year','month', 'day']])
    if str_type == 'vwretd':
        merged_mkt.plot(x = 'date', y = ['cum_vwretd', 'cum_mkt_vw'],\
            title = 'comparison between value-weighted portfolio and market')
    else:
        merged_mkt.plot(x = 'date', y = ['cum_ewretd', 'cum_mkt_vw'],\
            title = 'comparison between equal-weighted portfolio and market')
    plt.show()

compare_market(100, 10, 'ewretd')