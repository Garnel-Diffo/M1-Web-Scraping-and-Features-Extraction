from pymongo import MongoClient
db = MongoClient('mongodb://localhost:27017/')['SmartSearch']
url='https://nowtechcenter.com/produit/talkie-walkie-a522-portable-paire-de-2-avec-chargeur-bon-prix-en-vente-au-cameroun/'
print('exact', db['produits'].find_one({'url':url}) is not None)
url2=url.rstrip('/')
print('no slash', db['produits'].find_one({'url':url2}) is not None)
import re
print('regex', db['produits'].find_one({'url': {'$regex': 'talkie-walkie-a522'}}) is not None)
p=db['produits'].find_one()
print('sample', p.get('url')[:120])
