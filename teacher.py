from flask import render_template, request, redirect, url_for, session, flash
from db_config import DatabaseManager, logger, con
import sqlite3

def teacherLogin():
    if request.method == "GET":
        return render_template("teacher/teacherLogin.html")
    else:
        try:
            email = request.form["email"]
            password = request.form["password"]
            
            with DatabaseManager() as cursor:
                cursor.execute("SELECT * FROM teacher WHERE email=? AND password=?", (email, password))
                teacher = cursor.fetchone()
                
                if teacher:
                    session["teacher"] = teacher['tid']  # tid
                    session["teacher_name"] = teacher['name']  # name
                    session["teacher_email"] = teacher['email']  # email
                    logger.info(f"Teacher login successful: {email}")
                    return redirect(url_for("teacherDashboard"))
                else:
                    logger.warning(f"Failed login attempt for teacher: {email}")
                    flash("Invalid credentials", "error")
                    return redirect(url_for("teacherLogin"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error during teacher login: {db_error}")
            flash("A database error occurred during login", "error")
            return redirect(url_for("teacherLogin"))
        except Exception as e:
            logger.error(f"Error during teacher login: {str(e)}")
            flash("An error occurred during login", "error")
            return redirect(url_for("teacherLogin"))
        
# Teacher Signup Function
def validate_contact_number(contact):
    """Validate contact number format"""
    if not contact:
        return False, "Contact number is required"
    
    # Remove any spaces or special characters
    contact = ''.join(filter(str.isdigit, contact))
    
    # Check if it's exactly 10 digits
    if len(contact) != 10:
        return False, "Contact number must be 10 digits"
    
    # Check if it starts with a valid digit (6-9 for Indian numbers)
    if not contact[0] in '6789':
        return False, "Contact number must start with 6, 7, 8, or 9"
    
    return True, contact

def teacherSignup():
    if request.method == "GET":
        return render_template("teacher/teacherSignup.html")
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            branch = request.form["branch"]
            contact = request.form["contact"]

            # Check if passwords match
            if password != confirm_password:
                logger.warning(f"Password mismatch during teacher signup: {email}")
                flash("Passwords do not match.", "error")
                return redirect(url_for("Signup"))

            # Validate contact number
            is_valid, result = validate_contact_number(contact)
            if not is_valid:
                flash(result, "error")
                return redirect(url_for("teacherSignup"))
            contact = result  # Use the sanitized contact number

            with DatabaseManager() as cursor:
                # Check if the email already exists
                cursor.execute("SELECT * FROM teacher WHERE email=?", (email,))
                existing_teacher = cursor.fetchone()
                if existing_teacher:
                    logger.warning(f"Attempted signup with existing email: {email}")
                    flash("Email already registered.", "error")
                    return redirect(url_for("Signup"))

                # Insert new teacher into the database
                cursor.execute(
                    "INSERT INTO teacher (name, email, password, branch, contact) VALUES (?, ?, ?, ?, ?)",
                    (name, email, password, branch, contact)
                )
                logger.info(f"New teacher registered: {email}")
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("teacherLogin"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error during teacher signup: {db_error}")
            flash("A database error occurred during registration", "error")
            return redirect(url_for("Signup"))
        except Exception as e:
            logger.error(f"Error during teacher signup: {str(e)}")
            flash("An error occurred during registration", "error")
            return redirect(url_for("Signup"))


def teacherLogout():
    if "teacher" in session:
        teacher_email = session.get("teacher_email")
        session.pop("teacher", None)
        session.pop("teacher_name", None)
        session.pop("teacher_email", None)
        logger.info(f"Teacher logout: {teacher_email}")
    return redirect(url_for("teacherLogin"))

def teacherDashboard():
    if "teacher" not in session:
        logger.warning("Unauthorized access attempt to teacher dashboard")
        flash("Please login to access the dashboard", "error")
        return redirect(url_for("teacherLogin"))

    try:
        tid = session["teacher"]
        with DatabaseManager() as cursor:
            # Fetch distinct courses assigned to the teacher by joining teacher_subjects, subjects, and courses
            cursor.execute("""
                SELECT DISTINCT c.cid, c.course_name AS name, c.branch
                FROM courses c
                JOIN subjects s ON c.cid = s.course_id
                JOIN teacher_subjects ts ON s.subid = ts.subid
                WHERE ts.tid = ?
            """, (tid,))
            
            # Convert rows to list of dictionaries
            courses = []
            for row in cursor.fetchall():
                course = {
                    'cid': row['cid'],
                    'name': row['name'],
                    'branch': row['branch']
                }
                courses.append(course)
                
            # Get teacher info
            cursor.execute("SELECT * FROM teacher WHERE tid = ?", (tid,))
            teacher_data = cursor.fetchone()
            teacher = {
                'tid': teacher_data['tid'],
                'name': teacher_data['name'],
                'email': teacher_data['email'],
                'branch': teacher_data['branch']
            } if teacher_data else None
            
            # Get subjects taught by the teacher
            cursor.execute("""
                SELECT s.subid, s.subject_name, s.course_id, c.course_name
                FROM subjects s
                JOIN teacher_subjects ts ON s.subid = ts.subid
                JOIN courses c ON s.course_id = c.cid
                WHERE ts.tid = ?
            """, (tid,))
            
            subjects = []
            for row in cursor.fetchall():
                subject = {
                    'subid': row['subid'],
                    'subject_name': row['subject_name'],
                    'course_id': row['course_id'],
                    'course_name': row['course_name']
                }
                subjects.append(subject)
            
            return render_template("teacher/teacherDashboard.html", teacher=teacher, courses=courses, subjects=subjects)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in teacher dashboard: {db_error}")
        flash("A database error occurred while loading the dashboard", "error")
        return redirect(url_for("teacherLogin"))
    except Exception as e:
        logger.error(f"Error in teacher dashboard: {str(e)}")
        flash("An error occurred while loading the dashboard", "error")
        return redirect(url_for("teacherLogin"))

def addAttendance():
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))

    if request.method == "GET":
        cursor = con.cursor()
        tid = session["teacher"]
        
        # Get courses assigned to the teacher by joining teacher_subjects, subjects, and courses
        cursor.execute("""
            SELECT DISTINCT c.cid, c.course_name AS name, c.branch
            FROM courses c
            JOIN subjects s ON c.cid = s.course_id
            JOIN teacher_subjects ts ON s.subid = ts.subid
            WHERE ts.tid = ?
        """, (tid,))
        
        # Convert rows to list of dictionaries
        courses = []
        for row in cursor.fetchall():
            course = {}
            for idx, col in enumerate(cursor.description):
                course[col[0]] = row[idx]
            courses.append(course)
        
        # Get students
        cursor.execute("SELECT * FROM student")
        
        # Convert rows to list of dictionaries
        students = []
        for row in cursor.fetchall():
            student = {}
            for idx, col in enumerate(cursor.description):
                student[col[0]] = row[idx]
            students.append(student)
        
        return render_template("teacher/addAttendance.html", courses=courses, students=students)
    else:
        try:
            selected_date = request.form["date"]
            selected_time = request.form["time"]
            status = request.form["status"]
            student_id = request.form["student"]
            course_id = request.form["course"]
            subid = request.form["subject"]
            tid = session["teacher"]

            cursor = con.cursor()
            sql = "INSERT INTO attendance (sid, tid, cid, subid, date, time, status) VALUES (?, ?, ?, ?, ?, ?, ?)"
            val = (student_id, tid, course_id, subid, selected_date, selected_time, status)
            cursor.execute(sql, val)
            con.commit()
            flash("Attendance recorded successfully.", "success")
            return redirect(url_for("teacherDashboard"))
        except Exception as e:
            flash(f"Error recording attendance: {str(e)}", "error")
            return redirect(url_for("addAttendance"))

def viewAttendance():
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))

    with DatabaseManager() as cursor:
        tid = session["teacher"]
        
        cursor.execute("SELECT * FROM courses WHERE tid=?", (tid,))
        
        # Convert rows to list of dictionaries
        courses = []
        for row in cursor.fetchall():
            course = {}
            for idx, col in enumerate(cursor.description):
                course[col[0]] = row[idx]
            courses.append(course)

        course_id = request.args.get('course')
        date = request.args.get('date')
        
        sql = """
            SELECT a.date, a.time, c.course_name as course_name, s.name as student_name, a.status
            FROM attendance a
            JOIN student s ON a.sid = s.sid
            JOIN courses c ON a.cid = c.cid
            WHERE a.tid = ?
        """
        params = [tid]

        if course_id:
            sql += " AND a.cid = ?"
            params.append(course_id)

        if date:
            sql += " AND DATE(a.date) = ?"
            params.append(date)

        sql += " ORDER BY a.date DESC, a.time DESC"

        cursor.execute(sql, tuple(params))
        
        # Convert rows to list of dictionaries
        records = []
        for row in cursor.fetchall():
            record = {}
            for idx, col in enumerate(cursor.description):
                record[col[0]] = row[idx]
            records.append(record)
    return render_template("teacher/viewAttendance.html", records=records, courses=courses)

