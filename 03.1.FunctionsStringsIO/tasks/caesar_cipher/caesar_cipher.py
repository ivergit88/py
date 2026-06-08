def caesar_encrypt(message: str, n: int) -> str:
    """Encrypt message using caesar cipher

    :param message: message to encrypt
    :param n: shift
    :return: encrypted message
    """
    result: list[str] = []
    for char in message:
        if char.isupper():
            result.append(chr((ord(char) - ord('A') + n) % 26 + ord('A')))
        elif char.islower():
            result.append(chr((ord(char) - ord('a') + n) % 26 + ord('a')))
        else:
            result.append(char)
    return ''.join(result)
