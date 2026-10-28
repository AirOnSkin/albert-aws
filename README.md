# AWS services plugin

This Albert plugin lets you open various AWS services in the browser.  
It requires an Albert Python provider supporting interface **5.0**.

Set **AWS region** in the plugin's Albert settings (default: `eu-west-1`).
Changes are saved and apply to subsequent searches without restarting the plugin.
Blank input restores the default; invalid region code formats are ignored.
Global service links and account links are unaffected.

To customise links, update `AWS_URL_LIST` in [__init__.py](__init__.py).
Use `{0}` in regional URL templates for the configured region.

Trigger it with `aws `.

## Private account shortcuts

Copy [accounts.example.json](accounts.example.json) to [accounts.json](accounts.json)
beside the plugin and replace the example values with your SSO portal URL,
permission set name (for example, `readonly`) and account names and IDs.
Keep IDs as 12-digit strings to preserve leading zeros. Use the portal base URL
without a query string or fragment, for example `https://example.awsapps.com/start`.

The local file is excluded by [.gitignore](.gitignore); never force-add it.
Your existing local account list is preserved there. Account links and the portal
shortcut are read on each search, so edits do not require a restart. Missing files
disable account shortcuts; unreadable or invalid files produce a generic warning
in Albert's logs without preventing service searches. Do not put private account
data into the example file, source code or tests.

Ignoring the file does not remove account data from existing Git history.

## Validation

Run offline regression tests with `python3 -B -m unittest discover -s tests -v`.
These use an Albert interface 5.0 test double; loading the plugin, rendering icons
and opening URLs still need live validation inside Albert.
