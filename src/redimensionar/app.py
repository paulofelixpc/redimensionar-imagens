import os
import tempfile
import traceback
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QRadioButton, QGroupBox,
    QFileDialog, QMessageBox, QStatusBar, QSlider, QCheckBox,
    QMenuBar, QMenu, QSystemTrayIcon,
)
from PySide6.QtGui import QPixmap, QImage, QIcon, QShortcut, QKeySequence, QAction
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

log = get_logger("app")


class WorkerBatch(QThread):
    progresso = Signal(str, int, int)
    finalizado = Signal(int, list, str)

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

    def run(self):
        erros = []
        ok = 0
        total = len(self.arquivos)
        log.info("Processamento iniciado — %d imagem(ns)", total)

        for i, caminho in enumerate(self.arquivos):
            try:
                self.progresso.emit(os.path.basename(caminho), i, total)
                img = Image.open(caminho)
                img = corrigir_orientacao(img).convert("RGB")
                left, top, lado = self.coords_list[i]
                img = recortar_e_redimensionar(img, left, top, lado)

                if self.remover:
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

        log.info("Processamento finalizado — %d ok, %d erros", ok, len(erros))
        self.finalizado.emit(ok, erros, self.pasta)


VERSION = "1.1.0"


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Redimensionar Imagens — {TAMANHO}x{TAMANHO}")
        self.setMinimumSize(720, 640)

        self.arquivos = []
        self.previa_index = 0
        self._coords_por_imagem = {}
        self._logo_path = None
        self._process_start = None
        self._tray = None
        self._taskbar_button = None
        self._taskbar_progress = None

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        modo_group = QGroupBox("Modo")
        layout_modo = QVBoxLayout(modo_group)
        self.rb_redim = QRadioButton("Apenas redimensionar (máx 2MB)")
        self.rb_rem = QRadioButton("Remover fundo + redimensionar (máx 350KB)")
        self.rb_redim.setChecked(True)
        layout_modo.addWidget(self.rb_redim)
        layout_modo.addWidget(self.rb_rem)
        layout.addWidget(modo_group)

        row_arquivo = QHBoxLayout()
        self.btn_selecionar = QPushButton("Selecionar Imagens")
        self.btn_selecionar.clicked.connect(self.selecionar)
        row_arquivo.addWidget(self.btn_selecionar)
        self.lbl_qtd = QLabel("Nenhuma imagem selecionada")
        self.lbl_qtd.setStyleSheet("color: #666;")
        row_arquivo.addWidget(self.lbl_qtd)
        row_arquivo.addStretch()
        layout.addLayout(row_arquivo)

        row_nome = QHBoxLayout()
        row_nome.addWidget(QLabel("Nome base (SEO):"))
        self.entry_nome = QLineEdit()
        self.entry_nome.setText("minha-imagem")
        row_nome.addWidget(self.entry_nome)
        row_nome.addWidget(QLabel("-1, -2, -3..."))
        layout.addLayout(row_nome)

        self.crop_widget = CropWidget()
        layout.addWidget(self.crop_widget, stretch=1)

        row_zoom = QHBoxLayout()
        row_zoom.addStretch()
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setFixedWidth(32)
        self.btn_zoom_out.clicked.connect(self.crop_widget.zoom_out)
        row_zoom.addWidget(self.btn_zoom_out)
        btn_zoom_fit = QPushButton("Ajustar")
        btn_zoom_fit.clicked.connect(self.crop_widget.zoom_fit)
        row_zoom.addWidget(btn_zoom_fit)
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedWidth(32)
        self.btn_zoom_in.clicked.connect(self.crop_widget.zoom_in)
        row_zoom.addWidget(self.btn_zoom_in)
        row_zoom.addStretch()
        layout.addLayout(row_zoom)

        row_escala = QHBoxLayout()
        row_escala.addWidget(QLabel("Escala do produto na saída:"))
        self.escala_slider = QSlider(Qt.Horizontal)
        self.escala_slider.setRange(10, 100)
        self.escala_slider.setValue(100)
        self.escala_slider.setFixedWidth(200)
        row_escala.addWidget(self.escala_slider)
        self.lbl_escala = QLabel("100%")
        self.lbl_escala.setFixedWidth(40)
        row_escala.addWidget(self.lbl_escala)
        self.escala_slider.valueChanged.connect(
            lambda v: self.lbl_escala.setText(f"{v}%")
        )
        row_escala.addStretch()
        layout.addLayout(row_escala)

        row_marca = QHBoxLayout()
        self.chk_marca = QCheckBox("Adicionar marca d'água")
        row_marca.addWidget(self.chk_marca)
        self.btn_logo = QPushButton("Selecionar Logo")
        self.btn_logo.clicked.connect(self.selecionar_logo)
        self.btn_logo.setEnabled(False)
        row_marca.addWidget(self.btn_logo)
        self.lbl_logo = QLabel("Nenhum logo selecionado")
        self.lbl_logo.setStyleSheet("color: #999;")
        row_marca.addWidget(self.lbl_logo, stretch=1)
        self.chk_marca.toggled.connect(self.btn_logo.setEnabled)
        layout.addLayout(row_marca)

        row_nav = QHBoxLayout()
        row_nav.addStretch()
        self.btn_prev = QPushButton("◀")
        self.btn_prev.clicked.connect(self.anterior)
        row_nav.addWidget(self.btn_prev)
        self.lbl_contador = QLabel("")
        self.lbl_contador.setMinimumWidth(140)
        self.lbl_contador.setAlignment(Qt.AlignCenter)
        row_nav.addWidget(self.lbl_contador)
        self.btn_prox = QPushButton("▶")
        self.btn_prox.clicked.connect(self.proximo)
        row_nav.addWidget(self.btn_prox)
        row_nav.addStretch()
        layout.addLayout(row_nav)

        self.btn_processar = QPushButton("Processar e Salvar")
        self.btn_processar.setEnabled(False)
        self.btn_processar.clicked.connect(self.iniciar_processamento)
        self.btn_processar.setStyleSheet(
            "QPushButton { background: #4CAF50; color: white; font-weight: bold; "
            "padding: 8px 24px; border-radius: 4px; font-size: 13px; }"
            "QPushButton:disabled { background: #ccc; color: #888; }"
        )
        layout.addWidget(self.btn_processar, alignment=Qt.AlignCenter)

        QShortcut(QKeySequence("Ctrl+O"), self, self.selecionar)
        QShortcut(QKeySequence("Ctrl+S"), self, self.iniciar_processamento)
        QShortcut(QKeySequence("Ctrl++"), self, self.crop_widget.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.crop_widget.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.crop_widget.zoom_fit)
        QShortcut(QKeySequence(Qt.Key_Left), self, self.anterior)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.proximo)

        self.setTabOrder(self.entry_nome, self.btn_selecionar)
        self.setTabOrder(self.btn_selecionar, self.rb_redim)
        self.setTabOrder(self.rb_redim, self.rb_rem)
        self.setTabOrder(self.rb_rem, self.chk_marca)
        self.setTabOrder(self.chk_marca, self.btn_logo)
        self.setTabOrder(self.btn_logo, self.escala_slider)
        self.setTabOrder(self.escala_slider, self.btn_processar)

        self._criar_menu()
        self._criar_tray()

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")

        QTimer.singleShot(0, self._init_taskbar)

    def _criar_menu(self):
        bar = self.menuBar()

        arq = bar.addMenu("Arquivo")
        arq.addAction("Abrir Imagens", self.selecionar, QKeySequence("Ctrl+O"))
        arq.addAction("Processar e Salvar", self.iniciar_processamento, QKeySequence("Ctrl+S"))
        arq.addSeparator()
        arq.addAction("Sair", self.close, QKeySequence("Alt+F4"))

        view = bar.addMenu("Exibir")
        view.addAction("Zoom +", self.crop_widget.zoom_in, QKeySequence("Ctrl++"))
        view.addAction("Zoom -", self.crop_widget.zoom_out, QKeySequence("Ctrl+-"))
        view.addAction("Ajustar", self.crop_widget.zoom_fit, QKeySequence("Ctrl+0"))

        ajuda = bar.addMenu("Ajuda")
        ajuda.addAction("Sobre", self._mostrar_sobre)

    def _mostrar_sobre(self):
        QMessageBox.about(self, "Sobre o LS Imagecomm",
            "<b>LS Imagecomm</b><br><br>"
            "Redimensiona imagens para 1200×1200,<br>"
            "remove fundo com IA e adiciona marca d'água.<br><br>"
            f"Versão: {VERSION}<br>"
            "Totalmente offline.")

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
        self.lbl_qtd.setText(f"{len(self.arquivos)} imagem(ns) selecionada(s)")
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
            img = Image.open(caminho)
            img = corrigir_orientacao(img)
            self.crop_widget.set_image(img)

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

        pasta = QFileDialog.getExistingDirectory(self, "Escolher pasta para salvar")
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
        self.status_bar.showMessage("Processando...")

        logo_path = self._logo_path if self.chk_marca.isChecked() else None
        self.worker = WorkerBatch(
            self.arquivos, pasta, nome_base, remover, max_bytes, coords_list,
            escala_porc=self.escala_slider.value(),
            logo_path=logo_path,
        )
        self.worker.progresso.connect(self._atualizar_progresso)
        if remover:
            self.status_bar.showMessage("Removendo fundo (pode levar alguns segundos na primeira vez)...")
        self.worker.finalizado.connect(self._finalizar)
        self.worker.start()

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
        self.entry_nome.setEnabled(not bloqueado)
        self.rb_redim.setEnabled(not bloqueado)
        self.rb_rem.setEnabled(not bloqueado)
        self.escala_slider.setEnabled(not bloqueado)
        self.chk_marca.setEnabled(not bloqueado)
        self.btn_logo.setEnabled(not bloqueado and self.chk_marca.isChecked())

    def _atualizar_progresso(self, nome, atual, total):
        if self._taskbar_progress and total:
            self._taskbar_progress.setValue(int(atual * 100 / total))
            self._taskbar_progress.show()

        if nome:
            self.status_bar.showMessage(f"Processando: {nome}")
        elif self._process_start and atual > 0:
            import time
            decorrido = time.time() - self._process_start
            por_img = decorrido / atual
            restante = por_img * (total - atual)
            eta = f"{int(restante // 60)}m{int(restante % 60):02d}s"
            self.status_bar.showMessage(f"Processando... {atual}/{total} — ETA {eta}")
        else:
            self.status_bar.showMessage(f"Processando... {atual}/{total}")

    def _finalizar(self, ok, erros, pasta):
        self._bloqueia_ui(False)
        if ok:
            self.btn_processar.setEnabled(True)

        if self._taskbar_progress:
            self._taskbar_progress.setValue(100 if ok else 0)
            QTimer.singleShot(1500, self._taskbar_progress.hide)

        texto = f"{ok} imagem(ns) salva(s)"
        if erros:
            texto += f" com {len(erros)} erro(s)"
        self.status_bar.showMessage(texto)

        if self._tray and self._tray.supportsMessages():
            titulo = "Processamento Concluído"
            corpo = f"{ok} de {len(self.arquivos)} imagem(ns) salva(s) em:\n{pasta}"
            self._tray.showMessage(titulo, corpo, QSystemTrayIcon.Information, 5000)
            QTimer.singleShot(500, self._tray.show)

        msg = f"{ok} imagem(ns) salva(s) em:\n{pasta}"
        if erros:
            msg += f"\n\nErros:\n" + "\n".join(erros)
        QMessageBox.information(self, "Concluído", msg)


def _excepthook(tp, val, tb):
    log.critical("Exceção não capturada", exc_info=(tp, val, tb))
    import sys
    sys.__excepthook__(tp, val, tb)


def main():
    import sys
    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    try:
        icon = QIcon(os.path.join(os.path.dirname(__file__), "app_icon.png"))
        if not icon.isNull():
            app.setWindowIcon(icon)
    except Exception:
        pass
    janela = App()
    janela.show()
    sys.exit(app.exec())
