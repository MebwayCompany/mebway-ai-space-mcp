# Security

Mebway authorizes access to customer projects through OAuth. Review the requested permissions before authorizing a client. Use the account controls to revoke access when needed.

## Offline viewer

The renderer reads only the explicitly selected JSON file, validates bounded numbers, arrays and public text fields, and writes static HTML to the selected output file. It does not run a local server, evaluate formulas, execute client scripts, load thumbnails, embed remote assets, import Mebway private code, contact a service or automatically follow links. It escapes customer text for HTML/SVG contexts and restricts project links to explicit HTTPS Mebway hosts. Only strictly validated six-digit hex samples become colours; decor labels never become CSS. Unavailable samples use an explicitly labelled neutral placeholder. A restrictive content security policy adds protection; output escaping and schema validation are the primary protections.

Schematic rectangles and labels reveal the public room and furniture dimensions supplied in the input. Treat both JSON and HTML as project data. Unknown fields are ignored for rendering but remain in the input file; never use the renderer as a sanitizer for distributing the original JSON. To share data, obtain a safe projection from the hosted tool and inspect what will be shared.

The CLI is intended for explicit local use with files you select. It is not a multi-tenant upload server. Put separate request limits, process isolation, storage permissions and authentication around it if adapting it into a hosted service. The input file limit and bounded public schema reduce resource use but do not provide a sandbox.

## Report a security issue

Use the support contact on the [Mebway connection guide](https://mcp.mebway.ai/?lang=en). Share details privately and omit credentials and customer project data from public issues.
