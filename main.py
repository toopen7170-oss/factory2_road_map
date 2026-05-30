import sqlite3
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.text import LabelBase
from kivy.clock import Clock
from datetime import datetime

# 상대 경로 기준 한글 폰트 등록
font_path = 'font.ttf'
if os.path.exists(font_path):
    LabelBase.register(name='NanumGothic', fn_regular=font_path)

class IndoorCyclingApp(App):
    def build(self):
        # 로컬 운동 기록 데이터베이스 초기화
        db_status = self.init_database()
        
        # 메인 레이아웃 (전체 세로 정렬)
        main_layout = BoxLayout(orientation='vertical', padding=25, spacing=15)
        
        # 상단 헤더 영역 (TV 미러링 시 상단 타이틀)
        header = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        title = Label(text="🚴 스마트 실내 사이클링 대시보드", font_name='NanumGothic', font_size=24, bold=True)
        status_label = Label(text=f"스토리지: {db_status}", font_name='NanumGothic', font_size=14, color=(0, 1, 0, 1))
        header.add_widget(title)
        header.add_widget(status_label)
        main_layout.add_widget(header)
        
        # 중단: TV 화면 송출을 고려한 대형 운동 정보 디스플레이 그리드 (2X2 구조)
        stats_grid = GridLayout(cols=2, spacing=20, size_hint_y=0.55)
        
        self.lbl_speed = Label(text="0.0\nkm/h", font_name='NanumGothic', font_size=42, halign='center', color=(0.1, 0.7, 1, 1))
        self.lbl_time = Label(text="00:00\n시간", font_name='NanumGothic', font_size=42, halign='center')
        self.lbl_dist = Label(text="0.00\n거리 (km)", font_name='NanumGothic', font_size=42, halign='center')
        self.lbl_cal = Label(text="0\nkcal", font_name='NanumGothic', font_size=42, halign='center', color=(1, 0.6, 0, 1))
        
        stats_grid.add_widget(self.lbl_speed)
        stats_grid.add_widget(self.lbl_time)
        stats_grid.add_widget(self.lbl_dist)
        stats_grid.add_widget(self.lbl_cal)
        main_layout.add_widget(stats_grid)
        
        # 하단 제어 및 인터랙션 상태 창
        btn_layout = BoxLayout(orientation='horizontal', spacing=20, size_hint_y=0.15)
        btn_start = Button(text="▶ 주행 시작", font_name='NanumGothic', font_size=20, background_color=(0.15, 0.65, 0.3, 1))
        btn_stop = Button(text="■ 주행 종료 및 기록", font_name='NanumGothic', font_size=20, background_color=(0.84, 0.24, 0.24, 1))
        
        btn_start.bind(on_release=self.start_workout)
        btn_stop.bind(on_release=self.stop_workout)
        
        btn_layout.add_widget(btn_start)
        btn_layout.add_widget(btn_stop)
        main_layout.add_widget(btn_layout)
        
        # 최하단 안내 가이드 바
        self.status_msg = Label(text="페달을 굴리거나 주행 시작 버튼을 누르면 기록이 시작됩니다.", font_name='NanumGothic', font_size=16, size_hint_y=0.15)
        main_layout.add_widget(self.status_msg)
        
        # 내부 제어 매개변수 초기화
        self.is_running = False
        self.elapsed_seconds = 0
        self.total_distance = 0.0
        self.total_calories = 0
        
        return main_layout

    def init_database(self):
        """운동 기록을 누적 저장할 로컬 SQLite3 데이터베이스 검증 및 테이블 생성"""
        try:
            conn = sqlite3.connect('cycling_data.db')
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workout_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    distance REAL NOT NULL,
                    calories INTEGER NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
            return "정상 연결됨"
        except Exception as e:
            return "DB 오류"

    def start_workout(self, instance):
        """주행 시작 프로토콜 활성화"""
        if not self.is_running:
            self.is_running = True
            self.status_msg.text = "주행 기록 중... TV 미러링 화면을 보면서 실내 사이클링을 즐기세요!"
            Clock.schedule_interval(self.update_dashboard, 1)

    def update_dashboard(self, dt):
        """실시간 운동 데이터 연산 및 화면 갱신 트리거 (1초 주기 작동)"""
        if not self.is_running:
            return False
            
        self.elapsed_seconds += 1
        # 2단계 센서 연동 전 시뮬레이션을 위한 가상 증가값 세팅
        self.total_distance += 0.006  # 초당 대략 6미터 전진 가정
        self.total_calories = int(self.elapsed_seconds * 0.18)  # 대략적인 소모 칼로리 연산
        
        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60
        
        # UI 레이아웃 실시간 동기화
        self.lbl_speed.text = "21.6\nkm/h"  # 가상 속도 고정
        self.lbl_time.text = f"{minutes:02d}:{seconds:02d}\n시간"
        self.lbl_dist.text = f"{self.total_distance:.2f}\n거리 (km)"
        self.lbl_cal.text = f"{self.total_calories}\nkcal"

    def stop_workout(self, instance):
        """주행 종료 프로토콜 실행 및 데이터베이스 무결성 적재"""
        if self.is_running:
            self.is_running = False
            Clock.unschedule(self.update_dashboard)
            
            # 주행 데이터 처리 및 SQLite3 바인딩
            try:
                conn = sqlite3.connect('cycling_data.db')
                cursor = conn.cursor()
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                minutes = self.elapsed_seconds // 60
                seconds = self.elapsed_seconds % 60
                duration_str = f"{minutes:02d}:{seconds:02d}"
                
                cursor.execute('''
                    INSERT INTO workout_history (date, duration, distance, calories)
                    VALUES (?, ?, ?, ?)
                ''', (current_time, duration_str, round(self.total_distance, 2), self.total_calories))
                conn.commit()
                conn.close()
                
                self.status_msg.text = f"운동 완료! 기록이 안전하게 저장되었습니다. (총 {duration_str} / {self.total_distance:.2f}km)"
            except Exception as e:
                self.status_msg.text = f"데이터 저장 실패: {str(e)}"
            
            # 운동 리셋
            self.elapsed_seconds = 0
            self.total_distance = 0.0
            self.total_calories = 0

if __name__ == '__main__':
    IndoorCyclingApp().run()
