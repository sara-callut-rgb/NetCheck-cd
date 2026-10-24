from enum import Enum
from .utils import bin_to_int, int_to_bin

class ClassMask(Enum):
    CLASS_A = "255.0.0.0"
    CLASS_B = "255.255.0.0"
    CLASS_C = "255.255.255.0"
    CLASS_D = "N/A_D"
    CLASS_E = "N/A_E"
    ERROR = "error"

#Modification du message d'erreur pour les adresses IP invalides
def getIpError(ip: str) -> str | None:
    if type(ip) is not str or ip.strip() == "":
        return "Veuillez entrer une adresse IP."

    parts = ip.split(".")
    if len(parts) != 4:
        return "Attention ! Une adresse IP contient 4 octets."

    for part in parts:
        if not (part.isdigit()):
            return "Veuillez ne rentrer que des chiffres."
        if int(part) > 255:
            return "Veuillez entrer des nombres compris entre 0 et 255."

    return None

def isIp(ip: str) -> bool:
    return getIpError(ip) is None

def parseMask(mask: str) -> str | None:
    if type(mask) is not str:
        return None

    cleaned = mask.strip()
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]

    if cleaned.isdigit():
        cidr = int(cleaned)
        if cidr is None or cidr < 0 or cidr > 32:
            return None
        return _cidrToMask(cidr)

    if isIp(cleaned):
        return cleaned

    return None

def _cidrToMask(cidr: int) -> str:
    bits = "1" * cidr + "0" * (32 - cidr)
    octets = []

    for i in range(0, 32, 8):
        value = bin_to_int(bits[i:i + 8])
        octets.append(str(value))

    return ".".join(octets)

def isSubnetMask(mask: str) -> bool:
    normalized = parseMask(mask)
    if not normalized:
        return False

    bits = []
    for part in normalized.split("."):
        value = int(part)
        if value is None:
            return False
        bits.append(int_to_bin(value))

    return "01" not in "".join(bits)

#Vérification des messages d'erreur des masques
def getMaskError(mask: str) -> str | None:
    if type(mask) is not str or mask.strip() == "":
        return "Veuillez entrer un masque."

    cleaned = mask.strip()
    if cleaned.startswith("/"):
        cleaned = cleaned[1:]

    if cleaned.isascii() and cleaned.isdigit():
        if int(cleaned) > 32:
            return "Un masque CIDR doit être compris entre /0 et /32."
        return None

    parts = cleaned.split(".")
    if len(parts) != 4:
        return "Attention ! Un masque contient 4 octets."

    for part in parts:
        if not (part.isascii() and part.isdigit()):
            return "Un masque ne contient que des chiffres."
        if int(part) > 255:
            return "Veuillez entrer des nombres compris entre 0 et 255."

    if not isSubnetMask(cleaned):
        return "Masque invalide."

    return None

def getNetworkAddress(ip: str, mask: str) -> str:
    normalized = parseMask(mask)
    if not isIp(ip) or not normalized:
        return ClassMask.ERROR.value

    ip_parts = ip.split(".")
    mask_parts = normalized.split(".")

    result_parts = []
    for i in range(4):
        ip_value = int(ip_parts[i])
        mask_value = int(mask_parts[i])
        if ip_value is None or mask_value is None:
            return ClassMask.ERROR.value

        ip_bin = int_to_bin(ip_value)
        mask_bin = int_to_bin(mask_value)

        and_bits = []
        for j in range(8):
            if ip_bin[j] == "1" and mask_bin[j] == "1":
                and_bits.append("1")
            else:
                and_bits.append("0")

        and_value = bin_to_int("".join(and_bits))
        result_parts.append(str(and_value))

    return ".".join(result_parts)

def getIPClass(ip: str) -> ClassMask:
    if not isIp(ip):
        return ClassMask.ERROR

    firstNum = int(ip.split(".")[0])

    if 0 <= firstNum <= 127:
        return ClassMask.CLASS_A
    elif 128 <= firstNum <= 191:
        return ClassMask.CLASS_B
    elif 192 <= firstNum <= 223:
        return ClassMask.CLASS_C
    elif 224 <= firstNum <= 239:
        return ClassMask.CLASS_D
    elif 240 <= firstNum <= 255:
        return ClassMask.CLASS_E

    return ClassMask.ERROR

def isClassFull(mask: str) -> bool:
    normalized = parseMask(mask)
    if not normalized:
        return False

    return normalized in {
        ClassMask.CLASS_A.value,
        ClassMask.CLASS_B.value,
        ClassMask.CLASS_C.value,
    }

def isPrivateIp(ip: str) -> bool:
    if not isIp(ip):
        return False

    parts = ip.split(".")
    first = int(parts[0])
    second = int(parts[1])

    if first == 10:
        return True

    if first == 172 and 16 <= second <= 31:
        return True

    if first == 192 and second == 168:
        return True

    return False


