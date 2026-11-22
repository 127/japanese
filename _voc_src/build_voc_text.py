#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Собрать !_kanji_voc_all_text.pdf — словари, фразы и таблицы иероглифов уроков 1–6,
набранные шрифтом (текстовая версия сборника !_kanji_voc_all_scan.pdf).

Данные: voc_data.py рядом (перепечатаны со сканов из _scans/); таблицы иероглифов
берутся из _kanji_src/kanji_table.py и рисуются так же, как в !_kanji_all_text.pdf.
Порядок блоков — строго как в учебнике. Лист A4, поля 8 pt, две колонки: текст идёт сверху вниз по левой, потом по правой.
Весь текст одного размера (SIZE); крупнее только сам иероглиф в таблицах.
Выделение тона жирным из сканов сюда не перенесено.

Запуск (из корня репозитория):
    python3 _voc_src/build_voc_text.py            # пишет !_kanji_voc_all_text.pdf
    python3 _voc_src/build_voc_text.py out.pdf

Нужно: pip install playwright && playwright install chromium,
и японский шрифт в системе (Noto Serif/Sans CJK JP, Hiragino или Yu).
"""
import html, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "_kanji_src"))
from voc_data import BLOCKS
import build_kanji_table as kt

SIZE = os.environ.get("VOC_SIZE", "10.5pt")          # единый размер всего текста; крупнее только сам иероглиф в таблице
CSS = kt.CSS + """
@page{size:A4;margin:8pt}
body{column-count:2;column-gap:14pt;font-size:SIZE;line-height:1.15}
h4{font-size:SIZE;font-weight:normal;color:#777;margin:5pt 0 1pt;break-after:avoid;border-bottom:0.3pt solid #bbb}
h4:first-child{margin-top:0}
.row{height:auto;min-height:calc(SIZE * 2.6);padding:0.5pt 0;flex:none;break-inside:avoid;grid-template-columns:calc(SIZE * 2.9) calc(SIZE * 8.4) 1fr calc(SIZE * 3.3) calc(SIZE * 2.2)}
.row .k{font-size:calc(SIZE * 2.1)}
.row .r,.row .m,.row .key,.row .n{font-size:SIZE;line-height:1.12}
.e{display:grid;column-gap:6pt;break-inside:avoid;padding:0.3pt 0}
.e>span{min-width:0;overflow-wrap:break-word}
.e.v2{grid-template-columns:calc(SIZE * 8.5) 1fr}
.e.v3{grid-template-columns:calc(SIZE * 6.5) calc(SIZE * 8.5) 1fr}
.e.p{grid-template-columns:47% 1fr}
.e.s{grid-template-columns:calc(SIZE * 8.7) 1fr}
.w,.rd{font-size:SIZE;line-height:1.15}
.rd{color:#444}
.w,.rd,.row .r,.row .key{font-family:"Noto Sans CJK JP","Hiragino Sans","Yu Gothic",sans-serif}
""".replace("SIZE", SIZE)
e = html.escape
JP = lambda t: f'<span class="jp w">{e(t)}</span>'

def block(kind, title, scan, rows):
    out = [f'<h4>{e(title)}</h4>']
    if kind == "kanji":
        out += [kt.row(r, False) for r in rows]
    elif kind == "voc":
        three = any(r[1] for r in rows)
        for w, rd, tr in rows:
            mid = f'<span class="jp rd">{e(rd)}</span>' if three else ""
            out.append(f'<div class="e v{3 if three else 2}">{JP(w)}{mid}<span>{e(tr)}</span></div>')
    elif kind == "phr":
        for ph, tr in rows:
            jp = any(ord(c) > 0x3000 for c in ph)
            out.append(f'<div class="e p">{JP(ph) if jp else "<span>"+e(ph)+"</span>"}<span>{e(tr)}</span></div>')
    elif kind == "spell":
        for a, b in rows:
            out.append(f'<div class="e s">{JP(a)}<span class="jp rd">{e(b)}</span></div>')
    return "".join(out)

def build(out):
    body = "".join(block(*b) for b in BLOCKS)
    doc = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>'
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(); page = b.new_page()
        page.set_content(doc)
        page.evaluate(kt.FIT_JS, False)      # ужать только те чтения, что шире своей ячейки
        page.pdf(path=out, format="A4", print_background=True, prefer_css_page_size=True)
        b.close()
    print(out, "блоков:", len(BLOCKS))

if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "!_kanji_voc_all_text.pdf"))
