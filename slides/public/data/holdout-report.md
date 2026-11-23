# Held-out accuracy audit

On 2026-11-23, ten apps were checked against published primary sources. The sample was chosen before the batch. The AI-assisted manual document review saved its labels before reading either model pass.

An answer is correct when its values match the documented label under the frozen rubric. An empty answer or unresolved conflict is an abstention. Accuracy uses all scorable fields. Coverage uses the share answered. Accuracy on answers uses answered fields as its denominator. [Rubric and sources](holdout-labels.json)

| Pass | Accuracy | Coverage | Accuracy on answers | Incorrect | Abstained |
| --- | ---: | ---: | ---: | ---: | ---: |
| First pass | 34/57 (59.6%) | 47/57 (82.5%) | 34/47 (72.3%) | 13 | 10 |
| Revised | 31/57 (54.4%) | 43/57 (75.4%) | 31/43 (72.1%) | 12 | 14 |

Verification corrected 0 wrong answers and filled 0 abstentions correctly. It lost 3 previously correct answers and withdrew 2 wrong answers.

## Accuracy by dimension

| Dimension | First pass | Revised |
| --- | ---: | ---: |
| Auth | 7/10 (70.0%) | 7/10 (70.0%) |
| Credential access | 7/19 (36.8%) | 6/19 (31.6%) |
| API surface | 15/19 (78.9%) | 13/19 (68.4%) |
| MCP | 5/9 (55.6%) | 5/9 (55.6%) |

## Accuracy by app

| App | First pass | Revised |
| --- | ---: | ---: |
| Copper | 3/6 (50.0%) | 3/6 (50.0%) |
| Freshdesk | 4/6 (66.7%) | 1/6 (16.7%) |
| Zoho Cliq | 5/6 (83.3%) | 5/6 (83.3%) |
| SendGrid | 3/6 (50.0%) | 3/6 (50.0%) |
| BigCommerce | 1/6 (16.7%) | 1/6 (16.7%) |
| Waterfall.io | 3/5 (60.0%) | 3/5 (60.0%) |
| Snowflake | 4/6 (66.7%) | 4/6 (66.7%) |
| ClickUp | 6/6 (100.0%) | 6/6 (100.0%) |
| Binance | 2/5 (40.0%) | 2/5 (40.0%) |
| NotebookLM | 3/5 (60.0%) | 3/5 (60.0%) |

## Mismatches and abstentions

This table includes every field where at least one pass missed or withheld the answer.

