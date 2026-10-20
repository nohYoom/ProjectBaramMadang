import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-baram-madang')
    DATABASE = 'school_media.db'
    MEDIA_TYPES = ['articles', 'photos', 'videos']
    CATEGORIES = ['science', 'campus', 'robotics', 'events', 'general']
