import customtkinter
import tkinter as tk
import threading
import time
import os
import random
import game_logic

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class WordGameApp(customtkinter.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings = game_logic.load_settings()
        customtkinter.set_appearance_mode(self.settings["appearance_mode"])
        
        self.title("言葉当てゲーム"); self.geometry("600x750"); self.minsize(500, 700)
        self.title_font = ("Helvetica", 36, "bold"); self.info_font = ("Helvetica", 18)
        self.button_font = ("Helvetica", 18); self.game_font = ("Helvetica", 14)
        self.result_font = ("Helvetica", 24, "bold"); self.value_font = ("Courier", 18, "bold")

        self.protocol("WM_DELETE_WINDOW", self.ask_quit)

        container = customtkinter.CTkFrame(self); container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1); container.grid_columnconfigure(0, weight=1)
        self.frames = {}
        for F in (LoadingPage, StartPage, GamePage, SettingsPage, CustomModePage):
            frame = F(container, self); self.frames[F] = frame; frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(LoadingPage); self.start_loading()

    def show_frame(self, page_class):
        if page_class == LoadingPage: self.frames[LoadingPage].start_hit_and_blow()
        if page_class == SettingsPage: self.frames[SettingsPage].refresh_settings()
        frame = self.frames[page_class]; frame.tkraise()

    def ask_quit(self):
        if messagebox.askyesno("終了確認", "本当にアプリケーションを終了しますか？"):
            self.destroy()

    def save_and_apply_settings(self, new_settings):
        self.settings = new_settings; game_logic.save_settings(self.settings)
        customtkinter.set_appearance_mode(self.settings["appearance_mode"])

    def start_loading(self):
        self.loading_thread = threading.Thread(target=self.load_data_in_background, daemon=True)
        self.loading_thread.start()
        self.check_loading_status()

    def load_data_in_background(self):
        # MODEL_FILE_NAME = "jawiki.entity_vectors.300d.txt"
        MODEL_FILE_NAME = "cc.ja.300.vec"
        model_path = os.path.join("model", MODEL_FILE_NAME)
        game_logic.load_model(model_path); self.easy_data = game_logic.load_json_data("data/easy_data.json")
        self.normal_data = game_logic.load_json_data("data/normal_data.json"); self.hard_data = game_logic.load_json_data("data/hard_data.json")

    def check_loading_status(self):
        if self.loading_thread.is_alive(): self.after(100, self.check_loading_status)
        else: self.frames[LoadingPage].on_loading_complete()

    def start_game(self, difficulty):
        # ▼▼▼ カスタムモードのリプレイに対応 ▼▼▼
        if difficulty == "custom":
            # "custom"が指定されたら、カスタムゲーム開始処理に丸投げする
            self.start_custom_game(self.last_custom_time, self.last_custom_keyword)
            return
            
        self.current_difficulty = difficulty
        time_limit = self.settings["time_limits"][difficulty]
        question, genre = game_logic.generate_question_by_difficulty(difficulty, self.easy_data, self.normal_data, self.hard_data)
        if not question: return
        game_frame = self.frames[GamePage]
        game_frame.setup_new_game(question, genre, time_limit, self.settings.copy())
        self.show_frame(GamePage)

    def start_custom_game(self, time_limit, keyword):
        # ▼▼▼ カスタム設定を記憶 ▼▼▼
        self.current_difficulty = "custom"
        self.last_custom_time = time_limit
        self.last_custom_keyword = keyword
        
        question = game_logic.generate_custom_question(keyword)
        if not question:
            custom_frame = self.frames[CustomModePage]
            custom_frame.show_error("お題を生成できませんでした。\nキーワードが存在しないか、候補が見つかりません。")
            return
        genre = f"カスタム:「{keyword}」"
        game_frame = self.frames[GamePage]
        game_frame.setup_new_game(question, genre, time_limit, self.settings.copy())
        self.show_frame(GamePage)

