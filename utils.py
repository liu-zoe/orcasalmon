import numpy as np 
import datetime
import pandas as pd 

def conv_npdt64(np_datetime):
    """
    Converts a numpy datetime64 object to a python datetime object 
    Input:
      date - a np.datetime64 object
    Output:
      DATE - a python datetime object
    """
    py_datetime = np_datetime.astype(datetime.date)
    return py_datetime

def conv_to_date(x):
    """
    Converts a numpy datetime64 object to a python datetime object 
    Input:
      date - a np.datetime64 object
    Output:
      DATE - a python datetime object
    """
    if isinstance(x, np.datetime64):
      return pd.to_datetime(x).date()
    elif isinstance(x, pd._libs.tslibs.timestamps.Timestamp):
      return x.date()

def str2mon(m):
    mondict={"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, 
         "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12}
    if isinstance(m, str):
        x=mondict[m.lower()]
        return x

