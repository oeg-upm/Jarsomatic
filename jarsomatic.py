from flask import Flask, request
import ConfigParser
#import json
#import simplejson as json
import rson as json
import re
from subprocess import call
import os.path
from config import app_home
from github import Github



app = Flask(__name__)
target_files = ['.jar', '.csv']
#app_home = ''
config_file = 'jarsomatic.cfg'
config = ConfigParser.ConfigParser()
if not os.path.isfile(os.path.join(app_home, config_file)):
    print "\n*** The file: "+config_file+" is not here or is not accessible ***\n"
config.read(os.path.join(app_home, config_file))
jar_location = config.get('JAR', 'location')
jar_command = config.get('JAR', 'command')
target_files_str = config.get('DEFAULT', 'watch')
target_files = [f.strip().strip("'").strip('"') for f in target_files_str.split(",")]
github_token = config.get('GITHUB', 'token')
print "location: "+jar_location
print "command: "+jar_command
print "target_files_str: "+target_files_str

for f in target_files:
    print "file: "+f

g = Github(github_token)
try:
    g.get_user().login
except Exception as e:
    print "Github token is invalid"


@app.route("/testp", methods=["GET"])
def test_positive():
    d = os.path.join(app_home, "webhook_example_positive.txt")
    f = open(d)
    file_content = f.read()
    return webhook_handler(file_content)


@app.route("/testn", methods=["GET"])
def test_negative():
    d = os.path.join(app_home, "webhook_example_negative.txt")
    f = open(d)
    file_content = f.read()
    return webhook_handler(file_content)


@app.route("/webhook", methods=["POST"])
def webhook():
    values = request.values['payload']
    return webhook_handler(values)


def webhook_handler(payload_text):
    values = payload_text
    try:
        values = json.loads(str(values))
        payload = values['payload']
    except Exception as e:
        print "exception: "+str(e)
        return "exception occurred"
    changed_files = get_changed_files_from_payload(payload)
    return run_if_target(changed_files)


def get_changed_files_from_commit(commit):
    return commit["added"] + commit["modified"]


def get_changed_files_from_payload(payload):
    commits = payload['commits']
    changed_files = []
    for c in commits:
        changed_files += get_changed_files_from_commit(c)
    return changed_files


def create_pull_request(repo_str):
    global g
    username = g.get_user().login
    repo = g.get_repo(repo_str)
    title = 'Jarsomatic'
    body = 'Jarsomatic pull request'
    try:
        repo.create_pull(head=username+':master', base='master', title=title, body=body)
        return True
    except Exception as e:
        print "cannot create pull request, error:  <%s>"%(str(e))
        return False


def fork_repo(repo_str):
    global g
    u = g.get_user()
    repo = g.get_repo(repo_str)
    try:
        u.create_fork(repo)
        return True
    except Exception as e:
        print "error forking the repo %s, <%s>"%(repo_str, str(e))


def run_if_target(changed_files):
    jarsomatic_branch = "jarsomatic"
    print "found %d files"%(len(changed_files))
    found = False
    for f in changed_files:
        for t in target_files:
            if t == f:
                found = True
                break
        if found:
            break
    if found:
        print "Rerun"
        comm = "cd "+jar_location+"; "  # Go to the project location
        comm += "git pull; "  # get latest update
        comm += jar_command  # run the command and generate the output
        call(comm, shell=True)
        return "Rerun: "+"\ncd "+jar_location+";\n"+jar_command
    else:
        print "Ignore"
        return "Ignore"


# source: http://stackoverflow.com/questions/21495598/simplejson-encoding-issue-illegal-character
def remove_control_chars(s):
    control_chars = ''.join(map(unichr, range(0, 32) + range(127, 160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', s)


@app.route("/")
def hello():
    return "Welcome to Jarsomatic" + "<br><br><a href='testp'>Test Positive</a>" + \
           "<br><br><a href='testn'>Test Negative</a>"


if __name__ == "__main__":
    app.run()

