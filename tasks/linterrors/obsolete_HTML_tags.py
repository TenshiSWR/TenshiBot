import regex


def fix_obsolete_HTML_tags(page: str, text: str) -> str:
    text = regex.sub(r"<(\/)font>", r"<\1span>", text)
    if regex.search(r"<\/?font[^>]*>", text):
        tags = list(set(regex.findall(r"<\/?font[^>]*>", text)))
        for font in tags:
            if regex.search(r"<font[^>]+>", font):
                params = regex.search(r"<font ([^>]+)>", font).group(1)
                new_params = params
                new_params = regex.sub(r'color="?([^"]+)"?', r"color: \1;", new_params)
                if regex.search(r'size="(?:.\d*)"', new_params):
                    size = regex.search(r'size="(.\d*)"', new_params).group(1)
                new_params = regex.sub(r'face="([A-z ]+)"', r"font-family: \1;", new_params)
                text = regex.sub(r'<font {}>'.format(params), r'<span style="{}">'.format(new_params), text)
    text = regex.sub(r"(?<!<nowiki>)(?<!<syntaxhighlight)(<\/?)(?:[Ss]trike)>(?!.*?<\/nowiki>)", r"\1s>", text)
    while True:
        if text != regex.sub(r"<center>((?:(?!(?:{\||\|}|(?<!<center>)<\/center>|<\/center>(?=<\/center>))).)*)<\/center>", r'<div style="text-align: center;">\1</div>', text, flags=regex.DOTALL):
            text = regex.sub(r"<center>((?:(?!(?:{\||\|}|(?<!<center>)<\/center>|<\/center>(?=<\/center>))).)*)<\/center>", r'<div style="text-align: center;">\1</div>', text, flags=regex.DOTALL)
        else:
            break
    return text
