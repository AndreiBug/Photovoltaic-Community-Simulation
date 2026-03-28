from house import House

########## Functii pentru calculul energiei produse / consumate ##########

class EnergyProcessing(House):
    def __init__(self, house_id):
        super().__init__(house_id)
        
        # Foloseste datele pre-incarcate din loader
        self.consumption = self.loader.consumption_data.copy()
        self.solar_radiation = self.loader.solar_radiation_data.copy()
        self.production = {}  # Se calculeaza la nevoie cu get_power_estimated()
    
    def get_consumption(self): # Returneaza consumul (deja incarcat din loader)
        return self.consumption

    def get_solar_radiation(self): # Returneaza radiatia solara (deja incarcata din loader)
        return self.solar_radiation

    def get_power_estimated(self, n=10, Pm=575, f=0.8, GTSTC=1000): # Calculeaza puterea produsa estimata pentru n panouri
        if not self.solar_radiation:
            print("Radiatia solara nu este incarcata.")
            return {}
        
        self.production = {
            t: (Pm * n * f * G / GTSTC) / 6000  # W*10min -> kWh
            for t, G in self.solar_radiation.items()
        }
        
        return self.production

    def print_consumption(self): # Printeaza primele 30 valori de consum
        for i, (key, value) in enumerate(self.consumption.items()):
            if i >= 30:
                break
            print(f"Consum la ora {i + 1}: Epoch {key} -> {round(value, 3)} kWh")

    def print_solar_radiation(self): # Printeaza primele 30 valori de radiatie solara
        for i, (key, value) in enumerate(self.solar_radiation.items()):
            if i >= 30:
                break
            print(f"Radiatie la ora {i + 1}: Epoch {key} -> G = {value}")

    def print_power_estimated(self): # Printeaza primele 30 valori de putere estimata
        for i, (key, value) in enumerate(self.production.items()):
            if i >= 30:
                break
            print(f"Putere estimata la ora {i + 1}: Epoch {key} -> {round(value, 3)} kW")
