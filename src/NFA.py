from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs


@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def epsilon_closure(self, state: STATE) -> set[STATE]:
        # compute the epsilon closure of a state (you will need this for subset construction)
        # see the EPSILON definition at the top of this file
        closure = {state}
        state_queue = [state]

        while state_queue:
            curr_state = state_queue.pop()

            for next_state in self.d.get((curr_state, EPSILON), []):
                if next_state not in closure:
                    state_queue.append(next_state)
                    closure.add(next_state)

        return closure

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        # convert this nfa to a dfa using the subset construction algorithm
        dfa_q0 = frozenset(self.epsilon_closure(self.q0))
        dfa_k = {dfa_q0}
        dfa_d = dict()

        dfa_state_q = [dfa_q0]
        while dfa_state_q:
            dfa_curr_state = dfa_state_q.pop()

            for ltr in self.S:
                dfa_next_state = set()

                for nfa_state in dfa_curr_state:
                    nfa_next_states = self.d.get((nfa_state, ltr), set())

                    for nfa_next_state in nfa_next_states:
                        dfa_next_state.update(self.epsilon_closure(nfa_next_state))

                dfa_next_state = frozenset(dfa_next_state)

                if dfa_next_state not in dfa_k:
                    dfa_k.add(dfa_next_state)
                    dfa_state_q.append(dfa_next_state)

                dfa_d[(dfa_curr_state, ltr)] = dfa_next_state

        dfa_f = {dfa_state for dfa_state in dfa_k if dfa_state.intersection(self.F)}

        return DFA(self.S, dfa_k, dfa_q0, dfa_d, dfa_f)

    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        # optional, but may be useful for the second stage of the project. Works similarly to 'remap_states'
        # from the DFA class. See the comments there for more details.
        new_states = set([f(state) for state in self.K])
        new_d = dict()
        new_f = set([f(state) for state in self.F])

        for (state, symbol), next_states in self.d.items():
            new_d[(f(state), symbol)] = set([f(next_state) for next_state in next_states])

        return NFA(self.S, new_states, f(self.q0), new_d, new_f)
