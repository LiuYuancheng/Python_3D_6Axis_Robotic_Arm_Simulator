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

### 1. Introduction

The advancement of smart manufacturing and Industrial Control Systems (ICS) has driven the need for realistic, flexible, and secure simulation environments for both development and training purposes. In particular, robotic arms are widely used in modern production lines, where precise control, real-time monitoring, and reliable communication between system layers are critical. 

This project, **3D_6Axis_Robotic_Arm_Simulator with Python–wxPython–OpenGL and OPC-UA**, is designed to address these needs by providing a lightweight yet functional cyber-physical simulation environment. The system enables users to visualize, monitor, and control a six-axis robotic arm while emulating real industrial communication and control workflows.

#### 1.2 Introduction of Project Background

Two years ago I have created a project to control the Braccio Plus Robot Arm: https://www.linkedin.com/pulse/braccio-plus-robot-arm-controller-yuancheng-liu-h5gfc, but this need to hardware so it it difficult for using in cyber exercise and training which need more than one set of the environment. 

![](doc/img/assemble.png)



The idea for this project is inspired by Prof. Liu YaDong’s course "[A Robot Simulator Developed by Python, wxPython, VTK with OPC UA Support](https://youtu.be/zG4QcdsL4rM?si=WMlkdku4BwK09EiY)", as the course program source code is not publicly available and the 3D model resources TLS file for VTK needs to purchase, I did some modification of the design with simplified approach and free lib and added some additional functions : 

- Use `OpenGL` to replace the `VTK`  to construct a simplified 3D robot arm in the canvas 
- A cube object and related cube position sensor are introduced to simulate realistic interaction scenarios
- A gripper mechanism is implemented to demonstrate object (cube) pick-and-place operations

Special thanks again to Prof. Liu YaDong for sharing the original educational content on YouTube. For reference, the original tutorial series is listed below:

