# -*- coding: utf-8 -*-
"""
水豚噜噜 — 桌面宠物 (Windows Desktop Pet)
一只佛系芒果状的卡皮巴拉，在你的桌面上悠闲漫步。
双击退出，拖拽移动。
"""
import tkinter as tk
import math
import time
import random
import sys

# ---------- 窗口设置 ----------
WIN_W, WIN_H = 220, 240
BG_COLOR = '#f0f0f0'  # transparent color key

root = tk.Tk()
root.title('噜噜')
root.geometry(f'{WIN_W}x{WIN_H}+{root.winfo_screenwidth()-280}+{root.winfo_screenheight()-350}')
root.overrideredirect(True)
root.wm_attributes('-topmost', True)
root.wm_attributes('-transparentcolor', BG_COLOR)
root.configure(bg=BG_COLOR)

# ---------- Canvas ----------
canvas = tk.Canvas(root, width=WIN_W, height=WIN_H, bg=BG_COLOR,
                    highlightthickness=0, bd=0)
canvas.pack(fill=tk.BOTH, expand=True)

# ---------- 状态 ----------
class State:
    pass

s = State()
s.t = 0
s.mood = 'idle'      # idle | blink | happy | eat | sleep | laugh
s.ear_wiggle = 0.0
s.mouth_open = 0.0
s.sparkles = []
s.eye_offset = 0     # 0=normal, 1=look right
s.sleep_mode = False
s.drag_x = 0
s.drag_y = 0
s.dragging = False
s.click_count = 0
s.last_click_time = 0
s.happy_timer = 0

