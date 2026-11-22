#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собрать !_kanji_strokes.pdf — пошаговый порядок черт — из данных AnimCJK.

ЧТО ДЕЛАЕТ
    Для каждого иероглифа из строки K рисует полосу: иероглиф целиком, затем
    по кадру на черту. В кадре: ещё не написанные черты бледные, уже написанные
    серые, новая черта чёрная, рядом с ней красная стрелка — направление письма.

ОТКУДА ДАННЫЕ (единственный источник графики для этого файла)
    AnimCJK, японский набор: https://github.com/parsimonhi/animCJK, папка svgsJa,
    файл <десятичный код знака>.svg (一 = 19968.svg). В файле для каждой черты
    есть контур (path id="z<код>d<N>") и осевая линия от начала черты к концу
    (path clip-path="url(#z<код>c<N>)") — по ней строится стрелка.
    Скачанные файлы лежат рядом в animcjk/ без изменений; недостающий файл
    скрипт скачивает сам.

КАК ЗАПУСКАТЬ (из корня репозитория)
    python3 _strokes_src/build_strokes.py            # пишет !_kanji_strokes.pdf
    python3 _strokes_src/build_strokes.py out.pdf    # или в другой файл

КАК ДОБАВИТЬ ИЕРОГЛИФ
    Дописать его в строку K в нужном месте (порядок — как в таблицах учебника)
    и запустить скрипт. Размер кадра не менять: если не помещается — станет
    больше страниц.

РАЗМЕРЫ (держать всегда, см. AGENTS.md)
    A4, поля 8 pt; кадр 37,6 pt для всех знаков; промежуток между группами
    в строке 0,45 кадра, между строками 0,22 кадра; на страницах нет текста.

ЧТО НУЖНО
    pip install playwright && playwright install chromium

