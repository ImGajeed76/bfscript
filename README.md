# BrainfuckScript 🧠💻➡️🤯

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

**Compile a C-like language directly into Brainfuck!**

BrainfuckScript is a compiler written in Python that translates a more familiar, C-inspired syntax into notoriously
minimalistic Brainfuck code. It aims to make developing complex Brainfuck programs feasible by providing higher-level
abstractions like variables, loops, and conditional statements.

This project uses a 32-bit cell architecture for the target Brainfuck environment, allowing for larger numerical values
compared to the traditional 8-bit model.

## 🤔 What is Brainfuck?

Before diving into BrainfuckScript, it helps to understand what it compiles *to*. Brainfuck is an esoteric programming
language known for its extreme minimalism. It consists of only eight commands:

| Command | Description                        |
|:--------|:-----------------------------------|
| `>`     | Increment the data pointer.        |
| `<`     | Decrement the data pointer.        |
| `+`     | Increment the byte at the pointer. |
| `-`     | Decrement the byte at the pointer. |
| `.`     | Output the byte at the pointer.    |
| `,`     | Input a byte to the pointer.       |
| `[`     | Jump forward if byte is zero.      |
| `]`     | Jump backward if byte is non-zero. |

A simple "Hello World!" program in Brainfuck looks something like this:

```bf
++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.
```

As you can see, writing anything non-trivial directly in Brainfuck is a significant challenge. BrainfuckScript bridges
this gap!

## ✨ Key Features

* **C-like Syntax:** Write code using familiar constructs like variables (`size_t`), `if`/`else`, `while` loops, and
  basic arithmetic.
* **Brainfuck Compilation:** Generates functional Brainfuck code as output.
* **32-Bit Cells:** Targets a Brainfuck environment with 32-bit cells, enabling larger numbers.
* **Python Implementation:** Built with modern Python (>=3.13) and Poetry.
* **Lark Parser:** Uses the Lark library for robust parsing based on a defined grammar.
* **Included Interpreter:** Comes with a basic Brainfuck interpreter (also using 32-bit cells) to run the compiled code.

## 🚀 Getting Started

### Prerequisites

* **Python:** Version 3.13 or higher.
* **Poetry:** A Python dependency management tool. ([Installation Guide](https://python-poetry.org/docs/#installation))

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ImGajeed76/bfscript.git
   ```
2. **Navigate to the project directory:**
   ```bash
   cd bfscript
   ```
3. **Install dependencies using Poetry:**
   ```bash
   poetry install
   ```

## 🛠️ Usage

### Compiling BrainfuckScript (`.bfs`) to Brainfuck (`.bf`)

Use the `compiler.py` script to translate your BrainfuckScript code:

```bash
poetry run python compiler.py <input_file.bfs> <output_file.bf>
```

**Example:**

```bash
poetry run python compiler.py examples/pyramid.bfs pyramid.bf
```

This will read the code in `examples/pyramid.bfs` and write the compiled Brainfuck code to `pyramid.bf`.

### Running Compiled Brainfuck Code (`.bf`)

Use the included `interpreter.py` to execute the generated Brainfuck code:

```bash
poetry run python interpreter.py <brainfuck_file.bf>
```

**Example:**

```bash
poetry run python interpreter.py pyramid.bf
```

This will run the Brainfuck code stored in `pyramid.bf`.

**With Input:**

If your Brainfuck code requires input, you can provide it like this:

```bash
poetry run python interpreter.py pyramid.bf "Some input"
```

**Other Options:**

```bash
poetry run python interpreter.py your_script.bf "Input" -m 60000 -b 8 -t 10.0
```

| Option | Description                                 |
|:-------|:--------------------------------------------|
| `-m`   | Set the memory size (default: 30000 cells). |
| `-b`   | Set the cell size in bits (default: 32).    |
| `-t`   | Set the timeout in seconds (default: 5.0).  |

## 📝 Syntax Example

BrainfuckScript uses a syntax reminiscent of C. Here's an example that prints a pyramid pattern:

```c
// --- Pyramid Printer ---
// Prints a pyramid of '*' characters using nested loops.
// Avoids multiplication by incrementing the character count per row.

size_t height = 7; // Declare and initialize a variable

size_t current_row = 1;
size_t chars_for_this_row = 1;

// Loop for each row
while (current_row <= height) {

    // --- Print leading spaces ---
    size_t spaces_needed = height - current_row;
    size_t spaces_printed = 0;

    while (spaces_printed < spaces_needed) {
        output(' '); // Output a character literal
        spaces_printed = spaces_printed + 1;
    }

    // --- Print the characters ('*') ---
    size_t chars_printed = 0;
    while (chars_printed < chars_for_this_row) {
        output('*');
        chars_printed = chars_printed + 1;
    }

    // --- Print a newline character ---
    output('\n');

    // --- Prepare for the next row ---
    current_row = current_row + 1;
    // Add 2 characters for the next row (1 -> 3 -> 5 -> ...)
    chars_for_this_row = chars_for_this_row + 2;
}

// No explicit return needed for top-level code
```

## 🚧 Current Status & Limitations

This project is currently under development. The following features are **not yet implemented**:

* ❌ **Variable Multiplication (`*`)**: Multiplication involving two variables is not supported. Constant folding works (
  e.g., `5 * 2`).
* ❌ **Variable Division (`/`)**: Division involving two variables is not supported. Constant folding works (e.g.,
  `10 / 2`).
* ❌ **Functions**: Defining and calling custom functions (`void myFunc() { ... }`) is not yet implemented.
* ❌ **Stacks**: The `stack` data type and its associated operations (`.push()`, `.pop()`, `.peek()`) are not yet
  implemented.

These features are planned for future development!

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check
the [issues page](https://github.com/ImGajeed76/bfscript/issues). Please open an issue first to discuss what you would
like to change.

## 📜 License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for details.

---

Happy Brainfucking (the easier way)! 🎉