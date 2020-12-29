import glob
import json
import os.path
import io
import time
import tkinter
import pytz
import datetime
import emoji
import pickle
import configparser

from PIL import Image, ImageTk
import PySimpleGUI as sg

from fetchcomments import *

#interface declarations
sg.theme("SystemDefault")

#logic declarations
workout_path = '/Workouts/'

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

def get_img_data(f, maxsize=(500, 200), first=False):
    """Generate image data using PIL
    """
    img = Image.open(f)
    img.thumbnail(maxsize)
    if first:                     # tkinter is inactive the first time
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        imgsize=img.size
        del img
        return bio.getvalue(), imgsize
    return ImageTk.PhotoImage(img)

def FieldColumn(name, key, value=''):
    """Generate a column that contains two text fields - label and value
    """
    layout = [
            [sg.Text(name, size=(10,1)), sg.Text(value if value is not None else '', size=(18,1), key=key)]
            ]
    return sg.Col(layout, pad=(0,0))



def _to_python_time(endomondo_time):
    try:
        pt = datetime.datetime.strptime(endomondo_time, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=pytz.utc)
    except ValueError:
        pt = datetime.datetime.strptime(endomondo_time, "%Y-%m-%d %H:%M:%S %Z").replace(tzinfo=pytz.utc)
    return pt

def normalizefield(wodict):
    """Normalize dictionary of raw Endomondo data
    """
    if 'speed_avg' in wodict.keys():
        speed = float(wodict['speed_avg'])
        if speed != 0 :
            pace_sec = 60*60 / speed
            res = time.gmtime(pace_sec)
            wodict['pace'] = time.strftime('%M:%S', res)
            wodict['speed'] = str(round(speed, 2))
        else:
            wodict['pace'] = '0'
            wodict['speed'] = '0'
    if 'speed_avg_kmh' in wodict.keys():
        speed = float(wodict['speed_avg_kmh'])
        if speed != 0 :
            pace_sec = 60*60 / speed
            res = time.gmtime(pace_sec)
            wodict['pace'] = time.strftime('%M:%S', res)
            wodict['speed'] = str(round(speed, 2))
        else:
            wodict['pace'] = '0'
            wodict['speed'] = '0'
    if 'speed_kmh_avg' in wodict.keys():
        speed = float(wodict['speed_kmh_avg'])
        if speed != 0 :
            pace_sec = 60*60 / speed
            res = time.gmtime(pace_sec)
            wodict['pace'] = time.strftime('%M:%S', res)
            wodict['speed'] = str(round(speed, 2))
        else:
            wodict['pace'] = '0'
            wodict['speed'] = '0'
    #    return normalized
    if 'speed_max' in wodict.keys():
        speed = float(wodict['speed_max'])
        wodict['speed_max'] = str(round(speed, 2))
    if 'speed_max_kmh' in wodict.keys():
        speed = float(wodict['speed_max_kmh'])
        wodict['speed_max'] = str(round(speed, 2))
    if 'speed_kmh_max' in wodict.keys():
        speed = float(wodict['speed_kmh_max'])
        wodict['speed_max'] = str(round(speed, 2))
    #    return normalized
    if 'duration' in wodict.keys():
        res = time.gmtime(float(wodict['duration']))
        dur = time.strftime('%H:%M:%S', res)
        wodict['duration'] = dur
    if 'duration_s' in wodict.keys():
        res = time.gmtime(float(wodict['duration_s']))
        dur = time.strftime('%H:%M:%S', res)
        wodict['duration'] = dur
    if 'duration_sec' in wodict.keys():
        res = time.gmtime(float(wodict['duration_sec']))
        dur = time.strftime('%H:%M:%S', res)
        wodict['duration'] = dur
    #    return normalized
    if 'sport' in wodict.keys():
        sp = wodict['sport']
        if isinstance(sp, int):
            try:
                wodict['sport'] = SPORTS[sp]
            except KeyError:
                wodict['sport'] = SPORTS[22] #Unknown sport - 'Other'
        else:
            wodict['sport'] = sp.capitalize().replace('_', ' ')
    #    return normalized
    if 'distance' in wodict.keys():
        wodict['distance'] = str(round(float(wodict['distance']),2))
    if 'distance_km' in wodict.keys():
        wodict['distance'] = str(round(float(wodict['distance_km']),2))
    #    return normalized
    if 'start_time' in wodict.keys():
        tt = _to_python_time(wodict['start_time'])
        wodict['date'] = tt.date()
        wodict['time'] = tt.time()
        wodict['start_time'] = wodict['start_time']
    #    return normalized
    if 'message' in wodict.keys():
        wodict['message'] = emoji.get_emoji_regexp().sub(r'', wodict['message'])
    if 'ascent' in wodict.keys():
        wodict['ascend_m'] = wodict['ascent']
    if 'descent' in wodict.keys():
        wodict['descend_m'] = wodict['descent']
    
    #HEART RATE
    if 'heart_rate_avg' in wodict.keys():
        wodict['heart_rate_avg_bpm'] = wodict['heart_rate_avg']
    if 'heart_rate_max' in wodict.keys():
        wodict['heart_rate_max_bpm'] = wodict['heart_rate_max']
    if 'heart_rate_bpm_avg' in wodict.keys():
        wodict['heart_rate_avg_bpm'] = wodict['heart_rate_bpm_avg']
    if 'heart_rate_bpm_max' in wodict.keys():
        wodict['heart_rate_max_bpm'] = wodict['heart_rate_bpm_max']

    if 'cadence_avg' in wodict.keys():
        wodict['cadence_avg_rpm'] = wodict['cadence_avg']
    if 'cadence_max' in wodict.keys():
        wodict['cadence_max_rpm'] = wodict['cadence_max']
    
    #ALTITUDE
    if 'altitude_min' in wodict.keys():
        wodict['altitude_min_m'] = wodict['altitude_min']
    if 'altitude_max' in wodict.keys():
        wodict['altitude_max_m'] = wodict['altitude_max']
    if 'altitude_m_min' in wodict.keys():
        wodict['altitude_min_m'] = wodict['altitude_m_min']
    if 'altitude_m_max' in wodict.keys():
        wodict['altitude_max_m'] = wodict['altitude_m_max']
    
    if 'calories' in wodict.keys():
        wodict['calories_kcal'] = wodict['calories']
    #    return normalized

