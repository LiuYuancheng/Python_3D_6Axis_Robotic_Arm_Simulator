# 3D_6Axis_Robotic_Arm_Simulator with Python-wxPython-OpenGL and OPC-UA

**Project Design Purpose** : The goal of this project is to develop a software-based cyber-physical twin simulation system of the 3D 6-Axis Robotic Arm in OT environment utilizing `Python`, `wxPython`, `OpenGL`, and the `OPC-UA` protocol. The system design follows the international standard automation [ISA-95 (IEC/ISO 62264)](https://www.siemens.com/en-us/technology/isa-95-framework-layers/) and serves as a sophisticated Cyber Twin, bridging the gap between virtual simulation and industrial automation. 

The simulation system include three main modules mirror the ISA-95 automation hierarchy: 1. Robot Arm Simulator (Level 0 - Field Level),  2. Robot Arm OPC-UA PLC (Level 1 - Control Level) and 3. User Remote Controller (Level 2 - Supervisory Level). By integrating real-time physics simulation with industrial communication standards, the project provides a safe, scalable environment for robotics control development and OT security training.

The system overview demo is shown below:

![](doc/img/overview.gif)

```python
# Author:      Yuancheng Liu
# Created:     2026/01/20
# Version:     v_0.0.3
# Copyright:   Copyright (c) 2026 LiuYuancheng
# License:     MIT License
```

**Table of Contents** 

[TOC]

------

### Introduction

The advancement of smart manufacturing and Industrial Control Systems (ICS) has driven the need for realistic, flexible, and secure simulation environments for both development and training purposes. In particular, robotic arms are widely used in modern production lines, where precise control, real-time monitoring, and reliable communication between system layers are critical. The main idea for building this simulation project comes from Prof Liu YaDong's Tutorial : [A Robot Simulator Developed by Python, wxPython, VTK with OPC UA Support](https://youtu.be/zG4QcdsL4rM?si=WMlkdku4BwK09EiY) which published 4 years ago. Because the course doesn't provide the program code and the  robot 3D TLS files used in VTK canvas need to pay, so I use the OpenGL to build a more simple 3D Scene to replace VTK lib with the TLS files. And I added the cube object, the ground cube position sensor and gripper for simulating the scenario of the robot arm to find and grab the cube object. 

Again, many thanks for Prof Liu YaDong to share the insightful course vide on YouTube, if you want to learn the Tutorial below are the YouTube links:

- [Tutorial 0 --- A Robot Simulator Developed by Python, wxPython, VTK with OPC UA Support](https://youtu.be/zG4QcdsL4rM?si=MfSsPUuRWLiKoWmK)
- [Tutorial 1 --- Prepare Python, VTK and wxPython Environment for Robot Simulator Development](https://youtu.be/8NvP5yrUOOI?si=cIi_6sxE1dvtf8JG)
- [Tutorial 2 --- Prepare Robot OPC UA Information Model XML for Python/VTK Robot Simulator Development](https://youtu.be/-TB65k_qBB0?si=CpBeWKdAQhpFYUeZ)
- [Tutorial 3 --- Prepare Robot 3D Model for Python/VTK Robot Simulator Development](https://youtu.be/u3qc_QknfWA?si=vyf9p9UeCPD8qC8j)

#### Introduction of System Architecture

The platform is structured into the basic three primary functional modules that mirror the ISA-95 automation hierarchy as shown below diagram:

![](doc/img/s_03.png)

1. **Robot Arm Simulator (Level 0 - Field Level)** This module provides a 3D OpenGL-rendered interface to visualize the physical robot arm. It simulates hardware components—such as cube position sensors,  servo motors and tactile sensors—allowing for complex actions like object manipulation (e.g., "pick-and-place" operations). It also features a localized control panel for direct manual overrides and real-time state visualization.
2. **Robot Arm OPC-UA PLC (Level 1 - Control Level)** Acting as the brain of the operation, this module simulates an Industrial Programmable Logic Controller (PLC). It processes incoming sensor data from the simulator and dispatches control signals back to the virtual motors, facilitating the logic loop required for autonomous or semi-autonomous motion.
3. **User Remote Controller (Level 2 - Supervisory Level)** This is the Human-Machine Interface (HMI) for the end-user. It establishes a secure connection to the PLC via the OPC-UA protocol, enabling remote monitoring of the arm’s telemetry and the execution of remote commands across a network.



------









Main UI will be like this:

![](doc/img/s_01.png)

```python
# Author:      Yuancheng Liu
# Created:     2026/01/18
# Version:     v_0.0.1
# Copyright:   Copyright (c) 2026 Liu Yuancheng
# License:     MIT License
```

Controller UI:

![](doc/img/s_02.png)

The Idea is from this video:



This module is a simple simulator for a robotic arm by using the wxPython and OpenGL library.







