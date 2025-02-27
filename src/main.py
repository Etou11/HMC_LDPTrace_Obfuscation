# Libraries / packages
import pandas as pd
import numpy as np
import os
import pickle
import threading
from datetime import datetime
from pathlib import Path
from timeit import default_timer as timer

# Cross references
import split_dataframe
import helper
from ap_attack import ap_attack_processing
from heatmap import remove_profiles_out_of_bounds_coordinates, calculate_lat_lon_min_max

### Parameters Beginning
# Reduces the amount of profiles used to 10, to speed up processing
debugging = False

## Global Settings & Variables
# System path
src_path = Path.cwd()

# Column in the data frame that is used to determine the identity of a dataset
identifier_column = "FileName"

# Timer
start_timer = timer()
func_timer = 0

## Memory monitoring (deprecated)
# Global variable to hold memory usage
# Enable / disable memory output in console
memory_monitor_output = False
current_memory_usage = 0
memory_threshold = 85
memory_highest_value = 0
stop_event = threading.Event()

### Parameters End

date_time_now = datetime.now()
date_time_now_str = date_time_now.strftime("%H:%M:%S")
print(f"Starting execution at: {date_time_now_str}")

if debugging:
    print("Debugging mode is enabled! Only proceed if this is intentional!")


def load_profiles_from_text():
    ## Load cabspotting sets from txt files
    # Files Path
    files_path = Path("data/profiles_txt")
    source_files_path =  os.path.join(src_path, files_path)

    all_files = os.listdir(source_files_path)

    text_files = [file for file in all_files if file.endswith('.txt')]

    # Only use ten profiles to speed up debugging
    select_files = text_files  if not debugging else text_files[:10]

    # Vontains all original cab datasets as a list of data frames
    all_profiles = []

    for file_name in select_files:
        file_path = os.path.join(source_files_path, file_name)
        df = pd.read_csv(file_path, sep=" ", header=None, names=["Latitude", "Longitude", "Occupied", "Timestamp"])
        df["FileName"] = file_name[:-4]
        df = df.drop(columns="Occupied")
        all_profiles.append(df)

    return pd.DataFrame({"DataFrames": all_profiles})


def load_synthetic_profiles_from_pickl():

    ## Load synthetic cabspotting sets from pickle
    # Files path
    files_path = Path("data/profiles_pickl")
    source_files_path = os.path.join(src_path, files_path)

    all_files = os.listdir(source_files_path)

    pickle_files = [file for file in all_files if file.endswith('.pkl')]

    # Only use ten profiles to speed up debugging
    pickle_files = pickle_files if not debugging else pickle_files[::10]

    # Global variable that contains all synthetic cab datasets as a list of data frames
    all_synthetic_profiles = []

    for file_name in pickle_files:
        with open(f"{source_files_path}/{file_name}", 'rb') as f:
            trajectories = pickle.load(f)

        data_points = []

        # By default, synthetic trajectories contain multiple sub trajectories with one or multiple data points. To allow processing in HMC, this dimensionality is removed.
        # All subtrajectories are split and merged into single data points, conserving the original order.
        for trajectory in trajectories:
            for coord_pair in trajectory:
                longitude, latitude = coord_pair
                data_points.append([latitude, longitude])
                
        df = pd.DataFrame(data_points, columns=["Latitude", "Longitude"])
        df["FileName"] = file_name[:-4]
        all_synthetic_profiles.append(df)

    return  pd.DataFrame({"DataFrames": all_synthetic_profiles})


def prepare_dataset(normal_profiles_list, synthetic_profiles_list, first_part_dataset_type, last_part_dataset_type,
                     first_part_split_algorithm, last_part_split_algorithm, seed):
    
    first_part_data = normal_profiles_list if first_part_dataset_type == "NORMAL" else synthetic_profiles_list
    last_part_data = normal_profiles_list if last_part_dataset_type == "NORMAL" else synthetic_profiles_list

    first_part_data = remove_profiles_out_of_bounds_coordinates(first_part_data)
    last_part_data = remove_profiles_out_of_bounds_coordinates(last_part_data)

    first_part_data, _ = (split_dataframe.split_data_frame_list_by_half(first_part_data) if first_part_split_algorithm == "HALF" 
                       else split_dataframe.split_data_frame_list_randomly(first_part_data, seed=seed) if first_part_split_algorithm == "RANDOM"
                       else split_dataframe.split_data_frame_list_by_cluster(first_part_data))
    
    _, last_part_data = (split_dataframe.split_data_frame_list_by_half(last_part_data) if last_part_split_algorithm == "HALF" 
                       else split_dataframe.split_data_frame_list_randomly(last_part_data, seed=seed) if last_part_split_algorithm == "RANDOM"
                       else split_dataframe.split_data_frame_list_by_cluster(last_part_data))
    
    # Remove empty elements
    first_part_data = list(filter(lambda df: not df.empty, first_part_data["DataFrames"]))
    last_part_data = list(filter(lambda df: not df.empty, last_part_data["DataFrames"]))

    return first_part_data, last_part_data
         

