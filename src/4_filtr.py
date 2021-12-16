"""
To jest czwarty etap - po skrypcie pingi.py
wreszcie nadszedl czas na filtrowanie detekcji.

Najpierw filtrujemy czasowo,
potem wykorzystamy klasyfikatory CREDO-ML
"""
from credo_cf.image.gray import convert_to_gray_scale
from credo_cf.classification.artifact.too_often import too_often
from credo_cf.classification.artifact.too_bright import too_bright

from add_function import set_start_end,check_file
import base64
import json
import traceback
import pickle
import numpy as np
import os

from path_links import main_path,outfile_path,raw_detections_path,png_detections_path,good_detections_path
#os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

file_list_detect = main_path+ 'file_detections_completed.txt'


team_user ={}#team_user{team_id:{users_id}}
user_team = {}
user_activity_pings = {}#{user_id{Month{Day{Device{id:2312,Premia:5,Detect=20,Work=2.04}}}}
#wczytywanie słownikow

month_name={"01":"January","02":"February","03":"March","04":"April","05":"May","06":"June",
            "07":"July","08":"August","09":"September","10":"October","11":"November","12":"December"}
try:
    infile = open(outfile_path + "team_user", 'rb')
    team_user =(pickle.load(infile))
    infile.close()
except:
    print("nie wczytałem: team_user")

try:
    infile = open(outfile_path + "user_activity_pings", 'rb')
    user_activity_pings = (pickle.load(infile))
    infile.close()
except:
    print("nie wczytałem: user_activity_pings")
try:
    infile = open(outfile_path + "user_team", 'rb')
    user_team = (pickle.load(infile))
    infile.close()
except:
    print("nie wczytałem: user_team")

list_detections={}
user_in_teams = {"team_id":{}}#list users in teams
teams_score = {"team_id":{}}#dict teams score per day


def read_detections():
    """
    file listing, sending to load_json (file_name),
    we only receive those detections that have the "visible" state
    """
    year_list = ["2021"]
    for year in year_list:
        ypath = raw_detections_path + year + "/"
        months = [f for f in os.listdir(ypath) if os.path.isdir(os.path.join(ypath, f))]
        for month in months:
            mpath = ypath + str(month) + "/"
            days = [f for f in os.listdir(mpath) if os.path.isdir(os.path.join(mpath, f))]
            for day in days:
                dpath = mpath + str(day) + "/"
                print("***************")
                print(year, month, day)
                print("***************")
                files_day = [f for f in os.listdir(dpath) if os.path.isfile(os.path.join(dpath, f))]

                dict = []
                for file in files_day:
                    if ".json" in str(file):
                        current_file = dpath + file
                        file_name = file.split(".")
                        file_name = file_name[0]  # [0] - name file, [1] - ".json"
                        data = [str(year) ,str(month),str(day)]
                        start_analyze(current_file, file_name, data)

    #zapisanie slownika aktywnosci
    user_activity2 =[]

    for user in user_activity_pings:
        stan = 0
        activity_days=0
        userek = {"user_id": user,"detections":{}}
        for rok in user_activity_pings[user]:
            if rok not in userek["detections"]:
                userek["detections"][rok]={}
            for miesiac in user_activity_pings[user][rok]:
                miesiacstr=month_name[miesiac]
                if miesiacstr not in userek["detections"][rok]:
                    userek["detections"][rok][miesiacstr]=[]
                for dzien in user_activity_pings[user][rok][miesiac]:
                    print(user,dzien)
                    record = user_activity_pings[user][rok][miesiac][dzien]
                    if dzien =="01":
                        activity_days = 0
                    for devices in record:
                        activity_days = user_activity_pings[user][rok][miesiac][dzien][devices]["activity_days"]
                        stan=1
                        try:
                            try:
                                good = record[devices]["good"]
                                bad = record[devices]["bad"]
                                too_often = record[devices]["too_often"]
                            except:
                                good=0
                                bad = 0
                                too_often = 0
                            #print(element)
                            element = {"dzien":dzien,"device": devices,"activity_days": activity_days,"premia":0,
                                    "all": record[devices]["detect"],"work": record[devices]["work"],
                                    "good": good,"bad": bad ,
                                    "too_often": record[devices]["too_often"],"team_id":record[devices]["team_id"]}
                        except:
                            element = {"dzien": dzien, "device": devices, "activity_days": activity_days, "premia": 0,
                                       "all": 0, "work": int(record[devices]["work"]/3600),
                                       "good": 0, "bad": 0,
                                       "too_often": 0, "team_id": record[devices]["team_id"]}
                        userek["detections"][rok][miesiacstr].append(element)
            #if stan ==1:#dodajemu usera gdy mial conajmniej 1 dzien w ktorym pracowal 1 godz
            user_activity2.append(userek)


    with open(outfile_path + "user_activity_filtr.json", 'w') as json_file:
        dictionary = {'users': [user_activity2]}
        #print(dictionary)
        json.dump(dictionary, json_file, indent=4)

    with open(outfile_path + "user_activity_filtr2.json", 'w') as json_file:
        json.dump(user_activity2, json_file, indent=4)

    outfile = open(outfile_path + "user_activity_filtr", 'wb')
    pickle.dump(user_activity_pings, outfile)
    outfile.close()

    outfile = open(outfile_path + "user_activity_filtr2", 'wb')
    pickle.dump(user_activity2, outfile)
    outfile.close()

    #zapisanie csv
    # a=1
    # file = open(outfile_path + "users_stat.csv", "w")
    # file.write("user_id,miesiac,dzien,device_id,time_work,time_work_ping,time_work_device\n")
    # for user_id in user_activity:
    #     if a==1 and user_id==31553:
    #         for miesiac in user_activity[user_id]:
    #             for dzien in user_activity[user_id][miesiac]:
    #                 for device_id in user_activity[user_id][miesiac][dzien]:
    #                     element = user_activity[user_id][miesiac][dzien][device_id]
    #                     try:
    #                         file.write("%s,%s,%s,%s,%s,%s,%s\n" % (user_id, miesiac, dzien,device_id,element["work"],element["work_ping"],element["work_detect"]))
    #                     except:
    #                         file.write("%s,%s,%s,%s,%s,%s,%s\n" % (user_id, miesiac, dzien,device_id,element["work"],0,0))
    #
    #
    # file.close()


