---
name: erpnext-session
skill_type: skill
description: >-
  Check or change who the erpnext-mcp connector acts as: confirm the credential
  works with erpnext_get_logged_user, sign in with erpnext_login (user and
  password) and end that session with erpnext_logout. Use when a call is refused
  as unauthenticated, when the acting user must be confirmed before a write, or
  when a password session must be closed. Most deployments use a token and never
  need login.
license: MIT
tags: [erpnext, frappe, session, login, logout, identity, mcp]
metadata:
  version: '1.0.0'
---
# ERPNext session

## Steps

1. Check the acting user with `erpnext_get_logged_user` and verify it returns the user the requester named.
2. On an unauthenticated refusal with a password deployment, call `erpnext_login` and verify a later `erpnext_get_logged_user` call returns the requested user.
3. Close a password session with `erpnext_logout` and verify the response confirms the session ended.

## Failure recovery

| Failure | Cause | Recovery |
|---|---|---|
| Refused as unauthenticated on a token deployment | Token deployments do not use login | Do not call `erpnext_login`, and report the refusal to the requester |
| Wrong user returned | A different account is logged in | Call `erpnext_logout` and log in again with the account the requester named |
| Login rejected | The password is wrong | Ask the requester to supply credentials through their secret store, without echoing them, and call `erpnext_login` with the corrected value |

## Procedure
1. `erpnext_get_logged_user` returns the user the connector acts as. Run it
   first when a write is about to happen and the actor matters.
2. If the call is refused as unauthenticated and the deployment uses a password
   login, call `erpnext_login` with `usr` and `pwd`. Never print or store the
   password; with a token deployment, do not log in, report the refusal.
3. When the work is done and a password session was opened, call
   `erpnext_logout`.

## Never
- Never ask for, echo or write down a password or token in an answer.
- Never log in as a different user than the one the requester named.
