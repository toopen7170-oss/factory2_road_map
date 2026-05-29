import os
import sys
import traceback
import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.text import LabelBase

# ==========================================
# [코어 설정] 실시간 블랙박스 및 이중 폰트 가로채기
# ==========================================
log_dir = '/storage/emulated/0/Download'
log_file = os.path.join(log_dir, 'factory_blackbox.log')
font_path = '/storage/emulated/0/Download/factory/factory_road_map/font.ttf'

def write_blackbox(log_type, message):
    """모든 시스템 이벤트를 실시간으로 저장공간/Download/factory_blackbox.log에 기록"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] [{log_type}] {message}\n"
    print(log_entry.strip())
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"블랙박스 기록 실패: {str(e)}")

# 앱 불시 튕김 현상 무조건 포착 감지기
def blackbox_exception_handler(exctype, value, tb):
    error_msg = f"치명적 오류 발생 (앱 튕김): {exctype.__name__}: {value}\n"
    error_msg += "".join(traceback.format_exception(exctype, value, tb))
    write_blackbox("CRASH_DUMP", error_msg)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = blackbox_exception_handler

# 이중 폰트 가로채기 등록 (순정 기본 폰트명 자체를 우리 한글 폰트로 위장시킵니다)
FONT_NAME = 'MyFont'
if os.path.exists(font_path):
    try:
        # 1. 커스텀 이름 등록
        LabelBase.register(name=FONT_NAME, fn_regular=font_path)
        # 2. 순정 엔진 기본 이름(Roboto) 가로채기 등록 (힌트 텍스트 깨짐 물리적 방어)
        LabelBase.register(name='Roboto', fn_regular=font_path)
        write_blackbox("FONT_REG_SUCCESS", f"Kivy 핵심 엔진에 '{FONT_NAME}' 및 'Roboto' 이중 교차 가로채기 등록 성공.")
    except Exception as e:
        write_blackbox("FONT_REG_ERROR", f"폰트 등록 프로세스 예외 발생: {str(e)}")
else:
    write_blackbox("FONT_MISSING", f"지정된 경로에 폰트 파일이 없습니다: {font_path}")

# 1. 로컬 데이터베이스 엔진 가동
def init_db():
    try:
        conn = sqlite3.connect('factory2_road_map.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                password TEXT,
                point INTEGER DEFAULT 0,
                unlocked_maps INTEGER DEFAULT 1,
                vehicle_level INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
        write_blackbox("DB_READY", "로컬 데이터베이스 테이블 무결성 검증 완료.")
    except Exception as e:
        write_blackbox("DB_CRITICAL", f"DB 가동 실패: {str(e)}")

# 2. 로그인 시스템 화면
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        write_blackbox("UI_BUILD", "로그인 스크린 인터페이스 렌더링 개시")
        
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        # 타이틀
        title = Label(text='factory2 road_map\n로그인 시스템', font_size=60, halign='center', font_name=FONT_NAME)
        layout.add_widget(title)
        
        # 아이디 입력창 (오류를 유발하던 hint_text_font_name을 소각하고 무결한 font_name으로 단일 통제)
        self.user_id = TextInput(
            hint_text='아이디를 입력하세요', 
            multiline=False, 
            font_size=40, 
            size_hint_y=0.4, 
            font_name=FONT_NAME
        )
        layout.add_widget(self.user_id)
        
        # 비밀번호 입력창
        self.password = TextInput(
            hint_text='비밀번호를 입력하세요', 
            password=True, 
            multiline=False, 
            font_size=40, 
            size_hint_y=0.4, 
            font_name=FONT_NAME
        )
        layout.add_widget(self.password)
        
        # 하단 버튼 레이아웃
        btn_layout = BoxLayout(spacing=20, size_hint_y=0.5)
        
        btn_login = Button(text='로드 게임\n(로그인)', font_size=40, halign='center', font_name=FONT_NAME)
        btn_login.bind(on_press=self.do_login)
        btn_layout.add_widget(btn_login)
        
        btn_register = Button(text='새 게임\n(회원가입)', font_size=40, halign='center', font_name=FONT_NAME)
        btn_register.bind(on_press=self.do_register)
        btn_layout.add_widget(btn_register)
        
        layout.add_widget(btn_layout)
        self.add_widget(layout)
        write_blackbox("UI_READY", "로그인 화면 배치 및 이벤트 바인딩 100% 완료")

    def show_popup(self, title, message):
        write_blackbox("POPUP_LOG", f"팝업 트리거 -> [{title}] {message.replace('\n', ' ')}")
        content = Label(text=message, font_size=30, halign='center', font_name=FONT_NAME)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4), title_font=FONT_NAME)
        popup.open()

    def do_register(self, instance):
        uid = self.user_id.text.strip()
        upw = self.password.text.strip()
        write_blackbox("USER_ACTION", f"새 게임(회원가입) 터치 감지 - 입력 ID: '{uid}'")
        
        if not uid or not upw:
            self.show_popup("경고", "아이디와 비밀번호를\n모두 입력해주세요.")
            return
            
        try:
            conn = sqlite3.connect('factory2_road_map.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (id, password) VALUES (?, ?)", (uid, upw))
            conn.commit()
            write_blackbox("DB_INSERT", f"신규 회원 데이터 가입 성공 ID: {uid}")
            self.show_popup("가입 완료", "새 게임 계정이 생성되었습니다!\n이제 로드 게임을 눌러주세요.")
        except sqlite3.IntegrityError:
            write_blackbox("DB_WARN", f"가입 실패: 이미 존재하는 중복 ID ({uid})")
            self.show_popup("오류", "이미 존재하는 아이디입니다.\n다른 아이디를 입력하세요.")
        except Exception as e:
            write_blackbox("DB_ERROR", f"회원가입 처리 중 예외 발생: {str(e)}")
        finally:
            conn.close()

    def do_login(self, instance):
        uid = self.user_id.text.strip()
        upw = self.password.text.strip()
        write_blackbox("USER_ACTION", f"로드 게임(로그인) 터치 감지 - 입력 ID: '{uid}'")
        
        try:
            conn = sqlite3.connect('factory2_road_map.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE id=? AND password=?", (uid, upw))
            user = c.fetchone()
            conn.close()
            
            if user:
                write_blackbox("AUTH_SUCCESS", f"로그인 인증 성공! 접속자 ID: {uid}")
                self.show_popup("로그인 성공!", f"환영합니다, {uid} 마스터!\n누적 포인트: {user[2]} 점")
                self.manager.current = 'game'
            else:
                write_blackbox("AUTH_FAIL", f"로그인 거부: 일치하는 계정 정보 없음 입력 ID: '{uid}'")
                self.show_popup("오류", "아이디 또는 비밀번호가\n틀렸습니다.")
        except Exception as e:
            write_blackbox("AUTH_ERROR", f"로그인 연산 중 예외 발생: {str(e)}")

# 3. 메인 게임 로비 화면
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50)
        
        msg = Label(text='[가상 레이싱 로비 접속 완료]\n\n센서 동기화 대기 중...', font_size=50, halign='center', font_name=FONT_NAME)
        layout.add_widget(msg)
        
        self.add_widget(layout)
        write_blackbox("SCENE_CHANGE", "메인 게임 로비 화면 활성화 성공")

# 4. 앱 메인 실행기
class road_map_app(App):
    def build(self):
        write_blackbox("SYSTEM", "factory2 road_map 어플리케이션 초기화 엔진 가동")
        init_db()
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(GameScreen(name='game'))
        return sm

if __name__ == '__main__':
    try:
        road_map_app().run()
    except Exception as e:
        write_blackbox("CRITICAL_EXIT", f"어플리케이션 메인 루프 강제 종료됨: {str(e)}")

