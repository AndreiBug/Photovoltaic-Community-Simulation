from house_data_loader import HouseDataLoader

class House:
    def __init__(self, house_id):
        # Incarca toate datele pentru casa folosind HouseDataLoader
        self.loader = HouseDataLoader(house_id)
        
        # Expune atributele principale la nivel de House
        self.house_id = house_id
        self.zipcode = self.loader.zipcode
        self.location = self.loader.location
        self.weather_station_id = self.loader.weather_station_id
        self.start_epoch = self.loader.start_epoch
        self.end_epoch = self.loader.end_epoch
        self.appliances = self.loader.appliances
        
    def get_appliance_by_name(self, name): # Gaseste un aparat dupa nume
        return self.loader.get_appliance_by_name(name)
    
    def get_appliances_by_type(self, type_id): # Returneaza aparatele de un anumit tip
        return self.loader.get_appliances_by_type(type_id)
    
    def print_info(self): # Afiseaza informatii despre casa
        self.loader.print_info()
