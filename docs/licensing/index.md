---
title: Licensing & Third-Party Notices
description: Software Bill of Materials (SBOM) and third-party attribution notices for each Actian MCP Server for Databases container image.
---

# Licensing & Third-Party Notices

!!! warning "Draft — pending legal review"
    The files linked from this page are **drafts generated for review, not certified compliance artifacts.** Do not treat them as final until this notice is removed. Specifically still open:

    - Legal review of the third-party NOTICE files has not been completed.
    - The official HCLSoftware `hsvt` SBOM validator has not yet been run against these files.
    - The product's SCAL (Supply Chain Assurance Level) has not been confirmed, which affects whether component hashes are required.
    - A small number of components (mostly the base image's system `pip` and its vendored dependencies) have no machine-readable license and are listed as gaps in each NOTICE file rather than given a fabricated license.
    - The `actian-mcp-server` package's own version/license entry was corrected by hand for this release rather than produced by a rebuild; this is noted inline in both the SBOM (as a `properties` entry) and the NOTICE file. A future rebuild will produce this correctly without manual correction.

Each Actian MCP Server for Databases container image ships with a [CycloneDX](https://cyclonedx.org/) 1.6 Software Bill of Materials (SBOM) and a corresponding third-party NOTICE file listing every open-source and third-party component included in the image, together with its license and, where available, the applicable copyright notice and license text.

## Release 1.1.0

| Engine | SBOM (CycloneDX JSON) | Third-party NOTICE |
|---|---|---|
| Ingres | [sbom-ingres-1.1.0.json](sbom/sbom-ingres-1.1.0.json) | [NOTICE-ingres-1.1.0.txt](sbom/NOTICE-ingres-1.1.0.txt) |
| Analytics Engine | [sbom-analytics-engine-1.1.0.json](sbom/sbom-analytics-engine-1.1.0.json) | [NOTICE-analytics-engine-1.1.0.txt](sbom/NOTICE-analytics-engine-1.1.0.txt) |
| Zen | [sbom-zen-1.1.0.json](sbom/sbom-zen-1.1.0.json) | [NOTICE-zen-1.1.0.txt](sbom/NOTICE-zen-1.1.0.txt) |
| HCL Informix® | [sbom-informix-1.1.0.json](sbom/sbom-informix-1.1.0.json) | [NOTICE-informix-1.1.0.txt](sbom/NOTICE-informix-1.1.0.txt) |

## About these files

The SBOM is a machine-readable inventory of every component in the image — its name, version, and license. The NOTICE file is a human-readable document assembled from the same inventory, with the full copyright and license text for each component reproduced where it was available in the image.

The Actian MCP Server itself is licensed under the Actian Corporation Customer License and Support Services Agreement, referenced in each SBOM and NOTICE as `LicenseRef-Actian-EULA`.
