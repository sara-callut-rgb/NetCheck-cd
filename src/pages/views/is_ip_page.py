from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.logic import isIp, getIpError



class IsIpPage(QWidget):
    def __init__(self):
        super().__init__()

        # --- Structure principale ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- Carte outil ---
        card = QFrame()
        card.setObjectName("toolCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(14)

        # --- Ligne de saisie ---
        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IPv4")
        self.ip_input.setObjectName("primaryInput")
        self.ip_input.setFixedHeight(48)
        self.ip_input.returnPressed.connect(self.run_check)

        run_button = QPushButton("Vérifier")
        run_button.setObjectName("actionButton")
        run_button.setFixedWidth(140)
        run_button.setFixedHeight(48)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_check)

        form_row.addWidget(self.ip_input, 1)
        form_row.addWidget(run_button)

        # --- Etat vide ---
        self.empty_state = QFrame()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QHBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)
        empty_layout.setSpacing(10)

        empty_text = QLabel("Entrez une IP pour voir les détails ici")
        empty_text.setObjectName("emptyStateText")

        empty_layout.addWidget(empty_text)
        empty_layout.addStretch(1)


        # --- Carte resultat ---
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setVisible(False)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(18, 14, 18, 14)
        result_layout.setSpacing(8)

        self.result_ip = QLabel("IP:")
        self.result_ip.setObjectName("resultIp")

        self.status_badge = QLabel("INVALIDE")
        self.status_badge.setObjectName("badgeNeutral")
        self.status_badge.setFixedWidth(94)
        self.status_badge.setAlignment(Qt.AlignCenter)

        self.result_message = QLabel("")
        self.result_message.setObjectName("statusMessage")

        result_layout.addWidget(self.result_ip)
        result_layout.addWidget(self.status_badge, 0, Qt.AlignLeft)
        result_layout.addWidget(self.result_message)

        card_layout.addLayout(form_row)
        card_layout.addWidget(self.empty_state)
        card_layout.addWidget(self.result_card)
        card_layout.addStretch(1)

        layout.addWidget(card)


    def run_check(self):
        # --- Execution de la verification ---
        ip = self.ip_input.text().strip()
        valid = isIp(ip)

        self.empty_state.setVisible(False)
        self.result_card.setVisible(True)
        self.result_ip.setText(f"IP: {ip if ip else '-'}")

        if valid:
            self.status_badge.setText("VALIDE")
            self.status_badge.setObjectName("badgeValid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            self.result_message.setText("Adresse IP valide")
            self.result_message.setStyleSheet("color: #22c55e;")

        else:
            self.status_badge.setText("INVALIDE")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            self.result_message.setText(getIpError(ip) or "Adresse IP invalide")
            self.result_message.setStyleSheet("color: #ef4444;")
