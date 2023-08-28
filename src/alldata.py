# %%
import numpy as np
import pandas as pd
import dtale  # for visualize
from pathlib import Path
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
originfile = Path(__file__).resolve().parent / ".." / "fulldata" / "kiva_2023-08-10T17-57-12.parquet"
df = pd.read_parquet(str(originfile))
# 24 rows are all-na, don't know why
df.dropna(axis=0, how="all", inplace=True)


# %% keeps only some columns, for speed up process
class COL:
    LOAN_AMOUNT = "loanAmount"
    FUNDED_AMOUNT = "loanFundraisingInfo.fundedAmount"
    RAISED_DATE = "raisedDate"
    POSTED_DATE = "fundraisingDate"
    TAGS = "tags"
    COUNTRY_NAME = "geocode.country.name"
    COUNTRY = "geocode.country.isoCode"
    REGION = "geocode.country.region"
    STATE = "geocode.state"
    LAT = "geocode.latitude"
    LONG = "geocode.longitude"

    SPEED = "collection_speed"

#%%
df = df[
    [
        COL.LOAN_AMOUNT,
        COL.FUNDED_AMOUNT,
        COL.RAISED_DATE,
        COL.POSTED_DATE,
        "disbursalDate",
        COL.COUNTRY_NAME,
        COL.COUNTRY,
        COL.STATE,
        COL.REGION,
        COL.LAT,
        COL.LONG,
        COL.TAGS,
    ]
]

df.head()

# %% convert these columns to
df[COL.LOAN_AMOUNT] = df[COL.LOAN_AMOUNT].astype(float)
df[COL.FUNDED_AMOUNT] = df[COL.FUNDED_AMOUNT].astype(float)
df[COL.RAISED_DATE] = pd.to_datetime(df[COL.RAISED_DATE])
df[COL.POSTED_DATE] = pd.to_datetime(df[COL.POSTED_DATE])
df[COL.COUNTRY] = df[COL.COUNTRY].astype("category")
df[COL.COUNTRY_NAME] = df[COL.COUNTRY_NAME].astype("category")
df[COL.REGION] = df[COL.REGION].astype("category")
df[COL.STATE] = df[COL.STATE].astype("category")


# %% [markdown]
# We keep only the success loans

# %% success rate?
success = df[COL.LOAN_AMOUNT] == df[COL.FUNDED_AMOUNT]
counts = success.value_counts()
counts[True] / (counts[True] + counts[False])

# %%
# keep success only
df = df[success]

# %% na
df.isna().sum()

# %% [markdown]
# loanAmount                          0
# loanFundraisingInfo.fundedAmount    0
# raisedDate                          2
# fundraisingDate                     0
# tags                                0
# disbursalDate                       4
# dtype: int64

# it would be ok to remove mirror na
# %%
df.dropna(inplace=True)

# %% [markdown]
# One-hot encoding tags

# %%
# all unique tags
all_tags = []
for tag_list in df[COL.TAGS]:
    for tag in tag_list:
        all_tags.append(tag)
all_tags = set(all_tags)
all_tags = np.array(list(all_tags), dtype="str")

enc = OneHotEncoder()
enc.fit(all_tags.reshape(-1, 1))
enc.categories_

# %%
tag_df = pd.DataFrame(columns=enc.get_feature_names_out(["tag"]), index=df.index, dtype=int)
tag_df = pd.concat([df[COL.TAGS], tag_df], axis=1)
tag_df.head()

all_tags = set(all_tags)


def transform(row):
    for atags in row[COL.TAGS]:
        if atags in all_tags:
            row[f"tag_{atags}"] = 1
            break
    return row


tag_df = tag_df.progress_apply(transform, axis=1)
tag_df.dropna(axis=1, how="all", inplace=True)
tag_df.fillna(0, inplace=True)
tag_df.drop(columns=[COL.TAGS], inplace=True)
tag_df = tag_df.astype(int)

# Note that we could use
# pd.get_dummies(df[COL.TAGS].apply(pd.Series).stack()).groupby(level=2).sum()
# or
# mb = sklearn.preprocessing.MultiLabelBinarizer()

# %%
df = pd.concat([df, tag_df], axis=1)
# dtale.show(df.filter(regex="tag.*", axis=1).head())

# %% checkpoint
checkpoint =Path(__file__).resolve().parent / ".." / "fulldata" / "checkpoint.parquet"
df.to_parquet(str(checkpoint))

# %% load checkpoint
checkpoint = Path(__file__).resolve().parent / ".." / "fulldata" / "checkpoint.parquet"
df = pd.read_parquet(str(checkpoint))

# %% [markdown]
# ## Tag performance
# %% Calculate the amount of money collected per day
df["funding_duration"] = df[COL.RAISED_DATE] - df[COL.POSTED_DATE]
df["funding_duration_days"] = df["funding_duration"].dt.total_seconds() / (24 * 60 * 60)
df[COL.SPEED] = df[COL.FUNDED_AMOUNT] / df["funding_duration_days"]
df.head()

