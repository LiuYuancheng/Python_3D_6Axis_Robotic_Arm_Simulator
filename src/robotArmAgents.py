#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmAgents.py
#
# Purpose:     This module is the agent module to define the object used by the 
#              robot arm simulator.
#
# Author:      Yuancheng Liu
#
# Created:     2026/01/19
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import math

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class Cube(object):
    def __init__(self, x, y, z, size=0.3):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.original_pos = [x, y, z]
    
    def reset(self):
        self.x, self.y, self.z = self.original_pos
    
    def getPosition(self):
        return [self.x, self.y, self.z]
    
    def setPosition(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class RobotArm(object):
    def __init__(self):
        # Define all the public variables:
        # Link lengths
        self.l1 = 2.0  # Base to shoulder
        self.l2 = 1.5  # Shoulder to elbow
        self.l3 = 1.0  # Elbow to wrist
        self.l4 = 0.5  # Wrist to gripper
        # Joint angles (in degrees)
        self.theta1 = 45.0   # Base rotation
        self.theta2 = -15.0  # Shoulder
        self.theta3 = 30.0  # Elbow
        self.theta4 = 0.0   # Wrist
        self.theta5 = 0.0   # Gripper rotation
        self.gripper_open = 50.0  # Gripper opening (0-100)
        # Gripper state
        self.gripper_closed = False
        self.holding_cube = False
    
    #-----------------------------------------------------------------------------
    def forwardKinematics(self):
        """Calculate the position of each joint"""
        t1 = math.radians(self.theta1)  # Negate for correct rotation direction
        t2 = math.radians(self.theta2)
        t3 = math.radians(self.theta3)
        t4 = math.radians(self.theta4)
        # Base pos
        p0 = [0, 0, 0]
        # Joint 1
        p1 = [0, 0, self.l1]
        # Joint 2 (shoulder) - fixed rotation
        x2 = self.l2 * math.cos(-t1) * math.cos(t2)
        y2 = self.l2 * math.sin(-t1) * math.cos(t2)
        z2 = self.l1 + self.l2 * math.sin(t2)
        p2 = [x2, -y2, z2]
        # Joint 3 (elbow)
        angle_sum_23 = t2 + t3
        x3 = math.cos(t1) * (self.l2 * math.cos(t2) + self.l3 * math.cos(angle_sum_23))
        y3 = math.sin(t1) * (self.l2 * math.cos(t2) + self.l3 * math.cos(angle_sum_23))
        z3 = self.l1 + self.l2 * math.sin(t2) + self.l3 * math.sin(angle_sum_23)
        p3 = [x3, y3, z3]
        # End effector (gripper position)
        angle_sum_234 = t2 + t3 + t4
        x4 = math.cos(t1) * (self.l2 * math.cos(t2) + self.l3 * math.cos(angle_sum_23) + self.l4 * math.cos(angle_sum_234))
        y4 = math.sin(t1) * (self.l2 * math.cos(t2) + self.l3 * math.cos(angle_sum_23) + self.l4 * math.cos(angle_sum_234))
        z4 = self.l1 + self.l2 * math.sin(t2) + self.l3 * math.sin(angle_sum_23) + self.l4 * math.sin(angle_sum_234)
        p4 = [x4, y4, z4]    
        return [p0, p1, p2, p3, p4]
    
    #-----------------------------------------------------------------------------
    def getGripperOrientation(self):
        """Get the orientation angles for the gripper"""
        # Gripper always points down, so we set pitch to -90 degrees
        pitch = 180  # make the gripper always point down
        yaw = self.theta1  # Yaw angle (base rotation)
        roll = self.theta5  # Roll angle for gripper rotation
        return yaw, pitch, roll