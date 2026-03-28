import pandas as pd
import os

class DataDictionaries:
    # Clasa pentru gestionarea dictionarelor cu date din baza de date.
    
    instance = None  # Singleton pattern
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.initialized = False
        return cls.instance
    
    def __init__(self, verbose = False):
        if self.initialized:
            return
            
        self.initialized = True
        self.verbose = verbose
        
        # Determina calea catre directorul Database
        if os.path.exists("Database"):
            self.db_path = "Database"
        elif os.path.exists("../Database"):
            self.db_path = "../Database"
        else:
            raise FileNotFoundError("Nu s-a gasit directorul Database!")
        
        # Dictionare principale - acces direct dupa ID
        self.houses = {}
        self.appliances = {}
        self.appliance_types = {}
        self.weather_stations = {}
        
        # Dictionare de cautare pentru aparate
        self.appliances_by_house = {}
        self.appliances_by_type = {}
        
        # Cache-uri pentru DataFrames mari (lazy loading)
        self.consumption_df = None  # Se incarca la cerere
        self.appliance_df = None
        self.weather_data_df = None
        
        # Cache pentru datele procesate (grupate per casa si statie meteo)
        self.consumption_by_house = {}
        self.radiation_by_station = {}
        
        # Incarca toate datele
        self.load_all_data()
        
        if self.verbose:
            print("DataDictionaries initializat cu succes!")
            print(f"  - {len(self.houses)} case")
            print(f"  - {len(self.appliances)} aparate")
            print(f"  - {len(self.appliance_types)} tipuri de aparate")
            print(f"  - {len(self.weather_stations)} statii meteo")
    
    def load_all_data(self): # Incarca toate datele din CSV-uri in dictionare
        self.load_houses()
        self.load_appliance_types()
        self.load_appliances()
        self.load_weather_stations()
        
    def load_houses(self): # Incarca datele despre case din House.csv
        df = pd.read_csv(f"{self.db_path}/House.csv")
        
        for _, row in df.iterrows():
            house_id = row['ID']
            self.houses[house_id] = {
                'id': house_id,
                'zipcode': row['ZIPcode'],
                'location': row['Location'],
                'weather_station_id': row['WeatherStationIDREF'],
                'start_epoch': row['StartingEpochTime'],
                'end_epoch': row['EndingEpochTime']
            }
    
    def load_appliances(self): # Incarca datele despre aparate electrocasnice din Appliance.csv
        df = pd.read_csv(f"{self.db_path}/Appliance.csv")
        
        for _, row in df.iterrows():
            # ID-ul unic va fi combinatia (HouseIDREF, ID)
            house_id = row['HouseIDREF']
            appliance_id = row['ID']
            unique_key = (house_id, appliance_id)
            
            self.appliances[unique_key] = {
                'id': appliance_id,
                'house_id': house_id,
                'name': row['Name'],
                'type_id': row['TypeIDREF']
            }
            
            # Dictionar de cautare dupa casa
            if house_id not in self.appliances_by_house:
                self.appliances_by_house[house_id] = []
            self.appliances_by_house[house_id].append(unique_key)
            
            # Dictionar de cautare dupa tip
            type_id = row['TypeIDREF']
            if type_id not in self.appliances_by_type:
                self.appliances_by_type[type_id] = []
            self.appliances_by_type[type_id].append(unique_key)
    
    def load_appliance_types(self): # Incarca tipurile de aparate electrocasnice din ApplianceType.csv.
        df = pd.read_csv(f"{self.db_path}/ApplianceType.csv")
        
        for _, row in df.iterrows():
            type_id = row['ID']
            self.appliance_types[type_id] = {
                'id': type_id,
                'name': row['Name']
            }
    
    def load_weather_stations(self): # Incarca datele despre statiile meteo din WeatherStation.csv
        df = pd.read_csv(f"{self.db_path}/WeatherStation.csv")
        
        for _, row in df.iterrows():
            station_id = row['ID']
            self.weather_stations[station_id] = {
                'id': station_id,
                'location': row['Location'],
                'longitude': row['Longitude'],
                'latitude': row['Latitude'],
                'start_epoch': row['StartingEpochTime'],
                'end_epoch': row['EndingEpochTime']
            }
    
    # Acces case
    
    def get_house(self, house_id): # Returneaza toate atributele unei case dupa ID.
        return self.houses.get(house_id)
    
    def get_all_houses(self): # Returneaza dictionarul cu toate casele
        return self.houses
    
    # Acces aparate
    
    def get_appliances_for_house(self, house_id): # Returneaza toate aparatele dintr-o casa.
        appliance_keys = self.appliances_by_house.get(house_id, [])
        return [self.appliances[key] for key in appliance_keys]
    
    def get_appliances_by_type(self, type_id): # Returneaza toate aparatele de un anumit tip.

        appliance_keys = self.appliances_by_type.get(type_id, [])
        return [self.appliances[key] for key in appliance_keys]
    
    def get_appliance_by_name(self, house_id, appliance_name): # Gaseste un aparat dupa numele sau intr-o casa specifica.

        appliances = self.get_appliances_for_house(house_id)
        for app in appliances:
            if app['name'] == appliance_name:
                return app
        return None
    
    # Acces tipuri de aparate
    
    def get_appliance_type(self, type_id): # Returneaza tipul unui aparat dupa ID.
        return self.appliance_types.get(type_id)
    
    # Acces statii meteo
    
    def get_weather_station(self, station_id): # Returneaza informatii despre o statie meteo.
        return self.weather_stations.get(station_id)
    
    # Acces date procesate si DataFrame-uri mari
    
    def get_consumption_df(self): # Returneaza DataFrame-ul cu toate datele de consum, se initiaza cu None si se apeleaza la nevoie
        if self.consumption_df is None:
            if self.verbose:
                print("Incarcare Consumption.csv...")
            self.consumption_df = pd.read_csv(f"{self.db_path}/Consumption.csv")
            if self.verbose:
                print("Consumption.csv incarcat")
        return self.consumption_df
    
    def get_appliance_df(self): # Returneaza DataFrame-ul cu toate aparatele, se initiaza cu None si se apeleaza la nevoie
        if self.appliance_df is None:
            if self.verbose:
                print("Incarcare Appliance.csv...")
            self.appliance_df = pd.read_csv(f"{self.db_path}/Appliance.csv")
            if self.verbose:
                print("Appliance.csv incarcat")
        return self.appliance_df
    
    def get_weather_data_df(self): # Returneaza DataFrame-ul cu toate datele meteo, se initiaza cu None si se apeleaza la nevoie
        if self.weather_data_df is None:
            if self.verbose:
                print("Incarcare WeatherData.csv...")
            self.weather_data_df = pd.read_csv(f"{self.db_path}/WeatherData.csv")
            if self.verbose:
                print("WeatherData.csv incarcat")
        return self.weather_data_df
    
    def get_consumption_for_house(self, house_id):
        # Returneaza consumul procesat pentru o casa (dictionar {epoch_orar: kWh})

        if house_id not in self.consumption_by_house:
            df = self.get_consumption_df()
            df_house = df[df['HouseIDREF'] == house_id].copy()
            
            df_house['HourEpoch'] = df_house['EpochTime'] - (df_house['EpochTime'] % 3600)
            df_hourly = df_house.groupby('HourEpoch')['Value'].sum()
            
            # Convertire in kWh
            self.consumption_by_house[house_id] = (df_hourly / 6000).to_dict()
        
        return self.consumption_by_house[house_id]
    
    def get_solar_radiation_for_station(self, station_id):
        # Returneaza radiatia solara pentru o statie meteo (dictionar {epoch: W/m2})
        
        if station_id not in self.radiation_by_station:
            df = self.get_weather_data_df()
            
            # Filtreaza dupa statia meteo si variabila 4 (radiatie solara)
            df_filtered = df[
                (df['WeatherStationIDREF'] == station_id) &
                (df['WeatherVariableIDREF'] == 4)
            ]
            
            if df_filtered.empty:
                self.radiation_by_station[station_id] = {}
            else:
                self.radiation_by_station[station_id] = df_filtered.groupby('EpochTime')['Value'].sum().to_dict()
        
        return self.radiation_by_station[station_id]

