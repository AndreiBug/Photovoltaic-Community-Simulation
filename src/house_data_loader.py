import pandas as pd
from data_dictionaries import DataDictionaries

class HouseDataLoader:
    # Clasa care incarca toate datele necesare pentru o casa intr-un singur pas.
    # Foloseste DataDictionaries pentru datele casei si incarca datele de consum si meteo.
    
    def __init__(self, house_id):
        self.house_id = house_id
        
        # Incarca dictionarele globale (Singleton - se face o singura data)
        self.data_dict = DataDictionaries()
        
        # Verifica ca casa exista
        house_info = self.data_dict.get_house(house_id)
        if not house_info:
            raise ValueError(f"Casa cu ID {house_id} nu exista in baza de date.")
        
        # Stocheaza metadatele casei
        self.zipcode = house_info['zipcode']
        self.location = house_info['location']
        self.weather_station_id = house_info['weather_station_id']
        self.start_epoch = house_info['start_epoch']
        self.end_epoch = house_info['end_epoch']
        
        # Stocheaza aparatele casei
        self.appliances = self.data_dict.get_appliances_for_house(house_id)
        
        # Stocheaza informatii despre statia meteo
        self.weather_station = self.data_dict.get_weather_station(self.weather_station_id)
        
        # Incarca datele de consum si meteo (doar pentru casa curenta)
        self.consumption_data = {}  # {epoch: value_kWh}
        self.solar_radiation_data = {}  # {epoch: value_W/m2}
        
        self.load_consumption_data()
        self.load_solar_radiation_data()
    
    def load_consumption_data(self): # Incarca datele de consum pentru casa curenta din cache
        self.consumption_data = self.data_dict.get_consumption_for_house(self.house_id)
    
    def load_solar_radiation_data(self): # Incarca datele de radiatie solara pentru statia meteo a casei din cache
        self.solar_radiation_data = self.data_dict.get_solar_radiation_for_station(self.weather_station_id)
        if not self.solar_radiation_data:
            print(f"Nu s-au gasit date meteo pentru statia {self.weather_station_id}")
    
    def get_appliance_by_name(self, appliance_name): # Gaseste un aparat dupa nume
        for app in self.appliances:
            if app['name'] == appliance_name:
                return app
        return None
    
    def get_appliances_by_type(self, type_id): # Returneaza toate aparatele de un anumit tip din casa
        return [app for app in self.appliances if app['type_id'] == type_id]
    
    def print_info(self): # Afiseaza informatii complete despre casa
        print(f"\nCasa {self.house_id}")
        print(f"Locatie: {self.location} | Cod postal: {self.zipcode}")
        print(f"Statie meteo: {self.weather_station_id} ({self.weather_station['location']})")
        print(f"Perioada: {self.start_epoch} - {self.end_epoch}")
        print(f"Consum: {len(self.consumption_data)} intervale | Radiatie: {len(self.solar_radiation_data)} intervale")
        print(f"Aparate ({len(self.appliances)}):")
        for app in self.appliances:
            type_info = self.data_dict.get_appliance_type(app['type_id'])
            type_name = type_info['name'] if type_info else 'Unknown'
            print(f"  [{app['id']}] {app['name']} (Tip: {type_name})")
        print()
