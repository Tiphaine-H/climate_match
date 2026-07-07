# Finding your preferred city

ClimaCluster : Find your ideal city based on climate similarity and 10-day forecasts : try it out yourself [here](https://climate-match-dashboard-tiphaine.streamlit.app)!

## What it does: 

Discover which of 52 cities best matches your climate preferences.
Get your own result either for the next 10 days, based on preferences like temperature, rain, or daily sunshine duration, or simply indicate your favorite city climate-wise for the app to tell you where to go ! 


## How it works:
Cluster cities by climate profile :

- Data Source : Open-Meteo
- Feature engineering : Originally, I wanted to use each weather data of each day as a feature. It quickly proved to introduce a huge geographical bias : day to day, cities in a closer area would live through the same meteorological events. And cities from the Southern hemisphere could never be considered similar to cities in the Northern hemisphere, due to seasons inversion.  
  That is why I engineered the following features :
  - average temperature all year round ((sum(temp_max) + sum(temp_min)) / 2n)
  - average daily range of temperature all year round ((sum(temp_max) - sum(temp_min)) / 2n)
  - seasonal range of temperature (sum(temp_max of the hottest month) - sum(temp_min) of the coldest month)
  - average of precipiation all year round
  - dryest month
  - dry months count
  - average daily sunshine duration
  - Other features were not retained like frost_days_count (number of days with temperatures below 0 in a year), wettest_month (sum of precipitation over the month where it is highest) wet_months_count, as they were too strongly correlated (>=0.9) to minimal temperatures or to yearly precipitation amount. 
- K-means : the default value of k was chosen using the elbow method.
- PCA : this dimensionality reduction was originally operated before k-means, as each daily weather data was used as a feature (365 features only just for temperature). When reducing the number of features to a much smaller number, I kept it that way to remove potential noise. However, it appeared to show better result working directly on them before reduction. PCA is still running post k-means to allow for a 2D visual representation of the climate profile clusters.
- Forecast for your favorite city : as of now, the resulting favorite city is computed through scores. Future development will include weights, before switching to using a cosine similarity model instead.

## Technical Stack:
- Python
- scikit-learn (scaling, PCA, k-means)
- Streamlit (dashboard)
- Open-Meteo API
- matplotlib and seaborn for graphical representation

## How to: 

git clone https://github.com/tiphaine-h/climate_match.git
cd climate_match

### Using uv (recommended)
uv sync
source .venv/bin/activate
uv run streamlit run dashboard.py

### Or with pip
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

Locally runnable options :

- Favorite city based on preferences and 10 days forecast : python3 -m climate_match --forecast

- Favorite city based on preferences and dates : python3 -m climate_match --archive start_date end_date  
(start_date and end_date are in format "yyyy-mm-dd")

- clustering algorithm : python3 -m climate_match --clusters

- local dashboard : streamlit run dashboard.py

## Repo Structure

climate_match/  
├── /src  
│   ├── /src  
│   ├── main.py                # Entry point  
│   ├── utils.py               # Computing functions for features, scores, clustering, ...  
│   └── constants.py           # City names included in project  
├── __main__.py   
└── dashboard.py  
 
## Limits and Future Development

- The app is limited to 52 cities for now, which is already slow on first runs. Future development will include improving the cache, this time using a database to store the data longer term.
- Clustering is done only on the data of the year 2025. I would like to explore adding data for more years to see if improvement can be achieved. 
- Instead of flat scores, I will compute the resulting favorite city with weights, replace the sliders with natural language processing, and eventually use a cosine similarity model instead of scores.
