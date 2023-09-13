# ChameleonCloud Python Doniclient CLI

![ChameleonCloud Logo](https://www.chameleoncloud.org/static/images/logo.png)

Welcome to the ChameleonCloud Python Doniclient CLI repository! This command-line interface (CLI) provides a convenient way to interact with ChameleonCloud's Doni hardware inventory project, enabling you to manage and automate various hardware-related tasks.

## Table of Contents

- [Installation](#installation)
- [Authentication](#authentication)
- [Usage](#usage)
- [Testing](#testing)
- [Contributing](#contributing)

## Installation

You can install the ChameleonCloud Python Doniclient CLI using pip:

```bash
pip install python-doniclient
```

## Authentication
Environment variables are the primary authentication method. Please refer to the [documentation on OpenRC scripts](https://chameleoncloud.readthedocs.io/en/latest/technical/cli.html#the-openstack-rc-script)  to learn more about how to download and source your authentication credentials for the CLI;

## Usage
To use the CLI, you can run the `openstack hardware` command followed by the desired subcommand. `openstack hardware --help` shows all the subcommands available. Here's a basic usage examples:

### List all hardware in the Doni database.

```bash
openstack hardware list
```

Options:

- --all: List hardware from all owners (requires admin rights).
- --long: Include all columns in the output.
- --worker-type <worker_type>: Filter by worker type.
- --worker-state <worker_state>: Filter by worker state (choices: PENDING, IN_PROGRESS, ERROR, STEADY).

For more details on specific commands and their options use --help or -h

### Create hardware in the Doni database

```bash
openstack hardware create --name <hardware_name> --hardware-type <hardware_type> --property <property_name>=<property_value>
```

### List specific hardware item in Doni using name or uuid.

```bash
openstack hardware get <hardware_uuid>
```

```bash
openstack hardware get <hardware_name>
```

### Set properties and name of an existing hardware item.

```bash
openstack hardware set <hardware_uuid> --name <new_hardware_name> --property <property_name>=<new_property_value>
```

Sets new name and property for the item `<hardware_uuid>`

```bash
openstack hardware set <hardware_name> --property <property_name>=<new_property_value>
```

Sets property for the item `<hardware_name`

## Testing

Run the tests using `stestr`

```bash
stestr run
```

## Contributing

### Publishing new versions

Use `poetry`'s built-in publish utility. Currently packages are published under the `chameleoncloud` user account on PyPi.

```shell
poetry publish --build
```

