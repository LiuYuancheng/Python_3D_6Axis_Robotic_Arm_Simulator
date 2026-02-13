#-----------------------------------------------------------------------------
# Name:        robotArmCtrlGlobal.py
#
# Purpose:     This module is used as a local config file to set constants, 
#              global parameters which will be used in the other modules.
#              
# Author:      Yuancheng Liu
#
# Created:     2020/01/10
# Version:     v0.1.2
# Copyright:   Copyright (c) 2023 LiuYuancheng
# License:     MIT License 
#-----------------------------------------------------------------------------
"""
For good coding practice, follow the following naming convention:
    1) Global variables should be defined with initial character 'g'
    2) Global instances should be defined with initial character 'i'
    2) Global CONSTANTS should be defined with UPPER_CASE letters
"""
import os, sys

print("Current working directory is : %s" % os.getcwd())
dirpath = os.path.dirname(__file__)
print("Current source code location : %s" % dirpath)
APP_NAME = ('Controller', 'remoteController')

TOPDIR = 'src'
LIBDIR = 'lib'
CONFIG_FILE_NAME = 'controllerConfig.txt'

IMG_FD = 'img'
ICO_PATH = os.path.join(dirpath, IMG_FD, "icon.png")
BGIMG_PATH = os.path.join(dirpath, IMG_FD, "background.png")
SCE_FD = os.path.join(dirpath, 'Scenarios')

#-----------------------------------------------------------------------------
# find the lib directory
idx = dirpath.find(TOPDIR)
gTopDir = dirpath[:idx + len(TOPDIR)] if idx != -1 else dirpath   # found it - truncate right after TOPDIR
# Config the lib folder 
gLibDir = os.path.join(gTopDir, LIBDIR)
if os.path.exists(gLibDir):
    sys.path.insert(0, gLibDir)

#-----------------------------------------------------------------------------
# Init the logger:
import Log
Log.initLogger(gTopDir, 'Logs', APP_NAME[0], APP_NAME[1], historyCnt=100, fPutLogsUnderDate=True)

# Init the log type parameters.
DEBUG_FLG   = False
LOG_INFO    = 0
LOG_WARN    = 1
LOG_ERR     = 2
LOG_EXCEPT  = 3

def gDebugPrint(msg, prt=True, logType=None):
    if prt: print(msg)
    if logType == LOG_WARN:
        Log.warning(msg)
    elif logType == LOG_ERR:
        Log.error(msg)
    elif logType == LOG_EXCEPT:
        Log.exception(msg)
    elif logType == LOG_INFO or DEBUG_FLG:
        Log.info(msg)

#-----------------------------------------------------------------------------
# Init the configure file loader.
import ConfigLoader
gGonfigPath = os.path.join(dirpath, CONFIG_FILE_NAME)
iConfigLoader = ConfigLoader.ConfigLoader(gGonfigPath, mode='r')
if iConfigLoader is None:
    print("Error: The config file %s is not exist.Program exit!" %str(gGonfigPath))
    exit()
CONFIG_DICT = iConfigLoader.getJson()

#------<GLOBAL CONSTANTS>-------------------------------------------------------------
STR_DECODE = 'utf-8'
DEBUG = True

#-------<GLOBAL VARIABLES (start with "g")>------------------------------------
# VARIABLES are the built in data type.
gTestMD = CONFIG_DICT['TEST_MD']
gComPort = CONFIG_DICT['COM_PORT']
gbaudRate = CONFIG_DICT['COM_RATE']

gUpdateRate = 0.2     # main frame update rate 1 sec.
gHostAct = CONFIG_DICT['UDP_HOST']
gHostPort = int(CONFIG_DICT['UDP_PORT'])

gUAnamespace = 'Controller'
gPlcDict = {
    'id' : CONFIG_DICT['OPCUA_PLC_ID'],
    'ip' : CONFIG_DICT['OPCUA_PLC_IP'],
    'port' : int(CONFIG_DICT['OPCUA_PLC_PORT']),
}

#-------<GLOBAL PARAMTERS>-----------------------------------------------------
iMainFrame = None   # MainFrame.
iGridPanel = None   # MainFrame grid panel.
iCtrlManger = None
iconnHandler = None
iDataMgr = None