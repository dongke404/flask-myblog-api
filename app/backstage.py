# 后台接口
# 主业务逻辑中的视图和路由的定义
from curses.has_key import has_key
from unicodedata import name
from . import app, db
from flask_cors import CORS
from flask import request, jsonify, Blueprint
import math
import jwt
import time
import datetime
import re
from .config import (
    JWTSECRET,
    LOGINAME,
    PASSWORD,
    AUTHORIZE_EXPIRES,
    DOMIN,
    IMGPATH,
    APPIMGPATH,
)
from .map import OriginMap, CategoryMap, PrivacyMap
from .utils import insert_doc
import requests

CORS(app, supports_credentials=True)
BASEURL = "/api/admin"

# 蓝图注册模块
backstage = Blueprint("backstage", __name__)

# 拦截器后台所有请求都需要cookie
@backstage.before_request
def before_action():
    if request.path in [
        BASEURL + "/login",
    ]:
        return
    # print("拦截器",request.cookies)
    token = request.cookies.get("token")
    # print(request.cookies,111,token)
    try:
        usertokenInfo = jwt.decode(token, JWTSECRET, algorithms=["HS256"])
        ctime = usertokenInfo.get("ctime")
        expires = usertokenInfo.get("expires")
        # print("离身份过期的秒数:",int(expires)-int(time.time()-ctime))
        if int(time.time() - ctime) > int(expires):
            # print("身份信息过期")
            return jsonify({"code": 2, "msg": "身份信息已过期"})
    except Exception:
        return jsonify({"code": 2, "msg": "请重新登陆"})


# ip归属地查询
@backstage.route(BASEURL + "/user_ip", methods=["GET"])
def user_ip():
    ip = request.headers.get("X-Real-IP")
    url = "http://ip-api.com/json/{0}?lang=zh-CN".format(ip)
    r = requests.post(url)
    return r.json()


# 登录验证
@backstage.route(BASEURL + "/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"code": 1, "msg": "请求失败"})
    loginname = data.get("loginname")
    password = data.get("password")
    if loginname == LOGINAME and password == PASSWORD:
        token = jwt.encode(
            {
                "loginname": loginname,
                "ctime": int(time.time()),
                "expires": AUTHORIZE_EXPIRES,
            },
            JWTSECRET,
            algorithm="HS256",
        )
        # print(token)
        return jsonify({"code": 0, "msg": "success", "data": token.decode()})
    else:
        return jsonify({"code": 1, "msg": "用户名密码错误"})


# 获取文章列表
@backstage.route(BASEURL + "/articleList")
def reqArticle():
    # 参数提取
    params = request.args
    page_num = int(params.get("page_num"))
    current_page = int(params.get("page", 1))
    keyword = params.get("keyword")
    category = params.get("category_slug")
    tag = params.get("tag_name")
    if not page_num:
        page_num = 20
    # 语句处理
    sql = {
        "$or": [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}},
            {"content": {"$regex": keyword, "$options": "i"}},
        ]
    }
    if category:
        sql["category"] = category
    if tag:
        sql["tags"] = {"$in": [tag]}
    set1 = db.blogs
    set2 = db.comments
    iteration = (
        set1.find(sql, {"_id": 0})
        .sort("article_id", -1)
        .skip((current_page - 1) * page_num)
        .limit(page_num)
    )
    data = {}
    articlelist = []
    for x in iteration:
        cmt_num = set2.find({"post_id": x["article_id"]}).count()
        x["cmt_num"] = cmt_num
        articlelist.append(x)
    # print(data)
    data["list"] = articlelist
    data["current_page"] = current_page
    data["total_page"] = math.ceil(iteration.count() / page_num)
    data["total"] = iteration.count()
    return jsonify({"msg": "success", "code": 0, "data": data})


# 发表或编辑文章
@backstage.route(BASEURL + "/publish", methods=["POST", "PUT"])
def publish():
    params = request.get_json()
    set1 = db.blogs

    # 取文章第一张图片
    imgUrl = re.search(
        r".*?\[.*?\]\(http[s]?://.*?(/.+?)\).*", params["markvalue"], flags=re.S
    )
    if imgUrl:
        imgUrl = imgUrl.group(1)

    if request.method == "POST":
        data = {
            "category": CategoryMap[params["category"]],
            "origin": OriginMap[params["origin"]],
            "tags": params["tags"],
            "imgUrl": imgUrl,
            "title": params["title"],
            "description": params["description"],
            "date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),
            "view_num": 0,
            "likes": 0,
            "cmt_num": 0,
            "content": params["markvalue"],
            "privacy": PrivacyMap[params["privacy"]],
        }
        insert_doc(data, "blogs", db, "article_id")
        set1.insert(data)
    else:
        data = {
            "category": CategoryMap[params["category"]],
            "origin": OriginMap[params["origin"]],
            "tags": params["tags"],
            "imgUrl": imgUrl,
            "title": params["title"],
            "description": params["description"],
            "content": params["markvalue"],
            "privacy": PrivacyMap[params["privacy"]],
        }
        data["article_id"] = params["article_id"]
        set1.update({"article_id": params["article_id"]}, {"$set": data})
    return jsonify({"code": 0, "msg": "success"})