| App and field | Expected | First pass | Revised |
| --- | --- | --- | --- |
| Copper · Developer access | free_trial [Source](https://support.copper.com/en/articles/8823462-api-docs-and-tips) | paid_plan (incorrect) | abstained (abstained) |
| Copper · Production access | paid_plan, admin_approval [Source](https://support.copper.com/en/articles/8823462-api-docs-and-tips) | paid_plan (incorrect) | abstained (abstained) |
| Copper · MCP | community [Source](https://cotlet.dev/integrations/copper-crm-api-mcp-server) | abstained (abstained) | abstained (abstained) |
| Freshdesk · Auth | api_key, oauth2 [Source](https://developers.freshdesk.com/api/) | api_key (incorrect) | api_key (incorrect) |
| Freshdesk · Developer access | free_trial [Source](https://www.freshworks.com/freshdesk/pricing/free/) | free_trial, paid_plan (incorrect) | free_trial, paid_plan (incorrect) |
| Freshdesk · Production access | paid_plan [Source](https://support.freshdesk.com/support/solutions/articles/225439) | paid_plan (correct) | paid_plan, free_trial (incorrect) |
| Freshdesk · API interfaces | rest [Source](https://developers.freshdesk.com/api/) | rest (correct) | abstained (abstained) |
| Freshdesk · API breadth | broad [Source](https://developers.freshdesk.com/api/) | broad (correct) | abstained (abstained) |
| Zoho Cliq · Production access | free [Source](https://www.zoho.com/cliq/plan-comparison.html?zredirect=f) | free, paid_plan (incorrect) | free, paid_plan (incorrect) |
| SendGrid · Developer access | free_trial [Source](https://help.twilio.com/articles/47846436523419) | free (incorrect) | free (incorrect) |
| SendGrid · Production access | paid_plan [Source](https://www.twilio.com/docs/sendgrid/ui/account-and-settings/upgrading-your-plan) | free, paid_plan (incorrect) | free, paid_plan (incorrect) |
| SendGrid · MCP | community [Source](https://github.com/iiinigence/sendgrid-mcp) | abstained (abstained) | abstained (abstained) |
| BigCommerce · Auth | oauth2 [Source](https://docs.bigcommerce.com/developer/docs/overview/api-fundamentals/api-accounts) | abstained (abstained) | abstained (abstained) |
| BigCommerce · Developer access | free_trial [Source](https://docs.bigcommerce.com/developer/docs/overview/quick-start) | abstained (abstained) | abstained (abstained) |
| BigCommerce · Production access | paid_plan, admin_approval [Source](https://www.bigcommerce.com/pricing/faq/) | abstained (abstained) | abstained (abstained) |
| BigCommerce · API interfaces | rest, graphql [Source](https://docs.bigcommerce.com/developer/docs/overview/quick-start) | abstained (abstained) | abstained (abstained) |
| BigCommerce · API breadth | broad [Source](https://docs.bigcommerce.com/developer/docs/overview/quick-start) | abstained (abstained) | abstained (abstained) |
| Waterfall.io · Developer access | contact_sales [Source](https://docs.waterfall.io/v1/quickstart) | vendor_approval (incorrect) | vendor_approval (incorrect) |
| Waterfall.io · Production access | contact_sales, paid_plan [Source](https://docs.waterfall.io/v1/authentication) | vendor_approval (incorrect) | vendor_approval (incorrect) |
| Snowflake · Auth | oauth2, token, other [Source](https://docs.snowflake.com/en/developer-guide/sql-api/authenticating) | oauth2, api_key (incorrect) | oauth2, api_key, token, basic (incorrect) |
| Snowflake · API interfaces | rest, local_cli [Source](https://docs.snowflake.com/en/developer-guide/sql-api) | rest (incorrect) | rest (incorrect) |
| Binance · Developer access | free [Source](https://www.binance.com/en/binance-api) | abstained (abstained) | abstained (abstained) |
| Binance · API interfaces | rest, local_cli, other [Source](https://developers.binance.com/en/docs/introduction#api-types) | rest (incorrect) | rest (incorrect) |
| Binance · MCP | official [Source](https://www.binance.com/en/support/faq/detail/7a6e676e36fb455d96478932cb12d9f3) | abstained (abstained) | abstained (abstained) |
| NotebookLM · Developer access | free_trial [Source](https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/set-up-notebooklm) | paid_plan, admin_approval (incorrect) | paid_plan, admin_approval (incorrect) |
| NotebookLM · MCP | community [Source](https://github.com/jacob-bd/gemini-notebook-mcp-cli) | abstained (abstained) | abstained (abstained) |

## Unscored fields

- Waterfall.io · **MCP.** Waterfall documents Agent Skills for making HTTP calls and creating integrations. No verified product-data MCP implementation establishes a positive label. A documentation-search endpoint would have a different scope.
- Binance · **Production access.** Binance documents a self-service API Management flow and requires an identity-verified account, two-factor authentication, and a Spot deposit of any amount for account activation. The funding and identity prerequisites have no matching access label. The deposit is account funding.
- NotebookLM · **API interfaces.** Google explicitly documents how to call the Discovery Engine REST API and publishes a NotebookLM-specific RPC method reference. The RPC reference and REST binding syntax do not establish direct externally callable gRPC transport for the NotebookLM methods. The documented Google Cloud CLI command obtains credentials for the REST examples.

This small, stratified sample measures agreement with the published documentation. The test covered documented access paths.

Frozen labels SHA-256 `d7ef584752fbbc4c068bd1db71544401c4ffd9554f5a6aac540224cdbe85c7e7`

## What the verification log explains

- **Freshdesk drove all three regressions.** It added free trial access to the ongoing production answer. The official rate table has separate trial and paid allowances. The other two regressions were abstentions after the quote check rejected the API interface and breadth excerpts. The first pass had correctly identified a broad REST API. Its interface citation joined disjoint snippets with an ellipsis, and the retry repeated it. The breadth retry cited wording that the checker could not locate in the retained text. [Freshdesk API limits](https://support.freshdesk.com/support/solutions/articles/225439) · [REST API reference](https://developers.freshdesk.com/api/)
- **BigCommerce exposed a discovery gap.** The batch logged redirects from the old developer domain as out of scope. It discovered 16 URLs on the current docs domain, which the source rules excluded. Both passes left five of six scored fields unanswered. Current first-party docs explain how to generate credentials on a trial store and verify both REST and GraphQL. [BigCommerce developer quickstart](https://docs.bigcommerce.com/developer/docs/overview/quick-start)
- **ClickUp was an example of a clean hit.** Both passes matched all six checked fields. The first-party docs establish the personal access token and OAuth routes, API access on the Free Forever plan, and an official MCP server. [Authentication](https://developer.clickup.com/docs/authentication) · [Rate limits](https://developer.clickup.com/docs/rate-limits) · [MCP server](https://developer.clickup.com/docs/connect-an-ai-assistant-to-clickups-mcp-server)

The [scoring script](score.py) regenerates the scored tables from the frozen labels and the two run exports.
