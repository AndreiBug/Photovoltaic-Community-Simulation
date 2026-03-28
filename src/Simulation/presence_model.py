from energy_processing import EnergyProcessing
from datetime import datetime
import pandas as pd
import numpy as np
from data_dictionaries import DataDictionaries

# Model de prezenta al casei bazat pe consumul energetic
class PresenceModel(EnergyProcessing):
    def __init__(self, house_id):
        super().__init__(house_id)
        self.presence_data = {}  # Dictionar cu timestamp si prezenta (True/False)
        self.consumption_threshold = 0.0  # Prag minim de consum pentru prezenta
    
    def evaluate_presence_for_date(self, date_str, percentile = 40, verbose = True): # Evalueaza prezenta in casa pentru o zi specifica (perceptia managerului)
        if not self.consumption:
            print("Nu exista date de consum pentru casa", self.house_id)
            return {}
        
        target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        
        target_epoch_start = int(target_date.timestamp()) # 00:00 ziua respectiva
        target_epoch_end = target_epoch_start + 24 * 60 * 60  # 00:00 ziua urmatoare
        
        # Filtreaza consumul pentru ziua respectiva
        daily_consumption = {}
        for epoch_time, consumption_value in self.consumption.items():
            if target_epoch_start <= epoch_time < target_epoch_end:
                daily_consumption[epoch_time] = consumption_value
        
        if not daily_consumption:
            print("Nu exista date de consum pentru data", date_str)
            return {}
        
        # Converteste la array pentru calcule statistice
        consumption_values = np.array(list(daily_consumption.values()))
        sorted_times = sorted(daily_consumption.keys())
        total_daily_consumption = sum(daily_consumption.values())
        
        # Calcul statistici pentru afisare
        average_hourly_consumption = consumption_values.mean()
        median_consumption = np.percentile(consumption_values, 50)
        q1_consumption = np.percentile(consumption_values, 25)
        q3_consumption = np.percentile(consumption_values, 75)
        
        # Prag de prezenta = percentile ales din distributia zilnica
        self.consumption_threshold = np.percentile(consumption_values, percentile)
        
        if verbose:
            first_timestamp = min(daily_consumption.keys())
            last_timestamp = max(daily_consumption.keys())
            first_time_str = datetime.fromtimestamp(first_timestamp).strftime('%H:%M:%S')
            last_time_str = datetime.fromtimestamp(last_timestamp).strftime('%H:%M:%S')
            
            print(f"\nPERCEPTIA MANAGERULUI - Casa {self.house_id} - {date_str}")
            print(f"Interval: {first_time_str} - {last_time_str}")
            print(f"Consum total zilnic: {round(total_daily_consumption, 3)} kWh")
            print(f"Media: {round(average_hourly_consumption, 3)} kWh | Q1: {round(q1_consumption, 3)} | Median: {round(median_consumption, 3)} | Q3: {round(q3_consumption, 3)} kWh")
            print(f"Prag prezenta (percentila {percentile}): {round(self.consumption_threshold, 3)} kWh")
            print(f"\nOra, Timestamp, Consum (kWh), Depaseste Prag?, Prezenta")

        presence_results = {}
        
        for epoch_time in sorted_times:
            consumption_value = daily_consumption[epoch_time]
            
            # Manager percepe prezenta doar daca consumul > percentile ales
            is_present = consumption_value > self.consumption_threshold
            presence_results[epoch_time] = is_present
            
            if verbose:
                hour = datetime.fromtimestamp(epoch_time).strftime('%H:%M')
                presence_str = "PREZENT" if is_present else "ABSENT"
                threshold_diff = consumption_value - self.consumption_threshold
                threshold_str = f"+{round(threshold_diff, 3)}" if threshold_diff > 0 else f"{round(threshold_diff, 3)}"
                
                print(f"{hour}, {epoch_time}, {round(consumption_value, 3)}, {threshold_str}, {presence_str}")
        
        total_hours = len(presence_results)
        hours_present = sum(1 for p in presence_results.values() if p)
        hours_absent = total_hours - hours_present
        presence_percentage = (hours_present / total_hours * 100) if total_hours > 0 else 0
        
        if verbose:
            print(f"\nSTATISTICI: {total_hours} ore analizate | {hours_present} prezent ({round(presence_percentage, 1)}%) | {hours_absent} absent ({round(100 - presence_percentage, 1)}%)\n")
        
        self.presence_data = presence_results
        return presence_results
    
    def is_someone_home(self, epoch_time): # Verifica daca este cineva acasa la un timestamp specific.
        return self.presence_data[epoch_time]
    
    def evaluate_real_presence_for_date(self, date_str, min_active_appliances=2, verbose=True):
        
        # Pentru fiecare appliance, calculez minimul consumului din ziua respectiva
        # Daca minim = 0, folosesc 0.001 pentru a permite comparatia
        # La fiecare timestamp, daca consum_appliance > 2 * minim_zilei => appliance activ
        # Daca >= min_active_appliances (default 2) appliance-uri sunt active => prezenta

        # Foloseste cache-ul in loc sa citeasca CSV-urile
        data_cache = DataDictionaries(verbose=False)
        df_consumption = data_cache.get_consumption_df()
        df_appliances = data_cache.get_appliance_df()
        
        # Filtreaza pentru casa curenta
        df_consumption = df_consumption[df_consumption['HouseIDREF'] == self.house_id]
        house_appliances = df_appliances[df_appliances['HouseIDREF'] == self.house_id]
        
        if df_consumption.empty or house_appliances.empty:
            print(f"Nu exista date pentru casa {self.house_id}")
            return {}
        
        # Determina intervalul zilei
        target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(hour = 0, minute = 0, second = 0, microsecond = 0)
        target_epoch_start = int(target_date.timestamp())
        target_epoch_end = target_epoch_start + 24 * 60 * 60
        
        # Filtreaza pentru ziua respectiva
        df_daily = df_consumption[
            (df_consumption['EpochTime'] >= target_epoch_start) & 
            (df_consumption['EpochTime'] < target_epoch_end)
        ].copy()
        
        if df_daily.empty:
            print(f"Nu exista date pentru data {date_str}")
            return {}
        
        # Rotunjeste la inceputul orei
        df_daily['HourEpoch'] = df_daily['EpochTime'] - (df_daily['EpochTime'] % 3600)
        
        # Grupeaza pe ora si appliance
        df_hourly = df_daily.groupby(['HourEpoch', 'ApplianceIDREF'])['Value'].sum().reset_index()
        df_hourly['Value'] = df_hourly['Value'] / 6000  # Conversie la kWh
        
        # Calculeaza minimul pentru fiecare appliance pentru ziua respectiva
        appliance_daily_min = df_hourly.groupby('ApplianceIDREF')['Value'].min().to_dict()
        
        # Inlocuieste 0 cu 0.001 pentru a permite x2
        for app_id in appliance_daily_min:
            appliance_daily_min[app_id] = max(appliance_daily_min[app_id], 0.001)
        
        # Obtine toate timestamp-urile unice, sortate
        sorted_times = sorted(df_hourly['HourEpoch'].unique())
        
        presence_results = {}
        
        appliance_names = {}
        for _, row in house_appliances.iterrows():
            app_id = row['ID']
            if app_id in appliance_daily_min:
                appliance_names[app_id] = row['Name']
        
        if verbose:
            print(f"\nMODEL PREZENTA REAL - Casa {self.house_id} - {date_str}")
            print(f"Criterii: Minim {min_active_appliances} appliance-uri cu consum > 2x minimul zilei")
            print(f"Appliance-uri monitorizate: {len(appliance_names)}")
            print("\nOra, Active Appliances, Prezenta")
        
        # Pentru fiecare timestamp
        for epoch_time in sorted_times:
            # Obtine consumul pentru fiecare appliance la acest timestamp
            hour_data = df_hourly[df_hourly['HourEpoch'] == epoch_time]
            
            active_appliances = 0
            active_list = []
            
            # Verifica fiecare appliance
            for _, row in hour_data.iterrows():
                app_id = row['ApplianceIDREF']
                consumption = row['Value']
                daily_min = appliance_daily_min.get(app_id, 0.001)
                
                # Daca consumul > 2x minimul => appliance activ
                if consumption > 2 * daily_min:
                    active_appliances += 1
                    if app_id in appliance_names:
                        active_list.append(f"{appliance_names[app_id]}({consumption:.3f})")
            
            # Prezenta daca >= min_active_appliances sunt active
            is_present = active_appliances >= min_active_appliances
            presence_results[epoch_time] = is_present
            
            if verbose:
                hour = datetime.fromtimestamp(epoch_time).strftime('%H:%M')
                presence_str = "DA" if is_present else "NU"
                active_str = f"{active_appliances} active"
                
                if active_list and is_present:
                    print(f"{hour}, {active_str} ({', '.join(active_list[:3])}{'...' if len(active_list) > 3 else ''}), {presence_str}")
                else:
                    print(f"{hour}, {active_str}, {presence_str}")
        
        total_hours = len(presence_results)
        hours_present = sum(1 for p in presence_results.values() if p)
        hours_absent = total_hours - hours_present
        presence_percentage = (hours_present / total_hours * 100) if total_hours > 0 else 0
        
        if verbose:
            print(f"\nSTATISTICI: {total_hours} ore analizate | {hours_present} prezent ({presence_percentage:.1f}%) | {hours_absent} absent ({100 - presence_percentage:.1f}%)\n")
        
        return presence_results

