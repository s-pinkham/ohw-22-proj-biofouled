#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 10:17:16 2022

@author: rieke
"""

import xarray as xr

file = './data/example_data1.nc'
#file = './data/example_data2.nc'
ds = xr.open_dataset(file)


#plot manually assigned quality
ds.rollup_annotations_qc_results.plot()

#data summarised for each day
ds.resample(time='1D').mean().estimated_oxygen_concentration.plot(x="time")
ds.resample(time='1D').std().estimated_oxygen_concentration.plot(x="time")
ds.resample(time='1D').max().estimated_oxygen_concentration.plot(x="time")
ds.resample(time='1D').min().estimated_oxygen_concentration.plot(x="time")

#data summarised for each week
ds.resample(time='1W').mean().estimated_oxygen_concentration.plot(x="time")

#difference between each measurement and the one before??
ds.diff("time").estimated_oxygen_concentration.plot(x="time")
abs(ds.diff("time").estimated_oxygen_concentration).plot(x="time")
#dfference between mean of each day and the one fo the day before?
ds.resample(time='1D').mean().diff("time").estimated_oxygen_concentration.plot(x="time")

#create new variable that is 0 (False) when above threshold, and 1 (True) when below
def assignStatus(datarray, name, threshold = 30, timerange = False):
    
    #remove change variable if already defined
    if "changeOxygen" in ds.data_vars:    
        datarray = datarray.drop("changeOxygen")
    
    if timerange == False:
        datarray = datarray.assign(changeOxygen = abs(datarray.diff("time").estimated_oxygen_concentration))
    
    else:
        #calculte mean over the specified time range, take differene between consecutve times
        datarrayShort = abs(datarray.resample(time=timerange).mean().diff("time").estimated_oxygen_concentration)
        datarrayShort.name = "changeOxygen"
        #assign dfference back to original dataframe
        datarray = xr.combine_by_coords([datarray, datarrayShort.reindex_like(datarray, method = "ffill")], join = "right", coords = "time")
    
    #compare difference to given threshold
    #0 == False, 1 == True -> 0 means data is likely wrong, 1 means data is likely right
    datarray[name] = xr.where(datarray.changeOxygen > threshold, 0, 1)
    return datarray

# ds = assignStatus(ds, "good", 7, "1M")
# 
# ds.good.plot(x="time")
# xr.plot.scatter(ds, "time", "estimated_oxygen_concentration", hue = "good", hue_style="discrete")

#make regions with many bad data points completely bad
def expandStatus(datarray, name, nameExpanded, rollingtime, minRatio):
    datarray = datarray.assign(ratioGood = datarray[name].rolling(time = rollingtime, center = True).mean())
    #datarray.percentageGood.plot(x="time")
    datarray[nameExpanded] = xr.where(datarray.ratioGood < minRatio, 0, 1)
    
    return datarray

# ds = expandStatus(ds, "good", "goodExpanded", 300, 0.995)

# ds = ds.assign(percentageGood = ds["good"].rolling(time = 300, center = True).mean())
# ds.percentageGood.plot(x="time")
# ds["goodExpanded"] = xr.where(ds.percentageGood < 0.995, 0, 1)

def flagStatus(datarray, name, nameExpanded, 
               threshold = 30, timerange = False, 
               rollingtime = 300, minRatio = 0.995):
    '''
    Assign 0 (bad) and 1 (good) to oxygen data based on the dfference between consecutive values

    Parameters
    ----------
    datarray : xArray Dataset
        dataset to be analysed.
    name : string
        name of the variable where the flag status of each time point is stored.
    nameExpanded : string
        name of the variable where the flag status of each time point is stored.
    threshold : integer, optional
        Threshold for the difference between consecutive values above which 0 is assigned. The default is 30.
    timerange : time, optional
        Optional time range (e.g. one day: 1D, one week: 1W, one month: 1M) over which a mean is taken. If not False, the difference between consecutive means is compared to the threshold. The default is False.
    rollingtime : integer, optional
        The time window over which the rolling mean is applied to expand the status. Over a window with this length, a mean is taken from the status (resulting in a ratio between 0 and 1). The default is 300.
    minRatio : float, optional
        Minimal ratio of good data points that needs to be reached over a window of length rollingtime to assign status good (1) to the data point. If the ratio is lower, bad (0) is assigned. The default is 0.995.

    Returns
    -------
    datarray : xArray Dataset
        Input data array with two additional variables, named name and nameExpanded. They give the data status based on the difference of consecutive values and the given parameters.

    '''
    
    datarray = assignStatus(datarray, name, threshold, timerange)
    
    datarray = expandStatus(datarray, name, nameExpanded, rollingtime, minRatio)
    
    return datarray

ds = flagStatus(ds, "good", "goodExpanded")


ds.goodExpanded.plot(x="time")
xr.plot.scatter(ds, "time", "estimated_oxygen_concentration", hue = "goodExpanded", hue_style="discrete")


#convert Andrew's labelling to 0/1
ds["LabelAndrew"] = xr.where(ds.rollup_annotations_qc_results == 0, True, False)
xr.plot.scatter(ds, "time", "estimated_oxygen_concentration", hue = "LabelAndrew", hue_style="discrete")


#calculate accuracy of labelling
#exactly matching
ds["correct"] = xr.where(ds.LabelAndrew-ds.goodExpanded == 0, True, False)
ds.correct.mean()

#my own is False, while other is True
ds["falseNeg"] = xr.where(ds.LabelAndrew-ds.goodExpanded == 1, True, False)
ds.falseNeg.mean()

#my own is True while other is False
ds["falsePos"] = xr.where(ds.LabelAndrew-ds.goodExpanded == -1, True, False)
ds.falsePos.mean()
