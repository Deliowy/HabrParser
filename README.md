# HabrParser

---

# Dependencies

1. BeautifulSoup    4.10.0
2. Pandas           1.3.5
3. Matplotlib       3.5.1
4. Requests         2.26.0
5. WordCloud        1.8.1

---

# ENG

Parser for website [habr.com](https://habr.com/ru/top/daily/)

Used for collecting info about articles of main thematics from a given time period:
1. Development
2. Admin
3. Desing
4. Management
5. Marketing
6. PopSci

During execution interacts with device file system to create new directories and files

Due to intense usage of multithreading, programm can cause errors if executed in Jupyter Notebook

# RU

Парсер для сайта [habr.com](https://habr.com/ru/top/daily/)

Предназначен для сбора информации о статьях основных тематических разделов за определенный период:
1. Разработка
2. Администрирование
3. Дизайн
4. Менеждмент
5. Маркетинг
6. Научпоп

В ходе работы взаимодействует с файловой системой устройства для создания новых директорий и файлов

Из-за активного использования многопоточности, программа может вызвать ошибки при запуске в Jupyter Notebook
