from templates import load_templates, find_cards, find_template, has_duplicate_templates
from adb_utils import adb_screencap, adb_screencap_async, adb_tap
import time
import cv2
import os
import queue
import threading

SCREENSHOT = 'screen.png'
OPEN_CARDS_ANIMATION_DELAY = 0.26
CLOSE_CARDS_ANIMATION_DELAY = 1.1
START_DELAY=1.45

def get_card_center(coords):
    x, y, w, h = coords
    return (x + w // 2, y + h // 2)

def delayed_analysis(bot, delay=OPEN_CARDS_ANIMATION_DELAY):
    def task():
        bot.analyze_board()
    timer = threading.Timer(delay, task)
    timer.daemon = True
    timer.start()

class MemoryBot:
    def __init__(self, all_card_coords):
        self.queue = queue.Queue()
        self.known_cards = {}     # {(x,y): template_name}
        self.matched_cards = set() # {(x,y)}
        self.failed_pairs = set()
        self.all_coords = all_card_coords
        self.card_templates = load_templates()

    def init_queue(self):
        for i in range(0, 12, 2):
            self.queue.put((i, i + 1))

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
                    print(f"Ждем {START_DELAY} секунды, пока откроется игровое поле")
                    time.sleep(START_DELAY)
                    return True

    def analyze_board(self):
        start = time.perf_counter()
        adb_screencap()
        adb_screencap_async()
        screen = cv2.imread(SCREENSHOT)
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        cards = find_cards(screen_gray, self.card_templates)
        if has_duplicate_templates(cards):
            for tmpl, coords in cards:
                center = get_card_center(coords)
                nearest = min(self.all_coords, key=lambda c: abs(c[0] - center[0]) + abs(c[1] - center[1]))
                self.matched_cards.add(nearest)
                if nearest in self.known_cards:
                    del self.known_cards[nearest]
            print(f"Добавлено в matched_cards {len(cards)} карт (пара найдена)")
        else:
            for tmpl, coords in cards:
                center = get_card_center(coords)

                nearest = min(self.all_coords, key=lambda c: abs(c[0]-center[0]) + abs(c[1]-center[1]))
                if nearest not in self.matched_cards:
                    self.known_cards[nearest] = tmpl
        pairs = [p for p in self.find_pairs_to_open()
                if (p[0], p[1]) not in self.failed_pairs and (p[1], p[0]) not in self.failed_pairs]
        
        if pairs:
            print(f"Известных пар для открытия: {len(pairs)}")
            for c1, c2, tmpl in pairs:
                if c1 in self.matched_cards or c2 in self.matched_cards:
                    print(f"Пара {tmpl} по координатам {c1} и {c2} уже собрана, пропускаем.")
                    continue
                i1 = self.coord_to_index(c1)
                i2 = self.coord_to_index(c2)

                if i1 is None or i2 is None:
                    continue  # пропускаем если индексы не найдены

                print("Ставим пару в очередь")
                self.queue.put((i1, i2))
                self.mark_as_matched(c1, c2)
                self.failed_pairs.discard((c1, c2))
                self.failed_pairs.discard((c2, c1))

                print(f"Текущие собранные пары: {len(self.matched_cards)//2}")
        end = time.perf_counter()
        print(f"update_known_cards выполнилась за {end - start:.3f} секунд")

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

    def coord_to_index(self, coord):
        try:
            return self.all_coords.index(coord)
        except ValueError:
            print(f"Ошибка: координата {coord} не найдена в all_coords")
            return None

    def mark_as_matched(self, c1, c2):
        self.matched_cards.add(c1)
        self.matched_cards.add(c2)
        if c1 in self.known_cards: del self.known_cards[c1]
        if c2 in self.known_cards: del self.known_cards[c2]

    def open_pair(self, i1, i2):
        print(f"Открываем пару по координатам {i1} и {i2}")
        adb_tap(self.all_coords[i1])
        adb_tap(self.all_coords[i2])
        time.sleep(OPEN_CARDS_ANIMATION_DELAY)

    def play(self):
        print("Запускаем игру...")
        while True:
            try:
                i1, i2 = self.queue.get(timeout=1)
            except queue.Empty:
                break

            self.open_pair(i1, i2)
            delayed_analysis(self)
            time.sleep(CLOSE_CARDS_ANIMATION_DELAY)
            self.queue.task_done()

    def main(self):
        self.init_queue()
        click_thread = threading.Thread(target=self.play)
        click_thread.start()
        click_thread.join()

        print("Игра пройдена!")