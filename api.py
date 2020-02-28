import requests

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "e9hh8mpJf995M7SzMfst5A", "isbns": "9781632168146"})

data = res.json()

# print(data['books']['isbn'])