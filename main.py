import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QListWidget, QWidget, QComboBox
from pymongo import MongoClient
from bson.binary import Binary
import os
import subprocess
import tempfile

class FileDatabaseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.client = MongoClient('mongodb://localhost:27017')
        self.db = self.client['dbdoc']
        self.collections = self.db.list_collection_names()
        self.current_collection = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("File Database")
        self.setGeometry(100, 100, 800, 600)

        self.upload_button = QPushButton("Upload Folder", self)
        self.upload_button.setFixedSize(85, 25)
        self.upload_button.clicked.connect(self.upload_folder)

        self.view_all_button = QPushButton("View All Files", self)
        self.view_all_button.setFixedSize(85, 25)
        self.view_all_button.clicked.connect(self.view_all_files)

        self.collection_label = QLabel("Select Collection:")
        self.collection_combo = QComboBox()
        self.collection_combo.addItems(self.collections)
        self.collection_combo.currentIndexChanged.connect(self.collection_changed)

        self.search_label = QLabel("Search Files:")
        self.search_entry = QLineEdit()
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_files)

        self.results_label = QLabel("Search Results:")
        self.results = QListWidget()
        self.results.setSortingEnabled(True)

        self.status_label = QLabel()

        layout = QVBoxLayout()
        layout.addWidget(self.upload_button)
        layout.addWidget(self.view_all_button)
        layout.addWidget(self.collection_label)
        layout.addWidget(self.collection_combo)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_entry)
        layout.addWidget(self.search_button)
        layout.addWidget(self.results_label)
        layout.addWidget(self.results)
        layout.addWidget(self.status_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.results.itemDoubleClicked.connect(self.open_file)

    def collection_changed(self, index):
        collection_name = self.collection_combo.itemText(index)
        self.current_collection = self.db[collection_name]

    def upload_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path and self.current_collection is not None:
            for root, dirs, files in os.walk(folder_path):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    with open(file_path, 'rb') as file:
                        file_data = Binary(file.read())
                        # Используем только имя файла, без пути
                        self.current_collection.insert_one({'filename': file_name, 'data': file_data})
            self.status_label.setText('Folder uploaded successfully')
            self.view_all_files()
        else:
            self.status_label.setText('Please select a collection before uploading')

    def open_file(self, item):
        selected_text = item.text().strip()
        if selected_text and self.current_collection is not None:
            file_data = self.current_collection.find_one({'filename': selected_text})
            if file_data:
                file_extension = os.path.splitext(selected_text)[-1].lower()

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
                temp_file.write(file_data['data'])
                temp_file_path = temp_file.name
                temp_file.close()

                try:
                    subprocess.Popen(['start', '', temp_file_path], shell=True)
                except Exception as e:
                    self.status_label.setText(f'Error opening file: {e}')

            else:
                self.status_label.setText('File not found in the database')

    def search_files(self):
        query = self.search_entry.text()
        self.results.clear()
        if self.current_collection is not None:
            for file in self.current_collection.find({'filename': {'$regex': query, '$options': 'i'}}):
                self.results.addItem(file['filename'])
        else:
            self.status_label.setText('Please select a collection before searching')

    def view_all_files(self):
        if self.current_collection is not None:
            self.results.clear()
            for file in self.current_collection.find():
                self.results.addItem(file['filename'])
            self.status_label.setText('')
        else:
            self.status_label.setText('Please select a collection')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = FileDatabaseApp()
    main_app.show()
    sys.exit(app.exec())
