#!/usr/bin/python
#-----------------------------------------------------------------------------
# Name:        robotArmGlobal.py
#
# Purpose:     This module is a simple simulator for a 3D 6Axis robotic arm by 
#              using the wxPython and OpenGL library.
#
# Author:      Yuancheng Liu
#
# Created:     2026/01/20
# Version:     v_0.0.1
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
IMG_DIR = os.path.join(DIR_PATH, 'img')

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

# Init the log type parameters.
DEBUG_FLG   = False
LOG_INFO    = 0
LOG_WARN    = 1
LOG_ERR     = 2
LOG_EXCEPT  = 3

#-------<GLOBAL VARIABLES (start with "g")>------------------------------------
# VARIABLES are the built in data type.
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

gCanvasBgColor = (0.15, 0.15, 0.15, 1.0)
# Arm Link lengths
gArmBaseLen = 2.0
gArmShoulderLen = 1.5
gArmElbowLen = 1.0
gArmWristLen = 0.5