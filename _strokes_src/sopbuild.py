import json, sys
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
K = "一二三四五六七八人方生先十九子川女戸天水日今友木手本足何大山文冬年地花私図男英学東洋室連紙書第教語科"
NP = int(sys.argv[2])
sp = Image.open('sop_sprite.png')
meta = {m[0]: m for m in json.load(open('sop_meta.json'))['m']}
miss = json.load(open('miss.json'))
ROW1 = {"学": 8, "連": 6, "書": 9, "第": 10, "教": 9, "語": 9}   # frames in the first row of two-row strips
NSTROKES = json.load(open('nstrokes.json'))
items = []   # (char, image, frame pitch in px)
for ch in K:
    if ch in meta:
        _, y, w, h, v = meta[ch]
        im = sp.crop((0, y, w, y+h))
    else:
        im = Image.open(f'miss_{miss[ch][2]}.png').convert('RGB')
    frames = ROW1.get(ch, NSTROKES[ch] + 1)
    items.append((ch, im, im.width/frames))
W, H = A4; M = 8; GX, GY = 0.45, 0.22
def layout(cell):
    rows = []; cur = []; x = 0
    for ch, im, pitch in items:
        f = cell/pitch; w = im.width*f; h = im.height*f
        if cur and x + GX*cell + w > W-2*M: rows.append(cur); cur = []; x = 0
        if cur: x += GX*cell
        cur.append((ch, im, h, x, w)); x += w
    rows.append(cur)
    return rows
def paginate(rows, cell):
    pages = [[]]; y = 0
    for row in rows:
        h = max(hh for _, _, hh, _, _ in row)
        if pages[-1] and y + h > H-2*M: pages.append([]); y = 0
        pages[-1].append((row, y, h)); y += h + GY*cell
    return pages
cell = 60.0
while True:
    rows = layout(cell)
    if max(x+w for row in rows for _, _, _, x, w in row) <= W-2*M:
        pages = paginate(rows, cell)
        if len(pages) <= NP: break
    cell -= 0.1
print('cell pt', cell, 'pages', len(pages), [len(p) for p in pages])
c = canvas.Canvas(sys.argv[1], pagesize=A4)
for pg in pages:
    for row, y, h in pg:
        for ch, im, hh, x, w in row:
            c.drawImage(ImageReader(im), M+x, H-M-y-(h+hh)/2, w, hh)
    c.showPage()
c.save()
