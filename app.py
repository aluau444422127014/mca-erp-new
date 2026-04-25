from flask import Flask, render_template, request, redirect
import sqlite3

import os
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask, session

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "fallback123") 
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "None"  # 🔥 must
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
# DB create
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    # student table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            regno TEXT,
            admission TEXT,
            year TEXT,
            dept TEXT,
            phone TEXT,
            parent TEXT,
            address TEXT,
            assignment TEXT,
            batch TEXT
        )
    ''')

    # staff table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY,
            name TEXT,
            dept TEXT,
            contact TEXT,
            position TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY,
            date TEXT,
            regno TEXT,
            status TEXT,
            year TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            semester TEXT,
            access_key TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY,
            regno TEXT,
            subject_id INTEGER,
            exam TEXT,
            marks TEXT
        )
    ''')
    conn.commit()
    conn.close()

# call DB init
init_db()


@app.route('/')
def root():
    return redirect('/login')


@app.route('/register')
def register_page():
    return render_template("register.html")


@app.route('/login')
def login_page():
    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")


@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # check existing user
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cur.fetchone()

    if existing_user:
        conn.close()
        return render_template("register.html", error="User already registered!")

    cur.execute("INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
                (name, username, password, role))

    conn.commit()
    conn.close()

    return redirect('/login')


@app.route('/login', methods=['POST'])
def login():

    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND role=?",
        (username, password, role)
    )

    user = cur.fetchone()

    # 🔥 DEBUG PRINT
    print("USER:", user)

    if user:
        session["role"] = role
        session["username"] = username

        # 🔥 FIXED PART (ONLY THIS CHANGED)
        if role == "student":
            cur.execute(
                "SELECT regno FROM students WHERE regno=?",   # ✅ FIX
                (username,)
            )
            data = cur.fetchone()

            print("STUDENT DATA:", data)   # 🔍 DEBUG

            if data:
                session["regno"] = data[0]

        # 🔥 DEBUG SESSION
        print("SESSION AFTER LOGIN:", dict(session))

        conn.close()
        return redirect('/home')

    conn.close()
    return "Invalid Login ❌"

    print("LOGIN FAILED ❌")
    return render_template("login.html", error="Invalid login")

    




@app.route("/add_student", methods=["POST"])
def add_student():

    year = request.form.get("year")

    conn = sqlite3.connect("users.db")   # 🔥 FIX HERE
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO students
    (name, regno, admission, year, dept, phone, parent, address, assignment, batch)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form["regno"],
        request.form["admission"],
        year,
        request.form["dept"],
        request.form["phone"],
        request.form["parent"],
        request.form["address"],
        request.form["assignment"],
        request.form["batch_year"]
    ))

    conn.commit()
    conn.close()

    if year == "1":
        return redirect("/first_year")
    else:
        return redirect("/second_year")


@app.route('/add_staff', methods=['POST'])
def add_staff():
    data = tuple(request.form.values())

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("INSERT INTO staff VALUES (NULL,?,?,?,?)", data)

    conn.commit()
    conn.close()

    return redirect('/staff')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/home')
def home():

    if not session.get("role"):
        return redirect('/login')

    return render_template("home.html")


