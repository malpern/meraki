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

As demonstrated in his [YouTube video](https://www.youtube.com/watch?v=uaJSjgVEhMQ), Max's DSL transforms verbose Karabiner JSON:
```json
{
  "type": "basic",
  "from": { "key_code": "j", "modifiers": { "mandatory": ["command"] } },
  "to": [{ "shell_command": "open -a 'IntelliJ IDEA'" }]
}
```
Into clean, maintainable TypeScript:
```typescript
map('j').withModifiers('command').to(shell('open -a "IntelliJ IDEA"'))
```

### Our Implementation Pipeline
This project creates a complete toolchain to:
1. Parse Meraki's human-friendly syntax into an AST
2. Validate and lint the configuration
3. Transform it into Max's TypeScript DSL
4. Leverage karabiner.ts to generate Karabiner Elements JSON

Example of the full pipeline:
```ini
# Original Meraki config (Åsmund's syntax)
mod1 - l : {
    t : open -a Terminal;
    f : open -a Finder;
}

↓ (our parser + compiler)

// Generated TypeScript using Max's DSL
layer('apps', 'l')
  .withModifiers(mod1)
  .map('t', shell('open -a Terminal'))
  .map('f', shell('open -a Finder'))

↓ (karabiner.ts)

// Final Karabiner Elements JSON
{
  "type": "basic",
  "from": { "key_code": "l", "modifiers": { "mandatory": ["command", "option"] } },
  "to": [{ "set_variable": { "name": "apps", "value": 1 } }],
  "conditions": [{ "type": "variable_if", "name": "apps", "value": 1 }]
  // ... additional generated JSON for the layer implementation
}
```

### References
- [Meraki Sample Config](https://github.com/koekeishiya/meraki/blob/master/examples/merakirc) - Åsmund Vikane's original design
- [karabiner.ts](https://github.com/mxstbr/karabiner.ts) - Max Stoiber's TypeScript DSL
- [skhd](https://github.com/koekeishiya/skhd) - Åsmund's Simple Hotkey Daemon
- [Karabiner Elements](https://karabiner-elements.pqrs.org/) - The underlying keyboard customization engine
- ["Type-safe keyboard shortcuts on macOS"](https://www.youtube.com/watch?v=uaJSjgVEhMQ) - Max's video on karabiner.ts

---

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
   - ✅ Basic modifier definitions (`mod1 = lcmd + lalt`)
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

This analysis confirms that we've either included or explicitly planned for all features demonstrated in the official merakirc example.

---

## Development Plan

### Phase 1: Parsing (Current Phase)
#### Goal:
Build a parser to read Meraki config files and output an AST.

#### Implementation Status:
- ✅ Basic parser implemented using `pyparsing`
- ✅ Support for modifier definitions with comments
- ✅ Basic keybinding parsing
- ✅ Nested binding support with arbitrary depth
- ✅ Timeout support for leader keys (e.g., `[500ms]`)
- ✅ Comment preservation in AST
- ✅ Group syntax for similar commands
- ✅ Activation flags (`~down`, `~up`, `~repeat`)
- ✅ Initial test suite with core functionality

#### In Progress:
- 🔄 Compound modifiers (e.g., `mod2 + shift`)
- 🔄 Special key names (directional, function keys, etc.)
- 🔄 Command chaining with semicolon separator
- 🔄 Command arguments with quotes
- 🔄 Command flags and parameters
- 🔄 Relative values in commands
- 🔄 Multi-line comment support
- 🔄 Expanded test coverage for new features

#### Next Steps:
1. Complete implementation of remaining parser features
2. Add source position tracking for better error reporting
3. Implement error recovery for malformed input
4. Add validation for modifier references
5. Complete test coverage for all features

#### Deliverables:
1. **Parser Implementation** (`meraki_parser.py`):
   - Complete grammar definition
   - AST generator
   - Error recovery system
   - Source position tracking

2. **Test Suite** (`test_meraki_parser.py`):
   - Unit tests for all features
   - Error case coverage
   - Performance tests for large configs

3. **Documentation**:
   - Grammar specification
   - AST format reference
   - Error message catalog

#### AST Structure:
```json
{
  "modifiers": {
    "mod1": {
      "keys": ["lcmd", "lalt"],
      "comments": ["# Main modifier for app switching"],
      "line_number": 1
    },
    "mod2 + shift": {
      "keys": ["lshift", "lctrl", "shift"],
      "comments": [],
      "line_number": 2
    }
  },
  "keybindings": [
    {
      "key_combination": "mod1",
      "key": "l",
      "timeout": 500,  // Default timeout
      "nested_bindings": {
        "h": {
          "action": "open -a Safari",
          "nested_bindings": null,
          "comments": ["# Web browser"],
          "line_number": 4
        }
      },
      "comments": [],
      "line_number": 3
    },
    {
      "key_combination": "mod1",
      "key": "w",
      "timeout": 750,  // Custom timeout
      "nested_bindings": {
        "f": {
          "action": "window --focus full",
          "nested_bindings": null,
          "comments": [],
          "line_number": 6
        }
      },
      "comments": [],
      "line_number": 5
    },
    {
      "key_combination": "mod2",
      "key": "left",
      "action": "window --focus west",
      "args": {
        "focus": "west"
      },
      "activation_flags": ["down"],
      "comments": [],
      "line_number": 7
    },
    {
      "key_combination": "mod1",
      "key": "x",
      "actions": [  // Multiple actions in sequence
        {
          "command": "window --focus east",
          "args": {
            "focus": "east"
          }
        },
        {
          "command": "window --resize right:+100",
          "args": {
            "resize": "right:+100"
          }
        }
      ],
      "comments": ["# Resize and focus"],
      "line_number": 8
    },
    {
      "key_combination": "mod1",
      "key": "a",
      "group_syntax": {  // Group expansion
        "keys": ["c", "f", "m"],
        "commands": [
          "open -a Chrome",
          "open -a Finder",
          "open -a Mail"
        ]
      },
      "comments": ["# App launcher group"],
      "line_number": 9
    }
  ]
}
```

The AST structure captures:
1. **Modifiers**:
   - Basic and compound modifiers
   - Source comments and line numbers
   - Original key combinations

2. **Keybindings**:
   - Simple and nested bindings
   - Timeouts (default and custom)
   - Action sequences
   - Group syntax expansions
   - Activation flags
   - Command arguments
   - Source tracking

3. **Comments and Metadata**:
   - Line comments
   - Inline comments
   - Source positions
   - Original formatting

This structure serves as the contract between the parser and later phases, ensuring all Meraki features are properly represented.

#### Example Input:
```ini
# Define modifiers
mod1 = lcmd + lalt  # Main modifier for app switching
mod2 + shift = lshift + lctrl + shift  # Extended modifier

# App launching with timeout
mod1 - l [500ms] : {
    h : open -a Safari;  # Web browser
    t : open -a Terminal;  # Terminal
    c : open -a "Visual Studio Code";  # Editor
}

# Direct app launch
mod1 - m : open -a Mail  # Email client

# Multiple apps in sequence
mod1 - x : open -a Slack; open -a Discord  # Communication apps

# Group syntax for related apps
mod1 - d : {  # Development tools
    c : open -a Chrome;
    p : open -a "PyCharm CE";
    i : open -a iTerm;
}
```

#### Example AST Output:
```json
{
  "modifiers": {
    "mod1": {
      "keys": ["lcmd", "lalt"],
      "comments": ["# Main modifier for app switching"],
      "line_number": 1
    },
    "mod2 + shift": {
      "keys": ["lshift", "lctrl", "shift"],
      "comments": ["# Extended modifier"],
      "line_number": 2
    }
  },
  "keybindings": [
    {
      "key_combination": "mod1",
      "key": "l",
      "timeout": 500,
      "nested_bindings": {
        "h": {
          "action": "open -a Safari",
          "nested_bindings": null,
          "comments": ["# Web browser"],
          "line_number": 4
        },
        "t": {
          "action": "open -a Terminal",
          "nested_bindings": null,
          "comments": ["# Terminal"],
          "line_number": 5
        },
        "c": {
          "action": "open -a \"Visual Studio Code\"",
          "nested_bindings": null,
          "comments": ["# Editor"],
          "line_number": 6
        }
      },
      "comments": [],
      "line_number": 3
    },
    {
      "key_combination": "mod1",
      "key": "m",
      "action": "open -a Mail",
      "comments": ["# Email client"],
      "line_number": 7
    },
    {
      "key_combination": "mod1",
      "key": "x",
      "actions": [  // Multiple actions in sequence
        {
          "command": "open -a Slack"
        },
        {
          "command": "open -a Discord"
        }
      ],
      "comments": ["# Communication apps"],
      "line_number": 8
    },
    {
      "key_combination": "mod1",
      "key": "d",
      "group_syntax": {  // Group expansion
        "keys": ["c", "p", "i"],
        "commands": [
          "open -a Chrome",
          "open -a \"PyCharm CE\"",
          "open -a iTerm"
        ]
      },
      "comments": ["# Development tools"],
      "line_number": 9
    }
  ]
}
```

### Phase 2: Validation (Partially Started)
#### Goal:
Add validation rules to check the AST for errors and inconsistencies.

#### Implementation Status:
- ✅ Basic validation framework
- ✅ Unused modifier detection
- ✅ Duplicate keybinding detection
- ✅ Initial test suite for validators

#### Pending:
- 🔄 Timeout value validation
- 🔄 Nested binding depth validation
- 🔄 Activation flag combination validation
- 🔄 Command argument validation
- 🔄 Expanded test coverage

#### Example Validation Output:
```
# Error Examples:
Error [Line 5]: Undefined modifier 'mod3' in binding 'mod3 - x'
Error [Line 12]: Duplicate key binding 'mod1 - h'
Error [Line 15]: Invalid timeout value '-200ms'

# Warning Examples:
Warning [Line 1]: Modifier 'mod2' is defined but never used
Warning [Line 8]: Consider grouping similar app launch commands
Warning [Line 20]: Long action chain could be simplified using group syntax

# Validation Summary:
✗ 3 errors found
⚠ 3 warnings found
```

### Phase 3: Linting (Not Started)
#### Goal:
Generate warnings for non-critical issues and provide recommendations to fix them.

#### Deliverables:
- Integrated linting in `meraki_linter.py`
- Style guide enforcement
- Best practice recommendations

#### Example Lint Output:
```
Style [Line 4]: Inconsistent spacing around modifier operator
  Found: 'mod1-x'
  Suggested: 'mod1 - x'

Style [Line 8]: Unaligned colons in block
  Found:
    h: open -a Safari;
    tab:open -a Terminal;
  Suggested:
    h   : open -a Safari;
    tab : open -a Terminal;

Style [Line 12]: Mixed comment styles
  Found: 'mod1 - m : open -a Mail # mail app'
  Suggested: 'mod1 - m : open -a Mail  # mail app'

Hint [Line 15-20]: Consider extracting repeated app launch pattern into a group
```

### Phase 4: Formatting (Partially Started)
#### Goal:
Auto-format config files for consistent styling.

#### Implementation Status:
- ✅ Basic formatting framework
- ✅ Modifier definition formatting
- ✅ Basic keybinding formatting
- ✅ Comment alignment
- ✅ Initial test suite for formatters

#### Pending:
- 🔄 Group syntax formatting
- 🔄 Nested block indentation
- 🔄 Activation flag formatting
- 🔄 Command chain formatting
- 🔄 Expanded test coverage

#### Example Formatting:
```ini
# Input:
mod1=lcmd+lalt
mod1-l:{h:open -a Safari;t:open -a Terminal;}

# Output:
mod1 = lcmd + lalt  # Main modifier

mod1 - l : {
    h : open -a Safari;   # Browser
    t : open -a Terminal; # Terminal
}
```

### Phase 5: Compilation (Not Started)
#### Goal:
Compile the validated AST into Max Stoiber's TypeScript DSL, with integration support for external tools.

#### Feature Implementation Categories:
1. **Direct Karabiner Features** (Native Support):
   - Key combinations and modifiers
   - Application-specific bindings
   - Layer system for nested bindings
   - Timeout handling

2. **External Tool Integration** (Requires Additional Setup):
   - **Window Management** (via yabai):
     ```typescript
     // Meraki: mod2 - left : window --focus west
     // Compiles to:
     map('left').withModifiers(mod2)
       .to(shell('/usr/local/bin/yabai -m window --focus west'))

     // Meraki: mod1 - w [750ms] : { f : window --focus full }
     // Compiles to:
     layer('window', 'w').withModifiers(mod1)
       .timeout(750)
       .map('f', shell('/usr/local/bin/yabai -m window --toggle zoom-fullscreen'))
     ```

   - **Space Management** (via yabai):
     ```typescript
     // Meraki: mod2 + shift - n : space --create
     // Compiles to:
     map('n').withModifiers([...mod2, 'shift'])
       .to(shell('/usr/local/bin/yabai -m space --create'))
     ```

   - **Application Focus** (via system commands):
     ```typescript
     // Meraki: mod1 - j : focus --app "IntelliJ IDEA"
     // Compiles to:
     map('j').withModifiers(mod1)
       .to(shell('open -a "IntelliJ IDEA"'))
     ```

#### Configuration and Setup:
1. **Required External Tools**:
   - yabai for window/space management
   - skhd (optional, for additional hotkey support)
   - Any other user-specified tools

2. **Tool Detection and Configuration**:
   ```typescript
   // config.ts
   interface ExternalTools {
     windowManager: 'yabai' | 'amethyst' | 'rectangle' | null;
     hotkeyDaemon: 'skhd' | null;
     customTools: Record<string, string>;  // path to binaries
   }

   const config: ExternalTools = {
     windowManager: 'yabai',
     hotkeyDaemon: null,
     customTools: {
       // Add any additional tools here
     }
   }
   ```

3. **Fallback Behavior**:
   - Warn when commands require unavailable tools
   - Provide setup instructions for missing tools
   - Optional: implement basic fallbacks using native macOS commands

#### Documentation Requirements:
1. **Prerequisites**:
   - List of required external tools
   - Installation and setup instructions
   - Permissions and security requirements

2. **Feature Support Matrix**:
   ```markdown
   | Feature Category | Support Level | Required Tools |
   |-----------------|---------------|----------------|
   | Key Mapping     | Native        | None          |
   | Layers/Timeouts | Native        | None          |
   | Window Mgmt     | External      | yabai         |
   | Space Mgmt      | External      | yabai         |
   | App Launch      | Native        | None          |
   ```

3. **Tool-Specific Guides**:
   - yabai configuration for window management
   - Alternative window managers (Amethyst, Rectangle)
   - Custom tool integration

### Phase 6: Tooling (Not Started)
#### CLI Tool:
- Combine all features into a command-line interface:
  ```bash
  meraki-tool parse config.meraki
  meraki-tool lint config.meraki
  meraki-tool format config.meraki
  meraki-tool compile config.meraki --output config.ts
  ```

#### VSCode Plugin:
- Features:
  - **Basic Syntax Highlighting** using TextMate grammar
  - **Simple Diagnostics** without full LSP implementation
  - **Format on Save** using Python formatter
  - **Preview** compiled Karabiner TypeScript output

## Current Focus
We are currently in Phase 1 (Parsing), with some work started on Phase 2 (Validation) and Phase 4 (Formatting). The immediate priorities are:

1. Complete the parser implementation for remaining features
2. Expand test coverage for new functionality
3. Strengthen validation rules
4. Improve formatting capabilities

#### Deliverables for Current Phase:
1. **Parser**:
   - `meraki_parser.py` with complete feature support
   - Formal grammar definition
   - Comprehensive test suite
   - Example AST output:
     ```json
     {
       "modifiers": {
         "mod1": {
           "keys": ["lcmd", "lalt"],
           "comments": ["# Main modifier"]
         }
       },
       "keybindings": [
         {
           "key_combination": "mod1",
           "key": "l",
           "timeout": 500,
           "nested_bindings": {
             "h": { "action": "open -a Safari" },
             "t": { "action": "open -a Terminal" }
           },
           "comments": ["# App launcher"],
           "line_number": 4
         }
       ]
     }
     ```

2. **Validator**:
   - `meraki_validator.py` with error/warning detection
   - Example validation output:
     ```
     Error: Line 15: Undefined modifier 'mod3'
     Warning: Line 8: Modifier 'mod2' is defined but never used
     ```

3. **Formatter**:
   - `meraki_formatter.py` with consistent styling
   - Example formatting:
     ```ini
     # Input
     mod1=lcmd+lalt
     mod1-l:{h:open -a Safari;t:open -a Terminal;}

     # Output
     mod1 = lcmd + lalt

     mod1 - l : {
         h : open -a Safari;
         t : open -a Terminal;
     }
     ```

## Development Status
| **Phase**           | **Status**     | **Key Deliverables**                    |
|----------------------|----------------|----------------------------------------|
| Parsing              | In Progress    | AST Generator, Grammar Definition       |
| Validation           | Started        | Error Detection, Warning System         |
| Linting              | Not Started    | Style Checker, Best Practices          |
| Formatting           | Started        | Code Formatter, Style Enforcer          |
| Compilation          | Not Started    | TypeScript Generator, Karabiner Output  |
| CLI Tool             | Not Started    | Command Line Interface                  |
| VSCode Plugin        | Not Started    | Syntax Highlighting, Live Preview       |

---

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

---

## Timeline with Testing

| **Phase**           | **Duration**  | **Deliverables**                                   |
|----------------------|---------------|---------------------------------------------------|
| Parsing              | 1 week        | Parser + Unit Tests                               |
| Validation           | 1 week        | Linter + Unit Tests                               |
| Linting              | 1 week        | Linter with Style Rules + Unit Tests             |
| Formatting           | 1 week        | Formatter + Unit Tests                            |
| Compilation          | 2 weeks       | Compiler + Unit Tests                             |
| CLI Tool             | 1 week        | Fully Integrated CLI + End-to-End Tests          |
| VSCode Plugin        | 3 weeks       | Editor Features + Integration Tests              |

---

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

### Transformation Pipeline Example

Here's a real-world example showing how a simple Meraki configuration expands through each stage of transformation:

```ini
# Meraki Configuration (.meraki)
# A simple leader key sequence with timeout for app launching
mod1 - a [500ms] : {
    c : open -a "Chrome";
    f : open -a "Finder";
    t : {
        v : open -a "Visual Studio Code";
        s : open -a "Sublime Text";
    }
}
```

↓ (Parsed and compiled to karabiner.ts)

```typescript
// Max's TypeScript DSL (.ts)
layer('apps', 'a')
  .withModifiers(mod1)
  .timeout(500)
  .map('c', shell('open -a "Chrome"'))
  .map('f', shell('open -a "Finder"'))
  .layer('text_editors', 't')
    .map('v', shell('open -a "Visual Studio Code"'))
    .map('s', shell('open -a "Sublime Text"'))
```

↓ (Compiled to Karabiner Elements)

```json
// Karabiner Elements Complex Modification (.json)
{
  "title": "Meraki App Launcher",
  "rules": [
    {
      "description": "Leader Key: mod1 + a",
      "manipulators": [
        {
          "type": "basic",
          "from": {
            "key_code": "a",
            "modifiers": {
              "mandatory": ["command", "option"]
            }
          },
          "to": [
            {
              "set_variable": {
                "name": "apps_leader",
                "value": 1
              }
            }
          ],
          "parameters": {
            "basic.to_delayed_action_delay_milliseconds": 500
          },
          "to_delayed_action": {
            "to_if_invoked": [
              {
                "set_variable": {
                  "name": "apps_leader",
                  "value": 0
                }
              }
            ]
          }
        },
        {
          "type": "basic",
          "from": {
            "key_code": "c"
          },
          "to": [
            {
              "shell_command": "open -a \"Chrome\""
            }
          ],
          "conditions": [
            {
              "type": "variable_if",
              "name": "apps_leader",
              "value": 1
            }
          ]
        },
        {
          "type": "basic",
          "from": {
            "key_code": "f"
          },
          "to": [
            {
              "shell_command": "open -a \"Finder\""
            }
          ],
          "conditions": [
            {
              "type": "variable_if",
              "name": "apps_leader",
              "value": 1
            }
          ]
        },
        {
          "type": "basic",
          "from": {
            "key_code": "t"
          },
          "to": [
            {
              "set_variable": {
                "name": "text_editors_leader",
                "value": 1
              }
            }
          ],
          "conditions": [
            {
              "type": "variable_if",
              "name": "apps_leader",
              "value": 1
            }
          ]
        },
        {
          "type": "basic",
          "from": {
            "key_code": "v"
          },
          "to": [
            {
              "shell_command": "open -a \"Visual Studio Code\""
            }
          ],
          "conditions": [
            {
              "type": "variable_if",
              "name": "text_editors_leader",
              "value": 1
            }
          ]
        },
        {
          "type": "basic",
          "from": {
            "key_code": "s"
          },
          "to": [
            {
              "shell_command": "open -a \"Sublime Text\""
            }
          ],
          "conditions": [
            {
              "type": "variable_if",
              "name": "text_editors_leader",
              "value": 1
            }
          ]
        }
      ]
    }
  ]
}
```

### Toolchain Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│  Meraki Config  │     │  TypeScript DSL  │     │  Karabiner JSON    │
│  (.meraki)      │     │  (.ts)           │     │  (.json)           │
└────────┬────────┘     └────────┬─────────┘     └───┬────┬───────────┘
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

This example demonstrates how Meraki's elegant 7-line configuration expands into 15 lines of TypeScript and over 100 lines of Karabiner JSON. The TypeScript DSL serves as a crucial intermediate representation, providing type safety and maintainability while hiding the complexity of the raw JSON configuration.

The toolchain architecture shows how our development tools will support the entire workflow, from editing Meraki configs through to generating the final Karabiner Elements configuration.

## Error Handling Strategy

### Pipeline Failure Modes
1. **Parser Failures**:
   ```ini
   # Invalid syntax
   mod1 = lcmd + @invalid  # Parser error: Invalid modifier key '@invalid'
   mod1 - {: open -a Mail  # Parser error: Malformed block syntax
   ```
   - Return specific line numbers and detailed error messages
   - Continue parsing to find additional errors
   - Generate partial AST for valid sections

2. **Validation Failures**:
   ```ini
   # Undefined modifier
   undefined_mod - m : open -a Mail  # Validation error: Undefined modifier
   
   # Duplicate binding
   mod1 - m : open -a Mail
   mod1 - m : open -a Chrome  # Validation error: Duplicate binding
   ```
   - Collect all validation errors before failing
   - Distinguish between errors (blocking) and warnings (non-blocking)
   - Allow `--force` flag to bypass non-critical validation

3. **Compilation Failures**:
   ```typescript
   // TypeScript compilation errors
   map('invalid_key').withModifiers('mod1')  // Error: Invalid key name
   
   // Karabiner JSON generation errors
   {
     "type": "basic",
     "from": { "invalid_field": true }  // Error: Invalid Karabiner JSON
   }
   ```
   - Isolate failures to specific keybindings
   - Generate partial output for successful bindings
   - Provide detailed error context for debugging

### Error Recovery Strategy
1. **Partial Success Mode**:
   ```bash
   # Example: Compile with partial success
   meraki-tool compile config.meraki --partial-success
   
   # Output:
   Warning: 2 keybindings failed to compile
   - Line 15: Invalid modifier combination
   - Line 23: Unsupported command
   Successfully compiled 18/20 keybindings
   ```

2. **Error Aggregation**:
   - Collect all errors before stopping
   - Group related errors together
   - Provide context for each error

3. **Debug Output**:
   ```bash
   # Generate detailed debug info
   meraki-tool compile config.meraki --debug
   
   # Output includes:
   - Parser state at failure
   - AST fragment causing error
   - Generated TypeScript
   - Karabiner JSON output
   ```

## Configuration Management

### Global Configuration (.merakirc)
```ini
# ~/.merakirc - Global user preferences

[defaults]
# Default timeouts (in milliseconds)
leader_timeout = 500
mouse_timeout = 250

[tools]
# External tool paths (optional)
yabai = /usr/local/bin/yabai
karabiner = /Library/Application Support/org.pqrs/Karabiner-Elements

[formatting]
# Basic formatting preferences
indent = 4
```

### Configuration Loading
```python
DEFAULT_CONFIG = {
    'defaults': {
        'leader_timeout': 500,  # milliseconds
        'mouse_timeout': 250    # milliseconds
    },
    'formatting': {
        'indent': 4
    }
}

def load_config() -> Config:
    config = DEFAULT_CONFIG.copy()
    
    # Load user config if it exists
    if os.path.exists('~/.merakirc'):
        config.update(load_merakirc('~/.merakirc'))
        
    return config
```

The configuration system is kept simple and focused on:
- Default timeouts for leader keys and mouse operations
- Basic formatting preferences
- Optional tool paths for external integrations

---

// ... rest of existing content ...