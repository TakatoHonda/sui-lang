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
    from sui import SuiInterpreter

    print("Sui REPL (空行で実行、.exit / .quit / .reset)")
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
            print("状態をリセットしました。")
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
            try:
                interp.run_snippet(code)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)

