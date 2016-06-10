import ConfigParser

from flask import Flask, request, redirect, url_for, render_template

import rson as json
import re
from subprocess import call
import os.path
import random
import string
from github import Github
import logging
import time

from datetime import datetime

from models import Repo
from mongoengine import connect

current_repo = None
current_user = None
repo_name = None  # set in get_repo_from_payload
repo_rel_dir = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(9)])
app = Flask(__name__)
app_home = os.path.dirname(os.path.abspath(__file__))
log_filename = 'jarsomatic.log'
append_comm = " >> "+os.path.join(app_home, log_filename)
config_file = 'jarsomatic.cfg'
config = ConfigParser.ConfigParser()
if not os.path.isfile(os.path.join(app_home, config_file)):
    print "\n*** The file: "+config_file+" is not here or is not accessible ***\n"
config.read(os.path.join(app_home, config_file))
github_token = config.get('GITHUB', 'token')
temp_dir = config.get('DEFAULT', 'tmp')
g = Github(github_token)
logging.basicConfig(filename=os.path.join(app_home, log_filename), format='%(asctime)s: %(message)s',
                    level=logging.DEBUG)
connect("jarsomatic")


def dolog(msg):
    logging.critical(msg)
    # print msg
try:
    u = g.get_user().login
    dolog("user %s, token %s"%(u, github_token))
except Exception as e:
    dolog("Github token is invalid")


@app.route("/")
def hello():
    return render_template('home.html', repos=[r.json() for r in Repo.objects.all().order_by('-started_at')])


@app.route("/pull")
def pull_new_version():
    comm = "cd %s; git pull --no-edit -Xtheirs origin master "%(app_home)
    comm += append_comm
    dolog("will update Jarsomatic")
    dolog("Jarsomatic update command: "+comm)
    call(comm, shell=True)
    return redirect(url_for('getlog'))


@app.route("/clearlog")
def clearlog():
    f = open(os.path.join(app_home, log_filename), "w")
    f.close()
    return redirect(url_for('getlog'))


@app.route("/getlog")
def getlog():
    s = []
    with open(os.path.join(app_home, log_filename), "r") as f:
        for idx, l in enumerate(f):
            s.append("<tr><td>%d</td><td>%s</td></tr>" % (idx, l))
    return """<html><head>
                    <style>
                            table, th, td {
                            border: 1px solid black;
                            border-collapse: collapse;
                        }
                        th, td {
                            padding: 15px;
                        }
                    </style>
                    </head>
                    <body>
                        <br><br>
                        <a href="/">Home</a><br><br>
                        <a href="clearlog">clear logs</a><br>
                        <table>

                        <tr>
                            <td>Line</td>
                            <td>Log</td>
                        </tr>
                        %s
                        </table></body>
                    </html>""" % "".join(s[::-1])


@app.route("/testp", methods=["GET"])
def test_positive():
    d = os.path.join(app_home, "webhook_example_positive_nopayload.txt")
    f = open(d)
    file_content = f.read()
    file_content = json.loads(file_content)
    return webhook_handler(file_content)


@app.route("/testn", methods=["GET"])
def test_negative():
    d = os.path.join(app_home, "webhook_example_negative_nopayload.txt")
    f = open(d)
    file_content = f.read()
    file_content = json.loads(file_content)
    return webhook_handler(file_content)


@app.route("/webhook", methods=["POST"])
def webhook():
    global repo_rel_dir
    repo_rel_dir = ''.join([random.choice(string.ascii_letters+string.digits) for _ in range(9)])
    try:
        dolog("json: %s"%(str(request.json)))
    except Exception as e:
        dolog("exception: "+str(e))
    values = request.json
    if values["ref"].strip() == "refs/heads/gh-pages":
        return "gh-pages push will be ignored"
    try:
        pid = os.fork()
        if pid == 0:
            time.sleep(10)
            return webhook_handler(values)
        else:
            return "Process started to do the work"
    except Exception as e:
        return "Error forking the process: <%s>"%(str(e))


def webhook_handler(payload):
    try:
        print "payload %s"%(str(payload))
    except Exception as e:
        dolog("exception: "+str(e))
        return "exception occurred \n"
    dolog("will get changed files from payload")
    changed_files = get_changed_files_from_payload(payload)
    dolog("will get the repo from payload")
    repo_str = get_repo_from_payload(payload)
    dolog("will proceed to the workflow")
    return workflow(changed_files, repo_str)


def get_changed_files_from_commit(commit):
    return commit["added"] + commit["modified"]


