from templates import load_templates, find_cards, find_template
from adb_utils import adb_screencap, adb_screencap_async, adb_tap
import time
import cv2
import os

SCREENSHOT = 'screen.png'
ANIMATION_DELAY = 0.4

def get_card_center(coords):
    x, y, w, h = coords
    return (x + w // 2, y + h // 2)

class MemoryBot:
    def __init__(self, all_card_coords):
        self.known_cards = {}     # {(x,y): template_name}
        self.matched_cards = set() # {(x,y)}
        self.failed_pairs = set()
        self.all_coords = all_card_coords
        self.card_templates = load_templates()

    def wait_for_start_screen(self, templates_dir='templates/start', check_interval=0):
        if not os.path.isdir(templates_dir):
            print(f"Start templates folder not found: {templates_dir}")
            return False

        start_templates = []
        for file in os.listdir(templates_dir):
            path = os.path.join(templates_dir, file)
            if os.path.isfile(path):
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    start_templates.append(img)
                else:
                    print(f"Failed to load template: {path}")

        if not start_templates:
            print("No valid start templates found.")
            return False

        while True:
            if not adb_screencap():
                print("Failed to take screenshot.")
                time.sleep(check_interval)
                continue

            adb_screencap_async()

            screen = cv2.imread('screen.png', cv2.IMREAD_GRAYSCALE)
            if screen is None:
                print("Failed to load screenshot.")
                time.sleep(check_interval)
                continue

            for tmpl in start_templates:
                points = find_template(screen, tmpl)
                if points:
                    print("START screen detected.")
                    time.sleep(1)
                    return True

    def update_known_cards(self):
        adb_screencap()
        adb_screencap_async()
        screen = cv2.imread(SCREENSHOT)
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        cards = find_cards(screen_gray, self.card_templates)

        for tmpl, coords in cards:
            center = get_card_center(coords)

            nearest = min(self.all_coords, key=lambda c: abs(c[0]-center[0]) + abs(c[1]-center[1]))
            if nearest not in self.matched_cards:
                self.known_cards[nearest] = tmpl

    def find_unknown_cards(self):
        unknown = []
        for coord in self.all_coords:
            if coord not in self.known_cards and coord not in self.matched_cards:
                unknown.append(coord)
        return unknown

    def find_pairs_to_open(self):
        pairs = []
        template_to_coords = {}
        for coord, tmpl in self.known_cards.items():
            if coord not in self.matched_cards:
                template_to_coords.setdefault(tmpl, []).append(coord)

        for tmpl, coords_list in template_to_coords.items():
            if len(coords_list) >= 2:
                for i in range(0, len(coords_list), 2):
                    if i + 1 < len(coords_list):
                        pairs.append((coords_list[i], coords_list[i+1], tmpl))
        return pairs

    def mark_as_matched(self, c1, c2):
        self.matched_cards.add(c1)
        self.matched_cards.add(c2)
        if c1 in self.known_cards: del self.known_cards[c1]
        if c2 in self.known_cards: del self.known_cards[c2]
        print(f"Отмечены как собранные: {c1}, {c2}")
        print(f"Всего собранных пар: {len(self.matched_cards)//2}")

    def play(self):
        print("Запускаем игру...")
        prev_unknown_count = len(self.find_unknown_cards())

        while True:
            pairs = [p for p in self.find_pairs_to_open()
                    if (p[0], p[1]) not in self.failed_pairs and (p[1], p[0]) not in self.failed_pairs]

            if pairs:
                print(f"Известных пар для открытия: {len(pairs)}")
                for c1, c2, tmpl in pairs:
                    if c1 in self.matched_cards or c2 in self.matched_cards:
                        print(f"Пара {tmpl} по координатам {c1} и {c2} уже собрана, пропускаем.")
                        continue

                    print(f"Открываем пару {tmpl} по координатам {c1} и {c2}")
                    adb_tap(c1)
                    adb_tap(c2)
                    print(f"Ждем {ANIMATION_DELAY} секунд на анимацию...")
                    time.sleep(ANIMATION_DELAY)

                    print("Обновляем известные карты после открытия пары...")
                    self.update_known_cards()

                    self.mark_as_matched(c1, c2)
                    self.failed_pairs.discard((c1, c2))
                    self.failed_pairs.discard((c2, c1))

                    print(f"Текущие собранные пары: {len(self.matched_cards)//2}")

                prev_unknown_count = len(self.find_unknown_cards())

            else:
                unknown = self.find_unknown_cards()
                print(f"Неизвестных карт осталось: {len(unknown)}")
                if len(unknown) >= 2:
                    print(f"Открываем две неизвестные карты по координатам {unknown[0]} и {unknown[1]}")
                    adb_tap(unknown[0])
                    adb_tap(unknown[1])
                    print(f"Ждем {ANIMATION_DELAY} секунд, пока анимация откроется")
                    time.sleep(ANIMATION_DELAY)

                    print("Делаем скриншот и обновляем известные карты...")
                    self.update_known_cards()

                    current_unknown_count = len(self.find_unknown_cards())
                    print(f"Известных карт после обновления: {len(self.known_cards)}")
                    print(f"Собранных пар: {len(self.matched_cards)//2}")

                    if current_unknown_count > 0 and current_unknown_count >= prev_unknown_count:
                        print(f"[Error] количество неизвестных карт не уменьшилось! Было {prev_unknown_count}, стало {current_unknown_count}")

                    prev_unknown_count = current_unknown_count
                else:
                    print("Нет пар для открытия и неизвестных карт — игра завершена.")
                    break