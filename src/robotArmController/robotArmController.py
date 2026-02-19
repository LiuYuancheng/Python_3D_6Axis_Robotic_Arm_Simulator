#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmController.py
#
# Purpose:     This module is the main controller to connect to the robot arm 
#              PLC to read the sensor data and change the arm motor angles.
#
# Author:      Yuancheng Liu
#
# Version:     v_0.0.1
# Created:     2026/02/11
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License  
#-----------------------------------------------------------------------------

import os
import time
import json

import wx
import robotArmCtrlGlobal as gv
import robotArmCtrlConst as ct
import robotArmCtrlPanel as pl
import robotArmCtrlManger as mgr

FRAME_SIZE = (1320, 735)
PERIODIC = 300      # update in every 500ms

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class UIFrame(wx.Frame):
    """ Main UI frame window."""
    def __init__(self, parent, id, title):
        """ Init the UI and parameters """
        wx.Frame.__init__(self, parent, id, title, size=FRAME_SIZE)
        self.SetBackgroundColour(wx.Colour(200, 210, 200))
        #self.SetTransparent(gv.gTranspPct*255//100)
        self.SetIcon(wx.Icon(gv.ICO_PATH))
        # Build UI sizer
        self.connected = False
        # load the action config files
        self.actCfgFiles = [filename for filename in os.listdir(gv.SCE_FD) if filename.endswith('.json')]
        self.tasksList = []
        self.scenarioName = None

        self.SetSizer(self._buildUISizer())
        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('Test mode: %s' %str(gv.gTestMD))

        # Set the periodic call back
        self.lastPeriodicTime = time.time()
        self.timer = wx.Timer(self)
        self.updateLock = False
        self.Bind(wx.EVT_TIMER, self.periodic)
        self.timer.Start(PERIODIC)  # every 500 ms
        self.Bind(wx.EVT_CLOSE, self.onClose)

        if not gv.gTestMD:
            gv.iDataMgr = mgr.plcDataManager(self)
            gv.iDataMgr.start()

