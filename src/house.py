import pandas as pd

class House:
    def __init__(self, house_id):
        self.house_id = house_id

        house_df = pd.read_csv("Database/House.csv")

        house_data = house_df[house_df['ID'] == house_id]

        row = house_data.iloc[0]
        self.zipcode = row['ZIPcode']
        self.location = row['Location']
        self.weather_station_id = row['WeatherStationIDREF']
        self.start_epoch = row['StartingEpochTime']
        self.end_epoch = row['EndingEpochTime']
