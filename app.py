
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3, os

app = Flask(__name__)
DB = 'data.db'
PASSWORD_HASH = generate_password_hash('admin123')

def init_db():
    if not os.path.exists(DB):
        con=sqlite3.connect(DB)
        c=con.cursor()
        c.execute("CREATE TABLE stoerungen(id INTEGER PRIMARY KEY, asset TEXT, beschreibung TEXT)")
        con.commit()
        con.close()

@app.before_first_request
def setup():
    init_db()

@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST':
        if check_password_hash(PASSWORD_HASH, request.form.get('password','')):
            return redirect(url_for('list_stoerungen'))
    return render_template('login.html')

@app.route('/list')
def list_stoerungen():
    con=sqlite3.connect(DB)
    c=con.cursor()
    c.execute("SELECT * FROM stoerungen")
    data=c.fetchall()
    con.close()
    return render_template('list.html', data=data)

@app.route('/new', methods=['GET','POST'])
def new():
    if request.method=='POST':
        asset=request.form['asset']
        besch=request.form['beschreibung']
        con=sqlite3.connect(DB)
        c=con.cursor()
        c.execute("INSERT INTO stoerungen(asset,beschreibung) VALUES(?,?)",(asset,besch))
        con.commit()
        con.close()
        return redirect(url_for('list_stoerungen'))
    return render_template('new.html')

if __name__=='__main__':
    app.run(host='0.0.0.0')