# ---------- 绘制 ----------
def draw_pet():
    canvas.delete('all')
    w, h = WIN_W, WIN_H
    cx, cy = w // 2, h // 2 - 10

    t = time.time()
    s.t = t

    breathe = math.sin(t * 1.8) * 2
    body_y = cy + 20 + breathe

    # ---- 身体 (芒果状) ----
    body_grad = canvas.create_oval(
        cx - 55, body_y - 50, cx + 55, body_y + 50,
        fill='#dda048', outline='#c88a30', width=1
    )
    # 肚子高光
    canvas.create_oval(
        cx - 25, body_y - 30, cx + 25, body_y + 35,
        fill='#e8b966', outline=''
    )

    # ---- 短短腿 ----
    leg_color = '#c48430'
    canvas.create_oval(cx - 32, body_y + 40, cx - 18, body_y + 52,
                       fill=leg_color, outline='')
    canvas.create_oval(cx + 18, body_y + 40, cx + 32, body_y + 52,
                       fill=leg_color, outline='')

    # ---- 小尾巴 ----
    tail_wag = math.sin(t * 3) * 4
    canvas.create_oval(cx + 50, body_y - 12 + tail_wag,
                       cx + 62, body_y + 2 + tail_wag,
                       fill='#c48430', outline='')

    # ---- 耳朵 ----
    ew = s.ear_wiggle * math.sin(t * 20) * 4 if s.ear_wiggle > 0.01 else 0
    # 左耳
    canvas.create_oval(cx - 42 + ew, body_y - 56, cx - 24 + ew, body_y - 38,
                       fill='#d69840', outline='')
    canvas.create_oval(cx - 40 + ew, body_y - 54, cx - 26 + ew, body_y - 40,
                       fill='#e8b060', outline='')
    # 右耳
    canvas.create_oval(cx + 24 - ew, body_y - 56, cx + 42 - ew, body_y - 38,
                       fill='#d69840', outline='')
    canvas.create_oval(cx + 26 - ew, body_y - 54, cx + 40 - ew, body_y - 40,
                       fill='#e8b060', outline='')

    # ---- 腮红 ----
    canvas.create_oval(cx - 44, body_y - 6, cx - 30, body_y + 8,
                       fill='#eb7850', outline='', stipple='gray25')
    canvas.create_oval(cx + 30, body_y - 6, cx + 44, body_y + 8,
                       fill='#eb7850', outline='', stipple='gray25')

    # ---- 眼睛 ----
    eye_y = body_y - 12
    # 眨眼
    blink = False
    if s.mood == 'sleep' or s.sleep_mode:
        blink = True
    elif s.mood == 'blink':
        blink = True

    eye_h = 2 if blink else 10

    # 眼白
    canvas.create_oval(cx - 25, eye_y - eye_h, cx - 11, eye_y + eye_h,
                       fill='#faf8f0', outline='#8a7a5a', width=1)
    canvas.create_oval(cx + 11, eye_y - eye_h, cx + 25, eye_y + eye_h,
                       fill='#faf8f0', outline='#8a7a5a', width=1)

    if not blink:
        p_off = s.eye_offset * 3
        # 瞳孔
        canvas.create_oval(cx - 20 + p_off, eye_y - 6,
                           cx - 14 + p_off, eye_y + 5,
                           fill='#2a1a0a', outline='')
        canvas.create_oval(cx + 14 + p_off, eye_y - 6,
                           cx + 20 + p_off, eye_y + 5,
                           fill='#2a1a0a', outline='')
        # 高光
        canvas.create_oval(cx - 23 + p_off, eye_y - 5,
                           cx - 20 + p_off, eye_y - 2,
                           fill='white', outline='')
        canvas.create_oval(cx + 17 + p_off, eye_y - 5,
                           cx + 20 + p_off, eye_y - 2,
                           fill='white', outline='')
    else:
        # 睡觉表情
        canvas.create_arc(cx - 24, eye_y - 2, cx - 12, eye_y + 4,
                          start=0, extent=180, style=tk.ARC,
                          outline='#5a4a32', width=2)
        canvas.create_arc(cx + 12, eye_y - 2, cx + 24, eye_y + 4,
                          start=0, extent=180, style=tk.ARC,
                          outline='#5a4a32', width=2)

    # ---- 鼻子 ----
    canvas.create_oval(cx - 5, body_y - 4, cx + 5, body_y + 4,
                       fill='#6a5030', outline='')
    canvas.create_oval(cx - 2, body_y - 5, cx + 2, body_y - 2,
                       fill='#8a6040', outline='')

    # ---- 嘴巴 (标志性漏齿笑) ----
    if s.sleep_mode:
        # 睡觉微笑
        canvas.create_arc(cx - 10, body_y + 6, cx + 10, body_y + 16,
                          start=0, extent=180, style=tk.ARC,
                          outline='#6a5030', width=2)
    elif s.mood in ('happy', 'laugh'):
        # 大笑
        canvas.create_oval(cx - 12, body_y + 4, cx + 12, body_y + 18,
                           fill='#3a2010', outline='')
        # 牙齿
        canvas.create_rectangle(cx - 7, body_y + 4, cx - 2, body_y + 10,
                                fill='white', outline='#6a5030', width=1)
        canvas.create_rectangle(cx + 2, body_y + 4, cx + 7, body_y + 10,
                                fill='white', outline='#6a5030', width=1)
    else:
        # 标志性牙齿笑
        canvas.create_arc(cx - 14, body_y + 2, cx + 14, body_y + 16,
                          start=0, extent=180, style=tk.ARC,
                          outline='#6a5030', width=2)
        canvas.create_rectangle(cx - 6, body_y + 4, cx - 1, body_y + 10,
                                fill='white', outline='#6a5030', width=1)
        canvas.create_rectangle(cx + 1, body_y + 4, cx + 6, body_y + 10,
                                fill='white', outline='#6a5030', width=1)

    # ---- 泡温泉蒸汽 (装饰) ----
    if s.mood in ('happy', 'laugh'):
        for i in range(3):
            sx = cx - 30 + i * 30 + math.sin(t * 1.5 + i * 2) * 6
            sy = body_y - 70 - i * 8 + math.sin(t * 2 + i) * 3
            canvas.create_oval(
                sx - 8, sy - 4, sx + 8, sy + 4,
                fill='', outline='rgba(255,255,255,0.4)', width=1
            )

    # ---- 光橘爆弹火花 ----
    for spark in s.sparkles[:]:
        spark['x'] += spark['vx']
        spark['y'] += spark['vy']
        spark['vy'] += 0.08
        spark['life'] -= 1
        if spark['life'] > 0:
            size = spark['r'] * (spark['life'] / 30)
            canvas.create_oval(
                spark['x'] - size, spark['y'] - size,
                spark['x'] + size, spark['y'] + size,
                fill=spark['color'], outline=''
            )
        else:
            s.sparkles.remove(spark)

    # ---- Zzz ----
    if s.sleep_mode:
        z_off = math.sin(t * 2) * 5
        canvas.create_text(cx + 55, body_y - 50 + z_off,
                           text='💤', font=('Segoe UI Emoji', 14), fill='')
        canvas.create_text(cx + 65, body_y - 68 + z_off * 0.5,
                           text='💤', font=('Segoe UI Emoji', 10), fill='')

    # ---- 状态条 ----
    bar_y = WIN_H - 15
    canvas.create_rectangle(20, bar_y, WIN_W - 20, bar_y + 8,
                            fill='#eedcc4', outline='', width=0)
    hp = 0.8 + math.sin(t * 1.5) * 0.05 + s.happy_timer * 0.001
    hp_w = max(0, min(1, hp))
    bar_color = '#f5b87c' if hp > 0.4 else '#e89354'
    canvas.create_rectangle(20, bar_y,
                            20 + (WIN_W - 40) * hp_w, bar_y + 8,
                            fill=bar_color, outline='', width=0)
    canvas.create_text(WIN_W // 2, bar_y + 4,
                       text=f'❤️ {int(hp * 100)}', font=('Segoe UI', 8),
                       fill='#7a5f3a')

    root.after(40, draw_pet)

