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
        self.presence_accuracy = 0.0  # Acuratete perceptie vs prezenta reala (%)
    
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

    def calculate_presence_accuracy_from_data(self, manager_presence, real_presence, verbose=True):
        common_timestamps = sorted(set(manager_presence.keys()) & set(real_presence.keys()))
        if not common_timestamps:
            self.presence_accuracy = 0.0
            return {
                "accuracy_pct": 0.0,
                "total_points": 0,
                "agreements": 0,
                "true_positive": 0,
                "true_negative": 0,
                "false_positive": 0,
                "false_negative": 0,
                "manager_presence_hours": 0,
                "real_presence_hours": 0,
            }

        tp = tn = fp = fn = 0
        for t in common_timestamps:
            predicted = manager_presence[t]
            actual = real_presence[t]

            if predicted and actual:
                tp += 1
            elif (not predicted) and (not actual):
                tn += 1
            elif predicted and (not actual):
                fp += 1
            else:
                fn += 1

        agreements = tp + tn
        total = len(common_timestamps)
        accuracy_pct = (agreements / total) * 100

        manager_hours = sum(1 for t in common_timestamps if manager_presence[t])
        real_hours = sum(1 for t in common_timestamps if real_presence[t])

        self.presence_accuracy = accuracy_pct

        if verbose:
            print(f"Acuratete perceptie vs real: {accuracy_pct:.2f}% ({agreements}/{total})")
            print(f"TP: {tp} | TN: {tn} | FP: {fp} | FN: {fn}")
            print(f"Ore percepute prezente: {manager_hours} | Ore prezenta reala: {real_hours}")

        return {
            "accuracy_pct": accuracy_pct,
            "total_points": total,
            "agreements": agreements,
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "manager_presence_hours": manager_hours,
            "real_presence_hours": real_hours,
        }

    def calculate_presence_accuracy_for_date(self, date_str, percentile=40, min_active_appliances=2, verbose=True):
        manager_presence = self.evaluate_presence_for_date(date_str, percentile=percentile, verbose=False)
        real_presence = self.evaluate_real_presence_for_date(date_str, min_active_appliances=min_active_appliances, verbose=False)

        accuracy_stats = self.calculate_presence_accuracy_from_data(manager_presence, real_presence, verbose=False)
        if accuracy_stats["total_points"] == 0:
            if verbose:
                print(f"Nu exista timestamp-uri comune pentru calculul acuratetii prezentei la data {date_str}.")
            return accuracy_stats

        if verbose:
            print(f"\nACURATETE PREZENTA - Casa {self.house_id} - {date_str}")
            self.calculate_presence_accuracy_from_data(manager_presence, real_presence, verbose=True)

        return accuracy_stats

    def _calculate_for_house(self, house_model, percentile, min_active_appliances):
        all_dates = sorted({
            datetime.fromtimestamp(t).strftime("%Y-%m-%d")
            for t in house_model.consumption.keys()
        })

        tp = tn = fp = fn = 0
        total_points = agreements = days = 0

        for date_str in all_dates:
            daily_stats = house_model.calculate_presence_accuracy_for_date(
                date_str,
                percentile=percentile,
                min_active_appliances=min_active_appliances,
                verbose=False,
            )
            if daily_stats["total_points"] == 0:
                continue
            days += 1
            total_points += daily_stats["total_points"]
            agreements += daily_stats["agreements"]
            tp += daily_stats["true_positive"]
            tn += daily_stats["true_negative"]
            fp += daily_stats["false_positive"]
            fn += daily_stats["false_negative"]

        return {
            "total_points": total_points,
            "agreements": agreements,
            "days_analyzed": days,
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
        }

    def calculate_presence_accuracy_for_all_data(self, percentile=40, min_active_appliances=2, verbose=True):
        data_cache = DataDictionaries(verbose=False)
        all_house_ids = sorted(data_cache.get_all_houses().keys())

        global_tp = global_tn = global_fp = global_fn = 0
        global_total = global_agreements = global_days = 0
        houses_analyzed = 0

        for house_id in all_house_ids:
            house_model = PresenceModel(house_id)

            if not house_model.consumption:
                if verbose:
                    print(f"\nCasa {house_id}: Nu exista date de consum.")
                continue

            stats = self._calculate_for_house(house_model, percentile, min_active_appliances)

            if stats["total_points"] == 0:
                continue

            houses_analyzed += 1
            house_accuracy = (stats["agreements"] / stats["total_points"]) * 100

            global_tp += stats["true_positive"]
            global_tn += stats["true_negative"]
            global_fp += stats["false_positive"]
            global_fn += stats["false_negative"]
            global_total += stats["total_points"]
            global_agreements += stats["agreements"]
            global_days += stats["days_analyzed"]

            if verbose:
                loc = data_cache.get_house(house_id).get("location", "?")
                print(f"\n--- Casa {house_id} ({loc}) ---")
                print(f"  Acuratete: {house_accuracy:.2f}% ({stats['agreements']}/{stats['total_points']})")
                print(f"  TP: {stats['true_positive']} | TN: {stats['true_negative']} | FP: {stats['false_positive']} | FN: {stats['false_negative']}")
                print(f"  Zile analizate: {stats['days_analyzed']}")

        global_accuracy = (global_agreements / global_total) * 100 if global_total > 0 else 0.0
        self.presence_accuracy = global_accuracy

        if verbose:
            print(f"\n{'=' * 60}")
            print(f"ACURATETE GLOBALA - TOATE CASELE ({houses_analyzed} case)")
            print(f"{'=' * 60}")
            print(f"Acuratete globala:                               {global_accuracy:.2f}% ({global_agreements}/{global_total})")
            print(f"True Positive  (ore prezente corect detectate):  {global_tp}")
            print(f"True Negative  (ore absente corect detectate):   {global_tn}")
            print(f"False Positive (ore goale marcate ca ocupate):   {global_fp}")
            print(f"False Negative (ore ocupate ratate):             {global_fn}")
            print(f"Zile analizate:                                  {global_days}")

        return {
            "accuracy_pct": global_accuracy,
            "total_points": global_total,
            "agreements": global_agreements,
            "days_analyzed": global_days,
            "houses_analyzed": houses_analyzed,
            "true_positive": global_tp,
            "true_negative": global_tn,
            "false_positive": global_fp,
            "false_negative": global_fn,
        }

