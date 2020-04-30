import re
import math
import datetime

# print(math.ceil(5.1))

# string = '## 测试一下啊\n![test](http://cms-bucket.ws.126.net/2020/0420/86786531j00q91qqh006fc0008c005kc.jpg?imageView&thumbnail=300y200&quality=85)\n这是正文[test](http://cms-buuality=85)\n这是正文'


# res = re.search(r".*?\[.*?\]\((.+?)\).*", string, flags=re.S)
# print(res.group(1))


data=[{'article_id': 18, 'title': '阿萨德搜索所所所所所', 'description': '三生三世啥所所所所所所', 'date': '2020/04/27 15:04'}, {'article_id': 17, 'title': '阿萨达闪电阿萨达闪电', 'description': '阿达是多少', 'date': '2020/04/27 15:03'}, {'article_id': 16, 'title': '阿萨达闪电阿萨达闪电', 'description': '阿达是多少', 'date': '2020/04/27 15:02'}, {'article_id': 15, 'title': '阿是大师大师的', 'description': '啊大大大是', 'date': '2020/04/27 02:16'}, {'article_id': 14, 'title': '苏打水', 'description': 'adssss', 'date': '2020/04/25 02:03'}, {'article_id': 13, 'title': 'asddddddddddasd', 'description': 'adssss', 'date': '2020/04/25 02:02'}, {'article_id': 12, 'title': 'asddddddddddasd', 'description': 'adssss', 'date': '2020/04/25 02:02'}, {'article_id': 11, 'title': 'asddddddddddasd', 'description': 'adssss', 'date': '2020/04/25 01:21'}, {'article_id': 10, 'title': 'asddddddddddasd', 'description': 'adssss', 'date': '2020/04/24 03:41'}, {'article_id': 9, 'title': '阿萨德', 'description': '阿萨德', 'date': '2020/04/21 20:04'}, {'article_id': 8, 'title': '阿萨德', 'description': '阿萨德', 'date': '2020/04/21 15:45'}, {'article_id': 7, 'title': '阿萨德', 'description': '阿萨德', 'date': '2019/04/21 15:45'}, {'article_id': 6, 'title': '阿萨德', 'description': '阿萨德', 'date': '2019/04/21 15:45'}, {'article_id': 5, 'title': '阿萨德', 'description': '阿萨德', 'date': '2019/04/21 15:45'}, {'article_id': 4, 'title': '阿萨德', 'description': '阿萨德', 'date': '2018/04/21 15:45'}, {'article_id': 3, 'title': '阿萨德', 'description': '阿萨德', 'date': '2018/04/21 13:27'}, {'article_id': 2, 'title': '阿萨德', 
'description': '阿萨德', 'date': '2017/04/21 13:27'}, {'article_id': 1, 'title': '阿萨德', 'description': '阿萨德', 'date': '2017/04/21 13:27'}, {'say': '我出生了哈飒飒的是是是', 'date': '2020/04/28 16:41:53'}, {'say': '我出生了哈飒飒的', 'date': '2019/04/28 16:41:50'}, {'say': '我出生了哈', 'date': '2018/04/28 16:41:46'}, {'say': '我出生了哈三生达闪阿萨德', 'date': '2017/04/28 16:41:43'}, {'say': '我出生了哈三生达闪电是是是', 'date': '2017/04/28 16:41:39'}]

def get_list(s):
    return datetime.datetime.strptime(s,"%Y/%m/%d %H:%M").timestamp()

      
def getdate(x):
    return x["date"]
for x in data:
    print(getdate(x))

# res=sorted(data,key=lambda x:get_list(getdate(x)))
# res=datetime.datetime.strptime(s,"%Y/%m/%d %H:%M").timestamp()

# print(res)