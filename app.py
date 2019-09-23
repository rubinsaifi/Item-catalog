#!/usr/bin/env python3

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import flash, make_response
from flask import session as login_session
from flask import Flask, render_template, request, redirect, jsonify, url_for

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import httplib2
import random
import string
import json
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

# DB handler code
engine = create_engine(
    'sqlite:///catalog.db',
    connect_args={
        'check_same_thread': False
    }
)

# Bind engine to a session.
Session = sessionmaker(bind=engine)

# Create a Session object.
session = Session()

# end of db handler code

# Redirect to login page.
@app.route('/')
@app.route('/catalog/')
@app.route('/catalog/items/')
def home():
    """Landing Page"""

    categories = session.query(Category).all()
    items = session.query(Item).all()
    return render_template(
        'index.html', categories=categories, items=items)

# login endpoint
@app.route('/login/')
def login():
    """login route"""

    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template("login.html", STATE=state, client_id=CLIENT_ID)


# Connect to Google Sign-in OAuth method.
@app.route('/gconnect', methods=['POST'])
def gconnect():

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)

    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)

        response.headers['Content-Type'] = 'application/json'

        return response

    # Check if access token is valid or not
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If error - return
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token usage.
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    # Verify access token application validity
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match with application."), 401)
        print("Token's client ID mismatch with application")

        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store token in the session
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # user info.
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {
        'access_token': credentials.access_token,
        'alt': 'json'
    }
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    if "name" in data:
        login_session['username'] = data['name']
    else:
        temp_name = data['email'][:data['email'].find("@")]
        login_session['username'] = temp_name

    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists, if not then create it 
    user_id = get_user_id(data["email"])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    # Welcome msg
    output = ''
    output += '<h2>Welcome, '
    output += login_session['username']
    output += '!</h2>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; '
    output += 'border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;">'
    flash("You are now logged in as %s!" % login_session['username'])

    print("Login Successfull!!")
    return output


# Disconnect Google Login
def gdisconnect():
    """Disconnect Google logged-in user"""

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
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'

        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'

        return response


# Log out user.
@app.route('/logout')
def logout():
    """Log out user"""

    if 'username' in login_session:
        gdisconnect()
        del login_session['email']
        del login_session['access_token']
        del login_session['picture']
        del login_session['user_id']
        del login_session['google_id']
        del login_session['username']

        flash("You have been successfully logged out!")
        return redirect(url_for('home'))
    else:
        flash("You were not logged in!")
        return redirect(url_for('home'))


# Create new user
def create_user(login_session):
    """Crate new user"""

    new_user = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture']
    )

    session.add(new_user)
    session.commit()

    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_info(user_id):
    """Get user info"""

    user = session.query(User).filter_by(id=user_id).one()
    return user


def get_user_id(email):
    """Get user by email id"""

    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# Add a new category.
@app.route("/catalog/category/new/", methods=['GET', 'POST'])
def add_category():
    """Add a new category"""

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    elif request.method == 'POST':
        if request.form['new-category-name'] == '':
            flash('The field cannot be empty.')
            return redirect(url_for('home'))

        category = session.query(Category).\
            filter_by(name=request.form['new-category-name']).first()
        if category is not None:
            flash('Entered category already exists.')
            return redirect(url_for('add_category'))

        new_category = Category(
            name=request.form['new-category-name'],
            user_id=login_session['user_id'])
        session.add(new_category)
        session.commit()
        flash('New Category %s created!' % new_category.name)
        return redirect(url_for('home'))
    else:
        return render_template('new-category.html')


# Create new item
@app.route("/catalog/item/new/", methods=['GET', 'POST'])
def add_item():
    """Create a new item"""

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))
    elif request.method == 'POST':
        item = session.query(Item).filter_by(name=request.form['name']).first()
        if item:
            if item.name == request.form['name']:
                flash('The item already exists in the database!')
                return redirect(url_for("add_item"))

        new_item = Item(
            name=request.form['name'],
            category_id=request.form['category'],
            description=request.form['description'],
            user_id=login_session['user_id']
        )

        session.add(new_item)
        session.commit()

        flash('New item successfully created!')
        return redirect(url_for('home'))

    else:
        items = session.query(Item).\
                filter_by(user_id=login_session['user_id']).all()

        categories = session.query(Category).\
            filter_by(user_id=login_session['user_id']).all()

        return render_template(
            'new-item.html',
            items=items,
            categories=categories
        )


# Create item by Category ID
@app.route("/catalog/category/<int:category_id>/item/new/", methods=['GET', 'POST'])
def add_item_by_category(category_id):
    """Create item by Category ID"""

    if 'username' not in login_session:
        flash("You were not authorised to access that page.")
        return redirect(url_for('login'))

    elif request.method == 'POST':
        # Check if the item already exists
        item = session.query(Item).filter_by(name=request.form['name']).first()

        if item:
            if item.name == request.form['name']:
                flash('Item already exists in the database')
                return redirect(url_for("add_item"))

        new_item = Item(
            name=request.form['name'],
            category_id=category_id,
            description=request.form['description'],
            user_id=login_session['user_id'])

        session.add(new_item)
        session.commit()

        flash('New item successfully created!')
        return redirect(
            url_for(
                'show_items_in_category',
                category_id=category_id
            )
        )

    else:
        category = session.query(Category).filter_by(id=category_id).first()
        return render_template('new-item-2.html', category=category)


