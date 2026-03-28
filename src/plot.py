import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
from data_dictionaries import DataDictionaries
import os

########## Plotarea graficelor ##########

# Cache global pentru DataFrame-uri mari
data_cache = DataDictionaries(verbose=False)

# Constante pentru directoarele de ploturi
PLOTS_DIR = "Plots"
INITIAL_DATA_DIR = os.path.join(PLOTS_DIR, "Initial Data")
OPTIMISED_DATA_DIR = os.path.join(PLOTS_DIR, "Optimised Data")
RESULTS_DIR = os.path.join(PLOTS_DIR, "Results")

def plot_10min_consumption_for_day(indicator_obj, target_date):  # Plotare pe zi la interval de 10 minute pentru o casa
    
    df = data_cache.get_consumption_df()
    df = df[df['HouseIDREF'] == indicator_obj.house_id].copy()  # Pastreaza doar randurile care apartin casei curente

    if df.empty:
        print("Nu exista date pentru casa " + str(indicator_obj.house_id))
        return

    # Converteste EpochTime in data-ora si extrage doar data
    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit = 's')
    df['Date'] = df['Datetime'].dt.date

    # Verifica daca data introdusa este valida
    target_day = pd.to_datetime(target_date).date()

    # Cauta ziua ceruta
    df = df[df['Date'] == target_day]

    if df.empty:
        print("Nu exista consum in ziua " + str(target_date) + " pentru casa " + str(indicator_obj.house_id))
        return

    # Grupare pe intervale de 10 minute
    df['Interval'] = df['Datetime'].dt.floor('10min')
    interval_total = df.groupby('Interval')['Value'].sum().reset_index()

    fig = px.line(
        interval_total,
        x = 'Interval',
        y = 'Value',
        title = "Consum total la 10 minute in ziua " + str(target_date) + " pentru casa " + str(indicator_obj.house_id),
        labels = {'Interval': 'Ora (10 minute)', 'Value': 'Consum (W)'},
        markers = True
    )
    fig.update_layout(xaxis_tickformat = '%H:%M')
    fig.write_html(os.path.join(INITIAL_DATA_DIR, "Consum_10min_zi.html"))

def plot_hourly_consumption_for_day(indicator_obj, target_date):  # Plotare pe zi la interval de o ora pentru o casa

    df = data_cache.get_consumption_df()
    df = df[df['HouseIDREF'] == indicator_obj.house_id].copy()  # Filtrare dupa house_id

    if df.empty:
        print("Nu exista date pentru casa " + str(indicator_obj.house_id))
        return

    # Conversie EpochTime -> Datetime + extragere zi
    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit = 's')
    df['Date'] = df['Datetime'].dt.date

    try:
        target_day = pd.to_datetime(target_date).date()
    except Exception as e:
        print("Data introdusa este invalida: " + str(e))
        return

    df = df[df['Date'] == target_day]

    if df.empty:
        print("Nu exista consum in ziua " + str(target_date) + " pentru casa " + str(indicator_obj.house_id))
        return

    # Grupare pe ore
    df['Hour'] = df['Datetime'].dt.floor('h')
    hourly_total = df.groupby('Hour')['Value'].sum().reset_index()
    hourly_total['Value'] /= 6000  # Transformare in kWh

    fig = px.line(
        hourly_total,
        x = 'Hour',
        y = 'Value',
        title = "Consum total orar in ziua " + str(target_date) + " pentru casa " + str(indicator_obj.house_id),
        labels = {'Hour': 'Ora', 'Value': 'Consum (kWh)'},
        markers = True
    )
    fig.update_layout(xaxis_tickformat = '%H:%M')
    fig.write_html(os.path.join(INITIAL_DATA_DIR, "Consum_ora_zi.html"))

