import random
import tkinter as tk
from tkinter import ttk


BASE_TURN_MS = 5500
CLEAR_ACCURACY = 1.0
MISS_PENALTY_MS = 600
QUESTIONS_PER_STAGE = 20
TICK_MS = 100
WINDOW_WIDTH = 480
WINDOW_HEIGHT = 640

BG_COLOR = "#000000"
PANEL_COLOR = "#2B335F"
CARD_COLOR = "#000000"
BORDER_COLOR = "#EEEEEE"
HOVER_BORDER = "#E9C35B"
TITLE_COLOR = "#E9C35B"
TEXT_PRIMARY = "#EEEEEE"
TEXT_DIM = "#A3A3A3"
TEXT_GOOD = "#70C6A9"
TEXT_WARN = "#D4186C"
TEXT_INFO = "#A9C1FF"
DIGIT_BG = "#395C98"
DIGIT_ACTIVE = "#2B4675"
SPECIAL_BG = "#7E2072"
SPECIAL_ACTIVE = "#601858"
RESET_BG = "#7E2072"
RESET_ACTIVE = "#601858"
PIXEL_FONT = ("Courier", 13, "bold")
PIXEL_FONT_SMALL = ("Courier", 11, "bold")
PIXEL_FONT_LARGE = ("Courier", 28, "bold")
PIXEL_FONT_XL = ("Courier", 34, "bold")
KEYPAD_DIGIT_FONT = ("Courier", 24, "bold")
KEYPAD_ACTION_FONT = ("Courier", 14, "bold")

KEYPAD_LAYOUT = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
    ["0", "SKIP", "RESET"],
]


