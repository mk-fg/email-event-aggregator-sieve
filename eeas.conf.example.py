# -*- coding: utf-8 -*-
#
# "config" here is a python module that must have "parser" function.
# That function should generate signature of the email and
#  pass that to "eeas" object (passed as arg) methods.
# Not calling any of these would mean that email can't be classified.
#
# Already present in the namespace: it, op, ft, re, types, string, vars below
# eeas methods: eeas.signature_from, eeas.rate_limit, eeas.mail_pass, eeas.mail_filter

## Optional override for path to db where signatures and rate limiting meta are stored.
## Already set in the namespace, will be checked once after module eval.
# db_path =

## Optional override for max email size and verdict for oversized emails
# mail_max_bytes =
# mail_max_bytes_verdict =

def parser(eeas, tags, msg):
	agg_name = fingerprint = None
	agg_type = None

	subject = msg.headers.get('subject')
	if subject:
		m = re.search(r'^Cron\s+<(?P<src>[^>]+)>\s+(?P<name>.*)$', subject)
		if m:
			agg_type = 'cron'
			agg_name = '[{}] {}: {}'.format(m.group('src'), agg_type, m.group('name'))

	if not agg_name:
		eeas.log.debug('Did not match agg_name from mail subject: %r', subject)
		return

	if agg_type == 'cron':
		fingerprint = list()
		for line in msg.text.splitlines():
			# Strip iso8601-ish timestamps from output lines, if any
			m = re.search(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:,\d+)? :: (.*)$', line)
			if m: line = m.group(1)
			fingerprint.append(line)

	if not fingerprint:
		# Can raise error here to have mail dropped into --error-reports-dir for later check
		eeas.log.debug( 'Failed to calculate fingerprint'
			' for mail body (agg_name: %s, agg_type: %s)', agg_name, agg_type )
		return

	# Currently required "signature" keys are: aggregate_name, fingerprint
	# "aggregate_name" will be only printed in a digest
	#  to show how many mails with this fingerprint were filtered.
	data_sig = eeas.signature_from(aggregate_name=agg_name, fingerprint=fingerprint)

	# Parameters for the token-bucket algorithm
	# burst: each matched mail "grabs" a token, or a fraction
	#   of one, regardless of how it gets classified in the end
	#  burst=5 means "max 5 tokens in a bucket"
	# tmin: when number of tokens drops below "tmin", stuff gets rate-limited
	#  Note that number of tokens can be fractional, so that if mails hit bucket
	#   with interval=1d more than 1/d, there will always be 0 <= n < 1 tokens,
	#   so with tmin=1, nothing will pass, until rate drops below 1/d
	# interval: interval between new tokens, in seconds
	eeas.rate_limit_filter(data_sig, tmin=1, burst=3, interval=3*24*3600)

	# Only last verdict from eeas.* functions will be used
