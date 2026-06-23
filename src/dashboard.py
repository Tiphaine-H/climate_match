import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.cluster.vq import whiten, kmeans, vq, kmeans2
from climate_match.src.utils import get_city_coordinates, average_temp


cities = ["Paris", "London", "Liverpool"]
start_date = "2025-01-01"
end_date = "2025-12-31"


# Get data for the cities over one year
def get_yearly_weather():
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
        
    return pd.DataFrame(res)


# reduce dimension with PCA
def reduce_PCA(weather):
    scaler = StandardScaler()
    weather_scaled = scaler.fit_transform(weather)
    pca = PCA(n_components=2)
    pca_features = pca.fit_transform(weather_scaled)
    pca_df = pd.DataFrame(pca_features, columns=[f'PC{i+1}' for i in range(pca_features.shape[1])])
    # Give the dataframe a index to know which city corresponds to which data 
    pca_df['City'] = cities
    pca_df = pca_df.set_index('City')
    return pca_df

# k-means clustering algorithm

#  1. Normalize data points



#  2. Compute the centroids 




# 3. Form clusters and assign the data points


