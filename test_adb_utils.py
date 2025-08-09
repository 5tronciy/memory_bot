from adb_utils import adb_screencap, adb_tap

def test_screenshot():
    if adb_screencap():
        print('Скриншот сделан успешно')
    else:
        print('Ошибка при скриншоте')

def test_tap():
    adb_tap(100, 200)
    print('Тап отправлен')

if __name__ == '__main__':
    test_screenshot()
    test_tap()
