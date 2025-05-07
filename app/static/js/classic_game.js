// filepath: c:\Users\szere\Documents\test\my-flask-project\app\static\js\classic_game.js
// Values that were previously passed directly from Jinja
// will now be read from the 'gameConfig' object initialized in the HTML.
const gameConfig = JSON.parse(document.getElementById('game-config-data').textContent);

const nextMidnightISO = gameConfig.nextMidnightISO;
const isGameOverOnLoad = gameConfig.isGameOverOnLoad;
const isWinOnLoad = gameConfig.isWinOnLoad;
const dayNumberOnLoad = gameConfig.dayNumberOnLoad;
const incorrectGuessesOnLoad = gameConfig.incorrectGuessesOnLoad;
const maxGuessesOnLoad = gameConfig.maxGuessesOnLoad;
const MAX_GUESSES = gameConfig.MAX_GUESSES;
const initialRiddleId = gameConfig.initialRiddleId;
// const initialGameMode = gameConfig.initialGameMode; // selected_mode from gameConfig
// const answerDisplayString = gameConfig.answerDisplay; // answer_display from gameConfig
// const makeGuessUrl = gameConfig.makeGuessUrl; // url_for('main.make_guess') from gameConfig

let currentEmojiCharacter = ''; // To store the fetched emoji

