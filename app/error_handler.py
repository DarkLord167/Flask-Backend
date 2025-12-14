from logging.handlers import SMTPHandler, RotatingFileHandler
from app import app


email_handler = SMTPHandler(
        mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
        fromaddr='no-reply@' + app.config['MAIL_SERVER'], 
        toaddrs=app.config['ADMINS'],
        subject='Microblog Failure',
        secure=app.config['MAIL_USE_TLS'],
        timeout=5
    )


file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=1024, backupCount=3)

