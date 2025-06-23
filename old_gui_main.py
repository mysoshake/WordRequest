import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk  # プログレスバーなどモダンなウィジェットを使うためにインポート
import threading       # 並行処理のためにインポート
import time
import json
import os
import game_logic

class WordGameApp(tk.Tk):
    """GUIアプリケーションのメインクラス"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("言葉当てゲーム")
        self.geometry("600x700")
        self.title_font = tkfont.Font(family="Helvetica", size=32, weight="bold")
        self.info_font = tkfont.Font(family="Helvetica", size=14)
        self.button_font = tkfont.Font(family="Helvetica", size=16)
        self.game_font = tkfont.Font(family="Helvetica", size=12)
        self.result_font = tkfont.Font(family="Helvetica", size=20, weight="bold")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # 3つの画面（Loading, Start, Game）を作成
        for F in (LoadingPage, StartPage, GamePage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # 最初に「ロード中」画面を表示
        self.show_frame(LoadingPage)
        
        # モデルとデータの読み込みをバックグラウンドで開始
        self.start_loading()

    def show_frame(self, page_class):
        frame = self.frames[page_class]
        frame.tkraise()

    def start_loading(self):
        """モデルとデータの読み込みを別スレッドで開始する"""
        # daemon=Trueにすると、メインプログラム終了時にスレッドも強制終了する
        self.loading_thread = threading.Thread(target=self.load_data_in_background, daemon=True)
        self.loading_thread.start()
        # ロードが完了したか定期的にチェックする
        self.check_loading_status()

    def load_data_in_background(self):
        """バックグラウンドで実行される重い読み込み処理"""
        print("バックグラウンドで読み込み開始...")
        MODEL_FILE_NAME = "jawiki.entity_vectors.300d.txt"
        model_path = os.path.join("model", MODEL_FILE_NAME)
        game_logic.load_model(model_path)
        
        self.easy_data = game_logic.load_json_data("data/easy_data.json")
        self.normal_data = game_logic.load_json_data("data/normal_data.json")
        self.hard_data = game_logic.load_json_data("data/hard_data.json")
        print("バックグラウンドでの読み込み完了。")

    def check_loading_status(self):
        """読み込みスレッドが完了したかポーリング（監視）する"""
        if self.loading_thread.is_alive():
            #まだロード中なら、100ミリ秒後にもう一度チェック
            self.after(100, self.check_loading_status)
        else:
            # ロードが終わったら、スタート画面に切り替え
            print("画面をスタートページに切り替えます。")
            self.show_frame(StartPage)

    def start_game(self, difficulty):
        question, genre = game_logic.generate_question_by_difficulty(
            difficulty, self.easy_data, self.normal_data, self.hard_data
        )
        if not question:
            print("エラー: お題を生成できませんでした。")
            return
        if difficulty == "1": time_limit = 300
        elif difficulty == "2": time_limit = 240
        else: time_limit = 180
        game_frame = self.frames[GamePage]
        game_frame.setup_new_game(question, genre, time_limit)
        self.show_frame(GamePage)

# ▼▼▼ 新しく追加したロード中画面 ▼▼▼
class LoadingPage(tk.Frame):
    """ロード中画面のクラス"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label1 = tk.Label(self, text="ゲームの準備をしています...", font=controller.title_font)
        label1.pack(pady=40)
        label2 = tk.Label(self, text="モデルファイルの読み込みには数分かかります。\nそのままお待ちください。", font=controller.info_font)
        label2.pack(pady=20)

        # プログレスバー（進捗が不明な場合に左右に動くモード）
        progress_bar = ttk.Progressbar(self, mode='indeterminate')
        progress_bar.pack(pady=20, padx=50, fill='x')
        progress_bar.start(10) # 10ミリ秒間隔で動かす

