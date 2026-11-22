#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собрать !_kanji_all_text.pdf — таблицы иероглифов, набранные шрифтом (не скан).

Данные: kanji_table.py рядом (перепечатаны со сканов _scans/kanji001, 002, 004).
Вид строки, как в учебнике: иероглиф | он над чертой, кун под чертой |
значение | ключ | № ключа. Один лист A4: слева уроки 4 и 5, справа урок 6.
Поля 8 pt, на странице нет заголовков — экономим чернила и бумагу.

Запуск (из корня репозитория):
    python3 _kanji_src/build_kanji_table.py            # пишет !_kanji_all_text.pdf
    python3 _kanji_src/build_kanji_table.py out.pdf

Нужно: pip install playwright && playwright install chromium,
и японский шрифт в системе (Noto Serif/Sans CJK JP, Hiragino или Yu).
"""
import html, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from kanji_table import TABLES

CSS = """
@page{size:A4;margin:0} html,body{margin:0}
body{font-family:"DejaVu Sans","Helvetica Neue",Arial,sans-serif;font-size:8.5pt;color:#000}
.page{box-sizing:border-box;width:210mm;height:296.5mm;padding:8pt;display:flex;gap:10pt}
.col{flex:1;display:flex;flex-direction:column}
.gap{flex:0 0 7pt}
.row{flex:1 1 0;display:grid;grid-template-columns:30pt 76pt 1fr 40pt 20pt;align-items:center;
     column-gap:5pt;border-bottom:0.3pt solid #bbb;min-height:0}
.row.first{border-top:0.3pt solid #bbb}
.jp{font-family:"Noto Serif CJK JP","Hiragino Mincho ProN","Yu Mincho","Noto Sans CJK JP",serif}
.k{font-size:21pt;line-height:1;text-align:center}
.r{font-size:8.5pt;text-align:center;line-height:1.25}
.r .on{display:block;border-bottom:0.5pt solid #000;padding-bottom:0.5pt;margin:0 4pt}
.r .kun{display:block;padding-top:0.5pt;min-height:8pt}
.m{line-height:1.2}
.m.two span{display:block}
.key{font-size:12pt;text-align:center;white-space:nowrap}
.n{text-align:right;padding-right:2pt}
"""

def row(r, first):
    k, on, kun, m1, m2, key, no = r
    e = html.escape
    m = f'<div class="m two"><span>{e(m1)}</span><span>{e(m2)}</span></div>' if m2 else f'<div class="m">{e(m1)}</div>'
    return (f'<div class="row{" first" if first else ""}"><div class="k jp">{k}</div>'
            f'<div class="r jp"><span class="on">{e(on)}</span><span class="kun">{e(kun)}</span></div>'
            f'{m}<div class="key jp">{e(key)}</div><div class="n">{no}</div></div>')

def column(tables):
    out = []
    for i, (_, rows) in enumerate(tables):
        if i: out.append('<div class="gap"></div>')
        out += [row(r, j == 0) for j, r in enumerate(rows)]
    return '<div class="col">' + "".join(out) + '</div>'

def build(out):
    body = '<div class="page">' + column(TABLES[:2]) + column(TABLES[2:]) + '</div>'
    doc = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(); page = b.new_page()
        page.set_content(doc)
        page.pdf(path=out, format="A4", print_background=True, page_ranges="1",
                 margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    print(out, "иероглифов:", sum(len(r) for _, r in TABLES))

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "!_kanji_all_text.pdf"))
