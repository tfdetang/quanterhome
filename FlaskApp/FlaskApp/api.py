try:
    from FlaskApp.FlaskApp import app
except:
    import sys

    sys.path.append('..')
    from FlaskApp import app
import json
import os
from datetime import datetime, timedelta
import time

import pandas as pd
from flask import flash, redirect, session, url_for, request, g
from flask_login import logout_user, current_user, login_required
from sqlalchemy import create_engine
from werkzeug import secure_filename

from FlaskApp import Model
from FlaskApp.tools.utils import html_strip, get_abstract
from FlaskApp.views import *

Post = Model.Post
User = Model.User
Theme = Model.Theme
Comment = Model.Comment
Moment = Model.Moment
Alert = Model.Alert
Draft = Model.Draft
data_engine = create_engine(app.config['QUOTA_DATABASE_URI'], pool_size=100,
                            pool_recycle=5)


# ------------------------------------utils----------------------------------------------------

def add_moment(operation, user_id, url, url_name, context=''):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    moment = Moment(user_id=user_id, operation=operation, url=url, url_name=url_name, context=context, time_moment=now)
    moment.save()
    return True


def add_alert(you_id, me_id, operation, url, context):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if you_id == me_id:
        return False
    else:
        alert = Alert(you_id=you_id, me_id=me_id, operation=operation, url=url, context=context, time_alert=now,
                      is_read=0)
        alert.save()
        return True


def redirect_back():
    for target in request.values.get('next'), request.referrer:
        if not target:
            pass
        else:
            return redirect(target)

# --------------------------------------api---------------------------------------------------------


@app.route('/lobby/new_theme', methods=['GET', 'POST'])
@login_required
def create_theme():
    user = g.user
    name = request.values.get('name')
    url = request.values.get('url')
    introduce = request.values.get('introduce')
    file = request.files['file']
    file.save(os.path.join(app.config['UPLOAD_THEME'], secure_filename(url)))
    theme = Theme(name=name, url=url, introduce=introduce, creator=g.user.id)
    theme.save()
    add_moment(operation='创建了主题', url_name=name, user_id=user.id, url='/lobby/%s' % url)
    return redirect('/lobby')


@app.route('/lobby/favo_<theme_id>', methods=['GET', 'POST'])
@login_required
def add_favo_theme(theme_id):
    db = g.db
    user = g.user
    theme = db.session.query(Theme).filter(Theme.id == theme_id).one()
    user.favo_theme(theme)
    add_moment(operation='关注了主题', url_name=theme.name, user_id=user.id, url='/lobby/%s' % theme.url)
    return redirect('/lobby')


@app.route('/lobby/unfavo_<theme_id>', methods=['GET', 'POST'])
@login_required
def remove_favo_theme(theme_id):
    db = g.db
    user = g.user
    theme = db.session.query(Theme).filter(Theme.id == theme_id).one()
    user.unfavo_theme(theme)
    add_moment(operation='取消关注了主题', url_name=theme.name, user_id=user.id, url='/lobby/%s' % theme.url)
    return redirect('/lobby')


@app.route('/<topic_theme>/post', methods=['GET', 'POST'])
@login_required
def getpost(topic_theme):
    db = g.db
    user = g.user
    title = request.values.get('title')
    body = request.values.get('body')
    theme = request.values.get('theme-id')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    abstext = get_abstract(html_strip(body))
    post = Post(title=title, time_post=now, time_update=now, body=body, theme=theme, author_id=user.id,
                abstract=abstext)
    post.save()
    add_moment(operation='发表了文章',
               context=abstext,
               url_name=title,
               user_id=user.id,
               url='/topic/%s' % post.id)
    return redirect('/lobby/%s' % topic_theme)


