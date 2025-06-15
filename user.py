import sqlite3
import os
import time
from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from db_config import DatabaseManager, logger

UPLOAD_FOLDER = 'static/uploads/profile_pictures'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file has an allowed extension"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_profile_picture(file):
    """Handle profile picture upload safely"""
    if not file or not hasattr(file, 'filename') or not file.filename:
        return None
        
    if not allowed_file(file.filename):
        flash("Invalid file type. Only PNG, JPG, JPEG, and GIF files are allowed.", "error")
        return None
        
    try:
        safe_filename = file.filename
        if not isinstance(safe_filename, str):
            return None
            
        safe_filename = secure_filename(safe_filename)
        timestamp_filename = f"{int(time.time())}_{safe_filename}"
        file_path = os.path.join(UPLOAD_FOLDER, timestamp_filename)
        file.save(file_path)
        return f"uploads/profile_pictures/{timestamp_filename}"
    except Exception as e:
        logger.error(f"Error handling profile picture: {str(e)}")
        return None

# ------------------ Student Signup --------------------
def studentSignup():
    if request.method == "GET":
        return render_template("user/studentSignup.html")
    else:
        try:
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            contact = request.form.get("contact", "")
            course = request.form.get("course", "")

            # Validate password match
            if password != confirm_password:
                flash("Passwords do not match!", "error")
                return redirect(url_for("studentSignup"))

            # Validate contact number
            is_valid, result = validate_contact_number(contact)
            if not is_valid:
                flash(result, "error")
                return redirect(url_for("studentSignup"))
            contact = result

            # Handle profile picture
            profile_picture = None
            if 'profile_picture' in request.files:
                profile_picture = handle_profile_picture(request.files['profile_picture'])

            with DatabaseManager() as cursor:
                # Check if email already exists
                cursor.execute("SELECT * FROM student WHERE email = ?", (email,))
                if cursor.fetchone():
                    logger.warning(f"Attempted signup with existing email: {email}")
                    flash("Email already registered", "error")
                    return redirect(url_for("studentSignup"))

                # Insert new student
                sql = "INSERT INTO student (name, email, password, contact, course, profile_picture) VALUES (?, ?, ?, ?, ?, ?)"
                val = (name, email, password, contact, course, profile_picture)
                cursor.execute(sql, val)
                logger.info(f"New student registered: {email}")
                flash("Registration successful! Please login.", "success")
                return redirect(url_for("studentLogin"))

        except sqlite3.IntegrityError:
            logger.error(f"Database integrity error during student signup with email: {email}")
            flash("Email already registered", "error")
            return redirect(url_for("studentSignup"))
        except Exception as e:
            logger.error(f"Error during student signup: {str(e)}")
            flash("An error occurred during registration", "error")
            return redirect(url_for("studentSignup"))

# ------------------ Student Login --------------------
def studentLogin():
    if request.method == "GET":
        return render_template("user/studentLogin.html")
    else:
        try:
            email = request.form["email"]
            password = request.form["password"]
            
            with DatabaseManager() as cursor:
                sql = "SELECT * FROM student WHERE email = ? AND password = ?"
                val = (email, password)
                cursor.execute(sql, val)
                student_row = cursor.fetchone()
                
                # Convert row to dictionary for compatibility
                student = None
                if student_row:
                    student = {}
                    for idx, col in enumerate(cursor.description):
                        student[col[0]] = student_row[idx]
                
                if student:
                    session["student"] = student["email"]
                    session["student_id"] = student["sid"]
                    session["student_name"] = student["name"]
                    logger.info(f"Student logged in: {email}")
                    return redirect(url_for("studentDashboard"))
                else:
                    logger.warning(f"Failed login attempt for student email: {email}")
                    flash("Invalid email or password", "error")
                    return redirect(url_for("studentLogin"))
        except sqlite3.Error as db_error:
            logger.error(f"Database error during student login: {db_error}")
            flash("A database error occurred during login", "error")
            return redirect(url_for("studentLogin"))
        except Exception as e:
            logger.error(f"Error during student login: {str(e)}")
            flash("An error occurred during login", "error")
            return redirect(url_for("studentLogin"))

