"""
Hell Macro - Versão com Tabs
=============================
Dependências:
    pip install pyautogui keyboard

Uso:
    python auto_paste.py

Hotkey global: K (configurável) →  inicia ou para a automação
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import pyautogui
import keyboard
import json
import os
import random
from typing import Optional

# ──────────────────────────────────────────────
# Configurações globais de segurança do pyautogui
# ──────────────────────────────────────────────
pyautogui.PAUSE = 0          # sem pausa automática entre ações
pyautogui.FAILSAFE = True    # mover mouse pro canto superior-esquerdo aborta tudo

# ──────────────────────────────────────────────
# Arquivo de configuração (persistência)
# ──────────────────────────────────────────────
CONFIG_FILE = "macro_config.json"
LOG_FILE = "macro_history.log"

class AutoPasteApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Hell Macro")
        self.root.resizable(False, False)
        self.root.geometry("500x450")

        # Estado interno
        self._running = False          # True enquanto o loop estiver ativo
        self._stop_event = threading.Event()  # sinal para parar a thread
        self._thread: Optional[threading.Thread] = None
        self._thread_lock = threading.Lock()  # Previne múltiplas threads simultâneas
        self._current_hotkey = "k"     # hotkey atualmente registrada
        self._capturing_hotkey = False # se está em modo de captura de tecla
        self._listening_for_key = False # aguardando captura de nova tecla

        # Carregar configurações do cache antes de inicializar a UI
        self._load_config()

        # Opções de ações disponíveis (Lista Completa) - ANTES de inicializar as StringVars
        self._action_presets = {
            # --- Atalhos e Combinações ---
            "Ctrl+V → Enter": ("hotkey", ["ctrl", "v"], "enter"),
            "Ctrl+C": ("hotkey", ["ctrl", "c"]),
            "Ctrl+V": ("hotkey", ["ctrl", "v"]),
            "Ctrl+X": ("hotkey", ["ctrl", "x"]),
            "Ctrl+Z": ("hotkey", ["ctrl", "z"]),
            "Ctrl+S": ("hotkey", ["ctrl", "s"]),
            "Ctrl+A": ("hotkey", ["ctrl", "a"]),
            "Ctrl+W": ("hotkey", ["ctrl", "w"]),
            "Alt+Tab": ("hotkey", ["alt", "tab"]),
            "Shift+Tab": ("hotkey", ["shift", "tab"]),
            
            # --- Ações de Mouse ---
            "Clique Esquerdo": ("click", "left"),
            "Clique Direito": ("click", "right"),
            "Clique Meio (Scroll)": ("click", "middle"),

            # --- Teclas de Controle e Navegação ---
            "Enter": ("press", "enter"),
            "Espaço": ("press", "space"),
            "Tab": ("press", "tab"),
            "Backspace": ("press", "backspace"),
            "Esc": ("press", "esc"),
            "Delete": ("press", "delete"),
            "Insert": ("press", "insert"),
            "Home": ("press", "home"),
            "End": ("press", "end"),
            "Page Up": ("press", "pageup"),
            "Page Down": ("press", "pagedown"),
            "Print Screen": ("press", "printscreen"),

            # --- Setas Direcionais ---
            "Seta ↑ (Cima)": ("press", "up"),
            "Seta ↓ (Baixo)": ("press", "down"),
            "Seta ← (Esquerda)": ("press", "left"),
            "Seta → (Direita)": ("press", "right"),

            # --- Teclas de Função ---
            "F1": ("press", "f1"), "F2": ("press", "f2"),
            "F3": ("press", "f3"), "F4": ("press", "f4"),
            "F5": ("press", "f5"), "F6": ("press", "f6"),
            "F7": ("press", "f7"), "F8": ("press", "f8"),
            "F9": ("press", "f9"), "F10": ("press", "f10"),
            "F11": ("press", "f11"), "F12": ("press", "f12"),

            # --- Alfabeto ---
            "A": ("press", "a"), "B": ("press", "b"), "C": ("press", "c"),
            "D": ("press", "d"), "E": ("press", "e"), "F": ("press", "f"),
            "G": ("press", "g"), "H": ("press", "h"), "I": ("press", "i"),
            "J": ("press", "j"), "K": ("press", "k"), "L": ("press", "l"),
            "M": ("press", "m"), "N": ("press", "n"), "O": ("press", "o"),
            "P": ("press", "p"), "Q": ("press", "q"), "R": ("press", "r"),
            "S": ("press", "s"), "T": ("press", "t"), "U": ("press", "u"),
            "V": ("press", "v"), "W": ("press", "w"), "X": ("press", "x"),
            "Y": ("press", "y"), "Z": ("press", "z"),

            # --- Números (Teclado Alfanumérico) ---
            "0": ("press", "0"), "1": ("press", "1"), "2": ("press", "2"),
            "3": ("press", "3"), "4": ("press", "4"), "5": ("press", "5"),
            "6": ("press", "6"), "7": ("press", "7"), "8": ("press", "8"),
            "9": ("press", "9"),

            # --- Teclado Numérico (Numpad) ---
            "Numpad 0": ("press", "num0"), "Numpad 1": ("press", "num1"),
            "Numpad 2": ("press", "num2"), "Numpad 3": ("press", "num3"),
            "Numpad 4": ("press", "num4"), "Numpad 5": ("press", "num5"),
            "Numpad 6": ("press", "num6"), "Numpad 7": ("press", "num7"),
            "Numpad 8": ("press", "num8"), "Numpad 9": ("press", "num9"),
            "Numpad Multiplicar (*)": ("press", "multiply"),
            "Numpad Somar (+)": ("press", "add"),
            "Numpad Subtrair (-)": ("press", "subtract"),
            "Numpad Dividir (/)": ("press", "divide"),
            "Numpad Decimal (.)": ("press", "decimal"),
        }

        # Variáveis de configuração dinâmicas (inicializadas com valores carregados do cache)
        self._hotkey_display_var = tk.StringVar(value=self._current_hotkey.upper())
        self._action_display_var = tk.StringVar(value=self._current_action)
        self._button_text_var = tk.StringVar(value=f"▶  Iniciar  ({self._current_hotkey.upper()})")

        self._build_ui()
        # Atualizar o cabeçalho APÓS a UI ser construída e antes de registrar a hotkey
        self._update_header_display()
        self._register_hotkey()

    # ──────────────────────────────────────────
    # Construção da interface
    # ──────────────────────────────────────────
    def _build_ui(self):
        # ── Cabeçalho ──
        header = tk.Frame(self.root, bg="#F0803C")
        header.pack(fill="x")
        tk.Label(
            header, text="Hell Macro",
            bg="#F0803C", fg="#1e1e2e",
            font=("Segoe UI", 13, "bold"), pady=10
        ).pack()
        
        # Label dinâmico do cabeçalho
        self._header_label = tk.Label(
            header, textvariable=self._hotkey_display_var,
            bg="#F0803C", fg="#1e1e2e",
            font=("Segoe UI", 9)
        )
        self._header_label.pack(pady=(0, 8))
        
        # ── Sistema de Abas ──
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ── ABA 1: PRINCIPAL ──
        self._build_tab_principal(notebook)
        
        # ── ABA 2: HOTKEY CONF ──
        self._build_tab_hotkey_conf(notebook)
        
        # ── Créditos ──
        self._credits_label = tk.Label(
            self.root, text="Feito por Gilian",
            bg=self.root.cget("bg"), fg="gray",
            font=("Segoe UI", 7)
        )
        self._credits_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    def _build_tab_principal(self, notebook):
        """Aba Principal com controles de execução"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Principal")
        
        body = tk.Frame(tab, padx=14, pady=10)
        body.pack(fill="both", expand=True)

        # ── Intervalo ──
        tk.Label(body, text="Intervalo entre repetições", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2))

        self._interval_var = tk.DoubleVar(value=self._default_interval)  # ms

        self._slider = ttk.Scale(
            body, from_=100, to=5000,
            variable=self._interval_var,
            orient="horizontal", length=220,
            command=self._on_slider
        )
        self._slider.grid(row=1, column=0, columnspan=2, sticky="w")

        self._interval_label = tk.Label(body, text=f"{int(self._default_interval)} ms", width=7, anchor="e",
                                        font=("Segoe UI", 9))
        self._interval_label.grid(row=1, column=2, sticky="e")

        # ── Modo de repetição ──
        tk.Label(body, text="Modo de repetição", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(12, 2))

        self._mode_var = tk.StringVar(value=self._default_mode)

        mode_frame = tk.Frame(body)
        mode_frame.grid(row=3, column=0, columnspan=3, sticky="w")

        tk.Radiobutton(
            mode_frame, text="Infinito", variable=self._mode_var,
            value="infinite", command=self._on_mode_change
        ).pack(side="left")

        tk.Radiobutton(
            mode_frame, text="Finito", variable=self._mode_var,
            value="finite", command=self._on_mode_change
        ).pack(side="left", padx=(12, 4))

        # Campo de quantidade (modo finito)
        self._count_var = tk.StringVar(value=self._default_count)
        self._count_entry = ttk.Entry(
            mode_frame, textvariable=self._count_var, width=5, state="disabled" if self._default_mode == "infinite" else "normal"
        )
        self._count_entry.pack(side="left")
        tk.Label(mode_frame, text="× (máx. 100)", font=("Segoe UI", 8),
                 fg="gray").pack(side="left", padx=4)

        # ── Botão Iniciar/Parar ──
        self._btn = tk.Button(
            body, textvariable=self._button_text_var,
            font=("Segoe UI", 10, "bold"),
            bg="#F0803C", fg="#1e1e2e",
            activebackground="#AF3800",
            relief="flat", bd=0, padx=12, pady=6,
            cursor="hand2",
            command=self._toggle
        )
        self._btn.grid(row=4, column=0, columnspan=3, pady=(16, 4), sticky="ew")

        # ── Status ──
        self._status_var = tk.StringVar(value="Aguardando...")
        tk.Label(body, textvariable=self._status_var,
                 font=("Segoe UI", 8), fg="gray").grid(
            row=5, column=0, columnspan=3)

        # ── Progresso (modo finito) ──
        self._progress_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self._progress_var,
                 font=("Segoe UI", 8), fg="#a6e3a1").grid(
            row=6, column=0, columnspan=3)

    def _build_tab_hotkey_conf(self, notebook):
        """Aba de Configuração de Hotkey e Ações"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Hotkey Conf")
        
        body = tk.Frame(tab, padx=14, pady=10)
        body.pack(fill="both", expand=True)

        # ── Configurar Hotkey ──
        tk.Label(body, text="Configurar Hotkey de Ativação", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        tk.Label(body, text="Hotkey atual:", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=(2, 6))
        
        self._hotkey_current_label = tk.Label(
            body, text=self._current_hotkey.upper(),
            font=("Segoe UI", 9, "bold"), fg="#1e1e2e"
        )
        self._hotkey_current_label.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(2, 6))

        tk.Label(body, text="Nova hotkey:", font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky="w", pady=(2, 8))
        
        self._hotkey_input = tk.StringVar(value="")
        self._hotkey_entry = ttk.Entry(body, textvariable=self._hotkey_input, width=20)
        self._hotkey_entry.grid(row=2, column=1, sticky="w", padx=(10, 0), pady=(2, 8))

        # Botão de captura
        self._capture_btn = tk.Button(
            body, text="Capturar Tecla",
            font=("Segoe UI", 9),
            bg="#F0803C", fg="#1e1e2e",
            activebackground="#AF3800",
            relief="flat", bd=0, padx=8, pady=4,
            cursor="hand2",
            command=self._start_hotkey_capture
        )
        self._capture_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        tk.Label(body, text="(Clique para capturar, depois pressione a tecla desejada)", 
                 font=("Segoe UI", 8), fg="gray").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 12))

        # ── Separador ──
        ttk.Separator(body, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=12)

        # ── Configurar Ação Repetida ──
        tk.Label(body, text="Ação a Repetir", font=("Segoe UI", 10, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(0, 6))

        tk.Label(body, text="Selecione a ação:", font=("Segoe UI", 9)).grid(
            row=7, column=0, sticky="w", pady=(2, 8))

        self._action_var = tk.StringVar(value=self._current_action)
        action_combo = ttk.Combobox(
            body, textvariable=self._action_var,
            values=list(self._action_presets.keys()),
            state="readonly", width=25
        )
        action_combo.grid(row=7, column=1, sticky="ew", padx=(10, 0), pady=(2, 8))
        action_combo.bind("<<ComboboxSelected>>", self._on_action_changed)

        # Descrição da ação atual
        tk.Label(body, text="Ação atual:", font=("Segoe UI", 9)).grid(
            row=8, column=0, sticky="w", pady=(4, 12))
        
        self._action_current_label = tk.Label(
            body, textvariable=self._action_display_var,
            font=("Segoe UI", 9, "bold"), fg="#1e1e2e"
        )
        self._action_current_label.grid(row=8, column=1, sticky="w", padx=(10, 0), pady=(4, 12))

    # ──────────────────────────────────────────
    # Persistência de Configurações
    # ──────────────────────────────────────────
    def _load_config(self):
        """Carrega as configurações do arquivo JSON"""
        # Valores padrão
        default_hotkey = "k"
        default_action = "Ctrl+V → Enter"
        default_interval = 500
        default_mode = "infinite"
        default_count = "10"
        default_random_variance = 0  # 0% = sem variação
        
        # Tentar carregar do arquivo
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self._current_hotkey = config.get("hotkey", default_hotkey)
                    self._current_action = config.get("action", default_action)
                    self._default_interval = config.get("interval", default_interval)
                    self._default_mode = config.get("mode", default_mode)
                    self._default_count = config.get("count", default_count)
                    self._default_random_variance = config.get("random_variance", default_random_variance)
                    return
            except Exception as e:
                print(f"Erro ao carregar configurações: {e}")
        
        # Se não conseguir carregar, usar padrões
        self._current_hotkey = default_hotkey
        self._current_action = default_action
        self._default_interval = default_interval
        self._default_mode = default_mode
        self._default_count = default_count
        self._default_random_variance = default_random_variance

    def _save_config(self):
        """Salva as configurações no arquivo JSON"""
        config = {
            "hotkey": self._current_hotkey,
            "action": self._current_action,
            "interval": self._interval_var.get(),
            "mode": self._mode_var.get(),
            "count": self._count_var.get(),
            "random_variance": getattr(self, '_random_variance_var', tk.DoubleVar(value=0)).get() if hasattr(self, '_random_variance_var') else self._default_random_variance
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    # ──────────────────────────────────────────
    # Callbacks de UI
    # ──────────────────────────────────────────
    def _on_slider(self, value):
        ms = int(float(value))
        self._interval_label.config(text=f"{ms} ms")

    def _on_mode_change(self):
        if self._mode_var.get() == "finite":
            self._count_entry.config(state="normal")
        else:
            self._count_entry.config(state="disabled")

    def _on_action_changed(self, event=None):
        """Callback quando a ação é alterada no combobox"""
        new_action = self._action_var.get()
        if new_action in self._action_presets:
            self._current_action = new_action
            self._action_display_var.set(new_action)

    def _disable_controls(self) -> None:
        """Desabilita controles enquanto a macro está rodando"""
        self._slider.config(state="disabled")
        self._action_var.set(self._current_action)  # garante valor correto
        # Desabilita modo de captura
        self._capture_btn.config(state="disabled", text="Macro Ativa...")
        # Impede mudança de modo enquanto rodando
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Notebook):
                for tab_idx in range(widget.index("end")):
                    tab = widget.winfo_children()[tab_idx]
                    for child in tab.winfo_children():
                        if isinstance(child, tk.Frame):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, (ttk.Radiobutton, ttk.Entry, ttk.Combobox)):
                                    if hasattr(subchild, "config"):
                                        subchild.config(state="disabled")

    def _enable_controls(self) -> None:
        """Reabilita controles após parar a macro"""
        self._slider.config(state="normal")
        self._capture_btn.config(state="normal", text="Capturar Tecla", bg="#F0803C")
        # Reabilita modo de captura
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Notebook):
                for tab_idx in range(widget.index("end")):
                    tab = widget.winfo_children()[tab_idx]
                    for child in tab.winfo_children():
                        if isinstance(child, tk.Frame):
                            for subchild in child.winfo_children():
                                if isinstance(subchild, (ttk.Radiobutton, ttk.Entry, ttk.Combobox)):
                                    if hasattr(subchild, "config"):
                                        subchild.config(state="normal")

    def _update_header_display(self):
        """Atualiza o display do cabeçalho com hotkey e ação dinâmicas"""
        hotkey_display = self._current_hotkey.upper()
        action_display = self._current_action
        self._hotkey_display_var.set(f"Hotkey: {hotkey_display}  |  {action_display}")

    def _update_button_text(self):
        """Atualiza o texto dinâmico do botão com base no hotkey atual"""
        hotkey_upper = self._current_hotkey.upper()
        if self._running:
            self._button_text_var.set(f"■  Parar  ({hotkey_upper})")
        else:
            self._button_text_var.set(f"▶  Iniciar  ({hotkey_upper})")

    def _start_hotkey_capture(self):
        """Inicia o modo de captura de tecla para nova hotkey"""
        self._capturing_hotkey = True
        self._capture_btn.config(text="Aguardando tecla...", bg="#f38ba8", state="disabled")
        self._hotkey_entry.config(state="normal")
        self._hotkey_entry.delete(0, tk.END)
        
        # Inicia thread para capturar a próxima tecla
        capture_thread = threading.Thread(target=self._capture_next_key, daemon=True)
        capture_thread.start()

    def _capture_next_key(self) -> None:
        """Captura a próxima tecla pressionada (com timeout de 5s)"""
        try:
            # Aguarda por uma tecla com timeout
            event = keyboard.read_event(suppress=False)
            if event.event_type == "down":
                key_name = event.name.lower()
                self.root.after(0, self._apply_new_hotkey, key_name)
        except Exception as e:
            self.root.after(0, self._status_var.set, 
                          f"⚠ Erro na captura de tecla: {str(e)[:40]}")
            print(f"[ERRO] Captura de tecla: {e}")
        finally:
            self._capturing_hotkey = False
            self.root.after(0, self._capture_btn.config, 
                          {"text": "Capturar Tecla", "bg": "#F0803C", "state": "normal"})

    def _apply_new_hotkey(self, new_key: str):
        """Aplica a nova hotkey"""
        if new_key and new_key != "esc":
            # Desregistra a hotkey antiga
            try:
                keyboard.remove_hotkey(self._current_hotkey)
            except:
                pass
            
            # Atualiza para a nova hotkey
            self._current_hotkey = new_key
            self._hotkey_entry.delete(0, tk.END)
            self._hotkey_entry.insert(0, new_key.upper())
            self._hotkey_current_label.config(text=new_key.upper())
            
            # Registra a nova hotkey
            self._register_hotkey()
            
            # Atualiza displays
            self._update_header_display()
            self._update_button_text()
        
        # Restaura o botão
        self._capture_btn.config(text="Capturar Tecla", bg="#F0803C", state="normal")

    # ──────────────────────────────────────────
    # Registro do hotkey global
    # ──────────────────────────────────────────
    def _register_hotkey(self):
        # O callback do keyboard é chamado numa thread separada pelo próprio
        # pacote; usamos root.after() para manter thread-safety com tkinter
        try:
            # Remove hotkey antiga se existir
            keyboard.remove_hotkey(self._current_hotkey)
        except:
            pass
        
        # Registra nova hotkey
        keyboard.add_hotkey(self._current_hotkey, 
                          lambda: self.root.after(0, self._toggle))

    # ──────────────────────────────────────────
    # Liga / desliga a automação
    # ──────────────────────────────────────────
    def _toggle(self):
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self):
        # Protege contra múltiplas threads simultâneas
        if not self._thread_lock.acquire(blocking=False):
            self._status_var.set("⚠ Macro já está em execução.")
            return
        
        # Valida quantidade no modo finito
        if self._mode_var.get() == "finite":
            try:
                count = int(self._count_var.get())
                if not (1 <= count <= 100):
                    raise ValueError
            except ValueError:
                self._status_var.set("⚠ Quantidade inválida (1–100).")
                self._thread_lock.release()
                return

        self._running = True
        self._stop_event.clear()
        self._progress_var.set("")
        self._disable_controls()

        # Atualiza botão com hotkey dinâmica
        hotkey_upper = self._current_hotkey.upper()
        self._button_text_var.set(f"■  Parar  ({hotkey_upper})")
        self._btn.config(bg="#f38ba8", fg="#1e1e2e",
                         activebackground="#eba0ac")
        self._status_var.set("Rodando...")

        # Log de início
        mode_info = f"infinito" if self._mode_var.get() == "infinite" else f"{self._count_var.get()}x"
        self._log_action(f"✓ Macro iniciada - Modo: {mode_info}, Ação: {self._current_action}", "INFO")

        # Inicia loop numa thread separada (não congela a UI)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _stop(self):
        self._stop_event.set()   # sinaliza para a thread parar
        self._running = False
        self._enable_controls()
        
        # Log de parada
        self._log_action("⏹ Macro parada", "INFO")
        
        # Atualiza botão com hotkey dinâmica
        hotkey_upper = self._current_hotkey.upper()
        self._button_text_var.set(f"▶  Iniciar  ({hotkey_upper})")
        self._btn.config(bg="#F0803C", fg="#1e1e2e",
                         activebackground="#AF3800")
        self._status_var.set("Parado.")
        
        # Libera lock da thread
        try:
            self._thread_lock.release()
        except RuntimeError:
            pass  # Lock já foi liberado ou nunca foi adquirido

    # ──────────────────────────────────────────
    # Loop de automação (roda em thread separada)
    # ──────────────────────────────────────────
    def _execute_action(self) -> None:
        """Executa a ação configurada com tratamento robusto de erros"""
        if self._current_action not in self._action_presets:
            error_msg = f"Ação '{self._current_action}' não encontrada."
            self._log_action(error_msg, "ERROR")
            self.root.after(0, self._status_var.set, f"⚠ {error_msg}")
            return
        
        try:
            action_info = self._action_presets[self._current_action]
            action_type = action_info[0]
            
            if action_type == "hotkey":
                # Executa combinação de hotkeys: ["ctrl", "v"] seguido de "enter"
                keys_to_press = action_info[1:]
                for key_spec in keys_to_press:
                    if isinstance(key_spec, list):
                        # Lista de teclas para hotkey, ex: ["ctrl", "v"]
                        pyautogui.hotkey(*key_spec)
                    else:
                        # Tecla única para press, ex: "enter"
                        pyautogui.press(key_spec)
            
            elif action_type == "press":
                # Pressiona uma tecla única
                key = action_info[1]
                pyautogui.press(key)
            
            elif action_type == "click":
                # Realiza um clique de mouse
                button = action_info[1]
                pyautogui.click(button=button)
            
            # Log de sucesso
            self._log_action(f"✓ Ação executada: '{self._current_action}'", "INFO")
        
        except Exception as e:
            error_msg = f"Erro ao executar ação: {str(e)[:50]}"
            self._log_action(error_msg, "ERROR")
            self.root.after(0, self._status_var.set, f"⚠ {error_msg}")
            print(f"[ERRO] _execute_action: {e}")

    def _loop(self):
        interval_s = self._interval_var.get() / 1000.0  # converte ms → s
        infinite = self._mode_var.get() == "infinite"
        total = int(self._count_var.get()) if not infinite else None
        done = 0
        # Variância aleatória para anti-cheat (padrão: 0% = sem variação)
        random_variance = self._default_random_variance

        while not self._stop_event.is_set():
            # ── Ação principal (dinâmica) ──
            self._execute_action()
            done += 1

            # Atualiza progresso na UI de forma thread-safe
            if not infinite:
                self.root.after(0, self._progress_var.set,
                                f"{done} / {total} repetições")
                if done >= total:
                    break  # modo finito: atingiu o limite

            # Calcula delay com variância aleatória (anti-cheat)
            if random_variance > 0:
                variance_factor = random.uniform(1 - (random_variance / 100), 1 + (random_variance / 100))
                actual_interval = interval_s * variance_factor
            else:
                actual_interval = interval_s

            # Aguarda o intervalo, mas verifica o stop_event a cada 50 ms
            # para não travar a parada quando o intervalo é grande
            elapsed = 0.0
            step = 0.05
            while elapsed < actual_interval and not self._stop_event.is_set():
                time.sleep(step)
                elapsed += step

        # Garante que o estado da UI seja atualizado ao final (de forma segura)
        self.root.after(0, self._stop)

    # ──────────────────────────────────────────
    # Limpeza ao fechar a janela
    # ──────────────────────────────────────────
    def on_close(self):
        self._stop_event.set()
        self._save_config()
        keyboard.unhook_all()
        self.root.destroy()

    # ──────────────────────────────────────────
    # Logging e Histórico
    # ──────────────────────────────────────────
    def _log_action(self, message: str, level: str = "INFO") -> None:
        """Registra ações no arquivo de log com timestamp"""
        from datetime import datetime
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            log_message = f"[{timestamp}] [{level}] {message}\n"
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_message)
        except Exception as e:
            print(f"Erro ao logar: {e}")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = AutoPasteApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
