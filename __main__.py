import os
import requests
import csv
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')

if not GITHUB_API_TOKEN:
    print("Error: GitHub API token not found in .env file.")
    exit(1)

headers = {
    'Authorization': f'token {GITHUB_API_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

remaining_requests = 0
csv_file = 'contributors_data.csv'

def check_rate_limit():
    """Check the current rate limit status."""
    global remaining_requests
    url = 'https://api.github.com/rate_limit'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        rate_limit_data = response.json()
        remaining_requests = int(rate_limit_data['resources']['core']['remaining'])
        reset_time = int(rate_limit_data['resources']['core']['reset'])
        print(f"Remaining requests: {remaining_requests}")
        return reset_time
    except requests.exceptions.RequestException as e:
        print(f"Error checking rate limit: {e}")
        exit(1)

def handle_rate_limit():
    """Handle rate limit when remaining requests are exhausted."""
    reset_time = check_rate_limit()
    current_time = int(time.time())
    sleep_time = reset_time - current_time + 5
    if sleep_time > 0:
        reset_datetime = datetime.fromtimestamp(reset_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Requests finished. Sleeping until {reset_datetime} (in {sleep_time} seconds).")
        time.sleep(sleep_time)
    else:
        print("Rate limit should have reset. Continuing execution.")

def decrement_requests():
    """Decrement the remaining requests and handle rate limit if necessary."""
    global remaining_requests
    remaining_requests -= 1
    if remaining_requests <= 1:
        handle_rate_limit()
        remaining_requests = 5000

def is_bot(user_data):
    """Determine if the user is a bot."""
    return user_data.get('type', '').lower() == 'bot' or user_data.get('login', '').endswith('[bot]')

def save_to_csv(data, fieldnames):
    """Append data to the CSV file."""
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print(f"Error writing to CSV file: {e}")

def contributor_exists(username):
    """Check if the contributor is already in the CSV file."""
    if not os.path.isfile(csv_file):
        return False
    try:
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['username'] == username:
                    return True
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return False

def fetch_contributors():
    """Fetch contributors from the repository."""
    contributors = []
    page = 1
    per_page = 100

    print("Fetching contributors...")
    while True:
        url = f'https://api.github.com/repos/{owner}/{repo}/contributors'
        params = {'page': page, 'per_page': per_page}
        try:
            response = requests.get(url, headers=headers, params=params)
            decrement_requests()
            response.raise_for_status()
            contributors_page = response.json()
            if not contributors_page:
                break
            contributors.extend(contributors_page)
            print(f"Fetched page {page} of contributors.")
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching contributors: {e}")
            break
    return contributors

def fetch_user_data(username):
    """Fetch user profile data."""
    url = f'https://api.github.com/users/{username}'
    while True:
        try:
            response = requests.get(url, headers=headers)
            decrement_requests()
            response.raise_for_status()
            user_data = response.json()
            return user_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching user data for {username}: {e}")
            return {}

def fetch_commits(username, max_pages=10):
    """Fetch commits made by the user to the repository."""
    commits = []
    page = 1
    per_page = 100

    print(f"Fetching commits for {username}...")
    while page <= max_pages:
        url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        params = {'author': username, 'page': page, 'per_page': per_page}
        try:
            response = requests.get(url, headers=headers, params=params)
            decrement_requests()
            response.raise_for_status()
            commits_page = response.json()
            if not commits_page:
                break
            commits.extend(commits_page)
            print(f"Fetched page {page} of commits for {username}.")
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commits for {username}: {e}")
            break
    return commits[:100]

def fetch_pull_requests(username):
    """Fetch pull requests created by the user."""
    pull_requests = []
    page = 1
    per_page = 100

    print(f"Fetching pull requests for {username}...")
    while True:
        url = f'https://api.github.com/search/issues'
        params = {
            'q': f'repo:{owner}/{repo} is:pr author:{username}',
            'page': page,
            'per_page': per_page
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            decrement_requests()
            response.raise_for_status()
            prs_page = response.json().get('items', [])
            if not prs_page:
                break
            pull_requests.extend(prs_page)
            print(f"Fetched page {page} of pull requests for {username}.")
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching pull requests for {username}: {e}")
            break
    return pull_requests

def fetch_issues(username):
    """Fetch issues opened by the user."""
    issues = []
    page = 1
    per_page = 100

    print(f"Fetching issues for {username}...")
    while True:
        url = f'https://api.github.com/search/issues'
        params = {
            'q': f'repo:{owner}/{repo} is:issue author:{username}',
            'page': page,
            'per_page': per_page
        }
        try:
            response = requests.get(url, headers=headers, params=params)
            decrement_requests()
            response.raise_for_status()
            issues_page = response.json().get('items', [])
            if not issues_page:
                break
            issues.extend(issues_page)
            print(f"Fetched page {page} of issues for {username}.")
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error fetching issues for {username}: {e}")
            break
    return issues

def fetch_commit_stats(commit_sha):
    """Fetch stats for a specific commit."""
    url = f'https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}'
    while True:
        try:
            response = requests.get(url, headers=headers)
            decrement_requests()
            response.raise_for_status()
            commit_data = response.json()
            stats = commit_data.get('stats', {})
            return stats
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commit stats for {commit_sha}: {e}")
            return {}

def main():
    global owner, repo
    repository = input("Enter the repository (format: owner/repo, e.g., tensorflow/tensorflow): ")
    if not repository:
        repository = 'tensorflow/tensorflow'

    owner, repo = repository.split('/')

    check_rate_limit()

    contributors = fetch_contributors()
    fieldnames = [
        'username', 'email', 'bio', 'is_bot', 'total_commits',
        'total_additions', 'total_deletions', 'total_pull_requests',
        'total_issues', 'first_contribution', 'last_contribution'
    ]

    for contributor in contributors:
        username = contributor.get('login')
        if contributor_exists(username):
            print(f"Contributor {username} already exists in CSV. Skipping.")
            continue
        try:
            print(f"\nProcessing contributor: {username}")
            user_data = fetch_user_data(username)
            is_user_bot = is_bot(user_data)
            email = user_data.get('email', '')
            bio = user_data.get('bio', '')

            commits = fetch_commits(username)
            total_commits = len(commits)
            total_additions = 0
            total_deletions = 0
            timestamps = []

            for idx, commit in enumerate(commits, start=1):
                commit_sha = commit.get('sha')
                print(f"Processing commit {idx}/{total_commits} for {username}: {commit_sha}")
                commit_stats = fetch_commit_stats(commit_sha)
                total_additions += commit_stats.get('additions', 0)
                total_deletions += commit_stats.get('deletions', 0)
                commit_date = commit.get('commit', {}).get('author', {}).get('date')
                if commit_date:
                    timestamps.append(datetime.strptime(commit_date, '%Y-%m-%dT%H:%M:%SZ'))

            pull_requests = fetch_pull_requests(username)
            total_pull_requests = len(pull_requests)

            issues = fetch_issues(username)
            total_issues = len(issues)

            if timestamps:
                first_contribution = min(timestamps).strftime('%Y-%m-%d %H:%M:%S')
                last_contribution = max(timestamps).strftime('%Y-%m-%d %H:%M:%S')
            else:
                first_contribution = ''
                last_contribution = ''

            data = {
                'username': username,
                'email': email,
                'bio': bio,
                'is_bot': is_user_bot,
                'total_commits': total_commits,
                'total_additions': total_additions,
                'total_deletions': total_deletions,
                'total_pull_requests': total_pull_requests,
                'total_issues': total_issues,
                'first_contribution': first_contribution,
                'last_contribution': last_contribution
            }

            save_to_csv(data, fieldnames)
            print(f"Data saved for contributor: {username}")

        except Exception as e:
            print(f"An error occurred while processing contributor {username}: {e}")
            continue

if __name__ == "__main__":
    main()
