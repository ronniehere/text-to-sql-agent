-- Creating the employees table
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    hire_date DATE,
    salary DECIMAL(10, 2),
    email VARCHAR(100) UNIQUE,
    job_title VARCHAR(100),
    status VARCHAR(20),
    phone_number VARCHAR(20),
    manager_id INTEGER,
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);

-- Inserting sample data
INSERT INTO employees (first_name, last_name, department, hire_date, salary, email, job_title, status, phone_number, manager_id) VALUES
('John', 'Doe', 'Engineering', '2020-01-15', 75000.00, 'john.doe@company.com', 'Software Engineer', 'Active', '555-0101', NULL),
('Jane', 'Smith', 'Engineering', '2019-03-22', 80000.00, 'jane.smith@company.com', 'Senior Engineer', 'Active', '555-0102', 1),
('Alice', 'Johnson', 'HR', '2021-06-10', 65000.00, 'alice.johnson@company.com', 'HR Manager', 'Active', '555-0103', NULL),
('Bob', 'Williams', 'Engineering', '2022-09-01', 70000.00, 'bob.williams@company.com', 'Software Engineer', 'Active', '555-0104', 1),
('Emma', 'Brown', 'Marketing', '2020-11-12', 68000.00, 'emma.brown@company.com', 'Marketing Specialist', 'Active', '555-0105', NULL),
('Michael', 'Davis', 'Engineering', '2018-07-19', 85000.00, 'michael.davis@company.com', 'Tech Lead', 'Active', '555-0106', 1),
('Sarah', 'Wilson', 'HR', '2023-02-25', 62000.00, 'sarah.wilson@company.com', 'HR Coordinator', 'Active', '555-0107', 3),
('David', 'Miller', 'Engineering', '2023-01-05', 72000.00, 'david.miller@company.com', 'DevOps Engineer', 'Active', '555-0108', 6),
('Olivia', 'Garcia', 'Marketing', '2021-09-15', 69000.00, 'olivia.garcia@company.com', 'Content Strategist', 'Active', '555-0109', 5),
('James', 'Martinez', 'Finance', '2022-03-10', 73000.00, 'james.martinez@company.com', 'Financial Analyst', 'Active', '555-0110', NULL),
('Emily', 'Rodriguez', 'Engineering', '2020-06-01', 76000.00, 'emily.rodriguez@company.com', 'Frontend Developer', 'Active', '555-0111', 6),
('Daniel', 'Lopez', 'Sales', '2019-08-20', 70000.00, 'daniel.lopez@company.com', 'Account Executive', 'Active', '555-0112', NULL),
('Sophia', 'Hernandez', 'Sales', '2021-12-01', 68000.00, 'sophia.hernandez@company.com', 'Sales Associate', 'Active', '555-0113', 10),
('Matthew', 'Lee', 'Engineering', '2022-04-11', 74000.00, 'matthew.lee@company.com', 'Backend Developer', 'Active', '555-0114', 6),
('Chloe', 'Walker', 'Finance', '2020-02-17', 71000.00, 'chloe.walker@company.com', 'Accountant', 'Active', '555-0115', 9),
('Anthony', 'Hall', 'HR', '2017-05-30', 80000.00, 'anthony.hall@company.com', 'HR Director', 'Active', '555-0116', NULL),
('Grace', 'Allen', 'Marketing', '2023-04-01', 66000.00, 'grace.allen@company.com', 'SEO Specialist', 'Active', '555-0117', 5);