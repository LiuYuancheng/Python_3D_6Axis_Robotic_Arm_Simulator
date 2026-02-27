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
from scipy.optimize import fsolve

import robotArmCtrlGlobal as gv
import robotArmCtrlConst as ct
import opcuaComm

def getRobotJointAngles(x, y, initial_guess=None):
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
        eq2 = (d + e + f) + z_target   # Z-axis constraint (shift up by 2.0 so the cube is on the ground)
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
    return (int(np.degrees(t1)), int(np.degrees(t2)), int(np.degrees(t3)))

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
        #angles = getRobotJointAngles(x, y, resolution=5)
        angles = solve_robot_arm(x, y)
        gv.iMainFrame.baseDisCtrl.SetValue(int(baseAngle))
        gv.iMainFrame.shoulderDisCtrl.SetValue(int(angles[0]))
        gv.iMainFrame.elbowDisCtrl.SetValue(int(angles[1]))
        gv.iMainFrame.wristPitchDisCtrl.SetValue(int(angles[2]))
        
    #-----------------------------------------------------------------------------  
    def stop(self):
        self.isRunning = False