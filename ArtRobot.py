import sys
import threading
from datetime import datetime, timedelta
import os
import math

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QSizePolicy, QProgressBar, 
)
from PyQt5.QtCore import Qt, QTimer, QSize, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QIcon, QFont, QPalette, QColor, QPainter, QPen

# ✅ PC가 Modbus TCP Slave(서버)로 동작 (정상작동 확인한 구조)
from pymodbus.server.sync import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock


# =========================================================
# Modbus TCP Slave 설정 (PC가 서버)
# =========================================================
PC_IP = "192.168.xxx.xx"
PC_PORT = 502

# 주소 매핑
DI_ADDRS = list(range(0, 7))  # DI_0~DI_6 : 0~6
DO0_BUSY_ADDR = 7             # DO_0 : 7 (Coil)

# Discrete Inputs (fc=2) : PC -> 로봇 명령
di_block = ModbusSequentialDataBlock(0, [0] * 10)
# Coils (fc=1) : 로봇 -> PC 상태 (BUSY 등)
co_block = ModbusSequentialDataBlock(0, [0] * 10)
# Holding Registers (fc=3) : 필요시 확장
hr_block = ModbusSequentialDataBlock(0, [0] * 10)

store = ModbusSlaveContext(di=di_block, co=co_block, hr=hr_block)
context = ModbusServerContext(slaves=store, single=True)


def run_modbus_server():
    # StartTcpServer는 blocking 이므로 스레드로 실행
    StartTcpServer(context, address=(PC_IP, PC_PORT))


def start_modbus_slave_server():
    t = threading.Thread(target=run_modbus_server, daemon=True)
    t.start()
    return context


# -----------------------------
# Modbus 헬퍼 
# -----------------------------
def set_di(ctx, addr, val: int):
    # fc=2 Discrete Inputs
    ctx[0x00].setValues(2, addr, [int(val)])


def get_do(ctx, addr) -> int:
    # fc=1 Coils
    return int(ctx[0x00].getValues(1, addr, count=1)[0])


def reset_all_di(ctx):
    for a in DI_ADDRS:
        set_di(ctx, a, 0)


def set_only_one_di_on(ctx, on_addr: int):
    reset_all_di(ctx)
    set_di(ctx, on_addr, 1)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# 로그 저장 함수 (그림 이름과 시간을 기록)
def save_drawing_log(item_id: str):
    # ✅ id -> 한글 이름 매핑
    ID_TO_KR = {
        "tri": "세모",
        "rect": "네모",
        "circle": "동그라미",
        "heart": "하트",
        "star": "별",
        "cat": "고양이"
    }

    # 바탕화면 경로 설정
    desktop_path = os.path.expanduser("~/Desktop")  # 바탕화면 경로
    folder_name = "미술로봇 사용현황"  # 폴더 이름
    folder_path = os.path.join(desktop_path, folder_name)

    # 폴더가 없으면 생성
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    # 오늘 날짜로 파일명 설정 (yyyy-mm-dd 형식)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(folder_path, f"{today}.txt")

    # 현재 시간 구하기
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ✅ 저장할 그림명: tri면 세모로 변환, 모르면 원본 그대로
    drawing_name = ID_TO_KR.get(item_id, item_id)

    # 파일이 없다면 생성하고, 있으면 덧붙이기 (기록이 이어짐)
    with open(log_file, "a", encoding="utf-8-sig") as file:  # "a"는 이어쓰기 (append 모드)
        file.write(f"{current_time} - 그림: {drawing_name}\n")

