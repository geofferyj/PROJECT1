import os
from functools import wraps

from flask import Flask, session, redirect, render_template, url_for, request, flash
from flask_session import Session
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

dbstring = "postgres://fabeidpsjarnlm:080cd5f8a5a7ce8dd8d6c71863c76924e7a26ebcab39588e6dc637a1741bf496@ec2-3-234-109-123.compute-1.amazonaws.com:5432/de693jkmt9rih3"

# Configure session to use filesystem
app.config['SECRET_KEY'] = "efd432e0aca715610c505c533037b95d6fb22f5692a0d33820ab7b19ef06f513"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(dbstring)
db = scoped_session(sessionmaker(bind=engine))

db.execute("""CREATE TABLE IF NOT EXISTS users(uid SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                username VARCHAR NOT NULL UNIQUE,
                email VARCHAR NOT NULL UNIQUE,
                password VARCHAR NOT NULL)""")


db.execute("""CREATE TABLE IF NOT EXISTS books(isbn VARCHAR PRIMARY KEY,
                title VARCHAR NOT NULL,
                author VARCHAR NOT NULL,
                year INTEGER NOT NULL)""")


db.execute("""CREATE TABLE IF NOT EXISTS reviews(id SERIAL PRIMARY KEY,
                uid INTEGER NOT NULL REFERENCES users(uid),
                isbn VARCHAR NOT NULL REFERENCES books(isbn),
                review VARCHAR NOT NULL,
                rating INTEGER CHECK(rating > 0 AND rating <= 5) NOT NULL,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_uid_isbn UNIQUE(uid,isbn)
                )""")
db.commit()


def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('login', next=request.url))
        return func(*args, **kwargs)
    return wrapper


@app.route("/", methods = ["POST", "GET"])
@login_required
def index():
    
    if request.method == "POST":
        search = request.form.get("search")
        data = db.execute("SELECT * FROM books WHERE title ILIKE :search OR author ILIKE :search OR isbn ILIKE :search", {"search": '%' + search + '%'})
        return render_template('index.html', data=data)

    return render_template('index.html')


@app.route("/login/", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        form = request.form
        email = form["email"]
        password = form["password"]
        next_url = form["next"]
        user = db.execute("SELECT email FROM users WHERE email = :email", {"email": email}).fetchone()
        if user:
            session["email"] = user.email
            if next_url:
                flash("Login successful")
                return redirect(next_url)
            return redirect(url_for("index"))
        else:
            flash("user not found")
            return redirect(url_for("login"))
        
    return render_template("login.html")


@app.route("/logout/")
def logout():
    session.pop("email", None)

    return redirect(url_for("login"))

    
@app.route("/signup/", methods = ["POST", "GET"])
def signup():
    if request.method == "POST":
        form = request.form
        username = form["username"]
        name = form["name"]
        email = form["email"]
        password = form["password"]

        try:
            db.execute("INSERT INTO users(name, username, email, password) VALUES(:name, :username, :email, :password)", {
                       "name": name, "username": username, "email": email, "password": password})
            db.commit()
            return redirect(url_for('login'))
        except exc.IntegrityError:
            flash('Username Already exists, please try another')
            return redirect(url_for('signup'))
    return render_template('signup.html')


@app.route("/book/<isbn>/")
@login_required
def book_details(isbn):

    reviews = db.execute("SELECT name, review, rating FROM users, reviews WHERE users.uid = reviews.uid AND reviews.isbn = :isbn ORDER BY reviews.review_date", {"isbn":isbn}).fetchone()
    details = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()

    return render_template("book_details.html", details=details, reviews=reviews)


@app.shell_context_processor
def make_shell_context():
    return {'db': db}

if __name__ == "__main__":
    app.debug = True
    app.run()