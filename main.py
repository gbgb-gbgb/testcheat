import sys
import os
import threading
from typing import Optional

import keyboard
import pyautogui
import pytesseract
from PIL import ImageGrab
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QHBoxLayout,
    QLineEdit,
    QMessageBox
)

# Ajusta isto se o Tesseract estiver num local diferente:
# Exemplo no Windows:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class ScreenAnalysisWorker(QThread):
    """Worker thread para não bloquear a UI durante a análise do ecrã"""
    analysis_complete = pyqtSignal(str)

    def run(self):
        try:
            screenshot = pyautogui.screenshot()
            text = pytesseract.image_to_string(screenshot, config="--psm 6")
            cleaned = self.clean_text(text)
            self.analysis_complete.emit(cleaned if cleaned else "Nenhum texto detectado.")
        except Exception as e:
            self.analysis_complete.emit(f"Erro ao analisar o ecrã: {e}")

    @staticmethod
    def clean_text(text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        cleaned = [line for line in lines if line]
        return "\n".join(cleaned[:100]) if cleaned else ""


class ScreenAnalyzerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_hotkey = "ctrl+alt+z"
        self.window_visible = True
        self.analysis_worker = None

        self.setWindowTitle("🧠 TestCheat")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(480, 300)

        # Estilo do app
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f7f7f7;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Título
        title = QLabel("🧠 TestCheat")
        title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #1d1d1d;
            }
        """)
        layout.addWidget(title)

        # Label da hotkey atual
        self.hotkey_label = QLabel(f"Hotkey atual: {self.current_hotkey}")
        self.hotkey_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.hotkey_label)

        # Linha de hotkey
        hotkey_row = QHBoxLayout()
        hotkey_row.setSpacing(8)

        hotkey_input = QLineEdit(self.current_hotkey)
        hotkey_input.setPlaceholderText("Ex.: ctrl+alt+s, ctrl+shift+a, f12")
        hotkey_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: #ffffff;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid #0f8cff;
            }
        """)
        self.hotkey_input = hotkey_input

        set_hotkey_btn = QPushButton("Definir")
        set_hotkey_btn.clicked.connect(self.set_custom_hotkey)
        set_hotkey_btn.setMaximumWidth(80)
        set_hotkey_btn.setStyleSheet("""
            QPushButton {
                background: #2b2b2b;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #444;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
        """)

        hotkey_row.addWidget(QLabel("Hotkey:"))
        hotkey_row.addWidget(hotkey_input)
        hotkey_row.addWidget(set_hotkey_btn)
        layout.addLayout(hotkey_row)

        # Botão Analisar
        analyze_btn = QPushButton("🧠 Analisar")
        analyze_btn.clicked.connect(self.analyze_screen)
        analyze_btn.setMinimumHeight(44)
        analyze_btn.setStyleSheet("""
            QPushButton {
                background: #0f8cff;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #0a6fe6;
            }
            QPushButton:pressed {
                background: #0857cc;
            }
        """)
        layout.addWidget(analyze_btn)

        # Caixa de resultados
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Resultado da análise aparece aqui...")
        self.result_box.setStyleSheet("""
            QTextEdit {
                background: #ffffff;
                border: 1px solid #d9d9d9;
                border-radius: 6px;
                padding: 10px;
                color: #222;
                font-size: 12px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(self.result_box)

        self.central_widget.setLayout(layout)

        # Instalar hotkey global
        self.install_global_hotkey()
        self.show()

    def install_global_hotkey(self):
        """Instala a hotkey global"""
        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except Exception:
            pass

        try:
            keyboard.add_hotkey(self.current_hotkey, self.toggle_window_visibility)
        except Exception as e:
            self.result_box.setPlainText(f"Erro ao registrar hotkey: {e}")

    def set_custom_hotkey(self):
        """Define uma nova hotkey"""
        new_key = self.hotkey_input.text().strip()

        if not new_key:
            QMessageBox.warning(self, "Hotkey inválida", "Escreve uma hotkey válida.\nExemplos: ctrl+alt+z, ctrl+shift+a, f12")
            return

        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except Exception:
            pass

        self.current_hotkey = new_key
        self.hotkey_label.setText(f"Hotkey atual: {self.current_hotkey}")

        try:
            keyboard.add_hotkey(self.current_hotkey, self.toggle_window_visibility)
            self.result_box.setPlainText(f"✓ Hotkey definida: {self.current_hotkey}\n\nPressiona {self.current_hotkey} para mostrar/esconder a janela.")
        except Exception as e:
            self.result_box.setPlainText(f"✗ Hotkey inválida: {e}\n\nTenta uma outra. Exemplos: ctrl+alt+z, f12, ctrl+shift+a")

    def toggle_window_visibility(self):
        """Mostra/esconde a janela com a hotkey"""
        if self.window_visible:
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
        self.window_visible = not self.window_visible

    def analyze_screen(self):
        """Captura e analisa o ecrã"""
        self.result_box.setPlainText("🔍 A analisar o ecrã...")
        QApplication.processEvents()

        # Usar thread worker para não bloquear UI
        if self.analysis_worker is not None and self.analysis_worker.isRunning():
            self.result_box.setPlainText("⏳ Análise em progresso... Aguarda.")
            return

        self.analysis_worker = ScreenAnalysisWorker()
        self.analysis_worker.analysis_complete.connect(self.on_analysis_complete)
        self.analysis_worker.start()

    def on_analysis_complete(self, result: str):
        """Callback quando a análise termina"""
        self.result_box.setPlainText(result)

    def closeEvent(self, event):
        """Remove hotkey ao fechar"""
        try:
            keyboard.remove_hotkey(self.current_hotkey)
        except Exception:
            pass
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ScreenAnalyzerWindow()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
