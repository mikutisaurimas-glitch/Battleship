import tkinter as tk
import random
import sys
import time
from Ship import Ship
from Board import Board
from Game import Game
from ShipFactory import ShipFactory
from Stats import load as load_stats, record_win, record_loss, summary as stats_summary

IS_WINDOWS = sys.platform == "win32"

FONT_MONO  = "Consolas"    if IS_WINDOWS else "Menlo"
FONT_TITLE = "Courier New" if IS_WINDOWS else "American Typewriter"

COLS = 10
ROWS = 10
CELL = 36
GAP  = 2

BG         = "#0e2a4a"
PANEL_BG   = "#151a2e"
WATER      = "#6e97c5"
SHIP_COL   = "#000000"
PREVIEW_BG = "#1a3a5c"
BADPLACE   = "#7b241c"
HIT_COL    = "#c0392b"
MISS_COL   = "#2c3e50"
SUNK_COL   = "#8e1a10"
LABEL_FG   = "#4a9cc7"
WHITE      = "#e8f4f8"
GOLD       = "#f1c40f"
GREEN      = "#27ae60"
GRID_LINE  = "#1a3a5c"

HEADER = 22
SIDE   = 22

CANVAS_W = SIDE + COLS * CELL + (COLS - 1) * GAP

INSTR = "Use arrow keys or mouse to place, R or right mouse button to rotate, Enter or left mouse button to confirm."


class BoardCanvas(tk.Canvas):
    def __init__(self, parent, owner, gui, **kwargs):
        w = CANVAS_W
        h = HEADER + ROWS * CELL + (ROWS - 1) * GAP
        super().__init__(parent, width=w, height=h,
                         bg=BG, highlightthickness=0, **kwargs)
        self.owner = owner
        self.gui   = gui
        self.reset_canvas()

        if owner == "enemy":
            self.bind("<Button-1>", self._on_click)
        elif owner == "player":
            self.bind("<Button-1>", self._on_place_click)
            self.bind("<Button-2>", self.gui._toggle_orientation)
            self.bind("<Button-3>", self.gui._toggle_orientation)

        self.bind("<Motion>", self._on_motion)
        self.bind("<Leave>",  self._on_leave)

    def reset_canvas(self):
        self.delete("all")
        self._state = {}
        self._items = {}
        self._preview_ids = []
        self._draw_grid()

    def _cell_xy(self, r, c):
        x = SIDE + c * (CELL + GAP)
        y = HEADER + r * (CELL + GAP)
        return x, y

    def _pixel_to_cell(self, px, py):
        col = (px - SIDE) // (CELL + GAP)
        row = (py - HEADER) // (CELL + GAP)
        if 0 <= row < ROWS and 0 <= col < COLS:
            return int(row), int(col)
        return None

    def _draw_grid(self):
        for c in range(COLS):
            x, _ = self._cell_xy(0, c)
            self.create_text(x + CELL // 2, HEADER // 2,
                             text=chr(65 + c), fill=LABEL_FG,
                             font=(FONT_MONO, 10, "bold"))
        for r in range(ROWS):
            _, y = self._cell_xy(r, 0)
            self.create_text(SIDE // 2, y + CELL // 2,
                             text=str(r + 1), fill=LABEL_FG,
                             font=(FONT_MONO, 10, "bold"))
        for r in range(ROWS):
            for c in range(COLS):
                x, y = self._cell_xy(r, c)
                rid = self.create_rectangle(x, y, x + CELL, y + CELL,
                                            fill=WATER, outline=GRID_LINE, width=1)
                self._items[(r, c)] = rid

    def _play_splash(self, r, c):
        x_mid, y_mid = self._cell_xy(r, c)
        x_mid += CELL // 2
        y_mid += CELL // 2

        def animate_ripple(radius, step):
            if step > 6: return
            color = "#a0c4ff" if step % 2 == 0 else WHITE
            ripple = self.create_oval(x_mid - radius, y_mid - radius,
                                      x_mid + radius, y_mid + radius,
                                      outline=color, width=2)
            self.after(40, lambda: [self.delete(ripple), animate_ripple(radius + 4, step + 1)])

        animate_ripple(4, 0)

    def draw_rect_ship(self, r, c, size, orientation, color):
        ids = []
        cells = [(r, c + i) if orientation == "H" else (r + i, c) for i in range(size)]
        for (pr, pc) in cells:
            if 0 <= pr < ROWS and 0 <= pc < COLS:
                x, y = self._cell_xy(pr, pc)
                rid = self.create_rectangle(x, y, x + CELL, y + CELL,
                                            fill=color, outline="#333333", width=1)
                ids.append(rid)
        return ids

    def paint(self, r, c, colour, shape_type=""):
        x, y = self._cell_xy(r, c)
        tag = f"mark_{r}_{c}"
        self.delete(tag)
        self.itemconfig(self._items[(r, c)], fill=colour)
        padding = 6
        if shape_type == "✕":
            self.create_line(x + padding, y + padding,
                             x + CELL - padding, y + CELL - padding,
                             fill=WHITE, width=3, tags=tag)
            self.create_line(x + CELL - padding, y + padding,
                             x + padding, y + CELL - padding,
                             fill=WHITE, width=3, tags=tag)
        elif shape_type == "O":
            self.create_oval(x + padding, y + padding,
                             x + CELL - padding, y + CELL - padding,
                             outline=WHITE, width=3, tags=tag)
        self.update_idletasks()

    def _on_click(self, event):
        cell = self._pixel_to_cell(event.x, event.y)
        if cell: self.gui._enemy_click(*cell)

    def _on_place_click(self, event):
        cell = self._pixel_to_cell(event.x, event.y)
        if cell: self.gui._place_ship_click(*cell)

    def _on_motion(self, event):
        cell = self._pixel_to_cell(event.x, event.y)
        if self.owner == "player" and self.gui.placing and cell:
            self.gui._preview(*cell)

    def _on_leave(self, event):
        if self.owner == "player":
            self.gui._clear_preview()


