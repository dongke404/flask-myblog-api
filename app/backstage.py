# 后台接口
# 主业务逻辑中的视图和路由的定义
from . import app,db
from flask_cors import CORS
from flask import request, jsonify ,Blueprint
import math
import jwt
import time
import datetime
import re
from .config import JWTSECRET, LOGINAME, PASSWORD, AUTHORIZE_EXPIRES, OriginMap, CategoryMap, BASEURL, DOMIN, PrivacyMap
from .utils import mkdir
CORS(app, supports_credentials=True)

#蓝图注册模块
backstage=Blueprint('backstage',__name__)

# 拦截器(所有post请求需要提供cookie)
@backstage.before_request
def before_action():
    if request.path in [BASEURL + "/login", BASEURL + "/comment", BASEURL + "/like/comment", BASEURL+'/like/site', BASEURL + '/like/article']:
        return
    if request.method == "GET":
        return
    # print("拦截器",request.cookies)
    token = request.cookies.get("token")
    # print(request.cookies,111,token)
    try:
        usertokenInfo = jwt.decode(token, JWTSECRET, algorithms=['HS256'])
        print(usertokenInfo)
        ctime = usertokenInfo.get("ctime")
        expires = usertokenInfo.get("expires")
        # print("离身份过期的秒数:",int(expires)-int(time.time()-ctime))
        if int(time.time() - ctime) > int(expires):
            # print("身份信息过期")
            return jsonify(
                {
                    'status': 1,
                    'msg': "身份信息已过期"
                }
            )
    except Exception:
        return jsonify(
            {
                'status': 1,
                'msg': "请重新登陆"
            }
        )


