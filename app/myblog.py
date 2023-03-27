# blog页接口
# 主业务逻辑中的视图和路由的定义
import time
from . import app, db
from flask_cors import CORS
from flask import request, jsonify, Blueprint, abort
import math
import datetime
import os
from .config import PAGE_NUM, BASEURL, AUTHPWD, MoviePath
from .utils import get_list, send_email, insert_doc

CORS(app, supports_credentials=True)

# 蓝图注册模块
myblog = Blueprint("myblog", __name__)


import requests


# tweet模块
@myblog.route(BASEURL + "/tweet", methods=["GET"])
def tweet():
    params = request.args
    diyurl = params.get("url")
    headers = {
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAAGsHlgEAAAAAb%2B9PlDA4s0RymxfRNxzf0pFmldU%3DZJcxdDn2dZ0XFO2muw4Yd9c5FKOeVGhsRePSmMXcipaw2VhEEV"
    }
    url = "https://api.twitter.com/2/" + diyurl
    r=requests.get(url,headers=headers)
    data = r.json().get("data")
    ids = [i.get("id") for i in data]
    ids = ",".join(ids)
    url1 = "https://api.twitter.com/2/tweets?ids=" + ids + "&tweet.fields=created_at,public_metrics"
    r1=requests.get(url1,headers=headers)
    data1 = r1.json().get("data")
    return jsonify({"code": 0,  "msg": "success", "data": data1})

# 获取文章列表
@myblog.route(BASEURL + "/article")
def reqArticle():
    params = request.args
    # print(params)
    category = params.get("category")
    keyword = params.get("keyword")
    sort = params.get("sort")
    current_page = int(params.get("page", 1))
    limit = int(params.get("limit", 16))
    date = params.get("date")
    tag = params.get("tag")
    set1 = db.blogs
    set2 = db.comments
    if category:
        iteration = (
            set1.find({"category": category}, {"_id": 0})
            .sort("article_id", -1)
            .skip((current_page - 1) * limit)
            .limit(limit)
        )

    elif keyword:
        # set1.create_index([("title", 1)])
        iteration = (
            set1.find(
                {
                    "$or": [
                        {"title": {"$regex": keyword, "$options": "i"}},
                        {"category": {"$regex": keyword, "$options": "i"}},
                        {"description": {"$regex": keyword, "$options": "i"}},
                        {"content": {"$regex": keyword, "$options": "i"}},
                        {"origin": {"$regex": keyword, "$options": "i"}},
                        {"tags": {"$regex": keyword, "$options": "i"}},
                    ]
                },
                {"_id": 0},
            )
            .sort("article_id", -1)
            .skip((current_page - 1) * limit)
            .limit(limit)
        )
    elif sort:
        iteration = set1.find({}, {"_id": 0}).sort("view_num", -1).limit(10)
    elif date:
        date = date.replace("-", "/")
        iteration = set1.find({"date": {"$regex": date}}, {"_id": 0})
    elif tag:
        iteration = set1.find({"tags": {"$in": [tag]}}, {"_id": 0})
    else:
        iteration = (
            set1.find(
                {},
                {
                    "_id": 0,
                },
            )
            .sort("article_id", -1)
            .skip((current_page - 1) * limit)
            .limit(limit)
        )
    data = {}
    lst = []
    for x in iteration:
        cmt_num = set2.find({"post_id": x["article_id"]}).count()
        x["cmt_num"] = cmt_num
        x["src"] = "https://kedong.me" + x["imgUrl"]
        x["alt"] = x["title"]
        lst.append(x)
    pagination = {}
    pagination["page"] = current_page
    pagination["total_page"] = math.ceil(iteration.count() / limit)
    pagination["count"] = math.ceil(iteration.count())
    # 倒序
    data["list"] = lst
    data["pagination"] = pagination
    return jsonify({"data": data, "code": 0, "msg": "success"})

