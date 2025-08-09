from memory_bot import MemoryBot
from adb_utils import adb_tap, adb_screencap
from templates import load_templates, find_cards

if __name__ == '__main__':
    all_card_centers = [
      (260, 728), (540, 728), (820, 728),
      (260, 1010), (540, 1010), (820, 1010),
      (260, 1293), (540, 1293), (820, 1293),
      (260, 1575), (540, 1575), (820, 1575),
    ]

    bot = MemoryBot(all_card_centers)
    bot.play()