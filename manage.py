# import app.router
# import app.myblog
from app.myblog import myblog
from app.backstage import backstage
from app import app
#注册蓝图
app.register_blueprint(myblog)
app.register_blueprint(backstage)

if __name__ == '__main__':
    # app.run(debug=True,host='0.0.0.0', port=5000)
    # app.run(debug=True,host='0.0.0.0', port=5000,ssl_context=('/code/cert.pem','/code/key.pem'))

    app.run()
