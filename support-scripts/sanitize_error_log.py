import re

def strip_ansi_codes(input_file, output_file):
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    clean_text = ansi_escape.sub('', text)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(clean_text)

input_file = 'error-log.txt'  
output_file = 'error-log.txt'  
strip_ansi_codes(input_file, output_file)
