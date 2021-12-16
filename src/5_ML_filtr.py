"""
Piąty etap. Po wyodrebnieniu dobrze czasowo detekcji angażujemy do oceny detekcji modele ML (CNN, STD,baseline)
Finalnie oceniamy szanse % na to czy dany obraz jest sygnałem
"""
import os
from ML_function import preprocessData,CNN_classifier,STD_classifier,preprocesDataSTD,preprocesDataBL,BL_classifier,BaseTrigger
import cv2
import json
import glob
import joblib
from joblib import dump, load
#import cpickle

from path_links import main_path,png_detections_path,good_detections_path

#ML MODELE
#DWUKLASOWE MODELE - WSZYSTKIE
model_list_CNN = {'CNN_small_w0':(0,),'CNN_big_w0':(0,),
                  'CNN_small_w2':(2,),'CNN_big_w2':(2,),
                  'CNN_small_w0_2':(0,2,),'CNN_big_w0_2':(0,2,),
                  'CNN_small_w2_10':(2,4,6,8,10,),'CNN_big_w2_10':(2,4,6,8,10,),
                  'CNN_small_w20':(20,),'CNN_big_w20':(20,),
                  'CNN_small_w2_20':(2,4,6,8,10,12,14,16,18,20,),'CNN_big_w2_20':(2,4,6,8,10,12,14,16,18,20,),
                  'CNN_small_raw':('raw',),'CNN_big_raw':('raw',)}

#BASE
model_list_baseline = ['baseline','baseline_knn','baseline_rf']
#CZTEROKLASOWE - PROBLEM ZGODNOSCI ORAZ MASZYNY
model_list_STD= ['etc','bagsvc','gbc','knn','mlp','nsv','ovo_mlp','ovo_svm','ovr_mlp','rf','svm','vot']


def read_detections():
    global list_images_name, images, falki
    year_list = ["2021"]
    #Pętla po rok,dzien,miesiac - zapisuje detekcje po naszym starym filtrze wg danego dnia
    for year in year_list:
        ypath = png_detections_path + year + "/"
        months = [f for f in os.listdir(ypath) if os.path.isdir(os.path.join(ypath, f))]
        for month in months:
            mpath = ypath + str(month) + "/"
            days = [f for f in os.listdir(mpath) if os.path.isdir(os.path.join(mpath, f))]
            for day in days:
                print("***************")
                print(year, month, day)
                print("***************")

                images = []
                list_images_name = []
                location = year + "/" + month + "/" + day

                detect_dict,json_dict,file_name = read_json_detections(location)


                for img in glob.glob(png_detections_path + location + "/*.png"):
                    n = cv2.imread(img)
                    #n = cv2.resize(n, (60,60), interpolation = cv2.INTER_AREA)
                    size_xy=60
                    n = n[2:2 + size_xy, 2:2 + size_xy]
                    #cv2.imshow("cropped", crop_img)
                    #print(n.shape)
                    img = img.split(location + '/')
                    img = img[1].replace(".png","")
                    list_images_name.append(img)
                    images.append(n)

                detect_dict_final = ML_anallyze(images,list_images_name,detect_dict)
                json_dict_update = update_detections(json_dict,detect_dict_final)
                file_names = file_name.replace(".json","")
                with open(good_detections_path+location+"/"+ file_names+"_final.json", 'w') as json_file:
                    dictionary = {"detections":[detect_dict_final]}
                    json.dump(dictionary, json_file, indent=4)


                with open(good_detections_path+location+"/"+ file_names+"_update.json", 'w') as json_file:
                    dictionary = json_dict_update
                    json.dump(dictionary, json_file, indent=4)

