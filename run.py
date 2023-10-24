import cpu
import os
import re

variableRegex = r"\[.*?\]"

# mov From | To
def cmdMov(args):
    # Int to reg
    if args[0].isnumeric() and args[1] in regs.registerNames:
        regs.set(args[1], int(args[0]))
    
    # Int to ram
    elif args[0].isnumeric() and args[1].startswith("R"):
        if len(args) == 2:
            args.append(0)
        ram.set(args[1][1:], args[0], args[2])

    # Reg to reg
    elif args[0] in regs.registerNames and args[1] in regs.registerNames:
        value = regs.get(args[0])
        regs.set(args[1], value)

    # Reg to ram
    elif args[0] in regs.registerNames and args[1].startswith("R"):
        if len(args) == 2:
            args.append(0)
        ram.set(args[1][1:], regs.get(args[0]), args[2])

    # Ram to reg
    elif args[0].startswith("R") and args[1] in regs.registerNames:
        value = ram.get(args[0][1:])
        regs.set(args[1], value)

    # File to reg
    elif args[0].startswith("F") and args[3] in regs.registerNames:
        regs.set(args[3], file.read(args[0][1:], args[1], args[2]))

     # Reg to file
    elif args[0] in regs.registerNames and args[1].startswith("F"):
        file.write(args[1][1:], args[2], args[3], regs.get(args[0]))

     # Int to file
    elif args[0].isnumeric() and args[1].startswith("F"):
        file.write(args[1][1:], args[2], args[3], args[0])

# prt
def cmdPrt():
    value = regs.get("ESX")
    print(chr(value), end="", flush=True)

# rsr R___ | X of reserved | Reserved code
def cmdRr(args):
    if int(args[0][1:]) > 100:
        ram.setReservedBulk(args[0][1:], args[1], args[2])
    else:
        for index in range(int(args[0][1:]), int(args[0][1:]) + int(args[1])):
            ram.setReserved(index, args[2])

# rur Reserved code
def cmdUrr(args):
    found = False
    finished = False
    ramIndex = 1
    while not finished:
        ramData = ram.getReserved(ramIndex)

        if not found:
            if ramData == int(args[0]):
                found = True
        
        if found:
            if ramData != int(args[0]):
                finished = True
            else:
                ram.setReserved(ramIndex, 0)

        if ramIndex >= 60000:
            finished = True

        ramIndex += 1

# add Reg | Reg | Out reg
def cmdAdd(args):
    regA = regs.get(args[0])
    regB = regs.get(args[1])
    regs.set(args[2], regA + regB)

# sub Reg | Reg | Out reg
def cmdSub(args):
    regA = regs.get(args[0])
    regB = regs.get(args[1])
    regs.set(args[2], regA - regB)

# inc Reg
def cmdInc(args):
    reg = regs.get(args[0])
    regs.set(args[0], reg + 1)

# dec Reg
def cmdDec(args):
    reg = regs.get(args[0])
    regs.set(args[0], reg - 1)

# db String
def cmdDb(args):
    dbString = " ".join(args[3:])
    dbLenght = len(dbString)

    foundOrg = False
    search = int(args[0][1:])
    org = -1
    endOrg = -1
    while True:
        ramData = ram.get(search)

        if not foundOrg:
            if ramData == 0:
                foundOrg = True
                org = search

        if foundOrg:
            if ramData == 0:
                endOrg = search
            else:
                foundOrg = False

        calcLenght = endOrg - org + 1

        if calcLenght >= (dbLenght + 1):
            break

        search += 1

    if org == -1:
        print(f"Ram memory space exceded, tried to save {dbString} but no sufficient consistent space has been found")
        exit()

    vars[args[2]] = org

    ram.set(org, dbLenght, 1)
    for stringIndex, index in enumerate(range(org + 1, org + dbLenght + 1)):
        ram.set(index, ord(dbString[stringIndex]), args[1])

# rb Ram
def cmdRb(args):
    lenght = ram.get(args[0][1:])

    for index in range(int(args[0][1:]), int(args[0][1:]) + lenght + 1):
        ram.set(index, 0, 1)

# gin Search start location | Reservation code | Reg location output
def cmdGin(args):
    dbString = input()
    dbLenght = len(dbString)

    foundOrg = False
    search = int(args[0][1:])
    org = -1
    endOrg = -1
    while True:
        ramData = ram.get(search)

        if not foundOrg:
            if ramData == 0:
                foundOrg = True
                org = search

        if foundOrg:
            if ramData == 0:
                endOrg = search
            else:
                foundOrg = False

        calcLenght = endOrg - org + 1

        if calcLenght >= (dbLenght + 1):
            break

        search += 1

    if org == -1:
        print(f"Ram memory space exceded, tried to save {dbString} but no sufficient consistent space has been found")
        exit()

    ram.set(org, dbLenght, args[1])
    for stringIndex, index in enumerate(range(org + 1, org + dbLenght + 1)):
        ram.set(index, ord(dbString[stringIndex]), 1)

    regs.set(args[2], org)

