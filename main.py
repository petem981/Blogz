from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://Blogz:password@localhost:8889/Blogz"
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'random'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, user):
        self.title = title
        self.body = body
        self.user = user
        
    def __repr__(self):
        return '<Blog %r>' % self.title

class User(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='user')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


@app.before_request
def require_login():
    allowed_routes = ['login', 'blog', 'signup', 'index']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/blog', methods=['GET', 'POST'])
def blog():

    if request.method == 'GET':
        if 'user' in request.args:
            user_id = request.args.get('user')
            user = User.query.get(user_id)
            posts = Blog.query.filter_by(owner_id=user_id).all()
            return render_template('singleUser.html', username=user.username, posts=posts)
            #render blogs, but filter "posts" by user_id
        
        if 'id' in request.args:
            blog_id = request.args.get('id')
            blog = Blog.query.get(blog_id)
            user = User.query.get(blog.owner_id)
            return render_template('posts.html', title=blog.title, body=blog.body, user=user)
        
        else:
            posts = Blog.query.all()
            return render_template('blogs.html', title="Blogzzz!", posts=posts)
    if request.method == 'POST':
        title_error = ''    
        body_error = ''
        blog_title = request.form['title']
        blog_body = request.form['body']
        
@app.route('/newpost', methods=['GET', 'POST'])
def new_post():
    
    username = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'GET':
        title = request.args.get('title')
        body = request.args.get('body')
        title_error = request.args.get('title_error')
        body_error = request.args.get('body_error')
        if title_error == None and body_error == None:
            return render_template('newpost.html')
        if title_error == None:
            return render_template('newpost.html', body_error=body_error, title=title)
        if body_error == None:
            return render_template('newpost.html', title_error=title_error, body=body)
        
    if request.method == 'POST':
        blog_title = request.form['title']
        blog_body = request.form['body']
        title_error = ''
        body_error = ''
        if blog_title == '':
            title_error = "Call me boring or old fashioned, but you need to title your blog!"
        if blog_body == '':
            body_error = "Share something boring. That's what this is for."
        if title_error or body_error:    
            return render_template('newpost.html', title_error=title_error, blog_title=blog_title, body_error=body_error, blog_body=blog_body)
        new_blog = Blog(blog_title, blog_body, username)
        db.session.add(new_blog)
        db.session.commit()
        blog = Blog.query.filter_by(title=blog_title).first()
        blog_id = str(blog.id)
        return redirect('/blog?id=' + blog_id)            

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        #makes sure needed variables have values
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        user_error = ''
        pw_error = ''
        ver_error = ''
        divert = False
        #performs validation for username, password for signup
        if username.isalpha() == False:
            divert=True
            flash("Username can only be from the alphabet, no numbers.", "error")
        if len(username) < 3:
            divert=True
            flash("Username has to be longer than 3 letters.", "error")
        if username == '':
            divert=True            
            flash("What do you want your username to be?", "error")
        if len(password) < 3 or len(password) > 20 or " " in password:
            divert=True
            flash("Password must be between 3-20 characters with no spaces.", "error")
        if password == '':
            divert=True
            flash("Please enter a Password!", "error")
        if password != verify:
            divert=True
            flash("Ruh-Roh! Those passwords didn't match.", "error")
        if verify == '':
            divert=True
            flash("RE-Type the same password here silly goose.", "error")
        if divert: #if any error exists, have them try to sign up again.
            #how to not say "logged in as __" if no username
            return render_template('signup.html')
        
        
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')
        else:
            flash('User already exists', 'error')
            return render_template('signup.html')
    return render_template('signup.html')



@app.route('/login', methods=['POST', 'GET'])
def login():    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username = username).first()
        if user:
            if user.password == password:
                session['username'] = username
                flash("Logged in as " + session['username'])
                return redirect('/blog')
            else:
                flash("That wasn't the right password", 'error')
        else:
            flash('User does not exist', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/blog')


if __name__ == '__main__':
    app.run()