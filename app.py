from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this for security

DB_FILE = "cipher.db"

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- USER AUTHENTICATION ---
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        qualification = request.form["qualification"]
        dob = request.form["dob"]

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO user (username, password, full_name, qualification, dob) VALUES (?, ?, ?, ?, ?)",
                           (username, hashed_password, full_name, qualification, dob))
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists. Try a different one.", "danger")
        finally:
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            flash("Login successful!", "success")
            return redirect(url_for("user_dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")

@app.route("/user")
def user_dashboard():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))  # Ensure "login" is your actual route name

    return render_template("user_dashboard.html", fullname=session.get("full_name"))

@app.route("/user/search", methods=["GET"])
def user_search():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search subjects
    cursor.execute("SELECT * FROM subject WHERE name LIKE ?", (f"%{query}%",))
    subjects = cursor.fetchall()

    # Search quizzes by chapter name
    cursor.execute("""
        SELECT quiz.id, chapter.name AS chapter_name, quiz.date_of_quiz
        FROM quiz 
        JOIN chapter ON quiz.chapter_id = chapter.id
        WHERE chapter.name LIKE ?
    """, (f"%{query}%",))
    quizzes = cursor.fetchall()

    conn.close()

    return render_template("user_search_results.html", query=query, subjects=subjects, quizzes=quizzes)

@app.route("/user/quizzes")
def user_quizzes():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))  # Ensure this redirects to the correct login page

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # ✅ Ensures dictionary-like results
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT quiz.id, quiz.date_of_quiz, quiz.time_duration, quiz.remarks, chapter.name AS chapter_name
        FROM quiz
        JOIN chapter ON quiz.chapter_id = chapter.id
    """)
    quizzes = cursor.fetchall()
    
    print(quizzes)  # ✅ Debugging: See if data is fetched

    conn.close()

    return render_template("user_quizzes.html", quizzes=quizzes)
@app.route("/user/quiz_attempt/<int:quiz_id>")
def quiz_attempt(quiz_id):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch quiz details
    cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()
    
    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for("user_dashboard"))

    # Fetch questions
    cursor.execute("SELECT * FROM question WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()

    conn.close()

    return render_template("quiz_attempt.html", quiz=quiz, questions=questions)


@app.route("/user/submit_quiz/<int:quiz_id>", methods=["POST"])
def submit_quiz(quiz_id):
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch questions
    cursor.execute("SELECT id, correct_option FROM question WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()

    score = 0
    for question in questions:
        user_answer = request.form.get(f"q{question['id']}")
        if user_answer and int(user_answer) == question["correct_option"]:
            score += 1

    # Store score in DB (fix: only insert columns that exist)
    cursor.execute("""
        INSERT INTO score (quiz_id, user_id, total_scored)
        VALUES (?, ?, ?)
    """, (quiz_id, session["user_id"], score))

    conn.commit()
    conn.close()

    flash(f"Quiz submitted! Your score: {score}/{len(questions)}", "success")
    return redirect(url_for("user_dashboard"))


@app.route("/user/scores")
def user_scores():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT score.quiz_id, chapter.name AS quiz_name, score.total_scored, score.time_stamp_of_attempt
    FROM score
    JOIN quiz ON score.quiz_id = quiz.id
    JOIN chapter ON quiz.chapter_id = chapter.id
    WHERE score.user_id = ?
    ORDER BY score.time_stamp_of_attempt DESC
""", (session["user_id"],))
    scores = cursor.fetchall()
    conn.close()

    return render_template("user_scores.html", scores=scores)

