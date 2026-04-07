import random

import pyxel

WINDOW_WIDTH = 240
WINDOW_HEIGHT = 320
BASE_TURN_FRAMES = 165
CLEAR_ACCURACY = 0.8
MISS_PENALTY_FRAMES = 18
QUESTIONS_PER_STAGE = 20
KEYPAD_X = 19
KEYPAD_Y = 160
KEYPAD_W = 62
KEYPAD_H = 34
KEYPAD_GAP = 8
STATUS_X = 16
STATUS_Y = 142
STATUS_W = 208
STATUS_H = 12
STAGE_RESULT_X = 20
STAGE_RESULT_Y = 54
STAGE_RESULT_W = 200
STAGE_RESULT_H = 120
RESULT_BUTTON_Y = 200
RESULT_BUTTON_W = 92
RESULT_BUTTON_H = 28
RESULT_BUTTON_GAP = 16

KEY_KP_0 = getattr(pyxel, "KEY_KP_0", pyxel.KEY_0)
KEY_KP_1 = getattr(pyxel, "KEY_KP_1", pyxel.KEY_1)
KEY_KP_2 = getattr(pyxel, "KEY_KP_2", pyxel.KEY_2)
KEY_KP_3 = getattr(pyxel, "KEY_KP_3", pyxel.KEY_3)
KEY_KP_4 = getattr(pyxel, "KEY_KP_4", pyxel.KEY_4)
KEY_KP_5 = getattr(pyxel, "KEY_KP_5", pyxel.KEY_5)
KEY_KP_6 = getattr(pyxel, "KEY_KP_6", pyxel.KEY_6)
KEY_KP_7 = getattr(pyxel, "KEY_KP_7", pyxel.KEY_7)
KEY_KP_8 = getattr(pyxel, "KEY_KP_8", pyxel.KEY_8)
KEY_KP_9 = getattr(pyxel, "KEY_KP_9", pyxel.KEY_9)
KEY_DELETE = getattr(pyxel, "KEY_DELETE", pyxel.KEY_BACKSPACE)

DIGIT_KEYS = {
    pyxel.KEY_0: "0",
    pyxel.KEY_1: "1",
    pyxel.KEY_2: "2",
    pyxel.KEY_3: "3",
    pyxel.KEY_4: "4",
    pyxel.KEY_5: "5",
    pyxel.KEY_6: "6",
    pyxel.KEY_7: "7",
    pyxel.KEY_8: "8",
    pyxel.KEY_9: "9",
    KEY_KP_0: "0",
    KEY_KP_1: "1",
    KEY_KP_2: "2",
    KEY_KP_3: "3",
    KEY_KP_4: "4",
    KEY_KP_5: "5",
    KEY_KP_6: "6",
    KEY_KP_7: "7",
    KEY_KP_8: "8",
    KEY_KP_9: "9",
}

KEYPAD_LAYOUT = [
    ["7", "8", "9"],
    ["4", "5", "6"],
    ["1", "2", "3"],
    ["0", "SKIP", "RESET"],
]

MULTIPLICATION_FACTORS = [
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8), (1, 9),
    (2, 2), (2, 3), (2, 4),
    (3, 3),
]

