from mesa import Model
from Simulation.house_agent import HouseAgent, PresenceHouseAgent
from Simulation.recommendation_agent import RecommendationAgent, PresenceRecommendationAgent
from indicators import Indicators
from data_dictionaries import DataDictionaries
import pandas as pd

class CommunityModel(Model): # Model pentru o comunitate de case cu agent de recomandari
    
    # recommendation_type = community sau presence
    # house_type = probabilistic sau presence
    # application_rates este o lista cu probabilitati personalizate pentru fiecare casa pentru house_type probabilistic
    # agent_type = "100", "75", "50", "25" - doar pentru house_type probabilistic, determina probabilitatea de aplicare a recomandarii
    # specific_house_id = ID-ul unei case specifice (optional) - daca este setat, se foloseste doar aceasta casa
    
    def __init__(self, num_houses = 3, recommendation_type = "community", house_type = "probabilistic", agent_type = "100", application_rates = None, specific_house_id = None, recommendation_time_window = None, fixed_community_production = None):
        super().__init__()
        self.step_count = 0
        self.num_houses = num_houses
        self.recommendation_type = recommendation_type
        self.house_type = house_type
        self.agent_type = agent_type
        self.application_rates = application_rates
        self.recommendation_time_window = recommendation_time_window
        self.fixed_community_production = fixed_community_production

        if self.fixed_community_production is not None:
            if isinstance(self.fixed_community_production, dict):
                if not self.fixed_community_production:
                    print("Seria de productie a centralei este vida. Se foloseste productia reala cumulata a caselor.")
                    self.fixed_community_production = None
            elif not isinstance(self.fixed_community_production, (int, float)) or self.fixed_community_production < 0:
                print("Productia centralei este invalida. Se foloseste productia reala cumulata a caselor.")
                self.fixed_community_production = None

        if self.recommendation_time_window is not None:
            if (
                not isinstance(self.recommendation_time_window, tuple)
                or len(self.recommendation_time_window) != 2
            ):
                print("Fereastra orara invalida. Se foloseste trimiterea recomandarilor toata ziua.")
                self.recommendation_time_window = None
            else:
                start_hour, end_hour = self.recommendation_time_window
                if (
                    not isinstance(start_hour, int)
                    or not isinstance(end_hour, int)
                    or start_hour < 0
                    or end_hour > 23
                    or start_hour > end_hour
                ):
                    print("Fereastra orara invalida. Se foloseste trimiterea recomandarilor toata ziua.")
                    self.recommendation_time_window = None
        
        # Dictionare pentru stocare consum/productie fara si cu recomandari
        self.consumption_without_recommendations = {}
        self.production_without_recommendations = {}
        self.consumption_with_recommendations = {}
        self.production_with_recommendations = {}

        # Foloseste cache-ul pentru a obtine ID-urile caselor
        data_cache = DataDictionaries(verbose=False)
        all_houses = data_cache.get_all_houses()
        all_house_ids = list(all_houses.keys())
        
        # Daca este specificat specific_house_id, foloseste doar acea casa
        if specific_house_id is not None:
            house_ids = [specific_house_id]
            self.num_houses = 1
        else:
            # Cicleaza casele daca sunt mai putine decat num_houses
            if num_houses > len(all_house_ids):
                house_ids = (all_house_ids * ((num_houses // len(all_house_ids)) + 1))[:num_houses]
            else:
                house_ids = all_house_ids[:num_houses]

        # Creaza agentul de recomandari in functie de tip
        if recommendation_type == "community":
            self.recommendation_agent = RecommendationAgent("recommendation_system", self)
        elif recommendation_type == "presence":
            self.recommendation_agent = PresenceRecommendationAgent("recommendation_system", self)
        else:
            print(f"Tip recomandare necunoscut: {recommendation_type}. Optiuni: 'community' sau 'presence'")
        
        # Creeaza agentii pentru case in functie de tip
        self.houses = []
        
        if house_type == "probabilistic":
            # Determina application_rate pentru case
            if application_rates is not None:
                if len(application_rates) != num_houses:
                    print(f"Eroare: Numarul de application_rates ({len(application_rates)}) != num_houses ({num_houses})")
                self.house_application_rates = application_rates
            else:
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
            
            # Creaza case probabilistice
            for i in range(num_houses):
                house_id = house_ids[i]
                house_rate = self.house_application_rates[i]
                house_agent = HouseAgent(house_id, self, application_rate=house_rate)
                self.houses.append(house_agent)
        
        elif house_type == "presence":
            for i in range(num_houses):
                house_id = house_ids[i]
                house_agent = PresenceHouseAgent(house_id, self)
                self.houses.append(house_agent)
        
        else:
            print(f"Tip casa necunoscut: {house_type}. Optiuni: 'probabilistic' sau 'presence'")

    def can_send_recommendations(self, current_time):
        if current_time is None:
            return False

        if self.recommendation_time_window is None:
            return True

        start_hour, end_hour = self.recommendation_time_window
        hour = pd.to_datetime(current_time, unit='s').hour
        return start_hour <= hour <= end_hour

    def get_total_production(self, current_time=None):
        if self.fixed_community_production is not None:
            if isinstance(self.fixed_community_production, dict):
                if current_time is None:
                    return 0
                return float(self.fixed_community_production.get(current_time, 0))
            return float(self.fixed_community_production)
        return sum(h.current_production for h in self.houses)

    def get_house_production(self, house, current_time=None):
        if self.fixed_community_production is not None:
            return self.get_total_production(current_time)
        return house.current_production

    def step(self): # Un pas de simulare pentru toata comunitatea
        for house in self.houses:
            house.step()
        
        self.recommendation_agent.step()
        current_time = self.houses[0].current_time if self.houses else None
        
        if current_time is not None:
            central_production = self.get_total_production(current_time)

            # Actualizeaza istoricul fiecarei case DUPA aplicarea recomandarii
            for house in self.houses:
                house.consumption_history.append(house.current_consumption_adjusted)
                if self.fixed_community_production is not None:
                    house.current_production_adjusted = central_production
                else:
                    house.current_production_adjusted = house.current_production
                house.production_history.append(house.current_production_adjusted)
            
            # Calculeaza totaluri pentru acest timestamp
            total_consumption = sum(h.current_consumption for h in self.houses)
            total_production = central_production
            total_consumption_adjusted = sum(h.current_consumption_adjusted for h in self.houses)
            total_production_adjusted = central_production
            
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
