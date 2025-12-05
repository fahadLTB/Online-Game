import streamlit as st
import random
from typing import List, Tuple

# Initialize session state
if 'game_state' not in st.session_state:
    st.session_state.game_state = None

class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.face_up = False
    
    def get_value(self) -> int:
        if self.rank == 'K':
            return 0
        elif self.rank == 'J' or self.rank == 'Q':
            return 10
        elif self.rank == 'A':
            return 1
        else:
            return int(self.rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit}"

class GolfGame:
    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        self.deck = self.create_deck()
        self.discard_pile = []
        self.players_hands = [[] for _ in range(num_players)]
        self.current_player = 0
        self.game_over = False
        self.scores = [0] * num_players
        self.round_scores = [0] * num_players
        self.drawn_card = None
        self.phase = 'setup'  # setup, initial_flip, playing, round_end
        self.initial_flips = [0] * num_players
        self.last_round = False
        self.last_round_starter = None
        
    def create_deck(self) -> List[Card]:
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        return deck
    
    def deal_cards(self):
        for player in range(self.num_players):
            self.players_hands[player] = [self.deck.pop() for _ in range(6)]
        self.discard_pile.append(self.deck.pop())
        self.phase = 'initial_flip'
    
    def flip_initial_cards(self, player: int, positions: List[int]):
        for pos in positions:
            self.players_hands[player][pos].face_up = True
        self.initial_flips[player] = len(positions)
        
        if all(f >= 2 for f in self.initial_flips):
            self.phase = 'playing'
    
    def draw_from_deck(self) -> Card:
        if len(self.deck) == 0:
            # Reshuffle discard pile if deck is empty
            top_card = self.discard_pile.pop()
            self.deck = self.discard_pile
            random.shuffle(self.deck)
            self.discard_pile = [top_card]
        self.drawn_card = self.deck.pop()
        return self.drawn_card
    
    def draw_from_discard(self) -> Card:
        self.drawn_card = self.discard_pile.pop()
        return self.drawn_card
    
    def replace_card(self, position: int):
        old_card = self.players_hands[self.current_player][position]
        self.players_hands[self.current_player][position] = self.drawn_card
        self.players_hands[self.current_player][position].face_up = True
        self.discard_pile.append(old_card)
        self.drawn_card = None
        self.check_matching_columns()
        self.end_turn()
    
    def discard_drawn_card(self):
        self.discard_pile.append(self.drawn_card)
        self.drawn_card = None
    
    def flip_card(self, position: int):
        self.players_hands[self.current_player][position].face_up = True
        self.end_turn()
    
    def check_matching_columns(self):
        hand = self.players_hands[self.current_player]
        # Check columns (positions 0&3, 1&4, 2&5)
        for col in range(3):
            top = hand[col]
            bottom = hand[col + 3]
            if top.face_up and bottom.face_up and top.rank == bottom.rank:
                hand[col] = None
                hand[col + 3] = None
    
    def end_turn(self):
        # Check if current player has all cards face up
        if all(card is None or card.face_up for card in self.players_hands[self.current_player]):
            if not self.last_round:
                self.last_round = True
                self.last_round_starter = self.current_player
        
        self.current_player = (self.current_player + 1) % self.num_players
        
        # Check if round is over
        if self.last_round and self.current_player == self.last_round_starter:
            self.end_round()
    
    def end_round(self):
        self.phase = 'round_end'
        for player in range(self.num_players):
            score = self.calculate_hand_score(player)
            self.round_scores[player] = score
            self.scores[player] += score
    
    def calculate_hand_score(self, player: int) -> int:
        hand = self.players_hands[player]
        score = 0
        for card in hand:
            if card is not None:
                score += card.get_value()
        return score
    
    def new_round(self):
        self.deck = self.create_deck()
        self.discard_pile = []
        self.players_hands = [[] for _ in range(self.num_players)]
        self.drawn_card = None
        self.phase = 'setup'
        self.initial_flips = [0] * self.num_players
        self.last_round = False
        self.last_round_starter = None
        self.round_scores = [0] * self.num_players
        self.deal_cards()

# Streamlit UI
st.set_page_config(page_title="Golf Card Game", page_icon="⛳", layout="wide")

st.title("⛳ Golf Card Game")

# Sidebar for game setup
with st.sidebar:
    st.header("Game Setup")
    
    if st.session_state.game_state is None:
        num_players = st.number_input("Number of Players", min_value=2, max_value=4, value=2)
        if st.button("Start New Game", type="primary"):
            st.session_state.game_state = GolfGame(num_players)
            st.session_state.game_state.deal_cards()
            st.rerun()
    else:
        st.write(f"**Players:** {st.session_state.game_state.num_players}")
        st.write(f"**Current Player:** Player {st.session_state.game_state.current_player + 1}")
        
        st.divider()
        st.subheader("Scores")
        for i in range(st.session_state.game_state.num_players):
            st.write(f"Player {i+1}: {st.session_state.game_state.scores[i]}")
        
        st.divider()
        if st.button("Reset Game", type="secondary"):
            st.session_state.game_state = None
            st.rerun()

