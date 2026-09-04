# Snake Game v2.0 — Comprehensive Implementation Prompt

## Overview
Take the existing single-file `snake_game.py` (an enhanced Snake game with sound, wrap mode, obstacles, color schemes, and two-player support) and extend it with three major feature sets:

1. **🪟 Particle Effects System** — visual juice for eating, bonuses, and crashes
2. **⚡ Power-Up System** — four collectible power-ups with unique effects
3. **🗺️ Multiple Levels / Maps** — pre-defined obstacle layouts loaded from data

The result must remain a **single self-contained Python file** that runs with `python snake_game.py`, requires only pygame/pygame-ce, and does not regress any existing functionality.

---

## Technical Constraints
- Python 3.8+
- pygame (or pygame-ce) — no other external dependencies
- **Single file**: all new code lives inside `snake_game.py`
- Backward compatibility: existing options (`wrap`, `obstacles`, `two_player`, `scheme`, `sound`) and settings persistence must keep working
- Default settings file (`settings.txt`) must remain compatible — new options are appended, never renamed
- FPS cap must still respect `FPS_MAX`
- Code must follow PEP 8 and the existing modular style (`Game` class with `handle_events` / `update` / `draw` separation, helper functions above the class, constants at the top)
- All new code must be clearly commented

---

## Feature 1: 🪟 Particle Effects System

### Goals
Add satisfying visual feedback whenever something interesting happens in the game.

### Particle Types

| Trigger | Particle Behavior |
|---|---|
| Eating normal food | 8-12 small colored particles burst outward from food position, fade out over ~0.4s |
| Eating bonus food | 20-25 golden particles, larger and longer-lived (~0.7s) |
| Game over | 30 red/orange particles burst from the snake's head position |
| Snake moves | Optional faint trail particles behind the head (toggleable, default ON for neon scheme only) |

### Implementation Requirements

1. Create a **`Particle` class** with:
   - `pos`: (x, y) in pixel coordinates
   - `vel`: (vx, vy) initial velocity (randomized)
   - `color`: RGB tuple
   - `lifetime`: total time to live in seconds
   - `age`: time since spawn
   - `size`: starting radius in pixels
   - Methods: `update(dt)`, `is_alive()`, `draw(surface)`

2. Create a **`ParticleSystem` class** managing all active particles:
   - `emit(pos, color, count, speed_range, lifetime_range, size_range)` — spawn N particles
   - `update(dt)` — advance all particles, cull dead ones
   - `draw(surface)` — render all live particles
   - Use simple physics: position += velocity * dt, no gravity (or very light gravity for game-over particles)

3. Integrate into the `Game` class:
   - `self.particles = ParticleSystem()` created in `reset()`
   - `update()` accepts `dt` (seconds since last frame) and calls `self.particles.update(dt)`
   - `draw()` calls `self.particles.draw(self.screen)` **after** drawing the world but **before** HUD/overlays

4. Particle rendering must:
   - Use `pygame.draw.circle` with the particle's current color
   - Fade alpha based on age (use `pygame.Surface` with `SRCALPHA` and per-pixel alpha)
   - Optionally shrink slightly as it ages for extra polish

5. Sound triggers already exist — wire particles to fire **at the same time** as the existing `self.sound.play("eat")` / `self.sound.play("bonus")` / `self.sound.play("game_over")` calls.