# ------------------ Student Dashboard --------------------
def studentDashboard():
    if "student" not in session:
        return redirect(url_for("studentLogin"))

    try:
        with DatabaseManager() as cursor:
            cursor.execute("SELECT * FROM student WHERE email = ?", (session["student"],))
            student_row = cursor.fetchone()
            
            # Convert row to dictionary for compatibility
            student = None
            if student_row:
                student = {}
                for idx, col in enumerate(cursor.description):
                    student[col[0]] = student_row[idx]
            
            # Fetch events
            cursor.execute("SELECT * FROM events ORDER BY event_date DESC")
            events = []
            for row in cursor.fetchall():
                event = {}
                for idx, col in enumerate(cursor.description):
                    event[col[0]] = row[idx]
                events.append(event)

            logger.info(f"Student dashboard loaded for: {session['student']}")
            return render_template("user/studentDashboard.html", student=student, events=events)
    except sqlite3.Error as db_error:
        logger.error(f"Database error in student dashboard: {db_error}")
        flash("A database error occurred while loading the dashboard", "error")
        return redirect(url_for("studentLogin"))
    except Exception as e:
        logger.error(f"Error in student dashboard: {str(e)}")
        flash("An error occurred while loading the dashboard", "error")
        return redirect(url_for("studentLogin"))

# ------------------ Student Logout --------------------
def studentLogout():
    try:
        session.pop("student", None)
        session.pop("student_id", None)
        session.pop("student_name", None)
        logger.info("Student logged out successfully")
        flash("You have been logged out successfully", "success")
        return redirect(url_for("studentLogin"))
    except Exception as e:
        logger.error(f"Error during student logout: {str(e)}")
        flash("An error occurred during logout", "error")
        return redirect(url_for("studentLogin"))

def editStudentProfile():
    if "student" not in session:
        return redirect(url_for("studentLogin"))
    
    email = session["student"]
    
    if request.method == "GET":
        try:
            with DatabaseManager() as cursor:
                cursor.execute("SELECT * FROM student WHERE email=?", (email,))
                student_row = cursor.fetchone()
                
                # Convert row to dictionary for compatibility
                student = None
                if student_row:
                    student = {}
                    for idx, col in enumerate(cursor.description):
                        student[col[0]] = student_row[idx]
                logger.info(f"Student profile edit page loaded for: {email}")
                return render_template("user/editStudent.html", student=student)
        except sqlite3.Error as db_error:
            logger.error(f"Database error loading student profile: {db_error}")
            flash("A database error occurred while loading your profile", "error")
            return redirect(url_for("studentDashboard"))
        except Exception as e:
            logger.error(f"Error loading student profile: {str(e)}")
            flash("An error occurred while loading your profile", "error")
            return redirect(url_for("studentDashboard"))
    
    else:
        try:
            name = request.form["name"]
            contact = request.form["contact"]
            course = request.form["course"]
            
            # Validate contact number
            is_valid, result = validate_contact_number(contact)
            if not is_valid:
                flash(result, "error")
                return redirect(url_for("studentSignup"))
            contact = result  # Use the sanitized contact number
            
            # Handle profile picture upload
            profile_picture = None
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                profile_picture = handle_profile_picture(file)
                if not profile_picture:
                    flash("Failed to upload profile picture", "error")
                    return redirect(url_for("studentSignup"))
                    logger.info(f"Profile picture uploaded for student: {email}")

            with DatabaseManager() as cursor:
                if profile_picture:
                    # Update profile with new picture
                    sql = "UPDATE student SET name=?, contact=?, course=?, profile_picture=? WHERE email=?"
                    val = (name, contact, course, profile_picture, email)
                else:
                    # Update profile without changing picture
                    sql = "UPDATE student SET name=?, contact=?, course=? WHERE email=?"
                    val = (name, contact, course, email)
                    
                cursor.execute(sql, val)
                logger.info(f"Student profile updated successfully: {email}")
                flash("Profile updated successfully", "success")
                return redirect(url_for("studentDashboard"))
                
        except sqlite3.Error as db_error:
            logger.error(f"Database error updating student profile: {db_error}")
            flash("A database error occurred while updating your profile", "error")
            return redirect(url_for("editStudentProfile"))
        except Exception as e:
            logger.error(f"Error updating student profile: {str(e)}")
            flash("An error occurred while updating your profile", "error")
            return redirect(url_for("editStudentProfile"))


def uploadProfileImage():
    if "student" not in session:
        return redirect(url_for("studentLogin"))

    try:
        sid = session["student_id"]
        file = request.files.get("profile_image")
        
        rel_path = handle_profile_picture(file)
        if rel_path:
            with DatabaseManager() as cursor:
                cursor.execute("UPDATE student SET profile_picture = ? WHERE sid = ?", (rel_path, sid))
                logger.info(f"Profile image updated for student ID: {sid}")
                flash("Profile image updated successfully", "success")
        else:
            logger.warning(f"Invalid file upload attempt for student ID: {sid}")
            flash("Invalid file type. Please upload an image file.", "error")

        return redirect(url_for("studentDashboard"))
    except sqlite3.Error as db_error:
        logger.error(f"Database error updating profile image: {db_error}")
        flash("A database error occurred while updating your profile image", "error")
        return redirect(url_for("studentDashboard"))
    except Exception as e:
        logger.error(f"Error updating profile image: {str(e)}")
        flash("An error occurred while updating your profile image", "error")
        return redirect(url_for("studentDashboard"))


