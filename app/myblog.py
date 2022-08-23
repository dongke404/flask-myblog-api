# blog页接口
# 主业务逻辑中的视图和路由的定义
from . import app,db
from flask_cors import CORS
from flask import request, jsonify ,Blueprint, abort
import math
import datetime
import os
from .config import PAGE_NUM, BASEURL, AUTHPWD, MoviePath
from .utils import get_list
CORS(app, supports_credentials=True)

#蓝图注册模块
myblog=Blueprint('myblog',__name__)

# 获取文章列表
@myblog.route(BASEURL + '/article')
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
@myblog.route(BASEURL + '/timeline')
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
@myblog.route(BASEURL + '/article/<int:article_id>')
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
@myblog.route(BASEURL + '/announcement')
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
@myblog.route(BASEURL + '/comment', methods=["GET", "POST"])
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
@myblog.route(BASEURL + '/siteOption')
def siteOption():
    set1 = db.siteOption
    data = set1.find_one({}, {"_id": 0})
    if not data:
        create_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        set1.insert({"name": "dongke", "likes": 0, "blacklist": {
                    "mails": [], "keywords": []}, "create_time": create_time})
    return jsonify({'status': 0, 'data': data})

# 点赞文章
@myblog.route(BASEURL + '/like/article', methods=["POST"])
def likearticle():
    params = request.get_json()
    article_id = params.get("article_id")
    set1 = db.blogs
    set1.update({"article_id": article_id}, {'$inc': {'likes': 1}})
    return jsonify({'status': 0})


# 点赞留言板
@myblog.route(BASEURL + '/like/site', methods=["POST"])
def likeSite():
    set1 = db.siteOption
    set1.update({}, {'$inc': {'likes': 1}})
    return jsonify({'status': 0})


# 点赞评论
@myblog.route(BASEURL + '/like/comment', methods=["POST"])
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
@myblog.route(BASEURL + '/movielist')
def reqMovielist():
    filelist = os.listdir(MoviePath)
    print(MoviePath,filelist)
    return jsonify({'data': filelist})

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
        return jsonify({"status": 0, "data": data})