def generate_report_from_today_log():
    desktop_path = os.path.expanduser("~/Desktop")
    today = datetime.now().strftime("%Y-%m-%d")

    base_dir = os.path.join(desktop_path, "미술로봇 사용현황")
    log_file = os.path.join(base_dir, f"{today}.txt")

    # 로그가 없으면 보고서 생성 불가
    if not os.path.exists(log_file):
        print(f"[보고서] {today}.txt 로그가 없어 보고서를 생성하지 않습니다.")
        return

    drawing_counts = {}

    # ✅ 로그/보고서 모두 UTF-8 통일 권장 (save_drawing_log도 UTF-8로 맞추세요)
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if "그림: " in line:
                name = line.split("그림: ")[1].strip()
                drawing_counts[name] = drawing_counts.get(name, 0) + 1

    if not drawing_counts:
        print(f"[보고서] 로그에 그림 기록이 없어 보고서를 생성하지 않습니다.")
        return

    most_drawn = max(drawing_counts, key=drawing_counts.get)
    total_count = sum(drawing_counts.values())

    # 보고서 폴더: 미술로봇 사용현황/보고서
    report_dir = os.path.join(base_dir, "보고서")
    os.makedirs(report_dir, exist_ok=True)

    report_path = os.path.join(report_dir, f"{today}_보고서.txt")

    # 종료할 때마다 갱신(덮어쓰기)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"--- {today} 미술로봇 요약 보고서 ---\n")
        f.write(f"총 가동 횟수: {total_count}회\n")
        f.write(f"가장 많이 그린 그림: {most_drawn} ({drawing_counts[most_drawn]}회)\n")

    print(f"[보고서] 생성/갱신 완료: {report_path}")


# =========================================================
# DO_0(BUSY) 1→0 감지되면 DI 초기화
# =========================================================
class BusyEdgeResetter:
    """
    DO_0(BUSY, coil 7) 1→0 감지 시 DI_0~DI_6 전부 OFF(0)
    페이지 전환은 관여하지 않음
    """
    def __init__(self, ctx, poll_ms: int = 100, parent=None):
        self.ctx = ctx
        self.prev_busy = 0
        self.seen_busy_1 = False

        self.timer = QTimer(parent)
        self.timer.timeout.connect(self.poll)
        self.timer.start(poll_ms)

    def poll(self):
        try:
            busy = get_do(self.ctx, DO0_BUSY_ADDR)
        except Exception:
            return

        if busy == 1:
            self.seen_busy_1 = True

        # ✅ 하강엣지(1→0)에서만 초기화
        if self.seen_busy_1 and self.prev_busy == 1 and busy == 0:
            try:
                reset_all_di(self.ctx)
            except Exception:
                pass
            self.seen_busy_1 = False

        self.prev_busy = busy

