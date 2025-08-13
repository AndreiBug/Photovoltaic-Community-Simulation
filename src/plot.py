import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

########## Plotarea graficelor ##########

def plot_10min_consumption_for_day(house, target_date):  # Plotare pe zi la interval de 10 minute pentru o casa
    
    input_csv = "Database/Consumption.csv"
    df = pd.read_csv(input_csv)
    df = df[df['HouseIDREF'] == house.house_id]  # Pastreaza doar randurile care apartin casei curente

    if df.empty:
        print("Nu exista date pentru casa " + str(house.house_id))
        return

    # Converteste EpochTime in data-ora si extrage doar data
    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit = 's')
    df['Date'] = df['Datetime'].dt.date

    # Verifica daca data introdusa este valida
    target_day = pd.to_datetime(target_date).date()

    # Cauta ziua ceruta
    df = df[df['Date'] == target_day]

    if df.empty:
        print("Nu exista consum in ziua " + str(target_date) + " pentru casa " + str(house.house_id))
        return

    # Grupare pe intervale de 10 minute
    df['Interval'] = df['Datetime'].dt.floor('10min')
    interval_total = df.groupby('Interval')['Value'].sum().reset_index()

    fig = px.line(
        interval_total,
        x = 'Interval',
        y = 'Value',
        title = "Consum total la 10 minute in ziua " + str(target_date) + " pentru casa " + str(house.house_id),
        labels = {'Interval': 'Ora (10 minute)', 'Value': 'Consum (W)'},
        markers = True
    )
    fig.update_layout(xaxis_tickformat = '%H:%M')
    fig.write_html("Plots/Date initiale/Consum_10min_zi.html")

def plot_hourly_consumption_for_day(house, target_date):  # Plotare pe zi la interval de o ora pentru o casa
    input_csv = "Database/Consumption.csv"  # Fisierul cu datele de consum

    df = pd.read_csv(input_csv)
    df = df[df['HouseIDREF'] == house.house_id]  # Filtrare dupa house_id

    if df.empty:
        print("Nu exista date pentru casa " + str(house.house_id))
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
        print("Nu exista consum in ziua " + str(target_date) + " pentru casa " + str(house.house_id))
        return

    # Grupare pe ore
    df['Hour'] = df['Datetime'].dt.floor('h')
    hourly_total = df.groupby('Hour')['Value'].sum().reset_index()
    hourly_total['Value'] /= 6000  # Transformare in kWh

    fig = px.line(
        hourly_total,
        x = 'Hour',
        y = 'Value',
        title = "Consum total orar in ziua " + str(target_date) + " pentru casa " + str(house.house_id),
        labels = {'Hour': 'Ora', 'Value': 'Consum (kWh)'},
        markers = True
    )
    fig.update_layout(xaxis_tickformat = '%H:%M')
    fig.write_html("Plots/Date initiale/Consum_ora_zi.html")

def plot_daily_consumption_in_a_year(house):  # Plotare pe an la interval de o zi pentru o casa
    input_csv = "Database/Consumption.csv"

    df = pd.read_csv(input_csv)
    df = df[df['HouseIDREF'] == house.house_id]  # Filtrare dupa ID-ul casei

    if df.empty:
        print("Nu exista date pentru casa " + str(house.house_id))
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
        title = "Consum total pe zi pentru casa " + str(house.house_id),
        xaxis_title = 'Data',
        yaxis_title = 'Consum (kWh)',
        xaxis_tickformat = '%Y-%m-%d',
        hovermode = 'x unified'
    )

    fig.write_html("Plots/Date initiale/Consum_an.html")

