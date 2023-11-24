from .NFA import NFA
from dataclasses import dataclass
import re

class Regex:
    def thompson(self) -> NFA[int]:
        raise NotImplementedError('the thompson method of the Regex class should never be called')

# you should extend this class with the type constructors of regular expressions and overwrite the 'thompson' method
# with the specific nfa patterns. for example, parse_regex('ab').thompson() should return something like:

# >(0) --a--> (1) -epsilon-> (2) --b--> ((3))

# extra hint: you can implement each subtype of regex as a @dataclass extending Regex
    
@dataclass
class Concat(Regex):
    left: Regex
    right: Regex

    def thompson(self) -> NFA[int]:
        left_nfa = self.left.thompson()
        right_nfa = self.right.thompson()

        left_nfa.d[(left_nfa.F.pop(), '')] = {right_nfa.q0}
        left_nfa.d.update(right_nfa.d)
        left_nfa.F = right_nfa.F

        return left_nfa

@dataclass
class Union(Regex):
    left: Regex
    right: Regex

    def thompson(self) -> NFA[int]:
        left_nfa = self.left.thompson()
        right_nfa = self.right.thompson()

        right_nfa.remap_states(lambda x: x + len(left_nfa.K))

        left_nfa.d[(-1, '')] = {left_nfa.q0, right_nfa.q0}
        left_nfa.d[left_nfa.F.pop(), ''] = {-2}
        left_nfa.d[right_nfa.F.pop(), ''] = {-2}
        left_nfa.d.update(right_nfa.d)
        left_nfa.F = {-2}
        left_nfa.K.add(-1)
        left_nfa.K.add(-2)
        left_nfa.q0 = -1

        left_nfa.remap_states(lambda x: x + 2)

        return left_nfa

@dataclass
class Star(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        regex_nfa = self.regex.thompson()

        regex_nfa.d[(-1, '')] = {regex_nfa.q0}
        regex_nfa.d[regex_nfa.F.pop(), ''] = {-2}
        regex_nfa.d[(-1, '')].add(-2)
        regex_nfa.d[regex_nfa.F.pop(), ''] = {regex_nfa.q0}
        regex_nfa.d.update({(-1, ''): {-2}})
        regex_nfa.K.add(-1)
        regex_nfa.K.add(-2)
        regex_nfa.F = {-2}
        regex_nfa.q0 = -1

        regex_nfa.remap_states(lambda x: x + 2)

        return regex_nfa

@dataclass
class Plus(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        new_regex = Concat(self.regex, Star(self.regex))

        return new_regex.thompson()

@dataclass
class Question(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        regex_nfa = self.regex.thompson()
        regex_nfa.d[(regex_nfa.q0, '')] = regex_nfa.F
        return regex_nfa

@dataclass
class Char(Regex):
    char: str

    def thompson(self) -> NFA[int]:
        return NFA(set([self.char]), {0, 1}, 0, {(0, self.char): {1}}, {1})

@dataclass
class Epsilon(Regex):
    def thompson(self) -> NFA[int]:
        return NFA(set(), {0, 1}, 0, {(0, ''): {1}}, {1})

@dataclass
class Bracket(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        return self.regex.thompson()

@dataclass
class BigLetters(Regex):
    def thompson(self) -> NFA[int]:
        S = {chr(i) for i in range(ord('A'), ord('Z') + 1)}
        d = {(int(0), chr(i)) : {1} for i in range(ord('A'), ord('Z') + 1)} | {(int(1), chr(i)) : {2} for i in range(ord('A'), ord('Z') + 1)}

        return NFA(S, {0, 1, 2}, 0, d, {2})


@dataclass
class SmallLetters(Regex):
    def thompson(self) -> NFA[int]:
        S = {chr(i) for i in range(ord('a'), ord('z') + 1)}
        d = {(int(0), chr(i)) : {1} for i in range(ord('a'), ord('z') + 1)} | {(int(1), chr(i)) : {2} for i in range(ord('a'), ord('z') + 1)}

        return NFA(S, {0, 1, 2}, 0, d, {2})

@dataclass
class Numbers(Regex):
    def thompson(self) -> NFA[int]:
        S = {chr(i) for i in range(ord('0'), ord('9') + 1)}
        d = {(int(0), chr(i)) : {1} for i in range(ord('0'), ord('9') + 1)} | {(int(1), chr(i)) : {2} for i in range(ord('0'), ord('9') + 1)}

        return NFA(S, {0, 1, 2}, 0, d, {2})
    

def parse_regex(regex: str) -> Regex:
    return Char(regex)
