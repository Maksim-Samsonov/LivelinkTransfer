import logging
from typing import List, Optional
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QPushButton, QMenu,
    QLabel, QFileDialog, QProgressBar, QFrame
)
from PyQt6.QtGui import QIcon, QAction, QDrag, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QSize

from models.device_manager import File

logger = logging.getLogger(__name__)

class FileView(QWidget):
    """Виджет для отображения файлов с устройства"""
    
    files_selected = pyqtSignal(bool)  # Сигнал о выборе файлов (True если выбраны)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_device = None
        self.files = []
        self.filtered_files = []  # Файлы после фильтрации
        
        # Настройка стиля
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #555;
                border-radius: 4px;
            }
            QLabel#header {
                font-weight: bold;
                font-size: 16px;
                padding: 8px;
                color: #ddd;
            }
            QLineEdit {
                padding: 6px;
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.1);
            }
            QPushButton {
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)
        
        # Основной макет
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Создаем фрейм-контейнер
        self.frame = QFrame()
        
        # Макет для фрейма
        self.frame_layout = QVBoxLayout(self.frame)
        
        # Заголовок
        self.header = QLabel("Files")
        self.header.setObjectName("header")
        self.frame_layout.addWidget(self.header)
        
        # Панель инструментов для файлов
        self.tool_panel = QHBoxLayout()
        
        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files...")
        self.search_input.textChanged.connect(self.filter_files)
        self.tool_panel.addWidget(self.search_input)
        
        # Кнопка сортировки
        self.sort_button = QPushButton("Sort")
        self.sort_button.setIcon(QIcon("src/resources/icons/sort.png"))
        self.sort_menu = QMenu()
        
        sort_by_name = QAction("Sort by Name", self)
        sort_by_name.triggered.connect(lambda: self.sort_files("name"))
        self.sort_menu.addAction(sort_by_name)
        
        sort_by_date = QAction("Sort by Date", self)
        sort_by_date.triggered.connect(lambda: self.sort_files("date"))
        self.sort_menu.addAction(sort_by_date)
        
        sort_by_size = QAction("Sort by Size", self)
        sort_by_size.triggered.connect(lambda: self.sort_files("size"))
        self.sort_menu.addAction(sort_by_size)
        
        self.sort_button.setMenu(self.sort_menu)
        self.tool_panel.addWidget(self.sort_button)
        
        # Кнопка загрузки
        self.download_button = QPushButton("Download")
        self.download_button.setIcon(QIcon("src/resources/icons/download.png"))
        self.download_button.clicked.connect(self.download_selected)
        self.download_button.setEnabled(False)
        self.tool_panel.addWidget(self.download_button)
        
        # Добавляем панель инструментов в основной макет
        self.frame_layout.addLayout(self.tool_panel)
        
        # Таблица файлов
        self.file_table = QTableWidget()
        self.file_table.setColumnCount(4)
        self.file_table.setHorizontalHeaderLabels(["Name", "Size", "Date Modified", "Actions"])
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Включаем поддержку drag-and-drop
        self.file_table.setDragEnabled(True)
        self.file_table.setDefaultDropAction(Qt.DropAction.CopyAction)
        
        # Добавляем таблицу в основной макет
        self.frame_layout.addWidget(self.file_table)
        
        # Добавляем фрейм в основной макет
        self.main_layout.addWidget(self.frame)
        
    def set_device(self, device):
        """Устанавливает текущее устройство и обновляет список файлов"""
        self.current_device = device
        self.header.setText(f"Files from {device.name}")
        self.update_files([])
        
    def update_files(self, files):
        """Обновляет список файлов"""
        self.files = files
        self.filtered_files = files.copy()
        self.display_files()
        
    def display_files(self):
        """Отображает файлы в таблице"""
        self.file_table.setRowCount(len(self.filtered_files))
        
        for i, file in enumerate(self.filtered_files):
            # Имя файла
            name_item = QTableWidgetItem(file.name)
            self.file_table.setItem(i, 0, name_item)
            
            # Размер файла (форматированный)
            size_item = QTableWidgetItem(self.format_size(file.size))
            size_item.setData(Qt.ItemDataRole.UserRole, file.size)  # Сохраняем размер для сортировки
            self.file_table.setItem(i, 1, size_item)
            
            # Дата изменения
            date_str = file.date_modified.strftime("%Y-%m-%d %H:%M")
            date_item = QTableWidgetItem(date_str)
            date_item.setData(Qt.ItemDataRole.UserRole, file.date_modified.timestamp())  # Для сортировки
            self.file_table.setItem(i, 2, date_item)
            
            # Кнопка для загрузки файла
            download_widget = QWidget()
            download_layout = QHBoxLayout(download_widget)
            download_layout.setContentsMargins(4, 0, 4, 0)
            
            download_button = QPushButton()
            download_button.setIcon(QIcon("src/resources/icons/download.png"))
            download_button.setIconSize(QSize(16, 16))
            download_button.setFixedSize(QSize(24, 24))
            download_button.clicked.connect(lambda checked, f=file: self.download_file(f))
            
            download_layout.addWidget(download_button)
            download_layout.addStretch()
            
            self.file_table.setCellWidget(i, 3, download_widget)
            
        # Если нет файлов, показываем соответствующее сообщение
        if len(self.filtered_files) == 0:
            self.file_table.setRowCount(1)
            no_files_item = QTableWidgetItem("No files found")
            no_files_item.setFlags(Qt.ItemFlag.NoItemFlags)  # Делаем элемент неактивным
            self.file_table.setItem(0, 0, no_files_item)
            self.file_table.setSpan(0, 0, 1, 4)  # Объединяем ячейки
            
    def format_size(self, size_bytes):
        """Форматирование размера файла в человекочитаемый вид"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"
        
    def filter_files(self, text):
        """Фильтрация файлов по имени"""
        if not text:
            self.filtered_files = self.files.copy()
        else:
            text = text.lower()
            self.filtered_files = [file for file in self.files if text in file.name.lower()]
            
        self.display_files()
                
    def sort_files(self, criterion):
        """Сортировка файлов по выбранному критерию"""
        if criterion == "name":
            self.filtered_files.sort(key=lambda file: file.name.lower())
        elif criterion == "size":
            self.filtered_files.sort(key=lambda file: file.size)
        elif criterion == "date":
            self.filtered_files.sort(key=lambda file: file.date_modified, reverse=True)
            
        self.display_files()
            
    def on_selection_changed(self):
        """Обработчик изменения выделения в таблице"""
        selected_items = self.file_table.selectedItems()
        has_selection = len(selected_items) > 0
        
        # Включаем/выключаем кнопку загрузки
        self.download_button.setEnabled(has_selection)
        
        # Отправляем сигнал о выделении файлов
        self.files_selected.emit(has_selection)
        
    def download_selected(self):
        """Загрузка выбранных файлов"""
        files = self.get_selected_files()
        if not files:
            return
        
        # Выбираем директорию назначения
        default_path = self.controller.get_settings("default_download_path", "")
        destination = QFileDialog.getExistingDirectory(
            self, "Select Destination Folder", default_path, QFileDialog.Option.ShowDirsOnly
        )
        
        if destination:
            # Сохраняем путь назначения
            self.controller.set_settings("default_download_path", destination)
            
            # Передаем файлы
            self.controller.transfer_files(files, destination)
    
    def download_file(self, file):
        """Загрузка одного файла"""
        # Выбираем директорию назначения
        default_path = self.controller.get_settings("default_download_path", "")
        destination = QFileDialog.getExistingDirectory(
            self, "Select Destination Folder", default_path, QFileDialog.Option.ShowDirsOnly
        )
        
        if destination:
            # Сохраняем путь назначения
            self.controller.set_settings("default_download_path", destination)
            
            # Передаем файл
            self.controller.transfer_files([file], destination)
    
    def get_selected_files(self) -> List[File]:
        """Возвращает список выбранных файлов"""
        # Получаем уникальные номера выбранных строк
        selected_rows = set()
        for item in self.file_table.selectedItems():
            selected_rows.add(item.row())
        
        # Собираем файлы из выбранных строк
        selected_files = []
        for row in selected_rows:
            # Проверяем, что строка содержит файл, а не сообщение "No files found"
            if row < len(self.filtered_files):
                selected_files.append(self.filtered_files[row])
                
        return selected_files
    
    def clear_files(self):
        """Очищает список файлов"""
        self.files = []
        self.filtered_files = []
        self.header.setText("Files")
        self.display_files()
