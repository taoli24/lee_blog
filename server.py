import flask
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from forms import PostForm, UserRegisterForm, LoginForm, CommentForm
import smtplib
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
import itertools
import datetime as dt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from functools import wraps
import os
# env variables set up in heroku, comment out below two lines before push to GitHub.
# from dotenv import load_dotenv
# load_dotenv('./vars/.env')


secret_key = os.getenv('SECRET_KEY')
USER_NAME = os.getenv('USER_NAME')
PASSWORD = os.getenv('PASSWORD')

app = Flask(__name__)
Bootstrap5(app)
CKEditor(app)
login_manager = LoginManager(app)
api_end_point = 'https://api.npoint.io/0c739d27b0f3a1e8c51f#'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret_key
db = SQLAlchemy(app)
gravatar = Gravatar(app,
                    size=50,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.id == 1:
                return function(*args, **kwargs)
            else:
                return abort(403)
        else:
            return abort(403)

    return wrapper


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    posts = db.relationship('BlogPost', back_populates='author')
    comments = db.relationship('Comment', back_populates='author')


class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.relationship('User', back_populates='posts')
    title = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    body = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)
    image = db.Column(db.String(250), nullable=False)
    comments = db.relationship('Comment', back_populates='post')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = db.relationship('User', back_populates='comments')
    post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'))
    post = db.relationship('BlogPost', back_populates='comments')


# for this website, we will only request api once
# for future projects,we might need to request api every time user click the posts button

# retrieve the data from our old api endpoint, we won't need this anymore
# response = requests.get(api_end_point)
# post_data = response.json()
#
db.create_all()


#
# for post in post_data:
#     new_post = BlogPost(**post)
#     db.session.add(new_post)
#     db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    all_post = db.session.query(BlogPost).all()

    return render_template('index.html', posts=all_post, logged_in=current_user.is_authenticated)


@app.route('/about')
def about():
    return render_template('about.html', logged_in=current_user.is_authenticated)


@app.route('/contact', methods=['POST', 'GET'])
def contact():
    if request.method == 'GET':
        return render_template('contact.html', heading='Contact Me', logged_in=current_user.is_authenticated)
    else:
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        msg = request.form['message']

        with smtplib.SMTP('smtp.gmail.com') as connection:
            connection.starttls()
            connection.login(user=USER_NAME, password=PASSWORD)
            connection.sendmail(
                from_addr=USER_NAME,
                to_addrs='gujie713@gmail.com',
                msg=f'Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {msg}'
            )
        return render_template('contact.html', heading='Your message has been successfully sent.',
                               logged_in=current_user.is_authenticated)


@app.route('/post/<int:post_num>', methods=['GET', 'POST'])
def post(post_num):
    blog_post = BlogPost.query.get(post_num)
    form = CommentForm()
    if form.validate_on_submit():
        try:
            new_comment = Comment(
                author_id=current_user.id,
                post_id=blog_post.id,
                text=form.comment.data
            )

            db.session.add(new_comment)
            db.session.commit()
        except AttributeError:
            flask.flash('You need to sign in before making a comment.')

        return redirect(url_for('post', post_num=blog_post.id))

    return render_template('post_form.html', post=blog_post, logged_in=current_user.is_authenticated, form=form)


@app.route('/new_post', methods=['GET', 'POST'])
@admin_only
def make_post():
    form = PostForm()
    if form.validate_on_submit():
        # slice form data dictionary and retrieve the first 4 items
        kwargs = dict(itertools.islice(form.data.items(), 4))
        kwargs['date'] = dt.datetime.now().strftime('%B %d %Y')
        kwargs['author_id'] = current_user.id
        new_post = BlogPost(**kwargs)
        db.session.add(new_post)
        db.session.commit()
        print(form.data)
        return redirect(url_for('home'))
    return render_template('make_post.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/edit-post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    post_to_edit = BlogPost.query.get(post_id)
    edit_form = PostForm(
        title=post_to_edit.title,
        subtitle=post_to_edit.subtitle,
        # author=post_to_edit.author,
        image=post_to_edit.image,
        body=post_to_edit.body,
    )

    if edit_form.validate_on_submit():
        post_to_edit.title = edit_form.title.data
        post_to_edit.subtitle = edit_form.subtitle.data
        # post_to_edit.author = edit_form.author.data
        post_to_edit.image = edit_form.image.data
        post_to_edit.body = edit_form.body.data
        db.session.commit()

        return render_template('post_form.html', post=post_to_edit)

    return render_template('make_post.html', form=edit_form, edit=True, logged_in=current_user.is_authenticated)


@app.route('/delete')
@admin_only
def delete():
    post_id = request.args.get('id')
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = UserRegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        exist_user = User.query.filter_by(email=email).first()
        if not exist_user:
            new_user = User(
                email=email,
                name=form.name.data,
                password=generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
            )
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user)

            return redirect(url_for('home'))
        else:
            flask.flash("Email exist in our database, login instead.")
            return render_template('register.html', form=form)
    return render_template('register.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flask.flash("Incorrect password.")
                return render_template('login.html', form=form, logged_in=current_user.is_authenticated)
        else:
            flask.flash("Email address you've entered does not exist in our database.")
            return render_template('login.html', form=form, logged_in=current_user.is_authenticated)
    return render_template('login.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
