
email-event-aggregator-sieve
============================

Script to use from sieve filters (and occasionally command line) to aggregate
repeated event reports/notifications arriving to a mailbox.

Example might be cron job notifications - same thing failing over and over,
which you either don't have time or real need to address right now.

Idea though is not to "sweep these under the rug", but to make them not clutter
the mailbox (drowning out all other stuff) and draw disproportionate amount of
attention, compared to other - maybe much more rare, but also much more critical
stuff there.

This script enables usage scenario for (some subset of) a mailbox, where each
unread email is treated as an "open issue", and subsequent repeated
notifications about the same issue (with same content) don't need to be
prominent, but useful to get as an occasional reminder (e.g. aggregated into one
daily/weekly digest) while issue persists.


Operation
---------

This script is supposed to be hooked into e.g. `Dovecot/Pigeonhole "sieve" mail
filters`_, and process each message, calculating its distinct "fingerprint",
based on simple rules of your choosing (e.g. same subject + same body circa
timestamps) in a python "configuration" script (see "eeas.conf.example.py").

Repeated messages with the same fingerprint will then be rate-limited by a
token-bucket algorithm, returning negative (or just different - any string can
be returned) filtering result to sieve rules.

That doesn't mean that any mails should be dropped though - just dump them in
some "noise" dir of the mailbox (as opposed to e.g. "reports.cron") with "Seen"
flag set, so that whatever IMAP client/interface (MUA) won't be drawing
attention to these, and there won't be a "New Mail" notifications all the time.

Info about rate-limited mails should be stored in the database, so running
"digest" command (from the same script) every once in a while (e.g. daily) will
produce an email digest with the list of rate-limited stuff, if there was any.

This "digest" thing is not implemented yet.

.. _Dovecot/Pigeonhole "sieve" mail filters: http://wiki2.dovecot.org/Pigeonhole/Sieve/


Usage
-----

"eeas" here is a shorthand for "email-event-aggregator-sieve".

Configuration example (`Dovecot MDA`_):

``/etc/dovecot/dovecot.conf``::

  plugin {
    sieve = ~/.dovecot.sieve
    sieve_plugins = sieve_extprograms
    sieve_extensions = +vnd.dovecot.execute
    sieve_execute_socket_dir = sieve-execute
  }

  service eeas {
    executable = script /usr/local/bin/eeas
    user = dovenull
    unix_listener sieve-execute/eeas {
      mode = 0666
    }
  }

Note that ``sieve_execute_socket_dir`` will run command with specified (in the
``service`` block) uid/gid, not necessarily the ones of the maildir owner.
``sieve_execute_bin_dir`` option can be used for that instead.

``~/.dovecot.sieve``::

  if allof(
    execute :pipe :output "eeas_check" "eeas" "cron-jobs",
    not string :is "${eeas_check}" "pass"
  ) { fileinto :flags "\\Seen" "reports.cron.noise"; stop; }
  fileinto "reports.cron"; stop;

``~/.eeas.conf.py`` - see ``eeas.conf.example.py``

To test whether script/rules work, save one of the rate-limited mails (entire
thing, with headers) and run e.g.::

  % sieve-test -D -t- -Tdebug .dovecot.sieve message.eml

This should hit all the rules (showing which ones) and run the script, bumping
the rate-limit counters.

Run that a few more times (depending on configuration script), and eventually
limits should kick in, showing different outcome (as per sieve rules).

See also `Dovecot/Pigeonhole Sieve wiki`_, `vnd.dovecot.execute plugin spec`_
and `"extprograms" plugin page`_ for more info on dovecot configuration.

.. _Dovecot MDA: http://dovecot.org/
.. _Dovecot/Pigeonhole Sieve wiki: http://wiki2.dovecot.org/Pigeonhole/Sieve/
.. _vnd.dovecot.execute plugin spec:
   http://hg.rename-it.nl/pigeonhole-0.3-sieve-extprograms/raw-file/tip/doc/rfc/spec-bosch-sieve-extprograms.txt
.. _"extprograms" plugin page: http://wiki2.dovecot.org/Pigeonhole/Sieve/Plugins/Extprograms


Requirements
------------

* `Python 2.7 <http://python.org/>`__ (not 3.X)

* MDA (Mail Delivery Agent) with filtering that allows piping mail to scripts.


Notes
-----

* Email might not be the best place for event notifications, but it works, very
  robust and easiest to setup in most cases.

* This script obviously allows to run anything from its uid.
  Probably not a good idea to give that kind of access untrusted users, even if
  uid is something like "nobody" or "dovenull".

* I though it'd be more extensive thing initially, but nah, with embedded python
  for flexible "config", just one longish script seem to be enough.
