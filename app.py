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


@app.context_processor
def inject_user():
    return dict(role=session.get("role"))

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
    print("🔥 NEW CODE RUNNING SA 🔥")

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

    username = request.form.get('username')   # 👉 regno
    password = request.form.get('password')
    role = request.form.get('role')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔥 username check
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()

    if not user:
        conn.close()
        return render_template("login.html", error="Wrong Username ❌")

    # 🔥 password check
    if user[3] != password:
        conn.close()
        return render_template("login.html", error="Wrong Password ❌")

    # 🔥 role check
    if user[4] != role:
        conn.close()
        return render_template("login.html", error="Wrong Role ❌")

    # 🔥 SUCCESS LOGIN
    session["role"] = role
    session["username"] = username

    # 🔥 STUDENT → regno direct set
    if role == "student":
        session["regno"] = username

        # 👉 optional (year + batch auto fetch)
        cur.execute(
            "SELECT year, batch FROM students WHERE regno=?",
            (username,)
        )
        data = cur.fetchone()

        if data:
            session["year"] = data[0]
            session["batch"] = data[1]

    conn.close()
    return redirect('/home')

    




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

@app.route('/delete_student/<int:id>', methods=['POST'])
def delete_student(id):

    if session.get("role") != "staff":
        return "Unauthorized"

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(request.referrer)  # same pageக்கு திரும்பும்

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

    role = session.get("role")
    regno = request.args.get("regno")   # staff select student

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    student = None
    attendance = []
    marks = []

    # 🔥 STUDENT LOGIN
    if role == "student":

        regno = session.get("regno")

        # student details
        cur.execute("SELECT * FROM students WHERE regno=?", (regno,))
        student = cur.fetchone()

        # attendance
        cur.execute(
            "SELECT date, status FROM attendance WHERE regno=?",
            (regno,)
        )
        attendance = cur.fetchall()

        # marks (JOIN subjects)
        cur.execute("""
        SELECT subjects.name, marks.exam_type, marks.marks
        FROM marks
        JOIN subjects ON marks.subject_id = subjects.id
        WHERE marks.regno=?
        """, (regno,))
        marks = cur.fetchall()


    # 🔥 STAFF LOGIN
    elif role == "staff" and regno:

        # student details
        cur.execute("SELECT * FROM students WHERE regno=?", (regno,))
        student = cur.fetchone()

        # attendance
        cur.execute(
            "SELECT date, status FROM attendance WHERE regno=?",
            (regno,)
        )
        attendance = cur.fetchall()

        # marks
        cur.execute("""
        SELECT subjects.name, marks.exam_type, marks.marks
        FROM marks
        JOIN subjects ON marks.subject_id = subjects.id
        WHERE marks.regno=?
        """, (regno,))
        marks = cur.fetchall()

    conn.close()

    return render_template(
        "home.html",
        student=student,
        attendance=attendance,
        marks=marks,
        role=role
    )