# %%
tag_columns = [a for a in df.columns if a.startswith("tag_")]


def get_tag_performance(_df: pd.DataFrame, num_tag: int = 10) -> pd.DataFrame:
    """get speed performance by tags, keep only first `num_tag`"""
    tags_performances = []

    for atag in tag_columns:
        mean = _df[_df[atag] == 1][COL.SPEED].mean()
        std = _df[_df[atag] == 1][COL.SPEED].std()
        tags_performances.append({"tag": atag, "mean": mean, "std": std})

    tags_performances = pd.DataFrame(tags_performances)
    tags_performances.dropna(subset=["mean"], inplace=True)
    tags_performances.fillna(0, inplace=True)
    tags_performances.sort_values("mean", inplace=True, ascending=False)
    tags_performances.set_index("tag", inplace=True)
    return tags_performances.head(num_tag)


# fig = px.bar(tags_performances, y="tag", x="mean", error_x="std", text_auto=True)
fig = px.bar(get_tag_performance(df), y="mean", text_auto=True)
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()

# %% kedall correlation between speed and tags
corr = df[tag_columns].corrwith(df[COL.SPEED], method="kendall", drop=True)
fig = px.bar(corr.sort_values(ascending=False), text_auto=True)
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()

# %% [markdown]
# Country Analysis
# First start with Vietname, because why not?
# %%
"""convert coutry code to country name"""
code_to_name = df[[COL.COUNTRY_NAME, COL.COUNTRY]].drop_duplicates()
code_to_name.set_index(COL.COUNTRY, inplace=True)
code_to_name = code_to_name.to_dict()[COL.COUNTRY_NAME]
assert code_to_name["VN"] == "Vietnam"

# %%
country_code = 'VN'
vn_df = df[df[COL.COUNTRY] == country_code]
fig = px.bar(get_tag_performance(vn_df), y="mean", text_auto=True, title=f"Mean Collection Speed for {code_to_name[country_code]}")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()

# %%
country_code = 'KE'
vn_df = df[df[COL.COUNTRY] == country_code]
fig = px.bar(get_tag_performance(vn_df), y="mean", text_auto=True, title=f"Mean Collection Speed for {code_to_name[country_code]}")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()

# %%
country_code = 'KH'
vn_df = df[df[COL.COUNTRY] == country_code]
fig = px.bar(get_tag_performance(vn_df), y="mean", text_auto=True, title=f"Mean Collection Speed for {code_to_name[country_code]}")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()
# %%
country_code = 'SV'
vn_df = df[df[COL.COUNTRY] == country_code]
fig = px.bar(get_tag_performance(vn_df), y="mean", text_auto=True, title=f"Mean Collection Speed for {code_to_name[country_code]}")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.show()

# %% [markdown]
# ## Influence of the number of tags

# %%
df['tag_count'] = df[COL.TAGS].apply(len)
tag_count = df['tag_count'].value_counts()
tag_count_mean = df['tag_count'].mean()
tag_count_std = df['tag_count'].std()
fig = px.bar(tag_count, text_auto=True, title="Distribution of Number of Tags per Project")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.update_xaxes(tickmode='linear')
fig.add_vline(x=tag_count_mean)
fig.show()
# %%
# Number of above-average speed collection vs number of tags

speed_mean = df[COL.SPEED].mean()
above_average = df[df[COL.SPEED] >= speed_mean]

#%%
tag_count = above_average[COL.TAGS].apply(len).value_counts()
tag_count_mean = df['tag_count'].mean()
tag_count_std = df['tag_count'].std()
fig = px.bar(tag_count, text_auto=True, title="Effectiveness of Tags on Collection Speed")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.update_xaxes(tickmode='linear')
fig.add_vline(x=tag_count_mean)
fig.show()

# %%

from itertools import combinations

tag_columns = [a for a in df.columns if a.startswith("tag_")]
tag2_columns = list(combinations(tag_columns, 2))

#%%

for apair in tag2_columns:
    df[apair] = df[apair[0]] + df[apair[1]]

#%%
tag2_performances = []

for apair in tag2_columns:
    mean = above_average[above_average[apair] == 1][COL.SPEED].mean()
    std = above_average[above_average[apair] == 1][COL.SPEED].std()
    tag2_performances.append({"tag": apair, "mean": mean, "std": std})

#%%
tag2_count = above_average[tag2_columns].sum()
tag2_count.sort_values(ascending=False, inplace=True)
tag2_count = pd.DataFrame(tag2_count.head(20).rename('project count'))
# tag_count_mean = df['tag_count'].mean()
# tag_count_std = df['tag_count'].std()
fig = px.bar(tag2_count, text_auto=True, title="Effectiveness of Tags on Collection Speed")
fig.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
fig.update_xaxes(tickmode='linear')
# fig.add_vline(x=tag_count_mean)
fig.show()
# %%
