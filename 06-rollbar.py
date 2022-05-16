import os
import pickle

import pandas as pd

# new imports
import rollbar  # pip install rollbar
from dotenv import find_dotenv, load_dotenv  # pip install python-dotenv
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import LabelBinarizer, StandardScaler
from sklearn_pandas import DataFrameMapper

# find the dotenv file if it lives beside this script
load_dotenv(find_dotenv())

# load the key-value secret
ROLLBAR = os.getenv("ROLLBAR")
rollbar.init(ROLLBAR)

df = pd.read_csv("data/basketball.csv", parse_dates=[3])
df = df.sort_values(["name", "date"]).reset_index(drop=True)
df["points_1"] = df.groupby("name")["points"].shift(1)
df["points_2"] = df.groupby("name")["points"].shift(2)
df = df.dropna(subset=["points_1", "points_2"])

target = "points"
y = df[target]
X = df[["position", "points_1", "points_2"]]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.10, random_state=42, shuffle=False
)

mapper = DataFrameMapper(
    [
        (["position"], [SimpleImputer(strategy="most_frequent"), LabelBinarizer()]),
        (["points_1"], [SimpleImputer(), StandardScaler()]),
        (["points_2"], [SimpleImputer(), StandardScaler()]),
    ],
    df_out=True,
)

model = LinearRegression()

pipe = make_pipeline(mapper, model)
pipe.fit(X_train, y_train)
score = round(pipe.score(X_train, y_train), 2)

# sound the alarm if below
threshold = 0.45
if score < threshold:
    rollbar.report_message(
        f"score ({score}) is below acceptable threshold ({threshold})"
    )

with open("pickles/pipe.pkl", "wb") as f:
    pickle.dump(pipe, f)
