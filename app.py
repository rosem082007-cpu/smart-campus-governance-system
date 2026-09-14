from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_file
)
from email_service import send_email

from werkzeug.utils import secure_filename
from matplotlib import category
from openpyxl import Workbook
from database import create_table, get_db

from ai_model import (
    predict_category,
    predict_priority,
    check_duplicate,
    estimate_resolution
)

from datetime import datetime, timedelta
from flask import Flask
import os

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

print("Database Path:", os.path.abspath("campus.db"))

app.secret_key = "smart-campus-secret"

create_table()

# ---------------- HOME / ROLE SELECT ----------------

@app.route("/")
def home():

    return render_template("role_select.html")


# ---------------- STUDENT LOGIN ----------------

@app.route("/student-login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        db = get_db()

        # Check student by email
        user = db.execute("""
            SELECT *
            FROM users
            WHERE username = ?
            AND role = 'student'
        """, (email,)).fetchone()

        # Existing student
        if user:

            if user["password"] != password:

                db.close()

                return render_template(
                    "login.html",
                    error="❌ Invalid email or password"
                )

            session["username"] = user["username"]
            session["role"] = "student"
            session["name"] = user["name"]

            db.close()

            return redirect("/student")


        # New student → automatically create
        db.execute("""
            INSERT INTO users
            (username, password, role, name)
            VALUES (?, ?, ?, ?)
        """, (
            email,
            password,
            "student",
            name
        ))

        db.commit()

        session["username"] = email
        session["role"] = "student"
        session["name"] = name

        db.close()

        return redirect("/student")

    return render_template("login.html")


# ---------------- ADMIN LOGIN ----------------

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()

        admin = db.execute("""
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
            AND role = 'admin'
        """, (username, password)).fetchone()

        db.close()

        if admin:

            session["username"] = admin["username"]
            session["role"] = "admin"
            session["name"] = admin["name"]

            return redirect("/admin")

        return render_template(
            "admin_login.html",
            error="❌ Invalid admin username or password"
        )

    return render_template("admin_login.html")

# ---------------- STUDENT ----------------

@app.route("/student")
def student():

    if session.get("role") != "student":
        return redirect("/")

    return render_template(
        "student.html",
        name=session.get("name")
    )

# ---------------- COMPLAINT ----------------

@app.route("/complaint")
def complaint():

    if session.get("role") != "student":
        return redirect("/")

    return render_template("complaint.html")

#----------Submit-----------

@app.route("/submit", methods=["POST"])
def submit():

    if session.get("role") != "student":
        return redirect("/")

    name = session.get("name")
    department = request.form["department"]
    location = request.form["location"]
    other_location = request.form.get("otherLocation", "")

    if location == "Other":
        location = other_location

    description = request.form["description"]
    email = request.form['email']
    photo = request.files["photo"]

    category = predict_category(description)
    priority = predict_priority(description)
    estimated_time = estimate_resolution(category)

    db = get_db()

    old_complaints = db.execute(
        "SELECT * FROM complaints"
    ).fetchall()

    duplicate = check_duplicate(
        description,
        old_complaints
    )

    if duplicate:
        db.close()
        return render_template("duplicate.html")

    # Current Time
    created_at = datetime.now().isoformat()

    # Upload Photo
    photo_name = ""

    if photo and photo.filename != "":

        photo_name = secure_filename(photo.filename)

        photo.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                photo_name
            )
        )

    # Insert Complaint
    cursor = db.execute("""
        INSERT INTO complaints
        (
            student_name,
            department,
            location,
            description,
            category,
            priority,
            created_at,
            escalated,
            photo,
            email
        )
         VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (
        name,
        department,
        location,
        description,
        category,
        priority,
        created_at,
        photo_name,
        email
    ))

    complaint_id = cursor.lastrowid

    # Notification
    db.execute("""
        INSERT INTO notifications
        (
            message,
            status,
            created_at
        )
        VALUES (?, ?, ?)
    """, (
        f"📩 {name} submitted a {category} complaint.",
        "Unread",
        datetime.now().isoformat()
    ))

    # High Priority Notification
    if priority.startswith("High"):

        db.execute("""
            INSERT INTO notifications
            (
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            f"🚨 High Priority\n{name} submitted a {category} complaint.",
            "Unread",
            datetime.now().isoformat()
        ))

    db.commit()
    db.close()

    return render_template(
        "success.html",
        complaint_id=complaint_id,
        category=category,
        priority=priority
    )

    # ---------------- Notifications ----------------

    db.execute("""
        INSERT INTO notifications
        (message, status, created_at)
        VALUES (?, ?, ?)
    """, (
        f"📩 New complaint submitted by {name}",
        "Unread",
        datetime.now().isoformat()
    ))

    if priority.startswith("High"):

        db.execute("""
            INSERT INTO notifications
            (message, status, created_at)
            VALUES (?, ?, ?)
        """, (
            f"🚨 High Priority Complaint - {name}",
            "Unread",
            datetime.now().isoformat()
        ))

    db.commit()
    db.close()

    return render_template(
        "success.html",
        complaint_id=complaint_id,
        category=category,
        priority=priority
    )

