#!/usr/bin/python
import os
import sys
import plotly.plotly as py
from plotly.graph_objs import Scatter, Data, Layout, XAxis, YAxis, Figure, Marker, Line
import ConfigParser
import requests
import pandas as pd
import numpy as np
from datetime import datetime
from numpy import polyfit

def make_config_dict(cp):
    '''
    Return a nested dict of sections/options by iterating through a ConfigParser instance.
    '''
    d = {}
    for s in cp.sections():
        e = {}
        for o in cp.options(s):
            e[o] = cp.get(s,o)
        d[s] = e
    return d

def get_config(config_file):
    '''Return a dictionary of configuration options from the configuration file
    '''
    config = ConfigParser.ConfigParser()
    try:
        with open(config_file) as f:
            config.readfp(f)
    except IOError:
        print("Couldn't open configuration file.")
        sys.exit("Exiting.")
    config_dict = make_config_dict(config)
    # Change the natural language boolean to an actual boolean value
    config_dict['general']['upload_graph'] = config.getboolean('general', 'upload_graph')
    return config_dict

def graph_plotly(data, fit1, fit2, config_dict):
    print('Making Plotly graph...')
    py.sign_in(config_dict['secrets']['plotly_userid'], config_dict['secrets']['plotly_apikey'])
    Scatter1 = Scatter(x=data['0_x'],
               y=data['0_y'], name='Recorded Data', mode='markers', marker=Marker(color='red'), text=data['index'])
    Line1 = Scatter(x=fit1['x'],
               y=fit1['y'], name='Linear Fit (R<sup>2</sup> = ' +str(fit1['r2']) + ')', mode='lines', line=Line(color='orange'))
    Line2 = Scatter(x=fit2['x'],
               y=fit2['y'], name='Polynomial Fit (R<sup>2</sup> = ' +str(fit2['r2']) + ')', mode='lines', line=Line(shape='spline', color='blue'))
    data = Data([Scatter1, Line1, Line2])
    layout = Layout(
                    title='Electricity Usage & Mean Outdoor Temperature (updated daily)',
                    yaxis=YAxis(title='kWh'),
                    xaxis=XAxis(title='&deg;F')
                    )
    fig = Figure(data=data, layout=layout)
    url1 = py.plot(fig, filename='electricity-and-temperature', auto_open=False)
    print('Done uploading.')
    return url1

def r_squared(fit, y, yhat):
    ybar = np.mean(yhat)
    ssreg = np.sum((yhat-ybar)**2)
    sstot = np.sum((y - ybar)**2)
    return ssreg / sstot

def main():
    # Change to the working directory, which is the directory of the script
    pathname = os.path.dirname(sys.argv[0])
    working_dir = os.path.abspath(pathname)
    try:
        os.chdir(working_dir)
    except:
        print("Couldn't change to script directory.")
        sys.exit("Exiting.")
    
    # Get configuration options
    config_dict = get_config('elec_temp.conf')
        
    # Get the temperature data
    r = requests.get(config_dict['general']['url_temp'])
    temp_json = r.json()
    datetimes = temp_json['data'][0]['x']
    datetimes = [datetime.strptime(d, '%Y-%m-%d %H:%M:%S') for d in datetimes]
    temps = temp_json['data'][0]['y']
    df_temp = pd.DataFrame(temps,index=datetimes)
    grouper = pd.TimeGrouper("1D")
    df_temp_mean = df_temp.groupby(grouper).aggregate(np.mean)

    # Get the energy data
    r = requests.get(config_dict['general']['url_energy'])
    energy_json = r.json()
    datetimes = energy_json['data'][0]['x']
    datetimes = [datetime.strptime(d, '%Y-%m-%d') for d in datetimes]
    kwh = energy_json['data'][0]['y']
    df_energy = pd.DataFrame(kwh,index=datetimes)
    
    # Merge the two
    elec_temp = pd.merge(df_temp_mean, df_energy, left_index=True, right_index=True, how='inner')
    # Discard NaNs and index, sort x values so that lines can be plotted nicely
    elec_temp = elec_temp[np.isfinite(elec_temp['0_x'])]
    elec_temp = elec_temp.reset_index()
    elec_temp = elec_temp.sort('0_x')
    print "Data frame length: " + str(len(elec_temp))
    fit1 = np.poly1d(polyfit(elec_temp['0_x'], elec_temp['0_y'], deg=1))
    fit2 = np.poly1d(polyfit(elec_temp['0_x'], elec_temp['0_y'], deg=2))
    predicted_ys = fit1(elec_temp['0_x'])
    r2 = r_squared(fit1, elec_temp['0_y'], predicted_ys)
    print fit1
    print "Linear fit R^2 = " + str(r2)
    myfit1 = {'x': elec_temp['0_x'], 'y': predicted_ys, 'r2': round(r2, 2)}
    predicted_ys = fit2(elec_temp['0_x'])
    r2 = r_squared(fit2, elec_temp['0_y'], predicted_ys)
    print fit2
    print "Polynomial fit R^2 = " + str(r2)
    myfit2 = {'x': elec_temp['0_x'], 'y': predicted_ys, 'r2': round(r2, 2)}
    
    if config_dict['general']['upload_graph'] == True:
        url1 = graph_plotly(elec_temp, myfit1, myfit2, config_dict)
        print "View your graph at " + url1

if __name__ == "__main__":
    main()
