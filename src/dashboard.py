import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from climate_match.src.utils import get_city_coordinates, average_temp


start_date = "2025-01-01"
end_date = "2025-12-31"


# Get data for the cities over one year
def get_yearly_weather(cities):
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
                            "daily": ["temperature_2m_max",
                                        "temperature_2m_min"],
                            "timezone": "auto",
                        }
                    ).json()
        
        temp_max = weather['daily']["temperature_2m_max"]
        temp_min = weather['daily']["temperature_2m_min"]
        res.append(np.array(temp_min + temp_max))
        
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


def find_clusters(df):
    """
    k-means clustering algorithm
    returns original df with added column "cluster" (numeric)
    """
    # Normalize data points
    scaled_df = StandardScaler().fit_transform(df)

    # instantiate kmeans class
    kmeans = KMeans(init="random", n_clusters=6, n_init=10)
    # fit k-means algorithm to data
    kmeans.fit(scaled_df)

    df["cluster"] = kmeans.labels_
    print(kmeans.inertia_)

    return df
