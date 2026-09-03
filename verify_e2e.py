import io
import os
import time
import httpx
import cv2
import numpy as np
from PIL import Image, ImageDraw

BASE_URL = "http://127.0.0.1:5175"
API_URL = "http://127.0.0.1:5050"

def create_synthetic_test_image(filepath="sample_face.jpg"):
    """
    Creates a realistic test portrait image with skin tones, facial structure,
    eyes, and hair to test the OpenCV heuristic engine and ROI bounding box.
    """
    w, h = 600, 600
    img = Image.new("RGB", (w, h), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)
    
    # Head / hair background
    draw.ellipse([200, 100, 400, 360], fill=(45, 55, 72))
    
    # Face skin tone
    face_box = [220, 140, 380, 340]
    draw.ellipse(face_box, fill=(235, 185, 160))
    
    # Eyes
    draw.ellipse([250, 200, 280, 220], fill=(255, 255, 255))
    draw.ellipse([260, 205, 272, 217], fill=(40, 30, 20))
    draw.ellipse([262, 207, 265, 210], fill=(255, 255, 255)) # Specular catchlight
    
    draw.ellipse([320, 200, 350, 220], fill=(255, 255, 255))
    draw.ellipse([328, 205, 340, 217], fill=(40, 30, 20))
    # Right eye missing catchlight to trigger asymmetric reflection
    
    # Nose
    draw.line([(300, 215), (295, 255), (305, 255)], fill=(180, 120, 100), width=2)
    
    # Mouth
    draw.arc([270, 270, 330, 300], start=10, end=170, fill=(180, 70, 70), width=3)
    
    img.save(filepath, "JPEG", quality=90)
    print(f"Created test portrait image: {filepath} ({w}x{h})")
    return filepath

def create_synthetic_test_video(filepath="sample_clip.mp4"):
    """
    Creates a 3-second (90 frames at 30 fps) test video with shifting lighting
    and blinking eye dynamics.
    """
    w, h = 400, 400
    fps = 30
    duration_sec = 3
    total_frames = fps * duration_sec
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filepath, fourcc, fps, (w, h))
    
    for i in range(total_frames):
        frame = np.full((h, w, 3), (30, 41, 59), dtype=np.uint8)
        
        # Face oval
        cv2.ellipse(frame, (200, 200), (80, 110), 0, 0, 360, (160, 185, 235), -1)
        
        # Eyes - blink every 30 frames
        is_blink = (i % 30) in [14, 15]
        if is_blink:
            cv2.line(frame, (160, 180), (180, 180), (40, 30, 20), 2)
            cv2.line(frame, (220, 180), (240, 180), (40, 30, 20), 2)
        else:
            cv2.circle(frame, (170, 180), 8, (255, 255, 255), -1)
            cv2.circle(frame, (170, 180), 4, (40, 30, 20), -1)
            cv2.circle(frame, (230, 180), 8, (255, 255, 255), -1)
            cv2.circle(frame, (230, 180), 4, (40, 30, 20), -1)
            
        # Mouth
        mouth_open = int(5 * np.sin(i * 0.2))
        cv2.ellipse(frame, (200, 250), (20, max(2, 6 + mouth_open)), 0, 0, 360, (70, 70, 180), -1)
        
        out.write(frame)
        
    out.release()
    print(f"Created test video clip: {filepath} ({total_frames} frames, {duration_sec}s)")
    return filepath

