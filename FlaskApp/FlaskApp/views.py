try:
    from FlaskApp.FlaskApp import app, db
except:
    import sys

    sys.path.append('..')
    from FlaskApp import app, db
from datetime import datetime
from functools import wraps

import markdown
from flask import render_template, flash, redirect, session, url_for, request, g, Markup
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, LoginManager

from FlaskApp import Model
from FlaskApp import forms
from FlaskApp.tools import toc
from FlaskApp.tools.utils import momentjs, random_avatar, paginate, date_past

# ----------------------------init_settings----------------------------------


lm = LoginManager()
lm.init_app(app)
bcrypt = Bcrypt(app)

User = Model.User
Post = Model.Post
Theme = Model.Theme
Comment = Model.Comment
Message = Model.Message
Moment = Model.Moment
Alert = Model.Alert

app.jinja_env.globals['len'] = len
app.jinja_env.globals['str'] = str
app.jinja_env.globals['momentjs'] = momentjs
app.jinja_env.globals['Markup'] = Markup
app.jinja_env.globals['markdown'] = markdown.markdown


# -----------------------------events----------------------------------


@lm.user_loader
def load_user(id):
    db = g.db
    try:
        return db.session.query(User).filter(User.id == id).one()
    except:
        return None


@app.before_request
def before_request():
    g.user = current_user
    g.db = db


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('请先登陆或注册！')
            return redirect(url_for('registration'))
    return wrap


# -----------------------------utils------------------------------------------


def register(form):
    db = g.db
    if form.validate_on_submit():
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            if load_email(db, form.email.data):
                flash('This user name is already taken!')
        except:
            new_user = User(nickname=form.nickname.data,
                            password=bcrypt.generate_password_hash(form.password.data.encode('utf-8')),
                            email=form.email.data,
                            time_regist=now,
                            role='user',
                            avatar=random_avatar())
            new_user.save()
            flash('已成功注册，欢迎！！')
            return True
    else:
        for error in form.password.errors:
            flash(error)
        for error in form.email.errors:
            flash(error)
        for error in form.repeat.errors:
            flash(error)


def log_in(form):
    db = g.db
    if form.validate_on_submit():
        try:
            user = load_email(db, form.email.data.encode('utf-8'))
            if bcrypt.check_password_hash(user.password.encode('utf-8'), form.password.data.encode('utf-8')):
                session['logged_in'] = True
                session['id'] = user.id
                session['username'] = user.nickname
                session['avatar'] = user.avatar
                if form.remember_me.data:
                    remember = True
                else:
                    remember = False
                login_user(user, remember=remember)
                flash('欢迎登陆')
                return True
            else:
                form.password.errors.append('密码错误')
                flash('密码错误')
        except:
            form.email.errors.append('用户名不存在')
            flash('用户名不存在')
    else:
        for error in form.email.errors:
            flash(error)
        for error in form.password.errors:
            flash(error)


def comment(form):
    if form.validate_on_submit():
        pass
    else:
        for error in form.body.errors:
            flash(error)
            flash('评论不能少于6个字！！')


def load_email(db, email):
    return db.session.query(User).filter(User.email == email).one()


# -----------------------------page_handlers-----------------------------------


@app.route('/', methods=['GET', 'POST'])
def homepage():
    registform = forms.Register()
    if request.method == 'POST':
        registed = register(registform)
        if registed:
            return redirect(url_for('lobby'))
    return render_template('main.html', registform=registform)


@app.route('/register', methods=['GET', 'POST'])
def registration():
    loginform = forms.LoginForm()
    registform = forms.Register()
    if request.method == 'POST':
        form_name = request.form['form-name']
        if form_name == 'login':
            login = log_in(loginform)
            if login:
                return redirect(url_for('lobby'))
        else:
            registed = register(registform)
            if registed:
                return redirect(url_for('lobby'))
    return render_template('register.html', loginform=loginform, registform=registform)


@app.route('/lobby', methods=['GET', 'POST'])
def lobby():
    db = g.db
    user = g.user
    themeform = forms.Themecreate()
    try:
        if request.values.get('type') == 'favo':
            themes = user.favo_themes.all()
            type = 'favo'
        else:
            themes = db.session.query(Theme).all()
            type = 'all'
    except:
        themes = []
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect('/lobby')
    return render_template('lobby.html', loginform=loginform, themes=themes, type=type, themeform=themeform)


