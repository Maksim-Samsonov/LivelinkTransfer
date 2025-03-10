import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QFrame
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal

from models.device_manager import USBDevice, WiFiDevice

logger = logging.getLogger(__name__)

class DevicePanel(QWidget):
    """Панель со списком доступных устройств"""
    
    device_selected = pyqtSignal(object)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        
        # Настройка стиля панели
        self.setMinimumWidth(250)
        self.setMaximumWidth(350)
        
        # Создаем стиль границы
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
        """)
        
        # Основной макет
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Создаем фрейм-контейнер
        self.frame = QFrame()
        
        # Макет для фрейма
        self.frame_layout = QVBoxLayout(self.frame)
        
        # Заголовок панели
        self.header = QLabel("Devices")
        self.header.setObjectName("header")
        self.frame_layout.addWidget(self.header)
        
        # Список устройств
        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(200)
        self.device_list.itemClicked.connect(self.on_device_selected)
        self.frame_layout.addWidget(self.device_list)
        
        # Панель с кнопками
        self.button_layout = QHBoxLayout()
        
        # Кнопка обновления списка устройств
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(QIcon("src/resources/icons/refresh.png"))
        self.refresh_button.clicked.connect(self.controller.start_device_discovery)
        self.button_layout.addWidget(self.refresh_button)
        
        # Добавляем панель с кнопками в основной макет
        self.frame_layout.addLayout(self.button_layout)
        
        # Добавляем фрейм в основной макет
        self.main_layout.addWidget(self.frame)
        
        # Растягиваем основной макет вниз
        self.main_layout.addStretch(1)
        
    def update_devices(self, devices):
        """Обновляет список устройств"""
        logger.info(f"Updating device list with {len(devices)} devices")
        
        # Запоминаем текущий выбранный элемент
        current_item = self.device_list.currentItem()
        current_device_id = None
        if current_item:
            device = current_item.data(Qt.ItemDataRole.UserRole)
            current_device_id = device.id
        
        # Очищаем список устройств
        self.device_list.clear()
        
        # Добавляем устройства в список
        for device in devices:
            item = QListWidgetItem()
            item.setText(device.name)
            item.setData(Qt.ItemDataRole.UserRole, device)
            
            # Разные иконки для USB и Wi-Fi устройств
            if isinstance(device, USBDevice):
                item.setIcon(QIcon("src/resources/icons/usb.png"))
            else:
                item.setIcon(QIcon("src/resources/icons/wifi.png"))
                
            # Добавляем дополнительную информацию
            if isinstance(device, USBDevice):
                item.setToolTip(f"Model: {device.model}\niOS: {device.ios_version}")
            else:
                item.setToolTip(f"IP: {device.ip_address}\nPort: {device.port}")
            
            self.device_list.addItem(item)
            
            # Если это ранее выбранное устройство, выбираем его снова
            if device.id == current_device_id:
                self.device_list.setCurrentItem(item)
                
    def on_device_selected(self, item):
        """Обработчик выбора устройства в списке"""
        device = item.data(Qt.ItemDataRole.UserRole)
        logger.info(f"Device selected: {device.name} ({device.id})")
        self.device_selected.emit(device)
        
    def get_selected_device(self):
        """Возвращает выбранное устройство"""
        item = self.device_list.currentItem()
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None
