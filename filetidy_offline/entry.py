import command.starter as starter

import core.tools.confs as confs
if __name__ == '__main__':
    print(confs.conf)
    confs.load_conf()
    try:
        starter.MyCmd().cmdloop()
    except KeyboardInterrupt:
        print("stop")
    print(confs.conf)
    confs.save_conf()