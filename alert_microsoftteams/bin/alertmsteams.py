import sys
import json
import csv
import gzip
import requests
from collections import OrderedDict


def send_webhook_request(url, body, user_agent=None):
    if url is None:
        print("ERROR No URL provided", file=sys.stderr)
        return False
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
        if  settings['configuration'].get('actionname'):    
            actionname = settings['configuration'].get('actionname')
        try:
            actionurlkey
        except NameError:
            actionurlkey = None
        facts = []
        for key,value in list(settings.get('result').items()):
            if actionurlkey != None:
                if key != actionurlkey:
                    facts.append({"name":key, "value":value})
                elif key == actionurlkey:
                    actionurl = value
            else:
                facts.append({"name":key, "value":value})
        try:
            actionurl
        except NameError:
            actionurl = None
        if actionurl:
            body = OrderedDict(
                summary=settings.get('search_name') + " was triggered",
                title=settings.get('search_name'),
                sections=[
                    {"activityTitle": settings.get("search_name") + " was triggered"},
                    {
                        "title": "Details",
                        "markdown": "false",
                        "facts": facts
                    }
                ],
                potentialAction=[{
                    "@context":"http://schema.org",
                    "@type":"ViewAction",
                    "name":"View in Splunk",
                    "target":[settings.get('results_link')]
                    },{
                    "@context":"http://schema.org",
                    "@type":"ViewAction",
                    "name":actionname,
                    "target":[actionurl]
                    }]
            )
        else:
            body = OrderedDict(
                summary=settings.get('search_name') + " was triggered",
                title=settings.get('search_name'),
                sections=[
                    {"activityTitle": settings.get("search_name") + " was triggered"},
                    {
                        "title": "Details",
                        "markdown": "false",
                        "facts": facts
                    }
                ],
                potentialAction=[{
                    "@context":"http://schema.org",
                    "@type":"ViewAction",
                    "name":"View in Splunk",
                    "target":[settings.get('results_link')]
                    }]
            )
        user_agent = settings['configuration'].get('user_agent', 'Splunk')
        if not send_webhook_request(url, json.dumps(body), user_agent=user_agent):
            sys.exit(2)
    except Exception as e:
        print("ERROR Unexpected error: %s" % e, file=sys.stderr)
        sys.exit(3)
