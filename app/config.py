from app.database.db import DB_CONFIG

class Config:
    SECRET_KEY = 'default'
    
    POSTGRES_USER = DB_CONFIG['user']
    POSTGRES_PASSWORD = DB_CONFIG['password']
    POSTGRES_HOST = DB_CONFIG['host']
    POSTGRES_PORT = DB_CONFIG['port']
    POSTGRES_DB = DB_CONFIG['database']
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
configurations = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}