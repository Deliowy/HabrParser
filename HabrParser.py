import datetime as dtime
import json
import logging
import os
import re
from threading import Thread

import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup
from wordcloud import STOPWORDS, ImageColorGenerator, WordCloud

ENGAGE_COEF_MIN = 0.5



def _init_logger(filename: str, level: str):
    """Инициализация логгера для дальнейшего использования

    Parameters
    :param  filename - Имя файла логов
    :type   filename: str

    :param  level - Уровень логгера
    :type   level: str

    Return
    :return logger - Экземпляр класса Logger
    :type   logger: Logger
    """
    # Создание папки для хранения логов
    os.makedirs("./Logs/", exist_ok=True)
    # Базовая конфигурация создаваемого логгера
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh = logging.FileHandler(f"./Logs/{filename}.log")
    fh.setFormatter(formatter)

    logging.basicConfig(
        level=logging.getLevelName(level),
    )

    logger = logging.getLogger(f"{filename}_Logger")
    logger.addHandler(fh)

    logger.info(f"Логгер {logger.name} инициализирован")
    return logger


def makedir(path: str):
    """Создание папки для статей конкретного раздела

    Parameters
    :param  path - Путь создаваемой папки
    :type   path: str
    """
    try:
        _logger.info(f"Создание папки с путем {path}")
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        _logger.warning(f"При создании папки с путем {path} возникла ошибка: {e}")
    finally:
        _logger.info(f"Папка с путем {path} успешно создана")


def scrape_page(url: str):
    """Собрать верстку страницы

    Parameters
    :param  url - Ссылка на страницу
    :type   url: str

    Return
    :return soup - Полученная верстка страницы
    :type   soup: bs4.BeautifulSoup
    """
    try:
        _logger.info(f"Попытка спарсить страницу по адресу {url}")
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Host": "habr.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return scrape_page(url)
        soup = BeautifulSoup(response.text, "lxml")
        _logger.info(f"Парсинг страницы по адресу {url} выполнена успешно")
        return soup
    except Exception as e:
        _logger.warning(
            f"При попытке спарсить страницу по адресу {url} \n возникла ошибка: {e}"
        )


def get_article_views(article_item: BeautifulSoup):
    """Получить количество просмотров статьи

    Parameters
    :param  article_item - Суп статьи из списка
    :type   article_item: bs4.BeautifulSoup

    Returns
    :return views - Количество просмотров
    :type   views: int
    """
    views = article_item.find("span", title="Количество просмотров").find("span").text
    views = int(float(views[:-1]) * 1000)
    return views


def get_article_author(article: BeautifulSoup):
    """Получить ник автора статьи

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return author_handle - Никнейм автора
    :type   author_handle: str
    """
    author_handle = article.find("span", class_="tm-article-snippet__author").text
    return author_handle.strip()


def get_article_title(article: BeautifulSoup):
    """Получить название статьи

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return article_title - Название статьи
    :type   article_title: str
    """
    article_title = article.find("h1", class_="tm-article-snippet__title").text
    return article_title


