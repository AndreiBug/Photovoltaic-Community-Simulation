import gc
from house import House
import clean
import plot
from indicators import Indicators
import optimize
from Simulation.model import CommunityModel
from Simulation.presence_model import PresenceModel

# Curatare date
# clean.clean_files()

print("Incarcare date pentru casa")
h = House(2000938)
print("Finalizare incarcare date pentru casa")
# h.print_info()

indicator = Indicators(h.house_id)

indicator.get_power_estimated()  # Necesara pentru calculul indicatorilor

# Obtinerea indicatorilor
indicator.calculate_indicator("SS")
indicator.calculate_indicator("SC")
indicator.calculate_NEEG()
indicator.calculate_NPV(Cwp=0.6, Pm=575, n=10, Y=20, r=0.05, price_per_kWh=0.2)

indicator.print_indicators()
indicator.print_NEEG()
indicator.print_NPV()

# Acuratete prezenta perceputa vs reala pe toate datele disponibile
presence_model = PresenceModel(h.house_id)
# presence_model.calculate_presence_accuracy_for_all_data(percentile=50, min_active_appliances=2, verbose=True)

# SIMULARI DE COMUNITATE CU SISTEM DE RECOMANDARI
# 2 tipuri de manageri cu 2 tipuri de case => 4 combinatii
# None pentru recomandari toata ziua sau de exemplu (7, 22) pentru intervalul 07:00-22:00
recommendation_time_window = None
# Centrala comuna cu productie fixa pentru toata comunitatea
panel_count = 300
panel_power_w = 575
performance_factor = 0.8
central_indicator = Indicators(h.house_id)
fixed_community_production = central_indicator.get_power_estimated(n=panel_count, Pm=panel_power_w, f=performance_factor)

# Seteaza aici daca scenariile de comunitate folosesc productie fixa sau suma productiilor caselor
use_fixed_community_production = True
scenario_fixed_community_production = fixed_community_production if use_fixed_community_production else None

# Pentru productie individuala pe fiecare casa:
fixed_community_production = None

# 1. Agent bazat pe consum mediu comunitatii + case cu probabilitate de aplicare
print("\nCOMBINATIA 1: COMMUNITY + PROBABILISTIC")
model1 = CommunityModel(num_houses = 100, recommendation_type = "community", house_type = "probabilistic", agent_type = "100", recommendation_time_window = recommendation_time_window, fixed_community_production = scenario_fixed_community_production)
num_steps = len(model1.houses[0].time_keys)
for _ in range(num_steps):
    model1.step()
model1.print_performance_comparison()

# 2. Agent bazat pe consum mediu comunitatii + case care verifica prezenta reala
print("\nCOMBINATIA 2: COMMUNITY + PRESENCE")
model2 = CommunityModel(num_houses = 100, recommendation_type = "community", house_type = "presence", recommendation_time_window = recommendation_time_window, fixed_community_production = scenario_fixed_community_production)
num_steps = len(model2.houses[0].time_keys)
for _ in range(num_steps):
    model2.step()
model2.print_performance_comparison()

# 3. Agent bazat pe prezenta individuala + case cu probabilitate de aplicare
print("\nCOMBINATIA 3: PRESENCE + PROBABILISTIC")
model3 = CommunityModel(num_houses = 100, recommendation_type = "presence",
                        house_type = "probabilistic", agent_type = "100", recommendation_time_window = recommendation_time_window, fixed_community_production = scenario_fixed_community_production)
num_steps = len(model3.houses[0].time_keys)
for _ in range(num_steps):
    model3.step()
model3.print_performance_comparison()

# 4. Agent bazat pe prezenta individuala + case care verifica prezenta reala
print("\nCOMBINATIA 4: PRESENCE + PRESENCE")
model4 = CommunityModel(num_houses = 100, recommendation_type = "presence", house_type = "presence", recommendation_time_window = recommendation_time_window, fixed_community_production = scenario_fixed_community_production)
num_steps = len(model4.houses[0].time_keys)
for _ in range(num_steps):
    model4.step()
model4.print_performance_comparison()

del model1, model2, model3, model4
gc.collect()

########## PLOTARI ##########
print("GENERARE PLOTURI")

# ========== PLOTARI PENTRU DATE INITIALE (Initial Data) ==========
print("\n--- Ploturi pentru date initiale ---")

# Consum la intervale diferite pentru o zi specificata
plot.plot_10min_consumption_for_day(indicator, "1998-03-20")
plot.plot_hourly_consumption_for_day(indicator, "1998-03-20")
# Consum zilnic pe un an intreg
plot.plot_daily_consumption_in_a_year(indicator)
# Consum per aparat intr-o zi
plot.plot_appliance_hourly_consumption_for_day(indicator, "TV (60cm)", "1998-03-21")
# Productie solara intr-o zi (necesita indicator pentru acces la productia estimata)
plot.plot_hourly_production_for_day(indicator, "1998-03-20")
# Comparatie consum vs productie intr-o zi
plot.plot_hourly_consumption_and_production_for_day(indicator, "1998-03-20", n=3)
# Evolutie NPV pe mai multi ani
plot.plot_NPV_over_years(indicator, Cwp=0.6, Pm=575, n=10, Y=20, r=0.05, price_per_kWh=0.2)

# ========== PLOTARI PENTRU OPTIMIZARI (Optimised Data) ==========
print("\n--- Optimizare + Ploturi pentru date optimizate ---")

# Optimizeaza pe tot anul si ploteaza o zi
res = optimize.optimize_panels_max_ss_sc(indicator, date = "1998-03-20")
result_ss = optimize.optimize_panels_max_ss(indicator, date = "1998-03-20")
result_sc = optimize.optimize_panels_max_sc(indicator, date = "1998-03-20")
result_min_neeg = optimize.optimize_panels_min_neeg(indicator, date = "1998-03-20")

print("Rezultat maximizare SS si SC:", res)
print("Rezultat maximizare SS:", result_ss)
print("Rezultat maximizare SC:", result_sc)
print("Rezultat minimizare NEEG:", result_min_neeg)

# ========== PLOTARI PENTRU PREZENTA SI COMPARATII (Results) ==========
print("\n--- Ploturi pentru prezenta si comparatii ---")

# Comparatie perceptie manager vs prezenta reala
plot.plot_presence_comparison(house_id=h.house_id, date_str="1998-04-23", min_active_appliances=2, percentile=50)


# ========== PLOTARI PENTRU SCENARII SS-SC (Results) ==========
print("\n--- Ploturi pentru scenarii agenti ---")

# Plotare scenarii SS-SC pentru cele 4 combinatii de agenti (100 case, 300 panouri fixe)
scenarios = plot.plot_scenarios_ss_sc(num_houses=100, fixed_community_production=scenario_fixed_community_production)

# Plotare scenarii SS-SC pentru 10-100 case (din 10 in 10), cu numar de panouri variabil
# (3 panouri pentru fiecare casa: 10 case -> 30 panouri, 20 case -> 60 panouri, ..., 100 case -> 300 panouri)
plot.plot_scenarios_ss_sc_multiple_houses(
    num_houses_list = list(range(10, 101, 10)),
    panels_per_house = 3,
    house_id_for_production = h.house_id,
    panel_power_w = panel_power_w,
    performance_factor = performance_factor
)

print("FINALIZARE GENERARE PLOTURI")
