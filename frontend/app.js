/**
 * Chess AI Recommendation System - Frontend Controller
 * - Handles chessboard events
 * - Communicates with FastAPI backend
 * - Updates the Strategic Analysis dashboard
 */

let board = null;
let game = new Chess();
const $fenText = $('#fenText');
const $latencyText = $('#latencyText');
const $cardsContainer = $('#recommendationCards');

// Backend URL (FastAPI)
const API_URL = 'http://localhost:8000/recommend';

function onDragStart(source, piece, position, orientation) {
    // Only allow moves for the side to move
    if (game.game_over()) return false;
    if ((game.turn() === 'w' && piece.search(/^b/) !== -1) ||
        (game.turn() === 'b' && piece.search(/^w/) !== -1)) {
        return false;
    }
}

async function fetchRecommendations(fen) {
    const startTime = performance.now();
    try {
        const response = await fetch(`${API_URL}?fen=${encodeURIComponent(fen)}`);
        const endTime = performance.now();
        
        // Update Latency Stat
        const latency = Math.round(endTime - startTime);
        $latencyText.text(`Latency: ${latency}ms`);

        if (!response.ok) {
            throw new Error('Recommendations not found for this position.');
        }

        const data = await response.json();
        renderRecommendations(data.recommendations);
    } catch (error) {
        console.error('API Error:', error);
        $cardsContainer.html(`
            <div class="placeholder-card">
                <p>${error.message}</p>
            </div>
        `);
    }
}

function renderRecommendations(recs) {
    $cardsContainer.empty();
    
    const categories = [
        { key: 'most_popular', title: 'The Standard Path', class: 'popular', icon: 'users' },
        { key: 'highest_success', title: 'The Statistical Edge', class: 'success', icon: 'trophy' },
        { key: 'pro_choice', title: 'The Master\'s Secret', class: 'expert', icon: 'graduation-cap' }
    ];

    categories.forEach(cat => {
        const moveData = recs[cat.key];
        if (!moveData) {
            // As per user request, handle missing pro data transparently
            if (cat.key === 'pro_choice') {
                $cardsContainer.append(`
                    <div class="rec-card disabled">
                        <div class="card-type ${cat.class}">
                            <i data-lucide="${cat.icon}"></i> ${cat.title}
                        </div>
                        <p class="explanation">Insufficient data for Expert analysis in this position.</p>
                    </div>
                `);
            }
            return;
        }

        const cardHtml = `
            <div class="rec-card" onclick="highlightMoveOnBoard('${moveData.move}')">
                <div class="card-type ${cat.class}">
                    <i data-lucide="${cat.icon}"></i> ${cat.title}
                </div>
                <div class="card-main">
                    <h3 class="move-txt">${rowToSan(moveData.move)}</h3>
                    <div class="win-stat">
                        <span class="win-pct">${Math.round(moveData.win_rate * 100)}%</span>
                        <div class="win-label">SUCCESS</div>
                    </div>
                </div>
                <div class="explanation">
                    "${moveData.explanation}"
                </div>
                <div class="card-footer-stats">
                    <span class="pop-stat">Played ${moveData.popularity}</span>
                </div>
            </div>
        `;
        $cardsContainer.append(cardHtml);
    });

    // Re-initialize Lucide icons for new elements
    lucide.createIcons();
}

/**
 * Helper to convert UCI move (e.g. e2e4) to a friendly SAN or coordinate-only display
 * chessboard.js works better with simple coordinates or UCI logic
 */
function rowToSan(uci) {
    // For this demo, we'll just show the move string clearly
    return uci;
}

function onDrop(source, target) {
    // See if the move is legal
    let move = game.move({
        from: source,
        to: target,
        promotion: 'q' // Always promote to queen for simplicity in this demo
    });

    // Illegal move
    if (move === null) return 'snapback';

    updateStatus();
}

function updateStatus() {
    const fen = game.fen();
    $fenText.text(fen);
    
    // Fetch AI Analysis from Spark/MongoDB Backend
    fetchRecommendations(fen);
}

function onSnapEnd() {
    board.position(game.fen());
}

/**
 * Highlight a recommended move on the board squares
 */
window.highlightMoveOnBoard = function(uci) {
    const from = uci.substring(0, 2);
    const to = uci.substring(2, 4);
    
    $('.square-55d63').removeClass('highlight-move');
    $(`.square-${from}`).addClass('highlight-move');
    $(`.square-${to}`).addClass('highlight-move');
};

// Controls
$('#resetBtn').on('click', () => {
    game.reset();
    board.start();
    updateStatus();
});

$('#undoBtn').on('click', () => {
    game.undo();
    board.position(game.fen());
    updateStatus();
});

// Board Configuration
const config = {
    draggable: true,
    position: 'start',
    onDragStart: onDragStart,
    onDrop: onDrop,
    onSnapEnd: onSnapEnd,
    // Use the local piece set downloaded to the project
    pieceTheme: 'img/chesspieces/wikipedia/{piece}.png'
};

board = Chessboard('board', config);

// Initial Analysis
updateStatus();
console.log("Chess AI Frontend Initialized. Slate/Blue theme applied.");
