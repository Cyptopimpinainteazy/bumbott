from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QProgressBar, QLabel, QComboBox, QFileDialog
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QColor

class TrainingTabWidget(QWidget):
    """
    Widget for managing neural network training processes
    """
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Model selection
        self.model_selection_layout = QHBoxLayout()
        self.model_selector = QComboBox()
        self.model_selector.addItems(["LSTM Predictor", "Transformer Model", "Hybrid Architecture"])
        self.load_model_btn = QPushButton("Load Model")
        self.model_selection_layout.addWidget(QLabel("Active Model:"))
        self.model_selection_layout.addWidget(self.model_selector, 2)
        self.model_selection_layout.addWidget(self.load_model_btn)
        
        # Training controls
        self.controls_layout = QHBoxLayout()
        self.start_train_btn = QPushButton("Start Training")
        self.start_train_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.stop_train_btn = QPushButton("Stop Training")
        self.stop_train_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.controls_layout.addWidget(self.start_train_btn)
        self.controls_layout.addWidget(self.stop_train_btn)
        
        # Progress visualization
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Status indicators
        self.status_layout = QHBoxLayout()
        self.epoch_label = QLabel("Epoch: 0")
        self.loss_label = QLabel("Loss: --")
        self.accuracy_label = QLabel("Accuracy: --")
        self.status_layout.addWidget(self.epoch_label)
        self.status_layout.addWidget(self.loss_label)
        self.status_layout.addWidget(self.accuracy_label)
        
        # Add components to layout
        self.layout.addLayout(self.model_selection_layout)
        self.layout.addLayout(self.controls_layout)
        self.layout.addWidget(self.progress_bar)
        self.layout.addLayout(self.status_layout)
        
        # Connect signals
        self.start_train_btn.clicked.connect(self.on_start_training)
        self.stop_train_btn.clicked.connect(self.on_stop_training)
        self.load_model_btn.clicked.connect(self.on_load_model)
        
        # Training simulation
        self.training_active = False
        self.training_timer = QTimer()
        self.training_timer.timeout.connect(self.update_training)
        
    @pyqtSlot()
    def on_start_training(self):
        """Handle training start"""
        if not self.training_active:
            self.training_active = True
            self.start_train_btn.setEnabled(False)
            self.stop_train_btn.setEnabled(True)
            self.training_timer.start(100)  # Update every 100ms
            
    @pyqtSlot()
    def on_stop_training(self):
        """Handle training stop"""
        self.training_active = False
        self.start_train_btn.setEnabled(True)
        self.stop_train_btn.setEnabled(False)
        self.training_timer.stop()
        
    @pyqtSlot()
    def on_load_model(self):
        """Handle model loading"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Model", "", "Keras Models (*.keras)"
        )
        if filename:
            self.model_selector.addItem(filename.split("/")[-1])
            self.model_selector.setCurrentIndex(self.model_selector.count()-1)
            
    def update_training(self):
        """Simulate training progress"""
        if self.training_active:
            current = self.progress_bar.value()
            if current < 100:
                self.progress_bar.setValue(current + 1)
                self.epoch_label.setText(f"Epoch: {current}")
                self.loss_label.setText(f"Loss: {0.99 ** current:.4f}")
                self.accuracy_label.setText(f"Accuracy: {current * 0.8:.1f}%")
            else:
                self.on_stop_training()
