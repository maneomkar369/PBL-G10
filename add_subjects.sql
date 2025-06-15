USE college_erp;

-- Add subjects for Computer Science (CSE)
INSERT INTO subjects (subject_name, course_id, semester) VALUES
-- Semester 1
('Mathematics I', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 1),
('Physics', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 1),
('Chemistry', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 1),
('Programming in C', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 1),
('English', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 1),
-- Semester 2
('Mathematics II', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 2),
('Data Structures', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 2),
('Digital Electronics', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 2),
('Object Oriented Programming', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 2),
('Environmental Studies', (SELECT cid FROM courses WHERE course_name = 'Computer Science' AND branch = 'CSE'), 2);

-- Add subjects for Information Technology (IT)
INSERT INTO subjects (subject_name, course_id, semester) VALUES
-- Semester 1
('Mathematics I', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 1),
('Physics', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 1),
('Chemistry', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 1),
('Programming in C', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 1),
('English', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 1),
-- Semester 2
('Mathematics II', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 2),
('Data Structures', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 2),
('Digital Electronics', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 2),
('Object Oriented Programming', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 2),
('Environmental Studies', (SELECT cid FROM courses WHERE course_name = 'Information Technology' AND branch = 'IT'), 2);

-- Add subjects for AI & DS
INSERT INTO subjects (subject_name, course_id, semester) VALUES
-- Semester 1
('Mathematics I', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 1),
('Physics', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 1),
('Chemistry', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 1),
('Programming in C', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 1),
('English', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 1),
-- Semester 2
('Mathematics II', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 2),
('Data Structures', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 2),
('Digital Electronics', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 2),
('Object Oriented Programming', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 2),
('Environmental Studies', (SELECT cid FROM courses WHERE course_name = 'Artificial Intelligence' AND branch = 'AI & DS'), 2);

-- Add subjects for ENTC
INSERT INTO subjects (subject_name, course_id, semester) VALUES
-- Semester 1
('Mathematics I', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 1),
('Physics', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 1),
('Chemistry', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 1),
('Basic Electronics', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 1),
('English', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 1),
-- Semester 2
('Mathematics II', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 2),
('Network Analysis', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 2),
('Digital Electronics', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 2),
('Electronic Devices', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 2),
('Environmental Studies', (SELECT cid FROM courses WHERE course_name = 'Electronics and Telecommunication' AND branch = 'ENTC'), 2); 