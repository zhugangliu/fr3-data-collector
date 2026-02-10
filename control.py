# control.py
import time
import sys
import threading
import csv
import os

try:
    from fairino import Robot
except ImportError:
    print("❌ fairino library not found, please check the SDK folder.")
    sys.exit()

class FR3Agent:
    def __init__(self, ip='192.168.58.2'):
        print(f"🤖 [Control] Connecting to robot at {ip}...")
        try:
            self.robot = Robot.RPC(ip)
            mode = self.robot.robot_state_pkg.robot_mode
            if mode != 0:
                print(f"❌ [Critical Error] Robot is in manual mode (Mode {mode})!")
                sys.exit(1)
            print("✅ [Control] Connection successful (Auto mode active)")
            
            self.is_recording = False
            self.data_buffer = []
            self.lock = threading.Lock()
            self.start_time = None
            
        except Exception as e:
            print(f"❌ [Control] Connection failed: {e}")
            sys.exit(1)

    # Waiting logic compatible with older SDK versions
    def wait_arrival(self, target_joints=None):
        time.sleep(0.2)
        start_wait = time.time()
        while True:
            # If target is provided, check joint angle error (most reliable)
            if target_joints:
                current_joints = list(self.robot.robot_state_pkg.jt_cur_pos)
                max_diff = max([abs(c - t) for c, t in zip(current_joints, target_joints)])
                if max_diff < 1.0: break
            else:
                # Backup: check instruction_preemption (if supported)
                try:
                    if self.robot.robot_state_pkg.instruction_preemption == 0: break
                except:
                    break 
            
            if time.time() - start_wait > 20: break
            time.sleep(0.05)

    # ==========================
    #  PART 1: Data Recording (Modified: Store XYZ + Gripper only)
    # ==========================
    def start_logging(self, global_start_time):
        self.start_time = global_start_time
        self.data_buffer = []
        self.is_recording = True
        self.log_thread = threading.Thread(target=self._record_loop, daemon=True)
        self.log_thread.start()
        print("🚀 [Control] Robot data acquisition started...")

    def stop_and_save_log(self, filename_prefix):
        self.is_recording = False
        if hasattr(self, 'log_thread'):
            self.log_thread.join()
        filename = f"{filename_prefix}_Robot.csv"
        self._save_to_csv(filename)
        return filename

    def _record_loop(self):
        while self.is_recording:
            try:
                now = time.time()
                pkg = self.robot.robot_state_pkg
                
                # Fetch TCP (XYZ + RxRyRz) and Gripper position
                tcp = list(pkg.tl_cur_pos) # [x, y, z, rx, ry, rz]
                g_val = pkg.gripper_position
                
                # Combined data: XYZ(6) + Gripper(1) = 7 columns
                cart_7d = tcp + [g_val]

                with self.lock:
                    self.data_buffer.append({
                        "abs_time": now,
                        "cart_7d": cart_7d
                    })
            except: pass
            time.sleep(0.01) # 100Hz

    def _save_to_csv(self, filename):
        if not self.data_buffer: return

        # Headers: Excluded J1-J6
        headers = ["Relative_Time", "Abs_Time", "X", "Y", "Z", "Rx", "Ry", "Rz", "Gripper"]

        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for item in self.data_buffer:
                    rel_time = item["abs_time"] - self.start_time
                    row = [f"{rel_time:.4f}", f"{item['abs_time']:.4f}"] + item["cart_7d"]
                    writer.writerow(row)
            print(f"✅ [Control] CSV saved (Coordinates only): {filename}")
        except Exception as e:
            print(f"❌ [Control] Save failed: {e}")

    # ==========================
    #  PART 2: Motion Control
    # ==========================
    def initialize_gripper(self):
        print("⚙️ [Gripper] Initializing...")
        self.robot.SetGripperConfig(4, 0) 
        time.sleep(0.2)
        self.robot.ActGripper(1, 0)
        time.sleep(0.2)
        self.robot.ActGripper(1, 1)
        time.sleep(0.2)

    def move_gripper(self, open_it=True):
        pos = 100 if open_it else 0
        self.robot.MoveGripper(1, pos, 100, 50, 30000, 1, 0, 0, 0, 0)
        time.sleep(0.2)

    def move_joint(self, joint_angles, speed=30.0):
        # Use wait_arrival to ensure steps aren't skipped
        ret = self.robot.MoveJ(joint_angles, 0, 0, vel=speed, acc=100, ovl=100)
        if ret == 0: self.wait_arrival(joint_angles)

    def move_linear_relative(self, dz_mm, speed=20.0):
        ret, pose = self.robot.GetActualTCPPose()
        if ret != 0: return
        target_pose = list(pose)
        target_pose[2] += dz_mm
        
        # Logic: MoveL + auto-calculated sleep
        ret = self.robot.MoveL(target_pose, 0, 0, vel=speed, acc=100, ovl=100)
        if ret == 0:
            expected_time = (abs(dz_mm) / speed) + 0.2
            if expected_time < 0.1: expected_time = 0.1
            time.sleep(expected_time)

    def close(self):
        try: self.robot.CloseRPC()
        except: pass