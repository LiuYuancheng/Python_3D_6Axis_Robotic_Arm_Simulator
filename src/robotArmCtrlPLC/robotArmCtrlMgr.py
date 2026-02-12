#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmCtrlMgr.py
#
# Purpose:     This module is the control manager which provides a sub-thread 
#              to host the OPCUA server to receive the control command
#
# Author:      Yuancheng Liu
#
# Created:     2026/02/04
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import time
import asyncio
import threading
import robotArmGlobal as gv
import opcuaComm

SERVER_NAME = 'Robot Arm Control Server'
NAME_SPACE = 'Motor_Controller'
OBJ_NAME = 'newObject01'

M_SENSOR1_ID = 'RobotArmSensor1'
M_SENSOR2_ID = 'RobotArmSensor2'
M_SENSOR3_ID = 'RobotArmSensor3'
M_SENSOR4_ID = 'RobotArmSensor4'
M_SENSOR5_ID = 'RobotArmSensor5'
M_SENSOR6_ID = 'RobotArmSensor6'

M_TARGET1_ID = 'RobotArmTarget1'
M_TARGET2_ID = 'RobotArmTarget2'
M_TARGET3_ID = 'RobotArmTarget3'
M_TARGET4_ID = 'RobotArmTarget4'
M_TARGET5_ID = 'RobotArmTarget5'
M_TARGET6_ID = 'RobotArmTarget6'

CUBE_POS_X = 'CubePosX'
CUBE_POS_Y  = 'CubePosY'
CUBE_POS_Z  = 'CubePosZ'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class opcuaServerThread(threading.Thread):
    """ OPC-UA server thread class for host the PLC or RTU data and provide to clients."""

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.server = opcuaComm.opcuaServer(SERVER_NAME, NAME_SPACE)

    #-----------------------------------------------------------------------------
    async def initDataStorage(self):
        await self.server.initServer()
        # Add the variables.
        await self.server.addObject(NAME_SPACE, OBJ_NAME)
        idx = self.server.getNameSpaceIdx(NAME_SPACE)
        # Add the sensor variables
        await self.server.addVariable(idx, OBJ_NAME, M_SENSOR1_ID, gv.gMotoAngle1)
        await self.server.addVariable(idx, OBJ_NAME, M_SENSOR2_ID, gv.gMotoAngle2)
        await self.server.addVariable(idx, OBJ_NAME, M_SENSOR3_ID, gv.gMotoAngle3)
        await self.server.addVariable(idx, OBJ_NAME, M_SENSOR4_ID, gv.gMotoAngle4)
        await self.server.addVariable(idx, OBJ_NAME, M_SENSOR5_ID, gv.gMotoAngle5)
        await self.server.addVariable(idx, OBJ_NAME, M_SENSOR6_ID, gv.gMotoAngle6)
        # Add the target variables
        await self.server.addVariable(idx, OBJ_NAME, M_TARGET1_ID, gv.gMotoAngle1)
        await self.server.addVariable(idx, OBJ_NAME, M_TARGET2_ID, gv.gMotoAngle2)
        await self.server.addVariable(idx, OBJ_NAME, M_TARGET3_ID, gv.gMotoAngle3)
        await self.server.addVariable(idx, OBJ_NAME, M_TARGET4_ID, gv.gMotoAngle4)
        await self.server.addVariable(idx, OBJ_NAME, M_TARGET5_ID, gv.gMotoAngle5)
        await self.server.addVariable(idx, OBJ_NAME, M_TARGET6_ID, gv.gMotoAngle6)
        # Add the cube position variables
        await self.server.addVariable(idx, OBJ_NAME, CUBE_POS_X, gv.gCubePosX)
        await self.server.addVariable(idx, OBJ_NAME, CUBE_POS_Y, gv.gCubePosY)
        await self.server.addVariable(idx, OBJ_NAME, CUBE_POS_Z, gv.gCubePosZ)
        return True

    def getServer(self):
        return self.server

    def run(self):
        gv.gDebugPrint("OPC-UA server thread start.", logType=gv.LOG_INFO)
        asyncio.run(self.server.runServer())
        gv.gDebugPrint("OPC-UA server thread exit.", logType=gv.LOG_INFO)

    def stop(self):
        self.server.stopServer()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class robotArmCtrlMgr(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.opcuaServerTh = opcuaServerThread(gv.OPCUA_PORT)
        # Current sensor value
        self.motor1Sensor = gv.gMotoAngle1
        self.motor2Sensor = gv.gMotoAngle2
        self.motor3Sensor = gv.gMotoAngle3
        self.motor4Sensor = gv.gMotoAngle4
        self.motor5Sensor = gv.gMotoAngle5
        self.motor6Sensor = gv.gMotoAngle6
        # Current target value
        self.motor1Angle = gv.gMotoAngle1
        self.motor2Angle = gv.gMotoAngle2
        self.motor3Angle = gv.gMotoAngle3
        self.motor4Angle = gv.gMotoAngle4
        self.motor5Angle = gv.gMotoAngle5
        self.motor6Angle = gv.gMotoAngle6
        # 
        self.terminate = False

    #-----------------------------------------------------------------------------
    async def controlLoop(self):
        await self.opcuaServerTh.initDataStorage()
        self.opcuaServerTh.start()
        time.sleep(1)
        while not self.terminate:
            # get the sensor value from the robot arm
            self.motor1Sensor = gv.iRobotArmObj.theta1
            self.motor2Sensor = gv.iRobotArmObj.theta2
            self.motor3Sensor = gv.iRobotArmObj.theta3
            self.motor4Sensor = gv.iRobotArmObj.theta4
            self.motor5Sensor = gv.iRobotArmObj.theta5
            self.motor6Sensor = gv.iRobotArmObj.gripper_open
            # update the sensor value
            await self.opcuaServerTh.getServer().updateVariable(M_SENSOR1_ID, self.motor1Sensor)
            await self.opcuaServerTh.getServer().updateVariable(M_SENSOR2_ID, self.motor2Sensor)
            await self.opcuaServerTh.getServer().updateVariable(M_SENSOR3_ID, self.motor3Sensor)
            await self.opcuaServerTh.getServer().updateVariable(M_SENSOR4_ID, self.motor4Sensor)
            await self.opcuaServerTh.getServer().updateVariable(M_SENSOR5_ID, self.motor5Sensor)
            await self.opcuaServerTh.getServer().updateVariable(M_SENSOR6_ID, self.motor6Sensor)
            # update the targe value
            self.motor1Angle = await self.opcuaServerTh.getServer().getVariableVal(M_TARGET1_ID)
            self.motor2Angle = await self.opcuaServerTh.getServer().getVariableVal(M_TARGET2_ID)
            self.motor3Angle = await self.opcuaServerTh.getServer().getVariableVal(M_TARGET3_ID)
            self.motor4Angle = await self.opcuaServerTh.getServer().getVariableVal(M_TARGET4_ID)
            self.motor5Angle = await self.opcuaServerTh.getServer().getVariableVal(M_TARGET5_ID)
            self.motor6Angle = await self.opcuaServerTh.getServer().getVariableVal(M_TARGET6_ID)
            # update the cube position

    def run(self):
        gv.gDebugPrint("Robot arm control manager thread start.", logType=gv.LOG_INFO)
        asyncio.run(self.controlLoop())

