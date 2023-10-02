## Project Name: Orcasound Salmon
### Program Name: make_peak_data.py
### Purpose: To create long format data of Chinook CPUE at Albion & SRKW for modeling
##### Date Created: Sep 17th 2023

import os
from os.path import join as pjoin
from datetime import date
from datetime import datetime as dt 
import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

APP_PATH = os.path.abspath("")
#Get dates
today=date.today()
todaystr=str(today)
curyr=today.year
lastyr=curyr-1
twoyr=curyr-2
ayl=[y for y in range(1980, curyr+1)] #year list for Albion
byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam
twmyl=[y for y in range(1976, 2022)] #year list for TWM data
#Define data path
fos_path=pjoin(APP_PATH,'data/foschinook/')
bon_path=pjoin(APP_PATH,'data/bonchinook/')
acartia_path=pjoin(APP_PATH, 'data/acartia/')
twm_path=pjoin(APP_PATH, 'data/twm/')
srkw_path=pjoin(APP_PATH, 'data/')

def srkw_long(years=[1991,]):
    entry_lat=48.19437
    allpres=pd.DataFrame()
    for year in years:
        if year<2018:
            srkw1=pd.read_csv(twm_path+"twm"+str(year)+".csv")
            srkw=srkw1[srkw1['central_salish']==1][['SightDate','j','k','l']]
        elif (year >=2018) and (year<2022):
            srkw1=pd.read_csv(twm_path+"twm"+str(year)+".csv")
            srkw1=srkw1[srkw1['central_salish']==1][['SightDate','j','k','l']]
            srkw2=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")            
            srkw2['central_salish']=srkw2['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
            srkw2['SightDate']=srkw2['created'].apply(lambda x: x[:10])
            srkw2=srkw2[srkw2['central_salish']==1][['SightDate','J','K','L']]
            srkw2.columns=['SightDate','j','k','l']
            srkw=pd.concat([srkw1, srkw2])
        else:
            srkw2=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")            
            srkw2['central_salish']=srkw2['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
            srkw2['SightDate']=srkw2['created'].apply(lambda x: x[:10])
            srkw2=srkw2[srkw2['central_salish']==1][['SightDate','J','K','L']]
            srkw2.columns=['SightDate','j','k','l']
            srkw=srkw2
        srkw['day_of_year']=srkw['SightDate'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
        srkw_flat=srkw.groupby('day_of_year').sum()
        srkw_flat['year']=year
        srkw_flat['all_count']=srkw_flat.apply(lambda x: x['j']+x['k']+x['l'], axis=1)
        srkw_flat['AllSRpres']=srkw_flat.apply(lambda x: 1 if x['all_count']>0 else 0, axis=1)
        srkw_flat['Jpres']=srkw_flat.apply(lambda x: 1 if x['j']>0 else 0, axis=1)
        srkw_flat['Kpres']=srkw_flat.apply(lambda x: 1 if x['k']>0 else 0, axis=1)
        srkw_flat['Lpres']=srkw_flat.apply(lambda x: 1 if x['l']>0 else 0, axis=1)
        allpres=pd.concat([allpres, srkw_flat])
    return allpres
x=srkw_long(years=range(1990,2023))
x.to_csv(srkw_path+"srkw_presence.csv")

def albion_long(years=[1991,]):
    alldata=pd.DataFrame()
    for year in years:
        albion=pd.read_csv(fos_path+'fos'+str(year)+'.csv',\
        usecols=['day','mon','cpue1','catch1','sets1','effort1'])
        albion['year']=year
        albion['m']=albion['mon'].apply(lambda x: dt.strptime(x, '%b').month)
        albion['date']=albion.apply(lambda x: dt(year, x['m'],x['day']), axis=1)
        albion['day_of_year']=albion['date'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
        alldata=pd.concat([alldata, albion])
    alldata.columns=['day','mon','catch','sets','effort','cpue','year','month','date','calDay']
    alldata=alldata[['date','year','month','mon','day','calDay','cpue','catch','sets','effort']]
    return alldata 

y=albion_long(years=range(1980,2023))
y.to_csv(srkw_path+"albion_long.csv")