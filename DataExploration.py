#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 16 08:58:29 2022

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

#create new variable that is 0 (False) when below threshold, and 1 (True) when above
def assignStatus(datarray, name, threshold = 30):
    datarray[name] = xr.where(datarray.changeDissolvedOxygen > threshold, 0, 1)
    return datarray
    
ds = ds.assign(changeDissolvedOxygen = abs(ds.diff("time").estimated_oxygen_concentration))

ds = assignStatus(ds, "bad", 30)

ds.bad.plot(x="time")
xr.plot.scatter(ds, "time", "estimated_oxygen_concentration", hue = "bad", hue_style="discrete")


#convert Andrew's labelling to 0/1
ds["LabelAndrew"] = xr.where(ds.rollup_annotations_qc_results == 0, False, True)
xr.plot.scatter(ds, "time", "estimated_oxygen_concentration", hue = "LabelAndrew", hue_style="discrete")


#calculate accuracy of labelling
#exactly matching
ds["correct"] = xr.where(ds.LabelAndrew-ds.bad == 0, True, False)
ds.correct.mean()

#my own is False, while other is True
ds["falseNeg"] = xr.where(ds.LabelAndrew-ds.bad == 1, True, False)
ds.falseNeg.mean()

#my own is True while other is False
ds["falsePos"] = xr.where(ds.LabelAndrew-ds.bad == -1, True, False)
ds.falsePos.mean()
