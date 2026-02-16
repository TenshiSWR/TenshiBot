import regex

regexes = {}
text = input("Text: ")

print("\n")

for find, replace in regexes.items():
    if text != regex.sub(find, replace, text):
        print('r"'+find+'":', 'r"'+replace+'"')
