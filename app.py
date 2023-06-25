#%% [markdown]
## Project Name: Orcasound Salmon
### Program Name: app.py
### Purpose: To make a dash board for the Chinook salmon data
##### Date Created: Dec 3rd 2022
import os
from os.path import join as pjoin
import pathlib
import glob

import datetime
from datetime import date
from datetime import datetime as dt 
from time import strptime
from time import sleep
import calendar

import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

import numpy as np
from sklearn.linear_model import LinearRegression
import dash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output, State
import dash_daq as daq 

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
from plotly.express.colors import sample_colorscale
#%%
# Initialize app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "Chinook Salmon Dashboard"}, 
        {"name": "news_keywords", "content": "Chinook, Salmon, Orca, Killer Whales, Puget Sound"}
        ],
    )
server=app.server
#%%
#--------------------------Load And Process Data----------------------------#
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
mapbox_access_token = os.environ.get('MAPBOX_TOKEN')
#mapbox_access_token = open(pjoin(APP_PATH,"mapbox_token.txt")).read()
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
#%%
#Load Albion data
albion=pd.DataFrame(columns=['day','m'])
albion_cpue=[] # Albion cpue sum
for i in reversed(range(len(ayl))):
    d=pd.read_csv(fos_path+'fos'+str(ayl[i])+'.csv',\
        usecols=['day','mon','cpue1'])
    s=sum(d['cpue1'])
    albion_cpue.append(s)
    d['m']=d['mon'].apply(lambda x: dt.strptime(x, '%b').month)
    d=d.drop(columns='mon')
    d=d.rename(columns={'cpue1':'cpue'+str(ayl[i])})
    albion=pd.merge(left=albion, right=d, how='outer', on=['m','day'], sort=True)
