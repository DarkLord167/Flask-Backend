import os


basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'microblog'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = 1
    MAIL_USERNAME = 'onlyfortestingapps167@gmail.com'
    MAIL_PASSWORD = "yejxzuudbwvusjxy"
    ADMINS = ['admin@microblog.com']
    POST_PER_PAGE = 5
    PASSWORD_RESET_TOKEN_EXP = 600