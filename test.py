import cv2
import numpy as np
from deepface import DeepFace

def face_recognition_with_gui():
    REFERENCE_IMG = "test.jpg" 
    WINDOW_NAME = "Face Recognition (Press Q to quit)"
    try:
        reference_img = cv2.imread(REFERENCE_IMG)
        if reference_img is None:
            raise FileNotFoundError(f"Reference image not found at {REFERENCE_IMG}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Error: Could not access webcam")
        return
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 800, 600)
    print("✅ Face recognition started - Press Q in the window to quit")
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Warning: Failed to capture frame")
                continue
            frame = cv2.flip(frame, 1)
            try:
                result = DeepFace.verify(
                    img1_path=frame,
                    img2_path=reference_img,
                    model_name="Facenet",
                    detector_backend="opencv",
                    enforce_detection=False
                )

                if result.get("facial_areas", {}).get("img1"):
                    face = result["facial_areas"]["img1"]
                    x, y, w, h = face["x"], face["y"], face["w"], face["h"]
                    color = (0, 255, 0) if result["verified"] else (0, 0, 255)
                    thickness = 2
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
                    status = "MATCH" if result["verified"] else "NO MATCH"
                    cv2.putText(frame, status, (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, thickness)
                    confidence = f"Confidence: {1 - result['distance']:.2%}"
                    cv2.putText(frame, confidence, (x, y+h+30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, thickness)
            except Exception as e:
                print(f"⚠️ Face recognition error: {str(e)}")
            cv2.imshow(WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Face recognition stopped")

face_recognition_with_gui()