def loadfull(path):
    """Load data from Endomondo backup
    """
    dd=[]
    #create index to find workout by start_time (actually, date and time string)
    indx = {}
    fullpath = "".join([path, workout_path, '*.json']) #TODO: join paths correctly
    files = glob.glob(fullpath) #Load list of all JSON workout files
    total = len(files) #needed for progress bar
    for i, f in enumerate(files):
        with open(f, encoding='utf-8') as p:
            w = json.load(p)
            workout_dict = {}
            if isinstance(w, list):
                for dict in w:
                    #skip GPS track part for workout
                    if 'points' in dict.keys():
                        continue
                    normalizefield(dict)
                    workout_dict.update(dict)
            else:
                #we suppose it's dict (and we're dealing with backup from endobackup.py)
                normalizefield(w)
                workout_dict.update(w)
            workout_dict.update({'json_file': f}) #add path of processed file for future references
            dd.append(workout_dict)
        if total > 1:
            if not sg.OneLineProgressMeter('Loading Endo Backup', i, total-1,  'kkk', path):
                break
    #sort before creating an index
    dd.sort(key=lambda a: a['date'])
    dlen = len(dd)
    #create index to find specific workout using start time of workout
    #will need it when we will download comments from Endomondo
    for i, d in enumerate(dd):
        indx[d['start_time'][:-2]] = i #-2 to remove milliseconds from start time
        if dlen>1:
            sg.OneLineProgressMeter('Creating index', i, dlen-1)
    return dd, indx

