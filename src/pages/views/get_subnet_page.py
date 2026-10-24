from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.logic import ClassMask, getIPClass, getIPClassMask, getIpError, getMaskError, getNetworkAddress, getSubnet, isClassFull, isIp, isSubnetMask, parseMask



class GetSubnetPage(QWidget):
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

        self.mask_input = QLineEdit()
        self.mask_input.setPlaceholderText("Masque classful")
        self.mask_input.setObjectName("primaryInput")
        self.mask_input.setFixedHeight(46)
        self.mask_input.returnPressed.connect(self.run_check)

        run_button = QPushButton("Calculer")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(122, 46)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_check)

        row.addWidget(self.ip_input, 1)
        row.addWidget(self.mask_input, 1)
        row.addWidget(run_button)

        # --- Etat vide ---
        self.empty_state = QFrame()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QHBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)

        empty_text = QLabel("Ajoutez IP + masque pour calculer le sous-réseau")
        empty_text.setObjectName("emptyStateText")
        empty_layout.addWidget(empty_text)

        # --- Carte resultat ---
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setVisible(False)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(8)

        self.status_badge = QLabel("SOUS-RÉSEAU")
        self.status_badge.setObjectName("badgeNeutral")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedWidth(140)

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
        # --- Execution du calcul de sous-reseau ---
        ip = self.ip_input.text().strip()
        mask = self.mask_input.text().strip()
        normalized_mask = parseMask(mask)

        self.empty_state.setVisible(False)
        self.result_card.setVisible(True)

        if not isIp(ip):
            self.result.setText(getIpError(ip) or "Adresse IP invalide")   #Correction du message d'erreur
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        if not normalized_mask or not isSubnetMask(normalized_mask):
            self.result.setText(getMaskError(mask) or "Masque invalide")   #Correction du message d'erreur
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        #Correction de l'erreur de calcul
        if getIPClass(ip) in (ClassMask.CLASS_A, ClassMask.CLASS_B, ClassMask.CLASS_C) and getNetworkAddress(normalized_mask, getIPClassMask(ip)) != getIPClassMask(ip):
            self.result.setText("Le masque ne correspond pas à la classe de l'adresse IP")
            self.result.setStyleSheet("color: #f59e0b;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeWarn")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        ip_class = getIPClass(ip)
        expected_mask = getIPClassMask(ip)

        if ip_class in (ClassMask.CLASS_D, ClassMask.CLASS_E):
            self.result.setText("Classe IP non supportee")
            self.result.setStyleSheet("color: #f59e0b;")
            self.status_badge.setText("NON SUPPORTEE")
            self.status_badge.setObjectName("badgeWarn")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        if expected_mask == ClassMask.ERROR.value:
            self.result.setText("Adresse IP invalide")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        subnet = getSubnet(ip, normalized_mask)
        if subnet == ClassMask.ERROR.value:
            self.result.setText("Adresse IP invalide")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        class_network = getNetworkAddress(ip, expected_mask)
        if class_network == ClassMask.ERROR.value:
            self.result.setText("Adresse IP invalide")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return


        # ==========================================
        # AJOUT : Enregistrement en base de données SQLite 3
        # avec le tag de l'employé connecté (et écrasement si existant)
        # ==========================================
        from ...services.database import Database
        db = Database()
        db.save_f5_subnet(ip, normalized_mask)

        self.result.setText(
            "Réseau de classe (Majeur) : "
            f"{class_network}\n"
            "Sous-réseau personnalisé : "
            f"{subnet}"
        )
        self.result.setStyleSheet("color: #22c55e;")
        self.status_badge.setText("RÉSEAU")
        self.status_badge.setObjectName("badgeValid")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)
