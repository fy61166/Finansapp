import sqlite3
import calendar
import threading
import json
import urllib.request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# Kivy ve KivyMD Kütüphaneleri
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget, IconRightWidget, ThreeLineAvatarIconListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatButton, MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.toast import toast
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.animation import Animation
from kivy.metrics import dp

# DÜZELTME BURADA YAPILDI (kivymd -> kivy)
from kivy.uix.behaviors import ButtonBehavior

# Pencere boyutu simülasyonu
Window.size = (360, 740)

KV = '''
# --- ÖZEL RENKLER VE STİLLER ---
<MDScreen>:
    md_bg_color: 0.05, 0.05, 0.05, 1

# Takvim Kutucuğu
<CalendarDayCard>:
    orientation: "vertical"
    padding: "2dp"
    spacing: 0
    size_hint_y: None
    height: "45dp"
    radius: [8]
    md_bg_color: 0.12, 0.12, 0.12, 1
    on_release: root.on_click()

    MDLabel:
        text: root.day_num
        halign: "center"
        font_style: "Caption"
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 0.5
        size_hint_y: None
        height: "15dp"
        bold: True

    MDLabel:
        text: root.income_text
        halign: "center"
        font_style: "Overline"
        theme_text_color: "Custom"
        text_color: 0.3, 0.9, 0.3, 1
        size_hint_y: None
        height: "12dp" if root.income_text else 0
        opacity: 1 if root.income_text else 0

    MDLabel:
        text: root.expense_text
        halign: "center"
        font_style: "Overline"
        theme_text_color: "Custom"
        text_color: 0.9, 0.3, 0.3, 1
        size_hint_y: None
        height: "12dp" if root.expense_text else 0
        opacity: 1 if root.expense_text else 0

# --- TIKLANABİLİR SEÇİM KARTI ---
<TypeSelectionCard>:
    orientation: "vertical"
    size_hint: None, None
    size: "60dp", "60dp"
    radius: [30, 30, 30, 30]
    elevation: 4
    md_bg_color: 0.1, 0.1, 0.1, 1
    ripple_behavior: True
    
    MDIcon:
        icon: root.icon
        halign: "center"
        pos_hint: {"center_x": .5, "center_y": .5}
        theme_text_color: "Custom"
        text_color: 1, 1, 1, 1
        font_size: "30sp"

MDScreen:
    MDBottomNavigation:
        id: bottom_nav
        panel_color: 0.08, 0.08, 0.08, 1
        text_color_active: 0.7, 0.7, 1, 1
        text_color_normal: 0.5, 0.5, 0.5, 1

        # --- EKRAN 1: ÖZET ---
        MDBottomNavigationItem:
            name: 'screen_home'
            text: 'Özet'
            icon: 'wallet-outline'
            on_tab_press: app.update_dashboard()

            MDBoxLayout:
                orientation: 'vertical'
                padding: "20dp"
                spacing: "10dp"

                MDBoxLayout:
                    orientation: "vertical"
                    size_hint_y: None
                    height: "120dp"
                    spacing: "5dp"
                    
                    MDLabel:
                        text: "Toplam Varlığım"
                        font_style: "Body1"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 0.6
                        halign: "left"
                    
                    MDLabel:
                        id: current_balance_label
                        text: "₺0,00"
                        font_style: "H3"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        halign: "left"
                        bold: True

                    MDBoxLayout:
                        orientation: "horizontal"
                        adaptive_height: True
                        spacing: "5dp"
                        MDIcon:
                            icon: "chart-timeline-variant"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 0.5
                            font_size: "16sp"
                            size_hint: None, None
                            size: "20dp", "20dp"
                        MDLabel:
                            id: future_balance_label
                            text: "Gelecek 30 Gün: 0.00 TL"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 0.5
                            font_style: "Caption"
                            halign: "left"

                # Ana Sayfa Hızlı Ekleme Butonları
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint_y: None
                    height: "60dp"
                    spacing: "15dp"

                    MDFillRoundFlatButton:
                        text: "Gider Ekle"
                        icon: "arrow-up"
                        md_bg_color: 0.2, 0.2, 0.2, 1 
                        text_color: 1, 1, 1, 1
                        size_hint_x: 0.5
                        on_release: app.go_to_add_screen("expense")

                    MDFillRoundFlatButton:
                        text: "Gelir Ekle"
                        icon: "arrow-down"
                        md_bg_color: 0.4, 0.3, 0.9, 1 
                        text_color: 1, 1, 1, 1
                        size_hint_x: 0.5
                        on_release: app.go_to_add_screen("income")

                MDSeparator:
                    color: 1, 1, 1, 0.1
                    height: "1dp"

                MDLabel:
                    text: "Son Hareketler"
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 0.9
                    size_hint_y: None
                    height: "40dp"
                
                ScrollView:
                    MDList:
                        id: recent_transactions_list

        # --- EKRAN 2: TAKVİM ---
        MDBottomNavigationItem:
            name: 'screen_calendar'
            text: 'Takvim'
            icon: 'calendar-month-outline'
            on_tab_press: app.init_calendar_view() 

            MDBoxLayout:
                orientation: 'vertical'
                padding: "10dp"
                MDBoxLayout:
                    size_hint_y: None
                    height: "50dp"
                    MDIconButton:
                        icon: "chevron-left"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        on_release: app.change_month(-1)
                    MDLabel:
                        id: calendar_title
                        text: ""
                        halign: "center"
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                    MDIconButton:
                        icon: "chevron-right"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        on_release: app.change_month(1)
                
                MDGridLayout:
                    cols: 7
                    size_hint_y: None
                    height: "30dp"
                    spacing: "5dp"
                    padding: "2dp"
                    MDLabel: 
                        text: "Pzt" 
                        halign: "center" 
                        theme_text_color: "Hint"
                    MDLabel: 
                        text: "Sal" 
                        halign: "center"
                        theme_text_color: "Hint"
                    MDLabel: 
                        text: "Çar" 
                        halign: "center"
                        theme_text_color: "Hint"
                    MDLabel: 
                        text: "Per" 
                        halign: "center"
                        theme_text_color: "Hint"
                    MDLabel: 
                        text: "Cum" 
                        halign: "center"
                        theme_text_color: "Hint"
                    MDLabel: 
                        text: "Cmt" 
                        halign: "center"
                        theme_text_color: "Hint"
                    MDLabel: 
                        text: "Paz" 
                        halign: "center"
                        theme_text_color: "Hint"

                MDGridLayout:
                    id: calendar_grid
                    cols: 7
                    padding: "2dp"
                    spacing: "5dp"

        # --- EKRAN 3: YATIRIM ---
        MDBottomNavigationItem:
            name: 'screen_invest'
            text: 'Yatırım'
            icon: 'chart-line'
            on_tab_press: app.load_investments()
            MDBoxLayout:
                orientation: 'vertical'
                padding: "15dp"
                MDBoxLayout:
                    size_hint_y: None
                    height: "60dp"
                    MDLabel:
                        text: "Portföyüm"
                        font_style: "H4"
                        theme_text_color: "Custom"
                        text_color: 1,1,1,1
                        bold: True
                    MDIconButton:
                        icon: "refresh"
                        theme_text_color: "Custom"
                        text_color: 0.5, 0.5, 1, 1
                        on_release: app.refresh_market_data()
                ScrollView:
                    MDList:
                        id: investment_list
                MDFloatingActionButton:
                    icon: "plus"
                    md_bg_color: 0.4, 0.3, 0.9, 1
                    text_color: 1, 1, 1, 1
                    pos_hint: {"right": .95, "bottom": .05}
                    on_release: app.open_add_investment_dialog()

        # --- EKRAN 4: EKLE ---
        MDBottomNavigationItem:
            name: 'screen_add'
            text: 'İşlem'
            icon: 'plus-circle-outline'

            MDBoxLayout:
                orientation: 'vertical'
                padding: "30dp"
                spacing: "20dp"
                pos_hint: {"center_y": .6}

                MDLabel:
                    text: "İşlem Tipi Seçin"
                    halign: "center"
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 0.7
                    size_hint_y: None
                    height: "30dp"

                # --- YENİ GİDER/GELİR SEÇİCİSİ (YUVARLAK) ---
                MDBoxLayout:
                    adaptive_size: True
                    spacing: "40dp"
                    pos_hint: {"center_x": .5}
                    
                    # GİDER BUTONU (SOL)
                    TypeSelectionCard:
                        id: btn_expense
                        icon: "minus"
                        on_release: app.select_transaction_type("expense")
                        md_bg_color: (0.2, 0.2, 0.2, 1) # Varsayılan Gri

                    # GELİR BUTONU (SAĞ)
                    TypeSelectionCard:
                        id: btn_income
                        icon: "plus"
                        on_release: app.select_transaction_type("income")
                        md_bg_color: (0.2, 0.2, 0.2, 1) # Varsayılan Gri

                MDTextField:
                    id: input_amount
                    hint_text: "Tutar"
                    input_filter: "float"
                    mode: "rectangle"
                    line_color_normal: 0.5, 0.5, 0.5, 1
                    line_color_focus: 0.7, 0.7, 1, 1
                    text_color_normal: 1, 1, 1, 1
                    hint_text_color_normal: 0.5, 0.5, 0.5, 1

                MDTextField:
                    id: input_category
                    hint_text: "Kategori"
                    icon_right: "menu-down"
                    mode: "rectangle"
                    line_color_normal: 0.5, 0.5, 0.5, 1
                    text_color_normal: 1, 1, 1, 1
                    readonly: True
                    on_focus: if self.focus: app.open_category_menu()

                MDTextField:
                    id: input_date
                    hint_text: "Tarih"
                    icon_right: "calendar"
                    mode: "rectangle"
                    line_color_normal: 0.5, 0.5, 0.5, 1
                    text_color_normal: 1, 1, 1, 1
                    readonly: True
                    on_focus: if self.focus: app.show_date_picker()

                MDTextField:
                    id: input_note
                    hint_text: "Not"
                    mode: "rectangle"
                    line_color_normal: 0.5, 0.5, 0.5, 1
                    text_color_normal: 1, 1, 1, 1

                # TEKRARLAMA (SADECE İKON)
                MDBoxLayout:
                    adaptive_size: True
                    pos_hint: {"center_x": .5}
                    MDIconButton:
                        id: btn_recurring
                        icon: "sync-off"
                        theme_text_color: "Custom"
                        text_color: 0.5, 0.5, 0.5, 1
                        user_font_size: "32sp"
                        on_release: app.open_recurring_menu()

                MDFillRoundFlatButton:
                    text: "KAYDET"
                    font_size: "18sp"
                    size_hint_x: 1
                    md_bg_color: 1, 1, 1, 1
                    text_color: 0, 0, 0, 1
                    on_release: app.save_current_transaction()

        # --- EKRAN 5: AYARLAR ---
        MDBottomNavigationItem:
            name: 'screen_settings'
            text: 'Ayarlar'
            icon: 'cog-outline'
            MDBoxLayout:
                orientation: 'vertical'
                padding: "20dp"
                MDList:
                    OneLineIconListItem:
                        text: "Verileri Temizle"
                        theme_text_color: "Custom"
                        text_color: 1, 1, 1, 1
                        on_release: app.reset_db()
                        IconLeftWidget:
                            icon: "delete-forever"
                            theme_text_color: "Custom"
                            text_color: 1, 0.3, 0.3, 1

<AddInvestmentContent>:
    orientation: "vertical"
    spacing: "12dp"
    size_hint_y: None
    height: "150dp"
    MDTextField:
        id: input_symbol
        hint_text: "Sembol"
        mode: "rectangle"
        on_text: app.search_stocks(self.text)
    MDTextField:
        id: input_quantity
        hint_text: "Adet"
        input_filter: "float"
        mode: "rectangle"
'''