def get_changed_files_from_payload(payload):
    global current_user
    current_user = payload["head_commit"]["committer"]["name"]
    commits = payload['commits']
    changed_files = []
    for c in commits:
        changed_files += get_changed_files_from_commit(c)
    return changed_files


def get_repo_from_payload(payload):
    global repo_name
    r = payload["repository"]["full_name"]
    repo_name = payload["repository"]["name"]
    return r


def create_pull_request(repo_str):
    global g
    username = g.get_user().login
    repo = g.get_repo(repo_str)
    title = 'Jarsomatic'
    body = 'Jarsomatic pull request'
    dolog("will delete old pull requests")
    for p in repo.get_pulls():
        if p.title == title:
            p.edit(state="closed")
    print "deleted old pull requests"
    try:
        repo.create_pull(head=username+':gh-pages', base='gh-pages', title=title, body=body)
        return True
    except Exception as e:
        dolog("cannot create pull request, will try again. the was error:  <%s>"%(str(e)))
        time.sleep(20)
        try:
            repo.create_pull(head=username+':gh-pages', base='gh-pages', title=title, body=body)
            return True
        except Exception as e:
            dolog("still cannot create pull request. error:  <%s>"%(str(e)))
        return False


def fork_repo(repo_str):
    global g
    u = g.get_user()
    dolog("user %s"%(u.login))
    repo = g.get_repo(repo_str)
    dolog("repo %s"%(repo.full_name))
    try:
        f = u.create_fork(repo)
        return f.clone_url
    except Exception as e:
        print "error forking the repo %s, <%s>"%(repo_str, str(e))


def fork_cleanup():
    import shutil
    dolog("in fork cleanup")
    print "abs path: %s"%(get_repo_abs_path())
    for wo in os.walk(get_repo_abs_path()):
        dirpath, dirnames, filenames = wo
        break
    print "os walk is performed"
    for d in dirnames:
        print "dir: %s"%(d)
        if d.strip() != ".git":
            shutil.rmtree(d)
            print "delete: %s"%(d)
    print "checking file names"
    for f in filenames:
        f_dir = os.path.join(dirpath, f)
        print "file: %s"%(f_dir)
        os.remove(f_dir)


def update_fork(repo_str):
    global g
    repo = g.get_repo(repo_str)
    try:
        comm = "cd %s ; " \
               "git config user.email 'jarsomatic@delicias.dia.fi.upm.es' ; " \
               "git config user.name 'Jarsomatic' ; " \
               "git remote add upstream %s ; " \
               "git pull upstream master ; " \
               "git reset --hard upstream/master ; " \
               "git add . ; " \
               "git commit -m 'Jarsomatic update h' ; " \
               "git push -f origin master " % (get_repo_abs_path(), repo.ssh_url)
               #"git push -f origin master " % (get_repo_abs_path(), repo.clone_url)
        comm += append_comm
        dolog("update fork command: %s"%(comm))
        call(comm, shell=True)
    except Exception as e:
        dolog("error updating fork of repo %s, <%s>"%(repo_str, str(e)))


def delete_local_copy():
    comm = "cd "+temp_dir+"; rm -Rf "+repo_rel_dir
    call(comm, shell=True)


def switch_to_gh_pages():
    comm = "cd %s ; git branch gh-pages ; git checkout gh-pages"%(get_repo_abs_path())
    comm += append_comm
    dolog("switch to gh-pages: %s"%(comm))
    call(comm, shell=True)


def run_if_target(changed_files, target_files, jar_command):
    jarsomatic_branch = "jarsomatic"
    dolog("found %d files" % (len(changed_files)))
    found = False
    for f in changed_files:
        for t in target_files:
            if t == f:
                found = True
                break
        if found:
            break
    if found:
        print "Run"
        switch_to_gh_pages()
        comm = "cd "+get_repo_abs_path()+"; "  # Go to the project location
        comm += jar_command  # run the command and generate the output
        call(comm, shell=True)
        return found, "Run: "+comm
    else:
        dolog("Ignore")
        return found, "Ignore"