def plot_daily_consumption_in_a_year(indicator_obj):  # Plotare pe an la interval de o zi pentru o casa

    df = data_cache.get_consumption_df()
    df = df[df['HouseIDREF'] == indicator_obj.house_id].copy()  # Filtrare dupa ID-ul casei

    if df.empty:
        print("Nu exista date pentru casa " + str(indicator_obj.house_id))
        return

    # Conversie EpochTime -> Datetime + extragere data
    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit = 's')
    df['Date'] = df['Datetime'].dt.date

    # Grupare pe zi si transformare in kWh
    daily_total = df.groupby('Date')['Value'].sum().reset_index()
    daily_total['Value'] /= 6000

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = daily_total['Date'],
        y = daily_total['Value'],
        mode = 'lines+markers',
        name = 'Consum zilnic',
        marker = dict(size = 6, color = 'royalblue'),
        line = dict(color = 'royalblue'),
        hovertemplate = 'Data: %{x}<br>Consum: %{y:.2f} kWh<extra></extra>'
    ))

    fig.update_layout(
        title = "Consum total pe zi pentru casa " + str(indicator_obj.house_id),
        xaxis_title = 'Data',
        yaxis_title = 'Consum (kWh)',
        xaxis_tickformat = '%Y-%m-%d',
        hovermode = 'x unified'
    )

    fig.write_html(os.path.join(INITIAL_DATA_DIR, "Consum_an.html"))

def plot_appliance_hourly_consumption_for_day(indicator_obj, appliance_name, date_str):  # Plotare pe ora pentru un aparat intr-o zi specifica

    df_consumption = data_cache.get_consumption_df()
    df_appliance = data_cache.get_appliance_df()

    # Obtine ID-ul aparatului dupa nume si casa
    filtered_appliances = df_appliance[
        (df_appliance['HouseIDREF'] == indicator_obj.house_id) &
        (df_appliance['Name'] == appliance_name)
    ]

    if filtered_appliances.empty:
        print("Appliance-ul " + appliance_name + " nu a fost gasit pentru casa " + str(indicator_obj.house_id))
        return

    appliance_id = filtered_appliances.iloc[0]['ID']

    # Filtrare consum pentru acel aparat
    df = df_consumption[
        (df_consumption['HouseIDREF'] == indicator_obj.house_id) &
        (df_consumption['ApplianceIDREF'] == appliance_id)
    ].copy()

    if df.empty:
        print("Nu exista date de consum pentru appliance-ul " + appliance_name + " in casa " + str(indicator_obj.house_id))
        return

    # Conversie si filtrare dupa data
    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit = 's')
    df['Date'] = df['Datetime'].dt.date
    df['Hour'] = df['Datetime'].dt.hour

    target_date = pd.to_datetime(date_str).date()
    df = df[df['Date'] == target_date]

    if df.empty:
        print("Nu exista date pentru appliance-ul " + appliance_name + " in data " + date_str)
        return

    # Agregare pe ora
    hourly = df.groupby('Hour')['Value'].sum().reset_index()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = hourly['Hour'],
        y = hourly['Value'],
        mode = 'lines+markers',
        marker = dict(size = 6, color = 'royalblue'),
        line = dict(color = 'royalblue'),
        name = 'Consum',
        hovertemplate = 'Ora: %{x}<br>Consum: %{y:.2f} Wh<extra></extra>'
    ))

    fig.update_layout(
        title = "Consum orar pentru " + appliance_name + " in casa " + str(indicator_obj.house_id) + " (" + date_str + ")",
        xaxis_title = 'Ora',
        yaxis_title = 'Consum (Wh)',
        xaxis = dict(dtick = 1),
        hovermode = 'x unified'
    )

    fig.write_html(os.path.join(INITIAL_DATA_DIR, "Consum_appliance_zi.html"))

