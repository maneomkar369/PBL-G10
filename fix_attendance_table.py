import sqlite3

def fix_attendance_table():
    # Connect to SQLite database
    conn = sqlite3.connect('college_erp.db')
    cursor = conn.cursor()
    
    try:
        # Drop the existing attendance table
        cursor.execute('DROP TABLE IF EXISTS attendance')
        
        # Create the new attendance table with time column
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
        
        # Commit the changes
        conn.commit()
        print("Successfully recreated attendance table with time column")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_attendance_table()
