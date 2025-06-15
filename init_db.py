import sqlite3

# Connect to SQLite database (will create it if it doesn't exist)
conn = sqlite3.connect('college_erp.db')
cursor = conn.cursor()

# Create admin table
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    aid INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Create student table
cursor.execute('''
CREATE TABLE IF NOT EXISTS student (
    sid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    contact TEXT,
    course TEXT,
    profile_picture TEXT
)
''')

# Create teacher table
cursor.execute('''
CREATE TABLE IF NOT EXISTS teacher (
    tid INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    branch TEXT,
    contact TEXT,
    profile_picture TEXT
)
''')

# Create courses table
cursor.execute('''
CREATE TABLE IF NOT EXISTS courses (
    cid INTEGER PRIMARY KEY AUTOINCREMENT,
    course_name TEXT NOT NULL,
    branch TEXT NOT NULL,
    tid INTEGER,
    FOREIGN KEY (tid) REFERENCES teacher(tid)
)
''')

# Create subjects table
cursor.execute('''
CREATE TABLE IF NOT EXISTS subjects (
    subid INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    course_id INTEGER,
    semester INTEGER,
    FOREIGN KEY (course_id) REFERENCES courses(cid)
)
''')

# Create teacher_subjects table
cursor.execute('''
CREATE TABLE IF NOT EXISTS teacher_subjects (
    tsid INTEGER PRIMARY KEY AUTOINCREMENT,
    tid INTEGER,
    subid INTEGER,
    FOREIGN KEY (tid) REFERENCES teacher(tid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    UNIQUE (tid, subid)
)
''')

# Create marks table
cursor.execute('''
CREATE TABLE IF NOT EXISTS marks (
    mid INTEGER PRIMARY KEY AUTOINCREMENT,
    sid INTEGER,
    cid INTEGER,
    subid INTEGER,
    tid INTEGER,
    marks INTEGER,
    assessment_type TEXT,
    FOREIGN KEY (sid) REFERENCES student(sid),
    FOREIGN KEY (cid) REFERENCES courses(cid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    FOREIGN KEY (tid) REFERENCES teacher(tid)
)
''')

# Create attendance table
cursor.execute('''
CREATE TABLE IF NOT EXISTS attendance (
    aid INTEGER PRIMARY KEY AUTOINCREMENT,
    sid INTEGER,
    cid INTEGER,
    subid INTEGER,
    tid INTEGER,
    date TEXT,
    time TEXT,
    status TEXT,
    FOREIGN KEY (sid) REFERENCES student(sid),
    FOREIGN KEY (cid) REFERENCES courses(cid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    FOREIGN KEY (tid) REFERENCES teacher(tid)
)
''')

# Create timetable table
cursor.execute('''
CREATE TABLE IF NOT EXISTS timetable (
    tid INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT,
    start_time TEXT,
    end_time TEXT,
    subject_id INTEGER,
    teacher_id INTEGER,
    course_id INTEGER,
    room TEXT,
    FOREIGN KEY (subject_id) REFERENCES subjects(subid),
    FOREIGN KEY (teacher_id) REFERENCES teacher(tid),
    FOREIGN KEY (course_id) REFERENCES courses(cid)
)
''')

# Create fees table
cursor.execute('''
CREATE TABLE IF NOT EXISTS fees (
    feeid INTEGER PRIMARY KEY AUTOINCREMENT,
    sid INTEGER,
    amount REAL,
    
    status TEXT,
    due_date TEXT,
    payment_date TEXT,
    FOREIGN KEY (sid) REFERENCES student(sid)
)
''')

# Create events table
cursor.execute('''
DROP TABLE IF EXISTS event_registrations
''')

cursor.execute('''
DROP TABLE IF EXISTS events
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    event_date TEXT NOT NULL,
    event_type TEXT CHECK(event_type IN ('cultural', 'technical', 'sports', 'academic')) DEFAULT 'cultural',
    location TEXT DEFAULT 'Main Campus',
    duration TEXT DEFAULT '2h',
    capacity INTEGER DEFAULT 100,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS event_registrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    user_id TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK(user_type IN ('student', 'teacher')),
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    UNIQUE(event_id, user_id, user_type)
)
''')

# Insert default admin user
cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)", ("admin", "admin123"))

# Insert sample courses
cursor.execute("INSERT OR IGNORE INTO courses (course_name, branch) VALUES (?, ?)", ("Computer Science", "CS"))
cursor.execute("INSERT OR IGNORE INTO courses (course_name, branch) VALUES (?, ?)", ("Information Technology", "IT"))
cursor.execute("INSERT OR IGNORE INTO courses (course_name, branch) VALUES (?, ?)", ("Electronics", "EC"))

# Insert sample subjects
cursor.execute("INSERT OR IGNORE INTO subjects (subject_name, course_id, semester) VALUES (?, ?, ?)", ("Programming", 1, 1))
cursor.execute("INSERT OR IGNORE INTO subjects (subject_name, course_id, semester) VALUES (?, ?, ?)", ("Database Systems", 1, 2))
cursor.execute("INSERT OR IGNORE INTO subjects (subject_name, course_id, semester) VALUES (?, ?, ?)", ("Web Development", 2, 1))

# Insert sample events
events_data = [
    (
        'Annual Cultural Fest 2025',
        'Join us for an exciting celebration of art, music, and dance at our annual cultural festival.',
        '2025-06-20',
        'cultural',
        'Main Auditorium',
        '6h',
        500,
        'admin'
    ),
    (
        'Tech Symposium 2025',
        'A technical symposium featuring cutting-edge research presentations and workshops.',
        '2025-07-15',
        'technical',
        'Conference Hall',
        '8h',
        200,
        'admin'
    ),
    (
        'Sports Meet 2025',
        'Annual inter-college sports competition featuring various athletic events.',
        '2025-08-05',
        'sports',
        'Sports Complex',
        '12h',
        1000,
        'admin'
    ),
    (
        'Academic Conference',
        'International academic conference on emerging technologies and research.',
        '2025-09-10',
        'academic',
        'Seminar Hall',
        '8h',
        150,
        'admin'
    )
]

# Insert sample events
cursor.executemany("""
    INSERT INTO events (
        title, description, event_date, event_type, location, duration, capacity, created_by
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", events_data)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized successfully with tables and sample data.")