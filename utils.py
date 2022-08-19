import xarray as xr
import numpy as np
import pandas as pd
import re

def no_special(text):
    text = re.sub("[^a-zA-Z0-9.\-\s]+", "",text)
    return text

def parse_location(location):
    """Parse out the latitude, longitude, and depth from the location entry in the annotation"""
    # Check if it is a NaN
    try:
        np.isnan(location)
        return location, location, location
    except:
        location = no_special(location)
        location = location.split()
        for x in location:
            if x.endswith(("N", "S")):
                # Get the last entry
                hemi = x[-1]
                if hemi.lower() == "n":
                    hemi = 1
                else:
                    hemi = -1
                lat = hemi*float(x[:-1])
            elif x.endswith(("E","W")):
                # Get the last entry
                hemi = x[-1]
                if hemi.lower() == "e":
                    hemi = 1
                else:
                    hemi = -1
                lon = hemi*float(x[:-1])
            elif x.endswith("m"):
                depth = float(x[:-1])
            else:
                pass
        # Return the results
        return lat, lon, depth

    
def prep_deployments(deployments):
    """Cleans the deployment category entries from the Data Explorer annotations
    
    Params
    ------
    deployments: (pandas.DataFrame)
        The deployment category from the annotations downloaded from Data Explorer
        separated into their own dataframe
        
    Returns
    -------
    deployments: (pandas.DataFrame)
        A dataframe of the deployments that cleaned up overlapping time periods,
        the latitude, longitude, and start/endDates in floats or numpy datetime objects
    """
    deploymentNumber = deployments["ooi_deployment_id"].apply(lambda x: int(x[-4::]))
    deployments["deploymentNumber"] = deploymentNumber
    # Now groupby the deployment number and get the min and max 
    deployments = deployments.groupby(by="deploymentNumber").agg({"startDate":np.min, "endDate":np.max, "latitude": np.mean, "longitude": np.mean, "depth": np.mean})
    deployments = deployments.reset_index()
    # Now do time shifting to replace overlapping time periods 
    # Next, need to add the times and do some phase-shifting of the deployment ends to avoid overlapping time periods
    startDates = deployments["startDate"]
    endDates = deployments["endDate"]

    # Shift the endDates by +1
    endDates = endDates.shift(1)

    # Look for where startDates < endDates
    mask = startDates < endDates

    # Replace the startDates that are less than the shifted endDates with the shifted endDates
    startDates[mask] = endDates[mask]
    deployments["startDate"] = startDates
    
    return deployments


def parse_deployments(annotations):
    """Function to parse the deployment information from the annotation table"""
    
    # Use the category label to get the deployments
    deployments = annotations[annotations["category"] == "Deployment"]
    
    # Get the deployment number
    deploymentNumber = deployments["ooi_deployment_id"].apply(lambda x: int(x[-4::]))
    
    # Convert the start/endDates to datetime object
    deployments["startDate"] = deployments["startDate"].apply(lambda x: pd.to_datetime(x))
    deployments["endDate"] = deployments["endDate"].apply(lambda x: pd.to_datetime(x))
    
    # Next, need to parse out the location lat/lon/deployed depth
    deployments["deployment_location"] = deployments["deployment_location"].apply(lambda x: parse_location(x))
    
    # Break out the lat, lon, depth
    deployments["latitude"] = deployments["deployment_location"].apply(lambda x: x[0])
    deployments["longitude"] = deployments["deployment_location"].apply(lambda x: x[1])
    deployments["depth"] = deployments["deployment_location"].apply(lambda x: x[2])
    
    # Return the deployments
    return deployments


