# Held-out accuracy audit

On 2026-11-23, ten apps were checked against published primary sources. The seeded draw excluded the pilot and the original audit. The AI-assisted review froze its labels before opening the predictions. The patched verifier used the saved first-pass claims and cached source text from the original run.

An answer is correct when its values match the documented label under the frozen rubric. An empty answer or unresolved conflict is an abstention. Accuracy uses all scorable fields. Coverage uses the share answered. Accuracy on answers uses answered fields as its denominator. [Rubric and sources](recheck-labels.json)

| Pass | Accuracy | Coverage | Accuracy on answers | Incorrect | Abstained |
| --- | ---: | ---: | ---: | ---: | ---: |
| First pass | 37/59 (62.7%) | 54/59 (91.5%) | 37/54 (68.5%) | 17 | 5 |
| Original verifier | 35/59 (59.3%) | 49/59 (83.1%) | 35/49 (71.4%) | 14 | 10 |
| Patched verifier | 33/59 (55.9%) | 48/59 (81.4%) | 33/48 (68.8%) | 15 | 11 |

Against the original verifier, 0 fields went from incorrect to correct, 0 from abstained to correct, 2 from correct to incorrect or abstained, and 1 from incorrect to abstained.

## Accuracy by dimension

| Dimension | First pass | Original verifier | Patched verifier |
| --- | ---: | ---: | ---: |
| Auth | 2/10 (20.0%) | 2/10 (20.0%) | 2/10 (20.0%) |
| Credential access | 11/19 (57.9%) | 9/19 (47.4%) | 7/19 (36.8%) |
| API surface | 19/20 (95.0%) | 18/20 (90.0%) | 18/20 (90.0%) |
| MCP | 5/10 (50.0%) | 6/10 (60.0%) | 6/10 (60.0%) |

## Accuracy by app

| App | First pass | Original verifier | Patched verifier |
| --- | ---: | ---: | ---: |
| Podio | 5/6 (83.3%) | 5/6 (83.3%) | 5/6 (83.3%) |
| Intercom | 5/6 (83.3%) | 5/6 (83.3%) | 5/6 (83.3%) |
| Lark (Larksuite) | 4/6 (66.7%) | 4/6 (66.7%) | 3/6 (50.0%) |
| GoHighLevel | 3/6 (50.0%) | 3/6 (50.0%) | 3/6 (50.0%) |
| Salesforce Commerce Cloud | 2/5 (40.0%) | 2/5 (40.0%) | 2/5 (40.0%) |
| DataForSEO | 4/6 (66.7%) | 4/6 (66.7%) | 4/6 (66.7%) |
| Netlify | 5/6 (83.3%) | 2/6 (33.3%) | 2/6 (33.3%) |
| Harvest | 3/6 (50.0%) | 3/6 (50.0%) | 2/6 (33.3%) |
| Brex | 2/6 (33.3%) | 3/6 (50.0%) | 3/6 (50.0%) |
| Fathom | 4/6 (66.7%) | 4/6 (66.7%) | 4/6 (66.7%) |

## Mismatches and abstentions

This table includes every field where at least one pass missed or withheld the answer.

