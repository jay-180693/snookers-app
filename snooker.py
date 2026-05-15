from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_talisman import Talisman
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = 'Snooker@2026'
Talisman(app)

# In-memory storage (use database in production)
TOTAL_TABLES = 10
bookings = []
booking_log = []

class Table:
    def __init__(self, table_id):
        self.table_id = table_id
        self.is_booked = False
        self.booked_until = None

tables = {i: Table(i) for i in range(1, TOTAL_TABLES + 1)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tables')
def get_tables():
    available = sum(1 for t in tables.values() if not t.is_booked)
    return jsonify({
        'total': TOTAL_TABLES,
        'available': available,
        'tables': [{'id': t.table_id, 'available': not t.is_booked} for t in tables.values()]
    })

@app.route('/book', methods=['GET', 'POST'])
def book_table():
    if request.method == 'POST':
        data = request.form
        table_id = int(data.get('table_id'))
        duration = int(data.get('duration', 60))
        user_name = data.get('user_name')
        user_email = data.get('user_email')

        if table_id in tables and not tables[table_id].is_booked:
            booking = {
                'id': len(bookings) + 1,
                'table_id': table_id,
                'user_name': user_name,
                'user_email': user_email,
                'duration': duration,
                'booking_time': datetime.now().isoformat(),
                'amount': duration * 0.5
            }
            bookings.append(booking)
            return redirect(url_for('payment', booking_id=booking['id']))

        return jsonify({'success': False, 'error': 'Table not available'}), 400

    return render_template('book.html')

@app.route('/payment/<int:booking_id>')
def payment(booking_id):
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    if not booking:
        return redirect(url_for('index'))
    return render_template('payment.html', booking=booking)

@app.route('/confirm-booking/<int:booking_id>', methods=['POST'])
def confirm_booking(booking_id):
    booking = next((b for b in bookings if b['id'] == booking_id), None)
    if booking:
        table = tables[booking['table_id']]
        table.is_booked = True
        table.booked_until = datetime.now() + timedelta(minutes=booking['duration'])
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'table_number': booking['table_id'],
            'user_name': booking['user_name'],
            'user_email': booking['user_email'],
            'duration_minutes': booking['duration'],
            'amount_paid': booking['amount']
        }
        booking_log.append(log_entry)
        
        return jsonify({'success': True, 'message': 'Booking confirmed'})
    
    return jsonify({'success': False}), 400

@app.route('/logs')
def logs():
    return render_template('logs.html', logs=booking_log)

if __name__ == '__main__':
    app.run(debug=True)