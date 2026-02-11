#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmSimulator.py
#
# Purpose:     This module is a simple simulator for a 3D 6Axis robotic arm by 
#              using the wxPython and OpenGL library.
#
# Author:      Yuancheng Liu
#
# Created:     2026/01/20
# Version:     v_0.0.3
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import time
import math
import wx
import robotArmGlobal as gv
import robotArmAgents as agents
import robotArmDataMgr as dataMgr

FRAME_SIZE = (1100, 900)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class RobotArmFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title=gv.UI_TITLE, size=FRAME_SIZE)
        gv.iRobotArmObj = agents.RobotArm()
        gv.iCubeObj =agents.Cube(gv.gCubePosX, gv.gCubePosY, gv.gCubePosZ)  # Position cube near the arm
        # Create main panel
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Create OpenGL canvas
        self.canvas = agents.GLCanvas(panel, gv.iRobotArmObj, gv.iCubeObj)
        control_panel = self._buildControlPanel(panel)
        # Add to main sizer
        main_sizer.Add(self.canvas, 1, wx.EXPAND)
        main_sizer.Add(control_panel, 0, wx.EXPAND|wx.ALL, 5)
        panel.SetSizer(main_sizer)
        
        self.updateLock = False 
        self.lastPeriodicTime = time.time()
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(300)
        
        self.UpdatePosition()
        self.Centre()
        if gv.gTestMD:
            gv.iDataManager = dataMgr.robotArmDataMgr()
            gv.iDataManager.start()

    #-----------------------------------------------------------------------------
    def _buildControlPanel(self, mainPanel):
        """ Build the main UI sizer."""
       # Create control panel
        control_panel = wx.Panel(mainPanel)
        control_sizer = wx.BoxSizer(wx.VERTICAL)
        # Title
        title = wx.StaticText(control_panel, label="Robot Arm Controls")
        font = title.GetFont()
        font.PointSize += 2
        font = font.Bold()
        title.SetFont(font)
        control_sizer.Add(title, 0, wx.ALL, 10)
        # Added the local test control check box 
        self.checkBox = wx.CheckBox(control_panel, label="Enable the local control.")
        self.checkBox.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)
        control_sizer.Add(self.checkBox, 0, wx.ALL, 10)
        self.checkBox.SetValue(gv.gTestMD)
        # Joint 1 (Base)
        control_sizer.Add(wx.StaticText(control_panel, label="Base Rotation (θ1)"), 0, wx.LEFT|wx.TOP, 10)
        self.slider1 = wx.Slider(control_panel, value=int(gv.gMotoAngle1), minValue=-180, maxValue=180, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider1.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider1, 0, wx.EXPAND|wx.ALL, 10)
        # Joint 2 (Shoulder)
        control_sizer.Add(wx.StaticText(control_panel, label="Shoulder (θ2)"), 0, wx.LEFT, 10)
        self.slider2 = wx.Slider(control_panel, value=int(gv.gMotoAngle2), minValue=-90, maxValue=90, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider2.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider2, 0, wx.EXPAND|wx.ALL, 10)
        # Joint 3 (Elbow)
        control_sizer.Add(wx.StaticText(control_panel, label="Elbow (θ3)"), 0, wx.LEFT, 10)
        self.slider3 = wx.Slider(control_panel, value=int(gv.gMotoAngle3), minValue=-180, maxValue=180, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider3.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider3, 0, wx.EXPAND|wx.ALL, 10)
        # Joint 4 (Wrist)
        control_sizer.Add(wx.StaticText(control_panel, label="Wrist (θ4)"), 0, wx.LEFT, 10)
        self.slider4 = wx.Slider(control_panel, value=int(gv.gMotoAngle4), minValue=-90, maxValue=90, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider4.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider4, 0, wx.EXPAND|wx.ALL, 10)
        # Gripper Rotation (θ5)
        control_sizer.Add(wx.StaticText(control_panel, label="Gripper Rotation (θ5)"), 0, wx.LEFT, 10)
        self.slider5 = wx.Slider(control_panel, value=int(gv.gMotoAngle5), minValue=-180, maxValue=180, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
        self.slider5.Bind(wx.EVT_SLIDER, self.OnSlider)
        control_sizer.Add(self.slider5, 0, wx.EXPAND|wx.ALL, 10)
        # Gripper control
        control_sizer.Add(wx.StaticText(control_panel, label="Gripper Opening"), 0, wx.LEFT, 10)
        self.gripper_slider = wx.Slider(control_panel, value=int(gv.gMotoAngle6), minValue=0, maxValue=100, style=wx.SL_HORIZONTAL|wx.SL_LABELS)
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
        #control_sizer.Add(wx.StaticLine(control_panel), 0, wx.EXPAND|wx.ALL, 10)
        instructions = wx.StaticText(control_panel, label="Mouse Controls:\n• Left drag: Rotate view\n• Scroll: Zoom in/out\n\nGripper:\n• Close gripper near cube\n• Click 'Grab' to pick up\n• Move arm to relocate\n• Click 'Release' to drop")
        control_sizer.Add(instructions, 0, wx.ALL, 10)
        
        control_panel.SetSizer(control_sizer)
        return control_panel

    #-----------------------------------------------------------------------------
    def periodic(self, event):
        """ Call back every periodic time."""
        now = time.time()
        #if (not self.updateLock) and now - self.lastPeriodicTime >= 1:
        print("periodic(): main frame update at %s" % str(now))
        self.lastPeriodicTime = now
        self.canvas.updateCubeZ()
        # update the arm control movement.
        if not gv.gTestMD: self.updateArmMovement()
        self.canvas.Refresh()
        # update the manager.

    #-----------------------------------------------------------------------------
    def updateArmMovement(self):
        if gv.iDataManager is None: return 
        reqList = gv.iDataManager.getArmAngleRequest()
        crtList = gv.iRobotArmObj.getJointAngles()
        if reqList == crtList: 
            print("The arm is at the request position.")
            return
        # move the motor1
        if gv.iRobotArmObj.theta1 < reqList[0]:
            gv.iRobotArmObj.theta1 += gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta1 > reqList[0]:
                gv.iRobotArmObj.theta1 = reqList[0]
        elif gv.iRobotArmObj.theta1 > reqList[0]:
            gv.iRobotArmObj.theta1 -= gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta1 < reqList[0]:
                gv.iRobotArmObj.theta1 = reqList[0]
        # move the motor2
        if gv.iRobotArmObj.theta2 < reqList[1]:
            gv.iRobotArmObj.theta2 += gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta2 > reqList[1]:
                gv.iRobotArmObj.theta2 = reqList[1]
        elif gv.iRobotArmObj.theta2 > reqList[1]:
            gv.iRobotArmObj.theta2 -= gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta2 < reqList[1]:
                gv.iRobotArmObj.theta2 = reqList[1]
        # move the motor3
        if gv.iRobotArmObj.theta3 < reqList[2]:
            gv.iRobotArmObj.theta3 += gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta3 > reqList[2]:
                gv.iRobotArmObj.theta3 = reqList[2]
        elif gv.iRobotArmObj.theta3 > reqList[2]:
            gv.iRobotArmObj.theta3 -= gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta3 < reqList[2]:
                gv.iRobotArmObj.theta3 = reqList[2]
        # move the motor4
        if gv.iRobotArmObj.theta4 < reqList[3]:
            gv.iRobotArmObj.theta4 += gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta4 > reqList[3]:
                gv.iRobotArmObj.theta4 = reqList[3]
        elif gv.iRobotArmObj.theta4 > reqList[3]:
            gv.iRobotArmObj.theta4 -= gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta4 < reqList[3]:
                gv.iRobotArmObj.theta4 = reqList[3]
        # move the motor5
        if gv.iRobotArmObj.theta5 < reqList[4]:
            gv.iRobotArmObj.theta5 += gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta5 > reqList[4]:
                gv.iRobotArmObj.theta5 = reqList[4]
        elif gv.iRobotArmObj.theta5 > reqList[4]:
            gv.iRobotArmObj.theta5 -= gv.gMotorDegSpeed
            if gv.iRobotArmObj.theta5 < reqList[4]:
                gv.iRobotArmObj.theta5 = reqList[4]
        # move the gripper
        if gv.iRobotArmObj.gripper_open < reqList[5]:
            gv.iRobotArmObj.gripper_open += gv.gMotorDegSpeed
            if gv.iRobotArmObj.gripper_open > reqList[5]:
                gv.iRobotArmObj.gripper_open = reqList[5]
        elif gv.iRobotArmObj.gripper_open > reqList[5]:
            gv.iRobotArmObj.gripper_open -= gv.gMotorDegSpeed
            if gv.iRobotArmObj.gripper_open < reqList[5]:
                gv.iRobotArmObj.gripper_open = reqList[5]
        
        self.UpdatePosition()
        self.slider1.SetValue(int(gv.iRobotArmObj.theta1))
        self.slider2.SetValue(int(gv.iRobotArmObj.theta2))
        self.slider3.SetValue(int(gv.iRobotArmObj.theta3))
        self.slider4.SetValue(int(gv.iRobotArmObj.theta4))
        self.slider5.SetValue(int(gv.iRobotArmObj.theta5))
        self.gripper_slider.SetValue(int(gv.iRobotArmObj.gripper_open))

    #-----------------------------------------------------------------------------
    def OnCheckBox(self, event):
        cbObj = event.GetEventObject()
        gv.gTestMD = cbObj.IsChecked()
        self.slider1.Enable(gv.gTestMD)
        self.slider2.Enable(gv.gTestMD)
        self.slider3.Enable(gv.gTestMD)
        self.slider4.Enable(gv.gTestMD)
        self.slider5.Enable(gv.gTestMD)
        self.gripper_slider.Enable(gv.gTestMD)
        self.grab_btn.Enable(gv.gTestMD)

    #-----------------------------------------------------------------------------
    def OnSlider(self, event):
        gv.iRobotArmObj.theta1 = self.slider1.GetValue()
        gv.iRobotArmObj.theta2 = self.slider2.GetValue()
        gv.iRobotArmObj.theta3 = self.slider3.GetValue()
        gv.iRobotArmObj.theta4 = self.slider4.GetValue()
        gv.iRobotArmObj.theta5 = self.slider5.GetValue()
        
        # Update cube position if holding
        if gv.iRobotArmObj.holding_cube:
            positions = gv.iRobotArmObj.forwardKinematics()
            gripper_pos = positions[-1]
            gv.iCubeObj.setPosition(gripper_pos[0], gripper_pos[1], gripper_pos[2]-0.3)
        
        self.UpdatePosition()
        self.canvas.Refresh()
    
    #-----------------------------------------------------------------------------
    def OnGripperSlider(self, event):
        gv.iRobotArmObj.gripper_open = self.gripper_slider.GetValue()
        self.canvas.Refresh()
    
    #-----------------------------------------------------------------------------
    def OnGrabCube(self, event):
        positions = gv.iRobotArmObj.forwardKinematics()
        gripper_pos = positions[-1]
        cube_pos = gv.iCubeObj.getPosition()
        
        # Calculate distance between gripper and cube
        distance = math.sqrt(
            (gripper_pos[0] - cube_pos[0])**2 +
            (gripper_pos[1] - cube_pos[1])**2 +
            (gripper_pos[2] - cube_pos[2])**2
        )
        
        # Check if gripper is close enough and closed enough
        if distance < 1 and gv.iRobotArmObj.gripper_open < 30:
            gv.iRobotArmObj.holding_cube = True
            gv.iCubeObj.setPosition(gripper_pos[0], gripper_pos[1], gripper_pos[2]-0.3)
            self.grab_btn.Enable(False)
            self.release_btn.Enable(True)
            self.status_text.SetLabel("Status: Holding cube")
            self.canvas.Refresh()
        else:
            if distance >= 0.4:
                self.status_text.SetLabel("Status: Too far from cube!")
            else:
                self.status_text.SetLabel("Status: Close gripper more!")
    
    #-----------------------------------------------------------------------------
    def OnReleaseCube(self, event):
        gv.iRobotArmObj.holding_cube = False
        self.grab_btn.Enable(True)
        self.release_btn.Enable(False)
        self.status_text.SetLabel("Status: Cube released")
        self.canvas.Refresh()
    
    #-----------------------------------------------------------------------------
    def UpdatePosition(self):
        positions = gv.iRobotArmObj.forwardKinematics()
        end_pos = positions[-1]
        self.pos_text.SetLabel("X: %.2f\nY: %.2f\nZ: %.2f" %(end_pos[0], end_pos[1], end_pos[2]))
        
        cube_pos = gv.iCubeObj.getPosition()
        self.cube_text.SetLabel(f"X: {cube_pos[0]:.2f}\nY: {cube_pos[1]:.2f}\nZ: {cube_pos[2]:.2f}")
    
    #-----------------------------------------------------------------------------
    def OnReset(self, event):
        self.slider1.SetValue(gv.gMotoAngle1)
        self.slider2.SetValue(gv.gMotoAngle2)
        self.slider3.SetValue(gv.gMotoAngle3)
        self.slider4.SetValue(gv.gMotoAngle4)
        self.slider5.SetValue(gv.gMotoAngle5)

        self.gripper_slider.SetValue(gv.gMotoAngle6)
        
        gv.iRobotArmObj.holding_cube = False
        gv.iCubeObj.reset()
        self.grab_btn.Enable(True)
        self.release_btn.Enable(False)
        self.status_text.SetLabel("Status: Reset complete")
        
        self.OnSlider(None)

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    app = wx.App(False)
    gv.iMainFrame = RobotArmFrame()
    gv.iMainFrame.Show()
    app.MainLoop()
