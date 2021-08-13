from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setupusers import Base, Bookstore, BookGenre, User
import requests
from requests.auth import HTTPBasicAuth
from werkzeug.exceptions import HTTPException
# testing


# for broken pipe
from signal import signal, SIGPIPE, SIG_DFL

# New imports for this security  anti-forgery state step
from flask import session as login_session
import random
import string
import os

# IMPORTS FOR GOOGLE SINGIN Connection
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from flask_login import (LoginManager, login_user,
                         logout_user, login_required,
                         current_user)


# -------------------------------------------------------------

app = Flask(__name__)

# Loading google signin API cliend-id
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "bookstore"


# Create session and Connect to DatabaseB
engine = create_engine(
    'sqlite:///book.db', connect_args={'check_same_thread': False})

Base.metadata.bind = engine

DBsession = sessionmaker(bind=engine)
session = DBsession()


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'showLogin'


@login_manager.user_loader
def load_user(userid):
    """
    This callback is used to reload the user object from the user ID
     stored in the session.
    """
    return session.query(User).filter_by(id=userid).one()


# -------------------------------------------------------------------------
# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # Return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)
  
  
  
# ------------------------------------------------------------------
# FACEBOOK Oauth login implementation
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
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
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"
# --------------------------------------------------------------------------------------------------------------------

# Create Google connection


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
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

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
            'Current user is already connected.'), 200)
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

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    output += ' -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session

@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        make_response(json.dumps('Disconnected.'), 200)
        redirect('/bookstores')
        flash("You have Successfully logged out")
        return redirect('/logout')

    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logoutpage():
    return render_template('logout.html')


# -----------------------------------------------------------------------------
# JSON APIs to view Books in Bookstore Information
@app.route('/bookstores/<int:bookstore_id>/books/JSON')
@app.route('/bookstores/<int:bookstore_id>/JSON')
def booksJSON(bookstore_id):
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    items = session.query(BookGenre).filter_by(bookstore_id=bookstore_id).all()
    return jsonify(BookGenre=[i.serialize for i in items])


# JSON APIs to wiew Bookstore information according to bookgenre catagory
@app.route('/bookstores/<int:bookstore_id>/books/<int:bookgenre_id>/JSON')
@app.route('/bookstores/<int:bookstore_id>/<int:bookgenre_id>/JSON')
def bookgenreItemJSON(bookstore_id, bookgenre_id):
    Bookgenre_Item = session.query(BookGenre).filter_by(id=bookgenre_id).one()
    return jsonify(Bookgenre_Item=Bookgenre_Item.serialize)


# JSON APIs to view Bookstore  Information
@app.route('/bookstores/JSON')
def bookstoreJSON():
    bookstores = session.query(Bookstore).all()
    return jsonify(bookstores=[r.serialize for r in bookstores])


# JSON APIs to view all BOOK Information
@app.route('/books/JSON')
def bookJSON():
    bookstores = session.query(BookGenre).all()
    return jsonify(bookstores=[r.serialize for r in bookstores])


# -------------------------------------------------------------------------

# Show all bookstores, home page, latest books, number of items


@app.route('/bookstores/')
@app.route('/')
def home():
    showbookstores = session.query(Bookstore).order_by(
        asc(Bookstore.name)).all()
    lastitems = session.query(BookGenre).order_by(
        BookGenre.id.desc()).limit(5).all()
    items = session.query(BookGenre).order_by(
        asc(BookGenre.title)).all()
    total = session.query(Bookstore).order_by(
        Bookstore.id).count()
    # return number bookstore
    totalbook = session.query(BookGenre).order_by(BookGenre.id).count()
    # return number of book item

    if 'username' not in login_session:
        return render_template(
            'publicbookstores.html', showbookstores=showbookstores,
            lastitems=lastitems, items=items, total=total, totalbook=totalbook)
    else:
        return render_template(
            'bookstores.html',
            showbookstores=showbookstores,
            lastitems=lastitems,
            items=items, total=total,
            totalbook=totalbook)


# CREATE new Bookstore


