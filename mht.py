#!/usr/bin/env pyth
# -*- coding: utf-8

import sys
import os
import re
import quopri
import base64


def parse_part(part):
	part = part.strip()
	pat1 = 'Content-Type: (.*)'
	pat1_res = re.search(pat1, part, re.I)
	ctype = pat1_res.groups()[0].strip() if pat1_res else ''
	# get Content-Transfer-Encodin
	pat2 = 'Content-Transfer-Encoding: (.*)'
	pat2_res = re.search(pat2, part, re.I)
	cenc = pat2_res.groups()[0].strip() if pat2_res else ''
	# get Content-Locatio
	pat3 = 'Content-Location: (.*)'
	pat3_res = re.search(pat3, part, re.I)
	cloc = pat3_res.groups()[0].strip() if pat3_res else ''
	# check part descriptio
	if cenc == '':
		return (-1, ctype, cenc, cloc, '')
	# parse the content
	try:
		contents = part.split('\n\n', 1)[1]
	except:
		contents = part.split('\n\r\n', 1)[1]
	if cenc == 'base64':
		s = base64.b64decode(contents)
	elif cenc == 'quoted-printable':
		s = quopri.decodestring(contents)
	return (0, ctype, cenc, cloc, s)


def parse_file(contents):
	# get boundar
	bnd_pat = 'boundary *= *" *([^"]*) *'
	bnd_res = re.search(bnd_pat, contents, re.I)
	bnd = bnd_res.groups()[0] if bnd_res else ''
	if bnd == '': return (-1, 'no boundary')

	# split using the boundar
	parts = contents.split('--' + bnd)

	# parse the part
	out = []
	for i, part in enumerate(parts):
		(res, ctype, cenc, cloc, s) = parse_part(part)
		if res == -1: continue
		out.append([ctype, cenc, cloc, s])

	return (0, out)

if __name__ == '__main__':
	import sys
	src = sys.argv[1]
	dst = sys.argv[2]
	contents = open(src).read()
	ok, outs = parse_file(contents)
	print ok
	for out in outs:
		ctype, cenc, cloc, s = out
		cloc = cloc.strip("/")
		dst_cloc = os.path.join(dst, cloc)
		if not os.path.exists(os.path.dirname(dst_cloc)):
			os.makedirs(os.path.dirname(dst_cloc))
		if cenc == "base64":
			open(dst_cloc, "wb").write(s)
		print ctype, cenc, cloc

