# coding=UTF-8

from flask import Flask
from app.config import MONGODBHOST,DBUSERNAME,DBPASSWORD
from pymongo import MongoClient

app = Flask(__name__)
# 配置启动模式为调试模式
app.config["DEBUG"] = True
# session配置key
app.config["SECRET_KEY"] = "kedong.me"

myclient = MongoClient(MONGODBHOST,
                       username=DBUSERNAME,
                       password=DBPASSWORD,
                       # authSource='myblog',
                       authMechanism='SCRAM-SHA-1'
                       )
db = myclient["myblog"]
