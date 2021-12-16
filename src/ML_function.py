"""
większość pochodzi ze skryptów stworzonych przez zespół CREDO-ML,

https://github.com/olafbar/notebooks_classifiers/blob/main/CNN_classifier.ipynb
by przetestować preprocesing na detekcjach z IOS

"""
from sklearn.base import BaseEstimator
from sklearn.base import ClassifierMixin
from keras.models import load_model
import mahotas
import numpy as np
import pandas as pd
import joblib

from joblib import dump, load
#sciezka do katalogu gdzie masz wyuczone modele - modele powinny uczyc się na maszynie na ktorej bedzie odpalane
#inaczej nie jest optymalne, Olaf nie podesłał połowy skryptów
classifers_path ="/media/no_backup/nkg/projects/pk/credo/classify_ml/src/Modele/"

#DLA CNN
def preprocessData(data, wavelets=(2,), verbose=True):
    images = data
    features = []
    bl_images = []
    th_images = []

    for img in images:
        img = img.astype('int32')
        blackwhite = img[:, :, 0] + img[:, :, 1] + img[:, :, 2]
        bl_images.append(blackwhite.copy())

        threshold = blackwhite.mean() + blackwhite.std() * 5
        threshold = threshold if threshold < 100 else 100

        mask = np.where(blackwhite > threshold, 1, 0)
        blackwhite = blackwhite * mask

        th_images.append(blackwhite.copy())

        # Transform using Dx Wavelets to obtain transformed images

        img_x,img_y,img_z = img.shape
        # print("blackwhite: ",blackwhite.shape)
        # print(img_x,img_y,img_z)#nie wiemy jakie rozmiary beda
        layers = {
            'raw': img.reshape(img_x, img_y, 3),
            0: blackwhite.reshape(img_x, img_y, 1),
            2: mahotas.daubechies(blackwhite, 'D2').reshape(img_x, img_y, 1),
            4: mahotas.daubechies(blackwhite, 'D4').reshape(img_x, img_y, 1),
            6: mahotas.daubechies(blackwhite, 'D6').reshape(img_x, img_y, 1),
            8: mahotas.daubechies(blackwhite, 'D8').reshape(img_x, img_y, 1),
            10: mahotas.daubechies(blackwhite, 'D10').reshape(img_x, img_y, 1),
            12: mahotas.daubechies(blackwhite, 'D12').reshape(img_x, img_y, 1),
            14: mahotas.daubechies(blackwhite, 'D14').reshape(img_x, img_y, 1),
            16: mahotas.daubechies(blackwhite, 'D16').reshape(img_x, img_y, 1),
            18: mahotas.daubechies(blackwhite, 'D18').reshape(img_x, img_y, 1),
            20: mahotas.daubechies(blackwhite, 'D20').reshape(img_x, img_y, 1)
        }

        #print(layers)
        # tt = np.concatenate((t02, t04, t06, t08), axis=2)
        out = np.concatenate(tuple(map(layers.__getitem__, wavelets)), axis=2)

        features.append(out)

    feature_array = np.array(features)

    if verbose:
        print(feature_array.shape)

    return (feature_array)



def CNN_classifier(classifier,list_images_name,feature_array):
    #classifier = 'CNN_small_raw'
    #feature_array = preprocessData(data=(images), wavelets=falki)

    try:
        model = load_model(classifers_path + classifier + '.h5')
    except:
        model = load_model(classifers_path + classifier + '.pkl')


    y_pred2 = np.argmax(model.predict(feature_array), axis=1)
    for i in range(2):
        count = sum(map(lambda x: x == i, y_pred2))
        print(i, count)

    classifiers = [classifier for x in range(len(y_pred2))]
    df = pd.DataFrame({
        'Classifier': classifiers,
        'Hit ID': list_images_name,
        'Class': y_pred2
    })

    return df

#DLA STD
def preprocesDataSTD(list_images_img):
    """
    Przygotowanie obrazów dla modeli STD
    :param list_images_img: lista obrazów orginalnych
    :return: feature_array2 - zbiór do anali dla modeli STD
    """
    images = list_images_img
    rows, cols, _ = images[0].shape
    radius = np.sqrt((rows / 2) ** 2 + (cols / 2.) ** 2)
    features2 = []
    for img in images:
        blackwhite = img[:, :, 0] + img[:, :, 1] + img[:, :, 2]
        threshold = blackwhite.mean() + blackwhite.std() * 5
        threshold = threshold if threshold < 100 else 100
        mask = np.where(blackwhite > threshold, 1, 0)
        blackwhite = blackwhite * mask
        zm = mahotas.features.zernike_moments(blackwhite, radius, degree=8, cm=(rows / 2., cols / 2.))
        zm = np.hstack([zm, blackwhite.mean()])
        features2.append(zm)
    feature_array2 = np.array(features2)

    return feature_array2