del(d,i,s)
albion['cpue_hist']=albion.iloc[:,5:].mean(axis=1, skipna=True).round(decimals=2) #History up to 3 years ago
albion['cpue_hist2']=albion.iloc[:,3:].mean(axis=1, skipna=True).round(decimals=2) #History up to last year
albion['month']=albion['m'].apply(lambda x: dt.strptime(str(x), '%m').strftime('%b'))
albion['date']=albion[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
albionpd=pd.DataFrame({'year':ayl[:-1], 'alb_cpue':albion_cpue[:-1]}, columns=['year','alb_cpue'])
# %%
# Load Bonneville Dam data
bonnev=pd.DataFrame(columns=['day','m'])
for i in reversed(range(len(byl))):
    d=pd.read_csv(bon_path+'bon'+str(byl[i])+'.csv',\
        usecols=['Project','Date','Chin'])
    d=d[d['Project']=='Bonneville']
    d['Chin2']=d['Chin'].apply(lambda x: 0 if x<0 else x)
    d['m']=pd.DatetimeIndex(d['Date']).month
    d['day']=pd.DatetimeIndex(d['Date']).day
    d=d.rename(columns={'Chin2':'chin'+str(byl[i])})
    d=d.drop(columns=['Project','Date','Chin'])
    bonnev=pd.merge(left=bonnev, right=d, how='outer', on=['m','day'], sort=True)
del(d,i)
bonnev['chin_hist']=bonnev.iloc[:,5:].mean(axis=1, skipna=True).round(decimals=1)#History up to 3 years ago
bonnev['chin_hist2']=bonnev.iloc[:,3:].mean(axis=1, skipna=True).round(decimals=1)#History up to last year
bonnev['month']=bonnev['m'].apply(lambda x: dt.strptime(str(x), '%m').strftime('%b'))
bonnev['date']=bonnev[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
# %%
# Create calendar dataframes 
cal=bonnev[['date']]
cal=cal[cal['date']!='Feb-29']
cal['date1']=pd.to_datetime(cal['date'].apply(lambda x: str(2021)+'-'+x), format='%Y-%b-%d')
cal['m']=pd.DatetimeIndex(cal['date1']).month
cal['day']=pd.DatetimeIndex(cal['date1']).day
cal=cal.drop(columns=['date1'])
# Example data frame
# date  m day
# Jan-1 1 1 
# Create calendar dataframes for leapyear 
cal_leap=bonnev[['date']]
cal_leap['date1']=pd.to_datetime(cal_leap['date'].apply(lambda x: str(2020)+'-'+x), errors='coerce', format='%Y-%b-%d')
cal_leap['m']=pd.DatetimeIndex(cal_leap['date1']).month.astype('int')
cal_leap['day']=pd.DatetimeIndex(cal_leap['date1']).day.astype('int')
cal_leap=cal_leap.drop(columns=['date1'])
#%%
albion=albion.drop(columns=['date'])
albion=cal_leap.merge(albion, how='left', on=['m','day'])
# %%
def create_lagged(year, 
    lag1, # Albion lag
    lag2  # Bonneville lag
    ):
    # Create Albion lag dataset
    albion_lagged=albion[['date','cpue'+str(year),'cpue_hist']]
    if calendar.isleap(year)==False:
        albion_lagged=albion_lagged[albion_lagged['date']!='Feb-29']
    albion_lagged['date1']=pd.to_datetime(albion_lagged['date'], errors='coerce', format='%b-%d')
    albion_lagged['date2']=albion_lagged['date1'] - pd.Timedelta(days=lag1)
    albion_lagged['m']=pd.DatetimeIndex(albion_lagged['date2']).month
    albion_lagged['day']=pd.DatetimeIndex(albion_lagged['date2']).day
    albion_lagged=albion_lagged.drop(columns=['date','date1','date2'])
    # Create Bonneville Dam lagged dataset
    bonnev_lagged=bonnev[['date','chin'+str(year),'chin_hist']]
    if calendar.isleap(year)==False:
        bonnev_lagged=bonnev_lagged[bonnev_lagged['date']!='Feb-29']
    bonnev_lagged['date1']=pd.to_datetime(bonnev_lagged['date'].apply(lambda x: str(year)+'-'+x), errors='coerce',format='%Y-%b-%d')
    bonnev_lagged['date2']=bonnev_lagged['date1'] - pd.Timedelta(days=lag2)
    bonnev_lagged['year2']=pd.DatetimeIndex(bonnev_lagged['date2']).year
    bonnev_lagged['m']=pd.DatetimeIndex(bonnev_lagged['date2']).month
    bonnev_lagged['day']=pd.DatetimeIndex(bonnev_lagged['date2']).day
    bonnev_lagged=bonnev_lagged[bonnev_lagged['year2']==year]
    bonnev_lagged=bonnev_lagged.drop(columns=['date','date1','date2','year2'])
    #Combine Albion and Bonneville lagged data
    if calendar.isleap(year)==False:
        lagged=cal.merge(bonnev_lagged, how='left', on=['m','day'])
    else:
        lagged=cal_leap.merge(bonnev_lagged, how='left', on=['m','day'])
    lagged=lagged.merge(albion_lagged, on=['m','day'], how='left')
    return lagged
lagged=create_lagged(curyr, 10, 10)
# %% [markdown]
# Load Acartia data
# Function count orca reports or counts by day
def srkw_count(dat, count_orca=False):
    if count_orca:
        #print('Creating a daily average of number of orcas...')
        dat=dat.loc[:, ['no_sighted', 'date_ymd']]
        srkw_avg=dat.groupby(dat.date_ymd).mean().reset_index()
        srkw_avg=srkw_avg.rename(columns={'date_ymd':'date','no_sighted':'count'})
    else:
        #print('Creating a daily count of reports...')
        dat=dat.loc[:, ['date_ymd']]
        srkw_avg=dat['date_ymd'].value_counts().reset_index()
        srkw_avg=srkw_avg.rename(columns={'date_ymd':'count','index':'date'})
        srkw_avg=srkw_avg.sort_values(by=['date'])
    srkw_avg['day']=srkw_avg['date'].apply(lambda x: int(x.split('-')[2]))
    srkw_avg['m']=srkw_avg['date'].apply(lambda x: int(x.split('-')[1]))
    srkw_avg=srkw_avg.sort_values(by=['m','day'])
    return srkw_avg
#%%
# Function to read in acartia orca data for maps
def srkw_acartia_map(year, pod="All pods"):
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc=srkwc[~srkwc.date.isnull()]
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    srkwc['mon']=srkwc['date2'].apply(lambda x: x.month)
    srkwc['mon_frac']=srkwc['mon'].apply(lambda x: viri12pt[int(x)-1])
    srkwc['day_of_year']=srkwc['date_ymd'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    srkwc_k=srkwc[srkwc.K==1].reset_index()
    srkwc_l=srkwc[srkwc.L==1].reset_index()
    srkwc_j=srkwc[srkwc.J==1].reset_index()
    if pod=="L pod":
        srkw_dat=srkwc_l
    elif pod=="K pod":
        srkw_dat=srkwc_k
    elif pod=="J pod":
        srkw_dat=srkwc_j
    elif pod=="All pods":
        srkw_dat=srkwc[srkwc.srkw==1]
    return srkw_dat
#%% 
# Function to make orca count data of a certain year and merge with salmon data
def srkw_acartia_year(year, pod="All pods"):
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    #srkwc['day_of_year']=srkwc['date_ymd'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    # Define the north and south puget sound latitude
    entry_lat=48.19437
    srkwc['north_puget_sound']=srkwc['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
    srkwc_k=srkwc[srkwc.K==1].reset_index()
    srkwc_l=srkwc[srkwc.L==1].reset_index()
    srkwc_j=srkwc[srkwc.J==1].reset_index()

    if pod=="L pod":
        srkw_dat=srkwc_l
    elif pod=="K pod":
        srkw_dat=srkwc_k
    elif pod=="J pod":
        srkw_dat=srkwc_j
    elif pod=="All pods":
        srkw_dat=srkwc[srkwc.srkw==1]
    srkwc_north=srkw_dat[srkw_dat['north_puget_sound']==1]
    srkwc_north_avg=srkw_count(srkwc_north, count_orca=False)
    srkwc_north_avg.columns=['date','count_north','day','m']

    srkwc_south=srkw_dat[srkw_dat['north_puget_sound']==0]
    srkwc_south_avg=srkw_count(srkwc_south, count_orca=False)
    srkwc_south_avg.columns=['date','count_south','day','m']

    srkw_yrcount=srkw_count(srkwc, count_orca=False)
    
    # Add salmon data
    salmon=create_lagged(year, 4, 10)
    srkw_yrcount=srkw_yrcount.merge(salmon, left_on=['m','day'], right_on=['m','day'], how='right')
    srkw_yrcount=srkw_yrcount.drop(columns=['date_x'])
    srkw_yrcount=srkw_yrcount.rename(columns={'date_y':'date'})

    # Add srkw count north of puget sound
    srkw_yrcount=srkw_yrcount.merge(srkwc_north_avg, left_on=['m','day'], right_on=['m','day'], how='left')
    srkw_yrcount=srkw_yrcount.drop(columns=['date_y'])
    srkw_yrcount=srkw_yrcount.rename(columns={'date_x':'date'})

    # Add srkw count in puget sound
    srkw_yrcount=srkw_yrcount.merge(srkwc_south_avg, left_on=['m','day'], right_on=['m','day'], how='left')
    srkw_yrcount=srkw_yrcount.drop(columns=['date_y'])
    srkw_yrcount=srkw_yrcount.rename(columns={'date_x':'date'})

    # Keep a subset of variables 
    srkw_yrcount=srkw_yrcount[['date', 'm','day','count','count_north','count_south','chin'+str(year),'chin_hist','cpue'+str(year),'cpue_hist']]
    srkw_yrcount.columns=['date','m','day','srkw','srkw_north','srkw_south','bon'+str(year),'bon_hist','alb'+str(year),'alb_hist']
    return srkw_yrcount
#%% [markdown]
# Load the Whale Museum Data
def srkw_twm_map(year, pod="All pods"):
    srkwc=pd.read_csv(twm_path+"twm"+str(year)+".csv")
    srkwc['mon_frac']=srkwc['Month'].apply(lambda x: viri12pt[int(x)-1])
    srkwc['day_of_year']=srkwc['SightDate'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    srkwc['created']=srkwc['SightDate']+" "+srkwc['Time1']
    srkwc_k=srkwc[srkwc.k==1].reset_index()
    srkwc_l=srkwc[srkwc.l==1].reset_index()
    srkwc_j=srkwc[srkwc.j==1].reset_index()
    if pod=="L pod":
        srkw_dat=srkwc_l
    elif pod=="K pod":
        srkw_dat=srkwc_k
    elif pod=="J pod":
        srkw_dat=srkwc_j
    elif pod=="All pods":
        srkw_dat=srkwc
    return srkw_dat[['created','mon_frac','latitude','longitude']]
#%% [markdown]
# Load The Whale Museum Data 
def srkw_twm_year(year, pod="All pods"):
    srkwc=pd.read_csv(twm_path+"twm"+str(year)+".csv")
    # Define the north and south puget sound latitude
    entry_lat=48.19437
    srkwc['north_puget_sound']=srkwc['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
    srkwc['mon_frac']=srkwc['Month'].apply(lambda x: viri12pt[int(x)-1])
    srkwc['day_of_year']=srkwc['SightDate'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    srkwc['date_ymd']=srkwc['SightDate']
    srkwc['created']=srkwc['SightDate']+" "+srkwc['Time1']
    srkwc_k=srkwc[srkwc.k==1].reset_index()
    srkwc_l=srkwc[srkwc.l==1].reset_index()
    srkwc_j=srkwc[srkwc.j==1].reset_index()
    if pod=="L pod":
        srkw_dat=srkwc_l
    elif pod=="K pod":
        srkw_dat=srkwc_k
    elif pod=="J pod":
        srkw_dat=srkwc_j
    elif pod=="All pods":
        srkw_dat=srkwc

    srkwc_north=srkw_dat[srkw_dat['north_puget_sound']==1]
    srkwc_north_avg=srkw_count(srkwc_north, count_orca=False)
    srkwc_north_avg.columns=['date','count_north','day','m']

    srkwc_south=srkw_dat[srkw_dat['north_puget_sound']==0]
    srkwc_south_avg=srkw_count(srkwc_south, count_orca=False)
    srkwc_south_avg.columns=['date','count_south','day','m']

    srkw_yrcount=srkw_count(srkwc, count_orca=False)
    
    # Add salmon data
    salmon=create_lagged(year, 4, 10)
    srkw_yrcount=srkw_yrcount.merge(salmon, left_on=['m','day'], right_on=['m','day'], how='right')
    srkw_yrcount=srkw_yrcount.drop(columns=['date_x'])
    srkw_yrcount=srkw_yrcount.rename(columns={'date_y':'date'})

    # Add srkw count north of puget sound
    srkw_yrcount=srkw_yrcount.merge(srkwc_north_avg, left_on=['m','day'], right_on=['m','day'], how='left')
    srkw_yrcount=srkw_yrcount.drop(columns=['date_y'])
    srkw_yrcount=srkw_yrcount.rename(columns={'date_x':'date'})

    # Add srkw count in puget sound
    srkw_yrcount=srkw_yrcount.merge(srkwc_south_avg, left_on=['m','day'], right_on=['m','day'], how='left')
    srkw_yrcount=srkw_yrcount.drop(columns=['date_y'])
    srkw_yrcount=srkw_yrcount.rename(columns={'date_x':'date'})

    # Keep a subset of variables 
    srkw_yrcount=srkw_yrcount[['date', 'm','day','count','count_north','count_south','chin'+str(year),'chin_hist','cpue'+str(year),'cpue_hist']]
    srkw_yrcount.columns=['date','m','day','srkw','srkw_north','srkw_south','bon'+str(year),'bon_hist','alb'+str(year),'alb_hist']

    return srkw_yrcount

# Functions for calculating peak sightings of orca and peak count of Chinook
def to_datetime(date):
    """
    Converts a numpy datetime64 object to a python datetime object 
    Input:
      date - a np.datetime64 object
    Output:
      DATE - a python datetime object
    """
    timestamp = ((date - np.datetime64('1970-01-01T00:00:00'))
                 / np.timedelta64(1, 's'))
    return dt.utcfromtimestamp(timestamp).date()
def str2mon(m):
    if isinstance(m, str):
        ml=m.lower()
        if ml=="jan":
            x=1
        elif ml=="feb":
            x=2
        elif ml=="mar":
            x=3
        elif ml=="apr":
            x=4
        elif ml=="may":
            x=5
        elif ml=="jun":
            x=6
        elif ml=="jul":
            x=7
        elif ml=="aug":
            x=8
        elif ml=="sep":
            x=9
        elif ml=="oct":
            x=10
        elif ml=="nov":
            x=11
        elif ml=="dec":
            x=12
        return x
    else: 
        raise ValueError("Input value not string")
def peak_chinook(loc="Albion", year_zero=1990):
    ayl=[y for y in range(year_zero, curyr)] #year list for Albion up till last year
    byl=[y for y in range(year_zero, curyr)] #year list for Bonneville Dam up till last year
    peak_vals=[]
    peak_dates=[]
    peak_days=[]       
    if loc=="Albion":
        for i in range(len(ayl)):
            d=pd.read_csv(fos_path+'fos'+str(ayl[i])+'.csv',usecols=['day','mon','cpue1'])
            yr=ayl[i]
            peak_val=max(d['cpue1'])
            peak_row=d[d['cpue1']==peak_val]
            peak_day=peak_row.day.values[0]
            peak_mon=str2mon(peak_row.mon.values[0])
            peak_date=date(yr, peak_mon, peak_day)
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)                
    elif loc=="Bonneville":
        for i in range(len(byl)):
            d=pd.read_csv(bon_path+'bon'+str(byl[i])+'.csv',\
                    usecols=['Project','Date','Chin'])
            yr=byl[i]
            peak_val=max(d['Chin'].dropna())
            peak_row=d[d['Chin']==peak_val]
            peak_date=dt.strptime(peak_row.Date.values[0], '%Y-%m-%d').date()
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)                
    else:
        raise ValueError("Location other than 'Albion' and 'Bonneville'")
    return peak_vals, peak_dates, peak_days
def peak_srkw(src="twm", pod="", loc="", year_zero=1990):
    tyl=[y for y in range(year_zero, 2022)] #year list for data from The Whale Museum
    ayl=[y for y in range(2018, curyr)] #year list for data from Acartia
    byl=[y for y in range(year_zero, curyr)] #year list for data from both The Whale Museum plus Acartia
    peak_vals=[]
    peak_dates=[]
    peak_days=[]      
    # Read TWM data 
    twm_data=[]
    for i in range(len(tyl)):
        d1=pd.read_csv(os.path.join(twm_path,'twm'+str(tyl[i])+'.csv'))
        if pod=="":
            pass
        elif pod.lower()=="j":
            d1=d1[d1['j']==1]
        elif pod.lower()=="k":
            d1=d1[d1['k']==1]
        elif pod.lower()=="l":
            d1=d1[d1['l']==1]
        elif pod.lower()=="j or k or l":
            d1=d1[(d1['j']==1) | (d1['k']==1) | (d1['l']==1)]
        if loc=="":
            pass 
        elif loc.lower()=="puget sound":
            d1=d1[d1['puget_sound']==1]
        elif loc.lower()=="central salish":
            d1=d1[d1['central_salish']==1]
        d1=d1[['SightDate']]
        d1['SightDate']=d1['SightDate'].apply(lambda x: dt.strptime(x, '%Y-%m-%d').date())
        twm_data.append(d1)
    # Read Acartia Data 
    acartia_data=[]
    for i in range(len(ayl)):
        d2=pd.read_csv(os.path.join(acartia_path,'srkw_'+str(ayl[i])+'.csv'))
        d2['date2']=pd.to_datetime(d2['date_ymd'],format='%Y-%m-%d', errors='coerce')
        entry_lat=48.19437
        d2['central_salish']=d2['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
        d2['puget_sound']=d2['latitude'].apply(lambda x: 1 if x<=entry_lat else 0)            
        if pod=="":
            pass
        elif pod.lower()=="j":
            d2=d2[d2['J']==1]
        elif pod.lower()=="k":
            d2=d2[d2['K']==1]
        elif pod.lower()=="l":
            d2=d2[d2['L']==1]
        elif pod.lower()=="j or k or l":
            d2=d2[(d2['J']==1) | (d2['K']==1) | (d2['L']==1)]
        if loc=="":
            pass 
        elif loc.lower()=="puget sound":
            d2=d2[d2['puget_sound']==1]
        elif loc.lower()=="central salish":
            d2=d2[d2['central_salish']==1]
        d2=d2[['date2']]
        d2['date2']=d2['date2'].apply(lambda x: to_datetime(x))
        d2=d2.rename(columns={"date2":"SightDate"})
        acartia_data.append(d2)
    if src=="twm":
        for i in range(len(tyl)):
            d=twm_data[i]
            yr=tyl[i]
            d=d['SightDate'].value_counts().reset_index()
            d=d.rename(columns={'index':'Date', 'SightDate':'count'})
            peak_val=max(d['count'])
            peak_row=d[d['count']==peak_val]
            peak_date=peak_row['Date'].values[0]
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)                        
    elif src=="acartia":
        for i in range(len(ayl)):
            yr=ayl[i]
            d=acartia_data[i]
            d=d['SightDate'].value_counts().reset_index()
            d=d.rename(columns={'index':'Date', 'SightDate':'count'})   
            peak_val=max(d['count'])
            peak_row=d[d['count']==peak_val]
            peak_date=peak_row['Date'].values[0]
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)         
    elif src=="both":
        for i in range(len(byl)):
            yr=byl[i]
            if byl[i]<2018:
                j=tyl.index(byl[i])
                d=twm_data[j]
            elif (byl[i]>=2018) & (byl[i]<2022):
                j=tyl.index(byl[i])
                d1=twm_data[j]
                k=ayl.index(byl[i])
                d2=acartia_data[k]   
                d=pd.concat([d1, d2])              
            else:
                k=ayl.index(byl[i])
                d=acartia_data[k]
            d=d['SightDate'].value_counts().reset_index()
            d=d.rename(columns={'index':'Date', 'SightDate':'count'})   
            peak_val=max(d['count'])
            peak_row=d[d['count']==peak_val]
            peak_date=peak_row['Date'].values[0]
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)   
    else:
        raise ValueError("Source other than 'twm' and 'acartia'")
    return peak_vals, peak_dates, peak_days

# Calculating peak values of Chinook at Albion
year_zero=1990
albion_yl4peak=[y for y in range(year_zero, curyr+1)]
apeak=pd.DataFrame()
apv, apdt, apdy=peak_chinook(loc="Albion", year_zero=year_zero)
apeak['year']=albion_yl4peak[:-1]
apeak['peakvals']=apv 
apeak['peakdate']=apdt 
apeak['peakday']=apdy
x=apeak['year'].values.reshape((-1, 1))
y=apeak['peakday'].values
model = LinearRegression().fit(x, y)
r_sq = model.score(x, y)
albion_interc=model.intercept_
albion_slope=model.coef_

# Calculating peak values of Orca sightings 
def peak_mod_srkw(pod):
    if pod=="All pods":
        pod_value="j or k or l"
    else:
        pod_value=pod[0]
    srkw_cs_pv, srkw_cs_pdt, srkw_cs_pdy=peak_srkw(src="both", pod=pod_value, loc="central salish", year_zero=year_zero)
    srkw_cs_peak=pd.DataFrame()
    srkw_cs_peak['year']=[y for y in range(year_zero, curyr)]
    srkw_cs_peak['peakvals']=srkw_cs_pv 
    srkw_cs_peak['peakdate']=srkw_cs_pdt 
    srkw_cs_peak['peakday']=srkw_cs_pdy
    x=srkw_cs_peak['year'].values.reshape((-1, 1))
    y=srkw_cs_peak['peakday'].values
    model = LinearRegression().fit(x, y)
    srkw_interc=model.intercept_
    srkw_slope=model.coef_
    return srkw_cs_peak, srkw_interc, srkw_slope
# Get the intercept and slopes of orca sighitng models
srkw_cs_all_peak, srkw_all_interc, srkw_all_slope=peak_mod_srkw("All pods")
srkw_cs_j_peak, srkw_j_interc, srkw_j_slope=peak_mod_srkw("J")
srkw_cs_k_peak, srkw_k_interc, srkw_k_slope=peak_mod_srkw("K")
srkw_cs_l_peak, srkw_l_interc, srkw_l_slope=peak_mod_srkw("L")
#%% [markdow]
# Load The SRKW Population Data
srkwdata=pd.read_csv(pjoin(APP_PATH, "data/SRKW.csv"))
srkwdata_all=srkwdata[['year','JKL']]
srkwdata_all=srkwdata_all.rename(columns={"JKL":"SRKW"})
srkwdata_j=srkwdata[['year','J']]
srkwdata_j=srkwdata_j.rename(columns={"J":"SRKW"})
srkwdata_k=srkwdata[['year','K']]
srkwdata_k=srkwdata_k.rename(columns={"K":"SRKW"})
srkwdata_l=srkwdata[['year','L']]
srkwdata_l=srkwdata_l.rename(columns={"L":"SRKW"})
#%%
# Define path to salmon map image
salmon_map_path = 'assets/diagram_of_locations_v2.png'
# %%
# Create a color schemes and fonts
plotlycl=px.colors.qualitative.Plotly
viri12pt=[0.083,0.167,0.25,0.333,0.417,0.5,0.583,0.667,0.75,0.833,0.917,1]
viri12cl=sample_colorscale('viridis', samplepoints=viri12pt)
viri12=[[viri12pt[i], viri12cl[i]] for i in range(12)]
bgcl='white'
framecl='black'
markercl='salmon'
plotly_fonts=["Arial, sans-serif", "Balto, sans-serif", "Courier New, monospace",
            "Droid Sans, sans-serif", "Droid Serif, serif",
            "Droid Sans Mono, sans-serif",
            "Gravitas One, cursive", "Old Standard TT, serif",
            "Open Sans, sans-serif",
            "PT Sans Narrow, sans-serif", "Raleway, sans-serif",
            "Times New Roman, Times, serif"]
plotfont=plotly_fonts[10]
# %%
#----------------------------------App Title------------------------------------#
app.title='Chinook Salmon Dash Board'
#----------------------------------App Layout-----------------------------------#
app.layout = html.Div(
    id="root",
    children=[
            #Header,
            html.Div(
                id="header",
                children=[
                    html.A(id="github-link",children=[
                        html.Img(id="github", src=app.get_asset_url("icone-github-grise.png"),
                        ),
                    ], href='https://github.com/liu-zoe/orcasalmon', target="_blank"),
                    html.A(id="logo-link",
                           children=[
                        html.Img(id="logo", src=app.get_asset_url("wordlogo-seagreen.png"),
                        style={'height':'20%', 'width':'20%'}
                        ),        
                    ], href="https://www.orcasound.net", target="_blank"),
                
                    html.H3(children="Chinook and Orca",
                            style={'textAlign': 'left',},
                    ),
                    dcc.Markdown(
                        id="description",
                        children=
                        '''
                        A dash board to monitor Chinook salmon population and Orca movement around Puget Sound and Central Salish Sea                    
                        '''),
                    ],
                ),        
        dcc.Tabs(
            parent_className='custom-tabs',
            className='custom-tabs-container',
            children=[
            #----------------------------Tab 1: Salmon Time Series-----------------------------------#
                dcc.Tab(
                    label='Chinook Salmon', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Salmon Map column
                                html.Div(
                                    className="left-column",
                                    id="graph-container",
                                    children=[
                                        html.H6("Salish Sea and Puget Sound", 
                                                ),
                                        html.Img(id="salmon-static-map",
                                                src=salmon_map_path, 
                                                 ),
                                    ],
                                ),       
                                #Salmon time series Column
                                html.Div(
                                    className="right-column", 
                                    children=[
                                        html.Div(
                                            className="salmon-container",
                                            id="salmon-container",                                           
                                            children=[
                                                html.Div(
                                                    id="drop-downs",
                                                    children=[
                                                        html.H6("Select Location"),
                                                        dcc.Dropdown(
                                                            value="Albion v Bonneville",
                                                            className="location-dropdown",
                                                            id="location-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"Albion v Bonneville", 
                                                                    "value":"Albion v Bonneville"
                                                                },
                                                                {
                                                                    "label":"Albion",
                                                                    "value":"Albion",
                                                                },
                                                                {
                                                                    "label":"Bonneville Dam",
                                                                    "value":"Bonneville Dam",
                                                                },
                                                            ],
                                                        ),
                                                        
                                                    ],
                                                ),
                                                dcc.Graph(
                                                    className="salmon-timeseries", 
                                                    id="salmon-timeseries",
                                                                                         
                                                ),
                                            ],
                                        ),
                                    ],
                                ),                              
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H6(
                                    children=["Data Source",], 
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    1. Albion Chinook test fishery is located on the lower Fraser River at Albion, BC (near Fort Langley), Canada. The fishery collects data from early April to mid-October every year. Catching per unit effort, or CPUE, is defined as catch per thousand fathom minutes. Data is retrieved from the Fisheries and Oceans Canada [report website](https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242). Read more about the Albion Chinook gill net data set, such as what size of net is used, in this document on [Albion Chinook Gillnet](https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/docs/commercial/albionchinook-quinnat-eng.html). 
                                    2. Bonneville Dam data is retrieved from Columbia Basin Research [Adult Passage Queries](https://www.cbr.washington.edu/dart/query/adult_daily). Number of adult Chinook salmon passing through the Bonneville Dam was directly monitored April to October, with video monitoring covering the other months. See [Fish Passage Center] (https://www.fpc.org/adults/Q_adults_subsite.php) for more details. 
                                    '''),
                            ],
                        ),
                    ],
                ),
                #----------------------------Tab 2: Orca Viz-----------------------------------#
                dcc.Tab(
                    label='Southern Resident Orca', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Left Column
                                html.Div(
                                    className="left-half-column",
                                    id="orcamap-container",
                                    children=[
                                        html.Div(
                                                id="orca-dropdowns",
                                                children=[
                                                    html.H6("Southern Resident Orca Sightings"),
                                                    dcc.Dropdown(
                                                            value=2023,
                                                            className="year-dropdown",
                                                            id="year-dropdown",
                                                            options=[
                                                                {"label":"2023","value":2023,},
                                                                {"label":"2022","value":2022,},
                                                                {"label":"2021","value":2021,},
                                                                {"label":"2020","value":2020,},
                                                                {"label":"2019","value":2019,},
                                                                {"label":"2018","value":2018,},
                                                                {"label":"2017","value":2017,},
                                                                {"label":"2016","value":2016,},
                                                                {"label":"2015","value":2015,},
                                                                {"label":"2014","value":2014,},
                                                                {"label":"2013","value":2013,},
                                                                {"label":"2012","value":2012,},
                                                                {"label":"2011","value":2011,},
                                                                {"label":"2010","value":2010,},
                                                                {"label":"2009","value":2009,},
                                                                {"label":"2008","value":2008,},
                                                                {"label":"2007","value":2007,},
                                                                {"label":"2006","value":2006,},
                                                                {"label":"2005","value":2005,},
                                                                {"label":"2004","value":2004,},
                                                                {"label":"2003","value":2003,},
                                                                {"label":"2002","value":2002,},
                                                                {"label":"2001","value":2001,},                                                                
                                                                {"label":"2000","value":2000,},
                                                                {"label":"1999","value":1999,},
                                                                {"label":"1998","value":1998,},
                                                                {"label":"1997","value":1997,},
                                                                {"label":"1996","value":1996,},
                                                                {"label":"1995","value":1995,},
                                                                {"label":"1994","value":1994,},
                                                                {"label":"1993","value":1993,},
                                                                {"label":"1992","value":1992,},
                                                                {"label":"1991","value":1991,},
                                                                {"label":"1990","value":1990,},
                                                            ],
                                                        ),
                                                    dcc.Dropdown(
                                                            value="All pods",
                                                            className="pod-dropdown",
                                                            id="pod-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"L pod",
                                                                    "value":"L pod",
                                                                },
                                                                {
                                                                    "label":"K pod",
                                                                    "value":"K pod",
                                                                },
                                                                {
                                                                    "label":"J pod",
                                                                    "value":"J pod",
                                                                },
                                                                {
                                                                    "label":"All pods",
                                                                    "value":"All pods",
                                                                },
                                                            ],
                                                        ),                                                        
                                                    ],
                                                ),
                                                dcc.Graph(
                                                    className="orca-map",
                                                    id="orca-map",
                                                    animate=False,
                                                ),
                                    ],
                                ),
                                #Right column
                                html.Div(
                                    className="right-half-column", 
                                    children=[
                                        html.Div(
                                            className="salmon-orca-container",
                                            id="salmon-orca-container",                                           
                                            children=[
                                                html.H5("Why is Chinook Salmon important to Southern Resident Orcas?"),
                                                html.P("The Southern Resident killer whales, an iconic population of orcas found in the Pacific Northwest, face a critical threat to their survival due to the lack of chinook salmon. These majestic creatures, known for their intelligence and close-knit social structure, heavily rely on chinook salmon as their primary food source. However, the decline in chinook populations, caused by various factors including habitat degradation, overfishing, and dam construction, has left the Southern Resident orcas in a precarious state. With insufficient access to their preferred prey, these magnificent marine mammals struggle to meet their nutritional needs, resulting in malnutrition and overall population decline."),
                                                dcc.Graph(
                                                    className="salmon-orca-timeseries", 
                                                    id="salmon-orca-timeseries",                                      
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H6(
                                    children=[
                                        "Data Source",
                                    ],
                                    style={
                                        "margin-top":"1.8rem"
                                        },
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    1. Orca geolocation data are retrieved from [Acartia](https://acartia.io/home) and [the Whale Museum](whalemuseum.org). 
                                    2. Definition of central Salish Sea follows that of Monika Weiland in her talk about SRKW and Bigg's occupancy metrics.                                  
                                    '''),
                            ],
                        ),
                    ],
                ), 
            ],
        ),       
    ],
)
#-----------------------------------------------------------------------------#
#                                  Callback
# ----------------------------------------------------------------------------#
#~~~~~~~~~~~~~~~~~~~~~Salmon Time Series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("salmon-timeseries", "figure"),
    [
        Input("location-dropdown", "value"),
    ],
)
def update_salmon_timeseries(location_dropdown):
    if location_dropdown=="Bonneville Dam":
        # Define salmon time seires
        title='Bonneville Dam Adult Chinook Catch Count 3 recent years vs History'
        ylab='Count'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  
                        #--Year before last--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin'+str(twoyr)],
                        name=str(twoyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[2],
                        ),
                        opacity=0.85,     
                                ),
                        #--Last Year--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin'+str(lastyr)],
                        name=str(lastyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
                        #--This Year--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin'+str(curyr)],
                        name=str(curyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[0],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[0],
                        ),
                        opacity=0.85,     
                                ),
                        #--History--# 
                        go.Scatter(
                        x=bonnev['date'],
                        y=bonnev['chin_hist'],
                        name='Historical mean (1939-'+str(twoyr-1)+')',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[3],
                        ),
                        opacity=0.85,     
                                ),
                    ],
            )
        fig_salmon.update_layout(
                paper_bgcolor=bgcl, 
                plot_bgcolor=bgcl,
                margin=dict(l=0, t=0, b=0, r=0, pad=0),
                yaxis = dict(zeroline = False,
                            title=ylab,
                            color=framecl, 
                            showgrid=False,
                ),
                xaxis = dict(zeroline = False,
                            title=xlab,
                            color=framecl,
                            showgrid=False,
                            tickmode='array',
                            tickvals=['Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                            #nticks=10,
                            tickangle=45,
                ),
                font=dict(
                    family=plotfont, 
                    size=11, 
                    color=framecl,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=0.1
                ),
                title=dict(text = title,
                                    x = 0.1,
                                    y = 0.98,
                                    xanchor =  'left',
                                    yanchor = 'top',
                                    #pad = dict(
                                    #            t = 0
                                    #           ),
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
    elif location_dropdown=="Albion":
        # Define salmon time seires
        title='Albion Chinook Catch Per Unit Effort (CPUE) 3 recent years vs History'
        ylab='CPUE'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  
                        #--Year before last--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue'+str(twoyr)],
                        name=str(twoyr),
                        mode='lines+markers',
                        #mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[2],
                        ),
                        opacity=0.85,     
                                ),
                        #--Last Year--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue'+str(lastyr)],
                        name=str(lastyr),
                        mode='lines+markers',
                        #mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
                        #--This Year--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue'+str(curyr)],
                        name=str(curyr),
                        mode='lines+markers',
                        #mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[0],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[0],
                        ),
                        opacity=0.85,     
                                ),
                        #--History--# 
                        go.Scatter(
                        x=albion['date'],
                        y=albion['cpue_hist'],
                        name='Historical mean (1980-'+str(twoyr-1)+')',
                        #mode='lines+markers',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[3],
                        ),
                        opacity=0.85,     
                                ),
                    ],
            )
        fig_salmon.update_layout(
                paper_bgcolor=bgcl, 
                plot_bgcolor=bgcl,
                margin=dict(l=0, t=0, b=0, r=0, pad=0),
                yaxis = dict(zeroline = False,
                            title=ylab,
                            color=framecl, 
                            showgrid=False,
                ),
                xaxis = dict(zeroline = False,
                            title=xlab,
                            color=framecl,
                            showgrid=False,
                            tickmode='array',
                            tickvals=['Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1'],
                            #nticks=10,
                            tickangle=45,
                ),
                font=dict(
                    family=plotfont, 
                    size=11, 
                    color=framecl,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=0.1
                ),
                title=dict(text = title,
                                    x = 0.1,
                                    y = 0.98,
                                    xanchor =  'left',
                                    yanchor = 'top',
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
    elif location_dropdown=="Albion v Bonneville":
        # Define salmon time seires
        if today.month<=4:
            albbon=create_lagged(curyr, 0, 0)
            albbon_ly=create_lagged(lastyr, 0, 0)
            albbon=albbon.merge(albbon_ly[['m','day','chin'+str(lastyr),'cpue'+str(lastyr)]], how='left',on=['m','day'])
        else:
            albbon=create_lagged(curyr, 0, 0)
        title='Albion Chinook vs Bonneville Dam'
        ylab='CPUE'
        xlab='Date'
        fig_salmon = make_subplots(specs=[[{"secondary_y": True}]])
        fig_salmon.add_trace(
                go.Scatter(
                        x=albbon['date'],
                        y=albbon['cpue'+str(curyr)],
                        name='Albion'+str(curyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[0],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[0],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=False,
        )
        if today.month<=4:
            fig_salmon.add_trace(
                go.Scatter(
                        x=albbon['date'],
                        y=albbon['cpue'+str(lastyr)],
                        name='Albion'+str(lastyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[1],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[1],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=False,
            )
        fig_salmon.add_trace(
                go.Scatter(
                        x=albbon['date'],
                        y=albbon['cpue_hist'],
                        name='Albion historical mean',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[2],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[2],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=False,
        )
        fig_salmon.add_trace(
            go.Scatter(
                        x=albbon['date'],
                        y=albbon['chin'+str(curyr)],
                        name='Bonneville'+str(curyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[3],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[3],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=True,
        )
        if today.month<=4:
            fig_salmon.add_trace(
            go.Scatter(
                        x=albbon['date'],
                        y=albbon['chin'+str(lastyr)],
                        name='Bonneville'+str(lastyr),
                        mode='lines+markers',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[4],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[4],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=True,
            )
        fig_salmon.add_trace(
            go.Scatter(
                        x=albbon['date'],
                        y=albbon['chin_hist'],
                        name='Bonneville historical mean',
                        mode='lines',
                        hovertemplate='%{x}'+':%{y}',
                        marker = go.scatter.Marker(
                                    color = plotlycl[5],
                        ),
                        line = go.scatter.Line(
                                    color = plotlycl[5],
                        ),
                        opacity=0.85,     
                                ),
            secondary_y=True,
        )
        fig_salmon.update_yaxes(title_text="CPUE (Albion)", secondary_y=False)
        fig_salmon.update_yaxes(title_text="Count (Bonneville)", secondary_y=True)

        fig_salmon.update_layout(
                paper_bgcolor=bgcl, 
                plot_bgcolor=bgcl,
                margin=dict(l=0, t=0, b=0, r=0, pad=0),
                yaxis = dict(zeroline = False,
                            color=framecl, 
                            showgrid=False,
                ),
                xaxis = dict(zeroline = False,
                            title=xlab,
                            color=framecl,
                            showgrid=False,
                            tickmode='array',
                            tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                            #nticks=10,
                            tickangle=45,
                ),
                font=dict(
                    family=plotfont, 
                    size=11, 
                    color=framecl,
                ),
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.9,
                    xanchor="left",
                    x=0.1
                ),
                title=dict(text = title,
                                    x = 0.1,
                                    y = 0.98,
                                    xanchor =  'left',
                                    yanchor = 'top',
                                    #pad = dict(
                                    #            t = 0
                                    #           ),
                                    font = dict(
                                                #family='Courier New, monospace',
                                                size = 14,
                                                #color='#000000'
                                                )
                                    ),
            )
        fig_salmon.update_traces(connectgaps=True)
    return fig_salmon

#~~~~~~~~~~~~~~~~~~~~~Orca Map~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("orca-map", "figure"),
    [
        Input("pod-dropdown", "value"),
        Input("year-dropdown","value")
    ],
)
#%%
def update_orca_map(pod,year):
    if year>2021:      
        srkw_dat=srkw_acartia_map(year, pod)
    elif year>2017:
        srkw_dat0=srkw_acartia_map(year, pod)
        srkw_dat1=srkw_twm_map(year, pod)
        srkw_dat=pd.concat([srkw_dat0, srkw_dat1])
    else:
        srkw_dat=srkw_twm_map(year, pod)
    fig_orcamap = go.Figure()
    fig_orcamap.add_trace(go.Scattermapbox(
            lat=srkw_dat['latitude'],
            lon=srkw_dat['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                color=srkw_dat.mon_frac,
                size=7,
                colorscale=viri12cl,
                opacity=0.75,
                showscale=True,
                colorbar=dict(
                    title='Month',
                    thickness=20,
                    titleside='right',
                    outlinecolor='rgba(68,68,68,0)',
                    ticks='outside',
                    ticklen=3,
                    tickmode='array',
                    tickvals=viri12pt,
                    ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"
                    ],
                ),     
            ),
            text=srkw_dat['created'],
            hoverinfo='text'
        ))
    fig_orcamap.update_layout(
        autosize=True,
        showlegend=False,
        uirevision=True,
        margin=dict(l=0, r=0, t=0, b=0),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=dict(
                lat=47.635470,
                lon=-122.457417
            ),
            zoom=6,
            style='light'
        ),
    )
    return fig_orcamap
#%%
#~~~~~~~~~~~~~~~~~~~~~Orca Time series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("salmon-orca-timeseries", "figure"),
    [
        Input("pod-dropdown", "value"),
    ],
)
def update_orca_lines(pod):
    if pod=="All pods":
        pod_tag=""
        srkw_cs_peak=srkw_cs_all_peak
        srkw_interc=srkw_all_interc
        srkw_slope=srkw_all_slope
        srkw=srkwdata_all
    elif pod=="J pod":
        pod_tag="[J]"
        srkw_cs_peak=srkw_cs_j_peak
        srkw_interc=srkw_j_interc
        srkw_slope=srkw_j_slope   
        srkw=srkwdata_j
    elif pod=="K pod":
        pod_tag="[K]"
        srkw_cs_peak=srkw_cs_k_peak
        srkw_interc=srkw_k_interc
        srkw_slope=srkw_k_slope
        srkw=srkwdata_k
    elif pod=="L pod":
        pod_tag="[L]"
        srkw_cs_peak=srkw_cs_l_peak
        srkw_interc=srkw_l_interc
        srkw_slope=srkw_l_slope   
        srkw=srkwdata_l 

    fig_peak = make_subplots(rows=2,cols=1,
                         subplot_titles=['','Orca Population'],
                         row_heights=[0.7,0.3],
    specs=[[{"secondary_y": False}],[{"secondary_y": True}]]
    )
    fig_peak.add_trace(
            go.Scatter(
                x=srkw_cs_peak['year'],
                y=srkw_cs_peak['peakday'],
                name=f'Orca sightings peak day {pod_tag}',
                mode='markers',
                hovertemplate='%{y} day'+', %{x}',
                marker = go.scatter.Marker(
                            color = plotlycl[0],
                            symbol="triangle-ne",
                    ),
                    opacity=0.85, 
            ),row=1, col=1,
    )
    fig_peak.add_trace(
        go.Scatter(
            x=srkw_cs_peak['year'], 
            y=srkw_interc+srkw_slope*srkw_cs_peak['year'],
            mode='lines',
            name=f'Orca peak line {pod_tag}',
            line=go.scatter.Line(color=plotlycl[0]),
            showlegend=False,
        ),row=1, col=1,
    )
    fig_peak.add_trace(
            go.Scatter(
                x=apeak['year'],
                y=apeak['peakday'],
                name='Chinook at Albion peak day',
                mode='markers',
                hovertemplate='%{y} day'+', %{x}',
                marker = go.scatter.Marker(
                            color = plotlycl[1],
                            symbol="triangle-ne", 
                    ),
                    opacity=0.85, 
            ),row=1, col=1,
    )
    fig_peak.add_trace(
        go.Scatter(
            x=apeak['year'], 
            y=albion_interc+albion_slope*apeak['year'],
            mode='lines',
            name='Albion peak line',
            line=go.scatter.Line(color=plotlycl[1]),
            showlegend=False,
        ),row=1, col=1,
    )

    #---SRKW Population---#
    fig_peak.add_trace(
            go.Scatter(
                x=srkw['year'],
                y=srkw['SRKW'],
                name=f"Orca Number {pod}",
                mode='lines+markers',
                hovertemplate='%{x}'+':%{y}',
                marker = go.scatter.Marker(
                            color = plotlycl[0],
                            symbol="star",
                    ),
                line = go.scatter.Line(
                            color = plotlycl[0],
                            dash='dot',
                    ),
                    opacity=0.85, 
            ), secondary_y=False,row=2, col=1,
    )
    #---Albion Salmon Sum---#
    fig_peak.add_trace(
        go.Scatter(
                x=albionpd['year'],
                y=albionpd['alb_cpue'], 
                name='Chinook at Albion',
                mode='lines+markers',
                hovertemplate='%{x}'+':%{y}',
                marker = go.scatter.Marker(
                            color = plotlycl[1],
                            symbol="star",
                    ),
                line = go.scatter.Line(
                            color = plotlycl[1],
                            dash="dot",
                    ),
                    opacity=0.85, 
            ),secondary_y=True,row=2, col=1,
    )
    fig_peak.update_yaxes(title_text="Peak day of the year", tickvals=list(range(150,300,50)), range=[140, 300], row=1, col=1)
    fig_peak.update_yaxes(title_text="Number of Orca", row=2, col=1, secondary_y=False)
    fig_peak.update_yaxes(title_text="Albion Chinook CPUE", row=2, col=1, secondary_y=True)
    fig_peak.update_xaxes(title_text="Year",tickvals=list(range(1990,curyr,5)),range=[1989, 2023], row=1, col=1)
    fig_peak.update_xaxes(title_text="Year",tickvals=list(range(1990,curyr,5)),range=[1989, 2023], row=2, col=1)

    fig_peak.update_layout(
            paper_bgcolor=bgcl, 
            plot_bgcolor=bgcl,
            margin=dict(l=0, t=0, b=0, r=0, pad=0),
            yaxis = dict(zeroline = False,
                        color=framecl, 
                        showgrid=False,
            ),
            xaxis = dict(zeroline = False,
                        color=framecl,
                        showgrid=False,
            ),
            font=dict(
                family=plotfont, 
                size=11, 
                color=framecl,
            ),
            legend=dict(
                y=0.9,
            ),
            title=dict(text = "Peak day of Chinook Volume at Albion and Southern Resident Orca Sightings in Central Salish Sea",
                                x = 0.02,
                                y = 1,
                                xanchor = 'left',
                                yanchor = 'top',
                                pad = dict(
                                           t = 1
                                          ),
                                font = dict(
                                            family='Arial, sans-serif',
                                            size = 16,
                                            #color='#000000'
                                            )
                                ),
        )
    return fig_peak

if __name__ == '__main__':
    app.run_server(debug=True)
