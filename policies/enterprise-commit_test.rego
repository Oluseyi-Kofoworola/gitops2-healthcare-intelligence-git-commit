package enterprise.git

test_valid_commit {
  input := {
    "commits": [
      {
        "sha": "abc123",
        "message": "feat(payment): add apple pay support",
        "changed_files": ["services/payment-gateway/payment.go"],
      },
    ],
  }

  allow with input as input
}

test_invalid_commit_wip {
  input := {
    "commits": [
      {
        "sha": "def456",
        "message": "WIP: some stuff",
        "changed_files": ["services/payment-gateway/payment.go"],
      },
    ],
  }

  not allow with input as input
}
