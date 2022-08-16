# ohw-22-proj-biofouled
Develop a technique for identifity when instrument data have gone bad due to biofouling

## Summary
A challenge for deploying ocean instruments for extended periods of time or in productive environments is biofouling on sensors. This project would develop a technique(s) or method for identifying when data from different instruments when they have become biofouled.

## Personnel
* Thiago Caminha
* Rieke Schäfer
* Allen Smith
* Sunny Pinkham
* Andrew Reed

## Datasets and Infrastructure Supported
This project would start with looking at Aanderaa oxygen optodes from moorings deployed and maintained by the Ocean Observatories Initiative. Much of the oxygen data has already been manually annotated for when it was biofouled by the operators, providing for a training dataset. Additionally, the datasets and manual annotation can be downloaded as netCDF files from https://dataexplorer.oceanobservatories.org/ or from the ERDDAP server at https://erddap.dataexplorer.oceanobservatories.org/erddap

This could then hopefully extended to other instruments known to biofoul, such as 2-or-3 wavelength fluorometers and to instruments on profilers or gliders.

## Steps
* Download an Aanderaa dataset an associated manual annotations from OOI
* Visualize the dataset with the annotations noting biofouling
* Develop a statistic or apply a filtering technique to identify the biofouling
* Cross-reference the technique against the manual annotations

## Example
Here is a quick plot of the oxygen from the OOI Ocean Station Papa Subsurface Flanking Mooring A Deployment 2. The marked "annotations" are a Human-in-the-loop review of the data that marked data that is biofouled. 

![image](https://user-images.githubusercontent.com/22527731/184693082-b90a50a5-7bcf-4ee7-982d-53b8380a1541.png)