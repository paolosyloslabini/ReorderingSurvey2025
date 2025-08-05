# Module definitions directory

This directory contains YAML configuration files for different module sets that techniques can depend on.

## File Structure

Each `.yml` file defines a module set with:
- `name`: unique identifier
- `description`: human-readable description
- `modules`: list of module names to load
- `environment`: environment variables to set
- `post_load`: commands to run after loading modules

## Usage

Techniques reference module sets in their configuration files (reorder.yml, multiply.yml) using the `modules` field.