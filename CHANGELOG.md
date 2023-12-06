# RC - TBD

## Version 3.11.1 - 27 April 2022

### Changed

- Change bill template

### Issues

- `TB-215`

### Added

- Add password policy for admin and end-user
- Add recaptcha for django admin login

### Issues

- `TB-212 TB-213`

## Version 3.11.0 - 15 December 2021

### Added

- Add phone-operator group
- Implement CDR Api for phone operator

### Issues

- `TB-210`

## Version 3.10.0 - 13 October 2021

### Changed

- Change bill template

### Added

- Add number 9200 & 94200 rules

### Issues

- `TB-204 TB-206`

## Version 3.9.1 - 5 April 2021

### Fixed

- Fix custom date in numbering capacity

### Issues

- `TB-201`

## Version 3.9.0 - 5 April 2021

### Added

- Implement action logs for users
- Send web socket notification to finance dashboard in case of offline payments
- Implement numbering capacity

### Issues

- `TB-197 TB-198 TB-200`

## Version 3.8.1 - 24 January 2021

### Fixed

- Fix validation on login with MFA

### Issues

- `TB-195`


## Version 3.8.0 - 24 January 2021

### Added

- Add `Sales` groups to user groups
- Add uac reg reload for Kazoo Kamailio

### Changed

- Refactor the usage of user groups
- Change `Finance-Admin` to `Finance` in user groups

### Removed

- Remove `Finance-Operator` user group

### Issues

- `TB-195 TB-196`

## Version 3.7.0 - 5 January 2021

### Changed

- Add new fields to invoice API of SIAM

### Fixed

- Fix using pro code in Kazoo registration

### Issues

- `TB-193 TB-194`

## Version 3.6.2 - 22 December 2020

### Fixed

- Fix README.md doc

### Issues 

- `DEV-31`

## Version 3.6.1 - 22 December 2020

### Fixed

- Make check for spy compatible with rar edge project
- Fix re-initializing templates in cache

### Issues 

- `TB-180 TB-191`

## Version 3.6.0 - 13 December 2020

### Added

- Add PDF download for credit invoices

### Changed

- Change the response on issuing interim invoices

### Fixed

- Fix getting total count of query set in pagination

### Issues

- `TB-189 TB-190 CGRAT-243`


## Version 3.5.0 - 8 December 2020

### Added

- Add deallocation cause

### Changed

- Update the flow of data migration

### Fixed 

- Fix getting user ip from SBC
- Fix removing extensions in deallocation

### Issues

- `TB-180 TB-186 TB-188 CGRAT-237`


## Version 3.4.0 - 17 November 2020

### Added

- Add deprecated response for deprecated|removed APIs
- Add the ability to update extension from subscription
- Add docker mode
- Send notification on customer's admin user creation (migration)

### Changed

- Upgrade `python` version to 3.9
- Refactor data migration services, URLs and APIs
- Refactor and clean apps
- Apply DRY on payment and invoice apps
- Accept urls without ending slash
- Rename `gateway` to `subscription`
- Rename `main_number` to `number`
- Send periodic invoice notifications at 0830 local time

### Fixed

- Fix validation of prime code in generate token
- Fix updating forwarded number in extension

### Removed

- Remove version 1 and 2 of `crm` app
- Remove `gis`, `fax`, `notifier`, `signal`, `client` and `storage` apps

### Issues 

- `TB-178 TB-179 TB-183 TB-185 TB-186 TB-187`

## Version 3.3.0 - 26 October 2020

### Added

- Keep the change history of max call concurrency field in gateway

### Changed

- Change the database of Kazoo Kamailio SBC to MySQL

### Issues 

- `TB-176 TB-177`

## Version 3.2.0 - 12 October 2020

### Added 

- Add MFA integration for login
- Send notification on subscription deallocation
- Send notification on converting subscription to postpaid
- Add a new API to CRM app for list of packages
- Add API to impersonate support user

### Changed

- Refactor notifications from CGG to handle numbers
- Refactor due date notification to have cause
- Refactor due date and deallocation to have warnings

### Fixed
- Prevent updating users with more than one groups
- Fix the value of outbound proxy in crm response
- Fix inserting dispatch into Kamailio dispatcher table
- Fix expiry time in Kazoo's `uacreg` table in the sqlite database

### Issues 

- `CGRAT-226 CGRAT-227 CGRAT-228 CGRAT-229 TB-169 CGRAT-230 TB-171 TB-172 TB-173 TB-123 TB-174 TB-175`

## Version 3.1.2 - 24 September 2020

### Fixed

- Use seconds instead of minutes in PDF download of invoices
- Stop disabling/enabling accounts in CGRateS
- Check subscription type on enabling outbound

### Issues

- `TB-164 TB-165 TB-166`

## Version 3.1.1 - 22 September 2020

### Fixed

- Sync gateway filters on GET and Export APIs

### Issues

- `TB-163`

