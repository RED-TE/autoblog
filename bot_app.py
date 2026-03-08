# -*- coding: utf-8 -*-
# bot_app.py — 블로그 자동화 봇 v4.0
# ══════════════════════════════════════════════════════════════
# 트랙 1 (자동): 벤치마킹 + 노출형 페르소나 전용
# 트랙 2 (반자동): 팩트 직접 입력 + 딜러형 페르소나 전용
# 두 트랙은 절대 혼합되지 않습니다.
# ══════════════════════════════════════════════════════════════

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import os, sys, json, datetime, queue, shutil, subprocess

# ── 색상 테마 ─────────────────────────────────────────────────
BG        = "#0d0f17"
BG2       = "#131621"
BG3       = "#1a1d2e"
BORDER    = "#252840"
ACCENT    = "#7c3aed"   # 보라 (트랙1: 자동)
ACCENT2   = "#4f46e5"
TEAL      = "#0d9488"   # 청록 (트랙2: 반자동)
TEAL2     = "#0f766e"
TEXT      = "#e8eaf0"
TEXT_DIM  = "#7c85a2"
GREEN     = "#34d399"
RED       = "#f87171"
YELLOW    = "#fbbf24"
BLUE      = "#60a5fa"
FONT      = ("Segoe UI", 10)
FONTB     = ("Segoe UI", 10, "bold")
FONTH     = ("Segoe UI", 11, "bold")
FONTMONO  = ("Consolas", 9)

# 어떤 방식으로 실행하든(일반, 단축아이콘 등) 무조건 스크립트가 있는 진짜 경로를 찾아 박아넣습니다.
_REAL_BASE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(_REAL_BASE, "_app_state.json")

import persona_v2

# ── 트랙별 페르소나 정의 (절대 교차 금지) ─────────────────────
EXPOSURE_PERSONAS = [
    ("search_solver",            "🔍  [V2] 검색 의도 해결사 (추천)"),
    ("comparison_expert",        "⚖️  [V2] 비교 분석 전용"),
    ("problem_solver",           "🛠️  [V2] 문제 해결 단계별 제시"),
    ("trend_tracker",            "📅  [V2] 2025 최신 트렌드/프로모션"),
    ("local_community",          "📍  [V2] 지역 커뮤니티(강남·판교 등)"),
    ("data_analyst",             "📈  [V2] 숫자·데이터 시뮬레이션"),
    ("faq_master",               "❓  [V2] Q&A 핵심 요약"),
    ("case_study",               "📖  [V2] 실제 계약 전/후 후기형"),
    ("seasonal_guide",           "❄️  [V2] 시즌(연말·명절) 대응"),
    ("series_writer",            "📚  [V2] 시리즈 연재(1편·2편)"),
    ("investigative_journalist", "🔍  [V1] 탐사 기자 (내부고발 스타일)"),
    ("sns_trendsetter",          "📸  [V1] 인플루언서 스타일"),
] + persona_v2.CUSTOM_PERSONAS_UI_LIST

DEALER_PERSONAS = [
    ("veteran_dealer",       "🎖️   [V2] 베테랑 딜러 (솔직·정직)"),
    ("company_introducer",   "🏢  [V2] 업체 브랜드 차별화 강조"),
    ("experience_sharer",    "🤝  [V2] 경험 공유 (나도 그랬는데...)"),
    ("b2b_expert",           "📈  [V2] 법인/사업자 절세 전문"),
    ("urgency_specialist",   "🚨  [V2] 긴급 마감 임박 프로모션"),
    ("risk_preventer",       "⚠️   [V2] 계약 전 주의사항 (실패방지)"),
    ("custom_designer",      "📏  [V2] 1:1 맞춤 견적 설계 전문가"),
    ("review_collector",     "🌟  [V2] 만족도 후기 소셜 프루프"),
    ("quote_comparator",     "🧾  [V2] 타사 비교 견적 자신형"),
    ("longterm_manager",     "🛠️  [V2] 계약 후 사후관리·신뢰"),
    ("veteran_dealer",       "🎖️   [V1] 시니어 딜러 (15년 경력)"),
    ("young_specialist",     "📱  [V1] 디지털 딜러 (비대면 전문)"),
    ("corporate_specialist", "🏢  [V1] 법인 리스 전문가"),
    ("honest_advisor",       "🤝  [V1] 솔직한 어드바이저"),
    ("luxury_import_dealer", "💎  [V1] 수입 럭셔리 전문 딜러"),
] + persona_v2.CUSTOM_PERSONAS_UI_LIST


