import os
import subprocess

def main():
    # Change directory to the specified path
    os.chdir( '/home/xiaoyu/Desktop/yogee/dex-affordance')
    
    # Construct the command
    command = [
        'python3', 'tools/train_states2.py',
        '--cfg', 'exp_cfg/shapenet_relocate_mug_ilad_cfg.yaml',
    ]
    
    # Execute the command
    subprocess.run(command)

if __name__ == "__main__":
    main()