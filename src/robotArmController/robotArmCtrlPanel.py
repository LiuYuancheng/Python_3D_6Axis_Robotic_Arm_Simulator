#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        BraccioControllerPnl.py
#
# Purpose:     This module will provide the motor controller and potentiometer
#              reading display panel for the controller.
# 
# Author:      Yuancheng Liu
#
# Version:     v_0.1
# Created:     2023/09/21
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License  
#-----------------------------------------------------------------------------
import wx
import math

from datetime import datetime
import robotArmCtrlGlobal as gv

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class cubeSensorPanel(wx.Panel):
    """ Panel to display cube position from the sensor. """

    def __init__(self, parent, panelSize=(550, 550)):
        wx.Panel.__init__(self, parent, size=panelSize)
        self.SetBackgroundColour(wx.Colour('BLACK'))
        self.panelSize = panelSize
        self.cubeX = 2
        self.cubeY = 1
        self.cubeZ = 0.3
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.SetDoubleBuffered(True)

    #-----------------------------------------------------------------------------
    def onPaint(self, evt):
        """ Draw the map on the panel."""
        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen(wx.Colour(67, 138, 85), 1, style=wx.PENSTYLE_LONG_DASH))
        dc.SetBrush(wx.Brush(wx.Colour('BLACK'), wx.BRUSHSTYLE_TRANSPARENT))
        dc.SetTextForeground(wx.Colour("GREEN"))
        dc.DrawText('Ground Cube Sensor Display', 5, 5)
        w, h = self.panelSize
        # Draw the grid coordinate.
        for i in range(11):
            dc.DrawLine(i*50+25, 25, i*50+25, h-25)
            dc.DrawLine(25, i*50+25, w-25, i*50+25)
        dc.DrawCircle(275, 275, 10)
        dc.DrawCircle(275, 275, 120)
        for i in range(4):
            dc.DrawText(str(i+1), 275+i*50+55, 280)
            dc.DrawText(str(i+1), 280, 275+i*50+55)
            dc.DrawText(str(-i-1), 280, 270-i*50-60)
            dc.DrawText(str(-i-1), 270-i*50-60, 280)
        dc.DrawText('+X', 280, 530)
        dc.DrawText('+Y', 530, 280)
        dc.DrawText('-X', 280, 10)
        dc.DrawText('-Y', 10, 280)
        # Draw the cube
        #if self.cubeZ < 0.4:
        dc.SetBrush(wx.Brush(wx.Colour('GREEN')))
        dc.SetPen(wx.Pen(wx.Colour('YELLOW'), 1))
        dc.DrawRectangle(275+self.cubeY*50-10, 275+self.cubeX*50-10, 20, 20)
        dc.DrawText('Cube Coordinate: X = %.2f, Y = %.2f, Z = %.2f' % (self.cubeX, self.cubeY, self.cubeZ), 5, 530)

    #-----------------------------------------------------------------------------
    def updateCubePos(self, x, y, z):
        """ Update the cube position. """
        self.cubeX = x
        self.cubeY = y
        self.cubeZ = z

    #-----------------------------------------------------------------------------
    def updateDisplay(self, refreshFlag=True):
        """ Set/Update the display: if called as updateDisplay() the function will 
            update the panel, if called as updateDisplay(updateFlag=?) the function
            will set the self update flag.
        """
        self.Refresh(refreshFlag)
        self.Update()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class angleDisplayPanel(wx.Panel):
    """ Panel to display image. """

    def __init__(self, parent, title, angleS=0, angleC=0, panelSize=(240, 240)):
        wx.Panel.__init__(self, parent, size=panelSize)
        self.SetBackgroundColour(wx.Colour('BLACK'))
        self.panelSize = panelSize
        self.title = title
        self.angleS = int(angleS) # sensor angle
        self.angleC = int(angleC) # control angle
        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.SetDoubleBuffered(True)

    #-----------------------------------------------------------------------------
    def onPaint(self, evt):
        """ Draw the map on the panel."""
        dc = wx.PaintDC(self)        
        dc.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        dc.SetTextForeground(wx.Colour('GREEN'))
        dc.DrawText(self.title, 5, 5)
        dc.SetPen(wx.Pen(wx.Colour('GREEN'), 1, style=wx.PENSTYLE_LONG_DASH))
        dc.SetBrush(wx.Brush(wx.Colour('BLACK'), wx.BRUSHSTYLE_TRANSPARENT))
        dc.DrawLine(120, 0, 120, 240)
        dc.DrawLine(0, 120, 240, 120)
        dc.DrawCircle(120, 120, 100)
        dc.SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        dc.DrawText('0', 125, 225)
        dc.DrawText('-90', 2, 125)
        dc.DrawText('90', 225, 125)
        dc.DrawText('180', 130, 5)
        dc.DrawText('-180', 90, 5)
        # Draw the control angle.
        dc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        dc.SetPen(wx.Pen(wx.Colour('YELLOW'),2))
        x2, y2 = 120+math.sin(math.radians(self.angleC))*100, 120+math.cos(math.radians(self.angleC))*100
        dc.DrawLine(120, 120, x2, y2)
        dc.SetTextForeground(wx.Colour('YELLOW'))
        dc.DrawText(str(self.angleC)+"'", x2, y2)
        # Draw the sensor angle.
        dc.SetPen(wx.Pen(wx.Colour('GREEN'), 1, style=wx.PENSTYLE_LONG_DASH))
        x1, y1 = 120+math.sin(math.radians(self.angleS))*100, 120+math.cos(math.radians(self.angleS))*100
        dc.DrawLine(120, 120, x1, y1)
        dc.SetTextForeground(wx.Colour('GREEN'))
        dc.DrawText(str(self.angleS)+"'", x1, y1)
        return
    


        # draw the range detail.
        dc.SetPen(wx.Pen('Green'))
        dc.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
        x1, y1 = 150-math.sin(math.radians(self.limitRange[0]))*130, 150+math.cos(math.radians(self.limitRange[0]))*130
        dc.DrawLine(150,150, x1, y1)
        dc.DrawText(str(self.limitRange[0]), x1+5, y1-5)

        x2, y2 = 150-math.sin(math.radians(self.limitRange[1]))*130, 150+math.cos(math.radians(self.limitRange[1]))*130
        dc.DrawLine(150,150, x2, y2)
        dc.DrawText(str(self.limitRange[1]), x2+5, y2-5)
        dc.SetTextForeground(wx.Colour('YELLOW'))
        dc.SetPen(wx.Pen(wx.Colour('YELLOW'), width=3, style=wx.PENSTYLE_SHORT_DASH))
        if not self.angle1 is None:
            dc.DrawText("Output-1 Axis:%s" %str(self.angle1), 160, 180)
            x3, y4 = 150-math.sin(math.radians(self.angle1))*130, 150+math.cos(math.radians(self.angle1))*130
            dc.DrawLine(150,150, x3, y4)

        if not self.angle2 is None:
            dc.DrawText("Output-2 Axis:%s" %str(self.angle2), 160, 200)
            x5, y6 = 150-math.sin(math.radians(self.angle2))*130, 150+math.cos(math.radians(self.angle2))*130
            dc.DrawLine(150,150, x5, y6)

    def setSensorAngle(self, angle):
        self.angleS = int(angle)

    def setControlAngle(self, angle):
        self.angleC = int(angle)

    #-----------------------------------------------------------------------------
    def updateDisplay(self, updateFlag=None):
        """ Set/Update the display: if called as updateDisplay() the function will 
            update the panel, if called as updateDisplay(updateFlag=?) the function
            will set the self update flag.
        """
        self.Refresh(True)
        self.Update()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
def main():
    """ Main function used for local test debug panel. """

    print('Test Case start: type in the panel you want to check:')
    print('0 - PanelImge')
    print('1 - PanelCtrl')
    #pyin = str(input()).rstrip('\n')
    #testPanelIdx = int(pyin)
    testPanelIdx = 1    # change this parameter for you to test.
    print("[%s]" %str(testPanelIdx))
    app = wx.App()
    mainFrame = wx.Frame(gv.iMainFrame, -1, 'Debug Panel',
                         pos=(300, 300), size=(640, 480), style=wx.DEFAULT_FRAME_STYLE)

    testPanel = angleDisplayPanel(mainFrame, title="grip")
    mainFrame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()



