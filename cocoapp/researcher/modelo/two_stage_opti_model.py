from pulp import LpVariable, LpProblem, LpMaximize, lpSum, LpStatus,PULP_CBC_CMD, LpStatusOptimal
from .data import import_data_clim
from .decision_model import fTemp, fHeat, fSolar
from pulp import PULP_CBC_CMD
import pulp
import pandas as pd
import math
import numpy as np
import math

def RN(alfa, RS, RSO, SIGMA, TMIN, TMAX, RHMEAN, temp, Altitude, n, E, Cp, G, WS2M):
    eTMAX = [0.6108 * math.exp((17.27 * TMAX[i]) / (TMAX[i] + 237.3)) for i in range(len(TMAX))]
    eTMIN = [0.6108 * math.exp((17.27 * TMIN[i]) / (TMIN[i] + 237.3)) for i in range(len(TMIN))]
    ea = [(RHMEAN[i] / 100) * ((eTMAX[i] + eTMIN[i]) / 2) for i in range(len(RHMEAN))]
    TMAXK = [TMAX[i] + 273.16 for i in range(len(TMAX))]
    TMINK = [TMIN[i] + 273.16 for i in range(len(TMIN))]
    RNS = [(1 - alfa) * RS[i] for i in range(len(RS))]
    RNL = [SIGMA * ((TMINK[i]**4 + TMAXK[i]**4) / 2) * (0.34 - 0.14 * (ea[i]**0.5)) * (1.35 * (RS[i] / RSO[i]) - 0.35) for i in range(len(TMIN))]
    RN = [RNS[i] - RNL[i] for i in range(len(TMIN))]
    A = [4098 * (0.6108 * math.exp(17.27 * temp[i] / (temp[i] + 237.3))) / (temp[i] + 237.3)**2 for i in range(len(temp))]
    es = [(eTMAX[i] + eTMIN[i]) / 2 for i in range(len(TMIN))]
    es_ea = [es[i] - ea[i] for i in range(len(temp))]
    P = 101.3 * ((293 - 0.0065 * Altitude) / 293)**5.26
    y = ((Cp * P) / (n * E))
    ETO = [(0.408 * A[i] * (RN[i] - G) + y * (900 / (temp[i] + 273)) * WS2M[i] * es_ea[i]) / (A[i] + y * (1 + 0.34 * WS2M[i])) for i in range(len(temp))]
    KS = [1] * (int(len(ETO) * 5 / 18)) + [1.05] * (len(ETO) - int(len(ETO) * 5 / 18))
    ETC = [KS[i] * ETO[i] for i in range(len(ETO))]
    return ETO, ETC


def calculate_evaporation(df, eto):
    """Calculate evaporation based on scenario-specific precipitation and ETO."""
    return [(h * 0.2 if p > 0 and p >= h * 0.2 else p) for p, h in zip(df, eto)]


def escen_df(s, escen_prectotcorr):
    escn = {}
    str_index = str(s)

    if str_index in escen_prectotcorr:
        escn[str_index] = escen_prectotcorr[str_index]
    
    df_scen = pd.DataFrame.from_dict(escn, orient='index')
    df_scen = df_scen.transpose()
    df_scen.index = df_scen.index.str.replace('S', '').astype(int)
    #df_scen = df_scen.apply(pd.to_numeric)
    df_scen = df_scen[str_index]

    return df_scen

