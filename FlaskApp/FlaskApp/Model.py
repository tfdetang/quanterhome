try:
    from FlaskApp.FlaskApp import app, db
except:
    import sys

    sys.path.append('..')
    from FlaskApp import app, db
from sqlalchemy import Column, String, Integer, Text, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from flask_login import UserMixin
import flask_whooshalchemyplus as whooshalchemy
from jieba.analyse import ChineseAnalyzer

Base = declarative_base()

# ----------------------------------------------Util_tools---------------------------------

class Utils:
    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.merge(self)
        db.session.commit()

# ----------------------------------------------Associate_obj-------------------------------


follower = Table('follower', Base.metadata,
                 Column('follower_id', Integer, ForeignKey('user.id')),
                 Column('followed_id', Integer, ForeignKey('user.id')))


reply = Table('reply', Base.metadata,
              Column('comment_id', Integer, ForeignKey('comment.id')),
              Column('reply_id', Integer, ForeignKey('comment.id')))

post_read = Table('post_read', Base.metadata,
                  Column('post_id', Integer, ForeignKey('post.id')),
                  Column('user_id', Integer, ForeignKey('user.id')))

theme_favo = Table('theme_favo', Base.metadata,
                   Column('theme_id', Integer, ForeignKey('theme.id')),
                   Column('user_id', Integer, ForeignKey('user.id')))


class tag(Base, db.Model,Utils):

    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey('user.id'))
    tag_id = Column(ForeignKey('label.id'))
    tag_post = Column(ForeignKey('post.id'))
    label = relationship('Label', backref='label_tags')


class like(Base, db.Model,Utils):

    __tablename__ = 'like_post'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(ForeignKey('post.id'))
    user_id = Column(ForeignKey('user.id'))
    value = Column(Integer)

# -----------------------------------------------Model---------------------------------------


class Message(Base, db.Model,Utils):

    __tablename__ = 'message'

    id = Column(Integer, primary_key=True, autoincrement=True)
    me_id = Column(ForeignKey('user.id'))
    you_id = Column(String(45))
    direction = Column(Integer)
    body = Column(Text)
    time_send = Column(String(45))
    status = Column(Integer)


class User(Base, Utils, db.Model,UserMixin):

    __tablename__ = 'user'
    __searchable__ = ['nickname']
    __analyzer__ = ChineseAnalyzer()

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(45))
    nickname = Column(String(45))
    password = Column(Text)
    time_regist = Column(String(45))
    role = Column(String(10))
    avatar = Column(String(45))
    sex = Column(Integer)
    occupation = Column(String(10))
    brief = Column(String(45))
    followed = relationship('User',
                            secondary=follower,
                            primaryjoin=(follower.c.follower_id == id),
                            secondaryjoin=(follower.c.followed_id == id),
                            backref = backref('followers', lazy='dynamic'),
                            lazy='dynamic')
    post = relationship('Post', backref ='author', lazy ='dynamic')
    post_like = relationship('Post',
                              secondary='like_post',
                              backref='liked_user', lazy='dynamic')
    comments = relationship('Comment', backref='commented_user', lazy='dynamic')
    tag_added = relationship('tag', backref='user_tag', lazy='dynamic')
    themes = relationship('Theme', backref='theme_creator', lazy='dynamic')
    messages = relationship('Message', backref='user_messages', lazy='dynamic')
    favo_themes = relationship('Theme',
                               secondary = theme_favo,
                               backref='users_favo', lazy='dynamic')
    alerts = relationship('Alert', backref='alert_sender', lazy='dynamic')
    moments = relationship('Moment', backref='moments_user', lazy='dynamic')


    def is_authenticate(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return self.id
        except:
            return None

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            self.save()
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            self.save()
            return self

    def is_following(self, user):
        return self.followed.filter(follower.c.followed_id==user.id).count() > 0

    def send_message(self, user, body, time):
        me_message = Message(me_id=self.id, you_id=user.id, body=body, direction=0, time_send=time)
        you_message = Message(me_id=user.id, you_id=self.id, body=body, direction=1, time_send=time)
        me_message.save()
        you_message.save()

    def count_like(self):
        count = 0
        for post in self.post:
            count += post.liked.filter(like.value == 0).count()
        return count

    def followed_posts(self):
        return db.session.query(Post).join(follower, (follower.c.followed_id == Post.author_id))\
                             .filter(follower.c.follower_id == self.id)\
                             .order_by(Post.time_post.desc())

    def followed_moments(self):
        return db.session.query(Moment).join(follower, (follower.c.followed_id == Moment.user_id))\
                               .filter(follower.c.follower_id == self.id)\
                               .order_by(Moment.time_moment.desc())

    def favo_theme(self, theme):
        if not self.is_favoed(theme):
            self.favo_themes.append(theme)
            self.save()
            return self

    def unfavo_theme(self, theme):
        if self.is_favoed(theme):
            self.favo_themes.remove(theme)
            self.save()
            return self

    def is_favoed(self, theme):
        return self.favo_themes.filter(theme_favo.c.theme_id == theme.id).count() > 0

    def find_Alert(self):
        return db.session.query(Alert).filter((Alert.me_id == self.id) & (Alert.is_read == 0))

    def __repr__(self):
        return '<User %s>' % self.nickname


class Alert(Base, db.Model,Utils):

    __tablename__ = 'alert'

    id = Column(Integer, primary_key=True, autoincrement=True)
    me_id = Column(Integer)
    you_id = Column(ForeignKey('user.id'))
    operation = Column(String(45))
    url = Column(Text)
    context = Column(Text)
    time_alert = Column(String(45))
    is_read = Column(Integer)

    def read(self):
        read_alert = Alert(id=self.id, is_read=1)
        read_alert.update()


class Moment(Base, db.Model,Utils):

    __tablename__ = 'moment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(ForeignKey('user.id'))
    operation = Column(String(45))
    url = Column(Text)
    url_name = Column(String(45))
    context = Column(Text)
    time_moment = Column(String(45))


class Theme(Base, db.Model,Utils):

    __tablename__ = 'theme'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45))
    url = Column(String(45))
    introduce = Column(Text)
    creator = Column(ForeignKey('user.id'))
    theme_posts = relationship('Post', backref='post_theme', lazy='dynamic')

    def creat_theme(self, name, url, user,introduce):
        if not self.is_theme(name):
            new_theme= Theme(name=name, url=url, introduce=introduce, creator=user.id)
            new_theme.save()

    def is_theme(self, name):
        return db.session.query(Theme).filter(Theme.name==name).count() > 0


