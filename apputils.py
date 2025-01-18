import os
from os.path import join as pjoin
import pathlib
from datetime import date
from datetime import datetime as dt 
import calendar

import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 
import numpy as np
from utils import str2mon, conv_npdt64, conv_to_date
import dash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
from plotly.express.colors import sample_colorscale

## ----------------Functions to process salmon data ---------------------##
def load_albion(fos_path):
    curyr=date.today().year
    ayl=[y for y in range(1980, curyr+1)] #year list for Albion
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
    #albion['date']=albion[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
    albionpd=pd.DataFrame({'year':ayl[:-1], 'alb_cpue':albion_cpue[:-1]}, columns=['year','alb_cpue'])
    return albion, albionpd

def load_bon(bon_path):    
    curyr=date.today().year
    byl=[y for y in range(1939, curyr+1)] #year list for Bonneville Dam
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
    return bonnev

def load_wash(path):    
    curyr=date.today().year
    yl=[y for y in range(2024, curyr)] #year list for Bonneville Dam
    wash=pd.DataFrame(columns=['day','m'])
    for i in reversed(range(len(yl))):
        d=pd.read_csv(path+str(yl[i])+'.csv',\
            usecols=['Date','Daily Count',])
        d['m']=d.apply(lambda x: x["Date"].split("/")[0], axis=1)
        d['day']=d.apply(lambda x: x["Date"].split("/")[1], axis=1)        
        d=d.rename(columns={'Daily Count':'chin'+str(yl[i])})
        d=d.drop(columns=['Date',])
        d["sort_val"]=d.apply(lambda x: date(yl[i], int(x['m']), int(x['day'])), axis=1)
        wash=pd.merge(left=wash, right=d, how='outer', on=['m','day'])
        wash=wash.sort_values(by="sort_val")
        wash=wash.drop(columns=['sort_val'])        
    del(d,i)
    wash['month']=wash['m'].apply(lambda x: dt.strptime(str(x), '%m').strftime('%b'))
    wash['date']=wash[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
    return wash

def calendar_template(bonnev, leap=False):
    """
    Use Bonneville data to create a calendar tempalte 
    Example data frame
    date  m day
    Jan-1 1 1 
    """
    if leap: # Create calendar dataframes for leapyear 
        cal=bonnev[['date']]
        cal['date1']=pd.to_datetime(cal['date'].apply(lambda x: str(2020)+'-'+x), errors='coerce', format='%Y-%b-%d')
        cal['m']=pd.DatetimeIndex(cal['date1']).month.astype('int')
        cal['day']=pd.DatetimeIndex(cal['date1']).day.astype('int')
        cal=cal.drop(columns=['date1'])
    else:
        cal=bonnev[['date']]
        cal=cal[cal['date']!='Feb-29']
        cal['date1']=pd.to_datetime(cal['date'].apply(lambda x: str(2021)+'-'+x), format='%Y-%b-%d')
        cal['m']=pd.DatetimeIndex(cal['date1']).month
        cal['day']=pd.DatetimeIndex(cal['date1']).day
        cal=cal.drop(columns=['date1'])
    return cal

def create_lagged(year, 
    albion, #albion data in wide format
    bonnev, #bonneville data in wide format     
    lag1, # Albion lag
    lag2  # Bonneville lag
    ):
    # Create calendar dataframes 
    cal=calendar_template(bonnev)
    cal_leap=calendar_template(bonnev, leap=True)
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

## ----------------Functions to make data for SRKW map ---------------------##
def acartia_map_preproc(year, acartia_path, pod="All pods"):
    """
    Function to process arcartia srkw data for maps
    1) make make day of year and mon_frac for colorbar scaling 
    2) make tag and source variable 
    3) if a pod is specified, filter out other pod data 
    """
    clr12pt=np.linspace(0.083,1,12)
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc=srkwc[~srkwc.date.isnull()]
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    srkwc['mon']=srkwc['date2'].apply(lambda x: x.month)
    srkwc['mon_frac']=srkwc['mon'].apply(lambda x: clr12pt[int(x)-1])
    srkwc['day_of_year']=srkwc['date_ymd'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    srkwc['tag']="[Acartia]"+srkwc['created']
    srkwc['source']='arcartia'
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

def twm_map_preproc(year, twm_path, pod="All pods"):
    """
    Function to process twm srkw data for maps
    1) make make day of year and mon_frac for colorbar scaling 
    2) make tag and source variable 
    3) if a pod is specified, filter out other pod data 
    """
    clr12pt=np.linspace(0.083,1,12)
    srkwc=pd.read_csv(twm_path+"twm"+str(year)+".csv")
    srkwc['mon_frac']=srkwc['Month'].apply(lambda x: clr12pt[int(x)-1])
    srkwc['day_of_year']=srkwc['SightDate'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
    srkwc['created']=srkwc['SightDate']+" "+srkwc['Time1']
    srkwc['tag']="[TWM]"+srkwc['created']
    srkwc['source']='twm'
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
    return srkw_dat[['created','mon_frac','latitude','longitude','tag','source']]

## ----------------Functions to make data for SRKW Lineplot ---------------------##
def srkw_count(dat, count_orca=False):
    """
    Function to count srkw reports or counts by day 
    Called in acartia_count_year() and twm_count_year()
    """
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

def acartia_count_year(year, acartia_path, pod="All pods"):
    """
    Function to make orca count data of a certain year and merge with salmon data
    """
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    entry_lat=48.19437 # Define the north and south puget sound latitude
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

# Load The Whale Museum Data 
def twm_count_year(year, twm_path, pod="All pods"):
    clr12pt=np.linspace(0.083,1,12)
    srkwc=pd.read_csv(twm_path+"twm"+str(year)+".csv")
    # Define the north and south puget sound latitude
    entry_lat=48.19437
    srkwc['north_puget_sound']=srkwc['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
    srkwc['mon_frac']=srkwc['Month'].apply(lambda x: clr12pt[int(x)-1])
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


def srkw_count_year(type, year, d_path, pod="All pods"):
    """
    Function to make orca count data of a certain year and merge with salmon data
    """
    clr12pt=np.linspace(0.083,1,12)
    srkwc=pd.read_csv(d_path+"srkw_"+str(year)+".csv")
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
    entry_lat=48.19437 # Define the north and south puget sound latitude
    srkwc['north_puget_sound']=srkwc['latitude'].apply(lambda x: 1 if x>entry_lat else 0)
    if type=="twm": 
        srkwc['mon_frac']=srkwc['Month'].apply(lambda x: clr12pt[int(x)-1])
        srkwc['day_of_year']=srkwc['SightDate'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
        srkwc['date_ymd']=srkwc['SightDate']
        srkwc['created']=srkwc['SightDate']+" "+srkwc['Time1']

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
        if type=="twm":
            srkw_dat=srkwc
        else:
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

def peak_chinook(curyr, fos_path, bon_path, loc="Albion", year_zero=1990):
    ayl=[y for y in range(year_zero, curyr)] #year list for Albion up till last year
    byl=[y for y in range(year_zero, curyr)] #year list for Bonneville Dam up till last year
    peak_vals=[]
    peak_dates=[]
    peak_days=[]       
    peak_p95_df=[]
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
            #95 percentile          
            peak_p95=np.percentile(d['cpue1'], 95)
            d_p95=d[d['cpue1']>=peak_p95]
            d_p95['date']=d_p95.apply(lambda x: date(yr, str2mon(x['mon']), int(x['day'])) ,axis=1)
            d_p95['peak_day']=d_p95['date']-date(yr, 1, 1)
            d_p95['peak_day']=d_p95['peak_day'].apply(lambda x: x.days)
            peak_p95_df.append(d_p95)
    elif loc=="Bonneville":
        for i in range(len(byl)):
            d=pd.read_csv(bon_path+'bon'+str(byl[i])+'.csv',\
                    usecols=['Project','Date','Chin'])
            yr=byl[i]
            peak_val=max(d['Chin'].dropna())
            peak_p95=np.percentile(d['Chin'].dropna(), 95)
            peak_row=d[d['Chin']==peak_val]
            peak_date=dt.strptime(peak_row.Date.values[0], '%Y-%m-%d').date()
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)  
            #95 percentile          
            peak_p95=np.percentile(d['Chin'].dropna(), 95)
            d_p95=d[d['Chin']>=peak_p95]
            d_p95['peak_day']=d_p95['Date']-date(yr, 1, 1)
            d_p95['peak_day']=d_p95['peak_day'].apply(lambda x: x.days)
            peak_p95_df.append(d_p95)              
    else:
        raise ValueError("Location other than 'Albion' and 'Bonneville'")
    return peak_vals, peak_dates, peak_days, peak_p95_df

def peak_srkw(curyr, twm_path, acartia_path, src="twm", pod="", loc="", year_zero=1990):
    tyl=[y for y in range(year_zero, 2022)] #year list for data from The Whale Museum
    ayl=[y for y in range(2018, curyr)] #year list for data from Acartia
    byl=[y for y in range(year_zero, curyr)] #year list for data from both The Whale Museum plus Acartia
    peak_vals=[]
    peak_dates=[]
    peak_days=[]  
    peak_p95_df=[]    
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
        # d2['date2']=d2['date2'].apply(lambda x: conv_npdt64(x) if isinstance(x, np.datetime64) else x )
        d2=d2.rename(columns={"date2":"SightDate"})
        acartia_data.append(d2)
        # print(acartia_data)
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
            #95 percentile          
            peak_p95=np.percentile(d['count'], 95)
            d_p95=d[d['count']>=peak_p95]
            d_p95['peak_day']=d_p95['Date']-date(yr, 1, 1)
            d_p95['peak_day']=d_p95['peak_day'].apply(lambda x: x.days)
            peak_p95_df.append(d_p95)                    
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
            #95 percentile          
            peak_p95=np.percentile(d['count'], 95)
            d_p95=d[d['count']>=peak_p95]
            d_p95['peak_day']=d_p95['Date']-date(yr, 1, 1)
            d_p95['peak_day']=d_p95['peak_day'].apply(lambda x: x.days)
            peak_p95_df.append(d_p95)         
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
            d=d.rename(columns={'SightDate':'Date',})   
            peak_val=max(d['count'])
            peak_row=d[d['count']==peak_val]
            peak_date=peak_row['Date'].values[0]
            if isinstance(peak_date, np.datetime64):
                peak_date=pd.to_datetime(peak_date).date()
            peak_day=peak_date-date(yr,1,1)
            peak_vals.append(peak_val)
            peak_dates.append(peak_date)
            peak_days.append(peak_day.days)   
            #95 percentile          
            peak_p95=np.percentile(d['count'], 95)
            d_p95=d[d['count']>=peak_p95]
            d_p95['Date']=d_p95["Date"].apply(lambda x: pd.to_datetime(x).date() if isinstance(peak_date, np.datetime64) else x)
            d_p95['peak_day']=d_p95['Date'].apply(lambda x: x.date()-date(yr, 1, 1) if isinstance(x, pd._libs.tslibs.timestamps.Timestamp) else x-date(yr, 1, 1))
            peak_p95_df.append(d_p95)
    else:
        raise ValueError("Source other than 'twm' and 'acartia'")
    return peak_vals, peak_dates, peak_days, peak_p95_df

def apeak_df(curyr, fos_path, bon_path):
    year_zero=1990
    albion_yl4peak=[y for y in range(year_zero, curyr+1)]
    apeak=pd.DataFrame()
    apeak95=pd.DataFrame()
    apv, apdt, apdy, apdf=peak_chinook(curyr, fos_path, bon_path, loc="Albion", year_zero=year_zero)
    apeak['year']=albion_yl4peak[:-1]
    apeak['peakvals']=apv 
    apeak['peakdate']=apdt 
    apeak['peakday']=apdy

    peakdays95=[]
    peakyr95=[]
    for i in range(len(albion_yl4peak)-1):
        yr=albion_yl4peak[i]
        adf95=apdf[i]
        adf95_len=adf95.shape[0]
        peakdays95+=list(adf95['peak_day'])
        peakyr95+=[yr]*adf95_len
    apeak95['year']=peakyr95
    apeak95['peakday']=peakdays95

    return apeak, apeak95 

def srkw_peak_df(curyr, twm_path, acartia_path):
    year_zero=1990
    srkw_cs_pv, srkw_cs_pdt, srkw_cs_pdy, srkw_cs_df=peak_srkw(curyr, twm_path, acartia_path, src="both", loc="central salish")
    srkw_cs_peak=pd.DataFrame()
    srkw_cs_peak['year']=[y for y in range(year_zero, curyr)]
    srkw_cs_peak['peakvals']=srkw_cs_pv 
    srkw_cs_peak['peakdate']=srkw_cs_pdt
    srkw_cs_peak['peakday']=srkw_cs_pdy

    srkw_cs_peak95=pd.DataFrame()
    peakdays95=[]
    peakyr95=[]
    srkw_yrs=[y for y in range(year_zero, curyr)]
    for i in range(len(srkw_yrs)-1):
        yr=srkw_yrs[i]
        srkw_cs_df95=srkw_cs_df[i]
        srkw_cs_df95_len=srkw_cs_df95.shape[0]
        peakdays95+=list(srkw_cs_df95['peak_day'])
        peakyr95+=[yr]*srkw_cs_df95_len
    srkw_cs_peak95['year']=peakyr95
    srkw_cs_peak95['peakday']=peakdays95

    return srkw_cs_peak, srkw_cs_peak95