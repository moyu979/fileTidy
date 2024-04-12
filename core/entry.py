import argparse

import Init
import Check
import Add
import Move
parser = argparse.ArgumentParser()

subparsers = parser.add_subparsers(dest="command",help='functions')

parser_init=subparsers.add_parser("init",help="create new database to store datas")
parser_init.add_argument("--db",default="./",help="dir path to store database")

parser_add=subparsers.add_parser("add",help="add files to trace list")
parser_add.add_argument("--db",default="./",help="path of database")
parser_add.add_argument("--files",default=None,help="path of new files to trace")
parser_add.add_argument("--writeOrigin",default=True,help="write files to origins")
parser_add.add_argument("--checkExist",default=False,help="check hash of already exist files")

parser_check=subparsers.add_parser("check",help="check if files traced and record existed")
parser_check.add_argument("--db",default="./",help="path of database")
parser_check.add_argument("--files",default=None,help="path of new files to check")
parser_check.add_argument("--file",default=True,help="check if records existed")
parser_check.add_argument("--log",default=True,help="check if file traced")
parser_check.add_argument("--hash",default=False,help="cal hash to check")

parser_move=subparsers.add_parser("move",help="move file from a dir to another")
parser_move.add_argument("--db",default="./",help="path of database")
parser_move.add_argument("--source","-s",default=None,help="path of source dir")
parser_move.add_argument("--dest","-d",default=None,help="path of dest dir")

args = parser.parse_args()

if args.command=="init":
    Init.Init(args.db)
elif args.command=="check":
    Check.Check(args.db,args.files,args.existed,args.traced,args.checkHash)
elif args.command=="add":
    Add.Add(args.db,args.files,args.writeOrigin,args.checkExist)
elif args.command=="move":
    Move.Move(args.db,args.source,args.dest)