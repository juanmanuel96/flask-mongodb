from flask_mongodb import MongoDB

MAIN = 'main'
DB_NAME = 'flask_mongodb'

def remove_collections(mongo: MongoDB):
    collections = list(mongo.collections[MAIN].keys())
    for col in collections:
        mongo.connections[MAIN].drop_collection(col)