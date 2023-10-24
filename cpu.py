import re

registerERegex = r"E.{1}X"
registerXRegex = r".{1}X"
registerHRegex = r".{1}H"
registerLRegex = r".{1}L"
# 1 2 4 8 16 32 64 128 256 512 1024 2048 4096 8192 16384 32768
# 16 bit computer
# Max 65535
binaryNums = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

def numToBinary(number):
    binaryNumber = ""

    for divider in binaryNums[::-1]:
        if number >= divider:
            binaryNumber = "1" + binaryNumber
            number -= divider
        else:
            binaryNumber = "0" + binaryNumber

    return binaryNumber

def binaryToNum(binary):
    number = 0

    for index, bit in enumerate(binary):
        if bit == "1":
            number += binaryNums[index]

    return number

class registers:
    def __init__(self):
        # E_X = 0-65535
        # _X = 0-256
        # _L = 0-15
        # _H = 0-15
        # E_X       _L _H     _X       
        # 16        4   4     8        
        #           |-8-|         
        #       E_X=|----16----|
        self.registerNames = ["EAX","AX","AH","AL", "EBX","BX","BH","BL", "ECX","CX","CH","CL", "EDX","DX","DH","DL", "EEX","EX","EH","EL", "ESX","SX","SH","SL"]
        self.registers = {
            "EAX": "0000000000000000",
            "AL": "0000",
            "AH": "0000",
            "AX": "00000000",

            "EBX": "0000000000000000",
            "BL": "0000",
            "BH": "0000",
            "BX": "00000000",

            "ECX": "0000000000000000",
            "CL": "0000",
            "CH": "0000",
            "CX": "00000000",

            "EDX": "0000000000000000",
            "DL": "0000",
            "DH": "0000",
            "DX": "00000000",

            "EEX": "0000000000000000",
            "EL": "0000",
            "EH": "0000",
            "EX": "00000000",

            "ESX": "0000000000000000",
            "SL": "0000",
            "SH": "0000",
            "SX": "00000000"
        }
        self.stack = []

    def get(self, register):
        return binaryToNum(self.registers[register])

    def set(self, register, value):
        value = numToBinary(value)

        # E_X
        if re.match(registerERegex, register):
            self.registers[register] = value
            self.registers[register[1] + "L"] = value[0:4]
            self.registers[register[1] + "H"] = value[4:8]
            self.registers[register[1:3]] = value[8:16]

        # _X
        elif re.match(registerXRegex, register):
            self.registers[register] = value[0:8]
            self.registers["E" + register[0] + "X"] = self.registers[register[0] + "L"] + self.registers[register[0] + "H"] + self.registers[register[0] + "X"]

        # _H
        elif re.match(registerHRegex, register):
            self.registers[register] = value[0:4]
            self.registers["E" + register[0] + "X"] = self.registers[register[0] + "L"] + self.registers[register[0] + "H"] + self.registers[register[0] + "X"]

        # _L
        elif re.match(registerLRegex, register):
            self.registers[register] = value[0:4]
            self.registers["E" + register[0] + "X"] = self.registers[register[0] + "L"] + self.registers[register[0] + "H"] + self.registers[register[0] + "X"]

        #value = int(value)
        #registerType = list(register)[-1]
        #registerName = list(register)[0]
        #
        #if registerType == "X":
        #    self.registers[register] = value
        #
        #    if value > 128:
        #        self.registers[registerName + "L"] = 128
        #        self.registers[registerName + "H"] = value - 128
        #    else:
        #        self.registers[registerName + "L"] = value
        #        self.registers[registerName + "H"] = 0
        #else:
        #    self.registers[register] = value
        #    self.registers[registerName + "X"] = self.registers[registerName + "L"] + self.registers[registerName + "H"]

class ram:
    # Addr is from 0-65535
    def __init__(self):
        with open("./ram", "w") as data:
            data.write("0000000000000000\n"*65535)

    def get(self, addr):
        addr = int(addr) - 1

        with open("./ram", "r") as data:
            data = data.readlines()
            return binaryToNum(data[addr].strip("\n")[0:8])
        
    def getReserved(self, addr):
        addr = int(addr) - 1

        with open("./ram", "r") as data:
            data = data.readlines()
            return binaryToNum(data[addr].strip("\n")[8:16])
        
    def set(self, addr, value, reserved):
        addr = int(addr) - 1
        value = int(value)
        reserved = int(reserved)

        # Verify reserved
        reservedCode = self.getReserved(addr + 1)
        if reservedCode != 0 and reservedCode != reserved:
            print(f"Tried to access ram position {addr + 1} with reserved code {reserved}, but the ram position was reserved with {reservedCode}")
            exit()

        with open("./ram", "r") as data:
            oldData = data.readlines()

        oldData[addr] = f"{numToBinary(value)[0:8]}{numToBinary(self.getReserved(addr + 1))[0:8]}\n"

        with open("./ram", "w") as data:
            data.write("".join(oldData))

    def setReserved(self, addr, reserved):
        addr = int(addr) - 1
        reserved = int(reserved)

        with open("./ram", "r") as data:
            oldData = data.readlines()

        oldData[addr] = f"{numToBinary(self.get(addr + 1))[0:8]}{numToBinary(reserved)[0:8]}\n"

        with open("./ram", "w") as data:
            data.write("".join(oldData))

    def setReservedBulk(self, addr, count, reserved):
        addr = int(addr) - 1
        reserved = int(reserved)
        count = int(count)

        with open("./ram", "r") as data:
            oldData = data.readlines()

        for index in range(int(addr), int(addr) + int(count) + 1):
            oldData[index] = f"{numToBinary(self.get(addr + 1))[0:8]}{numToBinary(reserved)[0:8]}\n"

        with open("./ram", "w") as data:
            data.write("".join(oldData))

class file:
    def create(self, file):
        with open(f"./sim/{file}", "w") as file:
            file.write("\n")

    def write(self, fileName, line, char, value):
        line = int(line) - 1
        char = int(char) - 1
        value = int(value)

        with open(f"./sim/{fileName}", "r") as file:
            oldData = file.readlines()

        if len(oldData) != 0:
            if len(oldData) <= line:
                oldData.append([])
                oldDataLine = []
            else:
                oldDataLine = list(oldData[line])

            if len(oldDataLine) <= char:
                oldDataLine.append(chr(value))
            else:
                oldDataLine[char] = chr(value)
            oldData[line] = "".join(oldDataLine)
        else:
            oldData = [chr(value)]

        with open(f"./sim/{fileName}", "w") as file:
            file.write("".join(oldData))

    def read(self, file, line, char):
        line = int(line) - 1
        char = int(char) - 1

        with open(f"./sim/{file}", "r") as file:
            file = file.readlines()
            return ord(file[line][char])

    def lines(self, file):
        with open(f"./sim/{file}", "r") as file:
            file = file.readlines()
            return len(file)
        
    def chars(self, file, line):
        line = int(line) - 1

        with open(f"./sim/{file}", "r") as file:
            file = file.readlines()
            return len(file[line].strip("\n"))