# mongodb地址
# 开发模式
MONGODBHOST = "127.0.0.1:27017"
baseurl = ""
DOMIN="http://127.0.0.1:3000"

# 生产模式
# MONGODBHOST = "127.0.0.1:27017"
# baseurl = "/api"
# DOMIN = "https://kedong.me"

JWTSECRET = "myblog"
LOGINAME = "admin" #后台登陆账号 
PASSWORD = "admin" #后台登陆密码
AUTHORIZE_EXPIRES = 60*60*24*30
# 单页限制文章数
PAGE_NUM = 16
AUTHPWD = "admin" #文章密码

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

PrivacyMap = {
    "公开": 1,
    "私人": 0,
}
