#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmCtrlManger.py
#
# Purpose:     This module is the data manager module also used for handling 
#              the serial communication ( send the control request to Arduino and 
#              and fetch the potentiometer data).
#
# Author:      Yuancheng Liu
#
# Version:     v_0.0.1
# Created:     2026/02/11
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License  
#-----------------------------------------------------------------------------
import os 
import json
import time
import asyncio
from queue import Queue
import threading
import BraccioCtrlGlobal as gv
import robotArmCtrlConst as ct
import opcuaComm

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class plcDataManager(threading.Thread):
    """ The data manager is a module running parallel with the main thread to 
        connect to PLCs to do the data communication with IEC-104.
    """
    def __init__(self, parent) -> None:
        threading.Thread.__init__(self)
        self.parent = parent
        self.terminate = False
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
        # Init the OPC-UA connector
        serverUrl = "opc.tcp://%s:%s/%s/server/" %(gv.gPlcDict['ip'], str(gv.gPlcDict['port']), gv.gPlcDict['id'])
        self.armOPCUAclient = opcuaComm.opcuaClient(serverUrl, timeout=4, watchdog_interval=10)

    #-----------------------------------------------------------------------------
    def run(self):
        """ Thread run() function will be called by start(). """
        time.sleep(1)
        #gv.gDebugPrint('Management HMI PLC dataMgr run() loop start.', logType=gv.LOG_INFO)
        #while not self.terminate:
        #    self.periodic(time.time())
        #    time.sleep(2)
        asyncio.run(self.plcDataProcessLoop())


    def periodic(self, curTime):
        """ Periodic function to check the connection status and update the 
            PLC data dict.
        """
        pass

    #-----------------------------------------------------------------------------
    async def plcDataProcessLoop(self):
        await self.armOPCUAclient.connect()
        while not self.terminate:
            # Fetch data from IEC104 PLC(s)
            self.periodic(time.time())
            # Fetch cube sensor data from OPC-UA controller.
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_CUBE_POS_X)
            self.dataVariableDict[ct.VN_CUBE_POS_X] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_CUBE_POS_Y)
            self.dataVariableDict[ct.VN_CUBE_POS_Y] = round(val, 1)
            val = await self.armOPCUAclient.getVariableVal(gv.gUAnamespace, ct.OBJ_NAME, ct.VN_CUBE_POS_Z)
            self.dataVariableDict[ct.VN_CUBE_POS_Z] = round(val, 1)
            print(str(self.dataVariableDict))
            time.sleep(0.4)            
        await self.armOPCUAclient.disconnect()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
# class CtrlManager(object):
#     """ Control manager parent class"""

#     def __init__(self, maxQsz=MAX_QSZ) -> None:
#         self.connector = None
#         self.taskQueue = Queue(maxsize=MAX_QSZ)

#     def _enqueueTask(self, taskStr):
#         if self.taskQueue.full():
#             print("Tasks queue full, can not add cmd: %s" % str(taskStr))
#             return
#         self.taskQueue.put(taskStr)

#     def _dequeuTask(self):
#         return None if self.taskQueue.empty() else self.taskQueue.get_nowait()

#     def addTasks(self, tasklist):
#         """ Add the input tasks string list into the tasks queue."""
#         for cmd in tasklist:
#             self._enqueueTask(cmd)

#     def hasQueuedTask(self):
#         return not self.taskQueue.empty()

#     def getConnection(self):
#         if self.connector: return self.connector.isConnected()
#         return False
     
#     def stop(self):
#         if self.connector: self.connector.close()

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

# class connectionHandler(threading.Thread):

#     def __init__(self, parent) -> None:
#         threading.Thread.__init__(self)
#         self.parent = parent
#         self.server = udpCom.udpServer(None, gv.gHostPort)
#         #self.server.setBufferSize(bufferSize=gv.BUF_SZ)
#         # load face demo tasks list.
#         self.tasksList1 = []
#         actConfigPath = os.path.join(gv.SCE_FD, 'collectBox.json')
#         if os.path.exists(actConfigPath):
#             with open(actConfigPath) as json_file:
#                 self.tasksList1 = json.load(json_file)
#                 print("loaded the face demo scenario")
#         # load grab near task list
#         self.tasksList2 = []
#         actConfigPath = os.path.join(gv.SCE_FD, 'grabNear.json')
#         if os.path.exists(actConfigPath):
#             with open(actConfigPath) as json_file:
#                 self.tasksList2 = json.load(json_file)
#                 print("loaded the grab near demo scenario")

#         # load grab far task list 
#         self.tasksList3 = []
#         actConfigPath = os.path.join(gv.SCE_FD, 'grabFar.json')
#         if os.path.exists(actConfigPath):
#             with open(actConfigPath) as json_file:
#                 self.tasksList3 = json.load(json_file)
#                 print("loaded the grab far demo scenario")

#     #-----------------------------------------------------------------------------
#     def run(self):
#         print("Start the trojanReceiverMgr.")
#         print("Start the UDP echo server listening port [%s]" % str(UDP_PORT))
#         self.server.serverStart(handler=self.cmdHandler)
    
#     #-----------------------------------------------------------------------------
#     def parseIncomeMsg(self, msg):
#         """ Split the trojan connection's control cmd to:
#             - reqKey: request key which idenfiy the action category.
#             - reqType: request type which detail action type.
#             - reqData: request data which will be used in the action.
#         """
#         reqKey = reqType = reqData = None
#         try:
#             if isinstance(msg, bytes): msg = msg.decode('utf-8')
#             reqKey, reqType, reqData = msg.split(';', 2)
#             return (reqKey.strip(), reqType.strip(), reqData)
#         except Exception as err:
#             print('The incoming message format is incorrect, ignore it.')
#             print(err)
#             return (reqKey, reqType, reqData)
        
#     #-----------------------------------------------------------------------------
#     def cmdHandler(self, msg):
#         """ The trojan report handler method passed into the UDP server to handle the 
#             incoming messages.
#         """
#         if isinstance(msg, bytes): msg = msg.decode('utf-8')
#         print("incoming message: %s" %str(msg))
#         if msg == '': return None
#         resp = "busy"
#         if 'demo' in msg and gv.iCtrlManger :
#             tasksList = None 
#             if msg == 'demo1': tasksList = self.tasksList1
#             if msg == 'demo2': tasksList = self.tasksList2
#             if msg == 'demo3': tasksList = self.tasksList3

#             if not gv.iCtrlManger.hasQueuedTask():
#                 if tasksList and len(tasksList) > 0:
#                     print("Execute scenario: demo.json")
#                     for action in tasksList:
#                         if action['act'] == 'RST':
#                             gv.iCtrlManger.addRestTask()
#                         elif action['act'] == 'MOV':
#                             gv.iCtrlManger.addMotorMovTask(action['key'], action['val'])
#                     resp = "ready"
#         return resp