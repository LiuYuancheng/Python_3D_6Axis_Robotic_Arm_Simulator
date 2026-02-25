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









The 3D robot Arm simulator will simulate generate the sensors value of the cube position and the 6 joint's current angles data, the OPC-UA PLC module will fetch the data regualarly via UDP message. Here I use the UDP message to simulate the PLC collect the electrical signal or analog signal from physical sensor device. Then the data will be saved into the related UA data value, the PLC will make decision of the module based on the control UA data, such as if the user want to move the arm shoulder to angle1 but the current sensor value is angle value 2, then the PLC will send the motor control signal out from PLC to the related simulated motor in the 3D robot arm simulator until the sensor report the arm moved to the correct position. 

For The OPCUA plc simulation module I use this project [Python Virtual PLC Simulator with IEC 62541 OPC-UA-TCP Communication Protocol](https://www.linkedin.com/pulse/python-virtual-plc-simulator-iec-62541-opc-ua-tcp-protocol-liu-pm1pc) to implement the ladder logic control, UA data storage and process. For the detail you can check this link: https://github.com/LiuYuancheng/PLC_and_RTU_Simulator/tree/main/OPCUA_PLC_Simulator

On the controller side, it will start a OPCUA client thread to connect to the OPCUA server in the PLC to fetch the data and visualize them. The Cube current 3D position will be convert to ground projection position then shown on the cube position map, then the controller can identify whether the robot arm is long enough reach the cube and calculate the angle of each joint to reach the cube. Each join the real time position will shown in the 6 Axis display and the user can user the slider to manually adjust the servo motor's angle. It will also provide the action sequence selection/upload function for user to upload a pre-set arm movement sequence then the arm will keep repeat finish the actions automatically. 



















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