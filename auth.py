from kivy.metrics import dp
from kivy.lang import Builder
from session import SessionManager
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from pymongo import MongoClient
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarActionButton
from kivymd.uix.label import MDLabel
from homescreen import HomeScreen
import random

client = MongoClient("mongodb://localhost:27017/")
db = client["appDB"]
users_collection = db["users"]
otp_collection = db["otps"]

class LoginScreen(Screen):
    def go_to_otp(self):
        phone_number = self.ids.phone_number.text.strip()
        if phone_number and phone_number.isdigit():
            user = users_collection.find_one({"phone_number": phone_number})
            if user:
                otp = str(random.randint(100000, 999999))
                otp_collection.insert_one({"phone_number": phone_number, "otp": otp})
                self.show_snackbar(f"OTP sent to {phone_number}", "green")
                self.manager.current = "otp_screen"
            else:
                self.show_snackbar("User not found. Please sign up.", "red")
                self.manager.current = "signup_screen"
        else:
            self.show_snackbar("Enter a valid phone number.", "orange")

    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="OK", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()

class SignupScreen(Screen):
    def signup(self):
        full_name = self.ids.full_name.text.strip()
        phone_number = self.ids.phone_number.text.strip()
        
        if full_name and phone_number.isdigit():
            existing_user = users_collection.find_one({"phone_number": phone_number})
            if existing_user:
                self.show_snackbar("Phone number already registered.", "red")
            else:
                users_collection.insert_one({"full_name": full_name, "phone_number": phone_number})
                self.show_snackbar("Signup successful. Please verify OTP.", "green")
                self.manager.current = "otp_screen"
        else:
            self.show_snackbar("Enter valid details.", "orange")

    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="OK", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()

class OTPScreen(Screen):
    def verify_otp(self):
        phone_number = self.manager.get_screen("login_screen").ids.phone_number.text.strip()
        entered_otp = self.ids.otp.text.strip()
        
        otp_entry = otp_collection.find_one({"phone_number": phone_number, "otp": entered_otp})
        if otp_entry:
            otp_collection.delete_one({"phone_number": phone_number})
            self.show_snackbar("OTP Verified. Login Successful!", "green")
            app = MDApp.get_running_app()
            app.session_manager.create_session(phone_number)
            self.manager.current = "home_screen"
        else:
            self.show_snackbar("Invalid OTP. Try again.", "red")

    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="OK", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()

from kivy.lang import Builder

class AuthApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = SessionManager()

    def build(self):
        self.theme_cls.primary_palette = "Teal"
        
        # Load KV file
        Builder.load_file("UI/authapp.kv")  # Ensure path is correct

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignupScreen(name="signup_screen"))
        sm.add_widget(OTPScreen(name="otp_screen"))
        sm.add_widget(HomeScreen(name="home_screen"))
        return sm