def STD_classifier(classifier,list_images_name,feature_array2):
    """
    Klasyfikacja obrazów modelami STD
    :param classifier: model jaki ma być użyty
    :param list_images_name: nazwa obrazów
    :param feature_array2: obrazy przygotowane przez inną funkcje
    :return: df - wynik analizy konkretnego modelu
    """
    pkl_filename = classifers_path + classifier + '.pkl'
    scaler_filename = classifers_path + classifier + '_scaler.pkl'

    # print(pkl_filename,scaler_filename)


    clf1 = load(pkl_filename)
    scaler2 = load(scaler_filename)
    X_std2 = scaler2.transform(feature_array2)
    y_pred2 = clf1.predict(X_std2)
    # for i in range(4):
    #     count = sum(map(lambda x: x == i, y_pred2))
    #     print(i, count)

    classifiers = [classifier for x in range(len(y_pred2))]
    df = pd.DataFrame({
        'Classifier': classifiers,
        'Hit ID': list_images_name,
        'Class': y_pred2
    })

    return df


#DLA baseline
def preprocesDataBL(list_images_img, verbose = True):
    images = list_images_img

    features = []
    bl_images = []
    th_images = []

    for img in images:
        img = img.astype('int32')

    blackwhite = img[:, :, 0] + img[:, :, 1] + img[:, :, 2]

    threshold = blackwhite.mean() + blackwhite.std() * 5
    threshold = threshold if threshold < 100 else 100

    mask = np.where(blackwhite > threshold, 1, 0)
    blackwhite = blackwhite * mask

    # feature #1
    num_pixels_over_th = np.sum(mask)

    # feature #2
    total_luminosity_over_th = np.sum(blackwhite)

    out = (num_pixels_over_th, total_luminosity_over_th)
    features.append(out)

    feature_array = np.array(features)

    if verbose:
        print(feature_array.shape)

    return (feature_array)


def BL_classifier(classifier,list_images_name,feature_array):
    pkl_filename = classifers_path + classifier + '.pkl'
    clf1 = load(pkl_filename)

    y_pred2 = clf1.predict(feature_array)

    for i in range(2):
        count = sum(map(lambda x: x == i, y_pred2))
        print(i, count)

    classifiers = [classifier for x in range(len(y_pred2))]
    df = pd.DataFrame({
        'Classifier': classifiers,
        'Hit ID': list_images_name,
        'Class': y_pred2
    })

    return df


class BaseTrigger(BaseEstimator, ClassifierMixin):
    def __init__(self):
        pass

    def fit(self, X, y):
        #         compute minimal luminosity for artefacts and maximal luminosity for signals
        #         compute minimal pix_count for artefacts and maximal pix_count for signals
        self.min_pixcount_arte_ = X[:, 0].max()
        self.min_lum_arte_ = X[:, 1].max()
        self.max_pixcount_sig_ = X[:, 0].min()
        self.max_lum_sig_ = X[:, 1].min()
        print("{} {} {} {}\n".format(self.min_pixcount_arte_, self.min_lum_arte_, self.max_pixcount_sig_,
                                     self.max_lum_sig_))
        for features, label in zip(X, y):
            pix_count = features[0,]
            lum = features[1,]
            if label == 0:  # signal
                if pix_count > self.max_pixcount_sig_:
                    self.max_pixcount_sig_ = pix_count
                if lum > self.max_lum_sig_:
                    self.max_lum_sig_ = lum
            else:
                if pix_count < self.min_pixcount_arte_:
                    self.min_pixcount_arte_ = pix_count
                if lum < self.min_lum_arte_:
                    self.min_lum_arte_ = lum

        print("{} {} {} {}".format(self.min_pixcount_arte_, self.min_lum_arte_, self.max_pixcount_sig_,
                                   self.max_lum_sig_))
        self.border_lum_ = (self.min_lum_arte_ + self.max_lum_sig_) / 2
        self.border_pixcount_ = (self.min_pixcount_arte_ + self.max_pixcount_sig_) / 2
        return self

    def predict(self, X):
        Y = np.zeros(X.shape[0])
        for i in range(X.shape[0]):
            pix_count = X[i, 0]
            # pix_count=0
            lum = X[i, 1]
            if ((pix_count / self.border_pixcount_) ** 2 + (lum / self.border_lum_) ** 2 <= 1):
                Y[i] = 0
            else:
                Y[i] = 1
        return Y