from constants import hand_to_strength
'''
This file contains the base class that you should implement for your pokerbot.
'''


class Bot():
    '''
    The base class for a pokerbot.
    '''
    def __init__(self): 
        self.board_allocations = [[], [], []]

    def allocate(self, cards): 
        card_ranks = [c[0] for c in cards]
        for i in range(len(card_ranks) - 1): 
            for j in range(len(card_ranks)): 
                strength = hand_to_strength(card_ranks[i], card_ranks[j])

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
        self.board_allocations = [[], [], []]

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
        self.groups = [[], [], []]

    def get_actions(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your actions.
        '''
        raise NotImplementedError('get_actions')