def plot_hourly_production_for_day(indicator_obj, day = None): # Plotare productia unei case pe ora intr-o zi
    
    if not hasattr(indicator_obj, 'production') or not indicator_obj.production:
        print("Datele de productie nu sunt disponibile.")
        return

    data = {datetime.fromtimestamp(int(k)): v for k, v in indicator_obj.production.items()}

    if day is None:
        day = next(iter(data)).date()
    elif isinstance(day, str):
        day = datetime.fromisoformat(day).date()

    daily_data = {t: v for t, v in data.items() if t.date() == day}

    if not daily_data:
        print("Nu exista date pentru ziua " + str(day))
        return
    
    times = sorted(daily_data)
    values = [daily_data[t] for t in times]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = np.array(times),
        y = values,
        mode = 'lines+markers',
        name = 'Productie estimata',
        line = dict(color = 'orange'),
        marker = dict(size = 6),
        hovertemplate = 'Ora: %{x|%H:%M}<br>Productie: %{y:.2f} kWh<extra></extra>'
    ))

    fig.update_layout(
        title = "Productia estimata de energie pentru ziua " + str(day),
        xaxis_title = 'Ora',
        yaxis_title = 'Energie produsa (kWh)',
        xaxis = dict(
            tickformat = '%H:%M',
            tickangle = 45,
            title_standoff = 10
        ),
        hovermode = 'x unified',
        template = 'plotly_white'
    )

    fig.write_html(os.path.join(INITIAL_DATA_DIR, "Productie_zi.html"))

def plot_hourly_consumption_and_production_for_day(indicator_obj, target_date, html_filename=None): 
    # Plotare consum si productie pe acelasi grafic (pentru date optimizate sau initiale)

    df = data_cache.get_consumption_df()
    df = df[df['HouseIDREF'] == indicator_obj.house_id].copy()

    if df.empty:
        print("Nu exista date de consum pentru casa " + str(indicator_obj.house_id))
        return

    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit='s')
    df['Date'] = df['Datetime'].dt.date

    target_day = pd.to_datetime(target_date).date()
    df = df[df['Date'] == target_day]

    if df.empty:
        print("Nu exista consum in ziua " + str(target_date) + " pentru casa " + str(indicator_obj.house_id))
        return

    df['Hour'] = df['Datetime'].dt.floor('h')
    hourly_consumption = df.groupby('Hour')['Value'].sum().reset_index()
    hourly_consumption['Value'] /= 6000

    if not hasattr(indicator_obj, 'production') or not indicator_obj.production:
        print("Datele de productie nu sunt disponibile.")
        return

    production_data = {datetime.fromtimestamp(int(k)): v for k, v in indicator_obj.production.items()}
    daily_production = {t: v for t, v in production_data.items() if t.date() == target_day}

    if not daily_production:
        print("Nu exista productie in ziua " + str(target_day))
        return

    production_df = pd.DataFrame({
        'Datetime': np.array(list(daily_production.keys())),
        'Production': list(daily_production.values())
    })

    production_df['Hour'] = production_df['Datetime'].dt.floor('h')
    hourly_production = production_df.groupby('Hour')['Production'].sum().reset_index()

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hourly_consumption['Hour'],
        y=hourly_consumption['Value'],
        mode='lines+markers',
        name='Consum (kWh)',
        line=dict(color='blue'),
        hovertemplate='Ora: %{x|%H:%M}<br>Consum: %{y:.2f} kWh<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=hourly_production['Hour'],
        y=hourly_production['Production'],
        mode='lines+markers',
        name='Productie (kWh)',
        line=dict(color='orange'),
        hovertemplate='Ora: %{x|%H:%M}<br>Productie: %{y:.2f} kWh<extra></extra>'
    ))

    fig.update_layout(
        title="Consum vs Productie in ziua " + str(target_day) + ", casa " + str(indicator_obj.house_id),
        xaxis_title="Ora",
        yaxis_title="Energie (kWh)",
        xaxis=dict(tickformat='%H:%M'),
        hovermode='x unified',
        template='plotly_white'
    )

    if html_filename is None:
        html_filename = os.path.join(INITIAL_DATA_DIR, "Consum_vs_productie_zi.html")
    fig.write_html(html_filename)

