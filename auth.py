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
import requests

client = MongoClient("mongodb://localhost:27017/")
db = client["appDB"]
users_collection = db["users"]
notes_collection = db["notes"]

def send_otp(phone_number):
    url = "http://127.0.0.1:5000/send_otp"
    response = requests.post(url, json={"phone_number": phone_number})
    return response.json()

def verify_otp(session_info, otp_code):
    url = "http://127.0.0.1:5000/verify_otp"
    response = requests.post(url, json={"session_info": session_info, "otp_code": otp_code})
    return response.json()
phone_num = None
class LoginScreen(Screen):
    def go_to_otp(self):
        phone_number = self.ids.phone_number.text.strip()
        print(f"""Phone number: {phone_number}\n\n\n""")
        global phone_num
        phone_num = str(phone_number[3:])
        print(f"""Phone number: {phone_num}\n\n\n""")
        if phone_number:
            response = send_otp(phone_number)
            if "session_info" in response:
                self.manager.get_screen("otp_screen").session_info = response["session_info"]
                self.show_snackbar("OTP Sent Successfully!", "green")
                self.manager.current = "otp_screen"
            else:
                self.show_snackbar("Failed to send OTP.", "red")
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
    def open_menu(self, caller):
        menu_items = [
            {"text": "Guest", "viewclass": "OneLineListItem", "on_release": lambda x="Guest": self.set_item(x)},
            {"text": "Admin", "viewclass": "OneLineListItem", "on_release": lambda x="Admin": self.set_item(x)},
        ]

        self.menu = MDDropdownMenu(caller=caller, items=menu_items, width_mult=4)
        self.menu.open()

    def set_item(self, text):
        self.ids.user_type.text = text
        self.menu.dismiss()

    def signup(self):
        full_name = self.ids.full_name.text.strip()
        phone_number = self.ids.phone_number.text.strip()
        user_type = self.ids.user_type.text.strip()

        if full_name and phone_number.isdigit():
            existing_user = users_collection.find_one({"phone_number": phone_number})
            if existing_user:
                self.show_snackbar("Phone number already registered.", "red")
            else:
                users_collection.insert_one({"full_name": full_name, "phone_number": phone_number, "user_type": user_type})
                self.show_snackbar("Signup successful! Please verify OTP.", "green")
                self.manager.current = "login_screen"
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
    session_info = None

    def verify_otp(self):
        entered_otp = self.ids.otp.text.strip()
        if not self.session_info:
            self.show_snackbar("Session expired. Request OTP again.", "red")
            self.manager.current = "login_screen"
            return

        response = verify_otp(self.session_info, entered_otp)
        if response.get("success"):
            self.show_snackbar("OTP Verified. Login Successful!", "green")
            user = users_collection.find_one({"phone_number": phone_num})
            user_type = user['user_type']
            if user_type == "Admin":
                self.manager.current = "admin_home"
            else:
                self.manager.current = "guest_home"
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

class AuthApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = SessionManager()

    def change_screen(self, screen_name):
        self.root.current = screen_name  
        
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        Builder.load_file("UI/authapp.kv")  
        Builder.load_file("UI/homepage.kv")   

        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignupScreen(name="signup_screen"))
        sm.add_widget(OTPScreen(name="otp_screen"))
        sm.add_widget(GuestHomeScreen(name="guest_home"))
        sm.add_widget(AdminHomeScreen(name="admin_home"))
        return sm

if __name__ == '__main__':
    AuthApp().run()