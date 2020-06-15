from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route("/")
def render_timeline():
    return render_template('index.html')


@app.route("/<last_name>/<name>")
def render_timeline_name(last_name, name):
    return render_template('name_timeline.html',
                           vars={
                               'last_name': last_name,
                               'name': name
                           }
                           )


if __name__ == "__main__":
    app.run(port=5000, host='0.0.0.0', use_reloader=True, threaded=True, debug=True)
