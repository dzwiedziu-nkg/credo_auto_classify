"""
Rozpakowanie plików z pobranych JSON do PNG i przeprowadzenie ML.
"""
import os

from credo_cf.image.gray import convert_to_gray_scale

from ML_function import preprocessData,CNN_classifier,STD_classifier,preprocesDataSTD,preprocesDataBL,BL_classifier,BaseTrigger
import cv2
import json
import glob
import numpy as np
import psycopg2
import joblib
from joblib import dump, load
#import cpickle

from path_links import main_path,png_detections_path,good_detections_path

from io import BytesIO
from typing import List, Optional

from PIL import Image

from credo_cf import load_json, FRAME_CONTENT, X, Y, decode_base64, IMAGE, group_by_device_id, group_by_resolution, \
    group_by_timestamp_division, CROP_SIZE, encode_base64, store_png, DEVICE_ID, TIMESTAMP, ID, too_often, too_bright, \
    FRAME_DECODED

from settings import *


def load_parser(obj: dict, count: int, ret: List[dict]) -> Optional[bool]:
    if not obj.get(FRAME_CONTENT) or not obj.get(X) or not obj.get(Y):
        return False

    try:
        from credo_cf.image.image_utils import load_image, image_basic_metrics
        frame_decoded = decode_base64(obj.get(FRAME_CONTENT))
        pil = Image.open(BytesIO(frame_decoded))
        if pil.size == (60, 60) or pil.size == (64, 64) or pil.size == (128, 128):
            obj[IMAGE] = pil
            obj[CROP_SIZE] = pil.size
            return True

    except Exception as e:
        pass
    return False


def start_analyze(all_detections, log_prefix):
    print('%s  group by devices...' % log_prefix)
    by_devices = group_by_device_id(all_detections)
    print('%s  ... done' % log_prefix)

    dev_no = 0
    dev_count = len(by_devices.keys())

    for device_id, device_detections in by_devices.items():
        by_resolution = group_by_resolution(device_detections)
        for resolution, detections in by_resolution.items():
            dev_no += 1
            print('%s    start device %d of %d, device id: %s, resolution: %dx%d, detections count: %d' % (log_prefix, dev_no, dev_count, str(device_id), resolution[0], resolution[1], len(detections)))

            # try to merge hits on the same frame
            by_frame = group_by_timestamp_division(device_detections)
            reconstructed = 0
            for timestmp, in_frame in by_frame.items():
                if len(in_frame) <= 1:
                    continue

                image = None

                for d in reversed(in_frame):
                    if d.get(CROP_SIZE) == (60, 60):
                        if image is None:
                            image = Image.new('RGBA', (resolution[0], resolution[1]), (0, 0, 0))

                        cx = d.get(X) - 30
                        cy = d.get(Y) - 30
                        w, h = (60, 60)

                        image.paste(d.get(IMAGE), (cx, cy, cx + w, cy + h))

                        # fix bug in early CREDO Detector App: black filled boundary 1px too large
                        image.paste(image.crop((cx + w - 1, cy, cx + w, cy + h)), (cx + w, cy, cx + w + 1, cy + h))
                        image.paste(image.crop((cx, cy + h - 1, cx + w, cy + h)), (cx, cy + h, cx + w, cy + h + 1))
                        image.paste(image.crop((cx + w - 1, cy + h - 1, cx + w, cy + h)), (cx + w, cy + h, cx + w + 1, cy + h + 1))

                for d in in_frame:
                    if d.get(CROP_SIZE) == (60, 60):
                        cx = d.get(X) - 30
                        cy = d.get(Y) - 30
                        w, h = (60, 60)

                        hit_img = image.crop((cx, cy, cx + w, cy + h))
                        d[IMAGE] = hit_img
                reconstructed += 1
            print('%s    ... reconstructed frames: %d' % (log_prefix, reconstructed))


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


def ml(json_dict):
    global list_images_name, images, falki
    year_list = ["2021"]
    #Pętla po rok,dzien,miesiac - zapisuje detekcje po naszym starym filtrze wg danego dnia

    images = []
    list_images_name = []
    detect_dict = read_json_detections(json_dict)

    for d in json_dict:
        img = d.get(ID)
        n = np.asarray(d.get(IMAGE).convert('RGB'))
        # n = cv2.resize(n, (60,60), interpolation = cv2.INTER_AREA)
        size_xy = 60
        if n.shape == (64, 64, 3):
            n = n[2:2 + size_xy, 2:2 + size_xy]
        elif n.shape == (128, 128, 3):
            n = n[34:34 + size_xy, 34:34 + size_xy]
        # cv2.imshow("cropped", crop_img)
        # print(n.shape)
        list_images_name.append(str(img))
        images.append(n)

    detect_dict_final = ML_anallyze(images, list_images_name, detect_dict)
    json_dict_update = update_detections(json_dict, detect_dict_final)
    return detect_dict_final


