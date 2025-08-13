from house import House
import clean
import plot
from energy_processing import EnergyProcessing
from indicators import Indicators
import optimize

# Curatare date
# clean.clean_files()

h = House(2000938)
indicator = Indicators(h.house_id)

# Obtinerea inndicatorilor
indicator.get_consumption()
indicator.get_solar_radiation()
indicator.get_power_estimated()

indicator.calculate_indicator("SS")
indicator.calculate_indicator("SC")
indicator.calculate_NEEG()
indicator.calculate_NPV()

indicator.print_indicators()
indicator.print_NEEG()
indicator.print_NPV()

# # Plotari
# plot.plot_10min_consumption_for_day(indicator, "1998-03-20")
# plot.plot_hourly_consumption_for_day(indicator, "1998-03-20")
# plot.plot_daily_consumption_in_a_year(indicator)
# plot.plot_appliance_hourly_consumption_for_day(indicator, "Fridge (220l)", "1998-03-20")
# plot.plot_hourly_production_for_day(indicator, "1998-03-20") # Trebuie apelat cu indicator pentru ca altfel nu imi vede productia din cauza mostenirii
# plot.plot_hourly_consumption_and_production_for_day(indicator, "1998-03-20")

# # Optimizare
# res = optimize.optimize_panels_max_ss_sc(indicator, date = "1998-03-20") # Optimizeaza pe tot anul si ploteaza o zi
# result_ss = optimize.optimize_panels_max_ss(indicator, date = "1998-03-20")
# result_sc = optimize.optimize_panels_max_sc(indicator, date = "1998-03-20")
# result_min_neeg = optimize.optimize_panels_min_neeg(indicator, date = "1998-03-20")

# print("Rezultat maximizare SS si SC:", res)
# print("Rezultat maximizare SS:", result_ss)
# print("Rezultat maximizare SC:", result_sc)
# print("Rezultat minimizare NEEG:", result_min_neeg)