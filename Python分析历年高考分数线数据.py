from multiprocessing.pool import Pool


import requests

from bs4 import BeautifulSoup

import pymongo

import re



client = pymongo.MongoClient('localhost', 27017)

gaokao = client['gaokao']

provice_href = gaokao['provice_href']

score_detail = gaokao['score_detail']




# 获取省份及链接

pro_link = []

def get_provice(url):

    web_data = requests.get(url, headers=header)

    soup = BeautifulSoup(web_data.content, 'lxml')

    provice_link = soup.select('.area_box > a')

    for link in provice_link:

        href = link['href']

        provice = link.select('span')[0].text

        data = {

            'href': href,

            'provice': provice

        }

        provice_href.insert_one(data)#存入数据库

        pro_link.append(href)

    print('OK')





# 获取分数线

def get_score(url):

    web_data = requests.get(url, headers=header)

    soup = BeautifulSoup(web_data.content, 'lxml')

    # 获取省份信息

    provice = soup.select('.col-nav span')[0].text[0:-5]

    # 获取文理科

    categories = soup.select('h3.ft14')

    category_list = []

    for item in categories:

        category_list.append(item.text.strip().replace(' ', ''))

    # 获取分数

    tables = soup.select('h3 ~ table')

    for index, table in enumerate(tables):

        tr = table.find_all('tr', attrs={'class': re.compile('^c_\S*')})

        for j in tr:

            td = j.select('td')

            score_list = []

            for k in td:

                # 获取每年的分数

                if 'class' not in k.attrs:

                    score = k.text.strip()

                    score_list.append(score)



                # 获取分数线类别

                elif 'class' in k.attrs:

                    score_line = k.text.strip()



                score_data = {

                    'provice': provice.strip(),#省份

                    'category': category_list[index],#文理科分类

                    'score_line': score_line,#分数线类别

                    'score_list': score_list#分数列表

                }

            score_detail.insert_one(score_data)

        print("detail insert ok")





if __name__ == '__main__':



    header = {
           
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:58.0) Gecko/20100101 Firefox/58.0',

            'Connection': 'keep - alive'}

    url = 'http://www.gaokao.com/beijing/fsx/'



    get_provice(url)

    pool = Pool()

    pool.map(get_score, [i for i in pro_link])#使用多线程
    
import pymongo
import charts

client = pymongo.MongoClient('localhost', 27017)
gaokao = client['gaokao']
score_detail = gaokao['score_detail']

# 筛选分数线、省份、文理科
def get_score(line,pro,cate):
    score_list=[]
    for i in score_detail.find({"$and":[{"score_line":line},{"provice":pro},{'category': cate}]}):
        score_list = i['score_list']
        score_list.remove('-')#去掉没有数据的栏目
        score_list = list(map(int, score_list))
        score_list.reverse()
        return score_list
    
# 获取文理科分数
line = '一本'
pro = '北京'
cate_wen = '文 科' #这里中间有空格，但是已经在爬取的时候改正了
cate_li = '理 科' #这里中间有空格，但是已经在爬取的时候改正了
wen=[]
li = []
wen=get_score(line,pro,cate_wen)
li=get_score(line,pro,cate_li)


# 定义年份
year = [2017,2016,2015,2014,2013,2012,2011,2010,2009]
year.reverse()
print(year)


series = [
    {
    'name': '文 科',
    'data': wen,
    'type': 'line'
}, {
    'name': '理科',
    'data': li,
    'type': 'line',
    'color':'#ff0066'
}
         ]
options = {
    'chart'   : {'zoomType':'xy'},
    'title'   : {'text': '{}省{}分数线'.format(pro,line)},
    'subtitle': {'text': 'Source: gaokao.com'},
    'xAxis'   : {'categories': year},
    'yAxis'   : {'title': {'text': 'score'}}
    }

charts.plot(series, options=options,show='inline')