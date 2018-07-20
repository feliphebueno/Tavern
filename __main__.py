"""
Lib's rntry-point

"""
import sys
import os
from glob import glob
from tavern.core import run

# Adiciona o diretório de execução ao PATH para importação dos módulos da app
sys.path.append(os.getcwd())

STYLE_SUCCESS = '\33[42m\33[1m\33[37m'
STYLE_ERROR = '\33[101m\33[1m\33[37m'
END_STYLE = '\x1b[0m'

ENV_VARS = dict(os.environ)

if __name__ == '__main__':
    single_test: str = sys.argv[1] if len(sys.argv) > 1 else False
    test_files = glob('*.tavern.yaml') if single_test is False else [single_test]

    if len(test_files) == 0:
        print("No test file could be found")
        sys.exit(1)

    tests = dict()
    stages = 0
    passed = 0
    failed = 0

    target_url = os.environ.get("URL_API")

    if target_url is None:
        print("ERROR: Essetial environment variable URL_API not found.")
        sys.exit(1)

    failed = False
    for test_file in sorted(test_files, key=os.path.getmtime, reverse=True):
        result = run(test_file)

        if result['all_passed'] is True:
            print("%s All tests PASSED.%s" % (STYLE_SUCCESS, END_STYLE))
        else:
            failed = True
            print("%s %d tests FAILED.%s" % (STYLE_ERROR, len(result['failed']), END_STYLE))

    sys.exit(int(failed is True))
