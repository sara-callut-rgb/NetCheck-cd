from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

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

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IPv4 du réseau")
        self.ip_input.setObjectName("primaryInput")
        self.ip_input.setFixedHeight(46)

        self.mask_input = QLineEdit()
        self.mask_input.setPlaceholderText("Masque")
        self.mask_input.setObjectName("primaryInput")
        self.mask_input.setFixedHeight(46)

        self.nb_input = QLineEdit()
        self.nb_input.setPlaceholderText("Nombre de SR")
        self.nb_input.setObjectName("primaryInput")
        self.nb_input.setFixedHeight(46)
        self.nb_input.returnPressed.connect(self.run_check)

        run_button = QPushButton("Découper")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(122, 46)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_check)

        row.addWidget(self.ip_input, 1)
        row.addWidget(self.mask_input, 1)
        row.addWidget(self.nb_input, 1)
        row.addWidget(run_button)

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
        card_layout.addStretch(0)

        layout.addWidget(card)


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
        ip = self.ip_input.text().strip()
        mask = self.mask_input.text().strip()
        nb_text = self.nb_input.text().strip()

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
        Database().save_f7_subnet_split(rows[0]["address"], parseMask(mask), int(nb_text), rows)

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