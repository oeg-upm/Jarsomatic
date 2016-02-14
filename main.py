from flask import Flask, request
#import json
#import simplejson as json
import rson as json

import re


app = Flask(__name__)

target_files = ['.jar', '.csv']
host = 'http://127.0.0.1:5000/'


@app.route("/testp", methods=["GET"])
def test_positive():
    f = open("webhook_example_positive.txt")
    file_content = f.read()
    return webhook_handler(file_content)


@app.route("/testn", methods=["GET"])
def test_negative():
    f = open("webhook_example_negative.txt")
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
        return "exception occured"
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


def run_if_target(changed_files):
    print "found %d files"%(len(changed_files))
    found = False
    for f in changed_files:
        for t in target_files:
            if t in f:
                found = True
                break
        if found:
            break
    if found:
        print "Rerun"
        return "Rerun"
    else:
        print "Ignore"
        return "Ignore"


#source: http://stackoverflow.com/questions/21495598/simplejson-encoding-issue-illegal-character
def remove_control_chars(s):
    control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    return control_char_re.sub('', s)


@app.route("/")
def hello():
    return "Hello World!"


if __name__ == "__main__":
    app.run()