# 获取文章详情
@myblog.route(BASEURL + "/article/<int:article_id>")
def reqArticleDetail(article_id):
    # print(article_id)
    set1 = db.blogs
    set1.update({"article_id": article_id}, {"$inc": {"view_num": 1}})
    # 根据时间添加单日访问量
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    set2 = db.view_num
    set2.update(
        {"date": today},
        {"$inc": {"num": 1}},
        upsert=True,
    )
    data = set1.find_one({"article_id": article_id}, {"_id": 0})
    if not data:
        return jsonify({"code": 404, "msg": "文章不存在", "data": {}})
    related = set1.aggregate(
        [
            {"$sample": {"size": 6}},
            {"$project": {"_id": 0, "article_id": 1, "imgUrl": 1, "title": 1 , "description": 1}},
        ],
    )
    _ = []
    for i in related:
        _.append(i)
    data["related"] = _
    if data.get("privacy") == 0:
        authPwd = request.cookies.get("authPwd")
        if authPwd == AUTHPWD:
            return jsonify({"status": 0, "data": data})
        else:
            # data={}
            # data["related"] = _
            return jsonify({"code": 403, "msg": "权限不足", "data": data})
    return jsonify({"data": data, "code": 0, "msg": "success"})


# 归档模块
@myblog.route(BASEURL + "/timeline")
def reqTimeline():
    set1 = db.blogs
    set2 = db.announcements
    blog_cursor = set1.find(
        {},
        {
            "_id": 0,
            "article_id": 1,
            "title": 1,
            "description": 1,
            "date": 1,
            "view_num": 1,
            "cmt_num": 1,
            "likes": 1,
        },
    )
    data = []
    for i in blog_cursor:
        data.append(i)
    data = sorted(data, key=lambda x: get_list(x["date"]), reverse=True)
    # 按月组合数据
    res = {}
    curmonth = data[0]["date"][0:7]
    res[curmonth] = []
    for item in data:
        if item["date"][0:7] == curmonth:
            res[curmonth].append(item)
        else:
            curmonth = item["date"][0:7]
            res[curmonth] = []
            res[curmonth].append(item)

    resdata = []
    for k, v in res.items():
        dic = {}
        dic["year"] = k[0:4]
        # 去掉0
        dic["month"] = k[5:7].lstrip("0")
        dic["articles"] = v
        resdata.append(dic)
    return jsonify({"data": resdata, "code": 0, "msg": "success"})


# 评论打钩注册用户
@myblog.route(BASEURL + "/register", methods=["POST"])
def register():
    usersSet = db.users
    params = request.get_json()
    email = params["email"]
    user = usersSet.find_one({"email": email},{"_id":0})
    if user:
        if user['email'] == "dongkirk1992@gmail.com":
            return jsonify({"code": 1, "msg": "无法修改"})
        #更新用户信息
        usersSet.update(
            {"email":email},
            {"$set":{"name": params["name"], "site": params["site"],"gravatar": params["gravatar"]}},
        )
    else:
        insert_doc(params, "users", db, "user_id")
        usersSet.insert_one(params)
    user = usersSet.find_one({"email": email},{"_id":0})
    return jsonify({"code": 0, "msg": "success",'data':user})



