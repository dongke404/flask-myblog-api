
import datetime
# 邮件发送
from .config import FROM_ADDR, QQEMAILAUTH
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr
import smtplib
# 邮件发送    
def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

# FROM_ADDR = 'xxx@qq.com' #来源 登陆时要用
# QQEMAILAUTH = 'xxxxxxxxx' # 授权码
# to_addr = 'xxxx@qq.com' # 目标地址
def send_email(to_addr,title,text):
    try:
        msg = MIMEText(text, 'plain', 'utf-8')
        msg['From'] = _format_addr('Kirkdong <%s>' % FROM_ADDR)
        msg['To'] = _format_addr('管理员 <%s>' % to_addr)
        msg['Subject'] = Header(title, 'utf-8').encode()
            
        smtp_server = 'smtp.qq.com'
        smtp_port = 587
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.set_debuglevel(1)
        server.login(FROM_ADDR, QQEMAILAUTH)
        server.sendmail(FROM_ADDR, [to_addr], msg.as_string())
        server.quit()
    except Exception as e:
        print(e)
        return False

# 时间轴处理
def get_list(s):
    return datetime.datetime.strptime(s, "%Y/%m/%d %H:%M").timestamp()

# 创建文件夹
def mkdir(path):
    # 引入模块
    import os
    # 去除首位空格
    path = path.strip()
    # 去除尾部 \ 符号
    path = path.rstrip("\\")
    # 判断路径是否存在
    # 存在     True
    # 不存在   False
    isExists = os.path.exists(path)
    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)
        # print(path + ' 创建成功')
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        print(path + ' 目录已存在')
        return False

# id自增函数
def insert_doc(doc, collection, db, idname="id" ):
    doc[idname] = db.seqs.find_and_modify(
        query={ 'collection' : collection },
        update={'$inc': {'id': 1}},
        fields={'id': 1, '_id': 0},
        new=True 
    ).get('id')