# (LoadingPage, StartPage, SettingsPage, GamePageのクラス定義は変更なし。長いので省略)
class LoadingPage(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller; self.answer = ""; self.guesses = 0; self.grid_columnconfigure(0, weight=1)
        top_frame = customtkinter.CTkFrame(self, fg_color="transparent"); top_frame.grid(row=0, column=0, pady=10, padx=20, sticky="ew")
        self.loading_label = customtkinter.CTkLabel(top_frame, text="ゲームの準備をしています...", font=controller.info_font); self.loading_label.pack(side="left")
        self.progress_bar = customtkinter.CTkProgressBar(top_frame, mode='indeterminate'); self.progress_bar.pack(side="right", padx=10, fill='x', expand=True)
        game_frame = customtkinter.CTkFrame(self); game_frame.grid(row=1, column=0, pady=10, padx=20, sticky="nsew")
        game_frame.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        customtkinter.CTkLabel(game_frame, text="ヒット & ブロー", font=controller.title_font).grid(row=0, column=0, columnspan=2, pady=10)
        customtkinter.CTkLabel(game_frame, text="4桁の重複しない数字を当てよう！", font=controller.info_font).grid(row=1, column=0, columnspan=2, pady=5)
        self.entry = customtkinter.CTkEntry(game_frame, width=150, font=("Courier", 24, "bold"), justify='center'); self.entry.grid(row=2, column=0, pady=10)
        self.button = customtkinter.CTkButton(game_frame, text="推測", command=self.make_a_guess, font=controller.button_font); self.button.grid(row=2, column=1, pady=10)
        self.entry.bind("<Return>", self.make_a_guess)
        self.feedback_label = customtkinter.CTkLabel(game_frame, text="", font=controller.game_font); self.feedback_label.grid(row=3, column=0, columnspan=2)
        self.history_text = customtkinter.CTkTextbox(game_frame, font=("Courier", 16), height=200); self.history_text.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10, padx=10); self.history_text.configure(state='disabled')
        self.start_button = customtkinter.CTkButton(self, text="タイトルへ", font=controller.button_font, command=lambda: controller.show_frame(StartPage))
    def start_hit_and_blow(self):
        self.progress_bar.start(); self.answer = "".join(random.sample("0123456789", 4)); self.guesses = 0
        print(f"ヒットアンドブローの答え: {self.answer}"); self.feedback_label.configure(text="")
        for widget in [self.entry, self.button]: widget.configure(state='normal')
        self.history_text.configure(state='normal'); self.history_text.delete('1.0', 'end'); self.history_text.configure(state='disabled')
        self.start_button.grid_forget()
    def make_a_guess(self, event=None):
        guess = self.entry.get().strip()
        if not guess.isdigit() or len(guess) != 4 or len(set(guess)) != 4: self.feedback_label.configure(text="重複しない4桁の数字を入力してください", text_color="orange"); return
        self.guesses += 1; hits = sum(1 for i in range(4) if self.answer[i] == guess[i]); blows = sum(1 for digit in guess if digit in self.answer) - hits
        self.history_text.configure(state='normal'); self.history_text.insert('end', f"{self.guesses}回目: {guess}  ->  {hits} Hit, {blows} Blow\n")
        self.history_text.configure(state='disabled'); self.entry.delete(0, 'end')
        if hits == 4: self.feedback_label.configure(text=f"正解！ {self.guesses}回でクリアしました！", text_color="green"); [w.configure(state='disabled') for w in [self.entry, self.button]]
        else: self.feedback_label.configure(text="")
    def on_loading_complete(self):
        self.progress_bar.stop(); self.progress_bar.grid_forget()
        self.loading_label.configure(text="準備が完了しました！");
        for widget in [self.entry, self.button]: widget.configure(state='disabled')
        self.start_button.grid(row=2, column=0, columnspan=2, pady=20, ipadx=20, ipady=10)
