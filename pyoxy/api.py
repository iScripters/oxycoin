# -*- encoding: utf8 -*-
# © Toons

from . import __PY3__, __FROZEN__, ROOT, HOME
if not __PY3__: import cfg, slots
else: from . import cfg, slots

__TIMEOUT__ = 3

import os, sys, json, random, requests, logging, traceback

def getTokenPrice(token, fiat="usd"):
	cmc_ark = json.loads(requests.get("http://coinmarketcap.northpole.ro/api/v5/%s.json" % token).text)
	return float(cmc_ark["price"][fiat])

###################
## API endpoints ##
###################

# https://github.com/Oxycoin/api-documentation

POST_NDPT = [
	"/api/accounts/open",
	"/api/accounts/generatePublicKey",
	"/api/delegates/forging/enable",
	"/api/delegates/forging/disable",
	"/api/dapps/install",
	"/api/dapps/uninstall",
	"/api/dapps/launch",
	"/api/dapps/stop",
	"/api/multisignatures/sign",
]

PUT_NDPT = [
	"/api/accounts/delegates",
	"/api/transactions",
	"/api/signatures",
	"/api/dapps",
]

GET_NDPT = [
	"/api/accounts",
	"/api/accounts/getBalance",
	"/api/accounts/getPublicKey",
	"/api/accounts/delegates",
	"/api/loader/status",
	"/api/loader/status/sync",
	"/api/transactions",
	"/api/transactions/get",
	"/api/transactions/unconfirmed/get",
	"/api/transactions/unconfirmed",
	"/api/peers",
	"/api/peers/get",
	"/api/peers/version",
	"/api/blocks",
	"/api/blocks/get",
	"/api/blocks/getFee",
	"/api/blocks/getFees",
	"/api/blocks/getReward",
	"/api/blocks/getSupply",
	"/api/blocks/getHeight",
	"/api/blocks/getStatus",
	"/api/blocks/getNethash",
	"/api/blocks/getMilestone",
	"/api/signatures/get",
	"/api/delegates",
	"/api/delegates/get",
	"/api/delegates/count",
	"/api/delegates/voters",
	"/api/delegates/forging/getForgedByAccount",
	"/api/dapps",
	"/api/dapps/get",
	"/api/dapps/search",
	"/api/dapps/installed",
	"/api/dapps/installedIds",
	"/api/dapps/installing",
	"/api/dapps/uninstalling",
	"/api/dapps/launched",
	"/api/dapps/categories",
	"/api/multisignatures",
	"/api/multisignatures/pending",
	"/api/multisignatures/accounts",
]

#################
## API methods ##
#################

def get(entrypoint, dic={}, **kw):
	"""
generic GET call using requests lib. It returns server response as dict object.
It uses default peers registered in SEEDS list.

Argument:
entrypoint (str) -- entrypoint url path

Keyword argument:
dic (dict) -- api parameters as dict type
**kw       -- api parameters as keyword argument (overwriting dic ones)

Returns dict
"""
	# merge dic and kw values
	args = dict(dic, **kw)
	# API response contains several fields and wanted one can be extracted using
	# a returnKey that match the field name
	returnKey = args.pop("returnKey", False)
	args = dict([k.replace("and_", "AND:") if k.startswith("and_") else k, v] for k,v in args.items())
	
	try:
		text = requests.get(
			random.choice(cfg.peers) + entrypoint,
			params=args,
			headers=cfg.headers,
			verify=cfg.verify,
			timeout=__TIMEOUT__
		).text
		data = json.loads(text)
	except Exception as error:
		data = {"success":False, "error":error}
		if hasattr(error, "__traceback__"):
			data["details"] = "\n"+("".join(traceback.format_tb(error.__traceback__)).rstrip())
	else:
		if data["success"]:
			data = data[returnKey] if returnKey in data else data
	
	return data

def post(entrypoint, dic={}, **kw):
	# merge dic and kw values
	payload = dict(dic, **kw)
	# API response contains several fields and wanted one can be extracted using
	# a returnKey that match the field name
	returnKey = payload.pop("returnKey", False)
	try:
		text = requests.post(
			random.choice(cfg.peers)+entrypoint,
			data=json.dumps(payload),
			headers=cfg.headers,
			verify=cfg.verify,
			timeout=__TIMEOUT__
		).text
		data = json.loads(text)
	except Exception as error:
		sys.stdout.write(text + "\n")
		data = {"success":False, "error":error}
		if hasattr(error, "__traceback__"):
			data["details"] = "\n"+("".join(traceback.format_tb(error.__traceback__)).rstrip())
	return data

def put(entrypoint, dic={}, **kw):
	# merge dic and kw values
	payload = dict(dic, **kw)
	# API response contains several fields and wanted one can be extracted using
	# a returnKey that match the field name
	returnKey = payload.pop("returnKey", False)
	try:
		text = requests.put(
			random.choice(cfg.peers)+entrypoint,
			data=json.dumps(payload),
			headers=cfg.headers,
			verify=cfg.verify,
			timeout=__TIMEOUT__
		).text
		data = json.loads(text)
	except Exception as error:
		sys.stdout.write(text + "\n")
		data = {"success":False, "error":error}
		if hasattr(error, "__traceback__"):
			data["details"] = "\n"+("".join(traceback.format_tb(error.__traceback__)).rstrip())
	return data

#################
## API wrapper ##
#################

class Endpoint:
	
	def __init__(self, method, endpoint):
		self.method = method
		self.endpoint = endpoint

	def __call__(self, dic={}, **kw):
		return self.method(self.endpoint, dic, **kw)

	@staticmethod
	def createEndpoint(ndpt, method, path):
		elem = path.split("/")
		end = elem[-1]
		path = "/".join(elem[:2])
		for name in elem[2:]:
			path += "/"+name
			if not hasattr(ndpt, name):
				setattr(ndpt, name, Endpoint(method, path))
			ndpt = getattr(ndpt, name)

POST = Endpoint(post, "/api")
for endpoint in POST_NDPT:
	POST.createEndpoint(POST, post, endpoint)

PUT = Endpoint(put, "/api")
for endpoint in PUT_NDPT:
	PUT.createEndpoint(PUT, put, endpoint)

GET = Endpoint(get, "/api")
for endpoint in GET_NDPT:
	GET.createEndpoint(GET, get, endpoint)

#######################
## network selection ##
#######################

def use(network):
	networks = [os.path.splitext(name)[0] for name in os.listdir(HOME) if name.endswith(".net")]
	if len(networks) and network in networks:
		in_ = open(os.path.join(ROOT, network+".net"), "r" if __PY3__ else "rb")
		data = json.load(in_)
		in_.close()
		cfg.__dict__.update(data)
		cfg.verify = os.path.join(os.path.dirname(sys.executable), "cacert.pem") if __FROZEN__ else True
		cfg.begintime = slots.datetime.datetime(*cfg.begintime, tzinfo=slots.pytz.UTC)
		# update fees
		cfg.fees = GET.blocks.getFees(returnKey="fees")
		#update headers
		cfg.headers["version"] = GET.peers.version(returnKey="version")
		cfg.headers["nethash"] = GET.blocks.getNethash(returnKey="nethash")
		# update logger data so network appear on log 
		logger = logging.getLogger()
		logger.handlers[0].setFormatter(logging.Formatter('[%s]'%network + '[%(asctime)s] %(message)s'))
	else:
		raise NetworkError("Unknown %s network properties" % network)
