import os, requests
from functools import wraps

from flask import Flask, session, redirect, render_template, url_for, request, flash, jsonify, make_response, abort
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
        if 'uid' not in session:
            return redirect(url_for('login', next=request.url))
        return func(*args, **kwargs)
    return wrapper


@app.route("/", methods = ["POST", "GET"])
@login_required
def index():
    
    if request.method == "POST":
        search = request.form.get("search")
        data = db.execute("SELECT * FROM books WHERE title ILIKE :search OR author ILIKE :search OR isbn ILIKE :search", {"search": '%' + search + '%'}).fetchall()
        
        if data:
            return render_template('index.html', data=data)
        else:
            flash("Sorry No match was found for your search")
            return render_template('index.html', data=data)


    return render_template('index.html')


@app.route("/login/", methods = ["POST", "GET"])
def login():
    if request.method == "POST":
        form = request.form
        email = form["email"]
        password = form["password"]
        next_url = form["next"]
        user = db.execute("SELECT uid FROM users WHERE email = :email", {"email": email}).fetchone()
        if user:
            session["uid"] = user.uid
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
    session.pop("uid", None)

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
            flash('Username Already exists')
            return redirect(url_for('signup'))
    return render_template('signup.html')


@app.route("/book/<isbn>/", methods = ["GET", "POST"])
@login_required
def book_details(isbn):

    if request.method == "POST":
        review = request.form.get("review")
        rating = request.form.get("rating")
        uid = session["uid"]
        
        try:
            db.execute("INSERT INTO reviews (uid, isbn, review, rating) VALUES(:uid, :isbn, :review, :rating)", {"uid": uid, "isbn": isbn, "review": review, "rating": rating})
            db.commit()
        except exc.IntegrityError:
            flash('You have already revied this book')
            return redirect(url_for('book_details', isbn=isbn))

    reviews = db.execute("SELECT name, review, rating FROM users, reviews WHERE users.uid = reviews.uid AND reviews.isbn = :isbn ORDER BY reviews.review_date", {"isbn":isbn})
    details = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "e9hh8mpJf995M7SzMfst5A", "isbns": isbn}).json()

    for i in res['books']:
        gr_data = i

    return render_template("book_details.html", details=details, reviews=reviews, gr_data=gr_data)



@app.route("/api/<isbn>/", methods=['GET'])
def api(isbn):
    if request.method == 'GET':
        book = db.execute('SELECT * FROM books WHERE isbn = :isbn', {'isbn': isbn}).fetchone()

        if book:
            rating = db.execute("SELECT ROUND( AVG(rating), 2) FROM reviews WHERE isbn = :isbn", {'isbn':isbn}).fetchone()
            review = db.execute("SELECT COUNT(review) FROM reviews WHERE isbn = :isbn", {'isbn':isbn}).fetchone()

            for i in rating:
                if i:
                    avg_rating = float(i)
                else:
                    avg_rating = 0 

            
            for i in review:
                if i:
                    review_count = int(i)
                else:
                    review_count = 0 

            return make_response(jsonify({
                                        "title": book.title,
                                        "author": book.author,
                                        "year": book.year,
                                        "isbn": book.isbn,
                                        "review_count": review_count,
                                        "average_score": avg_rating,
                                        }))
        else:
            return abort(404)



@app.shell_context_processor
def make_shell_context():
    return {'db': db}

if __name__ == "__main__":
    app.debug = True
    app.run()