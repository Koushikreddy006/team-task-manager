from flask import Flask, render_template, request, redirect, url_for
from models import db, User, Task, Project
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ---------------- INIT ----------------
db.init_app(app)

# ✅ Create DB (Railway safe)
with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# ---------------- LOAD USER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- HOME ----------------
@app.route('/')
def home():
    return redirect(url_for('login'))

# ---------------- SIGNUP ----------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            return "User already exists!"

        user = User(name=name, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"

    return render_template('login.html')

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
@login_required
def dashboard():

    if current_user.role == "Admin":
        tasks = Task.query.all()
        users = User.query.all()
        projects = Project.query.all()
    else:
        tasks = Task.query.filter_by(user_id=current_user.id).all()
        users = None
        projects = Project.query.all()

    return render_template(
        'dashboard.html',
        tasks=tasks,
        users=users,
        projects=projects
    )

# ---------------- CREATE PROJECT ----------------
@app.route('/create_project', methods=['POST'])
@login_required
def create_project():
    if current_user.role != "Admin":
        return "Access denied"

    name = request.form.get('name')

    project = Project(
        name=name,
        created_by=current_user.id
    )

    db.session.add(project)
    db.session.commit()

    return redirect(url_for('dashboard'))

# ---------------- ADD TASK (FIXED) ----------------
@app.route('/add_task', methods=['POST'])
@login_required
def add_task():

    if current_user.role == "Admin":
        title = request.form.get('title')

        # ✅ FIX: convert to int
        user_id = int(request.form.get('user_id'))
        project_id = int(request.form.get('project_id'))

        task = Task(
            title=title,
            status="Pending",
            user_id=user_id,
            project_id=project_id
        )

    else:
        title = request.form.get('title')

        task = Task(
            title=title,
            status="Pending",
            user_id=current_user.id,
            project_id=None
        )

    db.session.add(task)
    db.session.commit()

    return redirect(url_for('dashboard'))

# ---------------- COMPLETE TASK ----------------
@app.route('/complete_task/<int:id>')
@login_required
def complete_task(id):
    task = Task.query.get(id)

    if task and task.user_id == current_user.id:
        task.status = "Done"
        db.session.commit()

    return redirect(url_for('dashboard'))

# ---------------- DELETE TASK ----------------
@app.route('/delete_task/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get(id)

    if task and (
        task.user_id == current_user.id or current_user.role == "Admin"
    ):
        db.session.delete(task)
        db.session.commit()

    return redirect(url_for('dashboard'))

# ---------------- LOGOUT ----------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)