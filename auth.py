from kivy.metrics import dp
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from session import SessionManager
from homescreen import GuestHomeScreen, AdminHomeScreen
from filescreen import FilesScreen
from chatbot import ChatbotScreen
from ocr import OCRScreen
from dotenv import load_dotenv
from config import notes_collection, users_collection
from biometric import BiometricLoginDialog, logger
import requests

load_dotenv()

class LoginScreen(Screen):
    API_BASE_URL = "http://localhost:5000"  # Flask API URL
    
    def go_to_biometric(self):
        """Start biometric face recognition"""
        phone_number = self.ids.phone_number.text.strip()
        if not phone_number:
            logger.warning("No phone number entered for biometric login")
            self.show_snackbar("Enter phone number first", "red")
            return
            
        logger.info(f"Starting biometric login for phone: {phone_number}")
        
        user = users_collection.find_one({"phone_number": phone_number[3:]})
        if not user:
            logger.warning(f"No user found for phone: {phone_number}")
            self.show_snackbar("User not found", "red")
            return
            
        reference_img = f"test.jpg"
        logger.info(f"Using reference image: {reference_img}")
        
        def on_success():
            """Handle successful recognition"""
            logger.info("Biometric recognition successful")
            self.on_biometric_success(user)
        
        self.biometric_dialog = BiometricLoginDialog(
            reference_img_path=reference_img,
            on_success=on_success
        )
        self.biometric_dialog.open()
        logger.info("Biometric dialog opened")

    def on_biometric_success(self, user):
        """Handle successful biometric login"""
        logger.info(f"Processing successful login for user: {user['_id']}")
        username = user['full_name']
        user_type = user['user_type']
        user_id = str(user['_id'])
        
        MDApp.get_running_app().session_manager.create_session(
            username, user_type, user_id
        )
        
        logger.info("Session created, navigating to home screen")
        self.show_snackbar("Biometric login successful!", "green")
        self.biometric_dialog.dismiss()
        self.manager.current = "admin_home" if user_type == "Admin" else "guest_home"

    def on_biometric_fail(self, dialog, message):
        """Handle failed biometric login"""
        dialog.dismiss()
        self.show_snackbar(f"Biometric login failed: {message}", "red")

    def go_to_otp(self):
        phone_number = self.ids.phone_number.text.strip()
        if not phone_number:
            self.show_snackbar("Enter a valid phone number.", "orange")
            return
            
        phone_num = str(phone_number[3:]) if phone_number.startswith("+91") else phone_number
        
        try:
            response = requests.post(
                f"{self.API_BASE_URL}/generate-otp",
                json={"phone_number": phone_num}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.manager.get_screen("otp_screen").secret_key = data["secret_key"]
                self.manager.get_screen("otp_screen").phone_number = phone_num
                self.show_snackbar("OTP Sent Successfully! Check your mail!", "green")
                self.manager.current = "otp_screen"
            else:
                error = response.json().get("error", "Failed to send OTP")
                self.show_snackbar(error, "red")
                
        except requests.exceptions.RequestException as e:
            self.show_snackbar("Failed to connect to OTP service", "red")

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
    API_BASE_URL = "http://localhost:5000"
    secret_key = None
    phone_number = None
    
    def verify_otp(self):
        entered_otp = self.ids.otp.text.strip()
        
        if not all([entered_otp, self.secret_key, self.phone_number]):
            self.show_snackbar("Invalid OTP verification request", "red")
            return
            
        try:
            response = requests.post(
                f"{self.API_BASE_URL}/verify-otp",
                json={
                    "phone_number": self.phone_number,
                    "otp": entered_otp,
                    "secret_key": self.secret_key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                user = data["user"]
                
                MDApp.get_running_app().session_manager.create_session(
                    user["full_name"],
                    user["user_type"],
                    user["id"]
                )
                
                self.show_snackbar("OTP Verified. Login Successful!", "green")
                self.manager.current = "admin_home" if user["user_type"] == "Admin" else "guest_home"
            else:
                error = response.json().get("error", "OTP verification failed")
                self.show_snackbar(error, "red")
                
        except requests.exceptions.RequestException as e:
            self.show_snackbar("Failed to connect to OTP service", "red")

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

# if __name__ == '__main__':
#     AuthApp().run()