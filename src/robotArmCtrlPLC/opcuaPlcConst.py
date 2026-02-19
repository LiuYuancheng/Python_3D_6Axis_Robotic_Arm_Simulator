#-----------------------------------------------------------------------------
# Name:        opcuaPlcConst.py
#
# Purpose:     The constant module for the robot arm control OPCUA PLC.
#              
# Author:      Yuancheng Liu
#
# Created:     2026/02/15
# Version:     v_0.0.2
# Copyright:   Copyright (c) 2026 Liu Yuancheng
# License:     GNU General Public License V3
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# PLC communication constants
PLC_LOGIN       = 'login'
PLC_COMM_GET    = 'GET'
PLC_COMM_SET    = 'POST'
PLC_COMM_REP    = 'REP'

# PLC data exchange key
PLC_CUBE_POS    = 'cubePos'
PLC_ARM_ANGLE   = 'armAngle'
PLC_GRIPPER_ON  = 'gripperOn'

# Arm Parameter Key
ARM_POS_TAG     = 'pos'
ARM_ANGLE_TAG   = 'angles'
ARM_GRIP_TAG    = 'gripper'

#-----------------------------------------------------------------------------
# All the OPCUA object variable names
OBJ_NAME = 'RobotArmCtrl' 

VN_GRIPPER_CTRL = 'gripperCtrl'

VN_MOTOR1_CTRL = 'motor1Ctrl'
VN_MOTOR2_CTRL = 'motor2Ctrl'
VN_MOTOR3_CTRL = 'motor3Ctrl'
VN_MOTOR4_CTRL = 'motor4Ctrl'
VN_MOTOR5_CTRL = 'motor5Ctrl'
VN_MOTOR6_CTRL = 'motor6Ctrl'

VN_CUBE_POS_X = 'cubePosX'
VN_CUBE_POS_Y = 'cubePosY'
VN_CUBE_POS_Z = 'cubePosZ'

VN_ARM_ANGLE_1 = 'armAngle1'
VN_ARM_ANGLE_2 = 'armAngle2'
VN_ARM_ANGLE_3 = 'armAngle3'
VN_ARM_ANGLE_4 = 'armAngle4'
VN_ARM_ANGLE_5 = 'armAngle5'
VN_ARM_ANGLE_6 = 'armAngle6'
