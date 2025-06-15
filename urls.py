from app import app
from flask import render_template, request, redirect, url_for, flash, jsonify
import admin as admin
import user as user
import teacher as teacher
import sqlite3
from db_config import DatabaseManager, logger

# Admin routes
import admin
app.add_url_rule("/adminLogin", view_func=admin.adminLogin, methods=["GET", "POST"])
app.add_url_rule("/adminDashboard", view_func=admin.adminDashboard)
app.add_url_rule("/addStudent", view_func=admin.addStudent, methods=["GET", "POST"])
app.add_url_rule("/deleteStudent/<sid>", view_func=admin.deleteStudent)
app.add_url_rule("/editStudent/<sid>", view_func=admin.editStudent, methods=["GET", "POST"])
app.add_url_rule("/adminLogout", view_func=admin.adminLogout)
app.add_url_rule("/manageTeacherSubjects", view_func=admin.manageTeacherSubjects, methods=["GET"])
app.add_url_rule("/adminAddSubject/<int:tid>", view_func=admin.adminAddSubject, methods=["POST"])
app.add_url_rule("/adminRemoveSubject/<int:tid>/<int:subid>", view_func=admin.adminRemoveSubject, methods=["POST"])

# Admin Fee Management Routes
app.add_url_rule("/admin/manage_fees", view_func=admin.manageFees, methods=["GET"])
app.add_url_rule("/admin/add_fee", view_func=admin.addFee, methods=["GET", "POST"])
app.add_url_rule("/admin/edit_fee/<int:feeid>", view_func=admin.editFee, methods=["GET", "POST"])
app.add_url_rule("/admin/update_fee_status/<int:feeid>", view_func=admin.updateFeeStatus, methods=["POST"])
app.add_url_rule("/admin/delete_fee/<int:feeid>", view_func=admin.deleteFee, methods=["GET"])
# Add this with other admin routes
app.add_url_rule("/admin/fee-report", view_func=admin.feeReport, methods=["GET"], endpoint="feeReport")
# New timetable management routes for admin
app.add_url_rule('/admin/manageTimetable', 'manageTimetable', admin.manageTimetable)
app.add_url_rule('/admin/addTimetableEntry', 'addTimetableEntry', admin.addTimetableEntry, methods=['POST'])
app.add_url_rule('/admin/deleteTimetableEntry/<int:tid>', 'deleteTimetableEntry', admin.deleteTimetableEntry, methods=['POST'])
# Course and Subject Management
app.add_url_rule("/admin/manageCourses", view_func=admin.manageCourses, methods=["GET"])
app.add_url_rule("/admin/addCourse", view_func=admin.addCourse, methods=["POST"])
app.add_url_rule("/admin/deleteCourse/<int:cid>", view_func=admin.deleteCourse, methods=["GET"])
app.add_url_rule("/admin/manageSubjects", view_func=admin.manageSubjects, methods=["GET"])
app.add_url_rule("/admin/addSubject", view_func=admin.addSubject, methods=["POST"])
app.add_url_rule("/admin/deleteSubject/<int:subid>", view_func=admin.deleteSubject, methods=["GET"])

from events import events_bp
app.register_blueprint(events_bp)
 
# ... existing routes ...


# User routes
app.add_url_rule("/Signup", view_func=user.studentSignup, methods=["GET", "POST"])
app.add_url_rule("/studentLogin", view_func=user.studentLogin, methods=["GET", "POST"])
app.add_url_rule("/studentDashboard", view_func=user.studentDashboard)
app.add_url_rule("/studentLogout", view_func=user.studentLogout)
app.add_url_rule("/editStudent", view_func=user.editStudentProfile, methods=["GET", "POST"])
app.add_url_rule("/viewMarks", view_func=user.viewMarks)
app.add_url_rule("/student/viewAttendance", view_func=user.viewAttendance)
app.add_url_rule("/viewFees", view_func=user.viewFees, methods=["GET"])
app.add_url_rule('/student/viewTimetable', 'viewTimetable', user.viewTimetable)



# Teacher routes
app.add_url_rule("/Signup", view_func=teacher.teacherSignup, methods=["GET", "POST"])
app.add_url_rule("/teacherLogin", view_func=teacher.teacherLogin, methods=["GET", "POST"])
app.add_url_rule("/teacherDashboard", view_func=teacher.teacherDashboard)
app.add_url_rule("/teacherLogout", view_func=teacher.teacherLogout)
app.add_url_rule("/addMarks", view_func=teacher.addMarks, methods=["GET", "POST"])
app.add_url_rule("/teacher/viewMarks", view_func=teacher.teacherViewMarks, methods=["GET"], endpoint="teacherViewMarks")
app.add_url_rule("/teacher/manageSubjects", view_func=teacher.manageSubjects, methods=["GET"], endpoint="teacher_manage_subjects")
app.add_url_rule("/teacher/addSubject/<int:subid>", view_func=teacher.addSubject, methods=["POST"], endpoint="teacher_add_subject")
app.add_url_rule("/removeSubject/<int:subid>", view_func=teacher.removeSubject, methods=["POST"])





