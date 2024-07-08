from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
import os 
import math
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_mail import Mail
import json

with open('config.json', 'r') as c:
    params = json.load(c)["params"]


local_server = True

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)
app.secret_key = 'hiten-shah'
app.config['UPLOAD_FOLDER'] = params['upload_location']

if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db = SQLAlchemy(app)

class Contacts(db.Model):
    # Sr_No. , Name, Email, Phone_num, Mes, Date
    Sr_No = db.Column(db.Integer, primary_key=True) 
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(20), nullable=False)
    Phone_num = db.Column(db.String(12), nullable=False)
    Mes = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12), nullable=True)

class Posts(db.Model):
    Sr_No = db.Column(db.Integer, primary_key=True)
    Title = db.Column(db.String(80), nullable=False) 
    Subtitle = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    Content = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12), nullable=True)
    Author = db.Column(db.String(12), nullable=True)
    img_url = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # [0:params['no_of_posts']]
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #Pagination Logic
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[((page-1)*int(params['no_of_posts'])):((page-1)*int(params['no_of_posts']) + int(params['no_of_posts']))]

    # First Page
    if(page == 1):
        prev = "#"
        next = "/?page=" + str(page + 1)

    # Last Page
    elif(page == last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    
    # Middle Page
    else:
        prev = "/?page="+ str(page - 1)
        next = "/?page="+ str(page + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, post=post)

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        # Add an entry to the database
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')

        # Sr.No. , Name, Email, Phone_num, Mes, Date
        entry = Contacts(Name=name, Email=email, Phone_num=phone, Mes=message, Date = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(name + " Contacted you!",
                        sender = email, 
                        recipients = [params['gmail-user']],
                        body = message + "\n" + phone)

    return render_template('contact.html', params=params)

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_pass']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
        
    return render_template('login.html', params=params)

@app.route("/edit/<string:Sr_No>", methods = ['GET', 'POST'])
def edit(Sr_No):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            req_title = request.form.get('title')
            req_subtitle = request.form.get('subtitle')
            req_slug = request.form.get('slug')
            req_content = request.form.get('content')
            req_imgURL = request.form.get('img_url')
            req_Date = datetime.now()
            req_Author = request.form.get('author')

            if Sr_No == '0':
                post = Posts(Title=req_title, Subtitle=req_subtitle, slug=req_slug, Content=req_content, Date=req_Date, img_url=req_imgURL, Author=req_Author)
                db.session.add(post)
                db.session.commit()
            
            else:
                post = Posts.query.filter_by(Sr_No=Sr_No).first()
                post.Title = req_title
                post.Subtitle = req_subtitle
                post.slug = req_slug
                post.Content = req_content
                post.img_url = req_imgURL
                post.Date = req_Date
                db.session.commit()
                return redirect('/edit/'+Sr_No)

                
        post = Posts.query.filter_by(Sr_No=Sr_No).first()
        return render_template('edit.html', params=params, post=post, Sr_No=Sr_No)
    else:
        return render_template('login.html', params=params)

@app.route("/delete/<string:Sr_No>", methods = ['GET', 'POST'])
def delete(Sr_No):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(Sr_No=Sr_No).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')        


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/uploader", methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully"
    else:
        return render_template('login.html', params=params)

app.run(debug=True)