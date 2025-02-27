import pandas as pd



def fill_mobility_of_cell(list_of_all_available_time_gaps, set_of_mobility_traces_to_copy_from, max_speed_between_time_gaps, max_time_gap_inside_set_of_records, limit_duration_of_data_points_to_copy):
    
    """
    TODO: Complete function for mobility trace reconstruction. Check paper for rererence. 
    """
    # Filter list_of_all_available_time_gaps to fulfill being in cell i, j & are within max_speed_between_time_gaps

    # Split set_of_mobility_traces_to_copy_from by max_time_gap_inside_set_of_records

    # Select element from list_of_all_available_time_gaps & set_of_mobility_traces_to_copy_from with least distance. Distance is the sum of the distance\
    # from start of the gap to the set of records AND from the set of records to the ending point of the gap
    None



def mobility_trace_reconstruction(obfuscated_heat_map, original_mobility_trace):

    """
    TODO: Complete function for mobility trace reconstruction. Check paper for rererence. 
    """

    modified_mobility_trace = modify_number_of_records(original_mobility_trace, len(obfuscated_heat_map))
    #modify_number_of_records(original_mobility_trace, amount_target_datapoints)
    #print(modified_mobility_trace)



def modify_number_of_records(mobility_trace, amount_target_datapoints):
    P = mobility_trace.copy()
    P['Timestamp'] = pd.to_datetime(P['Timestamp'], format='%d.%m.%Y %H:%M', errors='coerce')
    P_dash = pd.DataFrame(columns=P.columns)

    while len(P_dash) < amount_target_datapoints:
        P_dash = pd.concat([P_dash, P.iloc[[0]]], ignore_index=True)

        for i in range(1, len(P)):
            p_mid = pd.DataFrame(index=[0], columns=P.columns)
            p_mid["Longitude"] = (P["Longitude"].iloc[i - 1] + P["Longitude"].iloc[i]) / 2
            p_mid["Latitude"] = (P["Latitude"].iloc[i - 1] + P["Latitude"].iloc[i]) / 2
            
            timestamp_difference = (P["Timestamp"].iloc[i] - P["Timestamp"].iloc[i - 1]) / 2
            p_mid["Timestamp"] = P["Timestamp"].iloc[i - 1] + timestamp_difference

            P_dash = pd.concat([P_dash, p_mid], ignore_index=True)
            P_dash = pd.concat([P_dash, P.iloc[[i]]], ignore_index=True)
            #print("Added entry at index", i)

        P = P_dash.copy()

    print(P.head(100))
    P["FileName"] = P["FileName"][0]
    #print(P)
    print(f"Original Length: {len(mobility_trace)} New Length: {len(P)}")
    #random_selection = random.choices(P, weights = None, cum_weights = None, k = amount_target_datapoints)
    #print(random_selection)
    return P

