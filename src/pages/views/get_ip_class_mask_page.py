from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.logic import ClassMask, getIPClass, getIPClassMask, getIpError
from ...services.database import Database


class GetIpClassMaskPage(QWidget):
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

        run_button = QPushButton("Obtenir le masque")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(168, 46)
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

        empty_text = QLabel("Entrez une IP pour récupérer son masque par défaut")
        empty_text.setObjectName("emptyStateText")
        empty_layout.addWidget(empty_text)

        # --- Carte resultat ---
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setVisible(False)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(8)

        self.status_badge = QLabel("MASQUE")
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

        # --- Encadré d'aide F4 ---
        self.help_card = QFrame()
        self.help_card.setObjectName("resultCard")
        help_layout = QVBoxLayout(self.help_card)
        help_layout.setContentsMargins(16, 14, 16, 14)
        help_layout.setSpacing(6)
        help_title = QLabel(" Astuce : Masque Classful par défaut")
        help_title.setObjectName("resultIp")
        help_text = QLabel(
            "Le masque par défaut (ou masque classful) dépend directement de la classe de l'adresse IP :\n"
            "• Classe A : 255.0.0.0 (/8)\n"
            "• Classe B : 255.255.0.0 (/16)\n"
            "• Classe C : 255.255.255.0 (/24)"
        )
        help_text.setObjectName("emptyStateText")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        card_layout.addWidget(self.help_card)
        card_layout.addStretch(1)

        card_layout.addStretch(1)

        layout.addWidget(card)


    def run_check(self):
        # --- Execution du calcul de masque ---
        ip = self.ip_input.text().strip()
        ip_class = getIPClass(ip)
        mask = getIPClassMask(ip)

        self.empty_state.setVisible(False)
        self.result_card.setVisible(True)

        if ip_class == ClassMask.CLASS_D:
            self.result.setText("Classe D — pas de masque classful")
            self.result.setStyleSheet("color: #f59e0b;")
            self.status_badge.setText("CLASSE D")
            self.status_badge.setObjectName("badgeWarn")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        if ip_class == ClassMask.CLASS_E:
            self.result.setText("Classe E — pas de masque classful")
            self.result.setStyleSheet("color: #f59e0b;")
            self.status_badge.setText("CLASSE E")
            self.status_badge.setObjectName("badgeWarn")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        if mask == ClassMask.ERROR.value:
            self.result.setText(getIpError(ip) or "Adresse IP invalide")  #Va rechercher le message d'erreur correspondant à l'erreur
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("INVALIDE")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        Database().save_f4_class_mask(ip)   #Stockage dans la DB

        class_name = ip_class.name.replace("CLASS_", "Classe ")
        self.result.setText(f"{class_name}\nMasque de classe: {mask}")
        self.result.setStyleSheet("color: #22c55e;")
        self.status_badge.setText(ip_class.name.replace("CLASS_", "CLASSE "))
        self.status_badge.setObjectName("badgeValid")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    #fonction vider les champs
    def clear_fields(self):
        self.ip_input.clear()
        self.result_card.setVisible(False)
        self.empty_state.setVisible(True)
