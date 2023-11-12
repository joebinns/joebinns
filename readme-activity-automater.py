import argparse
import requests
import datetime

class RepoInfo:
    def __init__(self, repo):
        self.fullName = repo['full_name']
        self.url = repo['html_url']

class CommitInfo:
    def __init__(self, commit, repoInfo):
        self.repo = repoInfo
        self.url = commit['html_url']
        self.message = commit['commit']['message']
        self.author = commit['commit']['author']['name']
        self.dateTime = datetime.datetime.strptime(commit['commit']['author']['date'], "%Y-%m-%dT%H:%M:%SZ") # Convert ISO8601 string to datetime

def GetDynamicMarkdown(commit):
    # Format commit message
    # TODO: Strip new lines from commit message (and remove anything after them)

    # Set preposition based on commit message
    preposition = 'in'
    if ('add' in commit.message.lower()):
        preposition = 'to'
    elif ('remove' in commit.message.lower()):
        preposition = 'from'
    
    # Format datetime
    ## TODO: If date time was less than 24 hours ago, then use 'x hours ago' instead
    dateTimeStr = commit.dateTime.strftime('%A %b %d at %H:%M GMT')

    return "- [{commitMessage}]({commitUrl}) {preposition} [*{repoFullName}*]({repoUrl}) — {commitDate}".format(commitMessage=commit.message, commitUrl=commit.url, preposition=preposition, repoFullName=commit.repo.fullName, repoUrl=commit.repo.url, commitDate=dateTimeStr)

MAX_ENTRIES = 3

parser = argparse.ArgumentParser()
parser.add_argument('token', type=str)
args = parser.parse_args()

username = 'joebinns'
token = args.token
repos = requests.get('https://api.github.com/users/{user}/repos?sort=pushed?per_page={maxEntries}'.format(user=username, maxEntries=MAX_ENTRIES*MAX_ENTRIES), auth=(username,token)).json()

allCommits = []
for i in range(min(len(repos), MAX_ENTRIES)):
    repo = RepoInfo(repos[i])
    commits = requests.get('https://api.github.com/repos/{repoFullName}/commits?per_page={maxEntries}'.format(user=username, repoFullName=repo.fullName, maxEntries=MAX_ENTRIES), auth=(username,token)).json()

    for j in range(min(len(commits), MAX_ENTRIES)):
        commit = CommitInfo(commits[j], repo)
        allCommits.append(commit)
    
def GetDateTime(commit):
    return commit.dateTime

activitySection = []
allCommits.sort(key=GetDateTime, reverse=True)
for i in range(min(len(allCommits), MAX_ENTRIES)):
    commit = allCommits[i]
    activitySection.append(GetDynamicMarkdown(commit))

# Read the README, identify the dynamic part
lineNumsInActivitySection = []
with open('README.md', 'r') as file:
    inActivitySection = False
    for lineNum, line in enumerate(file):
        if ('<!--activity_section_end-->' in line):
            break
        if (inActivitySection):
            lineNumsInActivitySection.append(lineNum)
        if ('<!--activity_section_start-->' in line):
            inActivitySection = True
    file.close()

# Edit the dynamic part of the README      
activitySectionIndex = 0
with open('README.md', 'w') as file:
    for lineNum, line in enumerate(file):
        if (lineNum not in lineNumsInActivitySection):
            # Keep the lines that are not in the activity section
            file.write(line) 
        else:
            # Write the activity section
            for activitySectionLine in activitySection:
                file.write(activitySectionLine) 
    file.close()