def viewMarks():
    if "student" not in session:
        return redirect(url_for("studentLogin"))

    try:
        email = session["student"]

        with DatabaseManager() as cursor:
            cursor.execute("SELECT sid FROM student WHERE email=?", (email,))
            student_row = cursor.fetchone()
            
            # Convert row to dictionary for compatibility
            student = {}
            for idx, col in enumerate(cursor.description):
                student[col[0]] = student_row[idx]
            
            sid = student["sid"]

            cursor.execute("""
                SELECT sub.subject_name AS subject, m.marks, m.assessment_type
                FROM marks m
                JOIN subjects sub ON m.subid = sub.subid
                WHERE m.sid = ?
                ORDER BY m.mid DESC
            """, (sid,))
            
            # Convert rows to list of dictionaries
            all_marks = []
            for row in cursor.fetchall():
                mark = {}
                for idx, col in enumerate(cursor.description):
                    mark[col[0]] = row[idx]
                all_marks.append(mark)

            logger.info(f"Marks viewed for student ID: {sid}")
            return render_template("user/viewMarks.html", marks=all_marks)
    except sqlite3.Error as db_error:
        logger.error(f"Database error viewing marks: {db_error}")
        flash("A database error occurred while retrieving your marks", "error")
        return redirect(url_for("studentDashboard"))
    except Exception as e:
        logger.error(f"Error viewing marks: {str(e)}")
        flash("An error occurred while retrieving your marks", "error")
        return redirect(url_for("studentDashboard"))


def viewAttendance():
    if "student" not in session:
        return redirect(url_for("studentLogin"))

    try:
        email = session["student"]

        with DatabaseManager() as cursor:
            cursor.execute("SELECT sid FROM student WHERE email=?", (email,))
            student_row = cursor.fetchone()
            
            # Convert row to dictionary for compatibility
            student = {}
            for idx, col in enumerate(cursor.description):
                student[col[0]] = student_row[idx]
            
            sid = student["sid"]

            # First get the attendance details
            cursor.execute("""
                SELECT 
                    sub.subject_name AS subject,
                    a.date,
                    a.time,
                    a.status,
                    COUNT(*) OVER (PARTITION BY sub.subid) as total_classes,
                    SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) OVER (PARTITION BY sub.subid) as present_count
                FROM attendance a
                JOIN subjects sub ON a.subid = sub.subid
                WHERE a.sid = ?
                ORDER BY sub.subject_name, a.date DESC, a.time DESC
            """, (sid,))
            
            # Convert rows to list of dictionaries
            attendance_records = []
            for row in cursor.fetchall():
                record = {}
                for idx, col in enumerate(cursor.description):
                    record[col[0]] = row[idx]
                # Calculate attendance percentage
                if record['total_classes'] > 0:
                    record['percentage'] = (record['present_count'] / record['total_classes']) * 100
                else:
                    record['percentage'] = 0
                attendance_records.append(record)

            logger.info(f"Attendance viewed for student ID: {sid}")
            return render_template("user/viewAttendance.html", attendance=attendance_records)
    except sqlite3.Error as db_error:
        logger.error(f"Database error viewing attendance: {db_error}")
        flash("A database error occurred while retrieving your attendance", "error")
        return redirect(url_for("studentDashboard"))
    except Exception as e:
        logger.error(f"Error viewing attendance: {str(e)}")
        flash("An error occurred while retrieving your attendance", "error")
        return redirect(url_for("studentDashboard"))

