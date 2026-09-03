from flask import Flask, request, jsonify, send_from_directory, url_for, redirect, render_template, session, Response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
from passlib.hash import sha256_crypt
from datetime import datetime, timedelta
import os
import re
import uuid
import random
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
# Import for Google Sign-in
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
# Import the database models from models.py
from models import db, User, Equipment, Booking, Operator, OperatorBooking
from sqlalchemy import or_
# Import for PDF generation and QR codes
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import qrcode
from io import BytesIO
import base64

import math
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import abort


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance (km) between two lat/lon points.
    """
    R = 6371  # Earth radius in km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Create the Flask application instance
app = Flask(__name__, static_folder='../frontend/static', template_folder='../frontend')
CORS(app)
app.secret_key = "super_secret_key" 
# --- Configuration ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "super-secret-key-that-should-be-kept-safe"
app.config["SECRET_KEY"] = "a-secret-key-for-token-generation"
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
# Mail server configuration (you need to fill this out)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'AgroRentteam22@gmail.com'
app.config['MAIL_PASSWORD'] = 'cprc jtem pvvx ggbk'
mail = Mail(app)

# You must provide your own Google Client ID here
GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID_HERE"

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
jwt = JWTManager(app)
db.init_app(app)
CORS(app)

with app.app_context():
    # Create tables if they don't exist (preserves existing data)
    try:
        db.create_all()
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Try to create missing tables
        try:
            db.create_all()
        except Exception as e2:
            print(f"Failed to create database tables: {e2}")

# --- Password Validation Function ---
def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character."
    return None

# --- Email Validation Function ---
def validate_email(email):
    if not email:
        return "Email is required."
    
    email_regex = re.compile(r"^[\w.-]+@([\w-]+\.)+[\w-]{2,4}$")
    if not email_regex.match(email):
        return "Please enter a valid email address."
    
    domain = email.split('@')[-1]
    allowed_domains = ['gmail.com', 'yahoo.com', 'outlook.com']
    if domain not in allowed_domains:
        return f"Email domain '{domain}' is not supported."
        
    return None

def send_verification_email(to_email, reset_link):
    sender_email = app.config['MAIL_USERNAME']
    app_password = app.config['MAIL_PASSWORD']

    subject = "Password Reset Request"
    body = f"""
    Hello,

    We received a request to reset your password.
    Click here to reset it: {reset_link}

    If this wasn't you, please ignore this email.

    Regards,
    Team AgroRent
    """

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.attach(MIMEText(body, "plain"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        print("✅ Email sent successfully!")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False


# --- API Endpoints ---
@app.route("/")
def serve_home():
    return render_template("index.html")

@app.route("/index.html")
def serve_index():
    return render_template("index.html")

@app.route("/dash.html")
def serve_dashboard():
    return render_template("dash.html")

@app.route("/login.html")
def serve_login():
    return render_template("login.html")

@app.route("/booking.html")
def serve_booking():
    return render_template("booking.html")

@app.route("/addequipment.html")
def serve_addequipment():
    return render_template("addequipment.html")

@app.route("/account.html")
def serve_account():
    return render_template("account.html")

@app.route("/bookinghistory.html")
def serve_bookinghistory():
    return render_template("bookinghistory.html")

@app.route("/conformation.html")
def serve_conformation():
    return render_template("conformation.html")

@app.route("/hireoperators.html")
def serve_hireoperators():
    return render_template("hireoperators.html")

@app.route("/addsolutions.html")
def serve_addsolutions():
    return render_template("addsolutions.html")

@app.route("/addvideos.html")
def serve_addvideos():
    return render_template("addvideos.html")

@app.route("/forgotpassword.html")
def serve_forgotpassword():
    return render_template("forgotpassword.html")

@app.route("/reset_password.html")
def serve_reset_password():
    return render_template("reset_password.html")

@app.route("/loginwithotp.html")
def serve_loginwithotp():
    return render_template("loginwithotp.html")

@app.route("/operatorsbooking.html")
def serve_operatorsbooking():
    return render_template("operatorsbooking.html")

@app.route("/operatorsbookinghistory.html")
def serve_operatorsbookinghistory():
    return render_template("operatorsbookinghistory.html")

@app.route("/payment-history.html")
def serve_payment_history():
    return render_template("payment-history.html")


@app.route("/uploads/<filename>", methods=["GET"])
def get_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/images/<filename>", methods=["GET"])
def get_static_image(filename):
    images_path = os.path.join(basedir, '../images')
    return send_from_directory(images_path, filename)

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    full_name = data.get("full_name")
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "farmer")

    if not full_name or not username or not password or not email:
        return jsonify({"msg": "All required fields are missing"}), 400

    password_error = validate_password(password)
    if password_error:
        return jsonify({"msg": password_error}), 400

    email_error = validate_email(email)
    if email_error:
        return jsonify({"msg": email_error}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists"}), 409

    hashed_password = sha256_crypt.hash(password)
    new_user = User(username=username, password=hashed_password, role=role, full_name=full_name, email=email)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"msg": "User created successfully"}), 201

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username_or_email = data.get("username")
        password = data.get("password")

        # Debug logging
        print(f"Login attempt - Username/Email: '{username_or_email}', Password provided: {bool(password)}")
        print(f"Request data: {data}")

        if not username_or_email or not password:
            print("Missing username or password")
            return jsonify({"msg": "Username/phone/email and password are required"}), 400

        user = User.query.filter(
            or_(
                User.username == username_or_email,
                User.email == username_or_email
            )
        ).first()

        print(f"User found in database: {user is not None}")
        if user:
            print(f"Found user: {user.username}, {user.email}")
            password_valid = sha256_crypt.verify(password, user.password)
            print(f"Password valid: {password_valid}")

        if user and sha256_crypt.verify(password, user.password):
            access_token = create_access_token(identity=str(user.id))
            print("Login successful")
            return jsonify(
                access_token=access_token, 
                role=user.role, 
                full_name=user.full_name,
                email=user.email,
                user_id=user.id
            ), 200
        else:
            print("Login failed - invalid credentials")
            return jsonify({"msg": "Invalid username or password"}), 401
    return render_template('login.html')
    
@app.route("/google/callback", methods=["POST"])
def google_callback():
    data = request.get_json()
    token = data.get("token")
    if not token:
        return jsonify({"msg": "Token not provided"}), 400

    try:
        # Use a new request object for the verification call
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), "337803351297-uuqu9h0uas0qq4okmhq4g2649jn3v9s6.apps.googleusercontent.com")
        email = idinfo.get("email")
        if not email:
            return jsonify({"msg": "Email not found in token"}), 400
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # For this simple app, we can auto-register the user
            user = User(
                username=email, # Use email as username for Google logins
                email=email,
                full_name=idinfo.get("name"),
                password=sha256_crypt.hash(str(uuid.uuid4())), # Generate a random password
                role="farmer"
            )
            db.session.add(user)
            db.session.commit()
            
        access_token = create_access_token(identity=str(user.id))
        return jsonify(
            access_token=access_token,
            role=user.role,
            full_name=user.full_name,
            email=user.email
        ), 200
        
    except ValueError:
        return jsonify({"msg": "Invalid token"}), 400
    


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    print("📩 Forgot password request received for:", email) # DEBUG

    if not email:
        return jsonify({"msg": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "Email not found"}), 404

    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = s.dumps(user.email, salt='password-reset-salt')
    reset_link = url_for('verify_reset', token=token, _external=True)

    msg = Message(
        subject='Password Reset Request for AgroRent',
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    msg.body = (
        f'Hello {user.full_name},\n\n'
        f'Click the following link to reset your password: {reset_link}\n\n'
        f'The link will expire in 10 minutes.\n\n'
        f'If you did not request a password reset, please ignore this email.'
    )
    
    try:
        mail.send(msg)
        print("📨 Sending mail to:", email) # DEBUG
        return jsonify({"msg": "Password reset link sent to your email"}), 200
    except Exception as e:
        print("❌ Mail send failed:", e)
        return jsonify({"msg": "Failed to send email"}), 500


@app.route("/verify-reset/<token>", methods=["GET"])
def verify_reset(token):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=600)
    except (SignatureExpired, BadSignature):
        return jsonify({"msg": "Link expired or invalid, please request a new one."}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
        
    user.reset_token = token
    db.session.commit()
    
    return redirect(url_for('reset_password_page', token=token))
    
@app.route("/reset-password-page")
def reset_password_page():
    return render_template("reset_password.html")

@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        return jsonify({"msg": "Missing token or new password"}), 400

    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=600)
    except (SignatureExpired, BadSignature):
        return jsonify({"msg": "Link expired or invalid, please request a new one."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.reset_token != token:
        return jsonify({"msg": "Invalid or reused token"}), 400

    password_error = validate_password(new_password)
    if password_error:
        return jsonify({"msg": password_error}), 400

    user.password = sha256_crypt.hash(new_password)
    user.reset_token = None
    db.session.commit()

    return jsonify({"msg": "Password reset successful"}), 200

@app.route('/save-location', methods=['POST'])
def save_location():
    data = request.json
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not latitude or not longitude:
        return jsonify({"msg": "Missing latitude or longitude"}), 400

    # Store location in session
    session['latitude'] = float(latitude)
    session['longitude'] = float(longitude)

    return jsonify({"msg": "Location updated successfully"}), 200


@app.route("/addequipment", methods=["POST"])
@jwt_required()
def add_equipment():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.role != 'owner':
        return jsonify({"msg": "Permission denied"}), 403

    # form fields
    name = request.form.get("name")
    description = request.form.get("description")
    price = request.form.get("price")
    contact_number = request.form.get("contact_number")
    image_file = request.files.get("image")
    location = request.form.get("location")      # human readable address
    latitude = request.form.get("latitude")     # may be '' or None
    longitude = request.form.get("longitude")

    # basic validation (same as before + location optional)
    if not name or not description or not price or not contact_number or not image_file:
        return jsonify({"msg": "All required fields (name, description, price, contact_number, image) are required"}), 400

    try:
        price_val = float(price)
        if price_val <= 0:
            return jsonify({"msg": "Please enter a valid positive price."}), 400
    except ValueError:
        return jsonify({"msg": "Invalid price value."}), 400

    # save image
    image_filename = str(uuid.uuid4()) + os.path.splitext(image_file.filename)[1]
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    image_file.save(image_path)

    # convert coordinates if provided
    lat_val = None
    lon_val = None
    try:
        if latitude:
            lat_val = float(latitude)
        if longitude:
            lon_val = float(longitude)
    except Exception:
        # ignore conversion errors, store None
        lat_val = None
        lon_val = None

    new_equipment = Equipment(
        name=name,
        description=description,
        price=price_val,
        owner_id=current_user_id,
        contact_number=contact_number,
        image_filename=image_filename,
        location=location,
        latitude=lat_val,
        longitude=lon_val
    )

    db.session.add(new_equipment)
    db.session.commit()

    return jsonify({"msg": "Equipment added successfully"}), 201


@app.route("/my-equipment", methods=["GET"])
@jwt_required()
def my_equipment():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user or user.role != 'owner':
        return jsonify({"msg": "Permission denied. Only owners can view their equipment."}), 403

    owner_equipment = Equipment.query.filter_by(owner_id=current_user_id).all()

    equipment_list = [{
        "id": equip.id,
        "name": equip.name,
        "description": equip.description,
        "price": equip.price,
        "contact_number": equip.contact_number,
        "image_url": f"/uploads/{equip.image_filename}" if equip.image_filename else "https://placehold.co/600x400/cccccc/333333?text=No+Image",
        "location": equip.location,
        "latitude": equip.latitude,
        "longitude": equip.longitude
    } for equip in owner_equipment]

    return jsonify(equipment_list), 200

@app.route("/equipment", methods=["GET"])
def get_equipment():
    # Get location from session if available, fallback to query args
    lat = session.get('latitude', request.args.get("lat", type=float))
    lon = session.get('longitude', request.args.get("lon", type=float))

    equipment = Equipment.query.all()
    equipment_list = []

    for equip in equipment:
        dist = None
        if lat and lon and equip.latitude and equip.longitude:
            dist = haversine(lat, lon, equip.latitude, equip.longitude)

        equipment_list.append({
            "id": equip.id,
            "name": equip.name,
            "description": equip.description,
            "price": equip.price,
            "contact_number": equip.contact_number,
            "image_url": f"/uploads/{equip.image_filename}" if equip.image_filename else "https://placehold.co/600x400/cccccc/333333?text=No+Image",
            "location": equip.location,
            "latitude": equip.latitude,
            "longitude": equip.longitude,
            "distance": dist
        })

    # Sort by distance if a location is available
    if lat is not None and lon is not None:
        equipment_list.sort(key=lambda x: x["distance"] if x["distance"] is not None else float("inf"))

    return jsonify(equipment_list), 200

def _current_user_id():
    """Return JWT identity coerced to int when possible."""
    ident = get_jwt_identity()
    try:
        return int(ident)
    except Exception:
        return ident


@app.route("/delete-equipment/<int:equipment_id>", methods=["DELETE"])
@jwt_required()
def delete_equipment(equipment_id):
    current_user_id = _current_user_id()
    user = User.query.get(current_user_id)

    if not user or user.role != "owner":
        return jsonify({"error": "Permission denied"}), 403

    equipment = Equipment.query.get(equipment_id)

    if not equipment:
        return jsonify({"error": "Equipment not found"}), 404

    if equipment.owner_id != current_user_id:
        return jsonify({"error": "You can only delete your own equipment"}), 403

    # Delete associated image file if exists
    if equipment.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], equipment.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    db.session.delete(equipment)
    db.session.commit()

    return jsonify({"msg": "Equipment deleted successfully"}), 200


@app.route("/book", methods=["POST"])
@jwt_required()
def book_equipment():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != 'farmer':
        return jsonify({"msg": "Permission denied. Only farmers can book equipment."}), 403

    data = request.get_json()
    equipment_id = data.get("equipment_id")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date")

    if not equipment_id or not start_date_str or not end_date_str:
        return jsonify({"msg": "Missing booking details"}), 400

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD"}), 400

    existing_bookings = Booking.query.filter(
        Booking.equipment_id == equipment_id,
        Booking.start_date <= end_date,
        Booking.end_date >= start_date
    ).first()

    if existing_bookings:
        return jsonify({"msg": "Equipment is not available during this period"}), 409
    
    new_booking = Booking(
        user_id=current_user_id,
        equipment_id=equipment_id,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"msg": "Booking successful"}), 201


@app.route("/booking-history", methods=["GET"])
@jwt_required()
def booking_history():
    current_user_id = get_jwt_identity()

    history = db.session.query(Booking, Equipment).join(
        Equipment, Booking.equipment_id == Equipment.id
    ).filter(Booking.user_id == current_user_id).all()

    booking_list = [{
        "booking_id": booking.id,
        "equipment_name": equipment.name,
        "start_date": booking.start_date.strftime('%Y-%m-%d'),
        "end_date": booking.end_date.strftime('%Y-%m-%d'),
        "total_cost": (booking.end_date - booking.start_date).days * equipment.price
    } for booking, equipment in history]

    return jsonify(booking_list), 200

@app.route("/api/operator-bookings", methods=["GET"])
def operator_booking_history():
    """Get operator booking history for display and PDF generation"""
    # For testing, we'll use user_id = 1. In production, use JWT authentication
    user_id = request.args.get('user_id', 1, type=int)
    
    history = db.session.query(OperatorBooking, Operator).join(
        Operator, OperatorBooking.operator_id == Operator.id
    ).filter(OperatorBooking.user_id == user_id).order_by(OperatorBooking.created_at.desc()).all()

    booking_list = [{
        "booking_id": booking.id,
        "operator_name": operator.name,
        "operator_contact": operator.contact_number,
        "operator_location": operator.location,
        "start_date": booking.start_date.strftime('%Y-%m-%d'),
        "working_days": booking.working_days,
        "work_type": booking.work_type,
        "field_size": booking.field_size,
        "total_amount": booking.total_amount,
        "payment_method": booking.payment_method,
        "payment_id": booking.payment_id,
        "status": booking.status,
        "created_at": booking.created_at.strftime('%Y-%m-%d %H:%M'),
        "rate_per_day": operator.price_per_day,
        "specialization": operator.specialization,
        "experience": operator.experience_years
    } for booking, operator in history]

    return jsonify(booking_list), 200

@app.route("/api/create-equipment-booking", methods=["POST"])
def create_equipment_booking():
    """Create equipment booking without JWT for testing"""
    data = request.get_json()
    print(f"Booking creation data received: {data}")
    user_id = data.get("user_id", 1)  # Default to user_id 1 for testing
    print(f"Using user_id: {user_id}")
    equipment_name = data.get("equipment_name")
    start_date_str = data.get("start_date")
    end_date_str = data.get("end_date", start_date_str)  # Default to same day
    location = data.get("location", "Karnataka")
    payment_id = data.get("payment_id", "")
    amount = data.get("amount", 0)

    if not equipment_name or not start_date_str:
        return jsonify({"msg": "Missing booking details"}), 400

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = start_date
    except ValueError:
        return jsonify({"msg": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Find or create equipment entry
    equipment = Equipment.query.filter_by(name=equipment_name).first()
    if not equipment:
        # Create a dummy equipment entry for testing
        equipment = Equipment(
            name=equipment_name,
            description=f"Equipment: {equipment_name}",
            price=float(amount) if amount else 1500.0,
            owner_id=1,  # Default owner
            contact_number="+91 9876543210",
            location=location
        )
        db.session.add(equipment)
        db.session.flush()  # Get the ID

    new_booking = Booking(
        user_id=user_id,
        equipment_id=equipment.id,
        start_date=start_date,
        end_date=end_date
    )
    db.session.add(new_booking)
    db.session.commit()

    return jsonify({"msg": "Equipment booking created successfully", "booking_id": new_booking.id}), 201

@app.route("/api/create-test-equipment-booking", methods=["POST"])
def create_test_equipment_booking():
    """Create test equipment booking for debugging"""
    try:
        # Create or get test equipment
        equipment = Equipment.query.filter_by(name="John Deere 5050D Tractor").first()
        if not equipment:
            equipment = Equipment(
                name="John Deere 5050D Tractor",
                description="Powerful tractor for farming operations",
                price=1530.0,
                owner_id=1,
                contact_number="+91 9876543210",
                location="Mandya, Karnataka"
            )
            db.session.add(equipment)
            db.session.flush()

        # Create test booking
        test_booking = Booking(
            user_id=1,
            equipment_id=equipment.id,
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        db.session.add(test_booking)
        db.session.commit()

        return jsonify({"msg": "Test equipment booking created", "booking_id": test_booking.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/setup-test-equipment", methods=["GET", "POST"])
def setup_test_equipment():
    """Create diverse test equipment with different prices"""
    try:
        # Check if test equipment already exists to avoid duplicates
        existing_count = Equipment.query.count()
        if existing_count >= 5:
            return jsonify({"msg": f"Equipment already exists ({existing_count} items)", "count": existing_count}), 200

        # Create diverse test equipment with different prices
        test_equipment = [
            {
                "name": "John Deere 5050D Tractor",
                "description": "Powerful 50HP tractor perfect for plowing and heavy farming",
                "price": 1530.0,
                "location": "Mandya, Karnataka",
                "latitude": 12.5266,
                "longitude": 76.8966
            },
            {
                "name": "Mahindra 575 DI Tractor", 
                "description": "Reliable 42HP tractor for medium farming operations",
                "price": 1200.0,
                "location": "Mysore, Karnataka",
                "latitude": 12.2958,
                "longitude": 76.6394
            },
            {
                "name": "Rotavator RT-150",
                "description": "6-foot rotavator for soil preparation and tilling",
                "price": 800.0,
                "location": "Bangalore, Karnataka", 
                "latitude": 12.9716,
                "longitude": 77.5946
            },
            {
                "name": "Power Sprayer PS-400",
                "description": "High-capacity sprayer for pesticide and fertilizer application",
                "price": 600.0,
                "location": "Hassan, Karnataka",
                "latitude": 13.0033,
                "longitude": 76.1004
            },
            {
                "name": "Combine Harvester CH-500",
                "description": "Advanced combine harvester for wheat and rice harvesting",
                "price": 2500.0,
                "location": "Shimoga, Karnataka",
                "latitude": 13.9299,
                "longitude": 75.5681
            },
            {
                "name": "Seed Drill SD-200",
                "description": "Precision seed drill for accurate seed placement",
                "price": 900.0,
                "location": "Tumkur, Karnataka",
                "latitude": 13.3379,
                "longitude": 77.1017
            }
        ]

        equipment_created = []
        for equip_data in test_equipment:
            # Check if equipment already exists
            existing = Equipment.query.filter_by(name=equip_data["name"]).first()
            if not existing:
                new_equipment = Equipment(
                    name=equip_data["name"],
                    description=equip_data["description"],
                    price=equip_data["price"],
                    owner_id=1,  # Default owner
                    contact_number="+91 9876543210",
                    location=equip_data["location"],
                    latitude=equip_data["latitude"],
                    longitude=equip_data["longitude"]
                )
                db.session.add(new_equipment)
                equipment_created.append({
                    "name": equip_data["name"],
                    "price": equip_data["price"]
                })

        db.session.commit()
        
        return jsonify({
            "msg": "Test equipment created successfully",
            "created": equipment_created,
            "count": len(equipment_created)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/setup-test-bookings", methods=["GET", "POST"])
def setup_test_bookings():
    """Create test bookings for demonstration"""
    try:
        # Check if test bookings already exist
        existing_bookings = Booking.query.count()
        if existing_bookings >= 3:
            return jsonify({"msg": f"Test bookings already exist ({existing_bookings} bookings)", "count": existing_bookings}), 200

        # Get available equipment
        equipment_list = Equipment.query.limit(5).all()
        if not equipment_list:
            # Create test equipment first
            setup_response = setup_test_equipment()
            equipment_list = Equipment.query.limit(5).all()

        if not equipment_list:
            return jsonify({"error": "No equipment available to create bookings"}), 400

        # Create test user if not exists
        test_user = User.query.filter_by(id=1).first()
        if not test_user:
            test_user = User(
                username="testuser",
                password="hashed_password",
                role="user",
                full_name="Test User",
                email="test@example.com"
            )
            db.session.add(test_user)
            db.session.commit()

        # Create test bookings
        test_bookings = []
        for i, equipment in enumerate(equipment_list[:3]):
            start_date = datetime.now() - timedelta(days=30-i*10)
            end_date = start_date + timedelta(days=3+i)
            duration_days = (end_date - start_date).days
            total_amount = duration_days * equipment.price

            booking = Booking(
                user_id=1,
                equipment_id=equipment.id,
                start_date=start_date,
                end_date=end_date,
                payment_method="UPI" if i % 2 == 0 else "Card",
                payment_id=f"PAY{1000+i}",
                status="confirmed",
                total_amount=total_amount,
                created_at=start_date
            )
            db.session.add(booking)
            test_bookings.append({
                "equipment": equipment.name,
                "start_date": start_date.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "amount": total_amount
            })

        db.session.commit()
        
        return jsonify({
            "msg": "Test bookings created successfully",
            "bookings": test_bookings,
            "count": len(test_bookings)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/debug/database", methods=["GET"])
def debug_database():
    """Debug endpoint to check database status"""
    try:
        equipment_count = Equipment.query.count()
        booking_count = Booking.query.count()
        operator_count = Operator.query.count()
        operator_booking_count = OperatorBooking.query.count()
        user_count = User.query.count()
        
        return jsonify({
            "status": "connected",
            "counts": {
                "equipment": equipment_count,
                "bookings": booking_count,
                "operators": operator_count,
                "operator_bookings": operator_booking_count,
                "users": user_count
            },
            "sample_data": {
                "equipment": [{"id": e.id, "name": e.name} for e in Equipment.query.limit(3).all()],
                "bookings": [{"id": b.id, "equipment_id": b.equipment_id, "start_date": b.start_date.strftime('%Y-%m-%d')} for b in Booking.query.limit(3).all()]
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/api/admin/reset-database", methods=["POST"])
def reset_database():
    """Admin endpoint to reset database (DANGER: removes all data)"""
    try:
        db.drop_all()
        db.create_all()
        
        # Create default admin user
        admin_user = User(
            username="admin",
            password=sha256_crypt.hash("admin123"),
            role="admin",
            full_name="Administrator",
            email="admin@AgroRent.com"
        )
        db.session.add(admin_user)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Database reset successfully",
            "default_admin": {
                "username": "admin",
                "password": "admin123",
                "role": "admin"
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/api/create-test-user", methods=["POST"])
def create_test_user():
    """Create a test user for login testing"""
    try:
        # Check if test user already exists
        existing_user = User.query.filter_by(username="testuser").first()
        if existing_user:
            return jsonify({
                "status": "exists",
                "message": "Test user already exists",
                "credentials": {
                    "username": "testuser",
                    "password": "Test123!",
                    "email": "test@AgroRent.com"
                }
            }), 200

        # Create test user
        test_user = User(
            username="testuser",
            password=sha256_crypt.hash("Test123!"),
            role="user",
            full_name="Test User",
            email="test@AgroRent.com",
            address="Test Address, Karnataka",
            language="English"
        )
        db.session.add(test_user)
        db.session.commit()
        
        return jsonify({
            "status": "created",
            "message": "Test user created successfully",
            "credentials": {
                "username": "testuser",
                "password": "Test123!",
                "email": "test@AgroRent.com"
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/api/bookings", methods=["GET"])
def equipment_booking_history():
    """Get equipment booking history for display and PDF generation"""
    # For testing, we'll use user_id = 1. In production, use JWT authentication
    user_id = request.args.get('user_id', 1, type=int)
    
    history = db.session.query(Booking, Equipment).join(
        Equipment, Booking.equipment_id == Equipment.id
    ).filter(Booking.user_id == user_id).order_by(Booking.start_date.desc()).all()

    booking_list = []
    for booking, equipment in history:
        duration_days = (booking.end_date - booking.start_date).days
        if duration_days == 0:  # Same day booking
            duration_days = 1
        
        booking_list.append({
            "booking_id": booking.id,
            "equipment_name": equipment.name,
            "equipment_description": equipment.description,
            "equipment_location": equipment.location,
            "equipment_contact": equipment.contact_number,
            "equipment_image_url": f"/uploads/{equipment.image_filename}" if equipment.image_filename else "https://placehold.co/600x400/cccccc/333333?text=No+Image",
            "start_date": booking.start_date.strftime('%Y-%m-%d'),
            "end_date": booking.end_date.strftime('%Y-%m-%d'),
            "duration_days": duration_days,
            "price_per_day": equipment.price,
            "total_cost": booking.total_amount if booking.total_amount else (duration_days * equipment.price),
            "payment_method": booking.payment_method or "POD",
            "payment_id": booking.payment_id,
            "status": booking.status or "confirmed",
            "created_at": booking.created_at.strftime('%Y-%m-%d %H:%M') if booking.created_at else booking.start_date.strftime('%Y-%m-%d %H:%M')
        })

    return jsonify(booking_list), 200

@app.route("/api/payments", methods=["GET"])
def get_payment_history():
    """Get payment history for both equipment and operator bookings"""
    user_id = request.args.get('user_id', 1, type=int)
    
    payment_list = []
    
    # Get equipment booking payments
    equipment_payments = db.session.query(Booking, Equipment).join(
        Equipment, Booking.equipment_id == Equipment.id
    ).filter(Booking.user_id == user_id).order_by(Booking.created_at.desc()).all()
    
    for booking, equipment in equipment_payments:
        duration_days = (booking.end_date - booking.start_date).days
        if duration_days == 0:
            duration_days = 1
        
        # Calculate amount if not stored
        amount = booking.total_amount if booking.total_amount else (duration_days * equipment.price)
        
        payment_list.append({
            "id": f"EQP{booking.id}",
            "equipment": equipment.name,
            "date": booking.created_at.strftime('%Y-%m-%d') if booking.created_at else booking.start_date.strftime('%Y-%m-%d'),
            "amount": f"₹{amount:.0f}",
            "method": booking.payment_method or "POD",
            "status": "successful" if booking.status == "confirmed" else "pending",
            "type": "Equipment",
            "transaction_id": booking.payment_id or f"TXN{booking.id}"
        })
    
    # Get operator booking payments
    operator_payments = db.session.query(OperatorBooking, Operator).join(
        Operator, OperatorBooking.operator_id == Operator.id
    ).filter(OperatorBooking.user_id == user_id).order_by(OperatorBooking.created_at.desc()).all()
    
    for booking, operator in operator_payments:
        payment_list.append({
            "id": f"OPR{booking.id}",
            "equipment": f"{operator.name} (Operator)",
            "date": booking.created_at.strftime('%Y-%m-%d'),
            "amount": f"₹{booking.total_amount:.0f}",
            "method": booking.payment_method.upper(),
            "status": "successful" if booking.status == "confirmed" else ("pending" if booking.status == "pending" else "failed"),
            "type": "Operator",
            "transaction_id": booking.payment_id or f"TXN{booking.id}"
        })
    
    # Sort all payments by date (newest first)
    payment_list.sort(key=lambda x: x["date"], reverse=True)
    
    return jsonify(payment_list), 200

@app.route("/api/bookings/pdf", methods=["GET"])
def generate_equipment_bookings_pdf():
    """Generate PDF for equipment bookings"""
    from io import BytesIO
    import tempfile
    
    user_id = request.args.get('user_id', 1, type=int)
    
    # Fetch equipment bookings
    history = db.session.query(Booking, Equipment).join(
        Equipment, Booking.equipment_id == Equipment.id
    ).filter(Booking.user_id == user_id).order_by(Booking.start_date.desc()).all()
    
    if not history:
        return jsonify({"msg": "No equipment bookings found"}), 404
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#173c1c'),
        alignment=1  # Center
    )
    elements.append(Paragraph("🚜 AgroRent Equipment Booking History", title_style))
    elements.append(Spacer(1, 20))
    
    # User info
    user = User.query.get(user_id)
    user_info = f"<b>User:</b> {user.full_name if user and user.full_name else 'AgroRent User'}<br/>"
    user_info += f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
    user_info += f"<b>Total Bookings:</b> {len(history)}"
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['Booking ID', 'Equipment', 'Location', 'Start Date', 'End Date', 'Days', 'Rate/Day', 'Total']]
    
    for booking, equipment in history:
        duration = (booking.end_date - booking.start_date).days
        total_cost = duration * equipment.price
        data.append([
            str(booking.id),
            equipment.name[:20] + "..." if len(equipment.name) > 20 else equipment.name,
            equipment.location[:15] + "..." if equipment.location and len(equipment.location) > 15 else equipment.location or "N/A",
            booking.start_date.strftime('%Y-%m-%d'),
            booking.end_date.strftime('%Y-%m-%d'),
            str(duration),
            f"₹{equipment.price}",
            f"₹{total_cost}"
        ])
    
    # Create table
    table = Table(data, colWidths=[0.8*inch, 1.2*inch, 1.1*inch, 0.9*inch, 0.9*inch, 0.6*inch, 0.8*inch, 0.9*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#173c1c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Total summary
    total_amount = sum((booking.end_date - booking.start_date).days * equipment.price for booking, equipment in history)
    summary = f"<br/><b>Grand Total: ₹{total_amount}</b>"
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(summary, styles['Heading2']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=equipment_bookings_{datetime.now().strftime("%Y%m%d")}.pdf'}
    )

@app.route("/api/operator-bookings/pdf", methods=["GET"])
def generate_operator_bookings_pdf():
    """Generate PDF for operator bookings"""
    from io import BytesIO
    
    user_id = request.args.get('user_id', 1, type=int)
    
    # Fetch operator bookings
    history = db.session.query(OperatorBooking, Operator).join(
        Operator, OperatorBooking.operator_id == Operator.id
    ).filter(OperatorBooking.user_id == user_id).order_by(OperatorBooking.created_at.desc()).all()
    
    if not history:
        return jsonify({"msg": "No operator bookings found"}), 404
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.HexColor('#173c1c'),
        alignment=1  # Center
    )
    elements.append(Paragraph("👨‍🌾 AgroRent Operator Booking History", title_style))
    elements.append(Spacer(1, 20))
    
    # User info
    user = User.query.get(user_id)
    user_info = f"<b>User:</b> {user.full_name if user and user.full_name else 'AgroRent User'}<br/>"
    user_info += f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>"
    user_info += f"<b>Total Bookings:</b> {len(history)}"
    elements.append(Paragraph(user_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Table data
    data = [['Booking ID', 'Operator', 'Work Type', 'Start Date', 'Days', 'Rate/Day', 'Total', 'Status']]
    
    for booking, operator in history:
        data.append([
            str(booking.id),
            operator.name[:15] + "..." if len(operator.name) > 15 else operator.name,
            booking.work_type[:12] + "..." if len(booking.work_type) > 12 else booking.work_type,
            booking.start_date.strftime('%Y-%m-%d'),
            str(booking.working_days),
            f"₹{operator.price_per_day}",
            f"₹{booking.total_amount}",
            booking.status.title()
        ])
    
    # Create table
    table = Table(data, colWidths=[0.8*inch, 1.0*inch, 0.9*inch, 0.9*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#173c1c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Additional details section
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b>Booking Details:</b>", styles['Heading3']))
    
    for booking, operator in history:
        detail_text = f"""
        <b>Booking #{booking.id}</b><br/>
        Operator: {operator.name} ({operator.specialization})<br/>
        Experience: {operator.experience_years} years<br/>
        Location: {operator.location}<br/>
        Contact: {operator.contact_number}<br/>
        Field Size: {booking.field_size}<br/>
        Payment: {booking.payment_method.upper()} ({booking.payment_id})<br/>
        <br/>
        """
        elements.append(Paragraph(detail_text, styles['Normal']))
    
    # Total summary
    total_amount = sum(booking.total_amount for booking, operator in history)
    summary = f"<br/><b>Grand Total: ₹{total_amount}</b>"
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(summary, styles['Heading2']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=operator_bookings_{datetime.now().strftime("%Y%m%d")}.pdf'}
    )

@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name,
        "id": user.id
    }), 200

# ---------- Equipment detail & update (ADD THESE) ----------

@app.route("/equipment/<int:equipment_id>", methods=["GET"])
@jwt_required()
def get_equipment_by_id(equipment_id):
    """Owner can fetch a single equipment they own (handy if you need it)."""
    current_user_id = _current_user_id()
    eq = Equipment.query.get(equipment_id)
    if not eq:
        return jsonify({"msg": "Equipment not found"}), 404
    if eq.owner_id != current_user_id:
        return jsonify({"msg": "Permission denied"}), 403

    payload = {
        "id": eq.id,
        "name": eq.name,
        "description": eq.description,
        "price": eq.price,
        "contact_number": eq.contact_number,
        "image_url": f"/uploads/{eq.image_filename}" if eq.image_filename else None,
        "location": eq.location,
        "latitude": eq.latitude,
        "longitude": eq.longitude
    }
    return jsonify(payload), 200


@app.route("/equipment/<int:equipment_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_equipment(equipment_id):
    """
    Update fields for an equipment owned by current user.
    Accepts multipart/form-data for optional image replacement,
    or JSON for text/number fields.
    Allowed updatable fields: name, description, price, contact_number, location, latitude, longitude, image
    """
    current_user_id = _current_user_id()
    user = User.query.get(current_user_id)
    if not user or user.role != "owner":
        return jsonify({"msg": "Permission denied"}), 403

    eq = Equipment.query.get(equipment_id)
    if not eq:
        return jsonify({"msg": "Equipment not found"}), 404
    if eq.owner_id != current_user_id:
        return jsonify({"msg": "You can only update your own equipment"}), 403

    # Parse input
    is_multipart = request.content_type and "multipart/form-data" in request.content_type.lower()
    if is_multipart:
        form = request.form
        files = request.files
        name = (form.get("name") or "").strip()
        description = (form.get("description") or "").strip()
        price = form.get("price")
        contact_number = (form.get("contact_number") or "").strip()
        location = (form.get("location") or "").strip()
        latitude = form.get("latitude")
        longitude = form.get("longitude")
        image_file = files.get("image")
    else:
        data = request.get_json(silent=True) or {}
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        price = data.get("price")
        contact_number = (data.get("contact_number") or "").strip()
        location = (data.get("location") or "").strip()
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        image_file = None

    # Validate numbers if provided
    if price not in (None, ""):
        try:
            price_val = float(price)
            if price_val < 0:
                return jsonify({"msg": "Price must be a positive number."}), 400
        except ValueError:
            return jsonify({"msg": "Invalid price value."}), 400
        eq.price = price_val
    # lat/lon optional
    def _to_float_or_none(v):
        if v in (None, "", "null", "None"):
            return None
        try:
            return float(v)
        except Exception:
            return None
    lat_val = _to_float_or_none(latitude)
    lon_val = _to_float_or_none(longitude)
    if latitude is not None:
        eq.latitude = lat_val
    if longitude is not None:
        eq.longitude = lon_val

    if name: eq.name = name
    if description: eq.description = description
    if contact_number: eq.contact_number = contact_number
    if location: eq.location = location

    # Replace image if provided
    if image_file:
        ext = os.path.splitext(image_file.filename)[1].lower()
        new_name = f"equip_{eq.id}_{uuid.uuid4().hex}{ext}"
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], new_name)
        image_file.save(image_path)
        # delete old if existed
        if eq.image_filename:
            old = os.path.join(app.config["UPLOAD_FOLDER"], eq.image_filename)
            if os.path.exists(old):
                try: os.remove(old)
                except Exception: pass
        eq.image_filename = new_name

    db.session.commit()

    # Return updated card payload (same shape as /my-equipment uses)
    payload = {
        "id": eq.id,
        "name": eq.name,
        "description": eq.description,
        "price": eq.price,
        "contact_number": eq.contact_number,
        "image_url": f"/uploads/{eq.image_filename}" if eq.image_filename else "https://placehold.co/600x400/cccccc/333333?text=No+Image",
        "location": eq.location,
        "latitude": eq.latitude,
        "longitude": eq.longitude
    }
    return jsonify({"msg": "Equipment updated", "equipment": payload}), 200


# -----------------------------
# Operators API for frontend
# -----------------------------

@app.route("/api/operators", methods=["GET"])
def list_operators():
    """
    GET /api/operators
    optional query params:
        search - substring search on name or location
        availability - 'available' / 'unavailable' / 'all' (default all)
    Returns JSON list of operators.
    """
    search = request.args.get("search", "").strip()
    availability = request.args.get("availability", "all")

    query = Operator.query
    if availability in ("available", "unavailable"):
        query = query.filter(Operator.availability == availability)
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Operator.name.ilike(like), Operator.location.ilike(like)))

    ops = query.order_by(Operator.created_at.desc()).all()
    result = []
    for op in ops:
        # Check if operator should be available again
        current_availability = op.availability
        if op.unavailable_until and datetime.utcnow() >= op.unavailable_until:
            # Make operator available again
            op.availability = "available"
            op.unavailable_until = None
            db.session.commit()
            current_availability = "available"
            
        result.append({
            "id": op.id,
            "name": op.name,
            "contact_number": op.contact_number,
            "location": op.location or "",
            "latitude": op.latitude,
            "longitude": op.longitude,
            "availability": current_availability,
            "price_per_day": op.price_per_day or 800.0,
            "experience": f"{op.experience_years or 5} Years",
            "specialization": op.specialization or "Tractor Operations",
            "description": op.description or "Experienced operator"
        })
    return jsonify(result), 200


@app.route("/api/operators", methods=["POST"])
def create_operator():
    """
    POST /api/operators
    Body (application/json):
      { name, contact_number, location (optional), availability (optional), latitude (optional), longitude (optional) }
    """
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    contact_number = (data.get("contact_number") or "").strip()
    location = data.get("location")
    availability = data.get("availability") or "available"

    # Accept latitude/longitude if provided
    lat = data.get("latitude")
    lon = data.get("longitude")

    # basic validation
    if not name or not contact_number:
        return jsonify({"msg": "Name and contact number are required."}), 400

    try:
        if lat is not None:
            lat = float(lat)
        if lon is not None:
            lon = float(lon)
    except (ValueError, TypeError):
        return jsonify({"msg": "Latitude and longitude must be numeric."}), 400

    op = Operator(
        name=name,
        contact_number=contact_number,
        location=location,
        availability=availability,
        latitude=lat,
        longitude=lon
    )
    db.session.add(op)
    db.session.commit()

    return jsonify({
        "msg": "Operator created successfully.",
        "operator": {
            "id": op.id,
            "name": op.name,
            "contact_number": op.contact_number,
            "location": op.location,
            "availability": op.availability,
            "latitude": op.latitude,
            "longitude": op.longitude
        }
    }), 201



@app.route("/api/operators/<int:operator_id>/hire", methods=["POST"])
def hire_operator(operator_id):
    """
    POST /api/operators/<id>/hire
    Body (application/json): {
        "working_days": int,
        "work_type": str,
        "field_size": str,
        "start_date": str (ISO format),
        "payment_method": str,
        "payment_id": str (optional),
        "user_id": int (optional)
    }
    Creates a booking and marks operator unavailable for the booking period + 3 days.
    """
    op = Operator.query.get(operator_id)
    if not op:
        return jsonify({"msg": "Operator not found."}), 404

    if op.availability == "unavailable":
        return jsonify({"msg": "Operator is currently unavailable."}), 409

    data = request.get_json(force=True)
    
    # Extract booking data
    working_days = data.get("working_days", 1)
    work_type = data.get("work_type", "General Work")
    field_size = data.get("field_size", "Small")
    start_date_str = data.get("start_date")
    payment_method = data.get("payment_method", "pod")
    payment_id = data.get("payment_id", "")
    user_id = data.get("user_id", 1)  # Default user for testing
    
    try:
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00')) if start_date_str else datetime.utcnow()
    except:
        start_date = datetime.utcnow()
    
    # Calculate total amount
    total_amount = (op.price_per_day or 800.0) * working_days
    
    # Create operator booking
    booking = OperatorBooking(
        user_id=user_id,
        operator_id=operator_id,
        start_date=start_date,
        working_days=working_days,
        work_type=work_type,
        field_size=field_size,
        total_amount=total_amount,
        payment_method=payment_method,
        payment_id=payment_id,
        status="confirmed"
    )
    
    # Mark operator unavailable for working days + 3 additional days
    unavailable_days = working_days + 3
    op.availability = "unavailable"
    op.unavailable_until = start_date + timedelta(days=unavailable_days)
    
    db.session.add(booking)
    db.session.commit()

    return jsonify({
        "msg": "Operator booked successfully.",
        "booking_id": booking.id,
        "operator_id": op.id,
        "total_amount": total_amount,
        "unavailable_until": op.unavailable_until.isoformat()
    }), 200

@app.route("/api/operator-bookings", methods=["GET"])
def list_operator_bookings():
    """
    GET /api/operator-bookings
    Returns list of operator bookings
    """
    bookings = OperatorBooking.query.order_by(OperatorBooking.created_at.desc()).all()
    result = []
    
    for booking in bookings:
        operator = Operator.query.get(booking.operator_id)
        user = User.query.get(booking.user_id)
        
        result.append({
            "id": booking.id,
            "operator_name": operator.name if operator else "Unknown",
            "operator_contact": operator.contact_number if operator else "",
            "operator_location": operator.location if operator else "",
            "user_name": user.full_name if user else "Unknown",
            "start_date": booking.start_date.strftime("%Y-%m-%d"),
            "working_days": booking.working_days,
            "work_type": booking.work_type,
            "field_size": booking.field_size,
            "total_amount": booking.total_amount,
            "payment_method": booking.payment_method,
            "payment_id": booking.payment_id,
            "status": booking.status,
            "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    return jsonify(result), 200


@app.route("/api/operators/<int:operator_id>", methods=["PUT"])
def update_operator(operator_id):
    """
    PUT /api/operators/<id>
    Body: JSON fields to update: name, contact_number, location, availability
    """
    op = Operator.query.get(operator_id)
    if not op:
        return jsonify({"msg": "Operator not found."}), 404

    data = request.get_json(force=True)
    if "name" in data:
        op.name = data["name"]
    if "contact_number" in data:
        op.contact_number = data["contact_number"]
    if "location" in data:
        op.location = data["location"]
    if "availability" in data:
        op.availability = data["availability"]
    db.session.commit()
    return jsonify({"msg": "Operator updated.", "operator": {
        "id": op.id, "name": op.name, "contact_number": op.contact_number,
        "location": op.location, "availability": op.availability
    }}), 200

@app.route("/api/profile", methods=["GET"])
@jwt_required()
def api_profile():
    """
    GET /api/profile
    Returns the profile of the current JWT-authenticated user.
    """
    try:
        current_user_id = get_jwt_identity()
        # get_jwt_identity may return a string id - convert if needed
        try:
            uid = int(current_user_id)
        except Exception:
            uid = current_user_id

        user = User.query.get(uid)
        if not user:
            return jsonify({"msg": "User not found"}), 404

        profile = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.username,
            "role": user.role,
            "address": getattr(user, "address", None),
            "language": getattr(user, "language", None),
            # if you store user image filename/path:
            "image_url": (f"/uploads/{user.image_filename}" if getattr(user, "image_filename", None) else None)
        }
        return jsonify(profile), 200
    except Exception as e:
        app.logger.exception("Error in /api/profile")
        return jsonify({"msg": "Server error"}), 500
    
# ADD BELOW your existing /api/profile GET endpoint

@app.route("/api/profile", methods=["PUT", "PATCH", "POST"])
@jwt_required()
def update_profile():
    """
    Update current user's profile.
    Accepts either JSON or multipart/form-data (for image upload).
    Fields (all optional, only provided ones are updated):
      - full_name, email, phone (alias for username), address, language
      - image (file) -> saved into UPLOAD_FOLDER, stored in user.image_filename
    Returns updated profile JSON.
    """
    current_user_id = get_jwt_identity()
    # get_jwt_identity returns string if you set it that way
    try:
        uid = int(current_user_id)
    except Exception:
        uid = current_user_id

    user = User.query.get(uid)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Parse inputs
    is_multipart = request.content_type and "multipart/form-data" in request.content_type.lower()

    if is_multipart:
        form = request.form
        files = request.files
        full_name = (form.get("full_name") or "").strip()
        email = (form.get("email") or "").strip()
        phone = (form.get("phone") or "").strip()
        address = (form.get("address") or "").strip()
        language = (form.get("language") or "").strip()
        image_file = files.get("image")
    else:
        data = request.get_json(silent=True) or {}
        full_name = (data.get("full_name") or "").strip()
        email = (data.get("email") or "").strip()
        phone = (data.get("phone") or "").strip()
        address = (data.get("address") or "").strip()
        language = (data.get("language") or "").strip()
        image_file = None  # JSON path doesn't carry files

    # Email validation (only if provided and changed)
    if email and email != user.email:
        email_error = validate_email(email)
        if email_error:
            return jsonify({"msg": email_error}), 400
        # ensure uniqueness
        if User.query.filter(User.email == email, User.id != user.id).first():
            return jsonify({"msg": "Email already exists"}), 409

    # Username/phone uniqueness (only if provided and changed)
    if phone and phone != user.username:
        if User.query.filter(User.username == phone, User.id != user.id).first():
            return jsonify({"msg": "Username/phone already exists"}), 409

    # Persist image if provided
    if image_file:
        # sanitize + save
        ext = os.path.splitext(image_file.filename)[1].lower()
        safe_name = f"profile_{user.id}_{uuid.uuid4().hex}{ext}"
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
        image_file.save(image_path)
        # optional: delete old file if existed
        if getattr(user, "image_filename", None):
            old_path = os.path.join(app.config["UPLOAD_FOLDER"], user.image_filename)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except Exception:
                    pass
        user.image_filename = safe_name

    # Update scalar fields (only if provided)
    if full_name:
        user.full_name = full_name
    if email:
        user.email = email
    if phone:
        user.username = phone
    if address:
        user.address = address
    if language:
        user.language = language

    db.session.commit()

    # Build response profile
    profile = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.username,
        "role": user.role,
        "address": getattr(user, "address", None),
        "language": getattr(user, "language", None),
        "image_url": (f"/uploads/{user.image_filename}" if getattr(user, "image_filename", None) else None),
    }
    return jsonify({"msg": "Profile updated", "profile": profile}), 200

@app.route("/pod-success.html")
def serve_pod_success():
    return render_template("pod-success.html")

@app.route("/generate-qr", methods=["POST"])
def generate_qr():
    try:
        data = request.get_json()
        qr_data = data.get('data', '')
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({"qr_code": qr_base64}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download-invoice")
def download_invoice():
    try:
        # Get parameters
        booking_id = request.args.get('booking_id', 'AgroRent-2024-001')
        equipment = request.args.get('equipment', 'John Deere 5050D Tractor')
        amount = request.args.get('amount', '1530')
        days = request.args.get('days', '1')
        location = request.args.get('location', 'Mandya, Karnataka')
        payment_method = request.args.get('payment_method', 'Payment on Delivery')
        payment_id = request.args.get('payment_id', '')
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.HexColor('#173c1c')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#173c1c')
        )
        
        # Company Header
        story.append(Paragraph("AgroRent - ", title_style))
        
        # Different title based on payment method
        if payment_method == 'Razorpay' and payment_id:
            story.append(Paragraph("Payment Receipt & Equipment Booking Invoice", heading_style))
        else:
            story.append(Paragraph("Equipment Booking Invoice", heading_style))
        
        story.append(Spacer(1, 20))
        
        # Invoice details table
        invoice_data = [
            ['Invoice Details', ''],
            ['Booking ID:', booking_id],
            ['Date:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Payment Method:', payment_method],
        ]
        
        # Add payment ID for Razorpay payments
        if payment_method == 'Razorpay' and payment_id:
            invoice_data.append(['Payment ID:', payment_id])
            invoice_data.append(['Status:', 'PAID'])
        else:
            invoice_data.append(['Status:', 'Confirmed (Payment Pending)'])
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#173c1c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(invoice_table)
        story.append(Spacer(1, 30))
        
        # Equipment details
        story.append(Paragraph("Equipment Details", heading_style))
        
        equipment_data = [
            ['Equipment Details', ''],
            ['Equipment Name:', equipment],
            ['Location:', location],
            ['Rental Period:', f'{days} Day(s)'],
            ['Rate per Day:', f'₹{int(int(amount)/(int(days) if int(days) > 0 else 1))}'],
        ]
        
        equipment_table = Table(equipment_data, colWidths=[2*inch, 3*inch])
        equipment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#173c1c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(equipment_table)
        story.append(Spacer(1, 30))
        
        # Cost breakdown
        story.append(Paragraph("Cost Breakdown", heading_style))
        
        base_amount = int(int(amount) / 1.02)  # Remove 2% platform fee
        platform_fee = int(amount) - base_amount
        
        cost_data = [
            ['Cost Breakdown', ''],
            ['Rental Cost:', f'₹{base_amount}'],
            ['Platform Fee (2%):', f'₹{platform_fee}'],
            ['Total Amount:', f'₹{amount}'],
        ]
        
        # Add payment status based on method
        if payment_method == 'Razorpay' and payment_id:
            cost_data.append(['Amount Paid:', f'₹{amount}'])
            cost_data.append(['Balance Due:', '₹0'])
        else:
            cost_data.append(['Amount Paid:', '₹0'])
            cost_data.append(['Balance Due:', f'₹{amount}'])
        
        cost_table = Table(cost_data, colWidths=[2*inch, 3*inch])
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#173c1c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('BACKGROUND', (0, -3), (-1, -3), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, -3), (-1, -3), colors.whitesmoke),
            ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(cost_table)
        story.append(Spacer(1, 30))
        
        # Generate QR code for PDF
        qr_data = f"AgroRent-Booking:{booking_id}|Equipment:{equipment}|Amount:₹{amount}|Payment:{payment_method}|Verified"
        if payment_id:
            qr_data += f"|PaymentID:{payment_id}"
            
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to buffer
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # Add QR code to PDF
        story.append(Paragraph("Booking Verification QR Code", heading_style))
        story.append(Spacer(1, 10))
        
        # Create image from buffer
        qr_image = Image(qr_buffer, width=2*inch, height=2*inch)
        story.append(qr_image)
        story.append(Spacer(1, 20))
        
        # Terms and conditions
        story.append(Paragraph("Terms & Conditions", heading_style))
        terms = [
            "1. Equipment rental rates are per day basis",
            "2. Security deposit may be required for high-value equipment",
            "3. Late return charges: 20% of daily rate per hour",
            "4. Equipment damage charges apply as per assessment",
            "5. Cancellation allowed up to 2 hours before delivery",
            "6. Payment processing fees are non-refundable",
            "7. By using this service, you agree to our rental terms"
        ]
        
        if payment_method == 'Payment on Delivery':
            terms.append("8. Payment to be made in cash upon equipment delivery")
            terms.append("9. No equipment handover without payment completion")
        
        for term in terms:
            story.append(Paragraph(term, styles['Normal']))
        
        story.append(Spacer(1, 30))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.grey
        )
        
        if payment_method == 'Razorpay' and payment_id:
            story.append(Paragraph("Thank you for your payment and for choosing AgroRent!", footer_style))
        else:
            story.append(Paragraph("Thank you for choosing AgroRent!", footer_style))
            
        story.append(Paragraph("For support: support@AgroRent.com | Phone: +91-9876543210", footer_style))
        story.append(Paragraph("© 2024 AgroRent. All rights reserved.", footer_style))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        # Return PDF as response
        filename = f'AgroRent_Invoice_{booking_id}.pdf'
        if payment_method == 'Razorpay' and payment_id:
            filename = f'AgroRent_Receipt_{booking_id}.pdf'
            
        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)
