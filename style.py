class Style:
    # Text colors
    BLUE = '\033[94m'  # Blue text
    CYAN = '\033[96m'  # Cyan text
    GRAY = '\033[37m'  # Bright Gray text

    # Special styles
    HEADER = '\033[92m'  # Green text (Header)
    WARNING = '\033[93m'  # Yellow text (Warning)
    FAIL = '\033[31m'  # Red text

    # Text formatting
    BOLD = '\033[1m'  # Bold text
    UNDERLINE = '\033[4m'  # Underlined text

    # Reset to default
    END_STYLE = '\033[0m'  # End formatting/reset color
