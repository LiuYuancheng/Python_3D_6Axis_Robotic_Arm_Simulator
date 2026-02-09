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

import asyncio
import threading
import robotArmGlobal as gv
import opcuaComm

SERVER_NAME = 'Robot Arm Control Server'
NAME_SPACE = 'newNameSpace01'
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
class robotArmCtrlMgr(object):

    def __init__(self):
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

