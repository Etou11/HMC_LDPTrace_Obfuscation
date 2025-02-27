import numpy as np
from datetime import datetime
from timeit import default_timer as timer

from distance import calculate_distance_between_points
from hmc import heat_map_alteration


def ap_attack_processing(all_profiles_to_deobfuscate, all_compare_profiles, distance_type, results, obfuscation_type, identifier_column):

    func_timer = timer()
    print(f"AP-Attack started at {datetime.now()}")

    if obfuscation_type == "HMC":

        for profile_to_deobfuscate in all_profiles_to_deobfuscate.items():
            ap_timer = timer()

            obfuscation_factor = max(len(profile_to_deobfuscate[1].profile_data.iloc[0][identifier_column]) / 500, 50)
            hmc_obfuscated_profile, amount_iterations = heat_map_alteration(profile_to_deobfuscate, obfuscation_factor, all_compare_profiles, distance_type, 1000, identifier_column)

            results = ap_attack(hmc_obfuscated_profile, all_compare_profiles, results, distance_type, amount_iterations)
            print(f"Calculating smallest {distance_type} distance for profile {profile_to_deobfuscate[0]} took {timer() - ap_timer:.2f} seconds")

    else:

        for profile_to_deobfuscate in all_profiles_to_deobfuscate.items():
            ap_timer = timer()
            results = ap_attack(profile_to_deobfuscate, all_compare_profiles, results, distance_type)
            print(f"Calculating smallest {distance_type} distance for profile {profile_to_deobfuscate[0]} took {timer() - ap_timer:.2f} seconds")

    print(f"AP-Attack on {obfuscation_type.upper()} profiles with {distance_type} distance took {timer() - func_timer:.2f} seconds in total")

    return results


def ap_attack(profile_to_deobfuscate: tuple, all_compare_profiles: dict, results: list, distance_type: str, amount_iterations: str = "") -> list:
    """
    Find the closest matching profile based on heat map distances

    Parameters:
    profile_to_deobfuscate (tuple): Name and profile data (with heat map) to be deobfuscated
    all_compare_profiles (dict): Profile names and data (with heat maps) for comparison
    results (list): List to append the comparison results
    distance_type (str): Type of distance metric (e.g., 'topsoe', 'hausdorff')
    amount_iterations (str, optional): Number of iterations for the results

    Returns:
    list: Updated list of results
    """
    smallest_distance, smallest_distance_name = np.inf, ""
    
    for name, profile in all_compare_profiles.items():
        distance = calculate_distance_between_points(profile_to_deobfuscate[1].heat_map, profile.heat_map, distance_type)

        if distance < smallest_distance:
            smallest_distance, smallest_distance_name = distance, name
            print(f"Smallest Distance: {smallest_distance} to profile: {smallest_distance_name}")

    results.append({
        'Baseline': profile_to_deobfuscate[0],
        'Comparee': smallest_distance_name,
        'Distance': smallest_distance,
        'Iterations': amount_iterations,
        "Equal File Name": "Yes" if smallest_distance_name == profile_to_deobfuscate[0] else "No"
    })
    
    return results





