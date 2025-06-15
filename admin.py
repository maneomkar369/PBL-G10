from flask import render_template, request, redirect, url_for, session, flash
from db_config import DatabaseManager, logger
import sqlite3

# ------------------ Admin Login --------------------
def adminLogin():
    if request.method == "GET":
        return render_template("admin/adminLogin.html")
    else:
        try:
            username = request.form["username"]
            password = request.form["password"]
            
            with DatabaseManager() as cursor:
                sql = "SELECT * FROM admin WHERE username = ? AND password = ?"
                val = (username, password)
                cursor.execute(sql, val)
                admin = cursor.fetchone()
                
                if admin:
                    session["admin"] = admin['username']  # Using column name with row_factory
                    logger.info(f"Admin login successful: {username}")
                    return redirect(url_for("adminDashboard"))
                else:
                    flash("Invalid username or password", "error")
                    logger.warning(f"Failed login attempt for admin: {username}")
                    return redirect(url_for("adminLogin"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error during admin login: {db_error}")
            flash("A database error occurred during login", "error")
            return redirect(url_for("adminLogin"))
        except Exception as e:
            logger.error(f"Error during admin login: {str(e)}")
            flash("An error occurred during login", "error")
            return redirect(url_for("adminLogin"))

# ------------------ Admin Logout --------------------
def adminLogout():
    if "admin" in session:
        admin_username = session["admin"]
        session.pop("admin", None)
        logger.info(f"Admin logout: {admin_username}")
    return redirect(url_for("adminLogin"))

# ------------------ Admin Dashboard --------------------
def adminDashboard():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to admin dashboard")
        flash("Please login to access the dashboard", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("SELECT * FROM student")
            students = cursor.fetchall()

            # Convert to list of dictionaries for template compatibility
            student_list = []
            for student in students:
                student_dict = {
                    'sid': student['sid'],
                    'name': student['name'],
                    'email': student['email'],
                    'contact': student['contact'],
                    'course': student['course'],
                    'profile_picture': student['profile_picture']
                }
                student_list.append(student_dict)

        # Get admin info
        with DatabaseManager() as admin_cursor:
            admin_cursor.execute("SELECT * FROM admin WHERE username = ?", (session['admin'],))
            admin_data = admin_cursor.fetchone()
            admin = {'username': admin_data['username']} if admin_data else None

        return render_template("admin/adminDashboard.html", admin=admin, students=student_list)
    
    except sqlite3.Error as db_error:
        logger.error(f"Database error in admin dashboard: {db_error}")
        flash("A database error occurred while loading the dashboard", "error")
        return redirect(url_for("adminLogin"))
    
    except Exception as e:
        logger.error(f"Error in admin dashboard: {str(e)}")
        flash("An error occurred while loading the dashboard", "error")
        return redirect(url_for("adminDashboard"))  # Redirect to dashboard instead of login on general errors
def manageCourses():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage courses")
        flash("Please login to access course management", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            cursor.execute("SELECT * FROM courses ORDER BY course_name")
            courses_data = cursor.fetchall()
            
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data['cid'],
                    'course_name': course_data['course_name']
                }
                courses.append(course)
                
            return render_template("admin/manageCourses.html", courses=courses)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manage courses: {db_error}")
        flash("A database error occurred while loading courses", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manage courses: {str(e)}")
        flash("An error occurred while loading courses", "error")
        return redirect(url_for("adminDashboard"))

def addCourse():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add course")
        flash("Please login to add courses", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "POST":
        course_name = request.form.get("course_name")
        if course_name:
            try:
                with DatabaseManager() as cursor:
                    cursor.execute("INSERT INTO courses (course_name) VALUES (?)", (course_name,))
                    logger.info(f"Course added: {course_name}")
                    flash("Course added successfully", "success")
            except sqlite3.Error as db_error:
                logger.error(f"Database error adding course: {db_error}")
                flash(f"Database error adding course: {str(db_error)}", "error")
            except Exception as e:
                logger.error(f"Error adding course: {str(e)}")
                flash(f"Error adding course: {str(e)}", "error")
        else:
            logger.warning("Attempted to add course with empty name")
            flash("Course name is required", "error")
            
    return redirect(url_for("manageCourses"))

def deleteCourse(cid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to delete course {cid}")
        flash("Please login to delete courses", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            # First check if there are students enrolled in this course
            cursor.execute("SELECT COUNT(*) as count FROM student WHERE course = ?", (cid,))
            result = cursor.fetchone()
            if result and result['count'] > 0:
                logger.warning(f"Attempted to delete course {cid} with enrolled students")
                flash("Cannot delete course with enrolled students", "error")
                return redirect(url_for("manageCourses"))
                
            cursor.execute("DELETE FROM courses WHERE cid = ?", (cid,))
            logger.info(f"Course deleted: {cid}")
            flash("Course deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error deleting course {cid}: {db_error}")
        flash(f"Database error deleting course: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting course {cid}: {str(e)}")
        flash(f"Error deleting course: {str(e)}", "error")
        
    return redirect(url_for("manageCourses"))

# ------------------ Manage Subjects --------------------
def manageSubjects():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage subjects")
        flash("Please login to access subject management", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            # Fetch all subjects with course names
            cursor.execute("""
                SELECT s.subid, s.subject_name, c.course_name, s.semester
                FROM subjects s
                JOIN courses c ON s.course_id = c.cid
                ORDER BY c.course_name, s.subject_name
            """)
            subjects_data = cursor.fetchall()
            
            subjects = []
            for subject_data in subjects_data:
                subject = {
                    'subid': subject_data['subid'],
                    'subject_name': subject_data['subject_name'],
                    'course_name': subject_data['course_name'],
                    'semester': subject_data['semester']
                }
                subjects.append(subject)
                
            # Fetch all courses for the "Add Subject" form
            cursor.execute("SELECT cid, course_name FROM courses ORDER BY course_name")
            courses_data = cursor.fetchall()
            
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data['cid'],
                    'course_name': course_data['course_name']
                }
                courses.append(course)
            
            logger.info("Subjects data retrieved successfully")
            return render_template("admin/manageSubjects.html", subjects=subjects, courses=courses)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manage subjects: {db_error}")
        flash("A database error occurred while loading subjects", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manage subjects: {str(e)}")
        flash("An error occurred while loading subjects", "error")
        return redirect(url_for("adminDashboard"))

def addSubject():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add subject")
        flash("Please login to add subjects", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "POST":
        subject_name = request.form.get("subject_name")
        course_id = request.form.get("course_id")
        semester = request.form.get("semester")
        
        if subject_name and course_id and semester:
            try:
                with DatabaseManager() as cursor:
                    cursor.execute("INSERT INTO subjects (subject_name, course_id, semester) VALUES (?, ?, ?)", 
                                (subject_name, course_id, semester))
                    logger.info(f"Subject added: {subject_name} for course ID {course_id}, semester {semester}")
                    flash("Subject added successfully", "success")
            except sqlite3.Error as db_error:
                logger.error(f"Database error adding subject: {db_error}")
                flash(f"Database error adding subject: {str(db_error)}", "error")
            except Exception as e:
                logger.error(f"Error adding subject: {str(e)}")
                flash(f"Error adding subject: {str(e)}", "error")
        else:
            logger.warning("Attempted to add subject with missing fields")
            flash("All fields are required", "error")
            
    return redirect(url_for("manageSubjects"))

def deleteSubject(subid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to delete subject {subid}")
        flash("Please login to delete subjects", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM subjects WHERE subid = ?", (subid,))
            logger.info(f"Subject deleted: {subid}")
            flash("Subject deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error deleting subject {subid}: {db_error}")
        flash(f"Database error deleting subject: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting subject {subid}: {str(e)}")
        flash(f"Error deleting subject: {str(e)}", "error")
        
    return redirect(url_for("manageSubjects"))
# ------------------ Add Student --------------------
def addStudent():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add student")
        flash("Please login to add students", "error")
        return redirect(url_for("adminLogin"))
    
    import os
    import time
    from werkzeug.utils import secure_filename

    UPLOAD_FOLDER = 'static/uploads/profile_pictures'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch courses from courses table
                cursor.execute("SELECT cid, course_name FROM courses")
                courses = cursor.fetchall()
                # Convert to list of dictionaries for template compatibility
                course_list = []
                for course in courses:
                    course_dict = {
                        'cid': course[0],
                        'course_name': course[1]
                    }
                    course_list.append(course_dict)
                return render_template("admin/addStudent.html", courses=course_list)
        except sqlite3.Error as db_error:
            logger.error(f"Database error fetching courses: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("adminDashboard"))
        except Exception as e:
            logger.error(f"Error fetching courses: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("adminDashboard"))
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            contact = request.form.get("contact", "")
            course = request.form.get("course", "")

            # Handle profile picture upload
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    profile_picture = f"uploads/profile_pictures/{filename}"

            with DatabaseManager() as cursor:
                # Check if email already exists
                cursor.execute("SELECT * FROM student WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"Attempt to add student with existing email: {email}")
                    flash("Email already registered", "warning")
                    return redirect(url_for("addStudent"))

                # Insert new student with profile picture
                sql = "INSERT INTO student (name, email, password, contact, course, profile_picture) VALUES (?, ?, ?, ?, ?, ?)"
                val = (name, email, password, contact, course, profile_picture)
                cursor.execute(sql, val)
                logger.info(f"Student added successfully: {email}")
                flash("Student added successfully", "success")
                return redirect(url_for("adminDashboard"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error adding student: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("addStudent"))
        except Exception as e:
            logger.error(f"Error adding student: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("addStudent"))

# ------------------ Delete Student --------------------
def deleteStudent(sid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to delete student {sid}")
        flash("Please login to delete students", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            sql = "DELETE FROM student WHERE sid = ?"
            val = (sid,)
            cursor.execute(sql, val)
            logger.info(f"Student deleted successfully: {sid}")
            flash("Student deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error deleting student {sid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting student {sid}: {str(e)}")
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("adminDashboard"))

# ------------------ Edit Student --------------------
def editStudent(sid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to edit student {sid}")
        flash("Please login to edit students", "error")
        return redirect(url_for("adminLogin"))
    
    import os
    import time
    from werkzeug.utils import secure_filename

    UPLOAD_FOLDER = 'static/uploads/profile_pictures'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                cursor.execute("SELECT * FROM student WHERE sid = ?", (sid,))
                student_data = cursor.fetchone()
                if not student_data:
                    logger.warning(f"Attempt to edit non-existent student with ID: {sid}")
                    flash("Student not found", "error")
                    return redirect(url_for("adminDashboard"))
                    
                # Convert to dictionary for template compatibility
                student = {
                    'sid': student_data[0],
                    'name': student_data[1],
                    'email': student_data[2],
                    'password': student_data[3],
                    'contact': student_data[4],
                    'course': student_data[5],
                    'profile_picture': student_data[6]
                }
                return render_template("admin/editStudent.html", student=student)
        except sqlite3.Error as db_error:
            logger.error(f"Database error fetching student {sid}: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("adminDashboard"))
        except Exception as e:
            logger.error(f"Error fetching student {sid}: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("adminDashboard"))
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            contact = request.form["contact"]
            course = request.form["course"]

            # Handle profile picture upload
            profile_picture_update = False
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    profile_picture = f"uploads/profile_pictures/{filename}"
                    profile_picture_update = True

            with DatabaseManager() as cursor:
                if profile_picture_update:
                    # Update profile with new picture
                    sql = "UPDATE student SET name=?, email=?, contact=?, course=?, profile_picture=? WHERE sid=?"
                    val = (name, email, contact, course, profile_picture, sid)
                else:
                    # Update profile without changing picture
                    sql = "UPDATE student SET name=?, email=?, contact=?, course=? WHERE sid=?"
                    val = (name, email, contact, course, sid)

                cursor.execute(sql, val)
                logger.info(f"Student updated successfully: {sid}")
                flash("Student updated successfully", "success")
                return redirect(url_for("adminDashboard"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error updating student {sid}: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("editStudent", sid=sid))
        except Exception as e:
            logger.error(f"Error updating student {sid}: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("editStudent", sid=sid))

def manageTeacherSubjects():
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get all teachers
            cursor.execute("""
                SELECT t.tid, t.name, t.email, t.branch
                FROM teacher t
                ORDER BY t.name
            """)
            teachers_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            teachers = []
            for teacher_data in teachers_data:
                teacher = {
                    'tid': teacher_data[0],
                    'name': teacher_data[1],
                    'email': teacher_data[2],
                    'branch': teacher_data[3],
                    'subjects': []
                }
                teachers.append(teacher)

            # Get subjects for each teacher
            for teacher in teachers:
                cursor.execute("""
                    SELECT s.subid, s.subject_name, s.course_id, s.semester 
                    FROM subjects s
                    JOIN teacher_subjects ts ON s.subid = ts.subid
                    WHERE ts.tid = ?
                """, (teacher['tid'],))
                subjects_data = cursor.fetchall()
                
                # Convert to list of dictionaries
                subjects = []
                for subject_data in subjects_data:
                    subject = {
                        'subid': subject_data[0],
                        'subject_name': subject_data[1],
                        'course_id': subject_data[2],
                        'semester': subject_data[3]
                    }
                    subjects.append(subject)
                
                teacher['subjects'] = subjects

            # Get all available subjects
            cursor.execute("SELECT * FROM subjects ORDER BY subject_name")
            all_subjects_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            all_subjects = []
            for subject_data in all_subjects_data:
                subject = {
                    'subid': subject_data[0],
                    'subject_name': subject_data[1],
                    'course_id': subject_data[2],
                    'semester': subject_data[3]
                }
                all_subjects.append(subject)

            # Fetch all courses for the "Add Subject" form
            cursor.execute("SELECT cid, course_name FROM courses ORDER BY course_name")
            courses_data = cursor.fetchall()
            
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data[0],
                    'course_name': course_data[1]
                }
                courses.append(course)

            logger.info("Teacher subjects data retrieved successfully")
            return render_template("admin/manageTeacherSubjects.html",
                                teachers=teachers,
                                all_subjects=all_subjects,
                                courses=courses)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageTeacherSubjects: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manageTeacherSubjects: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))
def adminAddSubject(tid):
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    subid = request.form.get("subject")

    try:
        with DatabaseManager() as cursor:
            # Check if the subject is already assigned to the teacher
            cursor.execute("SELECT * FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            if cursor.fetchone():
                flash("This subject is already assigned to the teacher", "error")
                return redirect(url_for("manageTeacherSubjects"))

            # Assign the subject to the teacher
            cursor.execute("INSERT INTO teacher_subjects (tid, subid) VALUES (?, ?)", (tid, subid))
            logger.info(f"Subject {subid} assigned to teacher {tid} successfully")
            flash("Subject assigned successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error assigning subject {subid} to teacher {tid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error assigning subject {subid} to teacher {tid}: {str(e)}")
        flash(f"Error assigning subject: {str(e)}", "error")

    return redirect(url_for("manageTeacherSubjects"))

def adminRemoveSubject(tid, subid):
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            logger.info(f"Subject {subid} removed from teacher {tid} successfully")
            flash("Subject removed successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error removing subject {subid} from teacher {tid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error removing subject {subid} from teacher {tid}: {str(e)}")
        flash(f"Error removing subject: {str(e)}", "error")

    return redirect(url_for("manageTeacherSubjects"))

# ------------------ Manage Fees --------------------
def manageFees():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage fees")
        flash("Please login to access fee management", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get all fees
            cursor.execute("""
                SELECT f.feeid, f.sid, f.amount, f.due_date, f.status,
                       s.name as student_name, s.email as student_email
                FROM fees f
                JOIN student s ON f.sid = s.sid
                ORDER BY f.due_date DESC
            """)
            fees_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            fees = []
            for fee_data in fees_data:
                fee = {
                    'feeid': fee_data[0],
                    'sid': fee_data[1],
                    'amount': fee_data[2],
                    'due_date': fee_data[3],
                    'status': fee_data[4],
                    'student_name': fee_data[5],
                    'student_email': fee_data[6]
                }
                fees.append(fee)

            # Get all students for the add fee form
            cursor.execute("SELECT sid, name, email, course FROM student ORDER BY name")
            students_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            students = []
            for student_data in students_data:
                student = {
                    'sid': student_data[0],
                    'name': student_data[1],
                    'email': student_data[2],
                    'course': student_data[3]
                }
                students.append(student)

            logger.info("Fees data retrieved successfully")
            return render_template("admin/manageFees.html", fees=fees, students=students)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageFees: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manageFees: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))

# ------------------ Add Fee --------------------
def addFee():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add fee")
        flash("Please login to add fee records", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch students list for dropdown
                cursor.execute("SELECT sid, name FROM student ORDER BY name")
                students_data = cursor.fetchall()
                
                # Convert to list of dictionaries for template compatibility
                students = []
                for student_data in students_data:
                    student = {
                        'sid': student_data[0],
                        'name': student_data[1]
                    }
                    students.append(student)
                
                logger.info("Student data retrieved for fee form")
                return render_template("admin/addFee.html", students=students)
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addFee GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("manageFees"))
        except Exception as e:
            logger.error(f"Error in addFee GET: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("manageFees"))
    else:
        try:
            sid = request.form["sid"]
            amount = request.form["amount"]
            due_date = request.form["due_date"]
            status = request.form["status"]  # Get the fee status (Paid or Pending)
            payment_date = request.form.get("payment_date")  # Payment date is optional

            # If the status is "Paid", ensure payment_date is provided
            if status == "Paid" and not payment_date:
                logger.warning(f"Attempted to add paid fee without payment date for student ID: {sid}")
                flash("Payment date is required for paid fees", "error")
                return redirect(url_for("addFee"))

            with DatabaseManager() as cursor:
                # Insert the fee record into the database
                cursor.execute("""
                    INSERT INTO fees (sid, amount, due_date, status, payment_date) 
                    VALUES (?, ?, ?, ?, ?)
                """, (sid, amount, due_date, status, payment_date if payment_date else None))

                logger.info(f"Fee record added successfully for student ID: {sid}")
                flash("Fee record added successfully", "success")
                return redirect(url_for("manageFees"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addFee POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("addFee"))
        except Exception as e:
            logger.error(f"Error in addFee POST: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("addFee"))


# ------------------ Update Fee Status --------------------
def updateFeeStatus(feeid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to update fee status")
        flash("Please login to update fee status", "error")
        return redirect(url_for("adminLogin"))

    try:
        new_status = request.form["status"]  # Paid or Pending
        payment_date = None
        
        # If status is changed to Paid, set payment date to today if not provided
        if new_status == "Paid":
            payment_date = request.form.get("payment_date", datetime.now().strftime("%Y-%m-%d"))
            
        with DatabaseManager() as cursor:
            if payment_date:
                cursor.execute("UPDATE fees SET status = ?, payment_date = ? WHERE feeid = ?", 
                              (new_status, payment_date, feeid))
            else:
                cursor.execute("UPDATE fees SET status = ? WHERE feeid = ?", (new_status, feeid))
                
            logger.info(f"Fee status updated successfully for fee ID: {feeid}")
            flash("Fee status updated successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error in updateFeeStatus: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error updating fee status: {str(e)}")
        flash("An error occurred while updating fee status", "error")
    
    return redirect(url_for("manageFees"))

# ------------------ Delete Fee Record --------------------
def deleteFee(feeid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to delete fee")
        flash("Please login to delete fee records", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM fees WHERE feeid = ?", (feeid,))
            logger.info(f"Fee record deleted successfully for fee ID: {feeid}")
            flash("Fee record deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error in deleteFee: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting fee record: {str(e)}")
        flash("An error occurred while deleting fee record", "error")

    return redirect(url_for("manageFees"))


def editFee(feeid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to edit fee")
        flash("Please login to edit fee records", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch the fee record
                cursor.execute("""
                    SELECT f.feeid, f.sid, f.amount, f.description, f.due_date, f.status, f.payment_date, s.name 
                    FROM fees f 
                    JOIN student s ON f.sid = s.sid 
                    WHERE f.feeid = ?
                """, (feeid,))
                fee_data = cursor.fetchone()
                
                if not fee_data:
                    logger.warning(f"Attempted to edit non-existent fee with ID: {feeid}")
                    flash("Fee record not found", "error")
                    return redirect(url_for("manageFees"))
                
                # Convert to dictionary for template compatibility
                fee = {
                    'feeid': fee_data[0],
                    'sid': fee_data[1],
                    'amount': fee_data[2],
                    'description': fee_data[3],
                    'due_date': fee_data[4],
                    'status': fee_data[5],
                    'payment_date': fee_data[6],
                    'name': fee_data[7]
                }
                
                logger.info(f"Fee data retrieved for editing fee ID: {feeid}")
        except sqlite3.Error as db_error:
            logger.error(f"Database error in editFee GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("manageFees"))
        except Exception as e:
            logger.error(f"Error in editFee GET: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("manageFees"))
        
        return render_template("admin/editFee.html", fee=fee)
    
    elif request.method == "POST":
        try:
            amount = request.form["amount"]
            due_date = request.form["due_date"]
            fee_type = request.form["fee_type"]
            status = request.form["status"]
            payment_date = request.form.get("payment_date")
            
            # If status is Paid, ensure payment_date is provided
            if status == "Paid" and not payment_date:
                payment_date = datetime.now().strftime("%Y-%m-%d")
            
            with DatabaseManager() as cursor:
                if payment_date:
                    sql = """
                        UPDATE fees 
                        SET amount = ?, due_date = ?, fee_type = ?, status = ?, payment_date = ?
                        WHERE feeid = ?
                    """
                    val = (amount, due_date, fee_type, status, payment_date, feeid)
                else:
                    sql = """
                        UPDATE fees 
                        SET amount = ?, due_date = ?, fee_type = ?, status = ?
                        WHERE feeid = ?
                    """
                    val = (amount, due_date, fee_type, status, feeid)
                
                cursor.execute(sql, val)
                
                logger.info(f"Fee record updated successfully for fee ID: {feeid}")
                flash("Fee record updated successfully", "success")
                return redirect(url_for("manageFees"))
            
        except sqlite3.Error as db_error:
            logger.error(f"Database error in editFee POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("editFee", feeid=feeid))
        except Exception as e:
            logger.error(f"Error updating fee: {str(e)}")
            flash("An error occurred while updating the fee record", "error")
            return redirect(url_for("editFee", feeid=feeid))

def feeReport():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to fee report")
        flash("Please login to view fee reports", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            cursor.execute("""
                SELECT s.sid, s.name, f.feeid, f.amount, f.status, f.due_date, f.payment_date
                FROM student s
                LEFT JOIN fees f ON s.sid = f.sid
                ORDER BY s.name
            """)
            fee_report_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            fee_report = []
            for report_data in fee_report_data:
                report = {
                    'sid': report_data[0],
                    'name': report_data[1],
                    'feeid': report_data[2],
                    'amount': report_data[3],
                    'status': report_data[4],
                    'due_date': report_data[5],
                    'payment_date': report_data[6]
                }
                fee_report.append(report)
            
            logger.info("Fee report data retrieved successfully")
            return render_template("admin/feeReport.html", fee_report=fee_report)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in feeReport: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error fetching fee report: {str(e)}")
        flash("An error occurred while fetching the fee report", "error")
        return redirect(url_for("adminDashboard"))

def manageTimetable():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage timetable")
        flash("Please login to manage timetable", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Fetch all courses
            cursor.execute("SELECT cid, course_name FROM courses")
            courses_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data[0],
                    'course_name': course_data[1]
                }
                courses.append(course)

            # Fetch all subjects
            cursor.execute("SELECT subid, subject_name FROM subjects")
            subjects_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            subjects = []
            for subject_data in subjects_data:
                subject = {
                    'subid': subject_data[0],
                    'subject_name': subject_data[1]
                }
                subjects.append(subject)

            # Fetch all teachers
            cursor.execute("SELECT tid, name FROM teacher")
            teachers_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            teachers = []
            for teacher_data in teachers_data:
                teacher = {
                    'tid': teacher_data[0],
                    'name': teacher_data[1]
                }
                teachers.append(teacher)

            # Fetch existing timetable entries with time as string
            # SQLite doesn't have TIME_FORMAT or FIELD functions, so we need to adapt the query
            cursor.execute("""
                SELECT t.tid, c.course_name, t.day,
                       t.start_time, t.end_time,
                       s.subject_name, te.name as teacher_name
                FROM timetable t
                JOIN courses c ON t.course_id = c.cid
                JOIN subjects s ON t.subject_id = s.subid
                JOIN teacher te ON t.teacher_id = te.tid
                ORDER BY
                    CASE t.day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END, t.start_time
            """)
            timetable_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            timetable_entries = []
            for entry_data in timetable_data:
                entry = {
                    'tid': entry_data[0],
                    'course_name': entry_data[1],
                    'day': entry_data[2],
                    'start_time': entry_data[3],
                    'end_time': entry_data[4],
                    'subject_name': entry_data[5],
                    'teacher_name': entry_data[6]
                }
                timetable_entries.append(entry)

            logger.info("Timetable data retrieved successfully")
            return render_template("admin/manageTimetable.html", courses=courses, subjects=subjects, teachers=teachers, timetable_entries=timetable_entries)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageTimetable: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error fetching timetable data: {str(e)}")
        flash("An error occurred while loading timetable data", "error")
        return redirect(url_for("adminDashboard"))



def addTimetableEntry():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add timetable entry")
        flash("Please login to add timetable entries", "error")
        return redirect(url_for("adminLogin"))

    if request.method == "POST":
        course_id = request.form.get("course_id")
        day_of_week = request.form.get("day_of_week")
        time_start = request.form.get("time_start")
        time_end = request.form.get("time_end")
        subid = request.form.get("subid")
        tid_teacher = request.form.get("tid_teacher")

        try:
            with DatabaseManager() as cursor:
                sql = """
                    INSERT INTO timetable (course_id, day, start_time, end_time, subject_id, teacher_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                val = (course_id, day_of_week, time_start, time_end, subid, tid_teacher)
                cursor.execute(sql, val)
                
                logger.info(f"Timetable entry added successfully for course {course_id} on {day_of_week}")
                flash("Timetable entry added successfully", "success")
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addTimetableEntry: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
        except Exception as e:
            logger.error(f"Error adding timetable entry: {str(e)}")
            flash(f"Error adding timetable entry: {str(e)}", "error")

    return redirect(url_for("manageTimetable"))

def deleteTimetableEntry(tid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to delete timetable entry")
        flash("Please login to delete timetable entries", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM timetable WHERE tid = ?", (tid,))
            
            if cursor.rowcount > 0:
                logger.info(f"Timetable entry with ID {tid} deleted successfully")
                flash("Timetable entry deleted successfully", "success")
            else:
                logger.warning(f"No timetable entry found with ID {tid}")
                flash("No timetable entry found with the given ID", "warning")
    except sqlite3.Error as db_error:
        logger.error(f"Database error in deleteTimetableEntry: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting timetable entry: {str(e)}")
        flash(f"Error deleting timetable entry: {str(e)}", "error")

    return redirect(url_for("manageTimetable"))


def addStudent():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add student")
        flash("Please login to add students", "error")
        return redirect(url_for("adminLogin"))
    
    import os
    import time
    from werkzeug.utils import secure_filename

    UPLOAD_FOLDER = 'static/uploads/profile_pictures'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch courses from courses table
                cursor.execute("SELECT cid, course_name FROM courses")
                courses = cursor.fetchall()
                # Convert to list of dictionaries for template compatibility
                course_list = []
                for course in courses:
                    course_dict = {
                        'cid': course[0],
                        'course_name': course[1]
                    }
                    course_list.append(course_dict)
                logger.info("Courses fetched successfully for add student form")
                return render_template("admin/addStudent.html", courses=course_list)
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addStudent GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("adminDashboard"))
        except Exception as e:
            logger.error(f"Error loading add student form: {str(e)}")
            flash("An error occurred while loading the form", "error")
            return redirect(url_for("adminDashboard"))
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            contact = request.form.get("contact", "")
            course = request.form.get("course", "")

            # Handle profile picture upload
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    profile_picture = f"uploads/profile_pictures/{filename}"
                    logger.info(f"Profile picture uploaded for student {name}")

            with DatabaseManager() as cursor:
                # Check if email already exists
                cursor.execute("SELECT * FROM student WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"Attempt to register with existing email: {email}")
                    flash("Email already registered", "warning")
                    return redirect(url_for("addStudent"))

                # Insert new student with profile picture
                sql = "INSERT INTO student (name, email, password, contact, course, profile_picture) VALUES (?, ?, ?, ?, ?, ?)"
                val = (name, email, password, contact, course, profile_picture)
                cursor.execute(sql, val)
                
                logger.info(f"Student {name} added successfully with email {email}")
                flash("Student added successfully", "success")
                return redirect(url_for("adminDashboard"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addStudent POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("addStudent"))
        except Exception as e:
            logger.error(f"Error adding student: {str(e)}")
            flash("An error occurred while adding student", "error")
            return redirect(url_for("addStudent"))

# ------------------ Delete Student --------------------
def deleteStudent(sid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to delete student {sid}")
        flash("Please login to delete students", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            sql = "DELETE FROM student WHERE sid = ?"
            val = (sid,)
            cursor.execute(sql, val)
            logger.info(f"Student deleted successfully: {sid}")
            flash("Student deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error deleting student {sid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting student {sid}: {str(e)}")
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("adminDashboard"))

# ------------------ Edit Student --------------------
def editStudent(sid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to edit student {sid}")
        flash("Please login to edit students", "error")
        return redirect(url_for("adminLogin"))
    
    import os
    import time
    from werkzeug.utils import secure_filename

    UPLOAD_FOLDER = 'static/uploads/profile_pictures'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                cursor.execute("SELECT * FROM student WHERE sid = ?", (sid,))
                student_data = cursor.fetchone()
                if not student_data:
                    logger.warning(f"Attempt to edit non-existent student with ID: {sid}")
                    flash("Student not found", "error")
                    return redirect(url_for("adminDashboard"))
                    
                # Convert to dictionary for template compatibility
                student = {
                    'sid': student_data[0],
                    'name': student_data[1],
                    'email': student_data[2],
                    'password': student_data[3],
                    'contact': student_data[4],
                    'course': student_data[5],
                    'profile_picture': student_data[6]
                }
                return render_template("admin/editStudent.html", student=student)
        except sqlite3.Error as db_error:
            logger.error(f"Database error fetching student {sid}: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("adminDashboard"))
        except Exception as e:
            logger.error(f"Error fetching student {sid}: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("adminDashboard"))
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            contact = request.form["contact"]
            course = request.form["course"]

            # Handle profile picture upload
            profile_picture_update = False
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    profile_picture = f"uploads/profile_pictures/{filename}"
                    profile_picture_update = True

            with DatabaseManager() as cursor:
                if profile_picture_update:
                    # Update profile with new picture
                    sql = "UPDATE student SET name=?, email=?, contact=?, course=?, profile_picture=? WHERE sid=?"
                    val = (name, email, contact, course, profile_picture, sid)
                else:
                    # Update profile without changing picture
                    sql = "UPDATE student SET name=?, email=?, contact=?, course=? WHERE sid=?"
                    val = (name, email, contact, course, sid)

                cursor.execute(sql, val)
                logger.info(f"Student updated successfully: {sid}")
                flash("Student updated successfully", "success")
                return redirect(url_for("adminDashboard"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error updating student {sid}: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("editStudent", sid=sid))
        except Exception as e:
            logger.error(f"Error updating student {sid}: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("editStudent", sid=sid))

def manageTeacherSubjects():
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get all teachers
            cursor.execute("""
                SELECT t.tid, t.name, t.email, t.branch
                FROM teacher t
                ORDER BY t.name
            """)
            teachers_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            teachers = []
            for teacher_data in teachers_data:
                teacher = {
                    'tid': teacher_data[0],
                    'name': teacher_data[1],
                    'email': teacher_data[2],
                    'branch': teacher_data[3],
                    'subjects': []
                }
                teachers.append(teacher)

            # Get subjects for each teacher
            for teacher in teachers:
                cursor.execute("""
                    SELECT s.subid, s.subject_name, s.course_id, s.semester 
                    FROM subjects s
                    JOIN teacher_subjects ts ON s.subid = ts.subid
                    WHERE ts.tid = ?
                """, (teacher['tid'],))
                subjects_data = cursor.fetchall()
                
                # Convert to list of dictionaries
                subjects = []
                for subject_data in subjects_data:
                    subject = {
                        'subid': subject_data[0],
                        'subject_name': subject_data[1],
                        'course_id': subject_data[2],
                        'semester': subject_data[3]
                    }
                    subjects.append(subject)
                
                teacher['subjects'] = subjects

            # Get all available subjects
            cursor.execute("SELECT * FROM subjects ORDER BY subject_name")
            all_subjects_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            all_subjects = []
            for subject_data in all_subjects_data:
                subject = {
                    'subid': subject_data[0],
                    'subject_name': subject_data[1],
                    'course_id': subject_data[2],
                    'semester': subject_data[3]
                }
                all_subjects.append(subject)

            # Fetch all courses for the "Add Subject" form
            cursor.execute("SELECT cid, course_name FROM courses ORDER BY course_name")
            courses_data = cursor.fetchall()
            
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data[0],
                    'course_name': course_data[1]
                }
                courses.append(course)

            logger.info("Teacher subjects data retrieved successfully")
            return render_template("admin/manageTeacherSubjects.html",
                                teachers=teachers,
                                all_subjects=all_subjects,
                                courses=courses)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageTeacherSubjects: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manageTeacherSubjects: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))
def adminAddSubject(tid):
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    subid = request.form.get("subject")

    try:
        with DatabaseManager() as cursor:
            # Check if the subject is already assigned to the teacher
            cursor.execute("SELECT * FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            if cursor.fetchone():
                flash("This subject is already assigned to the teacher", "error")
                return redirect(url_for("manageTeacherSubjects"))

            # Assign the subject to the teacher
            cursor.execute("INSERT INTO teacher_subjects (tid, subid) VALUES (?, ?)", (tid, subid))
            logger.info(f"Subject {subid} assigned to teacher {tid} successfully")
            flash("Subject assigned successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error assigning subject {subid} to teacher {tid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error assigning subject {subid} to teacher {tid}: {str(e)}")
        flash(f"Error assigning subject: {str(e)}", "error")

    return redirect(url_for("manageTeacherSubjects"))

def adminRemoveSubject(tid, subid):
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            logger.info(f"Subject {subid} removed from teacher {tid} successfully")
            flash("Subject removed successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error removing subject {subid} from teacher {tid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error removing subject {subid} from teacher {tid}: {str(e)}")
        flash(f"Error removing subject: {str(e)}", "error")

    return redirect(url_for("manageTeacherSubjects"))

# ------------------ Manage Fees --------------------
def manageFees():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage fees")
        flash("Please login to access fee management", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get all fees
            cursor.execute("""
                SELECT f.feeid, f.sid, f.amount, f.due_date, f.status,
                       s.name as student_name, s.email as student_email
                FROM fees f
                JOIN student s ON f.sid = s.sid
                ORDER BY f.due_date DESC
            """)
            fees_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            fees = []
            for fee_data in fees_data:
                fee = {
                    'feeid': fee_data[0],
                    'sid': fee_data[1],
                    'amount': fee_data[2],
                    'due_date': fee_data[3],
                    'status': fee_data[4],
                    'student_name': fee_data[5],
                    'student_email': fee_data[6]
                }
                fees.append(fee)

            # Get all students for the add fee form
            cursor.execute("SELECT sid, name, email, course FROM student ORDER BY name")
            students_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            students = []
            for student_data in students_data:
                student = {
                    'sid': student_data[0],
                    'name': student_data[1],
                    'email': student_data[2],
                    'course': student_data[3]
                }
                students.append(student)

            logger.info("Fees data retrieved successfully")
            return render_template("admin/manageFees.html", fees=fees, students=students)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageFees: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manageFees: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))

# ------------------ Add Fee --------------------
def addFee():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add fee")
        flash("Please login to add fee records", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch students list for dropdown
                cursor.execute("SELECT sid, name FROM student ORDER BY name")
                students_data = cursor.fetchall()
                
                # Convert to list of dictionaries for template compatibility
                students = []
                for student_data in students_data:
                    student = {
                        'sid': student_data[0],
                        'name': student_data[1]
                    }
                    students.append(student)
                
                logger.info("Student data retrieved for fee form")
                return render_template("admin/addFee.html", students=students)
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addFee GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("manageFees"))
        except Exception as e:
            logger.error(f"Error in addFee GET: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("manageFees"))
    else:
        try:
            sid = request.form["sid"]
            amount = request.form["amount"]
            due_date = request.form["due_date"]
            status = request.form["status"]  # Get the fee status (Paid or Pending)
            payment_date = request.form.get("payment_date")  # Payment date is optional

            # If the status is "Paid", ensure payment_date is provided
            if status == "Paid" and not payment_date:
                logger.warning(f"Attempted to add paid fee without payment date for student ID: {sid}")
                flash("Payment date is required for paid fees", "error")
                return redirect(url_for("addFee"))

            with DatabaseManager() as cursor:
                # Insert the fee record into the database
                cursor.execute("""
                    INSERT INTO fees (sid, amount, due_date, status, payment_date) 
                    VALUES (?, ?, ?, ?, ?)
                """, (sid, amount, due_date, status, payment_date if payment_date else None))

                logger.info(f"Fee record added successfully for student ID: {sid}")
                flash("Fee record added successfully", "success")
                return redirect(url_for("manageFees"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addFee POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("addFee"))
        except Exception as e:
            logger.error(f"Error in addFee POST: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("addFee"))


# ------------------ Update Fee Status --------------------
def updateFeeStatus(feeid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to update fee status")
        flash("Please login to update fee status", "error")
        return redirect(url_for("adminLogin"))

    try:
        new_status = request.form["status"]  # Paid or Pending
        payment_date = None
        
        # If status is changed to Paid, set payment date to today if not provided
        if new_status == "Paid":
            payment_date = request.form.get("payment_date", datetime.now().strftime("%Y-%m-%d"))
            
        with DatabaseManager() as cursor:
            if payment_date:
                cursor.execute("UPDATE fees SET status = ?, payment_date = ? WHERE feeid = ?", 
                              (new_status, payment_date, feeid))
            else:
                cursor.execute("UPDATE fees SET status = ? WHERE feeid = ?", (new_status, feeid))
                
            logger.info(f"Fee status updated successfully for fee ID: {feeid}")
            flash("Fee status updated successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error in updateFeeStatus: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error updating fee status: {str(e)}")
        flash("An error occurred while updating fee status", "error")
    
    return redirect(url_for("manageFees"))

# ------------------ Delete Fee Record --------------------
def deleteFee(feeid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to delete fee")
        flash("Please login to delete fee records", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM fees WHERE feeid = ?", (feeid,))
            logger.info(f"Fee record deleted successfully for fee ID: {feeid}")
            flash("Fee record deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error in deleteFee: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting fee record: {str(e)}")
        flash("An error occurred while deleting fee record", "error")

    return redirect(url_for("manageFees"))


def editFee(feeid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to edit fee")
        flash("Please login to edit fee records", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch the fee record
                cursor.execute("""
                    SELECT f.feeid, f.sid, f.amount, f.description, f.due_date, f.status, f.payment_date, s.name 
                    FROM fees f 
                    JOIN student s ON f.sid = s.sid 
                    WHERE f.feeid = ?
                """, (feeid,))
                fee_data = cursor.fetchone()
                
                if not fee_data:
                    logger.warning(f"Attempted to edit non-existent fee with ID: {feeid}")
                    flash("Fee record not found", "error")
                    return redirect(url_for("manageFees"))
                
                # Convert to dictionary for template compatibility
                fee = {
                    'feeid': fee_data[0],
                    'sid': fee_data[1],
                    'amount': fee_data[2],
                    'description': fee_data[3],
                    'due_date': fee_data[4],
                    'status': fee_data[5],
                    'payment_date': fee_data[6],
                    'name': fee_data[7]
                }
                
                logger.info(f"Fee data retrieved for editing fee ID: {feeid}")
        except sqlite3.Error as db_error:
            logger.error(f"Database error in editFee GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("manageFees"))
        except Exception as e:
            logger.error(f"Error in editFee GET: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("manageFees"))
        
        return render_template("admin/editFee.html", fee=fee)
    
    elif request.method == "POST":
        try:
            amount = request.form["amount"]
            due_date = request.form["due_date"]
            fee_type = request.form["fee_type"]
            status = request.form["status"]
            payment_date = request.form.get("payment_date")
            
            # If status is Paid, ensure payment_date is provided
            if status == "Paid" and not payment_date:
                payment_date = datetime.now().strftime("%Y-%m-%d")
            
            with DatabaseManager() as cursor:
                if payment_date:
                    sql = """
                        UPDATE fees 
                        SET amount = ?, due_date = ?, fee_type = ?, status = ?, payment_date = ?
                        WHERE feeid = ?
                    """
                    val = (amount, due_date, fee_type, status, payment_date, feeid)
                else:
                    sql = """
                        UPDATE fees 
                        SET amount = ?, due_date = ?, fee_type = ?, status = ?
                        WHERE feeid = ?
                    """
                    val = (amount, due_date, fee_type, status, feeid)
                
                cursor.execute(sql, val)
                
                logger.info(f"Fee record updated successfully for fee ID: {feeid}")
                flash("Fee record updated successfully", "success")
                return redirect(url_for("manageFees"))
            
        except sqlite3.Error as db_error:
            logger.error(f"Database error in editFee POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("editFee", feeid=feeid))
        except Exception as e:
            logger.error(f"Error updating fee: {str(e)}")
            flash("An error occurred while updating the fee record", "error")
            return redirect(url_for("editFee", feeid=feeid))

def feeReport():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to fee report")
        flash("Please login to view fee reports", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            cursor.execute("""
                SELECT s.sid, s.name, f.feeid, f.amount, f.status, f.due_date, f.payment_date
                FROM student s
                LEFT JOIN fees f ON s.sid = f.sid
                ORDER BY s.name
            """)
            fee_report_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            fee_report = []
            for report_data in fee_report_data:
                report = {
                    'sid': report_data[0],
                    'name': report_data[1],
                    'feeid': report_data[2],
                    'amount': report_data[3],
                    'status': report_data[4],
                    'due_date': report_data[5],
                    'payment_date': report_data[6]
                }
                fee_report.append(report)
            
            logger.info("Fee report data retrieved successfully")
            return render_template("admin/feeReport.html", fee_report=fee_report)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in feeReport: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error fetching fee report: {str(e)}")
        flash("An error occurred while fetching the fee report", "error")
        return redirect(url_for("adminDashboard"))

def manageTimetable():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage timetable")
        flash("Please login to manage timetable", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Fetch all courses
            cursor.execute("SELECT cid, course_name FROM courses")
            courses_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data[0],
                    'course_name': course_data[1]
                }
                courses.append(course)

            # Fetch all subjects
            cursor.execute("SELECT subid, subject_name FROM subjects")
            subjects_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            subjects = []
            for subject_data in subjects_data:
                subject = {
                    'subid': subject_data[0],
                    'subject_name': subject_data[1]
                }
                subjects.append(subject)

            # Fetch all teachers
            cursor.execute("SELECT tid, name FROM teacher")
            teachers_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            teachers = []
            for teacher_data in teachers_data:
                teacher = {
                    'tid': teacher_data[0],
                    'name': teacher_data[1]
                }
                teachers.append(teacher)

            # Fetch existing timetable entries with time as string
            # SQLite doesn't have TIME_FORMAT or FIELD functions, so we need to adapt the query
            cursor.execute("""
                SELECT t.tid, c.course_name, t.day,
                       t.start_time, t.end_time,
                       s.subject_name, te.name as teacher_name
                FROM timetable t
                JOIN courses c ON t.course_id = c.cid
                JOIN subjects s ON t.subject_id = s.subid
                JOIN teacher te ON t.teacher_id = te.tid
                ORDER BY
                    CASE t.day
                        WHEN 'Monday' THEN 1
                        WHEN 'Tuesday' THEN 2
                        WHEN 'Wednesday' THEN 3
                        WHEN 'Thursday' THEN 4
                        WHEN 'Friday' THEN 5
                        WHEN 'Saturday' THEN 6
                        WHEN 'Sunday' THEN 7
                    END, t.start_time
            """)
            timetable_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            timetable_entries = []
            for entry_data in timetable_data:
                entry = {
                    'tid': entry_data[0],
                    'course_name': entry_data[1],
                    'day': entry_data[2],
                    'start_time': entry_data[3],
                    'end_time': entry_data[4],
                    'subject_name': entry_data[5],
                    'teacher_name': entry_data[6]
                }
                timetable_entries.append(entry)

            logger.info("Timetable data retrieved successfully")
            return render_template("admin/manageTimetable.html", courses=courses, subjects=subjects, teachers=teachers, timetable_entries=timetable_entries)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageTimetable: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error fetching timetable data: {str(e)}")
        flash("An error occurred while loading timetable data", "error")
        return redirect(url_for("adminDashboard"))



def addTimetableEntry():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add timetable entry")
        flash("Please login to add timetable entries", "error")
        return redirect(url_for("adminLogin"))

    if request.method == "POST":
        course_id = request.form.get("course_id")
        day_of_week = request.form.get("day_of_week")
        time_start = request.form.get("time_start")
        time_end = request.form.get("time_end")
        subid = request.form.get("subid")
        tid_teacher = request.form.get("tid_teacher")

        try:
            with DatabaseManager() as cursor:
                sql = """
                    INSERT INTO timetable (course_id, day, start_time, end_time, subject_id, teacher_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                val = (course_id, day_of_week, time_start, time_end, subid, tid_teacher)
                cursor.execute(sql, val)
                
                logger.info(f"Timetable entry added successfully for course {course_id} on {day_of_week}")
                flash("Timetable entry added successfully", "success")
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addTimetableEntry: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
        except Exception as e:
            logger.error(f"Error adding timetable entry: {str(e)}")
            flash(f"Error adding timetable entry: {str(e)}", "error")

    return redirect(url_for("manageTimetable"))

def deleteTimetableEntry(tid):
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to delete timetable entry")
        flash("Please login to delete timetable entries", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM timetable WHERE tid = ?", (tid,))
            
            if cursor.rowcount > 0:
                logger.info(f"Timetable entry with ID {tid} deleted successfully")
                flash("Timetable entry deleted successfully", "success")
            else:
                logger.warning(f"No timetable entry found with ID {tid}")
                flash("No timetable entry found with the given ID", "warning")
    except sqlite3.Error as db_error:
        logger.error(f"Database error in deleteTimetableEntry: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting timetable entry: {str(e)}")
        flash(f"Error deleting timetable entry: {str(e)}", "error")

    return redirect(url_for("manageTimetable"))


def addStudent():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add student")
        flash("Please login to add students", "error")
        return redirect(url_for("adminLogin"))
    
    import os
    import time
    from werkzeug.utils import secure_filename

    UPLOAD_FOLDER = 'static/uploads/profile_pictures'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch courses from courses table
                cursor.execute("SELECT cid, course_name FROM courses")
                courses = cursor.fetchall()
                # Convert to list of dictionaries for template compatibility
                course_list = []
                for course in courses:
                    course_dict = {
                        'cid': course[0],
                        'course_name': course[1]
                    }
                    course_list.append(course_dict)
                logger.info("Courses fetched successfully for add student form")
                return render_template("admin/addStudent.html", courses=course_list)
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addStudent GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("adminDashboard"))
        except Exception as e:
            logger.error(f"Error loading add student form: {str(e)}")
            flash("An error occurred while loading the form", "error")
            return redirect(url_for("adminDashboard"))
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            contact = request.form.get("contact", "")
            course = request.form.get("course", "")

            # Handle profile picture upload
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    profile_picture = f"uploads/profile_pictures/{filename}"
                    logger.info(f"Profile picture uploaded for student {name}")

            with DatabaseManager() as cursor:
                # Check if email already exists
                cursor.execute("SELECT * FROM student WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"Attempt to register with existing email: {email}")
                    flash("Email already registered", "warning")
                    return redirect(url_for("addStudent"))

                # Insert new student with profile picture
                sql = "INSERT INTO student (name, email, password, contact, course, profile_picture) VALUES (?, ?, ?, ?, ?, ?)"
                val = (name, email, password, contact, course, profile_picture)
                cursor.execute(sql, val)
                
                logger.info(f"Student {name} added successfully with email {email}")
                flash("Student added successfully", "success")
                return redirect(url_for("adminDashboard"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addStudent POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("addStudent"))
        except Exception as e:
            logger.error(f"Error adding student: {str(e)}")
            flash("An error occurred while adding student", "error")
            return redirect(url_for("addStudent"))

# ------------------ Delete Student --------------------
def deleteStudent(sid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to delete student {sid}")
        flash("Please login to delete students", "error")
        return redirect(url_for("adminLogin"))
    
    try:
        with DatabaseManager() as cursor:
            sql = "DELETE FROM student WHERE sid = ?"
            val = (sid,)
            cursor.execute(sql, val)
            logger.info(f"Student deleted successfully: {sid}")
            flash("Student deleted successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error deleting student {sid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error deleting student {sid}: {str(e)}")
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for("adminDashboard"))

# ------------------ Edit Student --------------------
def editStudent(sid):
    if "admin" not in session:
        logger.warning(f"Unauthorized access attempt to edit student {sid}")
        flash("Please login to edit students", "error")
        return redirect(url_for("adminLogin"))
    
    import os
    import time
    from werkzeug.utils import secure_filename

    UPLOAD_FOLDER = 'static/uploads/profile_pictures'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                cursor.execute("SELECT * FROM student WHERE sid = ?", (sid,))
                student_data = cursor.fetchone()
                if not student_data:
                    logger.warning(f"Attempt to edit non-existent student with ID: {sid}")
                    flash("Student not found", "error")
                    return redirect(url_for("adminDashboard"))
                    
                # Convert to dictionary for template compatibility
                student = {
                    'sid': student_data[0],
                    'name': student_data[1],
                    'email': student_data[2],
                    'password': student_data[3],
                    'contact': student_data[4],
                    'course': student_data[5],
                    'profile_picture': student_data[6]
                }
                return render_template("admin/editStudent.html", student=student)
        except sqlite3.Error as db_error:
            logger.error(f"Database error fetching student {sid}: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("adminDashboard"))
        except Exception as e:
            logger.error(f"Error fetching student {sid}: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("adminDashboard"))
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            contact = request.form["contact"]
            course = request.form["course"]

            # Handle profile picture upload
            profile_picture_update = False
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                    profile_picture = f"uploads/profile_pictures/{filename}"
                    profile_picture_update = True

            with DatabaseManager() as cursor:
                if profile_picture_update:
                    # Update profile with new picture
                    sql = "UPDATE student SET name=?, email=?, contact=?, course=?, profile_picture=? WHERE sid=?"
                    val = (name, email, contact, course, profile_picture, sid)
                else:
                    # Update profile without changing picture
                    sql = "UPDATE student SET name=?, email=?, contact=?, course=? WHERE sid=?"
                    val = (name, email, contact, course, sid)

                cursor.execute(sql, val)
                logger.info(f"Student updated successfully: {sid}")
                flash("Student updated successfully", "success")
                return redirect(url_for("adminDashboard"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error updating student {sid}: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("editStudent", sid=sid))
        except Exception as e:
            logger.error(f"Error updating student {sid}: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("editStudent", sid=sid))

def manageTeacherSubjects():
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get all teachers
            cursor.execute("""
                SELECT t.tid, t.name, t.email, t.branch
                FROM teacher t
                ORDER BY t.name
            """)
            teachers_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            teachers = []
            for teacher_data in teachers_data:
                teacher = {
                    'tid': teacher_data[0],
                    'name': teacher_data[1],
                    'email': teacher_data[2],
                    'branch': teacher_data[3],
                    'subjects': []
                }
                teachers.append(teacher)

            # Get subjects for each teacher
            for teacher in teachers:
                cursor.execute("""
                    SELECT s.subid, s.subject_name, s.course_id, s.semester 
                    FROM subjects s
                    JOIN teacher_subjects ts ON s.subid = ts.subid
                    WHERE ts.tid = ?
                """, (teacher['tid'],))
                subjects_data = cursor.fetchall()
                
                # Convert to list of dictionaries
                subjects = []
                for subject_data in subjects_data:
                    subject = {
                        'subid': subject_data[0],
                        'subject_name': subject_data[1],
                        'course_id': subject_data[2],
                        'semester': subject_data[3]
                    }
                    subjects.append(subject)
                
                teacher['subjects'] = subjects

            # Get all available subjects
            cursor.execute("SELECT * FROM subjects ORDER BY subject_name")
            all_subjects_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            all_subjects = []
            for subject_data in all_subjects_data:
                subject = {
                    'subid': subject_data[0],
                    'subject_name': subject_data[1],
                    'course_id': subject_data[2],
                    'semester': subject_data[3]
                }
                all_subjects.append(subject)

            # Fetch all courses for the "Add Subject" form
            cursor.execute("SELECT cid, course_name FROM courses ORDER BY course_name")
            courses_data = cursor.fetchall()
            
            courses = []
            for course_data in courses_data:
                course = {
                    'cid': course_data[0],
                    'course_name': course_data[1]
                }
                courses.append(course)

            logger.info("Teacher subjects data retrieved successfully")
            return render_template("admin/manageTeacherSubjects.html",
                                teachers=teachers,
                                all_subjects=all_subjects,
                                courses=courses)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageTeacherSubjects: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manageTeacherSubjects: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))
def adminAddSubject(tid):
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    subid = request.form.get("subject")

    try:
        with DatabaseManager() as cursor:
            # Check if the subject is already assigned to the teacher
            cursor.execute("SELECT * FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            if cursor.fetchone():
                flash("This subject is already assigned to the teacher", "error")
                return redirect(url_for("manageTeacherSubjects"))

            # Assign the subject to the teacher
            cursor.execute("INSERT INTO teacher_subjects (tid, subid) VALUES (?, ?)", (tid, subid))
            logger.info(f"Subject {subid} assigned to teacher {tid} successfully")
            flash("Subject assigned successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error assigning subject {subid} to teacher {tid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error assigning subject {subid} to teacher {tid}: {str(e)}")
        flash(f"Error assigning subject: {str(e)}", "error")

    return redirect(url_for("manageTeacherSubjects"))

def adminRemoveSubject(tid, subid):
    if "admin" not in session:
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("DELETE FROM teacher_subjects WHERE tid = ? AND subid = ?", (tid, subid))
            logger.info(f"Subject {subid} removed from teacher {tid} successfully")
            flash("Subject removed successfully", "success")
    except sqlite3.Error as db_error:
        logger.error(f"Database error removing subject {subid} from teacher {tid}: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
    except Exception as e:
        logger.error(f"Error removing subject {subid} from teacher {tid}: {str(e)}")
        flash(f"Error removing subject: {str(e)}", "error")

    return redirect(url_for("manageTeacherSubjects"))

# ------------------ Manage Fees --------------------
def manageFees():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to manage fees")
        flash("Please login to access fee management", "error")
        return redirect(url_for("adminLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get all fees
            cursor.execute("""
                SELECT f.feeid, f.sid, f.amount, f.due_date, f.status,
                       s.name as student_name, s.email as student_email
                FROM fees f
                JOIN student s ON f.sid = s.sid
                ORDER BY f.due_date DESC
            """)
            fees_data = cursor.fetchall()
            
            # Convert to list of dictionaries for template compatibility
            fees = []
            for fee_data in fees_data:
                fee = {
                    'feeid': fee_data[0],
                    'sid': fee_data[1],
                    'amount': fee_data[2],
                    'due_date': fee_data[3],
                    'status': fee_data[4],
                    'student_name': fee_data[5],
                    'student_email': fee_data[6]
                }
                fees.append(fee)

            # Get all students for the add fee form
            cursor.execute("SELECT sid, name, email, course FROM student ORDER BY name")
            students_data = cursor.fetchall()
            
            # Convert to list of dictionaries
            students = []
            for student_data in students_data:
                student = {
                    'sid': student_data[0],
                    'name': student_data[1],
                    'email': student_data[2],
                    'course': student_data[3]
                }
                students.append(student)

            logger.info("Fees data retrieved successfully")
            return render_template("admin/manageFees.html", fees=fees, students=students)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in manageFees: {db_error}")
        flash(f"Database error: {str(db_error)}", "error")
        return redirect(url_for("adminDashboard"))
    except Exception as e:
        logger.error(f"Error in manageFees: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for("adminDashboard"))

# ------------------ Add Fee --------------------
def addFee():
    if "admin" not in session:
        logger.warning("Unauthorized access attempt to add fee")
        flash("Please login to add fee records", "error")
        return redirect(url_for("adminLogin"))
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                # Fetch students list for dropdown
                cursor.execute("SELECT sid, name FROM student ORDER BY name")
                students_data = cursor.fetchall()
                
                # Convert to list of dictionaries for template compatibility
                students = []
                for student_data in students_data:
                    student = {
                        'sid': student_data[0],
                        'name': student_data[1]
                    }
                    students.append(student)
                
                logger.info("Student data retrieved for fee form")
                return render_template("admin/addFee.html", students=students)
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addFee GET: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("manageFees"))
        except Exception as e:
            logger.error(f"Error in addFee GET: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("manageFees"))
    else:
        try:
            sid = request.form["sid"]
            amount = request.form["amount"]
            due_date = request.form["due_date"]
            status = request.form["status"]  # Get the fee status (Paid or Pending)
            payment_date = request.form.get("payment_date")  # Payment date is optional

            # If the status is "Paid", ensure payment_date is provided
            if status == "Paid" and not payment_date:
                logger.warning(f"Attempted to add paid fee without payment date for student ID: {sid}")
                flash("Payment date is required for paid fees", "error")
                return redirect(url_for("addFee"))

            with DatabaseManager() as cursor:
                # Insert the fee record into the database
                cursor.execute("""
                    INSERT INTO fees (sid, amount, due_date, status, payment_date) 
                    VALUES (?, ?, ?, ?, ?)
                """, (sid, amount, due_date, status, payment_date if payment_date else None))

                logger.info(f"Fee record added successfully for student ID: {sid}")
                flash("Fee record added successfully", "success")
                return redirect(url_for("manageFees"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error in addFee POST: {db_error}")
            flash(f"Database error: {str(db_error)}", "error")
            return redirect(url_for("addFee"))
        except Exception as e:
            logger.error(f"Error in addFee POST: {str(e)}")
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for("addFee"))