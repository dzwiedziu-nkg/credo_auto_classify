"""
Wspólny plik konfiguracyjny dla skyrptów sklasyfikacji.

Schemat:
  *_source - pliki do przetworzenia, przetworzone pliki mogą być usunięte
  *_done - informacje o przetworzonych danych, aby ich drugi raz nie przetwarzać
"""

from settings_local import *

# 01
new_data_acquire_destination = common_paths_prefix + '02_source/'
new_data_acquire_done = common_paths_prefix + '01_done.txt'
new_data_acquire_files_limit = 1  # maksymalna liczba plików do przetworzenia przy jednym przebiegu łańcucha skryptów

# 02
png_extracts_source = new_data_acquire_destination
png_extracts_destination = common_paths_prefix + '03_source/'