class StartPage(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        customtkinter.CTkLabel(self, text="言葉当てゲーム", font=controller.title_font).pack(pady=40)
        customtkinter.CTkLabel(self, text="難易度を選択してください", font=controller.info_font).pack(pady=10)
        mode_frame = customtkinter.CTkFrame(self, fg_color="transparent"); mode_frame.pack(pady=10)
        customtkinter.CTkButton(mode_frame, text="かんたん", font=controller.button_font, command=lambda: controller.start_game("1")).pack(pady=10, ipadx=20, ipady=5)
        customtkinter.CTkButton(mode_frame, text="普通", font=controller.button_font, command=lambda: controller.start_game("2")).pack(pady=10, ipadx=20, ipady=5)
        customtkinter.CTkButton(mode_frame, text="むずかしい", font=controller.button_font, command=lambda: controller.start_game("3")).pack(pady=10, ipadx=20, ipady=5)
        customtkinter.CTkButton(mode_frame, text="カスタムモード", font=controller.button_font, fg_color="#334155", hover_color="#475569", command=lambda: controller.show_frame(CustomModePage)).pack(pady=10, ipadx=20, ipady=5)
        bottom_frame = customtkinter.CTkFrame(self, fg_color="transparent"); bottom_frame.pack(pady=40, fill="x", expand=True)
        customtkinter.CTkButton(bottom_frame, text="設定", font=controller.info_font, command=lambda: controller.show_frame(SettingsPage)).pack(side="left", padx=50)
        customtkinter.CTkButton(bottom_frame, text="終了", font=controller.info_font, fg_color="#c026d3", hover_color="#a21caf", command=controller.ask_quit).pack(side="right", padx=50)
class SettingsPage(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller
        self.vars = {"appearance_mode": tk.StringVar(), "time_easy": tk.IntVar(), "time_normal": tk.IntVar(), "time_hard": tk.IntVar(), "ranking_count": tk.IntVar(), "show_similarity": tk.BooleanVar()}
        self.grid_columnconfigure(1, weight=1)
        customtkinter.CTkLabel(self, text="設定", font=controller.title_font).grid(row=0, column=0, columnspan=3, pady=20, padx=20)
        customtkinter.CTkLabel(self, text="GUIの明るさ:").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        customtkinter.CTkOptionMenu(self, values=["Light", "Dark", "System"], variable=self.vars["appearance_mode"]).grid(row=1, column=1, columnspan=2, padx=20, pady=10, sticky="w")
        customtkinter.CTkLabel(self, text="制限時間 (秒):").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.time_easy_label = customtkinter.CTkLabel(self, text="", font=controller.value_font); customtkinter.CTkLabel(self, text="かんたん", font=controller.info_font).grid(row=3, column=0, padx=40, sticky="w")
        customtkinter.CTkSlider(self, from_=10, to=600, variable=self.vars["time_easy"], command=lambda v: self.time_easy_label.configure(text=int(v))).grid(row=3, column=1, padx=20, pady=10, sticky="ew"); self.time_easy_label.grid(row=3, column=2, padx=20)
        self.time_normal_label = customtkinter.CTkLabel(self, text="", font=controller.value_font); customtkinter.CTkLabel(self, text="普通", font=controller.info_font).grid(row=4, column=0, padx=40, sticky="w")
        customtkinter.CTkSlider(self, from_=10, to=600, variable=self.vars["time_normal"], command=lambda v: self.time_normal_label.configure(text=int(v))).grid(row=4, column=1, padx=20, pady=10, sticky="ew"); self.time_normal_label.grid(row=4, column=2, padx=20)
        self.time_hard_label = customtkinter.CTkLabel(self, text="", font=controller.value_font); customtkinter.CTkLabel(self, text="むずかしい", font=controller.info_font).grid(row=5, column=0, padx=40, sticky="w")
        customtkinter.CTkSlider(self, from_=10, to=600, variable=self.vars["time_hard"], command=lambda v: self.time_hard_label.configure(text=int(v))).grid(row=5, column=1, padx=20, pady=10, sticky="ew"); self.time_hard_label.grid(row=5, column=2, padx=20)
        self.ranking_count_label = customtkinter.CTkLabel(self, text="", font=controller.value_font); customtkinter.CTkLabel(self, text="ランキング表示項目数:", font=controller.info_font).grid(row=6, column=0, padx=20, pady=10, sticky="w")
        customtkinter.CTkSlider(self, from_=0, to=20, number_of_steps=21, variable=self.vars["ranking_count"], command=lambda v: self.ranking_count_label.configure(text=int(v))).grid(row=6, column=1, padx=20, pady=10, sticky="ew"); self.ranking_count_label.grid(row=6, column=2, padx=20)
        customtkinter.CTkCheckBox(self, text="ランキングに一致度を表示する", variable=self.vars["show_similarity"], font=controller.info_font).grid(row=7, column=0, columnspan=3, padx=20, pady=20)
        customtkinter.CTkButton(self, text="保存して戻る", font=controller.button_font, command=self.save_and_exit).grid(row=8, column=0, columnspan=3, pady=20, ipadx=10, ipady=10)
    def refresh_settings(self):
        s = self.controller.settings; self.vars["appearance_mode"].set(s["appearance_mode"])
        self.vars["time_easy"].set(s["time_limits"]["1"]); self.time_easy_label.configure(text=s["time_limits"]["1"])
        self.vars["time_normal"].set(s["time_limits"]["2"]); self.time_normal_label.configure(text=s["time_limits"]["2"])
        self.vars["time_hard"].set(s["time_limits"]["3"]); self.time_hard_label.configure(text=s["time_limits"]["3"])
        self.vars["ranking_count"].set(s["ranking_display_count"]); self.ranking_count_label.configure(text=s["ranking_display_count"])
        self.vars["show_similarity"].set(s["show_similarity"])
    def save_and_exit(self):
        new_s = {"appearance_mode": self.vars["appearance_mode"].get(), "bgm_volume": self.controller.settings["bgm_volume"], "se_volume": self.controller.settings["se_volume"],
                 "time_limits": {"1": self.vars["time_easy"].get(), "2": self.vars["time_normal"].get(), "3": self.vars["time_hard"].get()},
                 "ranking_display_count": self.vars["ranking_count"].get(), "show_similarity": self.vars["show_similarity"].get()}
        self.controller.save_and_apply_settings(new_s); self.controller.show_frame(StartPage)
class CustomModePage(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller; self.grid_columnconfigure(0, weight=1); self.time_var = tk.IntVar(value=300)
        customtkinter.CTkLabel(self, text="カスタムモード", font=controller.title_font).grid(row=0, column=0, columnspan=2, pady=20, padx=20)
        customtkinter.CTkLabel(self, text="ジャンルのキーワード:", font=controller.info_font).grid(row=1, column=0, columnspan=2, padx=20, pady=(20, 5), sticky="w")
        self.keyword_entry = customtkinter.CTkEntry(self, font=controller.info_font, placeholder_text="例: 果物"); self.keyword_entry.grid(row=2, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        customtkinter.CTkLabel(self, text="制限時間 (秒):", font=controller.info_font).grid(row=3, column=0, padx=20, pady=(20, 5), sticky="w")
        self.time_label = customtkinter.CTkLabel(self, text=self.time_var.get(), font=controller.value_font); self.time_label.grid(row=3, column=1, padx=20, sticky="e")
        customtkinter.CTkSlider(self, from_=10, to=600, variable=self.time_var, command=lambda v: self.time_label.configure(text=int(v))).grid(row=4, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        self.error_label = customtkinter.CTkLabel(self, text="", text_color="red", font=controller.game_font); self.error_label.grid(row=5, column=0, columnspan=2, pady=10)
        button_frame = customtkinter.CTkFrame(self, fg_color="transparent"); button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        customtkinter.CTkButton(button_frame, text="この設定でゲーム開始", font=controller.button_font, command=self.validate_and_start).pack(side="left", padx=10, ipadx=10, ipady=10)
        customtkinter.CTkButton(button_frame, text="タイトルに戻る", font=controller.info_font, command=lambda: controller.show_frame(StartPage)).pack(side="right", padx=10)
    def validate_and_start(self):
        keyword = self.keyword_entry.get().strip(); time_limit = self.time_var.get()
        if not keyword: self.show_error("キーワードを入力してください。"); return
        self.error_label.configure(text="お題を生成中..."); self.controller.start_custom_game(time_limit, keyword)
    def show_error(self, message): self.error_label.configure(text=message)
class GamePage(customtkinter.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent); self.controller = controller; self.after_id = None; self.grid_columnconfigure((0, 1), weight=1); self.grid_rowconfigure(4, weight=1)
        self.genre_label = customtkinter.CTkLabel(self, text="", font=controller.info_font); self.timer_label = customtkinter.CTkLabel(self, text="", font=controller.info_font)
        self.guess_entry = customtkinter.CTkEntry(self, font=controller.button_font); self.guess_button = customtkinter.CTkButton(self, text="推測！", font=controller.button_font, command=self.make_a_guess)
        self.feedback_label = customtkinter.CTkLabel(self, text="", font=controller.game_font, wraplength=500); self.ranking_title_label = customtkinter.CTkLabel(self, text="--- 推測単語ランキング ---", font=controller.info_font)
        self.ranking_text = customtkinter.CTkTextbox(self, font=controller.game_font); self.giveup_button = customtkinter.CTkButton(self, text="ギブアップ", font=controller.button_font, command=self.give_up)
        self.game_over_frame = customtkinter.CTkFrame(self)
        self.replay_button = customtkinter.CTkButton(self.game_over_frame, text="もう一回遊ぶ", font=controller.button_font, command=lambda: controller.start_game(controller.current_difficulty))
        self.back_to_title_button = customtkinter.CTkButton(self.game_over_frame, text="タイトルに戻る", font=controller.button_font, command=lambda: controller.show_frame(StartPage))
        self.replay_button.pack(side="left", padx=10, pady=10, ipadx=10, ipady=5); self.back_to_title_button.pack(side="right", padx=10, pady=10, ipadx=10, ipady=5)
        self.genre_label.grid(row=0, column=0, pady=10, padx=20, sticky="w"); self.timer_label.grid(row=0, column=1, pady=10, padx=20, sticky="e")
        self.guess_entry.grid(row=1, column=0, pady=10, padx=20, sticky="ew"); self.guess_button.grid(row=1, column=1, pady=10, padx=20)
        self.feedback_label.grid(row=2, column=0, columnspan=2, pady=5, padx=20); self.ranking_title_label.grid(row=3, column=0, columnspan=2, pady=(10,0), padx=20)
        self.ranking_text.grid(row=4, column=0, columnspan=2, pady=10, padx=20, sticky="nsew"); self.giveup_button.grid(row=5, column=0, columnspan=2, pady=10)
        self.game_over_frame.grid(row=6, column=0, columnspan=2, pady=10); self.guess_entry.bind("<Return>", self.make_a_guess)
    def setup_new_game(self, question, genre, time_limit, settings):
        self.question, self.time_limit, self.start_time, self.guessed_words, self.settings = question, time_limit, time.time(), {}, settings
        self.genre_label.configure(text=f"ジャンル: {genre}"); self.timer_label.configure(text=f"残り時間: {time_limit}秒")
        self.feedback_label.configure(text="------", font=self.controller.game_font, text_color=customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
        for widget in [self.guess_entry, self.guess_button, self.giveup_button]: widget.configure(state='normal')
        self.ranking_text.configure(state='normal'); self.ranking_text.delete('1.0', 'end'); self.ranking_text.configure(state='disabled')
        self.guess_entry.delete(0, 'end'); self.guess_entry.focus_set(); self.game_over_frame.grid_remove()
        if self.after_id: self.after_cancel(self.after_id);
        self.update_timer()
    def update_timer(self):
        remaining_time = self.time_limit - (time.time() - self.start_time)
        if remaining_time > 0: self.timer_label.configure(text=f"残り時間: {int(remaining_time)}秒"); self.after_id = self.after(1000, self.update_timer)
        else: self.game_over(is_win=False)
    def make_a_guess(self, event=None):
        guess = self.guess_entry.get().strip();
        if not guess: return
        if guess == self.question: self.game_over(is_win=True); return
        if not game_logic.word_exists(guess): self.feedback_label.configure(text="その単語は辞書にありません。", text_color="red")
        elif guess in self.guessed_words: self.feedback_label.configure(text="その単語は既に推測済みです。", text_color="orange")
        else:
            similarity = game_logic.check_similarity(self.question, guess); self.guessed_words[guess] = similarity
            if self.settings["show_similarity"]: feedback_text = f"「{guess}」... 正解との近さ: {similarity:.4f}"
            else: feedback_text = f"「{guess}」... 推測を受け付けました"
            self.feedback_label.configure(text=feedback_text, text_color="cyan", font=self.controller.game_font); self.update_ranking()
        self.guess_entry.delete(0, 'end')
    def update_ranking(self):
        self.ranking_text.configure(state='normal'); self.ranking_text.delete('1.0', 'end')
        sorted_guesses = sorted(self.guessed_words.items(), key=lambda i: i[1], reverse=True); total_guesses = len(sorted_guesses)
        display_count = self.settings["ranking_display_count"]
        if display_count == 0: self.ranking_text.configure(state='disabled'); return
        show_similarity = self.settings["show_similarity"]; text_to_display = []
        if total_guesses <= display_count * 2 and display_count != 0:
            for i, (word, sim) in enumerate(sorted_guesses): text_to_display.append(f"{i+1}位: {word}" + (f" ({sim:.2f})" if show_similarity else ""))
        elif display_count != 0:
            text_to_display.append(f"【正解に近いトップ{display_count}】"); [text_to_display.append(f"{i+1}位: {w}" + (f" ({s:.2f})" if show_similarity else "")) for i, (w, s) in enumerate(sorted_guesses[:display_count])]
            text_to_display.append("..."); text_to_display.append(f"【正解から遠いワースト{display_count}】")
            [text_to_display.append(f"{total_guesses-display_count+i+1}位: {w}" + (f" ({s:.2f})" if show_similarity else "")) for i, (w, s) in enumerate(sorted_guesses[-display_count:])]
        self.ranking_text.insert('end', "\n".join(text_to_display)); self.ranking_text.configure(state='disabled')
    def give_up(self): self.game_over(is_win=False, gave_up=True)
    def game_over(self, is_win, gave_up=False):
        if self.after_id: self.after_cancel(self.after_id)
        for widget in [self.guess_entry, self.guess_button, self.giveup_button]: widget.configure(state='disabled')
        final_text = ""; text_color = customtkinter.ThemeManager.theme["CTkLabel"]["text_color"]
        if is_win: final_text = "★★ 正解！おめでとうございます！ ★★"; text_color = "#00BF63"
        else:
            best_score_text = ""
            if self.guessed_words: best_guess = max(self.guessed_words, key=self.guessed_words.get); best_score = self.guessed_words[best_guess]; best_score_text = f"\nベストスコア: 「{best_guess}」 ({best_score:.4f})"
            if gave_up: final_text = f"ギブアップしました。正解は「{self.question}」でした。{best_score_text}"; text_color = "#FFA500"
            else: final_text = f"時間切れ！正解は「{self.question}」でした。{best_score_text}"; text_color = "#FF5733"
        self.feedback_label.configure(text=final_text, font=self.controller.result_font, text_color=text_color); self.game_over_frame.grid()


if __name__ == "__main__":
    # tkinter.messagebox を使うために必要
    from tkinter import messagebox
    random.seed()
    app = WordGameApp()
    app.mainloop()