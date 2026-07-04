import requests
from functools import lru_cache
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from transformers import pipeline
from climate_match.src.constants import city_names

# if this is modified, need to also update the cache structure for stored
# weather data previously collected
features_to_get = ["temperature_2m_max",
                   "temperature_2m_min",
                   "precipitation_sum",
                   "sunshine_duration"]



@lru_cache(maxsize=None)
def get_city_coordinates(city):
    """
    get the location of the city / connect city name to 
    its latitude and longitude
    """
    try:
        resp = requests.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1},
                timeout=5,
            )
        resp.raise_for_status()
        geo = resp.json()

        if not geo.get("results"):
            print("City {} Not Found".format(city))
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch coordinates for {city}: {e}") from e
    
    loc = geo["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]
    
    # TODO: remove ! TESTS !!!
    print(city + ", " + geo["results"][0]["country"])

    return lat, lon


def average_temp(weather):
    n = len(weather['daily']["temperature_2m_max"])
    avg = sum(weather['daily']["temperature_2m_max"]) + sum(weather['daily']["temperature_2m_min"])
    return avg / (2*n)


def average_temp_range(weather):
    n = len(weather['daily']["temperature_2m_max"])
    avg = sum(weather['daily']["temperature_2m_max"]) - sum(weather['daily']["temperature_2m_min"])
    return avg / n


cache_weather_forecast = dict()


def compute_score(pref_temp, pref_range, pref_precip, mode, start_date=None, end_date=None):
    """
    takes preference as input
    returns a score : the lower the better (closer to preferences input)
    can be in forecast (mode= forecast, no date specified)
    or in the past (mode = archive, dates to be specified)
    """
    # try:
    score_temperature = []
    score_temperature_ampl = []
    score_precipitation = []

    for city in city_names:
        lat, lon = get_city_coordinates(city)
        #  get weather data for this set of (lat, lon)
        if mode == "forecast":
            if city in cache_weather_forecast:
                weather = cache_weather_forecast[city]
            else:
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
                cache_weather_forecast[city] = weather

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
    
        avg_temp = average_temp(weather)
        temp_range = average_temp_range(weather)
        precip = weather["daily"]["precipitation_sum"]
        precip = [data for data in precip if data is not None]
        precipitation = sum(precip) / len(precip)
        
        # the lower the score, the better
        score_temperature.append(abs(avg_temp - pref_temp))
        score_temperature_ampl.append(abs(temp_range - pref_range))
        score_precipitation.append(abs(precipitation - pref_precip))
    total = (np.array(score_temperature) 
                + np.array(score_temperature_ampl) 
                + np.array(score_precipitation))
    return total.tolist()
    
    # except Exception as e:
    #     print("Mode does not exist, or other issue interrupted:")
    #     print(e)
    #     sys.exit(1)


################################
#    functions for USE CASE 2  #
################################
cache_features = dict()


def compute_obs(weather, size_window=30):
    """
    weather: json object received from open-meteo API
    returns list of the value of each desired parameter
    [yearly_avg_temp_max, yearly_avg_temp_min, avg_temp_coldest_month, avg_temp_hottest_month]
    """
    lat, lon = weather["latitude"], weather["longitude"]

    if (lat, lon) in cache_features:
        features = cache_features[(lat, lon)]
    else:
        # GET RAW FEATURES
        temperature_2m_min = weather['daily']["temperature_2m_min"]
        temperature_2m_max = weather['daily']["temperature_2m_max"]
        precip = weather["daily"]["precipitation_sum"]
        # remove "lost" data if there is some :
        precip = [data for data in precip if data is not None]

        n = len(temperature_2m_min)

        # AVG_TEMP
        temp_yearly = average_temp(weather)

        # AVG RANGE
        temp_yearly_range = average_temp_range(weather)

        # AVG PRECIPITATION (rain + snow + ...)
        precip_yearly = sum(precip) / len(precip)
        
        # prepare to find coldest month with sliding window:
        temp_min = temperature_2m_min + temperature_2m_min[:size_window]
        window_min = temp_min[:size_window]
        left, right = 0, size_window
        value_window_min = sum(window_min)
        coldest_month = value_window_min

        # prepare to find hottest month sum of temperatures
        temp_max = temperature_2m_max + temperature_2m_max[:size_window]
        window_max = temp_max[:size_window]
        value_window_max = sum(window_max)
        hottest_month = value_window_max

        # run sliding window to find hottest and coldest months
        while right < n + size_window:
            value_window_min = value_window_min + temp_min[right] - temp_min[left]
            value_window_max = value_window_max + temp_max[right] - temp_max[left]
            coldest_month = min(coldest_month, value_window_min)
            hottest_month = max(hottest_month, value_window_max)
            left += 1
            right += 1
        
        # sliding window for dryest month
        n_precip = len(precip)
        window_precip = precip[:size_window]
        left, right = 0, size_window
        value_window_precip = sum(window_precip)
        dryest_month = value_window_precip
        while right < n_precip:
            value_window_precip = value_window_precip + precip[right] - precip[left]
            dryest_month = min(dryest_month, value_window_precip)
            left += 1
            right += 1


        # days below 0
        # frost_days_count = sum([1 for day_temp in weather["daily"]["temperature_2m_min"] if day_temp < 0])

        # dry_months_count :
        precip_per_month = []
        for k in range(12):
            precip_month = sum(precip[30*k:30*(k+1)])
            precip_per_month.append(precip_month)
        dry_months_count = sum([1 for precip_month in precip_per_month 
                                if precip_month < 10])
        
        # WET MONTHS COUNT
        # drenched_months_count = sum([1 for precip_month in precip_per_month 
        #                            if precip_month > 50])
        
        sunshine_duration = weather['daily']["sunshine_duration"]
        sunshine_duration = [data for data in sunshine_duration if data is not None]
        sunshine_duration = sum(sunshine_duration)

        features = [temp_yearly,
                    temp_yearly_range,
                    hottest_month - coldest_month,
                    # frost_days_count,
                    precip_yearly,
                    dryest_month,
                    dry_months_count,
                    # drenched_months_count,
                    sunshine_duration]
        cache_features[(lat, lon)] = features
    return features


cache_weather = dict()


# Get data for the cities over one year
def get_yearly_weather(cities):
    start_date = "2025-01-01"
    end_date = "2026-01-01"
    res = []
    for city in cities:
        lat, lon = get_city_coordinates(city)
        if city in cache_weather:
            weather = cache_weather[city]
        else:
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
            cache_weather[city] = weather
        res.append(compute_obs(weather))
        
    res = pd.DataFrame(res)
    print(res.corr())

    res['City'] = cities
    res = res.set_index('City')
    return res


# reduce dimension with PCA
def reduce_PCA(weather, n_components=2):
    cities = weather.index
    print(cities)
    scaler = StandardScaler()
    weather_scaled = scaler.fit_transform(weather)
    pca = PCA(n_components)
    pca_features = pca.fit_transform(weather_scaled)
    pca_df = pd.DataFrame(pca_features, columns=[f'PC{i+1}' for i in range(pca_features.shape[1])])
    # Give the dataframe a index to know which city corresponds to which data 
    pca_df['City'] = cities
    pca_df = pca_df.set_index('City')
    print(pca.components_)
    print("pca_explained", pca.explained_variance_ratio_)
    return pca_df


def find_clusters(df, k=9):
    """
    k-means clustering algorithm
    returns original df with added column "cluster" (numeric)
    """
    # Normalize data points
    scaler = StandardScaler()
    scaled_df = scaler.fit_transform(df)

    # instantiate kmeans class
    kmeans = KMeans(init="random", n_clusters=k, n_init=10)
    # fit k-means algorithm to data
    kmeans.fit(scaled_df)

    df["cluster"] = kmeans.labels_
    # sse = kmeans.inertia_

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


################################
#    functions for DASHBOARD   #
################################


def find_holiday_place(pref_temp, pref_range, pref_precip, status):
    pref_temp = float(pref_temp)
    score_temperature = compute_score(pref_temp,
                                      pref_range,
                                      pref_precip,
                                      "forecast")
    scores = dict(zip(city_names, score_temperature))
    pref_city_res = min(scores, key=scores.get)
    status.update(label="Computing complete!", state="complete")
    return pref_city_res


def parse_preferences_nl(nl_input):
    print("work in progress")
    classifier = pipeline("zero-shot-classification")
    # TODO : rather sentence-transformers similarity (less heavy, better for streamlit)
