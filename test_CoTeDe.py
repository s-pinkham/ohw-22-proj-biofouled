#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 17 10:17:16 2022

@author: rieke
"""
import xarray as xr
import cotede
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np

file = './data/example_data1.nc'
#file = './data/example_data2.nc'
ds = xr.open_dataset(file)

#https://nbviewer.ipython.org/github/castelao/CoTeDe/blob/master/docs/notebooks/TSG_Saildrone.ipynb
ds_tested = cotede.ProfileQC(ds, {'estimated_oxygen_concentration':{'gradient': {'threshold': 5},
                                                                    'rate_of_change': {'threshold': 5},
                                                                    'spike': {'threshold': 5},
                                                                    'stuck_value': {'threshold': 5}}})

ds_tested.flags.keys()
ds_tested.flags['estimated_oxygen_concentration']


cmap = colors.ListedColormap(['#BBBBBB', '#009988', '#33BBEE', '#EE7733', '#CC3311'])
norm = colors.BoundaryNorm(np.arange(-0.5, 5.5, 1), cmap.N)

plt.scatter(ds_tested['time'].to_numpy(), ds_tested['estimated_oxygen_concentration'].to_numpy(),
         c = ds_tested.flags['estimated_oxygen_concentration']['overall'],
         cmap = cmap, norm = norm)
plt.colorbar(ticks=np.linspace(0, 5, 6))