BIG_FONT = {
    "0": ["11111", "10001", "10001", "10001", "11111"],
    "1": ["00100", "01100", "00100", "00100", "01110"],
    "2": ["11110", "00010", "11110", "10000", "11111"],
    "3": ["11110", "00010", "01110", "00010", "11110"],
    "4": ["10010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00010", "11110"],
    "6": ["01111", "10000", "11110", "10001", "01110"],
    "7": ["11111", "00010", "00100", "01000", "01000"],
    "8": ["01110", "10001", "01110", "10001", "01110"],
    "9": ["01110", "10001", "01111", "00001", "11110"],
    "E": ["11111", "10000", "11110", "10000", "11111"],
    "I": ["11111", "00100", "00100", "00100", "11111"],
    "K": ["10001", "10010", "11100", "10010", "10001"],
    "P": ["11110", "10001", "11110", "10000", "10000"],
    "+": ["00100", "00100", "11111", "00100", "00100"],
    "-": ["00000", "00000", "11111", "00000", "00000"],
    "*": ["10001", "01010", "00100", "01010", "10001"],
    "=": ["00000", "11111", "00000", "11111", "00000"],
    "_": ["00000", "00000", "00000", "00000", "11111"],
    "A": ["01110", "10001", "11111", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001"],
    "S": ["01111", "10000", "01110", "00001", "11110"],
    "W": ["10001", "10001", "10101", "11011", "10001"],
    "R": ["11110", "10001", "11110", "10010", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100"],
    " ": ["00000", "00000", "00000", "00000", "00000"],
}


class OniCalculationGame:
    def __init__(self):
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Pyxel Oni Calculation 6", fps=30)
        pyxel.mouse(True)
        self.best_stage = 1
        self.reset_all()
        pyxel.run(self.update, self.draw)

    def reset_all(self):
        self.stage = 1
        self.start_stage()

    def start_stage(self):
        self.questions_in_stage = QUESTIONS_PER_STAGE
        self.total_turns = self.questions_in_stage + self.stage
        self.turn_limit = max(60, BASE_TURN_FRAMES - (self.stage - 1) * 5)
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
        self.turn_timer = self.turn_limit
        self.prepare_turn()

    def generate_problem(self):
        op = random.choice(["+", "-"])

        if op == "+":
            answer = random.randint(0, 9)
            left = random.randint(0, answer)
            right = answer - left
        elif op == "-":
            answer = random.randint(0, 9)
            right = random.randint(0, 9 - answer)
            left = answer + right

        return {"text": f"{left} {op} {right} =", "answer": answer}

    def prepare_turn(self):
        if self.turn_index >= self.total_turns:
            self.finish_stage()
            return

        self.input_text = ""
        self.turn_timer = self.turn_limit

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
        self.turn_timer = max(1, self.turn_timer - MISS_PENALTY_FRAMES)

    def finish_stage(self):
        self.stage_finished = True
        accuracy = self.correct_answers / self.questions_in_stage
        self.stage_cleared = accuracy >= CLEAR_ACCURACY
        if self.stage_cleared:
            self.best_stage = max(self.best_stage, self.stage + 1)

    def next_stage(self):
        if self.stage_cleared:
            self.stage += 1
        self.start_stage()

    def append_digit(self, digit):
        if self.expected_answer is None:
            return

        if len(self.input_text) < len(self.expected_text):
            self.input_text += digit
            self.check_auto_answer()

    def delete_digit(self):
        self.input_text = self.input_text[:-1]

    def skip_turn(self):
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

    def handle_keyboard_input(self):
        for key, digit in DIGIT_KEYS.items():
            if pyxel.btnp(key):
                self.append_digit(digit)
                return

        if pyxel.btnp(pyxel.KEY_BACKSPACE) or pyxel.btnp(KEY_DELETE):
            self.delete_digit()

    def keypad_action_at(self, x, y):
        for row_index, row in enumerate(KEYPAD_LAYOUT):
            for col_index, label in enumerate(row):
                x0 = KEYPAD_X + col_index * (KEYPAD_W + KEYPAD_GAP)
                y0 = KEYPAD_Y + row_index * (KEYPAD_H + KEYPAD_GAP)
                if x0 <= x < x0 + KEYPAD_W and y0 <= y < y0 + KEYPAD_H:
                    return label
        return None

    def stage_result_action_at(self, x, y):
        labels = [self.stage_action_label(), "RESET"]
        start_x = (WINDOW_WIDTH - (RESULT_BUTTON_W * 2 + RESULT_BUTTON_GAP)) // 2

        for index, label in enumerate(labels):
            x0 = start_x + index * (RESULT_BUTTON_W + RESULT_BUTTON_GAP)
            if x0 <= x < x0 + RESULT_BUTTON_W and RESULT_BUTTON_Y <= y < RESULT_BUTTON_Y + RESULT_BUTTON_H:
                return label
        return None

    def handle_mouse_input(self):
        if not pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return

        action = self.keypad_action_at(pyxel.mouse_x, pyxel.mouse_y)
        if action is None:
            return

        if action == "SKIP":
            self.skip_turn()
        elif action == "RESET":
            self.reset_all()
        else:
            self.append_digit(action)

    def big_text_width(self, text, scale):
        char_width = 5 * scale
        gap = scale
        return len(text) * char_width + max(0, len(text) - 1) * gap

    def draw_big_text(self, x, y, text, color, scale):
        cursor_x = x
        for char in text:
            pattern = BIG_FONT.get(char, BIG_FONT[" "])
            for row_index, row in enumerate(pattern):
                for col_index, cell in enumerate(row):
                    if cell == "1":
                        px = cursor_x + col_index * scale
                        py = y + row_index * scale
                        pyxel.rect(px, py, scale, scale, color)
            cursor_x += 5 * scale + scale

    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_all()
            return

        if self.stage_finished:
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
                self.next_stage()
                return

            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                action = self.stage_result_action_at(pyxel.mouse_x, pyxel.mouse_y)
                if action == "RESET":
                    self.reset_all()
                    return
                if action == self.stage_action_label():
                    self.next_stage()
            return

        self.handle_keyboard_input()
        self.handle_mouse_input()

        if self.expected_answer is None:
            self.input_text = ""

        self.turn_timer -= 1
        if self.turn_timer <= 0:
            self.submit_turn(False)

    def draw_header(self):
        pyxel.text(12, 8, "ONI CALCULATION 6", 10)
        pyxel.text(12, 22, f"STAGE {self.stage}-BACK", 7)
        pyxel.text(132, 22, f"BEST {self.best_stage}-BACK", 6)
        pyxel.text(12, 34, f"TURN {min(self.turn_index + 1, self.total_turns)}/{self.total_turns}", 7)

        if self.total_checks > 0:
            accuracy = int(self.correct_answers * 100 / self.total_checks)
            pyxel.text(132, 34, f"ACC {accuracy}%", 11)
        else:
            pyxel.text(132, 34, "ACC --", 11)

    def draw_problem_area(self):
        pyxel.rect(16, 52, 208, 62, 1)
        pyxel.rectb(16, 52, 208, 62, 7)

        if self.current_problem is None:
            text = "ANSWER"
            scale = 3
            color = 10
            text_x = 120 - self.big_text_width(text, scale) // 2
            self.draw_big_text(text_x, 66, text, color, scale)
        else:
            text = self.current_problem["text"]
            scale = 2
            text_x = 120 - self.big_text_width(text, scale) // 2
            self.draw_big_text(text_x, 64, text, 7, scale)

        bar_w = int(196 * self.turn_timer / self.turn_limit)
        pyxel.rect(22, 102, 196, 6, 5)
        pyxel.rect(22, 102, bar_w, 6, 11 if self.turn_timer > 30 else 8)

    def draw_input_area(self):
        pyxel.rect(16, 122, 208, 18, 0)
        pyxel.rectb(16, 122, 208, 18, 13)

        if self.expected_answer is None:
            pyxel.text(28, 128, "Memorize this answer.", 6)
            return

        pyxel.text(28, 128, f"Type the answer from {self.stage}-back.", 7)

    def draw_keypad(self):
        for row_index, row in enumerate(KEYPAD_LAYOUT):
            for col_index, label in enumerate(row):
                x = KEYPAD_X + col_index * (KEYPAD_W + KEYPAD_GAP)
                y = KEYPAD_Y + row_index * (KEYPAD_H + KEYPAD_GAP)
                hovered = x <= pyxel.mouse_x < x + KEYPAD_W and y <= pyxel.mouse_y < y + KEYPAD_H
                fill = 5 if label.isdigit() else 2
                border = 10 if hovered else 7
                pyxel.rect(x, y, KEYPAD_W, KEYPAD_H, fill)
                pyxel.rectb(x, y, KEYPAD_W, KEYPAD_H, border)
                scale = 2 if label.isdigit() else 1
                text_w = self.big_text_width(label, scale)
                text_x = x + (KEYPAD_W - text_w) // 2
                text_y = y + (KEYPAD_H - 5 * scale) // 2
                self.draw_big_text(text_x, text_y, label, 7, scale)

    def draw_footer(self):
        color = 9 if self.turn_result == "Correct" else 8 if self.turn_result.startswith("Miss") or self.turn_result.startswith("Time up") else 6
        pyxel.rect(STATUS_X, STATUS_Y, STATUS_W, STATUS_H, 1)
        pyxel.rectb(STATUS_X, STATUS_Y, STATUS_W, STATUS_H, 13)
        pyxel.text(STATUS_X + 6, STATUS_Y + 3, self.turn_result, color)

    def stage_action_label(self):
        if self.stage_cleared:
            return "NEXT"
        return "RETRY"

    def draw_stage_result(self):
        box_x = STAGE_RESULT_X
        box_y = STAGE_RESULT_Y
        box_w = STAGE_RESULT_W
        box_h = STAGE_RESULT_H

        pyxel.rect(box_x, box_y, box_w, box_h, 0)
        pyxel.rectb(box_x, box_y, box_w, box_h, 11 if self.stage_cleared else 8)
        accuracy = int(self.correct_answers * 100 / self.questions_in_stage)
        pyxel.text(box_x + 53, box_y + 14, f"{self.stage}-BACK RESULT", 7)
        pyxel.text(box_x + 32, box_y + 38, f"CORRECT {self.correct_answers}/{self.questions_in_stage}", 7)
        pyxel.text(box_x + 32, box_y + 52, f"ACCURACY {accuracy}%", 7)

        if self.stage_cleared:
            pyxel.text(box_x + 24, box_y + 70, "CLEAR! NEXT BACK", 11)
            pyxel.text(box_x + 36, box_y + 80, "UNLOCKED", 11)
        else:
            pyxel.text(box_x + 45, box_y + 75, "RETRY THIS BACK", 8)

        pyxel.text(box_x + 24, box_y + 100, "ENTER/SPACE OR BUTTON", 6)

    def draw_stage_actions(self):
        labels = [self.stage_action_label(), "RESET"]
        start_x = (WINDOW_WIDTH - (RESULT_BUTTON_W * 2 + RESULT_BUTTON_GAP)) // 2

        for index, label in enumerate(labels):
            x = start_x + index * (RESULT_BUTTON_W + RESULT_BUTTON_GAP)
            hovered = x <= pyxel.mouse_x < x + RESULT_BUTTON_W and RESULT_BUTTON_Y <= pyxel.mouse_y < RESULT_BUTTON_Y + RESULT_BUTTON_H
            fill = 5 if label == "NEXT" else 2
            border = 10 if hovered else 7
            pyxel.rect(x, RESULT_BUTTON_Y, RESULT_BUTTON_W, RESULT_BUTTON_H, fill)
            pyxel.rectb(x, RESULT_BUTTON_Y, RESULT_BUTTON_W, RESULT_BUTTON_H, border)
            text_x = x + (RESULT_BUTTON_W - len(label) * 4) // 2
            pyxel.text(text_x, RESULT_BUTTON_Y + 10, label, 7)

    def draw(self):
        pyxel.cls(0)
        self.draw_header()

        if self.stage_finished:
            self.draw_stage_result()
            self.draw_stage_actions()
            return

        self.draw_problem_area()
        self.draw_input_area()
        self.draw_footer()
        self.draw_keypad()


OniCalculationGame()
