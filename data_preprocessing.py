import pandas as pd
import numpy as np
from datetime import datetime

df = pd.read_csv('contributors_data.csv')
df.drop(columns=['email', 'bio', 'is_bot'], inplace=True)

key_metrics = ['total_commits', 'total_additions', 'total_deletions',
               'total_pull_requests', 'total_issues']
df = df[~(df[key_metrics] == 0).all(axis=1)]

df['first_contribution'] = pd.to_datetime(df['first_contribution'])
df['last_contribution'] = pd.to_datetime(df['last_contribution'])

df['contribution_span_days'] = (df['last_contribution'] - df['first_contribution']).dt.days

df['contribution_span_days'].replace(0, 1, inplace=True)

df['avg_commits_per_day'] = df['total_commits'] / df['contribution_span_days']

df['avg_commits_per_day'].replace([np.inf, -np.inf], np.nan, inplace=True)

df.dropna(subset=['avg_commits_per_day'], inplace=True)

df['avg_commits_per_day'] = pd.to_numeric(df['avg_commits_per_day'], errors='coerce')

df['label'] = (df['avg_commits_per_day'] > 1).astype(int)

df['avg_additions_per_commit'] = df['total_additions'] / df['total_commits']
df['avg_deletions_per_commit'] = df['total_deletions'] / df['total_commits']

df['additions_deletions_ratio'] = df['total_additions'] / (df['total_deletions'] + 1)

df['code_changes'] = df['total_additions'] + df['total_deletions']
df['code_changes_per_commit'] = df['code_changes'] / df['total_commits']

df.to_csv('contributors_data_cleaned.csv', index=False)

print("Data cleaning and enrichment complete. Cleaned data saved to 'contributors_data_cleaned.csv'.")
