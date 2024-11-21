import os
import pandas as pd
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo
from sqlalchemy import create_engine
from werkzeug.utils import secure_filename
from flask_paginate import Pagination, get_page_args
from sqlalchemy import inspect
from datetime import datetime


from sqlalchemy import text

# Create Flask app & define database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'gsdb4.db')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
# login_manager.login_view = 'login'

# File upload configurations
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'csv', 'tsv', 'xlsx', 'xls'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

# User DB model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)

# DataTable model to store uploaded chemical data
class ChemicalData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    species = db.Column(db.String(255), nullable=False)
    chemical = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    doi = db.Column(db.String(255), nullable=False)

# UploadedData model to track who uploaded the data
class UploadedData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False)
    user = db.relationship('User', backref=db.backref('uploads', lazy=True))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    duplicates = []  # Initialize an empty list for duplicates
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Load data from file
            try:
                if filename.endswith('.csv') or filename.endswith('.tsv'):
                    df = pd.read_csv(file_path, delimiter=',' if filename.endswith('.csv') else '\t')
                else:
                    df = pd.read_excel(file_path)
            except Exception as e:
                flash(f"Error reading file: {e}", 'danger')
                return redirect(request.url)

            # Ensure 'Amount' column is consistently float
            try:
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')  # Convert to float, set invalid data to NaN
            except KeyError:
                flash(f"'Amount' column not found in the uploaded file.", 'danger')
                return redirect(request.url)

            # Remove rows with NaN in 'Amount' if they can't be converted
            df.dropna(subset=['Amount'], inplace=True)

            # Add the current user's username or ID to each row of data
            df['uploaded_by'] = current_user.username  # Or current_user.id

            # Check if the table exists before querying
            inspector = inspect(engine)
            if 'data_table' not in inspector.get_table_names():
                # If table does not exist, create it and insert all data
                df.to_sql('data_table', con=engine, if_exists='append', index=False)
                flash(f'Table created and {len(df)} row(s) uploaded by admin!', 'success')
            else:
                # Fetch existing data from the database if table exists
                existing_data = pd.read_sql('SELECT * FROM data_table', con=engine)

                # Ensure 'Amount' column in existing data is float
                existing_data['Amount'] = pd.to_numeric(existing_data['Amount'], errors='coerce')

                # Check for duplicates by comparing with existing data
                merged_df = pd.merge(df, existing_data, on=['Species', 'chemical', 'Amount', 'DOI'], how='left', indicator=True)
                duplicates = merged_df[merged_df['_merge'] == 'both']  # Rows that are duplicates
                non_duplicates = df.loc[~df.index.isin(duplicates.index)]  # Rows that are not duplicates

                duplicate_count = len(duplicates)
                if duplicate_count > 0:
                    flash(f'{duplicate_count} duplicate row(s) found. These were not inserted.', 'danger')

                # Insert only non-duplicate rows into the database
                if not non_duplicates.empty:
                    non_duplicates.to_sql('data_table', con=engine, if_exists='append', index=False)
                    flash(f'{len(non_duplicates)} row(s) successfully uploaded!', 'success')

            # Log who uploaded the file
            upload_log = UploadedData(user_id=current_user.id, filename=filename, upload_date=pd.Timestamp.now())
            db.session.add(upload_log)
            db.session.commit()

            return redirect(url_for('show_data'))

    return render_template('upload.html', duplicates=duplicates)





# Set items per page
ITEMS_PER_PAGE = 10

#data show from db
@app.route('/show')
@login_required
def show_data():
    # Query the data and convert to a list of dictionaries
    query = 'SELECT * FROM data_table'
    df = pd.read_sql(query, con=engine)
    data = df.to_dict(orient='records')

    # Get pagination arguments
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')

    # Slice the data for the current page
    paginated_data = data[offset: offset + per_page]

    # Create the pagination object
    pagination = Pagination(page=page, per_page=per_page, total=len(data), css_framework='bootstrap4')

    uploads = UploadedData.query.all()

    return render_template('show_data.html', data=paginated_data, pagination=pagination, uploads=uploads)

#all user login and session start from here
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('info'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if user.is_approved:
                login_user(user)
                return redirect(url_for('info'))
            else:
                flash('Your account is not approved yet.', 'warning')
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)


#new user register there self in db
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Djay Check if the email is already in use
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('This email is already registered. Please try another one.', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please wait for admin approval.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

#session logout of any user
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/info')
@login_required
def info():
    return render_template('info.html')

@app.route('/about')
def about():
    return render_template('about.html')

#only admin allow to access the admin panel
@app.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin page.', 'error')
        return redirect(url_for('info'))

    # Fetch all users
    users = User.query.all()
    return render_template('admin.html', users=users)

#admin delete the user parmanently

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'error')
        return redirect(url_for('admin'))

    user = User.query.get_or_404(user_id)

    if user.is_admin:
        flash('Cannot delete admin user.', 'danger')
        return redirect(url_for('admin'))

    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('admin'))


@app.route('/approve/<int:user_id>')
@login_required
def approve_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to approve users.', 'error')
        return redirect(url_for('info'))
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.username} has been approved.', 'success')
    return redirect(url_for('admin'))

# Create admin user
def create_admin_user():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com',
                     password=generate_password_hash('GY204'),
                     is_admin=True, is_approved=True)
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        create_admin_user()  # Optionally create an admin user
    app.run(debug=True)