def two_stage_model(df, merg_sce_colum_prect, merg_sce_probs_prect, escen_prectotcorr):

    # Fixed parameters
    CRUE = 0.296
    CHI = 0.0706
    fSolarmax = 0.94
    I50A = 680
    I50B = 200
    Tsum = 2764
    Tbase = 10
    Topt = 24
    Theat = 32
    Textreme = 38
    Swater = 0.6053
    critical_depletion = 94.08
    critical_water = 140
    SCO2 = 6.7249
    alfa = 0.23
    SIGMA = 0.000000004903
    Altitude = 658
    n = 2.45
    E = 0.622
    Cp = 1.013 / 1000
    G = 0

    # Calculated constants
    CCh = CRUE * CHI

    # Apply environmental stress functions (assuming these functions are defined elsewhere in your code)
    df['FTemp'] = fTemp(Tbase, Topt, pd.to_numeric(df['t2mdew'])).values
    df['FHeat'] = fHeat(Theat, Textreme, pd.to_numeric(df['t2m_max'])).values
    df['FSolar'] = fSolar(fSolarmax, I50A, I50B, Tsum, Tbase, pd.to_numeric(df['t2mdew'])).values
    df['EF_t'] = pd.to_numeric(df['allsky_sfc_sw_dwn']) * df['FSolar'] * SCO2 * df['FTemp']

    #### Adding depletion
    # Calculate ETO and ETC
    ETO, ETC = RN(alfa, pd.to_numeric(df['allsky_sfc_sw_dwn']), pd.to_numeric(df['clrsky_sfc_sw_dwn']), SIGMA, pd.to_numeric(df['t2m_min']), pd.to_numeric(df['t2m_max']), pd.to_numeric(df['rh2m']), (pd.to_numeric(df['t2m_min'])+pd.to_numeric(df['t2m_max']))/2, Altitude, n, E, Cp, G, pd.to_numeric(df['ws2m']))

    """
    # Define scenarios
    scenarios = ['1', '2', '3']
    probabilities = {'1': 0.3, '2': 0.3, '3': 0.4}
    # Create scenarios with adjusted precipitation
    df["P15_1"] = df["PRECIPITATION"] * 0.1
    df["P15_2"] = df["PRECIPITATION"] * 0.5 + np.random.normal(0.5, 0.05, 15)
    df["P15_3"] = df["PRECIPITATION"] * 0.1 + np.random.normal(2, 0.01, 15)
    """
    # Evaporation by scenario
    # Dictionary to store evaporation for each scenario
    evaporated = {}

    # Assuming 'scenarios' is a list of scenario identifiers and 'ETO' is a predefined list of evapotranspiration values
    for s in merg_sce_colum_prect:
        df_scen = escen_df(s, escen_prectotcorr)
        evaporated[s] = calculate_evaporation(df_scen, ETO)
    
    # Now, 'evaporated' dictionary contains the evaporation lists for each scenario


    # Initialize the problem
    model = LpProblem("Two_Stage_Optimization_with_Precipitation_Scenarios", LpMaximize)


    # Stage 1 Decision Variables (scenario-independent)
    # Define scenario-specific irrigation and drainage variables at the initial stage
    I_t0 = {s: LpVariable(f"Irrigation_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    D_t0 = {s: LpVariable(f"Draining_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    W_t = {s: LpVariable(f"W_t_{s}", lowBound=critical_depletion, cat='Continuous') for s in merg_sce_colum_prect}
    DR_t0 = {s: LpVariable(f"Depletion_t_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    # Auxiliar variables
    x_minus0 = {s: LpVariable(f"xminus_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    x_plus0 = {s: LpVariable(f"xplus_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    y_minus0 = {s: LpVariable(f"yminus_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    y_plus0 = {s: LpVariable(f"yplus_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    f_water0 = {s: LpVariable(f"fwater_t0_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}


    print(f"Stage 1 Variables: {I_t0}, {D_t0}, {W_t}")

    # Initialize scenario-independent variables at t=0
    W_0 = LpVariable('W_0', lowBound=critical_depletion, upBound=critical_water, cat='Continuous')
    W_0.setInitialValue(critical_water)
    DR_0 = LpVariable('DR_0', lowBound=0, cat='Continuous')
    DR_0.setInitialValue(0)

    print(f"Initial Condition Variables: {W_0} (Initial Water), {DR_0} (Initial Depletion)")

    # Stage 2 Decision Variables (scenario-dependent)


    I_t15 = {s: LpVariable(f'Irrigation_t15_{s}', lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    D_t15 = {s: LpVariable(f'Draining_t15_{s}', lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    W_t15 = {s: LpVariable(f"W_t15_{s}", lowBound=critical_depletion, upBound=critical_water, cat='Continuous') for s in merg_sce_colum_prect}
    DR_t15 = {s: LpVariable(f"Depletion_t15_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    # Auxiliar variables
    x_minus15 = {s: LpVariable(f"xminus_t15_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    x_plus15 = {s: LpVariable(f"xplus_t15_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    y_minus15 = {s: LpVariable(f"yminus_t15_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    y_plus15 = {s: LpVariable(f"yplus_t15_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}
    f_water15 = {s: LpVariable(f"fwater_t15_{s}", lowBound=0, cat='Continuous') for s in merg_sce_colum_prect}


    # Objective Function
    # Calculate contributions from stage 1
    objective_contributions_t1 = []
    idx_probs = 0
    for s in merg_sce_colum_prect:
        contribution_t1 = CCh * ((f_water0[s]*df['EF_t'][0]) - (x_minus0[s]*df['EF_t'][0]) )
        objective_contributions_t1.append(merg_sce_probs_prect[idx_probs] * contribution_t1)
        idx_probs +1

    # Calculate contributions from stage 2
    objective_contributions_t15 = []
    idx_probs = 0
    for s in merg_sce_colum_prect:
        contribution_t15 = merg_sce_probs_prect[idx_probs] * CCh * ((f_water15[s]*df['EF_t'].iloc[14]) - (x_minus15[s]*df['EF_t'].iloc[14]))
        objective_contributions_t15.append(contribution_t15)
        idx_probs +1

    # Constraints
    # Non-anticipativity constraint for W_t across scenarios
    for s1 in merg_sce_colum_prect:
        for s2 in merg_sce_colum_prect:
            if s1 != s2:

                model += I_t0[s1] == I_t0[s2], f"Non_Anticipativity_I_t0_{s1}_{s2}"
                model += D_t0[s1] == D_t0[s2], f"Non_Anticipativity_D_t0_{s1}_{s2}"


    # Base scenario constraints at time t with scenario-specific irrigation and drainage
    for s in merg_sce_colum_prect:
        df_scen = escen_df(s, escen_prectotcorr)
        model += ((ETC[0] + D_t0[s] + evaporated[s][0]) - (df_scen.iloc[0] + I_t0[s] + DR_0)) == DR_t0[s], f"Depletion_Calculation_t_{s}"
        model += (W_0 + df_scen.iloc[0] + I_t0[s]) - (D_t0[s] + ETC[0] + evaporated[s][0] + DR_0) <= W_t[s], f"Water_Balance_at_t1_Scenario_{s}"


    # model += critical_water <= W_t[s] + DR_t0[s], f"PAW_t{s}" #New constraint


    # Assuming initialization of scenarios, t_final, df, and ETC
    t_final = 15  # Define the final time step
    current_W_t = {}  # Dictionary to store water level variables
    current_DR_t = {}  # Dictionary to store water level variables
    current_RO_t = {}  # Dictionary to store runoff level variables
    for s in merg_sce_colum_prect:
        # Initialize W_t_next for the first calculation from previously defined initial conditions
        # current_W_t[(s, 1)] = LpVariable(f"W_1_{s}", lowBound=critical_depletion, cat='Continuous')
        df_scen = escen_df(s, escen_prectotcorr)

        for t in range(2, t_final):  # Loop from t=2 to t_final (inclusive)
            # Create a unique LpVariable for each scenario and time step
            current_W_t[(s, t)] = LpVariable(f"W_{t}_{s}", lowBound=0,  cat='Continuous')
            current_DR_t[(s, t)] = LpVariable(f"DR_{t}_{s}", lowBound=0, cat='Continuous')
            current_RO_t[(s, t)] = LpVariable(f"RunOff_{t}_{s}", lowBound=0, cat='Continuous')
            # Calculate water balance using the correct previous water level
            # model += critical_depletion <= current_W_t[(s, t)] <= critical_water
            if t == 2:
                # Use W_t[s] as the lagged value for t=2 (assuming W_t[s] is defined for t=1)
                model += (ETC[t-1] + evaporated[s][t-1]+current_RO_t[(s, t)]) - (df_scen.iloc[t-1] + DR_t0[s]) == current_DR_t[(s, t)], f"Depletion_Calculation_at_t{t}_Scenario_{s}"
                model += (W_t[s] + df_scen.iloc[t-1]) - (ETC[t-1] + DR_t0[s]+current_RO_t[(s, t)]+evaporated[s][t-1]) == current_W_t[(s, t)], f"Water_Balance_at_t{t}_Scenario_{s}"

                # model += critical_water-current_DR_t[(s, t)] <= current_W_t[(s, t)], f"PAW_t{s}_{t}" #New constraint

            else:
                # Use the previous time step's water level for t > 2
                model += (ETC[t-1] + evaporated[s][t-1]+current_RO_t[(s, t)]) - (df_scen.iloc[t-1] + current_DR_t[(s, t-1)]) == current_DR_t[(s, t)], f"Depletion_Calculation_at_t{t}_Scenario_{s}"
                model += (current_W_t[(s, t-1)] + df_scen.iloc[t-1]) - (ETC[t-1]+ current_DR_t[(s, t-1)]+current_RO_t[(s, t)]+evaporated[s][t-1]) == current_W_t[(s, t)], f"Water_Balance_at_t{t}_Scenario_{s}"

                # model += critical_water-current_DR_t[(s, t)] == current_W_t[(s, t)], f"PAW_t{s}_{t}" #New constraint


    # Analyze cases when depletion is negative due to environmental conditions, check the feasibility of constrains especially when calculate depeation daily
    # Base scenario constraints at time t=15  with scenario-specific irrigation and drainage
    for s in merg_sce_colum_prect:
        df_scen = escen_df(s, escen_prectotcorr)
        model += (ETC[14] + evaporated[s][14]+D_t15[s]) - (df_scen.iloc[14] +I_t15[s]+ current_DR_t[(s, 14)]) == DR_t15[s], f"Depletion_Calculation_at_t15_Scenario_{s}"
        model += (current_W_t[(s, 14)] + df_scen.iloc[14] + I_t15[s]) - (D_t15[s] +ETC[14]+evaporated[s][t-1] + current_DR_t[(s, 14)]) == W_t15[s], f"Water_Balance_at_t15_Scenario_{s}"
        model += critical_depletion <= W_t15[s] <= critical_water
        # model += critical_water-DR_t15[s] <= W_t15[s], f"PAW_t15{s}" #New constraint

    ## Other constrains for t = 1
    for s in merg_sce_colum_prect:
        model += f_water0[s] - x_minus0[s] + x_plus0[s]  == df['FHeat'][0]
        model += 0.096 * W_t[s]  - y_minus0[s]  + y_plus0[s]  ==  (ETC[0]+evaporated[s][0])
        model += f_water0[s]  - (0.096 * Swater / (ETC[0]+evaporated[s][0])) * W_t[s] + (Swater /( ETC[t]+evaporated[s][0])) * y_minus0[s] == 1 - Swater

    ## Other constrains for t = 15
    for s in merg_sce_colum_prect:
        model += f_water0[s] - x_minus15[s] + x_plus15[s]  == df['FHeat'][14]
        model += 0.096 * W_t15[s]  - y_minus15[s]  + y_plus15[s]  ==  (ETC[14]+evaporated[s][14])
        model += f_water15[s]  - (0.096 * Swater / (ETC[14]+evaporated[s][14])) * W_t15[s] + (Swater /( ETC[14]+evaporated[s][14])) * y_minus15[s] == 1 - Swater


    # Solve the model with CBC solver and specify tolerance
    from pulp import PULP_CBC_CMD

    solver = PULP_CBC_CMD(msg=True, options=['-feasTol', '1e-8', '-optTol', '1e-8','iisfind'])
    model.solve(solver)

    result = {}
    for s in merg_sce_colum_prect:
        result[s] = {'I_T0': I_t0[s].varValue, 'D_T0': D_t0[s].varValue, 'I_T15': I_t15[s].varValue, 'D_T15': D_t15[s].varValue,}

    """
    print("Solution Status:", LpStatus[model.status])
    print("Show balance for initial t")
    for s in merg_sce_colum_prect:
        df_scen = escen_df(s, escen_prectotcorr)
        precipitation = df_scen.iloc[0]
        print(f'Irrigation: {I_t0[s].varValue} Drainage: {D_t0[s].varValue}')
        print(f"DR for Scenario {s}: {ETC[0]}+{D_t0[s].varValue}+ {evaporated[s][0]}- {precipitation} - {I_t0[s].varValue} - {DR_0.varValue} == {DR_t0[s].varValue}")
        print(f"DR for Scenario {s}: {ETC[0]+D_t0[s].varValue + evaporated[s][0] - precipitation - I_t0[s].varValue + DR_0.varValue} == {DR_t0[s].varValue}")
        print(f"W for Scenario {s}: {W_0.value()} + {precipitation} + {I_t0[s].varValue} - {D_t0[s].varValue} - {ETC[0]} - {DR_0.varValue} <= {W_t[s].varValue}")
        print(f"W for Scenario {s}: {W_0.value() + precipitation + I_t0[s].varValue - D_t0[s].varValue - ETC[0] - DR_0.varValue} <= {W_t[s].varValue}")

    # Debugging: Show balance for t = 15
    for s in merg_sce_colum_prect:
        df_scen = escen_df(s, escen_prectotcorr)
        precipitation = df_scen.iloc[14]
        print(f'Scenario: {s}')
        print(f'Irrigation at t=15: {I_t15[s].varValue}, Drainage at t=15: {D_t15[s].varValue}')
        print(f"DR for Scenario {s} at t=15: {ETC[14]} + {evaporated[s][14]} + {D_t15[s].varValue} - {precipitation} - {I_t15[s].varValue} - {current_DR_t[(s, 14)].varValue} == {DR_t15[s].varValue}")
        print(f"DR for Scenario {s} at t=15 (Calculated): {ETC[14] + evaporated[s][14] + D_t15[s].varValue - precipitation - I_t15[s].varValue - current_DR_t[(s, 14)].varValue} == {DR_t15[s].varValue}")
        print(f"W for Scenario {s} at t=15: {current_W_t[(s, 14)].varValue} + {precipitation} + {I_t15[s].varValue} - {D_t15[s].varValue} - {ETC[14]} - {evaporated[s][14]} - {current_DR_t[(s, 14)].varValue} <= {W_t15[s].varValue}")
        print(f"W for Scenario {s} at t=15 (Calculated): {current_W_t[(s, 14)].varValue + precipitation + I_t15[s].varValue - D_t15[s].varValue - ETC[14] - evaporated[s][14] - current_DR_t[(s, 14)].varValue} <= {W_t15[s].varValue}")


    # Debugging: Show balance for each time step and scenario
    for s in merg_sce_colum_prect:
        df_scen = escen_df(s, escen_prectotcorr)
        for t in range(2, t_final):
            precipitation = df_scen.iloc[t-1]
            print(f'Scenario: {s}, Time step: {t}')
            print(f'Precipitation at t={t}: {precipitation}')
            print(f"Final available water at t={t}: {current_W_t[(s, t)].varValue}")
            print(f"DR for Scenario {s} at t={t}: {ETC[t-1]} + {evaporated[s][t-1]} + {current_RO_t[(s, t)].varValue} - {precipitation} - {DR_t0[s].varValue if t == 2 else current_DR_t[(s, t-1)].varValue} == {current_DR_t[(s, t)].varValue}")
            print(f"DR for Scenario {s} at t={t} (Calculated): {ETC[t-1] + evaporated[s][t-1] + current_RO_t[(s, t)].varValue - precipitation - (DR_t0[s].varValue if t == 2 else current_DR_t[(s, t-1)].varValue)} == {current_DR_t[(s, t)].varValue}")
            print(f"W for Scenario {s} at t={t}: {W_t[s].varValue if t == 2 else current_W_t[(s, t-1)].varValue} + {precipitation} - {ETC[t-1]} - {current_RO_t[(s, t)].varValue} - {DR_t0[s].varValue if t == 2 else current_DR_t[(s, t-1)].varValue} - {evaporated[s][t-1]} == {current_W_t[(s, t)].varValue}")
            print(f"W for Scenario {s} at t={t} (Calculated): {(W_t[s].varValue if t == 2 else current_W_t[(s, t-1)].varValue) + precipitation - ETC[t-1] - current_RO_t[(s, t)].varValue - (DR_t0[s].varValue if t == 2 else current_DR_t[(s, t-1)].varValue) - evaporated[s][t-1]} == {current_W_t[(s, t)].varValue}")
    """
    
    return model, result

def result_scen(idx, dic):
    result = {}
    for i in idx:
        str_index = str(i)
        if str_index in dic:
            result[str_index] = dic[str_index]
    return result

def main(pkFinca, fore_sce_dt_prect, merg_sce_colum_prect, merg_sce_probs_prect, perfil='investigador'):
    df = import_data_clim(pkFinca, 179, perfil)
    df = df.head(15)

    escen_prectotcorr = result_scen(merg_sce_colum_prect, fore_sce_dt_prect)

    model, result = two_stage_model(df, merg_sce_colum_prect, merg_sce_probs_prect, escen_prectotcorr)

    return result