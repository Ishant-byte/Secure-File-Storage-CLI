import random
import time
import mysql.connector
import database_setup as db

def get_db_connection():
    return mysql.connector.connect(
        host=db.DB_HOST,
        user=db.DB_USER,
        password=db.DB_PASSWORD,
        database=db.DB_NAME
    )

def generate_otp(length=6):
    """Generate a random numeric OTP of specified length"""
    digits = "0123456789"
    otp = ""
    for _ in range(length):
        otp += random.choice(digits)
    return otp

def store_otp(email, otp):
    """Store the OTP in the database with the user's email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear any existing OTPs for this email
    cursor.execute("DELETE FROM otps WHERE email = %s", (email,))
    
    # Insert new OTP
    cursor.execute(
        "INSERT INTO otps (email, otp, created_at) VALUES (%s, %s, NOW())",
        (email, otp)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def verify_otp(email, entered_otp):
    """Verify if the entered OTP matches the stored OTP for the email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get the stored OTP
    cursor.execute(
        "SELECT otp, created_at FROM otps WHERE email = %s ORDER BY created_at DESC LIMIT 1",
        (email,)
    )
    result = cursor.fetchone()
    
    if not result:
        cursor.close()
        conn.close()
        return False
    
    stored_otp, created_at = result
    
    # Check if OTP is expired (5 minutes validity)
    current_time = time.time()
    otp_time = created_at.timestamp()
    
    if current_time - otp_time > 300:  # 300 seconds = 5 minutes
        cursor.execute("DELETE FROM otps WHERE email = %s", (email,))
        conn.commit()
        cursor.close()
        conn.close()
        return False
    
    # Verify OTP
    is_valid = stored_otp == entered_otp
    
    # Remove used OTP
    if is_valid:
        cursor.execute("DELETE FROM otps WHERE email = %s", (email,))
        conn.commit()
    
    cursor.close()
    conn.close()
    return is_valid