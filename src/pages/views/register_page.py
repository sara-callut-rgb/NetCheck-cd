from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ...services.database import Database



class RegisterPage(QWidget):
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

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.username_input.setObjectName("primaryInput")
        self.username_input.setFixedHeight(46)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe temporaire")
        self.password_input.setObjectName("primaryInput")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(46)
        self.password_input.returnPressed.connect(self.run_register)

        self.role_input = QComboBox()
        self.role_input.setObjectName("primaryInput")
        self.role_input.addItems(["membre", "admin"])
        self.role_input.setFixedHeight(46)

        run_button = QPushButton("Inscrire")
        run_button.setObjectName("actionButton")
        run_button.setFixedSize(122, 46)
        run_button.setCursor(Qt.PointingHandCursor)
        run_button.clicked.connect(self.run_register)

        row.addWidget(self.username_input, 1)
        row.addWidget(self.password_input, 1)
        row.addWidget(self.role_input, 1)

        # --- Message ---
        self.message = QLabel("")
        self.message.setObjectName("statusMessage")

        card_layout.addLayout(row)
        card_layout.addWidget(run_button)
        card_layout.addWidget(self.message)
        card_layout.addStretch(1)

        layout.addWidget(card)

    def run_register(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password:
            self.show_message("Nom d'utilisateur et mot de passe obligatoires.", True)
            return

        if Database().addUser(username, password, role, is_temporary=True):
            self.show_message("Utilisateur ajouté avec succès.")
            self.username_input.clear()
            self.password_input.clear()
            return

        self.show_message("Échec de l'ajout (nom déjà pris).", True)

    def show_message(self, text, is_error=False):
        color = "#ff8da1" if is_error else "#a7f3d0"
        self.message.setStyleSheet(f"color: {color};")
        self.message.setText(text)