import app.router
from app import app

if __name__ == '__main__':
    # app.run(debug=True,host='0.0.0.0', port=5000)
    # app.run(debug=True,host='0.0.0.0', port=5000,ssl_context=('/code/cert.pem','/code/key.pem'))
    app.run()