- [Tutorial 0 --- A Robot Simulator Developed by Python, wxPython, VTK with OPC UA Support](https://youtu.be/zG4QcdsL4rM?si=MfSsPUuRWLiKoWmK)
- [Tutorial 1 --- Prepare Python, VTK and wxPython Environment for Robot Simulator Development](https://youtu.be/8NvP5yrUOOI?si=cIi_6sxE1dvtf8JG)
- [Tutorial 2 --- Prepare Robot OPC UA Information Model XML for Python/VTK Robot Simulator Development](https://youtu.be/-TB65k_qBB0?si=CpBeWKdAQhpFYUeZ)
- [Tutorial 3 --- Prepare Robot 3D Model for Python/VTK Robot Simulator Development](https://youtu.be/u3qc_QknfWA?si=vyf9p9UeCPD8qC8j)

#### 1.1 Introduction of System Architecture

The platform is designed based on the ISA-95 automation hierarchy pyramid, extending from Level 0 (field devices) up to Level 4 (enterprise systems). The current implementation focuses on Levels 0–2 as shown below:

![](doc/img/s_03.png)

1. **Robot Arm Simulator (Level 0 - Field Level)** :  This module provides a 3D OpenGL-rendered interface to visualize the physical robot arm. It simulates hardware components—such as cube position sensors,  servo motors and tactile sensors—allowing for complex actions like object manipulation (e.g., "pick-and-place" operations). It also features a localized control panel for direct manual overrides and real-time state visualization.
2. **Robot Arm OPC-UA PLC (Level 1 - Control Level)** : Acting as the brain of the operation, this module simulates an Industrial Programmable Logic Controller (PLC). It processes incoming sensor data from the simulator and dispatches control signals back to the virtual motors, facilitating the logic loop required for autonomous or semi-autonomous motion.
3. **User Remote Controller (Level 2 - Supervisory Level)** : This is the Human-Machine Interface (HMI) for the end-user. It establishes a secure connection to the PLC via the OPC-UA protocol, enabling remote monitoring of the arm’s telemetry and the execution of remote commands across a network.



------

### 2. Project Design

The system is developed using Python, with wxPython for GUI, OpenGL for 3D visualization, and OPC UA (IEC 62541) for standardized industrial communication. It is designed to emulate part of a realistic Operational Technology (OT) robot manufacture environment by integrating simulation, control logic, and supervisory monitoring into a unified platform. 

#### 2.1 System Design Objectives 

The design is guided by the following key objectives:

- **Simulate Realistic OT Behavior** : Recreate the dynamics of a servo motor-driven robotic arm, including multi-joint kinematics, sensor feedback, and actuator responses. The 3D visualization provides an intuitive representation of robot motion and interaction with objects.
- **Enable Remote Monitoring and Control** : Support real-time data exchange and control through OPC UA, allowing users to monitor system states and issue commands from a remote Human-Machine Interface (HMI).
- **Support OT Cybersecurity Training** : Provide a controlled and observable environment for analyzing industrial communication patterns, testing anomaly detection, and simulating potential attacks on PLC–HMI interactions.

#### 2.2  System Workflow Overview

The overall system workflow is illustrated in the diagram below, structured across three OT layers: Level 0 (simulation), Level 1 (PLC control), and Level 2 (supervisory control).

![](doc/img/s_04.png)

**2.2.1 Level 0 → Level 1: Sensor Data Simulation (UDP-based I/O Emulation)**

- The 3D Robot Arm Simulator (blue color section) continuously generates simulated field data, including: Cube position (ground position sensor) and Joint rotation angles (base, shoulder, elbow, wrist, gripper). These values are transmitted to the PLC module using **UDP messages**, which emulate real-world electrical or analog signal acquisition from physical sensors. 
- At the OPC-UA PLC (Level 1) side, the incoming UDP data is mapped to `PLC local input variables`, then the variables are also stored in the OPC UA address space (UA Namespace / UA Objects), for UA data storage type `UA-Int16` → cube coordinate values, `UA-Float` → joint angles, `UA-Bool` → gripper pressure sensor state. 

**2.2.2 Level 1: PLC Decision-Making and Ladder Logic Execution**

The PLC module acts as the core control engine. It is implemented using a virtual PLC framework that supports: adder logic execution and OPC UA server functionality. The control loop operates as follows below steps:

1. Read current sensor values (e.g., joint angles)
2. Compare with target values (from HMI or predefined sequence)
3. Execute control logic to determine required motion
4. Generate output control signals (servo motor commands)

For example If the **target shoulder angle ≠ current angle**, the PLC continuously sends adjustment signals until the sensor feedback matches the desired position. The resulting control signals are transmitted back to the simulator via **UDP**, simulating actuator control signals to servo motors.

**2.2.3 Level 1 → Level 2: OPC UA Communication**

The PLC exposes all relevant data through an **OPC UA server (OPC-UA-TCP)**, including: Joint angles, Cube position, Gripper state and Control commands. Then the **Level 2 HMI/Controller** connects as an OPC UA client and periodically retrieves updated values.

**2.2.4 Level 2: Supervisory Control and Visualization**

The **SCADA/HMI module** provides a user-facing interface for monitoring and control. Its key functions include:

- Real-time Visualization: Joint angles displayed in 6-axis charts, Cube position mapped onto a 2D ground projection and System state monitoring.
- Manual Control: Users can adjust each joint angle via sliders then motor control commands are sent to the PLC through OPC UA.
- Automatic Control (Trajectory Execution) : Users can load predefined action sequences and the system executes repeated pick-and-place operations
- Motion Calculation: The controller estimates whether the robotic arm can reach the target cube and calculate the joint angles to reach the cube.



------

### 3. Implement of Robot Arm Simulator 

This section will introduce the detailed implementation of the robot arm simulator. The simulator main UI frame is build by Wxpython and the Robot arm display is built by OpenGL.GL/GLU/GLUT. The simulator can run independently without the other module as we also provided the local control panel. The detailed UI view and function are marked in the below diagram:

![](doc/img/s_05.png)

#### 3.1 3D scene module implement

The arm includes 4 links: 

| Link Index | Color  | Connection        | Length            |
| ---------- | ------ | ----------------- | ----------------- |
| Link-00    | Red    | Base to shoulder  | length = 2.0 unit |
| Link-01    | Green  | Shoulder to elbow | length = 1.5 unit |
| Link-02    | Blue   | Elbow to wrist    | length = 1.0 unit |
| Link-03    | Yellow |                   |                   |

The robot arm includes 6 joints with the sensors and server motors: 

| Joint Index | Joint Function           | Angle Sensor    | Servo Motor    | Rotate Range  | Control Slider                       |
| ----------- | ------------------------ | --------------- | -------------- | ------------- | ------------------------------------ |
| Axis-0      | Base rotation (X, Y)     | Angle Sensor 01 | Servo Motor 01 | (-180°, 180°) | Base Servo Motor Control             |
| Axis-1      | Shoulder rotation (Y, Z) | Angle Sensor 02 | Servo Motor 02 | (-90°, 90°)   | Should Servo Motor Control           |
| Axis-2      | Elbow rotation (Y, Z)    | Angle Sensor 03 | Servo Motor 03 | (-180°, 180°) | Elbow Servo Motor Control            |
| Axis-3      | Wrist rotation (Y, Z)    | Angle Sensor 04 | Servo Motor 04 | (-90°, 90°)   | Wrist Servo Motor Control            |
| Axis-4      | Gripper rotation (X, Y)  | Angle Sensor 05 | Servo Motor 06 | (-180°, 180°) | Gripper Rotation Servo Motor Control |
| Axis-5      | Gripper opening          | Angle Sensor 06 | Servo Motor 07 | (0°, 100°)    | Gripper Opening Servo Motor Control  |

#### 3.2 Operation Function Implement

The gripper will always point down with the Z-Axis, as the OpenGL lib doesn't provide the physical object interaction function and the gravity function. This is how I implement the functions: 

Grab and release the cube: if the gripper is at the same position of the cube in the 0.04 unit range, when the gripper is closing, the gripper pressure sensor will try to detect the interaction with the cube, if the both griper fingers touch the cube surface, the gripper motor will stop and the arm can grab the cube and angle will not decrease. When the cube is grabbed, its color will be changed to orange color as shown below image. If the user pressed the release button the gripper angle will keep increase until the pressure sensor doesn't get value 0. 

![](doc/img/s_06.png)

Gravity function: If the cube is not grabbed by the Arm, in the system main FPS refresh loop, it will keep decrease the cube Z coordinate until the cube button touch the ground. 

The calculated gripper position and the   cube position sensor's reading will also shown at the local control panel. The If you want to reset the scenario press the reset button. 

The simulator will also start a UDP server thread to handler all the data fetching and motor control request from other module, you can also create your program and use the API (in `lib/physicalWorldComm.py`) to control and monitor the robot arm .





















For The OPCUA plc simulation module I use this project [Python Virtual PLC Simulator with IEC 62541 OPC-UA-TCP Communication Protocol](https://www.linkedin.com/pulse/python-virtual-plc-simulator-iec-62541-opc-ua-tcp-protocol-liu-pm1pc) to implement the ladder logic control, UA data storage and process. For the detail you can check this link: https://github.com/LiuYuancheng/PLC_and_RTU_Simulator/tree/main/OPCUA_PLC_Simulator





















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







Python VTK lib: https://docs.vtk.org/en/latest/about.html