document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;
    const timerDisplayElement = document.getElementById('timerDisplay');
    const countdownContainer = document.getElementById('countdownTimer');
    const shareSection = document.getElementById('share-section');
    const shareButton = document.getElementById('shareButton');
    const copyFeedback = document.getElementById('copy-feedback');
    const shareStatsButton = document.getElementById('shareStatsButton');
    const copyStatsFeedback = document.getElementById('copyStatsFeedback');

    if (isGameOverOnLoad && shareButton) {
        console.log("Setting share button data on page load.");
        shareButton.dataset.dayNumber = dayNumberOnLoad;
        const attemptsOnLoad = incorrectGuessesOnLoad + (isWinOnLoad ? 1 : 0);
        shareButton.dataset.attempts = attemptsOnLoad;
        shareButton.dataset.maxGuesses = maxGuessesOnLoad;
        shareButton.dataset.isWin = isWinOnLoad.toString(); // Ensure it's a string for dataset
    }

    let timerInterval = null;

    function updateCountdown() {
        if (!nextMidnightISO || nextMidnightISO === 'null' || !timerDisplayElement) {
            if(countdownContainer) countdownContainer.style.display = 'none';
            return;
        }
        const targetTime = new Date(nextMidnightISO).getTime();
        const now = new Date().getTime();
        const difference = targetTime - now;

        if (difference <= 0) {
            timerDisplayElement.textContent = "Ready!";
            if(countdownContainer) countdownContainer.innerHTML = "<strong>New Emojile available!</strong> Refresh the page.";
            clearInterval(timerInterval);
        } else {
            const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((difference % (1000 * 60)) / 1000);
            timerDisplayElement.textContent =
                `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            if(countdownContainer) countdownContainer.style.display = 'block';
        }
    }

    if (nextMidnightISO && nextMidnightISO !== 'null') {
        updateCountdown();
        timerInterval = setInterval(updateCountdown, 1000);
    } else {
        if(countdownContainer) countdownContainer.style.display = 'none';
    }

    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            darkModeToggle.textContent = '☀️';
        } else {
            body.classList.remove('dark-mode');
            darkModeToggle.textContent = '🌙';
        }
    };
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    darkModeToggle.addEventListener('click', () => {
        const currentTheme = body.classList.contains('dark-mode') ? 'dark' : 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    });

    if (initialRiddleId) {
        fetchEmojiAndDisplay(initialRiddleId, incorrectGuessesOnLoad, gameConfig.initialGameMode, isGameOverOnLoad);
    } else {
        displayEmoji('', incorrectGuessesOnLoad, gameConfig.initialGameMode, true); // Pass true for isGameOver if no riddle
    }

    document.addEventListener('keydown', (event) => {
        const key = event.key.toLowerCase();
        if (key.length === 1 && key >= 'a' && key <= 'z') {
            // Find the button element instead of an anchor
            const buttonTile = document.querySelector(`.letter-tile[data-letter="${key}"]`);
            if (buttonTile && !buttonTile.disabled) {
                buttonTile.click(); // Simulate click on the button
            }
        }
    });

    const alphabetContainer = document.querySelector('.alphabet-tiles');
    const guessesLeftDisplay = document.getElementById('guesses-left-display');
    const statsCard = document.getElementById('stats-card');
    // const statsBody = document.getElementById('stats-body'); // Not directly used in this scope
    // const flashContainer = document.querySelector('.container'); // Not directly used in this scope

    if (alphabetContainer) {
        alphabetContainer.addEventListener('click', handleGuess);
    }

    async function handleGuess(event) {
        if (!event.target.matches('.letter-tile:not(:disabled)')) {
            return;
        }
        const button = event.target;
        const letter = button.dataset.letter;
        
        // Optimistically disable button
        button.disabled = true;
        button.classList.add('disabled');

        try {
            const response = await fetch(gameConfig.makeGuessUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ guess: letter })
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                console.error("Guess Error:", data.error || `HTTP error! status: ${response.status}`);
                addFlashMessage(data.error || 'An error occurred.', 'danger');
                // Re-enable button only if the error is not "already guessed" or "game over"
                // and the game is not actually over according to server response (if available)
                if (!(data.error?.toLowerCase().includes('already guessed')) &&
                    !(data.error?.toLowerCase().includes('game is already over')) &&
                    !(data.game_over)) {
                    button.disabled = false;
                    button.classList.remove('disabled');
                }
                return;
            }

            // Call handleGuessResponse to update the UI with the server's data
            handleGuessResponse(data);

            // The specific styling for the guessed letter button (e.g., adding 'correct' class)
            // is handled within handleGuessResponse based on data.answer_display.
            // So, no need to add button.classList.add('correct') here directly based on data.is_correct.

        } catch (error) {
            console.error('Fetch error:', error);
            addFlashMessage('A network error occurred. Please try again.', 'danger');
            // Re-enable button on network error, if it's not part of guessed_letters already
            // This needs careful consideration; for now, re-enable if not part of an ongoing game over sequence.
            // A robust way would be to check if the letter is in `data.guessed_letters` if an error occurs after a successful response.
            // For a simple network error before response, re-enabling is usually safe.
            if (!document.body.classList.contains('game-over-state')) { // Assuming you add such a class on game over
                 button.disabled = false;
                 button.classList.remove('disabled');
            }
        }
    }

    if (shareButton) {
        shareButton.addEventListener('click', copyShareText);
    }

    function copyShareText() {
        const dayNum = shareButton.dataset.dayNumber;
        const attempts = shareButton.dataset.attempts;
        const maxGuess = shareButton.dataset.maxGuesses;
        const win = shareButton.dataset.isWin === 'true';
        let shareText = `Emojile Day ${dayNum}\n`;
        if (win) {
            shareText += `Guessed in ${attempts}/${maxGuess} attempts! 🎉\n`;
        } else {
            shareText += `X/${maxGuess} attempts 😥\n`;
        }
        shareText += `\n#emojile ${window.location.origin}${window.location.pathname}?mode=Classic`; // Generic link

        navigator.clipboard.writeText(shareText).then(() => {
            if (copyFeedback) {
                copyFeedback.style.display = 'inline';
                if(shareButton) shareButton.disabled = true;
                setTimeout(() => {
                    copyFeedback.style.display = 'none';
                    if(shareButton) shareButton.disabled = false;
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy text: ', err);
            addFlashMessage('Failed to copy score. Please try again.', 'danger');
        });
    }

    if (shareStatsButton) {
        shareStatsButton.addEventListener('click', copyOverallStats);
    }

    function copyOverallStats() {
        const totalGames = document.getElementById('stats-total-games')?.textContent || 'N/A';
        const avgIncorrect = document.getElementById('stats-avg-incorrect')?.textContent || 'N/A';
        const currentPlayStreak = document.getElementById('stats-current-play-streak')?.textContent || 'N/A';
        const longestPlayStreak = document.getElementById('stats-longest-play-streak')?.textContent || 'N/A';
        const currentCorrectStreak = document.getElementById('stats-current-correct-streak')?.textContent || 'N/A';
        const longestCorrectStreak = document.getElementById('stats-longest-correct-streak')?.textContent || 'N/A';
        let statsText = `My Emojile Stats:\n`;
        statsText += `Total Games: ${totalGames}\n`;
        statsText += `Avg Incorrect Guesses: ${avgIncorrect}\n`;
        statsText += `Current Play Streak: ${currentPlayStreak} 🔥\n`;
        statsText += `Longest Play Streak: ${longestPlayStreak}\n`;
        statsText += `Current Correct Streak: ${currentCorrectStreak} ✅\n`;
        statsText += `Longest Correct Streak: ${longestCorrectStreak}\n`;
        statsText += `\nPlay Emojile! ${window.location.origin}${window.location.pathname}`;

        navigator.clipboard.writeText(statsText).then(() => {
            if (copyStatsFeedback) {
                copyStatsFeedback.style.display = 'inline';
                if(shareStatsButton) shareStatsButton.disabled = true;
                setTimeout(() => {
                    copyStatsFeedback.style.display = 'none';
                    if(shareStatsButton) shareStatsButton.disabled = false;
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy stats text: ', err);
            addFlashMessage('Failed to copy stats. Please try again.', 'danger');
        });
    }
}); // End DOMContentLoaded

// Globally defined functions (can be moved inside DOMContentLoaded or organized differently if preferred)
function addFlashMessage(message, category) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${category} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    const referenceNode = document.getElementById('countdownTimer') || document.querySelector('h1');
    if (referenceNode && referenceNode.parentNode) {
        referenceNode.parentNode.insertBefore(alertDiv, referenceNode.nextSibling);
    } else {
        // Fallback: find .container and prepend
        const mainContainer = document.querySelector('.container');
        if (mainContainer) {
             mainContainer.insertBefore(alertDiv, mainContainer.firstChild);
        } else {
             document.body.insertBefore(alertDiv, document.body.firstChild); // Absolute fallback
        }
    }
    setTimeout(() => {
        const bootstrapAlert = bootstrap.Alert.getOrCreateInstance(alertDiv);
        if (bootstrapAlert) {
            bootstrapAlert.close();
        }
    }, 7000);
}

function updateStatsDisplay(statsData) {
    const fields = {
        'stats-total-games': statsData.total_games,
        'stats-avg-incorrect': statsData.avg_incorrect !== undefined ? statsData.avg_incorrect.toFixed(2) : '0.00',
        'stats-current-play-streak': statsData.current_play_streak,
        'stats-longest-play-streak': statsData.longest_play_streak,
        'stats-current-correct-streak': statsData.current_correct_streak,
        'stats-longest-correct-streak': statsData.longest_correct_streak,
        'stats-last-played': statsData.last_played_datetime_str ? `Last game finished: ${statsData.last_played_datetime_str}` : ''
    };
    for (const id in fields) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = fields[id];
        }
    }
}

async function fetchEmojiAndDisplay(riddleId, incorrectGuesses, gameMode, isGameOver) {
    if (!riddleId) {
        console.log("No riddle ID, clearing emoji display.");
        displayEmoji('', incorrectGuesses, gameMode, isGameOver);
        return;
    }
    try {
        const response = await fetch(`/api/get-emoji/${riddleId}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch emoji: ${response.statusText}`);
        }
        const data = await response.json();
        if (data.emoji) {
            currentEmojiCharacter = data.emoji; // Store for potential later use
            displayEmoji(currentEmojiCharacter, incorrectGuesses, gameMode, isGameOver);
        } else {
            console.error("Emoji not found in API response for riddle ID:", riddleId);
            displayEmoji('', incorrectGuesses, gameMode, isGameOver);
        }
    } catch (error) {
        console.error("Error fetching emoji:", error);
        displayEmoji('', incorrectGuesses, gameMode, isGameOver);
    }
}

function displayEmoji(emojiChar, incorrectGuesses, gameMode, isGameOver) {
    const textEmojiSpan = document.getElementById('text-emoji-display');
    const emojiContainer = document.getElementById('emoji-container');
    if (!textEmojiSpan || !emojiContainer) {
        console.error("Emoji display elements not found for Classic mode!");
        return;
    }
    const displayChar = emojiChar || '❓';
    textEmojiSpan.style.display = 'inline';
    emojiContainer.classList.add('classic-mode');
    emojiContainer.classList.remove('pixelated-mode');
    textEmojiSpan.textContent = displayChar;
}

function handleGuessResponse(data) {
    if (!data.success) {
        console.error("Guess Error:", data.error);
        // Optionally, display this error to the user using addFlashMessage
        // addFlashMessage(data.error, 'danger'); 
        return;
    }

    // 1. Update the Answer Tiles
    const answerTiles = document.querySelectorAll('.answer-tile');
    const newAnswerDisplayArray = data.answer_display.split('');

    answerTiles.forEach((tile, index) => {
        if (index < newAnswerDisplayArray.length) {
            const charToShow = newAnswerDisplayArray[index];
            if (charToShow === '_') {
                tile.innerHTML = '&nbsp;'; 
                tile.classList.remove('space'); 
            } else if (charToShow === ' ') {
                tile.innerHTML = '&nbsp;'; 
                tile.classList.add('space');    
            } else {
                tile.textContent = charToShow.toUpperCase(); 
                tile.classList.remove('space'); 
            }
        }
    });

    // 2. Update the Guessed Letters on the Keyboard
    const guessedLetters = data.guessed_letters; 
    guessedLetters.forEach(letter => {
        const letterTile = document.querySelector(`.letter-tile[data-letter="${letter.toLowerCase()}"]`);
        if (letterTile) {
            letterTile.classList.add('disabled');
            letterTile.disabled = true;
            // Style keyboard tile if letter is in the answer
            if (data.answer_display.toLowerCase().includes(letter.toLowerCase())) {
                 letterTile.classList.add('correct');
            } else {
                // Optionally, add an 'incorrect' class to style wrongly guessed letters on the keyboard
                // letterTile.classList.add('incorrect');
            }
        }
    });

    // 3. Update Guesses Left Display
    const guessesLeftDisplay = document.getElementById('guesses-left-display');
    if (guessesLeftDisplay && typeof gameConfig !== 'undefined' && gameConfig.MAX_GUESSES !== undefined) {
        guessesLeftDisplay.textContent = `Guesses left: ${gameConfig.MAX_GUESSES - data.incorrect_guesses}`;
    }

    // 4. Handle Game Over State
    if (data.game_over) {
        document.body.classList.add('game-over-state'); // Optional: for global styling/state checking
        // Disable all alphabet tiles that are not already disabled
        document.querySelectorAll('.letter-tile:not(.disabled)').forEach(tile => {
            tile.disabled = true;
            tile.classList.add('disabled');
        });

        const message = data.is_win ? 'Congratulations! You guessed it!' : 'Game over! Better luck next time.';
        // Using addFlashMessage for consistency, or keep alert if preferred
        addFlashMessage(message, data.is_win ? 'success' : 'warning');
        addFlashMessage(`The answer was: ${data.answer_display.toUpperCase()}`, 'info');


        const shareSection = document.getElementById('share-section');
        if (shareSection) {
            shareSection.style.display = 'block';
            const shareButton = document.getElementById('shareButton');
            if (shareButton && typeof gameConfig !== 'undefined') {
                shareButton.dataset.dayNumber = gameConfig.dayNumberOnLoad;
                shareButton.dataset.attempts = data.incorrect_guesses + (data.is_win ? 1 : 0);
                shareButton.dataset.maxGuesses = gameConfig.MAX_GUESSES;
                shareButton.dataset.isWin = data.is_win.toString();
            }
        }
        if (data.stats) {
            updateStatsDisplay(data.stats);
            const statsCard = document.getElementById('stats-card');
            if (statsCard) {
                statsCard.style.display = 'block';
            }
        }
    }
}

function updateIncorrectGuessesDisplay(count) {
    const displayElement = document.getElementById('incorrect-guesses-count'); // This ID doesn't exist in the HTML
    if (displayElement) {
        displayElement.textContent = `${count} / ${MAX_GUESSES}`;
    }
    // The actual display is 'guesses-left-display'
    const guessesLeftDisplay = document.getElementById('guesses-left-display');
    if (guessesLeftDisplay) {
         guessesLeftDisplay.textContent = `Guesses left: ${MAX_GUESSES - count}`;
    }
}