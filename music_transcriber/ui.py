import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, \
    QProgressBar
from music_transcriber.music_transcriber import MusicTranscriber


class MusicTranscriberUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.progress_bar = None
        self.loading_label = None
        self.upload_button = None
        self.music_transcriber = MusicTranscriber()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Music Transcriber')

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        self.upload_button = QPushButton('Upload Music File', self)
        self.upload_button.clicked.connect(self.on_upload_button_click)

        self.loading_label = QLabel('')
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setVisible(False)

        layout.addWidget(self.upload_button)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress_bar)

    def on_upload_button_click(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, 'Open Music File', '',
                                                   'Audio Files (*.wav *.mp3 *.ogg);;All Files (*)', options=options)

        if file_name:
            if not self.music_transcriber.is_valid_music_file(file_name):
                self.display_error('Invalid music file.')
                return

            output_file_name = self.prompt_output_file_name()
            self.display_loading_screen()
            QApplication.processEvents()

            notes_and_durations, music_tempo = self.music_transcriber.process_music_file(file_name)  # Unpack the tuple

            if output_file_name:
                self.music_transcriber.generate_music_xml(notes_and_durations, music_tempo, output_file_name)

            self.display_loading_screen(False)

    def display_loading_screen(self, show=True):
        if show:
            self.upload_button.setEnabled(False)
            self.loading_label.setText('Processing...')
            self.progress_bar.setVisible(True)
        else:
            self.upload_button.setEnabled(True)
            self.loading_label.setText('')
            self.progress_bar.setVisible(False)

    def display_error(self, message):
        self.loading_label.setText(message)

    def prompt_output_file_name(self):
        output_file_name, _ = QFileDialog.getSaveFileName(
            self, "Save MusicXML File", "", "MusicXML Files (*.xml)")
        return output_file_name


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MusicTranscriberUI()
    main_window.show()
    sys.exit(app.exec_())