### Quality Checks
- Particles must not leak memory — dead particles must be removed every frame
- Must not affect game performance: target max ~200 active particles
- Must look good on all four color schemes (particles use the food's color, not the scheme background)

---

## Feature 2: ⚡ Power-Up System

### Goals
Introduce four collectible power-ups that spawn occasionally and grant temporary effects.

### Power-Up Definitions

| Power-Up | Spawn Condition | Effect | Duration | Visual |
|---|---|---|---|---|
| 🍒 **Cherry** (slow time) | Random after score ≥ 8 | Halves the game speed (FPS is multiplied by 0.5) | 6 seconds | Red circle with cherry icon (two small dark dots) |
| 🧊 **Ice** (freeze obstacles) | Random after score ≥ 12 | Obstacles become non-lethal (still rendered but collisions ignored) | 5 seconds | Light-blue diamond shape |
| ⭐ **Star** (double points) | Random after score ≥ 5 | All food/bonus points worth 2× | 8 seconds | Yellow star drawn with polygon points |
| 💖 **Heart** (extra life) | Random after score ≥ 15 | Grants 1 extra life; consumed on next wall/self collision | One-time | Pink/red heart drawn with two circles + triangle |

### Implementation Requirements

1. Add a **`PowerUp` class** with:
   - `kind`: one of `"cherry"`, `"ice"`, `"star"`, `"heart"`
   - `pos`: (x, y) grid coordinates
   - `spawn_time`: pygame tick when spawned
   - Lifetime on the ground: 8 seconds (then despawns if not collected)
   - Methods: `update()`, `is_expired()`, `draw(surface, scheme)`

2. Add a **`PowerUpManager` class** managing:
   - The currently-active power-up on the field (only one at a time)
   - All active effects on the player (can stack for different kinds, but only one of each kind at a time)
   - Methods:
     - `maybe_spawn(score)` — random chance per frame (after minimum score)
     - `update(dt)` — advance timers, expire effects
     - `apply_to(snake, game)` — when snake head reaches power-up position, activate effect
     - `draw(surface, scheme)` — render the on-field power-up if any

3. Per-effect state must be tracked on the `Game` (or `Snake`) so `update()` can apply them:
   - `self.slow_timer` — remaining seconds of slow effect
   - `self.ice_timer` — remaining seconds of ice effect
   - `self.star_timer` — remaining seconds of double-points effect
   - `self.extra_lives` — int, starting at 0
   - When `extra_lives > 0` and a collision would normally kill the snake, instead decrement lives, do **not** kill, and briefly flash the snake

4. Power-up spawning rules:
   - At most one power-up on the field at any time
   - Spawn chance per game tick: 0.5% per frame after the per-power-up minimum score is met (so it's rare but noticeable)
   - Spawn position must avoid the snake's body, food, bonus food, obstacles, and other power-ups
   - Spawn position should be in a free cell

5. Power-up points (collected):
   - Cherry: 0 points (utility)
   - Ice: 0 points (utility)
   - Star: 0 points (utility)
   - Heart: 0 points (utility, but gives a life)

6. **Scoring** when `star_timer > 0`:
   - Normal food: 2 points instead of 1
   - Bonus food: 6 points instead of 3

7. **Speed** when `slow_timer > 0`:
   - Effective FPS = `current_fps() * 0.5` (don't go below 5 FPS)

8. **Obstacles** when `ice_timer > 0`:
   - Rendered normally but collision checks skip them
   - When ice expires, briefly flash all obstacles to warn the player

9. HUD additions (top of screen):
   - Show active effect icons with a shrinking bar underneath each
   - Show "♥ × N" when extra_lives > 0
   - Use small icons drawn programmatically (no image files)

10. Sound additions (extend `SoundManager`):
    - `"powerup"` — happy ascending tone when collecting
    - `"powerdown"` — short blip when an effect expires
    - `"life"` — special chime when gaining an extra life

### Quality Checks
- Effects must stack additively (e.g., having both cherry and ice is fine and they should each tick down independently)
- Collecting a power-up while its effect is already active should refresh the duration (not stack)
- Power-ups must never spawn inside the snake, on food/bonus food, or on obstacles
- Heart power-up should be obviously more rare than the others (maybe only one Heart ever spawns per game, until used)
- All effects must work in **two-player mode** (affect both snakes)

---

## Feature 3: 🗺️ Multiple Levels / Maps

### Goals
Add pre-defined obstacle layouts so the game feels fresh across playthroughs.

### Levels to Implement

| Level | Layout Description |
|---|---|
| **Open Field** | No obstacles (current default behavior when `obstacles` setting is OFF) |
| **Border Frame** | A thick border of obstacles around the playfield, leaving a 4-cell playable inner area |
| **Crossroads** | A horizontal wall across the middle row and a vertical wall down the middle column (with small gaps at intersections) |
| **Maze Lite** | A simple symmetric maze pattern using corridors ~3 cells wide |
| **Quadrants** | Four obstacle "islands" — each in a corner, with a small gap to the center |
| **Spiral** | A spiral-shaped wall from the outer edge inward |

### Implementation Requirements

1. Each level is defined as a **function or data structure** that returns a `set` of `(x, y)` grid coordinates representing obstacles:
   ```python
   def level_border_frame():
       obstacles = set()
       # ... populate and return
       return obstacles
   ```

2. Place all level functions in a module-level dict:
   ```python
   LEVELS = {
       "open_field":    ("Open Field",    level_open_field),
       "border_frame":  ("Border Frame",  level_border_frame),
       "crossroads":    ("Crossroads",    level_crossroads),
       "maze_lite":     ("Maze Lite",     level_maze_lite),
       "quadrants":     ("Quadrants",     level_quadrants),
       "spiral":        ("Spiral",        level_spiral),
   }
   ```

3. Add a new persistent setting: `"level"` with default value `"open_field"`.
   - Update `DEFAULT_SETTINGS`, `load_settings`, `save_settings` to include this key
   - The existing `obstacles` toggle should still work: when ON, the **selected level** is used; when OFF, no obstacles (regardless of level setting)

4. Add `level` to the **Options menu** as a `cycle`-type option (same UX as `scheme`).

5. Levels must:
   - Never spawn an obstacle on the snake's starting position (the center area)
   - Be deterministic (same level always produces same layout — no randomness in the level data itself)
   - Leave enough free space for the snake to move (at least 30% of cells should be free)

6. When the game **resets** (`reset()`), it must use the currently-selected level's obstacle set.
   - The existing `_generate_obstacles` method can stay as a fallback for a "Random" level (or be removed in favor of fixed levels — your choice)
   - Decision: **remove** `_generate_obstacles` in favor of the fixed level catalog for predictability

7. Each level should have a **name** shown in the Options menu (e.g., "Border Frame", "Crossroads", etc.).

### Quality Checks
- Levels must not be unfair: the snake must have a viable path to any food spawn point
- Levels must be visually distinct
- The Options menu must handle the new "level" entry alongside existing options without overflow (5 → 6 rows now, so reduce font size or add scrolling if needed — probably fine at current sizes since the menu is tall enough)
- If the user picks an unknown level (e.g., from a corrupted settings file), gracefully fall back to `"open_field"`

---

## Integration & Polish

### Settings Update
After implementing features, the default settings dict becomes:
```python
DEFAULT_SETTINGS = {
    "wrap": "off",
    "obstacles": "off",
    "two_player": "off",
    "scheme": "classic",
    "sound": "on",
    "level": "open_field",
}
```

`load_settings` already gracefully ignores unknown keys, so old settings.txt files will continue to work (just defaulting to `"open_field"`).

### HUD
The HUD must fit:
- Score (top-left)
- High score (top-right)
- Speed (FPS)
- Time played
- Active flags (WRAP / OBS / 2P)
- Active power-up effects with timers
- Extra lives indicator

If space gets tight, use a **two-row layout** or move power-up icons to a centered strip below the score.

### Menu Updates
- Main menu should mention the new features (one-line blurb)
- Options menu gets one new row for "Level"

### Documentation
Update `README.md` with:
- New feature descriptions
- Updated controls table (no new controls needed, but document power-ups)
- New "Levels" section listing the available maps

---

## Testing & Validation

After implementation, perform these checks (all must pass):

1. **Compile check**: `python -m py_compile snake_game.py` exits with 0
2. **Import check**: importing the module and instantiating `Game()` works without exceptions
3. **Smoke test** (write a temporary `smoke_test.py` in the same folder that):
   - Creates a Game
   - Toggles each new option (level, wrap, obstacles, two_player, etc.)
   - Iterates through every level and verifies the obstacle set is non-empty (except open_field) and doesn't overlap with the snake start
   - Verifies particles can be emitted without error
   - Verifies each power-up kind can be spawned and applied without crashing
   - Runs 100 game updates without exceptions
   - Then deletes itself
4. **Visual smoke test**: launch the actual game and confirm the window opens without errors

---

## Deliverables

1. **`snake_game.py`** — updated with all three features, single file
2. **`README.md`** — updated documentation
3. **`prompt_v2.md`** — this prompt (kept for reference)
4. **No new external files** required to run the game (highscore.txt and settings.txt are auto-created)

---

## Implementation Order (recommended)

1. **Particles first** — isolated, easy to verify, immediately visible improvement
2. **Levels second** — pure data + small wiring in `reset()`, low risk
3. **Power-ups last** — touches many systems (collision, scoring, speed, rendering, HUD, sound) so benefit from stable foundation

After each feature:
- Run `python -m py_compile snake_game.py`
- Run the smoke test (extend it incrementally)
- Confirm the game still launches and plays

When all three are done:
- Update README
- Run the full smoke test
- Launch the game for the user to play

---

## Out of Scope (explicitly NOT doing in this prompt)

- Online leaderboards
- Replay system
- Mobile/touch controls
- AI snake opponent
- Custom skin editor
- Background music loop
- Animated background
- Multiple high scores table

These can be future prompts.

---

Good luck — let's make this game feel *alive*. 🐍✨