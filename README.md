# 🤖 FR3 Robot Data Collection

This repository contains the automation scripts and SDK for the FR3 robot grasp-and-lift data collection task.

## 📦 Features
- **Plug & Play**: The `fairino` SDK is included. No manual setup required.
- **Sync Recording**: Records RGB video (30fps) and Robot States (100Hz) simultaneously.
- **Auto-Retry**: Automatically loops through 10 preset trials.

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/zhugangliu/fr3-data-collector.git
   cd fr3-data-collector
   ```

2. **Install Dependencies**
   (Recommended to use a virtual environment)
   ```bash
   pip install opencv-python
   ```

## 🔌 Hardware Setup (Crucial!)

### 1. Ethernet Configuration
The robot has a static IP: `192.168.58.2`.
You **must** configure your PC's Ethernet adapter to be on the same subnet:

- **IP Address**: `192.168.58.10` (Or any distinct IP ending in .x)
- **Subnet Mask**: `255.255.255.0`
- **Gateway**: Leave blank

### 2. Device Check
- ✅ **Robot**: Emergency Stop released (Blue light breathing).
- ✅ **Camera**: USB Webcam connected (Default ID: 0).

## 🚀 Usage

Run the main script:

```bash
python main.py
```

### Workflow
1. **Reset**: Robot moves to the start pose.
2. **Place Object**: You have **5 seconds** (countdown displayed) to place the object.
3. **Auto-Grasp**: The robot descends, grasps, lifts, and saves data.
4. **Loop**: Repeats for all 10 preset poses.

## 📂 Data Output

Data is saved in the `data/` folder (ignored by Git):
- **Video**: `Trial_X_Timestamp_Video.mp4`
- **Log**: `Trial_X_Timestamp_Robot.csv` (Columns: Time, TCP Pose, Gripper)

