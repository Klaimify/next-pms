from next_pms.install import create_roles, setup_custom_docperms


def execute() -> None:
    create_roles()
    setup_custom_docperms()