def viewFees():
    if "student" not in session:
        return redirect(url_for("studentLogin"))

    try:
        email = session["student"]

        with DatabaseManager() as cursor:
            cursor.execute("SELECT sid FROM student WHERE email=?", (email,))
            student_row = cursor.fetchone()
            
            # Convert row to dictionary for compatibility
            student = {}
            for idx, col in enumerate(cursor.description):
                student[col[0]] = student_row[idx]
            
            sid = student["sid"]

            cursor.execute("""
                SELECT amount, status, due_date, fee_type
                FROM fees
                WHERE sid = ?
                ORDER BY due_date ASC
            """, (sid,))
            
            # Convert rows to list of dictionaries
            fees = []
            for row in cursor.fetchall():
                fee = {}
                for idx, col in enumerate(cursor.description):
                    fee[col[0]] = row[idx]
                fees.append(fee)

            logger.info(f"Fees viewed for student ID: {sid}")
            return render_template("user/viewFees.html", fees=fees)
    except sqlite3.Error as db_error:
        logger.error(f"Database error viewing fees: {db_error}")
        flash("A database error occurred while retrieving your fees", "error")
        return redirect(url_for("studentDashboard"))
    except Exception as e:
        logger.error(f"Error viewing fees: {str(e)}")
        flash("An error occurred while retrieving your fees", "error")
        return redirect(url_for("studentDashboard"))

def viewTimetable():
    if "student" not in session:
        return redirect(url_for("studentLogin"))

    try:
        with DatabaseManager() as cursor:
            # Get student's course
            cursor.execute("SELECT course FROM student WHERE email = ?", (session["student"],))
            student_row = cursor.fetchone()
            
            # Convert row to dictionary for compatibility
            student_course = {}
            if student_row:
                for idx, col in enumerate(cursor.description):
                    student_course[col[0]] = student_row[idx]
            
            if not student_course or not student_course["course"]:
                logger.warning(f"No course assigned to student: {session['student']}")
                flash("No course assigned to student", "error")
                return redirect(url_for("studentDashboard"))

            course_name = student_course["course"]

            # Get course id
            cursor.execute("SELECT cid FROM courses WHERE course_name = ?", (course_name,))
            course_row = cursor.fetchone()
            
            # Convert row to dictionary for compatibility
            course = {}
            if course_row:
                for idx, col in enumerate(cursor.description):
                    course[col[0]] = course_row[idx]
            
            if not course:
                logger.warning(f"Course not found: {course_name}")
                flash("Course not found", "error")
                return redirect(url_for("studentDashboard"))

            course_id = course["cid"]

            # Fetch timetable entries for the student's course with time formatted as string
            # SQLite doesn't have TIME_FORMAT, so we'll format the time in Python
            # SQLite doesn't have FIELD for custom ordering, so we'll use CASE statement
            cursor.execute("""
                SELECT t.day_of_week, 
                       t.time_start, 
                       t.time_end, 
                       s.subject_name, 
                       te.name as teacher_name,
                       CASE t.day_of_week
                           WHEN 'Monday' THEN 1
                           WHEN 'Tuesday' THEN 2
                           WHEN 'Wednesday' THEN 3
                           WHEN 'Thursday' THEN 4
                           WHEN 'Friday' THEN 5
                           WHEN 'Saturday' THEN 6
                           WHEN 'Sunday' THEN 7
                       END as day_order
                FROM timetable t
                JOIN subjects s ON t.subid = s.subid
                JOIN teacher te ON t.tid_teacher = te.tid
                WHERE t.course_id = ?
                ORDER BY day_order, t.time_start
            """, (course_id,))
            
            # Convert rows to list of dictionaries and format time strings
            timetable_entries = []
            for row in cursor.fetchall():
                entry = {}
                for idx, col in enumerate(cursor.description):
                    entry[col[0]] = row[idx]
                
                # Format time strings (assuming time_start and time_end are in HH:MM:SS format)
                if 'time_start' in entry and entry['time_start']:
                    try:
                        time_parts = entry['time_start'].split(':')[:2]  # Get hours and minutes
                        entry['time_start'] = ':'.join(time_parts)  # Format as HH:MM
                    except (AttributeError, IndexError):
                        pass  # Keep original if formatting fails
                        
                if 'time_end' in entry and entry['time_end']:
                    try:
                        time_parts = entry['time_end'].split(':')[:2]  # Get hours and minutes
                        entry['time_end'] = ':'.join(time_parts)  # Format as HH:MM
                    except (AttributeError, IndexError):
                        pass  # Keep original if formatting fails
                        
                timetable_entries.append(entry)

            logger.info(f"Timetable viewed for student: {session['student']} (Course: {course_name})")
            return render_template("user/studentTimetable.html", timetable_entries=timetable_entries)
    except sqlite3.Error as db_error:
        logger.error(f"Database error viewing timetable: {db_error}")
        flash("A database error occurred while retrieving your timetable", "error")
        return redirect(url_for("studentDashboard"))
    except Exception as e:
        logger.error(f"Error viewing timetable: {str(e)}")
        flash("An error occurred while retrieving your timetable", "error")
        return redirect(url_for("studentDashboard"))

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

