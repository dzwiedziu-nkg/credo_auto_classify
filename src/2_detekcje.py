"""
To jest drugi etap - po skrypcie zespoly.py
Czytamy plik team_update.csv wyciagamy Id_api
potem szukamy w detekcjach rekordów zawierających team_id jakie posiadamy
na koniec te dane zapisujemy rozdzielajac na dni,
Przy okazji tworzymy slownik uzytkownikow w zespole oraz dniową aktywność
detections / pings /
"""

from add_function import set_start_end
import csv
import json
import os
from datetime import datetime
import time
import pickle

from path_links import main_path,team_file,outfile_path,detections_path,user_mapping

file_list_detect = main_path+ 'file_detections_completed.txt'
raw_detections_path = main_path+"detections/raw/"


os.makedirs(outfile_path,exist_ok=True)
team_dict={}
team_user ={}#team_user{team_id:{users_id}}
user_team = {}
user_activity = {}#{user_id{Month{Day{Device{id:2312,Premia:5,Detect=20,Work=2.04}}}}
#wczytywanie słownikow
# try:
#     infile = open(outfile_path + "team_user", 'rb')
#     team_user =(pickle.load(infile))
#     infile.close()
# except:
#     print("nie wczytałem: team_user")

try:
    infile = open(outfile_path + "user_activity", 'rb')
    user_activity = (pickle.load(infile))
    infile.close()
except:
    print("nie wczytałem: user_activity")
try:
    infile = open(outfile_path + "user_team", 'rb')
    user_team = (pickle.load(infile))
    infile.close()
except:
    print("nie wczytałem: user_team")

list_detections={}

