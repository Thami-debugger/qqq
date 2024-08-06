from flask import Flask, render_template, jsonify, redirect, url_for, request, session
import qrcode
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

queue = []
served_queue = []
missing_queue = []
current_number = 0
average_time_per_person = int(os.getenv('AVERAGE_TIME_PER_PERSON', 5))  # in minutes

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'password')

# Ensure the static directory exists
if not os.path.exists('static'):
    os.makedirs('static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join_queue')
def join_queue():
    global queue
    new_number = len(queue) + len(served_queue) + len(missing_queue) + 1
    queue.append(new_number)
    img = qrcode.make(f'{request.host_url}queue_status/{new_number}')
    img_path = f'static/queue_{new_number}.png'
    img.save(img_path)
    return render_template('queue.html', number=new_number, image_url=img_path)

@app.route('/queue_status/<int:number>')
def queue_status(number):
    return render_template('queue.html', number=number, image_url=f'/static/queue_{number}.png')

@app.route('/current_status')
def current_status():
    global current_number, queue, average_time_per_person
    if queue:
        current_number = queue[0]
    wait_time = (len(queue) * average_time_per_person) - average_time_per_person
    return jsonify({
        'current_number': current_number,
        'queue_length': len(queue),
        'average_wait_time': max(0, wait_time)
    })

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', queue=queue, current_number=current_number)

@app.route('/serve_next', methods=['POST'])
def serve_next():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    global queue, served_queue
    if queue:
        served_queue.append(queue.pop(0))
    return redirect(url_for('admin'))

@app.route('/mark_missing/<int:number>', methods=['POST'])
def mark_missing(number):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    global queue, missing_queue
    if number in queue:
        queue.remove(number)
        missing_queue.append(number)
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1'])