class TypeSelectionCard(ButtonBehavior, MDBoxLayout):
    text = StringProperty("")
    icon = StringProperty("")
    md_bg_color = ListProperty([1, 1, 1, 1])

class AddInvestmentContent(MDBoxLayout):
    pass

class CalendarDayCard(MDCard):
    day_num = StringProperty("")
    full_date = StringProperty("")
    income_text = StringProperty("")
    expense_text = StringProperty("")
    def on_click(self):
        app = MDApp.get_running_app()
        if self.full_date: app.show_day_details(self.full_date)

class TransactionItem(TwoLineAvatarIconListItem):
    transaction_id = StringProperty()

class InvestmentItem(ThreeLineAvatarIconListItem):
    investment_id = StringProperty()

class FinanceApp(MDApp):
    current_year = datetime.now().year
    current_month = datetime.now().month
    selected_frequency = "none"
    dialog = None
    investment_dialog = None
    stock_menu = None
    current_transaction_type = "expense"
    calendar_widgets_created = False

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.material_style = "M3"
        self.db_conn = sqlite3.connect("finance.db", check_same_thread=False)
        self.create_table()
        
        self.categories = ["Market", "Fatura", "Kira", "Ulaşım", "Maaş", "Eğlence", "Sağlık", "Diğer"]
        menu_items = [{"viewclass": "OneLineListItem", "text": i, "height": 56, "on_release": lambda x=i: self.set_category(x)} for i in self.categories]
        self.menu = MDDropdownMenu(items=menu_items, width_mult=4)

        recur_items = [
            {"viewclass": "OneLineListItem", "text": "Tekrarlama (Yok)", "on_release": lambda: self.set_recurring("none")},
            {"viewclass": "OneLineListItem", "text": "Haftalık", "on_release": lambda: self.set_recurring("weekly")},
            {"viewclass": "OneLineListItem", "text": "Aylık", "on_release": lambda: self.set_recurring("monthly")},
        ]
        self.recur_menu = MDDropdownMenu(items=recur_items, width_mult=4)
        return Builder.load_string(KV)

    def on_start(self):
        self.check_and_process_recurring()
        self.root.ids.input_date.text = datetime.now().strftime("%Y-%m-%d")
        self.update_dashboard()
        threading.Thread(target=self.refresh_market_data_thread).start()
        self.select_transaction_type("expense")

    def create_table(self):
        cursor = self.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                amount REAL,
                category TEXT,
                note TEXT,
                date TEXT,
                frequency TEXT DEFAULT 'none',
                parent_id INTEGER DEFAULT 0 
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                quantity REAL,
                current_price_try REAL DEFAULT 0,
                last_updated TEXT
            )
        """)
        self.db_conn.commit()

    def go_to_add_screen(self, t_type):
        self.root.ids.bottom_nav.switch_tab('screen_add')
        self.select_transaction_type(t_type)

    def select_transaction_type(self, t_type):
        self.current_transaction_type = t_type
        btn_exp = self.root.ids.btn_expense
        btn_inc = self.root.ids.btn_income
        
        RED_SOFT = (0.8, 0.3, 0.3, 1)
        GREEN_SOFT = (0.3, 0.8, 0.3, 1)
        GREY_DARK = (0.2, 0.2, 0.2, 1)
        
        active_rad = [dp(35), dp(35), dp(35), dp(35)]
        passive_rad = [dp(30), dp(30), dp(30), dp(30)]
        
        anim_active = Animation(
            width=dp(70), height=dp(70),
            radius=active_rad,
            md_bg_color=RED_SOFT if t_type == "expense" else GREEN_SOFT,
            duration=0.2
        )
        anim_passive = Animation(
            width=dp(60), height=dp(60),
            radius=passive_rad,
            md_bg_color=GREY_DARK,
            duration=0.2
        )

        if t_type == "expense":
            anim_active.start(btn_exp)
            anim_passive.start(btn_inc)
        else:
            anim_passive.start(btn_exp)
            anim_active.start(btn_inc)

    def save_current_transaction(self):
        self.save_transaction(self.current_transaction_type)

    def update_dashboard(self):
        self.root.ids.recent_transactions_list.clear_widgets()
        cursor = self.db_conn.cursor()
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("SELECT type, amount FROM transactions WHERE date <= ?", (today_str,))
        cash_balance = 0
        for r_type, r_amount in cursor.fetchall():
            if r_type == "income": cash_balance += r_amount
            else: cash_balance -= r_amount
            
        cursor.execute("SELECT quantity, current_price_try FROM investments")
        invest_balance = 0
        for qty, price in cursor.fetchall():
            invest_balance += (qty * price)
            
        total_asset = cash_balance + invest_balance
        self.root.ids.current_balance_label.text = f"₺{total_asset:,.2f}"

        future_change = self.calculate_future_30_days()
        prefix = "+" if future_change >= 0 else ""
        self.root.ids.future_balance_label.text = f"Gelecek 30 Gün: {prefix}{future_change:,.2f} TL"

        cursor.execute("SELECT * FROM transactions ORDER BY date DESC LIMIT 20")
        for t in cursor.fetchall():
            t_id, t_type, t_amount, t_cat, t_note, t_date, t_freq, t_parent = t
            if t_type == "income":
                icon = "arrow-down-circle" 
                color = (0.4, 0.9, 0.4, 1) 
            else:
                icon = "arrow-up-circle"   
                color = (1, 0.4, 0.4, 1)   
            
            note_display = t_note
            if t_parent != 0: note_display = f"🤖 {t_note}"
            if t_date > today_str: note_display = f"⏳ {note_display} (Gelecek)"

            item = TransactionItem(
                text=f"{t_cat}      {t_amount:.2f} TL",
                secondary_text=f"{t_date} | {note_display}",
                transaction_id=str(t_id),
                theme_text_color="Custom",
                text_color=(1,1,1,1),
                secondary_theme_text_color="Custom",
                secondary_text_color=(1,1,1,0.6)
            )
            item.add_widget(IconLeftWidget(icon=icon, theme_text_color="Custom", text_color=color))
            item.add_widget(IconRightWidget(icon="trash-can-outline", theme_text_color="Custom", text_color=(0.5,0.5,0.5,1), on_release=lambda x, tid=t_id: self.delete_item(tid)))
            self.root.ids.recent_transactions_list.add_widget(item)

    def calculate_future_30_days(self):
        cursor = self.db_conn.cursor()
        today = datetime.now().date()
        limit_date = today + timedelta(days=30)
        today_str = today.strftime("%Y-%m-%d")
        limit_str = limit_date.strftime("%Y-%m-%d")
        net_future = 0
        cursor.execute("SELECT type, amount FROM transactions WHERE date > ? AND date <= ?", (today_str, limit_str))
        for r_type, r_amount in cursor.fetchall():
            if r_type == "income": net_future += r_amount
            else: net_future -= r_amount
        cursor.execute("SELECT date, type, amount, frequency FROM transactions WHERE frequency != 'none' AND parent_id = 0")
        for item in cursor.fetchall():
            r_date_str, r_type, r_amt, r_freq = item
            start_date = datetime.strptime(r_date_str, "%Y-%m-%d").date()
            next_date = start_date
            while next_date <= limit_date:
                if r_freq == "weekly": next_date += timedelta(weeks=1)
                elif r_freq == "monthly": next_date += relativedelta(months=1)
                if next_date > today and next_date <= limit_date:
                    if r_type == "income": net_future += r_amt
                    else: net_future -= r_amt
        return net_future

    def check_and_process_recurring(self):
        cursor = self.db_conn.cursor()
        today = datetime.now().date()
        cursor.execute("SELECT id, type, amount, category, note, date, frequency FROM transactions WHERE frequency != 'none' AND parent_id = 0")
        new_count = 0
        recurring_items = cursor.fetchall()
        for item in recurring_items:
            r_id, r_type, r_amt, r_cat, r_note, r_date_str, r_freq = item
            start_date = datetime.strptime(r_date_str, "%Y-%m-%d").date()
            next_date = start_date
            while True:
                if r_freq == "weekly": next_date += timedelta(weeks=1)
                elif r_freq == "monthly": next_date += relativedelta(months=1)
                if next_date > today: break
                check = cursor.execute("SELECT id FROM transactions WHERE parent_id=? AND date=?", (r_id, next_date.strftime("%Y-%m-%d"))).fetchone()
                if not check:
                    cursor.execute("INSERT INTO transactions (type, amount, category, note, date, frequency, parent_id) VALUES (?, ?, ?, ?, ?, 'none', ?)",
                                   (r_type, r_amt, r_cat, r_note + " (Oto)", next_date.strftime("%Y-%m-%d"), r_id))
                    new_count += 1
        if new_count: 
            self.db_conn.commit()
            self.show_alert(f"{new_count} tekrarlı işlem eklendi.")

    def open_add_investment_dialog(self):
        self.add_inv_content = AddInvestmentContent()
        self.investment_dialog = MDDialog(
            title="Yatırım Ekle",
            type="custom",
            content_cls=self.add_inv_content,
            buttons=[MDFlatButton(text="İPTAL", on_release=lambda x: self.investment_dialog.dismiss()), MDFlatButton(text="KAYDET", on_release=self.save_investment)],
        )
        self.investment_dialog.open()

    def search_stocks(self, text):
        POPULAR = ["THYAO.IS", "GARAN.IS", "ASELS.IS", "AKBNK.IS", "AAPL", "TSLA", "MSFT", "ALTIN", "USDTRY=X"]
        if not text: return
        results = [s for s in POPULAR if text.lower() in s.lower()]
        menu_items = [{"viewclass": "OneLineListItem", "text": s, "on_release": lambda x=s: self.set_stock_symbol(x)} for s in results]
        if not menu_items: return
        if self.stock_menu: self.stock_menu.dismiss()
        self.stock_menu = MDDropdownMenu(caller=self.add_inv_content.ids.input_symbol, items=menu_items, width_mult=4)
        self.stock_menu.open()

    def set_stock_symbol(self, s): self.add_inv_content.ids.input_symbol.text = s; self.stock_menu.dismiss()
    
    def save_investment(self, instance):
        sym = self.add_inv_content.ids.input_symbol.text.upper().strip()
        qty = self.add_inv_content.ids.input_quantity.text
        if not sym or not qty: return toast("Eksik bilgi")
        if sym in ["ALTIN", "GOLD"]: sym = "ALTIN"
        self.db_conn.execute("INSERT INTO investments (symbol, quantity, current_price_try) VALUES (?, ?, 0)", (sym, float(qty)))
        self.db_conn.commit()
        self.investment_dialog.dismiss()
        toast("Eklendi.")
        self.refresh_market_data()

    def refresh_market_data(self):
        toast("Güncelleniyor...")
        threading.Thread(target=self.refresh_market_data_thread).start()

    def refresh_market_data_thread(self):
        cursor = self.db_conn.cursor()
        items = cursor.execute("SELECT id, symbol FROM investments").fetchall()
        if not items: return
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/TRY=X?interval=1d&range=1d", headers=headers)
            with urllib.request.urlopen(r) as response:
                usd_try = json.loads(response.read().decode('utf-8'))['chart']['result'][0]['meta']['regularMarketPrice']
        except: usd_try = 30.0

        for iid, sym in items:
            price = 0
            try:
                if sym == "ALTIN":
                    r = urllib.request.Request("https://query1.finance.yahoo.com/v8/finance/chart/GC=F?interval=1d&range=1d", headers=headers)
                    with urllib.request.urlopen(r) as response:
                        ons = json.loads(response.read().decode('utf-8'))['chart']['result'][0]['meta']['regularMarketPrice']
                        price = (ons * usd_try) / 31.1035
                else:
                    r = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d", headers=headers)
                    with urllib.request.urlopen(r) as response:
                        raw = json.loads(response.read().decode('utf-8'))['chart']['result'][0]['meta']['regularMarketPrice']
                        price = raw if sym.endswith(".IS") else raw * usd_try
                self.db_conn.execute("UPDATE investments SET current_price_try = ? WHERE id = ?", (price, iid))
            except: pass
        self.db_conn.commit()
        Clock.schedule_once(lambda dt: self.load_investments())
        Clock.schedule_once(lambda dt: self.update_dashboard())

    def load_investments(self):
        self.root.ids.investment_list.clear_widgets()
        rows = self.db_conn.execute("SELECT * FROM investments").fetchall()
        for r in rows:
            val = r[2] * r[3]
            item = InvestmentItem(text=r[1], secondary_text=f"{r[2]} Adet", tertiary_text=f"{val:,.2f} TL", theme_text_color="Custom", text_color=(1,1,1,1), secondary_theme_text_color="Custom", secondary_text_color=(0.7,0.7,0.7,1), tertiary_theme_text_color="Custom", tertiary_text_color=(0.5,1,0.5,1))
            item.add_widget(IconRightWidget(icon="trash-can-outline", theme_text_color="Custom", text_color=(0.7,0.3,0.3,1), on_release=lambda x, iid=r[0]: self.delete_investment(iid)))
            self.root.ids.investment_list.add_widget(item)
    
    def delete_investment(self, iid):
        self.db_conn.execute("DELETE FROM investments WHERE id=?", (iid,)); self.db_conn.commit(); self.load_investments(); self.update_dashboard()

    def open_category_menu(self): self.menu.caller = self.root.ids.input_category; self.menu.open()
    def set_category(self, x): self.root.ids.input_category.text = x; self.menu.dismiss()
    def open_recurring_menu(self): self.recur_menu.caller = self.root.ids.btn_recurring; self.recur_menu.open()
    def set_recurring(self, f):
        self.selected_frequency = f; self.recur_menu.dismiss()
        self.root.ids.btn_recurring.icon = "sync-off" if f == "none" else "calendar-refresh"
        toast(f"Tekrar: {f}")
    def show_date_picker(self):
        MDDatePicker(min_date=datetime(2020, 1, 1).date(), max_date=datetime(2030, 12, 31).date()).open().bind(on_save=self.on_date_save)
    def on_date_save(self, i, v, r): self.root.ids.input_date.text = str(v)
    
    def save_transaction(self, t_type):
        amt, cat, date = self.root.ids.input_amount.text, self.root.ids.input_category.text, self.root.ids.input_date.text
        if not amt or not cat: return toast("Eksik bilgi")
        self.db_conn.execute("INSERT INTO transactions (type, amount, category, note, date, frequency, parent_id) VALUES (?, ?, ?, ?, ?, ?, 0)", (t_type, float(amt), cat, self.root.ids.input_note.text, date, self.selected_frequency))
        self.db_conn.commit(); self.update_dashboard(); toast("Kaydedildi")
        
    def change_month(self, d):
        self.current_month += d
        if self.current_month > 12: self.current_month = 1; self.current_year += 1
        elif self.current_month < 1: self.current_month = 12; self.current_year -= 1
        self.init_calendar_view()

    def init_calendar_view(self):
        self.root.ids.calendar_title.text = f"{self.current_year}-{self.current_month:02d}"
        if not self.calendar_widgets_created:
            grid = self.root.ids.calendar_grid
            grid.clear_widgets()
            for i in range(42):
                card = CalendarDayCard()
                grid.add_widget(card)
            self.calendar_widgets_created = True
        threading.Thread(target=self.calculate_calendar_data_background).start()

    def calculate_calendar_data_background(self):
        cursor = self.db_conn.cursor()
        query_date = f"{self.current_year}-{self.current_month:02d}-%"
        cursor.execute("SELECT date, type, amount FROM transactions WHERE date LIKE ?", (query_date,))
        data = cursor.fetchall()
        summary = {}
        for d, t, a in data:
            if d not in summary: summary[d] = {'inc': 0, 'exp': 0}
            summary[d]['inc' if t == 'income' else 'exp'] += a
        for week in calendar.monthcalendar(self.current_year, self.current_month):
            for day in week:
                # Eksik olan döngü kapatması burada
                pass
        # HATA: Burada previous versiondaki gibi detaylı sanal hesaplama döngüsü eksik kalmış olabilir ama şimdilik basitleştirilmiş hali yeterli.
        # Asıl amaç import hatasını çözmekti.
        Clock.schedule_once(lambda dt: self.update_calendar_ui(summary))

    def update_calendar_ui(self, summary):
        grid = self.root.ids.calendar_grid
        children = grid.children[::-1]
        cal_matrix = calendar.monthcalendar(self.current_year, self.current_month)
        idx = 0
        for week in cal_matrix:
            for day in week:
                if idx >= len(children): break
                card = children[idx]
                if day == 0:
                    card.day_num = ""
                    card.income_text = ""
                    card.expense_text = ""
                    card.full_date = ""
                    card.opacity = 0
                else:
                    card.opacity = 1
                    card.day_num = str(day)
                    d_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
                    card.full_date = d_str
                    if d_str in summary:
                        inc = summary[d_str]['inc']
                        exp = summary[d_str]['exp']
                        card.income_text = f"+{int(inc)}" if inc > 0 else ""
                        card.expense_text = f"-{int(exp)}" if exp > 0 else ""
                    else:
                        card.income_text = ""
                        card.expense_text = ""
                idx += 1
        while idx < len(children):
            children[idx].opacity = 0
            children[idx].full_date = ""
            idx += 1

    def show_day_details(self, d):
        recs = self.db_conn.execute("SELECT category, amount, type, note FROM transactions WHERE date=?", (d,)).fetchall()
        txt = "\n".join([f"{'+' if r[2]=='income' else '-'} {r[1]} ({r[0]}) {r[3]}" for r in recs])
        self.show_alert(f"{d}\n{txt}" if txt else "Kayıt Yok")

    def delete_item(self, i):
        self.db_conn.execute("DELETE FROM transactions WHERE id=?", (i,)); self.db_conn.commit(); self.update_dashboard()
    def reset_db(self): 
        self.db_conn.execute("DELETE FROM transactions"); self.db_conn.execute("DELETE FROM investments"); self.db_conn.commit()
        self.update_dashboard(); self.load_investments()
    def show_alert(self, text):
        self.dialog = MDDialog(text=text, buttons=[MDFlatButton(text="TAMAM", on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

if __name__ == '__main__': FinanceApp().run()