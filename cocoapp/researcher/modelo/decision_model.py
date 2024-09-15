
import numpy as np
import pandas as pd
import math
from pulp import LpVariable, lpSum, LpProblem, LpMaximize, PULP_CBC_CMD


def fTemp(Tbase, Topt, T):
    ftemp = np.zeros(len(T))  # Initialize an array of zeros with the same length as T

    # Calculate FTemp values based on temperature conditions

    # Set FTemp to 0 for temperatures below Tbase
    ftemp[T < Tbase] = 0

    # Set FTemp to the relative value between Tbase and Topt for temperatures within that range
    ftemp[(T >= Tbase) & (T <= Topt)] = (T[(T >= Tbase) & (T <= Topt)] - Tbase) / (Topt - Tbase)

    # Set FTemp to 1 for temperatures above Topt
    ftemp[T > Topt] = 1

    return pd.DataFrame(ftemp, columns=['FTemp'])  # Return ftemp as a DataFrame with a single column 'FTemp'

def fHeat(Theat, Textreme, Tmax):
    fheat = np.ones(len(Tmax))  # Initialize an array of ones with the same length as Tmax

    # Calculate FHeat values based on temperature conditions

    # Set FHeat to 1 for temperatures less than or equal to Theat
    fheat[Tmax <= Theat] = 1

    # Set FHeat to the relative value between Theat and Textreme for temperatures within that range
    fheat[(Tmax > Theat) & (Tmax <= Textreme)] = 1 - np.round((Tmax[(Tmax > Theat) & (Tmax <= Textreme)] - Theat) / (Textreme - Theat), 3)

    # Set FHeat to 0 for temperatures greater than Textreme
    fheat[Tmax > Textreme] = 0

    return pd.DataFrame(fheat, columns=['FHeat'])  # Return fheat as a DataFrame with a single column 'FHeat'

def fSolar(fsolar, i50a, i50b, tsum, tbase, temp):
    temp = [(abs(i - tbase) + (i - tbase)) / 2 for i in temp]  # Calculate the temperature values based on tbase
    tt = []  # Initialize an empty list to store cumulative temperature values
    for i in range(len(temp)):
        if i == 0:
            tt.append(0.0)  # Append 0.0 for the first temperature value
        else:
            tt.append(temp[i] + tt[i-1])  # Calculate and append cumulative temperature values

    growth = [fsolar / (1 + math.exp(-0.01 * (i - i50a))) for i in tt]  # Calculate growth values
    senescence = [fsolar / (1 + math.exp(0.01 * (i - (tsum - i50b)))) for i in tt]  # Calculate senescence values

    result = [growth[i] if senescence[i] >= growth[i] else senescence[i] for i in range(len(senescence))]  # Determine final result based on growth and senescence values

    return pd.DataFrame(result, columns=['FSolar'])  # Return result as a DataFrame with a single column 'FSolar'

def RN(alfa,RS,RSO,SIGMA,TMIN,TMAX,RHMEAN,temp,Altitude,n,E,Cp,G,WS2M):
    eTMAX = [0.6108*math.exp((17.27*TMAX[i])/(TMAX[i]+237.3)) for i in range(len(TMAX))] #O
    eTMIN = [0.6108*math.exp((17.27*TMIN[i])/(TMIN[i]+237.3)) for i in range(len(TMIN))] #N
    ea = [(RHMEAN[i]/100)*((eTMAX[i]+eTMIN[i])/2) for i in range(len(RHMEAN))] #M
    TMAXK = [TMAX[i]+273.16 for i in range(len(TMAX))] #L
    TMINK = [TMIN[i]+273.16 for i in range(len(TMIN))] #J
    RNS = [(1-alfa)*RS[i] for i in range(len(RS))] #D
    RNL =[SIGMA*((TMINK[i]**4+TMAXK[i]**4)/2)*(0.34-0.14*(ea[i]**0.5))*(1.35*(RS[i]/RSO[i])-0.35) for i in range(len(TMIN))] #C
    RN = [RNS[i]-RNL[i] for i in range(len(TMIN))] #A
    A = [4098*(0.6108*math.exp(17.27*temp[i]/(temp[i]+237.3)))/(temp[i]+237.3)**2 for i in range(len(temp))] #ETO R
    es = [(eTMAX[i]+eTMIN[i])/2 for i in range(len(TMIN))] #Eto P
    es_ea = [es[i]-ea[i] for i in range(len(temp))] #Eto M
    P = 101.3*((293-0.0065*Altitude)/293)**5.26 #Eto H
    y = ((Cp*P)/(n*E)) # Eto F
    ETO = [(0.408*A[i]*(RN[i]- G)+y*(900/(temp[i]+273))*WS2M[i]*(es_ea[i]))/(A[i]+y*(1+0.34*WS2M[i]))for i in range(len(temp))] #eto B
    KS = [1]*(int(len(ETO)*5/18))+[1.05]*(int(len(ETO)*13/18)) #La igualo a longitud de ETO pero en el Excel aparece con longitud de 130 debo arreglarlo para múltiples periodos
    ETC = [KS[i]*ETO[i] for i in range(len(ETO))]
    return ETO, ETC

