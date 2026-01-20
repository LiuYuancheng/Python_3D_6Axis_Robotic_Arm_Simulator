#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmSimulator.py
#
# Purpose:     This module is a simple simulator for a robotic arm by using the 
#              wxPython and OpenGL library.
#
# Author:      Yuancheng Liu
#
# Created:     2026/01/20
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import time 
import math
import numpy as np

import wx
import wx.glcanvas as glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *


class RobotArm:
    def __init__(self):
        # Link lengths
        self.l1 = 2.0  # Base to shoulder
        self.l2 = 1.5  # Shoulder to elbow
        self.l3 = 1.0  # Elbow to wrist
        self.l4 = 0.5  # Wrist to gripper
        
        # Joint angles (in degrees)
        self.theta1 = 45.0   # Base rotation
        self.theta2 = 45.0  # Shoulder
        self.theta3 = 30.0  # Elbow
        self.theta4 = 0.0   # Wrist
        self.theta5 = 0.0   # Gripper rotation
        self.gripper_open = 50.0  # Gripper opening (0-100)
        
        # Gripper state
        self.gripper_closed = False
        self.holding_cube = False
    
    def forward_kinematics(self):
        """Calculate the position of each joint"""
        t1 = math.radians(self.theta1)  # Negate for correct rotation direction
        t2 = math.radians(self.theta2)
        t3 = math.radians(self.theta3)
        t4 = math.radians(self.theta4)
        
        # Base
        p0 = [0, 0, 0]
        
        # Joint 1
        p1 = [0, 0, self.l1]
        
        # Joint 2 (shoulder) - fixed rotation
        x2 = self.l2 * math.cos(-t1) * math.cos(t2)
        y2 = self.l2 * math.sin(-t1) * math.cos(t2)
        z2 = self.l1 + self.l2 * math.sin(t2)
        p2 = [x2, -y2, z2]
        #p2 = [1, 1, 1]
        
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
    
    def get_gripper_orientation(self):
        """Get the orientation angles for the gripper"""
        t1 = math.radians(self.theta1)  # Negated for correct rotation
        t2 = math.radians(self.theta2)
        t3 = math.radians(self.theta3)
        t4 = math.radians(self.theta4)
        
        # Calculate gripper orientation
        pitch = math.degrees(t2 + t3 + t4)  # Pitch angle
        yaw = self.theta1  # Yaw angle (already correct now)
        roll = self.theta5  # Roll angle for gripper rotation
        
        return yaw, pitch, roll


