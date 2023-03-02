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
from .utils import get_list
from .utils import insert_doc

CORS(app, supports_credentials=True)

# 蓝图注册模块
myblog = Blueprint("myblog", __name__)


import requests


@myblog.route(BASEURL + "/tweet", methods=["GET"])
def tweet():
    params = request.args
    time.sleep(5)
    # diyurl = params.get("url")
    # headers = {
    #     "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAAGsHlgEAAAAAb%2B9PlDA4s0RymxfRNxzf0pFmldU%3DZJcxdDn2dZ0XFO2muw4Yd9c5FKOeVGhsRePSmMXcipaw2VhEEV"
    # }
    # url = "https://api.twitter.com/2/" + diyurl
    # r=requests.get(url,headers=headers)
    # print(r.json())
    # return r.json()
    return jsonify(
        {
            "code": 0,
            "msg": "success",
            "data": [
                {
                    "edit_history_tweet_ids": ["1"],
                    "id": "1",
                    "text": "111111111",
                },
                {
                    "edit_history_tweet_ids": ["1619581346988580864"],
                    "id": "1619581346988580864",
                    "text": "test img https://t.co/2aFbQxuRjA",
                },
                {
                    "edit_history_tweet_ids": ["1619531173289660416"],
                    "id": "1619531173289660416",
                    "text": "testapi",
                },
                {
                    "edit_history_tweet_ids": ["1226503216264810496"],
                    "id": "1226503216264810496",
                    "text": "I just deployed a high performance cloud server on https://t.co/I75Qau2936 ! #ILoveVultr #Cloud https://t.co/GwEryuU3Uz",
                },
            ],
            "meta": {
                "newest_id": "1619581346988580864",
                "oldest_id": "1226503216264810496",
                "result_count": 3,
            },
        }
    )


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


# 获取时间轴列表
@myblog.route(BASEURL + "/timeline")
def reqTimeline():
    set1 = db.blogs
    set2 = db.announcements
    blog_cursor = set1.find(
        {}, {"_id": 0, "article_id": 1, "title": 1, "description": 1, "date": 1,"view_num" : 1,"cmt_num" : 1,'likes':1}
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
        #去掉0
        dic["month"] = k[5:7].lstrip("0")
        dic["articles"] = v
        resdata.append(dic)
    return jsonify({"data": resdata, "code": 0, "msg": "success"})


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
        return jsonify({"status": 404, "msg": "页面不存在", "data": {}})
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
    if data.get("privacy") == 0:
        authPwd = request.cookies.get("authPwd")
        if authPwd == AUTHPWD:
            return jsonify({"status": 0, "data": data})
        else:
            # data={}
            # data["related"] = _
            return jsonify({"status": 403, "msg": "权限不足", "data": data})
    return jsonify({"data": data, "code": 0, "msg": "success"})


# 获取随便说说内容
@myblog.route(BASEURL + "/announcement")
def announcement():
    set1 = db.announcements
    data = []
    for x in set1.find(
        {},
        {
            "_id": 0,
            "say": 1,
            "date": 1,
        },
    ).sort("_id", -1):
        data.append(x)
    data = data[0:10]
    return jsonify({"status": 0, "data": data})


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
        page_num = int(params["page_num"])
        sort = int(params["sort"])
        post_id = int(params["post_id"])
        data = {}
        # isReply不等于1的是评论
        commentsSql= commentsSet.find({"post_id": post_id}, {"_id": 0})
        data['count'] = commentsSql.count()
        lst = []
        if sort == 2:
            comments = (
                commentsSql
                .sort("likes", -1)
                .skip((page - 1) * page_num)
                .limit(page_num)
            )
        else:
            comments = (
                commentsSql
                .sort("comment_id", -1)
                .skip((page - 1) * page_num)
                .limit(page_num)
            )
        for comment in comments:
            replys = replysSet.find({"p_comment_id": comment["comment_id"]}, {"_id": 0})
            comment["replys"] = []
            for reply in replys:
                comment["replys"].append(reply)
            lst.append(comment)
        data["comments"] = lst
        return jsonify({"data": data, "code": 0, "msg": "success"})
    else:
        params = request.get_json()
        # ip = request.headers.get('X-Forwarded-For')
        params["create_time"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        params["likes"] = 0
        user = usersSet.find_one({"email": params['author']["email"]}, {"_id": 0})
        if not user:
            usersSet.insert({"email": params['author']["email"], "name": params['author']["name"], "site": params['author']["site"], "gravatar": params['author']["gravatar"]})
        params["author"] = params['author']["email"]
        insert_doc(params, "comments", db, "comment_id")
        if params["p_comment_id"]:
            insert_doc(params, "comments", db, "comment_id")
            replysSet.insert(params)
        else:
            insert_doc(params, "comments", db, "comment_id")
            commentsSet.insert(params)
        # if params["pid"]:
        #     targetCmt = commentsSet.find_one({"comment_id": params["pid"]}, {"_id": 0})
        #     params["taruser"] = targetCmt["author"]["name"]

        blogsSet.update({"article_id": params["post_id"]}, {"$inc": {"cmt_num": 1}})
        return jsonify({"data": 0, "code": 0, "msg": "success"})


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
    #view_num文档当日访问量
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    data["view_num_today"] = set4.find_one({"date": today}, {"_id": 0})
    if data["view_num_today"]:
        data["view_num_today"] = data["view_num_today"]["num"]
    else:
        data["view_num_today"] = 0
    return jsonify({"data": data, "code": 0, "msg": "success"})

# 点赞文章
@myblog.route(BASEURL + "/like/article", methods=["POST"])
def likearticle():
    params = request.get_json()
    article_id = params.get("article_id")
    set1 = db.blogs
    set1.update({"article_id": article_id}, {"$inc": {"likes": 1}})
    return jsonify({"status": 0})


# 点赞留言板
@myblog.route(BASEURL + "/like/site", methods=["POST"])
def likeSite():
    set1 = db.siteOption
    set1.update({}, {"$inc": {"likes": 1}})
    return jsonify({"status": 0})


# 点赞评论
@myblog.route(BASEURL + "/like/comment", methods=["POST"])
def likeComment():
    set1 = db.comments
    params = request.get_json()
    comment_id = params.get("comment_id")
    # print(comment_id)
    if comment_id:
        comment = set1.find_one({"comment_id": comment_id}, {"_id": 0})
        comment["likes"] += 1
        set1.update({"comment_id": comment_id}, comment)
    return jsonify({"status": 0})


# 获取电影列表
@myblog.route(BASEURL + "/movielist")
def reqMovielist():
    filelist = os.listdir(MoviePath)
    print(MoviePath, filelist)
    return jsonify({"data": filelist})


# 修改新的css
@myblog.route(BASEURL + "/fontcss", methods=["GET", "POST"])
def fontcss():
    set1 = db.fontcss
    if request.method == "GET":
        data = set1.find_one({}, {"_id": 0})
        return jsonify({"status": 0, "data": data})


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


# 测试接口
@myblog.route(BASEURL + "/testport")
def testport():
    # 延时2秒
    time.sleep(5)
    return jsonify({"code": 0, "data": "tesrt4444", "msg": "success"})
