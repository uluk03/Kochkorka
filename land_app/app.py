from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps
import hashlib

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this"  # Измените это на случайную строку

# Конфигурация админа
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9"  # хеш от "admin123"


def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    """Декоратор для проверки авторизации"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def form():
    return render_template("form.html")


@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    land_name = request.form["land_name"]
    hectares = float(request.form["hectares"])
    price_per_hectare = 2500  # фиксированная цена
    total_price = hectares * price_per_hectare

    # Сохраняем в БД
    conn = sqlite3.connect("lands.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            land_name TEXT,
            hectares REAL,
            price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("INSERT INTO lands (name, land_name, hectares, price) VALUES (?, ?, ?, ?)",
                (name, land_name, hectares, total_price))
    conn.commit()
    conn.close()

    return render_template("success.html", name=name, price=total_price)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and hash_password(password) == ADMIN_PASSWORD_HASH:
            session['admin_logged_in'] = True
            flash('Успешный вход в админ-панель!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверные учетные данные!', 'error')

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Вы вышли из админ-панели', 'info')
    return redirect(url_for('form'))


@app.route("/admin")
@login_required
def admin_dashboard():
    conn = sqlite3.connect("lands.db")
    cur = conn.cursor()

    # Убеждаемся что таблица существует
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            land_name TEXT,
            hectares REAL,
            price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Получаем все записи
    cur.execute("SELECT * FROM lands ORDER BY id DESC")
    lands = cur.fetchall()

    print(f"Найдено записей: {len(lands)}")  # Для отладки

    # Получаем статистику
    cur.execute("SELECT COUNT(*) FROM lands")
    total_lands = cur.fetchone()[0]

    cur.execute("SELECT SUM(hectares) FROM lands")
    total_hectares_result = cur.fetchone()[0]
    total_hectares = total_hectares_result if total_hectares_result else 0

    cur.execute("SELECT SUM(price) FROM lands")
    total_revenue_result = cur.fetchone()[0]
    total_revenue = total_revenue_result if total_revenue_result else 0

    conn.close()

    stats = {
        'total_lands': total_lands,
        'total_hectares': round(float(total_hectares), 2),
        'total_revenue': float(total_revenue)
    }

    print(f"Статистика: {stats}")  # Для отладки

    return render_template("admin_dashboard.html", lands=lands, stats=stats)


@app.route("/admin/delete/<int:land_id>", methods=["POST"])
@login_required
def delete_land(land_id):
    conn = sqlite3.connect("lands.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM lands WHERE id = ?", (land_id,))
    conn.commit()
    conn.close()

    flash('Запись успешно удалена!', 'success')
    return redirect(url_for('admin_dashboard'))


# Тестовая функция для создания данных
@app.route("/admin/test-data")
@login_required
def create_test_data():
    conn = sqlite3.connect("lands.db")
    cur = conn.cursor()

    # Создаем таблицу если её нет
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            land_name TEXT,
            hectares REAL,
            price REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Добавляем тестовые данные
    test_data = [
        ("Иван Иванов", "Участок 1", 2.5, 6250),
        ("Мария Петрова", "Дачный участок", 1.0, 2500),
        ("Сергей Сидоров", "Поле у озера", 5.0, 12500)
    ]

    for name, land_name, hectares, price in test_data:
        cur.execute("INSERT INTO lands (name, land_name, hectares, price) VALUES (?, ?, ?, ?)",
                    (name, land_name, hectares, price))

    conn.commit()
    conn.close()

    flash('Тестовые данные добавлены!', 'success')
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    app.run(debug=True)