# 文章中上传图片
@backstage.route(BASEURL + "/uploadImg", methods=["POST"])
def uploadImg():
    imgs = request.files.getlist("file[]")
    succMap = {}
    for img in imgs:
        filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + (
            img.filename[-8:]
        )  # 图片防止重复
        file_path = IMGPATH + filename
        succMap[img.filename] = DOMIN + file_path
        img.save(file_path)
        print(succMap)
    return jsonify({"msg": "", "code": 0, "data": {"errFiles": [], "succMap": succMap}})


# 获取文章详情
@backstage.route(BASEURL + "/article/<int:article_id>")
def reqArticleDetail(article_id):
    # print(article_id)
    set1 = db.blogs
    data = set1.find_one({"article_id": article_id}, {"_id": 0})
    if not data:
        return jsonify({"code": 1, "msg": "文章不存在", "data": {}})
    related = set1.aggregate(
        [
            {"$sample": {"size": 10}},
            {"$project": {"_id": 0, "article_id": 1, "imgUrl": 1, "title": 1}},
        ],
    )
    _ = []
    for i in related:
        _.append(i)
    data["related"] = _
    return jsonify({"code": 0, "data": data, "msg": "success"})


# 删除文章
@backstage.route(BASEURL + "/article_del", methods=["DELETE"])
def article_del():
    article_id = int(request.args.get("article_id"))
    set1 = db.blogs
    set1.remove({"article_id": article_id})
    return jsonify({"code": 0, "msg": "success"})


# 获取全部标签
@backstage.route(BASEURL + "/alltags", methods=["GET"])
def reqTags():
    set1 = db.tags
    set2 = db.blogs
    if request.method == "GET":
        cursor = set1.find({}, {"_id": 0})
        data = []
        for i in cursor:
            count = set2.find({"tags": {"$in": [i["name"]]}}, {"_id": 0}).count()
            i["count"] = count
            if not "sort" in i.keys():
                i["sort"] = 0
            data.append(i)
        data = sorted(data, key=lambda x: x["sort"], reverse=False)
        return jsonify({"msg": "success", "code": 0, "data": data})


# 修改标签排序
@backstage.route(BASEURL + "/tagSort", methods=["PUT"])
def tagsort():
    params = request.get_json()
    set1 = db.tags
    for i, v in enumerate(params):
        set1.update({"name": v}, {"$set": {"sort": i}})
    return jsonify({"code": 0, "msg": "success"})


# 新增标签
@backstage.route(BASEURL + "/addTag", methods=["POST"])
def addTag():
    params = request.get_json()
    set1 = db.tags
    sort = set1.find({}, {"_id": 0}).count()
    params["sort"] = sort
    set1.insert(params)
    return jsonify({"code": 0, "msg": "success"})


# 修改标签
@backstage.route(BASEURL + "/editTag", methods=["PUT"])
def editTag():
    params = request.get_json()
    set1 = db.tags
    name = params["target_name"]
    data = {}
    data["name"] = params["name"]
    data["icon"] = params["icon"]
    data["img"] = params["img"]
    data["description"] = params["description"]
    set1.update({"name": name}, {"$set": data})
    return jsonify({"code": 0, "msg": "success"})


# 删除标签
@backstage.route(BASEURL + "/delTag", methods=["DELETE"])
def delTag():
    params = request.args
    set1 = db.tags
    set2 = db.blogs
    set1.remove({"name": params["name"]})
    set2.update_many(
        {"tags": {"$in": [params["name"]]}}, {"$pull": {"tags": params["name"]}}
    )
    return jsonify({"code": 0, "msg": "success"})


# -----------------------------------------------todos开始-----------------------------------------------------------------------#

# 添加或更新todo
@backstage.route(BASEURL + "/addTodo", methods=["POST", "PUT"])
def addTodo():
    params = request.get_json()
    set1 = db.todos
    create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = {
        "content": params["content"],
        "remark": params["remark"],
        "stopDate": params["stopDate"],
        "todo_cate": params["todo_cate"],
        "finish_status": 0,  # 0: 未完成, 1: 已完成
        "is_del": 0,  # 0: 未删除, 1: 已删除
        "finish_time": "",
        "stop_timestamp": int(
            time.mktime(time.strptime(params["stopDate"], "%Y-%m-%d %H:%M:%S"))
        ),
        "finish_timestamp": 0,
    }
    # 新增
    if request.method == "POST":
        data["create_timestamp"] = int(time.time())
        data["create_time"] = create_time
        insert_doc(data, "todos", db, "todo_id")
        set1.insert(data)
    # 更新
    else:
        data["todo_id"] = params["todo_id"]
        set1.update({"todo_id": params["todo_id"]}, {"$set": data})
    return jsonify({"code": 0, "msg": "success"})


