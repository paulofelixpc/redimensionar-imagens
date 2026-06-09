import os
import sys
import tempfile
import traceback
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QRadioButton,
    QFileDialog, QMessageBox, QSlider, QCheckBox,
    QMenuBar, QMenu, QSystemTrayIcon, QProgressBar,
    QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QPixmap, QImage, QIcon, QShortcut, QKeySequence, QAction, QColor
from PySide6.QtCore import Qt, QThread, Signal, QTimer

try:
    from PySide6.QtWinExtras import QWinTaskbarButton, QWinTaskbarProgress
    HAS_TASKBAR = True
except ImportError:
    HAS_TASKBAR = False

from redimensionar.image_processor import (
    TAMANHO, MAX_BYTES_NORMAL, MAX_BYTES_REMFUNDO,
    corrigir_orientacao, recortar_e_redimensionar,
    ajustar_qualidade, remover_fundo, aplicar_marca_dagua,
)
from redimensionar.crop_widget import CropWidget
from redimensionar.logger import get_logger
from redimensionar.theme import aplicar_tema


log = get_logger("app")


class WorkerBatch(QThread):
    progresso = Signal(str, int, int)
    finalizado = Signal(int, list, str)
    cancelado = Signal()

    def __init__(self, arquivos, pasta, nome_base, remover, max_bytes, coords_list, escala_porc=100, logo_path=None):
        super().__init__()
        self.arquivos = arquivos
        self.pasta = pasta
        self.nome_base = nome_base
        self.remover = remover
        self.max_bytes = max_bytes
        self.coords_list = coords_list
        self.escala_porc = escala_porc
        self.logo_path = logo_path
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        erros = []
        ok = 0
        total = len(self.arquivos)
        log.info("Processamento iniciado — %d imagem(ns)", total)

        for i, caminho in enumerate(self.arquivos):
            if self._cancelled:
                log.info("Processamento cancelado pelo usuário")
                self.cancelado.emit()
                return

            try:
                self.progresso.emit(os.path.basename(caminho), i, total)
                img = Image.open(caminho)
                img = corrigir_orientacao(img).convert("RGB")
                left, top, lado = self.coords_list[i]
                img = recortar_e_redimensionar(img, left, top, lado)

                if self.remover:
                    log.debug("WorkerBatch: chamando remover_fundo com escala=%d", self.escala_porc)
                    img = remover_fundo(img, self.escala_porc)

                if self.logo_path:
                    img = aplicar_marca_dagua(img, self.logo_path)

                buf = ajustar_qualidade(img, self.max_bytes)
                nome_final = f"{self.nome_base}.jpg" if total == 1 else f"{self.nome_base}-{i + 1}.jpg"
                dest = os.path.join(self.pasta, nome_final)
                fd, tmp = tempfile.mkstemp(dir=self.pasta, suffix=".jpg")
                try:
                    with os.fdopen(fd, "wb") as f:
                        f.write(buf.getvalue())
                    os.replace(tmp, dest)
                except Exception:
                    try:
                        os.unlink(tmp)
                    except Exception:
                        pass
                    raise
                ok += 1
            except Exception as e:
                log.exception("Erro ao processar %s", caminho)
                erros.append(f"{os.path.basename(caminho)}: {e}")

            self.progresso.emit("", i + 1, total)

        if self._cancelled:
            log.info("Processamento cancelado pelo usuário")
            self.cancelado.emit()
            return

        log.info("Processamento finalizado — %d ok, %d erros", ok, len(erros))
        self.finalizado.emit(ok, erros, self.pasta)


VERSION = "1.3.0"


