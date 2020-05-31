# coding=UTF-8

from flask import Flask
from app.config import MONGODBHOST


from pymongo import MongoClient
app = Flask(__name__)
# 配置启动模式为调试模式
app.config["DEBUG"] = False
# session配置key
app.config["SECRET_KEY"] = "mysite2"


myclient = MongoClient(MONGODBHOST,
                       #  username='admin',
                       #  password='admin',
                       #  authSource='myblog',
                       #  authMechanism='SCRAM-SHA-256'
                       )
db = myclient["myblog"]