class StartPage(tk.Frame):
    """スタート画面のクラス"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        tk.Label(self, text="言葉当てゲーム", font=controller.title_font).pack(pady=40)
        tk.Label(self, text="難易度を選択してください", font=controller.info_font).pack(pady=10)
        tk.Button(self, text="かんたん", font=controller.button_font,
                  command=lambda: controller.start_game("1")).pack(pady=10, ipadx=20, ipady=5)
        tk.Button(self, text="普通", font=controller.button_font,
                  command=lambda: controller.start_game("2")).pack(pady=10, ipadx=20, ipady=5)
        tk.Button(self, text="むずかしい", font=controller.button_font,
                  command=lambda: controller.start_game("3")).pack(pady=10, ipadx=20, ipady=5)

class GamePage(tk.Frame):
    """ゲーム画面のクラス"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.after_id = None
        # (GamePageの中身は変更ありません。長いので省略します)
        self.grid_columnconfigure(0, weight=1)
        self.genre_label = tk.Label(self, text="ジャンル: ？？？", font=controller.info_font)
        self.timer_label = tk.Label(self, text="残り時間: ---秒", font=controller.info_font)
        self.guess_entry = tk.Entry(self, font=controller.button_font)
        self.guess_button = tk.Button(self, text="推測！", font=controller.button_font, command=self.make_a_guess)
        self.feedback_label = tk.Label(self, text="単語を入力して推測してください", font=controller.game_font)
        ranking_title_label = tk.Label(self, text="--- 推測単語ランキング ---", font=controller.info_font)
        self.ranking_text = tk.Text(self, height=15, width=40, font=controller.game_font, state='disabled')
        self.giveup_button = tk.Button(self, text="ギブアップ", font=controller.button_font, command=self.give_up)
        self.guess_entry.bind("<Return>", self.make_a_guess)
        self.genre_label.grid(row=0, column=0, pady=10, padx=10, sticky="w")
        self.timer_label.grid(row=0, column=1, pady=10, padx=10, sticky="e")
        self.guess_entry.grid(row=1, column=0, pady=10, padx=10, sticky="ew")
        self.guess_button.grid(row=1, column=1, pady=10, padx=10, sticky="ew")
        self.feedback_label.grid(row=2, column=0, columnspan=2, pady=5, padx=10)
        ranking_title_label.grid(row=3, column=0, columnspan=2, pady=10, padx=10)
        self.ranking_text.grid(row=4, column=0, columnspan=2, pady=10, padx=10)
        self.giveup_button.grid(row=5, column=0, columnspan=2, pady=20, padx=10)
    def setup_new_game(self, question, genre, time_limit):
        self.question, self.time_limit, self.start_time, self.guessed_words = question, time_limit, time.time(), {}
        self.genre_label.config(text=f"ジャンル: {genre}" if "ジャンル指定なし" not in genre else "")
        self.timer_label.config(text=f"残り時間: {time_limit}秒")
        self.feedback_label.config(text="単語を入力して推測してください", fg="black")
        for widget in [self.guess_entry, self.guess_button, self.giveup_button]: widget.config(state='normal')
        self.ranking_text.config(state='normal'); self.ranking_text.delete('1.0', 'end'); self.ranking_text.config(state='disabled')
        self.guess_entry.delete(0, 'end'); self.guess_entry.focus_set()
        if self.after_id: self.after_cancel(self.after_id)
        self.update_timer()
    def update_timer(self):
        remaining_time = self.time_limit - (time.time() - self.start_time)
        if remaining_time > 0:
            self.timer_label.config(text=f"残り時間: {int(remaining_time)}秒")
            self.after_id = self.after(1000, self.update_timer)
        else: self.game_over(is_win=False)
    def make_a_guess(self, event=None):
        guess = self.guess_entry.get().strip()
        if not guess: return
        if guess == self.question: self.game_over(is_win=True); return
        if not game_logic.word_exists(guess): self.feedback_label.config(text="その単語は辞書にありません。", fg="red")
        elif guess in self.guessed_words: self.feedback_label.config(text="その単語は既に推測済みです。", fg="orange")
        else:
            similarity = game_logic.check_similarity(self.question, guess); self.guessed_words[guess] = similarity
            self.feedback_label.config(text=f"「{guess}」... 正解との近さ: {similarity:.4f}", fg="blue"); self.update_ranking()
        self.guess_entry.delete(0, 'end')
    def update_ranking(self):
        self.ranking_text.config(state='normal'); self.ranking_text.delete('1.0', 'end')
        sorted_guesses = sorted(self.guessed_words.items(), key=lambda i: i[1], reverse=True); total_guesses = len(sorted_guesses)
        if total_guesses <= 10: [self.ranking_text.insert('end', f"{i+1}位: {w}\n") for i, (w, s) in enumerate(sorted_guesses)]
        else:
            self.ranking_text.insert('end', "【正解に近いトップ5】\n"); [self.ranking_text.insert('end', f"{i+1}位: {w}\n") for i, (w, s) in enumerate(sorted_guesses[:5])]
            self.ranking_text.insert('end', "...\n"); self.ranking_text.insert('end', "【正解から遠いワースト5】\n")
            [self.ranking_text.insert('end', f"{total_guesses-5+i+1}位: {w}\n") for i, (w, s) in enumerate(sorted_guesses[-5:])]
        self.ranking_text.config(state='disabled')
    def give_up(self): self.game_over(is_win=False, gave_up=True)
    def game_over(self, is_win, gave_up=False):
        if self.after_id: self.after_cancel(self.after_id)
        for widget in [self.guess_entry, self.guess_button, self.giveup_button]: widget.config(state='disabled')
        if is_win: self.feedback_label.config(text=f"★★ 正解！おめでとうございます！ ★★", font=self.controller.result_font, fg="green")
        elif gave_up: self.feedback_label.config(text=f"ギブアップしました。正解は「{self.question}」でした。", font=self.controller.result_font, fg="orange")
        else: self.feedback_label.config(text=f"時間切れ！正解は「{self.question}」でした。", font=self.controller.result_font, fg="red")


if __name__ == "__main__":
    app = WordGameApp()
    app.mainloop()