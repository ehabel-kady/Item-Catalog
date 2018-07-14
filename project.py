from flask import Flask, render_template, request, redirect, jsonify, url_for
from flask import flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item catalog"
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
# def create_user(login_session):
#     nuser = User(name=login_session['username'], email=login_session[
#         'email'])
#     session.add(nuser)
#     session.commit()
#     user = session.query(User).filter_by(email=login_session['email']).one()
#     return user.id


# def get_user_info(user_id):
#     user = session.query(User).filter_by(id=user_id).one()
#     return user


# def get_user_id(u_email):
#     try:
#         user = session.query(User).filter_by(email=u_email).one()
#         return user.id
#     except:
#         return None

@app.route('/login/')
def login_s():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


# Used to create user and stored in Users table on login
def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    creted_user_id = session.query(User).filter_by(
        email=login_session['email']).one()
    return creted_user_id.id


# Returns object of type User
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Returns user id if email existed in users table
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']        # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('Display_categories'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout/')
def logout():
    if 'username' in login_session:
        gdisconnect()
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        return redirect(url_for("Display_categories"))
    else:
        return redirect(url_for("login_s"))

@app.route('/catalog/JSON')
def catjson():
    cats = session.query(Categories).all()
    return jsonify(Category= [i.serialize for i in cats])


@app.route('/catalog/<cat_name>/JSON')
def itemsjson(cat_name):
    cat = session.query(Categories).filter_by(name=cat_name).one()
    items = session.query(Items).filter_by(cat_id=cat.id).all()
    return jsonify(Items= [i.serialize for i in items])


@app.route('/')
@app.route('/catalog/')
def Display_categories():
    categories = session.query(Categories).order_by(asc(Categories.name))
    # if 'username' not in login_session:
    # return render_template('publiccategories.html', categories=categories)
    # else:
    return render_template('categories.html', categories=categories)


@app.route('/catalog/new/', methods=['GET', 'POST'])
def Add_category():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newcategory = Categories(name=request.form['name'])
        session.add(newcategory)
        flash('New Category %s Successfully Created' % newcategory.name)
        session.commit()
        return redirect(url_for('Display_categories'))
    else:
        return render_template('newcategory.html')


@app.route('/catalog/<cat_name>/')
@app.route('/catalog/<cat_name>/items/')
def Display_Items(cat_name):
    category = session.query(Categories).filter_by(name=cat_name).one()
    items = session.query(Items).filter_by(cat_id=category.id).all()
    return render_template('items.html', category=category, items=items)


@app.route('/catalog/<cat_name>/items/new/', methods=['GET', 'POST'])
def Add_item(cat_name):
    if 'username' not in login_session:
        return redirect('/login')
    categories = session.query(Categories).order_by(asc(Categories.name))
    cat = session.query(Categories).filter_by(name=cat_name).one()
    # if login_session['user_id'] != cat.user_id:
    #  return "<script>function myFunction() {alert('You are not authorized'+
    # ' to delete menu items to this restaurant. Please create your own'+
    # ' restaurantin order to delete items.');}</script>"

    if request.method == 'POST':
        newitem = Items(
            name=request.form['name'],
            description=request.form['description'], cat_id=cat.id
            )
        session.add(newitem)
        session.commit()
        return redirect(url_for('Display_Items', cat_name=cat_name))
    else:
        return render_template('additem.html', cat=cat)


@app.route('/catalog/<cat_name>/items/<item_name>/')
def Display_Item(cat_name, item_name):
    category = session.query(Categories).filter_by(name=cat_name).one()
    items = session.query()
    return render_template('showitem.html', item=items, category=category)


@app.route(
    '/catalog/<cat_name>/items/<item_name>/edit/',
    methods=['GET', 'POST']
    )
def Edit_item(cat_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Items).filter_by(name=item_name).all()
    categories = session.query(Categories).order_by(asc(Categories.name))
    category = session.query(Categories).filter_by(name=cat_name).one()
    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() +{alert('You are not authorized"
        " to delete menu items to this restaurant. Please create your own"
        " restaurant in order to delete items.');}"
        "</script><body onload='myFunction()''>"

    if request.method == 'POST':
        item.name = request.form['name']
        item.description = request.form['description']
        session.add(item)
        session.commit()
        flash('Item Successfully Edited')
        return redirect(url_for('Display_Item', cat_name=cat_name,
                        item_name=request.form['name']))
    else:
        return render_template('edititem.html', category=category, item=item)


@app.route(
    '/catalog/<cat_name>/items/<item_name>/delete/',
    methods=['GET', 'POST']
    )
def Delete_item(cat_name, item_name):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Categories).filter_by(name=cat_name).one()
    item = session.query(Items).filter_by(name=item_name).one()
    if login_session['user_id'] != item.user_id:
        return "<script>function myFunction() +{alert('You are not authorized"
        " to delete menu items to this restaurant. Please create your own"
        " restaurant in order to delete items.');}"
        "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('Display_Items', cat_name=category.name))
    else:
        return render_template('deleteitem.html', item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
