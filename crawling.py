"""
いちかのBEMANI投票選抜戦2019(https://p.eagate.573.jp/game/bemani/bvs2019/index.html)のアクリルフィギュア優先権取得条件であるランキング100位のボーダーを取得しツイートする。
rootディレクトリから"~/documents/bemani/"上にあるこのコードを実行する必要がある
"""


import sys
import requests
import traceback
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime
import tweepy
import pandas as pd
import matplotlib.pyplot as plt

GAME_NAME_LIST = [
    "弐寺"
    , "ダンレボ"
    , "ダンスラ"
    , "ギタドラ"
    , "指"
    , "ポプ"
    , "ボルテ"
    , "ノスタ"
]
BASE_URL = "https://p.eagate.573.jp/game/bemani/bvs2019/vote/mani_"
URL_LIST = [
    "iidx.html"
    , "ddr.html"
    , "drs.html"
    , "gtdr.html"
    , "jubeat.html"
    , "popn.html"
    , "sdvx.html"
    , "nos.html"
]
CSV_NAME_LIST = ["./documents/bemani/ranking50.csv", "./documents/bemani/ranking100.csv"]
COLUMNS_NAME_LIST = ['time', 'IIDX', 'DDR', 'DANCERUSH', 'GITADORA', 'jubeat', "pop'n", 'SDVX', 'NOSTALSIA']
GRAPH_NAME_LIST = ['./documents/bemani/graph50.png','./documents/bemani/graph100.png']
GRAPH_TITLE_LIST = ['transitive graph(rank 50)', 'transitive graph(rank 100)']
MAX_RETRY_COUNT = 10
RETRY_WAIT_TIME = 5

# Twitter各種キー
CK=""
CS=""
AT=""
AS=""


def crawling(url: str) -> BeautifulSoup:
    """
    対象ページをクローリングし、soupの型で返す
​
    @param url: 対象のURL
    @return: BeautifulSoup
    """
    for count in range(MAX_RETRY_COUNT):
        try:
            time.sleep(1)
            request = requests.get(url)
            if request.status_code != 200:
                raise RuntimeError(f"status_code:{requests.status_code}")
            soup = BeautifulSoup(request.content, "html.parser")
            return soup
        except Exception:
            traceback.print_exc()
            time.sleep(RETRY_WAIT_TIME)

    print("ページの取得に失敗しました")
    sys.exit(1)


def get_ranking_point(soup: BeautifulSoup) -> list:
    """
    URLからurlを抽出する。
​
    @param soup: スクレイピング対象ページのBeautifulSoupオブジェクト
    @return: 50位と100位のポイントのリスト
    """
    table_id = "ranking"
    div_class_50 = "name_50"
    div_class_100 = "name_100"
    ranking_element = soup.find("table", id=table_id)
    ranking_50_element = ranking_element.find_all("div", class_=div_class_50)
    ranking_100_element = ranking_element.find_all("div", class_=div_class_100)

    point_list = [ranking_50_element[1].text, ranking_100_element[1].text]

    return point_list


def list_save(file_name: str, save_list: list, mode: str) -> None:
    """
    リストをファイルで保存
​
    @param file_name: ファイル名
    @param save_list: リスト
    @param mode:書き込みモード
    """

    str_save = ','.join(save_list) + '\n'
    with open(file_name, mode=mode, encoding='utf-8') as f:
        f.write(str_save)


def tweet(content: str) -> None:
    """
    画像付きツイートを行う,画像はGRAPH_NAME_LISTに

    @param content: ツイート内容(文字) 
    """
    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(AT, AS)
    api = tweepy.API(auth)
    tweet_graph = [','.join([api.media_upload(image).media_id_string for image in GRAPH_NAME_LIST])]
    # tweet
    api.update_status(status=content, media_ids=tweet_graph)


def make_tweet_content(name, point_list) -> str:
    """
    ツイート本文を作成
​
    @param name: 機種名
    @param point_list: 票数のリスト
    @return: ツイート内容(文字)
    """
    content = f"{name} 50位:{point_list[0]}, 100位:{point_list[1]}\n"
    return content


def make_graph(file_name: str, save_name: str, graph_title: str, columns_name_list: list):
    """
    今までに取得したログの折れ線グラフによる可視化を行う

    @param file_name: 読み込むcsvファイル
    @param save_name: 作成するpngファイルの名前
    @param graph_title: グラフのタイトル
    @param columns_name_list: 各項目(機種)の名前
    """
    df = pd.read_csv(file_name)
    df.columns = columns_name_list
    df = df.set_index(columns_name_list[0])
    df.index = pd.to_datetime(df.index, format='%m/%d %H:%M')
    fig, ax = plt.subplots(figsize=(12, 6))
    for columns_name in columns_name_list[1:]:
        ax.plot(df.index, df[columns_name], label=columns_name)
    # 軸目盛の設定
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=None, interval=1, tz=None))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.legend()
    ax.grid()
    
    # グラフタイトル
    plt.title(graph_title)
    
    plt.savefig(save_name)
    plt.close('all')


def main() -> None:    
    for csv_name in CSV_NAME_LIST:
        if not os.path.exists(csv_name):
            list_save(csv_name, ["時刻"] + GAME_NAME_LIST, "w")

    dt_now = datetime.now()
    now_time = dt_now.strftime('%m/%d %H:%M')
    point_list_50 = [now_time]
    point_list_100 = [now_time]
    point_list_name = [point_list_50, point_list_100]
    tweet_content = f"投票選抜戦各機種ボーダー票数({now_time})\n"
    for game_name, url in zip(GAME_NAME_LIST, URL_LIST):
        soup = crawling(BASE_URL+url)
        point = get_ranking_point(soup)
        tweet_content += make_tweet_content(game_name, point)
        point_list_50.append(point[0])
        point_list_100.append(point[1])

    for csv_name, point, graph_name, graph_title in zip(CSV_NAME_LIST, point_list_name, GRAPH_NAME_LIST, GRAPH_TITLE_LIST):
        list_save(csv_name, point, "a")
        make_graph(csv_name, graph_name, graph_title, COLUMNS_NAME_LIST)

    print(tweet_content)
    tweet(tweet_content)


if __name__ == "__main__":
    main()
    sys.exit(0)