@app.route("/user/quiz_summary")
def quiz_summary():
    if "user_id" not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch quiz summary: total quizzes attempted, total score, and average score
    cursor.execute("""
        SELECT COUNT(DISTINCT quiz_id) AS total_quizzes,
               SUM(total_scored) AS total_score,
               AVG(total_scored) AS avg_score
        FROM score
        WHERE user_id = ?
    """, (session["user_id"],))
    summary = cursor.fetchone()

    # Fetch the best & worst quiz performance
    cursor.execute("""
        SELECT chapter.name AS quiz_name, score.total_scored
        FROM score
        JOIN quiz ON score.quiz_id = quiz.id
        JOIN chapter ON quiz.chapter_id = chapter.id
        WHERE score.user_id = ?
        ORDER BY total_scored DESC LIMIT 1
    """, (session["user_id"],))
    best_quiz = cursor.fetchone()

    cursor.execute("""
        SELECT chapter.name AS quiz_name, score.total_scored
        FROM score
        JOIN quiz ON score.quiz_id = quiz.id
        JOIN chapter ON quiz.chapter_id = chapter.id
        WHERE score.user_id = ?
        ORDER BY total_scored ASC LIMIT 1
    """, (session["user_id"],))
    worst_quiz = cursor.fetchone()

    conn.close()

    return render_template("quiz_summary.html", summary=summary, best_quiz=best_quiz, worst_quiz=worst_quiz)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("home"))

# --- ADMIN AUTHENTICATION ---
# ADMIN LOGINA ND CO
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM admin WHERE username = ?", (username,))
        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password"], password):
            session["admin"] = username  # ✅ Keep username for consistency
            session["admin_id"] = admin["id"]  # ✅ Store admin ID for authentication
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid admin credentials.", "danger")

    return render_template("admin_login.html")

@app.route("/admin/search", methods=["GET"])
def admin_search():
    if "admin_id" not in session:
        flash("Please log in as Admin.", "warning")
        return redirect(url_for("admin_login"))

    query = request.args.get("q", "").strip()
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Search in users, subjects, quizzes, and questions
    cursor.execute("SELECT * FROM user WHERE username LIKE ?", (f"%{query}%",))

    users = cursor.fetchall()

    cursor.execute("SELECT * FROM subject WHERE name LIKE ?", (f"%{query}%",))
    subjects = cursor.fetchall()

    cursor.execute("""
        SELECT quiz.id, chapter.name AS chapter_name, quiz.date_of_quiz
        FROM quiz 
        JOIN chapter ON quiz.chapter_id = chapter.id
        WHERE chapter.name LIKE ?
    """, (f"%{query}%",))
    quizzes = cursor.fetchall()

    cursor.execute("SELECT * FROM question WHERE question_statement LIKE ?", (f"%{query}%",))
    questions = cursor.fetchall()

    conn.close()

    return render_template("admin_search_results.html", query=query, users=users, subjects=subjects, quizzes=quizzes, questions=questions)

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all subjects
    cursor.execute("SELECT * FROM subject")
    subjects = cursor.fetchall()

    # Fetch all chapters
    cursor.execute("SELECT * FROM chapter")
    chapters = cursor.fetchall()

    # Fetch all quizzes with chapter names
    cursor.execute("""
        SELECT quiz.id, quiz.chapter_id, quiz.date_of_quiz, quiz.time_duration, quiz.remarks, chapter.name AS chapter_name
        FROM quiz
        JOIN chapter ON quiz.chapter_id = chapter.id
    """)
    quizzes = cursor.fetchall()

    print("DEBUG: Quizzes fetched ->", quizzes)  # Debugging line

    conn.close()

    return render_template("admin_dashboard.html", subjects=subjects, chapters=chapters, quizzes=quizzes)



@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("admin_login"))

# --- ADMIN: MANAGE USERS ---
@app.route("/admin/manage-users")
def manage_users():
    if "admin" not in session:
        flash("Access denied!", "danger")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, qualification, dob FROM user")
    users = cursor.fetchall()
    conn.close()
    
    return render_template("manage_users.html", users=users)
    



@app.route("/admin/delete-user/<int:user_id>")
def delete_user(user_id):
    if "admin" not in session:
        flash("Access denied!", "danger")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash("User deleted successfully.", "success")
    return redirect(url_for("manage_users"))
### 🟢 Admin: View All Subjects
@app.route("/admin/admin_subjects")
def admin_subjects():
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subject")
    subjects = cursor.fetchall()
    conn.close()

    return render_template("admin_subjects.html", subjects=subjects)


### 🟢 Admin: Add Subject
@app.route("/admin/subjects/add", methods=["GET", "POST"])
def add_subject():
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO subject (name, description) VALUES (?, ?)", (name, description))
            conn.commit()
            flash("Subject added successfully!", "success")
        except sqlite3.IntegrityError:
            flash("Subject with this name already exists.", "danger")
        finally:
            conn.close()

        return redirect(url_for("admin_subjects"))

    return render_template("add_subject.html")


