# Python script to clean non-ASCII characters from requirements.txt and write to requirements_clean.txt

def clean_non_ascii(input_file: str, output_file: str):
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
        lines = infile.readlines()

    cleaned_lines = []
    for line in lines:
        cleaned_line = ''.join(char for char in line if 32 <= ord(char) <= 126 or char in '\r\n\t')
        cleaned_lines.append(cleaned_line)

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.writelines(cleaned_lines)

if __name__ == '__main__':
    clean_non_ascii('requirements.txt', 'requirements_clean.txt')
    print("Cleaned requirements.txt saved to requirements_clean.txt")
