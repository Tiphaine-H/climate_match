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


def compute_score(pref_temp, mode, start_date=None, end_date=None):
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
    parser.add_argument("--forecast", action="store_true")
    parser.add_argument("--archive", nargs=2, metavar=("start_date", "end_date"))
    parser.add_argument("--dashboard", action="store_true")
    args = parser.parse_args()

    if args.forecast or args.archive:
        print("Enter your preferences :")
        print("Average temperature :")
        while True:
            try:
                pref_temp = float(input())
                break
            except ValueError:
                print("The temperature should be given as numericals.")
        if args.forecast:
            score_temperature = compute_score(pref_temp, "forecast")
        else:
            score_temperature = compute_score(pref_temp, "archive", args.archive[0], args.archive[1])
        scores = dict(zip(city_names, score_temperature))
        print("Your preferred city is : ", min(scores, key=scores.get))

    if args.dashboard:
        print("todo")

if __name__ == "__main__":
    sys.exit(main())
