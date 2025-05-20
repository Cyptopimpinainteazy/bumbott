from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSlot, pyqtSignal, QObject
from web3 import Web3
from walletconnect.providers import WalletConnectProvider
import os
import qrcode

class MetaMaskSigner(QObject):
    connected = pyqtSignal(str)
    disconnected = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.web3 = Web3(Web3.WebsocketProvider('ws://localhost:8545'))
        self.account = None
        
    def connect(self):
        # TODO: Implement actual MetaMask connection
        self.account = '0x123...abc'
        self.connected.emit(self.account)
        
    def disconnect(self):
        self.account = None
        self.disconnected.emit()

class MetaMaskConnectWidget(QWidget):
    """
    Widget for connecting to MetaMask wallet
    """
    
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Not Connected")
        self.connect_btn = QPushButton("Connect MetaMask")
        self.connect_btn.setStyleSheet("background-color: #f6851b; color: white;")
        
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.connect_btn)
        
        self.signer = MetaMaskSigner()
        self.connect_btn.clicked.connect(self.signer.connect)
        self.signer.connected.connect(self.on_connected)
        self.signer.disconnected.connect(self.on_disconnected)
        
        self.wc = WalletConnectProvider({
            "projectId": "2f4346a4c911d6136a4c911d6c3f8b4a",
            "metadata": {
                "name": "BumBot",
                "description": "AI Trading Platform",
                "url": "https://bumbot.com",
                "icons": ["https://bumbot.com/icon.png"]
            }
        })
        
    @pyqtSlot(str)
    def on_connected(self, address):
        self.status_label.setText(f"Connected: {address[:10]}...")
        self.connect_btn.setText("Disconnect")
        self.connect_btn.clicked.disconnect()
        self.connect_btn.clicked.connect(self.signer.disconnect)
        
    @pyqtSlot()
    def on_disconnected(self):
        self.status_label.setText("Not Connected")
        self.connect_btn.setText("Connect MetaMask")
        self.connect_btn.clicked.disconnect()
        self.connect_btn.clicked.connect(self.signer.connect)

    def show_qr(self, uri):
        qr = qrcode.QRCode()
        qr.add_data(uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = os.path.join(os.path.dirname(__file__), "qrcode.svg")
        try:
            img.save(qr_path)
            self.qr_code.load(qr_path)
        except Exception as e:
            print(f"QR Error: {e}")

    def connect_walletconnect(self):
        conn_uri = self.wc.create_connection(chainId=137)  # Polygon Mainnet
        self.show_qr(conn_uri)
