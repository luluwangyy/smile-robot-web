# keyframe/config.py

SERVO_PAIRS = {
    1: 8,  # back right
    3: 5,  # front right
    6: 7,  # back left
    4: 2   # front left
}

ALL_SERVOS = list(range(1, 11))
CENTER_ANGLE = 120
REVERSED = [3, 4, 7, 8, 1, 6]  # front legs & hips flipped
