# Data handling

## Local package

The renderer and archive builder contain no analytics, telemetry, network client or automatic upload. The renderer reads the JSON file you name and writes HTML to the location you name. It does not copy your input into logs or the public release archive. The resulting HTML contains project names, room/furniture labels, public dimensions, finishes, the indicative estimate and an optional Mebway project link. There are no automatically loaded remote images or scripts. Clicking a project link intentionally contacts Mebway using your browser.

Files remain on your device until you remove them. There is no automatic expiry or deletion. Anyone with a copy of the JSON or HTML can read its contents; signing out of Mebway or expiring a link does not delete downloaded copies. Use appropriate local permissions and remove files when no longer needed. Do not commit real customer presentations to a public repository.

## Connected assistant and hosted service

Connecting an assistant uses Mebway OAuth and your assistant client's credential storage. Tool requests and returned project/presentation content pass between that client and the hosted Mebway service. Your AI provider may receive and retain the content you allow the client to use, under that provider's settings and policies. This package does not send your entire conversation to Mebway and does not control third-party retention. Share only project data necessary for the task and review the permissions requested during authorization.

A quotation request sends the selected project or furniture details to Mebway for review and follow-up.

See the [Mebway privacy notice](https://mebway.ai/legal/us/en#privacy) for information about the hosted service.
