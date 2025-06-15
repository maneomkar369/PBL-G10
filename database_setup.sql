CREATE DATABASE IF NOT EXISTS college_erp;
USE college_erp;

CREATE TABLE IF NOT EXISTS student (
    sid INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    contact VARCHAR(20),
    course VARCHAR(100),
    profile_picture VARCHAR(255) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS admin (
    aid INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

-- Insert a test student
INSERT INTO student (name, email, password, contact, course) 
VALUES ('Test Student', 'test@example.com', 'test123', '1234567890', 'Computer Science');

-- Insert admin user
INSERT INTO admin (username, password) 
VALUES ('admin', 'admin123'); 

SELECT * FROM student; 


--------teacher end---------
CREATE TABLE teacher (
    tid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100),
    password VARCHAR(100)
);

INSERT INTO teacher (name, email, password) VALUES
('Sanjay', 'sanjay@gmail.com', '1234');

CREATE TABLE course (
    cid INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    tid INT,
    FOREIGN KEY (tid) REFERENCES teacher(tid)
);

INSERT INTO course (name, tid) VALUES
('Mathematics', 1),
('Physics', 1);

-- Create attendance table
    CREATE TABLE attendance (
        aid INT PRIMARY KEY AUTO_INCREMENT,
        sid INT NOT NULL,
        tid INT NOT NULL,
        cid INT NOT NULL,
        date DATE NOT NULL,
        status ENUM('present', 'absent') NOT NULL,
        FOREIGN KEY (sid) REFERENCES student(sid),
        FOREIGN KEY (tid) REFERENCES teacher(tid),
        FOREIGN KEY (cid) REFERENCES course(cid)
    );

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create marks table
    CREATE TABLE marks (
        mid INT PRIMARY KEY AUTO_INCREMENT,
        sid INT NOT NULL,
        tid INT NOT NULL,
        cid INT NOT NULL,
        assessment_type ENUM('Assignment', 'Midterm', 'Final', 'Quiz', 'Project') NOT NULL,
        marks INT NOT NULL CHECK (marks >= 0 AND marks <= 100),
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sid) REFERENCES student(sid),
        FOREIGN KEY (tid) REFERENCES teacher(tid),
        FOREIGN KEY (cid) REFERENCES course(cid)
    );
