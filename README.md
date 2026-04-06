# 🏨 SandDunes - Hotel Management System

A **Flask + MySQL based Hotel Management System** that allows managing bookings, availability, check-ins, services, and billing.

---

## ✨ Features
- Room availability search
- Room booking with guest details and ID verification
- Check-in / Check-out management
- Service ordering and tracking
- Billing with auto-calculated charges + tax
- Responsive Bootstrap 5 UI
- Custom error pages (404, 500)

---

## 📂 Project Structure
├── app.py

├── requirements.txt 

├── templates/

├── static/

  └── css/style.css 
  
  └── js/script.js 
  
├── db/ 

  └── .env

---

## ⚙️ Installation

### 1️⃣ Clone the repo
```bash
git clone https://github.com/your-username/hotel-management-system.git
cd hotel-management-system
```
### 2️⃣ Create virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```
### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```
### 4️⃣ Configure environment
Create a .env file:
```bash
FLASK_SECRET_KEY=your-secret-key
FLASK_DEBUG=True
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=hotel_management
```
### 5️⃣ Setup MySQL Database
Create a database hotel_management and import the schema (tables: bookings, customers, rooms, services, billing, etc.).

### 6️⃣ Run the app
```bash
python app.py
```
Open 👉 http://127.0.0.1:5000/

🛠️ Tech Stack

Flask (Python)

MySQL

Bootstrap 5 + Font Awesome

Jinja2 Templates

Vanilla JavaScript

