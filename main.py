# main.py
import time
import sys
import os
from datetime import datetime

try:
    from camera import CameraRecorder
    from control import FR3Agent
except ImportError:
    print("❌ Cannot find camera.py or control.py")
    sys.exit()

# 10 Starting Poses (Joint Angles J1-J6)
START_POSES = [
    [126.036, -88.579, 70.097, -77.913, -78.169, -78.17],   
    [126.037, -86.155, 76.958, -103.23, -76.161, 100.602],  
    [136.854, -90.200, 76.958, -103.23, -111.39, 100.602],  
    [109.747, -118.00, 99.527, -76.947, -85.546, 100.602],  
    [95.108,  -90.201, 71.474, -76.945, -55.825, 100.602],  
    [109.746, -90.201, 71.473, -76.945, -85.546, 100.602],  
    [116.501, -134.93, 99.524, -76.945, -85.546, 100.602],  
    [144.508, -98.959, 75.279, -76.945, -97.159, 3.116],    
    [78.113,  -114.40, 82.873, -76.945, -50.502, -88.621],  
    [106.75,  -114.40, 82.873, -76.945, -85.927, -88.621]   
]

# Grasp Pre-position (Joint Angles)
TARGET_JOINTS = [136.841,-72.697,53.511,-75.248,-87.819,80.76]

def auto_mission():
    print("\n🤖 [Main] System Initializing...")
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # 1. 30FPS Camera
    cam_recorder = CameraRecorder(camera_id=0, target_fps=30.0)
    if not cam_recorder.connect():
        return

    # 2. Robot
    agent = FR3Agent('192.168.58.2') 
    agent.initialize_gripper()

    print(f"\n🚀 [Main] Starting Batch Collection ({len(START_POSES)} groups)...")

    for i, start_pose in enumerate(START_POSES):
        trial_id = i + 1
        print(f"\n======== 🟡 Group {trial_id} ========")

        # --- Phase 1: Reset ---
        print("🤖 Moving to starting position...")
        agent.move_joint(start_pose, speed=40)

        print("⏳ Arrived! Waiting 5 seconds (Please place object)...")
        for s in range(5, 0, -1):
            print(f" {s}...", end='', flush=True)
            time.sleep(1)
        print(" Go!")

        # --- Phase 2: Recording Start ---
        T0 = time.time()
        timestamp_str = datetime.now().strftime("%H%M%S")
        save_prefix = os.path.join(data_dir, f"Trial_{trial_id}_{timestamp_str}")
        
        print(f"🔫 Recording started! T0 = {T0:.4f}")
        
        cam_recorder.start_recording(T0)   
        agent.start_logging(T0)            

        try:
            # A. Move above grasp target
            agent.move_joint(TARGET_JOINTS, speed=40)
            
            # B. Prepare gripper
            agent.move_gripper(open_it=True)
            
            # C. Descend
            agent.move_linear_relative(dz_mm=-100.0, speed=40.0)
            
            # D. Grasp
            agent.move_gripper(open_it=False)
            
            # E. Lift
            agent.move_linear_relative(dz_mm=100.0, speed=40.0)

        except KeyboardInterrupt:
            print("\n🛑 User Interrupted")
            break
        except Exception as e:
            print(f"❌ Error during operation: {e}")
        finally:
            # --- Phase 3: Saving ---
            print("💾 Saving data...")
            
            csv_path = agent.stop_and_save_log(save_prefix)
            video_path = cam_recorder.stop_and_save(save_prefix)
            
            # Handle MP4 file renaming
            if os.path.exists("latest_recording.mp4"):
                if os.path.exists(video_path): os.remove(video_path)
                os.rename("latest_recording.mp4", video_path)
                print(f"✅ [Main] Video saved: {video_path}")
            else:
                print(f"⚠️ [Main] Warning: latest_recording.mp4 not found")

            agent.move_gripper(open_it=True)
            print(f"✅ Group {trial_id} complete")

    agent.close()
    print("\n🎉 All collections finished!")

if __name__ == "__main__":
    auto_mission()