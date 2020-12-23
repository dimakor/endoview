import uuid
import socket
import requests
import pprint
import pytz
import datetime
import json
import progressbar
import os
import getpass
import tcx

#TODO: https://pypi.org/project/gpxpy/

bar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)

operatingsys = "Android"
os_version = "2.2"
model = "M"
user_agent = "Dalvik/1.4.0 (Linux; U; %s %s; %s Build/GRI54)" % (operatingsys, os_version, model)
device_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))

max_results = 50

params = {
    #'email': email,
    #'password':    password,
    'country':     'US',
    'deviceId':    device_id,
    'os':          operatingsys,
    'appVersion':  "7.1",
    'appVariant':  "M-Pro",
    'osVersion':   os_version,
    'model':       model,
    'v':           2.4,
    'action':      'PAIR'}

SPORTS = {
    0:  'Running',
    1:  'Cycling, transport',
    2:  'Cycling, sport',
    3:  'Mountain biking',
    4:  'Skating',
    5:  'Roller skiing',
    6:  'Skiing, cross country',
    7:  'Skiing, downhill',
    8:  'Snowboarding',
    9:  'Kayaking',
    10: 'Kite surfing',
    11: 'Rowing',
    12: 'Sailing',
    13: 'Windsurfing',
    14: 'Fitness walking',
    15: 'Golfing',
    16: 'Hiking',
    17: 'Orienteering',
    18: 'Walking',
    19: 'Riding',
    20: 'Swimming',
    21: 'Spinning',
    22: 'Other',
    23: 'Aerobics',
    24: 'Badminton',
    25: 'Baseball',
    26: 'Basketball',
    27: 'Boxing',
    28: 'Climbing stairs',
    29: 'Cricket',
    30: 'Cross training',
    31: 'Dancing',
    32: 'Fencing',
    33: 'Football, American',
    34: 'Football, rugby',
    35: 'Football, soccer',
    36: 'Handball',
    37: 'Hockey',
    38: 'Pilates',
    39: 'Polo',
    40: 'Scuba diving',
    41: 'Squash',
    42: 'Table tennis',
    43: 'Tennis',
    44: 'Volleyball, beach',
    45: 'Volleyball, indoor',
    46: 'Weight training',
    47: 'Yoga',
    48: 'Martial arts',
    49: 'Gymnastics',
    50: 'Step counter'
}

# time converting functions
def _to_endomondo_time(time):
    return time.astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def _to_python_time(endomondo_time):
    return datetime.datetime.strptime(endomondo_time, "%Y-%m-%d %H:%M:%S UTC").replace(tzinfo=pytz.utc)

def to_datetime(v):
    return datetime.datetime.strptime(v, "%Y-%m-%d %H:%M:%S %Z")

def to_float(v):
    if v == '' or v is None:
        return None
    return float(v)

def to_int(v):
    if v == '' or v is None:
        return None
    return float(v)

def to_meters(v):
    v = to_float(v)
    if v:
        v *= 1000
    return v

def backup_name(email):
    return ''.join([datetime.date.today().strftime('%Y-%m-%d'), '_', email.replace('@', '_').replace('.','_')])

def download_pic(picurl, filename):
    headers = { 
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
                }
    ir = requests.get(picurl, headers=headers)
    if ir.status_code != 200:
        return ir.status_code
    try:
        with open(filename, 'wb') as f:
            f.write(ir.content)
    except:
        return 666
    return 0

def get_workout_pics(id, token):
    request = requests.session()
    request.headers['User-Agent'] = user_agent
    workout_params = {'workoutId': id, 'fields': 'pictures'}
    workout_params.update({'authToken': token,
                       'language': 'EN'})
    rr = request.get('https://api.mobile.endomondo.com/mobile/api/workout/get', params=workout_params)
    if rr.status_code != 200:
        print ('Error!' + str(rr.status_code))
    return(rr.json().get('pictures'))


