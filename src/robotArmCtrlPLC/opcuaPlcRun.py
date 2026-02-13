#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        opcuaPlcRun.py
#
# Purpose:     A simple OPC-UA plc simulation module to connect to the robot 
#              arm simulator to fetch the sensor information and send the motor
#              control command.
# 
# Author:      Yuancheng Liu
#
# Created:     2026/02/04
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2026 Liu Yuancheng
# License:     GNU General Public License V3
#-----------------------------------------------------------------------------

import time
import asyncio
import threading

import opcuaPlcGlobal as gv
import opcuaPlcConst as ct
import physicalWorldComm
import opcuaComm

OBJ_NAME = 'RobotArmCtrl' 

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class opcuaService(threading.Thread):
    """ OPC-UA server thread class for host the PLC or RTU data and provide 
        to clients.
    """
    def __init__(self, parent, threadID, port=4840):
        threading.Thread.__init__(self)
        self.parent = parent
        self.threadID = threadID
        self.nameSpace = gv.gUAnamespace
        self.port = int(port)
        self.server = opcuaComm.opcuaServer(gv.gPlcName, self.nameSpace, port=self.port)
        gv.gDebugPrint("OPC-UA service thread inited with serverName=%s, port=%s, nameSpace=%s" 
                       % (gv.gPlcName, str(port), self.nameSpace), logType=gv.LOG_INFO)
        
    #-----------------------------------------------------------------------------
    async def initDataStorage(self):
        await self.server.initServer()
        # Add the plan1 
        await self.server.addObject(self.nameSpace, OBJ_NAME)
        idx = self.server.getNameSpaceIdx(self.nameSpace)
        # Add the cube sensor variable
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_CUBE_POS_X, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_CUBE_POS_Y, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_CUBE_POS_Z, 0.0)
        # Add the arm angle sensor variable
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_ARM_ANGLE_1, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_ARM_ANGLE_2, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_ARM_ANGLE_3, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_ARM_ANGLE_4, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_ARM_ANGLE_5, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_ARM_ANGLE_6, 0.0)
        # Add gripper control variable
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_GRIPPER_CTRL, False)
        # Add the arm control request variable
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_MOTOR1_CTRL, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_MOTOR2_CTRL, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_MOTOR3_CTRL, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_MOTOR4_CTRL, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_MOTOR5_CTRL, 0.0)
        await self.server.addVariable(idx, OBJ_NAME, ct.VN_MOTOR6_CTRL, 0.0)

        return True

    #-----------------------------------------------------------------------------
    def getServer(self):
        return self.server

    def run(self):
        asyncio.run(self.server.runServer())
        print("OPC-UA server thread exit.")

    def stop(self):
        self.server.stopServer()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class opcuaPlcSimulator(object):
    """ PLC simulator to simulate the function of the ADS-B controller. """
    def __init__(self, parent, plcID, physicalWorldAddr, updateInt=1):
        """ 
            Args:
                parent (obj): _description_
                plcID (_type_): _description_
                physicalWorldAddr (tuple): (ipAddress, portNum) to link to the 
                    physical world simulation program.
                updateInt (float, optional): _description_. Defaults to 0.5.
        """
        self.parent = parent
        self.plcID = plcID
        self.physicalWorldAddr = physicalWorldAddr
        self.updateInt = updateInt
        self.pwConnector = physicalWorldComm.PhysicalWorldConnector(self, self.physicalWorldAddr,
                                                                    deviceID=self.plcID,
                                                                    reconnectCount=gv.gReconnectTime)
        self.opcuaServerTh = opcuaService(self, "opcuaServerTh", port=gv.gPlcHostIP[1])
        self.dataVariableDict = None
        self.controlVariableDict = None
        self.initFlag = True
        self.sendArmCtrlFlag = False # send the robot arm control command flag.
        self.sendGripperCtrlFlag = False # send the gripper control command flag.
        self._initPLCInternalVariables()
        self.terminate = False

    #-----------------------------------------------------------------------------
    def _initPLCInternalVariables(self):
        # Init all the variables input into the PLC.
        self.dataVariableDict = {
            ct.VN_CUBE_POS_X : 0.0,
            ct.VN_CUBE_POS_Y : 0.0,
            ct.VN_CUBE_POS_Z : 0.0,
            ct.VN_ARM_ANGLE_1 : 0.0,
            ct.VN_ARM_ANGLE_2 : 0.0,
            ct.VN_ARM_ANGLE_3 : 0.0,
            ct.VN_ARM_ANGLE_4 : 0.0,
            ct.VN_ARM_ANGLE_5 : 0.0,
            ct.VN_ARM_ANGLE_6 : 0.0
        }
        # init the final variable output PLC try to send to antenna to broadcast
        self.controlVariableDict = {
            ct.VN_GRIPPER_CTRL : False,
            ct.VN_MOTOR1_CTRL : 0,
            ct.VN_MOTOR2_CTRL : 0,
            ct.VN_MOTOR3_CTRL : 0,
            ct.VN_MOTOR4_CTRL : 0,
            ct.VN_MOTOR5_CTRL : 0,
            ct.VN_MOTOR6_CTRL : 0
        }       

    #-----------------------------------------------------------------------------
    def getCubeSensorData(self):
        requestDict = {'pos': None}
        _, _, result = self.pwConnector.getPWItemData(requestType=ct.PLC_CUBE_POS,
                                                      dataDict=requestDict)
        print(result)
        self.dataVariableDict[ct.VN_CUBE_POS_X] = result['pos'][0]
        self.dataVariableDict[ct.VN_CUBE_POS_Y] = result['pos'][1]
        self.dataVariableDict[ct.VN_CUBE_POS_Z] = result['pos'][2]
        return result

    def getArmSensorData(self):
        requestDict = {'angles': None}
        _, _, result = self.pwConnector.getPWItemData(requestType=ct.PLC_ARM_ANGLE,
                                                      dataDict=requestDict)
        self.dataVariableDict[ct.VN_ARM_ANGLE_1] = result['angles'][0]
        self.dataVariableDict[ct.VN_ARM_ANGLE_2] = result['angles'][1]
        self.dataVariableDict[ct.VN_ARM_ANGLE_3] = result['angles'][2]
        self.dataVariableDict[ct.VN_ARM_ANGLE_4] = result['angles'][3]
        self.dataVariableDict[ct.VN_ARM_ANGLE_5] = result['angles'][4]
        self.dataVariableDict[ct.VN_ARM_ANGLE_6] = result['angles'][5]
        return result
    
    def synchronizeData(self):
        self.controlVariableDict[ct.VN_MOTOR1_CTRL] = self.dataVariableDict[ct.VN_ARM_ANGLE_1]
        self.controlVariableDict[ct.VN_MOTOR2_CTRL] = self.dataVariableDict[ct.VN_ARM_ANGLE_2]
        self.controlVariableDict[ct.VN_MOTOR3_CTRL] = self.dataVariableDict[ct.VN_ARM_ANGLE_3]
        self.controlVariableDict[ct.VN_MOTOR4_CTRL] = self.dataVariableDict[ct.VN_ARM_ANGLE_4]
        self.controlVariableDict[ct.VN_MOTOR5_CTRL] = self.dataVariableDict[ct.VN_ARM_ANGLE_5]
        self.controlVariableDict[ct.VN_MOTOR6_CTRL] = self.dataVariableDict[ct.VN_ARM_ANGLE_6]
          
    #-----------------------------------------------------------------------------
    def setSimulatorArmState(self):
        """ Send the message need to broadcast back to the physical world simulator. """

        reqList = [
            self.controlVariableDict[ct.VN_MOTOR1_CTRL],
            self.controlVariableDict[ct.VN_MOTOR2_CTRL],
            self.controlVariableDict[ct.VN_MOTOR3_CTRL],
            self.controlVariableDict[ct.VN_MOTOR4_CTRL],
            self.controlVariableDict[ct.VN_MOTOR5_CTRL],
            self.controlVariableDict[ct.VN_MOTOR6_CTRL]
        ]
        requestDict = { 'angles' : reqList}
        gv.gDebugPrint("setSimulatorArmState: requestDict = %s")
        result =  self.pwConnector.setPWItemState(requestType=ct.PLC_ARM_ANGLE, 
                                                stateDict=requestDict)
        return result

    #-----------------------------------------------------------------------------
    def setSimulatorGripperState(self):
        """ Send the message need to broadcast back to the physical world simulator. """
        requestDict = { 'gripper' : self.controlVariableDict[ct.VN_GRIPPER_CTRL]}
        gv.gDebugPrint("setSimulatorGripperState: requestDict = %s")
        result =  self.pwConnector.setPWItemState(requestType=ct.PLC_GRIPPER, 
                                                stateDict=requestDict)
        return result

    #-----------------------------------------------------------------------------
    async def run(self):
        await self.opcuaServerTh.initDataStorage()
        self.opcuaServerTh.start()
        time.sleep(1)
        while not self.terminate:
            # simulate fetch real world simulator's components data
            self.getCubeSensorData()
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_CUBE_POS_X, float(self.dataVariableDict[ct.VN_CUBE_POS_X]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_CUBE_POS_Y, float(self.dataVariableDict[ct.VN_CUBE_POS_Y]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_CUBE_POS_Z, float(self.dataVariableDict[ct.VN_CUBE_POS_Z]))
            self.getArmSensorData()
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_ARM_ANGLE_1, float(self.dataVariableDict[ct.VN_ARM_ANGLE_1]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_ARM_ANGLE_2, float(self.dataVariableDict[ct.VN_ARM_ANGLE_2]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_ARM_ANGLE_3, float(self.dataVariableDict[ct.VN_ARM_ANGLE_3]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_ARM_ANGLE_4, float(self.dataVariableDict[ct.VN_ARM_ANGLE_4]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_ARM_ANGLE_5, float(self.dataVariableDict[ct.VN_ARM_ANGLE_5]))
            await self.opcuaServerTh.getServer().updateVariable(ct.VN_ARM_ANGLE_6, float(self.dataVariableDict[ct.VN_ARM_ANGLE_6]))
            print(str(self.dataVariableDict))
            if self.initFlag:
                self.initFlag = False
                self.synchronizeData()
                await self.opcuaServerTh.getServer().updateVariable(ct.VN_MOTOR1_CTRL, float(self.controlVariableDict[ct.VN_MOTOR1_CTRL]))
                await self.opcuaServerTh.getServer().updateVariable(ct.VN_MOTOR2_CTRL, float(self.controlVariableDict[ct.VN_MOTOR2_CTRL]))
                await self.opcuaServerTh.getServer().updateVariable(ct.VN_MOTOR3_CTRL, float(self.controlVariableDict[ct.VN_MOTOR3_CTRL]))
                await self.opcuaServerTh.getServer().updateVariable(ct.VN_MOTOR4_CTRL, float(self.controlVariableDict[ct.VN_MOTOR4_CTRL]))
                await self.opcuaServerTh.getServer().updateVariable(ct.VN_MOTOR5_CTRL, float(self.controlVariableDict[ct.VN_MOTOR5_CTRL]))
                await self.opcuaServerTh.getServer().updateVariable(ct.VN_MOTOR6_CTRL, float(self.controlVariableDict[ct.VN_MOTOR6_CTRL]))

            r0 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_GRIPPER_CTRL)
            if r0 != self.controlVariableDict[ct.VN_GRIPPER_CTRL]:
                self.controlVariableDict[ct.VN_GRIPPER_CTRL] = r0
                self.sendGripperCtrlFlag = True

            r1 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_MOTOR1_CTRL)
            if int(r1) != int(self.controlVariableDict[ct.VN_MOTOR1_CTRL]):
                self.controlVariableDict[ct.VN_MOTOR1_CTRL] = r1
                self.sendCmdFlag = True

            r2 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_MOTOR2_CTRL)
            if int(r2) != int(self.controlVariableDict[ct.VN_MOTOR2_CTRL]):
                self.controlVariableDict[ct.VN_MOTOR2_CTRL] = r2
                self.sendCmdFlag = True

            r3 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_MOTOR3_CTRL)
            if int(r3) != int(self.controlVariableDict[ct.VN_MOTOR3_CTRL]):
                self.controlVariableDict[ct.VN_MOTOR3_CTRL] = r3
                self.sendCmdFlag = True

            r4 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_MOTOR4_CTRL)
            if int(r4) != int(self.controlVariableDict[ct.VN_MOTOR4_CTRL]):
                self.controlVariableDict[ct.VN_MOTOR4_CTRL] = r4
                self.sendCmdFlag = True

            r5 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_MOTOR5_CTRL)
            if int(r5) != int(self.controlVariableDict[ct.VN_MOTOR5_CTRL]):
                self.controlVariableDict[ct.VN_MOTOR5_CTRL] = r5
                self.sendCmdFlag = True

            r6 = await self.opcuaServerTh.getServer().getVariableVal(ct.VN_MOTOR6_CTRL)
            if int(r6) != int(self.controlVariableDict[ct.VN_MOTOR6_CTRL]):
                self.controlVariableDict[ct.VN_MOTOR6_CTRL] = r6
                self.sendCmdFlag = True

            if self.sendGripperCtrlFlag:
                self.setSimulatorGripperState()
                self.sendGripperCtrlFlag = False

            if self.sendArmCtrlFlag:
                self.setSimulatorArmState()
                self.sendArmCtrlFlag = False

            time.sleep(self.updateInt)
        print("PLC simulator thread exit.")

    #-----------------------------------------------------------------------------
    def stop(self):
        self.terminate = True
        self.opcuaServerTh.stop()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    plcObj = opcuaPlcSimulator(None, gv.gPlcName, gv.gRealWorldIP, 
                               updateInt=gv.gInterval)
    asyncio.run(plcObj.run())