@app.route('/first_year', methods=['GET', 'POST'])
def first_year():

    selected_year = request.form.get('filter_year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if selected_year:
        cur.execute(
            "SELECT * FROM students WHERE year=? AND batch=?",
            ("1", selected_year)
        )
    else:
        cur.execute(
            "SELECT * FROM students WHERE year=?",
            ("1",)
        )

    students = cur.fetchall()
    conn.close()

    return render_template("first_year.html", students=students)


@app.route('/second_year', methods=['GET', 'POST'])
def second_year():

    selected_year = request.form.get('filter_year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if selected_year:
        cur.execute(
            "SELECT * FROM students WHERE year=? AND batch=?",
            ("2", selected_year)
        )
    else:
        cur.execute(
            "SELECT * FROM students WHERE year=?",
            ("2",)
        )

    students = cur.fetchall()
    conn.close()

    return render_template("second_year.html", students=students)


@app.route('/staff')
def staff():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM staff")
    staff_list = cur.fetchall()

    conn.close()

    return render_template("staff.html", staff=staff_list)


from datetime import date

from datetime import date

# 🔥 ATTENDANCE PAGE
@app.route('/attendance')
def attendance():

    today = date.today()

    # 🔥 student login → no student list load
    if session.get("role") == "student":
        return render_template(
            "attendance.html",
            today=today,
            role="student"
        )

    # 🔥 staff login → allow year selection
    year = request.args.get('year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if year:
        cur.execute(
            "SELECT name, regno FROM students WHERE year=? ORDER BY name",
            (year,)
        )
        students = cur.fetchall()
    else:
        students = []

    conn.close()

    return render_template(
        "attendance.html",
        students=students,
        today=today,
        selected_year=year,
        role="staff"
    )


# 🔥 SAVE ATTENDANCE (STAFF ONLY)
@app.route('/save_attendance', methods=['POST'])
def save_attendance():

    if session.get("role") != "staff":
        return "Access Denied"

    date_val = request.form.get('date')
    year = request.form.get('year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT regno FROM students WHERE year=?", (year,))
    students = cur.fetchall()

    for s in students:
        regno = s[0]

        status = "Present" if f"present_{regno}" in request.form else "Absent"

        cur.execute(
            "INSERT INTO attendance (date, regno, status, year) VALUES (?, ?, ?, ?)",
            (date_val, regno, status, year)
        )

    conn.commit()
    conn.close()

    return redirect('/attendance?year=' + year)


# 🔥 SEARCH ATTENDANCE (SECURE)
@app.route('/search_attendance', methods=['POST'])
def search_attendance():

    search_date = request.form.get('date')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔥 STUDENT → OWN DATA ONLY
    if session.get("role") == "student":

        cur.execute('''
        SELECT date, status 
        FROM attendance
        WHERE date=? AND regno=?
        ''', (search_date, session.get("regno")))

        records = cur.fetchall()

        conn.close()

        return render_template(
            "attendance.html",
            records=records,
            role="student"
        )

    # 🔥 STAFF → FULL DATA
    cur.execute('''
    SELECT students.name, attendance.regno, attendance.status, attendance.date
    FROM attendance
    JOIN students ON attendance.regno = students.regno
    WHERE attendance.date=?
    ''', (search_date,))

    records = cur.fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        records=records,
        role="staff"
    )
    
import os
from flask import request, redirect, send_from_directory

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.context_processor
def inject_data():
    return dict(show_result=show_result)

@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "staff":
        return "Access Denied"

    file = request.files["file"]
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
    return redirect("/materials")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("uploads", filename, as_attachment=True)

@app.route("/timetable", methods=["GET","POST"])
def timetable():
    if request.method == "POST":
        if session.get("role") != "staff":
            return "Access Denied"

        file = request.files["image"]
        file.save("static/timetable.png")

    return render_template("timetable.html")

announcements = []

@app.route("/announcement", methods=["GET","POST"])
def announcement():
    if request.method == "POST":
        if session.get("role") != "staff":
            return "Access Denied"

        file = request.files["image"]
        filename = file.filename
        file.save("static/" + filename)

        from datetime import date
        announcements.append((filename, str(date.today())))

    return render_template("announcement.html", data=announcements[::-1])

results = []
show_result = False   # 🔥 control

@app.route("/result", methods=["GET","POST"])
def result():
    global show_result

    if request.method == "POST":
        if session.get("role") != "staff":
            return "Access Denied"

        name = request.form["name"]
        mark = request.form["mark"]
        results.append((name, mark))

    return render_template("result.html", results=results, show=show_result)

from flask import flash

show_result = False

@app.route("/enable_result")
def enable_result():
    global show_result
    if session.get("role") == "staff":
        show_result = True
        flash("Result Enabled Successfully ✅")
    return redirect("/result")


@app.route("/disable_result")
def disable_result():
    global show_result
    if session.get("role") == "staff":
        show_result = False
        flash("Result Disabled Successfully ❌")
    return redirect("/result")


@app.route("/add_student_page")
def add_student_page():
    year = request.args.get("year")
    return render_template("add_student.html", year=year)


@app.route('/semester')
def semester():
    return render_template("semester.html")

@app.route('/semester/<sem>')
def subject_list(sem):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM subjects WHERE semester=?", (sem,))
    data = cur.fetchall()

    conn.close()
    return render_template("subjects.html", subjects=data, sem=sem)

@app.route('/add_subject', methods=['POST'])
def add_subject():
    name = request.form['name']
    sem = request.form['semester']
    key = request.form['key']

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO subjects (name, semester, access_key) VALUES (?, ?, ?)",
        (name, sem, key)
    )

    conn.commit()
    conn.close()

    return redirect('/semester/' + sem)


@app.route('/open_subject/<int:sid>', methods=['POST'])
def open_subject(sid):

    role = session.get("role")

    # 🔥 STUDENT → no key check
    if role == "student":
        return redirect('/subject/' + str(sid))

    # 🔥 STAFF → key check
    key = request.form.get('key')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT access_key FROM subjects WHERE id=?", (sid,))
    data = cur.fetchone()

    conn.close()

    if data and data[0] == key:
        return redirect('/subject/' + str(sid))
    else:
        return "Wrong Key ❌"

@app.route('/subject/<int:sid>')
def subject_page(sid):

    role = session.get("role")

    # 🔥 GET FILTER VALUES
    batch = request.args.get("batch")
    selected_exam = request.args.get("exam", "IIT1")   # ✅ முக்கியம்

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔥 STUDENTS LOAD (batch filter)
    if batch:
        cur.execute("SELECT name, regno FROM students WHERE batch=?", (batch,))
    else:
        cur.execute("SELECT name, regno FROM students")

    students = cur.fetchall()

    # 🔥 MARKS LOAD
    cur.execute(
        "SELECT regno, exam_type, marks FROM marks WHERE subject_id=?",
        (sid,)
    )
    data = cur.fetchall()

    # 🔥 CONVERT TO DICT
    marks = {}

    for regno, exam_type, mark in data:
        if regno not in marks:
            marks[regno] = {}

        marks[regno][exam_type] = mark

    conn.close()

    # 🔥 DEBUG (optional)
    print("SELECTED EXAM:", selected_exam)
    print("MARKS:", marks)

    return render_template(
        "subject_page.html",
        students=students,
        marks=marks,
        sid=sid,
        role=role,
        selected_exam=selected_exam,   # ✅ pass to HTML
        batch=batch                   # ✅ preserve batch
    )


@app.route('/add_marks', methods=['POST'])
def add_marks():
    regno = request.form['regno']
    name = request.form['name']
    sid = request.form['sid']
    exam = request.form['exam']
    marks = request.form['marks']

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO marks (regno, student_name, subject_id, exam_type, marks)
    VALUES (?, ?, ?, ?, ?)
    """, (regno, name, sid, exam, marks))

    conn.commit()
    conn.close()

    return redirect('/subject/' + sid)


@app.route('/view_marks', methods=['POST'])
def view_marks():
    regno = request.form['regno']

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT student_name, exam_type, marks 
    FROM marks 
    WHERE regno=?
    """, (regno,))

    data = cur.fetchall()
    conn.close()

    return render_template("view_marks.html", data=data, regno=regno)


@app.route('/save_marks', methods=['POST'])
def save_marks():

    if session.get("role") != "staff":
        return "Access Denied"

    sid = request.form.get("sid")
    exam = request.form.get("exam")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔥 all students load
    cur.execute("SELECT regno, name FROM students")
    students = cur.fetchall()

    for s in students:
        regno = s[0]
        name = s[1]

        mark = request.form.get(f"marks_{regno}")

        if mark:

            # 🔥 check existing record
            cur.execute("""
            SELECT id FROM marks 
            WHERE regno=? AND subject_id=? AND exam_type=?
            """, (regno, sid, exam))

            exist = cur.fetchone()

            if exist:
                cur.execute("""
                UPDATE marks SET marks=? WHERE id=?
                """, (mark, exist[0]))
            else:
                cur.execute("""
                INSERT INTO marks (regno, student_name, subject_id, exam_type, marks)
                VALUES (?, ?, ?, ?, ?)
                """, (regno, name, sid, exam, mark))

    conn.commit()
    conn.close()

    return redirect('/subject/' + sid)

# 🚀 RUN
if __name__ == "__main__":
    app.run()