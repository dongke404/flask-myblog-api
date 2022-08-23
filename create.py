# 脚本 第一次运行创建自增队列

from app.config import MONGODBHOST, DBUSERNAME, DBPASSWORD
from pymongo import MongoClient


myclient = MongoClient(
    MONGODBHOST,
    username=DBUSERNAME,
    password=DBPASSWORD,
    # authSource='myblog',
    authMechanism="SCRAM-SHA-1",
)
db = myclient["myblog"]

if __name__ == "__main__":
    colls=[{"collection": "blogs", "id": 0},{"collection": "todos", "id": 0}]
    db.seqs.insert_many(colls)