## Version 3.1.0 - 20 September 2020

### Added

- Play a playback if outbound calls is disabled

### Fixed

- Fix error checking in file upload
- Load templates only on uwsgi and runserver
- Fix Asterisk domain variable in ARI controller

### Issues

- `TB-160 TB-161 TB-162`

## Version 3.0.1 - 13 September 2020

### Fixed

- Fix some translations on invoices

## Version 3.0.0 - 12 September 2020

### Added

- Add export APIs for invoices and payments
- Add a custom command to fix latest bills
- Change payment flow based on credit invoices
- Add new APIs for credit invoices
- Add hybrid payment flow
- Add offline payment flow
- Integrate trunk backed with file service
- Add prepaid subscription flow
- Add packages and package invoices
- Add a new API to convert prepaid to postpaid
- Hang up calls based on a global limit
- Add a API to increase base balance without pay
- Add a API to increase credit without pay
- Add a API to debit balance without usage
- Add a API to change auto pay settings of subscriptions
- Add Data Migration app to handle sent data from old trunk
- Translate new messages
- Add export csv API for gateways
- Update Kazoo's Kamailio sqlite database on extension changes
- Add new filters on gateways
- Add the ability to decrease base balances (to credit or not)
- Add a filter on allow calls in gateways
- Use SIP headers to communicate between nodes

### Changed

- Change `CRM` subscription creation flow
- Upgrade `Django` version
- Refactor all apps to remove CGRateS exposed urls
- Change the flow of payments and payment redirects
- Refactor membership, gateway, client and cdr app completely
- Change the way of handling notifications (MIS)
- Change invoice PDF fields and format
- Make file app compatible with file service version 0.2.0
- Remove user from extension and add customer to it
- Separate CDR database from main database
- Change CRM's create product API to accept any package id for prepaid products
- Refactor realm and replace it with prime code
- Use `Customer.id` instead of `customer_code` in `CGG`
- Improve the performance of getting gateways
- Change gateway's status on prepaid max usage or expiry
- Populate Kazoo Kamailio's database when extension has hosted
- Use UTC as the default timezone

### Fixed

- Fix tax cost in invoice migration
- Fix import credits command
- Fix cause codes in playback
- Unregister extension on deallocation
- Fix creating new product after deallocation
- Fix pagination in CDRs and Gateways APIs
- Fix default ordering on some models
- Fix permissions on extension
- Fix API restrictions on branch, interconnection and gateway
- Fix PDF invoice alignment on fcp
- Fix API restrictions on extension and gateway APIs for customers
- Fix sending mobile number to MIS gateway on payment
- Fix generic or filter on users API
- Fix redis connection settings for ARI, caching and celery
- Fix exporting CDRs to csv
- Fix bypass pagination for large number of subscriptions
- Fix enabling outbound calls on successful pays for package invoices
- Fix jalali dates in invoice download

### Removed

- Remove most unused apps and codes

### Issues

- `TB-72 TB-73 TB-74 TB-75 TB-76 TB-77 TB-78 TB-79 TB-91 TB-92 TB-94 TB-95 TB-96 TB-107 TB-114 TB-117 TB-129 TB-136 CGRAT-133 CGRAT-137 CGRAT-138 CGRAT-139 CGRAT-140 CGRAT-141 CGRAT-147 CGRAT-166 CGRAT-168 CGRAT-169 CGRAT-170 CGRAT-171 CGRAT-172 CGRAT-181 CGRAT-182 CGRAT-185 CGRAT-186 CGRAT-190 TB-113 TB-115 TB-139 TB-137 TB-138 TB-144 TB-142 TB-143 CGRAT-205 TB-150 TB-151 TB-152 TB-153 CGRAT-213 TB-157 TB-158 CGRAT-216`

## Version 2.0.1 - 3 Mar 2020

### Added

- Introduce ServCo in our service.
- Write commands to migrate all call numbers format to `e164`.
- Add `credit` field to our billing service.
- Many fixes and improvements on ARI.
- Django-Admin enhancements on Bill, Gateway, Extension models.
- Add `uwsgi` as dependency in Pipfile.
- Refactor project settings to working properly with `.env`.
- Lots of improvements and bug fixes.

### Issues

- `TB-71 CGRAT-130 TB-70 CGRAT-128 TB-69 TB-65 TB-68 TB-49 TB-67 TB-64 TB-66 NXA-51 TB-60 CGRAT-76 CGRAT-119 CGRAT-120 TB-63 TB-62 TB-57 NXA-45 NXA-38 NXA-43 CGRAT-105 NXA-24 TB-56 NXA-42 TB-55 TB-53 TB-52 TB-51 TB-50 TB-47 TB-46 TB-44 TB-48 TB-43 TB-40 TB-41 TB-37 TB-35 TB-34 TB-36 TB-38 TB-39 TB-11 TB-33 TB-31 NXA-28 NXA-25 TB-16 TB-28 TB-30`
