import random

import pyxel

WINDOW_WIDTH = 220
WINDOW_HEIGHT = 300
BASE_TURN_FRAMES = 105
CLEAR_ACCURACY = 0.8
MISS_PENALTY_FRAMES = 18
KEYPAD_X = 19
KEYPAD_Y = 168
KEYPAD_W = 54
KEYPAD_H = 24
KEYPAD_GAP = 10

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
    ["0", "DEL", "RESET"],
]


class OniCalculationGame:
    def __init__(self):
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Pyxel Oni Calculation 3", fps=30)
        pyxel.mouse(True)
        self.best_stage = 1
        self.reset_all()
        pyxel.run(self.update, self.draw)

    def reset_all(self):
        self.stage = 1
        self.start_stage()

    def start_stage(self):
        self.questions_in_stage = max(12, self.stage + 8)
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
        if self.stage <= 2:
            operators = ["+", "-"]
        else:
            operators = ["+", "-", "*"]

        op = random.choice(operators)

        if op == "+":
            limit = min(9 + self.stage * 2, 25)
            left = random.randint(1, limit)
            right = random.randint(1, limit)
            answer = left + right
        elif op == "-":
            limit = min(9 + self.stage * 2, 25)
            left = random.randint(1, limit)
            right = random.randint(1, left)
            answer = left - right
        else:
            left = random.randint(2, min(9, 3 + self.stage))
            right = random.randint(2, min(9, 2 + self.stage))
            answer = left * right

        return {"text": f"{left} {op} {right} = ?", "answer": answer}

    def prepare_turn(self):
        if self.turn_index >= self.questions_in_stage:
            self.finish_stage()
            return

        self.current_problem = self.generate_problem()
        self.history.append(self.current_problem)
        self.input_text = ""
        self.turn_timer = self.turn_limit

        if self.turn_index >= self.stage:
            self.expected_answer = self.history[self.turn_index - self.stage]["answer"]
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
        accuracy = 1.0 if self.total_checks == 0 else self.correct_answers / self.total_checks
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
                if label is None:
                    continue

                px = KEYPAD_X + col_index * (KEYPAD_W + KEYPAD_GAP)
                py = KEYPAD_Y + row_index * (KEYPAD_H + KEYPAD_GAP)
                if px <= x < px + KEYPAD_W and py <= y < py + KEYPAD_H:
                    return label
        return None

    def handle_mouse_input(self):
        if not pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return

        action = self.keypad_action_at(pyxel.mouse_x, pyxel.mouse_y)
        if action is None:
            return

        if action == "DEL":
            self.delete_digit()
        elif action == "RESET":
            self.reset_all()
        else:
            self.append_digit(action)

    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_all()
            return

        if self.stage_finished:
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
                self.next_stage()
                return

            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                action = self.keypad_action_at(pyxel.mouse_x, pyxel.mouse_y)
                if action == "RESET":
                    self.reset_all()
                    return
                if action in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "DEL"}:
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
        pyxel.text(10, 8, "ONI CALCULATION 3", 10)
        pyxel.text(10, 22, f"STAGE {self.stage}-BACK", 7)
        pyxel.text(118, 22, f"BEST {self.best_stage}-BACK", 6)
        pyxel.text(10, 34, f"TURN {min(self.turn_index + 1, self.questions_in_stage)}/{self.questions_in_stage}", 7)

        if self.total_checks > 0:
            accuracy = int(self.correct_answers * 100 / self.total_checks)
            pyxel.text(118, 34, f"ACC {accuracy}%", 11)
        else:
            pyxel.text(118, 34, "ACC --", 11)

    def draw_problem_area(self):
        pyxel.rect(16, 52, 188, 48, 1)
        pyxel.rectb(16, 52, 188, 48, 7)
        pyxel.text(34, 66, self.current_problem["text"], 7)

        bar_w = int(180 * self.turn_timer / self.turn_limit)
        pyxel.rect(20, 88, 180, 6, 5)
        pyxel.rect(20, 88, bar_w, 6, 11 if self.turn_timer > 30 else 8)

    def draw_input_area(self):
        pyxel.rect(16, 110, 188, 44, 0)
        pyxel.rectb(16, 110, 188, 44, 13)

        if self.expected_answer is None:
            pyxel.text(28, 124, "Memorize this answer.", 6)
            pyxel.text(28, 136, "Input starts after warm-up.", 5)
            return

        pyxel.text(28, 118, f"Type the answer from {self.stage}-back.", 7)
        pyxel.text(28, 134, "INPUT:", 10)
        pyxel.rect(72, 130, 42, 14, 1)
        pyxel.rectb(72, 130, 42, 14, 7)
        pyxel.text(78, 135, self.input_text or "_", 7)
        pyxel.text(126, 134, "KEYBOARD / CLICK", 6)

    def draw_keypad(self):
        for row_index, row in enumerate(KEYPAD_LAYOUT):
            for col_index, label in enumerate(row):
                if label is None:
                    continue

                x = KEYPAD_X + col_index * (KEYPAD_W + KEYPAD_GAP)
                y = KEYPAD_Y + row_index * (KEYPAD_H + KEYPAD_GAP)
                hovered = x <= pyxel.mouse_x < x + KEYPAD_W and y <= pyxel.mouse_y < y + KEYPAD_H
                fill = 5 if label.isdigit() else 2
                border = 10 if hovered else 7
                pyxel.rect(x, y, KEYPAD_W, KEYPAD_H, fill)
                pyxel.rectb(x, y, KEYPAD_W, KEYPAD_H, border)
                text_x = x + (KEYPAD_W // 2) - len(label) * 2
                pyxel.text(text_x, y + 9, label, 7)

    def draw_footer(self):
        color = 9 if self.turn_result == "Correct" else 8 if self.turn_result.startswith("Miss") or self.turn_result.startswith("Time up") else 6
        pyxel.text(18, 158, self.turn_result, color)
        pyxel.text(18, 286, "R: RESET  WRONG INPUT CLEARS AND COSTS TIME", 5)

    def draw_stage_result(self):
        pyxel.rect(18, 70, 184, 92, 0)
        pyxel.rectb(18, 70, 184, 92, 11 if self.stage_cleared else 8)
        accuracy = 100 if self.total_checks == 0 else int(self.correct_answers * 100 / self.total_checks)
        pyxel.text(72, 84, f"{self.stage}-BACK RESULT", 7)
        pyxel.text(50, 106, f"CORRECT {self.correct_answers}/{self.total_checks}", 7)
        pyxel.text(50, 120, f"ACCURACY {accuracy}%", 7)

        if self.stage_cleared:
            pyxel.text(50, 136, "CLEAR! NEXT BACK UNLOCKED", 11)
        else:
            pyxel.text(50, 136, "RETRY THIS BACK", 8)

        pyxel.text(34, 148, "ENTER, SPACE OR CLICK KEYPAD", 6)

    def draw(self):
        pyxel.cls(0)
        self.draw_header()

        if self.stage_finished:
            self.draw_stage_result()
            self.draw_keypad()
            pyxel.text(18, 286, "CLICK ANY KEY TO CONTINUE / RESET TO RESTART", 5)
            return

        self.draw_problem_area()
        self.draw_input_area()
        self.draw_footer()
        self.draw_keypad()


OniCalculationGame()
