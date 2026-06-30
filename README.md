# Finding your preferred city


## Use Case 1: 
Based on inputs from the user (preferred temperature, rain, pollen allergy, ...), determines the best city for you,

A: over the next 10 days

or

B: over a chosen period of time in the past

## Use Case 2:
Cluster cities by climate profiles.

## Use Case 3:
Dashboard for user to have access to all other use cases.


## How to 
Depending on use case : 

1A: 

python3 -m climate_match --forecast

1B:

python3 -m climate_match --archive start_date end_date
start_date and end_date are in format "yyyy-mm-dd"


2:

python3 -m climate_match --clusters

3 : from inside the project :
streamlit run dashboard.py 