# ---------- 交互 ----------
def on_click(event):
    global click_timer
    now = time.time()
    if now - s.last_click_time < 0.4:
        # 双击退出
        root.destroy()
        return
    s.last_click_time = now

    # 随机反应
    r = random.random()
    if r < 0.3:
        s.mood = 'blink'
        s.ear_wiggle = 1.0
        s.happy_timer = min(100, s.happy_timer + 5)
        root.after(600, lambda: setattr(s, 'mood', 'idle'))
    elif r < 0.5:
        s.mood = 'happy'
        s.ear_wiggle = 1.5
        s.happy_timer = min(100, s.happy_timer + 10)
        for _ in range(8):
            s.sparkles.append({
                'x': event.x, 'y': event.y,
                'vx': random.uniform(-2, 2), 'vy': random.uniform(-3, -0.5),
                'r': random.uniform(2, 5), 'life': 25 + random.random() * 20,
                'color': f'#ff{random.choice(["a0","b0","c0","80"])}{random.choice(["30","40","50"])}'
            })
        root.after(800, lambda: setattr(s, 'mood', 'idle'))
    else:
        s.eye_offset = random.choice([-1, 0, 0, 1])
        root.after(1000, lambda: setattr(s, 'eye_offset', 0))


def on_double_click(event):
    root.destroy()


def on_drag_start(event):
    s.drag_x = event.x
    s.drag_y = event.y
    s.dragging = True


def on_drag_move(event):
    if s.dragging:
        dx = event.x - s.drag_x
        dy = event.y - s.drag_y
        x = root.winfo_x() + dx
        y = root.winfo_y() + dy
        root.geometry(f'+{int(x)}+{int(y)}')


def on_drag_end(event):
    s.dragging = False


def on_right_click(event):
    # 右键菜单
    menu = tk.Menu(root, tearoff=0, bg='#fff8ee', fg='#6f5535',
                   activebackground='#f0e0c8', activeforeground='#5a3a20')
    menu.add_command(label='🎀 噜噜很好', command=lambda: None)
    menu.add_separator()
    menu.add_command(label='💤 睡觉', command=lambda: toggle_sleep())
    menu.add_command(label='🍊 吃橘子', command=lambda: feed_orange())
    menu.add_separator()
    menu.add_command(label='❌ 退出', command=root.destroy)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()


def toggle_sleep():
    s.sleep_mode = not s.sleep_mode
    if s.sleep_mode:
        s.mood = 'sleep'
    else:
        s.mood = 'idle'


def feed_orange():
    s.mood = 'happy'
    s.happy_timer = min(100, s.happy_timer + 20)
    # 橘子动画
    canvas.create_oval(80, 60, 100, 80, fill='#f09030', outline='')
    canvas.create_oval(84, 64, 96, 76, fill='#e08020', outline='')
    root.after(1500, lambda: setattr(s, 'mood', 'idle'))


# ---------- 事件绑定 ----------
canvas.bind('<Button-1>', on_click)
canvas.bind('<Double-Button-1>', on_double_click)
canvas.bind('<Button-3>', on_right_click)
canvas.bind('<ButtonPress-1>', on_drag_start)
canvas.bind('<B1-Motion>', on_drag_move)
canvas.bind('<ButtonRelease-1>', on_drag_end)

# ---------- 自动状态更新 ----------
def auto_update():
    if s.ear_wiggle > 0:
        s.ear_wiggle -= 0.02
    if s.happy_timer > 0:
        s.happy_timer -= 0.1
    # 随机眨眼
    if s.mood == 'idle' and random.random() < 0.005:
        s.mood = 'blink'
        root.after(300, lambda: setattr(s, 'mood', 'idle'))
    # 随机小表情
    if s.mood == 'idle' and random.random() < 0.003:
        s.ear_wiggle = 0.5
    root.after(200, auto_update)

# ---------- 启动 ----------
draw_pet()
auto_update()
root.mainloop()
