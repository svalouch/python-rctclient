
.. _cli:

###
CLI
###

The library comes with a CLI tool called ``rctclient`` that offers some useful subcommands.

The tool is only installed if the `click <https://click.palletsprojects.com/>`_ module's present. If installing from
`pip`, the requirement can be pulled in by specifying ``rctclient[cli]``.

For certain parameters, the tool supports shell completion. Depending on your version of *Click*, there are different
ways to enable the completion:

* ``<  8.0.0``: ``eval "$(_RCTCLIENT_COMPLETE=source_bash rctclient)"`` (e.g. Debian 11, Ubuntu 20.04)
* ``>= 8.0.0``: ``eval "$(_RCTCLIENT_COMPLETE=bash_source rctclient)"`` (e.g. Arch, Fedora 35+, Gentoo)

Read more about this at the `click documentation <https://click.palletsprojects.com/en/7.x/bashcomplete/#activation>`_.

.. click:: rctclient.cli:cli
   :prog: rctclient
   :nested: full
