from memory_bot import MemoryBot

def test_update_and_find():
    bot = MemoryBot()
    success = bot.update_known_cards()
    if not success:
        print('Не удалось обновить карточки')
        return
    pairs = bot.find_unknown_cards()
    print(f'Найдено пар: {len(pairs)}')
    for tmpl, c1, c2 in pairs:
        print(f'{tmpl}: {c1} <-> {c2}')

if __name__ == '__main__':
    test_update_and_find()