@app.route('/lobby/<topic_theme>/', methods=['GET', 'POST'])
def dashboard(topic_theme):
    db = g.db
    page_limit = 8
    theme = db.session.query(Theme).filter(Theme.url == topic_theme).one()
    try:
        if request.values.get('method'):
            method = request.values.get('method')
        else:
            method = 'all'
    except:
        method = 'all'
    try:
        if request.values.get('page'):
            page = int(request.values.get('page'))
        else:
            page = 1
    except:
        page = 1
    try:
        if method == 'followed':
            query = g.user.followed_posts().filter(Post.theme == theme.id)
        elif method == 'hot':
            query = db.session.query(Post).filter(Post.theme == theme.id).order_by(Post.comment_count.desc())
        else:
            query = db.session.query(Post).filter(Post.theme == theme.id).order_by(Post.time_update.desc())
        post_len = query.count()
        posts = query.offset(0 + (page_limit * (page - 1))).limit(page_limit).all()
    except:
        posts = []
        post_len = 0
    page_info = paginate(page, page_limit, post_len)
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect('/lobby/%s/' % topic_theme)
    return render_template('dashboard.html', loginform=loginform, posts=posts, theme=theme, page_info=page_info,
                           method=method)


@app.route('/<theme_url>/new_post', methods=['GET', 'POST'])
@login_required
def new_post(theme_url):
    db = g.db
    try:
        theme = db.session.query(Theme).filter(Theme.url == theme_url).one()
    except:
        theme = []
    editorform = forms.Editor()
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect('/lobby/%s/1' % theme_url)
    return render_template('new_post.html', editorform=editorform, theme=theme, loginform=loginform)


@app.route('/<post_id>/editor', methods=['GET', 'POST'])
@login_required
def editor(post_id):
    db = g.db
    try:
        post = db.session.query(Post).filter(Post.id == post_id).one()
    except:
        post = []
    if not g.user.id == post.author.id:
        return redirect('/topic/%s/1' % post_id)
    editorform = forms.Editor()
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect('/topic/%s/1' % post_id)
    return render_template('editor.html', editorform=editorform, post=post, loginform=loginform)


@app.route('/topic/<topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    db = g.db
    try:
        if request.values.get('page'):
            page = int(request.values.get('page'))
        else:
            page = 1
    except:
        page = 1
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect('/topic/%s' % (topic_id))
    commentform = forms.CommentForm()
    comment(commentform)
    p = db.session.query(Post).filter(Post.id == topic_id).one()
    page_limit = 10
    if 'logged_in' in session:
        p.read(g.user)
    try:
        comments_len = p.comments.count()
        comments = p.comments.order_by(Comment.id.desc()).offset(0 + (page_limit * (page - 1))).limit(page_limit).all()
    except:
        comments = []
        comments_len = 0
    page_info = paginate(page, page_limit, comments_len)
    body = Markup(markdown.markdown(p.body, ['markdown.extensions.extra', 'markdown.extensions.toc']))
    TOC = Markup(toc.markdown_toc(body))
    return render_template('topic.html', loginform=loginform, body=body, post=p, commentform=commentform,
                           page_info=page_info, comments=comments, page=page, TOC=TOC)


@app.route('/people/<user_id>', methods=['GET', 'POST'])
@login_required
def profile(user_id):
    db = g.db
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    try:
        user = db.session.query(User).filter(User.id == user_id).one()
        moments = db.session.query(Moment).filter(Moment.user_id == user_id).order_by(Moment.time_moment.desc()).all()
    except:
        user = g.user
        moments = db.session.query(Moment).filter(Moment.user_id == user.id).order_by(Moment.time_moment.desc()).all()
    return render_template('profile.html', loginform=loginform, user=user, moments=moments)


@app.route('/people/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    db = g.db
    user = g.user
    if g.user.sex == 0:
        profileform = forms.Profile(sex=None)
    else:
        profileform = forms.Profile(sex=g.user.sex)
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    return render_template('profile_editor.html', loginform=loginform, user=user, profileform=profileform)


@app.route('/people/<user_id>/post', methods=['GET', 'POST'])
@login_required
def profile_post(user_id):
    db = g.db
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    user = db.session.query(User).filter(User.id == user_id).one()
    posts = db.session.query(Post).filter(Post.author_id == user_id).order_by(Post.time_post.desc()).all()
    return render_template('profile_post.html', loginform=loginform, user=user, posts=posts)


@app.route('/people/<user_id>/message', methods=['GET', 'POST'])
@login_required
def profile_message(user_id):
    db = g.db
    loginform = forms.LoginForm()
    messageform = forms.CommentForm()
    login = log_in(loginform)
    messages = g.user.messages.filter(Message.you_id == user_id).order_by(Message.id.desc()).all()
    if login:
        return redirect(url_for('lobby'))
    user = db.session.query(User).filter(User.id == user_id).one()
    return render_template('profile_message.html', loginform=loginform, user=user, messageform=messageform,
                           messages=messages)


@app.route('/people/notify', methods=['GET', 'POST'])
@login_required
def profile_notify():
    db = g.db
    user = g.user
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    alerts = db.session.query(Alert).filter(Alert.me_id == user.id).order_by(Alert.id.desc()).all()
    return render_template('profile_notification.html', loginform=loginform, user=user, alerts=alerts)


@app.route('/people/privicy', methods=['GET', 'POST'])
@login_required
def profile_privicy():
    db = g.db
    user = g.user
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    ChangePassform = forms.ChangePass()
    return render_template('profile_privicy.html', loginform=loginform, user=user, ChangePassform=ChangePassform)


@app.route('/moments', methods=['GET', 'POST'])
@login_required
def show_moments():
    db = g.db
    try:
        if request.values.get('limit'):
            limit = request.values.get('limit')
        else:
            limit = 20
    except:
        limit = 20
    try:
        if request.values.get('method'):
            method = request.values.get('method')
        else:
            method = 'all'
    except:
        method = 'all'
    user = g.user
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))

    if method == 'post':
        moments_method = user.followed_moments().filter(Moment.operation == '发表了文章')
    elif method == 'comment':
        moments_method = user.followed_moments().filter(Moment.operation == '评论了')
    elif method == 'agree':
        moments_method = user.followed_moments().filter(Moment.operation == '赞了文章')
    else:
        moments_method = user.followed_moments()

    if limit == 'week':
        moments = moments_method.filter(Moment.time_moment > date_past(7)).all()
        print('week')
    elif limit == 'month':
        moments = moments_method.filter(Moment.time_moment > date_past(30)).all()
    else:
        moments = moments_method.limit(int(limit)).all()
    return render_template('moments.html', loginform=loginform, user=user, moments=moments, limit=limit, method=method)


