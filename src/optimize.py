from scipy.optimize import differential_evolution
from plot import plot_hourly_consumption_and_production_for_day

########## Optimizarea panourilor solare in functie de indicatori ##########

def objective_max_sc_ss(x, indicator_obj, w_sc = 0.5, w_ss = 0.5, Pm = 575, f = 0.8, # Calculare functie obiectiv (scor maxim) pentru optimizarea SS si SC
                            GTSTC = 1000.0): 
    n_panels = x[0]

    # Salveaza productia curenta
    prod_backup = indicator_obj.production

    # Productie temporara pentru n_panels
    indicator_obj.get_power_estimated(n_panels, Pm = Pm, f = f, GTSTC = GTSTC)

    sc_val = indicator_obj.calculate_indicator("SC")
    ss_val = indicator_obj.calculate_indicator("SS")

    # Revenire la productia originala
    indicator_obj.production = prod_backup

    score = (w_sc * sc_val) + (w_ss * ss_val)

    # DE minimizeaza => intoarcem negativul
    return -score

def objective_min_neeg(x, indicator_obj, Pm = 575, f = 0.8, GTSTC = 1000.0): # Calculare functie obiectiv pentru optimizarea NEEG
    n_panels = x[0]

    prod_backup = indicator_obj.production

    indicator_obj.get_power_estimated(n_panels, Pm = Pm, f = f, GTSTC = GTSTC)

    neeg_val = indicator_obj.calculate_NEEG()

    indicator_obj.production = prod_backup

    return neeg_val  # DE minimizeaza, deci minimizam NEEG direct

def optimize_panels_max_ss_sc(indicator_obj, n_min = 1, n_max = 40, w_sc = 0.5, w_ss = 0.5, Pm = 575, f = 0.8, # Differential evolution pentru maximizare SS si SC
                                    GTSTC = 1000.0, maxiter = 40, popsize = 15):
    if not indicator_obj.consumption:
        print("Nu exista date pentru consum")
        return
    if not indicator_obj.solar_radiation:
        print("Nu exista date pentru radiatie")
        return

    bounds = [(n_min, n_max)]

    result = differential_evolution(
        objective_max_sc_ss,
        bounds = bounds,
        args = (indicator_obj, w_sc, w_ss, Pm, f, GTSTC),
        maxiter = maxiter,
        popsize = popsize,
    )

    n_opt = int(round(result.x[0]))
    n_opt = max(n_min, min(n_opt, n_max))

    # Seteaza productia optimizata in indicator_obj
    indicator_obj.get_power_estimated(n_opt, Pm = Pm, f = f, GTSTC = GTSTC)

    # Calculeaza indicatorii finali
    sc_opt = indicator_obj.calculate_indicator("SC")
    ss_opt = indicator_obj.calculate_indicator("SS")
    best_score = (w_sc * sc_opt) + (w_ss * ss_opt)

    print("\nRezultate Differential Evolution")
    print("Panouri optime:", n_opt)
    print("SC:", round(sc_opt, 3))
    print("SS:", round(ss_opt, 3))
    print("Scor combinat:", round(best_score, 3), "\n")

    # Afisare plot cu valori optimizate
    plot_hourly_consumption_and_production_for_day(indicator_obj, "1998-03-20", optimized=True)

    return {
        'best_n': n_opt,
        'best_score': best_score,
        'best_SC': sc_opt,
        'best_SS': ss_opt
    }

def optimize_panels_max_ss(indicator_obj, n_min = 1, n_max = 40, Pm = 575, f = 0.8, # Differential evolution pentru maximizare SS
                                GTSTC = 1000.0, maxiter = 40, popsize = 15):
    return optimize_panels_max_ss_sc(
        indicator_obj = indicator_obj, n_min = n_min, n_max = n_max, w_sc = 0.0, w_ss = 1.0,
        Pm = Pm, f = f, GTSTC = GTSTC, maxiter = maxiter, popsize = popsize
    )

def optimize_panels_max_sc(indicator_obj, n_min = 1, n_max = 40, Pm = 575, f = 0.8, # Differential evolution pentru maximizare SC
                                GTSTC = 1000.0, maxiter = 40, popsize = 15):
    return optimize_panels_max_ss_sc(
        indicator_obj = indicator_obj, n_min = n_min, n_max = n_max, w_sc = 1.0, w_ss = 0.0,
        Pm = Pm, f = f, GTSTC = GTSTC, maxiter = maxiter, popsize = popsize
    )

def optimize_panels_min_neeg(indicator_obj, n_min = 1, n_max = 40, Pm = 575, f = 0.8, # Differential evolution pentru minimizare NEEG
                                GTSTC = 1000.0, maxiter = 40, popsize = 15):
    if not indicator_obj.consumption:
        print("Nu exista date pentru consum")
        return
    if not indicator_obj.solar_radiation:
        print("Nu exista date pentru radiatie")
        return


    bounds = [(n_min, n_max)]

    result = differential_evolution(
        objective_min_neeg, bounds = bounds, args = (indicator_obj, Pm, f, GTSTC),
        maxiter = maxiter, popsize = popsize,
    )

    n_opt = int(round(result.x[0]))
    n_opt = max(n_min, min(n_opt, n_max))

    indicator_obj.get_power_estimated(n_opt, Pm = Pm, f = f, GTSTC = GTSTC)

    neeg_opt = indicator_obj.calculate_NEEG()

    print("\n Rezultate Minim NEEG ")
    print("Panouri optime: " + str(n_opt))
    print("NEEG minim: " + str(round(neeg_opt, 3)) + " kWh\n")

    # Afisare plot cu valori optimizate
    plot_hourly_consumption_and_production_for_day(indicator_obj, "1998-03-20", optimized = True)

    return {
        'best_n': n_opt,
        'best_NEEG': neeg_opt,
    }
