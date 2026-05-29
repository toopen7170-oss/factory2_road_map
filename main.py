import sqlite3
import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.text import LabelBase

# 상대 경로 기준 한글 폰트 등록
font_path = 'font.ttf'
if os.path.exists(font_path):
    LabelBase.register(name='NanumGothic', fn_regular=font_path)

class FactoryRoadMapApp(App):
    def build(self):
        self.log_message("=== Factory 2.0 로드맵 엔진 가동 ===")
        
        # 1. 로컬 데이터베이스 자동 검증 및 테이블 초기화
        db_status = self.init_database()
        
        # 메인 레이아웃 (세로 정렬)
        main_layout = BoxLayout(orientation='vertical', padding=15, spacing=12)
        
        # 상단 헤더 및 로컬 DB 커넥션 상태 표시줄
        header = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        title = Label(text="⚙️ Factory 2.0 마스터 로드맵", font_name='NanumGothic', font_size=20, bold=True)
        status_color = (0, 1, 0, 1) if "성공" in db_status else (1, 0, 0, 1)
        status_label = Label(text=f"DB: {db_status}", font_name='NanumGothic', font_size=14, color=status_color)
        header.add_widget(title)
        header.add_widget(status_label)
        main_layout.add_widget(header)
        
        # 중단: 새로 설계된 5단계 공정 스크롤 영역
        scroll = ScrollView(size_hint_y=0.7)
        grid = GridLayout(cols=1, spacing=15, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        # 데이터베이스로부터 실시간 공정 노드 호출
        roadmap_data = self.fetch_roadmap_data()
        for item in roadmap_data:
            node_id, stage, title_text, manager, status = item
            btn_text = f"[{stage}] {title_text}\n• 담당자: {manager}  |  • 상태: {status}"
            
            # 직관적인 대형 공정 노드 버튼 컴포넌트 생성
            btn = Button(
                text=btn_text, 
                font_name='NanumGothic', 
                size_hint_y=None, 
                height=90, 
                background_color=(0.15, 0.45, 0.7, 1)
            )
            # 클로저 공간을 활용한 클릭 이벤트 바인딩
            btn.bind(on_release=lambda instance, nid=node_id, name=title_text: self.on_node_click(nid, name))
            grid.add_widget(btn)
            
        scroll.add_widget(grid)
        main_layout.add_widget(scroll)
        
        # 하단: 실시간 인터랙션 상태 창 (블랙박스 터미널 뷰어)
        self.log_label = Label(
            text="공정 노드를 터치하면 세부 제어 로그가 활성화됩니다.", 
            font_name='NanumGothic', 
            size_hint_y=0.2, 
            halign='center', 
            valign='middle'
        )
        self.log_label.bind(size=self.log_label.setter('text_size'))
        main_layout.add_widget(self.log_label)
        
        return main_layout

    def init_database(self):
        """로컬 SQLite3 DB 무결성 전수검사 및 자동 테이블 생성기"""
        try:
            conn = sqlite3.connect('factory_data.db')
            cursor = conn.cursor()
            
            # 로드맵 저장을 위한 구조적 전용 테이블 사출
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roadmap (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT NOT NULL,
                    title TEXT NOT NULL,
                    manager TEXT,
                    status TEXT
                )
            ''')
            
            # 공정 테이블 초기 가동 여부 체크 및 초기 데이터 세트 주입
            cursor.execute('SELECT COUNT(*) FROM roadmap')
            if cursor.fetchone()[0] == 0:
                new_roadmap_design = [
                    ('1단계', '원자재 정밀 입고 및 규격 검사', '김생산', '공정 대기'),
                    ('2단계', '메인 프레임 자동화 라인 1차 가공', '이엔지', '준비 완료'),
                    ('3단계', '초정밀 모듈 조립 및 레이저 마킹', '박기술', '가동 중'),
                    ('4단계', 'AI 비전 광학 장비 기반 품질 검사(QA)', '최품질', '검사 대기'),
                    ('5단계', '완제품 진공 패킹 및 출하 물류 사출', '정물류', '대기 중')
                ]
                cursor.executemany(
                    'INSERT INTO roadmap (stage, title, manager, status) VALUES (?, ?, ?, ?)', 
                    new_roadmap_design
                )
                conn.commit()
                self.log_message("새로운 5단계 공정 로드맵 데이터를 DB에 바인딩했습니다.")
            
            conn.close()
            self.log_message("로컬 데이터베이스 연결 상태 검증 완료: 정상 작동 중")
            return "연결 성공 및 무결"
        except Exception as e:
            error_msg = f"DB 데이터베이스 치명적 결함 발견: {str(e)}"
            self.log_message(error_msg)
            return "연결 실패"

    def fetch_roadmap_data(self):
        """DB에 저장된 로드맵 테이블 자원 추출"""
        try:
            conn = sqlite3.connect('factory_data.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, stage, title, manager, status FROM roadmap ORDER BY id ASC')
            data = cursor.fetchall()
            conn.close()
            return data
        except:
            return []

    def on_node_click(self, node_id, node_name):
        """공정 노드 인터랙션 발생 시 실시간 동작 추적기"""
        action_log = f"인터랙션 포착 -> [공정 ID: {node_id}] {node_name}"
        self.log_message(action_log)
        self.log_label.text = f"최근 활성화된 공정 정보:\n{action_log}"

    def log_message(self, message):
        """앱 내부 블랙박스 무결성 로그 파일 저장 기능"""
        with open("factory_blackbox.log", "a", encoding="utf-8") as f:
            f.write(f"{message}\n")

if __name__ == '__main__':
    FactoryRoadMapApp().run()