def read_json_detections(location):
    pathes = good_detections_path+location+"/"
    files_day = [f for f in os.listdir(pathes) if os.path.isfile(os.path.join(pathes, f))]
    dict_detect = {}
    json_dict = {"detections": []}
    for file in files_day:
        if ".json" in str(file) and "final.json" not in str(file) and "update.json" not in str(file):
            file_name=file
            current_file = pathes + file

            with open(current_file) as json_file:
                json_load = json.load(json_file)

            for detection in json_load['detections']:
                id = str(detection["id"])
                if str(detection["good_bright"]) == "True":
                    ocena = "0,signal" #signal
                else:
                    ocena = "1,artefact" #artefact
                dict_detect[id]={"anti-artefact":ocena}
                json_dict["detections"].append(detection)

    return dict_detect,json_dict,file_name

def update_detections(json_dict,detect_dict_final):
    for detection in json_dict["detections"]:
        id = str(detection["id"])
        if id in detect_dict_final:
            score = detect_dict_final[id]["dobry_kandydat"]
            detection["ML_score"] = score
    return json_dict

def ML_anallyze(images,list_images_name,detect_dict):
    # DWUKLASOWE - CNN
    for model in model_list_CNN:#model_list_CNN_test:
        falki=model_list_CNN[model]
        feature_array = preprocessData(data=(images), wavelets=falki)
        #print("elementów: ",len(feature_array))

        if feature_array.size >1:
                try:
                    print(model)
                    # print("feature_array: ", feature_array.shape)
                    tmp = CNN_classifier(model, list_images_name, feature_array)
                    for i in range(len(tmp)):
                        detect_dict[tmp.loc[i]['Hit ID']][tmp.loc[i]['Classifier']]=int(tmp.loc[i]['Class'])


                except Exception as e:

                    print(e)
                    print("cos nie tak")

        else:
            print("feature_array nie jest prawidłowy")

    print("&&&&&&&&  STD MODELS  &&&&&&&")
    feature_array2 = preprocesDataSTD(images) #Dla STD
    for model in model_list_STD:
        print(model)
        try:
            tmp = STD_classifier(model,list_images_name,feature_array2)
            for i in range(len(tmp)):
                detect_dict[tmp.loc[i]['Hit ID']][tmp.loc[i]['Classifier']]=int(tmp.loc[i]['Class'])


        except Exception as e:
            print("error")
            print(e)

    print("&&&&&&&&  BASELINE MODELS  &&&&&&&")
    feature_arrayBL = preprocesDataBL(images)  # Dla baseline
    for model in model_list_baseline:
        print(model)
        try:
            tmp = BL_classifier(model, list_images_name, feature_array2)
            for i in range(len(tmp)):
                detect_dict[tmp.loc[i]['Hit ID']][tmp.loc[i]['Classifier']] = int(tmp.loc[i]['Class'])


        except Exception as e:
            print(e)

    anty,ML = 0,0
    for element in detect_dict:
        ocena = []
        #0 - sygnał, 1 -artefakt
        for klasyfikator in detect_dict[element]:
            value_class=-1#nie ustawiony
            if klasyfikator in model_list_CNN or klasyfikator in model_list_baseline:
                if detect_dict[element][klasyfikator]==0:
                    value_class = str(detect_dict[element][klasyfikator])+",signal"
                else:
                    value_class = str(detect_dict[element][klasyfikator])+",artefact"

            if klasyfikator in model_list_STD:
                if detect_dict[element][klasyfikator]<3:
                    value_class = str(detect_dict[element][klasyfikator])+",signal"
                else:
                    value_class = str(detect_dict[element][klasyfikator])+",artefact"

            if klasyfikator == "anti-artefact":
                value_class = detect_dict[element][klasyfikator]

            detect_dict[element][klasyfikator] = value_class
            if value_class !=-1:
                ocena.append(value_class)

        score = ((ocena.count("0,signal")+ocena.count("1,signal")+ocena.count("2,signal"))/len(ocena))*100
        detect_dict[element]["dobry_kandydat"]= round(score,2)
        if score>80: #im ocena bliższa 0 tym wieksza szansa na sygnał, im bliżej 1 tym wieksza szansa na artefact
            ML+=1
        if detect_dict[element]["anti-artefact"]==0:
            anty+=1

    print(anty,ML)

    return(detect_dict)



def main():
    read_detections()


if __name__ == '__main__':
    main()