def to_filename(name: str) -> str:
    result = ""
    for character in name:
        if character.isalnum():
            result += character.lower()
        else:
            result += "_"
    return result
