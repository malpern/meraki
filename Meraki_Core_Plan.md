# Meraki Configuration Tooling Plan

## Background

### Origins and Design Goals
Meraki was conceived by [Åsmund Vikane](https://github.com/koekeishiya), the creator of several influential macOS tools including skhd (Simple Hotkey Daemon), yabai (window manager), and khd (keyboard hotkey daemon). In 2023, Åsmund released a [sample configuration file](https://github.com/koekeishiya/meraki/blob/master/examples/merakirc) showcasing his vision for Meraki - a more powerful and intuitive keyboard configuration language.

Åsmund's design goals for Meraki included:
- A clean, readable syntax inspired by skhd's simplicity
- Support for advanced features like leader keys and deep keybinding chains
- Seamless integration with his other tools (yabai, etc.)
- A more expressive configuration language for complex keyboard customization

While Åsmund released the sample configuration to demonstrate these concepts, the actual implementation of Meraki hasn't been released. This project aims to bring Meraki into existence, though with a different technical approach than originally envisioned.

### Implementation Strategy
The original skhd engine, while powerful, doesn't support some of Meraki's key features like:
- Leader key timeouts
- Deep keybinding chains
- Complex modifier combinations
- State-based key handling

Instead of building on skhd, we'll implement Meraki by leveraging Karabiner Elements - macOS's most powerful keyboard customization engine. However, rather than working directly with Karabiner's complex JSON format, we'll use [Max Stoiber's](https://github.com/mxstbr) TypeScript DSL ([karabiner.ts](https://github.com/mxstbr/karabiner.ts)).

Max created karabiner.ts to solve several key problems with Karabiner Elements:
- Replace error-prone JSON configuration with type-safe TypeScript
- Enable hierarchical organization of keybindings
- Provide a scalable framework for complex modifications
- Add proper IDE support and validation

### Our Implementation Pipeline
This project creates a complete toolchain to:
1. Parse Meraki's human-friendly syntax into an AST
2. Validate and lint the configuration
3. Transform it into Max's TypeScript DSL
4. Leverage karabiner.ts to generate Karabiner Elements JSON

### References
- [Meraki Sample Config](https://github.com/koekeishiya/meraki/blob/master/examples/merakirc) - Åsmund Vikane's original design
- [karabiner.ts](https://github.com/mxstbr/karabiner.ts) - Max Stoiber's TypeScript DSL
- [skhd](https://github.com/koekeishiya/skhd) - Åsmund's Simple Hotkey Daemon
- [Karabiner Elements](https://karabiner-elements.pqrs.org/) - The underlying keyboard customization engine
- ["Type-safe keyboard shortcuts on macOS"](https://www.youtube.com/watch?v=uaJSjgVEhMQ) - Max's video on karabiner.ts

## Analyzed Features from Meraki Config File

### Sample Config File
```ini
# Define modifiers
mod1 = lcmd + lalt
mod2 = lshift + lctrl

# Basic application launching
mod1 - m : open -a Mail.app
mod1 - s : open -a "Sublime Text"

# Leader key with default timeout (500ms)
mod1 - l : {
    h : open -a Safari;     # Web browser
    t : open -a Terminal;   # Terminal emulator
    c : open -a Calendar;   # Calendar app
}

# Leader key with custom timeout
mod1 - w [750ms] : {
    f : open -a Finder;
    s : open -a "System Settings";
}

# Application focus
mod1 - j : focus --app "IntelliJ IDEA"
mod1 - k : focus --app "kitty"
```

### Current Features (v0.1):
1. **Modifiers**: 
   - Basic modifiers (`mod1`, `mod2`)
   - Support for standard modifiers (cmd, alt, shift, ctrl)
   - Compound modifiers (e.g., `mod2 + shift`)
   - Modifier-only keybinds with activation flags:
     ```ini
     cmd ~down: show_app_switcher
     cmd ~up:   hide_app_switcher
     ```
   - Activation flags (`~down`, `~up`, `~repeat`)
   - Activation thresholds for modifiers

2. **Basic Keybindings**:
   - Simple key mapping (`mod1 - m`)
   - Application launching (`open -a`)
   - Application focus (`focus --app`)

3. **Core Syntax**:
   - Leader keys with braces (`{}`)
   - Default timeout (500ms)
   - Optional custom timeout (`[Xms]`)
   - Group syntax for similar commands:
     ```ini
     # App launching with groups
     mod1 + { c, f, m } :
         open -a { "Chrome", "Finder", "Mail" }
     ```
   - Command expansion with groups
   - Multi-line commands with custom end markers
   - Chain syntax for command sequences

4. **Comments**:
   - Line comments (`# comment`)
   - Inline comments (`command  # comment`)
   - Multi-line notes with `@END` markers:
     ```ini
     @END This is a multi-line note
     that describes the following
     keybinding in detail. END
     ```

### Future Features (v0.2+):

1. **Window Management** (via yabai):
   ```ini
   # Window focus and movement
   mod1 + { h, j, k, l }:
       yabai -m window --focus { west, south, north, east }
   ```
   - Integration with window managers (yabai, Amethyst, Rectangle)
   - Window focus, resize, and movement commands
   - Space management commands

2. **Mouse Integration**:
   ```ini
   # Window dragging operations
   mod1 + mb1 ~down : yabai -m window --drag move.begin
   mod1 + mb1 ~up   : yabai -m window --drag move.end
   ```
   - Mouse button support (`mb1`, `mb2`)
   - Mouse + keyboard combinations
   - Mouse button activation flags

### Feature Coverage Analysis (vs Official merakirc):

1. **Supported in v0.1**:
   - ✅ Basic modifier definitions (`modwe1 = lcmd + lalt`)
   - ✅ Standard modifier support (`cmd`, `alt`, `ctrl`, `shift`)
   - ✅ Basic keybindings with modifiers
   - ✅ Application launching and focus
   - ✅ Group syntax and command expansion
   - ✅ Activation flags (`~down`, `~up`, `~repeat`)
   - ✅ Multi-line commands with end markers
   - ✅ Chain syntax for command sequences
   - ✅ Modifier-only keybinds
   - ✅ Comments and notes

2. **Planned for v0.2**:
   - 🔄 Window manager integration (yabai)
   - 🔄 Space management commands
   - 🔄 Mouse button support
   - 🔄 Window dragging operations

## Development Plan

### Phase 1: Parsing (Current Phase)
// ... existing Phase 1 content ...

### Phase 2: Validation (Partially Started)
// ... existing Phase 2 content ...

### Phase 3: Linting (Not Started)
// ... existing Phase 3 content ...

### Phase 4: Formatting (Partially Started)
// ... existing Phase 4 content ...

### Phase 5: Compilation (Not Started)
// ... existing Phase 5 content ...

### Phase 6: Tooling (Not Started)
// ... existing Phase 6 content ...

## Development History
```
Phase 1 (Current) ─────┐
                      │
Phase 2 (Started) ────┤
                      │
Phase 3              ─┤
                      ├─── v0.1 Release
Phase 4 (Started) ────┤     Core Features
                      │
Phase 5              ─┤
                      │
Phase 6              ─┘

Future Phases ────────┐
                      ├─── v0.2 Release
Window Management ────┤     Window Features
                      │
Mouse Support ───────┘
```

## Unit Testing Plan

### Current Test Coverage:
#### Parser Tests (Implemented):
- ✅ Basic modifier definitions
- ✅ Basic keybindings with actions
- ✅ Comment preservation
- ✅ Timeout support for leader keys
- ✅ Nested bindings with arbitrary depth
- ✅ Complex configurations with multiple features

#### Remaining Test Cases:
1. **Parser**:
   - Error handling and recovery
   - Edge cases in syntax
   - Performance with large configs

2. **Compiler**:
   - Basic compilation cases
   - Comment preservation
   - Dry-run output

## Final Deliverables
1. **Core Python Scripts**:
   - `meraki_parser.py`
   - `meraki_linter.py`
   - `meraki_formatter.py`
   - `meraki_compiler.py`

2. **CLI Tool**:
   - A unified command-line interface for parsing, linting, formatting, and compiling.

3. **VSCode Plugin**:
   - Full support for `.meraki` files with syntax highlighting, linting, and auto-formatting.

## Toolchain Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Meraki Config  │     │  TypeScript DSL  │     │  Karabiner JSON    │
│  (.meraki)      │     │  (.ts)           │     │  (.json)           │
└────────┬────────┘     └────────┬─────────┘     └────────┬───────────┘
         │                       │                         │
         ▼                       ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Meraki Tooling  │     │   karabiner.ts   │     │ Karabiner Elements │
├─────────────────┤     ├──────────────────┤     ├────────────────────┤
│ • Parser        │ ──► │ • Type Checking  │ ──► │ • Complex Mods     │
│ • Validator     │     │ • DSL Compiler   │     │ • Simple Mods      │
│ • Linter        │     │ • JSON Generator │     │ • Profiles         │
│ • Formatter     │     └──────────────────┘     └────────────────────┘
│ • VS Code Ext   │
└─────────────────┘
     ▲      ▲
     │      │
┌────┴──────┴────┐
│  Development   │
│  Tools         │
├────────────────┤
│ • Auto Format  │
│ • Syntax Check │
│ • Completions  │
│ • Diagnostics  │
└────────────────┘
```

The toolchain architecture shows how our development tools will support the entire workflow, from editing Meraki configs through to generating the final Karabiner Elements configuration. 