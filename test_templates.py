import cv2
from templates import load_templates, find_cards

def test_find_cards():
    templates = load_templates()
    screen = cv2.imread('screen.png')
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    cards = find_cards(screen_gray, templates)
    print(f'Найдено карточек: {len(cards)}')
    for name, (x, y, w, h) in cards:
        print(f'{name}: ({x}, {y}, {w}, {h})')

if __name__ == '__main__':
    test_find_cards()