def get_article_publication_time(article: BeautifulSoup):
    """Получить дату публикации статьи

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return article_publication_time - Дата публикации статьи
    :type   article_publication_time: datetime.datetime
    """
    article_publication_time = article.find("time")["datetime"]
    article_publication_time = dtime.datetime.strptime(
        article_publication_time, "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    return article_publication_time


def get_article_tags(article: BeautifulSoup):
    """Получить теги статьи

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return article_tags - Список тегов статьи
    :type   article_tags: list
    """
    article_tags = article.find_all("div", class_="tm-article-presenter__meta-list")[0]
    article_tags = list(map(lambda x: x.text.strip(), article_tags.ul.contents))
    return article_tags


def get_article_hubs(article: BeautifulSoup):
    """Получить хабы статьи

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return article_hubs - Список хабов статьи
    :type   article_hubs: str
    """
    article_hubs = article.find_all("div", class_="tm-article-presenter__meta-list")[1]
    article_hubs = list(map(lambda x: x.text.strip(), article_hubs.ul.contents))
    return article_hubs


def get_article_votes(article: BeautifulSoup):
    """Получить количество голосов статьи

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return article_upvotes - Количество положительных голосов статьи
    :type   article_title: int

    :return article_downvotes - Количество отрицательных голосов статьи
    :type   article_downvotes: int

    :return article_total_votes - Общее количество голосов статьи
    :type   article_total_votes: int
    """
    votes_soup = article.find("svg", class_="tm-votes-meter__icon")
    reg_exp = re.compile(r"\d+")
    votes = reg_exp.findall(votes_soup.text)
    votes = list(map(int, votes))
    article_total_votes, article_upvotes, article_downvotes = votes
    return article_upvotes, article_downvotes, article_total_votes


def get_article_bookmarks(article: BeautifulSoup):
    """Получить сколько раз статью добавляли в закладки

    Parameters
    :param  article - Суп страницы статьи
    :type   article: bs4.BeautifulSoup

    Returns
    :return article_bookmarks - Количество добавлений статьи в закладки
    :type   article_bookmarks: int
    """
    article_bookmarks = int(
        article.find("span", class_="bookmarks-button__counter").text.strip()
    )
    return article_bookmarks


def get_article_comments(article_id: int, flow_folder: str):
    """Получить комментарии к статье

    Parameters
    :param  article_id - ID статьи
    :type   article_id: int

    :param  flow_folder - Папка раздела
    :type   flow_folder: str

    Returns
    :return comments - DataFrame комментариев
    :type   comments: pd.DataFrame

    :return article_comments_quantity - Количество комментариев
    :type   article_comments_quantity: int
    """
    try:
        _logger.info(
            f"Попытка спарсить комментарии к статье по адресу https://habr.com/ru/post/{article_id}/"
        )
        comments_url = f"https://habr.com/kek/v2/articles/{article_id}/comments/"
        comments_csv_name = f"Comments_{article_id}.csv"

        response = requests.get(comments_url)
        while response.status_code != 200:
            response = requests.get(comments_url)
        data = json.loads(response.text)
        comments_json = data["comments"]

        comments = pd.DataFrame(columns=["Comment_Author", "Comment_Text"])

        for comment_id in comments_json:
            current = comments_json[comment_id]

            if current["author"] is None:
                continue

            comment_author = current["author"]["alias"]
            comment_text = BeautifulSoup(current["message"], "lxml").text

            clear_comment_text = re.sub(r"[^a-zA-Z0-9А-Яа-я\s]", " ", comment_text)

            comment_entry = {
                "Comment_Author": comment_author,
                "Comment_Text": clear_comment_text,
            }
            comments = comments.append(comment_entry, ignore_index=True)
        comments.to_csv(
            f"{flow_folder}{comments_csv_name}", index=False, encoding="utf-8"
        )

        _logger.info(
            f"Парсинг комментариев к статье по адресу https://habr.com/ru/post/{article_id}/ успешно выполнен"
        )
        return comments_csv_name, comments.shape[0]
    except Exception as e:
        _logger.warning(
            f"При попытке спарсить комментарии к статье по адресу https://habr.com/ru/post/{article_id}/ возникла ошибка {e}"
        )


def calc_engagement_coef(article_info: dict):
    """Вычислить показатель вовлеченности пользователей

    Parameters
    :param  article_info - Данные о статье для которой вычисляется показатель
    :type   article_info: dict

    Returns
    :return engage_coef - Показатель вовлеченности пользователей
    :type   engage_coef: float
    """
    engage_coef = (
        article_info["Total_votes"]
        + article_info["Bookmarks"]
        + article_info["Comments_Quantity"]
    ) / article_info["Views"]
    return engage_coef


def scrape_article(article: BeautifulSoup, articles_info: list, flow_folder: str):
    """Парсинг статьи

    Parameters
    :param  article - Суп статьи из списка
    :type   article: bs4.BeautifulSoup

    :param  articles_info - Список с инфомрацией о статьсях
    :type   articles_info: list

    :param  article_idx - Индекс статьи в списке
    :type   article_idx: int
    """
    habr_articles_url = "https://habr.com/ru/post"
    article_id = article["id"]
    article_url = f"{habr_articles_url}/{article_id}/"
    article_page_soup = scrape_page(article_url)

    article_title = get_article_title(article_page_soup)
    author_handle = get_article_author(article_page_soup)
    article_publication_time = get_article_publication_time(article_page_soup)
    article_tags = get_article_tags(article_page_soup)
    article_hubs = get_article_hubs(article_page_soup)
    article_views = get_article_views(article)
    article_upvotes, article_downvotes, article_total_votes = get_article_votes(
        article_page_soup
    )
    article_bookmarks = get_article_bookmarks(article_page_soup)
    article_comments_csv_name, article_comments_quantity = get_article_comments(
        article_id, flow_folder
    )

    article_info = {
        "Article_Title": article_title,
        "Article_Link": article_url,
        "Author": author_handle,
        "Engagement_Coef": 0,
        "Publication_Time": article_publication_time,
        "Tags": article_tags,
        "Hubs": article_hubs,
        "Views": article_views,
        "Upvotes": article_upvotes,
        "Downvotes": article_downvotes,
        "Total_votes": article_total_votes,
        "Bookmarks": article_bookmarks,
        "Comments_Quantity": article_comments_quantity,
        "Comments_CSV": article_comments_csv_name,
    }

    article_engage_coef = calc_engagement_coef(article_info)
    article_info.update({"Engagement_Coef": article_engage_coef})

    articles_info.append(article_info)
    return True


def get_all_articles(url: str):
    """Собрать все доступные статьи потока

    Parameters
    :param  url - Ссылка на основную страницу потока
    :type   url: str

    :param  months - За сколько месяцев нужны статьи
    :type   months: int (default 1)

    Returns
    :return articles - Список статей потока
    :type   articles: list
    """
    articles = []

    # flow_modifiers = ["", "top0/", "top10/", "top25/"]
    flow_modifiers = ["top10/", "top25/"]

    flow_pages = scrape_page(url).find_all("a", class_="tm-pagination__page")
    last_page = int(flow_pages[-1].text.strip())

    for modifier in flow_modifiers:
        for page in range(last_page):
            page_url = f"{url}{modifier}page{page+1}/"
            page_soup = scrape_page(page_url)
            page_articles = page_soup.find("div", class_="tm-articles-list").find_all(
                "article"
            )
            articles.extend(page_articles)

    return articles


def filter_engaging_articles(articles: list, min_engage_coef: float):
    """Убрать из списка статьи с недостаточным коэффициентом вовлекаемости

    Parameters
    :param  articles - Список статей
    :type   articles: list

    :param  min_engage_coef - Порог отбора статей по коэффициенту вовлекаемости
    :type   min_engage_coef: float

    Returns
    :return filtered_articles - Отфильтрованный список статей
    :type   filtered_articles: list
    """

    filtered_articles = []

    for article in articles:
        #TODO
        pass

    return filtered_articles


def filter_articles_from_metaposts(articles: list):
    """Убрать из списка статей метапосты(блоги компаний)

    Parameters
    :param  articles - Список статей и метапостов
    :type   articles: list

    Returns
    :return filtered_articles - Отфильтрованный список статей
    :type   filtered_articles: list
    """
    filtered_articles = []

    for article in articles:
        is_article = article.find("div", class_="tm-article-snippet")
        if is_article:
            filtered_articles.append(article)

    return filtered_articles


def filter_articles_by_months(articles: list, months: int):
    """Отфильтровать статьи опубликованные в течении указанного числа месяцев

    Parameters
    :param  articles - Список статей
    :type   articles: list

    :param  months - За сколько последних месяцев фильтровать статьи
    :type   months: int

    Returns
    :return filtered_articles - Отфильтрованный список статей
    :type   filtered_articles: list

    """
    filtered_articles = []

    current_month = dtime.datetime.today().month
    target_month = (current_month - months + 1) % 12

    for article in articles:
        article_month = get_article_publication_time(article).month
        if article_month >= target_month:
            filtered_articles.append(article)

    return filtered_articles

def filter_articles_wrapper(articles: list, months: int):
    """Оберточная функция для фильтрации статей по нескольким параметрам
    
    Parameters
    :param  articles - Список статей
    :type   articles: list

    :param  months - За сколько последних месяцев фильтровать статьи
    :type   months: int

    Returns
    :return filtered_articles - Отфильтрованный список статей
    :type   filtered_articles: list
    """

    filtered_articles = filter_articles_by_months(articles, months)
    filtered_articles = filter_articles_from_metaposts(filtered_articles)
    filtered_articles = filter_engaging_articles(filtered_articles)

    return filtered_articles

def scrape_flow(flow_folder: str, url: str, months: int = 1):
    """Спарсить все статьи раздела за указанное число месяцев

    Parameters
    :param  flow_folder - Путь к папке раздела
    :type   flow_folder: str

    :param  url - Ссылка на раздел
    :type   url: str

    :param  months - За сколько месяцев нужны статьи
    :type   months: int (default 1)

    Returns
    :return flow_df - DataFrame с информацией о статьях раздела
    :type   flow_df: pd.DataFrame
    """
    makedir(flow_folder)

    articles = get_all_articles(url)

    articles = filter_articles_wrapper(articles, months)

    articles_info = []
    articles_threads = []

    for article in articles:
        article_thread = Thread(
            target=scrape_article,
            args=[article, articles_info, flow_folder],
        )
        article_thread.start()
        articles_threads.append(article_thread)

    for thread in articles_threads:
        thread.join()
    _logger.info("Потоки парсившие статьи раздела завершились")

    flow_df = pd.DataFrame(articles_info).drop_duplicates(subset=["Article_Link"])

    filter_condition = flow_df["Engagement_Coef"] >= ENGAGE_COEF_MIN

    return flow_df[filter_condition]


def find_most_active_authors(flow_articles: pd.DataFrame, N: int = 10):
    """Найти N наиболее активных авторов в отдельном разделе

    Parameters
    :param  flow_articles - Список статей раздела
    :type   flow_articles: pandas.DataFrame

    :param  N - сколько авторов нужно найти
    :type   N: int (default 10)

    Returns
    :return most_active_authors - Словарь с наиболее активными авторами.\
        Ключ - имя автора, Значение - количество статей
    :type   most_acrive_authors: dict
    """
    most_active_authors = flow_articles["Author"].value_counts()[:N].to_dict()
    return most_active_authors


def find_most_active_commenters(flow_articles: pd.DataFrame, N: int = 10):
    """Найти N наиболее активных комментаторов в отдельном разделе
    
    Parameters
    :param  flow_articles - Список статей раздела
    :type   flow_articles: pandas.DataFrame

    :param  N - сколько комментаторов нужно найти
    :type   N: int (default 10)  

    Returns
    :return most_active_commenters - Словарь с наиболее активными комментаторами.\
        Ключ - имя автора, Значение - количество комментариев
    :type   most_active_commenters: dict
    """
    comments_files = flow_articles["Comments_CSV"]

    comments = pd.DataFrame(columns=["Comment_Author", "Comment_Text"])

    for file in comments_files:
        comments = comments.append(pd.read_csv(file, encoding="utf-8"))

    most_active_commenters = comments["Comment_Author"].value_counts()[:N].to_dict()
    return most_active_commenters


def make_titles_wordcloud(flow_name: str, flow_articles: pd.DataFrame):
    """Создать облако слов из названий статей в отдельном разделе

    Parameters
    :param  flow_name - Название раздела
    :type   flow_name: str

    :param  flow_articles - DataFrame с информацией о статьях раздела
    :type   flow_articles: pd.DataFrame
    """
    comment_words = ""
    stopwords = set(STOPWORDS)

    # iterate through the csv file
    for val in flow_articles["Article_Title"].values:

        # typecaste each val to string
        val = str(val)

        # split the value
        tokens = val.split()

        # Converts each token into lowercase
        for i in range(len(tokens)):
            tokens[i] = tokens[i].lower()

        comment_words += " ".join(tokens) + " "

    wordcloud = WordCloud(
        width=800,
        height=800,
        background_color="white",
        stopwords=stopwords,
        min_font_size=10,
    ).generate(comment_words)

    # plot the WordCloud image
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)

    plt.savefig(f"WordCloud_Titles_{flow_name}.jpg", bbox_inches="tight", dpi=250)
    plt.show()


