from datetime import datetime
from time import mktime
import os

def set_start_end(data_start,data_end):
    """

    :param data_start: data when we start, type: "YYYY-MM-DD HH:MM"
    :param data_end: data when we finish, i.e: "2022-06-13 12:00"
    :return: timestamp_start,timestamp_end
    """

    timestamp_start = int(mktime(datetime.strptime(data_start, '%Y-%m-%d %H:%M').timetuple()))
    timestamp_end = int(mktime(datetime.strptime(data_end, '%Y-%m-%d %H:%M').timetuple()))

    return timestamp_start,timestamp_end


def check_file(file_name,file_list_finish):
    """
    :param file_name: checked the file name
    :param file_list: file with a list of files that have already been checked
    :return:
    """
    file_was_read = 0  # 0 - no, 1 - yes
    if str(os.path.isfile(file_list_finish)) == "True":
        f = open(file_list_finish, "r")
        for line in f:
            line = line.rstrip("\n")
            if str(line) == str(file_name):
                #print(line, "was readed, we don't read this file")
                file_was_read = 1
        f.close()
    return file_was_read


