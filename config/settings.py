from datetime import datetime
from pathlib import Path
import os
from datetime import timedelta
from dotenv import read_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
read_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.environ.get("SECRET_KEY")


DEBUG = os.environ.get("DEBUG")


ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


INSTALLED_APPS = [
    'debug_toolbar',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'storages',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',

    'users',
    'shop',
    'campaigns',
    'chat',
    'payments',
    'alarms',

    'dj_rest_auth',
    'dj_rest_auth.registration',
    # django-allauth

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.kakao',
    'allauth.socialaccount.providers.google',

    'django_apscheduler',
    'taggit',
]

# 웹사이트 복수 생성시 사이트 지정을 위해 필요
SITE_ID = 2

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    "PAGE_SIZE": 6,
}


REST_USE_JWT = True
JWT_AUTH_COOKIE = 'jwt_token'
JTW_AUTH_REFRESH_COOKIE = 'jwt_refresh_token'

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
INTERNAL_IPS = [
    '127.0.0.1',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

CHANNEL_HOSTS = os.getenv('CHANNEL_HOSTS')
CHANNEL_PORT = int(os.getenv('CHANNEL_PORT'))
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(CHANNEL_HOSTS, CHANNEL_PORT)],
        },
    },
}

now = datetime.now()
str_now = now.strftime('%y%m%d_%H')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {module} {message}',
            'datefmt': '%Y-%m-%d %H:%M',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'debug_log': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': f'logs/debug/deb__{str_now}.log',
            'formatter': 'verbose',
        },
        'error_log': {
            'level': 'ERROR',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': f'logs/error/err__{str_now}.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['debug_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_log'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}

DATABASES = {
    'dev': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'production': {
        'NAME': os.environ.get('MYSQL_NAME'),
        'ENGINE': 'django.db.backends.mysql',
        'USER': os.environ.get('MYSQL_USER'),
        'HOST': os.environ.get('MYSQL_HOST'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD'),
        'PORT': os.environ.get('MYSQL_PORT')
    },
}

DATABASES['default'] = DATABASES['dev' if DEBUG == 'True' else 'production']

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = "ko-kr"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',

    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    'COOKIE_SAMESITE': 'Lax',
    'COOKIE_SECURE': True,

    "TOKEN_OBTAIN_SERIALIZER": "users.serializers.CustomTokenObtainPairSerializer",
}

JWT_AUTH = {
    'JWT_ALLOW_REFRESH': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=60),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=14),
    'JWT_COOKIE_SECURE': True,
    'JWT_COOKIE_SAMESITE': 'Lax',
}

BASE_URL = os.environ.get("BASE_URL")
FRONT_BASE_URL = os.environ.get("FRONT_BASE_URL")

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    BASE_URL,
    FRONT_BASE_URL
]

CORS_ALLOW_CREDENTIALS = True  # cross-site HTTP요청에 Cookie 추가

CORS_ALLOW_HEADERS = [
    'authorization-token',
    'content-type',  # 'Content-Type' 헤더 추가
    'authorization',  # 'authorization' 헤더 추가
]

AUTH_USER_MODEL = 'users.User'

ACCOUNT_EMAIL_REQUIRED = True            # email 필드 사용 o
ACCOUNT_USERNAME_REQUIRED = False        # username 필드 사용 x
ACCOUNT_AUTHENTICATION_METHOD = 'email'

IMP_KEY = os.environ.get('IMP_KEY')
IMP_SECRET = os.environ.get('IMP_SECRET')

APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
SCHEDULER_DEFAULT = True

USE_S3 = os.environ.get('USE_S3')

if USE_S3 == "True":
    DEFAULT_FILE_STORAGE = 'config.asset_starage.MediaStorage'

    AWS_ACCESS_KEY_ID = os.environ.get('MY_AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('MY_AWS_SECRET_ACCESS_KEY')

    AWS_REGION = 'ap-northeast-2'
    AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_CUSTOM_DOMAIN = '%s.s3.%s.amazonaws.com' % (
        AWS_STORAGE_BUCKET_NAME, AWS_REGION)
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_DEFAULT_ACL = 'public-read'
    AWS_LOCATION = 'static'
    STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static')
    ]

else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

    STATIC_URL = '/static/'
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

CARD_NUMBER = os.environ.get('CARD_NUMBER')
EXPIRY_AT = os.environ.get('EXPIRY_AT')
BIRTH = os.environ.get('BIRTH')
PWD_2DIGIT = os.environ.get('PWD_2DIGIT')
CSRF_TRUSTED_ORIGINS = [
    FRONT_BASE_URL,
    BASE_URL,
]

TAGGIT_CASE_INSENSITIVE = True
TAGGIT_LIMIT = 50

CIPHER_V1_KEY = os.environ.get('CIPHER_V1_KEY')
