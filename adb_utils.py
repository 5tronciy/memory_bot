import os
import time
import subprocess
import shutil
import threading
from logger import logger

DEBUG_DIR = 'debug_screenshots'

def ensure_debug_dir():
    if not os.path.exists(DEBUG_DIR):
        os.makedirs(DEBUG_DIR)

def adb_screencap(filename='screen.png'):
    result = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True)
    if result.returncode == 0:
        with open(filename, 'wb') as f:
            f.write(result.stdout)
        return True
    else:
        logger.error("Ошибка при снятии скриншота: %s", result.stderr.decode())
        return False

def adb_tap(coord):
    x, y = coord
    cmd = ['adb', 'shell', 'input', 'tap', str(x), str(y)]
    subprocess.run(cmd)
    logger.info(f"Тапнули по координатам: {x}, {y}")

def adb_screencap_async(src='screen.png', dst_folder='debug_screenshots'):
    def save_copy():
        ensure_debug_dir()
        dst = os.path.join(dst_folder, f'screen_{int(time.time()*1000)}.png')
        shutil.copy(src, dst)
        logger.debug("Debug screenshot saved to %s", dst)
    threading.Thread(target=save_copy, daemon=True, name="Debug").start()