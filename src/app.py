import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, planets, people, favorites

app = Flask(__name__)
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

@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user_favorites = favorites.query.filter_by(user_id=user_id).all()
    if not user_favorites:
        raise APIException("Favorites not found for user", status_code=404)
    return jsonify([favorite.serialize() for favorite in user_favorites]), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = request.json.get('user_id')
    new_favorite = favorites(user_id=user_id, planet_id=planet_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify(new_favorite.serialize()), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.json.get('user_id')
    favorite_to_delete = favorites.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if favorite_to_delete is None:
        raise APIException("Favorite not found", status_code=404)
    db.session.delete(favorite_to_delete)
    db.session.commit()
    return '', 204
    
@app.route('/planets', methods=['GET'])
def get_all_planets():
    all_planets = planets.query.all()
    return jsonify([planet.serialize() for planet in all_planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = planets.query.get(planet_id)
    if planet is None:
        raise APIException("Planet not found", status_code=404)
    return jsonify(planet.serialize()), 200

@app.route('/people', methods=['GET'])
def get_all_people():
    all_people = people.query.all()
    return jsonify([person.serialize() for person in all_people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = people.query.get(people_id)
    if person is None:
        raise APIException("Person not found", status_code=404)
    return jsonify(person.serialize()), 200

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user_id = request.json.get('user_id')
    new_favorite = favorites(user_id=user_id, people_id=people_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify(new_favorite.serialize()), 201

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_person(people_id):
    user_id = request.json.get('user_id')
    favorite_to_delete = favorites.query.filter_by(user_id=user_id, people_id=people_id).first()
    if favorite_to_delete is None:
        raise APIException("Favorite not found", status_code=404)
    db.session.delete(favorite_to_delete)
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
