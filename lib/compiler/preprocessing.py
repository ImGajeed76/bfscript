import os


def handle_includes(filepath: str, processed_files=None):
    """
    Recursively processes #include directives in a file.
    Returns the combined source code as a string.
    Prevents circular includes.
    """
    if processed_files is None:
        processed_files = set()

    abs_filepath = os.path.abspath(filepath)

    if abs_filepath in processed_files:
        raise RecursionError(f"Circular include detected: {filepath}")

    processed_files.add(abs_filepath)
    base_dir = os.path.dirname(abs_filepath)
    output_code = []

    try:
        with open(abs_filepath, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                stripped_line = line.strip()
                if stripped_line.startswith("#include"):
                    parts = stripped_line.split(maxsplit=1)
                    if len(parts) == 2 and parts[1].endswith(";"):
                        filename_part = parts[1][:-1].strip()
                        if filename_part.startswith('"') and filename_part.endswith('"'):
                            include_filename = filename_part[1:-1]
                            include_filepath = os.path.join(base_dir, include_filename)
                            try:
                                # Recursively process the included file
                                included_code = handle_includes(include_filepath, processed_files.copy())
                                output_code.append(f"// --- Start include: {include_filename} ---\n")
                                output_code.append(included_code)
                                output_code.append(f"\n// --- End include: {include_filename} ---")
                            except FileNotFoundError:
                                raise FileNotFoundError(
                                    f"Include file not found: '{include_filename}' "
                                    f"(referenced in {filepath}:{line_num})"
                                ) from None
                            except RecursionError as e:
                                raise RecursionError(
                                    f"{e} (referenced in {filepath}:{line_num})"
                                ) from None
                        else:
                            raise ValueError(
                                f"Invalid #include format in {filepath}:{line_num}. "
                                "Expected #include \"filename\";"
                            )
                    else:
                        raise ValueError(
                            f"Invalid #include format in {filepath}:{line_num}. "
                            "Expected #include \"filename\";"
                        )
                else:
                    # Append original line (preserving structure/comments for now)
                    output_code.append(line.rstrip()) # Avoid adding extra newlines
    except FileNotFoundError:
        raise FileNotFoundError(f"Main file not found: {filepath}") from None

    # Remove the file from the set for the current path *after* processing siblings/parents
    # This allows including the same file multiple times if not circular
    processed_files.remove(abs_filepath)

    return "\n".join(output_code)

def get_defines(full_code: str):
    """
    Extracts #define directives from a file.
    Returns a dictionary of defined constants.
    """
    defines = {}

    for line in full_code.splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("#define"):
            parts = stripped_line.split(maxsplit=2)
            if len(parts) == 3:
                name = parts[1]
                value = parts[2]
                defines[name] = value

    return defines