ЛИЦЕНЗИЯ ДАННЫХ
    SVG-файлы AnimCJK распространяются по Arphic Public License
    (текст: https://ftp.gnu.org/non-gnu/chinese-fonts-truetype/LICENSE);
    шапка с лицензией сохранена в каждом файле animcjk/*.svg.
"""
import math, os, re, sys, urllib.request

K = "一二三四五六七八人方生先十九子川女戸天水日今友木手本足何大山文冬年地花私図男英学東洋室連紙書第教語科"

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PW, PH, M = 595.28, 841.89, 8.0      # A4 и поля, pt
CELL = 37.6                          # размер кадра, pt
GX, GY = 0.45, 0.22                  # промежутки в долях кадра
U = 1024                             # поле AnimCJK


def load(ch):
    """-> [(контуры черты, точки осевой линии)] по порядку черт."""
    p = os.path.join(HERE, "animcjk", f"{ord(ch)}.svg")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        urllib.request.urlretrieve(
            f"https://raw.githubusercontent.com/parsimonhi/animCJK/master/svgsJa/{ord(ch)}.svg", p)
    txt = open(p, encoding="utf-8").read()
    shapes, medians = {}, {}
    for n, d in re.findall(r'<path\s+id="z\d+d(\d+)[a-z]?"\s+d="([^"]+)"', txt):
        shapes.setdefault(int(n), []).append(d)
    for n, d in re.findall(r'clip-path="url\(#z\d+c(\d+)[a-z]?\)"\s+d="([^"]+)"', txt):
        pts = [complex(float(x), float(y)) for x, y in re.findall(r'(-?[\d.]+)[ ,](-?[\d.]+)', d)]
        medians.setdefault(int(n), []).extend(pts)
    assert shapes and sorted(shapes) == sorted(medians), f"не разобран файл для {ch}"
    return [(shapes[n], medians[n]) for n in sorted(shapes)]


def resample(pts, step=16.0):
    """Точки вдоль ломаной через равные промежутки."""
    out = [pts[0]]; carry = 0.0
    for a, b in zip(pts, pts[1:]):
        L = abs(b - a)
        if L == 0: continue
        t = step - carry
        while t <= L:
            out.append(a + (b - a) * t / L); t += step
        carry = (carry + L) % step
    if abs(out[-1] - pts[-1]) > 1: out.append(pts[-1])
    return out


def arrow(k, strokes):
    """Стрелка вдоль начала черты k, сдвинутая вбок от неё: на ту сторону,
    где она меньше задевает уже написанные черты и край кадра."""
    med = resample(strokes[k][1])
    L = 16.0 * (len(med) - 1)
    alen = min(max(L * 0.7, 190.0), 520.0)
    seg = med[: int(alen / 16) + 1]
    if len(seg) < 2: seg = med[:2]
    if L < alen:                                   # короткая черта: продолжить прямо
        t = seg[-1] - seg[-2]; t /= abs(t)
        seg = seg + [seg[-1] + t * s for s in range(16, int(alen - L) + 1, 16)]
    obst = [p for kk in range(k) for p in resample(strokes[kk][1])] + [p for p in med if abs(p - med[0]) > alen + 150]
    best = None
    for off in (95, -95, 125, -125):
        poly = []
        for i, p in enumerate(seg):
            t = seg[min(i + 3, len(seg) - 1)] - seg[max(i - 3, 0)]; t /= abs(t)
            poly.append(p + off * t * 1j)
        clear = min([abs(a - p) for a in poly for p in obst]
                    + [min(a.real, a.imag, U - a.real, U - a.imag) + 40 for a in poly] + [400])
        score = clear - (25 if abs(off) > 100 else 0)
        if best is None or score > best[0]: best = (score, poly)
    poly = best[1]
    t = poly[-1] - poly[-2]; t /= abs(t); n = t * 1j
    tri = [poly[-1] + t * 74, poly[-1] + n * 36, poly[-1] - n * 36]
    fmt = lambda ps: " ".join(f"{p.real:.0f},{p.imag:.0f}" for p in ps)
    return f'<polyline points="{fmt(poly)}" class="a"/><polygon points="{fmt(tri)}" class="h"/>'


def strip(ch):
    strokes = load(ch)
    sc = CELL / U
    cells = ['<g transform="scale(%.5f)">%s</g>' % (sc, "".join(f'<path d="{d}" class="k"/>' for s, _ in strokes for d in s))]
    for i in range(len(strokes)):
        g = "".join(f'<path d="{d}" class="g"/>' for s, _ in strokes[i + 1:] for d in s)
        g += "".join(f'<path d="{d}" class="o"/>' for s, _ in strokes[:i] for d in s)
        g += "".join(f'<path d="{d}" class="n"/>' for d in strokes[i][0]) + arrow(i, strokes)
        cells.append('<g transform="translate(%.2f,0) scale(%.5f)">%s</g>' % (CELL * (i + 1), sc, g))
    return CELL * (len(strokes) + 1), "".join(cells)


def build(out):
    strips = [strip(ch) for ch in K]
    rows, cur, x = [], [], 0.0
    for w, g in strips:                             # группы в строку, пока помещаются
        if cur and x + GX * CELL + w > PW - 2 * M: rows.append(cur); cur, x = [], 0.0
        if cur: x += GX * CELL
        cur.append((x, g)); x += w
    rows.append(cur)
    pitch = CELL * (1 + GY)
    per = int((PH - 2 * M + CELL * GY) // pitch)    # строк на страницу
    pages = []
    for p in range(0, len(rows), per):
        body = "".join(f'<g transform="translate({M + x:.2f},{M + r * pitch:.2f})">{g}</g>'
                       for r, row in enumerate(rows[p:p + per]) for x, g in row)
        pages.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}pt" height="{PH - 1}pt" '
                     f'viewBox="0 0 {PW} {PH - 1}">{body}</svg>')
    css = ("@page{size:A4;margin:0}html,body{margin:0}svg{display:block;page-break-after:always}"
           ".k,.n{fill:#000}.o{fill:#8c8c8c}.g{fill:#ececec}"
           ".a{fill:none;stroke:#e06060;stroke-width:18;stroke-linecap:round;stroke-linejoin:round}.h{fill:#e06060}")
    html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(pages)}</body></html>'
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(); page = b.new_page()
        page.set_content(html)
        page.pdf(path=out, format="A4", print_background=True, page_ranges=f"1-{len(pages)}",
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    print(f"{out}: знаков {len(K)}, строк {len(rows)}, страниц {len(pages)}, кадр {CELL} pt")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "!_kanji_strokes.pdf"))
