import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
dbs = "postgres://fabeidpsjarnlm:080cd5f8a5a7ce8dd8d6c71863c76924e7a26ebcab39588e6dc637a1741bf496@ec2-3-234-109-123.compute-1.amazonaws.com:5432/de693jkmt9rih3"

# Set up database
engine = create_engine(dbs)
db = scoped_session(sessionmaker(bind=engine))


f = open("books.csv")
reader = csv.reader(f)
for isbn, title, author, year in reader: # loop gives each column a name
    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
    {"isbn": isbn, "title": title, "author": author, "year": year}) # substitute values from CSV line int
    print(f"Added book  {title} by {author} published {year}.")
db.commit() # transactions are assumed, so close the transaction finished