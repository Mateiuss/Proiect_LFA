from .NFA import NFA
from dataclasses import dataclass

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

        right_nfa = right_nfa.remap_states(lambda x: x + len(left_nfa.K))
        left_final_state = left_nfa.F.pop()

        left_nfa.S.update(right_nfa.S)
        if (left_final_state, '') in left_nfa.d:
            left_nfa.d[(left_final_state, '')].add(right_nfa.q0)
        else:
            left_nfa.d[(left_final_state, '')] = {right_nfa.q0}
        left_nfa.d.update(right_nfa.d)
        left_nfa.K = left_nfa.K.union(right_nfa.K)
        left_nfa.F = right_nfa.F

        return left_nfa

@dataclass
class Union(Regex):
    left: Regex
    right: Regex

    def thompson(self) -> NFA[int]:
        left_nfa = self.left.thompson()
        right_nfa = self.right.thompson()

        right_nfa = right_nfa.remap_states(lambda x: x + len(left_nfa.K))

        left_nfa.S.update(right_nfa.S)
        left_nfa.d[(-1, '')] = {left_nfa.q0, right_nfa.q0}
        left_final_state = left_nfa.F.pop()
        if (left_final_state, '') in left_nfa.d:
            left_nfa.d[(left_final_state, '')].add(-2)
        else:
            left_nfa.d[(left_final_state, '')] = {-2}
        right_final_state = right_nfa.F.pop()
        if (right_final_state, '') in right_nfa.d:
            right_nfa.d[(right_final_state, '')].add(-2)
        else:
            right_nfa.d[(right_final_state, '')] = {-2}
        left_nfa.d.update(right_nfa.d)
        left_nfa.F = {-2}
        left_nfa.K = left_nfa.K.union(right_nfa.K)
        left_nfa.K.add(-1)
        left_nfa.K.add(-2)
        left_nfa.q0 = -1

        left_nfa = left_nfa.remap_states(lambda x: x + 2)

        return left_nfa

@dataclass
class Star(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        regex_nfa = self.regex.thompson()

        final_state = regex_nfa.F.pop()

        regex_nfa.d[(-1, '')] = {regex_nfa.q0, -2}
        if (final_state, '') in regex_nfa.d:
            regex_nfa.d[(final_state, '')].update({regex_nfa.q0, -2})
        else:
            regex_nfa.d[(final_state, '')] = {regex_nfa.q0, -2}
        regex_nfa.K.add(-1)
        regex_nfa.K.add(-2)
        regex_nfa.F = {-2}
        regex_nfa.q0 = -1

        regex_nfa = regex_nfa.remap_states(lambda x: x + 2)

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

        final_state = regex_nfa.F.pop()
        regex_nfa.F.add(final_state)

        if (regex_nfa.q0, '') in regex_nfa.d:
            regex_nfa.d[(regex_nfa.q0, '')].add(final_state)
        else:
            regex_nfa.d[(regex_nfa.q0, '')] = {final_state}

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
        d = {(int(0), chr(i)) : {1} for i in range(ord('A'), ord('Z') + 1)}
        d[(int(1), '')] = {2}

        return NFA(S, {0, 1, 2}, 0, d, {2})


@dataclass
class SmallLetters(Regex):
    def thompson(self) -> NFA[int]:
        S = {chr(i) for i in range(ord('a'), ord('z') + 1)}
        d = {(int(0), chr(i)) : {1} for i in range(ord('a'), ord('z') + 1)}
        d[(int(1), '')] = {2}

        return NFA(S, {0, 1, 2}, 0, d, {2})

@dataclass
class Numbers(Regex):
    def thompson(self) -> NFA[int]:
        S = {chr(i) for i in range(ord('0'), ord('9') + 1)}
        d = {(int(0), chr(i)) : {1} for i in range(ord('0'), ord('9') + 1)}
        d[(int(1), '')] = {2}

        return NFA(S, {0, 1, 2}, 0, d, {2})


def is_char(c: str) -> bool:
    return c.isalpha() or c.isdigit()

# (, ), [, *, +, ?, |
def parse_regex(regex: str) -> Regex:
    s = []
    i = 0

    while i < len(regex):
        if regex[i] == ' ':
            i += 1
            continue

        if is_char(regex[i]):
            s.append(Char(regex[i]))
        else:
            if regex[i] == '*' or regex[i] == '+' or regex[i] == '?':
                if regex[i] == '*':
                    s.append(Star(s.pop()))
                elif regex[i] == '+':
                    s.append(Plus(s.pop()))
                else:
                    s.append(Question(s.pop()))
            elif regex[i] == '[':
                if regex[i + 1] == 'a':
                    s.append(SmallLetters())
                elif regex[i + 1] == 'A':
                    s.append(BigLetters())
                else:
                    s.append(Numbers())
                i = i + 4
            elif regex[i] == '(':
                s.append(regex[i])
            elif regex[i] == ')':
                last = 'c'

                while last != '(':
                    last = s.pop()
                    if last == '(':
                        break

                    nd_last = s.pop()
                    if nd_last == '(':
                        s.append(last)
                        break
                    elif nd_last == '|':
                        s.append(Union(s.pop(), last))
                    else:
                        s.append(Concat(nd_last, last))
            elif regex[i] == '|':
                if (len(s) > 1):
                    last = 'c'

                    while last != '(' and len(s) > 0:
                        last = s.pop()
                        if last == '(':
                            s.append(last)
                            break

                        if len(s) == 0:
                            s.append(last)
                            break

                        nd_last = s.pop()
                        if nd_last == '(':
                            s.append(nd_last)
                            s.append(last)
                            break

                        if nd_last == '|':
                            s.append(Union(s.pop(), last))
                        elif isinstance(nd_last, Regex):
                            s.append(Concat(nd_last, last))
                        else:
                            s.append(nd_last)
                            s.append(last)

                s.append(regex[i])
            elif regex[i] == '\\':
                s.append(Char(regex[i + 1]))
                i = i + 1
            else:
                s.append(Char(regex[i]))

        i += 1

    while len(s) > 1:
        last = s.pop()
        nd_last = s.pop()

        if nd_last == '|':
            s.append(Union(s.pop(), last))
        else:
            s.append(Concat(nd_last, last))
            
    return s.pop()
