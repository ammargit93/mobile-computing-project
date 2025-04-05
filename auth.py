from kivy.metrics import dp
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from pymongo import MongoClient
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from session import SessionManager
from homescreen import GuestHomeScreen, AdminHomeScreen
from filescreen import FilesScreen
from chatbot import ChatbotScreen
from ocr import OCRScreen
import pyotp
from dotenv import load_dotenv
from config import notes_collection, users_collection
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

email_address = os.getenv("EMAIL")
email_password = os.getenv("PASSWORD")
# client = MongoClient("mongodb://localhost:27017/")
# db = client["appDB"]
# users_collection = db["users"]
# notes_collection = db["notes"]

phone_num = None
gotp = None

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = email_address
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.sendmail(email_address, to_email, msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")

class LoginScreen(Screen):
    def go_to_otp(self):
        phone_number = self.ids.phone_number.text.strip()
        global phone_num
        phone_num = str(phone_number[3:])
        user = users_collection.find_one({"phone_number": phone_num})
        
        if not user:
            self.show_snackbar("User not found. Please sign up first.", "red")
            return
            
        if phone_number:
            self.secret_key = pyotp.random_base32()
            self.totp = pyotp.TOTP(self.secret_key)
            global gotp
            gotp = self.totp.now()
            email = user['email']
            send_email(email, "OTP Mail", f"Your OTP is {gotp}")
            self.show_snackbar("OTP Sent Successfully! Check your mail!", "green")
            self.manager.current = "otp_screen"
        else:
            self.show_snackbar("Enter a valid phone number.", "orange")

    def show_snackbar(self, message, color):
        MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="OK", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        ).open()

class SignupScreen(Screen):
    def open_menu(self, caller):
        MDDropdownMenu(
            caller=caller,
            items=[
                {"text": "Guest", "viewclass": "OneLineListItem", "on_release": lambda x="Guest": self.set_item(x)},
                {"text": "Admin", "viewclass": "OneLineListItem", "on_release": lambda x="Admin": self.set_item(x)},
            ],
            width_mult=4
        ).open()

    def set_item(self, text):
        self.ids.user_type.text = text

    def signup(self):
        full_name = self.ids.full_name.text.strip()
        phone_number = self.ids.phone_number.text.strip()
        user_type = self.ids.user_type.text.strip()
        email = self.ids.email.text.strip()
        
        if not all([full_name, phone_number.isdigit(), user_type, email]):
            self.show_snackbar("Enter valid details.", "orange")
            return
            
        if users_collection.find_one({"phone_number": phone_number}):
            self.show_snackbar("Phone number already registered.", "red")
            return
            
        users_collection.insert_one({
            "full_name": full_name,
            "phone_number": phone_number,
            "user_type": user_type,
            "email": email
        })
        self.show_snackbar("Signup successful! Please login.", "green")
        self.manager.current = "login_screen"

    def show_snackbar(self, message, color):
        MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="OK", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        ).open()

class OTPScreen(Screen):
    def verify_otp(self):
        entered_otp = self.ids.otp.text.strip()
        global phone_num, gotp
        
        if entered_otp != str(gotp):
            self.show_snackbar("Invalid OTP. Try again.", "red")
            return
            
        user = users_collection.find_one({"phone_number": phone_num})
        if not user:
            self.show_snackbar("User not found.", "red")
            return
            
        username = user['full_name']
        user_type = user['user_type']
        user_id = str(user['_id'])
        MDApp.get_running_app().session_manager.create_session(username, user_type, user_id)
        self.show_snackbar("OTP Verified. Login Successful!", "green")
        self.manager.current = "admin_home" if user_type == "Admin" else "guest_home"

    def show_snackbar(self, message, color):
        MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="OK", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        ).open()

class AuthApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = SessionManager()

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        Builder.load_file("UI/authapp.kv")  
        Builder.load_file("UI/homepage.kv")   
        Builder.load_file("UI/files.kv")   
        Builder.load_file("UI/chatbot.kv")   
        Builder.load_file("UI/ocr.kv")   
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignupScreen(name="signup_screen"))
        sm.add_widget(OTPScreen(name="otp_screen"))
        sm.add_widget(GuestHomeScreen(name="guest_home"))
        sm.add_widget(AdminHomeScreen(name="admin_home"))
        sm.add_widget(FilesScreen(name="files_screen"))
        sm.add_widget(ChatbotScreen(name="chatbot_screen"))
        sm.add_widget(OCRScreen(name="ocr_screen"))

        session = self.session_manager.get_session()
        if session:
            sm.current = "admin_home" if session['user_type'] == "Admin" else "guest_home"
        else:
            sm.current = "login_screen"
        return sm

if __name__ == '__main__':
    AuthApp().run()