def make_comments_wordcloud(flow_name: str, flow_articles: pd.DataFrame):
    """Создать облако слов из комментариев в отдельном разделе

    Parameters
    :param  flow_name - Название раздела
    :type   flow_name: str

    :param  flow_articles - DataFrame с информацией о статьях раздела
    :type   flow_articles: pd.DataFrame
    """
    comment_words = ""
    stopwords = set(STOPWORDS)

    comments_files = flow_articles["Comments_CSV"]

    comments = pd.DataFrame(columns=["Comment_Author", "Comment_Text"])

    for file in comments_files:
        comments = comments.append(pd.read_csv(file, encoding="cp1251"))

    # iterate through the csv file
    for val in comments["Comment_Text"].values:

        # typecaste each val to string
        val = str(val)

        # split the value
        tokens = val.split()

        # Converts each token into lowercase
        for i in range(len(tokens)):
            tokens[i] = tokens[i].lower()

        comment_words += " ".join(tokens) + " "

    wordcloud = WordCloud(
        width=800,
        height=800,
        background_color="white",
        stopwords=stopwords,
        min_font_size=10,
    ).generate(comment_words)

    # plot the WordCloud image
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad=0)

    plt.savefig(f"WordCloud_Comments_{flow_name}.jpg", bbox_inches="tight", dpi=250)
    plt.show()


