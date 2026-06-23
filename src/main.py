import sys
import argparse
import requests
import pandas as pd
from . import utils
from .constants import city_names


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
        print("todo")

if __name__ == "__main__":
    sys.exit(main())
