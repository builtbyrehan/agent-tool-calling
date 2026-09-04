"""
snake_game.py
An enhanced Snake game built with pygame / pygame-ce.

Features:
  - Sound effects (procedurally generated, no asset files needed)
  - Increasing difficulty (speed ramps up with score)
  - Optional wrap-around walls (toggle in menu)
  - Multiple obstacle levels (Border Frame, Crossroads, Maze, Quadrants, Spiral)
  - Multiple color schemes (Classic / Neon / Retro / Dark)
  - Two-player mode (toggle in menu)
  - Particle effects (food eat, bonus, crash, trail)
  - Power-ups: Cherry (slow), Ice (freeze obstacles), Star (2x points),
    Heart (extra life)

Run with: python snake_game.py
"""

import sys
import math
import random
import array

import pygame


# ---------- Configuration ----------
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT

FPS_BASE = 10
FPS_MAX = 25            # Speed cap when difficulty is maxed
DIFFICULTY_RAMP = 0.25  # FPS gained per point (capped at FPS_MAX)

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"
STATE_GAME_OVER = "game_over"
STATE_OPTIONS = "options"

# Files
HIGHSCORE_FILE = "highscore.txt"
SETTINGS_FILE = "settings.txt"

# Power-up definitions
POWERUP_CHERRY = "cherry"   # Slow time
POWERUP_ICE = "ice"         # Freeze obstacles
POWERUP_STAR = "star"       # Double points
POWERUP_HEART = "heart"     # Extra life

POWERUP_DURATION = {
    POWERUP_CHERRY: 6.0,
    POWERUP_ICE:    5.0,
    POWERUP_STAR:   8.0,
    POWERUP_HEART:  0.0,  # instant effect
}
POWERUP_MIN_SCORE = {
    POWERUP_CHERRY: 8,
    POWERUP_ICE:   12,
    POWERUP_STAR:   5,
    POWERUP_HEART: 15,
}
POWERUP_LIFETIME_GROUND = 8.0  # seconds before despawning on the field


# ---------- Color Schemes ----------
COLOR_SCHEMES = {
    "classic": {
        "bg":         (18, 18, 24),
        "grid":       (28, 28, 36),
        "snake_head": (80, 220, 100),
        "snake_body": (40, 170, 70),
        "snake2_head": (100, 180, 255),
        "snake2_body": (50, 110, 200),
        "food":       (220, 60, 60),
        "bonus":      (255, 200, 60),
        "obstacle":   (130, 90, 50),
        "text":       (235, 235, 235),
        "text_dim":   (150, 150, 150),
        "accent":     (255, 200, 60),
    },
    "neon": {
        "bg":         (5, 5, 15),
        "grid":       (15, 15, 30),
        "snake_head": (0, 255, 200),
        "snake_body": (0, 200, 160),
        "snake2_head": (255, 0, 220),
        "snake2_body": (200, 0, 170),
        "food":       (255, 40, 80),
        "bonus":      (255, 230, 0),
        "obstacle":   (180, 0, 255),
        "text":       (220, 255, 255),
        "text_dim":   (100, 180, 200),
        "accent":     (255, 230, 0),
    },
    "retro": {
        "bg":         (0, 0, 0),
        "grid":       (20, 20, 20),
        "snake_head": (0, 255, 0),
        "snake_body": (0, 180, 0),
        "snake2_head": (255, 255, 0),
        "snake2_body": (200, 200, 0),
        "food":       (255, 0, 0),
        "bonus":      (255, 255, 255),
        "obstacle":   (120, 120, 120),
        "text":       (0, 255, 0),
        "text_dim":   (0, 160, 0),
        "accent":     (255, 255, 255),
    },
    "dark": {
        "bg":         (10, 10, 12),
        "grid":       (18, 18, 22),
        "snake_head": (200, 200, 210),
        "snake_body": (130, 130, 145),
        "snake2_head": (240, 200, 160),
        "snake2_body": (170, 140, 110),
        "food":       (200, 80, 80),
        "bonus":      (230, 180, 90),
        "obstacle":   (90, 70, 50),
        "text":       (220, 220, 225),
        "text_dim":   (140, 140, 150),
        "accent":     (230, 180, 90),
    },
}
SCHEME_NAMES = list(COLOR_SCHEMES.keys())

# Per-scheme power-up colors (to remain readable on each background)
POWERUP_COLORS = {
    POWERUP_CHERRY: (240, 50, 80),
    POWERUP_ICE:    (140, 220, 255),
    POWERUP_STAR:   (255, 230, 60),
    POWERUP_HEART:  (255, 90, 130),
}


# ---------- Level Definitions ----------
def level_open_field():
    return set()


def level_border_frame():
    """Thick border around the playfield, inner 4-cell area is free."""
    obstacles = set()
    thickness = 2
    for x in range(GRID_WIDTH):
        for t in range(thickness):
            obstacles.add((x, t))
            obstacles.add((x, GRID_HEIGHT - 1 - t))
    for y in range(GRID_HEIGHT):
        for t in range(thickness):
            obstacles.add((t, y))
            obstacles.add((GRID_WIDTH - 1 - t, y))
    return obstacles


def level_crossroads():
    """Horizontal and vertical walls with gaps at intersections."""
    obstacles = set()
    mid_y = GRID_HEIGHT // 2
    mid_x = GRID_WIDTH // 2
    gap = 2  # gap size at intersection
    # Horizontal wall across the middle, with a gap in the center
    for x in range(GRID_WIDTH):
        if not (mid_x - gap <= x <= mid_x + gap):
            obstacles.add((x, mid_y))
    # Vertical wall down the middle, with a gap in the center
    for y in range(GRID_HEIGHT):
        if not (mid_y - gap <= y <= mid_y + gap):
            obstacles.add((mid_x, y))
    return obstacles


