"""Generate docs/assets/demo.gif for the Text-to-SQL Agent README."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
W, H = 1100, 640

INK = (19, 32, 25)
INK_SOFT = (42, 64, 52)
MOSS = (31, 107, 74)
MOSS_DEEP = (15, 61, 44)
LINE = (197, 212, 200)
CITRUS = (224, 122, 47)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_BRAND = font(42, True)
F_H = font(22, True)
F_B = font(16, False)
F_S = font(13, False)
F_XS = font(11, True)


def bg() -> Image.Image:
    img = Image.new("RGB", (W, H), (243, 246, 241))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((-200, -180, 700, 420), fill=(217, 235, 224, 90))
    od.ellipse((700, -120, 1300, 380), fill=(245, 230, 212, 80))
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def round_rect(draw: ImageDraw.ImageDraw, xy, r, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def draw_shell(status_live: bool = False, status_text: str = "No database"):
    img = bg()
    d = ImageDraw.Draw(img)
    d.text((40, 28), "Text-to-SQL", font=F_BRAND, fill=MOSS_DEEP)
    d.text(
        (40, 78),
        "Ask your database in plain language. Schema-grounded agentic SQL.",
        font=F_B,
        fill=INK_SOFT,
    )
    sw = 130
    sx0, sy0, sx1, sy1 = W - 40 - sw, 36, W - 40, 68
    if status_live:
        round_rect(d, (sx0, sy0, sx1, sy1), 2, (228, 243, 234), MOSS, 1)
        d.text((sx0 + 18, sy0 + 7), status_text.upper(), font=F_XS, fill=MOSS)
    else:
        round_rect(d, (sx0, sy0, sx1, sy1), 2, (255, 246, 236), (216, 196, 176), 1)
        d.text((sx0 + 12, sy0 + 7), status_text.upper(), font=F_XS, fill=CITRUS)
    d.line((40, 112, W - 40, 112), fill=LINE, width=1)
    left = (40, 130, 480, H - 36)
    right = (500, 130, W - 40, H - 36)
    round_rect(d, left, 2, WHITE, LINE, 1)
    round_rect(d, right, 2, WHITE, LINE, 1)
    d.text((56, 144), "SCHEMA ATELIER", font=F_XS, fill=MOSS)
    d.text((516, 144), "CONVERSATION", font=F_XS, fill=MOSS)
    return img, d


def frame_connect() -> Image.Image:
    img, d = draw_shell(False, "No database")
    round_rect(d, (56, 175, 464, 360), 2, (248, 251, 248), LINE, 1)
    d.text((72, 200), "Wire up a database", font=F_H, fill=MOSS_DEEP)
    d.text((72, 240), "Paste a SQLAlchemy URI. PostgreSQL works best.", font=F_S, fill=INK_SOFT)
    for i, t in enumerate(["discover → ground", "synthesize → critique"]):
        x = 72 + i * 160
        round_rect(d, (x, 280, x + 150, 305), 12, WHITE, LINE, 1)
        d.text((x + 10, 285), t, font=F_XS, fill=INK_SOFT)
    round_rect(d, (56, 390, 464, 430), 2, WHITE, LINE, 1)
    d.text((68, 400), "postgresql://demo:demo@postgres:5432/hr_demo", font=F_S, fill=INK)
    round_rect(d, (56, 450, 280, 490), 2, MOSS_DEEP)
    d.text((88, 460), "Connect database", font=F_B, fill=(244, 250, 246))
    round_rect(d, (516, 175, W - 56, 500), 2, (248, 251, 248), LINE, 1)
    d.text((540, 260), "Conversation waits", font=F_H, fill=MOSS_DEEP)
    d.text((540, 300), "on a connection", font=F_H, fill=MOSS_DEEP)
    d.text((540, 350), "Link a DB, then ask about headcount,", font=F_S, fill=INK_SOFT)
    d.text((540, 372), "salaries, or hire dates in plain English.", font=F_S, fill=INK_SOFT)
    return img


def frame_connected_browse() -> Image.Image:
    img, d = draw_shell(True, "Connected")
    d.text((56, 175), "Session a3f9c2e1…", font=F_S, fill=INK_SOFT)
    round_rect(d, (300, 170, 464, 205), 2, MOSS_DEEP)
    d.text((335, 178), "Disconnect", font=F_S, fill=WHITE)
    d.text((56, 220), "Browse table", font=F_S, fill=INK_SOFT)
    round_rect(d, (56, 245, 464, 285), 2, WHITE, LINE, 1)
    d.text((68, 255), "employees ▾", font=F_B, fill=INK)
    d.text((56, 300), "17 rows · preview", font=F_XS, fill=INK_SOFT)
    headers = ["id", "first_name", "department", "salary"]
    rows = [
        ["1", "John", "Engineering", "75000"],
        ["2", "Jane", "Engineering", "80000"],
        ["3", "Alice", "HR", "65000"],
        ["4", "Bob", "Engineering", "70000"],
        ["5", "Emma", "Marketing", "68000"],
    ]
    col_w = [50, 110, 130, 90]
    y0 = 325
    round_rect(d, (56, y0, 464, y0 + 28), 2, (220, 232, 224), LINE, 1)
    x = 64
    for h, w in zip(headers, col_w):
        d.text((x, y0 + 6), h, font=F_XS, fill=MOSS_DEEP)
        x += w
    for i, row in enumerate(rows):
        y = y0 + 28 + i * 26
        if i % 2 == 0:
            d.rectangle((56, y, 464, y + 26), fill=(248, 251, 248))
        x = 64
        for cell, w in zip(row, col_w):
            d.text((x, y + 5), cell, font=F_S, fill=INK)
            x += w
    d.rectangle((56, y0, 464, y0 + 28 + 5 * 26), outline=LINE)
    round_rect(d, (516, 175, W - 56, 420), 2, (248, 251, 248), LINE, 1)
    d.text((540, 250), "Ask anything about the data", font=F_H, fill=MOSS_DEEP)
    d.text((540, 295), "The agent will list tables, pull schema,", font=F_S, fill=INK_SOFT)
    d.text((540, 317), "draft SQL, review it, run it, and reply.", font=F_S, fill=INK_SOFT)
    round_rect(d, (516, 520, W - 56, 570), 2, WHITE, LINE, 1)
    d.text((532, 535), "Ask about your data…", font=F_B, fill=(150, 170, 158))
    return img


def frame_typing() -> Image.Image:
    img, d = draw_shell(True, "Connected")
    d.text((56, 175), "employees · preview", font=F_S, fill=INK_SOFT)
    round_rect(d, (56, 210, 464, 500), 2, (248, 251, 248), LINE, 1)
    d.text((72, 230), "Schema grounded · 17 rows loaded", font=F_B, fill=MOSS)
    round_rect(d, (516, 175, W - 56, 250), 2, WHITE, LINE, 1)
    d.text((532, 185), "YOU", font=F_XS, fill=MOSS)
    d.text((532, 210), "How many employees are in Engineering?", font=F_B, fill=INK)
    round_rect(d, (516, 270, W - 56, 360), 2, (228, 243, 234), MOSS, 1)
    d.text((532, 285), "AGENT", font=F_XS, fill=MOSS)
    d.text((532, 315), "Agent looping: schema → SQL → critique…", font=F_B, fill=MOSS_DEEP)
    for x in (532, 552, 572):
        d.ellipse((x, 340, x + 8, 348), fill=MOSS)
    round_rect(d, (516, 520, W - 56, 570), 2, WHITE, LINE, 1)
    d.text((532, 535), "How many employees are in Engineering?", font=F_B, fill=INK)
    return img


def frame_answer() -> Image.Image:
    img, d = draw_shell(True, "Connected")
    d.text((56, 175), "employees · preview", font=F_S, fill=INK_SOFT)
    round_rect(d, (56, 210, 464, 500), 2, (248, 251, 248), LINE, 1)
    d.text((72, 230), "Generated SQL (reviewed)", font=F_XS, fill=MOSS)
    round_rect(d, (72, 260, 448, 380), 2, MOSS_DEEP)
    d.text((88, 280), "SELECT COUNT(*) AS n", font=F_S, fill=(196, 230, 210))
    d.text((88, 305), "FROM employees", font=F_S, fill=(196, 230, 210))
    d.text((88, 330), "WHERE LOWER(department)", font=F_S, fill=(196, 230, 210))
    d.text((88, 355), "  LIKE '%engineering%';", font=F_S, fill=(196, 230, 210))
    round_rect(d, (516, 175, W - 56, 245), 2, WHITE, LINE, 1)
    d.text((532, 185), "YOU", font=F_XS, fill=MOSS)
    d.text((532, 210), "How many employees are in Engineering?", font=F_B, fill=INK)
    round_rect(d, (516, 265, W - 56, 430), 2, WHITE, LINE, 1)
    d.text((532, 280), "AGENT", font=F_XS, fill=MOSS)
    d.text((532, 315), "There are 7 employees in the", font=F_B, fill=INK)
    d.text((532, 340), "Engineering department.", font=F_B, fill=INK)
    d.text((532, 380), "Query checked · executed · answered", font=F_S, fill=MOSS)
    round_rect(d, (516, 520, W - 56, 570), 2, WHITE, LINE, 1)
    d.text((532, 535), "Ask about your data…", font=F_B, fill=(150, 170, 158))
    return img


def main() -> None:
    frames: list[Image.Image] = []
    for fn, n in (
        (frame_connect, 12),
        (frame_connected_browse, 12),
        (frame_typing, 10),
        (frame_answer, 16),
    ):
        frame = fn()
        frames.extend([frame] * n)
    out = OUT / "demo.gif"
    frames[0].save(
        out,
        save_all=True,
        append_images=frames[1:],
        duration=120,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
