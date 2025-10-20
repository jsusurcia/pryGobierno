from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()

def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)
    
    db.init_app(app)
    
    # Blueprints
    from app.routes.routes_productos import producto_bp
    app.register_blueprint(producto_bp)
    
    return app