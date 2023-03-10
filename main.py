from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests
import dotenv
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie_collection.db"
db = SQLAlchemy(app)

dotenv.load_dotenv()
tmdb_api_key = os.getenv("TMDB_API_KEY")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return '<Movie %r>' % self.title


class RateMovieForm(FlaskForm):
    rating = FloatField('Your Rating (Out of 10)', validators=[NumberRange(min=0, max=10), DataRequired()],
                        render_kw={"placeholder": "e.g. 7.5"})
    review = StringField('Your Review', validators=[DataRequired()], render_kw={"placeholder": '"I think it was..."'})
    submit = SubmitField('Change Rating')


class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()], render_kw={"placeholder": 'enter a movie title'})
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    movies = db.session.query(Movie).order_by(desc(Movie.rating))
    for idx, movie in enumerate(movies):
        if movie.ranking != idx + 1:
            movie.ranking = idx + 1
    db.session.commit()

    return render_template("index.html", movies=movies)


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        tmdb_api_url = (f"https://api.themoviedb.org/3/search/movie?api_key={tmdb_api_key}&language=en-US&page=1&"
                        f"include_adult=false&query={form.title.data}")
        tmdb_api_response = requests.get(tmdb_api_url)
        tmdb_api_response.raise_for_status()
        tmdb_json = tmdb_api_response.json()
        tmdb_movie_list = tmdb_json["results"]

        return render_template('select.html', searched_movies=tmdb_movie_list)

    return render_template('add.html', form=form)


@app.route("/create_movie_in_db/<tmdb_movie_id>", methods=["GET", "POST"])
def create_movie_in_db(tmdb_movie_id):
    # get movie details from TMDB API in JSON
    tmdb_movie_details_url = (f"https://api.themoviedb.org/3/movie/{tmdb_movie_id}?"
                              f"api_key={tmdb_api_key}&language=en-US")
    tmdb_movie_details_response = requests.get(tmdb_movie_details_url)
    tmdb_movie_details_response.raise_for_status()
    tmdb_movie_details_json = tmdb_movie_details_response.json()

    # add selected fields from JSON to database
    new_movie = Movie(
        title=tmdb_movie_details_json["title"],
        year=tmdb_movie_details_json["release_date"][:4],
        description=tmdb_movie_details_json["overview"],
        img_url=f'https://image.tmdb.org/t/p/original{tmdb_movie_details_json["poster_path"]}'
    )
    db.session.add(new_movie)
    db.session.commit()

    # query movie just added to database by movie title to be passed to edit_movie route
    movie_recently_created = Movie.query.filter_by(title=tmdb_movie_details_json["title"]).first()

    return redirect(url_for('edit_movie', movie_id=movie_recently_created.id))


@app.route("/edit_movie/<movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    form = RateMovieForm()
    movie_to_update = db.session.get(Movie, movie_id)
    if form.validate_on_submit():
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', form=form)


@app.route("/delete_movie/<movie_id>")
def delete_movie(movie_id):
    movie_to_delete = db.session.get(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(port=8000, debug=True)
