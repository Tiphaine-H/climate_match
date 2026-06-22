import requests
import pandas as pd
import utils
        
city_names = ["Barcelona",
              "Brest",
              "London",
              "Montpellier",
              "Paris",
              "Toulouse",
              ]

print("Enter your preferences :")
print("Average temperature :")
pref_temp = float(input())


score_temperature = []

for city in city_names:
    lat, lon = utils.get_city_coordinates(city)

    #  get weather data for this set of (lat, lon)
    weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": ["temperature_2m_max", "temperature_2m_min",
                        "precipitation_probability_max"],
                "timezone": "auto",
                "forecast_days": 10
            }
       ).json()

    # compute average temperatures
    avg_temp = (utils.average_temp(weather))
    # the lower the score, the better
    score_temperature.append(abs(avg_temp - pref_temp))

scores = dict(zip(city_names, score_temperature))
print("Your preferred city is : ", min(scores, key=scores.get))