def count_time_work(device_time):
    x = sorted(device_time)
    xdiff = np.diff(x)
    mean_detect = sum(xdiff)/len(xdiff)
    #print("dane:",mean_detect)
    time_data = sum(i for i in xdiff if i<mean_detect*2 and i<2*60*60 or i<mean_detect and i>10*60)
    #print("dane:", time_data)
    if mean_detect<10*(60*60):
        time_data+=mean_detect
    return time_data/(60*60)#w minutach


def start_analyze(current_file,file_name,data):
    print(current_file)

    location = data[0] + "/" + data[1] + "/" + data[2]
    number = 10
    time = 60000
    good_time_list = []
    try:
        with open(current_file) as json_file:
            json_load = json.load(json_file)
        list_devices ={}

        for detection in json_load['detections']:
            device_id = detection["device_id"]
            if device_id not in list_devices:
                list_devices[device_id]=[]
            list_devices[device_id].append(detection)

        for device_id in list_devices:

            print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
            print(device_id)
            print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
            list_detections = []
            detections = list_devices[device_id]
            device_time=[]
            for record in detections:
                team_id = record["team_id"]
                user_id = record["user_id"]

                device_time.append(int(record["timestamp"]/1000))
                record_gray = convert_to_gray_scale(record, "LA")
                list_detections.append(record_gray)  # nasza lista detekcji z gray - all

            #print(data[0],data[1],data[2])
            #print(user_activity_pings[user_id][data[0]][data[1]][data[2]])
            #test = user_activity[user_id][data[1]][data[2]][device_id]
            try:
                time_work_ping=int((user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["work"]/(60*60))+0.4)#czas pracy w godzinach z pingów
            except:
                time_work_ping=0
                print("error z",time_work_ping)
            time_work = time_work_ping  # domyslnie bierzemy z pingów
            time_work_detections = 0
            if len(device_time)>1:
                detekcji = len(device_time)
                try:
                    detekcjigodzinowych= detekcji/int(time_work_ping)
                except:
                    detekcjigodzinowych = 0

                time_work_detections = count_time_work(device_time)#czas pracy w godzinach z detekcji

                if time_work_detections>1+time_work:
                    time_work = time_work_detections
                    if time_work>24:
                        time_work=24
                if time_work_ping > 24:
                    time_work = 24


            #ODKOMENTOWAC GDY ZACZNIE ALL DZIALAC
            if user_id not in user_activity_pings:
                user_activity_pings[user_id]={}
            if data[0] not in user_activity_pings[user_id]:
                user_activity_pings[user_id][data[0]]={}

            if data[1] not in user_activity_pings[user_id][data[0]]:
                user_activity_pings[user_id][data[0]][data[1]]={}
            if data[2] not in user_activity_pings[user_id][data[0]][data[1]]:
                user_activity_pings[user_id][data[0]][data[1]][data[2]]={}
            if device_id not in user_activity_pings[user_id][data[0]][data[1]][data[2]]:
                user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]={
                    "activity_days": 1,
                    "detect": 0,
                    "work": 0,
                    "team_id": team_id}
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["work_ping"] = round(time_work_ping,2)
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["work_detect"] = round(time_work_detections,2)
            artefact, good_time = too_often(list_detections, number, time)  # yes - artefact, no - detection with good time

            good, bad = too_bright(good_time, 70, 70)
            print(device_id,len(detections),len(good),len(bad),len(artefact),len(good_time))
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["good"]=len(good)#ser_activity[user_id][miesiac][dzien][device_id]["good"]=good
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["bad"] = len(bad)
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["too_often"] = len(artefact)
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["detections"] = len(detections)
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["team_id"] = team_id
            user_activity_pings[user_id][data[0]][data[1]][data[2]][device_id]["work"] = int(time_work)

            if len(good_time) > 0:
                for elementy in good_time:
                    del elementy["gray"]
                    good_time_list.append(elementy)
                save_png(good_time,location)

    except Exception:
        traceback.print_exc()
        print("error with read file: ", file_name)
        f = open(main_path + "error_read_file.txt", "a")
        f.write(file_name + ".json\n")
        f.close()

    #zapisanie tylko dobrych detekcji czasowo
    if len(good_time_list) > 0:
        os.makedirs(good_detections_path +location,exist_ok=True)
        with open(good_detections_path +location+"/"+file_name+".json", 'w') as json_file:
            dictionary = {'detections': good_time_list}
            #print(dictionary)
            json.dump(dictionary, json_file, indent=4)


def save_png(good_time_detections,location):
    for detection in good_time_detections:
        img = detection["frame_content"]
        name=detection["id"]
        obrazek = img.encode('ascii')

        os.makedirs(png_detections_path+ location, exist_ok=True)
        adres=png_detections_path+ location+"/"+str(name)+".png"
        #print("img adres: ",adres)
        with open(adres, "wb") as fh:
            fh.write(base64.decodebytes(obrazek))

def main():
    global start, stop
    start,stop = set_start_end("2021-10-18 00:00","2022-06-13 12:00")

    read_detections()
    # update_teams_score()


if __name__ == '__main__':
    main()