# source: http://stackoverflow.com/questions/21495598/simplejson-encoding-issue-illegal-character
def remove_control_chars(s):
    control_chars = ''.join(map(unichr, range(0, 32) + range(127, 160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', s)


def clone_repo(repo_url):
    repo_url_with_token = "https://"+github_token+"@"+repo_url.strip()[8:]
    comm = "cd %s; mkdir %s ; cd %s; git clone %s"%(temp_dir, repo_rel_dir, repo_rel_dir, repo_url_with_token)
    comm += append_comm
    dolog("clone repo command: %s"%(comm))
    call(comm, shell=True)


def copy_repo():
    comm = "mkdir %s"%(os.path.join(temp_dir, repo_rel_dir))
    # target is the repo name in the test webhook example so the example work
    comm += "; cp -R %s %s"%(os.path.join(temp_dir, 'source'), os.path.join(temp_dir, repo_rel_dir, 'target'))
    comm += append_comm
    dolog("copy command: "+comm)
    call(comm, shell=True)
    dolog("command executed")


def push_changes():
    comm = "cd %s;" \
           "git config --global user.email 'jarsomatic@delicias.dia.fi.upm.es' ; " \
           "git config --global user.name 'Jarsomatic' ; " \
           "git pull -s ours --no-edit upstream gh-pages ; " \
           "git add . ; " \
           "git commit -m 'jarsomatic update p' ; " \
           "git push -f origin gh-pages "%(get_repo_abs_path())
    comm += append_comm
    dolog("push changes command: %s"%(comm))
    call(comm, shell=True)


def change_status(new_status=None, new_progress=None):
    global current_repo
    if new_status is not None:
        current_repo.status = new_status
    if new_progress is not None:
        current_repo.progress = new_progress
    current_repo.save()


def delete_forked_repo(repo_str):
    comm = 'curl -H "Content-Type: application/json" -H "Authorization: token %s" ' % github_token
    comm += '-X DELETE  https://api.github.com/repos/jarsomatic/%s' % repo_str.split('/')[1].strip()
    dolog("deleting the fork: "+repo_str)
    call(comm, shell=True)


def workflow(changed_files, repo_str):
    global current_repo, current_user
    current_repo = Repo(name=repo_str, user=current_user, status="starting", started_at=datetime.now(), progress=10)
    current_repo.save()
    dolog("deleting the repo if exists")
    change_status("preparation", 10)
    delete_forked_repo(repo_str)
    dolog("forking the repo %s"%(repo_str))
    change_status("forking", 20)
    repo_url = fork_repo(repo_str)
    dolog("cloning the repo %s"%(repo_url))
    change_status("cloning", 30)
    clone_repo(repo_url)
    # fork_cleanup()
    change_status("updating the fork", 40)
    update_fork(repo_str)  # update from upstream as the cloned repo is an old fork due to Github limitation
    dolog("getting jar configurations")
    change_status("getting configurations", 50)
    target_files, jar_command = get_jar_config(os.path.join(get_repo_abs_path(), 'jar.cfg'))
    if target_files is None or jar_command is None:
        dolog("get jar config failed")
        change_status("Error getting configurations", 100)
        delete_local_copy()
        return "get jar config failed"
    else:
        change_status("configuration parsed", 60)
    dolog("running if target")
    change_status("running if target", 70)
    is_found, msg = run_if_target(changed_files, target_files, jar_command)
    dolog("after running")
    if is_found:
        dolog("is found")
        change_status("pushing changes", 80)
        push_changes()
        dolog("after pushing the changes")
        change_status("creating pull request", 85)
        if create_pull_request(repo_str):
            dolog("pull request is Trueee")
            change_status("pull request created", 100)
            current_repo.completed_at = datetime.now()
            current_repo.save()
            msg += " And pull request is created"
            dolog("deleting the forked repo attempt")
        else:
            dolog("pull request is False")
            change_status("pull failed to be created", 100)
            current_repo.completed_at = datetime.now()
            current_repo.save()
            msg += " And pull request failed to be created"
    else:
        change_status("not found", 100)
        dolog("not found")
        current_repo.completed_at = datetime.now()
        current_repo.save()
    return msg


def get_jar_config(config_file):
    dolog("looking for: %s" % config_file)
    confi = ConfigParser.ConfigParser()
    if not os.path.isfile(config_file):
        dolog("\n*** The file: "+config_file+" is not here or is not accessible ***\n")
    dolog("read the file")
    try:
        confi.read(config_file)
    except Exception as e:
        dolog("Cannot read jar configuration file: %s"%(config_file))
        dolog("Exception: %s"%(str(e)))
        return None, None
    dolog("getting the command")
    jar_command = confi.get('DEFAULT', 'command')
    dolog("jar_command: %s" % jar_command)
    dolog("target files")
    target_files_str = confi.get('DEFAULT', 'watch')
    dolog("watch")
    target_files = [f.strip().strip("'").strip('"') for f in target_files_str.split(",")]
    dolog("target return")
    return target_files, jar_command


def get_repo_abs_path():
    return os.path.join(temp_dir, repo_rel_dir, repo_name)

if __name__ == "__main__":
    app.run(debug=True)
    #app.run()

