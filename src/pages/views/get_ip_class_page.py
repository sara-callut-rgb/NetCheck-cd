from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.logic import ClassMask, getIPClass, getIpError, isPrivateIp, isReservedIp
from ...services.database import Database


class GetIpClassPage(QWidget):
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
        row = QHBoxLayout()
        row.setSpacing(10)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IPv4")
        self.ip_input.setObjectName("primaryInput")
        self.ip_input.setFixedHeight(46)
        self.ip_input.returnPressed.connect(self.run_check)

        run_button = QPushButton("Obtenir la classe")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(160, 46)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_check)

        #bouton vider les champs
        clear_button = QPushButton("Vider")
        clear_button.setObjectName("actionButton")
        clear_button.setFixedSize(90, 46)
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.clear_fields)

        row.addWidget(self.ip_input, 1)
        row.addWidget(run_button)
        row.addWidget(clear_button)

        # --- Etat vide ---
        self.empty_state = QFrame()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QHBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)

        empty_text = QLabel("Saisissez une IP pour identifier sa classe")
        empty_text.setObjectName("emptyStateText")
        empty_layout.addWidget(empty_text)

        # --- Carte resultat ---
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setVisible(False)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(8)

        self.status_badge = QLabel("CLASSE")
        self.status_badge.setObjectName("badgeNeutral")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedWidth(130)

        self.result = QLabel("")
        self.result.setObjectName("statusMessage")

        result_layout.addWidget(self.status_badge, 0, Qt.AlignLeft)
        result_layout.addWidget(self.result)

        card_layout.addLayout(row)
        card_layout.addWidget(self.empty_state)
        card_layout.addWidget(self.result_card)
        card_layout.addStretch(1)

        layout.addWidget(card)


    def run_check(self):
        # --- Execution du calcul de classe ---
        ip = self.ip_input.text().strip()
        ip_class = getIPClass(ip)

        self.empty_state.setVisible(False)
        self.result_card.setVisible(True)
        
        if ip_class == ClassMask.ERROR:
            self.result.setText(getIpError(ip) or "Adresse IP invalide")    #Correction du message d'erreur
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("INVALIDE")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        Database().save_f3_ip_class(ip)  #Stockage dans la DB

        class_name = ip_class.name.replace("CLASS_", "Classe ")
        details = [class_name]

        is_reserved = isReservedIp(ip)
        is_private = isPrivateIp(ip)

        if is_reserved:
            details.append("Adresse réservée")

        if is_private:
            details.append("Adresse privée")

        if not is_reserved and not is_private:
            details.append("Adresse publique")

        self.result.setText("\n".join(details))
        self.result.setStyleSheet("color: #22c55e;")
        self.status_badge.setText(class_name.upper())
        self.status_badge.setObjectName("badgeValid")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    #fonction vider les champs
    def clear_fields(self):
        self.ip_input.clear()
        self.result_card.setVisible(False)
        self.empty_state.setVisible(True)
