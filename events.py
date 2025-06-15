from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
from db_config import DatabaseManager, logger, get_db_connection
import os
import traceback

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    GOOGLE_CALENDAR_ENABLED = True
except ImportError:
    GOOGLE_CALENDAR_ENABLED = False
    logger.warning("Google Calendar integration is disabled (required packages not installed)")

# Blueprint for events
events_bp = Blueprint('events', __name__)

# Helper functions
def get_user_role():
    """Determine the current user's role"""
    if 'admin' in session:
        return 'admin'
    elif 'teacher' in session:
        return 'teacher'
    elif 'student' in session:
        return 'student'
    return None

def handle_database_error(error, context=""):
    """Handle database errors consistently"""
    error_msg = f"Database error during {context}: {str(error)}"
    logger.error(error_msg)
    flash('An error occurred while accessing the database. Please try again.', 'error')
    return redirect(url_for(f'{get_user_role()}Dashboard'))

def role_required(allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_role = get_user_role()
            if not current_role:
                flash("Please login to access this page", "error")
                return redirect(url_for('login'))
            if current_role not in allowed_roles:
                flash("You don't have permission to access this page", "error")
                if current_role == 'admin':
                    return redirect(url_for('adminDashboard'))
                elif current_role == 'teacher':
                    return redirect(url_for('teacherDashboard'))
                else:
                    return redirect(url_for('studentDashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Google Calendar API setup
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    try:
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error setting up Google Calendar service: {e}")
        flash('Unable to connect to Google Calendar service', 'error')
        return None

from app import mail
from flask_mail import Message

# Twilio/Nodemailer setup (placeholders)
def send_sms_notification(to_number, message):
    # Add your Twilio SMS sending logic here
    try:
        # Placeholder for actual SMS sending logic
        logger.info(f"SMS notification sent to {to_number}: {message}")
    except Exception as e:
        logger.error(f"Failed to send SMS notification: {e}")

def send_email_notification(to_email, subject, body):
    try:
        msg = Message(subject, sender='your_email@gmail.com', recipients=[to_email])
        msg.body = body
        mail.send(msg)
        logger.info(f"Email notification sent to {to_email}: {subject}")
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        flash('Failed to send email notification', 'warning')

def get_filtered_events(filters=None, sort_by=None, sort_order='asc'):
    """Get filtered and sorted events"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Start with base query
        query_parts = ["SELECT * FROM events WHERE 1=1"]
        params = []

        # Add filters if provided
        if filters:
            if filters.get('search'):
                query_parts.append("AND (title LIKE ? OR description LIKE ?)")
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
            
            if filters.get('category'):
                query_parts.append("AND category = ?")
                params.append(filters['category'])
            
            if filters.get('date_from'):
                query_parts.append("AND event_date >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                query_parts.append("AND event_date <= ?")
                params.append(filters['date_to'])
            
            if filters.get('venue'):
                query_parts.append("AND venue = ?")
                params.append(filters['venue'])

        # Add sorting
        if sort_by:
            query_parts.append(f"ORDER BY {sort_by} {sort_order}")

        # Combine query parts
        final_query = " ".join(query_parts)
        
        # Execute query with parameters
        cursor.execute(final_query, params)
        
        # Fetch results
        return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Database error in get_filtered_events: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_filtered_events: {e}")
        raise
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

@events_bp.route('/events')
@role_required(['admin', 'teacher', 'student'])
def list_events():
    """List all events with filtering and sorting"""
    try:
        user_role = get_user_role()
        if not user_role:
            flash('Please login to view events', 'error')
            return redirect(url_for('login'))
        
        # Prepare filters
        filters = {
            'search': request.args.get('search'),
            'category': request.args.get('category'),
            'venue': request.args.get('venue'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to')
        }
        
        # Get sort parameters
        sort_by = request.args.get('sort_by', 'event_date')
        sort_order = request.args.get('sort_order', 'asc')
        
        # Get filtered events
        events_list = get_filtered_events(filters, sort_by, sort_order)
        
        # Get unique locations and event types for filters
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT venue FROM events WHERE venue IS NOT NULL")
        locations = [row['venue'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT category FROM events WHERE category IS NOT NULL")
        event_types = [row['category'] for row in cursor.fetchall()]
        
        # Render the appropriate template
        template = 'admin/manageEvents.html' if user_role == 'admin' else 'events/list.html'
        
        return render_template(
            template,
            events=events_list,
            locations=locations,
            event_types=event_types,
            role=user_role,
            filters=filters
        )
        
    except sqlite3.Error as e:
        error_msg = f"Database error in list_events: {e}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        flash('An error occurred while retrieving events', 'error')
        return redirect(url_for(f'{user_role}Dashboard'))
    except Exception as e:
        error_msg = f"Unexpected error in list_events: {e}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for(f'{user_role}Dashboard'))
    finally:
        try:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
        except Exception as e:
            logger.error(f"Error closing database connection in list_events: {e}")

@events_bp.route('/events/create', methods=['GET', 'POST'])
@role_required(['admin'])
def create_event():
    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            title = request.form['title']
            description = request.form['description']
            event_date = request.form['event_date']
            category = request.form.get('category')
            venue = request.form.get('venue')
            capacity = request.form.get('capacity', 0)
            
            # Validate inputs
            if not title or not event_date:
                flash('Title and date are required', 'error')
                return redirect(url_for('events.create_event'))

            # Database operation
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (title, description, event_date, category, venue, capacity, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (title, description, event_date, category, venue, capacity, session.get('admin_id')))
            
            conn.commit()
            flash('Event created successfully', 'success')
            return redirect(url_for('events.list_events'))
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            error_msg = f"Database error in create_event: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            flash('An error occurred while creating the event', 'error')
            return redirect(url_for('events.create_event'))
            
        except Exception as e:
            if conn:
                conn.rollback()
            error_msg = f"Unexpected error in create_event: {e}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            flash('An unexpected error occurred. Please try again.', 'error')
            return redirect(url_for('events.create_event'))
            
        finally:
            try:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()
            except Exception as e:
                logger.error(f"Error closing database connection in create_event: {e}")
    
    # GET request - render the create form
    return render_template('events/create.html')

# Add this helper function at the top with other helpers
def get_event_registrations(cursor, event_id):
    """Get list of registrations for an event"""
    cursor.execute("""
        SELECT er.*, 
               CASE 
                   WHEN er.user_type = 'student' THEN s.name 
                   WHEN er.user_type = 'teacher' THEN t.name 
               END as name,
               CASE 
                   WHEN er.user_type = 'student' THEN s.email 
                   WHEN er.user_type = 'teacher' THEN t.email 
               END as email
        FROM event_registrations er
        LEFT JOIN student s ON er.user_type = 'student' AND er.user_id = s.sid
        LEFT JOIN teacher t ON er.user_type = 'teacher' AND er.user_id = t.tid
        WHERE er.event_id = ?
        ORDER BY er.registered_at DESC
    """, (event_id,))
    return cursor.fetchall()

@events_bp.route('/events/<int:event_id>', methods=['GET'])
@role_required(['admin', 'teacher', 'student'])
def view_event(event_id):
    """Render the detailed view of a specific event."""
    try:
        user_role = get_user_role()
        user_id = None
        if user_role == 'teacher':
            user_id = session.get('teacher')
        elif user_role == 'student':
            user_id = session.get('student')

        with DatabaseManager() as cursor:
            # Get the requested event with registration count
            cursor.execute("""
                SELECT e.*, COUNT(er.id) as registration_count 
                FROM events e 
                LEFT JOIN event_registrations er ON e.id = er.event_id 
                WHERE e.id = ?
                GROUP BY e.id
            """, (event_id,))
            event = cursor.fetchone()
            
            if not event:
                flash('Event not found', 'error')
                return redirect(url_for('events.list_events'))

            # Check if the current user is registered
            is_registered = False
            if user_role in ['teacher', 'student'] and user_id:
                cursor.execute("""
                    SELECT * FROM event_registrations 
                    WHERE event_id = ? AND user_id = ? AND user_type = ?
                """, (event_id, user_id, user_role))
                is_registered = cursor.fetchone() is not None

            # Get registrations for admin view
            registrations = []
            if user_role == 'admin':
                registrations = get_event_registrations(cursor, event_id)

            # Get related events with their registration counts
            cursor.execute("""
                SELECT e.*, COUNT(er.id) as registration_count 
                FROM events e
                LEFT JOIN event_registrations er ON e.id = er.event_id
                WHERE e.id != ? 
                GROUP BY e.id
                ORDER BY 
                CASE 
                    WHEN e.event_date = ? THEN 0 
                    WHEN e.title LIKE ? THEN 1 
                    ELSE 2 
                END, 
                e.event_date DESC 
                LIMIT 3
            """, (event_id, event['event_date'], f"%{event['title'].split()[0]}%"))
            related_events = cursor.fetchall()

            # Can register if:
            # 1. User is student or teacher
            # 2. Not already registered
            # 3. Has valid user_id
            can_register = (
                user_role in ['teacher', 'student'] and
                not is_registered and
                user_id is not None
            )
            
            return render_template('events/view_event.html',
                                event=dict(event),
                                related_events=[dict(e) for e in related_events],
                                role=user_role,
                                is_registered=is_registered,
                                can_register=can_register,
                                registrations=[dict(r) for r in registrations])

    except sqlite3.Error as db_error:
        logger.error(f"Database error in view_event: {db_error}")
        flash('Failed to retrieve event details', 'error')
        return redirect(url_for('events.list_events'))
    except Exception as e:
        logger.error(f"Unexpected error in view_event: {e}")
        flash('An error occurred while loading the event details', 'error')
        return redirect(url_for('events.list_events'))

@events_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@role_required(['admin'])
def edit_event(event_id):
    try:
        with DatabaseManager() as cursor:
            if request.method == 'POST':
                title = request.form['title']
                description = request.form['description']
                event_date = request.form['event_date']
                
                cursor.execute("""
                    UPDATE events 
                    SET title = ?, description = ?, event_date = ? 
                    WHERE id = ?
                """, (title, description, event_date, event_id))
                
                flash('Event updated successfully', 'success')
                return redirect(url_for('events.list_events'))
            
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event = cursor.fetchone()
            if event:
                return render_template('events/edit.html', event=dict(event))
            
            flash('Event not found', 'error')
            return redirect(url_for('events.list_events'))
            
    except sqlite3.Error as e:
        logger.error(f"Database error in edit_event: {e}")
        flash('An error occurred while updating the event', 'error')
        return redirect(url_for('events.list_events'))

@events_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@role_required(['admin'])
def delete_event(event_id):
    try:
        with DatabaseManager() as cursor:
            # First check if event exists
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event = cursor.fetchone()
            if not event:
                flash('Event not found', 'error')
                return redirect(url_for('events.list_events'))
            
            # Delete event registrations first
            cursor.execute("DELETE FROM event_registrations WHERE event_id = ?", (event_id,))
            
            # Then delete the event
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            # The commit is handled by the DatabaseManager context

        flash('Event deleted successfully!', 'success')
    except sqlite3.Error as db_error:
        logger.error(f"Database error in delete_event: {db_error}")
        flash('Failed to delete event due to database error', 'error')
    except Exception as e:
        logger.error(f"Unexpected error in delete_event: {e}")
        flash('An unexpected error occurred', 'error')
        
    return redirect(url_for('events.list_events'))

@events_bp.route('/events/register')
def register_event():
    """Render the event registration page with embedded Google Form."""
    try:
        # Check if user is logged in (optional)
        # if 'student' not in session and 'admin' not in session and 'teacher' not in session:
        #     flash('Please login to register for events', 'warning')
        #     return redirect(url_for('studentLogin'))
        
        return render_template('events/register.html')
    except Exception as e:
        logger.error(f"Unexpected error in register_event: {e}")
        flash('An error occurred while loading the registration page', 'error')
        return redirect(url_for('events.list_events'))

# Add these helper functions near the top of the file, after other imports
def get_registration_count(cursor, event_id):
    """Get the number of registrations for an event"""
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM event_registrations 
        WHERE event_id = ?
    """, (event_id,))
    result = cursor.fetchone()
    return result['count'] if result else 0

def get_registered_users(cursor, event_id):
    """Get list of registered users for an event"""
    cursor.execute("""
        SELECT er.*, 
               CASE 
                   WHEN er.user_type = 'student' THEN s.name 
                   WHEN er.user_type = 'teacher' THEN t.name 
               END as name,
               CASE 
                   WHEN er.user_type = 'student' THEN s.email 
                   WHEN er.user_type = 'teacher' THEN t.email 
               END as email
        FROM event_registrations er
        LEFT JOIN student s ON er.user_type = 'student' AND er.user_id = s.sid
        LEFT JOIN teacher t ON er.user_type = 'teacher' AND er.user_id = t.tid
        WHERE er.event_id = ?
        ORDER BY er.registered_at DESC
    """, (event_id,))
    return cursor.fetchall()

@events_bp.route('/events/<int:event_id>/registrations')
@role_required(['admin'])
def view_registrations(event_id):
    """View all registrations for an event"""
    try:
        with DatabaseManager() as cursor:
            # Get event details
            cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
            event = cursor.fetchone()
            
            if not event:
                flash('Event not found', 'error')
                return redirect(url_for('events.list_events'))
            
            # Get registrations
            registrations = get_registered_users(cursor, event_id)
            
            return render_template('events/registrations.html',
                                event=dict(event),
                                registrations=registrations)
                                
    except sqlite3.Error as e:
        logger.error(f"Database error in view_registrations: {e}")
        flash('An error occurred while retrieving registrations', 'error')
        return redirect(url_for('events.view_event', event_id=event_id))

@events_bp.route('/events/<int:event_id>/register', methods=['POST'])
@role_required(['teacher', 'student'])
def register_for_event(event_id):
    """Register current user for an event"""
    try:
        user_role = get_user_role()
        if not user_role:
            flash('Please login to register for events', 'error')
            return redirect(url_for('login'))

        # Get user ID based on role
        user_id = None
        if user_role == 'teacher':
            user_id = session.get('teacher')
        elif user_role == 'student':
            user_id = session.get('student')
        
        if not user_id:
            flash('Session expired. Please login again', 'error')
            return redirect(url_for('login'))
        
        with DatabaseManager() as cursor:
            # Check if event exists and is upcoming
            cursor.execute("""
                SELECT * FROM events 
                WHERE id = ? 
                AND date(event_date) >= date('now')
            """, (event_id,))
            event = cursor.fetchone()
            
            if not event:
                flash('Event not found or registration closed', 'error')
                return redirect(url_for('events.list_events'))
            
            # Check if already registered
            cursor.execute("""
                SELECT * FROM event_registrations 
                WHERE event_id = ? AND user_id = ? AND user_type = ?
            """, (event_id, user_id, user_role))
            
            if cursor.fetchone():
                flash('You are already registered for this event', 'warning')
                return redirect(url_for('events.view_event', event_id=event_id))
            
            # Register for the event
            cursor.execute("""
                INSERT INTO event_registrations (event_id, user_id, user_type)
                VALUES (?, ?, ?)
            """, (event_id, user_id, user_role))
            
            flash('Successfully registered for the event', 'success')
            
            # Send confirmation email
            try:
                if user_role == 'student':
                    cursor.execute("SELECT email FROM student WHERE sid = ?", (user_id,))
                else:
                    cursor.execute("SELECT email FROM teacher WHERE tid = ?", (user_id,))
                user = cursor.fetchone()
                
                if user and user['email']:
                    send_email_notification(
                        user['email'],
                        f"Registration Confirmation: {event['title']}",
                        f"""
                        Dear participant,

                        Your registration for {event['title']} has been confirmed.
                        
                        Event Details:
                        - Date: {event['event_date']}
                        - Description: {event['description']}
                        
                        Please arrive 15 minutes before the event starts.
                        
                        Best regards,
                        College Events Team
                        """
                    )
            except Exception as e:
                logger.error(f"Failed to send registration confirmation: {e}")
                
            return redirect(url_for('events.view_event', event_id=event_id))
            
    except sqlite3.Error as e:
        logger.error(f"Database error in register_for_event: {e}")
        flash('An error occurred during registration', 'error')
        return redirect(url_for('events.view_event', event_id=event_id))

@events_bp.route('/events/<int:event_id>/cancel-registration', methods=['POST'])
@role_required(['teacher', 'student'])
def cancel_registration(event_id):
    """Cancel registration for an event"""
    try:
        user_role = get_user_role()
        if not user_role:
            flash('Please login to manage registrations', 'error')
            return redirect(url_for('login'))

        # Get user ID based on role
        user_id = None
        if user_role == 'teacher':
            user_id = session.get('teacher')
        elif user_role == 'student':
            user_id = session.get('student')
        
        if not user_id:
            flash('Session expired. Please login again', 'error')
            return redirect(url_for('login'))
        
        with DatabaseManager() as cursor:
            # Check if event exists and is upcoming
            cursor.execute("""
                SELECT * FROM events 
                WHERE id = ? 
                AND date(event_date) >= date('now')
            """, (event_id,))
            event = cursor.fetchone()
            
            if not event:
                flash('Event not found or cancellation period ended', 'error')
                return redirect(url_for('events.list_events'))
            
            # Remove registration
            cursor.execute("""
                DELETE FROM event_registrations 
                WHERE event_id = ? AND user_id = ? AND user_type = ?
            """, (event_id, user_id, user_role))
            
            if cursor.rowcount > 0:
                flash('Your registration has been cancelled', 'success')
            else:
                flash('You were not registered for this event', 'warning')
                
            return redirect(url_for('events.view_event', event_id=event_id))
            
    except sqlite3.Error as e:
        logger.error(f"Database error in cancel_registration: {e}")
        flash('An error occurred while cancelling registration', 'error')
        return redirect(url_for('events.view_event', event_id=event_id))