def updatetable(data, dd, window):
    """Update data table of the main window with data from dd
    """
    #data.clear()
    data = []
    for dict in dd:
        dict.setdefault('message', '') #avoid None in empty messages
        dict.setdefault('num_comments', '')
        piclist = dict.get('pictures')
        numpic = ' ' if piclist is None else len(piclist) #find out number of pictures in the workout
        data.append([dict.get('date'), dict.get('time'), dict.get('sport'),
            dict.get('distance'), dict.get('duration'), dict.get('pace'),
            numpic, dict.get('message'), dict.get('num_comments')])
    window['-DATA-'].update(data)

def updatecomments(dd, comm, indx):
    comm.sort(key=lambda a: a['start_time'])
    maxw = len(comm)
    for i, c in enumerate(comm):
        lcpc = c.get('num_comments')
        #TODO: notify if amount of workouts in databases are not the same
        if lcpc:
            #check if there are comments in workout
            if lcpc>0:
                try:
                    #find corresponding workout in internal database
                    j = indx[c['start_time'][:-4]]
                    dd[j]['num_comments']=lcpc
                    dd[j]['ecomments'] = c.get('comments')
                except:
                    pass
        sg.OneLineProgressMeter('Updating workouts', i, maxw-1,  'kkk')

def main():
    #Layout of lower frame of main window 
    details_frame = [
                        [FieldColumn("Sport: ", '-SPORT-'), FieldColumn("Date: ",'-DATE-'),
                        FieldColumn("Time: ", '-STARTTIME-'), FieldColumn("Duration: ", '-DURATION-'),
                        FieldColumn("Distance: ", '-DISTANCE-')],
                        [FieldColumn("Pace: ", '-PACE-'), FieldColumn("Ascent: ", '-ASC-'), 
                        FieldColumn("Descent: ", '-DESC-')],
                        [sg.Frame('Note', [[sg.Text(key='-NOTE-', size=(180,6))]])]
                    ]

    #List of labels for main table
    tabl_head = ['Date', 'Time', 'Type', 'Distance', 'Duration', 'Pace', 'Photos', 'Note', 'Comments']
    #Fill data for main table (needed as placeholder to define size for initial layout)
    data = [[' '*15,' '*15,' '*15,' '*10,' '*10,' '*10,' '*10,' '*45,' '*10] for row in range(16)]

    #Main window layout
    layout = [
        [sg.FolderBrowse(target='-FOLDER-'), sg.Input(key='-FOLDER-', enable_events=True), 
        sg.Submit(), sg.Button('Fetch Comments', key='-FETCH-'), sg.Exit()],
        [sg.Table(data, headings=tabl_head, justification='center', select_mode='browse',
            key='-DATA-', num_rows=30, enable_events=True, bind_return_key=True, max_col_width=100)],
        [sg.Column(details_frame, expand_y=True, expand_x=True)]
        ]

    
    window = sg.Window('EndoView', layout, size=(1320,670), finalize=True)
    window['-DATA-'].bind('<Double-Button-1>', '+DBL+')
    window['-DATA-'].bind('<Return>', '+ENTER+')

    config = configparser.ConfigParser()
    config.read('endoview.ini')
    dd={}
    max_workouts = 0

    try:
        if 'cache' in config['endoview']:
            folder_path = config['endoview']['BackupFolder']
            window['-FOLDER-'].update(folder_path)
            with open('cache.pkl', 'rb') as f:
                dd = pickle.load(f)
            max_workouts = len(dd)
            with open('index.pkl', 'rb') as f:
                indx = pickle.load(f)
            updatetable(data, dd, window)
    except:
        pass

    while True:  # Event Loop of main window
        try: event, values = window.read(timeout=100) #trap for strange exception
        except _tkinter.TclError as err:
            #print(err)
            pass

        if event == sg.TIMEOUT_KEY:
            continue
        #print(event, values)
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        elif event == '-FETCH-':
            #test if endoworkouts.json file is present
            if os.path.isfile(folder_path+'/endoworkouts.json'):
                with open(folder_path+'/endoworkouts.json') as p:
                    comm = json.load(p)
            else:
                #request email and password
                email = sg.PopupGetText("Endo Email:")
                password = sg.PopupGetText("Endo Password:", password_char='*')
                if folder_path:
                    fldr = folder_path + '/'
                else:
                    fldr = ''
                #print(fldr)
                comm = fetchcomments(email, password, max_workouts, fldr)
            if comm is not None:
                updatecomments(dd, comm, indx)
            with open("cache.pkl", "wb") as write_file:
                pickle.dump(dd, write_file, pickle.HIGHEST_PROTOCOL)
            updatetable(data, dd, window)
        elif event == '-FOLDER-' or (event == 'Submit' and len(values['-FOLDER-'])>0):
            folder_path = values['-FOLDER-']
            #test if endoworkouts.json file is present
            # if os.path.isfile(folder_path+'/endoworkouts.json'):
            #     with open(folder_path+'/endoworkouts.json') as p:
            #         dd = json.load(p)
            #     print('Loading endoworkouts.json')
            #     distance_key='distance_km'
            #     duration_key='duration'
            #     speed_avg_key='speed_avg'
            # else:
            dd, indx = loadfull(folder_path)
            max_workouts = len(dd)
            #print('Loading backup! ')
            # we have processed database in memory - let's write cache and create config file
            config = configparser.ConfigParser()
            config['endoview'] = {}
            config['endoview']['Cache'] = 'Y' #indicate that we have cached data
            config['endoview']['BackupFolder'] = folder_path #save location of Endomondo backup
            with open('endoview.ini', 'w') as configfile:
                config.write(configfile)
            #now store cache to file system
            with open("cache.pkl", "wb") as write_file:
                pickle.dump(dd, write_file, pickle.HIGHEST_PROTOCOL)
            with open("index.pkl", "wb") as write_file:
                pickle.dump(indx, write_file, pickle.HIGHEST_PROTOCOL)
            updatetable(data, dd, window)
        elif event == '-DATA-':
            try:
                workout = dd[values['-DATA-'][0]]
                window['-SPORT-'].update(workout.get('sport'))
                window['-DATE-'].update(workout.get('date'))
                window['-STARTTIME-'].update(workout.get('time'))
                window['-DURATION-'].update(workout.get('duration'))
                window['-DISTANCE-'].update(workout.get('distance'))
                window['-PACE-'].update(workout.get('pace'))
                window['-ASC-'].update(workout.get('ascend_m'))
                window['-DESC-'].update(workout.get('descend_m'))
                window['-NOTE-'].update(workout.get('message'))
            except IndexError:
                pass
        elif event == '-DATA-+DBL+' or event == '-DATA-+ENTER+':
            try:
                #in case of double click or ENTER press on specific line - pop up detailed window
                workout = dd[values['-DATA-'][0]] # selected workout
                #prepare layout for detailed window
                #define sizes of the details window TODO: bind to desktop size
                win2_width = 1100
                win2_height = 100
                WIN2_HEIGHT_MAX = 700

                windetails = [
                                [
                                    FieldColumn("Sport: ", '-SPORT-', workout.get('sport')),
                                    FieldColumn("Date: ",'-DATE-', workout.get('date')),
                                    FieldColumn("Time: ", '-STARTTIME-', workout.get('time')),
                                    FieldColumn("Duration: ", '-DURATION-', workout.get('duration')),
                                    FieldColumn("Distance: ", '-DISTANCE-', workout.get('distance'))
                                ],
                                [
                                    FieldColumn("Pace: ", '-PACE-', workout.get('pace')),
                                    FieldColumn("Ascent: ", '-ASC-', workout.get('ascend_m')),
                                    FieldColumn("Descent: ", '-DESC-', workout.get('descend_m')),
                                    FieldColumn("Alt min: ", '-ALTMIN-', workout.get('altitude_min_m')),
                                    FieldColumn("Alt max: ", '-ALTMAX-', workout.get('altitude_max_m'))
                                ],
                                [
                                    FieldColumn("HR AVG: ", '-HAVG-', workout.get('heart_rate_avg_bpm')),
                                    FieldColumn("HR MAX: ", '-HMAX-', workout.get('heart_rate_max_bpm')),
                                    FieldColumn("Calories: ", '-CAL-', workout.get('calories_kcal')),
                                    FieldColumn("Cad AVG: ", '-CADAVG-', workout.get('cadence_avg_rpm')),
                                    FieldColumn("Cad MAX: ", '-CADMAX-', workout.get('cadence_max_rpm'))
                                ],
                                [
                                    FieldColumn("Speed AVG: ", '-SPAVG-', workout.get('speed')),
                                    FieldColumn("Speed MAX: ", '-SPMAX-', workout.get('speed_max')),
                                ]
                            ]
                msg = workout.get('message')
                lennote = 0 if msg is None else len(msg) #find out length of text note
                if lennote>0: # if there is note in workout - add text field and fill it with note
                    nlines = msg.count('\n')+1
                    nheight = int(lennote/150)+1
                    if nlines < nheight:
                        nlines = nheight
                    windetails += [[sg.Frame('Note', [[sg.Text(msg, key='-NOTE-', size=(int(win2_width/8), nlines))]])]]
                    win2_height += nlines*8+50 #extend height of the window

                #check if there are pictures posted to the workout and add layout to the window
                pict = workout.get('pictures')
                if pict is not None:
                    linewidth = 0
                    imgline = []
                    for i in range(0, len(pict)):
                    #  try:
                        try:
                            url = pict[i][1].get('picture')[0][0].get('url')
                            data, (imgwidth, imgheight) = get_img_data(folder_path+'/'+url, first=True)
                        except KeyError:
                            url = pict[i].get('picture_file')
                            data, (imgwidth, imgheight) = get_img_data(os.path.join(folder_path, 'Images', 
                                        os.path.split(url)[1]), first=True)
                        if linewidth + imgwidth > win2_width:
                            windetails += [imgline]
                            win2_height += imgheight+50
                            imgline = []
                            linewidth = 0
                        imgline.append(sg.Image(key='-IMAGE'+str(i)+'-', data=data))
                        linewidth += imgwidth
                    if imgline !=[]:
                        windetails += [imgline]
                        win2_height += imgheight+50
                    # except Exception as err:
                    #     print("Images exception: ", err)
                    #     break
                
                #create comments section
                comm_num = workout.get('num_comments')
                if comm_num !='':
                    try:
                        comment = workout.get('ecomments').get('data')
                    except AttributeError:
                        comment = workout.get('comments').get('data')
                    
                    for i in range(len(comment)):
                        comtext = comment[i]['text']
                        comh = int(len(comtext)/100)+1 #height of the comment cell to fit the comment
                        frame_layout = [[sg.Text(emoji.get_emoji_regexp().sub(r'',comment[i]['from']['name'])+':', size=(20, comh)), 
                                        sg.Text(emoji.get_emoji_regexp().sub(r'',comtext), size=(100, comh), pad=(0,0))]]
                        windetails += frame_layout
                        win2_height += 28 #TODO: add height depending on comment height

                win2_height = WIN2_HEIGHT_MAX if win2_height > WIN2_HEIGHT_MAX else win2_height

                win2layout = [[sg.Column(windetails, scrollable=True, vertical_scroll_only=True, size=(win2_width, win2_height))]]
                win2 = sg.Window('Workout detail', win2layout, finalize=True, modal=True)
                win2.bind('<Escape>', '+ESC+')
                win2.bind('<Return>', '+ENTER+')

                while True:  # Event Loop
                    ev2, val2 = win2.read(timeout=100) #timeout for debugger
                    if ev2 == sg.TIMEOUT_KEY:
                        continue
                    if ev2 == sg.WIN_CLOSED or ev2=='+ESC+' or ev2=='+ENTER+':
                        break
                win2.close()
                del win2layout
                del win2
                del windetails
            except IndexError as err:
                print(err)
                pass
    
    window.close()

if __name__ == "__main__":
    main()