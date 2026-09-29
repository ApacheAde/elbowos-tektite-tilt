#!/usr/bin/env python3
"""Tektite Tilt — neon marble-labyrinth arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "TEKTITE TILT"
HANDLE = "x.com/ElbowOS"
VOID = (8, 6, 14)
WELL = (18, 12, 28)
AMBER = (255, 168, 48)
MINT = (72, 255, 186)
MAG = (255, 72, 148)
ICE = (240, 236, 255)
GOLD = (255, 214, 96)
OXIDE = (48, 220, 120)
SLAG = (255, 86, 70)
CYAN = (80, 220, 255)
BX, BY, BW, BH = 90, 280, 900, 1480


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=6):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 64)
        self.font_md = pygame.font.Font(None, 44)
        self.font_sm = pygame.font.Font(None, 30)
        self.reset()

    def reset(self) -> None:
        self.score = 0
        self.combo = 0
        self.pulse = 0.0
        self.over = False
        self.cool = 0.0
        self.tx = self.ty = 0.0
        self.aimx = self.aimy = 0.0
        self.bx = W / 2
        self.by = H / 2 + 80
        self.vx = self.vy = 0.0
        self.sparks: list[Spark] = []
        self.stars = [(random.randrange(W), random.randrange(H), random.uniform(0.3, 2.2)) for _ in range(90)]
        self.gems = []
        self.pits = []
        self.bumps = []
        rng = random.Random(7)
        for i in range(5):
            self.pits.append((rng.randint(BX + 120, BX + BW - 120), rng.randint(BY + 180, BY + BH - 180), rng.randint(38, 52)))
        for i in range(4):
            self.bumps.append([rng.randint(BX + 140, BX + BW - 140), rng.randint(BY + 200, BY + BH - 200), rng.randint(34, 48), 0.0])
        self._spawn_gems(8)

    def _spawn_gems(self, n: int) -> None:
        cols = (AMBER, MINT, MAG, GOLD, CYAN)
        for _ in range(n):
            for _try in range(40):
                x = random.randint(BX + 80, BX + BW - 80)
                y = random.randint(BY + 80, BY + BH - 80)
                if all(math.hypot(x - px, y - py) > pr + 50 for px, py, pr in self.pits):
                    self.gems.append([x, y, random.choice(cols), random.uniform(0, 6.28)])
                    break

    def burst(self, x, y, col, n=14) -> None:
        for _ in range(n):
            a = random.random() * 6.2832
            s = random.uniform(90, 420)
            self.sparks.append(Spark(x, y, s * math.cos(a), s * math.sin(a),
                                     random.uniform(0.22, 0.55), col, random.randint(3, 9)))

    def autoplay(self) -> None:
        if self.over:
            if self.cool <= 0:
                self.reset()
            return
        if not self.gems:
            self._spawn_gems(6)
            return
        gx, gy, _, _ = min(self.gems, key=lambda g: math.hypot(g[0] - self.bx, g[1] - self.by))
        dx, dy = gx - self.bx, gy - self.by
        for px, py, pr in self.pits:
            d = math.hypot(self.bx - px, self.by - py)
            if d < pr + 90:
                dx += (self.bx - px) * 2.4
                dy += (self.by - py) * 2.4
        mag = math.hypot(dx, dy) or 1
        self.aimx = max(-1, min(1, dx / mag))
        self.aimy = max(-1, min(1, dy / mag))

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.cool = max(0.0, self.cool - dt)
        if self.record:
            self.autoplay()
            self.tx += (self.aimx - self.tx) * min(1.0, dt * 6)
            self.ty += (self.aimy - self.ty) * min(1.0, dt * 6)
        else:
            keys = pygame.key.get_pressed()
            self.aimx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            self.aimy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            self.tx += (self.aimx - self.tx) * min(1.0, dt * 8)
            self.ty += (self.aimy - self.ty) * min(1.0, dt * 8)
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            alive.append(sp)
        self.sparks = alive
        if self.over:
            return
        g = 980
        self.vx += self.tx * g * dt
        self.vy += self.ty * g * dt
        self.vx *= 0.985
        self.vy *= 0.985
        self.bx += self.vx * dt
        self.by += self.vy * dt
        r = 28
        if self.bx < BX + r:
            self.bx, self.vx = BX + r, abs(self.vx) * 0.72
            self.burst(self.bx, self.by, CYAN, 5)
        if self.bx > BX + BW - r:
            self.bx, self.vx = BX + BW - r, -abs(self.vx) * 0.72
            self.burst(self.bx, self.by, CYAN, 5)
        if self.by < BY + r:
            self.by, self.vy = BY + r, abs(self.vy) * 0.72
            self.burst(self.bx, self.by, CYAN, 5)
        if self.by > BY + BH - r:
            self.by, self.vy = BY + BH - r, -abs(self.vy) * 0.72
            self.burst(self.bx, self.by, CYAN, 5)
        for b in self.bumps:
            b[3] = max(0.0, b[3] - dt)
            d = math.hypot(self.bx - b[0], self.by - b[1])
            if d < r + b[2] and d > 1:
                nx, ny = (self.bx - b[0]) / d, (self.by - b[1]) / d
                self.bx = b[0] + nx * (r + b[2] + 1)
                self.by = b[1] + ny * (r + b[2] + 1)
                dot = self.vx * nx + self.vy * ny
                self.vx = (self.vx - 2.2 * dot * nx) * 0.92
                self.vy = (self.vy - 2.2 * dot * ny) * 0.92
                b[3] = 0.25
                self.score += 4
                self.burst(b[0], b[1], GOLD, 8)
        kept = []
        for g in self.gems:
            g[3] += dt * 3
            if math.hypot(self.bx - g[0], self.by - g[1]) < r + 22:
                self.combo += 1
                self.score += 25 + self.combo * 4
                self.burst(g[0], g[1], g[2], 16)
            else:
                kept.append(g)
        self.gems = kept
        if len(self.gems) < 4:
            self._spawn_gems(3)
        for px, py, pr in self.pits:
            if math.hypot(self.bx - px, self.by - py) < pr - 6:
                self.over = True
                self.cool = 1.5
                self.burst(self.bx, self.by, SLAG, 28)
                self.combo = 0
                break

    def handle(self, ev) -> None:
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
            self.reset()

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        for sx, sy, sc in self.stars:
            tw = 8 + int(10 * math.sin(self.pulse * 2.2 + sx * 0.01))
            pygame.draw.circle(s, (22 + tw, 16 + tw, 36 + tw),
                               (sx, int((sy + self.pulse * 16 * sc) % H)), 1 if sc < 1 else 2)
        ox, oy = int(self.tx * 18), int(self.ty * 18)
        well = pygame.Rect(BX + ox, BY + oy, BW, BH)
        pygame.draw.rect(s, (10, 8, 16), well.move(10, 14), border_radius=48)
        pygame.draw.rect(s, WELL, well, border_radius=48)
        pygame.draw.rect(s, AMBER, well, 4, border_radius=48)
        for i in range(1, 6):
            x = well.x + i * well.w // 6
            pygame.draw.line(s, (32, 24, 44), (x, well.y + 20), (x, well.bottom - 20), 1)
        for i in range(1, 8):
            y = well.y + i * well.h // 8
            pygame.draw.line(s, (32, 24, 44), (well.x + 20, y), (well.right - 20, y), 1)
        for px, py, pr in self.pits:
            pygame.draw.circle(s, (4, 2, 8), (px + ox, py + oy), pr)
            pygame.draw.circle(s, SLAG, (px + ox, py + oy), pr, 3)
            pygame.draw.circle(s, (40, 12, 18), (px + ox, py + oy), max(8, pr - 16))
        for b in self.bumps:
            glow = 1 if b[3] > 0 else 0
            col = GOLD if glow else OXIDE
            pygame.draw.circle(s, col, (b[0] + ox, b[1] + oy), b[2] + (6 if glow else 0))
            pygame.draw.circle(s, ICE, (b[0] + ox, b[1] + oy), b[2], 2)
            pygame.draw.circle(s, (255, 255, 220), (b[0] + ox - 8, b[1] + oy - 8), 7)
        for g in self.gems:
            rr = 16 + int(4 * math.sin(g[3] * 2))
            pygame.draw.circle(s, g[2], (int(g[0]) + ox, int(g[1]) + oy), rr + 6)
            pygame.draw.circle(s, ICE, (int(g[0]) + ox, int(g[1]) + oy), rr)
            pygame.draw.circle(s, g[2], (int(g[0]) + ox, int(g[1]) + oy), rr - 6)
        mx, my = int(self.bx) + ox, int(self.by) + oy
        pygame.draw.circle(s, AMBER, (mx, my), 36)
        pygame.draw.circle(s, (48, 28, 12), (mx, my), 28)
        pygame.draw.circle(s, GOLD, (mx, my), 22)
        pygame.draw.circle(s, ICE, (mx - 7, my - 8), 7)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x), int(sp.y)), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, ICE)
        s.blit(title, title.get_rect(center=(W // 2, 70)))
        handle = self.font_sm.render(HANDLE, True, CYAN)
        s.blit(handle, handle.get_rect(center=(W // 2, 118)))
        meta = self.font_md.render(f"SCORE  {self.score}    COMBO  {self.combo}", True, AMBER)
        s.blit(meta, meta.get_rect(center=(W // 2, 176)))
        tilt = self.font_sm.render(f"TILT  {self.tx:+.2f}  {self.ty:+.2f}", True, MINT)
        s.blit(tilt, tilt.get_rect(center=(W // 2, 222)))
        hint = self.font_sm.render("WASD / arrows tilt the crater   R reset", True, ICE)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 44)))
        if self.over:
            over = self.font_md.render("SWALLOWED BY THE PIT", True, SLAG)
            s.blit(over, over.get_rect(center=(W // 2, 248)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/TEKTITE_TILT_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
