# Coding started for the new web project.


from sqlite3 import dbapi2 as sq
from flask import Flask, request, session, url_for, redirect, render_template, \
     g, flash, _app_ctx_stack


DATABASE = '.\\tmp\\web.db'
PER_PAGE = 30
DEBUG = True
SECRET_KEY = b'hello python'

# create application

app = Flask('web')
app.config.from_object(__name__)
app.config.from_envvar('WEB_SETTINGS', silent=True)


def get_db():
    """ Opens a new database connection if there is none yet"""

    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        top.sqlite_db = sq.connect(app.config['DATABASE'])
        top.sqlite_db.row_factory = sq.Row
    return top.sqlite_db


@app.teardown_appcontext
def close_database(exception):
    """ closes the database """
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()


def init_db():
    """ Initializes the database. """

    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.before_request
def before_request():
    g.user = None
    if 'shop_id' in session:
        print ('check')
        g.user = query_db('select * from shops where shop_id = ?',
                          [session['shop_id']], one=True)

@app.cli.command('initdb')
def initdb_command():
    """ creates the database tables."""
    init_db()
    print("initialized the database")


def query_db(query, args=(), one=False):
    """ Queries the database"""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


def get_user_id(shop_name):
    rv = query_db('select shop_id from shops where shop_name = ?', [shop_name], one=True)

    return rv[0] if rv else None


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if  g.user:
        return redirect(url_for('shop_view'))
    error = None
    if request.method == 'POST':

        user = query_db('''select * from shops where
            shop_name = ?''', [request.form['shop_name']], one=True)
        session['shop_id'] = user['shop_id']

        if user is None:

            error = 'Invalid shop_name'
        elif not user['password']==request.form['password']:
            error = 'Invalid type'

        else:
            print ( 'reached')
            flash('You were logged in')
            session['shop_id'] = user['shop_id']
            return redirect(url_for('shop_view'))
    return render_template('login.html', error=error)

@app.route('/shop_login', methods=['GET', 'POST'])
def shop_view():
        if not g.user:
            return redirect(url_for('login'))
        user = query_db('select * from shops where shop_id = ?', [session['shop_id']], one=True)

        q = '''select * from ''' + user['shop_name']
        item_list = query_db(q)

        if user is not None:

            north = user['north']
            east = user['east']

        if request.method == 'POST':

            flash("Shop Name:" + user['shop_name'])
            flash("Shop Type:" + user['type'])
            db = get_db()

            sql='''insert into ''' + user['shop_name'] + '''( name, type, price) values (?, ?, ?)'''
            db.execute(sql,
                       [request.form['name'], request.form['type'],
                        request.form['price']])
            db.commit()

            flash("item added")


            return  redirect(url_for('shop_view'))
        return render_template('shop_view.html', shop_name=user['shop_name'], type=user['type'], item_list=item_list)





@app.route('/',methods=['GET', 'POST'])
def homepage():
    """Registers the user."""
    check = None

    if request.method == 'POST':

        user = query_db('''select * from shops where
            shop_name = ?''', [request.form['search']], one=True)
        shop_list = query_db('''select shop_name from shops''')


        if shop_list is not None:
            for list in shop_list:

                sql = '''select * from '''+ list['shop_name']+ ''' where name = ? or type = ?'''
                data=query_db(sql,[request.form['search'], request.form['search']], one= True)
                if data is not None:
                    flash(data['name']+'     '+data['type']+'         '+str(data['price']))

        if user is None:
            check = 'Invalid shop_name'
        else:

            n=str(user['north'])
            e=str(user['east'])

            print (user['shop_id'])
            flash("shop_id :"+ str(user['shop_id']))
            flash("shop_name :"+user['shop_name'])
            flash("Type :"+user['type'])
            flash("Location :")
            session['shop_id']=user['shop_id']
            return redirect(url_for('homepage'))
    return render_template('homepage.html', error=check)



@app.route('/register/shop', methods=['GET', 'POST'])
def register_shop():
    """Registers the user."""
    if g.user:
        return redirect(url_for('homepage'))
    error = None
    if request.method == 'POST':
        if not request.form['shop_name']:
            error = 'You have to enter a shop_name'
        elif not request.form['type']:
            error = 'You have to enter a valid type'
        elif not request.form['north']:
            error = 'You have to enter a north'
        elif not request.form['east']:
            error = 'The east not added'
        elif get_user_id(request.form['shop_name']) is not None:
            error = 'The shop_name is already taken'
        else:
            db = get_db()
            db.execute('''insert into shops (
              shop_name, type, north, east, password) values (?, ?, ?, ?, ?)''',
                       [request.form['shop_name'], request.form['type'],
                        request.form['north'], request.form['east'], request.form['password']])
            db.commit()

            sql = '''CREATE TABLE
                                    IF NOT EXISTS ''' + str(request.form['shop_name']) + ''' (
                                    id integer PRIMARY KEY autoincrement,
                                    name text NOT NULL,
                                    type text,
                                    price integer
                                    review integer);'''
            k = query_db(sql)


            flash('You were successfully registered shops')
            return redirect(url_for('login'))
    return render_template('register.html', error=error)


@app.route('/location')
def map():
    print(session['shop_id'])
    user = query_db('''select * from shops where
                shop_id = ?''', [session['shop_id']], one=True)

    north=user['north']
    east=user['east']
    return render_template('map.html', north=north, east= east)


@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('shop_id', None)
    return redirect(url_for('login'))


if __name__=="__main__":
    app.run(host="0.0.0.0", port=33)
