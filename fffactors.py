import pandas as pd 
import numpy as np
import math 
from datetime import datetime
from pandas.tseries.offsets import *
import matplotlib.pyplot as plt

ccm = pd.read_csv('linktable.csv')
ccm['LINKDT']=pd.to_datetime(ccm['LINKDT'], format='%Y%m%d')
ccm['LINKENDDT']=pd.to_datetime(ccm['LINKENDDT'], errors='coerce', format='%Y%m%d')
# if linkenddt is missing then set to today date
ccm['LINKENDDT']=ccm['LINKENDDT'].fillna(pd.to_datetime('today'))
ccm['LINKENDDT']=pd.to_datetime(ccm['LINKENDDT']).dt.date


# load crsp data
crsp_m = pd.read_csv('stock2.csv')
#crsp_m[['PERMCO','PERMNO','SHRCD','EXCHCD']] = crsp_m[['PERMCO','PERMNO','SHRCD','EXCHCD']].apply(pd.to_numeric, errors='coerce')
crsp_m[['SHRCD','EXCHCD']]=crsp_m[['SHRCD','EXCHCD']].astype(np.int64, errors='ignore')

# Line up date to be end of month
crsp_m['date']=pd.to_datetime(crsp_m['date'], format='%Y%m%d')
crsp_m['jdate']=crsp_m['date']+MonthEnd(0)

crsp_m[['DLRET','RET']] = crsp_m[['DLRET','RET']].apply(pd.to_numeric, errors='coerce')
crsp = crsp_m.copy()
crsp['DLRET']=crsp['DLRET'].fillna(0)
crsp['RET']=crsp['RET'].fillna(0)
crsp['retadj']=(1+crsp['RET'])*(1+crsp['DLRET'])-1 # cumulative return
crsp['me']=crsp['PRC'].abs()*crsp['SHROUT']/1000 # calculate market equity
crsp = crsp[(crsp['SHRCD'].isin([10, 11])) & (crsp['EXCHCD'].isin([1,2,3]))]

### Aggregate Market Cap ###
# sum of me across different permno belonging to same permco a given date
crsp['aggme'] = crsp.groupby(['jdate','PERMCO'])['me'].transform(np.sum)

# keep December market cap
crsp['year']=crsp['jdate'].dt.year
crsp['month']=crsp['jdate'].dt.month
decme=crsp[crsp['month']==12]
decme=decme[['PERMNO','jdate','aggme','year']].rename(columns={'aggme':'dec_me'})

# t Jun to t+1 July is within a ffyear
crsp['ffdate']=crsp['jdate']+MonthEnd(-6)
crsp['ffyear']=crsp['ffdate'].dt.year
crsp['ffmonth']=crsp['ffdate'].dt.month

# lag market cap
crsp['lme']=crsp.groupby(['PERMNO'])['aggme'].shift(1)

# decme shift(1)
decme['ffyear']=decme['year']+1
decme=decme[['PERMNO','ffyear','dec_me']]

# use ffyear to merge decme
crsp_final = pd.merge(crsp, decme, how='left', on=['PERMNO','ffyear'])
crsp_final=crsp_final[['PERMNO', 'jdate','ffyear','ffmonth','SHRCD','EXCHCD','lme','dec_me','retadj']]
crsp_final=crsp_final.sort_values(by=['PERMNO','jdate'])

'''
 Book Equity is defined as the Compustat book value of stockholders' 
 equity plus balance sheet deferred taxes and investment tax credit 
 (if available) minus book value of preferred stock. 
 '''
comp = pd.read_csv('compustat2.csv')
comp['datadate']=pd.to_datetime(comp['datadate'], format='%Y%m%d') #convert datadate to date fmt
comp['year']=comp['datadate'].dt.year

# create Shareholders' equity
comp['she']=np.where(comp['seq'].isnull(), comp['ceq']+comp['pstk'], comp['seq'])
comp['she']=np.where(comp['she'].isnull(), comp['at']-comp['lt']-comp['mib'], comp['she'])
comp['she']=np.where(comp['she'].isnull(), comp['at']-comp['lt'], comp['she'])
comp['she']=np.where(comp['she'].isnull(), 0, comp['she'])

# Deferred taxes and investment tax credit
comp['dt']=np.where(comp['txditc'].isnull(), comp['itcb']+comp['txdb'], comp['txditc'])
comp['dt']=np.where(comp['dt'].isnull(), comp['itcb'], comp['dt'])
comp['dt']=np.where(comp['dt'].isnull(), comp['txdb'], comp['dt'])
comp['dt']=np.where(comp['dt'].isnull(), 0, comp['dt'])

# create preferrerd stock
comp['ps']=np.where(comp['pstkrv'].isnull(), comp['pstkl'], comp['pstkrv'])
comp['ps']=np.where(comp['ps'].isnull(),comp['pstk'], comp['ps'])
comp['ps']=np.where(comp['ps'].isnull(),0,comp['ps'])

# Add COMPUSTAT Pension
comp_pension = pd.read_csv('prba.csv')

comp_pension['datadate']=pd.to_datetime(comp['datadate'], format='%Y%m%d') #convert datadate to date fmt
comp = pd.merge(comp, comp_pension, how='left', on=['gvkey','datadate'])
comp['prba'] = comp['prba'].fillna(0)
# create book equity
comp['be']=comp['she']+comp['dt']-comp['ps']-comp['prba']
comp['be']=np.where(comp['be']>0, comp['be'], np.nan)
comp = comp.loc[comp['be'].notnull()]

comp=comp[['gvkey','datadate','year','be']]

# jdate plus 6 month before merging with crsp, so comp Dec data are in the row with crsp July data
ccm1=pd.merge(comp[['gvkey','datadate','be']],ccm,how='left',on=['gvkey'])
ccm1['yearend']=ccm1['datadate']+YearEnd(0)
ccm1['jdate']=ccm1['yearend']+MonthEnd(6)
ccm1['LINKENDDT'] = pd.to_datetime(ccm1['LINKENDDT'])
# set link date bounds
ccm2=ccm1[(ccm1['jdate']>=ccm1['LINKDT'])&(ccm1['jdate']<=ccm1['LINKENDDT'])].copy()
# create ffyear and delete jdate, because jdate is not actual date any more
ccm2['ffyear']=ccm2['jdate'].dt.year
ccm2=ccm2[['gvkey','LPERMNO','ffyear','be']].rename(columns= {'LPERMNO':'PERMNO'})
# link comp and crsp using permno and ffyear
ccm_final=pd.merge(crsp_final, ccm2, how='left', on=['PERMNO', 'ffyear'])
ccm_final=ccm_final.drop(['gvkey'],axis=1)
ccm_final['year']=ccm_final['jdate'].dt.year
ccm_final['month']=ccm_final['jdate'].dt.month
ccm_final['bm'] = ccm_final['be']/ccm_final['dec_me']
ccm_final.replace(np.inf, np.nan)

outdata = ccm_final[['PERMNO','jdate','lme','retadj','bm','year','month']]
outdata.to_csv('bm.csv',index=False)
