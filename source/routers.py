from __main__ import app

# a simple page that says hello
@app.route('/hello')
def hello():
    return 'Hello, World!'+str(app.config["BOOTSTRAP_IP"])
