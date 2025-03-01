import getpass
import os
import database_setup as db
import file_upload
import file_download
import local_otp
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host=db.DB_HOST,
        user=db.DB_USER,
        password=db.DB_PASSWORD,
        database=db.DB_NAME
    )

def register_user():
    print("\n--- User Registration ---")
    username = input("Enter username: ")
    email = input("Enter email: ")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        print("❌ User already exists! Please login instead.")
    else:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", 
                       (username, email, "default_hashed_password"))
        conn.commit()
        print("✅ Registration successful! Please login.")
    cursor.close()
    conn.close()

def login_user():
    print("\n--- User Login ---")
    email = input("Enter email: ")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    if not user:
        print("❌ User not found! Please register first.")
        cursor.close()
        conn.close()
        return None
    
    otp = local_otp.generate_otp()
    local_otp.store_otp(email, otp)
    print(f'🔢 Your OTP is: {otp}')  # Display OTP in terminal
    
    entered_otp = input("Enter OTP: ")
    if local_otp.verify_otp(email, entered_otp):
        print("✅ Login successful!")
        cursor.close()
        conn.close()
        return email
    else:
        print("❌ Incorrect OTP. Try again.")
        cursor.close()
        conn.close()
        return None

def upload_file(email):
    print("\n--- File Upload ---")
    file_path = input("Enter the full path of the file to upload: ")
    
    if not os.path.exists(file_path):
        print("❌ File not found! Please check the path and try again.")
        return
    
    if file_upload.upload_file(email, file_path):
        print("✅ File uploaded successfully!")
    else:
        print("❌ File upload failed.")

def download_file(email):
    print("\n--- Available Files for Download ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT filename FROM files 
        WHERE user_id = (SELECT id FROM users WHERE email = %s)
        AND is_hidden = 0
        ORDER BY filename
    """, (email,))
    files = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if not files:
        print("❌ No files found for download.")
        return
    
    for idx, file in enumerate(files, 1):
        print(f"{idx}. {file[0]}")
    
    choice = input("Enter the number of the file to download (or 'q' to quit): ")
    if choice.lower() == 'q':
        return
        
    try:
        selected_idx = int(choice) - 1
        if 0 <= selected_idx < len(files):
            selected_file = files[selected_idx][0]
            if file_download.download_file(email, selected_file):
                print("✅ File downloaded successfully!")
        else:
            print("❌ Invalid selection!")
    except (IndexError, ValueError):
        print("❌ Invalid selection!")

def manage_files(email):
    while True:
        print("\n--- Manage Files ---")
        print("1. Delete File")
        print("2. Hide File")
        print("3. Unhide File")
        print("4. Back to Main Menu")
        
        choice = input("Enter your choice: ")
        if choice == "1":
            delete_file(email)
        elif choice == "2":
            hide_file(email)
        elif choice == "3":
            unhide_file(email)
        elif choice == "4":
            return
        else:
            print("❌ Invalid choice!")

def delete_file(email):
    print("\n--- Delete File ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename FROM files 
        WHERE user_id = (SELECT id FROM users WHERE email = %s)
        ORDER BY filename
    """, (email,))
    files = cursor.fetchall()
    
    if not files:
        print("❌ No files found to delete.")
        cursor.close()
        conn.close()
        return
    
    for idx, (_, filename) in enumerate(files, 1):
        print(f"{idx}. {filename}")
    
    choice = input("Enter the number of the file to delete (or 'q' to quit): ")
    if choice.lower() == 'q':
        cursor.close()
        conn.close()
        return
        
    try:
        selected_idx = int(choice) - 1
        if 0 <= selected_idx < len(files):
            file_id, filename = files[selected_idx]
            
            confirm = input(f"Are you sure you want to delete '{filename}'? (y/n): ")
            if confirm.lower() == 'y':
                cursor.execute("SELECT file_path FROM files WHERE id = %s", (file_id,))
                file_path = cursor.fetchone()[0]
                
                # Delete from database
                cursor.execute("DELETE FROM files WHERE id = %s", (file_id,))
                conn.commit()
                
                # Delete from filesystem if exists
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        print("⚠️ File removed from database but could not be deleted from disk.")
                
                print(f"✅ File '{filename}' deleted successfully!")
            else:
                print("Deletion cancelled.")
        else:
            print("❌ Invalid selection!")
    except (IndexError, ValueError):
        print("❌ Invalid selection!")
    
    cursor.close()
    conn.close()

def hide_file(email):
    print("\n--- Hide File ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename FROM files 
        WHERE user_id = (SELECT id FROM users WHERE email = %s)
        AND is_hidden = 0
        ORDER BY filename
    """, (email,))
    files = cursor.fetchall()
    
    if not files:
        print("❌ No visible files found to hide.")
        cursor.close()
        conn.close()
        return
    
    for idx, (_, filename) in enumerate(files, 1):
        print(f"{idx}. {filename}")
    
    choice = input("Enter the number of the file to hide (or 'q' to quit): ")
    if choice.lower() == 'q':
        cursor.close()
        conn.close()
        return
        
    try:
        selected_idx = int(choice) - 1
        if 0 <= selected_idx < len(files):
            file_id, filename = files[selected_idx]
            
            cursor.execute("UPDATE files SET is_hidden = 1 WHERE id = %s", (file_id,))
            conn.commit()
            
            print(f"✅ File '{filename}' hidden successfully!")
        else:
            print("❌ Invalid selection!")
    except (IndexError, ValueError):
        print("❌ Invalid selection!")
    
    cursor.close()
    conn.close()

def unhide_file(email):
    print("\n--- Unhide File ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, filename FROM files 
        WHERE user_id = (SELECT id FROM users WHERE email = %s)
        AND is_hidden = 1
        ORDER BY filename
    """, (email,))
    files = cursor.fetchall()
    
    if not files:
        print("❌ No hidden files found to unhide.")
        cursor.close()
        conn.close()
        return
    
    for idx, (_, filename) in enumerate(files, 1):
        print(f"{idx}. {filename}")
    
    choice = input("Enter the number of the file to unhide (or 'q' to quit): ")
    if choice.lower() == 'q':
        cursor.close()
        conn.close()
        return
        
    try:
        selected_idx = int(choice) - 1
        if 0 <= selected_idx < len(files):
            file_id, filename = files[selected_idx]
            
            cursor.execute("UPDATE files SET is_hidden = 0 WHERE id = %s", (file_id,))
            conn.commit()
            
            print(f"✅ File '{filename}' unhidden successfully!")
        else:
            print("❌ Invalid selection!")
    except (IndexError, ValueError):
        print("❌ Invalid selection!")
    
    cursor.close()
    conn.close()

def main():
    logged_in_user = None  # Track the logged-in user

    # Ensure required directories exist
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)

    while True:
        print("\nWelcome to Secure File Storage CLI")
        print("1. Register")
        print("2. Login")
        print("3. Upload File")
        print("4. Download File")
        print("5. Manage Files")
        print("6. Exit")
        
        choice = input("Enter your choice: ")
        
        if choice == "1":
            register_user()
        elif choice == "2":
            logged_in_user = login_user()
        elif choice == "3":
            if logged_in_user:
                upload_file(logged_in_user)
            else:
                print("❌ Please login first!")
        elif choice == "4":
            if logged_in_user:
                download_file(logged_in_user)
            else:
                print("❌ Please login first!")
        elif choice == "5":
            if logged_in_user:
                manage_files(logged_in_user)
            else:
                print("❌ Please login first!")
        elif choice == "6":
            print("Exiting...")
            break
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main()