def processor(profiles_list, synthetic_profiles_list, distance_type, obfuscation_type, dataset_type_first_part, dataset_type_last_part,
               split_algorithm_first_part, split_algorithm_last_part, seed):

    """
    Select which data set shall be used
    !! Important: The synthetic_profiles by default DO NOT have a Timestamp component, which means that splits BY DATE are NOT possible !!
    """

    try:
        if True:
            distance_type = distance_type.upper()
            obfuscation_type = obfuscation_type.upper()
            dataset_type_first_part = dataset_type_first_part.upper()
            dataset_type_last_part = dataset_type_last_part.upper()
            split_algorithm_first_part = split_algorithm_first_part.upper()
            split_algorithm_last_part = split_algorithm_last_part.upper()


            first_part_df, last_part_df = prepare_dataset(profiles_list, synthetic_profiles_list, dataset_type_first_part, dataset_type_last_part,
                                                        split_algorithm_first_part,  split_algorithm_last_part, seed=seed)
            
            results = []

            func_timer = timer()  
            print("Starting pre computation at: ", datetime.now())

            # Precomputation of all necessary data to reduce runtime
            precomputed_profiles_first_half = helper.precomputation(first_part_df, identifier_column)
            precomputed_profile_last_half = helper.precomputation(last_part_df, identifier_column)

            print("Pre computation took", timer() - func_timer, "seconds")

            results = ap_attack_processing(precomputed_profiles_first_half, precomputed_profile_last_half, distance_type, results, obfuscation_type, identifier_column)

            # Export results to file
            helper.export_results_to_dataframe(results, distance_type, obfuscation_type, dataset_type_first_part, dataset_type_last_part,
                                        split_algorithm_first_part, split_algorithm_last_part, seed, src_path)
            # Add results to continously updated file for comparison
            #helper.append_results_to_existing_file(results, distance_type, obfuscation_type, dataset_type_first_part, dataset_type_last_part,
                                #split_algorithm_first_part, split_algorithm_last_part, seed, src_path)

    except Exception as error:
        print(f"An exception occured during processing! \nError:\n{error}") 


def main():

    #seed = 123
    #np.random.seed(seed)

    random_seeds = [123, 323, 581, 445, 4, 845, 286, 742, 301, 87]

    all_normal_profiles_df = load_profiles_from_text()

    # DF of profile DFs, from pickl (synthetic)
    all_synthetic_profiles_df = load_synthetic_profiles_from_pickl()

    # Calculate lat / lon min / max coordinates based on synthetic profiles
    calculate_lat_lon_min_max(all_synthetic_profiles_df)

    ## Legal parameters: "topsoe", "hausdorff"
    ## Legal parameters: "HMC", "NOBF" default: "NOBF"
    ## Legal paremters: "NORMAL", "SYNTHETIC"
    ## Legal parameters: "RANDOM", "HALF", "CLUSTER"

    # processor(profiles_list, synthetic_profiles_list, distance_type, obfuscation_type, dataset_type_first_part, dataset_type_last_part,
    #           split_algorithm_first_part, split_algorithm_last_part, seed)
    #rocessor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "nobf", "normal", "random", seed)
    for seed in random_seeds:
        np.random.seed(seed)
        #processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "hmc", "normal", "normal", "random", "random", seed)
        #processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "nobf", "normal", "normal", "random", "random", seed)
        #processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "hmc", "synthetic", "synthetic", "random", "random", seed)
        #processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "nobf", "synthetic", "synthetic", "random", "random", seed)
        processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "hmc", "normal", "synthetic", "random", "random", seed)
        #processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "hmc", "synthetic", "normal", "random", "random", seed)
        processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "nobf", "normal", "synthetic", "random", "random", seed)
        #processor(all_normal_profiles_df, all_synthetic_profiles_df, "topsoe", "nobf", "synthetic", "normal", "random", "random", seed)


if __name__ == "__main__":
    main()




"""
(DEPRECATED)

Code to run memory monitoring on a second thread

## Start the memory monitoring in a separate thread
monitor_thread = threading.Thread(target=monitor_memory, args=(stop_event,))
monitor_thread.daemon = True
monitor_thread.start()

# Start the data processing in a separate thread
processing_thread = threading.Thread(target=process_data, args=(split_algorithm, scenarios, stop_event))
processing_thread.start()

# Wait for the processing to finish
processing_thread.join()

# Ensure the monitor thread is stopped
monitor_thread.join()
"""