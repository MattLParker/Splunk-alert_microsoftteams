import sys
import json
import csv
import gzip
import requests
from collections import OrderedDict
global actionurl

def send_webhook_request(url, body, user_agent=None):
    if url is None:
        print("ERROR No URL provided", file=sys.stderr)
        exit(1)
    elif not url.startswith("https"):
        print("ERROR Not a TLS webhook - INSECURE", file=sys.stderr)
        exit(1)
    print("INFO Sending POST request to url=%s with size=%d bytes payload" % (url, len(body)), file=sys.stderr)
    print(body, file=sys.stderr)
    print("DEBUG Body: %s" % body, file=sys.stderr)
    try:
        res = requests.post(url, headers={"Content-Type": "application/json", "User-Agent": 'user_agent'}, data=body)
        if 200 <= res.status_code < 300:
            print("INFO Webhook receiver responded with HTTP status=%d" % res.status_code, file=sys.stderr)
            return True
        else:
            print("ERROR Webhook receiver responded with HTTP status=%d" % res.status_code, file=sys.stderr)
            return False
    except requests.ConnectionError as e:
        print("ERROR Error sending webhook request: %s" % e, file=sys.stderr)
    except ValueError as e:
        print("ERROR Invalid URL: %s" % e, file=sys.stderr)
    return False

def build_workflow_action(facts, actionname, actionurl):
    content = OrderedDict()
    content["type"] = "AdaptiveCard"
    content["$schema"] = "https://adaptivecards.io/schemas/adaptive-card.json"
    content["version"] = "1.4"
    content["body"] = [
            {
                "type": "TextBlock",
                "text": settings.get("search_name") + " was triggered",
                "wrap": True,
                "size": "Large",
                "weight": "Bolder",
                "style": "heading"
            },
            {
                "type": "TextBlock",
                "text": 'Details: ',
                "size": "Medium",
                "wrap": True,
                "id": "title"
            },
            {
                "type": "FactSet",
                "facts": facts
            },
            {
                "type": "ActionSet",
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View in Splunk",
                        "url": settings.get('results_link')
                    },
                    {
                        "type": "Action.OpenUrl",
                        "title": actionname,
                        "url": actionurl
                    }
                ]
            }
        ]
    attachments = OrderedDict()
    attachments["contentType"] = "application/vnd.microsoft.card.adaptive"
    attachments["contentUrl"] = "null"
    attachments["content"] = content
    output = {
        "type":"message",
        "attachments":[attachments]}

    return output

def build_workflow_noaction(facts):
    content = OrderedDict()
    content["type"] = "AdaptiveCard"
    content["$schema"] = "https://adaptivecards.io/schemas/adaptive-card.json"
    content["version"] = "1.4"
    content["body"] = [
            {
                "type": "TextBlock",
                "text": settings.get("search_name") + " was triggered",
                "wrap": True,
                "size": "Large",
                "weight": "Bolder",
                "style": "heading"
            },
            {
                "type": "TextBlock",
                "text": 'Details: ',
                "size": "Medium",
                "wrap": True,
                "id": "title"
            },
            {
                "type": "FactSet",
                "facts": facts
            },
            {
                "type": "ActionSet",
                "actions": [
                    {
                        "type": "Action.OpenUrl",
                        "title": "View in Splunk",
                        "url": settings.get('results_link')
                    }
                ]
            }
        ]
    attachments = OrderedDict()
    attachments["contentType"] = "application/vnd.microsoft.card.adaptive"
    attachments["contentUrl"] = "null"
    attachments["content"] = content
    output = {
        "type":"message",
        "attachments":[attachments]}

    return output

def build_facts_workflow(settings, actionurlkey):
    facts = []
    for key,value in list(settings.get('result').items()):
        if actionurlkey != None:
            if key != actionurlkey:
                facts.append({"title":key, "value":str(value)})
        else:
            facts.append({"title":key, "value":str(value)})
    return facts

def check_action_url(settings, actionurlkey):
    action = None
    for key,value in list(settings.get('result').items()):
        if actionurlkey != None:
            if key == actionurlkey:
                action = value
    return action

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "--execute":
        print("FATAL Unsupported execution mode (expected --execute flag)", file=sys.stderr)
        sys.exit(1)
    try:
        settings = json.loads(sys.stdin.read())
        print("DEBUG Settings: %s" % settings, file=sys.stderr)
        url = settings['configuration'].get('url')
        if  settings['configuration'].get('actionurl'):
            actionurlkey = settings['configuration'].get('actionurl')
        else:
            actionurlkey = None
        actionurl = check_action_url(settings, actionurlkey)
        if  settings['configuration'].get('actionname'):
            actionname = settings['configuration'].get('actionname')
        else:
            actionname = actionurl
        actionurl = check_action_url(settings, actionurlkey)
        facts = build_facts_workflow(settings, actionurlkey)
        if actionurl:
            body = build_workflow_action(facts, actionname, actionurl)
        else:
            body = build_workflow_noaction(facts)
        user_agent = settings['configuration'].get('user_agent', 'Splunk')
        if not send_webhook_request(url, json.dumps(body), user_agent=user_agent):
            sys.exit(2)
    except Exception as e:
        print("ERROR Unexpected error: %s" % e, file=sys.stderr)
        sys.exit(3)
