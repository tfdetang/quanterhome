import random
import math
from flask import Markup
from html.parser import HTMLParser
import datetime


class momentjs(object):
    def __init__(self, timestamp):
        '''
        moment.js的封装，用于显示各种时间格式
        :param timestamp: 输入数据库时间样式
        '''
        self.timestamp = timestamp

    def render(self, format):
        return Markup("<script>\ndocument.write(moment(\"%s\").%s);\n</script>" % (self.timestamp, format))

    def format(self, fmt):
        return self.render("format(\"%s\")" % fmt)

    def calendar(self):
        return self.render("calendar()")

    def fromNow(self):
        return self.render("fromNow()")


def random_avatar():
    rand = random.randint(1, 21)
    resource = 'static/avatar/%s.png' % str(rand)
    return resource


def paginate(page, page_limit, data_len, page_len=6):
    '''
    用于显示分页页码的函数
    :param page: 当前页码
    :param page_limit: 一页显示的条目上限
    :param data_len: 数据总长度
    :param page_len: 最多显示的页码数量
    :return: [{'page':1}, {'page':2, 'active':active}, {'page':3}]
    '''
    page_num = math.ceil(data_len / page_limit)
    page_info = []
    if page_num == 0:
        page_num = 1
    for i in range(1, page_len):
        cal = page - (page_len / 2) + i
        active = ''
        if cal == page:
            active = 'active'
        if cal > 0 and cal <= page_num:
            page_info.append({'page': int(page - (page_len / 2) + i), 'active': active})
    page_info.append({'page': page_num})
    return page_info


def date_past(days=7):
    today = datetime.datetime.now()
    past = today - datetime.timedelta(days=days)
    return datetime.datetime.strftime(past, "%Y-%m-%d %H:%M:%S")


def html_strip(html):
    html = html.replace("#", '')
    html = html.replace(">", '')
    html = html.replace("-", '')
    html = html.replace("*", '')
    html = html.strip()
    html = html.strip("\n")
    result = []
    parse = HTMLParser()
    parse.handle_data = result.append
    parse.feed(html)
    parse.close()
    return "".join(result)


def get_abstract(text, limit = 200):
    if len(text) > limit:
        return text[:200] + '...'
    else:
        return text


if __name__ == '__main__':
    print(date_past())