def read_team():
    with open(team_file, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                #print(f'Column names are {", ".join(row)}')
                line_count += 1
            #print(f'Id base: {row["Id_base"]} is Team name {row["Name"]}.')
            team_dict[row["Id_api"]]={"id_base":row["Id_base"],"name":row["Name"]}
            if row["Id_api"] not in team_user:
                print("nie ma zespołu ",row["Id_api"],"w team_user - dodam")
                team_user[row["Id_api"]] = {"users":[]}
            line_count += 1
        #print(f'Processed {line_count} lines.')

def check_file(file_name):
    """
    :param file_name: checked the file name
    :param file_list: file with a list of files that have already been checked
    :return:
    """
    file_was_read = 0  # 0 - no, 1 - yes
    if str(os.path.isfile(file_list_detect)) == "True":
        f = open(file_list_detect, "r")
        for line in f:
            line = line.rstrip("\n")
            if str(line) == str(file_name):
                #print(line, "was readed, we don't read this file")
                file_was_read = 1
        f.close()
    return file_was_read

def read_detections():
    list_file_json = sorted(os.listdir(detections_path))
    list_file_json = list_file_json
    index = 0

    for json_file in range(len(list_file_json)):
        file_was_read = check_file(list_file_json[json_file])

        if file_was_read == 0:
            current_file = detections_path + list_file_json[json_file]
            file_name = list_file_json[json_file].split(".")
            file_name = file_name[0]  # [0] - name file, [1] - ".json"
            print(index+1, "/", len(list_file_json), file_name)

            seperate(current_file, file_name)
        index += 1


    #zapisanie slownika aktywnosci
    with open(outfile_path + "user_activity.json", 'w') as json_file:
        dictionary = {'users': [user_activity]}
        json.dump(dictionary, json_file, indent=4)

    outfile = open(outfile_path + "user_activity", 'wb')
    pickle.dump(user_activity, outfile)
    outfile.close()

    #zapisanie slownika team_user


    for team in team_user:
        tmp = sorted(team_user[team]["users"])
        team_user[team]["users"] = tmp
    with open(outfile_path + "team_user.json", 'w') as json_file:
        dictionary = {'team': [team_user]}
        json.dump(dictionary, json_file, indent=1)

    outfile = open(outfile_path + "team_user", 'wb')
    pickle.dump(team_user, outfile)
    outfile.close()

    #zapisanie slownika user_team
    with open(outfile_path + "user_team.json", 'w') as json_file:
        dictionary = {'users': [user_team]}
        json.dump(dictionary, json_file, indent=1)

    outfile = open(outfile_path + "user_team", 'wb')
    pickle.dump(user_team, outfile)
    outfile.close()

def seperate(current_file,file_name):
    """
    Czytaj pliki,detekcje, rozdziel do slownikow
    :param current_file:
    :param file_name:
    :return:
    """
    with open(current_file) as json_file:
        json_load = json.load(json_file)

    temp_dict = {}
    json_path = detections_path + file_name
    with open(json_path+".json") as json_file:
        json_load = json.load(json_file)
    for detection in json_load['detections']:
        device_id = detection["device_id"]
        user_id = detection["user_id"]
        team_id = str(detection["team_id"])
        if team_id in team_dict:
            if str(detection["visible"]) == "True":
                timestamp = int(detection["timestamp"]/1000)
                #print(timestamp)
                if timestamp >start and timestamp<stop:#1603238400: #21.10.2020
                    if user_id not in team_user[team_id]["users"]:
                        team_user[team_id]["users"].append(user_id)
                    if user_id not in user_activity:
                        user_activity[user_id]={}
                    if user_id not in user_team:
                        user_team[user_id]=team_id
                    data_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    dt = time.strptime(str(data_str), '%Y-%m-%d %H:%M:%S')
                    data_str2 = datetime.fromtimestamp(timestamp-(24*60*60)).strftime('%Y-%m-%d %H:%M:%S')
                    dt_yesterday = time.strptime(str(data_str2), '%Y-%m-%d %H:%M:%S')#wczoraj
                    M,D = str(dt.tm_mon),str(dt.tm_mday)
                    M_y,D_y = str(dt_yesterday.tm_mon),str(dt_yesterday.tm_mday)
                    if int(M)<10:
                        M = "0"+str(M)
                    if int(D)<10:
                        D = "0" + str(D)

                    if int(M_y)<10:
                        M_y = "0"+str(M_y)
                    if int(D_y)<10:
                        D_y = "0" + str(D_y)

                    if M not in user_activity[user_id]:
                        user_activity[user_id][M]={}
                    if D not in user_activity[user_id][M]:
                        user_activity[user_id][M][D]={}
                    premia=1
                    if int(D) !=1:
                        try:
                            if device_id in user_activity[user_id][M_y][D_y]:
                                premia = user_activity[user_id][M_y][D_y][device_id]["activity_days"] +1
                        except:
                            premia=1
                    if device_id not in user_activity[user_id][M][D]:
                        user_activity[user_id][M][D][device_id]={"activity_days":premia,"detect":0,"work":0.00}


                    user_activity[user_id][M][D][device_id]["detect"]+=1

                    tm_data = ("%s/%s/%s/"%(dt.tm_year,M,D))
                    if dt.tm_yday not in temp_dict:
                        print("tworze date,",dt.tm_yday)
                        temp_dict[dt.tm_yday] = {}
                        temp_dict[dt.tm_yday]["string"] = tm_data
                        temp_dict[dt.tm_yday]["detections"]=[]

                    temp_dict[dt.tm_yday]["detections"].append(detection)

    #zapisanie detekcji
    for days in temp_dict:
        #print(len(temp_dict[days]["detections"]))
        if len(temp_dict[days]["string"]) > 0:
            path_save = raw_detections_path +temp_dict[days]["string"]
            os.makedirs(path_save, exist_ok=True)
            #print(path_save)
            outfile = open(path_save + file_name, 'wb')
            pickle.dump(temp_dict[days]["detections"], outfile)
            outfile.close()


    f = open(file_list_detect, "a")
    f.write(file_name + ".json\n")
    f.close()

def join_files():
    #files = os.listdir(save_path)
    path = raw_detections_path
    files = [ f for f in os.listdir(path) if os.path.isdir(os.path.join(path,f))]

    for year in files:
        ypath = path+str(year)+"/"
        months = [f for f in os.listdir(ypath) if os.path.isdir(os.path.join(ypath, f))]
        for month in months:
            mpath = ypath + str(month) + "/"
            days = [f for f in os.listdir(mpath) if os.path.isdir(os.path.join(mpath, f))]
            for day in days:
                dpath = mpath + str(day) + "/"
                print(dpath)
                files_day = [f for f in os.listdir(dpath) if os.path.isfile(os.path.join(dpath, f))]
                #print(files_day)
                dict = []
                for file in files_day:
                    if ".json" not in str(file):
                        infile = open(dpath+file, 'rb')
                        dict.append(pickle.load(infile))
                        infile.close()
                dict_detections = []
                for id in range(len(dict)):
                    dict_detections +=dict[id]
                start = int(datetime(int(year), int(month), int(day), 0, 0).timestamp())
                stop = int(datetime(int(year), int(month), int(day), 0, 0).timestamp())
                file_name = "export_"+str(start)+"000_"+str(stop)+"000.json"
                with open(dpath + file_name, 'w') as json_file:
                    dictionary = {'detections': []}
                    dictionary['detections'] = dict_detections
                    json.dump(dictionary, json_file, indent=4)

def user_name():
    user_name_dict=[]
    with open(user_mapping) as json_file:
        json_load = json.load(json_file)
    for user in json_load['users']:
        id = user["id"]
        if id in user_team:
            team_id = user_team[id]
            team_name = team_dict[team_id]["name"]
            team_id_base = team_dict[team_id]["id_base"]
            username = user["username"]
            display_name = user["display_name"]
            user_name_dict.append({"id":id, "team_id":team_id,"team_name":team_name,"team_id_base":team_id_base,"username":username,"display_name":display_name})


    with open(outfile_path + "user_name.json", 'w') as json_file:
        dictionary = user_name_dict
        json.dump(dictionary, json_file, indent=1)


def main():
    global start, stop
    start, stop = set_start_end("2021-10-18 00:00", "2022-06-13 12:00")

    read_team()
    print(team_dict)
    read_detections()
    join_files()
    user_name()

if __name__ == '__main__':
    main()