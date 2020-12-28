import uuid, socket
import requests
import pytz, datetime
import json
import time
import PySimpleGUI as sg

operatingsystem = "Android"
os_version = "2.2"
model = "M"
user_agent = "Dalvik/1.4.0 (Linux; U; %s %s; %s Build/GRI54)" % (operatingsystem, os_version, model)
device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))

max_results = 50

params = {
#    'email': email,
#    'password':    password,
    'country':     'US',
    'deviceId':    device_id,
    'os':          operatingsystem,
    'appVersion':  "7.1",
    'appVariant':  "M-Pro",
    'osVersion':   os_version,
    'model':       model,
    'v':           2.4,
    'action':      'PAIR'}

# time converting functions
def _to_endomondo_time(time):
    return time.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _to_python_time(endomondo_time):
    return datetime.datetime.strptime(endomondo_time, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=pytz.utc)

def fetchcomments(email, password, max_workouts, fullpath=''):
    params['email'] = email
    params['password'] = password

    request = requests.session()
    request.headers['User-Agent'] = user_agent
    r = request.get('http://api.mobile.endomondo.com/mobile/auth', params=params)
    if r.status_code != 200:
        print('Error!', r.status_code)
        return None

    lines = r.text.split("\n")
    if len(lines) < 1:
        print("Error: URL %s: empty response" % r.url)
        return None
    if lines[0] != "OK":
        print("Error: URL %s: %s" % (r.url, lines[0]))
        return None

    for line in lines[1:]:
        key, value = line.split("=")
        if key == "authToken":
            token = value
            break

    before = None
    after = None #_to_python_time('2020-11-10 00:07:38 UTC')
    results = [] # type: ignore

    workout_params = {'maxResults': max_results,
        'fields': 'device,simple,basic,interval,lcp_count,feed_id'}
    workout_params.update({'authToken': token,
                       'language': 'EN'})

    i = 0
    while True:
        if after is not None:
            workout_params.update({'after': _to_endomondo_time(after)})
        if before is not None:
            workout_params.update({'before': _to_endomondo_time(before)})

        r = request.get('http://api.mobile.endomondo.com/mobile/api/workout/list', 
                        params=workout_params)
        if r.status_code != 200:
            print('Error!', r.status_code)
            return None

        chunk = r.json()['data']
        for ch in chunk:
            i += 1
            feedid = 0
            num_comments = 0
            #check if there are comments
            t1 = ch.get('lcp_count')
            t2 = ch.get('comments')
            if t1:
                if t1['comments']>0:
                    num_comments = t1['comments']
            elif t2:
                if t2['count']>0:
                    num_comments = t2['count']
            try:
                if num_comments>0:
                    feedid=ch['feed_id']
                    #print('FEED ID: ', feedid, " Comm: ", num_comments)
                    workout_params = {'feedId': str(feedid)}
                    workout_params.update({'authToken': token,
                            'language': 'EN', 'maxResults': '200'})
                    rr = request.get('http://api.mobile.endomondo.com/mobile/api/feed/comments/get', params=workout_params)
                    if r.status_code != 200:
                        print ('Error!' + str(r.status_code))
                    jj = rr.json()
                    ch['comments'] = jj['data']
                    ch['num_comments'] = num_comments
            except KeyError:
                pass
            sg.OneLineProgressMeter("Downloading Endomondo comments...", i, max_workouts)
            
        if chunk:
            results.extend(chunk)
            last_start_time = chunk[-1]['start_time']
            before = _to_python_time(last_start_time)
        
        if not chunk:
            break
    
    with open(fullpath+'endoworkouts.json', 'w') as json_file:
        json.dump(results, json_file)
    print("Workout processed: "+str(len(results)))
    return results

