from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.logic import areIpsInSameNetwork, getNetworkAddress, isIp, isSubnetMask, parseMask



class SameNetworkPage(QWidget):
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

        self.ip1_input = QLineEdit()
        self.ip1_input.setPlaceholderText("IPv4 1")
        self.ip1_input.setObjectName("primaryInput")
        self.ip1_input.setFixedHeight(46)

        self.mask1_input = QLineEdit()
        self.mask1_input.setPlaceholderText("Masque 1")
        self.mask1_input.setObjectName("primaryInput")
        self.mask1_input.setFixedHeight(46)

        self.ip2_input = QLineEdit()
        self.ip2_input.setPlaceholderText("IPv4 2")
        self.ip2_input.setObjectName("primaryInput")
        self.ip2_input.setFixedHeight(46)
    
        self.mask2_input = QLineEdit()
        self.mask2_input.setPlaceholderText("Masque 2")
        self.mask2_input.setObjectName("primaryInput")
        self.mask2_input.setFixedHeight(46)
        self.mask2_input.returnPressed.connect(self.run_check)

        run_button = QPushButton("Vérifier")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(120, 46)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_check)

        row.addWidget(self.ip1_input, 1)
        row.addWidget(self.mask1_input, 1)
        row.addWidget(self.ip2_input, 1)
        row.addWidget(self.mask2_input, 1)
        row.addWidget(run_button)

        # --- Etat vide ---
        self.empty_state = QFrame()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QHBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)

        empty_text = QLabel("Entrez deux IP et leurs masques pour comparer")
        empty_text.setObjectName("emptyStateText")
        empty_layout.addWidget(empty_text)

        # --- Carte resultat ---
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setVisible(False)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(8)

        self.status_badge = QLabel("STATUT")
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
        # --- Execution de la comparaison ---
        ip1 = self.ip1_input.text().strip()
        mask1 = self.mask1_input.text().strip()
        ip2 = self.ip2_input.text().strip()
        mask2 = self.mask2_input.text().strip()
        normalized_mask1 = parseMask(mask1)
        normalized_mask2 = parseMask(mask2)

        self.empty_state.setVisible(False)
        self.result_card.setVisible(True)

        if not isIp(ip1) or not isIp(ip2):
            self.result.setText("Adresse IP invalide")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        if not normalized_mask1 or not normalized_mask2:
            self.result.setText("Masque invalide")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        if not isSubnetMask(normalized_mask1) or not isSubnetMask(normalized_mask2):
            self.result.setText("Masque invalide")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("ERREUR")
            self.status_badge.setObjectName("badgeInvalid")
            self.status_badge.style().unpolish(self.status_badge)
            self.status_badge.style().polish(self.status_badge)
            return

        same_network = areIpsInSameNetwork(ip1, normalized_mask1, ip2, normalized_mask2)
        direction_1 = getNetworkAddress(ip1, normalized_mask1) == getNetworkAddress(ip2, normalized_mask1)
        direction_2 = getNetworkAddress(ip2, normalized_mask2) == getNetworkAddress(ip1, normalized_mask2)

        # ==========================================
        # AJOUT : Enregistrement en base de données SQLite 3
        # avec le tag de l'employé connecté (et écrasement si existant)
        # ==========================================
        from ...services.database import Database
        db = Database()
        db.save_f6_same_network(ip1, normalized_mask1, ip2, normalized_mask2)

        if same_network:
            self.result.setText("Même réseau dans les deux sens")
            self.result.setStyleSheet("color: #22c55e;")
            self.status_badge.setText("OUI")
            self.status_badge.setObjectName("badgeValid")
        elif direction_1 or direction_2:
            details = []
            if direction_1:
                details.append("IP1 dans réseau IP2: OUI")
            else:
                details.append("IP1 dans réseau IP2: NON")

            if direction_2:
                details.append("IP2 dans réseau IP1: OUI")
            else:
                details.append("IP2 dans réseau IP1: NON")

            self.result.setText("\n".join(details))
            self.result.setStyleSheet("color: #f59e0b;")
            self.status_badge.setText("PARTIEL")
            self.status_badge.setObjectName("badgeWarn")
        else:
            self.result.setText("Aucun des deux sens ne correspond")
            self.result.setStyleSheet("color: #ef4444;")
            self.status_badge.setText("NON")
            self.status_badge.setObjectName("badgeInvalid")

        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)
