from mesa import Model
from Simulation.house_agent import HouseAgent, PresenceHouseAgent
from Simulation.recommendation_agent import RecommendationAgent, PresenceRecommendationAgent
from indicators import Indicators
from data_dictionaries import DataDictionaries
import pandas as pd

class CommunityModel(Model): # Model pentru o comunitate de case cu agent central de recomandari
    
    # recommendation_type = community sau presence
    # house_type = probabilistic sau presence
    # application_rates este o lista cu probabilitati personalizate pentru fiecare casa pentru house_type probabilistic
    # agent_type = "100", "75", "50", "25" - doar pentru house_type probabilistic, determina probabilitatea de aplicare a recomandarii
    
    def __init__(self, num_houses = 3, recommendation_type = "community", house_type = "probabilistic", agent_type = "100", application_rates = None):
        super().__init__()
        self.step_count = 0
        self.num_houses = num_houses
        self.recommendation_type = recommendation_type
        self.house_type = house_type
        self.agent_type = agent_type
        self.application_rates = application_rates
        
        # Dictionare pentru stocare consum/productie fara si cu recomandari
        self.consumption_without_recommendations = {}
        self.production_without_recommendations = {}
        self.consumption_with_recommendations = {}
        self.production_with_recommendations = {}

        # Foloseste cache-ul pentru a obtine ID-urile caselor
        data_cache = DataDictionaries(verbose=False)
        all_houses = data_cache.get_all_houses()
        house_ids = list(all_houses.keys())[:num_houses]

        # Creaza agentul de recomandari in functie de tip
        if recommendation_type == "community":
            self.recommendation_agent = RecommendationAgent("recommendation_system", self)
            print(f"Agent de recomandari: COMMUNITY (bazat pe consumul mediu al comunitatii)")
        elif recommendation_type == "presence":
            self.recommendation_agent = PresenceRecommendationAgent("recommendation_system", self)
            print(f"Agent de recomandari: PRESENCE (bazat pe prezenta si consum individual)")
        else:
            print(f"Tip recomandare necunoscut: {recommendation_type}. Optiuni: 'community' sau 'presence'")
        
        # Creeaza agentii pentru case in functie de tip
        self.houses = []
        print(f"Tip case: {house_type.upper()}")
        print("Adaugare case:")
        
        if house_type == "probabilistic":
            # Determina application_rate pentru case
            if application_rates is not None:
                # Foloseste lista de probabilitati specificata
                if len(application_rates) != num_houses:
                    print(f"Numarul de application_rates ({len(application_rates)}) trebuie sa fie egal cu num_houses ({num_houses})")
                self.house_application_rates = application_rates
                print(f"Probabilitati personalizate: {application_rates}")
            else:
                # Foloseste aceeasi probabilitate pentru toate casele bazat pe agent_type
                if agent_type == "100":
                    rate = 1.0
                elif agent_type == "75":
                    rate = 0.75
                elif agent_type == "50":
                    rate = 0.5
                elif agent_type == "25":
                    rate = 0.25
                else:
                    print(f"Tip agent necunoscut: {agent_type}. Se foloseste probabilitate 100%.")
                    rate = 1.0
                self.house_application_rates = [rate] * num_houses
                print(f"Probabilitate aplicare: {agent_type}%")
            
            # Creaza case probabilistice
            for i in range(num_houses):
                house_id = house_ids[i]
                house_rate = self.house_application_rates[i]
                print(f"  Casa {house_id} (application_rate: {house_rate*100:.0f}%)")
                house_agent = HouseAgent(house_id, self, application_rate=house_rate)
                self.houses.append(house_agent)
        
        elif house_type == "presence":
            # Creaza case cu detectie prezenta reala
            print("Case cu detectie prezenta reala (bazat pe appliance-uri)")
            for i in range(num_houses):
                house_id = house_ids[i]
                print(f"  Casa {house_id} (detectie prezenta: 10x minim, >=2 appliance-uri)")
                house_agent = PresenceHouseAgent(house_id, self)
                self.houses.append(house_agent)
        
        else:
            print(f"Tip casa necunoscut: {house_type}. Optiuni: 'probabilistic' sau 'presence'")
        
        print(f"\nComunitate initializata: {num_houses} case")
        print(f"  - Agent recomandari: {recommendation_type}")
        print(f"  - Tip case: {house_type}\n")

    def step(self): # Un pas de simulare pentru toata comunitatea
        for house in self.houses:
            house.step()
        
        self.recommendation_agent.step()
        current_time = self.houses[0].current_time if self.houses else None
        
        if current_time is not None:
            # Calculeaza totaluri pentru acest timestamp
            total_consumption = sum(h.current_consumption for h in self.houses)
            total_production = sum(h.current_production for h in self.houses)
            total_consumption_adjusted = sum(h.current_consumption_adjusted for h in self.houses)
            total_production_adjusted = sum(h.current_production_adjusted for h in self.houses)
            
            self.consumption_without_recommendations[current_time] = total_consumption
            self.production_without_recommendations[current_time] = total_production
            self.consumption_with_recommendations[current_time] = total_consumption_adjusted
            self.production_with_recommendations[current_time] = total_production_adjusted
        
        self.step_count += 1
    
    def print_performance_comparison(self): # Afiseaza comparatia de performanta inainte si dupa recomandari
        
        print("\nCOMPARATIE PERFORMANTA: INAINTE VS DUPA RECOMANDARI")
        
        # Creaza obiecte Indicators temporare pentru calcul
        temp_indicator_without = Indicators(self.houses[0].unique_id)
        temp_indicator_without.production = self.production_without_recommendations
        temp_indicator_without.consumption = self.consumption_without_recommendations
        
        temp_indicator_with = Indicators(self.houses[0].unique_id)
        temp_indicator_with.production = self.production_with_recommendations
        temp_indicator_with.consumption = self.consumption_with_recommendations
        
        # Calculeaza indicatorii fara recomandari
        ss_without = temp_indicator_without.calculate_indicator("SS")
        sc_without = temp_indicator_without.calculate_indicator("SC")
        neeg_without = temp_indicator_without.calculate_NEEG()
        
        # Calculeaza indicatorii cu recomandari
        ss_with = temp_indicator_with.calculate_indicator("SS")
        sc_with = temp_indicator_with.calculate_indicator("SC")
        neeg_with = temp_indicator_with.calculate_NEEG()
        
        # Totaluri
        total_consumption_without = sum(self.consumption_without_recommendations.values())
        total_production_without = sum(self.production_without_recommendations.values())
        total_consumption_with = sum(self.consumption_with_recommendations.values())
        total_production_with = sum(self.production_with_recommendations.values())
        
        print("\nFARA RECOMANDARI")
        print("Consum total: " + str(round(total_consumption_without, 2)) + " kWh")
        print("Productie totala: " + str(round(total_production_without, 2)) + " kWh")
        print("SS (Self-Sufficiency): " + str(round(ss_without, 2)))
        print("SC (Self-Consumption): " + str(round(sc_without, 2)))
        print("NEEG (Net Energy Exchange): " + str(round(neeg_without, 2)) + " kWh")
        
        print("\nCU RECOMANDARI APLICATE")
        print("Consum total ajustat: " + str(round(total_consumption_with, 2)) + " kWh")
        print("Productie totala: " + str(round(total_production_with, 2)) + " kWh")
        print("SS (Self-Sufficiency): " + str(round(ss_with, 2)))
        print("SC (Self-Consumption): " + str(round(sc_with, 2)))
        print("NEEG (Net Energy Exchange): " + str(round(neeg_with, 2)) + " kWh")
        
        print("\nIMBUNATATIRI")
        ss_improvement = ss_with - ss_without
        sc_improvement = sc_with - sc_without
        neeg_reduction = neeg_without - neeg_with
        
        # Imbunatatiri in procente
        ss_improvement_pct = (ss_improvement / ss_without * 100) if ss_without > 0 else 0
        sc_improvement_pct = (sc_improvement / sc_without * 100) if sc_without > 0 else 0
        neeg_reduction_pct = (neeg_reduction / neeg_without * 100) if neeg_without > 0 else 0
        
        print("SS: " + "imbunatatire de " + str(round(ss_improvement_pct, 2)) + "%")
        print("SC: " + "imbunatatire de " + str(round(sc_improvement_pct, 2)) + "%")
        print("NEEG: " + "reducere de " + str(round(neeg_reduction_pct, 2)) + "%")
        
        consumption_reduction = total_consumption_without - total_consumption_with
        consumption_reduction_pct = (consumption_reduction / total_consumption_without) * 100 if total_consumption_without > 0 else 0
        
        print("\nReducere consum: " + str(round(consumption_reduction, 2)) + " kWh (" + str(round(consumption_reduction_pct, 2)) + "%)")
