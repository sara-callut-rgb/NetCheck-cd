import os
import re
import json
import sqlite3
from datetime import datetime, timedelta
import bcrypt


class Database:
    """
    Classe gérant la connexion à la base de données SQLite 3,
    l'authentification des utilisateurs, la sécurité (verrouillage, double validation)
    et la persistance des données pour les fonctionnalités 1 à 7.
    """

    # Variable de classe statique : conserve les infos de l'utilisateur connecté
    # (notamment son employee_id) pour qu'elles soient accessibles depuis toutes les pages.
    current_session = None

    def __init__(self):
        """
        Constructeur : configure les chemins vers la base SQLite 3,
        initialise les attributs de session et lance la création des tables.
        """
        # Récupère le chemin racine du projet (remonte de 2 dossiers depuis src/services/)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        db_dir = os.path.join(base_dir, "database")
        
        # Crée le dossier database/ s'il n'existe pas encore
        os.makedirs(db_dir, exist_ok=True)
        
        # Chemins vers le fichier de base de données SQLite et le script d'initialisation SQL
        self.db_path = os.path.join(db_dir, "netcheck.db")
        self.init_sql_path = os.path.join(db_dir, "init.sql")

        # Attributs d'état de connexion et de session utilisateur
        self.conn = None
        self.userId = None
        self.employeeId = None
        self.userName = None
        self.userRole = None
        self.previous_last_login = None
        self.last_error = ""
        self.password_reset_required = False

        # Paramètres de sécurité pour la connexion et les mots de passe
        self.max_failed_attempts = 5      # Nombre max d'échecs avant blocage
        self.lockout_minutes = 15         # Durée du blocage temporaire (en minutes)
        self.password_min_length = 13     # Longueur minimale d'un mot de passe définitif

        # Exécute automatiquement init.sql pour créer les tables SQLite 3 au lancement
        self._init_database()

    def _connection(self):
        """
        Établit ou retourne la connexion active à la base de données SQLite 3.
        Active également la vérification des clés étrangères (FOREIGN KEYS).
        """
        if self.conn is not None:
            return self.conn
        try:
            # Connexion au fichier local database/netcheck.db
            self.conn = sqlite3.connect(self.db_path)
            # SQLite désactive les clés étrangères par défaut : on les active ici
            self.conn.execute("PRAGMA foreign_keys = ON;")
            self.last_error = ""
            return self.conn
        except sqlite3.Error:
            self.last_error = "Erreur de connexion a la base de donnees"
            self.conn = None
            return None

    def _cursor(self):
        """
        Crée et retourne un curseur SQLite permettant d'exécuter des requêtes SQL.
        """
        conn = self._connection()
        if conn is None:
            return None
        return conn.cursor()

    def _close(self):
        """
        Ferme proprement la connexion à la base de données SQLite 3.
        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _init_database(self):
        """
        Lit et exécute le script SQL contenu dans database/init.sql
        afin de créer toutes les tables et les utilisateurs par défaut s'ils n'existent pas.
        """
        conn = self._connection()
        if conn is None:
            return
        try:
            if os.path.exists(self.init_sql_path):
                with open(self.init_sql_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                # executescript permet d'exécuter plusieurs requêtes SQL d'un coup
                conn.executescript(sql_script)
                conn.commit()
        except sqlite3.Error as e:
            self.last_error = f"Erreur d'initialisation SQLite : {e}"

    # =========================================================================
    # GESTION DES UTILISATEURS ET AUTHENTIFICATION
    # =========================================================================

    def listUsers(self):
        """
        Récupère la liste complète des utilisateurs enregistrés en base de données
        pour l'afficher dans le tableau d'administration.
        """
        cursor = self._cursor()
        if cursor is None:
            return []
        cursor.execute("""
            SELECT id, username, role, is_temporary, is_active, failed_attempts, locked_until, last_login
            FROM users
            ORDER BY id
        """)
        rows = cursor.fetchall()
        cursor.close()

        # Convertit les valeurs SQLite (0/1 en booléens et les textes en objets datetime)
        records = []
        for r in rows:
            locked_dt = self._parse_dt(r[6])
            login_dt = self._parse_dt(r[7])
            records.append((r[0], r[1], r[2], bool(r[3]), bool(r[4]), r[5], locked_dt, login_dt))
        self.last_error = ""
        return records

    def addUser(self, username, password, role, is_temporary=True, employee_id=None):
        """
        Ajoute un nouvel utilisateur dans la base de données (réservé aux admins).
        Génère un numéro d'employé (EMP-XXX) si aucun n'est fourni et hache le mot de passe avec bcrypt.
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            # Si le mot de passe n'est pas temporaire, on vérifie sa robustesse
            if not is_temporary and not self._isPasswordStrong(password):
                self.last_error = "PASSWORD_WEAK"
                return False

            # Génération automatique du matricule employé (ex: EMP-006)
            if not employee_id:
                cursor.execute("SELECT COUNT(*) FROM users")
                next_num = cursor.fetchone()[0] + 1
                employee_id = f"EMP-{next_num:03d}"

            # Hachage sécurisé du mot de passe avec un sel (13 tours)
            salt = bcrypt.gensalt(rounds=13)
            hashPassword = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
            
            cursor.execute("""
                INSERT INTO users (employee_id, username, hashpassword, role, is_temporary, is_active, failed_attempts, locked_until, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (employee_id, username, hashPassword, role, int(is_temporary), 1, 0, None, None))
            self._connection().commit()
            return True
        except sqlite3.Error:
            self.last_error = "Operation SQL impossible"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def updateRole(self, username, newRole):
        """
        Modifie le rôle ('membre' ou 'admin') d'un utilisateur existant.
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            cursor.execute("UPDATE users SET role = ? WHERE username = ?", (newRole, username))
            affected = cursor.rowcount
            self._connection().commit()
            return affected > 0
        except sqlite3.Error:
            self.last_error = "Operation SQL impossible"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def updateUsername(self, username, newUsername):
        """
        Modifie le nom d'utilisateur d'un compte existant.
        Renvoie False avec l'erreur USERNAME_TAKEN si le nouveau nom existe déjà.
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            cursor.execute("UPDATE users SET username = ? WHERE username = ?", (newUsername, username))
            affected = cursor.rowcount
            self._connection().commit()
            return affected > 0
        except sqlite3.Error:
            self.last_error = "USERNAME_TAKEN"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def setPassword(self, username, newPassword):
        """
        Définit un nouveau mot de passe définitif pour l'utilisateur.
        Vérifie la complexité du mot de passe, le hache, retire le statut temporaire (is_temporary = 0)
        et réinitialise le compteur d'échecs de connexion.
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            # Vérifie que le mot de passe respecte les critères de sécurité
            if not self._isPasswordStrong(newPassword):
                self.last_error = "PASSWORD_WEAK"
                return False
            
            salt = bcrypt.gensalt(rounds=13)
            hashPassword = bcrypt.hashpw(newPassword.encode("utf-8"), salt).decode("utf-8")
            cursor.execute("""
                UPDATE users
                SET hashpassword = ?, is_temporary = 0, failed_attempts = 0, locked_until = NULL
                WHERE username = ?
            """, (hashPassword, username))
            affected = cursor.rowcount
            self._connection().commit()
            return affected > 0
        except sqlite3.Error:
            self.last_error = "Operation SQL impossible"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def setPasswordAndActivate(self, username, newPassword):
        """
        Alias de setPassword utilisé lors du premier changement de mot de passe sur la page de login.
        """
        return self.setPassword(username, newPassword)

    def setTemporaryPassword(self, username, newPassword):
        """
        Définit un mot de passe temporaire (par un admin) et force l'utilisateur
        à le changer lors de sa prochaine connexion (is_temporary = 1).
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            salt = bcrypt.gensalt(rounds=13)
            hashPassword = bcrypt.hashpw(newPassword.encode("utf-8"), salt).decode("utf-8")
            cursor.execute("""
                UPDATE users
                SET hashpassword = ?, is_temporary = 1, failed_attempts = 0, locked_until = NULL
                WHERE username = ?
            """, (hashPassword, username))
            affected = cursor.rowcount
            self._connection().commit()
            return affected > 0
        except sqlite3.Error:
            self.last_error = "Operation SQL impossible"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def updateLockout(self, username, locked_until):
        """
        Met à jour ou lève la date de blocage temporaire d'un utilisateur.
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            locked_str = locked_until.strftime("%Y-%m-%d %H:%M:%S") if locked_until else None
            cursor.execute("UPDATE users SET locked_until = ? WHERE username = ?", (locked_str, username))
            affected = cursor.rowcount
            self._connection().commit()
            return affected > 0
        except sqlite3.Error:
            self.last_error = "Operation SQL impossible"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def deleteUser(self, username):
        """
        Désactive le compte d'un utilisateur (suppression logique : is_active = 0).
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            cursor.execute("UPDATE users SET is_active = 0 WHERE username = ?", (username,))
            affected = cursor.rowcount
            self._connection().commit()
            return affected > 0
        except sqlite3.Error:
            self.last_error = "Operation SQL impossible"
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def validateCredentials(self, username, password):
        """
        Vérifie les identifiants lors de la connexion :
        1. Vérifie si le compte existe, s'il est actif et s'il n'est pas temporairement bloqué.
        2. Compare le mot de passe saisi avec le hash bcrypt stocké.
        3. Si is_temporary vaut 1, demande la redéfinition du mot de passe.
        4. Sinon, ouvre la session et sauvegarde l'employee_id en mémoire.
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        self.password_reset_required = False
        cursor.execute("""
            SELECT id, username, hashpassword, role, is_temporary, is_active,
                   failed_attempts, locked_until, last_login, employee_id
            FROM users
            WHERE username = ?
        """, (username,))
        record = cursor.fetchone()
        cursor.close()

        if record:
            hash_stocke = record[2]
            is_temporary = bool(record[4])
            is_active = bool(record[5])
            failed_attempts = record[6] if record[6] is not None else 0
            locked_until = self._parse_dt(record[7])

            # Refus si le compte a été désactivé par un admin
            if not is_active:
                self.last_error = "COMPTE INACTIVE"
                return False

            # Refus si la date de verrouillage temporaire n'est pas encore dépassée
            now = datetime.now()
            if locked_until and locked_until > now:
                self.last_error = "COMPTE BLOQUE"
                return False

            # Vérification du mot de passe via bcrypt
            if bcrypt.checkpw(password.encode("utf-8"), hash_stocke.encode("utf-8")):
                # Si le mot de passe est temporaire (ou suite à une alerte de sécurité),
                # on bloque l'entrée directe et on redirige vers le changement de mot de passe
                if is_temporary:
                    self.last_error = "PASSWORD_RESET_REQUIRED"
                    self.password_reset_required = True
                    return False

                # Connexion réussie : remise à zéro des échecs et mise à jour de last_login
                self.previous_last_login = self._parse_dt(record[8])
                self._resetFailedAttempts(username)
                self._setLastLogin(username)

                # Stockage des informations de l'employé connecté
                self.userId = record[0]
                self.userName = record[1]
                self.userRole = record[3]
                self.employeeId = record[9]
                self.last_error = ""

                # Enregistrement dans la variable de classe pour y accéder depuis toutes les vues
                Database.current_session = self.getUserInfo()
                return True

            # En cas de mauvais mot de passe, on incrémente le compteur d'échecs
            self._registerFailedAttempt(username, failed_attempts)
            self.last_error = "Identifiants incorrects"
        else:
            self.last_error = "Identifiants incorrects"
        return False

    # =========================================================================
    # TÂCHE CHRIST : BOUTON D'URGENCE ADMIN (2 CLICS SUR LA MÊME JOURNÉE)
    # =========================================================================

    def registerEmergencyResetClick(self, employee_id=None):
        """
        Gère le clic sur le bouton de sécurité Admin (en cas de vol de base de données).
        L'action ne se déclenche que si 2 utilisateurs distincts cliquent sur la même journée.
        Retourne un tuple : (succes: bool, statut_ou_message: str, nb_clics_du_jour: int)
        """
        if not employee_id and Database.current_session:
            employee_id = Database.current_session.get("employee_id")
        if not employee_id:
            return False, "Employé non identifié.", 0

        # Date du jour au format YYYY-MM-DD
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor = self._cursor()
        if cursor is None:
            return False, "Erreur de connexion DB.", 0

        try:
            # 1. Supprime tous les clics qui datent des jours précédents
            cursor.execute("DELETE FROM security_votes WHERE click_date != ?", (today_str,))

            # 2. Vérifie si cet administrateur a déjà cliqué aujourd'hui
            cursor.execute(
                "SELECT 1 FROM security_votes WHERE employee_id = ? AND click_date = ?",
                (employee_id, today_str)
            )
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM security_votes WHERE click_date = ?", (today_str,))
                count = cursor.fetchone()[0]
                return False, "Vous avez déjà cliqué aujourd'hui. En attente d'un 2e utilisateur.", count

            # 3. Enregistre le clic de l'administrateur pour la journée en cours
            cursor.execute(
                "INSERT INTO security_votes (employee_id, click_date) VALUES (?, ?)",
                (employee_id, today_str)
            )

            # 4. Compte combien d'utilisateurs différents ont cliqué aujourd'hui
            cursor.execute("SELECT COUNT(DISTINCT employee_id) FROM security_votes WHERE click_date = ?", (today_str,))
            count = cursor.fetchone()[0]

            if count >= 2:
                # 2 clics atteints sur la même journée :
                # On passe tous les utilisateurs en is_temporary = 1 pour les forcer à changer leur MDP
                cursor.execute("UPDATE users SET is_temporary = 1")
                # On nettoie la table des votes après déclenchement
                cursor.execute("DELETE FROM security_votes WHERE click_date = ?", (today_str,))
                self._connection().commit()
                return True, "TRIGGERED", 2
            else:
                # 1 seul clic pour l'instant : en attente de la 2e confirmation
                self._connection().commit()
                return True, "WAITING_SECOND", count

        except sqlite3.Error:
            self._connection().rollback()
            return False, "Erreur SQL lors du vote de sécurité.", 0
        finally:
            cursor.close()

    # =========================================================================
    # TÂCHE CHRIST : FONCTIONNALITÉS 5 ET 6 (TAG N° EMPLOYÉ AVEC ÉCRASEMENT)
    # =========================================================================

    def save_f5_subnet(self, ip_input: str, mask_input: str, employee_id: str = None):
        """
        Enregistre les paramètres d'entrée de la Fonctionnalité 5 (sans le résultat).
        Tague le numéro d'employé (last_modified_by). Si l'enregistrement existe déjà,
        écrase l'ancien numéro d'employé par celui du nouvel utilisateur.
        """
        if not employee_id and Database.current_session:
            employee_id = Database.current_session.get("employee_id", "EMP-001")
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # ON CONFLICT DO UPDATE permet d'écraser last_modified_by si l'entrée existe déjà
            cursor.execute("""
                INSERT INTO f5_subnet (ip_input, mask_input, last_modified_by, modified_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(ip_input, mask_input) DO UPDATE SET
                    last_modified_by = excluded.last_modified_by,
                    modified_at = excluded.modified_at
            """, (ip_input, mask_input, employee_id, now_str))
            self._connection().commit()
            return True
        except sqlite3.Error:
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def save_f6_same_network(self, ip1: str, mask1: str, ip2: str, mask2: str, employee_id: str = None):
        """
        Enregistre les paramètres d'entrée de la Fonctionnalité 6 (sans le résultat).
        Tague le numéro d'employé (last_modified_by). Si l'enregistrement existe déjà,
        écrase l'ancien numéro d'employé par celui du nouvel utilisateur.
        """
        if not employee_id and Database.current_session:
            employee_id = Database.current_session.get("employee_id", "EMP-001")
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # ON CONFLICT DO UPDATE écrase l'ancien numéro d'employé en cas de modification/recalcul
            cursor.execute("""
                INSERT INTO f6_same_net (ip1_input, mask1_input, ip2_input, mask2_input, last_modified_by, modified_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(ip1_input, mask1_input, ip2_input, mask2_input) DO UPDATE SET
                    last_modified_by = excluded.last_modified_by,
                    modified_at = excluded.modified_at
            """, (ip1, mask1, ip2, mask2, employee_id, now_str))
            self._connection().commit()
            return True
        except sqlite3.Error:
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    # =========================================================================
    # MÉTHODES POUR SARA (FONCTIONNALITÉS 1, 2, 3, 4 ET 7)
    # =========================================================================

    def save_f1_cidr_table(self, cidr_rows: list):
        """
        Fonctionnalité 1 : Stocke en base de données le tableau CIDR complet (entrées + résultats).
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            cursor.executemany("""
                INSERT OR REPLACE INTO f1_cidr (cidr, binary_mask, decimal_mask)
                VALUES (?, ?, ?)
            """, cidr_rows)
            self._connection().commit()
            return True
        except sqlite3.Error:
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def save_f2_ip_valid(self, ip_input: str):
        """Fonctionnalité 2 : Stocke uniquement l'IP saisie (sans le résultat)."""
        return self._save_single_ip_param("f2_ip_valid", ip_input)

    def save_f3_ip_class(self, ip_input: str):
        """Fonctionnalité 3 : Stocke uniquement l'IP saisie (sans le résultat)."""
        return self._save_single_ip_param("f3_ip_class", ip_input)

    def save_f4_class_mask(self, ip_input: str):
        """Fonctionnalité 4 : Stocke uniquement l'IP saisie (sans le résultat)."""
        return self._save_single_ip_param("f4_class_mask", ip_input)

    def _save_single_ip_param(self, table_name: str, ip_input: str):
        """
        Méthode générique interne pour enregistrer un paramètre IP simple (F2, F3, F4).
        """
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            cursor.execute(f"INSERT INTO {table_name} (ip_input) VALUES (?)", (ip_input,))
            self._connection().commit()
            return True
        except sqlite3.Error:
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    def save_f7_subnet_split(self, network_ip: str, base_mask: str, nb_subnets: int, splits_list: list, employee_id: str = None):
        """
        Fonctionnalité 7 (Nouvelle) : Stocke la découpe en sous-réseaux classique
        ainsi que le numéro d'employé dans la base SQLite 3.
        """
        if not employee_id and Database.current_session:
            employee_id = Database.current_session.get("employee_id", "EMP-001")
        cursor = self._cursor()
        if cursor is None:
            return False
        try:
            # Convertit la liste des sous-réseaux obtenus en chaîne JSON pour le stockage
            splits_json = json.dumps(splits_list, ensure_ascii=False)
            cursor.execute("""
                INSERT INTO f7_subnet_split (network_ip, base_mask, nb_subnets, splits_json, last_modified_by)
                VALUES (?, ?, ?, ?, ?)
            """, (network_ip, base_mask, nb_subnets, splits_json, employee_id))
            self._connection().commit()
            return True
        except sqlite3.Error:
            self._connection().rollback()
            return False
        finally:
            cursor.close()

    # =========================================================================
    # MÉTHODES INTERNES DE SÉCURITÉ ET DE FORMATAGE
    # =========================================================================

    def _parse_dt(self, value):
        """
        Convertit une date stockée sous forme de texte dans SQLite en objet datetime Python.
        """
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue
        return None

    def _isPasswordStrong(self, password):
        """
        Vérifie qu'un mot de passe respecte la politique de sécurité :
        - Au moins 13 caractères
        - Au moins 1 majuscule, 1 minuscule, 1 chiffre et 1 caractère spécial.
        """
        if not password or len(password) < self.password_min_length:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[^A-Za-z0-9]", password):
            return False
        return True

    def _registerFailedAttempt(self, username, failed_attempts):
        """
        Incrémente le nombre de tentatives de connexion échouées.
        Si le seuil (5 essais) est atteint, verrouille le compte pendant 15 minutes.
        """
        cursor = self._cursor()
        if cursor is None:
            return
        try:
            next_attempts = failed_attempts + 1
            locked_until = None
            if next_attempts >= self.max_failed_attempts:
                locked_dt = datetime.now() + timedelta(minutes=self.lockout_minutes)
                locked_until = locked_dt.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE users SET failed_attempts = ?, locked_until = ? WHERE username = ?
            """, (next_attempts, locked_until, username))
            self._connection().commit()
        except sqlite3.Error:
            self._connection().rollback()
        finally:
            cursor.close()

    def _resetFailedAttempts(self, username):
        """
        Remet à zéro le compteur d'échecs et déverrouille le compte après une connexion réussie.
        """
        cursor = self._cursor()
        if cursor is None:
            return
        try:
            cursor.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE username = ?", (username,))
            self._connection().commit()
        except sqlite3.Error:
            self._connection().rollback()
        finally:
            cursor.close()

    def _setLastLogin(self, username):
        """
        Enregistre la date et l'heure actuelles comme dernière connexion de l'utilisateur.
        """
        cursor = self._cursor()
        if cursor is None:
            return
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ? WHERE username = ?", (now_str, username))
            self._connection().commit()
        except sqlite3.Error:
            self._connection().rollback()
        finally:
            cursor.close()

    def getLastLogin(self, username):
        """
        Récupère la date de dernière connexion d'un utilisateur donné.
        """
        if self.userName == username and self.previous_last_login is not None:
            return self.previous_last_login
        cursor = self._cursor()
        if cursor is None:
            return None
        cursor.execute("SELECT last_login FROM users WHERE username = ?", (username,))
        record = cursor.fetchone()
        cursor.close()
        return self._parse_dt(record[0]) if record else None

    def getUserInfo(self):
        """
        Retourne un dictionnaire contenant toutes les informations de session de l'utilisateur
        connecté (id, employee_id, username, role, last_login).
        """
        if self.userId is None or self.userName is None or self.userRole is None:
            return Database.current_session
        return {
            "id": self.userId,
            "employee_id": self.employeeId,
            "username": self.userName,
            "role": self.userRole,
            "last_login": self.previous_last_login
        }