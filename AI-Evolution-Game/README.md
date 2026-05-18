# The Game of Revolution To AGI

## Overview
This interactive game demonstrates foundational AI concepts through a progressive transformation from data filtering to pattern recognition. The goal is to help users visualize how foundational AI evolves by removing noise and recognizing meaningful patterns, symbolized by transforming a rectangle into a trapezoid.

## Features (Phase 1)
- Data Filtering and Pattern Recognition: Users press the space bar or tap to simulate noise filtering. Each interaction triggers parts of the rectangle to "fall away," gradually shaping it into a trapezoid.
- End State: When only essential data remains, the game displays the message: "Congratulations! Patterns learned through differentiating signals and noise."

## Project Structure
```
.
├── assets/
│   ├── css/
│   │   └── styles.css           # Game styles
│   ├── images/
│   │   └── icon.png             # Placeholder icon
│   └── sounds/
│       └── fall-sound.mp3       # Placeholder sound effect
├── docs/
│   └── PRD.md                   # Product Requirements Document
├── src/
│   ├── index.html               # Main HTML file
│   ├── game.js                  # Game logic
│   └── utils.js                 # Utility functions
├── README.md                    # Project overview and instructions
└── LICENSE                      # MIT License
```
## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/codatta/AI-Evolution-Game.git
   ```

2. Navigate into the project folder:
   ```bash
   cd AI-Evolution-Game
   ```

## Testing
To test the game:
1. Open `src/index.html` in a web browser.
2. Press the Space Bar (or tap on mobile) to trigger falling pieces and transform the shape. The game completes when only the trapezoid remains.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
