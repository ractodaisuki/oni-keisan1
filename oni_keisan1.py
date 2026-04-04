import random

import pyxel

WINDOW_WIDTH = 240
WINDOW_HEIGHT = 180
BASE_TURN_FRAMES = 105
CLEAR_ACCURACY = 0.8

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
KEY_KP_ENTER = getattr(pyxel, "KEY_KP_ENTER", pyxel.KEY_RETURN)
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


class OniCalculationGame:
    def __init__(self):
        pyxel.init(WINDOW_WIDTH, WINDOW_HEIGHT, title="Pyxel Oni Calculation", fps=30)
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

        return {
            "text": f"{left} {op} {right} = ?",
            "answer": answer,
        }

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
            self.turn_result = f"Answer {self.stage}-back"
        else:
            self.expected_answer = None
            self.turn_result = "Warm-up turn"

    def submit_turn(self):
        if self.expected_answer is not None:
            self.total_checks += 1
            if self.input_text == str(self.expected_answer):
                self.correct_answers += 1
                self.turn_result = "Correct"
            else:
                expected = self.expected_answer
                self.turn_result = f"Miss  Ans:{expected}"
        else:
            self.turn_result = "Memorize only"

        self.turn_index += 1
        self.prepare_turn()

    def finish_stage(self):
        self.stage_finished = True
        if self.total_checks == 0:
            accuracy = 1.0
        else:
            accuracy = self.correct_answers / self.total_checks
        self.stage_cleared = accuracy >= CLEAR_ACCURACY
        if self.stage_cleared:
            self.best_stage = max(self.best_stage, self.stage + 1)

    def next_stage(self):
        if self.stage_cleared:
            self.stage += 1
        self.start_stage()

    def handle_number_input(self):
        for key, digit in DIGIT_KEYS.items():
            if pyxel.btnp(key):
                if len(self.input_text) < 3:
                    if self.input_text == "0":
                        self.input_text = digit
                    else:
                        self.input_text += digit
                return

        if pyxel.btnp(pyxel.KEY_BACKSPACE) or pyxel.btnp(KEY_DELETE):
            self.input_text = self.input_text[:-1]

    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_all()
            return

        if self.stage_finished:
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(KEY_KP_ENTER) or pyxel.btnp(pyxel.KEY_SPACE):
                self.next_stage()
            return

        self.handle_number_input()

        if self.expected_answer is None:
            self.input_text = ""

        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(KEY_KP_ENTER) or pyxel.btnp(pyxel.KEY_SPACE):
            self.submit_turn()
            return

        self.turn_timer -= 1
        if self.turn_timer <= 0:
            self.submit_turn()

    def draw_header(self):
        pyxel.text(10, 8, "ONI CALCULATION", 10)
        pyxel.text(10, 18, f"STAGE {self.stage}-BACK", 7)
        pyxel.text(118, 18, f"BEST {self.best_stage}-BACK", 6)
        pyxel.text(10, 28, f"TURN {min(self.turn_index + 1, self.questions_in_stage)}/{self.questions_in_stage}", 7)

        if self.total_checks > 0:
            accuracy = int(self.correct_answers * 100 / self.total_checks)
            pyxel.text(118, 28, f"ACC {accuracy}%", 11)
        else:
            pyxel.text(118, 28, "ACC --", 11)

    def draw_problem_area(self):
        pyxel.rect(18, 44, 204, 42, 1)
        pyxel.rectb(18, 44, 204, 42, 7)
        pyxel.text(29, 54, self.current_problem["text"], 7)

        bar_w = int(196 * self.turn_timer / self.turn_limit)
        pyxel.rect(22, 74, 196, 6, 5)
        pyxel.rect(22, 74, bar_w, 6, 11 if self.turn_timer > 30 else 8)

    def draw_input_area(self):
        pyxel.rect(18, 96, 204, 44, 0)
        pyxel.rectb(18, 96, 204, 44, 13)

        if self.expected_answer is None:
            pyxel.text(28, 108, "Memorize this answer.", 6)
            pyxel.text(28, 120, "Input starts after warm-up.", 5)
            return

        pyxel.text(28, 104, f"Type the answer from {self.stage}-back.", 7)
        pyxel.text(28, 118, "INPUT:", 10)
        pyxel.rect(72, 114, 42, 14, 1)
        pyxel.rectb(72, 114, 42, 14, 7)
        pyxel.text(78, 119, self.input_text or "_", 7)
        pyxel.text(130, 118, "ENTER/SPACE: SUBMIT", 6)

    def draw_footer(self):
        pyxel.text(18, 148, self.turn_result, 9 if self.turn_result == "Correct" else 8 if "Miss" in self.turn_result else 6)
        pyxel.text(18, 160, "0-9: INPUT  BACKSPACE: DELETE  R: RESET", 5)

    def draw_stage_result(self):
        pyxel.rect(28, 52, 184, 76, 0)
        pyxel.rectb(28, 52, 184, 76, 11 if self.stage_cleared else 8)
        accuracy = 100 if self.total_checks == 0 else int(self.correct_answers * 100 / self.total_checks)
        pyxel.text(84, 64, f"{self.stage}-BACK RESULT", 7)
        pyxel.text(60, 82, f"CORRECT {self.correct_answers}/{self.total_checks}", 7)
        pyxel.text(60, 94, f"ACCURACY {accuracy}%", 7)

        if self.stage_cleared:
            pyxel.text(60, 108, "CLEAR! NEXT BACK UNLOCKED", 11)
        else:
            pyxel.text(60, 108, "RETRY THIS BACK", 8)

        pyxel.text(44, 118, "PRESS ENTER OR SPACE", 6)

    def draw(self):
        pyxel.cls(0)
        self.draw_header()

        if self.stage_finished:
            self.draw_stage_result()
            pyxel.text(18, 150, "Rule: answer the value from N turns earlier.", 6)
            pyxel.text(18, 160, "R resets to 1-back.", 5)
            return

        self.draw_problem_area()
        self.draw_input_area()
        self.draw_footer()


OniCalculationGame()
