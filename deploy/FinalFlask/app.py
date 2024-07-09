import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
from ultralytics import YOLO
import pymysql
import requests
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'trashToTreasure'
}

# Load pre-trained YOLO model and class names
model = YOLO("best.pt")
target_class = 'chatime'  # Replace with the actual class name in your model

ESP32_CAM_IP = "http://172.20.10.13"  # Ganti dengan alamat IP ESP32-CAM Anda
ESP32_SERVO_IP = "http://172.20.10.14"  # Ganti dengan alamat IP ESP32 untuk servo

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return redirect(url_for('capture_image'))
    return render_template('index.html')

@app.route('/capture', methods=['GET', 'POST'])
def capture_image():
    try:
        # Kirim permintaan capture ke ESP32-CAM
        response = requests.get(f"{ESP32_CAM_IP}/capture")
        if response.status_code == 200:
            image_data = base64.b64decode(response.content)
            filename = "captured_image.jpg"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(filepath, "wb") as f:
                f.write(image_data)
            # Proses gambar
            img = Image.open(filepath)
            results = model.predict(img, conf=0.94)
            results[0].show()
            detected_chatime = (len(results[0].boxes) > 0)
            if detected_chatime:
                # Kirim perintah ke ESP32 untuk menggerakkan servo
                servo_response = requests.get(f"{ESP32_SERVO_IP}/move_servo")
                if servo_response.status_code == 200:
                    return redirect(url_for('input_phone'))
                else:
                    return 'Failed to move servo', 500
            else:
                return 'Detection failed', 400
        else:
            return 'Failed to capture image', 500
    except Exception as e:
        return str(e), 500

@app.route('/input_phone', methods=['GET', 'POST'])
def input_phone():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        update_score(phone_number)
        return 'Score updated successfully'
    return render_template('input_phone.html')

def update_score(phone_number):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE members SET score = score + 1 WHERE no_telp = %s"
            rows_affected = cursor.execute(sql, (phone_number,))
            if rows_affected == 0:
                sql_insert = "INSERT INTO members (no_telp, score) VALUES (%s, 1)"
                cursor.execute(sql_insert, (phone_number,))

        connection.commit()
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)
