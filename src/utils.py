import requests
import sys
from .constants import city_names


def get_city_coordinates(city):
    """
    get the location of the city / connect city name to 
    its latitude and longitude
    """
    geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1}
        ).json()

    if not geo.get("results"):
        print("City {} Not Found".format(city))

    loc = geo["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]
    return lat, lon


def average_temp(weather):
    n = len(weather['daily']["temperature_2m_max"])
    avg = sum(weather['daily']["temperature_2m_max"]) + sum(weather['daily']["temperature_2m_min"])
    return avg / (2*n)

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
            lat, lon = get_city_coordinates(city)
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
            avg_temp = (average_temp(weather))
            # the lower the score, the better
            score_temperature.append(abs(avg_temp - pref_temp))
        return score_temperature
    
    except:
        print("Mode does not exist.")
        sys.exit(1)