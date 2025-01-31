import command.starter as starter

import core.tools.confs as confs
if __name__ == '__main__':
    confs.load_conf()
    try:
        starter.MyCmd().cmdloop()
    except KeyboardInterrupt:
        print("stop")
    confs.save_conf()