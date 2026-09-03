# Синтез SFX для Drop Zone (22 кГц, 16-бит, моно) — v2, переработка
import numpy as np
import wave, os

SR = 22050
OUT = r"G:\Kimi project\Drop Zone\game\assets\sfx"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)

def save(name, data):
    d = np.clip(data, -1.0, 1.0)
    pcm = (d * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(name, len(d) / SR, "s")

def lowpass(x, alpha):
    # простейший IIR-фильтр
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = acc + alpha * (x[i] - acc)
        y[i] = acc
    return y

def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)

# --- выстрел: щелчок + шумовой хлопок + низкий удар ---
tt = t(0.22)
noise = rng.standard_normal(len(tt))
shot = lowpass(noise, 0.35) * np.exp(-tt * 30) * 0.9
shot += np.sign(np.sin(2 * np.pi * 160 * tt)) * np.exp(-tt * 90) * 0.35
shot += np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 40) * 0.5
save("shot", shot * 0.9)

# --- взрыв: низкий свип + бурый шум + грохот ---
tt = t(1.1)
faze = 2 * np.pi * (120 * tt - 45 * tt ** 2)  # свип 120 -> ~30 Гц
boom = np.sin(faze) * np.exp(-tt * 4.5) * 0.9
brown = np.cumsum(rng.standard_normal(len(tt)))
brown /= np.max(np.abs(brown))
boom += lowpass(brown, 0.12) * np.exp(-tt * 5.0) * 1.2
boom += lowpass(rng.standard_normal(len(tt)), 0.5) * np.exp(-tt * 18) * 0.5
save("explosion", boom * 0.85)

# --- попадание: короткий панч ---
tt = t(0.12)
hit = lowpass(rng.standard_normal(len(tt)), 0.55) * np.exp(-tt * 70) * 0.9
hit += np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 55) * 0.6
save("hit", hit * 0.85)

# --- вскрытие ящика: двойной механический щелчок ---
tt = t(0.25)
op = np.zeros(len(tt))
for at, pitch in [(0.0, 1800), (0.10, 1200)]:
    seg = int(SR * 0.05)
    start = int(SR * at)
    click = rng.standard_normal(seg) * np.exp(-np.linspace(0, 0.05, seg) * 120)
    click = np.convolve(click, np.sin(2 * np.pi * pitch * np.linspace(0, 0.05, seg))[:8], mode="same")
    op[start:start + seg] += click
save("open", op * 0.8)

# --- шаг: мягкий глухой удар ---
tt = t(0.09)
st = lowpass(rng.standard_normal(len(tt)), 0.18) * np.exp(-tt * 75)
st += np.sin(2 * np.pi * 75 * tt) * np.exp(-tt * 60) * 0.4
save("step", st * 0.5)

# --- смерть: нисходящий тон + выдох ---
tt = t(0.7)
faze = 2 * np.pi * (300 * tt - 160 * tt ** 2)
de = np.sin(faze) * np.exp(-tt * 4.0) * 0.5
de += lowpass(rng.standard_normal(len(tt)), 0.25) * np.exp(-tt * 7.0) * 0.6
save("death", de * 0.8)

# --- перезарядка: шорох магазина + тройной щелчок затвора ---
tt = t(0.4)
rel = lowpass(rng.standard_normal(len(tt)), 0.4) * np.exp(-tt * 25) * 0.25
for at, pitch in [(0.08, 900), (0.22, 1400), (0.30, 700)]:
    seg = int(SR * 0.04)
    start = int(SR * at)
    click = rng.standard_normal(seg) * np.exp(-np.linspace(0, 0.04, seg) * 140)
    click = np.convolve(click, np.sin(2 * np.pi * pitch * np.linspace(0, 0.04, seg))[:10], mode="same")
    rel[start:start + seg] += click * 1.4
save("reload", rel * 0.8)

# --- смена оружия: короткий металлический лязг ---
tt = t(0.16)
sw = lowpass(rng.standard_normal(len(tt)), 0.5) * np.exp(-tt * 90) * 0.5
seg = int(SR * 0.05)
start = int(SR * 0.05)
click = rng.standard_normal(seg) * np.exp(-np.linspace(0, 0.05, seg) * 130)
click = np.convolve(click, np.sin(2 * np.pi * 1600 * np.linspace(0, 0.05, seg))[:8], mode="same")
sw[start:start + seg] += click * 1.5
save("swap", sw * 0.8)

# --- новый уровень: короткое торжественное арпеджио ---
tt = t(0.55)
lu = np.zeros(len(tt))
for i, fr in enumerate([523.0, 659.0, 784.0, 1047.0]):
    at = i * 0.09
    seg = int(SR * 0.22)
    start = int(SR * at)
    if start + seg > len(lu):
        seg = len(lu) - start
    tone = np.sin(2 * np.pi * fr * np.linspace(0, seg / SR, seg))
    tone *= np.exp(-np.linspace(0, seg / SR, seg) * 8)
    lu[start:start + seg] += tone * 0.4
save("levelup", lu * 0.85)

# --- UI-клик: сухой короткий щелчок ---
tt = t(0.05)
ck = lowpass(rng.standard_normal(len(tt)), 0.7) * np.exp(-tt * 160)
ck += np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 200) * 0.3
save("click", ck * 0.7)

# --- сирена сужения зоны: два тона тревоги ---
tt = t(0.7)
zn = np.zeros(len(tt))
for at, fr in [(0.0, 660.0), (0.35, 520.0)]:
    seg = int(SR * 0.3)
    start = int(SR * at)
    tone = np.sign(np.sin(2 * np.pi * fr * np.linspace(0, 0.3, seg)))
    tone = lowpass(tone, 0.3) * np.exp(-np.linspace(0, 0.3, seg) * 4)
    zn[start:start + seg] += tone * 0.4
save("zone", zn * 0.75)

# --- эмбиент: ветер пустоши (зацикленный, 8 с) ---
tt = t(8.0)
wind = np.cumsum(rng.standard_normal(len(tt)))
wind /= np.max(np.abs(wind))
wind = lowpass(wind, 0.02) * 0.7
# медленная модуляция «порывов»
gust = 0.6 + 0.4 * np.sin(2 * np.pi * 0.35 * tt) * np.sin(2 * np.pi * 0.11 * tt)
wind *= gust
wind += lowpass(rng.standard_normal(len(tt)), 0.05) * 0.12 * gust
# бесшовная петля: кроссфейд конца в начало
fade = int(SR * 0.5)
wind[:fade] = wind[:fade] * np.linspace(0, 1, fade) + wind[-fade:] * np.linspace(1, 0, fade)
wind = wind[:-fade]  # хвост свёрнут в начало
save("wind", wind * 0.5)

print("SFX_V2_OK")
