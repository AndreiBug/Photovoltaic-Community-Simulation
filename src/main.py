from house import House
import clean
import plot
from energy_processing import EnergyProcessing
from indicators import Indicators
import optimize

h = House(2000938)

# Curatare date
# clean.clean_files()

indicator = Indicators(h.house_id)

# Obtinerea inndicatorilor
indicator.get_consumption()
indicator.get_solar_radiation()
indicator.get_power_estimated()

indicator.calculate_indicator("SS")
indicator.calculate_indicator("SC")
indicator.calculate_NEEG()
indicator.calculate_NPV()

# Plotari
# plot.plot_10min_consumption_for_day(h, "1998-03-20")
# plot.plot_hourly_consumption_for_day(h, "1998-03-20")
# plot.plot_daily_consumption_in_a_year(h)
# plot.plot_appliance_hourly_consumption_for_day(h, "Fridge (220l)", "1998-03-20")
# plot.plot_hourly_production_for_day(indicator, "1998-03-20") # Trebuie apelat cu indicator pentru ca altfel nu imi vede productia din cauza mostenirii
# plot.plot_hourly_consumption_and_production_for_day(indicator, "1998-03-20", optimized = False)

# Optimizare
res = optimize.optimize_panels_max_ss_sc(indicator_obj = indicator)
# result_ss = optimize.optimize_panels_max_ss(indicator)
# result_sc = optimize.optimize_panels_max_sc(indicator)
# result_min_neeg = optimize.optimize_panels_min_neeg(indicator)

print("Rezultat maximizare SS si SC:", res)
# print("Rezultat maximizare SS:", result_ss)
# print("Rezultat maximizare SC:", result_sc)
# print("Rezultat minimizare NEEG:", result_min_neeg)