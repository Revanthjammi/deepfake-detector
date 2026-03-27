"""
Video processing utilities
"""

import cv2
import os
import tempfile


def validate_video(video_path):
    """Validate video file"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False, "Cannot open video file"
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        return True, {
            'fps': fps,
            'frame_count': frame_count,
            'duration_seconds': duration
        }
        
    except Exception as e:
        return False, f"Invalid video: {str(e)}"


def get_video_info(video_path):
    """Get video information"""
    try:
        cap = cv2.VideoCapture(video_path)
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        cap.release()
        
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'duration_seconds': frame_count / fps if fps > 0 else 0,
            'size_mb': os.path.getsize(video_path) / (1024 * 1024)
        }
        
    except Exception as e:
        return None


def extract_thumbnail(video_path, frame_number=0):
    """Extract thumbnail from video"""
    try:
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
        
    except Exception as e:
        return None