# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import SECRET_KEY, ADMIN_DEFAULT_PASS
from models import Colleague, Sandwich, Order, OrderItem

app = Flask(__name__)
app.secret_key = SECRET_KEY


def ensure_admin_exists():
    if not Colleague.get_admin_exists():
        # Create default admin if not exists
        Colleague.add_colleague("admin", True, ADMIN_DEFAULT_PASS)


ensure_admin_exists()


@app.route('/')
def home():
    # If not logged in, go to login page
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('order_page'))  # Logged in users go to orders page


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()

        admin_user = Colleague.get_admin_by_credentials(name, password)
        if admin_user:
            # Admin login
            session['user_id'] = admin_user['colleague_id']
            session['user_name'] = admin_user['name']
            session['is_admin'] = True
            flash("Logged in as admin.")
            return redirect(url_for('order_page'))

        # Check normal user
        colleagues = Colleague.get_all()
        user = None
        for c in colleagues:
            if c['name'] == name and c['is_admin'] is False:
                user = c
                break

        if user:
            session['user_id'] = user['colleague_id']
            session['user_name'] = user['name']
            session['is_admin'] = False
            flash("Logged in successfully.")
            return redirect(url_for('order_page'))
        else:
            flash("Invalid credentials.")
    return render_template('login.html')


@app.route('/order', methods=['GET', 'POST'])
def order_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    colleagues = Colleague.get_all()
    sandwiches = Sandwich.get_all()

    if request.method == 'POST':
        if session.get('is_admin', False):
            selected_name = request.form.get('colleague_name')
        else:
            selected_name = session['user_name']

        selected_sandwich = request.form.get('sandwich_name')
        quantity_str = request.form.get('quantity', '1')
        try:
            quantity = int(quantity_str)
        except ValueError:
            quantity = 1

        # Find colleague_id
        colleague_id = None
        for c in colleagues:
            if c['name'] == selected_name:
                colleague_id = c['colleague_id']
                break

        # Find sandwich_id
        sandwich_id = None
        for s in sandwiches:
            if s['sandwich_name'] == selected_sandwich:
                sandwich_id = s['sandwich_id']
                break

        if colleague_id and sandwich_id:
            order_id = Order.create(colleague_id)
            OrderItem.add_item(order_id, sandwich_id, quantity=quantity)
            flash("Sandwich added to cart.")
            return redirect(url_for('order_page'))
        else:
            flash("Invalid colleague or sandwich selection.")

    # Get orders grouped by sandwich
    orders_by_sandwich = OrderItem.get_all_orders_by_sandwich()

    return render_template('order.html',
                           colleagues=colleagues,
                           sandwiches=sandwiches,
                           orders_by_sandwich=orders_by_sandwich,
                           is_admin=session.get('is_admin', False))


@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    if 'user_id' not in session or not session.get('is_admin', False):
        return redirect(url_for('login'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_colleague':
            name = request.form.get('colleague_name', '').strip()
            password = request.form.get('colleague_password', '').strip()
            is_admin = (request.form.get('colleague_is_admin') == 'on')
            if name and password:
                Colleague.add_colleague(name, is_admin, password)
                flash(f"Colleague '{name}' added.")
            else:
                flash("Name and password required.")

        elif action == 'clear_cart':
            Order.clear_all()
            flash("Cart cleared.")

        elif action == 'add_sandwich':
            sandwich_name = request.form.get('sandwich_name', '').strip()
            price_str = request.form.get('sandwich_price', '').strip()
            if sandwich_name and price_str:
                try:
                    price = float(price_str)
                    Sandwich.add_sandwich(sandwich_name, price)
                    flash(f"Sandwich '{sandwich_name}' added.")
                except ValueError:
                    flash("Price must be a number.")
            else:
                flash("Sandwich name and price required.")

        return redirect(url_for('admin_page'))

    return render_template('admin.html', is_admin=True)


@app.route('/details')
def details_page():
    # Get all orders grouped by colleague with pricing
    details = OrderItem.get_orders_grouped_by_colleague()
    return render_template('details.html', details=details)


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