def level_maze_lite():
    """Symmetric maze with corridors ~3 cells wide."""
    obstacles = set()
    # Vertical wall columns at x=7 and x=22, with horizontal gaps
    for y in range(GRID_HEIGHT):
        # Left vertical wall with gaps at rows 3, 9, 15
        if y not in (3, 9, 15):
            obstacles.add((7, y))
        # Right vertical wall with gaps at rows 5, 11, 17
        if y not in (5, 11, 17):
            obstacles.add((22, y))
    # Horizontal wall rows at y=4 and y=15, with vertical gaps
    for x in range(GRID_WIDTH):
        # Top horizontal with gaps at cols 12, 18
        if x not in (12, 18) and not (x == 7 or x == 22):
            obstacles.add((x, 4))
        # Bottom horizontal with gaps at cols 10, 16
        if x not in (10, 16) and not (x == 7 or x == 22):
            obstacles.add((x, 15))
    return obstacles


def level_quadrants():
    """Four obstacle islands in the corners with a gap to the center."""
    obstacles = set()
    islands = [
        (3, 3),                    # top-left
        (GRID_WIDTH - 4, 3),       # top-right
        (3, GRID_HEIGHT - 4),      # bottom-left
        (GRID_WIDTH - 4, GRID_HEIGHT - 4),  # bottom-right
    ]
    for cx, cy in islands:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                obstacles.add((cx + dx, cy + dy))
    return obstacles


def level_spiral():
    """A spiral wall from the outside inward, with gaps to enter/exit."""
    obstacles = set()
    # Build concentric rectangular rings with gaps
    rings = [
        # (top, bottom, left, right, gap_row, gap_col)
        (1, GRID_HEIGHT - 2, 1, GRID_WIDTH - 2, 1,  1),
        (4, GRID_HEIGHT - 5, 4, GRID_WIDTH - 5, GRID_HEIGHT - 5, GRID_WIDTH - 5),
        (7, GRID_HEIGHT - 8, 7, GRID_WIDTH - 8, 7, 7),
    ]
    for top, bottom, left, right, gap_row, gap_col in rings:
        for x in range(left, right + 1):
            if x != gap_col:
                obstacles.add((x, top))
                obstacles.add((x, bottom))
        for y in range(top, bottom + 1):
            if y != gap_row:
                obstacles.add((left, y))
                obstacles.add((right, y))
    return obstacles


LEVELS = {
    "open_field":   ("Open Field",   level_open_field),
    "border_frame": ("Border Frame", level_border_frame),
    "crossroads":   ("Crossroads",   level_crossroads),
    "maze_lite":    ("Maze Lite",    level_maze_lite),
    "quadrants":    ("Quadrants",    level_quadrants),
    "spiral":       ("Spiral",       level_spiral),
}
LEVEL_NAMES = list(LEVELS.keys())


def build_level_obstacles(level_key):
    """Return the obstacle set for the given level key, with a safe spawn area."""
    if level_key not in LEVELS:
        level_key = "open_field"
    obstacles = LEVELS[level_key][1]()
    # Carve out a wide safe zone covering both P1 (x=5..9) and P2 (x=20..24)
    # start areas plus the full center vertical strip.
    safe_zone = set()
    for x in range(4, 10):
        for y in range(7, 14):
            safe_zone.add((x, y))
    for x in range(20, 26):
        for y in range(7, 14):
            safe_zone.add((x, y))
    for y in range(7, 14):
        for x in range(10, 20):
            safe_zone.add((x, y))
    return obstacles - safe_zone


# ---------- Settings persistence ----------
DEFAULT_SETTINGS = {
    "wrap": "off",
    "obstacles": "off",
    "two_player": "off",
    "scheme": "classic",
    "sound": "on",
    "level": "open_field",
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    data[k.strip()] = v.strip()
            merged = dict(DEFAULT_SETTINGS)
            merged.update({k: v for k, v in data.items() if k in DEFAULT_SETTINGS})
            return merged
    except (FileNotFoundError, ValueError):
        return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f:
            for k, v in settings.items():
                f.write(f"{k}={v}\n")
    except OSError:
        pass


def load_highscore():
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip() or 0)
    except (FileNotFoundError, ValueError):
        return 0


def save_highscore(score):
    try:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
    except OSError:
        pass


