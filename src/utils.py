import requests
import sys
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from climate_match.src.constants import city_names


features_to_get = ["temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "sunshine_duration"]

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
    
    # TODO: remove ! TESTS !!!
    print(city + "," +geo["results"][0]["country"])

    return lat, lon


def average_temp(weather):
    n = len(weather['daily']["temperature_2m_max"])
    avg = sum(weather['daily']["temperature_2m_max"]) + sum(weather['daily']["temperature_2m_min"])
    return avg / (2*n)

def average_temp_range(weather):
    n = len(weather['daily']["temperature_2m_max"])
    avg = sum(weather['daily']["temperature_2m_max"]) - sum(weather['daily']["temperature_2m_min"])
    return avg / n

def compute_score(pref_temp, pref_range, pref_precip, mode, start_date=None, end_date=None):
    """
    takes preference as input
    returns a score : the lower the better (closer to preferences input)
    can be in forecast (mode= forecast, no date specified)
    or in the past (mode = archive, dates to be specified)
    """
    try:
        score_temperature = []
        score_temperature_ampl = []
        score_precipitation = []

        for city in city_names:
            lat, lon = get_city_coordinates(city)
            #  get weather data for this set of (lat, lon)
            if mode == "forecast":
                weather = requests.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "daily": features_to_get,
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
                        "daily": features_to_get,
                        "timezone": "auto",
                    }
                ).json()
        
            features = compute_obs(weather)
            avg_temp = features[0]
            temp_yearly_range = features[1]
            precipitation = features[3]
            # compute average temperatures
            
            # the lower the score, the better
            score_temperature.append(abs(avg_temp - pref_temp))
            score_temperature_ampl.append(abs(temp_yearly_range - pref_range))
            score_precipitation.append(abs(precipitation - pref_precip))
        total = (np.array(score_temperature) 
                 + np.array(score_temperature_ampl) 
                 + np.array(score_precipitation))
        return total.tolist()
    
    except Exception as e:
        print("Mode does not exist, or other issue interrupted:")
        print(e)
        sys.exit(1)


################################
#    functions for USE CASE 2  #
################################

def compute_obs(weather):
    """
    weather: json object received from open-meteo API
    returns list of the value of each desired parameter
    [yearly_avg_temp_max, yearly_avg_temp_min, avg_temp_coldest_month, avg_temp_hottest_month]
    """
    temperature_2m_min = weather['daily']["temperature_2m_min"]
    n = len(temperature_2m_min)
    temp_yearly = average_temp(weather)
    temp_yearly_range = average_temp_range(weather)
    # find coldest day
    coldest = min(temperature_2m_min)
    # day_index = temperature_2m_min.index(coldest)
    # day = weather['start_date'] + day_index
    # take 15 days before + 15 days after

    # coldest_month_max 
    frost_days_count = sum([1 for day_temp in weather["daily"]["temperature_2m_min"] if day_temp < 0])

    # yearly precipitation sum
    precipitation_yearly = sum(weather["daily"]["precipitation_sum"]) / n
    # easier than dry_months_count :
    dry_days_count = sum([1 for day_precip in weather["daily"]["precipitation_sum"] if day_precip < 10])

    sunshine_duration_yearly = sum(weather['daily']["sunshine_duration"])

    features = [temp_yearly, 
                temp_yearly_range, 
                frost_days_count,
                precipitation_yearly, 
                dry_days_count, 
                sunshine_duration_yearly]

    return features


# Get data for the cities over one year
def get_yearly_weather(cities):
    start_date = "2025-01-01"
    end_date = "2026-01-01"
    res = []
    for city in cities:
        lat, lon = get_city_coordinates(city)
        weather = requests.get(
                        "https://archive-api.open-meteo.com/v1/archive",
                        params={
                            "latitude": lat,
                            "longitude": lon,
                            "start_date": start_date,
                            "end_date": end_date,
                            "daily": features_to_get,
                            "timezone": "auto",
                        }
                    ).json()
        res.append(compute_obs(weather))
        
    res = pd.DataFrame(res)
    res['City'] = cities
    res = res.set_index('City')
    return res


# reduce dimension with PCA
def reduce_PCA(weather):
    cities = weather.index
    print(cities)
    scaler = StandardScaler()
    weather_scaled = scaler.fit_transform(weather)
    pca = PCA(n_components=2)
    pca_features = pca.fit_transform(weather_scaled)
    pca_df = pd.DataFrame(pca_features, columns=[f'PC{i+1}' for i in range(pca_features.shape[1])])
    # Give the dataframe a index to know which city corresponds to which data 
    pca_df['City'] = cities
    pca_df = pca_df.set_index('City')
    return pca_df


def find_clusters(df, k=6):
    """
    k-means clustering algorithm
    returns original df with added column "cluster" (numeric)
    """
    # Normalize data points
    scaled_df = StandardScaler().fit_transform(df)

    # instantiate kmeans class
    kmeans = KMeans(init="random", n_clusters=k, n_init=10)
    # fit k-means algorithm to data
    kmeans.fit(scaled_df)

    df["cluster"] = kmeans.labels_
    sse = kmeans.inertia_
    print(sse)

    return df

def find_k(df):
    """
    elbow method
    """
    scaled_df = StandardScaler().fit_transform(df)
    sse = []
    for i in range(3, 15):
        kmeans = KMeans(init="random", n_clusters=i, n_init=10)
        kmeans.fit(scaled_df)
        sse.append(kmeans.inertia_)

    #visualize results
    plt.plot(range(3, 15), sse)
    plt.xticks(range(3, 15))
    plt.xlabel("Number of Clusters")
    plt.ylabel("SSE")
    plt.show()

