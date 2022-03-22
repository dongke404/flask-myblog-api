# 主业务逻辑中的视图和路由的定义
from . import app
from . import db
from flask_cors import CORS
from flask import request, jsonify
import math
import jwt
import time
import datetime
import re
import os
from .config import JWTSECRET, LOGINAME, PASSWORD, AUTHORIZE_EXPIRES, OriginMap, CategoryMap, PAGE_NUM, BASEURL, DOMIN, AUTHPWD, PrivacyMap, MoviePath
from .utils import get_list, mkdir
CORS(app, supports_credentials=True)


# 拦截器(所有post请求需要提供cookie)
@app.before_request
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
@app.route(BASEURL + '/login', methods=["POST"])
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
@app.route(BASEURL + '/publish', methods=["POST"])
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
@app.route(BASEURL + '/uploadImg', methods=["POST"])
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
@app.route(BASEURL + '/addtalk', methods=["POST"])
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
@app.route(BASEURL + '/fontcss', methods=["GET", "POST"])
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
@app.route(BASEURL + '/tag', methods=["GET", "POST"])
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
@app.route(BASEURL + '/album', methods=["GET", "POST"])
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
@app.route(BASEURL + '/photo', methods=["GET", "POST"])
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
@app.route(BASEURL + '/file', methods=["GET", "POST"])
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
@app.route(BASEURL + '/friendlink', methods=["POST"])
def addfriendlink():
    set1 = db.siteOption
    params = request.get_json()
    set1.update({}, {"$push": {"friendlinks": params}})
    return jsonify({'status': 0})

#-------------------------非后台请求---------------------------#
# 获取文章列表
@app.route(BASEURL + '/article')
def reqArticle():
    params = request.args
    # print(params)
    category = params.get('category_slug')
    keyword = params.get('keyword')
    sort = params.get('sort')
    current_page = int(params.get("page", 1))
    date = params.get("date")
    tag = params.get('tag_name')
    set1 = db.blogs
    set2 = db.comments
    if category:
        iteration = set1.find({"category": category}, {"_id": 0}).sort(
            "article_id", -1).skip(
            (current_page-1)*PAGE_NUM).limit(PAGE_NUM)

    elif keyword:
        # set1.create_index([("title", 1)])
        iteration = set1.find({"$or": [
            {"title": {"$regex": keyword, "$options": 'i'}},
            {"category": {"$regex": keyword, "$options": 'i'}},
            {"description": {"$regex": keyword, "$options": 'i'}},
            {"content": {"$regex": keyword, "$options": 'i'}},
            {"origin": {"$regex": keyword, "$options": 'i'}},
            {"tags": {"$regex": keyword, "$options": 'i'}},
        ]}, {"_id": 0}).sort(
            "article_id", -1).skip(
            (current_page-1)*PAGE_NUM).limit(PAGE_NUM)
    elif sort:
        iteration = set1.find({}, {"_id": 0}).sort(
            "view_num", -1).limit(10)
    elif date:
        date = date.replace("-", "/")
        iteration = set1.find({"date": {"$regex": date}}, {"_id": 0})
    elif tag:
        iteration = set1.find({"tags": {"$in": [tag]}}, {"_id": 0})
    else:
        iteration = set1.find({}, {"_id": 0, }).sort(
            "article_id", -1).skip(
            (current_page-1)*PAGE_NUM).limit(PAGE_NUM)
    data = []
    for x in iteration:
        cmt_num = set2.find({"post_id": x["article_id"]}).count()
        x["cmt_num"] = cmt_num
        data.append(x)
    # print(data)
    pagination = {}
    pagination["current_page"] = current_page
    pagination["total_page"] = math.ceil(iteration.count()/PAGE_NUM)
    return jsonify({'pagination': pagination, 'data': data})


# 获取时间轴列表
@app.route(BASEURL + '/timeline')
def reqTimeline():
    set1 = db.blogs
    set2 = db.announcements
    blog_cursor = set1.find(
        {}, {"_id": 0, "article_id": 1, "title": 1, "description": 1, "date": 1})
    says_cursor = set2.find({}, {"_id": 0, "date": 1, 'say': 1})
    data = []
    for i in blog_cursor:
        data.append(i)
    for j in says_cursor:
        data.append(j)
    data = sorted(data, key=lambda x: get_list(x["date"]), reverse=True)
    # 按年份组合数据
    res = {}
    curyear = data[0]["date"][0:4]
    res[curyear] = []
    for item in data:
        if item["date"][0:4] == curyear:
            res[curyear].append(item)
        else:
            curyear = item["date"][0:4]
            res[curyear] = []
            res[curyear].append(item)
    resdata = []
    for k, v in res.items():
        dic = {}
        dic["year"] = k
        dic["data"] = v
        resdata.append(dic)
    return jsonify({'data': resdata})