def fWater(Swater, TAW,RAW,p, alfa, SIGMA, Precipitation,RS,RSO,TMIN,TMAX,RHMEAN,temp,Altitude,n,E,Cp,G,WS2M,la,S):
    ETO , ETC = RN(alfa,RS,RSO,SIGMA,TMIN,TMAX,RHMEAN,temp,Altitude,n,E,Cp,G,WS2M)
    #Water gain
    # Irrigation
    Irrigation = [0]*len(Precipitation)
    # Capillary Rise
    CapillaryRise = [0]*len(Precipitation)
    #Water gain
    WaterGain = [Precipitation[i] + Irrigation[i] +CapillaryRise[i] for i in range(len(Precipitation))]

    #Water Loss
    #Evaporated
    # Evaporated = [ ETO[i]*0.2 if Precipitation[i]> 0 and Precipitation[i]>= ETO[i]*0.2 else Precipitation[i] for i in range(len(Precipitation))]
    Evaporated = [ ETO[i]*0.2 if  Precipitation[i]>= ETO[i]*0.2 else Precipitation[i] for i in range(len(Precipitation))] #Simplyfied
    #Drain
    Drain = [((Precipitation[i]-la)**2)/(Precipitation[i]-la+S) if (Precipitation[i]>la) else 0 for i in range(len(Precipitation))]

    #Water Loss
    WaterLoss_DP = [ETC[i]+Drain[i]+Evaporated[i] for i in range(len(Precipitation))]
    #Depletion size
    Depletion = [0.0]*len(Precipitation)
    #Depletion lagged 1 step
    Depletion_lag = Depletion

    #Depletion
    for i in range(len(Depletion)):
        #print
        if i==0:
            Depletion[i] = 0.0
            Depletion_lag[i] = 0.0

        else:
            Depletion_lag[i] = Depletion[i-1]
            if WaterLoss_DP[i]-WaterGain[i]+Depletion_lag[i]>0:
                if WaterLoss_DP[i]-WaterGain[i]+Depletion_lag[i]>TAW:
                    Depletion[i] = TAW
                    # Depletion_lag[i] = Depletion[i-1]
                else:
                    Depletion[i] = WaterLoss_DP[i]-WaterGain[i]+Depletion_lag[i]
                    # Depletion_lag[i] = Depletion[i-1]
            else:
                Depletion[i] = 0


    #Paw
    PAW=[TAW-Depletion[i] if TAW > Depletion[i] else 0 for i in range(len(Depletion))]
    #Arid
    ARID = [1-min(ETO[i],0.096*PAW[i])/ETO[i] for i in range(len(PAW))]

    FWater = [1-Swater*ARID[i] for i in range(len(ARID))]

    return pd.DataFrame({'FWater': FWater, 'Depletion': Depletion})