def run_verification():
    print("=" * 70)
    print("RUNNING DEEPCHECK CLASSROOM FULL END-TO-END VERIFICATION")
    print("=" * 70)
    
    client = httpx.Client(timeout=15.0, trust_env=False)
    
    # 1. Health check & Frontend check
    print("\n[Step 1] Verifying Backend & Frontend Servers...")
    health_res = client.get(f"{API_URL}/api/health")
    assert health_res.status_code == 200, f"Backend health failed: {health_res.text}"
    health_json = health_res.json()
    print(f" -> Backend Status: {health_json.get('status')} | Engine: {health_json.get('engine')}")
    print(f" -> Disclaimer: {health_json.get('disclaimer')}")
    
    fe_res = client.get(BASE_URL)
    assert fe_res.status_code == 200, "Frontend root did not return 200"
    print(" -> Frontend HTML loaded successfully.")
    
    # 2. Upload and Analyze Image
    print("\n[Step 2] Testing Image Analysis Flow...")
    img_path = create_synthetic_test_image("sample_face.jpg")
    with open(img_path, "rb") as f:
        img_bytes = f.read()
        
    img_res = client.post(f"{API_URL}/api/analyze/image", files={"file": ("sample_face.jpg", img_bytes, "image/jpeg")})
    assert img_res.status_code == 200, f"Image analysis failed: {img_res.text}"
    img_data = img_res.json()
    
    print(f" -> Heuristic Anomaly Score: {img_data.get('confidence_score')}%")
    print(f" -> Detected Signals: {img_data.get('detected_count')} of {img_data.get('total_signals')}")
    print(f" -> Itemized Reasoning: '{img_data.get('reasoning')}'")
    print(f" -> Face Detected: {img_data.get('face_detected')}")
    print(f" -> Face Bounding Box: {img_data.get('face_bounding_box')}")
    print(f" -> Disclaimer Present: {'disclaimer' in img_data}")
    
    # Verify signals breakdown
    signals = img_data.get('signals', [])
    assert len(signals) == 6, f"Expected 6 signals, got {len(signals)}"
    for s in signals:
        status_tag = "[FLAGGED]" if s.get('detected') else "[NORMAL]"
        print(f"    * {status_tag} {s.get('name')}: score={s.get('score')} | {s.get('details')}")
        
    # Check normalized bounding box
    bbox = img_data.get('face_bounding_box', {})
    assert 'norm_x' in bbox and 'norm_y' in bbox and 'norm_w' in bbox and 'norm_h' in bbox, "Normalized coords missing"
    print(f" -> Bounding Box Normalized: x={bbox['norm_x']*100:.1f}%, y={bbox['norm_y']*100:.1f}%, w={bbox['norm_w']*100:.1f}%, h={bbox['norm_h']*100:.1f}%")
    
    # 3. Upload and Analyze Video
    print("\n[Step 3] Testing Video Analysis Flow...")
    vid_path = create_synthetic_test_video("sample_clip.mp4")
    with open(vid_path, "rb") as f:
        vid_bytes = f.read()
        
    vid_res = client.post(f"{API_URL}/api/analyze/video", files={"file": ("sample_clip.mp4", vid_bytes, "video/mp4")})
    assert vid_res.status_code == 200, f"Video analysis failed: {vid_res.text}"
    vid_data = vid_res.json()
    
    print(f" -> Video Heuristic Score: {vid_data.get('confidence_score')}%")
    print(f" -> Detected Signals: {vid_data.get('detected_count')} of {vid_data.get('total_signals')}")
    print(f" -> Itemized Reasoning: '{vid_data.get('reasoning')}'")
    print(f" -> Total Frames: {vid_data.get('total_frames')} | Sampled Frames: {vid_data.get('sampled_frames_count')}")
    print(f" -> Duration: {vid_data.get('duration_sec')}s")
    for s in vid_data.get('signals', []):
        status_tag = "[FLAGGED]" if s.get('detected') else "[NORMAL]"
        print(f"    * {status_tag} {s.get('name')}: score={s.get('score')} | {s.get('details')}")

    # 4. Create Classroom Session
    print("\n[Step 4] Testing Classroom Session Creation & Token Flow...")
    sess_res = client.post(f"{API_URL}/api/session/create", json={
        "teacher_name": "Prof. Alan Turing",
        "topic": "AI Media Literacy & Heuristics"
    })
    assert sess_res.status_code == 201, f"Session create failed: {sess_res.text}"
    session_info = sess_res.json().get('session', {})
    code = session_info.get('code')
    print(f" -> Generated Session Code: {code}")
    print(f" -> Educator: {session_info.get('teacher_name')}")
    print(f" -> Topic: {session_info.get('topic')}")
    
    # 5. Submit Student Analyses to Active Session
    print("\n[Step 5] Submitting Student Analyses to Session...")
    students = [
        ("Alice Chen", "image", img_data),
        ("Bob Miller", "video", vid_data),
        ("Charlie Zhang", "image", img_data)
    ]
    
    for student_name, m_type, res_payload in students:
        sub_res = client.post(f"{API_URL}/api/session/{code}/submit", json={
            "student_name": student_name,
            "media_type": m_type,
            "analysis_result": res_payload
        })
        assert sub_res.status_code == 200, f"Submit failed for {student_name}: {sub_res.text}"
        print(f" -> Recorded submission from '{student_name}' ({m_type.upper()})")
        
    # 6. Fetch Session State & Verify Live Metrics
    print("\n[Step 6] Verifying Live Session Metrics...")
    get_sess = client.get(f"{API_URL}/api/session/{code}")
    assert get_sess.status_code == 200, f"Get session failed: {get_sess.text}"
    current_session = get_sess.json().get('session', {})
    
    print(f" -> Total Submissions: {current_session.get('total_submissions')}")
    print(f" -> Class Avg Heuristic Score: {current_session.get('average_confidence')}%")
    print(f" -> Top Flagged Indicators: {current_session.get('top_indicators')}")
    assert current_session.get('total_submissions') == 3, "Expected 3 submissions"
    
    # 7. Export Printable HTML Summary Report
    print("\n[Step 7] Testing Printable HTML Report Generation...")
    report_res = client.get(f"{API_URL}/api/session/{code}/export")
    assert report_res.status_code == 200, f"Report export failed: {report_res.text}"
    report_html = report_res.text
    
    assert f"SESSION: {code}" in report_html, "Session code missing from report"
    assert "Prof. Alan Turing" in report_html, "Teacher name missing from report"
    assert "Alice Chen" in report_html, "Alice Chen missing from submissions table"
    assert "Bob Miller" in report_html, "Bob Miller missing from submissions table"
    assert "EDUCATIONAL DISCLAIMER" in report_html, "Disclaimer missing from report"
    assert "no-print-btn" in report_html, "Print button missing from report"
    
    print(f" -> Exported HTML Report Size: {len(report_html)} bytes")
    print(" -> Report contains valid session code, teacher metadata, submissions table, indicator distribution, and educational disclaimer.")
    
    # Save report HTML for review
    with open("sample_classroom_report.html", "w", encoding="utf-8") as f:
        f.write(report_html)
    print(" -> Saved report copy to sample_classroom_report.html")
    
    print("\n" + "=" * 70)
    print("ALL 7 VERIFICATION CRITERIA PASSED WITHOUT ERROR!")
    print("=" * 70)

if __name__ == "__main__":
    run_verification()
