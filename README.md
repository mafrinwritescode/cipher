# Cipher - Multi-User Exam Preparation Platform

## Table of Contents

Project Overview
Features
Installation
Running the Application
Database Initialization
Project Structure
Dependencies
Contributors

## Project Overview
Cipher is a multi-user web application designed to help users prepare for exams. It allows admins to manage subjects, quizzes, and users, while users can attempt quizzes, track their scores, and review performance.

## Features
### ✅ Admin Features:
Create, edit, and delete subjects, quizzes, and questions.

Manage user accounts.

View summary charts of quizzes and users.

Search functionality for users, subjects, quizzes, and questions.

### ✅ User Features:
Register, log in, and attempt quizzes.

Track past quiz attempts and scores.

View quiz results and performance analytics.

### ✅ Additional Features:
Timer functionality for quizzes.

Responsive and user-friendly Bootstrap-based UI.

## Installation
🔹 Step 1: Clone the Repository
```
git clone https://github.com/23f2001933/cipher.git
cd cipher
```
🔹 Step 2: Create a Virtual Environment (optional)
```
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows
```
🔹 Step 3: Install Dependencies
```
pip install -r requirements.txt
```
## Running the Application
🔹 Step 1: Set Environment Variables (Optional)
```
export FLASK_APP=app.py
export FLASK_ENV=development
(For Windows, use set instead of export)
```
🔹 Step 2: Run Flask Server
```
flask run
```
By default, the app runs on http://127.0.0.1:5000/.

## Database Initialization
To initialize the SQLite database, run:

```python database.py```

This will create necessary tables and populate them with default admin credentials.

Admin Login Credentials:

Username: admin@gmail.com

Password: admin123

## Project Structure
```
/cipher
│── /static              # CSS, JavaScript, Images
│── /templates           # Jinja2 HTML Templates
│── database.py          # Database Initialization
│── cipher.db            # Database 
│── app.py               # Main Flask Application
│── README.md            # Project Documentation
│── requirements.txt     # Python Dependencies
```
## Dependencies
To install all dependencies, run:
```
pip install -r requirements.txt
```

## Main dependencies:

Flask

Flask-Login

Flask-WTF

Flask-SQLAlchemy

SQLite


## CONTRIBUTORS
```
MAFRIN S
23f2001933@ds.study.iitm.ac.in
```
=======
## CIPHER
A multi-user exam preparation platform built using Flask, Jinja2, Bootstrap, and SQLite.
