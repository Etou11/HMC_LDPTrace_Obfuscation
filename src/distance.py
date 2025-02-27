# Libraries / packages
import numpy as np
import scipy
import scipy.spatial


def calculate_distance_between_points(array_a, array_b, distance_type):

    if distance_type == "TOPSOE":
        distance = calculate_topsoe_divergence(array_a, array_b)
        return distance
    elif distance_type == "HAUSDORFF":
        return calculate_hausdorff_distance(array_a, array_b)
    else:
        raise Exception("Missing or invalid selection of distance calculation algorithm!")


def calculate_topsoe_divergence(P_ij, Q_ij):
    return np.sum(P_ij * np.log(2 * P_ij / (P_ij + Q_ij))) + np.sum(Q_ij * np.log(2 * Q_ij / (P_ij + Q_ij)))


def calculate_hausdorff_distance(array_a, array_b):
    return scipy.spatial.distance.directed_hausdorff(array_a, array_b)[0]