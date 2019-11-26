#!/anaconda3/bin/python3.7
# -*- coding: utf-8 -*-
# Latex.py
# Bernard Schroffenegger
# 15th of October, 2019


from flask import Flask, render_template
app = Flask(__name__, template_folder='HTML')  # the WSGI-App (Web Server Gateway Interface)
app.config['SECRET_KEY'] = '9102_regnilluB_hcirnieH_kitsiugnilretupmoC_reuf_tutitsnI'

HOST = 'localhost'  # Hostname to listen on (localhost as default)
PORT = 5000  # defaults to 5000
DEBUG = True  # server reloads itself after code changes


# Start: HOME
@app.route('/')  # decorator: URL --> function
def index():
    return render_template('home.html', title='Bullinger Briefwechsel')


@app.route('/home', methods=['post', 'get'])
def home():
    return render_template('home.html')


@app.route('/login', methods=['post', 'get'])  # decorator: URL --> function
def load_page_login():
    return render_template('account_login.html')


@app.route('/register', methods=['post', 'get'])  # decorator: URL --> function
def load_page_register():
    return render_template('account_register.html')


@app.route('/admin', methods=['post', 'get'])  # decorator: URL --> function
def load_page_admin():
    return render_template('account_admin.html')


'''
@app.route('/login', methods=['post', 'get'])
def login():
    if request.method == 'POST':
        user = request.form["name"]
        email = request.form["email"]
        pw = request.form["password"]
        print(user, email, pw)
        return render_template('base.html')
'''

if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)  # local dev server