class BotApp(tk.Tk):
    def __init__(self, plan_obj=None):
        import updater
        if updater.check_and_apply_update():
            # 업데이트가 적용됨 -> 재시작
            from tkinter import messagebox
            messagebox.showinfo("업데이트 완료", "최신 버전 패치가 완료되었습니다.\n확인을 누르면 프로그램을 재시작합니다.")
            # 윈도우 환경에서 파이썬 스크립트 재실행
            import sys, os
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        super().__init__()
        self.plan_obj = plan_obj
        self.title("블로그 자동화 봇  v4.0")
        self.geometry("1080x800")
        self.minsize(900, 640)
        self.configure(bg=BG)
        self.resizable(True, True)
        try: self.iconbitmap(default="")
        except: pass

        self.process   = None
        self.log_queue = queue.Queue()
        self.running   = False
        self._loading  = False   # _load_state 중 _save_state 차단용
        
        # 다중 계정 상태
        self.accounts = [{}]
        self.active_acc_idx = 0

        # 공통
        self.var_naver_id  = tk.StringVar()
        self.var_naver_pw  = tk.StringVar()
        self.var_pause     = tk.BooleanVar(value=False)
        self.var_test_mode = tk.BooleanVar(value=False)

        # ── [NEW] 계정 간 대기 시간 (딜레이) 설정 ──
        self.var_acc_delay_min = tk.IntVar(value=60)
        self.var_acc_delay_max = tk.IntVar(value=120)
        self.var_acc_delay_skip = tk.BooleanVar(value=False)  # 즉시 실행 여부

        # 트랙 1 (자동)
        self.t1_images    = []
        self.var_t1_kw    = tk.StringVar()
        self.var_t1_car_model = tk.StringVar()
        self.var_t1_tags  = tk.StringVar()
        self.var_t1_biz   = tk.StringVar()
        self.var_t1_must_phrase = tk.StringVar()
        self.var_t1_must_pos_top = tk.BooleanVar(value=True)
        self.var_t1_must_pos_mid = tk.BooleanVar(value=False)
        self.var_t1_must_pos_bot = tk.BooleanVar(value=False)
        self.var_t1_count = tk.IntVar(value=5)
        self.var_t1_persona = tk.StringVar(value="random_exposure")
        self.var_t1_watermark_enable = tk.BooleanVar(value=True)
        self.var_t1_watermark_text = tk.StringVar(value="")
        self.t1_link_image = []
        self.var_t1_link_pos = tk.StringVar(value="하단")
        self.var_t1_image_link = tk.StringVar(value="")
        self.var_t1_schedule_publish = tk.BooleanVar(value=False)
        self.var_t1_schedule_date = tk.StringVar(value="")  # "2026. 03. 01"
        self.var_t1_schedule_hour = tk.StringVar(value="14")
        self.var_t1_schedule_min  = tk.StringVar(value="00")
        self.var_t1_post_length   = tk.StringVar(value="일반형 (1500~1800자)")
        self.var_t1_align         = tk.StringVar(value="기본")
        self.var_t1_advanced_format = tk.BooleanVar(value=True)

        # 트랙 2 (반자동)
        self.t2_images    = []
        self.var_t2_tags  = tk.StringVar(value="")
        self.var_t2_biz   = tk.StringVar(value="")
        self.var_t2_car_model = tk.StringVar()
        self.var_t2_title = tk.StringVar()
        self.var_t2_must_phrase = tk.StringVar()
        self.var_t2_must_pos_top = tk.BooleanVar(value=True)
        self.var_t2_must_pos_mid = tk.BooleanVar(value=False)
        self.var_t2_must_pos_bot = tk.BooleanVar(value=False)
        self.var_t2_persona = tk.StringVar(value="veteran_dealer")
        self.var_t2_content_type = tk.StringVar(value="inquiry")  # 후기형 | 문의전환형
        self.var_t2_watermark_enable = tk.BooleanVar(value=True)
        self.var_t2_watermark_text = tk.StringVar(value="")
        self.t2_link_image = []
        self.var_t2_link_pos = tk.StringVar(value="하단")
        self.var_t2_image_link = tk.StringVar(value="")
        self.var_t2_schedule_publish = tk.BooleanVar(value=False)
        self.var_t2_schedule_date = tk.StringVar(value="")  # "2026. 03. 01"
        self.var_t2_schedule_hour = tk.StringVar(value="14")
        self.var_t2_schedule_min  = tk.StringVar(value="00")
        self.var_t2_post_length   = tk.StringVar(value="일반형 (1500~1800자)")
        self.var_t2_align         = tk.StringVar(value="기본")
        self.var_t2_advanced_format = tk.BooleanVar(value=True)

        self._build_ui()
        self._load_state()
        self._poll_logs()

        # !! 중요: FocusOut + AutoSave 바인딩은 _load_state()가 완전히 끝난
        # 직후에야 활성화해야 합니다. 앱 시작 시 빈값 덮어쓰기(Race Condition) 방지!
        self.after(500, self._activate_save_bindings)

    def _on_closing(self):
        """앱 완전 종료 전 상태 강제 저장"""
        self._save_state()
        self.destroy()

    def _activate_save_bindings(self):
        """_load_state 완료 500ms 후 활성화 — 로드 중 빈값 개입 방지"""
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        # 15초 주기 자동저장 루프 시작
        self._auto_save_loop()

    def _auto_save_loop(self):
        if not self._loading:
            self._save_state()
        self.after(15000, self._auto_save_loop)

    # ══════════════════════════════════════════════════════════
    # UI 구성
    # ══════════════════════════════════════════════════════════
    def _build_ui(self):
        # ── 헤더 ──────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG3, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🤖  블로그 자동화 봇", font=("Segoe UI", 16, "bold"),
                 bg=BG3, fg=TEXT).pack(side="left", padx=20)
        self.status_lbl = tk.Label(hdr, text="● 대기 중", font=FONTB,
                                   bg=BG3, fg=TEXT_DIM)
        self.status_lbl.pack(side="right", padx=20)

        # ── 탭 버튼 ───────────────────────────────────────────
        tab_bar = tk.Frame(self, bg=BG2, pady=0)
        tab_bar.pack(fill="x")
        self.tab_track1_btn = tk.Button(
            tab_bar, text="⚡  트랙 1 — 완전 자동  (벤치마킹 + 노출 최적화)",
            font=FONTB, bg=ACCENT, fg="white",
            activebackground=ACCENT2, activeforeground="white",
            bd=0, padx=20, pady=11, cursor="hand2", relief="flat",
            command=lambda: self._switch_tab(1))
        self.tab_track1_btn.pack(side="left", fill="x", expand=True)

        tk.Frame(tab_bar, bg=BORDER, width=2).pack(side="left", fill="y")

        self.tab_track2_btn = tk.Button(
            tab_bar, text="✍️  트랙 2 — 반자동  (직접 입력 + 딜러형 신뢰 구축)",
            font=FONTB, bg=BG3, fg=TEXT_DIM,
            activebackground=TEAL2, activeforeground="white",
            bd=0, padx=20, pady=11, cursor="hand2", relief="flat",
            command=lambda: self._switch_tab(2))
        self.tab_track2_btn.pack(side="left", fill="x", expand=True)

        # ── 본체 ──────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=10)
        body.columnconfigure(0, weight=4)
        body.columnconfigure(1, weight=5)
        # body.rowconfigure(0, weight=1) -> acc_bar
        body.rowconfigure(1, weight=1)

        # ── 다중 계정 탭 바 (상단) ──────────────────────────────────
        self.acc_bar = tk.Frame(body, bg=BG2)
        self.acc_bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # 왼쪽 (스크롤)
        left = tk.Frame(body, bg=BG)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        right = tk.Frame(body, bg=BG)
        right.grid(row=1, column=1, sticky="nsew")

        canvas = tk.Canvas(left, bg=BG, bd=0, highlightthickness=0)
        sb = tk.Scrollbar(left, orient="vertical", command=canvas.yview)
        self.sf = tk.Frame(canvas, bg=BG)
        self.sf.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # 트랙 패널
        self.panel_t1 = tk.Frame(self.sf, bg=BG)
        self.panel_t2 = tk.Frame(self.sf, bg=BG)

        self._build_account_card(self.sf)   # 공통 계정 카드
        self._build_track1(self.panel_t1)
        self._build_track2(self.panel_t2)
        self._build_log(right)

        self._apply_plan_restrictions() # [NEW] 라이트/프로 권한 제한 적용

        self._switch_tab(1)  # 기본값: 트랙 1

    # [NEW] 플랜 제한 적용 함수
    def _apply_plan_restrictions(self):
        if not self.plan_obj or self.plan_obj.name != "라이트(도구)":
            return
            
        print("   🔒 [Lite Plan] 기능 제한 (UI Lock) 활성화")
        
        # 1. 포스트 길이 고정
        self.var_t1_post_length.set("간편형 (800~1000자)")
        self.var_t2_post_length.set("간편형 (800~1000자)")
        self.cb1_t1.config(state="disabled")
        self.cb2_t2.config(state="disabled")
        
        # 2. 벤치마킹 개수 고정
        self.var_t1_count.set(1)
        self.t1_count_lbl.config(text="1개 (LITE 고정)", fg=RED)
        self.t1_count_scale.config(state="disabled")
        
        # 3. 워터마크 비활성화
        self.var_t1_watermark_enable.set(False)
        self.var_t2_watermark_enable.set(False)
        self.t1_watermark_chk.config(state="disabled")
        self.t2_watermark_chk.config(state="disabled")
        self.t1_watermark_text_lbl.config(fg=TEXT_DIM, text="🖋️ 워터마크 문구 (LITE 불가)")
        self.t2_watermark_text_lbl.config(fg=TEXT_DIM, text="🖋️ 워터마크 문구 (LITE 불가)")
        self.t1_watermark_text_entry.config(state="disabled", fg=TEXT_DIM)
        self.t2_watermark_text_entry.config(state="disabled", fg=TEXT_DIM)
        
        # 4. 이미지 링크 비활성화
        self.t1_link_img_btn.config(state="disabled")
        self.t2_link_img_btn.config(state="disabled")
        self.t1_link_url_lbl.config(fg=TEXT_DIM)
        self.t2_link_url_lbl.config(fg=TEXT_DIM)
        self.t1_link_url_entry.config(state="disabled", fg=TEXT_DIM)
        self.t2_link_url_entry.config(state="disabled", fg=TEXT_DIM)
        for rb in self.t1_link_pos_rbs + self.t2_link_pos_rbs:
            rb.config(state="disabled")
            
        # 5. 예약 발행 비활성화
        self.var_t1_schedule_publish.set(False)
        self.var_t2_schedule_publish.set(False)
        self.t1_schedule_chk.config(state="disabled", text=" 🕰️ 예약 발행 (LITE 불가)")
        self.t2_schedule_chk.config(state="disabled", text=" 🕰️ 예약 발행 (LITE 불가)")
        
        # 6. 트랙 2 사용 불가 알림 (라벨 등을 변경하거나 _switch_tab에서 이미 막음)
        self.tab_track2_btn.config(text="✍️  트랙 2 — 반자동 (PRO 전용)")

    # ── 공통 계정 카드 ─────────────────────────────────────────
    def _build_account_card(self, parent):
        c = self._card(parent, "🔐  네이버 계정  (공통)")
        self._lbl(c, "아이디"); self._entry(c, self.var_naver_id)
        self._lbl(c, "비밀번호"); self._entry(c, self.var_naver_pw)

    # ══════════════════════════════════════════════════════════
    # 트랙 1 — 완전 자동
    # 벤치마킹 필수 / 노출형 페르소나만 / 딜러형 절대 금지
    # ══════════════════════════════════════════════════════════
    def _build_track1(self, parent):
        banner = tk.Label(parent,
            text="⚡  트랙 1: 키워드 → 상위 블로그 분석 → 노출 최적화 발행",
            font=("Segoe UI", 9, "bold"), bg="#1a1030", fg="#c4b5fd",
            pady=6, padx=12, anchor="w")
        banner.pack(fill="x", pady=(0, 8))

        # 포스팅 설정
        c1 = self._card(parent, "🔍  검색 설정")
        self._lbl(c1, "키워드 (벤치마킹 검색어)")
        self._entry_watch(c1, self.var_t1_kw)
        self._lbl(c1, "🚘 차종 (예: 쏘렌토 하이브리드)")
        self._entry_watch(c1, self.var_t1_car_model)
        self._lbl(c1, "🏢 업체명 (AI에 자동 반영)")
        self._entry_watch(c1, self.var_t1_biz)
        
        # [NEW] 필수 포함 문구 통합 UI
        self._lbl(c1, "🧩 필수 포함 문구 (AI가 글에 삽입)")
        self._entry_watch(c1, self.var_t1_must_phrase)
        pos_f1 = tk.Frame(c1, bg=BG2)
        pos_f1.pack(fill="x", pady=(2, 6))
        tk.Label(pos_f1, text="위치 선택:", font=("Segoe UI", 8), bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 10))
        for text, var in [("상단", self.var_t1_must_pos_top), ("중간", self.var_t1_must_pos_mid), ("하단", self.var_t1_must_pos_bot)]:
            tk.Checkbutton(pos_f1, text=text, variable=var, bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=("Segoe UI", 8), command=self._save_state).pack(side="left", padx=5)

        self._lbl(c1, "🏷️  필수태그 (쉼표 구분)")
        self._entry_watch(c1, self.var_t1_tags)
        self._lbl(c1, "📝 글 분량 (권장: 일반형)")
        length_opts = ["간편형 (800~1000자)", "일반형 (1500~1800자)", "정보형 (2000~2700자)"]
        self.cb1_t1 = tk.OptionMenu(c1, self.var_t1_post_length, *length_opts, command=lambda _: self._save_state())
        self.cb1_t1.config(bg=BG3, fg=TEXT, activebackground=BG2, activeforeground=TEXT, bd=0, highlightthickness=1, highlightbackground=BORDER, font=FONT, cursor="hand2")
        self.cb1_t1["menu"].config(bg=BG2, fg=TEXT, font=FONT)
        self.cb1_t1.pack(fill="x", pady=(0, 6), ipady=2)
        
        # [NEW] 상세 에디터 포맷팅
        row_fmt1 = tk.Frame(c1, bg=BG2)
        row_fmt1.pack(fill="x", pady=(4, 6))
        tk.Label(row_fmt1, text="🔠 정렬:", font=FONTB, bg=BG2, fg=TEXT).pack(side="left")
        for align_opt in ["기본", "왼쪽", "가운데", "오른쪽"]:
            tk.Radiobutton(row_fmt1, text=align_opt, variable=self.var_t1_align, value=align_opt,
                           bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=FONT,
                           command=self._save_state).pack(side="left", padx=(4, 8))
        
        tk.Checkbutton(c1, text=" 상세 서식 자동화 (동그라미/숫자 목록, 표 3x3 자동 삽입)",
                       variable=self.var_t1_advanced_format, bg=BG2, fg=TEAL,
                       activebackground=BG2, selectcolor=BG3, font=FONTB,
                       cursor="hand2", command=self._save_state).pack(anchor="w", pady=(0, 6))
        
        self._lbl(c1, "📋 벤치마킹 블로그 수 (최대 3개)")
        row = tk.Frame(c1, bg=BG2); row.pack(fill="x")
        self.t1_count_lbl = tk.Label(row, text=f"{self.var_t1_count.get()}개",
                                     font=FONTB, bg=BG2, fg=ACCENT, width=4)
        self.t1_count_lbl.pack(side="right")
        self.t1_count_scale = tk.Scale(row, from_=1, to=3, orient="horizontal", variable=self.var_t1_count,
                 bg=BG2, fg=TEXT, highlightthickness=0,
                 troughcolor=BG3, activebackground=ACCENT,
                 sliderrelief="flat", bd=0,
                 command=lambda v: (
                     self.t1_count_lbl.config(text=f"{int(float(v))}개"),
                     self._save_state()
                 ))
        self.t1_count_scale.pack(side="left", fill="x", expand=True)

        # 페르소나 선택
        c2 = self._card(parent, "🎭  페르소나 선택")
        all_opts = [("random_exposure", "🎲  랜덤 (5종 자동 순환)")] + EXPOSURE_PERSONAS
        
        # [NEW] 라이트 플랜인 경우 5개로 제한 (사용자 요청)
        if self.plan_obj and self.plan_obj.name == "라이트(도구)":
            all_opts = [
                ("random_exposure", "🎲  랜덤 (5종 자동 순환)"),
                ("search_solver", "🔍  [V2] 검색 의도 해결사 (추천)"),
                ("comparison_expert", "⚖️  [V2] 비교 분석 전용"),
                ("problem_solver", "🛠️  [V2] 문제 해결 단계별 제시"),
                ("trend_tracker", "📅  [V2] 2025 최신 트렌드/프로모션")
            ]
            
        self.t1_persona_rbs = []
        for val, lbl in all_opts:
            rb = tk.Radiobutton(c2, text=lbl, variable=self.var_t1_persona, value=val,
                                bg=BG2, fg=TEXT, activebackground=BG2, selectcolor=BG3,
                                font=FONT, cursor="hand2", anchor="w",
                                command=self._save_state)
            rb.pack(fill="x", ipady=2)
            self.t1_persona_rbs.append(rb)
        
        # [V2 추가] 페르소나 치트시트 & 커스텀 추가 버튼
        btn_f1 = tk.Frame(c2, bg=BG3)
        btn_f1.pack(fill="x", pady=(8, 0))
        tk.Button(btn_f1, text="💡 어떤 페르소나를 선택할까요? (치트시트)", font=("Segoe UI", 8),
                  bg=BG3, fg=ACCENT, bd=0, cursor="hand2", anchor="w",
                  command=self._show_cheat_sheet).pack(side="left", fill="x", expand=True)
        if self.plan_obj and self.plan_obj.name != "라이트(도구)":
            tk.Button(btn_f1, text="📂 커스텀 페르소나 (TXT)", font=("Segoe UI", 8),
                      bg=BORDER, fg="white", bd=0, cursor="hand2", anchor="e",
                      command=self._open_personas_folder).pack(side="right")

        # 이미지
        c3 = self._card(parent, "📷  이미지 및 안티봇 세탁")
        tk.Button(c3, text="+ 이미지 선택 (최대 10개)", font=FONT, bg=BG3, fg=TEXT,
                  activebackground=BORDER, bd=0, padx=10, pady=6,
                  cursor="hand2", relief="flat",
                  command=lambda: self._select_images(1)).pack(fill="x")
        self.t1_img_lbl = tk.Label(c3, text="선택된 이미지 없음",
                                   font=FONT, bg=BG2, fg=TEXT_DIM, anchor="w")
        self.t1_img_lbl.pack(fill="x", pady=(4, 0))
        
        # 워터마크 프레임
        wm_f1 = tk.Frame(c3, bg=BG2)
        wm_f1.pack(fill="x", pady=(6, 2))
        self.t1_watermark_chk = tk.Checkbutton(wm_f1, text=" 네이버 로직 우회용 이미지 세탁 적용 (크롭+회전+타일링)", 
                       variable=self.var_t1_watermark_enable,
                       bg=BG2, fg=TEXT, activebackground=BG2, selectcolor=BG3,
                       font=FONT, cursor="hand2", command=self._save_state)
        self.t1_watermark_chk.pack(side="left")
        
        self.t1_watermark_text_lbl = tk.Label(c3, text="🖋️ 워터마크 문구 (예: 신차장기렌트 전문)", font=FONTB, bg=BG2, fg=TEXT, anchor="w")
        self.t1_watermark_text_lbl.pack(fill="x", pady=(4, 2))
        self.t1_watermark_text_entry = self._entry_watch(c3, self.var_t1_watermark_text)
        c_link1 = self._card(parent, "🔗 링크 전용 특별 이미지 (1장만, 클릭 시 이동)")
        self.t1_link_img_btn = tk.Button(c_link1, text="+ 링크전용 이미지 선택", font=FONT, bg=BG3, fg=TEXT,
                  activebackground=BORDER, bd=0, padx=10, pady=6,
                  cursor="hand2", relief="flat",
                  command=lambda: self._select_link_images(1))
        self.t1_link_img_btn.pack(fill="x")
        self.t1_link_img_lbl = tk.Label(c_link1, text="선택된 이미지 없음", font=FONT, bg=BG2, fg=TEXT_DIM, anchor="w")
        self.t1_link_img_lbl.pack(fill="x", pady=(4, 0))
        
        self.t1_link_url_lbl = tk.Label(c_link1, text="이동할 URL (위 이미지 클릭 시 연결)", font=FONTB, bg=BG2, fg=TEXT, anchor="w")
        self.t1_link_url_lbl.pack(fill="x", pady=(4, 2))
        self.t1_link_url_entry = self._entry_watch(c_link1, self.var_t1_image_link)

        self.t1_link_pos_f = tk.Frame(c_link1, bg=BG2)
        self.t1_link_pos_f.pack(fill="x", pady=(4, 0))
        tk.Label(self.t1_link_pos_f, text="삽입 위치:", font=FONTB, bg=BG2, fg=TEXT, anchor="w").pack(fill="x", pady=(4, 2))
        
        self.t1_link_pos_rbs = []
        for v in ["상단", "중간", "하단"]:
            rb = tk.Radiobutton(self.t1_link_pos_f, text=v, variable=self.var_t1_link_pos, value=v,
                           bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=FONT, command=self._save_state)
            rb.pack(side="left", padx=(0,10))
            self.t1_link_pos_rbs.append(rb)

        # 발행 옵션 + 실행
        self._build_publish_options(parent, track=1)

    # ══════════════════════════════════════════════════════════
    # 트랙 2 — 반자동 (직접 입력)
    # 벤치마킹 없음 / 딜러형 페르소나만 / 노출형 절대 금지
    # ══════════════════════════════════════════════════════════
    def _build_track2(self, parent):
        banner = tk.Label(parent,
            text="✍️  트랙 2: 실제 팩트 직접 입력 → 딜러 신뢰형 발행 (벤치마킹 없음)",
            font=("Segoe UI", 9, "bold"), bg="#0f2e2b", fg="#5eead4",
            pady=6, padx=12, anchor="w")
        banner.pack(fill="x", pady=(0, 8))

        # 팩트 입력 (textarea)
        c1 = self._card(parent, "📋  핵심 팩트 직접 입력  (AI가 이것을 기반으로 글 작성)")
        tk.Label(c1, text="차종, 월 납입금, 보증금, 프로모션, 특장점, 주의사항 등 최대한 상세하게",
                 font=("Segoe UI", 8), bg=BG2, fg=TEXT_DIM, anchor="w").pack(fill="x", pady=(0, 4))
        self.t2_facts_text = tk.Text(c1, height=9, font=FONTMONO,
                                     bg="#090b12", fg=TEXT, insertbackground=TEXT,
                                     bd=0, relief="flat",
                                     highlightthickness=1, highlightbackground=BORDER,
                                     highlightcolor=TEAL, wrap="word")
        self.t2_facts_text.pack(fill="x")
        # <<Modified>>: 텍스트가 다쏌을 때 (Ctrl+V 포함) 맨 저장
        self.t2_facts_text.bind("<<Modified>>", self._on_text_modified)
        self.t2_facts_text.bind("<KeyRelease>", lambda e: self._save_state())

        # 추가 설정
        c2 = self._card(parent, "⚙️  포스팅 설정")
        self._lbl(c2, "📝 제목  (공란 → AI 자동 생성)")
        self._entry_watch(c2, self.var_t2_title)
        self._lbl(c2, "🚘 차종 (예: 쏘렌토 하이브리드)")
        self._entry_watch(c2, self.var_t2_car_model)
        self._lbl(c2, "🏢 업체명")
        self._entry_watch(c2, self.var_t2_biz)
        
        # [NEW] 필수 포함 문구 통합 UI
        self._lbl(c2, "🧩 필수 포함 문구 (AI가 글에 삽입)")
        self._entry_watch(c2, self.var_t2_must_phrase)
        pos_f2 = tk.Frame(c2, bg=BG2)
        pos_f2.pack(fill="x", pady=(2, 6))
        tk.Label(pos_f2, text="위치 선택:", font=("Segoe UI", 8), bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(0, 10))
        for text, var in [("상단", self.var_t2_must_pos_top), ("중간", self.var_t2_must_pos_mid), ("하단", self.var_t2_must_pos_bot)]:
            tk.Checkbutton(pos_f2, text=text, variable=var, bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=("Segoe UI", 8), command=self._save_state).pack(side="left", padx=5)

        self._lbl(c2, "🏷️  필수태그  (쉼표 구분)")
        self._entry_watch(c2, self.var_t2_tags)
        self._lbl(c2, "📝 글 분량 (권장: 일반형)")
        length_opts = ["간편형 (800~1000자)", "일반형 (1500~1800자)", "정보형 (2000~2700자)"]
        self.cb2_t2 = tk.OptionMenu(c2, self.var_t2_post_length, *length_opts, command=lambda _: self._save_state())
        self.cb2_t2.config(bg=BG3, fg=TEXT, activebackground=BG2, activeforeground=TEXT, bd=0, highlightthickness=1, highlightbackground=BORDER, font=FONT, cursor="hand2")
        self.cb2_t2["menu"].config(bg=BG2, fg=TEXT, font=FONT)
        self.cb2_t2.pack(fill="x", pady=(0, 6), ipady=2)

        # [NEW] 상세 에디터 포맷팅
        row_fmt2 = tk.Frame(c2, bg=BG2)
        row_fmt2.pack(fill="x", pady=(4, 6))
        tk.Label(row_fmt2, text="🔠 정렬:", font=FONTB, bg=BG2, fg=TEXT).pack(side="left")
        for align_opt in ["기본", "왼쪽", "가운데", "오른쪽"]:
            tk.Radiobutton(row_fmt2, text=align_opt, variable=self.var_t2_align, value=align_opt,
                           bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=FONT,
                           command=self._save_state).pack(side="left", padx=(4, 8))
        
        tk.Checkbutton(c2, text=" 상세 서식 자동화 (동그라미/숫자 목록, 표 3x3 자동 삽입)",
                       variable=self.var_t2_advanced_format, bg=BG2, fg=TEAL,
                       activebackground=BG2, selectcolor=BG3, font=FONTB,
                       cursor="hand2", command=self._save_state).pack(anchor="w", pady=(0, 6))

        # ── 콘텐츠 유형 서브탭 ──────────────────────────────────
        ct_card = self._card(parent, "✏️  콘텐츠 유형 선택")

        # 서브탭 버튼 바
        ct_bar = tk.Frame(ct_card, bg=BG2)
        ct_bar.pack(fill="x", pady=(0, 8))
        self.ct_btn_inquiry = tk.Button(
            ct_bar, text="💬  문의 전환형",
            font=FONTB, bg=TEAL, fg="white",
            activebackground=TEAL2, bd=0, padx=12, pady=7,
            cursor="hand2", relief="flat",
            command=lambda: self._switch_content_type("inquiry"))
        self.ct_btn_inquiry.pack(side="left", fill="x", expand=True)
        tk.Frame(ct_bar, bg=BORDER, width=2).pack(side="left", fill="y")
        self.ct_btn_review = tk.Button(
            ct_bar, text="⭐  후기형",
            font=FONTB, bg=BG3, fg=TEXT_DIM,
            activebackground="#854d0e", bd=0, padx=12, pady=7,
            cursor="hand2", relief="flat",
            command=lambda: self._switch_content_type("review"))
        self.ct_btn_review.pack(side="left", fill="x", expand=True)

        # 문의 전환형 설명 라벨
        self.ct_desc_lbl = tk.Label(ct_card, text="",
            font=("Segoe UI", 8), bg=BG2, fg=TEXT_DIM,
            anchor="w", justify="left", wraplength=340)
        self.ct_desc_lbl.pack(fill="x")

        # ── 페르소나 패널 (콘텐츠 유형별 교체) ─────────────────
        self.t2_persona_panel = tk.Frame(ct_card, bg=BG2)
        self.t2_persona_panel.pack(fill="x", pady=(8, 0))
        self._build_t2_persona_options()  # 초기 렌더
        
        # [V2 추가] 페르소나 치트시트 & 커스텀 추가 버튼 (트랙2용)
        btn_f2 = tk.Frame(ct_card, bg=BG3)
        btn_f2.pack(fill="x", pady=(8, 0))
        tk.Button(btn_f2, text="💡 어떤 페르소나를 선택할까요? (치트시트)", font=("Segoe UI", 8),
                  bg=BG3, fg=TEAL, bd=0, cursor="hand2", anchor="w",
                  command=self._show_cheat_sheet).pack(side="left", fill="x", expand=True)
        if self.plan_obj and self.plan_obj.name != "라이트(도구)":
            tk.Button(btn_f2, text="📂 커스텀 페르소나 (TXT)", font=("Segoe UI", 8),
                      bg=BORDER, fg="white", bd=0, cursor="hand2", anchor="e",
                      command=self._open_personas_folder).pack(side="right")
        self._switch_content_type(self.var_t2_content_type.get())

        # 이미지
        c4 = self._card(parent, "📷  이미지 및 안티봇 세탁")
        tk.Button(c4, text="+ 이미지 선택 (최대 10개)", font=FONT, bg=BG3, fg=TEXT,
                  activebackground=BORDER, bd=0, padx=10, pady=6,
                  cursor="hand2", relief="flat",
                  command=lambda: self._select_images(2)).pack(fill="x")
        self.t2_img_lbl = tk.Label(c4, text="선택된 이미지 없음",
                                   font=FONT, bg=BG2, fg=TEXT_DIM, anchor="w")
        self.t2_img_lbl.pack(fill="x", pady=(4, 0))
        
        # 워터마크 프레임
        wm_f2 = tk.Frame(c4, bg=BG2)
        wm_f2.pack(fill="x", pady=(6, 2))
        self.t2_watermark_chk = tk.Checkbutton(wm_f2, text=" 네이버 로직 우회용 이미지 세탁 적용 (크롭+회전+타일링)", 
                       variable=self.var_t2_watermark_enable,
                       bg=BG2, fg=TEXT, activebackground=BG2, selectcolor=BG3,
                       font=FONT, cursor="hand2", command=self._save_state)
        self.t2_watermark_chk.pack(side="left")
        
        self.t2_watermark_text_lbl = tk.Label(c4, text="🖋️ 워터마크 문구 (예: 한결오토리스)", font=FONTB, bg=BG2, fg=TEXT, anchor="w")
        self.t2_watermark_text_lbl.pack(fill="x", pady=(4, 2))
        self.t2_watermark_text_entry = self._entry_watch(c4, self.var_t2_watermark_text)
        
        c_link2 = self._card(parent, "🔗 링크 전용 특별 이미지 (1장만, 클릭 시 이동)")
        self.t2_link_img_btn = tk.Button(c_link2, text="+ 링크전용 이미지 선택", font=FONT, bg=BG3, fg=TEXT,
                  activebackground=BORDER, bd=0, padx=10, pady=6,
                  cursor="hand2", relief="flat",
                  command=lambda: self._select_link_images(2))
        self.t2_link_img_btn.pack(fill="x")
        self.t2_link_img_lbl = tk.Label(c_link2, text="선택된 이미지 없음", font=FONT, bg=BG2, fg=TEXT_DIM, anchor="w")
        self.t2_link_img_lbl.pack(fill="x", pady=(4, 0))
        
        self.t2_link_url_lbl = tk.Label(c_link2, text="이동할 URL (위 이미지 클릭 시 연결)", font=FONTB, bg=BG2, fg=TEXT, anchor="w")
        self.t2_link_url_lbl.pack(fill="x", pady=(4, 2))
        self.t2_link_url_entry = self._entry_watch(c_link2, self.var_t2_image_link)

        self.t2_link_pos_f = tk.Frame(c_link2, bg=BG2)
        self.t2_link_pos_f.pack(fill="x", pady=(4, 0))
        tk.Label(self.t2_link_pos_f, text="삽입 위치:", font=FONTB, bg=BG2, fg=TEXT, anchor="w").pack(fill="x", pady=(4, 2))
        
        self.t2_link_pos_rbs = []
        for v in ["상단", "중간", "하단"]:
            rb = tk.Radiobutton(self.t2_link_pos_f, text=v, variable=self.var_t2_link_pos, value=v,
                           bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, font=FONT, command=self._save_state)
            rb.pack(side="left", padx=(0,10))
            self.t2_link_pos_rbs.append(rb)

        # 발행 옵션 + 실행
        self._build_publish_options(parent, track=2)

    def _build_publish_options(self, parent, track: int):
        color = ACCENT if track == 1 else TEAL
        color2 = ACCENT2 if track == 1 else TEAL2

        c = self._card(parent, "🚦  발행 옵션")
        sched_var = self.var_t1_schedule_publish if track == 1 else self.var_t2_schedule_publish
        date_var  = self.var_t1_schedule_date    if track == 1 else self.var_t2_schedule_date
        hour_var  = self.var_t1_schedule_hour    if track == 1 else self.var_t2_schedule_hour
        min_var   = self.var_t1_schedule_min     if track == 1 else self.var_t2_schedule_min

        # 피커 프레임 (예약 체크 시만 표시)
        picker_frame = tk.Frame(c, bg=BG3, bd=0,
                                highlightthickness=1, highlightbackground=BORDER)

        def _toggle_picker(*_):
            if sched_var.get():
                picker_frame.pack(fill="x", pady=(4, 4))
            else:
                picker_frame.pack_forget()
            self._save_state()

        cb_sched = tk.Checkbutton(c,
                                  text=" 🕰️ 예약 발행  (날짜·시간 직접 선택)",
                                  variable=sched_var, bg=BG2, fg=TEXT,
                                  activebackground=BG2, selectcolor=BG3,
                                  font=FONT, cursor="hand2", command=_toggle_picker)
        cb_sched.pack(anchor="w", pady=(0, 2))
        
        if track == 1:
            self.t1_schedule_chk = cb_sched
        else:
            self.t2_schedule_chk = cb_sched

        # ── 날짜 행 ──────────────────────────────────────────────
        row_d = tk.Frame(picker_frame, bg=BG3); row_d.pack(fill="x", padx=10, pady=(8, 2))
        tk.Label(row_d, text="📅 날짜", font=FONTB, bg=BG3, fg=TEXT).pack(side="left")
        date_entry = tk.Entry(row_d, textvariable=date_var, font=FONTMONO,
                              bg="#090b12", fg=TEXT, insertbackground=TEXT,
                              bd=0, highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=color,
                              relief="flat", width=14)
        date_entry.pack(side="left", padx=(8, 4), ipady=5)
        date_entry.bind("<KeyRelease>", self._schedule_save)
        date_entry.bind("<FocusOut>",   self._schedule_save)

        import datetime as _dt
        def _set_day(delta=0):
            d = _dt.date.today() + _dt.timedelta(days=delta)
            date_var.set(f"{d.year}. {d.month:02d}. {d.day:02d}")
            self._save_state()

        tk.Button(row_d, text="오늘", font=FONT, bg=BG3, fg=TEXT_DIM,
                  activebackground=BORDER, bd=0, padx=6, pady=3,
                  cursor="hand2", relief="flat",
                  command=lambda: _set_day(0)).pack(side="left", padx=(0, 2))
        tk.Button(row_d, text="내일", font=FONT, bg=BG3, fg=TEXT_DIM,
                  activebackground=BORDER, bd=0, padx=6, pady=3,
                  cursor="hand2", relief="flat",
                  command=lambda: _set_day(1)).pack(side="left")

        # 힌트: 날짜 비워두면 AI가 추천
        tk.Label(picker_frame, text="💡 날짜를 비워두면 Gemini AI가 최적 업로드 시간을 자동으로 추천합니다",
                 font=("Segoe UI", 8), bg=BG3, fg=TEXT_DIM, anchor="w",
                 wraplength=320).pack(fill="x", padx=10, pady=(0, 4))

        # ── 시간 행 ──────────────────────────────────────────────
        row_t = tk.Frame(picker_frame, bg=BG3); row_t.pack(fill="x", padx=10, pady=(4, 8))
        tk.Label(row_t, text="⏰ 시간", font=FONTB, bg=BG3, fg=TEXT).pack(side="left")
        tk.Spinbox(row_t, from_=0, to=23, width=4, textvariable=hour_var,
                   format="%02.0f", font=FONTMONO,
                   bg="#090b12", fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BG3, bd=0, relief="flat",
                   highlightthickness=1, highlightbackground=BORDER,
                   command=self._schedule_save).pack(side="left", padx=(8, 2))
        tk.Label(row_t, text="시", font=FONT, bg=BG3, fg=TEXT_DIM).pack(side="left")

        tk.Spinbox(row_t, values=("00","10","20","30","40","50"), width=4,
                   textvariable=min_var, font=FONTMONO,
                   bg="#090b12", fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BG3, bd=0, relief="flat",
                   highlightthickness=1, highlightbackground=BORDER,
                   command=self._schedule_save).pack(side="left", padx=(6, 2))
        tk.Label(row_t, text="분", font=FONT, bg=BG3, fg=TEXT_DIM).pack(side="left")

        if sched_var.get():
            picker_frame.pack(fill="x", pady=(4, 4))




        cb = tk.Checkbutton(c, text="  발행 전 멈춤  (에디터에서 직접 확인 후 발행)",
                            variable=self.var_pause,
                            bg=BG2, fg=TEXT, activebackground=BG2, selectcolor=BG3,
                            font=FONT, cursor="hand2", command=self._save_state)
        cb.pack(anchor="w")
        tk.Label(c, text="⚠️ 체크 시: 글 입력 후 발행 버튼은 누르지 않음",
                 font=("Segoe UI", 8), bg=BG2, fg=YELLOW, anchor="w").pack(fill="x")

        # ── [NEW] 다중 계정 실행 시 계정 간 대기 옵션 ──
        delay_f = tk.Frame(c, bg=BG2)
        delay_f.pack(fill="x", pady=(10, 0))
        tk.Label(delay_f, text="⏳ 계정 전환 대기 (분):", font=FONTB, bg=BG2, fg=TEXT).pack(side="left")
        
        tk.Spinbox(delay_f, from_=1, to=1440, width=4, textvariable=self.var_acc_delay_min,
                   font=FONTMONO, bg="#090b12", fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BG3, bd=0, relief="flat", highlightthickness=1,
                   highlightbackground=BORDER, command=self._schedule_save).pack(side="left", padx=(6, 2))
        tk.Label(delay_f, text="~", font=FONT, bg=BG2, fg=TEXT_DIM).pack(side="left")
        tk.Spinbox(delay_f, from_=1, to=1440, width=4, textvariable=self.var_acc_delay_max,
                   font=FONTMONO, bg="#090b12", fg=TEXT, insertbackground=TEXT,
                   buttonbackground=BG3, bd=0, relief="flat", highlightthickness=1,
                   highlightbackground=BORDER, command=self._schedule_save).pack(side="left", padx=(2, 6))
        
        tk.Checkbutton(delay_f, text="즉시 실행 (대기 안함)", variable=self.var_acc_delay_skip,
                       bg=BG2, fg=RED, activebackground=BG2, selectcolor=BG3,
                       font=FONTB, cursor="hand2", command=self._save_state).pack(side="right")

        bf = tk.Frame(parent, bg=BG)
        bf.pack(fill="x", pady=(6, 0))


        cmd = (lambda: self._run_track1()) if track == 1 else (lambda: self._run_track2())
        label = "🚀  트랙 1 실행 (자동 벤치마킹)" if track == 1 else "🚀  트랙 2 실행 (반자동 발행)"

        if track == 1:
            self.run_btn1 = tk.Button(bf, text=label, font=("Segoe UI", 12, "bold"),
                                      bg=color, fg="white", activebackground=color2,
                                      bd=0, pady=12, cursor="hand2", relief="flat",
                                      command=cmd)
            self.run_btn1.pack(fill="x", pady=(0, 6))
        else:
            self.run_btn2 = tk.Button(bf, text=label, font=("Segoe UI", 12, "bold"),
                                      bg=color, fg="white", activebackground=color2,
                                      bd=0, pady=12, cursor="hand2", relief="flat",
                                      command=cmd)
            self.run_btn2.pack(fill="x", pady=(0, 6))

        stop_cmd = self._stop_bot
        if track == 1:
            self.stop_btn1 = tk.Button(bf, text="⛔  정지", font=FONTB,
                                       bg="#7f1d1d", fg=RED, activebackground="#991b1b",
                                       bd=0, pady=8, cursor="hand2", relief="flat",
                                       state="disabled", command=stop_cmd)
            self.stop_btn1.pack(fill="x")
        else:
            self.stop_btn2 = tk.Button(bf, text="⛔  정지", font=FONTB,
                                       bg="#7f1d1d", fg=RED, activebackground="#991b1b",
                                       bd=0, pady=8, cursor="hand2", relief="flat",
                                       state="disabled", command=stop_cmd)
            self.stop_btn2.pack(fill="x")

    # ══════════════════════════════════════════════════════════
    # 트랙 2 콘텐츠 유형 서브탭 제어
    # ══════════════════════════════════════════════════════════
    # 콘텐츠 유형별 페르소나
    _INQUIRY_PERSONAS = [
        ("veteran_dealer",       "🎖️   [V2] 베테랑 딜러 (솔직·정직)"),
        ("company_introducer",   "🏢  [V2] 업체 브랜드 차별화 강조"),
        ("b2b_expert",           "📈  [V2] 법인/사업자 절세 전문"),
        ("urgency_specialist",   "🚨  [V2] 긴급 마감 임박 프로모션"),
        ("risk_preventer",       "⚠️   [V2] 계약 전 주의사항 (실패방지)"),
        ("custom_designer",      "📏  [V2] 1:1 맞춤 견적 설계 전문가"),
        ("quote_comparator",     "🧾  [V2] 타사 비교 견적 자신형"),
        ("longterm_manager",     "🛠️  [V2] 계약 후 사후관리·신뢰"),
        ("veteran_dealer",       "🎖️   [V1] 시니어 딜러  (15년, 신주도 높음)"),
        ("young_specialist",     "📱  [V1] 디지털 딜러  (카톡 비대면 전문)"),
        ("corporate_specialist", "🏢  [V1] 법인 리스 전문가"),
        ("luxury_import_dealer", "💎  [V1] 수입 럭셔리 전문 딜러"),
    ]
    _REVIEW_PERSONAS = [
        ("experience_sharer",    "🤝  [V2] 경험 공유 (나도 그랬는데...)"),
        ("review_collector",     "🌟  [V2] 만족도 후기 소셜 프루프"),
        ("honest_advisor",       "🤝  [V1] 솔직한 어드바이저  (장단점 모두 공개)"),
        ("young_specialist",     "📱  [V1] 실사용 후기 스타일  (SNS 체험형)"),
        ("veteran_dealer",       "🎖️   [V1] 전문가 후기  (수백 건 사례 기반)"),
    ]

    def _switch_content_type(self, ctype: str):
        """'문의전환형' 또는 '후기형' 서브탭 전환"""
        self.var_t2_content_type.set(ctype)
        AMBER = "#d97706"
        if ctype == "inquiry":
            self.ct_btn_inquiry.config(bg=TEAL, fg="white")
            self.ct_btn_review.config(bg=BG3, fg=TEXT_DIM)
            self.ct_desc_lbl.config(
                text="타겟: 상담/문의 유도  •  딸러 CTA 포함  •  신뢰 구축 어조",
                fg=TEAL)
            personas = self._INQUIRY_PERSONAS
        else:
            self.ct_btn_review.config(bg=AMBER, fg="white")
            self.ct_btn_inquiry.config(bg=BG3, fg=TEXT_DIM)
            self.ct_desc_lbl.config(
                text="타겟: 실제 경험 기반 후기  •  장단점 모두 솔직하게  •  공감 포맰트",
                fg=AMBER)
            personas = self._REVIEW_PERSONAS

        # 페르소나 패널 재렌더
        for w in self.t2_persona_panel.winfo_children():
            w.destroy()
        for val, lbl in personas:
            tk.Radiobutton(
                self.t2_persona_panel, text=lbl,
                variable=self.var_t2_persona, value=val,
                bg=BG2, fg=TEXT, activebackground=BG2, selectcolor=BG3,
                font=FONT, cursor="hand2", anchor="w",
                command=self._schedule_save
            ).pack(fill="x", ipady=2)
        # ▶ 로드 중이 아닐 때 + 현재 선택값이 없을 때만 첫 옵션으로 초기화
        if not self._loading and personas and not self.var_t2_persona.get():
            self.var_t2_persona.set(personas[0][0])
        if not self._loading:
            self._schedule_save()


    def _build_t2_persona_options(self):
        """_switch_content_type에서 브렇더를 브리는 초기 호출용"""
        pass  # _switch_content_type이 실제 렌더링을 담당

    # ══════════════════════════════════════════════════════════
    # 탭 전환 (트랙 1 / 트랙 2)
    # ══════════════════════════════════════════════════════════
    # ── 로그 패널 ──────────────────────────────────────────────
    def _build_log(self, parent):
        hdr = tk.Frame(parent, bg=BG); hdr.pack(fill="x", pady=(0, 6))
        tk.Label(hdr, text="📟  실행 로그", font=FONTH, bg=BG, fg=TEXT).pack(side="left")
        tk.Button(hdr, text="지우기", font=FONT, bg=BG3, fg=TEXT_DIM,
                  activebackground=BORDER, bd=0, padx=8, pady=3,
                  cursor="hand2", relief="flat",
                  command=self._clear_log).pack(side="right")
        lf = tk.Frame(parent, bg=BORDER); lf.pack(fill="both", expand=True)
        self.log_text = scrolledtext.ScrolledText(
            lf, font=FONTMONO, bg="#080a0f", fg="#adb5c9",
            insertbackground=TEXT, bd=0, relief="flat", state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=1, pady=1)
        for tag, col in [("ok", GREEN), ("err", RED), ("warn", YELLOW),
                         ("dim", TEXT_DIM), ("acc", "#a78bfa"), ("blue", BLUE),
                         ("teal", "#34d4c0")]:
            self.log_text.tag_config(tag, foreground=col)

    # ══════════════════════════════════════════════════════════
    # 탭 전환
    # ══════════════════════════════════════════════════════════
    def _switch_tab(self, track: int):
        self.current_track = track
        if track == 1:
            self.panel_t2.pack_forget()
            self.panel_t1.pack(fill="x")
            self.tab_track1_btn.config(bg=ACCENT, fg="white")
            self.tab_track2_btn.config(bg=BG3, fg=TEXT_DIM)
        else:
            # 트랙 2 (수동모드) 진입 시 LITE 플랜이면 막기
            if self.plan_obj and self.plan_obj.name == "라이트(도구)":
                messagebox.showwarning("플랜 제한", "라이트 플랜에서는 트랙 2(반자동 딜러형)를 지원하지 않습니다.\n트랙 1만 이용 가능합니다.")
                return

            self.panel_t1.pack_forget()
            self.panel_t2.pack(fill="x")
            self.tab_track2_btn.config(bg=TEAL, fg="white")
            self.tab_track1_btn.config(bg=BG3, fg=TEXT_DIM)

    # ══════════════════════════════════════════════════════════
    # 공통 헬퍼
    # ══════════════════════════════════════════════════════════
    def _card(self, parent, title):
        w = tk.Frame(parent, bg=BG2, bd=0, highlightthickness=1,
                     highlightbackground=BORDER)
        w.pack(fill="x", pady=(0, 10))
        tk.Label(w, text=title, font=("Segoe UI", 8, "bold"),
                 bg=BG2, fg=TEXT_DIM, anchor="w").pack(fill="x", padx=14, pady=(9, 3))
        inner = tk.Frame(w, bg=BG2)
        inner.pack(fill="x", padx=14, pady=(0, 10))
        return inner

    def _lbl(self, parent, text):
        tk.Label(parent, text=text, font=FONTB, bg=BG2,
                 fg=TEXT, anchor="w").pack(fill="x", pady=(4, 2))

    # ── 디바운서: 0.5초 안에 여러 번 호출돼도 한 번만 저장 ────────
    _save_pending = False

    def _schedule_save(self, *_):
        """trace/이벤트가 연속 발화해도 0.5초 뒤 딱 한 번만 저장"""
        if self._loading:
            return
        if not self._save_pending:
            self._save_pending = True
            self.after(500, self._do_deferred_save)

    def _do_deferred_save(self):
        self._save_pending = False
        self._save_state()

    def _entry(self, parent, var, show=""):
        e = tk.Entry(parent, textvariable=var, font=FONT, show=show,
                     bg="#0a0c14", fg=TEXT, insertbackground=TEXT,
                     bd=0, highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=ACCENT, relief="flat")
        e.pack(fill="x", ipady=7, pady=(0, 2))
        e.bind("<KeyRelease>", self._schedule_save)
        e.bind("<FocusOut>",   self._schedule_save)
        return e

    def _entry_watch(self, parent, var, show=""):
        e = tk.Entry(parent, textvariable=var, font=FONT, show=show,
                     bg="#0a0c14", fg=TEXT, insertbackground=TEXT,
                     bd=0, highlightthickness=1,
                     highlightbackground=BORDER, highlightcolor=TEAL, relief="flat")
        e.pack(fill="x", ipady=7, pady=(0, 2))
        e.bind("<KeyRelease>", self._schedule_save)
        e.bind("<FocusOut>",   self._schedule_save)
        return e

    # ══════════════════════════════════════════════════════════
    # 이미지 선택
    # ══════════════════════════════════════════════════════════
    def _select_images(self, track: int):
        paths = filedialog.askopenfilenames(
            title="이미지 선택",
            filetypes=[("이미지", "*.jpg *.jpeg *.png *.webp"), ("전체", "*.*")])
        if paths:
            if track == 1:
                self.t1_images = list(paths)
                self.t1_img_lbl.config(text=f"✅ {len(paths)}장 선택됨", fg=GREEN)
            else:
                self.t2_images = list(paths)
                self.t2_img_lbl.config(text=f"✅ {len(paths)}장 선택됨", fg=GREEN)
            self._save_state()

    def _select_link_images(self, track: int):
        paths = filedialog.askopenfilenames(
            title="링크 전용 특별 이미지 선택 (1장만)",
            filetypes=[("이미지", "*.jpg *.jpeg *.png *.webp"), ("전체", "*.*")])
        if paths:
            path = paths[0]
            if track == 1:
                self.t1_link_image = [path]
                self.t1_link_img_lbl.config(text=f"✅ 1장 선택됨", fg=GREEN)
            else:
                self.t2_link_image = [path]
                self.t2_link_img_lbl.config(text=f"✅ 1장 선택됨", fg=GREEN)
            self._save_state()

    # ══════════════════════════════════════════════════════════
    # 트랙 1 실행 — 완전 자동 (벤치마킹 + 노출형만)
    # ══════════════════════════════════════════════════════════
    def _generate_multi_config(self, track_number: int):
        self._save_ui_to_account(self.active_acc_idx)
        
        # 유효한 계정만 필터링 (ID/PW 존재하는 것)
        valid_accs = []
        for a in self.accounts:
            if not a.get("naver_id") or not a.get("naver_pw"): continue
            tag_str = a.get(f"t{track_number}_tags", "")
            tags = [t.strip() for t in tag_str.split(",") if t.strip()]
            
            p_val = a.get(f"t{track_number}_persona", "")
            if track_number == 1:
                ptype = "exposure"
                images_dir = self._copy_images(a.get("t1_images", []), a.get("naver_id"))
                if p_val == "random_exposure": p_val = "random_exposure"
            else:
                ptype = "dealer"
                images_dir = self._copy_images(a.get("t2_images", []), a.get("naver_id"))
                
            # 테스트 모드 여부 확인
            is_test = self.var_test_mode.get()
            final_mode = "TEST" if is_test else ("BENCHMARK" if track_number == 1 else "SEMIAUTO")
                
            acc_cfg = {
                "naver_id": a["naver_id"],
                "naver_pw": a["naver_pw"],
                "MODE": final_mode,
                "keyword": a.get(f"t{track_number}_kw", ""),
                "car_model": a.get(f"t{track_number}_car_model", ""),
                "manual_title": a.get("t2_title", "") if track_number == 2 else "",
                "biz_name": a.get(f"t{track_number}_biz", ""),
                "must_phrase": a.get(f"t{track_number}_must_phrase", ""),
                "must_pos": [pos for pos in ["top", "mid", "bot"] if a.get(f"t{track_number}_must_pos_{pos}", False)],
                "tags": tags,
                "blog_count": int(a.get("t1_count", 5)) if track_number == 1 else 1,
                "persona_type": ptype,
                "persona": p_val,
                "content_type": a.get("t2_content_type", "inquiry") if track_number == 2 else "",
                "manual_facts": a.get("t2_facts", "") if track_number == 2 else "",
                "images_dir": images_dir,
                "watermark_enable": a.get(f"t{track_number}_watermark_enable", True),
                "watermark_text": a.get(f"t{track_number}_watermark_text", ""),
                "image_link": a.get(f"t{track_number}_image_link", ""),
                "link_image": self._copy_images(a.get(f"t{track_number}_link_image", []), a.get("naver_id")+"_link"),
                "link_pos": a.get(f"t{track_number}_link_pos", "하단"),
                "schedule_publish": a.get(f"t{track_number}_schedule_publish", False),
                "post_length": a.get(f"t{track_number}_post_length", "일반형 (1500~1800자)"),
                "align": a.get(f"t{track_number}_align", "기본"),
                "advanced_format": a.get(f"t{track_number}_advanced_format", True),
                "acc_delay_min": self.var_acc_delay_min.get(),
                "acc_delay_max": self.var_acc_delay_max.get(),
                "acc_delay_skip": self.var_acc_delay_skip.get(),
                "user_uid": getattr(self.plan_obj, "uid", ""),
                "user_token": getattr(self.plan_obj.db_client, "id_token", "") if hasattr(self.plan_obj, "db_client") else "",
                "is_trial": getattr(self.plan_obj, "is_trial", False)
            }
            
            # [NEW] 라이트 플랜 강제 옵션 적용 (UI 변조/버그 대비 백엔드 락)
            if self.plan_obj and self.plan_obj.name == "라이트(도구)":
                acc_cfg["blog_count"] = 1
                acc_cfg["watermark_enable"] = False
                acc_cfg["watermark_text"] = ""
                acc_cfg["image_link"] = ""
                acc_cfg["link_image"] = ""
                acc_cfg["schedule_publish"] = False
                acc_cfg["post_length"] = "간편형 (800~1000자)"
                acc_cfg["advanced_format"] = False
                # 허용된 페르소나가 아니면 무조건 랜덤으로 고정
                allowed_personas = [
                    "random_exposure", "search_solver", "comparison_expert", 
                    "problem_solver", "trend_tracker"
                ]
                if acc_cfg["persona"] not in allowed_personas:
                    acc_cfg["persona"] = "random_exposure"
            
            # ── schedule_time 문자열 조합 (예: "2026. 03. 01. 14:00") ──────
            if acc_cfg["schedule_publish"]:
                s_date = a.get(f"t{track_number}_schedule_date", "").strip()
                s_hour = str(a.get(f"t{track_number}_schedule_hour", "14")).zfill(2)
                s_min  = str(a.get(f"t{track_number}_schedule_min", "00")).zfill(2)
                if s_date:
                    # "2026. 03. 01" → "2026. 03. 01. 14:00"
                    acc_cfg["schedule_time"] = f"{s_date}. {s_hour}:{s_min}"
                else:
                    acc_cfg["schedule_time"] = ""
            else:
                acc_cfg["schedule_time"] = ""
            valid_accs.append(acc_cfg)
            
        return valid_accs

    def _copy_images(self, image_paths, acc_id) -> str:
        if not image_paths: return ""
        safe_id = acc_id.split('@')[0] if acc_id else "common"
        d = os.path.join(os.getcwd(), "_uploaded_images", safe_id)
        os.makedirs(d, exist_ok=True)
        for old in os.listdir(d):
            try: os.remove(os.path.join(d, old))
            except: pass
        for p in image_paths:
            if os.path.exists(p):
                try: shutil.copy2(p, d)
                except: pass
        return d

    def _run_track1(self):
        self._save_state()  # 실행 전 현재 화면의 값을 반드시 메모리에 찔러넣음!
        valid_accs = self._generate_multi_config(1)
        if not valid_accs:
            messagebox.showwarning("오류", "유효한 네이버 계정(ID/PW)이 최소 1개 이상 필요합니다.")
            return

        cfg = {
            "MODE": "MULTI_ACCOUNT",
            "TRACK": 1,
            "accounts": valid_accs
        }
        self._write_config(cfg)
        self._save_state()
        self._log(f"⚡ [트랙1] 다중 계정 일괄 실행 ({len(valid_accs)}개 계정 순방)", "acc")
        self._run_subprocess("")

    # ══════════════════════════════════════════════════════════
    # 트랙 2 실행 — 반자동 (직접 입력 + 딜러형만)
    # ══════════════════════════════════════════════════════════
    def _run_track2(self):
        self._save_state()  # 트랙2 역시 실행 직전에 무조건 화면 값을 메모리 배열로 이동시킴!
        valid_accs = self._generate_multi_config(2)
        if not valid_accs:
            messagebox.showwarning("오류", "유효한 네이버 계정(ID/PW)이 최소 1개 이상 필요합니다.")
            return
            
        cfg = {
            "MODE": "MULTI_ACCOUNT",
            "TRACK": 2,
            "accounts": valid_accs
        }
        self._write_config(cfg)
        self._save_state()
        self._log(f"✍️ [트랙2] 다중 계정 일괄 실행 ({len(valid_accs)}개 계정 순방)", "teal")
        self._run_subprocess("")

    def _run_subprocess(self, keyword: str):
        """두 트랙 모두 same entry point — MODE는 _ui_config.json에서 읽음"""
        python = sys.executable
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        self.process = subprocess.Popen(
            [python, "-u", "-X", "utf8", "main_bot.py", "FROM_UI"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=os.getcwd(), bufsize=1, env=env)
        self.running = True
        self._set_running(True)
        import threading
        threading.Thread(target=self._read_proc, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    # 공통 유틸
    # ══════════════════════════════════════════════════════════
    def _write_account(self, nid, npw):
        try:
            with open("account.txt", "w", encoding="utf-8") as f:
                f.write(f"{nid}\n{npw}\n")
        except Exception as e:
            self._log(f"⚠️ account.txt 오류: {e}", "warn")



    def _write_config(self, cfg):
        # API Key is now handled internally in gemini_core.py
        try:
            with open("_ui_config.json", "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"⚠️ config 저장 실패: {e}", "warn")


    # ══════════════════════════════════════════════════════════
    # 다중 계정 로직
    # ══════════════════════════════════════════════════════════
    def _render_account_tabs(self):
        for w in self.acc_bar.winfo_children():
            w.destroy()
            
        tk.Label(self.acc_bar, text="📁 계정 목록 :", font=FONTB, bg=BG2, fg=TEXT).pack(side="left", padx=(14, 10), pady=8)
        
        for i, acc in enumerate(self.accounts):
            nid = acc.get("naver_id", "").split("@")[0]
            name = f"계정 {i+1} ({nid})" if nid else f"새 계정 {i+1}"
            
            bg_color = ACCENT if i == self.active_acc_idx else BG3
            fg_color = "white" if i == self.active_acc_idx else TEXT_DIM
            
            btn = tk.Button(self.acc_bar, text=name, font=FONTB, bg=bg_color, fg=fg_color,
                            activebackground=ACCENT2, bd=0, padx=10, pady=4, cursor="hand2", relief="flat",
                            command=lambda idx=i: self._switch_account(idx))
            btn.pack(side="left", padx=(0, 6), pady=8)
            
        # Add new account button
        btnAdd = tk.Button(self.acc_bar, text=" + 추가 ", font=FONT, bg=TEAL, fg="white",
                           activebackground=TEAL2, bd=0, padx=8, pady=4, cursor="hand2", relief="flat",
                           command=self._add_account)
        btnAdd.pack(side="left", padx=(10, 6), pady=8)
        
        # Delete current account button
        if len(self.accounts) > 1:
            btnDel = tk.Button(self.acc_bar, text=" - 삭제 ", font=FONT, bg=RED, fg="white",
                               activebackground="#b91c1c", bd=0, padx=8, pady=4, cursor="hand2", relief="flat",
                               command=self._delete_account)
            btnDel.pack(side="left", padx=0, pady=8)
            
        # [NEW] Clone button
        btnClone = tk.Button(self.acc_bar, text=" 📋 현재 복제 ", font=FONTB, bg=BG3, fg=BLUE,
                             activebackground=BG, bd=0, padx=10, pady=4, cursor="hand2", relief="flat",
                             highlightthickness=1, highlightbackground=BLUE,
                             command=self._duplicate_account)
        btnClone.pack(side="left", padx=(20, 0), pady=8)
            
    def _switch_account(self, idx):
        if idx == self.active_acc_idx: return
        self._save_ui_to_account(self.active_acc_idx)
        self.active_acc_idx = idx
        self._load_account_to_ui(idx)
        self._render_account_tabs()
        self._save_state()
        
    def _add_account(self):
        if self.plan_obj and len(self.accounts) >= self.plan_obj.max_accounts:
            messagebox.showwarning("플랜 제한", f"현재 님의 플랜({self.plan_obj.name})에서는 최대 {self.plan_obj.max_accounts}개의 계정만 생성할 수 있습니다.")
            return

        self._save_ui_to_account(self.active_acc_idx)
        self.accounts.append({})
        self.active_acc_idx = len(self.accounts) - 1
        self._load_account_to_ui(self.active_acc_idx)
        self._render_account_tabs()
        self._save_state()
        
    def _delete_account(self):
        if messagebox.askyesno("계정 삭제", "현재 선택된 계정 탭을 삭제하시겠습니까?"):
            del self.accounts[self.active_acc_idx]
            self.active_acc_idx = max(0, self.active_acc_idx - 1)
            self._save_state()
            self._load_account_to_ui(self.active_acc_idx)
            self._render_account_tabs()

    def _duplicate_account(self):
        """현재 계정의 모든 설정을 복사하여 새 탭 생성 (대표님 요청)"""
        if self.plan_obj and len(self.accounts) >= self.plan_obj.max_accounts:
            messagebox.showwarning("플랜 제한", f"현재 님의 플랜({self.plan_obj.name})에서는 최대 {self.plan_obj.max_accounts}개의 계정만 생성할 수 있습니다.")
            return

        self._save_ui_to_account(self.active_acc_idx)
        import copy
        new_acc = copy.deepcopy(self.accounts[self.active_acc_idx])
        
        # 중복 방지를 위해 네이버 ID 뒤에 (복사) 붙임
        if new_acc.get("naver_id"):
            # 계정 복제 시 ID 뒤에 _copy가 붙지 않도록 수정 (대표님 요청)
            new_acc["naver_id"] = new_acc["naver_id"]
            
        self.accounts.append(new_acc)
        self.active_acc_idx = len(self.accounts) - 1
        self._load_account_to_ui(self.active_acc_idx)
        self._render_account_tabs()
        self._save_state()
        self._log(f"📋 계정 {self.active_acc_idx+1}로 현재 설정 복제 완료", "ok")

    def _save_ui_to_account(self, idx):
        if idx < 0 or idx >= len(self.accounts): return
        try: t2f = self.t2_facts_text.get("1.0", "end").strip()
        except: t2f = ""
        acc = {
            "naver_id":    self.var_naver_id.get(),
            "naver_pw":    self.var_naver_pw.get(),
            "t1_kw":       self.var_t1_kw.get(),
            "t1_car_model":self.var_t1_car_model.get(),
            "t1_biz":      self.var_t1_biz.get(),
            "t1_must_phrase":    self.var_t1_must_phrase.get(),
            "t1_must_pos_top":   self.var_t1_must_pos_top.get(),
            "t1_must_pos_mid":   self.var_t1_must_pos_mid.get(),
            "t1_must_pos_bot":   self.var_t1_must_pos_bot.get(),
            "t1_tags":     self.var_t1_tags.get(),
            "t1_count":    self.var_t1_count.get(),
            "t1_persona":  self.var_t1_persona.get(),
            "t1_images":   self.t1_images,
            "t1_watermark_enable": self.var_t1_watermark_enable.get(),
            "t1_watermark_text":   self.var_t1_watermark_text.get(),
            "t1_image_link":       self.var_t1_image_link.get(),
            "t1_link_image":       self.t1_link_image,
            "t1_link_pos":         self.var_t1_link_pos.get(),
            "t1_schedule_publish": self.var_t1_schedule_publish.get(),
            "t1_schedule_date":    self.var_t1_schedule_date.get(),
            "t1_schedule_hour":    self.var_t1_schedule_hour.get(),
            "t1_schedule_min":     self.var_t1_schedule_min.get(),
            "t1_post_length":      self.var_t1_post_length.get(),
            "t2_facts":         t2f,
            "t2_title":         self.var_t2_title.get(),
            "t2_car_model":     self.var_t2_car_model.get(),
            "t2_biz":           self.var_t2_biz.get(),
            "t2_must_phrase":    self.var_t2_must_phrase.get(),
            "t2_must_pos_top":   self.var_t2_must_pos_top.get(),
            "t2_must_pos_mid":   self.var_t2_must_pos_mid.get(),
            "t2_must_pos_bot":   self.var_t2_must_pos_bot.get(),
            "t2_tags":          self.var_t2_tags.get(),
            "t2_persona":       self.var_t2_persona.get(),
            "t2_content_type":  self.var_t2_content_type.get(),
            "t2_images":        self.t2_images,
            "t2_watermark_enable": self.var_t2_watermark_enable.get(),
            "t2_watermark_text":   self.var_t2_watermark_text.get(),
            "t2_image_link":       self.var_t2_image_link.get(),
            "t2_link_image":       self.t2_link_image,
            "t2_link_pos":         self.var_t2_link_pos.get(),
            "t2_schedule_publish": self.var_t2_schedule_publish.get(),
            "t2_schedule_date":    self.var_t2_schedule_date.get(),
            "t2_schedule_hour":    self.var_t2_schedule_hour.get(),
            "t2_schedule_min":     self.var_t2_schedule_min.get(),
            "t2_post_length":      self.var_t2_post_length.get(),
            "t1_align":            self.var_t1_align.get(),
            "t1_advanced_format":  self.var_t1_advanced_format.get(),
            "t2_align":            self.var_t2_align.get(),
            "t2_advanced_format":  self.var_t2_advanced_format.get(),
        }
        self.accounts[idx] = acc
        
    def _load_account_to_ui(self, idx):
        self._loading = True
        acc = self.accounts[idx] if idx < len(self.accounts) else {}
        
        self.var_naver_id.set(acc.get("naver_id", ""))
        self.var_naver_pw.set(acc.get("naver_pw", ""))
        self.var_t1_kw.set(acc.get("t1_kw", ""))
        self.var_t1_car_model.set(acc.get("t1_car_model", ""))
        self.var_t1_biz.set(acc.get("t1_biz", ""))
        self.var_t1_must_phrase.set(acc.get("t1_must_phrase", acc.get("t1_must_top", "")))
        self.var_t1_must_pos_top.set(acc.get("t1_must_pos_top", True))
        self.var_t1_must_pos_mid.set(acc.get("t1_must_pos_mid", False))
        self.var_t1_must_pos_bot.set(acc.get("t1_must_pos_bot", False))
        self.var_t1_tags.set(acc.get("t1_tags", ""))
        self.var_t1_count.set(acc.get("t1_count", 5))
        try: self.t1_count_lbl.config(text=f"{acc.get('t1_count', 5)}개")
        except: pass
        self.var_t1_persona.set(acc.get("t1_persona", "random_exposure"))
        self.var_t1_post_length.set(acc.get("t1_post_length", "일반형 (1500~1800자)"))
        self.var_t1_align.set(acc.get("t1_align", "기본"))
        self.var_t1_advanced_format.set(acc.get("t1_advanced_format", True))
        
        imgs1 = [p for p in acc.get("t1_images", []) if os.path.exists(p)]
        self.t1_images = imgs1
        if imgs1:
            try: self.t1_img_lbl.config(text=f"✅ {len(imgs1)}장 (이전)", fg=GREEN)
            except: pass
        else:
            try: self.t1_img_lbl.config(text="선택된 이미지 없음", fg=TEXT_DIM)
            except: pass
            
        t2f = acc.get("t2_facts", "")
        try:
            self.t2_facts_text.delete("1.0", "end")
            self.t2_facts_text.insert("1.0", t2f)
        except: pass
            
        self.var_t2_title.set(acc.get("t2_title", ""))
        self.var_t2_car_model.set(acc.get("t2_car_model", ""))
        self.var_t2_biz.set(acc.get("t2_biz", ""))
        self.var_t2_must_phrase.set(acc.get("t2_must_phrase", acc.get("t2_must_top", "")))
        self.var_t2_must_pos_top.set(acc.get("t2_must_pos_top", True))
        self.var_t2_must_pos_mid.set(acc.get("t2_must_pos_mid", False))
        self.var_t2_must_pos_bot.set(acc.get("t2_must_pos_bot", False))
        self.var_t2_tags.set(acc.get("t2_tags", ""))
        
        try:
            saved_ct = acc.get("t2_content_type", "inquiry")
            self._switch_content_type(saved_ct)
            self.var_t2_persona.set(acc.get("t2_persona", "veteran_dealer"))
        except Exception: pass
        
        self.var_t2_post_length.set(acc.get("t2_post_length", "일반형 (1500~1800자)"))
        self.var_t2_align.set(acc.get("t2_align", "기본"))
        self.var_t2_advanced_format.set(acc.get("t2_advanced_format", True))
        
        self.var_t1_watermark_enable.set(acc.get("t1_watermark_enable", True))
        self.var_t1_watermark_text.set(acc.get("t1_watermark_text", ""))
        self.var_t1_image_link.set(acc.get("t1_image_link", ""))
        self.var_t1_link_pos.set(acc.get("t1_link_pos", "하단"))
        imgs1_l = [p for p in acc.get("t1_link_image", []) if os.path.exists(p)]
        self.t1_link_image = imgs1_l
        if imgs1_l:
            try: self.t1_link_img_lbl.config(text="✅ 1장 (이전)", fg=GREEN)
            except: pass
        else:
            try: self.t1_link_img_lbl.config(text="선택된 이미지 없음", fg=TEXT_DIM)
            except: pass
        self.var_t1_schedule_publish.set(acc.get("t1_schedule_publish", False))
        self.var_t1_schedule_date.set(acc.get("t1_schedule_date", ""))
        self.var_t1_schedule_hour.set(acc.get("t1_schedule_hour", "14"))
        self.var_t1_schedule_min.set(acc.get("t1_schedule_min", "00"))
        
        self.var_t2_watermark_enable.set(acc.get("t2_watermark_enable", True))
        self.var_t2_watermark_text.set(acc.get("t2_watermark_text", ""))
        self.var_t2_image_link.set(acc.get("t2_image_link", ""))
        self.var_t2_link_pos.set(acc.get("t2_link_pos", "하단"))
        imgs2_l = [p for p in acc.get("t2_link_image", []) if os.path.exists(p)]
        self.t2_link_image = imgs2_l
        if imgs2_l:
            try: self.t2_link_img_lbl.config(text="✅ 1장 (이전)", fg=GREEN)
            except: pass
        else:
            try: self.t2_link_img_lbl.config(text="선택된 이미지 없음", fg=TEXT_DIM)
            except: pass
        self.var_t2_schedule_publish.set(acc.get("t2_schedule_publish", False))
        self.var_t2_schedule_date.set(acc.get("t2_schedule_date", ""))
        self.var_t2_schedule_hour.set(acc.get("t2_schedule_hour", "14"))
        self.var_t2_schedule_min.set(acc.get("t2_schedule_min", "00"))
        
        imgs2 = [p for p in acc.get("t2_images", []) if os.path.exists(p)]
        self.t2_images = imgs2
        if imgs2:
            try: self.t2_img_lbl.config(text=f"✅ {len(imgs2)}장 (이전)", fg=GREEN)
            except: pass
        else:
            try: self.t2_img_lbl.config(text="선택된 이미지 없음", fg=TEXT_DIM)
            except: pass
            
        self._loading = False
        # 로드 완료 후 화면 강제 갱신
        self.update_idletasks()

    # ── 텍스트 위젯 <<Modified>> 핸들러 ───────────────────────────
    def _on_text_modified(self, event=None):
        if not self._loading:
            self._save_state()
            # Modified 플래그 리셋 (reset 안 하면 이벤트가 다시 오지 않음)
            try:
                self.t2_facts_text.edit_modified(False)
            except:
                pass
    def _open_personas_folder(self):
        d = os.path.join(os.getcwd(), "personas")
        os.makedirs(d, exist_ok=True)
        try:
            sample_path = os.path.join(d, "my_custom_persona.txt")
            if not os.path.exists(sample_path):
                with open(sample_path, "w", encoding="utf-8") as f:
                    f.write("[페르소나: 나만의 커스텀]\\n여기에 원하는 페르소나의 성격, 특징, 작성 가이드라인을 적어주세요.\\n어투, 금지어, 강조사항 등을 상세히 적을수록 좋습니다.\\n파일 이름(확장자 제외)이 시스템 상의 페르소나 ID가 되며 UI에 표시됩니다.")
        except: pass
        
        import subprocess
        if sys.platform == "win32":
            os.startfile(d)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", d])
        else:
            subprocess.Popen(["xdg-open", d])
            
        messagebox.showinfo("커스텀 페르소나", "열린 폴더(personas)에 .txt 파일을 추가하거나 수정한 뒤\\n프로그램을 다시 실행하면 페르소나 목록에 자동 추가됩니다.")

    # ── 상태 저장/복원 ─────────────────────────────────────────
    def _save_state(self, *_):
        if self._loading: return
        self._save_ui_to_account(self.active_acc_idx)
        state = {
            "pause":          self.var_pause.get(),
            "active_acc_idx": self.active_acc_idx,
            "accounts":       self.accounts,
            "acc_delay_min":  self.var_acc_delay_min.get(),
            "acc_delay_max":  self.var_acc_delay_max.get(),
            "acc_delay_skip": self.var_acc_delay_skip.get(),
        }
        try:
            tmp_file = STATE_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            try:
                import shutil
                shutil.move(tmp_file, STATE_FILE)
            except:
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
                os.rename(tmp_file, STATE_FILE)
        except Exception as e:
            print(f"Save State Error: {e}")

    def _load_state(self):
        try:
            if not os.path.exists(STATE_FILE): 
                self._load_account_to_ui(0)
                self._render_account_tabs()
                return
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                
            self.var_pause.set(s.get("pause", False))
            self.var_test_mode.set(s.get("test_mode", False))

            if "accounts" in s:
                self.accounts = s["accounts"]
                self.active_acc_idx = s.get("active_acc_idx", 0)
                
                # [NEW] Restore Delay Settings
                self.var_acc_delay_min.set(s.get("acc_delay_min", 60))
                self.var_acc_delay_max.set(s.get("acc_delay_max", 120))
                self.var_acc_delay_skip.set(s.get("acc_delay_skip", False))
                
                if self.active_acc_idx >= len(self.accounts):
                    self.active_acc_idx = 0
            else:
                # 마이그레이션 (단일 계정 -> 배열)
                self.accounts = [s]
                self.active_acc_idx = 0
                
            self._load_account_to_ui(self.active_acc_idx)
            self._render_account_tabs()
            self._log("💾 계정 상태 복원됨", "blue")
        except Exception as e:
            self._log(f"⚠️ 상태 복원 실패: {e}", "warn")
            self._load_account_to_ui(0)
            self._render_account_tabs()



    # ── subprocess & 로그 ──────────────────────────────────────
    def _read_proc(self):
        try:
            for raw in iter(self.process.stdout.readline, b""):
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line: self.log_queue.put(line)
        except Exception: pass
        finally:
            try: self.process.stdout.close()
            except: pass
            self.log_queue.put("__DONE__")

    def _stop_bot(self):
        if self.process:
            if platform.system() == "Windows":
                # Windows에서는 트리 구조(/T)로 강제 종료(/F)해야 하위 브라우저 프로세스까지 잡힙니다.
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], 
                               capture_output=True)
            else:
                self.process.terminate()
        self.running = False
        self._set_running(False)
        self._log("⛔ 정지됨 (프로세스 트리 종료)", "err")

    def _set_running(self, on: bool):
        state = "disabled" if on else "normal"
        color = "#3b0764" if on else ACCENT
        label = "⏳  실행 중..." if on else "🚀  트랙 1 실행 (자동 벤치마킹)"
        try: self.run_btn1.config(state=state, bg=color, text=label)
        except: pass
        color2 = "#134e4a" if on else TEAL
        label2 = "⏳  실행 중..." if on else "🚀  트랙 2 실행 (반자동 발행)"
        try: self.run_btn2.config(state=state, bg=color2, text=label2)
        except: pass
        stop_state = "normal" if on else "disabled"
        try: self.stop_btn1.config(state=stop_state)
        except: pass
        try: self.stop_btn2.config(state=stop_state)
        except: pass
        self.status_lbl.config(
            text="● 실행 중", fg=YELLOW) if on else self.status_lbl.config(
            text="● 대기 중", fg=TEXT_DIM)

    def _log(self, msg: str, tag: str = ""):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _poll_logs(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                if line == "__DONE__":
                    self.running = False
                    self._set_running(False)
                    self._log("✅ 봇 종료", "ok")
                else:
                    tag = ""
                    if any(c in line for c in ["✅", "완료", "SUCCESS"]): tag = "ok"
                    elif any(c in line for c in ["❌", "⚠️", "실패", "Error"]): tag = "err"
                    elif "트랙1" in line or "⚡" in line: tag = "acc"
                    elif "트랙2" in line or "✍️" in line: tag = "teal"
                    elif "멈춤" in line or "PAUSE" in line: tag = "warn"
                    self._log(line, tag)
        except queue.Empty: pass
        self.after(150, self._poll_logs)


    def _show_cheat_sheet(self):
        from gemini_core import CHEAT_SHEET
        help_win = tk.Toplevel(self) # Changed self.root to self
        help_win.title("🎯 페르소나 선택 가이드 (치트시트)")
        help_win.geometry("500x700")
        help_win.configure(bg=BG)
        help_win.attributes("-topmost", True)
        
        txt = scrolledtext.ScrolledText(help_win, font=("Consolas", 10), bg=BG2, fg=TEXT, insertbackground=TEXT, bd=0, padx=15, pady=15)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", CHEAT_SHEET)
        txt.configure(state="disabled")
        
        tk.Button(help_win, text="닫기", font=FONTB, bg=BG3, fg=TEXT, bd=0, pady=10, cursor="hand2", command=help_win.destroy).pack(fill="x")

if __name__ == "__main__":
    import multiprocessing
    import sys
    # PyInstaller Windows 환경에서 multiprocessing (subprocess) 
    # 무한 증식(UI 다중 팝업) 방지를 위해 반드시 최상단에 선언
    multiprocessing.freeze_support()
    
    # [NEW] PyInstaller에서 subprocess.Popen([sys.executable, "main_bot.py", "FROM_UI"])을 
    # 호출하면 다시 이 실행파일(bot_app.exe)이 켜집니다.
    # 이때 인자를 가로채서 main_bot 로직만 켜고 UI는 켜지 않도록 분기처리합니다.
    if len(sys.argv) > 1 and ("main_bot.py" in sys.argv or "FROM_UI" in sys.argv):
        try:
            import main_bot
            main_bot.main()
        except Exception as e:
            print(f"Subprocess Fatal Error: {e}")
        sys.exit(0)
    
    import auth_client
    
    def run_auth_and_launch():
        # 로그인 UI 띄우기 전에 터미널/콘솔 기반 auth_flow 실행
        success, plan_obj = auth_client.auth_flow()
        if success and plan_obj:
            print(f"🔑 [Login Success] 인증 정보: {plan_obj.name}")
            app = BotApp(plan_obj)
            app.title(f"[RealCar/blolg] Blog Post Auto-Bot (v51.0) - {plan_obj.name} 플랜")
            app.mainloop()
        else:
            print("❌ 인증에 실패하여 프로그램을 종료합니다.")
            sys.exit(1)

    # ❗ GUI 실행
    run_auth_and_launch()
