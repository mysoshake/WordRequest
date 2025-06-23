import os
import random
import time
import json
from gensim.models import KeyedVectors

# --- グローバル変数としてモデルを保持 ---
# アプリケーション起動時に一度だけ読み込む
model = None

SETTINGS_FILE = "settings.json"

def load_model(model_path):
    """モデルを読み込み、グローバル変数に格納する"""
    global model
    print("モデルを読み込んでいます...")
    try:
        model = KeyedVectors.load_word2vec_format(model_path, binary=False)
        print("モデルの読み込みが完了しました。")
        return True
    except FileNotFoundError:
        print(f"エラー: モデルファイルが見つかりません。'{model_path}'")
        return False
    except Exception as e:
        print(f"モデル読み込み中にエラーが発生しました: {e}")
        return False

def load_json_data(filepath):
    """JSONファイルからデータを読み込む関数"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"エラー: データファイルが見つかりません。'{filepath}'")
        return None
    except json.JSONDecodeError:
        print(f"エラー: JSONの形式が正しくありません。'{filepath}'")
        return None

def generate_easy_question(data):
    """「かんたん」モードのお題を生成する"""
    SIMILARITY_THRESHOLD = 0.6
    RANDOM_CANDIDATE_COUNT = 5
    
    genre_list = list(data.keys())
    selected_genre = random.choice(genre_list)
    
    try:
        all_related_words = model.most_similar(selected_genre, topn=200)
    except KeyError: return None, None

    primary_candidates = [word for word, similarity in all_related_words if similarity >= SIMILARITY_THRESHOLD]
            
    if len(primary_candidates) < RANDOM_CANDIDATE_COUNT: return None, None

    secondary_candidates = random.sample(primary_candidates, RANDOM_CANDIDATE_COUNT)

    final_scores = {}
    example_words = data[selected_genre]["example_words"]
    for word in secondary_candidates:
        if word not in model: continue
        max_similarity_to_examples = max(
            (model.similarity(word, ex_word) for ex_word in example_words if ex_word in model),
            default=0
        )
        final_scores[word] = max_similarity_to_examples
        
    if not final_scores: return None, None
    final_question = max(final_scores, key=final_scores.get)
    return final_question, selected_genre

def generate_question_by_difficulty(difficulty, e_data, n_data, h_data):
    """難易度に応じてお題を生成し、(お題, ジャンル)のタプルを返す"""
    if difficulty == "1":
        if not e_data: return None, None
        return generate_easy_question(e_data)
    elif difficulty == "2":
        if not n_data: return None, None
        selected_genre = random.choice(list(n_data.keys()))
        question = random.choice(n_data[selected_genre])
        return question, "（ジャンル指定なし）"
    elif difficulty == "3":
        if not h_data: return None, None
        selected_genre = random.choice(list(h_data.keys()))
        question = random.choice(h_data[selected_genre])
        return question, "（ジャンル指定なし）"
    else: return None, None

def check_similarity(word1, word2):
    """2つの単語の類似度を計算する"""
    if word1 in model and word2 in model:
        return model.similarity(word1, word2)
    return 0

def word_exists(word):
    """単語がモデルに存在するかチェックする"""
    return word in model

def get_default_settings():
    """デフォルト設定を返す関数"""
    return {
      "appearance_mode": "System",
      "bgm_volume": 0.5,
      "se_volume": 0.8,
      "time_limits": {
        "1": 300, # かんたん
        "2": 240, # 普通
        "3": 180  # むずかしい
      },
      "ranking_display_count": 5,
      "show_similarity": False # 要望①にあった項目を先取り
    }

def load_settings():
    """settings.jsonから設定を読み込む。ファイルがなければデフォルト設定を返す。"""
    if not os.path.exists(SETTINGS_FILE):
        return get_default_settings()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
            # 古い設定ファイルに新しいキーがない場合に備え、デフォルト値で補完する
            default_settings = get_default_settings()
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
                elif isinstance(value, dict): # time_limitsのような辞書の中もチェック
                    for sub_key, sub_value in value.items():
                        if sub_key not in settings[key]:
                            settings[key][sub_key] = sub_value
            return settings
    except (json.JSONDecodeError, IOError):
        # ファイルが壊れている場合などもデフォルトを返す
        return get_default_settings()

def save_settings(settings):
    """設定をsettings.jsonに保存する"""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            # indent=2 で人間が読みやすいように整形して保存
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"設定の保存中にエラーが発生しました: {e}")
        
def generate_custom_question(keyword):
    """カスタムモード用のお題を生成する関数（新ロジック）"""
    if not keyword or not word_exists(keyword):
        # キーワードが空、またはモデルに存在しない場合は失敗
        return None

    try:
        # 類似語を上位100件取得
        related_words = model.most_similar(keyword, topn=100)
        
        # 候補の単語リストを作成
        candidates = [word for word, similarity in related_words]
        
        if not candidates:
            # 候補が見つからなかった場合（ほぼあり得ないが念のため）
            return None
            
        # 候補の中からランダムに1つ選ぶ
        return random.choice(candidates)

    except Exception as e:
        print(f"カスタムお題生成中にエラー: {e}")
        return None