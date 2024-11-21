### **Flask-Based Chemical Data Management Application**

---

### **Overview**
This Flask application is designed to facilitate the management and analysis of chemical data. It allows users to register, log in, upload data files, and visualize uploaded data in a paginated format. The app features user roles (admin and regular users), duplicate data detection, user approval workflows, and data integrity mechanisms.

---

### **Features**
- **User Authentication**:
  - User registration with email and password.
  - Secure password storage using hashed passwords.
  - Login/logout functionality.
  - Admin approval for new users.
  
- **File Uploads**:
  - Supports `.csv`, `.tsv`, `.xlsx`, and `.xls` file formats.
  - Validates and processes data files.
  - Detects and prevents duplicate entries during file uploads.
  
- **Data Management**:
  - Stores chemical data with details such as species, chemical name, amount, and DOI.
  - Tracks uploaded files and the respective user who uploaded them.
  - Displays data with pagination using Flask-Paginate.

- **Admin Dashboard**:
  - Admin privileges to approve or delete users.
  - User management interface with a list of all registered users.

---

### **Requirements**
- Python 3.x
- Flask and related extensions:
  - `flask`
  - `flask_sqlalchemy`
  - `flask_login`
  - `flask_wtf`
  - `flask_paginate`
- SQLite (as the database backend)
- Pandas (for file processing)
- SQLAlchemy
- Bootstrap 4 (for frontend styling)

---

### **Setup Instructions**
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**:
   Create a virtual environment and install the required libraries:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set Up the Database**:
   - Run the app to initialize the database:
     ```bash
     python app.py
     ```
   - The application automatically creates an admin user:
     - Username: `********`
     - Password: `********`

4. **Run the Application**:
   Start the Flask development server:
   ```bash
   flask run
   ```

5. **Access the App**:
   Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

---

### **Folder Structure**
```
project-directory/
│
├── app.py                # Main application file
├── gsdb4.db              # SQLite database file
├── uploads/              # Folder for storing uploaded files
├── templates/            # HTML templates
│   ├── home.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── show_data.html
│   ├── admin.html
│   └── about.html
├── static/               # Static files (CSS, JavaScript, images)
└── requirements.txt      # List of dependencies
```

---

### **Usage**
1. **User Registration**:
   - Register on the `/register` page.
   - Wait for admin approval before logging in.

2. **File Upload**:
   - Log in and navigate to `/upload`.
   - Upload a valid file (`.csv`, `.tsv`, `.xlsx`, or `.xls`).

3. **View Data**:
   - Go to `/show` to view the uploaded data.

4. **Admin Actions**:
   - Access `/admin` to approve or delete users.

---

### **Admin Actions**
- To create additional admin users:
  ```python
  admin = User(username='new_admin', email='new_admin@example.com',
               password=generate_password_hash('password'),
               is_admin=True, is_approved=True)
  db.session.add(admin)
  db.session.commit()
  ```

---

### **Future Improvements**
- Add support for advanced data analytics.
- Implement role-based data access.
- Integrate additional visualization tools for chemical data.

---

**License**: [MIT License](LICENSE)  
**Author**: [Dhananjay Sharma]  
