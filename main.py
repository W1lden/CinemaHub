from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from sqlalchemy import asc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, PasswordField, EmailField
from wtforms.validators import DataRequired, InputRequired, Length, ValidationError, Email
import requests
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from pprint import pprint
from random import choice, randint
from tmdbv3api import TMDb, Movie


TMDB_KEY = '6160c759fb7623e398533bccaeab98a5'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinemahub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
bcrypt = Bcrypt(app)
Bootstrap(app)
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

user_movie = db.Table('user_movie',
                db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                db.Column('movie_id', db.Integer, db.ForeignKey('movie.id'), primary_key=True)
                )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    # password = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    movies = db.relationship('Movie', secondary=user_movie, backref=db.backref('users', lazy=True))


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    year = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(250))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(500))
    img_url = db.Column(db.String(1000))
    movie_tmdb_id = db.Column(db.Integer)


class Login(FlaskForm):
    email = EmailField(label='Ваш адрес электронной почты', validators=[InputRequired(), DataRequired(), Length(min=4), Email(message='Неверный адрес')])
    password = PasswordField(label='Ваш пароль')
    submit = SubmitField(label="Войти")

class Register(FlaskForm):
    email = EmailField(label='Ваш адрес электронной почты', validators=[InputRequired(), DataRequired(), Length(min=4), Email(message='Неверный адрес')])
    password = PasswordField(label='Ваш пароль')
    submit = SubmitField(label="Зарегистрироваться")

    def validate_email(self, email):
        existing_user_email = User.query.filter_by(
            email=email.data).first()
        if existing_user_email:
            raise ValidationError(
                "That email already exists. Please choose a different one.")
        
class Edit(FlaskForm):
    rating = FloatField(label='Ваш рейтинг', validators=[DataRequired()])
    review = StringField(label='Ваш отзыв', validators=[DataRequired()])
    submit = SubmitField(label="Подтвердить")


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template("index.html")

@app.route("/detail", methods=['GET', 'POST'])
def detail():
    return render_template("detail.html")

