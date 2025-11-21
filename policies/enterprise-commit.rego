package enterprise.git

import future.keywords

# Simple, demo-level commit policy.
# In a real system, this input would be a structured representation of commits,
# usually built from `git log` by a small adapter.

default allow := false

allow if {
  # All commits in the push satisfy commit_ok
  every c in input.commits {
    commit_ok(c)
  }
}

commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  not regex.match("^security\\([^)]+\\):", c.message)
  not healthcare_compliance_required(c)
}

commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  not regex.match("^security\\([^)]+\\):", c.message)
  healthcare_compliance_required(c)
  has_compliance_metadata(c)
}

commit_ok(c) if {
  valid_format(c.message)
  not low_signal(c.message)
  not regex.match("^security\\([^)]+\\):", c.message)
  fda_validation_required(c)
  has_fda_validation(c)
}

commit_ok(c) if {
  regex.match("^security\\([^)]+\\):", c.message)
  valid_format(c.message)
  not low_signal(c.message)
  security_commit_touches_critical(c)
}

valid_format(msg) if {
  # Use regex.match instead of deprecated re_match
  regex.match("^(feat|fix|perf|security|docs|refactor|chore|breaking)\\([a-z-]+\\): .+", msg)
}

low_signal(msg) if {
  contains(lower(msg), "wip")
}

low_signal(msg) if {
  msg == "update"
}

low_signal(msg) if {
  contains(lower(msg), "temp")
}
