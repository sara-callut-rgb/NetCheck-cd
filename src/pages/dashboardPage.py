import os

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from ..services.database import Database

from .views import (
    CidrTablePage,
    GetIpClassMaskPage,
    GetIpClassPage,
    GetSubnetPage,
    IsIpPage,
    RegisterPage,
    SameNetworkPage,
    UserProfilePage,
    GetSubnetSplitPage
)



class DashboardWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, user_info=None):
        super().__init__()

        db = Database()
        session_user = user_info if user_info is not None else db.getUserInfo()
        username = session_user["username"] if session_user else "Utilisateur"
        role = session_user["role"] if session_user else "RÔLE INCONNU"

        self.setObjectName("dashboardWindow")
        self.setWindowTitle("NetCheck - Tableau de bord")
        self.setFixedSize(1150, 650)
        self.setWindowFlags(
            Qt.Window |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowCloseButtonHint
        )

        # --- Structure principale ---
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # --- Coque principale ---
        shell = QFrame()
        shell.setObjectName("dashboardShell")
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        # --- Barre laterale ---
        self.nav = QFrame()
        self.nav.setObjectName("navFrame")
        self.nav.setFixedWidth(222)
        nav_layout = QVBoxLayout(self.nav)
        nav_layout.setContentsMargins(16, 20, 16, 16)
        nav_layout.setSpacing(10)

        brand = QLabel("NetCheck")
        brand.setObjectName("sidebarBrand")

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        nav_layout.addWidget(brand)
        nav_layout.addWidget(separator)
        nav_layout.addSpacing(10)



        # --- Zone des pages ---
        self.stack = QStackedWidget()
        self.stack.setObjectName("pagesStack")

        self.current_page_title = QLabel("Validation IP")
        self.current_page_title.setObjectName("dashboardHeading")

        self.current_page_hint = QLabel("Vérifie si une adresse IPv4 est valide")
        self.current_page_hint.setObjectName("dashboardSubheading")

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        icons_dir = os.path.join(base_dir, "assets", "icons")
        user_page = UserProfilePage(user_info=session_user)
        user_page.logout_requested.connect(self.request_logout)

        # --- Liste des pages ---
        pages = [
            ("Table CIDR", "Affiche les masques de /8 à /30 en CIDR, binaire et décimal", QIcon(os.path.join(icons_dir, "cidr.svg")), CidrTablePage()),
            ("Validation IP", "Vérifie si une adresse IPv4 a le bon format", QIcon(os.path.join(icons_dir, "ip.svg")), IsIpPage()),
            ("Classe IP", "Détermine la classe et signale les IP privées ou réservées", QIcon(os.path.join(icons_dir, "class.svg")), GetIpClassPage()),
            ("Masque de classe", "Retourne le masque par défaut selon la classe IP", QIcon(os.path.join(icons_dir, "mask.svg")), GetIpClassMaskPage()),
            ("Réseau et sous-réseau", "Calcule l'adresse réseau et sous-réseau d'une adresse IP et un masque", QIcon(os.path.join(icons_dir, "subnet.svg")), GetSubnetPage()),
            ("Même réseau", "Vérifie si deux IP sont dans le même réseau", QIcon(os.path.join(icons_dir, "subnet.svg")), SameNetworkPage()),
            #Ajout de la nouvelle fonctionnalité
            ("Découpe en SR", "Découpe un réseau en sous-réseaux de même taille à partir du nombre de SR", QIcon(os.path.join(icons_dir, "subnet.svg")), GetSubnetSplitPage()),
        ]
        #Ajout de la page d'inscription pour les utilisateurs avec le rôle "admin"
        if str(role).lower() == "admin":
            pages.append(("Inscription", "Ajoute un nouvel utilisateur (réservé aux admins)", QIcon(os.path.join(icons_dir, "ip.svg")), RegisterPage()))
        
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.page_descriptions = {}

        for index, (name, description, icon, page) in enumerate(pages):
            self.stack.addWidget(page)
            self.page_descriptions[index] = description

            btn = QPushButton(name)
            btn.setIcon(icon)
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setObjectName("navButton")
            btn.setCursor(Qt.PointingHandCursor)
            #Forme de bouton différent pour l'inscription
            if name == "Inscription":
                btn.setStyleSheet("border-radius: 24px;")
            btn.clicked.connect(lambda _checked, idx=index, title=name: self.switch_page(idx, title))
            self.button_group.addButton(btn)
            nav_layout.addWidget(btn)

        self.profile_page_index = self.stack.addWidget(user_page)
        self.page_descriptions[self.profile_page_index] = "Informations du compte et session actuelle"

        nav_layout.addStretch(1)

        # --- Carte utilisateur ---
        user_card = QFrame()
        user_card.setObjectName("navUserCard")
        user_layout = QVBoxLayout(user_card)
        user_layout.setContentsMargins(12, 10, 12, 10)
        user_layout.setSpacing(2)

        user_name = QLabel(username)
        user_name.setObjectName("navUserName")

        user_role = QLabel(role)
        user_role.setObjectName("navUserRole")

        user_layout.addWidget(user_name)
        user_layout.addWidget(user_role)

        user_card.setCursor(Qt.PointingHandCursor)
        user_card.mousePressEvent = self.open_profile_page

        nav_layout.addWidget(user_card)

        # --- Zone de contenu ---
        self.content = QFrame()
        self.content.setObjectName("contentFrame")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(26, 22, 26, 22)
        content_layout.setSpacing(18)

        # --- En-tete page ---
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        header_text_col = QVBoxLayout()
        header_text_col.setSpacing(4)
        header_text_col.addWidget(self.current_page_title)
        header_text_col.addWidget(self.current_page_hint)

        header_row.addLayout(header_text_col)
        header_row.addStretch(1)

        content_layout.addLayout(header_row)
        content_layout.addWidget(self.stack, 1)

        shell_layout.addWidget(self.nav)
        shell_layout.addWidget(self.content, 1)

        root.addWidget(shell)

        if self.button_group.buttons():
            self.button_group.buttons()[0].setChecked(True)
            self.switch_page(0, self.button_group.buttons()[0].text())


    def switch_page(self, page_index, title):
        self.stack.setCurrentIndex(page_index)
        self.current_page_title.setText(title)
        self.current_page_hint.setText(self.page_descriptions.get(page_index, ""))
        self.current_page_hint.setVisible(page_index != self.profile_page_index)


    def open_profile_page(self, _event):
        self.switch_page(self.profile_page_index, "Profil utilisateur")
        for button in self.button_group.buttons():
            button.setChecked(False)


    def request_logout(self):
        self.logout_requested.emit()
        self.close()
