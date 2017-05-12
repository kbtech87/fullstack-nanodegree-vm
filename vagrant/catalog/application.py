from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_setup import Base, Categories, Items
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

#Create session and connect to db
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/')
def homepage():
    category = session.query(Categories).all()
    return render_template('homepage.html', category=category)

#@app.route('/categories/<int:category_id>/items')
#def categoryList(category_id):
#    category = session.query(Categories).filter_by(id=category_id).one()
#    items = session.query(Items).filter_by(category_id=category_id)
#    return render_template(
#        'itemlist.html', category=category, items=items, category_id=category_id)





if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
