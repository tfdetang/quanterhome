from flask_wtf import Form
from flask import g
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, RadioField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf.file import FileAllowed, FileRequired
from functools import wraps


# -------------------------------------Forms------------------------------------------


class LoginForm(Form):
    email = StringField('email', validators=[DataRequired(), Email()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class Register(Form):
    email = StringField('email', validators=[DataRequired(), Email()])
    nickname = StringField('nickname', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired(), Length(min=6, max=12)])
    repeat = PasswordField('repeat', validators=[DataRequired(), EqualTo('password')])


class Editor(Form):
    title = StringField('title', validators=[DataRequired(), Length(min=6, max=30)])
    # body = TextAreaField('body', validators=[DataRequired(), Length(min=6)])


class CommentForm(Form):
    body = TextAreaField('body', validators=[DataRequired(), Length(min=6)])


class Profile(Form):
    gender = RadioField('gender', choices=[(1, '男'), (2, '女')], default=1)
    occupation = StringField('occupation', validators=[Length(max=10)])
    brief = TextAreaField('brief')


class Themecreate(Form):
    name = StringField('name', validators=[DataRequired(), Length(max=10)])
    url = StringField('url', validators=[DataRequired(), Length(max=10)])
    introduce = TextAreaField('introduce', validators=[DataRequired(), Length(max=50)])
    file = FileField('file', validators=[FileRequired(), FileAllowed(upload_set=('jpg', 'jpeg', 'png', 'gif'))])


class ChangePass(Form):
    oldpassword = PasswordField('oldpassword', validators=[DataRequired(), Length(min=6, max=12)])
    password = PasswordField('password', validators=[DataRequired(), Length(min=6, max=12)])
    repeat = PasswordField('repeat', validators=[DataRequired(), EqualTo('password')])

# -----------------------------------Validators----------------------------------------
