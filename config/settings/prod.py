from .base import *  # noqa: F401,F403

from decouple import config as env

DEBUG = False
ALLOWED_HOSTS = [h.strip() for h in env('ALLOWED_HOSTS', default='').split(',') if h.strip()]
