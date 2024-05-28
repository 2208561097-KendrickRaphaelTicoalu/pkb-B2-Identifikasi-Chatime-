import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
from ultralytics import YOLO
import torchvision.transforms as T
import pymysql

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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            # Process image
            img = Image.open(filepath)
            results = model.predict(img,conf=0.94) 
            results[0].show()
            detected_chatime = (len(results[0].boxes) > 0) 
            if detected_chatime:
                return redirect(url_for('input_phone'))
            else:
                return 'Detection failed', 400
    return render_template('index.html')

@app.route('/input_phone', methods=['GET', 'POST'])
def input_phone():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        update_score(phone_number)
        return 'Score updated successfully'
    return '''
        <form method="post">
            Phone Number: <input type="text" name="phone_number"><br>
            <input type="submit" value="Submit">
        </form>
    '''

def update_score(phone_number):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = "UPDATE members SET score = score + 1 WHERE no_telp = %s"
            cursor.execute(sql, (phone_number,))
        connection.commit()
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)