@app.route("/status")
def status():

    if session.get("role") != "student":
        return redirect("/")

    db = get_db()

    complaints = db.execute("""
        SELECT *
        FROM complaints
        WHERE student_name = ?
        ORDER BY id DESC
    """, (session.get("name"),)).fetchall()

    # Convert sqlite rows to dictionary
    complaints = [dict(c) for c in complaints]

    # Format submitted date
    for c in complaints:
        if c["created_at"]:
            dt = datetime.fromisoformat(c["created_at"])
            c["formatted_date"] = dt.strftime("%d-%b-%Y %I:%M %p")
        else:
            c["formatted_date"] = "N/A"

    db.close()

    return render_template(
        "status.html",
        complaints=complaints
    )


# ---------------- ADMIN ----------------

@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()

    # ---------------- AUTO ESCALATION ----------------

    old_time = (
        datetime.now() - timedelta(hours=24)
    ).isoformat()

    db.execute("""
        UPDATE complaints
        SET status='Escalated',
            escalated=1
        WHERE priority LIKE 'High%'
        AND status='Pending'
        AND created_at IS NOT NULL
        AND created_at < ?
    """, (old_time,))

    db.commit()

    # ---------------- SEARCH & FILTER ----------------

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    priority = request.args.get("priority", "").strip()
    status = request.args.get("status", "").strip()

    query = """
        SELECT *
        FROM complaints
        WHERE 1=1
    """

    params = []

    if search:

        query += """
            AND (
                student_name LIKE ?
                OR department LIKE ?
                OR location LIKE ?
                OR description LIKE ?
            )
        """

        value = f"%{search}%"

        params.extend([
            value,
            value,
            value,
            value
        ])

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")

    if priority:
        query += " AND priority LIKE ?"
        params.append(f"%{priority}%")

    if status:
        query += " AND status=?"
        params.append(status)

    query += " ORDER BY id DESC"

    complaints = db.execute(
        query,
        params
    ).fetchall()

    # ---------------- NOTIFICATIONS ----------------

    notifications = db.execute("""
        SELECT *
        FROM notifications
        WHERE status='Unread'
        ORDER BY id DESC
    """).fetchall()

    notifications = [
        dict(n) for n in notifications
    ]

    count = len(notifications)

    # ---------------- NOTIFICATION TIME ----------------

    now = datetime.now()

    for n in notifications:

        if n.get("created_at"):

            dt = datetime.fromisoformat(
                n["created_at"]
            )

            diff = now - dt

            if diff.total_seconds() < 60:

                n["time"] = "🕒 Just now"

            elif diff.total_seconds() < 3600:

                mins = int(
                    diff.total_seconds() // 60
                )

                n["time"] = f"🕒 {mins} min ago"

            elif dt.date() == now.date():

                n["time"] = (
                    "🕒 Today "
                    + dt.strftime("%I:%M %p")
                )

            elif dt.date() == (
                now.date() - timedelta(days=1)
            ):

                n["time"] = (
                    "🕒 Yesterday "
                    + dt.strftime("%I:%M %p")
                )

            else:

                n["time"] = dt.strftime(
                    "🕒 %d-%b-%Y %I:%M %p"
                )

    # ---------------- MARK NOTIFICATIONS AS READ ----------------

    db.execute("""
        UPDATE notifications
        SET status='Read'
        WHERE status='Unread'
    """)

    db.commit()

    # ---------------- CLOSE DATABASE ----------------

    db.close()

    # ---------------- RETURN ADMIN PAGE ----------------

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        search=search,
        selected_category=category,
        selected_priority=priority,
        selected_status=status,
        notifications=notifications,
        count=count
    )
# ---------------- SETTINGS ----------------

@app.route("/settings", methods=["GET", "POST"])
def settings():

    if not session.get("role"):
        return redirect("/")

    db = get_db()

    if request.method == "POST":

        name = request.form["name"]
        username = request.form["username"]

        db.execute("""
            UPDATE users
            SET name = ?, username = ?
            WHERE id = ?
        """, (
            name,
            username,
            session.get("user_id")
        ))

        db.commit()

        session["name"] = name
        session["username"] = username

        db.close()

        return redirect("/settings")

    user = db.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (
        session.get("user_id"),
    )).fetchone()

    db.close()

    return render_template(
        "settings.html",
        user=user
    )


