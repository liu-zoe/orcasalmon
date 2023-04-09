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
import pytz
from pytz import timezone

import pandas as pd
pd.options.mode.chained_assignment = None #suppress chained assignment 

import numpy as np

import dash
from dash import dcc
from dash import html 
from dash.dependencies import Input, Output, State
import dash_daq as daq 

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
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

#Define data path
fos_path=pjoin(APP_PATH,'data/foschinook/')
bon_path=pjoin(APP_PATH,'data/bonchinook/')
acartia_path=pjoin(APP_PATH, 'data/acartia/')
srkw_sattellite_path=pjoin(APP_PATH, 'data/srkw_satellite_tagging')
#%%
#Load Albion data
albion=pd.DataFrame(columns=['day','m'])
for i in reversed(range(len(ayl))):
    d=pd.read_csv(fos_path+'fos'+str(ayl[i])+'.csv',\
        usecols=['day','mon','cpue1'])
    d['m']=d['mon'].apply(lambda x: dt.strptime(x, '%b').month)
    d=d.drop(columns='mon')
    d=d.rename(columns={'cpue1':'cpue'+str(ayl[i])})
    albion=pd.merge(left=albion, right=d, how='outer', on=['m','day'], sort=True)
del(d,i)
albion['cpue_hist']=albion.iloc[:,5:].mean(axis=1, skipna=True).round(decimals=2) #History up to 3 years ago
albion['cpue_hist2']=albion.iloc[:,3:].mean(axis=1, skipna=True).round(decimals=2) #History up to last year
albion['month']=albion['m'].apply(lambda x: dt.strptime(str(x), '%m').strftime('%b'))
albion['date']=albion[['month','day']].apply(lambda x: '-'.join(x.values.astype(str)), axis="columns")
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
    #bonnev_lagged=bonnev_lagged[bonnev_lagged['year2']<year]
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
# Loading Acartia data
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
# Function to make orca count data of a certain year and merge with salmon data
def srkw_year(year, pod="All pods"):
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
    if year in (2019, 2018):
        srkwc_north_avg=srkw_count(srkwc_north, count_orca=False)
    else:
        srkwc_north_avg=srkw_count(srkwc_north, count_orca=True)
    srkwc_north_avg.columns=['date','count_north','day','m']

    srkwc_south=srkw_dat[srkw_dat['north_puget_sound']==0]
    if year in (2019, 2018):
        srkwc_south_avg=srkw_count(srkwc_south, count_orca=False)
    else:
        srkwc_south_avg=srkw_count(srkwc_south, count_orca=True)
    srkwc_south_avg.columns=['date','count_south','day','m']

    srkw_yrcount=srkw_count(srkwc, count_orca=True)
    
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
srkw_curyr_count=srkw_year(curyr)
current_orca="J26"
# %%
# Create data for salmon data locations
salmon_loc = pd.DataFrame(columns=['loc','lon','lat','color','size'])
salmon_loc['loc']=['Puget Sound','Bonneville Dam','Albion Test Fishery']
salmon_loc['lat']=[47.635470, 45.644456, 49.181376]
salmon_loc['lon']=[-122.457417,-121.940530, -122.567295]
# %%
# Load in SRKW Satellite Tagging data
# Functions gmt2pst: convert GMT time to Pacific Time
def gmt2pst(yr,mon,day,h,m,s):
    tz=pytz.timezone('GMT')
    _date1=dt(yr, mon, day,h,m,s, tzinfo=tz)
    _date2=_date1.astimezone(timezone('US/Pacific'))
    return(_date2)
# Function orcaday: create number of days of orca movement from the earliest record
def orcaday(dat):
    day0=min(dat['date'])
    dat['day_move']=dat['date'].apply(lambda x: x-day0)
# Function geogen: create longitude and latitide 
def geogen(dat):
    import numpy as np
    dat['lon']=np.where(dat['lon_p']>-120, dat['lon_a'],dat['lon_p'])
    dat['lat']=np.where(dat['lon_p']>-120, dat['lat_a'],dat['lat_p'])

