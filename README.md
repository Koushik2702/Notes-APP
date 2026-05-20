# Notes App API

A simple Notes Management Backend built using FastAPI.

## Features

* User Registration and Login
* JWT Authentication
* Password Hashing using bcrypt
* Create, Read, Update and Delete Notes
* Search Notes
* Pagination for Notes API
* Share Notes with Other Users
* Permission-based Access Control
* Swagger API Documentation
* SQLite Database using SQLAlchemy

---

## Tech Stack

* FastAPI
* Python
* SQLite
* SQLAlchemy
* JWT
* Passlib / bcrypt
* Uvicorn

---

## Project Structure

```bash
.
├── main.py
├── auth.py
├── database.py
├── models.py
├── schemas.py
├── requirements.txt
└── .gitignore
```

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Koushik2702/Notes-APP.git
cd Notes-APP
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Mac/Linux

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Server

```bash
uvicorn main:app --reload
```

Server will start at:

```bash
http://127.0.0.1:8000
```

---

## API Documentation

Swagger Docs:

```bash
http://127.0.0.1:8000/docs
```

---

## Authentication

This project uses JWT Token Authentication.

After login:

1. Copy the access token
2. Click "Authorize" in Swagger
3. Enter:

```bash
Bearer your_token
```

---

## Main APIs

### Auth APIs

* Register User
* Login User

### Notes APIs

* Create Note
* Get All Notes
* Search Notes
* Update Note
* Delete Note
* Share Notes with Other Users

---

## Future Improvements

* AI-powered note summarization
* Frontend Integration
* Docker Support
* PostgreSQL Support
* Deployment on Render/Railway

---

## Author

Sai Koushik