class Post(Base, db.Model,Utils):

    __tablename__ = 'post'
    __searchable__ = ['title', 'abstract']
    __analyzer__ = ChineseAnalyzer()

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(45))
    abstract = Column(Text)
    body = Column(Text)
    time_post = Column(String(45))
    time_update = Column(String(45))
    comment_count = Column(Integer)
    theme = Column(ForeignKey('theme.id'))
    author_id = Column(ForeignKey('user.id'))
    liked = relationship('like', backref='post_liked', lazy='dynamic')
    user_like = relationship('User',
                             secondary='like_post',
                             backref='liked_post', lazy='dynamic')
    user_read = relationship('User',
                             secondary='post_read',
                             backref='read_post', lazy='dynamic')
    comments = relationship('Comment', backref='commented_post', lazy='dynamic')
    post_tags = relationship('tag', backref='tag_posts', lazy='dynamic')

    def read(self, user):
        if not self.is_read(user):
            self.user_read.append(user)
            self.save()
            return self

    def is_read(self, user):
        return self.user_read.filter(post_read.c.user_id==user.id).count() > 0

    def like_post(self, user, value):
        if not self.is_liked(user):
            Like = like(value=value, post_id=self.id, user_id=user.id)
            Like.save()

    def is_liked(self, user):
        return self.user_like.filter(like.user_id == user.id).count() > 0

    def liked_value(self, user):
        return self.liked.filter(like.user_id == user.id).one().value

    def liked_count(self):
        try:
            liked = self.liked.filter(like.value==0).count()
        except:
            liked = 0
        try:
            disliked = self.liked.filter(like.value==1).count()
        except:
            disliked = 0
        return {'like':liked, 'dislike':disliked}

    def comment_post(self, user, time, body):
        new_comment = Comment(post_id=self.id, user_id=user.id, comment_time=time, body=body)
        new_comment.save()

    def add_tag(self, name, userid):
        if self.is_labeled(name):
            pass
        else:
            new_label = Label(name=name)
            new_label.save()
        label = db.session.query(Label).filter(Label.name == name).one()

        if not self.is_hastag(label):
            new_tag = tag(tag_id=label.id, user_id=userid)
            self.post_tags.append(new_tag)
            self.save()
            return self

    def is_labeled(self, name):
        return db.session.query(Label).filter(Label.name==name).count() > 0

    def is_hastag(self, label):
        return self.post_tags.filter(tag.tag_id==label.id).count() > 0

    def __repr__(self):
        return '<Post %s>' % self.id


class Label(Base, db.Model,Utils):

    __tablename__ = 'label'
    __searchable__ = ['name']
    __analyzer__ = ChineseAnalyzer()

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45))

    def __repr__(self):
        return '<Label %s>' % self.name


class Comment(Base, db.Model,Utils):

    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(ForeignKey('post.id'))
    user_id = Column(ForeignKey('user.id'))
    time_comment = Column(String(45))
    body = Column(Text)
    replies = relationship('Comment',
                           secondary=reply,
                           primaryjoin=(reply.c.reply_id == id),
                           secondaryjoin=(reply.c.comment_id == id),
                           backref = 'replied_comment', lazy='dynamic')

    def reply_comment(self, user, time, body):
        new_reply = Comment(user_id=user.id, time_comment=time, body=body)
        new_reply.save()
        self.replies.append(new_reply)
        self.save()
        return self

    def __repr__(self):
        return '<Comment %s>' % self.id

# -------------------------------------------Searchble_setting---------------------------

whooshalchemy.init_app(app)
with app.app_context():
    whooshalchemy.whoosh_index(app, User)
    whooshalchemy.whoosh_index(app, Post)
    whooshalchemy.whoosh_index(app, Label)

# --------------------------------------------Test----------------------------------------


if __name__ == '__main__':

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, relationship, backref, scoped_session
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_size=120,
                           pool_recycle=20)
    session_factory = sessionmaker(bind=engine)
    DBSession = scoped_session(session_factory)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

