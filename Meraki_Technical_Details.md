# Meraki Technical Implementation Details

## AST Structure
The Abstract Syntax Tree (AST) is the core data structure that represents a parsed Meraki configuration. It serves as the contract between the parser and later phases.

### Comment Handling Strategy
The parser uses a multi-pass approach to handle comments:

1. **First Pass: Comment Extraction**
```python
{
  "comments": [
    {
      "type": "line",
      "text": "Define modifiers",
      "line_number": 1
    },
    {
      "type": "inline",
      "text": "Main modifier for app switching",
      "line_number": 2,
      "associated_code_line": 2
    },
    {
      "type": "multiline",
      "text": "This block configures\nall text editor bindings",
      "line_number": 5,
      "end_line": 7
    }
  ]
}
```

2. **Second Pass: Clean Configuration Parsing**
The parser processes the configuration with comments stripped, maintaining line numbers for later reattachment.

3. **Third Pass: Comment Reattachment**
Comments are attached to their relevant AST nodes based on line numbers and context.

### Structure Overview
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
          "comments": ["# Web browser"],
          "line_number": 4
        },
        "t": {
          "action": "open -a Terminal",
          "comments": ["# Terminal"],
          "line_number": 5
        }
      },
      "comments": [],
      "line_number": 3
    }
  ]
}
```

### Key Components
1. **Comments**:
   - Extracted and processed separately
   - Three types: line, inline, and multiline (@END...END)
   - Preserved line numbers for accurate reattachment
   - Associated with nearest meaningful code

2. **Modifiers**:
   - Basic and compound modifiers
   - Line numbers for error reporting
   - Attached comments from all three types

3. **Keybindings**:
   - Simple and nested bindings
   - Timeouts and actions
   - Associated comments maintained through parsing

### Usage in Pipeline
The AST structure is used by:
1. **Parser**: 
   - Extracts comments first
   - Parses clean configuration
   - Reattaches comments to AST nodes
2. **Validator**: Checks for errors and inconsistencies
3. **Formatter**: Uses comment positions for proper formatting
4. **Compiler**: Preserves comments in output formats

## Example Outputs By Phase

### Phase 1: Parser
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

### Phase 2: Validation
#### Example Output:
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

### Phase 3: Linting
#### Example Output:
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

### Phase 4: Formatting
#### Example Input/Output:
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

### Phase 5: Compilation
#### Current Features (v0.1)
1. **Application Management**:
```typescript
// Meraki: mod1 - j : focus --app "IntelliJ IDEA"
// Compiles to:
map('j').withModifiers(mod1)
  .to(shell('open -a "IntelliJ IDEA"'))

// Meraki: mod1 - l [500ms] : { c : open -a Chrome }
// Compiles to:
layer('apps', 'l').withModifiers(mod1)
  .timeout(500)
  .map('c', shell('open -a Chrome'))
```

2. **Modifier Handling**:
```typescript
// Meraki: mod2 + shift - n : open -a Notes
// Compiles to:
map('n').withModifiers([...mod2, 'shift'])
  .to(shell('open -a Notes'))
```

#### Future Features (v0.2)
Note: These features will be implemented in version 0.2:

1. **Window Management** (via yabai):
```typescript
// Future Implementation:
// mod2 - left : window --focus west
map('left').withModifiers(mod2)
  .to(shell('/usr/local/bin/yabai -m window --focus west'))
```

2. **Space Management** (via yabai):
```typescript
// Future Implementation:
// mod2 + shift - n : space --create
map('n').withModifiers([...mod2, 'shift'])
  .to(shell('/usr/local/bin/yabai -m space --create'))
```

#### Tool Detection and Configuration
```typescript
// config.ts
interface ExternalTools {
  // v0.1 tools
  karabiner: string;  // path to Karabiner Elements
  customTools: Record<string, string>;  // path to binaries

  // v0.2 tools (future)
  windowManager?: 'yabai' | 'amethyst' | 'rectangle' | null;
  hotkeyDaemon?: 'skhd' | null;
}

const config: ExternalTools = {
  karabiner: '/Library/Application Support/org.pqrs/Karabiner-Elements',
  customTools: {}
  // v0.2 features will be added here
}
```

#### Feature Support Matrix
| Feature Category | Version | Support Level | Required Tools |
|-----------------|---------|---------------|----------------|
| Key Mapping     | v0.1    | Native        | None          |
| Layers/Timeouts | v0.1    | Native        | None          |
| App Launch      | v0.1    | Native        | None          |
| Window Mgmt     | v0.2    | External      | yabai         |
| Space Mgmt      | v0.2    | External      | yabai         |
| Mouse Support   | v0.2    | Native        | None          |

### Complete Pipeline Example
Here's a real-world example showing how a v0.1 Meraki configuration expands through each stage:

1. **Original Meraki Config**:
```ini
# Define modifiers and leader key timeout
mod1 = lcmd + lalt
mod2 = lshift + lctrl

