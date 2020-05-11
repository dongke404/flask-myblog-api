# mongodb地址
# 开发模式
MONGODBHOST = "mongodb://127.0.0.1:27017/myblog"
baseurl = ""
DOMIN="http://127.0.0.1:3000"

# 生产模式
# MONGODBHOST = "mongodb://172.17.0.2:27017/myblog"
# baseurl = "/api"
# DOMIN = "https://kedong.me"

JWTSECRET = "myblog"
LOGINAME = "admin"
PASSWORD = "admin"
AUTHORIZE_EXPIRES = 60*60*24*30
# 单页限制文章数
PAGE_NUM = 16

OriginMap = {
    "原创": 0,
    "转载": 1,
    "参考": 2
}

CategoryMap = {
    "学习": "code",
    "思考": "think",
    "日常": "life"
}
