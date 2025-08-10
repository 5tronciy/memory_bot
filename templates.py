import cv2
import numpy as np
import os
import time

TEMPLATE_DIR = 'templates'
SCREENSHOT = 'screen.png'
THRESHOLD = 0.8

def load_templates():
    templates = {}
    for filename in os.listdir(TEMPLATE_DIR):
        if filename.endswith('.png'):
            path = os.path.join(TEMPLATE_DIR, filename)
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
            if all(abs(x - fx) > 35 or abs(y - fy) > 35 for fx, fy in filtered_points):
                filtered_points.append((x, y))

        for pt in filtered_points:
            found_cards.append((name, (pt[0], pt[1], w, h)))

    return found_cards

def find_template(screen_gray, template, treshold=THRESHOLD):
    w, h = template.shape[::-1]
    res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    loc = np.where(res >= treshold)
    points = list(zip(*loc[::-1]))
    return points