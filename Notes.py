from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'billa007'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MYSQL
mysql = MySQL(app)
# Articles = Articles()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    # create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        render_template('articles.html', msg=msg)

    # close connecction
    cur.close()


@app.route('/article/<string:id>')
def article(id):
    # create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("select * from articles where id=%s", [id])

    article = cur.fetchone()


    return render_template('article.html', article = article )

class RegisterForm(Form):
    name = StringField('Name', [validators.length(min=1, max=50)])
    username = StringField('Username',[validators.length(min=4, max=25)])
    email = StringField('Email', [validators.length(min=6,max=50)])
    password = PasswordField('Password',[validators.DataRequired(), validators.equal_to('confirm',message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # create Cursor
        cur = mysql.connection.cursor()

        # execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name,email,username,password))

        # COMMIT TO db
        mysql.connection.commit()

        # close connection
        cur.close()

        flash('You are now registered and can login','success')
        return redirect(url_for('index'))

        return render_template('register.html', form = form)
    return render_template('register.html', form = form)


# check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Un-Authorized, Please Login', 'danger')
            return redirect(url_for('login'))
    return wrap

# User Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("select * from users where username = %s ", [username])

        if result > 0:
            data = cur.fetchone()
            password = data['password']

            # compare password
            if sha256_crypt.verify(password_candidate, password):
                # passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are Logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error = error)
            # close connection
            cur.close()
        else:
            error = 'Username not Found'
            return render_template('login.html', error = error)

    return render_template('login.html')

#dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("select * from articles")

    articles = cur.fetchall()

    if result>0:
        return render_template('dashboard.html', articles = articles)
    else:
        msg = 'No Articles Found'
        render_template('dashboard.html', msg=msg)

    #close connecction
    cur.close()



#article form class
class ArticleForm(Form):
    title = StringField('Title', [validators.length(min=1, max=200)])
    body = TextAreaField('Body',[validators.length(min=30)])

# add article
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method =='POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("insert into articles (title,body,author) values(%s,%s,%s)",(title,body,session['username']))

        #commit to db
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)



# edit article
@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # create cursor
    cur = mysql.connection.cursor()

    #get article by id
    result = cur.execute("select * from articles where id = %s",[id])

    article = cur.fetchone()

    #get form
    form = ArticleForm(request.form)

    # populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']


    if request.method =='POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("update articles set title  = %s , body = %s where id = %s", ( title ,body, id) )

        #commit to db
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)


#delete Article
@app.route('/delete_article/<string:id>', methods = ['post'])
@is_logged_in
def delete_article(id):
    cur = mysql.connection.cursor()

    cur.execute("delete from articles where id=%s",[id])

    # commit to db
    mysql.connection.commit()

    # close connection
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


# logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
