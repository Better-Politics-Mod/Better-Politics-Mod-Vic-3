def filter_lines(input_file, output_file, keyword, skip_count=5):
    with open(input_file, 'r', encoding='utf-16-le') as file:
        lines = file.readlines()

    filtered_lines = []
    skip = 0

    for line in lines:
        if skip > 0:
            skip -= 1
            continue
        
        if keyword in line:
            skip = skip_count
            continue
        
        filtered_lines.append(line)

    # Write the filtered lines to the output file
    with open(output_file, 'w', encoding='utf-16-le') as file:
        file.writelines(filtered_lines)

input_file = 'error-log.txt'  
output_file = 'error-log.txt'  
keyword = 'dlc_bpm'
filter_lines(input_file, output_file, keyword)
