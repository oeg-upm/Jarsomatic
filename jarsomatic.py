from flask import Flask, request, redirect, url_for
import ConfigParser
# import json
# import simplejson as json
import rson as json
import re
from subprocess import call
import os.path
import random
import string
from github import Github
import logging
import time

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
# logging.basicConfig(filename=log_filename, format='%(asctime)s %(levelname)s: %(message)s', level=logging.DEBUG)
logging.basicConfig(filename=os.path.join(app_home, log_filename), format='%(asctime)s: %(message)s', level=logging.DEBUG)

def dolog(msg):
    logging.critical(msg)
    # print msg
try:
    u = g.get_user().login
    dolog("user %s, token %s"%(u, github_token))
except Exception as e:
    dolog("Github token is invalid")


@app.route("/pull")
def pull_new_version():
    comm = "cd %s; git pull --no-edit -Xtheirs origin master "%(app_home)
    comm+=append_comm
    dolog("will update Jarsomatic")
    dolog("Jarsomatic update command: "+comm)
    call(comm, shell=True)
    return redirect(url_for('getlog'))


@app.route("/clearlog")
def clearlog():
    f = open(log_filename, "w")
    f.close()
    return redirect(url_for('getlog'))


@app.route("/getlog")
def getlog():
    s = []
    with open(log_filename,"r") as f:
        for idx,l in enumerate(f):
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
                        <a href="/clearlog">clear logs</a><br>
                        <table>

                        <tr>
                            <td>Line</td>
                            <td>Log</td>
                        </tr>
                        %s
                        </table></body>
                    </html>""" % "".join(s[::-1])


@app.route("/")
def hello():
    return "Welcome to Jarsomatic" + "<br><br><a href='getlog'>see logs</a>"
           #"<br><br><a href='testp'>Test Positive</a>" + \
           #"<br><br><a href='testn'>Test Negative</a>"


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
    # print "values <%s>\n\n"%(str(request.values))
    # try:
    #     print "form: %s"%(str(request.form))
    #     # print "values of payload <%s>\n\n"%(str(request.form['payload']))
    #     # print "values of payload <%s>\n\n"%(str(request.values['payload']))
    # except:
    #     pass
    # print "data %s"%(str(request.data))
    # values = request.values['payload']
    # print "request: "+str(request)
    try:
        dolog("json: %s"%(str(request.json)))
        # print "form: %s"%(str(request.form))
        # print "values: %s"%(str(request.values))
        # print "data: %s"%(str(request.data))
    except Exception as e:
        dolog("exception: "+str(e))
    values = request.json
    # print "form %s"%(str(values))
    if values["ref"].strip() == "refs/heads/gh-pages":
        return "gh-pages push will be ignored"
    try:
        pid = os.fork()
        if pid==0:
            time.sleep(10)
            return webhook_handler(values)
        else:
            return "Process started to do the work"
    except Exception as e:
        return "Error forking the process: <%s>"%(str(e))
    # return webhook_handler(values)


def webhook_handler(payload):
    # values are expected to be a dict
    try:
        # print '\n\n****  values ***'
        # for v in values.values():
        #     print "\n*** v: "+str(v)
        # print '\n\n**** keys ***'
        # for v in values.keys():
        #     print "\n*** k: "+str(v)
        # print '\n\n**** items ***'
        # for v in values.items():
        #     print "\n*** i: "+str(v)

        # values = json.loads(str(values))
        # payload = values['payload']
        #payload = values.get('payload')
        print "payload %s"%(str(payload))
        # payload = values
    except Exception as e:
        dolog("exception: "+str(e))
        return "exception occurred \n"
        #return "exception occurred %s"%(str(values))
    dolog("will get changed files from payload")
    changed_files = get_changed_files_from_payload(payload)
    dolog("will get the repo from payload")
    repo_str = get_repo_from_payload(payload)
    dolog("will proceed to the workflow")
    return workflow(changed_files, repo_str)
    # return run_if_target(changed_files)


def get_changed_files_from_commit(commit):
    return commit["added"] + commit["modified"]


def get_changed_files_from_payload(payload):
    commits = payload['commits']
    changed_files = []
    for c in commits:
        changed_files += get_changed_files_from_commit(c)
    return changed_files


def get_repo_from_payload(payload):
    global repo_name
    # print "will get fullname"
    # for k in payload["repository"]:
    #     print "k: %s"%(k)
    r = payload["repository"]["full_name"]
    # print "will get name"
    repo_name = payload["repository"]["name"]
    # print "repository: %s"%(r)
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
        dolog("cannot create pull request, error:  <%s>"%(str(e)))
        return False


def fork_repo(repo_str):
    global g
    u = g.get_user()
    dolog("user %s"%(u.login))
    repo = g.get_repo(repo_str)
    dolog("repo %s"%(repo.full_name))
    try:
        # print "will create fork"
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
        # comm = "cd %s ; git config user.email 'jarsomatic@delicias.dia.fi.upm.es' ; git config user.name 'Jarsomatic' ; git branch ; git pull --no-edit -Xtheirs %s ; git add . ; git commit -m 'Jarsomatic update' ; git push "%(get_repo_abs_path(), repo.clone_url)
        comm = "cd %s ; git config user.email 'jarsomatic@delicias.dia.fi.upm.es' ; git config user.name 'Jarsomatic' ; git branch ; git remote add upstream %s ; git pull --no-edit -Xtheirs upstream master ; git add . ; git commit -m 'Jarsomatic update' ; git push origin master "%(get_repo_abs_path(), repo.clone_url)
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
    dolog("found %d files"%(len(changed_files)))
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
        # Because we already get the fork
        # if not TEST:
        #     comm += "git pull; "  # get latest update
        comm += jar_command  # run the command and generate the output
        call(comm, shell=True)
        #comm = "cd "+temp_dir+"; rm -Rf "+repo_rel_dir
        #call(comm, shell=True)
        return found, "Run: "+comm
    else:
        #comm = "cd "+temp_dir+"; rm -Rf "+repo_rel_dir
        #call(comm, shell=True)
        dolog("Ignore")
        return found, "Ignore"


# source: http://stackoverflow.com/questions/21495598/simplejson-encoding-issue-illegal-character
def remove_control_chars(s):
    control_chars = ''.join(map(unichr, range(0, 32) + range(127, 160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', s)


def clone_repo(repo_url):
    repo_url_with_token =  "https://"+github_token+"@"+repo_url.strip()[8:]
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
    comm = "cd %s; git config user.email 'jarsomatic@delicias.dia.fi.upm.es' ; git config user.name 'Jarsomatic' ; git pull -s ours --no-edit origin gh-pages; git add . ; git commit -m 'jarsomatic update' ; git push origin gh-pages "%(get_repo_abs_path())
    comm += append_comm
    dolog("push changes command: %s"%(comm))
    call(comm, shell=True)


def workflow(changed_files, repo_str):
    dolog("forking the repo %s"%(repo_str))
    repo_url = fork_repo(repo_str)
    dolog("cloning the repo %s"%(repo_url))
    clone_repo(repo_url)
    #fork_cleanup()
    update_fork(repo_str)  # update from upstream as the cloned repo is an old fork due to Github limitation
    dolog("getting jar configurations")
    target_files, jar_command = get_jar_config(os.path.join(get_repo_abs_path(), 'jar.cfg'))
    if target_files is None or jar_command is None:
        dolog("get jar config failed")
        delete_local_copy()
        return "get jar config failed"
    dolog("running if target")
    is_found, msg = run_if_target(changed_files, target_files, jar_command)
    dolog("after running")
    if is_found:
        dolog("is found")
        push_changes()
        dolog("after push changes")
        if create_pull_request(repo_str):
            dolog("pull request is True")
            msg += " And pull request is created"
        else:
            dolog("pull request is False")
            msg += " And pull request failed to be created"
    else:
        dolog("not found")
    delete_local_copy()
    return msg


def get_jar_config(config_file):
    dolog("looking for: %s"%(config_file))
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
    dolog("jar_command: %s"%jar_command)
    dolog("target files")
    target_files_str = confi.get('DEFAULT', 'watch')
    dolog("watch")
    target_files = [f.strip().strip("'").strip('"') for f in target_files_str.split(",")]
    dolog("target return")
    return target_files, jar_command


def get_repo_abs_path():
    return os.path.join(temp_dir, repo_rel_dir, repo_name)

if __name__ == "__main__":
    app.run()

