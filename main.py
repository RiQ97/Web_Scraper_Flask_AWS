import os
from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import pymongo
import ssl

load_dotenv()

app = Flask(__name__) # initializing a flask app
CORS(app)

@app.route('/', methods=['GET'])
@cross_origin()
def home_page():
    return render_template("index.html")

@app.route('/review', methods=['POST', 'GET'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            query = request.form['content'].strip().replace(" ", "")
            flipkart_url = f"https://www.flipkart.com/search?q={query}"
            context = ssl._create_unverified_context()
            flipkart_page = urlopen(flipkart_url, context=context).read()

            soup = bs(flipkart_page, "html.parser") #beautifies the output
            product_boxes = soup.findAll("div", {"class": "cPHDOP col-12-12"})[3:] #Updated
            
            if not product_boxes:
                return render_template('index.html', message="No products found!")

            product_link = "https://www.flipkart.com" + product_boxes[0].div.div.div.a['href']
            product_page = requests.get(product_link).text
            product_soup = bs(product_page, "html.parser")
            reviews_html = product_soup.find_all('div', {'class': "col EPCmJX"}) #Updated

            csvfile = query + ".csv"
            f = open(csvfile, 'w', newline='', encoding='utf-8')
            header = "Product, Customer Name, Rating, Heading, Comment \n"
            f.write(header)
            reviews = []
            for review in reviews_html:
                name = review.find('p', {'class': '_2NsDsF AwS1CA'}) #Updated
                rating = review.find('div', {'class': 'XQDdHH Ga3i8K'}) #Updated
                comment_head = review.find('p', {'class': 'z9E0IG'}) #Updated
                comment_body = review.find('div', {'class': 'ZmyHeo'}) #Updated

                review_data = {
                    "Product": query,
                    "Name": name.text if name else "No Name",
                    "Rating": rating.text if rating else "No Rating",
                    "CommentHead": comment_head.text if comment_head else "No Comment Heading",
                    "Comment": comment_body.div.text if comment_body else "No Comment"
                }
                reviews.append(review_data)
                f.write(f"{review_data['Product']}, {review_data['Name']}, {review_data['Rating']}, {review_data['CommentHead']}, {review_data['Comment']}\n")
            f.close()
            if reviews:
                mongo_uri = os.getenv('MONGO_URI')
                client = pymongo.MongoClient(mongo_uri)
                db = client['review_scrap']
                review_collection = db['review_scrap_data']
                review_collection.insert_many(reviews)

            return render_template('results.html', reviews=reviews[:len(reviews)])
        except Exception as e:
            print('The Exception message is:', e)
            return 'Something went wrong'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)

#create a .env file in the root directory & add ur mongodb url 
# MONGO_URI=<ur url>