import sqlite3
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('db_config')

# Thread-local storage for database connections
_thread_local = threading.local()

# Database configuration
DATABASE_PATH = 'college_erp.db'

def get_db_connection():
    """Get a database connection for the current thread.
    Creates a new connection if one doesn't exist.
    
    Returns:
        sqlite3.Connection: A SQLite connection object
    """
    if not hasattr(_thread_local, 'connection'):
        try:
            # Create a new connection for this thread
            _thread_local.connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
            _thread_local.connection.row_factory = sqlite3.Row
            logger.info(f"Created new database connection for thread {threading.current_thread().name}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    return _thread_local.connection

def close_db_connection():
    """Close the database connection for the current thread if it exists."""
    if hasattr(_thread_local, 'connection'):
        try:
            _thread_local.connection.close()
            delattr(_thread_local, 'connection')
            logger.info(f"Closed database connection for thread {threading.current_thread().name}")
        except sqlite3.Error as e:
            logger.error(f"Error closing database connection: {e}")

class DatabaseManager:
    """Context manager for database connections"""
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # An exception occurred, roll back the transaction
            logger.error(f"Transaction rolled back due to {exc_type.__name__}: {exc_val}")
            self.conn.rollback()
        else:
            # No exception, commit the transaction
            self.conn.commit()
        
        # Close the cursor but keep the connection open for reuse
        if self.cursor:
            self.cursor.close()

# Legacy connection for backward compatibility
# This should be gradually phased out in favor of the DatabaseManager
con = get_db_connection()

# Register an atexit handler to close all connections when the application exits
import atexit

@atexit.register
def cleanup_connections():
    """Close all database connections when the application exits."""
    close_db_connection()
    logger.info("All database connections closed")
