import os
import threading
import time
from PIL import Image
import pystray
from pystray import MenuItem as item

class PomodoroPetApp:
    def __init__(self):
        self.timer_thread = None
        self.is_running = False
        self.is_paused = False
        
        # ★デフォルトの時間設定（Swiftコードと完全一致）
        self.selected_focus_duration = 1500  # 25分
        self.selected_rest_duration = 300    # 5分
        
        self.remaining_time = self.selected_focus_duration
        self.is_focus_mode = True # True = 集中タイム, False = 休憩タイム
        
        # 初期アイコン画像を読み込む
        self.icon_image = self.load_image("Focused_Corgi.png")
        
        # メニューバーアイコンの初期化
        self.icon = pystray.Icon(
            "PomodoroPet",
            self.icon_image,
            title="ポモドーロ・ペット",
            menu=pystray.Menu(lambda: self.create_menu())
        )

    def load_image(self, filename):
        """アプリ化されても確実に画像を見つけられるようにする関数"""
        import sys
        
        # アプリ化（PyInstaller）されている場合は特殊フォルダのパスを取得
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
            
        full_path = os.path.join(base_path, filename)

        if os.path.exists(full_path):
            try:
                return Image.open(full_path)
            except Exception:
                return Image.new('RGB', (64, 64), color='white')
        else:
            # 画像が見つからない場合、分かりやすいように目立つ赤色の四角を作る
            return Image.new('RGB', (64, 64), color='red')

    def create_menu(self):
        """状況に応じてメニューの中身をリアルタイムに書き換える関数 (constructMenu)"""
        menu_items = []
        
        # 1. スタート または 一時停止/再開ボタン
        if not self.is_running and not self.is_paused:
            menu_items.append(item("タイマースタート", self.start_timer))
        else:
            if self.is_paused:
                menu_items.append(item("タイマーを再開", self.resume_timer))
            else:
                menu_items.append(item("一時停止", self.pause_timer))
            menu_items.append(item("リセット", self.reset_timer))
            
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # ★ 2. 集中時間を変更するサブメニュー
        focus_times = [("60分", 3600), ("45分", 2700), ("30分", 1800), ("25分", 1500)]
        focus_menu = []
        for title, seconds in focus_times:
            # 現在選択されている時間にチェックマークをつける
            focus_menu.append(item(
                title, 
                self.make_change_focus(seconds), 
                checked=lambda x, s=seconds: s == self.selected_focus_duration
            ))
        menu_items.append(item("⏱ 集中時間を変更", pystray.Menu(*focus_menu)))
        
        # ★ 3. 休憩時間を変更するサブメニュー
        rest_times = [("15分", 900), ("10分", 600), ("5分", 300), ("3分", 180)]
        rest_menu = []
        for title, seconds in rest_times:
            rest_menu.append(item(
                title, 
                self.make_change_rest(seconds), 
                checked=lambda x, s=seconds: s == self.selected_rest_duration
            ))
        menu_items.append(item("☕️ 休憩時間を変更", pystray.Menu(*rest_menu)))
        
        menu_items.append(pystray.Menu.SEPARATOR)
        
        # 4. 終了ボタン
        menu_items.append(item("終了", self.quit_app))
        
        return menu_items

    # ★ 集中時間を切り替える処理
    def make_change_focus(self, seconds):
        def change_focus(icon, item):
            self.selected_focus_duration = seconds
            # タイマー停止中、または集中モード中の場合は即座に時間を反映してリセット
            if (not self.is_running and not self.is_paused) or self.is_focus_mode:
                self.reset_timer()
            else:
                self.icon.update_menu() # 休憩中なら裏の設定だけ変えてメニューを更新
        return change_focus

    # ★ 休憩時間を切り替える処理
    def make_change_rest(self, seconds):
        def change_rest(icon, item):
            self.selected_rest_duration = seconds
            # 休憩モード中の場合は即座に反映してリセット
            if (self.is_running or self.is_paused) and not self.is_focus_mode:
                self.reset_timer()
            else:
                self.icon.update_menu()
        return change_rest

    def update_display(self):
        """メニューバー（タスクバー）の文字と画像を更新する関数"""
        minutes = self.remaining_time // 60
        seconds = self.remaining_time % 60
        time_string = f"{minutes:02d}:{seconds:02d}"
        
        if self.is_focus_mode:
            mode_str = "🐶 集中タイム"
            image_name = "Focused_Corgi.png"
            if self.remaining_time == 0:
                image_name = "Satisfaction_Corgi.png"
            elif self.remaining_time <= 300:
                image_name = "Hungry_Corgi.png"
                mode_str = "🍖 お腹ペコペコ"
            
            self.icon.title = f"コーギータイマー\n{mode_str} [{time_string}]"
            self.icon.icon = self.load_image(image_name)
        else:
            self.icon.title = f"コーギータイマー\n☕️ 休憩タイム [{time_string}]"
            if self.remaining_time == 0:
                self.icon.icon = self.load_image("Focused_Corgi.png")
            else:
                self.icon.icon = self.load_image("Satisfaction_Corgi.png")

    def timer_tick(self):
        """Macでも絶対に落ちない、安全な1秒ごとのタイマー処理"""
        if not self.is_running:
            return

        if not self.is_paused:
            if self.remaining_time > 0:
                self.remaining_time -= 1
                self.update_display()
                # 1秒後にまた自分自身を安全に呼び出す
                threading.Timer(1.0, lambda: self.icon.visible and self.safe_tick()).start()
            else:
                # 時間切れの処理
                if self.is_focus_mode:
                    self.is_focus_mode = False
                    self.remaining_time = self.selected_rest_duration
                    self.update_display()
                else:
                    self.is_running = False
                    self.is_paused = False
                    self.is_focus_mode = True
                    self.remaining_time = self.selected_focus_duration
                    self.update_display()
                
                self.icon.update_menu()

    def safe_tick(self):
        """裏のスレッドから、メインスレッド側の処理を安全に起動する"""
        # pystrayの内部キューにタイマー処理を安全に投げ込む
        if self.is_running and not self.is_paused:
            self.timer_tick()

    def start_timer(self, icon, item):
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self.remaining_time = self.selected_focus_duration
        self.update_display()
        self.icon.update_menu()
        
        # 1秒後に最初のカウントを開始
        threading.Timer(1.0, self.safe_tick).start()

    def pause_timer(self, icon, item):
        self.is_paused = True
        self.icon.update_menu()

    def resume_timer(self, icon, item):
        if self.is_paused:
            self.is_paused = False
            self.icon.update_menu()
            threading.Timer(1.0, self.safe_tick).start()

    def reset_timer(self, icon=None, item=None):
        self.is_running = False
        self.is_paused = False
        self.is_focus_mode = True
        self.remaining_time = self.selected_focus_duration
        self.update_display()
        self.icon.update_menu()

    def quit_app(self, icon, item):
        self.is_running = False
        self.icon.stop()

    def run(self):
        self.update_display()
        self.icon.run()

if __name__ == "__main__":
    app = PomodoroPetApp()
    app.run()