# %%
import numpy as np
import pandas as pd
import dtale # for visualize
import plotly.express as px
import matplotlib.pyplot as plt
from tqdm import tqdm
# sklearn
from sklearn.preprocessing import OneHotEncoder

tqdm.pandas()

# %% [markdown]
# # Read data
# First, read data in `.jsonl` file format as a pandas data frame
# Then store the dataframe in `.parquet` format for easy access later

# %% just do this one time
# df = pd.read_json("../fulldata/kiva_2023-08-10T17-57-12.jsonl", lines=True)
# df = pd.json_normalize(df["loan"])
# df.to_parquet("../fulldata/kiva_2023-08-10T17-57-12.parquet")

# %%
df = pd.read_parquet("../fulldata/kiva_2023-08-10T17-57-12.parquet")
# 24 rows are all-na, don't know why
df.dropna(axis=0, how="all", inplace=True)


# %% create some columns
class COL:
    LOAN_AMOUNT = "loanAmount"
    FUNDED_AMOUNT = "loanFundraisingInfo.fundedAmount"
    RAISED_DATE = "raisedDate"
    POSTED_DATE = "fundraisingDate"
    SPEED = "collection_speed"
    TAGS = "tags"


df[
    [
        COL.LOAN_AMOUNT,
        COL.FUNDED_AMOUNT,
        COL.RAISED_DATE,
        COL.POSTED_DATE,
        COL.TAGS,
        "disbursalDate",
    ]
].head()

# %% convert these columns to
df[COL.LOAN_AMOUNT] = df[COL.LOAN_AMOUNT].astype(float)
df[COL.FUNDED_AMOUNT] = df[COL.FUNDED_AMOUNT].astype(float)
df[COL.RAISED_DATE] = pd.to_datetime(df[COL.RAISED_DATE])
df[COL.POSTED_DATE] = pd.to_datetime(df[COL.POSTED_DATE])

# %% [markdown]
# We keep only the success loans

# %% success rate?
success = df[COL.LOAN_AMOUNT] == df[COL.FUNDED_AMOUNT]
success = success.value_counts()
success[True] / (success[True] + success[False])

# %%
# keep success only
df = df[success]

# %% na
# mask = df[COL.TAGS].isna()
# df.loc[mask, COL.TAGS] = [np.ndarray([], dtype=object) for _ in range(mask.sum())]
# df.loc[df[COL.TAGS].isna(), COL.TAGS] = np.ndarray([], dtype=object)

# %% [markdown] 
# One-hot encoding tags

#%%
# all unique tags
all_tags = []
for tag_list in df[COL.TAGS]:
    if tag_list is None:
        continue
    for tag in tag_list:
        all_tags.append(tag)
all_tags = set(all_tags)
all_tags = np.array(list(all_tags), dtype="str")

enc = OneHotEncoder()
enc.fit(all_tags.reshape(-1, 1))

# %%
tag_df = pd.DataFrame(columns=enc.get_feature_names_out(["tag"]), index=df.index)
tag_df = pd.concat([df[COL.TAGS], tag_df], axis=1)
tag_df.head()

def transform(row):
    for atags in row[COL.TAGS]:
        if atags in all_tags:
            row[f"tag_{atags}"] = 1
            break
    return row

tag_df = tag_df.progress_apply(transform, axis=1)
tag_df.fillna(0, inplace=True)
tag_df.drop(columns=[COL.TAGS], inplace=True)

# %%
df = pd.concat([df, tag_df], axis=1)
# dtale.show(df.filter(regex="tag.*", axis=1).head())

# %% checkpoint
df.to_parquet("checkpoint.parquet")

# %% load checkpoint
# df = pd.read_parquet('checkpoint.parquet')

# %% [markdown]
# ## Tag performance
# %% Calculate the amount of money collected per day
df["funding_duration"] = df[COL.RAISED_DATE] - df[COL.POSTED_DATE]
df["funding_duration_days"] = df["funding_duration"].dt.total_seconds() / (24 * 60 * 60)
df[COL.SPEED] = df[COL.FUNDED_AMOUNT] / df["funding_duration_days"]
df[COL.SPEED]

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
fig = px.bar(tags_performances.dropna().sort_values("mean"), y="tag", x="mean", text_auto=True)
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()
# %%
