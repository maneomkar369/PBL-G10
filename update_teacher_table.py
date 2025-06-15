import sqlite3

def update_teacher_table():
    # Connect to SQLite database
    conn = sqlite3.connect('college_erp.db')
    cursor = conn.cursor()
    
    try:
        # Create a temporary table with the new schema
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_new (
            tid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            branch TEXT,
            contact TEXT,
            profile_picture TEXT
        )
        ''')
        
        # Copy data from old table to new table
        cursor.execute('''
        INSERT INTO teacher_new (tid, name, email, password, branch, profile_picture)
        SELECT tid, name, email, password, branch, profile_picture FROM teacher
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE teacher')
        
        # Rename new table to teacher
        cursor.execute('ALTER TABLE teacher_new RENAME TO teacher')
        
        # Commit the changes
        conn.commit()
        print("Successfully updated teacher table with contact field")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    update_teacher_table()
