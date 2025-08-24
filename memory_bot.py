from templates import load_templates, find_cards, find_template, has_duplicate_templates
from adb_utils import adb_screencap, adb_screencap_async, adb_tap
from logger import logger
import time
import cv2
import os
import queue
import threading

SCREENSHOT = 'screen.png'
OPEN_CARDS_ANIMATION_DELAY = 0.26
CLOSE_CARDS_ANIMATION_DELAY = 1.12
START_DELAY = 1.48
START_DELAYS = {
    'st.png': 1.48,
    'rt.png': 0.8,
}

def get_card_center(coords):
    x, y, w, h = coords
    return (x + w // 2, y + h // 2)

def delayed_analysis(bot, delay=OPEN_CARDS_ANIMATION_DELAY):
    def task():
        bot.analyze_board()
    timer = threading.Timer(delay, task)
    timer.daemon = True
    timer.name = "AnalyzeBoard"
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
            logger.warning("Start templates folder not found: %s", templates_dir)
            return False

        start_templates = []
        template_files = []
        for file in os.listdir(templates_dir):
            path = os.path.join(templates_dir, file)
            if os.path.isfile(path):
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    start_templates.append(img)
                    template_files.append(file)
                else:
                    logger.error("Failed to load template: %s", path)

        if not start_templates:
            logger.error("No valid start templates found.")
            return False

        while True:
            if not adb_screencap():
                logger.error("Failed to take screenshot.")
                time.sleep(check_interval)
                continue

            adb_screencap_async()

            screen = cv2.imread('screen.png', cv2.IMREAD_GRAYSCALE)
            if screen is None:
                logger.error("Failed to load screenshot.")
                time.sleep(check_interval)
                continue

            for tmpl, fname in zip(start_templates, template_files):
                points = find_template(screen, tmpl)
                if points:
                    delay = START_DELAYS.get(fname, START_DELAY)
                    logger.info("START screen detected with template %s.", fname)
                    logger.info("Ждем %s секунды, пока откроется игровое поле", delay)
                    time.sleep(delay)
                    return True

    def analyze_board(self):
        logger.info("analyze_board начинает работу")
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
            logger.info("Добавлено в matched_cards %d карт (пара найдена)", len(cards))
        else:
            for tmpl, coords in cards:
                center = get_card_center(coords)

                nearest = min(self.all_coords, key=lambda c: abs(c[0]-center[0]) + abs(c[1]-center[1]))
                if nearest not in self.matched_cards:
                    self.known_cards[nearest] = tmpl
        pairs = [p for p in self.find_pairs_to_open()
                if (p[0], p[1]) not in self.failed_pairs and (p[1], p[0]) not in self.failed_pairs]
        
        if pairs:
            logger.info("Известных пар для открытия: %d", len(pairs))
            for c1, c2, tmpl in pairs:
                if c1 in self.matched_cards or c2 in self.matched_cards:
                    logger.info("Пара %s по координатам %d и %d уже собрана, пропускаем.", tmpl, c1, c2)
                    continue
                i1 = self.coord_to_index(c1)
                i2 = self.coord_to_index(c2)

                if i1 is None or i2 is None:
                    continue  # пропускаем если индексы не найдены

                logger.info("Ставим пару в очередь")
                self.queue.put((i1, i2))
                self.mark_as_matched(c1, c2)
                self.failed_pairs.discard((c1, c2))
                self.failed_pairs.discard((c2, c1))

                logger.info("Текущие собранные пары: %d", len(self.matched_cards)//2)
        end = time.perf_counter()
        logger.info("analyze_board выполнилась за %.3f секунд", end - start)

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
            logger.error("Ошибка: координата %d не найдена в all_coords", coord)
            return None

    def mark_as_matched(self, c1, c2):
        self.matched_cards.add(c1)
        self.matched_cards.add(c2)
        if c1 in self.known_cards: del self.known_cards[c1]
        if c2 in self.known_cards: del self.known_cards[c2]

    def open_pair(self, i1, i2):
        logger.info("Открываем пару по координатам %d и %d", i1, i2)
        adb_tap(self.all_coords[i1])
        adb_tap(self.all_coords[i2])
        time.sleep(OPEN_CARDS_ANIMATION_DELAY)

    def play(self):
        logger.info("Запускаем игру...")
        counter = 0

        while True:
            try:
                i1, i2 = self.queue.get(timeout=1)
            except queue.Empty:
                break

            self.open_pair(i1, i2)

            if counter < 6:
                delayed_analysis(self)
            counter += 1

            time.sleep(CLOSE_CARDS_ANIMATION_DELAY)
            self.queue.task_done()

    def main(self):
        self.init_queue()
        click_thread = threading.Thread(target=self.play, name="Main")
        click_thread.start()
        click_thread.join()

        logger.info("Игра пройдена!")