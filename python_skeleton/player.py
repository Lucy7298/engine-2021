'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction, AssignAction
from skeleton.states import GameState, TerminalState, RoundState, BoardState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND, NUM_BOARDS
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot

import eval7
from constants import hand_to_strength



class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        pass

    def allocate(self, cards): 
        card_ranks = [c[0] for c in cards]
        strengths = {} #map (index card 1, index card 2) -> strength of pair 
        for i in range(len(card_ranks) - 1): 
            for j in range(i + 1, len(card_ranks)): 
                strength = hand_to_strength(card_ranks[i], card_ranks[j])
                strengths[(i, j)] = strength
        rank_pairs = sorted(list(strengths.items()), key=lambda i: i[1], reverse=True)
        print(rank_pairs)
        cards_put = set()
        pair_kept = []
        for pair in rank_pairs: 
            idxes, strength = pair
            if idxes[0] in cards_put or idxes[1] in cards_put: 
                continue 
            else: 
                cards_put.add(idxes[0])
                cards_put.add(idxes[1])
                pair_kept.append(idxes)
            if len(pair_kept) == 3: 
                break 
        return [[cards[i[0]], cards[i[1]]] for i in pair_kept]

    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        opp_bankroll = game_state.opp_bankroll # ^but for your opponent
        game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your six cards at teh start of the round
        big_blind = bool(active)  # True if you are the big blind
        self.board_allocations = self.allocate(my_cards)
        self.board_allocations.reverse()

    def calculate_strength(self, hole, board_cards, iters): 
        '''
        A Monte Carlo method meant to estimate the win probability of a pair of 
        hole cards. Simlulates 'iters' games and determines the win rates of our cards
        Arguments:
        hole: a list of our two hole cards
        iters: a integer that determines how many Monte Carlo samples to take
        '''

        deck = eval7.Deck() #eval7 object!
        hole_cards = [eval7.Card(card) for card in hole] #card objects, used to evaliate hands

        for card in hole_cards: #remove cards that we know about! they shouldn't come up in simulations
            deck.cards.remove(card)
        for card in board_cards: 
            deck.cards.remove(card)

        score = 0

        for _ in range(iters): #take 'iters' samples
            deck.shuffle() #make sure our samples are random

            _COMM = 5 - len(board_cards) #the number of cards we need to draw
            _OPP = 2

            draw = deck.peek(_COMM + _OPP)

            opp_hole = draw[: _OPP]
            community = draw[_OPP: ]

            our_hand = hole_cards + community + board_cards #the two showdown hands
            opp_hand = opp_hole + community + board_cards

            our_hand_value = eval7.evaluate(our_hand) #the ranks of our hands (only useful for comparisons)
            opp_hand_value = eval7.evaluate(opp_hand)

            if our_hand_value > opp_hand_value: #we win!
                score += 2
            
            elif our_hand_value == opp_hand_value: #we tie.
                score += 1
            
            else: #we lost....
                score += 0
        
        hand_strength = score / (2 * iters) #this is our win probability!

        return hand_strength

    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        opp_delta = terminal_state.deltas[1-active] # your opponent's bankroll change from this round 
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        for terminal_board_state in previous_state.board_states:
            previous_board_state = terminal_board_state.previous_state
            my_cards = previous_board_state.hands[active]  # your cards
            opp_cards = previous_board_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass

    def get_actions(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs a triplet of actions from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your actions.
        '''
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards across all boards
        board_cards = [board_state.deck if isinstance(board_state, BoardState) else board_state.previous_state.deck for board_state in round_state.board_states] #the board cards
        my_pips = [board_state.pips[active] if isinstance(board_state, BoardState) else 0 for board_state in round_state.board_states] # the number of chips you have contributed to the pot on each board this round of betting
        opp_pips = [board_state.pips[1-active] if isinstance(board_state, BoardState) else 0 for board_state in round_state.board_states] # the number of chips your opponent has contributed to the pot on each board this round of betting
        continue_cost = [opp_pips[i] - my_pips[i] for i in range(NUM_BOARDS)] #the number of chips needed to stay in each board's pot
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        stacks = [my_stack, opp_stack]
        net_upper_raise_bound = round_state.raise_bounds()[1] # max raise across 3 boards
        net_cost = 0 # keep track of the net additional amount you are spending across boards this round
        my_actions = [None] * NUM_BOARDS

        for i in range(NUM_BOARDS):
            if AssignAction in legal_actions[i]:
                cards = self.board_allocations[i]
                my_actions[i] = AssignAction(cards)
            if street < 3: 
                if CheckAction in legal_actions[i]:  # check-call
                    my_actions[i] = CheckAction()
                else:
                    my_actions[i] = CallAction()
            else: 
                #self.calculate_strength(self.board_allocations[i], board_cards, 100)
                if RaiseAction(stacks[0]/3) in legal_actions[i]:
                    my_actions[i] = RaiseAction(stacks[0]/3)
                elif CallAction in legal_actions[i]:
                    my_actions[i] = CallAction()
                elif RaiseActions(stacks[0]) in legal_actions[i]:
                    my_actions[i] = RaiseActions(stack[0])
                elif CheckAction in legal_actions[i]:
                    my_actions[i] = CheckAction()
                else:
                    my_actions[i] = FoldAction()

        return my_actions


if __name__ == '__main__':
    run_bot(Player(), parse_args())
    # b = Player()git
    # print(b.allocate(["AS", "KH", "2D", "2D", "TH", "3H"]))
    # print(b.allocate(["AS", "KH", "2D", "AD", "TH", "3H"]))
