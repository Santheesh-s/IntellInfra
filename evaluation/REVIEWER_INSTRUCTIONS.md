# Reviewer Instructions — Hardware/OS Compatibility Validation

Thanks for helping validate this project! You'll look at 45 rows, each pairing
one campus machine's real specs against one operating system's minimum
requirements, and judge whether that machine could realistically run that OS.

**Please do this independently** — don't discuss your answers with other
reviewers until everyone has submitted, and don't ask the project author
which rule the system itself uses. The whole point is to see whether an
outside judgment matches the system's, so working it out yourself is what
makes this useful.

## What the columns mean

| Column | Meaning |
|---|---|
| `asset_id` | The machine being evaluated |
| `os_id` / `os_name` | The operating system being evaluated against |
| `ram_gb` | Machine's installed RAM | 
| `min_ram_gb` | OS's minimum required RAM |
| `storage_gb` | Machine's storage capacity |
| `min_storage_gb` | OS's minimum required storage |
| `cpu_cores` | Machine's CPU core count |
| `min_cpu_cores` | OS's minimum required CPU cores |
| `cpu_clock_ghz` | Machine's CPU clock speed |
| `min_clock_ghz` | OS's minimum required clock speed |
| `tpm_version` | Machine's TPM chip version (blank = no TPM chip at all) |
| `tpm_required` | TPM version the OS requires (blank = OS doesn't require TPM) |
| `secure_boot_support` | Whether the machine supports Secure Boot (True/False) |
| `secure_boot_required` | Whether the OS requires Secure Boot (True/False) |

## How to judge each row

For each row, compare the machine's specs to the OS's requirements:

- **`compatible`** — the machine meets or exceeds every requirement (RAM,
  storage, CPU cores, CPU clock, and, if the OS requires them, TPM version
  and Secure Boot).
- **`not_compatible`** — the machine falls short on at least one requirement
  that the OS actually needs. A blank `tpm_required` or `secure_boot_required`
  means the OS doesn't care about that one — don't fail a machine on a
  requirement the OS isn't asking for.
- **`borderline`** — use this if you genuinely think it's a judgment call
  (e.g. only marginally under a requirement, or you're unsure how strict a
  particular shortfall should be treated). Don't be afraid to use this
  option; it's useful signal on its own.

Fill your answer into the `expert_verdict` column (exactly one of
`compatible`, `not_compatible`, or `borderline`). Use `reviewer_notes` for
anything you want to flag — a row that felt ambiguous, a rule you weren't
sure how to apply, etc. That's genuinely useful even if you're confident in
your verdict.

## When you're done

Save the file and send it back to the project author. Once 2-3 reviewers
have completed it independently, the author will run:

```
python mcdm_validation_sample.py --score
```

to compute how often independent human judgment agreed with the system's
scoring — the actual number that goes in the paper's evaluation section.
