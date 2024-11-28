import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('contributors_data_cleaned.csv')

print("=== Data Summary ===")
total_contributors = len(df)
print(f"Total number of contributors: {total_contributors}")

label_counts = df['label'].value_counts()
print("\nNumber of contributors by label:")
print(label_counts)
print(f"\nPercentage of active contributors: {label_counts[1] / total_contributors * 100:.2f}%")
print(f"Percentage of inactive contributors: {label_counts[0] / total_contributors * 100:.2f}%")

key_features = [
    'total_commits', 'total_additions', 'total_deletions',
    'total_pull_requests', 'total_issues', 'avg_commits_per_day',
    'avg_additions_per_commit', 'avg_deletions_per_commit',
    'additions_deletions_ratio', 'code_changes_per_commit'
]

print("\n=== Basic Statistics of Key Features ===")
print(df[key_features].describe())

def plot_label_distribution(label_counts):
    plt.figure(figsize=(8, 6))
    label_counts.plot(kind='bar', color=['skyblue', 'salmon'])
    plt.title('Number of Contributors by Label')
    plt.xlabel('Label')
    plt.ylabel('Number of Contributors')
    plt.xticks([0, 1], ['Inactive', 'Active'], rotation=0)
    plt.show()

plot_label_distribution(label_counts)