# 评论操作GET读取,Post发布
@myblog.route(BASEURL + "/comment", methods=["GET", "POST"])
def comments():
    commentsSet = db.comments
    blogsSet = db.blogs
    usersSet = db.users
    replysSet = db.replys
    # 读取评论列表
    if request.method == "GET":
        params = request.args
        page = int(params["page"])
        limit = int(params["limit"])
        sort = int(params["sort"])
        post_id = int(params["post_id"])
        data = {}
        commentsSql = commentsSet.find({"post_id": post_id}, {"_id": 0})
        data["count"] = commentsSql.count()
        lst = []
        if sort == 2:
            comments = (
                commentsSql.sort("reply_num", -1).skip((page - 1) * limit).limit(limit)
            )
        elif sort == 1:
            comments = commentsSql.skip((page - 1) * limit).limit(limit)
        else:
            comments = (
                commentsSql.sort("comment_id", -1).skip((page - 1) * limit).limit(limit)
            )
        for comment in comments:
            if comment["author"]:
                if usersSet.find_one({"user_id": comment["author"]}, {"_id": 0}):
                    comment["author"]  = usersSet.find_one(
                        {"user_id": comment["author"]}, {"_id": 0, "email": 0}
                    )
                else:
                    comment["author"] = {"name": "游客", "site": ""}

            replys = replysSet.find({"p_comment_id": comment["comment_id"]}, {"_id": 0})
            comment["replys"] = []
            for reply in replys:
                if reply["author"]:
                    if usersSet.find_one({"user_id": reply["author"]}, {"_id": 0}):
                        reply["author"] = usersSet.find_one(
                            {"user_id": reply["author"]}, {"_id": 0, "email": 0}
                        )
                    else:
                        reply["author"] = {
                            "name": "游客",
                            "site": "",
                        }
                comment["replys"].append(reply)
            # sql写入回复数
            commentsSet.update(
                {"comment_id": comment["comment_id"]},
                {"$set": {"reply_num": len(comment["replys"])}},
            )
            lst.append(comment)
        data["comments"] = lst
        return jsonify({"data": data, "code": 0, "msg": "success"})
    else:
        params = request.get_json()
        # 获取ip
        ip = request.headers.get("Cf-Connecting-Ip")
        url = "http://ip-api.com/json/{0}?lang=zh-CN".format(ip)
        r = requests.post(url)
        ipInfo = r.json()
        if ipInfo["status"] == "success":
            _obj = {}
            # {'status': 'success', 'country': '中国', 'countryCode': 'CN', 'region': 'ZJ', 'regionName': '浙江省', 'city': '杭州', 'zip': '', 'lat': 30.2994, 'lon': 120.1612, 'timezone': 'Asia/Shanghai', 'isp': 'CHINANET', 'org': 'China Telecom', 'as': 'AS4134 CHINANET-BACKBONE', 'query': '240e:390:a33:1591:c10f:55c0:9de6:75c9'}
            _obj["country"] = ipInfo["country"]
            _obj["countryCode"] = ipInfo["countryCode"]
            _obj["region"] = ipInfo["region"]
            _obj["regionName"] = ipInfo["regionName"]
            _obj["city"] = ipInfo["city"]
            _obj["isp"] = ipInfo["isp"]
            params["ipInfo"] = _obj
        params["create_time"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        params["likes"] = 0
        user = usersSet.find_one({"email": params["author"]["email"]}, {"_id": 0})
        if not user:
            insert_doc(params["author"], "users", db, "user_id")
            usersSet.insert(params["author"])
            user = usersSet.find_one({"email": params["author"]["email"]}, {"_id": 0})
            params["author"] = params["author"]["user_id"]
        else:
            usersSet.update(
                {"email": params["author"]["email"]},
                {"$set": {"gravatar":params["author"]["gravatar"]}},
            )
            params["author"] = user["user_id"]
        # 有p_comment_id 是回复 没有是评论
        to_author_email = ""
        if params.get("p_comment_id"):
            insert_doc(params, "comments", db, "comment_id")
            if params["target_comment_id"] != params["p_comment_id"]:
                to_reply = replysSet.find_one(
                    {"comment_id": params["target_comment_id"]}, {"_id": 0}
                )
                to_author = usersSet.find_one(
                    {"user_id": to_reply["author"]}, {"_id": 0}
                )
                if to_author:
                    params["to_author"] = to_author["user_id"]
                    params["to_author_name"] = to_author["name"]
                    to_author_email = to_author["email"]
                else:
                    params["to_author_name"] = "匿名用户"
            replysSet.insert(params)
            title = "您在kirkdong的博客有了新的回复"
            content = "您在kirkdong的博客有了新的回复，快去看看吧！"
            if to_author_email:
                send_email(to_author_email, title, content)
        else:
            insert_doc(params, "comments", db, "comment_id")
            commentsSet.insert(params)
            send_email('454661578@qq.com', '您在kirkdong的博客有了新的评论', params["content"])
        blogsSet.update({"article_id": params["post_id"]}, {"$inc": {"cmt_num": 1}})
        return jsonify({"data": user , "code": 0, "msg": "success"})

# 点赞评论
@myblog.route(BASEURL + "/likeComment", methods=["POST"])
def likeComment():
    commentsSet = db.comments
    replysSet = db.replys
    usersSet = db.users
    params = request.get_json()
    comment_id =int(params.get("comment_id"))
    isReply = params.get("isReply")
    user_id = params.get("user_id")
    
    if user_id:
        # 点赞 去除 踩
        usersSet.update({"user_id":int(user_id)}, {"$addToSet": {"like_comments": comment_id},"$pull": {"dislike_comments": comment_id}})
    if isReply:
        replysSet.update({"comment_id": comment_id}, {"$inc": {"likes": 1}})
    else:
        commentsSet.update({"comment_id": comment_id}, {"$inc": {"likes": 1}})
    return jsonify({"data": {}, "code": 0, "msg": "success"})

# 踩评论
@myblog.route(BASEURL + "/dislikeComment", methods=["POST"])
def dislikeComment():
    commentsSet = db.comments
    replysSet = db.replys
    usersSet = db.users
    params = request.get_json()
    comment_id = int(params.get("comment_id"))
    isReply = params.get("isReply")
    user_id = params.get("user_id")
    if user_id:
        # 踩 去除 点赞
        usersSet.update({"user_id":int(user_id)}, {"$addToSet": {"dislike_comments": comment_id},"$pull": {"like_comments": comment_id}})
    if isReply:
        replysSet.update({"comment_id": comment_id}, {"$inc": {"dislikes": 1}})
    else:
        commentsSet.update({"comment_id": comment_id}, {"$inc": {"dislikes": 1}})

    return jsonify({"data": {}, "code": 0, "msg": "success"})

# 获取主站信息
@myblog.route(BASEURL + "/siteOption")
def siteOption():
    set1 = db.siteOption
    data = set1.find_one({}, {"_id": 0})
    if not data:
        create_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        set1.insert(
            {
                "name": "dongke",
                "likes": 0,
                "blacklist": {"mails": [], "keywords": []},
                "create_time": create_time,
            }
        )
    return jsonify({"data": data, "code": 0, "msg": "success"})


# 统计访问量,点赞,评论,总文章
@myblog.route(BASEURL + "/statistics")
def statistics():
    set1 = db.blogs
    set2 = db.comments
    set3 = db.siteOption
    set4 = db.view_num
    data = {}
    data["blog_num"] = set1.count()
    data["comment_num"] = set2.count()
    data["likes"] = set3.find_one({}, {"_id": 0})["likes"]
    # view_num文档当日访问量
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    data["view_num_today"] = set4.find_one({"date": today}, {"_id": 0})
    if data["view_num_today"]:
        data["view_num_today"] = data["view_num_today"]["num"]
    else:
        data["view_num_today"] = 0
    return jsonify({"data": data, "code": 0, "msg": "success"})


# 点赞文章
@myblog.route(BASEURL + "/vote_article", methods=["POST"])
def likearticle():
    usersSet = db.users
    blogsSet = db.blogs
    params = request.get_json()
    article_id = int(params.get("article_id")) 
    user_id = params.get("user_id")
    #更新用户喜欢的文章
    if user_id:
        usersSet.update({"user_id": int(user_id)}, {"$addToSet": {"like_articles": article_id}})
        #+1
        blogsSet.update({"article_id": article_id}, {"$inc": {"likes": 1}})
    else:
        blogsSet.update({"article_id": article_id}, {"$inc": {"likes": 1}})
    return jsonify({"data": 0, "code": 0, "msg": "success"})



# 点赞留言板
@myblog.route(BASEURL + "/like/site", methods=["POST"])
def likeSite():
    set1 = db.siteOption
    set1.update({}, {"$inc": {"likes": 1}})
    return jsonify({"status": 0})

# 获取电影列表
@myblog.route(BASEURL + "/movielist")
def reqMovielist():
    filelist = os.listdir(MoviePath)
    return jsonify({"data": filelist})


# 标签操作
@myblog.route(BASEURL + "/tag", methods=["GET", "POST"])
def tags():
    set1 = db.tags
    set2 = db.blogs
    if request.method == "GET":
        cursor = set1.find({}, {"_id": 0})
        data = []
        for i in cursor:
            count = set2.find({"tags": {"$in": [i["name"]]}}, {"_id": 0}).count()
            i["count"] = count
            data.append(i)
        return jsonify({"data": data, "code": 0, "msg": "success"})


# 测试功能接口
@myblog.route(BASEURL + "/testport")
def testport():
    # 延时2秒
    time.sleep(5)
    return jsonify({"code": 0, "data": "tesrt4444", "msg": "success"})
