# Mebway AI Space MCP

Connection examples and an offline presentation viewer for the Mebway AI space configurator. This directory is an independently distributable package. It contains no Mebway application server or CAD/CAM implementation. MIT applies to this package's code and documentation; it grants no rights to Mebway catalogue designs, trademarks, customer projects or third-party data.

## Connect your assistant

See the [Mebway connection guide](https://mcp.mebway.ai/?lang=en) for setup and account requirements.

Use a client that supports remote MCP over HTTP and browser-based OAuth. Set its server URL to **https://mcp.mebway.ai/v2/mcp**. For clients using an `mcpServers` configuration with HTTP entries, [examples/client-config.json](examples/client-config.json) supplies a minimal example; adapt the surrounding configuration format to your client.

1. Add the remote server URL in your client's MCP integration settings.
2. Start its OAuth connection flow. Sign in on the Mebway page in your browser and review the permissions before granting access. Never paste your password or token into a conversation or public configuration.
3. After authorization, discover the tools exposed to your account. Use an active, approved Mebway account with a verified email, a complete profile and a Mebway password. If you sign in with Google or Apple, set a Mebway password for the same account before connecting.
4. Ask your assistant to plan your space, work on a private furniture concept, or fetch `get_project_presentation` for a project you can access. Tool availability is determined by the server. Your client handles OAuth discovery, token storage, expiration and reconnection.
5. Review your concept, dimensions, finishes and indicative estimate. Only when you explicitly request submission should the assistant call `send_furniture_quote_request` for Mebway review. A request is not an accepted order, checkout, a binding quotation, a CAM export or manufacturing approval.

Keep tokens in your client's secure credential store. Disconnect the integration when finished; use Mebway account access controls to revoke access, and check that subsequent calls are refused. Signing out of one browser session does not by itself prove every integration token was revoked.

## Images, AI visualizations and purchasing

`render_furniture_preview`, `render_furniture_draft_preview` and `render_project_preview` return raster images directly as MCP image content. Geometry stays on the server. Draft previews require the current ready build and an owned concept. Colours are approximate. Clients may save images they receive; screenshots and images cannot be protected against copying.

Use `save_project_visualization_snapshot` to create a perspective source from the current saved scene without spending Credits. Then fetch `get_project_visualization_options` and explicitly confirm the tier and Credits cost before `create_project_visualization`. Supply its current price, Credits and project version; a changed quote or project requires fresh options. Generation uses the existing Credits reservation and job system. AI output is an interpretation, not a dimensional or manufacturing validation.

`list_project_visualizations` and `get_visualization_image` retrieve ready saved images. Existing equirectangular 360° panoramas retain their projection metadata. This MCP version creates perspective sources; create an initial 360° source in the browser's panorama capture before requesting AI panorama generation. A perspective image is never described as 360°.

For catalogue furniture, `get_project_purchase_options` checks eligibility and returns an indicative total. After explicit customer confirmation, `prepare_project_cart` checks the same scene, total and currency before creating a shop cart link. The customer completes checkout in the shop; the integration does not place or pay for orders. Mixed projects or custom furniture require an inquiry to Mebway rather than silently omitting items from a cart. Estimates are indicative and require Mebway verification.

## Render a presentation locally

Python 3.11 or newer is sufficient; the renderer has no third-party runtime dependencies. Unpack this package, change to its directory and run:

```sh
python -m mebway_mcp render examples/presentation.json --output presentation.html
```

Open `presentation.html` in your browser. For a real project, save the **presentation object** returned by `get_project_presentation` to a JSON file and pass that file explicitly:

```sh
python -m mebway_mcp render my-presentation.json --output my-presentation.html
```

The command does not log in, fetch a project, open a browser or send anything. Installing with `python -m pip install .` optionally provides the equivalent `mebway-mcp render …` command. Package installation uses a build tool; offline rendering directly from the unpacked package needs no installation.

For a submitted furniture concept, save the quotation receipt's `presentation` object as the input JSON. It presents only that requested furniture item (`presentation_scope: requested_furniture`). `get_project_presentation` presents the saved scene; unsaved changes belong to the requested revision, not automatically to the saved scene.

The HTML contains a responsive 2D plan, numbered generic furniture rectangles, approximate colours, names, SKU labels, public dimensions and finishes, and an indicative estimate panel. When the server supplies a sampled finish colour, its swatch is labelled estimated; texture and grain are not represented. For missing colours a neutral placeholder is labelled unavailable. The first sampled finish colours the generic furniture rectangle; this does not represent the colour of every furniture component. Rectangles rotate around their placement anchor. The plan is schematic and does not validate fit, collisions or feasibility. Unknown prices remain unavailable, never zero. Quote line details are not rendered.

## Public presentation contract

Version `1.0` has this shape; [examples/presentation.json](examples/presentation.json) is an executable synthetic example:

```json
{
  "schema_version": "1.0",
  "project": {
    "id": "project-id",
    "name": "Project name",
    "url": "",
    "rooms": [{
      "id": "room-id", "name": "Room", "width_cm": 500, "depth_cm": 400,
      "furniture": [{
        "id": "furniture-id", "name": "Desk", "sku": "EXAMPLE",
        "x_cm": 50, "y_cm": 70, "rotation_deg": 0,
        "width_cm": 120, "depth_cm": 60, "height_cm": 75,
        "finishes": [{"option": "Top", "decor": "Oak", "color_hex": "#B18A61", "color_provenance": "estimated"}]
      }]
    }]
  },
  "quotation": {
    "status": "indicative", "currency": "PLN", "total": null,
    "disclaimer": "Requires Mebway review", "items": []
  },
  "manufacturing_approved": false
}
```

Identifiers may be strings or integers. All dimensions and placements use centimetres; rotation uses degrees. Dimension values must be between 0.1 and 100,000 cm, coordinates between −100,000 and 100,000 cm, and rotation between −360 and 360°. Values must be finite numbers, not strings or booleans. There may be at most 100 rooms and 2,000 furniture items across the project, 30 finishes per item, and 2,000 quote item objects. Most text is limited to 500 characters, identifiers to 128, the disclaimer to 2,000 and project URL to 2,048. Currency is three uppercase letters and the optional total is nonnegative and at most 1,000,000,000. Input files may be at most 8 MiB.

Optional finish `color_hex` is a six-digit hex string (`#rrggbb`) or null; `color_provenance` is `estimated` or null. The renderer selects recognized fields and ignores extra fields; arbitrary quote item fields are never rendered. Do not include private data merely because it will be ignored by this renderer: the JSON file itself still contains it. Project URLs are empty or explicit HTTPS links on `mebway.ai`, `www.mebway.ai` or `mcp.mebway.ai`, with no credentials or nonstandard ports. They are clickable links only, never automatically fetched. Clicking opens the hosted project and may require signing in. For offline testing use an empty project URL; local HTTP preview links are deliberately rejected.

Customers can intentionally use this safe presentation JSON in their own AI application. It is a scene summary, not a construction recipe: no meshes, detailed part outlines, joints, formulas, manufacturing files, proprietary template structure, supplier purchase information or reusable model-download links belong in this contract. Any geometry or image displayed to a user can be captured; this package does not promise copy prevention.

## Prepare a public archive

```sh
python build_release.py --output /path/to/mebway-mcp-public.zip
```

The builder includes only its explicit file allowlist, refuses symlinks and refuses to overwrite an existing archive or a source file. It does not copy repository history, arbitrary files, customer input, rendered customer HTML, caches, tokens or private application modules. Review the files before sharing the archive.

See [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md) for the security boundary and data handling.

The renderer creates a new output file and refuses to overwrite existing files or links. Choose a new filename for each export. Unsupported Unicode control, formatting and surrogate characters are rejected before writing. Ordinary international text, newlines and tabs remain supported.
