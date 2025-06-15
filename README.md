<<<<<<< HEAD
# Event Management Portal

This is an Event Management Portal built using Python and Flask. It allows for managing events, student registrations, teacher management, and more.

## Features

- User authentication (Admin, Teacher, Student)
- Event creation and management
- Student registration for events
- Fee management
- Course and subject management
- Attendance and marks tracking

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd FINAL
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the database:**
    ```bash
    python init_db.py
    ```

5.  **Run the application:**
    ```bash
    python app.py
    ```

    The application should now be running on `http://127.0.0.1:5000/`.

## Database Schema

The project uses a SQLite database (`college_erp.db`). The schema is defined in `database.sql` and `database_setup.sql`.

## Contributing

Feel free to fork the repository and contribute. Please follow standard pull request procedures.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
