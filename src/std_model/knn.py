import numpy as np
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import os
from joblib import dump, load
from function import augment_train_data, computeZM, read_img
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score

path = "/media/no_backup/nkg/projects/pk/credo/classify_ml/src/tworzenie_modeli/hit-images/" #sciezka z ocenionyi obrazami
path2 = "/media/no_backup/nkg/projects/pk/credo/classify_ml/src/Modele/" #sciezka z wytrenowanym modelem


def create_model(images, targets):
    rs = np.random.randint(100)
    images_train4, images_test4, targets_train4, targets_test4 = train_test_split(images, targets, test_size=0.2,
                                                                                  stratify=targets, random_state=rs)
    images_train4, targets_train4 = augment_train_data(images_train4, targets_train4, augconf=[0, 4, 12, 0])
    X_train4, y_train4 = computeZM(images_train4, targets_train4)
    X_test4, y_test4 = computeZM(images_test4, targets_test4)

    name, scaler = 'StandardScaler', StandardScaler()
    scaler = scaler.fit(X_train4, y_train4)
    X_train4 = scaler.transform(X_train4)
    X_test4 = scaler.transform(X_test4)

    knn = KNeighborsClassifier(n_neighbors=1, metric='chebyshev')
    clf = knn.fit(X_train4, y_train4)
    clf1 = clf
    y_pred = clf1.predict(X_test4)
    print('Dokładność: {:.2f}%'.format(100 * accuracy_score(y_test4, y_pred)))
    #SŁABY MODEL - DOKŁADNOŚĆ OK 83%
    name2 = "knn"


    filename = os.path.join(path2, name2+".pkl")
    filename2 = os.path.join(path2, name2+"_scaler.pkl")
    dump(clf, filename)
    dump(scaler, filename2)

def main():
    images,targets = read_img()
    create_model(images, targets)


if __name__ == '__main__':
    main()