# Синтез SFX-пакета v6.106 для Drop Zone (22 кГц, 16-бит, моно)
# Выстрелы по классам оружия + swing + kill + cash + chest + новые hit/levelup
import numpy as np
import wave, os

SR = 22050
OUT = r"C:\Users\Антон\Documents\kimi\tasks\2026-10-01\21-36-36-d3d01b14\repo\game\assets\sfx"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, data):
    d = np.clip(data, -1.0, 1.0)
    pcm = (d * 32767).astype(np.int16)
    with wave.open(os.path.join(OUT, name + ".wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    print(name, round(len(d) / SR, 2), "s")


def lowpass(x, alpha):
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = acc + alpha * (x[i] - acc)
        y[i] = acc
    return y


def highpass(x, alpha):
    return x - lowpass(x, alpha)


def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def crack(dur, lp_a, dec, body_f, body_a, sub_f=0, sub_a=0.0):
    """щелчок выстрела: шумовой хлопок + тело + саб"""
    tt = t(dur)
    x = lowpass(rng.standard_normal(len(tt)), lp_a) * np.exp(-tt * dec) * 0.9
    x += np.sign(np.sin(2 * np.pi * body_f * tt)) * np.exp(-tt * dec * 2.2) * body_a
    if sub_f > 0:
        x += np.sin(2 * np.pi * sub_f * tt) * np.exp(-tt * dec * 1.6) * sub_a
    # атака — мгновенная; слегка подчистим клип
    return x


# --- пистолет: сухой резкий щелчок ---
save("shot_pistol", crack(0.16, 0.42, 38, 230, 0.45, 95, 0.3) * 0.9)

# --- револьвер: тяжёлый, с низким телом ---
save("shot_revolver", crack(0.30, 0.28, 24, 140, 0.55, 62, 0.5) * 0.95)

# --- пистолет-пулемёт: двойная очередь ---
tt = t(0.24)
smg = crack(0.24, 0.45, 40, 260, 0.4, 100, 0.25)
smg2 = np.zeros(len(tt))
s0 = crack(0.10, 0.45, 45, 260, 0.4, 100, 0.2)
smg2[:len(s0)] += s0
off = int(SR * 0.055)
smg2[off:off + len(s0)] += s0 * 0.9
save("shot_smg", smg2 * 0.85)

# --- автомат: двойной тяжёлый удар ---
tt = t(0.28)
s0 = crack(0.11, 0.32, 34, 170, 0.5, 75, 0.35)
rif = np.zeros(len(tt))
rif[:len(s0)] += s0
off = int(SR * 0.062)
rif[off:off + len(s0)] += s0 * 0.92
save("shot_rifle", rif * 0.9)

# --- дробовик: широкий глухой залп ---
tt = t(0.50)
brown = np.cumsum(rng.standard_normal(len(tt)))
brown /= np.max(np.abs(brown))
sg = lowpass(brown, 0.16) * np.exp(-tt * 13) * 1.1
sg += lowpass(rng.standard_normal(len(tt)), 0.5) * np.exp(-tt * 26) * 0.7
sg += np.sin(2 * np.pi * 78 * tt) * np.exp(-tt * 20) * 0.6
sg[:int(SR * 0.01)] *= 3.0  # атака
save("shot_shotgun", sg * 0.8)

# --- снайперка: громкий хлопок с длинным хвостом ---
tt = t(0.65)
sn = lowpass(rng.standard_normal(len(tt)), 0.30) * np.exp(-tt * 11) * 0.85
sn += np.sign(np.sin(2 * np.pi * 150 * tt)) * np.exp(-tt * 25) * 0.5
sn += np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 9) * 0.55
seg = int(SR * 0.02)
sn[:seg] *= np.linspace(1.0, 4.0, seg)
save("shot_sniper", sn * 0.85)

# --- гранатомёт/РПГ: взлёт снаряда — свист + толчок ---
tt = t(0.45)
faze = 2 * np.pi * (140 * tt + 260 * tt ** 2)  # свист вверх
wh = np.sin(faze) * np.exp(-tt * 9) * 0.35
wh += highpass(lowpass(rng.standard_normal(len(tt)), 0.5), 0.15) * np.exp(-tt * 8) * 0.5
wh += np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 18) * 0.5
save("shot_launcher", wh * 0.8)

