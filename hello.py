from flask import Flask, render_template

# создаю flask instance
app = Flask(__name__)

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