def read_json_detections(detections):
    number = 10
    time = 60000

    dict_detect = {}
    json_dict = {"detections": []}

    list_devices = {}
    for detection in detections:
        device_id = detection["device_id"]
        if device_id not in list_devices:
            list_devices[device_id] = []
        list_devices[device_id].append(detection)

    for device_id in list_devices:
        print("\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
        print(device_id)
        print("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n")
        list_detections = []
        detections = list_devices[device_id]
        device_time = []
        too_often(detections, number, time)
        for detection in detections:
            team_id = detection["team_id"]
            user_id = detection["user_id"]

            device_time.append(int(detection["timestamp"] / 1000))
            record_gray = convert_to_gray_scale(detection, "LA")
            list_detections.append(record_gray)  # nasza lista detekcji z gray - all
        too_bright(list_detections, 70, 70)

        for detection in detections:
            id = str(detection["id"])
            if str(detection["good_bright"]) == "True":
                ocena = "0,signal"  # signal
            else:
                ocena = "1,artefact"  # artefact
            dict_detect[id] = {"anti-artefact": ocena}
            json_dict["detections"].append(detection)

    return dict_detect


def update_detections(json_dict,detect_dict_final):
    for detection in json_dict:
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



conn_string = 'host=%s port=%d dbname=%s user=%s password=%s sslmode=require' % (
    DB_HOST, DB_PORT, DB_DBNAME, DB_USER, DB_PASSWORD
)

conn = psycopg2.connect(conn_string)

cursor = conn.cursor()

# odczyt ID-ków klasyfikatorów, oraz ich typ
cursor.execute('SELECT id_classifier, id_classifier_type, classifier_name FROM classifiers')

classifiers = {}  # type: dict[str, dict[str, str]]

for row in cursor.fetchall():
    classifiers[row[2]] = {'id': row[0], 'type': row[1]}


for fn in glob.glob(ml_source + '*'):
    print('Load file: %s' % fn)
    detections, count, errors = load_json(fn, load_parser)
    print('... there are %d detections with size 60x60 or larger' % len(detections))

    if len(detections) > 0:
        print('... simple classify bu too_bright and too_often ...')
        start_analyze(detections, '')

        print('... ML classification ...')
        result = ml(detections)

        print('... upload hits to DB ...')
        images_list = []
        for d in detections:
            if d["metadata"]:
                metadata = json.loads(d["metadata"])
            else:
                metadata = {}

            values = (
                d['id'],
                d['timestamp'],
                d['time_received'],
                d['source'],
                d['visible'],

                d['device_id'],
                d['user_id'],
                d['team_id'],

                d['accuracy'],
                d['altitude'],
                d['latitude'],
                d['longitude'],
                d['provider'],

                d['frame_content'],
                d['height'],
                d['width'],
                d['x'],
                d['y'],

                metadata.get('max'),
                metadata.get('average'),
                metadata.get('blacks'),
                metadata.get('black_threshold'),
                metadata.get('ax'),
                metadata.get('ay'),
                metadata.get('az'),
                metadata.get('orientation'),
                metadata.get('temperature'),

                d['ML_score']
            )
            images_list.append(values)

        sql = 'INSERT INTO images(id, timestamp, time_received, source, visible, device_id, user_id, team_id, accuracy, altitude, latitude, longitude, provider, frame_content, height, width, x, y, metadata_max, metadata_average, metadata_blacks, metadata_black_threshold, metadata_ax, metadata_ay, metadata_az, metadata_orientation, metadata_temperature, ml_score) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
        cursor.executemany(sql, images_list)
        conn.commit()

        print('... upload classifications of hits to DB ...')
        classifications_list = []
        for _id, outs in result.items():
            for _class, value in outs.items():
                if _class == 'dobry_kandydat':
                    continue
                num, _type = value.split(',')
                if classifiers[_class]['type'] == 0 and _type == 'artefact':
                    num = 3
                values = (
                    _id,
                    classifiers[_class]['id'],
                    num
                )
                classifications_list.append(values)
        sql = 'INSERT INTO classifications(id, id_classifier, id_class) VALUES(%s, %s, %s)'
        cursor.executemany(sql, classifications_list)
        conn.commit()

    os.remove(fn)
    print('... file %s done and remove' % fn)
