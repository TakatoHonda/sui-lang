import sys

def _calculate_block_depth(lines: list[str]) -> int:
    """
    Roughly track function block depth for REPL buffering.
    """
    depth = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(';'):
            continue
        tokens = stripped.split()
        if tokens[0] == '#' and tokens[-1] == '{':
            depth += 1
        elif tokens[0] == '}' and depth > 0:
            depth -= 1
    return depth


def run_repl():
    """
    Start interactive Sui shell.
    """
    try:
        import readline  # noqa: F401
    except Exception:
        # readline is optional; ignore if unavailable (e.g., Windows)
        pass

    # Local import to avoid circular dependency at module load time
    from ..sui import SuiInterpreter, validate_line

    print("Sui REPL (empty line to execute, .exit / .quit / .reset)")
    interp = SuiInterpreter()
    buffer: list[str] = []
    prompt = ">>> "

    while True:
        try:
            line = input(prompt)
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()  # suppress traceback on Ctrl+C
            break

        stripped = line.strip()

        # Meta commands (only when buffer is empty)
        if not buffer and stripped in {'.exit', '.quit'}:
            break
        if not buffer and stripped == '.reset':
            interp = SuiInterpreter()
            print("State reset.")
            continue

        # Skip pure empty line when there is nothing buffered
        if stripped == '' and not buffer:
            continue

        buffer.append(line)
        depth = _calculate_block_depth(buffer)
        prompt = "... " if depth > 0 else ">>> "

        # Execute when block is closed and user entered an empty line
        if depth == 0 and stripped == '':
            code = "\n".join(buffer).strip()
            buffer = []
            if not code:
                continue

            # Validate each line before execution
            has_error = False
            for i, code_line in enumerate(code.split('\n'), 1):
                is_valid, error_msg = validate_line(code_line)
                if not is_valid:
                    print(f"Error (line {i}): {error_msg}", file=sys.stderr)
                    has_error = True

            if has_error:
                continue

            try:
                interp.run_snippet(code)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