class App(QMainWindow):
    def __init__(self):
        log.debug("App.__init__: inicio")
        super().__init__()
        log.debug("App.__init__: super ok")
        self.setWindowTitle(f"Redimensionar Imagens — {TAMANHO}x{TAMANHO}")
        self.setMinimumSize(860, 680)
        self.resize(960, 760)

        self.arquivos = []
        self.previa_index = 0
        self._coords_por_imagem = {}
        self._logo_path = None
        self._process_start = None
        self._tray = None
        self._taskbar_button = None
        self._taskbar_progress = None

        log.debug("App.__init__: atributos ok")
        self._config_path = os.path.join(os.path.expanduser("~"), ".ls-imagecomm", "config.json")
        self._dark_mode = self._load_config("dark_mode", False)

        # Create crop widget first (sidebar controls reference it)
        self.crop_widget = CropWidget()

        central = QWidget()
        log.debug("App.__init__: QWidget ok")
        self.setCentralWidget(central)

        # ── ROOT: horizontal split with 24px outer margins and 24px spacing ──
        root = QHBoxLayout(central)
        root.setSpacing(24)
        root.setContentsMargins(24, 24, 24, 24)

        # ════════════════════════════════════════════════════════════════════
        # ── LEFT: Stage ──
        # ════════════════════════════════════════════════════════════════════
        left = QVBoxLayout()
        left.setSpacing(0)

        # Stage container
        stage = QFrame()
        stage.setObjectName("stage")
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(0, 0, 0, 0)
        stage_layout.addWidget(self.crop_widget)
        left.addWidget(stage, stretch=1)

        # Controls below stage
        ctrl_area = QVBoxLayout()
        ctrl_area.setSpacing(8)
        ctrl_area.setContentsMargins(0, 16, 0, 0)

        # Zoom buttons centered
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(4)
        zoom_layout.addStretch()
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setToolTip("Reduzir zoom (Ctrl+-)")
        self.btn_zoom_out.setFixedSize(40, 34)
        self.btn_zoom_out.setStyleSheet("QPushButton { font-size: 20px; font-weight: 700; }")
        self.btn_zoom_out.clicked.connect(self.crop_widget.zoom_out)
        zoom_layout.addWidget(self.btn_zoom_out)
        btn_zoom_fit = QPushButton("Ajustar")
        btn_zoom_fit.setToolTip("Ajustar zoom à janela (Ctrl+0)")
        btn_zoom_fit.setFixedHeight(34)
        btn_zoom_fit.setStyleSheet("QPushButton { padding: 0 18px; font-size: 10pt; }")
        btn_zoom_fit.clicked.connect(self.crop_widget.zoom_fit)
        zoom_layout.addWidget(btn_zoom_fit)
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setToolTip("Aumentar zoom (Ctrl++)")
        self.btn_zoom_in.setFixedSize(40, 34)
        self.btn_zoom_in.setStyleSheet("QPushButton { font-size: 20px; font-weight: 700; }")
        self.btn_zoom_in.clicked.connect(self.crop_widget.zoom_in)
        zoom_layout.addWidget(self.btn_zoom_in)
        zoom_layout.addStretch()
        ctrl_area.addLayout(zoom_layout)

        # Progress bar
        self.progresso_barra = QProgressBar()
        self.progresso_barra.setRange(0, 100)
        self.progresso_barra.setValue(0)
        self.progresso_barra.setTextVisible(False)
        self.progresso_barra.hide()
        ctrl_area.addWidget(self.progresso_barra)

        # Cancel button
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btnCancelar")
        self.btn_cancelar.setStyleSheet("QPushButton { background: transparent; color: #E17055; border: 1px solid #E17055; border-radius: 4px; padding: 4px 16px; font-size: 9pt; } QPushButton:hover { background: #E17055; color: white; }")
        self.btn_cancelar.clicked.connect(self._cancelar_processamento)
        self.btn_cancelar.hide()
        ctrl_area.addWidget(self.btn_cancelar, alignment=Qt.AlignCenter)

        # Status label
        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("statusLabel")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        ctrl_area.addWidget(self.lbl_status)

        left.addLayout(ctrl_area)

        root.addLayout(left, stretch=7)

        # ════════════════════════════════════════════════════════════════════
        # ── RIGHT: Inspector (fixed 320px) ──
        # ════════════════════════════════════════════════════════════════════
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(320)
        card.setMaximumWidth(320)
        shadow_card = QGraphicsDropShadowEffect()
        shadow_card.setBlurRadius(16)
        shadow_card.setOffset(0, 4)
        shadow_card.setColor(QColor(0, 0, 0, 50))
        card.setGraphicsEffect(shadow_card)

        cfg = QVBoxLayout(card)
        cfg.setContentsMargins(24, 24, 24, 24)
        cfg.setSpacing(24)

        # ── MODO ──
        lbl_modo = QLabel("MODO")
        lbl_modo.setObjectName("sectionTitle")
        cfg.addWidget(lbl_modo)

        self.rb_redim = QRadioButton("Apenas redimensionar")
        self.rb_redim.setToolTip("Corta e redimensiona para 1200×1200 (máx 2MB por arquivo)")
        cfg.addWidget(self.rb_redim)
        self.rb_rem = QRadioButton("Remover fundo + redimensionar")
        self.rb_rem.setToolTip("Remove o fundo com IA e redimensiona para 1200×1200 (máx 350KB)")
        cfg.addWidget(self.rb_rem)
        self.rb_redim.setChecked(True)

        # ── ARQUIVOS ──
        lbl_arq = QLabel("ARQUIVOS")
        lbl_arq.setObjectName("sectionTitle")
        cfg.addWidget(lbl_arq)

        row_arq = QHBoxLayout()
        row_arq.setSpacing(8)
        self.btn_selecionar = QPushButton("Selecionar")
        self.btn_selecionar.setObjectName("btnSelecionar")
        self.btn_selecionar.setToolTip("Escolha as imagens que deseja processar (Ctrl+O)")
        self.btn_selecionar.clicked.connect(self.selecionar)
        row_arq.addWidget(self.btn_selecionar)
        self.entry_path = QLineEdit()
        self.entry_path.setReadOnly(True)
        self.entry_path.setPlaceholderText("Nenhuma imagem selecionada")
        row_arq.addWidget(self.entry_path, stretch=1)
        cfg.addLayout(row_arq)

        row_nome = QHBoxLayout()
        row_nome.setSpacing(8)
        self.entry_nome = QLineEdit()
        self.entry_nome.setPlaceholderText("Nome do produto")
        self.entry_nome.setToolTip("Nome base para os arquivos de saída\nPreenchido automaticamente com o nome da primeira imagem")
        row_nome.addWidget(self.entry_nome)
        lbl_sfx = QLabel("-1, -2…")
        lbl_sfx.setStyleSheet("color: #999; font-size: 9pt;")
        row_nome.addWidget(lbl_sfx)
        cfg.addLayout(row_nome)

        # ── AJUSTES ──
        lbl_ajustes = QLabel("AJUSTES")
        lbl_ajustes.setObjectName("sectionTitle")
        cfg.addWidget(lbl_ajustes)

        # Escala
        row_escala = QHBoxLayout()
        row_escala.setSpacing(8)
        lbl_est = QLabel("Escala:")
        lbl_est.setToolTip("Controla o tamanho do produto na imagem final (modo remover fundo)")
        row_escala.addWidget(lbl_est)
        self.escala_slider = QSlider(Qt.Horizontal)
        self.escala_slider.setRange(10, 100)
        self.escala_slider.setValue(100)
        self.escala_slider.setToolTip("Quanto menor, mais espaço em branco ao redor do produto")
        row_escala.addWidget(self.escala_slider, stretch=1)
        self.lbl_escala = QLabel("100%")
        self.lbl_escala.setObjectName("escalaVal")
        self.lbl_escala.setFixedWidth(36)
        self.lbl_escala.setAlignment(Qt.AlignRight)
        row_escala.addWidget(self.lbl_escala)
        self.escala_slider.valueChanged.connect(lambda v: self.lbl_escala.setText(f"{v}%"))
        cfg.addLayout(row_escala)

        # Photo navigation frame
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        nav_layout.setContentsMargins(8, 4, 8, 4)
        nav_layout.setSpacing(8)
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("btnNav")
        self.btn_prev.setToolTip("Imagem anterior (←)")
        self.btn_prev.clicked.connect(self.anterior)
        nav_layout.addWidget(self.btn_prev)
        self.lbl_contador = QLabel("")
        self.lbl_contador.setAlignment(Qt.AlignCenter)
        self.lbl_contador.setStyleSheet("font-weight: 500;")
        nav_layout.addWidget(self.lbl_contador, stretch=1)
        self.btn_prox = QPushButton("▶")
        self.btn_prox.setObjectName("btnNav")
        self.btn_prox.setToolTip("Próxima imagem (→)")
        self.btn_prox.clicked.connect(self.proximo)
        nav_layout.addWidget(self.btn_prox)
        cfg.addWidget(nav_frame)

        # Watermark
        row_marca = QHBoxLayout()
        row_marca.setSpacing(8)
        self.chk_marca = QCheckBox("Marca d'água")
        self.chk_marca.setToolTip("Aplica uma grade diagonal do seu logo sobre a imagem")
        row_marca.addWidget(self.chk_marca)
        self.btn_logo = QPushButton("Logo…")
        self.btn_logo.setToolTip("Escolha uma imagem PNG para usar como marca d'água")
        self.btn_logo.clicked.connect(self.selecionar_logo)
        self.btn_logo.setEnabled(False)
        row_marca.addWidget(self.btn_logo)
        self.lbl_logo = QLabel("")
        self.lbl_logo.setStyleSheet("color: #999; font-size: 11px;")
        row_marca.addWidget(self.lbl_logo, stretch=1)
        self.chk_marca.toggled.connect(self.btn_logo.setEnabled)
        cfg.addLayout(row_marca)

        # Push CTA to bottom
        cfg.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # CTA button
        self.btn_processar = QPushButton("PROCESSAR E SALVAR")
        self.btn_processar.setObjectName("btnProcessar")
        self.btn_processar.setEnabled(False)
        self.btn_processar.setToolTip("Iniciar o processamento e escolher pasta de destino (Ctrl+S)")
        self.btn_processar.clicked.connect(self.iniciar_processamento)
        cfg.addWidget(self.btn_processar)

        root.addWidget(card, alignment=Qt.AlignTop)

        # ── Shortcuts ──
        QShortcut(QKeySequence("Ctrl+O"), self, self.selecionar)
        QShortcut(QKeySequence("Ctrl+S"), self, self.iniciar_processamento)
        QShortcut(QKeySequence("Ctrl++"), self, self.crop_widget.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.crop_widget.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.crop_widget.zoom_fit)
        QShortcut(QKeySequence(Qt.Key_Left), self, self.anterior)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.proximo)

        self.setTabOrder(self.entry_path, self.btn_selecionar)
        self.setTabOrder(self.btn_selecionar, self.rb_redim)
        self.setTabOrder(self.rb_redim, self.rb_rem)
        self.setTabOrder(self.rb_rem, self.chk_marca)
        self.setTabOrder(self.chk_marca, self.btn_logo)
        self.setTabOrder(self.btn_logo, self.btn_processar)

        log.debug("App.__init__: criando menu")
        self._criar_menu()
        log.debug("App.__init__: menu ok")

        QTimer.singleShot(0, self._init_extras)

    def _criar_menu(self):
        bar = self.menuBar()

        arq = bar.addMenu("Arquivo")
        arq.addAction("Abrir Imagens", self.selecionar, QKeySequence("Ctrl+O"))
        arq.addAction("Processar e Salvar", self.iniciar_processamento, QKeySequence("Ctrl+S"))
        arq.addSeparator()
        arq.addAction("Sair", self.close, QKeySequence("Alt+F4"))

        view = bar.addMenu("Exibir")
        view.addAction("Aumentar Zoom", self.crop_widget.zoom_in, QKeySequence("Ctrl++"))
        view.addAction("Diminuir Zoom", self.crop_widget.zoom_out, QKeySequence("Ctrl+-"))
        view.addAction("Ajustar à Tela", self.crop_widget.zoom_fit, QKeySequence("Ctrl+0"))
        view.addSeparator()
        self._act_tema = view.addAction("Alternar Tema Escuro")
        self._act_tema.setCheckable(True)
        self._act_tema.setChecked(self._dark_mode)
        self._act_tema.triggered.connect(self._toggle_tema)

        ajuda = bar.addMenu("Ajuda")
        ajuda.addAction("Sobre o LS Imagecomm", self._mostrar_sobre)

    def _mostrar_sobre(self):
        QMessageBox.about(self, "Sobre o LS Imagecomm",
            f"<h2>LS Imagecomm</h2>"
            f"<p>Redimensiona imagens para <b>1200×1200</b>,<br>"
            f"remove fundo com <b>IA</b> e adiciona <b>marca d'água</b>.</p>"
            f"<hr>"
            f"<p>Versão: <b>{VERSION}</b><br>"
            f"Totalmente <b>offline</b> — seus arquivos nunca saem do seu computador.</p>"
            f"<p style='color: #888; font-size: 11px;'>"
            f"LS Imagecomm © 2026</p>")

    def _init_extras(self):
        log.debug("_init_extras: iniciando")
        self._criar_tray()
        self._init_taskbar()
        log.debug("_init_extras: ok")

    def _criar_tray(self):
        try:
            icon = self.windowIcon()
            if icon.isNull():
                return
            self._tray = QSystemTrayIcon(icon, self)
            menu = QMenu(self)
            menu.addAction("Abrir", self.show)
            menu.addAction("Sair", self.close)
            self._tray.setContextMenu(menu)
            self._tray.show()
        except Exception:
            log.exception("Falha ao criar tray icon")
            self._tray = None

    def _init_taskbar(self):
        if not HAS_TASKBAR:
            return
        hwnd = self.windowHandle()
        if hwnd is None:
            return
        try:
            self._taskbar_button = QWinTaskbarButton(self)
            self._taskbar_button.setWindow(hwnd)
            self._taskbar_progress = self._taskbar_button.progress()
            self._taskbar_progress.setRange(0, 100)
            self._taskbar_progress.hide()
        except Exception:
            log.exception("Falha ao inicializar taskbar progress")
            self._taskbar_button = None
            self._taskbar_progress = None

    def selecionar(self):
        arquivos, _ = QFileDialog.getOpenFileNames(
            self, "Selecione as imagens",
            "",
            "Imagens (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff);;Todos (*.*)"
        )
        if not arquivos:
            return
        self.arquivos = arquivos
        self._coords_por_imagem = {}
        self.previa_index = 0
        if len(arquivos) == 1:
            self.entry_path.setText(arquivos[0])
        else:
            self.entry_path.setText(f"{len(arquivos)} imagens selecionadas")

        # Auto-fill product name from first file if field is empty
        if not self.entry_nome.text():
            nome = os.path.splitext(os.path.basename(arquivos[0]))[0]
            nome = self._sanitizar_nome(nome)
            self.entry_nome.setText(nome)

        self.btn_processar.setEnabled(True)
        self.mostrar_previa()

    def selecionar_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar logo para marca d'água",
            "", "Imagens (*.png *.jpg *.jpeg *.webp *.bmp);;Todos (*.*)"
        )
        if path:
            self._logo_path = path
            self.lbl_logo.setText(os.path.basename(path))

    def mostrar_previa(self):
        if not self.arquivos:
            return
        caminho = self.arquivos[self.previa_index]
        try:
            log.debug("mostrar_previa: abrindo %s", caminho)
            img = Image.open(caminho)
            log.debug("mostrar_previa: Image.open ok, mode=%s size=%s", img.mode, img.size)
            img = corrigir_orientacao(img)
            log.debug("mostrar_previa: corrigir_orientacao ok, mode=%s", img.mode)
            self.crop_widget.set_image(img)
            log.debug("mostrar_previa: set_image ok")

            if caminho in self._coords_por_imagem:
                left, top, lado = self._coords_por_imagem[caminho]
                self.crop_widget.set_crop_coords(left, top, lado)

            nome = os.path.basename(caminho)
            self.lbl_contador.setText(f"{self.previa_index + 1}/{len(self.arquivos)} — {nome}")
        except Exception:
            log.exception("Erro ao abrir prévia: %s", caminho)

    def anterior(self):
        if self.arquivos:
            self._salvar_coords()
            self.previa_index = (self.previa_index - 1) % len(self.arquivos)
            self.mostrar_previa()

    def proximo(self):
        if self.arquivos:
            self._salvar_coords()
            self.previa_index = (self.previa_index + 1) % len(self.arquivos)
            self.mostrar_previa()

    def _salvar_coords(self):
        caminho = self.arquivos[self.previa_index]
        left, top, lado = self.crop_widget.crop_coords_pil()
        if left is not None:
            self._coords_por_imagem[caminho] = (left, top, lado)

    def iniciar_processamento(self):
        if not self.arquivos:
            return

        pasta_dir = os.path.dirname(self.arquivos[0]) if self.arquivos else ""
        pasta = QFileDialog.getExistingDirectory(self, "Escolher pasta para salvar", pasta_dir)
        if not pasta:
            return

        nome_base = self._sanitizar_nome(self.entry_nome.text())
        if not nome_base:
            QMessageBox.warning(self, "Erro", "Digite um nome base válido para SEO")
            return

        self._salvar_coords()

        coords_list = []
        for caminho in self.arquivos:
            if caminho in self._coords_por_imagem:
                coords_list.append(self._coords_por_imagem[caminho])
            else:
                coords_list.append((None, None, None))

        remover = self.rb_rem.isChecked()
        max_bytes = MAX_BYTES_REMFUNDO if remover else MAX_BYTES_NORMAL

        import time as _time_mod
        self._process_start = _time_mod.time()
        log.info("Iniciando — modo=%s, pasta=%s, %d imagem(ns)",
                 "remover_fundo" if remover else "redimensionar", pasta, len(self.arquivos))
        self._bloqueia_ui(True)
        self.progresso_barra.setValue(0)
        self.lbl_status.setText("Processando…")

        logo_path = self._logo_path if self.chk_marca.isChecked() else None
        self.worker = WorkerBatch(
            self.arquivos, pasta, nome_base, remover, max_bytes, coords_list,
            escala_porc=self.escala_slider.value(),
            logo_path=logo_path,
        )
        self.worker.progresso.connect(self._atualizar_progresso)
        self.worker.cancelado.connect(self._processo_cancelado)
        if remover:
            self.lbl_status.setText("Removendo fundo (primeira vez pode levar alguns segundos)…")
        self.worker.finalizado.connect(self._finalizar)
        self.worker.start()

    def _cancelar_processamento(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.lbl_status.setText("Cancelando…")
            self.btn_cancelar.setEnabled(False)

    def _processo_cancelado(self):
        self._bloqueia_ui(False)
        self.progresso_barra.setValue(0)
        self.lbl_status.setText("")
        self.btn_processar.setEnabled(True)
        QMessageBox.information(self, "Cancelado", "Processamento cancelado pelo usuário.")

    def _load_config(self, key, default=None):
        try:
            if os.path.isfile(self._config_path):
                with open(self._config_path, "r") as f:
                    cfg = __import__("json").load(f)
                return cfg.get(key, default)
        except Exception:
            pass
        return default

    def _save_config(self, key, value):
        try:
            os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
            cfg = {}
            if os.path.isfile(self._config_path):
                with open(self._config_path, "r") as f:
                    cfg = __import__("json").load(f)
            cfg[key] = value
            with open(self._config_path, "w") as f:
                __import__("json").dump(cfg, f)
        except Exception:
            pass

    def _toggle_tema(self):
        self._dark_mode = not self._dark_mode
        self._save_config("dark_mode", self._dark_mode)
        from redimensionar.theme import aplicar_tema
        aplicar_tema(QApplication.instance(), dark=self._dark_mode)

    def _sanitizar_nome(self, nome):
        nome = nome.strip().lower().replace(" ", "-")
        nome = "".join(c for c in nome if c.isalnum() or c == "-")
        while "--" in nome:
            nome = nome.replace("--", "-")
        return nome.strip("-")

    def _bloqueia_ui(self, bloqueado):
        self.btn_selecionar.setEnabled(not bloqueado)
        self.btn_processar.setEnabled(not bloqueado)
        self.btn_prev.setEnabled(not bloqueado)
        self.btn_prox.setEnabled(not bloqueado)
        self.btn_zoom_in.setEnabled(not bloqueado)
        self.btn_zoom_out.setEnabled(not bloqueado)
        self.entry_path.setEnabled(not bloqueado)
        self.rb_redim.setEnabled(not bloqueado)
        self.rb_rem.setEnabled(not bloqueado)
        self.escala_slider.setEnabled(not bloqueado)
        self.chk_marca.setEnabled(not bloqueado)
        self.btn_logo.setEnabled(not bloqueado and self.chk_marca.isChecked())
        self.progresso_barra.setVisible(bloqueado)
        self.btn_cancelar.setVisible(bloqueado)

    def _atualizar_progresso(self, nome, atual, total):
        if self._taskbar_progress is not None and total:
            try:
                self._taskbar_progress.setValue(int(atual * 100 / total))
                self._taskbar_progress.show()
            except Exception:
                pass

        pct = int(atual * 100 / total) if total else 0
        self.progresso_barra.setValue(pct)

        if nome:
            self.lbl_status.setText(f"Processando: {nome} ({pct}%)")
        elif self._process_start and atual > 0:
            import time
            decorrido = time.time() - self._process_start
            por_img = decorrido / atual
            restante = por_img * (total - atual)
            eta = f"{int(restante // 60)}m{int(restante % 60):02d}s"
            self.lbl_status.setText(f"{pct}%  |  {atual}/{total}  |  ETA {eta}")
        else:
            self.lbl_status.setText(f"{pct}%")

    def _finalizar(self, ok, erros, pasta):
        self._bloqueia_ui(False)
        self.progresso_barra.setValue(100 if ok else 0)
        self.lbl_status.setText("")
        if ok:
            self.btn_processar.setEnabled(True)

        if self._taskbar_progress is not None:
            try:
                self._taskbar_progress.setValue(100 if ok else 0)
                QTimer.singleShot(1500, self._taskbar_progress.hide)
            except Exception:
                pass

        if self._tray is not None:
            try:
                titulo = "Processamento Concluído"
                corpo = f"{ok} de {len(self.arquivos)} imagem(ns) salva(s) em:\n{pasta}"
                self._tray.showMessage(titulo, corpo, QSystemTrayIcon.Information, 5000)
            except Exception:
                pass

        msg = f"{ok} imagem(ns) salva(s) em:\n{pasta}"
        if erros:
            msg += f"\n\nErros:\n" + "\n".join(erros)
        QMessageBox.information(self, "Concluído", msg)


def _excepthook(tp, val, tb):
    log.critical("Exceção não capturada", exc_info=(tp, val, tb))
    sys.__excepthook__(tp, val, tb)


def main():
    log.info("LS Imagecomm v%s — iniciando", VERSION)
    sys.excepthook = _excepthook

    cfg_path = os.path.join(os.path.expanduser("~"), ".ls-imagecomm", "config.json")
    dark = False
    try:
        if os.path.isfile(cfg_path):
            with open(cfg_path, "r") as f:
                dark = __import__("json").load(f).get("dark_mode", False)
    except Exception:
        pass

    log.debug("main: criando QApplication")
    app = QApplication(sys.argv)
    aplicar_tema(app, dark=dark)
    log.debug("main: tema aplicado")
    ico_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    if not os.path.isfile(ico_path):
        try:
            import sys as _sys
            alt = os.path.join(getattr(_sys, '_MEIPASS', ''), 'redimensionar', 'app_icon.png')
            if os.path.isfile(alt):
                ico_path = alt
        except Exception:
            pass
    try:
        icon = QIcon(ico_path)
        if not icon.isNull():
            app.setWindowIcon(icon)
            log.debug("Icone carregado de: %s", ico_path)
        else:
            log.debug("Icone nulo: %s", ico_path)
    except Exception:
        log.exception("Falha ao carregar icone: %s", ico_path)
    log.debug("main: criando App()")
    janela = App()
    log.debug("main: App() ok, show()")
    janela.show()
    center = QApplication.primaryScreen().availableGeometry().center()
    janela.move(center.x() - janela.width() // 2, center.y() - janela.height() // 2)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
