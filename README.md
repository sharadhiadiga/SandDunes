#  SandDunes

## Hotel Management System

---

#  Overview

SandDunes is a web-based Hotel Management System developed using Flask and MySQL to simplify hotel operations. The application enables hotel staff to efficiently manage room availability, guest bookings, check-ins, check-outs, service requests, and billing through an intuitive and responsive interface.

Designed to streamline day-to-day hotel management, SandDunes provides an organized workflow that improves operational efficiency while delivering a seamless experience for both administrators and guests.

---

#  Features

###  Room Management
- Search available rooms
- View room details and availability
- Efficient room allocation

###  Booking Management
- Create new reservations
- Store guest information
- ID verification during booking
- Manage booking records

###  Check-In & Check-Out
- Quick guest check-in
- Manage check-out process
- Track room occupancy

###  Service Management
- Order hotel services
- Track service requests
- Associate services with guest bookings

###  Billing System
- Automatic bill generation
- Tax calculation
- Service charge inclusion
- Final payment summary

###  Responsive Interface
- Modern Bootstrap 5 design
- Mobile-friendly layout
- Easy navigation

###  Error Handling
- Custom 404 page
- Custom 500 page
- Improved user experience

---

# 🛠️ Tech Stack

| Category | Technologies |
|----------|--------------|
| **Frontend** | HTML5, Bootstrap 5, Jinja2 Templates |
| **Backend** | Flask (Python) |
| **Database** | MySQL |
| **Styling** | CSS3, Font Awesome |
| **Scripting** | Vanilla JavaScript |

---

# 🚀 Installation

## Prerequisites

- Python 3.x
- MySQL Server
- Git

### Clone the Repository

```bash
git clone https://github.com/sharadhiadiga/SandDunes.git

cd SandDunes/Hotel-SandDunes-main
```

### Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

**Windows**

```bash
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure the Database

1. Create a MySQL database.
2. Update the database connection details inside **`app.py`** with your:
   - Host
   - Username
   - Password
   - Database name
3. Create the required tables (`rooms`, `bookings`, `customers`, `services`, `billing`, etc.) before running the application.

### Run the Application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000/
```

---

# 🚀 Future Work

- Online room reservation portal
- Secure payment gateway integration
- Customer feedback and ratings
- Email and SMS booking notifications
- Admin analytics dashboard
- Multi-branch hotel management
- Employee management system
- QR code-based check-in
- Inventory and housekeeping management
- AI-powered room pricing recommendations
