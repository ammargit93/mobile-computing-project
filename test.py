# import cv2
# from deepface import DeepFace

# # Load reference face embedding (e.g., user_face.jpg)
# reference_img = "user_face2.jpg"

# def compare_faces(frame):
#     try:
#         result = DeepFace.verify(frame, reference_img, model_name="Facenet", enforce_detection=False)
#         return result["verified"], result["distance"]
#     except Exception as e:
#         print("⚠️ Face not detected:", e)
#         return False, None

# # Start webcam capture
# cap = cv2.VideoCapture(0)

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         break

#     match, distance = compare_faces(frame)

#     text = "MATCH ✅" if match else "NO MATCH ❌"
#     cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if match else (0, 0, 255), 2)
    
#     cv2.imshow("Face Matching", frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to exit
#         break

# cap.release()
# cv2.destroyAllWindows()
from kivy.lang import Builder

from kivymd.app import MDApp


KV = '''
MDFloatLayout:
    MDCheckbox:
        size_hint: None, None
        size: "48dp", "48dp"
        pos_hint: {'center_x': .5, 'center_y': .5}
'''


class Example(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)


Example().run()