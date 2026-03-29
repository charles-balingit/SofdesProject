# models/model_bundle.py

import torch
import cv2
from pathlib import Path


class ModelBundle:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.face_model = None
        self.vitals_model = None

        self.load_models()

    # -------------------------
    # Load all models once
    # -------------------------
    def load_models(self):
        print("Loading models...")

        base_path = Path(__file__).parent

        face_path = base_path / "face_model.pt"
        vitals_path = base_path / "vitals_model.pt"

        self.face_model = torch.load(face_path, map_location=self.device)
        self.vitals_model = torch.load(vitals_path, map_location=self.device)

        self.face_model.eval()
        self.vitals_model.eval()

        print("Models loaded successfully.")

    # -------------------------
    # Face detection
    # -------------------------
    def detect_face(self, frame):
        # placeholder logic
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return gray

    # -------------------------
    # Predict vitals
    # -------------------------
    def predict_vitals(self, processed_frame):
        with torch.no_grad():
            tensor = torch.tensor(processed_frame).float().to(self.device)
            output = self.vitals_model(tensor)

        return output.cpu().numpy()


# Singleton instance (IMPORTANT)
model_bundle = ModelBundle()