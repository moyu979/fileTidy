def tape_check(device):
    
    status=print(f"""功能未完成，请自行检查磁带: {device}安全输入y，危险输入n""")
    if status == "y":
        return "health"
    else:
        return "danger"