
email-event-aggregator-sieve
============================

Script to use from sieve filters (and occasionally command line) to aggregate
repeated event reports/notifications arriving to a mailbox.

Example might be cron job notifications - same thing failing over and over,
which you either don't have time or real need to address right now.

Idea though is not to "sweep these under the rug", but to make them not clutter
the mailbox (drowning out all other stuff in there) and draw disproportionate
amount of attention, compared to other - maybe much more rare, but also much
more critical stuff there.

This script enables usage scenario (for some subset of) a mailbox, where each
unread email is treated as an "open issue", and subsequent repeated
notifications about the same issue don't need to be prominent, but useful to get
as an occasional reminder (e.g. aggregated in one digest) while issue persists.

**Under heavy development, not there yet**


Operation
---------

This script is supposed to be hooked into e.g. `Dovecot "sieve" mail filters`_,
and process each message, calculating its distinct "fingerprint", based on
simple regexp rules of your choosing (e.g. same subject + same body circa
timestamps).

Repeated messages with the same fingerprint will then be rate-limited by a
token-bucket algorithm, returning negative filtering result to sieve rules.

That doesn't mean that they should be dropped though - just dump them in some
"noise" dir of the mailbox (as opposed to e.g. "reports.cron") with "Seen" flag
set, so that whatever IMAP client/interface won't be drawing attention to these,
and there won't be any "New Mail" notifications all the time.

All the info about these mails gets stored in the database though, so running
"digest" command (from the same script) every once in a while (e.g. once a day)
will produce an email digest with the list of rate-limited stuff, if there was
any.

.. _Dovecot "sieve" mail filters: http://wiki2.dovecot.org/Pigeonhole/Sieve/


General note on email event notifications
-----------------------------------------

Email might not be the best place for these, but it works, very robust and
easiest to setup in most cases.