class PreviewCanvas(QWidget):
    """
    간단한 선분 시뮬레이션 캔버스
    - item_id 별로 미리 정의된 선분(segments)을
    - progress(0.0~1.0)에 맞춰 순차적으로 그려줌
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.item_id = None
        self.progress = 0.0

        CANVAS_SIZE = 600   # ← 원하는 크기
        self.setFixedSize(CANVAS_SIZE, CANVAS_SIZE)

        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.setStyleSheet("""
            background-color: white;
            border: 2px solid #4FC3F7;
            border-radius: 12px;
        """)

        # 선분 데이터: (x1,y1,x2,y2) 를 0~1 정규화 좌표로 저장
        self.SHAPES = {
            "tri": [
                (0.2, 0.75, 0.5, 0.25),
                (0.5, 0.25, 0.8, 0.75),
                (0.8, 0.75, 0.2, 0.75),
            ],
            "rect": [
                (0.25, 0.25, 0.75, 0.25),
                (0.75, 0.25, 0.75, 0.75),
                (0.75, 0.75, 0.25, 0.75),
                (0.25, 0.75, 0.25, 0.25),
            ],
            "circle": self._circle_segments(n=60),
            "heart": self._approx_heart_segments(n=60),
            "star": self._approx_star_segments(),
            "cat": self._approx_cat_segments(),
        }

    def _circle_segments(self, n=60, cx=0.5, cy=0.5, r=0.28):
        pts = []
        for i in range(n + 1):
            t = 2.0 * 3.1415926535 * i / n
            x = cx + r * (math.cos(t))
            y = cy + r * (math.sin(t))
            pts.append((x, y))
        return [(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]) for i in range(len(pts)-1)]

    def set_item(self, item_id: str):
        self.item_id = item_id
        self.progress = 0.0
        self.update()

    def set_progress(self, p: float):
        self.progress = max(0.0, min(1.0, float(p)))
        self.update()


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        # 배경
        painter.fillRect(self.rect(), QColor("#ffffff"))

        # 테두리
        pen_border = QPen(QColor("#d0d0d0"))
        pen_border.setWidth(2)
        painter.setPen(pen_border)
        painter.drawRoundedRect(self.rect().adjusted(6, 6, -6, -6), 18, 18)

        if not self.item_id or self.item_id not in self.SHAPES:
            return

        # ✅ cat은 귀/수염 선분을 메서드에서 생성
        if self.item_id == "cat":
            segs = self._approx_cat_segments()
        else:
            segs = self.SHAPES[self.item_id]

        if not segs:
            return

        # 그릴 선 개수 (progress 비율에 따라)
        total = len(segs)
        k = int(total * self.progress)

        pen = QPen(QColor("#039BE5"))
        pen.setWidth(6)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)

        # 실제 좌표 변환(패딩) - 정사각형 기준 + 가운데 정렬
        w = self.width()
        h = self.height()
        pad = 28
        side = max(1, min(w, h) - pad * 2)

        # 정사각형을 가운데 배치하기 위한 오프셋
        ox = (w - side) / 2
        oy = (h - side) / 2

        def map_pt(x, y):
            return QPointF(ox + x * side, oy + y * side)
        
        # ✅ cat 얼굴 원(정원) 먼저 그리기
        #if self.item_id == "cat":
            #center = map_pt(0.50, 0.55)
            #r = 0.28 * side
            #painter.drawEllipse(QRectF(center.x() - r, center.y() - r, 2 * r, 2 * r))

        # 완전 선분 k개
        for i in range(k):
            x1, y1, x2, y2 = segs[i]
            p1 = map_pt(x1, y1)
            p2 = map_pt(x2, y2)
            painter.drawLine(p1, p2)

        # 다음 선분을 “부분적으로” 그려서 더 자연스럽게
        # (k < total 일 때, k번째 선분의 일부만)
        if k < total:
            x1, y1, x2, y2 = segs[k]
            p1 = map_pt(x1, y1)
            p2 = map_pt(x2, y2)

            # 부분비율: (progress*total - k)
            frac = (self.progress * total) - k
            frac = max(0.0, min(1.0, frac))
            mid = QPointF(p1.x() + (p2.x() - p1.x()) * frac,
                          p1.y() + (p2.y() - p1.y()) * frac)
            painter.drawLine(p1, mid)



        # ---------- 아래는 간단한 근사 도형 생성 함수들 ----------

    def _approx_heart_segments(self, n=60):
        segs = []
        pts = []
        # 하트 parametric (정규화)
        for i in range(n + 1):
            t = 2 * math.pi * i / n
            x = 16 * math.sin(t)**3
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            # 스케일/정규화
            x = 0.5 + (x / 34.0) * 0.55
            y = 0.55 - (y / 34.0) * 0.55
            pts.append((x, y))
        for i in range(n):
            segs.append((*pts[i], *pts[i+1]))
        return segs

    def _approx_star_segments(self):
        # 5각 별(간단)
        pts = [
            (0.50, 0.20),
            (0.60, 0.45),
            (0.85, 0.45),
            (0.65, 0.60),
            (0.75, 0.85),
            (0.50, 0.70),
            (0.25, 0.85),
            (0.35, 0.60),
            (0.15, 0.45),
            (0.40, 0.45),
            (0.50, 0.20),
        ]
        return [(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1]) for i in range(len(pts)-1)]

    def _subdivide_line(self, x1, y1, x2, y2, parts=10):
        """긴 선을 parts 개로 쪼개서 동일한 속도로 그려지게 함"""
        segs = []
        for i in range(parts):
            t1 = i / parts
            t2 = (i + 1) / parts
            sx1 = x1 + (x2 - x1) * t1
            sy1 = y1 + (y2 - y1) * t1
            sx2 = x1 + (x2 - x1) * t2
            sy2 = y1 + (y2 - y1) * t2
            segs.append((sx1, sy1, sx2, sy2))
        return segs


    def _approx_circle_segments(self, cx=0.5, cy=0.55, r=0.22, n=80):
        
        segs = []
        for i in range(n):
            t1 = 2 * math.pi * i / n
            t2 = 2 * math.pi * (i + 1) / n
            x1 = cx + r * math.cos(t1)
            y1 = cy + r * math.sin(t1)
            x2 = cx + r * math.cos(t2)
            y2 = cy + r * math.sin(t2)
            segs.append((x1, y1, x2, y2))
        return segs


    def _approx_cat_segments(self):
        segs = []

        # 1) 얼굴 원: 한 번 추가 
        # 귀랑 붙이려면 cy를 조금 올리고, r을 조금 키우는 편이 자연스러움
        segs += self._approx_circle_segments(cx=0.5, cy=0.56, r=0.23, n=90)

        # 2) 수염 - 각 선을 쪼개서 속도 맞추기
        # 고양이 느낌으로 약간 기울임
        whisk_parts = 10
        segs.extend(self._subdivide_line(0.30, 0.56, 0.08, 0.50, parts=whisk_parts))
        segs.extend(self._subdivide_line(0.30, 0.60, 0.08, 0.60, parts=whisk_parts))
        segs.extend(self._subdivide_line(0.30, 0.64, 0.08, 0.70, parts=whisk_parts))

        segs.extend(self._subdivide_line(0.70, 0.56, 0.92, 0.50, parts=whisk_parts))
        segs.extend(self._subdivide_line(0.70, 0.60, 0.92, 0.60, parts=whisk_parts))
        segs.extend(self._subdivide_line(0.70, 0.64, 0.92, 0.70, parts=whisk_parts))

        # 3) 귀(삼각형) - 선을 쪼개서 속도 맞추기
        # 귀를 원과 붙이려면 y를 약간 내리거나(큰 y), 원의 cy/r을 조정해야함
        # 아래는 귀 밑변이 원 위쪽에 닿도록 좌표를 조정한 예시
        left_ear = [(0.38, 0.36), (0.34, 0.25), (0.43, 0.34)]
        right_ear = [(0.62, 0.36), (0.65, 0.25), (0.57, 0.34)]

        def add_poly(points, parts=8):
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]
                segs.extend(self._subdivide_line(x1, y1, x2, y2, parts=parts))

        add_poly(left_ear, parts=8)
        add_poly(right_ear, parts=8)

        return segs

# =========================
# 공통: "카드 버튼" 위젯
# =========================
class SelectCard(QFrame):
    def __init__(self, item_id: str, title: str, subtitle: str = "", on_click=None):
        super().__init__()
        self.item_id = item_id
        self.title = title
        self.on_click = on_click

        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("card")
        self.setProperty("selected", False)

        self.setStyleSheet("""
            QFrame#card {
                border: 2px solid #cfcfcf;
                border-radius: 16px;
                background: #ffffff;
            }
            QFrame#card[selected="true"] {
                border: 3px solid #2f6fed;
                background: #eef4ff;
            }
            QLabel#title {
                font-size: 26px;
                font-weight: 700;
            }
            QLabel#sub {
                font-size: 16px;
                color: #666;
            }
        """)

        v = QVBoxLayout(self)
        v.setContentsMargins(18, 18, 18, 18)
        v.setSpacing(8)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("title")
        self.lbl_title.setAlignment(Qt.AlignCenter)

        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setObjectName("sub")
        self.lbl_sub.setAlignment(Qt.AlignCenter)

        v.addStretch(1)
        v.addWidget(self.lbl_title)
        if subtitle:
            v.addWidget(self.lbl_sub)
        v.addStretch(1)

        # ✅ 정사각형 카드 고정
        CARD_SIZE = 240
        self.setFixedSize(CARD_SIZE, CARD_SIZE)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_selected(self, is_selected: bool):
        self.setProperty("selected", is_selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if callable(self.on_click):
            self.on_click(self.item_id)



# =========================
# 1) 메인 페이지
# =========================
class MainPage(QWidget):
    def __init__(self, go_select_page, image_path: str):
        super().__init__()
        self.go_select_page = go_select_page

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.bg = QLabel()
        self.bg.setAlignment(Qt.AlignCenter)
        self.bg.setStyleSheet("background-color: black;")
        root.addWidget(self.bg)

        pix = QPixmap(image_path)
        if not pix.isNull():
            self.bg.setPixmap(pix)
            self.bg.setScaledContents(True)
        else:
            self.bg.setText("메인 배경 이미지 로딩 실패\n경로를 확인하세요.")
            self.bg.setStyleSheet("color: white; font-size: 24px; background-color: black;")

        self.bg.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def mousePressEvent(self, event):
        self.go_select_page()


# =========================
# 2) 그림 선택 페이지
# =========================
class SelectPage(QWidget):
    def __init__(self, go_main, go_waiting, ctx):
        super().__init__()
        self.go_main = go_main
        self.go_waiting = go_waiting
        self.ctx = ctx

        # ✅ 선택 id -> DI 주소
        self.ITEM_TO_DI_ADDR = {
            "tri": 0,
            "rect": 1,
            "circle": 2,
            "heart": 3,
            "star": 4,
            "cat": 5          
        }

        self.categories = {
            "shape": [
                {"id": "tri", "label": "세모", "sub": ""},
                {"id": "rect", "label": "네모", "sub": ""},
                {"id": "circle", "label": "동그라미", "sub": ""},
                {"id": "heart", "label": "하트", "sub": ""},
                {"id": "star", "label": "별", "sub": ""},
            ],
            "animal": [
                {"id": "cat", "label": "고양이", "sub": ""}            
            ],
        }

        self.current_category = "shape"
        self.selected_id = None
        self.card_map = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # =========================
        # 상단 헤더 바 
        # =========================
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("background-color: #4FC3F7;")

        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(18, 12, 18, 12)
        header_lay.setSpacing(0)

        self.btn_home = QPushButton()
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setFixedSize(64, 64)
        self.btn_home.setStyleSheet("border: none; background: transparent;")

        home_img_path = resource_path(os.path.join('images', 'home.png'))
        pix = QPixmap(home_img_path)
        if not pix.isNull():
            self.btn_home.setIcon(QIcon(pix))
            self.btn_home.setIconSize(QSize(36, 36))
        else:
            self.btn_home.setText("HOME")
            self.btn_home.setStyleSheet("color:white; font-weight:900; border:none; background:transparent;")

        self.btn_home.clicked.connect(self.go_main)

        self.lbl_title = QLabel("Art Robo")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("color: white; font-size: 44px; font-weight: 900;")

        right_dummy = QWidget()
        right_dummy.setFixedSize(64, 64)

        header_lay.addWidget(self.btn_home, 0, Qt.AlignLeft)
        header_lay.addStretch(1)
        header_lay.addWidget(self.lbl_title, 0, Qt.AlignCenter)
        header_lay.addStretch(1)
        header_lay.addWidget(right_dummy, 0, Qt.AlignRight)

        root.addWidget(header)

        # =========================
        # 탭(도형/동물) 영역
        # =========================
        tab_wrap = QFrame()
        tab_wrap.setFixedHeight(70)
        tab_wrap.setStyleSheet("background-color: #4FC3F7;")

        tab_lay = QHBoxLayout(tab_wrap)
        tab_lay.setContentsMargins(18, 0, 18, 12)
        tab_lay.setSpacing(12)

        self.btn_tab_shape = QPushButton("도형")
        self.btn_tab_animal = QPushButton("동물")

        for b in (self.btn_tab_shape, self.btn_tab_animal):
            b.setCursor(Qt.PointingHandCursor)
            b.setFixedHeight(56)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.btn_tab_shape.setStyleSheet(self._tab_style(selected=True))
        self.btn_tab_animal.setStyleSheet(self._tab_style(selected=False))

        self.btn_tab_shape.clicked.connect(lambda: self.switch_category("shape"))
        self.btn_tab_animal.clicked.connect(lambda: self.switch_category("animal"))

        tab_lay.addWidget(self.btn_tab_shape, 1)
        tab_lay.addWidget(self.btn_tab_animal, 1)

        root.addWidget(tab_wrap)

        # =========================
        # 본문(카드 그리드) 영역
        # =========================
        content = QFrame()
        content.setStyleSheet("background-color: #f3f3f3;")
        content_lay = QVBoxLayout(content)
        content_lay.setContentsMargins(18, 18, 18, 18)
        content_lay.setSpacing(18)

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(18)
        self.grid.setVerticalSpacing(18)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        content_lay.addLayout(self.grid, 1)

        # =========================
        # 하단 시작 버튼
        # =========================
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        self.btn_start = QPushButton("그리기 시작")
        self.btn_start.setFixedHeight(80)
        self.btn_start.setEnabled(False)
        self.btn_start.setStyleSheet("""
            QPushButton {
                font-size: 26px;
                font-weight: 900;
                border-radius: 18px;
                background: white;
                border: 1px solid #cfcfcf;
            }
            QPushButton:disabled {
                color: #999;
                background: #e9e9e9;
            }
        """)
        self.btn_start.clicked.connect(self.start_drawing)

        bottom.addStretch(1)
        bottom.addWidget(self.btn_start, 2)
        bottom.addStretch(1)

        content_lay.addLayout(bottom)
        root.addWidget(content, 1)

        self.render_grid()

    def _tab_style(self, selected: bool) -> str:
        if selected:
            return """
                QPushButton {
                    border: none;
                    border-top-left-radius: 14px;
                    border-top-right-radius: 14px;
                    padding: 12px 0px;
                    font-size: 22px;
                    font-weight: 900;
                    background: white;
                    color: #039BE5;
                }
            """
        return """
            QPushButton {
                border: none;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                padding: 12px 0px;
                font-size: 22px;
                font-weight: 900;
                background: rgba(255,255,255,0.45);
                color: white;
            }
        """

    def switch_category(self, key: str):
        if self.current_category == key:
            return

        self.current_category = key
        self.btn_tab_shape.setStyleSheet(self._tab_style(selected=(key == "shape")))
        self.btn_tab_animal.setStyleSheet(self._tab_style(selected=(key == "animal")))

        self.reset_selection()
        self.render_grid()

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def render_grid(self):
        self.clear_grid()
        self.card_map = {}

        items = self.categories[self.current_category]
        cols = 4

        for i, item in enumerate(items):
            r = i // cols
            c = i % cols
            card = SelectCard(
                item_id=item["id"],
                title=item["label"],
                subtitle=item.get("sub", ""),
                on_click=self.on_select
            )
            self.card_map[item["id"]] = card
            self.grid.addWidget(card, r, c)

    def on_select(self, item_id: str):
        if self.selected_id in self.card_map:
            self.card_map[self.selected_id].set_selected(False)

        self.selected_id = item_id
        self.card_map[item_id].set_selected(True)
        self.btn_start.setEnabled(True)

    def start_drawing(self):
        if not self.selected_id:
            return
        
        # 그림을 그리기 시작할 때 선택된 그림 정보를 기록
        save_drawing_log(self.selected_id)  # 선택된 그림만 기록

        # ✅ 선택된 그림에 맞는 DI만 ON (DI_0~DI_6은 주소 0~6)
        di_addr = self.ITEM_TO_DI_ADDR.get(self.selected_id, None)
        if di_addr is not None:
            set_only_one_di_on(self.ctx, di_addr)

        # ✅ 로딩바/페이지 전환은 기존 로직 그대로
        self.go_waiting(self.selected_id)

    def reset_selection(self):
        if self.selected_id in self.card_map:
            self.card_map[self.selected_id].set_selected(False)
        self.selected_id = None
        self.btn_start.setEnabled(False)


# =========================
# 3) 그리는중 대기 페이지
# =========================
class WaitingPage(QWidget):
    def __init__(self, go_done):
        super().__init__()
        self.go_done = go_done
        self.current_item_id = None

        self.expected_sec = 5.0
        self.elapsed_ms = 0
        self.tick_ms = 50

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        root.addStretch(1)

        self.info = QLabel()
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setTextFormat(Qt.RichText)
        self.info.setText("""
        <div style="font-size:50px; font-weight:800; line-height:1.6;">
        로봇이 그림을 그리고 있습니다.<br>
        잠시만 기다려 주세요.
        </div>
        """)

        root.addWidget(self.info)

        self.preview = PreviewCanvas()
        root.addWidget(self.preview, 0, Qt.AlignHCenter)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(True)
        self.bar.setFixedHeight(42)
        self.bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cfcfcf;
                border-radius: 18px;
                background: #ffffff;
                font-size: 18px;
                font-weight: 800;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 18px;
                background: #4FC3F7;
            }
        """)
        root.addSpacing(28)
        root.addWidget(self.bar)
        root.addStretch(1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_tick)

        self.delay_timer = QTimer(self)
        self.delay_timer.setSingleShot(True)
        self.delay_timer.timeout.connect(self.finish)

        self._finished_once = False

    def start(self, item_id: str, expected_sec: float):
        self.current_item_id = item_id
        self.expected_sec = max(1.0, float(expected_sec))
        self.elapsed_ms = 0
        self.bar.setValue(0)
        self._finished_once = False
        self.preview.set_item(item_id)

        if self.delay_timer.isActive():
            self.delay_timer.stop()

        self.timer.start(self.tick_ms)

    def on_tick(self):
        if self._finished_once:
            return

        self.elapsed_ms += self.tick_ms
        total_ms = int(self.expected_sec * 1000)

        progress = self.elapsed_ms / total_ms

        if progress < 0.9:
            pct = int(progress / 0.9 * 90)
        else:
            slow_progress = (progress - 0.9) / 0.1
            pct = 90 + int(min(slow_progress, 1.0) * 10)

        if pct >= 100:
            pct = 100
            self.bar.setValue(100)

            self._finished_once = True
            self.timer.stop()
            self.delay_timer.start(2000)
            return

        self.bar.setValue(pct)
        self.preview.set_progress(min(progress, 1.0))

    def finish(self):
        self.go_done(self.current_item_id)


