from kivy.metrics import dp
from kivy.lang import Builder
from session import SessionManager
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from pymongo import MongoClient
from kivymd.uix.snackbar.snackbar import MDSnackbar, MDSnackbarActionButton
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import StringProperty, ListProperty
from kivy.graphics import Color, RoundedRectangle
from homescreen import HomeScreen
import cv2
import os

client = MongoClient("mongodb://localhost:27017/")
db = client["appDB"]
users_collection = db["users"]



import cv2
import numpy as np
from deepface import DeepFace

def load_and_convert_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image not found or unable to load!")
        return None
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    if image_rgb.dtype != np.uint8:
        image_rgb = (255 * (image_rgb / np.max(image_rgb))).astype(np.uint8)
    if image_rgb.size == 0:
        print("Error: Image is empty after conversion!")
        return None
    return image_rgb


class LoginScreen(Screen):
    def login(self):
        username = self.ids.username.text
        password = self.ids.password.text

        if username and password:
            user = users_collection.find_one({"username": username, "password": password})
            if user:
                self.show_snackbar(f"Login successful for {username}", "green")
                self.go_to_home()
                app = MDApp.get_running_app()
                app.session_manager.create_session(username)
            else:
                self.show_snackbar("User not found. Redirecting to Signup.", "red")
                self.go_to_signup()
        else:
            self.show_snackbar("Please fill in all fields", "orange")





    def biometric_login(self):
        reference_img = "user_face2.jpg"  
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.show_snackbar("Error: Could not access the webcam!", "red")
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                self.show_snackbar("Error: Failed to capture webcam frame!", "red")
                break
            try:
                result = DeepFace.verify(frame, reference_img, model_name="Facenet", enforce_detection=False)
                match = result["verified"]
            except Exception as e:
                print("⚠️ Face not detected:", e)
                match = False

            if match:
                self.show_snackbar("Biometric Login Successful!", "green")
                self.go_to_home()
                
                break  

        cap.release()  # Release webcam


    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(text=message),
            MDSnackbarActionButton(text="Done", theme_text_color="Custom", text_color=color),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.9,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()


    def go_to_signup(self):
        self.manager.current = "signup_screen"

    
    def go_to_login(self):
        self.manager.current = "login_screen"
    
    def go_to_home(self):
        self.manager.current = "home_screen"


class SignupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.role_menu = None

    
    def signup(self):
        username = self.ids.username.text
        email = self.ids.email.text
        password = self.ids.password.text
        confirm_password = self.ids.confirm_password.text
        
        if username and email and password and confirm_password:
            if password != confirm_password:
                self.show_snackbar("Passwords do not match!", "red")
                return

            existing_user = users_collection.find_one({"username": username})
            if existing_user:
                self.show_snackbar("Username already exists.", "red")
            else:
                users_collection.insert_one(
                    {"username": username, "email": email, "password": password}
                )
                self.manager.current = "login_screen"
                self.show_snackbar(f"Signup successful for {username}", "green")
        else:
            self.show_snackbar("Please fill in all fields", "orange")


    def show_snackbar(self, message, color):
        snackbar = MDSnackbar(
            MDLabel(
                text=message,
            ),
            MDSnackbarActionButton(
                text="Done",
                theme_text_color="Custom",
                text_color=color,
            ),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.5,
            md_bg_color="#E8D8D7",
        )
        snackbar.open()
        

class PreAuthScreen(Screen):
    def get_started(self):
        self.manager.current = "login_screen"


class AuthApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session_manager = SessionManager()

    def build(self):
        Builder.load_file('UI/authapp.kv')
        Builder.load_file('UI/homepage.kv')
        # Builder.load_file('UI/menu.kv')

        self.theme_cls.primary_palette = "Teal"
        sm = ScreenManager()

        session = self.session_manager.get_session()
        if session:
            sm.add_widget(HomeScreen(name="home_screen"))
            sm.current = "home_screen"
            sm.get_screen("home_screen").home()
        else:
            sm.add_widget(PreAuthScreen(name="pre_auth_screen"))
            sm.current = "pre_auth_screen"

        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(SignupScreen(name="signup_screen"))
        sm.add_widget(HomeScreen(name="home_screen"))

        return sm

    def go_back(self):
        login_screen = self.root.get_screen("login_screen")
        login_screen.ids.username.text = ""
        login_screen.ids.password.text = ""
        self.root.current = "login_screen"