def create_tcx(ch, token, request):
    workout_params = {'trackId': str(ch.get('id'))}
    workout_params.update({'authToken': token,
            'language': 'EN'})
    rr = request.get('https://api.mobile.endomondo.com/mobile/readTrack', params=workout_params)
    if rr.status_code != 200:
        print ('Points Error!', str(rr.status_code))
    lines = rr.text.split("\n")
    if (len(lines) < 1):
        print("Error: URL %s: empty response" % rr.url)
    data = lines[1].split(";")
    #pprint.pprint(data)
    start_t = to_datetime(data[6])
    activity = tcx.Activity()
    activity.sport = SPORTS.get(int(data[5]), "Other")
    activity.start_time = start_t
    activity.notes = ch.get('message') #TODO find note
    # create a single lap for the whole activity
    l = tcx.ActivityLap()
    l.start_time = start_t
    l.timestamp = to_datetime(data[1])
    l.total_time_seconds = to_float(data[7])
    l.distance_meters = to_meters(data[8])
    l.calories = to_int(data[9])
    l.min_altitude = to_float(data[11])
    l.max_altitude = to_float(data[12])
    l.max_heart = to_float(data[13])
    l.avg_heart = to_float(data[14])
    activity.laps.append(l)

    # extra lines are activity trackpoints
    try:
        for line in lines[2:]:
            data = line.split(";")
            #pprint.pprint(data)
            if len(data) >= 9:
                w = tcx.Trackpoint()
                w.timestamp = to_datetime(data[0]) #
                w.latitude = to_float(data[2])
                w.longitude = to_float(data[3])
                w.altitude_meters = to_float(data[6])
                w.distance_meters = to_meters(data[4])
                if data[7] != '':
                    w.heart_rate = to_int(data[7])
                activity.trackpoints.append(w)
    except ValueError:
        return None, rr.text[3:]
    return activity, rr.text[3:]

def main():
    email = input("Email: ")
    password = getpass.getpass()
    params['email'] = email
    params['password'] = password

    
    #directories for backup

    request = requests.session()
    request.headers['User-Agent'] = user_agent
    r = request.get('https://api.mobile.endomondo.com/mobile/auth', params=params)
    if r.status_code != 200:
        print ('Error!', r.status_code)

    lines = r.text.split("\n")
    if len(lines) < 1:
        print("Error: URL %s: empty response" % r.url)
    if lines[0] != "OK":
        print("Error: URL %s: %s" % (r.url, lines[0]))

    for line in lines[1:]:
        key, value = line.split("=")
        if key == "authToken":
            token = value
            break