# 获取todo详情
@backstage.route(BASEURL + "/todoDetail", methods=["GET"])
def reqTodoDetail():
    set1 = db.todos
    todo_id = int(request.args.get("todo_id"))
    data = set1.find_one({"todo_id": todo_id}, {"_id": 0})
    if not data:
        return jsonify({"code": 1, "msg": "todo不存在", "data": {}})
    return jsonify({"code": 0, "data": data, "msg": "success"})


# 获取todolist
@backstage.route(BASEURL + "/todoList", methods=["GET"])
def todolist():
    set1 = db.todos
    params = request.args
    # 获取当前时间戳
    now = int(time.time())
    # 获取已完成列表时间范围
    start_time = 0
    end_time = 0
    if params.get("selectStamp"):
        start_time, end_time = params.get("selectStamp").split(",")
    # "finish_timestamp": {"$gte": int(start_time),"$lte":int(end_time)}
    cursor = set1.find(
        {
            "is_del": 0,
        },
        {"_id": 0},
    )
    # list0未完成 list1已完成 list2逾期
    list0 = []
    list1 = []
    list2 = []
    for i in cursor:
        # 截止时间
        struct_time = time.strptime(i["stopDate"], "%Y-%m-%d %H:%M:%S")
        # 当前时间
        stamp = int(time.mktime(struct_time))
        # 过滤已删除的todo
        if i["is_del"] == 0:
            if i["finish_status"] == 0:
                if stamp > now:
                    list0.append(i)
                else:
                    i["over_time"] = now - stamp
                    list2.append(i)
            else:
                # print(start_time, end_time, i["finish_timestamp"])
                if start_time and end_time:
                    if (i["finish_timestamp"] >= int(float(start_time))) and (
                        i["finish_timestamp"] <= int(float(end_time))
                    ):
                        list1.append(i)
                else:
                    list1.append(i)
    data = {
        "list0": sorted(list0, key=lambda x: x["stop_timestamp"]),
        "list1": sorted(list1, key=lambda x: x["finish_timestamp"], reverse=True),
        "list2": list2,
    }
    return jsonify({"code": 0, "msg": "success", "data": data})


# 点击完成todo
@backstage.route(BASEURL + "/finishTodo", methods=["PUT"])
def finishTodo():
    params = request.get_json()
    set1 = db.todos
    finish_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    set1.update(
        {"todo_id": params["todo_id"]},
        {
            "$set": {
                "finish_status": 1,
                "finish_time": finish_time,
                "finish_timestamp": int(time.time()),
            }
        },
    )
    return jsonify({"code": 0, "msg": "success"})


# 撤销完成todo
@backstage.route(BASEURL + "/unfinishTodo", methods=["PUT"])
def unfinishTodo():
    params = request.get_json()
    set1 = db.todos
    set1.update(
        {"todo_id": params["todo_id"]},
        {"$set": {"finish_status": 0, "finish_time": "", "finish_timestamp": 0}},
    )
    return jsonify({"code": 0, "msg": "success"})


# 删除todo
@backstage.route(BASEURL + "/delTodo", methods=["PUT"])
def delTodo():
    params = request.get_json()
    set1 = db.todos
    set1.update({"todo_id": params["todo_id"]}, {"$set": {"is_del": 1}})
    return jsonify({"code": 0, "msg": "success"})


# -----------------------------------------------todos结束-----------------------------------------------------------------------#


# -----------------------------------------------发表动态开始-----------------------------------------------------------------------#
# 添加随便说说
@backstage.route(BASEURL + "/addtalk", methods=["POST"])
def addtalk():
    params = request.get_json()
    date = (datetime.datetime.now().strftime("%Y/%m/%d %H:%M"),)
    set1 = db.announcements
    data = {
        "say": params.get("content"),
        "date": date[0],
    }
    set1.insert(data)
    return jsonify({"status": 0})


# -----------------------------------------------发表动态结束-----------------------------------------------------------------------#


# 修改新的css
@backstage.route(BASEURL + "/fontcss", methods=["GET", "POST"])
def fontcss():
    set1 = db.fontcss
    if request.method == "GET":
        data = set1.find_one({}, {"_id": 0})
        return jsonify({"status": 0, "data": data})
    else:
        params = request.get_json()
        fontcss = params.get("fontcss")
        ishave = set1.find_one()
        if ishave:
            set1.update({}, {"fontcss": fontcss})
        else:
            set1.insert({}, {"fontcss": fontcss})
        return jsonify({"status": 0})


# 添加友情链接
@backstage.route(BASEURL + "/friendlink", methods=["POST"])
def addfriendlink():
    set1 = db.siteOption
    params = request.get_json()
    set1.update({}, {"$push": {"friendlinks": params}})
    return jsonify({"status": 0})


# -----------------------------------------------公共开始-----------------------------------------------------------------------#
# 后台的上传图片
@backstage.route(BASEURL + "/uploadOne", methods=["POST"])
def uploadOne():
    img = request.files["file"]
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + (
        img.filename[-8:]
    )  # 图片防止重复
    file_path = APPIMGPATH + filename
    img.save(file_path)
    return jsonify({"msg": "success", "code": 0, "data": file_path})


# -----------------------------------------------公共结束-----------------------------------------------------------------------#
