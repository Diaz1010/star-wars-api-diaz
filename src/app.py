import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, planets, people, favorites
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] ='secret'
jwt = JWTManager(app)
app.url_map.strict_slashes = False
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/users', methods=['GET'])
def handle_hello():
    users = User.query.all()
    if users is None:
        raise APIException("User not found", status_code=404)
    return jsonify([User.serialize() for User in users]), 200

@app.route('/user/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if user is None:
        raise APIException("User not found", status_code=404)
    return jsonify(user.serialize()), 200

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get("username", None)
    password = request.json.get("password", None)
    if username is None or password is None:
        return jsonify({"msg": "Bad username or password"}), 400

    user = User(username=username, password=password,)
    db.session.add(user)
    db.session.commit()
    return jsonify(user.serialize()), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if username is None or password is None:
        return jsonify({"msg": "Bad username or password"}), 400
    
    user = User.query.filter_by(username=username, password=password).first()
    
    if user is None:
        return jsonify({"msg": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user.username)
    return jsonify({"token": access_token, "username": user.username}), 200

@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user_favorites = favorites.query.filter_by(user_id=user_id).all()
    if not user_favorites:
        raise APIException("Favorites not found for user", status_code=404)
    return jsonify([favorite.serialize() for favorite in user_favorites]), 200

@app.route('/users/favorites', methods=['GET'])
@jwt_required()
def get_current_user_favorites():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    user_favorites = favorites.query.filter_by(user_id=user.id).all()
    if not user_favorites:
        raise APIException("Favorites not found for user", status_code=404)
    return jsonify([favorite.serialize() for favorite in user_favorites]), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
@jwt_required()
def add_favorite_planet(planet_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    planet = planets.query.get(planet_id)
    if planet is None:
        raise APIException("Planet not found", status_code=404)
    favorite = favorites(user_id=user.id, planet_id=planet_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.serialize()), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
@jwt_required()
def add_favorite_people(people_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    people = people.query.get(people_id)
    if people is None:
        raise APIException("People not found", status_code=404)
    favorite = favorites(user_id=user.id, people_id=people_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.serialize()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_planet(planet_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    favorite = favorites.query.filter_by(user_id=user.id, planet_id=planet_id).first()
    if favorite is None:
        raise APIException("Favorite not found", status_code=404)
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite deleted"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_people(people_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    favorite = favorites.query.filter_by(user_id=user.id, people_id=people_id).first()
    if favorite is None:
        raise APIException("Favorite not found", status_code=404)
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite deleted"}), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
