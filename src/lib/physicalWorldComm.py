#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        physicalWorldComm.py
#
# Purpose:     Physical world simulation program communication lib module, it 
#              provide the connector running in other PLC/RTU module to fetch
#              or set the real world simulator's electrical signal or sensor.
# 
# Author:      Yuancheng Liu
#
# Version:     v_0.0.1
# Created:     2025/05/18
# Copyright:   Copyright (c) 2025 LiuYuancheng
# License:     MIT License
#-----------------------------------------------------------------------------

import json

import Log  # the module need to work with the lib Log module
import udpCom

RECON_INT = 15          # reconnection time interval default set 30 sec
DEF_PW_PORT = 3001      # default physical world simulator UDP connection port
READ_REQ_KEY = 'GET'    # data read request key
SET_REQ_KEY = 'POST'    # data set request key
RESP_REQ_KEY = 'REP'    # data response request key

ACT_LOGIN_TYPE = 'login'

# Define all the local utility functions here:
#-----------------------------------------------------------------------------
def parseIncomeMsg(msg):
    """ Parse the income message to tuple with 3 elements: request key, type 
        and jsonString. 
    """
    req = msg.decode('UTF-8') if not isinstance(msg, str) else msg
    try:
        reqKey, reqType, reqJsonStr = req.split(';', 2)
        return (reqKey.strip(), reqType.strip(), reqJsonStr)
    except Exception as err:
        Log.error('parseIncomeMsg(): The income message format is incorrect.')
        Log.exception(err)
        return ('', '', json.dumps({}))

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
class PhysicalWorldConnector(object):
    """ Real world simulator connector."""

    def __init__(self, parent, address, deviceID=None, reconnectCount=RECON_INT) -> None:
        """ Init Example: pwConnector = PhysicalWorldConnector(self, ('192.168.1.100', DEF_RW_PORT), deviceID='PLC01')
            Args:
                parent (obj): PLC/RTU/IED object.
                address (tuple): ipaddress pair (ip, port).
                deviceID (int, optional): device ID to login to the physical world. Defaults to None.
                reconnectCount (int, optional): re-connection count. Defaults to RECON_INT.
        """
        self.parent = parent
        self.pwIP = str(address[0])
        self.pwPort = int(address[1])
        self.commClient = udpCom.udpClient((self.pwIP, self.pwPort))
        self.reconnectCount = reconnectCount
        # Test login the real world emulator
        self.deviceID = str(deviceID)
        self.pwOnlineState = self._loginPhysicalWorld(plcID= self.deviceID)

        connMsg = 'Login the physical world successfully.' if self.pwOnlineState else 'Cannot connect to the physical world emulator'
        Log.info(connMsg)

    #-----------------------------------------------------------------------------
    def _queryToPW(self, requestKey, requestType, requestDict):
        """ Query str message send to physical world simulator app.
            Args:
                requestKey (str): request key (GET/POST/REP)
                requestType (str): request type string.
                requestDict (dict): request detail dictionary.
            Returns:
                tuple: (key, type, result) or None if lose connection.
        """
        respKey = respType = respData = None
        if requestKey and requestType and requestDict:
            requestMsg = ';'.join((requestKey, requestType, json.dumps(requestDict)))
            if self.commClient:
                resp = self.commClient.sendMsg(requestMsg, resp=True)
                if resp is not None and len(resp) > 0:
                    respKey, respType, dataStr = parseIncomeMsg(resp)
                    if respKey != 'REP': Log.warning('_queryToPW() - The msg reply key is invalid: %s' % respKey)
                    if respType != requestType: Log.warning('_queryToPW() - The response type not match : %s' %str((requestType, respType)))
                    try:
                        respData = json.loads(dataStr)
                    except Exception as err:
                        Log.exception('_queryToPW() - Load data exception: %s' %str(err))
                        return None
                else:
                    Log.warning("Lost connection to the physical world simulator.")
                    self.pwOnlineState = False
                    return None
        else:
            Log.error("_queryToPW() - input missing: %s" %str((requestKey, requestType, requestDict)))
        return (respKey, respType, respData)

    #-----------------------------------------------------------------------------
    def _loginPhysicalWorld(self, plcID=None):
        """ Try to init connection to the physical world simulation and login 
            with the device ID.
        """
        Log.info("Device try to connect to the physical [%s:%s]..." % (self.pwIP, str(self.pwPort)))
        requestKey, requestType, requestDict = READ_REQ_KEY, ACT_LOGIN_TYPE, {'plcID': self.deviceID}
        result = self._queryToPW(requestKey, requestType, requestDict)
        if result is None:
            Log.warning("Login physical world simulator failed.")
            return False
        elif result and len(result) == 3:
            respKey, respType, respData = result
            if respKey == RESP_REQ_KEY and respType == ACT_LOGIN_TYPE:
                rst = 'state' in respData.keys() and respData['state'] == 'ready'
                Log.info("Login physical world simulator : %s" %str(rst))
                return rst
            else:
                Log.warning("Login physical world simulator failed, response not valid: %s" %str(result))
                return False
        else:
            Log.warning("Login physical world simulator failed, response format not valid: %s" %str(result))
            return False

    #-----------------------------------------------------------------------------
    def getConnectionState(self):
        return self.pwOnlineState

    def getCommClient(self):
        return self.commClient

    #-----------------------------------------------------------------------------
    def getPWItemData(self, requestType='input', dataDict={}):
        """ Return the item's generated data from the physical world emulator under 
            format: (key, requestType, inputResultDict)
        """
        if isinstance(dataDict, dict):
            return self._queryToPW(READ_REQ_KEY, requestType, dataDict)
        Log.warning("getPWItemData(): passed in dataDict parm needs to be a dict() type.")
        return None

    #-----------------------------------------------------------------------------
    def setPWItemState(self, requestType='signals', stateDict={}):
        """ Set the physical world simulator's item state """
        if isinstance(stateDict, dict):
            return self._queryToPW(SET_REQ_KEY, requestType, stateDict)
        Log.warning("setPWItemState(): passed in stateDict parm needs to be a dict() type.get %s" %str(stateDict))
        return None

    #-----------------------------------------------------------------------------
    def reconnectPW(self):
        """ Try to reconnect to the real world emulator."""
        if self.reconnectCount <= 0:
            Log.info('Try to reconnect to the physical world simulator.')
            self.pwOnlineState = self._loginPhysicalWorld(plcID=self.deviceID)
            self.reconnectCount = RECON_INT
            return
        print("Will reconnect to the physical world simulator in %s sec" %str(self.reconnectCount))
        self.reconnectCount -= 1

    #-----------------------------------------------------------------------------
    def stop(self):
        self.commClient.disconnect()
