from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ...services.database import Database
from ...services.logic import getSubnetSplit, parseMask



class GetSubnetSplitPage(QWidget):
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

        self.ip_input = QComboBox()
        self.ip_input.setEditable(True)
        self.ip_input.setInsertPolicy(QComboBox.NoInsert)
        self.ip_input.lineEdit().setPlaceholderText("IPv4 du réseau")
        self.ip_input.setObjectName("primaryInput")
        self.ip_input.setFixedHeight(46)

        self.mask_input = QComboBox()
        self.mask_input.setEditable(True)
        self.mask_input.setInsertPolicy(QComboBox.NoInsert)
        self.mask_input.lineEdit().setPlaceholderText("Masque")
        self.mask_input.setObjectName("primaryInput")
        self.mask_input.setFixedHeight(46)

        self.nb_input = QComboBox()
        self.nb_input.setEditable(True)
        self.nb_input.setInsertPolicy(QComboBox.NoInsert)
        self.nb_input.lineEdit().setPlaceholderText("Nombre de SR")
        self.nb_input.setObjectName("primaryInput")
        self.nb_input.setFixedHeight(46)
        self.nb_input.lineEdit().returnPressed.connect(self.run_check)

        for field in (self.ip_input, self.mask_input, self.nb_input):
            field.view().pressed.connect(lambda index: self.on_param_selected(index.row()))
            field.view().activated.connect(lambda index: self.on_param_selected(index.row()))

        self.selected_id = None
        self.load_params()

        run_button = QPushButton("Découper")
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
        row.addWidget(self.nb_input, 1)
        row.addWidget(run_button)
        row.addWidget(clear_button)

        # --- Etat vide ---
        self.empty_state = QFrame()
        self.empty_state.setObjectName("emptyState")
        empty_layout = QHBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 14, 18, 14)

        empty_text = QLabel("Entrez un réseau, son masque et le nombre de sous-réseaux souhaités")
        empty_text.setObjectName("emptyStateText")
        empty_layout.addWidget(empty_text)

        # --- Carte resultat ---
        self.result_card = QFrame()
        self.result_card.setObjectName("resultCard")
        self.result_card.setVisible(False)
        result_layout = QVBoxLayout(self.result_card)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(8)

        self.status_badge = QLabel("DÉCOUPE")
        self.status_badge.setObjectName("badgeNeutral")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedWidth(140)

        self.result = QLabel("")
        self.result.setObjectName("statusMessage")

        # --- Tableau du plan d'adressage ---
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["N° SR", "Adresse SR", "Adresse BC", "1ère IP", "Dernière IP", "Pas", "Machines"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setObjectName("cidrTable")
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        result_layout.addWidget(self.status_badge, 0, Qt.AlignLeft)
        result_layout.addWidget(self.result)
        result_layout.addWidget(self.table, 1)

        card_layout.addLayout(row)
        card_layout.addWidget(self.empty_state)
        card_layout.addWidget(self.result_card, 1)

        # --- Encadré d'aide F7 ---
        self.help_card = QFrame()
        self.help_card.setObjectName("resultCard")
        help_layout = QVBoxLayout(self.help_card)
        help_layout.setContentsMargins(16, 14, 16, 14)
        help_layout.setSpacing(6)
        help_title = QLabel(" Astuce : Plan d'adressage VLSM / Fixe")
        help_title.setObjectName("resultIp")
        help_text = QLabel(
            "Entrez un réseau de départ, son masque et le nombre de sous-réseaux souhaités. "
            "L'outil calculera automatiquement le nouveau masque, le pas, les adresses de diffusion "
            "et la plage d'hôtes disponibles pour chaque sous-réseau."
        )
        help_text.setObjectName("dashboardSubheading")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_title)
        help_layout.addWidget(help_text)
        card_layout.addWidget(self.help_card)
        card_layout.addStretch(0) #  ici, F7 utilise un stretch à 0 car il y a le tableau

        card_layout.addStretch(0)

        layout.addWidget(card)

    #Récupération des paramètres sauvegardés dans la base de données
    def load_params(self):
        for field in (self.ip_input, self.mask_input, self.nb_input):
            field.clear()
        for row_id, saved_ip, saved_mask, saved_nb in Database().list_f7_params():
            self.ip_input.addItem(saved_ip, row_id)
            self.mask_input.addItem(saved_mask, row_id)
            self.nb_input.addItem(str(saved_nb), row_id)
        for field in (self.ip_input, self.mask_input, self.nb_input):
            field.setCurrentIndex(-1)
        self.selected_id = None

    def on_param_selected(self, index):
        self.selected_id = self.ip_input.itemData(index)
        for field in (self.ip_input, self.mask_input, self.nb_input):
            field.setCurrentIndex(index)

    def show_error(self, message):
        # --- Affichage d'une erreur (le tableau est masqué) ---
        self.table.setRowCount(0)
        self.table.setVisible(False)
        self.result.setText(message)
        self.result.setStyleSheet("color: #ef4444;")
        self.status_badge.setText("ERREUR")
        self.status_badge.setObjectName("badgeInvalid")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)


    def run_check(self):
        # --- Execution de la decoupe en sous-reseaux ---
        ip = self.ip_input.currentText().strip()
        mask = self.mask_input.currentText().strip()
        nb_text = self.nb_input.currentText().strip()

        self.empty_state.setVisible(False)
        self.result_card.setVisible(True)

        if not (nb_text.isascii() and nb_text.isdigit()):
            self.show_error("Le nombre de sous-réseaux doit être un nombre entier.")
            return

        rows, error = getSubnetSplit(ip, mask, int(nb_text))
        if error:
            self.show_error(error)
            return

        # Stockage des paramètres et de la découpe, avec le n° d'employé connecté
        db = Database()
        row_id = self.selected_id or db.find_f7_subnet_split(rows[0]["address"], parseMask(mask), int(nb_text))
        if row_id:
            db.update_f7_subnet_split(row_id, rows[0]["address"], parseMask(mask), int(nb_text), rows)
        else:
            db.save_f7_subnet_split(rows[0]["address"], parseMask(mask), int(nb_text), rows)
        self.load_params()
        self.ip_input.setEditText(ip)
        self.mask_input.setEditText(mask)
        self.nb_input.setEditText(nb_text)
        # Remplissage du tableau
        self.table.setRowCount(len(rows))
        for row_idx, sr in enumerate(rows):
            values = [str(sr["sr"]), sr["address"], sr["broadcast"], sr["first"], sr["last"], sr["step"], str(sr["hosts"])]
            for col_idx, value in enumerate(values):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        self.table.setVisible(True)
        self.result.setText(f"Nouveau masque : {rows[0]['mask']} ({parseMask(rows[0]['mask'])})")
        self.result.setStyleSheet("color: #22c55e;")
        self.status_badge.setText("DÉCOUPE")
        self.status_badge.setObjectName("badgeValid")
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    #fonction vider les champs
    def clear_fields(self):
        self.ip_input.clearEditText()
        self.mask_input.clearEditText()
        self.nb_input.clearEditText()
        self.selected_id = None
        self.table.setRowCount(0)
        self.table.setVisible(False)
        self.result_card.setVisible(False)
        self.empty_state.setVisible(True)