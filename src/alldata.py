# %%
import numpy as np
import pandas as pd
import plotly.express as px
import dtale
import matplotlib.pyplot as plt

df = pd.read_json("../fulldata/kiva_2023-08-10T17-57-12.jsonl", lines=True)
df = pd.json_normalize(df["loan"])
# %%
df["raisedDate"] = pd.to_datetime(df["raisedDate"])
df["fundraisingDate"] = pd.to_datetime(df["fundraisingDate"])
df["loanFundraisingInfo.fundedAmount"] = df["loanFundraisingInfo.fundedAmount"].astype(float)
df[
    [
        "loanAmount",
        "loanFundraisingInfo.fundedAmount",
        "raisedDate",
        "fundraisingDate",
        "plannedExpirationDate",
        "disbursalDate",
    ]
]


# %% create some columns
class COL:
    LOAN_AMOUNT = "loanAmount"
    FUNDED_AMOUNT = "loanFundraisingInfo.fundedAmount"
    RAISED_DATE = "raisedDate"
    POSTED_DATE = "fundraisingDate"
    SPEED = "collection_speed"
    TAGS = "tags"


# %% Calculate the amount of money collected per day
df["funding_duration"] = df[COL.RAISED_DATE] - df[COL.POSTED_DATE]
df["funding_duration_days"] = df["funding_duration"].dt.total_seconds() / (24 * 60 * 60)
df[COL.SPEED] = df[COL.FUNDED_AMOUNT] / df["funding_duration_days"]
df[COL.SPEED]

# %% One-hot encoding tags
from sklearn.preprocessing import OneHotEncoder

# all unique tags
all_tags = set(tag for tag_list in df[COL.TAGS] for tag in tag_list)
all_tags = np.array(list(all_tags), dtype="str")
enc = OneHotEncoder()
enc.fit(all_tags.reshape(-1, 1))

# %%
tag_df = pd.DataFrame(columns=enc.get_feature_names_out(["tag"]), index=df.index)
df = pd.concat([df, tag_df], axis=1)


# %%
def transform(row):
    count = 0
    for atags in all_tags:
        if atags in row[COL.TAGS]:
            row[f"tag_{atags}"] = 1
            count += 1
        else:
            row[f"tag_{atags}"] = 0

    assert count == len(row[COL.TAGS]), row[COL.TAGS]
    return row


df = df.apply(transform, axis=1)
# %%
dtale.show(df.filter(regex="tag.*", axis=1).head())

# %% Tag performance
tags_performances = []

for atag in all_tags:
    mean = df[df[f"tag_{atag}"] == 1][COL.SPEED].mean()
    std = df[df[f"tag_{atag}"] == 1][COL.SPEED].std()
    tags_performances.append({"tag": f"tag_{atag}", "mean": mean, "std": std})


tags_performances = pd.DataFrame(tags_performances)

# %%
fig = px.bar(tags_performances.sort_values("mean"), y="tag", x="mean", error_x="std", text_auto=True)
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()
# %%
