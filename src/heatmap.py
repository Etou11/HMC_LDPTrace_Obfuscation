# Libraries / packages
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


# Map part that is used in calculations
lon_min = -122.50
lon_max = -122.35
lat_min = 37.60
lat_max = 37.85

# Amount of grid cells used. Default amount (8 x 8) is based upon Dr. Maouche's descriptions and depictions
num_lon_bins = 8
num_lat_bins = 8

def calculate_lat_lon_min_max(all_synthetic_profiles_df):

    # Initialize global minimum and maximum values
    global_min_lat = float('inf')
    global_max_lat = float('-inf')
    global_min_lon = float('inf')
    global_max_lon = float('-inf')

    # Iterate over all sub-DataFrames in the 'DataFrames' column
    for sub_df in all_synthetic_profiles_df["DataFrames"]:
        # Calculate the minimum and maximum values of the Latitude column
        min_lat = sub_df["Latitude"].min()
        max_lat = sub_df["Latitude"].max()
        
        # Calculate the minimum and maximum values of the Longitude column
        min_lon = sub_df["Longitude"].min()
        max_lon = sub_df["Longitude"].max()
        
        # Update global minimum and maximum values
        global_min_lat = min(global_min_lat, min_lat)
        global_max_lat = max(global_max_lat, max_lat)
        global_min_lon = min(global_min_lon, min_lon)
        global_max_lon = max(global_max_lon, max_lon)

    print(f"Global minimum Latitude: {global_min_lat}")
    print(f"Global maximum Latitude: {global_max_lat}")
    print(f"Global minimum Longitude: {global_min_lon}")
    print(f"Global maximum Longitude: {global_max_lon}")

    global lon_min, lon_max, lat_min, lat_max
    lon_min, lon_max, lat_min, lat_max = global_min_lon, global_max_lon, global_min_lat, global_max_lat



def create_heatmap(df, lon_bins = num_lon_bins, lat_bins = num_lat_bins, density = True):
    """
    Create a heat map based on the given DataFrame. By default returns a probability density heat map
    
    Args:
    - df: DataFrame containing 'Latitude' and 'Longitude' columns
    - lon_min: Minimum longitude for the bins
    - lon_max: Maximum longitude for the bins
    - lat_min: Minimum latitude for the bins
    - lat_max: Maximum latitude for the bins
    - num_lon_bins: Number of longitude bins
    - num_lat_bins: Number of latitude bins
    - density: If True, normalize the heat map to represent probability density
    
    Returns:
    - hist: 2D histogram representing the heat map
    """
    
    lat = df["Latitude"].values
    lon = df["Longitude"].values

    # Create grid from longitude / latitude data points
    lon_bins = np.linspace(lon_min, lon_max, num_lon_bins)
    lat_bins = np.linspace(lat_min, lat_max, num_lat_bins)

    # Create 2D histogram
    hist, _, _ = np.histogram2d(lon, lat, bins=[lon_bins, lat_bins], density=density)
    
    # Replace zero values with a small number to avoid issues with log calculations
    hist[hist == 0] = 1e-10
    
    return hist

def calculate_map_bins(long_upper = lon_max, long_lower = lon_min, lat_upper = lat_max, lat_lower = lat_min, num_lon_bins = num_lon_bins, num_lat_bins = num_lat_bins):
    """
    Calculates the map bins of the grid, based upon the specified values for latitude, longitude and the amount of grid cells
    
    Args:
    - long_upper: Upper limit of the longitude
    - long_lower: Lower limit of the longitude
    - lat_upper: Upper limit of the latitude
    - lat_lower: Lower limit of the latitude
    - num_lon_bins: Number of longitude bins
    - num_lat_bins: Number of latitude bins
    
    Returns:
    - bin_rows: DataFrame containing the calculated bins with their limits
    """
    
    long_total = long_upper - long_lower
    lat_total = lat_upper - lat_lower

    long_bin_size = long_total / num_lon_bins
    lat_bin_size = lat_total / num_lat_bins

    bin_rows = pd.DataFrame({
        "Index": range(num_lat_bins * num_lon_bins)
    })

    bin_rows['Longitude Lower Limit'] = long_lower + (bin_rows['Index'] % num_lon_bins) * long_bin_size
    bin_rows['Longitude Upper Limit'] = bin_rows['Longitude Lower Limit'] + long_bin_size
    bin_rows['Latitude Upper Limit'] = lat_upper - (bin_rows['Index'] // num_lon_bins) * lat_bin_size
    bin_rows['Latitude Lower Limit'] = bin_rows['Latitude Upper Limit'] - lat_bin_size

    return bin_rows

def show_heat_map(heat_map, title = ""):

    """
    Displays given heat map in the console
    """

    plt.imshow(heat_map.T, origin='lower', extent=[lon_min, lon_max, lat_min, lat_max], aspect='auto', cmap='magma')

    plt.colorbar()
    plt.title(title)
    
    plt.show()

def visited_bins(profile, map_bins = calculate_map_bins()):
    """
    Calculates the visited bins (grid cells) of a given DataFrame
    
    Args:
    - profile: DataFrame containing longitude and latitude columns.
    - map_bins: DataFrame containing the bin definitions with columns:
        ['Longitude Lower Limit', 'Longitude Upper Limit', 
         'Latitude Lower Limit', 'Latitude Upper Limit', 'Index']
         
    Returns:
    - sorted_bins: Array of unique visited bin indices, sorted.
    """
    
    # Initialize an empty list to store the indices of visited bins
    visited_bins = []

    # Iterate through each bin definition in map_bins
    for _, bin_row in map_bins.iterrows():
        # Find all profile entries that fall within the current bin
        in_bin = profile[
            (profile["Longitude"] >= bin_row["Longitude Lower Limit"]) &
            (profile["Longitude"] < bin_row["Longitude Upper Limit"]) &
            (profile["Latitude"] >= bin_row["Latitude Lower Limit"]) &
            (profile["Latitude"] < bin_row["Latitude Upper Limit"])
        ]
        if not in_bin.empty:
            visited_bins.append(bin_row["Index"])

    # Get unique and sorted bin indices
    unique_bins = np.unique(visited_bins)
    sorted_bins = np.sort(unique_bins)
    
    return sorted_bins

def remove_profiles_out_of_bounds_coordinates(profiles_df, lon_max = lon_max, lon_min = lon_min, lat_max = lat_max, lat_min = lat_min):
    """
    Removes coordinate points that are outliers and outside the specified part of the map 
    (outside min/max latitude/longitude range) to prevent out of bound errors.
    
    Args:
    - profiles_df: DataFrame containing a column 'DataFrames' with DataFrames that have 'Longitude' and 'Latitude' columns
    - lon_max: Maximum allowed longitude (default value: global variable)
    - lon_min: Minimum allowed longitude (default value: global variable)
    - lat_max: Maximum allowed latitude (default value: global variable)
    - lat_min: Minimum allowed latitude (default value: global variable)
    
    Returns:
    - profiles_df: DataFrame with 'DataFrames' column where each DataFrame has out of bounds coordinates removed
    """

    profiles_df["DataFrames"] = profiles_df["DataFrames"].apply(
        lambda df: df[
            (df["Longitude"] <= lon_max) &
            (df["Longitude"] >= lon_min) &
            (df["Latitude"] <= lat_max) &
            (df["Latitude"] >= lat_min)
        ].reset_index(drop=True)
    )
    
    return profiles_df
