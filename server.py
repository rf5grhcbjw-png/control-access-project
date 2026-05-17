from flask import Flask, render_template, request, redirect, url_for, flash
from database import get_conn, BLOCKS
from auth import check_resident, check_visitor, simulate_biometric_scan, log_attempt
from users import add_resident, remove_resident, add_visitor, deactivate_visitor

app = Flask(__name__)
app.secret_key = 'control_access_2026'


@app.route('/')
def index():
    return render_template('index.html', result=None, username=None)


@app.route('/checkin', methods=['POST'])
def checkin():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    method   = request.form.get('method', 'password')

    if not username:
        flash('Please enter a username.', 'warning')
        return redirect(url_for('index'))

    if method == 'password':
        granted = check_resident(username, password) or check_visitor(username)
        log_attempt(username, granted, 'password')
    else:
        granted = simulate_biometric_scan(username)
        log_attempt(username, granted, 'biometric')

    return render_template('index.html', result=granted, username=username)


@app.route('/residents')
def residents():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT block, username, reg_code, created_at FROM residents ORDER BY block, reg_code"
        ).fetchall()
    return render_template('residents.html', residents=rows, blocks=BLOCKS)


@app.route('/residents/add', methods=['POST'])
def residents_add():
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '').strip()
    b = request.form.get('block', '').strip()
    ok, msg = add_resident(u, p, b)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('residents'))


@app.route('/residents/remove', methods=['POST'])
def residents_remove():
    u = request.form.get('username', '').strip()
    ok, msg = remove_resident(u)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('residents'))


@app.route('/visitors')
def visitors():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, block, host, reason, temporary_access FROM visitors ORDER BY block, username"
        ).fetchall()
    return render_template('visitors.html', visitors=rows, blocks=BLOCKS)


@app.route('/visitors/add', methods=['POST'])
def visitors_add():
    u      = request.form.get('username', '').strip()
    b      = request.form.get('block', '').strip()
    host   = request.form.get('host', '').strip()
    reason = request.form.get('reason', '').strip()
    ok, msg = add_visitor(u, b, host, reason)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('visitors'))


@app.route('/visitors/deactivate', methods=['POST'])
def visitors_deactivate():
    u = request.form.get('username', '').strip()
    ok, msg = deactivate_visitor(u)
    flash(msg, 'success' if ok else 'danger')
    return redirect(url_for('visitors'))


@app.route('/log')
def log():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT timestamp, username, method, granted FROM access_log ORDER BY timestamp DESC"
        ).fetchall()
    return render_template('log.html', log=rows)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