def main():
    """Основной код программы"""

    work_dir = "."
    articles_folder = f"{work_dir}/Articles_Folder/"
    makedir(articles_folder)

    main_url = "https://habr.com/ru/flows"

    flows_dict = {
        "Разработка": f"{main_url}/develop/",
        "Администрирование": f"{main_url}/admin/",
        "Дизайн": f"{main_url}/design/",
        "Менеджмент": f"{main_url}/management/",
        "Маркетинг": f"{main_url}/marketing/",
        "Научпоп": f"{main_url}/popsci/",
    }

    for key in flows_dict:
        flow_folder = f"{articles_folder}{key}/"
        flow_df = scrape_flow(flow_folder, flows_dict[key], 3)
        _logger.info(f"Парсинг потока '{key}' завершен")
        print("Наиболее активные авторы:")
        print(find_most_active_authors(flow_df, 30))
        print("Наиболее активные комментаторы:")
        print(find_most_active_commenters(flow_df, 30))
        make_titles_wordcloud(key, flow_df)
        make_comments_wordcloud(key, flow_df)
        _logger.info(f"Вывод требуемой информации по потоку {key} завершен")

    _logger.info("Парсинг основных разделов завершен")


if __name__ == "__main__":
    _logger = _init_logger("HabrParser", "INFO")

    _logger.info("Запуск программы")

    main()

    _logger.info("Успешное завершение программы")