satellite_fname="SRKW occurrence coastal - SRKW occurrence coastal Data.csv"
satellite=pd.read_csv(pjoin(srkw_sattellite_path, satellite_fname))
satellite=satellite.rename(columns={'Lat P':'lat_p', 'Lon P':'lon_p', 'Lat A':'lat_a','Lon A':'lon_a'})
satellite=satellite[['Animal', 'lat_p', 'lon_p', 'lat_a',
       'lon_a', 'Dur', 'Sex', 'Popid', 
       'Month', 'Day', 'Year', 'Hour', 'Minute', 'Second']]
satellite['Popid']=satellite['Popid'].apply(lambda x: x.replace(' ',''))
satellite['datetime_pst']=satellite.apply(lambda x: gmt2pst(x.Year, x.Month, x.Day, x.Hour, x.Minute, x.Second), axis=1)
satellite=satellite.drop(columns=['Year','Month','Day','Hour','Minute','Second'])
satellite['date']=satellite.apply(lambda x: x.datetime_pst.date(), axis=1)
satellite['time']=satellite.apply(lambda x: x.datetime_pst.time(), axis=1)
satellite['year']=satellite.apply(lambda x: x.date.year, axis=1)
satellite['month']=satellite.apply(lambda x: x.date.month, axis=1)
satellite['day']=satellite.apply(lambda x: x.date.day, axis=1)
satellite['hour']=satellite.apply(lambda x: x.time.hour, axis=1)
satellite['minute']=satellite.apply(lambda x: x.time.minute, axis=1)
satellite['second']=satellite.apply(lambda x: x.time.second, axis=1)
satellite['day_of_year']=satellite['date'].apply(lambda x: pd.Period(x, freq='D').day_of_year)
satellite_j26=satellite[satellite.Popid=='J26']
satellite_j27=satellite[satellite.Popid=='J27']
satellite_k25=satellite[satellite.Popid=='K25']
satellite_k33=satellite[satellite.Popid=='K33']
satellite_l84=satellite[satellite.Popid=='L84']
satellite_l87=satellite[satellite.Popid=='L87']
satellite_l88=satellite[satellite.Popid=='L88']
satellite_l95=satellite[satellite.Popid=='L95']
# make an initial list of timestamps with j26
def make_slider_mark(indat, skip=0): 
    mark_index=[]
    timelist=[]
    i=indat.shape[0]-1
    while (i>=0):
        mark_index.append(i)
        #date='-'.join(str(indat['date'].values[i]).split('-')[1:])
        #time=':'.join(str(indat['time'].values[i]).split(':')[1:])
        date=str(indat['date'].values[i])
        time=str(indat['time'].values[i])
        timelist.append(date+" "+time)
        i-=(skip+1)
    mark_index.reverse()
    timelist.reverse()
    return(mark_index, timelist)
