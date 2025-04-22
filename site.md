title: BFScript

---

#description

BFScript is a compiler written in Python that translates a familiar, C-inspired syntax into notoriously minimalistic Brainfuck code. It aims to make developing complex Brainfuck programs more feasible by providing higher-level abstractions.

#main

# BFScript: Bridging the Gap Between Readability and Brainfuck

## The Idea: What It Is and Why I Built It

Ever since I first encountered esoteric programming languages, Brainfuck stood out. Its extreme minimalism was fascinating, but also intimidating. It's Turing complete, meaning *theoretically* you can compute anything with it, but *practically*, writing or reading anything beyond simple examples is incredibly difficult. The idea of simplifying this process got stuck in my head.

This led me to create BFScript: a compiler that takes code written in a simpler, C-like syntax and translates it into functional Brainfuck code.

My initial attempt was a different project, the [Brainfuck Transpiler](https://github.com/ImGajeed76/brainfuck_transpiler). However, I soon realized that approach had fundamental limitations and wasn't truly Turing complete. It couldn't handle the complexity I envisioned. So, I decided to start over with a more robust compiler approach, which became BFScript.

Primarily, this is a passion project born out of curiosity. It's for me, for the fun of tackling a weird challenge, and maybe for anyone else intrigued by the intersection of conventional programming and esoteric languages.

**What is Brainfuck, Anyway?**

Before diving into BFScript, it helps to understand the target language. Brainfuck uses only eight simple commands to manipulate a tape of memory cells:

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

A simple "Hello World!" in Brainfuck looks like this:

```bf
++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.
```

As you can see, readability isn't its strong suit. BFScript aims to fix that!

## The Journey: From Concept to Reality

After hitting the limits with the simple transpiler, I knew I needed a more structured approach for BFScript. I decided to build a proper compiler using Python.

The key technology choices were:

1.  **Python:** I chose Python because I'm comfortable with it, and it has excellent string manipulation capabilities and libraries, which are crucial for code generation. Its readability also helps manage the compiler's complexity.
2.  **Lark (Parsing Library):** Instead of writing a parser from scratch, I used Lark. It allows defining the grammar of the BFScript language in a clean way and automatically generates a parser that turns BFScript code into a structured tree (Abstract Syntax Tree - AST). This saved a massive amount of effort and let me focus on the harder part: translation.

The compilation process generally involves:

1.  **Parsing:** Lark reads the BFScript code (`.bfs` file) and validates its syntax, creating an AST.
2.  **Code Generation:** My Python code walks through this AST. For each node (like a variable declaration, `while` loop, `output` call), it generates the corresponding sequence of Brainfuck commands. This involves figuring out how to manage Brainfuck's memory tape to represent variables and control flow.

The BFScript language itself evolved to include features essential for non-trivial programs:

*   Variables (`size_t name = value;`)
*   Arithmetic (`+`, `-`)
*   Loops (`while (condition) { ... }`)
*   Basic I/O (`output('A');`, `output(variable);`)

Here's an example of BFScript code that prints a pyramid, showcasing its readability compared to raw Brainfuck:

```c
// --- Pyramid Printer ---
// Prints a pyramid of '*' characters using nested loops.

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
```

This is much easier to understand and maintain!

## Navigating Challenges: Hurdles and Solutions

This project was definitely challenging, pushing me to learn quite a bit.

*   **Technical Challenges:**
    *   **Brainfuck Logic:** The biggest hurdle was figuring out *how* to translate higher-level concepts into Brainfuck. How do you represent variables on the tape? How do you implement `while` loops or arithmetic efficiently using only `+`, `-`, `<`, `>`, `[`, `]`? This required studying Brainfuck programming techniques and designing specific Brainfuck "subroutines" for common operations. Managing the data pointer (`<`, `>`) effectively to avoid unnecessary movement was also tricky.
    *   **Compiler Complexity:** Designing the compiler structure itself, ensuring the generated Brainfuck code was correct for all language features and their combinations, was complex. Debugging the *output* Brainfuck code was particularly difficult, as Brainfuck gives you very little feedback when something goes wrong.
*   **Non-Technical Challenges:** Mostly time management and staying motivated on a project that's complex and doesn't have an immediate practical application outside of the learning experience itself.

*   **Solutions:**
    *   I tackled the Brainfuck logic by breaking problems down. I'd figure out how to implement a small piece (like adding two numbers stored at specific tape locations) and then build upon that.
    *   Using the Lark library significantly simplified the parsing stage, letting me focus on the translation logic.
    *   Lots of trial-and-error, testing small BFScript snippets, and examining the generated Brainfuck code helped iron out bugs.

## The Outcome: Where It Stands and What I Learned

BFScript is currently functional and usable. You can write programs like the pyramid example above and compile them into working Brainfuck code. While there's always room for improvement and more features, I'm happy with its current state as a proof-of-concept and a learning tool.

*   **Goals Achieved:** Yes, the main goal of creating a compiler that translates a C-like syntax into Turing-complete Brainfuck, overcoming the limitations of my previous transpiler, was met.
*   **Key Learnings:**
    *   A *lot* about compiler fundamentals (parsing, ASTs, code generation).
    *   Deep appreciation for the challenges of working in highly constrained environments like Brainfuck.
    *   How to map high-level programming constructs to low-level operations.
    *   The value of using good tools and libraries (like Lark).
    *   Problem-solving and debugging techniques for unconventional code.
*   **Proudest Aspect:** Getting variables and control flow (especially nested loops) working correctly was a major milestone. Seeing a readable BFScript program compile and run as intended in a Brainfuck interpreter is really satisfying.
*   **Future Ideas:** While not actively planned, I've considered exploring optimizations for the generated Brainfuck code (making it shorter or faster). The idea of using LLVM Intermediate Representation (IR) as a source, allowing potentially *any* language that compiles to LLVM to be compiled to Brainfuck, is also an interesting, though very ambitious, future thought experiment.
