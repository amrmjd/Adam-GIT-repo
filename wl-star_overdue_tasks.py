#!/usr/bin/python3.5

import json
import requests
from datetime import datetime
try: # for Python 3
    import urllib.request
except ImportError:
    import urllib2.request
import logging

lists_to_process = ["Later", "Now", "Waiting", "inbox", "Someday/maybe"]
lists_to_skip = ["CTO-Inbox"]
move_to_today_lists = ["Later", "Waiting", "Someday/maybe", "inbox"]
today_list = "Now"

"""
LAST FINISHED:
 - got the tasks by list title
NEXT UP TODO:
 - parse through the tasks lists and get the overdue tasks that aren't starred already and then call
              function to star them.

Criteria:
 - if not a shared list, apply to all tasks
 - if a shared list, check to see if assigned to me, then ensure "due_date" exists and check

LATER:
 - filter by lists
 - start with MAIN and INBOX

"""
debug_mode = False
debug_http = False
client_id = '88c7f43f8d54fafd0ddc'
access_token = 'e99b194a5f1afcdd794441471e1c88773d36956ce0c955ffa263c49f6260'

base_uri = 'https://a.wunderlist.com/api/v1/'

headers = {'X-Client-ID': client_id, 'X-Access-Token': access_token}
post_headers = {'X-Client-ID': client_id, 'X-Access-Token': access_token, 'Content-Type': 'application/json'}

# LOGGING ------
# Enabling debugging at http.client level (requests->urllib3->http.client)
# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.
if debug_http:

    try: # for Python 3
        from http.client import HTTPConnection
    except ImportError:
        from httplib import HTTPConnection
    HTTPConnection.debuglevel = 1

    logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
#  LOGGING ------

# with open('wunderlist_oauth.json') as data_file:
#    oauth = json.load(data_file)


def log_in_debug_mode(text_to_log):
    if debug_mode:
        print(text_to_log)


def fetch_from_api(fetch_url):
    uri = fetch_url % (access_token, client_id)
    # print(uri)
    resp = urllib.request.urlopen(uri).read()

    str_response = resp.decode('utf-8')
    r = json.loads(str_response)
    # r = json.loads(resp)
    return r


def push_to_api(push_url, payload, patch=False):

    # req = urllib.request.Request(push_url, json.dumps(payload), headers)
    utf_data = json.dumps(payload).encode('utf8')

    req = urllib.request.Request(push_url, utf_data, post_headers)
    if patch:
        req.get_method = lambda: 'PATCH'
    return urllib.request.urlopen(req).read()


def get_lists():
    list_url = base_uri + 'lists'
    r = requests.get(list_url, headers=headers)
    # print r.text
    wl_lists = r.text  # json.loads(r.text)
    return wl_lists


def get_tasks(list_id):
    tasks_url = base_uri + 'tasks'
    payload = {'list_id': list_id, 'completed': 'false'}
    r = requests.get(tasks_url, headers=headers, params=payload)
    # print(r.text)
    wl_tasks = r.text
    return wl_tasks


def get_list_id(wl_lists, list_name):

    uni_list = json.loads(wl_lists)
    for x in range(0, len(uni_list)-1):
        the_item = uni_list[x]
        if the_item["title"] == list_name:
            return the_item["id"]


def get_task(wl_task_id):
    get_task_url = base_uri + 'tasks/' + str(wl_task_id)
    r = requests.get(get_task_url, headers=headers)
    return r.text


def update_task(wl_task_id, json_data):
    patch_task_url = base_uri + 'tasks/' + str(wl_task_id)
    resp = fetch_from_api('https://a.wunderlist.com/api/v1/lists/' + str(list_id)) # + '?access_token=%s&client_id=%s')
    resp["starred"] = True

    r = push_to_api(patch_task_url, json_data, True)
    # r = requests.patch(patch_task_url, headers=post_headers, json=json_data)
    log_in_debug_mode(r.text)


def star_task(wl_task_id):
    patch_task_url = base_uri + 'tasks/' + str(wl_task_id)
    resp = fetch_from_api(patch_task_url + '?access_token=%s&client_id=%s')
    log_in_debug_mode(resp)
    # resp = json.loads(resp)
    resp["starred"] = True

    r = push_to_api(patch_task_url, resp, True)
    log_in_debug_mode(r)


def move_task_to_another_list(wl_task_id, target_list_id):
    patch_task_url = base_uri + 'tasks/' + str(wl_task_id)
    resp = fetch_from_api(patch_task_url + '?access_token=%s&client_id=%s')
    log_in_debug_mode(resp)
    # resp = json.loads(resp)
    resp["list_id"] = target_list_id

    r = push_to_api(patch_task_url, resp, True)
    log_in_debug_mode(r)


def star_due_or_overdue_tasks(wl_tasks, move_to_today_list=False):

    uni_tasks = json.loads(wl_tasks)
    log_in_debug_mode(uni_tasks)
    for x in range(len(uni_tasks)):
        the_item = uni_tasks[x]
        # print(the_item)
        if "due_date" in the_item:
            today = datetime.today()
            due_date = datetime.strptime(the_item["due_date"], '%Y-%m-%d')
            # print(due_date)
            # print(today)
            # if (datetime.strptime(the_item["due_date"], '%Y-%m-%d') - datetime.now()) < 0:
            if due_date <= today:
                log_in_debug_mode(" IS OVERDUE")
                # the_item["starred"] = True
                # update_task(the_item["id"],the_item)
                # resp = push_to_api('https://a.wunderlist.com/api/v1/task/' + str(the_item['id']), the_item, True)
                star_task(the_item["id"])
                if move_to_today_list:
                    log_in_debug_mode("MOVING to TODAY LIST:")
                    log_in_debug_mode(today_list)
                    move_task_to_another_list(the_item["id"], get_list_id(get_lists(), today_list))
        else:
            log_in_debug_mode(str(x) + " NO DUE DATE")


def get_memberships():
    resp = fetch_from_api(base_uri + "memberships?access_token=%s&client_id=%s")
    return resp





"""  END FUNCTIONS """


l_lists_to_skip = [excl_list.lower() for excl_list in lists_to_skip]
log_in_debug_mode(l_lists_to_skip)

the_lists = json.loads(get_lists())
log_in_debug_mode(the_lists)
for x in range(len(the_lists)):
    the_list = the_lists[x]
    log_in_debug_mode(the_list)
    if the_list["title"].lower() not in l_lists_to_skip:
        star_due_or_overdue_tasks(get_tasks(the_list["id"]), (the_list["title"] in move_to_today_lists))

    # list_id = get_list_id(get_lists(), lists_to_process[x])
    # if list_id is None:
    #     raise RuntimeError("List doesn't exist")
    # print("list: " + lists_to_process[x] + " " + str(list_id))



# print(get_lists())
# the_list_id = get_list_id(get_lists(), "!Today")
# print(the_list_id)
# tasks_list = get_tasks(the_list_id)
# star_due_or_overdue_tasks(tasks_list)

# star_due_or_overdue_tasks(tasks_list)

# print(tasks_list)