# =========================
# 4) 그림 완성 페이지
# =========================
class DonePage(QWidget):
    def __init__(self, go_main):
        super().__init__()
        self.go_main = go_main

        self.setAutoFillBackground(True)
        pal = self.palette()
        pal.setColor(QPalette.Window, QColor("white"))
        self.setPalette(pal)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(24)

        root.addStretch(1)

        self.img = QLabel()
        self.img.setAlignment(Qt.AlignCenter)

        last_img_path = resource_path(os.path.join('images', 'last.png'))
        pix = QPixmap(last_img_path)
        if not pix.isNull():
            scaled = pix.scaledToHeight(420, Qt.SmoothTransformation)
            self.img.setPixmap(scaled)
        else:
            self.img.setText("")
        root.addWidget(self.img)
        root.addSpacing(24)

        self.msg = QLabel()
        self.msg.setAlignment(Qt.AlignCenter)
        self.msg.setTextFormat(Qt.RichText)
        self.msg.setText("""
        <div style="font-size:50px; font-weight:800; line-height:1.6;">
        로봇이 그림을 완성했습니다.<br>
        종이를 가져가주세요.
        </div>
        """)
        root.addWidget(self.msg)

        self.btn_home = QPushButton("처음으로")
        self.btn_home.setFixedHeight(90)
        self.btn_home.setStyleSheet("""
            QPushButton {
                font-size: 30px;
                font-weight: 900;
                border-radius: 20px;
                background: #4FC3F7;
                color: white;
            }
            QPushButton:pressed {
                background: #29B6F6;
            }
        """)
        self.btn_home.clicked.connect(self.go_main)
        root.addWidget(self.btn_home)

        root.addStretch(1)

    def set_result(self, item_id=None, label=None):
        pass


