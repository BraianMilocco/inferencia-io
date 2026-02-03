def convert_errors_to_list(serializer_errors: dict) -> list[str]:
    """
    Converts serializer errors to a list of strings
    
    Args:
        serializer_errors (dict): Dictionary of serializer errors
    Returns:
        list[str]: List of errors as strings
    """
    error_messages = list()
    for field, errors in serializer_errors:
        for err in errors:
            error_messages.append(f"{field}: {err}")
    return error_messages