mark_index, timelist=make_slider_mark(satellite_j26)
# %%
# Create a color scheme and fonts
plotlycl=px.colors.qualitative.Plotly
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
                    html.Img(id="logo", src=app.get_asset_url("wordlogo-seagreen.png"),
                    style={'height':'20%', 'width':'20%'}
                    ),
                    html.H3(children="Chinook and Orca",
                            style={'textAlign': 'left',},
                    ),
                    dcc.Markdown(
                        id="description",
                        children=
                        '''
                        A dash board to monitor Chinook salmon population and Orca movement around Puget Sound                     
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
                                #Left Column
                                html.Div(
                                    className="left-column", 
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
                                                            value="Albion",
                                                            className="location-dropdown",
                                                            id="location-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"Albion",
                                                                    "value":"Albion",
                                                                },
                                                                {
                                                                    "label":"Bonneville Dam",
                                                                    "value":"Bonneville Dam",
                                                                },
                                                                {
                                                                    "label":"Albion v Bonneville", 
                                                                    "value":"Albion v Bonneville"
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
                                #Right column
                                html.Div(
                                    className="right-column",
                                    id="map-container",
                                    children=[
                                        dcc.Graph(
                                            className="salmon-map",
                                            id="salmon-map",
                                            animate=False, 
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H5(
                                    [
                                        "Data Source",
                                    ]
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
                    label='Orca Map', 
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
                                                    html.H6("Orca Sightings"),
                                                    dcc.Dropdown(
                                                            value=2023,
                                                            className="year-dropdown",
                                                            id="year-dropdown",
                                                            options=[
                                                                {
                                                                    "label":"2023",
                                                                    "value":2023,
                                                                },
                                                                {
                                                                    "label":"2022",
                                                                    "value":2022,
                                                                },
                                                                {
                                                                    "label":"2021",
                                                                    "value":2021,
                                                                },
                                                                {
                                                                    "label":"2020",
                                                                    "value":2020,
                                                                },
                                                                {
                                                                    "label":"2019",
                                                                    "value":2019,
                                                                },
                                                                {
                                                                    "label":"2018",
                                                                    "value":2018,
                                                                },
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
                                                html.H5("Number of Orcas vs Chinook"),
                                                html.P("Chinook data adjusted for travel distance"),
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
                                html.H5(
                                    [
                                        "Data Source",
                                    ]
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    1. Orca sightings data is retrieved from [Acartia](https://acartia.io/home).  
                                    2. Definition of central Salish Sea follows that of Monika Weiland in her talk talk about SRKW and Bigg's occupancy metrics.                                  
                                    '''),
                            ],
                        ),
                    ],
                ), 
                #----------------------------Tab 3: Orca Move-----------------------------------#
                # dcc.Tab(
                #     label='Orca Movement', 
                #     className='custom-tab',
                #     selected_className='custom-tab--selected',
                #     children=[
                #         html.Div(
                #             className="app-container", 
                #             children=[
                #                 html.Div(
                #                     className="left-column",
                #                     children=[
                #                         html.Div(
                #                             className="bubblemap-container",
                #                             id="bubblemap-container",
                #                             children=[
                #                                 html.H5(
                #                                     "Southern Reisdent Killer Whales Movement from Satellite Tagging Data",
                #                                     className="bubblemap-title",
                #                                     id="bubblemap-title",
                #                                     style={"textAlign":"left"},
                #                                 ),
                #                                 html.Div(
                #                                     className="slider-container",
                #                                     id="slider-container",
                #                                     children=[
                #                                         dcc.Interval(
                #                                             id='auto-stepper',
                #                                             interval=0.5*1000, # in ms
                #                                             n_intervals=0,
                #                                             max_intervals=0, 
                #                                             disabled=False,
                #                                         ),
                #                                         dcc.Slider(
                #                                             id="date-slider",
                #                                             min=0,
                #                                             max=len(mark_index)-1,
                #                                             value=0,
                #                                         ),
                #                                     ],
                #                                 ),
                #                                 dcc.Graph(
                #                                     className="satellite-bubble",
                #                                     id="satellite-bubble",
                #                                 )
                #                             ],
                #                         ),        
                #                     ],
                #                 ),
                #                 html.Div(
                #                     className="right-column",
                #                     children=[
                #                         html.Div(
                #                             className="orca-dropdown",
                #                             id="orca-dropdown",
                #                             children=[
                #                                 #html.H6("Select Orca"),
                #                                 dcc.Dropdown(
                #                                     value="J26",
                #                                     className="orca-picker",
                #                                     id="orca-picker",
                #                                     options=[
                #                                         {
                #                                             "label":"J26",
                #                                             "value":"J26",
                #                                         },
                #                                         {
                #                                             "label":"J27",
                #                                             "value":"J27",
                #                                         },
                #                                         {
                #                                             "label":"K25",
                #                                             "value":"K25",
                #                                         },
                #                                         {
                #                                             "label":"K33",
                #                                             "value":"K33",
                #                                         },
                #                                         {
                #                                             "label":"L84",
                #                                             "value":"L84",
                #                                         },
                #                                         {
                #                                             "label":"L87",
                #                                             "value":"L87",
                #                                         },
                #                                         {
                #                                             "label":"L88",
                #                                             "value":"L88",
                #                                         },
                #                                         {
                #                                             "label":"L95",
                #                                             "value":"L95",
                #                                         },
                #                                     ],
                #                                 ),
                #                                 html.Div(
                #                                     className="button-container",
                #                                     id="button-container",
                #                                     children=[
                #                                         html.Button(
                #                                             id="play-button",
                #                                             children="play",
                #                                             n_clicks=0,
                #                                             n_clicks_timestamp=-1,
                #                                             type='button',
                #                                             style={
                #                                                 'color':"#a2d1cf",
                #                                                 'textAlign':'center'
                #                                             },
                #                                         ),
                #                                         html.Button(
                #                                             id="pause-button",
                #                                             children="Pause",
                #                                             n_clicks=0,
                #                                             n_clicks_timestamp=-1,
                #                                             type='button',
                #                                             style={
                #                                                 'color':"#a2d1cf",
                #                                                 'textAlign':'center'
                #                                             },
                #                                         ),
                #                                     ],
                #                                 ),
                #                                 html.Div(
                #                                     children=[
                #                                         html.H6(
                #                                             id="orcamove-date",
                #                                             children=str(satellite_j26['date'].values[0]),
                #                                         ),
                #                                         daq.LEDDisplay(
                #                                             id="LED-time",
                #                                             color="#a2d1cf",
                #                                             value=str(satellite_j26['time'].values[0]),
                #                                         ),
                #                                         html.H6(
                #                                             id="orcatag",
                #                                             children="J26 Mike (21 yr)",
                #                                         ),
                #                                     ],
                #                                 ),
                #                             ],
                #                         ),                                                                                    
                #                     ],
                #                 ),
                #             ],
                #         ),
                #     ],
                # ),
            ],
        ),       
    ],
)
#-----------------------------------------------------------------------------#
#                                  Callback
# ----------------------------------------------------------------------------#
#~~~~~~~~~~~~~~~~~~~~~Salmon Time Series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output("salmon-timeseries", "figure"),
        Output("salmon-map","figure")
    ],
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
                data=[  #--This Year--# 
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
        # Define location for salmon map
        fig_salmonmap=go.Figure(
            data=go.Scattermapbox(
                lat=salmon_loc['lat'],
                lon=salmon_loc['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=[10,20,10],
                    color=['#33C3F0','#ff6666','#ff6666'],
                    opacity=0.7,
                ),
                text=salmon_loc['loc'],
                hoverinfo='text'
            ),
            layout=dict(
                autosize=True,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=47.635470,
                    lon=-122.457417
                ),
                zoom=5,
                style='light'
                ),
            ),
        )
        return fig_salmon,fig_salmonmap
    elif location_dropdown=="Albion":
        # Define salmon time seires
        title='Albion Chinook Catch Per Unit Effort (CPUE) 3 recent years vs History'
        ylab='CPUE'
        xlab='Date'
        fig_salmon=go.Figure(
                data=[  #--This Year--# 
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
        # Define location for salmon map
        fig_salmonmap=go.Figure(
            data=go.Scattermapbox(
                lat=salmon_loc['lat'],
                lon=salmon_loc['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=[10,10,20],
                    color=['#33C3F0','#ff6666','#ff6666'],
                    opacity=0.7,
                ),
                text=salmon_loc['loc'],
                hoverinfo='text'
            ),
            layout=dict(
                autosize=True,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=47.635470,
                    lon=-122.457417
                ),
                zoom=5,
                style='light'
                ),
            ),
        )
        return fig_salmon, fig_salmonmap
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
        # Define location for salmon map
        fig_salmonmap=go.Figure(
            data=go.Scattermapbox(
                lat=salmon_loc['lat'],
                lon=salmon_loc['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=[10,20,20],
                    color=['#33C3F0','#ff6666','#ff6666'],
                    opacity=0.7,
                ),
                text=salmon_loc['loc'],
                hoverinfo='text'
            ),
            layout=dict(
                autosize=True,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=dict(
                    lat=47.635470,
                    lon=-122.457417
                ),
                zoom=5,
                style='light'
                ),
            ),
        )
        return fig_salmon, fig_salmonmap

