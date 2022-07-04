"""

    cc_command_arg.cpp

"""


import lx
import lxu.command

SERVER_NAME_COMMAND = "py.command.arg"


class Command(lxu.command.BasicCommand):
    """ Command with a single argument using value hints. When executed should open a dialog with some options for user
    to select and then will print out the selected option to log. """
    def __init__(self):
        """ Register the argument and define a text hint so we get a drop down of options """
        lxu.command.BasicCommand.__init__(self)
        self.dyna_Add("encodedInt", lx.symbol.sTYPE_INTEGER)
        self.dyna_SetHint(0, ((-1, "down"), (0, "unchanged"), (1, "up")))

    def cmd_DialogInit(self):
        """ Sets the default argument whenever the dialog is opened. """
        if not self.dyna_IsSet(0):
            self.attr_SetInt(0, 0)

    def basic_Execute(self, msg, flags):
        """ Read the argument and print it to log. """
        encoded_int = self.dyna_Int(0)
        lx.out(f"{SERVER_NAME_COMMAND} got {encoded_int}")


lx.bless(Command, SERVER_NAME_COMMAND)
