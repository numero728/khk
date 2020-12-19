# reference: https://docs.microsoft.com/ko-kr/sql/machine-learning/data-exploration/python-dataframe-sql-server?view=sql-server-ver15

#------------------------------------------------------------------------------------------------------

import requests
import pandas as pd
from bs4 import BeautifulSoup as BS
import lxml
from xmltodict import parse
import os
import lxml

#------------------------------------------------------------------------------------------------------

def article_get(loc):
    try:
        article_res=requests.get(loc)
        article_soup=BS(article_res.content,'lxml')
        article_elems=article_soup.select('#container .story-news p')
        article_txt=[elem.text for elem in article_elems]
        article='\n'.join(article_txt)
    except Exception as e:
        print(e)
        article='Null'
    return article

#------------------------------------------------------------------------------------------------------

path=os.path.abspath(os.getcwd())
if 'chkduple' in os.listdir(path):
    pass
else:
    os.mkdir('chkduple')

sitemap_url='https://www.yna.co.kr/news-sitemap.xml'
sitemap_res=requests.get(sitemap_url)
sitemap_xml=parse(sitemap_res.content,'utf-8')
news_list=sitemap_xml['urlset']['url']

news_info=[
    {'loc':news['loc'],
    'pub_date':news['news:news']['news:publication_date'],
    'title':news['news:news']['news:title']}
    for news in news_list]
yna_news=pd.DataFrame(news_info,columns=news_info[0].keys())

from datetime import datetime
stamp=datetime.now().strftime('%Y-%m-%d')
filename=path+'\\chkduple\\'+stamp+'.txt'
news_scrapped=yna_news['loc']
if os.path.isfile(filename):
    news_duple=pd.read_csv(filename)
    yna_news=yna_news[~yna_news['loc'].isin(news_duple['loc'].tolist())]

#------------------------------------------------------------------------------------------------------

yna_news['article']=yna_news['loc'].apply(article_get)

#------------------------------------------------------------------------------------------------------

dialect='mssql'
driver='pyodbc'
driver_='pymssql'
database='scrap_data'
server='khkserver.database.windows.net'
username='khk'
password='k2hyokwang2!'
port='1433'


# sqlalchemy 이용하여 dataframe DB 적재

# 1. 필요 라이브러리 import
# 라이브러리: sqlalchemy(create_engine), pyodbc
# mySQL과 동일하게 url 설정 -> 단 url 끝에 get의 방식으로 driver 인자 지정(ODBC+Driver+13+for+SQL+Server)

# 2. create_engine 이용
from sqlalchemy import create_engine
from sqlalchemy.types import NVARCHAR
import pyodbc

db_url=f'{dialect}+{driver}://{username}:{password}@{server}:{port}/{database}?driver=ODBC+Driver+13+for+SQL+Server&charset=utf8'
conn=''
try:
    engine=create_engine(db_url, echo=True, encoding='utf8')
    conn=engine.connect()
    yna_news.to_sql('yna_news',conn,if_exists='append', index=False, dtype=NVARCHAR)
    news_scrapped.to_csv(filename)
except Exception as e:
    print(e)
finally:
    conn.close()

