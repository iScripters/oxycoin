# -*- encoding: utf8 -*-
# © Toons

__all__ = ["network", "account", "delegate"]

from .. import cfg, api, util, __PY3__, __FROZEN__, __version__
import io, os, sys, shlex, docopt, logging, traceback, collections

rootfolder = os.path.normpath(os.path.abspath(os.path.dirname(sys.executable) if __FROZEN__ else __path__[0]))

__doc__ = """Welcome to pyoxy-cli [Python %(python)s / pyoxy %(pyoxy)s]
Available commands: %(sets)s""" % {"python":sys.version.split()[0], "pyoxy":__version__, "sets": ", ".join(__all__)}

input = raw_input if not __PY3__ else input

def _whereami():
	return ""

class _Prompt(object):
	enable = True

	def __setattr__(self, attr, value):
		object.__setattr__(self, attr, value)

	def __repr__(self):
		return "%(hoc)s@%(net)s/%(wai)s> " % {
			"hoc": "hot" if cfg.hotmode else "cold",
			"net": cfg.network,
			"wai": self.module._whereami()
		} if _Prompt.enable else ""

	def state(self, state=True):
		_Prompt.enable = state

PROMPT = _Prompt()
PROMPT.module = sys.modules[__name__]

def parse(argv):
	if argv[0] in __all__:
		module = getattr(sys.modules[__name__], argv[0])
		if hasattr(module, "_whereami"):
			PROMPT.module = module
			if len(argv) > 1:
				return parse(argv[1:])
		else:
			PROMPT.module = sys.modules[__name__]
	elif argv[0] in ["exit", ".."]:
		if PROMPT.module == sys.modules[__name__]:
			return False, False
		else:
			PROMPT.module = sys.modules[__name__]
	elif argv[0] in ["help", "?"]:
		sys.stdout.write("%s\n" % PROMPT.module.__doc__.strip())
	elif hasattr(PROMPT.module, argv[0]):
		try:
			arguments = docopt.docopt(PROMPT.module.__doc__, argv=argv)
		except:
			arguments = False
			sys.stdout.write("%s\n" % PROMPT.module.__doc__.strip())
		finally:
			return getattr(PROMPT.module, argv[0]), arguments
	else:
		sys.stdout.write("Command %s does not exist\n" % argv[0])

	return True, False

def start():
	sys.stdout.write(__doc__+"\n")
	exit = False
	while not exit:
		command = input(PROMPT)
		argv = shlex.split(command)

		if len(argv) and _Prompt.enable:
			cmd, arg = parse(argv)
			if not cmd:
				exit = True
			elif arg:
				if "link" not in argv:
					logging.info(command)
				else:
					logging.info(" ".join(argv[:2]+["x"*len(e) for e in ([] if len(argv) <=2 else argv[2:])]))
				try:
					cmd(arg)
				except Exception as error:
					if hasattr(error, "__traceback__"):
						sys.stdout.write("".join(traceback.format_tb(error.__traceback__)).rstrip() + "\n")
					sys.stdout.write("%s\n" % error)

# def execute(*lines):
# 	common.EXECUTEMODE = True

# 	for line in lines:
# 		sys.stdout.write("%s%s\n" % (PROMPT, line))
# 		argv = shlex.split(line)
# 		if len(argv):
# 			cmd, arg = parse(argv)
# 			if cmd and arg:
# 				if "link" not in argv:
# 					logging.info(line)
# 				else:
# 					logging.info(" ".join(argv[:2]+["x"*len(e) for e in ([] if len(argv) <=2 else argv[2:])]))
# 				try:
# 					cmd(arg)
# 				except Exception as error:
# 					if hasattr(error, "__traceback__"):
# 						sys.stdout.write("".join(traceback.format_tb(error.__traceback__)).rstrip() + "\n")
# 					sys.stdout.write("%s\n" % error)

# 	common.EXECUTEMODE = False

# def launch(script):
# 	if os.path.exists(script):
# 		in_ = io.open(script, "r")
# 		execute(*[l.strip() for l in in_.readlines()])
# 		in_.close()

def checkRegisteredTx(registry):
	global DAEMON_CHECK, PROMPT
	PROMPT.state(False)
	sys.stdout.write("Transaction check will be run soon, please wait...\n")

	@util.setInterval(cfg.blocktime)
	def _checkRegisteredTx(registry):
		global PROMPT
		registered = util.loadJson(registry)

		sys.stdout.write("\n---\nRegistered transaction check, please wait...\n")
		for tx_id, payload in list(registered.items()):
			if api.GET.transactions.get(id=tx_id).get("success", False):
				registered.pop(tx_id)
			else:
				sys.stdout.write("Resending transaction #%s:\n    %.8f %s to %s\n" % (
					tx_id,
					payload["amount"]/100000000,
					cfg.token, payload["recipientId"]
				))
				util.prettyPrint(api.post("/peer/transactions", transactions=[payload]), log=True)
		
		util.dumpJson(registered, registry)
		if not len(registered):
			sys.stdout.write("\nCheck finished, all transactiosn broadcasted\nType <Enter> to take the hand...")
			DAEMON_CHECK.set()
			PROMPT.state(True)
		else:
			sys.stdout.write("\n%d transaction(s) went missing in blockchain\nPlease wait %d seconds for another check...\n" % (len(registered), cfg.blocktime))

	DAEMON_CHECK = _checkRegisteredTx(registry)

from . import network, account, delegate
