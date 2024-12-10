# models.py
from database import Database

class Colleague:
    @staticmethod
    def get_all():
        db = Database()
        db.query("SELECT colleague_id, name, is_admin, password FROM colleagues ORDER BY name;")
        rows = db.cursor.fetchall()
        db.close()
        return rows

    @staticmethod
    def get_admin_by_credentials(name, password):
        db = Database()
        db.query("SELECT colleague_id, name FROM colleagues WHERE name=%s AND password=%s AND is_admin=TRUE;", (name, password))
        row = db.cursor.fetchone()
        db.close()
        return row

    @staticmethod
    def add_colleague(name, is_admin=False, password=None):
        db = Database()
        db.query("INSERT INTO colleagues (name, is_admin, password) VALUES (%s, %s, %s);", (name, is_admin, password))
        db.close()

    @staticmethod
    def get_admin_exists():
        db = Database()
        db.query("SELECT 1 FROM colleagues WHERE is_admin=TRUE LIMIT 1;")
        result = db.cursor.fetchone()
        db.close()
        return result is not None


class Sandwich:
    @staticmethod
    def get_all():
        db = Database()
        db.query("SELECT sandwich_id, sandwich_name, price, is_available FROM sandwiches WHERE is_available=TRUE ORDER BY sandwich_name;")
        rows = db.cursor.fetchall()
        db.close()
        return rows

    @staticmethod
    def add_sandwich(name, price):
        db = Database()
        db.query("INSERT INTO sandwiches (sandwich_name, price, is_available) VALUES (%s, %s, TRUE);", (name, price))
        db.close()


class Order:
    @staticmethod
    def create(colleague_id):
        db = Database()
        db.query("INSERT INTO orders (colleague_id) VALUES (%s) RETURNING order_id;", (colleague_id,))
        order_id = db.cursor.fetchone()['order_id']
        db.close()
        return order_id

    @staticmethod
    def clear_all():
        db = Database()
        db.query("DELETE FROM order_items;")
        db.query("DELETE FROM orders;")
        db.close()


class OrderItem:
    @staticmethod
    def add_item(order_id, sandwich_id, quantity=1):
        db = Database()
        db.query("INSERT INTO order_items (order_id, sandwich_id, quantity) VALUES (%s, %s, %s);", (order_id, sandwich_id, quantity))
        db.close()

    @staticmethod
    def get_all_orders_by_sandwich():
        """
        Returns a list of dictionaries: sandwich_id, sandwich_name, total_quantity
        aggregated across all colleagues.
        """
        db = Database()
        sql = """
        SELECT s.sandwich_id, s.sandwich_name, SUM(oi.quantity) as total_quantity
        FROM order_items oi
        JOIN sandwiches s ON oi.sandwich_id = s.sandwich_id
        GROUP BY s.sandwich_id, s.sandwich_name
        ORDER BY s.sandwich_name;
        """
        db.query(sql)
        rows = db.cursor.fetchall()
        db.close()
        return rows

    @staticmethod
    def get_orders_grouped_by_colleague():
        """
        Returns a data structure grouping orders by colleague.
        Format:
        {
           colleague_name: {
               'total_price': X,
               'items': [
                  {'sandwich_name': ..., 'quantity': ..., 'line_price': ...},
                  ...
               ]
           },
           ...
        }
        """
        db = Database()
        sql = """
        SELECT c.name as colleague_name, s.sandwich_name, s.price, oi.quantity
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN colleagues c ON o.colleague_id = c.colleague_id
        JOIN sandwiches s ON oi.sandwich_id = s.sandwich_id
        ORDER BY c.name, s.sandwich_name;
        """
        db.query(sql)
        rows = db.cursor.fetchall()
        db.close()

        data = {}
        for row in rows:
            colleague_name = row['colleague_name']
            sandwich_name = row['sandwich_name']
            price = row['price']
            quantity = row['quantity']
            line_price = price * quantity

            if colleague_name not in data:
                data[colleague_name] = {
                    'total_price': 0,
                    'items': []
                }
            data[colleague_name]['items'].append({
                'sandwich_name': sandwich_name,
                'quantity': quantity,
                'line_price': line_price
            })
            data[colleague_name]['total_price'] += line_price

        return data
