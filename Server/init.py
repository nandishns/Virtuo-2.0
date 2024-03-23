import cv2
import mediapipe as mp
import math
import time

# Initialize MediaPipe Pose model
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

def detect_jump(prev_y, curr_y):
    jump_threshold = 50  # Threshold for jump detection
    return (curr_y - prev_y > jump_threshold)

def calculate_angle(a, b, c):
    ba = [a[0] - b[0], a[1] - b[1]]
    bc = [c[0] - b[0], c[1] - b[1]]
    dot_product = ba[0] * bc[0] + ba[1] * bc[1]
    magnitude_ba = math.sqrt(ba[0]**2 + ba[1]**2)
    magnitude_bc = math.sqrt(bc[0]**2 + bc[1]**2)
    angle_rad = math.acos(dot_product / (magnitude_ba * magnitude_bc))
    return math.degrees(angle_rad)

def detect_hands_raised(landmarks):
    # Get landmark indices for shoulder, elbow, and torso
    shoulder_idx = [11, 12]  # Right and left shoulder
    elbow_idx = [13, 14]  # Right and left elbow
    torso_idx = [23, 24]  # Right and left hip

    # Get landmark coordinates
    shoulder_points = [(landmarks[idx].x, landmarks[idx].y) for idx in shoulder_idx]
    elbow_points = [(landmarks[idx].x, landmarks[idx].y) for idx in elbow_idx]
    torso_points = [(landmarks[idx].x, landmarks[idx].y) for idx in torso_idx]

    # Calculate angles between shoulders, elbows, and torso
    angles = [calculate_angle(shoulder_points[i], elbow_points[i], torso_points[i]) for i in range(len(shoulder_points))]

    # Check if both angles are approximately 90 degrees
    if(all(abs(angle - 90) < 20 for angle in angles)):
        return True
    # elif(all(abs(angle) < 15 for angle in angles)):
    return False

def detect_single_hand_raised(landmarks):
    # Get landmark indices for shoulder, elbow, and hip of both hands
    right_shoulder_idx = 12  # Right shoulder
    right_elbow_idx = 14  # Right elbow
    right_hip_idx = 24  # Right hip

    left_shoulder_idx = 11  # Left shoulder
    left_elbow_idx = 13  # Left elbow
    left_hip_idx = 23  # Left hip

    # Get landmark coordinates for the right hand
    right_shoulder_point = (landmarks[right_shoulder_idx].x, landmarks[right_shoulder_idx].y)
    right_elbow_point = (landmarks[right_elbow_idx].x, landmarks[right_elbow_idx].y)
    right_hip_point = (landmarks[right_hip_idx].x, landmarks[right_hip_idx].y)

    # Calculate angle between right shoulder, elbow, and hip
    right_angle = calculate_angle(right_shoulder_point, right_elbow_point, right_hip_point)

    # Get landmark coordinates for the left hand
    left_shoulder_point = (landmarks[left_shoulder_idx].x, landmarks[left_shoulder_idx].y)
    left_elbow_point = (landmarks[left_elbow_idx].x, landmarks[left_elbow_idx].y)
    left_hip_point = (landmarks[left_hip_idx].x, landmarks[left_hip_idx].y)

    # Calculate angle between left shoulder, elbow, and hip
    left_angle = calculate_angle(left_shoulder_point, left_elbow_point, left_hip_point)

    # Check if only one hand is raised
    if abs(right_angle - 90) < 15 and abs(left_angle - 90) >= 15:
        return 'right'
    elif abs(left_angle - 90) < 15 and abs(right_angle - 90) >= 15:
        return 'left'
    else:
        return None

def main():
    # Initialize MediaPipe Pose model
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)

    # Initialize variables
    prev_head_y = 0
    jump_detected = False
    game = False

    # Open default camera
    cap = cv2.VideoCapture(0)
    start_time = None
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Perform pose detection
        results = pose.process(frame_rgb)

        # Extract key points if pose is detected
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            head_landmark = landmarks[mp_pose.PoseLandmark.NOSE]

            # Get current head y-coordinate
            curr_head_y = int(head_landmark.y * frame.shape[0])

            if start_time is None or time.time() - start_time > 2:
                if game and detect_jump(prev_head_y, curr_head_y) and not jump_detected :
                    print("Jump detected!")
                    start_time = time.time()
                    continue
                hands_raised = detect_hands_raised(landmarks)
                if hands_raised :
                    print("Hands raised to the side!")
                    start_time = time.time()
                    if game:
                        game = False
                    else:
                        game = True
                    print("game :",game) 
                    continue
                hand_raised = detect_single_hand_raised(landmarks)
                if game and hand_raised:
                    print(f"{hand_raised.capitalize()} hand raised!")
                    start_time = time.time() 
            
            # Update previous head y-coordinate
            prev_head_y = curr_head_y

        # Display frame
        cv2.imshow("Pose Detection", frame)

        # Break loop if 'q' is pressed
        cv2.waitKey(100)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release video capture and destroy windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()