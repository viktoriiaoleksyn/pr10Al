
from collections import Counter
import heapq
import itertools
import json
import math
import struct
from pathlib import Path


def pobuduvaty_derevo(chastoty):
    """Побудова дерева Хаффмана зі словника {символ: частота}."""
    cherha = []
    nomery = itertools.count()
    for symvol, chastota in sorted(chastoty.items()):
        heapq.heappush(cherha, (chastota, next(nomery), symvol))
    if not cherha:
        return None
    while len(cherha) > 1:
        vaga1, _, livyy = heapq.heappop(cherha)
        vaga2, _, pravyy = heapq.heappop(cherha)
        heapq.heappush(cherha, (vaga1 + vaga2, next(nomery), (livyy, pravyy)))
    return cherha[0][2]


def otrymaty_kody(derevo):
    kody = {}
    if derevo is None:
        return kody
    stek = [(derevo, '')]
    while stek:
        vuzol, kod = stek.pop()
        if isinstance(vuzol, tuple):
            stek.append((vuzol[1], kod + '1'))
            stek.append((vuzol[0], kod + '0'))
        else:
            kody[vuzol] = kod or '0'
    return kody


def dekoduvaty_ryadok(bity, derevo):
    if derevo is None:
        return ''
    if not isinstance(derevo, tuple):
        return derevo * len(bity)
    rezultat = []
    vuzol = derevo
    for bit in bity:
        vuzol = vuzol[int(bit)]
        if not isinstance(vuzol, tuple):
            rezultat.append(vuzol)
            vuzol = derevo
    return ''.join(rezultat)


def koduvaty_frazu():
    fraza = input('Введіть текстову фразу: ')
    if not fraza:
        print('Фраза порожня. Введіть хоча б один символ.')
        return
    chastoty = Counter(fraza)
    derevo = pobuduvaty_derevo(chastoty)
    kody = otrymaty_kody(derevo)
    zakodovano = ''.join(kody[s] for s in fraza)
    bitiv_na_symvol = max(1, math.ceil(math.log2(len(chastoty))))
    rivnomirna_dovzhyna = len(fraza) * bitiv_na_symvol

    print('\nТаблиця частот і кодів:')
    print(f"{'Символ':<12}{'Частота':<12}{'Код'}")
    for symvol, chastota in sorted(chastoty.items(), key=lambda item: (-item[1], item[0])):
        nazva = repr(symvol)
        print(f'{nazva:<12}{chastota:<12}{kody[symvol]}')
    print('\nЗакодована фраза:', zakodovano)
    print('Декодована фраза:', dekoduvaty_ryadok(zakodovano, derevo))
    print('Довжина коду Хаффмана:', len(zakodovano), 'біт')
    print('Довжина рівномірного коду:', rivnomirna_dovzhyna, 'біт')
    print('Бітів на символ у рівномірному коді:', bitiv_na_symvol)
    print('Економія:', rivnomirna_dovzhyna - len(zakodovano), 'біт')
    print('Порівняння не враховує зберігання таблиці кодів.')


def stysnuty():
    shlyah = Path(input('Шлях до текстового файлу UTF-8: ').strip().strip('"'))
    dani = shlyah.read_bytes()
    dani.decode('utf-8') 
    chastoty = Counter(dani)
    kody = otrymaty_kody(pobuduvaty_derevo(chastoty))
    zagolovok = json.dumps(dict(chastoty), separators=(',', ':')).encode('ascii')
    vykhid = shlyah.with_name(shlyah.name + '.huff')
    if vykhid.exists():
        raise FileExistsError(f'Архів {vykhid} вже існує. Перейменуйте його перед стисненням.')
    bufer = 0
    kilkist_bitiv = 0
    with vykhid.open('xb') as arkhiv:
        arkhiv.write(b'HUF1')
        arkhiv.write(struct.pack('>I', len(zagolovok)))
        arkhiv.write(zagolovok)
        for bayt in dani:
            for bit in kody[bayt]:
                bufer = (bufer << 1) | int(bit)
                kilkist_bitiv += 1
                if kilkist_bitiv == 8:
                    arkhiv.write(bytes([bufer]))
                    bufer = 0
                    kilkist_bitiv = 0
        if kilkist_bitiv:
            arkhiv.write(bytes([bufer << (8 - kilkist_bitiv)]))
    print(f'Архів створено: {vykhid}')
    print(f'Розмір початкового файлу: {len(dani)} байт')
    print(f'Розмір архіву: {vykhid.stat().st_size} байт')
    print('Службові дані можуть зробити маленький архів більшим за оригінал.')


def rozpokuvaty():
    shlyah = Path(input('Шлях до файлу .huff: ').strip().strip('"'))
    with shlyah.open('rb') as arkhiv:
        if arkhiv.read(4) != b'HUF1':
            raise ValueError('Невідомий формат архіву.')
        pole = arkhiv.read(4)
        if len(pole) != 4:
            raise ValueError('Архів пошкоджений: немає заголовка.')
        dovzhyna = struct.unpack('>I', pole)[0]
        if dovzhyna > 10000:
            raise ValueError('Архів пошкоджений: некоректний заголовок.')
        zagolovok = arkhiv.read(dovzhyna)
        chastoty = {int(k): v for k, v in json.loads(zagolovok).items()}
        if any(not 0 <= k <= 255 or type(v) is not int or v <= 0 for k, v in chastoty.items()):
            raise ValueError('Архів пошкоджений: некоректні частоти.')
        kilkist = sum(chastoty.values())
        derevo = pobuduvaty_derevo(chastoty)
        zakodovani = arkhiv.read()
    if not shlyah.name.endswith('.huff'):
        raise ValueError('Файл архіву повинен мати розширення .huff.')
    vykhid = shlyah.with_name('rozpakovano_' + shlyah.name[:-5])
    rezultat = bytearray()
    if derevo is not None and not isinstance(derevo, tuple):
        if len(zakodovani) * 8 < kilkist:
            raise ValueError('Архів пошкоджений: недостатньо даних.')
        rezultat.extend([derevo] * kilkist)
    elif derevo is not None:
        vuzol = derevo
        for bayt in zakodovani:
            for poz in range(7, -1, -1):
                vuzol = vuzol[(bayt >> poz) & 1]
                if not isinstance(vuzol, tuple):
                    rezultat.append(vuzol)
                    vuzol = derevo
                    if len(rezultat) == kilkist:
                        break
            if len(rezultat) == kilkist:
                break
        if len(rezultat) != kilkist:
            raise ValueError('Архів пошкоджений: недостатньо даних.')
    if Counter(rezultat) != chastoty:
        raise ValueError('Архів пошкоджений: частоти не збігаються.')
    if vykhid.exists():
        raise FileExistsError(f'Файл {vykhid} вже існує. Перейменуйте його перед розпакуванням.')
    vykhid.write_bytes(rezultat)
    print(f'Файл розпаковано: {vykhid}')


def main():
    while True:
        print('\n--- КОДУВАННЯ ХАФФМАНА ---')
        print('1. Закодувати текстову фразу')
        print('2. Стиснути текстовий файл')
        print('3. Розпакувати архів')
        print('0. Вихід')
        vybir = input('Оберіть дію: ').strip()
        try:
            if vybir == '1':
                koduvaty_frazu()
            elif vybir == '2':
                stysnuty()
            elif vybir == '3':
                rozpokuvaty()
            elif vybir == '0':
                print('Роботу програми завершено.')
                break
            else:
                print('Невідома дія. Спробуйте ще раз.')
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as pomylka:
            print('Помилка:', pomylka)


if __name__ == '__main__':
    main()
