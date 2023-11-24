import pylint.lint
from pylint.message import Message
from pylint.reporters.json_reporter import JSONReporter
from mypy import api
import argparse

from relevant_messages import all_messages

extensions = [
    'bad_builtin',
    'broad_try_clause',
    'check_elif',
    'code_style',
    'comparison_placement',
    'confusing_elif',
    'consider_refactoring_into_while_condition',
    'consider_ternary_expression',
    'dict_init_mutate',
    'docparams',
    'docstyle',
    'dunder',
    'empty_comment',
    'eq_without_hash',
    'for_any_all',
    'magic_value',
    'mccabe',
    'no_self_use',
    'overlapping_exceptions',
    'private_import',
    'redefined_loop_name',
    'redefined_variable_type',
    'set_membership',
    'typing',
    'while_used',
]

other_options = [
    # '--max_complexity=50',
    '--max-line-length=160',
]


def get_pylint_messages(tgt: str) -> list[Message]:
    json_reporter = JSONReporter()
    pylint.lint.Run([tgt, *(f'--load-plugins=pylint.extensions.{plugin}' for plugin in extensions),
                     '--disable=all', f'--enable={",".join(all_messages)}'],
                    reporter=json_reporter, exit=False)
    return json_reporter.messages


if __name__ == '__main__':
    argparser = argparse.ArgumentParser()

    argparser.add_argument('target')
    argparser.add_argument('--output', '-o', type=str, default='./report.txt')

    args = argparser.parse_args()

    so, se, ec = api.run([args.target, '--strict'])

    with open(args.output, 'w') as f:
        for m in get_pylint_messages(args.target):
            if m.category in ['fatal', 'error', 'warning']:
                print(f'[@{m.path}:{m.line}:{m.column}] found serious issue of class {m.category}: {m.symbol}', file=f)
            if m.category == 'convention':
                print(f'[@{m.path}:{m.line}:{m.column}] break convention {m.symbol}', file=f)
            if m.category == 'refactor':
                print(f'[@{m.path}:{m.line}:{m.column}] refactor suggested: {m.symbol}', file=f)

        print(so, se, ec, file=f)
