from mesa import Agent
from indicators import Indicators
from datetime import datetime
import random
import pandas as pd
from data_dictionaries import DataDictionaries

class HouseAgent(Agent): # Agent pentru o casa individuala care proceseza date si primeste recomandari
    
    def __init__(self, house_id, model, application_rate = 1.0):
        super().__init__(house_id, model)
        self.indicators = Indicators(house_id)
        self.indicators.get_power_estimated()  # Calculeaza productia pentru simulare
        self.application_rate = application_rate  # Probabilitatea de a aplica o recomandare (0 - 1)
        
        # Consum/productie actuala si ajustata
        self.current_consumption = 0
        self.current_production = 0
        self.current_consumption_adjusted = 0
        self.current_production_adjusted = 0
        
        self.current_time = None
        self.received_recommendation = ""
        
        # Istoric pentru tracking
        self.consumption_history = []
        self.production_history = []

        self.time_keys = sorted(
            set(self.indicators.production.keys()) & set(self.indicators.consumption.keys())
        )
        self.current_step = 0

    def step(self): # Actualizare stare casa si procesare date
        
        # Verifica daca mai exista pasi de executat
        if self.current_step >= len(self.time_keys):
            return
        
        t = self.time_keys[self.current_step]
        self.current_time = t

        self.current_production = self.indicators.production.get(t, 0)
        self.current_consumption = self.indicators.consumption.get(t, 0)
        
        # Initial: consumul ajustat = consumul real
        self.current_consumption_adjusted = self.current_consumption
        self.current_production_adjusted = self.current_production

        self.current_step += 1
    
    def receive_recommendation(self, recommendation): # Primeste si stocheaza recomandarea de la agentul central
        self.received_recommendation = recommendation
        # Aplica recomandarea cu o anumita probabilitate
        if random.random() < self.application_rate:
            self.apply_recommendation(recommendation)
        else:
            self.apply_recommendation("BALANCED")  # Nu aplica recomandarea
    
    def apply_recommendation(self, recommendation):
        
        if recommendation == "REDUCE_CONSUMPTION":
            self.current_consumption_adjusted = self.current_consumption * 0.7
            
        elif recommendation == "INCREASE_CONSUMPTION":
            self.current_consumption_adjusted = self.current_consumption * 1.3
            
        else:  # BALANCED
            self.current_consumption_adjusted = self.current_consumption

class PresenceHouseAgent(HouseAgent): # Agent casa care aplica recomandari doar daca detecteaza prezenta reala (bazat pe appliance-uri)

    def __init__(self, house_id, model):
        super().__init__(house_id, model, application_rate = 1.0)
        
        self.min_active_appliances = 2  # Minim 2 appliance-uri active pentru prezenta
        
        # Foloseste cache-ul pentru DataFrame-uri mari
        data_cache = DataDictionaries(verbose=False)
        consumption_df = data_cache.get_consumption_df()
        self.consumption_df = consumption_df[consumption_df['HouseIDREF'] == house_id].copy()
        
        appliance_df = data_cache.get_appliance_df()
        self.house_appliances = appliance_df[appliance_df['HouseIDREF'] == house_id].copy()
        
        # Pre-calculeaza totul in constructor pentru performanta maxima
        self.precalculate_presence_data()
    
    # Pre-calculeaza toate datele necesare pentru detectarea prezentei (consum > 2x minim zilnic)
    # Face toate operatiile o singura data in constructor
    def precalculate_presence_data(self):
        
        # Adauga coloane necesare
        self.consumption_df['Date'] = pd.to_datetime(self.consumption_df['EpochTime'], unit='s').dt.date
        self.consumption_df['HourEpoch'] = self.consumption_df['EpochTime'] - (self.consumption_df['EpochTime'] % 3600)
        
        # Grupeaza pe zi, ora si appliance
        hourly = self.consumption_df.groupby(['Date', 'HourEpoch', 'ApplianceIDREF'])['Value'].sum().reset_index()
        hourly['Value'] = hourly['Value'] / 6000  # Conversie la kWh
        
        # Calculeaza minimul zilnic pentru fiecare appliance
        self.daily_minimums = hourly.groupby(['Date', 'ApplianceIDREF'])['Value'].min().reset_index()
        self.daily_minimums.loc[self.daily_minimums['Value'] < 0.001, 'Value'] = 0.001
        
        # Creeaza dictionar(epoch_time - prezenta) pentru acces instant
        self.presence_cache = {}
        
        # Grupeaza consumul pe ora si appliance
        hourly_grouped = hourly.set_index(['HourEpoch', 'ApplianceIDREF'])['Value'].to_dict()
        
        # Creeaza un dictionar pentru minimuri
        min_dict = {}
        for _, row in self.daily_minimums.iterrows():
            min_dict[(row['Date'], row['ApplianceIDREF'])] = row['Value']
        
        # Pre-calculeaza prezenta pentru fiecare timestamp unic
        unique_times = self.consumption_df['HourEpoch'].unique()
        
        for epoch_time in unique_times:
            current_date = pd.to_datetime(epoch_time, unit='s').date()
            active_appliances = 0
            
            # Verifica fiecare appliance pentru acest timestamp
            for app_id in self.house_appliances['ID'].unique():
                consumption = hourly_grouped.get((epoch_time, app_id), 0)
                daily_min = min_dict.get((current_date, app_id), 0.001)
                
                # Daca consumul > 2x minimul => appliance activ
                if consumption > 2 * daily_min:
                    active_appliances += 1
            
            self.presence_cache[epoch_time] = (active_appliances >= self.min_active_appliances)
    
    def check_real_presence(self, epoch_time): # Verifica daca exista prezenta reala instant din cache
        return self.presence_cache.get(epoch_time, False)
    
    def receive_recommendation(self, recommendation): # Primeste recomandare si o aplica doar daca exista prezenta reala
        self.received_recommendation = recommendation
        # Verifica prezenta reala
        is_present = self.check_real_presence(self.current_time)
        if is_present:
            self.apply_recommendation(recommendation)
        else:
            self.apply_recommendation("BALANCED")