# Main game area
if st.session_state.game_state is None:
    st.info("👈 Start a new game from the sidebar!")
    
    with st.expander("📖 How to Play Golf"):
        st.markdown("""
        **Objective:** Have the lowest score after 9 rounds.
        
        **Setup:**
        - Each player gets 6 cards in a 2x3 grid (face down)
        - Flip any 2 cards to start
        
        **On Your Turn:**
        1. Draw a card from the deck or discard pile
        2. Either:
           - Replace one of your cards with the drawn card
           - Discard the drawn card and flip one of your face-down cards
        
        **Scoring:**
        - Number cards: Face value
        - Ace: 1 point
        - Jack/Queen: 10 points
        - King: 0 points
        - Matching column (same rank): Both cards removed (0 points)
        
        **Round End:** When one player has all cards face up, others get one more turn.
        """)
else:
    game = st.session_state.game_state
    
    # Initial flip phase
    if game.phase == 'initial_flip':
        st.subheader(f"Player {game.current_player + 1}: Choose 2 cards to flip")
        
        cols = st.columns(3)
        selected = []
        
        for i in range(6):
            col_idx = i % 3
            with cols[col_idx]:
                card = game.players_hands[game.current_player][i]
                if not card.face_up:
                    if st.button(f"Card {i+1}", key=f"init_{i}", use_container_width=True):
                        if len(selected) < 2:
                            selected.append(i)
                else:
                    st.write(f"**{card}**")
        
        # Store selections in session state
        if 'selected_initial' not in st.session_state:
            st.session_state.selected_initial = []
        
        for s in selected:
            if s not in st.session_state.selected_initial:
                st.session_state.selected_initial.append(s)
        
        if len(st.session_state.selected_initial) >= 2:
            if st.button("Confirm Selection", type="primary"):
                game.flip_initial_cards(game.current_player, st.session_state.selected_initial[:2])
                game.current_player = (game.current_player + 1) % game.num_players
                st.session_state.selected_initial = []
                st.rerun()
    
    # Playing phase
    elif game.phase == 'playing':
        st.subheader(f"Player {game.current_player + 1}'s Turn")
        
        # Show discard pile
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            st.write("**Discard Pile:**")
            if game.discard_pile:
                st.write(f"🂠 {game.discard_pile[-1]}")
                if game.drawn_card is None:
                    if st.button("Draw from Discard", type="primary"):
                        game.draw_from_discard()
                        st.rerun()
        
        with col2:
            st.write("**Deck:**")
            st.write(f"🂠 {len(game.deck)} cards")
            if game.drawn_card is None:
                if st.button("Draw from Deck", type="primary"):
                    game.draw_from_deck()
                    st.rerun()
        
        # Show drawn card
        if game.drawn_card:
            st.info(f"Drawn Card: **{game.drawn_card}** (Value: {game.drawn_card.get_value()})")
            
            st.write("Choose an action:")
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                st.write("**Replace a card:**")
                cols = st.columns(3)
                for i in range(6):
                    col_idx = i % 3
                    with cols[col_idx]:
                        card = game.players_hands[game.current_player][i]
                        if card is not None:
                            label = str(card) if card.face_up else "🂠"
                            if st.button(f"Replace {i+1}: {label}", key=f"replace_{i}"):
                                game.replace_card(i)
                                st.rerun()
            
            with action_col2:
                st.write("**Or discard and flip:**")
                if st.button("Discard Drawn Card", type="secondary"):
                    game.discard_drawn_card()
                    st.rerun()
                
                if game.drawn_card is None:
                    st.write("Choose a card to flip:")
                    cols = st.columns(3)
                    for i in range(6):
                        col_idx = i % 3
                        with cols[col_idx]:
                            card = game.players_hands[game.current_player][i]
                            if card is not None and not card.face_up:
                                if st.button(f"Flip {i+1}", key=f"flip_{i}"):
                                    game.flip_card(i)
                                    st.rerun()
        
        # Show all players' hands
        st.divider()
        for player in range(game.num_players):
            with st.expander(f"Player {player + 1}'s Hand" + (" - YOUR TURN" if player == game.current_player else ""), expanded=(player == game.current_player)):
                cols = st.columns(3)
                for i in range(6):
                    col_idx = i % 3
                    with cols[col_idx]:
                        card = game.players_hands[player][i]
                        if card is None:
                            st.write("❌ (Matched)")
                        elif card.face_up:
                            st.write(f"**{card}** ({card.get_value()})")
                        else:
                            st.write("🂠")
    
    # Round end phase
    elif game.phase == 'round_end':
        st.subheader("Round Complete! 🎉")
        
        st.write("**Round Scores:**")
        for i in range(game.num_players):
            st.write(f"Player {i+1}: {game.round_scores[i]} points (Total: {game.scores[i]})")
        
        if st.button("Start Next Round", type="primary"):
            game.new_round()
            st.rerun()
