import numpy as np
from itertools import product

def getRobotJointAngles(x, y, resolution=0.5):
    """
    Compute robot arm joint angles (theta1, theta2, theta3) for a target (x, y) position.
    
    Arm segments:
        a = sin(90 - theta1) * 1.5         (shoulder, length 1.5)
        b = sin(90 - theta1 - theta2) * 1  (elbow, length 1.0)
        c = sin(90 - theta1 - theta2 - theta3) * 0.5  (wrist, length 0.5)
        distance = a + b + c
    
    Args:
        x          : Target x coordinate
        y          : Target y coordinate
        resolution : Angle search step in degrees (smaller = more accurate, slower)
    
    Returns:
        Best (theta1, theta2, theta3) tuple in degrees, or None if unreachable
    """
    target_distance = np.sqrt(x**2 + y**2)

    theta1_range = np.arange(-80, 80 + resolution, resolution)
    theta2_range = np.arange(-180, 180 + resolution, resolution)
    theta3_range = np.arange(-90, 90 + resolution, resolution)

    best_solution = None
    best_error = 0.04

    for t1, t2, t3 in product(theta1_range, theta2_range, theta3_range):
        t1_r = np.radians(t1)
        t2_r = np.radians(t2)
        t3_r = np.radians(t3)

        a = np.sin(np.pi/2 - t1_r) * 1.5
        b = np.sin(np.pi/2 - t1_r - t2_r) * 1.0
        c = np.sin(np.pi/2 - t1_r - t2_r - t3_r) * 0.5

        computed_distance = a + b + c
        error = abs(computed_distance - target_distance)

        if error < best_error:
            best_error = error
            best_solution = (round(t1, 2), round(t2, 2), round(t3, 2))

        if error < 0.01:  # Early exit if close enough
            break

    print(f"Target distance : {target_distance:.4f}")
    print(f"Best match error: {best_error:.4f}")
    print(f"Angles => theta1: {best_solution[0]}°, theta2: {best_solution[1]}°, theta3: {best_solution[2]}°")

    return best_solution

# --- Example usage ---
if __name__ == "__main__":
    x, y = 1.5, -1.31
    angles = getRobotJointAngles(x, y, resolution=5)