| App and field | Expected | First pass | Original verifier | Patched verifier |
| --- | --- | --- | --- | --- |
| Podio · MCP | official [Source](https://www.progress.com/podio/documentation/using-podio/ai-and-mcp/podio-mcp-server-integration-guide) | abstained (abstained) | abstained (abstained) | abstained (abstained) |
| Intercom · Auth | oauth2, token [Source](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) |
| Lark (Larksuite) · Auth | oauth2, token [Source](https://open.larksuite.com/document/server-docs/getting-started/terminology) | oauth2, api_key (incorrect) | abstained (abstained) | abstained (abstained) |
| Lark (Larksuite) · Developer access | free [Source](https://open.larksuite.com/document/home/introduction-to-custom-app-development/testing-enterprise-and-personnel-functions) | free (correct) | free (correct) | abstained (abstained) |
| Lark (Larksuite) · Production access | free, admin_approval [Source](https://open.larksuite.com/document/uAjLw4CM/ukTMukTMukTM/api-call-guide/api-billing) | free (incorrect) | free (incorrect) | abstained (abstained) |
| GoHighLevel · Auth | oauth2, token [Source](https://marketplace.gohighlevel.com/docs/Authorization/authorization_doc/) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) |
| GoHighLevel · Developer access | free_trial [Source](https://marketplace.gohighlevel.com/docs/oauth/SandboxAccount/index.html) | paid_plan (incorrect) | paid_plan (incorrect) | paid_plan (incorrect) |
| GoHighLevel · Production access | paid_plan, admin_approval [Source](https://help.gohighlevel.com/support/solutions/articles/48001060529-highlevel-api-documentation) | paid_plan (incorrect) | paid_plan (incorrect) | paid_plan (incorrect) |
| Salesforce Commerce Cloud · Auth | oauth2 [Source](https://developer.salesforce.com/docs/commerce/commerce-api/guide/authorization.html) | oauth2, api_key, token (incorrect) | abstained (abstained) | oauth2, api_key (incorrect) |
| Salesforce Commerce Cloud · Production access | paid_plan, admin_approval [Source](https://www.salesforce.com/commerce/pricing/) | paid_plan (incorrect) | paid_plan (incorrect) | paid_plan (incorrect) |
| Salesforce Commerce Cloud · MCP | official [Source](https://github.com/salesforcecommercecloud/b2c-developer-tooling) | abstained (abstained) | abstained (abstained) | abstained (abstained) |
| DataForSEO · Auth | basic [Source](https://docs.dataforseo.com/v3/auth/) | api_key, token (incorrect) | api_key, token (incorrect) | api_key, token (incorrect) |
| DataForSEO · Developer access | free [Source](https://docs.dataforseo.com/v3/appendix-sandbox/) | free_trial (incorrect) | free_trial (incorrect) | free_trial (incorrect) |
| Netlify · Auth | oauth2, token [Source](https://docs.netlify.com/api-and-cli-guides/api-guides/get-started-with-api/#authentication) | oauth2, api_key (incorrect) | abstained (abstained) | abstained (abstained) |
| Netlify · Developer access | free [Source](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/#free-plan) | free (correct) | abstained (abstained) | abstained (abstained) |
| Netlify · Production access | free [Source](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/credit-based-pricing-plans/#free-plan) | free (correct) | abstained (abstained) | abstained (abstained) |
| Netlify · API breadth | broad [Source](https://open-api.netlify.com/) | broad (correct) | abstained (abstained) | abstained (abstained) |
| Harvest · Auth | oauth2, token [Source](https://help.getharvest.com/api-v2/authentication-api/authentication/authentication/) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) |
| Harvest · Developer access | free [Source](https://support.getharvest.com/hc/en-us/articles/360048180732-The-Harvest-API) | free (correct) | free (correct) | free_trial (incorrect) |
| Harvest · Production access | free [Source](https://support.getharvest.com/hc/en-us/articles/360048180732-The-Harvest-API) | paid_plan (incorrect) | paid_plan (incorrect) | paid_plan (incorrect) |
| Harvest · MCP | official [Source](https://support.getharvest.com/hc/en-us/articles/46293697226381-Harvest-MCP) | abstained (abstained) | abstained (abstained) | abstained (abstained) |
| Brex · Auth | oauth2, token [Source](https://developer.brex.com/guides/authentication) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) | oauth2, api_key (incorrect) |
| Brex · Developer access | free, vendor_approval [Source](https://www.brex.com/pricing) | free, admin_approval (incorrect) | free, admin_approval (incorrect) | free, admin_approval (incorrect) |
| Brex · Production access | free, vendor_approval, admin_approval [Source](https://www.brex.com/pricing) | vendor_approval (incorrect) | vendor_approval (incorrect) | vendor_approval (incorrect) |
| Brex · MCP | official [Source](https://developer.brex.com/docs/mcp) | abstained (abstained) | official (correct) | official (correct) |
| Fathom · API breadth | limited [Source](https://developers.fathom.ai/llms.txt) | broad (incorrect) | broad (incorrect) | broad (incorrect) |
| Fathom · MCP | official [Source](https://developers.fathom.ai/mcp-docs) | abstained (abstained) | abstained (abstained) | abstained (abstained) |

## Unscored fields

- Salesforce Commerce Cloud · **Developer access.** The quickstart offers a demo sandbox but expects the developer to supply a SLAS client. Salesforce documents provisioned sandboxes for entitled customers and partners. The minimum credential access gate for an independent developer remains unclear.

This small, stratified sample measures agreement with the published documentation. The test covered documented access paths.

Frozen labels SHA-256 `758a0d937e8753ab696b2694744bf8dd2e35189e0b2f8cd1655db1208dbd2364`

## What changed in the replay

- **Lark developer access.** The patched retry cited instructions for signing in, so its reviewer withheld the free-access claim. The public documentation confirms that developers can create test companies and that Starter includes a Basic API quota. [Test companies](https://open.larksuite.com/document/home/introduction-to-custom-app-development/testing-enterprise-and-personnel-functions) · [API billing](https://open.larksuite.com/document/uAjLw4CM/ukTMukTMukTM/api-call-guide/api-billing)
- **Harvest developer access.** Both retries cited a general trial offer. The original happened to match the `free` label with that citation. The patched retry answered `free_trial`, while Harvest's API help page confirms ongoing access on Free accounts. [Harvest API access](https://support.getharvest.com/hc/en-us/articles/360048180732-The-Harvest-API)
- **Authentication.** All three passes matched only 2 of 10 exact labels. A recurring error was labeling dashboard-issued tokens as API keys, including for Intercom and Harvest. [Intercom authentication](https://developers.intercom.com/docs/build-an-integration/learn-more/authentication) · [Harvest authentication](https://help.getharvest.com/api-v2/authentication-api/authentication/authentication/)

Separate targeted replays confirmed the Freshdesk citation and access fixes and the BigCommerce redirect fix. The follow-up score is from one replay with fresh verifier model calls and the original cached source bundle. The original verifier acquired its sources in stages. Model response variation and the documents available at each review stage may both contribute to the difference.
