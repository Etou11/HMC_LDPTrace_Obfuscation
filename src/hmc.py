# Libraries / packages
import numpy as np
import inspect
from datetime import datetime
from timeit import default_timer as timer
import gc


# Cross references
from distance import calculate_distance_between_points
from helper import update_alteration_counter


def area_coverage_precision(visited_bins_h: list[int], visited_bins_candidate: list[int]) -> float:
    """
    Calculate the precision of area coverage between two sets of visited bins
    
    Parameters:
    visited_bins_h (list[int]): The set of visited bins from the reference heat map
    visited_bins_candidate (list[int]): The set of visited bins from the candidate heat map
    
    Returns:
    float: The precision value, calculated as the ratio of the intersection of the two sets
           over the total number of bins in the candidate set. Returns 0 if the candidate set is empty
    """
    if len(visited_bins_candidate) == 0:
        return 0
    return len(set(visited_bins_h).intersection(visited_bins_candidate)) / len(visited_bins_candidate)


def area_coverage_recall(visited_bins_h: list[int], visited_bins_candidate: list[int]) -> float:
    """
    Calculate the recall of area coverage between two sets of visited bins
    
    Parameters:
    visited_bins_h (list[int]): The set of visited bins from the reference heat map
    visited_bins_candidate (list[int]): The set of visited bins from the candidate heat map
    
    Returns:
    float: The recall value, calculated as the ratio of the intersection of the two sets
           over the total number of bins in the reference set. Returns 0 if the reference set is empty
    """
    if len(visited_bins_h) == 0:
        return 0
    return len(set(visited_bins_h).intersection(visited_bins_candidate)) / len(visited_bins_h)


def calculate_area_coverage(visited_bins_h: list[int], visited_bins_candidate: list[int]) -> float:
    """
    Calculate the F1 score of area coverage between two heat maps
    
    Parameters:
    visited_bins_h (list[int]): The set of visited bins from the reference heat map
    visited_bins_candidate (list[int]): The set of visited bins from the candidate heat map
    
    Returns:
    float: The F1 score, calculated as the harmonic mean of precision and recall
           Returns 0 if both precision and recall are 0
    """
    precision = area_coverage_precision(visited_bins_h, visited_bins_candidate)
    recall = area_coverage_recall(visited_bins_h, visited_bins_candidate)
    return (2 * precision * recall) / (precision + recall) if (precision + recall) != 0 else 0



def get_profile_v(profile_h, precomputed_profiles, identifier_column):
    """
    Select profile v, the profile with the highest area coverage (utility) with profile h (profile to obfuscate).

    Args:
    - profile_h: The profile to be obfuscated.
    - precomputed_profiles: A dictionary containing precomputed profiles.

    Returns:
    - The profile with the highest area coverage with profile_h.
    """
    biggest_value = 0
    selected_candidate_id = None
    profile_h_visited_bins = profile_h.visited_bins

    # Remove profile_h from precomputed_profiles
    precomputed_profiles_sans_h = {k: v for k, v in precomputed_profiles.items() if k != profile_h.profile_data.iloc[0][identifier_column]}

    # Determine profile v, profile with the best utility (highest area coverage)
    for profile_candidate_id, data_candidate in precomputed_profiles_sans_h.items():
        if len(data_candidate.visited_bins) != 0:
            f_score = calculate_area_coverage(profile_h_visited_bins, data_candidate.visited_bins)
        else:
            print(f"0 Bins found for profile {profile_candidate_id}?!")
            continue

        if f_score > biggest_value:
            biggest_value = f_score
            selected_candidate_id = profile_candidate_id
    
    return precomputed_profiles[selected_candidate_id]


def get_profile_u(heat_map_h, precomputed_profiles, distance_type):

    """
    Selects profile u, the profile with the highest similarity (smallest topsoe divergence / hausdorff distance)
    """

    smallest_value = np.inf
    selected_candidate_id = None

    # Determine profile u, profile with the smallest topsoe divergence to the profile that shall be obfuscated, that is not the profile to obfuscate itself
    for profile_candidate_id, data_candidate in precomputed_profiles.items():

        topsoe_distance = calculate_distance_between_points(heat_map_h, data_candidate.heat_map, distance_type)
        
        if topsoe_distance < smallest_value and topsoe_distance > 0:
            smallest_value = topsoe_distance
            selected_candidate_id = profile_candidate_id
    
    return precomputed_profiles[selected_candidate_id]



