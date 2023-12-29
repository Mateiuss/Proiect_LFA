from .DFA import DFA
from .Regex import Regex
from .Regex import parse_regex
from .NFA import NFA

class Lexer:
    def __init__(self, spec: list[tuple[str, str]]) -> None:
        # initialisation should convert the specification to a dfa which will be used in the lex method
        # the specification is a list of pairs (TOKEN_NAME:REGEX)

        self.lexer = NFA(set(), set(frozenset({0})), 0, {}, set())
        self.tokens = {}

        i = 0
        for token, regex in spec:
            nfa = parse_regex(regex).thompson()
            nfa = nfa.remap_states(lambda x: x + len(self.lexer.K))

            value = nfa.F.pop()
            self.tokens[value] = (token, i)
            nfa.F.add(value)
            
            self.lexer.S.update(nfa.S)
            self.lexer.K.update(nfa.K)
            self.lexer.d.update(nfa.d)
            self.lexer.F.update(nfa.F)
            if (self.lexer.q0, '') in self.lexer.d:
                self.lexer.d[(self.lexer.q0, '')].add(nfa.q0)
            else:
                self.lexer.d[(self.lexer.q0, '')] = {nfa.q0}

            i += 1

        self.lexer = self.lexer.subset_construction()

        pass

    def is_sink(state) -> bool:
        return state == frozenset()
    
    def is_final(tokens, state) -> bool:
        for s in state:
            if s in tokens.keys():
                return True
            
        return False

    def lex(self, word: str) -> list[tuple[str, str]] | None:
        # this method splits the lexer into tokens based on the specification and the rules described in the lecture
        # the result is a list of tokens in the form (TOKEN_NAME:MATCHED_STRING)

        curr_state = self.lexer.q0
        tokens = []
        last_token = ()

        character_pos = -1
        line_number = 0
        i = -1

        last_token_pos = -1
        last_character_pos = -1
        last_line_number = 0
        while i < len(word):
            if Lexer.is_sink(curr_state):
                if last_token != ():
                    character_pos = last_character_pos
                    line_number = last_line_number
                    i = last_token_pos
                    tokens.append((last_token[0], word[:i + 1]))
                    word = word[i + 1:]
                    i = -1
                    last_token = ()
                    curr_state = self.lexer.q0

                    sinked = True

                    continue
                else:
                    return [("", "No viable alternative at character " + str(character_pos) + ", line " + str(line_number))]
            elif Lexer.is_final(self.tokens, curr_state):
                last_token = ()
                for j in curr_state:
                    if j in self.tokens.keys():
                        if last_token == () or self.tokens[j][1] < last_token[1]:
                            last_token = self.tokens[j]
                            last_token_pos = i
                            last_character_pos = character_pos
                            last_line_number = line_number
            elif i == len(word) - 1:
                return [("", "No viable alternative at character EOF"+ ", line " + str(line_number))]

            i += 1
            character_pos += 1

            if i == len(word):
                break

            if word[i] == '\n':
                line_number += 1
                character_pos = -1

            letter = word[i]

            if (curr_state, letter) not in self.lexer.d:
                return [("", "No viable alternative at character " + str(character_pos) + ", line " + str(line_number))]

            curr_state = self.lexer.d[(curr_state, letter)]

        if last_token != ():
            tokens.append((last_token[0], word))

        return tokens

        # if an error occurs and the lexing fails, you should return none # todo: maybe add error messages as a task