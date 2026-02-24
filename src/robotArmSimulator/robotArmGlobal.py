#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmGlobal.py
#
# Purpose:     This module is used as a local config file to set constants, 
#              global parameters which will be used in the other modules.
#
# Author:      Yuancheng Liu
#
# Created:     2026/01/20
# Version:     v_0.0.3
# Copyright:   Copyright (c) 2026 LiuYuancheng
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
DIR_PATH = dirpath = os.path.dirname(os.path.abspath(__file__))
print("Current source code location : %s" % dirpath)
APP_NAME = ('RobotArm', 'Simulator')

TOP_DIR = 'src'
LIB_DIR = 'lib'
#IMG_DIR = os.path.join(DIR_PATH, 'img')

idx = dirpath.rfind(TOP_DIR)
gTopDir = dirpath[:idx + len(TOP_DIR)] if idx != -1 else dirpath   # found it - truncate right after TOPDIR
# Config the lib folder 
gLibDir = os.path.join(gTopDir, LIB_DIR)
if os.path.exists(gLibDir):
    sys.path.insert(0, gLibDir)
import Log
Log.initLogger(gTopDir, 'Logs', APP_NAME[0], APP_NAME[1], historyCnt=100, fPutLogsUnderDate=True)

#-----------------------------------------------------------------------------
# load the config file.
import ConfigLoader
CONFIG_FILE_NAME = 'robotArmSimulatorConfig.txt'
gConfigPath = os.path.join(dirpath, CONFIG_FILE_NAME)
iConfigLoader = ConfigLoader.ConfigLoader(gConfigPath, mode='r')
if iConfigLoader is None:
    print("Error: The config file %s is not exist.Program exit!" %str(gConfigPath))
    exit()
CONFIG_DICT = iConfigLoader.getJson()
UI_TITLE = CONFIG_DICT['UI_TITLE']
UDP_PORT = 3001 # default UPD channel port.
# Init the log type parameters.
DEBUG_FLG   = False
LOG_INFO    = 0
LOG_WARN    = 1
LOG_ERR     = 2
LOG_EXCEPT  = 3

#-------<GLOBAL VARIABLES (start with "g")>------------------------------------
# VARIABLES are the built in data type.
def gDebugPrint(msg, prt=True, logType=LOG_INFO):
    if prt: print(msg)
    if logType == LOG_WARN:
        Log.warning(msg)
    elif logType == LOG_ERR:
        Log.error(msg)
    elif logType == LOG_EXCEPT:
        Log.exception(msg)
    elif logType == LOG_INFO or DEBUG_FLG:
        Log.info(msg)

gTestMD = CONFIG_DICT['TEST_MD']
gUDPPort = int(CONFIG_DICT['UDP_PORT']) if 'UDP_PORT' in CONFIG_DICT.keys() else UDP_PORT
gCanvasBgColor = (0.15, 0.15, 0.15, 1.0)    # Default canvas background color
# Arm Link lengths
gArmBaseLen = 2.0
gArmShoulderLen = 1.5
gArmElbowLen = 1.0
gArmWristLen = 0.5
# Arm theta init angles
gMotoAngle1 = 45.0
gMotoAngle2 = -15.0
gMotoAngle3 = 30.0
gMotoAngle4 = 0.0
gMotoAngle5 = 0.0
gMotoAngle6 = 50.0
gMotorDegSpeed = 5 # The moving speed of the motor.
# Cube init position in the canvas
gCubePosX = 2.0
gCubePosY = 1.0
gCubePosZ = 0.3

#-------</GLOBAL VARIABLES (start with "g")>------------------------------------
iRobotArmObj = None
iCubeObj = None
iDataManager = None
iMainFrame = None