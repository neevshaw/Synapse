import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random


project_folder = os.path.expanduser('~/mysite')  # PythonAnywhere project folder containing .env
load_dotenv(os.path.join(project_folder, '.env'))
LAMBDA_FUNCTION_URL = os.getenv('LAMBDA')

db = SQLAlchemy()
login_manager = LoginManager()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_pass_encoded = quote_plus(db_pass)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{db_user}:{db_pass_encoded}@{db_host}:3306/{db_name}"
)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), unique=False, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    account_type = db.Column(db.String(50), nullable=False, default='personal')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=False, nullable=False)
    age = db.Column(db.Integer, nullable=True)
    grade = db.Column(db.String(20), nullable=True)
    interests = db.Column(db.String(30), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    projects_completed = db.Column(db.Integer, nullable=True)
    courses = db.Column(db.String(50), nullable=True)

class Business(db.Model):
    __tablename__ = "businesses"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=False, nullable=False)
    phone = db.Column(db.String(150), unique=False, nullable=True)
    industry = db.Column(db.String(150), unique=False, nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=True)

class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, unique=False, nullable=False)
    title = db.Column(db.String(150), unique=False, nullable=False)
    deadline = db.Column(db.String(150), unique=False, nullable=False)
    short_description = db.Column(db.String(300), nullable=False)
    long_description = db.Column(db.Text, unique=False, nullable=False)
    additional_info = db.Column(db.String(150), unique=False, nullable=True)
    fulfilled = db.Column(db.Boolean)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    try:
        with app.app_context():
            result = db.session.execute(db.text('SELECT 1 FROM users LIMIT 1'))
            result.close()
    except Exception:
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("Database tables created successfully!")
                print("Database tables created successfully!")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
            print(f"Error creating database tables: {e}")

def ensure_db_exists():
    with app.app_context():
        try:
            db.create_all()  # only creates tables that don't exist yet
            print("Database initialization complete!")
        except Exception as e:
            print(f"Error with database initialization: {e}")

