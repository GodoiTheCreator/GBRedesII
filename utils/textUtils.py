def fromTexttoASCIIConverter(text):
    """
    Converts a given text to its ASCII representation.

    Args:
        text (str): The input text to be converted.

    Returns:
        str: The ASCII representation of the input text.
    """
    return ''.join(str(ord(char)) for char in text)

def fromASCIItoBinaryConverter(text):
    """
    Converts a given text to its binary representation.

    Args:
        text (str): The input text to be converted.

    Returns:
        str: The binary representation of the input text.
    """
    ascii_text = fromTexttoASCIIConverter(text)

    return ' '.join(format(int(char), '08b') for char in ascii_text)