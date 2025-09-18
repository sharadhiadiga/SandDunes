from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv
import os
from db.db_config import get_db_connection, close_db_connection
from datetime import datetime, timedelta
import mysql.connector

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Flask app
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Database connection
def get_db():
    """
    Creates a new database connection for each request
    Returns:
        connection: MySQL connection object
    """
    return get_db_connection()

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Main route
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if request.method == 'GET':
        conn = None
        cursor = None
        try:
            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")
            
            cursor = conn.cursor(dictionary=True)
            # Get all confirmed bookings with customer and room details
            cursor.execute("""
                SELECT b.booking_id, b.check_in_date, b.check_out_date,
                       c.first_name, c.last_name, c.email,
                       r.room_number, rt.type_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                JOIN rooms r ON b.room_id = r.room_id
                JOIN room_types rt ON r.type_id = rt.type_id
                WHERE b.status = 'confirmed'
                ORDER BY b.check_in_date DESC
            """)
            bookings = cursor.fetchall()
            
            # Format the booking data for display
            for booking in bookings:
                booking['display_text'] = f"Booking #{booking['booking_id']} - {booking['first_name']} {booking['last_name']} - Room {booking['room_number']} ({booking['type_name']}) - {booking['check_in_date'].strftime('%Y-%m-%d')}"
            
            return render_template('checkin.html', bookings=bookings)
        except mysql.connector.Error as err:
            flash(f"Error fetching bookings: {err}", "danger")
            return render_template('checkin.html', bookings=[])
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif request.method == 'POST':
        conn = None
        cursor = None
        try:
            # Get verified booking data
            booking_id = request.form['verified_booking_id']
            customer_id = request.form['verified_customer_id']
            check_in_date = datetime.strptime(request.form['check_in_date'], '%Y-%m-%dT%H:%M')
            check_out_date = datetime.strptime(request.form['check_out_date'], '%Y-%m-%dT%H:%M')
            special_requests = request.form.get('special_requests', '')

            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Verify booking is still valid
            cursor.execute("""
                SELECT b.*, r.room_id
                FROM bookings b
                JOIN rooms r ON b.room_id = r.room_id
                WHERE b.booking_id = %s AND b.customer_id = %s AND b.status = 'confirmed'
            """, (booking_id, customer_id))
            
            booking = cursor.fetchone()
            if not booking:
                flash("Invalid booking or booking already checked in", "danger")
                return redirect(url_for('checkin'))

            # Update booking status
            cursor.execute("""
                UPDATE bookings 
                SET status = 'checked_in',
                    check_in_date = %s,
                    check_out_date = %s,
                    special_requests = %s
                WHERE booking_id = %s
            """, (check_in_date, check_out_date, special_requests, booking_id))
            
            # Update room status
            cursor.execute("""
                UPDATE rooms SET status = 'occupied' WHERE room_id = %s
            """, (booking['room_id'],))

            conn.commit()
            flash("Check-in successful!", "success")
            return redirect(url_for('index'))

        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('checkin'))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('checkin'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'GET':
        conn = None
        cursor = None
        try:
            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")
            
            cursor = conn.cursor(dictionary=True)
            # Get all checked-in bookings with customer and room details
            cursor.execute("""
                SELECT b.booking_id, b.check_in_date, b.check_out_date,
                       c.first_name, c.last_name, c.email,
                       r.room_number, rt.type_name, rt.base_price
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                JOIN rooms r ON b.room_id = r.room_id
                JOIN room_types rt ON r.type_id = rt.type_id
                WHERE b.status = 'checked_in'
                ORDER BY b.check_in_date DESC
            """)
            bookings = cursor.fetchall()
            
            # Format the booking data for display
            for booking in bookings:
                # Calculate room charges
                days = (booking['check_out_date'] - booking['check_in_date']).days
                room_charges = float(booking['base_price']) * days
                booking['room_charges'] = room_charges
                booking['display_text'] = f"Booking #{booking['booking_id']} - {booking['first_name']} {booking['last_name']} - Room {booking['room_number']} ({booking['type_name']}) - Check-in: {booking['check_in_date'].strftime('%Y-%m-%d')}"
            
            return render_template('checkout.html', bookings=bookings)
        except mysql.connector.Error as err:
            flash(f"Error fetching bookings: {err}", "danger")
            return render_template('checkout.html', bookings=[])
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif request.method == 'POST':
        conn = None
        cursor = None
        try:
            # Get form data
            booking_id = request.form['booking_id']
            payment_method = request.form['payment_method']

            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Start transaction
            conn.start_transaction()
            
            # Get booking details with room charges
            cursor.execute("""
                SELECT b.*, r.room_id, rt.base_price,
                       (SELECT COALESCE(SUM(total_price), 0) FROM customer_services WHERE booking_id = b.booking_id) as service_charges
                FROM bookings b
                JOIN rooms r ON b.room_id = r.room_id
                JOIN room_types rt ON r.type_id = rt.type_id
                WHERE b.booking_id = %s AND b.status = 'checked_in'
            """, (booking_id,))
            
            booking = cursor.fetchone()
            if not booking:
                flash("Invalid booking or booking not checked in", "danger")
                return redirect(url_for('checkout'))

            # Calculate charges
            days = (booking['check_out_date'] - booking['check_in_date']).days
            room_charges = float(booking['base_price']) * days
            service_charges = float(booking['service_charges'])
            tax_rate = 10.00
            tax_amount = (room_charges + service_charges) * (tax_rate / 100)
            total_amount = room_charges + service_charges + tax_amount

            # Create bill first
            cursor.execute("""
                INSERT INTO billing (booking_id, room_charges, service_charges, 
                                   tax_rate, tax_amount, total_amount,
                                   payment_method, payment_status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
            """, (booking_id, room_charges, service_charges, tax_rate, tax_amount, 
                  total_amount, payment_method))
            
            bill_id = cursor.lastrowid

            # Update booking status
            cursor.execute("""
                UPDATE bookings 
                SET status = 'checked_out'
                WHERE booking_id = %s
            """, (booking_id,))
            
            # Update room status
            cursor.execute("""
                UPDATE rooms SET status = 'available' WHERE room_id = %s
            """, (booking['room_id'],))

            conn.commit()
            flash("Check-out successful!", "success")
            return redirect(url_for('billing', bill_id=bill_id))

        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('checkout'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@app.route('/availability')
def availability():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return render_template('error.html', message="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        # Only show rooms that are available (not reserved or occupied)
        cursor.execute("""
            SELECT r.*, rt.type_name, rt.description, rt.base_price, rt.capacity, rt.amenities
            FROM rooms r
            JOIN room_types rt ON r.type_id = rt.type_id
            WHERE r.status = 'available'
            ORDER BY r.room_number
        """)
        rooms = cursor.fetchall()
        return render_template('availability.html', rooms=rooms)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
        return render_template('availability.html', rooms=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if request.method == 'GET':
        room_id = request.args.get('room_id')
        if not room_id:
            flash("No room specified", "danger")
            return redirect(url_for('availability'))

        conn = get_db()
        if not conn:
            return render_template('error.html', message="Database connection failed")

        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT r.*, rt.*
                FROM rooms r
                JOIN room_types rt ON r.type_id = rt.type_id
                WHERE r.room_id = %s
            """, (room_id,))
            room = cursor.fetchone()

            if not room:
                flash("Room not found", "danger")
                return redirect(url_for('availability'))

            return render_template('booking.html', room=room)

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('availability'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif request.method == 'POST':
        conn = None
        cursor = None
        try:
            # Get form data
            room_id = request.form['room_id']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            id_type = request.form['id_type']
            id_number = request.form['id_number']
            num_guests = request.form['num_guests']
            check_in_date = datetime.strptime(request.form['check_in_date'], '%Y-%m-%dT%H:%M')
            check_out_date = datetime.strptime(request.form['check_out_date'], '%Y-%m-%dT%H:%M')
            special_requests = request.form.get('special_requests', '')

            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Start transaction
            conn.start_transaction()

            # Get the latest booking ID
            cursor.execute("SELECT MAX(booking_id) as max_id FROM bookings")
            result = cursor.fetchone()
            new_booking_id = (result['max_id'] or 0) + 1

            # Create new customer record for each booking
            cursor.execute("""
                INSERT INTO customers (first_name, last_name, email, phone, address, id_type, id_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, email, phone, address, id_type, id_number))
            customer_id = cursor.lastrowid

            # Create booking with integer ID
            cursor.execute("""
                INSERT INTO bookings (booking_id, customer_id, room_id, check_in_date, check_out_date, 
                                    num_guests, status, special_requests)
                VALUES (%s, %s, %s, %s, %s, %s, 'confirmed', %s)
            """, (new_booking_id, customer_id, room_id, check_in_date, check_out_date, num_guests, special_requests))
            
            # Update room status
            cursor.execute("""
                UPDATE rooms SET status = 'reserved' WHERE room_id = %s
            """, (room_id,))

            conn.commit()
            flash(f"Booking successful! Your booking ID is: {new_booking_id}", "success")
            return redirect(url_for('index'))

        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('booking', room_id=room_id))
        except Exception as e:
            if conn:
                conn.rollback()
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for('booking', room_id=room_id))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@app.route('/services', methods=['GET', 'POST'])
def services():
    if request.method == 'GET':
        conn = None
        cursor = None
        try:
            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Get all active bookings (checked-in)
            cursor.execute("""
                SELECT b.booking_id, b.check_in_date, b.check_out_date,
                       c.first_name, c.last_name, c.email,
                       r.room_number, rt.type_name
                FROM bookings b
                JOIN customers c ON b.customer_id = c.customer_id
                JOIN rooms r ON b.room_id = r.room_id
                JOIN room_types rt ON r.type_id = rt.type_id
                WHERE b.status = 'checked_in'
                ORDER BY b.check_in_date DESC
            """)
            bookings = cursor.fetchall()

            # Get all available services
            cursor.execute("SELECT * FROM services")
            services = cursor.fetchall()

            # Get selected booking's services if booking_id is provided
            booking_id = request.args.get('booking_id')
            ordered_services = []
            if booking_id:
                cursor.execute("""
                    SELECT s.*, cs.quantity, cs.total_price, cs.status
                    FROM customer_services cs
                    JOIN services s ON cs.service_id = s.service_id
                    WHERE cs.booking_id = %s
                """, (booking_id,))
                ordered_services = cursor.fetchall()

            return render_template('services.html', 
                                 bookings=bookings,
                                 services=services,
                                 ordered_services=ordered_services,
                                 selected_booking_id=booking_id)

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('index'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif request.method == 'POST':
        conn = None
        cursor = None
        try:
            booking_id = request.form['booking_id']
            service_id = request.form['service_id']
            quantity = int(request.form['quantity'])

            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Start transaction
            conn.start_transaction()
            
            # Get service price
            cursor.execute("SELECT price FROM services WHERE service_id = %s", (service_id,))
            service = cursor.fetchone()
            if not service:
                flash("Service not found", "danger")
                return redirect(url_for('services', booking_id=booking_id))

            # Calculate total price
            total_price = service['price'] * quantity

            # Add service order
            cursor.execute("""
                INSERT INTO customer_services (booking_id, service_id, quantity, 
                                            service_date, total_price, status)
                VALUES (%s, %s, %s, NOW(), %s, 'pending')
            """, (booking_id, service_id, quantity, total_price))

            conn.commit()
            flash("Service ordered successfully!", "success")
            return redirect(url_for('services', booking_id=booking_id))

        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('services', booking_id=booking_id))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@app.route('/billing', methods=['GET', 'POST'])
def billing():
    bill_id = request.args.get('bill_id')
    if not bill_id:
        flash("No bill specified", "danger")
        return redirect(url_for('index'))

    conn = get_db()
    if not conn:
        return render_template('error.html', message="Database connection failed")

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            # Start transaction
            conn.start_transaction()
            
            # Update payment status
            cursor.execute("""
                UPDATE billing 
                SET payment_status = 'paid',
                    payment_date = NOW()
                WHERE bill_id = %s
            """, (bill_id,))

            # Get booking ID from bill
            cursor.execute("SELECT booking_id FROM billing WHERE bill_id = %s", (bill_id,))
            bill_data = cursor.fetchone()
            
            if bill_data:
                # Update booking status
                cursor.execute("""
                    UPDATE bookings 
                    SET status = 'checked_out'
                    WHERE booking_id = %s
                """, (bill_data['booking_id'],))

                # Update room status
                cursor.execute("""
                    UPDATE rooms r
                    JOIN bookings b ON r.room_id = b.room_id
                    SET r.status = 'available'
                    WHERE b.booking_id = %s
                """, (bill_data['booking_id'],))

            conn.commit()
            return jsonify({'success': True, 'message': 'Payment successful! Check-out completed.'})
        
        # Get bill details
        cursor.execute("""
            SELECT b.*, bk.*, c.*, r.*, rt.*
            FROM billing b
            JOIN bookings bk ON b.booking_id = bk.booking_id
            JOIN customers c ON bk.customer_id = c.customer_id
            JOIN rooms r ON bk.room_id = r.room_id
            JOIN room_types rt ON r.type_id = rt.type_id
            WHERE b.bill_id = %s
        """, (bill_id,))
        bill = cursor.fetchone()

        if not bill:
            flash("Bill not found", "danger")
            return redirect(url_for('index'))

        # Get services
        cursor.execute("""
            SELECT s.*, cs.quantity, cs.total_price
            FROM customer_services cs
            JOIN services s ON cs.service_id = s.service_id
            WHERE cs.booking_id = %s
        """, (bill['booking_id'],))
        services = cursor.fetchall()

        return render_template('billing.html', bill=bill, services=services)

    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        if request.method == 'POST':
            return jsonify({'success': False, 'message': f'Database error: {err}'})
        flash(f"Database error: {err}", "danger")
        return redirect(url_for('index'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/verify_booking')
def verify_booking():
    booking_id = request.args.get('booking_id')
    id_type = request.args.get('id_type')
    id_number = request.args.get('id_number')

    if not all([booking_id, id_type, id_number]):
        return jsonify({'success': False, 'message': 'Missing required fields'})

    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'})

        cursor = conn.cursor(dictionary=True)
        
        # Verify booking and customer details
        cursor.execute("""
            SELECT b.*, c.*, r.room_number, rt.type_name
            FROM bookings b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN rooms r ON b.room_id = r.room_id
            JOIN room_types rt ON r.type_id = rt.type_id
            WHERE b.booking_id = %s 
            AND c.id_type = %s 
            AND c.id_number = %s
            AND b.status = 'confirmed'
        """, (booking_id, id_type, id_number))
        
        booking = cursor.fetchone()
        
        if not booking:
            return jsonify({'success': False, 'message': 'Invalid booking or ID verification failed'})

        return jsonify({
            'success': True,
            'booking_id': booking['booking_id'],
            'customer_id': booking['customer_id'],
            'first_name': booking['first_name'],
            'last_name': booking['last_name'],
            'email': booking['email'],
            'phone': booking['phone'],
            'address': booking['address'],
            'room_number': booking['room_number'],
            'room_type': booking['type_name'],
            'check_in_date': booking['check_in_date'].strftime('%Y-%m-%dT%H:%M'),
            'check_out_date': booking['check_out_date'].strftime('%Y-%m-%dT%H:%M')
        })

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Database error: {err}'})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/room_types')
def room_types():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return render_template('error.html', message="Database connection failed")
        
        cursor = conn.cursor(dictionary=True)
        # Get all room types with their rooms
        cursor.execute("""
            SELECT rt.*, 
                   COUNT(r.room_id) as total_rooms,
                   SUM(CASE WHEN r.status = 'available' THEN 1 ELSE 0 END) as available_rooms,
                   SUM(CASE WHEN r.status = 'occupied' THEN 1 ELSE 0 END) as occupied_rooms,
                   SUM(CASE WHEN r.status = 'reserved' THEN 1 ELSE 0 END) as reserved_rooms
            FROM room_types rt
            LEFT JOIN rooms r ON rt.type_id = r.type_id
            GROUP BY rt.type_id
            ORDER BY rt.type_name
        """)
        room_types = cursor.fetchall()

        # Get rooms for each type
        for room_type in room_types:
            cursor.execute("""
                SELECT r.*, 
                       CASE 
                           WHEN b.booking_id IS NOT NULL THEN b.status
                           ELSE r.status
                       END as current_status,
                       c.first_name, c.last_name,
                       b.check_in_date, b.check_out_date
                FROM rooms r
                LEFT JOIN bookings b ON r.room_id = b.room_id AND b.status IN ('checked_in', 'confirmed')
                LEFT JOIN customers c ON b.customer_id = c.customer_id
                WHERE r.type_id = %s
                ORDER BY r.room_number
            """, (room_type['type_id'],))
            room_type['rooms'] = cursor.fetchall()

        return render_template('room_types.html', room_types=room_types)
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", "danger")
        return render_template('room_types.html', room_types=[])
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/add_room_type', methods=['GET', 'POST'])
def add_room_type():
    if request.method == 'GET':
        return render_template('add_room_type.html')
    
    elif request.method == 'POST':
        conn = None
        cursor = None
        try:
            type_name = request.form['type_name']
            description = request.form['description']
            base_price = request.form['base_price']
            capacity = request.form['capacity']
            amenities = request.form['amenities']
            num_rooms = int(request.form['num_rooms'])

            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Start transaction
            conn.start_transaction()

            # Insert room type
            cursor.execute("""
                INSERT INTO room_types (type_name, description, base_price, capacity, amenities)
                VALUES (%s, %s, %s, %s, %s)
            """, (type_name, description, base_price, capacity, amenities))
            type_id = cursor.lastrowid

            # Insert rooms
            for i in range(1, num_rooms + 1):
                room_number = f"{type_name[:3].upper()}{i:03d}"
                cursor.execute("""
                    INSERT INTO rooms (room_number, type_id, status)
                    VALUES (%s, %s, 'available')
                """, (room_number, type_id))

            conn.commit()
            flash("Room type and rooms added successfully!", "success")
            return redirect(url_for('room_types'))

        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('add_room_type'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

@app.route('/edit_room_type/<int:type_id>', methods=['GET', 'POST'])
def edit_room_type(type_id):
    if request.method == 'GET':
        conn = None
        cursor = None
        try:
            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM room_types WHERE type_id = %s", (type_id,))
            room_type = cursor.fetchone()

            if not room_type:
                flash("Room type not found", "danger")
                return redirect(url_for('room_types'))

            return render_template('edit_room_type.html', room_type=room_type)

        except mysql.connector.Error as err:
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('room_types'))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    elif request.method == 'POST':
        conn = None
        cursor = None
        try:
            type_name = request.form['type_name']
            description = request.form['description']
            base_price = request.form['base_price']
            capacity = request.form['capacity']
            amenities = request.form['amenities']

            conn = get_db()
            if not conn:
                return render_template('error.html', message="Database connection failed")

            cursor = conn.cursor(dictionary=True)
            
            # Update room type
            cursor.execute("""
                UPDATE room_types 
                SET type_name = %s, description = %s, base_price = %s, 
                    capacity = %s, amenities = %s
                WHERE type_id = %s
            """, (type_name, description, base_price, capacity, amenities, type_id))

            conn.commit()
            flash("Room type updated successfully!", "success")
            return redirect(url_for('room_types'))

        except mysql.connector.Error as err:
            if conn:
                conn.rollback()
            flash(f"Database error: {err}", "danger")
            return redirect(url_for('edit_room_type', type_id=type_id))
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

def modify_customers_table():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return False

        cursor = conn.cursor()
        
        # Remove UNIQUE constraint from email
        cursor.execute("""
            ALTER TABLE customers 
            DROP INDEX email
        """)
        
        conn.commit()
        return True
    except mysql.connector.Error as err:
        if conn:
            conn.rollback()
        print(f"Error modifying table: {err}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Call this function when the app starts
modify_customers_table()

if __name__ == '__main__':
    app.run(debug=True)


    