def addMarks():
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))
    
    teacher_id = session["teacher"]
    
    try:
        with DatabaseManager() as cursor:
            # Get courses for the teacher by joining teacher_subjects, subjects, and courses
            cursor.execute("""
                SELECT DISTINCT c.cid, c.course_name, c.branch
                FROM courses c
                JOIN subjects s ON c.cid = s.course_id
                JOIN teacher_subjects ts ON s.subid = ts.subid
                WHERE ts.tid = ?
            """, (teacher_id,))
            
            # Convert rows to list of dictionaries
            courses = []
            for row in cursor.fetchall():
                course = {}
                for idx, col in enumerate(cursor.description):
                    course[col[0]] = row[idx]
                courses.append(course)
            print(f"Found {len(courses)} courses for teacher_id {teacher_id}")
            print(f"Courses: {courses}")
            
            # Get all students
            cursor.execute("SELECT * FROM student")
            
            # Convert rows to list of dictionaries
            students = []
            for row in cursor.fetchall():
                student = {}
                for idx, col in enumerate(cursor.description):
                    student[col[0]] = row[idx]
                students.append(student)
            print(f"Found {len(students)} students")
            
            if request.method == "POST":
                course_id = request.form["course"]
                subject_id = request.form["subject"]
                student_id = request.form["student"]
                assessment_type = request.form["assessment_type"]
                marks = request.form["marks"]
                
                print(f"Debug: course_id={course_id}, subject_id={subject_id}, student_id={student_id}, teacher_id={teacher_id}, assessment_type={assessment_type}, marks={marks}")
                
                # Insert marks into database
                cursor.execute("""
                    INSERT INTO marks (sid, cid, subid, tid, assessment_type, marks)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, course_id, subject_id, teacher_id, assessment_type, marks))
                # The commit is handled by DatabaseManager.__exit__
                
                flash("Marks added successfully!", "success")
                return redirect(url_for("teacherDashboard"))
            
            return render_template("teacher/addMarks.html", courses=courses, students=students)
    except Exception as e:
        print(f"Error in addMarks: {str(e)}")
        flash("An error occurred while processing your request.", "error")
        return redirect(url_for("teacherDashboard"))
    # The finally block with cursor.close() is no longer needed as DatabaseManager handles this

# NEW FUNCTION: View Marks
def teacherViewMarks():
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))
    
    tid = session["teacher"]
    
    with DatabaseManager() as cursor:
        # Fetch distinct courses assigned to the teacher by joining teacher_subjects, subjects, and courses
        cursor.execute("""
            SELECT DISTINCT c.cid, c.course_name AS name, c.branch
            FROM courses c
            JOIN subjects s ON c.cid = s.course_id
            JOIN teacher_subjects ts ON s.subid = ts.subid
            WHERE ts.tid = ?
        """, (tid,))
        
        # Convert rows to list of dictionaries
        courses = []
        for row in cursor.fetchall():
            course = {}
            for idx, col in enumerate(cursor.description):
                course[col[0]] = row[idx]
            courses.append(course)

        course_id = request.args.get("course")
        assessment_type = request.args.get("assessment_type")

        sql = """
            SELECT c.course_name as course_name, s.name as student_name,
                   m.assessment_type, m.marks
            FROM marks m
            JOIN student s ON m.sid = s.sid
            JOIN courses c ON m.cid = c.cid
            WHERE m.tid = ?
        """
        params = [tid]

        if course_id:
            sql += " AND m.cid = ?"
            params.append(course_id)

        if assessment_type:
            sql += " AND m.assessment_type = ?"
            params.append(assessment_type)

        sql += " ORDER BY m.marks DESC"

        cursor.execute(sql, tuple(params))
        
        # Convert rows to list of dictionaries
        records = []
        for row in cursor.fetchall():
            record = {}
            for idx, col in enumerate(cursor.description):
                record[col[0]] = row[idx]
            records.append(record)
    
    return render_template("teacher/viewMarks.html", records=records, courses=courses)

def manageSubjects():
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))

    tid = session["teacher"]
    
    with DatabaseManager() as cursor:
        # Get teacher's current subjects
        cursor.execute("""
            SELECT s.subid, s.subject_name, s.semester, c.course_name
            FROM subjects s
            JOIN teacher_subjects ts ON s.subid = ts.subid
            JOIN courses c ON s.course_id = c.cid
            WHERE ts.tid = ?
        """, (tid,))
        
        # Convert rows to list of dictionaries
        teacher_subjects = []
        for row in cursor.fetchall():
            subject = {}
            for idx, col in enumerate(cursor.description):
                subject[col[0]] = row[idx]
            teacher_subjects.append(subject)

        # Get available subjects (subjects not assigned to the teacher)
        cursor.execute("""
            SELECT s.subid, s.subject_name, s.semester, c.course_name
            FROM subjects s
            JOIN courses c ON s.course_id = c.cid
            WHERE s.subid NOT IN (
                SELECT subid FROM teacher_subjects WHERE tid = ?
            )
        """, (tid,))
        
        # Convert rows to list of dictionaries
        available_subjects = []
        for row in cursor.fetchall():
            subject = {}
            for idx, col in enumerate(cursor.description):
                subject[col[0]] = row[idx]
            available_subjects.append(subject)

    return render_template("teacher/manageSubjects.html", 
                         teacher_subjects=teacher_subjects,
                         available_subjects=available_subjects)

def addSubject(subid):
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))

    tid = session["teacher"]

    try:
        with DatabaseManager() as cursor:
            # Check if the subject is already assigned to the teacher
            cursor.execute("SELECT * FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            if cursor.fetchone():
                flash("This subject is already assigned to you", "error")
                return redirect(url_for("teacher_manage_subjects"))

            # Assign the subject to the teacher
            cursor.execute("INSERT INTO teacher_subjects (tid, subid) VALUES (?, ?)", (tid, subid))
            # The commit is handled by DatabaseManager.__exit__
            flash("Subject added successfully", "success")
    except Exception as e:
        flash(f"Error adding subject: {str(e)}", "error")

    return redirect(url_for("teacher_manage_subjects"))

def removeSubject(subid):
    if "teacher" not in session:
        return redirect(url_for("teacherLogin"))

    tid = session["teacher"]

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            # The commit is handled by DatabaseManager.__exit__
            flash("Subject removed successfully", "success")
    except Exception as e:
        flash(f"Error removing subject: {str(e)}", "error")

    return redirect(url_for("teacher_manage_subjects"))

