import sys
import argparse
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


def eval(pref_temp, mode, start_date=None, end_date=None):
    """
    takes preference as input
    returns a score : the lower the better (closer to preferences input)
    can be in forecast (mode= forecast, no date specified)
    or in the past (mode = archive, dates to be specified)
    """
    try:
        score_temperature = []

        for city in city_names:
            lat, lon = utils.get_city_coordinates(city)
            #  get weather data for this set of (lat, lon)
            if mode == "forecast":
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

            if mode == "archive":
                weather = requests.get(
                    "https://archive-api.open-meteo.com/v1/archive",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": start_date,
                        "end_date": end_date,
                        "daily": ["temperature_2m_max",
                                    "temperature_2m_min"],
                        "timezone": "auto",
                    }
                ).json()
        
            # compute average temperatures
            avg_temp = (utils.average_temp(weather))
            # the lower the score, the better
            score_temperature.append(abs(avg_temp - pref_temp))
        return score_temperature
    
    except:
        print("Mode does not exist.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user")
    args = parser.parse_args()
    if args.user:
        mode = sys.argv[2]
        print("Enter your preferences :")
        print("Average temperature :")
        pref_temp = float(input())
        score_temperature = eval(pref_temp, mode, "2026-05-23", "2026-06-01")
        # score_temperature = eval(pref_temp, mode)

        scores = dict(zip(city_names, score_temperature))
        print("Your preferred city is : ", min(scores, key=scores.get))


if __name__ == "__main__":
    sys.exit(main())
