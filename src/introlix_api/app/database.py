from pymongo import MongoClient
import datetime

client = MongoClient('mongodb+srv://introlix:satyam123TcoderTech@introlixfeed.wrarjib.mongodb.net/')

db = client.IntrolixDb

feed_data = db.feedData

# doc = {
#     "title": "NextJs and Python",
#     "desc": "Best Programming And Framework Combination",
#     "publication_date": datetime.datetime.utcnow()
# }

# post_id = feed_data.insert_one(doc).inserted_id

# print(post_id)