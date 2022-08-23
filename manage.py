from app.myblog import myblog
from app.backstage import backstage
from app import app
#注册蓝图
app.register_blueprint(myblog)
app.register_blueprint(backstage)

if __name__ == '__main__':
    app.run()
