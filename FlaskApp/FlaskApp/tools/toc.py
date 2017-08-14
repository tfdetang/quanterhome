from bs4 import BeautifulSoup

def markdown_toc(html):
    toc_list = []
    soup = BeautifulSoup(html, 'lxml')

    def has_id(tag):
        return tag.has_attr('id')

    index = soup.find_all(has_id)
    for i in index:
        toc_dict = {}
        toc_dict.update({'head': i.name})
        toc_dict.update({'id': i['id']})
        toc_dict.update({'text': i.text})
        toc_list.append(toc_dict)
    return toc_html(toc_list)


def toc_html(toc_list):
    str = ''
    for i in toc_list:
        if i['head'] == 'h1':
            str += '<li style="font-size:14px"><a href="#%s">%s</a></li>' % (i['id'], i['text'])
        elif i['head'] == 'h2':
            str += '<li style="font-size:12px"><a style="left:20px" href="#%s">%s</a></li>' % (i['id'], i['text'])
        elif i['head'] == 'h3':
            str += '<li style="font-size:12px"><a style="left:40px" href="#%s"> -%s</a></li>' % (i['id'], i['text'])
    return str
