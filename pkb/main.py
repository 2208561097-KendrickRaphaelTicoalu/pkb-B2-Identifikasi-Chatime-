from flask import Flask, current_app, flash, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_bcrypt import Bcrypt
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = '65b0b774279de460f1cc5c92'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@localhost/db_pkb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = 'filesystem'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
Session(app)

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User Class
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(255), nullable=False)  
    no_telp = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    poin = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'User("{self.nama}", "{self.no_telp}", "{self.email}", "{self.poin}")'

# Admin Class
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'Admin("{self.username}", "{self.id}")'

# Voucher Class
class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    gambar = db.Column(db.String(255), nullable=False)  # Path to the uploaded file
    poin = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'Voucher("{self.judul}", "{self.poin}")'

# Memastikan Tabel Ada
with app.app_context():
    db.create_all()
    initial_admin = Admin.query.filter_by(username='admin').first()
    if not initial_admin:
        hash_password = bcrypt.generate_password_hash('111').decode('utf-8')
        initial_admin = Admin(username='admin', password=hash_password)
        db.session.add(initial_admin)
        db.session.commit()

# Home
@app.route('/')
def index():
    return render_template('index.html', title="")

# admin login
@app.route('/admin/', methods=["POST", "GET"])
def adminIndex():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == "" or password == "":
            flash('Please fill all the fields', 'danger')
            return redirect('/admin/')
        else:
            admin = Admin.query.filter_by(username=username).first()
            if admin and bcrypt.check_password_hash(admin.password, password):
                session['admin_id'] = admin.id
                session['admin_name'] = admin.username
                flash('Login Successfully', 'success')
                return redirect('/admin/dashboard')
            else:
                flash('Invalid Username or Password', 'danger')
                return redirect('/admin/')
    else:
        return render_template('admin/index.html', title="Admin Login")

# admin Dashboard
@app.route('/admin/dashboard/')
def adminDashboard():
    if not session.get('admin_id'):
        return redirect('/admin/')
    totalUsers = User.query.count()
    totalVouchers = Voucher.query.count()
    return render_template('admin/dashboard.html', title="Admin Dashboard", totalUsers=totalUsers, totalVouchers=totalVouchers)

#admin profile
@app.route('/admin/profile/', methods=["GET"])
def adminProfile():
    if not session.get('admin_id'):
        return redirect('/admin/')

    admin = Admin.query.filter_by(id=session['admin_id']).first()
    return render_template('admin/profile.html', admin=admin)

@app.route('/admin/profile/change-password/', methods=["POST"])
def adminChangePassword():
    if not session.get('admin_id'):
        return redirect('/admin/')
    
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    admin = Admin.query.filter_by(id=session['admin_id']).first()

    if not admin or not bcrypt.check_password_hash(admin.password, current_password):
        flash('Current password is incorrect', 'danger')
        return redirect('/admin/profile/')

    if new_password != confirm_password:
        flash('New passwords do not match', 'danger')
        return redirect('/admin/profile/')

    admin.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()

    flash('Password changed successfully', 'success')
    return redirect('/admin/profile/')

# admin user 
@app.route('/admin/user/', methods=["POST", "GET"])
def adminGetAllUser():
    if not session.get('admin_id'):
        return redirect('/admin/')
    if request.method == "POST":
        search = request.form.get('search')
        users = User.query.filter(User.nama.like('%' + search + '%')).all()
        return render_template('admin/user.html', title='Approve User', users=users)
    else:
        users = User.query.all()
        return render_template('admin/user.html', title='Approve User', users=users)

#admin voucher
@app.route('/admin/voucher/', methods=["POST", "GET"])
def adminAddVoucher():
    if not session.get('admin_id'):
        return redirect('/admin/')
    
    if request.method == 'POST':
        judul = request.form.get('judul')
        deskripsi = request.form.get('deskripsi')
        poin = request.form.get('poin')
        file = request.files.get('gambar')

        if not judul or not deskripsi or not file or not poin:
            flash('Please fill all fields', 'danger')
            return redirect('/admin/voucher/')

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect('/admin/voucher/')

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Invalid file type. Allowed types are png, jpg, jpeg, gif', 'danger')
            return redirect('/admin/voucher/')

        try:
            poin = int(poin)
        except ValueError:
            flash('Points must be a number', 'danger')
            return redirect('/admin/voucher/')

        voucher = Voucher(judul=judul, deskripsi=deskripsi, gambar=filename, poin=poin)
        db.session.add(voucher)
        db.session.commit()
        flash('Voucher added successfully', 'success')
        return redirect('/admin/voucher/')

    return render_template('admin/voucher.html', title='Add Voucher')

# admin logout
@app.route('/admin/logout/')
def adminLogout():
    session['admin_id'] = None
    session['admin_name'] = None
    return redirect('/')

# User login
@app.route('/user/', methods=["POST", "GET"])
def userLogin():
    if session.get('user_id'):
        return redirect('/user/dashboard')

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please fill all fields', 'danger')
            return redirect('/user/')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.nama 
            flash('Login Successfully', 'success')
            return redirect('/user/dashboard')

        flash('Invalid Email or Password', 'danger')
        return redirect('/user/')

    return render_template('user/index.html', title="User Login")

#user register
@app.route('/user/signup/', methods=['POST', 'GET'])
def userSignup():
    if session.get('user_id'):
        return redirect('/user/dashboard')

    if request.method == 'POST':
        nama = request.form.get('nama')
        no_telp = request.form.get('no_telp')
        email = request.form.get('email')
        password = request.form.get('password')

        if not nama or not no_telp or not email or not password:
            flash('Please fill all fields', 'danger')
            return redirect('/user/signup')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists', 'danger')
            return redirect('/user/signup')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(nama=nama, no_telp=no_telp, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully', 'success')
        return redirect('/user/')

    return render_template('user/signup.html', title="User Signup")

# user dashboard 
@app.route('/user/dashboard/')
def userDashboard():
    if not session.get('user_id'):
        return redirect('/user/')
    user = User.query.get(session['user_id'])
    return render_template('user/dashboard.html', title="User Dashboard", user=user)

# user profile 
@app.route('/user/profile/', methods=["POST", "GET"])
def userProfile():
    if not session.get('user_id'):
        return redirect('/user/')
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        nama = request.form.get('nama')
        email = request.form.get('email')
        password = request.form.get('password')

        if not nama or not email or not password:
            flash('Please fill all fields', 'danger')
            return redirect('/user/profile')

        if email != user.email and User.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect('/user/profile')

        if not bcrypt.check_password_hash(user.password, password):
            flash('Current password is incorrect', 'danger')
            return redirect('/user/profile')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.nama = nama
        user.email = email
        user.password = hashed_password
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect('/user/dashboard')

    return render_template('user/profile.html', title="User Profile", user=user)

# user voucher 
@app.route('/user/voucher/')
def userVoucher():
    if not session.get('user_id'):
        return redirect('/user/')
    vouchers = Voucher.query.all()
    return render_template('user/voucher.html', title="Available Vouchers", vouchers=vouchers)

# user logout
@app.route('/user/logout/')
def userLogout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
