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

Primarily, this is a passion project exploring compiler design in a severely constrained environment—how do you build a usable language when your target has no stack, no registers, and only 8 instructions? It's for me, for the fun of tackling a weird challenge, and maybe for anyone else intrigued by the intersection of conventional programming and esoteric languages.

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

## How It Actually Works: The Technical Bits

Okay, so the interesting part isn't just *that* it compiles to Brainfuck—it's *how*. I had to solve some genuinely tricky problems to make this work, and honestly, I'm pretty proud of the solutions I came up with.

### The Code Generation Pattern: Functions All The Way Down

Here's the thing I figured out early on: I couldn't just immediately spit out Brainfuck strings as I walked the AST. Why? Because when you're parsing something like `a + b`, you don't yet know *where* the result needs to go. Maybe it's going into a variable. Maybe it's being output directly. Maybe it's part of a bigger expression like `(a + b) * c`.

So instead, I built a system where every expression returns a Python function—a `code_func`—that generates the actual Brainfuck code when you call it:

```python
def code_func(result_cell):
    c = []
    # Generate BF instructions that put the result in result_cell
    return c
```

This `result_cell` parameter is the key. It lets me decide *later* where the result should end up. When I finally know the context (like "store this in variable X"), I call the function and pass in the destination cell.

For something like `a + b * c`, these functions nest naturally:
1. Parse `b * c` → get back a `code_func_mult`
2. Parse `a + ...` → create a new `code_func_add` that *calls* `code_func_mult` internally
3. When I finally execute this chain, it recursively generates the right BF code in the right order

I later found out this is similar to something called "tagless final" from programming language research, which was kind of validating—I'd reinvented a real technique without knowing it existed.

### Memory Management: Keeping Track of the Tape

Brainfuck's tape is your only storage. No stack, no heap, just cells stretching out in both directions. I needed a way to manage this sanely.

Variables get permanent locations—each `size_t` gets assigned a specific cell number and stays there. But temporary calculations (like the intermediate result of `b * c` in `a + b * c`) need *temporary* cells that get cleaned up after use.

I built a `MemoryManager` class with a pool of temp cells (0–19 by default):

```python
class MemoryManager:
    def get_temp_cell(self):
        if not self.temp_cell_pool:
            raise MemoryError("Out of temporary cells!")
        return self.temp_cell_pool.pop(0)
    
    def release_temp_cell(self, cell):
        self.temp_cell_pool.insert(0, cell)  # LIFO reuse
```

The LIFO (last-in-first-out) reuse pattern is intentional—recently freed cells get reused first, which keeps the data pointer from wandering all over the tape. It's basically register allocation for a tape machine.

If you run out of temp cells, the compiler throws an error instead of silently corrupting memory. Better to fail loudly than generate broken code.

### Control Flow: Making Loops and Ifs Work

This was the hardest part. Brainfuck only has `[...]` (loop while cell ≠ 0). No `if`/`else`, no `break`, no labels you can jump to. And every operation can move the data pointer, so if you're not careful, you'll end up in the wrong place and everything breaks.

My solution was to build abstractions that enforce pointer discipline. For example, here's `loop_managed`:

```python
def loop_managed(self, condition_cell, loop_func):
    code = self.move_to_cell(condition_cell)
    code += self.open_brace()  # [
    code += loop_func()  # Execute the loop body (might move pointer)
    code += self.move_to_cell(condition_cell)  # Force pointer back
    code += self.close_brace()  # ]
    return code
```

The key insight: after the loop body runs, *explicitly* move the pointer back to the condition cell. This prevents pointer drift bugs where the loop breaks because you're checking the wrong cell.

For `if/else`, it's trickier. I copy the condition to a temp cell, then use `[...]` to run the if-branch. For the else-branch, I set a flag beforehand and clear it if the if-branch runs—then I use another `[...]` to check if the flag is still set. It's hacky but it works.

### Comparisons: The Countdown Algorithm

You can't just check if `a > b` in Brainfuck. No comparison instructions exist. So I had to get creative.