ensure_db_exists()

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('learn'))

    return render_template("home.html")

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('learn'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '')
        confirm_password = request.form.get('confirm_password', '')
        password = request.form.get('password', '')
        account_type = request.form.get('account_type', 'personal')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template("signup.html", name=full_name, password=password, confirm_password=confirm_password, account=account_type)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template("signup.html", name=full_name, email=email, account=account_type)

        if password != confirm_password:
            flash('Password does not match the confirmation.', 'error')
            return render_template("signup.html", name=full_name, email=email, account=account_type)

        try:
            user = User(email=email, account_type=account_type, name=full_name)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            login_user(user, remember=False)
            if account_type == "personal":
                account = Student(id=user.id, name=full_name)
            else:
                account = Business(id=user.id, name=full_name)
            db.session.add(account)
            db.session.commit()
            flash("Account created successfully! Please fill out the following information", "success")
            return redirect(url_for('profile'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred while creating your account. Please try again.', 'error')
            app.logger.error(f"Registration error: {e}")
            return redirect(url_for('register'))

    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('learn'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'

        if not email or not password:
            flash('Email and password are required.', 'error')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        login_user(user, remember=remember_me)

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        flash(f'Welcome back, {user.name}!', 'success')
        if user.account_type == "personal":
            return redirect(url_for('learn'))
        else:
            return redirect(url_for('projects'))

    return render_template("login.html")

@app.route('/match', methods=["POST"])
@login_required
def matching():
    if current_user.account_type == "personal":
        return jsonify({"message": "Not Allowed"}), 403
    data = request.get_json()
    students = []
    for student in Student.query.all():
        s= {"name": student.name, "age": student.age, "location": student.location, "projects_completed": (0 if student.projects_completed==None else student.projects_completed), "interests": [], "completed_courses": [], "email": User.query.get(student.id).email}
        inter = [
            "AI and Machine Learning",
            "Creating Mobile Apps",
            "Turning Data into Insights",
            "Growing Online Presence Efficiently",
            "Connecting Different Platforms Together",
            "Building Interactive Websites",
            "Launching Online Stores",
            "Collecting Data Autonomously",
            "Running Projects in the Cloud",
            "Saving Time on Repetitive Tasks",
        ]
        for i in range(len(inter)):
            if student.interests != None and student.interests[i] == "1":
                s["interests"].append(inter[i])
        tech_courses = [
            "Basic AI and Chatbot Development",
            "Mobile App Development for Beginners in Flutter",
            "Data Analysis with Excel and Python",
            "Social Media Automation Tools",
            "Introduction to APIs and HTTP Requests",
            "Introduction to HTML, CSS, and JavaScript",
            "E-commerce and Online Shopping",
            "Advanced Data Collection Techniques",
            "Introduction to Cloud Services (AWS/GCP)",
            "Workflow Automation in Repetitive Business Tasks"
        ]
        for i in range(len(tech_courses)):
            if student.courses != None and student.courses[i] == "1":
                s["completed_courses"].append(tech_courses[i])
        students.append(s)
    output = match(os.getenv('GEMINI_API'), data, students)
    result = {
        "output": output
    }
    return jsonify(result), 200

@app.route('/learn')
@login_required
def learn():
    if current_user.account_type == "personal":
        return render_template("learn.html")
    return redirect(url_for('projects'))

@app.route('/unit-<int:u>/lesson-<int:l>/module-<int:m>')
@login_required
def lesson(u, l, m):
    if current_user.account_type == "business":
        return redirect(url_for('projects'))
    template_file_path = os.path.join(app.root_path, 'templates', f'unit{u}', f'lesson{l}', f'module{m}.html')
    if os.path.exists(template_file_path):
        return render_template(f"unit{u}/lesson{l}/module{m}.html")
    return render_template("coming_soon.html")

@app.route('/complete/<int:project_id>', methods=["POST"])
@login_required
def complete(project_id):
    if current_user.account_type != "business":
        return redirect(url_for('projects'))
    Project.query.get(project_id).fulfilled = True
    db.session.commit()
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/unit-<int:u>/quiz')
@login_required
def quiz(u):
    if current_user.account_type == "business":
        return redirect(url_for('projects'))
    template_file_path = os.path.join(app.root_path, 'templates', f'unit{u}', f'quiz.html')
    if os.path.exists(template_file_path):
        return render_template(f"unit{u}/quiz.html")
    return render_template("coming_soon.html")

@app.route('/projects')
@login_required
def projects():
    return render_template("projects.html",  account=current_user.account_type, uid=current_user.id, projects=Project.query.all())

@app.route('/profile', methods=["GET", "POST"])
@login_required
def profile():
    if current_user.account_type == "personal":
        student = Student.query.get(current_user.id)
        if request.method == "POST":
            current_user.name = request.form.get("name")
            student.name = request.form.get("name")
            student.age = int(request.form.get("age")) if request.form.get("age") != '' else None
            student.grade = request.form.get("grade")
            student.location = request.form.get("location")
            all_options = list(range(1, 13))
            checked = request.form.getlist('interests')
            checked = [int(x) for x in checked]
            checkbox_states = [str(int(i in checked)) for i in all_options]
            student.interests = "".join(checkbox_states)
            student.courses = "".join(checkbox_states)
            student.projects_completed = random.randint(0, 5)
            db.session.commit()
            flash("Profile saved!", "success")
            return redirect(url_for('profile'))


        return render_template("student_profile.html", user=student)
    else:
        business = Business.query.get(current_user.id)
        if request.method == "POST":
            current_user.name = request.form.get("name")
            business.name = request.form.get("name")
            business.industry = request.form.get("industry")
            business.phone = request.form.get("phone")
            business.description = request.form.get("description")
            business.location = request.form.get("location")
            db.session.commit()
            flash("Profile saved!", "success")
            return redirect(url_for('profile'))

        return render_template("business_profile.html", user=business)

@app.route('/post', methods=["POST"])
@login_required
def post():
    if current_user.account_type == "personal":
        return redirect(url_for('projects'))
    title = request.form.get("title")
    short = request.form.get("description")
    deadline = request.form.get("deadline")
    big =  request.form.get("expected-outcome")
    add = None if request.form.get("additional-info")=="" else request.form.get("additional-info")

    project = Project(business_id=current_user.id, title=title, short_description=short, deadline=deadline, long_description=big, additional_info=add, fulfilled=False)
    db.session.add(project)
    db.session.commit()
    return redirect(url_for('projects'))

@app.route('/project/<int:project_id>', methods=["GET", "POST"])
@login_required
def project_details(project_id):
    p = Project.query.get(project_id)
    if p == None:
        abort(404)
    business = Business.query.get(p.business_id)
    email = User.query.get(p.business_id).email
    return render_template('project_template.html', p=p, b=business, e=email, account=current_user.account_type)


@app.route('/apply/<int:project_id>', methods=["POST"])
@login_required
def apply(project_id):
    if current_user.account_type != "personal":
        return redirect(url_for('projects'))
    body = request.form.get("application")
    add = None if request.form.get("additional-info")=="" else request.form.get("additional-info")

    project = Project.query.get(project_id)
    student = Student.query.get(current_user.id)

    payload = {
        "to": User.query.get(project.business_id).email,
        "subject": "Application Received for Project: " + project.title,
        "body": "Application:\n\n" + body + "\n\n"+ (add+"\n\n" if add !=None else "") + f"Student Info:\n\nName - {student.name}\nEmail - {current_user.email}"
    }
    res = requests.post(
        LAMBDA_FUNCTION_URL,
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    print("Email sent!")
    return redirect(url_for('projects'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Page Not Found</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="{{ url_for('index') }}">Go Home</a>
    </body>
    </html>
    '''), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>Internal Server Error</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
        <h1>500 - Internal Server Error</h1>
        <p>Something went wrong on our end.</p>
        <a href="{{ url_for('index') }}">Go Home</a>
    </body>
    </html>
    '''), 500

app.db = db
app.User = User

@app.cli.command()
def init_db_command():
    """Create any missing database tables."""
    with app.app_context():
        db.create_all()
        print('Initialized the database.')

if __name__ == '__main__':
    app.run(debug=True)