# 登录验证
@backstage.route(BASEURL + '/login', methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({
            "status": 1,
            "msg": "请求失败"
        })
    loginname = data.get("loginname")
    password = data.get("password")
    if loginname == LOGINAME and password == PASSWORD:
        token = jwt.encode({'loginname': loginname, "ctime": int(time.time()), 'expires': AUTHORIZE_EXPIRES}, JWTSECRET,
                           algorithm='HS256')
        # print(token)
        return jsonify({
            "status": 0,
            "msg": "登陆成功",
            "token": token.decode()
        })
    else:
        return jsonify({
            "status": 1,
            "msg": "用户名密码错误"
        })

# 发表文章
@backstage.route(BASEURL + '/publish', methods=["POST"])
def publish():
    params = request.get_json()
    set1 = db.blogs

    preArticle_id = set1.find({}, {'article_id': 1}).sort(
        "article_id", -1).limit(1)

    Article_id = 0
    for x in preArticle_id:
        if x:
            Article_id = x["article_id"]
    imgUrl = re.search(
        r".*?\[.*?\]\(http[s]?://.*?(/.+?)\).*", params['markvalue'], flags=re.S)
    if imgUrl:
        imgUrl = imgUrl.group(1)

    data = {
        "article_id": Article_id+1,
        "category": CategoryMap[params['category']],
        "origin": OriginMap[params['origin']],
        "tags": params['tags'],
        "imgUrl": imgUrl,
        "title": params['title'],
        "description":  params['description'],
        "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
        "view_num": 0,
        "likes": 0,
        "cmt_num": 0,
        "content": params['markvalue'],
        "privacy": PrivacyMap[params['privacy']]
    }
    set1.insert(data)
    return jsonify({'status': 0})

# 上传图片
@backstage.route(BASEURL + '/uploadImg', methods=["POST"])
def uploadImg():
    img = request.files['file']
    path = '/static/images/article/'
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + \
        (img.filename[-8:])  # 图片防止重复
    file_path = path + filename
    img.save(file_path)
    # 返回预览图
    return jsonify({
        'status': 0,
        'data': [DOMIN+'/static/images/article/' + filename]
    })

# 添加随便说说
@backstage.route(BASEURL + '/addtalk', methods=["POST"])
def addtalk():
    params = request.get_json()
    date = datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
    set1 = db.announcements
    data = {
        "say": params.get("content"),
        "date": date[0],
    }
    set1.insert(data)
    return jsonify({'status': 0})

# 修改新的css
@backstage.route(BASEURL + '/fontcss', methods=["GET", "POST"])
def fontcss():
    set1 = db.fontcss
    if request.method == "GET":
        data = set1.find_one({}, {"_id": 0})
        return jsonify({'status': 0, 'data': data})
    else:
        params = request.get_json()
        fontcss = params.get('fontcss')
        ishave = set1.find_one()
        if ishave:
            set1.update({}, {"fontcss": fontcss})
        else:
            set1.insert({}, {"fontcss": fontcss})
        return jsonify({'status': 0})

# 标签操作
@backstage.route(BASEURL + '/tag', methods=["GET", "POST"])
def tags():
    set1 = db.tags
    set2 = db.blogs
    if request.method == "GET":
        cursor = set1.find({}, {"_id": 0})
        data = []
        for i in cursor:
            count = set2.find({"tags": {"$in": [i["name"]]}}, {
                              "_id": 0}).count()
            i["count"] = count
            data.append(i)
        return jsonify({'status': 0, 'data': data})
    else:
        params = request.get_json()
        # print(params)
        name = params.get('name')
        icon = params.get('icon')
        description = params.get('description')
        img = params.get('img')
        data = {}

        if name and icon and img and description:
            data['name'] = name
            data['icon'] = icon
            data['description'] = description
            data['img'] = img
            set1.insert(data)
            return jsonify({'status': 0})


# 图集操作
@backstage.route(BASEURL + '/album', methods=["GET", "POST"])
def album():
    set1 = db.album
    if request.method == "GET":
        cursor = set1.find({}, {"_id": 0})
        data = []
        for i in cursor:
            data.append(i)
        return jsonify({'status': 0, 'data': data})
    else:
        params = request.get_json()
        # print(params)
        name = params.get('name')
        description = params.get('description')
        img = params.get('img')
        data = {}
        if name and img and description:
            data['name'] = name
            data['description'] = description
            data['img'] = img
            if mkdir("/static/images/photo/"+name):
                set1.insert(data)
                return jsonify({'status': 0})
            else:
                return jsonify({'status': 1, "msg": "目录已存在"})
        else:
            return jsonify({'status': 1, "msg": "有空内容"})


# 图片操作
@backstage.route(BASEURL + '/photo', methods=["GET", "POST"])
def photo():
    set1 = db.photos
    if request.method == "GET":
        params = request.args
        album = params.get('album')
        page = int(params.get('page'))
        # print(params)
        # print(album, page)
        if album:
            cursor = set1.find({'album': album}, {"_id": 0}).skip(
                (page-1)*30).limit(30)
        else:
            cursor = set1.find({}, {"_id": 0}).sort("_id", -1).skip(
                (page-1)*30).limit(30)
        photos = []
        for x in cursor:
            photos.append(x)
        # pagination["current_page"] = current_page
        total_page = math.ceil(1 if cursor.count() == 0 else cursor.count()/30)
        # print(22222,total_page)
        return jsonify({"data": photos, 'total_page': total_page})
    else:
        params = request.get_json()
        # print(params)
        album = params.get('album')
        img = params.get('img')

        if album and img:
            data = {}
            data["album"] = album
            data["img"] = img
            data["date"] = datetime.datetime.now().strftime(
                "%Y/%m/%d %H:%M")
            set1.insert(data)
            return jsonify({'status': 0})

# 添加资源链接
@backstage.route(BASEURL + '/file', methods=["GET", "POST"])
def file():
    set1 = db.files
    if request.method == "GET":
        params = request.args
        # print(params)
        category = params.get('category')
        page = int(params.get('page'))
        keyword = params.get('keyword')
        if category:
            cursor = set1.find({'category': category}, {"_id": 0}).sort("_id", -1).skip(
                (page-1)*20).limit(20)
        elif keyword:
            cursor = set1.find({"name": {"$regex": keyword, "$options": 'i'}}, {"_id": 0}).sort("_id", -1).skip(
                (page-1)*20).limit(20)
        else:
            cursor = set1.find({}, {"_id": 0}).sort("_id", -1).skip(
                (page-1)*20).limit(20)
        data = []
        total = cursor.count()
        # print(total)
        for x in cursor:
            data.append(x)
        return jsonify({'data': data, "total": total})
    else:
        params = request.get_json()
        params['date'] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        set1.insert(params)
        return jsonify({'status': 0})

# 添加友情链接
@backstage.route(BASEURL + '/friendlink', methods=["POST"])
def addfriendlink():
    set1 = db.siteOption
    params = request.get_json()
    set1.update({}, {"$push": {"friendlinks": params}})
    return jsonify({'status': 0})
