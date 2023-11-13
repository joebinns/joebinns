import argparse
import requests
import datetime

class RepoInfo:
    def __init__(self, repo):
        self.name = repo['name']
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
    dateTimeStr = ''
    secondsSinceCommit = (datetime.datetime.now() - commit.dateTime).total_seconds()
    minutesSinceCommit = secondsSinceCommit / 60
    hoursSinceCommit = minutesSinceCommit / 60
    daysSinceCommit = hoursSinceCommit / 24
    if (hoursSinceCommit < 1):
        minutes = max(round(minutesSinceCommit), 1)
        plural = ''
        if (minutes > 1):
            plural = 's'
        dateTimeStr = commit.dateTime.strftime('{minutes} minute{plural} ago'.format(minutes=minutes, plural=plural))
    if (daysSinceCommit < 1):
        hours = min(round(hoursSinceCommit), 23)
        plural = ''
        if (hours > 1):
            plural = 's'
        dateTimeStr = commit.dateTime.strftime('{hours} hour{plural} ago'.format(hours=hours, plural=plural))
    else:
        dateTimeStr = commit.dateTime.strftime('%A, %b %d at %H:%M GMT')

    return "- [{commitMessage}]({commitUrl}) {preposition} [*{repoName}*]({repoUrl}) — {commitDate}\n".format(commitMessage=commit.message, commitUrl=commit.url, preposition=preposition, repoName=commit.repo.name, repoUrl=commit.repo.url, commitDate=dateTimeStr)

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
    commits = requests.get('https://api.github.com/repos/{user}/{repoName}/commits?per_page={maxEntries}'.format(user=username, repoName=repo.name, maxEntries=MAX_ENTRIES), auth=(username,token)).json()

    for j in range(min(len(commits), MAX_ENTRIES)):
        commit = CommitInfo(commits[j], repo)
        allCommits.append(commit)
    
def GetDateTime(commit):
    return commit.dateTime

dynamicSection = []
allCommits.sort(key=GetDateTime, reverse=True)
for i in range(min(len(allCommits), MAX_ENTRIES)):
    commit = allCommits[i]
    dynamicSection.append(GetDynamicMarkdown(commit))

# Read the README, identify the dynamic part
text = []
with open('README.md', 'r') as fileReadOnly:
    inDynamicSection = False
    for lineNum, staticLine in enumerate(fileReadOnly):
        if ('<!--activity_section_end-->' in staticLine):
            inDynamicSection = False
        if (not inDynamicSection):
            text.append(staticLine)
        if ('<!--activity_section_start-->' in staticLine):
            for dynamicLine in dynamicSection:
                text.append(dynamicLine)
            inDynamicSection = True
    fileReadOnly.close()

# Edit the dynamic part of the README
with open('README.md', 'w') as fileWriteOnly:
    fileWriteOnly.writelines(text)
    fileWriteOnly.close()