# =========================
# 전체 윈도우 (페이지 전환)
# =========================
class KioskWindow(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.setWindowTitle("Art Robo")

        # ✅ 전체화면
        self.showFullScreen()

        self.ctx = ctx

        # ✅ 시작 시 혹시 남아있을 DI를 한번 초기화(안전)
        reset_all_di(self.ctx)

        # ✅ DO_0 1→0 감지 → DI 초기화 자동
        self.resetter = BusyEdgeResetter(self.ctx, poll_ms=100, parent=self)

        self.stack = QStackedWidget()

        main_img_path = resource_path(os.path.join('images', 'main.png'))
        self.page_main = MainPage(go_select_page=self.go_select, image_path=main_img_path)

        self.page_select = SelectPage(go_main=self.go_main, go_waiting=self.go_waiting, ctx=self.ctx)
        self.page_wait = WaitingPage(go_done=self.go_done)
        self.page_done = DonePage(go_main=self.go_main)

        self.stack.addWidget(self.page_main)   # 0
        self.stack.addWidget(self.page_select) # 1
        self.stack.addWidget(self.page_wait)   # 2
        self.stack.addWidget(self.page_done)   # 3

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)

        self.id_to_sec = {
            "tri": 11.0,
            "rect": 11.0,
            "circle": 12.0,
            "heart": 14.0,
            "star": 17.0,
            "cat": 32.0           
        }

    def go_main(self):
        self.page_select.reset_selection()
        self.stack.setCurrentIndex(0)

    def go_select(self):
        self.stack.setCurrentIndex(1)

    def go_waiting(self, item_id: str):
        sec = self.id_to_sec.get(item_id, 5.0)
        self.stack.setCurrentIndex(2)
        self.page_wait.start(item_id=item_id, expected_sec=sec)

    def go_done(self, item_id: str):
        self.stack.setCurrentIndex(3)
        self.page_done.set_result(item_id=item_id, label=None)


