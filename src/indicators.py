from energy_processing import EnergyProcessing

########## Calculul indicatorilor SS, SC, NEEG, NPV ##########

class Indicators(EnergyProcessing):
    def __init__(self, house_id):
        super().__init__(house_id)
        self.SC = 0
        self.SS = 0
        self.NPV = []
        self.NEEG = 0

    def is_production_available(self):
        if not self.production:
            print("Productia nu este disponibila.")
            return False
        return True

    def is_consumption_available(self):
        if not self.consumption:
            print("Consumul nu este disponibil.")
            return False
        return True

    def calculate_indicator(self, indicator_type): # Calculeaza SS sau SC, se dau ca parametru in functie
        if not self.is_production_available() or not self.is_consumption_available():
            return 0

        numerator = 0
        denominator = 0

        common_times = set(self.production.keys()) & set(self.consumption.keys())

        for t in common_times:
            prod = self.production[t]
            cons = self.consumption[t]
            numerator += min(prod, cons)

            if indicator_type == "SC":
                denominator += prod
            elif indicator_type == "SS":
                denominator += cons

        if denominator == 0:
            print(str(indicator_type) + ": Numitorul este 0. Nu poate fi calculat.")
            setattr(self, indicator_type, 0)
            return 0

        value = numerator / denominator
        setattr(self, indicator_type, value)
        return value

    def calculate_NEEG(self): # Calculul NEEG
        if not self.is_production_available() or not self.is_consumption_available():
            self.NEEG = 0
            return 0
        
        imported_energy = 0
        exported_energy = 0
        
        common_times = set(self.production.keys()) & set(self.consumption.keys())

        for t in common_times:
            prod = self.production[t]
            cons = self.consumption[t]
            
            if cons > prod:
                imported_energy += (cons - prod)
            elif prod > cons:
                exported_energy += (prod - cons)

        self.NEEG = imported_energy + exported_energy
        return self.NEEG

    def calculate_NPV(self, Cwp = 0.6, Pm = 575, n = 5, Y = 20, r = 0.05, price_per_kWh = 0.2): # Calculeaza lista NPV pe fiecare an pentru perioada de Y ani
        # Cwp = cost per watt
        # Pm = puterea unui panou (W)
        # n = numar panouri
        # Y = numar ani
        # r = rata de actualizare
        # price_per_kWh = pret energie

        # Recalculeaza productia pentru n panouri la Pm W, sa fie consistenta cu CapEX
        self.get_power_estimated(n=n, Pm=Pm)

        if not self.is_production_available() or not self.is_consumption_available():
            self.NPV = [0] * Y
            return [0] * Y

        # Cost initial (CapEX) si cost anual (OpEX)
        CapEX = Cwp * Pm * n
        OpEX = 0.03 * CapEX

        # Ore comune
        common_times = set(self.production.keys()) & set(self.consumption.keys())
        if not common_times:
            print("Nu exista date comune pentru calculul NPV.")
            return [0] * Y

        # Consum si autoconsum total
        total_consumption = sum(self.consumption[t] for t in common_times)
        total_self_consumption = sum(min(self.production[t], self.consumption[t]) for t in common_times)

        # Extindem la un an intreg
        hours_available = len(common_times)
        annual_consumption = (total_consumption / hours_available) * 8760
        annual_self_consumption = (total_self_consumption / hours_available) * 8760

        # Factura fara PV
        B_ref = annual_consumption * price_per_kWh

        # Factura cu PV
        energy_from_grid = max(0, annual_consumption - annual_self_consumption)
        B_new = energy_from_grid * price_per_kWh

        # Economie anuala
        G = B_ref - B_new

        # Calcul NPV pe fiecare an
        npv_values = []
        npv_cumul = -CapEX  # anul 0, investitia
        for t in range(1, Y + 1):
            npv_cumul += (G - OpEX) / ((1 + r) ** t)
            npv_values.append(npv_cumul)

        self.NPV = npv_values
        return npv_values

    def print_indicators(self): # Printeaza SS/SC
        if hasattr(self, "SC"):
            print(f"SC: {round(self.SC, 3)}")
        if hasattr(self, "SS"):
            print(f"SS: {round(self.SS, 3)}")

    def print_NEEG(self): # Printeaza NEEG
        if hasattr(self, "NEEG"):
            print(f"NEEG: {round(self.NEEG, 3)} kWh")

    def print_NPV(self): # Printeaza NPV
        if isinstance(self.NPV, list) and len(self.NPV) > 0:
            print(f"NPV final: {round(self.NPV[-1], 3)}")
            print(f"Lista NPV: {[round(val, 3) for val in self.NPV]}")
        else:
            print("NPV nu este calculat inca.")

