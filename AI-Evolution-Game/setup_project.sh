#!/bin/bash

# Name: setup_project.sh
# Description: Bash script to set up the initial structure for the Foundational AI Evolution Game project in the current directory.

# Create directories for assets, documentation, and source files
mkdir -p assets/css assets/images assets/sounds docs src

# Create the main README file and add initial content
echo "# Foundational AI Evolution Game" > README.md

# Create the LICENSE file (assuming MIT license)
echo "MIT License" > LICENSE

# Create CSS file in assets directory and add a basic style comment
echo "/* Styles for the game */" > assets/css/styles.css

# Add a placeholder image file in assets/images
touch assets/images/icon.png

# Add a placeholder sound file in assets/sounds
touch assets/sounds/fall-sound.mp3

# Create the Product Requirement Document (PRD) in docs
echo "# Product Requirement Document (PRD) for Foundational AI Game" > docs/PRD.md

# Create main HTML file in src and add a basic HTML structure
cat <<EOL > src/index.html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Foundational AI Evolution Game</title>
    <link rel="stylesheet" href="../assets/css/styles.css">
</head>
<body>
    <canvas id="gameCanvas"></canvas>
    <script src="game.js"></script>
</body>
</html>
EOL

# Create the main JavaScript file for game logic in src
echo "// Primary game logic" > src/game.js

# Create a utility JavaScript file in src for auxiliary functions
echo "// Utility functions for game state management" > src/utils.js

# Initialize a Git repository, stage all files, and make an initial commit
git init
git add .
git commit -m "Initial project structure with placeholder files"

# Feedback to user
echo "Project structure created and initial commit made in the current directory."
