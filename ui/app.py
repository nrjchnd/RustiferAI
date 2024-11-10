from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        source_repo = request.form['source_repo']
        source_branch = request.form['source_branch']
        source_auth = request.form['source_auth']
        dest_repo = request.form['dest_repo']
        dest_branch = request.form['dest_branch']
        dest_auth = request.form['dest_auth']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO repositories (source_repo, source_branch, source_auth, dest_repo, dest_branch, dest_auth)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (source_repo, source_branch, source_auth, dest_repo, dest_branch, dest_auth))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('index'))

    return render_template('index.html')