# App launcher with nested editors group
mod1 - a [500ms] : {
    c : open -a "Chrome";
    f : open -a "Finder";
    t : {  # Text editors
        v : open -a "Visual Studio Code";
        s : open -a "Sublime Text";
    }
}
```

2. **Generated AST**:
```json
{
  "modifiers": {
    "mod1": {
      "keys": ["lcmd", "lalt"],
      "line_number": 1
    },
    "mod2": {
      "keys": ["lshift", "lctrl"],
      "line_number": 2
    }
  },
  "keybindings": [
    {
      "key_combination": "mod1",
      "key": "a",
      "timeout": 500,
      "nested_bindings": {
        "c": {
          "action": "open -a \"Chrome\"",
          "line_number": 4
        },
        "f": {
          "action": "open -a \"Finder\"",
          "line_number": 5
        },
        "t": {
          "nested_bindings": {
            "v": {
              "action": "open -a \"Visual Studio Code\"",
              "line_number": 7
            },
            "s": {
              "action": "open -a \"Sublime Text\"",
              "line_number": 8
            }
          },
          "comments": ["# Text editors"],
          "line_number": 6
        }
      }
    }
  ]
}
```

3. **Generated TypeScript**:
```typescript
import { map, layer, shell } from 'karabiner.ts'

// Define modifiers
const mod1 = ['command', 'option']
const mod2 = ['shift', 'control']

// Create app launcher layer
const appLauncher = layer('apps', 'a')
  .withModifiers(mod1)
  .timeout(500)
  .map('c', shell('open -a "Chrome"'))
  .map('f', shell('open -a "Finder"'))

// Create nested text editors layer
const textEditors = layer('editors', 't')
  .withModifiers(mod1)
  .map('v', shell('open -a "Visual Studio Code"'))
  .map('s', shell('open -a "Sublime Text"'))

// Combine layers
const rules = [
  appLauncher,
  textEditors
]

// Write to profile
writeToProfile('Default', rules)
```

4. **Final Karabiner JSON**:
```json
{
  "title": "Meraki App Launcher",
  "rules": [
    {
      "description": "App Launcher (mod1 + a)",
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
        }
        // ... additional manipulators for other keys
      ]
    }
  ]
}
```

## Error Handling Strategy

### Comment-Related Errors
1. **Parser Failures**:
```ini
# Valid comments
# Normal comment
mod1 = lcmd + lalt  # Inline comment

# Invalid comments
@END incomplete block  # Error: Missing END marker
mod1 = lcmd + lalt # misplaced comment # duplicate comment
```

2. **Comment Validation**:
```ini
# Warning: Orphaned comment (no associated code)
# This comment has no context

mod1 = lcmd + lalt

@END
Documentation block
that should be attached
to something
END
# Warning: No code follows this documentation block
```

### Error Recovery Strategy
1. **Comment Processing**:
   - Continue parsing even if comment extraction fails
   - Mark malformed comments for warning output
   - Preserve line numbers for error reporting

2. **Comment Reattachment**:
   - Best-effort matching of comments to code
   - Warning for orphaned or misplaced comments
   - Maintain all comments even if attachment fails

## Configuration Management

### Global Configuration (.merakirc)
```ini
# ~/.merakirc - Global user preferences

[defaults]
# Default timeouts (in milliseconds)
leader_timeout = 500

[formatting]
# Basic formatting preferences
indent = 4

[tools]
# v0.1 tools
karabiner = /Library/Application Support/org.pqrs/Karabiner-Elements

# v0.2 tools (future)
# window_manager = /usr/local/bin/yabai
```

## CLI Tool Usage Examples
```bash
# Basic compilation
meraki-tool compile config.meraki
✓ Parsed successfully
✓ Validated (0 errors, 2 warnings)
✓ Generated TypeScript
✓ Compiled to Karabiner JSON
Output written to: ~/.config/karabiner/karabiner.json

# Watch mode with formatting
meraki-tool watch config.meraki --format
Watching for changes...
[12:01:15] File changed, reformatting...
[12:01:15] Compilation successful

# Validation only
meraki-tool check config.meraki
✓ Syntax valid
⚠ 2 warnings found:
  - Line 15: Consider grouping similar commands
  - Line 23: Unused modifier 'mod3'

# Format in place
meraki-tool format config.meraki
✓ Formatted 3 blocks
✓ Aligned 12 statements
✓ Fixed 5 spacing issues
```

## VSCode Extension Features
1. **Syntax Highlighting**:
```ini
# Modifiers highlighted in blue
mod1 = lcmd + lalt

# Commands highlighted in green
mod1 - l : open -a Safari

# Comments in gray
# This is a comment

# Errors underlined in red
mod3 - x : invalid command
```

2. **Hover Information**:
```
Hovering over 'mod1':
-------------------
Modifier: mod1
Keys: lcmd + lalt
Used in: 5 bindings
Defined at: line 1
```

3. **Command Completion**:
```
mod1 - l : op<cursor>
Suggestions:
- open -a Safari
- open -a Chrome
- open -a Terminal
``` 