#---------------EXPORT-----------------

@app.route("/export")
def export_excel():

    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()

    complaints = db.execute(
        "SELECT * FROM complaints"
    ).fetchall()

    db.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Complaints"

    ws.append([
        "ID",
        "Student",
        "Department",
        "Description",
        "Category",
        "Priority",
        "Status",
        "Created At"
    ])

    for c in complaints:
        ws.append([
            c["id"],
            c["student_name"],
            c["department"],
            c["description"],
            c["category"],
            c["priority"],
            c["status"],
            c["created_at"]
        ])

    filename = "complaints.xlsx"
    wb.save(filename)

    return send_file(
        filename,
        as_attachment=True
    )
#-----------------DELETE--------------

@app.route("/delete/<int:id>")
def delete_complaint(id):
    db = get_db()

    db.execute(
        "DELETE FROM complaints WHERE id = ?",
        (id,)
    )

    db.commit()
    db.close()

    return redirect("/admin")

#-------------RESOLVE--------------

@app.route('/resolve/<int:id>')
def resolve(id):

    db = get_db()

    complaint = db.execute(
        "SELECT * FROM complaints WHERE id=?",
        (id,)
    ).fetchone()

    db.execute(
        "UPDATE complaints SET status='Resolved' WHERE id=?",
        (id,)
    )

    db.commit()

    if complaint["email"]:
        send_email(
            complaint["email"],
            complaint["student_name"],      
            complaint["id"],
            complaint["category"]
        )

    return redirect('/admin')

#---------------ANALYTICS------------

@app.route("/analytics")
def analytics():

    db = get_db()

    complaints = db.execute("""
        SELECT * FROM complaints
    """).fetchall()

    db.close()

    # -----------------------------
    # BASIC COUNTS
    # -----------------------------

    total = len(complaints)

    pending = sum(
        1 for c in complaints
        if c["status"] == "Pending"
    )

    resolved = sum(
        1 for c in complaints
        if c["status"] == "Resolved"
    )

    high = sum(
        1 for c in complaints
        if c["priority"].startswith("High")
    )

    # -----------------------------
    # HEALTH SCORE
    # -----------------------------

    if total > 0:
        health_score = int((resolved / total) * 100)
    else:
        health_score = 100

    # -----------------------------
    # CATEGORY DATA
    # -----------------------------

    category_dict = {}

    for c in complaints:

        category = c["category"]

        if category:
            category_dict[category] = \
                category_dict.get(category, 0) + 1

    category_labels = list(category_dict.keys())
    category_counts = list(category_dict.values())

    # -----------------------------
    # PRIORITY DATA
    # -----------------------------

    priority_dict = {}

    for c in complaints:

        priority = c["priority"]

        if priority:
            priority_dict[priority] = \
                priority_dict.get(priority, 0) + 1

    priority_labels = list(priority_dict.keys())
    priority_counts = list(priority_dict.values())

    # -----------------------------
    # DEPARTMENT DATA
    # -----------------------------

    department_dict = {}

    for c in complaints:

        department = c["department"]

        if department:
            department_dict[department] = \
                department_dict.get(department, 0) + 1

    department_labels = list(department_dict.keys())
    department_counts = list(department_dict.values())

    # -----------------------------
    # SEND DATA TO HTML
    # -----------------------------

    return render_template(
        "analytics.html",

        health_score=health_score,

        total=total,
        pending=pending,
        resolved=resolved,
        high=high,

        category_labels=category_labels,
        category_counts=category_counts,

        priority_labels=priority_labels,
        priority_counts=priority_counts,

        department_labels=department_labels,
        department_counts=department_counts
    )

#------------FEEDBACK---------------


@app.route("/feedback/<int:id>", methods=["GET", "POST"])
def feedback(id):

    if session.get("role") != "student":
        return redirect("/")

    db = get_db()

    if request.method == "POST":

        rating = request.form["rating"]
        feedback = request.form["feedback"]

        db.execute(
            """
            UPDATE complaints
            SET rating=?, feedback=?
            WHERE id=?
            """,
            (rating, feedback, id)
        )

        db.commit()
        db.close()

        return redirect("/status")

    db.close()

    return render_template(
        "feedback.html",
        complaint_id=id
    )

#-----------------DELETE ALL COMPLAINTS----------------

@app.route("/delete_all")
def delete_all():

    if session.get("role") != "admin":
        return redirect("/")

    db = get_db()

    db.execute("DELETE FROM complaints")

    db.execute("DELETE FROM sqlite_sequence WHERE name='complaints'")

    db.commit()
    db.close()

    return redirect("/admin")

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)