class OniCalculationTk:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Oni Calculation 6 - Tkinter Sample")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.best_stage = 1
        self.after_id = None

        self.title_var = tk.StringVar()
        self.stage_var = tk.StringVar()
        self.best_var = tk.StringVar()
        self.turn_var = tk.StringVar()
        self.acc_var = tk.StringVar()
        self.problem_var = tk.StringVar()
        self.instruction_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.result_title_var = tk.StringVar()
        self.result_score_var = tk.StringVar()
        self.result_accuracy_var = tk.StringVar()
        self.result_message_var = tk.StringVar()
        self.result_hint_var = tk.StringVar(value="Press Enter/Space or use the buttons below.")

        self.build_ui()
        self.bind_keys()
        self.reset_all()
        self.tick()

    def build_ui(self):
        self.root.configure(bg=BG_COLOR)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(
            "Oni.Horizontal.TProgressbar",
            troughcolor=DIGIT_BG,
            background=TEXT_GOOD,
            bordercolor=BORDER_COLOR,
            lightcolor=TEXT_GOOD,
            darkcolor=TEXT_GOOD,
            thickness=12,
        )

        shell = tk.Frame(self.root, bg=BG_COLOR, padx=18, pady=18)
        shell.pack(fill="both", expand=True)

        game_shell = tk.Frame(
            shell,
            bg=BG_COLOR,
            padx=14,
            pady=12,
            highlightbackground=BORDER_COLOR,
            highlightthickness=2,
        )
        game_shell.pack(fill="both", expand=True)

        header = tk.Frame(game_shell, bg=BG_COLOR)
        header.pack(fill="x")

        tk.Label(
            header,
            textvariable=self.title_var,
            font=PIXEL_FONT,
            bg=BG_COLOR,
            fg=TITLE_COLOR,
        ).pack(anchor="w")

        meta = tk.Frame(header, bg=BG_COLOR)
        meta.pack(fill="x", pady=(8, 0))

        tk.Label(meta, textvariable=self.stage_var, font=PIXEL_FONT_SMALL, bg=BG_COLOR, fg=TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        tk.Label(meta, textvariable=self.best_var, font=PIXEL_FONT_SMALL, bg=BG_COLOR, fg=TEXT_DIM).grid(row=0, column=1, sticky="e")
        tk.Label(meta, textvariable=self.turn_var, font=PIXEL_FONT_SMALL, bg=BG_COLOR, fg=TEXT_PRIMARY).grid(row=1, column=0, sticky="w", pady=(4, 0))
        tk.Label(meta, textvariable=self.acc_var, font=PIXEL_FONT_SMALL, bg=BG_COLOR, fg=TEXT_INFO).grid(row=1, column=1, sticky="e", pady=(4, 0))
        meta.grid_columnconfigure(0, weight=1)
        meta.grid_columnconfigure(1, weight=1)

        container = tk.Frame(game_shell, bg=BG_COLOR)
        container.pack(fill="both", expand=True, pady=(14, 0))

        self.play_screen = tk.Frame(container, bg=BG_COLOR)
        self.result_screen = tk.Frame(container, bg=BG_COLOR)

        for frame in (self.play_screen, self.result_screen):
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.build_play_screen()
        self.build_result_screen()

    def build_play_screen(self):
        problem_card = tk.Frame(
            self.play_screen,
            bg=PANEL_COLOR,
            padx=16,
            pady=12,
            highlightbackground=TEXT_PRIMARY,
            highlightthickness=2,
        )
        problem_card.pack(fill="x")

        tk.Label(
            problem_card,
            textvariable=self.problem_var,
            font=PIXEL_FONT_XL,
            bg=PANEL_COLOR,
            fg=TEXT_PRIMARY,
        ).pack(pady=(8, 12))

        self.progress = ttk.Progressbar(problem_card, mode="determinate", maximum=BASE_TURN_MS, style="Oni.Horizontal.TProgressbar")
        self.progress.pack(fill="x")

        status_row = tk.Frame(problem_card, bg=PANEL_COLOR)
        status_row.pack(fill="x", pady=(8, 0))
        status_row.grid_columnconfigure(0, weight=1)
        status_row.grid_columnconfigure(1, weight=1)

        tk.Label(
            status_row,
            textvariable=self.instruction_var,
            font=PIXEL_FONT_SMALL,
            bg=PANEL_COLOR,
            fg=TEXT_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")
        self.status_label = tk.Label(
            status_row,
            textvariable=self.status_var,
            font=PIXEL_FONT_SMALL,
            bg=PANEL_COLOR,
            fg=TEXT_DIM,
            anchor="e",
        )
        self.status_label.grid(row=0, column=1, sticky="e")

        keypad = tk.Frame(self.play_screen, bg=BG_COLOR)
        keypad.pack(fill="both", expand=True, pady=(6, 0))

        for row_index, row in enumerate(KEYPAD_LAYOUT):
            keypad.grid_rowconfigure(row_index, weight=1, uniform="keypad", minsize=80)
            for col_index, label in enumerate(row):
                keypad.grid_columnconfigure(col_index, weight=1, uniform="keypad", minsize=108)
                button = tk.Label(
                    keypad,
                    text=label,
                    font=KEYPAD_DIGIT_FONT if label.isdigit() else KEYPAD_ACTION_FONT,
                    bg=DIGIT_BG if label.isdigit() else SPECIAL_BG,
                    fg=TEXT_PRIMARY,
                    anchor="center",
                    cursor="hand2",
                    highlightbackground=BORDER_COLOR,
                    highlightcolor=BORDER_COLOR,
                    highlightthickness=2,
                )
                button.bind("<Button-1>", lambda _event, value=label: self.handle_keypad(value))
                button.bind("<Enter>", lambda _event, widget=button: widget.configure(highlightbackground=HOVER_BORDER, highlightcolor=HOVER_BORDER))
                button.bind("<Leave>", lambda _event, widget=button: widget.configure(highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR))
                button.grid(row=row_index, column=col_index, sticky="nsew", padx=6, pady=6)

    def build_result_screen(self):
        result_card = tk.Frame(
            self.result_screen,
            bg=CARD_COLOR,
            padx=18,
            pady=18,
            highlightbackground=BORDER_COLOR,
            highlightthickness=2,
        )
        result_card.pack(fill="x", pady=(8, 0))

        tk.Label(result_card, textvariable=self.result_title_var, font=PIXEL_FONT, bg=CARD_COLOR, fg=TEXT_PRIMARY).pack(anchor="w")
        tk.Label(result_card, textvariable=self.result_score_var, font=PIXEL_FONT_SMALL, bg=CARD_COLOR, fg=TEXT_PRIMARY).pack(anchor="w", pady=(18, 0))
        tk.Label(result_card, textvariable=self.result_accuracy_var, font=PIXEL_FONT_SMALL, bg=CARD_COLOR, fg=TEXT_INFO).pack(anchor="w", pady=(8, 0))
        self.result_message_label = tk.Label(result_card, textvariable=self.result_message_var, font=PIXEL_FONT, bg=CARD_COLOR, fg=TEXT_GOOD)
        self.result_message_label.pack(anchor="w", pady=(18, 0))
        tk.Label(result_card, textvariable=self.result_hint_var, font=PIXEL_FONT_SMALL, bg=CARD_COLOR, fg=TEXT_DIM).pack(anchor="w", pady=(18, 0))

        button_row = tk.Frame(self.result_screen, bg=BG_COLOR)
        button_row.pack(fill="x", pady=(18, 0))
        button_row.grid_columnconfigure(0, weight=1)
        button_row.grid_columnconfigure(1, weight=1)

        self.next_button = tk.Label(
            button_row,
            font=PIXEL_FONT,
            bg=DIGIT_BG,
            fg=TEXT_PRIMARY,
            padx=12,
            pady=16,
            cursor="hand2",
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_COLOR,
            highlightthickness=2,
        )
        self.next_button.bind("<Button-1>", lambda _event: self.next_stage())
        self.next_button.bind("<Enter>", lambda _event: self.next_button.configure(highlightbackground=HOVER_BORDER, highlightcolor=HOVER_BORDER))
        self.next_button.bind("<Leave>", lambda _event: self.next_button.configure(highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR))
        self.next_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.reset_button = tk.Label(
            button_row,
            text="RESET",
            font=PIXEL_FONT,
            bg=RESET_BG,
            fg=TEXT_PRIMARY,
            padx=12,
            pady=16,
            cursor="hand2",
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_COLOR,
            highlightthickness=2,
        )
        self.reset_button.bind("<Button-1>", lambda _event: self.reset_all())
        self.reset_button.bind("<Enter>", lambda _event: self.reset_button.configure(highlightbackground=HOVER_BORDER, highlightcolor=HOVER_BORDER))
        self.reset_button.bind("<Leave>", lambda _event: self.reset_button.configure(highlightbackground=BORDER_COLOR, highlightcolor=BORDER_COLOR))
        self.reset_button.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def bind_keys(self):
        self.root.bind("<KeyPress>", self.on_keypress)
        self.root.bind("<Return>", self.on_confirm)
        self.root.bind("<space>", self.on_confirm)

    def on_keypress(self, event):
        key = event.keysym

        if key.lower() == "r":
            self.reset_all()
            return

        if self.stage_finished:
            return

        digit = None
        if key.isdigit():
            digit = key
        elif key.startswith("KP_") and key[-1].isdigit():
            digit = key[-1]

        if digit is not None:
            self.append_digit(digit)
            return

        if key in {"BackSpace", "Delete"}:
            self.delete_digit()

    def on_confirm(self, _event):
        if self.stage_finished:
            self.next_stage()

    def reset_all(self):
        self.stage = 1
        self.start_stage()

    def start_stage(self):
        self.questions_in_stage = QUESTIONS_PER_STAGE
        self.total_turns = self.questions_in_stage + self.stage
        self.turn_limit = max(2000, BASE_TURN_MS - (self.stage - 1) * 150)
        self.history = []
        self.turn_index = 0
        self.correct_answers = 0
        self.total_checks = 0
        self.turn_result = ""
        self.stage_cleared = False
        self.stage_finished = False
        self.input_text = ""
        self.current_problem = None
        self.expected_answer = None
        self.expected_text = ""
        self.turn_remaining = self.turn_limit
        self.prepare_turn()
        self.render()

    def generate_problem(self):
        op = random.choice(["+", "-"])

        if op == "+":
            answer = random.randint(0, 9)
            left = random.randint(0, answer)
            right = answer - left
        else:
            answer = random.randint(0, 9)
            right = random.randint(0, 9 - answer)
            left = answer + right

        return {"text": f"{left} {op} {right} =", "answer": answer}

    def prepare_turn(self):
        if self.turn_index >= self.total_turns:
            self.finish_stage()
            return

        self.input_text = ""
        self.turn_remaining = self.turn_limit

        if self.turn_index < self.questions_in_stage:
            self.current_problem = self.generate_problem()
            self.history.append(self.current_problem)
        else:
            self.current_problem = None

        answer_index = self.turn_index - self.stage
        if 0 <= answer_index < self.questions_in_stage:
            self.expected_answer = self.history[answer_index]["answer"]
            self.expected_text = str(self.expected_answer)
            self.turn_result = f"Answer {self.stage}-back"
        else:
            self.expected_answer = None
            self.expected_text = ""
            self.turn_result = "Warm-up turn"

        self.render()

    def submit_turn(self, is_correct):
        if self.expected_answer is not None:
            self.total_checks += 1
            if is_correct:
                self.correct_answers += 1
                self.turn_result = "Correct"
            else:
                self.turn_result = f"Time up  Ans:{self.expected_answer}"
        else:
            self.turn_result = "Memorize only"

        self.turn_index += 1
        self.prepare_turn()

    def register_wrong_input(self):
        self.turn_result = "Miss"
        self.input_text = ""
        self.turn_remaining = max(TICK_MS, self.turn_remaining - MISS_PENALTY_MS)
        self.render()

    def finish_stage(self):
        self.stage_finished = True
        accuracy = self.correct_answers / self.questions_in_stage
        self.stage_cleared = accuracy >= CLEAR_ACCURACY
        if self.stage_cleared:
            self.best_stage = max(self.best_stage, self.stage + 1)
        self.render()

    def next_stage(self):
        if not self.stage_finished:
            return
        if self.stage_cleared:
            self.stage += 1
        self.start_stage()

    def append_digit(self, digit):
        if self.stage_finished or self.expected_answer is None:
            return

        if len(self.input_text) < len(self.expected_text):
            self.input_text += digit
            self.check_auto_answer()
            self.render()

    def delete_digit(self):
        if self.stage_finished:
            return
        self.input_text = self.input_text[:-1]
        self.render()

    def skip_turn(self):
        if self.stage_finished:
            return

        if self.expected_answer is not None:
            self.total_checks += 1
            self.turn_result = f"Skip  Ans:{self.expected_answer}"
        else:
            self.turn_result = "Skip"
        self.turn_index += 1
        self.prepare_turn()

    def check_auto_answer(self):
        if not self.expected_text:
            return

        if not self.expected_text.startswith(self.input_text):
            self.register_wrong_input()
            return

        if self.input_text == self.expected_text:
            self.submit_turn(True)

    def handle_keypad(self, action):
        if self.stage_finished:
            return

        if action == "SKIP":
            self.skip_turn()
        elif action == "RESET":
            self.reset_all()
        else:
            self.append_digit(action)

    def tick(self):
        if not self.stage_finished:
            self.turn_remaining -= TICK_MS
            if self.turn_remaining <= 0:
                self.submit_turn(False)
            else:
                self.render()

        self.after_id = self.root.after(TICK_MS, self.tick)

    def render(self):
        self.title_var.set("ONI CALCULATION 6")
        self.stage_var.set(f"STAGE {self.stage}-BACK")
        self.best_var.set(f"BEST {self.best_stage}-BACK")
        self.turn_var.set(f"TURN {min(self.turn_index + 1, self.total_turns)}/{self.total_turns}")

        if self.total_checks > 0:
            accuracy = int(self.correct_answers * 100 / self.total_checks)
            self.acc_var.set(f"ACC {accuracy}%")
        else:
            self.acc_var.set("ACC --")

        if self.stage_finished:
            self.result_title_var.set(f"{self.stage}-BACK RESULT")
            self.result_score_var.set(f"Correct: {self.correct_answers}/{self.questions_in_stage}")
            self.result_accuracy_var.set(f"Accuracy: {int(self.correct_answers * 100 / self.questions_in_stage)}%")
            self.result_message_var.set("Clear! Next back unlocked" if self.stage_cleared else "Retry this back")
            self.next_button.configure(text="NEXT" if self.stage_cleared else "RETRY")
            self.next_button.configure(
                bg=DIGIT_BG if self.stage_cleared else SPECIAL_BG,
            )
            self.result_message_label.configure(fg=TEXT_GOOD if self.stage_cleared else TEXT_WARN)
            self.result_screen.tkraise()
            return

        self.problem_var.set(self.current_problem["text"] if self.current_problem is not None else "ANSWER")
        if self.expected_answer is None:
            self.instruction_var.set("Memorize this answer.")
        else:
            self.instruction_var.set(f"Type the answer from {self.stage}-back.")

        self.status_var.set(self.turn_result)
        if self.turn_result == "Correct":
            self.status_label.configure(fg=TEXT_GOOD)
        elif self.turn_result.startswith("Miss") or self.turn_result.startswith("Time up") or self.turn_result.startswith("Skip"):
            self.status_label.configure(fg=TEXT_WARN)
        else:
            self.status_label.configure(fg=TEXT_DIM)
        self.progress.configure(maximum=self.turn_limit, value=max(0, self.turn_remaining))
        self.play_screen.tkraise()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    OniCalculationTk().run()
