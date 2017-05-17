from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_setup import Base, Categories, Items
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
import random, string


app = Flask(__name__)

#Create session and connect to db
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
            for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html')

@app.route('/categories/<int:category_id>/items/JSON')
def itemListJSON(category_id):
    category = session.query(Categories).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])

@app.route('/categories/<int:category_id>/<int:item_id>/JSON')
def itemJSON(category_id, item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    return jsonify(Items = item.serialize)

@app.route('/')
def homepage():
    categories = session.query(Categories).all()
    print "categories:", categories
    return render_template('homepage.html', categories=categories)

@app.route('/categories/<int:category_id>/items')
def itemList(category_id):
    category = session.query(Categories).filter_by(id=category_id).one()
    items = session.query(Items).filter_by(category_id=category_id).all()
    return render_template(
        'itemlist.html', category=category, items=items,
        category_id=category_id)

@app.route('/categories/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    if request.method == 'POST':
        newItem = Items(name= request.form['name'], category_id=category_id)
        session.add(newItem)
        session.commit()
        return redirect(url_for('itemList', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)

@app.route('/categories/<int:category_id>/<int:item_id>/edit',
methods=['GET', 'POST'])
def editItem(category_id, item_id):
    editedItem = session.query(Items).filter_by(id=item_id).one()
    if request.method =='POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('itemList', category_id=category_id))
    else:
        return render_template('edititem.html', category_id=category_id,
        item_id=item_id, i=editedItem)

@app.route('/categories/<int:category_id>/<int:item_id>/delete',
methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    deletedItem = session.query(Items).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.remove(deletedItem)
        session.commit()
        return redirect(url_for('itemList', category_id=category_id))
    else:
        return render_template('deleteitem.html', category_id=category_id,
        item_id=item_id, i=deletedItem)




if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
