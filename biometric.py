import cv2
import numpy as np
from deepface import DeepFace
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.image import Image
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('biometric.log')  # File output
    ]
)
logger = logging.getLogger(__name__)

class BiometricLoginDialog(MDDialog):
    def __init__(self, reference_img_path, on_success, **kwargs):
        self.reference_img_path = reference_img_path
        self.on_success = on_success
        self.camera = None
        self.camera_image = Image()
        
        logger.info("Initializing biometric login dialog")
        
        super().__init__(
            title="Face Recognition Login",
            type="custom",
            content_cls=self.camera_image,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=self.cancel_recognition
                )
            ],
            size_hint=(0.8, 0.7),
            auto_dismiss=False
        )

    def on_open(self):
        """Start camera when dialog opens"""
        logger.info("Opening camera for face recognition")
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                logger.error("Could not access camera")
                self.show_error("Could not access camera")
                return
                
            logger.info("Camera successfully opened")
            Clock.schedule_interval(self.update_frame, 1.0/30.0)
        except Exception as e:
            logger.error(f"Camera initialization failed: {str(e)}")
            self.show_error(f"Camera error: {str(e)}")

    def update_frame(self, dt):
        """Capture and process each frame"""
        try:
            ret, frame = self.camera.read()
            if not ret:
                logger.warning("Failed to capture frame from camera")
                return
                
            # Mirror and convert frame
            frame = cv2.flip(frame, 1)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            logger.debug("Processing frame for face recognition")
            
            # Verify face
            result = DeepFace.verify(
                img1_path=frame_rgb,
                img2_path=self.reference_img_path,
                model_name="Facenet",
                detector_backend="opencv",
                enforce_detection=False
            )
            
            # Log verification results
            logger.debug(f"Face verification result: {result}")
            
            if result.get("facial_areas", {}).get("img1"):
                face = result["facial_areas"]["img1"]
                x, y, w, h = face["x"], face["y"], face["w"], face["h"]
                
                if result["verified"]:
                    color = (0, 255, 0)  # Green for match
                    status = "MATCH"
                    logger.info(f"Face match found! Confidence: {1 - result['distance']:.2%}")
                    self.on_success()
                else:
                    color = (0, 0, 255)  # Red for no match
                    status = "NO MATCH"
                    logger.debug("Face detected but no match")
                
                # Draw rectangle and status
                cv2.rectangle(frame_rgb, (x, y), (x+w, y+h), color, 2)
                cv2.putText(frame_rgb, status, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Update display
            self.update_camera_preview(frame_rgb)
            
        except Exception as e:
            logger.error(f"Error during face recognition: {str(e)}")
            self.show_error(f"Recognition error: {str(e)}")

    def update_camera_preview(self, frame):
        """Update the dialog with camera frame"""
        try:
            buf = frame.tobytes()
            texture = Texture.create(
                size=(frame.shape[1], frame.shape[0]), 
                colorfmt='rgb'
            )
            texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
            self.camera_image.texture = texture
        except Exception as e:
            logger.error(f"Error updating camera preview: {str(e)}")

    def cancel_recognition(self, *args):
        """Handle cancel button press"""
        logger.info("Biometric login cancelled by user")
        self.cleanup()
        self.dismiss()

    def show_error(self, message):
        """Display error message"""
        logger.error(message)
        self.cleanup()
        self.dismiss()
        # You can show a snackbar here if needed

    def cleanup(self):
        """Release camera resources"""
        logger.info("Cleaning up biometric resources")
        if self.camera:
            self.camera.release()
            logger.info("Camera released")
        Clock.unschedule(self.update_frame)
        logger.info("Frame update unscheduled")

    def on_dismiss(self):
        """Ensure cleanup when dialog is dismissed"""
        logger.info("Dialog dismissed, performing cleanup")
        self.cleanup()
        super().on_dismiss()