@app.route('/first_year', methods=['GET', 'POST'])
def first_year():

    role = session.get("role")   # 🔥 ADD THIS

    batch = request.form.get('first_year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if batch:
        cur.execute(
            "SELECT * FROM students WHERE year=? AND batch=?",
            ("1", batch)
        )
    else:
        cur.execute("SELECT * FROM students WHERE year=?", ("1",))

    students = cur.fetchall()
    conn.close()

    return render_template(
        "first_year.html",
        students=students,
        role=role   # 🔥 PASS HERE
    )


@app.route('/second_year', methods=['GET', 'POST'])
def second_year():

    role = session.get("role")   # 🔥 ADD THIS

    batch = request.form.get('second_year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if batch:
        cur.execute(
            "SELECT * FROM students WHERE year=? AND batch=?",
            ("2", batch)
        )
    else:
        cur.execute("SELECT * FROM students WHERE year=?", ("2",))

    students = cur.fetchall()
    conn.close()

    return render_template(
        "second_year.html",
        students=students,
        role=role   # 🔥 PASS HERE
    )

@app.route('/delete_staff/<int:id>', methods=['POST'])
def delete_staff(id):

    if session.get("role") != "staff":
        return "Unauthorized ❌"

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM staff WHERE id=?", (id,))  # 🔥 table name check pannunga

    conn.commit()
    conn.close()

    return redirect(request.referrer)

    
@app.route('/staff')
def staff():
    role = session.get("role")
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM staff")
    staff_list = cur.fetchall()

    conn.close()

    return render_template("staff.html", staff=staff_list)


from datetime import date

from datetime import date

# 🔥 ATTENDANCE PAGE
from datetime import date

@app.route('/attendance')
def attendance():

    role = session.get("role")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    students = []
    records = []

    # 🔥 FIX: initialize pannidu
    year = None
    batch = None

    # 🔥 STUDENT VIEW
    if role == "student":
        regno = session.get("regno")

        cur.execute('''
            SELECT date, status
            FROM attendance
            WHERE regno=?
            ORDER BY date DESC
        ''', (regno,))

        records = cur.fetchall()

    # 🔥 STAFF VIEW
    else:
        year = request.args.get("year")
        batch = request.args.get("batch")

        print("YEAR:", year)
        print("BATCH:", batch)

        if year and batch:
            cur.execute(
                "SELECT name, regno FROM students WHERE year=? AND batch=?",
                (year, batch)
            )
            students = cur.fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        students=students,
        records=records,
        role=role,
        today=date.today(),
        selected_year=year,
        selected_batch=batch
    )


# 🔥 SAVE ATTENDANCE (STAFF ONLY)
@app.route('/save_attendance', methods=['POST'])
def save_attendance():

    if session.get("role") != "staff":
        return "Access Denied"

    date_val = request.form.get('date')
    year = request.form.get('year')
    batch = request.form.get('batch')   # ✅ ADD THIS

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # ✅ FIX: filter by BOTH year + batch
    cur.execute(
        "SELECT regno FROM students WHERE year=? AND batch=?",
        (year, batch)
    )
    students = cur.fetchall()

    for s in students:
        regno = s[0]

        status = "Present" if f"present_{regno}" in request.form else "Absent"

        # check already exists
        cur.execute(
            "SELECT id FROM attendance WHERE regno=? AND date=?",
            (regno, date_val)
        )
        exist = cur.fetchone()

        if exist:
            cur.execute(
                "UPDATE attendance SET status=? WHERE id=?",
                (status, exist[0])
            )
        else:
            cur.execute(
                "INSERT INTO attendance (date, regno, status, year) VALUES (?, ?, ?, ?)",
                (date_val, regno, status, year)
            )

    conn.commit()
    conn.close()

    # ✅ FIX: redirect with batch also
    return redirect(f'/attendance?year={year}&batch={batch}')


# 🔥 SEARCH ATTENDANCE (SECURE)
@app.route('/search_attendance', methods=['POST'])
def search_attendance():

    role = session.get("role")
    search_date = request.form.get("date")

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    students = []
    records = []

    print("SEARCH DATE:", search_date)

    if role == "student":
        regno = session.get("regno")

        cur.execute('''
            SELECT date, status
            FROM attendance
            WHERE regno=? AND date=?
        ''', (regno, search_date))

        records = cur.fetchall()

    else:
        cur.execute('''
            SELECT students.name, attendance.regno, attendance.status, attendance.date
            FROM attendance
            JOIN students ON attendance.regno = students.regno
            WHERE attendance.date=?
        ''', (search_date,))

        records = cur.fetchall()

    print("RESULT:", records)

    conn.close()

    return render_template(
        "attendance.html",
        students=students,
        records=records,
        role=role,
        today=date.today()
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

@app.route('/delete_subject/<int:id>', methods=['POST'])
def delete_subject(id):

    if session.get("role") != "staff":
        return "Unauthorized ❌"

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM subjects WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)

    
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