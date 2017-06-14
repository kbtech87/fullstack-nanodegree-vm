from flask import Flask, render_template, request, redirect, url_for, jsonify
from database_setup import Base, Categories, Items, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

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
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri ='postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
                    'Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
            % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET') [1])
    # if there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    # verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps(
                    "Token's user id doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected')
            , 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    #store the access token in the session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    #get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data =  json.loads(answer.text) #or data = answer.json() ??

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    #see if user exists, if not make a new one
    user_id = getUserId(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    #flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

#disconnect - revoke current token and reset login_session
@app.route('/gdisconnect')
def gdisconnect():
    #only disconnect a connected user
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #execute http get request to revoke current token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        #reset user's session
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        #the given token was Invalid
        response = make_response(json.dumps('Failed to revoke token.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

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
    creator = getUserInfo(categories.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template('publicitems.html', category=category,
        items=items, category_id=category_id, creator=creator)
    else:
        return render_template(
            'itemlist.html', category=category, items=items,
            category_id=category_id)

@app.route('/categories/<int:category_id>/new', methods=['GET', 'POST'])
def newItem(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Items(name= request.form['name'], category_id=category_id,
        user_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(url_for('itemList', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)

@app.route('/categories/<int:category_id>/<int:item_id>/edit',
methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
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
    if 'username' not in login_session:
        return redirect('/login')
    deletedItem = session.query(Items).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.remove(deletedItem)
        session.commit()
        return redirect(url_for('itemList', category_id=category_id))
    else:
        return render_template('deleteitem.html', category_id=category_id,
        item_id=item_id, i=deletedItem)

def createUser(login_session):
    newUser = User(name = login_session['username'], email =
    login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def getUserId(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

app.secret_key = 'O5OAxAriVKSrSYUKGACVW443'



if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
    app.secret_key = 'O5OAxAriVKSrSYUKGACVW443'
