#1. Create database
#Creates the database university_services where all tables and data will be stored.
#Switches the active database to university_services for subsequent operations

CREATE DATABASE university_services;
USE university_services;

#2. Students Table
#This table satisfies the 1st table requirement with a primary key (student_id) and a unique constraint (email).
CREATE TABLE Students (
    student_id VARCHAR(10) PRIMARY KEY,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100) UNIQUE
);


#3. Services Table
#Creates the Services table to store the types of services available like Library, IT Support. 
#Primary Key: service_id is automatically generated and ensures each service has a unique identifier.
CREATE TABLE Services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(50),
    base_cost DECIMAL(6,2)
);

#4. StudentServices Table (Bridge Table)
#This table satisfies the 3rd table requirement, linking students to services with foreign keys (student_id and service_id).
CREATE TABLE StudentServices (
    student_service_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(10),
    service_id INT,
    service_date DATE,
    service_cost DECIMAL(6,2),
    FOREIGN KEY (student_id) REFERENCES Students(student_id),
    FOREIGN KEY (service_id) REFERENCES Services(service_id)
);

#Insert Sample Data
INSERT INTO Students VALUES
('S101','Ahmed','Ali','ahmed@example.com'),
('S102','Sara','Noor','sara@example.com'),
('S103','John','Lee','john@example.com');

INSERT INTO Services (service_name, base_cost) VALUES
('Library',10),
('IT Support',5),
('Counseling',20),
('Sports Center',15);

INSERT INTO StudentServices (student_id, service_id, service_date, service_cost) VALUES
('S101',1,'2025-01-01',10),
('S101',2,'2025-01-02',5),
('S102',3,'2025-01-05',20),
('S103',4,'2025-01-03',15),
('S103',2,'2025-01-04',5),
('S103',3,'2025-01-06',20);

#Create Indexes
CREATE INDEX idx_student_email #emial index
ON Students(email);

CREATE INDEX idx_service_name #name index
ON Services(service_name);

CREATE INDEX idx_student_service #composite index
ON StudentServices(student_id, service_id);

#Create Views
#Student Service Details
#This view allows easy access to student service information without repeatedly writing complex queries.
CREATE VIEW vw_student_services AS
SELECT 
    s.student_id,
    CONCAT(s.first_name,' ',s.last_name) AS student_name,
    sv.service_name,
    ss.service_date,
    ss.service_cost
FROM Students s
JOIN StudentServices ss ON s.student_id = ss.student_id
JOIN Services sv ON ss.service_id = sv.service_id;

#Total Cost per Student
#This view is useful for cost tracking per student.
CREATE VIEW vw_total_cost_per_student AS
SELECT 
    student_id,
    SUM(service_cost) AS total_cost
FROM StudentServices
GROUP BY student_id;

#SQL Queries
SELECT * FROM vw_student_services;
SELECT * FROM vw_total_cost_per_student;

#-------------Count How Many Times Each Service Is Used
#It uses JOIN to link the StudentServices table with the Services table and GROUP BY to aggregate data by service_name.
SELECT 
    sv.service_name,
    COUNT(*) AS usage_count
FROM StudentServices ss
JOIN Services sv ON ss.service_id = sv.service_id
GROUP BY sv.service_name;

#--------------Students Who Used Counseling
#Uses JOIN to combine Students, StudentServices, and Services and filters by service_name = 'Counseling'.
SELECT DISTINCT 
    s.first_name,
    s.last_name
FROM Students s
JOIN StudentServices ss ON s.student_id = ss.student_id
JOIN Services sv ON ss.service_id = sv.service_id
WHERE sv.service_name = 'Counseling';

#Average Cost of Services
SELECT AVG(service_cost) AS average_service_cost
FROM StudentServices;







































