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

        left_nfa.S.update(right_nfa.S)
        left_nfa.d[(left_nfa.F.pop(), '')] = {right_nfa.q0}
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
        left_nfa.d[left_nfa.F.pop(), ''] = {-2}
        left_nfa.d[right_nfa.F.pop(), ''] = {-2}
        left_nfa.d.update(right_nfa.d)
        left_nfa.F = {-2}
        left_nfa.K = left_nfa.K.union(right_nfa.K)
        left_nfa.K.add(-1)
        left_nfa.K.add(-2)
        left_nfa.q0 = -1

        left_nfa = left_nfa.remap_states(lambda x: x + 2)

        print(left_nfa)

        return left_nfa

@dataclass
class Star(Regex):
    regex: Regex

    def thompson(self) -> NFA[int]:
        regex_nfa = self.regex.thompson()

        final_state = regex_nfa.F.pop()

        regex_nfa.d[(-1, '')] = {regex_nfa.q0, -2}
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

def parse_regex(regex: str) -> Regex:
    s = []
    i = 0

    while i < len(regex):
        if regex[i] == ' ':
            i += 1
            continue

        if is_char(regex[i]):
            if len(s) == 0:
                s.append(Char(regex[i]))
            else:
                last = s.pop()
                if last == '|':
                    s.append(last)
                    s.append(Char(regex[i]))
                elif last != '(':
                    s.append(Concat(last, Char(regex[i])))
                elif last == '(':
                    s.append(last)
                    s.append(Char(regex[i]))
        elif regex[i] == '*' or regex[i] == '+' or regex[i] == '?' or regex[i] == '(' or regex[i] == ')' or regex[i] == '|' or regex[i] == '[':
            if len(s) == 1:
                if regex[i] == '*':
                    s.append(Star(s.pop()))
                elif regex[i] == '?':
                    s.append(Question(s.pop()))
                elif regex[i] == '+':
                    s.append(Plus(s.pop()))
                elif regex[i] == '[':
                    if regex[i + 1] == 'A':
                        s.append(BigLetters())
                        i += 4
                    elif regex[i + 1] == 'a':
                        s.append(SmallLetters())
                        i += 4
                    elif regex[i + 1] == '0':
                        s.append(Numbers())
                        i += 4
                else:
                    s.append(regex[i])
            else:
                if regex[i] == ')':
                    last = s.pop()

                    if isinstance(last, Regex):
                        op = s.pop()
                        if op == '(': 
                            s.append(last)
                        elif op == '|':
                            other = s.pop()
                            s.pop()
                            s.append(Union(other, last))
                elif regex[i] == '(':
                    s.append(regex[i])
                elif regex[i] == '|':
                    s.append(regex[i])
                elif regex[i] == '*':
                    last = s.pop()

                    s.append(Star(last))
                elif regex[i] == '?':
                    last = s.pop()

                    s.append(Question(last))
                elif regex[i] == '+':
                    last = s.pop()

                    s.append(Plus(last))
                elif regex[i] == '[':
                    if regex[i + 1] == 'A':
                        s.append(BigLetters())
                        i += 4
                    elif regex[i + 1] == 'a':
                        s.append(SmallLetters())
                        i += 4
                    elif regex[i + 1] == '0':
                        s.append(Numbers())
                        i += 4
        else:
            raise Exception('invalid character')
        
        i += 1
        
    print(s)

    if len(s) == 1:
        return s.pop()
    else:
        last = s.pop()

        if isinstance(last, Regex):
            op = s.pop()
            if op == '|':
                return Union(s.pop(), last)
            elif isinstance(op, Regex):
                return Concat(op, last)
            
        raise Exception('invalid regex')