class Cube:
    def __init__(self, x, y, z, size=0.3):
        self.x = x
        self.y = y
        self.z = z
        self.size = size
        self.original_pos = [x, y, z]
    
    def reset(self):
        self.x, self.y, self.z = self.original_pos
    
    def get_position(self):
        return [self.x, self.y, self.z]
    
    def set_position(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


class GLCanvas(glcanvas.GLCanvas):
    def __init__(self, parent, robot, cube):
        glcanvas.GLCanvas.__init__(self, parent, -1)
        self.context = glcanvas.GLContext(self)
        self.robot = robot
        self.cube = cube
        self.init = False
        self.rotation_x = 20
        self.rotation_y = 45
        self.distance = 10
        self.last_x = 0
        self.last_y = 0
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
    
    def InitGL(self):
        self.SetCurrent(self.context)
        glClearColor(0.95, 0.95, 0.95, 1.0)
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
    
    def OnPaint(self, event):
        if not self.init:
            self.InitGL()
        
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
    
    def DrawScene(self):
        # Draw grid
        self.DrawGrid()
        
        # Draw cube
        self.DrawCube()
        
        # Draw robot arm
        positions = self.robot.forward_kinematics()
        
        # Draw base
        glPushMatrix()
        glColor3f(0.5, 0.5, 0.5)
        glTranslatef(0, 0, 0)
        self.DrawCylinder(1, 0.1)
        glPopMatrix()
        
        # Draw arm segments
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 0)]
        
        for i in range(len(positions) - 1):
            p1 = positions[i]
            p2 = positions[i + 1]
            
            glColor3f(*colors[i])
            self.DrawSegment(p1, p2, 0.1)
            #print(p2)
            
            # Draw joint sphere
            glPushMatrix()
            glTranslatef(*p2)
            self.DrawSphere(0.15)
            glPopMatrix()
        

        #self.DrawSegment([1,1,1], [2,2,2], 0.1)

        # Draw gripper
        self.DrawGripper(positions[-1])
    
    def DrawGrid(self):
        glDisable(GL_LIGHTING)
        glColor3f(0.7, 0.7, 0.7)
        glBegin(GL_LINES)
        for i in range(-5, 6):
            glVertex3f(i, -5, 0)
            glVertex3f(i, 5, 0)
            glVertex3f(-5, i, 0)
            glVertex3f(5, i, 0)
        glEnd()
        
        # Draw coordinate labels at grid intersections
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
        for x in range(-5, 6, 2):
            for y in range(-5, 6, 2):
                # Draw a small cross at each major grid intersection
                glBegin(GL_LINES)
                if x == 0 and y == 0:
                    glColor3f(0.0, 0.0, 0.0)
                else:
                    glColor3f(0.4, 0.4, 0.4)
                
                # Horizontal line of cross
                glVertex3f(x - 0.1, y, 0.02)
                glVertex3f(x + 0.1, y, 0.02)
                # Vertical line of cross
                glVertex3f(x, y - 0.1, 0.02)
                glVertex3f(x, y + 0.1, 0.02)
                glEnd()


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
    
    def updateCubeZ(self):
        if self.cube.z > self.cube.size/2: 
            self.cube.z -= 0.1
        elif self.cube.z < self.cube.size/2:
            self.cube.z =self.cube.size/2


    def DrawCube(self):
        glPushMatrix()
        glTranslatef(self.cube.x, self.cube.y, self.cube.z)
        
        # Different color based on whether it's being held
        if self.robot.holding_cube:
            glColor3f(1.0, 0.5, 0.0)  # Orange when held
        else:
            glColor3f(1.0, 0.8, 0.0)  # Yellow when free
        
        s = self.cube.size / 2
        
        # Draw cube
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
    
    def DrawGripper(self, position):
        glPushMatrix()
        glTranslatef(*position)
        
        # Get gripper orientation
        yaw, pitch, roll = self.robot.get_gripper_orientation()
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
        
        glPopMatrix()
    
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
    

    def DrawSegment(self, p1, p2, radius):


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
    
    def DrawCylinder(self, radius, height):
        quad = gluNewQuadric()
        gluCylinder(quad, radius, radius, height, 20, 1)
        gluDeleteQuadric(quad)
    
    def DrawSphere(self, radius):
        quad = gluNewQuadric()
        gluSphere(quad, radius, 20, 20)
        gluDeleteQuadric(quad)
    
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


class RobotArmFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title="3D Robot Arm Simulation with Gripper", size=(1100, 750))
        
        self.robot = RobotArm()
        self.cube = Cube(2.0, 1.0, 0.3)  # Position cube near the arm
        
        # Create main panel
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Create OpenGL canvas
        self.canvas = GLCanvas(panel, self.robot, self.cube)
        
        # Create control panel
        control_panel = wx.Panel(panel)
        control_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(control_panel, label="Robot Arm Controls")
        font = title.GetFont()
        font.PointSize += 2
        font = font.Bold()
        title.SetFont(font)
        control_sizer.Add(title, 0, wx.ALL, 10)
        
        # Joint 1 (Base)
        control_sizer.Add(wx.StaticText(control_panel, label="Base Rotation (θ1)"), 0, wx.LEFT|wx.TOP, 10)
        self.slider1 = wx.Slider(control_panel, value=0, minValue=-180, maxValue=180, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider1.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider1, 0, wx.EXPAND|wx.ALL, 10)
        
        # Joint 2 (Shoulder)
        control_sizer.Add(wx.StaticText(control_panel, label="Shoulder (θ2)"), 0, wx.LEFT, 10)
        self.slider2 = wx.Slider(control_panel, value=45, minValue=-90, maxValue=90, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider2.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider2, 0, wx.EXPAND|wx.ALL, 10)
        
        # Joint 3 (Elbow)
        control_sizer.Add(wx.StaticText(control_panel, label="Elbow (θ3)"), 0, wx.LEFT, 10)
        self.slider3 = wx.Slider(control_panel, value=30, minValue=-180, maxValue=180, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider3.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider3, 0, wx.EXPAND|wx.ALL, 10)
        
        # Joint 4 (Wrist)
        control_sizer.Add(wx.StaticText(control_panel, label="Wrist (θ4)"), 0, wx.LEFT, 10)
        self.slider4 = wx.Slider(control_panel, value=0, minValue=-90, maxValue=90, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider4.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider4, 0, wx.EXPAND|wx.ALL, 10)
        
        # Gripper Rotation (θ5)
        control_sizer.Add(wx.StaticText(control_panel, label="Gripper Rotation (θ5)"), 0, wx.LEFT, 10)
        self.slider5 = wx.Slider(control_panel, value=0, minValue=-180, maxValue=180, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider5.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider5, 0, wx.EXPAND|wx.ALL, 10)
        
        # Gripper control
        control_sizer.Add(wx.StaticText(control_panel, label="Gripper Opening"), 0, wx.LEFT, 10)
        self.gripper_slider = wx.Slider(control_panel, value=50, minValue=0, maxValue=100, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.gripper_slider.Bind(wx.EVT_SLIDER, self.OnGripperSlider)
        control_sizer.Add(self.gripper_slider, 0, wx.EXPAND|wx.ALL, 10)
        
        # Gripper buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.grab_btn = wx.Button(control_panel, label="Grab Cube")
        self.grab_btn.Bind(wx.EVT_BUTTON, self.OnGrabCube)
        btn_sizer.Add(self.grab_btn, 1, wx.ALL, 5)
        
        self.release_btn = wx.Button(control_panel, label="Release Cube")
        self.release_btn.Bind(wx.EVT_BUTTON, self.OnReleaseCube)
        self.release_btn.Enable(False)
        btn_sizer.Add(self.release_btn, 1, wx.ALL, 5)
        control_sizer.Add(btn_sizer, 0, wx.EXPAND|wx.ALL, 5)
        
        # Position display
        control_sizer.Add(wx.StaticLine(control_panel), 0, wx.EXPAND|wx.ALL, 10)
        control_sizer.Add(wx.StaticText(control_panel, label="End Effector Position:"), 0, wx.LEFT|wx.TOP, 10)
        self.pos_text = wx.StaticText(control_panel, label="X: 0.00\nY: 0.00\nZ: 0.00")
        control_sizer.Add(self.pos_text, 0, wx.ALL, 10)
        
        # Cube position display
        control_sizer.Add(wx.StaticText(control_panel, label="Cube Position:"), 0, wx.LEFT, 10)
        self.cube_text = wx.StaticText(control_panel, label="X: 0.00\nY: 0.00\nZ: 0.00")
        control_sizer.Add(self.cube_text, 0, wx.ALL, 10)
        
        # Status
        self.status_text = wx.StaticText(control_panel, label="Status: Ready")
        control_sizer.Add(self.status_text, 0, wx.ALL, 10)
        
        # Reset button
        reset_btn = wx.Button(control_panel, label="Reset All")
        reset_btn.Bind(wx.EVT_BUTTON, self.OnReset)
        control_sizer.Add(reset_btn, 0, wx.EXPAND|wx.ALL, 10)
        
        # Instructions
        control_sizer.Add(wx.StaticLine(control_panel), 0, wx.EXPAND|wx.ALL, 10)
        instructions = wx.StaticText(control_panel, label="Mouse Controls:\n• Left drag: Rotate view\n• Scroll: Zoom in/out\n\nGripper:\n• Close gripper near cube\n• Click 'Grab' to pick up\n• Move arm to relocate\n• Click 'Release' to drop")
        control_sizer.Add(instructions, 0, wx.ALL, 10)
        
        control_panel.SetSizer(control_sizer)
        
        # Add to main sizer
        main_sizer.Add(self.canvas, 1, wx.EXPAND)
        main_sizer.Add(control_panel, 0, wx.EXPAND|wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
        
        self.updateLock = False 
        self.lastPeriodicTime = time.time()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(500)

        
        self.UpdatePosition()
        self.Centre()
    
    def periodic(self, event):
        """ Call back every periodic time."""
        now = time.time()
        if (not self.updateLock) and now - self.lastPeriodicTime >= 1:
            print("periodic(): main frame update at %s" % str(now))
            self.lastPeriodicTime = now
            self.canvas.updateCubeZ()
            self.canvas.Refresh()
            # update the manager.

    def OnSlider(self, event):
        self.robot.theta1 = self.slider1.GetValue()
        self.robot.theta2 = self.slider2.GetValue()
        self.robot.theta3 = self.slider3.GetValue()
        self.robot.theta4 = self.slider4.GetValue()
        self.robot.theta5 = self.slider5.GetValue()
        
        # Update cube position if holding
        if self.robot.holding_cube:
            positions = self.robot.forward_kinematics()
            gripper_pos = positions[-1]
            self.cube.set_position(gripper_pos[0], gripper_pos[1], gripper_pos[2])
        
        self.UpdatePosition()
        self.canvas.Refresh()
    
    def OnGripperSlider(self, event):
        self.robot.gripper_open = self.gripper_slider.GetValue()
        self.canvas.Refresh()
    
    def OnGrabCube(self, event):
        positions = self.robot.forward_kinematics()
        gripper_pos = positions[-1]
        cube_pos = self.cube.get_position()
        
        # Calculate distance between gripper and cube
        distance = math.sqrt(
            (gripper_pos[0] - cube_pos[0])**2 +
            (gripper_pos[1] - cube_pos[1])**2 +
            (gripper_pos[2] - cube_pos[2])**2
        )
        
        # Check if gripper is close enough and closed enough
        if distance < 1 and self.robot.gripper_open < 30:
            self.robot.holding_cube = True
            self.cube.set_position(gripper_pos[0], gripper_pos[1], gripper_pos[2])
            self.grab_btn.Enable(False)
            self.release_btn.Enable(True)
            self.status_text.SetLabel("Status: Holding cube")
            self.canvas.Refresh()
        else:
            if distance >= 0.4:
                self.status_text.SetLabel("Status: Too far from cube!")
            else:
                self.status_text.SetLabel("Status: Close gripper more!")
    
    def OnReleaseCube(self, event):
        self.robot.holding_cube = False
        self.grab_btn.Enable(True)
        self.release_btn.Enable(False)
        self.status_text.SetLabel("Status: Cube released")
        self.canvas.Refresh()
    
    def UpdatePosition(self):
        positions = self.robot.forward_kinematics()
        end_pos = positions[-1]
        self.pos_text.SetLabel(f"X: {end_pos[0]:.2f}\nY: {end_pos[1]:.2f}\nZ: {end_pos[2]:.2f}")
        
        cube_pos = self.cube.get_position()
        self.cube_text.SetLabel(f"X: {cube_pos[0]:.2f}\nY: {cube_pos[1]:.2f}\nZ: {cube_pos[2]:.2f}")
    
    def OnReset(self, event):
        self.slider1.SetValue(0)
        self.slider2.SetValue(45)
        self.slider3.SetValue(30)
        self.slider4.SetValue(0)
        self.slider5.SetValue(0)
        self.gripper_slider.SetValue(50)
        
        self.robot.holding_cube = False
        self.cube.reset()
        self.grab_btn.Enable(True)
        self.release_btn.Enable(False)
        self.status_text.SetLabel("Status: Reset complete")
        
        self.OnSlider(None)


if __name__ == '__main__':
    app = wx.App(False)
    frame = RobotArmFrame()
    frame.Show()
    app.MainLoop()