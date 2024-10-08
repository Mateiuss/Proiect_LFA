from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class DFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], STATE]
    F: set[STATE]

    def accept(self, word: str) -> bool:
        # simulate the dfa on the given word. return true if the dfa accepts the word, false otherwise
        current_state = self.q0

        for i in range(len(word)):
            if (current_state, word[i]) not in self.d:
                return False
            
            current_state = self.d[(current_state, word[i])]

        return current_state in self.F

    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'DFA[OTHER_STATE]':
        # optional, but might be useful for subset construction and the lexer to avoid state name conflicts.
        # this method generates a new dfa, with renamed state labels, while keeping the overall structure of the
        # automaton.

        # for example, given this dfa:

        # > (0) -a,b-> (1) ----a----> ((2))
        #               \-b-> (3) <-a,b-/
        #                   /     ⬉
        #                   \-a,b-/

        # applying the x -> x+2 function would create the following dfa:

        # > (2) -a,b-> (3) ----a----> ((4))
        #               \-b-> (5) <-a,b-/
        #                   /     ⬉
        #                   \-a,b-/
        new_states = set([f(state) for state in self.K])
        new_d = {(f(state), symbol): f(next_state) for (state, symbol), next_state in self.d.items()}
        new_f = set([f(state) for state in self.F])

        return DFA(self.S, new_states, f(self.q0), new_d, new_f)