@app.route('/people/post_from_draft/<draft_id>', methods=['GET', 'POST'])
@login_required
def post_from_draft(draft_id):
    db = g.db
    user = g.user
    title = request.values.get('title')
    body = request.values.get('body')
    theme = request.values.get('theme-id')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    abstext = get_abstract(html_strip(body))
    post = Post(title=title, time_post=now, time_update=now, body=body, theme=theme, author_id=user.id,
                abstract=abstext)
    post.save()
    draft = Draft(id=draft_id, title=title, time_update=now, body=body, author_id=user.id,
                  abstract=abstext)
    draft.update()
    add_moment(operation='发表了文章',
               context=abstext,
               url_name=title,
               user_id=user.id,
               url='/topic/%s' % post.id)
    return redirect('/topic/%s' % post.id)


@app.route('/topic/<postid>/editor', methods=['GET', 'POST'])
@login_required
def edit_post(postid):
    db = g.db
    user = g.user
    body = request.values.get('body')
    abstext = get_abstract(html_strip(body))
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    post = Post(id=postid,
                body=body,
                time_post=now,
                time_update=now,
                abstract=abstext)
    post.update()
    p = db.session.query(Post).filter(Post.id == postid).one()
    add_moment(operation='编辑了文章', url_name=p.title, user_id=user.id, url='/topic/%s' % postid)
    return redirect('/topic/%s' % postid)


@app.route('/topic/<postid>/<int:page>/add_tag', methods=['GET', 'POST'])
@login_required
def add_tag(postid, page):
    db = g.db
    p = db.session.query(Post).filter(Post.id == postid).one()
    name = request.values.get('tag')
    if name:
        p.add_tag(name, g.user.id)
        return redirect('/topic/%s?page=%s' % (postid, page))
    else:
        flash('标签内容不能为空')
        return redirect('/topic/%s?page=%s' % (postid, page))


@app.route('/topic/<postid>/<int:page>/like', methods=['GET', 'POST'])
@login_required
def like_dislike(postid, page):
    db = g.db
    user = g.user
    p = db.session.query(Post).filter(Post.id == postid).one()
    value = request.values.get('value')
    p.like_post(user, value)
    if value == '0':
        operation = '赞了文章'
    else:
        operation = '踩了文章'
    add_moment(operation=operation, url_name=p.title, user_id=user.id, url='/topic/%s' % p.id)
    add_alert(you_id=user.id, me_id=p.author.id, operation=operation, url='/topic/%s' % p.id, context=p.title)
    return redirect('/topic/%s?page=%s#like-area' % (postid, page))


@app.route('/topic/<postid>/<int:page>/comment', methods=['GET', 'POST'])
@login_required
def comment(postid, page):
    db = g.db
    user = g.user
    body = request.values.get('body')
    if body:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment = Comment(post_id=postid, user_id=user.id, time_comment=now, body=body)
        comment.save()
        p = db.session.query(Post).filter(Post.id == postid).one()
        post = Post(id=p.id, time_update=now, comment_count=p.comments.count())
        post.update()
        add_moment(operation='评论了', context=body, user_id=user.id, url_name=p.title, url='/topic/%s' % p.id)
        add_alert(you_id=user.id,
                  me_id=p.author.id,
                  operation='评论了你的文章',
                  url='/topic/%s#comment-area' % p.id, context=body)
        return redirect('/topic/%s?page=%s#comment-area' % (postid, page))
    else:
        flash('评论不能少于6个字！！')
        return redirect('/topic/%s?page=%s' % (postid, page))


@app.route('/quota/<postid>/comment', methods=['GET', 'POST'])
@login_required
def quota_comment(postid):
    db = g.db
    user = g.user
    body = request.values.get('body')
    if body:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment = Comment(post_id=postid, user_id=user.id, time_comment=now, body=body)
        comment.save()
        p = db.session.query(Post).filter(Post.id == postid).one()
        post = Post(id=p.id, time_update=now, comment_count=p.comments.count())
        post.update()
        return redirect_back()
    else:
        flash('评论不能少于6个字！！')
        return redirect_back()