# DrawingHistory 클래스: 로그 파일을 직접 읽어 분석하는 방식
class DrawingHistory:
    def __init__(self):
        # ✅ 로그에 저장된 값이 tri/rect/... 이면 보고서에서 한글로 바꿔서 집계/출력
        self.ID_TO_KR = {
            "tri": "세모",
            "rect": "네모",
            "circle": "동그라미",
            "heart": "하트",
            "star": "별",
            "cat": "고양이"
        }

    def generate_report(self):
        desktop_path = os.path.expanduser("~/Desktop")
        today = datetime.now().strftime("%Y-%m-%d")
        base_dir = os.path.join(desktop_path, "미술로봇 사용현황")
        log_file = os.path.join(base_dir, f"{today}.txt")

        # 1) 오늘 로그 파일 존재 확인
        if not os.path.exists(log_file):
            print(f"{today}의 로그 파일이 없어 보고서를 생성하지 않습니다.")
            return

        drawing_counts = {}
        hour_counts = {}  # 예: {10:3, 11:2, 12:5}
        
        try:
            # 2) 파일 읽기
            with open(log_file, "r", encoding="utf-8-sig") as file:
                for line in file:
                    if "그림: " in line:
                        # ✅ 1) 시간대 집계: "YYYY-MM-DD HH:MM:SS - 그림: ..."
                        try:
                            dt_str = line.split(" - ")[0].strip()  # "2025-12-18 11:29:13"
                            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                            h = dt.hour
                            hour_counts[h] = hour_counts.get(h, 0) + 1
                        except:
                            pass

                        # ✅ 2) 그림명 집계
                        raw = line.split("그림: ")[1].strip()      # tri 또는 세모 등
                        name = self.ID_TO_KR.get(raw, raw)         # tri면 세모로 변환, 아니면 그대로
                        drawing_counts[name] = drawing_counts.get(name, 0) + 1

            if not drawing_counts:
                print("로그는 있으나 집계할 그림 기록이 없습니다.")
                return


            # 3) 통계 계산
            total_count = sum(drawing_counts.values())

            # 시간대 분석 (동률이면 모두 표시)
            most_used_time_text = "기록 없음"
            if hour_counts:
                max_hour_cnt = max(hour_counts.values())
                top_hours = sorted([h for h, v in hour_counts.items() if v == max_hour_cnt])

                # 예: [12] -> "12시~1시 사이"
                # 예: [10,12] -> "10시~11시 사이, 12시~1시 사이"
                most_used_time_text = ", ".join([f"{h}시~{(h+1)%24}시 사이" for h in top_hours])

            max_cnt = max(drawing_counts.values())

            # 최대 횟수인 그림들 모두 추출
            top_drawings = [k for k, v in drawing_counts.items() if v == max_cnt]

            # 보기 좋게 정렬 (가나다순)
            top_drawings.sort()

            # "네모, 세모" 형태로 문자열 생성
            most_drawn_text = ", ".join(top_drawings)

            # 4) 보고서 폴더 및 파일 생성 (하위폴더: 보고서)
            report_dir = os.path.join(base_dir, "보고서", today)
            os.makedirs(report_dir, exist_ok=True)

            report_path = os.path.join(report_dir, "보고서.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"--- {today} 미술로봇 요약 보고서 ---\n")
                f.write(f"총 가동 횟수: {total_count}회\n")
                f.write(f"오늘 가장 많이 그린 그림: {most_drawn_text} (각 {max_cnt}회)\n")
                f.write(f"가장 많이 이용한 시간: {most_used_time_text}\n\n")
                f.write("[그림별 사용 횟수]\n")
                for k, v in sorted(drawing_counts.items(), key=lambda x: (-x[1], x[0])):
                    f.write(f"- {k}: {v}회\n")

            print(f"보고서 생성 완료: {report_path}")

        except Exception as e:
            print(f"보고서 생성 중 오류: {e}")


def main():
    # ✅ Modbus Slave 서버 시작(PC가 서버)
    ctx = start_modbus_slave_server()

    app = QApplication(sys.argv)
    app.setFont(QFont("Malgun Gothic"))


    w = KioskWindow(ctx)
    history = DrawingHistory()
    # ✅ 프로그램 종료 직전에 오늘 로그를 읽어서 보고서 생성/갱신
    app.aboutToQuit.connect(history.generate_report)
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