def add_deployments(ds, annotations):
    """Add the deployment number(s) to the dataset.
    
    Params
    ------
    ds: (xarray.Dataset)
        A dataset containing data downloaded from the oceanobservatories Data Explorer
    annotations: (pandas.DataFrame)
        A dataframe containing the associated annotations for the given dataset
        
    Returns
    -------
    ds: (xarray.Dataset)
        Returns an updated dataset with the deployment number(s) added as a new
        variable 'deployments'
    """
    
    # Add the 
    deployments = parse_deployments(annotations)
    deployments = prep_deployments(deployments)
 
    # Create a deploymentNumber dataArray
    deploymentNumber = xr.DataArray(
        data=np.zeros_like(ds.time, int),
        coords={"time": ds.time.data},
        dims="time",
        name="deployment",
    )
    
    # Now populate the intergers in the data array based on the deployment times
    for depNum in deployments["deploymentNumber"]:
        startDate = deployments[deployments["deploymentNumber"] == depNum]["startDate"].values
        endDate = deployments[deployments["deploymentNumber"] == depNum]["endDate"].values
        mask = (deploymentNumber.time >= startDate) & (deploymentNumber.time <= endDate)
        deploymentNumber[mask] = depNum
        
    # Add the data array to the dataset
    ds["deployment"] = deploymentNumber
    return ds


def parse_qc_description(desc):
    """Parse the qcResult description to get the qc flag"""
    # Search for the qc result
    m = re.search(r'\[(.+)\]', desc)
    if m is not None:
        if "suspect" in m.group(1):
            qc_flag = 3
        else:
            qc_flag = 0
    else:
        qc_flag = 0

    return qc_flag
    
    
def parse_qc_deploymentNumber(desc):
    """Parse out the deployment number applicable to the qc result"""
    depNum = re.search(r'(d|Deployment\s)[0-9]{1,2}', desc)
    if depNum is not None:
        depNum = int(depNum.group().split()[-1])
        return depNum
    else:
        return None
    
    
def add_qc_flag(ds, annotations):
    """Add the annotation qc flag tag from the description to the dataset
    
    Params
    ------
    ds: (xarray.DataSet)
        A dataset containing data downloaded from the oceanobservatories Data Explorer
    annotations: (pandas.DataFrame)
        A dataframe containing the associated annotations for the given dataset
        
    Returns
    -------
    ds: (xarray.Dataset)
        Returns an updated dataset with the deployment number(s) added as a new
        variable 'annotation_qc_flag'
    """
    # Get the entries that are a qc result
    qcResult = annotations[annotations["category"] == "QC Result"]

    # Clean up the start and end Dates so they are datetime objects
    qcResult["startDate"] = qcResult["startDate"].apply(lambda x: pd.to_datetime(x).tz_localize(None))
    qcResult["endDate"] = qcResult["endDate"].apply(lambda x: pd.to_datetime(x).tz_localize(None))
    
    # Add the flag
    qcResult["qcFlag"] = qcResult["description"].apply(lambda x: parse_qc_description(x))
    
    # Add the deployment Number
    qcResult["deploymentNumber"] = qcResult["description"].apply(lambda x: parse_qc_deploymentNumber(x))
    
    # Now add in the qcFlag to the dataset
    qcFlag = xr.DataArray(
        data=np.zeros_like(ds.time, int),
        coords={"time": ds.time.data},
        dims="time",
        name="qc_flag",
    )
    
    # Now add the qcFlags
    for ind in qcResult.index:
        # Get the startDate, endDate, deploymentNumber
        startDate = qcResult.loc[ind]["startDate"]
        endDate = qcResult.loc[ind]["endDate"]
        depNum = qcResult.loc[ind]["deploymentNumber"]
        # Get the qcFlag
        flag = qcResult.loc[ind]["qcFlag"]
        # Now mask off the relevant time periods
        if depNum is not None:
            mask = (qcFlag.time >= startDate) & (qcFlag.time <= endDate) & (ds.deployment == depNum)
        else:
            mask = (qcFlag.time >= startDate) & (qcFlag.time <= endDate)
        qcFlag[mask] = flag
        
    # Add the qcFlags to the dataset
    ds["annotation_qc_flag"] = qcFlag
    return ds