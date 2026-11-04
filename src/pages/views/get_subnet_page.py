from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.logic import ClassMask, getIPClass, getIPClassMask, getIpError, getMaskError, getNetworkAddress, getSubnet, isClassFull, isIp, isSubnetMask, parseMask
from ...services.database import Database

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

        #Liste des paramètres déjà enregistrés
        self.ip_input = QComboBox()
        self.ip_input.setEditable(True)
        self.ip_input.setInsertPolicy(QComboBox.NoInsert)
        self.ip_input.lineEdit().setPlaceholderText("IPv4")
        self.ip_input.setObjectName("primaryInput")
        self.ip_input.setFixedHeight(46)

        self.mask_input = QComboBox()
        self.mask_input.setEditable(True)
        self.mask_input.setInsertPolicy(QComboBox.NoInsert)
        self.mask_input.lineEdit().setPlaceholderText("Masque classful")
        self.mask_input.setObjectName("primaryInput")
        self.mask_input.setFixedHeight(46)
        self.mask_input.lineEdit().returnPressed.connect(self.run_check)

        for field in (self.ip_input, self.mask_input):
            field.view().pressed.connect(lambda index: self.on_param_selected(index.row()))
            field.view().activated.connect(lambda index: self.on_param_selected(index.row()))

        self.selected_id = None
        self.load_params()

        run_button = QPushButton("Calculer")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(122, 46)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_check)

        #boutton vider les champs
        clear_button = QPushButton("Vider")
        clear_button.setObjectName("actionButton")
        clear_button.setFixedSize(90, 46)
        clear_button.setCursor(Qt.PointingHandCursor)
        clear_button.clicked.connect(self.clear_fields)

        row.addWidget(self.ip_input, 1)
        row.addWidget(self.mask_input, 1)
        row.addWidget(run_button)
        row.addWidget(clear_button)

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

        # --- Encadré d'aide F5 ---
        self.help_card = QFrame()
        self.help_card.setObjectName("resultCard")
        help_layout = QVBoxLayout(self.help_card)
        help_layout.setContentsMargins(16, 14, 16, 14)
        help_layout.setSpacing(6)
        help_title = QLabel(" Rappel : Calcul de Sous-réseau")
        help_title.setObjectName("resultIp")
        help_text = QLabel(
            "L'opération ET logique (AND bit à bit) entre l'adresse IP et le masque de sous-réseau "
            "permet de déterminer l'adresse du réseau principal (majeur) ainsi que celle du sous-réseau personnalisé."
        )
        help_text.setObjectName("dashboardSubheading")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        card_layout.addWidget(self.help_card)
        card_layout.addStretch(1)


        card_layout.addStretch(1)

        layout.addWidget(card)

    #Récupération des paramètres sauvegardés dans la base de données
    def load_params(self):
        self.ip_input.clear()
        self.mask_input.clear()
        for row_id, saved_ip, saved_mask in Database().list_f5_params():
            self.ip_input.addItem(saved_ip, row_id)
            self.mask_input.addItem(saved_mask, row_id)
        self.ip_input.setCurrentIndex(-1)
        self.mask_input.setCurrentIndex(-1)
        self.selected_id = None

    def on_param_selected(self, index):
        self.selected_id = self.ip_input.itemData(index)
        self.ip_input.setCurrentIndex(index)
        self.mask_input.setCurrentIndex(index)

    def run_check(self):
        # --- Execution du calcul de sous-reseau ---
        ip = self.ip_input.currentText().strip()
        mask = self.mask_input.currentText().strip()
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
        db = Database()
        if self.selected_id:
            db.update_f5_subnet(self.selected_id, ip, normalized_mask)
        else:
            db.save_f5_subnet(ip, normalized_mask)
        self.load_params()
        self.ip_input.setEditText(ip)
        self.mask_input.setEditText(mask)

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

    #fonction vider les champs
    def clear_fields(self):
        self.selected_id = None
        self.ip_input.clearEditText()
        self.mask_input.clearEditText()
        self.result_card.setVisible(False)
        self.empty_state.setVisible(True)