@app.route('/bookstores/new/', methods=['GET', 'POST'])
def newBookstore():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newBookstore = Bookstore(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(newBookstore)
        flash('New Bookstore %s Successfully Created' % newBookstore.name)
        session.commit()
        return redirect(url_for('home'))
    else:
        return render_template('newBookstore.html')


# EDIT a bookstore


@app.route('/bookstores/<int:bookstore_id>/edit/', methods=['GET', 'POST'])
def editBookstore(bookstore_id):
    editedBookstore = session.query(
        Bookstore).filter_by(id=bookstore_id).one()

    if 'username' not in login_session:
        return redirect('/login')
    if editedBookstore.user_id != login_session['user_id']:
        flash('You are not authorized to EDIT this %s' % editedBookstore.name)
        return redirect(url_for('home'))
    if request.method == 'POST':
        if request.form['name']:
            editedBookstore.name = request.form['name']
            flash('bookstore Successfully Edited %s' % editedBookstore.name)
            return redirect(url_for('home'))
    else:
        return render_template(
            'editBookstore.html', bookstore=editedBookstore)
    # return 'This page will be for editing bookstore %s' % bookstore_id


# DELETE a bookstore


@app.route('/bookstores/<int:bookstore_id>/delete/', methods=['GET', 'POST'])
def deleteBookstore(bookstore_id):

    bookstoreToDelete = session.query(
        Bookstore).filter_by(id=bookstore_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if bookstoreToDelete.user_id != login_session['user_id']:
        flash(
            'You are not authorized to DELETE \
                this %s' % bookstoreToDelete.name
            )
        return redirect(url_for('home'))

    if request.method == 'POST':
        session.delete(bookstoreToDelete)
        flash('%s Successfully Deleted' % bookstoreToDelete.name)
        session.commit()
        return redirect(
            url_for('home', bookstore_id=bookstore_id))
    else:
        return render_template(
            'deleteBookstore.html', bookstore=bookstoreToDelete)
    # return 'This page will be for deleting bookstore %s' % bookstore_id

# -----------------------------------------------------------------------
# Show books in Given Bookstore


@app.route('/bookstores/<int:bookstore_id>/books')
@app.route('/bookstores/<int:bookstore_id>/')
def showBooks(bookstore_id):
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    creator = getUserInfo(bookstore.user_id)
    items = session.query(BookGenre).filter_by(
        bookstore_id=bookstore_id).all() 
    total_items = session.query(BookGenre).filter_by(
        bookstore_id=bookstore_id).count()  # numberbook  in each bookstore

    if 'username' not in login_session \
            or creator.id != login_session['user_id']:
        return render_template(
                                'publicbooks.html',
                                bookstore=bookstore,
                                items=items, creator=creator,
                                bookstore_id=bookstore_id,
                                total_items=total_items)
    else:
        return render_template(
                                'books.html',
                                bookstore=bookstore,
                                items=items, creator=creator,
                                bookstore_id=bookstore_id,
                                total_items=total_items)


# Create a New Book (newbook item)


@app.route(
    '/bookstores/<int:bookstore_id>/books/new/', methods=['GET', 'POST'])
@app.route('/bookstores/<int:bookstore_id>/new/', methods=['GET', 'POST'])
def newBookItem(bookstore_id):
    if 'username' not in login_session:
        return redirect('/login')

    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    if login_session['user_id'] != bookstore.user_id:
        flash(
            'Sorry, You are not authorized to CREATE in  \
                this bookstore %s' % bookstore.name
            )
        return redirect(url_for('home'))
    if request.method == 'POST':
        newItem = BookGenre(
                            genre=request.form['genre'],
                            title=request.form['title'],
                            autor=request.form['autor'],
                            bookimage=request.form['bookimage'],
                            description=request.form['description'],
                            price=request.form['price'],
                            bookstore_id=bookstore_id,
                            user_id=bookstore.user_id)
        session.add(newItem)
        session.commit()
        flash('New Book  %s Item Successfully Created' % (newItem.title))
        return redirect(url_for('showBooks', bookstore_id=bookstore_id))
    else:
        return render_template('newBook.html', bookstore_id=bookstore_id)


# EDIT BOOK Function


@app.route('/bookstores/<int:bookstore_id>/<int:genre_id>/edit/', methods=[
            'GET', 'POST'])
def editBookItem(bookstore_id, genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(BookGenre).filter_by(id=genre_id).one()
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    if login_session['user_id'] != bookstore.user_id:
        flash(
            'Sorry, You are not authorized to EDIT this item   \
                in this bookstore %s' % bookstore.name
            )
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form['genre']:
            editedItem.genre = request.form['genre']
        if request.form['title']:
            editedItem.title = request.form['title']
        if request.form['autor']:
            editedItem.autor = request.form['autor']
        if request.form['bookimage']:
            editedItem.bookimage = request.form['bookimage']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        session.add(editedItem)
        session.commit()
        flash('sellected book  %s Successfully EDITED' % editedItem.title)
        return redirect(url_for(
                                'showBooks',
                                bookstore_id=bookstore_id,
                                genre_id=genre_id))
    else:
        return render_template(
                                'editbookitem.html',
                                bookstore_id=bookstore_id,
                                genre_id=genre_id,
                                item=editedItem)


# Delete Book function here


@app.route('/bookstores/<int:bookstore_id>/<int:genre_id>/delete/', methods=[
            'GET', 'POST'])
def deleteBookItem(bookstore_id, genre_id):
    if 'username' not in login_session:
        return redirect('/login')
    bookstore = session.query(Bookstore).filter_by(id=bookstore_id).one()
    itemToDelete = session.query(BookGenre).filter_by(id=genre_id).one()
    if login_session['user_id'] != bookstore.user_id:
        flash(
            'Sorry, You are not authorized to DELETE this item \
                in this bookstore %s' % bookstore.name
            )
        return redirect(url_for('home'))

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('%s Successfully Deleted' % itemToDelete.title)
        return redirect(url_for('showBooks', bookstore_id=bookstore_id))
    else:
        return render_template('deletebookitem.html', item=itemToDelete)


@app.route('/cookie/')
def cookie():
    if not request.cookies.get('foo'):
        res = make_response("Setting a cookie")
        res.set_cookie('foo', 'bar', max_age=60*60*24*365*2)
    else:
        res = make_response(
            "Value of cookie foo is {}".format(request.cookies.get('foo')))
    return res


@app.errorhandler(Exception)
def handle_exception(e):
    # pass through HTTP errors
    if isinstance(e, HTTPException):
        return e

    # now you're handling non-HTTP exceptions only
    return render_template("500_generic.html", e=e), 500

# app name 
@app.errorhandler(404) 
  
# inbuilt function which takes error as parameter 
def not_found(e): 
  
# defining function 
  return render_template("404.html") 


# Running port at 50000
if __name__ == '__main__':
    app.secret_key = 'secret key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