# 获取文章详情
@app.route(BASEURL + '/article/<int:article_id>')
def reqArticleDetail(article_id):
    # print(article_id)
    set1 = db.blogs
    set1.update({"article_id": article_id}, {'$inc': {'view_num': 1}})
    data = set1.find_one({"article_id": article_id}, {"_id": 0})
    if not data:
        return jsonify({"status": 404, "msg": "页面不存在", "data": {}})
    related = set1.aggregate([{"$sample": {"size": 10}}, {"$project": {
                             "_id": 0, "article_id": 1, "imgUrl": 1, "title": 1}}],)
    _ = []
    for i in related:
        _.append(i)
    data["related"] = _
    if data.get('privacy')==0:
        authPwd=request.cookies.get("authPwd")
        if authPwd == AUTHPWD:   
            return jsonify({"status": 0, "data": data})           
        else:
            # data={}
            # data["related"] = _
            return jsonify({"status": 403, "msg": "权限不足", "data": data})
    return jsonify({"status": 0, "data": data})


# 获取随便说说内容
@app.route(BASEURL + '/announcement')
def announcement():
    set1 = db.announcements
    data = []
    for x in set1.find({}, {
        "_id": 0,
        "say": 1,
        "date": 1,
    }).sort("_id", -1):
        data.append(x)
    data = data[0:10]
    return jsonify({'status': 0, 'data': data})


# 评论操作GET读取,Post发布
@app.route(BASEURL + '/comment', methods=["GET", "POST"])
def comments():
    set1 = db.comments
    set2 = db.blogs
    # 读取评论列表
    if request.method == "GET":
        params = request.args
        page = int(params["page"])
        page_num = int(params["page_num"])
        sort = int(params["sort"])
        post_id = int(params["post_id"])
        data = []
        if sort == 2:
            comments = set1.find({'post_id': post_id}, {"_id": 0}).sort(
                "likes", -1).skip((page-1)*page_num).limit(page_num)
        else:
            comments = set1.find({'post_id': post_id}, {"_id": 0}).sort(
                "comment_id", sort).skip((page-1)*page_num).limit(page_num)
        for comment in comments:
            # pid 不等于0的话,找到回复的评论
            if comment["pid"]:
                targetCmt = set1.find_one(
                    {'comment_id': comment["pid"]}, {"_id": 0})
                comment["taruser"] = targetCmt["author"]["name"]
                data.append(comment)
            else:
                data.append(comment)
        pagination = {}
        pagination["total"] = comments.count()
        pagination["current_page"] = page
        # print(pagination)
        return jsonify({'pagination': pagination, 'data': data})
    else:
        params = request.get_json()
        # ip = request.headers.get('X-Forwarded-For')
        preComment_id = set1.find({}, {'comment_id': 1}).sort(
            "comment_id", -1).limit(1)
        Comment_id = 0
        for x in preComment_id:
            if x:
                Comment_id = x["comment_id"]
        params["comment_id"] = Comment_id+1
        params["create_time"] = datetime.datetime.now().strftime(
            "%Y/%m/%d %H:%M:%S")
        params["likes"] = 0
        # print(params)
        set1.insert(params)
        if params["pid"]:
            targetCmt = set1.find_one(
                {'comment_id': params["pid"]}, {"_id": 0})
            params["taruser"] = targetCmt["author"]["name"]
        params["_id"] = Comment_id+1
        set2.update({'article_id': params["post_id"]}, {
                    '$inc': {'cmt_num': 1}})
        return jsonify({'status': 0, 'data': params})


# 获取主站信息
@app.route(BASEURL + '/siteOption')
def siteOption():
    set1 = db.siteOption
    data = set1.find_one({}, {"_id": 0})
    if not data:
        create_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        set1.insert({"name": "dongke", "likes": 0, "blacklist": {
                    "mails": [], "keywords": []}, "create_time": create_time})
    return jsonify({'status': 0, 'data': data})

# 点赞文章
@app.route(BASEURL + '/like/article', methods=["POST"])
def likearticle():
    params = request.get_json()
    article_id = params.get("article_id")
    set1 = db.blogs
    set1.update({"article_id": article_id}, {'$inc': {'likes': 1}})
    return jsonify({'status': 0})


# 点赞留言板
@app.route(BASEURL + '/like/site', methods=["POST"])
def likeSite():
    set1 = db.siteOption
    set1.update({}, {'$inc': {'likes': 1}})
    return jsonify({'status': 0})


# 点赞评论
@app.route(BASEURL + '/like/comment', methods=["POST"])
def likeComment():
    set1 = db.comments
    params = request.get_json()
    comment_id = params.get('comment_id')
    # print(comment_id)
    if comment_id:
        comment = set1.find_one({'comment_id': comment_id}, {"_id": 0})
        comment["likes"] += 1
        set1.update({'comment_id': comment_id}, comment)
    return jsonify({'status': 0})


# 获取电影列表
@app.route(BASEURL + '/movielist')
def reqMovielist():
    filelist = os.listdir(MoviePath)
    print(MoviePath,filelist)
    return jsonify({'data': filelist})