#~~~~~~~~~~~~~~~~~~~~~Orca Map~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("orca-map", "figure"),
    [
        Input("pod-dropdown", "value"),
        Input("year-dropdown","value")
    ],
)
def update_orca_map(pod,year):
    srkwc=pd.read_csv(acartia_path+"srkw_"+str(year)+".csv")
    srkwc['date2']=pd.to_datetime(srkwc['date_ymd'],format='%Y-%m-%d', errors='coerce')
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
    fig_orcamap = go.Figure()
    fig_orcamap.add_trace(go.Scattermapbox(
            lat=srkw_dat['latitude'],
            lon=srkw_dat['longitude'],
            mode='markers',
            marker=go.scattermapbox.Marker(
                color=srkw_dat.day_of_year,
                size=7,
                colorscale='Viridis',
                opacity=0.75,
                showscale=True,
                colorbar=dict(
                title='Day of the year',
                thickness=20,
                titleside='right',
                outlinecolor='rgba(68,68,68,0)',
                ticks='outside',
                ticklen=3,),     
            ),
            text=srkw_dat['created']+'<br>'+srkw_dat['data_source_comments'],
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

#~~~~~~~~~~~~~~~~~~~~~Orca Time series~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("salmon-orca-timeseries", "figure"),
    [
        Input("pod-dropdown", "value"),
        Input("year-dropdown","value")
    ],
)
def update_orca_lines(pod,year):
    srkw_yr_count=srkw_year(year,pod) 
    if year in (2018, 2019):
        orca_line_yaxis_title='reports of orca sightings'
    else:
        orca_line_yaxis_title='# of orcas'
    fig_orcaline = make_subplots(rows=3, cols=1)
    fig_orcaline.append_trace(
        go.Scatter(
            x=srkw_yr_count['date'],
            y=srkw_yr_count['srkw_north'],
            mode="markers",
            name="Central Salish Sea", 
            hovertemplate='%{x}'+': %{y}',
            marker=go.scatter.Marker(color=px.colors.sequential.Viridis[0]),
            ),
    row=1, col=1)
    fig_orcaline.append_trace(
        go.Scatter(
                x=srkw_yr_count['date'],
                y=srkw_yr_count['srkw_south'],
                mode="markers",
                name="Puget Sound", 
                hovertemplate='%{x}'+': %{y}',
                marker=go.scatter.Marker(color=px.colors.sequential.Viridis[-1]),
            ),
    row=1, col=1
    )
    fig_orcaline.append_trace(
        go.Scatter(
            x=srkw_yr_count['date'],
            y=srkw_yr_count['alb'+str(year)],
            name='Albion'+str(year),
            mode='lines+markers',
            hovertemplate='%{x}'+':%{y}',
            marker = go.scatter.Marker(
                color = px.colors.sequential.Viridis[7],
            ),
            line = go.scatter.Line(
                color = px.colors.sequential.Viridis[7],
            ),
            opacity=0.85,), 
    row=2, col=1)
    fig_orcaline.append_trace(
        go.Scatter(
            x=srkw_yr_count['date'],
            y=srkw_yr_count['bon'+str(year)],
            name='Bonneville'+str(year),
            mode='lines+markers',
            hovertemplate='%{x}'+':%{y}',
            marker = go.scatter.Marker(
                color = px.colors.sequential.Viridis[4],
            ),
            line = go.scatter.Line(
                color = px.colors.sequential.Viridis[4],
            ),
            opacity=0.85,),
    row=3, col=1)


    fig_orcaline.update_layout(
        paper_bgcolor=bgcl,
        plot_bgcolor=bgcl,
        margin=dict(t=0, r=0, b=0, l=0, pad=0,),
        yaxis = dict(zeroline = False,
            title=orca_line_yaxis_title,
            color=framecl, 
            showgrid=False,                                
            ),
        xaxis = dict(zeroline = False,
            color=framecl,
            showgrid=False,
            ),
            font=dict(
                family=plotfont, 
                size=9.5, 
                color=framecl,
            ),
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1.2,
                xanchor="left",
                x=0.1
            ),
        )
    fig_orcaline.update_yaxes(title_text='Chinook CPUE', row=2, col=1)
    fig_orcaline.update_yaxes(title_text='Chinook Count',  row=3, col=1)
    fig_orcaline.update_xaxes(tickmode='array',
                        tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                        #nticks=12,
                        tickangle=45, row=1, col=1)
    fig_orcaline.update_xaxes(tickmode='array',
                        tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                        #nticks=12,
                        tickangle=45, row=2, col=1)
    fig_orcaline.update_xaxes(tickmode='array',
                        tickvals=['Jan-1','Feb-1','Mar-1','Apr-1','May-1','Jun-1','Jul-1','Aug-1','Sep-1','Oct-1','Nov-1','Dec-1'],
                        #nticks=12,
                        tickangle=45,  row=3, col=1)
    fig_orcaline.update_traces(connectgaps=True)
    return fig_orcaline

