import os
import time
# game_logic.pyから必要な関数や変数をインポート
from game_logic import (
    load_model,
    load_json_data,
    generate_question_by_difficulty,
    check_similarity,
    word_exists
)

def play_game_cui(question, time_limit, genre=None):
    """CUIでゲームをプレイするための関数"""
    start_time = time.time()
    guessed_words = {}

    print("\n--- ゲームスタート！ ---")
    if genre and "ジャンル指定なし" not in genre:
        print(f"ジャンル: {genre}")
    print(f"制限時間: {time_limit}秒")
    print("お題となる単語を推測してください。ギブアップする場合は 'giveup' と入力してください。")

    while True:
        elapsed_time = time.time() - start_time
        remaining_time = time_limit - elapsed_time
        if remaining_time <= 0:
            print(f"\n時間切れ！正解は「{question}」でした。")
            return

        guess = input(f"\n残り時間: {int(remaining_time)}秒 | 推測した単語を入力: ").strip()

        if guess.lower() == 'giveup':
            print(f"\nギブアップしました。正解は「{question}」でした。")
            return
        
        if guess == question:
            print(f"\n★★ 正解！おめでとうございます！正解は「{question}」でした！ ★★")
            return

        if not word_exists(guess):
            print("その単語は辞書にありません。別の単語を試してください。")
            continue
        
        if guess in guessed_words:
            print("その単語は既に推測済みです。")
            continue

        similarity = check_similarity(question, guess)
        guessed_words[guess] = similarity
        print(f"「{guess}」... 正解との近さ: {similarity:.4f}")

        if guessed_words:
            sorted_guesses = sorted(guessed_words.items(), key=lambda item: item[1], reverse=True)
            total_guesses = len(sorted_guesses)
            print("\n--- ヒント: 推測単語ランキング ---")
            if total_guesses <= 10:
                for i, (word, sim) in enumerate(sorted_guesses):
                    print(f"{i + 1}位: {word}")
            else:
                print("【正解に近いトップ5】")
                for i, (word, sim) in enumerate(sorted_guesses[:5]): print(f"{i + 1}位: {word}")
                print("...")
                print("【正解から遠いワースト5】")
                for i, (word, sim) in enumerate(sorted_guesses[-5:]):
                    rank = total_guesses - 5 + i + 1
                    print(f"{rank}位: {word}")


# --- メインの実行ブロック ---
if __name__ == "__main__":
    # 設定
    MODEL_FILE_NAME = "jawiki.entity_vectors.300d.txt"
    model_path = os.path.join("model", MODEL_FILE_NAME)

    # 1. モデルとデータを読み込む
    if load_model(model_path):
        easy_data = load_json_data(os.path.join("data", "easy_data.json"))
        normal_data = load_json_data(os.path.join("data", "normal_data.json"))
        hard_data = load_json_data(os.path.join("data", "hard_data.json"))

        if not all([easy_data, normal_data, hard_data]):
            print("\nデータファイルの読み込みに失敗したため、プログラムを終了します。")
        else:
            # 2. 難易度を選択してもらう
            print("\n言葉の近さからお題を当てるゲーム！")
            print("難易度を選択してください。")
            selected_difficulty = input("1: かんたん, 2: 普通, 3: むずかしい -> ")

            # 3. お題を生成
            question, genre = generate_question_by_difficulty(selected_difficulty, easy_data, normal_data, hard_data)

            if not question:
                print("\nお題を生成できませんでした。プログラムを終了します。")
            else:
                # 4. ゲームプレイを開始
                if selected_difficulty == "1": time_limit = 300
                elif selected_difficulty == "2": time_limit = 240
                else: time_limit = 180
                
                play_game_cui(question, time_limit, genre)