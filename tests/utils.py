from flask_mongodb import MongoDB

MAIN = 'main'
DB_NAME = 'flask_mongodb'


def remove_collections(mongo: MongoDB, using=MAIN):
    collections = list(mongo.collections[using].keys())
    for col in collections:
        mongo.connections[using].drop_collection(col)