#~~~~~~~~~~~~~~~~~~~~~Tab3: Orca Movement~~~~~~~~~~~~~~~~~~~~#
# @app.callback(
#     [
#         Output("satellite-bubble", "figure"),
#         Output('orcamove-date','children'),
#         Output('LED-time','value'),
#         Output('date-slider','max'),
#         Output('orcatag','children'),
#     ],
#     [
#         Input("orca-picker", "value"),
#         Input("date-slider", "value")
#     ],
# )
# def update_orca_move(orca, date_index):
#     #Pick orca
#     if orca=="J26":
#         orca_dat=satellite_j26
#         zoom_val=7
#         name="Mike"
#         age=min(orca_dat['year'])-1991
#     if orca=="J27":
#         orca_dat=satellite_j27
#         zoom_val=6        
#         name="Blackberry"
#         age=min(orca_dat['year'])-1991
#     if orca=="K25":
#         orca_dat=satellite_k25
#         zoom_val=4
#         name="Scoter"
#         age=min(orca_dat['year'])-1991
#     if orca=="K33":
#         orca_dat=satellite_k33
#         zoom_val=4
#         name="Tika"
#         age=min(orca_dat['year'])-2001
#     if orca=="L84":
#         orca_dat=satellite_l84
#         zoom_val=4
#         name="Nyssa"
#         age=min(orca_dat['year'])-1990
#     if orca=="L87":
#         orca_dat=satellite_l87
#         zoom_val=6
#         name="Onyx"
#         age=min(orca_dat['year'])-1992
#     if orca=="L88":
#         orca_dat=satellite_l88
#         zoom_val=5
#         name="Wave Walker"
#         age=min(orca_dat['year'])-1993
#     if orca=="L95":
#         orca_dat=satellite_l95
#         zoom_val=5
#         name="Nigel"
#         age=min(orca_dat['year'])-1996
#     orcaday(orca_dat)
#     geogen(orca_dat)
#     orca_dat=orca_dat.sort_values(by=['datetime_pst'])
#     lon_avg=orca_dat['lon'].mean()
#     lat_avg=orca_dat['lat'].mean()
#     #create index for slider
#     mark_index, _=make_slider_mark(orca_dat)
#     #Pick time
#     orca_dat=orca_dat.iloc[date_index, :]
#     #Define date and time for clock
#     cur_date=str(orca_dat['date'])
#     cur_time=str(orca_dat['time'])
#     #Define max of slider rack 
#     slider_max=len(mark_index)-1
#     #Define orca tag
#     orca_tag=" ".join([orca, name, "("+str(age)+"yr )"])
#     #Make plot
#     fig_orcamove = go.Figure()
#     fig_orcamove.add_trace(go.Scattermapbox(
#             lat=[orca_dat['lat']],
#             lon=[orca_dat['lon']],
#             mode='markers',
#             marker=go.scattermapbox.Marker(
#                 color="#016fb9",
#                 size=12,
#                 opacity=0.75,
#             ),        
#             text=[str(orca_dat['datetime_pst'])+"["+orca+"]"],
#             hoverinfo='text'
#         ))
#     fig_orcamove.update_layout(
#         autosize=True,
#         showlegend=False,
#         margin=dict(l=0, r=0, t=0, b=0),
#         mapbox=dict(
#             accesstoken=mapbox_access_token,
#             bearing=0,
#             center=dict(
#                 lat=lat_avg,
#                 lon=lon_avg
#             ),
#             zoom=zoom_val,
#             style='light'
#         ),
#     )    
#     return fig_orcamove, cur_date, cur_time, slider_max, orca_tag