# Signup route
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        user_type = request.form.get("user_type")
        if user_type == "student":
            # Handle student signup
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            contact = request.form.get("contact")
            course = request.form.get("course")
            photo = request.files.get("photo")
            
            # Save student data to database
            try:
                with DatabaseManager() as cursor:
                    # First, check if the course exists
                    cursor.execute("SELECT cid FROM courses WHERE course_name = ?", (course,))
                    course_result = cursor.fetchone()
                    
                    if not course_result:
                        flash(f"Course '{course}' does not exist. Please select a valid course.", "error")
                        return redirect(url_for("signup"))
                    
                    course_id = course_result[0]
                    
                    # Insert student data
                    sql = "INSERT INTO student (name, email, password, contact, course) VALUES (?, ?, ?, ?, ?)"
                    val = (name, email, password, contact, course_id)
                    cursor.execute(sql, val)
                    
                    # Get the last inserted ID
                    sid = cursor.lastrowid
                    
                    # Handle photo upload if provided
                    if photo:
                        filename = f"student_{sid}.jpg"
                        photo.save(f"static/uploads/{filename}")
                        cursor.execute("UPDATE student SET profile_picture = ? WHERE sid = ?", (filename, sid))
                
                flash("Student signup successful!", "success")
                return redirect(url_for("studentLogin"))
            except sqlite3.Error as db_error:
                logger.error(f"Database error during student signup: {db_error}")
                flash(f"Database error during signup: {str(db_error)}", "error")
                return redirect(url_for("signup"))
            except Exception as e:
                logger.error(f"Unexpected error during student signup: {e}")
                flash(f"Error during signup: {str(e)}", "error")
                return redirect(url_for("signup"))
            
        elif user_type == "teacher":
            # Handle teacher signup
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            branch = request.form.get("branch")
            photo = request.files.get("photo")
            
            # Save teacher data to database
            try:
                with DatabaseManager() as cursor:
                    sql = "INSERT INTO teacher (name, email, password, branch) VALUES (?, ?, ?, ?)"
                    val = (name, email, password, branch)
                    cursor.execute(sql, val)
                    
                    # Get the last inserted ID
                    tid = cursor.lastrowid
                    
                    # Handle photo upload if provided
                    if photo:
                        filename = f"teacher_{tid}.jpg"
                        photo.save(f"static/uploads/{filename}")
                        cursor.execute("UPDATE teacher SET profile_picture = ? WHERE tid = ?", (filename, tid))
                
                flash("Teacher signup successful!", "success")
                return redirect(url_for("teacherLogin"))
            except sqlite3.Error as db_error:
                logger.error(f"Database error during teacher signup: {db_error}")
                flash(f"Database error during signup: {str(db_error)}", "error")
                return redirect(url_for("signup"))
            except Exception as e:
                logger.error(f"Unexpected error during teacher signup: {e}")
                flash(f"Error during signup: {str(e)}", "error")
                return redirect(url_for("signup"))
            
        elif user_type == "admin":
            # Handle admin signup
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            
            # Save admin data to database
            try:
                with DatabaseManager() as cursor:
                    sql = "INSERT INTO admin (username, password) VALUES (?, ?)"
                    val = (email, password)  # Using email as username
                    cursor.execute(sql, val)
                
                flash("Admin signup successful!", "success")
                return redirect(url_for("adminLogin"))
            except sqlite3.Error as db_error:
                logger.error(f"Database error during admin signup: {db_error}")
                flash(f"Database error during signup: {str(db_error)}", "error")
                return redirect(url_for("signup"))
            except Exception as e:
                logger.error(f"Unexpected error during admin signup: {e}")
                flash(f"Error during signup: {str(e)}", "error")
                return redirect(url_for("signup"))
            
        else:
            flash("Invalid user type selected", "error")
            return redirect(url_for("signup"))

@app.route("/")
def homepage():
    return render_template('home.html')

app.add_url_rule("/addAttendance", view_func=teacher.addAttendance, methods=["GET", "POST"])
# Removed conflicting routes for viewAttendance
# Re-adding with distinct routes

app.add_url_rule("/teacher/viewAttendance", view_func=teacher.viewAttendance, endpoint="teacherViewAttendance")
app.add_url_rule("/student/viewAttendance", view_func=user.viewAttendance, endpoint="studentViewAttendance")

app.add_url_rule("/uploadProfileImage", view_func=user.uploadProfileImage, methods=["POST"])

@app.route("/get_subjects/<int:course_id>")
def get_subjects(course_id):
    try:
        with DatabaseManager() as cursor:
            # Get subjects for the course
            cursor.execute("""
                SELECT s.subid, s.subject_name, s.semester, c.course_name
                FROM subjects s
                JOIN courses c ON s.course_id = c.cid
                WHERE s.course_id = ?
                ORDER BY s.semester, s.subject_name
            """, (course_id,))
            subjects = cursor.fetchall()
            # Convert to list of dictionaries for JSON serialization
            subject_list = []
            for subject in subjects:
                subject_dict = {
                    'subid': subject['subid'],
                    'subject_name': subject['subject_name'],
                    'semester': subject['semester'],
                    'course_name': subject['course_name']
                }
                subject_list.append(subject_dict)
            logger.info(f"Found {len(subject_list)} subjects for course_id {course_id}")
            return jsonify(subject_list)
    except sqlite3.Error as db_error:
        logger.error(f"Database error fetching subjects for course {course_id}: {db_error}")
        return jsonify([]), 500
    except Exception as e:
        logger.error(f"Unexpected error fetching subjects: {e}")
        return jsonify([]), 500
