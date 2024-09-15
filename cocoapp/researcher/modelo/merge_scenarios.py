import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

def norm_matrix(matrix):
    return matrix.apply(lambda x: (x - x.mean()) / x.std(), axis=1)

def kantorovich_distance(df):
    # Transpose the DataFrame if there are more columns than rows
    if df.shape[1] > df.shape[0]:
        df = df.T
    return squareform(pdist(df, 'euclidean'))


def initialize_probability_matrix(num_rows, num_scenarios):
    return np.full((num_rows, num_scenarios), 1.0 / num_scenarios)

def select_scenarios_to_merge(Kan_dis, pi_vector, active_scenarios):
    min_cost = float('inf')
    scenario_to_merge = -1
    E_max = 1

    scenario_index_map = {scenario: index for index, scenario in enumerate(active_scenarios)}

    for i, scenario_i_name in enumerate(active_scenarios):
        for j, scenario_j_name in enumerate(active_scenarios):
            if i != j:
                scenario_i_index = scenario_index_map[scenario_i_name]
                scenario_j_index = scenario_index_map[scenario_j_name]
                cost = Kan_dis[scenario_i_index, scenario_j_index] * pi_vector[scenario_i_index] * pi_vector[scenario_j_index]

                if cost < min_cost:
                    min_cost = cost
                    scenario_to_merge = (i, j)
                    E_max = max(E_max, sum(Kan_dis[scenario_i_index, :]) * pi_vector[scenario_i_index])

    return scenario_to_merge, min_cost, E_max

# The rest of the code remains the same


def merge_scenarios(df, Q, Tol, a):
    if not(Tol is None):
        Tol = float(Tol)
    a = float(a)

    if Tol is None:
        Tol = 0.2
    norm_df = norm_matrix(df)
    Kan_dis = kantorovich_distance(norm_df)
    num_rows, num_scenarios = df.shape
    pi_matrix = initialize_probability_matrix(num_rows, num_scenarios)
    merge_history = []
    active_scenarios = df.columns.tolist()
    scenario_probabilities = {scenario: 1.0 / num_scenarios for scenario in df.columns}

    for t in range(num_rows - 1, -1, -1):
        scenarios_merged_in_step = False

        while len(active_scenarios) > min((Q if Q is not None else 1), len(Kan_dis)):
            scenario_to_merge, min_cost, E_max = select_scenarios_to_merge(Kan_dis, pi_matrix[t, :len(active_scenarios)], active_scenarios)
            Tol_rel = min_cost / E_max
            T = Tol / (a ** (num_rows - 1 - t))

            #print(f"Time Step: {t}, Tol_rel: {Tol_rel}, T: {T}")

            if Tol_rel < T and scenario_to_merge != -1:
                scenarios_merged_in_step = True
                merged_scenario_name, closest_scenario_name = [active_scenarios[i] for i in scenario_to_merge]

                pi_matrix[t, scenario_to_merge[1]] += pi_matrix[t, scenario_to_merge[0]]
                pi_matrix[t, scenario_to_merge[0]] = 0

                active_scenarios.remove(merged_scenario_name)
                merge_history.append((merged_scenario_name, closest_scenario_name, t))

                Kan_dis = np.delete(Kan_dis, scenario_to_merge[0], axis=0)
                Kan_dis = np.delete(Kan_dis, scenario_to_merge[0], axis=1)
                pi_matrix = np.delete(pi_matrix, scenario_to_merge[0], axis=1)

                merged_probability = scenario_probabilities.pop(merged_scenario_name)
                scenario_probabilities[closest_scenario_name] += merged_probability

                updated_probabilities = pi_matrix[t, :len(active_scenarios)]
                #print(f"Merging scenarios: {merged_scenario_name} into {closest_scenario_name}, Updated Probabilities: {updated_probabilities}")
                #print("Updated Kantorovich Distance Matrix:")
                #print(np.array2string(Kan_dis, formatter={'float_kind':lambda x: "%.2f" % x}))


                #print(f"Merging scenarios: {merged_scenario_name} into {closest_scenario_name}")
            else:
                #print(f"No feasible merge found at Time Step: {t}, advancing to next timestep")
                break

        if not scenarios_merged_in_step and t < num_rows - 1:
            pi_matrix[t + 1, :len(active_scenarios)] = pi_matrix[t, :len(active_scenarios)]
            print(f"Advancing to Time Step: {t + 1}")

    final_probabilities = [scenario_probabilities[scenario] for scenario in active_scenarios]

    print(f"Debug: Final Probabilities before extraction: {pi_matrix[-1]}")
    print(f"Active Scenarios: {active_scenarios}")
    print(f"Final Columns: {df[active_scenarios].columns}")
    print(f"Final Probabilities: {final_probabilities}")
    print(f"Merge History: {merge_history}")

    return df[active_scenarios].columns, final_probabilities, merge_history