# #~~~~~~~~~~~~~~~~~Interval of the Bubble Map~~~~~~~~~~~~~~~~~~~~~~~~~~#
# @app.callback(
#     [
#         Output('date-slider', 'value'),
#         Output('auto-stepper', 'max_intervals'),
#         Output('auto-stepper', 'disabled'),
#         Output('auto-stepper', 'n_intervals')
#     ],
#     [
#         Input('auto-stepper', 'n_intervals'),
#         Input('play-button','n_clicks_timestamp'),
#         Input('pause-button','n_clicks_timestamp'),
#         Input("orca-picker", "value"),
#     ]
# )
# def move_frames(n_intervals, play_timestamp, pause_timestamp,orca):
#     slider_value=0
#     max_intervals=0
#     int_disabled=True
#     #Pick orca
#     if orca=="J26":
#         orca_dat=satellite_j26
#         zoom_val=7
#     if orca=="J27":
#         orca_dat=satellite_j27
#         zoom_val=6        
#     if orca=="K25":
#         orca_dat=satellite_k25
#         zoom_val=4
#     if orca=="K33":
#         orca_dat=satellite_k33
#         zoom_val=4
#     if orca=="L84":
#         orca_dat=satellite_l84
#         zoom_val=4
#     if orca=="L87":
#         orca_dat=satellite_l87
#         zoom_val=6
#     if orca=="L88":
#         orca_dat=satellite_l88
#         zoom_val=5
#     if orca=="L95":
#         orca_dat=satellite_l95
#         zoom_val=5
#     orcaday(orca_dat)
#     geogen(orca_dat)
#     #refresh if it is a different orca
#     global current_orca
#     #create index for slider
#     mark_index, _=make_slider_mark(orca_dat)
#     if orca!=current_orca:
#         current_orca=orca
#         return 0, 0, True, 0
#     elif (play_timestamp==-1) & (pause_timestamp==-1):
#         return 0, 0, True, 0
#     elif  (play_timestamp>pause_timestamp):
#         slider_value=(n_intervals+1)%(len(mark_index))
#         max_intervals=-1
#         int_disabled=False
#     elif (pause_timestamp>play_timestamp):
#         slider_value=(n_intervals+1)%(len(mark_index))
#         max_intervals=0
#         int_disabled=False
#     return slider_value, max_intervals, int_disabled, n_intervals


if __name__ == '__main__':
    app.run_server(debug=True)