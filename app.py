# from crypt import methods
from flask import Flask, render_template, flash, request, redirect, url_for  
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate 
from werkzeug.security import generate_password_hash, check_password_hash 
from werkzeug.utils import secure_filename
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user 
from webforms import LoginForm, PostForm, UserForm, NamerForm, PasswordForm, SearchForm 
from flask_ckeditor import CKEditor
from sqlalchemy import desc
import uuid as uuid
import os 

# создаю flask instance
app = Flask(__name__)

# ckeditor
ckeditor = CKEditor(app)

# создаю БД 
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# БД на postgress
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://pksnyfujebenpn:d9dad89845a721460c3504320429cd75d348090cf739adb35046014f4fff3459@ec2-18-209-78-11.compute-1.amazonaws.com:5432/d816afa4dldt15'

# секретный ключ!
app.config['SECRET_KEY'] = 'КАКОЙ ТО СЕКРЕТНЫЙ КЛЮЧ'

# инициализация БД
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# flask_login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# pass stuff to navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# создаю страницу для админа
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 26:
        return render_template('admin.html')
    else:
        flash("Вы должны быть админом!")
        return redirect(url_for("dashboard"))

# функция поиска
@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        post.searched = form.searched.data
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template("search.html",
                               form = form,
                               searched = post.searched,
                               posts = posts) 

# создание страницы login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # проверяю хэш
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('Вы вошли!')
                return redirect(url_for('dashboard'))
            else:
                flash('Не правильный пароль!')
        else:
            flash('Такого пользователя нет!')

    return render_template('login.html', form=form)

# создание страницы выхода
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы. Приходите еще!')
    return redirect(url_for('login'))

# создание dashboard'а
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id 
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color'] 
        name_to_update.username = request.form['username']
        name_to_update.about_author = request.form['about_author']
        name_to_update.profile_pic = request.files['profile_pic']

        # берем имя картинки пользователя
        pic_filename = secure_filename(name_to_update.profile_pic.filename)
        
        # set UUID
        pic_name = str(uuid.uuid1()) + "_" + pic_filename
        
        # сохранение картинки
        saver = request.files['profile_pic']
        
        # изменяем картинку на строку
        name_to_update.profile_pic = pic_name

        try:
            db.session.commit()
            saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
            flash('Данные обновлены!!')
            return render_template('dashboard.html',
                form=form,
                name_to_update=name_to_update)
        except:
            flash('Ошибка! Попробуй ка еще дружочек.')
            return render_template('dashboard.html',
                form=form,
                name_to_update=name_to_update)
    else:
        return render_template('dashboard.html',
                form=form,
                name_to_update=name_to_update,
                id=id)
    return render_template('dashboard.html')

@app.route('/posts/delete/<int:id>')
@login_required 
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id 
    if id == post_to_delete.poster.id: 
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash('Blog Post Was Deleted!')
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template('posts.html', posts=posts)
        except:
            flash('Oooops! Blog Post Was NOT Deleted! Try Again.')
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template('posts.html', posts=posts)
    else:
        flash("You aren't autorized to delete that post!")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts)

@app.route('/post/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts')
def posts():
    posts = Posts.query.order_by(desc(Posts.date_posted))
    return render_template('posts.html', posts=posts)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        # post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data 
        
        # обновляю бд
        db.session.add(post)
        db.session.commit()
        flash('Post Has Been Updated!')
        return redirect(url_for('post', id=post.id))
    
    if current_user.id == post.poster_id:
        form.title.data = post.title
        # form.author.data = post.author
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You aren't autorized to edit that post!")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template('posts.html', posts=posts) 

# добавляю страницу постов
@app.route('/add-post', methods=['GET', 'POST'])
# @login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        poster = current_user.id 
        post = Posts(title=form.title.data,
                     content=form.content.data,
                     poster_id=poster,
                     slug=form.slug.data)
        form.title.data = ''
        form.content.data = ''
        # form.author.data = ''
        form.slug.data = ''

        # добавляю посты в бд
        db.session.add(post)
        db.session.commit()

        flash('Blog Post Submitted Successfuly!')

    # возвращаем на веб страницу
    return render_template('add_post.html', form=form)

# json
@app.route('/date')
def get_current_date():
    favorite_frute = {
        'Ruslan': 'Bananas',
        'Slava': 'Apples',
        'Katya': 'Oranges'
    }
    return favorite_frute
    # return {'Date': date.today()}

# удаление пользователя
@app.route('/delete/<int:id>')
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Пользователь Удален!')
        our_users = Users.query.order_by(Users.date_added)
        return render_template('add_user.html', 
                                form=form,
                                name=name,
                                our_users=our_users)
    except:
            flash('Упсс! Ты где то недоглядел.')
            return render_template('add_user.html', 
                                form=form,
                                name=name,
                                our_users=our_users)

# обновление записей в БД
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required 
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color'] 
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash('Данные обновлены!!')
            return render_template('update.html',
                form=form,
                name_to_update=name_to_update)
        except:
            flash('Ошибка! Попробуй ка еще дружочек.')
            return render_template('update.html',
                form=form,
                name_to_update=name_to_update)
    else:
        return render_template('update.html',
                form=form,
                name_to_update=name_to_update,
                id=id)

# добавление пользователей
@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # хэширование пароля!!
            hashed_pw = generate_password_hash(form.password_hash.data, 'sha256')
            user = Users(name=form.name.data,
                         username=form.username.data, 
                         email=form.email.data, 
                         favorite_color=form.favorite_color.data, 
                         password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''

        flash('Пользователь Добавлен!!!')
    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html', 
                           form=form,
                           name=name,
                           our_users=our_users)

# создаю декоратор пути
@app.route('/')
def index():
    first_name = 'Ruslan'
    favorite_food = ['pancackes', 'the_shaverma', 'pelmeniy']
    return render_template('index.html', 
                           first_name=first_name,
                           favorite_food=favorite_food)

# localhost:5000/user/ruslan
@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

# создаю кастомные страницы ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500 

# создаю страницу для теста
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    #форма валидации
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        
        form.email.data = ''
        form.password_hash.data = ''
        
        # lookup user by email
        pw_to_check = Users.query.filter_by(email=email).first()

        # проверка захэшированног пароля
        passed = check_password_hash(pw_to_check.password_hash, password)

    return render_template('test_pw.html',
        email = email,
        password = password,
        pw_to_check = pw_to_check,
        passed = passed,
        form = form)

# создаю страницу с именем
@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NamerForm()

    #форма валидации
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash('Success!')

    return render_template('name.html',
        name = name,
        form = form)

# модель blog post
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    # author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255)) 
    # ключ связующий Юзеров с Постами :)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

# создаю модель
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow) 
    profile_pic = db.Column(db.String(120), nullable=True)

    # хэширование паролей 
    password_hash = db.Column(db.String(128))
    
    # у одного юзера может быть несколько постов
    posts = db.relationship('Posts', backref='poster')

    @property
    def password(self):
        raise AssertionError('password is not readable attribute!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Create A String
    def __repr__(self):
        return '<Name %r>' % self.name 


