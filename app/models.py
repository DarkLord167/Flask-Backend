import json
from app import app, db, login, mail
from flask import render_template
from flask_mail import Message as EMAIL
import jwt
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, Table, Column, Integer, func, select, or_, Text, and_, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped, aliased
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from time import time

followers = Table(
        'followers',
        db.metadata,
        Column('follower_id', Integer, ForeignKey('user.id'), primary_key=True),
        Column('followed_id', Integer, ForeignKey('user.id'), primary_key=True)
        )

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(String(128), index=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    last_seen: Mapped[Optional[datetime]] = mapped_column(default=lambda: datetime.now(timezone.utc))
    about_me: Mapped[Optional[str]] = mapped_column(String(256))

    posts: WriteOnlyMapped['Post'] = relationship(back_populates='author')
    
    following: WriteOnlyMapped['User'] = relationship(
            secondary='followers',
            primaryjoin=followers.c.follower_id == id,
            secondaryjoin=followers.c.followed_id == id,
            back_populates='followers'
            )
    
    followers: WriteOnlyMapped['User'] = relationship(
            secondary='followers',
            primaryjoin=followers.c.followed_id == id,
            secondaryjoin=followers.c.follower_id == id,
            back_populates='following'
        )

    messages_sent: WriteOnlyMapped['Message'] = relationship(foreign_keys='Message.sender_id', back_populates='author')
    messages_received: WriteOnlyMapped['Message'] = relationship(foreign_keys='Message.recipient_id', back_populates='recipient')

    notifications: WriteOnlyMapped['Notification'] = relationship(back_populates='user')
    
    def set_password_hash(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password_hash(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_following(self, user):
        query = self.following.select().where(User.username == user.username)
        return db.session.scalar(query) is not None

    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def following_count(self):
        query = select(func.count()).select_from(self.following.select().subquery())
        return db.session.scalar(query)

    def followers_count(self):
        query = select(func.count()).select_from(self.followers.select().subquery())
        return db.session.scalar(query)

    def following_posts(self):
        Author = aliased(User)
        Follower = aliased(User)
        return (
            select(Post)
            .join(Post.author.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(or_(Follower.id == self.id, Author.id == self.id))
            .group_by(Post)
            .order_by(Post.timstamp.desc())
        )

    def generate_password_reset_token(self):
        token = jwt.encode({'reset_password': self.id, "exp": time() + app.config["PASSWORD_RESET_TOKEN_EXP"]}, app.config['SECRET_KEY'], algorithm='HS256')
        return token

    @staticmethod
    def validate_password_reset_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')['reset_password']
        except:
            return
        return db.session.get(User, id)
    
    def send_password_reset_email(self):
        token = self.generate_password_reset_token()
        email = EMAIL(
            subject='[Microblog] Password Reset Request',
            sender='no-reply@microblog.com',
            recipients=[self.email],
            body=render_template('email/reset_password.txt', user=self, token=token), 
            html=render_template('email/reset_password.html', user=self, token=token),
        )
        mail.send(email)

    def get_chat_list(self):
        list = db.session.scalars(select(Message).where(Message.recipient_id == self.id).group_by(Message.sender_id)).all()
        return list

    def get_conversation(self, user):
        query = select(Message).where(or_(
                and_((Message.sender_id == self.id), (Message.recipient_id == user.id)),
                and_((Message.sender_id == user.id), (Message.recipient_id == self.id))
            )
        ).order_by(Message.timestamp.asc())
        messages = db.session.scalars(query).all()
        return messages

    def get_unread_message_count(self):
        query = select(func.count()).select_from(self.messages_received.select().where(Message.is_read==False).subquery())
        return db.session.scalar(query)
    
    def add_notification(self, name, data):
        db.session.execute(self.notifications.delete().where(Notification.name == name))
        n = Notification(name=name, payload=data)
        self.notifications.add(n)
        

    def __repr__(self):
        return 'User {}'.format(self.username)
    

    
class Post(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(String(256))
    timstamp: Mapped[datetime] = mapped_column(index=True, default=lambda:datetime.now(timezone.utc))
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)

    author: Mapped['User'] = relationship(back_populates='posts')

    def __repr__(self):
        return 'Post {}'.format(self.body)


class Message(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
    recipient_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
    message: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    author: Mapped['User'] = relationship(foreign_keys='Message.sender_id', back_populates='messages_sent')
    recipient: Mapped['User'] = relationship(foreign_keys='Message.recipient_id', back_populates='messages_received')


class Notification(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id), index=True)
    timestamp: Mapped[float] = mapped_column(index=True, default=time)
    payload: Mapped[str] = mapped_column(Text)

    user: Mapped['User'] = relationship(back_populates='notifications')

    def get_data(self):
        return json.loads(self.payload)


@login.user_loader    
def load_user(id):
    return db.session.get(User, id)