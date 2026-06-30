import streamlit as st
import sys
import os
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from climate_match.src.constants import city_names
from climate_match.src import utils

st.title("Find your preferred city !")

# forecast
# TODO : foreacast + archive both here : chose dates, and app sees if past 
# or present
with st.container():
    st.subheader("Where to go in the next 10 days ?")
    pref_temp = st.text_input("What is you preferred temperature ? (daily average)", "Type here...")
    if st.button("Submit", key="forecast"):
        pref_temp = float(pref_temp)
        score_temperature = utils.compute_score(pref_temp, "forecast")
        scores = dict(zip(city_names, score_temperature))
        pref_city_res = min(scores, key=scores.get)
        st.write("Your preferred city for the next 10 days would be ", pref_city_res)

# cluster
with st.container():
    st.subheader("Where to move long-term?")
    pref_city = st.selectbox("What is your favorite city in this list? (climate-wise)", 
                             city_names)
    if st.button("Submit", key="clusters"):
        st.write("favorite city is ", pref_city)
        
        weather = utils.get_yearly_weather(city_names)
        weather_reduced = utils.reduce_PCA(weather)

        weather_cluster = utils.find_clusters(weather_reduced)


        # TO REMOVE LATER : 
        ax = sns.scatterplot(data=weather_cluster,
                             x="PC1",
                             y="PC2",
                             hue="cluster",
                             palette="tab10")

        for idx, row in weather_cluster.iterrows():
            ax.annotate(str(idx), xy=(row["PC1"], row["PC2"]), xytext=(5, 5),
                        textcoords='offset points', fontsize=8, color='gray')
        st.pyplot()

