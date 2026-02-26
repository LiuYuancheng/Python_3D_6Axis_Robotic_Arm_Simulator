#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmCtrlManger.py
#
# Purpose:     This module is the data manager module also used for communicating
#              with the robot arm control OPCUA PLC to read the sensor data and
#              send the arm movement control command.
#
# Author:      Yuancheng Liu
#
# Version:     v_0.0.2
# Created:     2026/02/11
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License  
#-----------------------------------------------------------------------------

import math
import time
import asyncio
import threading
import numpy as np
from itertools import product

import robotArmCtrlGlobal as gv
import robotArmCtrlConst as ct
import opcuaComm

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
    if target_distance > 2.4:
        print(f"Target distance {target_distance:.3f} exceeds max reach of 3.0")
        return None
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
    #print(f"Target distance : {target_distance:.4f}")
    #print(f"Best match error: {best_error:.4f}")
    #print(f"Angles => theta1: {best_solution[0]}°, theta2: {best_solution[1]}°, theta3: {best_solution[2]}°")
    return best_solution

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class plcDataManager(threading.Thread):
    """ The data manager is a module running parallel with the main thread to 
        connect to PLCs to do the data communication with OPCUA-TCP
    """
    def __init__(self, parent) -> None:
        threading.Thread.__init__(self)
        self.parent = parent
        self.terminate = False
        self.dataVariableDict = {
            ct.VN_CUBE_POS_X : ct.IV_CUBE_POS_X,
            ct.VN_CUBE_POS_Y : ct.IV_CUBE_POS_Y,
            ct.VN_CUBE_POS_Z : ct.IV_CUBE_POS_Z,
            ct.VN_ARM_ANGLE_1 : ct.IV_ARM_ANGLE_1,
            ct.VN_ARM_ANGLE_2 : ct.IV_ARM_ANGLE_2,
            ct.VN_ARM_ANGLE_3 : ct.IV_ARM_ANGLE_3,
            ct.VN_ARM_ANGLE_4 : ct.IV_ARM_ANGLE_4,
            ct.VN_ARM_ANGLE_5 : ct.IV_ARM_ANGLE_5,
            ct.VN_ARM_ANGLE_6 : ct.IV_ARM_ANGLE_6,
            # add the control variable
            ct.VN_GRIPPER_CTRL: False,
            ct.VN_MOTOR1_CTRL : ct.IV_ARM_ANGLE_1,
            ct.VN_MOTOR2_CTRL : ct.IV_ARM_ANGLE_2,
            ct.VN_MOTOR3_CTRL : ct.IV_ARM_ANGLE_3,
            ct.VN_MOTOR4_CTRL : ct.IV_ARM_ANGLE_4,
            ct.VN_MOTOR5_CTRL : ct.IV_ARM_ANGLE_5,
            ct.VN_MOTOR6_CTRL : ct.IV_ARM_ANGLE_6
        }
        # Init the OPC-UA connector
        serverUrl = "opc.tcp://%s:%s/%s/server/" %(gv.gPlcDict['ip'], str(gv.gPlcDict['port']), gv.gPlcDict['id'])
        self.armOPCUAclient = opcuaComm.opcuaClient(serverUrl, timeout=4, watchdog_interval=10)
        self.terminate = False
        gv.gDebugPrint('Management HMI PLC dataMgr init done.', logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def run(self):
        """ Thread run() function will be called by start(). """
        time.sleep(1)
        gv.gDebugPrint('Management HMI PLC dataMgr run() loop start.', logType=gv.LOG_INFO)
        asyncio.run(self.plcDataProcessLoop())
        gv.gDebugPrint('Management HMI PLC dataMgr run() loop end.', logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    async def plcDataProcessLoop(self):
        try:
            await self.armOPCUAclient.connect()
            self.parent.setConnection(True)
        except Exception as e:
            gv.gDebugPrint('Connect to PLC failed: %s' % str(e), logType=gv.LOG_ERROR)
            self.parent.setConnection(False)
            return False
        gv.gDebugPrint("Start the PLC data manager loop.", logType=gv.LOG_INFO)
        while not self.terminate:
            # Fetch data from OPCUA Plc
            # Fetch cube sensor data from OPC-UA controller.
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_CUBE_POS_X)
            self.dataVariableDict[ct.VN_CUBE_POS_X] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_CUBE_POS_Y)
            self.dataVariableDict[ct.VN_CUBE_POS_Y] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_CUBE_POS_Z)
            self.dataVariableDict[ct.VN_CUBE_POS_Z] = round(val, 1)
            #print(str(self.dataVariableDict))
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_ARM_ANGLE_1)
            self.dataVariableDict[ct.VN_ARM_ANGLE_1] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_ARM_ANGLE_2)
            self.dataVariableDict[ct.VN_ARM_ANGLE_2] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_ARM_ANGLE_3)
            self.dataVariableDict[ct.VN_ARM_ANGLE_3] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_ARM_ANGLE_4)
            self.dataVariableDict[ct.VN_ARM_ANGLE_4] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_ARM_ANGLE_5)
            self.dataVariableDict[ct.VN_ARM_ANGLE_5] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_ARM_ANGLE_6)
            self.dataVariableDict[ct.VN_ARM_ANGLE_6] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR1_CTRL)
            self.dataVariableDict[ct.VN_MOTOR1_CTRL] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR2_CTRL)
            self.dataVariableDict[ct.VN_MOTOR2_CTRL] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR3_CTRL)
            self.dataVariableDict[ct.VN_MOTOR3_CTRL] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR4_CTRL)
            self.dataVariableDict[ct.VN_MOTOR4_CTRL] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR5_CTRL)
            self.dataVariableDict[ct.VN_MOTOR5_CTRL] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR6_CTRL)
            self.dataVariableDict[ct.VN_MOTOR6_CTRL] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_GRIPPER_CTRL)
            self.dataVariableDict[ct.VN_GRIPPER_CTRL] = round(val, 1)
            # Change the angle if we do the auto grab cube
            if gv.gAutoGrabFlag: 
                self.setAutoGrabAngle()
                gv.gAutoGrabFlag = False
            # check whether need to update the control
            ctrlList = gv.iMainFrame.getAngleControlValues()
            if int(ctrlList[0]) != int(self.dataVariableDict[ct.VN_MOTOR1_CTRL]):
                await self.armOPCUAclient.setVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR1_CTRL, float(ctrlList[0]))
            if int(ctrlList[1]) != int(self.dataVariableDict[ct.VN_MOTOR2_CTRL]):
                await self.armOPCUAclient.setVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR2_CTRL, float(ctrlList[1]))
            if int(ctrlList[2]) != int(self.dataVariableDict[ct.VN_MOTOR3_CTRL]):
                await self.armOPCUAclient.setVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR3_CTRL, float(ctrlList[2]))
            if int(ctrlList[3]) != int(self.dataVariableDict[ct.VN_MOTOR4_CTRL]):
                await self.armOPCUAclient.setVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR4_CTRL, float(ctrlList[3]))
            if int(ctrlList[4]) != int(self.dataVariableDict[ct.VN_MOTOR5_CTRL]):
                await self.armOPCUAclient.setVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR5_CTRL, float(ctrlList[4]))
            if int(ctrlList[5]) != int(self.dataVariableDict[ct.VN_MOTOR6_CTRL]):
                await self.armOPCUAclient.setVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_MOTOR6_CTRL, float(ctrlList[5]))
            time.sleep(0.4)
        gv.gDebugPrint("Stop the PLC data manager loop.", logType=gv.LOG_INFO)
        await self.armOPCUAclient.disconnect()

    #-----------------------------------------------------------------------------
    def getSensorDataDict(self):
        return self.dataVariableDict

    def setAutoGrabAngle(self):
        x = self.dataVariableDict[ct.VN_CUBE_POS_X]
        y = self.dataVariableDict[ct.VN_CUBE_POS_Y]
        targetDistance = np.sqrt(x**2 + y**2)
        if targetDistance > 2.4:
            gv.gDebugPrint("The cube is too far away, cannot grab it.")
            return None 
        # Calculate the base angle
        baseAngle = 0 
        if x == 0 and y > 0:
            baseAngle = 90
        elif x == 0 and y < 0:
            baseAngle = -90
        else:
            baseAngle = math.degrees(math.atan2(y, x))
        # calculate the angle for the shoulder, elbow and wrist
        angles = getRobotJointAngles(x, y, resolution=5)
        gv.iMainFrame.baseDisCtrl.SetValue(int(baseAngle))
        gv.iMainFrame.shoulderDisCtrl.SetValue(int(angles[0]))
        gv.iMainFrame.elbowDisCtrl.SetValue(int(angles[1]))
        gv.iMainFrame.wristPitchDisCtrl.SetValue(int(angles[2]))
        
    #-----------------------------------------------------------------------------  
    def stop(self):
        self.isRunning = False