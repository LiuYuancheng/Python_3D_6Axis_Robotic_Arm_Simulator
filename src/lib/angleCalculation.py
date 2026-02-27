import numpy as np
from scipy.optimize import fsolve

def solve_robot_arm(x, y, initial_guess=None):
    """
    Solve inverse kinematics for a 3-DOF robot arm.
    
    Args:
        x: Target x-coordinate of the cube
        y: Target y-coordinate of the cube
        initial_guess: Optional initial guess for [theta1, theta2, theta3] in radians
    
    Returns:
        dict with theta1, theta2, theta3 in both radians and degrees,
        plus verification metrics
    """
    
    # Calculate target distance and z-height
    distance = np.sqrt(x**2 + y**2)
    z_target = 2.0  # Fixed z-axis constraint

    # Link lengths
    L1, L2, L3 = 1.5, 1.0, 0.5

    def equations(angles):
        t1, t2, t3 = angles

        # Cumulative angles
        a12  = t1 + t2
        a123 = t1 + t2 + t3

        # Ground projections (x-axis)
        a = np.cos(t1)  * L1
        b = np.cos(a12) * L2
        c = np.cos(a123)* L3

        # Z-axis projections
        d = np.sin(t1)  * L1
        e = np.sin(a12) * L2
        f = np.sin(a123)* L3

        eq1 = (a + b + c) - distance   # X-axis constraint
        eq2 = (d + e + f) - z_target   # Z-axis constraint
        eq3 = a123                     # Wrist flat constraint (sum = 0 keeps wrist level)

        return [eq1, eq2, eq3]

    # Default initial guess if none provided
    if initial_guess is None:
        initial_guess = [np.pi/4, -np.pi/4, 0.0]

    # Solve the system
    solution, info, ier, msg = fsolve(equations, initial_guess, full_output=True)
    
    if ier != 1:
        print(f"Warning: Solver did not fully converge — {msg}")

    t1, t2, t3 = solution

    # Verify solution
    a12  = t1 + t2
    a123 = t1 + t2 + t3
    computed_distance = np.cos(t1)*L1 + np.cos(a12)*L2 + np.cos(a123)*L3
    computed_z       = np.sin(t1)*L1 + np.sin(a12)*L2 + np.sin(a123)*L3

    return {
        "theta1_rad": t1,          "theta1_deg": np.degrees(t1),
        "theta2_rad": t2,          "theta2_deg": np.degrees(t2),
        "theta3_rad": t3,          "theta3_deg": np.degrees(t3),
        "target_distance": distance,
        "computed_distance": computed_distance,
        "target_z": z_target,
        "computed_z": computed_z,
        "distance_error": abs(computed_distance - distance),
        "z_error": abs(computed_z - z_target),
    }


# ── Example usage ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [(2.0, 1.0), (1.5, 0.5), (2.5, 1.5)]

    for x, y in test_cases:
        print(f"\nInput  →  x={x}, y={y}")
        result = solve_robot_arm(x, y)
        print(f"  θ₁ = {result['theta1_deg']:+.2f}°")
        print(f"  θ₂ = {result['theta2_deg']:+.2f}°")
        print(f"  θ₃ = {result['theta3_deg']:+.2f}°")
        print(f"  Distance  : target={result['target_distance']:.4f}  computed={result['computed_distance']:.4f}  err={result['distance_error']:.2e}")
        print(f"  Z-height  : target={result['target_z']:.4f}        computed={result['computed_z']:.4f}        err={result['z_error']:.2e}")