@app.route("/movie-list", methods=['GET', 'POST'])
def movie_list():
    return render_template("movie-list.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = Login()
    # if current_user.is_authenticated:
    #     return redirect(url_for('index'))

    if form.validate_on_submit():
        email = request.form['email']
        password = request.form['password']
        # remember_me = True if request.form.get('remember_me') else False
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            # movies = current_user.movies
        if user.email != email or user.password_hash != password:
            print('Invalid data!')
            return redirect(url_for('login'))
        # if not user or not user.check_password(password):
        #     flash('Invalid email or password')
        #     print('Invalid data!')
        #     print(f'{email}\n{password}')
        #     print(type(email))
        #     return redirect(url_for('login'))

        # login_user(user, remember=remember_me)
        login_user(user)
        # return redirect(url_for('my_movies', id=user.id))
        return redirect(url_for('my_movies'))

    # if form.validate_on_submit():
    #     user = User.query.filter_by(email=form.email.data).first()
    #     print(user)
    #     # if user:
    #     #     if bcrypt.check_password_hash(user.password, form.password.data):
    #     #         login_user(user)
    #     #         return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = Register()

    if form.validate_on_submit():
        # hashed_password = bcrypt.generate_password_hash(form.password.data)
        # new_user = User(email=form.email.data, password=hashed_password)
        # new_user = User(email=form.email.data, password=form.password.data)
        new_user = User(email=form.email.data, password_hash=form.password.data)
        with app.app_context():
            db.session.add(new_user)
            db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/my_movies', methods=["GET", "POST"])
@login_required
def my_movies():
    user_id = current_user.id
    print(user_id)
    user = User.query.get(user_id)
    print(user.email)
    movies = db.session.query(Movie).join(user_movie).filter(user_movie.c.user_id == user_id).all()
    print(movies)
    return render_template('my_movies.html', movies=movies)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    with app.app_context():
        movie = Movie.query.filter_by(id=id).first()
        form = Edit()
    if form.validate_on_submit():
        movie_to_edit = Movie.query.get(id)
        movie_to_edit.rating = form.rating.data
        movie_to_edit.review = form.review.data
        db.session.commit()
        return redirect(url_for('my_movies'))
    return render_template('edit.html', movie=movie, form=form)

@app.route('/delete/<int:id>')
def delete(id):
    with app.app_context():
        movie_to_delete = Movie.query.get(id)
        db.session.delete(movie_to_delete)
        db.session.commit()
    return redirect(url_for('my_movies'))

@app.route('/youtube', methods=["GET", "POST"])
def youtube():
    KEY = 'AIzaSyAevR8qG3m3BaWOZTtbCQo1Bu1iid4ZWRM'
    URL = 'https://www.googleapis.com/youtube/v3/search'
    key_phrases = ['обзор', 'интересные факты', 'пасхалки', 'разбор персонажей', 'актеры', 'анализ сюжета', 'объяснение концовки', 'лучшие моменты', 'вырезанные сцены', 'саундтреки']
    movies = ['The Amazing Spider-Man 2', 'Pirates of the Caribbean', 'Inception', 'The Godfather', 'Titanic']
    videos = []
    for i in range(6):
        query = f'{choice(movies)} фильм {choice(key_phrases)}'
        print(query)
        parameters = {
        'key': KEY,
        'maxResults': 3,
        'q': query
        }
        response = requests.get(url=URL, params=parameters)
        data = response.json()['items']
        for video in data:
            try:
                videos.append(f'https://www.youtube.com/embed/{video["id"]["videoId"]}')
            except KeyError:
                pass
    pprint(videos)
    return render_template('youtube.html', videos=videos)

@app.route('/music', methods=["GET", "POST"])
def music():
    musics = {
        1: {'item': 'pirates.of.the.caribbean.the.curse.of.the.black.pearl.original.motion.picture.soundtrack',
        'playlist': None,
        'img': 'https://archive.org/download/pirates.of.the.caribbean.the.curse.of.the.black.pearl.original.motion.picture.soundtrack/Klaus Badelt - Pirates of the Caribbean_ The Curse of the Black Pearl (Original Motion Picture Soundtrack)/cover.png'
        },
        2: {'item': 'theamazingspiderman2-theoriginalmotionpicturesoundtrackdeluxe',
        'playlist': None,
        'img': 'https://archive.org/download/theamazingspiderman2-theoriginalmotionpicturesoundtrackdeluxe/Various Artists - The Amazing Spider-Man 2 (The Original Motion Picture Soundtrack) [Deluxe]/cover.png'
        },
        3: {
            'item': 'lp_the-godfather-original-soundtrack-recor_nino-rota',
            'playlist': None,
            'img': 'https://ia902502.us.archive.org/BookReader/BookReaderImages.php?zip=/24/items/lp_the-godfather-original-soundtrack-recor_nino-rota/lp_the-godfather-original-soundtrack-recor_nino-rota_jp2.zip&file=lp_the-godfather-original-soundtrack-recor_nino-rota_jp2/lp_the-godfather-original-soundtrack-recor_nino-rota_0000.jp2&id=lp_the-godfather-original-soundtrack-recor_nino-rota'
        },
        4: {
            'item': '10.-death-of-titanic-james-horner',
            'playlist': None,
            'img': 'https://ia601608.us.archive.org/17/items/10.-death-of-titanic-james-horner/James%20Horner%20-%20Titanic%20%28Soundtrack%29.jpg?cnt=0'
        },
        5: {
            'item': 'cd_inception_hans-zimmer',
            'playlist': None,
            'img': 'https://ia600106.us.archive.org/BookReader/BookReaderImages.php?zip=/27/items/cd_inception_hans-zimmer/cd_inception_hans-zimmer_jp2.zip&file=cd_inception_hans-zimmer_jp2/cd_inception_hans-zimmer_0000.jp2&id=cd_inception_hans-zimmer'
        },
    }
    return render_template('music.html', musics=musics)

@app.route('/my_recommendations', methods=['GET', 'POST'])
@login_required
def my_recommendations():
    user_id = current_user.id
    movies = db.session.query(Movie).join(user_movie).filter(user_movie.c.user_id == user_id).all()
    # pprint(movies)
    ids = []
    for movie in movies:
        ids.append(movie.movie_tmdb_id)
    # ids = movies['movie_tmdb_id']
    pprint(ids)
    # ids = [22, 2]
    movies = []
    count = 1
    for id in ids:
        query = {"api_key": '6160c759fb7623e398533bccaeab98a5', "query": id}
        response = requests.get(url=f'https://api.themoviedb.org/3/movie/{id}/recommendations', params=query)
        data = response.json()['results']
        data = data[0:4]
        movies.append(data)
        # movies[count] = data
        count += 1

    return render_template('my_recommendations.html', movies=movies)

class AddForm(FlaskForm):
    movie_name = StringField(label='Movie name', validators=[DataRequired()])
    submit = SubmitField(label="Commit")

@app.route('/add', methods=['GET', 'POST'])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        query = {"api_key": TMDB_KEY, "query": add_form.movie_name.data}
        response = requests.get(url='https://api.themoviedb.org/3/search/movie', params=query)
        data = response.json()
        movies = data['results']
        return render_template("select.html", movies=movies)
    return render_template('add.html', form=add_form)

@app.route('/select')
def select():
    return render_template('select.html')

@app.route('/movie_add/<int:id>', methods=['GET', 'POST'])
def movie_add(id):
    response = requests.get(url=f'https://api.themoviedb.org/3/movie/{id}', params={"api_key": TMDB_KEY})
    response_img = requests.get(url=f'https://api.themoviedb.org/3/movie/{id}/images', params={"api_key": TMDB_KEY})
    img = response_img.json()['posters'][0]
    data = response.json()
    with app.app_context():
        new_movie = Movie(
            title=data['title'],
            year=data['release_date'],
            description=data['overview'],
            img_url=f"https://image.tmdb.org/t/p/w600_and_h900_bestv2/{img['file_path']}",
            movie_tmdb_id=data['id']
        )
        db.session.add(new_movie)
        db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