@app.route('/topic/<postid>/<int:page>/reply', methods=['GET', 'POST'])
@login_required
def reply(postid, page):
    db = g.db
    user = g.user
    body = request.values.get('body')
    if body:
        comment = db.session.query(Comment).filter(Comment.id == request.values.get('reply')).one()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment.reply_comment(user, now, body)
        add_alert(you_id=user.id,
                  me_id=comment.user_id,
                  operation='回复了你的评论',
                  url='/topic/%s#comment-area' % comment.post_id,
                  context=body)
        return redirect('/topic/%s?page=%s#comment-area' % (postid, page))
    else:
        flash('评论不能少于6个字！！')
        return redirect('/topic/%s?page=%s' % (postid, page))


@app.route('/quota/<postid>/reply', methods=['GET', 'POST'])
@login_required
def quota_reply(postid):
    db = g.db
    user = g.user
    body = request.values.get('body')
    if body:
        comment = db.session.query(Comment).filter(Comment.id == request.values.get('reply')).one()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        comment.reply_comment(user, now, body)
        add_alert(you_id=user.id,
                  me_id=comment.user_id,
                  operation='回复了你的评论',
                  url=request.values.get('back'),
                  context=body)
        return redirect_back()
    else:
        flash('评论不能少于6个字！！')
        return redirect_back()


@app.route('/people/save_draft', methods=['GET', 'POST'])
@login_required
def save_draft():
    db = g.db
    user = g.user
    title = request.values.get('title')
    body = request.values.get('body')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    abstext = get_abstract(html_strip(body))
    draft = Draft(title=title, time_post=now, time_update=now, body=body, author_id=user.id,
                  abstract=abstext)
    draft.save()
    return redirect_back()


@app.route('/people/del_draft/<draft_id>', methods=['GET', 'POST'])
@login_required
def del_draft(draft_id):
    db = g.db
    user = g.user
    try:
        draft = db.session.query(Draft).filter(Draft.id == draft_id).one()
    except:
        draft = []
    user.del_draft(draft)
    return redirect_back()


@app.route('/people/update_draft/<draft_id>', methods=['GET', 'POST'])
@login_required
def update_draft(draft_id):
    db = g.db
    user = g.user
    title = request.values.get('title')
    body = request.values.get('body')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    abstext = get_abstract(html_strip(body))
    draft = Draft(id=draft_id, title=title, time_update=now, body=body, author_id=user.id,
                  abstract=abstext)
    draft.update()
    return redirect_back()


@app.route('/people/change_avatar', methods=['GET', 'POST'])
@login_required
def change_avatar():
    db = g.db
    user_id = g.user.id
    avatar_id = request.values.get('avatar')
    avatar_url = 'static/avatar/' + avatar_id + '.png'
    user = User(id=user_id, avatar=avatar_url)
    user.update()
    return redirect('/people/edit')


@app.route('/people/change_profile', methods=['GET', 'POST'])
@login_required
def change_profile():
    db = g.db
    user_id = g.user.id
    user = User(id=user_id)
    gender = request.values.get('gender')
    user.sex = gender
    if request.values.get('occupation'):
        user.occupation = request.values.get('occupation')
    if request.values.get('brief'):
        user.brief = request.values.get('brief')
    user.update()
    return redirect('/people/%s' % g.user.id)


