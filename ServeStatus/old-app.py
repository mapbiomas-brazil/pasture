from flask import Flask
from flask import render_template
from flask import jsonify, redirect, url_for
from dynaconf import FlaskDynaconf
import ee
import urllib3


service_account = 'gee-jairo-mr@nxgame2009.iam.gserviceaccount.com'
credentials = ee.ServiceAccountCredentials(service_account, '../privatekey.json')
ee.Initialize(credentials)


# create your app
app = Flask(__name__)

FlaskDynaconf(app)


@app.route("/")
def index():
    e = ee.batch.Task.list()
    res =  [
        {
            'id':i.id,
            'name':i.config['description'],
            'status':i.state
        }for i in e]
    return jsonify(res)

@app.route("/api/all")
def get_all_task():
    try:  
        e = ee.batch.Task.list()
        res =  [
            {
                'id':i.id,
                'name':i.config['description'],
                'status':i.state
            }for i in e]
        return jsonify(res)
    except urllib3.exceptions.ProtocolError:
        return 'Aguarde por 5 segundos', {"Refresh": f"5; url={url_for('get_all_task')}"}


app.add_url_rule(app.config.TEST_RULE, view_func=lambda: "test")


if __name__ == "__main__":
    app.run()