class CheckError:

    # Check if the input is a number.
    def isnumber(self, input):
        for i in input:
            if i not in "0123456789":
                return False
        return True

    # Check if the input is a correct positive integer.
    def isproint(self, input):
        if input[0] in "123456789":
            for i in input:
                if i not in "0123456789":
                    return False
            return True
        return False

    # Check if the input is a correct positive number or 0.
    def ispronum(self, input):
        if input[0] in "0123456789":
            if input.count(".") <= 1:
                new_input = input.replace(".", "")
                for i in new_input:
                    if i not in "0123456789":
                        return False
                return True
            return False
        return False

    # Check if the input is a correct number.
    def isnum(self, input):
        if input[0] == "-" or input[0] in "0123456789":
            if input.count(".") <= 1 and input.count("-") <= 1:
                new_input = input.replace("-", "").replace(".", "")
                for i in new_input:
                    if i not in "0123456789":
                        return False
                return True
            return False
        return False

    # Check if the coordinate is in range of the isle.
    def isinisle(self, input1, input2):
        easting = float(input1)
        northing = float(input2)
        if easting < 415000 or easting > 480000 or northing < 65000 or northing > 110000:
            return False
        return True

    # Check if the mail address is correct.
    def checkmail(self, mail):
        if mail.count("@") == 1:
            mail = mail.replace(".", "").replace("@", "").replace("!", "").replace("#", "")\
                .replace("$", "").replace("%", "").replace("&", "").replace("'", "").replace("*", "")\
                .replace("+", "").replace("-", "").replace("/", "").replace("=", "").replace("?", "")\
                .replace("^", "").replace("_", "").replace("`", "").replace("{", "").replace("|", "")\
                .replace("}", "").replace("~", "")
            for i in mail:
                if not i.isalnum():
                    return False
            return True
        return False