@app.route('/people/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = g.user
    oldpass = request.values.get('oldpassword')
    if bcrypt.check_password_hash(user.password.encode('utf-8'), oldpass.encode('utf-8')):
        if request.values.get('password') == request.values.get('repeat'):
            password = bcrypt.generate_password_hash(request.values.get('password').encode('utf-8'))
            user = User(id=user.id, password=password)
            user.update()
            flash('修改密码成功')
        else:
            flash('两次密码输入不一致')
    else:
        flash('原始密码错误')
    return redirect('/people/privicy')


@app.route('/people/<user_id>/send_message', methods=['GET', 'POST'])
@login_required
def send_message(user_id):
    db = g.db
    me = g.user
    body = request.values.get('body')
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    you = db.session.query(User).filter(User.id == user_id).one()
    me.send_message(you, body, now)
    add_alert(you_id=me.id, me_id=you.id, operation='私信了你', url='/people/%s/message' % me.id, context=body)
    return redirect('/people/%s/message' % user_id)


@app.route('/people/read_alert/<alert_id>', methods=['GET', 'POST'])
@login_required
def read_alert(alert_id):
    db = g.db
    me = g.user
    alert = db.session.query(Alert).filter(Alert.id == alert_id).one()
    if me.id != alert.me_id:
        return redirect(url_for(page_not_found))
    alert.read()
    return redirect(alert.url)


@app.route('/people/<user_id>/follow', methods=['GET', 'POST'])
@login_required
def follow_user(user_id):
    db = g.db
    follower = g.user
    followee = db.session.query(User).filter(User.id == user_id).one()
    follower.follow(followee)
    add_alert(you_id=follower.id,
              me_id=user_id,
              operation='关注了你',
              url='/people/%s' % follower.id,
              context='查看%s的资料' % follower.nickname)
    return redirect_back()


@app.route('/people/<user_id>/unfollow', methods=['GET', 'POST'])
@login_required
def unfollow_user(user_id):
    db = g.db
    follower = g.user
    followee = db.session.query(User).filter(User.id == user_id).one()
    follower.unfollow(followee)
    add_alert(you_id=follower.id,
              me_id=user_id,
              operation='对你取消了关注',
              url='/people/%s' % follower.id,
              context='查看%s的资料' % follower.nickname)
    return redirect_back()


@app.route('/logout')
@login_required
def logout():
    user = current_user
    user.logged_in = False
    session.clear()
    logout_user()
    return redirect(url_for('homepage'))


# ---------------------------------------------DATA_API-------------------------------------------------------------
@app.route('/data/get_nxb_quota', methods=['GET', 'POST'])
def get_nxb_quota():
    time = request.values.get('time')
    code = request.values.get('code')
    date = request.values.get('date')
    sql = ''
    if date == '-1':
        sql = 'select date from %s_real order by date desc limit 1' % code
        trade_date = pd.read_sql(sql, data_engine)['date'][0]
        sql = 'select * from %s_real where date="%s" and time>"%s" order by time' % (code, trade_date, time)
    else:
        trade_date = date
        sql = 'select * from %s_1min where date="%s" and time>"%s" order by time' % (code, trade_date, time)
    df = pd.read_sql(sql, data_engine)
    df['discount'] = round(df['last_price'] / df['svs_last_price'] - 1, 4) * 100
    last_price = df['last_price'].tolist()
    svs_last_price = df['svs_last_price'].tolist()
    try:
        quota_dict = {'succeed': 0, 'time': df['time'].tolist()[-1], 'len': len(df),
                      'min': min(min(last_price), min(svs_last_price)),
                      'data': {'last_price': last_price,
                               'svs_price': svs_last_price,
                               'time': df['time'].tolist(),
                               'amount': df['diff'].tolist(),
                               'discount': df['discount'].tolist()}}
    except:
        quota_dict = {'succeed': 1}
    return json.dumps(quota_dict)


@app.route('/data/get_nxb_history', methods=['GET', 'POST'])
def get_nxb_history():
    code = request.values.get('code')
    backward = request.values.get('day')
    sql = 'select date from %s_10min order by date desc limit 1' % code
    trade_date = pd.read_sql(sql, data_engine)['date'][0]
    past = datetime.strptime(trade_date, '%Y%m%d') - timedelta(days=int(backward) + 1)
    date = datetime.strftime(past, "%Y%m%d")

    sql = 'select * from %s_10min where date>"%s" order by datetime' % (code, date)
    df = pd.read_sql(sql, data_engine)
    last_price = df['last_price'].tolist()
    svs_last_price = df['svs_last_price'].tolist()
    df['discount'] = round(df['last_price'] / df['svs_last_price'] - 1, 4) * 100
    quota_dict = {'succeed': 0, 'len': len(df),
                  'min': min(min(last_price), min(svs_last_price)),
                  'data': {'last_price': last_price,
                           'svs_price': svs_last_price,
                           'datetime': df['datetime'].tolist(),
                           'discount': df['discount'].tolist(),
                           'amount': df['diff'].tolist()}}
    return json.dumps(quota_dict)


@app.route('/data/get_zdb_history', methods=['GET', 'POST'])
def get_zdb_history():
    sql = 'select * from zdb_ratio'
    df = pd.read_sql(sql, data_engine)
    df['ratio'] = round(df['amount_up'] / df['amount_down'], 3)

    def cal_up_gain(row):
        if row['p_change'] > 0:
            up = round(row['p_change'] * (1 / row['ratio']) * 300, 2)
            return up
        else:
            up = round(row['p_change'] * 300, 2)
            return up

    def cal_down_gain(row):
        if row['p_change'] > 0:
            down = round(row['p_change'] * -300, 2)
            return down
        else:
            down = round(row['p_change'] * (row['ratio'] / 1) * -300, 2)
            return down

    up_gain = df.apply(cal_up_gain, axis=1)
    down_gain = df.apply(cal_down_gain, axis=1)


    quota_dict = {'succeed': 0, 'len': len(df),
                  'data': {'amount_up': df['amount_up'].tolist(),
                           'amount_down': (df['amount_down']).tolist(),
                           'ratio': df['ratio'].tolist(),
                           'up_gain': list(up_gain),
                           'down_gain': list(down_gain),
                           'date': df['date'].astype(str).tolist()}}
    return json.dumps(quota_dict)


@app.route('/data/get_nxb_price', methods=['GET', 'POST'])
def get_nxb_price():
    code = request.values.get('code')
    sql = 'select * from nxb_price where fund_code=%s' % code
    df = pd.read_sql(sql, data_engine)
    df['different'] = round(df['last_price'].astype(float) - df['svs_last_price'].astype(float), 3)
    data = df.to_dict(orient='index')
    discount = round(float(data[0]['last_price']) / float(data[0]['svs_last_price']) - 1, 4)
    try:
        price_dict = {'succeed': 0, 'time': data[0]['time'], 'discount': str(round(discount * 100, 2)) + '%',
                      'data': data[0]}
    except:
        price_dict = {'succeed': 1}
    return json.dumps(price_dict)


@app.route('/data/get_nxb_deal', methods=['GET', 'POST'])
def get_nxb_deal():
    code = request.values.get('code')
    sql = 'select * from nxb_price where fund_code=%s limit 1' % code
    df = pd.read_sql(sql, data_engine)
    data = df.to_dict(orient='index')
    close_price = data[0]['close_price']
    sql = 'select date from nxb_deal order by date desc limit 1'
    trade_date = pd.read_sql(sql, data_engine)['date'][0]
    sql = 'select * from nxb_deal where date="%s" and code="%s" order by time desc limit 10' % (trade_date, code)
    df = pd.read_sql(sql, data_engine)[::-1]
    deal_dict = {'succeed': 0, 'close_price': close_price,
                 'data': {'time': df['time'].tolist(),
                          'price': df['price'].tolist(),
                          'amount': df['amount'].tolist(),
                          'direction': df['direction'].tolist()}}
    return json.dumps(deal_dict)


@app.route('/data/get_zdb_real', methods=['GET', 'POST'])
def get_zdb_real():
    sql = 'select amount_up,amount_down from zdb_real order by date desc, time desc limit 1'
    df = pd.read_sql(sql, data_engine)
    df['k'] = round(df['amount_up'].astype(float) / df['amount_down'].astype(float), 2)
    zdb_data = df.to_dict(orient='index')[0]
    sql = 'select * from cyb_real order by datetime desc limit 1'
    df = pd.read_sql(sql, data_engine)
    cyb_data = df.to_dict(orient='index')[0]
    sql = 'select * from zdb_ratio order by date desc limit 1'
    zdb_his = pd.read_sql(sql, data_engine)
    his_data = zdb_his.to_dict(orient='index')[0]
    real_dict = {'succeed': 0,
                 'data': {'amount_up': float(zdb_data['amount_up']),
                          'amount_down': float(zdb_data['amount_down']),
                          'his_up': float(his_data['amount_up']),
                          'his_down': float(his_data['amount_down']),
                          'k': zdb_data['k'],
                          'cyb_change': round(cyb_data['change'] * 100, 2),
                          'datetime': cyb_data['datetime']}}
    return json.dumps(real_dict)