def plot_NPV_over_years(indicator_obj, Cwp = 0.6, Pm = 575, n = 10, Y = 20, r = 0.05, price_per_kWh = 0.2): # Plotare evolutie NPV pe Y ani
    
    npv_values = indicator_obj.calculate_NPV(Cwp=Cwp, Pm=Pm, n=n, Y=Y, r=r, price_per_kWh=price_per_kWh)
    years = list(range(1, Y + 1))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=years,
        y=npv_values,
        mode='lines+markers',
        name='NPV',
        line=dict(color='green')
    ))

    fig.add_trace(go.Scatter(
        x=years,
        y=[0] * len(years),
        mode='lines',
        name='Prag rentabilitate',
        line=dict(color='red', dash='dash')
    ))

    fig.update_layout(
        title=f"Evolutia NPV pe {Y} ani (Casa {indicator_obj.house_id})",
        xaxis_title="Ani",
        yaxis_title="NPV (€)",
        hovermode="x unified"
    )

    fig.write_html(os.path.join(INITIAL_DATA_DIR, "NPV_over_years.html"))

def plot_presence_comparison(house_id, date_str, min_active_appliances = 2, percentile = 40): # Compara perceptia managerului despre prezenta cu prezenta reala

    from Simulation.presence_model import PresenceModel
    from Simulation.model import CommunityModel
    
    # Creaza modelul de prezenta
    presence_model = PresenceModel(house_id)
    
    # Obtine datele de prezenta fara printari
    manager_presence = presence_model.evaluate_presence_for_date(date_str, percentile=percentile, verbose=False)
    real_presence = presence_model.evaluate_real_presence_for_date(date_str, min_active_appliances, verbose=False)
    
    if not manager_presence or not real_presence:
        return
    
    # Foloseste aceleasi date de consum ca si pentru evaluarea prezentei
    target_date = datetime.strptime(date_str, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
    target_epoch_start = int(target_date.timestamp())
    target_epoch_end = target_epoch_start + 24 * 60 * 60
    
    # Extrage consumul orar pentru ziua respectiva din aceeasi sursa ca prezenta
    hourly_consumption_dict = {}
    for epoch_time, consumption_value in presence_model.consumption.items():
        if target_epoch_start <= epoch_time < target_epoch_end:
            hourly_consumption_dict[epoch_time] = consumption_value
    
    if not hourly_consumption_dict:
        return
    
    # Ruleaza simularea pentru a obtine consumul ajustat si productia
    model = CommunityModel(num_houses=1, recommendation_type="presence", house_type="presence", specific_house_id=house_id)
    
    # Ruleaza simularea completa
    num_steps = len(model.houses[0].time_keys)
    for _ in range(num_steps):
        model.step()
    
    # Extrage datele de consum ajustat si productie pentru ziua respectiva
    house_agent = model.houses[0]
    adjusted_consumption_dict = {}
    production_dict = {}
    
    for t in house_agent.time_keys:
        if target_epoch_start <= t < target_epoch_end:
            # Gaseste indexul pentru acest timestamp
            idx = house_agent.time_keys.index(t)
            if idx < len(house_agent.consumption_history):
                adjusted_consumption_dict[t] = house_agent.consumption_history[idx]
            if idx < len(house_agent.production_history):
                production_dict[t] = house_agent.production_history[idx]
    
    # Converteste in format pentru plotare
    consumption_times = [datetime.fromtimestamp(t) for t in sorted(hourly_consumption_dict.keys())]
    consumption_values = [hourly_consumption_dict[t] for t in sorted(hourly_consumption_dict.keys())]
    
    adjusted_consumption_times = [datetime.fromtimestamp(t) for t in sorted(adjusted_consumption_dict.keys())]
    adjusted_consumption_values = [adjusted_consumption_dict[t] for t in sorted(adjusted_consumption_dict.keys())]
    
    production_times = [datetime.fromtimestamp(t) for t in sorted(production_dict.keys())]
    production_values = [production_dict[t] for t in sorted(production_dict.keys())]
    
    # Converteste datele de prezenta in format pentru grafic
    manager_timestamps = sorted(manager_presence.keys())
    manager_values = [1 if manager_presence[t] else 0 for t in manager_timestamps]
    manager_times = [datetime.fromtimestamp(t) for t in manager_timestamps]
    
    real_timestamps = sorted(real_presence.keys())
    real_values = [1 if real_presence[t] else 0 for t in real_timestamps]
    real_times = [datetime.fromtimestamp(t) for t in real_timestamps]
    
    # Creeaza graficul cu 5 subplots
    fig = make_subplots(
        rows=5, cols=1,
        subplot_titles=(
            f'Consum orar - Casa {house_id}',
            f'Prezenta perceputa de manager (percentila {percentile}, top {100-percentile}% consumuri)',
            f'Prezenta reala (min. {min_active_appliances} appliance-uri active, >2x minim)',
            f'Consum final dupa recomandari - Casa {house_id}',
            f'Productie solara - Casa {house_id}'
        ),
        vertical_spacing=0.08,
        row_heights=[0.22, 0.18, 0.18, 0.22, 0.20]
    )
    
    # Subplot 1: Consumul orar
    fig.add_trace(
        go.Scatter(
            x=consumption_times,
            y=consumption_values,
            mode='lines+markers',
            name='Consum',
            line=dict(color='blue', width=2),
            marker=dict(size=6),
            hovertemplate='Ora: %{x|%H:%M}<br>Consum: %{y:.3f} kWh<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Subplot 2: Prezenta manager
    fig.add_trace(
        go.Scatter(
            x=manager_times,
            y=manager_values,
            mode='lines',
            name='Prezenta manager',
            line=dict(color='orange', width=3, shape='hv'),
            fill='tozeroy',
            fillcolor='rgba(255, 165, 0, 0.3)',
            hovertemplate='Ora: %{x|%H:%M}<br>Prezenta: %{y}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Subplot 3: Prezenta reala
    fig.add_trace(
        go.Scatter(
            x=real_times,
            y=real_values,
            mode='lines',
            name='Prezenta reala',
            line=dict(color='green', width=3, shape='hv'),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 0, 0.3)',
            hovertemplate='Ora: %{x|%H:%M}<br>Prezenta: %{y}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # Subplot 4: Consumul ajustat dupa recomandari
    fig.add_trace(
        go.Scatter(
            x=adjusted_consumption_times,
            y=adjusted_consumption_values,
            mode='lines+markers',
            name='Consum dupa recomandari',
            line=dict(color='purple', width=2),
            marker=dict(size=6),
            hovertemplate='Ora: %{x|%H:%M}<br>Consum: %{y:.3f} kWh<extra></extra>'
        ),
        row=4, col=1
    )
    
    # Subplot 5: Productia solara
    fig.add_trace(
        go.Scatter(
            x=production_times,
            y=production_values,
            mode='lines+markers',
            name='Productie solara',
            line=dict(color='gold', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(255, 215, 0, 0.2)',
            hovertemplate='Ora: %{x|%H:%M}<br>Productie: %{y:.3f} kWh<extra></extra>'
        ),
        row=5, col=1
    )
    
    # Actualizeaza layout-ul
    fig.update_xaxes(title_text="Ora", tickformat='%H:%M', row=1, col=1)
    fig.update_xaxes(title_text="Ora", tickformat='%H:%M', row=2, col=1)
    fig.update_xaxes(title_text="Ora", tickformat='%H:%M', row=3, col=1)
    fig.update_xaxes(title_text="Ora", tickformat='%H:%M', row=4, col=1)
    fig.update_xaxes(title_text="Ora", tickformat='%H:%M', row=5, col=1)
    
    fig.update_yaxes(title_text="Consum (kWh)", row=1, col=1)
    fig.update_yaxes(title_text="Prezenta", tickvals=[0, 1], ticktext=['NU', 'DA'], row=2, col=1)
    fig.update_yaxes(title_text="Prezenta", tickvals=[0, 1], ticktext=['NU', 'DA'], row=3, col=1)
    fig.update_yaxes(title_text="Consum (kWh)", row=4, col=1)
    fig.update_yaxes(title_text="Productie (kWh)", row=5, col=1)
    
    # Calculeaza statistici de concordanta
    common_timestamps = set(manager_timestamps) & set(real_timestamps)
    if common_timestamps:
        agreements = sum(1 for t in common_timestamps if manager_presence[t] == real_presence[t])
        total = len(common_timestamps)
        agreement_rate = (agreements / total) * 100
        
        # Calculeaza ore prezenta pentru fiecare model
        manager_hours = sum(1 for t in manager_timestamps if manager_presence[t])
        real_hours = sum(1 for t in real_timestamps if real_presence[t])
        
        title_text = (f'Comparatie perceptie manager vs prezenta reala - {date_str}<br>'
                     f'<sub>Concordanta: {agreement_rate:.1f}% | '
                     f'Manager: {manager_hours}h prezenta | '
                     f'Real: {real_hours}h prezenta</sub>')
    else:
        title_text = f'Comparatie perceptie manager vs prezenta reala - {date_str}'
    
    fig.update_layout(
        title_text=title_text,
        height=1400,
        showlegend=True,
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Salveaza graficul
    output_file = os.path.join(RESULTS_DIR, f"Comparatie_prezenta_casa_{house_id}.html")
    fig.write_html(output_file)

def plot_scenarios_ss_sc(num_houses): # Ploteaza cele 4 scenarii de agenti pe un grafic 2D cu 1-SS si 1-SC
    
    from Simulation.model import CommunityModel
    from indicators import Indicators
    
    scenarios = []
    scenario_names = [
        "Community + Probabilistic",
        "Community + Presence",
        "Presence + Probabilistic",
        "Presence + Presence"
    ]
    
    scenario_configs = [
        {"recommendation_type": "community", "house_type": "probabilistic", "agent_type": "100"},
        {"recommendation_type": "community", "house_type": "presence"},
        {"recommendation_type": "presence", "house_type": "probabilistic", "agent_type": "100"},
        {"recommendation_type": "presence", "house_type": "presence"}
    ]
    
    # Ruleaza fiecare scenariu
    for i, config in enumerate(scenario_configs):
        model = CommunityModel(num_houses=num_houses, **config)
        
        num_steps = len(model.houses[0].time_keys)
        for _ in range(num_steps):
            model.step()
        
        # Calculeaza indicatorii cu recomandari
        temp_indicator = Indicators(model.houses[0].unique_id)
        temp_indicator.production = model.production_with_recommendations
        temp_indicator.consumption = model.consumption_with_recommendations
        
        ss = temp_indicator.calculate_indicator("SS")
        sc = temp_indicator.calculate_indicator("SC")
        
        scenarios.append({
            "name": scenario_names[i],
            "SS": ss,
            "SC": sc,
            "1-SS": 1 - ss,
            "1-SC": 1 - sc
        })
    
    # Creeaza graficul
    fig = go.Figure()
    
    colors = ['blue', 'red', 'green', 'purple']
    
    for i, scenario in enumerate(scenarios):
        fig.add_trace(go.Scatter(
            x=[scenario["1-SS"]],
            y=[scenario["1-SC"]],
            mode='markers+text',
            name=scenario["name"],
            marker=dict(size=15, color=colors[i]),
            text=[scenario["name"]],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate=(
                f'<b>{scenario["name"]}</b><br>'
                f'1-SS: {scenario["1-SS"]:.4f}<br>'
                f'1-SC: {scenario["1-SC"]:.4f}<br>'
                f'SS: {scenario["SS"]:.4f}<br>'
                f'SC: {scenario["SC"]:.4f}<extra></extra>'
            )
        ))
    
    fig.update_layout(
        title={
            'text': f"<b>Scenarii de agenti pentru {num_houses} case</b><br><sub>Comparatie indicatori 1-SS vs 1-SC (cu recomandari)</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title="<b>1 - SS (Self-Sufficiency)</b>",
        yaxis_title="<b>1 - SC (Self-Consumption)</b>",
        hovermode='closest',
        template='plotly_white',
        showlegend=True,
        width=1000,
        height=900,
        margin=dict(l=100, r=100, t=120, b=80),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[0, 1],
            constrain='domain',
            scaleanchor='y',
            scaleratio=1
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[0, 1],
            constrain='domain'
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1
        )
    )
    
    # Salveaza graficul
    output_file = os.path.join(RESULTS_DIR, f"Scenarii_SS_SC_{num_houses}_case.html")
    fig.write_html(output_file)
    
    return scenarios

def plot_scenarios_ss_sc_multiple_houses(num_houses_list=None, max_steps=None): # Ploteaza cele 4 scenarii pentru diferite numere de case
    # num_houses_list: lista cu nr de case (default: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    # max_steps: nr maxim de pasi de simulare (None = toti pasi)
    
    from Simulation.model import CommunityModel
    from indicators import Indicators
    import time
    
    if num_houses_list is None:
        num_houses_list = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Simulare pentru toate dimensiunile
    
    colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan', 'magenta', 'brown', 'pink', 'lime']
    
    scenario_names = [
        "Community + Probabilistic",
        "Community + Presence",
        "Presence + Probabilistic",
        "Presence + Presence"
    ]
    
    scenario_configs = [
        {"recommendation_type": "community", "house_type": "probabilistic", "agent_type": "100"},
        {"recommendation_type": "community", "house_type": "presence"},
        {"recommendation_type": "presence", "house_type": "probabilistic", "agent_type": "100"},
        {"recommendation_type": "presence", "house_type": "presence"}
    ]
    
    # Simboluri diferite pentru cele 4 scenarii
    symbols = ['circle', 'square', 'diamond', 'cross']
    
    fig = go.Figure()
    
    all_data = []
    
    total_simulations = len(num_houses_list) * len(scenario_configs)
    current_simulation = 0
    start_time = time.time()
    
    # Dictionar pentru a stoca duratele per dimensiune de comunitate
    duration_per_houses = {n: [] for n in num_houses_list}
    
    # Itereaza prin fiecare numar de case
    for houses_idx, num_houses in enumerate(num_houses_list):
        color = colors[houses_idx % len(colors)]
        
        # Ruleaza fiecare scenariu
        for scenario_idx, config in enumerate(scenario_configs):
            current_simulation += 1
            sim_start = time.time()
            
            model = CommunityModel(num_houses=num_houses, **config)
            
            num_steps = len(model.houses[0].time_keys)
            if max_steps is not None:
                num_steps = min(num_steps, max_steps)
            
            for step_i in range(num_steps):
                model.step()
            
            # Calculeaza indicatorii cu recomandari
            temp_indicator = Indicators(model.houses[0].unique_id)
            temp_indicator.production = model.production_with_recommendations
            temp_indicator.consumption = model.consumption_with_recommendations
            
            ss = temp_indicator.calculate_indicator("SS")
            sc = temp_indicator.calculate_indicator("SC")
            
            sim_duration = time.time() - sim_start
            duration_per_houses[num_houses].append(sim_duration)
            
            data_point = {
                "num_houses": num_houses,
                "scenario": scenario_names[scenario_idx],
                "SS": ss,
                "SC": sc,
                "1-SS": 1 - ss,
                "1-SC": 1 - sc,
                "duration_s": sim_duration
            }
            all_data.append(data_point)
            
            # Adauga punct pe grafic
            fig.add_trace(go.Scatter(
                x=[1 - ss],
                y=[1 - sc],
                mode='markers',
                name=f'{num_houses} case' if scenario_idx == 0 else None,
                legendgroup=f'group{houses_idx}',
                showlegend=(scenario_idx == 0),
                marker=dict(
                    size=12,
                    color=color,
                    symbol=symbols[scenario_idx],
                    line=dict(width=1, color='black')
                ),
                hovertemplate=(
                    f'<b>{num_houses} case - {scenario_names[scenario_idx]}</b><br>'
                    f'1-SS: {1-ss:.4f}<br>'
                    f'1-SC: {1-sc:.4f}<br>'
                    f'SS: {ss:.4f}<br>'
                    f'SC: {sc:.4f}<extra></extra>'
                )
            ))
    
    total_duration = time.time() - start_time
    
    # Formateaza titlul cu informatii despre simulare
    steps_info = f"(maxim {max_steps} pasi)" if max_steps else "(toti pasii disponibili)"
    
    fig.update_layout(
        title={
            'text': f"<b>Scenarii de agenti pentru diferite dimensiuni de comunitate</b><br><sub>Comparatie indicatori 1-SS vs 1-SC (cu recomandari) {steps_info}</sub>",
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title="<b>1 - SS (Self-Sufficiency)</b>",
        yaxis_title="<b>1 - SC (Self-Consumption)</b>",
        hovermode='closest',
        template='plotly_white',
        showlegend=True,
        width=1000,
        height=900,
        margin=dict(l=100, r=100, t=120, b=80),
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[0, 1],
            constrain='domain',
            scaleanchor='y',
            scaleratio=1
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[0, 1],
            constrain='domain'
        ),
        legend=dict(
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='gray',
            borderwidth=1,
            title='Numar de case'
        )
    )
    
    # Salveaza graficul 1-SS vs 1-SC
    output_file = os.path.join(OPTIMISED_DATA_DIR, "Scenarii_SS_SC_multiple.html")
    fig.write_html(output_file)
    
    # GRAFIC NOU: Media (SS+SC)/2 cea mai mare pentru fiecare dimensiune de comunitate
    best_scenarios = []
    
    for num_houses in num_houses_list:
        # Gaseste toate scenariile pentru acest numar de case
        house_data = [d for d in all_data if d['num_houses'] == num_houses]
        
        # Calculeaza media (SS+SC)/2 pentru fiecare scenariu
        best_scenario = None
        best_avg = -1
        
        for data in house_data:
            avg_ss_sc = (data['SS'] + data['SC']) / 2
            if avg_ss_sc > best_avg:
                best_avg = avg_ss_sc
                best_scenario = data.copy()
                best_scenario['avg_ss_sc'] = avg_ss_sc
        
        if best_scenario:
            best_scenarios.append(best_scenario)
    
    # Creeaza graficul pentru media maxima
    fig2 = go.Figure()
    
    houses_list = [s['num_houses'] for s in best_scenarios]
    avg_list = [s['avg_ss_sc'] for s in best_scenarios]
    scenario_list = [s['scenario'] for s in best_scenarios]
    ss_list = [s['SS'] for s in best_scenarios]
    sc_list = [s['SC'] for s in best_scenarios]
    
    # Defineste culori pentru cele 4 scenarii
    scenario_colors = {
        "Community + Probabilistic": 'blue',
        "Community + Presence": 'red',
        "Presence + Probabilistic": 'green',
        "Presence + Presence": 'purple'
    }
    
    colors_for_points = [scenario_colors.get(s, 'gray') for s in scenario_list]
    
    fig2.add_trace(go.Scatter(
        x=houses_list,
        y=avg_list,
        mode='lines+markers',
        name='Medie maxima (SS+SC)/2',
        line=dict(color='darkblue', width=2),
        marker=dict(
            size=12,
            color=colors_for_points,
            line=dict(width=2, color='black')
        ),
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>' +
            'Numar case: %{x}<br>' +
            'Medie (SS+SC)/2: %{y:.4f}<br>' +
            'SS: %{customdata[1]:.4f}<br>' +
            'SC: %{customdata[2]:.4f}<extra></extra>'
        ),
        customdata=list(zip(scenario_list, ss_list, sc_list))
    ))
    
    fig2.update_layout(
        title={
            'text': '<b>Scenariul cu media (SS+SC)/2 cea mai mare pentru fiecare dimensiune de comunitate</b><br><sub>Distributie pe numar de case</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'y': 0.95,
            'yanchor': 'top'
        },
        xaxis_title='<b>Numar de case in comunitate</b>',
        yaxis_title='<b>Media (SS+SC)/2</b>',
        hovermode='closest',
        template='plotly_white',
        width=1200,
        height=700,
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            dtick=10  # Tick la fiecare 10 case
        ),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray',
            range=[0, 1]
        )
    )
    
    # Salveaza graficul media maxima
    output_file2 = os.path.join(RESULTS_DIR, "Media_maxima_SS_SC_vs_case.html")
    fig2.write_html(output_file2)
    
    return all_data

