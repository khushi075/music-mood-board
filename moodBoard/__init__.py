from flask import Flask

from moodBoard.auth import auth_blueprint 

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'justabtanyrandomkey'

    app.register_blueprint(auth_blueprint)

    return app
