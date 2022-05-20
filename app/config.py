# mongodb地址
# 开发模式
# MONGODBHOST = "127.0.0.1:27017"
MONGODBHOST = "192.168.68.130:27017" #数据库地址
DBUSERNAME = 'admin'
DBPASSWORD = '123456'
BASEURL = "/api"
DOMIN="http://127.0.0.1:3000"

# 生产模式
# MONGODBHOST = "127.0.0.1:27017"
# DBUSERNAME = 'admin'
# DBPASSWORD = '123456'
# BASEURL = "/api"
# DOMIN = "https://kedong.me"

JWTSECRET = "myblog" 
LOGINAME = "admin" #后台登陆账号 
PASSWORD = "admin" #后台登陆密码
AUTHORIZE_EXPIRES = 60*60*24*30 #后台账号过期时间
# 单页限制文章数
PAGE_NUM = 16
AUTHPWD = "admin" #文章密码
MoviePath= "/static/video" #电影列表地址

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
