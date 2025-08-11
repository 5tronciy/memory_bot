import cv2
import numpy as np
import os
import time

TEMPLATE_CARDS_DIR = 'templates/cards'
SCREENSHOT = 'screen.png'
THRESHOLD = 0.72

def load_templates():
    templates = {}
    for filename in os.listdir(TEMPLATE_CARDS_DIR):
        if filename.endswith('.png'):
            path = os.path.join(TEMPLATE_CARDS_DIR, filename)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            templates[filename] = img
    return templates

def find_cards(screen_gray, templates):
    found_cards = []

    for name, tmpl in templates.items():
        w, h = tmpl.shape[::-1]
        res = cv2.matchTemplate(screen_gray, tmpl, cv2.TM_CCOEFF_NORMED)

        loc = np.where(res >= THRESHOLD)
        points = list(zip(*loc[::-1]))

        scores = res[loc]
        points_scores = list(zip(points, scores))
        points_scores.sort(key=lambda x: x[1], reverse=True)

        filtered_points = []

        for pt, score in points_scores:
            x, y = pt
            if all(abs(x - fx) > 52 or abs(y - fy) > 52 for fx, fy in filtered_points):
                filtered_points.append((x, y))

        for pt in filtered_points:
            found_cards.append((name, (pt[0], pt[1], w, h)))
    print(found_cards)

    return found_cards

def has_duplicate_templates(cards):
    seen = set()
    for tmpl, _ in cards:
        if tmpl in seen:
            return True
        seen.add(tmpl)
    return False

def find_template(screen_gray, template, treshold=THRESHOLD):
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= treshold)
    points = list(zip(*loc[::-1]))
    return points