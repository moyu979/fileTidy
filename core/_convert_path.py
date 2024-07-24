import re
def convert_path(path:str) ->str:
    pattern = r'([a-zA-Z]):/'
    replacement = r'/\1/'
    new_text = re.sub(pattern, replacement, path)
    new_new_text=new_text.replace("\\","/")
    return new_new_text