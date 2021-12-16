"""
Pobranie nowych hitów do sklasyfikowania w formacie JSON lub spakowanym JSON.
"""
from typing import Set

import requests
import urllib.request

from commons import *
from settings import *


def parse_apache_file_list(page: str, ignore_files: Set[str]) -> List[str]:
    """
    Zwraca listę plików pasujących do wzorca regex "export_\d+_\d+.json(.xz)?".

    :param page: strona HTML z listą plików w katalogu wygenerowana przez Apache HTTPD
    :return: lista plików
    """

    file_list = []

    # pocięcie strony na href'y do plików "export*"
    lefts = page.split('href="export')
    for left in lefts:
        # pominięcie kawałków nie pasujących do kolejnego znaku wzorca po "export"
        if left[0] != '_':
            continue

        # przycięcie na końcu href'a
        rights = left.split('">')
        file_name = 'export' + rights[0]
        if file_name in ignore_files:
            continue
        file_list.append(file_name)
    return file_list


def get_file_list(urls: List[str], ignore_files: Set[str]) -> List[str]:
    """
    Pobranie listy URL'i plików do ściągnięcia.

    :param urls: URL'e do stron zawierających listy plików
    :return: lista URLi
    """
    file_list = []
    for url in download_urls:
        # ściągnięcie listy plików Apache
        page = requests.get(url)

        # przygotowanie części URL'a doklejanej przed nazwą pliku (musi się kończyć na '/')
        prefix = url
        if not prefix.endswith('/'):
            prefix += '/'

        # dodanie plików do listy z doklejeniem URL'a przed
        file_list.extend(map(lambda a: prefix + a, parse_apache_file_list(page.text, ignore_files)))
    return file_list


# pobranie listy już ściągniętych plików aby jeszcze raz ich nie ściągać
ignore_files = set(read_file_to_lines(new_data_acquire_done))

# pobranie list nieściągniętych plików
file_list = get_file_list(download_urls, ignore_files)

# pobranie tych plików
done_list = []
create_dir_if_not_exist(new_data_acquire_destination)
for url in file_list:
    # zastosowanie ograniczenia liczby ściąganie plików z ustawienia: new_data_acquire_files_limit
    if new_data_acquire_files_limit is not None and len(done_list) >= new_data_acquire_files_limit:
        break

    # odseparowanie samej nazwy pliku
    fn = url.split('/')[-1]

    # ściągnięcie do pliku
    dest = os.path.join(new_data_acquire_destination, fn)
    urllib.request.urlretrieve(url, dest)

    # dodanie do listy plików ściągniętych
    done_list.append(fn)

# dopisanie ściągniętych do listy aby ich więcej nie ściągać
append_lines_to_file(new_data_acquire_done, done_list)
