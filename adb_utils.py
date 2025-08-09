import subprocess

def adb_screencap(filename='screen.png'):
    result = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True)
    if result.returncode == 0:
        with open(filename, 'wb') as f:
            f.write(result.stdout)
        return True
    else:
        print("Ошибка при снятии скриншота:", result.stderr.decode())
        return False

def adb_tap(coord):
    x, y = coord
    cmd = ['adb', 'shell', 'input', 'tap', str(x), str(y)]
    subprocess.run(cmd)
    print(f"Тапнули по координатам: {x}, {y}")
