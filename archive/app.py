import os
import pathlib
from functools import wraps
from datetime import datetime, timedelta
from io import BytesIO
from dotenv import load_dotenv
# Load environment variables early
load_dotenv(override=True)
from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort, send_file
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, UserMixin, current_user
)
import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import db  # runs DB connection & migrations on import

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# ─── Flask-Login Setup ─────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, email, password_hash, role):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def get(user_id):
        cur = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row:
            return User(row['id'], row['email'], row['password_hash'], row['role'])
        return None

    @staticmethod
    def find_by_email(email):
        cur = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        if row:
            return User(row['id'], row['email'], row['password_hash'], row['role'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

# Admin-only decorator
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Authentication Routes ───────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.find_by_email(request.form['email'])
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(request.args.get('next') or url_for('list_permits'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── Admin Dashboard ─────────────────────────────────────────────────
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin.html')

# ─── Home ─────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return redirect(url_for('list_permits'))

# ─── List Permits & Expiring Count ────────────────────────────────────
@app.route('/permits')
@login_required
def list_permits():
    show_archived = request.args.get('show_archived', 'false').lower() == 'true'
    cur = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if show_archived:
        cur.execute("SELECT * FROM permits ORDER BY id")
    else:
        cur.execute("SELECT * FROM permits WHERE archived = FALSE ORDER BY id")
    permits = cur.fetchall()
    cur.close()

    today = datetime.today().date()
    threshold = today + timedelta(days=30)
    expiring_count = 0

    for p in permits:
        exp = p.get('expiration_date')
        if isinstance(exp, datetime):
            exp = exp.date()
        p['expiring_soon'] = bool(exp and today <= exp <= threshold)
        if p['expiring_soon'] and not p['archived']:
            expiring_count += 1

    return render_template(
        'permits.html',
        permits=permits,
        show_archived=show_archived,
        expiring_count=expiring_count
    )

# ─── Permit Detail, Comments, Attachments & Audit ─────────────────────
@app.route('/permits/<int:id>', methods=['GET', 'POST'])
@login_required
def permit_detail(id):
    cur = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # Handle comments
    if request.method == 'POST' and 'content' in request.form:
        content = request.form['content']
        cur.execute(
            "INSERT INTO comments (permit_id, user_id, content) VALUES (%s, %s, %s)",
            (id, current_user.id, content)
        )
        cur.execute(
            "INSERT INTO permit_audit (permit_id, user_id, action) VALUES (%s, %s, %s)",
            (id, current_user.id, 'commented')
        )
        db.conn.commit()
    # Handle file upload
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        if file.filename:
            filename = secure_filename(file.filename)
            data = file.read()
            cur.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 AS next_ver FROM attachments WHERE permit_id = %s",
                (id,)
            )
            version = cur.fetchone()['next_ver']
            cur.execute(
                "INSERT INTO attachments (permit_id, filename, file_data, version, uploaded_by)"
                " VALUES (%s, %s, %s, %s, %s)",
                (id, filename, psycopg2.Binary(data), version, current_user.id)
            )
            cur.execute(
                "INSERT INTO permit_audit (permit_id, user_id, action) VALUES (%s, %s, %s)",
                (id, current_user.id, 'attached file')
            )
            db.conn.commit()
            flash(f"Uploaded {filename} (version {version})", 'success')
        else:
            flash('No file selected', 'warning')
    # Fetch data
    cur.execute("SELECT * FROM permits WHERE id = %s", (id,))
    permit = cur.fetchone()
    if not permit:
        cur.close()
        abort(404)
    cur.execute(
        "SELECT c.id, c.content, c.created_at, u.email FROM comments c"
        " JOIN users u ON c.user_id=u.id WHERE c.permit_id=%s ORDER BY c.created_at ASC",
        (id,)
    )
    comments = cur.fetchall()
    cur.execute(
        "SELECT a.id, a.filename, a.version, a.uploaded_at, u.email"
        " FROM attachments a JOIN users u ON a.uploaded_by=u.id"
        " WHERE a.permit_id=%s ORDER BY a.version DESC",
        (id,)
    )
    attachments = cur.fetchall()
    cur.execute(
        "SELECT a.id, a.action, a.timestamp, u.email"
        " FROM permit_audit a JOIN users u ON a.user_id=u.id"
        " WHERE a.permit_id=%s ORDER BY a.timestamp ASC",
        (id,)
    )
    audits = cur.fetchall()
    cur.close()
    return render_template(
        'permit_detail.html',
        permit=permit,
        comments=comments,
        attachments=attachments,
        audits=audits
    )

# ─── Permit Creation ────────────────────────────────────────────────────
@app.route('/permits/new', methods=['GET', 'POST'])
@login_required
def new_permit_form():
    if request.method == 'POST':
        data = request.form
        archived = data.get('archived') == 'on'
        cur = db.conn.cursor()
        cur.execute(
            "INSERT INTO permits (project_number, permit_number, permit_name, agency,"
            " application_date, issue_date, expiration_date, status, archived, created_by)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (
                data['project_number'], data['permit_number'], data.get('permit_name'),
                data.get('agency'), data.get('application_date') or None,
                data.get('issue_date') or None, data.get('expiration_date') or None,
                data.get('status'), archived, current_user.id
            )
        )
        row = cur.fetchone()
        new_id = row['id']
        cur.execute(
            "INSERT INTO permit_audit (permit_id, user_id, action) VALUES (%s,%s,%s)",
            (new_id, current_user.id, 'created')
        )
        db.conn.commit()
        cur.close()
        return redirect(url_for('list_permits'))
    return render_template('permit_form.html', permit=None)

# ─── Permit Editing ─────────────────────────────────────────────────────
@app.route('/permits/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_permit_form(id):
    cur = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        data = request.form
        archived = data.get('archived') == 'on'
        cur.execute(
            "UPDATE permits SET project_number=%s, permit_number=%s, permit_name=%s, agency=%s,"
            " application_date=%s, issue_date=%s, expiration_date=%s, status=%s, archived=%s,"
            " updated_by=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s",
            (
                data['project_number'], data['permit_number'], data.get('permit_name'),
                data.get('agency'), data.get('application_date') or None,
                data.get('issue_date') or None, data.get('expiration_date') or None,
                data.get('status'), archived, current_user.id, id
            )
        )
        cur.execute(
            "INSERT INTO permit_audit (permit_id, user_id, action) VALUES (%s,%s,%s)",
            (id, current_user.id, 'updated')
        )
        db.conn.commit()
        cur.close()
        return redirect(url_for('list_permits'))
    cur.execute("SELECT * FROM permits WHERE id = %s", (id,))
    permit = cur.fetchone()
    cur.close()
    if not permit:
        abort(404)
    return render_template('permit_form.html', permit=permit)

# ─── Permit Deletion ────────────────────────────────────────────────────
@app.route('/permits/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_permit(id):
    cur = db.conn.cursor()
    cur.execute(
        "INSERT INTO permit_audit (permit_id, user_id, action) VALUES (%s,%s,%s)",
        (id, current_user.id, 'deleted')
    )
    cur.execute("DELETE FROM permits WHERE id = %s", (id,))
    db.conn.commit()
    cur.close()
    return redirect(url_for('list_permits'))

# ─── User Management ─────────────────────────────────────────────────────
@app.route('/admin/users')
@login_required
@admin_required
def list_users():
    cur = db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id, email, role FROM users ORDER BY id")
    users = cur.fetchall()
    cur.close()
    return render_template('users.html', users=users)

@app.route('/admin/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        email = request.form['email']
        password_hash = generate_password_hash(request.form['password'])
        role = request.form['role']
        cur = db.conn.cursor()
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (%s,%s,%s)",
            (email, password_hash, role)
        )
        db.conn.commit()
        cur.close()
        return redirect(url_for('list_users'))
    return render_template('user_form.html', user=None)

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    cur = db.conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (id,))
    db.conn.commit()
    cur.close()
    return redirect(url_for('list_users'))

# ─── Run Server ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)