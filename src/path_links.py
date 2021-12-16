#Konkursowe
main_path = "/media/no_backup/nkg/projects/pk/credo/classify_ml/tmp/konkursy/particle_hunters/" #główny katalog konkursu
team_file_raw = main_path+"team.csv" #plik csv pobrany z listą zarejestrowanych zespołów w konkursie
team_file = main_path+"teams_update.csv" #plik z dodanym id zespołu w credo
outfile_path = main_path+"outfile/" #folder gdzie zapisuje jsony z wynikiem oraz *.pkl

raw_detections_path = main_path+"detections/raw/"
png_detections_path = main_path+"detections/png/"
good_detections_path = main_path+"detections/good_time/"

#Surowe dane detekcji pobierane ogólnym skryptem CREDO
start_path = "/media/slawekstu/CREDO-skrypty/api/"
detections_path = start_path+"credo-data-export/detections/"
pings_path = start_path+"credo-data-export/pings/"


#Mappingi
device_mapping = start_path+"credo-data-export/device_mapping.json"
user_mapping = start_path+"credo-data-export/user_mapping.json"
team_mapping = start_path+"credo-data-export/team_mapping.json"