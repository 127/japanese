#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Дорисовать полосу порядка черт для иероглифа, которого НЕТ на Викискладе.

ЗАЧЕМ
    !_kanji_strokes.pdf собирается из готовых картинок Викисклада
    (Commons: CJK Stroke Order Project, файлы 字-jbw.png / 字-bw.png).
    Для части знаков таких картинок нет (так было с 戸, 洋, 紙). Этот скрипт
    рисует для них полосу в том же стиле из данных KanjiVG: иероглиф целиком,
    затем по кадру на черту — написанные черты тёмные, ненаписанные бледные,
    зелёная точка в начале новой черты, красная стрелка рядом с ней.

КОГДА ЗАПУСКАТЬ
    Появился новый иероглиф, а на Викискладе нет ни 字-jbw.png, ни 字-bw.png.
    Если картинка на Викискладе есть — брать её, а не рисовать (см. AGENTS.md).

КАК ЗАПУСКАТЬ (из папки _strokes_src)
    python3 draw_missing.py 戸 洋 紙

    Для каждого знака скрипт:
      1. берёт kvg/<код>.svg; если файла нет — скачивает его из KanjiVG
         (https://github.com/KanjiVG/kanjivg, kanji/<код>.svg, код = 5 цифр hex);
      2. пишет полосу miss_<код>.png (кадр 120x120 px, кадров = черт + 1);
      3. дописывает знак в miss.json (ширина, высота, код) и nstrokes.json.
    После этого добавить знак в строку K в sopbuild.py (в нужном месте по
    порядку учебника) и пересобрать: python3 sopbuild.py out.pdf <страниц>.

ЧТО НУЖНО
    pip install svgpathtools playwright && playwright install chromium

ЛИЦЕНЗИЯ ДАННЫХ
    KanjiVG — CC BY-SA 3.0 (© Ulrich Apel), полученные картинки — тоже.
"""
import json, os, re, sys, urllib.request
from svgpathtools import parse_path
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
F = 120                 # размер кадра в пикселях (как шаг кадра на Викискладе, ~120)
SC = F / 109            # KanjiVG рисует в поле 109x109


def kvg_paths(ch):
    code = f"{ord(ch):05x}"
    p = os.path.join(HERE, "kvg", code + ".svg")
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        url = f"https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/{code}.svg"
        urllib.request.urlretrieve(url, p)
    return code, re.findall(r'<path[^>]*\sd="([^"]+)"', open(p, encoding="utf-8").read())


def sample(path, step=2.0):
    L = path.length(); n = max(2, int(L / step))
    return L, [path.point(path.ilength(min(L, L * i / n))) for i in range(n + 1)]


def arrow(k, strokes):
    """Красная стрелка рядом с началом черты k: идёт вдоль черты, сдвинута вбок
    на ту сторону, где меньше мешает уже написанным чертам."""
    L, pts = strokes[k]
    alen = min(max(L * 0.75, 14), 60)
    seg = [p for i, p in enumerate(pts) if i * L / (len(pts) - 1) <= alen]
    if len(seg) < 2: seg = pts[:2]
    obst = [p for kk in range(k) for p in strokes[kk][1]] + [p for p in pts if abs(p - pts[0]) > alen + 12]
    best = None
    for off in (7, -7, 10, -10):
        poly = []
        for i, p in enumerate(seg):
            t = seg[min(i + 1, len(seg) - 1)] - seg[max(i - 1, 0)]; t = t / abs(t) if abs(t) else 1
            poly.append(p + off * t * 1j)
        clear = min([abs(a - p) for a in poly for p in obst]
                    + [min(a.real, a.imag, 109 - a.real, 109 - a.imag) + 4 for a in poly] + [50])
        score = clear - (1.5 if abs(off) > 8 else 0)
        if best is None or score > best[0]: best = (score, poly)
    poly = best[1]
    t = poly[-1] - poly[-2]; t = t / abs(t) if abs(t) else 1
    n = t * 1j
    tri = [poly[-1] + t * 4, poly[-1] - t * 2 + n * 2.8, poly[-1] - t * 2 - n * 2.8]
    fmt = lambda ps: " ".join(f"{p.real:.1f},{p.imag:.1f}" for p in ps)
    return f'<path d="M{fmt(poly).replace(" ", " L")}" class="a"/><polygon points="{fmt(tri)}" fill="#e87878"/>'


def strip_svg(ds):
    strokes = [sample(parse_path(p)) for p in ds]
    n = len(ds); W = F * (n + 1)
    g = [f'<g transform="scale({SC:.4f})">' + "".join(f'<path d="{p}" class="k"/>' for p in ds) + "</g>"]
    for i in range(n):
        s0 = strokes[i][1][0]
        g.append(f'<g transform="translate({F * (i + 1)},0) scale({SC:.4f})">'
                 + "".join(f'<path d="{p}" class="g"/>' for p in ds[i + 1:])
                 + "".join(f'<path d="{p}" class="o"/>' for p in ds[:i + 1])
                 + arrow(i, strokes)
                 + f'<circle cx="{s0.real:.1f}" cy="{s0.imag:.1f}" r="3.2" fill="#55dd55"/></g>')
    css = ("path{fill:none;stroke-linecap:round;stroke-linejoin:round}.k{stroke:#000;stroke-width:5.5}"
           ".o{stroke:#555;stroke-width:5}.g{stroke:#e6e6e6;stroke-width:5}.a{stroke:#e87878;stroke-width:1.3}")
    return W, (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{F}" viewBox="0 0 {W} {F}">'
               f'<style>{css}</style><rect width="{W}" height="{F}" fill="#fff"/>{"".join(g)}</svg>')


def load(name):
    p = os.path.join(HERE, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def main(chars):
    if not chars:
        sys.exit(__doc__)
    miss, nst = load("miss.json"), load("nstrokes.json")
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for ch in chars:
            code, ds = kvg_paths(ch)
            W, svg = strip_svg(ds)
            page = b.new_page(viewport={"width": W, "height": F}, device_scale_factor=1)
            page.set_content(f'<!DOCTYPE html><html><body style="margin:0">{svg}</body></html>')
            page.screenshot(path=os.path.join(HERE, f"miss_{code}.png"))
            page.close()
            miss[ch] = [W, F, code]; nst[ch] = len(ds)
            print(ch, code, "черт:", len(ds), "->", f"miss_{code}.png")
        b.close()
    for name, d in (("miss.json", miss), ("nstrokes.json", nst)):
        json.dump(d, open(os.path.join(HERE, name), "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1:])
