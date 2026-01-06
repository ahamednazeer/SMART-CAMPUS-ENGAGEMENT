"""
Face recognition service using DeepFace for face verification.
"""
import os
import json
from typing import Optional, Tuple, List
import numpy as np


class FaceRecognitionService:
    """Service for face detection and recognition using DeepFace."""
    
    # Face match threshold (0-1, lower is stricter)
    # Face match threshold (0-1, lower is stricter)
    # For ArcFace with cosine distance, 0.68 is a standard threshold
    DEFAULT_THRESHOLD = 0.68  
    
    def __init__(self):
        self._deepface = None
    
    @property
    def deepface(self):
        """Lazy load DeepFace to avoid import overhead."""
        if self._deepface is None:
            try:
                from deepface import DeepFace
                self._deepface = DeepFace
            except ImportError:
                raise ImportError(
                    "DeepFace is not installed. Please run: pip install deepface"
                )
        return self._deepface
    
    def detect_faces(self, image_path: str) -> int:
        """
        Detect number of faces in an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Number of faces detected
        """
        try:
            # Use DeepFace's built-in face detection
            faces = self.deepface.extract_faces(
                img_path=image_path,
                detector_backend="opencv",
                enforce_detection=False
            )
            # Filter out low-confidence detections
            valid_faces = [f for f in faces if f.get("confidence", 0) > 0.5]
            return len(valid_faces)
        except Exception as e:
            # If detection fails entirely, return 0
            print(f"Face detection error: {e}")
            return 0
    
    def validate_face_image(self, image_path: str) -> Tuple[bool, str]:
        """
        Validate that an image has exactly one clear face.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(image_path):
            return False, "Image file not found"
        
        face_count = self.detect_faces(image_path)
        
        if face_count == 0:
            return False, "No face detected in image"
        elif face_count > 1:
            return False, f"Multiple faces detected ({face_count})"
        
        return True, "Valid face image"
    
    def extract_face_encoding(self, image_path: str) -> Optional[List[float]]:
        """
        Extract face embedding/encoding from an image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Face encoding as list of floats, or None if extraction fails
        """
        try:
            # Get face embedding using DeepFace
            embedding_objs = self.deepface.represent(
                img_path=image_path,
                model_name="ArcFace",
                detector_backend="opencv",
                enforce_detection=True
            )
            
            if embedding_objs and len(embedding_objs) > 0:
                # Return the first face's embedding
                return embedding_objs[0]["embedding"]
            return None
            
        except Exception as e:
            print(f"Face encoding extraction error: {e}")
            return None
    
    def compare_faces(
        self, 
        known_encoding: List[float], 
        unknown_encoding: List[float],
        threshold: float = None
    ) -> Tuple[bool, float]:
        """
        Compare two face encodings to determine if they match.
        
        Args:
            known_encoding: Reference face encoding
            unknown_encoding: Face encoding to verify
            threshold: Match threshold (lower = stricter)
            
        Returns:
            Tuple of (is_match, similarity_score)
            similarity_score is between 0 and 1, where 1 means identical
        """
        if threshold is None:
            threshold = self.DEFAULT_THRESHOLD
        
        try:
            # Convert to numpy arrays
            known = np.array(known_encoding)
            unknown = np.array(unknown_encoding)
            
            # Calculate cosine distance
            # Cosine distance = 1 - cosine_similarity
            dot_product = np.dot(known, unknown)
            norm_known = np.linalg.norm(known)
            norm_unknown = np.linalg.norm(unknown)
            
            cosine_similarity = dot_product / (norm_known * norm_unknown)
            cosine_distance = 1 - cosine_similarity
            
            # Convert distance to similarity score using informed mapping
            similarity_score = self._distance_to_similarity(cosine_distance)
            
            # Check if match (using the 60% uncertainty threshold as the absolute minimum)
            is_match = similarity_score >= 0.60
            
            return is_match, round(similarity_score, 4)
            
        except Exception as e:
            print(f"Face comparison error: {e}")
            return False, 0.0

    def _distance_to_similarity(self, distance: float) -> float:
        """
        Convert ArcFace cosine distance to similarity percentage based on user requirements.
        Threshold (d=0.68) maps to 60% (Uncertain boundary).
        
        Mapping logic:
        - 0.00 distance -> 100% (Identical)
        - 0.30 distance -> 90%  (Strong match boundary)
        - 0.50 distance -> 75%  (Likely same person boundary)
        - 0.68 distance -> 60%  (Uncertain boundary / Match threshold)
        - 1.00+ distance -> 0%  (Not a match)
        """
        d = min(max(distance, 0.0), 1.0)
        
        if d <= 0.3:
            # Linear map 0.0..0.3 to 1.0..0.9
            return 1.0 - (d / 0.3) * 0.1
        elif d <= 0.5:
            # Linear map 0.3..0.5 to 0.9..0.75
            return 0.9 - ((d - 0.3) / (0.5 - 0.3)) * 0.15
        elif d <= 0.68:
            # Linear map 0.5..0.68 to 0.75..0.6
            return 0.75 - ((d - 0.5) / (0.68 - 0.5)) * 0.15
        else:
            # Linear map 0.68..1.0 to 0.6..0.0
            return 0.60 - ((d - 0.68) / (1.0 - 0.68)) * 0.60

    def get_confidence_label(self, similarity_score: float) -> str:
        """
        Get descriptive label based on match confidence score.
        
        Args:
            similarity_score: Similarity score from 0.0 to 1.0
            
        Returns:
            Human-readable confidence label
        """
        score = similarity_score * 100
        
        if score >= 90:
            return "Strong match"
        elif score >= 75:
            return "Likely same person"
        elif score >= 60:
            return "Uncertain"
        else:
            return "Not a match"

    def verify_face(
        self, 
        reference_image_path: str, 
        live_image_path: str,
        threshold: float = None
    ) -> Tuple[bool, float, str]:
        """
        Verify if two images contain the same person's face.
        
        This is a convenience method that does the full verification in one call.
        
        Args:
            reference_image_path: Path to the reference (profile) image
            live_image_path: Path to the live captured image
            threshold: Match threshold
            
        Returns:
            Tuple of (is_match, similarity_score, message)
        """
        try:
            # Verify using DeepFace's built-in verification
            result = self.deepface.verify(
                img1_path=reference_image_path,
                img2_path=live_image_path,
                model_name="ArcFace",
                detector_backend="opencv",
                distance_metric="cosine",
                enforce_detection=True
            )
            
            # DeepFace returns distance, convert to similarity using informed mapping
            distance = result.get("distance", 1.0)
            similarity_score = self._distance_to_similarity(distance)
            
            label = self.get_confidence_label(similarity_score)
            
            # A "match" is anything 60% or higher
            is_match = similarity_score >= 0.60
            
            message = f"{label} ({round(similarity_score * 100, 1)}%)"
            
            return is_match, round(similarity_score, 4), message
                
        except ValueError as e:
            # Face not detected
            error_msg = str(e).lower()
            if "no face" in error_msg:
                return False, 0.0, "No face detected in image"
            return False, 0.0, f"Verification failed: {str(e)}"
        except Exception as e:
            return False, 0.0, f"Verification error: {str(e)}"
    
    @staticmethod
    def encoding_to_json(encoding: List[float]) -> str:
        """Convert face encoding to JSON string for database storage."""
        return json.dumps(encoding)
    
    @staticmethod
    def encoding_from_json(encoding_json: str) -> List[float]:
        """Parse face encoding from JSON string."""
        return json.loads(encoding_json)


# Singleton instance for reuse
_face_service: Optional[FaceRecognitionService] = None


def get_face_recognition_service() -> FaceRecognitionService:
    """Get singleton face recognition service instance."""
    global _face_service
    if _face_service is None:
        _face_service = FaceRecognitionService()
    return _face_service