def isReservedIp(ip: str) -> bool:
    if not isIp(ip):
        return False

    if ip == "0.0.0.0":
        return True

    if ip == "255.255.255.255":
        return True

    first = int(ip.split(".")[0])
    second = int(ip.split(".")[1])

    if first == 0:
        return True

    if first == 127:
        return True

    if first == 169 and second == 254:
        return True

    if 224 <= first <= 239:
        return True

    if 240 <= first <= 255:
        return True

    return False


def getIPClassMask(ip: str) -> str:
    if not isIp(ip):
        return ClassMask.ERROR.value

    ipClasse = getIPClass(ip)

    match ipClasse:
        case ClassMask.CLASS_A | ClassMask.CLASS_B | ClassMask.CLASS_C:
            return ipClasse.value
        case ClassMask.CLASS_D | ClassMask.CLASS_E:
            return "N/A"
        case _:
            return ClassMask.ERROR.value


def getSubnet(ip: str, mask: str) -> str:
    normalized = parseMask(mask)
    if not isIp(ip) or not normalized:
        return ClassMask.ERROR.value

    if not isSubnetMask(normalized):
        return ClassMask.ERROR.value

    return getNetworkAddress(ip, normalized)


def areIpsInSameNetwork(ip1: str, mask1: str, ip2: str, mask2: str) -> bool:
    if not isIp(ip1) or not isIp(ip2):
        return False

    normalized_1 = parseMask(mask1)
    normalized_2 = parseMask(mask2)
    if not normalized_1 or not normalized_2:
        return False

    if not isSubnetMask(normalized_1) or not isSubnetMask(normalized_2):
        return False

    network_from_1 = getNetworkAddress(ip1, normalized_1)
    network_from_2 = getNetworkAddress(ip2, normalized_2)

    if network_from_1 == ClassMask.ERROR.value or network_from_2 == ClassMask.ERROR.value:
        return False

    return (
        getNetworkAddress(ip1, normalized_1) == getNetworkAddress(ip2, normalized_1)
        and getNetworkAddress(ip2, normalized_2) == getNetworkAddress(ip1, normalized_2)
    )


def genererTableauCIDR() -> list[list[str]]:
    tableResult = []
    for cidr in range(8, 31):
        line = []

        binaires = "1" * cidr + "0" * (32 - cidr)
        octets_binaires = []

        for i in range(0, 32, 8):
            octets_binaires.append(binaires[i:i + 8])

        binaire_pointe = ".".join(octets_binaires)

        decimal = []
        for octet in octets_binaires:
            decimal.append(str(bin_to_int(octet)))

        decimal_pointe = ".".join(decimal)

        line.append(f"{cidr}")
        line.append(binaire_pointe)
        line.append(decimal_pointe)

        tableResult.append(line)

    return tableResult


#----------- NOUVELLE FONCTIONNALITE ----------- 
def _intToIp(value: int) -> str:
    octets = []
    for power in (3, 2, 1, 0):
        octets.append(str(value // 2 ** (8 * power) % 256))
    return ".".join(octets)


def getSubnetSplit(ip: str, mask: str, nb_subnets: int) -> tuple[list[dict], str | None]:
    """Découpe classique en sous-réseaux de même taille.
    Renvoie (liste des sous-réseaux, message d'erreur ou None)."""
    error = getIpError(ip)
    if error:
        return [], error

    error = getMaskError(mask)
    if error:
        return [], error
    normalized = parseMask(mask)

    if type(nb_subnets) is not int or nb_subnets < 1:
        return [], "Il faut au moins 1 sous-réseau."

    # Longueur du masque de départ = nombre de bits à 1
    prefix = "".join(int_to_bin(int(o)) for o in normalized.split(".")).count("1")

    # Bits à emprunter : plus petit n tel que 2^n - 1 >= nombre de SR demandés
    # (-1 car le dernier SR, celui dont tous les bits valent 1, n'est pas utilisable)
    bits = 1
    while 2 ** bits - 1 < nb_subnets:
        bits += 1

    new_prefix = prefix + bits
    if new_prefix > 30:
        return [], f"Découpe impossible : /{new_prefix} ne laisse plus de place pour des machines (maximum /30)."

    # Adresse du réseau de départ, convertie en entier
    parts = [int(p) for p in getNetworkAddress(ip, normalized).split(".")]
    network_int = parts[0] * 2 ** 24 + parts[1] * 2 ** 16 + parts[2] * 2 ** 8 + parts[3]

    size = 2 ** (32 - new_prefix)               # nombre d'adresses par SR
    octet_index = (new_prefix - 1) // 8 + 1     # octet où se lit le "pas"
    step = 2 ** (8 * octet_index - new_prefix)

    rows = []
    for i in range(nb_subnets):
        start = network_int + i * size
        rows.append({
            "sr": i + 1,
            "address": _intToIp(start),
            "first": _intToIp(start + 1),
            "last": _intToIp(start + size - 2),
            "broadcast": _intToIp(start + size - 1),
            "mask": f"/{new_prefix}",
            "step": f"{step} sur {octet_index}{'er' if octet_index == 1 else 'ème'} octet",
            "hosts": size - 2,
        })
    return rows, None