from house import House
import clean
import plot
from indicators import Indicators
import optimize
from Simulation.model import CommunityModel
from Simulation.presence_model import PresenceModel

# Curatare date
# clean.clean_files()

print("Incarcare date pentru casa 2000914")
h = House(2000914)
# h.print_info()  # Decomenteaza pentru a vedea informatii complete despre casa

indicator = Indicators(h.house_id)

# Calculeaza productia pentru numarul dorit de panouri (implicit 10)
indicator.get_power_estimated()  # Necesara pentru calculul indicatorilor

# Obtinerea indicatorilor
indicator.calculate_indicator("SS")
indicator.calculate_indicator("SC")
indicator.calculate_NEEG()
indicator.calculate_NPV()

indicator.print_indicators()
indicator.print_NEEG()
indicator.print_NPV()

# Plotari
# plot.plot_10min_consumption_for_day(indicator, "1998-03-20")
# plot.plot_hourly_consumption_for_day(indicator, "1998-03-20")
# plot.plot_daily_consumption_in_a_year(indicator)
# plot.plot_appliance_hourly_consumption_for_day(indicator, "Fridge (220l)", "1998-03-20")
# plot.plot_hourly_production_for_day(indicator, "1998-03-20") # Trebuie apelat cu indicator pentru ca altfel nu imi vede productia din cauza mostenirii
# plot.plot_hourly_consumption_and_production_for_day(indicator, "1998-03-20")

# Optimizare
# res = optimize.optimize_panels_max_ss_sc(indicator, date = "1998-03-20") # Optimizeaza pe tot anul si ploteaza o zi
# result_ss = optimize.optimize_panels_max_ss(indicator, date = "1998-03-20")
# result_sc = optimize.optimize_panels_max_sc(indicator, date = "1998-03-20")
# result_min_neeg = optimize.optimize_panels_min_neeg(indicator, date = "1998-03-20")

# print("Rezultat maximizare SS si SC:", res)
# print("Rezultat maximizare SS:", result_ss)
# print("Rezultat maximizare SC:", result_sc)
# print("Rezultat minimizare NEEG:", result_min_neeg)

# SIMULARI DE COMUNITATE CU SISTEM DE RECOMANDARI
# 2 tipuri de manageri cu 2 tipuri de case => 4 combinatii

# 1. Agent bazat pe consum mediu comunitatii + case cu probabilitate de aplicare
print("\nCOMBINATIA 1: COMMUNITY + PROBABILISTIC")
model1 = CommunityModel(num_houses = 3, recommendation_type = "community", house_type = "probabilistic", agent_type = "75")
num_steps = len(model1.houses[0].time_keys)
for _ in range(num_steps):
    model1.step()
model1.print_performance_comparison()

# 2. Agent bazat pe consum mediu comunitatii + case care verifica prezenta reala
print("\nCOMBINATIA 2: COMMUNITY + PRESENCE")
model2 = CommunityModel(num_houses = 3, recommendation_type = "community", house_type = "presence")
num_steps = len(model2.houses[0].time_keys)
for _ in range(num_steps):
    model2.step()
model2.print_performance_comparison()

# 3. Agent bazat pe prezenta individuala + case cu probabilitate de aplicare
print("\nCOMBINATIA 3: PRESENCE + PROBABILISTIC")
model3 = CommunityModel(num_houses = 3, recommendation_type = "presence",
                        house_type = "probabilistic", application_rates = [0.25, 0.75, 1.0])
num_steps = len(model3.houses[0].time_keys)
for _ in range(num_steps):
    model3.step()
model3.print_performance_comparison()

# 4. Agent bazat pe prezenta individuala + case care verifica prezenta reala
print("\nCOMBINATIA 4: PRESENCE + PRESENCE")
model4 = CommunityModel( num_houses = 3, recommendation_type = "presence", house_type = "presence")
num_steps = len(model4.houses[0].time_keys)
for _ in range(num_steps):
    model4.step()
model4.print_performance_comparison()

# Comparare perceptie vs realitate
presence_model = PresenceModel(h.house_id)

# Perceptia managerului (10% din media orara)
print("\n1. PERCEPTIA MANAGERULUI:")
manager_perception = presence_model.evaluate_presence_for_date("1998-03-20")

# Realitatea din casa (2x minimul zilei, minim 2 appliance-uri)
print("\n2. REALITATEA DIN CASA:")
real_presence = presence_model.evaluate_real_presence_for_date("1998-03-20", min_active_appliances=2)