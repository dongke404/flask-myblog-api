# coding=UTF-8

from flask import Flask
from app.config import MONGODBHOST
from flask_pymongo import PyMongo


app = Flask(__name__)
# 配置启动模式为调试模式
app.config["DEBUG"] = False
# session配置key
app.config["SECRET_KEY"] = "mysite2"
mongo = PyMongo(app, uri=MONGODBHOST)
