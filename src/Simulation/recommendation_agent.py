from mesa import Agent
import pandas as pd
from datetime import datetime

class RecommendationAgent(Agent): # Agent central care analizeaza consumul comunitatii si trimite recomandari tuturor caselor
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.estimated_consumption = 0
        self.estimated_production = 0
    
    def step(self): # Calculeaza consumul si productia totala a comunitatii si trimite recomandari
        self.estimated_consumption = 0
        self.estimated_production = 0
        
        house_agents = self.model.houses
        
        for house in house_agents:
            self.estimated_consumption += house.current_consumption_adjusted
            self.estimated_production += house.current_production
        
        # Genereaza recomandare bazata pe datele comunitatii si o trimite caselor
        recommendation = self.generate_recommendation()
        self.send_recommendation(recommendation)
    
    def generate_recommendation(self): # Genereaza recomandare bazata pe consumul si productia estimate a comunitatii
        if self.estimated_production == 0:
            return "BALANCED"
        elif self.estimated_consumption > 1.3 * self.estimated_production:
            return "REDUCE_CONSUMPTION"
        elif self.estimated_consumption < 0.7 * self.estimated_production:
            return "INCREASE_CONSUMPTION"
        else:
            return "BALANCED"
    
    def send_recommendation(self, recommendation): # Trimite recomandarea tuturor caselor din comunitate
        for house in self.model.houses:
            house.receive_recommendation(recommendation)

class PresenceRecommendationAgent(Agent): # Agent care analizeaza fiecare casa individual + prezenta si trimite recomandari personalizate
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.house_presence_threshold = {}  # Pragul de prezenta pentru fiecare casa
        self.initialized = False  # Flag pentru a calcula pragurile o singura data
    
    def calculate_presence_thresholds(self): # Calculeaza pragul de prezenta (10% din media) pentru fiecare casa din comunitate
        for house in self.model.houses:
            avg_consumption = sum(house.indicators.consumption.values()) / len(house.indicators.consumption)
            self.house_presence_threshold[house.unique_id] = avg_consumption * 0.1
        self.initialized = True
    
    def step(self): # Analizeaza fiecare casa individual si trimite recomandari personalizate
        if not self.initialized: # Calculeaza pragurile la primul step (dupa ce casele sunt create)
            self.calculate_presence_thresholds()
        
        for house in self.model.houses:
            recommendation = self.generate_recommendation_for_house(house)
            house.receive_recommendation(recommendation)

    # Genereaza recomandare pentru o casa specifica bazata pe consumul, productia si pragul de prezenta al acelei case    
    def generate_recommendation_for_house(self, house):
        current_consumption = house.current_consumption
        current_production = house.current_production
        presence_threshold = self.house_presence_threshold.get(house.unique_id, 0)
        
        # Verifica daca e cineva acasa (model manager: 10% din media)
        is_present = current_consumption >= presence_threshold
        
        if not is_present:
            return "BALANCED"
        if current_production == 0:
            return "BALANCED"
        if current_consumption > 1.3 * current_production:
            return "REDUCE_CONSUMPTION"
        elif current_consumption < 0.7 * current_production:
            return "INCREASE_CONSUMPTION"
        else:
            return "BALANCED"
