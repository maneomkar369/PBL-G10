e-- Create database if not exists
CREATE DATABASE IF NOT EXISTS college_erp;
USE college_erp;

-- Create student table
CREATE TABLE IF NOT EXISTS student (
    sid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    contact VARCHAR(20),
    course VARCHAR(50),
    profile_picture VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create teacher table
CREATE TABLE IF NOT EXISTS teacher (
    tid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    branch VARCHAR(50),
    profile_picture VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create admin table
CREATE TABLE IF NOT EXISTS admin (
    aid INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create subjects table
CREATE TABLE IF NOT EXISTS subjects (
    subid INT AUTO_INCREMENT PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL,
    course_id INT,
    semester INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(cid)
);

-- Create courses table
CREATE TABLE IF NOT EXISTS courses (
    cid INT AUTO_INCREMENT PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    branch VARCHAR(50) NOT NULL,
    tid INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tid) REFERENCES teacher(tid)
);

-- Create teacher_subjects table
CREATE TABLE IF NOT EXISTS teacher_subjects (
    tsid INT AUTO_INCREMENT PRIMARY KEY,
    tid INT,
    subid INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tid) REFERENCES teacher(tid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    UNIQUE KEY unique_teacher_subject (tid, subid)
);

-- Create marks table
CREATE TABLE IF NOT EXISTS marks (
    mid INT AUTO_INCREMENT PRIMARY KEY,
    sid INT,
    cid INT,
    subid INT,
    tid INT,
    marks INT,
    assessment_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sid) REFERENCES student(sid),
    FOREIGN KEY (cid) REFERENCES courses(cid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    FOREIGN KEY (tid) REFERENCES teacher(tid)
);

-- Create attendance table
CREATE TABLE IF NOT EXISTS attendance (
    aid INT AUTO_INCREMENT PRIMARY KEY,
    sid INT,
    cid INT,
    subid INT,
    tid INT,
    date DATE,
    status ENUM('Present', 'Absent'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sid) REFERENCES student(sid),
    FOREIGN KEY (cid) REFERENCES courses(cid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    FOREIGN KEY (tid) REFERENCES teacher(tid)
); 
-- Create timetable table
CREATE TABLE IF NOT EXISTS timetable (
    tid INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
    time_start TIME NOT NULL,
    time_end TIME NOT NULL,
    subid INT NOT NULL,
    tid_teacher INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(cid),
    FOREIGN KEY (subid) REFERENCES subjects(subid),
    FOREIGN KEY (tid_teacher) REFERENCES teacher(tid)
);
