#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmCtrlMgr.py
#
# Purpose:     This module is the data manager for receive the control command from 
#              the remote controller such as PLC and send the sensor data. 
#
# Author:      Yuancheng Liu
#
# Created:     2026/02/08
# Version:     v_0.0.3
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import time
import json
import threading

import robotArmGlobal as gv
import Log
import udpCom

#-----------------------------------------------------------------------------
# PLC communication constants
PLC_LOGIN = 'login'
PLC_COMM_GET = 'GET'
PLC_COMM_SET = 'POST'
PLC_COMM_REP = 'REP'

# PLC data exchange key
PLC_CUBE_POS = 'cubePos'
PLC_ARM_ANGLE = 'armAngle'
PLC_GRIPPER_ON = 'gripperOn'

# Define all the local utility functions here:
#-----------------------------------------------------------------------------
def parseIncomeMsg(msg):
    """ parse the income message to tuple with 3 elements: request key, type and jsonString
        Args: msg (str): example: 'GET;dataType;{"user":"<username>"}'
    """
    req = msg.decode('UTF-8') if not isinstance(msg, str) else msg
    try:
        reqKey, reqType, reqJsonStr = req.split(';', 2)
        return (reqKey.strip(), reqType.strip(), reqJsonStr)
    except Exception as err:
        Log.error('parseIncomeMsg(): The income message format is incorrect.')
        Log.exception(err)
        return('', '', json.dumps({}))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class robotArmDataMgr(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.terminate = False
        # Init a udp server to accept all the other plc module's data fetch/set request.
        self.server = udpCom.udpServer(None, gv.gUDPPort)
        self.daemon = True
        # Init the request robot arm angles list 
        #self.armAngleReq= [gv.gMotoAngle1, gv.gMotoAngle2, gv.gMotoAngle3, gv.gMotoAngle4,
        #                   gv.gMotoAngle5, gv.gMotoAngle6]
        self.armAngleReq= [25, -10,-50, 0, 0, 20]
    
    #-----------------------------------------------------------------------------
    def _fetchCubePos(self):
        posList = gv.iCubeObj.getPosition()
        respDict = {'pos': posList.copy()}
        return json.dumps(respDict)

    def _fetchArmAngles(self):
        angles = gv.iRobotArmObj.getJointAngles()
        respDict = {'angles': angles.copy()}
        return json.dumps(respDict)

    def getArmAngleRequest(self):
        return self.armAngleReq

    #-----------------------------------------------------------------------------
    def setArmAngleParm(self, reqJsonStr):
        """ Accept and handle weather state clients' weather change request."""
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            gv.gDebugPrint("setArmAngleParm(): accept motor angles set state: %s" %reqJsonStr, 
                           logType=gv.LOG_INFO)
            self.armAngleReq = list(reqDict['angles']).copy()
            respStr = json.dumps({'result': 'success'})
        except Exception as err:
            gv.gDebugPrint("setArmAngleParm() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr
    
    #-----------------------------------------------------------------------------
    def setGripperParm(self, reqJsonStr):
        """ Accept and handle weather state clients' weather change request."""
        respStr = json.dumps({'result': 'failed'})
        try:
            reqDict = json.loads(reqJsonStr)
            gv.gDebugPrint("setGripperParm(): accept gripper close state : %s" %reqJsonStr, 
                           logType=gv.LOG_INFO)
            if bool(reqDict['gripper']): 
                gv.iMainFrame.OnGrabCube(None)
            else:
                gv.iMainFrame.OnReleaseCube(None)
            respStr = json.dumps({'result': 'success'})
        except Exception as err:
            gv.gDebugPrint("setWeatherParm() Error: %s" %str(err), logType=gv.LOG_EXCEPT)
        return respStr

   #-----------------------------------------------------------------------------
    def msgHandler(self, msg):
        """ Function to handle the data-fetch/control request from the monitor-hub.
            Args:
                msg (str/bytes): incoming data from PLC modules though UDP.
            Returns:
                bytes: message bytes needs to reply to the PLC.
        """
        gv.gDebugPrint("Incoming message: %s" % str(msg), logType=gv.LOG_INFO)
        if msg == b'': return None
        # request message format: 
        # data fetch: GET:<key>:<val1>:<val2>...
        # data set: POST:<key>:<val1>:<val2>...
        resp = b'REP;deny;{}'
        (reqKey, reqType, reqJsonStr) = parseIncomeMsg(msg)
        if reqKey==PLC_COMM_GET:
            if reqType == PLC_LOGIN:
                resp = ';'.join((PLC_COMM_REP, PLC_LOGIN, json.dumps({'state':'ready'})))
            elif reqType == PLC_CUBE_POS:
                respStr = self._fetchCubePos()
                resp =';'.join((PLC_COMM_REP, PLC_CUBE_POS, respStr))
            elif reqType == PLC_ARM_ANGLE:
                respStr = self._fetchArmAngles()
                resp =';'.join((PLC_COMM_REP, PLC_ARM_ANGLE, respStr))
        elif reqKey== PLC_COMM_SET:
            if reqType == PLC_ARM_ANGLE:
                respStr = self.setArmAngleParm(reqJsonStr)
                resp =';'.join((PLC_COMM_REP, PLC_COMM_SET, respStr))
            elif reqType == PLC_GRIPPER_ON:
                respStr = self.setGripperParm(reqJsonStr)
                resp =';'.join((PLC_COMM_REP, PLC_COMM_SET, respStr))
            # TODO: Handle all the control request here.
        if isinstance(resp, str): resp = resp.encode('utf-8')
        #gv.gDebugPrint('reply: %s' %str(resp), logType=gv.LOG_INFO)
        return resp

    #-----------------------------------------------------------------------------
    def run(self):
        """ Thread run() function will be called by start(). """
        time.sleep(1)
        gv.gDebugPrint("DataManager sub-thread started.", logType=gv.LOG_INFO)
        self.server.serverStart(handler=self.msgHandler)
        gv.gDebugPrint("DataManager running finished.", logType=gv.LOG_INFO)

    #-----------------------------------------------------------------------------
    def stop(self):
        """ Stop the thread."""
        self.terminate = True
        if self.server: self.server.serverStop()
        endClient = udpCom.udpClient(('127.0.0.1', gv.UDP_PORT))
        endClient.disconnect()
        endClient = None