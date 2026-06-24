import sys
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
from climate_match.src.constants import city_names
from climate_match.src import utils


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
            score_temperature = utils.compute_score(pref_temp, "forecast")
        else:
            score_temperature = utils.compute_score(pref_temp, "archive", args.archive[0], args.archive[1])
        scores = dict(zip(city_names, score_temperature))
        print("Your preferred city is : ", min(scores, key=scores.get))

    if args.dashboard:
        weather = utils.get_yearly_weather(city_names)
        weather_reduced = utils.reduce_PCA(weather)

        weather_with_clusters = utils.find_clusters(weather_reduced)
        print(weather_with_clusters)

        sns.scatterplot(data=weather_with_clusters,
                        x="PC1",
                        y="PC2",
                        hue="cluster",
                        palette="tab10")
        plt.show()

if __name__ == "__main__":
    sys.exit(main())