#--UIFrame---------------------------------------------------------------------
    def _buildUISizer(self):
        """ Build the main UI Sizer. """
        flagsL = wx.LEFT
        mSizer = wx.BoxSizer(wx.VERTICAL)
        mSizer.AddSpacer(5)
        # Row 0 
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        self.commChoice = wx.Choice(self, size = (120, 30), choices = ['OPCUA : TCP',])
        self.commChoice.SetSelection(0)
        hbox0.Add(self.commChoice, flag=flagsL | wx.CENTER, border=2)
        hbox0.AddSpacer(10)
        self.serialLedBt = wx.Button(self, label='Comm Connection : OFF', size=(150, 26))
        self.serialLedBt.SetBackgroundColour(wx.Colour('GRAY'))
        hbox0.Add(self.serialLedBt, flag=flagsL, border=2)
        mSizer.Add(hbox0, flag=flagsL, border=2)
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(1310, -1),
                        style=wx.LI_HORIZONTAL), flag=wx.LEFT, border=2)
        mSizer.AddSpacer(10)
        # Row 1
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        # Cube sensor display 
        gv.iGridPanel = pl.cubeSensorPanel(self)
        hbox.Add(gv.iGridPanel, flag=flagsL, border=2)
        # Robot arm angle display and control panel.
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        gripSizer = self._buildGripSizer()
        hbox1.Add(gripSizer, flag=flagsL, border=2)
        wrstRSizer = self._buildWristRollSizer()
        hbox1.Add(wrstRSizer, flag=flagsL, border=2)
        wrstPSizer = self._buildWristPitchSizer()
        hbox1.Add(wrstPSizer, flag=flagsL, border=2)
        vbox.Add(hbox1, flag=flagsL, border=2)
        vbox.AddSpacer(5)
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        elbowSizer = self._buildElbowSizer()
        hbox2.Add(elbowSizer, flag=flagsL, border=2)
        shoulderSizer = self._buildShoulderSizer()
        hbox2.Add(shoulderSizer, flag=flagsL, border=2)
        baseSizer = self._buildBaseSizer()
        hbox2.Add(baseSizer, flag=flagsL, border=2)
        vbox.Add(hbox2, flag=flagsL, border=2)
        hbox.Add(vbox, flag=flagsL, border=2)
        mSizer.Add(hbox, flag=flagsL, border=2)
        mSizer.AddSpacer(5)
        mSizer.Add(wx.StaticLine(self, wx.ID_ANY, size=(1310, -1),
                        style=wx.LI_HORIZONTAL), flag=wx.LEFT, border=2)
        mSizer.AddSpacer(10)
        # Row 2 
        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.retBt = wx.Button(self, label='Reset Position', size=(100, 22))
        self.retBt.Bind(wx.EVT_BUTTON, self.onReset)
        hbox3.Add(self.retBt, flag=flagsL, border=2)
        hbox3.AddSpacer(10)
        self.loadBt = wx.Button(self, label='Load Action Scenario', size=(140, 22))
        self.loadBt.Bind(wx.EVT_BUTTON, self.onLoadScenario)
        hbox3.Add(self.loadBt, flag=flagsL, border=2)
        hbox3.AddSpacer(10)
        self.executeBt = wx.Button(self, label='Execute Scenario', size=(100, 22))
        self.executeBt.Bind(wx.EVT_BUTTON, self.onExecute)
        hbox3.Add(self.executeBt, flag=flagsL, border=2)
        hbox3.AddSpacer(10)
        self.scenarioLB = wx.StaticText(self, label=" Current Scenario: %s" %str(self.scenarioName))
        hbox3.Add(self.scenarioLB, flag=flagsL, border=2)
        hbox3.AddSpacer(10)
        mSizer.Add(hbox3, flag=flagsL, border=2)
        return mSizer

    #--UIFrame---------------------------------------------------------------------
    def _buildGripSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.gripDis = pl.angleDisplayPanel(self, "Gripper", angleS=ct.IV_ARM_ANGLE_6, angleC=ct.IV_ARM_ANGLE_6)
        sizer.Add(self.gripDis, flag=wx.LEFT, border=2)
        sizer.AddSpacer(5)
        self.gripperCtrl = wx.Slider(self, value = int(ct.IV_ARM_ANGLE_6), minValue = 0, maxValue = 100, size=(240, 30),
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        sizer.Add(self.gripperCtrl, flag=wx.CENTRE)
        sizer.AddSpacer(5)
        return sizer
    
    #--UIFrame---------------------------------------------------------------------
    def _buildWristRollSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.wristRollDis = pl.angleDisplayPanel(self, "WristRoll", angleS=ct.IV_ARM_ANGLE_5, angleC=ct.IV_ARM_ANGLE_5)
        sizer.Add(self.wristRollDis, flag=wx.LEFT, border=2)
        sizer.AddSpacer(5)
        self.wristRollDisCtrl = wx.Slider(self, value = int(ct.IV_ARM_ANGLE_5), minValue = -180, maxValue = 180, size=(240, 30),
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        sizer.Add(self.wristRollDisCtrl, flag=wx.CENTRE)
        sizer.AddSpacer(5)
        return sizer

    #--UIFrame---------------------------------------------------------------------
    def _buildWristPitchSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.wristPitchDis = pl.angleDisplayPanel(self, "wristPitch", angleS=ct.IV_ARM_ANGLE_4, angleC=ct.IV_ARM_ANGLE_4)
        sizer.Add(self.wristPitchDis, flag=wx.LEFT, border=2)
        sizer.AddSpacer(5)
        self.wristPitchDisCtrl = wx.Slider(self, value = int(ct.IV_ARM_ANGLE_4), minValue = -90, maxValue = 90, size=(240, 30),
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        sizer.Add(self.wristPitchDisCtrl, flag=wx.CENTRE)
        sizer.AddSpacer(5)
        return sizer

    #--UIFrame---------------------------------------------------------------------
    def _buildElbowSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.elbowDis = pl.angleDisplayPanel(self, "Elbow", angleS=ct.IV_ARM_ANGLE_3, angleC=ct.IV_ARM_ANGLE_3)
        sizer.Add(self.elbowDis, flag=wx.LEFT, border=2)
        sizer.AddSpacer(5)        
        self.elbowDisCtrl = wx.Slider(self, value = int(ct.IV_ARM_ANGLE_3), minValue = -180, maxValue = 180, size=(240, 30),
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        sizer.Add(self.elbowDisCtrl, flag=wx.CENTRE)
        sizer.AddSpacer(5)
        return sizer

    #--UIFrame---------------------------------------------------------------------
    def _buildShoulderSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.shoulderDis = pl.angleDisplayPanel(self, "Shoulder", angleS=ct.IV_ARM_ANGLE_2, angleC=ct.IV_ARM_ANGLE_2)
        sizer.Add(self.shoulderDis, flag=wx.LEFT, border=2)
        sizer.AddSpacer(5)
        self.shoulderDisCtrl = wx.Slider(self, value = int(ct.IV_ARM_ANGLE_2), minValue = -90, maxValue = 90, size=(240, 30),
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        sizer.Add(self.shoulderDisCtrl, flag=wx.CENTRE)
        sizer.AddSpacer(5)
        return sizer

    #--UIFrame---------------------------------------------------------------------
    def _buildBaseSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.baseDis = pl.angleDisplayPanel(self, "Base", angleS=ct.IV_ARM_ANGLE_1, angleC=ct.IV_ARM_ANGLE_1)
        sizer.Add(self.baseDis, flag=wx.LEFT, border=2)
        sizer.AddSpacer(5)
        self.baseDisCtrl = wx.Slider(self, value = int(ct.IV_ARM_ANGLE_1), minValue = -180, maxValue = 180, size=(240, 30),
        style = wx.SL_HORIZONTAL|wx.SL_LABELS)
        sizer.Add(self.baseDisCtrl, flag=wx.CENTRE)
        sizer.AddSpacer(5)
        return sizer

    def onReset(self, event):
        self.commMgr.addRestTask()

    def onExecute(self, event):
        if self.tasksList and len(self.tasksList) > 0:
            print("Execute scenario: %s" %str(self.scenarioName))
            for action in self.tasksList:
                if action['act'] == 'RST':
                    self.commMgr.addRestTask()
                elif action['act'] == 'MOV':
                    self.commMgr.addMotorMovTask(action['key'], action['val'])
        else:
            print("No action in scenario!")

    def setConnection(self, connFlg):
        self.connected = bool(connFlg)
        colourStr = 'GREEN' if connFlg else 'GRAY'
        labelStr = 'Comm Connection : ON ' if connFlg else 'Comm Connection : OFF'
        self.serialLedBt.SetBackgroundColour(wx.Colour(colourStr))
        self.serialLedBt.SetLabel(labelStr)
    
#-----------------------------------------------------------------------------
    def onLoadScenario(self, event):
        self.scenarioDialog = wx.SingleChoiceDialog(self,
                                                    'Select Scenario', 
                                                    'Scenario selection', 
                                                    self.actCfgFiles)
        resp = self.scenarioDialog.ShowModal()
        if resp == wx.ID_OK:
            actConfigName = self.scenarioDialog.GetStringSelection()
            self.scenarioName = actConfigName
            actConfigPath = os.path.join(gv.SCE_FD, actConfigName)
            if os.path.exists(actConfigPath):
                with open(actConfigPath) as json_file:
                    self.tasksList = json.load(json_file)
                self.scenarioLB.SetLabel(" Current Scenario: %s" %str(actConfigName))    
        self.scenarioDialog.Destroy()
        self.scenarioDialog = None


    def onLoad(self, event):
        taskList = [('grip', '220'), ('base', '90'), ('shld', '155'), ('elbw', '90'), ('wrtP', '205'),
                    ('wrtR', '150'),
                    ('grip', '160'),
                    ('elbw', '130'),
                    ('base', '180'),
                    ('grip', '220'),
                ]
        for mvtask in taskList:
            self.commMgr.addMotorMovTask(mvtask[0], mvtask[1])

#--UIFrame---------------------------------------------------------------------
    def periodic(self, event):
        """ Call back every periodic time."""
        now = time.time()
        if (not self.updateLock) and now - self.lastPeriodicTime >= gv.gUpdateRate:
            #print("main frame update at %s" % str(now))
            self.lastPeriodicTime = now
            self.updateSensorInfo()
            # update the display
            #angles = self.commMgr.getModtorPos()
            #if not angles is None:
            #    self.updateDisplay(angles)
            if gv.iGridPanel: gv.iGridPanel.updateDisplay()
            self.baseDis.updateDisplay()
            self.shoulderDis.updateDisplay()
            self.elbowDis.updateDisplay()
            self.wristPitchDis.updateDisplay()
            self.wristRollDis.updateDisplay()
            self.gripDis.updateDisplay()

    def getAngleControlValues(self):
        return [self.baseDisCtrl.GetValue(), self.shoulderDisCtrl.GetValue(), self.elbowDisCtrl.GetValue(),
                self.wristPitchDisCtrl.GetValue(), self.wristRollDisCtrl.GetValue(), self.gripperCtrl.GetValue()]

    def updateSensorInfo(self):
        if gv.iDataMgr:
            dataDict = gv.iDataMgr.getSensorDataDict()
            gv.iGridPanel.updateCubePos(dataDict[ct.VN_CUBE_POS_X], dataDict[ct.VN_CUBE_POS_Y], dataDict[ct.VN_CUBE_POS_Z])
            self.baseDis.setSensorAngle(int(dataDict[ct.VN_ARM_ANGLE_1]))
            self.baseDis.setControlAngle(int(self.baseDisCtrl.GetValue()))
            self.shoulderDis.setSensorAngle(int(dataDict[ct.VN_ARM_ANGLE_2]))
            self.shoulderDis.setControlAngle(int(self.shoulderDisCtrl.GetValue()))
            self.elbowDis.setSensorAngle(int(dataDict[ct.VN_ARM_ANGLE_3]))
            self.elbowDis.setControlAngle(int(self.elbowDisCtrl.GetValue()))
            self.wristPitchDis.setSensorAngle(int(dataDict[ct.VN_ARM_ANGLE_4]))
            self.wristPitchDis.setControlAngle(int(self.wristPitchDisCtrl.GetValue()))
            self.wristRollDis.setSensorAngle(int(dataDict[ct.VN_ARM_ANGLE_5]))
            self.wristRollDis.setControlAngle(int(self.wristRollDisCtrl.GetValue()))
            self.gripDis.setSensorAngle(int(dataDict[ct.VN_ARM_ANGLE_6]))
            self.gripDis.setControlAngle(int(self.gripperCtrl.GetValue()))

    def onClose(self, event):
        self.Destroy()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class MyApp(wx.App):
    def OnInit(self):
        gv.iMainFrame = UIFrame(None, -1, gv.APP_NAME[0])
        gv.iMainFrame.Show(True)
        return True

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    app = MyApp(0)
    app.MainLoop()