# var Name | Value
def cmdVar(args):
    vars[args[0]] = int(args[1])

# cfe File path | Result reg
def cmdCfe(args):
    if os.path.exists(args[0]):
        regs.set(args[1], 1)
    else:
        regs.set(args[1], 0)

# cbt R__ | R__ | Result reg
def cmdCbt(args):
    ramLenghtA = ram.get(args[0][1:][0])
    ramLenghtB = ram.get(args[1][1:][0])

    if ramLenghtA != ramLenghtB:
        regs.set(args[2], 0)
    else:
        for index in range(1, ramLenghtA + 1):
            if ram.get(args[0][1:] + index) != ram.get(args[1][1:] + index):
                regs.set(args[2], 0)
                return
    
    regs.set(args[2], 1)

def getLabels(code):
    for index, codeLine in enumerate(code):
        codeLine = codeLine.strip("\n")
        arguments = codeLine.split(" ")

        if arguments[0] != "lbl":
            continue

        labels[arguments[1]] = index

def runCode(code):
    counter = 0

    getLabels(code)

    while counter < len(code):
        codeLine = code[counter]
        codeLine = codeLine.strip("\n")

        # Reg value exists, example [EAX]
        for replacement in re.findall(variableRegex, codeLine):
            replacement = replacement.strip("[]")

            if replacement in regs.registerNames:
                replacement = regs.get(replacement)
            else:
                # DB var
                replacement = vars[replacement]
            
            codeLine = re.sub(variableRegex, str(replacement), codeLine, 1)

        # arguments = command, argA, argB...
        arguments = codeLine.split(" ")
        arguments[0] = arguments[0].lower()

        # Move
        if arguments[0] == "mov":
            cmdMov(arguments[1:])

        # Print
        elif arguments[0] == "prt":
            cmdPrt()

        # Print new line
        elif arguments[0] == "nlp":
            print("\n", end="")

        # Reserve ram
        elif arguments[0] == "rr":
            cmdRr(arguments[1:])

        # Unreserve ram
        elif arguments[0] == "urr":
            cmdUrr(arguments[1:])

        # Add
        elif arguments[0] == "add":
            cmdAdd(arguments[1:])

        # Sub
        elif arguments[0] == "sub":
            cmdAdd(arguments[1:])

        # Increment
        elif arguments[0] == "inc":
            cmdInc(arguments[1:])

        # Decrement
        elif arguments[0] == "dec":
            cmdDec(arguments[1:])

        # Define string
        elif arguments[0] == "db":
            cmdDb(arguments[1:])

        # Remove bytes
        elif arguments[0] == "rb":
            cmdRb(arguments[1:])

        # Jump
        elif arguments[0] == "jmp":
            if arguments[1].isnumeric():
                counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
            else:
                counter = labels[arguments[1]]
        
        # Jump not equal
        elif arguments[0] == "jne":
            regA = regs.get(arguments[2])
            regB = regs.get(arguments[3])
        
            if regA != regB:
                if arguments[1].isnumeric():
                    counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
                else:
                    counter = labels[arguments[1]]
        
        # Jump equal
        elif arguments[0] == "je":
            regA = regs.get(arguments[2])
            regB = regs.get(arguments[3])
        
            if regA == regB:
                if arguments[1].isnumeric():
                    counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
                else:
                    counter = labels[arguments[1]]
        
        # Jump grater than
        elif arguments[0] == "jgt":
            regA = regs.get(arguments[2])
            regB = regs.get(arguments[3])
        
            if regA > regB:
                if arguments[1].isnumeric():
                    counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
                else:
                    counter = labels[arguments[1]]
        
        # Jump less than
        elif arguments[0] == "jlt":
            regA = regs.get(arguments[2])
            regB = regs.get(arguments[3])
        
            if regA < regB:
                if arguments[1].isnumeric():
                    counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
                else:
                    counter = labels[arguments[1]]

        # Get input
        elif arguments[0] == "gin":
            cmdGin(arguments[1:])

        # Variable
        elif arguments[0] == "var":
            cmdVar(arguments[1:])

        # Clear screen
        elif arguments[0] == "scl":
            os.system("cls")

        # Sub process
        elif arguments[0] == "spr":
            regs.stack.append(counter)
            counter = labels[arguments[1]]

        # Sub end
        elif arguments[0] == "spe":
            returnAddr = regs.stack.pop()
            counter = returnAddr

        # End
        elif arguments[0] == "end":
            return

        # Run another file
        elif arguments[0] == "run":
            runFile = ""

            arguments[1] = arguments[1].split("/")
            ramReplacemet = False
            ramReplacemetIndex = 0
            for replacementIndex, replacement in enumerate(arguments[1]):
                if replacement.startswith("R"):
                    ramReplacemet = True
                    ramReplacemetIndex = replacementIndex

            if ramReplacemet:
                if ramReplacemetIndex > 0:
                    runFile = "/".join(arguments[1][0:ramReplacemetIndex])
                    runFile += "/"

                ramReadLength = ram.get(arguments[1][ramReplacemetIndex][1:])

                for index in range(int(arguments[1][ramReplacemetIndex][1:]) + 1, int(arguments[1][ramReplacemetIndex][1:]) + ramReadLength + 1):
                    runFile += chr(ram.get(index))

                if len(arguments[1]) > (ramReplacemetIndex + 1):
                    runFile += "/"

                runFile += "/".join(arguments[1][ramReplacemetIndex + 1:])
            else:
                runFile = "/".join(arguments[1])

            if os.path.exists(f"./sim/{runFile}"):  
                with open(f"./sim/{runFile}", "r") as newCode:
                    newCode = newCode.readlines()

                runCode(newCode)
                getLabels(code)

        # Does file exist (1/0)
        elif arguments[0] == "cfe":
            cmdCfe(arguments[1:])

        # Compare two byte strings (1/0)
        elif arguments[0] == "cbt":
            cmdCbt(arguments[1:])

        # Quit the program
        elif arguments[0] == "ptm":
            exit()

        #if arguments[0] == "mov":
        #    #if arguments[1].startswith("R["):
        #    #    arguments[1] = arguments[1].strip("R[]")
        #    #    arguments[1] = f"R{regs.get(arguments[1])}"
        #    #if arguments[2].startswith("R["):
        #    #    arguments[2] = arguments[2].strip("R[]")
        #    #    arguments[2] = f"R{regs.get(arguments[2])}"
        #
        #    # reg to reg
        #    if arguments[1] in regs.registerNames and arguments[2] in regs.registerNames:
        #        regValue = regs.get(arguments[1])
        #        regs.set(arguments[2], regValue)
        #
        #    # ram to reg
        #    elif arguments[1].startswith("R") and arguments[2] in regs.registerNames:
        #        regs.set(arguments[2], ram.get(int(arguments[1][1:]))[0])
        #
        #    # reg to ram
        #    elif arguments[1] in regs.registerNames and arguments[2].startswith("R"):
        #        reservedValue = ram.get(arguments[2][1:])[1]
        #        if reservedValue != "00000000":
        #            if arguments[3] != reservedValue:
        #                print(f"At line {counter} you tried to access ram ({arguments[2]}) that was reserved ({reservedValue})")
        #                exit()
        #
        #        ram.set(int(arguments[2][1:]), regs.get(arguments[1]), reservedValue)
        #
        #    # file to reg
        #    elif arguments[1].startswith("F") and arguments[4] in regs.registerNames:
        #        regs.set(arguments[4], file.read(arguments[1][1:], arguments[2], arguments[3]))
        #
        #    # reg to file
        #    elif arguments[1] in regs.registerNames and arguments[2].startswith("F"):
        #        file.write(arguments[2][1:], arguments[3], arguments[4], regs.get(arguments[1]))
        #
        #    # int to file
        #    elif arguments[1].isnumeric() and arguments[2].startswith("F"):
        #        file.write(arguments[2][1:], arguments[3], arguments[4], arguments[1])
        #
        #    # int to reg
        #    elif arguments[1].isnumeric() and arguments[2] in regs.registerNames:
        #        regs.set(arguments[2], int(arguments[1]))
        #
        #elif arguments[0] == "prt":
        #    value = regs.get("ESX")
        #    print(chr(value), end="", flush=True)
        #
        ##elif arguments[0] == "lbl":
        ##    labels[arguments[1]] = int(arguments[2])
        #
        #elif arguments[0] == "jmp":
        #    if arguments[1].isnumeric():
        #        counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
        #    else:
        #        counter = labels[arguments[1]]
        #
        ## AH + BH = CH
        #elif arguments[0] == "add":
        #    if len(arguments) == 1:
        #        regA = regs.get("EAX")
        #        regB = regs.get("EBX")
        #        regs.set("ECX", regA + regB)
        #    else:
        #        regA = regs.get(arguments[1])
        #        regB = regs.get(arguments[2])
        #        regs.set(arguments[3], regA + regB)
        #
        ## AH - BH = CH
        #elif arguments[0] == "sub":
        #    if len(arguments) == 1:
        #        regA = regs.get("EAX")
        #        regB = regs.get("EBX")
        #        regs.set("ECX", regA - regB)
        #    else:
        #        regA = regs.get(arguments[1])
        #        regB = regs.get(arguments[2])
        #        regs.set(arguments[3], regA - regB)
        #
        #elif arguments[0] == "jne":
        #    if len(arguments) == 2:
        #        regA = regs.get("EAX")
        #        regB = regs.get("EBX")
        #    else:
        #        regA = regs.get(arguments[2])
        #        regB = regs.get(arguments[3])
        #
        #    if regA != regB:
        #        if arguments[1].isnumeric():
        #            counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
        #        else:
        #            counter = labels[arguments[1]]
        #
        #elif arguments[0] == "je":
        #    if len(arguments) == 2:
        #        regA = regs.get("EAX")
        #        regB = regs.get("EBX")
        #    else:
        #        regA = regs.get(arguments[2])
        #        regB = regs.get(arguments[3])
        #
        #    if regA == regB:
        #        if arguments[1].isnumeric():
        #            counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
        #        else:
        #            counter = labels[arguments[1]]
        #
        #elif arguments[0] == "jgt":
        #    if len(arguments) == 2:
        #        regA = regs.get("EAX")
        #        regB = regs.get("EBX")
        #    else:
        #        regA = regs.get(arguments[2])
        #        regB = regs.get(arguments[3])
        #
        #    if regA > regB:
        #        if arguments[1].isnumeric():
        #            counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
        #        else:
        #            counter = labels[arguments[1]]
        #
        #elif arguments[0] == "jlt":
        #    if len(arguments) == 2:
        #        regA = regs.get("EAX")
        #        regB = regs.get("EBX")
        #    else:
        #        regA = regs.get(arguments[2])
        #        regB = regs.get(arguments[3])
        #
        #    if regA < regB:
        #        if arguments[1].isnumeric():
        #            counter = int(arguments[1]) - 2 # Counter +1, python starting at 0, so -2
        #        else:
        #            counter = labels[arguments[1]]
        #
        #elif arguments[0] == "fcr":
        #    file.create(arguments[1])
        #
        #elif arguments[0] == "fdl":
        #    os.remove(f"./sim/{arguments[1]}")
        #
        #elif arguments[0] == "gin":
        #    userInput = input()
        #    userInput = list(userInput)
        #    reservedValue = ram.get(arguments[1][1:])[1]
        #
        #    arguments[1] = arguments[1][1:]
        #
        #    ram.set(int(arguments[1]), len(userInput), reservedValue)
        #
        #    for index, char in enumerate(userInput):
        #        ram.set(int(arguments[1]) + index + 1, ord(char), reservedValue)
        #
        #elif arguments[0] == "inc":
        #    if len(arguments) == 1:
        #        regValue = regs.get("EAX")
        #        regs.set("EAX", regValue + 1)
        #    else:
        #        regValue = regs.get(arguments[1])
        #        regs.set(arguments[1], regValue + 1)
        #elif arguments[0] == "dec":
        #    if len(arguments) == 1:
        #        regValue = regs.get("EAX")
        #        regs.set("EAX", regValue - 1)
        #    else:
        #        regValue = regs.get(arguments[1])
        #        regs.set(arguments[1], regValue - 1)
        #
        #elif arguments[0] == "run":
        #    #arguments[1] = arguments[1][1:]
        #
        #    with open(f"./sim/{arguments[1]}", "r") as fileCode:
        #        fileCode = fileCode.readlines()
        #
        #    runCode(fileCode)
        #
        #elif arguments[0] == "fln":
        #    if len(arguments) == 2:
        #        regs.set("EAX", file.lines(arguments[1]))
        #    else:
        #        regs.set(arguments[2], file.lines(arguments[1]))
        #
        #elif arguments[0] == "fch":
        #    if len(arguments) == 3:
        #        regs.set("EAX", file.chars(arguments[1], arguments[2]))
        #    else:
        #        regs.set(arguments[3], file.chars(arguments[1], arguments[2]))
        #
        #elif arguments[0] == "rmr":
        #    for ramIndex in range(arguments[1][1:], arguments[1][1:] + arguments[2] + 2):
        #        ram.set(ramIndex, ram.get(ramIndex)[0], arguments[3])
        #
        #elif arguments[0] == "rur":
        #    found = False
        #    ramIndex = 0
        #    while not found:
        #        ramIndex += 1
        #        ramValue = ram.get(ramIndex)[1]
        #
        #        if ramValue == arguments[1]:
        #            found = True
        #
        #    while ramValue == arguments[1]:
        #        ram.set(ramIndex, ram.get(ramIndex)[0], "00000000")
        #        ramIndex += 1
        #        ramValue = ram.get(ramIndex)[1]
            
        counter += 1

regs = cpu.registers()
ram = cpu.ram()
file = cpu.file()
labels = {}
vars = {}

with open("./sim/boot", "r") as code:
    code = code.readlines()

runCode(code)