# ---------- Sound (procedurally generated) ----------
class SoundManager:
    """Generate short SFX so we don't need asset files."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
            self._build_sounds()
        except pygame.error:
            self.enabled = False

    def _build_sounds(self):
        self.sounds["eat"] = self._make_tone(freqs=[660, 880],
                                              duration=0.08, wave="square")
        self.sounds["bonus"] = self._make_tone(freqs=[523, 659, 784, 1047],
                                               duration=0.18, wave="square")
        self.sounds["game_over"] = self._make_tone(
            freqs=[440, 330, 220, 110], duration=0.18, wave="square")
        self.sounds["menu"] = self._make_tone(freqs=[520, 700],
                                              duration=0.06, wave="sine")
        self.sounds["powerup"] = self._make_tone(
            freqs=[523, 659, 784, 1046, 1318], duration=0.22, wave="square")
        self.sounds["powerdown"] = self._make_tone(
            freqs=[660, 330], duration=0.10, wave="square")
        self.sounds["life"] = self._make_tone(
            freqs=[392, 523, 659, 784], duration=0.25, wave="sine")

    def _make_tone(self, freqs, duration, wave="square", volume=0.35):
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        total = []
        steps = max(1, len(freqs) - 1)
        chunk = n_samples // steps
        for i, freq in enumerate(freqs):
            n = chunk if i < steps - 1 else n_samples - len(total)
            for j in range(n):
                t = j / sample_rate
                phase = (i * chunk + j) / sample_rate
                if wave == "square":
                    val = 1.0 if math.sin(2 * math.pi * freq * phase) >= 0 else -1.0
                else:
                    val = math.sin(2 * math.pi * freq * t)
                env = 1.0 - (j / max(1, n - 1)) * 0.4
                total.append(int(val * volume * env * 32767))
        samples = array.array("h", total)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.play()


# ---------- Particle System ----------
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "lifetime", "age", "size")

    def __init__(self, x, y, vx, vy, color, lifetime, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.size = size

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Slight drag
        self.vx *= 0.92
        self.vy *= 0.92

    def is_alive(self):
        return self.age < self.lifetime

    @property
    def progress(self):
        """0.0 at spawn, 1.0 at end of life."""
        if self.lifetime <= 0:
            return 1.0
        return min(1.0, self.age / self.lifetime)

    def draw(self, surface):
        # Fade alpha and shrink slightly
        alpha = max(0, int(255 * (1.0 - self.progress)))
        radius = max(1, int(self.size * (1.0 - 0.4 * self.progress)))
        # Use a temporary surface for alpha blending
        surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*self.color, alpha),
                           (radius + 1, radius + 1), radius)
        surface.blit(surf, (int(self.x - radius - 1), int(self.y - radius - 1)))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, pos, color, count, speed_range, lifetime_range, size_range):
        px, py = grid_to_pixel(pos)
        cx, cy = px + CELL_SIZE // 2, py + CELL_SIZE // 2
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            lifetime = random.uniform(*lifetime_range)
            size = random.uniform(*size_range)
            self.particles.append(
                Particle(cx, cy, vx, vy, color, lifetime, size))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

    def clear(self):
        self.particles.clear()


# ---------- Helpers ----------
def random_grid_position(occupied):
    occupied = set(occupied)
    free = [(x, y) for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
            if (x, y) not in occupied]
    if not free:
        return None
    return random.choice(free)


def grid_to_pixel(pos):
    return pos[0] * CELL_SIZE, pos[1] * CELL_SIZE


def draw_text(surface, text, font, color, center):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect(center=center)
    surface.blit(rendered, rect)


def draw_text_left(surface, text, font, color, pos):
    surface.blit(font.render(text, True, color), pos)


# ---------- Power-Up Field Item ----------
class PowerUpItem:
    def __init__(self, kind, pos):
        self.kind = kind
        self.pos = pos
        self.spawn_time = pygame.time.get_ticks()

    def update(self, dt):
        pass  # expiry handled by age check

    def is_expired(self):
        elapsed = (pygame.time.get_ticks() - self.spawn_time) / 1000
        return elapsed > POWERUP_LIFETIME_GROUND

    def draw(self, surface, scheme):
        px, py = grid_to_pixel(self.pos)
        cx, cy = px + CELL_SIZE // 2, py + CELL_SIZE // 2
        color = POWERUP_COLORS[self.kind]
        # Gentle pulse
        t = pygame.time.get_ticks() / 200.0
        pulse = 1.0 + 0.18 * math.sin(t)
        # White outer glow
        glow_r = int((CELL_SIZE // 2 + 2) * pulse)
        glow_surf = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2),
                                   pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*color, 80),
                           (glow_r + 1, glow_r + 1), glow_r)
        surface.blit(glow_surf, (cx - glow_r - 1, cy - glow_r - 1))
        # Body shape varies by kind
        if self.kind == POWERUP_CHERRY:
            pygame.draw.circle(surface, color, (cx - 3, cy + 2), 5)
            pygame.draw.circle(surface, color, (cx + 3, cy + 2), 5)
            pygame.draw.circle(surface, (40, 30, 20), (cx, cy - 4), 2)  # stem
        elif self.kind == POWERUP_ICE:
            pts = [(cx, cy - 7), (cx + 7, cy), (cx, cy + 7), (cx - 7, cy)]
            pygame.draw.polygon(surface, color, pts)
            pygame.draw.polygon(surface, (255, 255, 255), pts, 1)
        elif self.kind == POWERUP_STAR:
            points = []
            for i in range(10):
                ang = -math.pi / 2 + i * math.pi / 5
                r = 7 if i % 2 == 0 else 3
                points.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
            pygame.draw.polygon(surface, color, points)
            pygame.draw.polygon(surface, scheme["accent"], points, 1)
        elif self.kind == POWERUP_HEART:
            r = 5
            pygame.draw.circle(surface, color, (cx - 3, cy - 2), r)
            pygame.draw.circle(surface, color, (cx + 3, cy - 2), r)
            pts = [(cx - 7, cy), (cx + 7, cy), (cx, cy + 8)]
            pygame.draw.polygon(surface, color, pts)


# ---------- Snake (player) ----------
class Snake:
    def __init__(self, start, direction, color_head, color_body, controls):
        self.body = list(start)
        self.direction = direction
        self.next_direction = direction
        self.color_head = color_head
        self.color_body = color_body
        self.controls = controls
        self.grow = 0
        self.alive = True
        self.food_eaten = 0
        self.bonus_eaten = 0
        self.just_ate_bonus = False
        self.collision_immunity_timer = 0.0  # seconds of remaining i-frames

    def head(self):
        return self.body[0]

    def set_direction_from_key(self, key):
        new_dir = self.controls.get(key)
        if new_dir is None:
            return False
        if (new_dir[0] == -self.direction[0] and
                new_dir[1] == -self.direction[1]):
            return False
        self.next_direction = new_dir
        return True

    def step(self, wrap, obstacles, foods, obstacles_active=True):
        """
        Move one cell. Returns True if the snake died this step.
        `obstacles_active=False` simulates the Ice power-up.
        """
        self.direction = self.next_direction
        hx, hy = self.body[0]
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy

        if wrap:
            nx %= GRID_WIDTH
            ny %= GRID_HEIGHT
        else:
            if nx < 0 or nx >= GRID_WIDTH or ny < 0 or ny >= GRID_HEIGHT:
                self.alive = False
                return True

        new_head = (nx, ny)

        # Obstacle collision (skipped if ice is active)
        if obstacles_active and new_head in obstacles:
            self.alive = False
            return True

        # Self collision (ignore tail because it moves out of the way)
        if new_head in self.body[:-1]:
            self.alive = False
            return True

        ate = False
        ate_bonus = False
        for fpos, kind in foods:
            if new_head == fpos:
                ate = True
                if kind == "bonus":
                    ate_bonus = True
                    self.bonus_eaten += 1
                else:
                    self.food_eaten += 1
                break

        self.body.insert(0, new_head)

        if ate:
            self.grow += 1
            if ate_bonus:
                self.grow += 2
            self.just_ate_bonus = ate_bonus

        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()

        return False


# ---------- Game ----------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake Game - Enhanced Edition v2")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_xl = pygame.font.SysFont("arial", 56, bold=True)
        self.font_large = pygame.font.SysFont("arial", 40, bold=True)
        self.font_medium = pygame.font.SysFont("arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("arial", 20)
        self.font_tiny = pygame.font.SysFont("arial", 16)

        self.settings = load_settings()
        self.sound = SoundManager(enabled=self.settings["sound"] == "on")
        self.highscore = load_highscore()

        self.state = STATE_MENU
        self.options_index = 0
        self.reset()

    # ----- Settings helpers -----
    def scheme(self):
        return COLOR_SCHEMES[self.settings["scheme"]]

    def cycle_setting(self, key, options):
        cur = self.settings[key]
        i = options.index(cur) if cur in options else 0
        self.settings[key] = options[(i + 1) % len(options)]
        save_settings(self.settings)

    def toggle_setting(self, key):
        self.settings[key] = "off" if self.settings[key] == "on" else "on"
        save_settings(self.settings)
        if key == "sound":
            self.sound.enabled = self.settings[key] == "on"

    # ----- Power-up state helpers -----
    def reset_powerup_state(self):
        self.field_powerup = None
        self.slow_timer = 0.0
        self.ice_timer = 0.0
        self.star_timer = 0.0
        self.extra_lives = 0
        self.heart_used_this_game = False
        self.flash_timer = 0.0  # brief screen flash on events
        self.ice_warning = False

    def apply_powerup(self, kind):
        if kind == POWERUP_HEART:
            if self.heart_used_this_game:
                return  # never grant more than one heart per game
            self.extra_lives += 1
            self.heart_used_this_game = True
            self.sound.play("life")
        else:
            duration = POWERUP_DURATION[kind]
            if kind == POWERUP_CHERRY:
                self.slow_timer = max(self.slow_timer, duration)
            elif kind == POWERUP_ICE:
                self.ice_timer = max(self.ice_timer, duration)
            elif kind == POWERUP_STAR:
                self.star_timer = max(self.star_timer, duration)
            self.sound.play("powerup")
        # Burst particles at the pickup location
        if self.field_powerup:
            self.particles.emit(
                self.field_powerup.pos,
                POWERUP_COLORS[kind], count=18,
                speed_range=(60, 160), lifetime_range=(0.4, 0.7),
                size_range=(3, 5))
        self.field_powerup = None

    # ----- Game lifecycle -----
    def reset(self):
        scheme = self.scheme()
        mid_y = GRID_HEIGHT // 2

        p1_x = GRID_WIDTH // 4
        self.snake1 = Snake(
            start=[(p1_x, mid_y), (p1_x - 1, mid_y), (p1_x - 2, mid_y)],
            direction=RIGHT,
            color_head=scheme["snake_head"],
            color_body=scheme["snake_body"],
            controls={
                pygame.K_UP: UP, pygame.K_DOWN: DOWN,
                pygame.K_LEFT: LEFT, pygame.K_RIGHT: RIGHT,
                pygame.K_w: UP, pygame.K_s: DOWN,
                pygame.K_a: LEFT, pygame.K_d: RIGHT,
            },
        )

        if self.settings["two_player"] == "on":
            p2_x = GRID_WIDTH * 3 // 4
            self.snake2 = Snake(
                start=[(p2_x, mid_y), (p2_x + 1, mid_y), (p2_x + 2, mid_y)],
                direction=LEFT,
                color_head=scheme["snake2_head"],
                color_body=scheme["snake2_body"],
                controls={
                    pygame.K_i: UP, pygame.K_k: DOWN,
                    pygame.K_j: LEFT, pygame.K_l: RIGHT,
                },
            )
        else:
            self.snake2 = None

        self.food = None
        self.bonus_food = None
        self.bonus_spawn_time = 0
        if self.settings["obstacles"] == "on":
            self.obstacles = build_level_obstacles(self.settings["level"])
        else:
            self.obstacles = set()
        self.score = 0
        self.frame_count = 0
        self.start_ticks = pygame.time.get_ticks()
        self.pause_ticks = 0
        self.game_over_reason = ""
        self.last_dt = 1 / FPS_BASE
        self.particles = ParticleSystem()
        self.reset_powerup_state()
        self._spawn_initial_food()

    def _spawn_initial_food(self):
        occupied = set(self.snake1.body)
        if self.snake2:
            occupied |= set(self.snake2.body)
        occupied |= self.obstacles
        self.food = random_grid_position(occupied)

    def all_food(self):
        foods = []
        if self.food:
            foods.append((self.food, "normal"))
        if self.bonus_food:
            foods.append((self.bonus_food, "bonus"))
        return foods

    def effective_fps(self):
        """Current speed, with slow-power-up multiplier applied."""
        fps = self.current_fps()
        if self.slow_timer > 0:
            fps = max(5, fps * 0.5)
        return fps

    def current_fps(self):
        combined = self.snake1.food_eaten + self.snake1.bonus_eaten * 3
        if self.snake2:
            combined += self.snake2.food_eaten + self.snake2.bonus_eaten * 3
        return min(FPS_MAX, FPS_BASE + combined * DIFFICULTY_RAMP)

    def scoring_multiplier(self):
        return 2 if self.star_timer > 0 else 1

    # ----- Input -----
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            elif event.type == pygame.KEYDOWN:
                if self.state == STATE_MENU:
                    self._menu_input(event.key)
                elif self.state == STATE_OPTIONS:
                    self._options_input(event.key)
                elif self.state == STATE_PLAYING:
                    self._playing_input(event.key)
                elif self.state == STATE_PAUSED:
                    self._paused_input(event.key)
                elif self.state == STATE_GAME_OVER:
                    self._game_over_input(event.key)

    def _menu_input(self, key):
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            self.sound.play("menu")
            self.state = STATE_PLAYING
        elif key == pygame.K_o:
            self.state = STATE_OPTIONS
            self.options_index = 0
        elif key in (pygame.K_q, pygame.K_ESCAPE):
            self.quit_game()

    def _options_input(self, key):
        if key in (pygame.K_ESCAPE, pygame.K_o, pygame.K_RETURN):
            self.state = STATE_MENU
            self.sound.play("menu")
        elif key == pygame.K_UP:
            self.options_index = (self.options_index - 1) % len(SETTING_OPTIONS)
            self.sound.play("menu")
        elif key == pygame.K_DOWN:
            self.options_index = (self.options_index + 1) % len(SETTING_OPTIONS)
            self.sound.play("menu")
        elif key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_SPACE):
            self._apply_option_toggle(forward=(key == pygame.K_RIGHT))
            self.sound.play("menu")

    def _apply_option_toggle(self, forward=True):
        key, kind, options = SETTING_OPTIONS[self.options_index]
        if kind == "cycle":
            self.cycle_setting(key, options)
        elif kind == "toggle":
            self.settings[key] = "on" if forward else "off"
            save_settings(self.settings)
            if key == "sound":
                self.sound.enabled = self.settings[key] == "on"

    def _playing_input(self, key):
        self.snake1.set_direction_from_key(key)
        if self.snake2:
            self.snake2.set_direction_from_key(key)

        if key == pygame.K_p:
            self.state = STATE_PAUSED
            self.pause_ticks = pygame.time.get_ticks()
        elif key == pygame.K_ESCAPE:
            self.quit_game()

    def _paused_input(self, key):
        if key in (pygame.K_p, pygame.K_SPACE):
            paused_for = pygame.time.get_ticks() - self.pause_ticks
            self.start_ticks += paused_for
            self.state = STATE_PLAYING
        elif key == pygame.K_r:
            self.reset()
            self.state = STATE_PLAYING
        elif key == pygame.K_m:
            self.reset()
            self.state = STATE_MENU
        elif key == pygame.K_ESCAPE:
            self.quit_game()

    def _game_over_input(self, key):
        if key in (pygame.K_r, pygame.K_SPACE, pygame.K_RETURN):
            self.reset()
            self.state = STATE_PLAYING
        elif key == pygame.K_m:
            self.reset()
            self.state = STATE_MENU
        elif key in (pygame.K_q, pygame.K_ESCAPE):
            self.quit_game()

    # ----- Update -----
    def update(self):
        dt = self.last_dt  # use last frame's dt for stable time steps
        if self.state != STATE_PLAYING:
            return

        self.frame_count += 1
        wrap = self.settings["wrap"] == "on"
        foods = self.all_food()
        obstacles_active = (self.ice_timer <= 0)
        obstacles = self.obstacles

        # ---- Tick timers ----
        prev_slow = self.slow_timer
        prev_ice = self.ice_timer
        prev_star = self.star_timer
        self.slow_timer = max(0.0, self.slow_timer - dt)
        self.ice_timer = max(0.0, self.ice_timer - dt)
        self.star_timer = max(0.0, self.star_timer - dt)
        self.flash_timer = max(0.0, self.flash_timer - dt)
        if prev_slow > 0 and self.slow_timer == 0:
            self.sound.play("powerdown")
        if prev_ice > 0 and self.ice_timer == 0:
            self.sound.play("powerdown")
            self.flash_timer = 0.4
        if prev_star > 0 and self.star_timer == 0:
            self.sound.play("powerdown")
        for s in (self.snake1, self.snake2):
            if s:
                s.collision_immunity_timer = max(0.0,
                                                 s.collision_immunity_timer - dt)

        # ---- Move snakes ----
        died = self.snake1.step(wrap, obstacles, foods, obstacles_active)
        if self._try_kill_with_extra_life(self.snake1, died):
            pass  # survived via heart
        elif died:
            self._on_snake_death(self.snake1, "Player 1 crashed!")
            if self.state == STATE_GAME_OVER:
                return

        if self.snake2:
            died2 = self.snake2.step(wrap, obstacles, foods, obstacles_active)
            if self._try_kill_with_extra_life(self.snake2, died2):
                pass
            elif died2:
                self._on_snake_death(self.snake2, "Player 2 crashed!")
                if self.state == STATE_GAME_OVER:
                    return
            # Cross-collision
            if (self.snake1.alive and self.snake2.alive):
                if self.snake1.head() in set(self.snake2.body[:-1]):
                    self._on_snake_death(self.snake1, "Player 1 hit Player 2!")
                    if self.state == STATE_GAME_OVER:
                        return
                if self.snake2.head() in set(self.snake1.body[:-1]):
                    self._on_snake_death(self.snake2, "Player 2 hit Player 1!")
                    if self.state == STATE_GAME_OVER:
                        return

        # ---- Handle food / power-up consumption ----
        multiplier = self.scoring_multiplier()
        for snake in (self.snake1, self.snake2):
            if not snake or not snake.alive:
                continue
            head = snake.head()
            # Power-up
            if self.field_powerup and head == self.field_powerup.pos:
                self.apply_powerup(self.field_powerup.kind)
                continue
            # Food
            for fpos, kind in foods:
                if head == fpos:
                    if kind == "bonus":
                        self.sound.play("bonus")
                        self.score += 3 * multiplier
                        self.bonus_food = None
                        # Burst particles
                        self.particles.emit(
                            fpos, self.scheme()["bonus"], count=22,
                            speed_range=(60, 180), lifetime_range=(0.4, 0.8),
                            size_range=(3, 6))
                    else:
                        self.sound.play("eat")
                        self.score += 1 * multiplier
                        # Burst particles
                        self.particles.emit(
                            fpos, self.scheme()["food"], count=10,
                            speed_range=(40, 130), lifetime_range=(0.25, 0.5),
                            size_range=(2, 4))
                        # Possibly spawn a bonus
                        if (self.bonus_food is None and random.random() < 0.2
                                and self.score >= 5):
                            self._spawn_bonus()
                        self._respawn_food()
                    break

        # ---- Bonus food expiry / power-up field expiry / spawning ----
        if self.bonus_food and pygame.time.get_ticks() - self.bonus_spawn_time > 5000:
            self.bonus_food = None
        if self.field_powerup:
            if self.field_powerup.is_expired():
                self.field_powerup = None
            # Picked up via head check above
        else:
            # Maybe spawn a new power-up
            self._maybe_spawn_powerup()

        # ---- 2P win condition ----
        if self.snake2 and self.snake1.alive != self.snake2.alive:
            if not self.snake1.alive:
                self._trigger_game_over("Player 2 wins!")
                return
            else:
                self._trigger_game_over("Player 1 wins!")
                return

        # ---- Board cleared ----
        if self.food is None:
            self._trigger_game_over("You filled the board!")
            return

        # ---- Update particle system ----
        self.particles.update(dt)

    def _try_kill_with_extra_life(self, snake, would_die):
        """If snake would die and we have an extra life, consume one and survive."""
        if not would_die or self.extra_lives <= 0:
            return False
        self.extra_lives -= 1
        snake.alive = True
        snake.collision_immunity_timer = 1.5  # brief invulnerability
        self.sound.play("life")
        # Heal the snake back to a safe spot if needed
        head = snake.head()
        if head in snake.body[1:] or head in self.obstacles:
            # Move snake back one cell (best effort)
            if len(snake.body) > 1:
                snake.body.pop(0)
                snake.head()  # refresh
        self.flash_timer = 0.3
        # Burst particles at the snake head
        self.particles.emit(
            snake.head() if snake.body else head,
            self.scheme()["accent"], count=24,
            speed_range=(80, 200), lifetime_range=(0.3, 0.6),
            size_range=(3, 5))
        return True

    def _on_snake_death(self, snake, reason):
        # Spawn death particles at the snake's head
        if snake and snake.body:
            self.particles.emit(
                snake.head(), (255, 80, 60), count=30,
                speed_range=(80, 220), lifetime_range=(0.4, 0.9),
                size_range=(3, 6))
        self._trigger_game_over(reason)

    def _respawn_food(self):
        occupied = set(self.snake1.body)
        if self.snake2:
            occupied |= set(self.snake2.body)
        occupied |= self.obstacles
        if self.bonus_food:
            occupied.add(self.bonus_food)
        if self.field_powerup:
            occupied.add(self.field_powerup.pos)
        self.food = random_grid_position(occupied)

    def _spawn_bonus(self):
        occupied = set(self.snake1.body)
        if self.snake2:
            occupied |= set(self.snake2.body)
        occupied |= self.obstacles
        if self.food:
            occupied.add(self.food)
        if self.field_powerup:
            occupied.add(self.field_powerup.pos)
        pos = random_grid_position(occupied)
        if pos is not None:
            self.bonus_food = pos
            self.bonus_spawn_time = pygame.time.get_ticks()

    def _maybe_spawn_powerup(self):
        if self.field_powerup is not None:
            return
        if self.score < 5:
            return
        # Weighted random selection based on which power-ups are unlocked
        candidates = []
        weights = []
        for kind in (POWERUP_CHERRY, POWERUP_ICE, POWERUP_STAR, POWERUP_HEART):
            if kind == POWERUP_HEART and self.heart_used_this_game:
                continue
            if self.score < POWERUP_MIN_SCORE[kind]:
                continue
            candidates.append(kind)
            # Cherry/Ice/Star are common, Heart is rare
            weights.append(0.5 if kind == POWERUP_HEART else 1.0)
        if not candidates:
            return
        # Per-frame ~0.3% chance (roughly one every ~5s at 10fps)
        if random.random() > 0.003:
            return
        kind = random.choices(candidates, weights=weights)[0]
        occupied = set(self.snake1.body)
        if self.snake2:
            occupied |= set(self.snake2.body)
        occupied |= self.obstacles
        if self.food:
            occupied.add(self.food)
        if self.bonus_food:
            occupied.add(self.bonus_food)
        pos = random_grid_position(occupied)
        if pos is not None:
            self.field_powerup = PowerUpItem(kind, pos)

    def _trigger_game_over(self, reason):
        self.sound.play("game_over")
        self.game_over_reason = reason
        if self.score > self.highscore:
            self.highscore = self.score
            save_highscore(self.highscore)
        self.state = STATE_GAME_OVER

    # ----- Drawing -----
    def draw(self):
        scheme = self.scheme()
        self.screen.fill(scheme["bg"])
        self._draw_grid()

        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_OPTIONS:
            self._draw_options()
        elif self.state == STATE_PLAYING:
            self._draw_world()
            self.particles.draw(self.screen)
            self._draw_hud()
            self._draw_effects_overlay()
        elif self.state == STATE_PAUSED:
            self._draw_world()
            self.particles.draw(self.screen)
            self._draw_hud()
            self._draw_pause_overlay()
        elif self.state == STATE_GAME_OVER:
            self._draw_world()
            self.particles.draw(self.screen)
            self._draw_game_over()

        pygame.display.flip()

    def _draw_grid(self):
        scheme = self.scheme()
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, scheme["grid"],
                             (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, scheme["grid"],
                             (0, y), (SCREEN_WIDTH, y))

    def _draw_world(self):
        scheme = self.scheme()

        # Obstacles (with ice-warning flash when ice just expired)
        flash_obstacles = (self.flash_timer > 0 and self.ice_timer <= 0
                           and self.slow_timer <= 0)
        for ox, oy in self.obstacles:
            px, py = grid_to_pixel((ox, oy))
            rect = pygame.Rect(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2)
            # Tint slightly when ice is active
            if self.ice_timer > 0:
                color = (100, 180, 255)
            else:
                color = scheme["obstacle"]
            pygame.draw.rect(self.screen, color, rect)
            # Flash border briefly when ice warning
            border_color = scheme["accent"]
            if flash_obstacles:
                border_color = (255, 60, 60)
            pygame.draw.rect(self.screen, border_color, rect, 1)

        # Food
        if self.food:
            self._draw_food_piece(self.food, scheme["food"])
        if self.bonus_food:
            self._draw_food_piece(self.bonus_food, scheme["bonus"], bonus=True)

        # Field power-up
        if self.field_powerup:
            self.field_powerup.draw(self.screen, scheme)

        # Snakes
        if self.snake1.alive:
            self._draw_snake(self.snake1)
        if self.snake2 and self.snake2.alive:
            self._draw_snake(self.snake2)

    def _draw_food_piece(self, pos, color, bonus=False):
        px, py = grid_to_pixel(pos)
        if bonus:
            t = pygame.time.get_ticks() / 200.0
            radius = int((CELL_SIZE // 2 - 2) * (1 + 0.15 * math.sin(t)))
            cx, cy = px + CELL_SIZE // 2, py + CELL_SIZE // 2
            pygame.draw.circle(self.screen, color, (cx, cy), radius)
        else:
            rect = pygame.Rect(px + 2, py + 2, CELL_SIZE - 4, CELL_SIZE - 4)
            pygame.draw.rect(self.screen, color, rect)

    def _draw_snake(self, snake):
        # Brief transparency if collision-immune (just-got-heart)
        immune = snake.collision_immunity_timer > 0
        for i, segment in enumerate(snake.body):
            px, py = grid_to_pixel(segment)
            rect = pygame.Rect(px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2)
            color = snake.color_head if i == 0 else snake.color_body
            if immune and (pygame.time.get_ticks() // 80) % 2 == 0:
                # Flash white-ish when immune
                color = (240, 240, 240)
            pygame.draw.rect(self.screen, color, rect)

            if i == 0 and snake.alive:
                cx, cy = px + CELL_SIZE // 2, py + CELL_SIZE // 2
                dx, dy = snake.direction
                eye_offset = CELL_SIZE // 4
                eye1 = (int(cx + dx * eye_offset + dy * 3),
                        int(cy + dy * eye_offset + dx * 3))
                eye2 = (int(cx + dx * eye_offset - dy * 3),
                        int(cy + dy * eye_offset - dx * 3))
                pygame.draw.circle(self.screen, (0, 0, 0), eye1, 2)
                pygame.draw.circle(self.screen, (0, 0, 0), eye2, 2)

    def _draw_hud(self):
        scheme = self.scheme()
        elapsed = (pygame.time.get_ticks() - self.start_ticks) / 1000
        speed = self.effective_fps()

        # Top-left: Score / Speed / Time
        self.screen.blit(
            self.font_small.render(f"Score: {self.score}", True, scheme["text"]),
            (10, 8))
        self.screen.blit(
            self.font_small.render(f"High: {self.highscore}", True, scheme["text_dim"]),
            (SCREEN_WIDTH - 110, 8))
        self.screen.blit(
            self.font_small.render(f"Speed: {speed:.0f} FPS", True, scheme["accent"]),
            (10, 32))
        self.screen.blit(
            self.font_small.render(f"Time: {elapsed:05.1f}s", True, scheme["text_dim"]),
            (SCREEN_WIDTH - 130, 32))

        # Center top: mode flags + level
        flags = []
        if self.settings["wrap"] == "on":
            flags.append("WRAP")
        if self.settings["obstacles"] == "on":
            flags.append("OBS")
        if self.settings["two_player"] == "on":
            flags.append("2P")
        if flags:
            txt = self.font_tiny.render(" | ".join(flags),
                                        True, scheme["accent"])
            self.screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 8))

        # Second row: active effects + extra lives + level name
        effects = []
        if self.slow_timer > 0:
            effects.append(("🍒", self.slow_timer, POWERUP_DURATION[POWERUP_CHERRY]))
        if self.ice_timer > 0:
            effects.append(("❄", self.ice_timer, POWERUP_DURATION[POWERUP_ICE]))
        if self.star_timer > 0:
            effects.append(("★", self.star_timer, POWERUP_DURATION[POWERUP_STAR]))
        if self.extra_lives > 0:
            effects.append((f"♥ ×{self.extra_lives}", 0, 1))
        if effects:
            x = SCREEN_WIDTH // 2 - 90
            for icon, remaining, total in effects:
                txt = self.font_tiny.render(icon, True, scheme["accent"])
                self.screen.blit(txt, (x, 32))
                x += txt.get_width() + 6
                if total > 0 and remaining > 0:
                    # Draw small bar
                    ratio = remaining / total
                    bar_w = 30
                    bar_h = 4
                    bar_y = 34 + txt.get_height()
                    pygame.draw.rect(self.screen, scheme["text_dim"],
                                     (x, bar_y, bar_w, bar_h), 1)
                    pygame.draw.rect(self.screen, scheme["accent"],
                                     (x + 1, bar_y + 1,
                                      int((bar_w - 2) * ratio), bar_h - 2))
                    x += bar_w + 8

        # Level name (top-right area)
        if self.settings["obstacles"] == "on":
            level_label = LEVELS[self.settings["level"]][0]
            txt = self.font_tiny.render(f"Map: {level_label}",
                                        True, scheme["text_dim"])
            self.screen.blit(txt, (SCREEN_WIDTH - txt.get_width() - 10, 56))

    def _draw_effects_overlay(self):
        """Subtle full-screen tint based on active effects."""
        if self.flash_timer > 0:
            alpha = int(120 * (self.flash_timer / 0.4))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 60, 60, alpha))
            self.screen.blit(overlay, (0, 0))

    def _draw_menu(self):
        scheme = self.scheme()
        cy = SCREEN_HEIGHT // 2

        draw_text(self.screen, "SNAKE GAME", self.font_xl,
                  scheme["text"], (SCREEN_WIDTH // 2, cy - 160))
        draw_text(self.screen, "Enhanced Edition v2", self.font_medium,
                  scheme["accent"], (SCREEN_WIDTH // 2, cy - 110))

        lines = [
            ("ENTER / SPACE  -  Start", scheme["text"]),
            ("O               -  Options", scheme["text_dim"]),
            ("P               -  Pause", scheme["text_dim"]),
            ("Q / ESC         -  Quit", scheme["text_dim"]),
        ]
        for i, (line, color) in enumerate(lines):
            draw_text(self.screen, line, self.font_small, color,
                      (SCREEN_WIDTH // 2, cy - 50 + i * 28))

        # Feature blurb
        blurb = ("Particles • Power-Ups • Multiple Levels")
        draw_text(self.screen, blurb, self.font_small, scheme["accent"],
                  (SCREEN_WIDTH // 2, cy + 80))

        draw_text(self.screen, f"High Score: {self.highscore}",
                  self.font_large, scheme["accent"],
                  (SCREEN_WIDTH // 2, cy + 130))
        draw_text(self.screen, f"Theme: {self.settings['scheme'].title()}",
                  self.font_small, scheme["text_dim"],
                  (SCREEN_WIDTH // 2, cy + 175))

    def _draw_options(self):
        scheme = self.scheme()
        cy = SCREEN_HEIGHT // 2 - 120

        draw_text(self.screen, "OPTIONS", self.font_xl, scheme["text"],
                  (SCREEN_WIDTH // 2, cy))
        draw_text(self.screen, "Up/Down to select, Left/Right to change",
                  self.font_small, scheme["text_dim"],
                  (SCREEN_WIDTH // 2, cy + 50))

        for i, (key, kind, options) in enumerate(SETTING_OPTIONS):
            label = SETTING_LABELS[key]
            value = self.settings[key]
            if kind == "toggle":
                display = "ON" if value == "on" else "OFF"
            elif key == "level":
                display = LEVELS[value][0] if value in LEVELS else value
            else:
                display = value.title()
            row_y = cy + 100 + i * 38
            is_sel = (i == self.options_index)
            color = scheme["accent"] if is_sel else scheme["text"]
            arrow = "▶ " if is_sel else "  "
            draw_text_left(self.screen, arrow + label, self.font_small,
                           color, (SCREEN_WIDTH // 2 - 210, row_y))
            draw_text(self.screen, display, self.font_small, color,
                      (SCREEN_WIDTH // 2 + 130, row_y))

        draw_text(self.screen, "Press O or ESC to return",
                  self.font_tiny, scheme["text_dim"],
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))

    def _draw_pause_overlay(self):
        scheme = self.scheme()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        elapsed = (pygame.time.get_ticks() - self.start_ticks) / 1000
        cy = SCREEN_HEIGHT // 2

        draw_text(self.screen, "PAUSED", self.font_xl, scheme["text"],
                  (SCREEN_WIDTH // 2, cy - 110))

        stats = [
            f"Current Score: {self.score}",
            f"High Score:    {self.highscore}",
            f"Time Played:   {elapsed:05.1f} s",
            f"Food Eaten:    {self.snake1.food_eaten}",
            f"Bonus Eaten:   {self.snake1.bonus_eaten}",
            f"Snake Length:  {len(self.snake1.body)}",
            f"Speed:         {self.effective_fps():.0f} FPS",
            f"Extra Lives:   {self.extra_lives}",
        ]
        for i, line in enumerate(stats):
            draw_text_left(self.screen, line, self.font_small,
                           scheme["text_dim"], (SCREEN_WIDTH // 2 - 110,
                                                cy - 30 + i * 24))

        hints = [
            ("P / SPACE  -  Resume", scheme["text"]),
            ("R          -  Restart", scheme["text_dim"]),
            ("M          -  Main Menu", scheme["text_dim"]),
            ("ESC        -  Quit", scheme["text_dim"]),
        ]
        for i, (line, color) in enumerate(hints):
            draw_text(self.screen, line, self.font_small, color,
                      (SCREEN_WIDTH // 2, cy + 180 + i * 22))

    def _draw_game_over(self):
        scheme = self.scheme()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        cy = SCREEN_HEIGHT // 2
        draw_text(self.screen, "GAME OVER", self.font_xl, scheme["food"],
                  (SCREEN_WIDTH // 2, cy - 140))
        if self.game_over_reason:
            draw_text(self.screen, self.game_over_reason, self.font_medium,
                      scheme["text_dim"], (SCREEN_WIDTH // 2, cy - 90))

        elapsed = (pygame.time.get_ticks() - self.start_ticks) / 1000
        stats = [
            f"Final Score:  {self.score}",
            f"High Score:   {self.highscore}",
            f"Time Played:  {elapsed:05.1f} s",
            f"Food Eaten:   {self.snake1.food_eaten}",
            f"Bonus Eaten:  {self.snake1.bonus_eaten}",
            f"Max Length:   {len(self.snake1.body)}",
        ]
        for i, line in enumerate(stats):
            draw_text_left(self.screen, line, self.font_small,
                           scheme["text"], (SCREEN_WIDTH // 2 - 110,
                                            cy - 30 + i * 24))

        new_record = self.score == self.highscore and self.score > 0
        if new_record:
            draw_text(self.screen, "★ NEW HIGH SCORE ★",
                      self.font_medium, scheme["accent"],
                      (SCREEN_WIDTH // 2, cy + 130))

        hints = ("R / SPACE  -  Restart    M  -  Menu    Q  -  Quit",)
        draw_text(self.screen, hints[0], self.font_small, scheme["text_dim"],
                  (SCREEN_WIDTH // 2, cy + 175))

    # ----- Lifecycle -----
    def quit_game(self):
        pygame.quit()
        sys.exit(0)

    def run(self):
        last_time = pygame.time.get_ticks()
        while True:
            now = pygame.time.get_ticks()
            self.last_dt = min(0.1, (now - last_time) / 1000)
            last_time = now
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.effective_fps() if self.state == STATE_PLAYING
                            else FPS_BASE)


# ---------- Options menu definition ----------
SETTING_LABELS = {
    "wrap":       "Wrap walls",
    "obstacles":  "Obstacles",
    "level":      "Level",
    "two_player": "Two-player",
    "scheme":     "Color scheme",
    "sound":      "Sound",
}
SETTING_OPTIONS = [
    ("wrap",       "toggle", None),
    ("obstacles",  "toggle", None),
    ("level",      "cycle",  LEVEL_NAMES),
    ("two_player", "toggle", None),
    ("scheme",     "cycle",  SCHEME_NAMES),
    ("sound",      "toggle", None),
]


# ---------- Entry point ----------
def main():
    Game().run()


if __name__ == "__main__":
    main()