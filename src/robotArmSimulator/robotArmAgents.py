#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmAgents.py
#
# Purpose:     This module incudes all the agent classes to define the visible 
#              object (Cube, RobotArm, Env) shown in the robot arm simulator.
#
# Author:      Yuancheng Liu
#
# Created:     2026/01/19
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import math
import wx
import wx.glcanvas as glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import robotArmGlobal as gv

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class Cube(object):
    """ The small cube object for the robot arm to grab."""
    def __init__(self, x, y, z, size=0.3):
        """  self.cube =agents.Cube(2.0, 1.0, 0.3) 
        Args:
            x (float): Cube init position x coordinate.
            y (float): Cube init position y coordinate.
            z (float): Cube init position z coordinate.
            size (float, optional): size. Defaults to 0.3.
        """
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
    """ Robot arm agent object."""
    def __init__(self):
        # Define all the public variables:
        # Link lengths
        self.l1 = gv.gArmBaseLen # Base to shoulder
        self.l2 = gv.gArmShoulderLen  # Shoulder to elbow
        self.l3 = gv.gArmElbowLen  # Elbow to wrist
        self.l4 = gv.gArmWristLen  # Wrist to gripper
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
    
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class GLCanvas(glcanvas.GLCanvas):
    """ The sense and canvas of the robot arm and cube."""
    def __init__(self, parent, robot, cube):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.context = glcanvas.GLContext(self)
        self.robot = robot
        self.cube = cube
        self.init = False
        self.rotation_x = -50
        self.rotation_y = -80
        self.distance = 10 # cam distance to the origin (0, 0)
        self.last_x = 0
        self.last_y = 0
        # bind the mouse event.
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        gv.gDebugPrint("The Robot Arm Simulator Canvas is created.", logType=gv.LOG_INFO)
    
    #-----------------------------------------------------------------------------
    def InitGL(self):
        """ Init the openGL scene."""
        self.SetCurrent(self.context)
        #glClearColor(0.95, 0.95, 0.95, 1.0)
        glClearColor(gv.gCanvasBgColor[0], gv.gCanvasBgColor[1], gv.gCanvasBgColor[2], gv.gCanvasBgColor[3])
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        # Light position
        glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 10, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
        self.init = True
    
    #-----------------------------------------------------------------------------
    def OnPaint(self, event):
        if not self.init: self.InitGL()
        self.SetCurrent(self.context)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width, height = self.GetSize()
        gluPerspective(45, width / height, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, self.distance, 0, 0, 0, 0, 1, 0)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 0, 1)
        self.DrawScene()
        self.SwapBuffers()
    
    #-----------------------------------------------------------------------------
    def DrawScene(self):
        # Draw grid
        self.DrawGrid()
        # Draw cube
        self.DrawCube()
        # Draw robot arm
        positions = self.robot.forwardKinematics()
        # Draw base area identify the max range the robot can reach
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)
        glTranslatef(0, 0, 0)
        self.DrawCylinder(1, 0.05)
        glPopMatrix()
        # Draw arm segments
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)]
        for i in range(len(positions) - 1):
            p1 = positions[i]
            p2 = positions[i + 1]
            glColor3f(*colors[i])
            self.DrawSegment(p1, p2, 0.1)
            # Draw joint sphere
            glPushMatrix()
            glTranslatef(*p2)
            self.DrawSphere(0.15)
            glPopMatrix()
        # Draw gripper
        self.DrawGripper(positions[-1])
    
    #-----------------------------------------------------------------------------
    def DrawGrid(self):
        """Draw the ground grid."""
        glDisable(GL_LIGHTING)
        glColor3f(0.7, 0.7, 0.7)
        glBegin(GL_LINES)
        for i in range(-5, 6):
            glVertex3f(i, -5, 0)
            glVertex3f(i, 5, 0)
            glVertex3f(-5, i, 0)
            glVertex3f(5, i, 0)
        glEnd()
        # Draw coordinate markers at grid intersections
        glPointSize(5)
        glBegin(GL_POINTS)
        glColor3f(0.5, 0.5, 0.5)
        for x in range(-5, 6, 2):
            for y in range(-5, 6, 2):
                if x == 0 and y == 0:
                    glColor3f(0.0, 0.0, 0.0)  # Black for origin
                    glVertex3f(x, y, 0.02)
                    glColor3f(0.5, 0.5, 0.5)
                else:
                    glVertex3f(x, y, 0.02)
        glEnd()
        glPointSize(1)
        
        # Draw small coordinate markers with lines
        # for x in range(-5, 6, 2):
        #     for y in range(-5, 6, 2):
        #         # Draw a small cross at each major grid intersection
        #         glBegin(GL_LINES)
        #         if x == 0 and y == 0:
        #             glColor3f(0.0, 0.0, 0.0)
        #         else:
        #             glColor3f(0.4, 0.4, 0.4)
                
        #         # Horizontal line of cross
        #         glVertex3f(x - 0.1, y, 0.02)
        #         glVertex3f(x + 0.1, y, 0.02)
        #         # Vertical line of cross
        #         glVertex3f(x, y - 0.1, 0.02)
        #         glVertex3f(x, y + 0.1, 0.02)
        #         glEnd()

        # Draw axes
        glLineWidth(5)
        glBegin(GL_LINES)
        # X axis - red
        glColor3f(1, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(2, 0, 0)
        # Y axis - green
        glColor3f(0, 1, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 2, 0)
        # Z axis - blue
        glColor3f(0, 0, 1)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 2)
        glEnd()
        glLineWidth(1)
        glEnable(GL_LIGHTING)
    
    #-----------------------------------------------------------------------------
    def DrawCube(self):
        glPushMatrix()
        glTranslatef(self.cube.x, self.cube.y, self.cube.z)
        # Different color based on whether it's being held
        if self.robot.holding_cube:
            glColor3f(1.0, 0.5, 0.0)  # Orange when held
        else:
            glColor3f(1.0, 0.8, 0.0)  # Yellow when free
        s = self.cube.size / 2
        # Draw cube 6 faces
        glBegin(GL_QUADS)
        # Front face
        glNormal3f(0, 0, 1)
        glVertex3f(-s, -s, s)
        glVertex3f(s, -s, s)
        glVertex3f(s, s, s)
        glVertex3f(-s, s, s)
        # Back face
        glNormal3f(0, 0, -1)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, -s, -s)
        # Top face
        glNormal3f(0, 1, 0)
        glVertex3f(-s, s, -s)
        glVertex3f(-s, s, s)
        glVertex3f(s, s, s)
        glVertex3f(s, s, -s)
        # Bottom face
        glNormal3f(0, -1, 0)
        glVertex3f(-s, -s, -s)
        glVertex3f(s, -s, -s)
        glVertex3f(s, -s, s)
        glVertex3f(-s, -s, s)
        # Right face
        glNormal3f(1, 0, 0)
        glVertex3f(s, -s, -s)
        glVertex3f(s, s, -s)
        glVertex3f(s, s, s)
        glVertex3f(s, -s, s)
        # Left face
        glNormal3f(-1, 0, 0)
        glVertex3f(-s, -s, -s)
        glVertex3f(-s, -s, s)
        glVertex3f(-s, s, s)
        glVertex3f(-s, s, -s)
        glEnd()
        glPopMatrix()
    
    #-----------------------------------------------------------------------------
    def DrawGripper(self, position):
        glPushMatrix()
        glTranslatef(*position)
        # Get gripper orientation
        yaw, pitch, roll = self.robot.getGripperOrientation()
        print((yaw, pitch, roll))
        glRotatef(yaw, 0, 0, 1)
        glRotatef(pitch, 0, 1, 0)
        glRotatef(roll, 0, 0, 1)  # Add roll rotation
        # Draw gripper base
        glColor3f(0.3, 0.3, 0.3)
        self.DrawCylinder(0.08, 0.15)
        # Calculate gripper finger opening
        opening = self.robot.gripper_open / 100.0 * 0.2  # Max 0.2 units
        # Draw gripper fingers
        glColor3f(0.2, 0.2, 0.2)
        # Left finger
        glPushMatrix()
        glTranslatef(-opening, 0, 0.15)
        glScalef(0.03, 0.03, 0.2)
        self.DrawBox()
        glPopMatrix()
        # Right finger
        glPushMatrix()
        glTranslatef(opening, 0, 0.15)
        glScalef(0.03, 0.03, 0.2)
        self.DrawBox()
        glPopMatrix()
        # Draw gripper palm to the main scene
        glPopMatrix()
    
    #-----------------------------------------------------------------------------
    def DrawBox(self):
        glBegin(GL_QUADS)
        # Front
        glNormal3f(0, 0, 1)
        glVertex3f(-1, -1, 1)
        glVertex3f(1, -1, 1)
        glVertex3f(1, 1, 1)
        glVertex3f(-1, 1, 1)
        # Back
        glNormal3f(0, 0, -1)
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, 1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, -1, -1)
        # Top
        glNormal3f(0, 1, 0)
        glVertex3f(-1, 1, -1)
        glVertex3f(-1, 1, 1)
        glVertex3f(1, 1, 1)
        glVertex3f(1, 1, -1)
        # Bottom
        glNormal3f(0, -1, 0)
        glVertex3f(-1, -1, -1)
        glVertex3f(1, -1, -1)
        glVertex3f(1, -1, 1)
        glVertex3f(-1, -1, 1)
        # Right
        glNormal3f(1, 0, 0)
        glVertex3f(1, -1, -1)
        glVertex3f(1, 1, -1)
        glVertex3f(1, 1, 1)
        glVertex3f(1, -1, 1)
        # Left
        glNormal3f(-1, 0, 0)
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, -1, 1)
        glVertex3f(-1, 1, 1)
        glVertex3f(-1, 1, -1)
        glEnd()
    
    #-----------------------------------------------------------------------------
    def DrawSegment(self, p1, p2, radius):
        """Draw the arm segment"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dz = p2[2] - p1[2]
        length = math.sqrt(dx**2 + dy**2 + dz**2)
        glPushMatrix()
        glTranslatef(*p1)
        if length > 0:
            ax = math.degrees(math.atan2(dy, dx))
            ay = math.degrees(math.acos(dz / length))
            glRotatef(ax, 0, 0, 1)
            glRotatef(ay, 0, 1, 0)
        self.DrawCylinder(radius, length)
        glPopMatrix()
    
    #-----------------------------------------------------------------------------
    def DrawCylinder(self, radius, height):
        quad = gluNewQuadric()
        gluCylinder(quad, radius, radius, height, 20, 1)
        gluDeleteQuadric(quad)
    
    #-----------------------------------------------------------------------------
    def DrawSphere(self, radius):
        quad = gluNewQuadric()
        gluSphere(quad, radius, 20, 20)
        gluDeleteQuadric(quad)
    
    #-----------------------------------------------------------------------------
    def OnSize(self, event):
        self.Refresh()
    
    def OnMouseDown(self, event):
        self.last_x, self.last_y = event.GetPosition()
    
    def OnMouseMotion(self, event):
        if event.Dragging() and event.LeftIsDown():
            x, y = event.GetPosition()
            dx = x - self.last_x
            dy = y - self.last_y
            self.rotation_y += dx
            self.rotation_x += dy
            self.last_x = x
            self.last_y = y
            self.Refresh()
    
    def OnMouseWheel(self, event):
        delta = event.GetWheelRotation()
        self.distance -= delta / 120.0
        self.distance = max(3, min(20, self.distance))
        self.Refresh()

    #-----------------------------------------------------------------------------
    def updateCubeZ(self):
        """ Update the cube Z position to simulate the gravity effect."""
        if self.cube.z > self.cube.size/2: 
            self.cube.z -= 0.1
        elif self.cube.z < self.cube.size/2:
            self.cube.z =self.cube.size/2