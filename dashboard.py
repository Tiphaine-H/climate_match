import streamlit as st
import sys
import os
import seaborn as sns

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from climate_match.src.constants import city_names
from climate_match.src import utils


st.title("Find your preferred city !")

# forecast
# TODO : foreacast + archive both here : chose dates, and app sees if past 
# or present
with st.container():
    st.subheader("Where to go in the next 10 days ?")
    st.write("Please describe your ideal weather below:")

    use_nl = st.checkbox("Use natural language instead of sliders", value=False)

    # LLM + parsing to get preferences
    if use_nl:
        nl_input = st.text_area(
            "e.g. \"I want a lot of sunlight, I don't mind cold weather\"",
            height=80,
        )
        if st.button("Submit", key="forecast-llm"):
            if nl_input.strip():
                with st.spinner("Reading your preferences..."):
                    weights = parse_preferences_nl(nl_input)
                st.session_state["preference_weights"] = weights
                st.write("Here's what I understood:")
                st.json(weights)
            else:
                st.warning("Type something first!")

    # sliders for preferences 
    else:
        pref_temp = st.slider("What is your preferred temperature ?",
                            min_value=-20, max_value=30)
        pref_range = st.slider("What is your preferred temperature amplitude ?",
                            min_value=0, max_value=15)
        pref_precip = st.slider("How much rain are you ready for ?",
                                min_value=0, max_value=3)
        if st.button("Submit", key="forecast-sliders"):
            with st.status("Computing") as status:
                pref_city_res = utils.find_holiday_place(pref_temp, pref_range, pref_precip, status)
            st.success(f"Your preferred city for the next 10 days would be {pref_city_res}")
    

# cluster
with st.container():
    st.subheader("Where to move long-term?")
    pref_city = st.selectbox("What is your favorite city in this list? (climate-wise)", 
                             city_names)
    if st.button("Submit", key="clusters"):
        with st.status("Computing") as status:
            weather = utils.get_yearly_weather(city_names)
            weather_reduced = utils.reduce_PCA(weather)

            weather_cluster = utils.find_clusters(weather_reduced)

            # Find other cities that belong to same cluster + print
            pref_cluster = weather_cluster.loc[pref_city]["cluster"]
            # List of cities that are also in that cluster :
            pref_cities_res = weather_cluster[weather_cluster["cluster"] == pref_cluster]
            # We want other cities than the one given by the user : 
            pref_cities_res = pref_cities_res.drop(pref_city)
            pref_cities_res = (pref_cities_res.index).tolist()
            status.update(label="Computing complete!", state="complete")

        if pref_cities_res:
            # transform that list into a long string:
            pref_cities_res_print = ''
            for city in pref_cities_res:
                pref_cities_res_print += city + ', '
            pref_cities_res_print = pref_cities_res_print[:-2] + '.'

            st.success(f"You could also enjoy living in {pref_cities_res_print}")
        else:
            st.error(f"{pref_city} is too different from all other cities in the list for now.")

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
    