import os
from decouple import config, UndefinedValueError

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY') 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool) 

# Database Settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
        #'ENGINE': 'django.db.backends.mysql',
        #'NAME': config('DB_NAME'),
        #'USER': config('DB_USER'),
        #'PASSWORD': config('DB_PASSWORD'),
        #'HOST': config('DB_HOST'),
        #'PORT': config('DB_PORT')
    },
}

try:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                    "hosts": [("redis://:" + config('REDIS_SERVER_PASSWORD') + "@" + config('REDIS_SERVER_HOST') + ":" + config('REDIS_SERVER_PORT'))]
            },
        },
    }
except UndefinedValueError:
    # No password set
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(config('REDIS_SERVER_HOST'), config('REDIS_SERVER_PORT'))]            },
        },
    }