# --- замах ближнего боя: короткий свист ---
tt = t(0.18)
sw = highpass(lowpass(rng.standard_normal(len(tt)), 0.6), 0.1) * np.sin(np.pi * tt / 0.18) ** 2 * 0.7
save("swing", sw * 0.8)

# --- убийство: металлический «динь» + низкий акцент ---
tt = t(0.40)
kl = np.sin(2 * np.pi * 1660 * tt) * np.exp(-tt * 11) * 0.5
kl += np.sin(2 * np.pi * 2490 * tt) * np.exp(-tt * 14) * 0.2
kl += np.sin(2 * np.pi * 110 * tt) * np.exp(-tt * 32) * 0.55
kl += lowpass(rng.standard_normal(len(tt)), 0.5) * np.exp(-tt * 60) * 0.25
save("kill", kl * 0.9)

# --- монеты: два ярких перезвона ---
tt = t(0.38)
ca = np.zeros(len(tt))
for at, fr, a in [(0.0, 2093.0, 0.5), (0.09, 2637.0, 0.45), (0.16, 3136.0, 0.25)]:
    seg = int(SR * 0.16)
    st = int(SR * at)
    tt2 = np.linspace(0, seg / SR, seg)
    ca[st:st + seg] += (np.sin(2 * np.pi * fr * tt2) + 0.4 * np.sin(2 * np.pi * fr * 2.01 * tt2)) * np.exp(-tt2 * 22) * a
save("cash", ca * 0.8)

# --- сундук: толчок крышки + колокольное арпеджио вверх ---
tt = t(1.0)
ch = np.sin(2 * np.pi * 65 * tt) * np.exp(-tt * 12) * 0.5
ch += lowpass(rng.standard_normal(len(tt)), 0.3) * np.exp(-tt * 20) * 0.3
for i, fr in enumerate([523.0, 659.0, 784.0, 1047.0, 1319.0]):
    at = 0.12 + i * 0.09
    seg = int(SR * 0.35)
    st = int(SR * at)
    tt2 = np.linspace(0, seg / SR, seg)
    bell = (np.sin(2 * np.pi * fr * tt2) + 0.35 * np.sin(2 * np.pi * fr * 2.76 * tt2)) * np.exp(-tt2 * 7)
    if st + seg <= len(ch):
        ch[st:st + seg] += bell * 0.35
    else:
        rem = len(ch) - st
        ch[st:] += bell[:rem] * 0.35
save("chest", ch * 0.8)

# --- попадание (переделка): плотный панч со щелчком ---
tt = t(0.11)
hi = lowpass(rng.standard_normal(len(tt)), 0.6) * np.exp(-tt * 85) * 0.75
hi += np.sin(2 * np.pi * 150 * tt) * np.exp(-tt * 65) * 0.65
hi += np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 160) * 0.15
save("hit", hi * 0.85)

# --- новый уровень (переделка): аккорд + блестящее арпеджио ---
tt = t(0.85)
lu = np.zeros(len(tt))
for fr, a in [(523.0, 0.30), (659.0, 0.28), (784.0, 0.28), (1047.0, 0.22)]:
    lu += np.sin(2 * np.pi * fr * tt) * np.exp(-tt * 4.5) * a
    lu += np.sin(2 * np.pi * fr * 2.0 * tt) * np.exp(-tt * 6.0) * a * 0.25
for i, fr in enumerate([1047.0, 1319.0, 1568.0]):
    at = 0.10 + i * 0.10
    seg = int(SR * 0.3)
    st = int(SR * at)
    tt2 = np.linspace(0, seg / SR, seg)
    if st + seg <= len(lu):
        lu[st:st + seg] += np.sin(2 * np.pi * fr * tt2) * np.exp(-tt2 * 9) * 0.22
save("levelup", lu * 0.8)
