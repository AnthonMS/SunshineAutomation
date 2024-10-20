import sys
import subprocess
import os
modules = [
    're',
    'time',
    'pyuac',
    'psutil',
    'logging',
    'requests',
    'json',
    'urllib3',
    'pyautogui'
]
for module in modules:
    try:
        __import__(module)
    except ImportError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', module])
import re
import time
import pyuac
import psutil
import logging
import requests
import requests.exceptions
import json
import urllib3
import pyautogui
from dotenv import load_dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


THIS_PATH = os.path.dirname(os.path.realpath(__file__)) + '\\'
load_dotenv(f'{THIS_PATH}sunshine.env')
logging.basicConfig(filename=f'{THIS_PATH}sunshine.log', level=logging.INFO, format='%(asctime)s %(message)s')


DISPLAY_NAME = r'\\.\DISPLAY1'
VIRTUAL_DEVICE = 'root\\iddsampledriver'  # replace with your device ID
DEVCON_PATH = os.getenv("DEVCON_PATH")
SUNSHINE_PATH = os.getenv("SUNSHINE_PATH")
SUNSHINE_SHORTCUT = os.getenv("SUNSHINE_SHORTCUT")
SUNSHINE_WEB = os.getenv("SUNSHINE_WEB")
SUNSHINE_AUTH = os.getenv("SUNSHINE_AUTH")
SUNSHINE_HEADERS = {
    'Content-Type': 'text/plain;charset=UTF-8',
    'Authorization': f'Basic {SUNSHINE_AUTH}',
}
VIRTUAL_DEVICE_ENABLE = r"""
$device = Get-PnpDevice | Where-Object { $_.HardwareID -eq 'root\iddsampledriver' }
Enable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false
"""
VIRTUAL_DEVICE_DISABLE = r"""
$device = Get-PnpDevice | Where-Object { $_.HardwareID -eq 'root\iddsampledriver' }
Disable-PnpDevice -InstanceId $device.InstanceId -Confirm:$false
"""

def main():
    action = sys.argv[1]

    if action == 'start':
        logging.info("Executing Start...")
        close_apps()
        start_sunshine()
        start_virtual_display()
        update_sunshine_config()
        restart_sunshine()
        pyautogui.hotkey('win', 'm')


    elif action == 'stop':
        logging.info("Executing Stop...")
        stop_sunshine()
        stop_virtual_display()

    elif action == 'test':
        print("Testing...")
        logging.info("Testing...")



def close_apps():
    logging.info("Closing Discord...")
    stop_process('discord')


def start_sunshine():
    # Start sunshine if it isnt already
    if not is_process_running('sunshine'):
        logging.info('Sunshine is not running. Starting it now...')
        # logging.info(SUNSHINE_SHORTCUT)
        try:
            subprocess.Popen(["cmd", "/c", "start", "", SUNSHINE_SHORTCUT])
        except:
            logging.error("Error starting Sunshine!")
        time.sleep(15)
        logging.info('Sunshine should be running now!')
    else:
        logging.info('Sunshine is already running!')


def stop_sunshine():
    logging.info("Stopping sunshine...")
    stop_process('sunshine')

def restart_sunshine():
    try:
        logging.info("Restarting Sunshine......")
        requests.post('https://localhost:47990/api/restart', headers=SUNSHINE_HEADERS, verify=False)
    except requests.exceptions.ConnectionError:
        logging.info("Sunshine restarted successfully!")
    
def update_sunshine_config():
    logging.info("Updating Sunshine config...")

    data_dict = {"output_name": DISPLAY_NAME}
    if os.getenv("ENCODER"):
        data_dict["encoder"] = os.getenv("ENCODER")
    if os.getenv("NVENC_PRESET"):
        data_dict["nvenc_preset"] = os.getenv("NVENC_PRESET")
    if os.getenv("AUDIO_SINK"):
        data_dict["audio_sink"] = os.getenv("AUDIO_SINK")
        
    data = json.dumps(data_dict)
    response = requests.post('https://localhost:47990/api/config', headers=SUNSHINE_HEADERS, data=data, verify=False)

    logging.info(f"Config update?: {response.status_code}")



def start_virtual_display():
    global DISPLAY_NAME
    result = subprocess.run([SUNSHINE_PATH+'tools\\dxgi-info.exe'], stdout=subprocess.PIPE)
    output = result.stdout.decode()
    # logging.info(output)
    initial_matches = set(re.findall(r'Output Name\s+:\s+(\\\\\.\\DISPLAY\d+)', output))

    # Start Virtual Display if it isnt already
    status_result = subprocess.run([f'{DEVCON_PATH}\\devcon.exe', 'status', VIRTUAL_DEVICE], stdout=subprocess.PIPE)
    status_output = status_result.stdout.decode()
    if 'running' not in status_output: 
        logging.info("Enabling virtual display...")
        process = subprocess.Popen(["powershell", "-Command", VIRTUAL_DEVICE_ENABLE], stdout=subprocess.PIPE)
        while True:
            result = subprocess.run([SUNSHINE_PATH+'tools\\dxgi-info.exe'], stdout=subprocess.PIPE)
            output = result.stdout.decode()
            matches = set(re.findall(r'Output Name\s+:\s+(\\\\\.\\DISPLAY\d+)', output))
            new_displays = matches - initial_matches
            if new_displays:
                DISPLAY_NAME = new_displays.pop()
                # logging.info(f"DISPLAY_NAME: {DISPLAY_NAME}")
                break

            # logging.info("Waiting for new display to be enabled...")
            time.sleep(1)  # Check every second
        
    else:
        logging.info("Virtual display already enabled...")
        result = subprocess.run([SUNSHINE_PATH+'tools\\dxgi-info.exe'], stdout=subprocess.PIPE)
        output = result.stdout.decode()
        matches = re.findall(r'Output Name\s+:\s+(\\\\\.\\DISPLAY\d+)', output)
        DISPLAY_NAME = matches[-1] # Get the last match
        # logging.info(f"DISPLAY_NAME: {DISPLAY_NAME}")




def stop_virtual_display():
    status_result = subprocess.run([f'{DEVCON_PATH}\\devcon.exe', 'status', VIRTUAL_DEVICE], stdout=subprocess.PIPE)
    status_output = status_result.stdout.decode()
    if 'running' in status_output: 
        logging.info("Disabling virtual display...")
        process = subprocess.Popen(["powershell", "-Command", VIRTUAL_DEVICE_DISABLE], stdout=subprocess.PIPE)

def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False;

def stop_process(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if process_name.lower() in proc.info['name'].lower():
                proc.kill()
                logging.info(f"Stopped {process_name}!")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sunshine.py <start|stop>")
        sys.exit(1)
    
    # main()

    if not pyuac.isUserAdmin():
        pyuac.runAsAdmin()
    else:        
        main()