def heat_map_alteration(profile_h_full, obfuscation_factor, all_precomputed_profiles, distance_type, max_count_iterations, identifier_column):
    """
    Modify a heat map based on given datasets and obfuscation parameters.

    Args:
    - profile_h: The target profile to be obfuscated.
    - obfuscation_factor: The factor determining the extent of obfuscation.
    - all_precomputed_profiles: A dictionary containing precomputed profiles.
    - max_count_iterations: The maximum number of iterations allowed for alteration.

    Returns:
    - Modified heat map of profile_h.
    - Counter for the number of iterations performed.
    """

    try:
        func_timer = timer()
        print(f"Starting {inspect.currentframe().f_code.co_name} at: {datetime.now()}")

        profile_h = profile_h_full[1]

        # Get the number of data points in profile_h
        amount_data_points_H = len(profile_h.profile_data)
        # Get the identifier column from profile_h
        profile_h_id = profile_h.profile_data.iloc[0][identifier_column]
        # Get the heat map of profile_h
        heat_map_h = profile_h.heat_map

        counter_while = 0
        
        # Get profile_u based on heat_map_h
        timer_u = timer()
        profile_u = get_profile_u(heat_map_h, all_precomputed_profiles, distance_type)
        
        profile_u_id = profile_u.profile_data.iloc[0][identifier_column]

        print(f"Distance between profile U {profile_u_id} and profile H {profile_h_id} is {calculate_distance_between_points(profile_u.heat_map, profile_h.heat_map, distance_type)}")

        # If h and u belong to a different owner, no need to obfuscation
        if profile_u_id != profile_h_id:
            print(f"Profile U: {profile_u_id} Profile H: {profile_h_id} belong to a different owner. No need for obfuscation. Returning H.")
            return profile_h_full, counter_while

        # Filter out profile_u from all_precomputed_profiles
        filtered_precomputed_profiles = {profile_id: data for profile_id, data in all_precomputed_profiles.items() if profile_id != profile_u_id}

        # Get profile_u again after filtering
        profile_u = get_profile_u(heat_map_h, filtered_precomputed_profiles, distance_type)

        profile_u_id = profile_u.profile_data.iloc[0][identifier_column]

        # Further filter to ensure profile_u is not used for profile_v selection
        filtered_precomputed_profiles_for_v = {profile_id: data for profile_id, data in filtered_precomputed_profiles.items() if profile_id != profile_u_id}

        # Get profile_v based on profile_h_visited_bins
        profile_v = get_profile_v(profile_h, filtered_precomputed_profiles_for_v, identifier_column)
        
        profile_v_id = profile_v.profile_data.iloc[0][identifier_column]

        counter_obfuscation = 0

        # Get heat maps of profile_u and profile_v
        heat_map_u = filtered_precomputed_profiles[profile_u_id].heat_map
        heat_map_v = filtered_precomputed_profiles[profile_v_id].heat_map #all_precomputed_profiles[profile_v_id].heat_map

        # Debug output to ensure U and V are different
        #print(f"Profile H ID: {profile_h_id},Profile U ID: {profile_u_id}, Profile V ID: {profile_v_id}")
        #print(f"Topsoe Divergence U-V: {calculate_distance_between_points(heat_map_u, heat_map_v)}")

        if profile_u_id == profile_v_id:
            raise ValueError("Profile U and Profile V should not be the same")

        heat_map_h_dash = heat_map_h
        diff_previous = 0

        while (calculate_distance_between_points(heat_map_h_dash, heat_map_v, distance_type) > calculate_distance_between_points(heat_map_h_dash, heat_map_u, distance_type) 
                and counter_obfuscation <= max_count_iterations and counter_while < 150000): # Hard cap for iterations to avoid out of memory scenarios
            
            #mem = psutil.virtual_memory() 
            #if mem.percent > memory_threshold:
            #    print("Memory usage too high. Cancelling Heat Map Alteration and returning Heat Map V as a substitute.")
            #    return heat_map_v, counter_while

            # Calculate matrices for obfuscation
            matrix_r = heat_map_h_dash * amount_data_points_H
            matrix_w = heat_map_h_dash * heat_map_v * (1 - heat_map_u)
            matrix_o = matrix_r + ((obfuscation_factor/np.sum(matrix_w)) *  matrix_w)
            matrix_h_dash = (1 / amount_data_points_H) * matrix_o

            topsoe_divergence_h_v = calculate_distance_between_points(heat_map_h_dash, heat_map_v, distance_type)
            topsoe_divergence_h_u = calculate_distance_between_points(heat_map_h_dash, heat_map_u, distance_type)

            counter_while += 1

            if (topsoe_divergence_h_v - topsoe_divergence_h_u) < diff_previous:
                counter_obfuscation = update_alteration_counter(counter_obfuscation, heat_map_h_dash, matrix_h_dash, heat_map_u, heat_map_v, True)
                heat_map_h_dash = matrix_h_dash
                diff_previous = topsoe_divergence_h_v - topsoe_divergence_h_u
                continue

            counter_obfuscation = update_alteration_counter(counter_obfuscation, heat_map_h_dash, matrix_h_dash, heat_map_u, heat_map_v, False)
            heat_map_h_dash = matrix_h_dash
            diff_previous = topsoe_divergence_h_v - topsoe_divergence_h_u

        print(f"Iteration {counter_while} finished. Topsoe Divergence H V = {calculate_distance_between_points(heat_map_h_dash, heat_map_v, distance_type)} Topsoe Divergence H U = {calculate_distance_between_points(heat_map_h_dash, heat_map_u, distance_type)}")
        print(f"{inspect.currentframe().f_code.co_name} execution finished after {timer() - func_timer} seconds")

        if counter_obfuscation >= max_count_iterations:
            print(f"No solution found within {counter_while} iterations. Returning heat map V as a substitute.")
            profile_h_full[1].heat_map = heat_map_v
            return profile_h_full, counter_while

        profile_h_full[1].heat_map = heat_map_h_dash
        return profile_h_full, counter_while

    finally:
        # Cleanup code to free resources
        gc.collect()
        #print(f"Resources have been cleaned up after {inspect.currentframe().f_code.co_name}")
