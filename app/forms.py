from app import db
from app.models import User
from sqlalchemy import select
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SubmitField, EmailField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password')
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password')
    repeat_password = PasswordField('Repeat Password', validators=[EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Username is already taken!')

    def valdiate_email(self, email):
        user = db.session.scalar(select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('This email address has already created an account.')
        

class PostForm(FlaskForm):
    body = TextAreaField('Message', validators=[DataRequired(), length(min=1, max=256)])
    submit = SubmitField('Post')


class EditProfileForm(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.orignial_username = user.username
        
    def validate_username(self, username):
        if username.data != self.orignial_username:
            user = db.session.scalar(select(User).where(User.username==username.data))
            if user is not None:
                raise ValidationError('Please choose another username.')
        

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PasswordResetRequest(FlaskForm):
    email = EmailField('Email', validators=[Email()])
    submit = SubmitField('Submit')


class PasswordReset(FlaskForm):
    password = PasswordField('Password')
    repeat_password = PasswordField('Repeat Password', validators=[EqualTo('password')])
    submit = SubmitField('Sumbit')


class SendMessage(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SendMessageChat(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send')