#    print ("Token: "+token)
    # TODO: if token is None
    #     print("No auth token")
    #     break
    #generate backup folder paths
    workingfolder ='.' #for future use
    backupfolder = os.path.join(workingfolder, backup_name(email)) #backup root
    workoutfolder = os.path.join(backupfolder,'Workouts')
    imagefolder = os.path.join(backupfolder, 'Images')
    avafolder = os.path.join(backupfolder, 'Avatars')
    trackfolder = os.path.join(backupfolder, 'Tracks')
    for x in [workoutfolder, imagefolder, avafolder, trackfolder]:
        try:
            os.makedirs(x)
        except OSError:
            print ("Creation of the directory %s failed" % x)

    before = None #_to_python_time('2020-09-30 00:07:38 UTC') #None
    after = None #_to_python_time('2020-12-01 00:07:38 UTC') #None
    results = [] # type: ignore

    workout_params = {'maxResults': max_results,
        'fields': 'device,simple,basic,interval,lcp_count,feed_id,pictures,points'}
    workout_params.update({'authToken': token,
                       'language': 'EN'})

    i = 0
    nm = 0
    avatars = set()
    while True:
        i+=1
        if after is not None:
            workout_params.update({'after': _to_endomondo_time(after)})
        if before is not None:
            workout_params.update({'before': _to_endomondo_time(before)})

        r = request.get('https://api.mobile.endomondo.com/mobile/api/workout/list', 
                        params=workout_params)
        if r.status_code != 200:
            print ('Error!', r.status_code)

        chunk = r.json()['data']
        for ch in chunk:
            nm += 1
            feedid = 0
            num_comments = 0
            comments = None
            
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
                            'language': 'EN'})
                    rr = request.get('https://api.mobile.endomondo.com/mobile/api/feed/comments/get', params=workout_params)
                    if rr.status_code != 200:
                        print ('Error!' + str(rr.status_code))
                    jj = rr.json()
                    comments = jj['data']
                    ch['comments'] = comments
                    ch['num_comments'] = num_comments
                
                workout_name = ch['start_time'].replace(':', '_')
                workoutfname = os.path.join(workoutfolder, workout_name+'.json')
                trackfname = os.path.join(trackfolder, workout_name+'_track.tcx')
                trackfname_txt = os.path.join(trackfolder, workout_name+'_track.txt')
                trackfname_json = os.path.join(trackfolder, workout_name+'_track.json')

                #save points to separate file
                try:
                    track = ch.pop('points') #Also removes points from ch
                    ch['track_file'] = trackfname_json #save location of track file in workout
                    with open(trackfname_json, 'w') as f:
                        json.dump(track, f)
                except KeyError as err:
                    pass
                act_txt = []
                activity, act_txt = create_tcx(ch, token, request)
                with open(trackfname_txt, 'w') as f:
                    f.write(act_txt)
                if activity is not None:
                    writer = tcx.Writer()
                    tcxfile = writer.write(activity)
                    if tcxfile:
                        with open(trackfname, 'wb') as f:
                            f.write(tcxfile)
                            ch['track_file'] = trackfname
                else:
                    print('TCX failure: ', trackfname_txt)

                #download images
                pictures = ch.get('pictures')
                if pictures is None:
                    pictures = get_workout_pics(ch['id'], token)
                if pictures:
                    for pic in pictures:
                        picurl = pic['url']
                        imagefname = os.path.join(imagefolder, str(pic['id'])+'.jpg')
                        status = download_pic(picurl, imagefname)
                        if  status == 0:
                            pic['picture_file'] = imagefname

                #download avatars
                #1. owner
                try:
                    picurl = ch['owner']['picture_url']
                    if picurl not in avatars:
                        ownerid = ch['owner_id']
                        avafname = os.path.join(avafolder, str(ownerid)+'.jpg')
                        status = download_pic(picurl, avafname)
                        if status == 0:
                            ch['picture_file'] = avafname
                            avatars.add(picurl)
                except KeyError:
                    pass
                #2. commenters
                if num_comments >0:
                    for cm in comments['data']:
                        try:
                            frm = cm['from']
                            picurl = frm['picture_url']
                            if picurl not in avatars:
                                ownerid = frm['id']
                                avafname = os.path.join(avafolder, str(ownerid)+'.jpg')
                                status = download_pic(picurl, avafname)
                                if status == 0:
                                    frm['picture_file'] = avafname
                                    avatars.add(picurl)
                        except KeyError:
                            pass
                
                #save workout to file
                with open(workoutfname, 'w') as f:
                    json.dump(ch, f)
                bar.update(nm)            
            except KeyError:
                print(KeyError)

        if chunk:
            results.extend(chunk)
            last_start_time = chunk[-1]['start_time']
            before = _to_python_time(last_start_time)


#        if not chunk or (max_results and len(results) >= 50):
        if not chunk:
            break
    
    bar.finish()
    # with open(os.path.join(backupfolder,'endoworkouts.json'), 'w') as json_file:
    #     json.dump(results, json_file)
    print("Workout processed: ", nm)
    # feed_id = results['data'][0]['feed_id']
    # print('FEED ID:'+str(feed_id))
    # wo_id = json['data'][0]['id']
    # print('WORKOUT ID:'+str(wo_id))

    #workout_params = {'maxResults': 10, 'feedId': str(feed_id)}
    #workout_params = {'maxResults': 10, 'feedId': '281476638965936'}

if __name__ == "__main__":
    main()
