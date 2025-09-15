# CORRECTED vision_engine.py FILE

import logging
import os
from collections import Counter
from datetime import datetime, timezone

import cv2
import face_recognition
import numpy as np
from sklearn.cluster import KMeans

from app import db
from app.models import Case, Sighting

# Configure proper logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class VisionProcessor:
    def __init__(self, case_id):
        self.case_id = case_id
        # FIX: Check if the case exists immediately to prevent crashes.
        self.case = Case.query.get(case_id)
        if not self.case:
            logging.error(f"VisionProcessor failed to initialize: Case {case_id} not found.")
            raise ValueError(f"Case {case_id} not found")

        self.target_encodings = self._get_target_encodings()
        self.target_colors = self._get_target_clothing_colors()
        self.frame_skip = 15  # Process every 15th frame for efficiency

        # FIX: Initialize a proper person detector (HOG detector).
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        logging.info(f"VisionProcessor initialized for case {self.case_id}")

    def _get_target_encodings(self):
        """Load all target images and return face encodings."""
        encodings = []
        for target_image in self.case.target_images:
            try:
                # Secure path construction to prevent path traversal
                from werkzeug.utils import secure_filename
                from flask import current_app
                
                # Validate and secure the image path
                if not target_image.image_path or '..' in target_image.image_path:
                    logging.warning(f"Invalid image path for target image {target_image.id}")
                    continue
                    
                # Use secure path construction
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
                filename = os.path.basename(target_image.image_path)
                secure_name = secure_filename(filename)
                image_path = os.path.join(upload_folder, secure_name)
                
                # Ensure path is within allowed directory
                if not os.path.abspath(image_path).startswith(os.path.abspath(upload_folder)):
                    logging.warning(f"Path traversal attempt detected for image {target_image.id}")
                    continue
                    
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                if face_encodings:
                    encodings.extend(face_encodings)
            except Exception:
                logging.error(f"Error processing target image {target_image.id} for case {self.case_id}", exc_info=True)
        return encodings

    def _get_target_clothing_colors(self):
        """Get dominant colors from target images."""
        # This is a placeholder for a more advanced color analysis.
        # For now, it relies on the user-provided colors.
        colors = []
        if self.case.primary_clothing_color:
            colors.append(self.case.primary_clothing_color)
        if self.case.secondary_clothing_color:
            colors.append(self.case.secondary_clothing_color)
        # In a future version, you could analyze target_images here.
        return colors

    def _detect_people(self, frame):
        """Detect people in a frame using HOG detector."""
        # FIX: Replaced placeholder with a real person detection model.
        (rects, weights) = self.hog.detectMultiScale(frame, winStride=(4, 4), padding=(8, 8), scale=1.05)
        # We only care about detections with a reasonable confidence (weight)
        confident_rects = [r for i, r in enumerate(rects) if weights[i] > 0.5]
        return confident_rects

    def _process_frame(self, frame, frame_number, fps, video_obj):
        """Process a single frame for person detection and matching."""
        timestamp = frame_number / fps
        people_boxes = self._detect_people(frame)

        for (x, y, w, h) in people_boxes:
            person_roi = frame[y : y + h, x : x + w]

            # Try face matching first
            face_confidence = self._match_face(person_roi)
            if face_confidence > 0.75:  # High confidence threshold for faces
                self._create_sighting(timestamp, face_confidence, "face", video_obj, person_roi)
                continue  # If we get a strong face match, we can be confident.

            # If no strong face match, try clothing matching
            # This logic can be expanded in the future
            # clothing_confidence = self._match_clothing(person_roi)
            # if clothing_confidence > 0.6:
            #     self._create_sighting(timestamp, clothing_confidence, "clothing", video_obj, person_roi)

    def _match_face(self, person_roi):
        """Match face in a person's region of interest (ROI)."""
        if not self.target_encodings:
            return 0.0
        try:
            rgb_roi = cv2.cvtColor(person_roi, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_roi)
            if not face_locations:
                return 0.0

            roi_face_encodings = face_recognition.face_encodings(rgb_roi, face_locations)
            if not roi_face_encodings:
                return 0.0

            # Compare the first found face against all target encodings
            matches = face_recognition.compare_faces(self.target_encodings, roi_face_encodings[0], tolerance=0.6)
            if any(matches):
                face_distances = face_recognition.face_distance(self.target_encodings, roi_face_encodings[0])
                # Confidence is inverse of distance
                confidence = 1.0 - min(face_distances)
                return confidence
        except Exception:
            # FIX: Replaced print() with proper logging.
            logging.error(f"Error during face matching for case {self.case_id}", exc_info=True)
        return 0.0

    def _create_sighting(self, timestamp, confidence, method, video_obj, person_roi):
        """Create a sighting record and save a thumbnail image."""
        try:
            from werkzeug.utils import secure_filename
            from flask import current_app
            
            # Create a secure filename for the thumbnail
            timestamp_str = f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
            thumbnail_filename = f"sighting_{self.case_id}_{video_obj.id}_{timestamp_str}.jpg"
            secure_name = secure_filename(thumbnail_filename)
            
            # Use secure path construction
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
            thumbnail_save_path = os.path.join(upload_folder, secure_name)
            
            # Ensure path is within allowed directory
            if not os.path.abspath(thumbnail_save_path).startswith(os.path.abspath(upload_folder)):
                logging.error(f"Invalid thumbnail path for case {self.case_id}")
                return
            
            # Verify write operation success
            success = cv2.imwrite(thumbnail_save_path, person_roi)
            if not success:
                logging.error(f"Failed to save thumbnail for case {self.case_id}")
                return
            
            # Path to store in the database (relative path)
            db_path = os.path.join('static', 'uploads', secure_name).replace('\\', '/')

            sighting = Sighting(
                case_id=self.case_id,
                search_video_id=video_obj.id,
                timestamp=timestamp,
                confidence_score=confidence,
                detection_method=method,
                thumbnail_path=db_path
            )
            db.session.add(sighting)
            db.session.commit()
            logging.info(f"Sighting created for case {self.case_id} at timestamp {timestamp:.2f}s")
        except Exception:
            db.session.rollback()
            logging.error(f"Failed to create sighting for case {self.case_id}", exc_info=True)

    def run_analysis(self):
        """Main method to analyze all search videos for the case."""
        logging.info(f"Starting analysis for case {self.case_id}")
        search_videos = self.case.search_videos

        for video in search_videos:
            video_path = os.path.join('app', video.video_path)
            if not os.path.exists(video_path):
                logging.error(f"Video file not found: {video_path} for case {self.case_id}")
                continue

            cap = None  # Initialize cap to None
            try:
                video.status = "Processing"
                db.session.commit()

                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    logging.error(f"Could not open video file: {video_path}")
                    video.status = "Failed"
                    db.session.commit()
                    continue
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = 0

                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_count % self.frame_skip == 0:
                        self._process_frame(frame, frame_count, fps, video)
                    frame_count += 1

                video.status = "Completed"
                # FIX: Use timezone-aware datetime object.
                video.processed_at = datetime.now(timezone.utc)
                db.session.commit()
                logging.info(f"Finished processing video {video.id} for case {self.case_id}")

            except Exception:
                logging.error(f"A critical error occurred while processing video {video.id}", exc_info=True)
                video.status = "Failed"
                db.session.commit()
            
            finally:
                # FIX: Ensure video capture is always released to prevent memory leaks.
                if cap is not None:
                    cap.release()