# Check if item exists
def exists_item(item_id):
    """Check if item exists"""

    item = session.query(Item).filter_by(id=item_id).first()
    if item is not None:
        return True
    else:
        return False


# Check if the category exists
def exists_category(category_id):
    """Check if category existsthe database"""

    category = session.query(Category).filter_by(id=category_id).first()
    if category is not None:
        return True
    else:
        return False


# View item by ID
@app.route('/catalog/item/<int:item_id>/')
def view_item(item_id):
    """View item by ID"""

    if exists_item(item_id):
        item = session.query(Item).filter_by(id=item_id).first()
        category = session.query(Category)\
            .filter_by(id=item.category_id).first()

        owner = session.query(User).filter_by(id=item.user_id).first()

        return render_template(
            "view-item.html",
            item=item,
            category=category,
            owner=owner
        )

    else:
        flash('We are unable to process your request right now.')
        return redirect(url_for('home'))


# Edit existing item
@app.route("/catalog/item/<int:item_id>/edit/", methods=['GET', 'POST'])
def edit_item(item_id):
    """Edit existing item"""

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))

    if not exists_item(item_id):
        flash("Unable to process request")
        return redirect(url_for('home'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("Not Authorised to access this page.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form['name']:
            item.name = request.form['name']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['category']:
            item.category_id = request.form['category']

        session.add(item)
        session.commit()

        flash('Item successfully updated!')
        return redirect(url_for('edit_item', item_id=item_id))

    else:
        categories = session.query(Category).\
            filter_by(user_id=login_session['user_id']).all()

        return render_template(
            'update-item.html',
            item=item,
            categories=categories
        )


# Delete existing item
@app.route("/catalog/item/<int:item_id>/delete/", methods=['GET', 'POST'])
def delete_item(item_id):
    """Delete existing item"""

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))

    if not exists_item(item_id):
        flash("Unable to process request!")
        return redirect(url_for('home'))

    item = session.query(Item).filter_by(id=item_id).first()
    if login_session['user_id'] != item.user_id:
        flash("Not Authorised to access this page.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        session.delete(item)
        session.commit()

        flash("Item deleted!")
        return redirect(url_for('home'))

    else:
        return render_template('delete.html', item=item)


# Show items in particular category.
@app.route('/catalog/category/<int:category_id>/items/')
def show_items_in_category(category_id):
    """# Show items in particular category."""

    if not exists_category(category_id):
        flash("Unaable to process request!")
        return redirect(url_for('home'))

    category = session.query(Category).filter_by(id=category_id).first()
    items = session.query(Item).filter_by(category_id=category.id).all()
    total = session.query(Item).filter_by(category_id=category.id).count()

    return render_template(
        'items.html',
        category=category,
        items=items,
        total=total)


# Edit exiting category
@app.route('/catalog/category/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    """Edit existing category"""

    category = session.query(Category).filter_by(id=category_id).first()

    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))

    if not exists_category(category_id):
        flash("Unable to process request!")
        return redirect(url_for('home'))

    if login_session['user_id'] != category.user_id:
        flash("Unable to process request!")
        return redirect(url_for('home'))

    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            session.add(category)
            session.commit()
            flash('Category updated!')
            return redirect(
                url_for(
                    'show_items_in_category',
                    category_id=category.id
                )
            )

    else:
        return render_template('edit_category.html', category=category)


# Delete category
@app.route('/catalog/category/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    """Delete category"""

    category = session.query(Category).filter_by(id=category_id).first()
    if 'username' not in login_session:
        flash("Please log in to continue.")
        return redirect(url_for('login'))

    if not exists_category(category_id):
        flash("Unable to process request!")
        return redirect(url_for('home'))

    if login_session['user_id'] != category.user_id:
        flash("Unable to process request!")
        return redirect(url_for('home'))

    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash("Category deleted!")
        return redirect(url_for('home'))
    else:
        return render_template("delete_category.html", category=category)


# JSON Endpoints

@app.route('/api/v1/catalog.json')
def show_catalog_json():
    """Return items as JSON"""

    items = session.query(Item).order_by(Item.id.desc())
    return jsonify(catalog=[i.serialize for i in items])


# Return particular item
@app.route('/api/v1/categories/<int:category_id>/item/<int:item_id>/JSON')
def catalog_item_json(category_id, item_id):
    """Return particular item"""

    if exists_category(category_id) and exists_item(item_id):
        item = session.query(Item)\
               .filter_by(id=item_id, category_id=category_id).first()
        if item is not None:
            return jsonify(item=item.serialize)
        else:
            return jsonify(
                error='Ttem {} does not belong to category {}.'
                .format(item_id, category_id))
    else:
        return jsonify(error='Item or Category does not exist!')


# Return categories
@app.route('/api/v1/categories/JSON')
def categories_json():
    """Return categories"""

    categories = session.query(Category).all()
    return jsonify(categories=[i.serialize for i in categories])


if __name__ == "__main__":
    print('Starting Application')
    app.secret_key = b'$pV4BVvmVZaM9*CV2WD#RYcjH#-k*LaqVCy7-mP4F!n!PRRdZs++cMdt7eg!T6pBH!#LbaWCsR%KYg!gWPYZBBG%-Utf#AhbucW5'
    app.run(host="0.0.0.0", port=5000, debug=True)

