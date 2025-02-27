import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.cluster import KMeans

def split_data_frame_list_by_cluster(profiles_list):

    raise Exception("Functionality currently not possible. Expects list, gets df")

    first_half_list = []
    last_half_list = []

    for profile in profiles_list:
        if len(profile) > 1:  # Check if the DataFrame contains at least two data points
            # Calculate the number of clusters, limited to a minimum of 3 and a maximum of 5
            num_clusters = max(3, min(5, len(profile) // 2))
            # Perform K-Means clustering to identify clusters of geographic regions
            kmeans = KMeans(n_clusters=num_clusters, random_state=42)
            profile['Cluster'] = kmeans.fit_predict(profile[['Latitude', 'Longitude']])

            # Randomly split each cluster into two parts
            cluster_data_frames = []
            for cluster in range(num_clusters):
                cluster_data = profile[profile['Cluster'] == cluster]
                split_point = len(cluster_data) // 2
                shuffled_indices = np.random.permutation(cluster_data.index)
                first_part = cluster_data.loc[shuffled_indices[:split_point]]
                second_part = cluster_data.loc[shuffled_indices[split_point:]]
                cluster_data_frames.append((first_part, second_part))

            # Combine the parts of all clusters
            first_parts = pd.concat([df[0] for df in cluster_data_frames], ignore_index=True)
            last_parts = pd.concat([df[1] for df in cluster_data_frames], ignore_index=True)

            # Store the parts in the lists
            first_half_list.append(first_parts[['Longitude', 'Latitude', 'FileName']])
            last_half_list.append(last_parts[['Longitude', 'Latitude', 'FileName']])
        else:
            # If there are fewer than two data points, add the entire DataFrame to both lists
            first_half_list.append(profile[['Longitude', 'Latitude', 'FileName']])
            last_half_list.append(profile[['Longitude', 'Latitude', 'FileName']])

    return first_half_list, last_half_list



def split_data_frame_list_by_half(profiles_df):

    """
    Splits each DataFrame in a list of DataFrames into two halves
    """

    first_part_df = profiles_df.copy()
    last_part_df = profiles_df.copy()

    first_part_df["DataFrames"] = first_part_df["DataFrames"].apply(
        lambda df: df.iloc[:len(df) // 2] if len(df) > 1 else df
    )

    last_part_df["DataFrames"] = last_part_df["DataFrames"].apply(
        lambda df: df.iloc[len(df) // 2:] if len(df) > 1 else pd.DataFrame()
    )

    return first_part_df, last_part_df


def split_data_frame_list_randomly(profiles_df, seed):

    """
    Splits each DataFrame in a list of DataFrames into two halves with random lengths
    """
    np.random.seed(seed)

    first_part_df = profiles_df.copy()
    last_part_df = profiles_df.copy()

    def split_dataframe(df, seed):
        if len(df) > 1:
            np.random.seed(seed)
            split_index = np.random.randint(1, len(df))
            return df.iloc[:split_index], df.iloc[split_index:]
        else:
            return df, pd.DataFrame()

    split_results = first_part_df["DataFrames"].apply(lambda df: split_dataframe(df, seed))

    first_part_df["DataFrames"] = split_results.apply(lambda x: x[0])
    last_part_df["DataFrames"] = split_results.apply(lambda x: x[1])

    return first_part_df, last_part_df



def split_data_frame_list_top_30(profiles_list):

    """
    Splits a single data set in half - Based upon the 30 most active days (days with most data points) for each individual profile
    """

    raise Exception("Functionality currently not possible. Expects list, gets df")

    first_part = []
    last_part = []

    for df in profiles_list:

        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
        df['Date'] = df['Timestamp'].dt.date
        
        date_grouped = df.groupby('Date').size().reset_index(name='counts')
        
        top_30_days = date_grouped.nlargest(30, 'counts')['Date']
        
        first_half_df = pd.DataFrame()
        last_half_df = pd.DataFrame()
        
        for day in top_30_days:
            day_entries = df[df['Date'] == day]
            day_entries = day_entries.sort_values('Timestamp')
            mid_point = len(day_entries) // 2
            
            first_half = day_entries.iloc[:mid_point]
            last_half = day_entries.iloc[mid_point:]
            
            first_half_df = pd.concat([first_half_df, pd.DataFrame(first_half)], ignore_index=True)
            last_half_df = pd.concat([last_half_df, pd.DataFrame(last_half)], ignore_index=True)
        
        first_part.append(first_half_df)
        last_part.append(last_half_df)

    return first_part, last_part



def split_data_frame_list_by_date(profiles_list):

    """
    Splits a single data set into two (one as a baseline data set, the other one as a comparee data set) - Based upon date (Timestamp)
    """
    raise Exception("Functionality currently not possible. Expects list, gets df")

    first_80_percent = []
    last_20_percent = []

    # 29.05.2008 -> 50/50 Split     06.04.2008 -> 80/20 Split
    time_limit_str = "29.05.2008 23:59"
    datetime_limit = datetime.strptime(time_limit_str,'%d.%m.%Y %H:%M')


    for df in profiles_list:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
        df = df.sort_values('Timestamp')

        split_index = df[df['Timestamp'] > datetime_limit].first_valid_index()

        if split_index is not None:
            first_80_df = df.loc[:split_index - 1]
            first_80_df = first_80_df.loc[::5]
            last_20_df = df.loc[split_index:]
            last_20_df = last_20_df.loc[::5]
        else:
            first_80_df = df
            last_20_df = pd.DataFrame()

        first_80_percent.append(first_80_df)
        last_20_percent.append(last_20_df)

    return first_80_percent, last_20_percent


def split_single_dataframe(selected_profile):

    """
    (DEPRECATED) Splits a single trajectory (data set) in sub trajectories, depending on the value in "Occupied". A sub trajectory beigns and ends when the value of "Occupied" changes
    """
    
    # Find start of trajectory
    start_traj = selected_profile['Occupied'].diff() == 1

    # Find end of trajcetory
    end_traj = selected_profile['Occupied'].diff() == -1

    # Create new trajectory
    selected_profile['Trajectory_ID'] = (start_traj.cumsum() + end_traj.cumsum()).fillna(0).astype(int)

    # Group data frame by trajectory id
    grouped = selected_profile.groupby('Trajectory_ID')

    # Save trajectories in dictionary
    trajectories_list = [group.copy() for _, group in grouped]

    return trajectories_list
