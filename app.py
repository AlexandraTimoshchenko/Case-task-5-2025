from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(120))
    trips = db.relationship('Trip', backref='user', lazy=True)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    image = db.Column(db.String(100))
    cost = db.Column(db.Float)
    places = db.Column(db.Text)
    rating = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Создаем базу данных
with app.app_context():
    db.create_all()
    # Создаем тестового пользователя если его нет
    if not User.query.filter_by(username='test').first():
        user = User(username='test', password=generate_password_hash('test123'))
        db.session.add(user)
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты
@app.route('/')
def home():
    trips = Trip.query.order_by(Trip.created_at.desc()).all()
    return render_template('index.html', trips=trips)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash('Неверные данные')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Имя занято')
            return redirect(url_for('register'))

        user = User(
            username=request.form['username'],
            password=generate_password_hash(request.form['password'])
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_trip():
    if request.method == 'POST':
        # Обработка изображения
        image = request.files['image']
        image_name = None
        if image and image.filename != '':
            image_name = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        trip = Trip(
            title=request.form['title'],
            description=request.form['description'],
            location=request.form['location'],
            image=image_name,
            cost=float(request.form['cost']) if request.form['cost'] else None,
            places=request.form['places'],
            rating=int(request.form['rating']) if request.form['rating'] else None,
            user_id=current_user.id
        )
        db.session.add(trip)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add.html')

@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    trip = Trip.query.get_or_404(trip_id)
    return render_template('detail.html', trip=trip)

if __name__ == '__main__':
    app.run(debug=True)