def main_model_deterministic(altitude, df):
    df_RS = pd.to_numeric(df['allsky_sfc_sw_dwn']) #df['RS']
    df_RSO = pd.to_numeric(df['clrsky_sfc_sw_dwn']) #df['RSO']
    df_T2M = pd.to_numeric(df['t2mdew']) #df['T2M']
    df_T2M_MAX = pd.to_numeric(df['t2m_max']) #df['T2M_MAX']
    df_T2M_MIN = pd.to_numeric(df['t2m_min']) #df['T2M_MIN']
    df_WS2M = pd.to_numeric(df['ws2m']) #df['WS2M']
    df_PRECIPITATION = pd.to_numeric(df['prectotcorr']) #df['PRECIPITATION']
    df_RH2M = pd.to_numeric(df['rh2m']) #df['RH2M']

    # Initialize an empty DataFrame to store results
    results_df = pd.DataFrame(columns=['Time', 'ETC','Irrigation', 'Draining','Depletion', 'PAW', 'f_water', 'Heat_Stress_Surplus', 'Heat_Stress_Slack', 'Water_Excess', 'Water_Optimal', 'Objective_Value'])

    # Fixed parameters
    ##########################################################################################
    # Environmental Constants
    alfa = 0.23  # Albedo, unitless (fraction of solar radiation reflected)
    SIGMA = 0.000000004903  # Stefan-Boltzmann constant (W/m²K⁴)
    Altitude = 658  # Elevation above sea level (m)
    n = 2.45  # Number of air molecules per mole of moist air (mol/mol)
    E = 0.622  # Latent heat of vaporization (J/kg)
    Cp = 1.013 / 1000  # Specific heat of air at constant pressure (J/kg·K)
    G = 0  # Soil heat flux (W/m²)

    # Temperature Constants
    Tbase = 10  # Baseline temperature for growth (°C)
    Topt = 24  # Optimal temperature for growth (°C)
    Theat = 32  # Critical high temperature (°C)
    Textreme = 38  # Extreme temperature threshold (°C)
    I50A = 680  # Cumulative temperature for phase A (°C day)
    I50B = 200  # Cumulative temperature for phase B (°C day)
    Tsum = 2764  # Optimal quantity of cumulative temperature required for harvest (°C day)
    fSolarmax = 0.94  # Temperature threshold value, unitless

    # Water Constants
    Swater = 0.6053  # Sensitivity of Radiation Use Efficiency to drought, unitless
    critical_depletion = 94.08  # Critical depletion level in the root zone (mm)
    critical_water = 140  # Maximum water level in the root zone (mm)
    S = 25400 / 77 - 254  # Potential maximum water retention (mm/day)
    la = 0.2 * (S - 254)  # Initial depletion (mm/day)
    p = 0.3  # Proportion of rain reaching surface, unitless

    # Crop-Specific Constants
    CRUE = 0.296  # Radiation Use Efficiency (g/m²)
    CHI = 0.0706  # Cocoa harvest index, unitless
    SCO2 = 6.7249  # CO2 function value, unitless
    CCh = CRUE * CHI  # Product of Radiation Use Efficiency and Harvest Index

    # Temporal Constants
    T = 180  # Days from flowering to harvest

    # # Constant parameters
    # CRUE = 0.296 # Radiation Use Efficiency g/m2
    # CHI = 0.0706 # Cocoa harvest index
    # fSolarmax = 0.94 # Temperature Threshold Value (adimensional)
    # I50A = 680 # Cumulative temperature C day
    # I50B = 200 # Cumulative temperature C day
    # Tsum = 2764 # Optimal quantity of cumulative temperature required to harvest  C
    # Tbase = 10 # Baseline temperature C
    # Topt = 24 # Optimal temperature C
    # Theat = 32 # Critical temperature C
    # Textreme = 38 # Extreme temperature C
    # Swater = 0.6053# 0.790164697774427 #0.6053 #0.790164697774427
    # criticaldepletion =  94.08 # Minimum water value in the root zone mm
    # criticalwater = 140 #Maximum water value in the root zone mm
    # SCO2 = 6.7249 # CO2 Funcion value dimensionless
    # alfa = 0.23 # (unitless): Albedo, fraction of solar radiation reflected by the surface
    # SIGMA = 0.000000004903 #  (W/m²K⁴): Stefan-Boltzmann constant, used in the calculation of longwave radiation.
    # Altitude = 658 # Altitude meters over seal level
    # n = 2.45 #(mol/mol): Number of molecules of air per mole of moist air.
    # E = 0.622 # (J/kg): Latent heat of vaporization.
    # Cp = 1.013/1000 #  (J/kg·K): Specific heat of air at constant pressure.
    # G = 0 # (W/m²): Soil heat flux.
    # #Inital Depletion
    # la= 0.2*(25400/77-254)
    # S=25400/77-254 # The potential maximum water retention (mm/day)
    # p = 0.3 # Proportion of rain reaching surface dimensionless
    # T = 180 # Number of days from flowering to harvesting
    # Constant parameters known for all time periods
    CCh = CRUE * CHI  # Calculated from CRUE * CHI
    Swater = Swater  # Sensitivity of RUE to drought
    critical_depletion = critical_depletion  # Critical depletion level
    critical_water = critical_water  # Critical water level
    ##########################################################################################
    # Environmental parameters

    # Apply the functions to calculate the environmental stress factors
    df['FTemp'] = fTemp(Tbase, Topt, df_T2M).values
    df['FHeat'] = fHeat(Theat, Textreme, df_T2M_MAX).values
    df['FSolar'] = fSolar(fSolarmax, I50A, I50B, Tsum, Tbase, df_T2M).values
    # Calculate Environmental Factors effects
    df['EF_t'] = df_RS*df['FSolar']*SCO2*df['FTemp']
    # Calculate ETO and ETC
    ETO, ETC = RN(alfa, df_RS, df_RSO, SIGMA, df_T2M_MIN, df_T2M_MAX, df_RH2M, (df_T2M_MIN+df_T2M_MAX)/2, Altitude, n, E, Cp, G, df_WS2M)

    # Evaporated Water
    # Evaporated = [ ETO[i]*0.2 if  df_PRECIPITATION[i]>= ETO[i]*0.2 else df_PRECIPITATION[i] for i in range(len(df_PRECIPITATION))] #Simplyfied
    Evaporated = [(h * 0.2 if p > 0 and p >= h * 0.2 else p) for p, h in zip(df_PRECIPITATION, ETO)]


        #  fWater(Swater, TAW,RAW,p, alfa, SIGMA, Precipitation,RS,RSO,TMIN,TMAX,RHMEAN,temp,Altitude,n,E,Cp,G,WS2M,la,S):
    DR = fWater(Swater, critical_water, critical_depletion,p, alfa, SIGMA, df_PRECIPITATION, df_RS, df_RSO, df_T2M_MIN, df_T2M_MAX, df_RH2M,(df_T2M_MIN + df_T2M_MAX)/2, Altitude, n, E, Cp, G, df_WS2M,la,S)['Depletion']

    ETC = {t+1: value for t, value in enumerate(ETC)}
    P_t = {t: df_PRECIPITATION[t-1] for t in range(1, T+1)}  # Precipitation on day t
    ##########################################################################################
    # Parameters set to zero
    CR_t = {t: 0 for t in range(1, T+1)} # Capillary rise on day t
    DP_t = {t: 0 for t in range(1, T+1)} # Deep Percolation on day t

    # Time horizon
    T = 180
    ##########################################################################################
    # Set variables in t=0
    # Convert the initial Python numerical values into LpAffineExpression
    W_0 = LpVariable('W_0', lowBound=critical_depletion, upBound=critical_water, cat='Continuous')
    DR_0 = LpVariable('DR_0', lowBound=0, cat='Continuous')
    # Update the W_0 and DR_0 with the known initial values outside of the loop
    W_0.setInitialValue(140)  # Assuming an initial value of 140
    DR_0.setInitialValue(0)  # Assuming an initial value of 0


    # Decision variables and parameters specific to each time period
    I = {}  # Irrigation
    D = {}  # Draining
    DR = {} # Depletion in root zone
    f_water = {}  # Sensitivity to drought stress
    x_minus = {}  # Surplus of heat stress
    x_plus = {}  # Slack of heat stress
    y_minus = {}  # Surplus of water exceeding minimum level
    y_plus = {}  # Slack of water between ET and available water
    W = {}  # Plant Available Water

    for t in range(1,181):
        # Objective function
        model = LpProblem(f"Maximize_Biomass_at_t_{t}", LpMaximize)
        # Decision Variables at t time
        I[t] = LpVariable(f'Irrigation_{t}', lowBound=0, cat='Continuous')
        D[t] = LpVariable(f'Draining_{t}', lowBound=0, cat='Continuous')
        # DR[t] = pulp.LpVariable(f'Depletion_{t}', lowBound=0,upBound=1, cat='Continuous')
        DR[t] = LpVariable(f'Depletion_{t}', lowBound=0, cat='Continuous')
        f_water[t] = LpVariable(f"f_water_{t}", lowBound=0, upBound=1, cat='Continuous')
        x_minus[t] = LpVariable(f"x_minus_{t}", lowBound=0, cat='Continuous')
        x_plus[t] = LpVariable(f"x_plus_{t}", lowBound=0, cat='Continuous')
        y_minus[t] = LpVariable(f"y_minus_{t}", lowBound=0, cat='Continuous')
        y_plus[t] = LpVariable(f"y_plus_{t}", lowBound=0, cat='Continuous')
        # Ensure W[t] is correctly defined for each t
        W[t] = LpVariable(f"W_{t}", lowBound=critical_depletion, upBound=critical_water, cat='Continuous')

        # Evaluate the Objective Function
        model += CCh * (df['EF_t'][t-1] * f_water[t] - df['EF_t'][t-1] * x_minus[t]), "Objective_t_%d" % t

        # Constraints
        model += f_water[t] - x_minus[t] + x_plus[t] == df['FHeat'][t-1], "Heat_Stress_t_%d" % t
        model += 0.096 * W[t] - y_minus[t] + y_plus[t] ==  ETC[t], "Sensitive_Drought_Stress_t_%d" % t
        model += f_water[t] - 0.096 * Swater / ETC[t] * W[t] + Swater / ETC[t] * y_minus[t] == 1 - Swater, "Drought_Stress_t_%d" % t
        model += critical_water-DR[t] == W[t], f"PAW_t{t}" #New constraint
        if t == 1:
            D[t].bounds(0, None)
            #model += DR[t] == ETC[t] + D[t] + Evaporated[t]- P_t[t] - I[t] -CR_t[t]+ DR_0, "Depletion_Calculation"
            #model +=  (ETC[t]+ D[t]+Evaporated[t])-(P_t[t]+I[t])+DR_0 == DR[t], f"Depletion_Calculation_t_{t}"
            model += (ETC[t] + D[t] + Evaporated[t-1]+DP_t[t]) - (P_t[t] + I[t] + CR_t[t] + DR_0) == DR[t], f"Depletion_Calculation_t_{t}"
            model += W_0 + P_t[t] + I[t] + CR_t[t] - (D[t] + DR_0 + ETC[t]+DP_t[t]) == W[t], f"Water_Balance_Init_t_{t}"
            # model += W_0 + P_t[t] + I[t] + CR_t[t] - D[t] - DR_0 - ETC[t] == W[t], f"Water_Balance_Init_t_{t}"
        else:
            # model += ETC[t] + D[t] + Evaporated[t]- P_t[t] - I[t] -CR_t[t] + DR[t-1]  == DR[t], f"Depletion_Calculation_t_{t}"
            model += (ETC[t] + D[t] + Evaporated[t-1]+DP_t[t]) - (P_t[t] + I[t] + CR_t[t] +  DR[t-1]) == DR[t], f"Depletion_Calculation_t_{t}"
            model += (W[t-1] + P_t[t] + I[t] + CR_t[t]) -( D[t] + DR[t-1] + ETC[t]+DP_t[t])  == W[t], f"Water_Balance_t_{t}"

        solver = PULP_CBC_CMD(msg=0)
        solution_status = model.solve(solver)
        
        #print(f"Water Gain {P_t[t]+I[t].varValue}, Water Loss {ETC[t]+ D[t].varValue+Evaporated[t-1]}, Depletion is {DR[t].varValue}")
        #print(f"For t = {t}:  Precipitation {P_t[t]} + Irrigation {I[t].varValue}, minus ETC {ETC[t]} - Draining {D[t].varValue+Evaporated[t-1]}, - Depletion {DR[t].varValue} is PAW {W[t].varValue}")
        if model.status == 1:  # Assuming 1 represents a successful solve

            objective_value = model.objective.value()
            if objective_value is None:
                objective_value = 0

            results_row = {'Time': t,
                            'ETC': ETC[t],
                            'Irrigation': I[t].varValue,
                            'Draining': D[t].varValue,
                            'Depletion':DR[t].varValue,
                            'PAW': W[t].varValue,
                            'f_water': f_water[t].varValue,
                            'Heat_Stress_Surplus': x_minus[t].varValue,
                            'Heat_Stress_Slack': x_plus[t].varValue,
                            'Water_Excess': y_minus[t].varValue,
                            'Water_Optimal': y_plus[t].varValue,
                            'Objective_Value': objective_value}
            
            new_df = pd.DataFrame([results_row])  # Create a DataFrame from the row
            results_df = pd.concat([results_df, new_df], ignore_index=True)

    return results_df
