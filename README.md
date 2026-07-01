# Generate shorter Terraform registry URLs for AWS Provider

## Overview

```text
http://aws.nwlabs.dev/r/<resource> →
https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/<resource>
```

## Install dependendencies

```bash
brew bundle
```

## Install Terraform providers

```bash
TENV_AUTO_INSTALL=true terraform init
```

## Generate the latest versions of redirect HTML files

```bash
uv run generate
```