### 🟢 Admin: Edit Subject
@app.route("/admin/subjects/edit/<int:id>", methods=["GET", "POST"])
def edit_subject(id):
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subject WHERE id = ?", (id,))
    subject = cursor.fetchone()

    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for("admin_subjects"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]

        cursor.execute("UPDATE subject SET name = ?, description = ? WHERE id = ?", (name, description, id))
        conn.commit()
        conn.close()
        flash("Subject updated successfully!", "success")
        return redirect(url_for("admin_subjects"))

    conn.close()
    return render_template("edit_subject.html", subject=subject)


### 🟢 Admin: Delete Subject
@app.route("/admin/subjects/delete/<int:id>")
def delete_subject(id):
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subject WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Subject deleted successfully!", "success")
    return redirect(url_for("admin_subjects"))
# --- CHAPTER MANAGEMENT ---

@app.route("/admin/chapters/<int:subject_id>", methods=["GET", "POST"])
def admin_chapters(subject_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch subject details
    cursor.execute("SELECT * FROM subject WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()

    # Fetch all chapters for the given subject
    cursor.execute("SELECT * FROM chapter WHERE subject_id = ?", (subject_id,))
    chapters = cursor.fetchall()
    conn.close()

    return render_template("admin_chapters.html", subject=subject, chapters=chapters)

# --- ADD CHAPTER ---
@app.route("/admin/add_chapter/<int:subject_id>", methods=["POST"])
def add_chapter(subject_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    chapter_name = request.form["name"]
    chapter_description = request.form["description"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chapter (subject_id, name, description) VALUES (?, ?, ?)",
                   (subject_id, chapter_name, chapter_description))
    conn.commit()
    conn.close()

    flash("Chapter added successfully!", "success")
    return redirect(url_for("admin_chapters", subject_id=subject_id))

# --- EDIT CHAPTER ---
@app.route("/admin/edit_chapter/<int:chapter_id>", methods=["POST"])
def edit_chapter(chapter_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    chapter_name = request.form["name"]
    chapter_description = request.form["description"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE chapter SET name = ?, description = ? WHERE id = ?",
                   (chapter_name, chapter_description, chapter_id))
    conn.commit()
    conn.close()

    flash("Chapter updated successfully!", "success")
    return redirect(request.referrer)

# --- DELETE CHAPTER ---
@app.route("/admin/delete_chapter/<int:chapter_id>/<int:subject_id>", methods=["POST"])
def delete_chapter(chapter_id, subject_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chapter WHERE id = ?", (chapter_id,))
    conn.commit()
    conn.close()

    flash("Chapter deleted successfully!", "success")
    return redirect(url_for("admin_chapters", subject_id=subject_id))

@app.route("/admin/quizzes")
def admin_quizzes():
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT quiz.id, quiz.date_of_quiz, quiz.time_duration, quiz.remarks, chapter.name AS chapter_name 
        FROM quiz 
        JOIN chapter ON quiz.chapter_id = chapter.id
    """)
    quizzes = cursor.fetchall()

    # Debugging: Print all quizzes to see if multiple are fetched
    print("Fetched Quizzes:", quizzes)

    conn.close()

    return render_template("admin_quizzes.html", quizzes=quizzes)

@app.route("/admin/quiz/add", methods=["GET", "POST"])
def admin_add_quiz():
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        chapter_id = request.form.get("chapter_id")
        date_of_quiz = request.form.get("date_of_quiz")
        time_duration = request.form.get("time_duration")
        remarks = request.form.get("remarks")

        if not chapter_id or not date_of_quiz or not time_duration:
            flash("All fields are required!", "danger")
        else:
            cursor.execute(
                "INSERT INTO quiz (chapter_id, date_of_quiz, time_duration, remarks) VALUES (?, ?, ?, ?)",
                (chapter_id, date_of_quiz, time_duration, remarks),
            )
            conn.commit()
            flash("Quiz added successfully!", "success")
            return redirect(url_for("admin_quizzes"))

    cursor.execute("SELECT id, name FROM chapter")
    chapters = cursor.fetchall()
    conn.close()

    return render_template("admin_add_quiz.html", chapters=chapters)

@app.route("/admin/edit_quiz/<int:quiz_id>", methods=["GET", "POST"])
def admin_edit_quiz(quiz_id):
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()

    cursor.execute("SELECT id, name FROM chapter")
    chapters = cursor.fetchall()

    if request.method == "POST":
        chapter_id = request.form.get("chapter_id")
        date_of_quiz = request.form.get("date_of_quiz")
        time_duration = request.form.get("time_duration")
        remarks = request.form.get("remarks")

        if not time_duration:
            flash("Time Duration is required!", "danger")
            return render_template("admin_edit_quiz.html", quiz=quiz, chapters=chapters)

        cursor.execute(
            "UPDATE quiz SET chapter_id = ?, date_of_quiz = ?, time_duration = ?, remarks = ? WHERE id = ?",
            (chapter_id, date_of_quiz, time_duration, remarks, quiz_id),
        )
        conn.commit()
        conn.close()

        flash("Quiz updated successfully!", "success")
        return redirect(url_for("admin_quizzes"))

    conn.close()
    return render_template("admin_edit_quiz.html", quiz=quiz, chapters=chapters)

@app.route("/admin/delete_quiz/<int:quiz_id>")
def admin_delete_quiz(quiz_id):
    if "admin_id" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM quiz WHERE id = ?", (quiz_id,))
    conn.commit()
    conn.close()

    flash("Quiz deleted successfully!", "danger")
    return redirect(url_for("admin_quizzes"))
# ------------------------- ADMIN QUESTION MANAGEMENT -------------------------

# --- VIEW QUESTIONS UNDER A QUIZ ---
@app.route("/admin/questions/<int:quiz_id>")
def admin_questions(quiz_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quiz WHERE id = ?", (quiz_id,))
    quiz = cursor.fetchone()

    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor.execute("SELECT * FROM question WHERE quiz_id = ?", (quiz_id,))
    questions = cursor.fetchall()
    conn.close()

    return render_template("admin_questions.html", quiz=quiz, questions=questions)

# --- ADD QUESTION ---
@app.route("/admin/questions/add/<int:quiz_id>", methods=["GET", "POST"])
def admin_add_question(quiz_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        question_statement = request.form["question_statement"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_option = int(request.form["correct_option"])

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO question (quiz_id, question_statement, option1, option2, option3, option4, correct_option) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (quiz_id, question_statement, option1, option2, option3, option4, correct_option))
        conn.commit()
        conn.close()

        flash("Question added successfully!", "success")
        return redirect(url_for("admin_questions", quiz_id=quiz_id))

    return render_template("admin_add_question.html", quiz_id=quiz_id)

# --- EDIT QUESTION ---
@app.route("/admin/questions/edit/<int:question_id>", methods=["GET", "POST"])
def admin_edit_question(question_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM question WHERE id = ?", (question_id,))
    question = cursor.fetchone()

    if not question:
        flash("Question not found!", "danger")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        question_statement = request.form["question_statement"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_option = int(request.form["correct_option"])

        cursor.execute("""
            UPDATE question SET question_statement=?, option1=?, option2=?, option3=?, option4=?, correct_option=? 
            WHERE id=?
        """, (question_statement, option1, option2, option3, option4, correct_option, question_id))
        conn.commit()
        conn.close()

        flash("Question updated successfully!", "success")
        return redirect(url_for("admin_questions", quiz_id=question["quiz_id"]))

    conn.close()
    return render_template("admin_edit_question.html", question=question)

# --- DELETE QUESTION ---
@app.route("/admin/questions/delete/<int:question_id>", methods=["POST"])
def admin_delete_question(question_id):
    if "admin" not in session:
        flash("Please log in as an admin first.", "warning")
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quiz_id FROM question WHERE id = ?", (question_id,))
    question = cursor.fetchone()

    if not question:
        flash("Question not found!", "danger")
        return redirect(url_for("admin_dashboard"))

    cursor.execute("DELETE FROM question WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()

    flash("Question deleted successfully!", "success")
    return redirect(url_for("admin_questions", quiz_id=question["quiz_id"]))

# Run Flask App
if __name__ == "__main__":
    app.run(debug=True)
