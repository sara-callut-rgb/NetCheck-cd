-- Activation des clés étrangères dans SQLite 3
PRAGMA foreign_keys = ON;

-- 1. Table des utilisateurs (avec employee_id)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    hashpassword TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'membre' CHECK (role IN ('membre', 'admin')),
    is_temporary INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT,
    last_login TEXT
);

-- 2. Table pour le bouton d'urgence Admin (2 clics sur la même journée)
CREATE TABLE IF NOT EXISTS security_votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    click_date TEXT NOT NULL,
    UNIQUE(employee_id, click_date),
    FOREIGN KEY (employee_id) REFERENCES users(employee_id)
);

-- 3. Fonctionnalité 1 : Table CIDR (Paramètres + Résultat)
CREATE TABLE IF NOT EXISTS f1_cidr (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cidr TEXT NOT NULL UNIQUE,
    binary_mask TEXT NOT NULL,
    decimal_mask TEXT NOT NULL
);

-- 4. Fonctionnalité 2 : Validation IP (Paramètre uniquement)
CREATE TABLE IF NOT EXISTS f2_ip_valid (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_input TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 5. Fonctionnalité 3 : Classe IP (Paramètre uniquement)
CREATE TABLE IF NOT EXISTS f3_ip_class (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_input TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 6. Fonctionnalité 4 : Masque de classe (Paramètre uniquement)
CREATE TABLE IF NOT EXISTS f4_class_mask (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_input TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 7. Fonctionnalité 5 : Réseau / Sous-réseau (Paramètres + Tag n° employé)
CREATE TABLE IF NOT EXISTS f5_subnet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_input TEXT NOT NULL,
    mask_input TEXT NOT NULL,
    last_modified_by TEXT NOT NULL,
    modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip_input, mask_input),
    FOREIGN KEY (last_modified_by) REFERENCES users(employee_id)
);

-- 8. Fonctionnalité 6 : Même réseau (Paramètres + Tag n° employé)
CREATE TABLE IF NOT EXISTS f6_same_net (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip1_input TEXT NOT NULL,
    mask1_input TEXT NOT NULL,
    ip2_input TEXT NOT NULL,
    mask2_input TEXT NOT NULL,
    last_modified_by TEXT NOT NULL,
    modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip1_input, mask1_input, ip2_input, mask2_input),
    FOREIGN KEY (last_modified_by) REFERENCES users(employee_id)
);

-- 9. Fonctionnalité 7 (Nouvelle) : Découpe classique en SRs
CREATE TABLE IF NOT EXISTS f7_subnet_split (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_ip TEXT NOT NULL,
    base_mask TEXT NOT NULL,
    nb_subnets INTEGER NOT NULL,
    splits_json TEXT NOT NULL,
    last_modified_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (last_modified_by) REFERENCES users(employee_id)
);

-- Insertion des 5 utilisateurs par défaut (INSERT OR IGNORE évite les doublons au redémarrage)
INSERT OR IGNORE INTO users (employee_id, username, hashpassword, role, is_temporary, is_active, locked_until)
VALUES 
    ('EMP-001', 'User1', '$2b$13$bHlfV9VzzlDnd67MQoJtFOnjus0tPTc24YLoZ8uCYRjmQuZLbjiCi', 'admin',  0, 1, NULL),
    ('EMP-002', 'User2', '$2b$13$bHlfV9VzzlDnd67MQoJtFOnjus0tPTc24YLoZ8uCYRjmQuZLbjiCi', 'membre', 0, 1, NULL),
    ('EMP-003', 'User3', '$2b$13$bHlfV9VzzlDnd67MQoJtFOnjus0tPTc24YLoZ8uCYRjmQuZLbjiCi', 'membre', 1, 1, NULL),
    ('EMP-004', 'User4', '$2b$13$bHlfV9VzzlDnd67MQoJtFOnjus0tPTc24YLoZ8uCYRjmQuZLbjiCi', 'membre', 0, 1, '2026-12-31 23:59:59'),
    ('EMP-005', 'User5', '$2b$13$bHlfV9VzzlDnd67MQoJtFOnjus0tPTc24YLoZ8uCYRjmQuZLbjiCi', 'membre', 0, 0, NULL);