"""ghost-publisher — queue-driven scheduled publishing to Ghost.

Thomas writes Markdown into `queue/`. A weekly job takes the top item,
renders it, and creates it on Ghost as a *scheduled* post. Ghost publishes
it server-side at the slot time.
"""

__version__ = "0.1.0"
