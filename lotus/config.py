DEBUG = False
#SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345678@localhost/Lotus'
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Lotus210676!@82.165.244.152/lotus'
SECRET_KEY = 'ThisKeyIsRealFuckingSeecret'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
WTF_CSRF_TIME_LIMIT = None

MAIL_SERVER = 'smtp.ionos.de'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'system@lotusicafe.de'
MAIL_PASSWORD = 'Lotus210676!'
DEFAULT_MAIL_SENDER = 'system@lotusicafe.de'