My solution for `greater_than`:
1. Copy `a` and `b` to temporary cells (let's call them `temp1` and `temp2`)
2. Loop: decrement both `temp1` and `temp2` by 1 each iteration
3. If `temp2` hits zero first, then `a > b` (set result to 1)
4. If `temp1` hits zero first or they hit zero together, then `a ≤ b` (result stays 0)

It's essentially simulating a comparison by counting down both numbers in parallel and seeing which runs out first. Not the most efficient algorithm, but it works and it's provably correct.

Similar logic applies to `<`, `==`, etc. Each comparison has its own little algorithm.

### Why This Matters

I didn't find tutorials for any of this. The problem space—compiling a C-like language to Brainfuck with complex expressions and control flow—basically doesn't exist elsewhere. These patterns emerged from trial and error, trying to keep the compiler maintainable as I added features.

The closure-based approach especially felt like a breakthrough moment. It made composition natural, prevented a ton of bugs, and kept the code surprisingly clean considering what it's doing.

## Navigating Challenges: Hurdles and Solutions

This project was definitely challenging, pushing me to learn quite a bit.

*   **Technical Challenges:**
    *   **Brainfuck Logic:** The biggest hurdle was figuring out *how* to translate higher-level concepts into Brainfuck. How do you represent variables on the tape? How do you implement `while` loops or arithmetic efficiently using only `+`, `-`, `<`, `>`, `[`, `]`? This required studying Brainfuck programming techniques and designing specific Brainfuck "subroutines" for common operations. Managing the data pointer (`<`, `>`) effectively to avoid unnecessary movement was also tricky.
    *   **Compiler Complexity:** Designing the compiler structure itself, ensuring the generated Brainfuck code was correct for all language features and their combinations, was complex. Debugging the *output* Brainfuck code was particularly difficult, as Brainfuck gives you very little feedback when something goes wrong.
    *   **AI Wasn't Much Help:** I tried using AI assistants early on, but this problem is niche enough that they couldn't really guide me. There's no big corpus of "C-to-Brainfuck compiler" code for them to learn from. This forced me to think through the logic myself, which honestly made the learning experience better.
*   **Non-Technical Challenges:** Mostly time management and staying motivated on a project that's complex and doesn't have an immediate practical application outside of the learning experience itself.

*   **Solutions:**
    *   I tackled the Brainfuck logic by breaking problems down. I'd figure out how to implement a small piece (like adding two numbers stored at specific tape locations) and then build upon that.
    *   Using the Lark library significantly simplified the parsing stage, letting me focus on the translation logic.
    *   Lots of trial-and-error, testing small BFScript snippets, and examining the generated Brainfuck code helped iron out bugs.

## The Outcome: Where It Stands and What I Learned

BFScript is currently functional and usable. You can write programs like the pyramid example above and compile them into working Brainfuck code. While there's always room for improvement and more features (some edge cases in conditionals are still buggy, and I'm not going back to debug that nightmare), I'm happy with its current state as a proof-of-concept and a learning tool.

*   **Goals Achieved:** Yes, the main goal of creating a compiler that translates a C-like syntax into Turing-complete Brainfuck, overcoming the limitations of my previous transpiler, was met.
*   **Key Learnings:**
    *   A *lot* about compiler fundamentals (parsing, ASTs, code generation).
    *   Deep appreciation for the challenges of working in highly constrained environments like Brainfuck.
    *   How to map high-level programming constructs to low-level operations.
    *   The value of using good tools and libraries (like Lark).
    *   Problem-solving and debugging techniques for unconventional code.
    *   That I could design compiler patterns independently that turn out to mirror real academic research.
*   **Proudest Aspect:** Honestly, the closure-based code generation system. It emerged organically as I tried to handle nested expressions, and realizing later that it's similar to patterns from academic PL research (tagless final) was really validating. That "independent discovery" moment felt great.
*   **Future Ideas:** While not actively planned, I've considered exploring optimizations for the generated Brainfuck code (making it shorter or faster—there's definitely redundant `+-<>` sequences I could collapse). The idea of using LLVM Intermediate Representation (IR) as a source, allowing potentially *any* language that compiles to LLVM to be compiled to Brainfuck, is also an interesting, though very ambitious, future thought experiment.