@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    db = g.db
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    keyword = str(request.values.get('keyword'))
    finduser = User.query.whoosh_search(keyword).all()
    findpost = Post.query.whoosh_search(keyword).all()
    pass


@app.route('/quota/nxb', methods=['GET', 'POST'])
def nxb_quota():
    db = g.db
    try:
        if request.values.get('date'):
            date = request.values.get('date')
        else:
            date = '-1'
    except:
        date = '-1'
    try:
        if request.values.get('code'):
            code = request.values.get('code')
        else:
            code = '878004'
    except:
        code = '878004'
    codedict = {'878002': '沪深300看涨',
                '878003': '沪深300看跌',
                '878004': '创业看涨',
                '878005': '创业看跌',
                '878006': '上证50看涨',
                '878007': '上证50看跌',
                '878008': '中证500看涨',
                '878009': '中证500看跌'}
    name = codedict[code]
    user = g.user
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    return render_template('nxb_quota.html', loginform=loginform, user=user, date=date, code=code, name=name)


@app.route('/quota/nxb_history', methods=['GET', 'POST'])
def nxb_history():
    db = g.db
    try:
        if request.values.get('day'):
            day = request.values.get('day')
        else:
            day = '10'
    except:
        day = '10'
    try:
        if request.values.get('code'):
            code = request.values.get('code')
        else:
            code = '878004'
    except:
        code = '878004'
    codedict = {'878002': '沪深300看涨',
                '878003': '沪深300看跌',
                '878004': '创业看涨',
                '878005': '创业看跌',
                '878006': '上证50看涨',
                '878007': '上证50看跌',
                '878008': '中证500看涨',
                '878009': '中证500看跌'}
    name = codedict[code]
    user = g.user
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    return render_template('nxb_history.html', loginform=loginform, user=user, day=day, code=code, name=name)


@app.route('/quota/zdb_history', methods=['GET', 'POST'])
def zdb_history():
    db = g.db
    user = g.user
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    return render_template('zdb_history.html', loginform=loginform, user=user)


@app.route('/404')
@app.errorhandler(404)
def page_not_found(e):
    loginform = forms.LoginForm()
    login = log_in(loginform)
    if login:
        return redirect(url_for('lobby'))
    return render_template('page_not_found.html', loginform=loginform)