class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚓ BATTLESHIP ⚓")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._init_game_vars()
        self._build_ui()
        self.stats = load_stats()
        self.game_start_time = None

    def _init_game_vars(self):
        self.game = None
        self.placing = True
        self.ai_thinking = False
        self.ships_to_place = ShipFactory.create_fleet()
        self.ship_index = 0
        self.orientation = "H"
        self.current_pos = [0, 0]
        self._temp_board = Board(10)
        self.hits = 0
        self.misses = 0
        self.sunk = 0

    def _build_ui(self):
        tk.Label(self.root, text="⚓ B A T T L E S H I P ⚓",
                 font=(FONT_TITLE, 24, "bold"),
                 bg=BG, fg=GOLD).pack(pady=(25, 12))

        main_container = tk.Frame(self.root, bg=BG)
        main_container.pack(expand=True, padx=40, pady=10)

        left_col = tk.Frame(main_container, bg=BG)
        left_col.pack(side="left", padx=20)

        l_lbl_frame = tk.Frame(left_col, bg=BG, width=CANVAS_W, height=30)
        l_lbl_frame.pack_propagate(False)
        l_lbl_frame.pack()
        tk.Label(l_lbl_frame, text="YOUR FLEET", font=(FONT_MONO, 12, "bold"),
                 bg=BG, fg=GREEN).pack(expand=True)

        self.player_canvas = BoardCanvas(left_col, "player", self)
        self.player_canvas.pack()

        tk.Label(main_container, text="⚔", font=("Courier", 32),
                 bg=BG, fg=GOLD).pack(side="left", padx=15)

        right_col = tk.Frame(main_container, bg=BG)
        right_col.pack(side="left", padx=20)

        r_lbl_frame = tk.Frame(right_col, bg=BG, width=CANVAS_W, height=30)
        r_lbl_frame.pack_propagate(False)
        r_lbl_frame.pack()
        tk.Label(r_lbl_frame, text="ENEMY FLEET", font=(FONT_MONO, 12, "bold"),
                 bg=BG, fg=HIT_COL).pack(expand=True)

        self.enemy_canvas = BoardCanvas(right_col, "enemy", self)
        self.enemy_canvas.pack()

        bottom_panel = tk.Frame(self.root, bg=PANEL_BG)
        bottom_panel.pack(fill="x", side="bottom")

        self.status_bg = tk.Label(bottom_panel, bg=PANEL_BG)
        self.status_bg.pack(fill="x")

        self.status_var = tk.StringVar(value=INSTR)
        self.status_label = tk.Label(self.status_bg, textvariable=self.status_var,
                                     font=(FONT_MONO, 11), bg=PANEL_BG, fg=WHITE, pady=12)
        self.status_label.pack()

        score_row = tk.Frame(bottom_panel, bg=PANEL_BG)
        score_row.pack(pady=(0, 12))
        self.hits_var = tk.StringVar(value="Hits: 0")
        self.miss_var = tk.StringVar(value="Misses: 0")
        self.sunk_var = tk.StringVar(value="Sunk: 0 / 5")
        for var in (self.hits_var, self.miss_var, self.sunk_var):
            tk.Label(score_row, textvariable=var, font=(FONT_MONO, 12),
                     bg=PANEL_BG, fg=LABEL_FG, padx=30).pack(side="left")

        self.place_frame = tk.Frame(bottom_panel, bg=PANEL_BG)
        self.place_frame.pack(pady=(0, 15))
        self._update_place_panel()

        self.root.bind("<Left>",   lambda e: self._move_ship(0, -1))
        self.root.bind("<Right>",  lambda e: self._move_ship(0,  1))
        self.root.bind("<Up>",     lambda e: self._move_ship(-1, 0))
        self.root.bind("<Down>",   lambda e: self._move_ship( 1, 0))
        self.root.bind("<Return>", lambda e: self._confirm_placement())
        self.root.bind("<r>",      self._toggle_orientation)
        self.root.bind("<R>",      self._toggle_orientation)

        self.root.after(100, lambda: self._preview(0, 0))

    def _screen_shake(self, intensity=5, steps=10):
        orig_x = self.root.winfo_x()
        orig_y = self.root.winfo_y()

        def shake(n):
            if n == 0:
                self.root.geometry(f"+{orig_x}+{orig_y}")
                return
            nx = orig_x + random.randint(-intensity, intensity)
            ny = orig_y + random.randint(-intensity, intensity)
            self.root.geometry(f"+{nx}+{ny}")
            self.root.after(20, lambda: shake(n - 1))

        shake(steps)

    def _flash_status(self, color):
        self.status_bg.config(bg=color)
        self.status_label.config(bg=color)
        self.root.after(200, lambda: [self.status_bg.config(bg=PANEL_BG),
                                      self.status_label.config(bg=PANEL_BG)])

    def _reset_game(self, popup):
        popup.destroy()
        self._init_game_vars()
        self.player_canvas.reset_canvas()
        self.enemy_canvas.reset_canvas()
        self.hits_var.set("Hits: 0")
        self.miss_var.set("Misses: 0")
        self.sunk_var.set("Sunk: 0 / 5")
        self.status_var.set(INSTR)
        self._update_place_panel()
        self.root.after(100, lambda: self._preview(0, 0))

    def _update_place_panel(self):
        for w in self.place_frame.winfo_children(): w.destroy()
        if self.ship_index >= len(self.ships_to_place): return
        ship = self.ships_to_place[self.ship_index]
        container = tk.Frame(self.place_frame, bg=PANEL_BG)
        container.pack()
        tk.Label(container, text=f"PLACING: {ship.name.upper()} (SIZE {ship.size})",
                 font=(FONT_MONO, 12), bg=PANEL_BG, fg=GOLD).pack(side="left", padx=15)
        rot_text = "ROTATION: HORIZONTAL ->" if self.orientation == "H" else "ROTATION: VERTICAL v"
        tk.Label(container, text=rot_text, font=(FONT_MONO, 11),
                 bg=PANEL_BG, fg=WHITE).pack(side="left")

    def _toggle_orientation(self, event=None):
        if not self.placing: return
        self.orientation = "V" if self.orientation == "H" else "H"
        self._preview(self.current_pos[0], self.current_pos[1])
        self._update_place_panel()

    def _move_ship(self, dr, dc):
        if not self.placing: return
        self._preview(self.current_pos[0] + dr, self.current_pos[1] + dc)

    def _valid_placement(self, r, c, size, orientation):
        if orientation == "H" and c + size > COLS: return False
        if orientation == "V" and r + size > ROWS: return False
        cells = [(r, c + i) if orientation == "H" else (r + i, c) for i in range(size)]
        return all(self.player_canvas._state.get(cell) != "SHIP" for cell in cells)

    def _preview(self, r, c):
        self._clear_preview()
        if self.ship_index >= len(self.ships_to_place): return
        ship = self.ships_to_place[self.ship_index]
        if self.orientation == "H":
            r, c = max(0, min(r, ROWS - 1)), max(0, min(c, COLS - ship.size))
        else:
            r, c = max(0, min(r, ROWS - ship.size)), max(0, min(c, COLS - 1))
        self.current_pos = [r, c]
        p_color = PREVIEW_BG if self._valid_placement(r, c, ship.size, self.orientation) else BADPLACE
        self.player_canvas._preview_ids = self.player_canvas.draw_rect_ship(
            r, c, ship.size, self.orientation, p_color)

    def _clear_preview(self):
        for pid in self.player_canvas._preview_ids:
            self.player_canvas.delete(pid)
        self.player_canvas._preview_ids = []

    def _confirm_placement(self):
        if not self.placing: return
        self._place_ship_click(self.current_pos[0], self.current_pos[1])

    def _place_ship_click(self, r, c):
        if self.ship_index >= len(self.ships_to_place): return
        ship = self.ships_to_place[self.ship_index]
        if self.orientation == "H": c = max(0, min(c, COLS - ship.size))
        else: r = max(0, min(r, ROWS - ship.size))
        if not self._valid_placement(r, c, ship.size, self.orientation): return
        self._clear_preview()
        self._temp_board.place_ship(Ship(ship.name, ship.size), r, c, self.orientation)
        cells = [(r, c + i) if self.orientation == "H" else (r + i, c) for i in range(ship.size)]
        for (sr, sc) in cells:
            self.player_canvas.paint(sr, sc, SHIP_COL)
            self.player_canvas._state[(sr, sc)] = "SHIP"
        self.ship_index += 1
        if self.ship_index >= len(self.ships_to_place):
            self._start_game()
        else:
            self._update_place_panel()
            self.root.after(10, lambda: self._preview(r, c))

    def _start_game(self):
        self._clear_preview()
        self.game = Game("Player")
        self.game.player.board = self._temp_board
        self.placing = False
        self._update_place_panel()
        self.game_start_time = time.time()
        if self.game.ai_goes_first:
            self.ai_thinking = True
            self.status_var.set("AI goes first! Enemy is thinking...")
            self.root.after(1000, self._ai_fire)
        else:
            self.status_var.set("You go first! Attack the enemy.")

    def _enemy_click(self, r, c):
        if self.placing or self.ai_thinking or self.game is None or self.game.game_over: return
        if self.enemy_canvas._state.get((r, c)) == "GUESSED": return
        result, won, extra_turn = self.game.player_turn(r, c)
        if result == "Already attacked": return
        self._apply_result_enemy(r, c, result, force_sunk=won)
        self.status_var.set(f"Target at {chr(65+c)}{r+1}: {result.upper()} 🎯")
        if won:
            self._screen_shake(intensity=8)
            self.root.after(300, lambda: self.show_end_screen("MISSION SUCCESS!", GOLD))
        elif not extra_turn:
            self.ai_thinking = True
            self.status_var.set("AI THINKING...")
            self.root.after(800, self._ai_fire)

    def _apply_result_enemy(self, r, c, result, force_sunk=False):
        res_lower = result.lower()
        is_sunk = "sunk" in res_lower or force_sunk
        if is_sunk:
            self._flash_status(GREEN)
            self._screen_shake(intensity=4)
            if self.enemy_canvas._state.get((r, c)) != "GUESSED":
                self.hits += 1
                self.sunk += 1
            if self.game:
                target_ship = next(
                    (s for s in self.game.ai.board.ships if (r, c) in s.positions), None)
                if target_ship:
                    for (sr, sc) in target_ship.positions:
                        self.enemy_canvas.paint(sr, sc, SUNK_COL, "✕")
                        self.enemy_canvas._state[(sr, sc)] = "GUESSED"
                else:
                    self.enemy_canvas.paint(r, c, SUNK_COL, "✕")
                    self.enemy_canvas._state[(r, c)] = "GUESSED"
        elif "hit" in res_lower:
            self._flash_status("#1a4a2a")
            self.enemy_canvas.paint(r, c, HIT_COL, "✕")
            if self.enemy_canvas._state.get((r, c)) != "GUESSED":
                self.hits += 1
            self.enemy_canvas._state[(r, c)] = "GUESSED"
        else:
            self.enemy_canvas._play_splash(r, c)
            self.enemy_canvas.paint(r, c, MISS_COL, "O")
            self.enemy_canvas._state[(r, c)] = "GUESSED"
            self.misses += 1
        self.hits_var.set(f"Hits: {self.hits}")
        self.miss_var.set(f"Misses: {self.misses}")
        self.sunk_var.set(f"Sunk: {self.sunk} / 5")

    def _ai_fire(self):
        if self.game is None or self.game.game_over: return
        result, x, y, lost, extra_turn = self.game.ai_turn()
        self.status_var.set(f"Enemy attacks {chr(65+y)}{x+1}: {result.upper()}")
        res_lower = result.lower()
        if "sunk" in res_lower or lost:
            self._flash_status(BADPLACE)
            self._screen_shake(intensity=6)
            if lost:
                self._paint_all_sunk_player_ships()
            else:
                ship_name = result.split(":")[1] if ":" in result else None
                target_ship = next(
                    (s for s in self.game.player.board.ships if s.name == ship_name), None)
                if target_ship:
                    for (sr, sc) in target_ship.positions:
                        self.player_canvas.paint(sr, sc, SUNK_COL, "✕")
                else:
                    self.player_canvas.paint(x, y, SUNK_COL, "✕")
        elif "hit" in res_lower:
            self._flash_status("#4a1a1a")
            self.player_canvas.paint(x, y, HIT_COL, "✕")
        else:
            self.player_canvas._play_splash(x, y)
            self.player_canvas.paint(x, y, MISS_COL, "O")

        if lost:
            self.root.after(500, lambda: self.show_end_screen("MISSION FAILED!", HIT_COL))
        elif extra_turn:
            self.root.after(800, self._ai_fire)
        else:
            self.ai_thinking = False
            self.status_var.set("YOUR TURN: Select enemy coordinate")

    def _paint_all_sunk_player_ships(self):
        if self.game:
            for ship in self.game.player.board.ships:
                for (sr, sc) in ship.positions:
                    self.player_canvas.paint(sr, sc, SUNK_COL, "✕")

    def show_end_screen(self, message, color):
        elapsed = time.time() - self.game_start_time if self.game_start_time else 0
        if "SUCCESS" in message:
            record_win(self.stats, self.hits + self.misses, elapsed)
        else:
            record_loss(self.stats)
        popup = tk.Toplevel(self.root)
        popup.title("End of Mission")
        popup.geometry("350x220")
        popup.configure(bg=PANEL_BG)
        popup.resizable(False, False)
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 110
        popup.geometry(f"+{x}+{y}")
        tk.Label(popup, text=message, font=(FONT_MONO, 20, "bold"),
                 bg=PANEL_BG, fg=color).pack(expand=True, pady=(20, 0))
        tk.Label(popup, text=stats_summary(self.stats), font=(FONT_MONO, 9),
                 bg=PANEL_BG, fg=LABEL_FG, justify="center").pack(pady=(0, 8))
        btn_frame = tk.Frame(popup, bg=PANEL_BG)
        btn_frame.pack(expand=True, pady=20)
        tk.Button(btn_frame, text="PLAY AGAIN", font=(FONT_MONO, 10, "bold"),
                  bg="#dddddd", fg="#000000", highlightbackground=PANEL_BG,
                  command=lambda: self._reset_game(popup)).pack(side="left", padx=10)
        tk.Button(btn_frame, text="EXIT GAME", font=(FONT_MONO, 10, "bold"),
                  bg="#bbbbbb", fg="#000000", highlightbackground=PANEL_BG,
                  command=self.root.quit).pack(side="left", padx=10)
        popup.grab_set()


if __name__ == "__main__":
    root = tk.Tk()
    if IS_WINDOWS:
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    app = BattleshipGUI(root)
    root.mainloop()
