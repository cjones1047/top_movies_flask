from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie_collection.db"
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
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
    movies = db.session.query(Movie).all()

    return render_template("index.html", movies=movies)


@app.route("/add_movie", methods=["GET", "POST"])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        # code for what to do after form validation goes here:

        return redirect(url_for('home'))

    return render_template('add.html', form=form)


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