def plot_appliance_hourly_consumption_for_day(house, appliance_name, date_str):  # Plotare pe ora pentru un aparat intr-o zi specifica
    consumption_csv = "Database/Consumption.csv"
    appliance_csv = "Database/Appliance.csv"

    df_consumption = pd.read_csv(consumption_csv)
    df_appliance = pd.read_csv(appliance_csv)

    # Obtine ID-ul aparatului dupa nume si casa
    filtered_appliances = df_appliance[
        (df_appliance['HouseIDREF'] == house.house_id) &
        (df_appliance['Name'] == appliance_name)
    ]

    if filtered_appliances.empty:
        print("Appliance-ul " + appliance_name + " nu a fost gasit pentru casa " + str(house.house_id))
        return

    appliance_id = filtered_appliances.iloc[0]['ID']

    # Filtrare consum pentru acel aparat
    df = df_consumption[
        (df_consumption['HouseIDREF'] == house.house_id) &
        (df_consumption['ApplianceIDREF'] == appliance_id)
    ].copy()

    if df.empty:
        print("Nu exista date de consum pentru appliance-ul " + appliance_name + " in casa " + str(house.house_id))
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
        title = "Consum orar pentru " + appliance_name + " in casa " + str(house.house_id) + " (" + date_str + ")",
        xaxis_title = 'Ora',
        yaxis_title = 'Consum (Wh)',
        xaxis = dict(dtick = 1),
        hovermode = 'x unified'
    )

    fig.write_html("Plots/Date initiale/Consum_appliance_zi.html")

def plot_hourly_production_for_day(house, day = None): # Plotare productia unei case pe ora intr-o zi
    
    if not hasattr(house, 'production') or not house.production:
        print("Datele de productie nu sunt disponibile.")
        return

    data = {datetime.fromtimestamp(int(k)): v for k, v in house.production.items()}

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
        x = np.array(times),  # explicit np.array
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

    fig.write_html("Plots/Date initiale/Productie_zi.html")

def plot_hourly_consumption_and_production_for_day(house, target_date, html_filename="Plots/Date initiale/Consum_vs_productie_zi.html"): 
    # Plotare consum si productie pe acelasi grafic (pentru date optimizate sau initiale)

    consumption_csv = "Database/Consumption.csv"
    df = pd.read_csv(consumption_csv)
    df = df[df['HouseIDREF'] == house.house_id]

    if df.empty:
        print("Nu exista date de consum pentru casa " + str(house.house_id))
        return

    df['Datetime'] = pd.to_datetime(df['EpochTime'], unit='s')
    df['Date'] = df['Datetime'].dt.date

    target_day = pd.to_datetime(target_date).date()
    df = df[df['Date'] == target_day]

    if df.empty:
        print("Nu exista consum in ziua " + str(target_date) + " pentru casa " + str(house.house_id))
        return

    df['Hour'] = df['Datetime'].dt.floor('h')
    hourly_consumption = df.groupby('Hour')['Value'].sum().reset_index()
    hourly_consumption['Value'] /= 6000

    if not hasattr(house, 'production') or not house.production:
        print("Datele de productie nu sunt disponibile.")
        return

    production_data = {datetime.fromtimestamp(int(k)): v for k, v in house.production.items()}
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
        title="Consum vs Productie in ziua " + str(target_day) + ", casa " + str(house.house_id),
        xaxis_title="Ora",
        yaxis_title="Energie (kWh)",
        xaxis=dict(tickformat='%H:%M'),
        hovermode='x unified',
        template='plotly_white'
    )

    fig.write_html(html_filename)

def plot_NPV_over_years(house, Cwp = 0.6, Pm = 575, n = 10, Y = 20, r = 0.05, price_per_kWh = 0.2): # Plotare evolutie NPV pe Y ani
    npv_values = house.calculate_NPV(Cwp=Cwp, Pm=Pm, n=n, Y=Y, r=r, price_per_kWh=price_per_kWh)
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
        title=f"Evolutia NPV pe {Y} ani (Casa {house.house_id})",
        xaxis_title="Ani",
        yaxis_title="NPV (€)",
        hovermode="x unified"
    )

    fig.write_html("Plots/Date initiale/NPV_over_years.html")
